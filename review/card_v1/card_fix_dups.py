"""Stage 45g: the v1 build found 170 near-duplicate image pairs (dHash <= 4) ACROSS splits, e.g. germany_9 (train) vs
germany_10 (val): the same road driven on two sequences. Fix (no result has been seen yet):
1. dHash of every image of road_hazards_card_v1 (already resized to 960; read-only).
2. Link two ROUTE groups if any of their images are within dHash <= LINK (6, wider than the build check 4).
3. Union-find the linked groups into super-groups; split super-groups ~70/15/15 of images per dataset batch, seed 0
   (same rule as card_build.split), -> split_groups_v2.csv.
4. Copy the images/labels into the NEW folder road_hazards_card_v2 by the new split (v1 is left as it is).
5. Check again: near-duplicate pairs across splits at dHash <= 4 and <= 6 must both be 0, else stop.
Writes dup_pairs_v1.csv, split_groups_v2.csv, fix_dups_report.json."""
import os, sys, csv, re, json, random, shutil, collections
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
V1, V2 = os.path.join(ROOT, 'road_hazards_card_v1'), os.path.join(ROOT, 'road_hazards_card_v2')
LINK = 6

seq_group = {}
for r in csv.DictReader(open(os.path.join(HERE, 'split_groups.csv'), encoding='utf-8')):
    seq_group[(r['dataset'].replace('CARD-', ''), r['seq'].split('/')[-1].strip().replace(' ', ''))] = (r['dataset'], r['group'])
items = []
for sp in ('train', 'val', 'test'):
    for f in sorted(os.listdir(os.path.join(V1, 'images', sp))):
        ds, seq, fr = f[:-4].split('__')
        items.append((sp, f, seq_group[(ds, seq)]))
print('images', len(items), flush=True)
def dh(p):
    a = np.asarray(Image.open(p).convert('L').resize((9, 8), Image.BILINEAR), dtype=np.int16)
    bits = (a[:, :-1] > a[:, 1:]).flatten()
    return int(''.join('1' if b else '0' for b in bits), 2)
H = np.array([dh(os.path.join(V1, 'images', sp, f)) for sp, f, g in items], dtype=np.uint64)
print('hashes done', flush=True)
pc = np.array([bin(i).count('1') for i in range(256)], dtype=np.uint8)
def popcount(x):
    x = x.view(np.uint8).reshape(-1, 8); return pc[x].sum(1)
G = [g for _, _, g in items]
pairs = []
for i in range(len(items)):
    d = popcount(H[i + 1:] ^ H[i])
    for j in np.nonzero(d <= LINK)[0] + i + 1:
        if G[i] != G[j]: pairs.append((i, int(j), int(d[j - i - 1])))
with open(os.path.join(HERE, 'dup_pairs_v1.csv'), 'w', newline='') as fo:
    w = csv.writer(fo); w.writerow(['img_a', 'split_a', 'group_a', 'img_b', 'split_b', 'group_b', 'dhash'])
    for i, j, d in pairs: w.writerow([items[i][1], items[i][0], G[i][1], items[j][1], items[j][0], G[j][1], d])
par = {}
def find(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for g in set(G): find(g)
for i, j, d in pairs: par[find(G[i])] = find(G[j])
links = collections.Counter((min(G[i], G[j]), max(G[i], G[j])) for i, j, d in pairs)
print('cross-group pairs (dHash<=%d): %d, linked group pairs: %d' % (LINK, len(pairs), len(links)))
for (a, b), n in links.most_common(30): print('  link %s <-> %s : %d pairs' % (a[1], b[1], n))
cnt = collections.Counter(find(g) for g in G); members = collections.defaultdict(set)
for g in set(G): members[find(g)].add(g)
newsp = {}
for d in sorted(set(g[0] for g in G)):
    ks = sorted(k for k in cnt if k[0] == d); random.Random(0).shuffle(ks)
    tot = sum(cnt[k] for k in ks); acc = 0
    for k in ks:
        sp = 'test' if acc < 0.15 * tot else 'val' if acc < 0.30 * tot else 'train'
        acc += cnt[k]
        for g in members[k]: newsp[g] = sp
out = os.path.join(HERE, 'split_groups_v2.csv')
if os.path.exists(out): sys.exit(out + ' exists; refusing to overwrite')
with open(out, 'w', newline='', encoding='utf-8') as fo:
    w = csv.writer(fo); w.writerow(['dataset', 'group', 'super_group', 'split'])
    for g in sorted(newsp): w.writerow([g[0], g[1], find(g)[1], newsp[g]])
S2 = [newsp[g] for g in G]
bad = {4: 0, 6: 0}
for i, j, d in pairs:
    if S2[i] != S2[j]:
        for t in bad:
            if d <= t: bad[t] += 1
c = collections.Counter(S2)
lab = collections.Counter()
for (sp, f, g), s2 in zip(items, S2):
    for l in open(os.path.join(V1, 'labels', sp, f[:-4] + '.txt')).read().split('\n'):
        if l.strip(): lab['%s_%s' % (s2, l.split()[0])] += 1
rep = dict(images_per_split=c, boxes=lab, groups_per_split=collections.Counter(newsp.values()), super_groups=len(cnt),
           cross_split_near_dups_after={'dhash<=4': bad[4], 'dhash<=6': bad[6]}, link_threshold=LINK, linked_pairs=len(links))
json.dump(rep, open(os.path.join(HERE, 'fix_dups_report.json'), 'w'), indent=1, default=str)
print(json.dumps(rep, default=str))
if bad[4] or bad[6]: sys.exit('STILL NEAR-DUPLICATES ACROSS SPLITS - stop')
for (sp, f, g), s2 in zip(items, S2):
    for kind, ext in (('images', '.jpg'), ('labels', '.txt')):
        src = os.path.join(V1, kind, sp, f[:-4] + ext); dst = os.path.join(V2, kind, s2, f[:-4] + ext)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst): shutil.copyfile(src, dst)
y = os.path.join(V2, 'data.yaml')
if not os.path.exists(y): open(y, 'w').write('train: images/train\nval: images/val\nnames:\n  0: pothole\n  1: speed_bump\n')
print('V2 BUILD OK')

"""Stage 45h: PLACE-level split of CARD (no result has been seen yet).
Why: Stage 45g showed real same-road repeats across sequences INSIDE a city (germany_9/germany_10 same garage,
Munich5/Munich7, Ludwig2/Ludwig3, Munich1/Munich3), while whole-image dHash also linked different cities (car bonnet and
sky dominate the hash), so route groups and plain dHash are both unsafe. Rule now: one PLACE (city / area) = one group:
Batch1 'germany' (all 2-day sequences), bibi, korntal, ludwig, speedbump, ingol, munich, augsburg, nardo, vi, avetrana,
carmiano, monte. Places are assigned to train/val/test by exhaustive search: minimise |val share - 0.15| + |test share - 0.15|
for pothole images and for bump images (train >= 0.60 of both); ties -> lexicographic order. Source images = the resized
road_hazards_card_v1 (read-only); output = NEW folder road_hazards_card_v3.
Leak check across splits on the scene part only (top 62 % of the frame, bonnet removed): 16x16 dHash candidates
(distance <= 40 of 256 bits) verified with ORB + RANSAC homography (>= 30 inliers = same scene). Must be 0, else stop."""
import os, sys, re, csv, json, itertools, shutil, collections
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
V1, V3 = os.path.join(ROOT, 'road_hazards_card_v1'), os.path.join(ROOT, 'road_hazards_card_v3')
def place(fn):
    ds, seq, fr = fn[:-4].split('__')
    if ds == 'Germany-Batch1': return 'germany'
    return re.match(r'[a-z]+', seq.lower()).group()
items = []
for sp in ('train', 'val', 'test'):
    for f in sorted(os.listdir(os.path.join(V1, 'images', sp))):
        cls = [l.split()[0] for l in open(os.path.join(V1, 'labels', sp, f[:-4] + '.txt')).read().split('\n') if l.strip()]
        items.append(dict(sp=sp, f=f, place=place(f), pot='0' in cls, bump='1' in cls, n0=cls.count('0'), n1=cls.count('1')))
P = sorted(set(i['place'] for i in items))
cnt = {p: [sum(i['pot'] for i in items if i['place'] == p), sum(i['bump'] for i in items if i['place'] == p),
           sum(1 for i in items if i['place'] == p)] for p in P}
T0, T1 = sum(c[0] for c in cnt.values()), sum(c[1] for c in cnt.values())
print('places:', {p: cnt[p] for p in P}, flush=True)
best = None
for a in itertools.product((0, 1, 2), repeat=len(P)):  # 0 train 1 val 2 test
    s = [[0, 0], [0, 0], [0, 0]]
    for p, k in zip(P, a): s[k][0] += cnt[p][0]; s[k][1] += cnt[p][1]
    if s[1][0] == 0 or s[1][1] == 0 or s[2][0] == 0 or s[2][1] == 0: continue
    if s[0][0] < 0.6 * T0 or s[0][1] < 0.6 * T1: continue
    cost = abs(s[1][0] / T0 - .15) + abs(s[2][0] / T0 - .15) + abs(s[1][1] / T1 - .15) + abs(s[2][1] / T1 - .15)
    if best is None or cost < best[0] - 1e-12: best = (cost, a, s)
cost, a, s = best
assign = {p: ('train', 'val', 'test')[k] for p, k in zip(P, a)}
print('assignment:', assign, 'shares pothole/bump images:', [(round(x[0] / T0, 3), round(x[1] / T1, 3)) for x in s], flush=True)
for i in items: i['new'] = assign[i['place']]
# leak check
def load(i):
    im = cv2.imread(os.path.join(V1, 'images', i['sp'], i['f']), cv2.IMREAD_GRAYSCALE)
    return im[: int(im.shape[0] * 0.62)]
def dh16(g):
    a = cv2.resize(g, (17, 16), interpolation=cv2.INTER_AREA).astype(np.int16)
    return np.packbits((a[:, :-1] > a[:, 1:]).flatten())
print('hashing', len(items), flush=True)
H = np.stack([dh16(load(i)) for i in items])
pc = np.array([bin(x).count('1') for x in range(256)], dtype=np.uint16)
S = np.array([i['new'] for i in items])
orb = cv2.ORB_create(1500); bf = cv2.BFMatcher(cv2.NORM_HAMMING)
kp = {}
def feats(k):
    if k not in kp: kp[k] = orb.detectAndCompute(load(items[k]), None)
    return kp[k]
cand = conf = 0; hits = []
for i in range(len(items)):
    d = pc[np.bitwise_xor(H[i + 1:], H[i])].sum(1)
    for j in np.nonzero(d <= 40)[0] + i + 1:
        if S[i] == S[j]: continue
        cand += 1
        k1, d1 = feats(i); k2, d2 = feats(int(j))
        if d1 is None or d2 is None or len(k1) < 30 or len(k2) < 30: continue
        m = [x for x, y in (p for p in bf.knnMatch(d1, d2, k=2) if len(p) == 2) if x.distance < 0.75 * y.distance]
        if len(m) < 30: continue
        A = np.float32([k1[x.queryIdx].pt for x in m]); B = np.float32([k2[x.trainIdx].pt for x in m])
        Hm, mask = cv2.findHomography(A, B, cv2.RANSAC, 5.0)
        if mask is not None and int(mask.sum()) >= 30:
            conf += 1; hits.append((items[i]['f'], S[i], items[int(j)]['f'], S[j], int(d[j - i - 1]), int(mask.sum())))
print('cross-split candidates (dHash16<=40): %d, ORB-confirmed same scene: %d' % (cand, conf), flush=True)
with open(os.path.join(HERE, 'leak_check_v3.csv'), 'w', newline='') as fo:
    w = csv.writer(fo); w.writerow(['img_a', 'split_a', 'img_b', 'split_b', 'dhash16', 'inliers']); w.writerows(hits)
rep = dict(assignment=assign, place_counts_pot_bump_images=cnt, shares=[(x[0] / T0, x[1] / T1) for x in s], cost=cost,
           candidates=cand, orb_confirmed_cross_split=conf,
           images=collections.Counter(i['new'] for i in items),
           boxes={sp: [sum(i['n0'] for i in items if i['new'] == sp), sum(i['n1'] for i in items if i['new'] == sp)] for sp in ('train', 'val', 'test')})
json.dump(rep, open(os.path.join(HERE, 'place_split_report.json'), 'w'), indent=1, default=str)
print(json.dumps(rep, default=str))
if conf: sys.exit('SAME SCENE FOUND ACROSS SPLITS - see leak_check_v3.csv - stop (nothing copied)')
for i in items:
    for kind, ext in (('images', '.jpg'), ('labels', '.txt')):
        src = os.path.join(V1, kind, i['sp'], i['f'][:-4] + ext); dst = os.path.join(V3, kind, i['new'], i['f'][:-4] + ext)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst): shutil.copyfile(src, dst)
y = os.path.join(V3, 'data.yaml')
if not os.path.exists(y): open(y, 'w').write('train: images/train\nval: images/val\nnames:\n  0: pothole\n  1: speed_bump\n')
print('V3 BUILD OK')

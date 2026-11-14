"""Stage 45: build road_hazards_card_v1 from data_card/raw (fetched by card_fetch.py). Images are COPIED as-is (no resize, no
re-encode), labels are YOLO lines with the CARD class ids remapped to ours (0 pothole, 1 speed_bump) by --map, which MUST be
given explicitly after the class check sheet (no default).
Split = whole ROUTE groups (a route and its repeats, e.g. Munich7 / Munich7_2 / Munich7_LowExposure, never cross splits),
~70/15/15 of labelled frames per dataset batch, fixed seed 0, written to split_groups.csv BEFORE any image is copied.
Checks: class ids, bounds, zero-size boxes, image/label pairing, SHA-256 duplicates and dHash<=4 near-duplicates ACROSS splits.
  card_build.py split                -> split_groups.csv (refuses to overwrite)
  card_build.py build --map 0:1,1:0 [--resize 960] [--step 2]  -> road_hazards_card_v1 + build_report.json (resumable)"""
import os, sys, csv, re, json, random, hashlib, shutil, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RAW, OUT = os.path.join(ROOT, 'data_card', 'raw'), os.path.join(ROOT, 'road_hazards_card_v1')
IDX, SPL = os.path.join(HERE, 'card_index.csv'), os.path.join(HERE, 'split_groups.csv')
REPORT = 'build_report.json'
SUF = re.compile(r'((?<=\d)_2$|_slam\d*$|_lowexposure$|_isabell?[ae]\d*$|_exposure$|_cam1_contaminated$|_s7s$|_highspeed$|_slope$|_sw$|_offroad\d*$|_bumps$|_rock$)')
def group(d, seq):
    n = seq.split('/')[-1].strip().lower()
    while True:
        m = SUF.sub('', n)
        if m == n: break
        n = m
    if 'Italy' in d:  # Italian sequences: whole PLACE is one group (nardo test track, avetrana, carmiano, monte, vi)
        n = re.match(r'[a-z]+', n).group()
    return d.split('-')[1] + ':' + n
def do_split():
    if os.path.exists(SPL): sys.exit(SPL + ' exists; refusing to overwrite')
    rows = list(csv.DictReader(open(IDX, encoding='utf-8')))
    g = collections.defaultdict(lambda: [0, set()])
    for r in rows:
        if int(r['label_bytes']) > 0 and int(r['image_bytes']) > 0:
            k = (r['dataset'], group(r['dataset'], r['seq'])); g[k][0] += 1; g[k][1].add(r['seq'])
    out = []
    for d in sorted(set(k[0] for k in g)):
        ks = sorted(k for k in g if k[0] == d); random.Random(0).shuffle(ks)
        tot = sum(g[k][0] for k in ks); acc = 0
        for k in ks:
            sp = 'test' if acc < 0.15 * tot else 'val' if acc < 0.30 * tot else 'train'
            acc += g[k][0]; out += [[d, k[1], s, sp, g[k][0]] for s in sorted(g[k][1])]
    with open(SPL, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['dataset', 'group', 'seq', 'split', 'group_labelled_frames']); w.writerows(out)
    c = collections.Counter(); [c.__setitem__(o[3], c[o[3]] + 0) for o in out]
    for sp in ('train', 'val', 'test'):
        gs = set((o[0], o[1]) for o in out if o[3] == sp)
        print(sp, 'groups', len(gs), 'labelled frames', sum(g[k][0] for k in gs))
def dhash(p):
    from PIL import Image
    im = Image.open(p).convert('L').resize((9, 8)); px = list(im.getdata())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])
def do_build(mp):
    spl = {(r['dataset'], r['seq']): r['split'] for r in csv.DictReader(open(SPL, encoding='utf-8'))}
    rows = list(csv.DictReader(open(IDX, encoding='utf-8')))
    rep = collections.Counter(); sha = {}; dh = collections.defaultdict(list); bad = []
    seen = collections.Counter()
    for r in rows:
        sp = spl.get((r['dataset'], r['seq']))
        if sp is None: continue
        if STEP > 1 and int(r['label_bytes']) > 0:  # keep every STEP-th labelled frame per sequence (neighbours are near-duplicates)
            seen[(r['dataset'], r['seq'])] += 1
            if (seen[(r['dataset'], r['seq'])] - 1) % STEP: continue
        base = os.path.join(RAW, r['dataset'], os.sep.join(p.strip() for p in r['seq'].split('/')))
        im, lb = os.path.join(base, 'img', 'cam_1', r['frame'] + '.jpg'), os.path.join(base, 'labels', r['frame'] + '.txt')
        if not os.path.exists(im): continue
        if int(r['label_bytes']) > 0 and not os.path.exists(lb): bad.append('label missing ' + lb); continue
        lines = []
        for l in (open(lb).read().split('\n') if int(r['label_bytes']) > 0 else []):
            v = l.split()
            if not v: continue
            if len(v) != 5 or v[0] not in mp: bad.append('bad line %s: %s' % (lb, l)); continue
            x, y, w, h = map(float, v[1:])
            if w <= 0 or h <= 0: rep['zero_size_dropped'] += 1; continue
            if not (0 <= x - w / 2 + 1e-6 and x + w / 2 <= 1 + 1e-6 and 0 <= y - h / 2 + 1e-6 and y + h / 2 <= 1 + 1e-6): rep['out_of_bounds'] += 1
            lines.append('%s %s %s %s %s' % (mp[v[0]], v[1], v[2], v[3], v[4])); rep['%s_%s' % (sp, mp[v[0]])] += 1
        name = '%s__%s__%s' % (r['dataset'].replace('CARD-', ''), r['seq'].split('/')[-1].strip().replace(' ', ''), r['frame'])
        h = hashlib.sha256(open(im, 'rb').read()).hexdigest()
        if h in sha and sha[h][0] != sp: bad.append('SHA duplicate across splits %s %s' % (name, sha[h][1]))
        sha[h] = (sp, name); dh[sp].append((dhash(im), name))
        di, dl = os.path.join(OUT, 'images', sp, name + '.jpg'), os.path.join(OUT, 'labels', sp, name + '.txt')
        os.makedirs(os.path.dirname(di), exist_ok=True); os.makedirs(os.path.dirname(dl), exist_ok=True)
        if not os.path.exists(di):
            if RESIZE:  # uniform scale of the whole image (no crop, no pad): normalised YOLO boxes stay exactly the same
                from PIL import Image
                I = Image.open(im); W, H = I.size; s = RESIZE / max(W, H)
                I.convert('RGB').resize((round(W * s), round(H * s)), Image.LANCZOS).save(di, quality=95)
            else: shutil.copyfile(im, di)
        txt = '\n'.join(lines) + ('\n' if lines else '')
        if os.path.exists(dl) and open(dl).read() != txt: sys.exit('DIFFERENT label exists, refusing: ' + dl)
        if not os.path.exists(dl): open(dl, 'w', newline='\n').write(txt)
        rep['%s_images' % sp] += 1; rep['%s_negative_images' % sp] += 0 if lines else 1
    near = 0
    if '--no-dhash' in sys.argv: dh = collections.defaultdict(list)
    for a, b in (('train', 'val'), ('train', 'test'), ('val', 'test')):
        for ha, na in dh[a]:
            for hb, nb in dh[b]:
                if bin(ha ^ hb).count('1') <= 4: near += 1; bad.append('near-duplicate %s %s' % (na, nb)) if near <= 50 else None
    rep['near_duplicates_across_splits'] = near
    y = os.path.join(OUT, 'data.yaml')
    if not os.path.exists(y): open(y, 'w').write('train: images/train\nval: images/val\nnames:\n  0: pothole\n  1: speed_bump\n')
    json.dump(dict(counts=rep, problems=bad[:200], n_problems=len(bad), map=mp), open(os.path.join(HERE, REPORT), 'w'), indent=1)
    print(json.dumps(rep)); print('problems:', len(bad)); print('BUILD OK' if not bad else 'BUILD HAS PROBLEMS - see build_report.json')
if __name__ == '__main__':
    if sys.argv[1] == 'split': do_split()
    elif sys.argv[1] == 'build':
        mp = dict(p.split(':') for p in sys.argv[sys.argv.index('--map') + 1].split(','))
        RESIZE = int(sys.argv[sys.argv.index('--resize') + 1]) if '--resize' in sys.argv else 0
        if '--split' in sys.argv: SPL = os.path.join(HERE, sys.argv[sys.argv.index('--split') + 1])
        if '--out' in sys.argv: OUT = os.path.join(ROOT, sys.argv[sys.argv.index('--out') + 1])
        if '--report' in sys.argv: REPORT = sys.argv[sys.argv.index('--report') + 1]
        STEP = int(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 1
        do_build(mp)

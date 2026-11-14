"""Stage 41 audit, step 1: reconcile predictions_C_ALLVAL.csv with the full val manifest. Read-only. VAL ONLY.
Run from the repo root:  venv\\Scripts\\python.exe review\\alldata_v1\\audit_2026-11-13\\a1_reconcile.py
Writes reconcile_images.csv, zero_boxes.csv next to this file."""
import csv, os, collections, hashlib
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R))
CSV = os.path.join(R, 'export_2026-11-13', 'predictions_C_ALLVAL.csv')
P = os.path.join(R, 'onnx_eval', 'pred_C_val')
IM = os.path.join(R, 'ds', 'images', 'val')
LB = os.path.join(R, 'ds', 'labels', 'val')

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

print('sha256 csv', sha(CSV))
print('sha256 zip', sha(CSV[:-4] + '.zip'))
rows = list(csv.DictReader(open(CSV)))
print('csv rows', len(rows))
by = collections.defaultdict(list)
for r in rows: by[r['image']].append(r)
print('csv unique images', len(by))

man = [l.strip() for l in open(os.path.join(R, 'allval.txt')) if l.strip()]
names = {}
for p in man:
    q = os.path.relpath(p, ROOT).replace('\\', '/').split('/')
    s = 'r2' if q[0] == 'road_hazards_v3b_C' else q[1]
    names[s + '__' + q[-1]] = (s, p)
print('manifest lines', len(man), 'unique ds names', len(names))
print('manifest per source', dict(collections.Counter(s for s, _ in names.values())))
ds = set(os.listdir(IM))
print('ds/images/val == manifest names:', ds == set(names))
print('csv images not in manifest:', len(set(by) - set(names)))

# original file still identical to the ds copy? (image and label)
bad_img = bad_lab = 0
for n, (s, p) in names.items():
    if os.path.getsize(p) != os.path.getsize(os.path.join(IM, n)): bad_img += 1
    lsrc = p.replace('\\images\\', '\\labels\\').rsplit('.', 1)[0] + '.txt'
    ldst = os.path.join(LB, os.path.splitext(n)[0] + '.txt')
    if open(lsrc, 'rb').read() != open(ldst, 'rb').read(): bad_lab += 1
print('ds copy differs from original: images(size)', bad_img, 'labels(bytes)', bad_lab)

out = []
stat = collections.Counter(); wh_bad = 0; tot_npy = 0; csv_vs_npy = 0; maxdiff = 0.0
for n in sorted(names):
    s = names[n][0]
    f = os.path.join(P, os.path.splitext(n)[0] + '.npy')
    lp = os.path.join(LB, os.path.splitext(n)[0] + '.txt')
    g = [l.split() for l in open(lp) if l.strip()] if os.path.exists(lp) else None
    ngt0 = sum(1 for x in (g or []) if x[0] == '0'); ngt1 = sum(1 for x in (g or []) if x[0] == '1')
    if not os.path.exists(f):
        state = 'NOT_EVALUATED_no_npy'; nd = -1; h0 = w0 = -1
    else:
        a = np.load(f); nd = len(a) - 1; h0, w0 = int(a[-1, 0]), int(a[-1, 1]); tot_npy += nd
        state = 'evaluated_zero_predictions' if nd == 0 else 'evaluated'
        if nd != len(by.get(n, [])): csv_vs_npy += 1
        elif nd:
            c = np.array([[float(r[k]) for k in ('x1', 'y1', 'x2', 'y2', 'conf')] for r in by[n]])
            maxdiff = max(maxdiff, float(np.abs(c[:, :4] - a[:-1, :4]).max()))
        with Image.open(os.path.join(IM, n)) as im: W, H = im.size
        if (W, H) != (w0, h0): wh_bad += 1
        if n in by and (int(by[n][0]['img_w']), int(by[n][0]['img_h'])) != (W, H): wh_bad += 1
    in_csv = n in by
    stat[(s, state, 'in_csv' if in_csv else 'not_in_csv')] += 1
    out.append([n, s, state, int(in_csv), nd, w0, h0, 'MISSING_LABEL_FILE' if g is None else len(g), ngt0, ngt1])
for k, v in sorted(stat.items()): print(k, v)
print('total detections in npy', tot_npy, '| images where csv row count != npy count', csv_vs_npy)
print('image size mismatches (file vs npy vs csv)', wh_bad, '| max |csv box - npy box| px', round(maxdiff, 4))
csv.writer(open(os.path.join(HERE, 'reconcile_images.csv'), 'w', newline='')).writerows(
    [['image', 'source', 'state', 'in_csv', 'n_pred_npy', 'img_w', 'img_h', 'n_gt', 'gt_pothole', 'gt_speed_bump']] + out)
miss = [o for o in out if not o[3]]
print('images not in csv', len(miss), dict(collections.Counter(o[1] for o in miss)),
      '| of them with GT boxes:', sum(1 for o in miss if o[7] not in (0, 'MISSING_LABEL_FILE')),
      '| GT boxes on them (pothole, bump):', sum(o[8] for o in miss), sum(o[9] for o in miss))
print('label files missing', sum(1 for o in out if o[7] == 'MISSING_LABEL_FILE'), '| empty label files', sum(1 for o in out if o[7] == 0))

# class ids, duplicates, zero boxes, ranges
print('class pairs', dict(collections.Counter((r['class_id'], r['class_name']) for r in rows)))
d = collections.Counter(tuple(r.values()) for r in rows)
print('exact duplicate rows', sum(v - 1 for v in d.values() if v > 1))
cf = np.array([float(r['conf']) for r in rows]); print('conf min/max', cf.min(), cf.max())
oob = sum(1 for r in rows if float(r['x1']) < 0 or float(r['y1']) < 0 or float(r['x2']) > int(r['img_w']) or float(r['y2']) > int(r['img_h']))
print('boxes outside the image', oob)
z = []
for n, rs in by.items():
    a = np.load(os.path.join(P, os.path.splitext(n)[0] + '.npy'))
    for i, r in enumerate(rs):
        if float(r['x2']) - float(r['x1']) <= 0 or float(r['y2']) - float(r['y1']) <= 0:
            b = a[i]
            z.append([n, r['source'], r['class_name'], r['conf'], r['x1'], r['y1'], r['x2'], r['y2'], r['img_w'], r['img_h']] + [repr(float(v)) for v in b[:4]] + [float(b[2] - b[0]), float(b[3] - b[1])])
print('zero w/h boxes in csv', len(z), 'max conf', max(float(x[3]) for x in z) if z else None)
print('  of them zero also at full precision (npy):', sum(1 for x in z if x[-1] <= 0 or x[-2] <= 0))
for x in z: print('  ', x[0], x[2], x[3], 'csv', x[4:8], 'npy w,h', round(x[-2], 4), round(x[-1], 4), 'img', x[8], x[9])
csv.writer(open(os.path.join(HERE, 'zero_boxes.csv'), 'w', newline='')).writerows(
    [['image', 'source', 'class', 'conf', 'x1', 'y1', 'x2', 'y2', 'img_w', 'img_h', 'npy_x1', 'npy_y1', 'npy_x2', 'npy_y2', 'npy_w', 'npy_h']] + z)

# label sanity per source
ls = collections.defaultdict(collections.Counter)
for n in names:
    s = names[n][0]
    for l in open(os.path.join(LB, os.path.splitext(n)[0] + '.txt')):
        t = l.split()
        if not t: continue
        ls[s]['class_' + t[0]] += 1
        v = [float(x) for x in t[1:5]]
        if len(t) != 5: ls[s]['not_5_columns'] += 1
        if min(v) < 0 or max(v) > 1 or v[0] - v[2] / 2 < -1e-3 or v[0] + v[2] / 2 > 1 + 1e-3 or v[1] - v[3] / 2 < -1e-3 or v[1] + v[3] / 2 > 1 + 1e-3: ls[s]['out_of_range'] += 1
        if v[2] <= 0 or v[3] <= 0: ls[s]['zero_size'] += 1
for s in ls: print('labels', s, dict(ls[s]))
sz = collections.defaultdict(collections.Counter)
for o in out: sz[o[1]][(o[5], o[6])] += 1
for s in sz: print('sizes', s, len(sz[s]), 'distinct;', sz[s].most_common(3))

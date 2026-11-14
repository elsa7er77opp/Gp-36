"""Image-level accuracy of model C on ALLVAL (VAL ONLY, read-only; predictions already stored in onnx_eval/pred_C_val).
For each image and class: GT present? model alarm = any prediction of that class with conf >= thr.
'loose' = alarm anywhere in the image; 'strict' = for GT images the alarm must hit a GT box (IoU >= 0.5), for no-GT images any alarm is an FP.
Also 'hazard' = either class (image has any hazard GT vs any alarm of either class; strict = a pred hits a GT of its class)."""
import os, csv, sys
import numpy as np
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P, IM, LB = (os.path.join(R, *p) for p in (('onnx_eval', 'pred_C_val'), ('ds', 'images', 'val'), ('ds', 'labels', 'val')))
GP = os.path.dirname(os.path.dirname(R))
rad = set()
for r in csv.DictReader(open(os.path.join(GP, 'parts_r3', 'sr', 'manifest.csv'), encoding='utf-8')):
    if r['split'] == 'val' and r['meta'] == 'family=rad':
        rad.add('sr__' + os.path.basename(r['out_image'].replace('\\', '/'))[:-4])
def iou(a, b):
    lt = np.maximum(a[:, None, :2], b[None, :, :2]); rb = np.minimum(a[:, None, 2:], b[None, :, 2:])
    i = np.clip(rb - lt, 0, None).prod(2)
    return i / ((a[:, 2:] - a[:, :2]).prod(1)[:, None] + (b[:, 2:] - b[:, :2]).prod(1)[None] - i + 1e-7)
img = []
for f in sorted(os.listdir(IM)):
    st = os.path.splitext(f)[0]
    a = np.load(os.path.join(P, st + '.npy')); h0, w0 = a[-1, :2]; det = a[:-1]
    rows = [l.split() for l in open(os.path.join(LB, st + '.txt')) if l.strip()] if os.path.exists(os.path.join(LB, st + '.txt')) else []
    g = np.array(rows, float)[:, :5] if rows else np.zeros((0, 5))
    gb = np.stack([(g[:, 1]-g[:, 3]/2)*w0, (g[:, 2]-g[:, 4]/2)*h0, (g[:, 1]+g[:, 3]/2)*w0, (g[:, 2]+g[:, 4]/2)*h0], 1) if len(g) else np.zeros((0, 4))
    rec = dict(name=st, src=st.split('__')[0], rad=st in rad)
    for c in (0, 1):
        gc, dc = gb[g[:, 0] == c] if len(g) else gb, det[det[:, 5] == c]
        rec[c] = dict(gt=len(gc) > 0, maxc=float(dc[:, 4].max()) if len(dc) else 0.0,
                      hitc=float(dc[(iou(dc[:, :4], gc).max(1) >= 0.5), 4].max()) if len(dc) and len(gc) and (iou(dc[:, :4], gc).max(1) >= 0.5).any() else 0.0)
    img.append(rec)
def score(sel, cls, thr, strict):
    tp = fp = fn = tn = 0
    for r in sel:
        if cls == 'hazard':
            gt = r[0]['gt'] or r[1]['gt']
            alarm = max(r[0]['maxc'], r[1]['maxc']) >= thr
            hit = max(r[0]['hitc'], r[1]['hitc']) >= thr
        else:
            gt, alarm, hit = r[cls]['gt'], r[cls]['maxc'] >= thr, r[cls]['hitc'] >= thr
        if gt:
            if (hit if strict else alarm): tp += 1
            else: fn += 1
        else:
            if alarm: fp += 1
            else: tn += 1
    n = tp + fp + fn + tn
    acc = (tp + tn) / n if n else float('nan')
    rec_ = tp / (tp + fn) if tp + fn else float('nan'); spec = tn / (tn + fp) if tn + fp else float('nan')
    prec = tp / (tp + fp) if tp + fp else float('nan')
    return [n, tp, fp, fn, tn, round(acc, 4), round(prec, 4), round(rec_, 4), round(spec, 4), round((rec_ + spec) / 2, 4) if tp + fn and tn + fp else '']
sets = {'ALLVAL': img, 'ALLVAL_minus_rad': [r for r in img if not r['rad']]}
for s in ['r2', 'rsid', 'bucko', 'sr', 'pol_v2', 'red_v2', 'ng8_v2', 'egy_v2']:
    sets[s] = [r for r in img if r['src'] == s]
out = [['set', 'class', 'mode', 'thr', 'images', 'TP', 'FP', 'FN', 'TN', 'accuracy', 'precision', 'recall', 'specificity', 'balanced_acc']]
for sn, sel in sets.items():
    for cls in ('hazard', 0, 1):
        for mode in ('loose', 'strict'):
            for thr in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
                out.append([sn, {0: 'pothole', 1: 'speed_bump'}.get(cls, cls), mode, thr] + score(sel, cls, thr, mode == 'strict'))
fo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imgacc_C_ALLVAL.csv')
if os.path.exists(fo): sys.exit('exists, refusing to overwrite: ' + fo)
csv.writer(open(fo, 'w', newline='')).writerows(out)
print('images', len(img), 'rad', sum(r['rad'] for r in img), 'sources', sorted(set(r['src'] for r in img)))

"""Stage 41 audit, step 2: per-source AP50 + TP/FP/FN at fixed thresholds + sr speed_bump miss analysis. Read-only. VAL ONLY.
Run from the repo root:  venv\\Scripts\\python.exe review\\alldata_v1\\audit_2026-11-13\\a2_score.py [pred_dir_name]
Uses the full-precision predictions in onnx_eval/<pred_dir_name> (default pred_C_val) and labels in ds/labels/val.
AP = same code path as onnx_eval/onnx_val.py (Ultralytics-style greedy matching, 101-point AP).
Operating-point counts: per image and class, predictions with conf >= thr sorted by conf, each takes the unmatched GT
with the highest IoU if IoU >= 0.50 (one-to-one)."""
import csv, os, sys, collections
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
PD = sys.argv[1] if len(sys.argv) > 1 else 'pred_C_val'
P = os.path.join(R, 'onnx_eval', PD)
IM = os.path.join(R, 'ds', 'images', 'val')
LB = os.path.join(R, 'ds', 'labels', 'val')
assert 'test' not in P.replace('\\', '/').split('/')
TAG = PD.replace('pred_', '').replace('_val', '')
NAMES = ['pothole', 'speed_bump']
THR = [0.05, 0.10, 0.25, 0.50]
SRC = ['r2', 'rsid', 'bucko', 'sr', 'pol_v2', 'red_v2', 'ng8_v2', 'egy_v2']

def box_iou(a, b):
    lt = np.maximum(a[:, None, :2], b[None, :, :2]); rb = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.clip(rb - lt, 0, None).prod(2)
    return inter / ((a[:, 2:] - a[:, :2]).prod(1)[:, None] + (b[:, 2:] - b[:, :2]).prod(1)[None] - inter + 1e-7)

def compute_ap(r, p):
    mrec = np.concatenate(([0.0], r, [r[-1] if len(r) else 1.0], [1.0])); mpre = np.concatenate(([1.0], p, [0.0], [0.0]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre))); x = np.linspace(0, 1, 101)
    y = np.interp(x, mrec, mpre)
    return float(np.trapezoid(y, x) if hasattr(np, 'trapezoid') else np.trapz(y, x))

D = {}
for f in sorted(os.listdir(IM)):
    st = os.path.splitext(f)[0]
    a = np.load(os.path.join(P, st + '.npy')); h0, w0 = a[-1, :2]; det = a[:-1]
    rows = [l.split() for l in open(os.path.join(LB, st + '.txt')) if l.strip()]
    g = np.unique(np.array(rows, float)[:, :5], axis=0) if rows else np.zeros((0, 5))
    gb = np.stack([(g[:, 1] - g[:, 3] / 2) * w0, (g[:, 2] - g[:, 4] / 2) * h0, (g[:, 1] + g[:, 3] / 2) * w0, (g[:, 2] + g[:, 4] / 2) * h0], 1) if len(g) else np.zeros((0, 4))
    D[f] = dict(src=f.split('__')[0], det=det, gc=g[:, 0].astype(int), gb=gb, hw=(int(h0), int(w0)))

def ap50(files):
    """Ultralytics-style: greedy over predictions in file order (already conf-sorted per image), IoU 0.5 column only."""
    res = {}
    for c in (0, 1):
        tp, cf, nl = [], [], 0
        for f in files:
            d = D[f]; gb = d['gb'][d['gc'] == c]; nl += len(gb)
            det = d['det'][d['det'][:, 5] == c]
            if not len(det): continue
            cor = np.zeros(len(det), bool)
            if len(gb):
                iou = box_iou(gb, det[:, :4]); m = np.zeros(len(gb), bool)
                for j in range(len(det)):
                    av = np.where(m, 0, iou[:, j]); k = av.argmax()
                    if av[k] >= 0.5: cor[j] = True; m[k] = True
            tp.append(cor); cf.append(det[:, 4])
        npred = sum(len(x) for x in tp)
        if nl == 0: res[c] = (None, nl, npred); continue
        if npred == 0: res[c] = (0.0, nl, 0); continue
        tp = np.concatenate(tp); cf = np.concatenate(cf); i = np.argsort(-cf, kind='stable'); tp = tp[i]
        tpc = tp.cumsum(); fpc = (~tp).cumsum()
        res[c] = (compute_ap(tpc / (nl + 1e-16), tpc / (tpc + fpc)), nl, npred)
    return res

def op_counts(files, thr):
    """one-to-one at IoU>=0.5 -> per class TP, FP, FN; plus images without GT of that class that got >=1 alarm."""
    out = {}
    for c in (0, 1):
        TP = FP = FN = 0; neg_img = neg_alarm = 0
        for f in files:
            d = D[f]; gb = d['gb'][d['gc'] == c]
            det = d['det'][(d['det'][:, 5] == c) & (d['det'][:, 4] >= thr)]
            det = det[np.argsort(-det[:, 4], kind='stable')]
            m = np.zeros(len(gb), bool); tp = 0
            if len(gb) and len(det):
                iou = box_iou(gb, det[:, :4])
                for j in range(len(det)):
                    av = np.where(m, 0, iou[:, j]); k = av.argmax()
                    if av[k] >= 0.5: m[k] = True; tp += 1
            TP += tp; FP += len(det) - tp; FN += len(gb) - tp
            if not len(gb):
                neg_img += 1; neg_alarm += int(len(det) > 0)
        out[c] = (TP, FP, FN, neg_img, neg_alarm)
    return out

allf = sorted(D)
groups = [('ALLVAL', allf)] + [(s, [f for f in allf if D[f]['src'] == s]) for s in SRC]
ap_rows = [['model', 'set', 'images', 'class', 'gt_boxes', 'pred_boxes_conf>=0.001', 'AP50', 'note']]
print(f'== AP50 ({TAG}; IoU 0.50; 101-point; conf>=0.001; full-precision boxes) ==')
for name, fs in groups:
    r = ap50(fs); vals = []
    for c in (0, 1):
        ap, nl, npred = r[c]
        note = '' if ap is not None else 'no GT of this class: AP not computable'
        ap_rows.append([TAG, name, len(fs), NAMES[c], nl, npred, '' if ap is None else f'{ap:.6f}', note])
        if ap is not None: vals.append(ap)
    m = float(np.mean(vals))
    ap_rows.append([TAG, name, len(fs), 'mean_over_classes_with_GT', '', '', f'{m:.6f}', f'{len(vals)} class(es)'])
    print(f'{name:8s} img {len(fs):5d} | pothole {"-" if r[0][0] is None else format(r[0][0], ".4f")} (gt {r[0][1]}) | bump {"-" if r[1][0] is None else format(r[1][0], ".4f")} (gt {r[1][1]}) | mean {m:.4f}')
csv.writer(open(os.path.join(HERE, f'metrics_AP50_{TAG}.csv'), 'w', newline='')).writerows(ap_rows)

op_rows = [['model', 'set', 'images', 'class', 'conf_thr', 'TP', 'FP', 'FN', 'precision', 'recall', 'images_without_this_class', 'of_them_with_alarm', 'FP_per_image']]
print('== operating points (one-to-one, IoU>=0.50) ==')
for name, fs in groups:
    for t in THR:
        o = op_counts(fs, t)
        for c in (0, 1):
            TP, FP, FN, ni, na = o[c]
            pr = f'{TP / (TP + FP):.4f}' if TP + FP else ''
            rc = f'{TP / (TP + FN):.4f}' if TP + FN else ''
            op_rows.append([TAG, name, len(fs), NAMES[c], t, TP, FP, FN, pr, rc, ni, na, f'{FP / len(fs):.4f}'])
            if t == 0.25: print(f'{name:8s} {NAMES[c]:10s} thr {t}: TP {TP} FP {FP} FN {FN} | P {pr or "-"} R {rc or "-"} | alarm on {na}/{ni} images without this class')
csv.writer(open(os.path.join(HERE, f'metrics_operating_points_{TAG}.csv'), 'w', newline='')).writerows(op_rows)

# ---- per-GT error log (all sources, both classes) at thr 0.25 ----
def classify(d, gi, thr=0.25):
    c = d['gc'][gi]; gb = d['gb'][gi:gi + 1]; det = d['det']
    r = dict(best_same_iou=0.0, best_same_conf=0.0, same_iou50_maxconf=0.0, best_other_iou=0.0, best_other_conf=0.0)
    if len(det):
        iou = box_iou(gb, det[:, :4])[0]
        s = det[:, 5] == c; o = ~s
        if s.any():
            k = np.flatnonzero(s)[iou[s].argmax()]; r['best_same_iou'] = float(iou[k]); r['best_same_conf'] = float(det[k, 4])
            ok = s & (iou >= 0.5)
            if ok.any(): r['same_iou50_maxconf'] = float(det[ok, 4].max())
        if o.any():
            ok = o & (iou >= 0.5)
            if ok.any():
                k = np.flatnonzero(ok)[det[ok, 4].argmax()]
            else:
                k = np.flatnonzero(o)[iou[o].argmax()]
            r['best_other_iou'] = float(iou[k]); r['best_other_conf'] = float(det[k, 4])
    return r

err = [['image', 'source', 'gt_index', 'gt_class', 'gt_x1', 'gt_y1', 'gt_x2', 'gt_y2', 'gt_w_px', 'gt_h_px', 'img_w', 'img_h',
        'matched_at_0.25', 'reason', 'same_class_iou>=0.5_max_conf', 'best_same_class_iou', 'its_conf', 'other_class_iou', 'other_class_conf']]
reason_cnt = collections.defaultdict(collections.Counter)
for f in allf:
    d = D[f]
    # one-to-one match at 0.25 to know which GT is matched
    matched = np.zeros(len(d['gc']), bool)
    for c in (0, 1):
        gi = np.flatnonzero(d['gc'] == c); det = d['det'][(d['det'][:, 5] == c) & (d['det'][:, 4] >= 0.25)]
        if len(gi) and len(det):
            iou = box_iou(d['gb'][gi], det[:, :4]); m = np.zeros(len(gi), bool)
            for j in range(len(det)):
                av = np.where(m, 0, iou[:, j]); k = av.argmax()
                if av[k] >= 0.5: m[k] = True
            matched[gi] = m
    for gi in range(len(d['gc'])):
        r = classify(d, gi); c = d['gc'][gi]; b = d['gb'][gi]
        if matched[gi]: reason = 'detected'
        elif r['same_iou50_maxconf'] > 0: reason = 'same_class_box_low_conf'
        elif r['best_other_iou'] >= 0.5 and r['best_other_conf'] >= 0.25: reason = 'other_class_box_conf>=0.25'
        elif r['best_other_iou'] >= 0.5: reason = 'other_class_box_low_conf'
        elif r['best_same_iou'] >= 0.1: reason = 'same_class_box_bad_bounds_iou_0.1-0.5'
        else: reason = 'no_box_near'
        reason_cnt[(d['src'], NAMES[c])][reason] += 1
        err.append([f, d['src'], gi, NAMES[c]] + [round(float(x), 1) for x in b] + [round(float(b[2] - b[0]), 1), round(float(b[3] - b[1]), 1), d['hw'][1], d['hw'][0],
                    int(matched[gi]), reason, round(r['same_iou50_maxconf'], 4), round(r['best_same_iou'], 3), round(r['best_same_conf'], 4), round(r['best_other_iou'], 3), round(r['best_other_conf'], 4)])
csv.writer(open(os.path.join(HERE, f'error_log_per_gt_{TAG}.csv'), 'w', newline='')).writerows(err)
print('== per-GT outcome at conf 0.25 (source, class): counts ==')
for k in sorted(reason_cnt): print(k, sum(reason_cnt[k].values()), dict(reason_cnt[k]))

# ---- sr speed_bump: stats + overlays ----
srf = [f for f in allf if D[f]['src'] == 'sr']
bp = [(f, x) for f in srf for x in D[f]['det'] if x[5] == 1]
print('sr speed_bump predictions', len(bp), 'in', len(set(f for f, _ in bp)), 'images; max conf', round(max(float(x[4]) for _, x in bp), 4),
      '| kept at 0.50/0.25/0.10/0.05:', [sum(1 for _, x in bp if x[4] >= t) for t in (0.5, 0.25, 0.1, 0.05)])
print('sr images with a speed_bump GT:', sum(1 for f in srf if (D[f]['gc'] == 1).any()), '| GT bumps:', sum(int((D[f]['gc'] == 1).sum()) for f in srf))
if TAG == 'C':
    od = os.path.join(HERE, 'overlays_sr_speed_bump'); os.makedirs(od, exist_ok=True)
    for f in srf:
        d = D[f]
        if not (d['gc'] == 1).any(): continue
        im = cv2.imdecode(np.fromfile(os.path.join(IM, f), np.uint8), cv2.IMREAD_COLOR)
        s = max(im.shape[:2]) / 960; th = max(2, int(2 * s))
        for c, b in zip(d['gc'], d['gb']):
            col = (0, 255, 0) if c == 1 else (255, 200, 0)   # GT bump green, GT pothole cyan
            cv2.rectangle(im, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), col, th)
            cv2.putText(im, 'GT ' + NAMES[c], (int(b[0]), max(int(b[1]) - 6, 20)), 0, 0.6 * s, col, th)
        for x in d['det']:
            if x[4] < 0.05: continue
            col = (0, 0, 255) if x[5] == 1 else (255, 0, 255)   # pred bump red, pred pothole magenta
            cv2.rectangle(im, (int(x[0]), int(x[1])), (int(x[2]), int(x[3])), col, th)
            cv2.putText(im, f'{NAMES[int(x[5])][:4]} {x[4]:.2f}', (int(x[0]), int(x[3]) + int(22 * s)), 0, 0.6 * s, col, th)
        r = 960 / max(im.shape[:2])
        im = cv2.resize(im, (int(im.shape[1] * r), int(im.shape[0] * r)))
        cv2.imencode('.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tofile(os.path.join(od, f))
    print('overlays written:', od)

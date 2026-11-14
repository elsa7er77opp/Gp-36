"""AP50 of C on ALLVAL by GT box size (VAL ONLY, read-only, stored predictions). Size = sqrt(w*h) of the box after scaling the
image so its longer side is 960 (the inference size). Buckets: small <32, medium 32-96, large >=96 px (COCO limits).
COCO-style ignore: GT outside the bucket is 'ignore' (a prediction matched to it is neither TP nor FP); an unmatched
prediction whose own size is outside the bucket is dropped. 101-point AP, IoU 0.5, greedy by confidence."""
import os, sys, csv
import numpy as np
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P, IM, LB = (os.path.join(R, *p) for p in (('onnx_eval', 'pred_C_val'), ('ds', 'images', 'val'), ('ds', 'labels', 'val')))
B = {'all': (0, 1e9), 'small': (0, 32), 'medium': (32, 96), 'large': (96, 1e9), 'medium+large': (32, 1e9)}
def iou(a, b):
    lt = np.maximum(a[:, None, :2], b[None, :, :2]); rb = np.minimum(a[:, None, 2:], b[None, :, 2:])
    i = np.clip(rb - lt, 0, None).prod(2)
    return i / ((a[:, 2:] - a[:, :2]).prod(1)[:, None] + (b[:, 2:] - b[:, :2]).prod(1)[None] - i + 1e-7)
def ap(tp, conf, n):
    if n == 0: return float('nan')
    o = np.argsort(-conf); tp = tp[o]; c = np.cumsum(tp); f = np.cumsum(1 - tp)
    r = c / n; p = c / np.maximum(c + f, 1e-9)
    mr = np.concatenate(([0.], r, [r[-1] if len(r) else 1.], [1.])); mp = np.concatenate(([1.], p, [0.], [0.]))
    mp = np.flip(np.maximum.accumulate(np.flip(mp))); x = np.linspace(0, 1, 101); y = np.interp(x, mr, mp)
    return float(((y[1:] + y[:-1]) / 2 * np.diff(x)).sum())
acc = {}
for f in sorted(os.listdir(IM)):
    st = os.path.splitext(f)[0]; src = st.split('__')[0]
    a = np.load(os.path.join(P, st + '.npy')); h0, w0 = a[-1, :2]; det = a[:-1]; s = 960.0 / max(h0, w0)
    lp = os.path.join(LB, st + '.txt')
    rows = [l.split() for l in open(lp) if l.strip()] if os.path.exists(lp) else []
    g = np.unique(np.array(rows, float)[:, :5], axis=0) if rows else np.zeros((0, 5))
    gb = np.stack([(g[:, 1]-g[:, 3]/2)*w0, (g[:, 2]-g[:, 4]/2)*h0, (g[:, 1]+g[:, 3]/2)*w0, (g[:, 2]+g[:, 4]/2)*h0], 1) if len(g) else np.zeros((0, 4))
    for c in (0, 1):
        gc = gb[g[:, 0] == c] if len(g) else gb; dc = det[det[:, 5] == c]; dc = dc[np.argsort(-dc[:, 4])]
        gs = np.sqrt((gc[:, 2]-gc[:, 0]) * (gc[:, 3]-gc[:, 1])) * s; ds = np.sqrt(np.clip((dc[:, 2]-dc[:, 0]) * (dc[:, 3]-dc[:, 1]), 0, None)) * s
        M = iou(dc[:, :4], gc) if len(dc) and len(gc) else np.zeros((len(dc), len(gc)))
        for bn, (lo, hi) in B.items():
            ig = ~((gs >= lo) & (gs < hi)); used = np.zeros(len(gc), bool); tp, cf = [], []
            # in-bucket GT first, then ignore GT (COCO order)
            for i in range(len(dc)):
                best, bj = 0.5, -1
                for j in np.argsort(ig, kind='stable'):
                    if used[j] and not ig[j]: continue
                    if bj >= 0 and not ig[bj] and ig[j]: break
                    if M[i, j] >= best: best, bj = M[i, j], j
                if bj >= 0:
                    if ig[bj]: continue
                    used[bj] = True; tp.append(1); cf.append(dc[i, 4])
                elif lo <= ds[i] < hi: tp.append(0); cf.append(dc[i, 4])
            for key in (('ALLVAL', c, bn), (src, c, bn)):
                d = acc.setdefault(key, [[], [], 0]); d[0] += tp; d[1] += cf; d[2] += int((~ig).sum())
out = [['set', 'class', 'size', 'gt_boxes', 'AP50']]
for (sn, c, bn), (tp, cf, n) in sorted(acc.items(), key=lambda k: (k[0][0] != 'ALLVAL', k[0])):
    out.append([sn, ['pothole', 'speed_bump'][c], bn, n, '' if n == 0 else round(ap(np.array(tp, float), np.array(cf, float), n), 4)])
fo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ap_by_size_C_ALLVAL.csv')
if os.path.exists(fo): sys.exit('exists, refusing: ' + fo)
csv.writer(open(fo, 'w', newline='')).writerows(out)
for r in out:
    if r[0] in ('set', 'ALLVAL', 'r2'): print(*r)

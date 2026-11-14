"""CPU re-implementation of `yolo val` (Ultralytics 8.4.192, imgsz=960, batch=8, rect, pad=0.5, conf=0.001, iou=0.7,
max_det=300, multi_label NMS, greedy matching, 101-point AP) for an exported ONNX model. VAL ONLY: refuses any 'test' path.
  python3 onnx_val.py prep  <images_dir>                 -> order.json (rect order and batch shapes)
  python3 onnx_val.py run   <model.onnx> <images_dir> <pred_dir> [seconds]   (resumable; one .npy per image)
  python3 onnx_val.py score <images_dir> <pred_dir> [prefix]   (prefix = only files starting with it, e.g. r2__)
"""
import json, math, os, sys, time
import cv2, numpy as np
from PIL import Image, ImageOps
IMGSZ, BATCH, STRIDE, PAD, CONF, IOU, MAXDET, MAXWH, MAXNMS = 960, 8, 32, 0.5, 0.001, 0.7, 300, 7680, 30000
IOUV = np.linspace(0.5, 0.95, 10)
HERE = os.path.dirname(os.path.abspath(__file__))

def guard(p):
    if 'test' in os.path.normpath(p).replace('\\', '/').split('/'):
        sys.exit('refused: test split')

def exif_hw(p):
    im = Image.open(p); s = im.size
    try:
        o = im.getexif().get(274, 1)
        if o in (5, 6, 7, 8): s = (s[1], s[0])
    except Exception: pass
    return s[1], s[0]

def prep(imdir):
    guard(imdir)
    files = sorted(f for f in os.listdir(imdir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')))
    hw = np.array([exif_hw(os.path.join(imdir, f)) for f in files], dtype=float)
    ar = hw[:, 0] / hw[:, 1]; irect = ar.argsort(kind='stable')
    files = [files[i] for i in irect]; ar = ar[irect]
    bi = np.floor(np.arange(len(files)) / BATCH).astype(int)
    shapes = []
    for i in range(bi[-1] + 1):
        a = ar[bi == i]; mn, mx = a.min(), a.max()
        shapes.append([mx, 1] if mx < 1 else ([1, 1 / mn] if mn > 1 else [1, 1]))
    bs = (np.ceil(np.array(shapes) * IMGSZ / STRIDE + PAD).astype(int) * STRIDE).tolist()
    json.dump({'files': files, 'shape': [bs[b] for b in bi]}, open(os.path.join(imdir, '..', '..', 'order_' + os.path.basename(imdir) + '.json'), 'w'))
    print('prep', len(files))

def letterbox(p, rect):
    im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR); h0, w0 = im.shape[:2]
    r = IMGSZ / max(h0, w0)
    if r != 1:
        w, h = min(math.ceil(w0 * r), IMGSZ), min(math.ceil(h0 * r), IMGSZ)
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_LINEAR)
    h1, w1 = im.shape[:2]; g0 = (h1 / h0, w1 / w0)
    r2 = min(min(rect[0] / h1, rect[1] / w1), 1.0)
    nu = (max(round(w1 * r2), 1), max(round(h1 * r2), 1))
    dw, dh = (rect[1] - nu[0]) / 2, (rect[0] - nu[1]) / 2
    if (w1, h1) != nu: im = cv2.resize(im, nu, interpolation=cv2.INTER_LINEAR)
    top, bot, left, right = round(dh - 0.1), round(dh + 0.1), round(dw - 0.1), round(dw + 0.1)
    im = cv2.copyMakeBorder(im, top, bot, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    x = np.ascontiguousarray(im[..., ::-1].transpose(2, 0, 1))[None].astype(np.float32) / 255
    return x, (h0, w0), ((g0[0] * r2, g0[1] * r2), (left, top))

def nms_np(b, s, t):
    x1, y1, x2, y2 = b.T; area = (x2 - x1) * (y2 - y1); order = s.argsort()[::-1]; keep = []
    while order.size:
        i = order[0]; keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]]); yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]]); yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.clip(xx2 - xx1, 0, None) * np.clip(yy2 - yy1, 0, None)
        iou = inter / (area[i] + area[order[1:]] - inter)
        order = order[1:][iou <= t]
    return np.array(keep, dtype=int)

def post(out, h0w0, rp):
    p = out[0].T; cls = p[:, 4:]
    p = p[cls.max(1) > CONF]; cls = p[:, 4:]
    if not len(p): return np.zeros((0, 6), np.float32)
    xy, wh = p[:, :2], p[:, 2:4]; box = np.concatenate([xy - wh / 2, xy + wh / 2], 1)
    i, j = np.where(cls > CONF)
    x = np.concatenate([box[i], cls[i, j, None], j[:, None].astype(np.float32)], 1)
    if len(x) > MAXNMS: x = x[x[:, 4].argsort()[::-1][:MAXNMS]]
    k = nms_np(x[:, :4] + x[:, 5:6] * MAXWH, x[:, 4], IOU)[:MAXDET]; x = x[k]
    (gy, gx), (px, py) = rp
    x[:, [0, 2]] = (x[:, [0, 2]] - px) / gx; x[:, [1, 3]] = (x[:, [1, 3]] - py) / gy
    x[:, [0, 2]] = x[:, [0, 2]].clip(0, h0w0[1]); x[:, [1, 3]] = x[:, [1, 3]].clip(0, h0w0[0])
    return x.astype(np.float32)

def run(model, imdir, pdir, secs=160):
    guard(imdir); import onnxruntime as ort
    o = json.load(open(os.path.join(imdir, '..', '..', 'order_' + os.path.basename(imdir) + '.json')))
    os.makedirs(pdir, exist_ok=True)
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider']); t0 = time.time(); n = 0
    for f, sh in zip(o['files'], o['shape']):
        dst = os.path.join(pdir, os.path.splitext(f)[0] + '.npy')
        if os.path.exists(dst): continue
        if time.time() - t0 > secs: break
        x, hw, rp = letterbox(os.path.join(imdir, f), sh)
        det = post(sess.run(None, {'images': x})[0], hw, rp)
        np.save(dst + '.tmp.npy', np.concatenate([det, np.array([[hw[0], hw[1], 0, 0, -1, -1]], np.float32)]))
        os.replace(dst + '.tmp.npy', dst); n += 1
    done = sum(1 for f in o['files'] if os.path.exists(os.path.join(pdir, os.path.splitext(f)[0] + '.npy')))
    print(f'ran {n} this call; done {done}/{len(o["files"])}')

def box_iou(a, b):
    lt = np.maximum(a[:, None, :2], b[None, :, :2]); rb = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.clip(rb - lt, 0, None).prod(2)
    return inter / ((a[:, 2:] - a[:, :2]).prod(1)[:, None] + (b[:, 2:] - b[:, :2]).prod(1)[None] - inter + 1e-7)

def compute_ap(r, p):
    mrec = np.concatenate(([0.0], r, [r[-1] if len(r) else 1.0], [1.0])); mpre = np.concatenate(([1.0], p, [0.0], [0.0]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre))); x = np.linspace(0, 1, 101)
    return np.trapezoid(np.interp(x, mrec, mpre), x) if hasattr(np, 'trapezoid') else np.trapz(np.interp(x, mrec, mpre), x)

def score(imdir, pdir, prefix=''):
    guard(imdir); lab = os.path.join(os.path.dirname(os.path.dirname(imdir)), 'labels', os.path.basename(imdir))
    TP, CF, PC, TC = [], [], [], []; nimg = 0
    for f in sorted(os.listdir(imdir)):
        if prefix and not f.startswith(prefix): continue
        pp = os.path.join(pdir, os.path.splitext(f)[0] + '.npy')
        if not os.path.exists(pp): sys.exit('missing prediction ' + pp)
        a = np.load(pp); h0, w0 = a[-1, :2]; det = a[:-1]; nimg += 1
        lp = os.path.join(lab, os.path.splitext(f)[0] + '.txt'); g = np.zeros((0, 5))
        if os.path.exists(lp):
            rows = [l.split() for l in open(lp) if l.strip()]
            if rows: g = np.unique(np.array(rows, float)[:, :5], axis=0)
        gc = g[:, 0]; gb = np.stack([(g[:, 1] - g[:, 3] / 2) * w0, (g[:, 2] - g[:, 4] / 2) * h0, (g[:, 1] + g[:, 3] / 2) * w0, (g[:, 2] + g[:, 4] / 2) * h0], 1) if len(g) else np.zeros((0, 4))
        TC.append(gc)
        if not len(det): continue
        correct = np.zeros((len(det), 10), bool)
        if len(g):
            iou = box_iou(gb, det[:, :4]) * (gc[:, None] == det[:, 5][None])
            matched = np.zeros((len(g), 10), bool)
            for j in np.flatnonzero((iou >= IOUV.min()).any(0)):
                av = np.where(matched, 0, iou[:, j, None]); k = av.argmax(0)
                correct[j] = av[k, range(10)] >= IOUV; matched[k, range(10)] |= correct[j]
        TP.append(correct); CF.append(det[:, 4]); PC.append(det[:, 5])
    tp, conf, pc, tc = np.concatenate(TP), np.concatenate(CF), np.concatenate(PC), np.concatenate(TC)
    i = np.argsort(-conf, kind='stable'); tp, conf, pc = tp[i], conf[i], pc[i]
    res = {}
    for c, name in [(0, 'pothole'), (1, 'speed_bump')]:
        nl = int((tc == c).sum()); m = pc == c
        if nl == 0 or m.sum() == 0: res[name] = None; continue
        tpc = tp[m].cumsum(0); fpc = (1 - tp[m]).cumsum(0)
        rec = tpc / (nl + 1e-16); pre = tpc / (tpc + fpc)
        ap = np.array([compute_ap(rec[:, j], pre[:, j]) for j in range(10)])
        res[name] = {'boxes': nl, 'AP50': round(float(ap[0]), 4), 'AP50_95': round(float(ap.mean()), 4)}
    have = [v for v in res.values() if v]
    res['images'] = nimg; res['mean_AP50'] = round(float(np.mean([v['AP50'] for v in have])), 4)
    res['mean_AP50_95'] = round(float(np.mean([v['AP50_95'] for v in have])), 4)
    print(json.dumps(res))

if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'prep': prep(a[2])
    elif a[1] == 'run': run(a[2], a[3], a[4], float(a[5]) if len(a) > 5 else 160)
    elif a[1] == 'score': score(a[2], a[3], a[4] if len(a) > 4 else '')

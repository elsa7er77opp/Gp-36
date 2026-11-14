"""Stage 41b: WBF(C, v1) on ALLVAL next to C alone and v1 alone. VAL ONLY (refuses any test path). Read-only on the inputs.

  venv\\Scripts\\python.exe review\\alldata_v1\\audit_2026-11-13\\a5_wbf_allval.py --c <C predictions.json> --v1 <v1 predictions.json> --out <new folder>

Inputs: Ultralytics `yolo val save_json=True` files (image_id = file stem, category_id 1/2, bbox x,y,w,h px, conf >= 0.001).
WBF: tools/wbf_ensemble.fuse_files with the settings frozen in STATUS Stage 29/32: iou 0.55, skip 0.001, equal weights.
Nothing is tuned here. Scoring: the same functions as a2_score.py (AP50 101-point at IoU 0.50; one-to-one counts).
Operating thresholds are the ones chosen earlier on r2 val (review/metrics_r3/val_r2_final/report.json), not on ALLVAL.
Also prints the sensitivity without the 32 sr `rad` val images (official = with them)."""
import argparse, contextlib, csv, io, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ap = argparse.ArgumentParser()
ap.add_argument('--c', required=True); ap.add_argument('--v1', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--second-name', default='v1', help='label of the second model in the tables')
a = ap.parse_args()
for p in (a.c, a.v1, a.out):
    if 'test' in [s.lower() for s in os.path.normpath(p).replace('\\', '/').split('/')] or '_test' in p.lower():
        sys.exit('refused: test path ' + p)
if os.path.exists(a.out): sys.exit(a.out + ' exists; refusing to overwrite')

sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, HERE)
from wbf_ensemble import fuse_files
sys.argv = [sys.argv[0], 'pred_A1_val']            # a2_score needs a prediction folder to load GT; its own output is discarded
with contextlib.redirect_stdout(io.StringIO()):
    import a2_score as A
STEMS = {os.path.splitext(f)[0]: f for f in A.allf}
IOU, SKIP = 0.55, 0.001

def load(path):
    p = json.load(open(path, encoding='utf-8'))
    ids = {str(x['image_id']) for x in p}
    if not ids <= set(STEMS): sys.exit(f'{path}: {len(ids - set(STEMS))} image ids are not ALLVAL val images (wrong split?)')
    cats = {x['category_id'] for x in p}
    if not cats <= {1, 2}: sys.exit(f'{path}: unexpected category ids {cats}')
    return p

def to_det(preds):
    by = {s: [] for s in STEMS}
    for x in preds:
        b = x['bbox']; by[str(x['image_id'])].append([b[0], b[1], b[0] + b[2], b[1] + b[3], x['score'], x['category_id'] - 1])
    out = {}
    for s, rows in by.items():
        d = np.array(rows, np.float64).reshape(-1, 6)
        out[STEMS[s]] = d[np.argsort(-d[:, 4], kind='stable')]
    return out

pc, pv = load(a.c), load(a.v1)
fused, _ = fuse_files([pc, pv], [1.0, 1.0], IOU, SKIP)
os.makedirs(a.out)
json.dump(fused, open(os.path.join(a.out, 'predictions_WBF.json'), 'w'))
second = a.second_name
models = {'C': to_det(pc), second: to_det(pv), f'WBF(C,{second})': to_det(fused)}
thr = {}
rep = os.path.join(ROOT, 'review', 'metrics_r3', 'val_r2_final', 'report.json')
if os.path.exists(rep):
    m = json.load(open(rep, encoding='utf-8'))['models']
    for k, name in (('C', 'C'), ('v1', 'v1'), ('WBF_C_v1', 'WBF(C,v1)')):
        if k in m: thr[name] = (m[k]['classes']['pothole']['op']['thr'], m[k]['classes']['speed_bump']['op']['thr'])

fam = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'parts_r3', 'sr', 'manifest.csv'), encoding='utf-8')):
    fam['sr__' + os.path.basename(r['out_image'])] = r['meta'].split('=')[1]
rad = {f for f in A.allf if A.D[f]['src'] == 'sr' and fam[f] == 'rad'}
groups = [('ALLVAL', A.allf)] + [(s, [f for f in A.allf if A.D[f]['src'] == s]) for s in A.SRC] + [('ALLVAL_minus_32_sr_rad(sensitivity)', [f for f in A.allf if f not in rad])]

rows = [['model', 'set', 'images', 'class', 'gt_boxes', 'AP50', 'conf_thr', 'thr_source', 'TP', 'FP', 'FN', 'precision', 'recall']]
summary = {}
for name, det in models.items():
    for f in A.allf: A.D[f]['det'] = det[f]
    print(f'===== {name}: boxes {sum(len(det[f]) for f in A.allf)}, images with >=1 box {sum(1 for f in A.allf if len(det[f]))}/{len(A.allf)}')
    for gname, fs in groups:
        r = A.ap50(fs); vals = [r[c][0] for c in (0, 1) if r[c][0] is not None]; mean = float(np.mean(vals))
        summary[(name, gname)] = (r[0][0], r[1][0], mean)
        fmt = lambda v: '   -  ' if v is None else f'{v:.4f}'
        print(f'  {gname:36s} img {len(fs):5d} | pothole {fmt(r[0][0])} | bump {fmt(r[1][0])} | mean {mean:.4f}')
        tl = [(0.25, 0.25, 'fixed 0.25')] + ([(thr[name][0], thr[name][1], 'r2-val F1-opt (val_r2_final)')] if name in thr else [])
        for t0, t1, src in tl:
            o = (A.op_counts(fs, t0)[0], A.op_counts(fs, t1)[1])
            for c in (0, 1):
                TP, FP, FN = o[c][:3]
                rows.append([name, gname, len(fs), A.NAMES[c], r[c][1], '' if r[c][0] is None else f'{r[c][0]:.6f}', (t0, t1)[c], src, TP, FP, FN,
                             f'{TP / (TP + FP):.4f}' if TP + FP else '', f'{TP / (TP + FN):.4f}' if TP + FN else ''])
        rows.append([name, gname, len(fs), 'mean_over_classes_with_GT', '', f'{mean:.6f}', '', '', '', '', '', '', ''])
csv.writer(open(os.path.join(a.out, 'metrics_WBF_ALLVAL.csv'), 'w', newline='')).writerows(rows)

w = f'WBF(C,{second})'
dC, dW = summary[('C', 'ALLVAL')], summary[(w, 'ALLVAL')]
print('===== ALLVAL, WBF minus C: pothole %+.4f | bump %+.4f | mean %+.4f' % (dW[0] - dC[0], dW[1] - dC[1], dW[2] - dC[2]))
print('Stage 41 rule (written before the run): another candidate replaces C only if its ALLVAL mean AP50 >= C + 0.02 ->',
      'MET' if dW[2] - dC[2] >= 0.02 else 'NOT MET')
print('WBF runs two models per frame; latency is NOT measured here.')
json.dump({'wbf': {'iou': IOU, 'skip': SKIP, 'weights': [1, 1]}, 'inputs': {'C': a.c, second: a.v1},
           'ALLVAL': {k[0]: {'pothole_AP50': v[0], 'speed_bump_AP50': v[1], 'mean_AP50': v[2]} for k, v in summary.items() if k[1] == 'ALLVAL'},
           'ALLVAL_minus_32_sr_rad': {k[0]: {'pothole_AP50': v[0], 'speed_bump_AP50': v[1], 'mean_AP50': v[2]} for k, v in summary.items() if k[1].startswith('ALLVAL_minus')}},
          open(os.path.join(a.out, 'summary.json'), 'w'), indent=1)
print('written:', a.out)

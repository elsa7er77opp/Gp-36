"""Stage 41 audit, step 3 (read-only, VAL ONLY): (a) sr family breakdown of the val bump GT, (b) sensitivity of ALLVAL
bump AP50 to the 32 sr `rad` val images (reported next to, not instead of, the official number), (c) false alarms on
empty-label images, (d) group/video overlap between splits of every part.
Run from the repo root:  venv\Scripts\python.exe review\alldata_v1\audit_2026-11-13\a4_extra.py"""
import csv, os, sys, collections, io, contextlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.argv = [sys.argv[0], 'pred_C_val']
with contextlib.redirect_stdout(io.StringIO()):
    sys.path.insert(0, HERE); import a2_score as A
fam = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'parts_r3', 'sr', 'manifest.csv'), encoding='utf-8')):
    fam['sr__' + os.path.basename(r['out_image'])] = (r['meta'].split('=')[1], r['group_id'], r['split'])
srv = [f for f in A.allf if A.D[f]['src'] == 'sr']
c = collections.Counter()
for f in srv:
    k = fam[f][0]; c[(k, 'images')] += 1; c[(k, 'pothole_gt')] += int((A.D[f]['gc'] == 0).sum()); c[(k, 'bump_gt')] += int((A.D[f]['gc'] == 1).sum())
print('(a) sr val by family:', dict(sorted(c.items())))
rad = [f for f in srv if fam[f][0] == 'rad']
print('    rad val groups:', sorted(set(fam[f][1] for f in rad)))
def show(name, fs):
    r = A.ap50(fs); o = A.op_counts(fs, 0.25)
    v = [r[k][0] for k in (0, 1) if r[k][0] is not None]
    print(f'    {name}: images {len(fs)} | pothole AP50 {r[0][0]} gt {r[0][1]} | bump AP50 {r[1][0]} gt {r[1][1]} | mean {np.mean(v):.6f} | @0.25 pothole TP/FP/FN {o[0][:3]} bump TP/FP/FN {o[1][:3]}')
print('(b) sensitivity (official = with rad):')
show('ALLVAL official', A.allf)
show('ALLVAL minus 32 sr-rad images', [f for f in A.allf if f not in set(rad)])
show('sr official', srv); show('sr rad only', rad); show('sr minus rad (kg+dz)', [f for f in srv if f not in set(rad)])
print('(c) empty-label images (no GT box at all): alarms at conf>=0.25, per source')
for s in A.SRC:
    fs = [f for f in A.allf if A.D[f]['src'] == s and len(A.D[f]['gc']) == 0]
    n = [int(((A.D[f]['det'][:, 4] >= 0.25) & (A.D[f]['det'][:, 5] == k)).sum()) for f in fs for k in (0,)]
    a0 = sum(1 for f in fs if ((A.D[f]['det'][:, 4] >= 0.25) & (A.D[f]['det'][:, 5] == 0)).any())
    a1 = sum(1 for f in fs if ((A.D[f]['det'][:, 4] >= 0.25) & (A.D[f]['det'][:, 5] == 1)).any())
    aa = sum(1 for f in fs if (A.D[f]['det'][:, 4] >= 0.25).any())
    nb = sum(int((A.D[f]['det'][:, 4] >= 0.25).sum()) for f in fs)
    print(f'    {s:7s} empty-label images {len(fs):4d} | with any alarm {aa} (pothole {a0}, bump {a1}) | alarm boxes {nb}')
print('(d) group ids shared between splits, per part (manifest.csv group_id):')
for p in ['rsid', 'bucko', 'sr', 'pol_v2', 'red_v2', 'ng8_v2', 'egy_v2']:
    g = collections.defaultdict(set); n = collections.Counter()
    for r in csv.DictReader(open(os.path.join(ROOT, 'parts_r3', p, 'manifest.csv'), encoding='utf-8')):
        g[r['group_id']].add(r['split']); n[r['split']] += 1
    ng = collections.Counter(s for v in g.values() for s in v)
    print(f'    {p:7s} images {dict(n)} | groups per split {dict(ng)} | groups in >1 split: {sum(1 for v in g.values() if len(v) > 1)} | empty group ids: {sum(1 for k in g if not k)}')

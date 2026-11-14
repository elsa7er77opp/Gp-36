"""Cleanup step A (read-only): size of everything in GP36_AI. Depth 1, plus depth 2 inside runs/detect, review, _archive_2026-11-08,
parts_r3, external_tests, road_hazards_v5_* . Columns: path, MB, files, npy_MB (YOLO disk cache), newest file date. Writes inventory.csv."""
import os, csv, time, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.csv')
if os.path.exists(OUT): sys.exit('inventory.csv exists; refusing to overwrite')
def size(p):
    if os.path.isfile(p):
        st = os.stat(p); return st.st_size, 1, st.st_size if p.endswith('.npy') else 0, st.st_mtime
    b = n = npy = 0; mt = 0
    for dp, dn, fn in os.walk(p):
        for f in fn:
            try: st = os.stat(os.path.join(dp, f))
            except OSError: continue
            b += st.st_size; n += 1; mt = max(mt, st.st_mtime)
            if f.endswith('.npy'): npy += st.st_size
    return b, n, npy, mt
DEEP = {'runs', os.path.join('runs', 'detect'), 'review', '_archive_2026-11-08', 'parts_r3', 'external_tests'}
rows = []
def add(rel, depth):
    p = os.path.join(ROOT, rel); b, n, npy, mt = size(p)
    rows.append([rel, round(b / 1e6, 1), n, round(npy / 1e6, 1), time.strftime('%Y-%m-%d', time.localtime(mt)) if mt else '', depth])
for e in sorted(os.listdir(ROOT)):
    add(e, 1)
    if e in DEEP or e.startswith('road_hazards_v5'):
        for f in sorted(os.listdir(os.path.join(ROOT, e))):
            rel = os.path.join(e, f)
            if rel in DEEP:
                for g in sorted(os.listdir(os.path.join(ROOT, rel))): add(os.path.join(rel, g), 3)
            else: add(rel, 2)
with open(OUT, 'w', newline='', encoding='utf-8') as fo:
    w = csv.writer(fo); w.writerow(['path', 'MB', 'files', 'npy_MB', 'newest', 'depth']); w.writerows(rows)
top = sorted([r for r in rows if r[5] == 1], key=lambda r: -r[1])
print('TOTAL GP36_AI: %.1f GB' % (sum(r[1] for r in top) / 1e3))
for r in top[:40]: print('%9.1f MB  %7d files  npy %8.1f MB  %s  %s' % (r[1], r[2], r[3], r[4], r[0]))
print('INVENTORY OK ->', OUT)

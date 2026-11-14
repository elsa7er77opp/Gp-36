# Copies the ALLVAL / ALLTEST images and labels into review/alldata_v1/ds (new folder; originals untouched),
# so that YOLO's label cache is written inside this new folder and no existing .cache file is overwritten.
import os, shutil, sys
B = 'C:\\Users\\ahmed\\Desktop\\GP36_AI\\'
out = 'review/alldata_v1/ds'
for fn, split in [('review/alldata_v1/allval.txt', 'val'), ('review/alldata_v1/alltest.txt', 'test')]:
    os.makedirs(f'{out}/images/{split}', exist_ok=True); os.makedirs(f'{out}/labels/{split}', exist_ok=True)
    n = 0
    for l in open(fn):
        p = l.strip().replace(B, '').replace('\\', '/')
        parts = p.split('/')
        srcname = 'r2' if parts[0] == 'road_hazards_v3b_C' else parts[1]
        base = os.path.basename(p); stem = os.path.splitext(base)[0]
        dst = f'{out}/images/{split}/{srcname}__{base}'
        lsrc = p.replace('/images/', '/labels/').rsplit('.', 1)[0] + '.txt'
        ldst = f'{out}/labels/{split}/{srcname}__{stem}.txt'
        if not os.path.exists(dst): shutil.copyfile(p, dst)
        if not os.path.exists(ldst): shutil.copyfile(lsrc, ldst)
        n += 1
    print(split, n, flush=True)
print('DONE', flush=True)

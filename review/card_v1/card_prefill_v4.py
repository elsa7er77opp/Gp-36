"""Stage 45j helper: copy the already resized images of road_hazards_card_v1 (same --resize 960 procedure, same raw files)
into road_hazards_card_v4 under their PLACE split, so card_build.py skips them (saves ~35 min). Labels are not copied
(card_build writes them from the raw labels). Read-only on v1; never overwrites."""
import os, re, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
V1, V4 = os.path.join(ROOT, 'road_hazards_card_v1'), os.path.join(ROOT, 'road_hazards_card_v4')
A = json.load(open(os.path.join(HERE, 'place_split_report.json')))['assignment']
n = 0
for sp in ('train', 'val', 'test'):
    for f in os.listdir(os.path.join(V1, 'images', sp)):
        ds, seq, fr = f[:-4].split('__')
        p = 'germany' if ds == 'Germany-Batch1' else re.match(r'[a-z]+', seq.lower()).group()
        dst = os.path.join(V4, 'images', A[p], f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst): shutil.copyfile(os.path.join(V1, 'images', sp, f), dst); n += 1
print('prefilled', n)

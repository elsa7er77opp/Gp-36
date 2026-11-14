"""Stage 45: which CARD class id is pothole and which is speed bump? (read-only on data_card/raw; output stays on the laptop)
Prints per raw class id: box count, median box width/height (normalised), median aspect w/h; and draws sheets
class_check_<id>.jpg with 12 random boxed frames per id for Ahmed to look at. The paper (arXiv 2605.05014, Table 6) has
970 pothole / 755 speed bump boxes in its val split; speed bumps are wide and flat across the lane."""
import os, csv, random, statistics, collections
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, '..', '..', 'data_card', 'raw')
by = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(HERE, 'card_index.csv'), encoding='utf-8')):
    if int(r['label_bytes']) <= 0: continue
    b = os.path.join(RAW, r['dataset'], os.sep.join(p.strip() for p in r['seq'].split('/')))
    lp = os.path.join(b, 'labels', r['frame'] + '.txt')
    if not os.path.exists(lp): continue
    for l in open(lp).read().split('\n'):
        v = l.split()
        if len(v) == 5: by[v[0]].append((os.path.join(b, 'img', 'cam_1', r['frame'] + '.jpg'), *map(float, v[1:])))
for c, L in sorted(by.items()):
    print('class id %s: boxes %d, median w %.3f h %.3f, median w/h %.2f' % (c, len(L), statistics.median(x[3] for x in L), statistics.median(x[4] for x in L), statistics.median(x[3] / max(x[4], 1e-6) for x in L)))
    have = [x for x in L if os.path.exists(x[0])]
    random.Random(0).shuffle(have)
    tiles = []
    for p, x, y, w, h in have[:12]:
        im = Image.open(p).convert('RGB'); W, H = im.size; d = ImageDraw.Draw(im)
        d.rectangle([(x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H], outline=(255, 0, 0), width=12)
        tiles.append(im.resize((480, 480)))
    if tiles:
        sh = Image.new('RGB', (480 * 4, 480 * ((len(tiles) + 3) // 4)))
        for i, t in enumerate(tiles): sh.paste(t, ((i % 4) * 480, (i // 4) * 480))
        out = os.path.join(HERE, 'class_check_%s.jpg' % c)
        if not os.path.exists(out): sh.save(out, quality=85)
        print('  sheet:', out)
    else:
        print('  no images downloaded yet for this id')

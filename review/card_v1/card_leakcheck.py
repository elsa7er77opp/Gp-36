"""Stage 45j: leak check of a built CARD folder (read-only): scene part (top 62 %), 16x16 dHash candidates <= 40 of 256 bits
across splits, verified with ORB + RANSAC (>= 30 inliers). Usage: card_leakcheck.py road_hazards_card_v4. Exit 1 if any confirmed."""
import os, sys, csv, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
V1 = os.path.join(ROOT, sys.argv[1])
items = [dict(sp=sp, f=f, new=sp) for sp in ('train', 'val', 'test') for f in sorted(os.listdir(os.path.join(V1, 'images', sp)))]
# leak check
def load(i):
    im = cv2.imread(os.path.join(V1, 'images', i['sp'], i['f']), cv2.IMREAD_GRAYSCALE)
    return im[: int(im.shape[0] * 0.62)]
def dh16(g):
    a = cv2.resize(g, (17, 16), interpolation=cv2.INTER_AREA).astype(np.int16)
    return np.packbits((a[:, :-1] > a[:, 1:]).flatten())
print('hashing', len(items), flush=True)
H = np.stack([dh16(load(i)) for i in items])
pc = np.array([bin(x).count('1') for x in range(256)], dtype=np.uint16)
S = np.array([i['new'] for i in items])
orb = cv2.ORB_create(1500); bf = cv2.BFMatcher(cv2.NORM_HAMMING)
kp = {}
def feats(k):
    if k not in kp: kp[k] = orb.detectAndCompute(load(items[k]), None)
    return kp[k]
cand = conf = 0; hits = []
for i in range(len(items)):
    d = pc[np.bitwise_xor(H[i + 1:], H[i])].sum(1)
    for j in np.nonzero(d <= 40)[0] + i + 1:
        if S[i] == S[j]: continue
        cand += 1
        k1, d1 = feats(i); k2, d2 = feats(int(j))
        if d1 is None or d2 is None or len(k1) < 30 or len(k2) < 30: continue
        m = [x for x, y in (p for p in bf.knnMatch(d1, d2, k=2) if len(p) == 2) if x.distance < 0.75 * y.distance]
        if len(m) < 30: continue
        A = np.float32([k1[x.queryIdx].pt for x in m]); B = np.float32([k2[x.trainIdx].pt for x in m])
        Hm, mask = cv2.findHomography(A, B, cv2.RANSAC, 5.0)
        if mask is not None and int(mask.sum()) >= 30:
            conf += 1; hits.append((items[i]['f'], S[i], items[int(j)]['f'], S[j], int(d[j - i - 1]), int(mask.sum())))
print('cross-split candidates (dHash16<=40): %d, ORB-confirmed same scene: %d' % (cand, conf), flush=True)
out = os.path.join(HERE, 'leak_check_%s.csv' % sys.argv[1])
with open(out, 'w', newline='') as fo:
    w = csv.writer(fo); w.writerow(['img_a', 'split_a', 'img_b', 'split_b', 'dhash16', 'inliers']); w.writerows(hits)
print('LEAK CHECK ' + ('OK' if conf == 0 else 'FAILED'))
sys.exit(1 if conf else 0)

"""Contact sheets of overlays_sr_speed_bump (GT bump green, GT pothole cyan, pred bump red, pred pothole magenta; preds conf>=0.05)."""
import os, cv2, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); d = os.path.join(H, 'overlays_sr_speed_bump')
fs = sorted(os.listdir(d)); T = 480
for s in range(0, len(fs), 12):
    sheet = np.full((3 * T, 4 * T, 3), 30, np.uint8)
    for i, f in enumerate(fs[s:s + 12]):
        im = cv2.imdecode(np.fromfile(os.path.join(d, f), np.uint8), 1); r = T / max(im.shape[:2])
        im = cv2.resize(im, (int(im.shape[1] * r), int(im.shape[0] * r)))
        y, x = (i // 4) * T, (i % 4) * T; sheet[y:y + im.shape[0], x:x + im.shape[1]] = im
        cv2.putText(sheet, f.split('__')[-1][:8], (x + 4, y + T - 8), 0, 0.5, (255, 255, 255), 1)
    cv2.imwrite(os.path.join(H, 'sheet_sr_bump_%d.jpg' % (s // 12)), sheet)

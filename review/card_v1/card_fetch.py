"""Stage 45: fetch the CARD dataset (huggingface.co/CARD-Data, gated; Ahmed accepted the terms with his own account).
Only the right camera images that have a YOLO label file (cam_1) and the label files are fetched; no LiDAR / depth / raw.
The HF token is typed by Ahmed into a hidden prompt (getpass); it is never printed or saved.
  card_fetch.py list     -> card_index.csv (every cam_1 label file: dataset, sequence, frame, label bytes, image bytes) + summary
  card_fetch.py labels   -> downloads all NON-EMPTY label files (tiny) into data_card/raw/<dataset>/<seq>/labels/
  card_fetch.py images N -> downloads the cam_1 image of every non-empty label frame + every N-th empty frame (negatives);
                            resumable, checks byte size; refuses to overwrite a different existing file.
Sequences whose name starts with 'unused' are skipped (the authors mark them unused)."""
import os, sys, csv, json, getpass, time
import requests
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RAW = os.path.join(ROOT, 'data_card', 'raw')
DS = ['CARD-Germany-Batch1', 'CARD-Germany-Batch2', 'CARD-Germany-Batch3', 'CARD-Italy']
API = 'https://huggingface.co/api/datasets/CARD-Data/%s/tree/main/%s'
RES = 'https://huggingface.co/datasets/CARD-Data/%s/resolve/main/%s'
IDX = os.path.join(HERE, 'card_index.csv')
S = requests.Session()
def auth():
    tok = os.environ.get('HF_TOKEN') or getpass.getpass('Paste your Hugging Face READ token (hidden, not saved): ').strip()
    S.headers['Authorization'] = 'Bearer ' + tok
def get(url, **kw):
    for k in range(6):
        r = S.get(url, timeout=60, **kw)
        if r.status_code == 429:
            time.sleep(int(r.headers.get('retry-after', '30')) + 1); continue
        return r
    r.raise_for_status()
def tree(d, path, missing_ok=False):
    out, url = [], API % (d, requests.utils.quote(path))
    while url:
        r = get(url)
        if r.status_code == 404 and missing_ok: print('  (no folder %s - skipped)' % path); return []
        if r.status_code != 200: sys.exit('HTTP %d for %s (access not granted yet?)' % (r.status_code, url))
        out += r.json(); url = r.links.get('next', {}).get('url')
    return out
def do_list():
    if os.path.exists(IDX): sys.exit(IDX + ' exists; refusing to overwrite')
    rows = []
    for d in DS:
        for reg in [x['path'] for x in tree(d, '') if x['type'] == 'directory']:
            for seq in [x['path'] for x in tree(d, reg) if x['type'] == 'directory']:
                name = seq.split('/')[-1]
                if name.startswith('unused'): print('skip', d, name); continue
                lab = {x['path'].split('/')[-1][:-4]: x['size'] for x in tree(d, seq + '/labels', True) if x['type'] == 'file' and x['path'].endswith('.txt')}
                img = {x['path'].split('/')[-1][:-4]: x['size'] for x in tree(d, seq + '/img/cam_1', True) if x['type'] == 'file'}
                for fr, lb in sorted(lab.items()):
                    rows.append([d, seq, fr, lb, img.get(fr, -1)])
                n = sum(1 for fr in lab if lab[fr] > 0)
                print('%-22s %-40s labels %5d  non-empty %5d  cam_1 images %5d' % (d, name, len(lab), n, len(img)))
    with open(IDX, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['dataset', 'seq', 'frame', 'label_bytes', 'image_bytes']); w.writerows(rows)
    ne = [r for r in rows if r[3] > 0]
    print('SUMMARY: sequences %d, label files %d, non-empty %d, non-empty with image %d, their images %.2f GB, all cam_1 images %.2f GB'
          % (len(set((r[0], r[1]) for r in rows)), len(rows), len(ne), sum(r[4] > 0 for r in ne),
             sum(r[4] for r in ne if r[4] > 0) / 1e9, sum(r[4] for r in rows if r[4] > 0) / 1e9))
def fetch(d, path, dst, size):
    if os.path.exists(dst):
        if size < 0 or os.path.getsize(dst) == size: return 0
        raise RuntimeError('DIFFERENT file exists, refusing: ' + dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    r = get(RES % (d, requests.utils.quote(path)))
    if r.status_code != 200: raise RuntimeError('HTTP %d for %s' % (r.status_code, path))
    if size >= 0 and len(r.content) != size: raise RuntimeError('size mismatch ' + path)
    tmp = dst + '.part'
    open(tmp, 'wb').write(r.content); os.replace(tmp, dst); return 1
def rows():
    return [r for r in csv.DictReader(open(IDX, encoding='utf-8'))]
def run_parallel(jobs, what):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    n = done = 0; errs = []
    with ThreadPoolExecutor(16) as ex:
        fs = [ex.submit(fetch, *j) for j in jobs]
        for f in as_completed(fs):
            done += 1
            try: n += f.result()
            except BaseException as e: errs.append(str(e))
            if done % 500 == 0: print('%s %d / %d' % (what, done, len(jobs)), flush=True)
    print('%s downloaded now: %d, errors: %d' % (what, n, len(errs)))
    if errs: print('\n'.join(errs[:20])); sys.exit('SOME DOWNLOADS FAILED - run again to resume')
def do_labels():
    jobs = [(r['dataset'], r['seq'] + '/labels/' + r['frame'] + '.txt', os.path.join(RAW, r['dataset'], os.sep.join(p.strip() for p in r['seq'].split('/')), 'labels', r['frame'] + '.txt'), int(r['label_bytes']))
            for r in rows() if int(r['label_bytes']) > 0]
    run_parallel(jobs, 'labels')
def do_images(every):
    sel, k = [], 0
    for r in rows():
        if int(r['image_bytes']) <= 0: continue
        if int(r['label_bytes']) > 0: sel.append(r)
        else:
            k += 1
            if every > 0 and k % every == 0: sel.append(r)
    gb = sum(int(r['image_bytes']) for r in sel) / 1e9
    print('selected images: %d (%.2f GB)' % (len(sel), gb))
    run_parallel([(r['dataset'], r['seq'] + '/img/cam_1/' + r['frame'] + '.jpg', os.path.join(RAW, r['dataset'], os.sep.join(p.strip() for p in r['seq'].split('/')), 'img', 'cam_1', r['frame'] + '.jpg'), int(r['image_bytes'])) for r in sel], 'images')
    print('IMAGES OK')
if __name__ == '__main__':
    m = sys.argv[1] if len(sys.argv) > 1 else 'list'
    auth()
    {'list': do_list, 'labels': do_labels}.get(m, lambda: do_images(int(sys.argv[2]) if len(sys.argv) > 2 else 0))()

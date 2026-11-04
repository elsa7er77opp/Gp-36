"""Minimal Kaggle dataset client (list files / download) that never prints or stores the token.

    python -I tools/kaggle_dl.py files <owner/slug>
    python -I tools/kaggle_dl.py download <owner/slug> <new_dir>

The token is read from %USERPROFILE%\\.kaggle\\access_token (or env KAGGLE_API_TOKEN) and only sent in the
Authorization header to www.kaggle.com. The download goes to <new_dir>/<slug>.zip (resumable via a .part file);
<new_dir> must not exist yet unless it holds that .part file. Unzip with tools/intake_zip.py.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://www.kaggle.com/api/v1"


def token():
    t = os.environ.get("KAGGLE_API_TOKEN")
    if not t:
        p = Path(os.environ["USERPROFILE"]) / ".kaggle" / "access_token"
        t = p.read_text(encoding="ascii").strip() if p.exists() else ""
    if not t:
        sys.exit("no Kaggle token found")
    return t


def req(url, extra=None):
    h = {"Authorization": f"Bearer {token()}", "User-Agent": "gp36-kaggle-dl"}
    h.update(extra or {})
    return urllib.request.Request(url, headers=h)


def main():
    cmd, ref = sys.argv[1], sys.argv[2]
    if cmd == "files":
        with urllib.request.urlopen(req(f"{API}/datasets/list/{ref}"), timeout=60) as r:
            d = json.load(r)
        files = d.get("datasetFiles", d if isinstance(d, list) else [])
        print(f"{ref}: {len(files)} files listed (first page)")
        for f in files[:15]:
            print(" ", f.get("name"), f.get("totalBytes"))
        return
    out = Path(sys.argv[3])
    zp = out / f"{ref.split('/')[1]}.zip"
    part = zp.with_suffix(".zip.part")
    if out.exists() and not part.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    out.mkdir(parents=True, exist_ok=True)
    for attempt in range(8):
        have = part.stat().st_size if part.exists() else 0
        try:
            r = urllib.request.urlopen(req(f"{API}/datasets/download/{ref}", {"Range": f"bytes={have}-"} if have else None),
                                       timeout=120)
        except urllib.error.HTTPError as e:
            if e.code == 416:  # already complete
                break
            raise
        with r, open(part, "ab" if have and r.status == 206 else "wb") as f:
            total = r.headers.get("Content-Length")
            t0, n = time.time(), 0
            try:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
                    n += len(b)
            except Exception as e:  # noqa: BLE001
                print(f"attempt {attempt}: interrupted after {n} bytes ({e}); resuming", flush=True)
                continue
        print(f"downloaded {n} bytes ({total} announced) in {time.time() - t0:.0f} s", flush=True)
        break
    os.replace(part, zp)
    print(f"{zp} {zp.stat().st_size} bytes")


if __name__ == "__main__":
    main()

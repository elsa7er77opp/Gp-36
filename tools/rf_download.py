"""Download one Roboflow dataset version export (zip) without printing or storing the API key.

    set ROBOFLOW_API_KEY=<private key>          (Roboflow > Settings > API Keys; NOT the publishable rf_ key)
    python -I tools/rf_download.py refyy-i/rdd-6706t-8szyz 1 ..\\GP36_Dataset\\raw_v3\\rf_egyrdd [--format yolov8]

The key is read from ROBOFLOW_API_KEY (or roboflow_api_token, or the file ~/.roboflow/api_key) and sent only to api.roboflow.com. The REST call
GET https://api.roboflow.com/<workspace>/<project>/<version>/<format>?api_key=... returns a signed export link,
which is downloaded to <out>/export.zip and unzipped into <out>/x (the layout every cloud command assumes).
<out> must not exist yet. The signed link is not printed (it works without the key for a while).
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def key():
    k = os.environ.get("ROBOFLOW_API_KEY") or os.environ.get("roboflow_api_token") or ""
    kf = Path.home() / ".roboflow" / "api_key"  # laptop: a one-line file outside the repo (like ~/.kaggle)
    if not k and kf.exists():
        k = kf.read_text(encoding="utf-8-sig").strip()
    if not k:
        sys.exit(f"set ROBOFLOW_API_KEY or put the private key in {kf}")
    if k.startswith("rf_"):
        sys.exit("this is a publishable rf_ key; dataset exports need the PRIVATE API key")
    return k


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fmt = sys.argv[sys.argv.index("--format") + 1] if "--format" in sys.argv else "yolov8"
    if "--format" in sys.argv:
        args.remove(fmt)
    if len(args) != 3:
        sys.exit(__doc__)
    ref, ver, out = args[0], args[1], Path(args[2])
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    url = f"https://api.roboflow.com/{ref}/{ver}/{fmt}?" + urllib.parse.urlencode({"api_key": key()})
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "gp36"}), timeout=120) as r:
        d = json.load(r)
    link = (d.get("export") or {}).get("link")
    if not link:
        sys.exit(f"no export link yet (export may still be generating); keys in reply: {sorted(d)}")
    out.mkdir(parents=True)
    zp = out / "export.zip"
    with urllib.request.urlopen(urllib.request.Request(link, headers={"User-Agent": "gp36"}), timeout=600) as r, open(zp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():  # refuse path traversal
            if n.startswith("/") or ".." in Path(n).parts:
                sys.exit(f"unsafe path in zip: {n}")
        z.extractall(out / "x")
    zp.unlink()
    n_img = sum(1 for p in (out / "x").rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    print(f"{ref} v{ver} {fmt}: {n_img} images -> {out / 'x'}")


if __name__ == "__main__":
    main()

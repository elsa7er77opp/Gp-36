"""Download Egyptian Mapillary tiles (egm) from the Hugging Face mirror and extract them. Stdlib only, no token.

    python -I tools/egm_download.py --tiles 390_375 391_375 --out ..\\GP36_Dataset\\raw_v3\\egm

Source: huggingface.co/datasets/masterofaudio2077/egyptian-streets (mirror of Mapillary images; treat as
CC BY-SA 4.0, "(c) Mapillary contributors", see review/new_data_r3/vet/egm/README.md).
For every tile it lists data/<tile>/ through the public HF API, downloads each r*.tar to <out>/_tar/<tile>/
(resumes a partial file, checks the size against the API), then extracts it into <out>/<tile>_<r>/.
Nothing is deleted: the tar files are kept. An already-extracted folder is skipped. Prints a summary.
"""
import argparse
import json
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

REPO = "masterofaudio2077/egyptian-streets"
API = f"https://huggingface.co/api/datasets/{REPO}/tree/main/data/"
RES = f"https://huggingface.co/datasets/{REPO}/resolve/main/data/"


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "gp36-egm"}), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url, dst, size):
    dst.parent.mkdir(parents=True, exist_ok=True)
    have = dst.stat().st_size if dst.exists() else 0
    if have == size:
        return "ok (already)"
    req = urllib.request.Request(url, headers={"User-Agent": "gp36-egm", "Range": f"bytes={have}-"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dst, "ab" if have else "wb") as f:
        done = have
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            done += len(b)
            print(f"\r  {dst.name}: {done / 1e9:.2f} / {size / 1e9:.2f} GB", end="", flush=True)
    print()
    got = dst.stat().st_size
    if got != size:
        raise IOError(f"size mismatch for {dst}: {got} != {size}")
    return "downloaded"


def download_retry(url, dst, size, tries=8):
    """The connection sometimes drops mid-file; resume from the partial file up to `tries` times."""
    for k in range(tries):
        try:
            return download(url, dst, size)
        except (IOError, OSError) as e:  # urllib errors are OSError subclasses
            print(f"  retry {k + 1}/{tries}: {e}")
            time.sleep(5)
    sys.exit(f"giving up on {dst} after {tries} tries (run again to resume)")


def safe_extract(tar_path, out_dir):
    with tarfile.open(tar_path) as t:
        base = out_dir.resolve()
        for m in t.getmembers():
            p = (out_dir / m.name).resolve()
            if not str(p).startswith(str(base)) or m.issym() or m.islnk():
                sys.exit(f"unsafe member {m.name} in {tar_path}")
        t.extractall(out_dir, filter="data") if hasattr(tarfile, "data_filter") else t.extractall(out_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    total = {"tars": 0, "bytes": 0, "jpg": 0}
    for tile in a.tiles:
        files = [f for f in get_json(API + tile) if f.get("type") == "file" and f["path"].endswith(".tar")]
        if not files:
            sys.exit(f"no tar files listed for tile {tile}")
        for f in sorted(files, key=lambda x: x["path"]):
            name = Path(f["path"]).name
            size = int(f.get("lfs", {}).get("size") or f["size"])
            tar = out / "_tar" / tile / name
            print(f"{tile}/{name}: {download_retry(RES + tile + '/' + name, tar, size)}")
            ex = out / f"{tile}_{Path(name).stem}"
            if not ex.exists():
                ex.mkdir(parents=True)
                safe_extract(tar, ex)
            total["tars"] += 1
            total["bytes"] += size
            total["jpg"] += len(list(ex.rglob("*.jpg")))
    print(json.dumps({"tiles": a.tiles, "tars": total["tars"], "GB": round(total["bytes"] / 1e9, 2), "jpg": total["jpg"]}))


if __name__ == "__main__":
    main()

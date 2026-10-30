"""Extract selected RDD2022 countries from the Figshare download. Read-only on the zip.

Layout of the Figshare file (verified 2026-10-30): outer zip (stored) -> RDD2022_released_through_CRDDC2022.zip
(stored) -> RDD2022/<Country>.zip (stored) -> <Country>/train/{images,annotations/xmls}, <Country>/test/images.
Stored members are read in place through seekable windows (no temporary copies).

    python tools/extract_rdd2022.py --zip "<Downloads>\\21431547 (1).zip" --out ..\\GP36_Dataset\\raw_v3\\RDD2022

Only <Country>/train images + xmls of the chosen countries are written (test has no labels).
Resumable: writes into <out>.partial, skips files already written with the right size, stops after
--time-budget seconds (run again to continue); renames to <out> when complete. Refuses an existing <out>.
"""
import argparse, io, json, os, shutil, struct, sys, time, zipfile
from pathlib import Path

COUNTRIES = ["Japan", "India", "Czech", "United_States", "China_MotorBike"]


class Window(io.RawIOBase):
    def __init__(self, f, start, size):
        self.f, self.start, self.size, self.pos = f, start, size, 0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos
    def readinto(self, b):
        n = max(0, min(len(b), self.size - self.pos))
        if n == 0: return 0
        self.f.seek(self.start + self.pos)
        data = self.f.read(n); b[:len(data)] = data; self.pos += len(data)
        return len(data)


def _data_start(f, base, info):
    f.seek(base + info.header_offset)
    h = f.read(30)
    if h[:4] != b"PK\x03\x04": raise SystemExit("bad local header")
    n, x = struct.unpack("<HH", h[26:30])
    return base + info.header_offset + 30 + n + x


def open_stored_member(f, base, info):
    if info.compress_type != zipfile.ZIP_STORED:
        raise SystemExit(f"{info.filename} is compressed; extract it with another tool first")
    s = _data_start(f, base, info)
    return zipfile.ZipFile(io.BufferedReader(Window(f, s, info.file_size), 1 << 20)), s


def country_zips(path, countries):
    """Yield (country, ZipFile) for each wanted country, descending through stored nested zips."""
    f = open(path, "rb")
    level = [(zipfile.ZipFile(path), 0)]
    while level:
        z, base = level.pop()
        for i in z.infolist():
            name = i.filename.replace("\\", "/").rstrip("/").split("/")[-1]
            if not name.lower().endswith(".zip"): continue
            stem = name[:-4]
            if stem in countries:
                yield stem, open_stored_member(f, base, i)[0]
            elif stem not in ("Norway", "China_Drone") and not any(stem == c for c in countries):
                level.append(open_stored_member(f, base, i))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--countries", default=",".join(COUNTRIES))
    ap.add_argument("--time-budget", type=float, default=1e12)
    ap.add_argument("--only-with", default="", help="extract only images whose XML contains this object name (e.g. D40); "
                    "all XMLs are still scanned in memory and their object names counted in the report")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        print("refusing: output exists", out); return 2
    tmp = out.with_name(out.name + ".partial"); tmp.mkdir(parents=True, exist_ok=True)
    countries = [c.strip() for c in a.countries.split(",") if c.strip()]
    t0, counts, done_all = time.time(), {}, True
    for country, cz in country_zips(a.zip, countries):
        c = counts.setdefault(country, {"images": 0, "xmls": 0, "skipped_existing": 0})
        keep = None
        if a.only_with:
            import re
            names, keep, nx = {}, set(), 0
            for i in cz.infolist():
                q = i.filename.replace("\\", "/").split("/")
                if "train" in q and q[-2] == "xmls" and q[-1].lower().endswith(".xml"):
                    nx += 1
                    found = re.findall(r"<name>\s*([^<]+?)\s*</name>", cz.read(i).decode("utf-8", "replace"))
                    for n in found: names[n] = names.get(n, 0) + 1
                    if a.only_with in found: keep.add(q[-1].rsplit(".", 1)[0])
            c.update({"all_train_xmls": nx, "object_names": names, "selected_stems": len(keep)})
        for i in cz.infolist():
            if i.is_dir(): continue
            p = i.filename.replace("\\", "/").split("/")
            if "train" not in p: continue
            sub = "xmls" if p[-2] == "xmls" else ("images" if p[-2] == "images" else None)
            if sub is None: continue
            if keep is not None and p[-1].rsplit(".", 1)[0] not in keep: continue
            dst = tmp / country / sub / p[-1]
            if dst.exists() and dst.stat().st_size == i.file_size:
                c[sub] += 1; c["skipped_existing"] += 1; continue
            if time.time() - t0 > a.time_budget:
                done_all = False; break
            dst.parent.mkdir(parents=True, exist_ok=True)
            with cz.open(i) as src, open(dst, "wb") as fo:
                shutil.copyfileobj(src, fo, 1 << 20)
            c[sub] += 1
        if not done_all: break
    if not done_all:
        print("time budget reached - run again to continue:", json.dumps(counts)); return 3
    missing = [c for c in countries if c not in counts]
    if missing:
        print("countries not found in zip:", missing); return 4
    rep = {"zip": str(a.zip), "zip_size": os.path.getsize(a.zip), "countries": counts}
    (tmp / "extract_report.json").write_text(json.dumps(rep, indent=1))
    os.replace(tmp, out)
    print(json.dumps(rep, indent=1)); return 0


if __name__ == "__main__":
    sys.exit(main())

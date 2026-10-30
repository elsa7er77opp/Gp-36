"""Reproduce independent-audit issues 1, 2 and 4 on synthetic data (writes only to a temp dir)."""
import sys, tempfile, shutil, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from helpers import save, smooth_image, write_label
from gp36data.build import build_dataset, BuildError, MARKER
from gp36data.verify import verify_dataset

def make_ok(root):
    recs = []
    src = root / "src"
    for k, s in enumerate(["train", "train", "val", "test"]):
        img = save(smooth_image(200 + k), src / f"i{k}.jpg")
        lbl = write_label(src / f"i{k}.txt", "0 0.5 0.5 0.2 0.1\n")
        recs.append({"sample_id": f"s{k}", "source": "fx", "split": s, "image": img, "label": lbl, "class_map": {0: "pothole"}})
    build_dataset(recs, root / "ds", check_near_dups=False)
    return root / "ds"

def res(name, rep):
    print(f"{name:55s} -> {'PASS' if not rep['errors'] else 'FAIL'}  {rep['errors'][:2]}")

d = Path(tempfile.mkdtemp())
ds = make_ok(d); res("baseline built dataset", verify_dataset(ds, check_near_dups=False))
for split in ("train", "val", "test"):
    c = d / f"miss_{split}"; shutil.copytree(ds, c)
    shutil.rmtree(c / "images" / split); shutil.rmtree(c / "labels" / split)
    res(f"ISSUE1 missing split '{split}' (images+labels)", verify_dataset(c, check_near_dups=False))
c = d / "miss_lbldir"; shutil.copytree(ds, c); shutil.rmtree(c / "labels" / "val")
res("ISSUE1 labels/val dir missing", verify_dataset(c, check_near_dups=False))
c = d / "no_ck"; shutil.copytree(ds, c); (c / "checksums.sha256").unlink()
res("ISSUE2 checksums.sha256 deleted", verify_dataset(c, check_near_dups=False))
c = d / "bad_ck"; shutil.copytree(ds, c); (c / "checksums.sha256").write_text("garbage-line\n")
try: res("ISSUE2 malformed checksum line", verify_dataset(c, check_near_dups=False))
except Exception as e: print(f"{'ISSUE2 malformed checksum line':55s} -> CRASH {type(e).__name__}: {e}")
c = d / "out_ck"; shutil.copytree(ds, c); (c / "checksums.sha256").write_text((c / "checksums.sha256").read_text() + "0"*64 + "  ../outside.txt\n"); (d / "outside.txt").write_text("x")
res("ISSUE2 checksum entry outside root (../)", verify_dataset(c, check_near_dups=False))
c = d / "extra_file"; shutil.copytree(ds, c); save(smooth_image(999), c / "images" / "train" / "extra.jpg"); write_label(c / "labels" / "train" / "extra.txt", "")
res("ISSUE2 unlisted extra image+label added", verify_dataset(c, check_near_dups=False))
c = d / "dup_ck"; shutil.copytree(ds, c); t = (c / "checksums.sha256").read_text().splitlines(); (c / "checksums.sha256").write_text("\n".join(t + t[:1]) + "\n")
res("ISSUE2 duplicate checksum record", verify_dataset(c, check_near_dups=False))
c = d / "miss_test_no_ck"; shutil.copytree(ds, c); shutil.rmtree(c / "images" / "test"); shutil.rmtree(c / "labels" / "test"); (c / "checksums.sha256").unlink()
for _m in ("strict", "legacy"):
    try: res(f"ISSUE1 missing 'test' AND no checksums [{_m}]", verify_dataset(c, check_near_dups=False, mode=_m))
    except TypeError: res("ISSUE1 missing 'test' AND no checksums [old code]", verify_dataset(c, check_near_dups=False)); break
# ISSUE 4: a stale temp folder that has the marker but also foreign content
tmp = d / ".ds2.building"; tmp.mkdir(); (tmp / MARKER).write_text("x"); (tmp / "USER_NOTES.docx").write_text("important user file")
recs = [{"sample_id": "z", "source": "fx", "split": "train", "image": save(smooth_image(7), d / "z.jpg"), "label": write_label(d / "z.txt", "0 0.5 0.5 0.1 0.1\n"), "class_map": {0: "pothole"}}]
try:
    build_dataset(recs, d / "ds2", check_near_dups=False); print("ISSUE4 build over marked temp with foreign file -> build ran")
except BuildError as e: print("ISSUE4 -> BuildError", e)
print("ISSUE4 foreign file still exists after build:", (tmp / "USER_NOTES.docx").exists())
shutil.rmtree(d)

"""tools/build_part.py end to end on a tiny synthetic source: class map + ignore, unmapped id = hard error,
FAR_TINY removal / drop, leakage guard vs the internal set (exact and re-encoded copy), within-part guard."""
import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, save, smooth_image, write_label
from PIL import Image

from gp36data.manifest import sha256_file

TOOL = ROOT / "tools" / "build_part.py"


class TestBuildPart(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # internal frozen dataset with 2 images (one per split we protect)
        self.internal = self.tmp / "internal"
        rows = []
        for k, sp in enumerate(["val", "test"]):
            p = save(smooth_image(900 + k), self.internal / "images" / sp / f"int{k}.jpg")
            s = sha256_file(p)
            rows.append({"split": sp, "sample_id": f"int/{k}", "out_image": f"images/{sp}/int{k}.jpg",
                         "out_sha256": s, "orig_sha256": s})
        with open(self.internal / "manifest.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        self.src = self.tmp / "src"
        self.items = []

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def add(self, name, im, label, split="train", cmap=None, group="g"):
        img = save(im, self.src / f"{name}.jpg")
        lbl = write_label(self.src / f"{name}.txt", label)
        self.items.append({"image": str(img), "label": str(lbl),
                           "class_map": json.dumps(cmap or {"0": "pothole", "1": "ignore", "2": "speed_bump"}),
                           "group": group, "part_split": split, "meta": "fam=t"})

    def build(self, *extra):
        it = self.tmp / "items.csv"
        with open(it, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["image", "label", "class_map", "group", "part_split", "meta"])
            w.writeheader()
            w.writerows(self.items)
        out = self.tmp / "part"
        r = subprocess.run([sys.executable, "-I", str(TOOL), "--items", str(it), "--part", "t", "--out", str(out),
                            "--internal", str(self.internal), "--hash-cache", str(self.tmp / "cache.npz"), *extra],
                           capture_output=True, text=True)
        return r, out

    def drops(self, out):
        return {Path(r["image"]).stem: r["reason"] for r in csv.DictReader(open(out / "drop_log.csv", encoding="utf-8"))}

    def test_full_gate(self):
        self.add("ok", smooth_image(1), "0 0.5 0.5 0.2 0.2\n1 0.3 0.3 0.1 0.1\n2 0.5 0.8 0.5 0.05\n")
        self.add("tinyonly", smooth_image(2), "0 0.5 0.5 0.01 0.01\n")              # sqrt(1e-4)=0.01 < 0.02
        self.add("tinymix", smooth_image(3), "0 0.5 0.5 0.01 0.01\n2 0.5 0.7 0.4 0.1\n")
        self.add("ignoreonly", smooth_image(4), "1 0.5 0.5 0.3 0.3\n")             # manhole only -> negative
        self.add("leak_exact", smooth_image(0), "0 0.5 0.5 0.2 0.2\n")
        shutil.copyfile(self.internal / "images/val/int0.jpg", self.src / "leak_exact.jpg")  # byte-identical
        buf = io.BytesIO()
        Image.open(self.internal / "images/test/int1.jpg").transpose(Image.FLIP_LEFT_RIGHT).resize((200, 150)).save(buf, "JPEG", quality=40)
        self.add("leak_flip", Image.open(io.BytesIO(buf.getvalue())), "0 0.5 0.5 0.2 0.2\n")
        self.add("held", smooth_image(5), "2 0.5 0.5 0.3 0.1\n", split="val", group="h")
        self.add("trcopy", smooth_image(5).resize((300, 225)), "2 0.5 0.5 0.3 0.1\n", split="train")
        r, out = self.build()
        self.assertEqual(r.returncode, 0, r.stderr)
        info = json.loads((out / "build_info.json").read_text(encoding="utf-8"))
        d = self.drops(out)
        self.assertEqual(d["tinyonly"], "only_far_tiny")
        self.assertEqual(d["leak_exact"], "exact_dup_internal")
        self.assertEqual(d["leak_flip"], "near_dup_internal")
        self.assertEqual(d["trcopy"], "near_dup_part_heldout")
        self.assertEqual(info["far_tiny_boxes_removed"], 1)
        self.assertEqual(info["ignored_boxes_removed"], 2)
        tr = info["splits"]["train"]
        self.assertEqual((tr["images"], tr["negatives"], tr["pothole_boxes"], tr["speed_bump_boxes"]), (3, 1, 1, 2))
        self.assertEqual(info["splits"]["val"]["speed_bump_boxes"], 1)
        # labels are written with TARGET ids (pothole 0, speed_bump 1) and no ignore boxes
        man = {r["sample_id"]: r for r in csv.DictReader(open(out / "manifest.csv", encoding="utf-8"))}
        ok = man["t/ok.jpg"]
        lines = (out / "labels" / "train" / (Path(ok["out_image"]).stem + ".txt")).read_text().split("\n")
        self.assertEqual(sorted(ln.split()[0] for ln in lines if ln), ["0", "1"])
        self.assertTrue(ok["out_image"].startswith("images/train/t__"))
        self.assertFalse((self.tmp / "part.building").exists())

    def test_unmapped_class_is_hard_error(self):
        self.add("x", smooth_image(7), "5 0.5 0.5 0.2 0.2\n")
        r, out = self.build()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not in class_map", r.stderr)
        self.assertFalse(out.exists())

    def test_far_tiny_threshold_is_configurable(self):
        self.add("x", smooth_image(8), "0 0.5 0.5 0.03 0.03\n")
        r, out = self.build("--far-tiny", "0.05")
        self.assertEqual(self.drops(out).get("x"), "only_far_tiny")

    def test_guard_protects_extra_eval_set(self):
        ext = self.tmp / "ext"
        save(smooth_image(77), ext / "images" / "e.jpg")
        self.add("x", smooth_image(0), "0 0.5 0.5 0.2 0.2\n")
        shutil.copyfile(ext / "images" / "e.jpg", self.src / "x.jpg")
        r, out = self.build("--guard", str(ext))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.drops(out)["x"], "exact_dup_internal")

    def test_refuses_existing_output(self):
        self.add("x", smooth_image(9), "0 0.5 0.5 0.2 0.2\n")
        (self.tmp / "part").mkdir()
        r, _ = self.build()
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()

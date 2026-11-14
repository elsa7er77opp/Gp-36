"""tools/apply_box_corrections.py: removal policy per split, sha check, unmatched rows, no overwrite."""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, save, smooth_image, write_label

TOOL = ROOT / "tools" / "apply_box_corrections.py"
FIELDS = ["sample_id", "source", "split", "orig_image", "orig_label", "orig_sha256", "out_image", "out_sha256", "out_w",
          "out_h", "n_pothole", "n_speed_bump", "group_id", "part", "meta"]


class TestApply(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.raw, self.part = self.tmp / "raw", self.tmp / "part"
        rows = []
        # original labels: class 0 crack (ignored in the part), class 1 pothole
        spec = {"a": ("train", "0 0.1 0.1 0.05 0.05\n1 0.5 0.5 0.2 0.2\n1 0.3 0.7 0.1 0.1\n"),
                "b": ("val", "1 0.4 0.4 0.2 0.2\n1 0.6 0.8 0.1 0.1\n"),
                "c": ("test", "1 0.5 0.5 0.3 0.3\n")}
        for k, (name, (split, lab)) in enumerate(spec.items()):
            img = save(smooth_image(k), self.raw / f"{name}.jpg")
            lbl = write_label(self.raw / f"{name}.txt", lab)
            out_img = f"images/{split}/p__{name}.jpg"
            save(smooth_image(k), self.part / out_img)
            part_lines = "".join(f"0 {ln.split(None, 1)[1]}\n" for ln in lab.splitlines() if ln.startswith("1 "))
            write_label(self.part / "labels" / split / f"p__{name}.txt", part_lines)
            rows.append({"sample_id": f"p/{name}.jpg", "source": "p", "split": split, "orig_image": str(img),
                         "orig_label": str(lbl), "orig_sha256": "x", "out_image": out_img, "out_sha256": "x", "out_w": 320,
                         "out_h": 240, "n_pothole": part_lines.count("\n"), "n_speed_bump": 0, "group_id": "g", "part": "p",
                         "meta": ""})
        with open(self.part / "manifest.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        (self.part / "data.yaml").write_text("names: {0: pothole, 1: speed_bump}\n", encoding="utf-8")
        self.sha = {n: hashlib.sha256((self.raw / f"{n}.txt").read_bytes()).hexdigest() for n in "abc"}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def audit(self, rows):
        p = self.tmp / "audit.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["file", "label_sha256", "line", "class_id", "verdict", "note"])
            w.writeheader()
            for fn, line, verdict in rows:
                w.writerow({"file": f"{fn}.jpg", "label_sha256": self.sha[fn], "line": line, "class_id": "1",
                            "verdict": verdict, "note": ""})
        return p

    def run_tool(self, audit, out="v2"):
        return subprocess.run([sys.executable, "-I", str(TOOL), "--part", str(self.part), "--audit", str(audit),
                               "--out", str(self.tmp / out)], capture_output=True, text=True)

    def labels(self, split, name, out="v2"):
        return (self.tmp / out / "labels" / split / f"p__{name}.txt").read_text(encoding="utf-8").splitlines()

    def test_policy(self):
        a = self.audit([("a", 1, "remove_manhole"), ("a", 2, "uncertain"), ("b", 0, "uncertain"), ("b", 1, "keep"),
                        ("c", 0, "remove_not_pothole")])
        r = self.run_tool(a)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.labels("train", "a"), ["0 0.3 0.7 0.1 0.1"])      # manhole removed, uncertain kept in train
        self.assertEqual(self.labels("val", "b"), ["0 0.6 0.8 0.1 0.1"])        # uncertain removed in val
        self.assertEqual(self.labels("test", "c"), [])                          # image kept as negative
        info = json.loads((self.tmp / "v2" / "build_info.json").read_text(encoding="utf-8"))
        self.assertEqual(info["splits"]["test"]["negatives"], 1)
        self.assertEqual(info["splits"]["train"]["pothole_boxes"], 1)
        self.assertEqual(info["splits"]["test"]["changes"]["images_now_negative"], 1)
        log = list(csv.DictReader(open(self.tmp / "v2" / "change_log.csv", encoding="utf-8")))
        self.assertEqual(len(log), 5)
        man = {m["sample_id"]: m for m in csv.DictReader(open(self.tmp / "v2" / "manifest.csv", encoding="utf-8"))}
        self.assertEqual(man["p/c.jpg"]["n_pothole"], "0")
        self.assertTrue((self.tmp / "v2" / "images" / "test" / "p__c.jpg").exists())
        # the source part is untouched
        self.assertEqual(len((self.part / "labels" / "test" / "p__c.txt").read_text().splitlines()), 1)
        self.assertIn("checksums.sha256", {p.name for p in (self.tmp / "v2").iterdir()})

    def test_sha_mismatch_writes_nothing(self):
        a = self.audit([("a", 1, "remove_manhole")])
        (self.raw / "a.txt").write_text("1 0.5 0.5 0.2 0.2\n", encoding="utf-8")  # label changed after the audit
        r = self.run_tool(a)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("label_sha256 mismatch", r.stderr)
        self.assertFalse((self.tmp / "v2").exists())

    def test_wrong_class_or_line_is_error(self):
        a = self.audit([("a", 0, "remove_manhole")])  # line 0 is the crack (class 0), audit says class 1
        r = self.run_tool(a)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.tmp / "v2").exists())

    def test_unknown_verdict_is_error(self):
        a = self.audit([("a", 1, "resize")])
        self.assertNotEqual(self.run_tool(a).returncode, 0)

    def drop_csv(self, names):
        p = self.tmp / "drop.csv"
        p.write_text("file,split,what,note\n" + "".join(f"{n}.jpg,x,pothole,\n" for n in names), encoding="utf-8")
        return p

    def test_drop_images_valtest_only(self):
        a = self.audit([("a", 1, "keep")])
        r = subprocess.run([sys.executable, "-I", str(TOOL), "--part", str(self.part), "--audit", str(a), "--out",
                            str(self.tmp / "v2"), "--drop-images", str(self.drop_csv(["a", "b"]))], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.tmp / "v2" / "images" / "train" / "p__a.jpg").exists())   # train never dropped
        self.assertFalse((self.tmp / "v2" / "images" / "val" / "p__b.jpg").exists())
        man = [m["sample_id"] for m in csv.DictReader(open(self.tmp / "v2" / "manifest.csv", encoding="utf-8"))]
        self.assertNotIn("p/b.jpg", man)
        info = json.loads((self.tmp / "v2" / "build_info.json").read_text(encoding="utf-8"))
        self.assertEqual(info["images_dropped_valtest"], ["images/val/p__b.jpg"])
        self.assertEqual(info["splits"]["val"]["images"], 0)
        log = list(csv.DictReader(open(self.tmp / "v2" / "change_log.csv", encoding="utf-8")))
        self.assertEqual(sum(x["verdict"] == "drop_image" for x in log), 2)

    def test_drop_images_unknown_file_is_error(self):
        r = subprocess.run([sys.executable, "-I", str(TOOL), "--part", str(self.part), "--audit",
                            str(self.audit([("a", 1, "keep")])), "--out", str(self.tmp / "v2"),
                            "--drop-images", str(self.drop_csv(["zzz"]))], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.tmp / "v2").exists())

    def test_box_removed_at_build_is_logged_not_error(self):
        (self.part / "labels" / "train" / "p__a.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")  # line 2 gone
        r = self.run_tool(self.audit([("a", 2, "remove_bad_box")]))
        self.assertEqual(r.returncode, 0, r.stderr)
        info = json.loads((self.tmp / "v2" / "build_info.json").read_text(encoding="utf-8"))
        self.assertEqual(info["audit_rows_not_in_part"], 1)

    def test_refuses_existing_output(self):
        (self.tmp / "v2").mkdir()
        self.assertNotEqual(self.run_tool(self.audit([("a", 1, "keep")])).returncode, 0)


if __name__ == "__main__":
    unittest.main()

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from helpers import save, smooth_image, write_label
from PIL import Image

from gp36data import build as build_mod
from gp36data.build import MARKER, BuildError, build_dataset
from gp36data.manifest import build_manifest
from gp36data.verify import verify_dataset

CMAP = {0: "pothole", 1: "speed_bump"}


class BuildCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "src"
        self.records = []
        names = ["103_jpg.rf.d14ee11bf4ea4f9a6cfa6763e973a5d8.jpg", "a.b.c.d.e.f.jpg", "حفرة 1.jpg",
                 "webp_in_disguise.jpg", "pic.png", "big.jpg"]
        fmts = ["JPEG", "JPEG", "JPEG", "WEBP", "PNG", "JPEG"]
        splits = ["train", "train", "val", "train", "test", "train"]
        for k, (n, f, s) in enumerate(zip(names, fmts, splits)):
            size = (2000, 1000) if n == "big.jpg" else (320, 240)
            img = save(smooth_image(100 + k, size), self.src / n, f)
            lbl = write_label(self.src / (Path(n).stem + ".txt"), f"{k % 2} 0.5 0.5 0.2 0.1\n")
            self.records.append({"sample_id": f"t/{n}", "source": "fx", "split": s, "image": img, "label": lbl,
                                 "class_map": CMAP})

    def out(self, name="ds"):
        return self.tmp / name


class TestBuild(BuildCase):
    def test_build_passes_and_is_traceable(self):
        before = build_manifest(self.src)
        rep = build_dataset(self.records, self.out(), check_near_dups=True)
        self.assertEqual(rep["errors"], [])
        self.assertEqual(build_manifest(self.src), before)  # inputs untouched
        data = yaml.safe_load((self.out() / "data.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("path", data)  # portable: resolved relative to data.yaml
        self.assertEqual(data["names"], {0: "pothole", 1: "speed_bump"})
        n_img = sum(len(list((self.out() / "images" / s).iterdir())) for s in ("train", "val", "test"))
        n_lbl = sum(len(list((self.out() / "labels" / s).iterdir())) for s in ("train", "val", "test"))
        self.assertEqual((n_img, n_lbl), (6, 6))
        man = (self.out() / "manifest.csv").read_text(encoding="utf-8")
        self.assertIn("a.b.c.d.e.f.jpg", man)  # original name kept for traceability
        self.assertFalse((self.out() / MARKER).exists())
        for p in (self.out() / "images").rglob("*.jpg"):
            with Image.open(p) as im:
                self.assertEqual(im.format, "JPEG")  # WEBP/PNG converted, extension now truthful

    def test_refuses_existing_target(self):
        self.out().mkdir()
        (self.out() / "keep.txt").write_text("x")
        with self.assertRaises(BuildError):
            build_dataset(self.records, self.out())
        self.assertEqual((self.out() / "keep.txt").read_text(), "x")

    def test_rebuild_is_identical(self):
        r1 = build_dataset(self.records, self.out("v1"), check_near_dups=False)
        r2 = build_dataset(self.records, self.out("v2"), check_near_dups=False)
        self.assertEqual(r1["fingerprint_sha256"], r2["fingerprint_sha256"])
        self.assertEqual((self.out("v1") / "checksums.sha256").read_text(), (self.out("v2") / "checksums.sha256").read_text())

    def test_interrupted_build_leaves_no_version_and_recovers(self):
        real = build_mod._write_image
        calls = {"n": 0}

        def flaky(*a, **k):
            calls["n"] += 1
            if calls["n"] == 3:
                raise KeyboardInterrupt("simulated power loss")
            return real(*a, **k)

        with mock.patch.object(build_mod, "_write_image", flaky):
            with self.assertRaises(KeyboardInterrupt):
                build_dataset(self.records, self.out(), check_near_dups=False)
        self.assertFalse(self.out().exists())
        self.assertTrue((self.tmp / ".ds.building" / MARKER).exists())
        build_dataset(self.records, self.out(), check_near_dups=False)  # cleans its own leftover
        self.assertTrue(self.out().exists())
        self.assertFalse((self.tmp / ".ds.building").exists())

    def test_foreign_temp_folder_is_not_deleted(self):
        foreign = self.tmp / ".ds.building"
        foreign.mkdir()
        (foreign / "precious.txt").write_text("x")
        with self.assertRaises(BuildError):
            build_dataset(self.records, self.out())
        self.assertTrue((foreign / "precious.txt").exists())

    def test_validation_failures_write_nothing(self):
        bad_img = self.src / "corrupt.jpg"
        bad_img.write_bytes(b"\xff\xd8\xff garbage")
        cases = {
            "corrupt image": {"image": bad_img},
            "invalid box": {"label": write_label(self.src / "bad.txt", "0 0.5 0.5 1.5 0.1\n")},
            "unmapped class": {"label": write_label(self.src / "cls.txt", "7 0.5 0.5 0.1 0.1\n")},
            "missing label": {"label": None},
            "unknown split": {"split": "holdout"},
        }
        for name, change in cases.items():
            with self.subTest(name):
                recs = [dict(r) for r in self.records]
                recs[0].update(change)
                with self.assertRaises(BuildError):
                    build_dataset(recs, self.out())
                self.assertFalse(self.out().exists())
                self.assertFalse((self.tmp / ".ds.building").exists())

    def test_duplicate_content_across_splits_rejected(self):
        recs = [dict(r) for r in self.records]
        recs.append({**recs[0], "sample_id": "copy", "split": "test"})
        with self.assertRaises(BuildError) as cm:
            build_dataset(recs, self.out())
        self.assertIn("same content", str(cm.exception.problems))

    def test_exif_rotated_image_requires_explicit_handling(self):
        im = smooth_image(5)
        exif = im.getexif()
        exif[0x0112] = 6
        recs = [dict(r) for r in self.records]
        recs[0]["image"] = save(im, self.src / "rotated.jpg", exif=exif)
        with self.assertRaises(BuildError):
            build_dataset(recs, self.out())

    def test_negative_sample_gets_empty_label(self):
        recs = [dict(r) for r in self.records]
        recs[0].update(label=None, negative=True)
        build_dataset(recs, self.out(), check_near_dups=False)
        empty = [p for p in (self.out() / "labels").rglob("*.txt") if p.read_text() == ""]
        self.assertEqual(len(empty), 1)

    def test_ignored_only_image_is_not_a_negative(self):
        # e.g. RDD2022 image with cracks only (D00 -> ignore): must not silently become background
        recs = [dict(r) for r in self.records]
        recs[0].update(label=write_label(self.src / "crack_only.txt", "2 0.5 0.5 0.2 0.1\n"), ignore=[2])
        with self.assertRaises(BuildError) as cm:
            build_dataset(recs, self.out(), check_near_dups=False)
        self.assertIn("only ignored-class objects", str(cm.exception.problems))
        recs[0]["allow_ignored_only"] = True
        build_dataset(recs, self.out(), check_near_dups=False)
        self.assertTrue(self.out().exists())

    def test_max_side_resizes_preserving_aspect_and_labels(self):
        build_dataset(self.records, self.out(), max_side=1000, check_near_dups=False)
        sizes = []
        for p in (self.out() / "images").rglob("*.jpg"):
            with Image.open(p) as im:
                sizes.append(im.size)
        self.assertIn((1000, 500), sizes)  # 2000x1000 -> 1000x500
        self.assertIn((320, 240), sizes)  # small images untouched


class TestVerify(BuildCase):
    def test_detects_problems(self):
        build_dataset(self.records, self.out(), check_near_dups=False)
        ds = self.out()
        self.assertEqual(verify_dataset(ds)["errors"], [])
        # cross-split duplicate
        t = next((ds / "images" / "train").iterdir())
        shutil.copy(t, ds / "images" / "test" / "leak.jpg")
        shutil.copy(ds / "labels" / "train" / (t.stem + ".txt"), ds / "labels" / "test" / "leak.txt")
        # orphan label, bad class id
        write_label(ds / "labels" / "val" / "orphan.txt", "0 0.5 0.5 0.1 0.1\n")
        lbl = next((ds / "labels" / "train").iterdir())
        lbl.write_text("5 0.5 0.5 0.1 0.1\n")
        errs = "\n".join(verify_dataset(ds)["errors"])
        self.assertIn("identical image in splits", errs)
        self.assertIn("near-duplicate across splits", errs)
        self.assertIn("label without image orphan.txt", errs)
        self.assertIn("class 5 >= nc 2", errs)
        self.assertIn("checksum: modified file", errs)


if __name__ == "__main__":
    unittest.main()

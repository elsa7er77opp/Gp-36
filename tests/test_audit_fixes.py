"""Regression tests for the independent-audit findings of 2026-10-30 (issues 1, 2 and 4).

Each test builds a small synthetic dataset in a temp dir; no project data is touched."""
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from test_build_verify import BuildCase

from gp36data.build import MARKER, BuildError, build_dataset, stale_temp_problems
from gp36data.verify import verify_dataset

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def errs(ds, **kw):
    return "\n".join(verify_dataset(ds, check_near_dups=False, **kw)["errors"])


class AuditCase(BuildCase):
    def setUp(self):
        super().setUp()
        build_dataset(self.records, self.out(), check_near_dups=False)
        self.ds = self.out()

    def copy(self, name):
        dst = self.tmp / name
        shutil.copytree(self.ds, dst)
        return dst


class TestIssue1MissingSplits(AuditCase):
    def test_baseline_passes_strict(self):
        rep = verify_dataset(self.ds, check_near_dups=False)
        self.assertEqual(rep["mode"], "strict")
        self.assertEqual(rep["errors"], [])

    def test_missing_split_never_passes_in_any_mode_even_without_checksums(self):
        for split in ("train", "val", "test"):
            for mode in ("strict", "legacy"):
                with self.subTest(split=split, mode=mode):
                    ds = self.copy(f"miss_{split}_{mode}")
                    shutil.rmtree(ds / "images" / split)
                    shutil.rmtree(ds / "labels" / split)
                    (ds / "checksums.sha256").unlink()
                    (ds / "manifest.csv").unlink()
                    self.assertIn(f"{split}: required split directory missing", errs(ds, mode=mode))

    def test_missing_labels_dir_only(self):
        ds = self.copy("nolabels")
        shutil.rmtree(ds / "labels" / "val")
        self.assertIn("val: required split directory missing: labels/val", errs(ds))

    def test_empty_split_rejected(self):
        ds = self.copy("empty")
        for p in (ds / "images" / "test").iterdir():
            p.unlink()
        for p in (ds / "labels" / "test").iterdir():
            p.unlink()
        self.assertIn("test: split has no images", errs(ds, mode="legacy"))

    def test_data_yaml_pointing_elsewhere_rejected(self):
        ds = self.copy("yaml")
        (ds / "data.yaml").write_text("train: images/train\nval: images/train\nnames: {0: pothole, 1: speed_bump}\n")
        e = errs(ds)
        self.assertIn("'val' is 'images/train', expected images/val", e)
        self.assertIn("no 'test' entry", e)

    def test_empty_label_negative_is_supported(self):
        lbl = next((self.ds / "labels" / "train").iterdir())
        ds = self.copy("neg")
        (ds / "labels" / "train" / lbl.name).write_text("")
        rep = verify_dataset(ds, check_near_dups=False)
        self.assertEqual(rep["counts"]["train"]["empty_label_images"], 1)
        self.assertEqual([e for e in rep["errors"] if "checksum" not in e], [])  # only the hash change is reported


class TestIssue2StrictChecksums(AuditCase):
    def test_missing_checksum_file(self):
        ds = self.copy("nock")
        (ds / "checksums.sha256").unlink()
        self.assertIn("checksums.sha256 missing", errs(ds))
        rep = verify_dataset(ds, check_near_dups=False, mode="legacy")
        self.assertEqual(rep["errors"], [])  # legacy: allowed, but labelled
        self.assertTrue(any("LEGACY MODE" in w for w in rep["warnings"]))
        self.assertTrue(any("checksums.sha256 missing" in w for w in rep["warnings"]))

    def test_mismatch(self):
        ds = self.copy("mm")
        next((ds / "labels" / "train").iterdir()).write_text("0 0.5 0.5 0.3 0.3\n")
        for mode in ("strict", "legacy"):
            self.assertIn("checksum: modified file", errs(ds, mode=mode))

    def test_malformed_line_is_an_error_not_a_crash(self):
        ds = self.copy("mal")
        with open(ds / "checksums.sha256", "a", encoding="utf-8") as f:
            f.write("this is not a checksum line\n")
        for mode in ("strict", "legacy"):
            self.assertIn("malformed record", errs(ds, mode=mode))

    def test_duplicate_record(self):
        ds = self.copy("dup")
        first = (ds / "checksums.sha256").read_text(encoding="utf-8").splitlines()[0]
        with open(ds / "checksums.sha256", "a", encoding="utf-8") as f:
            f.write(first + "\n")
        self.assertIn("duplicate record", errs(ds))

    def test_outside_root_entries_rejected_and_not_read(self):
        (self.tmp / "outside.txt").write_text("secret")
        for rel in ("../outside.txt", "/etc/hostname", "C:/Windows/win.ini", "images\\..\\..\\outside.txt"):
            with self.subTest(rel=rel):
                ds = self.copy("out_" + str(abs(hash(rel))))
                with open(ds / "checksums.sha256", "a", encoding="utf-8") as f:
                    f.write("0" * 64 + "  " + rel + "\n")
                e = errs(ds)
                self.assertIn("outside dataset root", e)
                self.assertNotIn("modified file " + rel, e)

    def test_unlisted_files_rejected_in_strict(self):
        ds = self.copy("extra")
        img = next((ds / "images" / "train").iterdir())
        shutil.copy(img, ds / "images" / "train" / "extra_img.jpg")
        (ds / "labels" / "train" / "extra_img.txt").write_text("")
        (ds / "notes.txt").write_text("x")
        e = errs(ds)
        self.assertIn("not covered by checksums.sha256: images/train/extra_img.jpg", e)
        self.assertIn("not covered by checksums.sha256: notes.txt", e)
        self.assertIn("image on disk not listed: images/train/extra_img.jpg", e)  # manifest check

    def test_ultralytics_caches_are_tolerated_but_reported(self):
        ds = self.copy("cache")
        img = next((ds / "images" / "train").glob("*.jpg"))
        img.with_suffix(".npy").write_bytes(b"x")
        (ds / "labels" / "train.cache").write_bytes(b"x")
        (ds / "images" / "train" / "orphan.npy").write_bytes(b"x")  # no matching image -> not a cache
        rep = verify_dataset(ds, check_near_dups=False)
        self.assertEqual(rep["errors"], ["checksum: file not covered by checksums.sha256: images/train/orphan.npy"])
        self.assertTrue(any("2 derived training-cache" in w for w in rep["warnings"]))

    def test_manifest_required_and_consistent(self):
        ds = self.copy("man")
        txt = (ds / "manifest.csv").read_text(encoding="utf-8")
        (ds / "manifest.csv").unlink()
        self.assertIn("manifest.csv missing", errs(ds))
        ds2 = self.copy("man2")
        (ds2 / "manifest.csv").write_text(txt.replace(",train,", ",val,", 1), encoding="utf-8")
        e = errs(ds2)
        self.assertIn("does not match location", e)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            verify_dataset(self.ds, mode="lenient")

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, str(TOOLS / "verify_dataset.py"), str(self.ds), "--no-near-dups"],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("mode=strict", ok.stdout)
        ds = self.copy("cli")
        shutil.rmtree(ds / "images" / "test")
        bad = subprocess.run([sys.executable, str(TOOLS / "verify_dataset.py"), str(ds), "--no-near-dups"],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        (ds / "checksums.sha256").unlink()
        leg = subprocess.run([sys.executable, str(TOOLS / "verify_dataset.py"), str(self.ds), "--legacy", "--no-near-dups"],
                             capture_output=True, text=True)
        self.assertIn("LEGACY PASS", leg.stdout)


class TestIssue4TempSafety(BuildCase):
    def tmpdir(self):
        return self.tmp / ".ds.building"

    def make_stale(self, marker=None):
        t = self.tmpdir()
        (t / "images" / "train").mkdir(parents=True)
        (t / "labels" / "train").mkdir(parents=True)
        (t / "images" / "train" / "a.jpg").write_bytes(b"x")
        (t / "labels" / "train" / "a.txt").write_text("")
        (t / MARKER).write_text(marker if marker is not None else
                                json.dumps({"owner": "gp36data.build", "target": "ds", "created": "x"}))
        return t

    def test_own_stale_temp_is_cleaned(self):
        self.make_stale()
        build_dataset(self.records, self.out(), check_near_dups=False)
        self.assertTrue(self.out().exists())
        self.assertFalse(self.tmpdir().exists())

    def test_marked_temp_with_foreign_file_is_not_deleted(self):  # the reproduced defect
        t = self.make_stale()
        (t / "USER_NOTES.docx").write_text("precious")
        with self.assertRaises(BuildError) as cm:
            build_dataset(self.records, self.out(), check_near_dups=False)
        self.assertIn("unexpected entry: USER_NOTES.docx", str(cm.exception.problems))
        self.assertEqual((t / "USER_NOTES.docx").read_text(), "precious")
        self.assertFalse(self.out().exists())

    def test_unexpected_nested_content_refused(self):
        for rel in ("images/train/notes.docx", "images/holdout/x.jpg", "labels/train/sub/x.txt"):
            with self.subTest(rel=rel):
                shutil.rmtree(self.tmpdir(), ignore_errors=True)
                t = self.make_stale()
                p = t / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("x")
                self.assertTrue(stale_temp_problems(t, "ds"))
                with self.assertRaises(BuildError):
                    build_dataset(self.records, self.out(), check_near_dups=False)
                self.assertTrue(p.exists())

    def test_marker_for_another_target_or_old_format_refused(self):
        for marker in (json.dumps({"owner": "gp36data.build", "target": "other", "created": "x"}),
                       "2026-10-30T10:00:00", json.dumps({"owner": "someone", "target": "ds"})):
            with self.subTest(marker=marker):
                shutil.rmtree(self.tmpdir(), ignore_errors=True)
                t = self.make_stale(marker)
                with self.assertRaises(BuildError):
                    build_dataset(self.records, self.out(), check_near_dups=False)
                self.assertTrue((t / "images" / "train" / "a.jpg").exists())

    @unittest.skipIf(os.name == "nt", "creating symlinks needs admin rights on Windows")
    def test_symlink_inside_temp_refused_and_target_untouched(self):
        victim = self.tmp / "victim"
        victim.mkdir()
        (victim / "data.jpg").write_text("keep")
        t = self.make_stale()
        (t / "images" / "val").symlink_to(victim, target_is_directory=True)
        with self.assertRaises(BuildError):
            build_dataset(self.records, self.out(), check_near_dups=False)
        self.assertEqual((victim / "data.jpg").read_text(), "keep")

    def test_existing_output_untouched_and_failed_build_keeps_it(self):
        build_dataset(self.records, self.out("approved"), check_near_dups=False)
        before = {p.relative_to(self.out("approved")).as_posix(): p.read_bytes() for p in self.out("approved").rglob("*") if p.is_file()}
        with self.assertRaises(BuildError):
            build_dataset(self.records, self.out("approved"), check_near_dups=False)
        recs = [dict(r) for r in self.records]
        recs.append({**recs[0], "sample_id": "copy", "split": "test"})  # invalid build of another version
        with self.assertRaises(BuildError):
            build_dataset(recs, self.out("v_next"), check_near_dups=False)
        after = {p.relative_to(self.out("approved")).as_posix(): p.read_bytes() for p in self.out("approved").rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(self.out("v_next").exists())

    def test_target_appearing_during_build_is_not_replaced(self):
        from unittest import mock
        from gp36data import build as build_mod
        real = build_mod.verify_dataset

        def verify_then_squat(*a, **k):
            rep = real(*a, **k)
            self.out().mkdir()
            (self.out() / "someone_else.txt").write_text("x")
            return rep

        with mock.patch.object(build_mod, "verify_dataset", verify_then_squat):
            with self.assertRaises(BuildError):
                build_dataset(self.records, self.out(), check_near_dups=False)
        self.assertEqual(sorted(p.name for p in self.out().iterdir()), ["someone_else.txt"])


class TestRotateCw(BuildCase):
    """Owner-approved fix 2026-10-30: phone photos stored sideways while labels match the upright view."""

    def test_rotate_cw_turns_pixels_only(self):
        from PIL import Image
        src = Image.new("RGB", (40, 20), "white")
        src.paste((255, 0, 0), (0, 0, 10, 20))  # red strip on the LEFT edge of the stored image
        img = self.src / "sideways.jpg"
        src.save(img, "JPEG", quality=100)
        lbl = self.src / "sideways.txt"
        lbl.write_text("0 0.5 0.1 0.2 0.1\n")  # label drawn on the upright image (red strip at the TOP)
        recs = [dict(r) for r in self.records] + [{"sample_id": "t/sideways", "source": "fx", "split": "train", "image": img,
                                                   "label": lbl, "class_map": {0: "pothole", 1: "speed_bump"}, "rotate_cw": 90}]
        build_dataset(recs, self.out(), check_near_dups=False)
        import csv as _csv
        row = next(r for r in _csv.DictReader(open(self.out() / "manifest.csv", encoding="utf-8")) if r["sample_id"] == "t/sideways")
        self.assertEqual((row["out_w"], row["out_h"], row["rotate_cw"]), ("20", "40", "90"))
        with Image.open(self.out() / row["out_image"]) as out:
            top = out.getpixel((10, 2)); bottom = out.getpixel((10, 37))
        self.assertGreater(top[0] - top[1], 100)       # red is now at the top
        self.assertLess(abs(bottom[0] - bottom[1]), 40)  # bottom stays white
        lbl_out = (self.out() / row["out_image"].replace("images/", "labels/", 1)).with_suffix(".txt").read_text()
        self.assertEqual(lbl_out.split()[1:3], ["0.500000", "0.100000"])  # label coordinates unchanged

    def test_invalid_rotation_rejected(self):
        recs = [dict(r) for r in self.records]
        recs[0]["rotate_cw"] = 45
        with self.assertRaises(BuildError):
            build_dataset(recs, self.out(), check_near_dups=False)
        self.assertFalse(self.out().exists())


if __name__ == "__main__":
    unittest.main()

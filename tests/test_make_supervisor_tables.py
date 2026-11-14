"""tools/make_supervisor_tables.py: copies numbers only, refuses split mismatch ('test' label on a val report)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

TOOL = ROOT / "tools" / "make_supervisor_tables.py"


def cls_block(ap, near=None):
    op = {"thr": 0.3, "tp": 5, "fp": 1, "fn": 2, "P": 0.8333, "R": 0.7143, "F1": 0.7692, "BoxAcc": 0.625,
          "ImgAcc": 0.9, "n_img": 10, "n_neg": 4, "NearR": 0.5, "n_near": 2}
    e = {"n_gt": 7, "AP50": ap, "AP50_95": 0.3, "P_at_R50": 0.95, "op": op, "deploy": dict(op, thr=0.35)}
    if near is not None:
        e["near"] = {"care": "near", "n_gt": 2, "n_ignore_gt": 5, "AP50": near, "op": dict(op), "deploy": dict(op, P=0.77, R=0.66)}
    return e


class TestTables(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        rep = {"data": "toy", "split": "val", "thresholds_from": "argmax F1", "models": {
            "m": {"classes": {"pothole": cls_block(0.6123, 0.8456), "speed_bump": cls_block(0.7, None)}}}}
        (self.tmp / "r").mkdir()
        (self.tmp / "r" / "report.json").write_text(json.dumps(rep), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_spec(self, split, figures=False, model="m"):
        spec = {"title": "T", "split": split, "figures": figures,
                "rows": [{"label": "Model M", "report": "r/report.json", "model": model}]}
        sp = self.tmp / "spec.json"
        sp.write_text(json.dumps(spec), encoding="utf-8")
        return subprocess.run([sys.executable, "-I", str(TOOL), "--spec", str(sp), "--out", str(self.tmp / "out"),
                               "--base", str(self.tmp)], capture_output=True, text=True)

    def test_numbers_copied_with_source(self):
        r = self.run_spec("val")
        self.assertEqual(r.returncode, 0, r.stderr)
        md = (self.tmp / "out" / "tables.md").read_text(encoding="utf-8")
        self.assertIn("| Model M | 0.300 | 0.833 | 0.714 | 0.769 | 0.612 | 0.300 | 0.625 | 0.900 | 0.500 | 0.950 | 0.846 | 7 | 10 (4) | 2 | `r/report.json` |", md)
        self.assertIn("0.770 / 0.660", md)      # near P/R at 0.35
        self.assertIn("Split: **val**", md)

    def test_val_report_is_never_called_test(self):
        r = self.run_spec("test")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refused", r.stderr)
        self.assertFalse((self.tmp / "out").exists())

    def test_missing_model_writes_nothing(self):
        self.assertNotEqual(self.run_spec("val", model="zzz").returncode, 0)
        self.assertFalse((self.tmp / "out").exists())

    def test_figures(self):
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("matplotlib not installed")
        r = self.run_spec("val", figures=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        for cn in ("pothole", "speed_bump"):
            self.assertGreater((self.tmp / "out" / f"fig_{cn}_ap50.png").stat().st_size, 1000)

    def test_refuses_existing_output(self):
        (self.tmp / "out").mkdir()
        self.assertNotEqual(self.run_spec("val").returncode, 0)


if __name__ == "__main__":
    unittest.main()

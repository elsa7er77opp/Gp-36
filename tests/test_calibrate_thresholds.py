"""tools/calibrate_thresholds.py: mode selection on toy PR curves, val-only rule, no overwrite."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from helpers import ROOT
from test_metrics_report import make_toy_dataset, pred

sys.path.insert(0, str(ROOT / "tools"))
import calibrate_thresholds as ct  # noqa: E402

TOOL = ROOT / "tools" / "calibrate_thresholds.py"


def imgs(scores_tp, n_gt):
    """One synthetic image holding all predictions: list of (score, tp)."""
    s = np.array([x[0] for x in scores_tp], float)
    t = np.array([x[1] for x in scores_tp], bool)
    return [(s, t, n_gt)]


class TestChoose(unittest.TestCase):
    # ranking 0.9 TP, 0.8 TP, 0.7 FP, 0.6 TP, 0.5 FP, 0.4 TP ; n_gt 5
    I = imgs([(0.9, 1), (0.8, 1), (0.7, 0), (0.6, 1), (0.5, 0), (0.4, 1)], 5)

    def test_f1(self):
        r = ct.calibrate(self.I, "f1", 0.0)
        # F1 by thr: .9 .333, .8 .571, .7 .5, .6 .667, .5 .6, .4 .727 -> 0.4
        self.assertEqual(r["conf"], 0.4)
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (4, 2, 1))

    def test_recall_target_takes_highest_threshold(self):
        r = ct.calibrate(self.I, "recall:0.6", 0.0)
        self.assertEqual(r["conf"], 0.6)  # recall 3/5 first reached at 0.6
        self.assertTrue(r["reached"])

    def test_precision_target_takes_lowest_threshold(self):
        r = ct.calibrate(self.I, "precision:0.75", 0.0)
        self.assertEqual(r["conf"], 0.6)  # P at .6 = 3/4; at .5 = 3/5
        self.assertEqual(r["R"], 0.6)

    def test_unreachable_target(self):
        r = ct.calibrate(self.I, "recall:0.95", 0.0)
        self.assertFalse(r["reached"])

    def test_min_conf_cuts_the_curve(self):
        r = ct.calibrate(self.I, "f1", 0.55)
        self.assertEqual(r["conf"], 0.6)

    def test_bad_mode(self):
        with self.assertRaises(ValueError):
            ct.choose(np.ones(1), np.ones(1), np.ones(1), np.ones(1), "auc")

    def test_bootstrap_is_reproducible(self):
        a = ct.bootstrap(self.I * 4, "f1", 0.0, 20)
        b = ct.bootstrap(self.I * 4, "f1", 0.0, 20)
        self.assertEqual(a, b)


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        make_toy_dataset(self.tmp / "ds", {"a": [(0, 0.5, 0.8, 0.2, 0.2)], "b": [(1, 0.5, 0.3, 0.4, 0.1)], "c": []})
        P = [pred("a", 0, 0.9, 0.5, 0.8, 0.2, 0.2), pred("b", 1, 0.8, 0.5, 0.3, 0.4, 0.1), pred("c", 0, 0.6, 0.5, 0.5, 0.1, 0.1)]
        (self.tmp / "p.json").write_text(json.dumps(P), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_tool(self, *extra):
        return subprocess.run([sys.executable, "-I", str(TOOL), "--data", str(self.tmp / "ds"), "--pred",
                               str(self.tmp / "p.json"), "--model", "toy", *extra], capture_output=True, text=True)

    def test_writes_proposal_and_refuses_overwrite(self):
        out = self.tmp / "thr.json"
        r = self.run_tool("--out", str(out), "--mode", "f1", "recall:0.5")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(j["classes"]["pothole"]["conf"], 0.9)
        self.assertEqual(j["classes"]["speed_bump"]["mode"], "recall:0.5")
        self.assertIn("NOT edited", j["note"])
        self.assertNotEqual(self.run_tool("--out", str(out)).returncode, 0)

    def test_refuses_test_split(self):
        r = self.run_tool("--split", "test", "--out", str(self.tmp / "x.json"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("val only", r.stderr)


if __name__ == "__main__":
    unittest.main()

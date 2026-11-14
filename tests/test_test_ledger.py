"""tools/test_ledger.py: one test use per model per benchmark; repeats and unclear past uses block."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

TOOL = ROOT / "tools" / "test_ledger.py"


class TestLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.led = self.tmp / "L.csv"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_(self, *args):
        return subprocess.run([sys.executable, "-I", str(TOOL), *args, "--ledger", str(self.led)],
                              capture_output=True, text=True)

    def test_add_then_repeat_refused(self):
        self.assertEqual(self.run_("check", "--model", "M", "--benchmark", "r2_test").returncode, 0)
        r = self.run_("add", "--model", "M", "--benchmark", "r2_test", "--source", "runs/M_TEST.txt")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.run_("check", "--model", "M", "--benchmark", "r2_test").returncode, 1)
        self.assertEqual(self.run_("check", "--model", " m ", "--benchmark", "R2_TEST").returncode, 1)  # normalised
        self.assertEqual(self.run_("add", "--model", "M", "--benchmark", "r2_test", "--source", "x").returncode, 1)
        self.assertEqual(self.led.read_text(encoding="utf-8").count("\n"), 2)  # header + 1 row, repeat not written

    def test_other_benchmark_or_model_ok(self):
        self.run_("add", "--model", "M", "--benchmark", "r2_test", "--source", "s")
        self.assertEqual(self.run_("check", "--model", "M", "--benchmark", "bd87").returncode, 0)
        self.assertEqual(self.run_("check", "--model", "N", "--benchmark", "r2_test").returncode, 0)

    def test_unresolved_blocks_not_a_use_does_not(self):
        self.run_("add", "--model", "A", "--benchmark", "r1_test", "--status", "UNRESOLVED")
        self.run_("add", "--model", "B", "--benchmark", "bd87", "--status", "NOT_A_USE")
        self.assertEqual(self.run_("check", "--model", "A", "--benchmark", "r1_test").returncode, 1)
        self.assertEqual(self.run_("check", "--model", "B", "--benchmark", "bd87").returncode, 0)

    def test_verified_needs_source_and_ids_increase(self):
        self.assertNotEqual(self.run_("add", "--model", "M", "--benchmark", "t").returncode, 0)
        self.run_("add", "--model", "M", "--benchmark", "t", "--source", "s")
        self.run_("add", "--model", "M2", "--benchmark", "t", "--source", "s")
        rows = self.led.read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual([r.split(",")[0] for r in rows], ["1", "2"])

    def test_repo_ledger_backfill(self):
        led = ROOT / "review" / "metrics_r3" / "TEST_LEDGER.csv"
        r = subprocess.run([sys.executable, "-I", str(TOOL), "check", "--model", "v3a_r2_11n_960_s0", "--benchmark",
                            "r2_test", "--ledger", str(led)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)   # Run A already used the r2 test (STATUS use #1)


if __name__ == "__main__":
    unittest.main()

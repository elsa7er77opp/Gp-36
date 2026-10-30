"""Run the full suite and report passed / failed / errored / skipped separately (issue 5)."""
import sys, unittest
from pathlib import Path
T = Path(__file__).resolve().parents[2] / "tests"
sys.path.insert(0, str(T)); sys.path.insert(0, str(T.parent))
suite = unittest.defaultTestLoader.discover(str(T), top_level_dir=str(T))
class R(unittest.TextTestResult):
    def __init__(s, *a, **k): super().__init__(*a, **k); s.passed = []
    def addSuccess(s, t): super().addSuccess(t); s.passed.append(t)
r = unittest.TextTestRunner(resultclass=R, verbosity=0, stream=open("/dev/null" if sys.platform != "win32" else "NUL", "w")).run(suite)
print(f"ran {r.testsRun} | passed {len(r.passed)} | failed {len(r.failures)} | errors {len(r.errors)} | skipped {len(r.skipped)} | expected-failures {len(r.expectedFailures)}")
for t, why in r.skipped: print("SKIPPED", t.id(), "-", why)
for t, tb in r.failures + r.errors: print("FAILED/ERROR", t.id()); print(tb[-600:])
sys.exit(0 if r.wasSuccessful() else 1)

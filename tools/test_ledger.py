"""Test-set use ledger: ONE test use per model per benchmark. A repeat is refused (non-zero exit).

    python -I tools/test_ledger.py check --model v3b_C_11n_960_s0 --benchmark r2_test
    python -I tools/test_ledger.py add   --model v3b_C_11n_960_s0 --benchmark r2_test --stage "Stage 26" \
        --source runs/v3b_C_11n_960_s0_TEST.txt --note "final candidate, chosen on val (Stage 25)"
    python -I tools/test_ledger.py list

Ledger: review/metrics_r3/TEST_LEDGER.csv (--ledger to override). Columns:
  use_id, date_time, model, benchmark, stage, status, source, note
status: VERIFIED (use logged with its output file), UNRESOLVED (a use is known but its time / details are not in
any file seen), NOT_A_USE (an attempt that never read an image, kept for the record).
`check` exits 1 if (model, benchmark) already has a VERIFIED or UNRESOLVED row; an UNRESOLVED row also blocks,
because an unclear past use is still a use. `add` runs the same check first and appends only if it passes.
Model and benchmark names are compared case-insensitively after stripping spaces. Run `check` BEFORE `yolo val
split=test`; run `add` right after it.
"""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "review" / "metrics_r3" / "TEST_LEDGER.csv"
FIELDS = ["use_id", "date_time", "model", "benchmark", "stage", "status", "source", "note"]
COUNTED = {"VERIFIED", "UNRESOLVED"}


def norm(s):
    return "".join(s.split()).lower()


def read(path):
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def prior_uses(rows, model, benchmark):
    return [r for r in rows if norm(r["model"]) == norm(model) and norm(r["benchmark"]) == norm(benchmark)
            and r["status"] in COUNTED]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "add", "list"])
    ap.add_argument("--ledger", default=str(LEDGER))
    ap.add_argument("--model")
    ap.add_argument("--benchmark")
    ap.add_argument("--stage", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--status", default="VERIFIED", choices=["VERIFIED", "UNRESOLVED", "NOT_A_USE"])
    ap.add_argument("--date-time", help="default: now (local time, minutes)")
    a = ap.parse_args(argv)
    rows = read(a.ledger)
    if a.cmd == "list":
        for r in rows:
            print(" | ".join(r[k] for k in FIELDS))
        return 0
    if not a.model or not a.benchmark:
        sys.exit("--model and --benchmark are required")
    prev = prior_uses(rows, a.model, a.benchmark)
    if prev:
        p = prev[0]
        print(f"REFUSED: {a.model} was already tested on {a.benchmark} (use {p['use_id']}, {p['date_time']}, "
              f"{p['status']}, {p['source']}). One test use per model per benchmark.", file=sys.stderr)
        return 1
    if a.cmd == "check":
        print(f"OK: no prior test use of {a.model} on {a.benchmark}")
        return 0
    if a.status == "VERIFIED" and not a.source:
        sys.exit("a VERIFIED use needs --source (the output file of the test run)")
    ids = [int(r["use_id"]) for r in rows if r["use_id"].isdigit()]
    row = {"use_id": "—" if a.status == "NOT_A_USE" else str(max(ids, default=0) + 1),
           "date_time": a.date_time or datetime.now().strftime("%Y-%m-%d %H:%M"), "model": a.model,
           "benchmark": a.benchmark, "stage": a.stage, "status": a.status, "source": a.source, "note": a.note}
    new = not Path(a.ledger).exists()
    Path(a.ledger).parent.mkdir(parents=True, exist_ok=True)
    with open(a.ledger, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"logged use {row['use_id']}: {a.model} on {a.benchmark}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

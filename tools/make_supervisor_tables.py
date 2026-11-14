"""Supervisor tables (Markdown) and figures (PNG) from tools/metrics_report.py outputs. FORMATS ONLY, never computes:
every number is copied from a report.json, and each table names its source file.

    python -I tools/make_supervisor_tables.py --spec supervisor_2026-11-08/tables_spec.json --out supervisor_2026-11-08/tables

spec (JSON):
  {"title": "Validation (r2 val, frozen)",
   "split": "val",                        # what the table CLAIMS to be; must equal report.json "split" of every row
   "rows": [{"label": "D1 11n", "report": "review/metrics_r3/val_r2_all_2026-11-04/report.json", "model": "D1_11n"},
            ...],
   "figures": true}
Output: <out>/tables.md (one table per class at the val-chosen operating threshold, one at conf 0.35, plus counts and
sources) and, with figures, <out>/fig_<class>_ap50.png (AP50 all next to near-range AP50 when the report has
`--care near`; dashed line at 0.90). Refuses to write if a report's split differs from the spec split (so a val
report is never shown as "test"), if a model is missing, or if <out> exists. Missing values are shown as "—".
Columns: P, R, F1, AP50, AP50-95, BoxAcc, ImgAcc, NearR, P@R50, near AP50 (operating table);
P, R, F1, BoxAcc, ImgAcc, NearR, near P/R (0.35 table).
"""
import argparse
import json
import sys
from pathlib import Path

CLASSES = ("pothole", "speed_bump")
# reference categorical palette (dataviz skill references/palette.md, light mode): slot 1 blue, slot 2 orange
COL_ALL, COL_NEAR, INK, MUTED, SURFACE = "#2a78d6", "#eb6834", "#1f1f1e", "#6b6b68", "#fcfcfb"


def f3(v):
    return "—" if v is None else f"{v:.3f}"


def load_rows(spec, base=Path(".")):
    rows, errors = [], []
    want = spec.get("split")
    if want not in ("val", "test"):
        errors.append(f"spec split must be 'val' or 'test', got {want!r}")
    for r in spec["rows"]:
        p = base / r["report"]
        if not p.exists():
            errors.append(f"{r['label']}: {p} not found")
            continue
        rep = json.loads(p.read_text(encoding="utf-8"))
        if rep.get("split") != want:
            errors.append(f"{r['label']}: report split is {rep.get('split')!r}, spec claims {want!r} — refused "
                          "(a report is called 'test' only if its split is test)")
            continue
        m = rep["models"].get(r["model"])
        if m is None:
            errors.append(f"{r['label']}: model {r['model']} not in {p}")
            continue
        rows.append({"label": r["label"], "report": r["report"], "data": rep.get("data"),
                     "thresholds_from": rep.get("thresholds_from"), "classes": m["classes"]})
    return rows, errors


def tables_md(spec, rows):
    L = [f"# {spec['title']}", "",
         f"Split: **{spec['split']}**. All numbers copied from the `report.json` named in each row "
         "(`tools/metrics_report.py`); this file computes nothing. IoU 0.5. Definitions: "
         "`supervisor_2026-11-08/METRICS.md` §1.", ""]
    for cn in CLASSES:
        L += [f"## {cn} — at the operating threshold (argmax F1 on val; on test the val threshold is reused)", "",
              "| model | thr | P | R | F1 | AP50 | AP50-95 | BoxAcc | ImgAcc | NearR | P@R50 | near AP50 | n_gt | n_img (n_neg) | n_near | source |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            e = r["classes"][cn]
            o = e["op"]
            nr = e.get("near")
            L.append(f"| {r['label']} | {o['thr']:.3f} | {f3(o['P'])} | {f3(o['R'])} | {f3(o['F1'])} | {f3(e['AP50'])} | "
                     f"{f3(e['AP50_95'])} | {f3(o['BoxAcc'])} | {f3(o['ImgAcc'])} | {f3(o.get('NearR'))} | "
                     f"{f3(e.get('P_at_R50'))} | {f3(nr['AP50']) if nr else '—'} | {e['n_gt']} | {o['n_img']} ({o['n_neg']}) | "
                     f"{o.get('n_near', '—')} | `{r['report']}` |")
        L += ["", f"## {cn} — at the deployed conf 0.35", "",
              "| model | P | R | F1 | BoxAcc | ImgAcc | NearR | near P / R | source |", "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            e = r["classes"][cn]
            d = e["deploy"]
            nd = e["near"]["deploy"] if e.get("near") else None
            L.append(f"| {r['label']} | {f3(d['P'])} | {f3(d['R'])} | {f3(d['F1'])} | {f3(d['BoxAcc'])} | {f3(d['ImgAcc'])} | "
                     f"{f3(d.get('NearR'))} | {(f3(nd['P']) + ' / ' + f3(nd['R'])) if nd else '—'} | `{r['report']}` |")
        L.append("")
    L += ["Thresholds per report: " + "; ".join(sorted({f"`{r['report']}`: {r['thresholds_from']}" for r in rows})), ""]
    return "\n".join(L)


def figure(rows, cn, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = [r["label"] for r in rows]
    ap_all = [r["classes"][cn]["AP50"] or 0.0 for r in rows]
    near = [r["classes"][cn].get("near", {}).get("AP50") for r in rows]
    has_near = any(v is not None for v in near)
    n = len(rows)
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * n * (2 if has_near else 1) + 1.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    h = 0.38 if has_near else 0.6
    ys = list(range(n))[::-1]
    ax.barh([y + (h / 2 + 0.02 if has_near else 0) for y in ys], ap_all, height=h, color=COL_ALL, label="AP50 (all)")
    if has_near:
        ax.barh([y - h / 2 - 0.02 for y in ys], [v or 0.0 for v in near], height=h, color=COL_NEAR,
                label="near-range AP50")
    for y, v in zip(ys, ap_all):
        ax.text(v + 0.01, y + (h / 2 + 0.02 if has_near else 0), f"{v:.3f}", va="center", fontsize=8, color=INK)
    if has_near:
        for y, v in zip(ys, near):
            ax.text((v or 0) + 0.01, y - h / 2 - 0.02, f3(v) if v is not None else "near not computed", va="center", fontsize=8, color=INK if v is not None else MUTED)
    ax.axvline(0.90, color=MUTED, linestyle="--", linewidth=1)
    ax.text(0.90, n - 0.4, "0.90 target", color=MUTED, fontsize=8, ha="center")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, color=INK, fontsize=9)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("AP50 (IoU 0.5)", color=MUTED, fontsize=9)
    ax.set_title(f"{cn} — {title}", color=INK, fontsize=10, loc="left", pad=22 if has_near else 6)
    ax.grid(axis="x", color="#e4e4e1", linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c9c9c5")
    ax.tick_params(colors=MUTED, length=0)
    if has_near:
        ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default=".", help="repo root that report paths are relative to")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    rows, errors = load_rows(spec, Path(a.base))
    if errors:
        sys.exit("NOTHING WRITTEN:\n  " + "\n  ".join(errors))
    out.mkdir(parents=True)
    (out / "tables.md").write_text(tables_md(spec, rows), encoding="utf-8")
    if spec.get("figures"):
        for cn in CLASSES:
            figure(rows, cn, out / f"fig_{cn}_ap50.png", f"{spec['title']} ({spec['split']})")
    print(f"wrote {out / 'tables.md'}" + (" + figures" if spec.get("figures") else ""))


if __name__ == "__main__":
    main()

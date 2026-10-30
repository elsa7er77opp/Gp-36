"""Phase 1c: read-only forensics over all raw sources -> review package.

    python tools/run_forensics.py --out review/phase1c_2026-10-30

Writes (into a NEW folder; refuses to overwrite, so human edits are never lost):
  inventory.csv        one row per raw image: integrity, hashes, label summary
  links.csv            exact / near-duplicate / metadata links between images
  groups.csv           leakage groups (connected components of links)
  problems.csv         orphan images / labels
  ANNOTATION_AUDIT.csv review sheet: automatic flags + empty human-review columns
  sheets/<category>/   contact sheets for visual review
  summary.json
"""
import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image  # noqa: E402

from gp36data.dedup import find_links, group_samples  # noqa: E402
from gp36data.inventory import scan_sample  # noqa: E402
from gp36data.labels import Box, compare_box_sets, map_classes  # noqa: E402
from gp36data.overlay import contact_sheet, draw_boxes, tile  # noqa: E402
from gp36data.sources import enumerate_samples, load_sources  # noqa: E402

# Known cases from the project history (PROJECT_AUDIT / CRITICAL_ISSUES). Kept as review regression cases.
REGRESSION = {
    "ghpot/all/pothole_058.jpg": "historical 'pothole box on CAUTION sign' claim (CI table)",
    "ghpot/all/pothole_015.jpg": "cross-source duplicate of rf8 157_jpg (CI-10)",
    "ghpot/all/pothole_076.jpg": "near-duplicate of pothole_151 across v2 train/test (C3)",
    "ghpot/all/pothole_151.jpg": "near-duplicate of pothole_076 across v2 train/test (C3)",
    "rf8/train/G0040808_JPG.rf.db88a6d7fee09c7b426a27b644691f9e.jpg": "duplicate pair with conflicting labels; crosswalk (CI-3)",
    "rf8/test/G0040808_JPG.rf.e29f0b5101177b9051d4c54ff274a47b.jpg": "duplicate pair with conflicting labels; crosswalk (CI-3)",
}
AUDIT_COLUMNS = ["sample_id", "source", "orig_split", "image", "sha256", "format", "width", "height", "n_pothole",
                 "n_speed_bump", "min_box_px_at960", "group_id", "group_size", "group_reasons", "auto_flags",
                 "auto_status", "sheets", "review_status", "review_decision", "corrected_label", "reviewer",
                 "review_date", "review_notes"]


def short(sid):
    s = sid.split("/", 2)
    name = s[2]
    if ".rf." in name:
        name = name.split(".rf.")[0] + ".rf." + name.split(".rf.")[1][:6]
    return f"{s[0]}/{s[1]}/{name}"


def make_tile(r, extra=""):
    with Image.open(r["image"]) as im:
        im.load()
        img = draw_boxes(im, r["mapped"])
    cap = [short(r["sample_id"]), f"{r['width']}x{r['height']}  P:{r['n_pothole']} B:{r['n_speed_bump']}  grp {r['group_id']}"]
    if extra:
        cap.append(extra[:70])
    return tile(img, cap)


def write_sheets(out, category, groups_of_records, per_sheet, cols, title, index, captions=None):
    """groups_of_records: list of lists (records kept together on one sheet row-run)."""
    d = out / "sheets" / category
    d.mkdir(parents=True, exist_ok=True)
    page, n, cur = [], 0, 0
    flat_batches = []
    for g in groups_of_records:
        if cur + len(g) > per_sheet and page:
            flat_batches.append(page)
            page, cur = [], 0
        page.append(g)
        cur += len(g)
    if page:
        flat_batches.append(page)
    for k, batch in enumerate(flat_batches, start=1):
        tiles, name = [], f"{category}_{k:03d}.jpg"
        for g in batch:
            for r in g:
                tiles.append(make_tile(r, (captions or {}).get(r["sample_id"], "")))
                index[r["sample_id"]].append(f"{category}/{name}")
        contact_sheet(tiles, cols=cols, title=f"{title} - sheet {k}/{len(flat_batches)}").save(d / name, quality=85)
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/sources.yaml")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dhash-max", type=int, default=4)
    ap.add_argument("--phash-max", type=int, default=10)
    ap.add_argument("--tiny-px", type=float, default=6.0, help="flag boxes shorter than this at 960 px")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-sheets", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} exists; forensics outputs are never overwritten (it may contain review edits)")

    cfg = load_sources(args.config)
    target = cfg["target_names"]
    samples, problems = enumerate_samples(cfg)
    print(f"{len(samples)} samples, {len(problems)} pairing problems; scanning with {args.workers} workers...", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        recs = list(ex.map(scan_sample, samples, chunksize=8))

    for r in recs:
        src = cfg["sources"][r["source"]]
        r["mapping_error"] = ""
        try:
            mapped, _ = map_classes([Box(*b) for b in r["boxes"]], src["class_map"], src["ignore"], target)
        except Exception as e:
            mapped, r["mapping_error"] = [], str(e)
        r["mapped"] = [(b.cls, b.xc, b.yc, b.w, b.h) for b in mapped]
        r["n_pothole"] = sum(1 for b in mapped if b.cls == 0)
        r["n_speed_bump"] = sum(1 for b in mapped if b.cls == 1)

    links = find_links(recs, args.dhash_max, args.phash_max)
    gids = group_samples(recs, links)
    for r, g in zip(recs, gids):
        r["group_id"] = g
    members = defaultdict(list)
    for i, g in enumerate(gids):
        members[g].append(i)
    reasons = defaultdict(set)
    near_partner = defaultdict(list)
    for i, j, why, dd, pd in links:
        reasons[gids[i]].add(why)
        if why == "near":
            near_partner[i].append((j, dd, pd))
            near_partner[j].append((i, dd, pd))

    # exact-duplicate label comparison
    by_sha = defaultdict(list)
    for i, r in enumerate(recs):
        by_sha[r["sha256"]].append(i)
    dup_status = {}
    for idx in by_sha.values():
        if len(idx) < 2:
            continue
        base = [Box(*b) for b in recs[idx[0]]["mapped"]]
        worst = "same"
        for j in idx[1:]:
            st = compare_box_sets(base, [Box(*b) for b in recs[j]["mapped"]])
            worst = max(worst, st, key=["same", "minor", "conflict"].index)
        for j in idx:
            dup_status[j] = worst

    # automatic flags
    for i, r in enumerate(recs):
        g = members[r["group_id"]]
        f = []
        if not r["ok"]:
            f.append("UNREADABLE")
        if not r["ext_matches_format"]:
            f.append(f"EXT_FORMAT_MISMATCH:{r['format']}")
        if r["exif_orientation"] != 1:
            f.append(f"EXIF_ORIENTATION:{r['exif_orientation']}")
        f += [f"LABEL_ERROR:{c}" for c in r["label_errors"]]
        f += [f"LABEL_WARNING:{c}" for c in r["label_warnings"]]
        if r["mapping_error"]:
            f.append("CLASS_UNMAPPED")
        if r["n_poly"]:
            f.append("POLYGON_LABEL")
        if not r["boxes"]:
            f.append("EMPTY_LABEL")
        if i in dup_status:
            f.append({"same": "EXACT_DUP", "minor": "EXACT_DUP_LABEL_MINOR_DIFF", "conflict": "EXACT_DUP_LABEL_CONFLICT"}[dup_status[i]])
        if near_partner[i]:
            f.append("NEAR_DUP")
        if len({recs[k]["source"] for k in g}) > 1:
            f.append("CROSS_SOURCE_GROUP")
        if len({recs[k]["orig_split"] for k in g if recs[k]["source"] == r["source"]}) > 1:
            f.append("GROUP_SPANS_ORIG_SPLITS")
        if r["min_box_px_at960"] is not None and r["min_box_px_at960"] < args.tiny_px:
            f.append("TINY_BOX")
        if r["sample_id"] in REGRESSION:
            f.append("REGRESSION_CASE")
        r["auto_flags"] = f
        # GROUP_SPANS_ORIG_SPLITS / TINY_BOX alone are split/size facts, not annotation doubts
        doubt = [x for x in f if not x.startswith(("GROUP_SPANS_ORIG_SPLITS", "TINY_BOX", "EXT_FORMAT_MISMATCH"))]
        r["auto_status"] = "NEEDS_REVIEW" if doubt else "AUTO_CHECKS_PASSED"

    out.mkdir(parents=True)
    with open(out / "inventory.csv", "w", newline="", encoding="utf-8") as fh:
        cols = ["sample_id", "source", "orig_split", "image", "label", "group_key", "ok", "error", "format",
                "ext_matches_format", "width", "height", "mode", "exif_orientation", "sha256", "dhash", "phash",
                "n_poly", "label_errors", "label_warnings", "mapping_error", "n_pothole", "n_speed_bump",
                "min_box_px", "min_box_px_at960", "group_id", "boxes_raw"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            w.writerow({**r, "dhash": f"{r['dhash']:016x}", "phash": f"{r['phash']:016x}",
                        "label_errors": ";".join(r["label_errors"]), "label_warnings": ";".join(r["label_warnings"]),
                        "boxes_raw": json.dumps(r["boxes"])})
    with open(out / "links.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["a", "b", "reason", "dhash_dist", "phash_dist"])
        for i, j, why, dd, pd in links:
            w.writerow([recs[i]["sample_id"], recs[j]["sample_id"], why, dd, pd])
    with open(out / "groups.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["group_id", "size", "reasons", "sources", "orig_splits", "members"])
        for g, idx in sorted(members.items(), key=lambda kv: -len(kv[1])):
            if len(idx) > 1:
                w.writerow([g, len(idx), ";".join(sorted(reasons[g])), ";".join(sorted({recs[k]["source"] for k in idx})),
                            ";".join(sorted({recs[k]["orig_split"] for k in idx})), "|".join(recs[k]["sample_id"] for k in idx)])
    with open(out / "problems.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "split", "file", "problem"])
        w.writeheader()
        w.writerows(problems)

    sheet_index = defaultdict(list)
    n_sheets = {}
    if not args.skip_sheets:
        rng = random.Random(args.seed)
        R = recs
        # 1. every exact-duplicate set, members side by side
        order = ["conflict", "minor", "same"]
        dup_idx = sorted((idx for idx in by_sha.values() if len(idx) > 1),
                         key=lambda idx: (order.index(dup_status[idx[0]]), R[idx[0]]["sample_id"]))
        dup_sets = [[R[k] for k in idx] for idx in dup_idx]
        cap = {R[k]["sample_id"]: f"exact dup: {dup_status[k]}" for idx in by_sha.values() if len(idx) > 1 for k in idx}
        n_sheets["exact_duplicates"] = write_sheets(out, "exact_duplicates", dup_sets, 8, 4, "Byte-identical images (labels compared)", sheet_index, cap)
        # 2. perceptual near-duplicate pairs that cross original splits or sources (threshold calibration)
        cross = [(i, j, dd, pd) for i, j, why, dd, pd in links if why == "near" and
                 (R[i]["orig_split"] != R[j]["orig_split"] or R[i]["source"] != R[j]["source"])]
        cross.sort(key=lambda t: -(t[2] + t[3]))  # borderline (largest distance) first
        cap = {}
        for i, j, dd, pd in cross:
            cap.setdefault(R[i]["sample_id"], f"near d={dd} p={pd}")
            cap.setdefault(R[j]["sample_id"], f"near d={dd} p={pd}")
        n_sheets["near_dup_cross_split"] = write_sheets(out, "near_dup_cross_split", [[R[i], R[j]] for i, j, _, _ in cross], 8, 4,
                                                        "Near-duplicates across original splits/sources (largest distance first)", sheet_index, cap)
        # 3. all crowd-sourced potholes, 4. all speed-bump video frames
        n_sheets["ghpot_all"] = write_sheets(out, "ghpot_all", [[r] for r in R if r["source"] == "ghpot"], 12, 4,
                                             "Crowd-sourced potholes (all)", sheet_index, {r["sample_id"]: ",".join(r["auto_flags"]) for r in R})
        n_sheets["ghsb_all"] = write_sheets(out, "ghsb_all", [[r] for r in R if r["source"] == "ghsb"], 16, 4,
                                            "Speed-bump video frames (all)", sheet_index, {r["sample_id"]: ",".join(r["auto_flags"]) for r in R})
        # 5. random Roboflow samples by class (seeded), 6. regression cases, 7. label problems
        rf_b = [r for r in R if r["source"] == "rf8" and r["n_speed_bump"]]
        rf_p = [r for r in R if r["source"] == "rf8" and r["n_pothole"] and not r["n_speed_bump"]]
        n_sheets["rf8_random_speed_bump"] = write_sheets(out, "rf8_random_speed_bump", [[r] for r in rng.sample(rf_b, min(48, len(rf_b)))], 12, 4,
                                                         "Roboflow random sample: images with speed bumps", sheet_index)
        n_sheets["rf8_random_pothole"] = write_sheets(out, "rf8_random_pothole", [[r] for r in rng.sample(rf_p, min(48, len(rf_p)))], 12, 4,
                                                      "Roboflow random sample: pothole-only images", sheet_index)
        reg = [r for r in R if r["sample_id"] in REGRESSION]
        n_sheets["regression_cases"] = write_sheets(out, "regression_cases", [[r] for r in reg], 8, 2, "Regression cases",
                                                    sheet_index, REGRESSION)
        bad = [r for r in R if r["label_errors"] or r["label_warnings"] or r["n_poly"] or r["mapping_error"] or not r["ok"]]
        if bad:
            n_sheets["label_problems"] = write_sheets(out, "label_problems", [[r] for r in bad], 12, 4, "Label problems",
                                                      sheet_index, {r["sample_id"]: ",".join(r["auto_flags"]) for r in R})

    with open(out / "ANNOTATION_AUDIT.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=AUDIT_COLUMNS)
        w.writeheader()
        for r in recs:
            g = members[r["group_id"]]
            w.writerow({**{k: r.get(k, "") for k in AUDIT_COLUMNS}, "group_size": len(g),
                        "group_reasons": ";".join(sorted(reasons[r["group_id"]])), "auto_flags": ";".join(r["auto_flags"]),
                        "sheets": ";".join(sheet_index[r["sample_id"]]), "review_status": "UNREVIEWED",
                        "min_box_px_at960": "" if r["min_box_px_at960"] is None else round(r["min_box_px_at960"], 1)})

    flag_counts = Counter(f.split(":")[0] for r in recs for f in r["auto_flags"])
    sizes = Counter(len(v) for v in members.values())
    summary = {
        "n_samples": len(recs), "pairing_problems": len(problems), "thresholds": {"dhash_max": args.dhash_max, "phash_max": args.phash_max, "tiny_px_at960": args.tiny_px},
        "links_by_reason": dict(Counter(l[2] for l in links)), "n_groups": len(members), "group_size_hist": {str(k): v for k, v in sorted(sizes.items())},
        "largest_groups": sorted((len(v) for v in members.values()), reverse=True)[:10],
        "exact_dup_sets": sum(1 for v in by_sha.values() if len(v) > 1), "exact_dup_label_status": dict(Counter(dup_status[v[0]] for v in by_sha.values() if len(v) > 1)),
        "flag_counts": dict(flag_counts), "auto_status": dict(Counter(r["auto_status"] for r in recs)),
        "per_source": {s: {"images": sum(1 for r in recs if r["source"] == s), "pothole": sum(r["n_pothole"] for r in recs if r["source"] == s),
                           "speed_bump": sum(r["n_speed_bump"] for r in recs if r["source"] == s)} for s in cfg["sources"]},
        "sheets": n_sheets,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

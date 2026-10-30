"""Make the split manifest for road_hazards_v3a (INTERIM, partially reviewed) — 2026-10-30.

Selection policy (owner decisions 2026-10-30):
* rf8 / ghpot rows of ANNOTATION_AUDIT.csv:
    PASS -> include.
    UNREVIEWED -> include ("interim") only if every automatic flag is a leakage/format flag
      (NEAR_DUP, GROUP_SPANS_ORIG_SPLITS, CROSS_SOURCE_GROUP, LABEL_WARNING, EXT_FORMAT_MISMATCH, POLYGON_LABEL).
      Excluded: TINY_BOX (owner rule FAR_TINY), EMPTY_LABEL, REGRESSION_CASE; EXACT_DUP keeps one copy.
    REJECTED / QUARANTINED / NEEDS_REVIEW -> excluded.
* ghsb (one 370-frame video): excluded from v3a; listed in <out>_unseen_road.csv for a separate test.
* sb15 (Roboflow speed-bump v15): all images; class 1 -> speed_bump, class 0 rumble strip ignored (D6);
  rumble-strip-only images are kept as background (allow_ignored_only=1, justified by D6).
* Groups: forensics group_id for rf8/ghpot; sb15 = video 10-s blocks merged with exact/near-duplicate links.
* Natural class ratio (owner decision). Group-aware 70/20/10 split, seed 0.
Paths are written as Windows paths so the build runs in the Windows venv.
"""
import argparse, csv, sys
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gp36data.dedup import find_links, group_samples  # noqa: E402
from gp36data.hashing import dhash, phash  # noqa: E402
from gp36data.manifest import sha256_file  # noqa: E402
from gp36data.sources import enumerate_samples, load_sources  # noqa: E402
from gp36data.split import group_split  # noqa: E402

OK_FLAGS = {"NEAR_DUP", "GROUP_SPANS_ORIG_SPLITS", "CROSS_SOURCE_GROUP", "LABEL_WARNING", "EXT_FORMAT_MISMATCH", "POLYGON_LABEL", "EXACT_DUP"}
WIN_DESKTOP = r"C:\Users\ahmed\Desktop"


def to_win(p, desktop):
    p = str(p)
    return WIN_DESKTOP + p[len(desktop):].replace("/", "\\") if p.startswith(desktop) else p


def flags(r):
    return {f.split(":")[0] for f in r["auto_flags"].replace(",", ";").split(";") if f}


def label_of(img):
    p = Path(img.replace("\\", "/"))
    return str(p.parent.parent / "labels" / (p.name.rsplit(".", 1)[0] + ".txt")).replace("/", "\\")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="review/phase1c_2026-10-30/ANNOTATION_AUDIT.csv")
    ap.add_argument("--config", default="configs/sources.yaml")
    ap.add_argument("--out", default="manifests/v3a_split_manifest.csv")
    ap.add_argument("--desktop", required=True, help="this machine's path of the Desktop folder")
    ap.add_argument("--dhash-margin", type=int, default=7)
    ap.add_argument("--phash-margin", type=int, default=14)
    ap.add_argument("--time-budget", type=float, default=1e9, help="seconds of hashing before saving the cache and stopping")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.audit, encoding="utf-8")))
    sel, unseen, excl, seen_sha = [], [], Counter(), set()
    for r in sorted(rows, key=lambda r: r["sample_id"]):
        if r["source"] == "ghsb":
            unseen.append(r); continue
        st, fl = r["review_status"], flags(r)
        if st == "PASS":
            kind = "reviewed"
        elif st == "UNREVIEWED" and fl <= OK_FLAGS:
            kind = "interim"
        else:
            excl[st if st != "UNREVIEWED" else "unreviewed:" + ",".join(sorted(fl - OK_FLAGS))] += 1; continue
        if r["sha256"] in seen_sha:
            excl["exact_duplicate_copy"] += 1; continue
        seen_sha.add(r["sha256"])
        sel.append({"sample_id": r["sample_id"], "source": r["source"], "image": r["image"], "label": label_of(r["image"]),
                    "group": f"aud:{r['group_id']}", "cls": {0: int(r["n_pothole"]), 1: int(r["n_speed_bump"])},
                    "review": kind, "allow_ignored_only": 0})
    # sb15
    cfg = load_sources(a.config)
    smp, prob = enumerate_samples({"sources": {"sb15": cfg["sources"]["sb15"]}})
    assert not prob, prob[:3]
    import json, time
    cache_p = Path(a.out).with_name("v3a_sb15_hash_cache.json")
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    t0 = time.time()
    for s in smp:
        if s["sample_id"] not in cache:
            with Image.open(s["image"]) as im:
                cache[s["sample_id"]] = [dhash(im), phash(im), sha256_file(s["image"])]
            if time.time() - t0 > a.time_budget:
                cache_p.write_text(json.dumps(cache)); print(f"hash cache {len(cache)}/{len(smp)} - run again"); return
        s["dhash"], s["phash"], s["sha256"] = cache[s["sample_id"]]
    cache_p.write_text(json.dumps(cache))
    gids = group_samples(smp, find_links(smp))
    for s, g in zip(smp, gids):
        c = Counter(int(l.split()[0]) for l in open(s["label"], encoding="utf-8") if l.strip())
        sel.append({"sample_id": s["sample_id"], "source": "sb15", "image": to_win(s["image"], a.desktop),
                    "label": to_win(s["label"], a.desktop), "group": f"sb15:{g}", "cls": {0: 0, 1: c.get(1, 0)},
                    "review": "interim", "allow_ignored_only": 1 if c.get(1, 0) == 0 else 0})
    # Re-link ALL selected samples (all sources together) with a safety margin over the verifier's
    # thresholds (dHash<=4 & pHash<=10). Hashes of the original images can sit just outside the threshold
    # while the resized build images fall inside it (found 2026-10-30: G0066108 ~ G0066364).
    inv = {r["sample_id"]: r for r in csv.DictReader(open(Path(a.audit).with_name("inventory.csv"), encoding="utf-8"))}
    sbh = {s["sample_id"]: s for s in smp}
    def h(v):
        return int(v, 16) if isinstance(v, str) else int(v)
    link_in = []
    for s in sel:
        src = sbh[s["sample_id"]] if s["source"] == "sb15" else inv[s["sample_id"]]
        link_in.append({"sha256": src["sha256"], "dhash": h(src["dhash"]), "phash": h(src["phash"]), "group_key": s["group"]})
    comp = group_samples(link_in, find_links(link_in, dhash_max=a.dhash_margin, phash_max=a.phash_margin))
    for s, c in zip(sel, comp):
        s["group"] = f"g{c}"
    groups = defaultdict(lambda: {"n": 0, "classes": Counter()})
    for s in sel:
        g = groups[s["group"]]; g["n"] += 1; g["classes"].update(s["cls"])
    assign = group_split({k: {"n": v["n"], "classes": dict(v["classes"])} for k, v in groups.items()}, seed=0)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cols = ["sample_id", "source", "split", "image", "label", "negative", "group_id", "allow_ignored_only", "review"]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for s in sel:
            w.writerow({"sample_id": s["sample_id"], "source": s["source"], "split": assign[s["group"]], "image": s["image"],
                        "label": s["label"], "negative": 0, "group_id": s["group"],
                        "allow_ignored_only": s["allow_ignored_only"], "review": s["review"]})
    with open(a.out.replace(".csv", "_unseen_road.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["sample_id", "image"]); [w.writerow([r["sample_id"], r["image"]]) for r in unseen]
    tab = defaultdict(Counter)
    for s in sel:
        sp = assign[s["group"]]
        tab[sp]["images"] += 1; tab[sp]["pothole"] += s["cls"][0]; tab[sp]["speed_bump"] += s["cls"][1]
        tab[sp][f"{s['source']}"] += 1; tab[sp][s["review"]] += 1
    print("excluded:", dict(excl))
    print("groups:", len(groups), "sb15 groups:", len({s['group'] for s in sel if s['source'] == 'sb15'}))
    for sp in ("train", "val", "test"):
        print(sp, dict(tab[sp]))


if __name__ == "__main__":
    main()

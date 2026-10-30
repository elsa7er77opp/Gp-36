"""Re-evaluate historical best.pt on the historical v2 test split and on leakage-filtered subsets.
Read-only w.r.t. the project: images are hard-linked and labels copied into a scratchpad mirror."""
import json, os, shutil, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from ultralytics import YOLO

SP = Path(sys.argv[1]); V2 = Path(r"C:\Users\ahmed\Desktop\GP36_AI\road_hazards_v2"); RUNS = Path(r"C:\Users\ahmed\Desktop\GP36_AI\runs\detect")
sets = {s["set"]: s for s in json.load(open(SP / "forensics.json", encoding="utf-8"))}
near = set(json.load(open(SP / "v2_test_leak.json")))
sha_tv = collections.defaultdict(set)
for n in ("v2:train", "v2:val"):
    for r in sets[n]["records"]:
        sha_tv[r["sha256"]].add(n)
exact = {r["path"].split("\\")[-1] for r in sets["v2:test"]["records"] if r["sha256"] in sha_tv}
alltest = sorted(r["path"].split("\\")[-1] for r in sets["v2:test"]["records"])
subsets = {
    "full": alltest,
    "no_exact_dup": [f for f in alltest if f not in exact],
    "no_near_dup": [f for f in alltest if f not in near and f not in exact],
    "rf_only": [f for f in alltest if f.startswith("rf_")],
    "sb_only": [f for f in alltest if f.startswith("sb_")],
    "pot_only": [f for f in alltest if f.startswith("pot_")],
}
for name, files in subsets.items():
    root = SP / "mirror" / name
    if root.exists():
        shutil.rmtree(root)
    (root / "images" / "test").mkdir(parents=True); (root / "labels" / "test").mkdir(parents=True)
    for f in files:
        os.link(V2 / "images" / "test" / f, root / "images" / "test" / f)
        stem = f.rsplit(".", 1)[0]
        shutil.copy(V2 / "labels" / "test" / f"{stem}.txt", root / "labels" / "test" / f"{stem}.txt")
    (root / "data.yaml").write_text(f"path: {root.as_posix()}\ntrain: images/test\nval: images/test\ntest: images/test\nnames:\n  0: pothole\n  1: speed_bump\n")
    print(name, len(files))

runs = {"run2_v8n640": ("gp36_v2", 640), "run3_v8s960": ("gp36_v2_s960", 960), "run4_v8n960": ("gp36_v2_n960", 960), "run5_11n960": ("gp36_v2_11n960", 960)}
res = {}
for rk, (d, sz) in runs.items():
    m = YOLO(str(RUNS / d / "weights" / "best.pt"))
    for name in subsets:
        mt = m.val(data=str(SP / "mirror" / name / "data.yaml"), split="test", imgsz=sz, batch=8, workers=0, device=0,
                   plots=False, verbose=False, project=str(SP / "valruns"), name=f"{rk}_{name}", exist_ok=True)
        ap50 = {mt.names[int(c)]: round(float(mt.box.ap50[i]), 3) for i, c in enumerate(mt.box.ap_class_index)}
        res[(rk, name)] = dict(n=len(subsets[name]), mAP50=round(float(mt.box.map50), 3), mAP5095=round(float(mt.box.map), 3),
                               P=round(float(mt.box.mp), 3), R=round(float(mt.box.mr), 3), ap50=ap50,
                               ms=round(mt.speed["inference"], 2))
        print(rk, name, res[(rk, name)])
json.dump({f"{a}|{b}": v for (a, b), v in res.items()}, open(SP / "hist_eval.json", "w"), indent=1)
print("exact-dup test images:", len(exact), "near-dup (excl exact):", len(near - exact))

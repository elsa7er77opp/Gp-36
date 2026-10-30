# GP36 — ENVIRONMENT_REPORT (Phase 0, read-only)

Audit date: 2026-10-30. Everything below was measured on the laptop during this audit. No package was installed, upgraded or removed.

## Measured configuration

| Item | Measured value | Matches history? | Status |
|---|---|---|---|
| OS | Windows 11 Home Single Language 10.0.26200 | yes | PASS |
| CPU | Intel Core 5 210H, 8 cores / 12 threads | not recorded before | PASS |
| RAM | 15.6 GB total; **4.3 GB free** at audit time (other apps open); page file 17.8 GB | — | NEEDS_REVIEW (see risks) |
| Disk C: | 599.7 GB used, **147.1 GB free** | — | PASS |
| GPU | NVIDIA GeForce RTX 5050 Laptop, compute capability 12.0 (sm_120), 7.93 GiB usable VRAM | yes | PASS |
| NVIDIA driver | 617.42 (CUDA UMD 13.4), WDDM | yes (log: 617.42) | PASS |
| Python | 3.12.10, `C:\Users\ahmed\Desktop\GP36_AI\venv\Scripts\python.exe` | yes | PASS |
| venv | `GP36_AI\venv`, `include-system-site-packages = false` | — | PASS |
| PyTorch | 2.11.0+cu128, CUDA 12.8, arch list includes sm_120 | yes | PASS |
| CUDA runtime test | `torch.cuda.is_available()` = True; a 512×512 GPU matmul ran correctly | — | PASS |
| torchvision | 0.26.0+cu128 | — | PASS |
| Ultralytics | 8.4.192 | yes | PASS |
| OpenCV / NumPy / Pillow | 5.0.0.93 / 2.5.4 / 13.0.0 | — | PASS |
| `pip check` | "No broken requirements found." | — | PASS |
| GPU inference smoke test | All 4 historical `best.pt` ran validation on the GPU (see PROJECT_AUDIT §5) | — | PASS |

Full package list: anyio, certifi, charset-normalizer, contourpy, cycler, filelock, fonttools, fsspec, h11, httpcore, httpx, idna, Jinja2, kiwisolver, MarkupSafe, matplotlib 3.11.2, mpmath, networkx, numpy, nvidia-ml-py, opencv-python, packaging, pillow, pip 25.0.1, polars 2.1.0, psutil 7.2.2, pyparsing, python-dateutil, PyYAML, requests, setuptools, six, sympy, torch, torchvision, tzdata, ultralytics, ultralytics-platform 0.1.101, ultralytics-thop, urllib3.

## Disk usage of project artefacts

| Path | Size | Note |
|---|---|---|
| `GP36_AI/road_hazards_v2` | **65 GB** | 3,538 `.npy` files created by `cache=disk` (train 2,952 + val 586) beside the images. These are derived data that can be regenerated. |
| `GP36_AI/torch-2.11.0+cu128-cp312-cp312-win_amd64.whl` | 2.75 GB | Installer wheel already installed into the venv. |
| `GP36_AI/venv` | 4.8 GB | |
| `GP36_AI/road_hazards` (v1) | 140 MB | |
| `GP36_AI/runs` | 135 MB | 5 training runs and 5 test-evaluation folders. |
| `GP36_Dataset` | 3.6 GB | roboflow 2.2 GB, yolo-automotive 1.2 GB, speed_bumps 162 MB, potholes 79 MB |
| `Desktop/graduation project/GP36_Dataset` | 1.5 GB | Backup copy. `potholes/` and `speed_bumps/` are **byte-identical** to the working copy (SHA-256 verified). There is **no backup of `roboflow/`**. |

## Risks and recommendations

1. **RAM headroom (NEEDS_REVIEW).** 4.3 GB was free during the audit. Each Windows DataLoader worker is a separate process, and run 3 previously crashed with `workers=8`. Recommendation: use `workers=2` (validated in runs 3–5), check free RAM before each run, and close heavy apps during training.
2. **Disk cache (NEEDS_REVIEW).** `cache=disk` stores decoded uint8 arrays. Most Roboflow images are 3680×2760, about 30 MB each, which explains the 65 GB. A v3 dataset with the same images would need a similar amount. Recommendation: `cache=False`, or `cache=ram` only if the RAM check passes. Deleting the existing `.npy` files would free about 65 GB, but **only with your approval**.
3. **No dependency lock file.** There is no `requirements.txt` or lock file, so the environment cannot be rebuilt reproducibly. Recommendation: freeze it (`pip freeze > requirements-lock.txt`). This is non-destructive.
4. **Not under version control.** `GP36_AI` is not a git repository. Recommendation: `git init` with a `.gitignore` that excludes images, `.npy`, weights and the venv. This is non-destructive, but asks for your approval.
5. **No upgrades are needed.** The current stack runs sm_120 correctly. Ultralytics 8.4.192 already loads `weights/yolo26n.pt` (verified), so YOLO26 needs no separate environment.

## Gate A — Environment integrity: **PASS** (with the two NEEDS_REVIEW resource risks above)

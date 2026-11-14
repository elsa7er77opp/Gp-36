"""Read-only, standard-library audit. Never trains, reads test images, or uploads.
Run from anywhere: python tools/collect_f0_context.py --root .
"""
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import platform
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone

C_RUN = 'v3b_C_11n_960_s0_r2'
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 20 * 1024 * 1024


def inspect_dataset(root):
    counts = Counter()
    issues = []
    candidates = []
    sources = {}
    manifest = root / 'manifest.csv'
    if manifest.is_file():
        with manifest.open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                if row.get('split') in ('train', 'val'):
                    sources[(row['split'], Path(row.get('out_image', '')).stem)] = row.get('source', row.get('part', 'unknown'))
    else:
        issues.append('Missing manifest.csv; source breakdown unavailable.')
    for split in ('train', 'val'):
        labels = root / 'labels' / split
        images = root / 'images' / split
        if not labels.is_dir() or not images.is_dir():
            issues.append(f'Missing images or labels directory: {split}')
            continue
        # Names only: image bytes are never read.
        image_ids = Counter(p.stem for p in images.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff'})
        label_files = sorted(labels.glob('*.txt'))
        label_ids = {p.stem for p in label_files}
        counts[f'{split}/images'] = sum(image_ids.values())
        counts[f'{split}/missing_labels'] = len(set(image_ids) - label_ids)
        counts[f'{split}/orphan_labels'] = len(label_ids - set(image_ids))
        counts[f'{split}/duplicate_image_stems'] = sum(n > 1 for n in image_ids.values())
        for label in label_files:
            source = sources.get((split, label.stem), 'unknown')
            lines = label.read_text(encoding='utf-8-sig').splitlines()
            if not any(s.strip() for s in lines):
                counts[f'{split}/empty_label_files'] += 1
            for number, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    values = list(map(float, line.split()))
                    if len(values) != 5 or not all(math.isfinite(x) for x in values):
                        raise ValueError('expected five finite values')
                    cls, x, y, w, h = values
                    if cls not in (0, 1) or not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                        raise ValueError('class or coordinate outside range')
                    if min(x-w/2, y-h/2) < -1e-5 or max(x+w/2, y+h/2) > 1+1e-5:
                        raise ValueError('box extends outside image')
                except ValueError as exc:
                    counts[f'{split}/invalid_boxes'] += 1
                    if len(issues) < 100:
                        issues.append(f'{split}/{label.name}:{number}: {exc}')
                    continue
                cls = int(cls)
                near = y + h / 2 >= .60 and math.sqrt(w*h) >= .05
                counts[f'{split}/class_{cls}/boxes'] += 1
                counts[f'{split}/source_{source}/class_{cls}/boxes'] += 1
                if near:
                    counts[f'{split}/source_{source}/class_{cls}/near_boxes'] += 1
                if split == 'train' and cls == 1 and near:
                    candidates.append({'label': str(label.relative_to(root)), 'line': number,
                                       'source': source, 'unmarked': 'UNKNOWN_REQUIRES_HUMAN_REVIEW'})
    return {'counts': dict(sorted(counts.items())), 'issues': issues,
            'limitations': 'Geometry only; near does not imply Egyptian or unmarked. No pixel review, checksum verification or leakage audit.'}, candidates


def collect(root, output_dir):
    root = root.resolve()
    if not (root / 'road_hazards_v3b_C' / 'data.yaml').is_file():
        raise ValueError('Run inside the GP36 project root (road_hazards_v3b_C/data.yaml missing).')
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / ('GP36_F0_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:8] + '.zip')
    inventory, missing, skipped = [], [], []
    total = 0
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as z:
        def add_file(path):
            nonlocal total
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or not path.is_file():
                missing.append(rel)
                return
            size = path.stat().st_size
            if size > MAX_FILE or total + size > MAX_TOTAL:
                skipped.append(rel)
                return
            data = path.read_bytes()
            z.writestr('context/' + rel, data)
            total += len(data)
            inventory.append({'path': rel, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        for name in ('AGENTS.md', 'requirements.txt', 'pyproject.toml'):
            add_file(root / name)
        for name in ('args.yaml', 'results.csv'):
            add_file(root / 'runs' / 'detect' / C_RUN / name)
        for folder in ('gp36data', 'tests'):
            paths = sorted((root / folder).rglob('*.py'))
            if not paths:
                missing.append(folder + '/*.py')
            for path in paths:
                add_file(path)
        for report in ('val_r2_C', 'val_r2_levers_C', 'val_r2_E1', 'val_r2_E2', 'val_r2_final', 'partval_egy_v2_C'):
            for name in ('report.json', 'report.md'):
                add_file(root / 'review' / 'metrics_r3' / report / name)
        for dataset in ('road_hazards_v3a_r2', 'road_hazards_v3b_C'):
            path = root / dataset
            for name in ('data.yaml', 'build_info.json'):
                add_file(path / name)
            result, candidates = inspect_dataset(path)
            z.writestr(f'audit/{dataset}.json', json.dumps(result, ensure_ascii=False, indent=2))
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=('label', 'line', 'source', 'unmarked'))
            writer.writeheader()
            writer.writerows(candidates)
            z.writestr(f'audit/{dataset}_near_bump_train_review.csv', stream.getvalue())
        versions = {}
        for package in ('ultralytics', 'torch', 'torchvision', 'numpy', 'PyYAML', 'Pillow'):
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = 'NOT_INSTALLED_IN_THIS_PYTHON'
        z.writestr('environment.json', json.dumps({'python': platform.python_version(), 'system': platform.system(), 'packages': versions}, indent=2))
        z.writestr('inventory.json', json.dumps({'included': inventory, 'missing': missing, 'skipped_size_limit': skipped}, indent=2))
    print(f'Created: {output}\nSize: {output.stat().st_size / 1024:.1f} KB\nMissing optional/context items: {len(missing)}; skipped: {len(skipped)}')
    print('Collection complete, NOT a dataset-integrity PASS. Review audit/*.json for findings.')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    collect(args.root, args.root / 'review' / 'f0_context')


if __name__ == '__main__':
    main()

"""Build and verify the complete Stage 40 data plus a curated 10,000-image train split.

No source files are modified. Ambiguous images remain in the complete release.
Run with the repository venv: python tools/v5_build_release.py
"""
import csv
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review/v5'
BASE = ROOT / 'road_hazards_v5_all'
FULL = ROOT / 'road_hazards_v5_corrected_20261112'
CURATED = ROOT / 'road_hazards_v5_curated_10000'


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lab(root, image):
    p = Path(image)
    return root / 'labels' / p.parent.name / (p.stem + '.txt')


def expected_label(boxes):
    return ''.join(f'{c} {(x+X)/2:.6f} {(y+Y)/2:.6f} {X-x:.6f} {Y-y:.6f}\n'
                   for c, x, y, X, Y in boxes).replace('\n', os.linesep).encode()


def verify_labels(raw):
    counts = Counter()
    for line in raw.decode('utf-8-sig').splitlines():
        v = line.split()
        assert len(v) == 5, line
        c = int(v[0])
        x, y, w, h = map(float, v[1:])
        assert c in (0, 1) and all(math.isfinite(a) for a in (x, y, w, h))
        assert w > 0 and h > 0
        assert min(x-w/2, y-h/2) >= -1e-6 and max(x+w/2, y+h/2) <= 1+1e-6
        counts[c] += 1
    return counts


def main():
    resume = '--resume' in sys.argv
    assert not CURATED.exists(), 'Refusing to overwrite curated release'
    assert resume or not FULL.exists(), 'Use --resume to verify an existing complete build'
    fixes_list = [json.loads(l) for l in (REVIEW/'fixes.jsonl').read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    fixes = {f['image']: f for f in fixes_list}
    assert len(fixes) == len(fixes_list), 'Duplicate fix image'
    decisions = {}
    for name in ('unsure_recheck_codex.csv', 'forward_review_codex.csv', 'final_recheck_codex.csv'):
        for r in read_csv(REVIEW/name):
            decisions[r['image']] = r
    pending = {r['image'] for r in read_csv(REVIEW/'final_recheck_codex.csv') if r['decision'] == 'unsure'}
    pending.update(r['image'] for r in read_csv(REVIEW/'final_qa_flags_codex.csv'))
    assert len(read_csv(REVIEW/'final_recheck_codex.csv')) == len(read_csv(REVIEW/'final_recheck_queue_codex.csv'))
    if not FULL.exists():
        subprocess.run([sys.executable, str(ROOT/'tools/v5_fix.py'), 'apply', '--data', str(BASE),
                        '--fixes', str(REVIEW/'fixes.jsonl'), '--out', str(FULL), '--fixed-by', 'claude,codex'], check=True)
    rows = read_csv(FULL/'manifest.csv')
    original = {r['out_image']: r for r in read_csv(BASE/'manifest.csv')}
    stats = defaultdict(Counter)
    fingerprint = hashlib.sha256()
    for n, r in enumerate(rows, 1):
        image = r['out_image']
        raw = (FULL/image).read_bytes()
        digest = sha(raw)
        assert digest == sha((BASE/image).read_bytes()), image
        assert digest == original[image]['out_sha256'], image
        with Image.open(io.BytesIO(raw)) as im:
            assert im.size == (960, 720), image
            im.load()
        label = lab(FULL, image).read_bytes()
        expected = expected_label(fixes[image]['boxes']) if image in fixes else lab(BASE, image).read_bytes()
        assert label == expected, image
        counts = verify_labels(label)
        assert counts[0] == int(r['n_pothole']) and counts[1] == int(r['n_speed_bump']), image
        stats[r['split']].update(images=1, pothole_boxes=counts[0], speed_bump_boxes=counts[1], empty=int(not counts))
        fingerprint.update((image+digest+sha(label)).encode())
        if n % 2000 == 0:
            print(f'Full verification {n}/{len(rows)}', flush=True)
    assert stats['train']['images'] == 10562 and stats['val']['images'] == 830 and stats['test']['images'] == 323
    train = [r for r in rows if r['split'] == 'train']
    assert pending <= {r['out_image'] for r in train}
    eligible = [r for r in train if r['out_image'] not in pending]
    assert len(eligible) >= 10000, f'Only {len(eligible)} eligible; never pad with unresolved images'
    groups = defaultdict(list)
    for r in eligible:
        groups[(r['source'], int(r['n_pothole']) > 0, int(r['n_speed_bump']) > 0)].append(r)
    quotas = {g: int(len(v)*10000/len(eligible)) for g, v in groups.items()}
    remainder = 10000 - sum(quotas.values())
    order = sorted(groups, key=lambda g: (-(len(groups[g])*10000/len(eligible)-quotas[g]), g))
    for g in order[:remainder]:
        quotas[g] += 1
    selected = []
    for g, group in groups.items():
        group.sort(key=lambda r: sha(('stage40-curated-10000:'+r['out_image']).encode()))
        selected.extend(group[:quotas[g]])
    selected_ids = {r['out_image'] for r in selected}
    assert len(selected_ids) == 10000 and not selected_ids & pending
    assert {r['source'] for r in selected} == {r['source'] for r in train}
    release_rows = [r for r in rows if r['split'] != 'train' or r['out_image'] in selected_ids]
    tmp = CURATED.with_name(CURATED.name+'.building')
    assert not tmp.exists()
    tmp.mkdir()
    sys.path.insert(0, str(ROOT/'tools'))
    from v5_fix import link
    for r in release_rows:
        image = r['out_image']
        link(FULL/image, tmp/image)
        link(lab(FULL, image), lab(tmp, image))
        assert sha((tmp/image).read_bytes()) == r['out_sha256']
        assert lab(tmp, image).read_bytes() == lab(FULL, image).read_bytes()
    for name in ('data.yaml', 'data_stdframe.yaml', 'val_stdframe.txt', 'test_stdframe.txt'):
        if (FULL/name).exists():
            shutil.copyfile(FULL/name, tmp/name)
    write_csv(tmp/'manifest.csv', release_rows)
    provenance = []
    for r in train:
        image = r['out_image']
        status = 'unresolved_excluded' if image in pending else 'selected' if image in selected_ids else 'eligible_reserve'
        basis = 'ai_label_correction' if image in fixes else decisions.get(image, {}).get('decision', 'prior_stage39a_or_claude_visual_review')
        provenance.append(dict(image=image, source=r['source'], release_status=status, review_basis=basis,
                               image_sha256=r['out_sha256'], label_sha256=sha(lab(FULL,image).read_bytes())))
    write_csv(REVIEW/'release_selection_codex.csv', provenance)
    write_csv(FULL/'review_status.csv', provenance)
    write_csv(tmp/'review_status.csv', [r for r in provenance if r['release_status']=='selected'])
    summary = dict(date='2026-11-12', labelling='AI visual review by claude and codex; no detector output used',
                   reviewed_sheets=916, rechecked_uncertain_images=988, corrected_images=len(fixes),
                   unresolved_images=len(pending), eligible_train_images=len(eligible),
                   curated_train_images=10000, eligible_reserve_images=len(eligible)-10000,
                   train_sources=dict(Counter(r['source'] for r in selected)),
                   complete_dataset_splits={k:dict(v) for k,v in stats.items()},
                   full_content_fingerprint=fingerprint.hexdigest(),
                   verification='PASS: every full image decoded, dimension/hash checked, every label checked against fixes/source; curated pairs checked byte-for-byte',
                   val_test='Image and label bytes unchanged; no model evaluation performed',
                   limitations='Visual first pass complete; unresolved images preserved only in complete release. Curated data is AI-reviewed, not human ground truth or a guarantee of perfect annotation.')
    for dest, kind in ((FULL,'complete'), (tmp,'curated_10000_train')):
        (dest/'release_info.json').write_text(json.dumps(dict(summary, release_kind=kind),indent=2)+'\n',encoding='utf-8')
        (dest/'README_STAGE40.md').write_text(
            '# Stage 40 dataset release\n\n'
            + (f'Complete release: 10,562 train images; {len(pending)} unresolved cases including final QA flags are identified in review_status.csv.\n\n' if kind=='complete' else 'Curated release: exactly 10,000 train images from every source, excluding all recorded unresolved cases and final QA flags.\n\n')
            + 'Both releases include the original 830 validation and 323 test images and labels unchanged. Images are 960 x 720. Classes: 0 pothole, 1 speed_bump. Use data.yaml or data_stdframe.yaml.\n\n'
            + 'Labels were reviewed visually by AI (Claude/Codex), without detector predictions. This is not human-verified ground truth and does not imply perfect annotations. The complete release preserves every image; originals and previous releases are retained. No training or benchmark evaluation was run.\n\n'
            + 'See release_info.json, manifest.csv, review_status.csv, and review/v5/release_selection_codex.csv for provenance.\n',encoding='utf-8')
    # v5_fix build_info describes the complete dataset; regenerate curated statistics.
    curated_stats = defaultdict(Counter)
    for r in release_rows:
        curated_stats[r['split']].update(images=1,pothole_boxes=int(r['n_pothole']),speed_bump_boxes=int(r['n_speed_bump']))
    (tmp/'build_info.json').write_text(json.dumps(dict(from_dataset=str(FULL), splits={k:dict(v) for k,v in curated_stats.items()}, source_counts=summary['train_sources']),indent=2)+'\n')
    shutil.copyfile(REVIEW/'fixes.jsonl',FULL/'applied_fixes.jsonl')
    tmp.rename(CURATED)
    (REVIEW/'RELEASE_REPORT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__ == '__main__':
    main()

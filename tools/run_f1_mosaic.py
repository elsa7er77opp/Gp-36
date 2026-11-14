"""Controlled F1 experiment. Default: preflight only. --execute trains and validates.
Requires the existing project environment and data; no dependency installation.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'experiments/f1_mosaic02'
BASE = ROOT / 'runs/detect/v3b_C_11n_960_s0_r2'
NAME = 'v3b_F1_11n_960_mosaic02_s0'
OUT = ROOT / 'review/f1_mosaic02'
RUN = ROOT / 'runs/detect' / NAME
VAL = ROOT / 'runs/detect' / (NAME + '_VALr2_json')
PRED = ROOT / 'runs/detect/v3b_C_11n_960_s0_r2_VALr2_json/predictions.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_config(original, root):
    if original.get('mosaic') != 1.0 or original.get('split') != 'val' or original.get('resume'):
        raise ValueError('Unexpected baseline mosaic/split/resume.')
    if original.get('model') != 'yolo11n.pt' or original.get('optimizer') != 'auto':
        raise ValueError('Unexpected baseline model/optimizer.')
    cfg = dict(original)
    cfg.pop('save_dir', None)
    cfg.pop('cfg', None)
    cfg.update(mosaic=0.2, data=str(root / 'road_hazards_v3b_C/data.yaml'),
               project=str(root / 'runs/detect'), name=NAME, exist_ok=False)
    return cfg


def preflight():
    import yaml
    required = [BASE/'args.yaml', ROOT/'yolo11n.pt', PRED,
                ROOT/'tools/verify_dataset.py', ROOT/'tools/metrics_report.py',
                ROOT/'gp36data/verify.py']
    for dataset in ('road_hazards_v3b_C', 'road_hazards_v3a_r2'):
        required += [ROOT/dataset/x for x in ('data.yaml','manifest.csv','checksums.sha256')]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:
        raise ValueError('Missing project files: ' + ', '.join(missing))
    expected = json.loads((EXP/'expected_environment.json').read_text())
    for package, version in expected['packages'].items():
        actual = importlib.metadata.version(package)
        if actual != version:
            raise ValueError(f'{package}: expected {version}, found {actual}; do not upgrade automatically.')
    original = yaml.safe_load((BASE/'args.yaml').read_text(encoding='utf-8-sig'))
    reference = yaml.safe_load((EXP/'baseline_args.yaml').read_text(encoding='utf-8-sig'))
    # Absolute machine path is metadata, not a training parameter.
    for obj in (original, reference):
        obj.pop('save_dir', None)
    if original != reference:
        raise ValueError('Baseline args changed since F0. Send the current args.yaml.')
    # Pin image membership of C and the full checksum manifest of frozen r2.
    with (ROOT/'road_hazards_v3b_C/manifest.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    fingerprint = hashlib.sha256('\n'.join(sorted(f"{r['split']},{r['out_image']},{r['out_sha256']}" for r in rows)).encode()).hexdigest()
    if fingerprint != '00c94f6ecfdb965d89c4dd9ba3bfee80449fdc8d685937d14532dde8b8d728f5':
        raise ValueError('C image manifest differs from the F0 baseline.')
    checksum_lines = (ROOT/'road_hazards_v3a_r2/checksums.sha256').read_text(encoding='utf-8').splitlines()
    if hashlib.sha256('\n'.join(checksum_lines).encode()).hexdigest() != '4d7ca5f29ca86f0c425f70982ecca6f39469c55f8f1d05a39153a6fb2d757176':
        raise ValueError('Frozen r2 checksum manifest differs from baseline.')
    cfg = make_config(original, ROOT)
    from ultralytics.cfg import get_cfg
    get_cfg(overrides=cfg)  # Validate every key against the installed version.
    yolo = Path(sys.executable).parent / ('yolo.exe' if os.name == 'nt' else 'yolo')
    if not yolo.is_file():
        raise ValueError('YOLO executable missing beside the training Python.')
    for path in (OUT, RUN, VAL):
        if path.exists():
            raise ValueError(f'Refusing to reuse existing output: {path}')
    info = {'changed_training_parameter': {'mosaic': [1.0, 0.2]},
            'baseline_args_sha256': sha(BASE/'args.yaml'),
            'pretrained_sha256': sha(ROOT/'yolo11n.pt'),
            'baseline_val_predictions_sha256': sha(PRED),
            'environment': expected,
            'accept_rule': 'bump AP50 delta >= .02; pothole AP50 delta >= -.02; near bump AP50 delta >= 0. Val only; provisional single seed.',
            'dataset_metadata_sha256': {str(p.relative_to(ROOT)): sha(p) for p in required if p.name in ('data.yaml','manifest.csv','checksums.sha256')}}
    return cfg, info, yolo


# Windows WDDM can list ordinary desktop applications in compute-apps output.
# Only these known UI executables are ignored; Python, YOLO and unknown apps block.
WINDOWS_UI_APPS = frozenset({
    'crossdeviceresume.exe', 'startmenuexperiencehost.exe', 'searchhost.exe',
    'msedgewebview2.exe', 'textinputhost.exe', 'claude.exe', 'rtkuwp.exe',
    'windowsterminal.exe', 'whatsapp.root.exe', 'chatgpt classic.exe',
})


def classify_gpu_processes(output, windows=False):
    ignored, blockers = [], []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        pid, separator, executable = line.partition(',')
        name = executable.strip().strip('"').replace('\\', '/').rsplit('/', 1)[-1].casefold()
        if windows and separator and pid.strip().isdigit() and name in WINDOWS_UI_APPS:
            ignored.append(line)
        else:
            blockers.append(line)
    return ignored, blockers


def check_gpu_idle():
    smi = shutil.which('nvidia-smi')
    if smi is None:
        raise ValueError('nvidia-smi unavailable; cannot verify GPU availability.')
    subprocess.run([smi, '--query-gpu=name', '--format=csv,noheader'], check=True)
    result = subprocess.run([smi, '--query-compute-apps=pid,process_name', '--format=csv,noheader'],
                            check=True, text=True, capture_output=True)
    ignored, blockers = classify_gpu_processes(result.stdout, windows=(os.name == 'nt'))
    if ignored:
        print(f'Ignoring {len(ignored)} known Windows desktop GPU entries (not training jobs).')
    if blockers:
        raise ValueError('Possible GPU training/compute processes detected. Wait for them to finish; no processes will be stopped.\n' + '\n'.join(blockers))
    print('No competing compute process found in the current GPU snapshot.')


def run_logged(command, logfile):
    print('RUN:', subprocess.list2cmdline([str(x) for x in command]), flush=True)
    with logfile.open('x', encoding='utf-8') as log:
        proc = subprocess.Popen([str(x) for x in command], cwd=ROOT, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                text=True, encoding='utf-8', errors='replace')
        messages = queue.Queue()
        def read_output():
            try:
                for line in proc.stdout:
                    messages.put(line)
            finally:
                messages.put(None)
        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        started = time.monotonic()
        try:
            while True:
                try:
                    line = messages.get(timeout=15)
                except queue.Empty:
                    print(f'Still running: {logfile.name} | elapsed {int(time.monotonic()-started)} sec | please wait', flush=True)
                    continue
                if line is None:
                    break
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            code = proc.wait()
        except BaseException:
            print('Waiting for launched process to exit before releasing lock.', flush=True)
            proc.wait()
            raise
    if code:
        raise RuntimeError(f'Command failed ({code}); see {logfile}')


def judge(report):
    models = report['models']
    c, f = models['C']['classes'], models['F1']['classes']
    deltas = {'pothole_AP50': f['pothole']['AP50']-c['pothole']['AP50'],
              'bump_AP50': f['speed_bump']['AP50']-c['speed_bump']['AP50'],
              'near_bump_AP50': f['speed_bump']['near']['AP50']-c['speed_bump']['near']['AP50']}
    passed = deltas['pothole_AP50'] >= -.02 and deltas['bump_AP50'] >= .02 and deltas['near_bump_AP50'] >= 0
    return {'status': 'PROVISIONAL_ACCEPT' if passed else 'REJECT', 'deltas': deltas,
            'note': 'Single seed, validation only. This is not proof of 0.90 test performance.'}


def package_results():
    dest = OUT / 'GP36_F1_results.zip'
    with zipfile.ZipFile(dest, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and p.suffix in ('.json','.md','.yaml','.log'):
                z.write(p, p.relative_to(OUT))
        for name in ('args.yaml','results.csv'):
            p = RUN / name
            if p.is_file():
                z.write(p, 'training/' + name)
    print('SEND THIS FILE:', dest, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--retry-pretraining', action='store_true')
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.retry_pretraining:
        # Archive only attempts that demonstrably stopped before training.
        if not args.execute:
            raise ValueError('--retry-pretraining requires --execute')
        if (ROOT/'.gp36_f1_gpu.lock').exists():
            raise ValueError('Existing run lock found. Do not delete it; send this message for investigation.')
        if RUN.exists() or VAL.exists() or (OUT/'train.log').exists():
            raise ValueError('Training may already have started. Refusing automatic retry; send existing results.')
        if OUT.exists():
            archived = OUT.with_name(OUT.name + '_before_retry_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            OUT.rename(archived)
            print('Previous attempt preserved:', archived, flush=True)
    cfg, info, yolo = preflight()
    print('Preflight OK. F1 = C recipe, mosaic 1.0 -> 0.2. No test inference.')
    if not args.execute:
        print('Preflight only. To start: python tools/run_f1_mosaic.py --execute')
        return
    check_gpu_idle()
    lock = ROOT / '.gp36_f1_gpu.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode()); os.close(fd)
    try:
        import yaml
        OUT.mkdir(parents=True, exist_ok=False)
        (OUT/'plan.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
        cfgfile = OUT/'train_config.yaml'
        cfgfile.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding='utf-8')
        # Existing dataset only: checksums + exact duplicates; no new perceptual-duplicate audit.
        run_logged([sys.executable, '-I', ROOT/'tools/verify_dataset.py', ROOT/'road_hazards_v3b_C', '--no-near-dups'], OUT/'verify_C.log')
        run_logged([sys.executable, '-I', ROOT/'tools/verify_dataset.py', ROOT/'road_hazards_v3a_r2', '--no-near-dups'], OUT/'verify_r2.log')
        run_logged([yolo, 'train', f'cfg={cfgfile}'], OUT/'train.log')
        weights = RUN/'weights/best.pt'
        if not weights.is_file():
            raise RuntimeError('Training did not produce expected best.pt')
        run_logged([yolo, 'val', f'model={weights}', f'data={ROOT / "road_hazards_v3a_r2/data.yaml"}',
                    'split=val', 'imgsz=960', 'batch=8', 'conf=0.001', 'iou=0.7', 'max_det=300',
                    'save_json=True', 'plots=True', f'project={ROOT / "runs/detect"}', f'name={VAL.name}',
                    'exist_ok=False'], OUT/'val.log')
        run_logged([sys.executable, '-I', ROOT/'tools/metrics_report.py', '--data', ROOT/'road_hazards_v3a_r2',
                    '--split', 'val', '--care', 'near', '--by', 'source', '--pred', f'C={PRED}',
                    '--pred', f'F1={VAL / "predictions.json"}', '--out', OUT/'comparison'], OUT/'metrics.log')
        verdict = judge(json.loads((OUT/'comparison/report.json').read_text()))
        (OUT/'verdict.json').write_text(json.dumps(verdict, indent=2), encoding='utf-8')
        print(json.dumps(verdict, indent=2))
    except BaseException as exc:
        if OUT.exists():
            (OUT/'error.json').write_text(json.dumps({'error': str(exc), 'exception_type': type(exc).__name__}, indent=2), encoding='utf-8')
        raise
    finally:
        try:
            if OUT.exists():
                package_results()
        finally:
            lock.unlink(missing_ok=True)


if __name__ == '__main__':
    main()

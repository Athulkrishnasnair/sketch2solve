"""Run the default candidate detector repeatedly on an image directory.

Example (from the repository root):
  backend/.venv/bin/python evaluation/run_perception_baseline.py \
    --input-dir backend/evaluation/sketches \
    --output-dir evaluation/results/phase-a-2026-10-30/detector-baseline
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2


def run(input_dir: Path, output_dir: Path, repeats: int):
    backend_dir = Path(__file__).resolve().parents[1] / 'backend'
    sys.path.insert(0, str(backend_dir))
    from app.services.perception import detect_candidate_geometry, inspect_image_header, render_detections

    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
            continue
        payload = path.read_bytes()
        width, height, mime = inspect_image_header(payload)
        timings, results = [], []
        for _ in range(repeats):
            started = time.perf_counter()
            result = detect_candidate_geometry(payload)
            timings.append((time.perf_counter() - started) * 1000)
            results.append(result)
        if any(result != results[0] for result in results[1:]):
            raise RuntimeError(f'Non-deterministic detector output for {path.name}')
        result = results[0]
        record = result.to_dict()
        record['input'] = {
            'filename': path.name,
            'extension': path.suffix.lower(),
            'detected_mime_type': mime,
            'image_width': width,
            'image_height': height,
            'file_size_bytes': len(payload),
            'sha256': hashlib.sha256(payload).hexdigest(),
        }
        record['measurement'] = {
            'run_count': repeats,
            'runtime_ms_median': statistics.median(timings),
            'runtime_ms_min': min(timings),
            'runtime_ms_max': max(timings),
            'deterministic_across_runs': True,
            'candidate_cap_reached': len(result.lines) == 300,
            'endpoint_cluster_count': len(result.joints),
        }
        records.append(record)
        (output_dir / f'{path.stem}_candidate_overlay.png').write_bytes(render_detections(payload, result))

    return {
        'measured_at_utc': datetime.now(timezone.utc).isoformat(),
        'baseline_type': 'fresh measurement; current default detector configuration',
        'command': (
            'backend/.venv/bin/python evaluation/run_perception_baseline.py '
            f'--input-dir {input_dir.as_posix()} --output-dir {output_dir.as_posix()} --repeats {repeats}'
        ),
        'detector': 'app.services.perception.detect_candidate_geometry(image_bytes) with default PerceptionConfig',
        'opencv_version': cv2.__version__,
        'images': records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be at least 1')
    result = run(args.input_dir, args.output_dir, args.repeats)
    (args.output_dir / 'baseline.json').write_text(json.dumps(result, indent=2) + '\n')
    for image in result['images']:
        print(
            f"{image['input']['filename']}: {image['input']['detected_mime_type']} "
            f"{image['image_width']}x{image['image_height']}; "
            f"{len(image['lines'])} lines; {len(image['joints'])} endpoint clusters; "
            f"cap={image['measurement']['candidate_cap_reached']}; "
            f"median={image['measurement']['runtime_ms_median']:.3f} ms; "
            f"warnings={image['warnings']}"
        )


if __name__ == '__main__':
    main()

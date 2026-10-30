"""Create visual review sheets without assigning ground-truth labels."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_IMAGES = ("test1.jpg", "test2.jpg", "test3.png", "test4.jpg", "test5.png")


def image_metadata(path: Path) -> tuple[str, int, int]:
    content = path.read_bytes()
    decoded = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if decoded is None:
        raise ValueError(f"Could not decode evaluation image: {path.name}")
    height, width = decoded.shape[:2]
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif content.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
    elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        mime_type = "image/webp"
    else:
        raise ValueError(f"Unrecognized image signature: {path.name}")
    return mime_type, width, height


def review_sheet(result: dict, mime_type: str, width: int, height: int) -> str:
    filename = escape(result["filename"])
    stem = Path(filename).stem
    detection_image = f"../../evaluation/results/{stem}_final_default_opencv_4_14_0.png"
    source_image = f"../../backend/evaluation/sketches/{filename}"
    x_left, x_right, y_base, y_peak = width * 0.1, width * 0.9, height * 0.85, height * 0.2
    x_mid = width * 0.5
    lines = (
        f'<line x1="{x_left}" y1="{y_base}" x2="{x_right}" y2="{y_base}" />'
        f'<line x1="{x_left}" y1="{y_base}" x2="{x_mid}" y2="{y_peak}" />'
        f'<line x1="{x_right}" y1="{y_base}" x2="{x_mid}" y2="{y_peak}" />'
    )
    joints = "".join(
        f'<circle cx="{x}" cy="{y}" r="{max(width, height) * 0.008}" />'
        for x, y in ((x_left, y_base), (x_right, y_base), (x_mid, y_peak))
    )
    mock_data = json.dumps({
        "proposal_only": True,
        "test_fixture": "Synthetic triangle; not derived from this sketch",
        "image_width": width,
        "image_height": height,
        "joint_count": 3,
        "member_count": 3,
        "review_status": "pending_review",
    }, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QA review sheet — {filename}</title>
  <style>
    body {{ margin: 0; padding: 2rem; color: #252821; background: #f5f4ef; font: 15px/1.5 system-ui, sans-serif; }}
    main {{ max-width: 1200px; margin: auto; }}
    h1 {{ margin-bottom: .25rem; }}
    .status, .warning {{ padding: 1rem; border-radius: .6rem; }}
    .status {{ background: #fff1d6; }}
    .warning {{ margin: 1rem 0; color: #6b3a17; background: #ffeadb; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
    figure {{ margin: 0; padding: .8rem; background: white; border: 1px solid #deded7; border-radius: .6rem; }}
    figure img {{ display: block; width: 100%; height: auto; }}
    .proposal {{ position: relative; }}
    .proposal svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
    .proposal line {{ stroke: #d97627; stroke-width: 7; stroke-linecap: round; }}
    .proposal circle {{ fill: #fff; stroke: #b94a20; stroke-width: 5; }}
    pre {{ overflow: auto; padding: 1rem; background: #f5f4ef; }}
  </style>
</head>
<body>
<main>
  <h1>Review sheet: {filename}</h1>
  <p>{escape(mime_type)} · {width} × {height} px · {result["size_bytes"]:,} bytes · OpenCV candidates: {result["opencv_candidate_lines"]}</p>
  <p class="status"><strong>Human-review status: REQUIRED — NOT REVIEWED.</strong> No ground-truth geometry is present for this dataset item.</p>
  <p class="warning"><strong>Mock proposal only:</strong> The orange triangle is deterministic test-fixture data returned to test the interface. It is not inferred from, or a proposed interpretation of, this image. Do not compare it with the sketch or treat it as a label.</p>
  <div class="grid">
    <figure><figcaption>Original evaluation sketch</figcaption><img src="{source_image}" alt="Original sketch {filename}"></figure>
    <figure><figcaption>Saved OpenCV candidate overlay · {result["opencv_candidate_lines"]} candidate segments</figcaption><img src="{detection_image}" alt="OpenCV overlay for {filename}"></figure>
    <figure>
      <figcaption>Synthetic mocked proposal — not image-derived</figcaption>
      <div class="proposal"><img src="{source_image}" alt="Source image under a test-only proposal overlay"><svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" aria-label="Synthetic test triangle, not an interpretation">{lines}{joints}</svg></div>
    </figure>
    <figure><figcaption>Mock response metadata</figcaption><pre>{escape(mock_data)}</pre></figure>
  </div>
</main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    output = arguments.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing review-sheet output: {output}")

    results = json.loads(arguments.results.read_text(encoding="utf-8"))
    images = results["evaluation_images"]
    if tuple(item["filename"] for item in images) != EXPECTED_IMAGES:
        raise ValueError("Upload results do not contain the five discovered evaluation images in sorted order.")

    output.mkdir(parents=True)
    for result in images:
        path = ROOT / "backend" / "evaluation" / "sketches" / result["filename"]
        mime_type, width, height = image_metadata(path)
        if mime_type != result["detected_format"]:
            raise ValueError(f"Detected format changed for {result['filename']}.")
        (output / f"{Path(result['filename']).stem}.html").write_text(
            review_sheet(result, mime_type, width, height),
            encoding="utf-8",
        )

    links = "\n".join(
        f"- [{filename}](./{Path(filename).stem}.html)"
        for filename in EXPECTED_IMAGES
    )
    (output / "index.html").write_text(
        f"<!doctype html><meta charset=\"utf-8\"><title>Sketch2Solve QA review sheets</title>"
        f"<h1>Sketch2Solve QA review sheets</h1><p>Ground truth is absent; all images require human review.</p><ul>"
        + "".join(f"<li><a href=\"{Path(filename).stem}.html\">{escape(filename)}</a></li>" for filename in EXPECTED_IMAGES)
        + "</ul>",
        encoding="utf-8",
    )
    (output / "README.txt").write_text(
        "The original and OpenCV images link to repository evaluation assets. "
        "The orange proposal overlay is synthetic test-fixture data, not an AI interpretation or ground truth.\n",
        encoding="utf-8",
    )
    print(f"Generated {len(EXPECTED_IMAGES)} review sheets under {output}")


if __name__ == "__main__":
    main()

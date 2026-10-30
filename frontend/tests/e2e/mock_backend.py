"""Isolated Flask server used by browser tests; no real provider requests."""

from __future__ import annotations

import signal
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
from flask import abort, request, send_file

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))

from app import create_app
from app.services.gemini_interpretation import (
    GeminiAPIError,
    GeminiAuthenticationError,
    GeminiNetworkError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    InvalidGeminiResponseError,
    MissingGeminiAPIKeyError,
)


_PROVIDER_FAILURES = {
    "MISSING_GEMINI_API_KEY": MissingGeminiAPIKeyError,
    "GEMINI_AUTHENTICATION_FAILED": GeminiAuthenticationError,
    "GEMINI_RATE_LIMITED": GeminiRateLimitError,
    "GEMINI_TIMEOUT": GeminiTimeoutError,
    "GEMINI_NETWORK_ERROR": GeminiNetworkError,
    "INVALID_GEMINI_RESPONSE": InvalidGeminiResponseError,
    "GEMINI_API_ERROR": GeminiAPIError,
}


class MockProposal:
    def __init__(self, *, width: int, height: int, empty: bool = False):
        scale_x = max(width, 1)
        scale_y = max(height, 1)
        self.payload = {
            "image_width": width,
            "image_height": height,
            "coordinate_space": "original_image_pixels",
            "joints": [] if empty else [
                {"id": "J1", "x": scale_x * 0.1, "y": scale_y * 0.85},
                {"id": "J2", "x": scale_x * 0.9, "y": scale_y * 0.85},
                {"id": "J3", "x": scale_x * 0.5, "y": scale_y * 0.2},
            ],
            "members": [] if empty else [
                {"id": "M1", "joint_i": "J1", "joint_j": "J2", "connection_uncertain": False},
                {"id": "M2", "joint_i": "J1", "joint_j": "J3", "connection_uncertain": False},
                {"id": "M3", "joint_i": "J2", "joint_j": "J3", "connection_uncertain": False},
            ],
            "supports": [] if empty else [
                {"id": "S1", "x": scale_x * 0.1, "y": scale_y * 0.85, "possible_type": "pin", "uncertain": False},
                {"id": "S2", "x": scale_x * 0.9, "y": scale_y * 0.85, "possible_type": "roller", "uncertain": False},
            ],
            "loads": [] if empty else [
                {"id": "L1", "x": scale_x * 0.5, "y": scale_y * 0.2, "direction": "downward"},
            ],
            "ambiguities": ["This is synthetic test data, not an interpretation of the uploaded image."],
            "missing_information": ["Physical dimensions and units are not inferred."],
            "proposal_only": True,
        }

    def to_dict(self) -> dict:
        return self.payload


def mocked_interpretation(image_bytes: bytes, *, mime_type: str, **_kwargs) -> MockProposal:
    scenario = request.headers.get("X-QA-Mock-Provider", "")
    failure = _PROVIDER_FAILURES.get(scenario)
    if failure is not None:
        raise failure()

    if scenario == "MALFORMED_PROVIDER_MESSAGE":
        raise InvalidGeminiResponseError("The mock provider returned a malformed response.")

    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise AssertionError("A corrupt image reached the mocked provider.")
    height, width = image.shape[:2]
    return MockProposal(width=width, height=height, empty=scenario == "EMPTY_PROPOSAL")


def stop_server(_signal_number: int, _frame) -> None:
    raise SystemExit(0)


def main() -> None:
    signal.signal(signal.SIGTERM, stop_server)
    signal.signal(signal.SIGINT, stop_server)

    with tempfile.TemporaryDirectory(prefix="sketch2solve-playwright-") as directory:
        root = Path(directory)
        app = create_app({
            "TESTING": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{root / 'qa.sqlite'}",
            "UPLOAD_FOLDER": str(root / "uploads"),
        })
        sketches = Path(__file__).resolve().parents[3] / "backend" / "evaluation" / "sketches"

        @app.get("/__qa__/sketches/<filename>")
        def serve_evaluation_fixture(filename: str):
            image = sketches / filename
            if filename not in {f"test{index}.{extension}" for index in range(1, 6) for extension in ("jpg", "png")} or not image.is_file():
                abort(404)
            return send_file(image, conditional=True, max_age=0)

        with patch(
            "app.routes.analyses.interpretation_provider.interpret_truss_sketch",
            side_effect=mocked_interpretation,
        ):
            app.run(host="127.0.0.1", port=5101, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()

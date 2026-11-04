"""Configuration-based dispatch for isolated interpretation providers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.services import muse_interpretation


BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
SUPPORTED_PROVIDERS = frozenset({"meta"})


def resolve_provider(provider: str | None = None) -> str:
    """Return the active provider after loading local, non-secret settings.

    Meta is the only active provider. Gemini has been removed from active dispatch.
    """
    load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
    selected = (provider or os.environ.get("INTERPRETATION_PROVIDER", "meta")).strip().lower()
    if selected != "meta":
        raise ValueError("INTERPRETATION_PROVIDER must be 'meta'. Gemini is not supported in active dispatch.")
    return "meta"


def model_id_for(provider: str = "meta") -> str:
    """Return the configured model identifier without exposing credentials."""
    if provider == "meta":
        return os.environ.get("MODEL_NAME", muse_interpretation.MUSE_MODEL).strip() or muse_interpretation.MUSE_MODEL
    raise ValueError("INTERPRETATION_PROVIDER must be 'meta'.")


def interpret_truss_sketch(
    image_bytes: bytes,
    *,
    provider: str | None = None,
    mime_type: str | None = None,
    timeout_seconds: float | None = None,
    client: Any | None = None,
):
    """Dispatch exclusively to the Meta provider while preserving proposal semantics.

    Meta Model API (Muse Spark) is the only active interpretation provider.
    """
    resolve_provider(provider)

    kwargs = {"mime_type": mime_type, "client": client}
    if timeout_seconds is not None:
        kwargs["timeout_seconds"] = timeout_seconds
    return muse_interpretation.interpret_truss_sketch(image_bytes, **kwargs)

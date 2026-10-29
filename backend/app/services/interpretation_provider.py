"""Configuration-based dispatch for isolated interpretation providers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.services import gemini_interpretation, muse_interpretation


BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
SUPPORTED_PROVIDERS = frozenset({"meta", "gemini"})


def resolve_provider(provider: str | None = None) -> str:
    """Return a supported provider after loading local, non-secret settings."""
    load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
    selected = (provider or os.environ.get("INTERPRETATION_PROVIDER", "meta")).strip().lower()
    if selected not in SUPPORTED_PROVIDERS:
        raise ValueError("INTERPRETATION_PROVIDER must be 'meta' or 'gemini'.")
    return selected


def model_id_for(provider: str) -> str:
    """Return the configured model identifier without exposing credentials."""
    if provider == "gemini":
        return os.environ.get("GEMINI_MODEL", gemini_interpretation.DEFAULT_GEMINI_MODEL).strip() or gemini_interpretation.DEFAULT_GEMINI_MODEL
    if provider == "meta":
        return muse_interpretation.MUSE_MODEL
    raise ValueError("INTERPRETATION_PROVIDER must be 'meta' or 'gemini'.")


def interpret_truss_sketch(
    image_bytes: bytes,
    *,
    provider: str | None = None,
    mime_type: str | None = None,
    timeout_seconds: float | None = None,
    client: Any | None = None,
):
    """Dispatch to the configured provider while preserving proposal semantics.

    `INTERPRETATION_PROVIDER` may be `meta` (default) or `gemini`. Values from
    the process environment take precedence over entries in backend/.env.
    """
    selected = resolve_provider(provider)

    adapter = gemini_interpretation if selected == "gemini" else muse_interpretation
    kwargs = {"mime_type": mime_type, "client": client}
    if timeout_seconds is not None:
        kwargs["timeout_seconds"] = timeout_seconds
    return adapter.interpret_truss_sketch(image_bytes, **kwargs)

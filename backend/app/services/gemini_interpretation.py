"""Gemini adapter for untrusted visual truss interpretation proposals."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.services import muse_interpretation as _shared


DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 60.0
BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class GeminiInterpretationError(RuntimeError):
    """Base class for sanitized Gemini adapter failures."""

    code = "GEMINI_INTERPRETATION_FAILED"


class MissingGeminiAPIKeyError(GeminiInterpretationError):
    code = "MISSING_GEMINI_API_KEY"

    def __init__(self) -> None:
        super().__init__("GEMINI_API_KEY is not configured.")


class GeminiAPIError(GeminiInterpretationError):
    code = "GEMINI_API_ERROR"

    def __init__(self) -> None:
        super().__init__("Gemini API request failed.")


class GeminiAuthenticationError(GeminiInterpretationError):
    code = "GEMINI_AUTHENTICATION_FAILED"

    def __init__(self) -> None:
        super().__init__("Gemini authentication failed. Check the server-side credential and account access.")


class GeminiRateLimitError(GeminiInterpretationError):
    code = "GEMINI_RATE_LIMITED"

    def __init__(self) -> None:
        super().__init__("Gemini rate limit or quota was reached. Try again later.")


class GeminiInvalidModelError(GeminiInterpretationError):
    code = "GEMINI_INVALID_MODEL"

    def __init__(self) -> None:
        super().__init__("Gemini rejected the configured model. Check the model setting.")


class GeminiTimeoutError(GeminiInterpretationError):
    code = "GEMINI_TIMEOUT"

    def __init__(self) -> None:
        super().__init__("Gemini request timed out.")


class GeminiNetworkError(GeminiInterpretationError):
    code = "GEMINI_NETWORK_ERROR"

    def __init__(self) -> None:
        super().__init__("Gemini could not be reached. Check the backend network connection.")


class InvalidGeminiResponseError(GeminiInterpretationError):
    code = "INVALID_GEMINI_RESPONSE"


def interpret_truss_sketch(
    image_bytes: bytes,
    *,
    mime_type: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    client: Any | None = None,
) -> _shared.TrussInterpretationProposal:
    """Return a validated, proposal-only interpretation from Gemini.

    The local backend `.env` is loaded without overriding environment values.
    A client may be injected for tests; tests should never make a real request.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive finite number.")

    load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise MissingGeminiAPIKeyError()

    width, height, detected_mime = _shared._inspect_image(image_bytes, mime_type)
    use_sdk = client is None
    if use_sdk:
        client = _build_client(api_key, timeout_seconds)

    image_part = _image_part(image_bytes, detected_mime, use_sdk=use_sdk)
    try:
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
            contents=[_shared._USER_PROMPT, image_part],
            config={
                "system_instruction": _shared._SYSTEM_INSTRUCTIONS,
                "response_mime_type": "application/json",
                "response_json_schema": _shared._INTERPRETATION_SCHEMA,
                "temperature": 0,
            },
        )
    except Exception as error:
        # SDK errors can contain request details; retain only a stable public code/message.
        raise _safe_provider_error(error) from error

    output_text = getattr(response, "text", None)
    if not isinstance(output_text, str) or not output_text.strip():
        raise InvalidGeminiResponseError("Gemini returned no structured text.")
    try:
        payload = json.loads(output_text)
        return _shared._parse_proposal(payload, width=width, height=height)
    except _shared.InvalidMuseResponseError as error:
        raise InvalidGeminiResponseError("Gemini returned an invalid interpretation proposal.") from error
    except json.JSONDecodeError as error:
        raise InvalidGeminiResponseError("Gemini returned malformed JSON.") from error


def _build_client(api_key: str, timeout_seconds: float) -> Any:
    """Create the official Google Gen AI SDK client only when making a request."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise GeminiInterpretationError(
            "Install the google-genai dependency to use the Gemini provider."
        ) from error
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=max(1, int(timeout_seconds * 1000))),
    )


def _image_part(image_bytes: bytes, mime_type: str, *, use_sdk: bool) -> Any:
    if use_sdk:
        try:
            from google.genai import types
        except ImportError:
            # A patched client in unit tests may stand in for the absent SDK.
            pass
        else:
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    # The SDK accepts Part-shaped dictionaries too. This form keeps injected
    # mock clients testable when google-genai is not installed locally.
    return {"inline_data": {"mime_type": mime_type, "data": image_bytes}}


def _safe_provider_error(error: Exception) -> GeminiInterpretationError:
    name = type(error).__name__.lower()
    if isinstance(error, TimeoutError) or "timeout" in name:
        return GeminiTimeoutError()
    if isinstance(error, (ConnectionError, OSError)) or "connection" in name:
        return GeminiNetworkError()

    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(error, "code", None)
    normalized = str(status).upper()
    if status in (401, 403) or normalized in {"UNAUTHENTICATED", "PERMISSION_DENIED"}:
        return GeminiAuthenticationError()
    if status == 429 or normalized in {"RESOURCE_EXHAUSTED", "TOO_MANY_REQUESTS"}:
        return GeminiRateLimitError()
    if status == 404 or normalized in {"NOT_FOUND", "MODEL_NOT_FOUND"}:
        return GeminiInvalidModelError()
    return GeminiAPIError()

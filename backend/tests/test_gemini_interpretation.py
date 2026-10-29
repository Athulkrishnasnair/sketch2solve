"""Mocked tests for the Gemini sketch interpretation adapter and selector."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from app.services import gemini_interpretation as gemini
from app.services import interpretation_provider
from app.services import muse_interpretation
from test_muse_interpretation import valid_payload


def image_bytes(width=80, height=40, image_format=".png"):
    ok, encoded = cv2.imencode(image_format, np.full((height, width, 3), 235, dtype=np.uint8))
    if not ok:
        raise AssertionError(f"Synthetic {image_format} encoding failed")
    return encoded.tobytes()


class FakeModels:
    def __init__(self, response_text=None, error=None):
        self.response_text = response_text
        self.error = error
        self.kwargs = None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.response_text)


class FakeClient:
    def __init__(self, models):
        self.models = models


class GeminiInterpretationTests(unittest.TestCase):
    def test_success_reads_configured_key_and_returns_reviewable_candidates(self):
        fake = FakeClient(FakeModels(response_text=json.dumps(valid_payload())))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-key"}, clear=True), patch.object(
            gemini, "load_dotenv", return_value=True
        ) as dotenv_loader, patch.object(gemini, "_build_client", return_value=fake) as build_client:
            result = gemini.interpret_truss_sketch(image_bytes(), timeout_seconds=7, mime_type="image/jpeg")

        dotenv_loader.assert_called_once_with(dotenv_path=gemini.BACKEND_ENV_PATH, override=False)
        build_client.assert_called_once_with("test-gemini-key", 7)
        self.assertEqual((result.image_width, result.image_height), (80, 40))
        self.assertTrue(result.to_dict()["proposal_only"])
        self.assertTrue(result.members[0].connection_uncertain)
        request = fake.models.kwargs
        self.assertEqual(request["model"], "gemini-3.1-flash-lite")
        self.assertEqual(request["config"]["response_mime_type"], "application/json")
        self.assertIn("response_json_schema", request["config"])
        part = request["contents"][1]
        inline_data = part.inline_data if hasattr(part, "inline_data") else part["inline_data"]
        self.assertEqual(inline_data.mime_type if hasattr(inline_data, "mime_type") else inline_data["mime_type"], "image/png")
        self.assertEqual(inline_data.data if hasattr(inline_data, "data") else inline_data["data"], image_bytes())

    def test_gemini_model_can_be_overridden_from_configuration(self):
        fake = FakeClient(FakeModels(response_text=json.dumps(valid_payload())))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "test-model"}, clear=True), patch.object(
            gemini, "load_dotenv", return_value=False
        ):
            gemini.interpret_truss_sketch(image_bytes(), client=fake)
        self.assertEqual(fake.models.kwargs["model"], "test-model")

    def test_malformed_or_empty_output_is_rejected(self):
        for output in ("not json", " ", None, json.dumps({})):
            with self.subTest(output=output), patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True), patch.object(
                gemini, "load_dotenv", return_value=False
            ):
                fake = FakeClient(FakeModels(response_text=output))
                with self.assertRaises(gemini.InvalidGeminiResponseError):
                    gemini.interpret_truss_sketch(image_bytes(), client=fake)

    def test_missing_credentials_fail_without_client_creation(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(gemini, "load_dotenv", return_value=False), patch.object(
            gemini, "_build_client"
        ) as build_client:
            with self.assertRaises(gemini.MissingGeminiAPIKeyError):
                gemini.interpret_truss_sketch(image_bytes())
        build_client.assert_not_called()

    def test_api_failures_are_sanitized(self):
        fake = FakeClient(FakeModels(error=RuntimeError("private response and credential details")))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True), patch.object(
            gemini, "load_dotenv", return_value=False
        ):
            with self.assertRaises(gemini.GeminiAPIError) as context:
                gemini.interpret_truss_sketch(image_bytes(), client=fake)
        self.assertNotIn("private", str(context.exception))
        self.assertNotIn("credential", str(context.exception))

    def test_api_statuses_are_classified_as_safe_actionable_errors(self):
        cases = (
            (SimpleNamespace(status_code=401), gemini.GeminiAuthenticationError, "GEMINI_AUTHENTICATION_FAILED"),
            (SimpleNamespace(status_code=429), gemini.GeminiRateLimitError, "GEMINI_RATE_LIMITED"),
            (SimpleNamespace(status_code=404), gemini.GeminiInvalidModelError, "GEMINI_INVALID_MODEL"),
            (TimeoutError("private timeout text"), gemini.GeminiTimeoutError, "GEMINI_TIMEOUT"),
            (ConnectionError("private endpoint text"), gemini.GeminiNetworkError, "GEMINI_NETWORK_ERROR"),
        )
        for cause, error_type, code in cases:
            with self.subTest(code=code):
                error = gemini._safe_provider_error(cause)
                self.assertIsInstance(error, error_type)
                self.assertEqual(error.code, code)
                self.assertNotIn("private", str(error))

    def test_provider_inline_data_uses_verified_mime_for_each_supported_format(self):
        for image_format, expected_mime in ((".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp")):
            with self.subTest(image_format=image_format), patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True), patch.object(
                gemini, "load_dotenv", return_value=False
            ):
                content = image_bytes(image_format=image_format)
                fake = FakeClient(FakeModels(response_text=json.dumps(valid_payload())))
                gemini.interpret_truss_sketch(content, mime_type="image/png", client=fake)
                part = fake.models.kwargs["contents"][1]
                inline_data = part.inline_data if hasattr(part, "inline_data") else part["inline_data"]
                actual_mime = inline_data.mime_type if hasattr(inline_data, "mime_type") else inline_data["mime_type"]
                actual_data = inline_data.data if hasattr(inline_data, "data") else inline_data["data"]
                self.assertEqual(actual_mime, expected_mime)
                self.assertEqual(actual_data, content)

    def test_dispatcher_selects_gemini_or_meta_from_configuration(self):
        expected = object()
        with patch.dict(os.environ, {"INTERPRETATION_PROVIDER": "gemini"}, clear=True), patch.object(
            interpretation_provider, "load_dotenv", return_value=False
        ), patch.object(gemini, "interpret_truss_sketch", return_value=expected) as gemini_call:
            self.assertIs(interpretation_provider.interpret_truss_sketch(image_bytes()), expected)
        gemini_call.assert_called_once()

        with patch.dict(os.environ, {"INTERPRETATION_PROVIDER": "meta"}, clear=True), patch.object(
            interpretation_provider, "load_dotenv", return_value=False
        ), patch.object(muse_interpretation, "interpret_truss_sketch", return_value=expected) as meta_call:
            self.assertIs(interpretation_provider.interpret_truss_sketch(image_bytes()), expected)
        meta_call.assert_called_once()


if __name__ == "__main__":
    unittest.main()

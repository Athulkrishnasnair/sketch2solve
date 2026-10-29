"""Mocked tests for the isolated Muse Spark sketch adapter."""

import base64
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import httpx
import numpy as np
from openai import APIStatusError, APITimeoutError

from app.services import muse_interpretation as muse


def image_bytes(width=80, height=40, image_format=".png"):
    ok, encoded = cv2.imencode(image_format, np.full((height, width, 3), 235, dtype=np.uint8))
    if not ok:
        raise AssertionError(f"Synthetic {image_format} encoding failed")
    return encoded.tobytes()


def valid_payload():
    return {
        "joints": [
            {"id": "J1", "x_1000": 0, "y_1000": 0},
            {"id": "J2", "x_1000": 1000, "y_1000": 1000},
        ],
        "members": [
            {"id": "M1", "joint_i": "J1", "joint_j": "J2", "connection_uncertain": True, "notes": "Possible crossing."}
        ],
        "supports": [
            {"id": "S1", "x_1000": 1000, "y_1000": 0, "possible_type": "roller", "uncertain": False, "notes": "Visible roller symbol."}
        ],
        "loads": [
            {"id": "L1", "x_1000": 500, "y_1000": 250, "direction": "downward", "magnitude": 10, "unit": "kN", "uncertain": False, "notes": "Text is legible."},
            {"id": "L2", "x_1000": 500, "y_1000": 750, "direction": "rightward", "magnitude": None, "unit": None, "uncertain": True, "notes": "No readable magnitude."},
        ],
        "ambiguities": ["M1 may be a crossing rather than a connected joint."],
        "missing_information": ["Material and dimensions are not specified."],
    }


class FakeResponses:
    def __init__(self, output_text=None, error=None):
        self.output_text = output_text
        self.error = error
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.output_text)


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


class MuseInterpretationTests(unittest.TestCase):
    def invoke(self, payload=None, *, client=None, content=None, **kwargs):
        payload = valid_payload() if payload is None else payload
        output_text = json.dumps(payload)
        fake = client or FakeClient(FakeResponses(output_text=output_text))
        result = muse.interpret_truss_sketch(content or image_bytes(), client=fake, **kwargs)
        return result, fake

    def test_success_parses_candidates_preserves_pixel_dimensions_and_evidence(self):
        result, client = self.invoke(timeout_seconds=13.5, mime_type="image/jpeg")
        self.assertEqual((result.image_width, result.image_height), (80, 40))
        self.assertEqual(result.coordinate_space, "original_image_pixels")
        self.assertEqual(result.coordinate_convention, "origin_top_left_x_right_y_down")
        self.assertEqual((result.joints[0].x, result.joints[0].y), (0, 0))
        self.assertEqual((result.joints[1].x, result.joints[1].y), (79, 39))
        self.assertTrue(result.members[0].connection_uncertain)
        self.assertEqual(result.loads[0].magnitude, 10.0)
        self.assertEqual(result.loads[0].unit, "kN")
        self.assertIsNone(result.loads[1].magnitude)
        self.assertIsNone(result.loads[1].unit)
        self.assertEqual(result.ambiguities, ("M1 may be a crossing rather than a connected joint.",))
        self.assertTrue(result.to_dict()["proposal_only"])
        call = client.responses.kwargs
        self.assertEqual(call["model"], "muse-spark-1.3")
        self.assertEqual(call["timeout"], 13.5)
        self.assertFalse(call["store"])
        self.assertEqual(call["text"]["format"]["type"], "json_schema")
        self.assertIn("uncertain", call["instructions"])
        image_part = call["input"][0]["content"][1]
        data_url = image_part["image_url"]
        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        encoded = data_url.split(",", 1)[1]
        self.assertEqual(base64.b64decode(encoded), image_bytes())

    def test_openai_client_uses_meta_configuration_and_key_from_environment(self):
        fake = FakeClient(FakeResponses(output_text=json.dumps(valid_payload())))
        with patch.dict(os.environ, {"MODEL_API_KEY": "test-key"}, clear=True), patch.object(
            muse, "OpenAI", return_value=fake
        ) as constructor:
            muse.interpret_truss_sketch(image_bytes(), timeout_seconds=9)
        constructor.assert_called_once_with(
            base_url="https://api.meta.ai/v1",
            api_key="test-key",
            timeout=9,
            max_retries=0,
        )

    def test_missing_api_key_fails_without_constructing_client(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(muse.MissingModelAPIKeyError):
            muse.interpret_truss_sketch(image_bytes())

    def test_malformed_json_and_empty_response_are_controlled_errors(self):
        for text in ("not json", " ", None):
            with self.subTest(text=text):
                fake = FakeClient(FakeResponses(output_text=text))
                with self.assertRaises(muse.InvalidMuseResponseError):
                    muse.interpret_truss_sketch(image_bytes(), client=fake)

    def test_missing_or_out_of_range_coordinates_are_rejected(self):
        missing = valid_payload()
        del missing["joints"][0]["x_1000"]
        out_of_range = valid_payload()
        out_of_range["joints"][0]["x_1000"] = 1001
        for payload in (missing, out_of_range):
            with self.subTest(payload=payload):
                fake = FakeClient(FakeResponses(output_text=json.dumps(payload)))
                with self.assertRaises(muse.InvalidMuseResponseError):
                    muse.interpret_truss_sketch(image_bytes(), client=fake)

    def test_member_references_and_magnitude_units_are_validated(self):
        bad_reference = valid_payload()
        bad_reference["members"][0]["joint_j"] = "missing"
        bad_units = valid_payload()
        bad_units["loads"][0]["unit"] = None
        for payload in (bad_reference, bad_units):
            with self.subTest(payload=payload):
                fake = FakeClient(FakeResponses(output_text=json.dumps(payload)))
                with self.assertRaises(muse.InvalidMuseResponseError):
                    muse.interpret_truss_sketch(image_bytes(), client=fake)

    def test_timeout_and_api_errors_are_wrapped_without_internal_details(self):
        request = httpx.Request("POST", "https://api.meta.ai/v1/responses")
        timeout_client = FakeClient(FakeResponses(error=APITimeoutError(request=request)))
        with self.assertRaises(muse.MuseTimeoutError) as timeout_context:
            muse.interpret_truss_sketch(image_bytes(), client=timeout_client, timeout_seconds=2)
        self.assertEqual(str(timeout_context.exception), "Muse Model API request timed out.")
        self.assertEqual(timeout_client.responses.kwargs["timeout"], 2)

        response = httpx.Response(401, request=request)
        error_client = FakeClient(FakeResponses(error=APIStatusError("private response body", response=response, body={"secret": "hidden"})))
        with self.assertRaises(muse.MuseAPIError) as api_context:
            muse.interpret_truss_sketch(image_bytes(), client=error_client)
        self.assertEqual(api_context.exception.status_code, 401)
        self.assertEqual(api_context.exception.code, "MUSE_AUTHENTICATION_FAILED")
        self.assertNotIn("private", str(api_context.exception))
        self.assertNotIn("secret", str(api_context.exception))

    def test_provider_statuses_are_classified_without_reflecting_response_bodies(self):
        for status, expected in ((403, "MUSE_AUTHENTICATION_FAILED"), (404, "MUSE_INVALID_MODEL"), (429, "MUSE_RATE_LIMITED")):
            with self.subTest(status=status):
                error = muse.MuseAPIError(status)
                self.assertEqual(error.code, expected)
                self.assertNotIn(str(status), str(error))

    def test_invalid_image_and_invalid_timeout_fail_before_api_call(self):
        fake = FakeClient(FakeResponses(output_text=json.dumps(valid_payload())))
        with self.assertRaises(muse.InvalidSketchImageError):
            muse.interpret_truss_sketch(b"bad image", client=fake)
        with self.assertRaises(ValueError):
            muse.interpret_truss_sketch(image_bytes(), client=fake, timeout_seconds=0)
        self.assertIsNone(fake.responses.kwargs)

    def test_provider_data_url_uses_verified_mime_for_each_supported_format(self):
        for image_format, expected_mime in ((".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp")):
            with self.subTest(image_format=image_format):
                content = image_bytes(image_format=image_format)
                _, client = self.invoke(content=content, mime_type="image/png")
                data_url = client.responses.kwargs["input"][0]["content"][1]["image_url"]
                self.assertTrue(data_url.startswith(f"data:{expected_mime};base64,"))
                self.assertEqual(base64.b64decode(data_url.split(",", 1)[1]), content)


if __name__ == "__main__":
    unittest.main()

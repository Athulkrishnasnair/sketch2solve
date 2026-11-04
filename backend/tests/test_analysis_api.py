"""Persistence and review API tests; provider calls are mocked."""

from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np
from sqlalchemy.exc import SQLAlchemyError
from app import create_app
from app.extensions import db
from app.models.analysis import SketchAnalysis
from app.services.analysis_persistence import AnalysisPersistenceError, begin_analysis
from app.services.muse_interpretation import MuseAPIError


def image_bytes(width=96, height=64, image_format=".png"):
    image = np.full((height, width, 3), 245, dtype=np.uint8)
    cv2.line(image, (8, 55), (48, 10), (10, 10, 10), 2)
    cv2.line(image, (48, 10), (88, 55), (10, 10, 10), 2)
    ok, encoded = cv2.imencode(image_format, image)
    if not ok:
        raise AssertionError(f"Synthetic {image_format} encoding failed")
    return encoded.tobytes()


class FakeProposal:
    def to_dict(self):
        return {
            "image_width": 96,
            "image_height": 64,
            "coordinate_space": "original_image_pixels",
            "joints": [{"id": "J1", "x": 8, "y": 55}],
            "members": [],
            "supports": [],
            "loads": [],
            "ambiguities": ["Support is unclear."],
            "missing_information": ["Dimensions are not visible."],
            "proposal_only": True,
        }


class AnalysisApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_FOLDER": self.tempdir.name,
            "MAX_ANALYSIS_IMAGE_BYTES": 4096,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
        self.tempdir.cleanup()

    def upload(self, content=None, filename="drawing.png", mime="image/png", provider="meta"):
        return self.client.post(
            "/api/analyses",
            data={
                "provider": provider,
                "image": (BytesIO(image_bytes() if content is None else content), filename, mime),
            },
            content_type="multipart/form-data",
        )

    def create_reviewable_analysis(self):
        with patch("app.routes.analyses.interpretation_provider.interpret_truss_sketch", return_value=FakeProposal()):
            return self.upload().get_json()

    @staticmethod
    def valid_human_geometry():
        return {
            "schema_version": "1.0",
            "metadata": {"name": "Reviewed sketch", "source": "human_review", "units": {"length": "m", "force": "N"}},
            "model": {
                "nodes": [
                    {"id": "J1", "x": 0, "y": 0},
                    {"id": "J2", "x": 4, "y": 0},
                    {"id": "J3", "x": 2, "y": 3},
                ],
                "members": [
                    {"id": "M1", "node_i": "J1", "node_j": "J2"},
                    {"id": "M2", "node_i": "J1", "node_j": "J3"},
                    {"id": "M3", "node_i": "J2", "node_j": "J3"},
                ],
                "supports": [
                    {"id": "S1", "node": "J1", "type": "pin"},
                    {"id": "S2", "node": "J2", "type": "roller", "direction": "vertical"},
                ],
                "loads": [{"id": "L1", "node": "J3", "fx": 0, "fy": -10}],
            },
        }

    def test_successful_analysis_is_saved_and_available_through_history_and_image_routes(self):
        with patch("app.routes.analyses.interpretation_provider.interpret_truss_sketch", return_value=FakeProposal()) as interpret:
            response = self.upload()
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        analysis_id = data["analysis_id"]
        self.assertEqual(data["status"], "pending_review")
        self.assertEqual(data["review_status"], "pending_review")
        self.assertEqual(data["provider"], "meta")
        self.assertEqual(data["model_id"], "muse-spark-1.3")
        self.assertTrue(data["interpretation_proposal"]["proposal_only"])
        self.assertEqual(data["human_review"]["geometry"], None)
        self.assertEqual(data["validation"]["status"], "not_performed")
        self.assertNotIn("image_storage_name", data)
        self.assertNotIn("uploads", json.dumps(data))
        self.assertNotIn("MODEL_API_KEY", json.dumps(data))
        interpret.assert_called_once()

        detail = self.client.get(f"/api/analyses/{analysis_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["sketch"]["image_width"], 96)
        self.assertIsNotNone(detail.get_json()["perception"])

        listed = self.client.get("/api/analyses?page=1&per_page=5")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.get_json()["total"], 1)
        self.assertEqual(listed.get_json()["items"][0]["analysis_id"], analysis_id)

        image_response = self.client.get(f"/api/analyses/{analysis_id}/image")
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.mimetype, "image/png")
        self.assertEqual(image_response.data, image_bytes())
        self.assertIn("no-store", image_response.headers["Cache-Control"])
        image_response.close()

    def test_provider_failure_is_saved_without_provider_details(self):
        with patch(
            "app.routes.analyses.interpretation_provider.interpret_truss_sketch",
            side_effect=MuseAPIError(),
        ):
            response = self.upload()
        self.assertEqual(response.status_code, 502)
        body = response.get_json()
        self.assertEqual(body["error_code"], "MUSE_API_ERROR")
        self.assertNotIn("API_KEY", json.dumps(body))
        detail = self.client.get(f"/api/analyses/{body['analysis_id']}").get_json()
        self.assertEqual(detail["status"], "failed")
        self.assertEqual(detail["error_code"], "MUSE_API_ERROR")
        self.assertIsNotNone(detail["perception"])
        original = self.client.get(f"/api/analyses/{body['analysis_id']}/image")
        self.assertEqual(original.mimetype, "image/png")
        self.assertEqual(original.data, image_bytes())
        original.close()

    def test_invalid_missing_and_oversized_uploads_are_recorded(self):
        invalid = self.upload(content=b"not an image")
        self.assertEqual(invalid.status_code, 415)
        self.assertEqual(
            self.client.get(f"/api/analyses/{invalid.get_json()['analysis_id']}").get_json()["status"],
            "failed",
        )

        oversized = self.upload(content=b"x" * 4097)
        self.assertEqual(oversized.status_code, 413)
        self.assertEqual(oversized.get_json()["error_code"], "IMAGE_TOO_LARGE")

        missing = self.client.post("/api/analyses", data={}, content_type="multipart/form-data")
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.get_json()["error_code"], "MISSING_IMAGE")

    def test_declared_mime_and_filename_do_not_override_detected_image_format(self):
        for image_format, actual_mime, mismatched_mime, misleading_name in (
            (".png", "image/png", "image/jpeg", "sketch.jpg"),
            (".jpg", "image/jpeg", "image/png", "sketch.png"),
            (".webp", "image/webp", "application/octet-stream", "sketch.jpg"),
        ):
            with self.subTest(image_format=image_format), patch(
                "app.routes.analyses.interpretation_provider.interpret_truss_sketch",
                return_value=FakeProposal(),
            ) as interpret:
                content = image_bytes(image_format=image_format)
                response = self.upload(content=content, filename=misleading_name, mime=mismatched_mime)
            self.assertEqual(response.status_code, 201)
            item = response.get_json()
            self.assertEqual(item["mime_type"], actual_mime)
            interpret.assert_called_once()
            self.assertEqual(interpret.call_args.kwargs["mime_type"], actual_mime)
            self.assertEqual(interpret.call_args.args[0], content)
            restored = self.client.get(f"/api/analyses/{item['analysis_id']}/image")
            self.assertEqual(restored.mimetype, actual_mime)
            self.assertEqual(restored.data, content)
            restored.close()

        self.assertEqual(self.client.get("/api/analyses/not-a-real-id").status_code, 404)
        self.assertEqual(self.client.get("/api/analyses/not-a-real-id/image").status_code, 404)
        self.assertEqual(self.client.get("/api/analyses?page=zero").status_code, 400)

    def test_corrupt_supported_signature_is_rejected_before_storage_or_provider_call(self):
        with patch("app.routes.analyses.interpretation_provider.interpret_truss_sketch") as interpret:
            response = self.upload(content=b"\x89PNG\r\n\x1a\nbroken", mime="image/png")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error_code"], "INVALID_IMAGE")
        interpret.assert_not_called()
        record = self.client.get(f"/api/analyses/{response.get_json()['analysis_id']}").get_json()
        self.assertEqual(record["status"], "failed")
        self.assertIsNone(record["sketch"]["image_url"])

    def test_valid_but_unsupported_image_format_is_rejected(self):
        response = self.upload(content=image_bytes(width=16, height=16, image_format=".bmp"), filename="drawing.bmp", mime="image/bmp")
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.get_json()["error_code"], "UNSUPPORTED_IMAGE_TYPE")

    def test_database_failure_returns_sanitized_service_error(self):
        with patch("app.routes.analyses.begin_analysis", side_effect=AnalysisPersistenceError("private DB details")):
            response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.get_data(as_text=True))

        with self.app.app_context(), patch(
            "app.services.analysis_persistence.db.session.commit",
            side_effect=SQLAlchemyError("private DB details"),
        ):
            with self.assertRaises(AnalysisPersistenceError):
                begin_analysis("sketch")

    def test_unexpected_provider_error_does_not_echo_credential_text(self):
        private_marker = "test-api-key-must-not-appear"
        with patch(
            "app.routes.analyses.interpretation_provider.interpret_truss_sketch",
            side_effect=RuntimeError(f"MODEL_API_KEY={private_marker}"),
        ):
            response = self.upload()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(private_marker, response.get_data(as_text=True))
        detail = self.client.get(f"/api/analyses/{response.get_json()['analysis_id']}").get_json()
        self.assertNotIn(private_marker, json.dumps(detail))

    def test_no_uploaded_file_path_is_returned_or_deleted(self):
        with patch("app.routes.analyses.interpretation_provider.interpret_truss_sketch", return_value=FakeProposal()):
            body = self.upload().get_json()
        with self.app.app_context():
            record = db.session.get(SketchAnalysis, body["analysis_id"])
            stored_name = record.image_storage_name
            self.assertNotIn("/", stored_name)
            self.assertTrue((Path(self.tempdir.name) / stored_name).exists())

    def test_draft_save_preserves_original_proposal_and_rejects_invalid_geometry(self):
        created = self.create_reviewable_analysis()
        analysis_id = created["analysis_id"]
        original = created["interpretation_proposal"]

        invalid = self.valid_human_geometry()
        invalid["model"]["nodes"][0]["x"] = float("nan")
        rejected = self.client.put(f"/api/analyses/{analysis_id}/draft", json={"geometry": invalid, "coordinates_confirmed": True})
        self.assertEqual(rejected.status_code, 422)
        self.assertEqual(rejected.get_json()["error_code"], "VALIDATION_FAILED")
        self.assertIn("NON_FINITE_NUMBER", {issue["code"] for issue in rejected.get_json()["validation_issues"]})

        payload = self.valid_human_geometry()
        saved = self.client.put(f"/api/analyses/{analysis_id}/draft", json={"geometry": payload, "coordinates_confirmed": True})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.get_json()["review_status"], "draft")
        detail = self.client.get(f"/api/analyses/{analysis_id}").get_json()
        self.assertEqual(detail["interpretation_proposal"], original)
        self.assertEqual(detail["human_review"]["geometry"], payload)
        self.assertEqual(self.client.get(f"/api/analyses/{analysis_id}/draft").get_json()["draft"], payload)

    def test_draft_requires_explicit_coordinate_confirmation(self):
        created = self.create_reviewable_analysis()
        response = self.client.put(
            f"/api/analyses/{created['analysis_id']}/draft",
            json={"geometry": self.valid_human_geometry(), "coordinates_confirmed": False},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error_code"], "COORDINATES_NOT_CONFIRMED")
        detail = self.client.get(f"/api/analyses/{created['analysis_id']}").get_json()
        self.assertIsNone(detail["human_review"]["geometry"])

    def test_only_saved_valid_reviewed_draft_can_reach_solver_and_results_stay_associated(self):
        created = self.create_reviewable_analysis()
        analysis_id = created["analysis_id"]
        self.assertEqual(self.client.post(f"/api/analyses/{analysis_id}/review").status_code, 409)
        self.assertEqual(self.client.post(f"/api/analyses/{analysis_id}/solve").status_code, 409)

        geometry = self.valid_human_geometry()
        saved = self.client.put(f"/api/analyses/{analysis_id}/draft", json={"geometry": geometry, "coordinates_confirmed": True})
        self.assertEqual(saved.status_code, 200)
        reviewed = self.client.post(f"/api/analyses/{analysis_id}/review")
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(reviewed.get_json()["review_status"], "reviewed")

        solved = self.client.post(f"/api/analyses/{analysis_id}/solve")
        self.assertEqual(solved.status_code, 200)
        self.assertEqual(solved.get_json()["status"], "SOLVED")
        detail = self.client.get(f"/api/analyses/{analysis_id}").get_json()
        self.assertEqual(detail["review_status"], "submitted")
        self.assertEqual(detail["human_review"]["geometry"], geometry)
        self.assertEqual(detail["interpretation_proposal"], created["interpretation_proposal"])
        self.assertIn("M1", detail["solver_results"]["member_forces"])

        edit_after_submit = self.client.put(f"/api/analyses/{analysis_id}/draft", json={"geometry": geometry, "coordinates_confirmed": True})
        self.assertEqual(edit_after_submit.status_code, 409)

    def test_solver_failure_is_persisted_without_approving_or_discarding_draft(self):
        created = self.create_reviewable_analysis()
        analysis_id = created["analysis_id"]
        geometry = self.valid_human_geometry()
        geometry["model"]["supports"] = geometry["model"]["supports"][:1]
        self.assertEqual(self.client.put(f"/api/analyses/{analysis_id}/draft", json={"geometry": geometry, "coordinates_confirmed": True}).status_code, 200)
        self.assertEqual(self.client.post(f"/api/analyses/{analysis_id}/review").status_code, 200)
        failed = self.client.post(f"/api/analyses/{analysis_id}/solve")
        self.assertEqual(failed.status_code, 422)
        detail = self.client.get(f"/api/analyses/{analysis_id}").get_json()
        self.assertEqual(detail["status"], "failed")
        self.assertEqual(detail["review_status"], "reviewed")
        self.assertEqual(detail["human_review"]["geometry"], geometry)
        self.assertIsNotNone(detail["diagnostics"])
        self.assertIsNone(detail["solver_results"])


if __name__ == "__main__":
    unittest.main()

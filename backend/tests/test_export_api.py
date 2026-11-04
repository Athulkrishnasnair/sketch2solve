"""Tests for export endpoints and draft reopen behavior."""

from io import BytesIO
import json
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from app import create_app
from app.extensions import db
from app.models.analysis import SketchAnalysis


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
            "joints": [
                {"id": "J1", "x": 0, "y": 0},
                {"id": "J2", "x": 40, "y": 0},
                {"id": "J3", "x": 20, "y": 30},
            ],
            "members": [
                {"id": "M1", "joint_i": "J1", "joint_j": "J2"},
                {"id": "M2", "joint_i": "J1", "joint_j": "J3"},
                {"id": "M3", "joint_i": "J2", "joint_j": "J3"},
            ],
            "supports": [
                {"id": "S1", "joint": "J1", "type": "pin"},
                {"id": "S2", "joint": "J2", "type": "roller"},
            ],
            "loads": [
                {"id": "L1", "joint": "J3", "magnitude": 10.0},
            ],
            "ambiguities": [],
            "missing_information": [],
            "proposal_only": True,
        }


def valid_triangle_geometry():
    return {
        "schema_version": "1.0",
        "metadata": {
            "name": "Triangular Truss",
            "source": "human_review",
            "units": {"length": "m", "force": "kN"},
        },
        "model": {
            "nodes": [
                {"id": "J1", "x": 0.0, "y": 0.0},
                {"id": "J2", "x": 4.0, "y": 0.0},
                {"id": "J3", "x": 2.0, "y": 3.0},
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
            "loads": [
                {"id": "L1", "node": "J3", "fx": 0.0, "fy": -10.0},
            ],
        },
    }


class ExportApiTests(unittest.TestCase):
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

    def create_and_submit_analysis(self, solve=True):
        with patch("app.routes.analyses.interpretation_provider.interpret_truss_sketch", return_value=FakeProposal()):
            res = self.client.post(
                "/api/analyses",
                data={
                    "provider": "meta",
                    "image": (BytesIO(image_bytes()), "drawing.png", "image/png"),
                },
                content_type="multipart/form-data",
            )
            analysis_id = res.get_json()["analysis_id"]

        # Save draft
        self.client.put(
            f"/api/analyses/{analysis_id}/draft",
            data=json.dumps({
                "geometry": valid_triangle_geometry(),
                "coordinates_confirmed": True,
            }),
            content_type="application/json",
        )

        # Mark reviewed
        self.client.post(f"/api/analyses/{analysis_id}/review")

        if solve:
            # Solve
            self.client.post(f"/api/analyses/{analysis_id}/solve")

        return analysis_id

    def test_export_json_solved(self):
        analysis_id = self.create_and_submit_analysis(solve=True)
        res = self.client.get(f"/api/analyses/{analysis_id}/export/json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "application/json")
        self.assertIn("attachment; filename=", res.headers.get("Content-Disposition", ""))

        data = res.get_json()
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["metadata"]["analysis_id"], analysis_id)
        self.assertEqual(data["metadata"]["units"]["length"], "m")
        self.assertEqual(data["metadata"]["units"]["force"], "kN")
        self.assertIn("nodes", data["model"])
        self.assertEqual(len(data["model"]["nodes"]), 3)
        self.assertIn("solver_results", data)
        self.assertIn("member_forces", data["solver_results"])
        self.assertIn("M1", data["solver_results"]["member_forces"])

    def test_export_json_unsolved_draft(self):
        analysis_id = self.create_and_submit_analysis(solve=False)
        res = self.client.get(f"/api/analyses/{analysis_id}/export/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["schema_version"], "1.0")
        self.assertNotIn("solver_results", data)

    def test_export_csv_solved(self):
        analysis_id = self.create_and_submit_analysis(solve=True)
        res = self.client.get(f"/api/analyses/{analysis_id}/export/csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.content_type)
        self.assertIn("attachment; filename=", res.headers.get("Content-Disposition", ""))

        content = res.data.decode("utf-8")
        self.assertIn("# Sketch2Solve Structural Analysis Export", content)
        self.assertIn("[MEMBER AXIAL FORCES]", content)
        self.assertIn("Member ID,Joint I,Joint J,Length (m),Axial Force (kN),State,Classification", content)
        self.assertIn("[SUPPORT REACTIONS]", content)
        self.assertIn("Support ID,Joint ID,Support Type,Axis,Reaction Force (kN)", content)
        self.assertIn("M1", content)
        self.assertIn("M2", content)
        self.assertIn("M3", content)

    def test_export_csv_unsolved_returns_409(self):
        analysis_id = self.create_and_submit_analysis(solve=False)
        res = self.client.get(f"/api/analyses/{analysis_id}/export/csv")
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertEqual(data["error_code"], "RESULTS_REQUIRED")
        self.assertIn("Fresh successful solver results are required", data["message"])

    def test_export_png_solved_and_unsolved(self):
        analysis_id = self.create_and_submit_analysis(solve=True)
        res = self.client.get(f"/api/analyses/{analysis_id}/export/png")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "image/png")
        self.assertTrue(res.data.startswith(b"\x89PNG\r\n\x1a\n"))

        # Also test on draft / unsolved
        analysis_id_unsolved = self.create_and_submit_analysis(solve=False)
        res_unsolved = self.client.get(f"/api/analyses/{analysis_id_unsolved}/export/png")
        self.assertEqual(res_unsolved.status_code, 200)
        self.assertEqual(res_unsolved.content_type, "image/png")
        self.assertTrue(res_unsolved.data.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_export_query_param_format(self):
        analysis_id = self.create_and_submit_analysis(solve=True)
        res = self.client.get(f"/api/analyses/{analysis_id}/export?format=json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "application/json")

    def test_export_invalid_format_returns_400(self):
        analysis_id = self.create_and_submit_analysis(solve=True)
        res = self.client.get(f"/api/analyses/{analysis_id}/export/pdf")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data["error_code"], "INVALID_EXPORT_FORMAT")

    def test_reopen_submitted_analysis_as_draft(self):
        analysis_id = self.create_and_submit_analysis(solve=True)

        # Modifying a submitted analysis without reopen=true returns 409
        modified_geom = valid_triangle_geometry()
        modified_geom["model"]["nodes"][1]["x"] = 5.0
        res_fail = self.client.put(
            f"/api/analyses/{analysis_id}/draft",
            data=json.dumps({
                "geometry": modified_geom,
                "coordinates_confirmed": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(res_fail.status_code, 409)

        # Modifying with ?reopen=true succeeds and resets review_status to draft
        res_ok = self.client.put(
            f"/api/analyses/{analysis_id}/draft?reopen=true",
            data=json.dumps({
                "geometry": modified_geom,
                "coordinates_confirmed": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(res_ok.status_code, 200)
        draft_body = res_ok.get_json()
        self.assertEqual(draft_body["review_status"], "draft")
        self.assertEqual(draft_body["draft"]["model"]["nodes"][1]["x"], 5.0)

        # Since model was modified, results are stale; CSV export should now require fresh solve
        res_csv = self.client.get(f"/api/analyses/{analysis_id}/export/csv")
        self.assertEqual(res_csv.status_code, 409)


if __name__ == "__main__":
    unittest.main()

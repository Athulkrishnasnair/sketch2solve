"""Unit and API tests for non-persistent truss preview evaluation."""

from __future__ import annotations

import unittest

from app import create_app
from app.services.truss_preview import evaluate_truss_preview


class TrussPreviewTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        self.client = self.app.test_client()

    def valid_triangle_data(self):
        return {
            "schema_version": "1.0",
            "metadata": {"name": "Test Triangle", "units": {"length": "m", "force": "kN"}},
            "model": {
                "nodes": [
                    {"id": "J1", "x": 0.0, "y": 0.0},
                    {"id": "J2", "x": 4.0, "y": 0.0},
                    {"id": "J3", "x": 2.0, "y": 3.0},
                ],
                "members": [
                    {"id": "M1", "node_i": "J1", "node_j": "J2"},
                    {"id": "M2", "node_i": "J2", "node_j": "J3"},
                    {"id": "M3", "node_i": "J1", "node_j": "J3"},
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

    def test_valid_triangle_solves_successfully(self):
        data = self.valid_triangle_data()
        result = evaluate_truss_preview(data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["validation"]["status"], "valid")
        self.assertEqual(result["solvability"]["status"], "solvable")
        self.assertEqual(result["solvability"]["category"], "SQUARE_FULL_RANK")
        self.assertIsNotNone(result["solver_results"])
        self.assertEqual(result["solver_results"]["status"], "SOLVED")
        self.assertIn("M1", result["solver_results"]["member_forces"])
        self.assertIn("M1", result["solver_results"]["member_states"])
        self.assertIn("S1", result["solver_results"]["support_reactions"])
        self.assertLess(result["solver_results"]["max_equilibrium_residual"], 1e-10)

    def test_incomplete_truss_returns_incomplete_status(self):
        data = {
            "schema_version": "1.0",
            "metadata": {"units": {"length": "m", "force": "kN"}},
            "model": {
                "nodes": [{"id": "J1", "x": 0.0, "y": 0.0}],
                "members": [],
                "supports": [],
                "loads": [],
            },
        }
        result = evaluate_truss_preview(data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["solvability"]["status"], "incomplete")
        self.assertIsNone(result["solver_results"])

    def test_invalid_schema_returns_invalid_geometry(self):
        data = {
            "schema_version": "1.0",
            "metadata": {"units": {"length": "unknown_unit", "force": "kN"}},
            "model": {"nodes": [], "members": [], "supports": [], "loads": []},
        }
        result = evaluate_truss_preview(data)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["solvability"]["status"], "invalid_geometry")
        self.assertTrue(len(result["validation"]["errors"]) > 0)
        self.assertIsNone(result["solver_results"])

    def test_disconnected_joint_generates_warning(self):
        data = self.valid_triangle_data()
        data["model"]["nodes"].append({"id": "J_ISOLATED", "x": 10.0, "y": 10.0})
        result = evaluate_truss_preview(data)
        warning_codes = [w["code"] for w in result["validation"]["warnings"]]
        self.assertIn("DISCONNECTED_JOINT", warning_codes)
        warning = next(w for w in result["validation"]["warnings"] if w["code"] == "DISCONNECTED_JOINT")
        self.assertEqual(warning["element_id"], "J_ISOLATED")

    def test_duplicate_member_generates_warning(self):
        data = self.valid_triangle_data()
        data["model"]["members"].append({"id": "M_DUP", "node_i": "J2", "node_j": "J1"})
        result = evaluate_truss_preview(data)
        warning_codes = [w["code"] for w in result["validation"]["warnings"]]
        self.assertIn("DUPLICATE_MEMBER_CONNECTION", warning_codes)

    def test_unstable_mechanism_reports_unsolvable(self):
        data = self.valid_triangle_data()
        # Remove a support to make it under-constrained
        data["model"]["supports"] = [{"id": "S1", "node": "J1", "type": "pin"}]
        result = evaluate_truss_preview(data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["solvability"]["status"], "unsolvable")
        self.assertIn(result["solvability"]["category"], ["UNDERDETERMINED", "SINGULAR_SQUARE", "OVERDETERMINED"])
        self.assertIsNone(result["solver_results"])

    def test_preview_api_endpoint(self):
        data = self.valid_triangle_data()
        response = self.client.post("/api/analyses/preview", json={"geometry": data})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["is_valid"])
        self.assertEqual(body["solvability"]["status"], "solvable")
        self.assertIsNotNone(body["solver_results"])


if __name__ == "__main__":
    unittest.main()

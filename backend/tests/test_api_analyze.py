"""Flask API tests for the deterministic truss analysis endpoint."""

import math
import tempfile
import unittest

from app import create_app


def triangular_request():
    return {
        "schema_version": "1.0",
        "metadata": {"name": "Triangle", "source": "test", "units": {"length": "m", "force": "kN"}},
        "model": {
            "nodes": [
                {"id": "A", "x": 0, "y": 0},
                {"id": "B", "x": 4, "y": 0},
                {"id": "C", "x": 2, "y": 3},
            ],
            "members": [
                {"id": "AB", "node_i": "A", "node_j": "B"},
                {"id": "AC", "node_i": "A", "node_j": "C"},
                {"id": "BC", "node_i": "B", "node_j": "C"},
            ],
            "supports": [
                {"id": "S_A", "node": "A", "type": "pin"},
                {"id": "S_B", "node": "B", "type": "roller", "direction": "vertical"},
            ],
            "loads": [{"id": "L_C", "node": "C", "fx": 0, "fy": -10}],
        },
    }


class AnalyzeApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.client = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_FOLDER": self.tempdir.name,
        }).test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def post(self, body):
        return self.client.post("/api/analyze", json=body)

    def test_triangle_returns_forces_reactions_diagnostics_and_residuals(self):
        response = self.post(triangular_request())
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["analysis_id"])
        self.assertEqual(data["status"], "SOLVED")
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["units"], {"length": "m", "force": "kN"})
        self.assertAlmostEqual(data["results"]["member_forces"]["AB"], 10 / 3, delta=1e-12)
        expected_diagonal = -10 * math.sqrt(13) / 6
        self.assertAlmostEqual(data["results"]["member_forces"]["AC"], expected_diagonal, delta=1e-12)
        self.assertAlmostEqual(data["results"]["member_forces"]["BC"], expected_diagonal, delta=1e-12)
        self.assertAlmostEqual(data["results"]["support_reactions"]["S_A"]["x"], 0, delta=1e-12)
        self.assertAlmostEqual(data["results"]["support_reactions"]["S_A"]["y"], 5, delta=1e-12)
        self.assertAlmostEqual(data["results"]["support_reactions"]["S_B"]["y"], 5, delta=1e-12)
        diagnostics = data["diagnostics"]
        self.assertEqual(diagnostics["equation_count"], 6)
        self.assertEqual(diagnostics["unknown_count"], 6)
        self.assertEqual(diagnostics["matrix_shape"], [6, 6])
        self.assertEqual(diagnostics["numerical_rank"], 6)
        self.assertEqual(diagnostics["category"], "SQUARE_FULL_RANK")
        self.assertIsNotNone(diagnostics["condition_number"])
        results = data["results"]
        self.assertLessEqual(results["max_equilibrium_residual"], results["residual_tolerance"])
        self.assertEqual(results["force_unit"], "kN")
        history = self.client.get("/api/analyses/" + data["analysis_id"])
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.get_json()["solver_results"]["member_forces"], results["member_forces"])
        self.assertEqual(response.mimetype, "application/json")

    def test_missing_body_and_malformed_json_are_400(self):
        missing = self.client.post("/api/analyze")
        malformed = self.client.post("/api/analyze", data="{", content_type="application/json")
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.get_json()["error_code"], "INVALID_JSON")
        self.assertEqual(malformed.status_code, 400)
        self.assertEqual(malformed.get_json()["error_code"], "MALFORMED_JSON")
        self.assertTrue(missing.get_json()["analysis_id"])
        self.assertTrue(malformed.get_json()["analysis_id"])

    def test_validation_errors_are_structured(self):
        cases = []
        bad_version = triangular_request()
        bad_version["schema_version"] = "2.0"
        cases.append((bad_version, "UNSUPPORTED_SCHEMA_VERSION"))
        missing_fields = triangular_request()
        del missing_fields["model"]["members"]
        cases.append((missing_fields, "MISSING_FIELD"))
        bad_reference = triangular_request()
        bad_reference["model"]["members"][0]["node_j"] = "missing"
        cases.append((bad_reference, "UNKNOWN_NODE_REFERENCE"))
        zero_length = triangular_request()
        zero_length["model"]["nodes"][1]["x"] = 0
        zero_length["model"]["nodes"][1]["y"] = 0
        cases.append((zero_length, "ZERO_LENGTH_MEMBER"))
        for body, issue_code in cases:
            with self.subTest(issue_code=issue_code):
                response = self.post(body)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.get_json()["error_code"], "VALIDATION_FAILED")
                self.assertIn(issue_code, [issue["code"] for issue in response.get_json()["validation_issues"]])
                self.assertNotIn("results", response.get_json())

    def test_rank_deficient_and_nonsquare_fail_without_partial_results(self):
        rank_deficient = triangular_request()
        rank_deficient["model"]["members"][2] = {
            "id": "BC", "node_i": "A", "node_j": "C"
        }
        # Two coincident member directions make the square equilibrium matrix singular.
        rank_response = self.post(rank_deficient)
        self.assertEqual(rank_response.status_code, 422)
        rank_data = rank_response.get_json()
        self.assertEqual(rank_data["error_code"], "RANK_DEFICIENT_SYSTEM")
        self.assertEqual(rank_data["diagnostics"]["category"], "SINGULAR_SQUARE")
        self.assertNotIn("results", rank_data)

        nonsquare = triangular_request()
        nonsquare["model"]["supports"].pop()
        nonsquare_response = self.post(nonsquare)
        self.assertEqual(nonsquare_response.status_code, 422)
        nonsquare_data = nonsquare_response.get_json()
        self.assertEqual(nonsquare_data["error_code"], "NONSQUARE_SYSTEM")
        self.assertEqual(nonsquare_data["diagnostics"]["category"], "OVERDETERMINED")
        self.assertNotIn("results", nonsquare_data)

    def test_health_endpoint_is_preserved(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()

"""Unit and integration tests for AI-powered Issue Resolution Assistant."""

import copy
import unittest
from unittest.mock import MagicMock

from app import create_app
from app.services.ai_assistant import (
    resolve_geometry_issue,
    _test_apply_modifications,
)


def _sample_triangle_geometry():
    return {
        "schema_version": "1.0",
        "metadata": {"units": {"length": "m", "force": "kN"}},
        "model": {
            "nodes": [
                {"id": "N1", "x": 0.0, "y": 0.0},
                {"id": "N2", "x": 4.0, "y": 0.0},
                {"id": "N3", "x": 2.0, "y": 3.0},
            ],
            "members": [
                {"id": "M1", "node_i": "N1", "node_j": "N2"},
                {"id": "M2", "node_i": "N2", "node_j": "N3"},
                {"id": "M3", "node_i": "N3", "node_j": "N1"},
            ],
            "supports": [
                {"id": "S1", "node": "N1", "type": "pin"},
            ],
            "loads": [
                {"id": "L1", "node": "N3", "fx": 0.0, "fy": -10.0},
            ],
        },
    }


class TestAIIssueResolutionAssistant(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        self.client = self.app.test_client()

    def test_insufficient_supports_resolution_heuristic(self):
        """When supports < 3, assistant provides valid support addition fix."""
        geom = _sample_triangle_geometry()
        original_geom = copy.deepcopy(geom)
        issue = {
            "code": "INSUFFICIENT_SUPPORTS",
            "message": "The structure has 2 support constraints (at least 3 required).",
            "element_id": "S1",
        }
        diagnostics = {
            "category": "UNDERDETERMINED",
            "equation_count": 6,
            "unknown_count": 5,
            "rank": 5,
        }

        result = resolve_geometry_issue(geom, issue, diagnostics)
        self.assertEqual(result["status"], "success")
        self.assertIn("root_cause_explanation", result)
        self.assertIn("engineering_rationale", result)
        self.assertGreater(len(result["proposed_fixes"]), 0)

        # Ensure original geometry was not mutated
        self.assertEqual(geom, original_geom)

        # Check fix validity and solvability prediction
        fix = result["proposed_fixes"][0]
        self.assertTrue(fix["is_valid"])
        self.assertEqual(fix["predicted_status"], "solvable")
        self.assertEqual(fix["predicted_category"], "SQUARE_FULL_RANK")

    def test_disconnected_joint_resolution(self):
        """Disconnected joint resolution proposes connecting or deleting it."""
        geom = _sample_triangle_geometry()
        geom["model"]["nodes"].append({"id": "N4", "x": 5.0, "y": 5.0})  # disconnected
        original_geom = copy.deepcopy(geom)

        issue = {
            "code": "DISCONNECTED_JOINT",
            "element_id": "N4",
            "message": "Joint N4 has no connected members.",
        }

        result = resolve_geometry_issue(geom, issue)
        self.assertEqual(result["status"], "success")
        self.assertEqual(geom, original_geom)

        fix_titles = [f["title"] for f in result["proposed_fixes"]]
        # Should offer both connection and deletion
        self.assertTrue(any("Connect Joint N4" in t for t in fix_titles))
        self.assertTrue(any("Delete" in t for t in fix_titles))

        # Check that applying deletion leaves model valid
        del_fix = next(f for f in result["proposed_fixes"] if "Delete" in f["title"])
        self.assertTrue(del_fix["is_valid"])

    def test_zero_length_member_resolution(self):
        """Zero length member produces removal suggestion."""
        geom = _sample_triangle_geometry()
        geom["model"]["members"].append({"id": "M_zero", "node_i": "N1", "node_j": "N1"})
        issue = {
            "code": "ZERO_LENGTH_MEMBER",
            "element_id": "M_zero",
            "message": "Member M_zero connects identical node N1 to itself.",
        }

        result = resolve_geometry_issue(geom, issue)
        self.assertEqual(result["status"], "success")
        fixes = result["proposed_fixes"]
        self.assertGreater(len(fixes), 0)
        self.assertIn("M_zero", fixes[0]["modifications"]["members_to_remove"])
        self.assertTrue(fixes[0]["is_valid"])

    def test_invalid_ai_suggestions_are_caught_by_safety_gate(self):
        """If AI proposes an invalid fix (e.g. unknown node reference), it is marked invalid."""
        geom = _sample_triangle_geometry()
        # Test applying modifications with non-existent node reference
        bad_mods = {
            "members_to_add": [{"id": "M_bad", "node_i": "N1", "node_j": "NON_EXISTENT_NODE"}],
            "members_to_remove": [],
            "nodes_to_add": [],
            "nodes_to_remove": [],
            "supports_to_add": [],
            "supports_to_remove": [],
            "loads_to_add": [],
            "loads_to_remove": [],
        }
        is_valid, errors, _ = _test_apply_modifications(geom, bad_mods)
        self.assertFalse(is_valid)
        self.assertTrue(any("unknown node" in err.lower() for err in errors))

    def test_mock_ai_provider_call_and_timeout_fallback(self):
        """Mock provider call works, and timeout falls back cleanly to heuristics."""
        geom = _sample_triangle_geometry()
        issue = {"code": "INSUFFICIENT_SUPPORTS", "message": "Only 2 reactions"}

        # 1. Successful provider response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            '{"root_cause_explanation": "AI says missing constraint.", '
            '"engineering_rationale": "Planar equilibrium requires 3 reactions.", '
            '"proposed_fixes": [{"id": "fix_ai", "title": "Add roller at N2", "description": "Fixes it.", '
            '"affected_elements": {"nodes": ["N2"], "members": [], "supports": ["S_ai"], "loads": []}, '
            '"modifications": {"supports_to_add": [{"id": "S_ai", "node": "N2", "type": "roller", "direction": "vertical"}]}}]}'
        )
        mock_client.models.generate_content.return_value = mock_response

        res = resolve_geometry_issue(geom, issue, provider="gemini", client=mock_client)
        self.assertEqual(res["root_cause_explanation"], "AI says missing constraint.")
        self.assertEqual(len(res["proposed_fixes"]), 1)
        self.assertTrue(res["proposed_fixes"][0]["is_valid"])

        # 2. Timeout / Error fallback
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out")
        fallback_res = resolve_geometry_issue(geom, issue, provider="gemini", client=mock_client)
        self.assertEqual(fallback_res["status"], "success")
        self.assertIn("support", fallback_res["root_cause_explanation"].lower())
        self.assertGreater(len(fallback_res["proposed_fixes"]), 0)

    def test_api_endpoint_post_ai_assistant(self):
        """Test POST /api/ai/assistant HTTP endpoint."""
        geom = _sample_triangle_geometry()
        payload = {
            "geometry": geom,
            "issue": {
                "code": "INSUFFICIENT_SUPPORTS",
                "message": "Only 2 reactions.",
                "element_id": "S1",
            },
            "diagnostics": {"category": "UNDERDETERMINED"},
        }
        resp = self.client.post("/api/ai/assistant", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("root_cause_explanation", data)
        self.assertIn("proposed_fixes", data)

    def test_api_endpoint_validation_errors(self):
        """Test POST /api/ai/assistant with bad request bodies."""
        # Non-JSON
        resp = self.client.post("/api/ai/assistant", data="plain text")
        self.assertEqual(resp.status_code, 400)

        # Missing issue
        resp = self.client.post("/api/ai/assistant", json={"geometry": {}})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()

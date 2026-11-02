"""Deterministic geometry checks for the evaluation-only failure diagnostic."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "evaluation/diagnose_target_member_failures.py"
SPEC = importlib.util.spec_from_file_location("target_member_failure_diagnostic", SCRIPT)
DIAGNOSTIC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAGNOSTIC)


class TargetMemberDiagnosticTests(unittest.TestCase):
    def test_collinear_partial_segment_reports_angle_offset_and_overlap(self):
        result = DIAGNOSTIC.segment_metrics([0, 0], [0, 100], [2, 25], [2, 75])
        self.assertAlmostEqual(result["angle_mismatch_deg"], 0)
        self.assertAlmostEqual(result["centerline_offset_px"], 2)
        self.assertAlmostEqual(result["overlap_px"], 50)
        self.assertAlmostEqual(result["coverage_fraction"], 0.5)

    def test_fragment_union_reports_gap_without_bridging(self):
        merged, covered = DIAGNOSTIC._union([[0, 20], [25, 40], [50, 60]])
        self.assertEqual(merged, [[0, 20], [25, 40], [50, 60]])
        self.assertEqual(covered, 45)

    def test_outside_member_extent_has_no_positive_coverage(self):
        result = DIAGNOSTIC.segment_metrics([0, 0], [0, 100], [3, 105], [3, 120])
        self.assertEqual(result["overlap_px"], 0)
        self.assertIsNone(result["projection_interval_px"])


if __name__ == "__main__":
    unittest.main()

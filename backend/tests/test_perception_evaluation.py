"""Tests for the offline, human-reference perception evaluator."""

import importlib.util
from pathlib import Path
import unittest


EVALUATOR_PATH = Path(__file__).resolve().parents[2] / 'evaluation' / 'perception_evaluation.py'
SPEC = importlib.util.spec_from_file_location('perception_evaluation', EVALUATOR_PATH)
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def reference_annotation():
    return {
        'annotation_schema_version': '1.0',
        'image': {'filename': 'synthetic.png', 'sha256': 'fixture-hash', 'width': 200, 'height': 100},
        'coordinate_system': {
            'space': 'original_image_pixels', 'origin': 'top_left', 'x_axis': 'right', 'y_axis': 'down',
        },
        'assessment': {'status': 'confirmed', 'notes': 'independent synthetic fixture'},
        'evaluation_roi': [0, 0, 200, 100],
        'joints': [
            {'id': 'A', 'x': 20, 'y': 50, 'status': 'confirmed', 'reason': 'synthetic point'},
            {'id': 'B', 'x': 120, 'y': 50, 'status': 'confirmed', 'reason': 'synthetic point'},
        ],
        'members': [
            {'id': 'M1', 'node_i': 'A', 'node_j': 'B', 'status': 'confirmed', 'reason': 'synthetic segment'},
        ],
    }


def baseline_image():
    return {
        'image_width': 200,
        'image_height': 100,
        'joints': [
            {'point': [21, 50]},
            {'point': [22, 50]},
            {'point': [119, 50]},
        ],
        'lines': [
            {'start': [20, 50], 'end': [65, 50]},
            {'start': [66, 50], 'end': [120, 50]},
            {'start': [10, 80], 'end': [190, 80]},
        ],
    }


class PerceptionEvaluationTests(unittest.TestCase):
    def test_schema_accepts_confirmed_and_reasoned_ambiguous_annotations(self):
        annotation = reference_annotation()
        annotation['ambiguous_regions'] = [{'status': 'ambiguous', 'reason': 'crossing connection unclear'}]
        self.assertTrue(EVALUATOR.validate_annotation(annotation))

    def test_schema_rejects_missing_ambiguity_reason_and_invalid_member_reference(self):
        annotation = reference_annotation()
        annotation['joints'].append({'id': 'C', 'x': 10, 'y': 10, 'status': 'ambiguous'})
        with self.assertRaisesRegex(ValueError, 'require a reason'):
            EVALUATOR.validate_annotation(annotation)
        annotation = reference_annotation()
        annotation['members'][0]['node_j'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'reference annotated joints'):
            EVALUATOR.validate_annotation(annotation)

    def test_joint_matching_is_one_to_one_and_member_fragments_union_coverage(self):
        result = EVALUATOR.evaluate_image(baseline_image(), reference_annotation())
        self.assertEqual(result['matched_joints'], 2)
        self.assertAlmostEqual(result['joint_precision'], 2 / 3)
        self.assertEqual(result['joint_recall'], 1.0)
        self.assertEqual(result['members_with_at_least_80_percent_candidate_line_coverage'], 1)
        self.assertEqual(result['member_coverage_recall'], 1.0)
        self.assertIsNone(result['member_precision'])
        self.assertEqual(result['matched_joint_endpoint_error_px_mean'], 1.0)

    def test_ambiguous_image_has_unavailable_metrics(self):
        annotation = reference_annotation()
        annotation['assessment']['status'] = 'ambiguous'
        annotation['evaluation_roi'] = None
        annotation['joints'] = []
        annotation['members'] = []
        result = EVALUATOR.evaluate_image(baseline_image(), annotation)
        self.assertEqual(result['metrics_status'], 'unavailable')
        self.assertIsNone(result['joint_precision'])
        self.assertIsNone(result['member_coverage_recall'])

    def test_aggregate_uses_micro_counts_from_only_annotated_images(self):
        available = EVALUATOR.evaluate_image(baseline_image(), reference_annotation())
        ambiguous = reference_annotation()
        ambiguous['assessment']['status'] = 'ambiguous'
        ambiguous['evaluation_roi'] = None
        ambiguous['joints'] = []
        ambiguous['members'] = []
        ambiguous['image']['filename'] = 'ambiguous.png'
        unavailable = EVALUATOR.evaluate_image(baseline_image(), ambiguous)
        result = EVALUATOR.aggregate_results([available, unavailable])
        self.assertAlmostEqual(result['joint_precision'], 2 / 3)
        self.assertEqual(result['joint_recall'], 1.0)
        self.assertEqual(result['included_images'], ['synthetic.png'])
        self.assertEqual(result['excluded_images'], ['ambiguous.png'])


if __name__ == '__main__':
    unittest.main()

"""Tests for isolated ROI crop validation and coordinate mapping."""

import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / 'evaluation' / 'run_roi_crop_experiment.py'
SPEC = importlib.util.spec_from_file_location('run_roi_crop_experiment', SCRIPT_PATH)
EXPERIMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT)


class PerceptionRoiExperimentTests(unittest.TestCase):
    def test_config_rectangles_are_valid_and_match_original_source_bounds(self):
        config_path = SCRIPT_PATH.parents[1] / 'evaluation/results/phase-a-2026-10-30/roi-crop-experiment/roi_config.json'
        config = json.loads(config_path.read_text())
        self.assertEqual(EXPERIMENT.crop_bounds(576, 749, config['images']['test2.jpg']['roi']), (60, 565, 515, 749))
        self.assertEqual(EXPERIMENT.crop_bounds(2046, 1319, config['images']['test5.png']['roi']), (365, 630, 1745, 1050))
        self.assertEqual(len(config['test5_ambiguous_crossings_original_pixels']), 3)
        self.assertTrue(all(crossing['status'] == 'ambiguous' for crossing in config['test5_ambiguous_crossings_original_pixels']))

    def test_invalid_rectangle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'in-bounds'):
            EXPERIMENT.crop_bounds(20, 15, {'x': 10, 'y': 2, 'width': 11, 'height': 3})
        with self.assertRaisesRegex(ValueError, 'integers'):
            EXPERIMENT.crop_bounds(20, 15, {'x': 1.5, 'y': 2, 'width': 5, 'height': 3})

    def test_crop_local_lines_and_joints_translate_back_to_original_pixels(self):
        local = {
            'image_width': 30,
            'image_height': 20,
            'coordinate_space': 'image_pixels',
            'lines': [{'start': [1, 2], 'end': [29, 18]}],
            'joints': [{'point': [3.5, 4.5]}],
        }
        mapped = EXPERIMENT.translate_result_to_original(local, 100, 200, 500, 400)
        self.assertEqual(mapped['image_width'], 500)
        self.assertEqual(mapped['image_height'], 400)
        self.assertEqual(mapped['lines'][0], {'start': [101, 202], 'end': [129, 218]})
        self.assertEqual(mapped['joints'][0]['point'], [103.5, 204.5])
        self.assertEqual(local['lines'][0]['start'], [1, 2])


if __name__ == '__main__':
    unittest.main()

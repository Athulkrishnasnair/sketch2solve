"""Regression checks for the fixed rightmost-bay experiment configuration."""

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'evaluation/results/phase-a-2026-10-30/rightmost-bay-targeted-tile-2026-10-30/tile_config.json'
SCRIPT_PATH = ROOT / 'evaluation/run_rightmost_targeted_tile_experiment.py'
SPEC = importlib.util.spec_from_file_location('run_rightmost_targeted_tile_experiment', SCRIPT_PATH)
EXPERIMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT)


class RightmostTargetedTileTests(unittest.TestCase):
    def test_fixed_tile_contains_reference_roi_and_all_target_member_endpoints(self):
        config = json.loads(CONFIG_PATH.read_text())
        roi, tile = config['reference_roi'], config['tile']
        self.assertEqual((roi['x'], roi['y'], roi['width'], roi['height']), (365, 630, 1380, 420))
        self.assertEqual((tile['x'], tile['y'], tile['width'], tile['height']), (1200, 630, 545, 420))
        self.assertEqual(set(config['target_members']), {'M09', 'M10', 'M16'})
        for member in config['target_members'].values():
            for x, y in (member['start'], member['end']):
                self.assertTrue(tile['x'] <= x < tile['right_exclusive'])
                self.assertTrue(tile['y'] <= y < tile['bottom_exclusive'])
        self.assertEqual([point['status'] for point in config['ambiguous_crossings_original_pixels']], ['ambiguous'] * 3)


if __name__ == '__main__':
    unittest.main()

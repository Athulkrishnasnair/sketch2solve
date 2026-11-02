"""Synthetic tests for the isolated overlapping-tile evaluation helper."""

import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / 'evaluation' / 'run_overlapping_tile_experiment.py'
SPEC = importlib.util.spec_from_file_location('run_overlapping_tile_experiment', SCRIPT_PATH)
EXPERIMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT)


def segment(tile, line_id, start, end):
    return {
        'tile_id': tile,
        'line_id': line_id,
        'tile_origin': [0, 0],
        'start': list(start),
        'end': list(end),
    }


class OverlappingTileExperimentTests(unittest.TestCase):
    def test_frozen_tile_origins_cover_exact_roi_without_partial_tiles(self):
        config_path = SCRIPT_PATH.parents[1] / 'evaluation/results/phase-a-2026-10-30/overlapping-tile-experiment-2026-10-30/tile_config.json'
        config = json.loads(config_path.read_text())
        for tile_config in config['configurations'].values():
            EXPERIMENT._validate_tile_config(config['roi'], {'test': tile_config})
        self.assertEqual(config['configurations']['three_wide']['origins_original_pixels'], [[365, 630], [755, 630], [1145, 630]])
        self.assertEqual(config['configurations']['four_narrow']['origins_original_pixels'], [[365, 630], [665, 630], [965, 630], [1265, 630]])
        self.assertEqual([point['status'] for point in config['test5_ambiguous_crossings_original_pixels']], ['ambiguous'] * 3)

    def test_coordinate_mapping_preserves_tile_provenance(self):
        mapped = EXPERIMENT.map_segment_to_original(segment('tile-1', 'L1', (2, 3), (20, 30)), 100, 200)
        self.assertEqual(mapped['start'], [102, 203])
        self.assertEqual(mapped['end'], [120, 230])
        self.assertEqual(mapped['tile_id'], 'tile-1')
        self.assertEqual(mapped['line_id'], 'L1')

    def test_reversed_duplicate_endpoints_merge_and_retain_both_sources(self):
        lines = [
            segment('left', 'L1', (10, 20), (110, 20)),
            segment('right', 'L7', (109, 21), (9, 21)),
        ]
        merged = EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=4)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['source_tile_ids'], ['left', 'right'])
        self.assertEqual(len(merged[0]['source_detections']), 2)
        self.assertLessEqual(merged[0]['start'][0], 10)
        self.assertGreaterEqual(merged[0]['end'][0], 110)

    def test_same_member_in_overlapping_tiles_is_deduplicated(self):
        lines = [
            segment('tile-a', 'L1', (100, 50), (250, 50)),
            segment('tile-b', 'L2', (105, 51), (245, 51)),
        ]
        self.assertEqual(len(EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=4)), 1)

    def test_partially_overlapping_member_fragments_merge_without_a_gap(self):
        lines = [
            segment('tile-a', 'L1', (0, 0), (70, 0)),
            segment('tile-b', 'L2', (50, 1), (100, 1)),
        ]
        merged = EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=4)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['start'], [0, 0])
        self.assertEqual(merged[0]['end'], [100, 0])

    def test_nearby_parallel_members_remain_separate_at_primary_tolerance(self):
        lines = [segment('tile-a', 'L1', (0, 0), (100, 0)), segment('tile-b', 'L2', (0, 12), (100, 12))]
        self.assertEqual(len(EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=4)), 2)

    def test_perpendicular_members_sharing_a_joint_are_not_merged(self):
        lines = [
            segment('tile-a', 'L1', (0, 50), (100, 50)),
            segment('tile-b', 'L2', (100, 50), (100, 150)),
        ]
        self.assertEqual(len(EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=8)), 2)

    def test_disjoint_collinear_fragments_do_not_bridge_their_gap(self):
        lines = [segment('tile-a', 'L1', (0, 0), (40, 0)), segment('tile-b', 'L2', (60, 0), (100, 0))]
        self.assertEqual(len(EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=4)), 2)

    def test_deduplication_is_sensitive_to_the_recorded_distance_tolerance(self):
        lines = [segment('tile-a', 'L1', (0, 0), (100, 0)), segment('tile-b', 'L2', (0, 6), (100, 6))]
        self.assertEqual(len(EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=4)), 2)
        self.assertEqual(len(EXPERIMENT.deduplicate_segments(lines, perpendicular_tolerance_px=8)), 1)


if __name__ == '__main__':
    unittest.main()

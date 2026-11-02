"""Checks the evaluation-only staged parameter grid stays controlled."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "evaluation/run_canny_hough_sweep.py"
SPEC = importlib.util.spec_from_file_location("run_canny_hough_sweep", SCRIPT)
SWEEP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SWEEP)


class PerceptionParameterSweepTests(unittest.TestCase):
    def test_control_matches_production_default(self):
        self.assertEqual(SWEEP.CONTROL, SWEEP.PerceptionConfig())
        self.assertEqual(SWEEP._make_configs()["control"], SWEEP.CONTROL)

    def test_canny_threshold_pairs_are_ordered_and_hough_is_held_fixed(self):
        configs = SWEEP._make_configs()
        base = configs["control"]
        for name in ("canny_low", "canny_high"):
            candidate = configs[name]
            self.assertLess(candidate.canny_min_threshold, candidate.canny_max_threshold)
            self.assertEqual(candidate.hough_threshold, base.hough_threshold)
            self.assertEqual(candidate.min_line_length, base.min_line_length)
            self.assertEqual(candidate.max_line_gap, base.max_line_gap)
        self.assertLess(configs["canny_low"].canny_max_threshold, base.canny_max_threshold)
        self.assertGreater(configs["canny_high"].canny_min_threshold, base.canny_min_threshold)

    def test_hough_variants_change_one_hough_parameter_at_a_time(self):
        for name, changes in SWEEP.HOUGH_SETTINGS.items():
            if name == "control":
                continue
            candidate = SWEEP.replace(SWEEP.CONTROL, **changes)
            actual = SWEEP.asdict(candidate)
            base = SWEEP.asdict(SWEEP.CONTROL)
            differing = {key for key in actual if actual[key] != base[key]}
            self.assertEqual(differing, set(changes))
            self.assertEqual(len(differing), 1)


if __name__ == "__main__":
    unittest.main()

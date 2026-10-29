"""Synthetic image tests for candidate visual geometry extraction."""

import json
import unittest

import cv2
import numpy as np

from app.services.perception import (
    MAX_IMAGE_BYTES,
    PerceptionConfig,
    PerceptionInputError,
    detect_candidate_geometry,
    render_detections,
)


def png_bytes(image):
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise AssertionError("Synthetic PNG encoding failed")
    return encoded.tobytes()


def sketch(lines, *, width=240, height=180, background=238):
    image = np.full((height, width, 3), background, dtype=np.uint8)
    for start, end in lines:
        cv2.line(image, start, end, (35, 45, 55), 2, cv2.LINE_AA)
    return png_bytes(image)


class PerceptionTests(unittest.TestCase):
    def setUp(self):
        self.config = PerceptionConfig(
            hough_threshold=20,
            min_line_length=35,
            max_line_gap=10,
            endpoint_tolerance=14,
        )

    def test_horizontal_vertical_and_inclined_lines_are_detected(self):
        cases = (
            ((25, 50), (210, 50)),
            ((60, 20), (60, 160)),
            ((25, 155), (205, 25)),
        )
        for start, end in cases:
            with self.subTest(start=start, end=end):
                result = detect_candidate_geometry(sketch([(start, end)]), self.config)
                self.assertTrue(result.lines)
                expected_angle = np.degrees(np.arctan2(end[1] - start[1], end[0] - start[0])) % 180
                detected_angles = [np.degrees(np.arctan2(line.end[1] - line.start[1], line.end[0] - line.start[0])) % 180 for line in result.lines]
                angular_distance = lambda angle: min(abs(angle - expected_angle), 180 - abs(angle - expected_angle))
                self.assertLess(min(angular_distance(angle) for angle in detected_angles), 5)
                self.assertTrue(all(line.length_px > 30 for line in result.lines))

    def test_default_thresholds_detect_a_low_contrast_pencil_like_stroke(self):
        image = np.full((200, 320, 3), 190, dtype=np.uint8)
        cv2.line(image, (30, 150), (290, 40), (120, 120, 120), 2, cv2.LINE_AA)
        content = png_bytes(image)
        legacy_settings = PerceptionConfig(canny_sigma=0.33, canny_min_threshold=30, canny_max_threshold=220)
        self.assertEqual(detect_candidate_geometry(content, legacy_settings).lines, ())
        result = detect_candidate_geometry(content)
        self.assertTrue(result.lines)
        expected_angle = np.degrees(np.arctan2(40 - 150, 290 - 30)) % 180
        detected_angles = [np.degrees(np.arctan2(line.end[1] - line.start[1], line.end[0] - line.start[0])) % 180 for line in result.lines]
        self.assertLess(min(abs(angle - expected_angle) for angle in detected_angles), 5)

    def test_triangle_returns_candidates_without_structural_classification(self):
        result = detect_candidate_geometry(
            sketch([((35, 145), (205, 145)), ((35, 145), (120, 35)), ((205, 145), (120, 35))]),
            self.config,
        )
        self.assertGreaterEqual(len(result.lines), 3)
        self.assertTrue(result.joints)
        self.assertTrue(all(joint.evidence == "endpoint_cluster" for joint in result.joints))
        self.assertEqual(result.coordinate_space, "image_pixels")
        self.assertNotIn("members", result.to_dict())

    def test_blank_image_returns_warning_and_no_candidates(self):
        result = detect_candidate_geometry(png_bytes(np.full((100, 140, 3), 220, dtype=np.uint8)), self.config)
        self.assertEqual(result.lines, ())
        self.assertEqual(result.joints, ())
        self.assertTrue(result.warnings)

    def test_invalid_empty_small_and_oversized_inputs_are_rejected(self):
        for content in (b"", b"not an image"):
            with self.subTest(content=content):
                with self.assertRaises(PerceptionInputError):
                    detect_candidate_geometry(content, self.config)
        with self.assertRaises(PerceptionInputError):
            detect_candidate_geometry(png_bytes(np.zeros((7, 20, 3), dtype=np.uint8)), self.config)
        with self.assertRaises(PerceptionInputError):
            detect_candidate_geometry(b"x" * (MAX_IMAGE_BYTES + 1), self.config)
        # Explicit dimension guard; a compressed image above the pixel budget remains small.
        oversized = png_bytes(np.zeros((5000, 5000, 3), dtype=np.uint8))
        with self.assertRaises(PerceptionInputError):
            detect_candidate_geometry(oversized, self.config)

    def test_results_and_ids_are_deterministic_and_json_serializable(self):
        content = sketch([((30, 90), (200, 90)), ((30, 90), (115, 25))], background=205)
        first = detect_candidate_geometry(content, self.config)
        second = detect_candidate_geometry(content, self.config)
        self.assertEqual(first, second)
        self.assertEqual([line.id for line in first.lines], [f"L{i:03d}" for i in range(1, len(first.lines) + 1)])
        self.assertEqual([joint.id for joint in first.joints], [f"J{i:03d}" for i in range(1, len(first.joints) + 1)])
        json.dumps(first.to_dict())

    def test_endpoint_clustering_is_explicit_and_visualization_is_encoded(self):
        content = sketch([((25, 90), (120, 90)), ((125, 93), (210, 93))])
        result = detect_candidate_geometry(content, self.config)
        cluster = next(joint for joint in result.joints if len(joint.line_ids) == 2)
        self.assertEqual(cluster.evidence, "endpoint_cluster")
        annotated = render_detections(content, result)
        annotated_with_ids = render_detections(content, result, show_ids=True)
        self.assertNotEqual(annotated, annotated_with_ids)
        decoded = cv2.imdecode(np.frombuffer(annotated, dtype=np.uint8), cv2.IMREAD_COLOR)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.shape[:2], (result.image_height, result.image_width))

    def test_near_duplicate_hough_detections_are_filtered(self):
        result = detect_candidate_geometry(sketch([((25, 70), (210, 70))]), self.config)
        self.assertLessEqual(len(result.lines), 2)
        self.assertGreaterEqual(len(result.lines), 1)


if __name__ == "__main__":
    unittest.main()

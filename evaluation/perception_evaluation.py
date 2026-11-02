"""Evaluate endpoint-cluster and candidate-line coverage against human references.

This script reports visual-geometry evidence only. It does not classify support,
load, or structural safety semantics.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics

STATUSES = {'confirmed', 'ambiguous', 'unobservable'}


def validate_annotation(annotation):
    """Raise ValueError for malformed or internally inconsistent reference data."""
    if annotation.get('annotation_schema_version') != '1.0':
        raise ValueError('annotation_schema_version must be "1.0"')
    image = annotation.get('image')
    if not isinstance(image, dict) or not image.get('filename') or not image.get('sha256'):
        raise ValueError('image filename and sha256 are required')
    if not isinstance(image.get('width'), int) or not isinstance(image.get('height'), int) or image['width'] <= 0 or image['height'] <= 0:
        raise ValueError('image dimensions must be positive integers')
    coordinates = annotation.get('coordinate_system', {})
    if coordinates != {'space': 'original_image_pixels', 'origin': 'top_left', 'x_axis': 'right', 'y_axis': 'down'}:
        raise ValueError('coordinate_system must declare original raster pixels with top-left origin, x-right, y-down')
    assessment = annotation.get('assessment', {})
    if assessment.get('status') not in STATUSES | {'partial'}:
        raise ValueError('assessment status is not recognized')
    roi = annotation.get('evaluation_roi')
    if roi is not None and (len(roi) != 4 or not (0 <= roi[0] < roi[2] <= image['width'] and 0 <= roi[1] < roi[3] <= image['height'])):
        raise ValueError('evaluation_roi must be an in-bounds [x_min, y_min, x_max, y_max] box')

    nodes = annotation.get('joints')
    members = annotation.get('members')
    if not isinstance(nodes, list) or not isinstance(members, list):
        raise ValueError('joints and members must be arrays')
    node_ids = set()
    for node in nodes:
        if node.get('status') not in STATUSES or not node.get('id') or node['id'] in node_ids:
            raise ValueError('joint statuses and IDs must be valid and unique')
        node_ids.add(node['id'])
        if not all(math.isfinite(float(node.get(axis, float('nan')))) for axis in ('x', 'y')):
            raise ValueError('joint x/y coordinates must be finite')
        if not (0 <= node['x'] <= image['width'] and 0 <= node['y'] <= image['height']):
            raise ValueError('joint coordinates must be inside the source image')
        if node['status'] != 'confirmed' and not node.get('reason'):
            raise ValueError('ambiguous and unobservable joints require a reason')
    member_ids = set()
    for member in members:
        if member.get('status') not in STATUSES or not member.get('id') or member['id'] in member_ids:
            raise ValueError('member statuses and IDs must be valid and unique')
        member_ids.add(member['id'])
        if member.get('node_i') not in node_ids or member.get('node_j') not in node_ids:
            raise ValueError('member endpoints must reference annotated joints')
        if member['node_i'] == member['node_j']:
            raise ValueError('member endpoints must be distinct')
        if member['status'] != 'confirmed' and not member.get('reason'):
            raise ValueError('ambiguous and unobservable members require a reason')
    for collection_name in ('ambiguous_regions', 'unobservable_regions'):
        for region in annotation.get(collection_name, []):
            expected_status = 'ambiguous' if collection_name == 'ambiguous_regions' else 'unobservable'
            if region.get('status') != expected_status or not region.get('reason'):
                raise ValueError(f'{collection_name} entries require status={expected_status!r} and a reason')
            if 'point' in region:
                point = region['point']
                if len(point) != 2 or not (0 <= point[0] <= image['width'] and 0 <= point[1] <= image['height']):
                    raise ValueError(f'{collection_name} point must be inside the source image')
            if 'bbox' in region:
                box = region['bbox']
                if len(box) != 4 or not (0 <= box[0] < box[2] <= image['width'] and 0 <= box[1] < box[3] <= image['height']):
                    raise ValueError(f'{collection_name} bbox must be an in-bounds box')
    return True


def _inside_roi(point, roi):
    x, y = point
    return roi[0] <= x <= roi[2] and roi[1] <= y <= roi[3]


def _maximum_cardinality_matches(predicted, reference, tolerance):
    """Deterministic maximum-cardinality one-to-one matches under a distance gate."""
    adjacency = []
    for point in predicted:
        neighbors = [
            (math.dist(point, target), index)
            for index, target in enumerate(reference)
            if math.dist(point, target) <= tolerance
        ]
        adjacency.append([index for _distance, index in sorted(neighbors)])

    reference_to_prediction = [-1] * len(reference)

    def augment(prediction_index, visited):
        for reference_index in adjacency[prediction_index]:
            if reference_index in visited:
                continue
            visited.add(reference_index)
            previous = reference_to_prediction[reference_index]
            if previous == -1 or augment(previous, visited):
                reference_to_prediction[reference_index] = prediction_index
                return True
        return False

    for prediction_index in sorted(range(len(predicted)), key=lambda i: (len(adjacency[i]), i)):
        augment(prediction_index, set())

    matches = []
    for reference_index, prediction_index in enumerate(reference_to_prediction):
        if prediction_index != -1:
            matches.append((prediction_index, reference_index, math.dist(predicted[prediction_index], reference[reference_index])))
    return sorted(matches)


def _union_length(intervals):
    if not intervals:
        return 0.0
    intervals = sorted(intervals)
    start, end = intervals[0]
    total = 0.0
    for next_start, next_end in intervals[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + end - start


def _member_coverage(reference_member, candidate_lines, corridor_px, angle_tolerance_deg):
    start, end = reference_member
    rx, ry = end[0] - start[0], end[1] - start[1]
    length = math.hypot(rx, ry)
    if length == 0:
        return 0.0
    ux, uy = rx / length, ry / length
    intervals = []
    for candidate in candidate_lines:
        p1, p2 = candidate
        vx, vy = p2[0] - p1[0], p2[1] - p1[1]
        candidate_length = math.hypot(vx, vy)
        if candidate_length == 0:
            continue
        cosine = min(1.0, abs((rx * vx + ry * vy) / (length * candidate_length)))
        angle = math.degrees(math.acos(cosine))
        if angle > angle_tolerance_deg:
            continue
        distances = (
            abs(rx * (p1[1] - start[1]) - ry * (p1[0] - start[0])) / length,
            abs(rx * (p2[1] - start[1]) - ry * (p2[0] - start[0])) / length,
        )
        if max(distances) > corridor_px:
            continue
        projections = sorted(((p1[0] - start[0]) * ux + (p1[1] - start[1]) * uy,
                              (p2[0] - start[0]) * ux + (p2[1] - start[1]) * uy))
        lo, hi = max(0.0, projections[0]), min(length, projections[1])
        if hi > lo:
            intervals.append((lo, hi))
    return min(1.0, _union_length(intervals) / length)


def evaluate_image(baseline_image, annotation, *, joint_tolerance_floor_px=12.0,
                   joint_tolerance_diagonal_fraction=0.0075,
                   member_corridor_floor_px=12.0,
                   member_corridor_diagonal_fraction=0.0075,
                   member_angle_tolerance_deg=8.0,
                   member_coverage_threshold=0.80):
    width, height = baseline_image['image_width'], baseline_image['image_height']
    diagonal = math.hypot(width, height)
    joint_tolerance = max(joint_tolerance_floor_px, joint_tolerance_diagonal_fraction * diagonal)
    member_corridor = max(member_corridor_floor_px, member_corridor_diagonal_fraction * diagonal)
    roi = annotation.get('evaluation_roi', [0, 0, width, height])

    references = [node for node in annotation['joints'] if node['status'] == 'confirmed']
    members = [member for member in annotation['members'] if member['status'] == 'confirmed']
    if annotation['assessment']['status'] not in {'confirmed', 'partial'} or roi is None or not references or not members:
        return {
            'filename': annotation['image']['filename'],
            'annotation_assessment': annotation['assessment']['status'],
            'metrics_status': 'unavailable',
            'metrics_unavailable_reason': 'No complete, selected, confirmed joint/member reference graph is available for this image.',
            'joint_precision': None,
            'joint_recall': None,
            'member_coverage_recall': None,
            'member_precision': None,
            'matched_joint_endpoint_error_px_mean': None,
            'matched_joint_endpoint_error_px_median': None,
        }
    predictions = [joint for joint in baseline_image['joints'] if _inside_roi(joint['point'], roi)]
    matches = _maximum_cardinality_matches(
        [joint['point'] for joint in predictions],
        [(node['x'], node['y']) for node in references],
        joint_tolerance,
    )
    tp = len(matches)
    joint_precision = tp / len(predictions) if predictions else None
    joint_recall = tp / len(references) if references else None
    errors = [distance for _prediction, _reference, distance in matches]

    lines = [(line['start'], line['end']) for line in baseline_image['lines']]
    member_coverages = []
    for member in members:
        node_by_id = {node['id']: node for node in references}
        first, second = node_by_id[member['node_i']], node_by_id[member['node_j']]
        member_coverages.append(_member_coverage(
            ((first['x'], first['y']), (second['x'], second['y'])),
            lines,
            member_corridor,
            member_angle_tolerance_deg,
        ))
    recovered_members = sum(coverage >= member_coverage_threshold for coverage in member_coverages)

    return {
        'filename': annotation['image']['filename'],
        'annotation_assessment': annotation['assessment']['status'],
        'metrics_status': 'partial' if annotation['assessment']['status'] == 'partial' else 'available',
        'confirmed_reference_joint_count': len(references),
        'detected_candidate_joints_in_roi': len(predictions),
        'matched_joints': tp,
        'joint_precision': joint_precision,
        'joint_recall': joint_recall,
        'matched_joint_endpoint_error_px_mean': sum(errors) / len(errors) if errors else None,
        'matched_joint_endpoint_error_px_median': statistics.median(errors) if errors else None,
        'confirmed_reference_member_count': len(members),
        'members_with_at_least_80_percent_candidate_line_coverage': recovered_members,
        'member_coverage_recall': recovered_members / len(members) if members else None,
        'member_precision': None,
        'member_precision_unavailable_reason': 'The detector emits raw line segments, not grouped or semantically classified member predictions.',
        'thresholds': {
            'joint_match_tolerance_px': joint_tolerance,
            'member_centerline_corridor_px': member_corridor,
            'member_angle_tolerance_degrees': member_angle_tolerance_deg,
            'member_coverage_recall_threshold': member_coverage_threshold,
        },
    }


def evaluate(baseline_path: Path, annotations_dir: Path):
    baseline = json.loads(baseline_path.read_text())
    by_name = {image['input']['filename']: image for image in baseline['images']}
    results = []
    for annotation_path in sorted(annotations_dir.glob('test*.json')):
        annotation = json.loads(annotation_path.read_text())
        validate_annotation(annotation)
        image_name = annotation['image']['filename']
        image = by_name[image_name]
        if annotation['image']['sha256'] != image['input']['sha256']:
            raise ValueError(f'{annotation_path.name}: source image hash does not match baseline')
        if annotation['image']['width'] != image['image_width'] or annotation['image']['height'] != image['image_height']:
            raise ValueError(f'{annotation_path.name}: annotation dimensions do not match baseline')
        results.append(evaluate_image(image, annotation))
    return results


def aggregate_results(results):
    included = [result for result in results if result.get('metrics_status') in {'available', 'partial'}]
    if not included:
        return {'metrics_status': 'unavailable', 'reason': 'No image has a confirmed reference graph.'}
    joint_tp = sum(result['matched_joints'] for result in included)
    joint_predictions = sum(result['detected_candidate_joints_in_roi'] for result in included)
    reference_joints = sum(result['confirmed_reference_joint_count'] for result in included)
    endpoint_count = sum(result['matched_joints'] for result in included)
    member_count = sum(result['confirmed_reference_member_count'] for result in included)
    member_recovered = sum(result['members_with_at_least_80_percent_candidate_line_coverage'] for result in included)
    endpoint_mean = (
        sum(result['matched_joint_endpoint_error_px_mean'] * result['matched_joints'] for result in included)
        / endpoint_count
        if endpoint_count else None
    )
    return {
        'metrics_status': 'exploratory_micro_average',
        'included_images': [result['filename'] for result in included],
        'excluded_images': [result['filename'] for result in results if result not in included],
        'joint_precision': joint_tp / joint_predictions if joint_predictions else None,
        'joint_recall': joint_tp / reference_joints if reference_joints else None,
        'matched_joint_endpoint_error_px_mean': endpoint_mean,
        'member_coverage_recall': member_recovered / member_count if member_count else None,
        'member_precision': None,
        'member_precision_unavailable_reason': 'The detector does not produce grouped or semantic member predictions.',
        'note': 'Micro-average over confirmed reference graphs only; five-image exploratory sample, not a general performance estimate.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    image_results = evaluate(args.baseline, args.annotations)
    result = {'method': 'phase-a-v1', 'aggregate': aggregate_results(image_results), 'images': image_results}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

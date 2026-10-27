"""Unit tests for pure truss request validation."""

import math
import unittest

from app import create_app
from app.models.truss import Load, Member, Node, Support, TrussModel, Units
from app.services.validation import (
    ZERO_LENGTH_ABS_TOL,
    ZERO_LENGTH_REL_TOL,
    validate_truss_request,
)


def valid_payload():
    return {
        "schema_version": "1.0",
        "metadata": {
            "name": "Triangle",
            "source": "manual",
            "units": {"length": "m", "force": "kN"},
        },
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


def payload_with_short_member(model_scale, member_length, offset=0.0):
    payload = valid_payload()
    payload["model"]["nodes"] = [
        {"id": "A", "x": offset, "y": offset},
        {"id": "B", "x": offset + member_length, "y": offset},
        {"id": "C", "x": offset + model_scale, "y": offset + model_scale},
    ]
    payload["model"]["members"] = [{"id": "AB", "node_i": "A", "node_j": "B"}]
    payload["model"]["supports"] = []
    payload["model"]["loads"] = []
    return payload


class TrussValidationTests(unittest.TestCase):
    def assert_issue(self, payload, code, path, additional=()):
        result = validate_truss_request(payload)
        self.assertIsNone(result.model)
        expected = {(code, path), *additional}
        actual = {(issue.code, issue.path) for issue in result.errors}
        self.assertEqual(actual, expected)
        return result

    def test_valid_triangle_normalizes_to_frozen_dataclasses(self):
        result = validate_truss_request(valid_payload())
        self.assertTrue(result.is_valid)
        self.assertEqual(
            result.model,
            TrussModel(
                schema_version="1.0",
                name="Triangle",
                source="manual",
                units=Units(length="m", force="kN"),
                nodes=(
                    Node(id="A", x=0.0, y=0.0),
                    Node(id="B", x=4.0, y=0.0),
                    Node(id="C", x=2.0, y=3.0),
                ),
                members=(
                    Member(id="AB", node_i="A", node_j="B"),
                    Member(id="AC", node_i="A", node_j="C"),
                    Member(id="BC", node_i="B", node_j="C"),
                ),
                supports=(
                    Support(id="S_A", node="A", type="pin"),
                    Support(id="S_B", node="B", type="roller", direction="vertical"),
                ),
                loads=(Load(id="L_C", node="C", fx=0.0, fy=-10.0),),
            ),
        )
        self.assertIsInstance(result.model, TrussModel)
        with self.assertRaises((AttributeError, TypeError)):
            result.model.nodes[0].x = 5

    def test_optional_metadata_and_negative_values_are_valid(self):
        payload = valid_payload()
        payload["metadata"].pop("name")
        payload["metadata"].pop("source")
        payload["model"]["nodes"][0]["x"] = -2
        payload["model"]["loads"][0]["fx"] = -3
        self.assertTrue(validate_truss_request(payload).is_valid)

    def test_empty_nodes_are_reported_and_empty_member_set_is_allowed(self):
        payload = valid_payload()
        payload["model"]["members"] = []
        payload["model"]["supports"] = []
        payload["model"]["loads"] = []
        self.assertTrue(validate_truss_request(payload).is_valid)
        payload["model"]["nodes"] = []
        self.assert_issue(payload, "EMPTY_MODEL", "/model/nodes")

    def test_disconnected_model_is_not_rejected_as_invalid(self):
        payload = valid_payload()
        payload["model"]["members"] = [{"id": "AB", "node_i": "A", "node_j": "B"}]
        payload["model"]["loads"] = []
        self.assertTrue(validate_truss_request(payload).is_valid)

    def test_non_object_request_and_missing_fields(self):
        self.assert_issue([], "INVALID_TYPE", "")
        payload = valid_payload()
        del payload["schema_version"]
        self.assert_issue(payload, "MISSING_FIELD", "/schema_version")

    def test_schema_version_missing_null_wrong_type_and_unsupported(self):
        payload = valid_payload()
        del payload["schema_version"]
        self.assert_issue(payload, "MISSING_FIELD", "/schema_version")
        payload = valid_payload()
        payload["schema_version"] = None
        self.assert_issue(payload, "INVALID_TYPE", "/schema_version")
        payload = valid_payload()
        payload["schema_version"] = 1.0
        self.assert_issue(payload, "INVALID_TYPE", "/schema_version")
        payload = valid_payload()
        payload["schema_version"] = "2.0"
        self.assert_issue(payload, "UNSUPPORTED_SCHEMA_VERSION", "/schema_version")

    def test_unknown_keys_and_schema_version_are_rejected(self):
        payload = valid_payload()
        payload["model"]["extra"] = 1
        self.assert_issue(payload, "UNKNOWN_FIELD", "/model/extra")
        payload = valid_payload()
        payload["model"]["extra/key"] = 1
        payload["model"]["other~key"] = 1
        result = validate_truss_request(payload)
        self.assertIsNone(result.model)
        self.assertEqual(
            {(issue.code, issue.path) for issue in result.errors},
            {
                ("UNKNOWN_FIELD", "/model/extra~1key"),
                ("UNKNOWN_FIELD", "/model/other~0key"),
            },
        )
        payload = valid_payload()
        payload["schema_version"] = "2.0"
        self.assert_issue(payload, "UNSUPPORTED_SCHEMA_VERSION", "/schema_version")

    def test_invalid_units(self):
        payload = valid_payload()
        payload["metadata"]["units"]["length"] = "cm"
        self.assert_issue(payload, "INVALID_VALUE", "/metadata/units/length")

    def test_blank_and_duplicate_node_ids(self):
        payload = valid_payload()
        payload["model"]["nodes"][0]["id"] = " "
        payload["model"]["members"] = []
        payload["model"]["supports"] = []
        payload["model"]["loads"] = []
        self.assert_issue(payload, "EMPTY_ID", "/model/nodes/0/id")
        payload = valid_payload()
        payload["model"]["nodes"][1]["id"] = "A"
        payload["model"]["members"] = []
        payload["model"]["supports"] = []
        payload["model"]["loads"] = []
        self.assert_issue(payload, "DUPLICATE_NODE_ID", "/model/nodes/1/id")

    def test_duplicate_member_support_and_load_ids(self):
        for collection, second, code, path in (
            ("members", {"id": "AB", "node_i": "A", "node_j": "C"}, "DUPLICATE_MEMBER_ID", "/model/members/3/id"),
            ("supports", {"id": "S_A", "node": "C", "type": "pin"}, "DUPLICATE_SUPPORT_ID", "/model/supports/2/id"),
            ("loads", {"id": "L_C", "node": "A", "fx": 0, "fy": 0}, "DUPLICATE_LOAD_ID", "/model/loads/1/id"),
        ):
            with self.subTest(collection=collection):
                payload = valid_payload()
                payload["model"][collection].append(second)
                self.assert_issue(payload, code, path)

    def test_member_unknown_nodes_self_connection_and_zero_length(self):
        payload = valid_payload()
        payload["model"]["members"][0]["node_j"] = "missing"
        self.assert_issue(payload, "UNKNOWN_NODE_REFERENCE", "/model/members/0/node_j")
        payload = valid_payload()
        payload["model"]["members"][0]["node_j"] = "A"
        self.assert_issue(payload, "SELF_CONNECTED_MEMBER", "/model/members/0/node_j")
        payload = valid_payload()
        payload["model"]["nodes"][1]["x"] = ZERO_LENGTH_ABS_TOL / 2
        payload["model"]["nodes"][1]["y"] = 0
        self.assert_issue(payload, "ZERO_LENGTH_MEMBER", "/model/members/0")

    def test_exactly_coincident_member_endpoints_are_rejected(self):
        payload = payload_with_short_member(2.0, 0.0)
        self.assert_issue(payload, "ZERO_LENGTH_MEMBER", "/model/members/0")

    def test_tolerance_is_translation_invariant_at_large_offset(self):
        for member_length, should_be_zero in ((0.5, True), (2.0, False)):
            with self.subTest(member_length=member_length):
                at_origin = validate_truss_request(payload_with_short_member(1e12, member_length))
                translated = validate_truss_request(
                    payload_with_short_member(1e12, member_length, offset=1e15)
                )
                self.assertEqual(at_origin.is_valid, not should_be_zero)
                self.assertEqual(translated.is_valid, not should_be_zero)
                self.assertEqual(
                    {(issue.code, issue.path) for issue in at_origin.errors},
                    {(issue.code, issue.path) for issue in translated.errors},
                )
                if should_be_zero:
                    self.assertEqual(
                        {(issue.code, issue.path) for issue in at_origin.errors},
                        {("ZERO_LENGTH_MEMBER", "/model/members/0")},
                    )

    def test_tolerance_floor_and_relative_term_at_small_ordinary_and_large_scales(self):
        cases = (
            (1e-6, ZERO_LENGTH_ABS_TOL / 2, False),
            (1e-6, ZERO_LENGTH_ABS_TOL * 2, True),
            (4.0, ZERO_LENGTH_REL_TOL * 4 / 2, False),
            (4.0, ZERO_LENGTH_REL_TOL * 4 * 2, True),
            (1e9, ZERO_LENGTH_REL_TOL * 1e9 / 2, False),
            (1e9, ZERO_LENGTH_REL_TOL * 1e9 * 2, True),
        )
        for model_scale, member_length, expected_valid in cases:
            with self.subTest(model_scale=model_scale, member_length=member_length):
                result = validate_truss_request(
                    payload_with_short_member(model_scale, member_length)
                )
                self.assertEqual(result.is_valid, expected_valid)
                if expected_valid:
                    self.assertEqual(result.errors, ())
                else:
                    self.assertEqual(
                        {(issue.code, issue.path) for issue in result.errors},
                        {("ZERO_LENGTH_MEMBER", "/model/members/0")},
                    )

    def test_non_finite_and_boolean_numeric_values_are_rejected(self):
        for invalid, code in ((math.nan, "NON_FINITE_NUMBER"), (math.inf, "NON_FINITE_NUMBER"), (-math.inf, "NON_FINITE_NUMBER"), (True, "INVALID_TYPE")):
            with self.subTest(invalid=invalid):
                payload = valid_payload()
                payload["model"]["nodes"][0]["x"] = invalid
                payload["model"]["members"] = []
                payload["model"]["supports"] = []
                payload["model"]["loads"] = []
                self.assert_issue(payload, code, "/model/nodes/0/x")
        payload = valid_payload()
        payload["model"]["loads"][0]["fy"] = math.nan
        self.assert_issue(payload, "NON_FINITE_NUMBER", "/model/loads/0/fy")

    def test_support_type_direction_references_and_duplicate_nodes(self):
        cases = [
            (lambda p: p["model"]["supports"][0].update(type="fixed"), "INVALID_SUPPORT_TYPE"),
            (lambda p: p["model"]["supports"][1].pop("direction"), "MISSING_FIELD"),
            (lambda p: p["model"]["supports"][1].update(direction="diagonal"), "INVALID_VALUE"),
            (lambda p: p["model"]["supports"][0].update(direction="horizontal"), "UNEXPECTED_FIELD", "/model/supports/0/direction", (("UNKNOWN_FIELD", "/model/supports/0/direction"),)),
            (lambda p: p["model"]["supports"][1].update(node="unknown"), "UNKNOWN_NODE_REFERENCE", "/model/supports/1/node", ()),
            (lambda p: p["model"]["supports"].append({"id": "S_C", "node": "A", "type": "pin"}), "DUPLICATE_SUPPORT_NODE", "/model/supports/2/node", ()),
        ]
        # Give every focused case its exact code/path pair set.
        expected_fields = {
            "INVALID_SUPPORT_TYPE": "/model/supports/0/type",
            "MISSING_FIELD": "/model/supports/1/direction",
            "INVALID_VALUE": "/model/supports/1/direction",
        }
        for case in cases:
            if len(case) == 2:
                mutate, code = case
                path = expected_fields[code]
                additional = ()
            else:
                mutate, code, path, additional = case
            with self.subTest(code=code):
                payload = valid_payload()
                mutate(payload)
                self.assert_issue(payload, code, path, additional)

    def test_load_reference_and_duplicate_node_records(self):
        payload = valid_payload()
        payload["model"]["loads"][0]["node"] = "missing"
        self.assert_issue(payload, "UNKNOWN_NODE_REFERENCE", "/model/loads/0/node")
        payload = valid_payload()
        payload["model"]["loads"].append({"id": "L2", "node": "C", "fx": 0, "fy": 1})
        self.assert_issue(payload, "DUPLICATE_LOAD_NODE", "/model/loads/1/node")

    def test_health_endpoint_remains_available(self):
        response = create_app().test_client().get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "application": "Sketch2Solve"})


if __name__ == "__main__":
    unittest.main()

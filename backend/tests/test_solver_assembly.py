"""Unit tests for deterministic joint-equilibrium matrix assembly."""

import math
import unittest

import numpy as np

from app.models.truss import Load, Member, Node, Support, TrussModel, Units
from app.services.solver import SolverAssemblyError, assemble_equilibrium_system


def make_model(nodes, members=(), supports=(), loads=()):
    return TrussModel(
        schema_version="1.0",
        name=None,
        source=None,
        units=Units(length="m", force="kN"),
        nodes=tuple(nodes),
        members=tuple(members),
        supports=tuple(supports),
        loads=tuple(loads),
    )


class EquilibriumAssemblyTests(unittest.TestCase):
    def test_horizontal_member_direction_cosines_and_equations(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", 3, 0)),
            (Member("AB", "A", "B"),),
        )
        system = assemble_equilibrium_system(model)
        np.testing.assert_allclose(system.coefficient_matrix, [[1], [0], [-1], [0]])
        np.testing.assert_allclose(system.rhs, [0, 0, 0, 0])
        self.assertEqual(system.unknown_ids, ("member:AB",))
        self.assertEqual(
            system.equation_ids,
            ("node:A:fx", "node:A:fy", "node:B:fx", "node:B:fy"),
        )

    def test_vertical_member_direction_cosines(self):
        model = make_model(
            (Node("A", 1, -2), Node("B", 1, 5)),
            (Member("AB", "A", "B"),),
        )
        system = assemble_equilibrium_system(model)
        np.testing.assert_allclose(system.coefficient_matrix, [[0], [1], [0], [-1]])

    def test_inclined_member_uses_unrounded_direction_cosines(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", 3, 4)),
            (Member("AB", "A", "B"),),
        )
        system = assemble_equilibrium_system(model)
        np.testing.assert_allclose(
            system.coefficient_matrix,
            [[3 / 5], [4 / 5], [-3 / 5], [-4 / 5]],
            rtol=0,
            atol=1e-15,
        )

    def test_pin_and_vertical_roller_reaction_columns(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", 2, 0)),
            (Member("AB", "A", "B"),),
            (
                Support("S_A", "A", "pin"),
                Support("S_B", "B", "roller", "vertical"),
            ),
        )
        system = assemble_equilibrium_system(model)
        self.assertEqual(
            system.unknown_ids,
            ("member:AB", "reaction:S_A:x", "reaction:S_A:y", "reaction:S_B:y"),
        )
        np.testing.assert_allclose(
            system.coefficient_matrix,
            [
                [1, 1, 0, 0],
                [0, 0, 1, 0],
                [-1, 0, 0, 0],
                [0, 0, 0, 1],
            ],
        )

    def test_applied_loads_move_to_rhs_with_opposite_sign(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", 1, 0)),
            loads=(Load("L_B", "B", 7, -9),),
        )
        system = assemble_equilibrium_system(model)
        np.testing.assert_allclose(system.rhs, [0, 0, -7, 9])
        self.assertEqual(system.force_unit, "kN")

    def test_unknown_and_equation_order_follows_model_tuple_order(self):
        model = make_model(
            (Node("B", 1, 0), Node("A", 0, 0)),
            (Member("second", "B", "A"), Member("first", "A", "B")),
            (
                Support("roller", "B", "roller", "horizontal"),
                Support("pin", "A", "pin"),
            ),
        )
        system = assemble_equilibrium_system(model)
        self.assertEqual(
            system.unknown_ids,
            (
                "member:second",
                "member:first",
                "reaction:roller:x",
                "reaction:pin:x",
                "reaction:pin:y",
            ),
        )
        self.assertEqual(
            system.equation_ids,
            ("node:B:fx", "node:B:fy", "node:A:fx", "node:A:fy"),
        )
        self.assertEqual(system.coefficient_matrix[0, 2], 1.0)

    def test_zero_length_member_geometry_is_reported(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", 0, 0)),
            (Member("AB", "A", "B"),),
        )
        with self.assertRaises(SolverAssemblyError) as context:
            assemble_equilibrium_system(model)
        self.assertEqual(context.exception.code, "INVALID_GEOMETRY")

    def test_non_finite_node_geometry_is_reported(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", math.inf, 1)),
            (Member("AB", "A", "B"),),
        )
        with self.assertRaises(SolverAssemblyError) as context:
            assemble_equilibrium_system(model)
        self.assertEqual(context.exception.code, "INVALID_GEOMETRY")

    def test_triangular_truss_assembly(self):
        model = make_model(
            (Node("A", 0, 0), Node("B", 4, 0), Node("C", 2, 3)),
            (
                Member("AB", "A", "B"),
                Member("AC", "A", "C"),
                Member("BC", "B", "C"),
            ),
            (
                Support("S_A", "A", "pin"),
                Support("S_B", "B", "roller", "vertical"),
            ),
            (Load("L_C", "C", 0, -10),),
        )
        system = assemble_equilibrium_system(model)
        direction = 1 / math.sqrt(13)
        expected_matrix = np.array(
            [
                [1, 2 * direction, 0, 1, 0, 0],
                [0, 3 * direction, 0, 0, 1, 0],
                [-1, 0, -2 * direction, 0, 0, 0],
                [0, 0, 3 * direction, 0, 0, 1],
                [0, -2 * direction, 2 * direction, 0, 0, 0],
                [0, -3 * direction, -3 * direction, 0, 0, 0],
            ]
        )
        np.testing.assert_allclose(system.coefficient_matrix, expected_matrix, atol=1e-15)
        np.testing.assert_allclose(system.rhs, [0, 0, 0, 0, 0, 10])
        self.assertEqual(
            system.unknown_ids,
            (
                "member:AB",
                "member:AC",
                "member:BC",
                "reaction:S_A:x",
                "reaction:S_A:y",
                "reaction:S_B:y",
            ),
        )
        self.assertEqual(
            system.equation_ids,
            (
                "node:A:fx",
                "node:A:fy",
                "node:B:fx",
                "node:B:fy",
                "node:C:fx",
                "node:C:fy",
            ),
        )
        self.assertEqual(system.force_unit, "kN")


if __name__ == "__main__":
    unittest.main()

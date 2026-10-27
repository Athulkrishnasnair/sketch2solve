"""Unit tests for direct, determinate equilibrium-system solution."""

import math
import unittest

import numpy as np

from app.models.truss import Load, Member, Node, Support, TrussModel, Units
from app.services.solver import (
    EquilibriumSystem,
    MAX_CONDITION_NUMBER,
    RESIDUAL_ABS_TOL,
    RESIDUAL_REL_TOL,
    assemble_equilibrium_system,
    solve_equilibrium_system,
)


def triangular_model():
    return TrussModel(
        schema_version="1.0",
        name="Triangle",
        source="test",
        units=Units(length="m", force="kN"),
        nodes=(Node("A", 0, 0), Node("B", 4, 0), Node("C", 2, 3)),
        members=(
            Member("AB", "A", "B"),
            Member("AC", "A", "C"),
            Member("BC", "B", "C"),
        ),
        supports=(
            Support("S_A", "A", "pin"),
            Support("S_B", "B", "roller", "vertical"),
        ),
        loads=(Load("L_C", "C", 0, -10),),
    )


def system(matrix, rhs, unknown_ids=None, equation_ids=None):
    matrix = np.asarray(matrix, dtype=float)
    rhs = np.asarray(rhs, dtype=float)
    return EquilibriumSystem(
        coefficient_matrix=matrix,
        rhs=rhs,
        unknown_ids=tuple(unknown_ids if unknown_ids is not None else (f"u{i}" for i in range(matrix.shape[1]))),
        equation_ids=tuple(equation_ids if equation_ids is not None else (f"e{i}" for i in range(matrix.shape[0]))),
        force_unit="kN",
    )


class EquilibriumSolutionTests(unittest.TestCase):
    def test_triangular_truss_solves_to_analytical_forces_and_reactions(self):
        equilibrium = assemble_equilibrium_system(triangular_model())
        result = solve_equilibrium_system(equilibrium)

        self.assertEqual(result.status, "SOLVED")
        self.assertIsNone(result.error_code)
        np.testing.assert_allclose(
            result.unknown_values,
            (
                10 / 3,
                -10 * math.sqrt(13) / 6,
                -10 * math.sqrt(13) / 6,
                0.0,
                5.0,
                5.0,
            ),
            rtol=1e-12,
            atol=1e-12,
        )
        self.assertEqual(
            tuple(result.member_forces),
            ("AB", "AC", "BC"),
        )
        self.assertAlmostEqual(result.member_forces["AB"], 10 / 3, places=12)
        self.assertAlmostEqual(result.member_forces["AC"], -10 * math.sqrt(13) / 6, places=12)
        self.assertAlmostEqual(result.member_forces["BC"], -10 * math.sqrt(13) / 6, places=12)
        self.assertGreater(result.member_forces["AB"], 0.0)
        self.assertLess(result.member_forces["AC"], 0.0)
        self.assertLess(result.member_forces["BC"], 0.0)
        np.testing.assert_allclose(
            list(result.support_reactions.values()),
            [0.0, 5.0, 5.0],
            atol=1e-12,
        )
        self.assertLessEqual(result.max_residual, result.residual_tolerance)
        self.assertLessEqual(
            result.residual_tolerance,
            RESIDUAL_ABS_TOL + RESIDUAL_REL_TOL * 10,
        )
        self.assertEqual(result.force_unit, "kN")

    def test_nonsquare_system_returns_explicit_failure_without_values(self):
        equilibrium = system([[1.0], [0.0]], [0.0, 0.0])
        result = solve_equilibrium_system(equilibrium)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.error_code, "NONSQUARE_SYSTEM")
        self.assertIn("square", result.message)
        self.assertIsNone(result.unknown_values)
        self.assertIsNone(result.member_forces)
        self.assertIsNone(result.support_reactions)
        self.assertIsNone(result.max_residual)

    def test_rank_deficient_system_is_detected_before_solving(self):
        equilibrium = system([[1.0, 1.0], [2.0, 2.0]], [1.0, 2.0])
        result = solve_equilibrium_system(equilibrium)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.error_code, "RANK_DEFICIENT_SYSTEM")
        self.assertIn("rank", result.message)
        self.assertIsNone(result.unknown_values)

    def test_nonfinite_matrix_and_rhs_are_rejected(self):
        cases = (
            (system([[math.nan]], [1.0]), "NONFINITE_SYSTEM"),
            (system([[1.0]], [math.inf]), "NONFINITE_SYSTEM"),
        )
        for equilibrium, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                result = solve_equilibrium_system(equilibrium)
                self.assertEqual(result.status, "FAILED")
                self.assertEqual(result.error_code, expected_code)
                self.assertIsNone(result.unknown_values)
                self.assertIsNone(result.member_forces)

    def test_ill_conditioned_system_is_rejected(self):
        equilibrium = system([[1.0, 0.0], [0.0, 1 / (MAX_CONDITION_NUMBER * 10)]], [1.0, 1.0])
        result = solve_equilibrium_system(equilibrium)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.error_code, "ILL_CONDITIONED_SYSTEM")
        self.assertGreater(result.condition_number, MAX_CONDITION_NUMBER)
        self.assertIsNone(result.unknown_values)

    def test_nonfinite_direct_solution_is_not_returned(self):
        equilibrium = system([[1e-300]], [1e100], unknown_ids=("member:tiny",))
        result = solve_equilibrium_system(equilibrium)
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.error_code, "NONFINITE_SOLUTION")
        self.assertIsNone(result.unknown_values)
        self.assertIsNone(result.member_forces)

    def test_solved_values_map_deterministically_to_member_and_reaction_ids(self):
        first = solve_equilibrium_system(assemble_equilibrium_system(triangular_model()))
        second = solve_equilibrium_system(assemble_equilibrium_system(triangular_model()))
        self.assertEqual(first.unknown_values, second.unknown_values)
        self.assertEqual(first.member_forces, second.member_forces)
        self.assertEqual(first.support_reactions, second.support_reactions)
        self.assertEqual(
            list(first.support_reactions),
            [("S_A", "x"), ("S_A", "y"), ("S_B", "y")],
        )


if __name__ == "__main__":
    unittest.main()

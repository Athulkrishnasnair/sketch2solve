"""Matrix-level diagnostic tests; no physical stability is inferred here."""

import math
import unittest

import numpy as np

from app.models.truss import Load, Member, Node, Support, TrussModel, Units
from app.services.solver import (
    MAX_CONDITION_NUMBER,
    EquilibriumSystem,
    assemble_equilibrium_system,
    diagnose_equilibrium_system,
    solve_equilibrium_system,
)


def matrix_system(matrix, rhs=None):
    matrix = np.asarray(matrix, dtype=float)
    if rhs is None:
        rhs = np.zeros(matrix.shape[0])
    rhs = np.asarray(rhs, dtype=float)
    return EquilibriumSystem(
        coefficient_matrix=matrix,
        rhs=rhs,
        unknown_ids=tuple(f"unknown-{index}" for index in range(matrix.shape[1])),
        equation_ids=tuple(f"equation-{index}" for index in range(matrix.shape[0])),
        force_unit="kN",
    )


def triangle_system():
    model = TrussModel(
        schema_version="1.0",
        name=None,
        source=None,
        units=Units(length="m", force="kN"),
        nodes=(Node("A", 0, 0), Node("B", 4, 0), Node("C", 2, 3)),
        members=(
            Member("AB", "A", "B"),
            Member("AC", "A", "C"),
            Member("BC", "B", "C"),
        ),
        supports=(Support("S_A", "A", "pin"), Support("S_B", "B", "roller", "vertical")),
        loads=(Load("L_C", "C", 0, -10),),
    )
    return assemble_equilibrium_system(model)


class EquilibriumDiagnosticsTests(unittest.TestCase):
    def test_square_full_rank_triangle_diagnostics_and_solution_are_preserved(self):
        system = triangle_system()
        diagnostics = diagnose_equilibrium_system(system)
        self.assertEqual(diagnostics.category, "SQUARE_FULL_RANK")
        self.assertEqual(diagnostics.equation_count, 6)
        self.assertEqual(diagnostics.unknown_count, 6)
        self.assertEqual(diagnostics.matrix_shape, (6, 6))
        self.assertEqual(diagnostics.numerical_rank, 6)
        self.assertTrue(diagnostics.is_square)
        self.assertTrue(diagnostics.has_full_column_rank)
        self.assertTrue(diagnostics.has_full_row_rank)
        expected_tolerance = (
            max(system.coefficient_matrix.shape)
            * np.finfo(np.float64).eps
            * np.linalg.svd(system.coefficient_matrix, compute_uv=False)[0]
        )
        self.assertAlmostEqual(diagnostics.rank_tolerance, expected_tolerance, delta=0.0)
        self.assertIsNotNone(diagnostics.condition_number)

        solution = solve_equilibrium_system(system)
        self.assertEqual(solution.status, "SOLVED")
        self.assertAlmostEqual(solution.member_forces["AB"], 10 / 3, places=12)
        self.assertAlmostEqual(solution.member_forces["AC"], -10 * math.sqrt(13) / 6, places=12)
        self.assertAlmostEqual(solution.member_forces["BC"], -10 * math.sqrt(13) / 6, places=12)
        np.testing.assert_allclose(
            list(solution.support_reactions.values()), [0, 5, 5], atol=1e-12
        )
        self.assertLessEqual(solution.max_residual, solution.residual_tolerance)

    def test_square_rank_deficient_matrix_is_singular_square(self):
        diagnostics = diagnose_equilibrium_system(matrix_system([[1, 2], [2, 4]]))
        self.assertEqual(diagnostics.category, "SINGULAR_SQUARE")
        self.assertEqual(diagnostics.numerical_rank, 1)
        self.assertTrue(diagnostics.is_square)
        self.assertFalse(diagnostics.has_full_column_rank)
        self.assertFalse(diagnostics.has_full_row_rank)
        self.assertIsNone(diagnostics.condition_number)

    def test_fewer_equations_than_unknowns_is_underdetermined(self):
        diagnostics = diagnose_equilibrium_system(matrix_system([[1, 0, 1], [0, 1, 1]]))
        self.assertEqual(diagnostics.category, "UNDERDETERMINED")
        self.assertEqual(diagnostics.matrix_shape, (2, 3))
        self.assertEqual(diagnostics.numerical_rank, 2)
        self.assertFalse(diagnostics.is_square)
        self.assertFalse(diagnostics.has_full_column_rank)
        self.assertTrue(diagnostics.has_full_row_rank)
        self.assertIsNotNone(diagnostics.condition_number)

    def test_more_equations_than_unknowns_is_overdetermined(self):
        system = matrix_system([[1, 0], [0, 1], [1, 1]])
        diagnostics = diagnose_equilibrium_system(system)
        self.assertEqual(diagnostics.category, "OVERDETERMINED")
        self.assertEqual(diagnostics.matrix_shape, (3, 2))
        self.assertEqual(diagnostics.numerical_rank, 2)
        self.assertTrue(diagnostics.has_full_column_rank)
        self.assertFalse(diagnostics.has_full_row_rank)
        self.assertIsNone(diagnostics.error_code)
        # Phase 2B still refuses nonsquare systems instead of using a
        # least-squares result as a structural answer.
        solution = solve_equilibrium_system(system)
        self.assertEqual(solution.status, "FAILED")
        self.assertEqual(solution.error_code, "NONSQUARE_SYSTEM")
        self.assertIsNone(solution.unknown_values)

    def test_ill_conditioned_full_rank_square_matrix_is_flagged(self):
        diagnostics = diagnose_equilibrium_system(
            matrix_system([[1.0, 0.0], [0.0, 1 / (MAX_CONDITION_NUMBER * 10)]])
        )
        self.assertEqual(diagnostics.category, "NUMERICALLY_ILL_CONDITIONED")
        self.assertEqual(diagnostics.numerical_rank, 2)
        self.assertTrue(diagnostics.has_full_column_rank)
        self.assertTrue(diagnostics.has_full_row_rank)
        self.assertGreater(diagnostics.condition_number, MAX_CONDITION_NUMBER)

    def test_invalid_dimensions_and_nonfinite_values_are_invalid(self):
        bad_rhs_length = EquilibriumSystem(
            coefficient_matrix=np.eye(2),
            rhs=np.zeros(1),
            unknown_ids=("u0", "u1"),
            equation_ids=("e0", "e1"),
            force_unit="kN",
        )
        invalid_dimension_result = diagnose_equilibrium_system(bad_rhs_length)
        self.assertEqual(invalid_dimension_result.category, "INVALID_SYSTEM")
        self.assertEqual(invalid_dimension_result.error_code, "INVALID_SYSTEM")
        self.assertIsNone(invalid_dimension_result.numerical_rank)

        for invalid in (
            matrix_system([[math.nan]]),
            matrix_system([[1.0]], [math.inf]),
        ):
            with self.subTest(matrix=invalid.coefficient_matrix, rhs=invalid.rhs):
                diagnostics = diagnose_equilibrium_system(invalid)
                self.assertEqual(diagnostics.category, "INVALID_SYSTEM")
                self.assertEqual(diagnostics.error_code, "NONFINITE_SYSTEM")
                self.assertIsNone(diagnostics.rank_tolerance)
                self.assertIsNone(diagnostics.condition_number)

    def test_category_precedence_when_properties_overlap(self):
        # A square rank-deficient matrix is singular-square, not merely
        # underdetermined or ill-conditioned.
        square_singular = diagnose_equilibrium_system(matrix_system([[1, 1], [2, 2]]))
        self.assertEqual(square_singular.category, "SINGULAR_SQUARE")

        # A tall matrix with insufficient independent equations for all its
        # unknowns is underdetermined, despite having more rows than columns.
        tall_rank_deficient = diagnose_equilibrium_system(
            matrix_system([[1, 1], [2, 2], [3, 3]])
        )
        self.assertEqual(tall_rank_deficient.category, "UNDERDETERMINED")

        # Invalid values take precedence even when the matrix shape is also
        # nonsquare.
        invalid_tall = matrix_system([[math.inf], [1.0]])
        invalid_diagnostics = diagnose_equilibrium_system(invalid_tall)
        self.assertEqual(invalid_diagnostics.category, "INVALID_SYSTEM")
        self.assertFalse(invalid_diagnostics.is_square)


if __name__ == "__main__":
    unittest.main()

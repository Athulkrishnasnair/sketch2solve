"""Assembly and direct solution of small planar truss equilibrium systems.

This module assembles equations only; it does not solve or classify the
assembly does not classify structural stability. Member-force and reaction
unknowns are positive in their defined directions. Member force is positive
in tension and negative in compression. Global positive x points right and
positive y points up. Matrix coefficients are dimensionless direction cosines
or unit reaction directions; the right-hand side and force unknowns use
``model.units.force``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from app.models.truss import Node, TrussModel


FloatMatrix = NDArray[np.float64]
FloatVector = NDArray[np.float64]
DiagnosticCategory = Literal[
    "SQUARE_FULL_RANK",
    "UNDERDETERMINED",
    "OVERDETERMINED",
    "SINGULAR_SQUARE",
    "NUMERICALLY_ILL_CONDITIONED",
    "INVALID_SYSTEM",
]


@dataclass(frozen=True)
class EquilibriumSystem:
    """Joint-equilibrium matrix and its stable row/column labels."""

    coefficient_matrix: FloatMatrix
    rhs: FloatVector
    unknown_ids: tuple[str, ...]
    equation_ids: tuple[str, ...]
    force_unit: str


@dataclass(frozen=True)
class SystemDiagnostics:
    """Matrix-level facts and a cautious category for an equilibrium system."""

    category: DiagnosticCategory
    equation_count: int | None
    unknown_count: int | None
    matrix_shape: tuple[int, ...] | None
    numerical_rank: int | None
    rank_tolerance: float | None
    is_square: bool | None
    has_full_column_rank: bool | None
    has_full_row_rank: bool | None
    condition_number: float | None
    error_code: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class TrussSolution:
    """Complete direct-solve result, or an explicit failure with no values."""

    status: Literal["SOLVED", "FAILED"]
    unknown_values: tuple[float, ...] | None
    member_forces: dict[str, float] | None
    support_reactions: dict[tuple[str, str], float] | None
    max_residual: float | None
    residual_tolerance: float | None
    force_unit: str
    error_code: str | None = None
    message: str | None = None
    condition_number: float | None = None


class SolverAssemblyError(ValueError):
    """An invalid or geometrically unusable model cannot be assembled."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# Float64 policy for this initial direct-solve implementation. The condition
# number cutoff is a conservative heuristic, not a structural criterion.
MAX_CONDITION_NUMBER = 1e12
RESIDUAL_REL_TOL = 1e-10
RESIDUAL_ABS_TOL = 1e-12


def diagnose_equilibrium_system(system: EquilibriumSystem) -> SystemDiagnostics:
    """Report matrix properties without assigning a physical structural cause.

    Numerical rank uses singular values of the float64 matrix. Its threshold is
    ``max(m, n) * eps * largest_singular_value``, where ``m`` and ``n`` are
    matrix dimensions and ``eps`` is float64 machine precision. This standard
    scale-aware threshold grows with matrix size and coefficient scale; it is
    a numerical convention, not an exact boundary between physical states.

    Category precedence is: invalid input; singular square; fewer independent
    equations than unknowns (underdetermined); excessive condition number;
    then overdetermined or square full rank. Thus an overdetermined matrix
    whose rank is below its unknown count is categorized as underdetermined.
    An overdetermined category does not mean equations are consistent: this
    function does not solve or run a consistency/least-squares check.
    """
    try:
        matrix_input = np.asarray(system.coefficient_matrix)
        rhs_input = np.asarray(system.rhs)
        if (
            not np.issubdtype(matrix_input.dtype, np.number)
            or not np.issubdtype(rhs_input.dtype, np.number)
            or np.iscomplexobj(matrix_input)
            or np.iscomplexobj(rhs_input)
        ):
            return _invalid_diagnostics("Matrix and RHS must contain real numeric values.")
        matrix = np.asarray(matrix_input, dtype=np.float64)
        rhs = np.asarray(rhs_input, dtype=np.float64)
    except (TypeError, ValueError, OverflowError):
        return _invalid_diagnostics("Matrix and RHS must contain real numeric values.")

    shape = tuple(int(size) for size in matrix.shape)
    if matrix.ndim != 2 or rhs.ndim != 1:
        return _invalid_diagnostics(
            "Matrix must be 2D and RHS must be 1D.",
            matrix_shape=shape,
            equation_count=matrix.shape[0] if matrix.ndim == 2 else None,
            unknown_count=matrix.shape[1] if matrix.ndim == 2 else None,
        )

    equation_count, unknown_count = matrix.shape
    is_square = equation_count == unknown_count
    if (
        equation_count == 0
        or unknown_count == 0
        or rhs.shape[0] != equation_count
        or len(system.equation_ids) != equation_count
        or len(system.unknown_ids) != unknown_count
    ):
        return _invalid_diagnostics(
            "System dimensions must be nonempty and agree with the RHS and labels.",
            matrix_shape=shape,
            equation_count=equation_count,
            unknown_count=unknown_count,
            is_square=is_square,
        )
    if not np.all(np.isfinite(matrix)) or not np.all(np.isfinite(rhs)):
        return _invalid_diagnostics(
            "Matrix and RHS values must all be finite.",
            matrix_shape=shape,
            equation_count=equation_count,
            unknown_count=unknown_count,
            is_square=is_square,
            error_code="NONFINITE_SYSTEM",
        )

    try:
        singular_values = np.linalg.svd(matrix, compute_uv=False)
    except np.linalg.LinAlgError:
        return _invalid_diagnostics(
            "NumPy could not calculate singular values for the matrix.",
            matrix_shape=shape,
            equation_count=equation_count,
            unknown_count=unknown_count,
            is_square=is_square,
            error_code="NUMERICAL_DIAGNOSTIC_FAILED",
        )

    largest_singular_value = float(singular_values[0])
    if not np.all(np.isfinite(singular_values)):
        return _invalid_diagnostics(
            "Singular-value diagnostics produced non-finite values.",
            matrix_shape=shape,
            equation_count=equation_count,
            unknown_count=unknown_count,
            is_square=is_square,
            error_code="NUMERICAL_DIAGNOSTIC_FAILED",
        )
    rank_tolerance = max(equation_count, unknown_count) * np.finfo(np.float64).eps * largest_singular_value
    numerical_rank = int(np.count_nonzero(singular_values > rank_tolerance))
    has_full_column_rank = numerical_rank == unknown_count
    has_full_row_rank = numerical_rank == equation_count
    condition_number: float | None = None
    if numerical_rank == min(equation_count, unknown_count):
        smallest_singular_value = float(singular_values[-1])
        if smallest_singular_value > 0:
            condition_number = largest_singular_value / smallest_singular_value

    if is_square and numerical_rank < unknown_count:
        category: DiagnosticCategory = "SINGULAR_SQUARE"
    elif numerical_rank < unknown_count:
        category = "UNDERDETERMINED"
    elif condition_number is not None and (
        not math.isfinite(condition_number) or condition_number > MAX_CONDITION_NUMBER
    ):
        category = "NUMERICALLY_ILL_CONDITIONED"
    elif equation_count > unknown_count:
        category = "OVERDETERMINED"
    else:
        category = "SQUARE_FULL_RANK"

    return SystemDiagnostics(
        category=category,
        equation_count=equation_count,
        unknown_count=unknown_count,
        matrix_shape=shape,
        numerical_rank=numerical_rank,
        rank_tolerance=float(rank_tolerance),
        is_square=is_square,
        has_full_column_rank=has_full_column_rank,
        has_full_row_rank=has_full_row_rank,
        condition_number=condition_number,
    )


def _invalid_diagnostics(
    message: str,
    *,
    matrix_shape: tuple[int, ...] | None = None,
    equation_count: int | None = None,
    unknown_count: int | None = None,
    is_square: bool | None = None,
    error_code: str = "INVALID_SYSTEM",
) -> SystemDiagnostics:
    return SystemDiagnostics(
        category="INVALID_SYSTEM",
        equation_count=equation_count,
        unknown_count=unknown_count,
        matrix_shape=matrix_shape,
        numerical_rank=None,
        rank_tolerance=None,
        is_square=is_square,
        has_full_column_rank=None,
        has_full_row_rank=None,
        condition_number=None,
        error_code=error_code,
        message=message,
    )


def assemble_equilibrium_system(model: TrussModel) -> EquilibriumSystem:
    """Assemble ``A x = rhs`` in deterministic model tuple order.

    Rows are ordered by nodes, with x equilibrium then y equilibrium for each
    node. Columns are ordered by members, then supports; each support's axes
    are ordered x then y. Unknown labels are ``member:<id>`` and
    ``reaction:<support-id>:<axis>``. Applied loads are moved to the RHS, so
    ``rhs = -external_load`` for each joint equation.

    Raises ``SolverAssemblyError`` for duplicate identifiers, invalid support
    definitions/references, invalid load references, or unusable member
    geometry. The caller should validate external input before assembly.
    """
    node_rows: dict[str, int] = {}
    node_by_id: dict[str, Node] = {}
    for node_index, node in enumerate(model.nodes):
        if node.id in node_rows:
            raise SolverAssemblyError("DUPLICATE_NODE_ID", f"Duplicate node ID '{node.id}'.")
        if not math.isfinite(node.x) or not math.isfinite(node.y):
            raise SolverAssemblyError("INVALID_GEOMETRY", f"Node '{node.id}' has non-finite coordinates.")
        node_rows[node.id] = 2 * node_index
        node_by_id[node.id] = node

    unknown_ids: list[str] = []
    for member in model.members:
        unknown_id = f"member:{member.id}"
        if unknown_id in unknown_ids:
            raise SolverAssemblyError("DUPLICATE_MEMBER_ID", f"Duplicate member ID '{member.id}'.")
        unknown_ids.append(unknown_id)

    support_axes: list[tuple[str, tuple[str, ...]]] = []
    seen_support_ids: set[str] = set()
    seen_supported_nodes: set[str] = set()
    for support in model.supports:
        if support.id in seen_support_ids:
            raise SolverAssemblyError("DUPLICATE_SUPPORT_ID", f"Duplicate support ID '{support.id}'.")
        seen_support_ids.add(support.id)
        if support.node not in node_rows:
            raise SolverAssemblyError(
                "UNKNOWN_NODE_REFERENCE",
                f"Support '{support.id}' references unknown node '{support.node}'.",
            )
        if support.node in seen_supported_nodes:
            raise SolverAssemblyError(
                "DUPLICATE_SUPPORT_NODE",
                f"Node '{support.node}' has more than one support.",
            )
        seen_supported_nodes.add(support.node)

        if support.type == "pin" and support.direction is None:
            axes = ("x", "y")
        elif support.type == "roller" and support.direction == "horizontal":
            axes = ("x",)
        elif support.type == "roller" and support.direction == "vertical":
            axes = ("y",)
        else:
            raise SolverAssemblyError(
                "INVALID_SUPPORT",
                f"Support '{support.id}' has an invalid type or direction.",
            )
        support_axes.append((support.id, axes))
        unknown_ids.extend(f"reaction:{support.id}:{axis}" for axis in axes)

    for load in model.loads:
        if load.node not in node_rows:
            raise SolverAssemblyError(
                "UNKNOWN_NODE_REFERENCE",
                f"Load '{load.id}' references unknown node '{load.node}'.",
            )
        if not math.isfinite(load.fx) or not math.isfinite(load.fy):
            raise SolverAssemblyError("INVALID_LOAD", f"Load '{load.id}' has non-finite components.")

    equation_ids = tuple(
        label
        for node in model.nodes
        for label in (f"node:{node.id}:fx", f"node:{node.id}:fy")
    )
    column_by_id = {unknown_id: index for index, unknown_id in enumerate(unknown_ids)}
    matrix = np.zeros((2 * len(model.nodes), len(unknown_ids)), dtype=np.float64)
    rhs = np.zeros(2 * len(model.nodes), dtype=np.float64)

    for member in model.members:
        if member.node_i not in node_rows:
            raise SolverAssemblyError(
                "UNKNOWN_NODE_REFERENCE",
                f"Member '{member.id}' references unknown node '{member.node_i}'.",
            )
        if member.node_j not in node_rows:
            raise SolverAssemblyError(
                "UNKNOWN_NODE_REFERENCE",
                f"Member '{member.id}' references unknown node '{member.node_j}'.",
            )
        if member.node_i == member.node_j:
            raise SolverAssemblyError(
                "SELF_CONNECTED_MEMBER",
                f"Member '{member.id}' endpoints must be distinct.",
            )

        node_i = node_by_id[member.node_i]
        node_j = node_by_id[member.node_j]
        dx = node_j.x - node_i.x
        dy = node_j.y - node_i.y
        length = math.hypot(dx, dy)
        if not math.isfinite(length) or length == 0.0:
            raise SolverAssemblyError(
                "INVALID_GEOMETRY",
                f"Member '{member.id}' has coincident or numerically unusable endpoints.",
            )
        cx, cy = dx / length, dy / length
        column = column_by_id[f"member:{member.id}"]
        row_i = node_rows[member.node_i]
        row_j = node_rows[member.node_j]
        matrix[row_i, column] = cx
        matrix[row_i + 1, column] = cy
        matrix[row_j, column] = -cx
        matrix[row_j + 1, column] = -cy

    for support, (support_id, axes) in zip(model.supports, support_axes):
        row = node_rows[support.node]
        for axis in axes:
            column = column_by_id[f"reaction:{support_id}:{axis}"]
            matrix[row + (axis == "y"), column] = 1.0

    for load in model.loads:
        row = node_rows[load.node]
        rhs[row] -= load.fx
        rhs[row + 1] -= load.fy

    return EquilibriumSystem(
        coefficient_matrix=matrix,
        rhs=rhs,
        unknown_ids=tuple(unknown_ids),
        equation_ids=equation_ids,
        force_unit=model.units.force,
    )


def solve_equilibrium_system(system: EquilibriumSystem) -> TrussSolution:
    """Solve a square, full-rank, acceptably conditioned system with NumPy.

    Failure codes are ``INVALID_SYSTEM``, ``NONFINITE_SYSTEM``,
    ``NONSQUARE_SYSTEM``, ``RANK_DEFICIENT_SYSTEM``,
    ``ILL_CONDITIONED_SYSTEM``, ``NUMERICAL_DIAGNOSTIC_FAILED``,
    ``LINEAR_SOLVE_FAILED``, ``NONFINITE_SOLUTION``,
    ``NONFINITE_RESIDUAL``, ``RESIDUAL_TOO_LARGE``, and
    ``INVALID_UNKNOWN_IDENTIFIER``. These describe numerical/system
    properties only; they do not identify a physical mechanism or classify
    the truss.

    The residual limit is ``RESIDUAL_ABS_TOL + RESIDUAL_REL_TOL * scale``,
    where ``scale`` is the largest of ``max(abs(rhs))`` and
    ``max(abs(A) @ abs(x))``. The absolute floor is in the system's force unit.
    Rank uses the SVD tolerance documented by ``diagnose_equilibrium_system``.
    The relative residual tolerance and condition-number limit are float64
    heuristics; rescaling the matrix, unit system, or application can change
    their meaning.
    A small residual is a numerical check, not proof of structural stability.
    """
    diagnostics = diagnose_equilibrium_system(system)
    if diagnostics.category == "INVALID_SYSTEM":
        return _solve_failure(
            system,
            diagnostics.error_code or "INVALID_SYSTEM",
            diagnostics.message or "Equilibrium system is invalid.",
        )
    if not diagnostics.is_square:
        return _solve_failure(
            system,
            "NONSQUARE_SYSTEM",
            f"Direct solution requires a square matrix; received {diagnostics.equation_count}x{diagnostics.unknown_count}.",
            condition_number=diagnostics.condition_number,
        )
    if diagnostics.category == "SINGULAR_SQUARE":
        return _solve_failure(
            system,
            "RANK_DEFICIENT_SYSTEM",
            f"Matrix rank is {diagnostics.numerical_rank}; full rank {diagnostics.unknown_count} is required.",
            condition_number=diagnostics.condition_number,
        )
    if diagnostics.category == "NUMERICALLY_ILL_CONDITIONED":
        return _solve_failure(
            system,
            "ILL_CONDITIONED_SYSTEM",
            f"Condition number exceeds the supported limit of {MAX_CONDITION_NUMBER:.1e}.",
            condition_number=diagnostics.condition_number,
        )

    matrix = np.asarray(system.coefficient_matrix, dtype=np.float64)
    rhs = np.asarray(system.rhs, dtype=np.float64)
    condition_number = diagnostics.condition_number

    try:
        values = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        return _solve_failure(
            system,
            "LINEAR_SOLVE_FAILED",
            "NumPy could not solve the equilibrium system reliably.",
            condition_number=condition_number,
        )
    if not np.all(np.isfinite(values)):
        return _solve_failure(
            system,
            "NONFINITE_SOLUTION",
            "The direct solution contains non-finite values.",
            condition_number=condition_number,
        )

    with np.errstate(over="ignore", invalid="ignore"):
        residual = matrix @ values - rhs
        row_force_scale = np.abs(matrix) @ np.abs(values)
    if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(row_force_scale)):
        return _solve_failure(
            system,
            "NONFINITE_RESIDUAL",
            "Residual calculation produced non-finite values.",
            condition_number=condition_number,
        )
    max_residual = float(np.max(np.abs(residual)))
    scale = max(float(np.max(np.abs(rhs))), float(np.max(row_force_scale)))
    residual_tolerance = RESIDUAL_ABS_TOL + RESIDUAL_REL_TOL * scale
    if max_residual > residual_tolerance:
        return _solve_failure(
            system,
            "RESIDUAL_TOO_LARGE",
            f"Maximum equilibrium residual {max_residual:.6g} exceeds tolerance {residual_tolerance:.6g}.",
            condition_number=condition_number,
        )

    member_forces: dict[str, float] = {}
    support_reactions: dict[tuple[str, str], float] = {}
    for unknown_id, value in zip(system.unknown_ids, values):
        if unknown_id.startswith("member:"):
            member_forces[unknown_id[len("member:"):]] = float(value)
        elif unknown_id.startswith("reaction:"):
            reaction_id = unknown_id[len("reaction:"):]
            support_id, separator, axis = reaction_id.rpartition(":")
            if not separator or axis not in ("x", "y"):
                return _solve_failure(
                    system,
                    "INVALID_UNKNOWN_IDENTIFIER",
                    f"Unrecognized reaction unknown identifier '{unknown_id}'.",
                    condition_number=condition_number,
                )
            support_reactions[(support_id, axis)] = float(value)
        else:
            return _solve_failure(
                system,
                "INVALID_UNKNOWN_IDENTIFIER",
                f"Unrecognized unknown identifier '{unknown_id}'.",
                condition_number=condition_number,
            )

    return TrussSolution(
        status="SOLVED",
        unknown_values=tuple(float(value) for value in values),
        member_forces=member_forces,
        support_reactions=support_reactions,
        max_residual=max_residual,
        residual_tolerance=residual_tolerance,
        force_unit=system.force_unit,
        condition_number=condition_number,
    )


def _solve_failure(
    system: EquilibriumSystem,
    error_code: str,
    message: str,
    *,
    condition_number: float | None = None,
) -> TrussSolution:
    return TrussSolution(
        status="FAILED",
        unknown_values=None,
        member_forces=None,
        support_reactions=None,
        max_residual=None,
        residual_tolerance=None,
        force_unit=system.force_unit,
        error_code=error_code,
        message=message,
        condition_number=condition_number,
    )

"""
Generic mapping of physical pointwise displacement constraints to linear
constraints on generalized CSF-CUF end DOFs.

For one constrained physical displacement component at an end point (y,z),

    u_i(end,y,z) = sum_tau F_tau(y,z) q_{tau,i}^{end} = prescribed_value.

Therefore each physical pointwise boundary condition becomes one linear row

    A q = b

on the generalized CUF amplitudes associated with the boundary node.

This module performs only that mapping. It does not eliminate constraints,
assemble stiffness matrices, or solve a system.

No geometry shape, material law, benchmark, CUF basis family, or polynomial
order is hard-coded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np

from csf.utils.csf_cuf import CUFBasis
from csf_cuf_assembly import GlobalDOFLayout


_COMPONENT_INDEX = {
    "x": 0,
    "y": 1,
    "z": 2,
}


@dataclass(frozen=True)
class PointwiseDisplacementConstraint:
    """
    One physical displacement prescription on a longitudinal end section.

    Coordinates y,z are transverse solver coordinates.
    """

    end: str
    y: float
    z: float
    component: str
    value: float = 0.0


@dataclass(frozen=True)
class LinearConstraintSystem:
    """
    Linear generalized-DOF constraints

        matrix @ q = rhs

    written directly in the full global DOF numbering.
    """

    matrix: np.ndarray
    rhs: np.ndarray
    constraints: Tuple[PointwiseDisplacementConstraint, ...]

    def __post_init__(self) -> None:
        if self.matrix.ndim != 2:
            raise ValueError("constraint matrix must be two-dimensional")

        if self.rhs.shape != (self.matrix.shape[0],):
            raise ValueError(
                "constraint rhs is inconsistent with constraint matrix"
            )

        if len(self.constraints) != self.matrix.shape[0]:
            raise ValueError(
                "constraint metadata count is inconsistent with matrix rows"
            )


class PointwiseBoundaryConstraintMapper:
    """
    Map physical displacement constraints to generalized CUF linear equations.
    """

    def __init__(
        self,
        *,
        basis: CUFBasis,
        dof_layout: GlobalDOFLayout,
    ) -> None:
        if not isinstance(basis, CUFBasis):
            raise TypeError("basis must implement CUFBasis")

        if not isinstance(dof_layout, GlobalDOFLayout):
            raise TypeError(
                "dof_layout must be a GlobalDOFLayout"
            )

        if basis.size != dof_layout.basis_size:
            raise ValueError(
                "basis size and DOF layout basis size differ"
            )

        self.basis = basis
        self.dof_layout = dof_layout

    def map(
        self,
        constraints: Iterable[PointwiseDisplacementConstraint],
    ) -> LinearConstraintSystem:
        constraints = tuple(constraints)

        A = np.zeros(
            (
                len(constraints),
                self.dof_layout.total_dofs,
            ),
            dtype=float,
        )

        b = np.zeros(
            len(constraints),
            dtype=float,
        )

        for row, constraint in enumerate(constraints):
            node = self._end_node(constraint.end)

            if constraint.component not in _COMPONENT_INDEX:
                raise ValueError(
                    "component must be 'x', 'y', or 'z'"
                )

            component = _COMPONENT_INDEX[
                constraint.component
            ]

            if not np.isfinite(constraint.y):
                raise ValueError("constraint y must be finite")

            if not np.isfinite(constraint.z):
                raise ValueError("constraint z must be finite")

            if not np.isfinite(constraint.value):
                raise ValueError(
                    "constraint prescribed value must be finite"
                )

            for tau in range(
                1,
                self.basis.size + 1,
            ):
                coefficient = float(
                    self.basis.value(
                        tau,
                        float(constraint.y),
                        float(constraint.z),
                    )
                )

                dof = self.dof_layout.index(
                    node=node,
                    tau=tau,
                    component=component,
                )

                A[row, dof] = coefficient

            b[row] = float(constraint.value)

        return LinearConstraintSystem(
            matrix=A,
            rhs=b,
            constraints=constraints,
        )

    def _end_node(
        self,
        end: str,
    ) -> int:
        if end == "start":
            return 0

        if end == "end":
            return self.dof_layout.number_of_nodes - 1

        raise ValueError(
            "end must be 'start' or 'end'"
        )

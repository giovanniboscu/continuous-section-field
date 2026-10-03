"""End transverse supports plus a physical axial point anchor."""

from __future__ import annotations

from typing import Any

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


class TransverseSupportedPointAnchorConstraints:
    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
        del longitudinal_integrator

        layout = assembled.dof_layout
        row_count = 4 * int(basis.size) + 1
        matrix = np.zeros((row_count, layout.total_dofs), dtype=float)
        rhs = np.zeros(row_count, dtype=float)
        row = 0

        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, int(basis.size) + 1):
                    matrix[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=component,
                        ),
                    ] = 1.0
                    row += 1

        axial_anchor_factors = np.asarray(
            [
                basis.value(
                    tau,
                    0.0,
                    0.0,
                    x=float(mesh.x_start),
                )
                for tau in range(1, int(basis.size) + 1)
            ],
            dtype=float,
        )

        start_node = 0
        for tau, factor in enumerate(axial_anchor_factors, start=1):
            matrix[
                row,
                layout.index(
                    node=start_node,
                    tau=tau,
                    component=0,
                ),
            ] = float(factor)

        row += 1
        if row != row_count:
            raise RuntimeError("internal constraint-row count mismatch")

        return LinearConstraintSystem(
            matrix=matrix,
            rhs=rhs,
            constraints=tuple(None for _ in range(row_count)),
        )


def build_problem(problem_type: str, options: dict):
    del problem_type, options
    return TransverseSupportedPointAnchorConstraints()


__all__ = ("TransverseSupportedPointAnchorConstraints", "build_problem")

"""Perfect clamp of all CUF amplitudes at both longitudinal ends."""

from __future__ import annotations

from typing import Any

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


class FullClampConstraints:
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
        n_tau = int(basis.size)
        row_count = 6 * n_tau
        matrix = np.zeros((row_count, layout.total_dofs), dtype=float)
        rhs = np.zeros(row_count, dtype=float)
        row = 0

        for node in (0, mesh.number_of_nodes - 1):
            for component in (0, 1, 2):
                for tau in range(1, n_tau + 1):
                    matrix[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=component,
                        ),
                    ] = 1.0
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
    return FullClampConstraints()


__all__ = ("FullClampConstraints", "build_problem")

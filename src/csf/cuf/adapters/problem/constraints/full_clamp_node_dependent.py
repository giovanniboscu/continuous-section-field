"""Perfect clamp using the active transverse basis size of each end node."""

from __future__ import annotations

from typing import Any

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


class FullClampNodeDependentConstraints:
    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
        del basis, longitudinal_integrator

        layout = assembled.dof_layout
        end_nodes = (0, mesh.number_of_nodes - 1)
        end_basis_sizes = tuple(
            int(layout.basis_size_at_node(node))
            for node in end_nodes
        )
        row_count = 3 * sum(end_basis_sizes)
        matrix = np.zeros((row_count, layout.total_dofs), dtype=float)
        rhs = np.zeros(row_count, dtype=float)

        row = 0
        for node, node_basis_size in zip(end_nodes, end_basis_sizes):
            for component in (0, 1, 2):
                for tau in range(1, node_basis_size + 1):
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
    return FullClampNodeDependentConstraints()


__all__ = ("FullClampNodeDependentConstraints", "build_problem")

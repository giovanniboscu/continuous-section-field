"""End transverse supports plus the historical integrated axial constraint."""

from __future__ import annotations

from typing import Any

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


class TransverseSupportedIntegratedAxialConstraints:
    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
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

        length = float(mesh.x_end - mesh.x_start)

        for element in mesh.elements:
            for tau in range(1, int(basis.size) + 1):
                local = longitudinal_integrator.integrate_linear(
                    element=element,
                    load=lambda x, tau=tau: float(
                        basis.value(
                            tau,
                            0.0,
                            0.0,
                            x=float(x),
                        )
                    ) / length,
                )

                for a, node in enumerate(element.node_ids):
                    matrix[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=0,
                        ),
                    ] += float(local[a])

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
    return TransverseSupportedIntegratedAxialConstraints()


__all__ = ("TransverseSupportedIntegratedAxialConstraints", "build_problem")

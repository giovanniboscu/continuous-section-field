"""Reusable full clamp of the complete CUF start section.

All generalized CUF displacement amplitudes are set to zero at the first
longitudinal node for all three physical displacement components.

This imposes:

    u_x = 0
    u_y = 0
    u_z = 0

over the complete reconstructed start section.
"""

from __future__ import annotations

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


class FullStartSectionClamp:
    """Clamp the entire start section and leave all other sections free."""

    def build_constraints(
        self,
        *,
        assembled,
        mesh,
        basis,
        longitudinal_integrator,
    ):
        """Build homogeneous constraints for the complete start section."""

        del mesh, longitudinal_integrator

        layout = assembled.dof_layout
        basis_size = int(basis.size)

        row_count = 3 * basis_size
        matrix = np.zeros(
            (row_count, layout.total_dofs),
            dtype=float,
        )
        rhs = np.zeros(row_count, dtype=float)

        row = 0
        start_node = 0

        for component in (0, 1, 2):
            for tau in range(1, basis_size + 1):
                matrix[
                    row,
                    layout.index(
                        node=start_node,
                        tau=tau,
                        component=component,
                    ),
                ] = 1.0
                row += 1

        return LinearConstraintSystem(
            matrix=matrix,
            rhs=rhs,
            constraints=tuple(None for _ in range(row_count)),
        )


__all__ = ("FullStartSectionClamp",)

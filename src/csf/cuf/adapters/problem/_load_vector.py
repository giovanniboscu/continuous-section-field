"""Adapter-side helpers for building global load vectors.

These helpers use only generic numerical services supplied by the CUF core.
The core does not import or interpret any physical load type.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


def assemble_distributed_load_vector(
    *,
    mesh,
    dof_layout,
    longitudinal_integrator,
    component: str,
    fields: Iterable,
) -> np.ndarray:
    """Assemble adapter-defined scalar longitudinal fields into one global vector."""

    component_index = {
        "x": 0,
        "y": 1,
        "z": 2,
    }
    component_number = component_index[component]

    vector = np.zeros(dof_layout.total_dofs, dtype=float)

    for tau, field in enumerate(tuple(fields), start=1):
        if tau > dof_layout.basis_size:
            raise ValueError(
                f"load tau={tau} exceeds "
                f"maximum basis size {dof_layout.basis_size}"
            )

        for element in mesh.elements:
            if tau > dof_layout.basis_size_at_node(element.node_ids[0]):
                continue

            local_vector = longitudinal_integrator.integrate_linear(
                element=element,
                load=field.value,
            )

            expected_size = len(element.node_ids)
            if local_vector.shape != (expected_size,):
                raise ValueError("local load vector has inconsistent size")

            for a, global_node in enumerate(element.node_ids):
                global_dof = dof_layout.index(
                    node=global_node,
                    tau=tau,
                    component=component_number,
                )
                vector[global_dof] += float(local_vector[a])

    return vector

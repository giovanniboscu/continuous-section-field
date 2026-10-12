"""Reusable concentrated point force in the CUF global-z direction.

v4: Version label update only; no functional changes from v3.
v3: Add physical load, FE interpolation and assembled-vector diagnostics.
    Keep the v2 projection algorithm and public interfaces unchanged.
v2: Assemble at arbitrary longitudinal positions using FE shape functions;
    preserve the YAML interface and the global-z load convention.

The force is applied at one physical point:

    (x, y, z)

where:

    x       longitudinal CUF coordinate
    y, z    CUF cross-section coordinates

The longitudinal load is projected onto the FE shape functions of the
containing element, without requiring coincidence with a longitudinal node.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np


def _finite(value: Any, name: str) -> float:
    """Convert one YAML scalar to a finite float."""

    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


class PointForceGlobalZPoint:
    """Concentrated force acting in the CUF global-z direction."""

    def __init__(
        self,
        *,
        amplitude: float,
        x: float,
        y: float,
        z: float,
    ) -> None:
        self.amplitude = float(amplitude)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    @classmethod
    def from_mapping(cls, force: Mapping[str, Any]):
        """Create the load from a problem.force YAML mapping."""

        required = ("amplitude", "x", "y", "z")
        missing = [key for key in required if key not in force]
        if missing:
            raise ValueError(
                "problem.force missing: " + ", ".join(missing)
            )

        unsupported = sorted(
            str(key) for key in force if key not in required
        )
        if unsupported:
            raise ValueError(
                "problem.force contains unsupported option(s): "
                + ", ".join(unsupported)
            )

        return cls(
            amplitude=_finite(
                force["amplitude"],
                "problem.force.amplitude",
            ),
            x=_finite(force["x"], "problem.force.x"),
            y=_finite(force["y"], "problem.force.y"),
            z=_finite(force["z"], "problem.force.z"),
        )

    def build_load_vector(
        self,
        *,
        section_provider,
        basis,
        mesh,
        dof_layout,
        longitudinal_integrator,
        x0,
        x1,
    ):
        """Project a point force through longitudinal and transverse CUF bases."""

        del section_provider, longitudinal_integrator

        x_start = float(x0)
        x_end = float(x1)
        scale = max(1.0, abs(x_start), abs(x_end), abs(self.x))
        tol = 1.0e-12 * scale
        if self.x < x_start - tol or self.x > x_end + tol:
            raise ValueError(
                f"problem.force.x={self.x} lies outside the longitudinal "
                f"domain [{x_start}, {x_end}]"
            )

        # Choose one element at shared boundaries; the FE interpolant is
        # continuous there, so the load is assembled exactly once.
        selected = None
        for element in mesh.elements:
            left = float(element.x_start)
            right = float(element.x_end)
            if left - tol <= self.x <= right + tol:
                selected = element
                break
        if selected is None:
            raise ValueError(
                f"could not locate longitudinal FE element for x={self.x}"
            )

        # Snap only floating-point boundary roundoff, not arbitrary positions.
        point_x = min(max(self.x, float(selected.x_start)),
                      float(selected.x_end))
        xi = (2.0 * point_x - float(selected.x_start)
              - float(selected.x_end)) / float(selected.length)
        shapes = np.asarray(selected.shape_values(xi), dtype=float)
        if len(shapes) != len(selected.node_ids):
            raise ValueError("longitudinal FE shape/node size mismatch")

        load_vector = np.zeros(dof_layout.total_dofs, dtype=float)
        skipped_count = 0
        skipped_abs = 0.0
        for tau in range(1, int(basis.size) + 1):
            basis_value = float(basis.value(
                tau, self.y, self.z, x=self.x
            ))
            generalized_force = self.amplitude * basis_value
            for local_index, node in enumerate(selected.node_ids):
                coefficient = float(shapes[local_index])
                if coefficient == 0.0:
                    continue
                if tau > dof_layout.basis_size_at_node(node):
                    skipped_count += 1
                    skipped_abs += abs(coefficient * generalized_force)
                    continue
                dof = dof_layout.index(
                    node=node, tau=tau, component=2
                )
                load_vector[dof] += coefficient * generalized_force

        # Diagnostic only: never alter the assembled load or its indexing.
        # The generalized vector is NOT a physical nodal force vector, so its
        # coefficient sum/norm must not be interpreted as a force resultant.
        physical_force = np.array([0.0, 0.0, self.amplitude], dtype=float)
        physical_moment = np.cross(
            np.array([self.x, self.y, self.z], dtype=float), physical_force
        )
        active = np.flatnonzero(load_vector)
        print("[CUF point load] physical force (N): "
              f"({physical_force[0]:.12g}, {physical_force[1]:.12g}, {physical_force[2]:.12g})")
        print("[CUF point load] application point (mm): "
              f"({self.x:.12g}, {self.y:.12g}, {self.z:.12g})")
        print("[CUF point load] physical moment about origin (N mm): "
              f"({physical_moment[0]:.12g}, {physical_moment[1]:.12g}, {physical_moment[2]:.12g})")
        print("[CUF point load] longitudinal FE: "
              f"[{float(selected.x_start):.12g}, {float(selected.x_end):.12g}], "
              f"xi={xi:.12g}, local_nodes={len(selected.node_ids)}")
        print("[CUF point load] shape checks: "
              f"sum(N)={float(np.sum(shapes)):.12g}, "
              f"min(N)={float(np.min(shapes)):.12g}, "
              f"max(N)={float(np.max(shapes)):.12g}")
        print("[CUF point load] generalized vector: "
              f"total_dofs={load_vector.size}, nonzero={active.size}, "
              f"norm2={float(np.linalg.norm(load_vector)):.12g}, "
              f"max_abs={float(np.max(np.abs(load_vector))):.12g}")
        print("[CUF point load] omitted contributions (unavailable transverse DOFs): "
              f"count={skipped_count}, sum_abs={skipped_abs:.12g}")

        return load_vector, self

    def tracked_points(self, section_provider, x: float):
        """Expose the physical application point."""

        del section_provider, x
        return (
            ("point_force_global_z_point", self.y, self.z),
        )


__all__ = ("PointForceGlobalZPoint",)

"""Reusable concentrated point force in the CUF global-z direction.

The force is applied at one physical point:

    (x, y, z)

where:

    x       longitudinal CUF coordinate
    y, z    CUF cross-section coordinates

The longitudinal coordinate must coincide with one longitudinal FE node.
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


class PointForceGlobalZ:
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
        """Assemble the concentrated global-z force at one FE node."""

        del section_provider, longitudinal_integrator, x0, x1

        nodes = np.asarray(mesh.nodes, dtype=float)
        scale = max(
            1.0,
            abs(self.x),
            float(np.max(np.abs(nodes))),
        )

        matches = np.flatnonzero(
            np.isclose(
                nodes,
                self.x,
                rtol=0.0,
                atol=1.0e-10 * scale,
            )
        )

        if len(matches) != 1:
            raise ValueError(
                "problem.force.x must coincide with exactly one "
                f"longitudinal FE node; x={self.x}, matches={len(matches)}"
            )

        node = int(matches[0])
        load_vector = np.zeros(
            dof_layout.total_dofs,
            dtype=float,
        )

        for tau in range(1, int(basis.size) + 1):
            basis_value = float(
                basis.value(
                    tau,
                    self.y,
                    self.z,
                    x=self.x,
                )
            )

            load_vector[
                dof_layout.index(
                    node=node,
                    tau=tau,
                    component=2,
                )
            ] += self.amplitude * basis_value

        return load_vector, self

    def tracked_points(self, section_provider, x: float):
        """Expose the physical application point."""

        del section_provider, x
        return (
            ("point_force_global_z", self.y, self.z),
        )


__all__ = ("PointForceGlobalZ",)

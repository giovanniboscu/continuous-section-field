"""PointForceGlobalZArea v3 - surface rectangle in the CUF x-y plane.

Changelog v3:
- Integrate a force resultant on the physical x-y surface at constant z.
- Interpret width along longitudinal x and height along transverse y.
- Integrate across longitudinal FE element boundaries using FE shape functions.
- Validate that the patch lies on a CSF polygon boundary, without a node constraint.
- Preserve class, YAML keys, build_load_vector and tracked_points interfaces.

YAML: x/y/z are patch-centroid coordinates; width (x) and height (y) in mm;
fx/fy/fz are total force resultants in N, not tractions in N/mm^2.
"""
from __future__ import annotations

import math
from typing import Any, Mapping
import numpy as np


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _horizontal_boundary_covers(vertices: np.ndarray, y0: float, y1: float,
                                z: float, tol: float) -> bool:
    """Check that the complete y interval is covered by horizontal edges at z."""
    intervals = []
    for index in range(len(vertices)):
        ya, za = vertices[index]
        yb, zb = vertices[(index + 1) % len(vertices)]
        if abs(za - z) <= tol and abs(zb - z) <= tol:
            intervals.append((min(ya, yb), max(ya, yb)))
    position = y0
    for left, right in sorted(intervals):
        if left <= position + tol and right > position:
            position = max(position, right)
        if position >= y1 - tol:
            return True
    return False


class PointForceGlobalZArea:
    """Uniform total vector force on a rectangular physical x-y boundary patch."""

    def __init__(self, *, x: float, y: float, z: float,
                 width: float, height: float, fx: float = 0.0,
                 fy: float = 0.0, fz: float = 0.0) -> None:
        self.x = _finite(x, "problem.force.x")
        self.y = _finite(y, "problem.force.y")
        self.z = _finite(z, "problem.force.z")
        self.width = _finite(width, "problem.force.width")
        self.height = _finite(height, "problem.force.height")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("problem.force.width and height must be positive")
        self.area = self.width * self.height
        self.force = np.array([_finite(fx, "problem.force.fx"),
                               _finite(fy, "problem.force.fy"),
                               _finite(fz, "problem.force.fz")], dtype=float)
        if not np.any(self.force):
            raise ValueError("at least one of fx/fy/fz must be nonzero")

    @classmethod
    def from_mapping(cls, force: Mapping[str, Any]):
        required = ("x", "y", "z", "width", "height")
        missing = [key for key in required if key not in force]
        if missing:
            raise ValueError("problem.force missing: " + ", ".join(missing))
        allowed = (*required, "fx", "fy", "fz")
        unknown = sorted(str(key) for key in force if key not in allowed)
        if unknown:
            raise ValueError("problem.force contains unsupported option(s): " + ", ".join(unknown))
        return cls(**{key: _finite(force[key], f"problem.force.{key}")
                     for key in allowed if key in force})

    def _validate_surface(self, section_provider, stations: list[float]) -> None:
        """Verify the patch y-interval lies on the constant-z CSF boundary."""
        domains_fn = getattr(section_provider, "domains", None)
        if not callable(domains_fn):
            raise TypeError("section_provider must expose domains(x)")
        y0 = self.y - self.height / 2
        y1 = self.y + self.height / 2
        for x in stations:
            domains = tuple(domains_fn(float(x)))
            intervals = []
            scale = max(1.0, abs(y0), abs(y1), abs(self.z))
            tol = 1e-9 * scale
            for domain in domains:
                vertices = np.asarray(domain.vertices, dtype=float)
                if (vertices.ndim != 2 or vertices.shape[1] != 2
                        or len(vertices) < 3 or not np.isfinite(vertices).all()):
                    raise ValueError(f"invalid CSF polygon geometry at x={x}")
                if getattr(domain, "excluded_vertices", ()):
                    raise ValueError("CSF domains with excluded child regions cannot be verified as exterior surface")
                weightabs = getattr(domain, "weightabs", None)
                if weightabs is not None and float(weightabs) <= 0:
                    continue
                for index in range(len(vertices)):
                    ya, za = vertices[index]
                    yb, zb = vertices[(index + 1) % len(vertices)]
                    if abs(za - self.z) <= tol and abs(zb - self.z) <= tol:
                        intervals.append((min(ya, yb), max(ya, yb)))
            position = y0
            for left, right in sorted(intervals):
                if left <= position + tol and right > position:
                    position = max(position, right)
                if position >= y1 - tol:
                    break
            if position < y1 - tol:
                raise ValueError(
                    f"force patch is not on the specified CSF horizontal boundary "
                    f"at x={x}, z={self.z}, y=[{y0},{y1}]"
                )

    def build_load_vector(self, *, section_provider, basis, mesh, dof_layout,
                          longitudinal_integrator, x0, x1):
        """Integrate P/A * N_i(x) * F_tau(y,z,x) over the physical patch."""
        del longitudinal_integrator
        left = self.x - self.width / 2
        right = self.x + self.width / 2
        scale = max(1.0, abs(float(x0)), abs(float(x1)), abs(left), abs(right))
        tol = 1e-12 * scale
        if left < float(x0) - tol or right > float(x1) + tol:
            raise ValueError(f"patch x interval [{left}, {right}] outside [{x0}, {x1}]")

        segments = []
        for element in mesh.elements:
            a = max(left, float(element.x_start))
            b = min(right, float(element.x_end))
            if b > a + tol:
                segments.append((element, a, b))
        if not segments:
            raise ValueError("no longitudinal FE element intersects force patch")
        length = sum(b - a for _, a, b in segments)
        if not math.isclose(length, self.width, rel_tol=1e-10, abs_tol=tol):
            raise ValueError("FE element partition does not cover the full force patch")

        # Quadrature in physical x and y, split at every longitudinal FE boundary.
        order = max(4, min(64, int(math.ceil(math.sqrt(int(basis.size)))) + 3))
        gp, gw = np.polynomial.legendre.leggauss(order)
        y_half = self.height / 2
        y_samples = [(self.y + y_half * float(t), y_half * float(w))
                     for t, w in zip(gp, gw)]
        x_samples = []
        for element, a, b in segments:
            half = (b - a) / 2
            midpoint = (a + b) / 2
            x_samples.extend(midpoint + half * float(t) for t in gp)
            x_samples.extend((a, b))
        self._validate_surface(section_provider, sorted(set(x_samples)))

        vector = np.zeros(dof_layout.total_dofs, dtype=float)
        for element, a, b in segments:
            half = (b - a) / 2
            midpoint = (a + b) / 2
            for t, wx in zip(gp, gw):
                xx = midpoint + half * float(t)
                xi = (2 * xx - float(element.x_start) - float(element.x_end)) / float(element.length)
                shape = np.asarray(element.shape_values(xi), dtype=float)
                if len(shape) != len(element.node_ids):
                    raise ValueError("longitudinal FE shape/node size mismatch")
                for yy, dy in y_samples:
                    weight = half * float(wx) * dy / self.area
                    for tau in range(1, int(basis.size) + 1):
                        transverse = float(basis.value(tau, yy, self.z, x=xx))
                        for local_i, node in enumerate(element.node_ids):
                            coefficient = weight * transverse * float(shape[local_i])
                            if coefficient == 0:
                                continue
                            if tau > dof_layout.basis_size_at_node(node):
                                continue
                            for component, force in enumerate(self.force):
                                if force:
                                    vector[dof_layout.index(node=node, tau=tau,
                                                            component=component)] += coefficient * float(force)
        return vector, self

    def tracked_points(self, section_provider, x: float):
        del section_provider, x
        return (("point_force_global_z_area", self.y, self.z),)


__all__ = ("PointForceGlobalZArea",)

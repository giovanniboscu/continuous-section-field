# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Section-integration numerical utilities used by the CUF solver."""

from __future__ import annotations

import numpy as np

from csf.cuf.core.integration import SectionIntegrator


class FixedGaussPolygonIntegrator(SectionIntegrator):
    """Fixed Gauss integration over net homogeneous polygonal domains.

    Topology and material ownership are resolved upstream.  This class sees
    only one outer polygon, its direct geometric exclusions and ``weightabs``.
    It converts that net geometry into physical Gauss points and area weights.
    """

    def __init__(self, order: int):
        if not isinstance(order, int) or order < 2:
            raise ValueError("section Gauss order must be an integer >= 2")
        self.order = int(order)
        self.points, self.weights = np.polynomial.legendre.leggauss(self.order)

    @staticmethod
    def _z_intervals_at_y(vertices, y: float):
        intersections = []
        count = len(vertices)
        for i in range(count):
            y0, z0 = vertices[i]
            y1, z1 = vertices[(i + 1) % count]
            if y0 == y1:
                continue
            lower, upper = min(y0, y1), max(y0, y1)
            if not (lower <= y < upper):
                continue
            t = (y - y0) / (y1 - y0)
            intersections.append(float(z0 + t * (z1 - z0)))
        intersections.sort()
        if len(intersections) % 2 != 0:
            raise ValueError("polygon slicing produced an odd number of intersections")
        return tuple(
            (intersections[i], intersections[i + 1])
            for i in range(0, len(intersections), 2)
            if intersections[i + 1] > intersections[i]
        )

    @staticmethod
    def _y_subintervals(domain):
        # A child vertex can change the number or shape of occupied z
        # intervals.  Its y coordinate must therefore be a slicing breakpoint
        # just like a vertex of the outer polygon.
        rings = (domain.vertices, *domain.excluded_vertices)
        values = sorted(
            set(float(point[0]) for ring in rings for point in ring)
        )
        if len(values) < 2:
            raise ValueError("polygon has zero extent in y")
        return tuple((a, b) for a, b in zip(values[:-1], values[1:]) if b > a)

    @staticmethod
    def _merge_intervals(intervals):
        """Return the union of sorted one-dimensional intervals."""
        ordered = sorted(
            (float(start), float(end))
            for start, end in intervals
            if end > start
        )
        if not ordered:
            return ()
        merged = [ordered[0]]
        for start, end in ordered[1:]:
            previous_start, previous_end = merged[-1]
            if start <= previous_end:
                merged[-1] = (previous_start, max(previous_end, end))
            else:
                merged.append((start, end))
        return tuple(merged)

    @classmethod
    def _net_z_intervals_at_y(cls, domain, y: float):
        """Slice outer polygon minus all direct-child polygons at one y."""
        occupied = cls._merge_intervals(
            cls._z_intervals_at_y(domain.vertices, y)
        )
        excluded = cls._merge_intervals(
            interval
            for child_vertices in domain.excluded_vertices
            for interval in cls._z_intervals_at_y(child_vertices, y)
        )
        if not excluded:
            return occupied

        net = []
        for occupied_start, occupied_end in occupied:
            fragments = [(occupied_start, occupied_end)]
            for excluded_start, excluded_end in excluded:
                next_fragments = []
                for fragment_start, fragment_end in fragments:
                    if excluded_end <= fragment_start or excluded_start >= fragment_end:
                        next_fragments.append((fragment_start, fragment_end))
                        continue
                    if excluded_start > fragment_start:
                        next_fragments.append((fragment_start, excluded_start))
                    if excluded_end < fragment_end:
                        next_fragments.append((excluded_end, fragment_end))
                fragments = next_fragments
                if not fragments:
                    break
            net.extend(fragments)
        return tuple(
            (start, end) for start, end in net if end > start
        )

    def quadrature_points(self, domain):
        """
        Return the fixed-Gauss polygon rule as physical (y, z, weight) arrays.

        The point ordering and weights are exactly those used by ``integrate``
        and ``integrate_vector``.  Exposing the rule allows the sectional layer
        to evaluate many CUF coefficient families by dense matrix algebra while
        preserving the same geometric quadrature.
        """

        # A zero absolute weight denotes a void domain.  Its geometry was
        # already removed from its parent, and it must not be reintroduced as
        # an independently integrated sub-domain.
        if domain.weightabs is not None and float(domain.weightabs) == 0.0:
            empty = np.asarray([], dtype=float)
            return empty.copy(), empty.copy(), empty.copy()

        y_points = []
        z_points = []
        quadrature_weights = []

        for y0, y1 in self._y_subintervals(domain):
            y_mid = 0.5 * (y0 + y1)
            y_jac = 0.5 * (y1 - y0)

            for xi_y, w_y in zip(self.points, self.weights):
                y = y_mid + y_jac * float(xi_y)

                for z0, z1 in self._net_z_intervals_at_y(domain, y):
                    z_mid = 0.5 * (z0 + z1)
                    z_jac = 0.5 * (z1 - z0)

                    for xi_z, w_z in zip(self.points, self.weights):
                        z = z_mid + z_jac * float(xi_z)

                        y_points.append(float(y))
                        z_points.append(float(z))
                        quadrature_weights.append(
                            float(w_y)
                            * float(w_z)
                            * y_jac
                            * z_jac
                        )

        return (
            np.asarray(y_points, dtype=float),
            np.asarray(z_points, dtype=float),
            np.asarray(quadrature_weights, dtype=float),
        )

    def integrate(self, domain, integrand):
        if domain.weightabs is not None and float(domain.weightabs) == 0.0:
            return 0.0
        total = 0.0
        for y0, y1 in self._y_subintervals(domain):
            y_mid, y_jac = 0.5 * (y0 + y1), 0.5 * (y1 - y0)
            for xi_y, w_y in zip(self.points, self.weights):
                y = y_mid + y_jac * float(xi_y)
                for z0, z1 in self._net_z_intervals_at_y(domain, y):
                    z_mid, z_jac = 0.5 * (z0 + z1), 0.5 * (z1 - z0)
                    for xi_z, w_z in zip(self.points, self.weights):
                        z = z_mid + z_jac * float(xi_z)
                        total += (
                            float(w_y) * float(w_z) * y_jac * z_jac
                            * float(integrand(float(y), float(z)))
                        )
        return float(total)

    def integrate_vector(self, domain, integrand, *, size: int):
        if not isinstance(size, int) or size < 1:
            raise ValueError("size must be a positive integer")
        if domain.weightabs is not None and float(domain.weightabs) == 0.0:
            return np.zeros(size, dtype=float)
        total = np.zeros(size, dtype=float)
        for y0, y1 in self._y_subintervals(domain):
            y_mid, y_jac = 0.5 * (y0 + y1), 0.5 * (y1 - y0)
            for xi_y, w_y in zip(self.points, self.weights):
                y = y_mid + y_jac * float(xi_y)
                for z0, z1 in self._net_z_intervals_at_y(domain, y):
                    z_mid, z_jac = 0.5 * (z0 + z1), 0.5 * (z1 - z0)
                    for xi_z, w_z in zip(self.points, self.weights):
                        z = z_mid + z_jac * float(xi_z)
                        value = np.asarray(integrand(float(y), float(z)), dtype=float)
                        if value.shape != (size,):
                            raise ValueError(
                                f"vector integrand returned {value.shape}; expected {(size,)}"
                            )
                        total += float(w_y) * float(w_z) * y_jac * z_jac * value
        if not np.all(np.isfinite(total)):
            raise RuntimeError("fixed polygon quadrature returned non-finite values")
        return total

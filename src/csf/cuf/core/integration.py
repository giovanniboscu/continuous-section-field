# Version: CSF-CUF net homogeneous domain slicer v19 - 2026-08-27
"""
Generic transverse section integration for the CSF-CUF bridge.

This module contains only the numerical integration layer:
- SectionIntegrator
- AdaptivePolygonIntegrator

No constitutive, CUF-basis, longitudinal, load, or benchmark-specific
assumption is introduced here.
"""

from abc import ABC, abstractmethod
from typing import Callable, Tuple

import numpy as np
from scipy.integrate import quad, quad_vec

from .section import PolygonDomain


# =============================================================================
# Section integration API
# =============================================================================

class SectionIntegrator(ABC):
    """
    Generic numerical integration backend over a transverse CSF domain.

    The bridge does not assume a particular polygon shape, material law,
    CUF basis, or quadrature strategy.  A SectionIntegrator receives the
    current domain and a scalar integrand and returns the domain integral.
    """

    @abstractmethod
    def integrate(
        self,
        domain: PolygonDomain,
        integrand: Callable[[float, float], float],
    ) -> float:
        """Return the integral of ``integrand(y,z)`` over ``domain``."""
        raise NotImplementedError


class AdaptivePolygonIntegrator(SectionIntegrator):
    """
    Adaptive integration over a generic simple polygon.

    The polygon is sliced along the first transverse coordinate.  At each
    slice, the even-odd rule determines all interior intervals in the second
    transverse coordinate.  No rectangular or prismatic specialization is
    used.

    Tolerances are numerical solver options, not physical assumptions.
    """

    def __init__(
        self,
        *,
        epsabs: float = 1.0e-8,
        epsrel: float = 1.0e-9,
        inner_limit: int = 100,
        outer_limit: int = 200,
    ) -> None:
        if epsabs <= 0.0:
            raise ValueError("epsabs must be positive")
        if epsrel <= 0.0:
            raise ValueError("epsrel must be positive")
        if inner_limit <= 0:
            raise ValueError("inner_limit must be positive")
        if outer_limit <= 0:
            raise ValueError("outer_limit must be positive")

        self.epsabs = float(epsabs)
        self.epsrel = float(epsrel)
        self.inner_limit = int(inner_limit)
        self.outer_limit = int(outer_limit)

    def integrate(
        self,
        domain: PolygonDomain,
        integrand: Callable[[float, float], float],
    ) -> float:
        if domain.weightabs is not None and float(domain.weightabs) == 0.0:
            return 0.0

        vertices = domain.vertices

        if len(vertices) < 3:
            raise ValueError("polygon must contain at least three vertices")

        rings = (vertices, *domain.excluded_vertices)
        y_values = [point[0] for ring in rings for point in ring]
        y_min = min(y_values)
        y_max = max(y_values)

        if y_max <= y_min:
            raise ValueError("polygon has zero extent in y")

        breakpoints = sorted(set(y_values))
        interior_breakpoints = [
            value
            for value in breakpoints
            if y_min < value < y_max
        ]

        def integrate_at_y(y: float) -> float:
            subtotal = 0.0

            for z0, z1 in self._net_z_intervals_at_y(domain, y):
                value = self._quad_interval(
                    lambda z: integrand(y, z),
                    z0,
                    z1,
                    limit=self.inner_limit,
                )
                subtotal += value

            return subtotal

        # Integrate piecewise between polygon-vertex ordinates.  This avoids
        # asking QUADPACK to discover changes in the slice topology itself.
        bounds = [y_min, *interior_breakpoints, y_max]
        result = 0.0

        for left, right in zip(bounds[:-1], bounds[1:]):
            if right <= left:
                continue

            value = self._quad_interval(
                integrate_at_y,
                left,
                right,
                limit=self.outer_limit,
            )
            result += value

        return float(result)

    def integrate_vector(
        self,
        domain: PolygonDomain,
        integrand,
        *,
        size: int,
    ) -> np.ndarray:
        """
        Integrate a vector-valued function over a generic polygon.

        The polygon slicing is identical to ``integrate``.  The difference is
        that all requested sectional coefficients are accumulated in one
        adaptive traversal of the domain.

        This method is purely numerical.  It introduces no assumption on
        geometry, material, CUF basis, or longitudinal variation.
        """

        if not isinstance(size, int) or size < 1:
            raise ValueError("size must be a positive integer")
        if domain.weightabs is not None and float(domain.weightabs) == 0.0:
            return np.zeros(size, dtype=float)

        vertices = domain.vertices

        if len(vertices) < 3:
            raise ValueError("polygon must contain at least three vertices")

        rings = (vertices, *domain.excluded_vertices)
        y_values = [point[0] for ring in rings for point in ring]
        y_min = min(y_values)
        y_max = max(y_values)

        if y_max <= y_min:
            raise ValueError("polygon has zero extent in y")

        breakpoints = sorted(set(y_values))
        interior_breakpoints = [
            value
            for value in breakpoints
            if y_min < value < y_max
        ]

        zero = np.zeros(size, dtype=float)

        def integrate_at_y(y: float) -> np.ndarray:
            subtotal = zero.copy()

            for z0, z1 in self._net_z_intervals_at_y(domain, y):
                value, _ = quad_vec(
                    lambda z: np.asarray(
                        integrand(float(y), float(z)),
                        dtype=float,
                    ),
                    z0,
                    z1,
                    epsabs=self.epsabs,
                    epsrel=self.epsrel,
                    limit=self.inner_limit,
                )

                value = np.asarray(value, dtype=float)

                if value.shape != (size,):
                    raise ValueError(
                        "vector sectional integrand returned an "
                        f"unexpected shape {value.shape}; expected {(size,)}"
                    )

                subtotal += value

            return subtotal

        bounds = [y_min, *interior_breakpoints, y_max]
        result = zero.copy()

        for left, right in zip(bounds[:-1], bounds[1:]):
            if right <= left:
                continue

            value, _ = quad_vec(
                lambda y: integrate_at_y(float(y)),
                left,
                right,
                epsabs=self.epsabs,
                epsrel=self.epsrel,
                limit=self.outer_limit,
            )

            value = np.asarray(value, dtype=float)

            if value.shape != (size,):
                raise ValueError(
                    "vector polygon integration returned an "
                    f"unexpected shape {value.shape}; expected {(size,)}"
                )

            result += value

        if not np.all(np.isfinite(result)):
            raise RuntimeError(
                "vector sectional integration returned non-finite values"
            )

        return result

    def _quad_interval(
        self,
        function: Callable[[float], float],
        left: float,
        right: float,
        *,
        limit: int,
        depth: int = 0,
        max_depth: int = 12,
    ) -> float:
        """
        Integrate one scalar interval with controlled roundoff recovery.

        QUADPACK may report roundoff when a signed integral is very small
        because of cancellation, even when both sub-interval integrals are
        individually well resolved.  The generic recovery is interval
        bisection: no geometric symmetry, material law, polynomial structure,
        or benchmark-specific information is assumed.

        ``full_output=1`` is used so QUADPACK diagnostics are inspected rather
        than emitted as IntegrationWarning messages.

        If QUADPACK still reports a diagnostic after ``max_depth`` recursive
        bisections, the integration is rejected instead of silently accepting
        an uncontrolled result.
        """

        output = quad(
            function,
            left,
            right,
            epsabs=self.epsabs,
            epsrel=self.epsrel,
            limit=limit,
            full_output=1,
        )

        value = float(output[0])

        # Successful QUADPACK calls return the usual three entries.
        if len(output) == 3:
            return value

        if depth >= max_depth:
            message = str(output[3]).strip()
            raise RuntimeError(
                "adaptive sectional integration failed after recursive "
                f"bisection on [{left}, {right}]: {message}"
            )

        midpoint = 0.5 * (left + right)

        if not (left < midpoint < right):
            message = str(output[3]).strip()
            raise RuntimeError(
                "adaptive sectional integration cannot bisect interval "
                f"[{left}, {right}]: {message}"
            )

        return (
            self._quad_interval(
                function,
                left,
                midpoint,
                limit=limit,
                depth=depth + 1,
                max_depth=max_depth,
            )
            +
            self._quad_interval(
                function,
                midpoint,
                right,
                limit=limit,
                depth=depth + 1,
                max_depth=max_depth,
            )
        )

    @staticmethod
    def _z_intervals_at_y(
        vertices: Tuple[Tuple[float, float], ...],
        y: float,
    ) -> Tuple[Tuple[float, float], ...]:
        intersections = []
        count = len(vertices)

        for i in range(count):
            y0, z0 = vertices[i]
            y1, z1 = vertices[(i + 1) % count]

            if y0 == y1:
                continue

            lower = min(y0, y1)
            upper = max(y0, y1)

            # Half-open rule prevents double-counting polygon vertices.
            if not (lower <= y < upper):
                continue

            t = (y - y0) / (y1 - y0)
            intersections.append(float(z0 + t * (z1 - z0)))

        intersections.sort()

        if len(intersections) % 2 != 0:
            if not intersections:
                return tuple()
            raise ValueError(
                "polygon slicing produced an odd number of intersections"
            )

        intervals = []

        for index in range(0, len(intersections), 2):
            z0 = intersections[index]
            z1 = intersections[index + 1]

            if z1 > z0:
                intervals.append((z0, z1))

        return tuple(intervals)

    @staticmethod
    def _merge_intervals(intervals):
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
        """Return outer slice intervals after direct-child subtraction."""
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
        return tuple((start, end) for start, end in net if end > start)


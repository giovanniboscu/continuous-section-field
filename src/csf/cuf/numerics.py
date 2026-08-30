# Version: CSF-CUF isolated transverse expansion plugins v21 - 2026-08-29
from __future__ import annotations

import math
import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.integration import SectionIntegrator


class _ScaledMaclaurinFactorPlan:
    """Precompiled evaluation plan for selected value/derivative factors."""

    __slots__ = (
        "_y_scale",
        "_z_scale",
        "_entries",
    )

    def __init__(
        self,
        *,
        y_scale: float,
        z_scale: float,
        entries,
    ) -> None:
        self._y_scale = float(y_scale)
        self._z_scale = float(z_scale)
        self._entries = tuple(entries)

    def __call__(self, y: float, z: float) -> np.ndarray:
        # Compute the scaled coordinates once.  The arithmetic below preserves
        # the same per-factor operation order used by value()/derivative().
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale
        values = np.empty(len(self._entries), dtype=float)

        for index, (p_y, p_z, derivative_code) in enumerate(self._entries):
            if derivative_code == 0:
                values[index] = (Y ** p_y) * (Z ** p_z)
            elif derivative_code == 1:
                if p_y == 0:
                    values[index] = 0.0
                else:
                    values[index] = (
                        p_y
                        * (Y ** (p_y - 1))
                        * (Z ** p_z)
                        / self._y_scale
                    )
            else:
                if p_z == 0:
                    values[index] = 0.0
                else:
                    values[index] = (
                        p_z
                        * (Y ** p_y)
                        * (Z ** (p_z - 1))
                        / self._z_scale
                    )

        return values


class ScaledMaclaurinBasis(CUFBasis):
    """Complete two-dimensional Maclaurin basis with numerical coordinate scaling."""

    def __init__(self, order: int, *, y_scale: float, z_scale: float):
        if not isinstance(order, int) or order < 0:
            raise ValueError("order must be a non-negative integer")
        if not (math.isfinite(y_scale) and y_scale > 0.0):
            raise ValueError("y_scale must be positive and finite")
        if not (math.isfinite(z_scale) and z_scale > 0.0):
            raise ValueError("z_scale must be positive and finite")
        self._order = int(order)
        self._y_scale = float(y_scale)
        self._z_scale = float(z_scale)
        self._exponents = tuple(
            (p_y, degree - p_y)
            for degree in range(order + 1)
            for p_y in range(degree, -1, -1)
        )
        self._size = len(self._exponents)

        # Dense exponent index arrays for all-at-once basis evaluation during
        # fixed-x post-processing.  They contain only basis metadata and are
        # independent of section geometry, material state, and x.
        self._p_y = np.fromiter(
            (item[0] for item in self._exponents),
            dtype=np.intp,
            count=self._size,
        )
        self._p_z = np.fromiter(
            (item[1] for item in self._exponents),
            dtype=np.intp,
            count=self._size,
        )
        self._p_y.setflags(write=False)
        self._p_z.setflags(write=False)

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._size

    @property
    def scales(self) -> tuple[float, float]:
        return self._y_scale, self._z_scale

    def exponents(self, tau: int):
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}")
        return self._exponents[tau - 1]

    def value(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}")
        p_y, p_z = self._exponents[tau - 1]
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale
        return float((Y ** p_y) * (Z ** p_z))

    def values(
        self, y: float, z: float, *, x: float | None = None
    ) -> np.ndarray:
        """Evaluate all scaled Maclaurin basis functions at one point.

        This is algebraically identical to calling ``value(tau, y, z)`` for
        every tau, but computes the powers of the scaled transverse
        coordinates only once and gathers the complete basis vector in one
        operation.  It introduces no assumption on section geometry or
        material variation.
        """
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale

        y_powers = np.empty(self._order + 1, dtype=float)
        z_powers = np.empty(self._order + 1, dtype=float)
        y_powers[0] = 1.0
        z_powers[0] = 1.0

        for degree in range(1, self._order + 1):
            y_powers[degree] = y_powers[degree - 1] * Y
            z_powers[degree] = z_powers[degree - 1] * Z

        return np.asarray(
            y_powers[self._p_y] * z_powers[self._p_z],
            dtype=float,
        )

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}")
        p_y, p_z = self._exponents[tau - 1]
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale
        if direction == "y":
            if p_y == 0:
                return 0.0
            return float(
                p_y
                * (Y ** (p_y - 1))
                * (Z ** p_z)
                / self._y_scale
            )
        if direction == "z":
            if p_z == 0:
                return 0.0
            return float(
                p_z
                * (Y ** p_y)
                * (Z ** (p_z - 1))
                / self._z_scale
            )
        raise ValueError("direction must be 'y' or 'z'")

    def compile_factors(self, factors):
        """
        Compile selected (tau, derivative) factors for repeated point queries.

        The returned callable contains only basis metadata.  Physical point
        coordinates remain inputs, so this introduces no section or material
        constancy assumption.
        """
        entries = []

        for tau, derivative in tuple(factors):
            tau = int(tau)
            if not 1 <= tau <= self._size:
                raise IndexError(f"tau must be in 1..{self._size}")

            p_y, p_z = self._exponents[tau - 1]

            if derivative is None:
                derivative_code = 0
            elif derivative == "y":
                derivative_code = 1
            elif derivative == "z":
                derivative_code = 2
            else:
                raise ValueError("derivative must be None, 'y', or 'z'")

            entries.append((p_y, p_z, derivative_code))

        return _ScaledMaclaurinFactorPlan(
            y_scale=self._y_scale,
            z_scale=self._z_scale,
            entries=entries,
        )


def _legendre_values_and_derivatives(order: int, coordinate: float):
    """Return P_n and dP_n/dcoordinate for n=0..order."""
    values = np.empty(order + 1, dtype=float)
    derivatives = np.empty(order + 1, dtype=float)
    values[0] = 1.0
    derivatives[0] = 0.0
    if order == 0:
        return values, derivatives

    values[1] = float(coordinate)
    derivatives[1] = 1.0
    for degree in range(2, order + 1):
        a = (2.0 * degree - 1.0) / degree
        b = (degree - 1.0) / degree
        values[degree] = a * coordinate * values[degree - 1] - b * values[degree - 2]
        derivatives[degree] = (
            a * (values[degree - 1] + coordinate * derivatives[degree - 1])
            - b * derivatives[degree - 2]
        )
    return values, derivatives


class _ScaledLegendreFactorPlan:
    """Precompiled evaluation plan for selected Legendre factors."""

    __slots__ = ("_order", "_y_scale", "_z_scale", "_entries")

    def __init__(self, *, order, y_scale, z_scale, entries):
        self._order = int(order)
        self._y_scale = float(y_scale)
        self._z_scale = float(z_scale)
        self._entries = tuple(entries)

    def __call__(self, y: float, z: float) -> np.ndarray:
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale
        py, dpy = _legendre_values_and_derivatives(self._order, Y)
        pz, dpz = _legendre_values_and_derivatives(self._order, Z)
        result = np.empty(len(self._entries), dtype=float)
        for index, (p_y, p_z, derivative_code) in enumerate(self._entries):
            if derivative_code == 0:
                result[index] = py[p_y] * pz[p_z]
            elif derivative_code == 1:
                result[index] = dpy[p_y] * pz[p_z] / self._y_scale
            else:
                result[index] = py[p_y] * dpz[p_z] / self._z_scale
        return result


class ScaledLegendreBasis(CUFBasis):
    """Complete-total-degree product Legendre basis on scaled coordinates.

    This spans exactly the same polynomial space as ScaledMaclaurinBasis of
    the same order, while replacing monomials by Legendre polynomials.
    """

    def __init__(self, order: int, *, y_scale: float, z_scale: float):
        if not isinstance(order, int) or order < 0:
            raise ValueError("order must be a non-negative integer")
        if not (math.isfinite(y_scale) and y_scale > 0.0):
            raise ValueError("y_scale must be positive and finite")
        if not (math.isfinite(z_scale) and z_scale > 0.0):
            raise ValueError("z_scale must be positive and finite")
        self._order = int(order)
        self._y_scale = float(y_scale)
        self._z_scale = float(z_scale)
        self._exponents = tuple(
            (p_y, degree - p_y)
            for degree in range(order + 1)
            for p_y in range(degree, -1, -1)
        )
        self._size = len(self._exponents)

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._size

    @property
    def scales(self) -> tuple[float, float]:
        return self._y_scale, self._z_scale

    def exponents(self, tau: int):
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}")
        return self._exponents[tau - 1]

    def _all(self, y: float, z: float):
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale
        py, dpy = _legendre_values_and_derivatives(self._order, Y)
        pz, dpz = _legendre_values_and_derivatives(self._order, Z)
        return py, dpy, pz, dpz

    def value(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        p_y, p_z = self.exponents(tau)
        py, _, pz, _ = self._all(y, z)
        return float(py[p_y] * pz[p_z])

    def values(
        self, y: float, z: float, *, x: float | None = None
    ) -> np.ndarray:
        py, _, pz, _ = self._all(y, z)
        return np.asarray([py[a] * pz[b] for a, b in self._exponents], dtype=float)

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        p_y, p_z = self.exponents(tau)
        py, dpy, pz, dpz = self._all(y, z)
        if direction == "y":
            return float(dpy[p_y] * pz[p_z] / self._y_scale)
        if direction == "z":
            return float(py[p_y] * dpz[p_z] / self._z_scale)
        raise ValueError("direction must be 'y' or 'z'")

    def compile_factors(self, factors):
        entries = []
        for tau, derivative in tuple(factors):
            p_y, p_z = self.exponents(tau)
            if derivative is None:
                derivative_code = 0
            elif derivative == "y":
                derivative_code = 1
            elif derivative == "z":
                derivative_code = 2
            else:
                raise ValueError("derivative must be None, 'y', or 'z'")
            entries.append((p_y, p_z, derivative_code))
        return _ScaledLegendreFactorPlan(
            order=self._order,
            y_scale=self._y_scale,
            z_scale=self._z_scale,
            entries=entries,
        )


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


def all_vertices(section_provider, x: float) -> np.ndarray:
    return np.asarray(
        [
            (float(y), float(z))
            for domain in section_provider.domains(float(x))
            for y, z in domain.vertices
        ],
        dtype=float,
    )


def transverse_scales(section_provider) -> tuple[float, float]:
    x0, x1 = map(float, section_provider.longitudinal_domain())
    vertices = np.vstack((all_vertices(section_provider, x0), all_vertices(section_provider, x1)))
    y_scale = float(np.max(np.abs(vertices[:, 0])))
    z_scale = float(np.max(np.abs(vertices[:, 1])))
    if y_scale <= 0.0 or z_scale <= 0.0:
        raise ValueError("CSF transverse coordinate scales must be positive")
    return y_scale, z_scale


def transverse_bounds(section_provider, x: float):
    vertices = all_vertices(section_provider, x)
    return (
        float(np.min(vertices[:, 0])), float(np.max(vertices[:, 0])),
        float(np.min(vertices[:, 1])), float(np.max(vertices[:, 1])),
    )

# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Scaled complete-total-degree Legendre transverse basis."""

from __future__ import annotations

import math
import numpy as np

from csf.cuf.core.basis import CUFBasis


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


    def __call__(
        self,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> np.ndarray:
        del x
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

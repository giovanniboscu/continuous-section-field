# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Scaled complete-total-degree Maclaurin transverse basis."""

from __future__ import annotations

import math
import numpy as np

from csf.cuf.core.basis import CUFBasis


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

    def __call__(
        self,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> np.ndarray:
        del x
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

# Version: CSF-CUF scaled Taylor expansion v1 - 2026-09-20
"""Complete scaled Taylor transverse expansion."""

from __future__ import annotations

import math
import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin
from csf.cuf.numerics import transverse_scales


class ScaledTaylorBasis(CUFBasis):
    """Complete two-dimensional Taylor basis in shifted scaled coordinates."""

    def __init__(
        self,
        order: int,
        *,
        y_scale: float,
        z_scale: float,
        y_center: float = 0.0,
        z_center: float = 0.0,
    ) -> None:
        if not isinstance(order, int) or order < 0:
            raise ValueError("scaled_taylor order must be a non-negative integer")

        y_scale = float(y_scale)
        z_scale = float(z_scale)
        y_center = float(y_center)
        z_center = float(z_center)

        if not math.isfinite(y_scale) or y_scale <= 0.0:
            raise ValueError("y_scale must be positive and finite")
        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError("z_scale must be positive and finite")
        if not math.isfinite(y_center):
            raise ValueError("y_center must be finite")
        if not math.isfinite(z_center):
            raise ValueError("z_center must be finite")

        self._order = int(order)
        self._y_scale = y_scale
        self._z_scale = z_scale
        self._y_center = y_center
        self._z_center = z_center

        self._exponents = tuple(
            (p_y, degree - p_y)
            for degree in range(order + 1)
            for p_y in range(degree, -1, -1)
        )
        self._size = len(self._exponents)

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

        self._power_coefficients = self._build_power_coefficients()
        self._power_coefficients.setflags(write=False)

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._size

    @property
    def scales(self) -> tuple[float, float]:
        return self._y_scale, self._z_scale

    @property
    def center(self) -> tuple[float, float]:
        return self._y_center, self._z_center

    def exponents(self, tau: int) -> tuple[int, int]:
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}")
        return self._exponents[tau - 1]

    def _scaled_coordinates(self, y: float, z: float) -> tuple[float, float]:
        return (
            (float(y) - self._y_center) / self._y_scale,
            (float(z) - self._z_center) / self._z_scale,
        )

    def value(self, tau: int, y: float, z: float, *, x: float | None = None) -> float:
        p_y, p_z = self.exponents(tau)
        Y, Z = self._scaled_coordinates(y, z)
        return float((Y ** p_y) * (Z ** p_z))

    def values(self, y: float, z: float, *, x: float | None = None) -> np.ndarray:
        Y, Z = self._scaled_coordinates(y, z)
        y_powers = np.empty(self._order + 1, dtype=float)
        z_powers = np.empty(self._order + 1, dtype=float)
        y_powers[0] = 1.0
        z_powers[0] = 1.0
        for degree in range(1, self._order + 1):
            y_powers[degree] = y_powers[degree - 1] * Y
            z_powers[degree] = z_powers[degree - 1] * Z
        return np.asarray(y_powers[self._p_y] * z_powers[self._p_z], dtype=float)

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
        Y, Z = self._scaled_coordinates(y, z)

        if direction == "y":
            if p_y == 0:
                return 0.0
            return float(p_y * (Y ** (p_y - 1)) * (Z ** p_z) / self._y_scale)

        if direction == "z":
            if p_z == 0:
                return 0.0
            return float(p_z * (Y ** p_y) * (Z ** (p_z - 1)) / self._z_scale)

        raise ValueError("direction must be 'y' or 'z'")

    def _build_power_coefficients(self) -> np.ndarray:
        count = self.order + 1
        coefficients = np.zeros((self.size, count, count), dtype=float)
        for tau in range(1, self.size + 1):
            p, q = self.exponents(tau)
            for i in range(p + 1):
                cy = (
                    math.comb(p, i)
                    * ((-self._y_center) ** (p - i))
                    / (self._y_scale ** p)
                )
                for j in range(q + 1):
                    cz = (
                        math.comb(q, j)
                        * ((-self._z_center) ** (q - j))
                        / (self._z_scale ** q)
                    )
                    coefficients[tau - 1, i, j] += cy * cz
        return coefficients

    def power_coefficients(self) -> np.ndarray:
        """Return F_tau coefficients in ascending physical powers of y and z."""
        return self._power_coefficients.copy()


def _parse_options(options):
    options = dict(options)
    allowed = {"y_center", "z_center"}
    unknown = sorted(set(options) - allowed)
    if unknown:
        raise ValueError(
            "scaled_taylor received unsupported cuf.basis_options: "
            f"{unknown}"
        )

    y_center = float(options.get("y_center", 0.0))
    z_center = float(options.get("z_center", 0.0))
    if not math.isfinite(y_center):
        raise ValueError("scaled_taylor y_center must be finite")
    if not math.isfinite(z_center):
        raise ValueError("scaled_taylor z_center must be finite")
    return y_center, z_center


def _build(*, order, section_provider, continuous_section_field, options):
    del continuous_section_field  # Available by contract; unused here.
    y_center, z_center = _parse_options(options)
    y_scale, z_scale = transverse_scales(section_provider)
    return ScaledTaylorBasis(
        int(order),
        y_scale=y_scale,
        z_scale=z_scale,
        y_center=y_center,
        z_center=z_center,
    )


def _section_gauss_minimum(basis):
    return int(basis.order) + 1


def _longitudinal_transverse_degree(basis):
    return 2 * int(basis.order)


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_taylor",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=_longitudinal_transverse_degree,
    )
)

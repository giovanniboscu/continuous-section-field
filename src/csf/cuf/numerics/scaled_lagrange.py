# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Scaled hierarchical Serendipity-Lagrange transverse basis."""

from __future__ import annotations

import math

from csf.cuf.core.basis import CUFBasis, SerendipityLagrangeReferenceBasis


class ScaledLagrangeBasis(CUFBasis):
    """
    Hierarchical Serendipity-Lagrange basis in scaled coordinates.

    The physical coordinates are converted to reference coordinates as:

        xi  = y / y_scale
        eta = z / z_scale

    The underlying reference basis constructs the complete hierarchy
    associated with the requested order.
    """

    def __init__(
        self,
        *,
        order: int,
        y_scale: float,
        z_scale: float,
    ) -> None:
        """Construct the scaled hierarchical basis."""

        if not isinstance(order, int):
            raise TypeError(
                "scaled_lagrange order must be an integer"
            )

        if order < 1:
            raise ValueError(
                "scaled_lagrange order must be >= 1"
            )

        y_scale = float(y_scale)
        z_scale = float(z_scale)

        if not math.isfinite(y_scale) or y_scale <= 0.0:
            raise ValueError(
                "y_scale must be positive and finite"
            )

        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError(
                "z_scale must be positive and finite"
            )

        # This object owns the hierarchical term definitions,
        # reference values, and reference derivatives.
        self._reference_basis = (
            SerendipityLagrangeReferenceBasis(order)
        )

        self._y_scale = y_scale
        self._z_scale = z_scale



    @property
    def order(self) -> int:
        """Return the hierarchy order requested by the YAML file."""

        return self._reference_basis.order

    @property
    def size(self) -> int:
        """Return the total number of transverse expansion functions."""

        return self._reference_basis.size

    @property
    def scales(self) -> tuple[float, float]:
        """Return the fixed transverse coordinate scales."""

        return self._y_scale, self._z_scale

    def definition(self, tau: int):
        """Return the hierarchical definition associated with tau."""

        return self._reference_basis.definition(tau)

    


    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """
        Evaluate one basis function at physical coordinates.

        The current expansion uses fixed global scales and therefore
        does not depend explicitly on x.
        """

        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        return float(
            self._reference_basis.value(
                tau,
                xi,
                eta,
            )
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
        """
        Evaluate one physical transverse derivative.

        The reference derivatives are converted through:

            d/dy = (1/y_scale) d/dxi
            d/dz = (1/z_scale) d/deta
        """

        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        if direction == "y":
            derivative_xi = (
                self._reference_basis.derivative(
                    tau,
                    "y",
                    xi,
                    eta,
                )
            )

            return float(
                derivative_xi / self._y_scale
            )

        if direction == "z":
            derivative_eta = (
                self._reference_basis.derivative(
                    tau,
                    "z",
                    xi,
                    eta,
                )
            )

            return float(
                derivative_eta / self._z_scale
            )

        raise ValueError(
            "direction must be 'y' or 'z'"
        )

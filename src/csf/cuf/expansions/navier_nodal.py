# Version: CSF-CUF Navier-harmonic nodal longitudinal basis v1 - 2026-11-21
"""Nodal C0 trigonometric longitudinal basis containing Navier half-waves.

This is a *finite-element shape-function basis*, not the global modal Navier
solution.  It exactly represents both sin(pi*t) and cos(pi*t) with one element
of order >= 2, where t=(xi+1)/2 is the normalized element coordinate.

On each element the interpolation space is

    span{1, cos(pi*t), sin(k*pi*t), k=1,...,order-1}.

Reference DOFs are real nodal displacement values at equally spaced points.
Only endpoint DOFs are shared between adjoining elements.  The interior
sinusoidal bubbles use the discrete sine transform (DST-I), avoiding a dense,
ill-conditioned trigonometric Vandermonde inversion.

The CUF nucleus, physical section description, FEM topology, and general
stiffness assembly need no knowledge of this basis's concrete formulas.
"""

from __future__ import annotations

import numpy as np

from csf.cuf.core.longitudinal_basis import NodalC0LongitudinalBasis
from csf.cuf.core.longitudinal_basis_plugins import (
    LongitudinalBasisPlugin,
    register_longitudinal_basis_plugin,
)


class NavierNodalLongitudinalBasis(NodalC0LongitudinalBasis):
    """Cardinal trigonometric FE basis with exact first Navier harmonics.

    ``order`` is the number of equally spaced *subintervals* of one element;
    the number of shape functions is ``order + 1``.  The endpoint functions
    are 1/2*(1 +/- cos(pi*t)), corrected by the interior sine-cardinal
    functions.  This achieves a partition of unity and Kronecker delta nodal
    interpolation with a genuinely non-polynomial approximation space.
    """

    def __init__(self, order: int) -> None:
        if not isinstance(order, int) or isinstance(order, bool):
            raise TypeError("navier_nodal order must be an integer")
        if order < 1:
            raise ValueError("navier_nodal order must be >= 1")
        self._order = order
        self._nodes = np.linspace(-1.0, 1.0, order + 1, dtype=float)
        self._frequencies = np.arange(1, order, dtype=float)
        self._interior_t = np.arange(1, order, dtype=float) / order
        # Orthogonality of the DST-I implies S^{-1} = (2/order) S^T.
        self._sine_table = np.sin(
            np.pi * np.outer(self._interior_t, self._frequencies)
        )
        self._left_samples = 0.5 * (
            1.0 + np.cos(np.pi * self._interior_t)
        )
        self._right_samples = 1.0 - self._left_samples

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._order + 1

    @property
    def polynomial_degree(self) -> None:
        """This basis is non-polynomial; never invent a polynomial degree."""
        return None

    @property
    def reference_nodes(self) -> np.ndarray:
        return self._nodes.copy()

    @staticmethod
    def _coordinate(xi: float) -> float:
        xi = float(xi)
        if not np.isfinite(xi):
            raise ValueError("navier_nodal reference coordinate must be finite")
        return 0.5 * (xi + 1.0)

    def values(self, xi: float) -> np.ndarray:
        t = self._coordinate(xi)
        # Interior shape functions are the DST-I cardinal basis, with zeros at
        # both endpoints; the empty array naturally handles order == 1.
        bubbles = (2.0 / self._order) * (
            self._sine_table @ np.sin(np.pi * self._frequencies * t)
        )
        left = 0.5 * (1.0 + np.cos(np.pi * t))
        right = 1.0 - left
        result = np.empty(self.size, dtype=float)
        result[0] = left - self._left_samples @ bubbles
        result[1:-1] = bubbles
        result[-1] = right - self._right_samples @ bubbles
        return result

    def derivatives_reference(self, xi: float) -> np.ndarray:
        t = self._coordinate(xi)
        # Derivative is with respect to xi, NOT the physical element length.
        # d/dxi = (1/2) d/dt.
        d_bubbles = (np.pi / self._order) * (
            self._sine_table @ (
                self._frequencies * np.cos(np.pi * self._frequencies * t)
            )
        )
        d_left = -0.25 * np.pi * np.sin(np.pi * t)
        result = np.empty(self.size, dtype=float)
        result[0] = d_left - self._left_samples @ d_bubbles
        result[1:-1] = d_bubbles
        result[-1] = -d_left - self._right_samples @ d_bubbles
        return result

    def minimum_gauss_order(self, *, coefficient_polynomial_degree: int) -> int:
        """Conservative Gauss-Legendre *recommendation*, not an exactness claim.

        Products of shapes/derivatives have harmonics through 2*(order-1).
        Gauss-Legendre does not exactly integrate trigonometric products. The
        3*order+6 baseline deliberately oversamples the highest frequency;
        quadrature refinement remains necessary for convergence verification,
        especially for rapidly varying CSF material or geometry fields.
        """
        degree = int(coefficient_polynomial_degree)
        if degree < 0:
            raise ValueError("coefficient_polynomial_degree must be >= 0")
        return 3 * self.order + 6 + (degree + 1) // 2

    # power_coefficients() intentionally inherits None; trigonometric shapes
    # must never be serialized as a false polynomial displacement checkpoint.


def _build(*, order: int, options: dict) -> NavierNodalLongitudinalBasis:
    options = dict(options)
    if options:
        raise ValueError(
            "navier_nodal received unsupported longitudinal.basis_options: "
            f"{sorted(options)}"
        )
    return NavierNodalLongitudinalBasis(int(order))


register_longitudinal_basis_plugin(
    LongitudinalBasisPlugin(name="navier_nodal", builder=_build)
)

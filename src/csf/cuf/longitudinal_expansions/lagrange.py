# Version: CSF-CUF longitudinal Lagrange plugin v1 - 2026-09-21
"""Equally spaced nodal Lagrange longitudinal basis.

This plugin reproduces the historical longitudinal shape functions exactly,
but the implementation is now isolated from the finite-element machinery.
"""

from __future__ import annotations

import numpy as np

from csf.cuf.core.longitudinal_basis import NodalC0LongitudinalBasis
from csf.cuf.core.longitudinal_basis_plugins import (
    LongitudinalBasisPlugin,
    register_longitudinal_basis_plugin,
)


class LagrangeLongitudinalBasis(NodalC0LongitudinalBasis):
    """Equally spaced cardinal Lagrange basis on ``[-1, 1]``."""

    def __init__(self, order: int) -> None:
        if not isinstance(order, int):
            raise TypeError("longitudinal Lagrange order must be an integer")
        if order < 1:
            raise ValueError("longitudinal Lagrange order must be >= 1")

        self._order = order
        self._nodes = np.linspace(-1.0, 1.0, order + 1, dtype=float)
        self._power_coefficients = self._build_power_coefficients(self._nodes)

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._order + 1

    @property
    def polynomial_degree(self) -> int:
        return self._order

    @property
    def reference_nodes(self) -> np.ndarray:
        return self._nodes.copy()

    def values(self, xi: float) -> np.ndarray:
        xi = float(xi)
        count = self.size
        values = np.ones(count, dtype=float)

        for a in range(count):
            for b in range(count):
                if a == b:
                    continue
                values[a] *= (
                    (xi - self._nodes[b])
                    / (self._nodes[a] - self._nodes[b])
                )

        return values

    def derivatives_reference(self, xi: float) -> np.ndarray:
        xi = float(xi)
        count = self.size
        derivatives = np.zeros(count, dtype=float)

        for a in range(count):
            total = 0.0
            for k in range(count):
                if k == a:
                    continue

                term = 1.0 / (self._nodes[a] - self._nodes[k])
                for b in range(count):
                    if b == a or b == k:
                        continue
                    term *= (
                        (xi - self._nodes[b])
                        / (self._nodes[a] - self._nodes[b])
                    )
                total += term

            derivatives[a] = total

        return derivatives

    def power_coefficients(self) -> np.ndarray:
        return self._power_coefficients.copy()

    @staticmethod
    def _build_power_coefficients(nodes: np.ndarray) -> np.ndarray:
        nodes = np.asarray(nodes, dtype=float)
        count = int(nodes.size)
        result = np.empty((count, count), dtype=float)
        for index in range(count):
            other_nodes = np.delete(nodes, index)
            denominator = np.prod(nodes[index] - other_nodes)
            result[index, :] = np.poly(other_nodes)[::-1] / denominator
        return result


def _reject_options(options) -> None:
    if options:
        raise ValueError(
            "lagrange does not accept longitudinal.basis_options; "
            f"received {sorted(options)}"
        )


def _build(*, order, options):
    _reject_options(options)
    return LagrangeLongitudinalBasis(int(order))


register_longitudinal_basis_plugin(
    LongitudinalBasisPlugin(
        name="lagrange",
        builder=_build,
    )
)

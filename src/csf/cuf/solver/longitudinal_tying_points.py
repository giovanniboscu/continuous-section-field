# Version: CSF-CUF longitudinal tying-point selector v01 - 2026-10-11
"""Select 1D longitudinal tying points independently of the CUF core.

The selector supplies reference coordinates only. It does not change the
longitudinal displacement basis, choose quadrature, interpolate strains, or
assemble a stiffness matrix.

The first registered criterion, ``barlow``, uses the p-point Gauss-Legendre
locations for longitudinal polynomial degree p. Carrera et al. (2017),
Eqs. (25)-(27), explicitly document the cases p=1, 2, 3. Application of the
same point-selection rule for p>3 is a mathematical extension, NOT a validated
MITC formulation from that paper.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


PointRule = Callable[[int], np.ndarray]


class LongitudinalTyingPointSelector:
    """Dispatch named point-selection criteria without basis-specific logic.

    Register additional methods with :meth:`register`. No method other than
    ``barlow`` is assumed or used implicitly.
    """

    def __init__(self) -> None:
        self._rules: dict[str, PointRule] = {}
        self.register("barlow", self._barlow_points)

    def register(self, criterion: str, rule: PointRule) -> None:
        """Register a rule accepting polynomial degree and returning 1D nodes."""
        if not isinstance(criterion, str) or not criterion.strip():
            raise ValueError("criterion must be a nonempty string")
        if criterion != criterion.strip():
            raise ValueError("criterion must not contain outer whitespace")
        if criterion in self._rules:
            raise ValueError(f"tying-point criterion {criterion!r} is already registered")
        if not callable(rule):
            raise TypeError("tying-point rule must be callable")
        self._rules[criterion] = rule

    @property
    def criteria(self) -> tuple[str, ...]:
        return tuple(self._rules)

    def points(self, *, criterion: str, longitudinal_degree: int) -> np.ndarray:
        """Return nodes in [-1,1] for the explicit criterion and degree.

        Only coordinates are returned; other numerical operators (including
        interpolation weights) are provided by their respective components.
        """
        if isinstance(longitudinal_degree, bool) or not isinstance(longitudinal_degree, int):
            raise TypeError("longitudinal_degree must be an integer")
        if longitudinal_degree < 1:
            raise ValueError("longitudinal_degree must be >= 1")
        try:
            rule = self._rules[criterion]
        except (KeyError, TypeError):
            raise ValueError(
                f"unknown tying-point criterion {criterion!r}; "
                f"available: {', '.join(self.criteria)}"
            ) from None

        coords = np.asarray(rule(longitudinal_degree), dtype=float)
        if coords.ndim != 1 or coords.size == 0:
            raise ValueError(f"criterion {criterion!r} returned no valid 1D point array")
        if not np.all(np.isfinite(coords)):
            raise ValueError(f"criterion {criterion!r} returned non-finite coordinates")
        if np.unique(coords).size != coords.size:
            raise ValueError(f"criterion {criterion!r} returned duplicate coordinates")
        if np.any((coords < -1.0) | (coords > 1.0)):
            raise ValueError(f"criterion {criterion!r} returned coordinates outside [-1,1]")
        return coords.copy()

    @staticmethod
    def _barlow_points(longitudinal_degree: int) -> np.ndarray:
        points, _weights = np.polynomial.legendre.leggauss(longitudinal_degree)
        return points

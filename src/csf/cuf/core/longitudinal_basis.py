# Version: CSF-CUF isolated longitudinal basis API v1 - 2026-09-21
"""Runtime contracts for longitudinal approximation bases.

The longitudinal finite-element machinery depends on this API only.  Concrete
shape-function families live in ``csf.cuf.longitudinal_expansions`` and are
loaded through the longitudinal basis plugin registry.

The separation is intentional:

    finite-element discretization  ->  LongitudinalBasis API  <-  plugins

No concrete basis family is imported here or by the FEM implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class LongitudinalBasis(ABC):
    """Generic local longitudinal approximation basis on ``xi in [-1, 1]``."""

    @property
    @abstractmethod
    def order(self) -> int:
        """User-facing approximation order."""
        raise NotImplementedError

    @property
    @abstractmethod
    def size(self) -> int:
        """Number of local longitudinal coefficients/functions."""
        raise NotImplementedError

    @property
    @abstractmethod
    def polynomial_degree(self) -> int:
        """Maximum polynomial degree carried by one basis function."""
        raise NotImplementedError

    @abstractmethod
    def values(self, xi: float) -> np.ndarray:
        """Return all basis values at one reference coordinate."""
        raise NotImplementedError

    @abstractmethod
    def derivatives_reference(self, xi: float) -> np.ndarray:
        """Return all first derivatives with respect to ``xi``."""
        raise NotImplementedError

    def power_coefficients(self) -> np.ndarray | None:
        """Return exact ascending-power coefficients when available.

        Row ``a`` contains the coefficients of local basis function ``a`` in
        ascending powers of ``xi``.  ``None`` explicitly means that this basis
        does not provide a polynomial checkpoint representation.
        """
        return None


class NodalC0LongitudinalBasis(LongitudinalBasis):
    """Longitudinal basis with direct nodal C0 finite-element traces.

    This is a *capability contract*, not a concrete shape-function family.
    The current ``finite_element`` discretizer supports this topology because
    adjacent elements can share the right/left endpoint coefficient directly.
    Non-nodal or non-C0 bases may implement :class:`LongitudinalBasis`, but
    require a different FEM topology adapter and are rejected explicitly by
    the current discretizer rather than being interpreted as Lagrange.
    """

    @property
    @abstractmethod
    def reference_nodes(self) -> np.ndarray:
        """Reference coordinates associated with the local nodal coefficients."""
        raise NotImplementedError

    def validated_reference_nodes(self) -> np.ndarray:
        nodes = np.asarray(self.reference_nodes, dtype=float)
        if nodes.shape != (self.size,):
            raise ValueError(
                "nodal longitudinal basis reference_nodes must have shape "
                f"({self.size},), got {nodes.shape}"
            )
        if not np.all(np.isfinite(nodes)):
            raise ValueError("longitudinal reference nodes must be finite")
        if np.any(np.diff(nodes) <= 0.0):
            raise ValueError(
                "longitudinal reference nodes must be strictly increasing"
            )
        if not np.isclose(nodes[0], -1.0, rtol=0.0, atol=1.0e-14):
            raise ValueError(
                "a nodal C0 longitudinal basis must expose a left endpoint "
                "node at xi=-1"
            )
        if not np.isclose(nodes[-1], 1.0, rtol=0.0, atol=1.0e-14):
            raise ValueError(
                "a nodal C0 longitudinal basis must expose a right endpoint "
                "node at xi=1"
            )
        return nodes.copy()

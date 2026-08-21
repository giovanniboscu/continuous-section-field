"""
Generic one-dimensional longitudinal finite-element discretization for CSF-CUF.

This module performs only the kinematic discretization along x:

    CSF longitudinal domain
        -> nodes
        -> elements
        -> Lagrange shape functions N_a(x)
        -> first derivatives dN_a/dx

It does NOT:
- integrate element matrices;
- assemble the global system;
- apply boundary conditions;
- solve for unknowns;
- contain geometry/material/benchmark data.

The physical longitudinal interval is obtained exclusively from the generic
SectionProvider API. It is never repeated in solver configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from csf.cuf.core.section import SectionProvider
from csf.cuf.problem.problem import LongitudinalDiscretization


@dataclass(frozen=True)
class LongitudinalElement1D:
    """
    One isoparametric 1D Lagrange finite element.

    ``node_ids`` refer to the global longitudinal mesh.
    ``coordinates`` contain the corresponding physical x coordinates.
    """

    index: int
    node_ids: Tuple[int, ...]
    coordinates: Tuple[float, ...]

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("element index must be non-negative")

        if len(self.node_ids) < 2:
            raise ValueError("an element requires at least two nodes")

        if len(self.coordinates) != len(self.node_ids):
            raise ValueError(
                "element coordinates and node_ids must have the same size"
            )

        if any(
            self.coordinates[i + 1] <= self.coordinates[i]
            for i in range(len(self.coordinates) - 1)
        ):
            raise ValueError(
                "element coordinates must be strictly increasing"
            )

    @property
    def order(self) -> int:
        return len(self.node_ids) - 1

    @property
    def x_start(self) -> float:
        return float(self.coordinates[0])

    @property
    def x_end(self) -> float:
        return float(self.coordinates[-1])

    @property
    def length(self) -> float:
        return self.x_end - self.x_start

    @property
    def reference_nodes(self) -> np.ndarray:
        """
        Equally spaced interpolation nodes on the reference interval [-1, 1].
        """
        return np.linspace(-1.0, 1.0, self.order + 1)

    def map_to_physical(self, xi: float) -> float:
        """
        Affine map from reference coordinate xi in [-1,1] to physical x.

        The mesh uses equally spaced physical nodes, so the isoparametric map
        is affine for every polynomial order.
        """
        xi = float(xi)

        return (
            0.5 * (1.0 - xi) * self.x_start
            + 0.5 * (1.0 + xi) * self.x_end
        )

    @property
    def jacobian(self) -> float:
        """dx/dxi for the affine element map."""
        return 0.5 * self.length

    def shape_values(self, xi: float) -> np.ndarray:
        """
        Evaluate all Lagrange shape functions at reference coordinate xi.
        """
        xi = float(xi)
        nodes = self.reference_nodes
        count = len(nodes)
        values = np.ones(count, dtype=float)

        for a in range(count):
            for b in range(count):
                if a == b:
                    continue
                values[a] *= (xi - nodes[b]) / (nodes[a] - nodes[b])

        return values

    def shape_derivatives_reference(self, xi: float) -> np.ndarray:
        """
        Evaluate dN_a/dxi for all Lagrange shape functions.
        """
        xi = float(xi)
        nodes = self.reference_nodes
        count = len(nodes)
        derivatives = np.zeros(count, dtype=float)

        for a in range(count):
            total = 0.0

            for k in range(count):
                if k == a:
                    continue

                term = 1.0 / (nodes[a] - nodes[k])

                for b in range(count):
                    if b == a or b == k:
                        continue

                    term *= (xi - nodes[b]) / (nodes[a] - nodes[b])

                total += term

            derivatives[a] = total

        return derivatives

    def shape_derivatives_physical(self, xi: float) -> np.ndarray:
        """
        Evaluate dN_a/dx for all shape functions.
        """
        return self.shape_derivatives_reference(xi) / self.jacobian


@dataclass(frozen=True)
class LongitudinalMesh1D:
    """
    Generic 1D finite-element mesh over the longitudinal CSF domain.
    """

    x_start: float
    x_end: float
    nodes: Tuple[float, ...]
    elements: Tuple[LongitudinalElement1D, ...]
    order: int

    @property
    def number_of_nodes(self) -> int:
        return len(self.nodes)

    @property
    def number_of_elements(self) -> int:
        return len(self.elements)

    @property
    def length(self) -> float:
        return self.x_end - self.x_start


class LongitudinalDiscretizer:
    """
    Build a longitudinal FE mesh from SectionProvider + solver options.

    The domain comes only from ``section_provider.longitudinal_domain()``.
    """

    def build(
        self,
        *,
        section_provider: SectionProvider,
        discretization: LongitudinalDiscretization,
    ) -> LongitudinalMesh1D:
        if discretization.method != "finite_element":
            raise ValueError(
                "LongitudinalDiscretizer currently supports "
                "'finite_element' only"
            )

        x_start, x_end = section_provider.longitudinal_domain()

        x_start = float(x_start)
        x_end = float(x_end)

        if not np.isfinite(x_start) or not np.isfinite(x_end):
            raise ValueError("longitudinal domain endpoints must be finite")

        if x_end <= x_start:
            raise ValueError(
                "longitudinal domain must satisfy x_end > x_start"
            )

        n_elements = discretization.elements
        order = discretization.order

        # C0-conforming Lagrange mesh:
        # each new element adds ``order`` new global nodes.
        n_nodes = n_elements * order + 1

        nodes_array = np.linspace(
            x_start,
            x_end,
            n_nodes,
            dtype=float,
        )

        elements = []

        for element_index in range(n_elements):
            first = element_index * order
            node_ids = tuple(
                range(
                    first,
                    first + order + 1,
                )
            )

            coordinates = tuple(
                float(nodes_array[node_id])
                for node_id in node_ids
            )

            elements.append(
                LongitudinalElement1D(
                    index=element_index,
                    node_ids=node_ids,
                    coordinates=coordinates,
                )
            )

        return LongitudinalMesh1D(
            x_start=x_start,
            x_end=x_end,
            nodes=tuple(float(x) for x in nodes_array),
            elements=tuple(elements),
            order=order,
        )


# =============================================================================
# Generic longitudinal element integration
# =============================================================================

from abc import ABC, abstractmethod
from typing import Callable


ScalarLongitudinalField = Callable[[float], float]


class LongitudinalIntegrator(ABC):
    """
    Generic integration backend for one-dimensional longitudinal elements.

    The integrator operates only on:
        - a LongitudinalElement1D;
        - longitudinal shape functions N_a(x);
        - their first derivatives dN_a/dx;
        - a scalar coefficient field c(x).

    It does not know anything about:
        - section geometry;
        - material laws;
        - CUF basis functions;
        - J or K semantics;
        - boundary conditions;
        - global assembly.

    The derivative orders currently admitted are 0 and 1, exactly matching
    the weak-form longitudinal orders generated by FundamentalNucleusProvider.
    """

    @abstractmethod
    def integrate_bilinear(
        self,
        *,
        element: LongitudinalElement1D,
        coefficient: ScalarLongitudinalField,
        test_x_order: int,
        trial_x_order: int,
    ) -> np.ndarray:
        """
        Return the local matrix

            A_ab = integral_e
                   D^(test_x_order) N_a(x)
                   c(x)
                   D^(trial_x_order) N_b(x)
                   dx.
        """
        raise NotImplementedError

    @abstractmethod
    def integrate_linear(
        self,
        *,
        element: LongitudinalElement1D,
        load: ScalarLongitudinalField,
    ) -> np.ndarray:
        """
        Return the local load vector

            f_a = integral_e N_a(x) q(x) dx.
        """
        raise NotImplementedError


class GaussLegendreLongitudinalIntegrator(LongitudinalIntegrator):
    """
    Gauss-Legendre quadrature on the reference interval [-1, 1].

    ``quadrature_order`` is the number of Gauss points.

    This is a numerical integration strategy only. It imposes no assumption
    that the longitudinal coefficient field is constant or polynomial.
    """

    def __init__(
        self,
        quadrature_order: int,
    ) -> None:
        if not isinstance(quadrature_order, int):
            raise TypeError("quadrature_order must be an integer")

        if quadrature_order < 1:
            raise ValueError("quadrature_order must be >= 1")

        self.quadrature_order = quadrature_order

        points, weights = np.polynomial.legendre.leggauss(
            quadrature_order
        )

        self._points = np.asarray(points, dtype=float)
        self._weights = np.asarray(weights, dtype=float)

    @property
    def points(self) -> np.ndarray:
        return self._points.copy()

    @property
    def weights(self) -> np.ndarray:
        return self._weights.copy()

    def integrate_bilinear(
        self,
        *,
        element: LongitudinalElement1D,
        coefficient: ScalarLongitudinalField,
        test_x_order: int,
        trial_x_order: int,
    ) -> np.ndarray:
        self._validate_derivative_order(
            test_x_order,
            name="test_x_order",
        )
        self._validate_derivative_order(
            trial_x_order,
            name="trial_x_order",
        )

        if not callable(coefficient):
            raise TypeError("coefficient must be callable")

        size = element.order + 1
        matrix = np.zeros((size, size), dtype=float)

        jacobian = element.jacobian

        for xi, weight in zip(
            self._points,
            self._weights,
        ):
            x = element.map_to_physical(float(xi))

            c = float(coefficient(x))

            if not np.isfinite(c):
                raise ValueError(
                    f"coefficient field returned non-finite value at x={x}"
                )

            test_vector = self._shape_operator(
                element=element,
                xi=float(xi),
                x_order=test_x_order,
            )

            trial_vector = self._shape_operator(
                element=element,
                xi=float(xi),
                x_order=trial_x_order,
            )

            matrix += (
                float(weight)
                * jacobian
                * c
                * np.outer(
                    test_vector,
                    trial_vector,
                )
            )

        return matrix

    def integrate_linear(
        self,
        *,
        element: LongitudinalElement1D,
        load: ScalarLongitudinalField,
    ) -> np.ndarray:
        if not callable(load):
            raise TypeError("load must be callable")

        size = element.order + 1
        vector = np.zeros(size, dtype=float)

        jacobian = element.jacobian

        for xi, weight in zip(
            self._points,
            self._weights,
        ):
            x = element.map_to_physical(float(xi))
            q = float(load(x))

            if not np.isfinite(q):
                raise ValueError(
                    f"load field returned non-finite value at x={x}"
                )

            N = element.shape_values(float(xi))

            vector += (
                float(weight)
                * jacobian
                * q
                * N
            )

        return vector

    @staticmethod
    def _shape_operator(
        *,
        element: LongitudinalElement1D,
        xi: float,
        x_order: int,
    ) -> np.ndarray:
        if x_order == 0:
            return element.shape_values(xi)

        if x_order == 1:
            return element.shape_derivatives_physical(xi)

        raise ValueError(
            "longitudinal derivative order must be 0 or 1"
        )

    @staticmethod
    def _validate_derivative_order(
        value: int,
        *,
        name: str,
    ) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")

        if value not in (0, 1):
            raise ValueError(
                f"{name} must be 0 or 1"
            )

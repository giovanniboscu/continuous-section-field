# Version: CSF-CUF normalized longitudinal partition v3 - 2026-09-21
"""Generic one-dimensional longitudinal finite-element discretization.

The FEM layer owns only longitudinal mesh/discretization responsibilities:

    CSF longitudinal domain
        -> finite elements
        -> element mapping/connectivity
        -> use of a LongitudinalBasis supplied from outside

Concrete longitudinal shape-function families are not implemented or imported
here.  They live in ``csf.cuf.longitudinal_expansions`` and reach this module
only through the abstract longitudinal-basis API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Tuple

import numpy as np

from csf.cuf.core.longitudinal_basis import (
    LongitudinalBasis,
    NodalC0LongitudinalBasis,
)
from csf.cuf.core.section import SectionProvider
from csf.cuf.problem.problem import LongitudinalDiscretization


@dataclass(frozen=True)
class LongitudinalElement1D:
    """One generic 1D finite element using an injected longitudinal basis.

    ``node_ids`` and ``coordinates`` describe the current nodal-C0 FEM
    topology.  Shape values and derivatives are delegated entirely to
    ``basis``; this element contains no concrete interpolation formula.
    """

    index: int
    node_ids: Tuple[int, ...]
    coordinates: Tuple[float, ...]
    basis: LongitudinalBasis

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("element index must be non-negative")

        if not isinstance(self.basis, LongitudinalBasis):
            raise TypeError("basis must implement LongitudinalBasis")

        if len(self.node_ids) != self.basis.size:
            raise ValueError(
                "element node_ids size must match longitudinal basis size"
            )

        if len(self.coordinates) != len(self.node_ids):
            raise ValueError(
                "element coordinates and node_ids must have the same size"
            )

        if len(self.coordinates) < 2:
            raise ValueError("an element requires at least two trace coordinates")

        if any(
            self.coordinates[i + 1] <= self.coordinates[i]
            for i in range(len(self.coordinates) - 1)
        ):
            raise ValueError("element coordinates must be strictly increasing")

    @property
    def order(self) -> int:
        return int(self.basis.order)

    @property
    def local_size(self) -> int:
        return int(self.basis.size)

    @property
    def reference_nodes(self) -> np.ndarray:
        """Compatibility view for nodal-C0 bases only."""
        if not isinstance(self.basis, NodalC0LongitudinalBasis):
            raise TypeError(
                "this longitudinal basis does not expose nodal reference coordinates"
            )
        return self.basis.validated_reference_nodes()

    @property
    def x_start(self) -> float:
        return float(self.coordinates[0])

    @property
    def x_end(self) -> float:
        return float(self.coordinates[-1])

    @property
    def length(self) -> float:
        return self.x_end - self.x_start

    def map_to_physical(self, xi: float) -> float:
        """Affine map from ``xi in [-1,1]`` to the physical element interval."""
        xi = float(xi)
        return (
            0.5 * (1.0 - xi) * self.x_start
            + 0.5 * (1.0 + xi) * self.x_end
        )

    @property
    def jacobian(self) -> float:
        """Return ``dx/dxi`` for the affine element map."""
        return 0.5 * self.length

    def shape_values(self, xi: float) -> np.ndarray:
        values = np.asarray(self.basis.values(float(xi)), dtype=float)
        if values.shape != (self.local_size,):
            raise ValueError(
                "longitudinal basis returned shape values with invalid size"
            )
        return values

    def shape_derivatives_reference(self, xi: float) -> np.ndarray:
        derivatives = np.asarray(
            self.basis.derivatives_reference(float(xi)),
            dtype=float,
        )
        if derivatives.shape != (self.local_size,):
            raise ValueError(
                "longitudinal basis returned reference derivatives with invalid size"
            )
        return derivatives

    def shape_derivatives_physical(self, xi: float) -> np.ndarray:
        return self.shape_derivatives_reference(xi) / self.jacobian


@dataclass(frozen=True)
class LongitudinalMesh1D:
    """Generic 1D finite-element mesh over the longitudinal CSF domain."""

    x_start: float
    x_end: float
    nodes: Tuple[float, ...]
    elements: Tuple[LongitudinalElement1D, ...]
    basis: LongitudinalBasis

    def __post_init__(self) -> None:
        if not isinstance(self.basis, LongitudinalBasis):
            raise TypeError("mesh basis must implement LongitudinalBasis")
        if not self.elements:
            raise ValueError("longitudinal mesh requires at least one element")
        if any(element.basis is not self.basis for element in self.elements):
            raise ValueError(
                "all longitudinal elements must use the mesh longitudinal basis instance"
            )

    @property
    def number_of_nodes(self) -> int:
        return len(self.nodes)

    @property
    def number_of_elements(self) -> int:
        return len(self.elements)

    @property
    def length(self) -> float:
        return self.x_end - self.x_start

    @property
    def order(self) -> int:
        return int(self.basis.order)

    @property
    def local_size(self) -> int:
        return int(self.basis.size)


class LongitudinalDiscretizer:
    """Build a longitudinal FE mesh from CSF + an injected basis.

    The current ``finite_element`` topology supports bases implementing
    :class:`NodalC0LongitudinalBasis`.  This requirement is explicit: the FEM
    does not infer Lagrange or any other concrete family.  A future topology
    adapter can support non-nodal bases without changing the basis plugins.
    """

    def build(
        self,
        *,
        section_provider: SectionProvider,
        discretization: LongitudinalDiscretization,
        basis: LongitudinalBasis,
    ) -> LongitudinalMesh1D:
        if discretization.method != "finite_element":
            raise ValueError(
                "LongitudinalDiscretizer currently supports 'finite_element' only"
            )

        if not isinstance(basis, LongitudinalBasis):
            raise TypeError("basis must implement LongitudinalBasis")

        if not isinstance(basis, NodalC0LongitudinalBasis):
            raise ValueError(
                "longitudinal.method='finite_element' currently requires a "
                "NodalC0LongitudinalBasis topology; the selected plugin is "
                f"{type(basis).__name__}"
            )

        reference_nodes = basis.validated_reference_nodes()

        x_start, x_end = section_provider.longitudinal_domain()
        x_start = float(x_start)
        x_end = float(x_end)

        if not np.isfinite(x_start) or not np.isfinite(x_end):
            raise ValueError("longitudinal domain endpoints must be finite")
        if x_end <= x_start:
            raise ValueError("longitudinal domain must satisfy x_end > x_start")

        local_size = int(basis.size)
        equispaced_reference = np.linspace(
            -1.0,
            1.0,
            local_size,
            dtype=float,
        )

        if discretization.elements is not None:
            n_elements = int(discretization.elements)
            boundaries = np.linspace(
                x_start,
                x_end,
                n_elements + 1,
                dtype=float,
            )
            uniform_count_partition = True
        else:
            normalized_boundaries = np.asarray(
                discretization.element_boundaries,
                dtype=float,
            )
            n_elements = normalized_boundaries.size - 1
            uniform_count_partition = False

            # Explicit FEM boundaries are configured in the normalized
            # longitudinal coordinate eta in [0, 1].  Only the discretizer
            # maps them to the physical CSF domain; the basis plugin remains
            # entirely independent of the partition and of physical x.
            boundaries = (
                x_start
                + normalized_boundaries * (x_end - x_start)
            )
            boundaries = np.asarray(boundaries, dtype=float)
            boundaries[0] = x_start
            boundaries[-1] = x_end

        elements = []

        if (
            uniform_count_partition
            and np.array_equal(reference_nodes, equispaced_reference)
        ):
            # Preserve the historical global coordinate construction exactly
            # for the legacy count-based uniform partition.  This is a topology
            # property, not a dependency on a concrete shape-function family.
            n_nodes = n_elements * (local_size - 1) + 1
            nodes_array = np.linspace(
                x_start,
                x_end,
                n_nodes,
                dtype=float,
            )

            for element_index in range(n_elements):
                first = element_index * (local_size - 1)
                node_ids = tuple(range(first, first + local_size))
                coordinates = tuple(
                    float(nodes_array[node_id]) for node_id in node_ids
                )
                elements.append(
                    LongitudinalElement1D(
                        index=element_index,
                        node_ids=node_ids,
                        coordinates=coordinates,
                        basis=basis,
                    )
                )

            nodes = tuple(float(value) for value in nodes_array)
        else:
            # Generic partition path.  The FEM owns the normalized partition
            # and its mapping to physical element boundaries; the longitudinal
            # basis owns only reference-space trace locations and shape functions.
            nodes_list = []
            previous_last_node = None

            for element_index in range(n_elements):
                a = float(boundaries[element_index])
                b = float(boundaries[element_index + 1])
                coordinates_array = (
                    0.5 * (1.0 - reference_nodes) * a
                    + 0.5 * (1.0 + reference_nodes) * b
                )
                coordinates_array[0] = a
                coordinates_array[-1] = b
                coordinates = tuple(
                    float(value) for value in coordinates_array
                )

                local_ids = []
                if previous_last_node is None:
                    first_node = len(nodes_list)
                    nodes_list.append(coordinates[0])
                else:
                    first_node = int(previous_last_node)
                local_ids.append(first_node)

                for coordinate in coordinates[1:]:
                    local_ids.append(len(nodes_list))
                    nodes_list.append(float(coordinate))

                element = LongitudinalElement1D(
                    index=element_index,
                    node_ids=tuple(local_ids),
                    coordinates=coordinates,
                    basis=basis,
                )
                elements.append(element)
                previous_last_node = local_ids[-1]

            nodes = tuple(nodes_list)

        return LongitudinalMesh1D(
            x_start=x_start,
            x_end=x_end,
            nodes=nodes,
            elements=tuple(elements),
            basis=basis,
        )


# =============================================================================
# Generic longitudinal element integration
# =============================================================================

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

        size = element.local_size
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

        size = element.local_size
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

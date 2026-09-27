# CSF-CUF: longitudinal product-cache optimization.
# Derived from the tested reference supplied in cuf_longitudinal_products.zip.
# This is not a verified checkout of the current upstream main branch.
# Retains the GPL license supplied with that package; see COPYING.
# Original reference SHA256: 74ec9dd39a7f95e5e7ae15852fb9b29720cd11d4a81c945f0d6fe36f5bb4325f

"""
Generic CSF-CUF longitudinal element matrix construction.

This module connects two already-generic layers:

    FundamentalNucleusProvider
        -> x-independent NucleusTermDefinition objects
        -> generalized sectional coefficient J(x)

and

    LongitudinalIntegrator
        -> N_a(x), dN_a/dx
        -> element integration

to produce the complete local CUF matrix for one longitudinal element and one
ordered CUF pair (tau, s).
No global assembly, boundary-condition application, load assembly, or linear
solution is performed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from csf.cuf.core.nucleus import (
    FundamentalNucleusProvider,
    JSignature,
    NucleusTermDefinition,
)
from csf.cuf.solver.longitudinal import (
    LongitudinalElement1D,
    LongitudinalIntegrator,
)

@dataclass(frozen=True)
class ElementCUFBlock:
    """
    One component block of a local CUF element matrix.

    ``matrix`` has size m x m, where m is the local longitudinal basis size.
    """

    test_component: int
    trial_component: int
    matrix: np.ndarray


@dataclass(frozen=True)
class ElementCUFMatrix:
    """
    Complete 3x3 component block matrix for one (tau, s) pair.

    Blocks are ordered by displacement components (x, y, z).
    """
    tau: int
    s: int
    element_index: int
    blocks: Tuple[Tuple[ElementCUFBlock, ...], ...]

    def block(
        self,
        test_component: int,
        trial_component: int,
    ) -> np.ndarray:
        return self.blocks[test_component][trial_component].matrix

    def dense_component_major(self) -> np.ndarray:
        """
        Return the local matrix in component-major ordering:

            [x-node dofs, y-node dofs, z-node dofs].
        """
        return np.block(
            [
                [
                    self.blocks[i][j].matrix
                    for j in range(3)
                ]
                for i in range(3)
            ]
        )


class CUFElementMatrixBuilder:
    """
    Build local CUF matrices while preserving the full x-dependence of J(x).

    The builder never freezes J at an element midpoint. Each scalar coefficient
    is queried by the longitudinal integrator at its quadrature coordinates.
    """
    def __init__(
        self,
        *,
        nucleus: FundamentalNucleusProvider,
        integrator: LongitudinalIntegrator,
    ) -> None:
        if not isinstance(nucleus, FundamentalNucleusProvider):
            raise TypeError(
                "nucleus must be a FundamentalNucleusProvider"
            )

        if not isinstance(integrator, LongitudinalIntegrator):
            raise TypeError(
                "integrator must implement LongitudinalIntegrator"
            )
        self.nucleus = nucleus
        self.integrator = integrator

        # Longitudinal shape functions depend only on the element and on the
        # longitudinal quadrature points, not on the CUF pair (tau, s).
        # Assembly visits all CUF pairs of the same element consecutively, so
        # keep a one-element cache and reuse these quantities across pairs.
        self._cached_longitudinal_element = None
        self._cached_longitudinal_quadrature_data = None
    def _longitudinal_quadrature_data(
        self,
        element: LongitudinalElement1D,
    ):
        """
        Return longitudinal quadrature data reusable by every CUF pair.

        The mapped coordinate, longitudinal shape values, physical
        derivatives, and integration scale depend on the element and the
        longitudinal quadrature only. They are therefore computed once for
        the current element instead of once for every (tau, s) pair.
        """
        if self._cached_longitudinal_element is element:
            return self._cached_longitudinal_quadrature_data

        jacobian = element.jacobian
        data = []

        for xi, weight in zip(
            self.integrator.points,
            self.integrator.weights,
        ):
            xi = float(xi)
            data.append(
                (
                    element.map_to_physical(xi),
                    {
                        0: element.shape_values(xi),
                        1: element.shape_derivatives_physical(xi),
                    },
                    float(weight) * jacobian,
                )
            )

        data = tuple(data)
        self._cached_longitudinal_element = element
        self._cached_longitudinal_quadrature_data = data
        return data
    def build_pair(
        self,
        *,
        element: LongitudinalElement1D,
        tau: int,
        s: int,
    ) -> ElementCUFMatrix:
        """
        Build the complete local 3x3 component matrix for one (tau, s) pair.
        When the sectional provider exposes ``J_batch`` and the longitudinal
        integrator exposes Gauss points/weights, all nucleus coefficients at a
        longitudinal quadrature point are integrated together. Custom backends
        retain the original scalar path automatically.
        """

        sectional = self.nucleus.sectional_coefficients
        if (
            hasattr(sectional, "J_batch")
            and hasattr(self.integrator, "points")
            and hasattr(self.integrator, "weights")
        ):
            return self._build_pair_batched(
                element=element,
                tau=tau,
                s=s,
            )

        return self._build_pair_scalar(
            element=element,
            tau=tau,
            s=s,
        )
    def _build_pair_scalar(
        self,
        *,
        element: LongitudinalElement1D,
        tau: int,
        s: int,
    ) -> ElementCUFMatrix:
        blocks = []

        for test_component in range(3):
            row = []
            for trial_component in range(3):
                matrix = self._build_component_block(
                    element=element,
                    tau=tau,
                    s=s,
                    test_component=test_component,
                    trial_component=trial_component,
                )
                row.append(
                    ElementCUFBlock(
                        test_component=test_component,
                        trial_component=trial_component,
                        matrix=matrix,
                    )
                )

            blocks.append(tuple(row))

        return ElementCUFMatrix(
            tau=tau,
            s=s,
            element_index=element.index,
            blocks=tuple(blocks),
        )
    def _longitudinal_product_data(self, element):
        """Reuse unweighted shape products for the current quadrature-data object.

        This adds no stronger invariance assumption than the existing shape cache.
        A new tuple from _longitudinal_quadrature_data invalidates this cache, even
        for the same element object. Only one element's products are retained.
        Quadrature weights and sectional coefficients are NOT folded into products,
        preserving the original floating-point multiplication and accumulation order.
        """
        longitudinal_data = self._longitudinal_quadrature_data(element)
        if getattr(self, "_cached_longitudinal_product_source", None) is longitudinal_data:
            return self._cached_longitudinal_products

        data = []
        for x, shape_operator, scale in longitudinal_data:
            products = {}
            for test_order, test_values in shape_operator.items():
                for trial_order, trial_values in shape_operator.items():
                    product = np.outer(test_values, trial_values)
                    product.setflags(write=False)
                    products[(test_order, trial_order)] = product
            data.append((x, products, scale))

        products_data = tuple(data)
        self._cached_longitudinal_product_source = longitudinal_data
        self._cached_longitudinal_products = products_data
        return products_data

    def _build_pair_batched(
        self,
        *,
        element: LongitudinalElement1D,
        tau: int,
        s: int,
    ) -> ElementCUFMatrix:
        """
        Batched quadrature for all 9 component blocks of one (tau,s) pair.
        """

        definitions = {}
        unique_signatures = []
        seen_signatures = set()
        for test_component in range(3):
            for trial_component in range(3):
                block_definitions = self.nucleus.K_block_structure(
                    tau=tau,
                    s=s,
                    test_component=test_component,
                    trial_component=trial_component,
                )

                definitions[
                    (test_component, trial_component)
                ] = block_definitions
                for definition in block_definitions:
                    signature = definition.signature

                    if signature not in seen_signatures:
                        seen_signatures.add(signature)
                        unique_signatures.append(signature)

        size = element.local_size

        matrices = {
            (i, j): np.zeros((size, size), dtype=float)
            for i in range(3)
            for j in range(3)
        }
        sectional = self.nucleus.sectional_coefficients
        longitudinal_data = self._longitudinal_product_data(element)

        for x, shape_products, scale in longitudinal_data:
            values = sectional.J_batch(
                x=x,
                signatures=tuple(unique_signatures),
            )

            coefficient_by_signature = dict(
                zip(unique_signatures, values)
            )
            for block_key, block_definitions in definitions.items():
                matrix = matrices[block_key]

                for definition in block_definitions:
                    coefficient = coefficient_by_signature[
                        definition.signature
                    ]
                    matrix += (
                        scale
                        * coefficient
                        * shape_products[(definition.test_x_order, definition.trial_x_order)]
                    )

        blocks = []
        for test_component in range(3):
            row = []

            for trial_component in range(3):
                row.append(
                    ElementCUFBlock(
                        test_component=test_component,
                        trial_component=trial_component,
                        matrix=matrices[
                            (test_component, trial_component)
                        ],
                    )
                )

            blocks.append(tuple(row))
        return ElementCUFMatrix(
            tau=tau,
            s=s,
            element_index=element.index,
            blocks=tuple(blocks),
        )
    def _build_component_block(
        self,
        *,
        element: LongitudinalElement1D,
        tau: int,
        s: int,
        test_component: int,
        trial_component: int,
    ) -> np.ndarray:
        definitions = self.nucleus.K_block_structure(
            tau=tau,
            s=s,
            test_component=test_component,
            trial_component=trial_component,
        )

        size = element.local_size
        block = np.zeros((size, size), dtype=float)
        for definition in definitions:
            coefficient = self._coefficient_field(
                definition.signature
            )

            block += self.integrator.integrate_bilinear(
                element=element,
                coefficient=coefficient,
                test_x_order=definition.test_x_order,
                trial_x_order=definition.trial_x_order,
            )

        return block
    def _coefficient_field(
        self,
        signature: JSignature,
    ):
        """
        Return a scalar field x -> J_signature(x).
        """
        def field(x: float) -> float:
            return self.nucleus.sectional_coefficients.J(
                x=x,
                tau=signature.tau,
                test_derivative=signature.test_derivative,
                s=signature.s,
                trial_derivative=signature.trial_derivative,
                m=signature.m,
                n=signature.n,
            )

        return field

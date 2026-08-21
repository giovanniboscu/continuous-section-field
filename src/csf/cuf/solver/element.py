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

    ``matrix`` has size (p+1) x (p+1), where p is the longitudinal element
    interpolation order.
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

        size = element.order + 1

        matrices = {
            (i, j): np.zeros((size, size), dtype=float)
            for i in range(3)
            for j in range(3)
        }

        jacobian = element.jacobian
        points = self.integrator.points
        weights = self.integrator.weights

        sectional = self.nucleus.sectional_coefficients

        for xi, weight in zip(points, weights):
            xi = float(xi)
            x = element.map_to_physical(xi)

            values = sectional.J_batch(
                x=x,
                signatures=tuple(unique_signatures),
            )

            coefficient_by_signature = dict(
                zip(unique_signatures, values)
            )

            shape_operator = {
                0: element.shape_values(xi),
                1: element.shape_derivatives_physical(xi),
            }

            scale = float(weight) * jacobian

            for block_key, block_definitions in definitions.items():
                matrix = matrices[block_key]

                for definition in block_definitions:
                    coefficient = coefficient_by_signature[
                        definition.signature
                    ]

                    matrix += (
                        scale
                        * coefficient
                        * np.outer(
                            shape_operator[
                                definition.test_x_order
                            ],
                            shape_operator[
                                definition.trial_x_order
                            ],
                        )
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

        size = element.order + 1
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

# Version: CSF-CUF optional MITC diagnostics v08 - 2026-10-11
# Changelog: one configuration line; opt-in factor diagnostics; leave K/J_batch and verification unchanged.
# Version: CSF-CUF MITC verification activation v07 - 2026-10-11
# Changelog: print effective builder MITC/verification flags at initialization.
# Version: CSF-CUF MITC assembly verification v06 - 2026-10-11
# Changelog: independent local matrix reconstruction and discrepancy report; solver matrix untouched.
# Version: CSF-CUF selectable MITC diagnostic v05 - 2026-10-11
# Changelog: Per-element diagnostic of ordinary vs MITC longitudinal shear factors; assembly unchanged.
# Version: CSF-CUF selectable MITC v04 - 2026-10-11
# Changelog: default classical path, opt-in MITC; keep J_batch unchanged.
# Version: CSF-CUF MITC longitudinal shear factors v03 - 2026-10-11
# Changelog: Substitute Barlow-interpolated longitudinal shear factors while
# retaining the original J_batch sectional integration and CUF block assembly.
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
        correctionMITC: bool = False,
        verifyMITCAssembly: bool = False,
        mitcDiagnostic: bool = False,
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
        if not isinstance(correctionMITC, bool):
            raise TypeError("correctionMITC must be a bool")
        self.correctionMITC = correctionMITC
        if not isinstance(verifyMITCAssembly, bool):
            raise TypeError("verifyMITCAssembly must be a bool")
        self.verifyMITCAssembly = verifyMITCAssembly
        if not isinstance(mitcDiagnostic, bool):
            raise TypeError("mitcDiagnostic must be a bool")
        self.mitcDiagnostic = mitcDiagnostic
        self._verified_mitc_elements = set()
        print(
            f"[MITC] correctionMITC={self.correctionMITC} "
            f"mitcDiagnostic={self.mitcDiagnostic} "
            f"verifyMITCAssembly={self.verifyMITCAssembly}",
            flush=True,
        )

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

        if not self.correctionMITC:
            return self._build_pair_scalar(element=element, tau=tau, s=s)
        raise TypeError(
            "MITC longitudinal-factor assembly requires J_batch and "
            "a longitudinal integrator exposing points and weights"
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
        """Cache ordinary and MITC longitudinal products for this element.

        The Barlow reconstruction changes only the longitudinal factors of
        the shear strains (Voigt rows 5 and 6); generalized sectional
        coefficients J(x) and their integration remain unchanged.
        """
        longitudinal_data = self._longitudinal_quadrature_data(element)
        if getattr(self, "_cached_longitudinal_product_source", None) is longitudinal_data:
            return self._cached_longitudinal_products

        if not self.correctionMITC:
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

        from csf.cuf.solver.longitudinal_tying_points import (
            LongitudinalTyingPointSelector,
        )

        basis = element.basis
        interpolate = getattr(basis, "interpolation_values", None)
        if not callable(interpolate):
            raise TypeError(
                "MITC requires longitudinal basis.interpolation_values(xi, nodes)"
            )
        points = LongitudinalTyingPointSelector().points(
            criterion="barlow",
            longitudinal_degree=int(basis.polynomial_degree),
        )
        samples = {
            0: np.asarray([element.shape_values(float(xi)) for xi in points]),
            1: np.asarray([
                element.shape_derivatives_physical(float(xi)) for xi in points
            ]),
        }
        data = []
        # Optional diagnostics use exactly the stiffness factors; the entire
        # audit (including allocating temporary outer products) is skipped
        # when mitcDiagnostic is false.
        diagnostic = None
        if self.mitcDiagnostic:
            diagnostic = {
                name: {"max_abs": 0.0, "sum_diff2": 0.0, "sum_ref2": 0.0, "count": 0}
                for name in ("N", "dNdx", "N*N", "N*dNdx", "dNdx*dNdx")
            }

            def observe(name, baseline, corrected):
                baseline = np.asarray(baseline, dtype=float)
                corrected = np.asarray(corrected, dtype=float)
                difference = corrected - baseline
                item = diagnostic[name]
                item["max_abs"] = max(item["max_abs"], float(np.max(np.abs(difference))))
                item["sum_diff2"] += float(np.sum(difference * difference))
                item["sum_ref2"] += float(np.sum(baseline * baseline))
                item["count"] += difference.size

        for xi, (x, ordinary, scale) in zip(self.integrator.points, longitudinal_data):
            weights = np.asarray(interpolate(float(xi), points), dtype=float)
            if weights.shape != points.shape or not np.all(np.isfinite(weights)):
                raise ValueError("MITC tying interpolation returned invalid weights")
            modified = {order: weights @ values for order, values in samples.items()}
            if diagnostic is not None:
                observe("N", ordinary[0], modified[0])
                observe("dNdx", ordinary[1], modified[1])
                for label, left_order, right_order in (
                    ("N*N", 0, 0),
                    ("N*dNdx", 0, 1),
                    ("dNdx*dNdx", 1, 1),
                ):
                    observe(
                        label,
                        np.outer(ordinary[left_order], ordinary[right_order]),
                        np.outer(modified[left_order], modified[right_order]),
                    )
            products = {}
            for test_order, test_values in ordinary.items():
                for trial_order, trial_values in ordinary.items():
                    product = np.outer(test_values, trial_values)
                    product.setflags(write=False)
                    # Retain existing keys for the ordinary longitudinal product.
                    products[(test_order, trial_order)] = product
                    products[(False, False, test_order, trial_order)] = product

                    for test_shear, trial_shear in ((True, False), (False, True), (True, True)):
                        left = modified[test_order] if test_shear else test_values
                        right = modified[trial_order] if trial_shear else trial_values
                        shear_product = np.outer(left, right)
                        shear_product.setflags(write=False)
                        products[(test_shear, trial_shear, test_order, trial_order)] = shear_product
            data.append((x, products, scale))

        products_data = tuple(data)
        self._cached_longitudinal_product_source = longitudinal_data
        self._cached_longitudinal_products = products_data
        if diagnostic is not None:
            print(
                f"[MITC] element={element.index} degree={int(basis.polynomial_degree)} "
                f"tying={points.tolist()} stiffness=MODIFIED integration=J_batch",
                flush=True,
            )
            print(f"[MITC diagnostic] element={element.index} Gauss_points={len(data)}", flush=True)
            for name, item in diagnostic.items():
                rms_abs = (item["sum_diff2"] / item["count"]) ** 0.5
                relative_l2 = (
                    (item["sum_diff2"] / item["sum_ref2"]) ** 0.5
                    if item["sum_ref2"] > 0.0 else float("nan")
                )
                print(
                    f"  {name:13s} max_abs={item['max_abs']:.6e} "
                    f"rms_abs={rms_abs:.6e} rel_L2={relative_l2:.6e}",
                    flush=True,
                )
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
                    if self.correctionMITC:
                        product_key = (
                            definition.signature.m in (5, 6),
                            definition.signature.n in (5, 6),
                            definition.test_x_order,
                            definition.trial_x_order,
                        )
                    else:
                        product_key = (
                            definition.test_x_order,
                            definition.trial_x_order,
                        )
                    matrix += (scale * coefficient * shape_products[product_key])

        if self.correctionMITC and self.verifyMITCAssembly and element.index not in self._verified_mitc_elements:
            self._verify_mitc_pair_assembly(element, tau, s, definitions, matrices)
            self._verified_mitc_elements.add(element.index)

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
    def _verify_mitc_pair_assembly(self, element, tau, s, definitions, assembled):
        """Independent Barlow reconstruction, compared against the cached J_batch path.

        Exactly one ordered CUF pair per longitudinal element is audited, including
        all 9 component blocks and all B/S constitutive couplings. This reference
        uses direct Lagrange interpolation, not the cached products or the
        longitudinal-basis interpolation routine used by the production path.
        Sectional coefficients remain supplied by unchanged J_batch(x_gauss).
        """
        from csf.cuf.solver.longitudinal_tying_points import LongitudinalTyingPointSelector

        points = np.asarray(LongitudinalTyingPointSelector().points(
            criterion="barlow", longitudinal_degree=int(element.basis.polynomial_degree)
        ), dtype=float)
        if len(points) == 0:
            raise ValueError("MITC verification has no Barlow points")

        tying_0 = np.asarray([element.shape_values(float(t)) for t in points], dtype=float)
        tying_1 = np.asarray([element.shape_derivatives_physical(float(t)) for t in points], dtype=float)
        size = element.local_size
        reference = {(i, j): np.zeros((size, size), dtype=float)
                     for i in range(3) for j in range(3)}
        signatures = tuple(dict.fromkeys(term.signature
                          for terms in definitions.values() for term in terms))
        for xi, w in zip(self.integrator.points, self.integrator.weights):
            xi = float(xi)
            # Independent Lagrange cardinal polynomial evaluation.
            weights = np.ones(len(points), dtype=float)
            for m in range(len(points)):
                for k in range(len(points)):
                    if k != m:
                        weights[m] *= (xi - points[k]) / (points[m] - points[k])
            ordinary = {0: np.asarray(element.shape_values(xi)),
                        1: np.asarray(element.shape_derivatives_physical(xi))}
            assumed = {0: np.einsum('m,mi->i', weights, tying_0),
                       1: np.einsum('m,mi->i', weights, tying_1)}
            xg = element.map_to_physical(xi)
            coeffs = dict(zip(signatures, self.nucleus.sectional_coefficients.J_batch(
                x=xg, signatures=signatures)))
            scale = float(w) * element.jacobian
            for key, terms in definitions.items():
                for term in terms:
                    test_shear = term.signature.m in (5, 6)
                    trial_shear = term.signature.n in (5, 6)
                    left = (assumed if test_shear else ordinary)[term.test_x_order]
                    right = (assumed if trial_shear else ordinary)[term.trial_x_order]
                    reference[key] += scale * coeffs[term.signature] * np.outer(left, right)

        total_diff2 = total_ref2 = 0.0
        largest = (0.0, None)
        for key in sorted(reference):
            difference = assembled[key] - reference[key]
            maxabs = float(np.max(np.abs(difference)))
            total_diff2 += float(np.sum(difference ** 2))
            total_ref2 += float(np.sum(reference[key] ** 2))
            if maxabs > largest[0]:
                largest = (maxabs, key)
        relative = (total_diff2 / total_ref2) ** 0.5 if total_ref2 else (total_diff2 ** 0.5)
        print(f"[MITC assembly verify] element={element.index} pair=({tau},{s}) "
              f"blocks=9 max_abs={largest[0]:.6e} rel_F={relative:.6e} "
              f"worst_block={largest[1]} status={'PASS' if relative <= 1e-9 else 'DIFF'}",
              flush=True)

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

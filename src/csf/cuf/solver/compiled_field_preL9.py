# Version: CSF-CUF compiled displacement field v21 - 2026-09-23
"""Pure compiled representation of the solved CUF displacement field.

The ``.cuf.npz`` checkpoint stores only the data required to reconstruct the
continuous solved displacement field

    u_i(x, y, z)

for ``i = x, y, z``.  No CSF geometry, material data, constitutive provider,
constitutive matrix, stress data, or recovery context is persisted.

The physical field is represented by the solved element coefficients together
with the longitudinal and transverse polynomial representations needed to
evaluate it exactly.  Three transverse representations are supported:

Version 1 (static transverse polynomial):

    F_tau(y,z) = sum_{p,q} C[tau-1,p,q] y**p z**q.

Version 2 (smooth longitudinally varying transverse polynomial):

    F_tau(x,y,z) = sum_{r,p,q} C[tau-1,r,p,q] x**r y**p z**q.

Version 3 (piecewise transverse polynomial):

    F_tau^(k)(y,z) = sum_{p,q} C[k,tau-1,p,q] y**p z**q.

Analytical derivatives of ``u_i`` with respect to ``x``, ``y`` and ``z`` are
evaluated directly from these polynomial coefficients.  Derivative samples are
not stored in the checkpoint.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile

import numpy as np


_FORMAT_NAME = "csf-cuf-compiled-displacement"
_STATIC_FORMAT_VERSION = 1
_VARIABLE_FORMAT_VERSION = 2
_SEGMENTED_FORMAT_VERSION = 3
_SUPPORTED_FORMAT_VERSIONS = {
    _STATIC_FORMAT_VERSION,
    _VARIABLE_FORMAT_VERSION,
    _SEGMENTED_FORMAT_VERSION,
}


class CompiledDisplacementField:
    """Self-contained callable representation of the solved displacement."""

    def __init__(
        self,
        *,
        element_x_starts,
        element_x_ends,
        element_coefficients,
        longitudinal_shape_coefficients,
        transverse_power_coefficients=None,
        transverse_x_power_coefficients=None,
        transverse_segment_boundaries=None,
        transverse_segment_power_coefficients=None,
        metadata=None,
    ) -> None:
        self._element_x_starts = np.asarray(element_x_starts, dtype=float)
        self._element_x_ends = np.asarray(element_x_ends, dtype=float)
        self._element_coefficients = np.asarray(element_coefficients, dtype=float)
        self._longitudinal_shape_coefficients = np.asarray(
            longitudinal_shape_coefficients,
            dtype=float,
        )

        if transverse_power_coefficients is None:
            self._transverse_power_coefficients = None
        else:
            self._transverse_power_coefficients = np.asarray(
                transverse_power_coefficients,
                dtype=float,
            )

        if transverse_x_power_coefficients is None:
            self._transverse_x_power_coefficients = None
        else:
            self._transverse_x_power_coefficients = np.asarray(
                transverse_x_power_coefficients,
                dtype=float,
            )

        if transverse_segment_boundaries is None:
            self._transverse_segment_boundaries = None
        else:
            self._transverse_segment_boundaries = np.asarray(
                transverse_segment_boundaries,
                dtype=float,
            )

        if transverse_segment_power_coefficients is None:
            self._transverse_segment_power_coefficients = None
        else:
            self._transverse_segment_power_coefficients = np.asarray(
                transverse_segment_power_coefficients,
                dtype=float,
            )


        self._metadata = dict(metadata or {})
        self._validate()

        values = [
            self._element_x_starts,
            self._element_x_ends,
            self._element_coefficients,
            self._longitudinal_shape_coefficients,
        ]
        if self._transverse_power_coefficients is not None:
            values.append(self._transverse_power_coefficients)
        if self._transverse_x_power_coefficients is not None:
            values.append(self._transverse_x_power_coefficients)
        if self._transverse_segment_boundaries is not None:
            values.append(self._transverse_segment_boundaries)
        if self._transverse_segment_power_coefficients is not None:
            values.append(self._transverse_segment_power_coefficients)
        for value in values:
            value.setflags(write=False)

    @staticmethod
    def _basis_has_longitudinal_dependence(basis) -> bool:
        marker = getattr(basis, "provides_longitudinal_derivative", None)
        if marker is None:
            marker = callable(getattr(basis, "longitudinal_derivative", None))
        return bool(marker)

    @staticmethod
    def _static_transverse_power_coefficients(basis):
        """Reconstruct one longitudinally constant polynomial basis."""

        if CompiledDisplacementField._basis_has_longitudinal_dependence(basis):
            return None

        try:
            order = int(basis.order)
            size = int(basis.size)
            y_scale, z_scale = map(float, basis.scales)
        except (AttributeError, TypeError, ValueError):
            return None

        if order < 0 or size < 1:
            return None
        if (
            not np.isfinite(y_scale)
            or not np.isfinite(z_scale)
            or y_scale <= 0.0
            or z_scale <= 0.0
        ):
            return None

        count = order + 1
        if count == 1:
            points = np.asarray((0.0,), dtype=float)
        else:
            points = np.polynomial.chebyshev.chebpts2(count)

        vandermonde = np.polynomial.chebyshev.chebvander(points, order)
        inverse_vandermonde = np.linalg.inv(vandermonde)
        values = np.empty((size, count, count), dtype=float)

        for iy, normalized_y in enumerate(points):
            y = y_scale * float(normalized_y)
            for iz, normalized_z in enumerate(points):
                z = z_scale * float(normalized_z)
                if hasattr(basis, "values"):
                    current = np.asarray(basis.values(y, z), dtype=float)
                else:
                    current = np.asarray(
                        [
                            basis.value(tau, y, z)
                            for tau in range(1, size + 1)
                        ],
                        dtype=float,
                    )
                if current.shape != (size,):
                    raise ValueError("transverse basis evaluation has invalid shape")
                values[:, iy, iz] = current

        chebyshev_coefficients = np.einsum(
            "ai,tij,bj->tab",
            inverse_vandermonde,
            values,
            inverse_vandermonde,
            optimize=True,
        )

        conversion = np.zeros((count, count), dtype=float)
        for degree in range(count):
            unit = np.zeros(count, dtype=float)
            unit[degree] = 1.0
            polynomial = np.polynomial.chebyshev.cheb2poly(unit)
            conversion[: polynomial.size, degree] = polynomial

        normalized_power_coefficients = np.einsum(
            "pa,tab,qb->tpq",
            conversion,
            chebyshev_coefficients,
            conversion,
            optimize=True,
        )

        y_scaling = np.power(y_scale, -np.arange(count, dtype=float))
        z_scaling = np.power(z_scale, -np.arange(count, dtype=float))
        coefficients = (
            normalized_power_coefficients
            * y_scaling[None, :, None]
            * z_scaling[None, None, :]
        )

        if not np.all(np.isfinite(coefficients)):
            raise ValueError(
                "compiled transverse polynomial contains non-finite values"
            )
        return np.asarray(coefficients, dtype=float)

    @staticmethod
    def _variable_transverse_x_power_coefficients(basis):
        """Compile the current longitudinal Lagrange blend exactly.

        The blend basis exposes ``states`` and ``x_nodes``.  Each child state
        must itself be a longitudinally constant polynomial basis.  The
        returned array has shape ``(tau, x_power, y_power, z_power)``.
        """

        try:
            states = tuple(basis.states)
            x_nodes = np.asarray(basis.x_nodes, dtype=float)
            global_size = int(basis.size)
        except (AttributeError, TypeError, ValueError):
            return None

        if not states or x_nodes.shape != (len(states),):
            return None
        if not np.all(np.isfinite(x_nodes)) or np.unique(x_nodes).size != x_nodes.size:
            return None
        if global_size < 1:
            return None

        child_coefficients = []
        max_y_count = 0
        max_z_count = 0
        for state in states:
            child_basis = getattr(state, "basis", None)
            if child_basis is None:
                return None
            current = CompiledDisplacementField._static_transverse_power_coefficients(
                child_basis
            )
            if current is None:
                return None
            child_coefficients.append(current)
            max_y_count = max(max_y_count, int(current.shape[1]))
            max_z_count = max(max_z_count, int(current.shape[2]))

        lagrange_x = CompiledDisplacementField._cardinal_lagrange_power_coefficients(x_nodes)
        x_count = int(lagrange_x.shape[1])
        result = np.zeros(
            (global_size, x_count, max_y_count, max_z_count),
            dtype=float,
        )

        for state_index, current in enumerate(child_coefficients):
            local_size = int(current.shape[0])
            if local_size > global_size:
                return None
            result[
                :local_size,
                :,
                : current.shape[1],
                : current.shape[2],
            ] += (
                lagrange_x[state_index][None, :, None, None]
                * current[:, None, :, :]
            )

        if not np.all(np.isfinite(result)):
            raise ValueError(
                "compiled longitudinally variable transverse polynomial "
                "contains non-finite values"
            )
        return result

    @staticmethod
    def _segmented_transverse_power_coefficients(basis):
        """Compile a piecewise transverse basis into physical coefficients.

        The checkpoint intentionally stores no expansion object or expansion
        definition.  Only segment boundaries and the polynomial coefficients
        needed to evaluate the physical field are persisted.
        """

        try:
            segments = tuple(basis.segments)
            boundaries = np.asarray(basis.boundaries, dtype=float)
            global_size = int(basis.size)
        except (AttributeError, TypeError, ValueError):
            return None

        if not segments or boundaries.shape != (len(segments) + 1,):
            return None
        if global_size < 1:
            return None
        if not np.all(np.isfinite(boundaries)) or np.any(np.diff(boundaries) <= 0.0):
            return None

        child_coefficients = []
        max_y_count = 0
        max_z_count = 0
        for segment in segments:
            child_basis = getattr(segment, "basis", None)
            if child_basis is None:
                return None
            current = CompiledDisplacementField._static_transverse_power_coefficients(
                child_basis
            )
            if current is None:
                return None
            if int(current.shape[0]) > global_size:
                return None
            child_coefficients.append(current)
            max_y_count = max(max_y_count, int(current.shape[1]))
            max_z_count = max(max_z_count, int(current.shape[2]))

        result = np.zeros(
            (len(segments), global_size, max_y_count, max_z_count),
            dtype=float,
        )
        for segment_index, current in enumerate(child_coefficients):
            result[
                segment_index,
                : current.shape[0],
                : current.shape[1],
                : current.shape[2],
            ] = current

        if not np.all(np.isfinite(result)):
            raise ValueError(
                "compiled segmented transverse polynomial contains non-finite values"
            )

        return np.asarray(boundaries, dtype=float), result

    # Backward-compatible private name used by older local code/tests.
    _transverse_power_coefficients = _static_transverse_power_coefficients

    @classmethod
    def from_solution_data(
        cls,
        *,
        mesh,
        dof_layout,
        solved_dofs,
        basis,
        section_provider=None,
        constitutive_provider=None,
        metadata=None,
    ):
        """Compile solved FE/CUF coefficients into a reusable field.

        Static polynomial bases use checkpoint v1.  Smooth longitudinal
        polynomial dependence uses v2.  Piecewise transverse laws use v3.
        Unsupported expansions return ``None`` and remain on the normal
        in-memory path.

        ``section_provider`` and ``constitutive_provider`` are accepted only
        for compatibility with the solver call signature.  They are deliberately
        ignored and are never retained or written to the displacement checkpoint.
        """

        _ = section_provider, constitutive_provider

        solved_dofs = np.asarray(solved_dofs, dtype=float)
        if solved_dofs.shape != (dof_layout.total_dofs,):
            raise ValueError("solved_dofs size is inconsistent with DOF layout")
        if not np.all(np.isfinite(solved_dofs)):
            raise ValueError("solved_dofs contains non-finite values")

        elements = tuple(mesh.elements)
        if not elements:
            raise ValueError("compiled displacement requires an element")

        local_node_count = len(elements[0].node_ids)
        if any(len(element.node_ids) != local_node_count for element in elements):
            raise ValueError("compiled displacement requires one longitudinal order")

        if getattr(dof_layout, "is_uniform", True):
            element_coefficients = np.empty(
                (
                    len(elements),
                    local_node_count,
                    dof_layout.basis_size,
                    3,
                ),
                dtype=float,
            )
            for element_index, element in enumerate(elements):
                for local_node, global_node in enumerate(element.node_ids):
                    first = global_node * dof_layout.dofs_per_node
                    last = first + dof_layout.dofs_per_node
                    element_coefficients[element_index, local_node, :, :] = (
                        solved_dofs[first:last].reshape(dof_layout.basis_size, 3)
                    )
        else:
            # Serialization container only: inactive slots are exactly zero and
            # element_basis_sizes records the physical ragged trace size.  No
            # padded algebraic DOFs exist in the solved system.
            element_coefficients = np.zeros(
                (
                    len(elements),
                    local_node_count,
                    dof_layout.basis_size,
                    3,
                ),
                dtype=float,
            )
            for element_index, element in enumerate(elements):
                active_size = dof_layout.basis_size_at_node(element.node_ids[0])
                for local_node, global_node in enumerate(element.node_ids):
                    for tau in range(1, active_size + 1):
                        for component in range(3):
                            dof = dof_layout.index(
                                node=global_node, tau=tau, component=component
                            )
                            element_coefficients[
                                element_index, local_node, tau - 1, component
                            ] = solved_dofs[dof]

        longitudinal_exporter = getattr(
            elements[0].basis,
            "power_coefficients",
            None,
        )
        if not callable(longitudinal_exporter):
            return None
        longitudinal_coefficients = longitudinal_exporter()
        if longitudinal_coefficients is None:
            return None
        longitudinal_coefficients = np.asarray(
            longitudinal_coefficients,
            dtype=float,
        )
        if (
            longitudinal_coefficients.ndim != 2
            or longitudinal_coefficients.shape[0] != local_node_count
            or not np.all(np.isfinite(longitudinal_coefficients))
        ):
            raise ValueError(
                "longitudinal basis power_coefficients() returned an invalid "
                "checkpoint representation"
            )

        transverse_coefficients = cls._static_transverse_power_coefficients(basis)
        transverse_x_coefficients = None
        transverse_segment_boundaries = None
        transverse_segment_coefficients = None
        format_version = _STATIC_FORMAT_VERSION
        if transverse_coefficients is None:
            segmented = cls._segmented_transverse_power_coefficients(basis)
            if segmented is not None:
                (
                    transverse_segment_boundaries,
                    transverse_segment_coefficients,
                ) = segmented
                format_version = _SEGMENTED_FORMAT_VERSION
            else:
                transverse_x_coefficients = cls._variable_transverse_x_power_coefficients(
                    basis
                )
                if transverse_x_coefficients is None:
                    return None
                format_version = _VARIABLE_FORMAT_VERSION

        combined_metadata = dict(metadata or {})
        combined_metadata.update(
            {
                "format": _FORMAT_NAME,
                "format_version": format_version,
                "basis_class": (
                    f"{basis.__class__.__module__}.{basis.__class__.__qualname__}"
                ),
                "basis_order": int(basis.order),
                "basis_size": int(basis.size),
                "longitudinal_basis_class": (
                    f"{elements[0].basis.__class__.__module__}."
                    f"{elements[0].basis.__class__.__qualname__}"
                ),
                "longitudinal_basis_order": int(elements[0].basis.order),
                "longitudinal_basis_size": int(elements[0].basis.size),
                "components": ["ux", "uy", "uz"],
                "element_basis_sizes": [
                    int(dof_layout.basis_size_at_node(element.node_ids[0]))
                    for element in elements
                ],
            }
        )
        if format_version == _VARIABLE_FORMAT_VERSION:
            combined_metadata["transverse_representation"] = "x_y_z_power"
        elif format_version == _SEGMENTED_FORMAT_VERSION:
            combined_metadata["transverse_representation"] = "piecewise_y_z_power"
        else:
            combined_metadata["transverse_representation"] = "y_z_power"

        return cls(
            element_x_starts=[element.x_start for element in elements],
            element_x_ends=[element.x_end for element in elements],
            element_coefficients=element_coefficients,
            longitudinal_shape_coefficients=longitudinal_coefficients,
            transverse_power_coefficients=transverse_coefficients,
            transverse_x_power_coefficients=transverse_x_coefficients,
            transverse_segment_boundaries=transverse_segment_boundaries,
            transverse_segment_power_coefficients=(
                transverse_segment_coefficients
            ),
            metadata=combined_metadata,
        )

    @staticmethod
    def _cardinal_lagrange_power_coefficients(nodes: np.ndarray) -> np.ndarray:
        """Return cardinal Lagrange polynomials in ascending powers.

        This helper belongs to compilation of the transverse longitudinal-blend
        expansion.  It is not the longitudinal FEM shape-function provider.
        """
        nodes = np.asarray(nodes, dtype=float)
        count = int(nodes.size)
        result = np.empty((count, count), dtype=float)
        for index in range(count):
            other_nodes = np.delete(nodes, index)
            denominator = np.prod(nodes[index] - other_nodes)
            result[index, :] = np.poly(other_nodes)[::-1] / denominator
        return result

    def _validate(self) -> None:
        starts = self._element_x_starts
        ends = self._element_x_ends
        coefficients = self._element_coefficients
        longitudinal = self._longitudinal_shape_coefficients
        transverse = self._transverse_power_coefficients
        transverse_x = self._transverse_x_power_coefficients
        segment_boundaries = self._transverse_segment_boundaries
        segment_transverse = self._transverse_segment_power_coefficients

        if starts.ndim != 1 or ends.shape != starts.shape or starts.size < 1:
            raise ValueError("element bounds have invalid shape")
        if not np.all(np.isfinite(starts)) or not np.all(np.isfinite(ends)):
            raise ValueError("element bounds contain non-finite values")
        if np.any(ends <= starts):
            raise ValueError("every element must have positive length")
        if np.any(starts[1:] != ends[:-1]):
            raise ValueError("element bounds must be contiguous")
        if coefficients.ndim != 4 or coefficients.shape[0] != starts.size:
            raise ValueError("element coefficients have invalid shape")
        if coefficients.shape[3] != 3:
            raise ValueError("displacement coefficients require 3 components")
        if longitudinal.shape != (coefficients.shape[1], coefficients.shape[1]):
            raise ValueError("longitudinal coefficients have invalid shape")

        has_static = transverse is not None
        has_variable = transverse_x is not None
        has_segmented = (
            segment_boundaries is not None or segment_transverse is not None
        )
        if (segment_boundaries is None) != (segment_transverse is None):
            raise ValueError(
                "segmented checkpoint requires both boundaries and coefficients"
            )
        if sum((has_static, has_variable, has_segmented)) != 1:
            raise ValueError(
                "checkpoint requires exactly one transverse polynomial representation"
            )

        if has_static:
            if transverse.ndim != 3 or transverse.shape[0] != coefficients.shape[2]:
                raise ValueError("transverse coefficients have invalid shape")
        elif has_variable:
            if transverse_x.ndim != 4 or transverse_x.shape[0] != coefficients.shape[2]:
                raise ValueError("x-dependent transverse coefficients have invalid shape")
        else:
            if (
                segment_boundaries.ndim != 1
                or segment_boundaries.size < 2
                or not np.all(np.isfinite(segment_boundaries))
                or np.any(np.diff(segment_boundaries) <= 0.0)
            ):
                raise ValueError("segmented transverse boundaries are invalid")
            if (
                segment_transverse.ndim != 4
                or segment_transverse.shape[0] != segment_boundaries.size - 1
                or segment_transverse.shape[1] != coefficients.shape[2]
            ):
                raise ValueError("segmented transverse coefficients have invalid shape")
            tolerance = 1.0e-10 * max(
                1.0,
                abs(float(starts[0])),
                abs(float(ends[-1])),
            )
            if not np.isclose(
                segment_boundaries[0],
                starts[0],
                rtol=0.0,
                atol=tolerance,
            ) or not np.isclose(
                segment_boundaries[-1],
                ends[-1],
                rtol=0.0,
                atol=tolerance,
            ):
                raise ValueError(
                    "segmented transverse boundaries must cover the solved x-domain"
                )

        values = [coefficients, longitudinal]
        if has_static:
            values.append(transverse)
        elif has_variable:
            values.append(transverse_x)
        else:
            values.extend((segment_boundaries, segment_transverse))
        if not all(np.all(np.isfinite(value)) for value in values):
            raise ValueError("compiled displacement contains non-finite data")

    @property
    def metadata(self) -> dict:
        return dict(self._metadata)

    @property
    def x_start(self) -> float:
        return float(self._element_x_starts[0])

    @property
    def x_end(self) -> float:
        return float(self._element_x_ends[-1])

    def _element_index(self, x: float) -> int:
        if not np.isfinite(x):
            raise ValueError("x must be finite")
        if x < self.x_start or x > self.x_end:
            raise ValueError(
                f"x={x} lies outside longitudinal domain "
                f"[{self.x_start}, {self.x_end}]"
            )
        index = int(np.searchsorted(self._element_x_ends, x, side="right"))
        return min(index, self._element_x_ends.size - 1)

    @staticmethod
    def _powers_and_derivatives(value: float, count: int) -> tuple[np.ndarray, np.ndarray]:
        """Return monomial powers and their exact analytical derivatives."""

        value = float(value)
        count = int(count)
        if not np.isfinite(value):
            raise ValueError("polynomial coordinate must be finite")
        if count < 1:
            raise ValueError("polynomial coefficient count must be positive")

        powers = np.power(value, np.arange(count, dtype=int))
        derivatives = np.zeros(count, dtype=float)
        if count > 1:
            degrees = np.arange(1, count, dtype=float)
            derivatives[1:] = degrees * np.power(
                value,
                np.arange(count - 1, dtype=int),
            )
        return powers, derivatives

    def _amplitudes_and_derivatives(self, x: float) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate generalized CUF amplitudes and exact d/dx derivatives."""

        x = float(x)
        index = self._element_index(x)
        start = float(self._element_x_starts[index])
        end = float(self._element_x_ends[index])
        length = end - start
        xi = 2.0 * (x - start) / length - 1.0

        xi_powers, xi_derivatives = self._powers_and_derivatives(
            xi,
            self._longitudinal_shape_coefficients.shape[1],
        )
        shape_values = self._longitudinal_shape_coefficients @ xi_powers
        shape_derivatives_x = (
            self._longitudinal_shape_coefficients @ xi_derivatives
        ) * (2.0 / length)

        coefficients = self._element_coefficients[index]
        amplitudes = np.tensordot(shape_values, coefficients, axes=(0, 0))
        amplitude_derivatives_x = np.tensordot(
            shape_derivatives_x,
            coefficients,
            axes=(0, 0),
        )
        return (
            np.asarray(amplitudes, dtype=float),
            np.asarray(amplitude_derivatives_x, dtype=float),
        )

    def _transverse_values_and_derivatives(
        self,
        x: float,
        y: float,
        z: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate F_tau and exact analytical derivatives Fx, Fy, Fz."""

        x = float(x)
        y = float(y)
        z = float(z)
        if not np.isfinite(y) or not np.isfinite(z):
            raise ValueError("y and z must be finite")

        if self._transverse_power_coefficients is not None:
            coefficients = self._transverse_power_coefficients
            x_dependent = False
        elif self._transverse_segment_power_coefficients is not None:
            boundaries = self._transverse_segment_boundaries
            segment_index = int(
                np.searchsorted(boundaries[1:-1], x, side="right")
            )
            coefficients = self._transverse_segment_power_coefficients[
                segment_index
            ]
            x_dependent = False
        else:
            coefficients = self._transverse_x_power_coefficients
            x_dependent = True

        if x_dependent:
            x_powers, x_derivatives = self._powers_and_derivatives(
                x, coefficients.shape[1]
            )
            y_powers, y_derivatives = self._powers_and_derivatives(
                y, coefficients.shape[2]
            )
            z_powers, z_derivatives = self._powers_and_derivatives(
                z, coefficients.shape[3]
            )
            values = np.einsum(
                "trpq,r,p,q->t",
                coefficients, x_powers, y_powers, z_powers,
                optimize=True,
            )
            derivative_x = np.einsum(
                "trpq,r,p,q->t",
                coefficients, x_derivatives, y_powers, z_powers,
                optimize=True,
            )
            derivative_y = np.einsum(
                "trpq,r,p,q->t",
                coefficients, x_powers, y_derivatives, z_powers,
                optimize=True,
            )
            derivative_z = np.einsum(
                "trpq,r,p,q->t",
                coefficients, x_powers, y_powers, z_derivatives,
                optimize=True,
            )
        else:
            y_powers, y_derivatives = self._powers_and_derivatives(
                y, coefficients.shape[1]
            )
            z_powers, z_derivatives = self._powers_and_derivatives(
                z, coefficients.shape[2]
            )
            values = np.einsum(
                "tpq,p,q->t", coefficients, y_powers, z_powers, optimize=True
            )
            derivative_x = np.zeros_like(values)
            derivative_y = np.einsum(
                "tpq,p,q->t",
                coefficients, y_derivatives, z_powers,
                optimize=True,
            )
            derivative_z = np.einsum(
                "tpq,p,q->t",
                coefficients, y_powers, z_derivatives,
                optimize=True,
            )

        return tuple(
            np.asarray(value, dtype=float)
            for value in (values, derivative_x, derivative_y, derivative_z)
        )

    def displacement_gradient(self, x: float, y: float, z: float) -> np.ndarray:
        """Evaluate the exact analytical gradient of the compiled CUF field.

        The returned matrix uses displacement components by rows and physical
        coordinates ``(x, y, z)`` by columns, i.e. ``gradient[i, j] = du_i/dx_j``.
        No finite differences, sampling, smoothing, or fitted recovery is used.
        """

        amplitudes, amplitude_derivatives_x = self._amplitudes_and_derivatives(x)
        F, Fx, Fy, Fz = self._transverse_values_and_derivatives(x, y, z)

        derivative_x = Fx @ amplitudes + F @ amplitude_derivatives_x
        derivative_y = Fy @ amplitudes
        derivative_z = Fz @ amplitudes
        gradient = np.column_stack((derivative_x, derivative_y, derivative_z))
        gradient = np.asarray(gradient, dtype=float)

        if gradient.shape != (3, 3):
            raise RuntimeError("compiled displacement gradient has invalid shape")
        if not np.all(np.isfinite(gradient)):
            raise RuntimeError(
                "compiled displacement gradient contains non-finite values"
            )
        return gradient

    def displacement_derivative_x(
        self,
        x: float,
        y: float,
        z: float,
    ) -> np.ndarray:
        """Return the exact analytical vector du_i/dx from the solved field."""

        return self.displacement_gradient(x, y, z)[:, 0].copy()

    def displacement_derivative_y(
        self,
        x: float,
        y: float,
        z: float,
    ) -> np.ndarray:
        """Return the exact analytical vector du_i/dy from the solved field."""

        return self.displacement_gradient(x, y, z)[:, 1].copy()

    def displacement_derivative_z(
        self,
        x: float,
        y: float,
        z: float,
    ) -> np.ndarray:
        """Return the exact analytical vector du_i/dz from the solved field."""

        return self.displacement_gradient(x, y, z)[:, 2].copy()

    def strain(self, x: float, y: float, z: float) -> np.ndarray:
        """Evaluate the continuous six-component small-strain field.

        Voigt order:
            [epsilon_xx, epsilon_yy, epsilon_zz,
             gamma_yz, gamma_xz, gamma_xy]
        """

        gradient = self.displacement_gradient(x, y, z)
        strain = np.asarray(
            [
                gradient[0, 0],
                gradient[1, 1],
                gradient[2, 2],
                gradient[1, 2] + gradient[2, 1],
                gradient[0, 2] + gradient[2, 0],
                gradient[0, 1] + gradient[1, 0],
            ],
            dtype=float,
        )
        return strain

    def section_evaluator(self, x: float):
        """Compile one fixed-x section evaluator from persisted coefficients."""

        x = float(x)
        index = self._element_index(x)
        start = float(self._element_x_starts[index])
        end = float(self._element_x_ends[index])
        xi = 2.0 * (x - start) / (end - start) - 1.0

        xi_powers = np.power(
            xi,
            np.arange(self._longitudinal_shape_coefficients.shape[1]),
        )
        shape_values = self._longitudinal_shape_coefficients @ xi_powers
        amplitudes = np.tensordot(
            shape_values,
            self._element_coefficients[index],
            axes=(0, 0),
        )

        if self._transverse_power_coefficients is not None:
            transverse_at_x = self._transverse_power_coefficients
        elif self._transverse_segment_power_coefficients is not None:
            boundaries = self._transverse_segment_boundaries
            segment_index = int(
                np.searchsorted(boundaries[1:-1], x, side="right")
            )
            transverse_at_x = self._transverse_segment_power_coefficients[
                segment_index
            ]
        else:
            x_powers = np.power(
                x,
                np.arange(self._transverse_x_power_coefficients.shape[1]),
            )
            transverse_at_x = np.tensordot(
                self._transverse_x_power_coefficients,
                x_powers,
                axes=(1, 0),
            )

        section_power_coefficients = np.tensordot(
            transverse_at_x,
            amplitudes,
            axes=(0, 0),
        )
        section_power_coefficients = np.asarray(
            section_power_coefficients,
            dtype=float,
        ).reshape(-1, 3)
        section_power_coefficients.setflags(write=False)
        y_count = int(transverse_at_x.shape[1])
        z_count = int(transverse_at_x.shape[2])

        def evaluate(y: float, z: float) -> np.ndarray:
            y = float(y)
            z = float(z)
            if not np.isfinite(y) or not np.isfinite(z):
                raise ValueError("y and z must be finite")
            y_powers = np.power(y, np.arange(y_count))
            z_powers = np.power(z, np.arange(z_count))
            monomials = np.multiply.outer(y_powers, z_powers).reshape(-1)
            displacement = monomials @ section_power_coefficients
            return np.asarray(displacement, dtype=float)

        return evaluate

    def __call__(self, x: float, y: float, z: float) -> np.ndarray:
        return self.section_evaluator(float(x))(float(y), float(z))

    def _format_version(self) -> int:
        if self._transverse_segment_power_coefficients is not None:
            return _SEGMENTED_FORMAT_VERSION
        if self._transverse_x_power_coefficients is not None:
            return _VARIABLE_FORMAT_VERSION
        return _STATIC_FORMAT_VERSION

    def save_atomic(self, path: str | Path) -> tuple[Path, str]:
        """Atomically save and verify a pure displacement-field NPZ checkpoint.

        Only the numerical representation required to evaluate ``u_i(x,y,z)``
        is persisted.  Analytical derivatives are reconstructed from the same
        coefficients and are therefore not duplicated in the archive.
        """

        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        format_version = self._format_version()

        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                payload = {
                    "element_x_starts": self._element_x_starts,
                    "element_x_ends": self._element_x_ends,
                    "element_coefficients": self._element_coefficients,
                    "longitudinal_shape_coefficients": (
                        self._longitudinal_shape_coefficients
                    ),
                }

                if format_version == _STATIC_FORMAT_VERSION:
                    payload["transverse_power_coefficients"] = (
                        self._transverse_power_coefficients
                    )
                elif format_version == _VARIABLE_FORMAT_VERSION:
                    payload["transverse_x_power_coefficients"] = (
                        self._transverse_x_power_coefficients
                    )
                else:
                    payload["transverse_segment_boundaries"] = (
                        self._transverse_segment_boundaries
                    )
                    payload["transverse_segment_power_coefficients"] = (
                        self._transverse_segment_power_coefficients
                    )

                np.savez_compressed(stream, **payload)
                stream.flush()
                os.fsync(stream.fileno())

            # A successful reload validates the complete persisted field structure.
            type(self).load(temporary_path)
            os.replace(temporary_path, path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, digest

    @classmethod
    def load(cls, path: str | Path):
        """Load a pure compiled displacement field from an NPZ checkpoint."""

        path = Path(path).resolve()
        with np.load(path, allow_pickle=False) as archive:
            names = set(archive.files)

            has_static = "transverse_power_coefficients" in names
            has_variable = "transverse_x_power_coefficients" in names
            has_segmented = (
                "transverse_segment_boundaries" in names
                or "transverse_segment_power_coefficients" in names
            )

            if sum((has_static, has_variable, has_segmented)) != 1:
                raise ValueError(
                    "compiled displacement checkpoint must contain exactly one "
                    "transverse field representation"
                )
            if has_segmented and not {
                "transverse_segment_boundaries",
                "transverse_segment_power_coefficients",
            }.issubset(names):
                raise ValueError(
                    "segmented compiled displacement checkpoint is incomplete"
                )

            required = {
                "element_x_starts",
                "element_x_ends",
                "element_coefficients",
                "longitudinal_shape_coefficients",
            }
            missing = required.difference(names)
            if missing:
                raise ValueError(
                    "compiled displacement checkpoint is missing: "
                    + ", ".join(sorted(missing))
                )

            common = dict(
                element_x_starts=archive["element_x_starts"],
                element_x_ends=archive["element_x_ends"],
                element_coefficients=archive["element_coefficients"],
                longitudinal_shape_coefficients=(
                    archive["longitudinal_shape_coefficients"]
                ),
                metadata=None,
            )

            if has_static:
                return cls(
                    transverse_power_coefficients=(
                        archive["transverse_power_coefficients"]
                    ),
                    **common,
                )
            if has_variable:
                return cls(
                    transverse_x_power_coefficients=(
                        archive["transverse_x_power_coefficients"]
                    ),
                    **common,
                )
            return cls(
                transverse_segment_boundaries=(
                    archive["transverse_segment_boundaries"]
                ),
                transverse_segment_power_coefficients=(
                    archive["transverse_segment_power_coefficients"]
                ),
                **common,
            )

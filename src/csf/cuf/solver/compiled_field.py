# Version: CSF-CUF compiled displacement field v26 - 2026-10-10
# Revision-ID: c5d87e8d-9cf1-4ce2-b702-6a24cc7707ae
# Changelog v26:
# - Generic format v5: solved physical field in moving isoparametric domains.
# - Persist solved natural-domain coefficients and exact affine domain trajectories.
# - Analytical displacement gradient including domain motion in longitudinal d/dx.
# - Preserve legacy formats v1-v4, shared-interface side selection, and entry points.
# - No concrete transverse expansion name or CUF solver change.
# Based on v25.1 (Revision-ID: 903aa66a-948f-4983-8e97-8c7fee05af53).

"""Pure compiled representation of the solved CUF displacement field.

The ``.cuf.npz`` checkpoint stores only the data required to reconstruct the
continuous solved displacement field

    u_i(x, y, z)

for ``i = x, y, z``.  No CSF geometry, material data, constitutive provider,
constitutive matrix, stress data, or recovery context is persisted.

The physical field is represented by solved coefficients and domain maps
sufficient to evaluate the displacement and its derivatives without the
original transverse basis or the CSF provider. Legacy formats are supported:

Version 1 (static transverse polynomial):

    F_tau(y,z) = sum_{p,q} C[tau-1,p,q] y**p z**q.

Version 2 (smooth longitudinally varying transverse polynomial):

    F_tau(x,y,z) = sum_{r,p,q} C[tau-1,r,p,q] x**r y**p z**q.

Version 3 (piecewise transverse polynomial):

    F_tau^(k)(y,z) = sum_{p,q} C[k,tau-1,p,q] y**p z**q.

Version 4 (solved physical field, transverse-expansion independent):

    u_i^(e,a,k)(y,z) = sum_{p,q} U[e,a,k,p,q,i] y**p z**q.

Version 5 (moving-domain solved physical field):

    u_i^(e,a,k)(alpha,beta) = sum_{p,q} U[e,a,k,p,q,i] alpha**p beta**q,

with a bilinear transverse isoparametric domain map whose physical vertices
vary affinely along x. The physical x-gradient includes map motion exactly.

The v4/v5 checkpoints contain already-contracted physical displacement
coefficients at each longitudinal FE node.  No transverse basis index or
expansion object is retained or required after this representation is created.
The moving-domain vertex trajectories describe the support of the solved field,
not a reference to the original CSF model.

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
_SOLVED_FIELD_FORMAT_VERSION = 4
_MOVING_SOLVED_FIELD_FORMAT_VERSION = 5
_SUPPORTED_FORMAT_VERSIONS = {
    _STATIC_FORMAT_VERSION,
    _VARIABLE_FORMAT_VERSION,
    _SEGMENTED_FORMAT_VERSION,
    _SOLVED_FIELD_FORMAT_VERSION,
    _MOVING_SOLVED_FIELD_FORMAT_VERSION,
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
        solved_domain_vertices=None,
        solved_nodal_domain_power_coefficients=None,
        moving_domain_vertex_endpoints=None,
        solved_nodal_domain_natural_coefficients=None,
        moving_domain_x_bounds=None,
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

        if solved_domain_vertices is None:
            self._solved_domain_vertices = None
        else:
            self._solved_domain_vertices = np.asarray(
                solved_domain_vertices, dtype=float
            )

        if solved_nodal_domain_power_coefficients is None:
            self._solved_nodal_domain_power_coefficients = None
        else:
            self._solved_nodal_domain_power_coefficients = np.asarray(
                solved_nodal_domain_power_coefficients, dtype=float
            )

        self._moving_domain_vertex_endpoints = (
            None if moving_domain_vertex_endpoints is None else
            np.asarray(moving_domain_vertex_endpoints, dtype=float)
        )
        self._solved_nodal_domain_natural_coefficients = (
            None if solved_nodal_domain_natural_coefficients is None else
            np.asarray(solved_nodal_domain_natural_coefficients, dtype=float)
        )
        self._moving_domain_x_bounds = (
            None if moving_domain_x_bounds is None else
            np.asarray(moving_domain_x_bounds, dtype=float)
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
        if self._solved_domain_vertices is not None:
            values.append(self._solved_domain_vertices)
        if self._solved_nodal_domain_power_coefficients is not None:
            values.append(self._solved_nodal_domain_power_coefficients)
        for value in (
            self._moving_domain_vertex_endpoints,
            self._solved_nodal_domain_natural_coefficients,
            self._moving_domain_x_bounds,
        ):
            if value is not None:
                values.append(value)
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

        # New generic solved-field path.  A transverse expansion may expose an
        # exact, self-contained mathematical representation through the optional
        # hook below.  The compiler does not inspect the expansion class/name.
        # It immediately contracts the transverse CUF index and then delegates
        # to checkpoint v4, where no expansion object or tau index survives.
        representation_exporter = getattr(
            basis,
            "compiled_transverse_representation",
            None,
        )
        if callable(representation_exporter):
            representation = representation_exporter()
            if representation is not None:
                if not isinstance(representation, dict):
                    raise TypeError(
                        "compiled_transverse_representation() must return "
                        "a dict or None"
                    )

                kind = str(representation.get("kind", "")).strip()
                if kind == "domain_natural_power_affine_x":
                    try:
                        domain_vertices = np.asarray(
                            representation["domain_vertex_endpoints"], dtype=float
                        )
                        domain_coefficients = np.asarray(
                            representation["coefficients"], dtype=float
                        )
                        x_bounds = np.asarray(
                            representation["x_bounds"], dtype=float
                        )
                    except KeyError as exc:
                        raise ValueError(
                            "moving solved field requires domain_vertex_endpoints, "
                            "coefficients, and x_bounds"
                        ) from exc
                    if (
                        domain_vertices.ndim != 4 or domain_vertices.shape[0] != 2
                        or domain_vertices.shape[2:] != (4, 2)
                        or domain_coefficients.ndim != 4
                        or domain_coefficients.shape[:2] != (
                            domain_vertices.shape[1], element_coefficients.shape[2]
                        )
                        or x_bounds.shape != (2,) or x_bounds[1] <= x_bounds[0]
                    ):
                        raise ValueError("moving solved field has invalid representation shapes")
                    if not all(np.all(np.isfinite(a)) for a in (
                        domain_vertices, domain_coefficients, x_bounds,
                    )):
                        raise ValueError("moving solved field contains non-finite input")
                    if not np.allclose(
                        x_bounds,
                        (elements[0].x_start, elements[-1].x_end),
                        rtol=0.0, atol=1e-10 * max(1.0, abs(float(x_bounds[-1])))
                    ):
                        raise ValueError("moving domain x bounds disagree with solved FE bounds")

                    solved_field_coefficients = np.einsum(
                        "ktpq,eatc->eakpqc",
                        domain_coefficients, element_coefficients, optimize=True,
                    )
                    combined_metadata = dict(metadata or {})
                    combined_metadata.update({
                        "basis_order": int(basis.order),
                        "basis_size": int(basis.size),
                        "longitudinal_basis_order": int(elements[0].basis.order),
                    })
                    return cls.from_solved_moving_field_data(
                        element_x_starts=[el.x_start for el in elements],
                        element_x_ends=[el.x_end for el in elements],
                        longitudinal_shape_coefficients=longitudinal_coefficients,
                        domain_vertex_endpoints=domain_vertices,
                        nodal_domain_natural_coefficients=solved_field_coefficients,
                        domain_x_bounds=x_bounds,
                        metadata=combined_metadata,
                    )

                if kind != "domain_y_z_power":
                    raise ValueError(
                        "unsupported compiled transverse representation kind "
                        f"{kind!r}"
                    )

                try:
                    domain_vertices = np.asarray(
                        representation["domain_vertices"],
                        dtype=float,
                    )
                    domain_coefficients = np.asarray(
                        representation["coefficients"],
                        dtype=float,
                    )
                except KeyError as exc:
                    raise ValueError(
                        "domain_y_z_power representation requires "
                        "domain_vertices and coefficients"
                    ) from exc

                if domain_vertices.ndim != 3 or domain_vertices.shape[2] != 2:
                    raise ValueError(
                        "domain_y_z_power domain_vertices must have shape "
                        "(domain, vertex, 2)"
                    )
                if domain_vertices.shape[1] < 3:
                    raise ValueError(
                        "domain_y_z_power requires at least 3 vertices per domain"
                    )
                if domain_coefficients.ndim != 4:
                    raise ValueError(
                        "domain_y_z_power coefficients must have shape "
                        "(domain, tau, y_power, z_power)"
                    )
                if domain_coefficients.shape[0] != domain_vertices.shape[0]:
                    raise ValueError(
                        "domain_y_z_power domain count is inconsistent"
                    )
                if domain_coefficients.shape[1] != element_coefficients.shape[2]:
                    raise ValueError(
                        "domain_y_z_power transverse size is inconsistent "
                        "with the solved CUF coefficients"
                    )
                if not np.all(np.isfinite(domain_vertices)) or not np.all(
                    np.isfinite(domain_coefficients)
                ):
                    raise ValueError(
                        "compiled transverse representation contains "
                        "non-finite values"
                    )

                # Contract tau immediately:
                #   U[e,a,k,p,q,i] = sum_tau C[k,tau,p,q] q[e,a,tau,i]
                solved_field_coefficients = np.einsum(
                    "ktpq,eatc->eakpqc",
                    domain_coefficients,
                    element_coefficients,
                    optimize=True,
                )

                combined_metadata = dict(metadata or {})
                combined_metadata.update(
                    {
                        "basis_class": (
                            f"{basis.__class__.__module__}."
                            f"{basis.__class__.__qualname__}"
                        ),
                        "basis_order": int(basis.order),
                        "basis_size": int(basis.size),
                        "longitudinal_basis_class": (
                            f"{elements[0].basis.__class__.__module__}."
                            f"{elements[0].basis.__class__.__qualname__}"
                        ),
                        "longitudinal_basis_order": int(elements[0].basis.order),
                        "longitudinal_basis_size": int(elements[0].basis.size),
                        "element_basis_sizes": [
                            int(dof_layout.basis_size_at_node(element.node_ids[0]))
                            for element in elements
                        ],
                    }
                )

                return cls.from_solved_field_data(
                    element_x_starts=[element.x_start for element in elements],
                    element_x_ends=[element.x_end for element in elements],
                    longitudinal_shape_coefficients=longitudinal_coefficients,
                    domain_vertices=domain_vertices,
                    nodal_domain_power_coefficients=solved_field_coefficients,
                    metadata=combined_metadata,
                )

        # Legacy v1-v3 compilation remains unchanged for existing expansion
        # families that do not provide the generic solved-field export hook.
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

    @classmethod
    def from_solved_field_data(
        cls,
        *,
        element_x_starts,
        element_x_ends,
        longitudinal_shape_coefficients,
        domain_vertices,
        nodal_domain_power_coefficients,
        metadata=None,
    ):
        """Create checkpoint v4 from an already-compiled physical solution.

        This is the expansion-independent checkpoint boundary.  The caller must
        provide the solved displacement field already contracted over the
        transverse CUF index.  Consequently this method has no ``basis``
        argument and cannot call a transverse expansion.

        ``nodal_domain_power_coefficients`` has shape

            (element, local_node, domain, y_power, z_power, component)

        and represents, for every longitudinal FE node and transverse domain,

            u_i(y,z) = sum[p,q] U[...,p,q,i] y**p z**q.

        ``domain_vertices`` has shape ``(domain, vertex, 2)`` and is used only
        to select the transverse polynomial valid at a requested physical point.
        """
        starts = np.asarray(element_x_starts, dtype=float)
        ends = np.asarray(element_x_ends, dtype=float)
        longitudinal = np.asarray(longitudinal_shape_coefficients, dtype=float)
        vertices = np.asarray(domain_vertices, dtype=float)
        solved = np.asarray(nodal_domain_power_coefficients, dtype=float)

        if starts.ndim != 1 or ends.shape != starts.shape or starts.size < 1:
            raise ValueError("element bounds have invalid shape")
        if solved.ndim != 6 or solved.shape[0] != starts.size:
            raise ValueError(
                "nodal_domain_power_coefficients must have shape "
                "(element, local_node, domain, y_power, z_power, 3)"
            )
        if solved.shape[-1] != 3:
            raise ValueError("solved field coefficients require 3 components")
        local_node_count = int(solved.shape[1])
        if longitudinal.shape != (local_node_count, local_node_count):
            raise ValueError("longitudinal coefficients have invalid shape")
        if vertices.ndim != 3 or vertices.shape[0] != solved.shape[2] or vertices.shape[2] != 2:
            raise ValueError(
                "domain_vertices must have shape (domain, vertex, 2) and match "
                "the solved-field domain count"
            )
        if vertices.shape[1] < 3:
            raise ValueError("every solved-field domain requires at least 3 vertices")
        arrays = (starts, ends, longitudinal, vertices, solved)
        if not all(np.all(np.isfinite(value)) for value in arrays):
            raise ValueError("solved field representation contains non-finite values")

        combined_metadata = dict(metadata or {})
        combined_metadata.update(
            {
                "format": _FORMAT_NAME,
                "format_version": _SOLVED_FIELD_FORMAT_VERSION,
                "transverse_representation": "solved_domain_y_z_power",
                "components": ["ux", "uy", "uz"],
            }
        )

        # v4 no longer stores generalized transverse amplitudes.  A zero-width
        # compatibility container is supplied only so the common constructor can
        # keep the established object layout for v1-v3.
        placeholder = np.zeros((starts.size, local_node_count, 0, 3), dtype=float)
        return cls(
            element_x_starts=starts,
            element_x_ends=ends,
            element_coefficients=placeholder,
            longitudinal_shape_coefficients=longitudinal,
            solved_domain_vertices=vertices,
            solved_nodal_domain_power_coefficients=solved,
            metadata=combined_metadata,
        )

    @classmethod
    def from_solved_moving_field_data(
        cls, *, element_x_starts, element_x_ends,
        longitudinal_shape_coefficients, domain_vertex_endpoints,
        nodal_domain_natural_coefficients, domain_x_bounds, metadata=None,
    ):
        """Construct a standalone moving-domain solved field (format v5).

        Domain maps are stored as physical vertex endpoint trajectories; the
        solved displacement coefficients are in generic natural coordinates.
        Neither the input transverse expansion nor CSF survives compilation.
        """
        starts = np.asarray(element_x_starts, dtype=float)
        solved = np.asarray(nodal_domain_natural_coefficients, dtype=float)
        vertices = np.asarray(domain_vertex_endpoints, dtype=float)
        bounds = np.asarray(domain_x_bounds, dtype=float)
        longitudinal = np.asarray(longitudinal_shape_coefficients, dtype=float)
        if starts.ndim != 1 or starts.size < 1 or solved.ndim != 6:
            raise ValueError("invalid moving solved field element dimensions")
        if solved.shape[0] != starts.size or solved.shape[-1] != 3:
            raise ValueError("invalid moving solved field coefficient dimensions")
        if vertices.shape != (2, solved.shape[2], 4, 2):
            raise ValueError("moving domain vertex endpoints shape mismatch")
        if bounds.shape != (2,) or not bounds[0] < bounds[1]:
            raise ValueError("moving domain x_bounds invalid")
        if longitudinal.shape != (solved.shape[1], solved.shape[1]):
            raise ValueError("moving solved field longitudinal basis mismatch")
        placeholder = np.zeros((starts.size, solved.shape[1], 0, 3))
        combined_metadata = dict(metadata or {})
        combined_metadata.update({
            "format": _FORMAT_NAME,
            "format_version": _MOVING_SOLVED_FIELD_FORMAT_VERSION,
            "transverse_representation": "solved_moving_domain_natural_power",
            "components": ["ux", "uy", "uz"],
        })
        return cls(
            element_x_starts=starts, element_x_ends=element_x_ends,
            element_coefficients=placeholder,
            longitudinal_shape_coefficients=longitudinal,
            moving_domain_vertex_endpoints=vertices,
            solved_nodal_domain_natural_coefficients=solved,
            moving_domain_x_bounds=bounds,
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
        solved_vertices = self._solved_domain_vertices
        solved_field = self._solved_nodal_domain_power_coefficients
        moving_vertices = self._moving_domain_vertex_endpoints
        moving_field = self._solved_nodal_domain_natural_coefficients
        moving_bounds = self._moving_domain_x_bounds

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
        has_solved_field = (solved_vertices is not None or solved_field is not None)
        if (segment_boundaries is None) != (segment_transverse is None):
            raise ValueError(
                "segmented checkpoint requires both boundaries and coefficients"
            )
        if (solved_vertices is None) != (solved_field is None):
            raise ValueError(
                "solved-field checkpoint requires both domain vertices and coefficients"
            )
        has_moving = any(value is not None for value in (
            moving_vertices, moving_field, moving_bounds
        ))
        if has_moving and any(value is None for value in (
            moving_vertices, moving_field, moving_bounds
        )):
            raise ValueError("moving solved field requires vertices, coefficients and x bounds")
        if sum((has_static, has_variable, has_segmented, has_solved_field, has_moving)) != 1:
            raise ValueError(
                "checkpoint requires exactly one displacement-field representation"
            )

        if has_moving:
            if moving_field.ndim != 6 or moving_field.shape[-1] != 3:
                raise ValueError("moving solved field requires 6D displacement coefficients")
            if moving_field.shape[:2] != (starts.size, longitudinal.shape[0]):
                raise ValueError("moving solved field longitudinal dimensions mismatch")
            if moving_vertices.shape != (2, moving_field.shape[2], 4, 2):
                raise ValueError("moving solved field domain vertex dimensions mismatch")
            if moving_bounds.shape != (2,) or moving_bounds[1] <= moving_bounds[0]:
                raise ValueError("moving solved field longitudinal bounds invalid")
            if not np.allclose(
                moving_bounds, (starts[0], ends[-1]), rtol=0.0,
                atol=1e-10 * max(1.0, abs(float(ends[-1])))
            ):
                raise ValueError("moving solved field bounds mismatch")
        elif has_solved_field:
            if solved_vertices.ndim != 3 or solved_vertices.shape[2] != 2:
                raise ValueError("solved-field domain vertices have invalid shape")
            if solved_vertices.shape[1] < 3:
                raise ValueError("solved-field domains require at least 3 vertices")
            if solved_field.ndim != 6 or solved_field.shape[-1] != 3:
                raise ValueError("solved-field coefficients have invalid shape")
            if solved_field.shape[0] != starts.size:
                raise ValueError("solved-field element count is inconsistent")
            if solved_field.shape[1] != longitudinal.shape[0]:
                raise ValueError("solved-field local-node count is inconsistent")
            if solved_field.shape[2] != solved_vertices.shape[0]:
                raise ValueError("solved-field domain count is inconsistent")
        elif has_static:
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
        if has_moving:
            values.extend((moving_vertices, moving_field, moving_bounds))
        elif has_solved_field:
            values.extend((solved_vertices, solved_field))
        elif has_static:
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

    @staticmethod
    def _point_on_segment_2d(y, z, a, b, tolerance):
        ay, az = map(float, a)
        by, bz = map(float, b)
        dy = by - ay
        dz = bz - az
        py = float(y) - ay
        pz = float(z) - az
        cross = dy * pz - dz * py
        length = float(np.hypot(dy, dz))
        if length == 0.0:
            return float(np.hypot(py, pz)) <= tolerance
        if abs(cross) > tolerance * length:
            return False
        dot = py * dy + pz * dz
        if dot < -tolerance * length:
            return False
        squared = dy * dy + dz * dz
        return dot <= squared + tolerance * length

    @classmethod
    def _point_in_polygon_inclusive_2d(cls, y, z, vertices):
        vertices = np.asarray(vertices, dtype=float)
        scale = max(1.0, abs(float(y)), abs(float(z)), float(np.max(np.abs(vertices))))
        tolerance = 1.0e-10 * scale
        count = int(vertices.shape[0])
        for index in range(count):
            if cls._point_on_segment_2d(
                y, z, vertices[index], vertices[(index + 1) % count], tolerance
            ):
                return True
        inside = False
        j = count - 1
        for i in range(count):
            yi, zi = vertices[i]
            yj, zj = vertices[j]
            if (zi > z) != (zj > z):
                y_cross = (yj - yi) * (z - zi) / (zj - zi) + yi
                if y < y_cross:
                    inside = not inside
            j = i
        return inside

    def domain_vertices_at(self, x: float) -> np.ndarray | None:
        """Physical transverse domains at x, independent of basis/CSF objects."""
        if self._moving_domain_vertex_endpoints is None:
            return self.solved_domain_vertices
        x = float(x)
        self._element_index(x)
        bounds = self._moving_domain_x_bounds
        fraction = (x - bounds[0]) / (bounds[1] - bounds[0])
        endpoints = self._moving_domain_vertex_endpoints
        return ((1.0 - fraction) * endpoints[0] + fraction * endpoints[1]).copy()

    @staticmethod
    def _quad_bilinear_data(alpha, beta):
        a, b = float(alpha), float(beta)
        weights = 0.25 * np.array([
            (1-a)*(1-b), (1+a)*(1-b),
            (1+a)*(1+b), (1-a)*(1+b),
        ])
        derivative_a = 0.25 * np.array([-(1-b), 1-b, 1+b, -(1+b)])
        derivative_b = 0.25 * np.array([-(1-a), -(1+a), 1+a, 1-a])
        return weights, derivative_a, derivative_b

    @classmethod
    def _moving_natural_coordinates(cls, y, z, vertices):
        """Invert the generic 4-corner bilinear domain map, never L9 functions."""
        point = np.asarray((y,z), dtype=float)
        natural = np.zeros(2, dtype=float)
        scale = max(1.0, float(np.max(np.abs(vertices))))
        for _ in range(25):
            weights, d_a, d_b = cls._quad_bilinear_data(*natural)
            residual = weights @ vertices - point
            if np.linalg.norm(residual, ord=np.inf) <= 1e-12 * scale:
                return natural, weights, np.column_stack((d_a @ vertices, d_b @ vertices))
            jacobian = np.column_stack((d_a @ vertices, d_b @ vertices))
            if abs(np.linalg.det(jacobian)) <= 1e-15 * scale * scale:
                raise ValueError("singular moving solved-field domain map")
            natural -= np.linalg.solve(jacobian, residual)
            if not np.all(np.isfinite(natural)):
                break
        raise ValueError("moving solved-field bilinear domain inverse did not converge")

    def _moving_field_values_and_derivatives(
        self, x, y, z, *, require_unique_domain=False, domain_index=None,
    ):
        x, y, z = float(x), float(y), float(z)
        element = self._element_index(x)
        start = self._element_x_starts[element]
        end = self._element_x_ends[element]
        xi = 2.0 * (x - start) / (end - start) - 1.0
        xi_powers, xi_derivatives = self._powers_and_derivatives(
            xi, self._longitudinal_shape_coefficients.shape[1]
        )
        shape = self._longitudinal_shape_coefficients @ xi_powers
        shape_x = (self._longitudinal_shape_coefficients @ xi_derivatives) * (2/(end-start))
        vertices = self.domain_vertices_at(x)
        domain = self._solved_field_domain_index(
            y, z, require_unique=require_unique_domain, domain_index=domain_index,
            vertices_at_x=vertices,
        )
        coords, weights, jacobian = self._moving_natural_coordinates(y, z, vertices[domain])
        a, b = coords
        coeff = self._solved_nodal_domain_natural_coefficients[element, :, domain]
        a_pow, a_der = self._powers_and_derivatives(a, coeff.shape[1])
        b_pow, b_der = self._powers_and_derivatives(b, coeff.shape[2])
        nodal = np.einsum('npqc,p,q->nc', coeff, a_pow, b_pow, optimize=True)
        da = np.einsum('npqc,p,q->nc', coeff, a_der, b_pow, optimize=True)
        db = np.einsum('npqc,p,q->nc', coeff, a_pow, b_der, optimize=True)
        natural_field_grad = np.stack((shape @ da, shape @ db))
        if abs(np.linalg.det(jacobian)) <= 1e-15 * max(1., np.max(abs(vertices[domain]))) ** 2:
            raise ValueError('singular moving solved-field Jacobian')
        physical_grad = np.linalg.solve(jacobian.T, natural_field_grad)
        endpoint_velocity = (
            self._moving_domain_vertex_endpoints[1,domain]
            - self._moving_domain_vertex_endpoints[0,domain]
        ) / (self._moving_domain_x_bounds[1] - self._moving_domain_x_bounds[0])
        spatial_velocity = weights @ endpoint_velocity
        natural_velocity = -np.linalg.solve(jacobian, spatial_velocity)
        return (
            shape @ nodal,
            shape_x @ nodal + natural_velocity @ natural_field_grad,
            physical_grad[0], physical_grad[1],
        )

    @property
    def solved_domain_vertices(self) -> np.ndarray | None:
        """Read-only-by-copy transverse domain geometry of a v4 solved field.

        Domain indices are zero-based mathematical representation indices,
        not CSF domain IDs or expansion-specific L9 connectivity.
        Legacy v1-v3 checkpoints return None.
        """
        if self._solved_domain_vertices is None:
            return None
        return self._solved_domain_vertices.copy()

    def _solved_field_domain_index(
        self, y: float, z: float, *, require_unique: bool = False,
        domain_index: int | None = None,
        vertices_at_x=None,
    ) -> int:
        domain_vertices = (
            self._solved_domain_vertices if vertices_at_x is None else
            np.asarray(vertices_at_x, dtype=float)
        )
        if domain_index is not None:
            if isinstance(domain_index, (bool, np.bool_)) or not isinstance(
                domain_index, (int, np.integer)
            ):
                raise TypeError("domain_index must be a zero-based integer")
            selected = int(domain_index)
            if not 0 <= selected < len(domain_vertices):
                raise IndexError(f"domain_index {selected} is outside solved-field domains")
            if not self._point_in_polygon_inclusive_2d(
                y, z, domain_vertices[selected]
            ):
                raise ValueError(
                    f"point (y={y}, z={z}) does not belong to selected "
                    f"solved-field domain_index={selected}"
                )
            return selected

        matches = [
            index
            for index, vertices in enumerate(domain_vertices)
            if self._point_in_polygon_inclusive_2d(y, z, vertices)
        ]
        if not matches:
            raise ValueError(f"point (y={y}, z={z}) lies outside solved transverse domains")
        if require_unique and len(matches) != 1:
            raise ValueError(
                "solved-field transverse derivative is side-dependent on a shared "
                f"domain interface at (y,z)=({y},{z}); domains={matches}. "
                "Pass domain_index explicitly to select a one-sided derivative."
            )
        # A conforming C0 displacement has a unique value on a shared edge.
        # The persisted domain order supplies a deterministic evaluation side
        # for displacement only; no derivative is silently selected or averaged.
        return int(matches[0])

    def _solved_field_values_and_derivatives(
        self, x, y, z, *, require_unique_domain: bool = False,
        domain_index: int | None = None,
    ):
        x = float(x)
        y = float(y)
        z = float(z)
        index = self._element_index(x)
        start = float(self._element_x_starts[index])
        end = float(self._element_x_ends[index])
        length = end - start
        xi = 2.0 * (x - start) / length - 1.0
        xi_powers, xi_derivatives = self._powers_and_derivatives(
            xi, self._longitudinal_shape_coefficients.shape[1]
        )
        shape_values = self._longitudinal_shape_coefficients @ xi_powers
        shape_derivatives_x = (
            self._longitudinal_shape_coefficients @ xi_derivatives
        ) * (2.0 / length)
        domain = self._solved_field_domain_index(
            y, z, require_unique=require_unique_domain, domain_index=domain_index
        )
        coeff = self._solved_nodal_domain_power_coefficients[index, :, domain]
        y_powers, y_derivatives = self._powers_and_derivatives(y, coeff.shape[1])
        z_powers, z_derivatives = self._powers_and_derivatives(z, coeff.shape[2])
        nodal_values = np.einsum("npqc,p,q->nc", coeff, y_powers, z_powers, optimize=True)
        nodal_dy = np.einsum("npqc,p,q->nc", coeff, y_derivatives, z_powers, optimize=True)
        nodal_dz = np.einsum("npqc,p,q->nc", coeff, y_powers, z_derivatives, optimize=True)
        value = shape_values @ nodal_values
        derivative_x = shape_derivatives_x @ nodal_values
        derivative_y = shape_values @ nodal_dy
        derivative_z = shape_values @ nodal_dz
        return tuple(np.asarray(v, dtype=float) for v in (value, derivative_x, derivative_y, derivative_z))

    def displacement_gradient(
        self, x: float, y: float, z: float, *, domain_index: int | None = None
    ) -> np.ndarray:
        """Evaluate the exact analytical gradient of the compiled CUF field.

        The returned matrix uses displacement components by rows and physical
        coordinates ``(x, y, z)`` by columns, i.e. ``gradient[i, j] = du_i/dx_j``.
        No finite differences, sampling, smoothing, or fitted recovery is used.
        """

        if self._solved_nodal_domain_natural_coefficients is not None:
            _, derivative_x, derivative_y, derivative_z = (
                self._moving_field_values_and_derivatives(
                    x, y, z, require_unique_domain=True,
                    domain_index=domain_index,
                )
            )
        elif self._solved_nodal_domain_power_coefficients is not None:
            _, derivative_x, derivative_y, derivative_z = (
                self._solved_field_values_and_derivatives(
                    x, y, z, require_unique_domain=True,
                    domain_index=domain_index,
                )
            )
        else:
            if domain_index is not None:
                raise ValueError(
                    "domain_index applies only to domain-wise solved-field checkpoints v4"
                )
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
        *,
        domain_index: int | None = None,
    ) -> np.ndarray:
        """Return the exact analytical vector du_i/dx from the solved field."""

        return self.displacement_gradient(x, y, z, domain_index=domain_index)[:, 0].copy()

    def displacement_derivative_y(
        self,
        x: float,
        y: float,
        z: float,
        *,
        domain_index: int | None = None,
    ) -> np.ndarray:
        """Return the exact analytical vector du_i/dy from the solved field."""

        return self.displacement_gradient(x, y, z, domain_index=domain_index)[:, 1].copy()

    def displacement_derivative_z(
        self,
        x: float,
        y: float,
        z: float,
        *,
        domain_index: int | None = None,
    ) -> np.ndarray:
        """Return the exact analytical vector du_i/dz from the solved field."""

        return self.displacement_gradient(x, y, z, domain_index=domain_index)[:, 2].copy()

    def strain(
        self, x: float, y: float, z: float, *, domain_index: int | None = None
    ) -> np.ndarray:
        """Evaluate the continuous six-component small-strain field.

        Voigt order:
            [epsilon_xx, epsilon_yy, epsilon_zz,
             gamma_yz, gamma_xz, gamma_xy]
        """

        gradient = self.displacement_gradient(x, y, z, domain_index=domain_index)
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
        if self._solved_nodal_domain_natural_coefficients is not None:
            self._element_index(x)
            def evaluate(y: float, z: float) -> np.ndarray:
                value, _, _, _ = self._moving_field_values_and_derivatives(x, y, z)
                return value.copy()
            return evaluate

        if self._solved_nodal_domain_power_coefficients is not None:
            def evaluate(y: float, z: float) -> np.ndarray:
                value, _, _, _ = self._solved_field_values_and_derivatives(x, y, z)
                return value.copy()
            return evaluate

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
        if self._solved_nodal_domain_natural_coefficients is not None:
            return _MOVING_SOLVED_FIELD_FORMAT_VERSION
        if self._solved_nodal_domain_power_coefficients is not None:
            return _SOLVED_FIELD_FORMAT_VERSION
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

                if format_version == _MOVING_SOLVED_FIELD_FORMAT_VERSION:
                    payload["moving_domain_vertex_endpoints"] = self._moving_domain_vertex_endpoints
                    payload["solved_nodal_domain_natural_coefficients"] = (
                        self._solved_nodal_domain_natural_coefficients
                    )
                    payload["moving_domain_x_bounds"] = self._moving_domain_x_bounds
                elif format_version == _SOLVED_FIELD_FORMAT_VERSION:
                    payload["solved_domain_vertices"] = self._solved_domain_vertices
                    payload["solved_nodal_domain_power_coefficients"] = (
                        self._solved_nodal_domain_power_coefficients
                    )
                elif format_version == _STATIC_FORMAT_VERSION:
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
            has_moving = any(name in names for name in (
                "moving_domain_vertex_endpoints",
                "solved_nodal_domain_natural_coefficients",
                "moving_domain_x_bounds",
            ))
            has_solved_field = (
                "solved_domain_vertices" in names
                or "solved_nodal_domain_power_coefficients" in names
            )

            if sum((has_static, has_variable, has_segmented, has_solved_field, has_moving)) != 1:
                raise ValueError(
                    "compiled displacement checkpoint must contain exactly one "
                    "transverse field representation"
                )
            if has_moving and not {
                "moving_domain_vertex_endpoints",
                "solved_nodal_domain_natural_coefficients",
                "moving_domain_x_bounds",
            }.issubset(names):
                raise ValueError("moving solved-field checkpoint is incomplete")
            if has_solved_field and not {
                "solved_domain_vertices",
                "solved_nodal_domain_power_coefficients",
            }.issubset(names):
                raise ValueError(
                    "solved-field compiled displacement checkpoint is incomplete"
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

            if has_moving:
                return cls(
                    moving_domain_vertex_endpoints=archive["moving_domain_vertex_endpoints"],
                    solved_nodal_domain_natural_coefficients=(
                        archive["solved_nodal_domain_natural_coefficients"]
                    ),
                    moving_domain_x_bounds=archive["moving_domain_x_bounds"],
                    **common,
                )
            if has_solved_field:
                return cls(
                    solved_domain_vertices=archive["solved_domain_vertices"],
                    solved_nodal_domain_power_coefficients=(
                        archive["solved_nodal_domain_power_coefficients"]
                    ),
                    **common,
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

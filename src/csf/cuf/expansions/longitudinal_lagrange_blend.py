# Version: CSF-CUF explicit x-dependent transverse expansion v2.1 - 2026-09-15
"""Longitudinally varying transverse CUF expansion.

This plugin makes the axial dependence of a transverse expansion explicit.
It supports both the original smooth Lagrange blend and a segmented law in
which one complete transverse expansion is selected on each longitudinal
interval.
In CSF-CUF coordinates ``x`` is the beam axis and ``(y,z)`` are transverse.
The basis returned by this plugin is

    F_tau(x,y,z) = sum_i L_i(x) F_tau^(i)(x,y,z)

where ``L_i`` are Lagrange interpolation weights associated with user-defined
axial states and ``F_tau^(i)`` are ordinary CUF expansion plugins.

For child expansions that are longitudinally constant this reduces to

    F_tau(x,y,z) = sum_i L_i(x) F_tau^(i)(y,z)

and the required axial derivative is evaluated exactly as

    dF_tau/dx = sum_i [
        dL_i/dx F_tau^(i) + L_i dF_tau^(i)/dx
    ].

The second term preserves composability: a child expansion may itself depend
on x.  Classical child expansions simply contribute zero there through the
CUFBasis backward-compatible default.

The formulation is deliberately expressed in terms of axial *states*, not FE
nodes.  It is therefore a genuine transverse-expansion plugin and remains
independent of the longitudinal FE discretization used by the solver.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    get_cuf_basis_plugin,
    register_cuf_basis_plugin,
)


_PLUGIN_NAME = "longitudinal_lagrange_blend"


@dataclass(frozen=True)
class _ExpansionState:
    x: float
    basis_name: str
    basis: object
    section_gauss_minimum: int
    longitudinal_transverse_degree: int


@dataclass(frozen=True)
class _ExpansionSegment:
    x_start: float
    x_end: float
    basis_name: str
    basis: object
    definition_key: tuple
    section_gauss_minimum: int
    longitudinal_transverse_degree: int


class LongitudinalSegmentedBasis(CUFBasis):
    """Piecewise longitudinal law selecting one transverse basis per interval.

    The object is intentionally still a normal :class:`CUFBasis`: existing
    sectional/nucleus code can evaluate it at physical ``x`` without knowing
    about segmentation.  In addition, ``segments`` and ``boundaries`` expose
    the longitudinal law to the solver so it can validate the FE partition.

    Internal boundaries are right-continuous for direct point evaluation; the
    global right endpoint belongs to the final segment.  In STEP 1, boundaries
    may lie on any longitudinal FE node only when adjacent segments use the
    same child-expansion definition, so the selector introduces no actual
    discontinuity inside an element.
    """

    def __init__(self, *, segments: Sequence[_ExpansionSegment], configured_order: int) -> None:
        segments = tuple(segments)
        if not segments:
            raise ValueError("segmented longitudinal expansion requires at least one segment")

        previous_end = None
        sizes = []
        for index, segment in enumerate(segments, start=1):
            x_start = float(segment.x_start)
            x_end = float(segment.x_end)
            if not (math.isfinite(x_start) and math.isfinite(x_end) and x_end > x_start):
                raise ValueError(f"segment {index} must satisfy finite x_end > x_start")
            if previous_end is not None and not math.isclose(
                x_start, previous_end, rel_tol=0.0, abs_tol=1.0e-12 * max(1.0, abs(previous_end))
            ):
                raise ValueError("segmented longitudinal expansion must be contiguous")
            previous_end = x_end
            sizes.append(int(segment.basis.size))

        if any(size < 1 for size in sizes):
            raise ValueError("every segmented child basis must be non-empty")

        self._segments = segments
        self._configured_order = int(configured_order)
        self._size = max(sizes)
        self._boundaries = tuple(
            [float(segments[0].x_start)]
            + [float(segment.x_end) for segment in segments]
        )

    @property
    def order(self) -> int:
        return self._configured_order

    @property
    def size(self) -> int:
        return self._size

    @property
    def segments(self) -> tuple[_ExpansionSegment, ...]:
        return self._segments

    @property
    def boundaries(self) -> tuple[float, ...]:
        return self._boundaries

    @property
    def section_gauss_minimum(self) -> int:
        return max(segment.section_gauss_minimum for segment in self._segments)

    @property
    def longitudinal_transverse_degree(self) -> int:
        # No artificial polynomial degree is introduced by the selector itself.
        # Inside every segment only the selected child expansion contributes.
        return max(
            segment.longitudinal_transverse_degree for segment in self._segments
        )

    def _require_x(self, x: float | None) -> float:
        if x is None:
            raise ValueError(
                "segmented longitudinal expansion requires the physical axial "
                "coordinate x during basis evaluation"
            )
        x = float(x)
        if not math.isfinite(x):
            raise ValueError("x must be finite")
        return x

    def _validate_tau(self, tau: int) -> int:
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}, got {tau}")
        return tau

    def basis_at(self, x: float):
        x = self._require_x(x)
        x0 = self._boundaries[0]
        x1 = self._boundaries[-1]
        tol = 1.0e-12 * max(1.0, abs(x0), abs(x1))
        if x < x0 - tol or x > x1 + tol:
            raise ValueError(
                f"x={x} lies outside segmented expansion domain [{x0}, {x1}]"
            )

        if x >= x1 - tol:
            return self._segments[-1].basis

        # Right-continuous selection at internal interfaces.
        for segment in self._segments:
            if x < float(segment.x_end) - tol:
                return segment.basis
        return self._segments[-1].basis

    def value(self, tau: int, y: float, z: float, *, x: float | None = None) -> float:
        tau = self._validate_tau(tau)
        x = self._require_x(x)
        basis = self.basis_at(x)
        if tau > int(basis.size):
            return 0.0
        return float(basis.value(tau, float(y), float(z), x=x))

    def values(self, y: float, z: float, *, x: float | None = None) -> np.ndarray:
        x = self._require_x(x)
        basis = self.basis_at(x)
        active_size = int(basis.size)
        if hasattr(basis, "values"):
            active = np.asarray(basis.values(float(y), float(z), x=x), dtype=float)
        else:
            active = np.asarray(
                [basis.value(tau, float(y), float(z), x=x) for tau in range(1, active_size + 1)],
                dtype=float,
            )
        if active.shape != (active_size,):
            raise ValueError("segmented child basis returned an invalid values() shape")
        values = np.zeros(self._size, dtype=float)
        values[:active_size] = active
        return values

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        if direction not in {"y", "z"}:
            raise ValueError("direction must be 'y' or 'z'")
        tau = self._validate_tau(tau)
        x = self._require_x(x)
        basis = self.basis_at(x)
        if tau > int(basis.size):
            return 0.0
        return float(basis.derivative(tau, direction, float(y), float(z), x=x))

    def longitudinal_derivative(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """Return the child dF/dx inside the active open segment.

        A discontinuous selector has no classical derivative at an interface.
        Those interfaces are deliberately handled by the longitudinal solver
        partition (and later by bond constraints), not by smearing a derivative
        through the section integral.
        """
        tau = self._validate_tau(tau)
        x = self._require_x(x)
        basis = self.basis_at(x)
        if tau > int(basis.size):
            return 0.0
        method = getattr(basis, "longitudinal_derivative", None)
        if method is None:
            return 0.0
        return float(method(tau, float(y), float(z), x=x))


class LongitudinalLagrangeBlendBasis(CUFBasis):
    """Explicit ``F_tau(x,y,z)`` obtained from axial Lagrange blending.

    Every state supplies one complete transverse basis.  In the default
    ``strict`` size policy all state bases must expose the same number of
    terms, so a fixed global ``tau`` has an unambiguous meaning at every x.

    ``zero_pad`` is available for intentionally nested/hierarchical bases.
    Under that policy the global size is the largest state size and a state
    contributes zero whenever ``tau`` exceeds its local size.  This policy is
    mathematically explicit but should only be used when the caller knows that
    the local tau ordering is compatible across the selected child bases.
    """

    def __init__(
        self,
        *,
        states: Sequence[_ExpansionState],
        configured_order: int,
        size_policy: str = "strict",
    ) -> None:
        states = tuple(states)
        if not states:
            raise ValueError(
                "longitudinal_lagrange_blend requires at least one state"
            )

        xs = np.asarray([float(state.x) for state in states], dtype=float)
        if not np.all(np.isfinite(xs)):
            raise ValueError("all longitudinal blend state coordinates must be finite")
        if np.unique(xs).size != xs.size:
            raise ValueError(
                "longitudinal blend state coordinates must be pairwise distinct"
            )

        policy = str(size_policy).strip().lower()
        if policy not in {"strict", "zero_pad"}:
            raise ValueError(
                "longitudinal_lagrange_blend size_policy must be "
                "'strict' or 'zero_pad'"
            )

        sizes = tuple(int(state.basis.size) for state in states)
        if any(size < 1 for size in sizes):
            raise ValueError("every longitudinal blend state basis must be non-empty")

        if policy == "strict" and len(set(sizes)) != 1:
            details = ", ".join(
                f"{state.basis_name}:{size}"
                for state, size in zip(states, sizes)
            )
            raise ValueError(
                "longitudinal_lagrange_blend states must have the same basis "
                "size under size_policy='strict'; got " + details
            )

        self._states = states
        self._x_nodes = xs
        self._size_policy = policy
        self._size = sizes[0] if policy == "strict" else max(sizes)
        self._configured_order = int(configured_order)

        # Denominators of the Lagrange cardinal polynomials are constant and
        # are precomputed once.  Numerators remain functions of physical x.
        denominators = np.ones(xs.size, dtype=float)
        for i in range(xs.size):
            for j in range(xs.size):
                if i == j:
                    continue
                denominators[i] *= xs[i] - xs[j]
        self._lagrange_denominators = denominators

    @property
    def order(self) -> int:
        """Return the parent CUF order used as the default child order."""
        return self._configured_order

    @property
    def size(self) -> int:
        return self._size

    @property
    def states(self) -> tuple[_ExpansionState, ...]:
        return self._states

    @property
    def x_nodes(self) -> tuple[float, ...]:
        return tuple(float(value) for value in self._x_nodes)

    @property
    def size_policy(self) -> str:
        return self._size_policy

    @property
    def state_count(self) -> int:
        return len(self._states)

    @property
    def section_gauss_minimum(self) -> int:
        return max(state.section_gauss_minimum for state in self._states)

    @property
    def longitudinal_transverse_degree(self) -> int:
        # Each L_i has degree state_count-1.  A sectional coefficient contains
        # a product of two basis factors, so axial blending can add at most
        # 2*(state_count-1) polynomial degrees.  Child declarations already
        # account for their own transverse/explicit-x contribution.
        child_degree = max(
            state.longitudinal_transverse_degree for state in self._states
        )
        return int(child_degree + 2 * (self.state_count - 1))

    def _require_x(self, x: float | None) -> float:
        if x is None:
            raise ValueError(
                "longitudinal_lagrange_blend requires the physical axial "
                "coordinate x during basis evaluation"
            )
        x = float(x)
        if not math.isfinite(x):
            raise ValueError("x must be finite")
        return x

    def _validate_tau(self, tau: int) -> int:
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}, got {tau}")
        return tau

    def _weights_and_derivatives(self, x: float) -> tuple[np.ndarray, np.ndarray]:
        """Return L_i(x) and dL_i/dx in physical coordinates."""
        count = self._x_nodes.size
        if count == 1:
            return (
                np.asarray([1.0], dtype=float),
                np.asarray([0.0], dtype=float),
            )

        weights = np.empty(count, dtype=float)
        derivatives = np.zeros(count, dtype=float)

        for i in range(count):
            numerator = 1.0
            for j in range(count):
                if i == j:
                    continue
                numerator *= x - self._x_nodes[j]
            weights[i] = numerator / self._lagrange_denominators[i]

            # Derivative of the product defining the i-th cardinal function.
            derivative_numerator = 0.0
            for k in range(count):
                if k == i:
                    continue
                term = 1.0
                for j in range(count):
                    if j == i or j == k:
                        continue
                    term *= x - self._x_nodes[j]
                derivative_numerator += term
            derivatives[i] = (
                derivative_numerator / self._lagrange_denominators[i]
            )

        return weights, derivatives

    @staticmethod
    def _local_value(state: _ExpansionState, tau: int, y: float, z: float, x: float) -> float:
        if tau > int(state.basis.size):
            return 0.0
        return float(state.basis.value(tau, y, z, x=x))

    @staticmethod
    def _local_derivative(
        state: _ExpansionState,
        tau: int,
        direction: str,
        y: float,
        z: float,
        x: float,
    ) -> float:
        if tau > int(state.basis.size):
            return 0.0
        return float(state.basis.derivative(tau, direction, y, z, x=x))

    @staticmethod
    def _local_longitudinal_derivative(
        state: _ExpansionState,
        tau: int,
        y: float,
        z: float,
        x: float,
    ) -> float:
        if tau > int(state.basis.size):
            return 0.0
        method = getattr(state.basis, "longitudinal_derivative", None)
        if method is None:
            return 0.0
        return float(method(tau, y, z, x=x))

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        tau = self._validate_tau(tau)
        x = self._require_x(x)
        weights, _ = self._weights_and_derivatives(x)

        value = 0.0
        for weight, state in zip(weights, self._states):
            if weight == 0.0:
                continue
            value += float(weight) * self._local_value(
                state, tau, float(y), float(z), x
            )
        return float(value)

    def values(
        self,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> np.ndarray:
        x = self._require_x(x)
        weights, _ = self._weights_and_derivatives(x)
        output = np.zeros(self._size, dtype=float)

        for weight, state in zip(weights, self._states):
            if weight == 0.0:
                continue
            local_size = int(state.basis.size)
            if hasattr(state.basis, "values"):
                local = np.asarray(
                    state.basis.values(float(y), float(z), x=x),
                    dtype=float,
                )
                if local.shape != (local_size,):
                    raise ValueError(
                        f"child basis {state.basis_name!r} returned an invalid "
                        "values() shape"
                    )
            else:
                local = np.asarray(
                    [
                        state.basis.value(tau, float(y), float(z), x=x)
                        for tau in range(1, local_size + 1)
                    ],
                    dtype=float,
                )
            output[:local_size] += float(weight) * local

        return output

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        if direction not in {"y", "z"}:
            raise ValueError("direction must be 'y' or 'z'")

        tau = self._validate_tau(tau)
        x = self._require_x(x)
        weights, _ = self._weights_and_derivatives(x)

        value = 0.0
        for weight, state in zip(weights, self._states):
            if weight == 0.0:
                continue
            value += float(weight) * self._local_derivative(
                state,
                tau,
                direction,
                float(y),
                float(z),
                x,
            )
        return float(value)

    def longitudinal_derivative(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """Return the exact product-rule derivative ``dF_tau/dx``."""
        tau = self._validate_tau(tau)
        x = self._require_x(x)
        weights, derivatives = self._weights_and_derivatives(x)

        value = 0.0
        for weight, weight_dx, state in zip(
            weights,
            derivatives,
            self._states,
        ):
            local_value = self._local_value(
                state, tau, float(y), float(z), x
            )
            local_dx = self._local_longitudinal_derivative(
                state, tau, float(y), float(z), x
            )
            value += float(weight_dx) * local_value
            value += float(weight) * local_dx

        return float(value)


def _as_mapping(value, label: str) -> dict:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return dict(value)


def _freeze_definition_value(value):
    """Return a stable immutable representation of YAML/plugin options.

    The segmented STEP-1 validator uses this only to decide whether two
    adjacent segments were built from the same child-expansion definition.
    It deliberately compares the construction specification, not object
    identity, because each segment owns a separately built basis instance.
    """
    if isinstance(value, Mapping):
        return tuple(
            sorted(
                (str(key), _freeze_definition_value(item))
                for key, item in value.items()
            )
        )
    if isinstance(value, np.ndarray):
        return tuple(_freeze_definition_value(item) for item in value.tolist())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_freeze_definition_value(item) for item in value)
    if isinstance(value, np.generic):
        return value.item()
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


def _state_x(spec: dict, *, x0: float, x1: float, index: int) -> float:
    has_x = "x" in spec
    has_fraction = "x_fraction" in spec
    if has_x == has_fraction:
        raise ValueError(
            f"longitudinal_lagrange_blend state {index} must define exactly "
            "one of 'x' or 'x_fraction'"
        )

    if has_x:
        x = float(spec.pop("x"))
    else:
        fraction = float(spec.pop("x_fraction"))
        if not math.isfinite(fraction):
            raise ValueError(f"state {index} x_fraction must be finite")
        x = x0 + fraction * (x1 - x0)

    if not math.isfinite(x):
        raise ValueError(f"state {index} axial coordinate must be finite")
    return float(x)


def _build(*, order, section_provider, continuous_section_field, options):
    options = dict(options or {})

    interpolation = str(options.pop("interpolation", "lagrange")).strip().lower()
    if interpolation not in {"lagrange", "segmented"}:
        raise ValueError(
            "longitudinal_lagrange_blend interpolation must be "
            "'lagrange' or 'segmented'"
        )

    # ``size_policy`` belongs only to the smooth Lagrange-blend path.
    # Segmented interpolation always uses the actual child-basis size of each
    # segment and couples unequal spaces through the longitudinal perfect bond.
    size_policy_option = options.pop("size_policy", None)
    state_specs = options.pop("states", None)
    segment_specs = options.pop("segments", None)
    if options:
        raise ValueError(
            "unsupported longitudinal_lagrange_blend cuf.basis_options: "
            f"{sorted(options)}"
        )

    x0, x1 = map(float, section_provider.longitudinal_domain())
    if not (math.isfinite(x0) and math.isfinite(x1) and x1 > x0):
        raise ValueError("CSF longitudinal domain must satisfy finite x1 > x0")

    parent_order = int(order)

    if interpolation == "segmented":
        if state_specs is not None:
            raise ValueError(
                "segmented interpolation uses basis_options.segments, not states"
            )
        # No size policy is required for segmented interpolation.  A legacy
        # size_policy key is accepted for YAML compatibility but has no effect.
        if not isinstance(segment_specs, Sequence) or isinstance(segment_specs, (str, bytes)):
            raise TypeError(
                "longitudinal_lagrange_blend basis_options.segments must be a sequence"
            )
        if not segment_specs:
            raise ValueError(
                "longitudinal_lagrange_blend basis_options.segments must not be empty"
            )

        segments = []
        for index, raw_spec in enumerate(segment_specs, start=1):
            spec = _as_mapping(raw_spec, f"segment {index}")

            has_start = "x_start" in spec
            has_start_fraction = "x_start_fraction" in spec
            has_end = "x_end" in spec
            has_end_fraction = "x_end_fraction" in spec
            if has_start == has_start_fraction or has_end == has_end_fraction:
                raise ValueError(
                    f"segment {index} must define exactly one of x_start/x_start_fraction "
                    "and exactly one of x_end/x_end_fraction"
                )

            if has_start:
                segment_start = float(spec.pop("x_start"))
            else:
                fraction = float(spec.pop("x_start_fraction"))
                segment_start = x0 + fraction * (x1 - x0)

            if has_end:
                segment_end = float(spec.pop("x_end"))
            else:
                fraction = float(spec.pop("x_end_fraction"))
                segment_end = x0 + fraction * (x1 - x0)

            basis_name = str(spec.pop("basis", "")).strip()
            if not basis_name:
                raise ValueError(f"segment {index} must define a non-empty basis name")
            if basis_name == _PLUGIN_NAME:
                raise ValueError(
                    "longitudinal_lagrange_blend cannot directly use itself as a child basis"
                )

            child_order = int(spec.pop("order", parent_order))
            child_options = _as_mapping(
                spec.pop("basis_options", {}),
                f"segment {index}.basis_options",
            )
            if spec:
                raise ValueError(
                    f"unsupported keys in longitudinal segment {index}: {sorted(spec)}"
                )

            definition_key = (
                basis_name,
                int(child_order),
                _freeze_definition_value(child_options),
            )
            child_plugin = get_cuf_basis_plugin(basis_name)
            child_basis = child_plugin.build(
                order=child_order,
                section_provider=section_provider,
                continuous_section_field=continuous_section_field,
                options=child_options,
            )
            segments.append(
                _ExpansionSegment(
                    x_start=float(segment_start),
                    x_end=float(segment_end),
                    basis_name=basis_name,
                    basis=child_basis,
                    definition_key=definition_key,
                    section_gauss_minimum=child_plugin.minimum_section_gauss_order(child_basis),
                    longitudinal_transverse_degree=child_plugin.transverse_x_polynomial_degree(child_basis),
                )
            )

        segments.sort(key=lambda item: item.x_start)
        tol = 1.0e-12 * max(1.0, abs(x0), abs(x1))
        if not math.isclose(segments[0].x_start, x0, rel_tol=0.0, abs_tol=tol):
            raise ValueError("segmented expansion must start at the CSF longitudinal domain start")
        if not math.isclose(segments[-1].x_end, x1, rel_tol=0.0, abs_tol=tol):
            raise ValueError("segmented expansion must end at the CSF longitudinal domain end")

        return LongitudinalSegmentedBasis(
            segments=segments,
            configured_order=parent_order,
        )

    if segment_specs is not None:
        raise ValueError(
            "lagrange interpolation uses basis_options.states, not segments"
        )
    size_policy = (
        "strict"
        if size_policy_option is None
        else str(size_policy_option).strip().lower()
    )
    if not isinstance(state_specs, Sequence) or isinstance(state_specs, (str, bytes)):
        raise TypeError(
            "longitudinal_lagrange_blend basis_options.states must be a sequence"
        )
    if not state_specs:
        raise ValueError(
            "longitudinal_lagrange_blend basis_options.states must not be empty"
        )

    states = []

    for index, raw_spec in enumerate(state_specs, start=1):
        spec = _as_mapping(raw_spec, f"state {index}")
        x = _state_x(spec, x0=x0, x1=x1, index=index)

        basis_name = str(spec.pop("basis", "")).strip()
        if not basis_name:
            raise ValueError(f"state {index} must define a non-empty basis name")
        if basis_name == _PLUGIN_NAME:
            raise ValueError(
                "longitudinal_lagrange_blend cannot directly use itself as a "
                "child basis"
            )

        child_order = int(spec.pop("order", parent_order))
        child_options = spec.pop("basis_options", {})
        child_options = _as_mapping(
            child_options,
            f"state {index}.basis_options",
        )
        if spec:
            raise ValueError(
                f"unsupported keys in longitudinal blend state {index}: "
                f"{sorted(spec)}"
            )

        child_plugin = get_cuf_basis_plugin(basis_name)
        child_basis = child_plugin.build(
            order=child_order,
            section_provider=section_provider,
            continuous_section_field=continuous_section_field,
            options=child_options,
        )

        states.append(
            _ExpansionState(
                x=x,
                basis_name=basis_name,
                basis=child_basis,
                section_gauss_minimum=(
                    child_plugin.minimum_section_gauss_order(child_basis)
                ),
                longitudinal_transverse_degree=(
                    child_plugin.transverse_x_polynomial_degree(child_basis)
                ),
            )
        )

    states.sort(key=lambda item: item.x)

    return LongitudinalLagrangeBlendBasis(
        states=states,
        configured_order=parent_order,
        size_policy=size_policy,
    )


def _section_gauss_minimum(basis):
    if not isinstance(
        basis,
        (LongitudinalLagrangeBlendBasis, LongitudinalSegmentedBasis),
    ):
        raise TypeError(
            "longitudinal_lagrange_blend received an incompatible basis"
        )
    return basis.section_gauss_minimum


def _longitudinal_transverse_degree(basis):
    if not isinstance(
        basis,
        (LongitudinalLagrangeBlendBasis, LongitudinalSegmentedBasis),
    ):
        raise TypeError(
            "longitudinal_lagrange_blend received an incompatible basis"
        )
    return basis.longitudinal_transverse_degree


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name=_PLUGIN_NAME,
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=_longitudinal_transverse_degree,
    )
)

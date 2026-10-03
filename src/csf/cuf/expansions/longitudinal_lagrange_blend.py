# Version: CSF-CUF explicit x-dependent transverse expansion plugin v3 - 2026-09-30
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

import math
from typing import Mapping, Sequence

import numpy as np

from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    get_cuf_basis_plugin,
    register_cuf_basis_plugin,
)
from csf.cuf.numerics.longitudinal_lagrange_blend import (
    LongitudinalLagrangeBlendBasis,
    LongitudinalSegmentedBasis,
    _ExpansionSegment,
    _ExpansionState,
)


_PLUGIN_NAME = "longitudinal_lagrange_blend"


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

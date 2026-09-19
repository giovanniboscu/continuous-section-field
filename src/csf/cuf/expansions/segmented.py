# Version: CSF-CUF direct segmented expansion law v1.0 - 2026-09-15
"""Direct piecewise longitudinal selection of transverse CUF expansions.

This module is intentionally *not* a CUF basis plugin.  A segmented law is a
longitudinal routing rule owned by the case/solver layer:

    [x0, x1] -> transverse basis A
    [x1, x2] -> transverse basis B
    ...

The child transverse bases remain ordinary registered CUF basis plugins.  The
runtime object below only adapts that piecewise law to the existing generic
CUFBasis evaluation contract used by sectional integration and recovery.  It
is therefore an internal dispatcher, not a user-selectable wrapper expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import get_cuf_basis_plugin


@dataclass(frozen=True)
class ExpansionSegment:
    x_start: float
    x_end: float
    basis_name: str
    basis: object
    definition_key: tuple
    section_gauss_minimum: int
    longitudinal_transverse_degree: int


def _as_mapping(value, label: str) -> dict:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return dict(value)


def _freeze_definition_value(value):
    """Return a stable immutable representation of child plugin options."""
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


def _segment_coordinate(
    spec: dict,
    *,
    absolute_key: str,
    fraction_key: str,
    x0: float,
    x1: float,
    index: int,
) -> float:
    has_absolute = absolute_key in spec
    has_fraction = fraction_key in spec
    if has_absolute == has_fraction:
        raise ValueError(
            f"segment {index} must define exactly one of "
            f"{absolute_key}/{fraction_key}"
        )

    if has_absolute:
        value = float(spec.pop(absolute_key))
    else:
        fraction = float(spec.pop(fraction_key))
        if not math.isfinite(fraction):
            raise ValueError(f"segment {index} {fraction_key} must be finite")
        value = x0 + fraction * (x1 - x0)

    if not math.isfinite(value):
        raise ValueError(f"segment {index} longitudinal coordinate must be finite")
    return float(value)


class SegmentedExpansionLaw(CUFBasis):
    """Piecewise longitudinal routing law for complete transverse bases.

    ``size`` is the maximum child basis size so the existing CUF core can keep
    one envelope for generic evaluation.  The actual number of active terms is
    still retained per segment and is passed separately to the DOF layout by
    the solver.

    ``order`` exists only as a compatibility/numerical-envelope property for
    code that asks a generic CUFBasis for an order.  It is the maximum child
    order and is *not* a global expansion order of the segmented model.
    """

    def __init__(self, *, segments: Sequence[ExpansionSegment]) -> None:
        segments = tuple(segments)
        if not segments:
            raise ValueError("cuf.segments must contain at least one segment")

        previous_end = None
        sizes = []
        orders = []
        for index, segment in enumerate(segments, start=1):
            x_start = float(segment.x_start)
            x_end = float(segment.x_end)
            if not (
                math.isfinite(x_start)
                and math.isfinite(x_end)
                and x_end > x_start
            ):
                raise ValueError(
                    f"segment {index} must satisfy finite x_end > x_start"
                )
            if previous_end is not None:
                tol = 1.0e-12 * max(1.0, abs(previous_end))
                if not math.isclose(
                    x_start,
                    previous_end,
                    rel_tol=0.0,
                    abs_tol=tol,
                ):
                    raise ValueError("cuf.segments must be contiguous")
            previous_end = x_end

            size = int(segment.basis.size)
            if size < 1:
                raise ValueError("every segmented child basis must be non-empty")
            sizes.append(size)

            child_order = getattr(segment.basis, "order", None)
            if child_order is not None:
                orders.append(int(child_order))

        self._segments = segments
        self._size = max(sizes)
        self._order = max(orders) if orders else 0
        self._boundaries = tuple(
            [float(segments[0].x_start)]
            + [float(segment.x_end) for segment in segments]
        )

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._size

    @property
    def segments(self) -> tuple[ExpansionSegment, ...]:
        return self._segments

    @property
    def boundaries(self) -> tuple[float, ...]:
        return self._boundaries

    @property
    def section_gauss_minimum(self) -> int:
        return max(segment.section_gauss_minimum for segment in self._segments)

    @property
    def longitudinal_transverse_degree(self) -> int:
        # The selector itself introduces no polynomial x dependence inside an
        # open segment.  Only the active child basis contributes.
        return max(
            segment.longitudinal_transverse_degree
            for segment in self._segments
        )

    def _require_x(self, x: float | None) -> float:
        if x is None:
            raise ValueError(
                "segmented expansion requires the physical axial coordinate x"
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
        basis = self.basis_at(x)
        if tau > int(basis.size):
            return 0.0
        return float(basis.value(tau, float(y), float(z), x=x))

    def values(
        self,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> np.ndarray:
        x = self._require_x(x)
        basis = self.basis_at(x)
        active_size = int(basis.size)
        if hasattr(basis, "values"):
            active = np.asarray(
                basis.values(float(y), float(z), x=x),
                dtype=float,
            )
        else:
            active = np.asarray(
                [
                    basis.value(tau, float(y), float(z), x=x)
                    for tau in range(1, active_size + 1)
                ],
                dtype=float,
            )
        if active.shape != (active_size,):
            raise ValueError(
                "segmented child basis returned an invalid values() shape"
            )
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
        return float(
            basis.derivative(tau, direction, float(y), float(z), x=x)
        )

    def longitudinal_derivative(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """Return the active child's dF/dx inside an open segment."""
        tau = self._validate_tau(tau)
        x = self._require_x(x)
        basis = self.basis_at(x)
        if tau > int(basis.size):
            return 0.0
        method = getattr(basis, "longitudinal_derivative", None)
        if method is None:
            return 0.0
        return float(method(tau, float(y), float(z), x=x))


def build_segmented_expansion(
    *,
    segment_specs,
    section_provider,
    continuous_section_field,
) -> SegmentedExpansionLaw:
    """Build a direct segmented expansion law from ``cuf.segments``."""

    if not isinstance(segment_specs, Sequence) or isinstance(
        segment_specs,
        (str, bytes),
    ):
        raise TypeError("cuf.segments must be a sequence")
    if not segment_specs:
        raise ValueError("cuf.segments must not be empty")

    x0, x1 = map(float, section_provider.longitudinal_domain())
    if not (math.isfinite(x0) and math.isfinite(x1) and x1 > x0):
        raise ValueError("CSF longitudinal domain must satisfy finite x1 > x0")

    segments = []
    for index, raw_spec in enumerate(segment_specs, start=1):
        spec = _as_mapping(raw_spec, f"cuf.segments[{index - 1}]")

        segment_start = _segment_coordinate(
            spec,
            absolute_key="x_start",
            fraction_key="x_start_fraction",
            x0=x0,
            x1=x1,
            index=index,
        )
        segment_end = _segment_coordinate(
            spec,
            absolute_key="x_end",
            fraction_key="x_end_fraction",
            x0=x0,
            x1=x1,
            index=index,
        )

        basis_name = str(spec.pop("basis", "")).strip()
        if not basis_name:
            raise ValueError(f"segment {index} must define a non-empty basis")

        if "order" not in spec:
            raise ValueError(
                f"segment {index} must define its own order; "
                "a segmented model has no global cuf.order"
            )
        child_order = int(spec.pop("order"))
        if child_order < 1:
            raise ValueError(f"segment {index} order must be >= 1")

        child_options = _as_mapping(
            spec.pop("basis_options", {}),
            f"segment {index}.basis_options",
        )
        if spec:
            raise ValueError(
                f"unsupported keys in cuf segment {index}: {sorted(spec)}"
            )

        definition_key = (
            basis_name,
            child_order,
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
            ExpansionSegment(
                x_start=segment_start,
                x_end=segment_end,
                basis_name=basis_name,
                basis=child_basis,
                definition_key=definition_key,
                section_gauss_minimum=(
                    child_plugin.minimum_section_gauss_order(child_basis)
                ),
                longitudinal_transverse_degree=(
                    child_plugin.transverse_x_polynomial_degree(child_basis)
                ),
            )
        )

    segments.sort(key=lambda item: item.x_start)
    tol = 1.0e-12 * max(1.0, abs(x0), abs(x1), abs(x1 - x0))

    if not math.isclose(
        segments[0].x_start,
        x0,
        rel_tol=0.0,
        abs_tol=tol,
    ):
        raise ValueError(
            "cuf.segments must start at the CSF longitudinal domain start"
        )
    if not math.isclose(
        segments[-1].x_end,
        x1,
        rel_tol=0.0,
        abs_tol=tol,
    ):
        raise ValueError(
            "cuf.segments must end at the CSF longitudinal domain end"
        )

    return SegmentedExpansionLaw(segments=segments)

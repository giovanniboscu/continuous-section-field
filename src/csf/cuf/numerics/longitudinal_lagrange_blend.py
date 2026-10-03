# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Numerical basis implementations for longitudinally varying transverse expansions."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from csf.cuf.core.basis import CUFBasis


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

"""Backward-compatible surface-halfwave problem adapter.

The reusable implementations are split into:

- ``loads.surface_halfwave`` for the physical half-wave load;
- ``constraints.full_clamp`` for the end constraints.

This module only composes those two components for legacy
``problem.type: surface_halfwave`` cases.  It contains no duplicated load or
constraint implementation.
"""

from __future__ import annotations

from typing import Any

from csf.cuf.adapters.problem.constraints.full_clamp import FullClampConstraints
from csf.cuf.adapters.problem.loads.surface_halfwave import (
    PROBLEM_TYPE,
    SurfaceHalfWaveLoadProblem as _SurfaceHalfWaveLoadProblem,
    build_load_problem as _build_load_problem,
)


class SurfaceHalfWaveLoadProblem(_SurfaceHalfWaveLoadProblem):
    """composed problem: reusable load plus full-clamp constraints."""

    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
        return FullClampConstraints().build_constraints(
            assembled=assembled,
            mesh=mesh,
            basis=basis,
            longitudinal_integrator=longitudinal_integrator,
        )


def build_problem(problem_type: str, options: dict):
    """Build the legacy composed adapter from the split load/constraint parts."""

    load_problem = _build_load_problem(problem_type, options)
    return SurfaceHalfWaveLoadProblem(
        selector=load_problem.selector,
        amplitude=load_problem.amplitude,
    )


__all__ = (
    "HorizontalRuledSurface",
    "PROBLEM_TYPE",
    "SurfaceSelector",
    "HalfWavePhysicalSurfaceProjector",
    "SurfaceHalfWaveLoadProblem",
    "build_problem",
)

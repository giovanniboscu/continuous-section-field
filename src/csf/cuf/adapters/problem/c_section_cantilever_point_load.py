"""Carrera Table 9.13 problem composition.

This module contains no load mechanics and no constraint mechanics.

It only composes two reusable adapters:

    loads.point_force_global_z
    constraints.full_start_section_clamp
"""

from __future__ import annotations

from typing import Mapping

from csf.cuf.adapters.problem.loads.point_force_global_z import (
    PointForceGlobalZ,
)
from csf.cuf.adapters.problem.constraints.full_start_section_clamp import (
    FullStartSectionClamp,
)


PROBLEM_TYPE = "c_section_table_9_13"


class CarreraTable913Problem:
    """Carrera Table 9.13 benchmark assembled from reusable adapters."""

    def __init__(self, *, load: PointForceGlobalZ) -> None:
        self.load = load
        self.constraint = FullStartSectionClamp()

    def build_load_vector(self, **kwargs):
        """Delegate load-vector construction."""
        return self.load.build_load_vector(**kwargs)

    def build_constraints(self, **kwargs):
        """Delegate constraint construction."""
        return self.constraint.build_constraints(**kwargs)

    def tracked_points(self, section_provider, x: float):
        """Expose the load point to post-processing."""
        return self.load.tracked_points(section_provider, x)


def build_problem(problem_type: str, options: dict):
    """Build the benchmark from the YAML problem definition."""

    if problem_type != PROBLEM_TYPE:
        raise ValueError(
            f"unsupported problem.type: {problem_type!r}; "
            f"expected {PROBLEM_TYPE!r}"
        )

    if not isinstance(options, Mapping):
        raise TypeError("problem must be a YAML mapping")

    force = options.get("force")
    if not isinstance(force, Mapping):
        raise TypeError("problem.force must be a YAML mapping")

    return CarreraTable913Problem(
        load=PointForceGlobalZ.from_mapping(force),
    )


__all__ = (
    "PROBLEM_TYPE",
    "CarreraTable913Problem",
    "build_problem",
)

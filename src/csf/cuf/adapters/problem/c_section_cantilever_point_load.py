"""C-section cantilever: explicit selection of point or area load adapters.

This module composes the same clamp with exactly one load implementation.
The physical loading mode is selected by problem.force.type, not inferred
from the presence/absence of area or amplitude.
"""

from __future__ import annotations

from typing import Mapping

from csf.cuf.adapters.problem.loads.point_force_global_z_point import PointForceGlobalZPoint
from csf.cuf.adapters.problem.loads.point_force_global_z_area import PointForceGlobalZArea
from csf.cuf.adapters.problem.constraints.full_start_section_clamp import FullStartSectionClamp

PROBLEM_TYPE = "c_section_cantilever"
LOAD_TYPES = {"point": PointForceGlobalZPoint, "area": PointForceGlobalZArea}


class CSectionCantileverProblem:
    """One physical cantilever problem with an explicitly chosen load."""

    def __init__(self, *, load):
        self.load = load
        self.constraint = FullStartSectionClamp()

    def build_load_vector(self, **kwargs):
        return self.load.build_load_vector(**kwargs)

    def build_constraints(self, **kwargs):
        return self.constraint.build_constraints(**kwargs)

    def tracked_points(self, section_provider, x: float):
        return self.load.tracked_points(section_provider, x)


def build_problem(problem_type: str, options: Mapping):
    if problem_type != PROBLEM_TYPE:
        raise ValueError(f"unsupported problem.type: {problem_type!r}; expected {PROBLEM_TYPE!r}")
    if not isinstance(options, Mapping):
        raise TypeError("problem must be a YAML mapping")
    force = options.get("force")
    if not isinstance(force, Mapping):
        raise TypeError("problem.force must be a YAML mapping")
    kind = force.get("type")
    if kind not in LOAD_TYPES:
        raise ValueError("problem.force.type must be 'point' or 'area'")
    params = {k: v for k, v in force.items() if k != "type"}
    load = LOAD_TYPES[kind].from_mapping(params)
    return CSectionCantileverProblem(load=load)


__all__ = ("PROBLEM_TYPE", "CSectionCantileverProblem", "build_problem")

# Version: CSF-CUF normalized longitudinal partition v3 - 2026-09-21
"""
Generic longitudinal problem-data layer for the CSF-CUF solver.

Current scope
-------------
1. Essential boundary conditions.
2. Generic longitudinal discretization options.

No geometry, material, beam length, section dimensions, or benchmark-specific
data are stored here. Those remain owned by CSF or by verification cases.

The longitudinal domain is not duplicated. The solver receives it from CSF
and applies the discretization declared here to that domain.

Expected YAML
-------------
problem:
  boundary_conditions:
    - end: start
      tau: 1
      component: y
      value: 0.0

  solver:
    longitudinal_discretization:
      method: finite_element
      elements: 40

Alternative explicit partition:

  solver:
    longitudinal_discretization:
      method: finite_element
      element_boundaries: [0.0, 0.2, 0.5, 1.0]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import math


EndLabel = Literal["start", "end"]
ComponentLabel = Literal["x", "y", "z"]


# =============================================================================
# Boundary conditions
# =============================================================================

@dataclass(frozen=True)
class EssentialBoundaryCondition:
    """Prescribed longitudinal CUF amplitude."""

    end: EndLabel
    tau: int
    component: ComponentLabel
    value: float

    def __post_init__(self) -> None:
        if self.end not in ("start", "end"):
            raise ValueError(
                f"end must be 'start' or 'end', got {self.end!r}"
            )

        if not isinstance(self.tau, int):
            raise TypeError("tau must be an integer")

        if self.tau < 1:
            raise ValueError("tau must be >= 1")

        if self.component not in ("x", "y", "z"):
            raise ValueError(
                "component must be 'x', 'y', or 'z'"
            )

        if not isinstance(self.value, (int, float)):
            raise TypeError("value must be numeric")

        if not math.isfinite(float(self.value)):
            raise ValueError("value must be finite")


# =============================================================================
# Generic longitudinal discretization API
# =============================================================================

@dataclass(frozen=True)
class LongitudinalDiscretization:
    """Generic declaration of the longitudinal discretization topology.

    The approximation family and its order are intentionally not owned by
    this object.  They are supplied through the independent longitudinal-basis
    plugin API.  This keeps ``finite_element`` separate from any concrete
    shape-function implementation.

    Parameters
    ----------
    method:
        Discretization family. Currently only ``finite_element`` is supported.

    elements:
        Number of uniformly distributed longitudinal finite elements.

    element_boundaries:
        Explicit normalized finite-element boundaries in the interval [0, 1].
        The discretizer maps them to the physical CSF longitudinal domain.
        Exactly one between ``elements`` and ``element_boundaries`` is required.
    """

    method: str
    elements: int | None = None
    element_boundaries: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.method != "finite_element":
            raise ValueError(
                "currently supported longitudinal discretization method "
                "is 'finite_element'"
            )

        has_elements = self.elements is not None
        has_boundaries = self.element_boundaries is not None
        if has_elements == has_boundaries:
            raise ValueError(
                "exactly one of elements or element_boundaries is required"
            )

        if has_elements:
            if not isinstance(self.elements, int):
                raise TypeError("elements must be an integer")
            if self.elements < 1:
                raise ValueError("elements must be >= 1")
            return

        boundaries = tuple(float(value) for value in self.element_boundaries)
        if len(boundaries) < 2:
            raise ValueError("element_boundaries must contain at least two points")
        if any(not math.isfinite(value) for value in boundaries):
            raise ValueError("element_boundaries values must be finite")
        if any(
            right <= left
            for left, right in zip(boundaries, boundaries[1:])
        ):
            raise ValueError("element_boundaries must be strictly increasing")
        endpoint_tolerance = 1.0e-12
        if not math.isclose(
            boundaries[0], 0.0, rel_tol=0.0, abs_tol=endpoint_tolerance
        ):
            raise ValueError(
                "element_boundaries are normalized coordinates and must start at 0"
            )
        if not math.isclose(
            boundaries[-1], 1.0, rel_tol=0.0, abs_tol=endpoint_tolerance
        ):
            raise ValueError(
                "element_boundaries are normalized coordinates and must end at 1"
            )
        boundaries = (0.0, *boundaries[1:-1], 1.0)
        object.__setattr__(self, "element_boundaries", boundaries)

    @property
    def number_of_elements(self) -> int:
        if self.elements is not None:
            return int(self.elements)
        if self.element_boundaries is None:
            raise RuntimeError("longitudinal partition is not configured")
        return len(self.element_boundaries) - 1


@dataclass(frozen=True)
class SolverOptions:
    """Generic solver options currently implemented."""

    longitudinal_discretization: LongitudinalDiscretization

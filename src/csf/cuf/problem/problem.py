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
      order: 2
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
    """
    Generic declaration of the longitudinal numerical discretization.

    This object does not contain the longitudinal coordinates themselves.
    Those are obtained from CSF.

    Current concrete method
    -----------------------
    finite_element

    Parameters
    ----------
    method:
        Discretization family. Currently only ``finite_element`` is supported.

    elements:
        Number of longitudinal finite elements.

    order:
        Polynomial interpolation order of each longitudinal element.
    """

    method: str
    elements: int
    order: int

    def __post_init__(self) -> None:
        if self.method != "finite_element":
            raise ValueError(
                "currently supported longitudinal discretization method "
                "is 'finite_element'"
            )

        if not isinstance(self.elements, int):
            raise TypeError("elements must be an integer")

        if self.elements < 1:
            raise ValueError("elements must be >= 1")

        if not isinstance(self.order, int):
            raise TypeError("order must be an integer")

        if self.order < 1:
            raise ValueError("order must be >= 1")


@dataclass(frozen=True)
class SolverOptions:
    """Generic solver options currently implemented."""

    longitudinal_discretization: LongitudinalDiscretization

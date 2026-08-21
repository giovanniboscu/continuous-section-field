"""
Generic longitudinal problem-data layer for the CSF-CUF solver.

Current scope
-------------
1. Essential boundary conditions.
2. Generic generalized longitudinal load fields.
3. Generic longitudinal discretization options.

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

  loads:
    - tau: 1
      component: y
      field:
        type: piecewise_linear
        samples:
          - [0.0, 0.0]
          - [5.0, 1.0]
          - [10.0, 0.0]

  solver:
    longitudinal_discretization:
      method: finite_element
      elements: 40
      order: 2
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Tuple

import math
import yaml


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
# Generic generalized-load API
# =============================================================================

class ScalarLoadField(ABC):
    """Generic scalar longitudinal load field."""

    @abstractmethod
    def value(self, x: float) -> float:
        raise NotImplementedError


@dataclass(frozen=True)
class PiecewiseLinearLoadField(ScalarLoadField):
    """
    Piecewise-linear scalar field defined by ordered (x, value) samples.

    Extrapolation outside the tabulated interval is intentionally forbidden.
    """

    samples: Tuple[Tuple[float, float], ...]

    def __post_init__(self) -> None:
        if len(self.samples) < 2:
            raise ValueError(
                "piecewise-linear load field requires at least two samples"
            )

        previous_x = None

        for index, sample in enumerate(self.samples, start=1):
            if len(sample) != 2:
                raise ValueError(
                    f"sample #{index} must contain exactly [x, value]"
                )

            x = float(sample[0])
            value = float(sample[1])

            if not math.isfinite(x) or not math.isfinite(value):
                raise ValueError(
                    f"sample #{index} must contain finite numbers"
                )

            if previous_x is not None and x <= previous_x:
                raise ValueError(
                    "piecewise-linear sample coordinates must be "
                    "strictly increasing"
                )

            previous_x = x

    @property
    def x_min(self) -> float:
        return float(self.samples[0][0])

    @property
    def x_max(self) -> float:
        return float(self.samples[-1][0])

    def value(self, x: float) -> float:
        x = float(x)

        if not math.isfinite(x):
            raise ValueError("x must be finite")

        if x < self.x_min or x > self.x_max:
            raise ValueError(
                f"x={x} is outside load field interval "
                f"[{self.x_min}, {self.x_max}]"
            )

        if x == self.x_max:
            return float(self.samples[-1][1])

        for left, right in zip(
            self.samples[:-1],
            self.samples[1:],
        ):
            x0, v0 = map(float, left)
            x1, v1 = map(float, right)

            if x0 <= x <= x1:
                ratio = (x - x0) / (x1 - x0)
                return float(v0 + ratio * (v1 - v0))

        raise RuntimeError(
            "piecewise-linear interpolation failed for an in-range coordinate"
        )


@dataclass(frozen=True)
class GeneralizedLongitudinalLoad:
    """One generalized CUF load component."""

    tau: int
    component: ComponentLabel
    field: ScalarLoadField

    def __post_init__(self) -> None:
        if not isinstance(self.tau, int):
            raise TypeError("tau must be an integer")

        if self.tau < 1:
            raise ValueError("tau must be >= 1")

        if self.component not in ("x", "y", "z"):
            raise ValueError(
                "component must be 'x', 'y', or 'z'"
            )

        if not isinstance(self.field, ScalarLoadField):
            raise TypeError(
                "field must implement the ScalarLoadField API"
            )

    def value(self, x: float) -> float:
        return self.field.value(x)


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


# =============================================================================
# Problem data container
# =============================================================================

@dataclass(frozen=True)
class CSFCUFProblemData:
    """Generic longitudinal problem data."""

    boundary_conditions: Tuple[EssentialBoundaryCondition, ...]
    loads: Tuple[GeneralizedLongitudinalLoad, ...]
    solver: SolverOptions | None


# =============================================================================
# YAML reader
# =============================================================================

class CSFCUFProblemReader:
    """
    Read and validate generic CSF-CUF longitudinal problem data.

    CSF-owned data such as geometry, material properties, and longitudinal
    domain are intentionally rejected here.
    """

    def read_file(
        self,
        filepath: str | Path,
    ) -> CSFCUFProblemData:
        path = Path(filepath)

        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)

        return self.read_data(data)

    def read_data(
        self,
        data: Any,
    ) -> CSFCUFProblemData:
        if not isinstance(data, dict):
            raise ValueError("problem YAML root must be a mapping")

        unknown_root = set(data) - {"problem"}
        if unknown_root:
            raise ValueError(
                "unsupported root keys: "
                + ", ".join(sorted(unknown_root))
            )

        if "problem" not in data:
            raise ValueError("missing top-level 'problem' key")

        problem = data["problem"]

        if not isinstance(problem, dict):
            raise ValueError("'problem' must be a mapping")

        allowed_problem_keys = {
            "boundary_conditions",
            "loads",
            "solver",
        }

        unknown_problem = set(problem) - allowed_problem_keys

        if unknown_problem:
            raise ValueError(
                "unsupported problem keys at current API level: "
                + ", ".join(sorted(unknown_problem))
            )

        raw_conditions = problem.get(
            "boundary_conditions",
            [],
        )

        raw_loads = problem.get(
            "loads",
            [],
        )

        if not isinstance(raw_conditions, list):
            raise ValueError(
                "'boundary_conditions' must be a list"
            )

        if not isinstance(raw_loads, list):
            raise ValueError("'loads' must be a list")

        conditions = tuple(
            self._parse_boundary_condition(
                item,
                index=index,
            )
            for index, item in enumerate(
                raw_conditions,
                start=1,
            )
        )

        loads = tuple(
            self._parse_load(
                item,
                index=index,
            )
            for index, item in enumerate(
                raw_loads,
                start=1,
            )
        )

        solver = None
        if "solver" in problem:
            solver = self._parse_solver(problem["solver"])

        return CSFCUFProblemData(
            boundary_conditions=conditions,
            loads=loads,
            solver=solver,
        )

    @staticmethod
    def _parse_boundary_condition(
        item: Any,
        *,
        index: int,
    ) -> EssentialBoundaryCondition:
        if not isinstance(item, dict):
            raise ValueError(
                f"boundary condition #{index} must be a mapping"
            )

        allowed = {
            "end",
            "tau",
            "component",
            "value",
        }

        unknown = set(item) - allowed

        if unknown:
            raise ValueError(
                f"boundary condition #{index} has unsupported keys: "
                + ", ".join(sorted(unknown))
            )

        missing = allowed - set(item)

        if missing:
            raise ValueError(
                f"boundary condition #{index} is missing keys: "
                + ", ".join(sorted(missing))
            )

        return EssentialBoundaryCondition(
            end=item["end"],
            tau=item["tau"],
            component=item["component"],
            value=float(item["value"]),
        )

    @staticmethod
    def _parse_load(
        item: Any,
        *,
        index: int,
    ) -> GeneralizedLongitudinalLoad:
        if not isinstance(item, dict):
            raise ValueError(
                f"load #{index} must be a mapping"
            )

        allowed = {
            "tau",
            "component",
            "field",
        }

        unknown = set(item) - allowed

        if unknown:
            raise ValueError(
                f"load #{index} has unsupported keys: "
                + ", ".join(sorted(unknown))
            )

        missing = allowed - set(item)

        if missing:
            raise ValueError(
                f"load #{index} is missing keys: "
                + ", ".join(sorted(missing))
            )

        field = CSFCUFProblemReader._parse_load_field(
            item["field"],
            load_index=index,
        )

        return GeneralizedLongitudinalLoad(
            tau=item["tau"],
            component=item["component"],
            field=field,
        )

    @staticmethod
    def _parse_load_field(
        data: Any,
        *,
        load_index: int,
    ) -> ScalarLoadField:
        if not isinstance(data, dict):
            raise ValueError(
                f"load #{load_index} field must be a mapping"
            )

        if "type" not in data:
            raise ValueError(
                f"load #{load_index} field is missing 'type'"
            )

        field_type = data["type"]

        if field_type == "piecewise_linear":
            allowed = {
                "type",
                "samples",
            }

            unknown = set(data) - allowed

            if unknown:
                raise ValueError(
                    f"load #{load_index} piecewise-linear field has "
                    "unsupported keys: "
                    + ", ".join(sorted(unknown))
                )

            if "samples" not in data:
                raise ValueError(
                    f"load #{load_index} piecewise-linear field "
                    "is missing 'samples'"
                )

            raw_samples = data["samples"]

            if not isinstance(raw_samples, list):
                raise ValueError(
                    f"load #{load_index} samples must be a list"
                )

            samples = []

            for sample_number, sample in enumerate(
                raw_samples,
                start=1,
            ):
                if (
                    not isinstance(sample, (list, tuple))
                    or len(sample) != 2
                ):
                    raise ValueError(
                        f"load #{load_index} sample #{sample_number} "
                        "must contain exactly [x, value]"
                    )

                samples.append(
                    (
                        float(sample[0]),
                        float(sample[1]),
                    )
                )

            return PiecewiseLinearLoadField(
                samples=tuple(samples),
            )

        raise ValueError(
            f"unsupported load field type {field_type!r}"
        )

    @staticmethod
    def _parse_solver(data: Any) -> SolverOptions:
        if not isinstance(data, dict):
            raise ValueError("'solver' must be a mapping")

        allowed = {
            "longitudinal_discretization",
        }

        unknown = set(data) - allowed

        if unknown:
            raise ValueError(
                "unsupported solver keys: "
                + ", ".join(sorted(unknown))
            )

        if "longitudinal_discretization" not in data:
            raise ValueError(
                "solver is missing 'longitudinal_discretization'"
            )

        discretization_data = data["longitudinal_discretization"]

        if not isinstance(discretization_data, dict):
            raise ValueError(
                "'longitudinal_discretization' must be a mapping"
            )

        allowed_discretization = {
            "method",
            "elements",
            "order",
        }

        unknown_discretization = (
            set(discretization_data) - allowed_discretization
        )

        if unknown_discretization:
            raise ValueError(
                "unsupported longitudinal discretization keys: "
                + ", ".join(sorted(unknown_discretization))
            )

        missing = (
            allowed_discretization - set(discretization_data)
        )

        if missing:
            raise ValueError(
                "longitudinal discretization is missing keys: "
                + ", ".join(sorted(missing))
            )

        discretization = LongitudinalDiscretization(
            method=discretization_data["method"],
            elements=discretization_data["elements"],
            order=discretization_data["order"],
        )

        return SolverOptions(
            longitudinal_discretization=discretization,
        )

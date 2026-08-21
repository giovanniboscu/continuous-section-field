"""
Generic problem interface for the CSF-CUF solver.

A problem definition supplies the solver with:

1. generalized loads;
2. linear constraints.

The interface is independent of geometry, material, benchmark, and
transverse CUF basis family. Concrete applications, such as the
Carrera-Giunta validation problems, implement this contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml


class CUFProblem(Protocol):
    """Problem contract required by the general CSF-CUF solver."""

    def build_loads(
        self,
        *,
        section_provider: Any,
        basis: Any,
        x0: float,
        x1: float,
    ) -> tuple[Any, Any]:
        """Build generalized loads for the longitudinal assembly."""
        ...

    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ) -> Any:
        """Build the linear constraint system for the assembled problem."""
        ...


@dataclass(frozen=True)
class ProblemDefinition:
    """Physical problem definition loaded from a problem YAML."""

    path: Path
    model_path: Path
    problem_type: str
    problem_options: dict[str, Any]



def load_problem(path: str | Path) -> ProblemDefinition:
    """Load one solver-independent physical problem definition."""

    path = Path(path).resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise TypeError("problem file must contain a YAML mapping")

    model = raw.get("model")
    if not isinstance(model, dict):
        raise TypeError("problem.model must be a YAML mapping")

    problem = raw.get("problem")
    if not isinstance(problem, dict):
        raise TypeError("problem.problem must be a YAML mapping")

    if "csf_yaml" not in model:
        raise ValueError("problem.model.csf_yaml is required")

    if "type" not in problem:
        raise ValueError("problem.problem.type is required")

    model_path = Path(str(model["csf_yaml"]))
    if not model_path.is_absolute():
        model_path = (path.parent / model_path).resolve()

    return ProblemDefinition(
        path=path,
        model_path=model_path,
        problem_type=str(problem["type"]),
        problem_options={
            key: value
            for key, value in problem.items()
            if key != "type"
        },
    )


def load_problem_adapter(path: str | Path):
    """Load a problem adapter module from an explicit filesystem path."""

    import importlib.util

    path = Path(path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"problem adapter not found: {path}")

    module_name = f"_csf_cuf_problem_adapter_{path.stem}"

    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load problem adapter: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    build_problem = getattr(module, "build_problem", None)

    if not callable(build_problem):
        raise TypeError(
            f"problem adapter {path} must define callable build_problem()"
        )

    return module

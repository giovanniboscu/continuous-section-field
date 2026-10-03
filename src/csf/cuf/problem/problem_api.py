"""
Generic problem interface for the CSF-CUF solver.

A problem definition supplies the solver with:

1. its contribution to the global load vector;
2. linear constraints.

Historically both responsibilities are supplied by one adapter object.  The
loader also supports composing independent load and constraint adapter objects
without changing the solver-facing problem contract.

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

    def build_load_vector(
        self,
        *,
        section_provider: Any,
        basis: Any,
        mesh: Any,
        dof_layout: Any,
        longitudinal_integrator: Any,
        x0: float,
        x1: float,
    ) -> tuple[Any, Any]:
        """Build this problem's contribution to the global load vector."""
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


class CUFLoadProblem(Protocol):
    """Load-side contract for a split problem adapter."""

    def build_load_vector(
        self,
        *,
        section_provider: Any,
        basis: Any,
        mesh: Any,
        dof_layout: Any,
        longitudinal_integrator: Any,
        x0: float,
        x1: float,
    ) -> tuple[Any, Any]:
        ...


class CUFConstraintProblem(Protocol):
    """Constraint-side contract for a split problem adapter."""

    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ) -> Any:
        ...


@dataclass(frozen=True)
class CompositeCUFProblem:
    """Compose independent load and constraint problem components.

    The solver still sees the historical single ``problem`` object.  Only the
    adapter-loading layer knows that its load and constraint responsibilities
    may come from different modules.  ``tracked_points`` belongs to the load
    side and is therefore delegated there as well.
    """

    load_problem: Any
    constraint_problem: Any

    def build_load_vector(self, **kwargs):
        return self.load_problem.build_load_vector(**kwargs)

    def build_constraints(self, **kwargs):
        return self.constraint_problem.build_constraints(**kwargs)

    def tracked_points(self, section_provider: Any, x: float):
        tracked_points = getattr(self.load_problem, "tracked_points", None)
        if not callable(tracked_points):
            return ()
        return tracked_points(section_provider, x)


def compose_problem(load_problem: Any, constraint_problem: Any) -> CompositeCUFProblem:
    """Validate and compose independently built problem components."""

    if not callable(getattr(load_problem, "build_load_vector", None)):
        raise TypeError(
            "load adapter build_problem() result must define callable "
            "build_load_vector()"
        )
    if not callable(getattr(constraint_problem, "build_constraints", None)):
        raise TypeError(
            "constraint adapter build_problem() result must define callable "
            "build_constraints()"
        )

    return CompositeCUFProblem(
        load_problem=load_problem,
        constraint_problem=constraint_problem,
    )


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


def _adapter_is_path(reference: str | Path) -> bool:
    if isinstance(reference, Path):
        return True

    text = str(reference)
    path = Path(text)
    return (
        path.is_absolute()
        or path.suffix == ".py"
        or "/" in text
        or "\\" in text
    )


def load_problem_adapter(reference: str | Path):
    """
    Load a problem adapter from a filesystem path or importable module name.

    Examples:
        ../adapters/carrera_problem.py
        csf.cuf.adapter.surface_load_problem
    """

    import importlib
    import importlib.util

    if _adapter_is_path(reference):
        path = Path(reference).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"problem adapter not found: {path}")

        module_name = f"_csf_cuf_problem_adapter_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)

        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load problem adapter: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = str(path)
    else:
        module_name = str(reference).strip()
        if not module_name:
            raise ValueError("problem adapter module name must not be empty")
        module = importlib.import_module(module_name)
        source = module_name

    build_problem = getattr(module, "build_problem", None)

    if not callable(build_problem):
        raise TypeError(
            f"problem adapter {source} must define callable build_problem()"
        )

    return module

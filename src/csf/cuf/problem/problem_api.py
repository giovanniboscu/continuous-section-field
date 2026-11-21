# Version: CSF-CUF local composite context v02 - 2026-11-20
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
        # Optional geometry handoff for independent constraint components.
        # The solver calls build_load_vector before build_constraints. The
        # constraint receives geometry from the *compositor*, NOT from the
        # load component, so neither component depends on the other.
        # Older constraint adapters do not implement this hook and therefore
        # retain exactly their original execution path.
        bind_geometry = getattr(self.constraint_problem, "bind_section_context", None)
        if callable(bind_geometry):
            bind_geometry(
                section_provider=kwargs["section_provider"],
                x0=kwargs["x0"],
                x1=kwargs["x1"],
            )
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


def build_local_composite_problem(definition: ProblemDefinition) -> CompositeCUFProblem:
    """Build exactly one local load and one local constraint from problem YAML.

    A component declares ``adapter`` (a .py file or importable module name)
    and component-specific options, but no ``type``. Relative .py paths are
    resolved against the *problem YAML* directory, not the case directory.

    No automatic library registry, list composition, or solver changes are
    introduced by this first version. External factories keep the existing
    signature ``build_problem(problem_type, options)``; the problem type is
    the declared ``composite`` and options are local to that component.
    """

    if definition.problem_type != "composite":
        raise ValueError(
            "declarative problem without a case adapter requires "
            "problem.type: composite"
        )

    # In the new declaration, silently overwriting two 'load' YAML keys
    # would conceal a second component. PyYAML safe_load permits duplicate
    # mapping keys, so reject them explicitly for composite problems only.
    def reject_duplicate_keys(node, location: str):
        if isinstance(node, yaml.MappingNode):
            seen = set()
            for key_node, value_node in node.value:
                if not isinstance(key_node, yaml.ScalarNode):
                    continue
                key = key_node.value
                if key in seen:
                    raise ValueError(
                        f"duplicate YAML key {location}.{key} in composite "
                        "problem; duplicate entries cannot represent "
                        "multiple components"
                    )
                seen.add(key)
                reject_duplicate_keys(value_node, f"{location}.{key}")
        elif isinstance(node, yaml.SequenceNode):
            for index, item in enumerate(node.value):
                reject_duplicate_keys(item, f"{location}[{index}]")

    root_node = yaml.compose(definition.path.read_text(encoding="utf-8"))
    reject_duplicate_keys(root_node, "problem_yaml")

    options = definition.problem_options
    if "loads" in options or "constraints" in options:
        raise ValueError(
            "problem.type=composite currently supports exactly one 'load' "
            "and one 'constraint'; 'loads' and 'constraints' lists are not "
            "supported (use a custom unified problem adapter for multiple loads)"
        )
    extra = sorted(str(key) for key in options if key not in ("load", "constraint"))
    if extra:
        raise ValueError(
            "problem.type=composite contains unsupported field(s): "
            + ", ".join(extra)
        )

    def build_component(role: str):
        entry = options.get(role)
        if not isinstance(entry, dict):
            raise TypeError(
                f"problem.{role} must be a YAML mapping with one 'adapter' "
                "(one component only; lists are not supported)"
            )
        if "type" in entry:
            raise ValueError(
                f"problem.{role}.type is not supported in local composite v01; "
                f"specify problem.{role}.adapter instead"
            )

        reference = entry.get("adapter")
        if not isinstance(reference, str) or not reference.strip():
            raise ValueError(
                f"problem.{role}.adapter must be a nonempty Python file "
                "path or module name (automatic type lookup is not yet enabled)"
            )
        reference = reference.strip()
        if _adapter_is_path(reference):
            path = Path(reference)
            if not path.is_absolute():
                path = (definition.path.parent / path).resolve()
            reference = path
        module = load_problem_adapter(reference)
        local_options = {key: value for key, value in entry.items() if key != "adapter"}
        return module.build_problem("composite", local_options)

    return compose_problem(
        build_component("load"),
        build_component("constraint"),
    )

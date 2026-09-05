#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import importlib.util
from pathlib import Path

from csf.cuf.case import load_case
from csf.cuf.csf_bridge import CSFCUFModelBridge
from csf.cuf.problem.problem_api import (
    load_problem,
    load_problem_adapter,
)
from csf.cuf.solver.engine import solve_case


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


def _load_output_adapter(reference: str | Path):
    """Load an output adapter from a filesystem path or module name."""

    if _adapter_is_path(reference):
        path = Path(reference).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"output adapter not found: {path}")

        module_name = f"_csf_cuf_output_adapter_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)

        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load output adapter: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = str(path)
    else:
        module_name = str(reference).strip()
        if not module_name:
            raise ValueError("output adapter module name must not be empty")
        module = importlib.import_module(module_name)
        source = module_name

    write_outputs = getattr(module, "write_outputs", None)

    if not callable(write_outputs):
        raise TypeError(
            f"output adapter {source} must define callable write_outputs()"
        )

    return module


def run(case_path, *, progress=True):
    case = load_case(case_path)

    problem_definition = load_problem(case.problem_path)

    problem_adapter = load_problem_adapter(
        case.problem_adapter_path
    )

    output_adapter = _load_output_adapter(
        case.output_adapter_path
    )

    model = CSFCUFModelBridge.from_yaml(
        problem_definition.model_path
    )

    problem = problem_adapter.build_problem(
        problem_definition.problem_type,
        problem_definition.problem_options,
    )

    print("CSF-CUF solver")
    print("==============")
    print(f"case                = {case.name}")
    print(f"problem             = {case.problem_path}")
    print(f"CSF model           = {problem_definition.model_path}")
    print("solver public output= u(x,y,z)")
    print(f"CUF order           = {case.cuf.order}")
    print(
        f"longitudinal FE     = "
        f"{case.longitudinal.elements} x order "
        f"{case.longitudinal.order}"
    )
    print()

    u = solve_case(
        case,
        model,
        problem,
        progress=progress,
    )

    paths = output_adapter.write_outputs(
        u,
        model,
        case,
        problem_definition,
    )

    print()
    print("continuous displacement field = READY")
    print(f"output directory              = {case.output_dir}")

    for path in paths:
        print(f"  {path.name}")

    return u


def main():
    parser = argparse.ArgumentParser(
        description="Run a CSF-CUF analysis case."
    )
    parser.add_argument(
        "case_yaml",
        help="CUF analysis case YAML",
    )

    args = parser.parse_args()

    run(args.case_yaml)


if __name__ == "__main__":
    main()

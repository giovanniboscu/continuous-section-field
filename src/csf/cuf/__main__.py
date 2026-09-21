# Version: CSF-CUF normalized longitudinal partition v3 - 2026-09-21
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
from pathlib import Path

from csf.cuf.case import load_case
from csf.cuf.csf_bridge import CSFCUFModelBridge
from csf.cuf.problem.problem_api import (
    load_problem,
    load_problem_adapter,
)
from csf.cuf.solver.engine import solve_case, solve_case_runs


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


def _write_outputs(
    output_adapter,
    u,
    model,
    case,
    problem_definition,
    *,
    equilibration_iterations=None,
):
    """Call one post adapter, passing equilibration metadata only if asked.

    Output adapters remain responsible for their filenames and formats. An
    adapter opts into the per-run equilibration value by declaring an
    ``equilibration_iterations`` parameter (or ``**kwargs``) in
    ``write_outputs``.
    """

    write_outputs = output_adapter.write_outputs
    kwargs = {}

    if equilibration_iterations is not None:
        signature = inspect.signature(write_outputs)
        parameter = signature.parameters.get(
            "equilibration_iterations"
        )
        accepts_kwargs = any(
            item.kind == inspect.Parameter.VAR_KEYWORD
            for item in signature.parameters.values()
        )

        if parameter is not None:
            if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                raise TypeError(
                    "output adapter write_outputs() declares "
                    "equilibration_iterations as positional-only; it must "
                    "be keyword-capable"
                )
            kwargs["equilibration_iterations"] = int(
                equilibration_iterations
            )
        elif accepts_kwargs:
            kwargs["equilibration_iterations"] = int(
                equilibration_iterations
            )

    return write_outputs(
        u,
        model,
        case,
        problem_definition,
        **kwargs,
    )


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
    if case.cuf.is_segmented:
        segment_summary = " | ".join(
            f"{segment['basis']} N{int(segment['order'])}"
            for segment in case.cuf.segments
        )
        print(f"CUF expansion       = segmented: {segment_summary}")
    else:
        print(f"CUF order           = {case.cuf.order}")
    if case.longitudinal.elements is not None:
        print(
            f"longitudinal FE     = "
            f"{case.longitudinal.elements} uniform elements x order "
            f"{case.longitudinal.order}"
        )
    else:
        print(
            f"longitudinal FE     = "
            f"{case.longitudinal.number_of_elements} explicit elements x order "
            f"{case.longitudinal.order}"
        )
        print(
            "element boundaries  = "
            + ", ".join(
                f"{value:.16g}"
                for value in case.longitudinal.element_boundaries
            )
            + " (normalized)"
        )
    print(f"longitudinal basis  = {case.longitudinal.basis}")
    print()

    equilibration = case.solver.equilibration

    if not equilibration.is_sweep:
        u = solve_case(
            case,
            model,
            problem,
            progress=progress,
        )

        paths = _write_outputs(
            output_adapter,
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

    requested = equilibration.iteration_values
    print(
        "equilibration sweep = "
        + ", ".join(str(value) for value in requested)
    )
    print()

    output_paths = []
    successful_iterations = []

    for solved_run in solve_case_runs(
        case,
        model,
        problem,
        progress=progress,
    ):
        current_iterations = solved_run.equilibration_iterations
        paths = _write_outputs(
            output_adapter,
            solved_run.solution,
            model,
            case,
            problem_definition,
            equilibration_iterations=current_iterations,
        )
        output_paths.extend(paths)
        successful_iterations.append(current_iterations)

        # Do not retain the previous physical field while the next potentially
        # large KKT factorization is being computed.
        del solved_run

    print()
    print(
        "continuous displacement fields = READY "
        f"({len(successful_iterations)}/{len(requested)})"
    )
    print(
        "successful equilibration       = "
        + ", ".join(str(value) for value in successful_iterations)
    )
    print(f"output directory              = {case.output_dir}")

    for path in output_paths:
        print(f"  {path.name}")

    # Sweep fields are deliberately streamed through the post adapter rather
    # than retained together in memory. Programmatic callers that need each
    # field can iterate solve_case_runs() directly.
    return tuple(successful_iterations)


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

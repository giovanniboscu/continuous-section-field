# Version: CSF-CUF direct segmented case syntax v22 - 2026-09-15
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


AdapterReference = Path | str


@dataclass(frozen=True)
class CUFSettings:
    # Standard/smooth CUF expansion path.  Both are None when the case uses
    # the direct piecewise law declared by ``segments``.
    basis: str | None
    order: int | None
    basis_options: dict[str, Any]
    segments: tuple[dict[str, Any], ...] = ()

    @property
    def is_segmented(self) -> bool:
        return bool(self.segments)


@dataclass(frozen=True)
class LongitudinalSettings:
    method: str
    elements: int
    order: int
    gauss_order: int
    material_polynomial_degree: int | None


@dataclass(frozen=True)
class SectionIntegrationSettings:
    method: str
    gauss_order: int


@dataclass(frozen=True)
class EquilibrationSettings:
    # Scalar keeps the historical single-solve mode. A tuple marks an
    # equilibration sweep requested by a YAML sequence.
    iterations: int | tuple[int, ...]

    def __post_init__(self) -> None:
        # Keep the invariant even for programmatic construction, not only for
        # values coming through load_case().
        object.__setattr__(
            self,
            "iterations",
            _equilibration_iterations(self.iterations),
        )

    @property
    def is_sweep(self) -> bool:
        return isinstance(self.iterations, tuple)

    @property
    def iteration_values(self) -> tuple[int, ...]:
        if isinstance(self.iterations, tuple):
            return self.iterations
        return (self.iterations,)


@dataclass(frozen=True)
class SolverSettings:
    equilibration: EquilibrationSettings


@dataclass(frozen=True)
class SamplingSettings:
    stations: tuple[float, ...]
    displacement_samples: int
    stress_grid: int


@dataclass(frozen=True)
class CaseDefinition:
    path: Path
    name: str
    problem_path: Path
    problem_adapter_path: AdapterReference
    output_adapter_path: AdapterReference
    cuf: CUFSettings
    longitudinal: LongitudinalSettings
    section_integration: SectionIntegrationSettings
    solver: SolverSettings
    sampling: SamplingSettings
    output_dir: Path


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a YAML mapping")
    return value


def _relative(base: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return (base / path).resolve()


def _equilibration_iterations(value: Any) -> int | tuple[int, ...]:
    """Normalize one scalar or YAML sequence of equilibration iterations.

    A sequence is a sweep request. Sweep values are de-duplicated and sorted
    increasingly so progressive equilibration can be reused between requested
    checkpoints. Zero is valid and means solve the original KKT system without
    equilibration. The scalar form intentionally preserves the historical mode.
    """

    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError(
                "solver.equilibration.iterations sequence must not be empty"
            )
        parsed = tuple(int(item) for item in value)
        if any(item < 0 for item in parsed):
            raise ValueError(
                "solver.equilibration.iterations values must be >= 0"
            )
        return tuple(sorted(set(parsed)))

    parsed = int(value)
    if parsed < 0:
        raise ValueError(
            "solver.equilibration.iterations must be >= 0"
        )
    return parsed


def _adapter_reference(base: Path, value: Any) -> AdapterReference:
    """
    Resolve one adapter reference without changing the YAML key.

    Filesystem adapters keep the existing path-based behavior. Importable
    package adapters remain dotted module names, for example:

        csf.cuf.adapter.surface_load_problem
    """

    text = str(value).strip()
    if not text:
        raise ValueError("adapter reference must not be empty")

    candidate = Path(text)
    path_like = (
        candidate.is_absolute()
        or candidate.suffix == ".py"
        or "/" in text
        or "\\" in text
    )

    if path_like:
        return _relative(base, text)

    return text


def load_case(path: str | Path) -> CaseDefinition:
    path = Path(path).resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _mapping(raw, "case file")

    case = _mapping(root.get("case", {}), "case")
    problem = _mapping(root.get("problem"), "problem")
    cuf = _mapping(root.get("cuf"), "cuf")
    longitudinal = _mapping(root.get("longitudinal"), "longitudinal")
    
    section = _mapping(root.get("section_integration", {}), "section_integration")
    solver = _mapping(root.get("solver", {}), "solver")
    equilibration = _mapping(
        solver.get("equilibration", {}),
        "solver.equilibration",
    )
    sampling = _mapping(root.get("sampling", {}), "sampling")
    output = _mapping(root.get("output"), "output")

    stations = tuple(float(v) for v in sampling.get("stations", [0.0, 0.5]))
    if not stations or any(v < 0.0 or v > 1.0 for v in stations):
        raise ValueError("sampling.stations must contain values in [0,1]")

    raw_segments = cuf.get("segments")
    if raw_segments is not None:
        if any(key in cuf for key in ("basis", "order", "basis_options")):
            raise ValueError(
                "cuf.segments is a direct longitudinal expansion law and cannot "
                "be combined with top-level cuf.basis, cuf.order, or "
                "cuf.basis_options"
            )
        if not isinstance(raw_segments, list) or not raw_segments:
            raise TypeError("cuf.segments must be a non-empty YAML sequence")

        segment_specs = []
        segment_orders = []
        for index, raw_segment in enumerate(raw_segments, start=1):
            segment = _mapping(
                raw_segment,
                f"cuf.segments[{index - 1}]",
            ).copy()
            basis_name = str(segment.get("basis", "")).strip()
            if not basis_name:
                raise ValueError(
                    f"cuf.segments[{index - 1}].basis must be non-empty"
                )
            if "order" not in segment:
                raise ValueError(
                    f"cuf.segments[{index - 1}].order is required; "
                    "a segmented model has no global cuf.order"
                )
            segment_order = int(segment["order"])
            if segment_order < 1:
                raise ValueError(
                    f"cuf.segments[{index - 1}].order must be >= 1"
                )
            segment["order"] = segment_order
            if "basis_options" in segment:
                segment["basis_options"] = _mapping(
                    segment["basis_options"],
                    f"cuf.segments[{index - 1}].basis_options",
                ).copy()
            segment_specs.append(segment)
            segment_orders.append(segment_order)

        cuf_basis = None
        cuf_order = None
        basis_options = {}
        cuf_default_order = max(segment_orders)
        cuf_segments = tuple(segment_specs)
    else:
        cuf_basis = str(cuf.get("basis", "scaled_maclaurin"))
        cuf_order = int(cuf.get("order", 5))
        if cuf_order < 1:
            raise ValueError("cuf.order must be >= 1")
        basis_options = _mapping(
            cuf.get("basis_options", {}),
            "cuf.basis_options",
        ).copy()
        cuf_default_order = cuf_order
        cuf_segments = ()

    longitudinal_order = int(longitudinal.get("order", 3))
    elements = int(longitudinal.get("elements", 4))
    section_order = int(section.get("gauss_order", cuf_default_order + 1))
    longitudinal_gauss = int(
        longitudinal.get(
            "gauss_order",
            cuf_default_order + longitudinal_order + 1,
        )
    )
    material_polynomial_degree_raw = longitudinal.get(
        "material_polynomial_degree"
    )
    material_polynomial_degree = (
        None
        if material_polynomial_degree_raw is None
        else int(material_polynomial_degree_raw)
    )
    equilibration_iterations = _equilibration_iterations(
        equilibration.get("iterations", 8)
    )

    if elements < 1:
        raise ValueError("longitudinal.elements must be >= 1")
    if longitudinal_order < 1:
        raise ValueError("longitudinal.order must be >= 1")
    if section_order < 2:
        raise ValueError("section_integration.gauss_order must be >= 2")
    if longitudinal_gauss < 1:
        raise ValueError("longitudinal.gauss_order must be >= 1")
    if (
        material_polynomial_degree is not None
        and material_polynomial_degree < 0
    ):
        raise ValueError(
            "longitudinal.material_polynomial_degree must be >= 0"
        )
    return CaseDefinition(
        path=path,
        name=str(case.get("name", path.stem)),
        problem_path=_relative(path.parent, problem["yaml"]),
        problem_adapter_path=_adapter_reference(
            path.parent,
            problem["adapter"],
        ),
        output_adapter_path=_adapter_reference(
            path.parent,
            output["adapter"],
        ),
        cuf=CUFSettings(
            basis=cuf_basis,
            order=cuf_order,
            basis_options=basis_options,
            segments=cuf_segments,
        ),
        longitudinal=LongitudinalSettings(
            method=str(longitudinal.get("method", "finite_element")),
            elements=elements,
            order=longitudinal_order,
            gauss_order=longitudinal_gauss,
            material_polynomial_degree=material_polynomial_degree,
        ),
        section_integration=SectionIntegrationSettings(
            method=str(section.get("method", "fixed_gauss_polygon")),
            gauss_order=section_order,
        ),
        solver=SolverSettings(
            equilibration=EquilibrationSettings(
                iterations=equilibration_iterations,
            ),
        ),
        sampling=SamplingSettings(
            stations=stations,
            displacement_samples=int(sampling.get("displacement_samples", 201)),
            stress_grid=int(sampling.get("stress_grid", 41)),
        ),
        output_dir=_relative(path.parent, output["directory"]),
    )

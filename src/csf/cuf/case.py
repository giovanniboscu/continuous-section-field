from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CUFSettings:
    basis: str
    order: int


@dataclass(frozen=True)
class LongitudinalSettings:
    method: str
    elements: int
    order: int
    gauss_order: int


@dataclass(frozen=True)
class SectionIntegrationSettings:
    method: str
    gauss_order: int


@dataclass(frozen=True)
class SamplingSettings:
    stations: tuple[float, ...]
    displacement_samples: int
    stress_grid: int


@dataclass(frozen=True)
class CaseDefinition:
    path: Path
    name: str
    model_path: Path
    problem_type: str
    problem_options: dict[str, Any]
    cuf: CUFSettings
    longitudinal: LongitudinalSettings
    section_integration: SectionIntegrationSettings
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


def load_case(path: str | Path) -> CaseDefinition:
    path = Path(path).resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _mapping(raw, "case file")

    case = _mapping(root.get("case", {}), "case")
    model = _mapping(root.get("model"), "model")
    problem = _mapping(root.get("problem"), "problem")
    cuf = _mapping(root.get("cuf"), "cuf")
    longitudinal = _mapping(root.get("longitudinal"), "longitudinal")
    section = _mapping(root.get("section_integration"), "section_integration")
    sampling = _mapping(root.get("sampling", {}), "sampling")
    output = _mapping(root.get("output"), "output")

    stations = tuple(float(v) for v in sampling.get("stations", [0.0, 0.5]))
    if not stations or any(v < 0.0 or v > 1.0 for v in stations):
        raise ValueError("sampling.stations must contain values in [0,1]")

    cuf_order = int(cuf.get("order", 5))
    longitudinal_order = int(longitudinal.get("order", 3))
    elements = int(longitudinal.get("elements", 4))
    section_order = int(section.get("gauss_order", cuf_order + 1))
    longitudinal_gauss = int(
        longitudinal.get("gauss_order", cuf_order + longitudinal_order + 1)
    )

    if cuf_order < 1:
        raise ValueError("cuf.order must be >= 1")
    if elements < 1:
        raise ValueError("longitudinal.elements must be >= 1")
    if longitudinal_order < 1:
        raise ValueError("longitudinal.order must be >= 1")
    if section_order < 2:
        raise ValueError("section_integration.gauss_order must be >= 2")
    if longitudinal_gauss < 1:
        raise ValueError("longitudinal.gauss_order must be >= 1")

    return CaseDefinition(
        path=path,
        name=str(case.get("name", path.stem)),
        model_path=_relative(path.parent, model["csf_yaml"]),
        problem_type=str(problem["type"]),
        problem_options={k: v for k, v in problem.items() if k != "type"},
        cuf=CUFSettings(
            basis=str(cuf.get("basis", "scaled_maclaurin")),
            order=cuf_order,
        ),
        longitudinal=LongitudinalSettings(
            method=str(longitudinal.get("method", "finite_element")),
            elements=elements,
            order=longitudinal_order,
            gauss_order=longitudinal_gauss,
        ),
        section_integration=SectionIntegrationSettings(
            method=str(section.get("method", "fixed_gauss_polygon")),
            gauss_order=section_order,
        ),
        sampling=SamplingSettings(
            stations=stations,
            displacement_samples=int(sampling.get("displacement_samples", 201)),
            stress_grid=int(sampling.get("stress_grid", 41)),
        ),
        output_dir=_relative(path.parent, output["directory"]),
    )

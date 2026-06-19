"""
Compare CSF-OpenSees results against the analytical reference.

Writes per-scenario and global CSV/Markdown reports.
The Markdown report is structured to highlight the two conceptual cases:

1. baseline NREL case: smooth reference validation
2. degraded NREL case: convergence sensitivity under localized stiffness variation
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Tuple


@dataclass(frozen=True)
class ScenarioFiles:
    scenario_name: str
    opensees_dir: Path
    reference_dir: Path


DEFAULT_SCENARIOS: Tuple[ScenarioFiles, ...] = (
    ScenarioFiles(
        scenario_name="NREL-5-MW",
        opensees_dir=Path("openseeslab_output_NREL-5-MW"),
        reference_dir=Path("baseline_output_nrel_constant"),
    ),
    ScenarioFiles(
        scenario_name="NREL-5-MW-degr",
        opensees_dir=Path("openseeslab_output_NREL-5-MW-degr"),
        reference_dir=Path("baseline_output_nrel_degraded"),
    ),
)


@dataclass
class TipRow:
    scenario: str
    model_id: str
    model_label: str
    n_elems: int
    n_section_calls: int
    uy_opensees: float
    rz_opensees: float
    uy_reference: float
    rz_reference: float

    @property
    def uy_abs_error(self) -> float:
        return self.uy_opensees - self.uy_reference

    @property
    def rz_abs_error(self) -> float:
        return self.rz_opensees - self.rz_reference

    @property
    def uy_rel_error(self) -> float:
        return 100.0 * self.uy_abs_error / self.uy_reference

    @property
    def rz_rel_error(self) -> float:
        return 100.0 * self.rz_abs_error / self.rz_reference

    @property
    def compact_model_label(self) -> str:
        match = re.search(r"uniform\s+(\d+)", self.model_label, re.IGNORECASE)
        if match:
            return f"Uniform-{match.group(1)}"
        return self.model_label


def read_reference(reference_file: Path) -> tuple[float, float]:
    text = reference_file.read_text(encoding="utf-8")

    uy_match = re.search(r"Uy_reference\s*:\s*([-+0-9.eE]+)", text)
    rz_match = re.search(r"Rz_reference\s*:\s*([-+0-9.eE]+)", text)

    if uy_match is None:
        raise RuntimeError(f"Unable to find Uy_reference in {reference_file}")

    if rz_match is None:
        raise RuntimeError(f"Unable to find Rz_reference in {reference_file}")

    return float(uy_match.group(1)), float(rz_match.group(1))


def read_tip_response(
    scenario_name: str,
    tip_csv: Path,
    uy_reference: float,
    rz_reference: float,
) -> List[TipRow]:
    rows: List[TipRow] = []

    with open(tip_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {
            "model_id",
            "model_label",
            "n_elems",
            "n_section_calls",
            "Uy_tip",
            "Rz_tip",
        }

        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"Missing columns in {tip_csv}: {sorted(missing)}")

        for row in reader:
            rows.append(
                TipRow(
                    scenario=scenario_name,
                    model_id=row["model_id"],
                    model_label=row["model_label"],
                    n_elems=int(row["n_elems"]),
                    n_section_calls=int(row["n_section_calls"]),
                    uy_opensees=float(row["Uy_tip"]),
                    rz_opensees=float(row["Rz_tip"]),
                    uy_reference=uy_reference,
                    rz_reference=rz_reference,
                )
            )

    return rows


def write_csv(rows: Iterable[TipRow], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "scenario",
            "model_id",
            "model_label",
            "n_elems",
            "n_section_calls",
            "Uy_OpenSees",
            "Uy_reference",
            "Uy_abs_error",
            "Uy_rel_error",
            "Rz_OpenSees",
            "Rz_reference",
            "Rz_abs_error",
            "Rz_rel_error (%)",
        ])

        for r in rows:
            writer.writerow([
                r.scenario,
                r.model_id,
                r.model_label,
                r.n_elems,
                r.n_section_calls,
                f"{r.uy_opensees:.12e}",
                f"{r.uy_reference:.12e}",
                f"{r.uy_abs_error:.12e}",
                f"{r.uy_rel_error:.12e}",
                f"{r.rz_opensees:.12e}",
                f"{r.rz_reference:.12e}",
                f"{r.rz_abs_error:.12e}",
                f"{r.rz_rel_error:.12e}",
            ])


def group_by_scenario(rows: Iterable[TipRow]) -> Dict[str, List[TipRow]]:
    grouped: Dict[str, List[TipRow]] = {}

    for row in rows:
        grouped.setdefault(row.scenario, []).append(row)

    for scenario_rows in grouped.values():
        scenario_rows.sort(key=lambda r: r.n_elems)

    return grouped


def scenario_title(scenario: str) -> str:
    if scenario == "NREL-5-MW":
        return "Case A - undegraded NREL tower"
    if scenario == "NREL-5-MW-degr":
        return "Case B - degraded NREL tower"
    return scenario


def scenario_interpretation(scenario: str) -> str:
    if scenario == "NREL-5-MW":
        return (
            "This case validates the CSF-OpenSees coupling on a smooth, "
            "undegraded reference configuration. The response converges rapidly, "
            "and coarse meshes already give small errors for this configuration."
        )

    if scenario == "NREL-5-MW-degr":
        return (
            "This case introduces localized stiffness degradation. The low-order "
            "piecewise discretizations show a less regular convergence pattern, "
            "highlighting the need for finer sectional sampling when the stiffness "
            "field varies sharply along the tower."
        )

    return (
        "This case compares the CSF-OpenSees response against the analytical "
        "reference for the selected configuration."
    )


def write_markdown_table(lines: List[str], rows: List[TipRow]) -> None:
    lines.append(
        "| Model | Elements | Section evaluations | "
        "Uy OpenSees | Uy reference | Uy rel. error [%] | "
        "Rz OpenSees | Rz reference | Rz rel. error [%] |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for r in rows:
        lines.append(
            "| "
            f"{r.compact_model_label} | "
            f"{r.n_elems} | "
            f"{r.n_section_calls} | "
            f"{r.uy_opensees:.6e} | "
            f"{r.uy_reference:.6e} | "
            f"{r.uy_rel_error:.6e} | "
            f"{r.rz_opensees:.6e} | "
            f"{r.rz_reference:.6e} | "
            f"{r.rz_rel_error:.6e} |"
        )


def write_markdown(
    rows: List[TipRow],
    output_file: Path,
    title: str,
    input_dirs: Dict[str, Tuple[Path, Path]],
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    grouped = group_by_scenario(rows)

    lines: List[str] = []

    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        "This report compares the CSF-OpenSees tip response against an "
        "independent analytical reference."
    )
    lines.append("")
    lines.append("## Conceptual structure")
    lines.append("")
    lines.append(
        "Two configurations are compared. The undegraded NREL tower is used as "
        "the baseline validation case. The degraded tower is used as the "
        "critical convergence case, because localized stiffness variation makes "
        "coarse piecewise discretizations less reliable."
    )
    lines.append("")
    lines.append("## Key quantities")
    lines.append("")
    lines.append("- `Uy`: transverse tip displacement.")
    lines.append("- `Rz`: torsional tip rotation.")
    lines.append("- `Section evaluations`: number of CSF section evaluations used by the model.")
    lines.append("- Relative error: `100 * (OpenSees - reference) / reference`.")
    lines.append("")

    for scenario, scenario_rows in grouped.items():
        lines.append(f"## {scenario_title(scenario)}")
        lines.append("")
        lines.append(scenario_interpretation(scenario))
        lines.append("")
        write_markdown_table(lines, scenario_rows)
        lines.append("")

    lines.append("## Input files")
    lines.append("")

    for scenario in grouped:
        reference_dir, opensees_dir = input_dirs[scenario]
        lines.append(f"- `{scenario}`:")
        lines.append(f"  - Analytical reference: `{reference_dir / 'analytical_reference.txt'}`.")
        lines.append(f"  - OpenSees tip response: `{opensees_dir / 'openseeslab_tip_response.csv'}`.")

    lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")


def input_dirs_from_scenarios(scenarios: Iterable[ScenarioFiles]) -> Dict[str, Tuple[Path, Path]]:
    return {
        scenario.scenario_name: (scenario.reference_dir, scenario.opensees_dir)
        for scenario in scenarios
    }


def run_scenario(
    scenario: ScenarioFiles,
    input_dirs: Dict[str, Tuple[Path, Path]],
) -> List[TipRow]:
    tip_csv = scenario.opensees_dir / "openseeslab_tip_response.csv"
    reference_file = scenario.reference_dir / "analytical_reference.txt"

    if not tip_csv.is_file():
        raise FileNotFoundError(f"Missing OpenSees tip response CSV: {tip_csv}")

    if not reference_file.is_file():
        raise FileNotFoundError(f"Missing analytical reference report: {reference_file}")

    uy_reference, rz_reference = read_reference(reference_file)

    rows = read_tip_response(
        scenario_name=scenario.scenario_name,
        tip_csv=tip_csv,
        uy_reference=uy_reference,
        rz_reference=rz_reference,
    )

    write_csv(rows, scenario.opensees_dir / "validation_comparison_summary.csv")
    write_markdown(
        rows,
        scenario.opensees_dir / "validation_comparison_summary.md",
        title=f"Validation comparison - {scenario.scenario_name}",
        input_dirs=input_dirs,
    )

    return rows


def main() -> None:
    input_dirs = input_dirs_from_scenarios(DEFAULT_SCENARIOS)

    all_rows: List[TipRow] = []

    for scenario in DEFAULT_SCENARIOS:
        print(f"Reading scenario: {scenario.scenario_name}")
        print(f"  OpenSees response dir: {scenario.opensees_dir}")
        print(f"  Analytical reference dir: {scenario.reference_dir}")

        rows = run_scenario(scenario, input_dirs)
        all_rows.extend(rows)

        print(f"  wrote: {scenario.opensees_dir / 'validation_comparison_summary.csv'}")
        print(f"  wrote: {scenario.opensees_dir / 'validation_comparison_summary.md'}")

    write_csv(all_rows, Path("validation_comparison_summary_all.csv"))
    write_markdown(
        all_rows,
        Path("validation_comparison_summary_all.md"),
        title="Validation comparison - all scenarios",
        input_dirs=input_dirs,
    )

    print()
    print("DONE")
    print("Global CSV: validation_comparison_summary_all.csv")
    print("Global Markdown: validation_comparison_summary_all.md")


if __name__ == "__main__":
    main()

"""Build the published validation comparison for the two NREL scenarios."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_SCENARIOS: Tuple[str, ...] = ("NREL-5-MW", "NREL-5-MW-degr")


@dataclass(frozen=True)
class ScenarioFiles:
    name: str
    reference_file: Path
    tip_response_file: Path


@dataclass(frozen=True)
class TipRow:
    scenario: str
    model_label: str
    n_elems: int
    n_section_calls: int
    uy_opensees: float
    rz_opensees: float
    uy_reference: float
    rz_reference: float

    @property
    def uy_rel_error(self) -> float:
        return 100.0 * (self.uy_opensees - self.uy_reference) / self.uy_reference

    @property
    def rz_rel_error(self) -> float:
        return 100.0 * (self.rz_opensees - self.rz_reference) / self.rz_reference

    @property
    def compact_model_label(self) -> str:
        match = re.search(r"uniform\s+(\d+)", self.model_label, re.IGNORECASE)
        if match:
            return f"Uniform-{match.group(1)}"
        return self.model_label


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the published CSF/OpenSees validation comparison.")
    return parser.parse_args()


def scenario_files(name: str) -> ScenarioFiles:
    return ScenarioFiles(
        name=name,
        reference_file=Path(f"baseline_output_{name}") / "analytical_reference.txt",
        tip_response_file=Path(f"openseeslab_output_{name}") / "openseeslab_tip_response.csv",
    )


def read_reference(reference_file: Path) -> Tuple[float, float]:
    text = reference_file.read_text(encoding="utf-8")

    uy_match = re.search(r"Uy_reference\s*:\s*([-+0-9.eE]+)", text)
    rz_match = re.search(r"Rz_reference\s*:\s*([-+0-9.eE]+)", text)

    if uy_match is None:
        raise RuntimeError(f"Unable to find Uy_reference in {reference_file}")
    if rz_match is None:
        raise RuntimeError(f"Unable to find Rz_reference in {reference_file}")

    return float(uy_match.group(1)), float(rz_match.group(1))


def read_tip_rows(files: ScenarioFiles) -> List[TipRow]:
    if not files.reference_file.is_file():
        raise FileNotFoundError(f"Missing analytical reference: {files.reference_file}")
    if not files.tip_response_file.is_file():
        raise FileNotFoundError(f"Missing OpenSees tip response: {files.tip_response_file}")

    uy_ref, rz_ref = read_reference(files.reference_file)
    rows: List[TipRow] = []

    with open(files.tip_response_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"model_label", "n_elems", "n_section_calls", "Uy_tip", "Rz_tip"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"Missing columns in {files.tip_response_file}: {sorted(missing)}")

        for row in reader:
            rows.append(
                TipRow(
                    scenario=files.name,
                    model_label=row["model_label"],
                    n_elems=int(row["n_elems"]),
                    n_section_calls=int(row["n_section_calls"]),
                    uy_opensees=float(row["Uy_tip"]),
                    rz_opensees=float(row["Rz_tip"]),
                    uy_reference=uy_ref,
                    rz_reference=rz_ref,
                )
            )

    rows.sort(key=lambda r: r.n_elems)
    return rows


def group_by_scenario(rows: Iterable[TipRow]) -> Dict[str, List[TipRow]]:
    grouped: Dict[str, List[TipRow]] = {}
    for row in rows:
        grouped.setdefault(row.scenario, []).append(row)
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
    return "This case compares the CSF-OpenSees response against the independent reference."


def write_csv(rows: List[TipRow], output_file: Path) -> None:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenario",
            "model_label",
            "n_elems",
            "n_section_calls",
            "Uy_OpenSees",
            "Uy_reference",
            "Uy_rel_error_pct",
            "Rz_OpenSees",
            "Rz_reference",
            "Rz_rel_error_pct",
        ])
        for r in rows:
            writer.writerow([
                r.scenario,
                r.model_label,
                r.n_elems,
                r.n_section_calls,
                f"{r.uy_opensees:.12e}",
                f"{r.uy_reference:.12e}",
                f"{r.uy_rel_error:.12e}",
                f"{r.rz_opensees:.12e}",
                f"{r.rz_reference:.12e}",
                f"{r.rz_rel_error:.12e}",
            ])


def write_markdown_table(lines: List[str], rows: List[TipRow]) -> None:
    lines.append("| Model | Elements | Section evaluations | Uy OpenSees | Uy reference | Uy rel. error [%] | Rz OpenSees | Rz reference | Rz rel. error [%] |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
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


def write_markdown(rows: List[TipRow], files_by_scenario: Dict[str, ScenarioFiles], output_file: Path) -> None:
    grouped = group_by_scenario(rows)
    lines: List[str] = []

    lines.append("# Validation comparison - all scenarios")
    lines.append("")
    lines.append("This report compares the CSF-OpenSees tip response against an independent analytical reference.")
    lines.append("")
    lines.append("## Conceptual structure")
    lines.append("")
    lines.append(
        "Two configurations are compared. The undegraded NREL tower is used as the "
        "baseline validation case. The degraded tower is used as the critical "
        "convergence case, because localized stiffness variation makes coarse "
        "piecewise discretizations less reliable."
    )
    lines.append("")
    lines.append("## Key quantities")
    lines.append("")
    lines.append("- `Uy`: transverse tip displacement.")
    lines.append("- `Rz`: torsional tip rotation.")
    lines.append("- `Section evaluations`: number of CSF section evaluations used by the model.")
    lines.append("- Relative error: `100 * (OpenSees - reference) / reference`.")
    lines.append("")

    for scenario in DEFAULT_SCENARIOS:
        scenario_rows = grouped.get(scenario, [])
        if not scenario_rows:
            continue
        lines.append(f"## {scenario_title(scenario)}")
        lines.append("")
        lines.append(scenario_interpretation(scenario))
        lines.append("")
        write_markdown_table(lines, scenario_rows)
        lines.append("")

    lines.append("## Input files")
    lines.append("")
    for scenario in DEFAULT_SCENARIOS:
        files = files_by_scenario[scenario]
        lines.append(f"- `{scenario}`:")
        lines.append(f"  - Analytical reference: `{files.reference_file}`.")
        lines.append(f"  - OpenSees tip response: `{files.tip_response_file}`.")
    lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()

    files_by_scenario = {name: scenario_files(name) for name in DEFAULT_SCENARIOS}
    rows: List[TipRow] = []

    for name in DEFAULT_SCENARIOS:
        rows.extend(read_tip_rows(files_by_scenario[name]))

    write_csv(rows, Path("validation_comparison_summary_all.csv"))
    write_markdown(rows, files_by_scenario, Path("validation_comparison_summary_all.md"))

    print("DONE")
    print("Global CSV: validation_comparison_summary_all.csv")
    print("Global Markdown: validation_comparison_summary_all.md")


if __name__ == "__main__":
    main()

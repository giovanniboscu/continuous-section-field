"""
Independent continuous baseline for the NREL tower case
===============================================================

This script computes an independent continuous reference for the NREL-type
closed-cell tower benchmark used in the paper.

It is intentionally case-specific. It is not a generic CSF evaluator. The YAML
weight law is read only to select one of the supported hardcoded NREL material
cases. The YAML file provides:

    YAML endpoint geometry and material-case selector
        -> annular closed-section formulas
        -> explicit E(z) law selected from hardcoded benchmark cases
        -> isotropic G(z) = E(z) / [2(1 + nu)]
        -> continuous EI(z) and GJ(z)
        -> Simpson integration of Uy and Rz

This makes the baseline independent from CSF section-sampling APIs and from CSF
expression evaluation. The modelling choices are stated directly where they are
used.

Run example
-----------

    python nrel_degraded_independent_baseline_paper.py NREL-5-MW.yaml
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import yaml


# =====================================================================
# USER-CONTROLLED NUMERICAL CASE
# =====================================================================

# Reference-grid selection. The selected grid is the first grid satisfying the
# tolerance against the finest grid in this prescribed sequence.
REF_TOL_PCT = 1.0e-10
N_REF_SEQUENCE: Tuple[int, ...] = (251, 501, 1001, 2001, 4001, 8001)

# Isotropic relation used by the benchmark to reconstruct G(z) from E(z).
NU = 0.3

# Static load case used for the response comparison.
# FZ_TIP is intentionally not used in this baseline because this reference
# computes Uy and Rz only; it does not compute axial shortening or second-order
# geometric effects.
FY_TIP = 1.2e6   # Transverse concentrated tip force.
FZ_TIP = -5.0e6  # Axial tip force in OpenSees; excluded from this baseline.
MX_TIP = 8.0e6   # Concentrated bending moment about global X.
MZ_TIP = 3.0e6   # Concentrated torsional moment about global Z.
WY_DIST = 8.0e3  # Uniform transverse distributed load.


# =====================================================================
# DATA STRUCTURES
# =====================================================================

@dataclass(frozen=True)
class ProblemData:
    """Endpoint geometry and selected material law used by the independent NREL baseline."""

    yaml_file: Path
    z0: float
    z1: float
    L: float
    ri0: float
    ro0: float
    ri1: float
    ro1: float
    material_case: str
    E_fn: Callable[[float, float], float]


@dataclass(frozen=True)
class ReferenceResult:
    """Reference response computed on one axial grid."""

    n_ref: int
    dz: float
    uy_force_component: float
    uy_uniform_component: float
    uy_tip_moment_component: float
    uy_reference: float
    rz_reference: float


@dataclass(frozen=True)
class GridSelectionRow:
    """One row of the numerical reference-grid selection table."""

    n_coarse: int
    n_fine: int
    dz_fine: float
    uy_err_est_pct: float
    rz_err_est_pct: float
    max_err_est_pct: float
    accepted: bool


# =====================================================================
# 1. COMMAND-LINE INPUTS
# =====================================================================

def parse_args() -> argparse.Namespace:
    """Read the YAML input explicitly from the command line."""
    parser = argparse.ArgumentParser(
        description="Compute the independent baseline for the supported NREL tower cases."
    )
    parser.add_argument(
        "yaml",
        type=Path,
        help="CSF YAML input file. Endpoint geometry and weight-law selector are read from it.",
    )
    return parser.parse_args()


# =====================================================================
# 2. YAML GEOMETRY AND MATERIAL-CASE READING
# =====================================================================

def load_yaml(path: Path) -> Dict[str, Any]:
    """Load the YAML file used for endpoint geometry and material-case selection."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def polygon_radii(vertices: List[List[float]]) -> Tuple[float, float]:
    """Return minimum and maximum radius from polygon vertices.

    The baseline is dedicated to the NREL-type annular closed-cell tower. Each
    endpoint polygon is therefore reduced to an inner and outer radius for the
    closed-section formulas used below.
    """
    radii: List[float] = []

    for v in vertices:
        x = float(v[0])
        y = float(v[1])
        radii.append(math.sqrt(x * x + y * y))

    if not radii:
        raise ValueError("Polygon has no vertices.")

    return min(radii), max(radii)


def nrel_constant_E(z: float, L: float) -> float:
    """Return the constant E used by the non-degraded NREL benchmark."""
    return 210.0e9


def extract_single_weight_expression(csf: Dict[str, Any]) -> str:
    """Read the single YAML weight-law expression only to select the hardcoded case."""
    weight_laws = csf.get("weight_laws", [])

    if len(weight_laws) != 1:
        raise ValueError(
            "This NREL baseline expects exactly one weight law. "
            f"Found {len(weight_laws)}."
        )

    raw = str(weight_laws[0]).strip()

    if ":" in raw:
        raw = raw.split(":", 1)[1].strip()

    return raw


def normalize_expression(expr: str) -> str:
    """Normalize a weight-law string for deterministic case selection."""
    return (
        str(expr)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("\n", "")
    )


def select_hardcoded_material_law(
    weight_expr: str,
) -> Tuple[str, Callable[[float, float], float]]:
    """Select one of the hardcoded NREL material laws from the YAML weight law.

    The YAML expression is used only as a selector. It is not evaluated.
    """
    expr = normalize_expression(weight_expr)

    try:
        value = float(expr)
        if math.isclose(value, 210.0e9, rel_tol=0.0, abs_tol=1.0):
            return "NREL constant E = 210e9", nrel_constant_E
    except ValueError:
        pass

    degraded_scale_tokens = (
        "210000000000",
        "210e9",
        "210.0e9",
        "2.1e11",
        "2.10e11",
    )
    degraded_shape_tokens = (
        "0.84",
        "0.10",
        "0.14",
        "0.33*l",
        "0.67*l",
        "0.03*l",
        "exp",
    )

    if (
        any(token in expr for token in degraded_scale_tokens)
        and all(token in expr for token in degraded_shape_tokens)
    ):
        return "NREL degraded E(z)", nrel_degraded_E

    raise ValueError(
        "Unsupported NREL material law. "
        "This script only supports the hardcoded constant and degraded NREL cases. "
        f"YAML weight expression was: {weight_expr}"
    )


def read_problem_data(yaml_file: Path) -> ProblemData:
    """Read endpoint geometry and select the supported hardcoded material case.

    This function is deliberately specialized to the paper benchmark:
      - endpoint sections S0 and S1;
      - one annular closed-cell polygon per endpoint section;
      - the YAML weight law is read only to select one of the supported
        hardcoded E(z) laws. The expression itself is not evaluated.
    """
    data = load_yaml(yaml_file)
    csf = data["CSF"]

    weight_expr = extract_single_weight_expression(csf)
    material_case, E_fn = select_hardcoded_material_law(weight_expr)

    s0 = csf["sections"]["S0"]
    s1 = csf["sections"]["S1"]

    z0 = float(s0["z"])
    z1 = float(s1["z"])

    # L is the physical member length. It must be positive and must not depend
    # on the orientation used by the YAML endpoint coordinates.
    L = abs(z1 - z0)
    if L <= 0.0:
        raise ValueError(f"Invalid member length from YAML endpoints: z0={z0}, z1={z1}")

    # The first polygon is intentionally used because this benchmark has one
    # closed-cell polygon per endpoint section. This script is not a multi-zone
    # CSF YAML interpreter.
    poly0 = next(iter(s0["polygons"].values()))
    poly1 = next(iter(s1["polygons"].values()))

    ri0, ro0 = polygon_radii(poly0["vertices"])
    ri1, ro1 = polygon_radii(poly1["vertices"])

    return ProblemData(
        yaml_file=yaml_file,
        z0=z0,
        z1=z1,
        L=L,
        ri0=ri0,
        ro0=ro0,
        ri1=ri1,
        ro1=ro1,
        material_case=material_case,
        E_fn=E_fn,
    )


# =====================================================================
# 3. EXPLICIT BENCHMARK MATERIAL LAWS
# =====================================================================

def nrel_degraded_E(z: float, L: float) -> float:
    """Return the degraded E(z) law used by the paper benchmark.

    This is one of the supported hardcoded material laws used by this baseline.
    baseline. 

    The coordinate z is local: z = 0 at the base and z = L at the tip.
    """
    return 210.0e9 * max(
        0.84,
        1.0
        - 0.10 * math.exp(-((z - 0.33 * L) ** 2) / (2.0 * (0.03 * L) ** 2))
        - 0.14 * math.exp(-((z - 0.67 * L) ** 2) / (2.0 * (0.03 * L) ** 2)),
    )


# =====================================================================
# 4. CONTINUOUS REFERENCE COMPUTATION
# =====================================================================

def simpson(y: np.ndarray, x: np.ndarray) -> float:
    """Composite Simpson integration for an odd number of equally spaced points."""
    if len(x) < 3:
        raise ValueError("Need at least 3 points.")
    if len(x) % 2 == 0:
        raise ValueError("Need odd number of points.")

    h = (x[-1] - x[0]) / (len(x) - 1)

    return float(
        h / 3.0 * (
            y[0]
            + y[-1]
            + 4.0 * np.sum(y[1:-1:2])
            + 2.0 * np.sum(y[2:-2:2])
        )
    )


def compute_reference(n_ref: int, problem: ProblemData) -> ReferenceResult:
    """Compute the independent continuous reference on one axial grid.

    The baseline uses a local axial coordinate z in [0, L]. It does not call CSF
    section APIs and it does not evaluate YAML weight laws.
    """
    if n_ref % 2 == 0:
        raise ValueError("n_ref must be odd for Simpson integration.")

    L = problem.L
    z = np.linspace(0.0, L, n_ref)
    eta = z / L

    # Linear interpolation of endpoint radii for the NREL tower geometry.
    r_outer = problem.ro0 + (problem.ro1 - problem.ro0) * eta
    r_inner = problem.ri0 + (problem.ri1 - problem.ri0) * eta

    # Hardcoded E(z) law selected from the YAML case. The YAML expression is
    # used only to choose the supported benchmark case; it is not evaluated.
    E = np.array([problem.E_fn(float(zi), L) for zi in z], dtype=float)
    G = E / (2.0 * (1.0 + NU))

    # Closed annular section formulas. These are not generic CSF formulas; they
    # are the independent analytical formulas for this NREL-type tower baseline.
    I = math.pi / 4.0 * (r_outer**4 - r_inner**4)
    EI = E * I

    J = 0.5 * math.pi * (r_outer**4 - r_inner**4)
    GJ = G * J

    # Unit-load bending integrand for tip displacement Uy.
    m_unit = L - z

    # Sign convention used by this baseline:
    #   - FY_TIP produces the positive Uy contribution below;
    #   - the distributed load and the tip bending moment use the signs adopted
    #     in the OpenSees comparison case.
    M_fy = FY_TIP * (L - z)
    M_wy = 0.5 * WY_DIST * (L - z) ** 2
    M_mx = MX_TIP * np.ones_like(z)

    uy_fy_component = simpson(M_fy * m_unit / EI, z)
    uy_wy_component = -simpson(M_wy * m_unit / EI, z)
    uy_mx_component = -simpson(M_mx * m_unit / EI, z)

    uy_reference = uy_fy_component + uy_wy_component + uy_mx_component
    rz_reference = MZ_TIP * simpson(1.0 / GJ, z)

    return ReferenceResult(
        n_ref=int(n_ref),
        dz=float(L / (n_ref - 1)),
        uy_force_component=float(uy_fy_component),
        uy_uniform_component=float(uy_wy_component),
        uy_tip_moment_component=float(uy_mx_component),
        uy_reference=float(uy_reference),
        rz_reference=float(rz_reference),
    )


# =====================================================================
# 5. REFERENCE GRID SELECTION
# =====================================================================

def relative_error_pct(value: float, reference: float) -> float:
    """Return absolute relative error in percent."""
    return abs(100.0 * (value - reference) / reference)


def build_grid_selection(
    convergence: List[ReferenceResult],
) -> Tuple[List[GridSelectionRow], ReferenceResult, str]:
    """Select the first grid satisfying the tolerance against the finest grid.

    The result is a numerical continuous reference, not a symbolic closed-form
    exact solution. The finest grid in N_REF_SEQUENCE is used as the reference
    for grid-selection purposes.
    """
    finest = convergence[-1]
    uy_finest = finest.uy_reference
    rz_finest = finest.rz_reference

    selection_rows: List[GridSelectionRow] = []
    selected: ReferenceResult | None = None
    status = "tolerance not reached"

    for coarse, fine in zip(convergence[:-1], convergence[1:]):
        uy_err = relative_error_pct(fine.uy_reference, uy_finest)
        rz_err = relative_error_pct(fine.rz_reference, rz_finest)
        max_err = max(uy_err, rz_err)
        accepted = max_err <= REF_TOL_PCT

        row = GridSelectionRow(
            n_coarse=int(coarse.n_ref),
            n_fine=int(fine.n_ref),
            dz_fine=float(fine.dz),
            uy_err_est_pct=float(uy_err),
            rz_err_est_pct=float(rz_err),
            max_err_est_pct=float(max_err),
            accepted=bool(accepted),
        )
        selection_rows.append(row)

        if accepted and selected is None:
            selected = fine
            status = "tolerance reached"

    if selected is None:
        selected = finest

    return selection_rows, selected, status


# =====================================================================
# 6. OUTPUTS
# =====================================================================

def write_csv_files(
    convergence_file: Path,
    selection_file: Path,
    convergence: List[ReferenceResult],
    selection_rows: List[GridSelectionRow],
    selected_n_ref: int,
) -> None:
    """Write convergence and grid-selection CSV files."""
    finest = convergence[-1]
    uy_finest = finest.uy_reference
    rz_finest = finest.rz_reference

    with open(convergence_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "N_REF",
            "dz",
            "Uy_reference",
            "Uy_rel_diff_vs_finest_pct",
            "Rz_reference",
            "Rz_rel_diff_vs_finest_pct",
            "selected",
        ])

        for row in convergence:
            uy_rel = 100.0 * (row.uy_reference - uy_finest) / uy_finest
            rz_rel = 100.0 * (row.rz_reference - rz_finest) / rz_finest
            selected = "yes" if int(row.n_ref) == selected_n_ref else "no"
            writer.writerow([
                int(row.n_ref),
                f"{row.dz:.12e}",
                f"{row.uy_reference:.12e}",
                f"{uy_rel:.12e}",
                f"{row.rz_reference:.12e}",
                f"{rz_rel:.12e}",
                selected,
            ])

    with open(selection_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "N_coarse",
            "N_fine",
            "dz_fine",
            "Uy_err_est_pct",
            "Rz_err_est_pct",
            "max_err_est_pct",
            "accepted",
        ])

        for row in selection_rows:
            writer.writerow([
                row.n_coarse,
                row.n_fine,
                f"{row.dz_fine:.12e}",
                f"{row.uy_err_est_pct:.12e}",
                f"{row.rz_err_est_pct:.12e}",
                f"{row.max_err_est_pct:.12e}",
                "yes" if row.accepted else "no",
            ])


def build_report(
    problem: ProblemData,
    convergence: List[ReferenceResult],
    selection_rows: List[GridSelectionRow],
    selected: ReferenceResult,
    status: str,
) -> str:
    """Build the text report printed to stdout and written to file."""
    lines: List[str] = []

    lines.append("")
    lines.append("INDEPENDENT CONTINUOUS BASELINE")
    lines.append("=" * 78)
    lines.append(f"YAML file                  : {problem.yaml_file}")
    lines.append(f"z0                         : {problem.z0:.12e}")
    lines.append(f"z1                         : {problem.z1:.12e}")
    lines.append(f"L                          : {problem.L:.12e}")
    lines.append(f"REF_TOL_PCT                : {REF_TOL_PCT:.12e}")
    lines.append("N_REF_SEQUENCE             : " + ", ".join(str(n) for n in N_REF_SEQUENCE))

    lines.append("")
    lines.append("Geometry read from YAML")
    lines.append("-" * 78)
    lines.append(f"R_OUTER_BASE               : {problem.ro0:.12e}")
    lines.append(f"R_OUTER_TOP                : {problem.ro1:.12e}")
    lines.append(f"R_INNER_BASE               : {problem.ri0:.12e}")
    lines.append(f"R_INNER_TOP                : {problem.ri1:.12e}")

    lines.append("")
    lines.append("Reference E(z) law used in the computation")
    lines.append("-" * 78)
    lines.append(f"Material case               : {problem.material_case}")
    lines.append("The selected E(z) law is hardcoded in this script.")

    lines.append("")
    lines.append("Baseline assumptions")
    lines.append("-" * 78)
    lines.append("- NREL-type annular closed-cell section.")
    lines.append("- One endpoint polygon per section is reduced to inner/outer radii.")
    lines.append("- The YAML weight law is read only to select a supported hardcoded case.")
    lines.append("- No YAML weight law expression is evaluated by this baseline.")
    lines.append("- G(z) is reconstructed from E(z) through G = E / [2(1 + nu)].")
    lines.append("- The reference is numerical continuous, selected by grid convergence.")

    lines.append("")
    lines.append("ADAPTIVE REFERENCE GRID SELECTION")
    lines.append("=" * 78)
    lines.append(
        "N_coarse  N_fine     dz_fine [m]   Uy err. est. [%]   "
        "Rz err. est. [%]   max err. est. [%]   accepted"
    )
    lines.append("-" * 116)

    for row in selection_rows:
        lines.append(
            f"{row.n_coarse:>8d}  "
            f"{row.n_fine:>7d}    "
            f"{row.dz_fine:>12.6e}  "
            f"{row.uy_err_est_pct:>18.12e}  "
            f"{row.rz_err_est_pct:>18.12e}  "
            f"{row.max_err_est_pct:>18.12e}  "
            f"{'yes' if row.accepted else 'no':>8}"
        )

    lines.append("")
    lines.append("SELECTED REFERENCE GRID")
    lines.append("=" * 78)
    lines.append(f"N_REF                      : {int(selected.n_ref)}")
    lines.append(f"dz [m]                     : {selected.dz:.12e}")
    lines.append(f"Selection status            : {status}")

    lines.append("")
    lines.append("REFERENCE RESULTS")
    lines.append("=" * 78)

    lines.append("")
    lines.append("CHECK 1 - TIP DISPLACEMENT Uy")
    lines.append("-" * 78)
    lines.append(f"Uy_force_component         : {selected.uy_force_component:.12e}")
    lines.append(f"Uy_uniform_component       : {selected.uy_uniform_component:.12e}")
    lines.append(f"Uy_tip_moment_component    : {selected.uy_tip_moment_component:.12e}")
    lines.append(f"Uy_reference               : {selected.uy_reference:.12e}")

    lines.append("")
    lines.append("CHECK 2 - TIP TORSIONAL ROTATION Rz")
    lines.append("-" * 78)
    lines.append(f"Rz_reference               : {selected.rz_reference:.12e} rad")

    lines.append("")
    lines.append("REFERENCE GRID VALUES")
    lines.append("=" * 78)
    lines.append("N_REF     dz [m]        Uy_reference       Rz_reference       selected")
    lines.append("-" * 82)

    selected_n_ref = int(selected.n_ref)
    for row in convergence:
        selected_label = "yes" if int(row.n_ref) == selected_n_ref else "no"
        lines.append(
            f"{int(row.n_ref):>5d}  "
            f"{row.dz:>12.6e}  "
            f"{row.uy_reference:>18.12e}  "
            f"{row.rz_reference:>18.12e}  "
            f"{selected_label:>8}"
        )

    return "\n".join(lines)


# =====================================================================
# 7. WORKFLOW
# =====================================================================

def run_baseline(yaml_file: Path) -> Tuple[Path, Path, Path]:
    """Run the independent continuous baseline and write output files."""
    yaml_stem = yaml_file.stem
    output_dir = Path(f"baseline_output_{yaml_stem}")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "analytical_reference.txt"
    convergence_file = output_dir / "analytical_reference_convergence.csv"
    selection_file = output_dir / "analytical_reference_grid_selection.csv"

    problem = read_problem_data(yaml_file)

    convergence = [compute_reference(n_ref, problem) for n_ref in N_REF_SEQUENCE]
    selection_rows, selected, status = build_grid_selection(convergence)
    selected_n_ref = int(selected.n_ref)

    output_text = build_report(
        problem=problem,
        convergence=convergence,
        selection_rows=selection_rows,
        selected=selected,
        status=status,
    )

    write_csv_files(
        convergence_file=convergence_file,
        selection_file=selection_file,
        convergence=convergence,
        selection_rows=selection_rows,
        selected_n_ref=selected_n_ref,
    )

    print(output_text)
    report_file.write_text(output_text + "\n", encoding="utf-8")

    return report_file, convergence_file, selection_file


def main() -> None:
    """Entry point."""
    args = parse_args()
    report_file, convergence_file, selection_file = run_baseline(args.yaml)

    print()
    print(f"Baseline reference report: {report_file}")
    print(f"Reference convergence CSV: {convergence_file}")
    print(f"Reference grid selection CSV: {selection_file}")


if __name__ == "__main__":
    main()

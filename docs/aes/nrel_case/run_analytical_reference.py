"""
Independent continuous baseline from CSF YAML without using CSF section APIs.

The script:
  - reads geometry directly from YAML;
  - reads weight_laws directly from YAML;
  - reconstructs:
        E(z)
        G(z)
        EI(z)
        GJ(z)
  - computes:
        Uy tip displacement
        Rz tip torsional rotation
  - selects the reference grid from a prescribed tolerance.

No CSF section sampling APIs are used.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import yaml


DEFAULT_YAML = "NREL-5-MW.yaml"
REF_TOL_PCT = 1.0e-10
N_REF_SEQUENCE = (251, 501, 1001, 2001, 4001, 8001)
NU = 0.3


# Load case used for the structural response comparison.
# FY_TIP, MX_TIP, and WY_DIST contribute to the transverse tip displacement Uy.
# MZ_TIP contributes to the torsional tip rotation Rz.
# FZ_TIP is applied in the OpenSees model as axial load, but it is not used
# in the independent analytical reference because this check does not evaluate
# axial shortening or second-order geometric effects.
FY_TIP = 1.2e6   # Transverse concentrated tip force in global Y.
FZ_TIP = -5.0e6  # Axial tip force; excluded from Uy/Rz analytical checks.
MX_TIP = 8.0e6   # Concentrated bending moment about global X.
MZ_TIP = 3.0e6   # Concentrated torsional moment about global Z.
WY_DIST = 8.0e3  # Uniform transverse distributed load in global/local Y.



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


def load_yaml(path: str) -> Dict[str, Any]:
    """Load a CSF YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def polygon_radii(vertices: List[List[float]]) -> Tuple[float, float]:
    """Return minimum and maximum radius from polygon vertices."""
    radii: List[float] = []

    for v in vertices:
        x = float(v[0])
        y = float(v[1])
        radii.append(math.sqrt(x * x + y * y))

    if not radii:
        raise ValueError("Polygon has no vertices.")

    return min(radii), max(radii)


def compile_weight_expression(expr: str):
    """Compile a CSF weight expression into a function of z and L."""
    expr = str(expr).strip()

    if ":" in expr:
        expr = expr.split(":", 1)[1].strip()

    expr = expr.replace("^", "**")

    allowed = {
        "np": np,
        "exp": np.exp,
        "sqrt": np.sqrt,
        "sin": np.sin,
        "cos": np.cos,
        "pi": np.pi,
        "maximum": np.maximum,
        "minimum": np.minimum,
    }

    def evaluator(z, L):
        return eval(
            expr,
            {"__builtins__": {}},
            {
                **allowed,
                "z": z,
                "L": L,
            },
        )

    return evaluator


def read_problem_data(yaml_file: str) -> Dict[str, Any]:
    """Read the geometry and weight law needed by the autonomous reference."""
    data = load_yaml(yaml_file)
    csf = data["CSF"]

    s0 = csf["sections"]["S0"]
    s1 = csf["sections"]["S1"]

    z0 = float(s0["z"])
    z1 = float(s1["z"])
    L = z1 - z0

    poly0 = next(iter(s0["polygons"].values()))
    poly1 = next(iter(s1["polygons"].values()))

    ri0, ro0 = polygon_radii(poly0["vertices"])
    ri1, ro1 = polygon_radii(poly1["vertices"])

    weight_expr = csf["weight_laws"][0]
    weight_fn = compile_weight_expression(weight_expr)

    return {
        "L": L,
        "ri0": ri0,
        "ro0": ro0,
        "ri1": ri1,
        "ro1": ro1,
        "weight_expr": weight_expr,
        "weight_fn": weight_fn,
    }


def compute_reference(
    n_ref: int,
    L: float,
    ro0: float,
    ro1: float,
    ri0: float,
    ri1: float,
    weight_fn,
) -> Dict[str, float]:
    """Compute the independent continuous reference on one axial grid."""
    if n_ref % 2 == 0:
        raise ValueError("n_ref must be odd for Simpson integration.")

    z = np.linspace(0.0, L, n_ref)
    eta = z / L

    r_outer = ro0 + (ro1 - ro0) * eta
    r_inner = ri0 + (ri1 - ri0) * eta

    E = np.array([float(weight_fn(zi, L)) for zi in z], dtype=float)
    G = E / (2.0 * (1.0 + NU))

    I = math.pi / 4.0 * (r_outer**4 - r_inner**4)
    EI = E * I

    J = 0.5 * math.pi * (r_outer**4 - r_inner**4)
    GJ = G * J

    m_unit = L - z

    M_fy = FY_TIP * (L - z)
    M_wy = 0.5 * WY_DIST * (L - z) ** 2
    M_mx = MX_TIP * np.ones_like(z)

    uy_fy_component = simpson(M_fy * m_unit / EI, z)
    uy_wy_component = -simpson(M_wy * m_unit / EI, z)
    uy_mx_component = -simpson(M_mx * m_unit / EI, z)

    uy_reference = uy_fy_component + uy_wy_component + uy_mx_component
    rz_reference = MZ_TIP * simpson(1.0 / GJ, z)

    return {
        "N_REF": int(n_ref),
        "dz": float(L / (n_ref - 1)),
        "Uy_force_component": float(uy_fy_component),
        "Uy_uniform_component": float(uy_wy_component),
        "Uy_tip_moment_component": float(uy_mx_component),
        "Uy_reference": float(uy_reference),
        "Rz_reference": float(rz_reference),
    }


def relative_error_pct(value: float, reference: float) -> float:
    """Return absolute relative error in percent."""
    return abs(100.0 * (value - reference) / reference)


def build_grid_selection(convergence: List[Dict[str, float]]) -> Tuple[List[Dict[str, Any]], Dict[str, float], str]:
    """Select the first reference grid satisfying REF_TOL_PCT against the finest grid."""
    finest = convergence[-1]
    uy_finest = finest["Uy_reference"]
    rz_finest = finest["Rz_reference"]

    selection_rows: List[Dict[str, Any]] = []
    selected: Dict[str, float] | None = None
    status = "tolerance not reached"

    for coarse, fine in zip(convergence[:-1], convergence[1:]):
        uy_err = relative_error_pct(fine["Uy_reference"], uy_finest)
        rz_err = relative_error_pct(fine["Rz_reference"], rz_finest)
        max_err = max(uy_err, rz_err)
        accepted = max_err <= REF_TOL_PCT

        row = {
            "N_coarse": int(coarse["N_REF"]),
            "N_fine": int(fine["N_REF"]),
            "dz_fine": float(fine["dz"]),
            "Uy_err_est_pct": float(uy_err),
            "Rz_err_est_pct": float(rz_err),
            "max_err_est_pct": float(max_err),
            "accepted": bool(accepted),
        }
        selection_rows.append(row)

        if accepted and selected is None:
            selected = fine
            status = "tolerance reached"

    if selected is None:
        selected = finest

    return selection_rows, selected, status


def write_csv_files(
    convergence_file: Path,
    selection_file: Path,
    convergence: List[Dict[str, float]],
    selection_rows: List[Dict[str, Any]],
    selected_n_ref: int,
) -> None:
    """Write convergence and adaptive grid-selection CSV files."""
    finest = convergence[-1]
    uy_finest = finest["Uy_reference"]
    rz_finest = finest["Rz_reference"]

    convergence_lines = [
        "N_REF,dz,Uy_reference,Uy_rel_diff_vs_finest_pct,"
        "Rz_reference,Rz_rel_diff_vs_finest_pct,selected"
    ]

    for row in convergence:
        uy_rel = 100.0 * (row["Uy_reference"] - uy_finest) / uy_finest
        rz_rel = 100.0 * (row["Rz_reference"] - rz_finest) / rz_finest
        selected = "yes" if int(row["N_REF"]) == selected_n_ref else "no"
        convergence_lines.append(
            f"{int(row['N_REF'])},"
            f"{row['dz']:.12e},"
            f"{row['Uy_reference']:.12e},"
            f"{uy_rel:.12e},"
            f"{row['Rz_reference']:.12e},"
            f"{rz_rel:.12e},"
            f"{selected}"
        )

    selection_lines = [
        "N_coarse,N_fine,dz_fine,Uy_err_est_pct,Rz_err_est_pct,"
        "max_err_est_pct,accepted"
    ]

    for row in selection_rows:
        selection_lines.append(
            f"{row['N_coarse']},"
            f"{row['N_fine']},"
            f"{row['dz_fine']:.12e},"
            f"{row['Uy_err_est_pct']:.12e},"
            f"{row['Rz_err_est_pct']:.12e},"
            f"{row['max_err_est_pct']:.12e},"
            f"{'yes' if row['accepted'] else 'no'}"
        )

    convergence_file.write_text("\n".join(convergence_lines) + "\n", encoding="utf-8")
    selection_file.write_text("\n".join(selection_lines) + "\n", encoding="utf-8")


def build_report(
    yaml_file: str,
    problem: Dict[str, Any],
    convergence: List[Dict[str, float]],
    selection_rows: List[Dict[str, Any]],
    selected: Dict[str, float],
    status: str,
) -> str:
    """Build the text report printed to stdout and written to file."""
    L = problem["L"]
    ro0 = problem["ro0"]
    ro1 = problem["ro1"]
    ri0 = problem["ri0"]
    ri1 = problem["ri1"]
    weight_expr = problem["weight_expr"]

    finest = convergence[-1]
    uy_finest = finest["Uy_reference"]
    rz_finest = finest["Rz_reference"]

    lines: List[str] = []

    lines.append("")
    lines.append("INDEPENDENT CONTINUOUS BASELINE")
    lines.append("=" * 78)
    lines.append(f"YAML file                  : {yaml_file}")
    lines.append(f"L                          : {L:.12e}")
    lines.append(f"REF_TOL_PCT                : {REF_TOL_PCT:.12e}")
    lines.append("N_REF_SEQUENCE             : " + ", ".join(str(n) for n in N_REF_SEQUENCE))

    lines.append("")
    lines.append("Geometry")
    lines.append("-" * 78)
    lines.append(f"R_OUTER_BASE               : {ro0:.12e}")
    lines.append(f"R_OUTER_TOP                : {ro1:.12e}")
    lines.append(f"R_INNER_BASE               : {ri0:.12e}")
    lines.append(f"R_INNER_TOP                : {ri1:.12e}")

    lines.append("")
    lines.append("Weight law")
    lines.append("-" * 78)
    lines.append(str(weight_expr))

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
            f"{row['N_coarse']:>8d}  "
            f"{row['N_fine']:>7d}    "
            f"{row['dz_fine']:>12.6e}  "
            f"{row['Uy_err_est_pct']:>18.12e}  "
            f"{row['Rz_err_est_pct']:>18.12e}  "
            f"{row['max_err_est_pct']:>18.12e}  "
            f"{'yes' if row['accepted'] else 'no':>8}"
        )

    lines.append("")
    lines.append("SELECTED REFERENCE GRID")
    lines.append("=" * 78)
    lines.append(f"N_REF                      : {int(selected['N_REF'])}")
    lines.append(f"dz [m]                     : {selected['dz']:.12e}")
    lines.append(f"Selection status            : {status}")

    lines.append("")
    lines.append("REFERENCE RESULTS")
    lines.append("=" * 78)

    lines.append("")
    lines.append("CHECK 1 - TIP DISPLACEMENT Uy")
    lines.append("-" * 78)
    lines.append(f"Uy_force_component         : {selected['Uy_force_component']:.12e}")
    lines.append(f"Uy_uniform_component       : {selected['Uy_uniform_component']:.12e}")
    lines.append(f"Uy_tip_moment_component    : {selected['Uy_tip_moment_component']:.12e}")
    lines.append(f"Uy_reference               : {selected['Uy_reference']:.12e}")

    lines.append("")
    lines.append("CHECK 2 - TIP TORSIONAL ROTATION Rz")
    lines.append("-" * 78)
    lines.append(f"Rz_reference               : {selected['Rz_reference']:.12e} rad")

    lines.append("")
    lines.append("REFERENCE GRID VALUES")
    lines.append("=" * 78)
    lines.append("N_REF     dz [m]        Uy_reference       Rz_reference       selected")
    lines.append("-" * 82)

    selected_n_ref = int(selected["N_REF"])
    for row in convergence:
        selected_label = "yes" if int(row["N_REF"]) == selected_n_ref else "no"
        lines.append(
            f"{int(row['N_REF']):>5d}  "
            f"{row['dz']:>12.6e}  "
            f"{row['Uy_reference']:>18.12e}  "
            f"{row['Rz_reference']:>18.12e}  "
            f"{selected_label:>8}"
        )

    return "\n".join(lines)


def main() -> None:
    yaml_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_YAML

    yaml_stem = Path(yaml_file).stem
    output_dir = Path(f"baseline_output_{yaml_stem}")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "analytical_reference.txt"
    convergence_file = output_dir / "analytical_reference_convergence.csv"
    selection_file = output_dir / "analytical_reference_grid_selection.csv"

    problem = read_problem_data(yaml_file)

    convergence = [
        compute_reference(
            n_ref,
            problem["L"],
            problem["ro0"],
            problem["ro1"],
            problem["ri0"],
            problem["ri1"],
            problem["weight_fn"],
        )
        for n_ref in N_REF_SEQUENCE
    ]

    selection_rows, selected, status = build_grid_selection(convergence)
    selected_n_ref = int(selected["N_REF"])

    output_text = build_report(
        yaml_file=yaml_file,
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

    print()
    print(f"Baseline reference report: {report_file}")
    print(f"Reference convergence CSV : {convergence_file}")
    print(f"Reference grid selection CSV : {selection_file}")


if __name__ == "__main__":
    main()

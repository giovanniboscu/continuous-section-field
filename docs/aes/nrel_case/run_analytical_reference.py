"""
Independent continuous reference for the NREL tower validation cases.

Reviewer-oriented purpose
-------------------------
This script computes the reference quantities used to compare the finite-element
OpenSees validation model against an independent continuous calculation.

The script is intentionally case-specific:

1. It reads the endpoint geometry from a CSF YAML file.
2. It extracts the single YAML weight law only to identify which supported
   material law is being used.
3. It does not evaluate arbitrary YAML expressions. Instead, it maps the YAML
   law to one of two hardcoded Python functions:
      - constant NREL elastic modulus E = 210e9;
      - the degraded NREL E(z) law used in the validation case.
4. It computes two reference responses by direct numerical integration:
      - Uy: tip displacement contribution from the prescribed bending actions;
      - Rz: torsional rotation from the prescribed tip torque.

This file is therefore not a general CSF post-processor. It is a controlled,
case-specific baseline generator for the supported NREL validation examples.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import yaml


# Relative tolerance, expressed in percent, used to select a sufficiently fine
# Simpson grid by comparing coarser integrations against the finest one.
REF_TOL_PCT = 1.0e-10

# Candidate numbers of stations for the continuous reference integration.
# They are all odd because Simpson integration requires an odd number of points.
N_REF_SEQUENCE: Tuple[int, ...] = (251, 501, 1001, 2001, 4001, 8001)

# Poisson's ratio used to derive G from E through G = E / [2(1 + nu)].
NU = 0.3

# Loads used in the NREL validation reference calculation.
# FY_TIP produces a bending moment varying linearly along the tower.
FY_TIP = 1.2e6

# MX_TIP is treated as a constant bending moment along the tower.
MX_TIP = 8.0e6

# MZ_TIP is the torsional moment used for the torsional rotation reference.
MZ_TIP = 3.0e6

# WY_DIST is the distributed lateral load used in the bending reference.
WY_DIST = 8.0e3


@dataclass(frozen=True)
class ProblemData:
    """Input data needed by the analytical reference calculation.

    The dataclass is frozen to make the extracted problem definition immutable
    after reading the YAML file.
    """

    # Source YAML file used to define endpoint geometry and material-law label.
    yaml_file: Path

    # Axial coordinates of the two endpoint sections read from the YAML file.
    z0: float
    z1: float

    # Member length computed from the endpoint coordinates.
    L: float

    # Inner and outer radii at the base endpoint.
    ri0: float
    ro0: float

    # Inner and outer radii at the top endpoint.
    ri1: float
    ro1: float

    # Human-readable name of the selected material case.
    material_case: str

    # Function returning E(z, L) for the selected material case.
    E_fn: Callable[[float, float], float]


@dataclass(frozen=True)
class ReferenceResult:
    """Result of one continuous-reference integration grid."""

    # Number of integration stations used by Simpson integration.
    n_ref: int

    # Axial station spacing.
    dz: float

    # Reference tip displacement from the bending calculation.
    uy_reference: float

    # Reference torsional rotation from the torsion calculation.
    rz_reference: float


def parse_args() -> argparse.Namespace:
    """Read the command-line argument containing the CSF YAML path."""

    parser = argparse.ArgumentParser(
        description="Compute the independent Uy/Rz reference for the supported NREL tower cases."
    )

    # The script expects exactly one positional input: the YAML file to process.
    parser.add_argument("yaml", type=Path, help="CSF YAML input file.")
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file and return its parsed dictionary representation."""

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def polygon_radii(vertices: List[List[float]]) -> Tuple[float, float]:
    """Return the minimum and maximum radial distance of polygon vertices.

    For this NREL tower case the section is represented by circular/annular
    endpoint polygons. The smallest vertex radius is used as the inner radius;
    the largest vertex radius is used as the outer radius.
    """

    # Convert every vertex coordinate to float and compute its distance from
    # the origin in the section plane.
    radii = [math.hypot(float(v[0]), float(v[1])) for v in vertices]

    # A polygon without vertices cannot define a section radius.
    if not radii:
        raise ValueError("Polygon has no vertices.")

    # Return inner and outer radii inferred from the endpoint polygon.
    return min(radii), max(radii)


def nrel_constant_E(z: float, L: float) -> float:
    """Constant elastic modulus for the non-degraded NREL validation case."""

    # z and L are accepted to keep the same call signature as E(z, L) laws.
    return 210.0e9


def nrel_degraded_E(z: float, L: float) -> float:
    """Axially varying elastic modulus for the degraded NREL validation case.

    The law contains two Gaussian-shaped reductions along the tower axis and a
    lower bound of 0.84 times the nominal elastic modulus.
    """

    return 210.0e9 * max(
        0.84,
        1.0
        - 0.10 * math.exp(-((z - 0.33 * L) ** 2) / (2.0 * (0.03 * L) ** 2))
        - 0.14 * math.exp(-((z - 0.67 * L) ** 2) / (2.0 * (0.03 * L) ** 2)),
    )


def extract_single_weight_expression(csf: Dict[str, Any]) -> str:
    """Extract the only supported weight-law expression from the CSF YAML data.

    This reference script supports exactly one weight law. That restriction is
    deliberate because the analytical baseline is defined only for the NREL
    cases handled in this file.
    """

    # Read the YAML list of weight laws. Missing weight_laws is treated as an
    # empty list, which will fail the explicit length check below.
    weight_laws = csf.get("weight_laws", [])

    # The reference calculation is case-specific and expects one global law.
    if len(weight_laws) != 1:
        raise ValueError(f"Expected exactly one weight law. Found {len(weight_laws)}.")

    # Convert the stored law to string and remove leading/trailing whitespace.
    raw = str(weight_laws[0]).strip()

    # CSF weight laws may include a label before a colon. The analytical script
    # only needs the expression after the colon.
    if ":" in raw:
        raw = raw.split(":", 1)[1].strip()

    return raw


def normalize_expression(expr: str) -> str:
    """Normalize a material-law expression for simple string matching."""

    # Lowercase and remove whitespace/newlines so that equivalent formatting in
    # the YAML file does not prevent recognition of the supported laws.
    return str(expr).strip().lower().replace(" ", "").replace("\n", "")


def select_material_law(weight_expr: str) -> Tuple[str, Callable[[float, float], float]]:
    """Map the YAML weight expression to one supported hardcoded E(z) law.

    The function intentionally does not evaluate arbitrary expressions. It only
    recognizes the two validation laws supported by this reference script.
    """

    expr = normalize_expression(weight_expr)

    # First recognition path: the YAML expression is a numeric constant.
    try:
        value = float(expr)

        # Accept values numerically equal to 210e9 within an absolute tolerance
        # of 1.0 Pa, avoiding false rejection due to harmless formatting.
        if math.isclose(value, 210.0e9, rel_tol=0.0, abs_tol=1.0):
            return "NREL constant E = 210e9", nrel_constant_E
    except ValueError:
        # If the expression is not a single float, continue with the string-token
        # recognition path for the degraded law.
        pass

    # Tokens that identify the nominal modulus scale in the degraded expression.
    degraded_scale_tokens = ("210000000000", "210e9", "210.0e9", "2.1e11", "2.10e11")

    # Tokens that identify the specific degraded-law shape used by the NREL case.
    degraded_shape_tokens = ("0.84", "0.10", "0.14", "0.33*l", "0.67*l", "0.03*l", "exp")

    # The degraded law is selected only when one recognized modulus scale and all
    # expected shape tokens are present in the normalized YAML expression.
    if any(t in expr for t in degraded_scale_tokens) and all(t in expr for t in degraded_shape_tokens):
        return "NREL degraded E(z)", nrel_degraded_E

    # Any other material law is outside the scope of this case-specific reference.
    raise ValueError(f"Unsupported NREL material law: {weight_expr}")


def read_problem_data(yaml_file: Path) -> ProblemData:
    """Read the CSF YAML file and assemble the data required by the baseline."""

    data = load_yaml(yaml_file)
    csf = data["CSF"]

    # Select the analytical E(z) function corresponding to the YAML weight law.
    material_case, E_fn = select_material_law(extract_single_weight_expression(csf))

    # This reference expects two endpoint sections named S0 and S1.
    s0 = csf["sections"]["S0"]
    s1 = csf["sections"]["S1"]

    # Read endpoint coordinates and derive the absolute member length.
    z0 = float(s0["z"])
    z1 = float(s1["z"])
    L = abs(z1 - z0)

    # A non-positive length would invalidate all following interpolation and
    # integration steps.
    if L <= 0.0:
        raise ValueError(f"Invalid member length from YAML endpoints: z0={z0}, z1={z1}")

    # The NREL YAML case is expected to contain one annular polygon per endpoint.
    # next(iter(...)) takes that polygon without depending on its display name.
    poly0 = next(iter(s0["polygons"].values()))
    poly1 = next(iter(s1["polygons"].values()))

    # Infer inner and outer endpoint radii from the endpoint polygon vertices.
    ri0, ro0 = polygon_radii(poly0["vertices"])
    ri1, ro1 = polygon_radii(poly1["vertices"])

    # Return an immutable object that contains all data needed downstream.
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


def simpson(y: np.ndarray, x: np.ndarray) -> float:
    """Integrate y(x) using composite Simpson's rule on a uniform grid."""

    # Simpson integration requires at least three points.
    if len(x) < 3:
        raise ValueError("Need at least 3 points.")

    # Composite Simpson integration requires an odd number of grid points.
    if len(x) % 2 == 0:
        raise ValueError("Need odd number of points.")

    # Uniform station spacing. The caller supplies uniform grids through
    # np.linspace, so the formula uses the first and last coordinates.
    h = (x[-1] - x[0]) / (len(x) - 1)

    # Composite Simpson formula:
    # h/3 * [y0 + yn + 4 * odd-index terms + 2 * interior even-index terms].
    return float(h / 3.0 * (y[0] + y[-1] + 4.0 * np.sum(y[1:-1:2]) + 2.0 * np.sum(y[2:-2:2])))


def compute_reference(n_ref: int, problem: ProblemData) -> ReferenceResult:
    """Compute Uy and Rz for one selected integration grid."""

    # Guard the Simpson requirement at the public function boundary.
    if n_ref % 2 == 0:
        raise ValueError("n_ref must be odd for Simpson integration.")

    L = problem.L

    # Continuous axial grid from the base coordinate 0 to the member length L.
    z = np.linspace(0.0, L, n_ref)

    # Non-dimensional axial coordinate used for linear interpolation between
    # endpoint radii.
    eta = z / L

    # Linear interpolation of outer and inner radii between endpoint sections.
    r_outer = problem.ro0 + (problem.ro1 - problem.ro0) * eta
    r_inner = problem.ri0 + (problem.ri1 - problem.ri0) * eta

    # Evaluate the selected elastic modulus law at every integration station.
    E = np.array([problem.E_fn(float(zi), L) for zi in z], dtype=float)

    # Convert E to G using the fixed Poisson's ratio defined above.
    G = E / (2.0 * (1.0 + NU))

    # Second moment of area of an annulus about a centroidal bending axis.
    I = math.pi / 4.0 * (r_outer**4 - r_inner**4)

    # Polar second moment of area of the annulus used for the torsion reference.
    J = 0.5 * math.pi * (r_outer**4 - r_inner**4)

    # Unit-load bending moment shape associated with the tip displacement Uy.
    m_unit = L - z

    # Bending moment contribution from the tip lateral force.
    M_fy = FY_TIP * (L - z)

    # Bending moment contribution from the distributed lateral load.
    M_wy = 0.5 * WY_DIST * (L - z) ** 2

    # Constant bending moment contribution from the prescribed tip moment MX.
    M_mx = MX_TIP * np.ones_like(z)

    # Tip displacement reference from virtual-work integration. The signs follow
    # the sign convention used by the validation script.
    uy_reference = (
        simpson(M_fy * m_unit / (E * I), z)
        - simpson(M_wy * m_unit / (E * I), z)
        - simpson(M_mx * m_unit / (E * I), z)
    )

    # Torsional rotation reference from integral of torque over GJ.
    rz_reference = MZ_TIP * simpson(1.0 / (G * J), z)

    # Store both responses together with the grid resolution used to compute them.
    return ReferenceResult(
        n_ref=int(n_ref),
        dz=float(L / (n_ref - 1)),
        uy_reference=float(uy_reference),
        rz_reference=float(rz_reference),
    )


def relative_error_pct(value: float, reference: float) -> float:
    """Return absolute relative error in percent."""

    return abs(100.0 * (value - reference) / reference)


def select_reference_grid(convergence: List[ReferenceResult]) -> Tuple[ReferenceResult, str, float]:
    """Select the first grid that matches the finest grid within tolerance."""

    # The last item is treated as the finest available numerical reference.
    finest = convergence[-1]

    # Default to the finest grid unless a coarser grid satisfies the tolerance.
    selected = finest
    status = "tolerance not reached"
    selected_max_err = 0.0

    # Compare all coarser integrations against the finest one.
    for candidate in convergence[:-1]:
        uy_err = relative_error_pct(candidate.uy_reference, finest.uy_reference)
        rz_err = relative_error_pct(candidate.rz_reference, finest.rz_reference)
        max_err = max(uy_err, rz_err)

        # Select the first grid that satisfies both Uy and Rz through their
        # maximum relative error.
        if max_err <= REF_TOL_PCT:
            selected = candidate
            status = "tolerance reached"
            selected_max_err = max_err
            break

    # If no coarser grid satisfies the tolerance, the finest grid is selected.
    # In that case the error against itself is reported as zero.
    if selected is finest:
        selected_max_err = 0.0

    return selected, status, selected_max_err


def build_report(problem: ProblemData, selected: ReferenceResult, status: str, max_err_pct: float) -> str:
    """Build the text report written to disk and printed to the terminal."""

    # The report records the input geometry, selected material case, selected
    # integration grid, convergence status, and final reference values.
    lines = [
        "",
        "INDEPENDENT CONTINUOUS BASELINE",
        "==============================================================================",
        f"YAML file                  : {problem.yaml_file}",
        f"Material case              : {problem.material_case}",
        f"L                          : {problem.L:.12e}",
        f"R_OUTER_BASE               : {problem.ro0:.12e}",
        f"R_OUTER_TOP                : {problem.ro1:.12e}",
        f"R_INNER_BASE               : {problem.ri0:.12e}",
        f"R_INNER_TOP                : {problem.ri1:.12e}",
        f"N_REF                      : {selected.n_ref:d}",
        f"dz [m]                     : {selected.dz:.12e}",
        f"Selection status           : {status}",
        f"Max err. vs finest [%]     : {max_err_pct:.12e}",
        "",
        "REFERENCE RESULTS",
        "==============================================================================",
        f"Uy_reference               : {selected.uy_reference:.12e}",
        f"Rz_reference               : {selected.rz_reference:.12e} rad",
    ]
    return "\n".join(lines)


def run_baseline(yaml_file: Path) -> Path:
    """Run the complete baseline workflow for one YAML input file."""

    # Create one output directory per YAML stem, keeping reports separated by case.
    output_dir = Path(f"baseline_output_{yaml_file.stem}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read geometry and select the supported material law.
    problem = read_problem_data(yaml_file)

    # Compute the reference response on every candidate integration grid.
    convergence = [compute_reference(n_ref, problem) for n_ref in N_REF_SEQUENCE]

    # Select the coarsest grid that agrees with the finest grid within tolerance.
    selected, status, max_err_pct = select_reference_grid(convergence)

    # Build the report text from the selected reference result.
    output_text = build_report(problem, selected, status, max_err_pct)

    # Save the report next to the case-specific output directory.
    report_file = output_dir / "analytical_reference.txt"
    report_file.write_text(output_text + "\n", encoding="utf-8")

    # Echo the same report to the terminal for immediate inspection.
    print(output_text)
    print()
    print(f"Baseline reference report: {report_file}")

    return report_file


def main() -> None:
    """Command-line entry point."""

    # Parse the YAML path from the command line and run the baseline workflow.
    args = parse_args()
    run_baseline(args.yaml)


# Standard Python guard: execute main() only when this file is run as a script,
# not when it is imported as a module.
if __name__ == "__main__":
    main()

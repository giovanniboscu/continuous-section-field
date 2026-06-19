"""
Independent continuous reference for the NREL tower validation cases.

Reviewer-oriented purpose
-------------------------
This script computes the reference quantities used to compare the finite-element
OpenSees validation model against an independent continuous calculation.

The script is intentionally case-specific:

1. The NREL endpoint dimensions are fixed directly in this file.
2. The only external input is the material-case selector:
      - constant;
      - degraded.
3. No CSF YAML file is read by this analytical reference.
4. No arbitrary material expression is parsed or evaluated.
5. The script computes two reference responses by direct numerical integration:
      - Uy: tip displacement contribution from the prescribed bending actions;
      - Rz: torsional rotation from the prescribed tip torque.

This file is therefore not a CSF post-processor. It is a controlled,
case-specific baseline generator for the NREL validation examples.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np


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
class EndpointDimensions:
    """Fixed endpoint dimensions for one NREL tower section."""

    label: str
    z: float
    outer_diameter_x: float
    outer_diameter_y: float
    outer_radius: float
    wall_thickness: float
    inner_radius: float
    inner_diameter: float


# Fixed endpoint dimensions used by the analytical reference.
BASE_SECTION = EndpointDimensions(
    label="S0",
    z=0.0,
    outer_diameter_x=6.0,
    outer_diameter_y=6.0,
    outer_radius=3.0,
    wall_thickness=0.0351,
    inner_radius=2.9649,
    inner_diameter=5.9298,
)

TOP_SECTION = EndpointDimensions(
    label="S1",
    z=87.6,
    outer_diameter_x=3.87,
    outer_diameter_y=3.87,
    outer_radius=1.935,
    wall_thickness=0.0247,
    inner_radius=1.9103,
    inner_diameter=3.8206,
)


@dataclass(frozen=True)
class ProblemData:
    """Input data needed by the analytical reference calculation."""

    # External material-case key selected from the command line.
    case_key: str

    # Human-readable name of the selected material case.
    material_case: str

    # Function returning E(z, L) for the selected material case.
    E_fn: Callable[[float, float], float]

    # Fixed endpoint dimensions.
    base: EndpointDimensions
    top: EndpointDimensions

    # Member length computed from the fixed endpoint coordinates.
    L: float


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


@dataclass(frozen=True)
class MaterialCase:
    """Supported NREL material case."""

    label: str
    E_fn: Callable[[float, float], float]


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


MATERIAL_CASES: Dict[str, MaterialCase] = {
    "constant": MaterialCase(
        label="NREL constant E = 210e9",
        E_fn=nrel_constant_E,
    ),
    "degraded": MaterialCase(
        label="NREL degraded E(z)",
        E_fn=nrel_degraded_E,
    ),
}


def parse_args() -> argparse.Namespace:
    """Read the material-case selector from the command line."""

    parser = argparse.ArgumentParser(
        description="Compute the independent Uy/Rz reference for the supported NREL tower cases."
    )

    # The script expects exactly one positional input: the material case.
    parser.add_argument(
        "case",
        choices=tuple(MATERIAL_CASES.keys()),
        help="Material case to compute: constant or degraded.",
    )
    return parser.parse_args()


def validate_endpoint(section: EndpointDimensions) -> None:
    """Check that the fixed endpoint dimensions are internally consistent."""

    # The NREL case used here has equal outer diameters in x and y.
    if not math.isclose(section.outer_diameter_x, section.outer_diameter_y, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError(f"Endpoint {section.label} has unequal outer diameters.")

    # Check the relation between outer diameter and outer radius.
    if not math.isclose(0.5 * section.outer_diameter_x, section.outer_radius, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError(f"Endpoint {section.label} has inconsistent outer diameter and radius.")

    # Check the relation between wall thickness and inner radius.
    if not math.isclose(section.outer_radius - section.wall_thickness, section.inner_radius, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError(f"Endpoint {section.label} has inconsistent wall thickness and inner radius.")

    # Check the relation between inner radius and inner diameter.
    if not math.isclose(2.0 * section.inner_radius, section.inner_diameter, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError(f"Endpoint {section.label} has inconsistent inner radius and diameter.")


def build_problem_data(case_key: str) -> ProblemData:
    """Build the fixed NREL problem data for the selected material case."""

    validate_endpoint(BASE_SECTION)
    validate_endpoint(TOP_SECTION)

    material_case = MATERIAL_CASES[case_key]

    # Compute the member length from the fixed endpoint coordinates.
    L = abs(TOP_SECTION.z - BASE_SECTION.z)

    # A non-positive length would invalidate all following interpolation and
    # integration steps.
    if L <= 0.0:
        raise ValueError(f"Invalid member length from endpoint coordinates: L={L}")

    # Return an immutable object that contains all data needed downstream.
    return ProblemData(
        case_key=case_key,
        material_case=material_case.label,
        E_fn=material_case.E_fn,
        base=BASE_SECTION,
        top=TOP_SECTION,
        L=L,
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
    r_outer = problem.base.outer_radius + (problem.top.outer_radius - problem.base.outer_radius) * eta
    r_inner = problem.base.inner_radius + (problem.top.inner_radius - problem.base.inner_radius) * eta

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


def format_endpoint(section: EndpointDimensions) -> List[str]:
    """Build report lines for one fixed endpoint section."""

    return [
        f"{section.label} z [m]                 : {section.z:.12e}",
        f"{section.label} outer diameter x [m]  : {section.outer_diameter_x:.12e}",
        f"{section.label} outer diameter y [m]  : {section.outer_diameter_y:.12e}",
        f"{section.label} outer radius [m]      : {section.outer_radius:.12e}",
        f"{section.label} wall thickness [m]    : {section.wall_thickness:.12e}",
        f"{section.label} inner radius [m]      : {section.inner_radius:.12e}",
        f"{section.label} inner diameter [m]    : {section.inner_diameter:.12e}",
    ]


def build_report(problem: ProblemData, selected: ReferenceResult, status: str, max_err_pct: float) -> str:
    """Build the text report written to disk and printed to the terminal."""

    # The report records the fixed dimensions, selected material case, selected
    # integration grid, convergence status, and final reference values.
    lines = [
        "",
        "INDEPENDENT CONTINUOUS BASELINE",
        "==============================================================================",
        f"Case selector              : {problem.case_key}",
        f"Material case              : {problem.material_case}",
        f"L [m]                      : {problem.L:.12e}",
        "",
        "FIXED ENDPOINT DIMENSIONS",
        "==============================================================================",
        *format_endpoint(problem.base),
        "",
        *format_endpoint(problem.top),
        "",
        "REFERENCE INTEGRATION",
        "==============================================================================",
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


def run_baseline(case_key: str) -> Path:
    """Run the complete baseline workflow for one material case."""

    # Create one output directory per material case, keeping reports separated.
    output_dir = Path(f"baseline_output_nrel_{case_key}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the fixed NREL problem definition for the selected material case.
    problem = build_problem_data(case_key)

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

    # Parse the material-case selector and run the baseline workflow.
    args = parse_args()
    run_baseline(args.case)


# Standard Python guard: execute main() only when this file is run as a script,
# not when it is imported as a module.
if __name__ == "__main__":
    main()

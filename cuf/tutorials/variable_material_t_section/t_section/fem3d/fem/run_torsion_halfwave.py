#!/usr/bin/env python3
# Version: T-section non-prismatic FEM3D torsional line-pair half-wave v1 - 2026-09-04
"""
FEM3D reference for the CSF-CUF ``torsion_halfwave`` problem.

This wrapper is the sinusoidal counterpart of the existing FEM3D
``torsion_uniform`` reference. It deliberately preserves exactly the same:

- CSF geometry and moving load vertices;
- opposite global-z force pair;
- longitudinal load measure dx;
- structured 3D mesh;
- material interpolation;
- end constraints;
- pointwise axial anchor u_x(x_start, 0, 0) = 0;
- solver and output routines.

The only mechanical change is the longitudinal intensity law

    + amplitude * sin(pi * (x - x0) / L)
    - amplitude * sin(pi * (x - x0) / L).

The half-wave is evaluated at the physical longitudinal Gauss coordinate x.
The consistent nodal line load is integrated with dx, exactly matching the
CUF generalized-load definition. No trajectory arc-length Jacobian is used.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

import common_t_fem3d as common


HALFWAVE_TYPE = "torsion_halfwave"


def _finite_float(value: Any, *, path: str) -> float:
    """Convert one YAML scalar to a finite float with a precise error path."""

    if isinstance(value, bool):
        raise TypeError(f"{path} must be a finite number, got {value!r}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{path} must be a finite number, got {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{path} must be finite, got {value!r}")
    return result


def _parse_torsion_halfwave_problem(problem: dict) -> dict:
    """Parse exactly the same YAML options accepted by the CUF adapter."""

    allowed = {"type", "amplitude"}
    unknown = sorted(str(key) for key in problem if key not in allowed)
    if unknown:
        raise ValueError(
            "torsion_halfwave contains unsupported key(s): " + ", ".join(unknown)
        )

    amplitude = _finite_float(
        problem.get("amplitude", 1.0),
        path="problem.amplitude",
    )
    return {"amplitude": amplitude}


def read_case(case_path: str | Path) -> dict:
    """Read one FEM3D torsion half-wave case using the reference infrastructure."""

    case_path = Path(case_path).resolve()
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    problem, problem_path, model_path = common._problem_from_case(case_path, case)

    problem_type = str(problem.get("type", ""))
    if problem_type != HALFWAVE_TYPE:
        raise ValueError(
            f"expected problem.type={HALFWAVE_TYPE!r}, got {problem_type!r}"
        )
    problem_data = _parse_torsion_halfwave_problem(problem)

    model = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    csf = model["CSF"]
    sections = sorted(csf["sections"].items(), key=lambda kv: float(kv[1]["z"]))
    if len(sections) != 2:
        raise ValueError("this FEM3D reference expects exactly two CSF sections S0/S1")

    s0 = common._section_data(sections[0][1])
    s1 = common._section_data(sections[1][1])
    if not s1["x"] > s0["x"]:
        raise ValueError("S1 must lie after S0 along the beam axis")

    if set(s0["polygons"]) != set(s1["polygons"]):
        raise ValueError("S0/S1 must contain the same named CSF polygons")
    for name in s0["polygons"]:
        if len(s0["polygons"][name]["vertices"]) != len(
            s1["polygons"][name]["vertices"]
        ):
            raise ValueError(
                f"polygon {name!r} must preserve its CSF vertex topology between S0/S1"
            )

    mesh = case["mesh"]
    analysis = case.get("analysis", {})
    output = case.get("output", {})
    element_type = str(analysis.get("element", "stdBrick"))
    if element_type not in common.SUPPORTED_ELEMENTS:
        raise ValueError(
            f"element must be one of {sorted(common.SUPPORTED_ELEMENTS)}"
        )

    result = {
        "case_path": case_path,
        "model_path": model_path,
        "problem_path": problem_path,
        "case_name": str(case.get("case", {}).get("name", case_path.stem)),
        "problem_type": problem_type,
        "s0": s0,
        "s1": s1,
        "x0": s0["x"],
        "x1": s1["x"],
        "L": s1["x"] - s0["x"],
        "nu": common._parse_nu(csf),
        "nx": int(mesh["longitudinal_divisions"]),
        "web_ny": int(mesh["web_width_divisions"]),
        "web_nz": int(mesh["web_height_divisions"]),
        "overhang_ny": int(mesh["flange_overhang_divisions"]),
        "flange_nz": int(mesh["flange_thickness_divisions"]),
        "load_gauss_order": int(mesh.get("load_gauss_order", 4)),
        "element_type": element_type,
        "system": str(analysis.get("system", "SparseGeneral")),
        "output_dir": common._resolve(
            case_path.parent,
            output.get("directory", f"../output/{case_path.stem}"),
        ),
        "stations": tuple(
            float(value)
            for value in case.get("sampling", {}).get(
                "stations", [0.0, 0.25, 0.5, 0.75, 1.0]
            )
        ),
    }
    result.update(problem_data)
    return result


def torsion_halfwave_loads(
    d: dict,
    mesh: common.TSectionMesh,
) -> dict[int, np.ndarray]:
    """Assemble the CUF ``torsion_halfwave`` pair with longitudinal measure dx.

    At every section the positive point is the leftmost CSF vertex on the
    maximum-z boundary and the negative point is the rightmost CSF vertex on
    the minimum-z boundary, exactly as in the CUF adapter.

    The two global-z line-load intensities are

        + amplitude * sin(pi * (x - x0) / L)
        - amplitude * sin(pi * (x - x0) / L).

    The load is defined per unit global longitudinal coordinate x, so the
    integration Jacobian is dx/dr = (xb-xa)/2. The actual inclined trajectory
    length is intentionally NOT used; adding it would define a different
    physical problem from the CUF model.
    """

    points, weights = np.polynomial.legendre.leggauss(d["load_gauss_order"])
    loads: dict[int, np.ndarray] = {}

    for ix in range(d["nx"]):
        xa = d["x0"] + d["L"] * ix / d["nx"]
        xb = d["x0"] + d["L"] * (ix + 1) / d["nx"]

        plus_a, minus_a = common._torsion_points(d, xa)
        plus_b, minus_b = common._torsion_points(d, xb)
        paths = (
            (plus_a, plus_b, +1.0),
            (minus_a, minus_b, -1.0),
        )

        for point_a, point_b, sign in paths:
            tags = [
                mesh.existing_node(ix, point_a[0], point_a[1]),
                mesh.existing_node(ix + 1, point_b[0], point_b[1]),
            ]

            # Consistent two-node line load. Only dx enters the measure.
            local = np.zeros(2, dtype=float)
            jacx = 0.5 * (xb - xa)

            for r, wr in zip(points, weights):
                r = float(r)
                N = common._l2(r)
                x_gauss = float(N @ np.asarray([xa, xb], dtype=float))
                phase = math.sin(math.pi * (x_gauss - d["x0"]) / d["L"])
                qz = sign * float(d["amplitude"]) * phase
                local += float(wr) * N * qz * jacx

            for tag, fz in zip(tags, local):
                common._add_load(loads, tag, (0.0, 0.0, float(fz)))

    return loads


def _analytical_torsional_resultant(d: dict) -> float:
    """Return the exact continuum Mx for the affine CSF trajectories.

    CSF interpolates homologous section vertices affinely along x. Therefore
    Delta-y(x) = y_plus(x) - y_minus(x) is affine and

        integral_0^L Delta-y(x) sin(pi*x/L) dx
            = L * (Delta-y(0) + Delta-y(L)) / pi.
    """

    plus_0, minus_0 = common._torsion_points(d, d["x0"])
    plus_1, minus_1 = common._torsion_points(d, d["x1"])
    delta_y_0 = float(plus_0[0] - minus_0[0])
    delta_y_1 = float(plus_1[0] - minus_1[0])
    return (
        float(d["amplitude"])
        * float(d["L"])
        * (delta_y_0 + delta_y_1)
        / math.pi
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "FEM3D reference for the CSF-CUF torsional line-pair half-wave case"
        )
    )
    parser.add_argument(
        "case",
        nargs="?",
        default="../cases/torsion_halfwave_model2.yaml",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--element",
        choices=("stdBrick", "SSPbrick"),
        default=None,
    )
    args = parser.parse_args()

    d = read_case(args.case)
    if args.element is not None:
        d["element_type"] = args.element

    mesh = common.TSectionMesh(d)
    loads = torsion_halfwave_loads(d, mesh)
    common.print_diagnostics(d, mesh, loads)

    force, moment = common.resultants(mesh.nodes, loads)
    expected_mx = _analytical_torsional_resultant(d)

    print(f"amplitude : {d['amplitude']:+.12e}")
    print("law       : +/- amplitude * sin(pi * (x - x0) / L)")
    print("direction : opposite global-z pair")
    print("measure   : dx (no trajectory-length factor)")
    print(f"Mx exact  : {expected_mx:+.12e}")
    print(f"Mx FEM    : {float(moment[0]):+.12e}")
    print(f"Mx error  : {float(moment[0] - expected_mx):+.12e}")
    print(f"net Fz    : {float(force[2]):+.12e}")

    if args.dry_run:
        print("dry-run   : mesh/load construction OK; solve not executed")
        return

    u, reactions, anchor = common.solve(d, mesh, loads)
    common.write_outputs(d, mesh, loads, u, reactions)
    print(f"anchor ux : node {anchor} at {mesh.nodes[anchor]}")
    print(f"output    : {d['output_dir']}")


if __name__ == "__main__":
    main()

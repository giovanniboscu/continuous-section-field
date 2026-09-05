#!/usr/bin/env python3
# Version: T-section non-prismatic FEM3D physical-surface half-wave bending v2 - 2026-09-05
"""
FEM3D reference for the CSF-CUF ``surface_halfwave`` problem.

This wrapper is the sinusoidal counterpart of the existing FEM3D
``uniform_surface_load`` bending reference.  It deliberately reuses the same:

- CSF geometry and physical surface selector;
- structured 3D mesh;
- real isoparametric surface Jacobian;
- material state queried from the CSF API;
- end constraints;
- pointwise axial anchor u_x(x_start, 0, 0) = 0;
- solver and output routines.

The only mechanical change is the traction law

    t_global(x) = (0, 0, amplitude * sin(pi * (x - x0) / L)).

The half-wave is evaluated at the physical x coordinate of each surface Gauss
point before the consistent nodal load is assembled.  Therefore FEM3D and CUF
represent the same physical traction on the same real surface.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

import common_t_fem3d as common


HALFWAVE_TYPE = "surface_halfwave"


def _finite_float(value: Any, *, path: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{path} must be a finite number, got {value!r}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{path} must be a finite number, got {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{path} must be finite, got {value!r}")
    return result


def _parse_surface_halfwave_problem(problem: dict) -> dict:
    """Parse exactly the same problem interface used by the CUF adapter."""

    allowed = {"type", "surface", "amplitude"}
    unknown = sorted(str(key) for key in problem if key not in allowed)
    if unknown:
        raise ValueError(
            "surface_halfwave contains unsupported key(s): "
            + ", ".join(unknown)
        )

    surface = problem.get("surface")
    if not isinstance(surface, dict):
        raise TypeError("problem.surface must be a YAML mapping")

    surface_allowed = {"polygon_name", "edge_start_point_id"}
    unknown = sorted(str(key) for key in surface if key not in surface_allowed)
    if unknown:
        raise ValueError(
            "problem.surface contains unsupported key(s): "
            + ", ".join(unknown)
        )

    if "polygon_name" not in surface or "edge_start_point_id" not in surface:
        raise ValueError(
            "problem.surface requires polygon_name and edge_start_point_id"
        )

    polygon_name = str(surface["polygon_name"]).strip()
    if not polygon_name:
        raise ValueError("problem.surface.polygon_name must not be empty")

    edge_id = surface["edge_start_point_id"]
    if isinstance(edge_id, bool) or not isinstance(edge_id, int):
        raise TypeError("problem.surface.edge_start_point_id must be an integer")
    if edge_id < 0:
        raise ValueError("problem.surface.edge_start_point_id must be >= 0")

    if "amplitude" not in problem:
        raise ValueError("problem.amplitude is required")
    amplitude = _finite_float(problem["amplitude"], path="problem.amplitude")

    return {
        "surface_polygon_name": polygon_name,
        "surface_edge_start_point_id": int(edge_id),
        "amplitude": amplitude,
    }


def read_case(case_path: str | Path) -> dict:
    """Read one FEM3D bending half-wave case using the CSF API-backed reference."""

    case_path = Path(case_path).resolve()
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    problem, problem_path, model_path = common._problem_from_case(case_path, case)

    problem_type = str(problem.get("type", ""))
    if problem_type != HALFWAVE_TYPE:
        raise ValueError(
            f"expected problem.type={HALFWAVE_TYPE!r}, got {problem_type!r}"
        )
    problem_data = _parse_surface_halfwave_problem(problem)

    result = common._base_case_data(
        case_path=case_path,
        case=case,
        model_path=model_path,
        problem_path=problem_path,
        problem_type=problem_type,
    )
    return common._finish_case_data(result, problem_data)


def bending_halfwave_loads(
    d: dict,
    mesh: common.TSectionMesh,
) -> dict[int, np.ndarray]:
    """Assemble the CUF ``surface_halfwave`` traction on the real FEM surface.

    For each physical Q4 surface patch, the same real 3D isoparametric Jacobian
    used by the uniform FEM3D reference is retained.  At every Gauss point the
    current physical x coordinate is evaluated from the Q4 interpolation and
    the global-z traction is

        amplitude * sin(pi * (x - x0) / L).

    No local normal/tangential decomposition and no projected-area convention
    are introduced.
    """

    points, weights = np.polynomial.legendre.leggauss(d["load_gauss_order"])
    loads: dict[int, np.ndarray] = {}

    for ix in range(d["nx"]):
        xa = d["x0"] + d["L"] * ix / d["nx"]
        xb = d["x0"] + d["L"] * (ix + 1) / d["nx"]

        edge_a = common._selected_edge(d, xa)
        edge_b = common._selected_edge(d, xb)
        nodes_a = common._nodes_on_section_edge(mesh, ix, *edge_a)
        nodes_b = common._nodes_on_section_edge(mesh, ix + 1, *edge_b)

        if len(nodes_a) != len(nodes_b):
            raise ValueError(
                "selected surface edge has incompatible FEM subdivisions "
                f"between planes {ix} and {ix + 1}"
            )

        for (ta, _), (tb, _) in zip(nodes_a, nodes_b):
            if not math.isclose(ta, tb, rel_tol=0.0, abs_tol=1.0e-10):
                raise ValueError(
                    "selected surface edge uses non-homologous FEM subdivisions "
                    f"between planes {ix} and {ix + 1}"
                )

        for j in range(len(nodes_a) - 1):
            tags = [
                nodes_a[j][1],
                nodes_b[j][1],
                nodes_b[j + 1][1],
                nodes_a[j + 1][1],
            ]
            xyz = np.asarray([mesh.nodes[tag] for tag in tags], dtype=float)
            local = np.zeros((4, 3), dtype=float)

            for r, wr in zip(points, weights):
                for s, ws in zip(points, weights):
                    r = float(r)
                    s = float(s)
                    N = common._q4(r, s)
                    dndr, dnds = common._q4_derivatives(r, s)

                    tangent_r = dndr @ xyz
                    tangent_s = dnds @ xyz
                    jacobian = float(np.linalg.norm(np.cross(tangent_r, tangent_s)))
                    if not jacobian > 0.0:
                        raise ValueError("degenerate loaded FEM surface patch")

                    # Physical Gauss-point coordinate on the real surface.
                    x_gauss = float(N @ xyz[:, 0])
                    phase = math.sin(
                        math.pi * (x_gauss - d["x0"]) / d["L"]
                    )
                    traction_z = float(d["amplitude"]) * phase

                    local[:, 2] += (
                        float(wr)
                        * float(ws)
                        * jacobian
                        * N
                        * traction_z
                    )

            for tag, force in zip(tags, local):
                common._add_load(loads, tag, force)

    return loads


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "FEM3D reference for the CSF-CUF physical-surface half-wave bending case"
        )
    )
    parser.add_argument(
        "case",
        nargs="?",
        default="cases/bending_halfwave_model2.yaml",
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
    loads = bending_halfwave_loads(d, mesh)
    common.print_diagnostics(d, mesh, loads)

    print(f"amplitude : {d['amplitude']:+.12e}")
    print("law       : sin(pi * (x - x0) / L)")
    print("direction : global z only")
    print("measure   : real FEM surface Jacobian")

    if args.dry_run:
        print("dry-run   : mesh/load construction OK; solve not executed")
        return

    u, reactions, anchor = common.solve(d, mesh, loads)
    common.write_outputs(d, mesh, loads, u, reactions)
    print(f"anchor ux : node {anchor} at {mesh.nodes[anchor]}")
    print(f"output    : {d['output_dir']}")


if __name__ == "__main__":
    main()

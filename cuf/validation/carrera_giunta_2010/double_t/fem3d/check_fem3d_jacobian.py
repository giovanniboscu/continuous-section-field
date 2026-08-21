from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import numpy as np
import yaml

from csf_fem3d import build_mesh, read_csf_field


NATURAL_NODE_SIGNS = np.asarray(
    [
        [-1.0, -1.0, -1.0],
        [+1.0, -1.0, -1.0],
        [+1.0, +1.0, -1.0],
        [-1.0, +1.0, -1.0],
        [-1.0, -1.0, +1.0],
        [+1.0, -1.0, +1.0],
        [+1.0, +1.0, +1.0],
        [-1.0, +1.0, +1.0],
    ],
    dtype=float,
)


def load_case(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("case YAML must contain a mapping")
    return data


def resolve_relative(base_file: Path, value: str) -> Path:
    return (base_file.parent / value).resolve()


def shape_derivatives(r: float, s: float, t: float) -> np.ndarray:
    """Return dN/d(r,s,t) for the standard 8-node trilinear brick."""
    ri = NATURAL_NODE_SIGNS[:, 0]
    si = NATURAL_NODE_SIGNS[:, 1]
    ti = NATURAL_NODE_SIGNS[:, 2]

    dndr = 0.125 * ri * (1.0 + si * s) * (1.0 + ti * t)
    dnds = 0.125 * si * (1.0 + ri * r) * (1.0 + ti * t)
    dndt = 0.125 * ti * (1.0 + ri * r) * (1.0 + si * s)

    return np.column_stack((dndr, dnds, dndt))


def jacobian_det(coords: np.ndarray, r: float, s: float, t: float) -> float:
    dndxi = shape_derivatives(r, s, t)
    jacobian = coords.T @ dndxi
    return float(np.linalg.det(jacobian))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check the geometric Jacobian determinant of every CSF-FEM3D "
            "stdBrick at the eight 2x2x2 Gauss integration points."
        )
    )
    parser.add_argument("case_yaml", type=Path)
    args = parser.parse_args()

    case_path = args.case_yaml.resolve()
    case = load_case(case_path)
    model_path = resolve_relative(case_path, case["model"]["csf_yaml"])

    field = read_csf_field(model_path)
    mesh = build_mesh(field, case["mesh"])

    g = 1.0 / np.sqrt(3.0)
    gauss_points = list(product((-g, +g), repeat=3))

    min_det = np.inf
    max_det = -np.inf
    nonpositive = 0
    total_points = 0
    min_record = None
    min_volume = np.inf
    min_volume_record = None

    for brick in mesh.bricks:
        coords = np.asarray(
            [mesh.nodes[tag] for tag in brick.node_tags],
            dtype=float,
        )

        dets = []
        for r, s, t in gauss_points:
            det_j = jacobian_det(coords, r, s, t)
            dets.append(det_j)
            total_points += 1

            if det_j <= 0.0:
                nonpositive += 1

            if det_j < min_det:
                min_det = det_j
                centroid = coords.mean(axis=0)
                min_record = (
                    brick.tag,
                    brick.role,
                    tuple(float(v) for v in centroid),
                    (float(r), float(s), float(t)),
                    tuple(int(v) for v in brick.node_tags),
                )

            if det_j > max_det:
                max_det = det_j

        # For 2x2x2 Gauss integration all weights are 1.
        volume = float(sum(dets))
        if volume < min_volume:
            min_volume = volume
            centroid = coords.mean(axis=0)
            min_volume_record = (
                brick.tag,
                brick.role,
                tuple(float(v) for v in centroid),
            )

    if min_record is None or min_volume_record is None:
        raise RuntimeError("mesh contains no brick elements")

    min_tag, min_role, min_centroid, min_gp, min_nodes = min_record
    vol_tag, vol_role, vol_centroid = min_volume_record

    print("FEM3D Jacobian check")
    print("====================")
    print(f"case                 : {case_path}")
    print(f"CSF model            : {model_path}")
    print(f"nodes                : {len(mesh.nodes)}")
    print(f"stdBrick elements    : {len(mesh.bricks)}")
    print(f"Gauss points checked : {total_points}")
    print()
    print(f"min(detJ)            : {min_det:.12e}")
    print(f"max(detJ)            : {max_det:.12e}")
    print(f"non-positive detJ    : {nonpositive}")
    print(f"min element volume   : {min_volume:.12e}")
    print()
    print("Minimum detJ location")
    print("---------------------")
    print(f"element              : {min_tag}")
    print(f"role                 : {min_role}")
    print(
        "centroid (x,y,z)     : "
        f"({min_centroid[0]:.12g}, "
        f"{min_centroid[1]:.12g}, "
        f"{min_centroid[2]:.12g})"
    )
    print(
        "Gauss (r,s,t)        : "
        f"({min_gp[0]:.12g}, {min_gp[1]:.12g}, {min_gp[2]:.12g})"
    )
    print(f"node tags            : {min_nodes}")
    print()
    print("Minimum-volume element")
    print("----------------------")
    print(f"element              : {vol_tag}")
    print(f"role                 : {vol_role}")
    print(
        "centroid (x,y,z)     : "
        f"({vol_centroid[0]:.12g}, "
        f"{vol_centroid[1]:.12g}, "
        f"{vol_centroid[2]:.12g})"
    )
    print()

    if nonpositive == 0 and min_det > 0.0:
        print("RESULT: PASS -- detJ > 0 at every stdBrick Gauss point")
        return 0

    print("RESULT: FAIL -- at least one stdBrick has detJ <= 0")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

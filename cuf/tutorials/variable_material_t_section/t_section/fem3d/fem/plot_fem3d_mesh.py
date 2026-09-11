#!/usr/bin/env python3
"""Visualize the exact FEM3D mesh generated from a FEM3D case YAML.

The script does NOT define geometry or mesh presets.
It reads the same case YAML used by run_torsion_halfwave.py and builds the
mesh through the same read_case() + common_t_fem3d.TSectionMesh path.

Place this file in the FEM3D directory, next to:
    run_torsion_halfwave.py
    common_t_fem3d.py

Usage:
    python3 plot_fem3d_mesh.py cases/torsion_halfwave_model2.yaml

Optional save:
    python3 plot_fem3d_mesh.py cases/torsion_halfwave_model2.yaml --save mesh.png
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection

import common_t_fem3d as common
import run_torsion_halfwave as torsion


# H8 faces for the connectivity used by common_t_fem3d.TSectionMesh.
H8_FACES = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (0, 1, 5, 4),
    (1, 2, 6, 5),
    (2, 3, 7, 6),
    (3, 0, 4, 7),
)


def boundary_faces(mesh: common.TSectionMesh) -> list[tuple[int, int, int, int]]:
    """Return only faces belonging to the external boundary of the brick mesh."""
    counts: Counter[tuple[int, ...]] = Counter()
    oriented: dict[tuple[int, ...], tuple[int, int, int, int]] = {}

    for element in mesh.elements:
        conn = element.conn
        for local_face in H8_FACES:
            face = tuple(conn[i] for i in local_face)
            key = tuple(sorted(face))
            counts[key] += 1
            oriented[key] = face

    return [oriented[key] for key, count in counts.items() if count == 1]


def boundary_edges(faces: list[tuple[int, int, int, int]]) -> list[tuple[int, int]]:
    """Return unique edges of the external boundary faces."""
    edges: set[tuple[int, int]] = set()
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            edges.add(tuple(sorted((a, b))))
    return sorted(edges)


def set_equal_axes(ax, xyz: np.ndarray) -> None:
    mins = xyz.min(axis=0)
    maxs = xyz.max(axis=0)
    spans = maxs - mins
    spans[spans == 0.0] = 1.0

    ax.set_xlim(mins[0], maxs[0])
    ax.set_ylim(mins[1], maxs[1])
    ax.set_zlim(mins[2], maxs[2])
    ax.set_box_aspect(tuple(spans))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot the exact structured FEM3D mesh from a FEM3D case YAML."
    )
    parser.add_argument(
        "case",
        type=Path,
        help="Same FEM3D case YAML passed to run_torsion_halfwave.py",
    )
    parser.add_argument("--save", type=Path, default=None, help="Optional image file")
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--elev", type=float, default=20.0)
    parser.add_argument("--azim", type=float, default=-60.0)
    parser.add_argument("--linewidth", type=float, default=0.28)
    parser.add_argument("--alpha", type=float, default=0.65)
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    # Exact same input chain as the FEM3D torsion solver:
    # case YAML -> problem YAML -> CSF model -> mesh controls.
    d = torsion.read_case(args.case)
    mesh = common.TSectionMesh(d)

    faces = boundary_faces(mesh)
    edges = boundary_edges(faces)

    node_xyz = mesh.nodes
    segments = np.asarray(
        [[node_xyz[a], node_xyz[b]] for a, b in edges],
        dtype=float,
    )
    xyz = np.asarray(list(node_xyz.values()), dtype=float)

    print(f"case       : {d['case_name']}")
    print(f"case yaml  : {d['case_path']}")
    print(f"problem    : {d['problem_path']}")
    print(f"CSF model  : {d['model_path']}")
    print(f"nodes      : {len(mesh.nodes)}")
    print(f"stdBricks  : {len(mesh.elements)}")
    print(f"nx         : {d['nx']}")
    print(f"web ny/nz  : {d['web_ny']} / {d['web_nz']}")
    print(f"flange ny  : {d['overhang_ny']} overhang, {d['web_ny']} over web")
    print(f"flange nz  : {d['flange_nz']}")

    fig = plt.figure(figsize=(13, 7))
    ax = fig.add_subplot(111, projection="3d")

    collection = Line3DCollection(
        segments,
        linewidths=args.linewidth,
        alpha=args.alpha,
    )
    ax.add_collection3d(collection)

    set_equal_axes(ax, xyz)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_title(
        f"{d['case_name']}\n"
        f"{len(mesh.elements):,} stdBrick elements - {len(mesh.nodes):,} nodes"
    )
    ax.view_init(elev=args.elev, azim=args.azim)

    fig.tight_layout()

    if args.save is not None:
        fig.savefig(args.save, dpi=args.dpi, bbox_inches="tight")
        print(f"saved      : {args.save}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()

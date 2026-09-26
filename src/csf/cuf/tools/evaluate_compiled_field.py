# Version: CSF-CUF self-contained field evaluator v3 - 2026-09-22
#!/usr/bin/env python3
"""Evaluate u, grad(u), strain, C and stress from one self-contained CUF NPZ."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from csf.cuf.solver.compiled_field import CompiledDisplacementField


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load a self-contained CUF .cuf.npz checkpoint and evaluate the "
            "continuous displacement, strain, constitutive and stress fields "
            "at one physical point."
        )
    )
    parser.add_argument("checkpoint", type=Path, help="Path to the .cuf.npz file")
    parser.add_argument("--x", type=float, required=True, help="Longitudinal coordinate")
    parser.add_argument("--y", type=float, required=True, help="Section y coordinate")
    parser.add_argument("--z", type=float, required=True, help="Section z coordinate")
    return parser


def _print_vector(title: str, labels, values) -> None:
    print(title)
    for label, value in zip(labels, values):
        print(f"  {label:<10s} = {float(value):.16e}")
    print()


def _print_matrix(title: str, matrix: np.ndarray) -> None:
    print(title)
    for row in np.asarray(matrix, dtype=float):
        print("  " + " ".join(f"{float(value): .16e}" for value in row))
    print()


def main() -> None:
    args = build_parser().parse_args()

    field = CompiledDisplacementField.load(args.checkpoint)
    if not field.has_self_contained_stress:
        raise RuntimeError(
            "checkpoint does not contain the self-contained CSF constitutive "
            "context; regenerate it with the updated solver"
        )

    x = float(args.x)
    y = float(args.y)
    z = float(args.z)

    displacement = field(x, y, z)
    gradient = field.displacement_gradient(x, y, z)
    strain = field.strain(x, y, z)
    domain = field.domain_at_point(x, y, z)
    constitutive = field.constitutive_matrix(x, y, z)
    stress = field.stress(x, y, z)

    metadata = field.metadata
    print(f"Checkpoint : {args.checkpoint}")
    print(f"Case       : {metadata.get('case_name', '<unknown>')}")
    print(f"Point      : x={x:g}, y={y:g}, z={z:g}")
    print(f"Domain id  : {getattr(domain, 'domain_id', '<unknown>')}")
    print(f"Domain name: {getattr(domain, 'name', None) or '<unnamed>'}")
    print()

    _print_vector(
        "DISPLACEMENT",
        ("ux", "uy", "uz"),
        displacement,
    )

    _print_matrix(
        "DISPLACEMENT GRADIENT  [rows=u components, columns=x,y,z]",
        gradient,
    )

    _print_vector(
        "STRAIN",
        (
            "epsilon_xx",
            "epsilon_yy",
            "epsilon_zz",
            "gamma_yz",
            "gamma_xz",
            "gamma_xy",
        ),
        strain,
    )

    _print_matrix("CONSTITUTIVE MATRIX C", constitutive)

    _print_vector(
        "STRESS",
        (
            "sigma_xx",
            "sigma_yy",
            "sigma_zz",
            "tau_yz",
            "tau_xz",
            "tau_xy",
        ),
        stress,
    )


if __name__ == "__main__":
    main()

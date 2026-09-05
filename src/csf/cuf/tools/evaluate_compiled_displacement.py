#!/usr/bin/env python3
"""Load a saved CUF displacement checkpoint and evaluate u(x, y, z)."""

from __future__ import annotations

import argparse
from pathlib import Path

from csf.cuf.solver.compiled_field import CompiledDisplacementField


HERE = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = (
    HERE / "data" / "double_t_torsion_halfwave_lagrange_N12.cuf.npz"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load a self-contained CUF displacement checkpoint and evaluate "
            "the solved displacement field at one physical point."
        )
    )
    parser.add_argument(
        "checkpoint",
        nargs="?",
        type=Path,
        default=DEFAULT_CHECKPOINT,
        help="Path to a .cuf.npz checkpoint (default: bundled example file).",
    )
    parser.add_argument("--x", type=float, default=500.0, help="Longitudinal coordinate.")
    parser.add_argument("--y", type=float, default=0.0, help="Section y coordinate.")
    parser.add_argument("--z", type=float, default=0.0, help="Section z coordinate.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    field = CompiledDisplacementField.load(args.checkpoint)
    displacement = field(args.x, args.y, args.z)

    metadata = field.metadata
    print(f"Checkpoint : {args.checkpoint}")
    print(f"Case       : {metadata.get('case_name', '<unknown>')}")
    print(f"Basis      : {metadata.get('basis_name', '<unknown>')}")
    print(f"Order      : {metadata.get('basis_order', '<unknown>')}")
    print(f"x domain   : [{field.x_start:g}, {field.x_end:g}]")
    print()
    print(f"u({args.x:g}, {args.y:g}, {args.z:g})")
    print(f"  ux = {displacement[0]:.12e}")
    print(f"  uy = {displacement[1]:.12e}")
    print(f"  uz = {displacement[2]:.12e}")


if __name__ == "__main__":
    main()

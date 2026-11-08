#!/usr/bin/env python3
"""Plot the saved H20 mesh series without rerunning a structural solver.

Run from cuf/I-Shape_L:
    python3 fem3d/plot_h20_convergence.py

The input is the set of T*_h20.npz checkpoints and the accompanying
T*_strong_residual.json files produced by run_h20_convergence.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path,
                        default=Path("fem3d/output/h20_convergence"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("fem3d/output/h20_convergence/figures"))
    parser.add_argument("--dpi", type=int, default=170)
    args = parser.parse_args()

    checkpoints = sorted(
        (p for p in args.input_dir.glob("T*_h20.npz")
         if re.fullmatch(r"T[0-9]+_h20\.npz", p.name)),
        key=lambda p: int(p.stem.split("_")[0][1:]),
    )
    if len(checkpoints) < 2:
        raise SystemExit(f"Expected at least two solved T-level checkpoints in {args.input_dir}")
    rows = []
    for path in checkpoints:
        level = path.stem.split("_")[0]
        residual_path = args.input_dir / f"{level}_strong_residual.json"
        if not residual_path.is_file():
            raise SystemExit(f"Missing residual file: {residual_path}")
        with np.load(path, allow_pickle=False) as d:
            displacement = d["displacement"]
            if displacement.size == 0:
                raise SystemExit(f"Missing solved displacements: {path}")
            n_elements = len(d["elements"])
            min_uz = float(displacement[:, 2].min())
        residuals = json.loads(residual_path.read_text(encoding="utf-8"))
        rms = residuals["metrics"]
        rows.append((level, n_elements, min_uz,
                     float(rms["norm"]["rms"]), float(rms["z"]["rms"])))

    labels = [row[0] for row in rows]
    nel = np.asarray([row[1] for row in rows])
    uz = np.asarray([row[2] for row in rows])
    norm = np.asarray([row[3] for row in rows])
    rz = np.asarray([row[4] for row in rows])
    changes = 100 * np.abs(np.diff(uz) / uz[:-1])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def save(filename: str) -> None:
        plt.grid(alpha=0.25)
        plt.tight_layout()
        dest = args.output_dir / filename
        plt.savefig(dest, dpi=args.dpi, bbox_inches="tight")
        plt.close()
        print("Saved:", dest)

    plt.figure(figsize=(8.5, 4.8))
    plt.plot(nel, uz, "o-", linewidth=1.7)
    for n, u, label in zip(nel, uz, labels):
        plt.annotate(label, (n, u), xytext=(0, 8),
                     textcoords="offset points", ha="center", fontsize=9)
    plt.xlabel("Number of H20 elements")
    plt.ylabel("Minimum vertical displacement, $u_z$ (mm)")
    plt.title("H20 mesh refinement: minimum vertical displacement")
    save("min_uz_vs_mesh.png")

    plt.figure(figsize=(8.5, 4.8))
    plt.plot(nel[1:], changes, "o-", linewidth=1.7)
    plt.axhline(0.1, color="gray", linestyle="--", linewidth=1, label="0.1% criterion")
    for n, change, label in zip(nel[1:], changes, labels[1:]):
        plt.annotate(label, (n, change), xytext=(0, 8),
                     textcoords="offset points", ha="center", fontsize=9)
    plt.xlabel("Number of H20 elements")
    plt.ylabel("Change from preceding level (%)")
    plt.yscale("log")
    plt.legend(loc="upper right", fontsize=9)
    plt.title("Displacement stabilization under mesh refinement")
    save("relative_change_vs_mesh.png")

    plt.figure(figsize=(8.5, 4.8))
    plt.plot(nel, norm, "o-", linewidth=1.7, label="Full residual norm")
    plt.plot(nel, rz, "s--", linewidth=1.4, label="$z$ equation")
    plt.xlabel("Number of H20 elements")
    plt.ylabel("One-point volume-weighted RMS (MPa/mm)")
    plt.title("Interior equilibrium diagnostic across the H20 mesh series")
    plt.legend()
    save("interior_residual_vs_mesh.png")


if __name__ == "__main__":
    main()

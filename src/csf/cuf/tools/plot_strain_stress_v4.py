#!/usr/bin/env python3
# Version: CSF-CUF plot_strain_stress v4 - 2026-09-23
# Native model values only: no assumed unit system and no automatic scaling.
"""Plot all displacements, all strains and all stresses along x.

Inputs:
    compiled CUF displacement checkpoint (.cuf.npz)
    original CSF YAML

For every sampled physical point (x, y, z):
    u       = compiled_field(x, y, z)
    epsilon = compiled_field.strain(x, y, z)
    C       = bridge.constitutive_provider.matrix(...)
    sigma   = C @ epsilon

The constitutive matrix therefore comes directly from the CUF-core provider.
No constitutive law is duplicated in this tool.

Outputs:
    1 combined PNG containing:
        ux, uy, uz,
        epsilon_xx, epsilon_yy, epsilon_zz, gamma_yz, gamma_xz, gamma_xy,
        sigma_xx, sigma_yy, sigma_zz, tau_yz, tau_xz, tau_xy

    separate PNG files for each of the same curves

    optional CSV containing all recovered values
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from csf.cuf.csf_bridge import CSFCUFModelBridge
from csf.cuf.solver.compiled_field import CompiledDisplacementField


CURVES = [
    ("ux", 0, "displacement", r"$u_x$", r"(a) Displacement, $u_x$"),
    ("uy", 1, "displacement", r"$u_y$", r"(b) Displacement, $u_y$"),
    ("uz", 2, "displacement", r"$u_z$", r"(c) Displacement, $u_z$"),
    ("epsilon_xx", 0, "strain", r"$\varepsilon_{xx}$", r"(d) Strain, $\varepsilon_{xx}$"),
    ("epsilon_yy", 1, "strain", r"$\varepsilon_{yy}$", r"(e) Strain, $\varepsilon_{yy}$"),
    ("epsilon_zz", 2, "strain", r"$\varepsilon_{zz}$", r"(f) Strain, $\varepsilon_{zz}$"),
    ("gamma_yz", 3, "strain", r"$\gamma_{yz}$", r"(g) Shear strain, $\gamma_{yz}$"),
    ("gamma_xz", 4, "strain", r"$\gamma_{xz}$", r"(h) Shear strain, $\gamma_{xz}$"),
    ("gamma_xy", 5, "strain", r"$\gamma_{xy}$", r"(i) Shear strain, $\gamma_{xy}$"),
    ("sigma_xx", 0, "stress", r"$\sigma_{xx}$", r"(j) Stress, $\sigma_{xx}$"),
    ("sigma_yy", 1, "stress", r"$\sigma_{yy}$", r"(k) Stress, $\sigma_{yy}$"),
    ("sigma_zz", 2, "stress", r"$\sigma_{zz}$", r"(l) Stress, $\sigma_{zz}$"),
    ("tau_yz", 3, "stress", r"$\tau_{yz}$", r"(m) Stress, $\tau_{yz}$"),
    ("tau_xz", 4, "stress", r"$\tau_{xz}$", r"(n) Stress, $\tau_{xz}$"),
    ("tau_xy", 5, "stress", r"$\tau_{xy}$", r"(o) Stress, $\tau_{xy}$"),
]


def recover_longitudinal_fields(
    npz_path: str | Path,
    csf_yaml: str | Path,
    *,
    section_y: float,
    section_z: float,
    points: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if points < 2:
        raise ValueError("points must be >= 2")

    field = CompiledDisplacementField.load(Path(npz_path))
    bridge = CSFCUFModelBridge.from_yaml(Path(csf_yaml))

    field_domain = np.asarray((field.x_start, field.x_end), dtype=float)
    csf_domain = np.asarray(bridge.longitudinal_domain(), dtype=float)
    scale = max(1.0, float(np.max(np.abs(np.r_[field_domain, csf_domain]))))
    atol = 64.0 * np.finfo(float).eps * scale
    if not np.allclose(field_domain, csf_domain, rtol=0.0, atol=atol):
        raise ValueError(
            "NPZ and CSF YAML longitudinal domains differ: "
            f"NPZ={tuple(field_domain)}, CSF={tuple(csf_domain)}"
        )

    section_provider = bridge.section_provider
    constitutive_provider = bridge.constitutive_provider

    section_y = float(section_y)
    section_z = float(section_z)

    x_values = np.linspace(field.x_start, field.x_end, int(points))
    displacement = np.empty((x_values.size, 3), dtype=float)
    strain = np.empty((x_values.size, 6), dtype=float)
    stress = np.empty((x_values.size, 6), dtype=float)

    for i, x in enumerate(x_values):
        x = float(x)
        domain = section_provider.domain_at_point(x, section_y, section_z)

        displacement[i, :] = np.asarray(field(x, section_y, section_z), dtype=float)

        strain_i = np.asarray(field.strain(x, section_y, section_z), dtype=float)
        if strain_i.shape != (6,):
            raise RuntimeError(f"compiled strain returned shape {strain_i.shape}, expected (6,)")
        strain[i, :] = strain_i

        C = np.asarray(
            constitutive_provider.matrix(
                x=x,
                domain_id=domain.domain_id,
                y=section_y,
                z=section_z,
            ),
            dtype=float,
        )
        if C.shape != (6, 6):
            raise RuntimeError(f"CUF constitutive provider returned shape {C.shape}, expected (6, 6)")

        stress[i, :] = C @ strain_i

    return x_values, displacement, strain, stress


def _style_axis(ax, ylabel: str, title: str) -> None:
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend()


def _plot_curve(ax, x: np.ndarray, values: np.ndarray, *, ylabel: str, title: str, markevery: int) -> None:
    ax.plot(
        x,
        values,
        marker="o",
        markersize=2.8,
        markevery=markevery,
        linewidth=1.0,
        label="CSF-CUF",
    )
    _style_axis(ax, ylabel, title)


def _select_values(kind: str, index: int, displacement: np.ndarray, strain: np.ndarray, stress: np.ndarray) -> np.ndarray:
    if kind == "displacement":
        return displacement[:, index]
    if kind == "strain":
        return strain[:, index]
    if kind == "stress":
        return stress[:, index]
    raise ValueError(f"unsupported kind: {kind}")


def save_combined_plot(
    x: np.ndarray,
    displacement: np.ndarray,
    strain: np.ndarray,
    stress: np.ndarray,
    *,
    points: int,
    output: str | Path,
) -> Path:
    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(8, 2, figsize=(12.0, 28.0), sharex=True)
    axes = axes.ravel()
    markevery = max(1, points // 50)

    for ax, (name, index, kind, ylabel, title) in zip(axes, CURVES):
        values = _select_values(kind, index, displacement, strain, stress)
        _plot_curve(ax, x, values, ylabel=ylabel, title=title, markevery=markevery)
        ax.set_xlabel(r"$x$")

    # Hide the one unused subplot in the 8x2 grid.
    for ax in axes[len(CURVES):]:
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def save_separate_plots(
    x: np.ndarray,
    displacement: np.ndarray,
    strain: np.ndarray,
    stress: np.ndarray,
    *,
    points: int,
    directory: str | Path,
) -> list[Path]:
    output_dir = Path(directory).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    markevery = max(1, points // 50)

    paths: list[Path] = []
    for name, index, kind, ylabel, title in CURVES:
        values = _select_values(kind, index, displacement, strain, stress)
        fig, ax = plt.subplots(figsize=(8.0, 5.2))
        _plot_curve(ax, x, values, ylabel=ylabel, title=title, markevery=markevery)
        ax.set_xlabel(r"$x$")
        fig.tight_layout()

        path = output_dir / f"{name}.png"
        fig.savefig(path, dpi=220, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)

    return paths


def save_csv(path: str | Path, x: np.ndarray, displacement: np.ndarray, strain: np.ndarray, stress: np.ndarray) -> Path:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    values = np.column_stack((x, displacement, strain, stress))
    header = (
        "x,ux,uy,uz,"
        "epsilon_xx,epsilon_yy,epsilon_zz,gamma_yz,gamma_xz,gamma_xy,"
        "sigma_xx,sigma_yy,sigma_zz,tau_yz,tau_xz,tau_xy"
    )
    np.savetxt(output, values, delimiter=",", header=header, comments="")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot all CSF-CUF displacement, strain and stress components along x "
            "from a compiled displacement NPZ and CSF YAML."
        )
    )
    parser.add_argument("npz_path", type=Path)
    parser.add_argument("csf_yaml", type=Path)
    parser.add_argument("--section-y", type=float, required=True, help="Fixed CSF section y coordinate.")
    parser.add_argument("--section-z", type=float, required=True, help="Fixed CSF section z coordinate.")
    parser.add_argument("--points", type=int, default=401, help="Number of longitudinal samples used for plotting (default: 401).")
    parser.add_argument("--output", type=Path, default=Path("strain_stress_all.png"), help="Combined PNG output path.")
    parser.add_argument(
        "--separate-dir",
        type=Path,
        default=None,
        help=("Directory for individual PNG files. Default: a sibling directory named <output-stem>_components."),
    )
    parser.add_argument("--csv", type=Path, default=None, help="Optional CSV containing x, all displacements, all strains and all stresses.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    x, displacement, strain, stress = recover_longitudinal_fields(
        args.npz_path,
        args.csf_yaml,
        section_y=args.section_y,
        section_z=args.section_z,
        points=args.points,
    )

    combined_path = save_combined_plot(
        x,
        displacement,
        strain,
        stress,
        points=args.points,
        output=args.output,
    )

    if args.separate_dir is None:
        output = Path(args.output).expanduser().resolve()
        separate_dir = output.parent / f"{output.stem}_components"
    else:
        separate_dir = args.separate_dir

    separate_paths = save_separate_plots(
        x,
        displacement,
        strain,
        stress,
        points=args.points,
        directory=separate_dir,
    )

    print(f"point y,z     : ({args.section_y:g}, {args.section_z:g})")
    print(f"points        : {args.points}")
    print(f"combined plot : {combined_path}")
    print(f"separate dir  : {Path(separate_dir).expanduser().resolve()}")
    print(f"separate PNGs : {len(separate_paths)}")

    if args.csv is not None:
        csv_path = save_csv(args.csv, x, displacement, strain, stress)
        print(f"csv           : {csv_path}")


if __name__ == "__main__":
    main()

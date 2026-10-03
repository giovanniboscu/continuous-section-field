#!/usr/bin/env python3
"""
Plot a CUF displacement component reconstructed from compatible NPZ files
found directly inside one input directory, along a coordinate line.

Exactly two coordinates must be fixed and the third must be given as a range.

Examples
--------
Vary x from 0 to 1000, fixing y=-5 and z=-50:

    python3 plot_npz_line_response_v4.py results \
        --component uz --y=-5 --z=-50 --x=0,1000

Vary y instead:

    python3 plot_npz_line_response_v4.py results \
        --component uy --x=500 --z=-50 --y=-5,95

Required NPZ arrays
-------------------
- element_x_starts
- element_x_ends
- element_coefficients
- longitudinal_shape_coefficients
- transverse_x_power_coefficients
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np


REQUIRED_KEYS = (
    "element_x_starts",
    "element_x_ends",
    "element_coefficients",
    "longitudinal_shape_coefficients",
    "transverse_x_power_coefficients",
)

COMPONENTS = {"ux": 0, "uy": 1, "uz": 2}


def parse_coord_spec(text: str) -> tuple[float, ...]:
    """Parse 'value' or 'min,max'."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) not in (1, 2):
        raise argparse.ArgumentTypeError(
            f"expected one value or min,max, got: {text!r}"
        )
    try:
        values = tuple(float(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid numeric value: {text!r}") from exc

    if len(values) == 2 and values[0] == values[1]:
        raise argparse.ArgumentTypeError("range endpoints must be different")
    return values


def label_from_path(path: Path) -> str:
    name = path.name
    if name.endswith(".cuf.npz"):
        return name[: -len(".cuf.npz")]
    if name.endswith(".npz"):
        return name[: -len(".npz")]
    return path.stem


def float_powers(value: float, count: int) -> np.ndarray:
    """Return [1, value, value^2, ...] in floating point."""
    return np.power(float(value), np.arange(count, dtype=float))


class CUFResult:
    def __init__(self, path: Path):
        self.path = path
        with np.load(path, allow_pickle=False) as data:
            missing = [key for key in REQUIRED_KEYS if key not in data.files]
            if missing:
                raise KeyError("missing keys: " + ", ".join(missing))

            self.element_x_starts = np.asarray(data["element_x_starts"], dtype=float)
            self.element_x_ends = np.asarray(data["element_x_ends"], dtype=float)
            self.element_coefficients = np.asarray(
                data["element_coefficients"], dtype=float
            )
            self.longitudinal_shape_coefficients = np.asarray(
                data["longitudinal_shape_coefficients"], dtype=float
            )
            self.transverse_x_power_coefficients = np.asarray(
                data["transverse_x_power_coefficients"], dtype=float
            )

        self._validate_shapes()

    def _validate_shapes(self) -> None:
        xs = self.element_x_starts
        xe = self.element_x_ends
        q = self.element_coefficients
        lc = self.longitudinal_shape_coefficients
        tc = self.transverse_x_power_coefficients

        if xs.ndim != 1 or xe.ndim != 1 or xs.shape != xe.shape:
            raise ValueError("invalid element_x_starts/element_x_ends shapes")
        if q.ndim != 4 or q.shape[0] != xs.size or q.shape[-1] != 3:
            raise ValueError(f"unexpected element_coefficients shape {q.shape}")
        if lc.ndim != 2 or lc.shape[0] != q.shape[1]:
            raise ValueError(
                "longitudinal_shape_coefficients is incompatible with "
                "element_coefficients"
            )
        if tc.ndim != 4 or tc.shape[0] != q.shape[2]:
            raise ValueError(
                "transverse_x_power_coefficients is incompatible with "
                "element_coefficients"
            )

    @property
    def x_min(self) -> float:
        return float(np.min(self.element_x_starts))

    @property
    def x_max(self) -> float:
        return float(np.max(self.element_x_ends))

    def _element_index(self, x: float) -> int:
        tol = 1.0e-10 * max(1.0, abs(self.x_min), abs(self.x_max))
        if x < self.x_min - tol or x > self.x_max + tol:
            raise ValueError(
                f"x={x:g} outside [{self.x_min:g}, {self.x_max:g}]"
            )

        # Use half-open intervals [x_start, x_end), except for the last end.
        if abs(x - self.x_max) <= tol:
            return len(self.element_x_starts) - 1

        candidates = np.where(
            (x >= self.element_x_starts - tol)
            & (x < self.element_x_ends - tol)
        )[0]
        if candidates.size:
            return int(candidates[0])

        # Fallback for roundoff exactly on an internal interface.
        candidates = np.where(
            (x >= self.element_x_starts - tol)
            & (x <= self.element_x_ends + tol)
        )[0]
        if not candidates.size:
            raise ValueError(f"no longitudinal element contains x={x:g}")
        return int(candidates[-1])

    def displacement(self, x: float, y: float, z: float) -> np.ndarray:
        """Reconstruct [ux, uy, uz] at physical coordinates (x, y, z)."""
        e = self._element_index(float(x))
        x0 = self.element_x_starts[e]
        x1 = self.element_x_ends[e]
        if x1 == x0:
            raise ValueError(f"zero-length element {e}")

        # Local longitudinal coordinate in [-1, 1].
        xi = 2.0 * (float(x) - x0) / (x1 - x0) - 1.0

        # Each row contains ascending polynomial coefficients of one
        # longitudinal shape function: N_i(xi) = sum_p c[i,p] * xi**p.
        xi_powers = float_powers(xi, self.longitudinal_shape_coefficients.shape[1])
        shape = self.longitudinal_shape_coefficients @ xi_powers

        # F_tau(x,y,z) = sum_{a,b,c} T[tau,a,b,c] x**a y**b z**c.
        # The x-dependence is needed by longitudinally blended transverse bases.
        t = self.transverse_x_power_coefficients
        x_powers = float_powers(x, t.shape[1])
        y_powers = float_powers(y, t.shape[2])
        z_powers = float_powers(z, t.shape[3])
        transverse = np.einsum(
            "tabc,a,b,c->t",
            t,
            x_powers,
            y_powers,
            z_powers,
            optimize=True,
        )

        # q[e, i, tau, component]
        return np.einsum(
            "i,t,itc->c",
            shape,
            transverse,
            self.element_coefficients[e],
            optimize=True,
        )


def build_line(
    x_spec: tuple[float, ...],
    y_spec: tuple[float, ...],
    z_spec: tuple[float, ...],
    samples: int,
) -> tuple[str, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    specs = {"x": x_spec, "y": y_spec, "z": z_spec}
    varying = [name for name, spec in specs.items() if len(spec) == 2]
    fixed = [name for name, spec in specs.items() if len(spec) == 1]

    if len(varying) != 1 or len(fixed) != 2:
        raise ValueError(
            "exactly one of --x/--y/--z must be a range min,max and the "
            "other two must be single fixed values"
        )

    axis = varying[0]
    start, end = specs[axis]
    s = np.linspace(start, end, samples)

    coords = {}
    for name, spec in specs.items():
        if name == axis:
            coords[name] = s
        else:
            coords[name] = np.full(samples, spec[0], dtype=float)

    return axis, s, coords["x"], coords["y"], coords["z"]


def fixed_description(
    axis: str,
    x_spec: tuple[float, ...],
    y_spec: tuple[float, ...],
    z_spec: tuple[float, ...],
) -> str:
    specs = {"x": x_spec, "y": y_spec, "z": z_spec}
    return ", ".join(
        f"{name}={spec[0]:g}" for name, spec in specs.items() if name != axis
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plot reconstructed CUF displacement along a line for every "
            "compatible NPZ found directly inside the specified directory."
        )
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="directory containing the NPZ files to process; subdirectories are ignored",
    )
    parser.add_argument("--x", required=True, type=parse_coord_spec, help="x or xmin,xmax")
    parser.add_argument("--y", required=True, type=parse_coord_spec, help="y or ymin,ymax")
    parser.add_argument("--z", required=True, type=parse_coord_spec, help="z or zmin,zmax")
    parser.add_argument(
        "--component",
        required=True,
        choices=("ux", "uy", "uz"),
        help="displacement component to plot (required)",
    )
    parser.add_argument(
        "--samples", type=int, default=501, help="number of points along the line"
    )
    parser.add_argument(
        "--pattern", default="*.npz", help="filename pattern in the specified directory; default: *.npz"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("line_plots"),
        help="output directory; default: line_plots",
    )
    parser.add_argument(
        "--show", action="store_true", help="also open the matplotlib window"
    )
    args = parser.parse_args()

    if args.samples < 2:
        parser.error("--samples must be at least 2")
    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")

    try:
        axis, s, xs, ys, zs = build_line(args.x, args.y, args.z, args.samples)
    except ValueError as exc:
        parser.error(str(exc))

    paths = sorted(p for p in args.directory.glob(args.pattern) if p.is_file())
    if not paths:
        parser.error(f"no files matching {args.pattern!r} in {args.directory}")

    results: list[CUFResult] = []
    for path in paths:
        try:
            results.append(CUFResult(path))
        except Exception as exc:
            print(f"[skip] {path}: {exc}", file=sys.stderr)

    if not results:
        parser.error("no compatible CUF NPZ files found")

    selected = [args.component]

    # Keep plots outside an input tree rooted at a directory named "output".
    # Example:
    #   input:  /project/output/case_A
    #   --output-dir plots
    # becomes:
    #   /project/plots
    if args.output_dir.is_absolute():
        output_dir = args.output_dir
    else:
        input_dir = args.directory.resolve()
        output_root = None
        for candidate in (input_dir, *input_dir.parents):
            if candidate.name == "output":
                output_root = candidate.parent
                break

        if output_root is None:
            output_dir = Path.cwd() / args.output_dir
        else:
            output_dir = output_root / args.output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    fixed_text = fixed_description(axis, args.x, args.y, args.z)

    # Reconstruct each file once for all requested components.
    curves: dict[Path, np.ndarray] = {}
    for result in results:
        values = np.empty((args.samples, 3), dtype=float)
        try:
            for j, (x, y, z) in enumerate(zip(xs, ys, zs)):
                values[j] = result.displacement(float(x), float(y), float(z))
        except Exception as exc:
            print(f"[skip] {result.path}: {exc}", file=sys.stderr)
            continue
        curves[result.path] = values

    if not curves:
        parser.error("no compatible NPZ could be evaluated on the requested line")

    for component in selected:
        idx = COMPONENTS[component]
        fig, ax = plt.subplots(figsize=(10, 6))

        for path, values in curves.items():
            ax.plot(s, values[:, idx], label=label_from_path(path))

        ax.set_xlabel(axis)
        ax.set_ylabel(component)
        ax.set_title(f"{component} along {axis} ({fixed_text})")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize="small")
        fig.tight_layout()

        out = output_dir / f"{component}_along_{axis}.png"
        fig.savefig(out, dpi=180)
        print(out)

        if args.show:
            plt.show()
        plt.close(fig)

    print(f"plotted {len(curves)} NPZ file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

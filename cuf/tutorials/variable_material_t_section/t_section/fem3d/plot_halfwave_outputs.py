#!/usr/bin/env python3
# v3.0 - Standalone CUF/FEM3D half-wave plotter with automatic CUF discovery.
#
# This file merges the CUF/FEM3D response parser and the separate-N plotting
# workflow into one script. It discovers every supported response.txt below
# ../output by default, so no case list or CUF filename pattern is hard-coded.

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


POINT_ORDER = ("center", "plus", "minus", "bottom_mid")
COMPONENTS = ("ux", "uy", "uz")
CASE_RE = re.compile(
    r"^(?P<problem>bending|torsion)_halfwave"
    r"(?:_v\d+(?:\.\d+)?)?_"
    r"(?P<family>.+)_N(?P<order>\d+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DiscoveredCase:
    response: Path
    directory_name: str
    problem: str
    family: str
    order: int

    @property
    def key(self) -> str:
        return self.directory_name

    @property
    def title(self) -> str:
        return (
            f"{self.problem.capitalize()} half-wave - "
            f"{self.family.replace('_', ' ').title()} - N={self.order:02d}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Discover CUF half-wave response.txt files and generate separate "
            "CUF-vs-FEM3D displacement figures for every case found."
        )
    )
    parser.add_argument(
        "--cuf-output-root",
        type=Path,
        default=Path("../output"),
        help="CUF output tree to scan recursively (default: ../output).",
    )
    parser.add_argument(
        "--fem3d-root",
        type=Path,
        default=Path("../fem3d/output"),
        help=(
            "FEM3D output tree containing station_points.csv references "
            "(default: ../fem3d/output)."
        ),
    )
    parser.add_argument(
        "--bending-fem3d",
        type=Path,
        default=None,
        help=(
            "Optional explicit bending FEM3D directory or station_points.csv. "
            "Overrides automatic discovery."
        ),
    )
    parser.add_argument(
        "--torsion-fem3d",
        type=Path,
        default=None,
        help=(
            "Optional explicit torsion FEM3D directory or station_points.csv. "
            "Overrides automatic discovery."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("plots_halfwave"),
        help="Directory in which plot folders are written (default: plots_halfwave).",
    )
    parser.add_argument(
        "--component",
        choices=("all", "ux", "uy", "uz"),
        default="all",
        help="Displacement component to plot (default: all).",
    )
    parser.add_argument(
        "--scale-mode",
        choices=("human", "local"),
        default="human",
        help=(
            "Y-axis policy. 'human' uses one common scale for every discovered "
            "case of the same physical problem/component; 'local' zooms each panel. "
            "Default: human."
        ),
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also write a PDF copy of every figure.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=220,
        help="PNG resolution in dots per inch (default: 220).",
    )
    return parser.parse_args()


def _cuf_float(text: str) -> float:
    """Parse ordinary or Fortran-style floating-point text."""
    return float(text.replace("D", "E").replace("d", "e"))


def read_cuf_response(path: Path) -> dict[tuple[float, str], dict[str, float]]:
    """Read current or legacy CUF station rows without depending on the header."""
    values: dict[tuple[float, str], dict[str, float]] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.replace("|", " ").replace(",", " ").replace(";", " ")
        fields = line.split()

        # Current post format:
        # x/L  x  y  z  point  ux  uy  uz
        if len(fields) >= 8 and fields[4] in POINT_ORDER:
            try:
                x_over_l, x_mm, y_mm, z_mm = map(_cuf_float, fields[:4])
                point = fields[4]
                ux, uy, uz = map(_cuf_float, fields[5:8])
            except ValueError:
                continue

            values[(round(x_over_l, 10), point)] = {
                "x_cuf_mm": x_mm,
                "y_cuf_mm": y_mm,
                "z_cuf_mm": z_mm,
                "ux_cuf_mm": ux,
                "uy_cuf_mm": uy,
                "uz_cuf_mm": uz,
            }
            continue

        # Legacy post format:
        # x/L  point  ux  uy  uz
        if len(fields) >= 5 and fields[1] in POINT_ORDER:
            try:
                x_over_l = _cuf_float(fields[0])
                point = fields[1]
                ux, uy, uz = map(_cuf_float, fields[2:5])
            except ValueError:
                continue

            values[(round(x_over_l, 10), point)] = {
                "ux_cuf_mm": ux,
                "uy_cuf_mm": uy,
                "uz_cuf_mm": uz,
            }

    if not values:
        raise ValueError(f"No CUF station rows found in {path}")

    return values


def validate_station_grid(rows: list[dict[str, float | str]]) -> None:
    """Require the same ordered x/L grid for all four section points."""
    grids = {
        point: tuple(
            sorted(
                round(float(row["x_over_L"]), 10)
                for row in rows
                if row["point"] == point
            )
        )
        for point in POINT_ORDER
    }

    reference = grids[POINT_ORDER[0]]
    if len(reference) < 2:
        raise ValueError("At least two longitudinal stations are required")

    for point, grid in grids.items():
        if grid != reference:
            raise ValueError(
                f"Point {point} does not use the common longitudinal grid"
            )


def join_results(
    cuf_response: Path,
    fem_stations: Path,
) -> list[dict[str, float | str]]:
    """Match CUF and FEM3D rows by (x/L, point) and verify physical coordinates."""
    cuf = read_cuf_response(cuf_response)
    joined: list[dict[str, float | str]] = []

    with fem_stations.open(newline="", encoding="utf-8") as handle:
        for fem_row in csv.DictReader(handle):
            x_over_l = float(fem_row["x_over_L"])
            point = fem_row["point"]
            key = (round(x_over_l, 10), point)

            if key not in cuf:
                raise KeyError(
                    f"Missing CUF result for x/L={x_over_l:g}, point={point}"
                )

            cuf_row = cuf[key]
            x_mm = float(fem_row["x"])
            y_mm = float(fem_row["y"])
            z_mm = float(fem_row["z"])

            # Current CUF response files contain physical coordinates. Verify that
            # CUF and FEM3D are comparing exactly the same physical section points.
            if "x_cuf_mm" in cuf_row:
                for axis, fem_value, cuf_value in (
                    ("x", x_mm, cuf_row["x_cuf_mm"]),
                    ("y", y_mm, cuf_row["y_cuf_mm"]),
                    ("z", z_mm, cuf_row["z_cuf_mm"]),
                ):
                    if not math.isclose(
                        fem_value,
                        float(cuf_value),
                        rel_tol=0.0,
                        abs_tol=5.0e-8,
                    ):
                        raise ValueError(
                            f"Coordinate mismatch at x/L={x_over_l:g}, "
                            f"point={point}, axis={axis}: "
                            f"FEM3D={fem_value}, CUF={cuf_value}"
                        )

            row: dict[str, float | str] = {
                "x_over_L": x_over_l,
                "point": point,
                "y_mm": y_mm,
                "z_mm": z_mm,
            }
            for component in COMPONENTS:
                row[f"{component}_fem3d_mm"] = float(fem_row[component])
                row[f"{component}_cuf_mm"] = float(
                    cuf_row[f"{component}_cuf_mm"]
                )
            joined.append(row)

    matched_keys = {
        (round(float(row["x_over_L"]), 10), str(row["point"]))
        for row in joined
    }
    extra_cuf_keys = set(cuf) - matched_keys
    if extra_cuf_keys:
        raise ValueError(f"CUF contains unmatched station rows: {extra_cuf_keys}")

    validate_station_grid(joined)
    return joined


def discover_cases(cuf_output_root: Path) -> list[DiscoveredCase]:
    """Discover supported half-wave response.txt files below the CUF output tree."""
    root = cuf_output_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"CUF output directory not found: {root}")

    discovered: list[DiscoveredCase] = []
    ignored: list[Path] = []

    for response in sorted(root.rglob("response.txt")):
        directory_name = response.parent.name
        match = CASE_RE.match(directory_name)
        if match is None:
            ignored.append(response)
            continue

        discovered.append(
            DiscoveredCase(
                response=response.resolve(),
                directory_name=directory_name,
                problem=match.group("problem").lower(),
                family=match.group("family").lower(),
                order=int(match.group("order")),
            )
        )

    discovered.sort(
        key=lambda case: (case.problem, case.family, case.order, case.directory_name)
    )

    if ignored:
        print("Ignored response.txt files whose directory name is not a supported half-wave case:")
        for path in ignored:
            print(f"  {path}")
        print()

    if not discovered:
        raise FileNotFoundError(
            f"No supported bending/torsion half-wave response.txt files found below {root}"
        )

    return discovered


def _explicit_station_file(path: Path | None, *, label: str) -> Path | None:
    if path is None:
        return None

    resolved = path.resolve()
    if resolved.is_dir():
        resolved = resolved / "station_points.csv"

    if not resolved.is_file():
        raise FileNotFoundError(f"{label} FEM3D station file not found: {resolved}")

    return resolved


def _candidate_fem3d_roots(requested_root: Path) -> list[Path]:
    """Return the requested root plus a few harmless legacy-layout fallbacks."""
    raw = (
        requested_root,
        Path("../fem3d/output"),
        Path("fem3d/output"),
        Path("output"),
    )

    result: list[Path] = []
    seen: set[Path] = set()
    for item in raw:
        resolved = item.resolve()
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def discover_fem3d_station_files(
    *,
    problems: set[str],
    fem3d_root: Path,
    bending_fem3d: Path | None,
    torsion_fem3d: Path | None,
) -> dict[str, Path]:
    """Resolve one FEM3D station_points.csv reference for each physical problem."""
    explicit = {
        "bending": _explicit_station_file(bending_fem3d, label="Bending"),
        "torsion": _explicit_station_file(torsion_fem3d, label="Torsion"),
    }

    resolved: dict[str, Path] = {
        problem: path
        for problem, path in explicit.items()
        if problem in problems and path is not None
    }

    roots = _candidate_fem3d_roots(fem3d_root)
    all_station_files: list[Path] = []
    for root in roots:
        all_station_files.extend(path.resolve() for path in root.rglob("station_points.csv"))
    all_station_files = sorted(set(all_station_files))

    for problem in sorted(problems):
        if problem in resolved:
            continue

        tokens = (f"{problem}_halfwave", problem)
        candidates = [
            path
            for path in all_station_files
            if tokens[0] in str(path).lower()
        ]
        if not candidates:
            candidates = [
                path
                for path in all_station_files
                if tokens[1] in str(path).lower()
            ]

        if len(candidates) == 1:
            resolved[problem] = candidates[0]
            continue

        if not candidates:
            roots_text = ", ".join(str(path) for path in roots) or "<none found>"
            raise FileNotFoundError(
                f"No FEM3D station_points.csv found for {problem}. "
                f"Searched roots: {roots_text}. Use --{problem}-fem3d to specify it."
            )

        candidates_text = "\n".join(f"  {path}" for path in candidates)
        raise RuntimeError(
            f"More than one FEM3D station_points.csv matches {problem}:\n"
            f"{candidates_text}\n"
            f"Use --{problem}-fem3d to select the reference explicitly."
        )

    return resolved


def select_rows(rows: list[dict[str, float | str]], point: str):
    selected = [row for row in rows if row["point"] == point]
    return sorted(selected, key=lambda row: float(row["x_over_L"]))


def point_coordinate_label(rows: list[dict[str, float | str]]) -> str:
    first = rows[0]
    last = rows[-1]

    y0 = float(first["y_mm"])
    z0 = float(first["z_mm"])
    y1 = float(last["y_mm"])
    z1 = float(last["z_mm"])

    if np.allclose((y0, z0), (y1, z1), rtol=0.0, atol=1.0e-12):
        return f"y,z = ({y0:g}, {z0:g}) mm"

    return f"y,z: ({y0:g}, {z0:g}) -> ({y1:g}, {z1:g}) mm"


def local_limits(values: list[np.ndarray], pad_fraction: float = 0.08):
    """Per-panel zoom retained for diagnostics of small residual components."""
    merged = np.concatenate(values)
    finite = merged[np.isfinite(merged)]

    if finite.size == 0:
        return -1.0, 1.0

    lo = float(np.min(finite))
    hi = float(np.max(finite))

    if np.isclose(lo, hi):
        scale = max(abs(lo), 1.0e-6)
        pad = 0.05 * scale
    else:
        pad = pad_fraction * (hi - lo)

    return lo - pad, hi + pad


def human_limits(values: list[np.ndarray], pad_fraction: float = 0.08):
    """Build a common physical y-scale that includes zero and all supplied values."""
    if not values:
        return -1.0e-6, 1.0e-6

    merged = np.concatenate(values)
    finite = merged[np.isfinite(merged)]
    if finite.size == 0:
        return -1.0e-6, 1.0e-6

    lo = min(float(np.min(finite)), 0.0)
    hi = max(float(np.max(finite)), 0.0)

    if np.isclose(lo, 0.0) and np.isclose(hi, 0.0):
        return -1.0e-6, 1.0e-6

    span = hi - lo
    pad = pad_fraction * span if span > 0.0 else 0.0

    plot_lo = lo - pad if lo < 0.0 else 0.0
    plot_hi = hi + pad if hi > 0.0 else 0.0

    if np.isclose(plot_lo, plot_hi):
        scale = max(abs(plot_lo), abs(plot_hi), 1.0e-6)
        return -scale, scale

    return plot_lo, plot_hi


def load_all_rows(
    cases: list[DiscoveredCase],
    fem_refs: dict[str, Path],
) -> dict[str, list[dict[str, float | str]]]:
    rows_by_case: dict[str, list[dict[str, float | str]]] = {}

    for case in cases:
        fem_stations = fem_refs[case.problem]
        rows_by_case[case.key] = join_results(case.response, fem_stations)

    return rows_by_case


def build_human_scales(
    *,
    cases: list[DiscoveredCase],
    rows_by_case: dict[str, list[dict[str, float | str]]],
    components: tuple[str, ...],
) -> dict[tuple[str, str], tuple[float, float]]:
    """Build one shared y-range per physical problem and displacement component."""
    grouped_values: dict[tuple[str, str], list[np.ndarray]] = {}

    for case in cases:
        rows = rows_by_case[case.key]
        for component in components:
            bucket = grouped_values.setdefault((case.problem, component), [])
            for point in POINT_ORDER:
                selected = select_rows(rows, point)
                if not selected:
                    continue

                fem = np.array(
                    [float(row[f"{component}_fem3d_mm"]) for row in selected],
                    dtype=float,
                )
                cuf = np.array(
                    [float(row[f"{component}_cuf_mm"]) for row in selected],
                    dtype=float,
                )
                bucket.extend((fem, cuf))

    return {
        key: human_limits(values)
        for key, values in grouped_values.items()
    }


def plot_case_component(
    *,
    case: DiscoveredCase,
    rows: list[dict[str, float | str]],
    component: str,
    output_dir: Path,
    dpi: int,
    write_pdf: bool,
    scale_mode: str,
    shared_ylim: tuple[float, float],
) -> list[Path]:
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12.6, 9.2),
        sharex=True,
        sharey=(scale_mode == "human"),
        constrained_layout=True,
    )

    first_visible_ax = None

    for ax, point in zip(axes.ravel(), POINT_ORDER):
        selected = select_rows(rows, point)
        if not selected:
            ax.set_visible(False)
            continue

        if first_visible_ax is None:
            first_visible_ax = ax

        x = np.array([float(row["x_over_L"]) for row in selected], dtype=float)
        fem = np.array(
            [float(row[f"{component}_fem3d_mm"]) for row in selected],
            dtype=float,
        )
        cuf = np.array(
            [float(row[f"{component}_cuf_mm"]) for row in selected],
            dtype=float,
        )

        ax.plot(
            x,
            fem,
            "o-",
            linewidth=1.45,
            markersize=3.4,
            color="0.20",
            label="FEM3D",
            zorder=3,
        )
        ax.plot(
            x,
            cuf,
            "s--",
            linewidth=1.35,
            markersize=3.2,
            label=f"CUF N={case.order}",
            zorder=4,
        )

        if scale_mode == "human":
            ax.set_ylim(*shared_ylim)
        else:
            ax.set_ylim(*local_limits([fem, cuf]))

        ax.set_xlim(-0.025, 1.025)
        ax.set_xticks([0.0, 0.25, 0.50, 0.75, 1.0])
        ax.axhline(0.0, color="0.55", linewidth=0.7)
        ax.grid(True, alpha=0.25)
        ax.set_title(point.replace("_", " "), fontsize=13)
        ax.text(
            0.03,
            0.04,
            point_coordinate_label(selected),
            transform=ax.transAxes,
            fontsize=8.5,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "alpha": 0.85,
                "edgecolor": "#cccccc",
            },
        )
        ax.ticklabel_format(
            style="sci",
            axis="y",
            scilimits=(-3, 4),
            useMathText=True,
        )

    scale_note = (
        "Shared physical y-scale across all discovered cases of this problem/component"
        if scale_mode == "human"
        else "Local per-panel zoom (diagnostic view)"
    )

    fig.suptitle(
        f"{case.title}\n"
        f"Longitudinal displacement {component}: CUF vs FEM3D\n"
        f"{scale_note}",
        fontsize=16,
    )
    fig.supxlabel("x/L", fontsize=14)
    fig.supylabel(f"{component} [mm]", fontsize=14)

    if first_visible_ax is not None:
        handles, labels = first_visible_ax.get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.905),
            ncol=2,
            frameon=True,
        )

    case_output_dir = output_dir / case.directory_name
    case_output_dir.mkdir(parents=True, exist_ok=True)

    output_base = case_output_dir / f"displacement_{component}_along_beam"
    outputs = [output_base.with_suffix(".png")]
    fig.savefig(outputs[0], dpi=dpi, bbox_inches="tight", pad_inches=0.10)

    if write_pdf:
        outputs.append(output_base.with_suffix(".pdf"))
        fig.savefig(outputs[-1], bbox_inches="tight", pad_inches=0.10)

    plt.close(fig)
    return outputs


def main() -> None:
    args = parse_args()

    cases = discover_cases(args.cuf_output_root)
    print(f"CUF scan root: {args.cuf_output_root.resolve()}")
    print(f"Found {len(cases)} supported response file(s):")
    for case in cases:
        print(
            f"  [{case.problem:7s}] {case.directory_name} -> {case.response}"
        )
    print()

    problems = {case.problem for case in cases}
    fem_refs = discover_fem3d_station_files(
        problems=problems,
        fem3d_root=args.fem3d_root,
        bending_fem3d=args.bending_fem3d,
        torsion_fem3d=args.torsion_fem3d,
    )

    print("FEM3D references:")
    for problem in sorted(fem_refs):
        print(f"  {problem:7s} -> {fem_refs[problem]}")
    print()

    components = COMPONENTS if args.component == "all" else (args.component,)
    rows_by_case = load_all_rows(cases, fem_refs)

    shared_scales: dict[tuple[str, str], tuple[float, float]] = {}
    if args.scale_mode == "human":
        shared_scales = build_human_scales(
            cases=cases,
            rows_by_case=rows_by_case,
            components=components,
        )
        print("Shared y-scales:")
        for (problem, component), ylim in sorted(shared_scales.items()):
            print(
                f"  {problem:7s} {component}: "
                f"{ylim[0]:.6g} .. {ylim[1]:.6g} mm"
            )
        print()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for case in cases:
        rows = rows_by_case[case.key]
        for component in components:
            shared_ylim = shared_scales.get(
                (case.problem, component),
                (-1.0e-6, 1.0e-6),
            )
            outputs = plot_case_component(
                case=case,
                rows=rows,
                component=component,
                output_dir=args.output_dir,
                dpi=args.dpi,
                write_pdf=args.pdf,
                scale_mode=args.scale_mode,
                shared_ylim=shared_ylim,
            )
            generated.extend(outputs)
            print(
                f"[ok] {case.directory_name} component={component}"
            )
            for output in outputs:
                print(f"     {output.resolve()}")

    print()
    print(f"Generated {len(generated)} file(s).")
    print(f"Output root: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()

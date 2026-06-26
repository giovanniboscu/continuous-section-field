"""Generate a CSF YAML geometry for a tapered onion-layer circular hollow pole.

The generator writes two CSF stations, S0 and S1. Each station contains:
- concentric annular concrete cells;
- discrete circular PC-bar / strand polygons on a guide radius.

The polygon order is identical at S0 and S1. This is required because CSF pairs
corresponding polygons by order, while names are used for law assignment.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


class CleanDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class Point(list):
    pass


def _repr_point(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", list(data), flow_style=True)


CleanDumper.add_representer(Point, _repr_point)


@dataclass(frozen=True)
class SectionParameters:
    z: float
    radii: list[float]
    bar_guide_radius: float


def parse_csv_floats(value: str) -> list[float]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("Expected a comma-separated list of numbers.")
    try:
        return [float(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid numeric list: {value}") from exc


def parse_csv_names(value: str) -> list[str]:
    names = [part.strip() for part in value.split(",") if part.strip()]
    if not names:
        raise argparse.ArgumentTypeError("Expected a comma-separated list of names.")
    return names


def parse_index_law(value: str) -> tuple[int, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("Expected INDEX:LAW, for example '3:w0*(1-0.2*t)'.")
    idx_text, law = value.split(":", 1)
    try:
        idx = int(idx_text.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid layer index in law entry: {value}") from exc
    law = law.strip()
    if not law:
        raise argparse.ArgumentTypeError(f"Empty law in entry: {value}")
    return idx, law


def validate_radii(radii: list[float], label: str) -> None:
    if len(radii) < 2:
        raise ValueError(f"{label} must contain at least two radii.")
    for a, b in zip(radii, radii[1:]):
        if b <= a:
            raise ValueError(f"{label} must be strictly increasing.")


def circle_loop(cx: float, cy: float, radius: float, n: int, theta0_deg: float = 0.0) -> list[list[float]]:
    if radius <= 0.0:
        raise ValueError("Circle radius must be positive.")
    if n < 3:
        raise ValueError("A circular loop requires at least three vertices.")
    theta0 = math.radians(theta0_deg)
    return [
        [cx + radius * math.cos(theta0 + 2.0 * math.pi * k / n),
         cy + radius * math.sin(theta0 + 2.0 * math.pi * k / n)]
        for k in range(n)
    ]


def close_loop(points: list[list[float]]) -> list[list[float]]:
    if not points:
        return points
    if points[0] == points[-1]:
        return points
    return points + [points[0]]


def to_points(vertices: Iterable[Iterable[float]]) -> list[Point]:
    return [Point([float(x), float(y)]) for x, y in vertices]


def disk_vertices(cx: float, cy: float, radius: float, n: int, theta0_deg: float) -> list[Point]:
    return to_points(close_loop(circle_loop(cx, cy, radius, n, theta0_deg)))


def annular_cell_vertices(
    cx: float,
    cy: float,
    inner_radius: float,
    outer_radius: float,
    n: int,
    theta0_deg: float,
) -> list[Point]:
    """Return one polygonal ring as outer loop followed by reversed inner loop."""
    if inner_radius <= 0.0:
        raise ValueError("Annular cell inner radius must be positive.")
    if outer_radius <= inner_radius:
        raise ValueError("Annular cell outer radius must be greater than inner radius.")

    outer = close_loop(circle_loop(cx, cy, outer_radius, n, theta0_deg))
    inner = close_loop(circle_loop(cx, cy, inner_radius, n, theta0_deg))
    inner_reversed = list(reversed(inner))
    return to_points(outer + inner_reversed)


def bar_vertices(
    cx: float,
    cy: float,
    guide_radius: float,
    bar_radius: float,
    bar_sides: int,
    bar_index: int,
    n_bars: int,
    theta0_deg: float,
    bar_theta0_deg: float,
) -> list[Point]:
    angle = math.radians(theta0_deg + 360.0 * bar_index / n_bars)
    bx = cx + guide_radius * math.cos(angle)
    by = cy + guide_radius * math.sin(angle)
    local_theta = math.degrees(angle) + bar_theta0_deg
    return disk_vertices(bx, by, bar_radius, bar_sides, local_theta)


def validate_bar_fit(
    radii: list[float],
    bar_guide_radius: float,
    bar_radius: float,
    host_layer_index: int,
    label: str,
) -> None:
    if host_layer_index < 0 or host_layer_index >= len(radii) - 1:
        raise ValueError(
            "bar_host_layer_index must identify a physical annular layer. "
            "For radii [r0, r1, ...], valid layer indices are 0..len(radii)-2."
        )
    r_in = radii[host_layer_index]
    r_out = radii[host_layer_index + 1]
    if bar_guide_radius - bar_radius < r_in - 1e-12:
        raise ValueError(f"Bars at {label} cross inside the selected host layer.")
    if bar_guide_radius + bar_radius > r_out + 1e-12:
        raise ValueError(f"Bars at {label} cross outside the selected host layer.")


def build_section_polygons(args, params: SectionParameters) -> dict:
    polygons: dict[str, dict] = {}
    names = args.layer_names
    weights = args.layer_weights

    # Annular concrete layers are written directly from successive radii.
    for i in range(len(names)):
        polygons[f"{names[i]}@cell"] = {
            "weight": float(weights[i]),
            "vertices": annular_cell_vertices(
                args.cx,
                args.cy,
                params.radii[i],
                params.radii[i + 1],
                args.N,
                args.theta0_deg,
            ),
        }

    # Discrete PC-bars / strands.
    if args.n_bars > 0:
        bar_radius = 0.5 * args.bar_diameter
        for j in range(args.n_bars):
            polygons[f"{args.bar_prefix}_{j:02d}"] = {
                "weight": float(args.bar_weight),
                "vertices": bar_vertices(
                    args.cx,
                    args.cy,
                    params.bar_guide_radius,
                    bar_radius,
                    args.bar_sides,
                    j,
                    args.n_bars,
                    args.theta0_deg,
                    args.bar_theta0_deg,
                ),
            }

    return polygons


def build_laws(args) -> tuple[list[str], list[str]]:
    weight_laws: list[str] = []
    shear_weight_laws: list[str] = []
    logical_names = args.layer_names

    for idx, law in args.layer_law or []:
        if idx < 0 or idx >= len(logical_names):
            raise ValueError(f"Layer law index {idx} is outside the valid range.")
        name = logical_names[idx]
        if name == "void":
            raise ValueError("The void polygon should not receive a participation law.")
        weight_laws.append(f"{name},{name}: {law}")

    for idx, law in args.layer_shear_law or []:
        if idx < 0 or idx >= len(logical_names):
            raise ValueError(f"Layer shear law index {idx} is outside the valid range.")
        name = logical_names[idx]
        if name == "void":
            raise ValueError("The void polygon should not receive a shear participation law.")
        shear_weight_laws.append(f"{name},{name}: {law}")

    # No implicit shear law is assigned. Bars only receive shear if explicitly
    # requested through --all-bars-shear-law.
    if args.all_bars_law:
        for j in range(args.n_bars):
            name = f"{args.bar_prefix}_{j:02d}"
            weight_laws.append(f"{name},{name}: {args.all_bars_law}")

    if args.all_bars_shear_law:
        for j in range(args.n_bars):
            name = f"{args.bar_prefix}_{j:02d}"
            shear_weight_laws.append(f"{name},{name}: {args.all_bars_shear_law}")

    return weight_laws, shear_weight_laws


def build_geometry(args) -> dict:
    validate_radii(args.radii0, "radii0")
    validate_radii(args.radii1, "radii1")
    if len(args.radii0) != len(args.radii1):
        raise ValueError("radii0 and radii1 must have the same count.")
    if len(args.layer_names) != len(args.radii0) - 1:
        raise ValueError("layer_names count must be len(radii)-1.")
    if len(args.layer_weights) != len(args.layer_names):
        raise ValueError("layer_weights count must match layer_names count.")
    if args.z1 <= args.z0:
        raise ValueError("z1 must be greater than z0.")
    if args.N < 16:
        raise ValueError("N should be at least 16 for this circular section case.")
    if args.n_bars < 0:
        raise ValueError("n_bars cannot be negative.")
    if args.n_bars > 0:
        if args.bar_sides < 8:
            raise ValueError("bar_sides should be at least 8.")
        bar_radius = 0.5 * args.bar_diameter
        validate_bar_fit(args.radii0, args.bar_guide_radius0, bar_radius, args.bar_host_layer_index, "S0")
        validate_bar_fit(args.radii1, args.bar_guide_radius1, bar_radius, args.bar_host_layer_index, "S1")

    s0 = SectionParameters(args.z0, args.radii0, args.bar_guide_radius0)
    s1 = SectionParameters(args.z1, args.radii1, args.bar_guide_radius1)

    data = {
        "CSF": {
            "sections": {
                "S0": {"z": float(args.z0), "polygons": build_section_polygons(args, s0)},
                "S1": {"z": float(args.z1), "polygons": build_section_polygons(args, s1)},
            }
        }
    }

    weight_laws, shear_weight_laws = build_laws(args)
    if shear_weight_laws:
        data["CSF"]["shear_weight_laws"] = shear_weight_laws
    if weight_laws:
        data["CSF"]["weight_laws"] = weight_laws

    return data


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--z0", type=float, required=True)
    parser.add_argument("--z1", type=float, required=True)
    parser.add_argument("--cx", type=float, default=0.0)
    parser.add_argument("--cy", type=float, default=0.0)
    parser.add_argument("--radii0", type=parse_csv_floats, required=True)
    parser.add_argument("--radii1", type=parse_csv_floats, required=True)
    parser.add_argument("--layer-names", type=parse_csv_names, required=True)
    parser.add_argument("--layer-weights", type=parse_csv_floats, required=True)
    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--n-bars", type=int, default=0)
    parser.add_argument("--bar-guide-radius0", type=float, default=0.0)
    parser.add_argument("--bar-guide-radius1", type=float, default=0.0)
    parser.add_argument("--bar-host-layer-index", type=int, default=2)
    parser.add_argument("--bar-diameter", type=float, default=0.0127)
    parser.add_argument("--bar-sides", type=int, default=16)
    parser.add_argument("--bar-weight", type=float, default=1.0)
    parser.add_argument("--bar-prefix", type=str, default="pcbar")
    parser.add_argument("--theta0-deg", type=float, default=0.0)
    parser.add_argument("--bar-theta0-deg", type=float, default=0.0)
    parser.add_argument("--layer-law", type=parse_index_law, action="append", default=None)
    parser.add_argument(
        "--layer-shear-law",
        type=parse_index_law,
        action="append",
        default=None,
        help=(
            "Assign an explicit shear/torsion law to a layer by index. "
            "Use T_lookup(...) or iso(<nu>) and do not rely on any implicit default."
        ),
    )
    parser.add_argument("--all-bars-law", type=str, default="")
    parser.add_argument(
        "--all-bars-shear-law",
        type=str,
        default="",
        help=(
            "Assign an explicit shear/torsion law to all bars. "
            "Use T_lookup(...) or iso(<nu>) explicitly."
        ),
    )
    parser.add_argument("--out", type=Path, default=Path("tapered_pc_pole_onion.yaml"))
    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    data = build_geometry(args)
    with args.out.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=CleanDumper, sort_keys=False, default_flow_style=False)

    print(f"File generated successfully: {args.out}")
    print(f"Layers: {len(args.layer_names) - 1}")
    print(f"Bars: {args.n_bars}")
    print(f"S0 outer radius: {args.radii0[-1]:.6f} m")
    print(f"S1 outer radius: {args.radii1[-1]:.6f} m")


if __name__ == "__main__":
    main()

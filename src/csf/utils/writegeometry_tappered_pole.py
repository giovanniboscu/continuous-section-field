"""Generate a CSF YAML geometry for a tapered circular hollow pole
with radial onion levels split into angular sector cells.

Naming convention used by this generator:
- concrete polygon id: <sector>_<level>_<type>
- steel polygon id:    <bar>_<host_level>_S

where:
- sector/bar numbering starts from 0;
- level is one-based and follows the radial order of the input radii;
- type is C for concrete, CH for the concrete host level of the bars, S for steel.

The polygon order is identical at S0 and S1. CSF pairs corresponding polygons by
order, while names are used for law assignment.
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
        raise argparse.ArgumentTypeError("Expected INDEX:LAW, for example '3:w0*T_lookup(...)'.")
    idx_text, law = value.split(":", 1)
    try:
        idx = int(idx_text.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid layer index in law entry: {value}") from exc
    law = law.strip()
    if not law:
        raise argparse.ArgumentTypeError(f"Empty law in entry: {value}")
    return idx, law


def parse_sector_law(value: str) -> tuple[int, int, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "Expected LAYER_INDEX:SECTOR_INDEX:LAW, for example '2:7:w0*T_lookup(...)'."
        )
    layer_text, sector_text, law = parts
    try:
        layer_idx = int(layer_text.strip())
        sector_idx = int(sector_text.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid layer/sector index in law entry: {value}") from exc
    law = law.strip()
    if not law:
        raise argparse.ArgumentTypeError(f"Empty law in entry: {value}")
    return layer_idx, sector_idx, law


def parse_bar_law(value: str) -> tuple[int, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("Expected BAR_INDEX:LAW, for example '8:w0*T_lookup(...)'.")
    idx_text, law = value.split(":", 1)
    try:
        idx = int(idx_text.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid bar index in law entry: {value}") from exc
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


def close_loop(points: list[list[float]]) -> list[list[float]]:
    if not points:
        return points
    if points[0] == points[-1]:
        return points
    return points + [points[0]]


def to_points(vertices: Iterable[Iterable[float]]) -> list[Point]:
    return [Point([float(x), float(y)]) for x, y in vertices]


def arc_points(
    cx: float,
    cy: float,
    radius: float,
    theta_a: float,
    theta_b: float,
    n_steps: int,
) -> list[list[float]]:
    if radius <= 0.0:
        raise ValueError("Arc radius must be positive.")
    if n_steps < 1:
        raise ValueError("arc_steps must be at least 1.")

    return [
        [
            cx + radius * math.cos(theta_a + (theta_b - theta_a) * k / n_steps),
            cy + radius * math.sin(theta_a + (theta_b - theta_a) * k / n_steps),
        ]
        for k in range(n_steps + 1)
    ]


def annular_sector_vertices(
    cx: float,
    cy: float,
    inner_radius: float,
    outer_radius: float,
    theta_a: float,
    theta_b: float,
    arc_steps: int,
) -> list[Point]:
    if inner_radius <= 0.0:
        raise ValueError("Sector inner radius must be positive.")
    if outer_radius <= inner_radius:
        raise ValueError("Sector outer radius must be greater than inner radius.")
    if theta_b <= theta_a:
        raise ValueError("Sector end angle must be greater than start angle.")

    outer = arc_points(cx, cy, outer_radius, theta_a, theta_b, arc_steps)
    inner = arc_points(cx, cy, inner_radius, theta_a, theta_b, arc_steps)
    vertices = outer + list(reversed(inner))
    return to_points(close_loop(vertices))


def circle_loop(cx: float, cy: float, radius: float, n: int, theta0_deg: float = 0.0) -> list[list[float]]:
    if radius <= 0.0:
        raise ValueError("Circle radius must be positive.")
    if n < 3:
        raise ValueError("A circular loop requires at least three vertices.")
    theta0 = math.radians(theta0_deg)
    return [
        [
            cx + radius * math.cos(theta0 + 2.0 * math.pi * k / n),
            cy + radius * math.sin(theta0 + 2.0 * math.pi * k / n),
        ]
        for k in range(n)
    ]


def disk_vertices(cx: float, cy: float, radius: float, n: int, theta0_deg: float) -> list[Point]:
    return to_points(close_loop(circle_loop(cx, cy, radius, n, theta0_deg)))


def concrete_sector_name(sector_index: int, layer_index: int, bar_host_layer_index: int) -> str:
    level = layer_index + 1
    polygon_type = "CH" if layer_index == bar_host_layer_index else "C"
    return f"{sector_index}_{level}_{polygon_type}"


def bar_name(bar_index: int, bar_host_layer_index: int) -> str:
    host_level = bar_host_layer_index + 1
    return f"{bar_index}_{host_level}_S"


def bar_vertices(
    cx: float,
    cy: float,
    guide_radius: float,
    bar_radius: float,
    bar_sides: int,
    bar_index: int,
    n_bars: int,
    theta0_deg: float,
    center_offset_deg: float,
    bar_theta0_deg: float,
) -> list[Point]:
    angle_deg = theta0_deg + center_offset_deg + 360.0 * bar_index / n_bars
    angle = math.radians(angle_deg)
    bx = cx + guide_radius * math.cos(angle)
    by = cy + guide_radius * math.sin(angle)
    local_theta = angle_deg + bar_theta0_deg
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


def validate_sector_index(layer_idx: int, sector_idx: int, n_layers: int, n_sectors: int, label: str) -> None:
    if layer_idx < 0 or layer_idx >= n_layers:
        raise ValueError(f"{label}: layer index {layer_idx} is outside the valid range.")
    if sector_idx < 0 or sector_idx >= n_sectors:
        raise ValueError(f"{label}: sector index {sector_idx} is outside the valid range.")


def validate_bar_index(bar_idx: int, n_bars: int, label: str) -> None:
    if bar_idx < 0 or bar_idx >= n_bars:
        raise ValueError(f"{label}: bar index {bar_idx} is outside the valid range.")


def generated_concrete_names(args) -> list[str]:
    names: list[str] = []
    for layer_idx in range(len(args.radii0) - 1):
        for sector_idx in range(args.N):
            names.append(concrete_sector_name(sector_idx, layer_idx, args.bar_host_layer_index))
    return names


def generated_bar_names(args) -> list[str]:
    if args.n_bars <= 0:
        return []
    return [bar_name(j, args.bar_host_layer_index) for j in range(args.n_bars)]


def build_section_polygons(args, params: SectionParameters) -> dict:
    polygons: dict[str, dict] = {}
    dtheta = 2.0 * math.pi / args.N
    theta0 = math.radians(args.theta0_deg)

    n_layers = len(params.radii) - 1
    for layer_idx in range(n_layers):
        inner_radius = params.radii[layer_idx]
        outer_radius = params.radii[layer_idx + 1]
        base_weight = float(args.layer_weights[layer_idx])

        for sector_idx in range(args.N):
            theta_a = theta0 + sector_idx * dtheta
            theta_b = theta0 + (sector_idx + 1) * dtheta
            name = concrete_sector_name(sector_idx, layer_idx, args.bar_host_layer_index)
            polygons[name] = {
                "weight": base_weight,
                "vertices": annular_sector_vertices(
                    args.cx,
                    args.cy,
                    inner_radius,
                    outer_radius,
                    theta_a,
                    theta_b,
                    args.arc_steps,
                ),
            }

    if args.n_bars > 0:
        bar_radius = 0.5 * args.bar_diameter
        center_offset_deg = (
            args.bar_center_offset_deg
            if args.bar_center_offset_deg is not None
            else 180.0 / args.N
        )
        for j in range(args.n_bars):
            name = bar_name(j, args.bar_host_layer_index)
            polygons[name] = {
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
                    center_offset_deg,
                    args.bar_theta0_deg,
                ),
            }

    return polygons


def add_law_entry(laws: dict[str, str], name: str, law: str) -> None:
    if law:
        laws[name] = law


def law_strings_from_map(laws: dict[str, str]) -> list[str]:
    return [f"{name},{name}: {law}" for name, law in laws.items()]


def build_laws(args) -> tuple[list[str], list[str]]:
    n_layers = len(args.radii0) - 1
    n_sectors = args.N

    weight_laws: dict[str, str] = {}
    shear_weight_laws: dict[str, str] = {}

    for layer_idx, law in args.layer_law or []:
        if layer_idx < 0 or layer_idx >= n_layers:
            raise ValueError(f"Layer law index {layer_idx} is outside the valid range.")
        for sector_idx in range(n_sectors):
            add_law_entry(
                weight_laws,
                concrete_sector_name(sector_idx, layer_idx, args.bar_host_layer_index),
                law,
            )

    for layer_idx, sector_idx, law in args.sector_law or []:
        validate_sector_index(layer_idx, sector_idx, n_layers, n_sectors, "sector_law")
        name = concrete_sector_name(sector_idx, layer_idx, args.bar_host_layer_index)
        add_law_entry(weight_laws, name, law)

    for layer_idx, law in args.layer_shear_law or []:
        if layer_idx < 0 or layer_idx >= n_layers:
            raise ValueError(f"Layer shear law index {layer_idx} is outside the valid range.")
        for sector_idx in range(n_sectors):
            add_law_entry(
                shear_weight_laws,
                concrete_sector_name(sector_idx, layer_idx, args.bar_host_layer_index),
                law,
            )

    for layer_idx, sector_idx, law in args.sector_shear_law or []:
        validate_sector_index(layer_idx, sector_idx, n_layers, n_sectors, "sector_shear_law")
        name = concrete_sector_name(sector_idx, layer_idx, args.bar_host_layer_index)
        add_law_entry(shear_weight_laws, name, law)

    if args.all_bars_law:
        for name in generated_bar_names(args):
            add_law_entry(weight_laws, name, args.all_bars_law)

    for bar_idx, law in args.bar_law or []:
        validate_bar_index(bar_idx, args.n_bars, "bar_law")
        add_law_entry(weight_laws, bar_name(bar_idx, args.bar_host_layer_index), law)

    if args.all_bars_shear_law:
        for name in generated_bar_names(args):
            add_law_entry(shear_weight_laws, name, args.all_bars_shear_law)

    for bar_idx, law in args.bar_shear_law or []:
        validate_bar_index(bar_idx, args.n_bars, "bar_shear_law")
        add_law_entry(shear_weight_laws, bar_name(bar_idx, args.bar_host_layer_index), law)

    return law_strings_from_map(weight_laws), law_strings_from_map(shear_weight_laws)


def build_geometry(args) -> dict:
    validate_radii(args.radii0, "radii0")
    validate_radii(args.radii1, "radii1")
    if len(args.radii0) != len(args.radii1):
        raise ValueError("radii0 and radii1 must have the same count.")
    if len(args.layer_weights) != len(args.radii0) - 1:
        raise ValueError("layer_weights count must match len(radii)-1.")
    if args.z1 <= args.z0:
        raise ValueError("z1 must be greater than z0.")
    if args.N < 1:
        raise ValueError("N must be at least 1.")
    if args.arc_steps < 1:
        raise ValueError("arc_steps must be at least 1.")
    if args.n_bars < 0:
        raise ValueError("n_bars cannot be negative.")

    if args.n_bars > 0:
        if args.bar_sides < 8:
            raise ValueError("bar_sides should be at least 8.")
        if args.n_bars != args.N and args.bar_center_offset_deg is None:
            raise ValueError(
                "When n_bars differs from N, pass --bar-center-offset-deg explicitly."
            )
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

    return data


def commented_law_blocks(weight_laws: list[str], shear_weight_laws: list[str]) -> str:
    lines: list[str] = []
    if shear_weight_laws:
        lines.append("# shear_weight_laws:")
        for entry in shear_weight_laws:
            lines.append(f"# - '{entry}'")
        lines.append("")
    if weight_laws:
        lines.append("# weight_laws:")
        for entry in weight_laws:
            lines.append(f"# - '{entry}'")
    return "\n".join(lines)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--z0", type=float, required=True)
    parser.add_argument("--z1", type=float, required=True)
    parser.add_argument("--cx", type=float, default=0.0)
    parser.add_argument("--cy", type=float, default=0.0)
    parser.add_argument("--radii0", type=parse_csv_floats, required=True)
    parser.add_argument("--radii1", type=parse_csv_floats, required=True)
    parser.add_argument("--layer-names", type=parse_csv_names, default=None)
    parser.add_argument("--layer-weights", type=parse_csv_floats, required=True)
    parser.add_argument(
        "--N",
        type=int,
        required=True,
        help="Number of angular sectors for the concrete sector grid.",
    )
    parser.add_argument(
        "--arc-steps",
        type=int,
        default=8,
        help="Number of segments used to approximate each curved side of a sector cell.",
    )
    parser.add_argument("--n-bars", type=int, default=0)
    parser.add_argument("--bar-guide-radius0", type=float, default=0.0)
    parser.add_argument("--bar-guide-radius1", type=float, default=0.0)
    parser.add_argument("--bar-host-layer-index", type=int, default=1)
    parser.add_argument("--bar-diameter", type=float, default=0.0127)
    parser.add_argument("--bar-sides", type=int, default=16)
    parser.add_argument("--bar-weight", type=float, default=1.0)
    parser.add_argument("--bar-prefix", type=str, default="")
    parser.add_argument("--theta0-deg", type=float, default=90.0)
    parser.add_argument(
        "--bar-center-offset-deg",
        type=float,
        default=None,
        help=(
            "Angular offset for bar centres. If omitted, bars are shifted by half "
            "one concrete sector: 180/N degrees."
        ),
    )
    parser.add_argument("--bar-theta0-deg", type=float, default=0.0)

    parser.add_argument("--layer-law", type=parse_index_law, action="append", default=None)
    parser.add_argument("--sector-law", type=parse_sector_law, action="append", default=None)
    parser.add_argument("--all-bars-law", type=str, default="")
    parser.add_argument("--bar-law", type=parse_bar_law, action="append", default=None)

    parser.add_argument("--layer-shear-law", type=parse_index_law, action="append", default=None)
    parser.add_argument("--sector-shear-law", type=parse_sector_law, action="append", default=None)
    parser.add_argument("--all-bars-shear-law", type=str, default="")
    parser.add_argument("--bar-shear-law", type=parse_bar_law, action="append", default=None)

    parser.add_argument("--out", type=Path, default=Path("tapered_pc_pole_sectorgrid_centered.yaml"))
    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    data = build_geometry(args)

    weight_laws, shear_weight_laws = build_laws(args)
    comment_block = commented_law_blocks(weight_laws, shear_weight_laws)

    with args.out.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=CleanDumper, sort_keys=False, default_flow_style=False)
        if comment_block:
            f.write("\n")
            f.write(comment_block)
            f.write("\n")

    n_layers = len(args.radii0) - 1
    concrete_polygons = n_layers * args.N
    total_polygons = concrete_polygons + args.n_bars
    center_offset_deg = (
        args.bar_center_offset_deg
        if args.bar_center_offset_deg is not None
        else 180.0 / args.N
    )

    print(f"File generated successfully: {args.out}")
    print(f"Radial levels: {n_layers}")
    print(f"Angular sectors: {args.N}")
    print(f"Concrete polygons per station: {concrete_polygons}")
    print(f"Bars: {args.n_bars}")
    print(f"Total polygons per station: {total_polygons}")
    print(f"Bar centre angular offset: {center_offset_deg:.12g} deg")
    print(f"S0 outer radius: {args.radii0[-1]:.6f} m")
    print(f"S1 outer radius: {args.radii1[-1]:.6f} m")


if __name__ == "__main__":
    main()

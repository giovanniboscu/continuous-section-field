"""
CSF-SP complex @wall verification example.

Purpose
-------
This script verifies a complex open thin-walled built-up section using CSF
@wall polygons and the csf_sp / sectionproperties integration path.

The verification compares two equivalent CSF models:

1) Ordinary reference model
   - finite-thickness rectangular plates;
   - no @wall tags;
   - used as the geometric reference.

2) Tagged @wall model
   - the same finite-thickness rectangular plates;
   - each plate is tagged as @wall@t=...;
   - passed through csf_sp to sectionproperties;
   - used by CSF to activate J_sv_wall.

The plates are non-overlapping. They may share boundaries, but no area is
double-counted.

The geometry is uniformly scaled from S0 to S1, so the benchmark also checks
longitudinal interpolation consistency.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt

from csf import (
    ContinuousSectionField,
    Polygon,
    Pt,
    Section,
    section_full_analysis,
)
from csf.utils.csf_sp import analyse


Z0 = 0.0
Z1 = 10.0

DEFAULT_MESH_SIZE = 0.03
DEFAULT_Z_STATIONS = (0.0, 2.5, 5.0, 7.5, 10.0)

GEOM_ABS_TOL = 1.0e-8
GEOM_REL_TOL = 1.0e-6

TORSION_ABS_TOL = 1.0e-6
TORSION_REL_TOL = 2.0e-1


# ---------------------------------------------------------------------------
# Numeric helpers.
# ---------------------------------------------------------------------------
def _safe_rel_delta(delta: float, reference: float) -> float:
    """Return a relative delta.

    When the reference is zero, the relative delta is not meaningful. In that
    case this helper returns zero and the absolute tolerance decides the row.
    """
    if abs(reference) == 0.0:
        return 0.0
    return delta / reference


def _principal_from_inertia(ix: float, iy: float, ixy: float) -> Tuple[float, float]:
    """Compute principal second moments from centroidal Ix, Iy and Ixy."""
    avg = 0.5 * (ix + iy)
    rad = math.sqrt((0.5 * (ix - iy)) ** 2 + ixy**2)
    return avg + rad, avg - rad


def _format_float(value: float) -> str:
    """Format one numeric value for compact text and Markdown reports."""
    return f"{value:.12e}"


def _extract_first(value):
    """Return the first component when CSF returns a tuple-valued property."""
    if isinstance(value, tuple):
        return value[0]
    return value


def _get_sp_ej(sec_sp) -> float:
    """Return sectionproperties composite torsion stiffness e.j."""
    if hasattr(sec_sp, "get_ej"):
        return float(sec_sp.get_ej())

    raise AttributeError(
        "sectionproperties object does not expose get_ej(); "
        "cannot extract composite torsion result e.j."
    )


def _comparison_rows(
    csf_result: Dict[str, float],
    sp_result: Dict[str, float],
    keys: Sequence[str],
    abs_tol: float,
    rel_tol: float,
) -> List[Tuple[str, float, float, float, float, bool]]:
    """Build comparison rows: name, CSF, SP, delta, relative delta, pass flag."""
    rows = []

    for key in keys:
        csf_value = float(csf_result[key])
        sp_value = float(sp_result[key])
        delta = csf_value - sp_value
        rel_delta = _safe_rel_delta(delta, sp_value)
        pass_flag = abs(delta) <= abs_tol or abs(rel_delta) <= rel_tol
        rows.append((key, csf_value, sp_value, delta, rel_delta, pass_flag))

    return rows


def _rows_to_text(title: str, rows: Sequence[Tuple[str, float, float, float, float, bool]]) -> str:
    """Render comparison rows as a fixed-width text table."""
    lines = [
        "",
        title,
        f"{'Property':<14} {'CSF':>20} {'SP':>20} {'Delta':>20} {'RelDelta':>14} {'OK':>5}",
        "-" * 101,
    ]

    for name, csf_value, sp_value, delta, rel_delta, pass_flag in rows:
        lines.append(
            f"{name:<14} "
            f"{csf_value:>20.12e} "
            f"{sp_value:>20.12e} "
            f"{delta:>20.12e} "
            f"{rel_delta:>14.6e} "
            f"{str(pass_flag):>5}"
        )

    return "\n".join(lines)


def _rows_to_markdown(
    title: str,
    rows: Sequence[Tuple[str, float, float, float, float, bool]],
) -> str:
    """Render comparison rows as a Markdown table."""
    lines = [
        f"### {title}",
        "",
        "| Property | CSF | SP | Delta | RelDelta | OK |",
        "|---|---:|---:|---:|---:|:---:|",
    ]

    for name, csf_value, sp_value, delta, rel_delta, pass_flag in rows:
        lines.append(
            "| "
            f"{name} | "
            f"{_format_float(csf_value)} | "
            f"{_format_float(sp_value)} | "
            f"{_format_float(delta)} | "
            f"{rel_delta:.6e} | "
            f"{'yes' if pass_flag else 'no'} |"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Geometry helpers.
# ---------------------------------------------------------------------------
def _rect(x0: float, x1: float, y0: float, y1: float) -> Tuple[Pt, Pt, Pt, Pt]:
    """Return a CCW rectangle."""
    return (
        Pt(x0, y0),
        Pt(x1, y0),
        Pt(x1, y1),
        Pt(x0, y1),
    )


def _scale_vertices(vertices: Sequence[Pt], scale: float) -> Tuple[Pt, ...]:
    """Uniformly scale a vertex sequence."""
    return tuple(Pt(p.x * scale, p.y * scale) for p in vertices)


def _polygon(vertices: Sequence[Pt], weight: float, name: str) -> Polygon:
    """Create one CSF polygon."""
    return Polygon(vertices=tuple(vertices), weight=weight, name=name)


def _make_complex_wall_polygons(scale: float, tagged: bool) -> Tuple[Polygon, ...]:
    """Create a non-overlapping complex open built-up wall section.

    All plates are rectangles. Adjacent plates may share boundaries. No plate
    overlaps another plate in area.

    The dimensions below are base dimensions at scale = 1.0. All coordinates
    and thickness tags are uniformly scaled for S1.
    """
    web_t = 0.36
    flange_t = 0.52
    side_t = 0.30
    lip_t = 0.24
    lower_plate_t = 0.22

    parts = [
        # Main web.
        (
            "central_web",
            _rect(-0.5 * web_t, 0.5 * web_t, -4.10, 4.10),
            web_t,
        ),

        # Flanges. They touch the web only along y = +/-4.10 boundaries.
        (
            "top_flange",
            _rect(-3.00, 3.00, 4.10, 4.62),
            flange_t,
        ),
        (
            "bottom_flange",
            _rect(-2.60, 2.60, -4.62, -4.10),
            flange_t,
        ),

        # Upper stiffeners. They are outside the web strip in x and below the
        # top flange, so they do not overlap either the web or the flange.
        (
            "upper_left_stiffener",
            _rect(-1.95, -1.65, 2.45, 4.10),
            side_t,
        ),
        (
            "upper_right_stiffener",
            _rect(1.62, 1.92, 2.05, 4.10),
            side_t,
        ),

        # Lower stiffeners. They are outside the web strip in x and above the
        # bottom flange, so they do not overlap either the web or the flange.
        (
            "lower_left_stiffener",
            _rect(-1.45, -1.15, -4.10, -2.20),
            side_t,
        ),
        (
            "lower_right_stiffener",
            _rect(1.25, 1.55, -4.10, -2.55),
            side_t,
        ),

        # Top lip plates. They touch the top flange along y = 4.62.
        (
            "top_left_lip",
            _rect(-3.00, -2.76, 4.62, 5.22),
            lip_t,
        ),
        (
            "top_right_lip",
            _rect(2.76, 3.00, 4.62, 5.05),
            lip_t,
        ),

        # Lower offset plate. It touches the lower-right stiffener along x=1.25
        # but does not overlap it.
        (
            "lower_offset_plate",
            _rect(0.45, 1.25, -3.05, -2.83),
            lower_plate_t,
        ),
    ]

    polygons = []

    for name, vertices, thickness in parts:
        scaled_vertices = _scale_vertices(vertices, scale)
        scaled_thickness = thickness * scale

        if tagged:
            poly_name = f"{name}@wall@t={scaled_thickness:.12g}"
        else:
            poly_name = name

        polygons.append(_polygon(scaled_vertices, 1.0, poly_name))

    return tuple(polygons)


def build_fields() -> Tuple[ContinuousSectionField, ContinuousSectionField]:
    """Build ordinary reference field and tagged @wall field."""
    ordinary_s0 = Section(
        polygons=_make_complex_wall_polygons(scale=1.0, tagged=False),
        z=Z0,
    )
    ordinary_s1 = Section(
        polygons=_make_complex_wall_polygons(scale=0.86, tagged=False),
        z=Z1,
    )

    wall_s0 = Section(
        polygons=_make_complex_wall_polygons(scale=1.0, tagged=True),
        z=Z0,
    )
    wall_s1 = Section(
        polygons=_make_complex_wall_polygons(scale=0.86, tagged=True),
        z=Z1,
    )

    ordinary_field = ContinuousSectionField(section0=ordinary_s0, section1=ordinary_s1)
    wall_field = ContinuousSectionField(section0=wall_s0, section1=wall_s1)

    return ordinary_field, wall_field


# ---------------------------------------------------------------------------
# Result extraction.
# ---------------------------------------------------------------------------
def extract_sp_results(sec_sp) -> Dict[str, float]:
    """Extract sectionproperties composite results and derived quantities."""
    area = sec_sp.get_ea()
    cx, cy = sec_sp.get_c()
    ix, iy, ixy = sec_sp.get_eic()

    ip = ix + iy
    i1, i2 = _principal_from_inertia(ix, iy, ixy)
    rx = math.sqrt(ix / area)
    ry = math.sqrt(iy / area)
    ej = _get_sp_ej(sec_sp)

    return {
        "A": area,
        "Cx": cx,
        "Cy": cy,
        "Ix": ix,
        "Iy": iy,
        "Ixy": ixy,
        "Ip": ip,
        "I1": i1,
        "I2": i2,
        "rx": rx,
        "ry": ry,
        "e.j": ej,
    }


def extract_csf_results(field: ContinuousSectionField, z: float) -> Dict[str, float]:
    """Run CSF section analysis at one station."""
    return section_full_analysis(field.section(z))


# ---------------------------------------------------------------------------
# Main verification routine.
# ---------------------------------------------------------------------------
def run_verification(
    z_stations: Iterable[float],
    mesh_size: float,
    report_path: Path,
    plot: bool,
) -> bool:
    """Run the complex @wall verification and write a Markdown report."""
    ordinary_field, wall_field = build_fields()

    geometry_keys = ("A", "Cx", "Cy", "Ix", "Iy", "Ixy", "Ip", "I1", "I2", "rx", "ry")

    all_geometry_rows = []
    all_torsion_rows = []
    text_blocks = []

    markdown_blocks = [
        "# CSF-SP Complex @wall Verification Report",
        "",
        "Source code: [`csf_sp_wall_complex_verification.py`](./csf_sp_wall_complex_verification.py)",
        "",
        "## Model",
        "",
        "This benchmark verifies a complex open built-up thin-walled section.",
        "",
        "The section is represented by several non-overlapping finite-thickness "
        "rectangular wall plates. The plates may share boundaries, but no plate "
        "area is intentionally overlapped.",
        "",
        "Two CSF fields are used:",
        "",
        "1. an ordinary reference field with the same wall plates and no `@wall` tags;",
        "2. a tagged field with the same wall plates named as `@wall@t=...` polygons.",
        "",
        "The geometry is uniformly scaled from S0 to S1. The comparison is made "
        "at multiple stations along `z`.",
        "",
        f"Geometry absolute tolerance: `{GEOM_ABS_TOL:.1e}`",
        f"Geometry relative tolerance: `{GEOM_REL_TOL:.1e}`",
        f"Torsion absolute tolerance: `{TORSION_ABS_TOL:.1e}`",
        f"Torsion relative tolerance: `{TORSION_REL_TOL:.1e}`",
        f"Mesh size: `{mesh_size:.6g}`",
        "",
    ]

    z_stations = tuple(z_stations)

    for z in z_stations:
        csf_ordinary = extract_csf_results(ordinary_field, z)
        csf_wall = extract_csf_results(wall_field, z)

        print(f"\nStarting sectionproperties analysis at z = {z} with mesh = {mesh_size}")
        sec_sp = analyse(wall_field, z=z, mesh=mesh_size)

        if plot:
            ax = sec_sp.geometry.plot_geometry(
                labels=("points", "facets", "control_points"),
                cp=True,
            )
            ax.set_title(f"complex @wall sectionproperties geometry at z = {z}")
            ax.set_aspect("equal", adjustable="box")
            plt.show(block=True)

            ax = sec_sp.plot_mesh(materials=False)
            ax.set_title(f"complex @wall sectionproperties mesh at z = {z}")
            ax.set_aspect("equal", adjustable="box")
            plt.show(block=True)

        sp_result = extract_sp_results(sec_sp)

        geometry_rows = _comparison_rows(
            csf_ordinary,
            sp_result,
            geometry_keys,
            GEOM_ABS_TOL,
            GEOM_REL_TOL,
        )

        csf_j_wall = float(_extract_first(csf_wall["J_sv_wall"]))
        torsion_rows = _comparison_rows(
            {"J_sv_wall": csf_j_wall},
            {"J_sv_wall": sp_result["e.j"]},
            ("J_sv_wall",),
            TORSION_ABS_TOL,
            TORSION_REL_TOL,
        )

        all_geometry_rows.extend((z, *row) for row in geometry_rows)
        all_torsion_rows.extend((z, *row) for row in torsion_rows)

        geom_title = f"Geometric check: CSF ordinary complex wall vs csf_sp @wall at z = {z}"
        torsion_title = f"Torsion check: CSF J_sv_wall vs sectionproperties e.j at z = {z}"

        text_blocks.append(_rows_to_text(geom_title, geometry_rows))
        text_blocks.append(_rows_to_text(torsion_title, torsion_rows))
        text_blocks.append("")
        text_blocks.append("Expected @wall torsion flags")
        text_blocks.append(f"J_sv_wall: {csf_wall['J_sv_wall']}")
        text_blocks.append(f"J_sv_cell: {csf_wall['J_sv_cell']}")

        markdown_blocks.append(_rows_to_markdown(geom_title, geometry_rows))
        markdown_blocks.append("")
        markdown_blocks.append(_rows_to_markdown(torsion_title, torsion_rows))
        markdown_blocks.append("")
        markdown_blocks.append("Expected `@wall` torsion flags:")
        markdown_blocks.append("")
        markdown_blocks.append(f"- `J_sv_wall`: `{csf_wall['J_sv_wall']}`")
        markdown_blocks.append(f"- `J_sv_cell`: `{csf_wall['J_sv_cell']}`")
        markdown_blocks.append("")

    max_geom_abs = max(abs(row[4]) for row in all_geometry_rows)
    max_geom_rel = max(abs(row[5]) for row in all_geometry_rows)
    max_torsion_abs = max(abs(row[4]) for row in all_torsion_rows)
    max_torsion_rel = max(abs(row[5]) for row in all_torsion_rows)

    failed_geometry = [row for row in all_geometry_rows if not row[6]]
    failed_torsion = [row for row in all_torsion_rows if not row[6]]

    passed = len(failed_geometry) == 0 and len(failed_torsion) == 0

    summary = [
        "",
        "GLOBAL SUMMARY",
        "==============",
        f"stations checked: {len(z_stations)}",
        f"geometry properties per station: {len(geometry_keys)}",
        f"maximum geometry absolute delta: {max_geom_abs:.12e}",
        f"maximum geometry relative delta: {max_geom_rel:.6e}",
        f"maximum torsion absolute delta: {max_torsion_abs:.12e}",
        f"maximum torsion relative delta: {max_torsion_rel:.6e}",
        f"overall status: {'PASS' if passed else 'FAIL'}",
    ]

    text_blocks.extend(summary)

    markdown_blocks.extend(
        [
            "## Global summary",
            "",
            f"- Stations checked: `{len(z_stations)}`",
            f"- Geometry properties per station: `{len(geometry_keys)}`",
            f"- Maximum geometry absolute delta: `{max_geom_abs:.12e}`",
            f"- Maximum geometry relative delta: `{max_geom_rel:.6e}`",
            f"- Maximum torsion absolute delta: `{max_torsion_abs:.12e}`",
            f"- Maximum torsion relative delta: `{max_torsion_rel:.6e}`",
            f"- Overall status: `{'PASS' if passed else 'FAIL'}`",
            "",
        ]
    )

    if failed_geometry or failed_torsion:
        markdown_blocks.append("## Failed rows")
        markdown_blocks.append("")
        markdown_blocks.append("| Group | z | Property | Delta | RelDelta |")
        markdown_blocks.append("|---|---:|---|---:|---:|")

        for z, name, _csf_value, _sp_value, delta, rel_delta, _pass_flag in failed_geometry:
            markdown_blocks.append(
                f"| geometry | {z:.6g} | {name} | {_format_float(delta)} | {rel_delta:.6e} |"
            )

        for z, name, _csf_value, _sp_value, delta, rel_delta, _pass_flag in failed_torsion:
            markdown_blocks.append(
                f"| torsion | {z:.6g} | {name} | {_format_float(delta)} | {rel_delta:.6e} |"
            )

        markdown_blocks.append("")

    report_path.write_text("\n".join(markdown_blocks), encoding="utf-8")

    print("\n".join(text_blocks))
    print(f"\nMarkdown report written to: {report_path}")

    return passed


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a complex CSF-SP @wall verification case."
    )
    parser.add_argument(
        "--mesh",
        type=float,
        default=DEFAULT_MESH_SIZE,
        help=f"sectionproperties mesh size. Default: {DEFAULT_MESH_SIZE}",
    )
    parser.add_argument(
        "--z",
        type=float,
        nargs="*",
        default=list(DEFAULT_Z_STATIONS),
        help="z stations to check. Default: 0.0 2.5 5.0 7.5 10.0",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("csf_sp_wall_complex_verification_report.md"),
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Show sectionproperties geometry and mesh plots at each station.",
    )
    return parser.parse_args()


def main() -> int:
    """Program entry point."""
    args = parse_args()

    passed = run_verification(
        z_stations=tuple(args.z),
        mesh_size=args.mesh,
        report_path=args.report,
        plot=args.plot,
    )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

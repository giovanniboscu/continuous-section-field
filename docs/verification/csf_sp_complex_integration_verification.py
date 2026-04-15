"""
CSF-SP complex integration verification example.

Purpose
-------
This script validates a non-prismatic CSF section against the csf_sp /
sectionproperties path at multiple stations along z.

The model is intentionally more complex than a single hole case:
- one irregular outer boundary;
- two explicit voids with weight = 0.0;
- one locally stiffer insert with weight = 1.8;
- one locally degraded insert with weight = 0.35;
- all polygons vary from S0 to S1 with matching vertex counts.

No @cell polygon is used here. This is an ordinary CSF geometry test.

The script compares stiffness-weighted sectionproperties quantities against
the corresponding CSF homogenized geometric quantities. Since csf_sp builds a
material-based sectionproperties model, sectionproperties exposes composite
quantities through get_ea(), get_eic(), etc.

In this validation, the effective material scale is the CSF polygon weight.
Therefore:
- get_ea()  is compared with CSF A;
- get_eic() is compared with CSF Ix, Iy and Ixy.

The script prints a detailed report and also writes a Markdown report file.
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

DEFAULT_MESH_SIZE = 2.0e-4
DEFAULT_Z_STATIONS = (0.0, 2.5, 5.0, 7.5, 10.0)

ABS_TOL = 1.0e-9
REL_TOL = 1.0e-7


# ---------------------------------------------------------------------------
# Basic report helpers.
# ---------------------------------------------------------------------------
def _safe_rel_delta(delta: float, reference: float) -> float:
    """Return a relative delta, using zero only when the reference is zero."""
    if abs(reference) == 0.0:
        return 0.0
    return delta / reference


def _principal_from_inertia(ix: float, iy: float, ixy: float) -> Tuple[float, float]:
    """Compute principal second moments from centroidal Ix, Iy and Ixy."""
    avg = 0.5 * (ix + iy)
    rad = math.sqrt((0.5 * (ix - iy)) ** 2 + ixy**2)
    return avg + rad, avg - rad


def _format_float(value: float) -> str:
    """Format one numeric value for a compact text report."""
    return f"{value:.12e}"


def _comparison_rows(
    csf_result: Dict[str, float],
    sp_result: Dict[str, float],
    keys: Sequence[str],
) -> List[Tuple[str, float, float, float, float, bool]]:
    """Build comparison rows: name, CSF, SP, delta, relative delta, pass flag."""
    rows = []

    for key in keys:
        csf_value = float(csf_result[key])
        sp_value = float(sp_result[key])
        delta = csf_value - sp_value
        rel_delta = _safe_rel_delta(delta, sp_value)

        pass_flag = abs(delta) <= ABS_TOL or abs(rel_delta) <= REL_TOL
        rows.append((key, csf_value, sp_value, delta, rel_delta, pass_flag))

    return rows


def _rows_to_text(title: str, rows: Sequence[Tuple[str, float, float, float, float, bool]]) -> str:
    """Render comparison rows as a fixed-width text table."""
    lines = [
        "",
        title,
        f"{'Property':<12} {'CSF':>20} {'SP':>20} {'Delta':>20} {'RelDelta':>14} {'OK':>5}",
        "-" * 99,
    ]

    for name, csf_value, sp_value, delta, rel_delta, pass_flag in rows:
        lines.append(
            f"{name:<12} "
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
# Geometry definition.
# ---------------------------------------------------------------------------
def _polygon(vertices: Sequence[Pt], weight: float, name: str) -> Polygon:
    """Create one CSF polygon."""
    return Polygon(vertices=tuple(vertices), weight=weight, name=name)


def build_field() -> ContinuousSectionField:
    """Build a non-prismatic ordinary CSF section field."""

    # S0 outer boundary: irregular CCW polygon.
    outer_s0 = (
        Pt(-0.50, -0.28),
        Pt(-0.28, -0.40),
        Pt( 0.05, -0.42),
        Pt( 0.42, -0.30),
        Pt( 0.56, -0.08),
        Pt( 0.50,  0.18),
        Pt( 0.30,  0.38),
        Pt( 0.02,  0.48),
        Pt(-0.32,  0.40),
        Pt(-0.54,  0.16),
        Pt(-0.60, -0.10),
    )

    # S1 outer boundary: same vertex count, tapered and warped.
    outer_s1 = (
        Pt(-0.42, -0.23),
        Pt(-0.24, -0.34),
        Pt( 0.06, -0.36),
        Pt( 0.36, -0.25),
        Pt( 0.48, -0.06),
        Pt( 0.43,  0.16),
        Pt( 0.25,  0.32),
        Pt( 0.01,  0.40),
        Pt(-0.27,  0.34),
        Pt(-0.46,  0.13),
        Pt(-0.50, -0.08),
    )

    # Explicit void A, weight = 0.0.
    void_a_s0 = (
        Pt(-0.32, -0.05),
        Pt(-0.25, -0.12),
        Pt(-0.14, -0.10),
        Pt(-0.10, -0.02),
        Pt(-0.15,  0.08),
        Pt(-0.28,  0.11),
        Pt(-0.38,  0.06),
        Pt(-0.40, -0.02),
    )

    void_a_s1 = (
        Pt(-0.27, -0.04),
        Pt(-0.21, -0.10),
        Pt(-0.12, -0.09),
        Pt(-0.08, -0.01),
        Pt(-0.13,  0.07),
        Pt(-0.24,  0.09),
        Pt(-0.33,  0.05),
        Pt(-0.34, -0.02),
    )

    # Explicit void B, weight = 0.0.
    void_b_s0 = (
        Pt(0.18, 0.05),
        Pt(0.32, 0.04),
        Pt(0.40, 0.13),
        Pt(0.36, 0.25),
        Pt(0.22, 0.28),
        Pt(0.12, 0.18),
    )

    void_b_s1 = (
        Pt(0.15, 0.04),
        Pt(0.27, 0.03),
        Pt(0.34, 0.11),
        Pt(0.30, 0.21),
        Pt(0.18, 0.23),
        Pt(0.10, 0.15),
    )

    # Stiffer insert, weight = 1.8.
    insert_stiff_s0 = (
        Pt(-0.05, -0.28),
        Pt( 0.16, -0.31),
        Pt( 0.28, -0.23),
        Pt( 0.20, -0.12),
        Pt( 0.02, -0.10),
        Pt(-0.10, -0.18),
    )

    insert_stiff_s1 = (
        Pt(-0.04, -0.23),
        Pt( 0.13, -0.26),
        Pt( 0.23, -0.19),
        Pt( 0.17, -0.10),
        Pt( 0.02, -0.08),
        Pt(-0.08, -0.15),
    )

    # Degraded insert, weight = 0.35.
    insert_soft_s0 = (
        Pt(-0.28, 0.20),
        Pt(-0.10, 0.18),
        Pt(-0.04, 0.28),
        Pt(-0.18, 0.36),
        Pt(-0.35, 0.32),
        Pt(-0.40, 0.24),
    )

    insert_soft_s1 = (
        Pt(-0.23, 0.16),
        Pt(-0.08, 0.15),
        Pt(-0.03, 0.23),
        Pt(-0.15, 0.30),
        Pt(-0.29, 0.27),
        Pt(-0.34, 0.20),
    )

    s0 = Section(
        polygons=(
            _polygon(outer_s0, 1.0, "outer"),
            _polygon(void_a_s0, 0.0, "void_a"),
            _polygon(void_b_s0, 0.0, "void_b"),
            _polygon(insert_stiff_s0, 1.8, "insert_stiff"),
            _polygon(insert_soft_s0, 0.35, "insert_soft"),
        ),
        z=Z0,
    )

    s1 = Section(
        polygons=(
            _polygon(outer_s1, 1.0, "outer"),
            _polygon(void_a_s1, 0.0, "void_a"),
            _polygon(void_b_s1, 0.0, "void_b"),
            _polygon(insert_stiff_s1, 1.8, "insert_stiff"),
            _polygon(insert_soft_s1, 0.35, "insert_soft"),
        ),
        z=Z1,
    )

    return ContinuousSectionField(section0=s0, section1=s1)


# ---------------------------------------------------------------------------
# sectionproperties extraction.
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
    """Run the full CSF-SP verification and write a Markdown report."""
    field = build_field()

    keys = ("A", "Cx", "Cy", "Ix", "Iy", "Ixy", "Ip", "I1", "I2", "rx", "ry")

    all_rows = []
    text_blocks = []
    markdown_blocks = [
        "# CSF-SP Complex Integration Verification Report",
        "",
        "## Model",
        "",
        "Ordinary non-prismatic CSF geometry with:",
        "",
        "- one irregular outer polygon with `weight = 1.0`;",
        "- two explicit void polygons with `weight = 0.0`;",
        "- one stiff insert with `weight = 1.8`;",
        "- one degraded insert with `weight = 0.35`;",
        "- no `@cell` polygon.",
        "",
        "The comparison uses `sectionproperties` composite accessors because `csf_sp` "
        "builds a material-based model. The effective material scale is the CSF "
        "polygon weight, so `EA`, `EIx` and `EIy` are compared with CSF `A`, `Ix` "
        "and `Iy`.",
        "",
        f"Absolute tolerance: `{ABS_TOL:.1e}`",
        f"Relative tolerance: `{REL_TOL:.1e}`",
        f"Mesh size: `{mesh_size:.6g}`",
        "",
    ]

    for z in z_stations:
        csf_result = extract_csf_results(field, z)

        sec_sp = analyse(field, z=z, mesh=mesh_size)

        if plot:
            ax = sec_sp.geometry.plot_geometry(
                labels=("points", "facets", "control_points"),
                cp=True,
            )
            ax.set_title(f"sectionproperties geometry at z = {z}")
            ax.set_aspect("equal", adjustable="box")
            plt.show(block=True)

            ax = sec_sp.plot_mesh(materials=False)
            ax.set_title(f"sectionproperties mesh at z = {z}")
            ax.set_aspect("equal", adjustable="box")
            plt.show(block=True)

        sp_result = extract_sp_results(sec_sp)
        rows = _comparison_rows(csf_result, sp_result, keys)
        all_rows.extend((z, *row) for row in rows)

        title = f"CSF ordinary weighted geometry vs sectionproperties at z = {z}"
        text_blocks.append(_rows_to_text(title, rows))
        markdown_blocks.append(_rows_to_markdown(title, rows))
        markdown_blocks.append("")

        text_blocks.append("")
        text_blocks.append("Expected torsion flags for ordinary no-cell geometry")
        text_blocks.append(f"J_sv_cell: {csf_result['J_sv_cell']}")
        text_blocks.append(f"J_sv_wall: {csf_result['J_sv_wall']}")

        markdown_blocks.append("Expected torsion flags for ordinary no-cell geometry:")
        markdown_blocks.append("")
        markdown_blocks.append(f"- `J_sv_cell`: `{csf_result['J_sv_cell']}`")
        markdown_blocks.append(f"- `J_sv_wall`: `{csf_result['J_sv_wall']}`")
        markdown_blocks.append("")

    max_abs = max(abs(row[4]) for row in all_rows)
    max_rel = max(abs(row[5]) for row in all_rows)
    failed = [row for row in all_rows if not row[6]]
    passed = len(failed) == 0

    summary = [
        "",
        "GLOBAL SUMMARY",
        "==============",
        f"stations checked: {len(tuple(z_stations))}",
        f"properties per station: {len(keys)}",
        f"maximum absolute delta: {max_abs:.12e}",
        f"maximum relative delta: {max_rel:.6e}",
        f"overall status: {'PASS' if passed else 'FAIL'}",
    ]

    text_blocks.extend(summary)

    markdown_blocks.extend(
        [
            "## Global summary",
            "",
            f"- Stations checked: `{len(tuple(z_stations))}`",
            f"- Properties per station: `{len(keys)}`",
            f"- Maximum absolute delta: `{max_abs:.12e}`",
            f"- Maximum relative delta: `{max_rel:.6e}`",
            f"- Overall status: `{'PASS' if passed else 'FAIL'}`",
            "",
        ]
    )

    if failed:
        markdown_blocks.append("## Failed rows")
        markdown_blocks.append("")
        markdown_blocks.append("| z | Property | Delta | RelDelta |")
        markdown_blocks.append("|---:|---|---:|---:|")
        for z, name, _csf_value, _sp_value, delta, rel_delta, _pass_flag in failed:
            markdown_blocks.append(
                f"| {z:.6g} | {name} | {_format_float(delta)} | {rel_delta:.6e} |"
            )
        markdown_blocks.append("")

    report_path.write_text("\n".join(markdown_blocks), encoding="utf-8")

    print("\n".join(text_blocks))
    print(f"\nMarkdown report written to: {report_path}")

    return passed


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a complex CSF-SP integration verification case."
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
        default=Path("csf_sp_complex_integration_report.md"),
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

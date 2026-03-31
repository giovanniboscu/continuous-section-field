from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]


def _clean_zero(value: float, tol: float = 1.0e-15) -> float:
    """Remove numerical noise around zero for cleaner YAML output."""
    return 0.0 if abs(value) < tol else value


def regular_ngon_from_bbox_ccw(
    center: Point,
    lx: float,
    ly: float,
    n: int,
) -> List[Point]:
    """
    Build a CCW n-gon inscribed in the rectangle (lx, ly), starting from the leftmost point.

    For lx == ly this is a regular polygon. For lx != ly this is the affine-scaled version
    of the same angular discretization, still emitted CCW.
    """
    if n < 3:
        raise ValueError("n must be >= 3")
    if lx <= 0.0 or ly <= 0.0:
        raise ValueError("lx and ly must be > 0")

    cx, cy = center
    rx = 0.5 * lx
    ry = 0.5 * ly

    vertices: List[Point] = []
    theta0 = math.pi
    dtheta = 2.0 * math.pi / n

    for i in range(n):
        theta = theta0 + i * dtheta
        x = _clean_zero(cx + rx * math.cos(theta))
        y = _clean_zero(cy + ry * math.sin(theta))
        vertices.append((x, y))

    return vertices


def _fmt_num(value: float) -> str:
    """Compact float formatting for YAML output."""
    value = _clean_zero(float(value))
    text = f"{value:.12g}"
    if text == "-0":
        return "0"
    return text


def _emit_vertices(lines: List[str], vertices: Sequence[Point], base_indent: str) -> None:
    for x, y in vertices:
        lines.append(f"{base_indent}- [{_fmt_num(x)}, {_fmt_num(y)}]")


def build_csf_yaml_text(
    *,
    script_name: str,
    single_pole: bool,
    geometry_yaml_filename: str,
    outer_poly_name: str,
    void_poly_name: str,
    w_default: float,
    z0: float,
    z1: float,
    w0: float,
    w1: float,
    inner_center_s0: Point,
    inner_lx_s0: float,
    inner_ly_s0: float,
    inner_n_s0: int,
    outer_center_s0: Point,
    outer_lx_s0: float,
    outer_ly_s0: float,
    outer_n_s0: int,
    inner_center_s1: Point,
    inner_lx_s1: float,
    inner_ly_s1: float,
    inner_n_s1: int,
    outer_center_s1: Point,
    outer_lx_s1: float,
    outer_ly_s1: float,
    outer_n_s1: int,
    weight_laws: Iterable[str],
) -> str:
    outer_s0 = regular_ngon_from_bbox_ccw(outer_center_s0, outer_lx_s0, outer_ly_s0, outer_n_s0)
    inner_s0 = regular_ngon_from_bbox_ccw(inner_center_s0, inner_lx_s0, inner_ly_s0, inner_n_s0)
    outer_s1 = regular_ngon_from_bbox_ccw(outer_center_s1, outer_lx_s1, outer_ly_s1, outer_n_s1)
    inner_s1 = regular_ngon_from_bbox_ccw(inner_center_s1, inner_lx_s1, inner_ly_s1, inner_n_s1)

    lines: List[str] = []
    lines.append("# -----------------------------------------------------------------------------")
    lines.append("# GEOMETRY INPUTS (auto-recorded by generator)")
    lines.append("# -----------------------------------------------------------------------------")
    lines.append(f"# SCRIPT                : {script_name}")
    lines.append(f"# SINGLE_POLE           : {single_pole}")
    lines.append(f"# GEOMETRY_YAML_FILENAME: {geometry_yaml_filename}")
    lines.append(f"# OUTER_POLY_NAME       : {outer_poly_name}")
    lines.append(f"# VOID_POLY_NAME        : {void_poly_name}")
    lines.append(f"# W_DEFAULT             : {_fmt_num(w_default)}")
    lines.append(f"# z0                    : {_fmt_num(z0)}")
    lines.append(f"# z1                    : {_fmt_num(z1)}")
    lines.append("#")
    lines.append("# S0:")
    lines.append(f"#   W0           : {_fmt_num(w0)}")
    lines.append(f"#   INNER_CENTER : ({_fmt_num(inner_center_s0[0])}, {_fmt_num(inner_center_s0[1])})")
    lines.append(f"#   INNER_LX     : {_fmt_num(inner_lx_s0)}")
    lines.append(f"#   INNER_LY     : {_fmt_num(inner_ly_s0)}")
    lines.append(f"#   INNER_N      : {inner_n_s0}")
    lines.append(f"#   OUTER_CENTER : ({_fmt_num(outer_center_s0[0])}, {_fmt_num(outer_center_s0[1])})")
    lines.append(f"#   OUTER_LX     : {_fmt_num(outer_lx_s0)}")
    lines.append(f"#   OUTER_LY     : {_fmt_num(outer_ly_s0)}")
    lines.append(f"#   OUTER_N      : {outer_n_s0}")
    lines.append("#")
    lines.append("# S1:")
    lines.append(f"#   W1           : {_fmt_num(w1)}")
    lines.append(f"#   INNER_CENTER : ({_fmt_num(inner_center_s1[0])}, {_fmt_num(inner_center_s1[1])})")
    lines.append(f"#   INNER_LX     : {_fmt_num(inner_lx_s1)}")
    lines.append(f"#   INNER_LY     : {_fmt_num(inner_ly_s1)}")
    lines.append(f"#   INNER_N      : {inner_n_s1}")
    lines.append(f"#   OUTER_CENTER : ({_fmt_num(outer_center_s1[0])}, {_fmt_num(outer_center_s1[1])})")
    lines.append(f"#   OUTER_LX     : {_fmt_num(outer_lx_s1)}")
    lines.append(f"#   OUTER_LY     : {_fmt_num(outer_ly_s1)}")
    lines.append(f"#   OUTER_N      : {outer_n_s1}")
    lines.append("# -----------------------------------------------------------------------------")
    lines.append("CSF:")
    lines.append("  sections:")

    lines.append("    S0:")
    lines.append(f"      z: {_fmt_num(z0)}")
    lines.append("      polygons:")
    lines.append(f"        {outer_poly_name}:")
    lines.append(f"          weight: {_fmt_num(w0)}")
    lines.append("          vertices:")
    _emit_vertices(lines, outer_s0, "            ")
    lines.append(f"        {void_poly_name}:")
    lines.append("          weight: 0")
    lines.append("          vertices:")
    _emit_vertices(lines, inner_s0, "            ")

    lines.append("    S1:")
    lines.append(f"      z: {_fmt_num(z1)}")
    lines.append("      polygons:")
    lines.append(f"        {outer_poly_name}:")
    lines.append(f"          weight: {_fmt_num(w1)}")
    lines.append("          vertices:")
    _emit_vertices(lines, outer_s1, "            ")
    lines.append(f"        {void_poly_name}:")
    lines.append("          weight: 0")
    lines.append("          vertices:")
    _emit_vertices(lines, inner_s1, "            ")

    lines.append("  weight_laws:")
    for law in weight_laws:
        lines.append(f"    - '{law}'")

    return "\n".join(lines) + "\n"


def write_geometry_yaml(output_path: str, yaml_text: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_text)


if __name__ == "__main__":
    # Output
    GEOMETRY_YAML_FILENAME = "ekofisk_geometry_m.yaml"
    SCRIPT_NAME = "csf_polygon_hole_builder_v2.py"

    # Metadata recorded in the YAML header
    SINGLE_POLE = False
    OUTER_POLY_NAME = "poly"
    VOID_POLY_NAME = "void"
    W_DEFAULT = 1.0

    # Stations
    z0 = 0.0
    z1 = 175.0
    W0 = 1.0
    W1 = 1.0

    # S0
    INNER_CENTER_S0 = (0.0, 0.0)
    INNER_LX_S0 = 2.3
    INNER_LY_S0 = 2.3
    INNER_N_S0 = 8

    OUTER_CENTER_S0 = (0.0, 0.0)
    OUTER_LX_S0 = 2.4
    OUTER_LY_S0 = 2.4
    OUTER_N_S0 = 8

    # S1
    INNER_CENTER_S1 = (0.0, 0.0)
    INNER_LX_S1 = 2.25
    INNER_LY_S1 = 2.25
    INNER_N_S1 = 8

    OUTER_CENTER_S1 = (0.0, 0.0)
    OUTER_LX_S1 = 2.4
    OUTER_LY_S1 = 2.4
    OUTER_N_S1 = 8

    # Weight laws
    WEIGHT_LAWS = [
        "poly,poly: 1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))",
    ]

    yaml_text = build_csf_yaml_text(
        script_name=SCRIPT_NAME,
        single_pole=SINGLE_POLE,
        geometry_yaml_filename=GEOMETRY_YAML_FILENAME,
        outer_poly_name=OUTER_POLY_NAME,
        void_poly_name=VOID_POLY_NAME,
        w_default=W_DEFAULT,
        z0=z0,
        z1=z1,
        w0=W0,
        w1=W1,
        inner_center_s0=INNER_CENTER_S0,
        inner_lx_s0=INNER_LX_S0,
        inner_ly_s0=INNER_LY_S0,
        inner_n_s0=INNER_N_S0,
        outer_center_s0=OUTER_CENTER_S0,
        outer_lx_s0=OUTER_LX_S0,
        outer_ly_s0=OUTER_LY_S0,
        outer_n_s0=OUTER_N_S0,
        inner_center_s1=INNER_CENTER_S1,
        inner_lx_s1=INNER_LX_S1,
        inner_ly_s1=INNER_LY_S1,
        inner_n_s1=INNER_N_S1,
        outer_center_s1=OUTER_CENTER_S1,
        outer_lx_s1=OUTER_LX_S1,
        outer_ly_s1=OUTER_LY_S1,
        outer_n_s1=OUTER_N_S1,
        weight_laws=WEIGHT_LAWS,
    )

    write_geometry_yaml(GEOMETRY_YAML_FILENAME, yaml_text)
    print(f"Wrote: {GEOMETRY_YAML_FILENAME}")

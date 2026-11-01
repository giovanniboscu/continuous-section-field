#!/usr/bin/env python3
# compare_prism_taper_table9_v1.py - v1.0
"""CSF-CUF vs FEM3D line profiles along every CSF polygon vertex track.

For every polygon vertex, the script follows the corresponding physical point
continuously from S0 to S1 and writes three line plots (ux, uy, uz). Every plot
contains exactly two curves: FEM3D and CSF-CUF over x/L in [0,1].

By default the line is sampled at 201 uniformly spaced x/L positions. FEM3D is
evaluated on the corresponding HEXA8 longitudinal edge by its exact linear edge
interpolation; CUF is evaluated at exactly the same physical coordinates.

Each CSF polygon is sampled at its four geometric corners.  The extra
collinear YAML points on the top and bottom flange boundaries are not treated
as additional vertices for this comparison.

    top_flange:    4 corners
    web:           4 corners
    bottom_flange: 4 corners

Shared physical corners are retained under both polygon labels when they
belong to two polygon boundaries.

Coordinates written to CSV and shown in plot titles remain in the CSF system:

    CSF X = first polygon coordinate
    CSF Y = second polygon coordinate
    CSF Z = longitudinal coordinate

No CSF coordinate transformation is applied to the reported coordinates.

Displacements retain the Carrera/Table-9 convention used by the previous
comparison scripts:

    paper ux = -solver uz
    paper uy =  solver uy
    paper uz =  solver ux

Outputs:

* vertex_profiles_continuous.csv
* 12 polygon corners x 3 displacement components = 36 line plots

The script supports both the current compiled displacement checkpoint format
and the older static compiled NPZ format without a top-level ``format_version``.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    from csf.cuf.solver.compiled_field import CompiledDisplacementField
except ImportError:
    try:
        from cuf.solver.compiled_field import CompiledDisplacementField
    except ImportError:
        CompiledDisplacementField = None


VERSION = "v2.0"
REFERENCE_A = 100.0
REFERENCE_E = 71700.0
DEFAULT_FEM3D = Path(__file__).resolve().parent / "output" / "taper80_bending_fem3d.npz"
DEFAULT_OUTPUT_DIR = Path("plots_table9_polygon_vertices")
DEFAULT_POINTS = 201
DEFAULT_LINE_WIDTH_SCALE = 0.7
BASE_PROFILE_LINE_WIDTH = 1.7
BASE_ZERO_LINE_WIDTH = 0.8

POLYGON_ORDER = ("top_flange", "web", "bottom_flange")
VERTEX_COUNT = {"top_flange": 4, "web": 4, "bottom_flange": 4}
COMPONENTS = ("ux", "uy", "uz")
COMPONENT_COLUMNS = {"ux": 0, "uy": 1, "uz": 2}
SCALES = {"ux": 10.0, "uy": 1000.0, "uz": 100.0}
Y_LABELS = {
    "ux": r"$10\,u_x^*$",
    "uy": r"$10^3\,u_y^*$",
    "uz": r"$10^2\,u_z^*$",
}

# HEXA8 longitudinal edge pairs used by run_bending_fem3d_v2.py.
_HEX_X_EDGE_PAIRS = ((0, 1), (3, 2), (4, 5), (7, 6))


class _LegacyStaticCompiledField:
    """Read legacy static compiled CUF NPZ files without top-level format_version."""

    def __init__(self, path: Path) -> None:
        with np.load(path, allow_pickle=False) as data:
            required = {
                "element_x_starts",
                "element_x_ends",
                "element_coefficients",
                "longitudinal_shape_coefficients",
                "transverse_power_coefficients",
            }
            missing = sorted(required - set(data.files))
            if missing:
                raise ValueError(
                    "legacy CUF NPZ is missing required arrays: " + ", ".join(missing)
                )
            self._starts = np.asarray(data["element_x_starts"], dtype=float).copy()
            self._ends = np.asarray(data["element_x_ends"], dtype=float).copy()
            self._ecoef = np.asarray(data["element_coefficients"], dtype=float).copy()
            self._lcoef = np.asarray(
                data["longitudinal_shape_coefficients"], dtype=float
            ).copy()
            self._tcoef = np.asarray(
                data["transverse_power_coefficients"], dtype=float
            ).copy()

        if self._starts.ndim != 1 or self._ends.shape != self._starts.shape:
            raise ValueError("invalid legacy CUF element ranges")
        if self._starts.size == 0:
            raise ValueError("legacy CUF NPZ contains no elements")

    @property
    def x_start(self) -> float:
        return float(self._starts[0])

    @property
    def x_end(self) -> float:
        return float(self._ends[-1])

    def _element_index(self, x: float) -> int:
        x = float(x)
        tol = 1.0e-12 * max(1.0, abs(self.x_start), abs(self.x_end))
        if math.isclose(x, self.x_end, rel_tol=0.0, abs_tol=tol):
            return int(self._starts.size - 1)
        hits = np.flatnonzero((x >= self._starts - tol) & (x < self._ends - tol))
        if hits.size != 1:
            raise ValueError(f"cannot identify CUF element for x={x}")
        return int(hits[0])

    def section_evaluator(self, x: float):
        e = self._element_index(float(x))
        x0 = float(self._starts[e])
        x1 = float(self._ends[e])
        xi = 2.0 * (float(x) - x0) / (x1 - x0) - 1.0

        lpowers = np.asarray(
            [xi**k for k in range(self._lcoef.shape[1])], dtype=float
        )
        N = self._lcoef @ lpowers

        def evaluate(y: float, z: float) -> np.ndarray:
            yp = np.asarray(
                [float(y) ** i for i in range(self._tcoef.shape[1])], dtype=float
            )
            zp = np.asarray(
                [float(z) ** j for j in range(self._tcoef.shape[2])], dtype=float
            )
            F = np.einsum("tij,i,j->t", self._tcoef, yp, zp)
            return np.einsum("i,t,itc->c", N, F, self._ecoef[e])

        return evaluate


def load_cuf_field(path: Path):
    """Load current compiled fields and the older static coefficient NPZ format."""
    with np.load(path, allow_pickle=False) as data:
        keys = set(data.files)

    if "format_version" in keys:
        if CompiledDisplacementField is None:
            raise ImportError(
                "current CUF checkpoint detected, but CompiledDisplacementField "
                "cannot be imported from csf.cuf or cuf"
            )
        return CompiledDisplacementField.load(path)

    legacy_required = {
        "element_x_starts",
        "element_x_ends",
        "element_coefficients",
        "longitudinal_shape_coefficients",
        "transverse_power_coefficients",
    }
    if legacy_required.issubset(keys):
        print("[CUF] legacy static compiled NPZ detected (no top-level format_version)")
        return _LegacyStaticCompiledField(path)

    raise ValueError(
        "CUF NPZ is neither a current CompiledDisplacementField checkpoint nor "
        "the supported legacy static compiled format. Available keys: "
        + ", ".join(sorted(keys))
    )


def _scalar(data: np.lib.npyio.NpzFile, key: str) -> float:
    if key not in data.files:
        raise ValueError(f"FEM3D NPZ is missing required key {key!r}")
    value = np.asarray(data[key])
    if value.size != 1:
        raise ValueError(f"FEM3D NPZ key {key!r} must contain one scalar")
    return float(value.reshape(-1)[0])


def load_fem3d(path: Path):
    with np.load(path, allow_pickle=False) as data:
        required = {"nodes", "elements", "displacement", "amplitude", "x0", "x1"}
        missing = sorted(required - set(data.files))
        if missing:
            raise ValueError(f"FEM3D NPZ is missing keys: {', '.join(missing)}")

        nodes = np.asarray(data["nodes"], dtype=float)
        elements = np.asarray(data["elements"], dtype=int)
        displacement = np.asarray(data["displacement"], dtype=float)
        amplitude = _scalar(data, "amplitude")
        x0 = _scalar(data, "x0")
        x1 = _scalar(data, "x1")

    if nodes.ndim != 2 or nodes.shape[1] != 3:
        raise ValueError("FEM3D 'nodes' must have shape (n, 3)")
    if displacement.shape != nodes.shape:
        raise ValueError("FEM3D 'displacement' must have the same shape as 'nodes'")
    if elements.ndim != 2 or elements.shape[1] != 8:
        raise ValueError("FEM3D 'elements' must have shape (n, 8)")
    if amplitude == 0.0:
        raise ValueError("FEM3D amplitude is zero; Table-9 normalization is undefined")
    if x1 <= x0:
        raise ValueError(f"invalid FEM3D beam range: x0={x0}, x1={x1}")

    return nodes, elements, displacement, amplitude, x0, x1


def paper_components(displacement: np.ndarray) -> np.ndarray:
    displacement = np.asarray(displacement, dtype=float)
    if displacement.ndim == 1:
        if displacement.shape != (3,):
            raise ValueError("displacement vector must have shape (3,)")
        return np.asarray((-displacement[2], displacement[1], displacement[0]), dtype=float)
    if displacement.ndim == 2 and displacement.shape[1] == 3:
        return np.column_stack((-displacement[:, 2], displacement[:, 1], displacement[:, 0]))
    raise ValueError("displacement must have shape (3,) or (n,3)")


def normalization_factor(length: float, amplitude: float, a: float, E: float) -> float:
    return (math.pi**4 / 12.0) * (a**3 / length**4) * (E / amplitude)


def section_layers(nodes: np.ndarray) -> list[tuple[float, np.ndarray]]:
    layers: list[tuple[float, np.ndarray]] = []
    for x in np.sort(np.unique(nodes[:, 0])):
        ids = np.flatnonzero(nodes[:, 0] == x)
        if ids.size == 0:
            raise RuntimeError(f"internal error grouping FEM station x={x}")
        layers.append((float(x), ids))
    return layers


def _longitudinal_mapping(
    nodes: np.ndarray,
    elements: np.ndarray,
    left_ids: np.ndarray,
    right_ids: np.ndarray,
    x_left: float,
    x_right: float,
) -> np.ndarray:
    """Map every left-layer node to its matching right-layer node through HEXA8 x-edges."""
    left_set = set(int(v) for v in left_ids)
    right_set = set(int(v) for v in right_ids)
    mapping: dict[int, int] = {}

    tol = 1.0e-10 * max(1.0, abs(x_left), abs(x_right), abs(x_right - x_left))

    for conn in elements:
        ex = nodes[conn, 0]
        if float(np.min(ex)) > x_left + tol or float(np.max(ex)) < x_right - tol:
            continue
        if not (
            math.isclose(float(np.min(ex)), x_left, rel_tol=0.0, abs_tol=tol)
            and math.isclose(float(np.max(ex)), x_right, rel_tol=0.0, abs_tol=tol)
        ):
            continue

        for ia, ib in _HEX_X_EDGE_PAIRS:
            a = int(conn[ia])
            b = int(conn[ib])
            xa = float(nodes[a, 0])
            xb = float(nodes[b, 0])
            if xa > xb:
                a, b = b, a
                xa, xb = xb, xa
            if not (
                math.isclose(xa, x_left, rel_tol=0.0, abs_tol=tol)
                and math.isclose(xb, x_right, rel_tol=0.0, abs_tol=tol)
            ):
                continue
            if a not in left_set or b not in right_set:
                continue
            previous = mapping.get(a)
            if previous is not None and previous != b:
                raise RuntimeError("inconsistent longitudinal FEM node mapping")
            mapping[a] = b

    missing = [int(v) for v in left_ids if int(v) not in mapping]
    if missing:
        raise RuntimeError(
            f"could not map {len(missing)} section nodes from x={x_left} to x={x_right}"
        )

    return np.asarray([mapping[int(v)] for v in left_ids], dtype=int)


def interpolate_section(
    nodes: np.ndarray,
    elements: np.ndarray,
    displacement: np.ndarray,
    layers: list[tuple[float, np.ndarray]],
    target_x: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return FEM section-node coordinates/displacements exactly at target_x."""
    xs = np.asarray([x for x, _ in layers], dtype=float)
    scale = max(1.0, float(np.max(np.abs(xs))))
    tol = 1.0e-10 * scale

    exact = np.flatnonzero(np.isclose(xs, target_x, rtol=0.0, atol=tol))
    if exact.size:
        ids = layers[int(exact[0])][1]
        return np.asarray(nodes[ids], dtype=float), np.asarray(displacement[ids], dtype=float)

    j = int(np.searchsorted(xs, target_x, side="right"))
    if j <= 0 or j >= len(layers):
        raise ValueError(f"target x={target_x} lies outside FEM3D longitudinal layers")

    x_left, left_ids = layers[j - 1]
    x_right, right_ids = layers[j]
    if len(left_ids) != len(right_ids):
        raise RuntimeError("FEM section node count changes between adjacent longitudinal layers")

    mapped_right = _longitudinal_mapping(
        nodes, elements, left_ids, right_ids, x_left, x_right
    )
    alpha = (target_x - x_left) / (x_right - x_left)

    xyz = (1.0 - alpha) * nodes[left_ids] + alpha * nodes[mapped_right]
    u = (1.0 - alpha) * displacement[left_ids] + alpha * displacement[mapped_right]
    xyz[:, 0] = target_x
    return np.asarray(xyz, dtype=float), np.asarray(u, dtype=float)


def _unique_tol(values: np.ndarray, decimals: int = 10) -> np.ndarray:
    return np.unique(np.round(np.asarray(values, dtype=float), decimals=decimals))


def infer_i_section_bounds(section_xyz: np.ndarray) -> dict[str, tuple[float, float, float, float]]:
    """Infer the three rectangular CSF polygon bounds from one structured FEM section."""
    # Solver section coordinates = CSF (X,Y).
    X = np.asarray(section_xyz[:, 1], dtype=float)
    Y = np.asarray(section_xyz[:, 2], dtype=float)

    X_levels = _unique_tol(X)
    Y_levels = _unique_tol(Y)
    X_min = float(np.min(X_levels))
    X_max = float(np.max(X_levels))
    Y_min = float(np.min(Y_levels))
    Y_max = float(np.max(Y_levels))

    tol = 1.0e-8 * max(1.0, abs(X_min), abs(X_max), abs(Y_min), abs(Y_max))

    # The row closest to Y=0 belongs only to the web and gives its X bounds.
    Y_mid = float(Y_levels[np.argmin(np.abs(Y_levels))])
    mid_mask = np.isclose(Y, Y_mid, rtol=0.0, atol=tol)
    if np.count_nonzero(mid_mask) < 2:
        raise RuntimeError("cannot identify the web row near CSF Y=0")
    web_X_min = float(np.min(X[mid_mask]))
    web_X_max = float(np.max(X[mid_mask]))

    # Full-width rows belong to the flanges.  The two rows closest to Y=0 are
    # the web/flange interfaces.
    full_width_Y: list[float] = []
    for y_level in Y_levels:
        row = np.isclose(Y, y_level, rtol=0.0, atol=tol)
        row_X_min = float(np.min(X[row]))
        row_X_max = float(np.max(X[row]))
        if math.isclose(row_X_min, X_min, rel_tol=0.0, abs_tol=tol) and math.isclose(
            row_X_max, X_max, rel_tol=0.0, abs_tol=tol
        ):
            full_width_Y.append(float(y_level))

    below = [v for v in full_width_Y if v <= Y_mid + tol]
    above = [v for v in full_width_Y if v >= Y_mid - tol]
    if not below or not above:
        raise RuntimeError("cannot identify the web/flange interface rows")

    web_Y_min = max(below)
    web_Y_max = min(above)
    if not (Y_min < web_Y_min < web_Y_max < Y_max):
        raise RuntimeError(
            "invalid inferred I-section topology: "
            f"Y=[{Y_min},{Y_max}], web Y=[{web_Y_min},{web_Y_max}]"
        )

    return {
        "top_flange": (X_min, X_max, web_Y_max, Y_max),
        "web": (web_X_min, web_X_max, web_Y_min, web_Y_max),
        "bottom_flange": (X_min, X_max, Y_min, web_Y_min),
    }


def polygon_vertices_from_bounds(
    bounds_by_polygon: dict[str, tuple[float, float, float, float]]
) -> dict[str, tuple[tuple[float, float], ...]]:
    """Return the four geometric corners of each CSF polygon.

    The top and bottom flange YAML polygons contain two additional collinear
    interface points.  Those points do not create additional geometric
    corners and are deliberately omitted here, giving exactly 4 x 3 tracks.
    """
    result: dict[str, tuple[tuple[float, float], ...]] = {}
    for polygon in POLYGON_ORDER:
        X0, X1, Y0, Y1 = bounds_by_polygon[polygon]
        result[polygon] = (
            (X0, Y0),
            (X1, Y0),
            (X1, Y1),
            (X0, Y1),
        )
    return result


def _single_section_node(
    section_xyz: np.ndarray,
    *,
    csf_X: float,
    csf_Y: float,
    label: str,
) -> int:
    """Return the unique FEM section node at one CSF section coordinate."""
    X = np.asarray(section_xyz[:, 1], dtype=float)
    Y = np.asarray(section_xyz[:, 2], dtype=float)
    scale = max(1.0, abs(csf_X), abs(csf_Y))
    tol = 1.0e-8 * scale
    mask = np.isclose(X, csf_X, rtol=0.0, atol=tol) & np.isclose(
        Y, csf_Y, rtol=0.0, atol=tol
    )
    matches = np.flatnonzero(mask)
    if matches.size != 1:
        raise ValueError(
            f"expected exactly one FEM3D section node for {label} at "
            f"CSF(X,Y)=({csf_X:.12g},{csf_Y:.12g}); found {matches.size}"
        )
    return int(matches[0])


def build_rows(
    field,
    nodes: np.ndarray,
    elements: np.ndarray,
    fem_displacement: np.ndarray,
    *,
    x0: float,
    x1: float,
    amplitude: float,
    a: float,
    E: float,
    points: int,
) -> list[dict[str, float | int | str]]:
    length = x1 - x0
    factor = normalization_factor(length, amplitude, a, E)
    layers = section_layers(nodes)
    rows: list[dict[str, float | int | str]] = []
    fractions = np.linspace(0.0, 1.0, int(points), dtype=float)

    for fraction in fractions:
        target_x = x0 + float(fraction) * length
        section_xyz, section_u = interpolate_section(
            nodes, elements, fem_displacement, layers, target_x
        )
        fem_paper = paper_components(section_u)
        bounds_by_polygon = infer_i_section_bounds(section_xyz)
        vertices = polygon_vertices_from_bounds(bounds_by_polygon)
        evaluator = field.section_evaluator(target_x)

        for polygon in POLYGON_ORDER:
            expected = VERTEX_COUNT[polygon]
            if len(vertices[polygon]) != expected:
                raise RuntimeError(
                    f"internal vertex count mismatch for {polygon}: "
                    f"expected {expected}, got {len(vertices[polygon])}"
                )

            for vertex_id, (csf_X, csf_Y) in enumerate(vertices[polygon]):
                label = f"{polygon}_v{vertex_id}"
                local_id = _single_section_node(
                    section_xyz,
                    csf_X=float(csf_X),
                    csf_Y=float(csf_Y),
                    label=label,
                )

                cuf_solver = np.asarray(evaluator(float(csf_X), float(csf_Y)), dtype=float)
                cuf_paper = paper_components(cuf_solver)
                fem_values = fem_paper[local_id]

                row: dict[str, float | int | str] = {
                    "track": label,
                    "polygon": polygon,
                    "vertex_id": int(vertex_id),
                    "x_over_L": float(fraction),
                    "csf_X_mm": float(csf_X),
                    "csf_Y_mm": float(csf_Y),
                    "csf_Z_mm": float(target_x),
                }

                for component in COMPONENTS:
                    col = COMPONENT_COLUMNS[component]
                    scale = SCALES[component]
                    cuf_scaled = scale * factor * float(cuf_paper[col])
                    fem_scaled = scale * factor * float(fem_values[col])
                    row[f"cuf_{component}"] = cuf_scaled
                    row[f"fem3d_{component}"] = fem_scaled
                    row[f"fem_minus_cuf_{component}"] = fem_scaled - cuf_scaled

                rows.append(row)

    return rows


def write_csv(rows: list[dict[str, float | int | str]], path: Path) -> None:
    fieldnames = [
        "track",
        "polygon",
        "vertex_id",
        "x_over_L",
        "csf_X_mm",
        "csf_Y_mm",
        "csf_Z_mm",
    ]
    for component in COMPONENTS:
        fieldnames.extend(
            (
                f"cuf_{component}",
                f"fem3d_{component}",
                f"fem_minus_cuf_{component}",
            )
        )

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fmt_coord(value: float) -> str:
    if math.isclose(value, round(value), rel_tol=0.0, abs_tol=1.0e-10):
        return str(int(round(value)))
    return f"{value:.6g}"


def plot_vertex_profiles(
    rows: list[dict[str, float | int | str]],
    output_dir: Path,
) -> None:
    """Write one FEM3D-vs-CUF line graph per polygon vertex and component."""
    for polygon in POLYGON_ORDER:
        for vertex_id in range(VERTEX_COUNT[polygon]):
            track = f"{polygon}_v{vertex_id}"
            track_rows = [r for r in rows if r["track"] == track]
            track_rows.sort(key=lambda r: float(r["x_over_L"]))
            if not track_rows:
                continue

            x = np.asarray([float(r["x_over_L"]) for r in track_rows], dtype=float)

            first = track_rows[0]
            last = track_rows[-1]
            s0 = (
                float(first["csf_X_mm"]),
                float(first["csf_Y_mm"]),
                float(first["csf_Z_mm"]),
            )
            s1 = (
                float(last["csf_X_mm"]),
                float(last["csf_Y_mm"]),
                float(last["csf_Z_mm"]),
            )
            coord_line = (
                "CSF S0=("
                + ", ".join(_fmt_coord(v) for v in s0)
                + ")  ->  S1=("
                + ", ".join(_fmt_coord(v) for v in s1)
                + ") mm"
            )

            for component in COMPONENTS:
                cuf = np.asarray(
                    [float(r[f"cuf_{component}"]) for r in track_rows], dtype=float
                )
                fem = np.asarray(
                    [float(r[f"fem3d_{component}"]) for r in track_rows], dtype=float
                )

                fig, ax = plt.subplots(figsize=(8.5, 5.0))
                ax.plot(
                    x,
                    fem,
                    linewidth=1.6,
                    label="FEM3D",
                )
                ax.plot(
                    x,
                    cuf,
                    linestyle="--",
                    linewidth=1.6,
                    label="CSF-CUF",
                )
                ax.axhline(0.0, linewidth=0.8)
                ax.set_xlim(0.0, 1.0)
                ax.set_xlabel("x/L")
                ax.set_ylabel(Y_LABELS[component])
                ax.set_title(f"{polygon} - vertex {vertex_id} - {component}\n{coord_line}")
                ax.grid(True, alpha=0.25)
                ax.legend()
                fig.tight_layout()
                fig.savefig(output_dir / f"{track}_{component}.png", dpi=180)
                plt.close(fig)


def print_summary(rows: list[dict[str, float | int | str]]) -> None:
    print("\nPolygon-vertex CSF-CUF vs FEM3D comparison")
    print("==========================================")
    for polygon in POLYGON_ORDER:
        for vertex_id in range(VERTEX_COUNT[polygon]):
            track = f"{polygon}_v{vertex_id}"
            track_rows = [r for r in rows if r["track"] == track]
            track_rows.sort(key=lambda r: float(r["x_over_L"]))
            if not track_rows:
                continue

            first = track_rows[0]
            last = track_rows[-1]
            print(
                f"\n{track}: "
                f"CSF S0=({float(first['csf_X_mm']):.6g},"
                f"{float(first['csf_Y_mm']):.6g},"
                f"{float(first['csf_Z_mm']):.6g}) -> "
                f"S1=({float(last['csf_X_mm']):.6g},"
                f"{float(last['csf_Y_mm']):.6g},"
                f"{float(last['csf_Z_mm']):.6g})"
            )
            for component in COMPONENTS:
                diff = np.asarray(
                    [float(r[f"fem_minus_cuf_{component}"]) for r in track_rows],
                    dtype=float,
                )
                print(
                    f"  {component}: max |FEM3D-CUF| = "
                    f"{float(np.max(np.abs(diff))):.6e}"
                )



def _index_rows(rows: list[dict[str, float | int | str]]) -> dict[tuple[str, float], dict[str, float | int | str]]:
    result: dict[tuple[str, float], dict[str, float | int | str]] = {}
    for row in rows:
        key = (str(row["track"]), round(float(row["x_over_L"]), 12))
        if key in result:
            raise RuntimeError(f"duplicate profile row for {key}")
        result[key] = row
    return result


def write_combined_csv(
    prism_rows: list[dict[str, float | int | str]],
    taper_rows: list[dict[str, float | int | str]],
    path: Path,
) -> None:
    prism = _index_rows(prism_rows)
    taper = _index_rows(taper_rows)
    if set(prism) != set(taper):
        only_prism = sorted(set(prism) - set(taper))[:5]
        only_taper = sorted(set(taper) - set(prism))[:5]
        raise RuntimeError(
            "prismatic and tapered profile grids differ; "
            f"only_prism={only_prism}, only_taper={only_taper}"
        )

    fieldnames = [
        "track", "polygon", "vertex_id", "x_over_L",
        "prism_csf_X_mm", "prism_csf_Y_mm", "prism_csf_Z_mm",
        "taper_csf_X_mm", "taper_csf_Y_mm", "taper_csf_Z_mm",
    ]
    for component in COMPONENTS:
        fieldnames.extend(
            [
                f"prism_cuf_{component}",
                f"prism_fem3d_{component}",
                f"prism_fem_minus_cuf_{component}",
                f"taper_cuf_{component}",
                f"taper_fem3d_{component}",
                f"taper_fem_minus_cuf_{component}",
            ]
        )

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(prism, key=lambda k: (k[0], k[1])):
            rp = prism[key]
            rt = taper[key]
            row: dict[str, float | int | str] = {
                "track": rp["track"],
                "polygon": rp["polygon"],
                "vertex_id": rp["vertex_id"],
                "x_over_L": rp["x_over_L"],
                "prism_csf_X_mm": rp["csf_X_mm"],
                "prism_csf_Y_mm": rp["csf_Y_mm"],
                "prism_csf_Z_mm": rp["csf_Z_mm"],
                "taper_csf_X_mm": rt["csf_X_mm"],
                "taper_csf_Y_mm": rt["csf_Y_mm"],
                "taper_csf_Z_mm": rt["csf_Z_mm"],
            }
            for component in COMPONENTS:
                row[f"prism_cuf_{component}"] = rp[f"cuf_{component}"]
                row[f"prism_fem3d_{component}"] = rp[f"fem3d_{component}"]
                row[f"prism_fem_minus_cuf_{component}"] = rp[f"fem_minus_cuf_{component}"]
                row[f"taper_cuf_{component}"] = rt[f"cuf_{component}"]
                row[f"taper_fem3d_{component}"] = rt[f"fem3d_{component}"]
                row[f"taper_fem_minus_cuf_{component}"] = rt[f"fem_minus_cuf_{component}"]
            writer.writerow(row)


def plot_prism_vs_taper(
    prism_rows: list[dict[str, float | int | str]],
    taper_rows: list[dict[str, float | int | str]],
    output_dir: Path,
    *,
    line_width_scale: float,
) -> None:
    prism = _index_rows(prism_rows)
    taper = _index_rows(taper_rows)

    for polygon in POLYGON_ORDER:
        for vertex_id in range(VERTEX_COUNT[polygon]):
            track = f"{polygon}_v{vertex_id}"
            keys = sorted(
                [k for k in prism if k[0] == track],
                key=lambda k: k[1],
            )
            if not keys:
                continue
            if any(k not in taper for k in keys):
                raise RuntimeError(f"tapered rows missing for track {track}")

            x = np.asarray([float(prism[k]["x_over_L"]) for k in keys], dtype=float)
            p0, p1 = prism[keys[0]], prism[keys[-1]]
            t0, t1 = taper[keys[0]], taper[keys[-1]]

            prism_coord = (
                "Prism CSF S0=("
                + ", ".join(_fmt_coord(float(p0[k])) for k in ("csf_X_mm", "csf_Y_mm", "csf_Z_mm"))
                + ") -> S1=("
                + ", ".join(_fmt_coord(float(p1[k])) for k in ("csf_X_mm", "csf_Y_mm", "csf_Z_mm"))
                + ") mm"
            )
            taper_coord = (
                "Taper CSF S0=("
                + ", ".join(_fmt_coord(float(t0[k])) for k in ("csf_X_mm", "csf_Y_mm", "csf_Z_mm"))
                + ") -> S1=("
                + ", ".join(_fmt_coord(float(t1[k])) for k in ("csf_X_mm", "csf_Y_mm", "csf_Z_mm"))
                + ") mm"
            )

            for component in COMPONENTS:
                p_fem = np.asarray([float(prism[k][f"fem3d_{component}"]) for k in keys])
                p_cuf = np.asarray([float(prism[k][f"cuf_{component}"]) for k in keys])
                t_fem = np.asarray([float(taper[k][f"fem3d_{component}"]) for k in keys])
                t_cuf = np.asarray([float(taper[k][f"cuf_{component}"]) for k in keys])

                fig, ax = plt.subplots(figsize=(8.5, 5.4))
                prism_color = ax._get_lines.get_next_color()
                taper_color = ax._get_lines.get_next_color()
                profile_line_width = BASE_PROFILE_LINE_WIDTH * float(line_width_scale)
                zero_line_width = BASE_ZERO_LINE_WIDTH * float(line_width_scale)
                ax.plot(x, p_fem, color=prism_color, linewidth=profile_line_width, label="Prismatic FEM3D")
                ax.plot(x, p_cuf, color=prism_color, linestyle="--", linewidth=profile_line_width, label="Prismatic CSF-CUF")
                ax.plot(x, t_fem, color=taper_color, linewidth=profile_line_width, label="Tapered FEM3D")
                ax.plot(x, t_cuf, color=taper_color, linestyle="--", linewidth=profile_line_width, label="Tapered CSF-CUF")
                ax.axhline(0.0, linewidth=zero_line_width)
                ax.set_xlim(0.0, 1.0)
                ax.set_xlabel("x/L")
                ax.set_ylabel(Y_LABELS[component])
                ax.set_title(
                    f"{polygon} - vertex {vertex_id} - {component}\n"
                    f"{prism_coord}\n{taper_coord}"
                )
                ax.grid(True, alpha=0.25)
                ax.legend()
                fig.tight_layout()
                fig.savefig(output_dir / f"{track}_{component}.png", dpi=180)
                plt.close(fig)


def print_cross_case_summary(
    prism_rows: list[dict[str, float | int | str]],
    taper_rows: list[dict[str, float | int | str]],
) -> None:
    prism = _index_rows(prism_rows)
    taper = _index_rows(taper_rows)
    print("\nPrismatic vs tapered comparison")
    print("===============================")
    for component in COMPONENTS:
        prism_fem = np.asarray([float(r[f"fem3d_{component}"]) for r in prism.values()])
        taper_fem = np.asarray([float(taper[k][f"fem3d_{component}"]) for k in prism])
        prism_cuf = np.asarray([float(r[f"cuf_{component}"]) for r in prism.values()])
        taper_cuf = np.asarray([float(taper[k][f"cuf_{component}"]) for k in prism])
        print(
            f"{component}: max |taper-prism| "
            f"FEM3D={float(np.max(np.abs(taper_fem-prism_fem))):.6e}  "
            f"CUF={float(np.max(np.abs(taper_cuf-prism_cuf))):.6e}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare prismatic and tapered Table-9 cases. Each case contains a CUF "
            "checkpoint and its matching FEM3D NPZ. The script writes 36 four-curve "
            "plots on common axes plus one combined CSV."
        )
    )
    parser.add_argument("prism_cuf_npz", type=Path, help="prismatic compiled CUF .cuf.npz")
    parser.add_argument("taper_cuf_npz", type=Path, help="tapered compiled CUF .cuf.npz")
    parser.add_argument("--prism-fem3d", type=Path, required=True, help="prismatic FEM3D NPZ")
    parser.add_argument("--taper-fem3d", type=Path, required=True, help="tapered FEM3D NPZ")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("plots_table9_prism_vs_taper"),
        help="dedicated output directory (default: plots_table9_prism_vs_taper)",
    )
    parser.add_argument(
        "--points", type=int, default=DEFAULT_POINTS,
        help=f"uniform samples along x/L in [0,1] (default: {DEFAULT_POINTS})",
    )
    parser.add_argument("--a", type=float, default=REFERENCE_A, help="Table-9 a [mm]")
    parser.add_argument("--E", type=float, default=REFERENCE_E, help="Table-9 E [MPa]")
    parser.add_argument(
        "--line-width-scale",
        type=float,
        default=DEFAULT_LINE_WIDTH_SCALE,
        help=(
            "multiply all plotted line widths by this factor "
            f"(default: {DEFAULT_LINE_WIDTH_SCALE}, i.e. 30%% thinner than the current widths)"
        ),
    )
    return parser.parse_args()


def _load_case(cuf_path: Path, fem_path: Path, *, points: int, a: float, E: float):
    field = load_cuf_field(cuf_path)
    nodes, elements, displacement, amplitude, x0, x1 = load_fem3d(fem_path)
    domain_scale = max(1.0, abs(x0), abs(x1))
    domain_tol = 1.0e-10 * domain_scale
    if not math.isclose(field.x_start, x0, rel_tol=0.0, abs_tol=domain_tol) or not math.isclose(
        field.x_end, x1, rel_tol=0.0, abs_tol=domain_tol
    ):
        raise ValueError(
            "CUF and FEM3D longitudinal domains differ: "
            f"CUF=[{field.x_start},{field.x_end}], FEM3D=[{x0},{x1}]"
        )
    rows = build_rows(
        field, nodes, elements, displacement,
        x0=x0, x1=x1, amplitude=amplitude, a=a, E=E, points=points,
    )
    return rows, (x0, x1)


def main() -> None:
    args = parse_args()
    prism_cuf = args.prism_cuf_npz.resolve()
    taper_cuf = args.taper_cuf_npz.resolve()
    prism_fem = args.prism_fem3d.resolve()
    taper_fem = args.taper_fem3d.resolve()
    output_dir = args.output_dir.resolve()

    for path in (prism_cuf, taper_cuf, prism_fem, taper_fem):
        if not path.is_file():
            raise FileNotFoundError(path)

    points = int(args.points)
    if points < 2:
        raise ValueError("--points must be >= 2")

    prism_rows, prism_domain = _load_case(
        prism_cuf, prism_fem, points=points, a=float(args.a), E=float(args.E)
    )
    taper_rows, taper_domain = _load_case(
        taper_cuf, taper_fem, points=points, a=float(args.a), E=float(args.E)
    )
    if not np.allclose(prism_domain, taper_domain, rtol=0.0, atol=1.0e-10):
        raise ValueError(
            f"prismatic and tapered longitudinal domains differ: "
            f"prism={prism_domain}, taper={taper_domain}"
        )

    line_width_scale = float(args.line_width_scale)
    if line_width_scale <= 0.0:
        raise ValueError("--line-width-scale must be > 0")

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "vertex_profiles_prism_vs_taper.csv"
    write_combined_csv(prism_rows, taper_rows, csv_path)
    plot_prism_vs_taper(
        prism_rows,
        taper_rows,
        output_dir,
        line_width_scale=line_width_scale,
    )

    print_summary(prism_rows)
    print("\n--- tapered case ---")
    print_summary(taper_rows)
    print_cross_case_summary(prism_rows, taper_rows)

    print(f"\nPrismatic CUF   : {prism_cuf}")
    print(f"Prismatic FEM3D : {prism_fem}")
    print(f"Tapered CUF     : {taper_cuf}")
    print(f"Tapered FEM3D   : {taper_fem}")
    print(f"CSV             : {csv_path}")
    print(f"plots           : {output_dir}")
    print(f"line-width-scale: {line_width_scale}")
    print(f"samples         : {points} uniformly spaced positions over x/L in [0,1]")
    print("plots           : 12 polygon corners x 3 components = 36 line PNGs")
    print("each plot       : prismatic FEM3D/CUF + tapered FEM3D/CUF on the same axes")


if __name__ == "__main__":
    main()

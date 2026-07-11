"""
Create a standalone interactive HTML visual report from CSF pole-check CSV outputs.

Usage:
    python create_visual_report_v13.py <input_dir> <output_dir>

Expected input files:
    internal_actions.csv
    navier_stresses.csv
    shear_stresses.csv
    section_polygons.csv

The script does not read the CSF YAML/model. It consumes only the generated CSV data.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from plotly.offline.offline import get_plotlyjs
except Exception as exc:  # pragma: no cover
    raise RuntimeError("plotly is required: python -m pip install plotly") from exc


# -----------------------------------------------------------------------------
# Visual style parameters
# -----------------------------------------------------------------------------

CROSS_MARKER_SIZE = 5
CROSS_MARKER_LINE_WIDTH = 0.8
CROSS_MARKER_COLOR = "#111827"


# -----------------------------------------------------------------------------
# Basic parsing
# -----------------------------------------------------------------------------


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return float("nan")
    try:
        return float(value)
    except Exception:
        return float("nan")


def _to_int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        f = float(value)
    except Exception:
        return None
    if not math.isfinite(f):
        return None
    return int(f)


def _z_key(z: Any) -> str:
    return f"{float(z):.12g}"


def _strip_csf_name(name: Any) -> str:
    return str(name or "").split("@", 1)[0].strip()


def _is_s_polygon_name(name: Any) -> bool:
    base_name = _strip_csf_name(name)
    return base_name.split("_")[-1] == "S"


def _direction_from_component(component: str) -> str:
    return "x" if str(component).startswith("tau_x_") else "y"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _read_section_polygons(path: Path) -> list[dict[str, Any]]:
    """
    Read the CSF block-style polygon vertex export.

    Expected blocks:
        ## GEOMETRY EXPORT ##
        # z=0.0
        idx_polygon,idx_container,...,x,y
        ...
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing required input file: {path}")

    out: list[dict[str, Any]] = []
    current_z: float | None = None
    header: list[str] | None = None

    with open(path, "r", encoding="utf-8", newline="") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("##"):
                header = None
                continue

            if line.startswith("#"):
                if line.startswith("# z="):
                    current_z = float(line.split("=", 1)[1].strip())
                    header = None
                continue

            if line.startswith("idx_polygon,"):
                header = next(csv.reader([line]))
                continue

            if current_z is None or header is None:
                continue

            values = next(csv.reader([line]))
            row = dict(zip(header, values))
            row["z"] = current_z

            out.append(
                {
                    "z": current_z,
                    "z_key": _z_key(current_z),
                    "idx_polygon": int(row["idx_polygon"]),
                    "idx_container": _to_int_or_none(row.get("idx_container")),
                    "s0_name": str(row.get("s0_name", "")),
                    "s1_name": str(row.get("s1_name", "")),
                    "w": _to_float(row.get("w")),
                    "shear_w": _to_float(row.get("shear_w")),
                    "poisson": _to_float(row.get("poisson")),
                    "vertex_i": int(row["vertex_i"]),
                    "x": _to_float(row.get("x")),
                    "y": _to_float(row.get("y")),
                }
            )

    if not out:
        raise ValueError(f"No polygon vertices parsed from: {path}")

    return out


# -----------------------------------------------------------------------------
# Data assembly
# -----------------------------------------------------------------------------


def _compute_depths(polygons_by_idx: dict[int, dict[str, Any]]) -> None:
    cache: dict[int, int] = {}

    def depth(idx: int, stack: set[int] | None = None) -> int:
        if idx in cache:
            return cache[idx]
        if stack is None:
            stack = set()
        if idx in stack:
            cache[idx] = 0
            return 0

        parent = polygons_by_idx[idx].get("idx_container")
        if parent is None or parent not in polygons_by_idx:
            cache[idx] = 0
            return 0

        stack.add(idx)
        cache[idx] = depth(int(parent), stack) + 1
        stack.remove(idx)
        return cache[idx]

    for idx in polygons_by_idx:
        polygons_by_idx[idx]["depth"] = depth(idx)



def _assemble_sections(
    geometry_rows: list[dict[str, Any]],
    navier_rows: list[dict[str, str]],
    shear_rows: list[dict[str, str]],
) -> dict[str, Any]:
    sections: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)

    for r in geometry_rows:
        zk = r["z_key"]
        idx = int(r["idx_polygon"])
        poly = sections[zk].get(idx)
        if poly is None:
            poly = {
                "z": float(r["z"]),
                "idx": idx,
                "idx_container": r["idx_container"],
                "s0_name": r["s0_name"],
                "s1_name": r["s1_name"],
                "polygon_name": r["s0_name"],
                "w": float(r["w"]),
                "shear_w": float(r["shear_w"]),
                "poisson": float(r["poisson"]),
                "depth": 0,
                "vertices": [],
                "values": {
                    "w": float(r["w"]),
                    "shear_w": float(r["shear_w"]),
                    "poisson": float(r["poisson"]),
                },
            }
            sections[zk][idx] = poly

        poly["vertices"].append(
            {"i": int(r["vertex_i"]), "x": float(r["x"]), "y": float(r["y"])}
        )

    for zk, by_idx in sections.items():
        _compute_depths(by_idx)
        for poly in by_idx.values():
            poly["values"]["depth"] = int(poly["depth"])
            poly["vertices"].sort(key=lambda v: int(v["i"]))

    for r in navier_rows:
        zk = _z_key(r["z"])
        idx = int(r["polygon_idx"])
        poly = sections.get(zk, {}).get(idx)
        if poly is None:
            continue
        for key in ("sigma_min", "sigma_max", "sigma_extreme"):
            poly["values"][key] = _to_float(r.get(key))

        points = poly.setdefault("points", {})
        points["sigma_min"] = {
            "x": _to_float(r.get("x_min")),
            "y": _to_float(r.get("y_min")),
            "component": "sigma_min",
            "value": _to_float(r.get("sigma_min")),
        }
        points["sigma_max"] = {
            "x": _to_float(r.get("x_max")),
            "y": _to_float(r.get("y_max")),
            "component": "sigma_max",
            "value": _to_float(r.get("sigma_max")),
        }
        x_ext = r.get("x", r.get("x_extreme"))
        y_ext = r.get("y", r.get("y_extreme"))
        points["sigma_extreme"] = {
            "x": _to_float(x_ext),
            "y": _to_float(y_ext),
            "component": "sigma_extreme",
            "value": _to_float(r.get("sigma_extreme")),
        }

    for r in shear_rows:
        zk = _z_key(r["z"])
        idx = int(r["polygon_idx"])
        poly = sections.get(zk, {}).get(idx)
        if poly is None:
            continue

        poly["polygon_name"] = str(r.get("polygon_name", poly["s0_name"]))

        for key in (
            "tau_x_min",
            "tau_x_max",
            "tau_y_min",
            "tau_y_max",
            "tau_x_mean",
            "tau_y_mean",
            "scan_count_x",
            "scan_count_y",
        ):
            poly["values"][key] = _to_float(r.get(key))

        points = poly.setdefault("points", {})
        shear_point_specs = {
            "tau_x_min": ("x_tau_x_min", "y_tau_x_min"),
            "tau_x_max": ("x_tau_x_max", "y_tau_x_max"),
            "tau_y_min": ("x_tau_y_min", "y_tau_y_min"),
            "tau_y_max": ("x_tau_y_max", "y_tau_y_max"),
        }
        candidates: list[tuple[str, float, float, float]] = []
        for key, (x_key, y_key) in shear_point_specs.items():
            value = _to_float(r.get(key))
            x_val = _to_float(r.get(x_key))
            y_val = _to_float(r.get(y_key))
            points[key] = {
                "x": x_val,
                "y": y_val,
                "component": key,
                "direction": _direction_from_component(key),
                "value": value,
            }
            if math.isfinite(value):
                candidates.append((key, value, x_val, y_val))

        if candidates:
            key_best, value_best, x_best, y_best = max(
                candidates, key=lambda item: abs(item[1])
            )
            direction_best = _direction_from_component(key_best)
            poly["values"]["tau_governing"] = value_best
            poly["values"]["tau_governing_direction"] = direction_best
            points["tau_governing"] = {
                "x": x_best,
                "y": y_best,
                "component": key_best,
                "direction": direction_best,
                "value": value_best,
            }
        else:
            poly["values"]["tau_governing"] = float("nan")
            poly["values"]["tau_governing_direction"] = ""
            points["tau_governing"] = {
                "x": float("nan"),
                "y": float("nan"),
                "component": "",
                "direction": "",
                "value": float("nan"),
            }

    z_keys = sorted(sections.keys(), key=lambda k: float(k))
    serial_sections: dict[str, list[dict[str, Any]]] = {}
    for zk in z_keys:
        serial_sections[zk] = [sections[zk][idx] for idx in sorted(sections[zk])]

    return {"z_values": z_keys, "sections": serial_sections}



def _actions_payload(rows: list[dict[str, str]]) -> dict[str, list[float]]:
    keys = ["z", "N", "Mx", "My", "Tx_jourawski", "Ty_jourawski", "Tz"]
    out: dict[str, list[float]] = {k: [] for k in keys}
    for r in sorted(rows, key=lambda row: float(row["z"])):
        for k in keys:
            out[k].append(_to_float(r.get(k)))
    return out



def _shear_extreme_rows(
    rows: list[dict[str, str]],
    *,
    select_s: bool,
) -> list[dict[str, Any]]:
    """Return the S or NON-S polygons sharing maximum ``abs(tau_governing)`` per z."""

    by_z: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        polygon_name = str(row.get("polygon_name", ""))
        if _is_s_polygon_name(polygon_name) == bool(select_s):
            by_z[_z_key(row["z"])].append(row)

    components = {
        "tau_x_min": ("x_tau_x_min", "y_tau_x_min"),
        "tau_x_max": ("x_tau_x_max", "y_tau_x_max"),
        "tau_y_min": ("x_tau_y_min", "y_tau_y_min"),
        "tau_y_max": ("x_tau_y_max", "y_tau_y_max"),
    }

    out: list[dict[str, Any]] = []
    for zk in sorted(by_z.keys(), key=lambda key: float(key)):
        candidates: list[dict[str, Any]] = []

        for row in by_z[zk]:
            for component, (x_key, y_key) in components.items():
                value = _to_float(row.get(component))
                if not math.isfinite(value):
                    continue

                candidates.append(
                    {
                        "z": _to_float(row.get("z")),
                        "tau_governing": value,
                        "direction": _direction_from_component(component),
                        "polygon_idx": int(row["polygon_idx"]),
                        "polygon_name": str(row["polygon_name"]),
                        "x": _to_float(row.get(x_key)),
                        "y": _to_float(row.get(y_key)),
                    }
                )

        if not candidates:
            continue

        max_abs_tau = max(abs(item["tau_governing"]) for item in candidates)
        tolerance = max(max_abs_tau, 1.0) * 1.0e-12
        matches = [
            item
            for item in candidates
            if abs(abs(item["tau_governing"]) - max_abs_tau) <= tolerance
        ]
        matches.sort(
            key=lambda item: (
                int(item["polygon_idx"]),
                str(item["direction"]),
                float(item["x"]),
                float(item["y"]),
            )
        )
        out.extend(matches)

    return out


# -----------------------------------------------------------------------------
# HTML generation
# -----------------------------------------------------------------------------


QUANTITIES = [
    {"id": "depth", "label": "Hierarchy depth", "signed": False},
    {"id": "w", "label": "w", "signed": False},
    {"id": "shear_w", "label": "shear_w", "signed": False},
    {"id": "poisson", "label": "poisson", "signed": False},
    {"id": "sigma_min", "label": "Navier sigma_min", "signed": True},
    {"id": "sigma_max", "label": "Navier sigma_max", "signed": True},
    {"id": "sigma_extreme", "label": "Navier sigma_extreme", "signed": True},
    {"id": "tau_x_min", "label": "Jourawski tau_x_min", "signed": True},
    {"id": "tau_x_max", "label": "Jourawski tau_x_max", "signed": True},
    {"id": "tau_y_min", "label": "Jourawski tau_y_min", "signed": True},
    {"id": "tau_y_max", "label": "Jourawski tau_y_max", "signed": True},
    {"id": "tau_x_mean", "label": "Jourawski tau_x_mean", "signed": True},
    {"id": "tau_y_mean", "label": "Jourawski tau_y_mean", "signed": True},
    {"id": "tau_governing", "label": "Jourawski tau_governing", "signed": True},
    {"id": "scan_count_x", "label": "scan_count_x", "signed": False},
    {"id": "scan_count_y", "label": "scan_count_y", "signed": False},
]

STRESS_QUANTITIES = [
    {"id": "sigma_min", "label": "Navier sigma_min", "signed": True},
    {"id": "sigma_max", "label": "Navier sigma_max", "signed": True},
    {"id": "sigma_extreme", "label": "Navier sigma_extreme", "signed": True},
    {"id": "tau_x_min", "label": "Jourawski tau_x_min", "signed": True},
    {"id": "tau_x_max", "label": "Jourawski tau_x_max", "signed": True},
    {"id": "tau_y_min", "label": "Jourawski tau_y_min", "signed": True},
    {"id": "tau_y_max", "label": "Jourawski tau_y_max", "signed": True},
    {"id": "tau_governing", "label": "Jourawski tau_governing", "signed": True},
]


def _json_script_object(name: str, obj: Any) -> str:
    raw = json.dumps(obj, allow_nan=True, separators=(",", ":"))
    raw = raw.replace("</", "<\\/")
    return f"const {name} = {raw};"


def _build_html(
    *,
    actions: dict[str, list[float]],
    section_data: dict[str, Any],
    shear_extremes_s: list[dict[str, Any]],
    shear_extremes_non_s: list[dict[str, Any]],
) -> str:
    plotly_js = get_plotlyjs()
    css = """
    :root { --fg:#1f2937; --muted:#6b7280; --line:#d1d5db; --bg:#ffffff; --panel:#f9fafb; }
    body { margin:0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--fg); background:var(--bg); }
    header { padding: 20px 28px; border-bottom:1px solid var(--line); }
    h1 { margin:0; font-size:24px; }
    h2 { margin:30px 0 12px; font-size:19px; }
    h3 { margin:18px 0 8px; font-size:15px; }
    main { padding: 0 28px 40px; }
    .grid { display:grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap:18px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px; }
    .plot { height:360px; }
    .section-layout { display:grid; grid-template-columns: 270px 1fr; gap:18px; align-items:start; }
    .controls { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px; position:sticky; top:12px; }
    label { display:block; font-size:12px; color:var(--muted); margin-top:12px; margin-bottom:4px; }
    select { width:100%; padding:7px; border:1px solid var(--line); border-radius:7px; background:white; }
    #sectionPlot { height:720px; background:white; border:1px solid var(--line); border-radius:10px; }
    #rangeInfo { margin-top:12px; font-size:12px; color:var(--muted); line-height:1.35; }
    .extremeTableWrap, #polygonStressWrap { max-height:520px; overflow:auto; border:1px solid var(--line); border-radius:10px; }
    .stress-gallery { display:grid; grid-template-columns: repeat(2, minmax(420px, 1fr)); gap:18px; margin-top:12px; }
    .stress-card { background:white; border:1px solid var(--line); border-radius:10px; padding:8px; }
    .stress-plot { height:520px; }
    table { width:100%; border-collapse:collapse; font-size:12px; }
    th { position:sticky; top:0; background:#f3f4f6; border-bottom:1px solid var(--line); text-align:right; padding:6px 8px; }
    td { border-bottom:1px solid #e5e7eb; text-align:right; padding:5px 8px; white-space:nowrap; }
    td.name, th.name { text-align:left; }
    .note { color:var(--muted); font-size:13px; }
    .legend-grid { display:grid; grid-template-columns: repeat(3, minmax(240px, 1fr)); gap:12px; margin: 10px 0 14px; }
    .legend-card { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px; font-size:13px; line-height:1.35; }
    .legend-card b { display:block; margin-bottom:4px; }
    #legendTableWrap { max-height:430px; overflow:auto; border:1px solid var(--line); border-radius:10px; }
    @media (max-width: 1000px) { .grid { grid-template-columns:1fr; } .legend-grid { grid-template-columns:1fr; } .section-layout { grid-template-columns:1fr; } .controls { position:relative; } }
    """

    legend_rows = [
        (
            "Hierarchy depth",
            "Topological containment depth. 0 is the outer/root polygon; larger values indicate nested polygons.",
            "Depth palette.",
        ),
        (
            "w",
            "Axial/bending participation or absolute weight read from section_polygons.csv.",
            "Viridis min/max scale.",
        ),
        (
            "shear_w",
            "Shear/torsion participation or absolute shear weight read from section_polygons.csv.",
            "Viridis min/max scale.",
        ),
        (
            "poisson",
            "Poisson ratio assigned to the polygon.",
            "Viridis min/max scale.",
        ),
        (
            "Navier sigma_min",
            "Minimum signed vertex normal stress in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Navier sigma_max",
            "Maximum signed vertex normal stress in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Navier sigma_extreme",
            "Signed vertex normal stress with maximum absolute value in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_x_min",
            "Minimum signed Jourawski shear-stress value reported for the x scan in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_x_max",
            "Maximum signed Jourawski shear-stress value reported for the x scan in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_y_min",
            "Minimum signed Jourawski shear-stress value reported for the y scan in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_y_max",
            "Maximum signed Jourawski shear-stress value reported for the y scan in the polygon.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_x_mean",
            "Mean of the reported tau_x scan values for the polygon, when present in the CSV.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_y_mean",
            "Mean of the reported tau_y scan values for the polygon, when present in the CSV.",
            "Signed blue-white-red scale.",
        ),
        (
            "Jourawski tau_governing",
            "tau_governing is the signed Jourawski shear-stress value having the largest absolute magnitude in the polygon, selected among tau_x_min, tau_x_max, tau_y_min and tau_y_max. The original sign is preserved; direction identifies x or y.",
            "Signed blue-white-red scale.",
        ),
        (
            "scan_count_x",
            "Number of x-scan values reported for the polygon.",
            "Viridis min/max scale.",
        ),
        (
            "scan_count_y",
            "Number of y-scan values reported for the polygon.",
            "Viridis min/max scale.",
        ),
    ]
    legend_rows_html = []
    for quantity, meaning, scale in legend_rows:
        legend_rows_html.append(
            "<tr>"
            f"<td class='name'>{html.escape(quantity)}</td>"
            f"<td class='name'>{html.escape(meaning)}</td>"
            f"<td class='name'>{html.escape(scale)}</td>"
            "</tr>"
        )

    def build_extreme_rows_html(rows: list[dict[str, Any]]) -> str:
        html_rows: list[str] = []
        for row in rows:
            html_rows.append(
                "<tr>"
                f"<td>{float(row['z']):.6g}</td>"
                f"<td>{float(row['tau_governing']):.6e}</td>"
                f"<td class='name'>{html.escape(str(row['direction']))}</td>"
                f"<td>{int(row['polygon_idx'])}</td>"
                f"<td class='name'>{html.escape(str(row['polygon_name']))}</td>"
                f"<td>{float(row['x']):.6e}</td>"
                f"<td>{float(row['y']):.6e}</td>"
                "</tr>"
            )
        return "".join(html_rows)

    extreme_rows_s_html = build_extreme_rows_html(shear_extremes_s)
    extreme_rows_non_s_html = build_extreme_rows_html(shear_extremes_non_s)

    js_data = "\n".join(
        [
            _json_script_object("ACTIONS", actions),
            _json_script_object("SECTION_DATA", section_data),
            _json_script_object("QUANTITIES", QUANTITIES),
            _json_script_object("STRESS_QUANTITIES", STRESS_QUANTITIES),
            _json_script_object("CROSS_MARKER_SIZE", int(CROSS_MARKER_SIZE)),
            _json_script_object("CROSS_MARKER_LINE_WIDTH", float(CROSS_MARKER_LINE_WIDTH)),
            _json_script_object("CROSS_MARKER_COLOR", str(CROSS_MARKER_COLOR)),
        ]
    )

    js_runtime = r"""
    function finite(v) { return typeof v === 'number' && Number.isFinite(v); }
    function fmt(v) {
      if (!finite(v)) return 'nan';
      const av = Math.abs(v);
      if ((av !== 0 && (av >= 1e4 || av < 1e-3))) return v.toExponential(6);
      return v.toPrecision(7);
    }
    function esc(s) {
      return String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[ch]));
    }
    function polygonCentroid(verts) {
      let a2 = 0, cx = 0, cy = 0;
      const n = verts.length;
      if (n < 3) return {x: NaN, y: NaN};
      for (let i=0; i<n; i++) {
        const p0 = verts[i], p1 = verts[(i+1)%n];
        const cross = p0.x * p1.y - p1.x * p0.y;
        a2 += cross;
        cx += (p0.x + p1.x) * cross;
        cy += (p0.y + p1.y) * cross;
      }
      if (Math.abs(a2) < 1e-30) {
        return {x: verts.reduce((s,v)=>s+v.x,0)/n, y: verts.reduce((s,v)=>s+v.y,0)/n};
      }
      return {x: cx / (3*a2), y: cy / (3*a2)};
    }
    function polygonAbsArea(verts) {
      let a2 = 0;
      const n = verts.length;
      if (n < 3) return 0;
      for (let i=0; i<n; i++) {
        const p0 = verts[i], p1 = verts[(i+1)%n];
        a2 += p0.x * p1.y - p1.x * p0.y;
      }
      return Math.abs(0.5 * a2);
    }

    function polygonDrawArea(p) {
      return polygonAbsArea((p && p.vertices) ? p.vertices : []);
    }
    function orderedPolygonsForDrawing(polys) {
      // Draw larger / outer polygons first and smaller / nested polygons later.
      // Plotly hit-testing then sees the visible local sector instead of an
      // overlapping carrier/container polygon drawn above it.
      const out = [...(polys || [])];
      out.sort((a, b) => {
        const aa = polygonDrawArea(a);
        const bb = polygonDrawArea(b);
        const areaTol = Math.max(aa, bb, 1.0) * 1.0e-12;
        if (Math.abs(bb - aa) > areaTol) return bb - aa;
        const da = Number.isFinite(a.depth) ? a.depth : 0;
        const db = Number.isFinite(b.depth) ? b.depth : 0;
        if (da !== db) return da - db;
        return (a.idx || 0) - (b.idx || 0);
      });
      return out;
    }

    function sectionBounds(polys) {
      const xs = [], ys = [];
      for (const p of polys) {
        for (const v of (p.vertices || [])) {
          if (finite(v.x) && finite(v.y)) { xs.push(v.x); ys.push(v.y); }
        }
      }
      if (!xs.length || !ys.length) {
        return {xmin:-1, xmax:1, ymin:-1, ymax:1, dx:2, dy:2, scale:2};
      }
      const xmin = Math.min(...xs), xmax = Math.max(...xs);
      const ymin = Math.min(...ys), ymax = Math.max(...ys);
      const dx = Math.max(xmax - xmin, 1.0e-12);
      const dy = Math.max(ymax - ymin, 1.0e-12);
      return {xmin, xmax, ymin, ymax, dx, dy, scale:Math.max(Math.hypot(dx, dy), 1.0e-12)};
    }
    function sectionScale(polys) {
      return sectionBounds(polys).scale;
    }
    function boxesOverlap(a, b) {
      return !(a.xmax < b.xmin || a.xmin > b.xmax || a.ymax < b.ymin || a.ymin > b.ymax);
    }
    function labelBox(label, x, y, bounds) {
      const text = String(label.text || '');
      const width = bounds.dx * Math.max(0.020, 0.0068 * text.length);
      const height = bounds.dy * 0.028;
      return {xmin:x - width/2, xmax:x + width/2, ymin:y - height/2, ymax:y + height/2};
    }

    function labelParts(text) {
      const s = String(text || '');
      const m = s.match(/^(.*)_([^_]+)$/);
      if (!m) return {base:s, suffix:''};
      return {base:m[1], suffix:m[2]};
    }
    function swapSteelCoverLabelTexts(labels) {
      // In the CSF sector-grid naming convention, <base>_S and <base>_CH
      // may share the same local position. For the hierarchy map the visible
      // label is swapped so the steel label is displayed on the cover-host
      // position and the CH label is moved to the companion steel position.
      const out = labels.map(d => ({...d}));
      const byBase = new Map();
      for (let i = 0; i < out.length; i++) {
        const p = labelParts(out[i].text);
        if (!byBase.has(p.base)) byBase.set(p.base, {});
        byBase.get(p.base)[p.suffix] = i;
      }
      for (const group of byBase.values()) {
        if (group.S !== undefined && group.CH !== undefined) {
          const iS = group.S;
          const iCH = group.CH;
          const tmp = out[iS].text;
          out[iS].text = out[iCH].text;
          out[iCH].text = tmp;
        }
      }
      return out;
    }
    function placeHierarchyLabels(labels, bounds) {
      const ordered = labels.map((d, i) => ({...d, originalIndex:i}));
      function chsRank(text) {
        const p = labelParts(text);
        if (p.suffix === 'S') return 0;
        if (p.suffix === 'CH') return 1;
        return 2;
      }
      ordered.sort((a, b) => {
        const pa = labelParts(a.text);
        const pb = labelParts(b.text);
        if (pa.base === pb.base) {
          const ra = chsRank(a.text);
          const rb = chsRank(b.text);
          if (ra !== rb && (ra < 2 || rb < 2)) return ra - rb;
        }
        const aa = finite(a.area) ? a.area : 0;
        const bb = finite(b.area) ? b.area : 0;
        if (bb !== aa) return bb - aa;
        return String(a.text).localeCompare(String(b.text), undefined, {numeric:true});
      });

      const placed = [];
      const result = new Array(labels.length);
      const baseStep = bounds.scale * 0.026;
      const radialStep = bounds.scale * 0.018;
      const angleSteps = 16;

      for (const label of ordered) {
        const baseAngle = Math.atan2(label.y, label.x);
        const candidates = [{x:label.x, y:label.y}];

        for (let ring=1; ring<=7; ring++) {
          const r = baseStep + radialStep * (ring - 1);
          for (let k=0; k<angleSteps; k++) {
            const a = baseAngle + (2 * Math.PI * k / angleSteps);
            candidates.push({x:label.x + r * Math.cos(a), y:label.y + r * Math.sin(a)});
          }
        }

        let chosen = candidates[candidates.length - 1];
        for (const c of candidates) {
          const b = labelBox(label, c.x, c.y, bounds);
          let ok = true;
          for (const existing of placed) {
            if (boxesOverlap(b, existing.box)) { ok = false; break; }
          }
          if (ok) { chosen = c; break; }
        }

        const box = labelBox(label, chosen.x, chosen.y, bounds);
        placed.push({box, label});
        result[label.originalIndex] = {...label, x:chosen.x, y:chosen.y};
      }
      return result;
    }
    function hexToRgb(hex) {
      const h = hex.replace('#','');
      return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
    }
    function rgbToHex(rgb) {
      return '#' + rgb.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2,'0')).join('');
    }
    function interp(a,b,t) { return a + (b-a)*t; }
    function colorBetween(c1,c2,t) {
      const a = hexToRgb(c1), b = hexToRgb(c2);
      return rgbToHex([interp(a[0],b[0],t), interp(a[1],b[1],t), interp(a[2],b[2],t)]);
    }
    function viridis(t) {
      const stops = [
        [0.00,'#440154'], [0.25,'#3b528b'], [0.50,'#21918c'], [0.75,'#5ec962'], [1.00,'#fde725']
      ];
      return scaleStops(stops, t);
    }
    function blueWhiteRed(t) {
      const stops = [[0,'#2166ac'], [0.5,'#f7f7f7'], [1,'#b2182b']];
      return scaleStops(stops, t);
    }
    function scaleStops(stops, t) {
      t = Math.max(0, Math.min(1, t));
      for (let i=0; i<stops.length-1; i++) {
        if (t >= stops[i][0] && t <= stops[i+1][0]) {
          const tt = (t - stops[i][0]) / (stops[i+1][0] - stops[i][0]);
          return colorBetween(stops[i][1], stops[i+1][1], tt);
        }
      }
      return stops[stops.length-1][1];
    }
    function plotLine(div, traces, title, ytitle) {
      Plotly.newPlot(div, traces, {
        title: {text:title, x:0.02, xanchor:'left'},
        margin: {l:70, r:25, t:45, b:55},
        xaxis: {title:'z'},
        yaxis: {title:ytitle, zeroline:true},
        legend: {orientation:'h'}
      }, {responsive:true, displaylogo:false});
    }
    function initGlobalPlots() {
      const z = ACTIONS.z;
      plotLine('plotN', [{x:z, y:ACTIONS.N, name:'N', mode:'lines+markers'}], 'Axial force', 'N');
      plotLine('plotM', [
        {x:z, y:ACTIONS.Mx, name:'Mx', mode:'lines+markers'},
        {x:z, y:ACTIONS.My, name:'My', mode:'lines+markers'}
      ], 'Bending moments', 'M');
      plotLine('plotShear', [
        {x:z, y:ACTIONS.Tx_jourawski, name:'Tx_jourawski', mode:'lines+markers'},
        {x:z, y:ACTIONS.Ty_jourawski, name:'Ty_jourawski', mode:'lines+markers'}
      ], 'Shear components passed to Jourawski', 'T');
      plotLine('plotTz', [{x:z, y:ACTIONS.Tz, name:'Tz', mode:'lines+markers'}], 'Torsional moment', 'Tz');
    }
    function quantityById(id) { return QUANTITIES.find(q => q.id === id) || QUANTITIES[0]; }
    function initControls() {
      const zSelect = document.getElementById('zSelect');
      SECTION_DATA.z_values.forEach(z => {
        const opt = document.createElement('option');
        opt.value = z;
        opt.textContent = z;
        zSelect.appendChild(opt);
      });
      const qSelect = document.getElementById('quantitySelect');
      QUANTITIES.forEach(q => {
        const opt = document.createElement('option');
        opt.value = q.id;
        opt.textContent = q.label;
        qSelect.appendChild(opt);
      });
      zSelect.addEventListener('change', renderSection);
      qSelect.addEventListener('change', renderSection);
    }
    function signedQuantityValue(p, q) {
      if (!p) return NaN;
      const rawValue = p.values ? p.values[q.id] : NaN;
      const pointValue = p.points && p.points[q.id] && finite(p.points[q.id].value)
        ? p.points[q.id].value
        : NaN;
      if (q.signed && finite(pointValue)) return pointValue;
      return rawValue;
    }
    function valueRange(polys, q) {
      const vals = polys.map(p => signedQuantityValue(p, q)).filter(finite);
      if (vals.length === 0) return {min:NaN, max:NaN, abs:NaN, vals:[]};
      const minv = Math.min(...vals), maxv = Math.max(...vals);
      const abs = Math.max(...vals.map(v => Math.abs(v)));
      return {min:minv, max:maxv, abs:abs, vals:vals};
    }
    function colorForValue(value, range, q, depth) {
      if (!finite(value)) return '#eeeeee';
      if (q.id === 'depth') {
        const palette = ['#f3f4f6','#dbeafe','#bfdbfe','#93c5fd','#60a5fa','#3b82f6','#1d4ed8'];
        return palette[Math.max(0, Math.min(palette.length-1, depth|0))];
      }
      if (q.signed) {
        const a = finite(range.abs) && range.abs > 0 ? range.abs : 1;
        return blueWhiteRed(0.5 + 0.5 * value / a);
      }
      const span = range.max - range.min;
      const t = span > 0 ? (value - range.min) / span : 0.5;
      return viridis(t);
    }

    function quantityColorScale(q) {
      if (q.signed) return [[0,'#2166ac'], [0.5,'#f7f7f7'], [1,'#b2182b']];
      return [[0.00,'#440154'], [0.25,'#3b528b'], [0.50,'#21918c'], [0.75,'#5ec962'], [1.00,'#fde725']];
    }
    function quantityColorLimits(range, q) {
      if (q.signed) {
        const a = finite(range.abs) && range.abs > 0 ? range.abs : 1;
        return {cmin:-a, cmax:a};
      }
      let cmin = finite(range.min) ? range.min : 0;
      let cmax = finite(range.max) ? range.max : 1;
      if (cmax === cmin) { cmax = cmin + 1; }
      return {cmin, cmax};
    }
    function quantityLegendText(range, q) {
      if (q.id === 'depth') {
        return 'legend: hierarchy depth, 0 = outer/root polygon; larger values = nested polygons';
      }
      if (q.signed) {
        const a = finite(range.abs) && range.abs > 0 ? range.abs : 1;
        return 'legend: blue = negative, white = zero, red = positive; symmetric scale ±' + fmt(a);
      }
      return 'legend: viridis scale; min=' + fmt(range.min) + ', max=' + fmt(range.max);
    }
    function sectionColorbarTrace(bounds, range, q) {
      const limits = quantityColorLimits(range, q);
      return {
        type:'scatter', mode:'markers',
        x:[bounds.xmax + bounds.dx * 10, bounds.xmax + bounds.dx * 10],
        y:[bounds.ymax + bounds.dy * 10, bounds.ymax + bounds.dy * 10],
        marker:{
          size:0,
          color:[limits.cmin, limits.cmax],
          colorscale:quantityColorScale(q),
          cmin:limits.cmin,
          cmax:limits.cmax,
          showscale:true,
          colorbar:{title:q.label, thickness:14, len:0.78}
        },
        hoverinfo:'skip',
        showlegend:false
      };
    }
    function stressDivId(zIndex, qId) {
      return 'stress_z' + zIndex + '_' + qId;
    }
    function initStressGalleryContainers() {
      const gallery = document.getElementById('stressGallery');
      if (!gallery) return;
      gallery.innerHTML = SECTION_DATA.z_values.map((z, zi) => {
        const cards = STRESS_QUANTITIES.map(q =>
          '<div class="stress-card"><div id="' + stressDivId(zi, q.id) + '" class="stress-plot"></div></div>'
        ).join('');
        return '<section class="station-stress-block">' +
          '<h3>z = ' + z + '</h3>' +
          '<div class="stress-gallery">' + cards + '</div>' +
        '</section>';
      }).join('');
    }
    function stressPointHover(p, q, point, value) {
      const component = point && point.component ? point.component : q.id;
      const direction = point && point.direction
        ? point.direction
        : (component.indexOf('tau_x_') === 0 ? 'x' : (component.indexOf('tau_y_') === 0 ? 'y' : ''));
      const signedValue = point && finite(point.value) ? point.value : value;
      const shownValue = q.signed ? signedValue : value;
      const rows = [
        '<b>z</b>: ' + fmt(p.z),
        '<b>polygon_idx</b>: ' + p.idx,
        '<b>polygon_name</b>: ' + esc(p.polygon_name || p.s0_name),
        '<b>quantity</b>: ' + esc(q.label),
        '<b>value</b>: ' + fmt(shownValue)
      ];
      if (direction) rows.push('<b>direction</b>: ' + esc(direction));
      rows.push('<b>x</b>: ' + fmt(point ? point.x : NaN));
      rows.push('<b>y</b>: ' + fmt(point ? point.y : NaN));
      return rows.join('<br>');
    }

    function polygonLineSegmentsForCoord(verts, axis, coord) {
      if (!verts || verts.length < 3 || !finite(coord)) return [];
      const values = [];
      const eps = 1.0e-12;
      for (let i = 0; i < verts.length; i++) {
        const p1 = verts[i];
        const p2 = verts[(i + 1) % verts.length];
        const c1 = axis === 'x' ? p1.x : p1.y;
        const c2 = axis === 'x' ? p2.x : p2.y;
        const o1 = axis === 'x' ? p1.y : p1.x;
        const o2 = axis === 'x' ? p2.y : p2.x;
        if (!finite(c1) || !finite(c2) || !finite(o1) || !finite(o2)) continue;
        if (Math.abs(c1 - coord) <= eps && Math.abs(c2 - coord) <= eps) continue;
        const crosses = (c1 <= coord && coord < c2) || (c2 <= coord && coord < c1);
        if (!crosses) continue;
        const denom = c2 - c1;
        if (Math.abs(denom) <= eps) continue;
        const t = (coord - c1) / denom;
        values.push(o1 + t * (o2 - o1));
      }
      values.sort((a, b) => a - b);
      const unique = [];
      for (const v of values) {
        if (!finite(v)) continue;
        if (!unique.length || Math.abs(v - unique[unique.length - 1]) > eps) unique.push(v);
      }
      const segments = [];
      for (let i = 0; i + 1 < unique.length; i += 2) {
        const a = unique[i], b = unique[i + 1];
        if (Math.abs(b - a) > eps) segments.push([a, b]);
      }
      return segments;
    }
    function representativePointOnPolygonCut(verts, axis, coord, fallback) {
      const segments = polygonLineSegmentsForCoord(verts, axis, coord);
      if (!segments.length) return fallback;
      let lengthSum = 0.0;
      let midSum = 0.0;
      for (const seg of segments) {
        const len = Math.abs(seg[1] - seg[0]);
        const mid = 0.5 * (seg[0] + seg[1]);
        lengthSum += len;
        midSum += len * mid;
      }
      const other = lengthSum > 0 ? midSum / lengthSum : 0.5 * (segments[0][0] + segments[0][1]);
      if (axis === 'x') return {x: coord, y: other};
      return {x: other, y: coord};
    }
    function localStressPoint(p, q, point) {
      if (!point) return null;
      if (q.id === 'tau_governing') return point;
      const comp = point.component || q.id;
      if (comp.indexOf('tau_x_') === 0 && finite(point.x)) {
        return representativePointOnPolygonCut(p.vertices, 'x', point.x, point);
      }
      if (comp.indexOf('tau_y_') === 0 && finite(point.y)) {
        return representativePointOnPolygonCut(p.vertices, 'y', point.y, point);
      }
      return point;
    }

    function spreadStressMarkers(markers, bounds) {
      if (!markers || markers.length <= 1) return markers || [];
      const scale = Math.max(bounds.dx, bounds.dy, 1.0e-9);
      const tol = scale * 0.004;
      const radius = scale * 0.007;
      const groups = new Map();
      for (const m of markers) {
        const kx = Math.round(m.x / tol);
        const ky = Math.round(m.y / tol);
        const key = kx + ',' + ky;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(m);
      }
      const out = [];
      for (const group of groups.values()) {
        if (group.length === 1) {
          out.push(group[0]);
          continue;
        }
        const cx = group.reduce((s, m) => s + m.x, 0) / group.length;
        const cy = group.reduce((s, m) => s + m.y, 0) / group.length;
        group.sort((a, b) => (a.idx || 0) - (b.idx || 0));
        for (let i = 0; i < group.length; i++) {
          const angle = -Math.PI / 2 + 2 * Math.PI * i / group.length;
          out.push(Object.assign({}, group[i], {
            x: cx + radius * Math.cos(angle),
            y: cy + radius * Math.sin(angle)
          }));
        }
      }
      return out;
    }
    function buildStressMapTraces(polys, q) {
      const range = valueRange(polys, q);
      const bounds = sectionBounds(polys);
      const limits = quantityColorLimits(range, q);
      const traces = [];
      const crossMarkers = [];

      for (const p of orderedPolygonsForDrawing(polys)) {
        const verts = p.vertices || [];
        if (verts.length < 3) continue;
        const xs = verts.map(v => v.x);
        const ys = verts.map(v => v.y);
        xs.push(verts[0].x);
        ys.push(verts[0].y);
        const value = signedQuantityValue(p, q);
        const fill = colorForValue(value, range, q, p.depth);
        const parent = p.idx_container === null || p.idx_container === undefined ? '' : p.idx_container;
        const hover = [
          '<b>idx</b>: ' + p.idx,
          '<b>polygon_name</b>: ' + esc(p.polygon_name || p.s0_name),
          '<b>container</b>: ' + parent,
          '<b>depth</b>: ' + p.depth,
          '<b>' + esc(q.label) + '</b>: ' + fmt(value)
        ].join('<br>');
        traces.push({
          type:'scatter', mode:'lines', x:xs, y:ys,
          fill:'toself', fillcolor:fill,
          line:{color:'#374151', width:0.55},
          hoverinfo:'text', hoveron:'fills', text:hover,
          showlegend:false
        });

        const rawPoint = p.points ? p.points[q.id] : null;
        let point = localStressPoint(p, q, rawPoint);
        if (!(point && finite(point.x) && finite(point.y)) && finite(value)) {
          const c = polygonCentroid(verts);
          if (finite(c.x) && finite(c.y)) {
            point = {x:c.x, y:c.y, component:q.id, value:value};
          }
        }
        if (point && finite(point.x) && finite(point.y) && finite(value)) {
          crossMarkers.push({
            x:point.x,
            y:point.y,
            text:stressPointHover(p, q, point, value),
            idx:p.idx
          });
        }
      }

      traces.push({
        type:'scatter', mode:'markers',
        x:[bounds.xmax + bounds.dx * 10, bounds.xmax + bounds.dx * 10],
        y:[bounds.ymax + bounds.dy * 10, bounds.ymax + bounds.dy * 10],
        marker:{
          size:0,
          color:[limits.cmin, limits.cmax],
          colorscale:quantityColorScale(q),
          cmin:limits.cmin,
          cmax:limits.cmax,
          showscale:true,
          colorbar:{title:q.label, thickness:14, len:0.76}
        },
        hoverinfo:'skip', showlegend:false
      });

      const shiftedCrossMarkers = spreadStressMarkers(crossMarkers, bounds);
      if (shiftedCrossMarkers.length) {
        traces.push({
          type:'scatter', mode:'markers',
          x:shiftedCrossMarkers.map(m => m.x),
          y:shiftedCrossMarkers.map(m => m.y),
          marker:{symbol:'x', size:CROSS_MARKER_SIZE, color:CROSS_MARKER_COLOR, line:{width:CROSS_MARKER_LINE_WIDTH, color:CROSS_MARKER_COLOR}},
          hoverinfo:'text', text:shiftedCrossMarkers.map(m => m.text),
          name:'extreme point', showlegend:false
        });
      }
      return {traces, bounds, range};
    }
    function renderStressMap(divId, polys, q, z) {
      const built = buildStressMapTraces(polys, q);
      const b = built.bounds;
      const pad = Math.max(b.dx, b.dy) * 0.08;
      Plotly.react(divId, built.traces, {
        title:{text:'z=' + z + ' - ' + q.label, x:0.02, xanchor:'left'},
        margin:{l:30, r:95, t:45, b:30},
        xaxis:{scaleanchor:'y', scaleratio:1, zeroline:false, range:[b.xmin - pad, b.xmax + pad]},
        yaxis:{zeroline:false, range:[b.ymin - pad, b.ymax + pad]},
        hovermode:'closest'
      }, {responsive:true, displaylogo:false});
    }
    function renderStressGallery() {
      const gallery = document.getElementById('stressGallery');
      if (!gallery) return;
      SECTION_DATA.z_values.forEach((z, zi) => {
        const polys = SECTION_DATA.sections[z] || [];
        STRESS_QUANTITIES.forEach(q => renderStressMap(stressDivId(zi, q.id), polys, q, z));
      });
    }
    function renderSection() {
      const z = document.getElementById('zSelect').value;
      const q = quantityById(document.getElementById('quantitySelect').value);
      const polys = SECTION_DATA.sections[z] || [];
      const range = valueRange(polys, q);
      const traces = [];
      const hierarchyLabels = [];
      const crossMarkers = [];
      const bounds = sectionBounds(polys);
      const stressIds = new Set(STRESS_QUANTITIES.map(item => item.id));
      const showStressCrosses = stressIds.has(q.id);
      for (const p of orderedPolygonsForDrawing(polys)) {
        const verts = p.vertices || [];
        if (verts.length < 3) continue;
        const xs = verts.map(v => v.x);
        const ys = verts.map(v => v.y);
        xs.push(verts[0].x);
        ys.push(verts[0].y);
        const value = signedQuantityValue(p, q);
        const fill = colorForValue(value, range, q, p.depth);
        const parent = p.idx_container === null || p.idx_container === undefined ? '' : p.idx_container;
        const hover = [
          '<b>idx</b>: ' + p.idx,
          '<b>polygon_name</b>: ' + esc(p.polygon_name || p.s0_name),
          '<b>s1_name</b>: ' + p.s1_name,
          '<b>container</b>: ' + parent,
          '<b>depth</b>: ' + p.depth,
          '<b>w</b>: ' + fmt(p.w),
          '<b>shear_w</b>: ' + fmt(p.shear_w),
          '<b>poisson</b>: ' + fmt(p.poisson),
          '<b>' + q.label + '</b>: ' + fmt(value)
        ].join('<br>');
        traces.push({
          type:'scatter', mode:'lines', x:xs, y:ys,
          fill:'toself', fillcolor:fill,
          line:{color:'#374151', width:0.6},
          hoverinfo:'text', hoveron:'fills', text:hover,
          showlegend:false
        });
        if (q.id === 'depth') {
          const c = polygonCentroid(verts);
          if (finite(c.x) && finite(c.y)) {
            hierarchyLabels.push({x:c.x, y:c.y, text:(p.s0_name || String(p.idx)), area:polygonAbsArea(verts)});
          }
        }
        if (showStressCrosses) {
          const rawPoint = p.points ? p.points[q.id] : null;
          let point = localStressPoint(p, q, rawPoint);
          if (!(point && finite(point.x) && finite(point.y)) && finite(value)) {
            const c = polygonCentroid(verts);
            if (finite(c.x) && finite(c.y)) {
              point = {x:c.x, y:c.y, component:q.id, value:value};
            }
          }
          if (point && finite(point.x) && finite(point.y) && finite(value)) {
            crossMarkers.push({
              x:point.x,
              y:point.y,
              text:stressPointHover(p, q, point, value),
              idx:p.idx
            });
          }
        }
      }
      if (q.id === 'depth' && hierarchyLabels.length) {
        const shifted = placeHierarchyLabels(swapSteelCoverLabelTexts(hierarchyLabels), bounds);
        traces.push({
          type:'scatter',
          mode:'text',
          x:shifted.map(d => d.x),
          y:shifted.map(d => d.y),
          text:shifted.map(d => d.text),
          textfont:{size:8, color:'#111827'},
          textposition:'middle center',
          hoverinfo:'skip',
          showlegend:false
        });
      }
      traces.push(sectionColorbarTrace(bounds, range, q));
      if (showStressCrosses && crossMarkers.length) {
        const shiftedCrossMarkers = spreadStressMarkers(crossMarkers, bounds);
        traces.push({
          type:'scatter', mode:'markers',
          x:shiftedCrossMarkers.map(m => m.x),
          y:shiftedCrossMarkers.map(m => m.y),
          marker:{symbol:'x', size:CROSS_MARKER_SIZE, color:CROSS_MARKER_COLOR, line:{width:CROSS_MARKER_LINE_WIDTH, color:CROSS_MARKER_COLOR}},
          hoverinfo:'text', text:shiftedCrossMarkers.map(m => m.text),
          name:'extreme point', showlegend:false
        });
      }
      const pad = Math.max(bounds.dx, bounds.dy) * 0.08;
      Plotly.react('sectionPlot', traces, {
        title: {text:'Section map - z=' + z + ' - ' + q.label, x:0.02, xanchor:'left'},
        margin: {l:35, r:95, t:50, b:35},
        xaxis: {scaleanchor:'y', scaleratio:1, zeroline:false, range:[bounds.xmin - pad, bounds.xmax + pad]},
        yaxis: {zeroline:false, range:[bounds.ymin - pad, bounds.ymax + pad]},
        hovermode:'closest'
      }, {responsive:true, displaylogo:false});
      const info = document.getElementById('rangeInfo');
      info.innerHTML = '<b>Quantity:</b> ' + q.label + '<br>' +
        '<b>range:</b> min=' + fmt(range.min) + ', max=' + fmt(range.max) + '<br>' +
        quantityLegendText(range, q) + '<br>' +
        '<b>polygons:</b> ' + polys.length;
      renderPolygonStressTable(polys);
    }
    function renderPolygonStressTable(polys) {
      const body = document.getElementById('polygonStressBody');
      if (!body) return;
      const sorted = [...polys].sort((a,b) => a.idx - b.idx);
      body.innerHTML = sorted.map(p => {
        const v = p.values || {};
        const container = (p.idx_container === null || p.idx_container === undefined) ? '' : p.idx_container;
        return '<tr>' +
          '<td>' + p.idx + '</td>' +
          '<td class="name">' + esc(p.polygon_name || p.s0_name) + '</td>' +
          '<td>' + container + '</td>' +
          '<td>' + p.depth + '</td>' +
          '<td>' + fmt(v.sigma_min) + '</td>' +
          '<td>' + fmt(v.sigma_max) + '</td>' +
          '<td>' + fmt(v.sigma_extreme) + '</td>' +
          '<td>' + fmt(v.tau_x_min) + '</td>' +
          '<td>' + fmt(v.tau_x_max) + '</td>' +
          '<td>' + fmt(v.tau_y_min) + '</td>' +
          '<td>' + fmt(v.tau_y_max) + '</td>' +
          '<td>' + fmt(v.tau_governing) + '</td>' +
          '<td>' + esc(v.tau_governing_direction || '') + '</td>' +
        '</tr>';
      }).join('');
    }
    document.addEventListener('DOMContentLoaded', () => {
      initGlobalPlots();
      initControls();
      initStressGalleryContainers();
      renderSection();
      renderStressGallery();
    });
    """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CSF visual report</title>
<style>{css}</style>
<script>{plotly_js}</script>
</head>
<body>
<header>
  <h1>CSF visual report</h1>
  <div class="note">Standalone HTML generated from CSV outputs.</div>
</header>
<main>
  <h2>Legend</h2>
  <div class="legend-grid">
    <div class="legend-card"><b>Signed quantities</b>Blue = negative, white = zero, red = positive. The scale is symmetric around zero using the local maximum absolute value for the selected station and quantity.</div>
    <div class="legend-card"><b>Positive quantities</b>Viridis scale from local minimum to local maximum. This includes w, shear_w, poisson, and scan counts.</div>
    <div class="legend-card"><b>Markers</b>Black crosses mark the available source point or representative cut point associated with the displayed stress value.</div>
  </div>
  <p class="note"><b>tau_governing</b> is the signed Jourawski shear-stress value having the largest absolute magnitude in each polygon, selected among tau_x_min, tau_x_max, tau_y_min and tau_y_max. The original sign is preserved; direction identifies x or y.</p>
  <div id="legendTableWrap">
    <table>
      <thead>
        <tr><th class="name">quantity</th><th class="name">meaning</th><th class="name">color scale</th></tr>
      </thead>
      <tbody>{''.join(legend_rows_html)}</tbody>
    </table>
  </div>

  <h2>Global diagrams</h2>
  <div class="grid">
    <div class="panel"><div id="plotN" class="plot"></div></div>
    <div class="panel"><div id="plotM" class="plot"></div></div>
    <div class="panel"><div id="plotShear" class="plot"></div></div>
    <div class="panel"><div id="plotTz" class="plot"></div></div>
  </div>

  <h2>Section maps by station</h2>
  <div class="section-layout">
    <div class="controls">
      <label for="zSelect">z station</label>
      <select id="zSelect"></select>
      <label for="quantitySelect">map quantity</label>
      <select id="quantitySelect"></select>
      <div id="rangeInfo"></div>
      <p class="note">One quantity is displayed at a time. Hover a polygon to inspect its data and containment.</p>
    </div>
    <div id="sectionPlot"></div>
  </div>

  <h2>Stress maps by station and quantity</h2>
  <p class="note">A separate set of maps is generated for each z station. Each panel uses its own local color range for the displayed station and quantity. Polygon color is mapped to the reported value; crosses mark the available source point or representative cut point where that value is attained when coordinates are available in the CSV.</p>
  <div id="stressGallery"></div>

  <h2>Polygon stresses at selected station</h2>
  <p class="note">Rows are updated with the selected z station. Each row reports Navier and Jourawski values for one polygon.</p>
  <div id="polygonStressWrap">
    <table>
      <thead>
        <tr>
          <th>polygon_idx</th><th class="name">polygon_name</th><th>container</th><th>depth</th>
          <th>sigma_min</th><th>sigma_max</th><th>sigma_extreme</th>
          <th>tau_x_min</th><th>tau_x_max</th><th>tau_y_min</th><th>tau_y_max</th><th>tau_governing</th><th>direction</th>
        </tr>
      </thead>
      <tbody id="polygonStressBody"></tbody>
    </table>
  </div>

  <h2>Shear extreme rows</h2>
  <p class="note"><b>tau_governing</b> is the signed Jourawski shear-stress value having the largest absolute magnitude in each polygon, selected among tau_x_min, tau_x_max, tau_y_min and tau_y_max. For each z, the tables list the polygons sharing the maximum absolute tau_governing separately for S and NON-S.</p>

  <h3>SHEAR EXTREME ROWS - S</h3>
  <div class="extremeTableWrap">
    <table>
      <thead>
        <tr><th>z</th><th>tau_governing</th><th class="name">direction</th><th>polygon_idx</th><th class="name">polygon_name</th><th>x</th><th>y</th></tr>
      </thead>
      <tbody>{extreme_rows_s_html}</tbody>
    </table>
  </div>

  <h3>SHEAR EXTREME ROWS - NON-S</h3>
  <div class="extremeTableWrap">
    <table>
      <thead>
        <tr><th>z</th><th>tau_governing</th><th class="name">direction</th><th>polygon_idx</th><th class="name">polygon_name</th><th>x</th><th>y</th></tr>
      </thead>
      <tbody>{extreme_rows_non_s_html}</tbody>
    </table>
  </div>
</main>
<script>
{js_data}
{js_runtime}
</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def create_visual_report(input_dir: Path, output_dir: Path) -> Path:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    actions_rows = _read_csv_rows(input_dir / "internal_actions.csv")
    navier_rows = _read_csv_rows(input_dir / "navier_stresses.csv")
    shear_rows = _read_csv_rows(input_dir / "shear_stresses.csv")
    geometry_rows = _read_section_polygons(input_dir / "section_polygons.csv")

    actions = _actions_payload(actions_rows)
    section_data = _assemble_sections(
        geometry_rows=geometry_rows,
        navier_rows=navier_rows,
        shear_rows=shear_rows,
    )
    shear_extremes_s = _shear_extreme_rows(shear_rows, select_s=True)
    shear_extremes_non_s = _shear_extreme_rows(shear_rows, select_s=False)

    html_text = _build_html(
        actions=actions,
        section_data=section_data,
        shear_extremes_s=shear_extremes_s,
        shear_extremes_non_s=shear_extremes_non_s,
    )

    out_path = output_dir / "csf_visual_report.html"
    out_path.write_text(html_text, encoding="utf-8")
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a standalone CSF HTML visual report from CSV outputs."
    )
    parser.add_argument("input_dir", help="Directory containing the generated CSV files.")
    parser.add_argument("output_dir", help="Directory where the HTML report will be written.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_path = create_visual_report(Path(args.input_dir), Path(args.output_dir))
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()

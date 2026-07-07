
"""
Minimal CSF cantilever pole section check.

Workflow
--------
CSF field -> S(z) -> residual prestress resultant -> signed internal actions
-> Navier normal stresses + Jourawski shear-stress envelopes.

This script does not build a beam/FEM model. It evaluates the CSF section field
directly at the requested z stations.

Sign policy
-----------
All input forces are used with the sign supplied in the YAML settings.
The script does not apply abs(), sign corrections, or automatic convention fixes.

Prestress force:
    Pp = prestress.force_healthy * residual_area_ratio

Prestress eccentricity:
    ex = xp - Cx
    ey = yp - Cy

Prestress moments:
    Mx_prestress = Pp * ey
    My_prestress = Pp * ex

External tip-force convention:
    Mx_ext(z) = -tip_force_y * (L - z)
    My_ext(z) = 0
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyYAML is required to read the settings file.") from exc


# --------------------------------------------------------------
# Data containers
# --------------------------------------------------------------


@dataclass(frozen=True)
class AnalysisSettings:
    """Runtime settings read from YAML."""

    csf_yaml: Path
    debug_enabled: bool

    prestress_bar_type: str
    prestress_force_healthy: float

    z_stations: list[float]
    num_sudx: int
    num_sudy: int

    gradient_dz: float
    gradient_scheme: str

    tip_force_y: float
    tip_torque_z: float

    output_directory: Path
    prestress_resultant_file: str
    internal_actions_file: str
    navier_stresses_file: str
    shear_stresses_file: str
    polygon_vertices_file: str
    mechanical_report_file: str


@dataclass(frozen=True)
class PrestressBarResult:
    """Effective residual prestress-bar resultant at one station."""

    z: float
    x_resultant: float
    y_resultant: float
    area_effective: float
    area_reference: float
    ratio: float


@dataclass(frozen=True)
class PrestressState:
    """Signed prestress force and eccentricity relative to the CSF section centroid."""

    z: float
    Pp: float
    xp: float
    yp: float
    Cx: float
    Cy: float
    ex: float
    ey: float
    ratio: float
    area_effective: float
    area_reference: float


@dataclass(frozen=True)
class MomentState:
    """Signed axial force and bending/torsional moments at one station."""

    z: float
    N: float
    Mx_ext: float
    My_ext: float
    Mx_prestress: float
    My_prestress: float
    Mx: float
    My: float
    Tz: float
    Pp: float
    ex: float
    ey: float


@dataclass(frozen=True)
class GradientWindow:
    """Central-difference window actually used for moment-gradient evaluation."""

    z_station: float
    z_gradient: float
    z_minus: float
    z_plus: float


@dataclass(frozen=True)
class InternalActions:
    """Actions passed to the stress APIs at one station."""

    z: float
    N: float
    Mx: float
    My: float
    Tx_jourawski: float
    Ty_jourawski: float
    Tz: float

    Mx_ext: float
    My_ext: float
    Mx_prestress: float
    My_prestress: float
    dMx_dz: float
    dMy_dz: float

    Pp: float
    ex: float
    ey: float
    gradient_window: GradientWindow


# --------------------------------------------------------------
# Settings
# --------------------------------------------------------------


def read_settings(settings_file: Path) -> AnalysisSettings:
    """Read the YAML settings file and return a typed settings object."""

    with open(settings_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("The settings file must contain a YAML mapping.")

    model = _required_mapping(data, "model")
    prestress = _required_mapping(data, "prestress")
    moment_gradient = _required_mapping(data, "moment_gradient")
    loads = _required_mapping(data, "loads")
    outputs = _required_mapping(data, "outputs")

    debug = data.get("debug", {})
    if debug is None:
        debug = {}
    if not isinstance(debug, dict):
        raise ValueError("debug must be a YAML mapping when provided.")

    csf_yaml = Path(_required(model, "csf_yaml"))
    if not csf_yaml.is_absolute():
        csf_yaml = settings_file.parent / csf_yaml

    z_stations_raw = _required(data, "z_stations")
    if not isinstance(z_stations_raw, list):
        raise ValueError("z_stations must be a YAML list.")
    z_stations = [float(z) for z in z_stations_raw]

    output_directory = Path(_required(outputs, "directory"))
    if not output_directory.is_absolute():
        output_directory = settings_file.parent / output_directory

    num_sudx, num_sudy = _read_shear_num_subdivisions(data)

    return AnalysisSettings(
        csf_yaml=csf_yaml,
        debug_enabled=bool(debug.get("enabled", False)),

        prestress_bar_type=str(_required(prestress, "bar_type")),
        prestress_force_healthy=float(_required(prestress, "force_healthy")),

        z_stations=z_stations,
        num_sudx=num_sudx,
        num_sudy=num_sudy,

        gradient_dz=float(_required(moment_gradient, "dz")),
        gradient_scheme=str(_required(moment_gradient, "scheme")),

        tip_force_y=float(_required(loads, "tip_force_y")),
        tip_torque_z=float(_required(loads, "tip_torque_z")),

        output_directory=output_directory,
        prestress_resultant_file=str(_required(outputs, "prestress_resultant")),
        internal_actions_file=str(_required(outputs, "internal_actions")),
        navier_stresses_file=str(_required(outputs, "navier_stresses")),
        shear_stresses_file=str(_required(outputs, "shear_stresses")),
        polygon_vertices_file=str(outputs.get("polygon_vertices", outputs.get("section_polygons", "section_polygons.csv"))),
        mechanical_report_file=str(_required(outputs, "mechanical_report")),
    )


def _read_shear_num_subdivisions(data: dict[str, Any]) -> tuple[int, int]:
    """Read global Jourawski scan subdivisions from the shear settings block."""

    shear = _required_mapping(data, "shear")
    num_sudx = int(_required(shear, "num_sudx"))
    num_sudy = int(_required(shear, "num_sudy"))

    if num_sudx < 1:
        raise ValueError("shear.num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("shear.num_sudy must be >= 1.")

    return num_sudx, num_sudy


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    """Return a required YAML mapping."""

    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid settings block: {key}")
    return value


def _required(data: dict[str, Any], key: str) -> Any:
    """Return a required YAML value."""

    if key not in data:
        raise ValueError(f"Missing required setting: {key}")
    value = data[key]
    if value is None:
        raise ValueError(f"Setting must not be null: {key}")
    return value


# --------------------------------------------------------------
# CSF loading and bounds
# --------------------------------------------------------------


def build_section_field(csf_yaml: Path):
    """Load the CSF field through CSFReader."""

    try:
        from csf.io.csf_issues import CSFIssues
        from csf.io.csf_reader import CSFReader
    except Exception as exc:
        raise RuntimeError(
            "CSF is not importable. Install the repository with `python -m pip install -e .`."
        ) from exc

    result = CSFReader().read_file(str(csf_yaml))
    if not result.ok:
        print(CSFIssues.format_report(result.issues))
        raise SystemExit(1)

    return result.field


def field_bounds(section_field) -> tuple[float, float, float]:
    """Return z0, z1, and L from a CSF field."""

    z0 = float(getattr(section_field, "z0", getattr(section_field.s0, "z")))
    z1 = float(getattr(section_field, "z1", getattr(section_field.s1, "z")))
    L = float(getattr(section_field, "L", z1 - z0))
    return z0, z1, L


# --------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------


def strip_csf_name(name: Any) -> str:
    """Remove CSF topology suffixes from polygon names."""

    return str(name or "").split("@", 1)[0].strip()


def is_prestressing_bar_name(name: Any, bar_type: str) -> bool:
    """
    Identify prestressing-bar polygons.

    Expected polygon-id convention:
        <sector>_<level>_<bar_type>
    """

    base = strip_csf_name(name)
    parts = base.split("_")
    return (
        len(parts) == 3
        and parts[0].isdigit()
        and parts[1].isdigit()
        and parts[2] == str(bar_type)
    )


def polygon_area_centroid(poly) -> tuple[float, float, float]:
    """Compute signed polygon area and centroid from evaluated polygon vertices."""

    verts = tuple(poly.vertices)
    if len(verts) < 3:
        raise ValueError(f"Polygon has fewer than 3 vertices: {getattr(poly, 'name', '')}")

    a2 = 0.0
    cx_num = 0.0
    cy_num = 0.0

    for i in range(len(verts)):
        p0 = verts[i]
        p1 = verts[(i + 1) % len(verts)]

        x0 = float(p0.x)
        y0 = float(p0.y)
        x1 = float(p1.x)
        y1 = float(p1.y)

        cross = x0 * y1 - x1 * y0
        a2 += cross
        cx_num += (x0 + x1) * cross
        cy_num += (y0 + y1) * cross

    if a2 == 0.0:
        raise ValueError(f"Zero-area polygon: {getattr(poly, 'name', '')}")

    area = 0.5 * a2
    cx = cx_num / (3.0 * a2)
    cy = cy_num / (3.0 * a2)

    return area, cx, cy


def polygon_reference_weight(poly) -> float:
    """Return the endpoint reference weight of a polygon."""

    weight = getattr(poly, "weight", None)
    if weight is None:
        raise ValueError(f"Polygon has no reference weight: {getattr(poly, 'name', '')}")
    return float(weight)


def reference_weight_at_z(section_field, polygon_idx: int, z: float) -> float:
    """Interpolate the endpoint reference weight at station z."""

    z0, z1, _ = field_bounds(section_field)
    t = (float(z) - z0) / (z1 - z0)

    p0 = section_field.s0.polygons[int(polygon_idx)]
    p1 = section_field.s1.polygons[int(polygon_idx)]

    w0 = polygon_reference_weight(p0)
    w1 = polygon_reference_weight(p1)

    return (1.0 - t) * w0 + t * w1


def area_record_w_abs(record: dict[str, Any]) -> float:
    """Return absolute polygon weight from a CSF area/weight record."""

    if "w_abs" in record and record["w_abs"] not in ("", None):
        return float(record["w_abs"])

    area_geom = float(record["area_geom"])
    area = float(record["area"])
    if area_geom == 0.0:
        raise ValueError("Cannot recover w_abs from area/area_geom because area_geom is zero.")

    return area / area_geom


# --------------------------------------------------------------
# Prestress resultant
# --------------------------------------------------------------


def prestress_bar_resultant_at_z(
    section_field,
    z: float,
    bar_type: str,
    debug_rows: list[dict[str, Any]] | None = None,
) -> PrestressBarResult:
    """
    Compute the residual prestress resultant at station z.

    Only polygons whose original S0 name matches <sector>_<level>_<bar_type>
    are included.
    """

    z = float(z)
    section = section_field.section(z)
    report = section_field.section_area_by_weight(z=z, include_per_polygon=True)

    area_effective = 0.0
    area_reference = 0.0
    x_num = 0.0
    y_num = 0.0

    local_debug_rows: list[dict[str, Any]] = []

    for record in report.get("per_polygon", []):
        idx = int(record["idx"])

        name_s0 = getattr(section_field.s0.polygons[idx], "name", "")
        name_eval = getattr(section.polygons[idx], "name", "")

        if not is_prestressing_bar_name(name_s0, bar_type):
            continue

        poly = section.polygons[idx]
        _, x_bar, y_bar = polygon_area_centroid(poly)

        area_geom = abs(float(record["area_geom"]))
        w_abs = area_record_w_abs(record)
        w_ref_abs = reference_weight_at_z(section_field, idx, z)

        if w_ref_abs == 0.0:
            raise ValueError(
                f"Zero reference weight for prestress bar {name_s0!r} at z={z}."
            )

        q_eff = w_abs / w_ref_abs
        area_eff = area_geom * q_eff

        area_effective += area_eff
        area_reference += area_geom
        x_num += x_bar * area_eff
        y_num += y_bar * area_eff

        local_debug_rows.append(
            {
                "z": z,
                "idx": idx,
                "name_s0": name_s0,
                "name_eval": name_eval,
                "area_geom": area_geom,
                "w_abs": w_abs,
                "w_ref_abs": w_ref_abs,
                "q_eff": q_eff,
                "area_eff": area_eff,
                "x_bar": x_bar,
                "y_bar": y_bar,
                "x_num": x_bar * area_eff,
                "y_num": y_bar * area_eff,
            }
        )

    if area_reference == 0.0:
        raise ValueError(
            f"No prestressing bars found at z={z}. "
            f"Expected polygon IDs like <sector>_<level>_{bar_type}."
        )

    if area_effective == 0.0:
        raise ValueError(f"Residual prestressing bar effective area is zero at z={z}.")

    ratio = area_effective / area_reference
    x_resultant = x_num / area_effective
    y_resultant = y_num / area_effective

    if debug_rows is not None:
        debug_rows.extend(local_debug_rows)
        debug_rows.append(
            {
                "z": z,
                "idx": "",
                "name_s0": "prestress_resultant",
                "name_eval": "",
                "area_geom": "",
                "w_abs": "",
                "w_ref_abs": "",
                "q_eff": "",
                "area_eff": area_effective,
                "x_bar": "",
                "y_bar": "",
                "x_num": x_num,
                "y_num": y_num,
                "area_reference": area_reference,
                "ratio": ratio,
                "x_resultant": x_resultant,
                "y_resultant": y_resultant,
            }
        )

    return PrestressBarResult(
        z=z,
        x_resultant=x_resultant,
        y_resultant=y_resultant,
        area_effective=area_effective,
        area_reference=area_reference,
        ratio=ratio,
    )


def section_centroid_at_z(section_field, z: float) -> tuple[float, float]:
    """Return the CSF section centroid at station z."""

    from csf import section_full_analysis

    section = section_field.section(float(z))
    analysis = section_full_analysis(section)
    return float(analysis["Cx"]), float(analysis["Cy"])


def prestress_state_at_z(
    section_field,
    settings: AnalysisSettings,
    z: float,
    debug_rows: list[dict[str, Any]] | None = None,
) -> PrestressState:
    """Return signed prestress force and eccentricity at station z."""

    bar_result = prestress_bar_resultant_at_z(
        section_field=section_field,
        z=float(z),
        bar_type=settings.prestress_bar_type,
        debug_rows=debug_rows,
    )

    Cx, Cy = section_centroid_at_z(section_field, float(z))

    xp = bar_result.x_resultant
    yp = bar_result.y_resultant

    ex = xp - Cx
    ey = yp - Cy

    # Signed input policy: use the YAML prestress force exactly as supplied.
    Pp = float(settings.prestress_force_healthy) * float(bar_result.ratio)

    return PrestressState(
        z=float(z),
        Pp=Pp,
        xp=xp,
        yp=yp,
        Cx=Cx,
        Cy=Cy,
        ex=ex,
        ey=ey,
        ratio=bar_result.ratio,
        area_effective=bar_result.area_effective,
        area_reference=bar_result.area_reference,
    )


# --------------------------------------------------------------
# Internal actions and gradients
# --------------------------------------------------------------


def moment_state_at_z(
    section_field,
    settings: AnalysisSettings,
    z: float,
) -> MomentState:
    """
    Compute signed axial force and moments at station z.

    No sign correction is applied. The YAML force signs and explicit differences
    ex = xp - Cx and ey = yp - Cy define the result.
    """

    _, _, L = field_bounds(section_field)
    prestress = prestress_state_at_z(
        section_field=section_field,
        settings=settings,
        z=float(z),
        debug_rows=None,
    )

    arm = L - float(z)

    # Cantilever sign convention for a signed tip_force_y.
    Mx_ext = -float(settings.tip_force_y) * arm
    My_ext = 0.0

    # Prestress eccentricity contribution. Pp is already signed.
    Mx_prestress = prestress.Pp * prestress.ey
    My_prestress = prestress.Pp * prestress.ex

    Mx = Mx_ext + Mx_prestress
    My = My_ext + My_prestress

    return MomentState(
        z=float(z),
        N=prestress.Pp,

        Mx_ext=Mx_ext,
        My_ext=My_ext,
        Mx_prestress=Mx_prestress,
        My_prestress=My_prestress,

        Mx=Mx,
        My=My,
        Tz=float(settings.tip_torque_z),

        Pp=prestress.Pp,
        ex=prestress.ex,
        ey=prestress.ey,
    )


def gradient_window(
    section_field,
    settings: AnalysisSettings,
    z_station: float,
) -> GradientWindow:
    """
    Return the central-difference window for moment gradients.

    If the station is too close to an end, the derivative point is shifted inside
    the domain so that z_minus and z_plus remain inside the CSF field.
    """

    z0, z1, _ = field_bounds(section_field)
    dz = float(settings.gradient_dz)

    if settings.gradient_scheme != "central_shift_inside_domain":
        raise ValueError(
            "Only moment_gradient.scheme: central_shift_inside_domain is supported."
        )

    if dz <= 0.0:
        raise ValueError("moment_gradient.dz must be positive.")

    if z0 + dz > z1 - dz:
        raise ValueError("moment_gradient.dz is too large for the CSF field length.")

    z_gradient = float(z_station)

    if z_gradient - dz < z0:
        z_gradient = z0 + dz
    elif z_gradient + dz > z1:
        z_gradient = z1 - dz

    return GradientWindow(
        z_station=float(z_station),
        z_gradient=float(z_gradient),
        z_minus=float(z_gradient - dz),
        z_plus=float(z_gradient + dz),
    )


def internal_actions_at_z(
    section_field,
    settings: AnalysisSettings,
    z: float,
    gradient_debug_rows: list[dict[str, Any]] | None = None,
) -> InternalActions:
    """
    Compute signed actions passed to Navier and Jourawski.

    Jourawski API convention:
        Tx = shear component associated with My
        Ty = shear component associated with Mx

    Therefore:
        Tx_jourawski = dMy/dz
        Ty_jourawski = dMx/dz
    """

    state = moment_state_at_z(
        section_field=section_field,
        settings=settings,
        z=float(z),
    )

    window = gradient_window(
        section_field=section_field,
        settings=settings,
        z_station=float(z),
    )

    state_minus = moment_state_at_z(
        section_field=section_field,
        settings=settings,
        z=window.z_minus,
    )
    state_plus = moment_state_at_z(
        section_field=section_field,
        settings=settings,
        z=window.z_plus,
    )

    dz = float(settings.gradient_dz)

    dMx_dz = (state_plus.Mx - state_minus.Mx) / (2.0 * dz)
    dMy_dz = (state_plus.My - state_minus.My) / (2.0 * dz)

    Tx_jourawski = dMy_dz
    Ty_jourawski = dMx_dz

    if gradient_debug_rows is not None:
        gradient_debug_rows.append(
            {
                "z_station": window.z_station,
                "z_gradient": window.z_gradient,
                "z_minus": window.z_minus,
                "z_plus": window.z_plus,
                "Mx_minus": state_minus.Mx,
                "Mx_plus": state_plus.Mx,
                "My_minus": state_minus.My,
                "My_plus": state_plus.My,
                "dMx_dz": dMx_dz,
                "dMy_dz": dMy_dz,
                "Tx_jourawski": Tx_jourawski,
                "Ty_jourawski": Ty_jourawski,
            }
        )

    return InternalActions(
        z=float(z),
        N=state.N,
        Mx=state.Mx,
        My=state.My,
        Tx_jourawski=Tx_jourawski,
        Ty_jourawski=Ty_jourawski,
        Tz=state.Tz,

        Mx_ext=state.Mx_ext,
        My_ext=state.My_ext,
        Mx_prestress=state.Mx_prestress,
        My_prestress=state.My_prestress,
        dMx_dz=dMx_dz,
        dMy_dz=dMy_dz,

        Pp=state.Pp,
        ex=state.ex,
        ey=state.ey,
        gradient_window=window,
    )


# --------------------------------------------------------------
# Stress API calls
# --------------------------------------------------------------


def navier_rows_at_z(
    section_field,
    z: float,
    actions: InternalActions,
) -> list[dict[str, Any]]:
    """Run CSF Navier stress analysis and return minimal output rows."""

    from csf.section_field import analyse_polygon_navier_stress

    raw_rows = analyse_polygon_navier_stress(
        section_field=section_field,
        z=float(z),
        N=float(actions.N),
        Mx=float(actions.Mx),
        My=float(actions.My),
    )

    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        rows.append(
            {
                "z": float(z),
                "polygon_idx": int(row["idx"]),
                "polygon_name": str(row["name"]),
                "sigma_min": float(row["sigma_min"]),
                "vertex_index_min": int(row.get("vertex_index_min", -1)),
                "x_min": float(row.get("x_min", float("nan"))),
                "y_min": float(row.get("y_min", float("nan"))),

                "sigma_max": float(row["sigma_max"]),
                "vertex_index_max": int(row.get("vertex_index_max", -1)),
                "x_max": float(row.get("x_max", float("nan"))),
                "y_max": float(row.get("y_max", float("nan"))),

                "sigma_extreme": float(row["sigma_extreme"]),
                "vertex_index_extreme": int(row.get("vertex_index", -1)),
                "x_extreme": float(row.get("x", float("nan"))),
                "y_extreme": float(row.get("y", float("nan"))),
            }
        )

    return rows


def shear_rows_at_z(
    section_field,
    settings: AnalysisSettings,
    z: float,
    actions: InternalActions,
) -> list[dict[str, Any]]:
    """Run CSF Jourawski shear analysis and return minimal output rows."""

    from csf.section_field import analyse_polygon_jourawski_shear_stress

    raw_rows = analyse_polygon_jourawski_shear_stress(
        section_field=section_field,
        z=float(z),
        Tx=float(actions.Tx_jourawski),
        Ty=float(actions.Ty_jourawski),
        num_sudx=int(settings.num_sudx),
        num_sudy=int(settings.num_sudy),
        debug=bool(settings.debug_enabled),
    )

    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        rows.append(
            {
                "z": float(z),
                "polygon_idx": int(row["idx"]),
                "polygon_name": str(row["name"]),

                "weight": float(row.get("weight", float("nan"))),
                "weight_ref": float(row.get("weight_ref", float("nan"))),
                "weight_norm": float(row.get("weight_norm", float("nan"))),

                "tau_x_min": float(row["tau_x_min"]),
                "tau_x_max": float(row["tau_x_max"]),
                "tau_y_min": float(row["tau_y_min"]),
                "tau_y_max": float(row["tau_y_max"]),

                "x_tau_x_min": float(row.get("x_tau_x_min", float("nan"))),
                "y_tau_x_min": float(row.get("y_tau_x_min", float("nan"))),
                "x_tau_x_max": float(row.get("x_tau_x_max", float("nan"))),
                "y_tau_x_max": float(row.get("y_tau_x_max", float("nan"))),

                "x_tau_y_min": float(row.get("x_tau_y_min", float("nan"))),
                "y_tau_y_min": float(row.get("y_tau_y_min", float("nan"))),
                "x_tau_y_max": float(row.get("x_tau_y_max", float("nan"))),
                "y_tau_y_max": float(row.get("y_tau_y_max", float("nan"))),

                "coord_tau_y_max": float(row.get("coord_tau_y_max", float("nan"))),
                "tau_reference_y_max": float(row.get("tau_reference_y_max", float("nan"))),
                "b_weighted_y_max": float(row.get("b_weighted_y_max", float("nan"))),
                "Sx_part_y_max": float(row.get("Sx_part_y_max", float("nan"))),
                "Sy_part_y_max": float(row.get("Sy_part_y_max", float("nan"))),

                "tau_x_mean": float(row.get("tau_x_mean", float("nan"))),
                "tau_y_mean": float(row.get("tau_y_mean", float("nan"))),
                "scan_count_x": int(row.get("scan_count_x", 0)),
                "scan_count_y": int(row.get("scan_count_y", 0)),
                "grid_x": int(row.get("grid_x", 0)),
                "grid_y": int(row.get("grid_y", 0)),
                "converged_x": bool(row.get("converged_x", False)),
                "converged_y": bool(row.get("converged_y", False)),
            }
        )

    return rows


# --------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------


def format_float(value: Any) -> str:
    """Format floats consistently for CSV and text output."""

    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.12e}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    """Write a CSV file with stable column order."""

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({key: format_float(row.get(key, "")) for key in fieldnames})

    return path


def write_prestress_resultant_csv(
    output_path: Path,
    prestress_rows: list[dict[str, Any]],
) -> Path:
    """Write the minimal prestress resultant CSV."""

    return write_csv(
        path=output_path,
        rows=prestress_rows,
        fieldnames=["z", "Pp", "ex", "ey"],
    )


def write_internal_actions_csv(
    output_path: Path,
    action_rows: list[dict[str, Any]],
) -> Path:
    """Write the signed internal actions passed to the stress APIs."""

    return write_csv(
        path=output_path,
        rows=action_rows,
        fieldnames=["z", "N", "Mx", "My", "Tx_jourawski", "Ty_jourawski", "Tz"],
    )


def write_navier_stresses_csv(
    output_path: Path,
    navier_rows: list[dict[str, Any]],
) -> Path:
    """Write polygon-wise Navier stress envelopes."""

    return write_csv(
        path=output_path,
        rows=navier_rows,
        fieldnames=[
            "z",
            "polygon_idx",
            "polygon_name",
            "sigma_min",
            "vertex_index_min",
            "x_min",
            "y_min",
            "sigma_max",
            "vertex_index_max",
            "x_max",
            "y_max",
            "sigma_extreme",
            "vertex_index_extreme",
            "x_extreme",
            "y_extreme",
        ],
    )


def write_shear_stresses_csv(
    output_path: Path,
    shear_rows: list[dict[str, Any]],
) -> Path:
    """Write polygon-wise Jourawski shear-stress envelopes."""

    return write_csv(
        path=output_path,
        rows=shear_rows,
        fieldnames=[
            "z",
            "polygon_idx",
            "polygon_name",

            "weight",
            "weight_ref",
            "weight_norm",

            "tau_x_min",
            "tau_x_max",
            "tau_y_min",
            "tau_y_max",

            "x_tau_x_min",
            "y_tau_x_min",
            "x_tau_x_max",
            "y_tau_x_max",
            "x_tau_y_min",
            "y_tau_y_min",
            "x_tau_y_max",
            "y_tau_y_max",

            "coord_tau_y_max",
            "tau_reference_y_max",
            "b_weighted_y_max",
            "Sx_part_y_max",
            "Sy_part_y_max",

            "tau_x_mean",
            "tau_y_mean",

            "scan_count_x",
            "scan_count_y",
            "grid_x",
            "grid_y",
            "converged_x",
            "converged_y",
        ],
    )



def write_polygon_vertices_csv(
    *,
    section_field,
    output_path: Path,
    z_values: list[float],
) -> Path:
    """Write the CSF standard polygon-vertices export for the requested stations."""

    from csf.section_field import export_polygon_vertices_csv_file

    export_polygon_vertices_csv_file(
        field=section_field,
        z_values=[float(z) for z in z_values],
        exp_filename=str(output_path),
        fmt="{:.16g}",
    )
    return output_path

def _finite_shear_candidates(
    shear_rows: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Return finite shear candidates with value, component, polygon identity, and location."""

    candidates: list[dict[str, Any]] = []

    for row in shear_rows:
        for key in keys:
            value = float(row[key])
            if not math.isfinite(value):
                continue

            x_key = f"x_{key}"
            y_key = f"y_{key}"

            candidates.append(
                {
                    "z": float(row["z"]),
                    "tau": value,
                    "component": key,
                    "polygon_idx": int(row["polygon_idx"]),
                    "polygon_name": str(row["polygon_name"]),
                    "x": float(row.get(x_key, float("nan"))),
                    "y": float(row.get(y_key, float("nan"))),
                }
            )

    return candidates


def shear_extreme_rows_at_station(
    shear_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return all polygon rows sharing the maximum absolute shear at one station."""

    candidates = _finite_shear_candidates(
        shear_rows=shear_rows,
        keys=("tau_x_min", "tau_x_max", "tau_y_min", "tau_y_max"),
    )
    if not candidates:
        return []

    max_abs_tau = max(abs(float(candidate["tau"])) for candidate in candidates)
    tolerance = max(max_abs_tau, 1.0) * 1.0e-12

    return [
        candidate
        for candidate in candidates
        if abs(abs(float(candidate["tau"])) - max_abs_tau) <= tolerance
    ]

def station_summary_row(
    z: float,
    actions: InternalActions,
    navier_rows: list[dict[str, Any]],
    shear_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate polygon-wise stress rows into one readable station summary row."""

    sigma_min = min(float(row["sigma_min"]) for row in navier_rows)
    sigma_max = max(float(row["sigma_max"]) for row in navier_rows)
    sigma_extreme = max(
        (float(row["sigma_extreme"]) for row in navier_rows),
        key=lambda value: abs(value),
    )

    if shear_rows:
        tau_x_min = min(float(row["tau_x_min"]) for row in shear_rows)
        tau_x_max = max(float(row["tau_x_max"]) for row in shear_rows)
        tau_y_min = min(float(row["tau_y_min"]) for row in shear_rows)
        tau_y_max = max(float(row["tau_y_max"]) for row in shear_rows)
    else:
        tau_x_min = float("nan")
        tau_x_max = float("nan")
        tau_y_min = float("nan")
        tau_y_max = float("nan")

    return {
        "z": float(z),
        "N": actions.N,
        "Mx": actions.Mx,
        "My": actions.My,
        "Tx": actions.Tx_jourawski,
        "Ty": actions.Ty_jourawski,
        "Tz": actions.Tz,
        "sigma_min": sigma_min,
        "sigma_max": sigma_max,
        "sigma_extreme": sigma_extreme,
        "tau_x_min": tau_x_min,
        "tau_x_max": tau_x_max,
        "tau_y_min": tau_y_min,
        "tau_y_max": tau_y_max,
    }


def write_mechanical_report(
    output_path: Path,
    settings: AnalysisSettings,
    station_summary_rows: list[dict[str, Any]],
    shear_extreme_rows: list[dict[str, Any]],
) -> Path:
    """Write a compact human-readable TXT report."""

    lines: list[str] = []

    lines.append("CSF CANTILEVER POLE - MECHANICAL REPORT")
    lines.append("=======================================")
    lines.append("")

    lines.append("MODEL")
    lines.append("-----")
    lines.append(f"CSF YAML              : {settings.csf_yaml}")
    lines.append(f"prestress bar type    : {settings.prestress_bar_type}")
    lines.append(f"z stations            : {len(settings.z_stations)}")
    lines.append("")

    lines.append("LOADS")
    lines.append("-----")
    lines.append(f"prestress.force_healthy : {settings.prestress_force_healthy:.12e}")
    lines.append(f"tip_force_y              : {settings.tip_force_y:.12e}")
    lines.append(f"tip_torque_z             : {settings.tip_torque_z:.12e}")
    lines.append("")

    lines.append("SHEAR / MOMENT GRADIENT")
    lines.append("-----------------------")
    lines.append(f"num_sudx             : {settings.num_sudx}")
    lines.append(f"num_sudy             : {settings.num_sudy}")
    lines.append(f"gradient scheme      : {settings.gradient_scheme}")
    lines.append(f"gradient dz          : {settings.gradient_dz:.12e}")
    lines.append("")

    if station_summary_rows:
        sigma_extreme_values = [row["sigma_extreme"] for row in station_summary_rows]

        lines.append("GLOBAL EXTREMES")
        lines.append("---------------")
        lines.append(
            f"min sigma      : {min(row['sigma_min'] for row in station_summary_rows): .12e}"
        )
        lines.append(
            f"max sigma      : {max(row['sigma_max'] for row in station_summary_rows): .12e}"
        )
        lines.append(
            f"max |sigma_ext|: {max(sigma_extreme_values, key=lambda v: abs(v)): .12e}"
        )
        lines.append(
            f"min tau_x      : {min(row['tau_x_min'] for row in station_summary_rows): .12e}"
        )
        lines.append(
            f"max tau_x      : {max(row['tau_x_max'] for row in station_summary_rows): .12e}"
        )
        lines.append(
            f"min tau_y      : {min(row['tau_y_min'] for row in station_summary_rows): .12e}"
        )
        lines.append(
            f"max tau_y      : {max(row['tau_y_max'] for row in station_summary_rows): .12e}"
        )
        lines.append("")

    lines.append("STATION SUMMARY")
    lines.append("---------------")

    headers = [
        "z",
        "N",
        "Mx",
        "My",
        "Tx",
        "Ty",
        "Tz",
        "sig_min",
        "sig_max",
        "sig_ext",
        "tx_min",
        "tx_max",
        "ty_min",
        "ty_max",
    ]

    widths = [11, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14]
    lines.append(" ".join(label.rjust(width) for label, width in zip(headers, widths)))
    lines.append(" ".join("-" * width for width in widths))

    for row in station_summary_rows:
        values = [
            row["z"],
            row["N"],
            row["Mx"],
            row["My"],
            row["Tx"],
            row["Ty"],
            row["Tz"],
            row["sigma_min"],
            row["sigma_max"],
            row["sigma_extreme"],
            row["tau_x_min"],
            row["tau_x_max"],
            row["tau_y_min"],
            row["tau_y_max"],
        ]

        lines.append(
            " ".join(
                f"{float(value):{width}.5e}"
                for value, width in zip(values, widths)
            )
        )

    lines.append("")
    lines.append("SHEAR EXTREME ROWS")
    lines.append("------------------")

    shear_headers = [
        "z",
        "tau",
        "component",
        "polygon_idx",
        "polygon_name",
        "x",
        "y",
    ]
    shear_widths = [11, 14, 12, 12, 18, 14, 14]
    lines.append(
        " ".join(
            label.rjust(width)
            for label, width in zip(shear_headers, shear_widths)
        )
    )
    lines.append(" ".join("-" * width for width in shear_widths))

    for row in shear_extreme_rows:
        lines.append(
            f"{float(row['z']):{shear_widths[0]}.5e} "
            f"{float(row['tau']):{shear_widths[1]}.5e} "
            f"{str(row['component']):>{shear_widths[2]}} "
            f"{int(row['polygon_idx']):>{shear_widths[3]}} "
            f"{str(row['polygon_name']):>{shear_widths[4]}} "
            f"{float(row['x']):{shear_widths[5]}.5e} "
            f"{float(row['y']):{shear_widths[6]}.5e}"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    return output_path


def write_debug_outputs(
    settings: AnalysisSettings,
    prestress_debug_rows: list[dict[str, Any]],
    gradient_debug_rows: list[dict[str, Any]],
    section_debug_rows: list[dict[str, Any]],
) -> list[Path]:
    """Write debug files when debug.enabled is true."""

    if not settings.debug_enabled:
        return []

    out: list[Path] = []

    out.append(
        write_csv(
            path=settings.output_directory / "debug_prestress_bars.csv",
            rows=prestress_debug_rows,
            fieldnames=[
                "z",
                "idx",
                "name_s0",
                "name_eval",
                "area_geom",
                "w_abs",
                "w_ref_abs",
                "q_eff",
                "area_eff",
                "x_bar",
                "y_bar",
                "x_num",
                "y_num",
                "area_reference",
                "ratio",
                "x_resultant",
                "y_resultant",
            ],
        )
    )

    out.append(
        write_csv(
            path=settings.output_directory / "debug_moment_gradient.csv",
            rows=gradient_debug_rows,
            fieldnames=[
                "z_station",
                "z_gradient",
                "z_minus",
                "z_plus",
                "Mx_minus",
                "Mx_plus",
                "My_minus",
                "My_plus",
                "dMx_dz",
                "dMy_dz",
                "Tx_jourawski",
                "Ty_jourawski",
            ],
        )
    )

    out.append(
        write_csv(
            path=settings.output_directory / "debug_section_quantities.csv",
            rows=section_debug_rows,
            fieldnames=[
                "z",
                "Pp",
                "ratio",
                "area_effective",
                "area_reference",
                "xp",
                "yp",
                "Cx",
                "Cy",
                "ex",
                "ey",
                "Mx_ext",
                "My_ext",
                "Mx_prestress",
                "My_prestress",
                "dMx_dz",
                "dMy_dz",
            ],
        )
    )

    return out


# --------------------------------------------------------------
# Workflow
# --------------------------------------------------------------


def run(settings: AnalysisSettings) -> list[Path]:
    """Run the full section-check workflow."""

    settings.output_directory.mkdir(parents=True, exist_ok=True)

    section_field = build_section_field(settings.csf_yaml)

    prestress_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    navier_rows_all: list[dict[str, Any]] = []
    shear_rows_all: list[dict[str, Any]] = []
    station_summary_rows: list[dict[str, Any]] = []
    shear_extreme_rows_all: list[dict[str, Any]] = []

    prestress_debug_rows: list[dict[str, Any]] = []
    gradient_debug_rows: list[dict[str, Any]] = []
    section_debug_rows: list[dict[str, Any]] = []

    for z in settings.z_stations:
        prestress_debug_target = prestress_debug_rows if settings.debug_enabled else None

        prestress = prestress_state_at_z(
            section_field=section_field,
            settings=settings,
            z=float(z),
            debug_rows=prestress_debug_target,
        )

        actions = internal_actions_at_z(
            section_field=section_field,
            settings=settings,
            z=float(z),
            gradient_debug_rows=gradient_debug_rows if settings.debug_enabled else None,
        )

        navier_rows = navier_rows_at_z(
            section_field=section_field,
            z=float(z),
            actions=actions,
        )

        shear_rows = shear_rows_at_z(
            section_field=section_field,
            settings=settings,
            z=float(z),
            actions=actions,
        )


        prestress_rows.append(
            {
                "z": float(z),
                "Pp": prestress.Pp,
                "ex": prestress.ex,
                "ey": prestress.ey,
            }
        )

        action_rows.append(
            {
                "z": float(z),
                "N": actions.N,
                "Mx": actions.Mx,
                "My": actions.My,
                "Tx_jourawski": actions.Tx_jourawski,
                "Ty_jourawski": actions.Ty_jourawski,
                "Tz": actions.Tz,
            }
        )

        navier_rows_all.extend(navier_rows)
        shear_rows_all.extend(shear_rows)

        station_summary_rows.append(
            station_summary_row(
                z=float(z),
                actions=actions,
                navier_rows=navier_rows,
                shear_rows=shear_rows,
            )
        )
        shear_extreme_rows_all.extend(shear_extreme_rows_at_station(shear_rows))

        if settings.debug_enabled:
            section_debug_rows.append(
                {
                    "z": float(z),
                    "Pp": prestress.Pp,
                    "ratio": prestress.ratio,
                    "area_effective": prestress.area_effective,
                    "area_reference": prestress.area_reference,
                    "xp": prestress.xp,
                    "yp": prestress.yp,
                    "Cx": prestress.Cx,
                    "Cy": prestress.Cy,
                    "ex": prestress.ex,
                    "ey": prestress.ey,
                    "Mx_ext": actions.Mx_ext,
                    "My_ext": actions.My_ext,
                    "Mx_prestress": actions.Mx_prestress,
                    "My_prestress": actions.My_prestress,
                    "dMx_dz": actions.dMx_dz,
                    "dMy_dz": actions.dMy_dz,
                }
            )

    written_files: list[Path] = []

    written_files.append(
        write_prestress_resultant_csv(
            output_path=settings.output_directory / settings.prestress_resultant_file,
            prestress_rows=prestress_rows,
        )
    )

    written_files.append(
        write_internal_actions_csv(
            output_path=settings.output_directory / settings.internal_actions_file,
            action_rows=action_rows,
        )
    )

    written_files.append(
        write_navier_stresses_csv(
            output_path=settings.output_directory / settings.navier_stresses_file,
            navier_rows=navier_rows_all,
        )
    )

    written_files.append(
        write_shear_stresses_csv(
            output_path=settings.output_directory / settings.shear_stresses_file,
            shear_rows=shear_rows_all,
        )
    )

    written_files.append(
        write_polygon_vertices_csv(
            section_field=section_field,
            output_path=settings.output_directory / settings.polygon_vertices_file,
            z_values=settings.z_stations,
        )
    )

    written_files.append(
        write_mechanical_report(
            output_path=settings.output_directory / settings.mechanical_report_file,
            settings=settings,
            station_summary_rows=station_summary_rows,
            shear_extreme_rows=shear_extreme_rows_all,
        )
    )

    written_files.extend(
        write_debug_outputs(
            settings=settings,
            prestress_debug_rows=prestress_debug_rows,
            gradient_debug_rows=gradient_debug_rows,
            section_debug_rows=section_debug_rows,
        )
    )

    return written_files


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Run a minimal CSF cantilever pole section check."
    )
    parser.add_argument(
        "settings",
        nargs="?",
        default="pole_analysis_settings.yaml",
        help="Path to the YAML settings file.",
    )
    return parser.parse_args()


def main() -> None:
    """Command-line entry point."""

    args = parse_args()
    settings = read_settings(Path(args.settings).resolve())

    written_files = run(settings)

    print("CSF cantilever pole check completed.")
    print("Written files:")
    for path in written_files:
        print(f"  - {path}")


if __name__ == "__main__":
    main()

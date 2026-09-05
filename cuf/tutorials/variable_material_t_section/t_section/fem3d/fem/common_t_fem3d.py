#!/usr/bin/env python3
# Version: T-section non-prismatic FEM3D validation v5 - 2026-09-03
# H8/SSPbrick reference driven by the same CSF geometry and problem YAML
# definitions used by the CUF bending and torsion validation cases.

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml


SUPPORTED_ELEMENTS = {"stdBrick", "SSPbrick"}
BENDING_TYPE = "uniform_surface_load"
TORSION_TYPE = "torsion_uniform"


def _resolve(base: Path, rel: str) -> Path:
    path = Path(rel)
    return path if path.is_absolute() else (base / path).resolve()


def _parse_nu(csf: dict) -> float:
    laws = csf.get("shear_weight_laws", [])
    if not laws:
        raise ValueError("missing CSF shear_weight_laws")
    token = str(laws[0]).strip()
    if not (token.startswith("iso(") and token.endswith(")")):
        raise ValueError("expected CSF shear_weight_laws: ['iso(nu)']")
    return float(token[4:-1])


def _polygon_data(poly: dict) -> dict:
    name = str(poly.get("name", "")).strip()
    if not name:
        raise ValueError("every CSF polygon must have a non-empty name")
    vertices = np.asarray(poly["vertices"], dtype=float)
    if vertices.ndim != 2 or vertices.shape[0] < 3 or vertices.shape[1] != 2:
        raise ValueError(f"invalid vertices for polygon {name!r}")

    # The structured T-section mesh must represent the CSF polygon exactly,
    # never replace a more general polygon by its bounding box.  Collinear
    # intermediate vertices are allowed (the supplied top flange uses them).
    shifted = np.roll(vertices, -1, axis=0)
    polygon_area = 0.5 * abs(float(np.sum(vertices[:, 0] * shifted[:, 1] - shifted[:, 0] * vertices[:, 1])))
    ymin = float(vertices[:, 0].min())
    ymax = float(vertices[:, 0].max())
    zmin = float(vertices[:, 1].min())
    zmax = float(vertices[:, 1].max())
    box_area = (ymax - ymin) * (zmax - zmin)
    area_tol = 1.0e-10 * max(1.0, box_area)
    if not math.isclose(polygon_area, box_area, rel_tol=0.0, abs_tol=area_tol):
        raise ValueError(
            f"CSF polygon {name!r} is not the exact rectangle required by the structured T-section mesher; "
            "refusing to approximate or reshape the geometry"
        )

    return {
        "name": name,
        "vertices": tuple((float(y), float(z)) for y, z in vertices),
        "ymin": ymin,
        "ymax": ymax,
        "zmin": zmin,
        "zmax": zmax,
        "E": float(poly["weight"]),
    }


def _section_data(section: dict) -> dict:
    polygons = {}
    for raw in section.get("polygons", []):
        poly = _polygon_data(raw)
        if poly["name"] in polygons:
            raise ValueError(f"duplicate CSF polygon name {poly['name']!r}")
        polygons[poly["name"]] = poly

    # The structured reference mesh is the existing T-section mesher.  Its
    # dimensions are always read from the CSF polygons; no geometry values are
    # duplicated in the FEM adapter.
    try:
        top = polygons["top_flange"]
        web = polygons["web"]
    except KeyError as exc:
        raise ValueError("this FEM3D T-section mesher requires CSF polygons 'top_flange' and 'web'") from exc

    scale = max(
        1.0,
        abs(top["zmin"]), abs(top["zmax"]),
        abs(web["zmin"]), abs(web["zmax"]),
    )
    tol = 1.0e-10 * scale
    if not math.isclose(web["zmax"], top["zmin"], rel_tol=0.0, abs_tol=tol):
        raise ValueError("top_flange must start at the web top surface")
    if not (top["ymin"] < web["ymin"] < web["ymax"] < top["ymax"]):
        raise ValueError("top_flange must overhang both sides of the web")
    return {
        "x": float(section["z"]),
        "polygons": polygons,
        "top_flange": top,
        "web": web,
    }


def _problem_from_case(
    case_path: Path,
    case: dict,
) -> tuple[dict, Path | None, Path]:
    spec = case["problem"]
    if not isinstance(spec, dict):
        raise TypeError("case.problem must be a YAML mapping")

    if "yaml" not in spec:
        model_spec = case.get("model")
        if not isinstance(model_spec, dict) or "csf_yaml" not in model_spec:
            raise ValueError("inline FEM problem requires case.model.csf_yaml")
        return spec, None, _resolve(case_path.parent, model_spec["csf_yaml"])

    problem_path = _resolve(case_path.parent, spec["yaml"])
    document = yaml.safe_load(problem_path.read_text(encoding="utf-8"))
    problem = document.get("problem")
    if not isinstance(problem, dict):
        raise TypeError(f"{problem_path}: top-level 'problem' must be a YAML mapping")
    model_spec = document.get("model")
    if not isinstance(model_spec, dict) or "csf_yaml" not in model_spec:
        raise ValueError(f"{problem_path}: top-level model.csf_yaml is required")
    model_path = _resolve(problem_path.parent, model_spec["csf_yaml"])

    # If a case-level model is also supplied, it is only accepted when it
    # resolves to the same file. This prevents the FEM load and geometry from
    # silently coming from different specifications.
    case_model = case.get("model")
    if case_model is not None:
        if not isinstance(case_model, dict) or "csf_yaml" not in case_model:
            raise ValueError("case.model must contain csf_yaml")
        case_model_path = _resolve(case_path.parent, case_model["csf_yaml"])
        if case_model_path != model_path:
            raise ValueError(
                "case.model.csf_yaml and problem YAML model.csf_yaml resolve to different files"
            )

    return problem, problem_path, model_path


def _parse_uniform_surface_problem(problem: dict) -> dict:
    unknown = sorted(str(key) for key in problem if key not in {"type", "surface", "components"})
    if unknown:
        raise ValueError(f"uniform_surface_load contains unsupported key(s): {', '.join(unknown)}")

    surface = problem.get("surface")
    if not isinstance(surface, dict):
        raise TypeError("problem.surface must be a YAML mapping")
    unknown = sorted(str(key) for key in surface if key not in {"polygon_name", "edge_start_point_id"})
    if unknown:
        raise ValueError(f"problem.surface contains unsupported key(s): {', '.join(unknown)}")
    if "polygon_name" not in surface or "edge_start_point_id" not in surface:
        raise ValueError("problem.surface requires polygon_name and edge_start_point_id")
    polygon_name = str(surface["polygon_name"]).strip()
    if not polygon_name:
        raise ValueError("problem.surface.polygon_name must not be empty")
    edge_id = surface["edge_start_point_id"]
    if isinstance(edge_id, bool) or not isinstance(edge_id, int):
        raise TypeError("problem.surface.edge_start_point_id must be an integer")
    if edge_id < 0:
        raise ValueError("problem.surface.edge_start_point_id must be >= 0")

    components = problem.get("components")
    if not isinstance(components, dict):
        raise TypeError("problem.components must be a YAML mapping")
    unsupported = sorted(str(key) for key in components if key != "z")
    if unsupported:
        raise ValueError(
            "problem.components contains unsupported component(s): "
            f"{', '.join(unsupported)}; the CUF adapter accepts only global z"
        )
    if "z" not in components:
        raise ValueError("problem.components.z is required")

    z_component = float(components["z"])
    if not math.isfinite(z_component):
        raise ValueError("problem.components.z must be finite")
    return {
        "surface_polygon_name": polygon_name,
        "surface_edge_start_point_id": edge_id,
        "surface_z_component": z_component,
    }


def _parse_uniform_torsion_problem(problem: dict) -> dict:
    unknown = sorted(str(key) for key in problem if key not in {"type", "amplitude"})
    if unknown:
        raise ValueError(f"torsion_uniform contains unsupported key(s): {', '.join(unknown)}")
    amplitude = float(problem.get("amplitude", 1.0))
    if not math.isfinite(amplitude):
        raise ValueError("problem.amplitude must be finite")
    return {"amplitude": amplitude}


def read_case(case_path: str | Path) -> dict:
    case_path = Path(case_path).resolve()
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    problem, problem_path, model_path = _problem_from_case(case_path, case)
    model = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    csf = model["CSF"]
    sections = sorted(csf["sections"].items(), key=lambda kv: float(kv[1]["z"]))
    if len(sections) != 2:
        raise ValueError("this FEM3D reference expects exactly two CSF sections S0/S1")
    s0 = _section_data(sections[0][1])
    s1 = _section_data(sections[1][1])
    if not s1["x"] > s0["x"]:
        raise ValueError("S1 must lie after S0 along the beam axis")

    if set(s0["polygons"]) != set(s1["polygons"]):
        raise ValueError("S0/S1 must contain the same named CSF polygons")
    for name in s0["polygons"]:
        if len(s0["polygons"][name]["vertices"]) != len(s1["polygons"][name]["vertices"]):
            raise ValueError(f"polygon {name!r} must preserve its CSF vertex topology between S0/S1")

    problem_type = str(problem.get("type", ""))
    if problem_type == BENDING_TYPE:
        problem_data = _parse_uniform_surface_problem(problem)
    elif problem_type == TORSION_TYPE:
        problem_data = _parse_uniform_torsion_problem(problem)
    else:
        raise ValueError(f"unsupported problem.type {problem_type!r}")

    mesh = case["mesh"]
    analysis = case.get("analysis", {})
    output = case.get("output", {})
    element_type = str(analysis.get("element", "stdBrick"))
    if element_type not in SUPPORTED_ELEMENTS:
        raise ValueError(f"element must be one of {sorted(SUPPORTED_ELEMENTS)}")

    result = {
        "case_path": case_path,
        "model_path": model_path,
        "problem_path": problem_path,
        "case_name": str(case.get("case", {}).get("name", case_path.stem)),
        "problem_type": problem_type,
        "s0": s0,
        "s1": s1,
        "x0": s0["x"],
        "x1": s1["x"],
        "L": s1["x"] - s0["x"],
        "nu": _parse_nu(csf),
        "nx": int(mesh["longitudinal_divisions"]),
        "web_ny": int(mesh["web_width_divisions"]),
        "web_nz": int(mesh["web_height_divisions"]),
        "overhang_ny": int(mesh["flange_overhang_divisions"]),
        "flange_nz": int(mesh["flange_thickness_divisions"]),
        "load_gauss_order": int(mesh.get("load_gauss_order", 4)),
        "element_type": element_type,
        "system": str(analysis.get("system", "SparseGeneral")),
        "output_dir": _resolve(case_path.parent, output.get("directory", f"../output/{case_path.stem}")),
        "stations": tuple(float(v) for v in case.get("sampling", {}).get("stations", [0.0, 0.25, 0.5, 0.75, 1.0])),
    }
    result.update(problem_data)
    return result


def _lerp(a: float, b: float, t: float) -> float:
    return float(a + (b - a) * t)


def state_at(d: dict, x: float) -> dict:
    t = (float(x) - d["x0"]) / d["L"]
    state = {"x": float(x), "polygons": {}}
    for name in d["s0"]["polygons"]:
        r0 = d["s0"]["polygons"][name]
        r1 = d["s1"]["polygons"][name]
        v0 = np.asarray(r0["vertices"], dtype=float)
        v1 = np.asarray(r1["vertices"], dtype=float)
        vertices = v0 + (v1 - v0) * t
        poly = {
            key: _lerp(r0[key], r1[key], t)
            for key in ("ymin", "ymax", "zmin", "zmax", "E")
        }
        poly["name"] = name
        poly["vertices"] = tuple((float(y), float(z)) for y, z in vertices)
        state["polygons"][name] = poly

    state["top_flange"] = state["polygons"]["top_flange"]
    state["web"] = state["polygons"]["web"]
    return state


def _selected_edge(d: dict, x: float) -> tuple[np.ndarray, np.ndarray]:
    state = state_at(d, x)
    name = d["surface_polygon_name"]
    try:
        vertices = np.asarray(state["polygons"][name]["vertices"], dtype=float)
    except KeyError as exc:
        raise ValueError(f"problem.surface.polygon_name {name!r} is not present in the CSF model") from exc
    index = int(d["surface_edge_start_point_id"])
    if index < 0 or index >= len(vertices):
        raise ValueError(
            f"problem.surface.edge_start_point_id={index} is outside polygon {name!r} "
            f"with {len(vertices)} vertices"
        )
    return vertices[index], vertices[(index + 1) % len(vertices)]


def _all_vertices_at(d: dict, x: float) -> tuple[tuple[float, float], ...]:
    state = state_at(d, x)
    return tuple(
        (float(y), float(z))
        for poly in state["polygons"].values()
        for y, z in poly["vertices"]
    )


def _torsion_points(d: dict, x: float) -> tuple[tuple[float, float], tuple[float, float]]:
    vertices = _all_vertices_at(d, x)
    if not vertices:
        raise ValueError(f"no CSF vertices available at x={x}")
    z_values = [point[1] for point in vertices]
    z_min = min(z_values)
    z_max = max(z_values)
    scale = max(1.0, abs(z_min), abs(z_max))
    tol = 1.0e-10 * scale
    top = [point for point in vertices if math.isclose(point[1], z_max, rel_tol=0.0, abs_tol=tol)]
    bottom = [point for point in vertices if math.isclose(point[1], z_min, rel_tol=0.0, abs_tol=tol)]
    if not top or not bottom:
        raise ValueError(f"cannot identify CUF torsion vertices at x={x}")
    return min(top, key=lambda point: point[0]), max(bottom, key=lambda point: point[0])


def _grid(a: float, b: float, n: int) -> np.ndarray:
    if n < 1:
        raise ValueError("all mesh divisions must be >= 1")
    return np.linspace(float(a), float(b), int(n) + 1)


@dataclass(frozen=True)
class ElementRecord:
    tag: int
    conn: tuple[int, ...]
    region: str
    ix: int


class TSectionMesh:
    """Conforming H8 mesh: web + three top-flange blocks, with shared interface nodes."""

    def __init__(self, d: dict):
        self.d = d
        self.nodes: dict[int, tuple[float, float, float]] = {}
        self._node_by_key: dict[tuple[int, float, float], int] = {}
        self.elements: list[ElementRecord] = []
        self._build()

    @staticmethod
    def _round(value: float) -> float:
        return round(float(value), 12)

    def _node(self, ix: int, y: float, z: float) -> int:
        key = (int(ix), self._round(y), self._round(z))
        if key not in self._node_by_key:
            tag = len(self._node_by_key) + 1
            x = self.d["x0"] + self.d["L"] * ix / self.d["nx"]
            self._node_by_key[key] = tag
            self.nodes[tag] = (float(x), float(y), float(z))
        return self._node_by_key[key]

    def existing_node(self, ix: int, y: float, z: float) -> int:
        return self._node_by_key[(int(ix), self._round(y), self._round(z))]

    def _add_block(self, ix: int, region: str, y0a: float, y1a: float, z0a: float, z1a: float,
                   y0b: float, y1b: float, z0b: float, z1b: float, ny: int, nz: int) -> None:
        ya = _grid(y0a, y1a, ny)
        za = _grid(z0a, z1a, nz)
        yb = _grid(y0b, y1b, ny)
        zb = _grid(z0b, z1b, nz)
        for jy in range(ny):
            for kz in range(nz):
                conn = (
                    self._node(ix,     ya[jy],     za[kz]),
                    self._node(ix + 1, yb[jy],     zb[kz]),
                    self._node(ix + 1, yb[jy + 1], zb[kz]),
                    self._node(ix,     ya[jy + 1], za[kz]),
                    self._node(ix,     ya[jy],     za[kz + 1]),
                    self._node(ix + 1, yb[jy],     zb[kz + 1]),
                    self._node(ix + 1, yb[jy + 1], zb[kz + 1]),
                    self._node(ix,     ya[jy + 1], za[kz + 1]),
                )
                self.elements.append(ElementRecord(len(self.elements) + 1, conn, region, ix))

    def _build(self) -> None:
        d = self.d
        for ix in range(d["nx"]):
            xa = d["x0"] + d["L"] * ix / d["nx"]
            xb = d["x0"] + d["L"] * (ix + 1) / d["nx"]
            a, b = state_at(d, xa), state_at(d, xb)
            wa, wb = a["web"], b["web"]
            fa, fb = a["top_flange"], b["top_flange"]

            self._add_block(ix, "web",
                            wa["ymin"], wa["ymax"], wa["zmin"], wa["zmax"],
                            wb["ymin"], wb["ymax"], wb["zmin"], wb["zmax"],
                            d["web_ny"], d["web_nz"])

            # Top flange split into left overhang, center over web, right overhang.
            self._add_block(ix, "top_flange",
                            fa["ymin"], wa["ymin"], fa["zmin"], fa["zmax"],
                            fb["ymin"], wb["ymin"], fb["zmin"], fb["zmax"],
                            d["overhang_ny"], d["flange_nz"])
            self._add_block(ix, "top_flange",
                            wa["ymin"], wa["ymax"], fa["zmin"], fa["zmax"],
                            wb["ymin"], wb["ymax"], fb["zmin"], fb["zmax"],
                            d["web_ny"], d["flange_nz"])
            self._add_block(ix, "top_flange",
                            wa["ymax"], fa["ymax"], fa["zmin"], fa["zmax"],
                            wb["ymax"], fb["ymax"], fb["zmin"], fb["zmax"],
                            d["overhang_ny"], d["flange_nz"])

    def plane_nodes(self, ix: int) -> list[int]:
        x = self.d["x0"] + self.d["L"] * ix / self.d["nx"]
        tol = 1.0e-10 * max(1.0, abs(self.d["L"]))
        return [tag for tag, xyz in self.nodes.items() if abs(xyz[0] - x) <= tol]


def _q4(r: float, s: float) -> np.ndarray:
    return np.asarray([
        0.25 * (1-r) * (1-s),
        0.25 * (1+r) * (1-s),
        0.25 * (1+r) * (1+s),
        0.25 * (1-r) * (1+s),
    ], dtype=float)


def _q4_derivatives(r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    dndr = np.asarray([
        -0.25 * (1-s),
        +0.25 * (1-s),
        +0.25 * (1+s),
        -0.25 * (1+s),
    ], dtype=float)
    dnds = np.asarray([
        -0.25 * (1-r),
        -0.25 * (1+r),
        +0.25 * (1+r),
        +0.25 * (1-r),
    ], dtype=float)
    return dndr, dnds


def _l2(r: float) -> np.ndarray:
    return np.asarray([0.5 * (1-r), 0.5 * (1+r)], dtype=float)


def _add_load(loads: dict[int, np.ndarray], tag: int, vec: Iterable[float]) -> None:
    loads.setdefault(int(tag), np.zeros(3, dtype=float))
    loads[int(tag)] += np.asarray(tuple(vec), dtype=float)


def _nodes_on_section_edge(
    mesh: TSectionMesh,
    ix: int,
    p0: np.ndarray,
    p1: np.ndarray,
) -> list[tuple[float, int]]:
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    direction = p1 - p0
    length2 = float(np.dot(direction, direction))
    if length2 <= 0.0:
        raise ValueError("selected CSF polygon edge has zero length")
    scale = max(1.0, float(np.linalg.norm(p0)), float(np.linalg.norm(p1)))
    tol = 1.0e-9 * scale
    result = []
    for tag in mesh.plane_nodes(ix):
        _, y, z = mesh.nodes[tag]
        point = np.asarray([y, z], dtype=float)
        t = float(np.dot(point - p0, direction) / length2)
        if t < -tol or t > 1.0 + tol:
            continue
        projected = p0 + t * direction
        if float(np.linalg.norm(point - projected)) <= tol:
            result.append((min(1.0, max(0.0, t)), tag))
    result.sort(key=lambda item: item[0])
    if len(result) < 2:
        raise ValueError(f"selected CSF edge is not represented by FEM boundary nodes on plane {ix}")
    if not math.isclose(result[0][0], 0.0, rel_tol=0.0, abs_tol=tol):
        raise ValueError(f"FEM boundary does not contain selected edge start on plane {ix}")
    if not math.isclose(result[-1][0], 1.0, rel_tol=0.0, abs_tol=tol):
        raise ValueError(f"FEM boundary does not contain selected edge end on plane {ix}")
    return result


def bending_loads(d: dict, mesh: TSectionMesh) -> dict[int, np.ndarray]:
    """Assemble the CUF ``uniform_surface_load`` on the real FEM surface.

    The surface is selected by the same CSF polygon name and edge-start vertex
    index used by the CUF adapter.  The traction is the same uniform global-z
    traction and the quadrature uses the actual isoparametric surface Jacobian,
    so the physical (not projected) surface measure is integrated.
    """
    points, weights = np.polynomial.legendre.leggauss(d["load_gauss_order"])
    loads: dict[int, np.ndarray] = {}
    traction = np.asarray([0.0, 0.0, d["surface_z_component"]], dtype=float)

    for ix in range(d["nx"]):
        xa = d["x0"] + d["L"] * ix / d["nx"]
        xb = d["x0"] + d["L"] * (ix + 1) / d["nx"]
        edge_a = _selected_edge(d, xa)
        edge_b = _selected_edge(d, xb)
        nodes_a = _nodes_on_section_edge(mesh, ix, *edge_a)
        nodes_b = _nodes_on_section_edge(mesh, ix + 1, *edge_b)
        if len(nodes_a) != len(nodes_b):
            raise ValueError(
                f"selected surface edge has incompatible FEM subdivisions between planes {ix} and {ix + 1}"
            )
        for (ta, _), (tb, _) in zip(nodes_a, nodes_b):
            if not math.isclose(ta, tb, rel_tol=0.0, abs_tol=1.0e-10):
                raise ValueError(
                    f"selected surface edge uses non-homologous FEM subdivisions between planes {ix} and {ix + 1}"
                )

        for j in range(len(nodes_a) - 1):
            tags = [
                nodes_a[j][1],
                nodes_b[j][1],
                nodes_b[j + 1][1],
                nodes_a[j + 1][1],
            ]
            xyz = np.asarray([mesh.nodes[tag] for tag in tags], dtype=float)
            local = np.zeros((4, 3), dtype=float)
            for r, wr in zip(points, weights):
                for s, ws in zip(points, weights):
                    r = float(r)
                    s = float(s)
                    N = _q4(r, s)
                    dndr, dnds = _q4_derivatives(r, s)
                    tangent_r = dndr @ xyz
                    tangent_s = dnds @ xyz
                    jacobian = float(np.linalg.norm(np.cross(tangent_r, tangent_s)))
                    if not jacobian > 0.0:
                        raise ValueError("degenerate loaded FEM surface patch")
                    local += (
                        float(wr)
                        * float(ws)
                        * jacobian
                        * N[:, None]
                        * traction[None, :]
                    )
            for tag, force in zip(tags, local):
                _add_load(loads, tag, force)
    return loads


def torsion_loads(d: dict, mesh: TSectionMesh) -> dict[int, np.ndarray]:
    """Assemble the CUF ``torsion_uniform`` pair with longitudinal measure dx.

    At every section the positive point is the leftmost CSF vertex on the
    maximum-z boundary and the negative point is the rightmost CSF vertex on
    the minimum-z boundary, exactly as in the CUF adapter.  No half-wave phase
    and no fixed transverse coordinates are introduced.
    """
    points, weights = np.polynomial.legendre.leggauss(d["load_gauss_order"])
    loads: dict[int, np.ndarray] = {}
    for ix in range(d["nx"]):
        xa = d["x0"] + d["L"] * ix / d["nx"]
        xb = d["x0"] + d["L"] * (ix + 1) / d["nx"]
        plus_a, minus_a = _torsion_points(d, xa)
        plus_b, minus_b = _torsion_points(d, xb)
        paths = (
            (plus_a, plus_b, +1.0),
            (minus_a, minus_b, -1.0),
        )
        for point_a, point_b, sign in paths:
            tags = [
                mesh.existing_node(ix, point_a[0], point_a[1]),
                mesh.existing_node(ix + 1, point_b[0], point_b[1]),
            ]
            local = np.zeros(2, dtype=float)
            jacx = 0.5 * (xb - xa)
            for r, wr in zip(points, weights):
                qz = sign * d["amplitude"]
                local += float(wr) * _l2(float(r)) * qz * jacx
            for tag, fz in zip(tags, local):
                _add_load(loads, tag, (0.0, 0.0, float(fz)))
    return loads


def build_loads(d: dict, mesh: TSectionMesh) -> dict[int, np.ndarray]:
    if d["problem_type"] == BENDING_TYPE:
        return bending_loads(d, mesh)
    if d["problem_type"] == TORSION_TYPE:
        return torsion_loads(d, mesh)
    raise ValueError(d["problem_type"])


def resultants(nodes: dict[int, tuple[float, float, float]], forces: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    force = np.zeros(3, dtype=float)
    moment = np.zeros(3, dtype=float)
    for tag, f in forces.items():
        r = np.asarray(nodes[tag], dtype=float)
        f = np.asarray(f, dtype=float)
        force += f
        moment += np.cross(r, f)
    return force, moment


def material_table(d: dict) -> tuple[dict[tuple[str, int], int], dict[int, float]]:
    key_to_tag: dict[tuple[str, int], int] = {}
    tag_to_E: dict[int, float] = {}
    unique: dict[float, int] = {}
    for ix in range(d["nx"]):
        xmid = d["x0"] + d["L"] * (ix + 0.5) / d["nx"]
        state = state_at(d, xmid)
        for region in ("web", "top_flange"):
            E = float(state[region]["E"])
            ek = round(E, 10)
            if ek not in unique:
                tag = len(unique) + 1
                unique[ek] = tag
                tag_to_E[tag] = E
            key_to_tag[(region, ix)] = unique[ek]
    return key_to_tag, tag_to_E


def end_constraints(d: dict, mesh: TSectionMesh, ops) -> tuple[list[int], list[int], int]:
    end0 = mesh.plane_nodes(0)
    end1 = mesh.plane_nodes(d["nx"])

    # Match the CUF gauge exactly: the only axial restraint is the physical
    # point (x_start, y, z) = (x_start, 0, 0).  Do not silently substitute
    # the nearest FEM node if that point is absent from the mesh.
    try:
        anchor = mesh.existing_node(0, 0.0, 0.0)
    except KeyError as exc:
        raise ValueError(
            "FEM mesh does not contain the required axial anchor node "
            "(x_start, y, z) = (x_start, 0, 0)"
        ) from exc

    for tag in end0:
        if tag == anchor:
            ops.fix(tag, 1, 1, 1)
        else:
            ops.fix(tag, 0, 1, 1)
    for tag in end1:
        ops.fix(tag, 0, 1, 1)
    return end0, end1, anchor


def solve(d: dict, mesh: TSectionMesh, loads: dict[int, np.ndarray]):
    try:
        import openseespy.opensees as ops
    except ModuleNotFoundError as exc:
        raise RuntimeError("OpenSeesPy required: python -m pip install openseespy") from exc

    ops.wipe()
    ops.model("Basic", "-ndm", 3, "-ndf", 3)
    for tag, (x, y, z) in mesh.nodes.items():
        ops.node(tag, x, y, z)

    element_material, tag_to_E = material_table(d)
    for mat_tag, E in sorted(tag_to_E.items()):
        ops.nDMaterial("ElasticIsotropic", mat_tag, float(E), float(d["nu"]))

    for rec in mesh.elements:
        mat_tag = element_material[(rec.region, rec.ix)]
        ops.element(d["element_type"], rec.tag, *rec.conn, mat_tag)

    end0, end1, anchor = end_constraints(d, mesh, ops)
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for tag, f in loads.items():
        ops.load(tag, float(f[0]), float(f[1]), float(f[2]))

    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system(d["system"])
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    code = int(ops.analyze(1))
    if code != 0:
        raise RuntimeError(f"OpenSees analyze failed with code {code}")

    disp = {tag: np.asarray(ops.nodeDisp(tag), dtype=float) for tag in mesh.nodes}
    ops.reactions()
    reactions = {tag: np.asarray(ops.nodeReaction(tag), dtype=float) for tag in set(end0 + end1)}
    return disp, reactions, anchor


def write_outputs(d: dict, mesh: TSectionMesh, loads: dict[int, np.ndarray], displacements: dict[int, np.ndarray], reactions: dict[int, np.ndarray] | None = None) -> None:
    out = Path(d["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "fem3d_native_displacements.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["node_id", "x", "y", "z", "ux", "uy", "uz"])
        for tag in sorted(mesh.nodes):
            writer.writerow([tag, *mesh.nodes[tag], *map(float, displacements[tag])])

    stations_path = out / "station_extrema.csv"
    with stations_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["x_over_L", "x", "max_abs_ux", "max_abs_uy", "max_abs_uz"])
        for station in d["stations"]:
            target = d["x0"] + station * d["L"]
            ix = int(round(station * d["nx"]))
            tags = mesh.plane_nodes(max(0, min(d["nx"], ix)))
            vals = np.asarray([displacements[tag] for tag in tags], dtype=float)
            writer.writerow([station, target, *np.max(np.abs(vals), axis=0)])

    # Point-by-point sampling matched to the CUF post-processing.
    # The existing sectional extrema above are preserved unchanged.
    points_path = out / "station_points.csv"
    with points_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["x_over_L", "x", "point", "y", "z", "ux", "uy", "uz"])
        for station in d["stations"]:
            target = d["x0"] + station * d["L"]
            ix = int(round(station * d["nx"]))
            ix = max(0, min(d["nx"], ix))
            x_plane = d["x0"] + d["L"] * ix / d["nx"]
            tol_x = 1.0e-10 * max(1.0, abs(d["L"]))
            if not math.isclose(x_plane, target, rel_tol=0.0, abs_tol=tol_x):
                raise ValueError(
                    f"sampling station x/L={station} does not coincide with a FEM3D mesh plane"
                )

            state = state_at(d, x_plane)
            flange = state["top_flange"]
            web = state["web"]
            points = (
                ("center", 0.0, 0.0),
                ("plus", flange["ymin"], flange["zmax"]),
                ("minus", web["ymax"], web["zmin"]),
                ("bottom_mid", 0.0, web["zmin"]),
            )

            for name, y, z in points:
                try:
                    tag = mesh.existing_node(ix, y, z)
                except KeyError as exc:
                    raise ValueError(
                        f"CUF-matched sampling point {name!r} at x/L={station} "
                        f"is not a FEM3D node: (x,y,z)=({x_plane},{y},{z})"
                    ) from exc
                vec = np.asarray(displacements[tag], dtype=float)
                writer.writerow([station, x_plane, name, y, z, *map(float, vec)])

    af, am = resultants(mesh.nodes, loads)
    summary = out / "summary.txt"
    with summary.open("w", encoding="utf-8") as stream:
        stream.write(f"case = {d['case_name']}\n")
        stream.write(f"problem = {d['problem_type']}\n")
        stream.write(f"element = {d['element_type']}\n")
        stream.write(f"nodes = {len(mesh.nodes)}\n")
        stream.write(f"elements = {len(mesh.elements)}\n")
        stream.write(f"applied_force = {af.tolist()}\n")
        stream.write(f"applied_moment_about_origin = {am.tolist()}\n")
        if reactions is not None:
            rf, rm = resultants(mesh.nodes, reactions)
            stream.write(f"reaction_force = {rf.tolist()}\n")
            stream.write(f"reaction_moment_about_origin = {rm.tolist()}\n")
            stream.write(f"force_balance = {(af + rf).tolist()}\n")
            stream.write(f"moment_balance = {(am + rm).tolist()}\n")


def print_diagnostics(d: dict, mesh: TSectionMesh, loads: dict[int, np.ndarray]) -> None:
    af, am = resultants(mesh.nodes, loads)
    s0, s1 = d["s0"], d["s1"]
    print(f"case      : {d['case_name']}")
    print(f"problem   : {d['problem_type']}")
    print(f"model     : {d['model_path']}")
    if d.get("problem_path") is not None:
        print(f"problem-yaml: {d['problem_path']}")
    print(f"element   : {d['element_type']}")
    print(f"mesh      : nx={d['nx']} web_ny={d['web_ny']} web_nz={d['web_nz']} overhang_ny={d['overhang_ny']} flange_nz={d['flange_nz']}")
    print(f"nodes     : {len(mesh.nodes)}")
    print(f"elements  : {len(mesh.elements)}")
    print(f"S0 E      : flange={s0['top_flange']['E']:.6g} web={s0['web']['E']:.6g}")
    print(f"S1 E      : flange={s1['top_flange']['E']:.6g} web={s1['web']['E']:.6g}")
    print(f"load F    : {af}")
    print(f"load M@O  : {am}")

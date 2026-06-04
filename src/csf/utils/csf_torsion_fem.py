#!/usr/bin/env python3
"""
csf_torsion_fem.py

Dedicated Saint-Venant torsion FEM tool for CSF YAML models.

Purpose
-------
This module loads a generic CSF YAML model, samples one or more z-stations,
builds the active 2D cross-section topology, meshes it automatically, assigns
the resolved CSF shear carrier G_i / shear_w_i to each material region, and
builds a reusable torsion FEM pipeline.  The CSF/topology/mesh/material layer is
independent from the selected torsion formulation.

It intentionally does not read CSV exports and does not use sectionproperties
for the torsion solve.  The only sectional result produced here is the FEM unit-twist torsional stiffness through a selectable formulation.

The first implemented formulation is:

    prandtl-dirichlet

which solves the Prandtl stress-function problem for simply connected/open
sections.  Other formulations can be added to the registry without changing
the CSF YAML loader, topology bridge, mesh generator, material mapping, CLI
station handling, or output layer.

Dependencies
------------
Required at runtime:
    pip install numpy scipy pyyaml shapely triangle scikit-fem csfpy

Notes
-----
- scikit-fem is used as the mesh container for the generated triangular mesh.
- The CSF-to-FEM pipeline is formulation-independent.
- Each torsion formulation is implemented as a registered solver function.
- The linear systems are assembled explicitly here to keep every formulation
  transparent and independent from sectionproperties.
- CSF geometry/material loading is done directly from YAML through CSFReader.
- Missing inputs are command-line parameters; no structural or material default
  is invented silently.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import yaml
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
from shapely.geometry import MultiPolygon, Polygon as ShapelyPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

try:
    import triangle as triangle_lib
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'triangle'. Install it with: pip install triangle"
    ) from exc

try:
    from skfem import MeshTri
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'scikit-fem'. Install it with: pip install scikit-fem"
    ) from exc

from csf.io.csf_reader import CSFReader
from csf.io.csf_rough_validator import validate_text


TOKEN_CELL = "@cell"
TOKEN_CLOSED = "@closed"
TOKEN_WALL = "@wall"


@dataclass(frozen=True)
class PolygonInput:
    """Sampled CSF polygon payload used by this torsion FEM backend."""

    idx_polygon: int
    idx_container: Optional[int]
    name: str
    w: float
    shear_w: Optional[float]
    poisson: Optional[float]
    is_cell: bool
    vertices: List[Tuple[float, float]]


@dataclass(frozen=True)
class NodeShape:
    """Cached geometric payload for one CSF polygon node."""

    support_region: ShapelyPolygon
    outer_envelope: ShapelyPolygon


@dataclass(frozen=True)
class MeshPayload:
    """Triangular mesh and per-element shear carrier."""

    mesh: MeshTri
    points: np.ndarray          # shape: (npoints, 2)
    triangles: np.ndarray       # shape: (nelems, 3)
    element_G: np.ndarray       # shape: (nelems,)
    element_region: np.ndarray  # shape: (nelems,)
    region_names: Dict[int, str]


@dataclass(frozen=True)
class TorsionResult:
    """Result for one sampled station."""

    z: float
    gj_fem: float
    polar_upper_bound: float
    area: float
    nodes: int
    elements: int
    mesh_max_area: float
    min_angle: float
    formulation: str

    @property
    def reduction_ratio(self) -> float:
        """Return GJ_fem / integral(G*r^2 dA)."""
        if self.polar_upper_bound == 0.0:
            return float("nan")
        return self.gj_fem / self.polar_upper_bound


# -----------------------------------------------------------------------------
# CSF YAML loading
# -----------------------------------------------------------------------------


def _format_text_block(header: str, lines: List[str]) -> str:
    out = [header]
    out.extend(str(line) for line in lines)
    return "\n".join(out)


def _format_reader_issues(issues: List[Any], header: str) -> str:
    lines: List[str] = [header]
    for issue in issues:
        severity = str(getattr(issue, "severity", "ERROR"))
        code = getattr(issue, "code", None)
        path = getattr(issue, "path", None)
        message = getattr(issue, "message", str(issue))
        hint = getattr(issue, "hint", None)
        prefix = f"[{severity}]"
        if code:
            prefix += f" {code}"
        if path:
            prefix += f" {path}"
        lines.append(f"{prefix}: {message}")
        if hint:
            lines.append(f"Hint: {hint}")
    return "\n".join(lines)


def load_yaml(path: str | Path) -> Any:
    """Load a CSF YAML model and return the ContinuousSectionField object."""
    yaml_path = Path(path)
    try:
        text = yaml_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise SystemExit(f"Cannot read CSF YAML '{yaml_path}': {exc}") from exc

    ok, report_lines = validate_text(text, source=str(yaml_path))
    if not ok:
        raise SystemExit(
            _format_text_block(f"Prevalidation failed for '{yaml_path}':", report_lines)
        )

    try:
        res = CSFReader().read_file(str(yaml_path))
    except Exception as exc:
        raise SystemExit(
            f"Unexpected failure while reading CSF YAML '{yaml_path}': {exc}"
        ) from exc

    issues = list(getattr(res, "issues", []) or [])
    if not getattr(res, "ok", False) or getattr(res, "field", None) is None:
        if issues:
            raise SystemExit(_format_reader_issues(issues, f"CSFReader failed for '{yaml_path}':"))
        raise SystemExit(f"Could not load CSF model from '{yaml_path}'.")

    return res.field


def _load_station_set(run_config_path: Path, station_set_name: str) -> List[float]:
    """Load a station set from a YAML run-config/action file."""
    try:
        data = yaml.safe_load(run_config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot read run-config YAML '{run_config_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Run-config YAML '{run_config_path}' must contain a mapping.")

    station_sets = data.get("station_sets")
    if not isinstance(station_sets, dict) or not station_sets:
        raise SystemExit(
            f"Run-config YAML '{run_config_path}' must contain a non-empty 'station_sets:' mapping."
        )

    if station_set_name not in station_sets:
        raise SystemExit(
            f"Station set '{station_set_name}' not found. Available: {sorted(station_sets.keys())}"
        )

    raw = station_sets[station_set_name]
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"station_sets.{station_set_name} must be a non-empty list.")

    out: List[float] = []
    for i, value in enumerate(raw):
        if type(value) not in (int, float):
            raise SystemExit(
                f"station_sets.{station_set_name}[{i}] must be numeric, got {value!r}."
            )
        out.append(float(value))
    return out


def _parse_z_values(args: argparse.Namespace) -> List[float]:
    """Resolve z-stations explicitly from CLI arguments."""
    values: List[float] = []

    if args.z is not None:
        values.extend(float(z) for z in args.z)

    if args.z_list:
        for token in args.z_list.split(","):
            token = token.strip()
            if token:
                values.append(float(token))

    if args.run_config is not None or args.station_set is not None:
        if args.run_config is None or args.station_set is None:
            raise SystemExit("Use --run-config and --station-set together.")
        values.extend(_load_station_set(Path(args.run_config), args.station_set))

    if not values:
        raise SystemExit("No z-stations provided. Use --z, --z-list, or --run-config with --station-set.")

    # Preserve order but remove exact duplicates.
    seen = set()
    unique: List[float] = []
    for z in values:
        if z not in seen:
            seen.add(z)
            unique.append(z)
    return unique


# -----------------------------------------------------------------------------
# CSF sampled polygons and topology
# -----------------------------------------------------------------------------


def _name_has_cell_tag(name: str) -> bool:
    low = (name or "").lower()
    return (TOKEN_CELL in low) or (TOKEN_CLOSED in low)


def _read_optional_shear_w(idx_polygon: int, poly: Any) -> Optional[float]:
    """Read the sampled CSF shear carrier if it is explicitly exposed."""
    for attr_name in ("shear_weightabs", "shear_w"):
        if not hasattr(poly, attr_name):
            continue
        value = getattr(poly, attr_name)
        if value is None:
            return None
        try:
            shear_w = float(value)
        except Exception as exc:
            raise SystemExit(
                f"idx_polygon={idx_polygon} has invalid {attr_name}={value!r}."
            ) from exc
        if math.isnan(shear_w):
            return None
        return shear_w
    return None


def polygon_inputs_from_field(field: Any, z: float) -> Dict[int, PolygonInput]:
    """Sample a CSF field and return topology-aware polygon inputs."""
    sec = field.section(float(z))
    children_map = field.build_direct_children_map(float(z))

    parent_of: Dict[int, Optional[int]] = {}
    for parent_idx, child_idx_list in children_map.items():
        for child_idx in child_idx_list:
            parent_of[child_idx] = parent_idx

    out: Dict[int, PolygonInput] = {}
    for idx, poly in enumerate(sec.polygons):
        if not hasattr(poly, "weightabs"):
            raise SystemExit(f"idx_polygon={idx}: sampled polygon has no 'weightabs'.")

        name = str(getattr(poly, "name", f"poly_{idx}"))
        vertices = [(float(v.x), float(v.y)) for v in poly.vertices]
        w_abs = float(poly.weightabs)
        shear_w = _read_optional_shear_w(idx, poly)
        poisson = None
        if hasattr(poly, "poisson") and getattr(poly, "poisson") is not None:
            try:
                poisson = float(getattr(poly, "poisson"))
            except Exception:
                poisson = None

        out[idx] = PolygonInput(
            idx_polygon=idx,
            idx_container=parent_of.get(idx),
            name=name,
            w=w_abs,
            shear_w=shear_w,
            poisson=poisson,
            is_cell=_name_has_cell_tag(name),
            vertices=vertices,
        )
    return out


def _make_polygon(coords: List[Tuple[float, float]], label: str) -> ShapelyPolygon:
    """Build a shapely polygon without silently repairing invalid geometry."""
    poly = ShapelyPolygon(coords)
    if poly.is_empty:
        raise ValueError(f"{label}: polygon is empty.")
    if not poly.is_valid:
        raise ValueError(f"{label}: polygon is invalid.")
    if poly.geom_type != "Polygon":
        raise ValueError(f"{label}: expected Polygon, got {poly.geom_type}.")
    return poly


def _split_cell_polygon(vertices: List[Tuple[float, float]], label: str) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Split a slit-encoded @cell/@closed polygon into outer and inner loops."""
    if len(vertices) < 8:
        raise ValueError(f"{label}: too few vertices for a slit-encoded cell polygon.")

    first = vertices[0]
    i_outer_end: Optional[int] = None
    for i in range(1, len(vertices)):
        if vertices[i] == first:
            i_outer_end = i
            break

    if i_outer_end is None or i_outer_end < 3:
        raise ValueError(f"{label}: missing repeated first vertex for outer closure.")

    outer = vertices[:i_outer_end]
    inner = vertices[i_outer_end + 1 :]
    if inner and inner[-1] == first:
        inner = inner[:-1]
    if inner and inner[0] == inner[-1]:
        inner = inner[:-1]
    if len(inner) < 3:
        raise ValueError(f"{label}: insufficient inner loop vertices.")

    poly_a = _make_polygon(outer, f"{label} outer_candidate")
    poly_b = _make_polygon(inner, f"{label} inner_candidate")
    if abs(poly_a.area) >= abs(poly_b.area):
        return outer, inner
    return inner, outer


def _looks_like_slit_encoded_polygon(vertices: List[Tuple[float, float]]) -> bool:
    if len(vertices) < 8:
        return False
    first = vertices[0]
    return any(vertices[i] == first for i in range(1, len(vertices) - 3))


def _collect_children(polygon_inputs: Dict[int, PolygonInput]) -> Dict[Optional[int], List[int]]:
    children: Dict[Optional[int], List[int]] = {}
    for pid, poly in polygon_inputs.items():
        children.setdefault(poly.idx_container, []).append(pid)
    return children


def _union_or_raise(polys: List[ShapelyPolygon], label: str) -> BaseGeometry:
    out = unary_union(polys)
    if out.is_empty:
        raise ValueError(f"{label}: union produced an empty geometry.")
    return out


def _polygon_parts_from_geometry(geom: BaseGeometry, label: str) -> List[ShapelyPolygon]:
    """Extract polygonal area parts and ignore lower-dimensional leftovers."""
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        parts = [geom]
    elif geom.geom_type == "MultiPolygon":
        parts = list(geom.geoms)
    elif geom.geom_type == "GeometryCollection":
        parts = [g for g in geom.geoms if g.geom_type == "Polygon" and not g.is_empty]
    else:
        raise ValueError(f"{label}: expected polygonal geometry, got {geom.geom_type}.")

    out: List[ShapelyPolygon] = []
    for i, part in enumerate(parts):
        if not part.is_valid:
            raise ValueError(f"{label}: invalid polygon part {i}.")
        out.append(part)
    return out


def _build_node_shapes(polygon_inputs: Dict[int, PolygonInput]) -> Dict[int, NodeShape]:
    """Build support regions and parent cutout envelopes for all CSF nodes."""
    out: Dict[int, NodeShape] = {}
    for pid, poly in polygon_inputs.items():
        label = f"idx_polygon={pid} ({poly.name})"
        if poly.is_cell:
            outer_xy, inner_xy = _split_cell_polygon(poly.vertices, label)
            outer_poly = _make_polygon(outer_xy, f"{label} outer")
            inner_poly = _make_polygon(inner_xy, f"{label} inner")
            support_region = ShapelyPolygon(
                shell=list(outer_poly.exterior.coords)[:-1],
                holes=[list(inner_poly.exterior.coords)[:-1]],
            )
            if support_region.is_empty or not support_region.is_valid:
                raise ValueError(f"{label}: invalid intrinsic cell support region.")
            out[pid] = NodeShape(
                support_region=support_region,
                outer_envelope=support_region,
            )
            continue

        if _looks_like_slit_encoded_polygon(poly.vertices):
            raise ValueError(f"{label}: polygon looks slit-encoded but is not tagged @cell/@closed.")

        outer_poly = _make_polygon(poly.vertices, label)
        out[pid] = NodeShape(support_region=outer_poly, outer_envelope=outer_poly)
    return out


def compute_node_local_domains(polygon_inputs: Dict[int, PolygonInput]) -> Dict[int, List[ShapelyPolygon]]:
    """Compute each node local domain as support minus direct child envelopes."""
    children = _collect_children(polygon_inputs)
    node_shapes = _build_node_shapes(polygon_inputs)
    local_domains: Dict[int, List[ShapelyPolygon]] = {}

    for pid in polygon_inputs:
        label = f"idx_polygon={pid}"
        region: BaseGeometry = node_shapes[pid].support_region
        child_cutouts = [node_shapes[cid].outer_envelope for cid in children.get(pid, [])]
        if child_cutouts:
            region = region.difference(_union_or_raise(child_cutouts, f"{label} direct_children"))
        local_domains[pid] = _polygon_parts_from_geometry(region, f"{label} local_domain")
    return local_domains


# -----------------------------------------------------------------------------
# Triangle mesh generation
# -----------------------------------------------------------------------------


def _add_ring(vertices: List[Tuple[float, float]], vertex_map: Dict[Tuple[float, float], int], points: List[Tuple[float, float]], segments: List[Tuple[int, int]], precision: int) -> None:
    """Append a polygon ring to the global PSLG vertex/segment lists."""
    clean = list(vertices)
    if clean and clean[0] == clean[-1]:
        clean = clean[:-1]
    if len(clean) < 3:
        raise ValueError("Cannot mesh a ring with fewer than three vertices.")

    ids: List[int] = []
    for x, y in clean:
        key = (round(float(x), precision), round(float(y), precision))
        idx = vertex_map.get(key)
        if idx is None:
            idx = len(points)
            vertex_map[key] = idx
            points.append((float(x), float(y)))
        ids.append(idx)

    for i, a in enumerate(ids):
        b = ids[(i + 1) % len(ids)]
        if a != b:
            segments.append((a, b))


def _active_regions_from_domains(
    polygon_inputs: Dict[int, PolygonInput],
    local_domains: Dict[int, List[ShapelyPolygon]],
    require_shear: bool,
) -> Tuple[List[Tuple[int, ShapelyPolygon, float, str]], Dict[int, str]]:
    """Return active polygon parts with positive shear carrier."""
    regions: List[Tuple[int, ShapelyPolygon, float, str]] = []
    region_names: Dict[int, str] = {}
    next_region_id = 1

    for pid, poly in polygon_inputs.items():
        if poly.w == 0.0:
            continue
        if poly.shear_w is None:
            if require_shear:
                raise SystemExit(
                    f"idx_polygon={pid} ({poly.name}) has no sampled shear_w. "
                    "Declare shear_weight_laws or provide isotropic shear data in the CSF YAML."
                )
            continue
        G = float(poly.shear_w)
        if G <= 0.0:
            raise SystemExit(
                f"idx_polygon={pid} ({poly.name}) has non-positive shear carrier G={G}."
            )
        for part_i, part in enumerate(local_domains.get(pid, [])):
            if part.area <= 0.0:
                continue
            region_id = next_region_id
            next_region_id += 1
            label = f"idx={pid}:part={part_i}:{poly.name}"
            regions.append((region_id, part, G, label))
            region_names[region_id] = label

    if not regions:
        raise SystemExit("No active positive-G regions found at this station.")
    return regions, region_names


def build_mesh(
    polygon_inputs: Dict[int, PolygonInput],
    mesh_max_area: float,
    min_angle: float,
    boundary_precision: int,
    require_shear: bool = True,
) -> MeshPayload:
    """Build a constrained triangular mesh and return a scikit-fem MeshTri payload."""
    if mesh_max_area <= 0.0:
        raise SystemExit("--mesh-max-area must be positive.")
    if min_angle <= 0.0 or min_angle >= 34.0:
        raise SystemExit("--min-angle must be > 0 and < 34 for Triangle quality meshing.")

    local_domains = compute_node_local_domains(polygon_inputs)
    regions, region_names = _active_regions_from_domains(polygon_inputs, local_domains, require_shear)

    points: List[Tuple[float, float]] = []
    segments: List[Tuple[int, int]] = []
    holes: List[Tuple[float, float]] = []
    tri_regions: List[Tuple[float, float, int, float]] = []
    vertex_map: Dict[Tuple[float, float], int] = {}
    G_by_region: Dict[int, float] = {}

    for region_id, poly, G, _label in regions:
        _add_ring(list(poly.exterior.coords), vertex_map, points, segments, boundary_precision)
        for interior in poly.interiors:
            ring = list(interior.coords)
            _add_ring(ring, vertex_map, points, segments, boundary_precision)
            seed = ShapelyPolygon(ring).representative_point()
            holes.append((float(seed.x), float(seed.y)))
        seed = poly.representative_point()
        tri_regions.append((float(seed.x), float(seed.y), int(region_id), float(mesh_max_area)))
        G_by_region[region_id] = G

    pslg: Dict[str, Any] = {
        "vertices": np.asarray(points, dtype=float),
        "segments": np.asarray(segments, dtype=np.int32),
        "regions": np.asarray(tri_regions, dtype=float),
    }
    if holes:
        pslg["holes"] = np.asarray(holes, dtype=float)

    switches = f"pq{min_angle:g}a{mesh_max_area:g}A"

    tri = triangle_lib.triangulate(pslg, switches)


    if "vertices" not in tri or "triangles" not in tri:
        raise SystemExit("Triangle meshing failed: no vertices/triangles returned.")
    if "triangle_attributes" not in tri:
        raise SystemExit("Triangle meshing failed: region attributes were not returned.")

    out_points = np.asarray(tri["vertices"], dtype=float)
    out_tris = np.asarray(tri["triangles"], dtype=np.int32)
    attrs = np.asarray(tri["triangle_attributes"]).reshape(-1)
    elem_region = np.rint(attrs).astype(int)
    elem_G = np.asarray([G_by_region.get(int(r), float("nan")) for r in elem_region], dtype=float)

    if np.any(~np.isfinite(elem_G)):
        bad = sorted(set(int(r) for r in elem_region[~np.isfinite(elem_G)]))
        raise SystemExit(f"Mesh contains elements with unknown region attributes: {bad}")

    mesh = MeshTri(
     np.ascontiguousarray(out_points.T),
     np.ascontiguousarray(out_tris.T),
    )
    
    return MeshPayload(
        mesh=mesh,
        points=out_points,
        triangles=out_tris,
        element_G=elem_G,
        element_region=elem_region,
        region_names=region_names,
    )




# -----------------------------------------------------------------------------
# Debug diagnostics
# -----------------------------------------------------------------------------


def mesh_diagnostics(mesh_payload: MeshPayload) -> Dict[str, Any]:
    """Return explicit mesh diagnostics used to validate a torsion run."""
    points = mesh_payload.points
    triangles = mesh_payload.triangles
    boundary = _boundary_nodes_from_triangles(triangles)
    is_boundary = np.zeros(points.shape[0], dtype=bool)
    is_boundary[boundary] = True
    free_count = int(np.count_nonzero(~is_boundary))

    if points.shape[0] > 0:
        xmin, ymin = np.min(points, axis=0)
        xmax, ymax = np.max(points, axis=0)
    else:
        xmin = ymin = xmax = ymax = float("nan")

    elem_areas: List[float] = []
    for tri in triangles:
        A, _b, _c, _centroid = _triangle_geometry(points, tri)
        elem_areas.append(float(A))
    area_arr = np.asarray(elem_areas, dtype=float)

    unique_regions = sorted(set(int(r) for r in mesh_payload.element_region.tolist()))
    region_counts = {
        int(region): int(np.count_nonzero(mesh_payload.element_region == region))
        for region in unique_regions
    }

    return {
        "nodes": int(points.shape[0]),
        "elements": int(triangles.shape[0]),
        "boundary_nodes": int(boundary.size),
        "free_nodes": free_count,
        "bbox": [float(xmin), float(ymin), float(xmax), float(ymax)],
        "element_area_min": float(np.min(area_arr)) if area_arr.size else float("nan"),
        "element_area_max": float(np.max(area_arr)) if area_arr.size else float("nan"),
        "element_area_mean": float(np.mean(area_arr)) if area_arr.size else float("nan"),
        "G_min": float(np.min(mesh_payload.element_G)) if mesh_payload.element_G.size else float("nan"),
        "G_max": float(np.max(mesh_payload.element_G)) if mesh_payload.element_G.size else float("nan"),
        "regions": unique_regions,
        "region_counts": region_counts,
        "region_names": {int(k): str(v) for k, v in mesh_payload.region_names.items()},
    }


def print_mesh_diagnostics(mesh_payload: MeshPayload, *, z: float, mesh_max_area: float, min_angle: float) -> None:
    """Print human-readable diagnostics before solving."""
    d = mesh_diagnostics(mesh_payload)
    print("\n[csf_torsion_fem debug]")
    print(f"  z                       : {z:g}")
    print(f"  requested mesh max area : {mesh_max_area:g}")
    print(f"  requested min angle     : {min_angle:g}")
    print(f"  nodes                   : {d['nodes']}")
    print(f"  elements                : {d['elements']}")
    print(f"  boundary nodes          : {d['boundary_nodes']}")
    print(f"  free/interior nodes     : {d['free_nodes']}")
    print(
        "  bbox                    : "
        f"xmin={d['bbox'][0]:.12g}, ymin={d['bbox'][1]:.12g}, "
        f"xmax={d['bbox'][2]:.12g}, ymax={d['bbox'][3]:.12g}"
    )
    print(
        "  element area            : "
        f"min={d['element_area_min']:.12g}, "
        f"mean={d['element_area_mean']:.12g}, "
        f"max={d['element_area_max']:.12g}"
    )
    print(f"  element G range         : min={d['G_min']:.12g}, max={d['G_max']:.12g}")
    print(f"  regions                 : {d['regions']}")
    for region in d["regions"]:
        name = d["region_names"].get(region, "<unknown>")
        count = d["region_counts"].get(region, 0)
        print(f"    region {region}: elems={count}, {name}")
    if d["free_nodes"] == 0:
        print("  diagnostic              : no interior unknowns are available for the selected formulation.")
        print("  action                  : reduce --mesh-max-area; for small sections try area/50 or area/100.")


# -----------------------------------------------------------------------------
# Torsion FEM formulation registry
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SolverOutput:
    """Raw output returned by one torsion formulation backend."""

    gj: float
    polar_upper_bound: float
    area: float
    field: np.ndarray


TorsionSolver = Any
TORSION_FORMULATIONS: Dict[str, TorsionSolver] = {}


def register_formulation(name: str):
    """Register a torsion formulation by CLI/API name."""
    if not name or not isinstance(name, str):
        raise ValueError("Formulation name must be a non-empty string.")

    def _decorator(func: TorsionSolver) -> TorsionSolver:
        if name in TORSION_FORMULATIONS:
            raise ValueError(f"Duplicate torsion formulation name: {name}")
        TORSION_FORMULATIONS[name] = func
        return func

    return _decorator


def available_formulations() -> List[str]:
    """Return the registered torsion formulation names."""
    return sorted(TORSION_FORMULATIONS.keys())


def solve_torsion(
    mesh_payload: MeshPayload,
    formulation: str,
    *,
    pin_node: int,
) -> SolverOutput:
    """Dispatch the torsion solve to a registered formulation backend."""
    try:
        solver = TORSION_FORMULATIONS[formulation]
    except KeyError as exc:
        raise SystemExit(
            f"Unknown --formulation {formulation!r}. "
            f"Available formulations: {available_formulations()}"
        ) from exc
    return solver(mesh_payload, pin_node=pin_node)


# -----------------------------------------------------------------------------
# Shared element helpers
# -----------------------------------------------------------------------------


def _triangle_geometry(points: np.ndarray, tri: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray, Tuple[float, float]]:
    """Return area, shape-function gradients, centroid and centroid tuple."""
    xy = points[tri]
    x1, y1 = xy[0]
    x2, y2 = xy[1]
    x3, y3 = xy[2]
    det = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    area = 0.5 * det
    if area <= 0.0:
        # Triangle may be clockwise depending on the mesher. Use positive area
        # and gradients consistent with the signed determinant.
        pass
    A = abs(area)
    if A <= 0.0:
        raise ValueError("Degenerate triangle with zero area.")
    denom = det
    if denom == 0.0:
        raise ValueError("Degenerate triangle with zero determinant.")
    b = np.array([y2 - y3, y3 - y1, y1 - y2], dtype=float) / denom
    c = np.array([x3 - x2, x1 - x3, x2 - x1], dtype=float) / denom
    centroid = np.mean(xy, axis=0)
    return A, b, c, (float(centroid[0]), float(centroid[1]))


def _boundary_nodes_from_triangles(triangles: np.ndarray) -> np.ndarray:
    """Return the sorted node ids lying on the exterior mesh boundary.

    Boundary edges are triangle edges that occur exactly once in the element
    connectivity.  These nodes receive the Prandtl stress-function Dirichlet
    condition phi = 0 for simply connected Saint-Venant torsion.
    """
    edge_count: Dict[Tuple[int, int], int] = {}
    for tri in triangles:
        edges = (
            (int(tri[0]), int(tri[1])),
            (int(tri[1]), int(tri[2])),
            (int(tri[2]), int(tri[0])),
        )
        for a, b in edges:
            key = (a, b) if a < b else (b, a)
            edge_count[key] = edge_count.get(key, 0) + 1

    nodes = sorted({node for edge, count in edge_count.items() if count == 1 for node in edge})
    return np.asarray(nodes, dtype=np.int64)


@register_formulation("prandtl-dirichlet")
def solve_prandtl_dirichlet(mesh_payload: MeshPayload, pin_node: int = 0) -> SolverOutput:
    """
    Solve Saint-Venant torsion with the Prandtl stress function.

    This replaces the earlier warping-field prototype.  The previous prototype
    could collapse to the polar stiffness integral GIp for coarse/symmetric
    meshes; that is not an acceptable torsion result for general sections.

    Formulation used here for unit twist theta = 1:

        div((1 / G) grad(phi)) = -2
        phi = 0 on the external boundary

    Weak form:

        integral_A (1 / G) grad(phi) . grad(v) dA = integral_A 2 v dA

    Post-processing:

        GJ = 2 * integral_A phi dA

    Scope:
    - correct target for simply connected solid/open sections;
    - conservative first implementation for holes because all boundary
      components are set to phi = 0.  General multiply-connected closed cells
      require one unknown constant per inner boundary plus compatibility
      constraints, and should not be silently hidden in this module.

    The pin_node argument is kept for CLI compatibility but is not used by this
    Dirichlet Prandtl solve.
    """
    del pin_node

    points = mesh_payload.points
    triangles = mesh_payload.triangles
    G_elems = mesh_payload.element_G
    n = points.shape[0]

    rows: List[int] = []
    cols: List[int] = []
    data: List[float] = []
    rhs = np.zeros(n, dtype=float)

    for e, tri in enumerate(triangles):
        G = float(G_elems[e])
        if G <= 0.0:
            raise SystemExit(f"Element {e} has non-positive G={G}.")
        A, b, c, _centroid = _triangle_geometry(points, tri)
        ke = (A / G) * (np.outer(b, b) + np.outer(c, c))
        fe = np.full(3, 2.0 * A / 3.0, dtype=float)
        for i_local, i_global in enumerate(tri):
            rhs[int(i_global)] += float(fe[i_local])
            for j_local, j_global in enumerate(tri):
                rows.append(int(i_global))
                cols.append(int(j_global))
                data.append(float(ke[i_local, j_local]))

    K = coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()

    boundary = _boundary_nodes_from_triangles(triangles)
    is_free = np.ones(n, dtype=bool)
    is_free[boundary] = False

    if not np.any(is_free):
        raise SystemExit(
            "Prandtl solve has no interior free nodes. Refine the mesh by reducing --mesh-max-area."
        )

    phi = np.zeros(n, dtype=float)
    Kff = K[is_free][:, is_free]
    rhsf = rhs[is_free]
    phi[is_free] = spsolve(Kff, rhsf)

    gj = 0.0
    polar_upper = 0.0
    area_total = 0.0
    for e, tri in enumerate(triangles):
        G = float(G_elems[e])
        A, _b, _c, (xc, yc) = _triangle_geometry(points, tri)
        phi_mean = float(np.mean(phi[tri]))
        gj += 2.0 * A * phi_mean
        polar_upper += G * A * (xc**2 + yc**2)
        area_total += A

    return SolverOutput(
        gj=float(gj),
        polar_upper_bound=float(polar_upper),
        area=float(area_total),
        field=phi,
    )


def analyse_field_at_z(
    field: Any,
    z: float,
    mesh_max_area: float,
    min_angle: float,
    boundary_precision: int,
    pin_node: int,
    formulation: str,
    debug: bool = False,
) -> TorsionResult:
    """Run the complete CSF YAML -> mesh -> selected torsion FEM pipeline for one station."""
    polygon_inputs = polygon_inputs_from_field(field, float(z))
    mesh_payload = build_mesh(
        polygon_inputs=polygon_inputs,
        mesh_max_area=float(mesh_max_area),
        min_angle=float(min_angle),
        boundary_precision=int(boundary_precision),
        require_shear=True,
    )
    if debug:
        print_mesh_diagnostics(mesh_payload, z=float(z), mesh_max_area=float(mesh_max_area), min_angle=float(min_angle))
    solved = solve_torsion(mesh_payload, formulation=formulation, pin_node=pin_node)
    return TorsionResult(
        z=float(z),
        gj_fem=solved.gj,
        polar_upper_bound=solved.polar_upper_bound,
        area=solved.area,
        nodes=int(mesh_payload.points.shape[0]),
        elements=int(mesh_payload.triangles.shape[0]),
        mesh_max_area=float(mesh_max_area),
        min_angle=float(min_angle),
        formulation=str(formulation),
    )


# -----------------------------------------------------------------------------
# Output helpers and CLI
# -----------------------------------------------------------------------------


def _result_to_row(result: TorsionResult) -> Dict[str, Any]:
    return {
        "z": result.z,
        "GJ_fem": result.gj_fem,
        "GIp_mesh": result.polar_upper_bound,
        "GJ_over_GIp": result.reduction_ratio,
        "area_mesh": result.area,
        "nodes": result.nodes,
        "elements": result.elements,
        "mesh_max_area": result.mesh_max_area,
        "min_angle": result.min_angle,
        "formulation": result.formulation,
    }


def _print_table(results: Sequence[TorsionResult]) -> None:
    header = (
        f"{'z':>14} {'formulation':>20} {'GJ_fem':>18} {'GIp_mesh':>18} {'GJ/GIp':>12} "
        f"{'area':>14} {'nodes':>8} {'elems':>8}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r.z:14.6g} {r.formulation:>20} {r.gj_fem:18.10e} {r.polar_upper_bound:18.10e} "
            f"{r.reduction_ratio:12.6g} {r.area:14.6g} {r.nodes:8d} {r.elements:8d}"
        )


def _write_json(path: Path, results: Sequence[TorsionResult]) -> None:
    payload = [_result_to_row(r) for r in results]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Dedicated CSF YAML -> scikit-fem torsion FEM tool. No CSV input."
    )
    ap.add_argument("--yaml", required=True, type=Path, help="CSF geometry YAML file.")
    ap.add_argument(
        "--z",
        action="append",
        type=float,
        default=None,
        help="One z-station. Can be repeated.",
    )
    ap.add_argument(
        "--z-list",
        type=str,
        default=None,
        help="Comma-separated z-stations, e.g. '0,2.5,5,10'.",
    )
    ap.add_argument(
        "--run-config",
        type=Path,
        default=None,
        help="YAML file containing station_sets. Use with --station-set.",
    )
    ap.add_argument(
        "--station-set",
        type=str,
        default=None,
        help="Name of the station set to read from --run-config.",
    )
    ap.add_argument(
        "--mesh-max-area",
        type=float,
        required=True,
        help="Maximum triangle area passed to Triangle. Required; no default is hidden.",
    )
    ap.add_argument(
        "--min-angle",
        type=float,
        required=True,
        help="Triangle minimum angle in degrees, usually 20 to 30. Required.",
    )
    ap.add_argument(
        "--boundary-precision",
        type=int,
        required=True,
        help="Decimal precision used to merge coincident boundary vertices. Required.",
    )
    ap.add_argument(
        "--formulation",
        required=True,
        choices=available_formulations(),
        help="Torsion FEM formulation to use. Required; no formulation default is hidden.",
    )
    ap.add_argument(
        "--pin-node",
        type=int,
        required=True,
        help="Gauge/pinning node used only by formulations that require a scalar nullspace constraint. Required even when ignored by the selected formulation.",
    )
    ap.add_argument(
        "--debug",
        action="store_true",
        help="Print mesh/material diagnostics before solving.",
    )
    ap.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON output path. No CSV output is produced.",
    )
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    z_values = _parse_z_values(args)
    field = load_yaml(args.yaml)

    results: List[TorsionResult] = []
    for z in z_values:
        result = analyse_field_at_z(
            field=field,
            z=float(z),
            mesh_max_area=float(args.mesh_max_area),
            min_angle=float(args.min_angle),
            boundary_precision=int(args.boundary_precision),
            pin_node=int(args.pin_node),
            formulation=str(args.formulation),
            debug=bool(args.debug),
        )
        results.append(result)

    _print_table(results)
    if args.json_out is not None:
        _write_json(args.json_out, results)
        print(f"\nJSON written to: {args.json_out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

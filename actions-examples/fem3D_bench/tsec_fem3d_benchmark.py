"""
CSF / OpenSees 3D continuum benchmark for the T-section model - v17.

The script has four deliberately separated paths:

1. Read the common CSF representation from YAML.
2. Solve the CSF sectional problem at the comparison station.
3. Build and solve an independent OpenSees 3D SSPbrick continuum model
   from field.section(z), using only CSF runtime geometry/material data.
4. Compare the CSF and 3D fields pointwise at SSPbrick centres.

The OpenSees path never receives stresses, fitted fields, scale factors or
section resultants reconstructed from the CSF solution. The two paths share
only the model representation and the prescribed physical loading.

Paper-oriented comparison diagnostics
--------------------------------------
In addition to spatial stress maps, the script can write a 3 x 3 frequency
figure for the signed pointwise differences CSF - FEM3D. The comparison cells
are divided geometrically into three structural zones: upper flange, web and
lower flange. The three columns contain sigma_zz, tau_x and tau_y.

When the histogram mode is "percent", every component is normalised by the
peak absolute FEM3D value of that component over the complete comparison
section. The same denominator and bin edges are therefore used for all three
zones of a component, so the distributions can be compared directly.

Version-2 preflight and meshing scope
---------------------------------------
Before the CSF potential solve, the script checks polygon boundary noding at
S0, S1 and the comparison station. If a vertex of one polygon lies strictly
inside an edge of another polygon without being represented as a shared edge
node, the script stops with a precise diagnostic. This catches T-junctions such
as a web meeting the middle of a longer flange edge before the potential-FEM
assembler is entered.

The check does not alter, repair or re-mesh the CSF representation.

Version-1 meshing scope retained
--------------------------------
The SSPbrick mesher is intentionally simple and inspectable. It builds a
conforming quadrilateral transverse grid from all polygon x/y boundary tracks,
then connects corresponding grids along z.

For this version, every polygon boundary in every sampled section must be
rectilinear in the global x-y plane: every edge must be parallel to either x
or y. The boundary tracks may move along z, so S0 and S1 may differ.

Nested polygons are handled generically through Polygon.container_idx:

    occupied(parent) = parent - union(children)

A child with zero absolute carriers becomes a void. A child with positive
absolute carriers becomes a material inclusion. No polygon-name special cases
are used.

Material scope
--------------
OpenSees SSPbrick uses ElasticIsotropic. Therefore each active runtime polygon
must satisfy, within numerical tolerance,

    G = E / (2 * (1 + nu))

with

    E  = polygon.weightabs
    G  = polygon.shear_weightabs
    nu = polygon.poisson

The script raises an explicit error for an incompatible carrier triplet rather
than inventing an orthotropic constitutive model.

Expected command
----------------
    python3 tsec_fem3d_benchmark_v17.py tsec_fem3d_settings.yaml
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import csv
import math
import sys

import numpy as np
import yaml

from csf import section_full_analysis
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues
import csf.polygon_stress as polygon_stress_module

try:
    import openseespy.opensees as ops
except ImportError:
    ops = None


# ============================================================
# 0. SMALL I/O / NUMERICAL UTILITIES
# ============================================================

SCRIPT_VERSION = "17"

GEOMETRY_TOL = 1.0e-10
MATERIAL_RTOL = 1.0e-8
MATERIAL_ATOL = 1.0e-12


def require_opensees() -> None:
    if ops is None:
        raise SystemExit(
            "OpenSeesPy is required for this benchmark. "
            "Install it in the active Python environment."
        )


def load_settings(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)

    if not isinstance(data, dict):
        raise ValueError("The settings YAML must contain a mapping at the root.")

    return data


def get_required(mapping: dict, *keys: str):
    value = mapping
    traversed = []

    for key in keys:
        traversed.append(key)

        if not isinstance(value, dict) or key not in value:
            raise KeyError(
                "Missing required settings key: "
                + ".".join(traversed)
            )

        value = value[key]

    return value


def resolve_from_settings(settings_file: Path, value: str) -> Path:
    path = Path(value)

    if path.is_absolute():
        return path

    return settings_file.parent / path


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def normalized_l2_error(
    rows: list[dict[str, object]],
    prediction_key: str,
    reference_key: str,
) -> float:
    numerator = sum(
        float(row["area"])
        * (
            float(row[prediction_key])
            - float(row[reference_key])
        ) ** 2
        for row in rows
    )
    denominator = sum(
        float(row["area"])
        * float(row[reference_key]) ** 2
        for row in rows
    )

    if denominator <= 0.0:
        return float("nan")

    return math.sqrt(numerator / denominator)


def normalized_max_error(
    rows: list[dict[str, object]],
    prediction_key: str,
    reference_key: str,
) -> float:
    numerator = max(
        abs(
            float(row[prediction_key])
            - float(row[reference_key])
        )
        for row in rows
    )
    denominator = max(
        abs(float(row[reference_key]))
        for row in rows
    )

    if denominator <= 0.0:
        return float("nan")

    return numerator / denominator


def normalized_vector_l2_error(
    rows: list[dict[str, object]],
) -> float:
    numerator = sum(
        float(row["area"])
        * (
            (
                float(row["tau_x_csf"])
                - float(row["tau_zx_3d"])
            ) ** 2
            + (
                float(row["tau_y_csf"])
                - float(row["tau_yz_3d"])
            ) ** 2
        )
        for row in rows
    )
    denominator = sum(
        float(row["area"])
        * (
            float(row["tau_zx_3d"]) ** 2
            + float(row["tau_yz_3d"]) ** 2
        )
        for row in rows
    )

    if denominator <= 0.0:
        return float("nan")

    return math.sqrt(numerator / denominator)


def normalized_vector_max_error(
    rows: list[dict[str, object]],
) -> float:
    numerator = max(
        math.hypot(
            float(row["tau_x_csf"])
            - float(row["tau_zx_3d"]),
            float(row["tau_y_csf"])
            - float(row["tau_yz_3d"]),
        )
        for row in rows
    )
    denominator = max(
        math.hypot(
            float(row["tau_zx_3d"]),
            float(row["tau_yz_3d"]),
        )
        for row in rows
    )

    if denominator <= 0.0:
        return float("nan")

    return numerator / denominator


# ============================================================
# 1. READ THE COMMON CSF MODEL
# ============================================================


def read_csf_model(csf_yaml: Path):
    result = CSFReader().read_file(str(csf_yaml))

    if not result.ok or result.field is None:
        raise RuntimeError(
            "CSF model validation failed:\n"
            + CSFIssues.format_report(result.issues)
        )

    return result.field


def validate_polygon_interface_noding(
    section,
    *,
    tolerance: float = 1.0e-10,
) -> None:
    """
    Reject un-noded polygon T-junctions before the potential solver is called.

    A conforming polygon interface requires every boundary vertex that lies on
    another polygon edge to be represented as a vertex of that edge as well.

    The function is intentionally diagnostic only:
    - it does not insert vertices;
    - it does not modify polygon ordering;
    - it does not modify CSF topology;
    - it does not repair geometry.

    This preserves the YAML/CSF representation as the sole source of geometry.
    """

    def same_point(a, b) -> bool:
        return (
            abs(float(a.x) - float(b.x)) <= tolerance
            and abs(float(a.y) - float(b.y)) <= tolerance
        )

    def point_on_segment_interior(point, a, b) -> bool:
        px = float(point.x)
        py = float(point.y)
        ax = float(a.x)
        ay = float(a.y)
        bx = float(b.x)
        by = float(b.y)

        dx = bx - ax
        dy = by - ay
        length2 = dx * dx + dy * dy

        if length2 <= tolerance * tolerance:
            return False

        cross = (px - ax) * dy - (py - ay) * dx
        length = math.sqrt(length2)

        if abs(cross) > tolerance * max(1.0, length):
            return False

        parameter = (
            (px - ax) * dx + (py - ay) * dy
        ) / length2

        parameter_tolerance = tolerance / max(length, 1.0)

        return (
            parameter_tolerance
            < parameter
            < 1.0 - parameter_tolerance
        )

    polygons = section.polygons

    for source_idx, source_polygon in enumerate(polygons):
        for source_vertex_idx, source_vertex in enumerate(
            source_polygon.vertices
        ):
            for target_idx, target_polygon in enumerate(polygons):
                if target_idx == source_idx:
                    continue

                target_vertices = target_polygon.vertices

                for target_edge_idx in range(len(target_vertices)):
                    a = target_vertices[target_edge_idx]
                    b = target_vertices[
                        (target_edge_idx + 1) % len(target_vertices)
                    ]

                    if not point_on_segment_interior(
                        source_vertex,
                        a,
                        b,
                    ):
                        continue

                    if (
                        same_point(source_vertex, a)
                        or same_point(source_vertex, b)
                    ):
                        continue

                    raise RuntimeError(
                        "Un-noded polygon interface detected before the CSF "
                        "local-shear-potential solve. "
                        f"z={float(section.z):.12g}, "
                        f"polygon_idx={source_idx} "
                        f"('{source_polygon.name}'), "
                        f"vertex_idx={source_vertex_idx}, "
                        f"point=({float(source_vertex.x):.12g}, "
                        f"{float(source_vertex.y):.12g}) lies inside "
                        f"polygon_idx={target_idx} "
                        f"('{target_polygon.name}') edge_idx={target_edge_idx} "
                        f"from ({float(a.x):.12g}, {float(a.y):.12g}) "
                        f"to ({float(b.x):.12g}, {float(b.y):.12g}). "
                        "Add the coincident interface point to the target "
                        "polygon vertex list in both S0 and S1. "
                        "No automatic geometry repair is performed."
                    )


def validate_csf_interface_noding(
    field,
    comparison_z: float,
) -> None:
    """
    Check S0, S1 and the actual comparison section.

    Checking S0 and S1 verifies explicit interface noding at both ends of the
    continuous field. The comparison section is checked as the exact geometry
    entering the local potential solve.
    """
    sections = (
        ("S0", field.s0),
        ("S1", field.s1),
        ("comparison", field.section(float(comparison_z))),
    )

    for label, section in sections:
        try:
            validate_polygon_interface_noding(section)
        except RuntimeError as exc:
            raise RuntimeError(
                f"CSF interface-noding preflight failed at {label}: {exc}"
            ) from exc


def beam_actions_simply_supported_udl_y(
    z: float,
    z0: float,
    z1: float,
    q: float,
) -> dict[str, float]:
    """
    Beam-resultant convention used by the CSF path.

    s = z - z0
    L = z1 - z0

    Mx = q * s * (L - s) / 2
    Ty = q * (L/2 - s)
    """
    s = float(z) - float(z0)
    L = float(z1) - float(z0)

    return {
        "N": 0.0,
        "Mx": q * s * (L - s) / 2.0,
        "My": 0.0,
        "Tx": 0.0,
        "Ty": q * (L / 2.0 - s),
    }


# ============================================================
# 2. CSF SECTIONAL SOLUTION
# ============================================================


class PotentialFieldEvaluator:
    """
    Same-point evaluator for the piecewise-constant P1 CSF shear field.

    The CSF potential solver returns one constant (tau_x, tau_y) pair per
    triangle. The evaluator uses a Shapely STRtree and, when requested, filters
    candidates by polygon index so a material interface is never crossed
    accidentally during point evaluation.
    """

    def __init__(self, triangle_rows: list[dict[str, object]]):
        try:
            from shapely.geometry import Point as ShapelyPoint
            from shapely.geometry import Polygon as ShapelyPolygon
            from shapely.strtree import STRtree
        except ImportError as exc:
            raise RuntimeError(
                "Shapely >= 2.1 is required by this benchmark."
            ) from exc

        self._Point = ShapelyPoint

        self._triangles = [
            ShapelyPolygon(
                (
                    (float(row["x0"]), float(row["y0"])),
                    (float(row["x1"]), float(row["y1"])),
                    (float(row["x2"]), float(row["y2"])),
                )
            )
            for row in triangle_rows
        ]

        self._tree = STRtree(self._triangles)
        self._polygon_idx = np.asarray(
            [int(row["polygon_idx"]) for row in triangle_rows],
            dtype=int,
        )
        self._area = np.asarray(
            [float(row["area"]) for row in triangle_rows],
            dtype=float,
        )
        self._tau_x = np.asarray(
            [float(row["tau_x"]) for row in triangle_rows],
            dtype=float,
        )
        self._tau_y = np.asarray(
            [float(row["tau_y"]) for row in triangle_rows],
            dtype=float,
        )

    def evaluate(
        self,
        x: float,
        y: float,
        polygon_idx: int,
    ) -> tuple[float, float, int]:
        point = self._Point(float(x), float(y))

        candidate_indices = np.asarray(
            self._tree.query(
                point,
                predicate="intersects",
            ),
            dtype=int,
        )

        if candidate_indices.size == 0:
            raise RuntimeError(
                "No CSF potential triangle contains point "
                f"({x:.12g}, {y:.12g})."
            )

        candidate_indices = candidate_indices[
            self._polygon_idx[candidate_indices] == int(polygon_idx)
        ]

        if candidate_indices.size == 0:
            raise RuntimeError(
                "CSF potential point found only in a different polygon at "
                f"({x:.12g}, {y:.12g}); requested polygon_idx={polygon_idx}."
            )

        weights = self._area[candidate_indices]
        weight_sum = float(np.sum(weights))

        if weight_sum <= 0.0:
            raise RuntimeError("Invalid CSF potential triangle areas.")

        tau_x = float(
            np.sum(
                weights * self._tau_x[candidate_indices]
            ) / weight_sum
        )
        tau_y = float(
            np.sum(
                weights * self._tau_y[candidate_indices]
            ) / weight_sum
        )

        return tau_x, tau_y, int(candidate_indices.size)


def solve_csf_path(
    field,
    comparison_z: float,
    actions: dict[str, float],
    dz_relative: float,
    mesh_refinements: int,
    compatibility_rtol: float,
    compatibility_atol: float,
) -> dict[str, object]:
    z0 = float(field.s0.z)
    z1 = float(field.s1.z)
    length = z1 - z0

    dz = abs(length) * float(dz_relative)

    if dz <= 0.0:
        raise ValueError("csf.local_shear_potential.dz_relative must be > 0.")

    potential = polygon_stress_module.analyse_navier_local_shear_potential(
        section_field=field,
        z=float(comparison_z),
        N=float(actions["N"]),
        Mx=float(actions["Mx"]),
        My=float(actions["My"]),
        Tx=float(actions["Tx"]),
        Ty=float(actions["Ty"]),
        dN_dz=0.0,
        dz=dz,
        mesh_refinements=int(mesh_refinements),
        plot_mesh=False,
        validation_points=None,
        compatibility_rtol=float(compatibility_rtol),
        compatibility_atol=float(compatibility_atol),
    )

    navier_state = polygon_stress_module._navier_section_state(
        section_field=field,
        z=float(comparison_z),
        N=float(actions["N"]),
        Mx=float(actions["Mx"]),
        My=float(actions["My"]),
    )

    return {
        "potential": potential,
        "potential_evaluator": PotentialFieldEvaluator(
            potential["triangles"]
        ),
        "navier_state": navier_state,
    }


def evaluate_csf_sigma_zz(
    navier_state: dict[str, object],
    polygon,
    x: float,
    y: float,
) -> float:
    """
    Evaluate the same Navier point equation used internally by polygon_stress.py.

    No OpenSees quantity enters this evaluation.
    """
    return float(
        polygon_stress_module._navier_sigma_at_point(
            poly=polygon,
            x=float(x),
            y=float(y),
            state=navier_state,
        )
    )


# ============================================================
# 3. THREE-DIMENSIONAL FEM SOLUTION
# ============================================================


def unique_sorted(values: list[float]) -> list[float]:
    values = sorted(float(value) for value in values)
    result: list[float] = []

    for value in values:
        if not result or abs(value - result[-1]) > GEOMETRY_TOL:
            result.append(value)

    return result


def section_coarse_levels(section, axis: str) -> list[float]:
    if axis == "x":
        return unique_sorted(
            [
                float(vertex.x)
                for polygon in section.polygons
                for vertex in polygon.vertices
            ]
        )

    if axis == "y":
        return unique_sorted(
            [
                float(vertex.y)
                for polygon in section.polygons
                for vertex in polygon.vertices
            ]
        )

    raise ValueError(f"Unsupported axis: {axis}")


def validate_rectilinear_section(section) -> None:
    for polygon_idx, polygon in enumerate(section.polygons):
        vertices = polygon.vertices

        for edge_idx in range(len(vertices)):
            p0 = vertices[edge_idx]
            p1 = vertices[(edge_idx + 1) % len(vertices)]

            dx = abs(float(p1.x) - float(p0.x))
            dy = abs(float(p1.y) - float(p0.y))

            if dx > GEOMETRY_TOL and dy > GEOMETRY_TOL:
                raise NotImplementedError(
                    "Version 1 SSPbrick mesher requires rectilinear polygon "
                    "edges in every transverse section. "
                    f"polygon_idx={polygon_idx}, edge_idx={edge_idx}, "
                    f"z={float(section.z):.12g}."
                )


def build_axis_template(
    section0,
    section1,
    axis: str,
    target_size: float,
) -> tuple[list[int], int]:
    levels0 = section_coarse_levels(section0, axis)
    levels1 = section_coarse_levels(section1, axis)

    if len(levels0) != len(levels1):
        raise NotImplementedError(
            f"Version 1 requires stable {axis}-boundary-track topology "
            "between S0 and S1."
        )

    if len(levels0) < 2:
        raise ValueError(
            f"At least two distinct {axis} coordinates are required."
        )

    subdivisions: list[int] = []

    for idx in range(len(levels0) - 1):
        width0 = levels0[idx + 1] - levels0[idx]
        width1 = levels1[idx + 1] - levels1[idx]

        if width0 <= GEOMETRY_TOL or width1 <= GEOMETRY_TOL:
            raise NotImplementedError(
                f"Version 1 requires stable ordered {axis} tracks."
            )

        width = max(width0, width1)
        subdivisions.append(
            max(1, int(math.ceil(width / target_size)))
        )

    return subdivisions, len(levels0)


def refined_axis(
    section,
    axis: str,
    subdivisions: list[int],
    expected_coarse_count: int,
) -> np.ndarray:
    coarse = section_coarse_levels(section, axis)

    if len(coarse) != expected_coarse_count:
        raise NotImplementedError(
            f"The number of {axis} boundary tracks changes at z={section.z}."
        )

    values: list[float] = []

    for idx, count in enumerate(subdivisions):
        interval = np.linspace(
            coarse[idx],
            coarse[idx + 1],
            int(count) + 1,
        )

        if idx > 0:
            interval = interval[1:]

        values.extend(float(value) for value in interval)

    return np.asarray(values, dtype=float)


def polygon_depths(section) -> list[int]:
    depths: list[int] = []

    for polygon_idx, polygon in enumerate(section.polygons):
        seen: set[int] = set()
        parent = polygon.container_idx
        depth = 0

        while parent is not None:
            parent = int(parent)

            if parent in seen:
                raise ValueError(
                    "Cycle detected in polygon container topology."
                )

            if not (0 <= parent < len(section.polygons)):
                raise ValueError(
                    f"Invalid container_idx={parent} "
                    f"for polygon_idx={polygon_idx}."
                )

            seen.add(parent)
            depth += 1
            parent = section.polygons[parent].container_idx

        depths.append(depth)

    return depths


def build_polygon_geometries(section):
    try:
        from shapely.geometry import Point as ShapelyPoint
        from shapely.geometry import Polygon as ShapelyPolygon
    except ImportError as exc:
        raise RuntimeError(
            "Shapely >= 2.1 is required by this benchmark."
        ) from exc

    geometries = [
        ShapelyPolygon(
            [(float(p.x), float(p.y)) for p in polygon.vertices]
        )
        for polygon in section.polygons
    ]

    return ShapelyPoint, geometries


def classify_point(
    section,
    point_factory,
    polygon_geometries,
    depths: list[int],
    x: float,
    y: float,
) -> int | None:
    point = point_factory(float(x), float(y))

    candidates = [
        idx
        for idx, geometry in enumerate(polygon_geometries)
        if geometry.covers(point)
    ]

    if not candidates:
        return None

    max_depth = max(depths[idx] for idx in candidates)
    deepest = [
        idx
        for idx in candidates
        if depths[idx] == max_depth
    ]

    if len(deepest) != 1:
        raise ValueError(
            "Ambiguous overlapping polygon regions at "
            f"({x:.12g}, {y:.12g}), z={section.z}: {deepest}"
        )

    return int(deepest[0])


def isotropic_material_values(
    polygon,
    polygon_idx: int,
    z: float,
) -> tuple[float, float, float] | None:
    E = float(polygon.weightabs)
    G = float(polygon.shear_weightabs)
    nu = float(polygon.poisson)

    if (
        abs(E) <= MATERIAL_ATOL
        and abs(G) <= MATERIAL_ATOL
    ):
        return None

    if not (
        math.isfinite(E)
        and math.isfinite(G)
        and math.isfinite(nu)
    ):
        raise ValueError(
            f"Non-finite material data for polygon_idx={polygon_idx} "
            f"at z={z:.12g}."
        )

    if E <= 0.0 or G <= 0.0:
        raise ValueError(
            "An active OpenSees material requires positive absolute carriers: "
            f"polygon_idx={polygon_idx}, z={z:.12g}, E={E}, G={G}."
        )

    if not (-1.0 < nu < 0.5):
        raise ValueError(
            f"Invalid isotropic Poisson ratio for polygon_idx={polygon_idx}: "
            f"nu={nu}."
        )

    G_from_E_nu = E / (2.0 * (1.0 + nu))

    if not math.isclose(
        G,
        G_from_E_nu,
        rel_tol=MATERIAL_RTOL,
        abs_tol=MATERIAL_ATOL,
    ):
        raise NotImplementedError(
            "Version 1 OpenSees path uses ElasticIsotropic and therefore "
            "cannot represent independent E/G carriers. "
            f"polygon_idx={polygon_idx}, z={z:.12g}, "
            f"weightabs={E:.12e}, shear_weightabs={G:.12e}, "
            f"poisson={nu:.12e}, isotropic_G={G_from_E_nu:.12e}."
        )

    return E, G, nu


def cell_area_from_mid_grid(
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    i: int,
    j: int,
) -> float:
    return float(
        (x_grid[i + 1] - x_grid[i])
        * (y_grid[j + 1] - y_grid[j])
    )


def plot_comparison_section_mesh(
    output_file: Path,
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    cell_polygon: dict[tuple[int, int], int],
    comparison_z: float,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 7.0))

    for (j, i), polygon_idx in cell_polygon.items():
        x0 = float(x_grid[i])
        x1 = float(x_grid[i + 1])
        y0 = float(y_grid[j])
        y1 = float(y_grid[j + 1])

        ax.plot(
            [x0, x1, x1, x0, x0],
            [y0, y0, y1, y1, y0],
            linewidth=0.5,
        )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(
        f"OpenSees SSPbrick transverse mesh at z = {comparison_z:.6g} m"
    )
    ax.grid(False)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close(fig)


def run_fem3d_path(
    field,
    z0: float,
    z1: float,
    comparison_z: float,
    comparison_t: float,
    q: float,
    load_projection_polygon: str,
    nz: int,
    target_size_xy: float,
    system_name: str,
    algorithm_name: str,
    section_jpg: Path,
) -> dict[str, object]:
    require_opensees()

    if nz < 1:
        raise ValueError("fem3d.mesh.nz must be >= 1.")

    if target_size_xy <= 0.0:
        raise ValueError("fem3d.mesh.target_size_xy must be > 0.")

    selected_k_float = float(comparison_t) * nz - 0.5
    selected_k = int(round(selected_k_float))

    if (
        selected_k < 0
        or selected_k >= nz
        or abs(selected_k_float - selected_k) > 1.0e-10
    ):
        raise ValueError(
            "comparison_t must coincide with an SSPbrick layer centre: "
            "(k + 0.5) / nz. "
            f"comparison_t={comparison_t}, nz={nz}."
        )

    length = z1 - z0

    # Cache every section required by the 3D discretization exactly once.
    node_sections = [
        field.section(
            z0 + length * k / nz
        )
        for k in range(nz + 1)
    ]
    mid_sections = [
        field.section(
            z0 + length * (k + 0.5) / nz
        )
        for k in range(nz)
    ]

    for section in node_sections:
        validate_rectilinear_section(section)

    for section in mid_sections:
        validate_rectilinear_section(section)

    x_subdivisions, x_coarse_count = build_axis_template(
        node_sections[0],
        node_sections[-1],
        "x",
        target_size_xy,
    )
    y_subdivisions, y_coarse_count = build_axis_template(
        node_sections[0],
        node_sections[-1],
        "y",
        target_size_xy,
    )

    x_node_grids = [
        refined_axis(
            section,
            "x",
            x_subdivisions,
            x_coarse_count,
        )
        for section in node_sections
    ]
    y_node_grids = [
        refined_axis(
            section,
            "y",
            y_subdivisions,
            y_coarse_count,
        )
        for section in node_sections
    ]
    x_mid_grids = [
        refined_axis(
            section,
            "x",
            x_subdivisions,
            x_coarse_count,
        )
        for section in mid_sections
    ]
    y_mid_grids = [
        refined_axis(
            section,
            "y",
            y_subdivisions,
            y_coarse_count,
        )
        for section in mid_sections
    ]

    nx = len(x_node_grids[0]) - 1
    ny = len(y_node_grids[0]) - 1

    if nx < 1 or ny < 1:
        raise RuntimeError("The transverse FEM grid is empty.")

    for grid in x_node_grids + x_mid_grids:
        if len(grid) != nx + 1:
            raise NotImplementedError(
                "x-grid topology changes along z."
            )

    for grid in y_node_grids + y_mid_grids:
        if len(grid) != ny + 1:
            raise NotImplementedError(
                "y-grid topology changes along z."
            )

    # Classify every transverse cell independently at every longitudinal
    # layer centre. container_idx supplies the resolved material replacement.
    cell_polygon_by_k: list[dict[tuple[int, int], int]] = []
    material_values_by_k_polygon: list[
        dict[int, tuple[float, float, float] | None]
    ] = []

    for k, section in enumerate(mid_sections):
        point_factory, geometries = build_polygon_geometries(section)
        depths = polygon_depths(section)

        x_mid_grid = x_mid_grids[k]
        y_mid_grid = y_mid_grids[k]

        cell_polygon: dict[tuple[int, int], int] = {}

        for j in range(ny):
            y_cell = 0.5 * (
                y_mid_grid[j] + y_mid_grid[j + 1]
            )

            for i in range(nx):
                x_cell = 0.5 * (
                    x_mid_grid[i] + x_mid_grid[i + 1]
                )

                polygon_idx = classify_point(
                    section,
                    point_factory,
                    geometries,
                    depths,
                    x_cell,
                    y_cell,
                )

                if polygon_idx is None:
                    continue

                material = isotropic_material_values(
                    section.polygons[polygon_idx],
                    polygon_idx,
                    float(section.z),
                )

                if material is None:
                    # True void: the parent has already been punched by the
                    # deepest-region classification, and no child brick is made.
                    continue

                cell_polygon[(j, i)] = polygon_idx

        if not cell_polygon:
            raise RuntimeError(
                f"No active FEM cells at z={float(section.z):.12g}."
            )

        cell_polygon_by_k.append(cell_polygon)

        used_polygon_indices = sorted(set(cell_polygon.values()))
        material_values_by_k_polygon.append(
            {
                polygon_idx: isotropic_material_values(
                    section.polygons[polygon_idx],
                    polygon_idx,
                    float(section.z),
                )
                for polygon_idx in used_polygon_indices
            }
        )

    selected_section = mid_sections[selected_k]
    selected_x_grid = x_mid_grids[selected_k]
    selected_y_grid = y_mid_grids[selected_k]
    selected_cell_polygon = cell_polygon_by_k[selected_k]

    plot_comparison_section_mesh(
        section_jpg,
        selected_x_grid,
        selected_y_grid,
        selected_cell_polygon,
        comparison_z,
    )

    ops.wipe()
    ops.model(
        "basic",
        "-ndm", 3,
        "-ndf", 3,
    )

    # One OpenSees material per layer/polygon is sufficient. All bricks in
    # that layer and physical region share the same sampled CSF properties.
    material_tag_by_k_polygon: dict[tuple[int, int], int] = {}
    next_material_tag = 1

    for k in range(nz):
        for polygon_idx, material in (
            material_values_by_k_polygon[k].items()
        ):
            if material is None:
                continue

            E, G, nu = material

            material_tag_by_k_polygon[(k, polygon_idx)] = (
                next_material_tag
            )

            ops.nDMaterial(
                "ElasticIsotropic",
                next_material_tag,
                E,
                nu,
                0.0,
            )

            next_material_tag += 1

    # Create only nodes that belong to at least one active SSPbrick.
    needed_nodes: set[tuple[int, int, int]] = set()

    for k, cell_polygon in enumerate(cell_polygon_by_k):
        for j, i in cell_polygon:
            for kk in (k, k + 1):
                needed_nodes.update(
                    {
                        (kk, j, i),
                        (kk, j, i + 1),
                        (kk, j + 1, i + 1),
                        (kk, j + 1, i),
                    }
                )

    node_tag_by_index: dict[tuple[int, int, int], int] = {}
    node_coordinates: dict[int, tuple[float, float, float]] = {}

    next_node_tag = 1

    for k in range(nz + 1):
        z_node = z0 + length * k / nz
        x_grid = x_node_grids[k]
        y_grid = y_node_grids[k]

        layer_indices = sorted(
            index
            for index in needed_nodes
            if index[0] == k
        )

        for _, j, i in layer_indices:
            tag = next_node_tag
            x = float(x_grid[i])
            y = float(y_grid[j])

            ops.node(
                tag,
                x,
                y,
                z_node,
            )

            node_tag_by_index[(k, j, i)] = tag
            node_coordinates[tag] = (x, y, z_node)
            next_node_tag += 1

    selected_metadata: dict[int, dict[str, object]] = {}
    brick_element_tags: list[int] = []
    next_element_tag = 1

    for k in range(nz):
        x_mid_grid = x_mid_grids[k]
        y_mid_grid = y_mid_grids[k]
        z_mid = float(mid_sections[k].z)

        for (j, i), polygon_idx in sorted(
            cell_polygon_by_k[k].items()
        ):
            n1 = node_tag_by_index[(k,     j,     i)]
            n2 = node_tag_by_index[(k,     j,     i + 1)]
            n3 = node_tag_by_index[(k,     j + 1, i + 1)]
            n4 = node_tag_by_index[(k,     j + 1, i)]
            n5 = node_tag_by_index[(k + 1, j,     i)]
            n6 = node_tag_by_index[(k + 1, j,     i + 1)]
            n7 = node_tag_by_index[(k + 1, j + 1, i + 1)]
            n8 = node_tag_by_index[(k + 1, j + 1, i)]

            material_tag = material_tag_by_k_polygon[
                (k, polygon_idx)
            ]

            ops.element(
                "SSPbrick",
                next_element_tag,
                n1, n2, n3, n4,
                n5, n6, n7, n8,
                material_tag,
                0.0, 0.0, 0.0,
            )

            brick_element_tags.append(next_element_tag)

            if k == selected_k:
                x0 = float(x_mid_grid[i])
                x1 = float(x_mid_grid[i + 1])
                y0 = float(y_mid_grid[j])
                y1 = float(y_mid_grid[j + 1])
                polygon = selected_section.polygons[polygon_idx]

                selected_metadata[next_element_tag] = {
                    "element_tag": next_element_tag,
                    "polygon_idx": polygon_idx,
                    "polygon_name": str(polygon.name),
                    "container_idx": (
                        ""
                        if polygon.container_idx is None
                        else int(polygon.container_idx)
                    ),
                    "material_tag": material_tag,
                    "weightabs": float(polygon.weightabs),
                    "shear_weightabs": float(
                        polygon.shear_weightabs
                    ),
                    "poisson": float(polygon.poisson),
                    "i": i,
                    "j": j,
                    "k": k,
                    "x": 0.5 * (x0 + x1),
                    "y": 0.5 * (y0 + y1),
                    "z": z_mid,
                    "area": cell_area_from_mid_grid(
                        x_mid_grid,
                        y_mid_grid,
                        i,
                        j,
                    ),
                    "x0": x0,
                    "x1": x1,
                    "y0": y0,
                    "y1": y1,
                }

            next_element_tag += 1

    if not selected_metadata:
        raise RuntimeError(
            "No SSPbrick elements found at the comparison station."
        )

    # ------------------------------------------------------------
    # Simply-supported continuum constraints.
    #
    # Point supports are placed at the base of the web, consistently with the
    # CSF beam support line. A six-scalar 3-2-1 pattern removes the rigid-body
    # modes without constraining either complete end section or a longitudinal
    # x-track through the solid:
    #
    #   A, z=0, base of web : ux = uy = uz = 0
    #   B, z=L, base of web : ux = uy      = 0
    #   C, z=0, upper point : ux           = 0
    #
    # A and B are the two vertical simple supports. C only suppresses the
    # remaining rigid-body mode in the transverse x direction.
    # ------------------------------------------------------------

    left_support_nodes = [
        tag
        for (k, j, i), tag in node_tag_by_index.items()
        if k == 0
    ]
    right_support_nodes = [
        tag
        for (k, j, i), tag in node_tag_by_index.items()
        if k == nz
    ]

    support_i = int(
        np.argmin(
            np.abs(x_node_grids[0])
        )
    )

    support_keys = {
        "A": (0, 0, support_i),
        "B": (nz, 0, support_i),
        "C": (0, ny, support_i),
    }

    missing_supports = {
        name: key
        for name, key in support_keys.items()
        if key not in node_tag_by_index
    }
    if missing_supports:
        raise RuntimeError(
            "Could not construct the point-support pattern at the web "
            f"centreline: {missing_supports}."
        )

    support_A = node_tag_by_index[support_keys["A"]]
    support_B = node_tag_by_index[support_keys["B"]]
    support_C = node_tag_by_index[support_keys["C"]]

    ops.fix(support_A, 1, 1, 1)
    ops.fix(support_B, 1, 1, 0)
    ops.fix(support_C, 1, 0, 0)

    # ------------------------------------------------------------
    # Global-y UDL mapped to the upper exposed faces above a selected CSF
    # polygon.
    #
    # The physical line load q is unchanged. At each longitudinal layer, the
    # selected CSF polygon defines the x-range of the loaded strip. Each loaded
    # face receives the fraction q * dz * dx / loaded_width of the layer load,
    # distributed equally to its four corner nodes. Every applied nodal force
    # is parallel to the global y axis, independently of the local surface
    # inclination. Therefore the FEM3D load has no spurious global-z component.
    # ------------------------------------------------------------

    def projection_polygon_at(section, requested_name: str):
        matches = []

        for polygon_idx, polygon in enumerate(section.polygons):
            runtime_name = str(polygon.name)
            name_tokens = tuple(
                token.strip()
                for token in runtime_name.split(":")
                if token.strip()
            )

            if (
                runtime_name == requested_name
                or requested_name in name_tokens
            ):
                matches.append((polygon_idx, polygon))

        if len(matches) != 1:
            raise RuntimeError(
                "Load-projection polygon must identify exactly one runtime "
                f"polygon; requested '{requested_name}', matches={len(matches)}."
            )

        return matches[0]

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    loaded_face_count = 0

    for k in range(nz):
        cell_polygon = cell_polygon_by_k[k]
        x_mid_grid = x_mid_grids[k]
        load_section = mid_sections[k]

        _, load_polygon = projection_polygon_at(
            load_section,
            load_projection_polygon,
        )
        load_x = [float(vertex.x) for vertex in load_polygon.vertices]
        load_x_min = min(load_x)
        load_x_max = max(load_x)
        load_tolerance = max(
            GEOMETRY_TOL,
            1.0e-10 * max(1.0, abs(load_x_min), abs(load_x_max)),
        )

        top_cells = [
            (j, i)
            for (j, i) in cell_polygon
            if (j + 1, i) not in cell_polygon
        ]

        loaded_cells = [
            (j, i)
            for j, i in top_cells
            if (
                float(x_mid_grid[i]) >= load_x_min - load_tolerance
                and float(x_mid_grid[i + 1]) <= load_x_max + load_tolerance
            )
        ]

        loaded_width = sum(
            float(x_mid_grid[i + 1] - x_mid_grid[i])
            for j, i in loaded_cells
        )

        if loaded_width <= 0.0:
            raise RuntimeError(
                "No upward-facing cells found inside the load projection of "
                f"polygon '{load_projection_polygon}' at layer k={k}."
            )

        dz_layer = float(length) / float(nz)

        for j, i in loaded_cells:
            try:
                s1 = node_tag_by_index[(k,     j + 1, i)]
                s2 = node_tag_by_index[(k + 1, j + 1, i)]
                s3 = node_tag_by_index[(k + 1, j + 1, i + 1)]
                s4 = node_tag_by_index[(k,     j + 1, i + 1)]
            except KeyError as exc:
                raise RuntimeError(
                    "Top surface is not conforming between adjacent "
                    "longitudinal layers."
                ) from exc

            dx = float(x_mid_grid[i + 1] - x_mid_grid[i])
            face_force_y = float(q) * dz_layer * dx / loaded_width
            nodal_force_y = face_force_y / 4.0

            for node_tag in (s1, s2, s3, s4):
                ops.load(
                    node_tag,
                    0.0,
                    nodal_force_y,
                    0.0,
                )

            loaded_face_count += 1

    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system(str(system_name))
    ops.integrator("LoadControl", 1.0)
    ops.algorithm(str(algorithm_name))
    ops.analysis("Static")

    analysis_code = ops.analyze(1)

    if analysis_code != 0:
        raise RuntimeError(
            "OpenSees static analysis failed with code "
            f"{analysis_code}."
        )

    ops.reactions()

    left_reaction_y = sum(
        float(ops.nodeReaction(tag, 2))
        for tag in left_support_nodes
    )
    right_reaction_y = sum(
        float(ops.nodeReaction(tag, 2))
        for tag in right_support_nodes
    )
    total_reaction_y = left_reaction_y + right_reaction_y

    # Extract the six SSPbrick stress components at the comparison layer.
    # Ordering for SSPbrick / ElasticIsotropic:
    # [sigma_xx, sigma_yy, sigma_zz, tau_xy, tau_yz, tau_zx]
    fem_rows: list[dict[str, object]] = []

    for element_tag, metadata in selected_metadata.items():
        stress = tuple(
            float(value)
            for value in ops.eleResponse(
                int(element_tag),
                "stress",
            )
        )

        if len(stress) != 6:
            raise RuntimeError(
                f"SSPbrick {element_tag} returned "
                f"{len(stress)} stress components; six were expected."
            )

        fem_rows.append(
            {
                **metadata,
                "sigma_xx_3d": stress[0],
                "sigma_yy_3d": stress[1],
                "sigma_zz_3d": stress[2],
                "tau_xy_3d": stress[3],
                "tau_yz_3d": stress[4],
                "tau_zx_3d": stress[5],
            }
        )

    return {
        "selected_k": selected_k,
        "nz": nz,
        "target_size_xy": target_size_xy,
        "selected_section": selected_section,
        "fem_rows": fem_rows,
        "node_count": len(node_tag_by_index),
        "brick_element_count": len(brick_element_tags),
        "loaded_face_count": loaded_face_count,
        "material_count": len(material_tag_by_k_polygon),
        "nx": nx,
        "ny": ny,
        "left_reaction_y": left_reaction_y,
        "right_reaction_y": right_reaction_y,
        "total_reaction_y": total_reaction_y,
        "selected_cell_polygon": selected_cell_polygon,
        "selected_x_grid": selected_x_grid,
        "selected_y_grid": selected_y_grid,
    }


# ============================================================
# 4. CSF / FEM 3D COMPARISON
# ============================================================


def reconstruct_fem3d_resultants(
    fem_rows: list[dict[str, object]],
    section_analysis: dict[str, object],
) -> dict[str, float]:
    Cx = float(section_analysis["Cx"])
    Cy = float(section_analysis["Cy"])

    N = sum(
        float(row["area"]) * float(row["sigma_zz_3d"])
        for row in fem_rows
    )
    Mx = sum(
        float(row["area"])
        * float(row["sigma_zz_3d"])
        * (float(row["y"]) - Cy)
        for row in fem_rows
    )
    My = sum(
        float(row["area"])
        * float(row["sigma_zz_3d"])
        * (float(row["x"]) - Cx)
        for row in fem_rows
    )
    Tx = sum(
        float(row["area"]) * float(row["tau_zx_3d"])
        for row in fem_rows
    )
    Ty = sum(
        float(row["area"]) * float(row["tau_yz_3d"])
        for row in fem_rows
    )

    return {
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
    }


def build_pointwise_comparison(
    csf_path: dict[str, object],
    fem_rows: list[dict[str, object]],
    selected_section,
) -> list[dict[str, object]]:
    evaluator: PotentialFieldEvaluator = csf_path[
        "potential_evaluator"
    ]
    navier_state = csf_path["navier_state"]

    rows: list[dict[str, object]] = []

    for fem_row in fem_rows:
        polygon_idx = int(fem_row["polygon_idx"])
        x = float(fem_row["x"])
        y = float(fem_row["y"])

        sigma_zz_csf = evaluate_csf_sigma_zz(
            navier_state,
            selected_section.polygons[polygon_idx],
            x,
            y,
        )
        tau_x_csf, tau_y_csf, triangle_hits = evaluator.evaluate(
            x,
            y,
            polygon_idx,
        )

        rows.append(
            {
                **fem_row,
                "sigma_zz_csf": sigma_zz_csf,
                "tau_x_csf": tau_x_csf,
                "tau_y_csf": tau_y_csf,
                "potential_triangle_hits": triangle_hits,
                "sigma_zz_error": (
                    sigma_zz_csf
                    - float(fem_row["sigma_zz_3d"])
                ),
                "tau_x_error": (
                    tau_x_csf
                    - float(fem_row["tau_zx_3d"])
                ),
                "tau_y_error": (
                    tau_y_csf
                    - float(fem_row["tau_yz_3d"])
                ),
            }
        )

    return rows


def comparison_metrics(
    rows: list[dict[str, object]],
) -> dict[str, float]:
    return {
        "sigma_zz_rel_l2": normalized_l2_error(
            rows,
            "sigma_zz_csf",
            "sigma_zz_3d",
        ),
        "sigma_zz_rel_max": normalized_max_error(
            rows,
            "sigma_zz_csf",
            "sigma_zz_3d",
        ),
        "tau_x_rel_l2": normalized_l2_error(
            rows,
            "tau_x_csf",
            "tau_zx_3d",
        ),
        "tau_x_rel_max": normalized_max_error(
            rows,
            "tau_x_csf",
            "tau_zx_3d",
        ),
        "tau_y_rel_l2": normalized_l2_error(
            rows,
            "tau_y_csf",
            "tau_yz_3d",
        ),
        "tau_y_rel_max": normalized_max_error(
            rows,
            "tau_y_csf",
            "tau_yz_3d",
        ),
        "tau_vector_rel_l2": normalized_vector_l2_error(rows),
        "tau_vector_rel_max": normalized_vector_max_error(rows),
    }



def plot_pointwise_difference_map(
    path: Path,
    rows: list[dict[str, object]],
    comparison_z: float,
    mode: str = "absolute",
) -> None:
    """
    Plot CSF - FEM3D pointwise stress differences on the FEM cell geometry.

    The map uses the exact transverse rectangles associated with the SSPbrick
    centres used by build_pointwise_comparison(). No spatial interpolation is
    introduced.

    Three fields are shown:
        delta_sigma_zz = sigma_zz_csf - sigma_zz_3d
        delta_tau_x    = tau_x_csf    - tau_zx_3d
        delta_tau_y    = tau_y_csf    - tau_yz_3d

    mode="absolute"
        Display absolute differences in MPa.

    mode="percent"
        Display globally normalised differences in percent, using the peak
        absolute FEM3D value of each component over the whole comparison
        section:

            100 * (CSF - FEM3D) / max_A(|FEM3D|)
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.collections import PatchCollection
        from matplotlib.colors import TwoSlopeNorm
        from matplotlib.patches import Rectangle
    except ImportError as exc:
        raise RuntimeError(
            "Matplotlib is required to write the CSF/FEM3D difference map."
        ) from exc

    if not rows:
        raise ValueError(
            "Cannot plot the CSF/FEM3D difference map from an empty point set."
        )

    mode = str(mode).strip().lower()

    if mode not in ("absolute", "percent"):
        raise ValueError(
            "difference_map_mode must be either 'absolute' or 'percent'."
        )

    fields = (
        ("sigma_zz_error", "sigma_zz_3d", r"$\Delta\sigma_{zz}$"),
        ("tau_x_error", "tau_zx_3d", r"$\Delta\tau_x$"),
        ("tau_y_error", "tau_yz_3d", r"$\Delta\tau_y$"),
    )

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(12.0, 5.2),
        constrained_layout=True,
    )

    for ax, (error_key, reference_key, title) in zip(axes, fields):
        patches = []

        for row in rows:
            x0 = float(row["x0"])
            x1 = float(row["x1"])
            y0 = float(row["y0"])
            y1 = float(row["y1"])

            patches.append(
                Rectangle(
                    (x0, y0),
                    x1 - x0,
                    y1 - y0,
                )
            )

        if mode == "absolute":
            values = np.asarray(
                [float(row[error_key]) / 1.0e6 for row in rows],
                dtype=float,
            )
            title_suffix = "  [MPa]"
            colorbar_label = "CSF - FEM3D [MPa]"
        else:
            references = np.asarray(
                [float(row[reference_key]) for row in rows],
                dtype=float,
            )
            field_max_abs_reference = float(np.max(np.abs(references)))
            denominator = max(1.0e-12, field_max_abs_reference)
            values = np.asarray(
                [100.0 * float(row[error_key]) / denominator for row in rows],
                dtype=float,
            )
            title_suffix = "  [% of FEM3D peak]"
            colorbar_label = "100 · (CSF - FEM3D) / max_A(|FEM3D|) [%]"

        maximum = float(np.max(np.abs(values)))
        if maximum <= 0.0:
            maximum = 1.0

        collection = PatchCollection(
            patches,
            cmap="coolwarm",
            norm=TwoSlopeNorm(
                vmin=-maximum,
                vcenter=0.0,
                vmax=maximum,
            ),
            edgecolor="none",
        )
        collection.set_array(values)

        ax.add_collection(collection)
        ax.autoscale_view()
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.set_title(title + title_suffix)

        colorbar = fig.colorbar(
            collection,
            ax=ax,
            orientation="vertical",
            shrink=0.84,
        )
        colorbar.set_label(colorbar_label)

    mode_label = "percentage of FEM3D peak" if mode == "percent" else "absolute"
    fig.suptitle(
        "CSF - FEM3D pointwise stress differences "
        f"({mode_label}) at z={float(comparison_z):.6g} m"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)


def plot_pointwise_stress_maps(
    path: Path,
    rows: list[dict[str, object]],
    comparison_z: float,
) -> None:
    """
    Plot CSF and FEM3D stresses on the common FEM3D comparison-cell mesh.

    The CSF values in this figure are the pointwise CSF evaluations already
    stored in ``rows`` at the SSPbrick centres. This is therefore the direct
    same-point visual counterpart of the numerical comparison metrics.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.collections import PatchCollection
        from matplotlib.colors import Normalize, TwoSlopeNorm
        from matplotlib.patches import Rectangle
    except ImportError as exc:
        raise RuntimeError(
            "Matplotlib is required to write the pointwise stress maps."
        ) from exc

    if not rows:
        raise ValueError("Cannot plot pointwise stress maps from an empty set.")

    fields = (
        ("sigma_zz_csf", "sigma_zz_3d", r"$\sigma_{zz}$"),
        ("tau_x_csf", "tau_zx_3d", r"$\tau_x$ / $\tau_{zx}$"),
        ("tau_y_csf", "tau_yz_3d", r"$\tau_y$ / $\tau_{yz}$"),
    )

    patches = [
        Rectangle(
            (float(row["x0"]), float(row["y0"])),
            float(row["x1"]) - float(row["x0"]),
            float(row["y1"]) - float(row["y0"]),
        )
        for row in rows
    ]

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(13.2, 9.4),
        constrained_layout=True,
    )

    for col, (csf_key, fem_key, title) in enumerate(fields):
        csf_values = np.asarray(
            [float(row[csf_key]) / 1.0e6 for row in rows],
            dtype=float,
        )
        fem_values = np.asarray(
            [float(row[fem_key]) / 1.0e6 for row in rows],
            dtype=float,
        )
        combined = np.concatenate((csf_values, fem_values))

        if np.any(combined < 0.0) and np.any(combined > 0.0):
            limit = float(np.max(np.abs(combined)))
            if limit <= 0.0:
                limit = 1.0
            norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)
            cmap = "coolwarm"
        else:
            vmin = min(0.0, float(np.min(combined)))
            vmax = float(np.max(combined))
            if vmax <= vmin:
                vmax = vmin + 1.0
            norm = Normalize(vmin=vmin, vmax=vmax)
            cmap = "viridis"

        for row_idx, (values, label) in enumerate(
            ((csf_values, "CSF"), (fem_values, "FEM3D"))
        ):
            ax = axes[row_idx, col]
            collection = PatchCollection(
                patches,
                cmap=cmap,
                norm=norm,
                edgecolor="none",
            )
            collection.set_array(values)
            ax.add_collection(collection)
            ax.autoscale_view()
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("x [m]")
            ax.set_ylabel("y [m]")
            ax.set_title(f"{label}: {title} [MPa]")
            colorbar = fig.colorbar(
                collection,
                ax=ax,
                orientation="vertical",
                shrink=0.84,
            )
            colorbar.set_label("[MPa]")

    fig.suptitle(
        f"CSF and FEM3D stress fields at z={float(comparison_z):.6g} m"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_csf_native_stress_rows(
    csf_path: dict[str, object],
    selected_section,
) -> list[dict[str, float | int]]:
    """
    Attach sigma_zz to the native CSF potential triangles.

    tau_x and tau_y are the native piecewise-constant values returned directly
    by the CSF potential solver. sigma_zz is evaluated at each native triangle
    centroid with the same Navier field used by the CSF solution.
    """
    navier_state = csf_path["navier_state"]
    rows: list[dict[str, float | int]] = []

    for triangle in csf_path["potential"]["triangles"]:
        polygon_idx = int(triangle["polygon_idx"])
        x0 = float(triangle["x0"])
        y0 = float(triangle["y0"])
        x1 = float(triangle["x1"])
        y1 = float(triangle["y1"])
        x2 = float(triangle["x2"])
        y2 = float(triangle["y2"])
        x = (x0 + x1 + x2) / 3.0
        y = (y0 + y1 + y2) / 3.0

        rows.append(
            {
                "polygon_idx": polygon_idx,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "x": x,
                "y": y,
                "sigma_zz": evaluate_csf_sigma_zz(
                    navier_state,
                    selected_section.polygons[polygon_idx],
                    x,
                    y,
                ),
                "tau_x": float(triangle["tau_x"]),
                "tau_y": float(triangle["tau_y"]),
            }
        )

    return rows


def plot_native_stress_maps(
    path: Path,
    csf_path: dict[str, object],
    selected_section,
    fem_rows: list[dict[str, object]],
    comparison_z: float,
    percentile: float = 99.0,
) -> None:
    """
    Plot stresses on the native CSF and FEM3D transverse meshes.

    Top row:
        native CSF potential triangles. No sampling onto the FEM3D grid.

    Bottom row:
        native FEM3D SSPbrick transverse cells at the comparison layer.

    For each stress component the CSF and FEM3D panels share one colour scale,
    clipped at ``percentile`` of the combined native values. Actual minima and
    maxima are annotated so clipping never hides the native extrema.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.collections import PatchCollection
        from matplotlib.colors import Normalize, TwoSlopeNorm
        from matplotlib.patches import Polygon as MplPolygon, Rectangle
    except ImportError as exc:
        raise RuntimeError(
            "Matplotlib is required to write the native-mesh stress maps."
        ) from exc

    percentile = float(percentile)
    if not (0.0 < percentile <= 100.0):
        raise ValueError(
            "native_stress_maps_percentile must satisfy 0 < value <= 100."
        )
    if not fem_rows:
        raise ValueError("Cannot plot native FEM3D stresses from an empty set.")

    csf_rows = build_csf_native_stress_rows(csf_path, selected_section)
    if not csf_rows:
        raise ValueError("Cannot plot native CSF stresses from an empty set.")

    csf_patches = [
        MplPolygon(
            [
                (float(row["x0"]), float(row["y0"])),
                (float(row["x1"]), float(row["y1"])),
                (float(row["x2"]), float(row["y2"])),
            ],
            closed=True,
        )
        for row in csf_rows
    ]
    fem_patches = [
        Rectangle(
            (float(row["x0"]), float(row["y0"])),
            float(row["x1"]) - float(row["x0"]),
            float(row["y1"]) - float(row["y0"]),
        )
        for row in fem_rows
    ]

    fields = (
        ("sigma_zz", "sigma_zz_3d", r"$\sigma_{zz}$"),
        ("tau_x", "tau_zx_3d", r"$\tau_x$ / $\tau_{zx}$"),
        ("tau_y", "tau_yz_3d", r"$\tau_y$ / $\tau_{yz}$"),
    )

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(13.4, 9.8),
        constrained_layout=True,
    )

    for col, (csf_key, fem_key, title) in enumerate(fields):
        csf_values = np.asarray(
            [float(row[csf_key]) / 1.0e6 for row in csf_rows],
            dtype=float,
        )
        fem_values = np.asarray(
            [float(row[fem_key]) / 1.0e6 for row in fem_rows],
            dtype=float,
        )
        combined = np.concatenate((csf_values, fem_values))

        signed = bool(np.any(combined < 0.0) and np.any(combined > 0.0))
        if signed:
            limit = float(np.percentile(np.abs(combined), percentile))
            if limit <= 0.0:
                limit = max(float(np.max(np.abs(combined))), 1.0)
            norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)
            cmap = "coolwarm"
        else:
            vmin = min(0.0, float(np.min(combined)))
            vmax = float(np.percentile(combined, percentile))
            if vmax <= vmin:
                vmax = max(float(np.max(combined)), vmin + 1.0)
            norm = Normalize(vmin=vmin, vmax=vmax)
            cmap = "viridis"

        panels = (
            (axes[0, col], csf_patches, csf_values, "CSF native"),
            (axes[1, col], fem_patches, fem_values, "FEM3D native"),
        )

        for ax, patches, values, label in panels:
            collection = PatchCollection(
                patches,
                cmap=cmap,
                norm=norm,
                edgecolor="none",
            )
            collection.set_array(values)
            ax.add_collection(collection)
            ax.autoscale_view()
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("x [m]")
            ax.set_ylabel("y [m]")
            ax.set_title(f"{label}: {title} [MPa]")
            ax.text(
                0.02,
                0.02,
                "actual min="
                f"{float(np.min(values)):.4g} MPa\n"
                "actual max="
                f"{float(np.max(values)):.4g} MPa",
                transform=ax.transAxes,
                ha="left",
                va="bottom",
                fontsize=8,
                bbox={
                    "facecolor": "white",
                    "alpha": 0.72,
                    "edgecolor": "none",
                },
            )
            colorbar = fig.colorbar(
                collection,
                ax=ax,
                orientation="vertical",
                shrink=0.84,
            )
            colorbar.set_label("[MPa]")

    fig.suptitle(
        "Native CSF and FEM3D stress fields "
        f"at z={float(comparison_z):.6g} m "
        f"(colour scale: {percentile:.6g}th percentile)"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


# ============================================================
# 5. ZONE-WISE FREQUENCY OF CSF / FEM3D DIFFERENCES
# ============================================================


def find_named_polygon(section, requested_name: str):
    """
    Return exactly one runtime polygon identified by name.

    Runtime polygon names may contain colon-separated tokens. This mirrors the
    name matching used by the load-projection code and keeps the diagnostic
    independent of polygon ordering.
    """
    matches = []

    for polygon_idx, polygon in enumerate(section.polygons):
        runtime_name = str(polygon.name)
        name_tokens = tuple(
            token.strip()
            for token in runtime_name.split(":")
            if token.strip()
        )

        if (
            runtime_name == requested_name
            or requested_name in name_tokens
        ):
            matches.append((polygon_idx, polygon))

    if len(matches) != 1:
        raise RuntimeError(
            "Zone-frequency diagnostic requires exactly one runtime polygon "
            f"identified as '{requested_name}'; matches={len(matches)}."
        )

    return matches[0]


def web_vertical_bounds(selected_section) -> tuple[float, float]:
    """
    Return the lower and upper y coordinates of the web polygon.

    The flange/web subdivision is geometric, not material-based. This is useful
    when a flange is itself split into several material polygons: every FEM3D
    comparison cell above the web is still assigned to the upper-flange zone,
    and every cell below the web is assigned to the lower-flange zone.
    """
    _, web_polygon = find_named_polygon(selected_section, "web")
    y_values = np.asarray(
        [float(vertex.y) for vertex in web_polygon.vertices],
        dtype=float,
    )

    if y_values.size == 0:
        raise RuntimeError("The web polygon has no vertices.")

    return float(np.min(y_values)), float(np.max(y_values))


def classify_comparison_zone(
    row: dict[str, object],
    web_y_min: float,
    web_y_max: float,
) -> str:
    """
    Classify one FEM3D comparison cell as upper flange, web or lower flange.

    The SSPbrick comparison rows contain the exact transverse rectangle
    [x0, x1] x [y0, y1]. Because the mesher is conforming to polygon boundary
    tracks, the web/flange interfaces coincide with cell edges.
    """
    y0 = float(row["y0"])
    y1 = float(row["y1"])

    scale = max(
        1.0,
        abs(web_y_min),
        abs(web_y_max),
        abs(y0),
        abs(y1),
    )
    tolerance = 100.0 * GEOMETRY_TOL * scale

    if y0 >= web_y_max - tolerance:
        return "upper_flange"

    if y1 <= web_y_min + tolerance:
        return "lower_flange"

    if y0 >= web_y_min - tolerance and y1 <= web_y_max + tolerance:
        return "web"

    raise RuntimeError(
        "A comparison cell crosses a web/flange interface, which should not "
        "occur in the conforming transverse mesh: "
        f"y0={y0:.12g}, y1={y1:.12g}, "
        f"web=[{web_y_min:.12g}, {web_y_max:.12g}]."
    )


def zone_difference_values(
    rows: list[dict[str, object]],
    zone_by_element: dict[int, str],
    zone: str,
    error_key: str,
    reference_key: str,
    mode: str,
    global_reference_peak: float,
) -> np.ndarray:
    """
    Return signed CSF - FEM3D differences for one zone and one component.

    mode="absolute"
        Values are returned in MPa.

    mode="percent"
        Values are returned as

            100 * (CSF - FEM3D) / max_A(|FEM3D|)

        where max_A is evaluated over the complete comparison section for the
        selected stress component. This is the same normalisation used by the
        percentage difference map, and it avoids singular local percentages
        where the reference stress passes through zero.
    """
    selected = [
        row
        for row in rows
        if zone_by_element[int(row["element_tag"])] == zone
    ]

    if not selected:
        return np.asarray([], dtype=float)

    errors = np.asarray(
        [float(row[error_key]) for row in selected],
        dtype=float,
    )

    if mode == "absolute":
        return errors / 1.0e6

    if mode == "percent":
        denominator = max(1.0e-12, float(global_reference_peak))
        return 100.0 * errors / denominator

    raise ValueError(
        "zone_frequency_mode must be either 'absolute' or 'percent'."
    )


def plot_zone_frequency_histograms(
    path: Path,
    rows: list[dict[str, object]],
    selected_section,
    comparison_z: float,
    *,
    bins: int = 50,
    mode: str = "percent",
) -> None:
    """
    Plot frequency distributions of pointwise CSF - FEM3D differences.

    Rows of the figure represent structural zones:

        1. upper flange
        2. web
        3. lower flange

    Columns represent stress components:

        1. sigma_zz
        2. tau_x / tau_zx
        3. tau_y / tau_yz

    The histogram frequency is the number of FEM3D comparison cells whose
    centre-point difference falls in each bin. No interpolation or smoothing is
    introduced. For each stress component the same bin edges are used in all
    three zones, which makes the three distributions directly comparable.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Matplotlib is required to write zone-frequency histograms."
        ) from exc

    if not rows:
        raise ValueError(
            "Cannot plot zone-frequency histograms from an empty point set."
        )

    bins = int(bins)
    if bins < 2:
        raise ValueError("zone_frequency_bins must be >= 2.")

    mode = str(mode).strip().lower()
    if mode not in ("absolute", "percent"):
        raise ValueError(
            "zone_frequency_mode must be either 'absolute' or 'percent'."
        )

    web_y_min, web_y_max = web_vertical_bounds(selected_section)

    zone_by_element = {
        int(row["element_tag"]): classify_comparison_zone(
            row,
            web_y_min,
            web_y_max,
        )
        for row in rows
    }

    zones = (
        ("upper_flange", "Upper flange"),
        ("web", "Web"),
        ("lower_flange", "Lower flange"),
    )
    fields = (
        (
            "sigma_zz_error",
            "sigma_zz_3d",
            r"$\Delta\sigma_{zz}$",
        ),
        (
            "tau_x_error",
            "tau_zx_3d",
            r"$\Delta\tau_x$",
        ),
        (
            "tau_y_error",
            "tau_yz_3d",
            r"$\Delta\tau_y$",
        ),
    )

    reference_peaks = {
        reference_key: float(
            np.max(
                np.abs(
                    np.asarray(
                        [float(row[reference_key]) for row in rows],
                        dtype=float,
                    )
                )
            )
        )
        for _, reference_key, _ in fields
    }

    values_by_zone_and_field: dict[tuple[str, str], np.ndarray] = {}
    bin_edges_by_field: dict[str, np.ndarray] = {}

    for error_key, reference_key, _ in fields:
        component_values = []

        for zone_key, _ in zones:
            values = zone_difference_values(
                rows,
                zone_by_element,
                zone_key,
                error_key,
                reference_key,
                mode,
                reference_peaks[reference_key],
            )
            values_by_zone_and_field[(zone_key, error_key)] = values

            if values.size:
                component_values.append(values)

        if not component_values:
            maximum = 1.0
        else:
            all_values = np.concatenate(component_values)
            maximum = float(np.max(np.abs(all_values)))
            if maximum <= 0.0:
                maximum = 1.0

        # Symmetric bins around zero make positive and negative bias visible.
        bin_edges_by_field[error_key] = np.linspace(
            -maximum,
            maximum,
            bins + 1,
        )

    fig, axes = plt.subplots(
        3,
        3,
        figsize=(14.0, 10.5),
        constrained_layout=True,
    )

    for row_idx, (zone_key, zone_title) in enumerate(zones):
        for col_idx, (error_key, reference_key, field_title) in enumerate(fields):
            ax = axes[row_idx, col_idx]
            values = values_by_zone_and_field[(zone_key, error_key)]
            bin_edges = bin_edges_by_field[error_key]

            if values.size:
                ax.hist(values, bins=bin_edges)

                statistics = (
                    f"n = {values.size}\n"
                    f"mean = {float(np.mean(values)):.3g}\n"
                    f"median = {float(np.median(values)):.3g}\n"
                    f"std = {float(np.std(values)):.3g}"
                )
                ax.text(
                    0.97,
                    0.95,
                    statistics,
                    transform=ax.transAxes,
                    ha="right",
                    va="top",
                    fontsize=8,
                    bbox={
                        "facecolor": "white",
                        "alpha": 0.78,
                        "edgecolor": "none",
                    },
                )
            else:
                ax.text(
                    0.5,
                    0.5,
                    "No cells",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                )

            ax.axvline(0.0, linewidth=0.9)
            ax.set_xlim(float(bin_edges[0]), float(bin_edges[-1]))
            ax.set_title(f"{zone_title}: {field_title}")
            ax.set_ylabel("Frequency [cells]")

            if mode == "absolute":
                ax.set_xlabel("CSF - FEM3D [MPa]")
            else:
                ax.set_xlabel(
                    "100 · (CSF - FEM3D) / max$_A$(|FEM3D|) [%]"
                )

    mode_description = (
        "signed differences in MPa"
        if mode == "absolute"
        else "signed differences normalised by the whole-section FEM3D peak"
    )

    fig.suptitle(
        "Frequency of CSF - FEM3D pointwise differences by section zone\n"
        f"z = {float(comparison_z):.6g} m; {mode_description}"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


# ============================================================
# 6. OUTPUT / REPORT
# ============================================================


def write_report(
    path: Path,
    *,
    model_file: Path,
    settings_file: Path,
    z0: float,
    z1: float,
    comparison_t: float,
    comparison_z: float,
    q: float,
    actions: dict[str, float],
    selected_section,
    fem3d: dict[str, object],
    csf_path: dict[str, object],
    fem_resultants: dict[str, float],
    metrics: dict[str, float],
    output_paths: dict[str, Path],
) -> None:
    potential = csf_path["potential"]
    polygon_element_counts = Counter(
        int(row["polygon_idx"])
        for row in fem3d["fem_rows"]
    )

    lines: list[str] = []

    lines.append("CSF / OpenSees 3D continuum benchmark")
    lines.append("=" * 43)
    lines.append("")
    lines.append("MODEL")
    lines.append(f"  CSF YAML        : {model_file}")
    lines.append(f"  settings YAML   : {settings_file}")
    lines.append(f"  z0              : {z0:.12g} m")
    lines.append(f"  z1              : {z1:.12g} m")
    lines.append(f"  L               : {z1 - z0:.12g} m")
    lines.append(f"  comparison_t    : {comparison_t:.12g}")
    lines.append(f"  comparison_z    : {comparison_z:.12g} m")
    lines.append("")
    lines.append("LOADING")
    lines.append("  type            : simply_supported_udl_y")
    lines.append(f"  q               : {q:.12e} N/m")
    lines.append("")
    lines.append("CSF INPUT ACTIONS AT COMPARISON STATION")

    for key in ("N", "Mx", "My", "Tx", "Ty"):
        unit = "N" if key in ("N", "Tx", "Ty") else "N m"
        lines.append(
            f"  {key:<15s} : {actions[key]:.12e} {unit}"
        )

    lines.append("")
    lines.append("POLYGONS AT COMPARISON STATION")
    lines.append(
        "  idx  name                         container_idx"
        "        weightabs     shear_weightabs      poisson"
        "    FEM cells"
    )

    for idx, polygon in enumerate(selected_section.polygons):
        container = (
            "-"
            if polygon.container_idx is None
            else str(int(polygon.container_idx))
        )
        lines.append(
            f"  {idx:>3d}  "
            f"{str(polygon.name):<28.28s} "
            f"{container:>13s} "
            f"{float(polygon.weightabs):>16.8e} "
            f"{float(polygon.shear_weightabs):>19.8e} "
            f"{float(polygon.poisson):>12.6g} "
            f"{polygon_element_counts.get(idx, 0):>10d}"
        )

    lines.append("")
    lines.append("FEM 3D MESH")
    lines.append(f"  nz                    : {fem3d['nz']}")
    lines.append(
        f"  target_size_xy        : {fem3d['target_size_xy']:.12g} m"
    )
    lines.append(f"  transverse nx cells   : {fem3d['nx']}")
    lines.append(f"  transverse ny cells   : {fem3d['ny']}")
    lines.append(f"  nodes                 : {fem3d['node_count']}")
    lines.append(
        f"  SSPbrick elements     : {fem3d['brick_element_count']}"
    )
    lines.append(
        f"  loaded top faces      : {fem3d['loaded_face_count']}"
    )
    lines.append(f"  material tags         : {fem3d['material_count']}")
    lines.append(
        f"  comparison layer k    : {fem3d['selected_k']}"
    )
    lines.append("")
    lines.append("FEM 3D REACTIONS")
    lines.append(
        f"  left Ry               : {fem3d['left_reaction_y']:.12e} N"
    )
    lines.append(
        f"  right Ry              : {fem3d['right_reaction_y']:.12e} N"
    )
    lines.append(
        f"  total Ry              : {fem3d['total_reaction_y']:.12e} N"
    )
    lines.append("")
    lines.append("CSF LOCAL-SHEAR-POTENTIAL RESULTANTS")
    lines.append(
        f"  Tx recovered          : "
        f"{float(potential['resultants']['Tx_recovered']):.12e} N"
    )
    lines.append(
        f"  Ty recovered          : "
        f"{float(potential['resultants']['Ty_recovered']):.12e} N"
    )
    lines.append(
        f"  Tx error              : "
        f"{float(potential['resultants']['Tx_error']):.12e} N"
    )
    lines.append(
        f"  Ty error              : "
        f"{float(potential['resultants']['Ty_error']):.12e} N"
    )
    lines.append("")
    lines.append("FEM 3D RECONSTRUCTED SECTION RESULTANTS")

    for key in ("N", "Mx", "My", "Tx", "Ty"):
        unit = "N" if key in ("N", "Tx", "Ty") else "N m"
        lines.append(
            f"  {key:<21s} : {fem_resultants[key]:.12e} {unit}"
        )

    lines.append("")
    lines.append("POINTWISE ERROR METRICS")

    for key, value in metrics.items():
        lines.append(f"  {key:<24s}: {value:.12e}")

    lines.append("")
    lines.append("OUTPUT FILES")

    for key, output_path in output_paths.items():
        lines.append(f"  {key:<24s}: {output_path}")

    lines.append("")
    lines.append("NOTES")
    lines.append(
        "  - No CSF stress/resultant is passed into the OpenSees solution."
    )
    lines.append(
        "  - FEM material values are sampled from field.section(z): "
        "weightabs, shear_weightabs, poisson."
    )
    lines.append(
        "  - container_idx controls material replacement / parent punching."
    )
    lines.append(
        "  - Version 3 performs an interface-noding preflight and never "
        "repairs geometry automatically."
    )
    lines.append(
        "  - OpenSees material is ElasticIsotropic only."
    )
    lines.append(
        "  - The transverse brick mesher requires rectilinear "
        "polygon boundaries."
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


# ============================================================
# 7. MAIN
# ============================================================


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python3 tsec_fem3d_benchmark_v17.py "
            "tsec_fem3d_settings.yaml"
        )

    settings_file = Path(sys.argv[1]).resolve()
    settings = load_settings(settings_file)

    csf_yaml = resolve_from_settings(
        settings_file,
        str(get_required(settings, "model", "csf_yaml")),
    ).resolve()

    comparison_t = float(
        get_required(
            settings,
            "benchmark",
            "comparison_t",
        )
    )
    loading_type = str(
        get_required(
            settings,
            "benchmark",
            "loading",
            "type",
        )
    )
    q = float(
        get_required(
            settings,
            "benchmark",
            "loading",
            "q",
        )
    )
    load_projection_polygon = str(
        get_required(
            settings,
            "benchmark",
            "loading",
            "projection_polygon",
        )
    )

    if loading_type != "simply_supported_udl_y":
        raise NotImplementedError(
            "Version 1 supports only "
            "benchmark.loading.type=simply_supported_udl_y."
        )

    dz_relative = float(
        get_required(
            settings,
            "csf",
            "local_shear_potential",
            "dz_relative",
        )
    )
    mesh_refinements = int(
        get_required(
            settings,
            "csf",
            "local_shear_potential",
            "mesh_refinements",
        )
    )
    compatibility_rtol = float(
        get_required(
            settings,
            "csf",
            "local_shear_potential",
            "compatibility_rtol",
        )
    )
    compatibility_atol = float(
        get_required(
            settings,
            "csf",
            "local_shear_potential",
            "compatibility_atol",
        )
    )

    solver_name = str(
        get_required(
            settings,
            "fem3d",
            "solver",
        )
    )

    if solver_name != "openseespy":
        raise NotImplementedError(
            "Version 1 supports fem3d.solver=openseespy."
        )

    nz = int(
        get_required(
            settings,
            "fem3d",
            "mesh",
            "nz",
        )
    )
    target_size_xy = float(
        get_required(
            settings,
            "fem3d",
            "mesh",
            "target_size_xy",
        )
    )
    system_name = str(
        get_required(
            settings,
            "fem3d",
            "analysis",
            "system",
        )
    )
    algorithm_name = str(
        get_required(
            settings,
            "fem3d",
            "analysis",
            "algorithm",
        )
    )

    output_directory = resolve_from_settings(
        settings_file,
        str(
            get_required(
                settings,
                "output",
                "directory",
            )
        ),
    ).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    difference_map_mode = str(
        settings.get("output", {}).get("difference_map_mode", "absolute")
    ).strip().lower()

    if difference_map_mode not in ("absolute", "percent"):
        raise ValueError(
            "output.difference_map_mode must be either 'absolute' or 'percent'."
        )

    native_stress_maps_percentile = float(
        settings.get("output", {}).get("native_stress_maps_percentile", 99.0)
    )
    if not (0.0 < native_stress_maps_percentile <= 100.0):
        raise ValueError(
            "output.native_stress_maps_percentile must satisfy 0 < value <= 100."
        )

    # The zone-frequency figure is optional in the YAML so v17 remains usable
    # with settings files written before this paper-oriented diagnostic existed.
    # By default it follows difference_map_mode, keeping the map and histogram
    # normalisation consistent.
    zone_frequency_mode = str(
        settings.get("output", {}).get(
            "zone_frequency_mode",
            difference_map_mode,
        )
    ).strip().lower()
    if zone_frequency_mode not in ("absolute", "percent"):
        raise ValueError(
            "output.zone_frequency_mode must be either 'absolute' or 'percent'."
        )

    zone_frequency_bins = int(
        settings.get("output", {}).get("zone_frequency_bins", 50)
    )
    if zone_frequency_bins < 2:
        raise ValueError("output.zone_frequency_bins must be >= 2.")

    zone_frequency_filename = str(
        settings.get("output", {}).get(
            "zone_frequency_jpg",
            "csf_fem3d_zone_frequency_histograms.jpg",
        )
    )

    output_paths = {
        "pointwise_csv": output_directory
        / str(get_required(settings, "output", "pointwise_csv")),
        "summary_csv": output_directory
        / str(get_required(settings, "output", "summary_csv")),
        "csf_field_csv": output_directory
        / str(get_required(settings, "output", "csf_field_csv")),
        "fem3d_field_csv": output_directory
        / str(get_required(settings, "output", "fem3d_field_csv")),
        "fem3d_section_jpg": output_directory
        / str(
            get_required(
                settings,
                "output",
                "fem3d_section_jpg",
            )
        ),
        "difference_map_jpg": output_directory
        / str(
            get_required(
                settings,
                "output",
                "difference_map_jpg",
            )
        ),
        "stress_maps_jpg": output_directory
        / str(get_required(settings, "output", "stress_maps_jpg")),
        "native_stress_maps_jpg": output_directory
        / str(get_required(settings, "output", "native_stress_maps_jpg")),
        "zone_frequency_jpg": output_directory / zone_frequency_filename,
        "report_txt": output_directory
        / str(get_required(settings, "output", "report_txt")),
    }

    field = read_csf_model(csf_yaml)

    z0 = float(field.s0.z)
    z1 = float(field.s1.z)

    if z1 <= z0:
        raise ValueError("The CSF longitudinal domain must satisfy z1 > z0.")

    if not (0.0 < comparison_t < 1.0):
        raise ValueError("benchmark.comparison_t must satisfy 0 < t < 1.")

    comparison_z = z0 + comparison_t * (z1 - z0)

    actions = beam_actions_simply_supported_udl_y(
        comparison_z,
        z0,
        z1,
        q,
    )

    # Geometry preflight is deliberately performed before either numerical path.
    # It checks only whether shared polygon interfaces are explicitly noded in
    # the CSF representation; it never changes the model.
    validate_csf_interface_noding(
        field,
        comparison_z,
    )

    print(f"CSF / OpenSees 3D benchmark v{SCRIPT_VERSION}")
    print("  interface noding: OK")
    print(f"  model          : {csf_yaml}")
    print(f"  comparison_t   : {comparison_t:.12g}")
    print(f"  comparison_z   : {comparison_z:.12g} m")
    print(f"  q              : {q:.12e} N/m")

    # ========================================================
    # 2. CSF SECTIONAL SOLUTION
    # ========================================================

    csf_path = solve_csf_path(
        field,
        comparison_z,
        actions,
        dz_relative,
        mesh_refinements,
        compatibility_rtol,
        compatibility_atol,
    )

    selected_section = field.section(comparison_z)
    section_analysis = section_full_analysis(
        selected_section,
        compute_vroark=False,
    )

    write_csv(
        output_paths["csf_field_csv"],
        csf_path["potential"]["triangles"],
    )

    # ========================================================
    # 3. THREE-DIMENSIONAL FEM SOLUTION
    # ========================================================

    fem3d = run_fem3d_path(
        field,
        z0,
        z1,
        comparison_z,
        comparison_t,
        q,
        load_projection_polygon,
        nz,
        target_size_xy,
        system_name,
        algorithm_name,
        output_paths["fem3d_section_jpg"],
    )

    # Reuse the exact cached FEM comparison section.
    selected_section = fem3d["selected_section"]

    write_csv(
        output_paths["fem3d_field_csv"],
        fem3d["fem_rows"],
    )

    # ========================================================
    # 4. CSF / FEM 3D COMPARISON
    # ========================================================

    pointwise_rows = build_pointwise_comparison(
        csf_path,
        fem3d["fem_rows"],
        selected_section,
    )
    metrics = comparison_metrics(pointwise_rows)
    fem_resultants = reconstruct_fem3d_resultants(
        fem3d["fem_rows"],
        section_analysis,
    )

    write_csv(
        output_paths["pointwise_csv"],
        pointwise_rows,
    )

    plot_pointwise_difference_map(
        output_paths["difference_map_jpg"],
        pointwise_rows,
        comparison_z,
        difference_map_mode,
    )

    plot_pointwise_stress_maps(
        output_paths["stress_maps_jpg"],
        pointwise_rows,
        comparison_z,
    )

    plot_native_stress_maps(
        output_paths["native_stress_maps_jpg"],
        csf_path,
        selected_section,
        fem3d["fem_rows"],
        comparison_z,
        native_stress_maps_percentile,
    )

    plot_zone_frequency_histograms(
        output_paths["zone_frequency_jpg"],
        pointwise_rows,
        selected_section,
        comparison_z,
        bins=zone_frequency_bins,
        mode=zone_frequency_mode,
    )

    summary_row = {
        "comparison_t": comparison_t,
        "comparison_z": comparison_z,
        "q": q,
        "N_input": actions["N"],
        "Mx_input": actions["Mx"],
        "My_input": actions["My"],
        "Tx_input": actions["Tx"],
        "Ty_input": actions["Ty"],
        "N_fem3d": fem_resultants["N"],
        "Mx_fem3d": fem_resultants["Mx"],
        "My_fem3d": fem_resultants["My"],
        "Tx_fem3d": fem_resultants["Tx"],
        "Ty_fem3d": fem_resultants["Ty"],
        "Tx_csf_recovered": float(
            csf_path["potential"]["resultants"]["Tx_recovered"]
        ),
        "Ty_csf_recovered": float(
            csf_path["potential"]["resultants"]["Ty_recovered"]
        ),
        **metrics,
        "fem3d_nodes": fem3d["node_count"],
        "fem3d_bricks": fem3d["brick_element_count"],
        "fem3d_materials": fem3d["material_count"],
        "reaction_y_total": fem3d["total_reaction_y"],
    }

    write_csv(
        output_paths["summary_csv"],
        [summary_row],
    )

    write_report(
        output_paths["report_txt"],
        model_file=csf_yaml,
        settings_file=settings_file,
        z0=z0,
        z1=z1,
        comparison_t=comparison_t,
        comparison_z=comparison_z,
        q=q,
        actions=actions,
        selected_section=selected_section,
        fem3d=fem3d,
        csf_path=csf_path,
        fem_resultants=fem_resultants,
        metrics=metrics,
        output_paths=output_paths,
    )

    print("")
    print("Pointwise comparison")
    print(
        "  sigma_zz relative L2 : "
        f"{metrics['sigma_zz_rel_l2']:.6e}"
    )
    print(
        "  tau_x relative L2    : "
        f"{metrics['tau_x_rel_l2']:.6e}"
    )
    print(
        "  tau_y relative L2    : "
        f"{metrics['tau_y_rel_l2']:.6e}"
    )
    print(
        "  tau vector relative L2: "
        f"{metrics['tau_vector_rel_l2']:.6e}"
    )
    print("")
    print(f"Outputs: {output_directory}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

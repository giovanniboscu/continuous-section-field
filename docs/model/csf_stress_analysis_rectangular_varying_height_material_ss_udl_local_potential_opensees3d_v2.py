"""
Definitive CSF local-shear-potential / OpenSees 3D continuum benchmark.

This file is derived directly from the simple CSF example
``csf_stress_analysis_rectangular_varying_height_material_ss_udl.py`` and keeps
its physical case unchanged:

- simply supported beam;
- span L = 10 m;
- constant width b = 0.30 m;
- top face fixed at y = +0.30 m;
- lower face varying linearly from y = -0.30 m to y = -0.70 m;
- fixed material interface at y = 0;
- upper axial-flexural participation equal to 1;
- lower participation varying linearly from 1 to 0.45;
- common Poisson ratio nu = 0.25;
- uniformly distributed transverse load q = 20 kN/m;
- comparison station z = 3 m.

The purpose of this version is deliberately narrower and stronger than the
earlier reduced-form benchmarks: the newly implemented CSF local
shear-potential field is compared directly with an independent three-dimensional
OpenSees continuum model.

No analytical non-prismatic correction is used as a reference in this file.

CSF prediction
--------------
The primary CSF shear field is obtained only from

    analyse_navier_local_shear_potential(...)

which solves the reduced local equilibrium closure

    div(G_like * grad(phi)) = -partial(sigma_zz) / partial(z)

with

    tau = G_like * grad(phi).

The complete Navier normal stress supplies the longitudinal source. The
polygon-level ``shear_weightabs`` field supplies ``G_like``. Moving-boundary and
material-interface conditions are handled inside the core API.

OpenSees 3D comparison
----------------------
The continuum model uses SSPbrick elements. The upper region has

    E = E_REF_3D,

while the lower region has the same longitudinal participation law as CSF:

    E_lower(z) = E_REF_3D * lower_weight(z).

The same Poisson ratio is used in both regions, so the lower shear modulus also
follows the CSF isotropic participation law.

A pressure q / b is applied to the top face. The model is simply supported in
the transverse y direction, with minimal additional constraints used only to
remove rigid-body modes.

Comparison rules
----------------
1. The CSF potential field is solved independently of OpenSees.
2. No field scaling, fitting, projection or action matching is applied.
3. OpenSees stresses are sampled at SSPbrick centres located exactly at z = 3 m.
4. The CSF fields are evaluated at those same physical (x, y) coordinates.
5. Both pointwise errors and reconstructed section resultants are reported.
6. A directional 3D mesh-refinement suite separates x, y and z discretization
   sensitivity.
7. The CSF potential mesh is fixed and substantially finer than the 3D section
   meshes so that the reported trend is primarily a continuum-mesh study.

The main comparison quantities are

    sigma_zz_CSF  <-> sigma_zz_3D
    tau_x_CSF     <-> tau_zx_3D
    tau_y_CSF     <-> tau_yz_3D

and the two-component shear-vector error

    ||tau_CSF - tau_3D||_L2 / ||tau_3D||_L2.

Interpretation
--------------
This script does not assume in advance that the reduced CSF field must coincide
pointwise with three-dimensional elasticity. The numerical discrepancy and its
mesh trend are the result of the benchmark.

The 3D model can retain local Poisson effects, support effects and through-width
stress variation that are outside a reduced sectional closure. For that reason,
the script enforces strict checks only on internal consistency, constitutive
response, reactions and CSF resultant recovery; it reports CSF-versus-3D stress
errors without forcing an arbitrary pass/fail tolerance.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import math

import numpy as np

from csf import (
    ContinuousSectionField,
    Polygon,
    Pt,
    Section,
    section_full_analysis,
    section_properties,
)

import csf.polygon_stress as polygon_stress_module

try:
    import openseespy.opensees as ops
except ImportError:
    ops = None


# ---------------------------------------------------------------------------
# 1. ORIGINAL SIMPLE-BENCHMARK GEOMETRY AND LOADING
# ---------------------------------------------------------------------------

L = 10.0  # [m]
q = 20_000.0  # [N/m]
b = 0.30  # [m]

y_top = 0.30  # [m]
y_bottom_start = -0.30  # [m]
y_bottom_end = -0.70  # [m]
y_interface = 0.00  # [m]

upper_weight_start = 1.00
upper_weight_end = 1.00
lower_weight_start = 1.00
lower_weight_end = 0.45

nu = 0.25

# The selected station is unchanged from the source example. The OpenSees NZ
# values below are chosen so this station is exactly an SSPbrick centre.
z = 3.00  # [m]

# Classical simply-supported-beam resultants under the UDL. These are supplied
# to CSF independently of the 3D solution.
R = q * L / 2.0  # [N]
N = 0.0
Mx = q * z * (L - z) / 2.0
My = 0.0
Tx = 0.0
Ty = q * (L / 2.0 - z)


# ---------------------------------------------------------------------------
# 2. CONTINUOUS SECTION FIELD -- UNCHANGED PHYSICAL CASE
# ---------------------------------------------------------------------------

upper_start = Polygon(
    vertices=(
        Pt(-b / 2, y_interface),
        Pt( b / 2, y_interface),
        Pt( b / 2, y_top),
        Pt(-b / 2, y_top),
    ),
    weight=upper_weight_start,
    name="upper_region",
)

lower_start = Polygon(
    vertices=(
        Pt(-b / 2, y_bottom_start),
        Pt( b / 2, y_bottom_start),
        Pt( b / 2, y_interface),
        Pt(-b / 2, y_interface),
    ),
    weight=lower_weight_start,
    name="lower_region",
)

upper_end = Polygon(
    vertices=(
        Pt(-b / 2, y_interface),
        Pt( b / 2, y_interface),
        Pt( b / 2, y_top),
        Pt(-b / 2, y_top),
    ),
    weight=upper_weight_end,
    name="upper_region",
)

lower_end = Polygon(
    vertices=(
        Pt(-b / 2, y_bottom_end),
        Pt( b / 2, y_bottom_end),
        Pt( b / 2, y_interface),
        Pt(-b / 2, y_interface),
    ),
    weight=lower_weight_end,
    name="lower_region",
)

field = ContinuousSectionField(
    section0=Section(
        polygons=(lower_start, upper_start),
        z=0.0,
    ),
    section1=Section(
        polygons=(lower_end, upper_end),
        z=L,
    ),
)

field.set_weight_laws(
    [
        "lower_region,lower_region : w0 + (w1 - w0) * t",
    ]
)

field.set_shear_weight_laws(
    [
        f"lower_region,lower_region : iso({nu})",
        f"upper_region,upper_region : iso({nu})",
    ]
)


# ---------------------------------------------------------------------------
# 3. DEFINITIVE-BENCHMARK NUMERICAL SETTINGS
# ---------------------------------------------------------------------------

E_REF_3D = 210.0e9  # [Pa]
RHO_3D = 0.0  # [kg/m^3]

OUTPUT_DIRECTORY = Path(
    "output_csf_local_potential_opensees3d_definitive"
)
SUMMARY_CSV = OUTPUT_DIRECTORY / "mesh_comparison_summary.csv"
POTENTIAL_TRIANGLES_CSV = OUTPUT_DIRECTORY / "local_potential_triangles.csv"
POTENTIAL_SUMMARY_CSV = OUTPUT_DIRECTORY / "local_potential_summary.csv"

# A high-resolution CSF potential mesh is solved once and reused for every 3D
# mesh case. For this two-region rectangular section, refinement level 7 is
# intentionally much finer than the section discretization used by OpenSees.
POTENTIAL_MESH_REFINEMENTS = 7
POTENTIAL_DZ = 1.0e-4  # [m]

# Internal CSF guards. These do not constrain the CSF-vs-3D comparison itself.
POTENTIAL_RESULTANT_TOLERANCE = 1.0e-3  # [N]

# OpenSees internal checks. The 3D stress comparison remains descriptive.
CONSTITUTIVE_RELATIVE_TOLERANCE = 1.0e-10
REACTION_RELATIVE_TOLERANCE = 1.0e-8


@dataclass(frozen=True)
class MeshCase:
    name: str
    purpose: str
    nx: int
    ny_lower: int
    ny_upper: int
    nz: int


# The suite is the same controlled refinement pattern previously used for this
# geometry. Only one discretization direction is changed at a time, followed by
# a combined refined case.
MESH_CASES = (
    MeshCase(
        "coarse",
        "deliberately coarse baseline",
        nx=2,
        ny_lower=4,
        ny_upper=3,
        nz=75,
    ),
    MeshCase(
        "reference",
        "reference discretization",
        nx=4,
        ny_lower=8,
        ny_upper=6,
        nz=125,
    ),
    MeshCase(
        "x_refined",
        "width-direction refinement from reference",
        nx=8,
        ny_lower=8,
        ny_upper=6,
        nz=125,
    ),
    MeshCase(
        "y_refined",
        "section-depth refinement from reference",
        nx=4,
        ny_lower=12,
        ny_upper=9,
        nz=125,
    ),
    MeshCase(
        "z_refined",
        "longitudinal refinement from reference",
        nx=4,
        ny_lower=8,
        ny_upper=6,
        nz=175,
    ),
    MeshCase(
        "combined_refined",
        "combined x-y-z refinement",
        nx=8,
        ny_lower=12,
        ny_upper=9,
        nz=175,
    ),
)


# ---------------------------------------------------------------------------
# 4. BASIC CONTINUOUS GEOMETRY / ACTION HELPERS
# ---------------------------------------------------------------------------


def require_opensees() -> None:
    """Require OpenSeesPy only when the continuum benchmark is executed."""
    if ops is None:
        raise SystemExit(
            "OpenSeesPy is required for this benchmark. "
            "Install it in the active Python environment."
        )


def bottom_ordinate_at(z_value: float) -> float:
    """Return the exact linearly varying lower outer ordinate."""
    t_value = float(z_value) / L
    return (
        y_bottom_start
        + (y_bottom_end - y_bottom_start) * t_value
    )


def lower_weight_at(z_value: float) -> float:
    """Return the exact linearly varying lower-region participation."""
    t_value = float(z_value) / L
    return (
        lower_weight_start
        + (lower_weight_end - lower_weight_start) * t_value
    )


def actions_at(z_value: float) -> tuple[float, float, float, float, float]:
    """Return the analytical section resultants at one beam station."""
    z_value = float(z_value)
    return (
        0.0,
        q * z_value * (L - z_value) / 2.0,
        0.0,
        0.0,
        q * (L / 2.0 - z_value),
    )


# ---------------------------------------------------------------------------
# 5. NAVIER POINT EVALUATION
# ---------------------------------------------------------------------------


def navier_point_stress(
    *,
    z_value: float,
    x_value: float,
    y_value: float,
    polygon_index: int,
    N_value: float,
    Mx_value: float,
    My_value: float,
) -> float:
    """
    Evaluate the complete CSF Navier normal stress at one physical point.

    The equation is reproduced explicitly here so the 3D comparison does not
    depend on polygon-envelope post-processing. The same weighted section
    properties used by the core Navier implementation are reconstructed at the
    requested station.
    """
    section = field.section(float(z_value))
    analysis = section_full_analysis(
        section,
        compute_vroark=False,
    )

    A = float(analysis["A"])
    Cx = float(analysis["Cx"])
    Cy = float(analysis["Cy"])
    Ix = float(analysis["Ix"])
    Iy = float(analysis["Iy"])
    Ixy = float(analysis["Ixy"])

    D = Ix * Iy - Ixy * Ixy

    if abs(A) <= 1.0e-14 * max(1.0, abs(A)):
        raise ValueError("Invalid weighted area in Navier point evaluation.")

    if abs(D) <= 1.0e-14 * max(
        1.0,
        abs(Ix * Iy),
        abs(Ixy * Ixy),
    ):
        raise ValueError("Singular weighted inertia in Navier point evaluation.")

    axial = float(N_value) / A
    bx = (
        float(My_value) * Ix
        - float(Mx_value) * Ixy
    ) / D
    by = (
        float(Mx_value) * Iy
        - float(My_value) * Ixy
    ) / D

    weightabs = float(
        section.polygons[int(polygon_index)].weightabs
    )

    return weightabs * (
        axial
        + bx * (float(x_value) - Cx)
        + by * (float(y_value) - Cy)
    )


# ---------------------------------------------------------------------------
# 6. LOCAL SHEAR-POTENTIAL SOLUTION AND SAME-POINT EVALUATOR
# ---------------------------------------------------------------------------


def local_potential_api():
    """Return the installed core local-shear-potential function."""
    function = getattr(
        polygon_stress_module,
        "analyse_navier_local_shear_potential",
        None,
    )

    if function is None:
        raise RuntimeError(
            "The installed csf.polygon_stress module does not expose "
            "analyse_navier_local_shear_potential(). "
            "Install the validated polygon_stress.py candidate first."
        )

    return function


def solve_reference_potential() -> dict[str, object]:
    """
    Solve the CSF local field once from the analytical beam resultants.

    No OpenSees quantity is passed to this call. The resulting field is therefore
    an independent CSF prediction throughout the complete 3D mesh suite.
    """
    result = local_potential_api()(
        section_field=field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
        Tx=Tx,
        Ty=Ty,
        dN_dz=0.0,
        dz=POTENTIAL_DZ,
        mesh_refinements=POTENTIAL_MESH_REFINEMENTS,
        validation_points=None,
    )

    Tx_error = float(result["resultants"]["Tx_error"])
    Ty_error = float(result["resultants"]["Ty_error"])

    if abs(Tx_error) > POTENTIAL_RESULTANT_TOLERANCE:
        raise RuntimeError(
            "CSF local-potential Tx recovery failed before the 3D comparison: "
            f"error={Tx_error:.6e} N."
        )

    if abs(Ty_error) > POTENTIAL_RESULTANT_TOLERANCE:
        raise RuntimeError(
            "CSF local-potential Ty recovery failed before the 3D comparison: "
            f"error={Ty_error:.6e} N."
        )

    return result


class PotentialFieldEvaluator:
    """
    Evaluate the piecewise-constant P1 shear field at arbitrary section points.

    The core returns one constant shear vector per triangle. A Shapely STRtree
    identifies all triangles intersecting a requested point. If the point lies
    exactly on an internal potential-mesh edge, the adjacent triangle stresses
    are area-weight averaged rather than selecting an arbitrary side.

    The SSPbrick centres used below are never on the physical material interface,
    but they can coincide accidentally with an internal triangulation diagonal;
    this averaging makes that numerical coincidence harmless.
    """

    def __init__(self, triangle_rows: list[dict[str, object]]):
        try:
            from shapely.geometry import Point as ShapelyPoint
            from shapely.geometry import Polygon as ShapelyPolygon
            from shapely.strtree import STRtree
        except ImportError as exc:
            raise RuntimeError(
                "Shapely >= 2.1 is required to evaluate the local potential field."
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
        self._tau_x = np.asarray(
            [float(row["tau_x"]) for row in triangle_rows],
            dtype=float,
        )
        self._tau_y = np.asarray(
            [float(row["tau_y"]) for row in triangle_rows],
            dtype=float,
        )
        self._area = np.asarray(
            [float(row["area"]) for row in triangle_rows],
            dtype=float,
        )

    def evaluate(self, x_value: float, y_value: float) -> tuple[float, float, int]:
        """Return tau_x, tau_y and the number of containing triangles."""
        point = self._Point(float(x_value), float(y_value))
        indices = np.asarray(
            self._tree.query(
                point,
                predicate="intersects",
            ),
            dtype=int,
        )

        if indices.size == 0:
            raise RuntimeError(
                "No local-potential triangle contains comparison point "
                f"({x_value}, {y_value})."
            )

        weights = self._area[indices]
        weight_sum = float(np.sum(weights))

        if weight_sum <= 0.0:
            raise RuntimeError("Invalid local-potential triangle area sum.")

        tau_x = float(
            np.sum(weights * self._tau_x[indices]) / weight_sum
        )
        tau_y = float(
            np.sum(weights * self._tau_y[indices]) / weight_sum
        )

        return tau_x, tau_y, int(indices.size)


# ---------------------------------------------------------------------------
# 7. NUMERICAL METRICS
# ---------------------------------------------------------------------------


def area_integral(
    rows: list[dict[str, object]],
    key: str,
) -> float:
    """Integrate one sampled field over the comparison section."""
    return sum(
        float(row["area"]) * float(row[key])
        for row in rows
    )


def normalized_l2_error(
    rows: list[dict[str, object]],
    *,
    prediction_key: str,
    reference_key: str,
) -> float:
    """Return the area-weighted scalar normalized L2 error."""
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
    *,
    prediction_key: str,
    reference_key: str,
) -> float:
    """Return max absolute scalar error normalized by max reference magnitude."""
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
    """Return the area-weighted normalized error of the two-component shear vector."""
    numerator = sum(
        float(row["area"])
        * (
            (
                float(row["tau_x_potential_csf"])
                - float(row["tau_zx_3d"])
            ) ** 2
            + (
                float(row["tau_y_potential_csf"])
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
    """Return max shear-vector error normalized by max 3D shear-vector magnitude."""
    numerator = max(
        math.hypot(
            float(row["tau_x_potential_csf"])
            - float(row["tau_zx_3d"]),
            float(row["tau_y_potential_csf"])
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


def maximum_x_spread_at_equal_y(
    rows: list[dict[str, object]],
    key: str,
) -> float:
    """
    Return the maximum through-width spread at equal region and y coordinate.

    The reduced rectangular CSF field is x-invariant. This diagnostic quantifies
    the genuinely three-dimensional through-width variation retained by the
    continuum solution.
    """
    grouped: dict[tuple[str, float], list[float]] = {}

    for row in rows:
        group_key = (
            str(row["region"]),
            round(float(row["y"]), 12),
        )
        grouped.setdefault(
            group_key,
            [],
        ).append(float(row[key]))

    return max(
        (
            max(values) - min(values)
            for values in grouped.values()
        ),
        default=0.0,
    )


# ---------------------------------------------------------------------------
# 8. OPENSEES 3D MODEL
# ---------------------------------------------------------------------------


def run_opensees_case(
    case: MeshCase,
    *,
    potential_result: dict[str, object],
    potential_evaluator: PotentialFieldEvaluator,
) -> dict[str, object]:
    """
    Run one independent SSPbrick continuum discretization.

    The geometry and longitudinal material participation are sampled directly
    from the same continuous definitions used to construct the original CSF
    example, but no stress result from CSF enters the OpenSees analysis.
    """
    if case.nx < 2 or case.nx % 2 != 0:
        raise ValueError(
            f"{case.name}: nx must be an even integer >= 2."
        )

    if min(
        case.ny_lower,
        case.ny_upper,
        case.nz,
    ) < 1:
        raise ValueError(
            f"{case.name}: mesh subdivision counts must be positive."
        )

    dz_3d = L / case.nz

    # The selected station must coincide with the centre of one longitudinal
    # brick layer; otherwise OpenSees and CSF would not be compared at the same
    # z coordinate.
    selected_index_float = z / dz_3d - 0.5
    selected_k = int(round(selected_index_float))

    if abs(selected_index_float - selected_k) > 1.0e-10:
        raise ValueError(
            f"{case.name}: no SSPbrick centre lies at z={z}. "
            "Choose NZ such that (k + 0.5)L/NZ = z."
        )

    total_ny = case.ny_lower + case.ny_upper

    def vertical_levels_at(z_value: float) -> tuple[float, ...]:
        """Return all y-levels of the conforming two-region 3D mesh."""
        y_bottom = bottom_ordinate_at(z_value)

        lower_levels = tuple(
            y_bottom
            + (y_interface - y_bottom) * j / case.ny_lower
            for j in range(case.ny_lower + 1)
        )

        upper_levels = tuple(
            y_interface
            + (y_top - y_interface) * j / case.ny_upper
            for j in range(1, case.ny_upper + 1)
        )

        return lower_levels + upper_levels

    ops.wipe()
    ops.model(
        "basic",
        "-ndm", 3,
        "-ndf", 3,
    )

    # Upper material is constant. The lower material is piecewise constant by
    # longitudinal brick layer and samples the exact continuous CSF weight law at
    # that layer centre. Under z refinement this converges to the continuous
    # material-participation field.
    upper_material_tag = 1

    ops.nDMaterial(
        "ElasticIsotropic",
        upper_material_tag,
        E_REF_3D,
        nu,
        RHO_3D,
    )

    lower_material_tag_by_k: dict[int, int] = {}
    lower_modulus_by_k: dict[int, float] = {}

    for k in range(case.nz):
        z_mid = L * (k + 0.5) / case.nz
        material_tag = 1_000 + k
        elastic_modulus = (
            E_REF_3D * lower_weight_at(z_mid)
        )

        ops.nDMaterial(
            "ElasticIsotropic",
            material_tag,
            elastic_modulus,
            nu,
            RHO_3D,
        )

        lower_material_tag_by_k[k] = material_tag
        lower_modulus_by_k[k] = elastic_modulus

    node_tag_by_index: dict[tuple[int, int, int], int] = {}
    node_coordinates: dict[int, tuple[float, float, float]] = {}

    node_tag = 1

    for k in range(case.nz + 1):
        z_node = L * k / case.nz
        y_levels = vertical_levels_at(z_node)

        if len(y_levels) != total_ny + 1:
            raise RuntimeError(
                f"{case.name}: unexpected vertical level count."
            )

        for j, y_node in enumerate(y_levels):
            for i in range(case.nx + 1):
                x_node = (
                    -b / 2.0
                    + b * i / case.nx
                )

                ops.node(
                    node_tag,
                    x_node,
                    y_node,
                    z_node,
                )

                node_tag_by_index[(k, j, i)] = node_tag
                node_coordinates[node_tag] = (
                    x_node,
                    y_node,
                    z_node,
                )
                node_tag += 1

    brick_element_tags: list[int] = []
    selected_metadata: dict[int, dict[str, object]] = {}
    element_tag = 1

    for k in range(case.nz):
        z0_element = L * k / case.nz
        z1_element = L * (k + 1) / case.nz
        z_mid = 0.5 * (z0_element + z1_element)

        y_levels_0 = vertical_levels_at(z0_element)
        y_levels_1 = vertical_levels_at(z1_element)
        y_levels_mid = vertical_levels_at(z_mid)

        for j in range(total_ny):
            is_lower = j < case.ny_lower
            region = (
                "lower_region"
                if is_lower
                else "upper_region"
            )
            polygon_index = 0 if is_lower else 1

            material_tag = (
                lower_material_tag_by_k[k]
                if is_lower
                else upper_material_tag
            )

            elastic_modulus = (
                lower_modulus_by_k[k]
                if is_lower
                else E_REF_3D
            )

            for i in range(case.nx):
                n1 = node_tag_by_index[(k,     j,     i)]
                n2 = node_tag_by_index[(k,     j,     i + 1)]
                n3 = node_tag_by_index[(k,     j + 1, i + 1)]
                n4 = node_tag_by_index[(k,     j + 1, i)]
                n5 = node_tag_by_index[(k + 1, j,     i)]
                n6 = node_tag_by_index[(k + 1, j,     i + 1)]
                n7 = node_tag_by_index[(k + 1, j + 1, i + 1)]
                n8 = node_tag_by_index[(k + 1, j + 1, i)]

                ops.element(
                    "SSPbrick",
                    element_tag,
                    n1, n2, n3, n4,
                    n5, n6, n7, n8,
                    material_tag,
                    0.0, 0.0, 0.0,
                )

                brick_element_tags.append(element_tag)

                if k == selected_k:
                    x0 = (
                        -b / 2.0
                        + b * i / case.nx
                    )
                    x1 = (
                        -b / 2.0
                        + b * (i + 1) / case.nx
                    )
                    x_mid = 0.5 * (x0 + x1)

                    y0_mid = y_levels_mid[j]
                    y1_mid = y_levels_mid[j + 1]
                    y_mid = 0.5 * (
                        y0_mid + y1_mid
                    )

                    area = (
                        (x1 - x0)
                        * (y1_mid - y0_mid)
                    )

                    selected_metadata[element_tag] = {
                        "element_tag": element_tag,
                        "region": region,
                        "polygon_index": polygon_index,
                        "i": i,
                        "j": j,
                        "k": k,
                        "material_tag": material_tag,
                        "elastic_modulus": elastic_modulus,
                        "x": x_mid,
                        "y": y_mid,
                        "z": z_mid,
                        "area": area,
                        "y0_at_z0": y_levels_0[j],
                        "y1_at_z0": y_levels_0[j + 1],
                        "y0_at_z1": y_levels_1[j],
                        "y1_at_z1": y_levels_1[j + 1],
                    }

                element_tag += 1

    # -----------------------------------------------------------------------
    # Support constraints.
    #
    # Both end sections are supported against global y translation. The
    # centreline x DOFs are fixed to suppress the rigid x mode while preserving
    # width-direction Poisson deformation. One z DOF is fixed to remove the
    # remaining longitudinal rigid-body mode.
    # -----------------------------------------------------------------------

    fixity_by_node: dict[int, list[int]] = {
        tag: [0, 0, 0]
        for tag in node_coordinates
    }

    left_support_nodes: list[int] = []
    right_support_nodes: list[int] = []

    for j in range(total_ny + 1):
        for i in range(case.nx + 1):
            left_tag = node_tag_by_index[(0, j, i)]
            right_tag = node_tag_by_index[(case.nz, j, i)]

            fixity_by_node[left_tag][1] = 1
            fixity_by_node[right_tag][1] = 1

            left_support_nodes.append(left_tag)
            right_support_nodes.append(right_tag)

    mid_width_index = case.nx // 2

    for k in range(case.nz + 1):
        for j in range(total_ny + 1):
            centreline_tag = node_tag_by_index[
                (k, j, mid_width_index)
            ]
            fixity_by_node[centreline_tag][0] = 1

    anchor_tag = node_tag_by_index[
        (0, case.ny_lower, mid_width_index)
    ]
    fixity_by_node[anchor_tag][2] = 1

    for tag, fixity in fixity_by_node.items():
        if any(fixity):
            ops.fix(
                tag,
                *fixity,
            )

    # -----------------------------------------------------------------------
    # UDL as a top-surface pressure.
    #
    # Since the section width is b, the pressure magnitude q/b integrates to
    # exactly q per unit beam length.
    # -----------------------------------------------------------------------

    ops.timeSeries(
        "Linear",
        1,
    )
    ops.pattern(
        "Plain",
        1,
        1,
    )

    pressure = q / b
    top_level_index = total_ny
    surface_element_count = 0

    for k in range(case.nz):
        for i in range(case.nx):
            s1 = node_tag_by_index[
                (k,     top_level_index, i)
            ]
            s2 = node_tag_by_index[
                (k + 1, top_level_index, i)
            ]
            s3 = node_tag_by_index[
                (k + 1, top_level_index, i + 1)
            ]
            s4 = node_tag_by_index[
                (k,     top_level_index, i + 1)
            ]

            ops.element(
                "SurfaceLoad",
                element_tag,
                s1, s2, s3, s4,
                pressure,
            )

            element_tag += 1
            surface_element_count += 1

    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system("UmfPack")
    ops.integrator(
        "LoadControl",
        1.0,
    )
    ops.algorithm("Linear")
    ops.analysis("Static")

    analysis_code = ops.analyze(1)

    if analysis_code != 0:
        raise RuntimeError(
            f"{case.name}: OpenSees static analysis failed "
            f"with code {analysis_code}."
        )

    # -----------------------------------------------------------------------
    # Reactions: an independent global equilibrium check.
    # -----------------------------------------------------------------------

    ops.reactions()

    left_reaction_y = sum(
        float(ops.nodeReaction(tag, 2))
        for tag in left_support_nodes
    )
    right_reaction_y = sum(
        float(ops.nodeReaction(tag, 2))
        for tag in right_support_nodes
    )

    total_reaction_y = (
        left_reaction_y + right_reaction_y
    )

    # OpenSees reaction sign convention for the SurfaceLoad orientation used
    # above is opposite to the positive beam-load/resultant convention adopted
    # by this benchmark. This is the same convention already verified in the
    # preceding SSPbrick benchmark:
    #
    #     applied UDL magnitude in the beam convention : +q
    #     total OpenSees support reaction in global y  : -q * L
    #
    # The sign difference is therefore a convention difference, not a failure
    # of global equilibrium. Do not reverse the SurfaceLoad merely to make this
    # diagnostic positive: the present element orientation is the one for which
    # the recovered SSPbrick Mx and Ty components were previously validated
    # against the analytical beam resultants.
    expected_total_reaction_y = -q * L

    reaction_relative_error = abs(
        total_reaction_y
        - expected_total_reaction_y
    ) / abs(expected_total_reaction_y)

    if reaction_relative_error > REACTION_RELATIVE_TOLERANCE:
        raise RuntimeError(
            f"{case.name}: support-reaction equilibrium failed: "
            f"relative error={reaction_relative_error:.6e}."
        )

    # -----------------------------------------------------------------------
    # Recover the six SSPbrick stress components at the selected layer.
    #
    # OpenSees ElasticIsotropic / SSPbrick returns:
    #
    #   [sigma_xx, sigma_yy, sigma_zz, tau_xy, tau_yz, tau_zx].
    #
    # The constitutive reconstruction below independently verifies that this
    # component interpretation is internally consistent.
    # -----------------------------------------------------------------------

    raw_rows: list[dict[str, object]] = []
    maximum_constitutive_difference = 0.0
    maximum_stress_scale = 0.0

    for current_element_tag, metadata in selected_metadata.items():
        stress = tuple(
            float(value)
            for value in ops.eleResponse(
                int(current_element_tag),
                "stress",
            )
        )
        strain = tuple(
            float(value)
            for value in ops.eleResponse(
                int(current_element_tag),
                "strain",
            )
        )

        if len(stress) != 6 or len(strain) != 6:
            raise RuntimeError(
                f"{case.name}: SSPbrick {current_element_tag} returned "
                f"{len(stress)} stresses and {len(strain)} strains; "
                "six were expected."
            )

        E_value = float(metadata["elastic_modulus"])
        G_value = E_value / (
            2.0 * (1.0 + nu)
        )
        lame_lambda = (
            E_value * nu
            / (
                (1.0 + nu)
                * (1.0 - 2.0 * nu)
            )
        )

        trace_strain = (
            strain[0]
            + strain[1]
            + strain[2]
        )

        stress_from_strain = (
            2.0 * G_value * strain[0]
            + lame_lambda * trace_strain,
            2.0 * G_value * strain[1]
            + lame_lambda * trace_strain,
            2.0 * G_value * strain[2]
            + lame_lambda * trace_strain,
            G_value * strain[3],
            G_value * strain[4],
            G_value * strain[5],
        )

        constitutive_difference = max(
            abs(
                stress[index]
                - stress_from_strain[index]
            )
            for index in range(6)
        )

        maximum_constitutive_difference = max(
            maximum_constitutive_difference,
            constitutive_difference,
        )
        maximum_stress_scale = max(
            maximum_stress_scale,
            max(abs(value) for value in stress),
        )

        raw_rows.append(
            {
                **metadata,
                "sigma_xx_3d": stress[0],
                "sigma_yy_3d": stress[1],
                "sigma_zz_3d": stress[2],
                "tau_xy_3d": stress[3],
                "tau_yz_3d": stress[4],
                "tau_zx_3d": stress[5],
                "epsilon_xx_3d": strain[0],
                "epsilon_yy_3d": strain[1],
                "epsilon_zz_3d": strain[2],
                "gamma_xy_3d": strain[3],
                "gamma_yz_3d": strain[4],
                "gamma_zx_3d": strain[5],
                "constitutive_max_difference": constitutive_difference,
            }
        )

    constitutive_relative_difference = (
        maximum_constitutive_difference
        / max(1.0, maximum_stress_scale)
    )

    if (
        constitutive_relative_difference
        > CONSTITUTIVE_RELATIVE_TOLERANCE
    ):
        raise RuntimeError(
            f"{case.name}: constitutive stress reconstruction failed: "
            f"relative difference={constitutive_relative_difference:.6e}."
        )

    # -----------------------------------------------------------------------
    # Reconstruct 3D section resultants.
    #
    # These are direct area integrals of the physical continuum stresses. No
    # CSF weight is applied here because the material participation is already
    # present in the OpenSees constitutive stress itself.
    # -----------------------------------------------------------------------

    section_analysis = section_full_analysis(
        field.section(z),
        compute_vroark=False,
    )

    Cx = float(section_analysis["Cx"])
    Cy = float(section_analysis["Cy"])

    N_3d = area_integral(
        raw_rows,
        "sigma_zz_3d",
    )

    Mx_3d = sum(
        float(row["area"])
        * float(row["sigma_zz_3d"])
        * (float(row["y"]) - Cy)
        for row in raw_rows
    )

    My_3d = sum(
        float(row["area"])
        * float(row["sigma_zz_3d"])
        * (float(row["x"]) - Cx)
        for row in raw_rows
    )

    Tx_3d = area_integral(
        raw_rows,
        "tau_zx_3d",
    )
    Ty_3d = area_integral(
        raw_rows,
        "tau_yz_3d",
    )

    # -----------------------------------------------------------------------
    # Same-point CSF evaluation.
    #
    # The local potential has already been solved independently. Here it is
    # merely sampled at the exact SSPbrick-centre coordinates.
    # -----------------------------------------------------------------------

    comparison_rows: list[dict[str, object]] = []

    analytical_actions = actions_at(z)

    for raw_row in raw_rows:
        x_value = float(raw_row["x"])
        y_value = float(raw_row["y"])
        polygon_index = int(raw_row["polygon_index"])

        sigma_csf = navier_point_stress(
            z_value=z,
            x_value=x_value,
            y_value=y_value,
            polygon_index=polygon_index,
            N_value=analytical_actions[0],
            Mx_value=analytical_actions[1],
            My_value=analytical_actions[2],
        )

        (
            tau_x_csf,
            tau_y_csf,
            potential_triangle_hits,
        ) = potential_evaluator.evaluate(
            x_value,
            y_value,
        )

        comparison_rows.append(
            {
                **raw_row,
                "N_input": analytical_actions[0],
                "Mx_input": analytical_actions[1],
                "My_input": analytical_actions[2],
                "Tx_input": analytical_actions[3],
                "Ty_input": analytical_actions[4],
                "N_3d_reconstructed": N_3d,
                "Mx_3d_reconstructed": Mx_3d,
                "My_3d_reconstructed": My_3d,
                "Tx_3d_reconstructed": Tx_3d,
                "Ty_3d_reconstructed": Ty_3d,
                "sigma_zz_csf": sigma_csf,
                "tau_x_potential_csf": tau_x_csf,
                "tau_y_potential_csf": tau_y_csf,
                "potential_triangle_hits": potential_triangle_hits,
            }
        )

    # -----------------------------------------------------------------------
    # Pointwise error metrics.
    # -----------------------------------------------------------------------

    sigma_l2 = normalized_l2_error(
        comparison_rows,
        prediction_key="sigma_zz_csf",
        reference_key="sigma_zz_3d",
    )
    sigma_max = normalized_max_error(
        comparison_rows,
        prediction_key="sigma_zz_csf",
        reference_key="sigma_zz_3d",
    )

    tau_y_l2 = normalized_l2_error(
        comparison_rows,
        prediction_key="tau_y_potential_csf",
        reference_key="tau_yz_3d",
    )
    tau_y_max = normalized_max_error(
        comparison_rows,
        prediction_key="tau_y_potential_csf",
        reference_key="tau_yz_3d",
    )

    tau_vector_l2 = normalized_vector_l2_error(
        comparison_rows
    )
    tau_vector_max = normalized_vector_max_error(
        comparison_rows
    )

    max_abs_tau_x_3d = max(
        abs(float(row["tau_zx_3d"]))
        for row in comparison_rows
    )
    max_abs_tau_x_csf = max(
        abs(float(row["tau_x_potential_csf"]))
        for row in comparison_rows
    )

    max_abs_tau_y_3d = max(
        abs(float(row["tau_yz_3d"]))
        for row in comparison_rows
    )
    max_abs_tau_y_csf = max(
        abs(float(row["tau_y_potential_csf"]))
        for row in comparison_rows
    )

    tau_y_3d_x_spread = maximum_x_spread_at_equal_y(
        comparison_rows,
        "tau_yz_3d",
    )
    tau_y_csf_x_spread = maximum_x_spread_at_equal_y(
        comparison_rows,
        "tau_y_potential_csf",
    )

    # Midpoint integration of the CSF values at the 3D sampling grid is reported
    # separately from the exact area integration already returned by the
    # potential core. This exposes only sampling/discretization error.
    Tx_csf_sampled = area_integral(
        comparison_rows,
        "tau_x_potential_csf",
    )
    Ty_csf_sampled = area_integral(
        comparison_rows,
        "tau_y_potential_csf",
    )

    detailed_csv = (
        OUTPUT_DIRECTORY
        / f"comparison_{case.name}.csv"
    )

    with detailed_csv.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(
                comparison_rows[0].keys()
            ),
        )
        writer.writeheader()
        writer.writerows(comparison_rows)

    print(f"\nCASE: {case.name}")
    print(f"  purpose             : {case.purpose}")
    print(
        f"  mesh                : nx={case.nx}, "
        f"ny_lower={case.ny_lower}, ny_upper={case.ny_upper}, "
        f"nz={case.nz}"
    )
    print(
        f"  selected SSPbricks  : {len(comparison_rows)}"
    )
    print(
        "  3D resultants       : "
        f"N={N_3d:.9e} N, "
        f"Mx={Mx_3d:.9e} N m, "
        f"My={My_3d:.9e} N m, "
        f"Tx={Tx_3d:.9e} N, "
        f"Ty={Ty_3d:.9e} N"
    )
    print(
        "  prescribed actions  : "
        f"N={N:.9e} N, "
        f"Mx={Mx:.9e} N m, "
        f"My={My:.9e} N m, "
        f"Tx={Tx:.9e} N, "
        f"Ty={Ty:.9e} N"
    )
    print(
        "  stress errors       : "
        f"sigma_L2={sigma_l2:.9e}, "
        f"tau_y_L2={tau_y_l2:.9e}, "
        f"tau_vector_L2={tau_vector_l2:.9e}"
    )
    print(
        "  max errors          : "
        f"sigma={sigma_max:.9e}, "
        f"tau_y={tau_y_max:.9e}, "
        f"tau_vector={tau_vector_max:.9e}"
    )
    print(
        "  through-width tau_y : "
        f"CSF spread={tau_y_csf_x_spread:.6e} Pa, "
        f"3D spread={tau_y_3d_x_spread:.6e} Pa"
    )

    return {
        "case": case,
        "brick_count": len(brick_element_tags),
        "surface_count": surface_element_count,
        "selected_count": len(comparison_rows),
        "N_3d": N_3d,
        "Mx_3d": Mx_3d,
        "My_3d": My_3d,
        "Tx_3d": Tx_3d,
        "Ty_3d": Ty_3d,
        "Tx_csf_exact": float(
            potential_result["resultants"]["Tx_recovered"]
        ),
        "Ty_csf_exact": float(
            potential_result["resultants"]["Ty_recovered"]
        ),
        "Tx_csf_sampled": Tx_csf_sampled,
        "Ty_csf_sampled": Ty_csf_sampled,
        "sigma_l2": sigma_l2,
        "sigma_max": sigma_max,
        "tau_y_l2": tau_y_l2,
        "tau_y_max": tau_y_max,
        "tau_vector_l2": tau_vector_l2,
        "tau_vector_max": tau_vector_max,
        "max_abs_tau_x_3d": max_abs_tau_x_3d,
        "max_abs_tau_x_csf": max_abs_tau_x_csf,
        "max_abs_tau_y_3d": max_abs_tau_y_3d,
        "max_abs_tau_y_csf": max_abs_tau_y_csf,
        "tau_y_3d_x_spread": tau_y_3d_x_spread,
        "tau_y_csf_x_spread": tau_y_csf_x_spread,
        "constitutive_relative_difference": constitutive_relative_difference,
        "left_reaction_y": left_reaction_y,
        "right_reaction_y": right_reaction_y,
        "reaction_relative_error": reaction_relative_error,
        "detailed_csv": str(detailed_csv),
    }


# ---------------------------------------------------------------------------
# 9. OUTPUT OF THE INDEPENDENT CSF POTENTIAL SOLUTION
# ---------------------------------------------------------------------------


def write_potential_outputs(
    potential_result: dict[str, object],
) -> None:
    """Write the exact CSF potential mesh/resultants used by every 3D case."""
    triangle_rows = potential_result["triangles"]

    with POTENTIAL_TRIANGLES_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(triangle_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(triangle_rows)

    summary_row = {
        "z": z,
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
        "derivative_step": potential_result["derivative"]["step"],
        "derivative_scheme": potential_result["derivative"]["scheme"],
        "mesh_refinements": potential_result["mesh"]["refinements"],
        "node_count": potential_result["mesh"]["node_count"],
        "triangle_count": potential_result["mesh"]["triangle_count"],
        "connected_components": potential_result["mesh"]["connected_components"],
        "Tx_recovered": potential_result["resultants"]["Tx_recovered"],
        "Ty_recovered": potential_result["resultants"]["Ty_recovered"],
        "Tx_error": potential_result["resultants"]["Tx_error"],
        "Ty_error": potential_result["resultants"]["Ty_error"],
        "global_compatibility_residual": potential_result["equilibrium"][
            "global_compatibility_residual"
        ],
        "max_component_compatibility_residual": potential_result["equilibrium"][
            "max_component_compatibility_residual"
        ],
        "linear_residual_inf": potential_result["equilibrium"][
            "linear_residual_inf"
        ],
    }

    with POTENTIAL_SUMMARY_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(summary_row.keys()),
        )
        writer.writeheader()
        writer.writerow(summary_row)


# ---------------------------------------------------------------------------
# 10. FULL CONTROLLED 3D MESH SUITE
# ---------------------------------------------------------------------------


def run_mesh_suite(
    *,
    potential_result: dict[str, object],
    potential_evaluator: PotentialFieldEvaluator,
) -> list[dict[str, object]]:
    """Run every independent 3D mesh and write one machine-readable summary."""
    results = [
        run_opensees_case(
            case,
            potential_result=potential_result,
            potential_evaluator=potential_evaluator,
        )
        for case in MESH_CASES
    ]

    summary_rows: list[dict[str, object]] = []

    for result in results:
        case = result["case"]

        summary_rows.append(
            {
                "case": case.name,
                "purpose": case.purpose,
                "nx": case.nx,
                "ny_lower": case.ny_lower,
                "ny_upper": case.ny_upper,
                "nz": case.nz,
                "brick_count": result["brick_count"],
                "selected_count": result["selected_count"],
                "N_3d": result["N_3d"],
                "Mx_3d": result["Mx_3d"],
                "My_3d": result["My_3d"],
                "Tx_3d": result["Tx_3d"],
                "Ty_3d": result["Ty_3d"],
                "N_input": N,
                "Mx_input": Mx,
                "My_input": My,
                "Tx_input": Tx,
                "Ty_input": Ty,
                "Tx_csf_exact": result["Tx_csf_exact"],
                "Ty_csf_exact": result["Ty_csf_exact"],
                "Tx_csf_sampled": result["Tx_csf_sampled"],
                "Ty_csf_sampled": result["Ty_csf_sampled"],
                "sigma_l2": result["sigma_l2"],
                "sigma_max": result["sigma_max"],
                "tau_y_l2": result["tau_y_l2"],
                "tau_y_max": result["tau_y_max"],
                "tau_vector_l2": result["tau_vector_l2"],
                "tau_vector_max": result["tau_vector_max"],
                "max_abs_tau_x_3d": result["max_abs_tau_x_3d"],
                "max_abs_tau_x_csf": result["max_abs_tau_x_csf"],
                "max_abs_tau_y_3d": result["max_abs_tau_y_3d"],
                "max_abs_tau_y_csf": result["max_abs_tau_y_csf"],
                "tau_y_3d_x_spread": result["tau_y_3d_x_spread"],
                "tau_y_csf_x_spread": result["tau_y_csf_x_spread"],
                "constitutive_relative_difference": result[
                    "constitutive_relative_difference"
                ],
                "left_reaction_y": result["left_reaction_y"],
                "right_reaction_y": result["right_reaction_y"],
                "reaction_relative_error": result["reaction_relative_error"],
                "detailed_csv": result["detailed_csv"],
            }
        )

    with SUMMARY_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(summary_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print("\nMESH COMPARISON SUMMARY")
    print(
        "case              sigma_L2       tau_y_L2       tau_vec_L2     "
        "tau_y_max      Ty_3D [N]"
    )

    for row in summary_rows:
        print(
            f"{str(row['case']):<17} "
            f"{float(row['sigma_l2']):.6e}  "
            f"{float(row['tau_y_l2']):.6e}  "
            f"{float(row['tau_vector_l2']):.6e}  "
            f"{float(row['tau_y_max']):.6e}  "
            f"{float(row['Ty_3d']):.6e}"
        )

    coarse = summary_rows[0]
    combined = summary_rows[-1]

    print("\nCOARSE -> COMBINED-REFINED CHANGE")
    print(
        f"sigma_L2 : {float(coarse['sigma_l2']):.6e} "
        f"-> {float(combined['sigma_l2']):.6e}"
    )
    print(
        f"tau_y_L2 : {float(coarse['tau_y_l2']):.6e} "
        f"-> {float(combined['tau_y_l2']):.6e}"
    )
    print(
        f"tau_vec_L2: {float(coarse['tau_vector_l2']):.6e} "
        f"-> {float(combined['tau_vector_l2']):.6e}"
    )

    print(
        "\nNo CSF-vs-3D error threshold is imposed here. "
        "The mesh trend above is the benchmark result."
    )
    print(f"Summary written to: {SUMMARY_CSV}")

    return summary_rows


# ---------------------------------------------------------------------------
# 11. DRIVER
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the independent CSF field and the complete OpenSees 3D mesh suite."""
    require_opensees()
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    section_at_z = field.section(z)
    properties = section_properties(section_at_z)

    print("DEFINITIVE CSF LOCAL-POTENTIAL / OPENSEES 3D BENCHMARK")
    print(f"Span L = {L:.6f} m")
    print(f"UDL q = {q:.9e} N/m")
    print(f"Selected station z = {z:.6f} m")
    print(
        "Section properties: "
        f"A={float(properties['A']):.12e} m^2, "
        f"Ix={float(properties['Ix']):.12e} m^4, "
        f"Iy={float(properties['Iy']):.12e} m^4, "
        f"Ixy={float(properties['Ixy']):.12e} m^4"
    )
    print(
        "Prescribed section actions: "
        f"N={N:.9e} N, "
        f"Mx={Mx:.9e} N m, "
        f"My={My:.9e} N m, "
        f"Tx={Tx:.9e} N, "
        f"Ty={Ty:.9e} N"
    )

    print("\nINTERPOLATED PARTICIPATION AT z")
    for polygon in section_at_z.polygons:
        print(
            f"{polygon.name}: "
            f"weight={float(polygon.weightabs):.9e}, "
            f"shear_weight={float(polygon.shear_weightabs):.9e}"
        )

    print("\nSOLVING INDEPENDENT CSF LOCAL SHEAR-POTENTIAL FIELD")
    potential_result = solve_reference_potential()

    print(
        "Potential mesh: "
        f"refinements={potential_result['mesh']['refinements']}, "
        f"nodes={potential_result['mesh']['node_count']}, "
        f"triangles={potential_result['mesh']['triangle_count']}"
    )
    print(
        "Potential resultants: "
        f"Tx={float(potential_result['resultants']['Tx_recovered']):.12e} N, "
        f"Ty={float(potential_result['resultants']['Ty_recovered']):.12e} N"
    )
    print(
        "Potential equilibrium: "
        f"global compatibility="
        f"{float(potential_result['equilibrium']['global_compatibility_residual']):.12e}, "
        f"linear residual="
        f"{float(potential_result['equilibrium']['linear_residual_inf']):.12e}"
    )

    write_potential_outputs(
        potential_result
    )

    potential_evaluator = PotentialFieldEvaluator(
        potential_result["triangles"]
    )

    try:
        run_mesh_suite(
            potential_result=potential_result,
            potential_evaluator=potential_evaluator,
        )
    finally:
        # OpenSees keeps a global domain. Always release it, including when a
        # diagnostic check raises an exception part-way through the suite.
        if ops is not None:
            ops.wipe()


if __name__ == "__main__":
    main()

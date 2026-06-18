"""
CSF / OpenSeesPy controlled model-comparison laboratory
=======================================================

This script compares uniform OpenSees beam discretizations generated from the
same CSF continuous section field loaded from YAML.

The script is intentionally written as a controlled research script, not as a
general-purpose application. The main priority is readability of the modelling
path:

    CSF field
        -> sampled section records
        -> OpenSees beam model
        -> element-end and nodal-trace resultants
        -> CSV/report/tip-response plots

The comments document the modelling choices directly where they are made.

Run example
-----------

    python openseeslab_paper_readable_separated.py NREL-5-MW.yaml --gauss-points 2
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import yaml

from csf import ContinuousSectionField, section_full_analysis
from csf.io.csf_issues import CSFIssues
from csf.io.csf_reader import CSFReader


# =====================================================================
# USER-CONTROLLED NUMERICAL CASE
# =====================================================================

# Uniform mesh densities used in the convergence comparison.
# These values are part of the benchmark definition, not hidden runtime defaults.
ELEMENT_COUNTS: Tuple[int, ...] = (4, 6, 8, 12, 16, 24, 32)

# Loads used in the static cantilever case.
# They define the numerical experiment and are therefore stated as constants.
FY_TIP = 1.2e6   # Concentrated transverse tip force applied at the reference tip node.
FZ_TIP = -5.0e6  # Concentrated axial tip force applied at the reference tip node.
MX_TIP = 8.0e6   # Concentrated bending moment about global X.
MZ_TIP = 3.0e6   # Concentrated torsional moment about global Z.
WY_DIST = 8.0e3  # Uniform distributed load in the OpenSees local transverse direction.

# CSF provides the section quantities already in the stiffness scale selected for
# this comparison. OpenSees therefore receives unit material scalars in the
# Elastic section definition. This is a deliberate CSF-to-OpenSees projection,
# not a claim that the physical material has E = G = 1.
E_OPENSEES_UNIT = 1.0
G_OPENSEES_UNIT = 1.0


# =====================================================================
# DATA STRUCTURES
# =====================================================================

@dataclass
class SectionRecord:
    """One CSF-evaluated section mapped to one OpenSees section definition."""

    tag: int
    z: float
    A: float
    Iz: float
    Iy: float
    J: float
    xc: float
    yc: float


@dataclass
class CSFOpenSeesProjection:
    """Data produced by CSF and consumed by OpenSees.

    This object is the interface between the CSF model and the OpenSees model.
    OpenSees does not query the CSF field directly; it only receives sampled
    section records, station nodes, and integration-rule data.
    """

    z_nodes: np.ndarray
    z_gauss: np.ndarray
    gauss_xi: np.ndarray
    gauss_w: np.ndarray
    node_sections: List[SectionRecord]
    integration_sections: List[SectionRecord]
    n_section_calls: int


@dataclass
class ElementEndResultants:
    """OpenSees element-end resultants for one beam element.

    N and MT are signed projections along the element axis.
    T and MB are transverse vector magnitudes and are therefore non-negative.

    The values are kept at element ends. Internal-node values are not averaged.
    """

    element_id: int
    z_i: float
    z_j: float
    N_i: float
    T_i: float
    MB_i: float
    MT_i: float
    N_j: float
    T_j: float
    MB_j: float
    MT_j: float


@dataclass
class NodalTraceResultants:
    """One-sided element traces at a station node.

    At an internal node there are two OpenSees traces:
      - left  trace: right end of the previous element;
      - right trace: left end of the next element.

    Boundary nodes have only one trace. The script reports the two traces and
    their algebraic difference when both are available. It does not create a
    single nodal value by arithmetic averaging.
    """

    z_node: float
    N_left: Optional[float]
    N_right: Optional[float]
    N_jump: Optional[float]
    T_left: Optional[float]
    T_right: Optional[float]
    T_jump: Optional[float]
    MB_left: Optional[float]
    MB_right: Optional[float]
    MB_jump: Optional[float]
    MT_left: Optional[float]
    MT_right: Optional[float]
    MT_jump: Optional[float]


@dataclass
class ModelResult:
    """OpenSees result for one uniform discretization."""

    model_id: str
    label: str
    n_elems: int
    n_section_calls: int
    uy_tip: float
    rz_tip: float
    element_ends: List[ElementEndResultants]
    nodal_traces: List[NodalTraceResultants]


# =====================================================================
# 1. COMMAND-LINE INPUTS
# =====================================================================

def parse_args() -> argparse.Namespace:
    """Read explicit experiment inputs from the command line.

    The YAML file and the Gauss rule are required inputs. The run command then
    records the numerical experiment instead of relying on hidden defaults.
    """
    parser = argparse.ArgumentParser(
        description="Run the CSF/OpenSees controlled model-comparison laboratory."
    )

    parser.add_argument(
        "yaml",
        type=Path,
        help="CSF YAML input file.",
    )

    parser.add_argument(
        "--gauss-points",
        type=int,
        required=True,
        help="Number of Gauss integration points per OpenSees element.",
    )

    args = parser.parse_args()

    if args.gauss_points < 1:
        raise ValueError(f"--gauss-points must be >= 1. Got: {args.gauss_points}.")

    return args


# =====================================================================
# 2. CSF MODEL LOADING AND INPUT SUMMARY
# =====================================================================

def load_yaml_data(path: Path) -> Dict[str, Any]:
    """Load raw YAML data for the human-readable input summary."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def polygon_radii(vertices: List[List[float]]) -> Tuple[float, float]:
    """Return minimum and maximum radius from polygon vertices."""
    radii = [float(np.hypot(float(v[0]), float(v[1]))) for v in vertices]

    if not radii:
        raise ValueError("Polygon has no vertices.")

    return min(radii), max(radii)


def print_csf_opensees_input_summary(yaml_file: Path, gauss_points: int) -> None:
    """Print the model inputs that control the CSF-to-OpenSees projection.

    This summary is intentionally descriptive. It helps the reviewer connect the
    YAML input, the CSF section field, and the OpenSees sampling rule.
    """
    data = load_yaml_data(yaml_file)
    csf = data["CSF"]

    s0 = csf["sections"]["S0"]
    s1 = csf["sections"]["S1"]

    z0 = float(s0["z"])
    z1 = float(s1["z"])
    L = abs(z1 - z0)

    # The NREL tower benchmark uses one closed-cell polygon at each endpoint
    # section. This summary is intentionally tied to that controlled case.
    poly0 = next(iter(s0["polygons"].values()))
    poly1 = next(iter(s1["polygons"].values()))

    ri0, ro0 = polygon_radii(poly0["vertices"])
    ri1, ro1 = polygon_radii(poly1["vertices"])

    weight_laws = csf.get("weight_laws", [])
    shear_weight_laws = csf.get("shear_weight_laws", [])

    lines: List[str] = []
    lines.append("")
    lines.append("CSF / OPENSEES MODEL INPUT")
    lines.append("=" * 78)
    lines.append(f"YAML file                  : {yaml_file}")
    lines.append(f"L                          : {L:.12e}")

    lines.append("")
    lines.append("Geometry")
    lines.append("-" * 78)
    lines.append(f"R_OUTER_BASE               : {ro0:.12e}")
    lines.append(f"R_OUTER_TOP                : {ro1:.12e}")
    lines.append(f"R_INNER_BASE               : {ri0:.12e}")
    lines.append(f"R_INNER_TOP                : {ri1:.12e}")

    lines.append("")
    lines.append("Weight laws")
    lines.append("-" * 78)
    if weight_laws:
        lines.extend(str(law) for law in weight_laws)
    else:
        lines.append("<none>")

    lines.append("")
    lines.append("Shear-weight laws")
    lines.append("-" * 78)
    if shear_weight_laws:
        lines.extend(str(law) for law in shear_weight_laws)
    else:
        lines.append("<none>")

    lines.append("")
    lines.append("CSF to OpenSees projection")
    lines.append("-" * 78)
    lines.append("Section integration rule   : Gauss-Legendre")
    lines.append(f"Gauss points per element   : {gauss_points:d}")
    lines.append("OpenSees E scalar          : 1.0")
    lines.append("OpenSees G scalar          : 1.0")
    lines.append("")

    print("\n".join(lines))


def build_section_field(yaml_file: Path) -> ContinuousSectionField:
    """Load the CSF member from YAML.

    The loaded object is the authoritative CSF model. Its public length property
    `L` is used later instead of reconstructing the length externally.
    """
    res = CSFReader().read_file(str(yaml_file))

    if not res.ok:
        print(CSFIssues.format_report(res.issues))
        raise SystemExit(1)

    return res.field


# =====================================================================
# 3. CSF SAMPLING AND PROJECTION DATA
# =====================================================================

def make_uniform_station_nodes(L: float, n_elems: int) -> np.ndarray:
    """Return uniformly spaced physical station nodes over [0, L]."""
    if n_elems < 1:
        raise ValueError(f"n_elems must be >= 1. Got: {n_elems}.")

    return np.linspace(0.0, float(L), n_elems + 1)


def gauss_points_on_station_mesh(
    z_nodes: np.ndarray,
    n_gauss_points: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return Gauss point coordinates, normalized locations, and weights.

    Physical station nodes are not changed by the integration rule. Gauss points
    are internal element sampling stations used to build element stiffness.
    """
    xi_raw, w_raw = np.polynomial.legendre.leggauss(n_gauss_points)
    gauss_xi = 0.5 * (xi_raw + 1.0)
    gauss_w = 0.5 * w_raw

    z_gauss: List[float] = []
    for zi, zj in zip(z_nodes[:-1], z_nodes[1:]):
        h = float(zj - zi)
        for xi in gauss_xi:
            z_gauss.append(float(zi + float(xi) * h))

    return np.asarray(z_gauss, dtype=float), gauss_xi, gauss_w


def sample_section_record(section_field: ContinuousSectionField, z: float, tag: int) -> SectionRecord:

    """Evaluate CSF at one station and create an OpenSees section record.

    The analysis keys are used directly. This is intentional: the script knows
    the CSF API and does not probe alternative names as if the model were an
    unknown external object.
    """
    sec = section_field.section(float(z))
    analysis = section_full_analysis(sec)

    A = float(analysis["A"])
    Iz = float(analysis["Ix"])
    Iy = float(analysis["Iy"])

    # For this single closed-cell polygon case, CSF returns J_sv_cell as
    # (J_sv_cell, t), where t is the cell wall thickness used by the torsion
    # calculation. OpenSees Elastic section requires only the torsional constant J.
    J = float(analysis["J_sv_cell"][0])

    xc = float(analysis["Cx"])
    yc = float(analysis["Cy"])

    return SectionRecord(tag=tag, z=float(z), A=A, Iz=Iz, Iy=Iy, J=J, xc=xc, yc=yc)

    sec = section_field.section(float(z))
    analysis = section_full_analysis(sec)

    A = float(analysis["A"])
    Iz = float(analysis["Ix"])
    Iy = float(analysis["Iy"])
    # For this single closed-cell polygon case, CSF returns J_sv_cell as a tuple.
    # The first entry is the Saint-Venant torsional constant required by the
    # OpenSees Elastic section; the remaining tuple data are not used here.    
    J =  float(analysis["J_sv_cell"][0])
    xc = float(analysis["Cx"])
    yc = float(analysis["Cy"])

    return SectionRecord(tag=tag, z=float(z), A=A, Iz=Iz, Iy=Iy, J=J, xc=xc, yc=yc)


def sample_sections(section_field: ContinuousSectionField, z_values: np.ndarray, tag0: int) -> List[SectionRecord]:
    """Sample all requested CSF sections."""
    return [sample_section_record(section_field, float(z), tag0 + i) for i, z in enumerate(z_values)]


def build_csf_opensees_projection(
    section_field: ContinuousSectionField,
    n_elems: int,
    n_gauss_points: int,
) -> CSFOpenSeesProjection:
    """Build the complete CSF data package consumed by one OpenSees model.

    This function is the end of the CSF side of the workflow. It samples the
    continuous section field at physical station nodes and at Gauss integration
    points, then returns plain records for OpenSees to consume.
    """
    L = float(section_field.L)
    z_nodes = make_uniform_station_nodes(L, n_elems)
    z_gauss, gauss_xi, gauss_w = gauss_points_on_station_mesh(z_nodes, n_gauss_points)

    # Node sections define the centroidal axis geometry.
    node_sections = sample_sections(section_field, z_nodes, tag0=100000)

    # Integration sections define the element stiffness through OpenSees
    # UserDefined beamIntegration.
    integration_sections = sample_sections(section_field, z_gauss, tag0=1)

    n_section_calls = int(len(node_sections) + len(integration_sections))

    return CSFOpenSeesProjection(
        z_nodes=z_nodes,
        z_gauss=z_gauss,
        gauss_xi=gauss_xi,
        gauss_w=gauss_w,
        node_sections=node_sections,
        integration_sections=integration_sections,
        n_section_calls=n_section_calls,
    )


# =====================================================================
# 4. OPENSEES MODEL BUILDING AND SOLUTION
# =====================================================================

def build_local_basis(axis_e3: np.ndarray, vecxz: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a right-handed local basis from the member axis and reference vector.

    The local basis is used to place centroidal nodes from CSF centroid offsets.
    The same reference direction also makes the OpenSees transverse load
    orientation explicit.
    """
    e3 = axis_e3 / np.linalg.norm(axis_e3)

    v = np.asarray(vecxz, dtype=float)
    v_perp = v - np.dot(v, e3) * e3

    if np.linalg.norm(v_perp) < 1.0e-10:
        raise ValueError("The reference vector for the local basis is parallel to the member axis.")

    e1 = v_perp / np.linalg.norm(v_perp)
    e2 = np.cross(e3, e1)
    e2 = e2 / np.linalg.norm(e2)

    return e1, e2, e3


def section_xyz(section: SectionRecord, e1: np.ndarray, e2: np.ndarray) -> np.ndarray:
    """Return centroidal node coordinates for one sampled CSF section."""
    ref_xyz = np.array([0.0, 0.0, section.z], dtype=float)
    return ref_xyz + section.xc * e1 + section.yc * e2


def define_opensees_sections(ops, sections: List[SectionRecord]) -> None:
    """Define OpenSees Elastic sections from CSF section records.

    OpenSees receives A, Iz, Iy, and J from CSF. E and G are unit scalars because
    the CSF values have already been projected into the stiffness scale used by
    this comparison.
    """
    for s in sections:
        ops.section(
            "Elastic",
            int(s.tag),
            float(E_OPENSEES_UNIT),
            float(s.A),
            float(s.Iz),
            float(s.Iy),
            float(G_OPENSEES_UNIT),
            float(s.J),
        )


def create_reference_and_centroid_nodes(
    ops,
    node_sections: List[SectionRecord],
    e1: np.ndarray,
    e2: np.ndarray,
) -> Tuple[List[int], List[int], List[np.ndarray]]:
    """Create reference-axis nodes, centroidal nodes, and rigid offsets.

    Loads and boundary conditions are applied on the reference axis. Beam
    elements are placed on the centroidal axis. The rigid links make this choice
    explicit instead of silently merging the two axes.
    """
    ref_nodes: List[int] = []
    cen_nodes: List[int] = []
    cen_xyzs: List[np.ndarray] = []

    for i, sec in enumerate(node_sections):
        ref_tag = 1 + i
        cen_tag = 10000 + i

        ref_xyz = np.array([0.0, 0.0, sec.z], dtype=float)
        cen_xyz = section_xyz(sec, e1, e2)

        ops.node(ref_tag, float(ref_xyz[0]), float(ref_xyz[1]), float(ref_xyz[2]))
        ops.node(cen_tag, float(cen_xyz[0]), float(cen_xyz[1]), float(cen_xyz[2]))

        # Rigid kinematic offset from reference axis to centroidal axis.
        ops.rigidLink("beam", ref_tag, cen_tag)

        ref_nodes.append(ref_tag)
        cen_nodes.append(cen_tag)
        cen_xyzs.append(cen_xyz)

    return ref_nodes, cen_nodes, cen_xyzs


def create_force_beam_column_elements(
    ops,
    projection: CSFOpenSeesProjection,
    cen_nodes: List[int],
    cen_xyzs: List[np.ndarray],
    transf_tag: int,
) -> Tuple[List[int], List[np.ndarray]]:
    """Create forceBeamColumn elements using CSF-sampled Gauss sections."""
    n_elems = int(len(projection.z_nodes) - 1)
    n_ip = int(len(projection.gauss_xi))

    ele_tags: List[int] = []
    element_axes: List[np.ndarray] = []

    for i in range(n_elems):
        ele_tag = i + 1
        int_tag = 20000 + i

        sec_tags = [int(projection.integration_sections[n_ip * i + k].tag) for k in range(n_ip)]

        # UserDefined integration receives section tags, normalized locations,
        # and weights. This is the precise OpenSees mechanism used to project
        # the continuous CSF section field into element stiffness.
        ops.beamIntegration(
            "UserDefined",
            int_tag,
            n_ip,
            *sec_tags,
            *[float(x) for x in projection.gauss_xi],
            *[float(w) for w in projection.gauss_w],
        )

        ops.element("forceBeamColumn", ele_tag, cen_nodes[i], cen_nodes[i + 1], transf_tag, int_tag)

        ele_tags.append(ele_tag)
        element_axes.append(cen_xyzs[i + 1] - cen_xyzs[i])

    return ele_tags, element_axes


def solve_static_case(ops, base_ref_node: int, tip_ref_node: int, ele_tags: List[int]) -> Tuple[float, float, List[List[float]]]:
    """Apply the controlled static case and return tip response plus element forces."""
    ops.fix(int(base_ref_node), 1, 1, 1, 1, 1, 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    # Concentrated loads are applied at the reference-axis tip node. The rigid
    # offset transfers them to the centroidal beam line.
    ops.load(
        int(tip_ref_node),
        0.0,
        float(FY_TIP),
        float(FZ_TIP),
        float(MX_TIP),
        0.0,
        float(MZ_TIP),
    )

    # OpenSees beamUniform loads are element-local loads. WY_DIST is therefore
    # intentionally interpreted in the local transverse direction defined by the
    # geometric transformation, not as an automatically global-Y load.
    for ele_tag in ele_tags:
        ops.eleLoad(
            "-ele",
            int(ele_tag),
            "-type",
            "-beamUniform",
            float(WY_DIST),
            0.0,
            0.0,
        )

    # Linear transformation and static analysis are used because the laboratory
    # checks linear elastic section projection, not P-Delta effects, buckling, or
    # large-displacement kinematics.
    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")

    ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError(f"OpenSees analysis failed with code {ok}.")

    uy_tip = float(ops.nodeDisp(int(tip_ref_node), 2))
    rz_tip = float(ops.nodeDisp(int(tip_ref_node), 6))
    ele_forces = [ops.eleForce(int(ele_tag)) for ele_tag in ele_tags]

    return uy_tip, rz_tip, ele_forces


def run_opensees_model(
    projection: CSFOpenSeesProjection,
    model_id: str,
    label: str,
) -> ModelResult:
    """Build, solve, and post-process one OpenSees model.

    This function is the OpenSees side of the workflow. It receives the already
    sampled CSF projection and does not query the CSF field.
    """
    try:
        import openseespy.opensees as ops
    except Exception as e:
        raise RuntimeError("openseespy is not available. Install openseespy.") from e

    n_elems = int(len(projection.z_nodes) - 1)
    L = float(projection.z_nodes[-1] - projection.z_nodes[0])

    # The member reference axis is aligned with global Z. The reference vector
    # fixes the transverse orientation used to place centroid offsets.
    e1, e2, _ = build_local_basis(
        np.array([0.0, 0.0, L], dtype=float),
        np.array([1.0, 0.0, 0.0], dtype=float),
    )

    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    transf_tag = 1
    ops.geomTransf("Linear", transf_tag, 1.0, 0.0, 0.0)

    define_opensees_sections(ops, projection.integration_sections)

    ref_nodes, cen_nodes, cen_xyzs = create_reference_and_centroid_nodes(
        ops,
        projection.node_sections,
        e1,
        e2,
    )

    ele_tags, element_axes = create_force_beam_column_elements(
        ops,
        projection,
        cen_nodes,
        cen_xyzs,
        transf_tag,
    )

    uy_tip, rz_tip, ele_forces = solve_static_case(ops, ref_nodes[0], ref_nodes[-1], ele_tags)

    element_ends = recover_element_end_resultants(
        z_nodes=projection.z_nodes,
        ele_forces=ele_forces,
        element_axes=element_axes,
        ele_tags=ele_tags,
    )
    nodal_traces = build_nodal_trace_resultants(projection.z_nodes, element_ends)

    print(
        f"[RUN] {label:<24} | "
        f"CSF_section_calls={projection.n_section_calls:d} | "
        f"Uy_tip={uy_tip:.6e} | "
        f"Rz_tip={rz_tip:.6e} rad"
    )

    return ModelResult(
        model_id=model_id,
        label=label,
        n_elems=n_elems,
        n_section_calls=projection.n_section_calls,
        uy_tip=uy_tip,
        rz_tip=rz_tip,
        element_ends=element_ends,
        nodal_traces=nodal_traces,
    )


# =====================================================================
# 5. ELEMENT-END AND NODAL-TRACE RESULTANTS
# =====================================================================

def _project_force_components(force_vec: np.ndarray, axis: np.ndarray) -> Tuple[float, float]:
    """Project a 3D force vector into axial and transverse components."""
    e = axis / np.linalg.norm(axis)
    n = float(np.dot(force_vec, e))
    t_vec = force_vec - n * e
    t = float(np.linalg.norm(t_vec))
    return n, t


def _element_end_resultants(arr: np.ndarray, axis: np.ndarray) -> Tuple[float, float, float, float, float, float, float, float]:
    """Extract scalar resultants from one OpenSees element-force vector.

    The OpenSees element-end convention is preserved. The function does not
    average adjacent elements and does not reinterpret signs into a different
    sectional-force convention.
    """
    arr = np.asarray(arr, dtype=float)
    if arr.size != 12:
        raise ValueError(f"Unexpected eleForce size: {arr.size}. Expected 12.")

    F_i = arr[0:3]
    M_i_vec = arr[3:6]
    F_j = arr[6:9]
    M_j_vec = arr[9:12]

    e = axis / np.linalg.norm(axis)

    N_i, T_i = _project_force_components(F_i, axis)
    N_j, T_j = _project_force_components(F_j, axis)

    MT_i = float(np.dot(M_i_vec, e))
    MB_i = float(np.linalg.norm(M_i_vec - MT_i * e))

    MT_j = float(np.dot(M_j_vec, e))
    MB_j = float(np.linalg.norm(M_j_vec - MT_j * e))

    return N_i, T_i, MB_i, MT_i, N_j, T_j, MB_j, MT_j


def recover_element_end_resultants(
    z_nodes: np.ndarray,
    ele_forces: List[List[float]],
    element_axes: List[np.ndarray],
    ele_tags: List[int],
) -> List[ElementEndResultants]:
    """Recover OpenSees resultants at the two ends of every element."""
    if len(ele_forces) != len(z_nodes) - 1:
        raise ValueError("Expected one eleForce vector for each element.")
    if len(element_axes) != len(ele_forces):
        raise ValueError("element_axes and ele_forces must have the same length.")
    if len(ele_tags) != len(ele_forces):
        raise ValueError("ele_tags and ele_forces must have the same length.")

    out: List[ElementEndResultants] = []

    for eidx, (ele_tag, force_vec, axis) in enumerate(zip(ele_tags, ele_forces, element_axes)):
        N_i, T_i, MB_i, MT_i, N_j, T_j, MB_j, MT_j = _element_end_resultants(
            np.asarray(force_vec, dtype=float),
            np.asarray(axis, dtype=float),
        )

        out.append(
            ElementEndResultants(
                element_id=int(ele_tag),
                z_i=float(z_nodes[eidx]),
                z_j=float(z_nodes[eidx + 1]),
                N_i=N_i,
                T_i=T_i,
                MB_i=MB_i,
                MT_i=MT_i,
                N_j=N_j,
                T_j=T_j,
                MB_j=MB_j,
                MT_j=MT_j,
            )
        )

    return out


def _jump(left: Optional[float], right: Optional[float]) -> Optional[float]:
    """Return right-minus-left only when both one-sided traces exist."""
    if left is None or right is None:
        return None
    return float(right - left)


def build_nodal_trace_resultants(
    z_nodes: np.ndarray,
    element_ends: List[ElementEndResultants],
) -> List[NodalTraceResultants]:
    """Build one-sided nodal traces from element-end resultants.

    The reported jump is the algebraic difference between adjacent OpenSees
    traces in the preserved OpenSees convention. It is a diagnostic quantity,
    not a replacement for the original element-end data.
    """
    n_nodes = len(z_nodes)
    traces: List[NodalTraceResultants] = []

    for i in range(n_nodes):
        left = element_ends[i - 1] if i > 0 else None
        right = element_ends[i] if i < len(element_ends) else None

        N_left = left.N_j if left is not None else None
        N_right = right.N_i if right is not None else None

        T_left = left.T_j if left is not None else None
        T_right = right.T_i if right is not None else None

        MB_left = left.MB_j if left is not None else None
        MB_right = right.MB_i if right is not None else None

        MT_left = left.MT_j if left is not None else None
        MT_right = right.MT_i if right is not None else None

        traces.append(
            NodalTraceResultants(
                z_node=float(z_nodes[i]),
                N_left=N_left,
                N_right=N_right,
                N_jump=_jump(N_left, N_right),
                T_left=T_left,
                T_right=T_right,
                T_jump=_jump(T_left, T_right),
                MB_left=MB_left,
                MB_right=MB_right,
                MB_jump=_jump(MB_left, MB_right),
                MT_left=MT_left,
                MT_right=MT_right,
                MT_jump=_jump(MT_left, MT_right),
            )
        )

    return traces


# =====================================================================
# 6. OUTPUTS: CSV, MARKDOWN, TIP-RESPONSE PLOTS
# =====================================================================

def _fmt_optional(value: Optional[float]) -> str:
    """Format optional numeric values for CSV output."""
    if value is None:
        return ""
    return f"{value:.12e}"


def write_element_end_csv(output_dir: Path, results: List[ModelResult]) -> Path:
    """Write OpenSees resultants at every element end.

    This is the primary internal-force output because it preserves exactly the
    two element-end values returned by OpenSees.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "openseeslab_element_end_resultants.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_id",
            "model_label",
            "n_elems",
            "n_section_calls",
            "element_id",
            "z_i",
            "z_j",
            "N_i",
            "T_i",
            "MB_i",
            "MT_i",
            "N_j",
            "T_j",
            "MB_j",
            "MT_j",
        ])

        for result in results:
            for e in result.element_ends:
                writer.writerow([
                    result.model_id,
                    result.label,
                    result.n_elems,
                    result.n_section_calls,
                    e.element_id,
                    f"{e.z_i:.12e}",
                    f"{e.z_j:.12e}",
                    f"{e.N_i:.12e}",
                    f"{e.T_i:.12e}",
                    f"{e.MB_i:.12e}",
                    f"{e.MT_i:.12e}",
                    f"{e.N_j:.12e}",
                    f"{e.T_j:.12e}",
                    f"{e.MB_j:.12e}",
                    f"{e.MT_j:.12e}",
                ])

    return csv_file


def write_nodal_trace_csv(output_dir: Path, results: List[ModelResult]) -> Path:
    """Write one-sided nodal traces and jumps for every station node."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "openseeslab_nodal_trace_resultants.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_id",
            "model_label",
            "n_elems",
            "n_section_calls",
            "z_node",
            "N_left",
            "N_right",
            "N_jump",
            "T_left",
            "T_right",
            "T_jump",
            "MB_left",
            "MB_right",
            "MB_jump",
            "MT_left",
            "MT_right",
            "MT_jump",
        ])

        for result in results:
            for tr in result.nodal_traces:
                writer.writerow([
                    result.model_id,
                    result.label,
                    result.n_elems,
                    result.n_section_calls,
                    f"{tr.z_node:.12e}",
                    _fmt_optional(tr.N_left),
                    _fmt_optional(tr.N_right),
                    _fmt_optional(tr.N_jump),
                    _fmt_optional(tr.T_left),
                    _fmt_optional(tr.T_right),
                    _fmt_optional(tr.T_jump),
                    _fmt_optional(tr.MB_left),
                    _fmt_optional(tr.MB_right),
                    _fmt_optional(tr.MB_jump),
                    _fmt_optional(tr.MT_left),
                    _fmt_optional(tr.MT_right),
                    _fmt_optional(tr.MT_jump),
                ])

    return csv_file


def write_tip_response_csv(output_dir: Path, results: List[ModelResult]) -> Path:
    """Write tip displacement and torsional rotation for every model."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "openseeslab_tip_response.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model_id", "model_label", "n_elems", "n_section_calls", "Uy_tip", "Rz_tip"])

        for result in results:
            writer.writerow([
                result.model_id,
                result.label,
                result.n_elems,
                result.n_section_calls,
                f"{result.uy_tip:.12e}",
                f"{result.rz_tip:.12e}",
            ])

    return csv_file


def write_markdown_report(output_dir: Path, results: List[ModelResult], yaml_file: Path, gauss_points: int) -> Path:
    """Write a compact report with inputs, modelling choices, and tip responses."""
    report_file = output_dir / "openseeslab_report.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# CSF/OpenSees controlled model-comparison report\n\n")

        f.write("## Inputs\n\n")
        f.write(f"- YAML file: `{yaml_file}`\n")
        f.write(f"- Gauss points per element: `{gauss_points}`\n")
        f.write(f"- Element counts: `{ELEMENT_COUNTS}`\n\n")

        f.write("## Modelling choices encoded in the script\n\n")
        f.write("- CSF section records are built before the OpenSees model is created.\n")
        f.write("- CSF section properties are passed to OpenSees with unit E and G scalars.\n")
        f.write("- `J_sv_cell` is used as the torsional constant for the closed-cell tower case.\n")
        f.write("- Beam stiffness is sampled at Gauss integration points through UserDefined beamIntegration.\n")
        f.write("- The beam line follows the CSF centroidal axis; rigid links connect reference nodes to centroidal nodes.\n")
        f.write("- Element-end resultants are preserved. Internal-node traces are not averaged.\n\n")

        f.write("## Loads\n\n")
        f.write(f"- FY_tip = {FY_TIP:.6e}\n")
        f.write(f"- FZ_tip = {FZ_TIP:.6e}\n")
        f.write(f"- MX_tip = {MX_TIP:.6e}\n")
        f.write(f"- MZ_tip = {MZ_TIP:.6e}\n")
        f.write(f"- WY_dist = {WY_DIST:.6e}\n\n")

        f.write("## Tip response\n\n")
        f.write("| Model | N_elems | CSF section calls | Uy_tip | Rz_tip |\n")
        f.write("|---|---:|---:|---:|---:|\n")

        for result in results:
            f.write(
                f"| {result.label} | {result.n_elems} | "
                f"{result.n_section_calls} | "
                f"{result.uy_tip:.8e} | {result.rz_tip:.8e} |\n"
            )

        f.write("\n## Output files\n\n")
        f.write("- `openseeslab_element_end_resultants.csv`\n")
        f.write("- `openseeslab_nodal_trace_resultants.csv`\n")
        f.write("- `openseeslab_tip_response.csv`\n")
        f.write("- `plot_tip_displacement_convergence.png`\n")
        f.write("- `plot_tip_torsional_rotation_convergence.png`\n")

    return report_file


def plot_tip_displacement(output_dir: Path, results: List[ModelResult]) -> None:
    """Plot tip displacement versus element count."""
    n_elems = [r.n_elems for r in results]
    uy_tip = [r.uy_tip for r in results]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(n_elems, uy_tip, marker="o", linewidth=1.8)
    ax.set_title("Tip displacement versus number of elements")
    ax.set_xlabel("Number of elements")
    ax.set_ylabel("Uy_tip")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(output_dir / "plot_tip_displacement_convergence.png", dpi=200)
    plt.close(fig)


def plot_tip_torsional_rotation(output_dir: Path, results: List[ModelResult]) -> None:
    """Plot tip torsional rotation versus element count."""
    n_elems = [r.n_elems for r in results]
    rz_tip = [r.rz_tip for r in results]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(n_elems, rz_tip, marker="o", linewidth=1.8)
    ax.set_title("Tip torsional rotation versus number of elements")
    ax.set_xlabel("Number of elements")
    ax.set_ylabel("Rz_tip [rad]")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(output_dir / "plot_tip_torsional_rotation_convergence.png", dpi=200)
    plt.close(fig)


# =====================================================================
# 7. WORKFLOW
# =====================================================================

def run_lab(yaml_file: Path, gauss_points: int) -> Tuple[List[ModelResult], Path, Path, Path, Path]:
    """Run the full CSF/OpenSees controlled comparison."""
    output_dir = Path(f"openseeslab_output_{yaml_file.stem}_gauss{gauss_points}")
    output_dir.mkdir(parents=True, exist_ok=True)

    section_field = build_section_field(yaml_file)
    print_csf_opensees_input_summary(yaml_file, gauss_points)

    results: List[ModelResult] = []
    for n_elems in ELEMENT_COUNTS:
        model_id = f"uniform_{n_elems}"
        label = f"uniform {n_elems}"

        projection = build_csf_opensees_projection(
            section_field=section_field,
            n_elems=n_elems,
            n_gauss_points=gauss_points,
        )

        results.append(
            run_opensees_model(
                projection=projection,
                model_id=model_id,
                label=label,
            )
        )

    element_end_csv_file = write_element_end_csv(output_dir, results)
    nodal_trace_csv_file = write_nodal_trace_csv(output_dir, results)
    tip_csv_file = write_tip_response_csv(output_dir, results)
    report_file = write_markdown_report(output_dir, results, yaml_file, gauss_points)

    # Only tip-response convergence plots are produced. Internal-force data are
    # exported as element-end and one-sided nodal traces to avoid introducing an
    # arbitrary averaged nodal representative.
    plot_tip_displacement(output_dir, results)
    plot_tip_torsional_rotation(output_dir, results)

    return results, element_end_csv_file, nodal_trace_csv_file, tip_csv_file, report_file


def main() -> None:
    """Entry point."""
    args = parse_args()
    results, element_end_csv_file, nodal_trace_csv_file, tip_csv_file, report_file = run_lab(
        yaml_file=args.yaml,
        gauss_points=args.gauss_points,
    )

    print("\nDONE")
    print(f"Element-end resultants CSV: {element_end_csv_file}")
    print(f"Nodal trace resultants CSV: {nodal_trace_csv_file}")
    print(f"Tip response CSV: {tip_csv_file}")
    print(f"Markdown report: {report_file}")
    print("Tip displacement plot: plot_tip_displacement_convergence.png")
    print("Tip torsional rotation plot: plot_tip_torsional_rotation_convergence.png")

    print("\nTip response:")
    print(f"{'Model':<18} | {'CSF calls':>9} | {'Uy_tip':>13} | {'Rz_tip [rad]':>13}")
    print("-" * 64)

    for result in results:
        print(
            f"{result.label:<18} | "
            f"{result.n_section_calls:9d} | "
            f"{result.uy_tip:13.6e} | "
            f"{result.rz_tip:13.6e}"
        )


if __name__ == "__main__":
    main()

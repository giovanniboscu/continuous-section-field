"""
CSF / OpenSeesPy nodal-resultant model-comparison laboratory
=============================================================

Purpose
-------
This script compares segmented OpenSees beam discretizations generated from the
same CSF continuous section field loaded from YAML.

The comparison reported by this script is intentionally limited to quantities
that OpenSees returns at model nodes / element ends:

    - tip displacement;
    - tip torsional rotation;
    - raw nodal axial resultant N(z);
    - raw nodal shear resultant T(z);
    - raw nodal moment resultant M(z).

No action interpolation, no trunk representative values, no section-integration
point reporting, and no delta plots are produced. The Gauss integration-point
sampling is used only internally to define the OpenSees element sections.

Structural case
---------------
- Cantilever beam / tower
- Fixed base at z=0
- Concentrated transverse tip force FY_TIP in global Y
- Concentrated axial tip force FZ_TIP in global Z
- Concentrated tip moment MX_TIP in global X
- Concentrated tip torsional moment MZ_TIP in global Z
- Uniform distributed transverse load WY_DIST applied through OpenSees beamUniform

Notes
-----
- The comparison is about beam resultants, not local 3D stresses.
- Comments are intentionally in English.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
import argparse
import matplotlib.pyplot as plt
import numpy as np

from csf import ContinuousSectionField, section_full_analysis,Visualizer
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues


# =============================================================================
# USER SETTINGS
# =============================================================================

# Segmented model definitions.
# Each scenario may use either:
#   - {"label": "uniform 12", "n_elems": 12}
#   - {"label": "custom near degraded zone", "z_fracs": [0.0, ..., 1.0]}
#   - {"label": "custom absolute z", "z_nodes": [0.0, ..., L]}
#
# z_fracs are normalized stations in [0, 1]. z_nodes are absolute stations.
# For custom scenarios, OpenSees elements use the same station nodes, but the
# section properties are sampled internally with the selected integration rule.
MODEL_STATION_SCENARIOS: List[Dict[str, Any]] = [
    {"label": "uniform 4", "n_elems": 4},    # 13 calls
    {"label": "uniform 6", "n_elems": 6},    # 19 calls
    {"label": "uniform 8", "n_elems": 8},    # 25 calls
    {"label": "uniform 12", "n_elems": 12},  # 37 calls
    {"label": "uniform 16", "n_elems": 16},  # 49 calls
    {"label": "uniform 24", "n_elems": 24},  # 73 calls
    {"label": "uniform 32", "n_elems": 32},  # 97 calls
]

MODEL_IDS = [f"model_{i}" for i in range(len(MODEL_STATION_SCENARIOS))]

# Loads.
# leave this commented part please
#FY_TIP = -50000.0
#FZ_TIP = -25000.0
#MX_TIP = 10000.0
#MZ_TIP = 3000.0
#WY_DIST = -5000.0

FY_TIP = 1.2e6
FZ_TIP = -5.0e6
MX_TIP = 8.0e6
# Plausible tower-level torsional tip moment, kept independent from MX_TIP.
MZ_TIP = 3.0e6
WY_DIST = 8.0e3

# OpenSees receives already weighted CSF section properties.
# Therefore the Elastic section uses neutral scalar carriers.
E_CARRIER = 1.0
G_CARRIER = 1.0

# Output formatting.
DISP_OUTPUT_SCALE = 1000.0
DISP_OUTPUT_UNIT = "mm"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SectionRecord:
    """One sampled CSF section used internally by the OpenSees model."""

    tag: int
    z: float
    A: float
    Iz: float
    Iy: float
    J: float
    xc: float
    yc: float


@dataclass
class RawNodalResultants:
    """Raw section resultants at model station nodes."""

    z_nodes: np.ndarray
    N_nodes: np.ndarray
    T_nodes: np.ndarray
    M_nodes: np.ndarray


@dataclass
class ModelResult:
    """Result of one segmented OpenSees model."""

    model_id: str
    label: str
    n_elems: int
    n_section_calls: int
    uy_tip: float
    rz_tip: float
    raw: RawNodalResultants


# =============================================================================
# 1. CSF MODEL LOADING
# =============================================================================
parser = argparse.ArgumentParser()
parser.add_argument(
    "yaml",
    nargs="?",
    default="NREL-5-MW.yaml",
    help="CSF YAML input file",
)

ARGS = parser.parse_args()

YAML_FILE = ARGS.yaml
YAML_STEM = Path(YAML_FILE).stem
OUTPUT_DIR = Path(f"openseeslab_output_{YAML_STEM}")


def build_section_field() -> ContinuousSectionField:
    """Load the CSF member from a YAML file."""
    res = CSFReader().read_file(YAML_FILE)

    if not res.ok:
        print(CSFIssues.format_report(res.issues))
        raise SystemExit(1)
    field = res.field
    viz = Visualizer(field)

    # 3D ruled skeleton (30% of generator lines for readability)
    viz.plot_volume_3d(line_percent=10.0, seed="w")

    
    plt.show()


    print("OK")
    return field


def _section_field_length(section_field: ContinuousSectionField) -> float:
    """Return the CSF member length from the loaded section field."""
    for attr in ("L", "length"):
        value = getattr(section_field, attr, None)
        if isinstance(value, (int, float, np.number)):
            return float(value)

    z_values: List[float] = []
    for attr in ("section0", "section1", "s0", "s1"):
        sec = getattr(section_field, attr, None)
        z = getattr(sec, "z", None)
        if isinstance(z, (int, float, np.number)):
            z_values.append(float(z))

    if len(z_values) >= 2:
        return float(max(z_values) - min(z_values))

    raise RuntimeError("Unable to determine member length from the loaded CSF field.")


def make_station_nodes(L: float, scenario: Dict[str, Any]) -> np.ndarray:
    """Return model station nodes for one discretization scenario.

    Supported scenario forms:
      - {"n_elems": N}: uniform spacing over [0, L].
      - {"z_fracs": [...]}: explicit normalized stations over [0, 1].
      - {"z_nodes": [...]}: explicit absolute stations over [0, L].
    """
    if "n_elems" in scenario:
        n_elems = int(scenario["n_elems"])
        if n_elems < 1:
            raise ValueError(f"n_elems must be >= 1. Got: {n_elems}")
        return np.linspace(0.0, float(L), n_elems + 1)
    if "z_fracs" in scenario:
        z_nodes = np.asarray(scenario["z_fracs"], dtype=float) * float(L)
    elif "z_nodes" in scenario:
        z_nodes = np.asarray(scenario["z_nodes"], dtype=float)
    else:
        raise KeyError("Each scenario must define either 'n_elems', 'z_fracs', or 'z_nodes'.")

    if z_nodes.ndim != 1 or z_nodes.size < 2:
        raise ValueError("A custom station list must contain at least two stations.")
    if not np.all(np.isfinite(z_nodes)):
        raise ValueError("Station list contains non-finite values.")
    if not np.all(np.diff(z_nodes) > 0.0):
        raise ValueError("Station list must be strictly increasing.")
    if abs(float(z_nodes[0])) > 1.0e-9:
        raise ValueError(f"First station must be 0.0. Got: {z_nodes[0]}")
    if abs(float(z_nodes[-1]) - float(L)) > max(1.0e-9, 1.0e-9 * abs(float(L))):
        raise ValueError(f"Last station must be L={L}. Got: {z_nodes[-1]}")

    return z_nodes


def scenario_label(index: int, scenario: Dict[str, Any]) -> str:
    """Return the printed label for one station scenario."""
    if "label" in scenario:
        return str(scenario["label"])
    if "n_elems" in scenario:
        return f"uniform {int(scenario['n_elems'])}"
    return f"custom {index}"


# =============================================================================
# 2. CSF SAMPLING FOR OPENSEES SECTION DEFINITIONS
# =============================================================================

def _get_analysis_value(analysis: Dict, names: List[str], default: float | None = None) -> float:
    """Read a scalar numeric value from a CSF analysis dictionary."""
    for name in names:
        if name not in analysis:
            continue
        value = analysis[name]
        if isinstance(value, (int, float, np.number)):
            return float(value)

    if default is not None:
        return float(default)

    available = ", ".join(str(k) for k in analysis.keys())
    raise KeyError(
        f"None of these keys were found as scalar values: {names}. "
        f"Available keys: {available}"
    )


def _get_j_sv_cell(analysis: Dict) -> float:
    """Return only the closed-cell Saint-Venant torsional constant J_sv_cell.

    For CSF @cell polygons, section_full_analysis may return either a scalar:
        J_sv_cell
    or a tuple/list:
        (J_sv_cell, t)

    OpenSees Elastic section requires only the scalar torsional constant J.
    No fallback to J, K_torsion, J_sv_wall, J_s_vroark, or e.j is allowed here.
    """
    key = "J_sv_cell"
    if key not in analysis:
        available = ", ".join(str(k) for k in analysis.keys())
        raise KeyError(f"Required key {key!r} not found. Available keys: {available}")

    value = analysis[key]

    if isinstance(value, (tuple, list)):
        if len(value) == 0:
            raise ValueError("J_sv_cell is an empty tuple/list.")
        value = value[0]

    if isinstance(value, np.ndarray):
        if value.size == 0:
            raise ValueError("J_sv_cell is an empty array.")
        value = value.flat[0]

    if not isinstance(value, (int, float, np.number)):
        raise TypeError(f"J_sv_cell must be numeric or (numeric, t). Got: {type(value)!r}")

    J = float(value)
    if not np.isfinite(J):
        raise ValueError(f"J_sv_cell is not finite: {J}")
    if J <= 0.0:
        raise ValueError(f"J_sv_cell must be positive for this @cell torsion model. Got: {J}")

    return J


def sample_section_record(section_field: ContinuousSectionField, z: float, tag: int) -> SectionRecord:
    """Sample the CSF section field and create an OpenSees-ready section record."""

    sec = section_field.section(float(z))
    analysis = section_full_analysis(sec)

    A = _get_analysis_value(analysis, ["A", "area", "e.a"])
    Iz = _get_analysis_value(analysis, ["Iz", "Ix", "Ixx", "Ixx_c", "e.ixx_c"])
    Iy = _get_analysis_value(analysis, ["Iy", "Iyy", "Iyy_c", "e.iyy_c"])
    J = _get_j_sv_cell(analysis)
    xc = _get_analysis_value(analysis, ["Cx", "cx", "x_c", "xc"], default=0.0)
    yc = _get_analysis_value(analysis, ["Cy", "cy", "y_c", "yc"], default=0.0)

    return SectionRecord(tag=tag, z=float(z), A=A, Iz=Iz, Iy=Iy, J=J, xc=xc, yc=yc)


def sample_sections(section_field: ContinuousSectionField, z_values: np.ndarray, tag0: int = 1) -> List[SectionRecord]:
    """Sample all requested CSF sections."""
    return [sample_section_record(section_field, float(z), tag0 + i) for i, z in enumerate(z_values)]


# =============================================================================
# 3. OPENSEES MODEL BUILDING
# =============================================================================

def build_local_basis(axis_e3: np.ndarray, vecxz: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a right-handed local basis."""
    e3 = axis_e3 / np.linalg.norm(axis_e3)

    v = np.array(vecxz, dtype=float)
    v_perp = v - np.dot(v, e3) * e3

    if np.linalg.norm(v_perp) < 1.0e-10:
        v = np.array([1.0, 0.0, 0.0], dtype=float)
        v_perp = v - np.dot(v, e3) * e3

    e1 = v_perp / np.linalg.norm(v_perp)
    e2 = np.cross(e3, e1)
    e2 = e2 / np.linalg.norm(e2)

    return e1, e2, e3


def section_xyz(section: SectionRecord, e1: np.ndarray, e2: np.ndarray) -> np.ndarray:
    """Return centroidal node coordinates for one section record."""
    ref_xyz = np.array([0.0, 0.0, section.z], dtype=float)
    return ref_xyz + section.xc * e1 + section.yc * e2


def define_opensees_sections(ops, sections: List[SectionRecord]) -> None:
    """Define OpenSees Elastic sections."""
    E = float(E_CARRIER)
    G = float(G_CARRIER)

    for s in sections:
        ops.section(
            "Elastic",
            int(s.tag),
            E,
            float(s.A),
            float(s.Iz),
            float(s.Iy),
            G,
            float(max(abs(s.J), 1.0e-18)),
        )


def solve_static_case(ops, base_ref_node: int, tip_ref_node: int, ele_tags: List[int]) -> Tuple[float, float, List[List[float]]]:
    """Apply boundary conditions, loads, solve, and return tip response plus element forces."""
    ops.fix(int(base_ref_node), 1, 1, 1, 1, 1, 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    # Concentrated tip loads.
    ops.load(
        int(tip_ref_node),
        0.0,
        float(FY_TIP),
        float(FZ_TIP),
        float(MX_TIP),
        0.0,
        float(MZ_TIP),
    )

    # Uniform distributed load on each beam element.
    # OpenSees '-beamUniform' is applied in the element local transverse system.
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


def run_segmented_model(
    section_field: ContinuousSectionField,
    z_nodes: np.ndarray,
    model_id: str,
    label: str,
) -> ModelResult:
    """Run one segmented OpenSees model with Gauss section sampling."""
    try:
        import openseespy.opensees as ops
    except Exception as e:
        raise RuntimeError("openseespy is not available. Install openseespy.") from e

    L = _section_field_length(section_field)
    z_nodes = np.asarray(z_nodes, dtype=float)
    n_elems = int(len(z_nodes) - 1)

    # Two-point Gauss rule on the normalized element interval [0, 1].
    # The station nodes are unchanged; only the internal section sampling rule changes.
    gauss_xi = np.array([
        0.2113248654051871,
        0.7886751345948129,
    ], dtype=float)
    gauss_w = np.array([0.5, 0.5], dtype=float)

    z_gauss: List[float] = []
    for zi, zj in zip(z_nodes[:-1], z_nodes[1:]):
        h = float(zj - zi)
        z_gauss.extend([
            float(zi + gauss_xi[0] * h),
            float(zi + gauss_xi[1] * h),
        ])

    # Total calls to section_field.section(float(z)) made by this model:
    #   - one call for each physical station node;
    #   - two internal Gauss-section calls for each element.
    # This is an output metric only; it does not alter the sampling logic.
    n_section_calls = int(len(z_nodes) + len(z_gauss))

    # Node geometry: use real CSF sections at the physical station nodes.
    node_sections = sample_sections(section_field, z_nodes, tag0=100000)

    # Element stiffness: two Gauss-section samples per element.
    # These sampling points are not reported; they only define the element sections.
    trunk_sections = sample_sections(section_field, np.asarray(z_gauss, dtype=float), tag0=1)

    e1, e2, _ = build_local_basis(
        np.array([0.0, 0.0, L], dtype=float),
        np.array([1.0, 0.0, 0.0], dtype=float),
    )

    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    transf_tag = 1
    ops.geomTransf("Linear", transf_tag, 1.0, 0.0, 0.0)

    define_opensees_sections(ops, trunk_sections)

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
        ops.rigidLink("beam", ref_tag, cen_tag)

        ref_nodes.append(ref_tag)
        cen_nodes.append(cen_tag)
        cen_xyzs.append(cen_xyz)

    ele_tags: List[int] = []
    element_axes: List[np.ndarray] = []

    for i in range(n_elems):
        ele_tag = i + 1
        int_tag = 20000 + i

        sec_tag_1 = int(trunk_sections[2 * i + 0].tag)
        sec_tag_2 = int(trunk_sections[2 * i + 1].tag)

        # Same station mesh; two internal Gauss section samples per element.
        ops.beamIntegration(
            "UserDefined",
            int_tag,
            2,
            sec_tag_1,
            sec_tag_2,
            float(gauss_xi[0]),
            float(gauss_xi[1]),
            float(gauss_w[0]),
            float(gauss_w[1]),
        )

        ops.element("forceBeamColumn", ele_tag, cen_nodes[i], cen_nodes[i + 1], transf_tag, int_tag)

        ele_tags.append(ele_tag)
        element_axes.append(cen_xyzs[i + 1] - cen_xyzs[i])

    uy_tip, rz_tip, ele_forces = solve_static_case(ops, ref_nodes[0], ref_nodes[-1], ele_tags)

    raw = recover_raw_nodal_resultants(
        z_nodes=z_nodes,
        ele_forces=ele_forces,
        element_axes=element_axes,
    )

    print(
        f"[RUN] {label:<42} | "
        f"CSF_section_calls={n_section_calls:d} | "
        f"Uy_tip={uy_tip * DISP_OUTPUT_SCALE:.6f} {DISP_OUTPUT_UNIT} | "
        f"Rz_tip={rz_tip:.6e} rad"
    )

    return ModelResult(
        model_id=model_id,
        label=label,
        n_elems=n_elems,
        n_section_calls=n_section_calls,
        uy_tip=uy_tip,
        rz_tip=rz_tip,
        raw=raw,
    )


# =============================================================================
# 4. RAW SECTION RESULTANT RECOVERY
# =============================================================================

def _project_force_components(force_vec: np.ndarray, axis: np.ndarray) -> Tuple[float, float]:
    """Project a 3D force vector onto the element axis."""
    e = axis / np.linalg.norm(axis)
    n = float(np.dot(force_vec, e))
    t_vec = force_vec - n * e
    t = float(np.linalg.norm(t_vec))
    return n, t


def _element_end_resultants(arr: np.ndarray, axis: np.ndarray) -> Tuple[float, float, float, float, float, float]:
    """Extract scalar resultants from one OpenSees element force vector."""
    arr = np.asarray(arr, dtype=float)
    if arr.size < 12:
        raise ValueError(f"Unexpected eleForce size: {arr.size}. Expected at least 12.")

    F_i = arr[0:3]
    M_i_vec = arr[3:6]
    F_j = arr[6:9]
    M_j_vec = arr[9:12]

    N_i, T_i = _project_force_components(F_i, axis)
    N_j, T_j = _project_force_components(F_j, axis)

    M_i = float(np.linalg.norm(M_i_vec))
    M_j = float(np.linalg.norm(M_j_vec))

    return abs(N_i), T_i, M_i, abs(N_j), T_j, M_j


def recover_raw_nodal_resultants(
    z_nodes: np.ndarray,
    ele_forces: List[List[float]],
    element_axes: List[np.ndarray],
) -> RawNodalResultants:
    """Recover raw nodal section resultants from OpenSees element end forces."""
    n_nodes = len(z_nodes)
    if len(ele_forces) != n_nodes - 1:
        raise ValueError("Expected one eleForce vector for each element.")
    if len(element_axes) != len(ele_forces):
        raise ValueError("element_axes and ele_forces must have the same length.")

    N_acc: List[List[float]] = [[] for _ in range(n_nodes)]
    T_acc: List[List[float]] = [[] for _ in range(n_nodes)]
    M_acc: List[List[float]] = [[] for _ in range(n_nodes)]

    for eidx, (force_vec, axis) in enumerate(zip(ele_forces, element_axes)):
        N_i, T_i, M_i, N_j, T_j, M_j = _element_end_resultants(
            np.asarray(force_vec, dtype=float),
            np.asarray(axis, dtype=float),
        )

        left = eidx
        right = eidx + 1

        N_acc[left].append(N_i)
        T_acc[left].append(T_i)
        M_acc[left].append(M_i)

        N_acc[right].append(N_j)
        T_acc[right].append(T_j)
        M_acc[right].append(M_j)

    N_nodes = np.array([float(np.mean(v)) for v in N_acc], dtype=float)
    T_nodes = np.array([float(np.mean(v)) for v in T_acc], dtype=float)
    M_nodes = np.array([float(np.mean(v)) for v in M_acc], dtype=float)

    return RawNodalResultants(
        z_nodes=np.asarray(z_nodes, dtype=float),
        N_nodes=N_nodes,
        T_nodes=T_nodes,
        M_nodes=M_nodes,
    )


# =============================================================================
# 5. OUTPUTS: CSV, MARKDOWN, PLOTS
# =============================================================================

def build_comparison(results: List[ModelResult]) -> Dict[str, Dict[str, np.ndarray | float | str]]:
    """Collect model outputs without calculating deltas."""
    out: Dict[str, Dict[str, np.ndarray | float | str]] = {}

    for r in results:
        out[r.model_id] = {
            "label": r.label,
            "n_elems": r.n_elems,
            "n_section_calls": r.n_section_calls,
            "uy_tip": float(r.uy_tip),
            "rz_tip": float(r.rz_tip),
            "raw_z_nodes": r.raw.z_nodes,
            "raw_N_nodes": r.raw.N_nodes,
            "raw_T_nodes": r.raw.T_nodes,
            "raw_M_nodes": r.raw.M_nodes,
        }

    return out


def write_raw_nodal_csv(output_dir: Path, comparison: Dict[str, Dict[str, np.ndarray | float | str]]) -> Path:
    """Write all raw nodal resultants returned by OpenSees."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "openseeslab_raw_nodal_values.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_id",
            "model_label",
            "n_elems",
            "n_section_calls",
            "z_node",
            "N_node",
            "T_node",
            "M_node",
        ])

        for model_id in MODEL_IDS:
            data = comparison[model_id]
            z_nodes = np.asarray(data["raw_z_nodes"], dtype=float)
            N_nodes = np.asarray(data["raw_N_nodes"], dtype=float)
            T_nodes = np.asarray(data["raw_T_nodes"], dtype=float)
            M_nodes = np.asarray(data["raw_M_nodes"], dtype=float)

            for i, z in enumerate(z_nodes):
                writer.writerow([
                    model_id,
                    data["label"],
                    int(data["n_elems"]),
                    int(data["n_section_calls"]),
                    f"{z:.12e}",
                    f"{N_nodes[i]:.12e}",
                    f"{T_nodes[i]:.12e}",
                    f"{M_nodes[i]:.12e}",
                ])

    return csv_file


def write_tip_response_csv(output_dir: Path, comparison: Dict[str, Dict[str, np.ndarray | float | str]]) -> Path:
    """Write tip displacement and torsional rotation convergence table."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "openseeslab_tip_response.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model_id", "model_label", "n_elems", "n_section_calls", "Uy_tip", "Rz_tip"])
        for model_id in MODEL_IDS:
            data = comparison[model_id]
            writer.writerow([
                model_id,
                data["label"],
                int(data["n_elems"]),
                int(data["n_section_calls"]),
                f"{float(data['uy_tip']):.12e}",
                f"{float(data['rz_tip']):.12e}",
            ])

    return csv_file


def write_markdown_report(output_dir: Path, comparison: Dict[str, Dict[str, np.ndarray | float | str]]) -> Path:
    """Write a compact report with absolute nodal values only."""
    report_file = output_dir / "openseeslab_nodal_absolute_report.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# CSF/OpenSees nodal absolute-resultant report\n\n")

        f.write("## Models\n\n")
        for model_id in MODEL_IDS:
            data = comparison[model_id]
            f.write(
                f"- {data['label']}: segmented beam model, "
                f"{int(data['n_elems'])} elements, "
                f"{int(data['n_section_calls'])} CSF section calls.\n"
            )
        f.write("\n")

        f.write("## Structural case\n\n")
        f.write("- Scheme: cantilever tower/beam.\n")
        f.write("- Boundary condition: fixed base at z=0.\n")
        f.write(f"- FY_tip = {FY_TIP:.6e}\n")
        f.write(f"- FZ_tip = {FZ_TIP:.6e}\n")
        f.write(f"- MX_tip = {MX_TIP:.6e}\n")
        f.write(f"- MZ_tip = {MZ_TIP:.6e}\n")
        f.write(f"- WY_dist = {WY_DIST:.6e}\n\n")

        f.write("## Comparison rule\n\n")
        f.write("This report lists only the nodal/end action resultants returned by OpenSees.\n")
        f.write("All sampled model nodes are retained for each discretization.\n")
        f.write("No action interpolation, no nodal deltas, no trunk representative values, and no midpoint section-sampling stations are reported.\n\n")

        f.write("## Tip response\n\n")
        f.write("| Model | N_elems | CSF section calls | Uy_tip | Rz_tip |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for model_id in MODEL_IDS:
            data = comparison[model_id]
            f.write(
                f"| {data['label']} | {int(data['n_elems'])} | "
                f"{int(data['n_section_calls'])} | "
                f"{float(data['uy_tip']):.8e} | {float(data['rz_tip']):.8e} |\n"
            )

        f.write("\n## Nodal samples\n\n")
        f.write("| Model | N_elems | CSF section calls | nodal samples |\n")
        f.write("|---|---:|---:|---:|\n")
        for model_id in MODEL_IDS:
            data = comparison[model_id]
            n_nodes = len(np.asarray(data["raw_z_nodes"], dtype=float))
            f.write(
                f"| {data['label']} | {int(data['n_elems'])} | "
                f"{int(data['n_section_calls'])} | {n_nodes} |\n"
            )

        f.write("\n## Output files\n\n")
        f.write("- `openseeslab_raw_nodal_values.csv`: absolute nodal OpenSees resultants N, T, M for every sampled node of every model.\n")
        f.write("- `openseeslab_tip_response.csv`: tip displacement and torsional rotation for each model.\n")
        f.write("- `plot_N/T/M_raw_nodal_values.png`: absolute nodal OpenSees resultants.\n")

    return report_file


def plot_raw_nodal_values(output_dir: Path, comparison: Dict[str, Dict[str, np.ndarray | float | str]]) -> None:
    """Plot raw nodal N(z), T(z), M(z) for every model."""
    for key, title, ylabel, filename in [
        ("raw_N_nodes", "Raw nodal axial resultant", "N", "plot_N_raw_nodal_values.png"),
        ("raw_T_nodes", "Raw nodal shear resultant", "T", "plot_T_raw_nodal_values.png"),
        ("raw_M_nodes", "Raw nodal moment resultant", "M", "plot_M_raw_nodal_values.png"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 6))

        for model_id in MODEL_IDS:
            data = comparison[model_id]
            z = np.asarray(data["raw_z_nodes"], dtype=float)
            y = np.asarray(data[key], dtype=float)
            ax.plot(
                z,
                y,
                marker="o",
                linewidth=1.8,
                label=f"{data['label']} ({int(data['n_section_calls'])} CSF calls)",
            )

        ax.set_title(title)
        ax.set_xlabel("z")
        ax.set_ylabel(ylabel)
        ax.grid(True)
        ax.legend()

        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=200)
        plt.close(fig)


def _is_uniform_scenario(scenario: Dict[str, Any]) -> bool:
    """Return True only for scenarios defined by uniform element count."""
    return "n_elems" in scenario


def _split_tip_response_by_sampling_type(
    comparison: Dict[str, Dict[str, np.ndarray | float | str]],
    value_key: str,
) -> Tuple[List[int], List[float], List[int], List[float], List[str]]:
    """Split tip responses into uniform and custom station scenarios."""
    uniform_n: List[int] = []
    uniform_y: List[float] = []
    custom_n: List[int] = []
    custom_y: List[float] = []
    custom_labels: List[str] = []

    for model_id, scenario in zip(MODEL_IDS, MODEL_STATION_SCENARIOS):
        data = comparison[model_id]
        n_elems = int(data["n_elems"])
        value = float(data[value_key])

        if _is_uniform_scenario(scenario):
            uniform_n.append(n_elems)
            uniform_y.append(value)
        else:
            custom_n.append(n_elems)
            custom_y.append(value)
            custom_labels.append(str(data["label"]))

    pairs = sorted(zip(uniform_n, uniform_y), key=lambda item: item[0])
    if pairs:
        uniform_n, uniform_y = map(list, zip(*pairs))
    else:
        uniform_n, uniform_y = [], []

    return uniform_n, uniform_y, custom_n, custom_y, custom_labels


def _annotate_custom_points(ax, custom_n: List[int], custom_y: List[float], custom_labels: List[str]) -> None:
    """Annotate custom station scenarios without connecting them to the uniform curve."""
    for x, y, label in zip(custom_n, custom_y, custom_labels):
        ax.annotate(
            "custom",
            xy=(x, y),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
        )


def plot_tip_displacement(output_dir: Path, comparison: Dict[str, Dict[str, np.ndarray | float | str]]) -> None:
    """Plot tip displacement versus element count.

    Uniform discretizations are connected as a convergence curve.
    Custom station layouts are shown as isolated markers because they represent
    targeted sampling, not a uniform mesh-density sequence.
    """
    uniform_n, uniform_uy, custom_n, custom_uy, custom_labels = _split_tip_response_by_sampling_type(
        comparison,
        "uy_tip",
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    if uniform_n:
        ax.plot(uniform_n, uniform_uy, marker="o", linewidth=1.8, label="uniform stations")
    if custom_n:
        ax.scatter(custom_n, custom_uy, marker="*", s=130, label="custom peak-aligned stations")
        _annotate_custom_points(ax, custom_n, custom_uy, custom_labels)

    ax.set_title("Tip displacement versus number of elements")
    ax.set_xlabel("Number of elements")
    ax.set_ylabel("Uy_tip")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "plot_tip_displacement_convergence.png", dpi=200)
    plt.close(fig)


def plot_tip_torsional_rotation(output_dir: Path, comparison: Dict[str, Dict[str, np.ndarray | float | str]]) -> None:
    """Plot tip torsional rotation versus element count.

    Uniform discretizations are connected as a convergence curve.
    Custom station layouts are shown as isolated markers because they represent
    targeted sampling, not a uniform mesh-density sequence.
    """
    uniform_n, uniform_rz, custom_n, custom_rz, custom_labels = _split_tip_response_by_sampling_type(
        comparison,
        "rz_tip",
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    if uniform_n:
        ax.plot(uniform_n, uniform_rz, marker="o", linewidth=1.8, label="uniform stations")
    if custom_n:
        ax.scatter(custom_n, custom_rz, marker="*", s=130, label="custom peak-aligned stations")
        _annotate_custom_points(ax, custom_n, custom_rz, custom_labels)

    ax.set_title("Tip torsional rotation versus number of elements")
    ax.set_xlabel("Number of elements")
    ax.set_ylabel("Rz_tip [rad]")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "plot_tip_torsional_rotation_convergence.png", dpi=200)
    plt.close(fig)


# =============================================================================
# 6. WORKFLOW
# =============================================================================

def run_lab() -> Tuple[List[ModelResult], Dict[str, Dict[str, np.ndarray | float | str]], Path, Path, Path]:
    """Run the nodal absolute-resultant comparison laboratory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section_field = build_section_field()

    results: List[ModelResult] = []

    L = _section_field_length(section_field)
    for i, scenario in enumerate(MODEL_STATION_SCENARIOS):
        z_nodes = make_station_nodes(L, scenario)
        n_elems = int(len(z_nodes) - 1)
        label = f"Model {i} - {scenario_label(i, scenario)} ({n_elems} elements)"
        results.append(
            run_segmented_model(
                section_field,
                z_nodes=z_nodes,
                model_id=f"model_{i}",
                label=label,
            )
        )

    comparison = build_comparison(results)

    raw_csv_file = write_raw_nodal_csv(OUTPUT_DIR, comparison)
    tip_csv_file = write_tip_response_csv(OUTPUT_DIR, comparison)
    report_file = write_markdown_report(OUTPUT_DIR, comparison)

    plot_raw_nodal_values(OUTPUT_DIR, comparison)
    plot_tip_displacement(OUTPUT_DIR, comparison)
    plot_tip_torsional_rotation(OUTPUT_DIR, comparison)

    return results, comparison, raw_csv_file, tip_csv_file, report_file


def main() -> None:
    """Entry point."""
    _, comparison, raw_csv_file, tip_csv_file, report_file = run_lab()

    print("\nDONE")
    print(f"Raw nodal CSV: {raw_csv_file}")
    print(f"Tip response CSV: {tip_csv_file}")
    print(f"Markdown report: {report_file}")
    print("Nodal resultant plots: plot_N/T/M_raw_nodal_values.png")
    print("Tip displacement plot: plot_tip_displacement_convergence.png")
    print("Tip torsional rotation plot: plot_tip_torsional_rotation_convergence.png")
    print("\nTip response:")
    print(f"{'Model':<50} | {'CSF calls':>9} | {'Uy_tip':>13} | {'Rz_tip [rad]':>13}")
    print("-" * 98)

    for model_id in MODEL_IDS:
        data = comparison[model_id]
        print(
            f"{str(data['label']):<50} | "
            f"{int(data['n_section_calls']):9d} | "
            f"{float(data['uy_tip']):13.6e} | "
            f"{float(data['rz_tip']):13.6e}"
        )

    print("\nNodal samples:")
    print(f"{'Model':<50} | {'CSF calls':>9} | {'nodes':>7}")
    print("-" * 75)
    for model_id in MODEL_IDS:
        data = comparison[model_id]
        n_nodes = len(np.asarray(data["raw_z_nodes"], dtype=float))
        print(f"{str(data['label']):<50} | {int(data['n_section_calls']):9d} | {n_nodes:7d}")


if __name__ == "__main__":
    main()

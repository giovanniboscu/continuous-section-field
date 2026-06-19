"""
CSF / OpenSeesPy tip-response validation
========================================

This script computes the OpenSees tip response used in the CSF validation
comparison.

The relevant modelling chain is intentionally kept single-source:

    CSF YAML input
        -> CSFReader
        -> ContinuousSectionField
        -> section_field.section(z)
        -> section_full_analysis(section)
        -> sampled section records
        -> OpenSees beam model
        -> tip-response CSV/report/plots

No geometric quantity used in the printed summary or in the OpenSees model is
reconstructed directly from raw YAML polygons or vertices. The YAML file is read
only by CSFReader; after that point, section data come from the evaluated CSF
section and from section_full_analysis().

Run example
-----------

    python run_csf_opensees_gaussN_public_csf_only.py NREL-5-MW.yaml --gauss-points 2
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from csf import ContinuousSectionField, section_full_analysis
from csf.visualizer import Visualizer
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
FY_TIP = 1.2e6   # Concentrated transverse tip force at the reference tip node.
MX_TIP = 8.0e6   # Concentrated bending moment about global X.
MZ_TIP = 3.0e6   # Concentrated torsional moment about global Z.
WY_DIST = 8.0e3  # Uniform distributed load in the OpenSees local transverse direction.

# CSF provides the section quantities already in the stiffness scale selected for
# this comparison. OpenSees therefore receives unit material scalars in the
# Elastic section definition. This is a CSF-to-OpenSees projection convention,
# not a statement that the physical material has E = G = 1.
E_OPENSEES_UNIT = 1.0
G_OPENSEES_UNIT = 1.0


# =====================================================================
# DATA STRUCTURES
# =====================================================================

@dataclass(frozen=True)
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


@dataclass(frozen=True)
class CSFOpenSeesProjection:
    """Data produced by CSF and consumed by one OpenSees model.

    This object is the interface between the CSF model and OpenSees. OpenSees
    does not query the CSF field directly; it receives sampled section records,
    station nodes, and integration-rule data.
    """

    z_nodes: np.ndarray
    gauss_xi: np.ndarray
    gauss_w: np.ndarray
    node_sections: List[SectionRecord]
    integration_sections: List[SectionRecord]
    n_section_calls: int


@dataclass(frozen=True)
class ModelResult:
    """OpenSees result for one uniform discretization."""

    model_id: str
    label: str
    n_elems: int
    n_section_calls: int
    uy_tip: float
    rz_tip: float


# =====================================================================
# 1. COMMAND-LINE INPUTS
# =====================================================================

def parse_args() -> argparse.Namespace:
    """Read explicit experiment inputs from the command line."""
    parser = argparse.ArgumentParser(
        description="Run the CSF/OpenSees tip-response validation model."
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
# 2. CSF MODEL LOADING
# =====================================================================

def build_section_field(yaml_file: Path) -> ContinuousSectionField:
    """Load the CSF member from YAML through the CSF reader.

    The returned ContinuousSectionField is the authoritative model used by this
    script. The raw YAML structure is not parsed elsewhere to reconstruct
    geometric quantities.
    """
    res = CSFReader().read_file(str(yaml_file))

    if not res.ok:
        print(CSFIssues.format_report(res.issues))
        raise SystemExit(1)

    return res.field


# =====================================================================
# 3. CSF SECTION EVALUATION
# =====================================================================

def sample_section_record(
    section_field: ContinuousSectionField,
    z: float,
    tag: int,
) -> SectionRecord:
    """Evaluate CSF at one station and create an OpenSees section record.

    This is the only source of section properties used by the model. The
    function evaluates the CSF section first, then reads the required quantities
    from section_full_analysis().
    """
    sec = section_field.section(float(z))
    analysis = section_full_analysis(sec)

    return SectionRecord(
        tag=int(tag),
        z=float(z),
        A=float(analysis["A"]),
        Iz=float(analysis["Ix"]),
        Iy=float(analysis["Iy"]),
        J=float(analysis["J_sv_cell"][0]),
        xc=float(analysis["Cx"]),
        yc=float(analysis["Cy"]),
    )


def sample_sections(
    section_field: ContinuousSectionField,
    z_values: np.ndarray,
    tag0: int,
) -> List[SectionRecord]:
    """Sample all requested CSF sections."""
    return [
        sample_section_record(section_field, float(z), int(tag0 + i))
        for i, z in enumerate(z_values)
    ]


def print_csf_opensees_input_summary(
    section_field: ContinuousSectionField,
    yaml_file: Path,
    gauss_points: int,
) -> None:
    """Print the inputs controlling the CSF-to-OpenSees projection.

    The printed section quantities are evaluated from the CSF model itself:

        section_field.section(z) -> section_full_analysis(section)

    No radius, area, inertia, centroid, or torsion quantity is reconstructed
    directly from raw YAML polygons or vertices.
    """
    L = float(section_field.L)

    base = sample_section_record(section_field, z=0.0, tag=0)
    top = sample_section_record(section_field, z=L, tag=0)

    lines: List[str] = []
    lines.append("")
    lines.append("CSF / OPENSEES MODEL INPUT")
    lines.append("=" * 78)
    lines.append(f"YAML file                  : {yaml_file}")
    lines.append(f"L                          : {L:.12e}")

    lines.append("")
    lines.append("Endpoint section quantities from CSF")
    lines.append("-" * 78)
    lines.append("Source                     : section_full_analysis(section_field.section(z))")
    lines.append(f"BASE z                     : {base.z:.12e}")
    lines.append(f"TOP z                      : {top.z:.12e}")
    lines.append(f"A_BASE                     : {base.A:.12e}")
    lines.append(f"A_TOP                      : {top.A:.12e}")
    lines.append(f"Cx_BASE                    : {base.xc:.12e}")
    lines.append(f"Cx_TOP                     : {top.xc:.12e}")
    lines.append(f"Cy_BASE                    : {base.yc:.12e}")
    lines.append(f"Cy_TOP                     : {top.yc:.12e}")
    lines.append(f"Ix_BASE                    : {base.Iz:.12e}")
    lines.append(f"Ix_TOP                     : {top.Iz:.12e}")
    lines.append(f"Iy_BASE                    : {base.Iy:.12e}")
    lines.append(f"Iy_TOP                     : {top.Iy:.12e}")
    lines.append(f"J_sv_cell_BASE             : {base.J:.12e}")
    lines.append(f"J_sv_cell_TOP              : {top.J:.12e}")

    lines.append("")
    lines.append("CSF to OpenSees projection")
    lines.append("-" * 78)
    lines.append("Section integration rule   : Gauss-Legendre")
    lines.append(f"Gauss points per element   : {gauss_points:d}")
    lines.append("OpenSees E scalar          : 1.0")
    lines.append("OpenSees G scalar          : 1.0")
    lines.append("")

    print("\n".join(lines))


# =====================================================================
# 4. CSF SAMPLING AND PROJECTION DATA
# =====================================================================

def make_uniform_station_nodes(L: float, n_elems: int) -> np.ndarray:
    """Return uniformly spaced physical station nodes over [0, L]."""
    if n_elems < 1:
        raise ValueError(f"n_elems must be >= 1. Got: {n_elems}.")

    return np.linspace(0.0, float(L), int(n_elems) + 1)


def gauss_points_on_station_mesh(
    z_nodes: np.ndarray,
    n_gauss_points: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return Gauss point coordinates, normalized locations, and weights.

    Physical station nodes are not changed by the integration rule. Gauss points
    are internal element sampling stations used to build element stiffness.
    """
    xi_raw, w_raw = np.polynomial.legendre.leggauss(int(n_gauss_points))
    gauss_xi = 0.5 * (xi_raw + 1.0)
    gauss_w = 0.5 * w_raw

    z_gauss: List[float] = []
    for zi, zj in zip(z_nodes[:-1], z_nodes[1:]):
        h = float(zj - zi)
        for xi in gauss_xi:
            z_gauss.append(float(zi + float(xi) * h))

    return np.asarray(z_gauss, dtype=float), gauss_xi, gauss_w


def build_csf_opensees_projection(
    section_field: ContinuousSectionField,
    n_elems: int,
    n_gauss_points: int,
) -> CSFOpenSeesProjection:
    """Build the complete CSF data package consumed by one OpenSees model.

    The function samples the continuous CSF section field at physical station
    nodes and at Gauss integration points, then returns plain records for
    OpenSees to consume.
    """
    L = float(section_field.L)
    z_nodes = make_uniform_station_nodes(L, int(n_elems))
    z_gauss, gauss_xi, gauss_w = gauss_points_on_station_mesh(
        z_nodes,
        int(n_gauss_points),
    )

    # Node sections define the centroidal axis geometry.
    node_sections = sample_sections(section_field, z_nodes, tag0=100000)

    # Integration sections define element stiffness through OpenSees
    # UserDefined beamIntegration.
    integration_sections = sample_sections(section_field, z_gauss, tag0=1)

    n_section_calls = int(len(node_sections) + len(integration_sections))

    return CSFOpenSeesProjection(
        z_nodes=z_nodes,
        gauss_xi=gauss_xi,
        gauss_w=gauss_w,
        node_sections=node_sections,
        integration_sections=integration_sections,
        n_section_calls=n_section_calls,
    )


# =====================================================================
# 5. OPENSEES MODEL BUILDING AND SOLUTION
# =====================================================================

def build_local_basis(
    axis_e3: np.ndarray,
    vecxz: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a right-handed local basis from the member axis and reference vector.

    The local basis places centroidal nodes from CSF centroid offsets. The same
    reference direction also fixes the OpenSees transverse load orientation.
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
) -> Tuple[List[int], List[int]]:
    """Create reference-axis nodes, centroidal nodes, and rigid offsets.

    Loads and boundary conditions are applied on the reference axis. Beam
    elements are placed on the centroidal axis. Rigid links make this modelling
    choice explicit instead of silently merging the two axes.
    """
    ref_nodes: List[int] = []
    cen_nodes: List[int] = []

    for i, sec in enumerate(node_sections):
        ref_tag = 1 + i
        cen_tag = 10000 + i

        ref_xyz = np.array([0.0, 0.0, sec.z], dtype=float)
        cen_xyz = section_xyz(sec, e1, e2)

        ops.node(ref_tag, float(ref_xyz[0]), float(ref_xyz[1]), float(ref_xyz[2]))
        ops.node(cen_tag, float(cen_xyz[0]), float(cen_xyz[1]), float(cen_xyz[2]))

        # Rigid kinematic offset from the reference axis to the centroidal axis.
        ops.rigidLink("beam", ref_tag, cen_tag)

        ref_nodes.append(ref_tag)
        cen_nodes.append(cen_tag)

    return ref_nodes, cen_nodes


def create_force_beam_column_elements(
    ops,
    projection: CSFOpenSeesProjection,
    cen_nodes: List[int],
    transf_tag: int,
) -> List[int]:
    """Create forceBeamColumn elements using CSF-sampled Gauss sections."""
    n_elems = int(len(projection.z_nodes) - 1)
    n_ip = int(len(projection.gauss_xi))

    ele_tags: List[int] = []
    for i in range(n_elems):
        ele_tag = i + 1
        int_tag = 20000 + i

        sec_tags = [
            int(projection.integration_sections[n_ip * i + k].tag)
            for k in range(n_ip)
        ]

        # UserDefined integration receives section tags, normalized locations,
        # and weights. This is the OpenSees mechanism used to project the
        # continuous CSF section field into element stiffness.
        ops.beamIntegration(
            "UserDefined",
            int_tag,
            n_ip,
            *sec_tags,
            *[float(x) for x in projection.gauss_xi],
            *[float(w) for w in projection.gauss_w],
        )

        ops.element(
            "forceBeamColumn",
            ele_tag,
            cen_nodes[i],
            cen_nodes[i + 1],
            transf_tag,
            int_tag,
        )

        ele_tags.append(ele_tag)

    return ele_tags


def solve_static_case(
    ops,
    base_ref_node: int,
    tip_ref_node: int,
    ele_tags: List[int],
) -> Tuple[float, float]:
    """Apply the controlled static case and return the tip response."""
    ops.fix(int(base_ref_node), 1, 1, 1, 1, 1, 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    # Concentrated loads are applied at the reference-axis tip node. The rigid
    # offset transfers them to the centroidal beam line.
    ops.load(
        int(tip_ref_node),
        0.0,
        float(FY_TIP),
        0.0,
        float(MX_TIP),
        0.0,
        float(MZ_TIP),
    )

    # OpenSees beamUniform loads are element-local loads. WY_DIST is therefore
    # intentionally interpreted in the local transverse direction defined by the
    # geometric transformation.
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

    # Linear transformation and static analysis are used because the validation
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

    return uy_tip, rz_tip


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
    except Exception as exc:
        raise RuntimeError("openseespy is not available. Install openseespy.") from exc

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

    ref_nodes, cen_nodes = create_reference_and_centroid_nodes(
        ops,
        projection.node_sections,
        e1,
        e2,
    )

    ele_tags = create_force_beam_column_elements(
        ops,
        projection,
        cen_nodes,
        transf_tag,
    )

    uy_tip, rz_tip = solve_static_case(ops, ref_nodes[0], ref_nodes[-1], ele_tags)

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
    )


# =====================================================================
# 7. OUTPUTS: CSV, MARKDOWN, TIP-RESPONSE PLOTS
# =====================================================================

def write_tip_response_csv(output_dir: Path, results: List[ModelResult]) -> Path:
    """Write tip displacement and torsional rotation for every model."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_file = output_dir / "openseeslab_tip_response.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model_id",
            "model_label",
            "n_elems",
            "n_section_calls",
            "Uy_tip",
            "Rz_tip",
        ])

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


def write_markdown_report(
    output_dir: Path,
    results: List[ModelResult],
    yaml_file: Path,
    gauss_points: int,
) -> Path:
    """Write a compact report with inputs, modelling choices, and tip responses."""
    report_file = output_dir / "openseeslab_report.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# CSF/OpenSees controlled model-comparison report\n\n")

        f.write("## Inputs\n\n")
        f.write(f"- YAML file: `{yaml_file}`\n")
        f.write(f"- Gauss points per element: `{gauss_points}`\n")
        f.write(f"- Element counts: `{ELEMENT_COUNTS}`\n\n")

        f.write("## Modelling choices encoded in the script\n\n")
        f.write("- The YAML input is loaded only through `CSFReader`.\n")
        f.write("- Section quantities are obtained from `section_full_analysis(section_field.section(z))`.\n")
        f.write("- No geometric quantity is reconstructed directly from raw YAML vertices.\n")
        f.write("- The 3D volume plot is generated from `Visualizer(section_field)`.\n")
        f.write("- CSF section properties are passed to OpenSees with unit E and G scalars.\n")
        f.write("- `J_sv_cell` is used as the torsional constant for the closed-cell tower case.\n")
        f.write("- Beam stiffness is sampled at Gauss integration points through UserDefined beamIntegration.\n")
        f.write("- The beam line follows the CSF centroidal axis; rigid links connect reference nodes to centroidal nodes.\n\n")

        f.write("## Loads\n\n")
        f.write(f"- FY_tip = {FY_TIP:.6e}\n")
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
        f.write("- `openseeslab_tip_response.csv`\n")
        f.write("- `plot_csf_volume_3d.png`\n")
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
# 8. COMMAND-LINE WORKFLOW
# =====================================================================

def main() -> None:
    """Run the complete validation workflow.

    The reviewer-facing execution order is intentionally explicit here. Helper
    functions above do one operation each; this function shows the actual script
    sequence from command-line input to final files.
    """
    # 1. Read command-line inputs.
    args = parse_args()
    yaml_file = args.yaml
    gauss_points = args.gauss_points

    # 2. Create the output directory from the YAML file stem.
    output_dir = Path(f"openseeslab_output_{yaml_file.stem}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Load the CSF model once. All section quantities below come from this
    #    object, not from direct YAML reconstruction.
    section_field = build_section_field(yaml_file)
    print_csf_opensees_input_summary(section_field, yaml_file, gauss_points)

    # 4. Run one OpenSees model for each requested uniform mesh density.
    results: List[ModelResult] = []
    for n_elems in ELEMENT_COUNTS:
        model_id = f"uniform_{n_elems}"
        label = f"uniform {n_elems}"

        # Sample CSF at the element nodes and Gauss integration stations.
        projection = build_csf_opensees_projection(
            section_field=section_field,
            n_elems=n_elems,
            n_gauss_points=gauss_points,
        )

        # Build and solve the corresponding OpenSees model.
        result = run_opensees_model(
            projection=projection,
            model_id=model_id,
            label=label,
        )
        results.append(result)

    # 5. Write numerical outputs.
    tip_csv_file = write_tip_response_csv(output_dir, results)
    report_file = write_markdown_report(output_dir, results, yaml_file, gauss_points)

    # 6. Write plots. These calls save figures and close them; they do not block
    #    the command-line workflow.
    plot_tip_displacement(output_dir, results)
    plot_tip_torsional_rotation(output_dir, results)
    #volume_plot_file = plot_csf_volume_3d(output_dir, section_field)

    # 7. Print final file locations and the same compact response table.
    print("\nDONE")
    print(f"Tip response CSV: {tip_csv_file}")
    print(f"Markdown report: {report_file}")
    print(f"Tip displacement plot: {output_dir / 'plot_tip_displacement_convergence.png'}")
    print(f"Tip torsional rotation plot: {output_dir / 'plot_tip_torsional_rotation_convergence.png'}")

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
    vis = Visualizer(section_field)
    vis.plot_volume_3d(
        show_end_sections=True,
        line_percent=15.0,
        seed="w",
        title="Ruled volume (vertex-connection lines)",
        ax=None
    )
    plt.show()
    
if __name__ == "__main__":
    main()

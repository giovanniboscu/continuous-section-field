"""
Convert a CSF YAML tower model into BModes and ElastoDyn tower inputs.

Outputs:
  1. <stem>_ElastoDyn_Tower.dat   OpenFAST-compatible ElastoDyn tower file
  2. <stem>_BModes_tower.bmt      BModes distributed-properties file
  3. <stem>_BModes_tower.bmi      BModes main input file (if RNA data are provided)

Optional complete-pipeline steps:
  4. run BModes automatically if --bmodes-exe is provided
  5. parse the BModes .out file
  6. fit ElastoDyn mode-shape coefficients
  7. rewrite <stem>_ElastoDyn_Tower.dat with fitted TwFAM*Sh and TwSSM*Sh

Requirements:
  pip install csfpy pyyaml numpy
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml

from csf import section_full_analysis
from csf.io.csf_reader import CSFReader


# ============================================================================
# Command-line interface
# ============================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert a CSF YAML tower model to BModes and ElastoDyn inputs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("yaml", help="CSF geometry YAML file")

    # Tower material.
    p.add_argument("--E", type=float, default=210e9, help="Young's modulus [Pa]")
    p.add_argument("--G", type=float, default=80.8e9, help="Shear modulus [Pa]")
    p.add_argument("--rho", type=float, default=8500.0, help="Density [kg/m3]")
    p.add_argument("--n", type=int, default=11, help="Number of output stations")
    p.add_argument("--damp", type=float, default=1.0, help="Structural damping ratio [%%]")
    p.add_argument("--out", type=str, default=None, help="Output filename stem")

    # RNA tip-mass data for BModes .bmi generation.
    rna = p.add_argument_group(
        "RNA tip-mass",
        "All six parameters are required together to generate the BModes .bmi file.",
    )
    rna.add_argument("--mass-tip", type=float, default=None, help="Total RNA mass [kg]")
    rna.add_argument("--ixx-tip", type=float, default=None, help="RNA side-to-side inertia [kg m^2]")
    rna.add_argument("--iyy-tip", type=float, default=None, help="RNA fore-aft inertia [kg m^2]")
    rna.add_argument("--izz-tip", type=float, default=None, help="RNA torsional inertia [kg m^2]")
    rna.add_argument("--cm-loc", type=float, default=None, help="RNA center-of-mass lateral offset [m]")
    rna.add_argument("--cm-axial", type=float, default=None, help="RNA center-of-mass axial offset [m]")

    # Complete-pipeline options.
    p.add_argument(
        "--bmodes-exe",
        type=str,
        default=None,
        help="Path to BModes executable. If provided, BModes is run automatically.",
    )
    p.add_argument(
        "--bmodes-out",
        type=str,
        default=None,
        help="Path to an existing BModes .out file to parse and inject into ElastoDyn.",
    )
    p.add_argument(
        "--ss-mode-ids",
        type=int,
        nargs=2,
        default=None,
        metavar=("M1", "M2"),
        help="Explicit 1-based BModes mode numbers for side-to-side mode 1 and 2.",
    )
    p.add_argument(
        "--fa-mode-ids",
        type=int,
        nargs=2,
        default=None,
        metavar=("M1", "M2"),
        help="Explicit 1-based BModes mode numbers for fore-aft mode 1 and 2.",
    )
    return p.parse_args()


# ============================================================================
# CSF helpers
# ============================================================================

def load_csf_field(yaml_path: str):
    """Load a CSF geometry YAML and return (field, z0, z1, issues)."""
    read_result = CSFReader().read_file(yaml_path)
    field = read_result.field

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    z0 = float(data["CSF"]["sections"]["S0"]["z"])
    z1 = float(data["CSF"]["sections"]["S1"]["z"])
    return field, z0, z1, read_result.issues


def _extract_torsion_constant(sa: dict) -> float:
    """
    Return a scalar torsional constant for BModes.

    Preference order:
      1) J_sv_cell first component, if available and positive
      2) J_sv_wall
      3) J_s_vroark
      4) K_torsion
      5) Ip
    """
    j_cell = sa.get("J_sv_cell")
    if isinstance(j_cell, (tuple, list)) and len(j_cell) >= 1:
        try:
            val = float(j_cell[0])
            if val > 0.0:
                return val
        except Exception:
            pass
    if isinstance(j_cell, (int, float)) and float(j_cell) > 0.0:
        return float(j_cell)

    for key in ("J_sv_wall", "J_s_vroark", "K_torsion", "Ip"):
        val = sa.get(key)
        if isinstance(val, (int, float)) and float(val) > 0.0:
            return float(val)

    return 0.0


def compute_properties(field, z_stations: Iterable[float]):
    """
    Compute section properties at each z station using csfpy.

    Returns a list of dictionaries with keys:
      z, A, Ix, Iy, Jt
    """
    results = []
    for z in z_stations:
        sa = section_full_analysis(field.section(float(z)))
        results.append(
            {
                "z": float(z),
                "A": float(sa["A"]),
                "Ix": float(sa["Ix"]),
                "Iy": float(sa["Iy"]),
                "Jt": _extract_torsion_constant(sa),
            }
        )
    return results


# ============================================================================
# BModes output parsing and fitting
# ============================================================================

def read_bmodes_out(filename: str):
    """
    Read a BModes .out file.

    Returns:
      frequencies : list[float]
      mode_shapes : list[np.ndarray]

    Each mode-shape array has columns:
      span_loc, s-s disp, s-s slope, f-a disp, f-a slope, twist
    """
    frequencies = []
    mode_shapes = []

    with open(filename, encoding="utf-8", errors="ignore") as f:
        first_line = f.readline()
        if "BModes" not in first_line:
            raise ValueError(f'File "{filename}" does not look like a BModes .out file.')

        row_string = first_line
        while row_string:
            row_string = f.readline()
            if not row_string:
                break
            freq_match = re.search(r"freq\s*=\s*([+\-]?[0-9]*\.?[0-9]+(?:[Ee][+\-]?[0-9]+)?)", row_string)
            if freq_match:
                frequencies.append(float(freq_match.group(1)))
                # Skip blank line, header line, blank line.
                f.readline()
                f.readline()
                f.readline()
                data = []
                while True:
                    row_data = f.readline()
                    if (not row_data) or len(row_data.strip()) == 0 or row_data.startswith("==="):
                        break
                    data.append(row_data.split())
                mode_shapes.append(np.asarray(data, dtype=float))

    if not frequencies or not mode_shapes:
        raise ValueError(f'No modal data were found in "{filename}".')

    return frequencies, mode_shapes


def fit_modal_coefficients(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Fit ElastoDyn coefficients a2..a6 with the exact constraint:
      a2 + a3 + a4 + a5 + a6 = 1
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    x = (x - x.min()) / (x.max() - x.min())

    tip = float(y[-1])
    if abs(tip) <= 1.0e-14:
        idx = int(np.argmax(np.abs(y)))
        tip = float(y[idx])
    if abs(tip) <= 1.0e-14:
        raise ValueError("Cannot fit a mode shape with near-zero displacement everywhere.")

    y = y / tip
    if y[-1] < 0.0:
        y = -y

    # Eliminate a6 = 1 - (a2 + a3 + a4 + a5)
    b2 = x**2 - x**6
    b3 = x**3 - x**6
    b4 = x**4 - x**6
    b5 = x**5 - x**6
    rhs = y - x**6

    A = np.column_stack([b2, b3, b4, b5])
    a2, a3, a4, a5 = np.linalg.lstsq(A, rhs, rcond=None)[0]
    a6 = 1.0 - (a2 + a3 + a4 + a5)
    return np.array([a2, a3, a4, a5, a6], dtype=float)


def identify_bending_modes(
    frequencies: list[float],
    mode_shapes: list[np.ndarray],
    ss_mode_ids: list[int] | None = None,
    fa_mode_ids: list[int] | None = None,
):
    """
    Identify BModes bending modes to map into ElastoDyn.

    Automatic selection:
      - classify by dominant bending displacement
      - penalize modes with strong twist participation
      - take the two best low-frequency candidates for each family

    Manual override:
      - ss_mode_ids / fa_mode_ids are 1-based BModes mode numbers
    """
    if ss_mode_ids is not None and fa_mode_ids is not None:
        return {
            "SS1": ss_mode_ids[0] - 1,
            "SS2": ss_mode_ids[1] - 1,
            "FA1": fa_mode_ids[0] - 1,
            "FA2": fa_mode_ids[1] - 1,
        }

    candidates = []
    for i, (freq, data) in enumerate(zip(frequencies, mode_shapes)):
        ss_amp = float(np.max(np.abs(data[:, 1])))
        fa_amp = float(np.max(np.abs(data[:, 3])))
        tw_amp = float(np.max(np.abs(data[:, 5])))
        dom_amp = max(ss_amp, fa_amp)
        if dom_amp <= 1.0e-12:
            continue
        family = "SS" if ss_amp >= fa_amp else "FA"
        twist_ratio = tw_amp / dom_amp if dom_amp > 0.0 else np.inf
        candidates.append(
            {
                "idx": i,
                "family": family,
                "freq": float(freq),
                "twist_ratio": float(twist_ratio),
            }
        )

    ss = [c for c in candidates if c["family"] == "SS"]
    fa = [c for c in candidates if c["family"] == "FA"]

    if len(ss) < 2 or len(fa) < 2:
        raise ValueError(
            "Automatic mode identification failed. Provide --ss-mode-ids and --fa-mode-ids explicitly."
        )

    ss.sort(key=lambda c: (c["twist_ratio"], c["freq"]))
    fa.sort(key=lambda c: (c["twist_ratio"], c["freq"]))

    ss_best = sorted(ss[: max(2, min(6, len(ss)))], key=lambda c: c["freq"])
    fa_best = sorted(fa[: max(2, min(6, len(fa)))], key=lambda c: c["freq"])

    return {
        "SS1": ss_best[0]["idx"],
        "SS2": ss_best[1]["idx"],
        "FA1": fa_best[0]["idx"],
        "FA2": fa_best[1]["idx"],
    }


def build_modal_payload(
    bmodes_out: str,
    ss_mode_ids: list[int] | None = None,
    fa_mode_ids: list[int] | None = None,
):
    """Parse BModes .out and return fitted ElastoDyn coefficients."""
    frequencies, mode_shapes = read_bmodes_out(bmodes_out)
    selected = identify_bending_modes(frequencies, mode_shapes, ss_mode_ids, fa_mode_ids)

    payload = {}
    for tag, mode_idx in selected.items():
        data = mode_shapes[mode_idx]
        x = data[:, 0]
        y = data[:, 1] if tag.startswith("SS") else data[:, 3]
        payload[tag] = {
            "mode_number": mode_idx + 1,
            "frequency_hz": float(frequencies[mode_idx]),
            "coeffs": fit_modal_coefficients(x, y),
        }
    return payload


# ============================================================================
# Writers
# ============================================================================

def write_elastodyn(
    outfile: str,
    props: list[dict],
    z0: float,
    z1: float,
    E: float,
    rho: float,
    damp: float,
    yaml_path: str,
    modal_payload: dict | None = None,
) -> None:
    """
    Write an OpenFAST-compatible ElastoDyn tower file.

    This writer deliberately avoids extra comment lines that break the
    OpenFAST tower-file parser.
    """
    L = z1 - z0
    n = len(props)

    coeffs_fa1 = [0.0] * 5 if modal_payload is None else modal_payload["FA1"]["coeffs"]
    coeffs_fa2 = [0.0] * 5 if modal_payload is None else modal_payload["FA2"]["coeffs"]
    coeffs_ss1 = [0.0] * 5 if modal_payload is None else modal_payload["SS1"]["coeffs"]
    coeffs_ss2 = [0.0] * 5 if modal_payload is None else modal_payload["SS2"]["coeffs"]

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("------- ELASTODYN V1.00.* TOWER INPUT FILE -------------------------------------\n")
        f.write("Tower input properties generated from CSF.\n")
        f.write("---------------------- TOWER PARAMETERS ----------------------------------------\n")
        f.write(f"{n}   NTwInpSt   - Number of input stations to specify tower geometry (-)\n")
        f.write(f"{damp:.2f}   TwrFADmp(1)  - Tower 1st fore-aft mode structural damping ratio (%)\n")
        f.write(f"{damp:.2f}   TwrFADmp(2)  - Tower 2nd fore-aft mode structural damping ratio (%)\n")
        f.write(f"{damp:.2f}   TwrSSDmp(1)  - Tower 1st side-to-side mode structural damping ratio (%)\n")
        f.write(f"{damp:.2f}   TwrSSDmp(2)  - Tower 2nd side-to-side mode structural damping ratio (%)\n")
        f.write("---------------------- TOWER ADJUSTMENT FACTORS --------------------------------\n")
        f.write("1.0   FAStTunr(1)  - Tower fore-aft modal stiffness tuner, 1st mode (-)\n")
        f.write("1.0   FAStTunr(2)  - Tower fore-aft modal stiffness tuner, 2nd mode (-)\n")
        f.write("1.0   SSStTunr(1)  - Tower side-to-side stiffness tuner, 1st mode (-)\n")
        f.write("1.0   SSStTunr(2)  - Tower side-to-side stiffness tuner, 2nd mode (-)\n")
        f.write("1.0   AdjTwMa      - Factor to adjust tower mass density (-)\n")
        f.write("1.0   AdjFASt      - Factor to adjust tower fore-aft stiffness (-)\n")
        f.write("1.0   AdjSSSt      - Factor to adjust tower side-to-side stiffness (-)\n")
        f.write("---------------------- DISTRIBUTED TOWER PROPERTIES ----------------------------\n")
        f.write(f"{'HtFract':>14} {'TMassDen':>14} {'TwFAStif':>14} {'TwSSStif':>14}\n")
        f.write(f"{'(-)':>14} {'(kg/m)':>14} {'(Nm^2)':>14} {'(Nm^2)':>14}\n")
        for row in props:
            ht = (row["z"] - z0) / L
            f.write(f"{ht:>14.7E} {rho*row['A']:>14.5E} {E*row['Iy']:>14.5E} {E*row['Ix']:>14.5E}\n")
        f.write("---------------------- TOWER FORE-AFT MODE SHAPES ------------------------------\n")
        for c, val in zip([2, 3, 4, 5, 6], coeffs_fa1):
            f.write(f"{val:.10E}   TwFAM1Sh({c})  - Mode 1, coefficient of x^{c} term\n")
        for c, val in zip([2, 3, 4, 5, 6], coeffs_fa2):
            f.write(f"{val:.10E}   TwFAM2Sh({c})  - Mode 2, coefficient of x^{c} term\n")
        f.write("---------------------- TOWER SIDE-TO-SIDE MODE SHAPES --------------------------\n")
        for c, val in zip([2, 3, 4, 5, 6], coeffs_ss1):
            f.write(f"{val:.10E}   TwSSM1Sh({c})  - Mode 1, coefficient of x^{c} term\n")
        for c, val in zip([2, 3, 4, 5, 6], coeffs_ss2):
            f.write(f"{val:.10E}   TwSSM2Sh({c})  - Mode 2, coefficient of x^{c} term\n")

    print(f"[ElastoDyn] Written : {outfile}  ({n} stations)")
    print(f"            TMassDen  {rho*props[0]['A']:.2f} ... {rho*props[-1]['A']:.2f} kg/m")
    print(f"            TwFAStif  {E*props[0]['Iy']:.4e} ... {E*props[-1]['Iy']:.4e} N·m2")
    if modal_payload is not None:
        print("            Mode-shape coefficients injected from BModes output")


def write_bmodes_bmt(outfile: str, props: list[dict], z0: float, z1: float, E: float, G: float, rho: float, yaml_path: str) -> None:
    """Write the BModes distributed-properties file."""
    L = z1 - z0
    n = len(props)
    cols = [
        "sec_loc",
        "str_tw",
        "tw_iner",
        "mass_den",
        "flp_iner",
        "edge_iner",
        "flp_stff",
        "edge_stff",
        "tor_stff",
        "axial_stff",
        "cg_offst",
        "sc_offst",
        "tc_offst",
    ]
    units = [
        "(-)",
        "(deg)",
        "(kg-m)",
        "(kg/m)",
        "(kg-m)",
        "(kg-m)",
        "(N-m^2)",
        "(N-m^2)",
        "(N-m^2)",
        "(N)",
        "(m)",
        "(m)",
        "(m)",
    ]
    widths = [12, 10, 13, 13, 13, 13, 15, 15, 15, 15, 10, 10, 10]
    fmts = [".7f", ".4f"] + [".5E"] * 8 + [".4f"] * 3

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("Tower section properties\n")
        f.write(f"{n:<10d} n_secs:     number of tower sections at which properties are specified (-)\n")
        f.write("\n")
        f.write("".join(f"{c:>{w}}" for c, w in zip(cols, widths)) + "\n")
        f.write("".join(f"{u:>{w}}" for u, w in zip(units, widths)) + "\n")
        for row in props:
            vals = [
                (row["z"] - z0) / L,
                0.0,
                rho * row["Jt"],
                rho * row["A"],
                rho * row["Iy"],
                rho * row["Ix"],
                E * row["Iy"],
                E * row["Ix"],
                G * row["Jt"],
                E * row["A"],
                0.0,
                0.0,
                0.0,
            ]
            f.write("".join(f"{v:>{w}{fmt}}" for v, w, fmt in zip(vals, widths, fmts)) + "\n")

    print(f"[BModes]    Written : {outfile}  ({n} stations)")
    print(f"            mass_den  {rho*props[0]['A']:.2f} ... {rho*props[-1]['A']:.2f} kg/m")
    print(f"            flp_stff  {E*props[0]['Iy']:.4e} ... {E*props[-1]['Iy']:.4e} N·m2")


def write_bmodes_bmi(outfile: str, bmt_file: str, z0: float, z1: float, n_stations: int, rna: dict, yaml_path: str) -> None:
    """Write the BModes main input file for a land-based tower."""
    H = z1 - z0
    bmt_rel = os.path.basename(bmt_file)
    el_loc = np.linspace(0.0, 1.0, n_stations)
    el_str = "  ".join(f"{v:.6f}" for v in el_loc)

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("======================   BModes v3.00 Main Input File   =======================\n")
        f.write(f"Generated by csf_to_elastodyn.py from: {yaml_path}\n")
        f.write("\n")
        f.write("--------- General parameters -----------------------------------------------\n")
        f.write("False     Echo         Echo input file contents to *.echo file if true.\n")
        f.write("2         beam_type    1: blade, 2: tower\n")
        f.write("0.0       rot_rpm      rotor speed [rpm], automatically set to zero for tower\n")
        f.write("1.0       rpm_mult     rotor-speed multiplicative factor (-)\n")
        f.write(f"{H:.4f}    radius       flexible tower height [m]  (z1 - z0)\n")
        f.write("0.0       rroot        rigid-base height above ground [m]  (0 for land-based)\n")
        f.write("0.0       precone      automatically zero for tower\n")
        f.write("0.0       bl_thp       automatically zero for tower\n")
        f.write("1         hub_conn     retained for BModes format compatibility\n")
        f.write("20        modepr       number of modes to be printed (-)\n")
        f.write("True      TabDelim     tab-delimited output tables\n")
        f.write("False     mid_node_tw  no mid-node twist outputs\n")
        f.write("\n")
        f.write("--------- Tip-mass (RNA: rotor + nacelle + hub) --------------------------------\n")
        f.write(f"{rna['mass_tip']:.4f}    tip_mass   total RNA mass [kg]\n")
        f.write(f"{rna['cm_loc']:.6f}    cm_loc     RNA center-of-mass lateral offset [m]\n")
        f.write(f"{rna['cm_axial']:.6f}    cm_axial   RNA center-of-mass axial offset [m]\n")
        f.write(f"{rna['ixx_tip']:.4f}    ixx_tip    RNA side-to-side inertia [kg m^2]\n")
        f.write(f"{rna['iyy_tip']:.4f}    iyy_tip    RNA fore-aft inertia [kg m^2]\n")
        f.write(f"{rna['izz_tip']:.4f}    izz_tip    RNA torsional inertia [kg m^2]\n")
        f.write("0.0       ixy_tip    cross product of inertia xy [kg m^2]\n")
        f.write("0.0       izx_tip    cross product of inertia zx [kg m^2]\n")
        f.write("0.0       iyz_tip    cross product of inertia yz [kg m^2]\n")
        f.write("\n")
        f.write("--------- Distributed-property identifiers --------------------------------------\n")
        f.write("1         id_mat         material type: 1=isotropic\n")
        f.write(f"'{bmt_rel}'   sec_props_file   distributed properties file (same folder)\n")
        f.write("\n")
        f.write("Property scaling factors..............................\n")
        f.write("1.0 sec_mass_mult\n")
        f.write("1.0 flp_iner_mult\n")
        f.write("1.0 lag_iner_mult\n")
        f.write("1.0 flp_stff_mult\n")
        f.write("1.0 edge_stff_mult\n")
        f.write("1.0 tor_stff_mult\n")
        f.write("1.0 axial_stff_mult\n")
        f.write("1.0 cg_offst_mult\n")
        f.write("1.0 sc_offst_mult\n")
        f.write("1.0 tc_offst_mult\n")
        f.write("\n")
        f.write("--------- Finite element discretization -----------------------------------------\n")
        f.write(f"{n_stations - 1} nselt\n")
        f.write("Distance of element boundary nodes from root (normalized), el_loc()\n")
        f.write(f"{el_str}\n")
        f.write("\n")
        f.write("--------- Tower support ----------------------------------------------------------\n")
        f.write("0 tow_support\n")

    print(f"[BModes]    Written : {outfile}")
    print(f"            RNA mass  {rna['mass_tip']:.0f} kg")
    print(f"            iyy_tip   {rna['iyy_tip']:.0f} kg·m2  (FA)")
    print(f"            ixx_tip   {rna['ixx_tip']:.0f} kg·m2  (SS)")


# ============================================================================
# BModes execution
# ============================================================================

def run_bmodes(bmodes_exe: str, bmi_file: str) -> str:
    """Run BModes and return the expected .out path."""
    bmi_path = Path(bmi_file).resolve()
    out_path = bmi_path.with_suffix(".out")
    subprocess.run([str(Path(bmodes_exe).resolve()), bmi_path.name], cwd=str(bmi_path.parent), check=True)
    if not out_path.exists():
        raise FileNotFoundError(f'BModes completed but output file "{out_path}" was not found.')
    return str(out_path)


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    args = parse_args()

    stem = args.out if args.out else os.path.splitext(args.yaml)[0]
    out_elastodyn = stem + "_ElastoDyn_Tower.dat"
    out_bmt = stem + "_BModes_tower.bmt"
    out_bmi = stem + "_BModes_tower.bmi"

    rna_params = {
        "mass_tip": args.mass_tip,
        "ixx_tip": args.ixx_tip,
        "iyy_tip": args.iyy_tip,
        "izz_tip": args.izz_tip,
        "cm_loc": args.cm_loc,
        "cm_axial": args.cm_axial,
    }
    have_all_rna = all(v is not None for v in rna_params.values())
    have_any_rna = any(v is not None for v in rna_params.values())

    if have_any_rna and not have_all_rna:
        raise ValueError(
            "RNA parameters are partial. Provide all six: --mass-tip --ixx-tip --iyy-tip --izz-tip --cm-loc --cm-axial"
        )
    if args.bmodes_exe and not have_all_rna and not args.bmodes_out:
        raise ValueError(
            "BModes automatic execution requires all RNA parameters so the .bmi file can be generated."
        )

    print()
    field, z0, z1, issues = load_csf_field(args.yaml)
    print(f"CSF file  : {args.yaml}")
    print(f"z range   : {z0} -> {z1} m")
    print(f"Stations  : {args.n}")
    print(f"Material  : E={args.E:.3e} Pa   G={args.G:.3e} Pa   rho={args.rho:.1f} kg/m3")
    if have_all_rna:
        print("RNA       : provided — .bmi will be generated")
    else:
        print("RNA       : missing (mass_tip, ixx_tip, iyy_tip, izz_tip, cm_loc, cm_axial) — .bmi will be skipped")
    if issues:
        for issue in issues:
            print(f"CSF issue : {issue.severity.value} {issue.code} — {issue.message}")
    print()

    z_stations = list(np.linspace(z0, z1, args.n))
    props = compute_properties(field, z_stations)

    write_elastodyn(out_elastodyn, props, z0, z1, args.E, args.rho, args.damp, args.yaml, modal_payload=None)
    print()
    write_bmodes_bmt(out_bmt, props, z0, z1, args.E, args.G, args.rho, args.yaml)
    print()

    if have_all_rna:
        write_bmodes_bmi(out_bmi, out_bmt, z0, z1, args.n, rna_params, args.yaml)
        print()

    bmodes_out = None
    if args.bmodes_out:
        bmodes_out = args.bmodes_out
    elif args.bmodes_exe:
        print(f"[BModes]    Running  : {args.bmodes_exe} {out_bmi}")
        bmodes_out = run_bmodes(args.bmodes_exe, out_bmi)
        print(f"[BModes]    Output   : {bmodes_out}")
        print()

    if bmodes_out:
        payload = build_modal_payload(
            bmodes_out,
            ss_mode_ids=args.ss_mode_ids,
            fa_mode_ids=args.fa_mode_ids,
        )
        write_elastodyn(out_elastodyn, props, z0, z1, args.E, args.rho, args.damp, args.yaml, modal_payload=payload)
        print()
        print("Pipeline status:")
        print(f"  1. ElastoDyn distributed file : {out_elastodyn}")
        print(f"  2. BModes auxiliary file      : {out_bmt}")
        if have_all_rna:
            print(f"  3. BModes main file           : {out_bmi}")
        print(f"  4. BModes output parsed       : {bmodes_out}")
        print("  5. ElastoDyn mode-shape coefficients injected automatically")
    else:
        print("Next steps:")
        if not have_all_rna:
            print(f"  1. Provide RNA parameters to generate {out_bmi}:")
            print("     --mass-tip  --ixx-tip  --iyy-tip  --izz-tip  --cm-loc  --cm-axial")
            print(f"  2. Run BModes on            : {out_bmt}  (with a manually written .bmi)")
            print(f"  3. Re-run this script with  : --bmodes-out <BModes .out>")
        else:
            print(f"  1. Run BModes on            : {out_bmi}")
            print(f"  2. Re-run this script with  : --bmodes-out {Path(out_bmi).with_suffix('.out')}")
            print(f"     or set --bmodes-exe to execute BModes automatically")
        print(f"  4. Set TwrFile in ElastoDyn : {out_elastodyn}")


if __name__ == "__main__":
    main()

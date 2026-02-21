"""
continuous section field + property digestor + 2D/3D visualization

Assumptions (explicit):
- Two endpoint sections exist at z0 and z1.
- Same number of polygons in start/end.
- For each polygon: same number of vertices in start/end.
- Vertex ordering is already consistent (your matching is given/assumed).
- Polygons are simple enough for shoelace formulas (no self-intersections).

Dependencies: matplotlib (standard in most Python setups).
"""
from __future__ import annotations
import traceback
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from typing import Tuple, Dict, Optional, List
import math
import random
import warnings
import os
import sys
import numbers
import textwrap
#import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 
import re
from datetime import datetime
from typing import overload, Union, Literal
from pathlib import Path
Point = Tuple[float, float]
Segment = Tuple[Point, Point]

# -----------------------------
# Robust 2D segment intersection
# -----------------------------
#
# Your current implementation uses a "strict proper intersection" test:
#     (o1 * o2 < 0) and (o3 * o4 < 0)
# which detects only crossings where the intersection lies strictly inside both segments.
#
# It does NOT detect:
# - touching at endpoints (T-junctions, vertex-on-edge contact),
# - collinear overlaps,
# - near-collinear cases where numerical noise makes orientation() return 0.
#
# The functions below implement a more complete predicate:
# - detects proper crossings,
# - detects endpoint touching,
# - detects collinear overlap,
# while still allowing you to ignore adjacent edges (handled by caller).

EPS_L = 1e-12  # default Use this for: orientation tests, point-on-segment, segment intersection, etc.
EPS_A = 1e-12  # EPS_A: area tolerance. Must scale as S^2. Use this for: "area nearly zero" checks, summed areas, etc.
EPS_K = 1e-12 # Numerical/matrix tolerances.
EPS_K_RTOL = 1e-10
EPS_K_ATOL = 1e-12
DDEBUG = False

# (Optional: se vuoi usare PyYAML quando disponibile)
try:
    import yaml  # type: ignore
except Exception as e:
    print("PyYAML import failed:", repr(e))
    yaml = None

if yaml is not None:
    class XY(tuple):
        """Coppia (x,y) da stampare in flow style."""
        pass

    class CSFDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    def _repr_xy(dumper, data: XY):
        # forza sempre: [x, y]
        return dumper.represent_sequence(
            "tag:yaml.org,2002:seq",
            [float(data[0]), float(data[1])],
            flow_style=True,
        )

    CSFDumper.add_representer(XY, _repr_xy)
else:
    XY = None
    CSFDumper = None



# Add this method inside class ContinuousSectionField.
#
# Goal:
#   Provide an API to compute an AREA BREAKDOWN of one 2D section by MATERIAL WEIGHT (W)
#   without requiring the user to manually manage nested polygons and negative "void" weights.
#
# Model assumptions (CSF nesting rule):
#   - Polygons never intersect; they may touch.
#   - Each polygon has an *immediate container* (or None if outermost), determinable on S0.
#   - The Section returned by self.section(z) already uses RELATIVE weights:
#         w_rel(child) = w_abs(child) - w_abs(container(child))
#     This method reconstructs absolute weights w_abs and assigns area to the exclusive region
#     of each polygon (polygon area minus its immediate children areas).

from typing import Any, Dict, List, Optional, Tuple



#################################################################
# -----------------------------------------------------------------------------
# Plot helper
# -----------------------------------------------------------------------------

def plot_section_variation(
    stations_data: Sequence[Dict[str, Any]],
    filename: str = "section_variation.png",
    show: bool = False,
) -> str:
    """
    Plot a quick visual preview of how a few properties vary along z.

    Notes
    -----
    - This function is optional. It only runs if matplotlib is available.
    - Units are intentionally NOT printed; they depend on the user's consistent unit system.
    - The function expects each station dict to have at least:
        'z', 'A', 'Ix', 'Iy', 'J'

    Parameters
    ----------
    stations_data:
        List of station dictionaries produced by _compute_station_data(...)
    filename:
        Path to save the plot image.
    show:
        If True, calls plt.show(). Otherwise it only saves.

    Returns
    -------
    str:
        The image path written to disk.

    Raises
    ------
    RuntimeError:
        If matplotlib is not available.
    """

    z = [st['z'] for st in stations_data]
    area = [st['A'] for st in stations_data]
    i33 = [st['Ix'] for st in stations_data]
    i22 = [st['Iy'] for st in stations_data]
    j = [st['J'] for st in stations_data]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Plot Area
    ax1.plot(z, area, 'o-', color='blue', label='Area [m²]')
    ax1.set_ylabel('Cross Section Area [m²]')
    ax1.grid(True, linestyle='--')
    ax1.legend()
    ax1.set_title('Variation of Geometric Properties along Z (Absolute)')

    # Plot Inertia and Torsion
    ax2.plot(z, i33, 's-', color='red', label='I33 (Strong Axis) [m⁴]')
    ax2.plot(z, i22, 'd-', color='green', label='I22 (Weak Axis) [m⁴]')
    ax2.plot(z, j, 'x--', color='purple', label='J (Torsion) [m⁴]')
    ax2.set_xlabel('Z coordinate [m]')
    ax2.set_ylabel('Inertia / Torsion [m⁴]')
    ax2.grid(True, linestyle='--')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(filename)
    print(f"[PLOT] Preview saved as '{filename}'")
    if show:
        plt.show()



# -----------------------------------------------------------------------------
# Station generation
# -----------------------------------------------------------------------------
def get_lobatto_intervals(z_min: float, z_max: float, n_intervals: int) -> "np.ndarray":
    """
    Compute Gauss-Lobatto stations for a given number of intervals.

    Why "intervals" and not "points"?
    --------------------------------
    For a beam discretization, users often think in terms of N segments (intervals).
    Gauss-Lobatto rules include both endpoints, so the number of stations is:

        n_stations = n_intervals + 1

    The previous naming (get_lobatto_points(..., n_points)) easily leads to confusion
    because the implementation returns n_points+1 stations for n_points >= 3.

    Parameters
    ----------
    z_min, z_max:
        Endpoints of the interval in physical coordinates.
    n_intervals:
        Number of intervals. Must be >= 1.

    Returns
    -------
    np.ndarray:
        Sorted station coordinates of length n_intervals + 1.

    Implementation detail
    ---------------------
    We use a Jacobi matrix eigenvalue method to compute the internal Lobatto nodes for
    the (n_stations)-point rule, then map from [-1,1] to [z_min,z_max].

    Raises
    ------
    ValueError:
        If n_intervals < 1
    RuntimeError:
        If numpy is not available.
    """
    if np is None:
        raise RuntimeError("numpy is required for get_lobatto_intervals().")
    if n_intervals < 1:
        raise ValueError("n_intervals must be >= 1.")

    n_stations = n_intervals + 1

    # Trivial cases:
    if n_stations == 2:
        nodes = np.array([-1.0, 1.0], dtype=float)
    elif n_stations == 1:
        nodes = np.array([0.0], dtype=float)
    else:
        # For an n_stations-point Lobatto rule, there are m = n_stations-2 internal nodes.
        n = n_stations
        m = n - 2  # number of internal nodes => H must be m x m

        # Off-diagonal coefficients have length (m-1)
        i = np.arange(1, m, dtype=float)  # 1..m-1
        a = np.sqrt(i * (i + 2.0) / ((2.0 * i + 1.0) * (2.0 * i + 3.0)))

        # Jacobi matrix (symmetric tridiagonal) of size m x m
        H = np.zeros((m, m), dtype=float)
        H[np.arange(m - 1), np.arange(1, m)] = a
        H[np.arange(1, m), np.arange(m - 1)] = a

        internal_nodes = np.sort(np.linalg.eigvalsh(H))
        nodes = np.concatenate((np.array([-1.0]), internal_nodes, np.array([1.0])))

    # Map [-1, 1] -> [z_min, z_max]
    z_min_f = float(z_min)
    z_max_f = float(z_max)
    return 0.5 * (nodes + 1.0) * (z_max_f - z_min_f) + z_min_f


# -----------------------------------------------------------------------------
# Core property sampling
# -----------------------------------------------------------------------------
def _compute_station_data(
    field: Any,
    z_values: Sequence[float],
) -> List[Dict[str, Any]]:
    """
    Sample the CSF field at the provided z positions and compute section properties.

    This function delegates the actual validation/computation to the CSF library's
    analysis function. We intentionally do NOT "second-guess" the CSF analysis.

    Expected CSF interface
    ----------------------
    - field.section(z) -> a section object at that z
    - csf.section_field.section_full_analysis(section,alpha) -> dict with keys like:
        'A', 'Cx', 'Cy', 'Ix', 'Iy', 'Ixy', 'J', ...
      (We fall back to sensible defaults if some keys are missing.)

    Returns
    -------
    List[Dict[str, Any]]:
        Each dict contains:
          id (1-based),
          z,
          Cx, Cy,
          A, Ix, Iy, Ixy, J,
          plus any extra keys the analysis returns (stored under 'analysis_raw').

    Raises
    ------
    RuntimeError:
        If section_full_analysis cannot be imported.
    """
    try:
        from csf.section_field import section_full_analysis  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Cannot import csf.section_field.section_full_analysis; "
            "this template generator requires the CSF analysis function."
        ) from e

    out: List[Dict[str, Any]] = []

    for i, z in enumerate(z_values):
        section_at_z = field.section(float(z))
        analysis = section_full_analysis(section_at_z,alpha = 1.0,) 

        cx = analysis.get("Cx", analysis.get("cx", 0.0))
        cy = analysis.get("Cy", analysis.get("cy", 0.0))
        A = analysis.get("A", analysis.get("area", 0.0))
        Ix = analysis.get("Ix", analysis.get("ix", analysis.get("ixx_g", 0.0)))
        Iy = analysis.get("Iy", analysis.get("iy", analysis.get("iyy_g", 0.0)))
        Ixy = analysis.get("Ixy", analysis.get("ixy", 0.0))
        # Torsion: different libraries may report 'J' or 'K_torsion' etc.
        J = analysis.get("J", analysis.get("j", analysis.get("K_torsion", 0.0)))
        print
        out.append(
            {
                "id": i + 1,
                "z": float(z),
                "Cx": float(cx),
                "Cy": float(cy),
                "A": float(A),
                "Ix": float(Ix),
                "Iy": float(Iy),
                "Ixy": float(Ixy),
                "J": float(J),
                "analysis_raw": analysis,
            }
        )

    return out


# -----------------------------------------------------------------------------
# Template pack writer
# -----------------------------------------------------------------------------
_Mode = Literal["BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"]

def write_sap2000_template_pack(
    field: Any,
    n_intervals: int = 20,
    template_filename: str = "template.txt",
    *,
    mode: _Mode = "BOTH",
    section_prefix: str = "SEC",
    joint_prefix: str = "J",
    frame_prefix: str = "F",
    material_name: str = "S355",
    E_ref: Optional[float] = None,
    nu: Optional[float] = None,
    include_plot: bool = True,
    plot_filename: str = "section_variation.png",
    show_plot: bool = False,
    z_values: Optional[List[float]] = None,
) -> str:
    """
    Generate a SAP2000 "template pack" text file from a CSF field.

    What this produces
    ------------------
    A single text file (template pack) that contains:
      - assumptions and modeling modes,
      - station list (z) and section naming for each station,
      - a full numeric property table per station (the "core"),
      - copy/paste-ready candidate SAP2000 table blocks with placeholders,
      - a checklist of items that might still be required in SAP2000.

    What this does NOT claim
    ------------------------
    This file is NOT guaranteed to import as-is into SAP2000.
    It is designed as a complete data pack to enable a user (or a downstream script)
    to construct a correct SAP2000 import file for their specific SAP2000 version.

    Parameters
    ----------
    field:
        A ContinuousSectionField-like object (must have field.s0.z, field.s1.z, and field.section(z)).
    n_intervals:
        Number of intervals along the element; number of stations is n_intervals + 1.
        This parameter is used only when `z_values` is not provided.
    template_filename:
        Output text file path.
    mode:
        "BOTH" -> prints both centroidal and reference-line blocks.
        "CENTROIDAL_LINE" -> prints only centroidal-line blocks.
        "REFERENCE_LINE" -> prints only reference-line blocks.
    section_prefix, joint_prefix, frame_prefix:
        Naming prefixes used in the generated copy/paste blocks.
    material_name:
        A suggested material label. The user may change this in SAP2000.
    E_ref, nu:
        Optional reference elastic constants included as *suggested* values.
        Units are not enforced here; they must be consistent in SAP2000.
    include_plot:
        If True and matplotlib is available, saves a plot image of property variation.
    plot_filename:
        Image path for the plot (saved only if include_plot and matplotlib available).
    show_plot:
        If True, displays the plot interactively (if backend allows).
    z_values:
        Optional explicit station coordinates in absolute z units.

        Backward compatibility behavior:
        - If z_values is None: the function uses the original Gauss-Lobatto generation
          over [z_start, z_end] based on n_intervals (unchanged behavior).
        - If z_values is provided: the function uses the provided station list and does
          not generate Lobatto points.

        Validation for explicit z_values:
        - must be a non-empty list,
        - each value must be numeric,
        - values must be finite,
        - values must be strictly increasing (no duplicates),
        - every value must be within [z_start, z_end].

        This keeps behavior explicit and avoids silently fixing user input.

    Returns
    -------
    str:
        The template file path written.
    """
    if mode not in ("BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"):
        raise ValueError("mode must be one of: BOTH, CENTROIDAL_LINE, REFERENCE_LINE")

    # Extract CSF absolute bounds exactly as before.
    z_start = float(getattr(field.s0, "z"))
    z_end = float(getattr(field.s1, "z"))
    L = z_end - z_start

    # -------------------------------------------------------------------------
    # Station generation / selection
    # -------------------------------------------------------------------------
    # Minimal-impact rule:
    # - keep the original Lobatto path untouched when z_values is not provided;
    # - add a small explicit branch for user-provided stations.
    if z_values is None:
        # Original behavior (fully preserved).
        station_z = get_lobatto_intervals(z_start, z_end, int(n_intervals)).tolist()
    else:
        # Explicit-stations behavior (new, opt-in).
        if not isinstance(z_values, list) or len(z_values) == 0:
            raise ValueError("z_values must be a non-empty list of numeric z coordinates.")

        station_z = []
        for i, v in enumerate(z_values):
            try:
                z = float(v)
            except Exception as e:
                raise ValueError(f"z_values[{i}] is not numeric: {v!r}") from e

            # Finite check without extra imports:
            # NaN fails z == z; infinities are caught by bound checks below.
            if z != z:
                raise ValueError(f"z_values[{i}] is NaN.")

            # Range check in absolute coordinates.
            if z < z_start or z > z_end:
                raise ValueError(
                    f"z_values[{i}]={z} is outside field bounds [{z_start}, {z_end}]."
                )

            station_z.append(z)

        # Strict monotonic increase:
        # no sorting/dedup on purpose (explicit input policy, no silent fixes).
        for i in range(1, len(station_z)):
            if not (station_z[i] > station_z[i - 1]):
                raise ValueError(
                    "z_values must be strictly increasing (no duplicates, no descending values)."
                )

    # Compute section data at selected stations (unchanged downstream flow).
    stations_data = _compute_station_data(field, station_z)

    # Optional plot (best-effort).
    plot_path_written: Optional[str] = None
    if include_plot and plt is not None:
        try:
            plot_path_written = plot_section_variation(
                stations_data,
                filename=plot_filename,
                show=show_plot,
            )
        except Exception:
            # Plotting must never prevent template creation.
            plot_path_written = None

    # -------------------------------------------------------------------------
    # Build template text (unchanged logic below)
    # -------------------------------------------------------------------------
    lines: List[str] = []
    lines.append("SAP2000 TEMPLATE PACK (from CSF)")
    lines.append("=" * 78)
    lines.append("")
    lines.append("DISCLAIMER")
    lines.append("-" * 78)
    lines.append(
        "This template is a data pack intended to help build a SAP2000 import file. "
        "It may require adaptation depending on SAP2000 version/table format."
    )
    lines.append("")
    lines.append("MODEL METADATA")
    lines.append("-" * 78)
    lines.append(f"z_start      : {z_start:.9g}")
    lines.append(f"z_end        : {z_end:.9g}")
    lines.append(f"length (L)   : {L:.9g}")
    lines.append(f"stations     : {len(stations_data)}")
    lines.append(f"mode         : {mode}")
    lines.append(f"material     : {material_name}")
    if E_ref is not None:
        lines.append(f"E_ref        : {float(E_ref):.9g}")
    if nu is not None:
        lines.append(f"nu           : {float(nu):.9g}")
    if plot_path_written is not None:
        lines.append(f"plot         : {plot_path_written}")
    lines.append("")

    lines.append("STATIONS (CORE)")
    lines.append("-" * 78)
    lines.append(
        "Columns: id, z, Cx, Cy, A, Ix, Iy, Ixy, J"
    )
    for d in stations_data:
        lines.append(
            f"{d['id']:>4d}  {d['z']:.9g}  {d['Cx']:.9g}  {d['Cy']:.9g}  "
            f"{d['A']:.9g}  {d['Ix']:.9g}  {d['Iy']:.9g}  {d['Ixy']:.9g}  {d['J']:.9g}"
        )
    lines.append("")

    lines.append("SECTION NAMES")
    lines.append("-" * 78)
    for d in stations_data:
        lines.append(f"{section_prefix}{d['id']:04d} @ z={d['z']:.9g}")
    lines.append("")

    lines.append("CANDIDATE TABLE BLOCKS (EDIT/ADAPT FOR YOUR SAP2000 VERSION)")
    lines.append("-" * 78)
    lines.append("1) Frame Section Property Definitions")
    lines.append(
        "   - Create one section per station using the core properties above."
    )
    lines.append(
        "   - Map section names with section_prefix + station id."
    )
    lines.append("")
    lines.append("2) Joint Coordinates (if using segmented model)")
    lines.append(
        "   - Build joints along the member axis with joint_prefix and z station coordinates."
    )
    lines.append("")
    lines.append("3) Connectivity and Section Assignment")
    lines.append(
        "   - Create frame objects with frame_prefix and assign station-based sections."
    )
    lines.append("")

    if mode in ("BOTH", "CENTROIDAL_LINE"):
        lines.append("MODE BLOCK: CENTROIDAL_LINE")
        lines.append("-" * 78)
        lines.append(
            "Use Cx, Cy at each station to define centroidal alignment if needed."
        )
        lines.append("")

    if mode in ("BOTH", "REFERENCE_LINE"):
        lines.append("MODE BLOCK: REFERENCE_LINE")
        lines.append("-" * 78)
        lines.append(
            "Keep a fixed geometric/reference axis and assign varying station properties."
        )
        lines.append("")

    lines.append("CHECKLIST")
    lines.append("-" * 78)
    lines.append("[] Confirm units consistency (geometry, E, inertia, torsion).")
    lines.append("[] Confirm SAP2000 table schema/version for import.")
    lines.append("[] Confirm local axis conventions and sign conventions.")
    lines.append("[] Confirm material definition exists in model.")
    lines.append("[] Confirm section assignment strategy (per object/per segment).")
    lines.append("")

    text = "\n".join(lines).rstrip() + "\n"

    # Ensure output directory exists.
    out_path = Path(template_filename)
    if out_path.parent and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    return str(out_path)



#--------------------------------------------------------------------------------
def write_sap2000_template_pack2toremove(
    field: Any,
    n_intervals: int = 20,
    template_filename: str = "template.txt",
    *,
    mode: _Mode = "BOTH",
    section_prefix: str = "SEC",
    joint_prefix: str = "J",
    frame_prefix: str = "F",
    material_name: str = "S355",
    E_ref: Optional[float] = None,
    nu: Optional[float] = None,
    include_plot: bool = True,
    plot_filename: str = "section_variation.png",
    show_plot: bool = False,
) -> str:
    """
    Generate a SAP2000 "template pack" text file from a CSF field.

    What this produces
    ------------------
    A single text file (template pack) that contains:
      - assumptions and modeling modes,
      - station list (z) and section naming for each station,
      - a full numeric property table per station (the "core"),
      - copy/paste-ready candidate SAP2000 table blocks with placeholders,
      - a checklist of items that might still be required in SAP2000.

    What this does NOT claim
    ------------------------
    This file is NOT guaranteed to import as-is into SAP2000.
    It is designed as a complete data pack to enable a user (or a downstream script)
    to construct a correct SAP2000 import file for their specific SAP2000 version.

    Parameters
    ----------
    field:
        A ContinuousSectionField-like object (must have field.s0.z, field.s1.z, and field.section(z)).
    n_intervals:
        Number of intervals along the element; number of stations is n_intervals + 1.
    template_filename:
        Output text file path.
    mode:
        "BOTH" -> prints both centroidal and reference-line blocks.
        "CENTROIDAL_LINE" -> prints only centroidal-line blocks.
        "REFERENCE_LINE" -> prints only reference-line blocks.
    section_prefix, joint_prefix, frame_prefix:
        Naming prefixes used in the generated copy/paste blocks.
    material_name:
        A suggested material label. The user may change this in SAP2000.
    E_ref, nu:
        Optional reference elastic constants included as *suggested* values.
        Units are not enforced here; they must be consistent in SAP2000.
    include_plot:
        If True and matplotlib is available, saves a plot image of property variation.
    plot_filename:
        Image path for the plot (saved only if include_plot and matplotlib available).
    show_plot:
        If True, displays the plot interactively (if backend allows).

    Returns
    -------
    str:
        The template file path written.
    """
    if mode not in ("BOTH", "CENTROIDAL_LINE", "REFERENCE_LINE"):
        raise ValueError("mode must be one of: BOTH, CENTROIDAL_LINE, REFERENCE_LINE")

    # Extract CSF absolute bounds.
    z_start = float(getattr(field.s0, "z"))
    z_end = float(getattr(field.s1, "z"))
    L = z_end - z_start

    # Generate station coordinates using Lobatto on [z_start, z_end].
    z_values = get_lobatto_intervals(z_start, z_end, int(n_intervals)).tolist()

    stations_data = _compute_station_data(field, z_values)

    # Optional plot (best-effort).
    plot_path_written: Optional[str] = None
    if include_plot and plt is not None:
        try:
            plot_path_written = plot_section_variation(
                stations_data,
                filename=plot_filename,
                show=show_plot,
            )
        except Exception:
            # Plotting must never prevent template creation.
            plot_path_written = None

    # Prepare paths and directory.
    out_path = Path(template_filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Decide whether to include a reference elastic constants block.
    # If E_ref and nu are provided, we compute G_ref (isotropic assumption) as informational.
    G_ref: Optional[float] = None
    if E_ref is not None and nu is not None:
        try:
            G_ref = float(E_ref) / (2.0 * (1.0 + float(nu)))
        except Exception:
            G_ref = None

    # Helper naming functions
    def sec_name(st_id: int) -> str:
        # Stable naming: include station id; users may rename later.
        return f"{section_prefix}_{st_id}"

    def joint_name(st_id: int) -> str:
        return f"{joint_prefix}{st_id}"

    def frame_name(seg_id: int) -> str:
        return f"{frame_prefix}{seg_id}"

    # Write template
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = []
    lines.append("#" * 78)
    lines.append("# SAP2000 TEMPLATE PACK (CSF)")
    lines.append("#" * 78)
    lines.append(f"# Generated: {now}")
    lines.append("#")
    lines.append("# DISCLAIMER:")
    lines.append("#   This file is a DATA + COPY/PASTE TEMPLATE. It is not guaranteed to import")
    lines.append("#   as a complete SAP2000 model without edits, because SAP2000 text tables and")
    lines.append("#   required fields can vary by version and workflow.")
    lines.append("#")
    lines.append("# UNITS:")
    lines.append("#   Units are NOT enforced here. Use one consistent unit system throughout.")
    lines.append("#")
    lines.append("# MODELING MODES SUPPORTED:")
    lines.append("#   1) CENTROIDAL_LINE:")
    lines.append("#      - Nodes follow the centroid (Cx(z), Cy(z)) in the global XY plane.")
    lines.append("#      - The beam axis is the z-direction (absolute z stations).")
    lines.append("#   2) REFERENCE_LINE:")
    lines.append("#      - Nodes lie on a nominal axis (X=0, Y=0), with Z=z.")
    lines.append("#      - Cx(z), Cy(z) are provided as offsets/eccentricities to be applied in SAP.")
    lines.append("#")
    lines.append("# CSF DOMAIN:")
    lines.append(f"#   z_start = {z_start:.6f}")
    lines.append(f"#   z_end   = {z_end:.6f}")
    lines.append(f"#   L       = {L:.6f}")
    lines.append(f"#   n_intervals = {int(n_intervals)}  ->  n_stations = {len(stations_data)}")
    lines.append("#")
    lines.append("# SUGGESTED ELASTIC CONSTANTS (OPTIONAL):")
    lines.append(f"#   material_name = {material_name}")
    if E_ref is not None and nu is not None:
        lines.append(f"#   E_ref = {float(E_ref):.6e}")
        lines.append(f"#   nu    = {float(nu):.6f}")
        if G_ref is not None:
            lines.append(f"#   G_ref = E_ref/(2*(1+nu)) = {G_ref:.6e}  (isotropic)")
        else:
            lines.append("#   G_ref could not be computed (invalid E_ref/nu)")
    else:
        lines.append("#   (not provided) -> define material properties directly in SAP2000 as needed.")
    if plot_path_written:
        lines.append(f"# PREVIEW PLOT: {plot_path_written}")
    lines.append("#" * 78)
    lines.append("")

    # ---------------------------------------------------------------------
    # Stations + naming
    # ---------------------------------------------------------------------
    lines.append("### STATIONS (ABSOLUTE z) + SECTION NAMING")
    lines.append("")
    lines.append("# Each station i is assigned a section name SEC_i (customizable).")
    lines.append("# You can use this mapping to create SAP2000 'General' sections and then")
    lines.append("# assign them to frame segments.")
    lines.append("")
    lines.append("# id, z, section_name")
    for st in stations_data:
        lines.append(f"# {st['id']:>3d}, {st['z']:.6f}, {sec_name(int(st['id']))}")
    lines.append("")

    # ---------------------------------------------------------------------
    # Core properties table (the heart)
    # ---------------------------------------------------------------------
    lines.append("### TABLE C — SECTION PROPERTIES PER STATION (CORE DATA)")
    lines.append("")
    lines.append("# Meaning of columns:")
    lines.append("#   z   : absolute station coordinate")
    lines.append("#   A   : total net area")
    lines.append("#   Cx,Cy: centroid coordinates in the section plane (CSF local axes)")
    lines.append("#   Ix,Iy,Ixy: second moments / product of inertia about centroid (CSF local axes)")
    lines.append("#   J   : torsional constant (as reported by CSF analysis; naming may differ by library)")
    lines.append("#")
    lines.append("# IMPORTANT AXIS NOTE:")
    lines.append("#   SAP2000 uses local axes 1-2-3 for frame sections. If you map CSF (x,y) to SAP (2,3),")
    lines.append("#   a common convention is: Ix -> I33, Iy -> I22, Ixy -> I23. Confirm your axis mapping.")
    lines.append("")
    lines.append("z,A,Cx,Cy,Ix,Iy,Ixy,J,section_name")
    for st in stations_data:
        lines.append(
            f"{st['z']:.10g},"
            f"{st['A']:.10g},"
            f"{st['Cx']:.10g},"
            f"{st['Cy']:.10g},"
            f"{st['Ix']:.10g},"
            f"{st['Iy']:.10g},"
            f"{st['Ixy']:.10g},"
            f"{st['J']:.10g},"
            f"{sec_name(int(st['id']))}"
        )
    lines.append("")

    # ---------------------------------------------------------------------
    # Candidate SAP2000 blocks (copy/paste)
    # ---------------------------------------------------------------------
    lines.append("### TABLE D — COPY/PASTE CANDIDATE SAP2000 TEXT TABLES (VERSION-DEPENDENT)")
    lines.append("")
    lines.append("# These blocks are *starting points* for SAP2000's text-table import.")
    lines.append("# Depending on SAP2000 version, you may need to adjust table names/columns.")
    lines.append("# This template aims to avoid missing numeric data: all values you need are above.")
    lines.append("")

    # --- JOINT COORDINATES (CENTROIDAL LINE) ---
    if mode in ("BOTH", "CENTROIDAL_LINE"):
        lines.append("#### D1) JOINT COORDINATES — CENTROIDAL_LINE")
        lines.append("# Nodes follow centroid coordinates Cx(z), Cy(z).")
        lines.append("# Copy/paste example format (verify table/column names in your SAP2000 version):")
        lines.append('TABLE: "JOINT COORDINATES"')
        for st in stations_data:
            jn = joint_name(int(st["id"]))
            # Use centroid as global XY
            lines.append(
                f"  Joint={jn}  CoordSys=GLOBAL  CoordType=Cartesian  "
                f"XorR={st['Cx']:.6f}  Y={st['Cy']:.6f}  Z={st['z']:.6f}  SpecialJt=No"
            )
        lines.append("")

    # --- JOINT COORDINATES (REFERENCE LINE) ---
    if mode in ("BOTH", "REFERENCE_LINE"):
        lines.append("#### D2) JOINT COORDINATES — REFERENCE_LINE")
        lines.append("# Nodes lie on a nominal axis (X=0, Y=0), with Z=z.")
        lines.append("# Cx(z), Cy(z) are provided later as offsets/eccentricities.")
        lines.append('TABLE: "JOINT COORDINATES"')
        for st in stations_data:
            jn = joint_name(int(st["id"]))
            lines.append(
                f"  Joint={jn}  CoordSys=GLOBAL  CoordType=Cartesian  "
                f"XorR={0.0:.6f}  Y={0.0:.6f}  Z={st['z']:.6f}  SpecialJt=No"
            )
        lines.append("")
        lines.append("#### D2b) OFFSETS / ECCENTRICITIES — REFERENCE_LINE (PLACEHOLDER)")
        lines.append("# SAP2000 has multiple ways to apply offsets (insertion point, joint offsets, frame offsets).")
        lines.append("# This template provides the numerical offsets you would need:")
        lines.append("#   dx = Cx(z), dy = Cy(z)  (signs depend on your axis mapping)")
        lines.append("# Apply them in SAP2000 using your chosen method.")
        lines.append("# id, z, dx, dy")
        for st in stations_data:
            lines.append(f"# {st['id']:>3d}, {st['z']:.6f}, dx={st['Cx']:.6f}, dy={st['Cy']:.6f}")
        lines.append("")

    # --- FRAME CONNECTIVITY ---
    lines.append("#### D3) FRAME CONNECTIVITY (SEGMENTS BETWEEN STATIONS)")
    lines.append("# Discretization: create one frame between each consecutive pair of joints.")
    lines.append("# Example format (verify exact table name/columns):")
    lines.append('TABLE: "CONNECTIVITY - FRAME"')
    for i in range(len(stations_data) - 1):
        n1 = joint_name(int(stations_data[i]["id"]))
        n2 = joint_name(int(stations_data[i + 1]["id"]))
        fn = frame_name(i + 1)
        lines.append(f"  Frame={fn}  JointI={n1}  JointJ={n2}  IsCurved=No")
    lines.append("")

    # --- FRAME SECTION PROPERTIES: GENERAL ---
    lines.append("#### D4) FRAME SECTION PROPERTIES — GENERAL (CANDIDATE)")
    lines.append("# For each station, define a 'General' section with A, Ixx/Iyy/Ixy, and torsion J.")
    lines.append("# NOTE ON TORSION COLUMN NAME:")
    lines.append("#   Different text exports have used different column names (e.g., TorsConst vs TorsProp).")
    lines.append("#   You MUST verify the expected column name in your SAP2000 version.")
    lines.append("#")
    lines.append("# Option A (commonly documented style): use TorsConst=")
    lines.append('TABLE: "FRAME SECTION PROPERTIES 01 - GENERAL"')
    for st in stations_data:
        sn = sec_name(int(st["id"]))
        lines.append(
            f"  SectionName={sn}  Material={material_name}  Shape=General  "
            f"Area={st['A']:.8e}  I33={st['Ix']:.8e}  I22={st['Iy']:.8e}  I23={st['Ixy']:.8e}  "
            f"TorsConst={st['J']:.8e}"
        )
    lines.append("")
    lines.append("# Option B (alternate style): use TorsProp= (if your SAP2000 table expects this name)")
    lines.append("#  (same numeric values; only the torsion column name differs)")
    lines.append("#  Example line:")
    lines.append("#    SectionName=SEC_1 ... Area=... I33=... I22=... I23=... TorsProp=...")
    lines.append("")

    # --- FRAME SECTION ASSIGNMENTS ---
    lines.append("#### D5) FRAME SECTION ASSIGNMENTS (CANDIDATE)")
    lines.append("# Assign each frame segment the section corresponding to its start station.")
    lines.append("# If your workflow uses a dedicated assignment table, paste there.")
    lines.append("# Example format (verify exact table name/columns):")
    lines.append('TABLE: "FRAME SECTION ASSIGNMENTS"')
    for i in range(len(stations_data) - 1):
        fn = frame_name(i + 1)
        sn = sec_name(int(stations_data[i]["id"]))
        lines.append(f"  Frame={fn}  Section={sn}")
    lines.append("")

    # --- MATERIAL PROPERTIES ---
    lines.append("#### D6) MATERIAL PROPERTIES (OPTIONAL TEMPLATE)")
    lines.append("# If your SAP2000 model requires explicit material definitions, use:")
    lines.append("#  - E, nu, and optionally G (if not derived automatically)")
    lines.append("# Units must be consistent with the rest of the model.")
    if E_ref is not None and nu is not None and G_ref is not None:
        lines.append(f"# Suggested: Material={material_name}  E={float(E_ref):.6e}  nu={float(nu):.6f}  G={G_ref:.6e}")
    else:
        lines.append("# (No suggested E_ref/nu provided in this template pack.)")
    lines.append("")

    # ---------------------------------------------------------------------
    # Checklist of missing/unknown items
    # ---------------------------------------------------------------------
    lines.append("### TABLE E — CHECKLIST (MAY STILL BE REQUIRED IN SAP2000)")
    lines.append("")
    lines.append("# The following items are not handled automatically by this template pack and may be")
    lines.append("# required depending on your SAP2000 workflow/model:")
    lines.append("#")
    lines.append("# 1) Units setup in SAP2000 (choose a consistent unit system).")
    lines.append("# 2) Material properties (E, nu, G, density/mass) and design parameters.")
    lines.append("# 3) Frame local axis orientation (rotation about axis 1).")
    lines.append("# 4) Insertion point / offsets / end offsets (especially for REFERENCE_LINE mode).")
    lines.append("# 5) Shear area (AS2/AS3) if your model requires shear deformation effects.")
    lines.append("# 6) Modifiers (A, I, J modifiers), if used in your SAP2000 practice.")
    lines.append("# 7) End releases / boundary conditions / connectivity to the rest of the structure.")
    lines.append("# 8) Loads, combinations, analysis settings, recorders, etc. (model-specific).")
    lines.append("#")
    lines.append("# If you discover that your SAP2000 version requires additional columns in any table,")
    lines.append("# add them in the SAP file and keep using the numeric values from TABLE C above.")
    lines.append("")

    # Write file
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(out_path)


def write_sap2000_geometry(*args: Any, **kwargs: Any) -> str:
    """
    Backward-compatible wrapper.

    Historically this function tried to generate a SAP2000 .s2k directly. In v2 we avoid
    promising direct import correctness and instead generate a template pack.

    Use:
        write_sap2000_template_pack(...)

    This wrapper calls write_sap2000_template_pack with the provided arguments.
    """
    return write_sap2000_template_pack(*args, **kwargs)

#################################################################

def _csf__is_finite_number(x: Any) -> bool:
    """Return True if x can be converted to a finite float."""
    try:
        v = float(x)
    except Exception:
        return False
    return math.isfinite(v)


def _csf__ensure_parent_dir_exists(path: str) -> None:
    """
    Ensure the parent directory exists; otherwise raise CSFError.

    Note: we intentionally do NOT auto-create directories. This makes typos
    in output paths fail fast and is easier to debug.
    """
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        raise CSFError(
            f"Output directory does not exist for yaml_path='{path}'. "
            f"Missing directory: '{parent}'."
        )


def _csf__atomic_write_text(path: str, text: str) -> None:
    """
    Write a file atomically:
      1) write to path + '.tmp'
      2) os.replace to final name
    """
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp_path, path)


def _csf__section_to_Sz_dict(section_obj,nodesection: str) -> Dict[str, Any]:
    """
    Convert a computed Section into the minimal YAML dict format:

      Sz:
        z: <float>
        polygons:
          <poly_name>:
            weight: <float>
            vertices:
              - [x, y]
              - [x, y]
              ...

    Polygon weights are exported exactly as computed at z (already include w(z)).
    """
    out_polys: Dict[str, Any] = {}

    for i, poly in enumerate(section_obj.polygons):
        if not hasattr(poly, "name"):
            raise CSFError(f"Polygon at index {i} has no attribute 'name'.")
        if not hasattr(poly, "weight"):
            raise CSFError(f"Polygon '{getattr(poly,'name','?')}' at index {i} has no attribute 'weight'.")
        if not hasattr(poly, "vertices"):
            raise CSFError(f"Polygon '{getattr(poly,'name','?')}' at index {i} has no attribute 'vertices'.")

        verts_out = []
        for j, v in enumerate(poly.vertices):
            if not hasattr(v, "x") or not hasattr(v, "y"):
                raise CSFError(f"Vertex {j} of polygon '{poly.name}' lacks x/y attributes.")

            x = float(v.x)
            y = float(v.y)

            # If your module defines XY (PyYAML pretty mode), use it to enforce flow style [x, y].
            if "XY" in globals() and globals().get("XY") is not None:
                verts_out.append(globals()["XY"]((x, y)))  # type: ignore[index]
            else:
                verts_out.append([x, y])

        out_polys[str(poly.name)] = {
            "weight": float(poly.weight),
            "vertices": verts_out,
        }

    return {
        nodesection: {
            "z": float(getattr(section_obj, "z", float("nan"))),
            "polygons": out_polys,
        }
    }
#

def _yaml_scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"

    # supporto numeri numpy (np.float64, np.int64, ecc.)
    try:
        import numpy as np
        if isinstance(v, np.generic):
            v = v.item()
    except Exception:
        pass

    if isinstance(v, (int, float)):
        return str(v)

    s = str(v)
    # quote se serve
    if s == "" or any(c in s for c in [":", "#", "\n", "{", "}", "[", "]"]):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _simple_yaml_dump(data, indent: int = 0) -> str:
    sp = "  " * indent

    if isinstance(data, dict):
        out = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                out.append(f"{sp}{k}:")
                out.append(_simple_yaml_dump(v, indent + 1))
            else:
                out.append(f"{sp}{k}: {_yaml_scalar(v)}")
        return "\n".join(out)

    if isinstance(data, list):
        out = []
        for item in data:
            if isinstance(item, (dict, list)):
                out.append(f"{sp}-")
                out.append(_simple_yaml_dump(item, indent + 1))
            else:
                out.append(f"{sp}- {_yaml_scalar(item)}")
        return "\n".join(out)

    # scalare singolo
    return f"{sp}{_yaml_scalar(data)}"




def safe_evaluate_weight_zrelative(formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float,print=True) -> tuple[float, dict]:
    """
    Evaluates a weight formula string safely by trapping all potential exceptions.
    
    This function performs:
    1. Proactive File System check (pre-evaluation).
    2. Mathematical evaluation via eval/evaluate_weight_formula.
    3. Physical constraint validation (e.g., negative results).
    4. Immediate visual reporting via print_evaluation_report.
    """
    # 1. Initialize the internal report structure
    t_pos=z/(z1-z0)
    report = {
        "status": "SUCCESS",
        "error_type": None,
        "message": "Formula evaluated successfully.",
        "suggestion": None,
        "z_pos": z ,
        "t_pos": t_pos,
        "formula": formula.strip()
    }
    
    result = 0.0
    
    try:
        # --- BLOCK 1: PROACTIVE FILE SYSTEM CHECK ---
        # Scan formula for E_lookup('filename') calls using Regex
        # Handles single/double quotes and optional spaces
        match = re.search(r"E_lookup\s*\(\s*['\"](.+?)['\"]\s*\)", report["formula"])
       
        if match:
            filename = match.group(1)
            # Check if file exists on disk BEFORE calling the core logic
            if not os.path.exists(filename):
                report.update({
                    "status": "ERROR",
                    "error_type": "File System Error",
                    "message": f"Lookup file '{filename}' not found.",
                    "suggestion": f"Ensure the file exists in the current directory: {os.getcwd()}"
                })
                print_evaluation_report(0.0, report)
                return 0.0, report

        # --- BLOCK 2: FORMULA EVALUATION ---
        # Attempt to run the core evaluation logic
        result = evaluate_weight_formula_zrelative(formula, p0, p1, z0,z1, z)
        
        # --- BLOCK 3: PHYSICAL VALIDATION ---
        # Check for non-physical results (e.g., negative stiffness or weight)
        if result < 0:
            report.update({
                "status": "WARNING",
                "error_type": "Physical Constraint",
                "message": f"Calculated value is negative ({result:g}).",
                "suggestion": "Verify if a void was intended. Consider using 'np.maximum(0, ...)'."
            })

    # --- BLOCK 4: ERROR TRAPPING ---
    
    except NameError as e:
        # Occurs if a variable (like 'w0' or 'z') is misspelled or 'np' is not loaded
        report.update({
            "status": "ERROR",
            "error_type": "Syntax/Variable Error",
            "message": f"Undefined variable or function: {str(e)}",
            "suggestion": "Check variable names. Remember Python is case-sensitive (e.g., 'w0' vs 'W0')."
        })

    except ZeroDivisionError:
        # Occurs if the formula divides by zero at this specific z-position
        report.update({
            "status": "ERROR",
            "error_type": "Mathematical Error",
            "message": "Division by zero encountered during evaluation.",
            "suggestion": "Add a small epsilon to the denominator, e.g., (x + ESP_L)."
        })

    except IndexError:
        # Occurs if d(i,j) refers to a vertex that doesn't exist
        report.update({
            "status": "ERROR",
            "error_type": "Geometry Index Error",
            "message": "Vertex index out of range in d(i,j) function.",
            "suggestion": "Ensure polygon indices are correct and start from 1."
        })

    except Exception as e:
        # Catch-all for any other unforeseen execution errors
        report.update({
            "status": "ERROR",
            "error_type": "Execution Error",
            "message": str(e),
            "suggestion": "Check the formula syntax and any external data sources."
        })

    # --- BLOCK 5: IMMEDIATE OUTPUT ---
    # Call the tabular printer before returning values
    final_value = result if report["status"] != "ERROR" else 0.0
    if print:
        print_evaluation_report(final_value, report)
    
    return float(final_value), report



from datetime import datetime

def print_evaluation_report(value: float, report: dict):
    """
    Prints a professional, minimalist structured report with Timestamp.
    Designed for maximum visual impact and traceability.
    """
    # 1. Icons and Styling
    icons = {"SUCCESS": "🟢", "WARNING": "🟡", "ERROR": "🔴"}
    icon = icons.get(report["status"], "⚪")
    bw = 72  # Reference width for horizontal lines
    
    # 2. Helper for clean line printing
    def print_line(label, content):
        print(f"  {label:<12} {content}")

    # 3. Header
    print("\n" + "═" * bw)
    header_text = f"{icon}  CSF WEIGHT LAW INSPECTOR  |  {report['status']}"
    print(" " * ((bw - len(header_text)) // 2) + header_text)
    print("═" * bw)

    # 4. Input Section
    formula_display = report['formula'] if len(report['formula']) < 60 else report['formula'][:57] + "..."
    print_line("FORMULA:", formula_display)
    print_line("POSITION Z:", f"{report['z_pos']:.4f}  (ref. coordinate)")
    print_line("POSITION t:", f"{report['t_pos']:.4f}  (ref. normalized)")
    # 5. Results Section (Separator)
    print("-" * bw)
    if report["status"] != "ERROR":
        w_str = f"{value:g}" if abs(value) < 1e5 else f"{value:.4e}"
        print_line("RESULT W:", f"➤ {w_str}")
    else:
        print_line("RESULT W:", "❌ [EVALUATION FAILED]")

    # 6. Contextual Error/Warning Section
    if report["status"] != "SUCCESS":
        print("-" * bw)
        print_line("CATEGORY:", report.get("error_type", "Unknown"))
        print_line("DETAIL:", report.get("message", "N/A"))
        print_line("ADVICE:", report.get("suggestion", "Check input parameters."))

    # 7. Footer with Timestamp
    print("-" * bw)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Aligned to the right
    timestamp_str = f"Validated on: {now}"
    print(" " * (bw - len(timestamp_str)) + timestamp_str)
    print("═" * bw + "\n")



def evaluate_weight_formula( formula: str, p0: Polygon, p1: Polygon,  z0: float, z1: float, zt: float) -> float:
    """
    Wrapper function intended for use within 'eval()' contexts.
    It bridges the string evaluation to the structural lookup logic.

    Evaluates a string-based mathematical formula to determine the polygon weight at a 
            
    Args:
        formula (str): The Python expression to evaluate.
        p0 (Polygon): The polygon definition at the start section (z=0).
        p1 (Polygon): The polygon definition at the end section (z=L).
        zt (float): real relative or normalized values
        normalize: how to interpred zt
        
    Returns:
        float: The calculated weight (Elastic Modulus).
        
    Raises:
        Exception: Propagates any error encountered during evaluation.
    """
    # 2. Generate a temporary for the 'd(i,j)' helper.
    # This allows the formula to access distances at the current evaluation point.
    #   
    # z is absolute
    z = zt  
    # z must be absolute for interpolationg the poligons sections
    l_total=z1-z0
    current_verts = tuple(
        v0.lerp(v1, z,l_total) for v0, v1 in zip(p0.vertices, p1.vertices)
    )
    p_z = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)
   
    t=(zt-z0)/(z1-z0)
    #print(f"DEBUG z0 {z0} z1 {z1} zt {zt} t{t}")
    # 3. Define the external file lookup helper
    z=zt-z0
    def E_lookup(filename: str) -> float:
        # in this case z is abosolute
        # we need to go in relative z
        return lookup_homogenized_elastic_modulus(filename, z)
    
    def T_lookup(filename: str) -> float:
        # only for T_lookup zt is normalized
        return lookup_homogenized_elastic_modulus(filename, t)   
        
    # 4. Define local distance helpers for the context
    # These are used in the formula as d(i,j), d0(i,j), d1(i,j)
    d  = lambda i, j: get_points_distance(p_z, i, j)
    di = lambda i, j: get_points_distance(p0, i, j)
    de = lambda i, j: get_points_distance(p1, i, j)

    # 5. Build the evaluation context (Environment)
    #t = z / l_total if abs(l_total) > EPS_L else 0.0
    context = {
        "w0": p0.weight,        # Start weight
        "w1": p1.weight,        # End weight
        "z": z,                 # Alias for z-axis consistency
        "t": t,    
        "L": l_total,           # Physical length
        "math": math,           # Python math library
        "np": np,               # NumPy for advanced math
        "d": d,                 # Current distance function
        "d0": di,               # Start distance function
        "d1": de,               # End distance function
        "E_lookup": E_lookup,    # File-based data lookup
        "T_lookup": T_lookup    # File-based data lookup
    }

    # 6. Execute evaluation in a clean sandbox
    # We disable __builtins__ for safety to ensure only provided tools are used.

    return float(eval(formula, {"__builtins__": {}}, context))


'''
def t_lookup(filename: str, t: float) -> float:
    """
    normalised
    Wrapper function intended for use within 'eval()' contexts.
    It bridges the string evaluation to the structural lookup logic.
    """
    z=t # to be implemented
    return lookup_homogenized_elastic_modulus(filename, z)
''' 


def evaluate_weight_formula_zrelative( formula: str, p0: Polygon, p1: Polygon, z0: float, z1: float, z: float) -> float:
        """
        Evaluates a string-based mathematical formula to determine the polygon weight at a 
                
        Args:
            formula (str): The Python expression to evaluate.
            p0 (Polygon): The polygon definition at the start section (z=0).
            p1 (Polygon): The polygon definition at the end section (z=L).
            z (float): real relative z
            
        Returns:
            float: The calculated weight (Elastic Modulus).
            
        Raises:
            Exception: Propagates any error encountered during evaluation.
        """

        #evaluate_weight_formula( formula, p0, p1, l_total, z)
        '''
        # 2. Generate a temporary for the 'd(i,j)' helper.
        # This allows the formula to access distances at the current evaluation point.
        #
      
        current_verts = tuple(
            v0.lerp(v1, z,l_total) for v0, v1 in zip(p0.vertices, p1.vertices)
        )
        p_z = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)
        #print(f"DEBUG p_z {p_z}")
        # 3. Define the external file lookup helper
        def E_lookup(filename: str) -> float:
            return lookup_homogenized_elastic_modulus(filename, z)
        def T_lookup(filename: str) -> float:
            t=z
            return lookup_homogenized_elastic_modulus(filename, t)       
        # 4. Define local distance helpers for the context
        # These are used in the formula as d(i,j), d0(i,j), d1(i,j)
        d  = lambda i, j: get_points_distance(p_z, i, j)
        di = lambda i, j: get_points_distance(p0, i, j)
        de = lambda i, j: get_points_distance(p1, i, j)

        # 5. Build the evaluation context (Environment)
        #t = z / l_total if abs(l_total) > EPS_L else 0.0
        context = {
            "w0": p0.weight,        # Start weight
            "w1": p1.weight,        # End weight
            "z": z,                 # Alias for z-axis consistency
            #"t": t,    
            "L": l_total,           # Physical length
            "math": math,           # Python math library
            "np": np,               # NumPy for advanced math
            "d": d,                 # Current distance function
            "d0": di,               # Start distance function
            "d1": de,               # End distance function
            "E_lookup": E_lookup,    # File-based data lookup
            "T_lookup": T_lookup    # File-based data lookup
        }

        '''
        zabsolute = z0+z
        return evaluate_weight_formula( formula, p0, p1, z0,z1, zabsolute)



def section_print_analysis(full_analysis, fmt=".8f"):
    """
    Prints the structural analysis report for a cross-section.
    
    Args:
        full_analysis (dict): Dictionary containing the calculated properties.
        fmt (str): Optional Python format string for numerical output. 
                   Defaults to ".8f" (fixed-point with 8 decimals). 
          
                   Can be set to ".4e" for scientific notation or others.
    """

    def fmt_val_or_pair(x: Union[float, Tuple[float, float]], fmt: str) -> str:
        """
        Format either:
        - a single float -> formatted with `fmt`
        - a pair (v, t)  -> f"{v_fmt} t={t_fmt}" using the same `fmt`
        """
        # Case 1: single float
        if isinstance(x, (int, float)):
            return format(float(x), fmt)

        # Case 2: tuple of 2 floats
        if isinstance(x, tuple) and len(x) == 2:
            v, t = x
            return f"{format(float(v), fmt)} t={format(float(t), fmt)}"

        raise TypeError("x must be a float/int or a tuple of 2 floats")    
    span = 130
    print("\n" + "="*span)
    print("FULL MODEL ANALYSIS REPORT - SECTION EVALUATION")
    print("#  Name                              Key")
    print("="*span)
    
    # Using the 'fmt' parameter inside f-strings for all numerical values
    print(f"1) Area (A):                          A                     {full_analysis['A']:{fmt}}     # Total Homogenized area")
    print(f"2) Centroid Cx:                       Cx                    {full_analysis['Cx']:{fmt}}     # Horizontal geometric centroid (X-axis locus)")
    print(f"3) Centroid Cy:                       Cy                    {full_analysis['Cy']:{fmt}}     # Vertical geometric centroid (Y-axis locus)")
    print(f"4) Inertia Ix:                        Ix                    {full_analysis['Ix']:{fmt}}     # Second moment of area about the centroidal X-axis")
    print(f"5) Inertia Iy:                        Iy                    {full_analysis['Iy']:{fmt}}     # Second moment of area about the centroidal Y-axis")
    print(f"6) Inertia Ixy:                       Ixy                   {full_analysis['Ixy']:{fmt}}     # Product of inertia (indicates axis symmetry)")
    print(f"7) Polar Moment (J):                  J                     {full_analysis['J']:{fmt}}     # Polar second moment of area (sum of Ix and Iy)")
    print(f"8) Principal Inertia I1:              I1                    {full_analysis['I1']:{fmt}}     # Major principal second moment of area")
    print(f"9) Principal Inertia I2:              I2                    {full_analysis['I2']:{fmt}}     # Minor principal second moment of area")
    print(f"10) Radius of Gyration rx:            rx                    {full_analysis['rx']:{fmt}}     # Radii of gyration relative to the X-axis")
    print(f"11) Radius of Gyration ry:            ry                    {full_analysis['ry']:{fmt}}     # Radii of gyration relative to the Y-axis")
    print(f"12) Elastic Modulus Wx:               Wx                    {full_analysis['Wx']:{fmt}}     # Elastic section modulus (flexural strength about X)")
    print(f"13) Elastic Modulus Wy:               Wy                    {full_analysis['Wy']:{fmt}}     # Elastic section modulus (flexural strength about Y)")
    print(f"14) Torsional Rigidity K:             K_torsion             {full_analysis['K_torsion']:{fmt}}     # Semi-empirical torsional stiffness approximation")
    print(f"15) First_moment:                     Q_na                  {full_analysis['Q_na']:{fmt}}     # First moment of area at NA (governs shear capacity)" )
    print(f"16) Torsional const K:                J_sv                  {full_analysis['J_sv']:{fmt}}     # alpha = {full_analysis['J_sv_alpha']:{fmt}} Effective St. Venant torsional constant (J)")
    print(f"17) Torsional const K cell            J_sv_cell             {fmt_val_or_pair(full_analysis['J_sv_cell'],fmt)}   # Saint-Venant torsional constant for closed thin-walled by applying  Bredt–Batho formula")    
    print(f"18) Torsional const K wall            J_sv_wall             {fmt_val_or_pair(full_analysis['J_sv_wall'],fmt)}   # computes the Saint-Venant torsional constant for open thin-walled walls")
    print(f"19) Torsional const K roark:          J_s_vroark            {full_analysis['J_s_vroark']:{fmt}}     # Refined J using Roark-Young thickness correction")
    print(f"20) Torsional const K roark fidelity: J_s_vroark_fidelity   {full_analysis['J_s_vroark_fidelity']:{fmt}}     # Reliability index based on aspect-ratio (1.0 = Thin-walled, 0.0 = Stout")
    
    print("="*span)
    

def section_full_analysis_keys() -> List[str]:
    """
    Returns the ordered list of keys generated by the full analysis.
    Useful for mapping, CSV headers, or selective data extraction.
    """
    return [
        'A',
        'Cx',
        'Cy',
        'Ix',
        'Iy',
        'Ixy',
        'J',
        'I1',
        'I2',
        'rx',
        'ry',
        'Wx',
        'Wy',
        'K_torsion'
        ,'Q_na'
        ,'J_sv'
        ,'J_sv_wall'
        ,'J_sv_cell'
        ,'J_s_vroark'
        ,'J_s_vroark_fidelity'
    ]

def write_opensees_geometry(
    field,
    n_points: int,
    E_ref: float = 2.1e11,
    nu: float = 0.30,
    filename: str = "geometry.tcl",
):
    """
    Write a CSF-style OpenSees geometry file **as DATA** (to be parsed line-by-line),
    not as a Tcl script to be sourced.

    --------------------------------------------------------------------------------
    FILE CONTRACT (DATA, NOT Tcl)
    --------------------------------------------------------------------------------
    1) Exact stations (critical for reproducibility)
       We write the exact longitudinal stations used by CSF:
           # CSF_Z_STATIONS: z0 z1 ... zN-1
       A downstream builder must use these stations (no re-generation).

    2) Section record format (data record that *resembles* OpenSees)
       We write one record per station:

           section Elastic <tag> <E_ref> <A*> <Iz*> <Iy*> <G_ref> <J_tors> <Cx> <Cy>

       IMPORTANT:
       - This is a DATA record. OpenSees Tcl would NOT accept the trailing <Cx> <Cy>.
       - Cx,Cy are appended for CSF parsers/builders (centroid offsets in section plane).
       - A*, Iz*, Iy* are assumed already "CSF-weighted / modular" properties
         (i.e., heterogeneity/holes already reflected by CSF analysis).

    3) Torsion export without tying the file to a single CSF torsion model
       CSF may provide multiple torsion candidates (e.g., wall/cell/legacy).
       This writer exports a single neutral value J_tors (to feed OpenSees "J"):
         - Prefer J_sv_wall if > 0
         - else prefer J_sv_cell if > 0
         - else use legacy "J" if > 0
         - else fail-fast (recommended; avoids silent torsion defaults)

       Note: In OpenSees, the "J" field in section Elastic is the torsion constant.
             We export our selected torsion constant into that "J" slot.

    4) Reference shear modulus
       G_ref is computed as isotropic:
           G_ref = E_ref / (2*(1+nu))

    --------------------------------------------------------------------------------
    OUTPUT CONTENTS
    --------------------------------------------------------------------------------
    - Header comments
    - # CSF_Z_STATIONS: exact z-coordinates
    - Optional informational nodes (best-fit line through centroid offsets)
    - geomTransf Linear 1 1 0 0 (simple default)
    - One section record per station (as described above)

    --------------------------------------------------------------------------------
    REQUIREMENTS
    --------------------------------------------------------------------------------
    - numpy must be available
    - section_full_analysis(sec, ...) must return at least:
        "A", "Ix", "Iy", "Cx", "Cy"
      and (for torsion export) at least one of:
        "J_sv_wall", "J_sv_cell", "J"
    """

    import numpy as np

    # -------------------------------------------------------------------------
    # Helper: robust positive check for torsion fields
    # Convention: J_* == 0 means "not provided / not applicable"
    # -------------------------------------------------------------------------
    def _is_pos(v: object, eps: float = 0.0) -> bool:
        try:
            x = float(v)
        except Exception:
            return False
        return np.isfinite(x) and (x > eps)

    # -------------------------------------------------------------------------
    # 0) Member endpoints (same z convention used by the CSF field)
    # -------------------------------------------------------------------------
    z0 = float(field.s0.z)
    z1 = float(field.s1.z)

    # -------------------------------------------------------------------------
    # 1) Exact sampling stations provided by CSF.
    #    We do not assume formulas here; we trust the field.
    # -------------------------------------------------------------------------
    z_coords = field.get_opensees_integration_points(n_points)
    z_coords = [float(z) for z in z_coords]

    # -------------------------------------------------------------------------
    # 2) Run section analysis at each station
    # -------------------------------------------------------------------------
    results = []
    cx_list = []
    cy_list = []

    for z in z_coords:
        sec = field.section(z)

        # NOTE:
        # If your CSF legacy torsion uses alpha=1 internally, that should be handled
        # inside section_full_analysis / torsion routines.
        # The exporter should not encode that assumption here unless it is part of
        # the section analysis contract.
        res = section_full_analysis(sec)

        # Minimal required keys
        for k in ("A", "Ix", "Iy", "Cx", "Cy"):
            if k not in res:
                raise KeyError(f"section_full_analysis() missing required key '{k}' at z={z}")

        results.append(res)
        cx_list.append(float(res["Cx"]))
        cy_list.append(float(res["Cy"]))

    # -------------------------------------------------------------------------
    # 3) Informational-only: best-fit straight line through centroid offsets
    #    (kept only for legacy scripts/human readability)
    # -------------------------------------------------------------------------
    m_y, q_y = np.polyfit(z_coords, cy_list, 1)
    m_x, q_x = np.polyfit(z_coords, cx_list, 1)

    # -------------------------------------------------------------------------
    # 4) Reference shear modulus
    # -------------------------------------------------------------------------
    G_ref = float(E_ref) / (2.0 * (1.0 + float(nu)))

    # -------------------------------------------------------------------------
    # 5) Write file (DATA)
    # -------------------------------------------------------------------------
    try:
        with open(filename, "w", encoding="utf-8") as f:
            # ---- Header (comments only) ----
            f.write("# OpenSees Geometry DATA File - Generated by CSF\n")
            f.write(f"# Beam Span: {z1 - z0:.6f} (units follow your model)\n")
            f.write(f"# Stations: {len(z_coords)}\n")
            f.write("# NOTE: This file is meant to be PARSED AS DATA (do NOT source it as Tcl).\n")
            f.write("# NOTE: Section lines append 'Cx Cy' as CSF-only fields (not OpenSees syntax).\n")
            f.write("#\n")
            f.write("# CSF_EXPORT_MODE: E=E_ref ; A/I/J are station-wise CSF results (already weighted)\n")
            f.write("# CSF_TORSION_SELECTION: J_eff = max(J_sv_cell, J_sv_wall) if any >0 else J_sv if >0 else ERROR")

            # ---- Exact z stations ----
            f.write("\n\n# CSF_Z_STATIONS: " + " ".join(f"{z:.12g}" for z in z_coords) + "\n\n")

            # ---- Informational nodes (optional) ----
            f.write("# Informational nodes (best-fit line through centroid offsets)\n")
            f.write(f"node 1 {m_x * z0 + q_x:.12g} {m_y * z0 + q_y:.12g} {z0:.12g}\n")
            f.write(f"node 2 {m_x * z1 + q_x:.12g} {m_y * z1 + q_y:.12g} {z1:.12g}\n\n")

            # ---- Default transformation (builder may override) ----
            f.write("geomTransf Linear 1 1 0 0\n\n")

            # ---- Section records ----
            # Record format (DATA):
            #   section Elastic tag E_ref A Iz Iy G_ref J_tors Cx Cy
            #
            # Mapping:
            #   Iz := Ix from CSF (if your axes are aligned); otherwise swap upstream.
            #   Iy := Iy from CSF
            #
            # IMPORTANT: ensure your downstream builder interprets Ix/Iy consistently.
            for i, res in enumerate(results):
                tag = i + 1


                # -------------------------------------------------------------------------
                # Select torsion constant to export into OpenSees "J"
                #
                # POLICY:
                #   1) If any thin-walled candidate is available:
                #        J_eff = max(J_sv_cell, J_sv_wall)
                #      and set torsion_method to the SELECTED KEY:
                #        "J_sv_cell" or "J_sv_wall"
                #
                #   2) If no thin-walled candidate is available:
                #        fallback to J_sv
                #      and set torsion_method = "J_sv"
                #
                #   3) If nothing is available: fail-fast.
                # -------------------------------------------------------------------------
                cell_ok = _is_pos(res.get("J_sv_cell"), 0.0)
                wall_ok = _is_pos(res.get("J_sv_wall"), 0.0)

                if cell_ok or wall_ok:
                    J_cell = float(res["J_sv_cell"]) if cell_ok else 0.0
                    J_wall = float(res["J_sv_wall"]) if wall_ok else 0.0

                    if J_cell >= J_wall:
                        J_tors = J_cell
                        torsion_method = "J_sv_cell"
                    else:
                        J_tors = J_wall
                        torsion_method = "J_sv_wall"

                elif _is_pos(res.get("J_sv"), 0.0):
                    J_tors = float(res["J_sv"])
                    torsion_method = "J_sv"

                else:
                    raise KeyError(
                        f"No torsion value available at station {tag} (z={z_coords[i]}). "
                        "Expected positive J_sv_cell, J_sv_wall, or J_sv."
                    )



                # Write section data record
                f.write(
                    "section Elastic {tag} {E:.6e} {A:.6e} {Iz:.6e} {Iy:.6e} {G:.6e} {J:.6e} "
                    "{Cx:.6e} {Cy:.6e}  # torsion={tm}\n".format(
                        tag=tag,
                        E=float(E_ref),
                        A=float(res["A"]),
                        Iz=float(res["Ix"]),
                        Iy=float(res["Iy"]),
                        G=float(G_ref),
                        J=float(J_tors),
                        Cx=float(res["Cx"]),
                        Cy=float(res["Cy"]),
                        tm=torsion_method,
                    )
                )

        print(f"[SUCCESS] Wrote CSF geometry data to: {filename}")
        print(f"[INFO] Stations: {len(z_coords)} | Span: {z1 - z0:.6f}")

    except OSError as e:
        print(f"[ERROR] Could not write '{filename}': {e}")
        raise



def write_opensees_geometry2(field, n_points, E_ref=2.1e11, nu=0.30, filename="geometry.tcl"):
    """
    Generate a CSF-style OpenSees "geometry.tcl" file that is meant to be READ AS DATA
    (i.e., parsed line-by-line), not necessarily sourced as a Tcl script.

    -------------------------------------------------------------------------------
    KEY DESIGN GOALS / CONTRACT (why the file is written this way)
    -------------------------------------------------------------------------------
    1) No ambiguity in station placement:
       - We explicitly write the exact CSF sampling stations as:
            # CSF_Z_STATIONS: z0 z1 z2 ... zN-1
         so any downstream builder can place stations exactly at those coordinates
         without re-generating Lobatto points or assuming uniform spacing.

    2) No "double counting" of stiffness:
       - The file writes CONSTANT reference moduli (E_ref and G_ref).
       - The section properties coming from `section_full_analysis(sec)` are assumed
         ALREADY "CSF-weighted / modular" (e.g., accounting for holes, materials,
         and CSF weights).
       - Therefore OpenSees stiffness products become:
            EA  = E_ref * A*
            EIx = E_ref * Ix*
            EIy = E_ref * Iy*
         which matches Σ(E_i * property_i) when CSF weights are defined consistently
         (e.g., weights normalized by E_ref).

       IMPORTANT:
       - This only makes sense if your CSF exporter intentionally encodes material
         heterogeneity into the section properties (A*, Ix*, Iy*, ...).
       - If instead geometry.tcl already contains physical E(z), G(z), then your
         builder should use MATERIAL_INPUT_MODE="from_file" and properties should
         be unweighted. That is a different contract.

    3) Centroid tracking (tilt field):
       - We export centroid offsets (Cx, Cy) at every station (if available).
       - A downstream builder can reconstruct a centroid axis via rigid links.
       - If Cx/Cy vary along the member, that implies geometric "tilt" / eccentricity
         variation along z.

    -------------------------------------------------------------------------------
    WHAT THIS FUNCTION WRITES
    -------------------------------------------------------------------------------
    - Header comments (beam length, station count, export mode)
    - # CSF_Z_STATIONS: exact station z coordinates (critical)
    - Two "node" lines (legacy/template):
         node 1 x(z0) y(z0) z0
         node 2 x(z1) y(z1) z1
      NOTE: these are derived by linear regression of Cx(z), Cy(z). Many builders
      ignore these and build a clean reference axis instead.
    - geomTransf Linear 1 1 0 0 (simple default orientation)
    - One 'section Elastic' per station:
         section Elastic tag E_ref A* Ix* Iy* G_ref J_placeholder Cx Cy
    - A "TEMPLATE ONLY" hint for humans (not used by robust parsers/builders)

    The goal is that changing ONLY `geometry.tcl` (stations + sections) is sufficient
    to change the member description in downstream OpenSees / OpenSeesPy builders.
    """

    # ---------------------------------------------------------------------------
    # 0) Member endpoints (in the same coordinate system used by CSF field)
    # ---------------------------------------------------------------------------
    z0 = field.s0.z
    z1 = field.s1.z

    # ---------------------------------------------------------------------------
    # 1) The *actual* integration/sampling stations used by CSF.
    #    Typically these are Gauss–Lobatto stations including the endpoints,
    #    but we do NOT assume any formula here: we ask the field for them.
    #
    #    These z coordinates are written verbatim to "# CSF_Z_STATIONS:" so
    #    downstream readers can be exact.
    # ---------------------------------------------------------------------------
    z_coords = field.get_opensees_integration_points(n_points)

    # Lists used to store centroid offsets and section properties at each station
    cx_list = []
    cy_list = []
    section_results = []

    # ---------------------------------------------------------------------------
    # 2) Cross-section analysis at each station.
    #
    #    `section_full_analysis(sec,alpha)` is assumed to return *already CSF-weighted*
    #    properties (A, Ix, Iy, etc.), plus centroid offsets (Cx, Cy).
    #
    #    Expected keys (minimum):
    #       - "A", "Ix", "Iy", "Cx", "Cy"
    #    Optional keys might exist (torsion, shear areas, etc.); this writer
    #    currently exports a placeholder J (see below).
    # ---------------------------------------------------------------------------
    for z in z_coords:
        # Construct the cross-section object at coordinate z
        sec = field.section(z)


        # Perform section analysis (properties assumed to already incorporate CSF weights)
        res = section_full_analysis(sec,alpha=0)#alpha not used

        # Store centroid offsets for later regression and for writing into the file
        cx_list.append(res["Cx"])
        cy_list.append(res["Cy"])

        # Store the full dictionary so we can write A/Ix/Iy/etc. later
        section_results.append(res)

    # ---------------------------------------------------------------------------
    # 3) Linear regression for legacy/template end nodes.
    #
    #    Why do we do this?
    #      - Some legacy workflows expect "node 1" and "node 2" to exist.
    #      - We approximate a straight line passing through centroid offsets.
    #
    #    What is it used for?
    #      - Only to write the two 'node' lines below.
    #
    #    What is it NOT used for?
    #      - A robust OpenSees builder should rely on CSF_Z_STATIONS + (Cx,Cy)
    #        per station and build its own reference/centroid axis.
    # ---------------------------------------------------------------------------
    m_y, q_y = np.polyfit(z_coords, cy_list, 1)
    m_x, q_x = np.polyfit(z_coords, cx_list, 1)

    # ---------------------------------------------------------------------------
    # 4) Reference shear modulus for an isotropic material:
    #
    #       G_ref = E_ref / (2*(1+nu))
    #
    #    If you had a custom legacy formula (e.g., E_ref/2.6), you can swap it,
    #    but do so knowingly because it directly changes shear stiffness (GA, GJ).
    # ---------------------------------------------------------------------------
    G_ref = E_ref / (2.0 * (1.0 + nu))

    # ---------------------------------------------------------------------------
    # 5) Torsional constant placeholder.
    #
    #    Many CSF pipelines either:
    #      (a) do not export torsion, or
    #      (b) export a station-wise torsion constant J(z).
    #
    #    If you have station-wise torsion, you should write it per station.
    #    For now we keep a constant placeholder to preserve old behavior.
    # ---------------------------------------------------------------------------
    st_venant_j = 2.6247e-06

    # ---------------------------------------------------------------------------
    # 6) Write the file.
    #
    #    NOTE: This file is intended to be PARSED as data.
    #    Downstream scripts should not assume this file is safe to 'source'.
    # ---------------------------------------------------------------------------
    try:
        with open(filename, "w", encoding="utf-8") as f:
            # ---- Header / metadata (comments only) ----
            f.write("# OpenSees Geometry File - Generated by CSF Library\n")
            f.write(f"# Beam Length: {z1 - z0:.3f} m | Int. Points: {n_points}\n")
            f.write("# CSF_EXPORT_MODE: E=E_ref ; A/I are CSF-weighted (modular) properties\n\n")

            # -------------------------------------------------------------------
            # CRITICAL: explicit station coordinates used by CSF.
            #
            # This is the single most important line for reproducibility:
            # it prevents any re-computation of points (Lobatto/uniform/etc.)
            # and makes downstream verification exact.
            # -------------------------------------------------------------------
            f.write("# CSF_Z_STATIONS: " + " ".join(f"{float(z):.6f}" for z in z_coords) + "\n\n")

            # -------------------------------------------------------------------
            # Legacy/template nodes:
            #
            # These nodes are NOT required by robust builders.
            # They are kept for human readability or old scripts that expect them.
            #
            # x(z) = m_x*z + q_x, y(z) = m_y*z + q_y are just the best-fit line
            # through the centroid offsets. This does NOT preserve a curved axis.
            # -------------------------------------------------------------------
            f.write(f"node 1 {m_x * z0 + q_x:.6f} {m_y * z0 + q_y:.6f} {z0:.6f}\n")
            f.write(f"node 2 {m_x * z1 + q_x:.6f} {m_y * z1 + q_y:.6f} {z1:.6f}\n\n")

            # -------------------------------------------------------------------
            # Transformation:
            #
            # We write a simple default orientation for the local x–z plane.
            # Downstream tools may override / ignore this if they compute their
            # own basis. Still, writing it keeps the file self-describing.
            # -------------------------------------------------------------------
            f.write("geomTransf Linear 1 1 0 0\n\n")

            # -------------------------------------------------------------------
            # Sections:
            #
            # One Elastic section per station.
            #
            # Format used by downstream parsers:
            #   section Elastic tag E_ref A* Ix* Iy* G_ref J [Cx Cy]
            #
            # - tag:     station index + 1 (stable ordering)
            # - E_ref:   constant reference modulus (may be overridden later)
            # - A*:      CSF-weighted area at station
            # - Ix*,Iy*: CSF-weighted bending inertias at station
            # - G_ref:   constant reference shear modulus
            # - J:       torsion placeholder (constant for now)
            # - Cx,Cy:   centroid offsets at station (used for "tilt"/eccentricity)
            # -------------------------------------------------------------------
            for i, res in enumerate(section_results):
                tag = i + 1

                f.write(
                    f"section Elastic {tag} {E_ref:.6e} {res['A']:.6e} "
                    f"{res['Ix']:.6e} {res['Iy']:.6e} {G_ref:.6e} {st_venant_j:.6e} "
                    f"{res['Cx']:.6f} {res['Cy']:.6f}\n"
                )

            # -------------------------------------------------------------------
            # TEMPLATE ONLY (commented out):
            #
            # This is just a human hint. A robust builder should define its own
            # beamIntegration/element blocks based on CSF_Z_STATIONS and the sections.
            # -------------------------------------------------------------------
            tag_str = " ".join(map(str, range(1, n_points + 1)))
            f.write("\n# TEMPLATE ONLY (the Python builder defines the actual integration)\n")
            f.write(f"# beamIntegration Lobatto 1 {tag_str} 1\n")
            f.write("# element forceBeamColumn 1 1 2 1 1\n")

        print(f"[SUCCESS] {filename} created correctly (CSF modular properties + centroid tracking).")
        print(f"[INFO] Beam span: {z1 - z0:.3f} (units follow your model convention).")

    except OSError as e:
        print(f"[ERROR] Could not write geometry file '{filename}': {e}")
        raise


def lookup_homogenized_elastic_modulus(filename: str, zt: float) -> float:
    """
    Retrieves the elastic modulus (E) for a given longitudinal coordinate (z) 
    from an external lookup file.
    
    ALGORITHM STRATEGY:
    1. Parsing: The function reads a text file where each line contains a pair of 
       values: [coordinate_z, modulus_E].
    2. Exact Match: If the requested 'z' matches a coordinate in the file, 
       the corresponding E is returned immediately.
    3. Boundary Handling: If 'z' is outside the range defined in the file, 
       it performs flat extrapolation (returns the nearest boundary value).
    4. Linear Interpolation (LERP): If 'z' falls between two points (z_i, E_i) 
       and (z_j, E_j), it calculates E via:
       E = E_i + (E_j - E_i) * (z - z_i) / (z_j - z_i)

    FILE FORMAT ASSUMPTIONS:
    - The file should be a space, tab, or comma-separated text file.
    - Column 0: Z-coordinate (must be in increasing order for correct interpolation).
    - Column 1: Elastic Modulus value.

    Args:
        filename (str): Path to the lookup data file.
        zt (float): The current coordinate where the property is needed. can be both normalised or not

    Returns:
        float: The interpolated or exact Elastic Modulus.
    """
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Lookup file not found: {filename}")

    # --- STEP 1: LOAD DATA ---
    # We use a list of tuples to store the [z, E] pairs.
    # Data is expected to be numeric.
    data = []
    with open(filename, 'r') as f:
        for line in f:
            # Skip empty lines or comments starting with '#'
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # Support for common delimiters (comma, tab, space)
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:
                    z_val = float(parts[0])
                    e_val = float(parts[1])
                    data.append((z_val, e_val))
            except ValueError:
                # Skip lines that do not contain valid numbers
                continue

    if not data:
        raise ValueError(f"No valid data found in lookup file: {filename}")

    # Ensure data is sorted by Z-coordinate for the interpolation logic
    data.sort(key=lambda x: x[0])

    # --- STEP 2: BOUNDARY CHECKS (Extrapolation) ---
    # If the requested z is below the minimum z in the file
    if zt <= data[0][0]:
        return data[0][1]
    # If the requested z is above the maximum z in the file
    if zt >= data[-1][0]:
        return data[-1][1]

    # --- STEP 3: SEARCH AND INTERPOLATION ---
    # Iterate through the pairs to find the interval [z_i, z_i+1] containing z.
    for i in range(len(data) - 1):
        z0, e0 = data[i]
        z1, e1 = data[i+1]
        
        # Exact match check
        if abs(zt - z0) < EPS_L:
            
            return e0
           # Exact match check
        if abs(zt - z1) < EPS_L:
            
            return e1

        # Check if z is within the current segment
        if z0 < zt < z1:
            # Linear Interpolation Formula:
            # weight = (target - start) / (end - start)
            t = (zt - z0) / (z1 - z0)
            # Result = start_val + weight * (end_val - start_val)
            return e0 + t * (e1 - e0)
    # end for
    # Fallback for the very last point
    return data[-1][1]
######################################################################################################################################
"""


CSF-consistent rewrite of:

    def compute_saint_venant_Jv2(poly_input, verbose=False) -> Tuple[float, float]

Design goals
------------

Representation-invariant for sections:
   - The Roark equivalent-rectangle mapping is non-linear, so computing J per polygon
     and summing depends on how the same domain is split into polygons.
   - Therefore, for a Section we first aggregate (A, centroid, Ix, Iy, Ixy) algebraically
     and apply the mapping ONCE.
Fidelity is also representation-invariant:
   - It is computed from the *equivalent rectangle* only (optionally via an external
     diagnostic), not by averaging per-piece fidelities.

Preconditions (expected upstream in CSF)
----------------------------------------
- Each polygon is a simple CCW loop with positive signed area.
- EPS_A and EPS_K are provided upstream (as globals or attached to objects).
"""

# -----------------------------------------------------------------------------
# Tolerance resolution (no hard-coded constants here)
# -----------------------------------------------------------------------------

def _resolve_eps_a(obj: Any) -> float:
    """Resolve EPS_A from globals(), obj, or obj.field; otherwise fail."""
    if "EPS_A" in globals():
        return float(globals()["EPS_A"])
    if hasattr(obj, "EPS_A"):
        return float(getattr(obj, "EPS_A"))
    fld = getattr(obj, "field", None)
    if fld is not None and hasattr(fld, "EPS_A"):
        return float(getattr(fld, "EPS_A"))
    raise ValueError("EPS_A not found. Define EPS_A upstream or attach it to the object.")


def _resolve_eps_k(obj: Any) -> float:
    """Resolve EPS_K from globals(), obj, or obj.field; otherwise fail."""
    if "EPS_K" in globals():
        return float(globals()["EPS_K"])
    if hasattr(obj, "EPS_K"):
        return float(getattr(obj, "EPS_K"))
    fld = getattr(obj, "field", None)
    if fld is not None and hasattr(fld, "EPS_K"):
        return float(getattr(fld, "EPS_K"))
    raise ValueError("EPS_K not found. Define EPS_K upstream or attach it to the object.")


# -----------------------------------------------------------------------------
# Signed polygon integrals (no abs())
# -----------------------------------------------------------------------------

def _poly_signed_area_centroid(pts: Any, eps_a: float) -> Tuple[float, float, float]:
    """
    Shoelace integration.

    Returns (A, Cx, Cy) with signed area A.
    Under CSF preconditions polygons are CCW so A > 0.
    """
    def _xy(p):
        if hasattr(p, "x") and hasattr(p, "y"):
            return float(p.x), float(p.y)
        return float(p[0]), float(p[1])    
    n = len(pts)
    if n < 3:
        raise ValueError("Polygon has < 3 vertices.")

    a2 = 0.0
    cx6 = 0.0
    cy6 = 0.0

    for i in range(n):
        v0 = pts[i]
        v1 = pts[(i + 1) % n]
        cross = v0.x * v1.y - v1.x * v0.y
        a2 += cross
        cx6 += (v0.x + v1.x) * cross
        cy6 += (v0.y + v1.y) * cross

        '''
        print(f"i={i:2d}: v0=({v0.x:8.6f}, {v0.y:8.6f}) v1=({v1.x:8.6f}, {v1.y:8.6f})")
        print(f"     cross={cross:10.6f}  a2={a2:10.6f}  cx6_contrib={(v0.x + v1.x)*cross:10.6f}")
        print(f"     cy6_contrib={(v0.y + v1.y)*cross:10.6f}  cx6_tot={cx6:10.6f}  cy6_tot={cy6:10.6f}")
        print()  # riga vuota
        '''



    A = 0.5 * a2
    if A <= eps_a:
        raise ValueError("Polygon area is non-positive or too small (expected CCW, non-degenerate).")

    Cx = cx6 / (3.0 * a2)
    Cy = cy6 / (3.0 * a2)
    return A, Cx, Cy


def _poly_centroidal_inertia(pts: Any, cx: float, cy: float) -> Tuple[float, float, float]:
    """
    Centroidal second moments via signed polygon integration.

    Returns (Ix, Iy, Ixy) about the polygon centroid.
    """
    n = len(pts)
    ix = 0.0
    iy = 0.0
    ixy = 0.0

    for i in range(n):
        x0 = pts[i].x - cx
        y0 = pts[i].y - cy
        x1 = pts[(i + 1) % n].x - cx
        y1 = pts[(i + 1) % n].y - cy
        cross = x0 * y1 - x1 * y0

        ix += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        iy += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        ixy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cross

    ix /= 12.0
    iy /= 12.0
    ixy /= 24.0
    return ix, iy, ixy


def _principal_inertias(ix: float, iy: float, ixy: float) -> Tuple[float, float]:
    """Principal inertias (eigenvalues) of the 2x2 centroidal inertia tensor."""
    tr = ix + iy
    diff = ix - iy
    rad = math.sqrt((0.5 * diff) * (0.5 * diff) + ixy * ixy)
    i1 = 0.5 * tr + rad
    i2 = 0.5 * tr - rad
    return i1, i2


# -----------------------------------------------------------------------------
# Roark equivalent-rectangle torsion proxy
# -----------------------------------------------------------------------------

def _roark_torsion_rect(a: float, b: float) -> float:
    """
    Roark-style torsion approximation for a solid rectangle; requires a >= b > 0:

        J ≈ (1/3 - 0.21*(b/a)*(1 - (b/a)^4/12)) * a * b^3
    """
    ratio = b / a
    factor = (1.0 / 3.0) - 0.21 * ratio * (1.0 - (ratio ** 4) / 12.0)
    return factor * a * (b ** 3)


def _equiv_rectangle_dims(A: float, i_min: float, eps_k: float) -> Tuple[float, float]:
    """
    Map (A, I_min) to equivalent rectangle dimensions (a >= b).

    Uses: I_min = (A * t^2) / 12  -> t = sqrt(12*I_min/A),  b = A/t
    """
    if A <= 0.0:
        raise ValueError("Effective area must be positive for the solid-rectangle mapping.")
    if i_min <= 0.0:
        raise ValueError("Minor principal inertia must be positive for the solid-rectangle mapping.")

    t = math.sqrt(12.0 * i_min / A)
    if t <= eps_k:
        raise ValueError("Equivalent thickness too small; torsion proxy ill-conditioned.")

    b_equiv = A / t
    if b_equiv >= t:
        a_dim = b_equiv
        b_dim = t
    else:
        a_dim = t
        b_dim = b_equiv
    return a_dim, b_dim


# -----------------------------------------------------------------------------
# Representation-invariant fidelity
# -----------------------------------------------------------------------------

class _TmpPt:
    __slots__ = ("x", "y")
    def __init__(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)

class _TmpPoly:
    __slots__ = ("vertices", "weight", "name")
    def __init__(self, vertices, name: str = "equiv_rect") -> None:
        self.vertices = vertices
        self.weight = 1.0
        self.name = name

def _equiv_rectangle_polygon(a: float, b: float) -> _TmpPoly:
    """Build a CCW rectangle centered at the origin with side lengths a (x) and b (y)."""
    hx = 0.5 * float(a)
    hy = 0.5 * float(b)
    verts = [_TmpPt(-hx, -hy), _TmpPt(hx, -hy), _TmpPt(hx, hy), _TmpPt(-hx, hy)]
    return _TmpPoly(verts)

def _fidelity_from_equiv_rectangle(a: float, b: float) -> float:
    """
    Fidelity index for the Roark proxy, invariant to polygon splitting.

    Policy:
    - If an external callable `evaluate_torsional_fidelity(obj)` exists, use it,
      but evaluate it on the equivalent rectangle (synthetic polygon).
    - Otherwise, return the rectangle aspect ratio b/a (with a >= b), which is a
      simple compactness indicator in (0, 1].

    No abs(), no sign normalization.
    """
    a = float(a)
    b = float(b)
    if a == 0.0:
        return float("nan")
    ratio = b / a

    diag_fn = globals().get("evaluate_torsional_fidelity", None)
    if callable(diag_fn):
        try:
            diag = diag_fn(_equiv_rectangle_polygon(a, b))
            if isinstance(diag, dict) and ("confidence_index" in diag):
                v = float(diag["confidence_index"])
                if math.isfinite(v):
                    return v
        except Exception:
            pass

    return ratio


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------



def compute_saint_venant_Jv2(poly_input: Any, verbose: bool = False) -> Tuple[float, float]:
    """
    Returns (J_total, fidelity).

    - Polygon input: compute centroidal inertias, map to equivalent rectangle, apply Roark.
    - Section input (has `.polygons`): aggregate (A, centroid, Ix, Iy, Ixy) first, then map ONCE.

    Weighting:
    - For polygons: J_i is multiplied by polygon.weight.
    - For sections: the aggregation uses A_eff = w_i*A_i and inertia_eff = w_i*(I_i + A_i*shift^2).
      This is algebraic and representation-invariant.
    """
    eps_a = _resolve_eps_a(poly_input)
    eps_k = _resolve_eps_k(poly_input)

    # -------------------------------------------------------------------------
    # 1) Section: aggregate keys then map once (representation-invariant)
    # -------------------------------------------------------------------------
    if hasattr(poly_input, "polygons"):
        polys = poly_input.polygons

        # First pass: effective area and centroid
        A_tot = 0.0
        Qx = 0.0
        Qy = 0.0

        cache = []  # (A_i, cx_i, cy_i, Ix_i, Iy_i, Ixy_i, w_i)

        for p in polys:
            pts = p.vertices() if callable(getattr(p, "vertices", None)) else getattr(p, "vertices", None)
            if pts is None:
                raise ValueError("Polygon has no vertices.")
            if not hasattr(p, "weight"):
                raise ValueError("Polygon has no weight.")
            w_i = float(getattr(p, "weight"))

            A_i, cx_i, cy_i = _poly_signed_area_centroid(pts, eps_a)
            Ix_i, Iy_i, Ixy_i = _poly_centroidal_inertia(pts, cx_i, cy_i)

            A_eff = w_i * A_i
            A_tot += A_eff
            Qx += A_eff * cx_i
            Qy += A_eff * cy_i
            cache.append((A_i, cx_i, cy_i, Ix_i, Iy_i, Ixy_i, w_i))

        if A_tot <= eps_a:
            print(f"WARNING:: Composite effective area is non-positive A_tot: {A_tot}; cannot compute solid-rectangle torsion proxy")
            return 0,0
            #raise ValueError(f"Composite effective area is non-positive A_tot: {A_tot}; cannot compute solid-rectangle torsion proxy.")

        cx_tot = Qx / A_tot
        cy_tot = Qy / A_tot

        # Second pass: centroidal inertias about composite centroid
        Ix = 0.0
        Iy = 0.0
        Ixy = 0.0

        for A_i, cx_i, cy_i, Ix_i, Iy_i, Ixy_i, w_i in cache:
            dx = cx_i - cx_tot
            dy = cy_i - cy_tot
            Ix += w_i * (Ix_i + A_i * (dy * dy))
            Iy += w_i * (Iy_i + A_i * (dx * dx))
            Ixy += w_i * (Ixy_i + A_i * (dx * dy))

        i1, i2 = _principal_inertias(Ix, Iy, Ixy)
        i_min = i2 if i2 <= i1 else i1

        a_dim, b_dim = _equiv_rectangle_dims(A_tot, i_min, eps_k)
        J_total = _roark_torsion_rect(a_dim, b_dim)
        fid = _fidelity_from_equiv_rectangle(a_dim, b_dim)

        if verbose and math.isfinite(fid) and (fid < 0.5):
            print(
                "[SECTION ANALYSIS] Global fidelity for '%s' is low (%.2f)." %
                (getattr(poly_input, "name", "unnamed"), fid)
            )

        return float(J_total), float(fid)

    # -------------------------------------------------------------------------
    # 2) Single polygon
    # -------------------------------------------------------------------------
    pts = poly_input.vertices() if callable(getattr(poly_input, "vertices", None)) else getattr(poly_input, "vertices", None)
    if pts is None:
        raise ValueError("Polygon has no vertices.")
    if len(pts) < 3:
        return 0.0, float("nan")
    if not hasattr(poly_input, "weight"):
        raise ValueError("Polygon has no weight.")
    w = float(getattr(poly_input, "weight"))

    A, cx, cy = _poly_signed_area_centroid(pts, eps_a)
    ix, iy, ixy = _poly_centroidal_inertia(pts, cx, cy)
    i1, i2 = _principal_inertias(ix, iy, ixy)
    i_min = i2 if i2 <= i1 else i1

    a_dim, b_dim = _equiv_rectangle_dims(A, i_min, eps_k)
    J_geom = _roark_torsion_rect(a_dim, b_dim)
    J_value = w * J_geom
    fid = _fidelity_from_equiv_rectangle(a_dim, b_dim)

    return float(J_value), float(fid)

######################################################################################################################################


def calculate_t_eq(points):
    """
    Calcola t_eq = 2*A/P per poligono thin-walled.
    points: list [[x1,y1], [x2,y2], ..., [xn,yn]] linea mediana.
    """
    points = np.array(points)
    # Area shoelace
    x, y = points[:,0], points[:,1]
    A = 0.5 * np.abs(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1)))
    # Perimetro
    diffs = np.diff(points, axis=0, append=points[0:1])
    P = np.sum(np.sqrt(np.sum(diffs**2, axis=1)))
    t_eq = 2 * A / P if P > 0 else 0
    return t_eq, A, P  # Ritorna anche A, P per debug


"""
CSF torsion (Saint-Venant) - CELL-based closed thin-walled variant
==================================================================

This file provides a *single* drop-in function:

    compute_saint_venant_J_cell(section)

It is designed to live in the same module where your CSF geometry and torsion
functions already exist (e.g., your `section_field.py`), because it expects
these symbols to be available:

Required symbols from your codebase
-----------------------------------
- compute_saint_venant_J(section)      : legacy fallback
- polygon_area_centroid(poly) -> (A_signed, (Cx, Cy))
- EPS_A, EPS_L                         : tolerances
- CSFError                             : exception type (subclass of ValueError)
- Section / Polygon data model:
    section.polygons iterable of Polygon-like objects, each with:
      - p.name (string)
      - p.weight (float)   (MUST exist; no silent defaults)
      - p.vertices iterable of points with .x and .y

User convention for CLOSED thin-walled cells
--------------------------------------------
A polygon is treated as a "closed thin-walled cell" entity if its name contains
either token (case-insensitive):

    "@CLOSED"  or  "@CELL"

Examples:
    ring@wall@closed@t=0.020
    box_skin@CELL
    cell1@cell@t=0.008

Important: "@WALL" is *not* required here; you can combine tags if you want.

Dispatch rule (same spirit as @WALL)
------------------------------------
- If no polygon name contains "@CLOSED" or "@CELL": this function returns
  compute_saint_venant_J(section) (legacy).
- Otherwise: only polygons tagged with "@CLOSED"/"@CELL" contribute.

Thickness per cell polygon
--------------------------
- If polygon name contains "@t=<value>": use that thickness (meters).
- Else: estimate thickness via the SAME rigid rule you already adopted for @WALL:

      t := 2*A / P

  where:
    A = abs(signed area of the *single polygon*),
    P = perimeter of the *single polygon* boundary.

Closed thin-walled torsion model (single-cell, constant thickness)
------------------------------------------------------------------
This function uses the Bredt-Batho single-cell engineering formula:

    J ≈ 4 * A_m^2 / ∮(ds/t)

For constant thickness t along the median line:

    J ≈ 4 * A_m^2 * t / b

where:
- A_m is the area enclosed by the median line,
- b = ∮ ds is the median line length (a "midline perimeter").

Key modelling point for your "single polygon ring with a cut"
-------------------------------------------------------------
Your "ring as ONE polygon" representation typically follows the pattern:
- traverse outer contour,
- insert a radial connection to the inner contour,
- traverse inner contour,
- connect back.

To compute A_m from this single polygon, we *reconstruct* two contours
(outer and inner) by exploiting the repeated vertices that delimit the loops.

Expected vertex pattern (robustly detected)
-------------------------------------------
Let v[0] be the first vertex.
We expect to find:
1) a second occurrence of v[0] somewhere later  -> end of OUTER loop
2) the next vertex is the INNER loop start v_in
3) a second occurrence of v_in later            -> end of INNER loop

From these two reconstructed loops:
- A_outer = |area(outer loop)|
- A_inner = |area(inner loop)|

Then:
- A_wall  = max(A_outer - A_inner, 0)
- A_m     ≈ (A_outer + A_inner)/2   (median-area proxy; exact for t->0 limit)

Finally, with constant thickness:
    b ≈ A_wall / t        (because A_wall ≈ b * t)
so:
    J ≈ 4 * A_m^2 * t / b = 4 * A_m^2 * t^2 / A_wall

Limitations / non-goals (explicit)
----------------------------------
- Multi-cell connected torsion is NOT solved here (compatibility matrices, etc.).
  If you tag multiple disjoint cells (physically disconnected), summing their J
  contributions is reasonable and is what we do.
- If the polygon does not match the expected "two loops separated by repeated points"
  pattern, we raise a CSFError to fail fast (transparent, no heuristics).

Weight convention
-----------------
For torsional stiffness (G*J), negative stiffness is not physically meaningful.
We therefore scale each polygon contribution by abs(weight), consistent with your
compute_saint_venant_J_wall implementation.

"""

def compute_saint_venant_J_cell(section: "Section") -> float:
    """
    Compute closed-cell Saint-Venant torsional constant J_sv [m^4]
    for polygons tagged as @cell/@closed using a thin-walled closed-cell model.

    Key parsing policy for @cell:
    - OUTER loop is detected by the first repeated occurrence of the first vertex.
    - INNER loop is the remaining tail after OUTER closure.
    - INNER explicit repeated endpoint is optional; implicit closure is accepted.
    """
    TOKEN_CELL = "@cell"
    TOKEN_CLOSED = "@closed"
    TOKEN_T = "@t="
    REQUIRE_EXPLICIT_T = True

    polys = getattr(section, "polygons", None)
    if not polys:
        return 0.0

    # -------------------------------------------------------------------------
    # 0) Select @cell polygons
    # -------------------------------------------------------------------------
    cell_polys = []
    for p in polys:
        nm = str(getattr(p, "name", "") or "")
        low = nm.lower()
        if (TOKEN_CELL in low) or (TOKEN_CLOSED in low):
            cell_polys.append(p)

    if not cell_polys:
        return 0.0

    # -------------------------------------------------------------------------
    # 1) Local helpers
    # -------------------------------------------------------------------------
    def _xy_list(poly) -> List[Tuple[float, float]]:
        """
        Return polygon vertices as [(x, y), ...], preserving original sequence.
        """
        verts = getattr(poly, "vertices", None)
        if not verts or len(verts) < 3:
            return []
        return [(float(v.x), float(v.y)) for v in verts]

    def _perimeter_xy(xy: List[Tuple[float, float]]) -> float:
        """
        Perimeter of a closed polygonal chain (last->first included).
        """
        n = len(xy)
        if n < 2:
            return 0.0
        P = 0.0
        for i in range(n):
            x0, y0 = xy[i]
            x1, y1 = xy[(i + 1) % n]
            dx = x1 - x0
            dy = y1 - y0
            P += (dx * dx + dy * dy) ** 0.5
        return P

    def _signed_area_xy(xy: List[Tuple[float, float]]) -> float:
        """
        Signed area by shoelace (>0 CCW, <0 CW).
        """
        area, _, _ = _poly_signed_area_centroid_xy(xy, EPS_A)
        return area

    def _key(pt: Tuple[float, float], ndigits: int = 12) -> Tuple[float, float]:
        """
        Quantized key for robust repeated-point detection.
        """
        return (round(pt[0], ndigits), round(pt[1], ndigits))

    def _parse_t(name: str) -> Optional[float]:
        """
        Parse @t=<value> from polygon name. Return positive float or None.
        """
        low = name.lower()
        idx = low.find(TOKEN_T)
        if idx < 0:
            return None

        start = idx + len(TOKEN_T)
        if start >= len(name):
            return None

        allowed = set("0123456789.+-eE")
        s = []
        for ch in name[start:]:
            if ch in allowed:
                s.append(ch)
            else:
                break

        if not s:
            return None

        try:
            tval = float("".join(s))
        except Exception:
            return None

        if tval <= 0.0:
            return None
        return tval

    def _find_outer_bridge_index(xy: List[Tuple[float, float]], nm: str) -> int:
        """
        Return index of first point matching the first vertex within global tolerance.
        Uses EPS_L as requested.
        """
        if not xy:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has empty vertex list."
            )

        x0, y0 = xy[0]
        tol2 = EPS_L * EPS_L
        i_outer_end = None

        for i in range(1, len(xy)):
            dx = xy[i][0] - x0
            dy = xy[i][1] - y0
            if (dx * dx + dy * dy) <= tol2:
                i_outer_end = i
                break

        if i_outer_end is None or i_outer_end < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' cannot split OUTER loop "
                f"(missing repeated outer-start vertex within tol={EPS_L:.6e})."
            )
        
        return i_outer_end

    def _extract_inner_loop_after_outer(
        xy: List[Tuple[float, float]],
        keys: List[Tuple[float, float]],
        i_outer_end: int,
        nm: str,
    ) -> List[Tuple[float, float]]:
        """
        Extract INNER loop from the tail after OUTER closure.

        Policy:
        - Implicit closure is accepted (no mandatory repeated last point).
        - If tail starts and ends with the same key, treat last as explicit closure
          and drop it.
        """
        rem_start = i_outer_end + 1
        if rem_start >= len(xy):
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' missing INNER loop segment."
            )

        rem_xy = xy[rem_start:]
        rem_keys = keys[rem_start:]

        # At least 3 vertices are required for an implicitly closed loop.
        if len(rem_xy) < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' insufficient vertices for INNER loop."
            )

        # Optional explicit closure on inner tail.
        if len(rem_xy) >= 2 and rem_keys[0] == rem_keys[-1]:
            inner_xy = rem_xy[:-1]
        else:
            inner_xy = rem_xy

        if len(inner_xy) < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' INNER loop degenerate."
            )

        return inner_xy

    def _split_outer_inner_loops(
        xy: List[Tuple[float, float]], nm: str
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]], int]:
        """
        Split slit-encoded polygon into OUTER and INNER loop candidates.

        OUTER:
            xy[0:i_outer_end], where i_outer_end is the first repetition of xy[0].
        INNER:
            extracted from remaining tail with implicit closure support.
        """
        keys = [_key(pt) for pt in xy]
        i_outer_end = _find_outer_bridge_index(xy, nm)

        #print(f"DEBUG i_outer_end {i_outer_end}")

        loop_a = xy[0:i_outer_end]
        loop_b = _extract_inner_loop_after_outer(xy, keys, i_outer_end, nm)

        if len(loop_a) < 3 or len(loop_b) < 3:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' produced degenerate loops."
            )

        return loop_a, loop_b, i_outer_end

    def _compute_J_geom_from_global_mid_quantities(
        outer_xy: List[Tuple[float, float]],
        inner_xy: List[Tuple[float, float]],
        t: float,
        nm: str,
        i_cell: int,
        z_sec,
    ) -> float:
        """
        Compute J using global mid-quantities (no pointwise pairing):
            A_m = 0.5*(A_outer + A_inner)
            b_m = 0.5*(P_outer + P_inner)
            J   = 4*A_m^2*t/b_m
        """
        A_outer = abs(_signed_area_xy(outer_xy))
        A_inner = abs(_signed_area_xy(inner_xy))
        A_wall = A_outer - A_inner

        if A_wall <= EPS_A:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has non-positive wall area "
                f"(A_outer={A_outer:.12g}, A_inner={A_inner:.12g})."
            )

        P_outer = _perimeter_xy(outer_xy)
        P_inner = _perimeter_xy(inner_xy)

        A_m = 0.5 * (A_outer + A_inner)
        b_m = 0.5 * (P_outer + P_inner)

        if A_m <= EPS_A or b_m <= EPS_L:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' degenerate global mid quantities "
                f"(A_m={A_m:.12g}, b_m={b_m:.12g})."
            )
        '''
        print(
            f"[CELL-GEOM][idx={i_cell}][z={z_sec}][{nm}] "
            f"A_outer={A_outer:.12g} A_inner={A_inner:.12g} A_wall={A_wall:.12g} "
            f"P_outer={P_outer:.12g} P_inner={P_inner:.12g} "
            f"A_m={A_m:.12g} b_m={b_m:.12g} t={t:.12g}"
        )
        '''
        return 4.0 * (A_m ** 2) * t / b_m

    # -------------------------------------------------------------------------
    # 2) Accumulate contributions
    # -------------------------------------------------------------------------
    J_total = 0.0

    for i_cell, p in enumerate(cell_polys):
        nm = str(getattr(p, "name", "") or "")

        # No silent default for structural weight.
        w = float(getattr(p, "weight"))
        if abs(w) < EPS_A:
            continue

        xy = _xy_list(p)
        z_sec = getattr(section, "z", None)
        '''
        print(
            f"[CELL-START][idx={i_cell}] z={z_sec} name={nm} "
            f"id={id(p)} nverts={len(xy)} first={xy[0] if xy else None}"
        )
        '''

        if len(xy) < 8:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' has too few vertices for slit-cell encoding."
            )

        # Thickness from @t=... (strict by policy).
        t = _parse_t(nm)
        if t is None:
            if REQUIRE_EXPLICIT_T:
                raise CSFError(
                    f"compute_saint_venant_J_cell(v3): polygon '{nm}' is @cell/@closed but missing '@t=...'."
                )
            A_poly_fallback = abs(float(polygon_area_centroid(p)[0]))
            P_poly_fallback = _perimeter_xy(xy)
            if P_poly_fallback < EPS_L:
                raise CSFError(
                    f"compute_saint_venant_J_cell(v3): polygon '{nm}' has near-zero perimeter."
                )
            t = 2.0 * A_poly_fallback / P_poly_fallback

        if t < EPS_L:
            raise CSFError(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' invalid thickness t={t}."
            )

        # Split loops (inner explicit closure is optional).
        loop_a, loop_b, i_outer_end = _split_outer_inner_loops(xy, nm)
        '''
        print(
            f"[OUTER_CLOSE][idx={i_cell}][z={z_sec}][{nm}] "
            f"first={xy[0]} repeated={xy[i_outer_end]}"
        )
        '''
        area_a = abs(_signed_area_xy(loop_a))
        area_b = abs(_signed_area_xy(loop_b))
        '''
        print(
            f"[CELL-LOOPS][idx={i_cell}][z={z_sec}][{nm}] "
            f"len_loop_a={len(loop_a)} len_loop_b={len(loop_b)} "
            f"area_a={area_a:.12g} area_b={area_b:.12g}"
        )
        '''
        # OUTER is the loop with larger absolute area.
        if area_a >= area_b:
            outer_xy = loop_a
            inner_xy = loop_b
        else:
            outer_xy = loop_b
            inner_xy = loop_a

        s_outer_before = _signed_area_xy(outer_xy)
        s_inner_before = _signed_area_xy(inner_xy)

        if s_outer_before < 0.0:
            outer_xy = list(reversed(outer_xy))
        if s_inner_before < 0.0:
            inner_xy = list(reversed(inner_xy))

        s_outer_after = _signed_area_xy(outer_xy)
        s_inner_after = _signed_area_xy(inner_xy)
        '''
        print(
            f"[CELL-ORIENT][idx={i_cell}][z={z_sec}][{nm}] "
            f"s_outer_before={s_outer_before:.12g} s_outer_after={s_outer_after:.12g} "
            f"s_inner_before={s_inner_before:.12g} s_inner_after={s_inner_after:.12g}"
        )
        '''
        # Optional area consistency warning.
        A_outer = abs(_signed_area_xy(outer_xy))
        A_inner = abs(_signed_area_xy(inner_xy))
        A_wall = A_outer - A_inner

        A_poly = abs(_signed_area_xy(xy))
        abs_err = abs(A_poly - A_wall)
        rel_err = abs_err / max(abs(A_wall), EPS_A)
        
        if abs_err > EPS_A and rel_err > EPS_K_RTOL:
            warnings.warn(
                f"compute_saint_venant_J_cell(v3): polygon '{nm}' "
                f"(idx={i_cell}, z={z_sec}) geometric area mismatch. "
                f"A_poly={A_poly:.12g}, A_outer-A_inner={A_wall:.12g}, "
                f"abs_err={abs_err:.12g}, rel_err={rel_err:.6e}",
                RuntimeWarning,
            )
        
        J_geom = _compute_J_geom_from_global_mid_quantities(
            outer_xy, inner_xy, t, nm, i_cell, z_sec
        )

        contrib = w * J_geom
        
        '''
        print(
            f"[CELL-CONTRIB][idx={i_cell}][z={z_sec}][{nm}] "
            f"w={w:.12g} J_geom={J_geom:.12g} contrib={contrib:.12g} J_total_before={J_total:.12g}"
        )
        '''
        J_total += contrib
        #print(f"[CELL-TOTAL][idx={i_cell}][z={z_sec}][{nm}] J_total_after={J_total:.12g}")


        if t is None:
                raise ValueError(
                    "compute_saint_venant_J_cell: no @cell polygon contributed; thickness t is undefined."
                )

        if len(cell_polys) == 1:
            return J_total, t
        else:
            return J_total

#----------------------------------------------------------------------------


"""
CSF torsion (Saint-Venant) - WALL-based variant with optional thickness override

Drop-in snippet: add this function in the same module where:
- Section / Polygon classes are defined
- polygon_area_centroid(poly) exists and returns (signed_area, cx, cy)
- compute_saint_venant_J(section) exists (legacy fallback)
- EPS_A, EPS_L exist (or replace with your tolerances)

User convention
---------------
A polygon is treated as a "wall entity" if its name contains the token "@WALL"
(case-insensitive). Example:

    web@wall
    top_flange@WALL

Optional thickness override:
----------------------------
The user may also provide a thickness override inside the SAME name string:

    web@wall@t=0.01
    top_flange@wall@t=0.0125

Rules:
- If "@t=<number>" is present, that thickness (in meters) is used for that wall polygon.
- If "@t=" is absent, thickness is estimated from pure geometry (rigid rule):

        t := 2*A / P

This is intentionally profile-agnostic: no shape recognition, no heuristics, no tests.
The user is responsible for tagging the correct polygons.

Theory (international standard: open thin-walled approximation)
---------------------------------------------------------------
For open thin-walled sections:

    J_sv ≈ Σ ( b_i * t_i^3 / 3 )

To avoid explicitly computing the midline length b_i, use the thin-wall identity:

    A_i ≈ b_i * t_i  =>  b_i ≈ A_i / t_i

Then:

    J_i ≈ (A_i / t_i) * t_i^3 / 3 = A_i * t_i^2 / 3

Important note on weights
-------------------------
CSF polygon weights may be used as stiffness scalars.
For torsion stiffness (G * J), negative stiffness is not physically meaningful,
so we scale contributions by abs(weight).
If you want a different convention, change abs(w) accordingly.
"""
def compute_saint_venant_J_wall(section: "Section") -> float:
    """
    Compute Saint-Venant torsional constant J_sv using "@WALL" polygons.

    Dispatch
    --------
    - If no polygon name contains "@WALL": return compute_saint_venant_J(section) (legacy).
    - Otherwise: use open thin-walled approximation on polygons tagged with "@WALL".

    Thickness choice per wall polygon
    ---------------------------------
    - If polygon name contains "@t=<value>": use that thickness (meters).
    - Else: estimate thickness via t := 2*A/P.

    Returns
    -------
    float
        Effective Saint-Venant torsional constant J_sv [m^4].
    """
    token_wall = "@WALL"
    token_t = "@t="

    polys = getattr(section, "polygons", None)
    if not polys:
        return 0.0

    # -----------------------------
    # 0) Select wall polygons
    # -----------------------------
    wall_polys = []
    for p in polys:
        nm = str(getattr(p, "name", "") or "")
        if token_wall.lower() in nm.lower():
            wall_polys.append(p)
    # No "@WALL" anywhere exit
    if not wall_polys:
        return 0.0 
    
    # -----------------------------
    # 1) Geometry helpers
    # -----------------------------
    def _poly_area_abs(poly) -> float:
        A_signed = polygon_area_centroid(poly)[0]
        return abs(float(A_signed))

    def _poly_perimeter(poly) -> float:
        verts = getattr(poly, "vertices", None)
        if not verts or len(verts) < 2:
            return 0.0
        perim = 0.0
        n = len(verts)
        for i in range(n):
            j = (i + 1) % n
            dx = float(verts[j].x) - float(verts[i].x)
            dy = float(verts[j].y) - float(verts[i].y)
            perim += (dx * dx + dy * dy) ** 0.5
        return perim

    # -----------------------------
    # 2) Parse optional "@t=<...>"
    # -----------------------------
    def _parse_thickness_from_name(name: str) -> Optional[float]:
        """
        Parse thickness override from a polygon name.

        Accepted patterns (case-insensitive):
            "...@t=0.01"
            "...@T=0.01"

        Parsing stops at the first non-numeric character (besides . + - e E).

        Returns
        -------
        float | None
            Thickness in meters, or None if not present / not parseable.
        """
        low = name.lower()
        idx = low.find(token_t)
        if idx < 0:
            return None

        start = idx + len(token_t)
        if start >= len(name):
            return None

        # Collect a valid float substring 
        allowed = set("0123456789.+-eE")
        s = []
        for ch in name[start:]:
            if ch in allowed:
                s.append(ch)
            else:
                break

        if not s:
            return None

        try:
            tval = float("".join(s))
        except Exception:
            return None

        # Reject non-positive values
        if tval <= 0.0:
            return None

        return tval

    # -----------------------------
    # 3) Compute J_sv (open thin-walled)
    # -----------------------------
    J = 0.0
    n_wall_used = 0 
    for p in wall_polys:
        w = float(getattr(p, "weight"))
        if abs(w) < EPS_A:
            continue

        A = _poly_area_abs(p)
        if A < EPS_A:
            continue

        nm = str(getattr(p, "name", "") or "")
        t_override = _parse_thickness_from_name(nm)
        t_source = "?"
        if t_override is not None:
            t = float(t_override)
            t_source = "@t"

        else:
            P = _poly_perimeter(p)
            if P < EPS_L:
                continue
            t = 2.0 * A / P
            t_source = "2A/P"
        if t < EPS_L:
            continue

        # Use A ≈ b*t to avoid explicit midline computation:
        # b ≈ A/t, so J_i ≈ (A/t)*t^3/3 = A*t^2/3
        J_i = (A * (t ** 2)) / 3.0

        J_i_wall = J_i


        P_dbg = _poly_perimeter(p)
        b_est = (A / t) if t > EPS_L else 0.0
        '''
        print(
            f"[J_WALL] nm={nm}  A={A:.6f}  P={P_dbg:.6f}  t={t:.6f} ({t_source})  "
            f"b_est=A/t={b_est:.6f}  J_i={J_i_wall:.6f}  w={w:.6f} "
        )
        '''

        # Keep torsional stiffness non-negative
        J += w * J_i

    if len(wall_polys) == 1:
        return float(J),t
    else:
        return float(J)



#---------------------------------------------------------------------------------------


"""
compute_saint_venant_j_co.py

Saint-Venant torsional constant J for *solid* polygonal domains (grid-based Prandtl solve).

Why your "simple box" looked like an infinite loop
--------------------------------------------------
With the previous defaults (auto_n=200, max_iter=20000), a 0.4 x 0.4 square generates
a grid of about 201 x 201 nodes (≈ 40k unknowns). Running 20k SOR sweeps means
~800 million node updates, which can look like a hang.

This revision keeps the same numerical method, but adds *explicit safety caps*:
- lower default auto_n
- lower default max_iter
- a maximum total grid node count; if exceeded, an error is raised (no silent coarsening)

Contract (explicit, by design)
------------------------------
- NO geometry validation: no convexity checks, no self-intersection checks, no orientation checks.
- NO sign post-processing: no abs(), no clipping, no "make positive".
- NO inner (nested) helper functions: all helpers are module-level.
- Each polygon is treated as its own SOLID filled domain; final result is a weighted sum.

Model (per polygon Ω_i)
-----------------------
Solve Prandtl stress function ψ:

    ∇²ψ = -2   in Ω_i
    ψ  =  0    on ∂Ω_i

Then:

    J_i = 2 ∫_{Ω_i} ψ dA

Method
------
Masked Cartesian grid + in-place SOR for the Poisson equation.

Weighted output
---------------
    J_total = Σ w_i * J_i     (weights are taken verbatim from poly.weight)
"""




PointXY = Tuple[float, float]


def _poly_vertices_xy(poly: Any) -> List[PointXY]:
    """Extract polygon vertices as plain (x, y) float tuples."""
    verts = getattr(poly, "vertices", None)
    if verts is None:
        raise ValueError(f"Polygon '{getattr(poly, 'name', None)}' has no .vertices attribute.")
    out: List[PointXY] = []
    for v in verts:
        out.append((float(getattr(v, "x")), float(getattr(v, "y"))))
    return out


def _bbox_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float, float]:
    """Axis-aligned bounding box for a vertex list."""
    if not verts:
        raise ValueError("Empty vertex list.")
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    return (min(xs), min(ys), max(xs), max(ys))


def _auto_grid_h_from_bbox(verts: Sequence[PointXY], auto_n: int) -> float:
    """
    Automatic grid spacing based on the polygon bounding box:

        h := min(span_x, span_y) / auto_n
    """
    if auto_n <= 0:
        raise ValueError("auto_n must be > 0.")
    x0, y0, x1, y1 = _bbox_xy(verts)
    span_x = x1 - x0
    span_y = y1 - y0
    span = span_x if span_x < span_y else span_y
    if span <= 0.0:
        raise ValueError("Degenerate polygon bounding box (zero span).")
    return span / float(auto_n)


def _point_on_segment_sq(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
    eps_l: float
) -> bool:
    """
    Return True if point (px,py) lies on segment AB, with tolerance.

    No abs(); uses squared comparisons.
    """
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay

    ab2 = abx * abx + aby * aby
    eps2 = eps_l * eps_l

    # Degenerate segment (A≈B): treat as a point.
    if ab2 <= eps2:
        dx = px - ax
        dy = py - ay
        return (dx * dx + dy * dy) <= eps2

    # Collinearity: cross product magnitude squared <= (eps^2 * |AB|^2)
    cross = abx * apy - aby * apx
    if (cross * cross) > (eps2 * ab2):
        return False

    # Projection: 0 <= dot <= |AB|^2 (with tolerance)
    dot = apx * abx + apy * aby
    if dot < -eps_l:
        return False
    if dot > (ab2 + eps_l):
        return False

    return True


def _point_in_poly_inclusive(px: float, py: float, verts: Sequence[PointXY], eps_l: float) -> bool:
    """
    Ray casting point-in-polygon, counting boundary as inside.

    No validation is performed; self-intersections may yield undefined results.
    """
    n = len(verts)
    if n < 3:
        return False

    # Boundary inclusion: test "on any edge".
    for i in range(n):
        ax, ay = verts[i]
        bx, by = verts[(i + 1) % n]
        if _point_on_segment_sq(px, py, ax, ay, bx, by, eps_l):
            return True

    inside = False
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]

        # Edge straddles horizontal line at py?
        cond = (y1 > py) != (y2 > py)
        if cond:
            x_int = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x_int > px:
                inside = not inside

    return inside


def _build_inside_mask(
    verts: Sequence[PointXY],
    xs: np.ndarray,
    ys: np.ndarray,
    eps_l: float
) -> np.ndarray:
    """Build boolean mask M[j,i] = True if grid node (xs[i], ys[j]) is inside polygon."""
    ny = int(ys.size)
    nx = int(xs.size)
    mask = np.zeros((ny, nx), dtype=bool)

    for j in range(ny):
        y = float(ys[j])
        for i in range(nx):
            x = float(xs[i])
            if _point_in_poly_inclusive(x, y, verts, eps_l):
                mask[j, i] = True

    return mask


def _solve_poisson_sor(
    mask: np.ndarray,
    h: float,
    *,
    max_iter: int,
    tol: float,
    omega: float
) -> np.ndarray:
    """
    Solve ∇²ψ = -2 on a masked grid using SOR, with ψ=0 outside.

    Stopping rule:
        max update magnitude <= tol
    (implemented via squared values; no abs()).
    """
    ny, nx = mask.shape
    psi = np.zeros((ny, nx), dtype=float)

    h2 = h * h
    tol2 = tol * tol
    rhs_term = 2.0 * h2  # from discretization of -2

    for _ in range(int(max_iter)):
        max_d2 = 0.0

        for j in range(ny):
            for i in range(nx):
                if not mask[j, i]:
                    continue

                old = psi[j, i]

                # Neighbor values, ψ=0 outside.
                e = psi[j, i + 1] if (i + 1 < nx and mask[j, i + 1]) else 0.0
                w = psi[j, i - 1] if (i - 1 >= 0 and mask[j, i - 1]) else 0.0
                n = psi[j - 1, i] if (j - 1 >= 0 and mask[j - 1, i]) else 0.0
                s = psi[j + 1, i] if (j + 1 < ny and mask[j + 1, i]) else 0.0

                gs = (e + w + n + s + rhs_term) * 0.25
                new = (1.0 - omega) * old + omega * gs
                psi[j, i] = new

                d = new - old
                d2 = d * d
                if d2 > max_d2:
                    max_d2 = d2

        if max_d2 <= tol2:
            break

    return psi


def _torsion_J_from_psi(psi: np.ndarray, mask: np.ndarray, h: float) -> float:
    """Discrete J ≈ 2 Σ ψ h^2 over inside nodes."""
    h2 = h * h
    return 2.0 * float(np.sum(psi[mask]) * h2)


def _compute_J_solid_polygon_grid(
    verts: Sequence[PointXY],
    *,
    grid_h: float,
    pad: float,
    eps_l: float,
    max_iter: int,
    tol: float,
    omega: float,
    max_grid_nodes: int
) -> float:
    """Compute J for ONE polygon as a solid filled domain."""
    if grid_h <= 0.0:
        raise ValueError("grid_h must be > 0.")

    x0, y0, x1, y1 = _bbox_xy(verts)

    x0 = x0 - pad
    y0 = y0 - pad
    x1 = x1 + pad
    y1 = y1 + pad

    xs = np.arange(x0, x1 + 0.5 * grid_h, grid_h, dtype=float)
    ys = np.arange(y0, y1 + 0.5 * grid_h, grid_h, dtype=float)

    nx = int(xs.size)
    ny = int(ys.size)
    nodes = nx * ny
    if nodes > int(max_grid_nodes):
        raise ValueError(
            "Grid too large for this polygon at the requested resolution. "
            "Increase grid_h or reduce auto_n, or raise max_grid_nodes explicitly."
        )

    if nx < 3 or ny < 3:
        raise ValueError("Grid too coarse for this polygon bounding box. Decrease grid_h.")

    mask = _build_inside_mask(verts, xs, ys, eps_l)

    if not np.any(mask):
        raise ValueError("No interior grid nodes detected. Decrease grid_h or check polygon scale.")

    psi = _solve_poisson_sor(mask, grid_h, max_iter=max_iter, tol=tol, omega=omega)
    return _torsion_J_from_psi(psi, mask, grid_h)



#----------------------------------------------------------------------------------------------------------------------------------------------


def alpha_from_keys(
    A: float,
    J: float,
    I1: float,
    I2: float,
    K_torsion: float | None = None,
) -> float:
    """
    Return alpha for the approximation J_SV ≈ alpha * J_p, with J_p = J (= Ix + Iy).

    Two modes:
    1) If K_torsion is provided, interpret it as an available estimate of J_SV and return:
           alpha = K_torsion / J
    2) Otherwise, assume a compact "rectangle-like" section and compute alpha from a
       rectangle-equivalent approximation based on A, I1, I2, J.

    No abs(), no sign normalization. Caller must ensure inputs make sense.


    """


    if J == 0.0:
        raise ValueError("J must be non-zero.")

    if K_torsion is not None:
        return K_torsion / J

    if I1 == 0.0 or I2 == 0.0:
        raise ValueError("I1 and I2 must be non-zero for the rectangle-equivalent mode.")

    # Ensure r >= 1 by swapping if needed (no abs involved).
    if I2 > I1:
        I1, I2 = I2, I1

    r = math.sqrt(I1 / I2)  # r >= 1
    if r == 0.0:
        raise ValueError("Invalid I1/I2 ratio.")

    # Rectangle-equivalent torsion approximation:
    # J_SV,rect ≈ (A^2 / (3 r)) * (1 - 0.63/r + 0.052/r^5)
    J_sv_rect = (A * A) / (3.0 * r) * (1.0 - 0.63 / r + 0.052 / (r**5))
    alpha = J_sv_rect / J
    return alpha



"""
compute_saint_venant_j_new_approc.py

A CSF-friendly (fast, deterministic) approximation for the Saint-Venant torsional constant J.

Why this exists
---------------
A PDE-based Prandtl solve (FEM/FD + iterative Poisson) is not aligned with CSF goals:
- it is slow and can appear to "hang" depending on grid/shape,
- it introduces solver parameters and convergence heuristics,
- it is fragile for "unknown" polygon quality (self-intersections, near-degeneracy).

This file provides a deliberately simple alternative:

    J_sv  ≈  α * J_p

where J_p is the polar second moment of area about the centroid:

    J_p = I_x + I_y

This approximation is:
- O(N_vertices) if you already compute section properties (constant-time wrapper),
- O(N_polygons * N_vertices) in the pure-geometry fallback,
- deterministic (no loops, no convergence, no timeouts),
- composable with CSF polygon weights.

Accuracy note
-------------
For a solid circle:  J_sv = J_p  (α = 1).
For a solid square:  J_sv ≈ 0.8436 * J_p.

So α is a *shape factor* capturing warping effects in a single scalar.
Default α is set to match the solid square case (common engineering baseline).

Scope / contract
----------------
- No geometric validation: no convexity checks, no self-intersection checks, no orientation checks.
- No repair or normalization of signs.
- No nested helper functions (module-level helpers only).
- Polygons are combined through their weights exactly as CSF does for other properties.

Recommended usage in CSF
------------------------
If your codebase already has:

    section_properties(section) -> dict with keys 'Ix','Iy' (centroidal) and/or 'J'

then you should rely on that (fastest, most consistent with the rest of CSF).

Otherwise, this module includes a standalone, pure-geometry fallback that computes:
- weighted area A,
- weighted centroid (Cx,Cy),
- weighted centroidal inertias Ix,Iy,
- then J_p = Ix + Iy.

Data model expectations
-----------------------
- section.polygons: iterable of polygon-like objects
- each polygon has:
    - .vertices: iterable of points with .x and .y
    - .weight  : numeric (MUST exist; no silent default)

Return value
------------
A single float: the *weighted* torsional constant approximation for the section.
"""

PointXY = Tuple[float, float]


# -----------------------------------------------------------------------------
# Helpers: robust "sign-agnostic" comparisons without using abs()
# -----------------------------------------------------------------------------

def _sq(x: float) -> float:
    return x * x


def _is_near_zero(x: float, eps: float) -> bool:
    """
    Compare x to 0 using squared values to avoid abs().

    Note: This is for degeneracy guards only (division-by-zero avoidance).
    It does not "fix" or "normalize" signs.
    """
    return _sq(x) <= _sq(eps)


# -----------------------------------------------------------------------------
# Geometry fallback: compute weighted centroidal polar moment without relying on
# external CSF helpers.
# -----------------------------------------------------------------------------

def _poly_signed_area_centroid_xy(verts: Sequence[PointXY], eps_a: float) -> Tuple[float, float, float]:
    """
    Shoelace formula.

    Returns
    -------
    (A, Cx, Cy)
        A  : signed polygon area (depends on vertex winding).
        Cx : centroid x
        Cy : centroid y

    Notes
    -----
    - Works for simple (non self-intersecting) polygons.
    - For self-intersecting polygons, results are an algebraic "signed" integral.
    """
    n = len(verts)
    if n < 3:
        raise ValueError("Polygon has <3 vertices.")

    a2 = 0.0
    cx6 = 0.0
    cy6 = 0.0

    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a2 += cross
        cx6 += (x0 + x1) * cross
        cy6 += (y0 + y1) * cross

    A = 0.5 * a2

    if _is_near_zero(A, eps_a):
        raise ValueError("Polygon area is ~0; cannot compute centroid/inertia reliably.")

    Cx = cx6 / (3.0 * a2)
    Cy = cy6 / (3.0 * a2)

    return A, Cx, Cy


def _poly_inertia_about_origin_xy(verts: Sequence[PointXY]) -> Tuple[float, float, float]:
    """
    Second moments about the origin (0,0) using standard polygon formulas.

    Returns
    -------
    (Ix_o, Iy_o, Ixy_o)
        About origin, signed consistently with the polygon winding.
    """
    n = len(verts)
    if n < 3:
        raise ValueError("Polygon has <3 vertices.")

    Ix = 0.0
    Iy = 0.0
    Ixy = 0.0

    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0

        Ix += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        Iy += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        Ixy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cross

    Ix *= (1.0 / 12.0)
    Iy *= (1.0 / 12.0)
    Ixy *= (1.0 / 24.0)
    return Ix, Iy, Ixy


def _section_polar_moment_fallback(section: Any, eps_a: float) -> float:
    """
    Compute the weighted polar second moment J_p = Ix + Iy about the *weighted* centroid.

    This is a pure-geometry fallback used only if `section_properties(section)` is not available.

    Important:
    - No "fixing" of winding is performed.
    - Polygon weights are applied as linear scalars to (A, Ix, Iy, Ixy).
    """
    polys = getattr(section, "polygons", None)
    if polys is None:
        raise ValueError("Input 'section' has no .polygons attribute.")

    # First pass: weighted area and centroid
    A_tot = 0.0
    Qx = 0.0
    Qy = 0.0

    cache: List[Tuple[Sequence[PointXY], float, float, float, float]] = []
    # cache item: (verts_xy, w, A, Cx, Cy)

    for p in polys:
        if not hasattr(p, "weight"):
            raise ValueError(f"Polygon '{getattr(p, 'name', None)}' has no .weight attribute.")
        w = float(getattr(p, "weight"))

        verts_obj = getattr(p, "vertices", None)
        if not verts_obj:
            raise ValueError(f"Polygon '{getattr(p, 'name', None)}' has no .vertices.")
        verts_xy = [(float(v.x), float(v.y)) for v in verts_obj]

        A, Cx, Cy = _poly_signed_area_centroid_xy(verts_xy, eps_a)
        Aw = w * A
        A_tot += Aw
        Qx += Aw * Cx
        Qy += Aw * Cy

        cache.append((verts_xy, w, A, Cx, Cy))

    if _is_near_zero(A_tot, eps_a):
        raise ValueError("Composite area is ~0; cannot compute section centroid/properties reliably.")

    Cx_tot = Qx / A_tot
    Cy_tot = Qy / A_tot

    # Second pass: weighted inertias about origin, then shift to composite centroid
    Ix_o = 0.0
    Iy_o = 0.0
    Ixy_o = 0.0

    for verts_xy, w, _, _, _ in cache:
        ix, iy, ixy = _poly_inertia_about_origin_xy(verts_xy)
        Ix_o += w * ix
        Iy_o += w * iy
        Ixy_o += w * ixy

    # Parallel axis theorem to composite centroid
    Ix_c = Ix_o - A_tot * (Cy_tot * Cy_tot)
    Iy_c = Iy_o - A_tot * (Cx_tot * Cx_tot)
    # Ixy_c not needed for J_p, but kept here as a reminder:
    # Ixy_c = Ixy_o - A_tot * (Cx_tot * Cy_tot)

    return Ix_c + Iy_c


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def compute_saint_venant_J(
    section: Any,
    alpha: float = 0.8436,
    *,
    eps_a: Optional[float] = None,
) -> float:
    """
    Approximate Saint-Venant torsional constant for a (possibly composite) section.

    Formula
    -------
        J_sv ≈ alpha * J_p
        J_p  = I_x + I_y  (about the centroid)

    Parameters
    ----------
    section:
        Section-like object with .polygons.
    alpha:
        Shape factor. Default 0.8436 matches a solid square.
        Set alpha=1.0 to match a solid circle.
    eps_a:
        Area tolerance used only for degeneracy checks in the fallback path.
        If None, we try to read EPS_A from `section` or `section.field`.
        If neither exists, eps_a defaults to 0.0 (exact zero check).

    Behavior
    --------
    1) If a callable `section_properties` symbol exists in the current namespace,
       it is used as the primary source of centroidal inertias (fast and consistent).
       Expected keys:
         - either 'J' (polar moment) OR both 'Ix' and 'Iy' (centroidal).
    2) Otherwise, a pure-geometry fallback computes J_p directly.

    Notes
    -----
    - This function never iterates a solver and cannot "hang".
    - No attempt is made to interpret convexity, holes, or topology.
      The result is exactly as "blind" as alpha * (Ix+Iy) can be.
    """
    # Resolve eps_a (only used in fallback degeneracy checks).
    if eps_a is None:
        eps_val = None
        if hasattr(section, "EPS_A"):
            try:
                eps_val = float(getattr(section, "EPS_A"))
            except Exception:
                eps_val = None
        if eps_val is None:
            fld = getattr(section, "field", None)
            if fld is not None and hasattr(fld, "EPS_A"):
                try:
                    eps_val = float(getattr(fld, "EPS_A"))
                except Exception:
                    eps_val = None
        eps_a_val = float(eps_val) if eps_val is not None else 0.0
    else:
        eps_a_val = float(eps_a)

    # Primary path: rely on existing CSF section_properties if present.
    sp = globals().get("section_properties", None)
    if callable(sp):
        props = sp(section)
        if isinstance(props, dict):
            if "J" in props:
                Jp = float(props["J"])
            elif ("Ix" in props) and ("Iy" in props):
                Jp = float(props["Ix"]) + float(props["Iy"])
            else:
                raise ValueError("section_properties(section) did not provide 'J' nor ('Ix','Iy').")
        else:
            raise ValueError("section_properties(section) did not return a dict-like object.")
    else:
        # Fallback path: compute J_p directly from polygon geometry.
        Jp = _section_polar_moment_fallback(section, eps_a_val)

    return float(alpha) * float(Jp)


##############################################################################################################################################à

def export_to_opensees_tcl(field, K_12x12, filename="csf_model.tcl"):
    """
      Generates an OpenSees-ready .tcl file that defines the nodes and the stiffness-matrix element computed by CSF.
    """
    z0 = field.z0
    z1 = field.z1
    
    with open(filename, "w") as f:
        f.write("# --------------------------------------------------\n")
        f.write("# Model automatically generated by CSF (Continuous Section Field)\n")
        f.write("# --------------------------------------------------\n\n")
        
        # 1. Definition of the Nodes (Base and Top)
        # Syntax: node nodeTag x y z
        f.write(f"node 1 0.0 0.0 {z0}\n")
        f.write(f"node 2 0.0 0.0 {z1}\n\n")
        
        # 2. Definition of the stiffness matrix K in TCL list format
        f.write("set K {\n")
        for row in K_12x12:
            row_str = " ".join(f"{val:.8e}" for val in row)
            f.write(f"    {row_str}\n")
        f.write("}\n\n")
        
        # 3. Definition of the geometric transformation (required in OpenSees)
        f.write("geomTransf Linear 1 0 1 0\n\n")
        
        # 4. Definition of the MatrixBeamColumn element
        # Syntax: element matrixBeamColumn eleTag iNode jNode transfTag Klist
        f.write("element matrixBeamColumn 1 1 2 1 $K\n\n")
        
        f.write("puts \"CSF model successfully loaded: 2 nodes, 1 element (12×12 stiffness matrix)\"\n")

    print(f"TCL file generated successfully: {filename}")


def assemble_element_stiffness_matrix(field: ContinuousSectionField, E_ref: float = 1.0, 
                                nu: float = 0.3, n_gauss: int = 5) -> np.ndarray:
    """
    Assembles the complete 12x12 Timoshenko beam stiffness matrix with full EIxy coupling.

    DOF order (OpenSees compatible): [ux1,uy1,uz1,θx1,θy1,θz1 | ux2,uy2,uz2,θx2,θy2,θz2]
    Full asymmetric section support (EIxy coupling) + Saint-Venant torsion.
    """
    L = abs(field.z1 - field.z0)
    if L < EPS_L:
        raise ValueError("Element length must be positive")

    G_ref = E_ref / (2 * (1 + nu))

    # Gaussian quadrature points (n_gauss sufficient for exact integration)
    gauss_points = np.polynomial.legendre.leggauss(n_gauss)

    K = np.zeros((12, 12))

    for xi, weight in gauss_points:
        z_phys = ((field.z1 - field.z0) * xi + (field.z1 + field.z0)) / 2.0 # absolute z
        W = weight * (L / 2.0)
        
        # Sectional properties
        K_sec = section_stiffness_matrix(field.section(z_phys), E_ref=E_ref) # absolute z
        props = section_full_analysis(field.section(z_phys))#alpha not used
        
        Jt = props.get("J_sv", 0.0)
        if Jt <= 0.0:
            Jt = props.get("J_s_vroark", 0.0)
        GK = G_ref * Jt

        EA = K_sec[0, 0]
        EIx = K_sec[1, 1] 
        EIy = K_sec[2, 2]
        EIxy = K_sec[1, 2]
        #GK = props['J'] * G_ref  # Correct Saint-Venant torsion
        
        # Integration coefficients (Euler-Bernoulli exact)
        c1 = 12 * W / L**3
        c2 = 6 * W / L**2  
        c3 = 4 * W / L
        c4 = 2 * W / L
        
        # AXIAL (DOF 0,6)
        axial = EA * W / L
        K[0,0] += axial; K[6,6] += axial
        K[0,6] -= axial; K[6,0] -= axial
        
        # TORSION (DOF 3,9) - Saint-Venant
        tors = GK * W / L
        K[3,3] += tors; K[9,9] += tors  
        K[3,9] -= tors; K[9,3] -= tors
        
        # FLEXURE YZ (about X) - DOF 1,5,7,11 [uy1,θz1,uy2,θz2]
        K[1,1] += c1*EIx; K[1,5] += c2*EIx; K[1,7] -= c1*EIx; K[1,11] += c2*EIx
        K[5,5] += c3*EIx; K[5,7] -= c2*EIx; K[5,11] += c4*EIx
        K[7,7] += c1*EIx; K[7,11] -= c2*EIx
        K[11,11] += c3*EIx
        
        # FLEXURE XZ (about Y) - DOF 2,4,8,10 [uz1,θy1,uz2,θy2] 
        K[2,2] += c1*EIy; K[2,4] -= c2*EIy; K[2,8] -= c1*EIy; K[2,10] -= c2*EIy
        K[4,4] += c3*EIy; K[4,8] += c2*EIy; K[4,10] += c4*EIy
        K[8,8] += c1*EIy; K[8,10] += c2*EIy
        K[10,10] += c3*EIy
        
        # FULL EIxy COUPLING (24 terms) - Bending-bending interaction
        # Node 1 rotations [uy1,uz1] = [1,2] couple with [θz1,θy1] = [5,4]
        K[1,2] += c1*EIxy; K[2,1] += c1*EIxy
        K[1,4] -= c2*EIxy; K[4,1] -= c2*EIxy  
        K[1,8] -= c1*EIxy; K[8,1] -= c1*EIxy
        K[1,10] -= c2*EIxy; K[10,1] -= c2*EIxy
        
        K[2,5] += c2*EIxy; K[5,2] += c2*EIxy
        K[4,5] += c4*EIxy; K[5,4] += c4*EIxy  # Corrected from 0.0
        K[2,7] -= c1*EIxy; K[7,2] -= c1*EIxy
        K[2,11] -= c2*EIxy; K[11,2] -= c2*EIxy
        
        K[5,8] -= c2*EIxy; K[8,5] -= c2*EIxy
        K[5,10] += c4*EIxy; K[10,5] += c4*EIxy
        K[7,4] -= c2*EIxy; K[4,7] -= c2*EIxy
        K[7,10] += c2*EIxy; K[10,7] += c2*EIxy
        
        K[11,4] += c2*EIxy; K[4,11] += c2*EIxy
        K[11,8] -= c2*EIxy; K[8,11] -= c2*EIxy

    # Final validation (reciprocity theorem)
    if not np.allclose(K, K.T, rtol=EPS_K_RTOL, atol=EPS_K_ATOL):
        warnings.warn("Minor asymmetry detected - enforcing symmetry", RuntimeWarning)
        K = (K + K.T) / 2.0

    # Physical bounds check
    if np.any(np.diag(K[:6]) < 0):
        raise ValueError("Negative diagonal stiffness detected")
        
    return K

    
def polygon_inertia_about_origin(poly: Polygon) -> Tuple[float, float, float]:
    """
    Second moments about the origin (0,0) using standard polygon formulas.
    Returns (Ix, Iy, Ixy) about origin, INCLUDING poly.weight.

    Notes:
    - Works for simple polygons (non self-intersecting).
    - Sign/orientation is handled by using signed cross; we then multiply by weight.
    - For holes, you can use negative weight or a separate convention.
    """
    verts = poly.vertices
    n = len(verts)

    Ix = 0.0
    Iy = 0.0
    Ixy = 0.0

    for i in range(n):
        x0, y0 = verts[i].x, verts[i].y
        x1, y1 = verts[(i + 1) % n].x, verts[(i + 1) % n].y
        cross = x0 * y1 - x1 * y0

        Ix += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        Iy += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        Ixy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cross

    Ix *= (1.0 / 12.0)
    Iy *= (1.0 / 12.0)
    Ixy *= (1.0 / 24.0)

    # Apply weight; keep sign conventions consistent by using magnitude of orientation implicitly
    # For typical usage, we want weighted contributions. We take absolute values of Ix/Iy if polygon orientation flips.
    # Using signed formulas + abs for Ix/Iy tends to be robust for mixed orientations in prototypes.
    return (poly.weight * abs(Ix), poly.weight * abs(Iy), poly.weight * Ixy)


"""
Volume integration utilities for CSF (ContinuousSectionField).

This file provides a drop-in replacement for the fixed n-point Gauss–Legendre
volume integration used in section_field.py.

The core idea is unchanged:

    V = ∫_z0^z1 A(z) dz

where A(z) is obtained by evaluating the CSF section at z and extracting its
(net / transformed) area from section_properties(...).

The improvement is that the number of Gauss points is now a parameter.

"""
# NOTE:
# - This function assumes the following names exist in section_field.py:
#     - class ContinuousSectionField with attributes z0, z1 and method section(z)
#     - function section_properties(section) returning a dict containing key "A"
#
# If your code uses different names (e.g., "field.z0/z1" or "props['A_tr']"),
# adjust only the extraction line where we read the area.
def integrate_volume(
    field: "ContinuousSectionField",
    z0: float,
    z1: float,
    n_points: int = 20,
    *,
    idx: int | None = None,
) -> float | tuple[float, float]:
    """
    Integrate "volume-like" quantities over [z0, z1] using Gauss–Legendre quadrature.

    Two scenarios only
    ------------------
    1) idx is None (LEGACY):
         Returns a single float:
           V_legacy = ∫ A_global(z) dz
         where A_global(z) is taken from:
           section_properties(field.section(z))["A"]
         (This preserves the existing legacy meaning: global area as defined by section_properties.)

    2) idx is an int (0-based):
         Returns a tuple of two floats:
           (V_geom, V_weighted)
         computed for ONE polygon only, using the "occupied surface" rule:
           - polygon has w=1
           - direct inners have w=0

         At each z we use polygon_surface_w1_inners0[_single] to get:
           A_net(z) = occupied surface (w=1 on polygon, w=0 on direct inners)
           A_w(z)   = A_net(z) * w_eff(z)

         Then:
           V_geom     = ∫ A_net(z) dz
           V_weighted = ∫ A_w(z) dz

    Notes
    -----
    - In idx mode we DO NOT call section_properties(...) to avoid mixing global weighted section logic.
    - Integration uses |z1 - z0| so results are positive "volumes" regardless of interval direction.
    """
    # --- basic validation ---
    if not isinstance(n_points, int) or n_points < 1:
        raise ValueError("n_points must be an integer >= 1")

    if not isinstance(z0, (int, float)):
        raise TypeError(f"z0 must be a number (float), got {type(z0).__name__}")
    if not isinstance(z1, (int, float)):
        raise TypeError(f"z1 must be a number (float), got {type(z1).__name__}")
    z0 = float(z0)
    z1 = float(z1)

    if idx is not None:
        if not isinstance(idx, int):
            raise TypeError(f"idx must be an int (0-based) or None, got {type(idx).__name__}")
        if idx < 0:
            raise ValueError(f"idx must be >= 0 (0-based), got {idx}")

    # Interval length (use absolute to produce positive "volume-like" values)
    L = abs(z1 - z0)
    if L == 0.0:
        return (0.0, 0.0) if idx is not None else 0.0

    z_mid = 0.5 * (z0 + z1)
    half_L = 0.5 * L

    # Gauss–Legendre nodes/weights on [-1, 1]
    xi, wi = np.polynomial.legendre.leggauss(n_points)

    # --- accumulators ---
    if idx is None:
        volume_legacy = 0.0
    else:
        volume_geom = 0.0
        volume_weighted = 0.0

    def _poly_A_pair_at_z(z_abs: float) -> tuple[float, float]:
        """
        Return (A_net, A_w) for the selected polygon idx at z_abs.

        Prefer a dedicated single-polygon function if it exists; otherwise
        fall back to computing the full list and selecting the requested idx.
        """
        # Try the specialized single function if available in the module namespace.
        fn = globals().get("polygon_surface_w1_inners0_single")
        if callable(fn):
            rec = fn(field, z_abs, idx)  # type: ignore[misc]
            return float(rec["A"]), float(rec["A_w"])

        # Fallback: compute full list once at this z and pick the record by idx.
        rows = polygon_surface_w1_inners0(field, z_abs)
        for r in rows:
            if int(r.get("idx", -1)) == idx:
                return float(r["A"]), float(r["A_w"])
        raise ValueError(f"Polygon idx={idx} not found at z={z_abs}.")

    # --- integration loop ---
    for x, w in zip(xi, wi):
        # Map x in [-1,1] to z in [z0,z1] (using midpoint + half-length)
        z = z_mid + half_L * float(x)
        w = float(w)

        if idx is None:
            # -----------------------------------------------------------------
            # LEGACY integrand (explicit and isolated):
            #   A_global(z) from section_properties(...)["A"]
            # -----------------------------------------------------------------
            sec = field.section(z)
            props = section_properties(sec)
            A_global = float(props["A"])
            volume_legacy += A_global * w * half_L
        else:
            # -----------------------------------------------------------------
            # IDX integrands (explicit and isolated):
            #   A_net(z): occupied surface (w=1 on polygon, w=0 on direct inners)
            #   A_w(z)  : A_net(z) * w_eff(z)
            # -----------------------------------------------------------------
            A_net, A_w = _poly_A_pair_at_z(z)
            volume_geom += A_net * w * half_L
            volume_weighted += A_w * w * half_L

    return volume_legacy if idx is None else (volume_geom, volume_weighted)



def section_full_analysis(section: Section,alpha: float = 1.0):
    """
    Performs a comprehensive structural and geometric analysis of a cross-section.
    
    This function integrates primary geometric data with advanced derived properties, 
    including principal inertial axes, elastic section moduli for bending stress 
    estimation, and a refined torsional constant based on Saint-Venant's semi-empirical 
    approximation for shape-agnostic rigidity.
    """
    
    # -------------------------------------------------------------------------
    # 1. PRIMARY GEOMETRIC COMPUTATION
    # -------------------------------------------------------------------------
    # Calculate fundamental properties: Net Area (A), Centroid coordinates (Cx, Cy),
    # Global Moments of Inertia (Ix, Iy, Ixy), and the Polar Moment (J).
    # This step accounts for weighted polygons (e.g., negative weights for holes).

    
    props = section_properties(section)
    
    # -------------------------------------------------------------------------
    # 2. PRINCIPAL AXIS ANALYSIS
    # -------------------------------------------------------------------------
    # Compute principal moments of inertia (I1, I2) and the rotation angle (theta).
    # This identifies the orientation where the product of inertia is zero, 
    # crucial for analyzing unsymmetrical bending.
    derived = section_derived_properties(props)
    
    # -------------------------------------------------------------------------
    # 3. ELASTIC SECTION MODULI (W) - BENDING CAPACITY
    # -------------------------------------------------------------------------
    # To determine the maximum bending stress (sigma = M/W), we must find the 
    # distance to the "extreme fibers" (the points furthest from the centroid).
    
    # Extract all vertex coordinates from every polygon in the section
    all_x = [v.x for poly in section.polygons for v in poly.vertices]
    all_y = [v.y for poly in section.polygons for v in poly.vertices]
    
    # Compute the maximum perpendicular distance from the centroidal axes:
    # y_dist_max is used for bending about the X-axis (Top/Bottom fiber)
    y_dist_max = max(max(all_y) - props['Cy'], props['Cy'] - min(all_y))
    # x_dist_max is used for bending about the Y-axis (Left/Right fiber)
    x_dist_max = max(max(all_x) - props['Cx'], props['Cx'] - min(all_x))
    
    # Calculate Elastic Moduli: W = I / c_max.
    # A tolerance check (EPS_K) prevents division by zero in degenerate geometries.
    props['Wx'] = props['Ix'] / y_dist_max if y_dist_max > EPS_K else 0.0
    props['Wy'] = props['Iy'] / x_dist_max if x_dist_max > EPS_K else 0.0
    
# -------------------------------------------------------------------------
    # 4. TORSIONAL RIGIDITY (K) - BETA ESTIMATION
    # -------------------------------------------------------------------------
    # J (props['J']) is the Polar Moment of Inertia (computed via Green's theorem).
    # For non-circular sections, J overestimates torsional stiffness.
    # We add 'K_torsion' as a semi-empirical approximation: J_eff ≈ A^4 / (40 * Ip)
    
    A = props['A']
    Ip = props['Ix'] + props['Iy'] # Polar moment about centroid (Ip = J for centroidal axes)
    
    # Keep props['J'] exactly as originally computed by section_properties
    if Ip > EPS_K:
        props['K_torsion'] = (A**4) / (40.0 * Ip)
    else:
        props['K_torsion'] = 0.0
    

# -------------------------------------------------------------------------
    # 4b. ADVANCED ANALYSIS (Statical Moment and Refined Torsion) Statical Moment
    # first moment na
    # -------------------------------------------------------------------------
    # 1. Calculate Q at the Neutral Axis (useful for shear stress tau = V*Q/I*b)
    # Using the robust version of section_statical_moment_partial.
    props['Q_na'] = section_statical_moment_partial(section, y_cut=props['Cy'])
    
    # Torsional_constant
    # 2. Calculate Refined Saint-Venant Torsional Constant (J) torsional_constant
    # This provides a more accurate value than K_torsion for specific shapes.
    prop_deriv=section_derived_properties(props)
    '''
    alpha = alpha_from_keys(
        A=props["A"],
        J=props["J"],
        I1=prop_deriv["I1"],
        I2=prop_deriv["I2"],
        K_torsion=props.get("K_torsion"),  # omit or set to None to use rectangle-equivalent mode
    )
    '''

    props['J_sv'] = compute_saint_venant_J(section, alpha=alpha, eps_a=EPS_A)#compute_saint_venant_J(section)
    props['J_sv_alpha']=alpha
    props['J_sv_cell'] =compute_saint_venant_J_cell(section)#compute_saint_venant_J_wall(section)
    props['J_sv_wall'] = compute_saint_venant_J_wall(section)
    props['J_s_vroark'],props['J_s_vroark_fidelity']= compute_saint_venant_Jv2(section)
    


    # -------------------------------------------------------------------------
    # 5. DATA CONSOLIDATION
    # -------------------------------------------------------------------------
    # Merge the primary properties with the derived principal axis data into 
    # a single comprehensive dictionary for downstream structural solvers.
    return {**props, **derived}

def polygon_statical_moment(poly: Polygon, y_axis: float) -> float:
    """
    Computes the First Moment of Area (Statical Moment), Q, of a SINGLE polygon 
    relative to a specific horizontal axis (y_axis).
    
    TECHNICAL NOTES:
    - Formula: Q = Area * (y_centroid - y_axis)
    - Sign Convention: Positive if the polygon centroid is above the reference axis.
    - Homogenization: Uses weighted area to account for holes or material density.
    """
    area_i, (cx_i, cy_i) = polygon_area_centroid(poly)
    # Distance from the polygon centroid to the reference axis
    d_y = cy_i - y_axis
    return area_i * d_y

def section_statical_moment_partial(section: Section, y_cut: float, reference_axis: float | None = None) -> float:
    """
    Compute the statical moment Q of the portion of the section located ABOVE y_cut,
    with respect to a horizontal reference axis y = y_ref.

    The section is processed polygon-by-polygon:
    - Each polygon is clipped by the half-plane y >= y_cut.
    - For the retained part, we compute its area and centroid.
    - We accumulate Q = A_part * (Cy_part - y_ref), using signed area if the polygon
      representation supports signed contributions (e.g., holes via orientation/sign).
    """
    # Compute section-level properties to obtain the default reference axis (neutral axis).
    props = section_properties(section)
    y_ref = props["Cy"] if reference_axis is None else reference_axis

    q_total = 0.0
    eps = EPS_L  # Geometric tolerance for comparisons and degenerate cases.

    for poly in section.polygons:
        verts = poly.vertices
        n = len(verts)

        # Clip polygon against the half-plane y >= y_cut using an edge-walking approach.
        clipped: list[Pt] = []

        for i in range(n):
            p1 = verts[i]
            p2 = verts[(i + 1) % n]

            # Classify endpoints with a tolerance to reduce numerical flicker at the cut line.
            p1_in = (p1.y >= y_cut - eps)
            p2_in = (p2.y >= y_cut - eps)

            if p1_in and p2_in:
                # Edge fully inside: keep the end vertex.
                clipped.append(p2)

            elif p1_in and not p2_in:
                # Edge exits the half-plane: add the intersection point (if not horizontal).
                dy = p2.y - p1.y
                if abs(dy) > eps:
                    t = (y_cut - p1.y) / dy
                    clipped.append(Pt(p1.x + t * (p2.x - p1.x), y_cut))

            elif (not p1_in) and p2_in:
                # Edge enters the half-plane: add the intersection point then the end vertex.
                dy = p2.y - p1.y
                if abs(dy) > eps:
                    t = (y_cut - p1.y) / dy
                    clipped.append(Pt(p1.x + t * (p2.x - p1.x), y_cut))
                clipped.append(p2)

            # If both endpoints are outside, add nothing.

        # A valid polygonal region needs at least 3 vertices after clipping.
        if len(clipped) < 3:
            continue

        # Skip regions that are effectively flat on the cut line.
        if all(abs(v.y - y_cut) < eps for v in clipped):
            continue

        # Build a clipped polygon with the same weight as the source polygon.
        clipped_poly = Polygon(vertices=tuple(clipped), weight=poly.weight)

        # Compute area and centroid of the clipped part.
        area_part, (_, cy_part) = polygon_area_centroid(clipped_poly)

        # Ignore negligible contributions.
        if abs(area_part) <= eps:
            continue

        # Statical moment contribution of this clipped part about y = y_ref.
        q_total += area_part * (cy_part - y_ref)

    return q_total

def section_derived_properties_debug(props: Dict[str, float], debug: bool = True) -> Dict[str, float]:
    """
    Computes derived structural properties including principal moments of inertia,
    principal axis rotation, and radius of gyration.

    Brutal debug mode:
    - Set debug=True to print every intermediate quantity and consistency checks.
    """
    # --- mandatory inputs ---
    Ix = float(props['Ix'])
    Iy = float(props['Iy'])
    Ixy = float(props['Ixy'])
    A = float(props['A'])

    # Optional context fields (if present) for easier trace
    z_here = props.get('z', None)
    sec_name = props.get('name', 'unnamed')

    # --- Mohr circle core terms ---
    avg = 0.5 * (Ix + Iy)
    diff = 0.5 * (Ix - Iy)
    R_sq = diff * diff + Ixy * Ixy
    R = math.sqrt(R_sq) if R_sq >= 0.0 else float("nan")  # defensive, should be >= 0

    I1 = avg + R
    I2 = avg - R

    # --- principal direction (with isotropy guard) ---
    iso_thr = abs(avg) * EPS_K
    is_near_isotropic = (R < iso_thr)

    if is_near_isotropic:
        theta = 0.0
        theta_mode = "forced_zero_by_isotropy_guard"
    else:
        theta = 0.5 * math.atan2(-2.0 * Ixy, Ix - Iy)
        theta_mode = "atan2"

    theta_deg = math.degrees(theta)

    # --- radii of gyration ---
    rx = math.sqrt(Ix / A) if A > 0.0 else 0.0
    ry = math.sqrt(Iy / A) if A > 0.0 else 0.0

    # --- brutal consistency checks ---
    # Eigenvalue invariants for 2x2 inertia tensor:
    # trace = Ix + Iy = I1 + I2
    # det   = Ix*Iy - Ixy^2 = I1*I2
    trace_in = Ix + Iy
    trace_pr = I1 + I2
    det_in = Ix * Iy - Ixy * Ixy
    det_pr = I1 * I2

    # Reconstruction checks (from principal values + theta):
    c = math.cos(theta)
    s = math.sin(theta)
    Ix_rec = I1 * c * c + I2 * s * s
    Iy_rec = I1 * s * s + I2 * c * c
    Ixy_rec = (I2 - I1) * s * c

    # Relative errors (safe denominators)
    def _rel_err(a: float, b: float, floor: float = 1e-30) -> float:
        den = max(abs(a), abs(b), floor)
        return abs(a - b) / den

    e_trace = _rel_err(trace_in, trace_pr)
    e_det = _rel_err(det_in, det_pr)
    e_Ix = _rel_err(Ix, Ix_rec)
    e_Iy = _rel_err(Iy, Iy_rec)
    e_Ixy = _rel_err(Ixy, Ixy_rec)
    e_sym = abs((I1 - I2) - 2.0 * R)  # should be ~0 by definition

    # Branch fingerprint to catch "kinks"
    if abs(Ixy) <= abs(avg) * EPS_K:
        # In near-product-free case, principal values tend toward Ix/Iy ordering
        branch = "Ixy~0"
    else:
        branch = "general"

    if debug:
        print("\n" + "=" * 160)
        print("[DERIVED][INPUT]"
              f" name={sec_name} z={z_here} A={A:+.16e} Ix={Ix:+.16e} Iy={Iy:+.16e} Ixy={Ixy:+.16e}")
        print("[DERIVED][MOHR]"
              f" avg={avg:+.16e} diff={diff:+.16e} R_sq={R_sq:+.16e} R={R:+.16e}")
        print("[DERIVED][PRINCIPAL]"
              f" I1={I1:+.16e} I2={I2:+.16e} (I1-I2)={I1-I2:+.16e} 2R={2.0*R:+.16e} e_sym={e_sym:.3e}")
        print("[DERIVED][THETA]"
              f" mode={theta_mode} theta_rad={theta:+.16e} theta_deg={theta_deg:+.16e}"
              f" iso_thr={iso_thr:+.16e} is_near_isotropic={is_near_isotropic} branch={branch}")
        print("[DERIVED][INVARIANTS]"
              f" trace_in={trace_in:+.16e} trace_pr={trace_pr:+.16e} e_trace={e_trace:.3e} |"
              f" det_in={det_in:+.16e} det_pr={det_pr:+.16e} e_det={e_det:.3e}")
        print("[DERIVED][RECON]"
              f" Ix_rec={Ix_rec:+.16e} e_Ix={e_Ix:.3e} |"
              f" Iy_rec={Iy_rec:+.16e} e_Iy={e_Iy:.3e} |"
              f" Ixy_rec={Ixy_rec:+.16e} e_Ixy={e_Ixy:.3e}")
        print("[DERIVED][GYRATION]"
              f" rx={rx:+.16e} ry={ry:+.16e}")
        print("=" * 160)

    return {
        'I1': I1,                      # Major principal moment of inertia
        'I2': I2,                      # Minor principal moment of inertia
        'theta_rad': theta,
        'theta_deg': theta_deg,
        'rx': rx,
        'ry': ry,
    }



def section_derived_properties(props: Dict[str, float]) -> Dict[str, float]:
    """
    Computes derived structural properties including principal moments of inertia,
    principal axis rotation, and radius of gyration.
    """
    Ix = props['Ix']
    Iy = props['Iy']
    Ixy = props['Ixy']

    # Calculate Mohr's Circle parameters
    avg = (Ix + Iy) / 2
    diff = (Ix - Iy) / 2
    # R is the radius of Mohr's Circle: R = sqrt(((Ix - Iy)/2)^2 + Ixy^2)
    R = math.sqrt(diff**2 + Ixy**2)

    # --- NUMERICAL STABILITY & ISOTROPY CHECK ---
    # For perfectly symmetric sections (like circles or squares), Ix = Iy and Ixy = 0.
    # This creates a mathematical singularity where the principal angle is indeterminate
    # (Mohr's Circle collapses to a single point). 
    # To prevent numerical noise from producing erratic rotation angles,
    # we detect if the radius R is negligible compared to the magnitude of inertia.
    # If isotropic, the principal angle is set to 0.0 by engineering convention.
    if R < abs(avg) * EPS_K: 
        theta = 0.0
    else:
        # Standard calculation for the angle of the principal X-axis
        theta = 0.5 * math.atan2(-2 * Ixy, Ix - Iy)
    # --------------------------------------------

    return {
        'I1': avg + R,  # Major principal moment of inertia
        'I2': avg - R,  # Minor principal moment of inertia
        'theta_rad': theta,
        'theta_deg': math.degrees(theta),
        'rx': math.sqrt(Ix / props['A']) if props['A'] > 0 else 0,
        'ry': math.sqrt(Iy / props['A']) if props['A'] > 0 else 0,
    }


# -------------------------
# Stiffness Matrix Calculation
# -------------------------

def section_stiffness_matrix(section: Section, E_ref: float = 1.0) -> np.ndarray:
    """
 Assembles the 3x3 constitutive stiffness matrix relating generalized 
    strains to internal forces (N, Mx, My).

    TECHNICAL SUMMARY:
    This function performs a numerical integration over the composite 
    polygonal domain to compute the sectional stiffness properties relative 
    to the global origin (0,0). It accounts for multi-material homogenization 
    via the polygon weighting system.

    STIFFNESS MATRIX FORMULATION:
    The resulting matrix K maps the axial strain (epsilon) and curvatures 
    (kappa_x, kappa_y) to the Resultant Normal Force (N) and Bending Moments (Mx, My):
    
        [ N  ]   [ EA    ESx   -ESy  ] [ epsilon ]
        [ Mx ] = [ ESx   EIxx  -EIxy ] [ kappa_x ]
        [ My ]   [ -ESy -EIxy   EIyy ] [ kappa_y ]

    COMPUTATIONAL STRATEGY:
    1. Fan Triangulation: 
       Each polygon is decomposed into triangles using a "fan" approach, 
       with the first vertex (v0) acting as the common pivot.
       
    2. Numerical Integration (Gauss Quadrature):
       For each triangular sub-domain, the function calls the Gaussian 
       integrator to retrieve optimal sampling points.
       
    3. Contribution Mapping:
       At each Gauss point (x, y) with differential area dA:
       - Axial Stiffness (EA): Σ E * dA
       - First Moments (ESx, ESy): Σ E * y * dA and Σ E * x * dA
       - Second Moments (EIxx, EIyy, EIxy): Σ E * y^2 * dA, Σ E * x^2 * dA, 
         and Σ E * x * y * dA.

    4. Homogenization:
       The 'poly.weight' parameter scales the reference Young's Modulus (E_ref), 
       allowing for the modeling of hollow sections (negative weights) or 
       composite structures with varying material stiffness.

    5. Symmetrization:
       Enforces the Maxwell-Betti reciprocal theorem by ensuring K[i,j] = K[j,i].

    RETURNS:
       A 3x3 NumPy array representing the cross-sectional stiffness tensor.   
    """
    # 1. Get exact geometric properties (already multiplied by interpolated weight)
    props = section_properties(section)
    
    area = props['A']
    # If Sx/Sy are not explicitly in props, they are computed from Area * Centroid
    sx = props.get('Sx', area * props['Cy'])
    sy = props.get('Sy', area * props['Cx'])
    
    # 2. Build the 3x3 matrix weighted by E_ref
    # Since 'area', 'Ix', etc. already include 'weight', 
    # E_ref acts as the global Young's Modulus scale.
    k_matrix = np.array([
        [E_ref * area,         E_ref * sy,           -E_ref * sx],
        [E_ref * sy,           E_ref * props['Iy'],  -E_ref * props['Ixy']],
        [-E_ref * sx,         -E_ref * props['Ixy'],  E_ref * props['Ix']]
    ])
    
    return k_matrix



def _segments_intersect(p1, p2, p3, p4) -> bool:
    '''
    Determines if two finite line segments (p1-p2 and p3-p4) intersect in a 2D plane.

    TECHNICAL SUMMARY:
    This function implements a robust geometric intersection test based on the 
    'Orientation Test' (cross-product method). It is primarily used to detect 
    self-intersections in homogenized polygons, ensuring the topological integrity 
    of the cross-sectional boundaries.

    MATHEMATICAL FORMULATION:
    1. Orientation Primitive:
       The inner 'orient' function computes the signed area of the triangle formed 
       by points (a, b, c). 
       - If Result > 0: The sequence (a, b, c) is Counter-Clockwise (CCW).
       - If Result < 0: The sequence is Clockwise (CW).
       - If Result = 0: The points are Collinear.

    2. Relative Orientation Logic:
       For two segments to intersect, the endpoints of each segment must lie on 
       opposite sides of the line defined by the other segment.
       - o1, o2 check points p3 and p4 relative to line p1-p2.
       - o3, o4 check points p1 and p2 relative to line p3-p4.

    3. Intersection Criterion:
       The condition (o1 * o2 < 0) and (o3 * o4 < 0) identifies a 'Proper Intersection'.
       This occurs when the endpoints strictly straddle the opposing lines, 
       excluding collinear overlaps or shared endpoints to maintain computational 
       stability during polygon validation.

    APPLICABILITY IN RULED SURFACE MODELING:
    By preventing self-intersecting polygons, this function ensures that the 
    Shoelace formula and Gaussian integration yield physically consistent results 
    for the area and inertia of the tower sections.

    RETURNS:
       - True: If segments p1-p2 and p3-p4 intersect.
       - False: Otherwise.

    '''

    def orient(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)

    return (o1 * o2 < 0) and (o3 * o4 < 0)





def polygon_has_self_intersections(poly: Polygon) -> bool:
    """
    Returns True if the polygon has any self-intersection between NON-adjacent edges.

    This version is *robust*:
    - Detects proper crossings (X-shaped intersections)
    - Also detects "touching" (vertex on edge) and collinear overlaps

    Why this matters:
    - Your current _segments_intersect() uses a strict test (o1*o2 < 0 and o3*o4 < 0),
        which will NOT flag touching or collinear overlap. :contentReference[oaicite:1]{index=1}
    - For ruled-surface interpolation across z, "touching" can appear due to numerical
        noise or twisting, and you typically want a warning.

    Input model:
    - poly.vertices: Tuple[Pt, ...]
    - Pt has fields .x, .y
    """
    verts = poly.vertices
    n = len(verts)

    # Triangles cannot self-intersect (excluding degeneracy, which you already validate elsewhere).
    if n < 4:
        return False

    eps = EPS_L  # Use your global linear tolerance

    # ---------- Local geometric primitives (kept inside function; no extra global funcs) ----------

    def _orient(a: Pt, b: Pt, c: Pt) -> float:
        """Signed area*2 of triangle (a,b,c)."""
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    def _sign(x: float) -> int:
        """Map x to {-1,0,+1} using eps."""
        if x > eps:
            return 1
        if x < -eps:
            return -1
        return 0

    def _on_segment(a: Pt, b: Pt, p: Pt) -> bool:
        """
        Return True if p lies on segment ab (including endpoints), assuming collinearity
        (or near-collinearity) has already been established.
        """
        return (
            min(a.x, b.x) - eps <= p.x <= max(a.x, b.x) + eps
            and min(a.y, b.y) - eps <= p.y <= max(a.y, b.y) + eps
        )

    def _segments_intersect_robust(a1: Pt, a2: Pt, b1: Pt, b2: Pt) -> bool:
        """
        Robust 2D segment intersection test:
        - Proper intersection (strict crossing)
        - Touching at endpoints / vertex-on-edge
        - Collinear overlap
        """
        o1 = _sign(_orient(a1, a2, b1))
        o2 = _sign(_orient(a1, a2, b2))
        o3 = _sign(_orient(b1, b2, a1))
        o4 = _sign(_orient(b1, b2, a2))

        # Proper crossing (strict)
        if o1 * o2 < 0 and o3 * o4 < 0:
            return True

        # Touching / collinear cases
        if o1 == 0 and _on_segment(a1, a2, b1):
            return True
        if o2 == 0 and _on_segment(a1, a2, b2):
            return True
        if o3 == 0 and _on_segment(b1, b2, a1):
            return True
        if o4 == 0 and _on_segment(b1, b2, a2):
            return True

        return False

    # ---------- Edge pair scanning ----------
    # Edge i: verts[i] -> verts[(i+1)%n]
    # Compare only with non-adjacent edges to avoid trivial shared-vertex "intersections".
    for i in range(n):
        a1 = verts[i]
        a2 = verts[(i + 1) % n]

        # j starts at i+2 to skip the adjacent edge (i+1).
        for j in range(i + 2, n):
            # Skip the edge that shares the closing vertex with edge i
            # (i=0 edge is adjacent to the last edge).
            if (j + 1) % n == i:
                continue

            b1 = verts[j]
            b2 = verts[(j + 1) % n]

            if _segments_intersect_robust(a1, a2, b1, b2):
                return True

    return False



class CSFError(ValueError):
    
    pass




# -------------------------
# Geometry primitives
# -------------------------

@dataclass(frozen=True)
class Pt:
    x: float
    y: float

    def lerp(self, other: "Pt", z_real: float, length: float) -> "Pt": 
            """
            Calculates the interpolated point at a specific distance using slopes.
            
            Args:
                self start point
                other (Pt): Ending point (top).
                z_real (float): relative Distance from the starting point (0 to length).
                length (float): Total vertical length of the segment.
            """
         
            # Avoid division by zero
            if abs(length) < EPS_L:
                return self

            # 1. Calculate the geometric slope (how much x and y change per meter)
            slope_x = (other.x - self.x) / length
            slope_y = (other.y - self.y) / length

            # 2. Add the change to the initial x and y coordinates
            # New = Initial + (Rate of change * distance)
            xr = self.x + (slope_x * z_real)
            yr = self.y + (slope_y * z_real) 
            
            return Pt( 
                x = xr, 
                y = yr  
            )

@dataclass(frozen=True)
class Polygon:
    vertices: Tuple[Pt, ...]
    weight: float = 1.0   # Homogenization coefficient, can be negative for holes
    name: str = ""        # Optional label / ID

    def __post_init__(self) -> None:
        """
        Validation steps executed automatically after object initialization.
        """
        # 1. Check for minimum number of vertices
        if len(self.vertices) < 3:
            raise ValueError(f"Polygon '{self.name}' must have at least 3 vertices.")

        # 2. Check for Counter-Clockwise (CCW) orientation
        # We use the Shoelace formula to calculate the signed area (a2).
        # A positive result indicates CCW, a negative result indicates CW.
        verts = self.vertices
        n = len(verts)
        a2 = 0.0
        for i in range(n):
            x0, y0 = verts[i].x, verts[i].y
            x1, y1 = verts[(i + 1) % n].x, verts[(i + 1) % n].y
            a2 += (x0 * y1 - x1 * y0)
        
        # If a2 is negative, the winding order is Clockwise (CW).
        if a2 <= 0:
            raise ValueError(
                f"GEOMETRIC ERROR: Polygon '{self.name}' has area {a2}. "
                f"Polygons must have a positive area and be defined in Counter-Clockwise (CCW) order. "
                f"An area of 0 means the polygon is degenerate (e.g., only 2 sides)."
            )
        
        if abs(a2) < EPS_A: # Check if the area is practically zero
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' has zero area (degenerate polygon). "
                    f"A polygon must have at least 3 non-collinear vertices (it cannot have only 2 sides)."
                )        
        # GEOMETRIC INTEGRITY CHECK
        if a2 < EPS_A:  # Covers both negative area and zero area
            if a2 < 0:
                # Case: Clockwise (CW) order
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' is defined in Clockwise (CW) order. "
                    f"All polygons must be Counter-Clockwise (CCW). "
                    f"Use weight={self.weight} for voids instead of flipping vertices."
                )
            else:
                # Case: Zero Area (2 sides or collinear points)
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' has zero area (degenerate). "
                    f"A polygon must have at least 3 non-collinear vertices to enclose an area."
                )


@dataclass(frozen=True)
class Section:
    polygons: Tuple[Polygon, ...]
    z: float

    def __post_init__(self):

        seen_names = set()
        for i, poly in enumerate(self.polygons):
            # 1. Check for empty or whitespace-only names
            if not poly.name or not poly.name.strip():
                raise ValueError(
                    f"VALIDATION ERROR: Polygon at index {i} in section at Z={self.z} "
                    f"has an empty or invalid name. All polygons must have a unique name."
                )
            
            # 2. Check for uniqueness
            if poly.name in seen_names:
                raise ValueError(
                    f"VALIDATION ERROR: Duplicate polygon name '{poly.name}' detected "
                    f"in section at Z={self.z}. Each polygon within a section must have a unique name."
                )
            
            seen_names.add(poly.name)

        # Common error case: (poly) instead of (poly,)
        if isinstance(self.polygons, Polygon):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon. "
                "For a single polygon, use (poly,) not (poly)."
            )

        if not isinstance(self.polygons, tuple):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon."
            )

        if len(self.polygons) == 0:
            raise ValueError(
                "Section must contain at least one Polygon."
            )

        for p in self.polygons:
            if not isinstance(p, Polygon):
                raise TypeError(
                    "All elements of Section.polygons must be Polygon."
                )



def poly_from_string(s: str, weight: float = 1.0, name: str = "") -> Polygon:
    """
    Utility: build a Polygon from a string like:
      "-0.5,-0.5  0.5,-0.5  0.5,0.5  -0.5,0.5"
    """
    pts = []
    for token in s.split():
        x_str, y_str = token.split(",")
        pts.append(Pt(float(x_str), float(y_str)))
    return Polygon(vertices=tuple(pts), weight=weight, name=name)

'''
def get_points_distance(polygon: Polygon, i: int, j: int) -> float:
    """
    Calculates the Euclidean distance between vertex i and vertex j of a polygon.
    Indices i and j are 1-based (from 1 to N).
    
    This can measure sides (if i, j are consecutive) or diagonals/distances 
    between any two nodes of the polygon.
    """
    verts = polygon.vertices
    n = len(verts)

    # Validate indices to prevent Out of Range errors
    if not (1 <= i <= n) or not (1 <= j <= n):
        raise IndexError(f"Vertex indices {i, j} out of range for polygon with {n} vertices.")

    # Convert 1-based indices to 0-based for Python list access
    p1 = verts[i - 1]
    p2 = verts[j - 1]

    # Euclidean distance formula: sqrt((x2-x1)^2 + (y2-y1)^2)
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
'''



def get_points_distance(polygon: Polygon, i: int, j: int) -> float:
    """
    Calculates the Euclidean distance between vertex i and vertex j of a polygon.
    Indices i and j are 1-based (from 1 to N).
    
    This can measure sides (if i, j are consecutive) or diagonals/distances 
    between any two nodes of the polygon.
    """
    verts = polygon.vertices
    n = len(verts)

    # Validate indices to prevent Out of Range errors
    if not (1 <= i <= n) or not (1 <= j <= n):
        raise IndexError(f"Vertex indices {i, j} out of range for polygon with {n} vertices.")

    # Convert 1-based indices to 0-based for Python list access
    p1 = verts[i - 1]
    p2 = verts[j - 1]

    # Euclidean distance formula: sqrt((x2-x1)^2 + (y2-y1)^2)
    dist = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
    
    return dist

# -------------------------
# Core: Continuous section field (geometry-only)
# -------------------------
def get_edge_length(polygon: Polygon, edge_idx: int) -> float:
    """
    Calculates the length of the j-th edge of a polygon.
    edge_idx is 1-based (1 to N).
    """
    verts = polygon.vertices
    n = len(verts)
    
    # Translate 1-based index to 0-based
    # Edge j connects vertex j-1 to vertex j
    idx1 = (edge_idx - 1) % n
    idx2 = edge_idx % n
    
    p1 = verts[idx1]
    p2 = verts[idx2]
    
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)

##################################################################################################################################



def list_polygons_with_contents(csf: Any, z: float) -> List[Dict[str, Any]]:
    """
    Return a per-polygon list with direct containment at coordinate z.

    Output record fields:
      - idx (int): polygon index in the sampled section ordering at z
      - name (str): polygon name
      - container_name (str | None): immediate container polygon name (or None if root)
      - direct_children (List[str]): polygon names directly contained in this polygon
      - is_container (bool): True if it has direct children

    Notes:
    - Direct children only (no grandchildren).
    - Uses csf.build_direct_children_map(z) for containment; no geometry is recomputed.
    - Validates: unique names at z, and hierarchy references only existing polygons.
    """
    if not isinstance(z, (int, float)):
        raise TypeError(f"z must be a number (float), got {type(z).__name__}")

    sec = csf.section(float(z))
    if sec is None:
        raise ValueError("csf.section(z) returned None (invalid z or failed sampling).")

    polygons = getattr(sec, "polygons", None)
    if polygons is None:
        raise ValueError("Sampled section has no 'polygons' attribute.")
    from collections.abc import Sequence

    # In CSF, polygons may be stored as a tuple for immutability; accept any Sequence.
    # Reject strings/bytes explicitly to avoid treating them as sequences of characters.
    if (not isinstance(polygons, Sequence)) or isinstance(polygons, (str, bytes)):
        raise TypeError(
            f"section.polygons must be a sequence (list/tuple), got {type(polygons).__name__}."
        )

    # Collect polygon names in the section order; enforce uniqueness.
    names: List[str] = []
    seen = set()
    for i, poly in enumerate(polygons):
        name = getattr(poly, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError(f"Polygon at index {i} has no valid string 'name'.")
        if name in seen:
            raise ValueError(f"Duplicate polygon name at z={z}: '{name}'.")
        seen.add(name)
        names.append(name)

    # Direct containment from CSF (parent -> [children]).
    children_map = csf.build_direct_children_map(float(z))
    if children_map is None:
        raise ValueError("build_direct_children_map(z) returned None (expected dict).")
    if not isinstance(children_map, dict):
        raise TypeError(
            f"build_direct_children_map(z) must return dict, got {type(children_map).__name__}."
        )

    # Invert to child -> parent map (one container or none).
    parent_of: Dict[str, str] = {}
    for parent, childs in children_map.items():
        if not isinstance(parent, str) or not parent:
            raise ValueError(f"Invalid parent name in children_map: {parent!r}")
        if parent not in seen:
            raise ValueError(
                f"Hierarchy references parent '{parent}' not present in section at z={z}."
            )
        if not isinstance(childs, list):
            raise TypeError(
                f"children_map['{parent}'] must be a list, got {type(childs).__name__}."
            )
        for child in childs:
            if not isinstance(child, str) or not child:
                raise ValueError(f"Invalid child name under '{parent}': {child!r}")
            if child not in seen:
                raise ValueError(
                    f"Hierarchy references child '{child}' not present in section at z={z}."
                )
            if child in parent_of:
                raise ValueError(
                    f"Polygon '{child}' has multiple containers: '{parent_of[child]}' and '{parent}'."
                )
            parent_of[child] = parent

    # Assemble records in the section ordering.
    out: List[Dict[str, Any]] = []
    for idx, name in enumerate(names):
        direct_children = children_map.get(name, [])
        if direct_children and not isinstance(direct_children, list):
            raise TypeError(f"children_map['{name}'] must be a list.")

        out.append(
            {
                "idx": idx,
                "name": name,
                "container_name": parent_of.get(name),
                "direct_children": list(direct_children),
                "is_container": bool(direct_children),
            }
        )

    return out


def polygon_surface_w1_inners0(self: Any, z: float) -> List[Dict[str, Any]]:
    """
    Args:
        z (float): longitudinal coordinate.

    Returns:
        List[Dict[str, Any]]: one record per polygon with:
          - idx (int)
          - name (str)
          - container_name (str | None)
          - direct_inners (List[str])
          - w (float): effective weight w_eff(p,z)
          - A (float): occupied surface with w(p)=1 and w(inners)=0 (signed)
          - A_w (float): A * w
    """
    if not isinstance(z, (int, float)):
        raise TypeError(f"z must be a number (float), got {type(z).__name__}")
    z = float(z)

    # 1) Hierarchy (direct inners).
    rows = list_polygons_with_contents(self, z)
    if not isinstance(rows, list):
        raise TypeError("list_polygons_with_contents(...) must return a list.")

    container_of: Dict[str, str | None] = {}
    direct_inners_of: Dict[str, List[str]] = {}

    for r in rows:
        if not isinstance(r, dict):
            raise TypeError("list_polygons_with_contents(...) must return list of dicts.")
        name = r.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("Hierarchy row has missing/invalid 'name'.")
        if name in container_of:
            raise ValueError(f"Duplicate polygon name in hierarchy rows at z={z}: '{name}'.")

        container_of[name] = r.get("container_name")  # may be None

        # Helper still uses 'direct_children' internally; we expose 'direct_inners'.
        inners = r.get("direct_children", [])
        if inners and not isinstance(inners, list):
            raise TypeError(f"direct_children for '{name}' must be a list.")
        direct_inners_of[name] = list(inners)

    # 2) Signed areas + relative weights from CSF inspection.
    if not hasattr(self, "inspect_section_entities"):
        raise AttributeError("Expected self.inspect_section_entities(z) to exist.")

    entities = self.inspect_section_entities(z)
    if not isinstance(entities, list):
        raise TypeError("inspect_section_entities(z) must return a list of dict records.")

    area_by_name: Dict[str, float] = {}
    w_rel_by_name: Dict[str, float] = {}

    for e in entities:
        if not isinstance(e, dict):
            raise TypeError("inspect_section_entities(z) must return a list of dict records.")
        name = e.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("inspect_section_entities(z) returned an entity with missing/invalid 'name'.")
        if name in area_by_name:
            raise ValueError(f"Duplicate entity name from inspect_section_entities at z={z}: '{name}'.")

        if "area_signed" not in e:
            raise ValueError(f"Entity '{name}' has no 'area_signed' field.")
        if "weight_at_z" not in e:
            raise ValueError(f"Entity '{name}' has no 'weight_at_z' field.")

        area_by_name[name] = float(e["area_signed"])
        
        w_rel_by_name[name] = float(e["weight_at_z"])
        
    # Ensure hierarchy names exist in inspection.
    for name in container_of:
        if name not in area_by_name:
            raise ValueError(
                f"Polygon '{name}' is in hierarchy but missing from inspect_section_entities at z={z}."
            )

    # 3) Reconstruct effective weights (w_eff) from the immediate-container chain.
    w_eff_by_name: Dict[str, float] = {}

    # Initialize roots (no container).
    for name, parent in container_of.items():
        if parent is None:
            w_eff_by_name[name] = w_rel_by_name[name]

    unresolved = set(container_of.keys()) - set(w_eff_by_name.keys())
    progress = True
    while unresolved and progress:
        progress = False
        for name in list(unresolved):
            parent = container_of[name]
            if parent is None:
                w_eff_by_name[name] = w_rel_by_name[name]
                unresolved.remove(name)
                progress = True
                continue
            if parent not in w_eff_by_name:
                continue
            w_eff_by_name[name] = w_rel_by_name[name] + w_eff_by_name[parent]
            unresolved.remove(name)
            progress = True

    if unresolved:
        missing = {name: container_of[name] for name in unresolved}
        raise ValueError(f"Cannot resolve effective weights (cycle or missing container): {missing}")

    # 4) Compute A and A*w for each polygon (local rule: w(p)=1, w(inners)=0).
    out: List[Dict[str, Any]] = []
    for r in rows:
        name = r["name"]
        inners = direct_inners_of.get(name, [])
        area_p = area_by_name[name]

        inners_sum = 0.0
        for inner_name in inners:
            if inner_name not in area_by_name:
                raise ValueError(f"Inner polygon '{inner_name}' missing from inspection at z={z}.")
            inners_sum += area_by_name[inner_name]

        A = area_p - inners_sum
        w_eff = w_eff_by_name[name]
        #print(f"DEBUG { ["idx"]} name {name} {area_by_name[name]} {w_rel_by_name[name]}: {float(w_eff)} : {float(A)} inners_sum: {inners_sum}")
        out.append(
            {
                "idx": int(r["idx"]),
                "name": name,
                "container_name": r.get("container_name"),
                "direct_inners": list(inners),
                "w": float(w_eff),
                "A": float(A),
                "A_w": float(A * w_eff),
            }
        )

    return out


def polygon_surface_w1_inners0_single(self: Any, z: float, idx: int) -> Dict[str, Any]:
    """
    Compute the *net occupied surface* for ONE polygon at coordinate z, using the local rule:
      - w(polygon) = 1
      - w(direct inners) = 0

    And its weighted counterpart:
      - A_w = A_net * w_eff(z)

    This is a specialized version of polygon_surface_w1_inners0(...):
    it reproduces the SAME math, but only for the requested polygon idx, avoiding
    computing A/A_w for every polygon when you only need one.

    Inputs:
        z   : longitudinal coordinate (absolute).
        idx : polygon index (0-based).

    Returns:
        Dict[str, Any] with:
          - idx (int)
          - name (str)
          - container_name (str | None)
          - direct_inners (List[str])
          - w (float): effective weight w_eff(p,z)
          - A (float): occupied surface with w(p)=1 and w(inners)=0 (signed)
          - A_w (float): A * w
    """
    # -------------------------------------------------------------------------
    # 0) Basic validation
    # -------------------------------------------------------------------------
    if not isinstance(z, (int, float)):
        raise TypeError(f"z must be a number (float), got {type(z).__name__}")
    z = float(z)

    if not isinstance(idx, int):
        raise TypeError(f"idx must be an int (0-based), got {type(idx).__name__}")
    if idx < 0:
        raise ValueError(f"idx must be >= 0 (0-based), got {idx}")

    # -------------------------------------------------------------------------
    # 1) Hierarchy at z: for the target polygon we need:
    #    - its container (possibly None for root)
    #    - its direct inners (names)
    #    For w_eff we also need the container chain up to the root.
    # -------------------------------------------------------------------------
    rows = list_polygons_with_contents(self, z)
    if not isinstance(rows, list):
        raise TypeError("list_polygons_with_contents(...) must return a list.")

    # Build name -> container_name map (needed to walk the container chain for w_eff).
    container_of: Dict[str, str | None] = {}

    target_row: Dict[str, Any] | None = None
    for r in rows:
        if not isinstance(r, dict):
            raise TypeError("list_polygons_with_contents(...) must return list of dicts.")

        name = r.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("Hierarchy row has missing/invalid 'name'.")
        if name in container_of:
            raise ValueError(f"Duplicate polygon name in hierarchy rows at z={z}: '{name}'.")

        container_of[name] = r.get("container_name")  # may be None

        # Identify the target polygon by idx (0-based).
        if "idx" not in r:
            raise ValueError("Hierarchy row missing required 'idx' field.")
        if int(r["idx"]) == idx:
            target_row = r

    if target_row is None:
        raise ValueError(f"Polygon idx={idx} not found in hierarchy rows at z={z}.")

    target_name = target_row.get("name")
    if not isinstance(target_name, str) or not target_name:
        raise ValueError(f"Target polygon idx={idx} has missing/invalid 'name' at z={z}.")

    # Expose "direct_inners" but hierarchy helper still uses "direct_children".
    inners = target_row.get("direct_children", [])
    if inners and not isinstance(inners, list):
        raise TypeError(f"direct_children for '{target_name}' must be a list.")
    direct_inners = list(inners)

    container_name = target_row.get("container_name")  # may be None

    # -------------------------------------------------------------------------
    # 2) Signed areas + relative weights at z (single point of truth):
    #    We rely on inspect_section_entities(z) which must provide:
    #      - area_signed (signed geometric area)
    #      - weight_at_z (relative weight: W_rel = W_abs(child) - W_abs(container))
    # -------------------------------------------------------------------------
    if not hasattr(self, "inspect_section_entities"):
        raise AttributeError("Expected self.inspect_section_entities(z) to exist.")

    entities = self.inspect_section_entities(z)
    if not isinstance(entities, list):
        raise TypeError("inspect_section_entities(z) must return a list of dict records.")

    area_by_name: Dict[str, float] = {}
    w_rel_by_name: Dict[str, float] = {}

    for e in entities:
        if not isinstance(e, dict):
            raise TypeError("inspect_section_entities(z) must return a list of dict records.")
        name = e.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("inspect_section_entities(z) returned an entity with missing/invalid 'name'.")
        if name in area_by_name:
            raise ValueError(f"Duplicate entity name from inspect_section_entities at z={z}: '{name}'.")

        if "area_signed" not in e:
            raise ValueError(f"Entity '{name}' has no 'area_signed' field.")
        if "weight_at_z" not in e:
            raise ValueError(f"Entity '{name}' has no 'weight_at_z' field.")

        area_by_name[name] = float(e["area_signed"])
        w_rel_by_name[name] = float(e["weight_at_z"])

    # Ensure the target polygon exists in inspection.
    if target_name not in area_by_name:
        raise ValueError(
            f"Polygon '{target_name}' (idx={idx}) is in hierarchy but missing from inspect_section_entities at z={z}."
        )

    # Ensure inners exist in inspection.
    for inner_name in direct_inners:
        if inner_name not in area_by_name:
            raise ValueError(f"Inner polygon '{inner_name}' missing from inspection at z={z}.")

    # -------------------------------------------------------------------------
    # 3) Reconstruct effective weight w_eff for the target polygon only:
    #    w_eff(target) = w_rel(target) + w_rel(parent) + ... + w_rel(root)
    #    (root has container=None).
    # -------------------------------------------------------------------------
    w_eff = 0.0
    cur = target_name
    visited: set[str] = set()

    while True:
        if cur in visited:
            raise ValueError(f"Cannot resolve effective weight: cycle detected in container chain at z={z}: {cur}")
        visited.add(cur)

        if cur not in w_rel_by_name:
            raise ValueError(f"Polygon '{cur}' missing 'weight_at_z' in inspection at z={z}.")
        w_eff += w_rel_by_name[cur]

        parent = container_of.get(cur)
        if parent is None:
            break
        if parent not in container_of:
            raise ValueError(f"Container '{parent}' for polygon '{cur}' missing from hierarchy rows at z={z}.")
        cur = parent

    # -------------------------------------------------------------------------
    # 4) Compute net occupied surface A and the weighted A_w for the target polygon:
    #    A = area(target) - sum(area(direct_inners))
    # -------------------------------------------------------------------------
    area_p = area_by_name[target_name]
    inners_sum = 0.0
    for inner_name in direct_inners:
        inners_sum += area_by_name[inner_name]

    A = area_p - inners_sum
    A_w = A * w_eff

    return {
        "idx": int(idx),
        "name": target_name,
        "container_name": container_name,
        "direct_inners": direct_inners,
        "w": float(w_eff),
        "A": float(A),
        "A_w": float(A_w),
    }



##################################################################################################################################



class ContinuousSectionField:

    

    def inspect_section_entities(self, z: float) -> List[Dict[str, Any]]:
        """
        Performs a sterile, comprehensive inspection of all polygonal entities at a 
        specific longitudinal coordinate z, including parent-child relationships.
        
        This function discloses the complete genealogy and mechanical state of each 
        polygon. For each entity, it reports both its descendants (if any) and its 
        ancestor (the immediate container).
        
        Fields returned include:
        - Positional data (idx, name)
        - Endpoint references (s0_name, s1_name, s0_weight, s1_weight)
        - Interpolated state (weight_at_z, weight_law)
        - Geometric property (area_signed, unaltered)
        - Descendant info (is_container, direct_children)
        - Ancestor info (container_idx, container_name) <-- NEW
        
        Args:
            z (float): Longitudinal coordinate for section sampling.
                    
        Returns:
            List[Dict[str, Any]]: List of entity records with fields:
            
            - idx (int): Position in section at z.
            - name (str): Polygon identifier.
            - s0_name, s1_name (str): Endpoint polygon names.
            - s0_weight, s1_weight (float): Reference weights at ends.
            - weight_at_z (float): Interpolated weight at z.
            - weight_law (str | None): Weight law formula string.
            - area_signed (float): Raw geometric area (shoelace, signed).
            - is_container (bool): True if this polygon has children.
            - direct_children (List[str]): Names of contained polygons.
            - container_idx (int | None): Index of parent polygon (if nested).
            - container_name (str | None): Name of parent polygon (if nested).
        """
        # --- 1) Sample section and get hierarchy ---
        sec = self.section(z)
        children_map = self.build_direct_children_map(z)
        
        # --- 2) Build child -> parent inverse mapping ---
        # children_map is {parent_name: [child1, child2, ...]}
        # We invert it to {child_name: parent_name} for O(1) lookup
        parent_of: Dict[str, str] = {}
        for parent_name, child_list in children_map.items():
            for child_name in child_list:
                parent_of[child_name] = parent_name
        
        # --- 3) Pre-compute name -> index mapping for current section ---
        # This allows us to find the container's index quickly
        name_to_idx: Dict[str, int] = {
            getattr(poly, "name", f"unnamed_{i}"): i 
            for i, poly in enumerate(sec.polygons)
        }
        
        # --- 4) Compile records ---
        records = []
        
        for idx, poly in enumerate(sec.polygons):
            name = getattr(poly, "name", f"unnamed_{idx}")
            weight_at_z = float(getattr(poly, "weight", 0.0))
            
            # Endpoint data
            s0_poly = self.s0.polygons[idx]
            s1_poly = self.s1.polygons[idx]
            s0_name = getattr(s0_poly, "name", name)
            s1_name = getattr(s1_poly, "name", name)
            s0_weight = float(getattr(s0_poly, "weight", 0.0))
            s1_weight = float(getattr(s1_poly, "weight", 0.0))
            
            # Weight law
            weight_law = None
            if self.weight_laws is not None:
                if (idx + 1) in self.weight_laws:
                    weight_law = str(self.weight_laws[idx + 1])
                elif name in self.weight_laws:
                    weight_law = str(self.weight_laws[name])
            '''
            # Geometric area (sterile, signed)
            verts = poly.vertices
            n = len(verts)
            shoelace = sum(
                float(verts[i].x) * float(verts[(i+1)%n].y) - 
                float(verts[(i+1)%n].x) * float(verts[i].y)
                for i in range(n)
            )
            area_signed = 0.5 * shoelace
            '''
            area_signed, _ = _polygon_signed_area_and_centroid(poly)

            
            # Hierarchy: Descendants (am I a container?)
            is_container = name in children_map
            direct_children = children_map.get(name, [])
            
            # Hierarchy: Ancestor (do I have a container?)
            container_name = parent_of.get(name)  # Returns None if not present (outermost)
            container_idx = name_to_idx.get(container_name) if container_name else None
            
            records.append({
                "idx": idx,
                "name": name,
                "s0_name": s0_name,
                "s1_name": s1_name,
                "s0_weight": s0_weight,
                "s1_weight": s1_weight,
                "weight_at_z": weight_at_z,
                "weight_law": weight_law,
                "area_signed": area_signed,
                "is_container": is_container,
                "direct_children": direct_children,
                "container_idx": container_idx,      # <-- NEW
                "container_name": container_name     # <-- NEW
            })
        
        return records


    def build_direct_children_map(self, z: float) -> Dict[str, List[str]]:
        """
        Builds a direct parent-to-children mapping for polygons at a given z-section.
        
        This function analyzes the containment hierarchy at section coordinate `z` 
        and returns a mapping where each parent polygon is associated with its 
        immediate (direct) children only. This excludes nested descendants 
        (grandchildren are not listed under grandparents).
        
        The hierarchy is determined from the stable S0 section topology and applied 
        to the section at `z` via polygon names.
        
        Args:
            z: Longitudinal coordinate where to sample the section.
            
        Returns:
            Dict[str, List[str]]: A dictionary mapping parent polygon names to 
            a list of their direct children names. 
            
            Example:
            {
                "outer_flange": ["web", "hole_1"],
                "web": ["inner_cutout"]  # Only direct child, not grandchildren
            }
            
            Polygons with no children will not appear as keys in the dictionary.
            
        Raises:
            ValueError: If polygon names are missing, empty, or duplicated.
            CSFError: If section at z cannot be computed.
        """
        # --- 1) Validate section at z (ensures coordinate is valid) ---
        sec = self.section(z)
        
        # --- 2) Build stable name mapping from S0 ---
        s0_polys = self.s0.polygons
        if not s0_polys:
            return {}
        
        s0_names: List[str] = []
        seen_names = set()
        
        for poly in s0_polys:
            name = getattr(poly, "name", None)
            if not name:
                raise ValueError(
                    f"Polygon at index {len(s0_names)} in S0 has no name. "
                    f"All polygons must have unique names."
                )
            if name in seen_names:
                raise ValueError(f"Duplicate polygon name in S0: '{name}'")
            seen_names.add(name)
            s0_names.append(name)
        
        # --- 3) Determine immediate container for each polygon (child -> parent) ---
        container_of: Dict[str, Optional[str]] = {}
        
        for idx, poly in enumerate(s0_polys):
            child_name = s0_names[idx]
            parent_idx = self.get_container_polygon_index(poly, idx)
            
            # Safety: prevent self-containment loops
            if parent_idx == idx:
                parent_idx = None
                
            if parent_idx is None:
                parent_name = None
            else:
                if not (0 <= parent_idx < len(s0_polys)):
                    raise ValueError(
                        f"Invalid container index {parent_idx} returned for "
                        f"polygon '{child_name}'"
                    )
                parent_name = s0_names[parent_idx]
                # Defensive: name-level self-containment check
                if parent_name == child_name:
                    parent_name = None
                    
            container_of[child_name] = parent_name
        
        # --- 4) Invert mapping: parent -> list of direct children ---
        children_map: Dict[str, List[str]] = {}
        
        for child_name, parent_name in container_of.items():
            if parent_name is not None:
                if parent_name not in children_map:
                    children_map[parent_name] = []
                children_map[parent_name].append(child_name)
        
        return children_map






    def get_container_polygon_index(self, poly: "Polygon", i: int):
        """
        Return the index (0-based) of the *immediate container* of `poly` in self.s0.polygons.
        Returns the index of the immediate container polygon (smallest-area polygon that contains `poly`),
        not the outermost/global container.
        Logic (as requested):
        1) Take polygon p (= poly).
        2) Collect all other polygons that contain p.
        3) Pick pp such that pp contains p and there is no other polygon between them
            (i.e., no q with p ⊂ q ⊂ pp). Polygons may touch (boundary counts as inside).

        Debug:
        - Enable with: self.debug_container = True
        - No global variables are used to activate debug output.

        Returns
        -------
        int | None
            Index of the immediate container polygon, or None if no container exists.
        """
        debug = bool(getattr(self, "debug_container", False))

        def _dbg(msg: str) -> None:
            if debug:
                print(msg)

        polys = self.s0.polygons
        n_polys = len(polys)

        # Find the index of the same polygon in self.s0.polygons robustly.
        # We only trust 'i' if it points to the same name; otherwise we search by name.
        self_idx = None
        poly_name = getattr(poly, "name", None)

        if 0 <= i < n_polys and getattr(polys[i], "name", None) == poly_name:
            self_idx = i
        else:
            if poly_name is not None:
                for k, p in enumerate(polys):
                    if getattr(p, "name", None) == poly_name:
                        self_idx = k
                        break
            _dbg(f"[get_container_polygon_index] index mismatch: given i={i}, inferred self_idx={self_idx}, name={poly_name!r}")

        # Linear tolerance (allow per-instance override, fallback to module default)
        eps_l = float(getattr(self, "eps_l", EPS_L))
        eps_a = eps_l * eps_l  # area-like tolerance derived from eps_l

        def _strip_closure(verts):
            # If polygon is explicitly closed (last == first), drop last vertex.
            if len(verts) >= 2 and verts[0] == verts[-1]:
                return verts[:-1]
            return verts

        def _area_abs(verts) -> float:
            # Shoelace area magnitude.
            a2 = 0.0
            n = len(verts)
            for k in range(n):
                x0, y0 = verts[k].x, verts[k].y
                x1, y1 = verts[(k + 1) % n].x, verts[(k + 1) % n].y
                a2 += (x0 * y1 - x1 * y0)
            return abs(0.5 * a2)

        def _bbox(verts):
            xs = [v.x for v in verts]
            ys = [v.y for v in verts]
            return (min(xs), min(ys), max(xs), max(ys))

        def _bbox_contains(b_out, b_in) -> bool:
            # Inclusive bbox containment with tolerance.
            ox0, oy0, ox1, oy1 = b_out
            ix0, iy0, ix1, iy1 = b_in
            return (ox0 <= ix0 + eps_l and oy0 <= iy0 + eps_l and
                    ox1 >= ix1 - eps_l and oy1 >= iy1 - eps_l)

        def _point_on_segment(px, py, ax, ay, bx, by) -> bool:
            # Robust "point on segment" with degenerate segment handling.
            abx, aby = (bx - ax), (by - ay)
            apx, apy = (px - ax), (py - ay)
            ab2 = abx * abx + aby * aby

            # Degenerate edge -> treat as a point.
            if ab2 <= eps_l * eps_l:
                dx = px - ax
                dy = py - ay
                return (dx * dx + dy * dy) <= eps_l * eps_l

            # Collinearity via cross product.
            cross = abx * apy - aby * apx
            if abs(cross) > eps_l:
                return False

            # Projection check.
            dot = apx * abx + apy * aby
            if dot < -eps_l:
                return False
            if dot > ab2 + eps_l:
                return False
            return True

        def _point_in_poly(px, py, verts) -> bool:
            # Ray casting with boundary inclusion.
            inside = False
            n = len(verts)
            for k in range(n):
                x1, y1 = verts[k].x, verts[k].y
                x2, y2 = verts[(k + 1) % n].x, verts[(k + 1) % n].y

                # On-edge => inside.
                if _point_on_segment(px, py, x1, y1, x2, y2):
                    return True

                # Ray casting toggle.
                if (y1 > py) != (y2 > py):
                    x_int = x1 + (py - y1) * (x2 - x1) / (y2 - y1 + 0.0)
                    if x_int > px:
                        inside = not inside
            return inside

        def _poly_inside(inner_verts, outer_verts) -> bool:
            # Containment: all inner vertices must be inside or on boundary.
            return all(_point_in_poly(v.x, v.y, outer_verts) for v in inner_verts)

        inner_verts = _strip_closure(poly.vertices)
        if len(inner_verts) < 3:
            _dbg("[get_container_polygon_index] inner polygon degenerate (<3 vertices) -> None")
            return None

        a_inner = _area_abs(inner_verts)
        b_inner = _bbox(inner_verts)

        _dbg(f"[get_container_polygon_index] target={poly_name!r} a_inner={a_inner:.16g} bbox={b_inner}")

        # 1) Collect all container candidates of p.
        candidates = []  # list of tuples: (j, a_outer, outer_verts)
        for j, outer in enumerate(polys):
            if self_idx is not None and j == self_idx:
                continue
            if getattr(outer, "name", None) == poly_name:
                continue

            outer_verts = _strip_closure(outer.vertices)
            if len(outer_verts) < 3:
                continue

            # Fast bbox reject.
            if not _bbox_contains(_bbox(outer_verts), b_inner):
                continue

            a_outer = _area_abs(outer_verts)

            # Must be strictly larger (with tolerance).
            if a_outer <= a_inner + eps_a:
                continue

            if _poly_inside(inner_verts, outer_verts):
                candidates.append((j, a_outer, outer_verts))
                _dbg(f"  candidate j={j} name={getattr(outer,'name',None)!r} a_outer={a_outer:.16g}")

        if not candidates:
            _dbg("[get_container_polygon_index] no containers found -> None")
            return None

        # 2) Choose the immediate container:
        #    pp is a container of p such that there is no other container q with p ⊂ q ⊂ pp.
        immediate = []
        for j, a_j, v_j in candidates:
            has_between = False
            for k, a_k, v_k in candidates:
                if k == j:
                    continue
                # q is "between" if it is inside pp and is smaller than pp.
                # Under non-intersection assumptions, this captures nesting.
                if a_k < a_j - eps_a and _poly_inside(v_k, v_j):
                    has_between = True
                    _dbg(f"    reject j={j} because k={k} is between (k inside j)")
                    break
            if not has_between:
                immediate.append((j, a_j))

        if not immediate:
            # This should not happen under the stated assumptions; fall back to smallest-area container.
            best_idx = min(candidates, key=lambda t: t[1])[0]
            _dbg(f"[get_container_polygon_index] no immediate candidate (unexpected). Fallback best_idx={best_idx}")
            return best_idx

        # If multiple immediate candidates exist (should be rare), pick the smallest-area one.
        best_idx, best_area = min(immediate, key=lambda t: t[1])
        _dbg(f"[get_container_polygon_index] result best_idx={best_idx} name={getattr(polys[best_idx],'name',None)!r} a={best_area:.16g}")
        return best_idx



    def write_section(self, z0: float,z1: float, yaml_path: str) -> None:
        """
        Export the computed section at absolute coordinate `z` to a YAML file.

        Parameters
        ----------
        z0, z1: floats
            Absolute coordinates along the CSF axis (same convention used by self.section(z)).
        yaml_path : str
            Output YAML filepath.

        Raises
        ------
        CSFError
            If validation fails, section computation fails, YAML serialization fails,
            or file writing fails.
        """
        # Validate z0 e z1
        z_min, z_max = min(self.s0.z, self.s1.z), max(self.s0.z, self.s1.z)
        if not (z_min <= z0 <= z_max and z_min <= z1 <= z_max):
            bad_zs = [z for z in (z0, z1) if not (z_min <= z <= z_max)]
            raise CSFError(f"write_section: z0/z1 must be in [{z_min}, {z_max}]. Out: {bad_zs!r}")

        if not all(_csf__is_finite_number(z) for z in (z0, z1)):
            bad_zs = [z for z in (z0, z1) if not _csf__is_finite_number(z)]
            raise CSFError(f"write_section: z must be finite number. Got: {bad_zs!r}")

        
        yaml_path = yaml_path.strip()
        _csf__ensure_parent_dir_exists(yaml_path)
       
        # 2) Compute Section at z (includes w(z) logic)
        weight_laws_yaml = []
        secz0 = self.section(float(z0))
        secz1 = self.section(float(z1))
        if self.weight_laws is not None:   
            try:
                secz0 = self.section(float(z0))
                secz1 = self.section(float(z1))  
                for key in self.weight_laws:
                    idx = key - 1
                    
                    namestartlaw = self.s0.polygons[idx].name 
                    nameendlaw   =  self.s0.polygons[idx].name
                    law_string = f"{namestartlaw},{nameendlaw}: {self.weight_laws[key]}"
                    weight_laws_yaml.append(law_string)
            except CSFError:
                raise
            except Exception as e:
                raise CSFError(
                    "write_section: weight_laws_yaml section(z) failed. "
                    f"z={float(z0):.6g}, error={type(e).__name__}: {e}"
                ) from e

        # 3) Build minimal dict
        try:
            datas0 = _csf__section_to_Sz_dict(secz0,"S0")
            datas1 = _csf__section_to_Sz_dict(secz1,"S1")
        except CSFError:
            raise
        except Exception as e:
            raise CSFError(
                "write_section: failed while converting Section -> Sz dict. "
                f"z={float(z1):.6g}, error={type(e).__name__}: {e}"
            ) from e

        # 4) Serialize to YAML (PyYAML if available, otherwise _simple_yaml_dump fallback)
        try:
            if "yaml" in globals() and globals().get("yaml") is not None:
                dumper = globals().get("CSFDumper", None)
                if dumper is None:
                    yml = globals()["yaml"].safe_dump(data, sort_keys=False)  # type: ignore[index]
                else:
                   
                        new_data = {
                            "CSF": {
                                **{
                                    "sections": {
                                        **datas0,
                                        **datas1,
                                    }
                                }
                            }
                        }

                        if len(weight_laws_yaml)>0:  # True if empty
                            new_data["CSF"]["weight_laws"] = weight_laws_yaml

                        yml = globals()["yaml"].dump(  # type: ignore[index]
                        new_data,
                        Dumper=dumper,
                        sort_keys=False,
                        allow_unicode=True,
                        indent=2,
                        default_flow_style=False,
                    )
            else:
                if "_simple_yaml_dump" not in globals() or globals().get("_simple_yaml_dump") is None:
                    raise CSFError(
                        "write_section: YAML backend unavailable. "
                        "Neither PyYAML (yaml) nor _simple_yaml_dump(...) are defined."
                    )
                yml = globals()["_simple_yaml_dump"](data) + "\n"  # type: ignore[index]
        except CSFError:
            raise
        except Exception as e:
            raise CSFError(
                "write_section: YAML serialization failed. "
                f"z={float(z0):.6g}, error={type(e).__name__}: {e}"
            ) from e

        # 5) Atomic write to disk
        try:
            _csf__atomic_write_text(yaml_path, yml)
        except Exception as e:
            raise CSFError(
                f"write_section: could not write YAML file '{yaml_path}'. "
                f"error={type(e).__name__}: {e}"
            ) from e
    # write_section

    @staticmethod
    def _section_to_dict(sec):
        poly_map = {}
        poly_names = [name for name, obj in globals().items() if isinstance(obj, Polygon)]
        for p in sec.polygons:
            key = p.name
            if key in poly_map:
                raise ValueError(f"Duplicate polygon name in section z={sec.z}: '{key}'")
            poly_map[key] = ContinuousSectionField._polygon_to_dict(p)

        return {
            "z": float(sec.z),
            "polygons": poly_map,  # <-- dict, non lista
        }

    @staticmethod
    def _pt_to_xy(pt):
        return [float(pt.x), float(pt.y)]

    @staticmethod
    def _polygon_to_dict(poly):
        if XY is not None:
            verts = [XY((float(v.x), float(v.y))) for v in poly.vertices]
        else:
            verts = [[float(v.x), float(v.y)] for v in poly.vertices]

        return {
            "weight": float(poly.weight),
            "vertices": verts,
        }



    def section_area_by_weight(
        self,
        z: float,
        w_tol: float = 0.0,
        include_per_polygon: bool = False,
        debug: bool = False,
        zero_w_eps: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Compute area breakdown at section z grouped by ABSOLUTE weight (w_abs).
        
        This is a sterile implementation:
        - Polygon areas preserve their signed value from the shoelace formula (no abs).
        - Effective area (material area) is computed as sum(area * w_rel).
        - No data clipping (max(0, ...)) is applied unless explicitly requested.
        
        Args:
            z: Longitudinal coordinate where the section is sampled.
            w_tol: Grouping tolerance for weights. If > 0, weights are rounded to 
                   the nearest multiple of w_tol for grouping purposes only.
            include_per_polygon: If True, includes detailed per-polygon data in output.
            debug: If True, prints debug information to stdout.
            zero_w_eps: Threshold for considering an absolute weight as zero when
                        computing total_area_nonzero. If |w_abs| <= zero_w_eps, 
                        that polygon's contribution is excluded from the nonzero sum.
                        
        Returns:
            Dictionary containing:
            - z: Coordinate (float)
            - total_area: Effective area = sum(area * w_rel) for all polygons
            - total_area_nonzero: Effective area excluding |w_abs| <= zero_w_eps
            - total_area_geometric: Raw geometric sum = sum(area) (sterile, signed)
            - groups: List of weight groups with accumulated geometric areas
            - per_polygon: (Optional) Detailed polygon data
        """
        # --- 1) Sample section at z ---
        sec = self.section(z)

        # --- 2) Geometric helpers (sterile, sign-preserving) ---
        def _extract_vertices(poly) -> List[Tuple[float, float]]:
            """Extract vertices as list of (x, y) tuples."""
            verts = getattr(poly, "vertices", None)
            if verts is None:
                raise ValueError(f"Polygon '{getattr(poly, 'name', None)}' has no vertices.")
            out = []
            for v in verts:
                if isinstance(v, (list, tuple)) and len(v) >= 2:
                    out.append((float(v[0]), float(v[1])))
                else:
                    out.append((float(getattr(v, "x")), float(getattr(v, "y"))))
            return out

        def _signed_area(vertices: List[Tuple[float, float]]) -> float:
            """
            Compute signed area using the shoelace formula.
            Positive for CCW orientation, negative for CW.
            No abs() is applied; the raw signed value is returned.
            """
            n = len(vertices)
            if n < 3:
                return 0.0
            # Handle explicit closure safely (if last == first, modulo handles it)
            cross_sum = 0.0
            for i in range(n):
                x1, y1 = vertices[i]
                x2, y2 = vertices[(i + 1) % n]
                cross_sum += x1 * y2 - x2 * y1
            return 0.5 * cross_sum

        # --- 3) Build container hierarchy from S0 (stable reference) ---
        s0_polys = self.s0.polygons
        if not s0_polys:
            raise ValueError("S0 has no polygons; cannot establish container map.")

        # Map index to name for S0
        s0_names: List[str] = []
        seen_names = set()
        for p in s0_polys:
            nm = getattr(p, "name", None)
            if not nm:
                raise ValueError("All S0 polygons must have a unique name.")
            if nm in seen_names:
                raise ValueError(f"Duplicate polygon name in S0: '{nm}'")
            seen_names.add(nm)
            s0_names.append(nm)

        # Map child_name -> parent_name (None if outermost)
        container_of: Dict[str, Optional[str]] = {}
        for idx, poly in enumerate(s0_polys):
            child_name = s0_names[idx]
            parent_idx = self.get_container_polygon_index(poly, idx)
            
            # Prevent self-containment
            if parent_idx == idx:
                parent_idx = None
                
            if parent_idx is None:
                parent_name = None
            else:
                if not (0 <= parent_idx < len(s0_polys)):
                    raise ValueError(f"Invalid container index {parent_idx} for '{child_name}'")
                parent_name = s0_names[parent_idx]
                if parent_name == child_name:
                    parent_name = None
            container_of[child_name] = parent_name

        # --- 4) Map current section polygons with raw data ---
        poly_data: Dict[str, Dict[str, Any]] = {}
        for idx, poly in enumerate(sec.polygons):
            name = getattr(poly, "name", None)
            if not name:
                raise ValueError(f"Polygon at index {idx} has no name.")
            if name in poly_data:
                raise ValueError(f"Duplicate polygon name in section at z={z}: '{name}'")
            
            w_rel = float(getattr(poly, "weight"))
            verts = _extract_vertices(poly)
            area_geom = _signed_area(verts)  # Sterile: preserves sign
            
            poly_data[name] = {
                "idx": idx,
                "w_rel": w_rel,          # Relative weight (may be negative for voids)
                "area_geom": area_geom,   # Raw geometric area (signed)
            }

        # Verify all S0 polygons exist in current section
        for name in container_of.keys():
            if name not in poly_data:
                raise ValueError(f"Polygon '{name}' from S0 not found in section at z={z}")

        # --- 5) Compute absolute weights (w_abs) via recursive chain ---
        w_abs_cache: Dict[str, float] = {}
        
        def get_w_abs(poly_name: str) -> float:
            """Compute absolute weight: w_rel + w_abs(parent)."""
            if poly_name in w_abs_cache:
                return w_abs_cache[poly_name]
            parent = container_of[poly_name]
            w_rel = poly_data[poly_name]["w_rel"]
            if parent is None:
                w_abs = w_rel
            else:
                w_abs = w_rel + get_w_abs(parent)
            w_abs_cache[poly_name] = w_abs
            return w_abs

        for name in container_of.keys():
            get_w_abs(name)

        # --- 6) Group by absolute weight (with optional binning) ---
        def bin_weight(w: float) -> float:
            """Optional weight binning for grouping tolerance."""
            if w_tol and w_tol > 0.0:
                return round(w / w_tol) * w_tol
            return w

        groups: Dict[float, Dict[str, Any]] = {}
        per_polygon_records = []

        for name in container_of.keys():
            w_abs_raw = w_abs_cache[name]
            w_abs_grouped = bin_weight(w_abs_raw) if w_tol > 0 else w_abs_raw
            area_geom = poly_data[name]["area_geom"]
            
            # Accumulate geometric area in groups (sterile sum, preserves sign)
            if w_abs_grouped not in groups:
                groups[w_abs_grouped] = {"w": w_abs_grouped, "area": 0.0, "polygons": []}
            groups[w_abs_grouped]["area"] += area_geom
            groups[w_abs_grouped]["polygons"].append(name)

            # Record for per-polygon output
            per_polygon_records.append({
                "idx": poly_data[name]["idx"],
                "name": name,
                "container": container_of[name],
                "w_rel": poly_data[name]["w_rel"],
                "w_abs": w_abs_raw,  # Store original, not binned
                "area": area_geom,
            })

        # --- 7) Compute totals (sterile calculations) ---
        
        # Effective mechanical area: sum of (geometric area * relative weight)
        # This accounts for voids (negative w_rel) and material ratios.
        total_effective = sum(
            poly_data[name]["area_geom"] * poly_data[name]["w_rel"]
            for name in container_of.keys()
        )
        
        # Effective area excluding near-zero absolute weights
        total_effective_nonzero = sum(
            poly_data[name]["area_geom"] * poly_data[name]["w_rel"]
            for name in container_of.keys()
            if abs(w_abs_cache[name]) > float(zero_w_eps)
        )
        
        # Pure geometric sum (sterile, includes signs from orientation)
        total_geometric = sum(g["area"] for g in groups.values())

        # Prepare groups list with fractions
        groups_list = sorted(groups.values(), key=lambda d: d["w"])
        effective_denom = total_effective if total_effective != 0 else 1.0
        for g in groups_list:
            # Fraction relative to effective area (can be >1 or negative if mixed signs)
            g["area_fraction"] = (g["area"] * g["w"]) / effective_denom if g["w"] != 0 else 0.0

        # --- 8) Debug output ---
        if debug:
            print("=" * 60)
            print(f"section_area_by_weight (sterile) at z={z}")
            print("-" * 60)
            for rec in sorted(per_polygon_records, key=lambda x: x["idx"]):
                print(f"  [{rec['idx']}] {rec['name']:<15} "
                      f"w_rel={rec['w_rel']:+.3f} w_abs={rec['w_abs']:+.3f} "
                      f"area={rec['area']:+.6e}")
            print("-" * 60)
            print(f"Geometric Sum:   {total_geometric:+.6e}")
            print(f"Homogenized orea (|w|>0):  {total_effective:+.6e}")
            print(f"Geometric Total Surface: {total_effective_nonzero:+.6e}")
            print("=" * 60)

        # --- 9) Assemble output ---
        result: Dict[str, Any] = {
            "z": float(z),
            "total_area": float(total_effective),           # Area omogeneizzata effettiva
            "total_area_nonzero": float(total_effective_nonzero),
            "total_area_geometric": float(total_geometric),  # Somma geometrica pura
            "groups": groups_list,
        }
        
        if include_per_polygon:
            result["per_polygon"] = per_polygon_records
            
        return result

    
    def _determine_magnitude(self) -> None:
        """
        Compute a global geometric magnitude (scale) from the model's geometry and
        define tolerance values derived from that scale.

        This method is intentionally self-contained (no external helper functions),
        so it can be called once after object construction.

        It defines:
          - self.SCALE: characteristic length scale of the model
          - self.EPS_L: linear/length tolerance (geometry predicates, intersections)
          - self.EPS_A: area tolerance (degeneracy checks on areas, section integrals)
          - self.EPS_K_ATOL / self.EPS_K_RTOL: tolerances for matrix/numerical checks
        """
        # 1) Collect bounding box over all points in start/end sections
        inf = float("inf")
        min_x, min_y = inf, inf
        max_x, max_y = -inf, -inf

        # NOTE: adapt these attribute names to your internal storage.
        # The idea is: iterate over all polygons in both end sections and read their vertices.
        #
        # Expected structure (examples):
        #   self.sections["I"][obj_id][poly_id].points  -> list[(x,y)]
        #   self.sections["F"][obj_id][poly_id].points
        #
        # If your storage differs, only adjust this traversal; the rest stays the same.


        # --- Bounding box over BOTH endpoint sections (S0 and S1) ---
        # In your code:
        #   self.s0, self.s1 are Section objects
        #   section.polygons is Tuple[Polygon, ...]
        #   polygon.vertices is Tuple[Pt, ...]
        #   Pt has attributes .x and .y

        for sec in (self.s0, self.s1):
            for poly in sec.polygons:
                for v in poly.vertices:
                    x = float(v.x)
                    y = float(v.y)

                    if x < min_x: min_x = x
                    if y < min_y: min_y = y
                    if x > max_x: max_x = x
                    if y > max_y: max_y = y




        # Handle empty geometry defensively
        if min_x is inf:
            # No points found: fall back to a safe default
            dx = dy = 0.0
        else:
            dx = max_x - min_x
            dy = max_y - min_y

        # 2) Characteristic length scale.
        # Include L so long/slender members scale reasonably even with small cross-section extents.
        L = float(getattr(self, "L", 0.0))
        S = max(dx, dy, abs(L), 1.0)

        SCALE = S

        # 3) Tolerances
        #
        # EPS_L: geometric/linear tolerance.
        # Use this for: orientation tests, point-on-segment, segment intersection, etc.
        EPS_L = 1e-12 * S

        # EPS_A: area tolerance. Must scale as S^2.
        # Use this for: "area nearly zero" checks, summed areas, etc.
        EPS_A = 1e-12 * (S * S)

        # EPS_K: numerical/matrix tolerances.
        # Here it's better to keep a relative tolerance and a small absolute tolerance.
        # - RTOL controls proportional differences (scale-free).
        # - ATOL controls tiny absolute noise.
        #
        # If your matrices scale strongly with geometry/material, you can scale ATOL too,
        # but RTOL is the primary guard.
        EPS_K_RTOL = 1e-10
        EPS_K_ATOL = 1e-12

        # Optional: if you want a single "EPS_K" name as you wrote,
        # keep it as the absolute tolerance, and still keep RTOL separately.
        EPS_K = EPS_K_ATOL
        #print(f"SCALE {SCALE} EPS_K {EPS_K} EPS_L{EPS_L} EPS_A {EPS_A}")


    def to_dict(self, include_weight_laws=True):
        data = {
            "CSF": {
                "sections": {
                    "S0": self._section_to_dict(self.s0),
                    "S1": self._section_to_dict(self.s1),
                },
            }
        }
        # 
        if include_weight_laws and isinstance(self.weight_laws, dict):
            out = []
            for idx in sorted(self.weight_laws):
                i = idx - 1
                n0 = self.s0.polygons[i].name
                n1 = self.s1.polygons[i].name
                out.append(f"{n0},{n1}: {self.weight_laws[idx]}")
            data["CSF"]["weight_laws"] = out
        return data

    def to_yaml(self, filepath: Optional[str] = None, include_weight_laws: bool = True) -> str:
        """
        Produce YAML come stringa; se filepath è dato, scrive anche su file.
        """
        
        data = self.to_dict(include_weight_laws=include_weight_laws)
        if yaml is not None:
            yml = yaml.dump(
                data,
                Dumper=CSFDumper,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
                default_flow_style=False,
            )
        else:
           
            yml = _simple_yaml_dump(data) + "\n"

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(yml)

        return yml



        if include_weight_laws:
            laws_out = []
            if isinstance(self.weight_laws, dict):
                for idx in sorted(self.weight_laws.keys()):
                    expr = self.weight_laws[idx]
                    i = int(idx) - 1
                    n0 = self.s0.polygons[i].name
                    n1 = self.s1.polygons[i].name
                    laws_out.append(f"{n0},{n1}: {expr}")
            data["field"]["weight_laws"] = laws_out

        return data

    """
    Geometry-only object:
    - stores two endpoint sections (at z0 and z1)
    - returns intermediate Section at any z via linear interpolation of corresponding vertices
    """


    def get_opensees_integration_points(self, n_points: int = 5, L: float = None) -> List[float]:
        """
        Calculates the global Z-coordinates for OpenSees integration points using 
        the Gauss-Lobatto quadrature rule.
        
        RATIONALE:
        In finite element analysis (specifically for OpenSees forceBeamColumn elements), 
        the Gauss-Lobatto rule is preferred because it includes the endpoints of the 
        interval (z=0 and z=L). This is critical for detecting anomalies at the 
        very base of the shaft (e.g., FHWA Soft Toe) or at the top connection.
        
        ALGORITHM:
        1. Generate the roots of the derivative of the (n-1)-th Legendre Polynomial.
        2. These roots (plus -1.0 and 1.0) form the abscissae in the natural 
        coordinate system [-1, 1].
        3. Map these abscissae from [-1, 1] to the physical domain [z0, z1] or [0, L].
        
        Args:
            n_points (int): Number of integration points. Must be >= 2.
            L (float, optional): Total length of the element. If None, it uses 
                                the distance between the two defined sections.
        
        Returns:
            List[float]: A list of global Z-coordinates where OpenSees will 
                        sample the section properties.
        """
        z_start = self.s0.z
        z_end = self.s1.z
        
        if n_points < 2:
            raise ValueError("Number of integration points must be at least 2 for Gauss-Lobatto.")

        # 1. Physical boundaries
        
        
        
        
        # Usiamo section0 e section1 come definito nel costruttore field = ContinuousSectionField(section0=s0, section1=s1)
        
        z_start = self.s0.z
        z_end = self.s1.z
        actual_L = L if L is not None else (z_end - z_start)

        # 2. Calculation of Gauss-Lobatto Abscissae in range [-1, 1]
        # For n points, we need roots of P'_{n-1}(x)
        if n_points == 2:
            abscissae = [-1.0, 1.0]
        else:
            # The internal points are the roots of the derivative of Legendre polynomial P_{n-1}
            roots = np.polynomial.legendre.Legendre.deriv(
                np.polynomial.legendre.Legendre([0]*(n_points-1) + [1])
            ).roots()
            abscissae = np.concatenate(([-1.0], roots, [1.0]))

        # 3. Mapping from [-1, 1] to [z_start, z_start + actual_L]
        z_coords = [z_start + (xi + 1.0) * (actual_L / 2.0) for xi in abscissae]
        
        # Sort to ensure numerical stability
        z_coords = sorted(z_coords)
        return z_coords



    def __init__(self, section0: Section, section1: Section):
            
        if len(section0.polygons) != len(section1.polygons):
            raise ValueError(
                f"Mismatch: section0 has {len(section0.polygons)} polygons, "
                f"but section1 has {len(section1.polygons)} polygons."
        )

        if section0.z == section1.z:
            raise ValueError("Sections must be at different z coordinates.")

        self.s0 = section0
        self.s1 = section1

        # single source of truth
        self.z0 = section0.z
        self.z1 = section1.z
        self._determine_magnitude()
        # Optional list of callables or strings for custom weight interpolation
        self.weight_laws: Optional[Dict[int, str]] = None

        self._validate_inputs()
         
    def _strip_model_tags(name: str) -> str:
        """
        Remove everything starting from @cell or @wall (case-insensitive).
        If neither tag exists, return original trimmed name.
        Examples:
          "MP1_outer@cell@t=0.05" -> "MP1_outer"
          "legA@wall@alpha=0.8"   -> "legA"
          "poly_no_tags"          -> "poly_no_tags"
        """
        s = (name or "").strip()
        # cut from first occurrence of @cell or @wall to end of string
        return re.sub(r'(?i)@(cell|wall)\b.*$', '', s).strip()

    def _strip_model_tags(self, name: str) -> str:
        """
        Normalize polygon name for matching:
        - trim spaces
        - remove everything starting from @cell, @wall, or @closed (case-insensitive)
        """
        s = str(name or "").strip()
        return re.sub(r'(?i)@(cell|wall|closed)\b.*$', '', s).strip()


    def set_weight_laws(self, laws: Union[List[str], Dict[Union[int, str], str]]) -> None:
        """
        Sets weight variation laws. 
        If a polygon name is not found or homology fails, it raises an error 
        to prevent falling back to default linear behavior.
        """
        print("set_weight_laws")
        if not isinstance(laws, (list, dict)):
            raise ValueError("weight_laws must be a list or a dictionary.")
        
        num_polygons = len(self.s0.polygons)
        #valid_names0 = [p.name for p in self.s0.polygons]
        #valid_names1 = [p.name for p in self.s1.polygons]
        
        # Keep original polygon names as declared in S0/S1 strip @cell @wall
        valid_names0 = [self._strip_model_tags(p.name) for p in self.s0.polygons]
        valid_names1 = [self._strip_model_tags(p.name) for p in self.s1.polygons]
        #print(f"DEBUG valid_names0 {valid_names0} valid_names1 {valid_names1}")
        # Reset current laws 
        self.weight_laws = {}
        normalized_map = {}

        # 1. PARSING & STRICT TRANSLATION
        if isinstance(laws, list):
            for i, item in enumerate(laws):
                if isinstance(item, str) and ":" in item:
                    left, formula = item.split(":", 1)
                    left, formula = left.strip(), formula.strip()
                    #raw_names = [n.strip() for n in left.split(",")]
                    raw_names = [self._strip_model_tags(n) for n in left.split(",")]
                    if len(raw_names) == 2:
                        n0, n1 = raw_names
                        # STRICT CHECK: If the name does not exist, Error
                        if n0 not in valid_names0:
                            raise KeyError(f"Critical Error: Polygon '{ raw_names[0]}' not found in Section 0.")
                        if n1 not in valid_names1:
                            raise KeyError(f"Critical Error: Polygon '{raw_names[1]}' not found in Section 1.")
                        
                        idx0 = valid_names0.index(n0) + 1
                        idx1 = valid_names1.index(n1) + 1
                        
                        
                        # STRICT CHECK: Homology (must be the same polygon)
                        if idx0 != idx1:
                            raise ValueError(f"Homology Mismatch: '{n0}' (pos {idx0}) and '{n1}' (pos {idx1}) must match.")
                        #print(f"DEBUB idx0 {idx0} idx1 {idx1}")
                        normalized_map[idx0] = formula
                    
                    elif len(raw_names) == 1:
                        n0 = raw_names[0]
                        if n0 not in valid_names0:
                            raise KeyError(f"Critical Error: Polygon '{n0}' not found.")
                        normalized_map[valid_names0.index(n0) + 1] = formula
                else:
                    # Positional list case
                    if i < num_polygons:
                        normalized_map[i + 1] = item

        elif isinstance(laws, dict):
            for key, law in laws.items():
                target_idx = None
                if isinstance(key, int):
                    target_idx = key
                elif isinstance(key, str):
                    if key not in valid_names0:
                        raise KeyError(f"Critical Error: No polygon named '{key}' found.")
                    target_idx = valid_names0.index(key) + 1
                
                if target_idx is not None:
                    if target_idx < 1 or target_idx > num_polygons:
                        raise IndexError(f"Index {target_idx} out of range (1-{num_polygons}).")
                    normalized_map[target_idx] = law

        z0, z1 = self.s0.z, self.s1.z
        z_mid = (z0 + z1) / 2.0 # Actual RELATIVE Z value halfway between the sections
        L_val = z1 - z0

        # Compute t consistently with the interpolation formula
        # If L_val is 0 (coincident sections), t is forced to 0 to avoid division by zero
        #t_mid = (z_mid - z0) / L_val if L_val != 0 else 0.0
        

        for idx, formula in normalized_map.items():
            

            if isinstance(formula, str):
                try:
                    # Endpoint polygon references for distance calculations
                    p0_test = self.s0.polygons[idx-1]
                    p1_test = self.s1.polygons[idx-1]
                    
                    # Generation of midpoint vertices for p_mid (required for d(i,j) helper)
                    current_verts = tuple(v0.lerp(v1,z_mid,L_val) for v0, v1 in zip(p0_test.vertices, p1_test.vertices))
                    p_mid = Polygon(vertices=current_verts, weight=p0_test.weight, name=p0_test.name)
                    
                    # 1. Calculate the total length of the field
                    l_total = abs(self.s1.z - self.s0.z)
                    try:
                        # We test the formula at mid-span (t=0.5) to verify syntax and logic
                        we = evaluate_weight_formula(formula, p0_test, p1_test,z0=self.s0.z,z1=self.s1.z,zt=z_mid)
                    except Exception as e:                      
                        raise ValueError(
                            f"VALIDATION FAILED: The formula for '{p0_test.name}' is not valid.\n"
                            f"Formula: '{formula}'\n"
                            f"Error encountered at the midpoint::: {e}"
                        )

                except Exception as e:
                    raise ValueError(
                        f":VALIDATION FAILED: The formula for '{valid_names0[idx-1]}' is not valid.\n"
                        f"Formula: '{formula}'\n"
                        f"Error encountered at the midpoint:- {e}"
                    )
                
        # -------------------------------------------
        # 2. EFFECTIVE ASSIGNMENT (Bypassing FrozenInstanceError)
        for idx, formula in normalized_map.items():

            if formula is None: continue
           
            # Save as an integer for the interpolator
            self.weight_laws[idx] = str(formula)
            try:
                numeric_w = float(formula)
                if 1 <= idx <= num_polygons:
                    # Force update on s0 and s1 polygons
                    object.__setattr__(self.s0.polygons[idx-1], 'weight', numeric_w)
                    object.__setattr__(self.s1.polygons[idx-1], 'weight', numeric_w)
            except ValueError:
                # The formula is a function; it will be evaluated during interpolation
                pass
        # SUCCESS - Weight laws correctly assigned
        print(f"SUCCESS - Weight laws correctly assigned: {self.weight_laws}")


    def _validate_inputs(self) -> None:
        if len(self.s0.polygons) != len(self.s1.polygons):
            raise ValueError("Start/end sections must have the same number of polygons.")

        for i, (p0, p1) in enumerate(zip(self.s0.polygons, self.s1.polygons)):
            if len(p0.vertices) != len(p1.vertices):
                raise ValueError(
                    f"Polygon index {i} has different vertex counts: "
                    f"{len(p0.vertices)} vs {len(p1.vertices)}"
                )
            


    def _interpolate_weight(self, w0: float, w1: float, z: float, p0: Polygon, p1: Polygon, law: Optional[str]) -> float:
        #
        L_val = abs(self.s1.z - self.s0.z)
        
        if isinstance(law, str) and law.strip():
            # z is real RELATIVE not [0..1]
            # Use the existing section attributes. 
            # Based on the error, self.section1 doesn't exist. 
            # In ContinuousSectionField, endpoints are usually self.s0 and self.s1
            # Since p_current is not in the signature, we interpolate vertices 
            # locally to allow the d(i, j) helper to work at height z
            #
            current_verts = tuple(v0.lerp(v1, z,L_val) for v0, v1 in zip(p0.vertices, p1.vertices))
            p_current = Polygon(vertices=current_verts, weight=w0, name=p0.name) ## w0 is dummy value
           
            try:
                # We test the formula at t and verify syntax and logic
                
                wcust = evaluate_weight_formula(law, p0, p1, self.s0.z,self.s1.z,zt=z)  
                
                return wcust
            except Exception as e:                  
                raise ValueError(
                    f"VALIDATION FAILED-: The formula for '{p0.name} '{p1.name}' is not valid.\n"
                    f"Formula: '{law}'\n"
                    f"Error encountered at the midpoint:: {e}"
                )
            
        # Default fallback: Linear Interpolation
        return w0 + (w1 - w0)/L_val * z

  
    def _to_t(self, z: float) -> float:
        z = float(z)
        if not (min(self.z0, self.z1) <= z <= max(self.z0, self.z1)):
            raise ValueError(f"z={z} is outside [{self.z0}, {self.z1}].")
        return (z - self.z0) / (self.z1 - self.z0)



    def section(self, z: float) -> Section: 

        #-----------------------------------------------------
        # helpers
        #-----------------------------------------------------


        def _resolve_topology_and_t_from_names(
            p0_name: str,
            p1_name: str,
            z: float,
            z0: float,
            z1: float,
        ) -> Tuple[Optional[str], Optional[float]]:
            """
            Resolve topology tag and thickness t(z) from two polygon names.

            Design intent
            -------------
            This helper is conservative and explicit:
            - It resolves topology from tags in names (@cell, @wall, @closed).
            - It resolves thickness from @t=... with linear interpolation in z.
            - It does NOT build the final runtime name (that is delegated to a second helper).

            Topology policy
            ---------------
            - If both names define topology and they differ, raise CSFError (blocking).
            - If topology exists only on one side, keep it as constant.
            - If no topology is found on both sides, return topology=None.

            Thickness policy
            ----------------
            - If @t exists on both sides -> interpolate linearly at z.
            - If @t exists on one side only -> keep constant.
            - If @t missing on both sides -> t_value=None.
            - If resolved topology is @cell and t_value is None -> blocking CSFError.

            Parameters
            ----------
            p0_name, p1_name : str
                Polygon names at start/end stations.
            z : float
                Absolute query coordinate.
            z0, z1 : float
                Absolute bounds used for interpolation.

            Returns
            -------
            (topology_tag, t_value) : Tuple[Optional[str], Optional[float]]
                topology_tag in {'@cell', '@wall', '@closed'} or None.
                t_value as positive float or None.

            Raises
            ------
            CSFError
                On incompatible topology, invalid @t format/value, or @cell without thickness.
            """

            def _norm_name(s: str) -> str:
                """Lowercase + trim helper."""
                return str(s or "").strip().lower()

            def _extract_topology(name: str) -> Optional[str]:
                """
                Extract at most one topology tag from name.

                Valid tags:
                    @cell, @wall, @closed

                If more than one topology tag appears in the same name, raise CSFError.
                """
                low = _norm_name(name)
                has_cell = "@cell" in low
                has_wall = "@wall" in low
                has_closed = "@closed" in low

                n = int(has_cell) + int(has_wall) + int(has_closed)
                if n > 1:
                    raise CSFError(
                        f"Invalid polygon name '{name}': multiple topology tags found "
                        f"(@cell/@wall/@closed)."
                    )

                if has_cell:
                    return "@cell"
                if has_wall:
                    return "@wall"
                if has_closed:
                    return "@closed"
                return None

            def _parse_t(name: str) -> Optional[float]:
                """
                Parse @t=<number> from a name.

                Returns
                -------
                float | None
                    Positive thickness if present, otherwise None.

                Raises
                ------
                CSFError
                    If @t exists but is malformed or non-positive.
                """
                s = str(name or "")
                low = s.lower()
                token = "@t="
                i = low.find(token)
                if i < 0:
                    return None

                j = i + len(token)
                if j >= len(s):
                    raise CSFError(f"Invalid @t tag in polygon name: '{name}'")

                allowed = set("0123456789.+-eE")
                buf = []
                for ch in s[j:]:
                    if ch in allowed:
                        buf.append(ch)
                    else:
                        break

                if not buf:
                    raise CSFError(f"Invalid numeric @t value in polygon name: '{name}'")

                try:
                    t_val = float("".join(buf))
                except Exception:
                    raise CSFError(f"Invalid numeric @t value in polygon name: '{name}'")

                if t_val <= 0.0:
                    raise CSFError(f"Non-positive @t value in polygon name: '{name}'")
                return t_val

            def _interp_linear(zv: float, z0v: float, z1v: float, v0: float, v1: float) -> float:
                """
                Linear interpolation with clamped lambda in [0, 1].
                """
                dz = z1v - z0v
                if abs(dz) <= EPS_L:
                    return v0
                lam = (zv - z0v) / dz
                if lam < 0.0:
                    lam = 0.0
                elif lam > 1.0:
                    lam = 1.0
                return (1.0 - lam) * v0 + lam * v1

            # --- Resolve topology ---
            top0 = _extract_topology(p0_name)
            top1 = _extract_topology(p1_name)

            if top0 is not None and top1 is not None and top0 != top1:
                raise CSFError(
                    f"Incompatible topology tags between stations: "
                    f"'{p0_name}' ({top0}) vs '{p1_name}' ({top1})."
                )

            topology = top0 if top0 is not None else top1

            # --- Resolve thickness ---
            t0 = _parse_t(p0_name)
            t1 = _parse_t(p1_name)

            if t0 is not None and t1 is not None:
                t_val = _interp_linear(float(z), float(z0), float(z1), float(t0), float(t1))
            elif t0 is not None:
                t_val = float(t0)  # constant from S0
            elif t1 is not None:
                t_val = float(t1)  # constant from S1
            else:
                t_val = None

            # Defensive post-check
            if t_val is not None and t_val <= 0.0:
                raise CSFError(
                    f"Resolved non-positive thickness t={t_val} "
                    f"from '{p0_name}' -> '{p1_name}' at z={z}."
                )

            # Mandatory thickness for @cell
            if topology == "@cell" and t_val is None:
                raise CSFError(
                    f"Missing @t for @cell between '{p0_name}' and '{p1_name}'."
                )

            return topology, t_val


        def _build_interpolated_polygon_name(
            p0_name: str,
            p1_name: str,
            topology_tag: Optional[str],
            t_value: Optional[float],
        ) -> str:
            """
            Build the runtime polygon name from resolved metadata.

            Important
            ---------
            - This helper does NOT interpolate values.
            - It only formats a canonical name for the interpolated section.

            Naming policy
            -------------
            - Canonical base name is taken from S0 left-part before '@'
            (fallback to S1 if S0 base is empty).
            - Different S0/S1 base names are allowed (no blocking mismatch).
            - If topology is None -> return only base.
            - @cell requires t_value.
            - @wall / @closed accept optional t_value.

            Examples
            --------
            - base@cell@t=0.25
            - base@wall
            - base@wall@t=0.18
            - base@closed
            """

            def _left_of_at(name: str) -> str:
                """Return substring before first '@'."""
                s = str(name or "").strip()
                k = s.find("@")
                return s[:k] if k >= 0 else s

            def _fmt_t(t: float) -> str:
                """Compact numeric formatting for tags."""
                return f"{float(t):.12g}"

            base0 = _left_of_at(p0_name)
            base1 = _left_of_at(p1_name)

            # Conservative base selection: prefer S0 identity.
            base = base0 if base0 else base1
            if not base:
                raise CSFError(
                    f"Invalid polygon base name(s): '{p0_name}' / '{p1_name}'"
                )

            # No topology -> plain base name
            if topology_tag is None:
                return base

            if topology_tag == "@cell":
                if t_value is None:
                    raise CSFError(f"Missing @t for @cell polygon '{base}'.")
                return f"{base}@cell@t={_fmt_t(t_value)}"

            if topology_tag == "@wall":
                if t_value is None:
                    return f"{base}@wall"
                return f"{base}@wall@t={_fmt_t(t_value)}"

            if topology_tag == "@closed":
                if t_value is None:
                    return f"{base}@closed"
                return f"{base}@closed@t={_fmt_t(t_value)}"

            raise CSFError(
                f"Unsupported topology tag '{topology_tag}' for polygon '{base}'."
            )




        def _build_interpolated_polygon_name(
            p0_name: str,
            p1_name: str,
            topology_tag: Optional[str],
            t_value: Optional[float],
        ) -> str:
            """
            Build runtime polygon name from resolved metadata.

            Notes
            -----
            - This helper only formats the name.
            - It does not validate/interpolate z-dependent values.
            - Different base names between S0/S1 are allowed by design.
            """

            def _left_of_at(name: str) -> str:
                s = str(name or "").strip()
                k = s.find("@")
                return s[:k] if k >= 0 else s

            def _fmt_t(t: float) -> str:
                return f"{float(t):.12g}"

            base0 = _left_of_at(p0_name)
            base1 = _left_of_at(p1_name)

            # Use S0 base as canonical runtime name; fallback to S1 if needed.
            base = base0 if base0 else base1
            if not base:
                raise CSFError(f"Invalid polygon base name(s): '{p0_name}' / '{p1_name}'")

            if topology_tag is None:
                return base

            if topology_tag == "@cell":
                if t_value is None:
                    raise CSFError(f"Missing @t for @cell polygon '{base}'.")
                return f"{base}@cell@t={_fmt_t(t_value)}"

            if topology_tag == "@wall":
                if t_value is None:
                    return f"{base}@wall"
                return f"{base}@wall@t={_fmt_t(t_value)}"

            if topology_tag == "@closed":
                if t_value is None:
                    return f"{base}@closed"
                return f"{base}@closed@t={_fmt_t(t_value)}"

            raise CSFError(f"Unsupported topology tag '{topology_tag}' for polygon '{base}'.")



        ### end helpers ----------------------------------------------------------------------------
        # in input z is absol   ute
        origz=z-self.z0 # make origz relative
        #t = self._to_t(z) # normalize z 
        lenght = abs(self.z1 - self.z0)
        if z < self.z0 or z > self.z1:
            raise CSFError(f"z={z} out of bounds [{self.z0}, {self.z1}]")
        polys: List[Polygon] = []
       
        for i, (p0, p1) in enumerate(zip(self.s0.polygons, self.s1.polygons)):
            
            verts = tuple(v0.lerp(v1, origz,lenght) for v0, v1 in zip(p0.vertices, p1.vertices))
            #print(f"DEBUG t {verts}")
            # keep weight/name from p0 by default
            # polys.append(Polygon(vertices=verts, weight=p0.weight, name=p0.name))

            ### interpolation here
            # Identify if a custom law exists for the current polygon index.
            # Support for both List (by index) and Dictionary (by index or by name).
            current_law = None
            idx = i + 1 

            
    
            if isinstance(self.weight_laws, list):
               
                if i < len(self.weight_laws):
                    current_law = self.weight_laws[idx]
                    
            elif isinstance(self.weight_laws, dict):
                # Look up by index first, then by polygon name
                #current_law = self.weight_laws.get(i, self.weight_laws.get(p0.name))
                current_law = self.weight_laws.get(idx)
                #print(f"DEBUG idx {idx} current_law {current_law}")
            else:
                None
                #print(f"DEBUG3  interp_weight  {idx} {current_law}")  
            
            interp_weight_child = self._interpolate_weight(p0.weight, p1.weight, origz, p0, p1, current_law)
            idx_pol_parent= self.get_container_polygon_index(p0,i)
            #interp_weight = self.weight_effective(p0.weight, p1.weight, origz, p0, p1, current_law)

            polparent0 = None
            polparent1 = None
            parent_law = None
            interp_weight_parent = 0 # default value when for parent is not found
            if idx_pol_parent is not None:
                polparent0 = self.s0.polygons[idx_pol_parent]
                polparent1 = self.s1.polygons[idx_pol_parent]

                # Get parent law with same conventions used elsewhere (list/dict, 1-based index)
                if isinstance(self.weight_laws, list):
                    # If your list is 1-based (because you use idx=i+1), keep that convention:
                    parent_key = idx_pol_parent + 1
                    if 0 <= idx_pol_parent < len(self.weight_laws):
                        parent_law = self.weight_laws[parent_key]
                elif isinstance(self.weight_laws, dict):
                   
                    parent_key = idx_pol_parent + 1  # same 1-based convention
                    parent_law = self.weight_laws.get(parent_key, None)
                    
                    interp_weight_parent = self._interpolate_weight(polparent0.weight, polparent1.weight, origz, polparent0, polparent1, parent_law)
                else:
                    interp_weight_parent = self._interpolate_weight(polparent0.weight, polparent1.weight, origz, polparent0, polparent1, parent_law)

            interp_weight_relative = interp_weight_child - interp_weight_parent #this is very important 
            #print (f"DEBUG idx_pol_parent {idx_pol_parent}-{i} interp_weight_child {interp_weight_child} interp_weight_parent {interp_weight_parent} interp_weight_relative {interp_weight_relative} ")
            #print ("------------------------------------------------------")
            #print(f"DEBUG z {z} child {i} : name {p0.name}  interp_weight_child {interp_weight_child}  : idx_pol_parent {idx_pol_parent} parent_law {parent_law} : interp_weight_parent {interp_weight_parent} : interp_weight_relative {interp_weight_relative}")

            #poly = Polygon(vertices=verts, weight=interp_weight_relative, name=p0.name)


            # Build runtime polygon metadata from both reference names.
            # We first resolve topology and thickness consistently along z
            # (including mandatory @t for @cell and optional @t for @wall),
            # then compose a normalized name for the interpolated section.
            # This centralizes tag logic in section(z) 

            topology_tag, t_value = _resolve_topology_and_t_from_names(
                p0_name=p0.name,
                p1_name=p1.name,
                z=z,          # oppure origz con coerenza al tuo resolver
                z0=self.z0,
                z1=self.z1,
            )

            poly_name = _build_interpolated_polygon_name(
                p0_name=p0.name,
                p1_name=p1.name,
                topology_tag=topology_tag,
                t_value=t_value,
            )

            poly = Polygon(vertices=verts, weight=interp_weight_relative, name=poly_name)





            # --------------------------
       
            if not re.search(r'(?i)@(cell|wall|closed)\b', str(poly.name or "")) and  polygon_has_self_intersections(poly):
                warnings.warn(
                    f"Self-intersection detected in polygon '{poly.name}' at z={z:.3f}",
                    RuntimeWarning
                )


            polys.append(poly)
        return Section(polygons=tuple(polys), z=float(z))

# -------------------------
# Digestor: Section properties (2D polygon-based)
# -------------------------

def _polygon_signed_area_and_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    """
    Shoelace. Returns signed area (can be negative depending on orientation) and centroid. never in CSF
    """
    verts = poly.vertices
    n = len(verts)

    a2 = 0.0  # 2*Area signed
    cx6 = 0.0
    cy6 = 0.0

    for i in range(n):
        # Current vertex and next vertex (cyclic)
       
        v0 = verts[i]
        v1 = verts[(i + 1) % n]
       
        x0, y0 = v0.x, v0.y
        x1, y1 = v1.x, v1.y
        
        # Calculate cross product for this segment
        cross = x0 * y1 - x1 * y0

        
        a2 += cross
        cx6 += (x0 + x1) * cross
        cy6 += (y0 + y1) * cross

    if abs(a2) < EPS_A:
        return 0.0, (0.0, 0.0)

    A = 0.5 * a2
    Cx = cx6 / (3.0 * a2)
    Cy = cy6 / (3.0 * a2)
    return A, (Cx, Cy)

def polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    """
    Computes the signed area and geometric centroid of a non-self-intersecting polygon.

    TECHNICAL SUMMARY:
    This function implements the Surveyor's Formula (Shoelace Algorithm), 
    derived from Green's Theorem, to integrate area and first moments over 
    a planar polygonal domain. It is designed to handle both "solid" (counter-clockwise) 
    and "void" (clockwise) polygons to model hollow sections like wind turbine towers.

    MATHEMATICAL FORMULATION:
    1. Signed Area (A):
       The area is computed as the sum of cross-products of vertex vectors:
       A = 0.5 * Σ (x_i * y_{i+1} - x_{i+1} * y_i)
       The sign of the area indicates the vertex winding order:
       - Positive: Counter-Clockwise (CCW).
       - Negative: Clockwise (CW).

    2. Geometric Centroid (Cx, Cy):
       The coordinates of the centroid (center of area) are derived from the 
       first moments of area (Qx, Qy):
       Cx = (1 / 6A) * Σ (x_i + x_{i+1}) * (x_i * y_{i+1} - x_{i+1} * y_i)
       Cy = (1 / 6A) * Σ (y_i + y_{i+1}) * (x_i * y_{i+1} - x_{i+1} * y_i)

    COMPUTATIONAL ROBUSTNESS:
    - Degeneracy Handling: Includes a threshold check (EPS_K) to identify 
      degenerate polygons (lines or points) and prevent division-by-zero errors.
    - Consistency: Since it utilizes a cyclic vertex indexing [(i + 1) % n], 
      it ensures a closed-loop integration regardless of vertex count.

    APPLICABILITY IN RULED SURFACE MODELING:
    By returning the signed area, this function allows for seamless 
    homogenization. When a void (e.g., the inner diameter of a tower) is 
    modeled with an opposite winding order or negative weight, the integration 
    correctly subtracts its properties from the total section digest.

    RETURNS:
       - Area: Signed area of the polygon [L²].
       - Centroid: Tuple (Cx, Cy) representing the geometric center [L].
    """
    A_signed, (Cx, Cy) = _polygon_signed_area_and_centroid(poly)
    
    #A_mag = abs(A_signed) #qui
    A_mag = (A_signed) #qui
    return poly.weight * A_mag, (Cx, Cy)


def section_data(field: ContinuousSectionField, z: float) -> dict:
    """
    z is ABSOLUTE
    Extracts the complete geometric state and physical properties of a section 
    at a specific longitudinal coordinate (z).

    TECHNICAL SUMMARY:
    This function acts as a high-level accessor for the Continuous Section Field. 
    It performs a synchronized extraction of both the interpolated boundary 
    geometry and the corresponding integral properties (Area, First/Second Moments). 
    It provides a discrete "snapshot" of a 3D ruled solid at any point along 
    its integration path.

    WORKFLOW AND DATA ARCHITECTURE:
    1. Geometric Reconstruction:
       The function first invokes the internal Linear Interpolation (LERP) 
       mechanism to reconstruct the homogenized polygonal boundaries at 
       coordinate 'z'. This ensures topological consistency across the 
       longitudinal domain.

    2. Property Integration:
       Once the geometry is established, the 'section_properties' engine 
       is executed to compute the sectional digest. This involves:
       - Zeroth Moment: Area (A).
       - First Moments: Centroidal coordinates (Cx, Cy).
       - Second Moments: Moments of inertia (Ix, Iy, Ixy) and the Polar 
         Moment (J).

    3. Data Encapsulation:
       The results are packaged into a dictionary structure, decoupling the 
       raw geometric data (vertices/polygons) from the derived structural 
       parameters.

    APPLICABILITY:
    This function is the standard interface for structural analysis routines 
    that require local stiffness or stress evaluation at specific points 
    along a non-prismatic member.

    RETURNS:
       A dictionary containing:
       - 'section': The Section object (polygonal boundaries at z).
       - 'properties': A dictionary of computed geometric constants.
    """




    section = field.section(z)
    props = section_properties(section)

    return {
        "section": section,     # geometria completa
        "properties": props,    # A, Cx, Cy, Ix, Iy, Ixy, J
    }



def section_properties(section: Section) -> Dict[str, float]:
    """
    Computes the integral geometric properties for a composite cross-section.

    TECHNICAL SUMMARY:
    This function performs a multi-pass integration over a set of weighted 
    polygons to derive the global geometric constants. It manages homogenization 
    by algebraically summing contributions, allowing for the representation of 
    complex domains with voids or varying material densities.

    ALGORITHMIC WORKFLOW:
    1. First-Order Moments (Area and Centroid):
       - Aggregates the weighted area (A) and the first moments of area (Qx, Qy) 
         for all constituent polygons.
       - Locates the global centroid (Cx, Cy) of the composite section.

    2. Second-Order Moments (Inertia about Origin):
       - Computes the area moments of inertia (Ix, Iy) and the product of 
         inertia (Ixy) relative to the global coordinate origin (0,0).

    3. Translation of Axes (Parallel Axis Theorem):
       - Applies the Huygens-Steiner Theorem to shift the moments of inertia 
         from the global origin to the newly calculated centroidal axes:
         I_centroid = I_origin - A * d^2
       - This transformation ensures the properties are intrinsic to the 
         section's geometry, independent of the global coordinate system.

    4. Polar Moment Extraction:
       - Derives the Polar Second Moment of Area (J) about the centroid as 
         the sum of the orthogonal centroidal moments (Ix + Iy).

    RETURNS:
       A comprehensive dictionary containing:
       - 'A': Net weighted area.
       - 'Cx', 'Cy': Centroidal coordinates.
       - 'Ix', 'Iy', 'Ixy': Second moments of area about centroidal axes.
       - 'J': Polar moment of area.
    """
    # First pass: area + centroid
    A_tot = 0.0
    Cx_num = 0.0
    Cy_num = 0.0

    poly_cache = []
    ii=0
    for poly in section.polygons:
        ii=ii+1
        A_i, (cx_i, cy_i) = polygon_area_centroid(poly)
        A_tot += A_i
        
        Cx_num += A_i * cx_i
        Cy_num += A_i * cy_i
        poly_cache.append((poly, A_i, cx_i, cy_i))

    if abs(A_tot) < EPS_A:
        raise ValueError("Composite area is ~0;- cannot compute centroid/properties reliably. ")

    Cx = Cx_num / A_tot
    Cy = Cy_num / A_tot

    # Second pass: inertia about origin then shift to centroid
    Ix_o = 0.0
    Iy_o = 0.0
    Ixy_o = 0.0

    for poly, _, _, _ in poly_cache:
        ix, iy, ixy = polygon_inertia_about_origin(poly)
        Ix_o += ix
        Iy_o += iy
        Ixy_o += ixy

    # Parallel axis theorem to centroid
    Ix_c = Ix_o - A_tot * (Cy * Cy)
    Iy_c = Iy_o - A_tot * (Cx * Cx)
    Ixy_c = Ixy_o - A_tot * (Cx * Cy)

    J = Ix_c + Iy_c


    if abs(A_tot)<EPS_A:
        A_tot = 0
    if abs(Cx)<EPS_L:
        Cx = 0
    if abs(Cy)<EPS_L:
        Cy = 0
    if abs(Ix_c)<EPS_K_ATOL:
        Ix_c = 0
    if abs(Iy_c)<EPS_K_ATOL:
        Iy_c = 0
    if abs(Ixy_c)<EPS_K_ATOL:
        Ixy_c= 0
    if abs(J)<EPS_K_ATOL:
        J= 0                

    return {
        "z": section.z,
        "A": A_tot,
        "Cx": Cx,
        "Cy": Cy,
        "Ix": Ix_c,
        "Iy": Iy_c,
        "Ixy": Ixy_c,
        "J": J,
    }


# -------------------------
# Visualization helpers
# -------------------------

def _set_axes_equal_3d(ax) -> None:
    """
    Configures 3D axis limits to perform a 'selective zoom' and maintain 
    consistent aspect ratios for cross-sectional visualization.

    TECHNICAL SUMMARY:
    This function normalizes the viewport of a Matplotlib 3D projection. 
    It ensures that the horizontal plane (X-Y) is scaled isotropically 
    (equal aspect ratio) to prevent geometric distortion of the sections, 
    while allowing the longitudinal axis (Z) to retain its full physical 
    extent for structural context.

    ALGORITHMIC LOGIC:
    1. Limit Extraction:
       Retrieves current bounding box limits for X, Y, and Z dimensions 
       to determine the object's spatial center.

    2. Planar Isotropic Scaling:
       Calculates a maximum radius based on the spans of X and Y. By 
       applying this radius symmetrically to both horizontal axes, the 
       function ensures that circles or ellipses appear without 
       eccentricity distortion.

    3. Longitudinal Preservation:
       Unlike standard 'equal axis' commands, this logic preserves the 
       original Z-limits. This is crucial for high-aspect-ratio solids, 
       ensuring the entire height is visible within the frame.

    4. Box Aspect Ratio:
       Sets the 'box_aspect' to (1, 1, 2) to force a vertical emphasis, 
       making slender solids visually representative of their physical 
       proportions.
    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    # Calcoliamo i centri
    x_mid = sum(x_limits) / 2.0
    y_mid = sum(y_limits) / 2.0
    z_mid = sum(z_limits) / 2.0

    # Determine the maximum range for the X-Y plane only
    # (Ensures horizontal geometry fills the space without distortion)
    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    radius_xy = 0.5 * max(x_range, y_range)

    # Apply centered isotropic zoom on X and Y
    ax.set_xlim3d([x_mid - radius_xy, x_mid + radius_xy])
    ax.set_ylim3d([y_mid - radius_xy, y_mid + radius_xy])
    
    # Maintain physical Z-limits for the longitudinal axis
    ax.set_zlim3d(z_limits)

    # Force a visual box aspect to emphasize verticality
    ax.set_box_aspect((1, 1, 2))


class Visualizer:
    """
    Adds 2D and 3D plotting utilities on top of a ContinuousSectionField.
    """

    def __init__(self, field: ContinuousSectionField):
        self.field = field
    # ----------------------------------------------------------------------------


    def plot_weight(self, num_points=100, tol=1e-12):
        """
        Plot w(z) per polygon pair, skipping polygons with w(z) == 0 for all sampled z.
        Skipped polygons are listed in a figure note.
        Min/Max markers are shown on each plotted curve.
        """
        import numpy as np
        import matplotlib.pyplot as plt

        z_start = self.field.s0.z
        z_end = self.field.s1.z
        z_values = np.linspace(z_start, z_end, num_points)

        num_polys = len(self.field.s0.polygons)
        poly_w_series = {i: [] for i in range(num_polys)}

        # Evaluate weights
        for z in z_values:
            for i in range(num_polys):
                p0 = self.field.s0.polygons[i]
                p1 = self.field.s1.polygons[i]

                if self.field.weight_laws is not None and (i + 1) in self.field.weight_laws:
                    current_law = self.field.weight_laws[i + 1]
                else:
                    current_law = None

                w_val = self.field._interpolate_weight(
                    p0.weight, p1.weight, z, p0, p1, current_law
                )
                poly_w_series[i].append(float(w_val))

        # Split polygons: zero-flat vs plottable
        zero_polys = []
        plot_indices = []

        for i in range(num_polys):
            p0 = self.field.s0.polygons[i]
            p1 = self.field.s1.polygons[i]
            label = f"[{i}] s0:{p0.name} -> s1:{p1.name}"

            y = np.asarray(poly_w_series[i], dtype=float)
            if np.all(np.isclose(y, 0.0, atol=tol, rtol=0.0)):
                zero_polys.append(label)
            else:
                plot_indices.append(i)

        # If all are zero, no plot
        if len(plot_indices) == 0:
            print("All polygon weights are identically zero on sampled z.")
            print("Skipped polygons:")
            for s in zero_polys:
                print(" -", s)
            return

        # Create subplots only for non-zero polygons
        n_plot = len(plot_indices)
        fig_w, axes_w = plt.subplots(n_plot, 1, figsize=(10, 2.4 * n_plot), sharex=True)
        if n_plot == 1:
            axes_w = [axes_w]
        print("\n=== START WEIGHT MIN/MAX REPORT ===")
        for ax_pos, i in enumerate(plot_indices):
            ax = axes_w[ax_pos]
            p0 = self.field.s0.polygons[i]
            p1 = self.field.s1.polygons[i]
            y = np.asarray(poly_w_series[i], dtype=float)

            idx_min = int(np.argmin(y))
            idx_max = int(np.argmax(y))
            w_min, w_max = float(y[idx_min]), float(y[idx_max])
            z_min, z_max = float(z_values[idx_min]), float(z_values[idx_max])
            print(
              f"[{i}] s0:{p0.name} -> s1:{p1.name} | "
              f"min w={w_min:.12g} at z={z_min:.12g} | "
              f"max w={w_max:.12g} at z={z_max:.12g}"
            )
            # Main curve
            ax.plot(z_values, y, linewidth=1.5, label=f"s0 {p0.name} - s1 {p1.name}")

            # Min/Max small markers on the curve
            ax.scatter([z_min], [w_min], marker="v", s=26, zorder=3, label="min")
            ax.scatter([z_max], [w_max], marker="^", s=26, zorder=3, label="max")

            # Optional tiny text near markers
            ax.annotate(f"{w_min:.4f}", (z_min, w_min), textcoords="offset points", xytext=(4, -12), fontsize=7)
            ax.annotate(f"{w_max:.4f}", (z_max, w_max), textcoords="offset points", xytext=(4, 6), fontsize=7)

            # y-limits
            if w_max != w_min:
                margin = (w_max - w_min) * 0.10
            else:
                margin = max(abs(w_max) * 0.05, 0.05)
            ax.set_ylim(w_min - margin, w_max + margin)

            ax.set_ylabel(f"s0 {p0.name}\ns1 {p1.name}", fontweight="bold")
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.set_title(
                f"Weight (w) | min={w_min:.6f} @ z={z_min:.3f} | max={w_max:.6f} @ z={z_max:.3f}",
                loc="right", fontsize=8
            )
        print("=== END WEIGHT MIN/MAX REPORT ===")
        axes_w[-1].set_xlabel("z")

        # Figure-level note for zero-flat polygons
        if zero_polys:
            note = "Skipped (w=0 for all z): " + "; ".join(zero_polys)
            fig_w.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8)

        fig_w.suptitle(
            f"Individual Polygon Weight (w) Distributions (Interpolated # {num_points} points)",
            fontweight="bold"
        )
        fig_w.tight_layout(rect=[0, 0.04, 1, 0.96])
        plt.show()







    # ----------------------------------------------------------------------------
    def plot_properties(self, keys_to_plot=None, alpha=1, num_points=100):
        """
        Plot the evolution of selected section properties along the Z-axis.

        Generic behavior for returned values:
        - If a property is scalar -> plot on left y-axis.
        - If a property returns a pair (left_value, right_value):
            * left_value  is plotted on left y-axis
            * right_value is plotted on right y-axis (twin axis)

        Title behavior:
        - Right side (top): min/max summary of left channel (same style as before)
        - Left side  (top): only t(z0), t(z1) when right channel exists

        Args:
            keys_to_plot (list[str] | None):
                Property keys to plot (e.g., ["A", "Ix", "Iy"]).
                If None, defaults to empty list.
            alpha (float):
                Passed through to section_full_analysis.
            num_points (int):
                Number of z samples between s0.z and s1.z.
        """
        import numpy as np
        import matplotlib.pyplot as plt

        # Z bounds from field endpoints
        z_start = self.field.s0.z
        z_end = self.field.s1.z

        # Keep current convention: None -> empty list
        if keys_to_plot is None:
            keys_to_plot = []

        # Early exit if no keys are requested
        if len(keys_to_plot) == 0:
            plt.show()
            return

        # Uniform sampling along z
        z_values = np.linspace(z_start, z_end, num_points)

        # Left-axis values (main channel)
        data_series = {key: [] for key in keys_to_plot}

        # Right-axis values (secondary channel; only if property returns a pair)
        data_series_right = {key: [] for key in keys_to_plot}

        # -------------------------------------------------------------------------
        # 1) Evaluate properties at each sampled z
        # -------------------------------------------------------------------------
        for z in z_values:
            # Build section at current z
            current_section = self.field.section(z)

            # Compute all properties for current section
            props = section_full_analysis(current_section, alpha=alpha)

            for key in keys_to_plot:
                if key not in props:
                    # Keep alignment with z_values even when key is missing
                    data_series[key].append(np.nan)
                    data_series_right[key].append(np.nan)
                    continue

                raw = props[key]

                # Generic pair detection: any 2-item sequence is treated as (left, right)
                is_pair = isinstance(raw, (tuple, list, np.ndarray)) and len(raw) == 2

                if is_pair:
                    # Left channel
                    v_left = raw[0]
                    if v_left is None:
                        v_left = np.nan
                    else:
                        v_left = float(v_left)
                        if abs(v_left) < EPS_L:
                            v_left = 0.0

                    # Right channel
                    v_right = raw[1]
                    if v_right is None:
                        v_right = np.nan
                    else:
                        v_right = float(v_right)
                        if abs(v_right) < EPS_L:
                            v_right = 0.0

                    data_series[key].append(v_left)
                    data_series_right[key].append(v_right)

                else:
                    # Legacy scalar path (left only)
                    v = raw
                    if v is None:
                        v = np.nan
                    else:
                        v = float(v)
                        if abs(v) < EPS_L:
                            v = 0.0

                    data_series[key].append(v)
                    data_series_right[key].append(np.nan)

        # -------------------------------------------------------------------------
        # 2) Build one subplot per key
        # -------------------------------------------------------------------------
        num_keys = len(keys_to_plot)
        fig, axes = plt.subplots(num_keys, 1, figsize=(10, 2.2 * num_keys), sharex=True)
        if num_keys == 1:
            axes = [axes]

        colors = plt.cm.viridis(np.linspace(0, 0.9, num_keys))

        # Console report header
        print("\n=== PROPERTIES MIN/MAX REPORT ===")
        print(f"z range: [{z_start:.6f}, {z_end:.6f}] | sampled points: {num_points}")

        for i, (key, color) in enumerate(zip(keys_to_plot, colors)):
            ax = axes[i]

            # Left channel data and finite mask
            y_left = np.asarray(data_series[key], dtype=float)
            finite_left = np.isfinite(y_left)

            # Right channel data and finite mask
            y_right = np.asarray(data_series_right[key], dtype=float)
            finite_right = np.isfinite(y_right)
            has_right = bool(np.any(finite_right))

            # Extract right-channel endpoint values (used for left top text: t(z0), t(z1))
            t_start_txt = None
            t_end_txt = None
            if has_right:
                idx_right = np.where(finite_right)[0]
                if idx_right.size > 0:
                    i0 = int(idx_right[0])    # first finite right sample
                    i1 = int(idx_right[-1])   # last finite right sample
                    t_start_txt = float(y_right[i0])
                    t_end_txt = float(y_right[i1])

            # ---------------------------------------------------------------------
            # Case A: no valid left data
            # ---------------------------------------------------------------------
            if y_left.size == 0 or not np.any(finite_left):
                ax.plot(z_values, y_left, color=color, linewidth=2)
                ax.set_ylabel(key, fontweight="bold")
                ax.grid(True, linestyle=":", alpha=0.6)

                # Right-top text: status only (kept on the right)
                title_right = f"{key}: no valid left-axis data"
                ax.text(
                    0.995, 1.01, title_right,
                    transform=ax.transAxes,
                    ha="right", va="bottom",
                    fontsize=9,
                    clip_on=False
                )

                # Left-top text: t endpoints only (requested behavior)
                if t_start_txt is not None and t_end_txt is not None:
                    title_left_t = f"t(z0)={t_start_txt:.6g}  t(z1)={t_end_txt:.6g}"
                    ax.text(
                        0.005, 1.01, title_left_t,
                        transform=ax.transAxes,
                        ha="left", va="bottom",
                        fontsize=9,
                        clip_on=False,
                        wrap=True,
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.2)
                    )

                print(f"{key}: no valid left-axis data")

                # Plot right channel if present
                if has_right:
                    ax_r = ax.twinx()
                    ax_r.plot(z_values, y_right, linestyle="--", linewidth=1.5)
                    #ax_r.set_ylabel(f"{key} (right)", fontweight="bold")
                    ax_r.grid(False)

                    # Console min/max for right channel
                    y_rf = y_right[finite_right]
                    z_rf = z_values[finite_right]
                    i_min_r = int(np.argmin(y_rf))
                    i_max_r = int(np.argmax(y_rf))
                    v_min_r = float(y_rf[i_min_r])
                    v_max_r = float(y_rf[i_max_r])
                    z_min_r = float(z_rf[i_min_r])
                    z_max_r = float(z_rf[i_max_r])

                    print(
                        f"{key} [right]: min={v_min_r:.12g} at z={z_min_r:.12g} | "
                        f"max={v_max_r:.12g} at z={z_max_r:.12g}"
                    )
                continue

            # ---------------------------------------------------------------------
            # Case B: valid left data
            # ---------------------------------------------------------------------
            y_lf = y_left[finite_left]
            z_lf = z_values[finite_left]

            i_min_l = int(np.argmin(y_lf))
            i_max_l = int(np.argmax(y_lf))

            v_min_l = float(y_lf[i_min_l])
            v_max_l = float(y_lf[i_max_l])
            z_min_l = float(z_lf[i_min_l])
            z_max_l = float(z_lf[i_max_l])

            # Plot left curve
            ax.plot(z_values, y_left, color=color, linewidth=2)

            # Mark min/max on left channel
            ax.scatter([z_min_l], [v_min_l], marker="v", s=26, zorder=3)
            ax.scatter([z_max_l], [v_max_l], marker="^", s=26, zorder=3)

            # Annotate left min/max values near markers
            if np.isclose(v_min_l, v_max_l):
                ax.annotate(
                    f"{v_min_l:.4g}",
                    (z_min_l, v_min_l),
                    textcoords="offset points",
                    xytext=(4, 6),
                    fontsize=7,
                )
            else:
                ax.annotate(
                    f"{v_min_l:.4g}",
                    (z_min_l, v_min_l),
                    textcoords="offset points",
                    xytext=(4, -12),
                    fontsize=7,
                )
                ax.annotate(
                    f"{v_max_l:.4g}",
                    (z_max_l, v_max_l),
                    textcoords="offset points",
                    xytext=(4, 6),
                    fontsize=7,
                )

            # Left y-axis limits with margin
            if v_max_l != v_min_l:
                margin_l = (v_max_l - v_min_l) * 0.10
            else:
                margin_l = max(abs(v_max_l) * 0.05, 0.1)
            ax.set_ylim(v_min_l - margin_l, v_max_l + margin_l)

            ax.set_ylabel(key, fontweight="bold")
            ax.grid(True, linestyle=":", alpha=0.6)

            # Right-top text: min/max summary (unchanged side)
            title_right = (
                f"{key}: min={v_min_l:.6g}@z={z_min_l:.6g}  max={v_max_l:.6g}@z={z_max_l:.6g}"
            )
            ax.text(
                0.995, 1.01, title_right,
                transform=ax.transAxes,
                ha="right", va="bottom",
                fontsize=9,
                clip_on=False
            )

            # Left-top text: only t(z0), t(z1)
            if t_start_txt is not None and t_end_txt is not None:
                title_left_t = f"t(z0)={t_start_txt:.6g}  t(z1)={t_end_txt:.6g}"
                ax.text(
                    0.0015, 1.01, title_left_t,
                    transform=ax.transAxes,
                    ha="left", va="bottom",
                    fontsize=9,
                    clip_on=False,
                    wrap=True,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.2)
                )
                            # Console min/max for left channel
            print(
                f"{key}: min={v_min_l:.12g} at z={z_min_l:.12g} | "
                f"max={v_max_l:.12g} at z={z_max_l:.12g}"
            )

            # Plot right channel if present
            if has_right:
                ax_r = ax.twinx()
                ax_r.plot(z_values, y_right, linestyle="--", linewidth=1.5)
                #ax_r.set_ylabel(f"{key} (right)", fontweight="bold")
                ax_r.grid(False)

                # Console min/max for right channel
                y_rf = y_right[finite_right]
                z_rf = z_values[finite_right]

                i_min_r = int(np.argmin(y_rf))
                i_max_r = int(np.argmax(y_rf))

                v_min_r = float(y_rf[i_min_r])
                v_max_r = float(y_rf[i_max_r])
                z_min_r = float(z_rf[i_min_r])
                z_max_r = float(z_rf[i_max_r])

                print(
                    f"{key} [right]: min={v_min_r:.12g} at z={z_min_r:.12g} | "
                    f"max={v_max_r:.12g} at z={z_max_r:.12g}"
                )

        print("=== END PROPERTIES MIN/MAX REPORT ===\n")

        axes[-1].set_xlabel(f"Z coordinate")

        # Reserve top margin for top-left/top-right text lines
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()


    
    # -----------------------------------------------------------------------------------------------------------------------------------------
    def plot_section_2d(
        self,
        z: float,
        show_ids: bool = True,
        show_weights: bool = True,
        show_vertex_ids: bool = False,
        title: Optional[str] = None,
        ax=None,
    ):
        """
        Draw the 2D section at a given longitudinal coordinate z.

        This implementation places the legend BELOW the plot and computes layout
        dynamically from real rendered sizes (no fixed "magic" vertical offsets).

        Why this version is robust
        --------------------------
        - Legend is anchored in FIGURE coordinates, not AXES coordinates.
        - After first draw, legend height is measured from renderer bbox.
        - Bottom subplot margin is then adjusted to reserve exactly enough space.
        - Legend is finally repositioned inside that reserved strip.

        Result:
        - No overlap between legend and axes.
        - No clipping/cut-off of legend text.
        - Works with different font sizes, DPI, and label lengths.
        """
        #print(f"DEBUG show_vertex_ids {show_vertex_ids} show_ids {show_ids} ")
        # Local imports keep the method self-contained as a drop-in replacement.
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.legend_handler import HandlerTuple

        sec = self.field.section(z)

        created_new_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            created_new_fig = True
        else:
            fig = ax.figure

        # Store one color per section polygon (same order as sec.polygons).
        poly_colors = []

        # -------------------------------------------------------------------------
        # 1) Plot polygon outlines
        # -------------------------------------------------------------------------
        for idx, poly in enumerate(sec.polygons):
            xs = [p.x for p in poly.vertices]
            ys = [p.y for p in poly.vertices]

            # Close polyline only if needed.
            if len(poly.vertices) >= 2:
                x0, y0 = poly.vertices[0].x, poly.vertices[0].y
                xN, yN = poly.vertices[-1].x, poly.vertices[-1].y
                if (x0, y0) != (xN, yN):
                    xs.append(x0)
                    ys.append(y0)

            line, = ax.plot(xs, ys, linewidth=1, zorder=2)
            color = line.get_color()
            poly_colors.append(color)

            # Optional vertex numbering inside axes.
            if show_vertex_ids:
                for v_idx, v in enumerate(poly.vertices, start=1):
                    ax.text(
                        v.x,
                        v.y,
                        f" {v_idx}",
                        color=color,
                        fontsize=9,
                        fontweight="bold",
                        zorder=4,
                    )
            # Optional polygon id inside axes (placed at simple vertex-mean center)
            if show_ids and len(poly.vertices) > 0:
                cx = sum(p.x for p in poly.vertices) / float(len(poly.vertices))
                cy = sum(p.y for p in poly.vertices) / float(len(poly.vertices))
                ax.text(
                    cx,
                    cy,
                    f"ID={idx}",
                    color=color,
                    fontsize=10,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    zorder=5,
                )


        # -------------------------------------------------------------------------
        # 2) Compute container mapping (S0-aware, then remapped to current section)
        # -------------------------------------------------------------------------
        sec_name_to_idx = {getattr(p, "name", None): i for i, p in enumerate(sec.polygons)}
        s0_name_to_idx = {getattr(p, "name", None): i for i, p in enumerate(self.field.s0.polygons)}

        container_id_by_sec = [None] * len(sec.polygons)
        child_s0_idx_by_sec = [None] * len(sec.polygons)

        for idx, poly in enumerate(sec.polygons):
            container_id = None
            child_s0_idx = None

            try:
                child_name = getattr(poly, "name", None)
                child_s0_idx = s0_name_to_idx.get(child_name)

                if child_s0_idx is not None:
                    parent_s0_idx = self.field.get_container_polygon_index(
                        self.field.s0.polygons[child_s0_idx],
                        child_s0_idx,
                    )
                    if parent_s0_idx is not None:
                        parent_name = getattr(self.field.s0.polygons[parent_s0_idx], "name", None)
                        container_id = sec_name_to_idx.get(parent_name)

            except Exception:
                # Keep plotting resilient even if containment query fails.
                container_id = None
                child_s0_idx = None

            container_id_by_sec[idx] = container_id
            child_s0_idx_by_sec[idx] = child_s0_idx

        # -------------------------------------------------------------------------
        # 3) Reconstruct absolute weights at z from relative weights + container chain
        # -------------------------------------------------------------------------
        w_rel_z = [float(getattr(p, "weight", 0.0)) for p in sec.polygons]
        w_abs_z_cache = {}

        def _w_abs_z(i: int) -> float:
            if i in w_abs_z_cache:
                return w_abs_z_cache[i]
            parent = container_id_by_sec[i]
            if parent is None:
                w_abs_z_cache[i] = w_rel_z[i]
            else:
                w_abs_z_cache[i] = w_rel_z[i] + _w_abs_z(parent)
            return w_abs_z_cache[i]

        w_abs_z = [_w_abs_z(i) for i in range(len(sec.polygons))]
        _ = w_abs_z  # currently used by optional legend blocks only

        # -------------------------------------------------------------------------
        # 4) Build legend entries (relative weights + container id)
        # -------------------------------------------------------------------------
        legend_handles = []
        legend_labels = []

        for idx, poly in enumerate(sec.polygons):
            container_id = container_id_by_sec[idx]

            # Child handle
            h_poly = Line2D([0], [0], color=poly_colors[idx], linewidth=5.0)

            # If container exists, legend handle is a tuple (child, container)
            if container_id is not None and 0 <= container_id < len(poly_colors):
                h_container = Line2D([0], [0], color=poly_colors[container_id], linewidth=5.0)
                legend_handles.append((h_poly, h_container))
            else:
                legend_handles.append(h_poly)

            name = (getattr(poly, "name", None) or f"poly_{idx}").strip()

            label = (
                f"ID={idx}  "
                f"w={w_rel_z[idx]:g}  "
                f"{name}  "
                f"container={container_id if container_id is not None else 'None'}"
            )
            #print(f"DEBUG legend_label={repr(label)}")
            legend_labels.append(label)

        # -------------------------------------------------------------------------
        # 5) Axes style
        # -------------------------------------------------------------------------
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, linestyle=":", alpha=0.5, zorder=1)

        if title is None:
            title = f"Section at z={z:g}"
        ax.set_title(title)


        if ax is None:
            fig, ax = plt.subplots(constrained_layout=True)
            created_new_fig = True
        else:
            fig = ax.figure
            try:
                fig.set_constrained_layout(True)
            except Exception:
                pass


        # -------------------------------------------------------------------------
        # 6) Legend below axes (axes-anchored, no overlap with X label)
        # -------------------------------------------------------------------------
        leg = ax.legend(
            legend_handles,
            legend_labels,
            loc="upper center",                 # top-center of legend box
            bbox_to_anchor=(0.5, -0.16),        # place below axes
            bbox_transform=ax.transAxes,        # anchor in AXES coordinates
            borderaxespad=0.0,
            frameon=True,
            title="Polygons (w is relative)",
            handler_map={tuple: HandlerTuple(ndivide=None)},
            ncol=1,
        )

        # -------------------------------------------------------------------------
        # 7) Final draw (no manual subplots_adjust needed)
        # -------------------------------------------------------------------------
        fig.canvas.draw()




        return ax






    def plot_volume_3d(self, show_end_sections: bool = True, line_percent: float = 100.0,
                       seed: int = 0, title: str = "Ruled volume (vertex-connection lines)", ax=None):
        """
        Draw the 3D ruled "skeleton":
        - endpoint section outlines (optional)
        - straight lines connecting corresponding vertices (ruled generators)
        - ability to display only a percentage of those lines for readability

        line_percent:
          0..100 : percentage of connection lines shown (random subsample).
        """
        if not (0.0 <= line_percent <= 100.0):
            raise ValueError("line_percent must be within [0, 100].")
            
        # 2. AXES INITIALIZATION
        # If no existing axis is provided, create a new 3D figure with a default perspective.
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
            ax.view_init(elev=15, azim=120)

        # 3. GEOMETRY EXTRACTION
        # Get endpoint sections at the field's start (z0) and end (z1).
        z0, z1 = self.field.z0, self.field.z1
        s0 = self.field.section(z0)
        s1 = self.field.section(z1)

        # 4. DRAW END SECTIONS
        # If show_end_sections is True, plot the perimeter of all polygons at Z0 and Z1.
        # This helps visualize the boundary transition of the ruled
        if show_end_sections:
            for sec in (s0, s1):
                for poly in sec.polygons:
                    xs = [p.x for p in poly.vertices] + [poly.vertices[0].x]
                    ys = [p.y for p in poly.vertices] + [poly.vertices[0].y]
                    zs = [sec.z] * len(xs)
                    ax.plot(xs, ys, zs)
        # 5. BUILD GENERATOR LINES
        # Create a list of all straight lines (ruled generators) connecting
        # each vertex in the start section to its corresponding vertex in the end section.
            all_lines = []
        for p0, p1 in zip(s0.polygons, s1.polygons):
            for v0, v1 in zip(p0.vertices, p1.vertices):
                all_lines.append((v0, v1))

        # 6. SUBSAMPLING (Visual Clarity)
        # If line_percent < 100, we randomly select a subset of lines to avoid visual clutter.
        # Using a fixed 'seed' ensures the same set of lines is picked every time (reproducibility).
        if line_percent < 100.0:
            rng = random.Random(seed)
            k = int(math.ceil(len(all_lines) * (line_percent / 100.0)))
            k = max(0, min(k, len(all_lines)))
            all_lines = rng.sample(all_lines, k)

        # 7. PLOTTING
        # Draw the connection lines between the two Z-planes.
        for v0, v1 in all_lines:
            ax.plot([v0.x, v1.x], [v0.y, v1.y], [z0, z1],linewidth=0.7)

        # Draw axes labels
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)

        # Improve scaling
        _set_axes_equal_3d(ax)
        return ax


# ============================================================
# Example: Continuous Section Field – Static Properties Demo
# ============================================================
#
# This script demonstrates how to:
# - define polygonal cross-sections,
# - interpolate them along a longitudinal axis (Z),
# - compute geometric and static properties,
# - visualize both 2D sections and the 3D ruled solid.
#
# The example uses a tapered T-section composed of:
# - a flange polygon
# - a web polygon
#
# Coordinate system:
#   X → horizontal
#   Y → vertical
#   Z → longitudinal
#
# NOTE:
# A negative centroid Y-coordinate (Cy) is expected in this example
# because most of the section area lies below the global X-axis.
#
# ============================================================


if __name__ == "__main__":

    # --------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 0)
    # --------------------------------------------------------
    # The start section is a T-shape composed of two polygons:
    # - flange (horizontal plate)
    # - web (vertical plate)


    # Define start polygons (T-Section at Z=0)
    poly0_start = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web Definition: Rectangle from (-0.2, -1.0) to (0.2, 0.2)
    # Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left (CCW)
    poly1_start = Polygon(
        vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0),  Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

    # --------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 10)
    # --------------------------------------------------------
    # The flange remains unchanged.
    # The web depth increases linearly from 1.0 to 2.5,
    # producing a tapered T-section along the Z-axis.

    poly0_end = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web becomes deeper: Y-bottom moves from -1.0 to -2.5
    # MAINTAIN CCW ORDER: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left
    poly1_end = Polygon(
        vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

      # --------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # --------------------------------------------------------
    # Each Section groups polygons and assigns a Z position.

    s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)

    # --------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.
    field = ContinuousSectionField(section0=s0, section1=s1)

    # --------------------------------------------------------
    # 5 Print Analysis
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.


    sec= field.section(10.0)
    full_analysis = section_full_analysis(sec)
    section_print_analysis(full_analysis)
    print(f"Area (A):               {full_analysis['A']:.4f}      # Net area")

    # --------------------------------------------------------
    # 6. VISUALIZATION
    # --------------------------------------------------------
    # - 2D section plot at Z = 5.0
    # - 3D ruled solid visualization
    viz = Visualizer(field)
    # Generate 2D plot for the specified slice
    viz.plot_section_2d(z=10.0)
    # Generate 3D plot of the interpolated solid
    # line_percent determines the density of the longitudinal ruled lines
    viz.plot_volume_3d(line_percent=100.0, seed=1)
    plt.show()
    


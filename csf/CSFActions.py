"""
CSFReader_ver_W.py
================

User-facing runner for CSF using two declarative YAML files:

  1) geometry.yaml  -> CSF geometry (validated + loaded by CSFReader)
  2) actions.yaml   -> actions plan (FULL validation required before execution)

Design goals
------------
- This tool is meant for NON-Python users.
- Errors must be clear, friendly, and actionable.
- No raw Python tracebacks by default.
- YAML errors should show a short snippet with line numbers and a caret pointer.
- Warnings do NOT require snippets (per project spec).

Scope (v0.1)
------------
- Load geometry.yaml via CSFReader (and always print CSFReader issues).
- Load + FULL-validate actions.yaml against a flexible "action spec" catalog:
    * stations: REQUIRED
    * actions:  REQUIRED
    * each action item: a dict with exactly one action key
    * common action envelope:
        - stations (REQUIRED): list of station names
        - output   (OPTIONAL): list[str] default ["stdout"]
        - params   (OPTIONAL): mapping; action-specific
    * station lists: YAML list of numbers
        - WARNING if not sorted ascending
        - WARNING if duplicates are found
- Execute actions in order.
  For now, only 'section_full_analysis' is implemented.
  Other actions are placeholders and will stop the run with a controlled error.

Implemented action: section_full_analysis
-----------------------------------------
Wraps ready-made library functions:

    from csf.section_field import section_full_analysis, section_print_analysis

Behavior:
- Expand z-values from the selected station sets.
- For each z:
    - compute section = field.section(z)
    - compute full_analysis = section_full_analysis(section)
    - print report using section_print_analysis(full_analysis, fmt=...)
- Output routing:
    - stdout: prints human report
    - file ending with ".csv": writes tabular CSV (z + analysis keys)
    - any other file: writes text report (captured print output)

Action params (v0.1)
--------------------
section_full_analysis.params:
  - fmt_display (OPTIONAL) : str, default ".8f"
      Python format for displaying numbers in the printed report.
      Example: ".4f", ".4e"
      NOTE: if the user writes fmt_display: =".4f" we strip the leading '=' with a WARNING.

Help
----
- --help-actions prints the action catalog and parameters to stdout.

Usage
-----
python CSFActions.py geometry.yaml actions.yaml
python CSFActions.py --help-actions

Development convenience:
- If you run the script with no CLI args, it falls back to:
    geometry=case.yaml
    actions=actions_example.yaml

"""

from __future__ import annotations
import sys
import argparse
import csv
import io
import os
import re
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple



import argparse
import csv
import io
import os
import re
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
import numpy as np 
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues, Issue, Severity

# The analysis/printing functions are defined at module level in section_field.py.
# Adjust the import path if your package layout differs.
try:
    from csf.section_field import (
        ContinuousSectionField,
        section_full_analysis,
        section_full_analysis_keys,
        section_print_analysis,
        Visualizer,
        safe_evaluate_weight_zrelative,
        write_opensees_geometry,
        write_sap2000_template_pack,
        polygon_surface_w1_inners0,
    )
except Exception:
    # If imports fail, we keep them as None and emit a friendly error later.
    ContinuousSectionField = None  # type: ignore
    section_full_analysis = None  # type: ignore
    section_full_analysis_keys = None  # type: ignore
    section_print_analysis = None  # type: ignore
    Visualizer = None  # type: ignore
    safe_evaluate_weight_zrelative = None  # type: ignore
    write_opensees_geometry = None  # type: ignore
    polygon_surface_w1_inners0 = None  # type: ignore
 # type: ignore

try:
    from PIL import Image  # type: ignore
    import matplotlib
    import matplotlib.pyplot as plt  # type: ignore
    
except Exception as e:
    raise RuntimeError(f"Missing plotting dependencies (pillow/matplotlib): {e}")

# ---------------------------------------------------------------------------
# Actions catalog (flexible schema)
# ---------------------------------------------------------------------------

TOP_KEY = "CSF_ACTIONS"

# ---------------------------------------------------------------------------
# Deferred matplotlib display (development prototype)
#
# The runner intentionally does NOT call plt.show() inside each plotting action.
# Instead, plotting actions just create figures and set one of these global flags.
# At the very end of main(), we decide which figure groups to keep and show.
#
# NOTE: These globals are intentionally kept as-is (simple strings/None) because
# other development code may rely on this exact structure.
# ---------------------------------------------------------------------------
want_show_2d = None
want_show_3d = None

# Figure labels used by the deferred-show logic.
# If new plotting actions are added, extend these lists rather than changing
# the global-flag mechanism.
# 2D figure visibility registry (development prototype)
#
# Each plotting action labels the figures it creates. At the end of the run we:
#   - close whole groups if the corresponding action never ran
#   - additionally close file-only figures (not meant to be shown)
#
# Convention used by plot_section_2d:
#   - 'plot2d_show'  -> keep for the final interactive plt.show()
#   - 'plot2d_file'  -> save to file only, close before plt.show()
PLOT_2D_VISIBILITY = {
    'plot2d_show': True,
    'plot2d_file': False,
}

# Legacy label 'plot2d' is kept for backward compatibility.
PLOT_2D_LABELS = ['plot2d', 'plot2d_show', 'plot2d_file']
# 3D figure visibility registry (development prototype)
#
# Convention for plot-producing actions:
#   - 'plot3d_show' -> keep for the final interactive display
#   - 'plot3d_file' -> save to file only, close before interactive display (currently unused)
#
# Legacy label 'plot3d' is kept for backward compatibility with older actions.
PLOT_3D_VISIBILITY = {
    'plot3d': True,
    'plot3d_show': True,
    'plot3d_file': False,
}

PLOT_3D_LABELS = ['plot3d', 'plot3d_show', 'plot3d_file']
PolyPair = Tuple[str, str]
#######################################################################

def csf_weight_catalog_by_pair(field: Any, *, include_default_linear: bool = True) -> Dict[PolyPair, Dict[str, Any]]:
    """
    Build a catalog of polygon weights/laws, grouped by the polygon-name pair (S0_name, S1_name).

    Returns a dict:
        {
          (name0, name1): {
              "index": i+1,
              "w0": <float>,          # endpoint weight in section S0
              "w1": <float>,          # endpoint weight in section S1
              "law": <str|None>,      # custom weight law expression (if any)
              "effective": <str>,     # "linear" if no custom law (and include_default_linear=True)
          },
          ...
        }
    """
    if not hasattr(field, "s0") or not hasattr(field, "s1"):
        raise TypeError("field must expose .s0 and .s1 sections.")
    if not hasattr(field.s0, "polygons") or not hasattr(field.s1, "polygons"):
        raise TypeError("field.s0 and field.s1 must expose .polygons.")

    p0_list = list(field.s0.polygons)
    p1_list = list(field.s1.polygons)

    if len(p0_list) != len(p1_list):
        raise ValueError(f"Endpoint polygon count mismatch: {len(p0_list)} vs {len(p1_list)}")

    laws = getattr(field, "weight_laws", None)

    def _get_law_for_index(idx1: int, name0: str) -> Optional[str]:
        """idx1 is 1-based polygon index (same convention used by field.section())."""
        if laws is None:
            return None
        # Most common case in your code: dict keyed by 1-based index -> str
        if isinstance(laws, dict):
            v = laws.get(idx1)
            if v is None:
                # Defensive fallback: some older variants might have name-keys
                v = laws.get(name0)
            return None if v is None else str(v)

        # Rare case: list; your field.section() attempts 1-based access (laws[idx1]).
        if isinstance(laws, list):
            v = None
            if 0 <= idx1 < len(laws):
                v = laws[idx1]  # 1-based style
            elif 0 <= (idx1 - 1) < len(laws):
                v = laws[idx1 - 1]  # 0-based fallback
            return None if v is None else str(v)

        return None

    out: Dict[PolyPair, Dict[str, Any]] = {}

    for i, (p0, p1) in enumerate(zip(p0_list, p1_list)):
        idx1 = i + 1
        name0 = str(getattr(p0, "name", f"poly_{idx1}"))
        name1 = str(getattr(p1, "name", f"poly_{idx1}"))

        w0 = float(getattr(p0, "weight", 1.0))
        w1 = float(getattr(p1, "weight", 1.0))

        law = _get_law_for_index(idx1, name0)
        effective = (law if law is not None else ("linear" if include_default_linear else None))

        out[(name0, name1)] = {
            "index": idx1,
            "w0": w0,
            "w1": w1,
            "law": law,
            "effective": effective,
        }

    return out


def csf_weights_by_pair_at_z(field: Any, z: float) -> Dict[PolyPair, float]:
    """
    Compute the actual interpolated weights w(z) at absolute coordinate z, grouped by (S0_name, S1_name).

    Returns:
        { (name0, name1): w_at_z, ... }
    """
    if not hasattr(field, "section"):
        raise TypeError("field must expose section(z).")

    sec = field.section(float(z))
    if not hasattr(sec, "polygons"):
        raise TypeError("field.section(z) must return an object exposing .polygons.")

    # Names in computed section are taken from S0 in your implementation.
    # Pairing back to S1 is done by index (homology assumption).
    p0_list = list(field.s0.polygons)
    p1_list = list(field.s1.polygons)
    sp_list = list(sec.polygons)

    if not (len(p0_list) == len(p1_list) == len(sp_list)):
        raise ValueError(
            "Polygon count mismatch among S0, S1 and computed section at z. "
            f"len(S0)={len(p0_list)}, len(S1)={len(p1_list)}, len(Sz)={len(sp_list)}"
        )

    out: Dict[PolyPair, float] = {}
    for i, (p0, p1, pz) in enumerate(zip(p0_list, p1_list, sp_list)):
        name0 = str(getattr(p0, "name", f"poly_{i+1}"))
        name1 = str(getattr(p1, "name", f"poly_{i+1}"))
        w = float(getattr(pz, "weight", float("nan")))
        out[(name0, name1)] = w

    return out

class RawTextDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass



@dataclass
class ParamSpec:
    """
    Specification for one action parameter under action.params.
    """
    name: str
    required: bool
    typ: str  # "str" | "int" | "float" | "bool" | "dict" | "list"
    default: Any = None
    description: str = ""
    aliases: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionSpec:
    """
    Specification for one action (name + params schema + documentation).
    """
    name: str
    summary: str
    description: str
    params: Tuple[ParamSpec, ...] = ()


# IMPORTANT:
# - We keep a stable "common envelope" for every action: stations/output/params.
# - Action-specific parameters live under params and are validated by ParamSpec.
ACTION_SPECS: Dict[str, ActionSpec] = {
    "section_full_analysis": ActionSpec(
        name="section_full_analysis",
        summary="Compute a full (weighted) section property report at one or more stations.",
        description=(
            "Computes the complete section property set at each requested station z and renders a report.\n"
            "\n"
            "YAML fields\n"
            "- stations: REQUIRED. One or more station-set names defined under CSF_ACTIONS.stations (absolute z).\n"
            "- output:  OPTIONAL. Default is [stdout]. Add file paths to write reports/tables to disk.\n"
            "          If output does NOT include 'stdout', the action is file-only.\n"
            "\n"
            "Outputs\n"
            "- stdout : human-readable report per station.\n"
            "- *.csv  : numeric table (z + all reported keys).\n"
            "- other : captured text report (written to the given path).\n"
            "\n"
            "Modeling note (scope)\n"
            "- All reported properties are intended for slender-beam (Euler–Bernoulli) member models.\n"
            "  CSF does not model local effects, shear deformation, or 3D continuum behavior."
        ),
        params=(
            ParamSpec(
                name="fmt_display",  # NOTE: keep spelling as requested
                required=False,
                typ="str",
                default=".8f",
                description="Python format spec used by section_print_analysis (e.g. '.4f', '.4e').",
                aliases=("fmt_display",),  # we accept the more correct spelling as alias
            ),
        ),
    ),




    "weight_lab": ActionSpec(
        name="weight_lab",
        summary="Placeholder: weight-law exploration (not implemented in this runner).",
        description=(
            "Reserved action name for future weight-law reporting tools.\n"
            "\n"
            "Status\n"
            "- Not implemented in this CSFActions runner version.\n"
            "- If you need weight-law inspection, use: weight_lab_zrelative or plot_weight."
        ),
        params=(),
    ),




    "plot_volume_3d": ActionSpec(
        name="plot_volume_3d",
        summary="Plot a 3D ruled volume preview between the two end sections.",
        description=(
            "Shows a 3D visualization of the ruled volume (vertex-connection generator lines) between field endpoints.\n"
            "\n"
            "YAML fields\n"
            "- stations: NOT USED (forbidden). This action always uses the field endpoints (z0, z1).\n"
            "- output:   stdout only. The visualization is shown interactively at the end of the run.\n"
            "\n"
            "Params\n"
            "- show_end_sections : draw end-section outlines at z0 and z1.\n"
            "- line_percent      : percentage (0..100) of generator lines displayed (random subsample).\n"
            "- seed              : RNG seed used when line_percent < 100.\n"
            "- title             : window/figure title."
        ),
        params=(
            ParamSpec(
                name="show_end_sections",
                required=False,
                typ="bool",
                default=True,
                description="If True, draws the end section outlines at z0 and z1.",
            ),
            ParamSpec(
                name="line_percent",
                required=False,
                typ="float",
                default=100.0,
                description="0..100 percentage of generator lines shown (random subsample).",
            ),
            ParamSpec(
                name="seed",
                required=False,
                typ="int",
                default=0,
                description="Random seed used when line_percent < 100.",
            ),
            ParamSpec(
                name="title",
                required=False,
                typ="str",
                default="Ruled volume (vertex-connection lines)",
                description="Plot title.",
            ),
        ),
    ),


    "plot_properties": ActionSpec(
        name="plot_properties",
        summary="Plot selected section properties along z (field sampling between endpoints).",
        description=(
            "Plots the evolution of one or more section properties along the member axis by sampling the field.\n"
            "\n"
            "YAML fields\n"
            "- stations:    NOT USED (forbidden). This action samples internally between z0 and z1.\n"
            "- properties:  REQUIRED. List of property keys to plot (e.g. ['A','Ix','Iy','J']).\n"
            "- output:      OPTIONAL. Default is [stdout] (show a window at end of run, if supported).\n"
            "              If output contains file path(s), the plot is saved to disk.\n"
            "              If output does NOT include 'stdout', the action is file-only.\n"
            "\n"
            "Params\n"
            "- num_points: number of sampling points between z0 and z1."
        ),
        params=(
            ParamSpec(
                name="num_points",
                required=False,
                typ="int",
                default=100,
                description="Number of sampling points along Z between z0 and z1.",
            ),
        ),
    ),


    "plot_weight": ActionSpec(
        name="plot_weight",
        summary="Plot interpolated polygon weights w(z) along the field axis.",
        description=(
            "Plots polygon weight values w(z) along the member axis by sampling between z0 and z1.\n"
            "\n"
            "YAML fields\n"
            "- stations: NOT USED (forbidden). This action samples internally between endpoints.\n"
            "- output:   OPTIONAL. Default is [stdout] (show a window at end of run, if supported).\n"
            "           If output contains file path(s), the plot is saved to disk.\n"
            "           If output does NOT include 'stdout', the action is file-only.\n"
            "\n"
            "Params\n"
            "- num_points: number of sampling points between z0 and z1."
        ),
        params=(
            ParamSpec(
                name="num_points",
                required=False,
                typ="int",
                default=100,
                description="Number of sampling points along Z between z0 and z1.",
            ),
        ),
    ),


    "weight_lab_zrelative": ActionSpec(
        name="weight_lab_zrelative",
        summary="Inspect weight-law expressions at user-provided *relative* z stations (text-only).",
        description=(
            "Text-only inspector for custom weight laws evaluated at user-provided stations, interpreted as *relative* z.\n"
            "\n"
            "Expression environment\n"
            "- z  : relative coordinate along the element (provided by the station set)\n"
            "- L  : total element length (computed as field.s1.z - field.s0.z)\n"
            "- np : numpy namespace (np.sin, np.cos, np.pi, ...)\n"
            "\n"
            "YAML fields\n"
            "- stations:   REQUIRED. Interpreted as relative z values (user responsibility).\n"
            "- weith_law:  REQUIRED. List[str] of expressions to evaluate (kept outside params; spelling preserved).\n"
            "- output:     OPTIONAL. Default is [stdout]. Add file paths to write the full inspector text.\n"
            "\n"
            "Outputs\n"
            "- stdout : prints the inspector report.\n"
            "- file   : writes the inspector report (file-only if stdout not requested).\n"
            "\n"
            "Notes\n"
            "- This action is intended to verify/debug expressions without writing Python.\n"
            "- The evaluation uses the same safe-evaluator used by the field."
        ),
        params=(),
    ),


    "write_opensees_geometry": ActionSpec(
        name="write_opensees_geometry",
        summary="Export an OpenSees Tcl geometry file (sections + stations) for forceBeamColumn workflows.",
        description=(
            "Writes a Tcl file that can be consumed by OpenSees/OpenSeesPy beam models built from a station list.\n"
            "\n"
            "YAML fields\n"
            "- stations: OPTIONAL. If provided, use this named station set (absolute z values).\n-           If omitted, stations are generated from n_intervals (Lobatto).\n"
            "- output:   REQUIRED. File-only: exactly one Tcl path (*.tcl). 'stdout' is forbidden.\n"
            "\n"
            "Params (required)\n"
            "- n_points (int) : number of sampling / integration points along the member (stations = n_points).\n"
            "- E_ref (float)  : reference Young's modulus written into exported Elastic sections.\n"
            "- nu (float)     : Poisson ratio; the exporter uses isotropic elasticity (G derived from E_ref and nu).\n"
            "\n"
            "Material/weight contract (important)\n"
            "- CSF section properties exported by this action are assumed to be already *modular/weighted*.\n"
            "- Provide a physical E_ref (and nu) only once in the solver-side section definition to avoid double counting.\n"
            "\n"
            "Modeling note (scope)\n"
            "- The output is intended for slender-beam (Euler–Bernoulli) member formulations."
        ),
        params=(
            ParamSpec(
                name="n_points",
                required=True,
                typ="int",
                default=None,
                description="Number of integration/sampling points along the member (required).",
            ),
            ParamSpec(
                name="E_ref",
                required=True,
                typ="float",
                default=None,
                description="Reference Young's modulus (required).",
            ),
            ParamSpec(
                name="nu",
                required=True,
                typ="float",
                default=None,
                description="Poisson ratio (required).",
            ),
        ),
    ),


    "write_sap2000_geometry": ActionSpec(
        name="write_sap2000_geometry",
        summary="Write a SAP2000 template-pack text file (copy/paste helper) from the CSF field.",
        description=(
            "Generates a *template pack* text file that helps build a SAP2000 model for a variable section member.\n"
            "\n"
            "YAML fields\n"
            "- stations: OPTIONAL. If provided, uses explicit absolute stations; if omitted, stations are generated from n_intervals (Lobatto).\n"
            "- output:   REQUIRED. File-only: exactly one path (typically *.txt). 'stdout' is forbidden.\n"
            "\n"
            "Params (required)\n"
            "- n_intervals (int): number of Lobatto intervals (stations = n_intervals + 1).\n"
            "- E_ref (float)    : suggested physical Young's modulus for the SAP2000 material/header.\n"
            "- nu (float)       : suggested Poisson ratio (used for shear modulus derivation if needed).\n"
            "\n"
            "Params (optional)\n"
            "- material_name : label used in SAP2000 copy/paste blocks.\n"
            "- mode          : output mode: CENTROIDAL_LINE, REFERENCE_LINE, or BOTH.\n"
            "- include_plot  : if True, writes a preview PNG (when matplotlib is available).\n"
            "- plot_filename : output filename/path for the preview plot.\n"
            "\n"
            "Material/weight contract (important)\n"
            "- CSF properties are assumed to be already *modular/weighted*; E_ref should not be applied twice.\n"
            "\n"
            "Modeling note (scope)\n"
            "- Intended for slender-beam (Euler–Bernoulli) member workflows (no local/shear effects)."
        ),
        params=(
            ParamSpec(
                name="n_intervals",
                required=False,
                typ="int",
                default=None,
                description="Number of Lobatto intervals. Used when stations are not provided.",
            ),
            ParamSpec(
                name="E_ref",
                required=True,
                typ="float",
                default=None,
                description="Suggested Young's modulus written into the template header (required).",
            ),
            ParamSpec(
                name="nu",
                required=True,
                typ="float",
                default=None,
                description="Suggested Poisson ratio written into the template header (required).",
            ),
            ParamSpec(
                name="material_name",
                required=False,
                typ="str",
                default="S355",
                description="Material label used in SAP2000 copy/paste blocks.",
            ),
            ParamSpec(
                name="mode",
                required=False,
                typ="str",
                default="BOTH",
                description="Output mode: CENTROIDAL_LINE, REFERENCE_LINE, or BOTH.",
            ),
            ParamSpec(
                name="include_plot",
                required=False,
                typ="bool",
                default=True,
                description="If True, writes a preview PNG plot when matplotlib is available.",
            ),
            ParamSpec(
                name="plot_filename",
                required=False,
                typ="str",
                default="section_variation.png",
                description="PNG filename/path for the preview plot.",
            ),
        ),
    ),


}


# Actions that MUST NOT define the common field `stations:`.
# (They use only field endpoints or other special inputs.)
STATIONS_FORBIDDEN = {
    "plot_volume_3d",
    "plot_properties",
    "plot_weight",
    "write_opensees_geometry",
}
# ---------------------------------------------------------------------------
# Action runners registry (implemented actions)
# ---------------------------------------------------------------------------

# NOTE:
# - ACTION_SPECS is the validated action catalog (includes placeholders).
# - ACTION_RUNNERS contains only the actions that are actually executable in this runner.
ACTION_RUNNERS: Dict[str, Any] = {}
_ACTIONS_LOADED: bool = False


def register_action(spec: ActionSpec, runner: Any) -> None:
    """Register an executable action runner.

    This is intentionally explicit (no side-effect registration) to keep imports simple
    and to avoid circular import patterns during the modularization step.
    """
    name = spec.name
    if name in ACTION_RUNNERS:
        raise RuntimeError(f"Duplicate action runner registration: {name}")

    # Keep the spec catalog aligned with the registered runner name.
    ACTION_SPECS[name] = spec
    ACTION_RUNNERS[name] = runner



# Allowed property keys for the plot_properties action.
# This list is intentionally explicit: users get a clear error if they request
# a property that is not available / not supported by the current analysis core.
#
# NOTE: These are the keys requested by the user spec, not necessarily every key
# that might exist internally.
PLOT_PROPERTIES_ALLOWED = (
    "A",
    "Cx",
    "Cy",
    "Ix",
    "Iy",
    "Ixy",
    "J",
    "I1",
    "I2",
    "rx",
    "ry",
    "Wx",
    "Wy",
    "K_torsion",
    "Q_na",
    "J_sv",
    "J_sv_wall",
    "J_sv_cell",
    "J_s_vroark",
    "J_s_vroark_fidelity",
)


# ---------------------------------------------------------------------------
# Friendly YAML snippet helpers for errors
# ---------------------------------------------------------------------------

def _make_snippet(text: str, line_no: Optional[int], col_no: Optional[int]) -> str:
    """
    Create a short text snippet around (line, col) with line numbers.
    line_no and col_no are 1-based. If line_no is None, show first lines.
    """
    lines = text.splitlines()
    if not lines:
        return "<empty file>"

    if line_no is None:
        return "\n".join(f"{i+1:4d} | {lines[i]}" for i in range(min(8, len(lines))))

    lo = max(1, line_no - 2)
    hi = min(len(lines), line_no + 2)
    out: List[str] = []
    for k in range(lo, hi + 1):
        prefix = ">>" if k == line_no else "  "
        out.append(f"{prefix} {k:4d} | {lines[k - 1]}")
        if k == line_no and col_no is not None and col_no > 0:
            caret_pos = len(f"{prefix} {k:4d} | ") + (col_no - 1)
            out.append(" " * caret_pos + "^")
    return "\n".join(out)


def _find_key_line(text: str, key: str) -> Optional[int]:
    """
    Best-effort line lookup: find first line matching '<indent>key:'.
    """
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(#.*)?$")
    for i, raw in enumerate(text.splitlines(), start=1):
        base = raw.split("#", 1)[0].rstrip()
        if pat.match(base):
            return i
    return None


# ---------------------------------------------------------------------------
# Actions YAML parsing + corruption precheck
# ---------------------------------------------------------------------------

def _precheck_corruption_actions(text: str) -> List[Issue]:
    """
    Heuristic "corruption" check BEFORE YAML parsing.
    The goal is to catch common user mistakes and provide a friendlier message
    than the raw YAML parser.

    Current checks:
      A) Missing ':' after a key (bare token) when next line is more indented
      A0) 'key value' on one line -> missing ':'
      B) Under a stations list, a numeric line without '-' (common YAML mistake)

    Returns:
      List of ERROR issues if corruption is detected; empty list otherwise.
    """
    issues: List[Issue] = []
    lines = text.splitlines()

    # A/A0: missing ':' patterns
    for i, raw in enumerate(lines, start=1):
        base = raw.split("#", 1)[0].rstrip("\n")
        if base.strip() == "":
            continue
        if base.lstrip().startswith("-"):
            continue
        if ":" in base:
            continue

        # A0: "key value" missing ':'
        m_kv = re.match(r"^\s*([A-Za-z_][\w-]*)\s+(\S.*)\s*$", base)
        if m_kv:
            key = m_kv.group(1)
            val = m_kv.group(2)
            issues.append(
                CSFIssues.make(
                    "CSFA_E_YAML_MISSING_COLON",
                    path="$",
                    message=f"Missing ':' between key '{key}' and its value.",
                    hint=f"Use '{key}: {val}'",
                    context={"snippet": _make_snippet(text, i, 1), "location": {"line": i, "column": 1}},
                )
            )
            return issues

        # A: bare key token (likely missing ':')
        m_key = re.match(r"^\s*([A-Za-z_][\w-]*)\s*$", base)
        if not m_key:
            continue

        indent = len(base) - len(base.lstrip(" "))
        next_indent: Optional[int] = None
        j = i
        while j < len(lines):
            j += 1
            nxt = lines[j - 1].split("#", 1)[0].rstrip("\n")
            if nxt.strip() == "":
                continue
            next_indent = len(nxt) - len(nxt.lstrip(" "))
            break

        if next_indent is not None and next_indent > indent:
            key = m_key.group(1)
            issues.append(
                CSFIssues.make(
                    "CSFA_E_YAML_MISSING_COLON",
                    path="$",
                    message=f"Missing ':' after key '{key}'.",
                    hint=f"Use '{key}:'",
                    context={"snippet": _make_snippet(text, i, 1), "location": {"line": i, "column": 1}},
                )
            )
            return issues

    # B: missing '-' inside station lists (rough, but useful)
    # We look for:
    #   stations:
    #     station_name:
    #       0.0   <-- missing '-'
    station_key_line = _find_key_line(text, "stations")
    if station_key_line is not None:
        # only scan below the stations: line
        for i in range(station_key_line, len(lines) + 1):
            raw = lines[i - 1]
            base = raw.split("#", 1)[0].rstrip("\n")
            if base.strip() == "":
                continue
            # a numeric item without '-' and with indentation suggests broken list item
            m_num = re.match(r"^\s+([+-]?\d+(\.\d+)?([eE][+-]?\d+)?)\s*$", base)
            if m_num and not base.lstrip().startswith("-"):
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_YAML_LIST_MISSING_DASH",
                        path="$",
                        message="A station list item is missing '-' (YAML list marker).",
                        hint="Example:\n  station_sparse:\n    - 0.0\n    - 5.0\n    - 10.0",
                        context={"snippet": _make_snippet(text, i, 1), "location": {"line": i, "column": 1}},
                    )
                )
                return issues

    return issues


def _parse_actions_yaml(text: str, filepath: str) -> Tuple[Optional[Dict[str, Any]], List[Issue]]:
    """
    Parse actions.yaml into a Python dict, with controlled error reporting.
    """
    issues: List[Issue] = []

    # Precheck corruption first (friendlier than YAML parser)
    issues.extend(_precheck_corruption_actions(text))
    if any(i.severity == Severity.ERROR for i in issues):
        return None, issues

    try:
        import yaml  # type: ignore
    except Exception:
        issues.append(
            CSFIssues.make(
                "CSFA_E_YAML_NO_PYYAML",
                path="$",
                message="PyYAML is not available (cannot parse actions YAML).",
                hint="Install PyYAML (pip install pyyaml).",
                context={"filepath": filepath},
            )
        )
        return None, issues

    try:
        # IMPORTANT: YAML duplicate keys silently overwrite earlier values.
        # For this project we prefer a controlled, friendly error instead.
        class _UniqueKeyLoader(yaml.SafeLoader):
            pass

        def _construct_mapping(loader: Any, node: Any, deep: bool = False) -> Any:
            mapping: Dict[Any, Any] = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                if key in mapping:
                    # Raise a ConstructorError with a useful mark at the duplicate key.
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        f"found duplicate key ({key})",
                        key_node.start_mark,
                    )
                value = loader.construct_object(value_node, deep=deep)
                mapping[key] = value
            return mapping

        _UniqueKeyLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
        )

        doc = yaml.load(text, Loader=_UniqueKeyLoader)
    except Exception as e:
        line_no: Optional[int] = None
        col_no: Optional[int] = None
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            line_no = int(getattr(mark, "line", 0)) + 1
            col_no = int(getattr(mark, "column", 0)) + 1

        # Special-case: duplicate keys (commonly: two 'actions:' blocks)
        msg = str(e)
        m_dup = re.search(r"found duplicate key \(([^)]+)\)", msg)
        if m_dup:
            dup_key = m_dup.group(1)
            hint = "YAML does not allow duplicate keys. Merge the repeated blocks into one." \
                if dup_key != "actions" else (
                    "Keep only one 'actions:' block. Merge all action items into that single list."
                )
            issues.append(
                CSFIssues.make(
                    "CSFA_E_YAML_DUPLICATE_KEY",
                    path="$",
                    message=f"Duplicate YAML key '{dup_key}' detected. YAML would overwrite the earlier value.",
                    hint=hint,
                    context={
                        "filepath": filepath,
                        "location": {"line": line_no, "column": col_no},
                        "snippet": _make_snippet(text, line_no, col_no),
                    },
                )
            )
            return None, issues

        issues.append(
            CSFIssues.make(
                "CSFA_E_YAML_PARSE",
                path="$",
                message="Actions YAML parsing failed. Fix the file near the indicated location.",
                hint="Common causes: missing ':', wrong indentation, missing '-' in lists.",
                context={
                    "filepath": filepath,
                    "location": {"line": line_no, "column": col_no},
                    "snippet": _make_snippet(text, line_no, col_no),
                    "parser": str(e),
                },
            )
        )
        return None, issues

    if not isinstance(doc, dict):
        issues.append(
            CSFIssues.make(
                "CSFA_E_ROOT_TYPE",
                path="$",
                message="Actions YAML root must be a mapping (dictionary).",
                hint=f"Expected '{TOP_KEY}:' at the top level.",
                context={"filepath": filepath, "snippet": _make_snippet(text, 1, 1)},
            )
        )
        return None, issues

    return doc, issues


# ---------------------------------------------------------------------------
# Full actions.yaml validation (structure + per-action params)
# ---------------------------------------------------------------------------

def _validate_output_writable(out_str: str) -> Optional[str]:
    """
    Pre-check output path writability.
    Returns None if OK, else a friendly error string.
    """
    if out_str == "stdout":
        return None

    p = Path(out_str)
    parent = p.parent if str(p.parent) != "" else Path(".")
    if not parent.exists():
        return f"Output directory does not exist: {parent}"

    if p.exists():
        if not os.access(str(p), os.W_OK):
            return f"Cannot write to existing file: {p}"
    else:
        if not os.access(str(parent), os.W_OK):
            return f"Cannot create files in directory: {parent}"

    return None


def _coerce_param_aliases(action: str, params: Dict[str, Any], issues: List[Issue]) -> Dict[str, Any]:
    """
    Accept parameter aliases by moving alias values to the canonical name.
    Adds a WARNING when an alias is used.
    """
    spec = ACTION_SPECS[action]
    out = dict(params)

    for ps in spec.params:
        for alias in ps.aliases:
            if alias in out and ps.name not in out:
                issues.append(
                    CSFIssues.make(
                        "CSFA_W_PARAM_ALIAS",
                        path=f"{TOP_KEY}.actions.{action}.params",
                        message=f"Parameter '{alias}' is an alias of '{ps.name}' (using '{ps.name}').",
                        hint=f"Prefer '{ps.name}' for consistency.",
                        context={"action": action, "alias": alias, "canonical": ps.name},
                    )
                )
                out[ps.name] = out.pop(alias)
    return out


def _validate_action_params(
    action: str,
    params: Dict[str, Any],
    filepath: str,
    text: str,
    line_hint: Optional[int],
) -> Tuple[List[Issue], Dict[str, Any]]:
    """
    Validate params mapping for one action using its ActionSpec.
    Unknown params are WARNING (not ERROR), to keep evolution flexible.
    """
    issues: List[Issue] = []
    spec = ACTION_SPECS[action]

    # Accept aliases (warn)
    params2 = _coerce_param_aliases(action, params, issues)

    # Normalize section_full_analysis fmt param:
    # user might write fmt_display: =".4f" (leading '='). We strip it with a WARNING.
    if action in ("section_full_analysis", "section_selected_analysis") and "fmt_display" in params2 and isinstance(params2["fmt_display"], str):
        v = params2["fmt_display"].strip()
        if v.startswith("="):
            issues.append(
                CSFIssues.make(
                    "CSFA_W_FMT_LEADING_EQUALS",
                    path=f"{TOP_KEY}.actions.section_full_analysis.params.fmt_display",
                    message="Found leading '=' in fmt_display; it will be ignored.",
                    hint='Use fmt_display: ".4f" (without "=").',
                    context={"value": params2["fmt_display"]},
                )
            )
            params2["fmt_display"] = v.lstrip("=").strip()

    # Apply defaults for optional params.
    # NOTE: we only apply non-None defaults to avoid type errors on optional params
    # that intentionally use "no default" (default=None) for non-string types.
    for ps in spec.params:
        if ps.name not in params2 and (not ps.required) and ps.default is not None:
            params2[ps.name] = ps.default

    # Check required params and types
    def _type_ok(v: Any, typ: str) -> bool:
        if typ == "str":
            return isinstance(v, str) or v is None
        if typ == "int":
            return type(v) is int
        if typ == "float":
            return type(v) in (int, float)  # allow ints where floats are expected
        if typ == "bool":
            return type(v) is bool
        if typ == "dict":
            return isinstance(v, dict)
        if typ == "list":
            return isinstance(v, list)
        return False

    for ps in spec.params:
        if ps.name not in params2:
            if ps.required:
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_PARAM_MISSING",
                        path=f"{TOP_KEY}.actions.{action}.params.{ps.name}",
                        message=f"Missing required parameter '{ps.name}' for action '{action}'.",
                        hint=ps.description or "Provide the missing parameter under 'params:'.",
                        context={"filepath": filepath, "snippet": _make_snippet(text, line_hint, 1)},
                    )
                )
            continue

        v = params2[ps.name]
        if not _type_ok(v, ps.typ):
            issues.append(
                CSFIssues.make(
                    "CSFA_E_PARAM_TYPE",
                    path=f"{TOP_KEY}.actions.{action}.params.{ps.name}",
                    message=f"Parameter '{ps.name}' for action '{action}' has wrong type.",
                    hint=f"Expected {ps.typ}.",
                    context={"filepath": filepath, "found_type": type(v).__name__, "snippet": _make_snippet(text, line_hint, 1)},
                )
            )

    # Unknown params -> WARNING (not rigid)
    known = {ps.name for ps in spec.params}
    for k in params2.keys():
        if k not in known:
            issues.append(
                CSFIssues.make(
                    "CSFA_W_PARAM_UNKNOWN",
                    path=f"{TOP_KEY}.actions.{action}.params.{k}",
                    message=f"Unknown parameter '{k}' for action '{action}'.",
                    hint="It will be ignored unless the action implementation uses it.",
                    context={"action": action, "param": k},
                )
            )

    # Action-specific semantic checks
    if action == "plot_volume_3d" and "line_percent" in params2 and type(params2["line_percent"]) in (int, float):
        lp = float(params2["line_percent"])
        if not (0.0 <= lp <= 100.0):
            issues.append(
                CSFIssues.make(
                    "CSFA_E_PARAM_RANGE",
                    path=f"{TOP_KEY}.actions.plot_volume_3d.params.line_percent",
                    message="Parameter 'line_percent' must be within [0, 100].",
                    hint="Use a percentage between 0 and 100 (e.g. 40.0).",
                    context={"filepath": filepath, "snippet": _make_snippet(text, line_hint, 1), "value": lp},
                )
            )

    return issues, params2


def _validate_actions_doc(doc: Dict[str, Any], text: str, filepath: str) -> Tuple[Optional[Dict[str, Any]], List[Issue]]:
    """
    FULL validation of actions.yaml.
    Returns (normalized_root, issues).
    - normalized_root is the TOP_KEY mapping if validation passes enough to use it.
    - issues includes warnings and errors.
    """
    issues: List[Issue] = []

    # Ensure the action registry is populated. In the modular layout, some specs are added at load time.
    _load_actions()

    if TOP_KEY not in doc:
        ln = _find_key_line(text, TOP_KEY) or 1
        issues.append(
            CSFIssues.make(
                "CSFA_E_TOPKEY_MISSING",
                path="$",
                message=f"Not a CSF actions file: missing top-level '{TOP_KEY}:' key.",
                hint=f"Add '{TOP_KEY}:' at the top of the file.",
                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
            )
        )
        return None, issues

    root = doc[TOP_KEY]
    if not isinstance(root, dict):
        ln = _find_key_line(text, TOP_KEY) or 1
        issues.append(
            CSFIssues.make(
                "CSFA_E_TOPKEY_TYPE",
                path=TOP_KEY,
                message=f"'{TOP_KEY}' must be a mapping (dictionary).",
                hint="Example:\nCSF_ACTIONS:\n  stations: {...}\n  actions: [...]",
                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
            )
        )
        return None, issues

    # actions REQUIRED
    if "actions" not in root:
        ln = _find_key_line(text, "actions") or (_find_key_line(text, "stations") or 1)
        issues.append(
            CSFIssues.make(
                "CSFA_E_ACTIONS_MISSING",
                path=f"{TOP_KEY}",
                message="Missing required 'actions:' list.",
                hint="Add:\n  actions:\n    - section_full_analysis: {stations: [station_base]}",
                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
            )
        )
        return None, issues

    actions = root["actions"]
    if not isinstance(actions, list) or len(actions) == 0:
        ln = _find_key_line(text, "actions") or 1
        issues.append(
            CSFIssues.make(
                "CSFA_E_ACTIONS_TYPE",
                path=f"{TOP_KEY}.actions",
                message="'actions' must be a non-empty YAML list.",
                hint="Example:\n  actions:\n    - section_full_analysis: {...}",
                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
            )
        )
        return None, issues

    # stations are required only if at least one action needs them.
    # For now, all actions require stations except those in STATIONS_FORBIDDEN.
    need_stations = False
    for it in actions:
        if isinstance(it, dict) and len(it) == 1:
            nm = next(iter(it.keys()))
            if nm in STATIONS_FORBIDDEN:
                continue
            need_stations = True
            break
        # Malformed action items are treated as "need stations" to avoid skipping useful errors.
        need_stations = True
        break

    stations = root.get("stations")
    if stations is None:
        if need_stations:
            ln = _find_key_line(text, "stations") or (_find_key_line(text, TOP_KEY) or 1)
            issues.append(
                CSFIssues.make(
                    "CSFA_E_STATIONS_MISSING",
                    path=f"{TOP_KEY}",
                    message="Missing required 'stations:' section.",
                    hint="Add:\n  stations:\n    station_base: [0.0, 5.0, 10.0]",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            return None, issues
        # No action needs stations: accept missing stations.
        stations = {}
    else:
        if not isinstance(stations, dict):
            ln = _find_key_line(text, "stations") or 1
            issues.append(
                CSFIssues.make(
                    "CSFA_E_STATIONS_TYPE",
                    path=f"{TOP_KEY}.stations",
                    message="'stations' must be a mapping (station_name -> list of numbers).",
                    hint="Example:\n  stations:\n    station_sparse: [0.0, 5.0, 10.0]",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            return None, issues
        if len(stations) == 0 and need_stations:
            ln = _find_key_line(text, "stations") or 1
            issues.append(
                CSFIssues.make(
                    "CSFA_E_STATIONS_TYPE",
                    path=f"{TOP_KEY}.stations",
                    message="'stations' must be a non-empty mapping (station_name -> list of numbers).",
                    hint="Example:\n  stations:\n    station_sparse: [0.0, 5.0, 10.0]",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            return None, issues

    # Validate stations content (warnings for duplicates/sort)
    station_map: Dict[str, List[float]] = {}
    for sname, sval in stations.items():
        spath = f"{TOP_KEY}.stations.{sname}"

        if not isinstance(sname, str) or sname.strip() == "":
            ln = _find_key_line(text, "stations") or 1
            issues.append(
                CSFIssues.make(
                    "CSFA_E_STATION_NAME",
                    path=spath,
                    message="Station name must be a non-empty string.",
                    hint="Use names like 'station_base', 'station_sparse'.",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            continue

        if not isinstance(sval, list) or len(sval) == 0:
            ln = _find_key_line(text, sname) or (_find_key_line(text, "stations") or 1)
            issues.append(
                CSFIssues.make(
                    "CSFA_E_STATION_LIST",
                    path=spath,
                    message=f"Station '{sname}' must be a non-empty YAML list of numbers.",
                    hint="Example: station_sparse: [0.0, 5.0, 10.0]",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            continue

        zvals: List[float] = []
        for idx, v in enumerate(sval):
            # Strict numeric scalars only: ints/floats (no strings, no booleans)
            if type(v) not in (int, float):
                ln = _find_key_line(text, sname) or (_find_key_line(text, "stations") or 1)
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_STATION_VALUE",
                        path=f"{spath}[{idx}]",
                        message=f"Station '{sname}' contains a non-numeric value at index {idx}.",
                        hint="Station lists must contain only numbers (e.g. 0.0, 5.0, 10.0).",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1), "found": repr(v)},
                    )
                )
                break
            zvals.append(float(v))

        if any(i.severity == Severity.ERROR and i.path.startswith(spath) for i in issues):
            continue

        # WARNING duplicates
        if len(set(zvals)) != len(zvals):
            dups = [x for x in sorted(set(zvals)) if zvals.count(x) > 1]
            issues.append(
                CSFIssues.make(
                    "CSFA_W_STATION_DUPLICATES",
                    path=spath,
                    message=f"Station '{sname}' contains duplicate z values.",
                    hint="Consider removing duplicates to avoid repeated evaluations.",
                    context={"duplicates": dups},
                )
            )

        # WARNING not sorted
        if any(zvals[i] > zvals[i + 1] for i in range(len(zvals) - 1)):
            issues.append(
                CSFIssues.make(
                    "CSFA_W_STATION_NOT_SORTED",
                    path=spath,
                    message=f"Station '{sname}' is not sorted ascending.",
                    hint="Sort the station list (recommended).",
                    context={"values": zvals},
                )
            )

        station_map[sname] = zvals

    # Stop if stations errors exist
    if any(i.severity == Severity.ERROR for i in issues):
        return None, issues

    # Validate actions list and normalize into a simpler list
    normalized_actions: List[Dict[str, Any]] = []
  
    for idx, item in enumerate(actions):
        apath = f"{TOP_KEY}.actions[{idx}]"
        ln_actions = _find_key_line(text, "actions") or 1

        if not isinstance(item, dict):
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_ITEM_TYPE",
                    path=apath,
                    message="Each action item must be a mapping (dictionary).",
                    hint="Example:\n  - section_full_analysis:\n      stations: [station_base]",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln_actions, 1)},
                )
            )
            continue

        if len(item) != 1:
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_ITEM_KEYS",
                    path=apath,
                    message="Each action item must define exactly one action name key.",
                    hint="Example:\n  - section_full_analysis: {...}",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln_actions, 1), "found_keys": list(item.keys())},
                )
            )
            continue

        action_name = next(iter(item.keys()))
        if action_name not in ACTION_SPECS:
            ln = _find_key_line(text, action_name) or ln_actions
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_UNKNOWN",
                    path=apath,
                    message=f"Unknown action '{action_name}'.",
                    hint=f"Supported actions: {', '.join(sorted(ACTION_SPECS.keys()))}",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            continue

        payload = item[action_name] if item[action_name] is not None else {}
        if not isinstance(payload, dict):
            ln = _find_key_line(text, action_name) or ln_actions
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_PAYLOAD_TYPE",
                    path=f"{apath}.{action_name}",
                    message=f"Action '{action_name}' parameters must be a mapping.",
                    hint="Example:\n  - section_full_analysis:\n      stations: [station_base]\n      output: [stdout]\n      params: {}",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            continue

        # Common: stations REQUIRED                            <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # Common: stations
        # - Most actions REQUIRE stations
        # - Some actions MUST NOT have stations (they use field endpoints or other special inputs)
        if action_name in STATIONS_FORBIDDEN:
            if "stations" in payload:
                ln = _find_key_line(text, action_name) or ln_actions
                hint = (
                    "Remove 'stations:' from this action. The plot uses only the end sections (z0 and z1)."
                    if action_name == "plot_volume_3d"
                    else "Remove 'stations:' from this action. It does not use stations."
                )
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_ACTION_STATIONS_NOT_ALLOWED",
                        path=f"{apath}.{action_name}.stations",
                        message=f"Action '{action_name}' must not define 'stations:'.",
                        hint=hint,
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue
            stations_ref = []  # keep normalized shape
        else:
            # stations REQUIRED for most actions.
            # write_sap2000_geometry is backward-compatible: stations may be omitted
            # and Lobatto (n_intervals) is used by the action/base function.
            if "stations" not in payload:
                if action_name == "write_sap2000_geometry":
                    stations_ref = []
                else:
                    ln = _find_key_line(text, action_name) or ln_actions
                    issues.append(
                        CSFIssues.make(
                            "CSFA_E_ACTION_STATIONS_MISSING",
                            path=f"{apath}.{action_name}",
                            message=f"Action '{action_name}' is missing required 'stations:' list.",
                            hint="Add:\n  stations: [station_base]",
                            context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                        )
                    )
                    continue
            else:
                stations_ref = payload.get("stations", [])


            if isinstance(stations_ref, str):
                stations_ref = [stations_ref]

            # Action-specific requirement (dual-mode):
            # - If 'stations' is omitted (or resolves to empty), this action must have params.n_intervals (Gauss–Lobatto mode).
            # - If 'stations' is provided, n_intervals is optional (may still be validated for type elsewhere).
            if action_name == "write_sap2000_geometry":
                # NOTE: We intentionally keep backward compatibility with historical YAML where
                # stations could be omitted to request Lobatto sampling.
                if isinstance(stations_ref, list) and len(stations_ref) == 0:
                    params_obj = payload.get("params", None)
                    if not isinstance(params_obj, dict):
                        ln = _find_key_line(text, action_name) or ln_actions
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_ACTION_PARAMS_TYPE",
                                path=f"{apath}.{action_name}.params",
                                message=f"Action '{action_name}'.params must be a mapping.",
                                hint="Example:\n  params:\n    n_intervals: 7\n    E_ref: 2.1e+11\n    nu: 0.30",
                                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                        continue

                    if "n_intervals" not in params_obj:
                        ln = _find_key_line(text, action_name) or ln_actions
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_PARAM_MISSING",
                                path=f"{apath}.{action_name}.params.n_intervals",
                                message="Missing required parameter 'n_intervals' for action 'write_sap2000_geometry' when 'stations' is omitted (Gauss–Lobatto mode).",
                                hint="Add under params:\n  n_intervals: 7",
                                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                        continue

                    v = params_obj.get("n_intervals")
                    if type(v) is not int:
                        ln = _find_key_line(text, action_name) or ln_actions
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_PARAM_TYPE",
                                path=f"{apath}.{action_name}.params.n_intervals",
                                message="Parameter 'n_intervals' for action 'write_sap2000_geometry' has wrong type.",
                                hint="Expected int (e.g. 7).",
                                context={"filepath": filepath, "found_type": type(v).__name__, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                        continue
                    if v < 1:
                        ln = _find_key_line(text, action_name) or ln_actions
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_PARAM_RANGE",
                                path=f"{apath}.{action_name}.params.n_intervals",
                                message="Parameter 'n_intervals' must be >= 1 for Gauss–Lobatto mode.",
                                hint="Use an integer >= 1 (stations = n_intervals + 1).",
                                context={"filepath": filepath, "value": v, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                        continue


            # Backward compatibility:
            # - write_sap2000_geometry may omit 'stations' and fallback to Lobatto later.
            # - all other actions keep the historical requirement for non-empty station names.
            if action_name == "write_sap2000_geometry" and isinstance(stations_ref, list) and len(stations_ref) == 0:
                pass
            elif not isinstance(stations_ref, list) or len(stations_ref) == 0:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_ACTION_STATIONS_TYPE",
                        path=f"{apath}.{action_name}.stations",
                        message=f"Action '{action_name}'.stations must be a non-empty list of station names.",
                        hint="Example:\n  stations: [station_sparse, station_base]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            if not (action_name == "write_sap2000_geometry" and len(stations_ref) == 0):
                missing: List[str] = []
                for si, sref in enumerate(stations_ref):
                    if not isinstance(sref, str) or sref.strip() == "":
                        missing.append(f"<invalid at index {si}>")
                        continue
                    if sref not in station_map:
                        missing.append(sref)
                #--------------------------
                if missing:
                    # Try to locate the exact 'stations:' line inside the current action block.
                    ln = None
                    try:
                        lines = text.splitlines()
                        action_hdr = f"  {action_name}:"
                        stations_key = "    stations:"
                        in_action = False
                        action_indent = None

                        for i, line in enumerate(lines, start=1):
                            if not in_action:
                                if line.startswith(action_hdr):
                                    in_action = True
                                    action_indent = len(line) - len(line.lstrip(" "))
                                    continue
                            else:
                                cur_indent = len(line) - len(line.lstrip(" "))
                                # End of current action block when indentation returns to action level or less
                                if line.strip() and cur_indent <= action_indent:
                                    break
                                if line.startswith(stations_key):
                                    ln = i
                                    break
                    except Exception:
                        ln = None

                    if ln is None:
                        ln = _find_key_line(text, "stations") or _find_key_line(text, action_name) or ln_actions

                    issues.append(
                        CSFIssues.make(
                            "CSFA_E_ACTION_STATIONS_UNKNOWN",
                            path=f"{apath}.{action_name}.stations",
                            message=f"Action '{action_name}' references unknown station(s): {', '.join(missing)}",
                            hint=f"Define missing station names under '{TOP_KEY}.stations'.",
                            context={
                                        "filepath": filepath,
                                        "missing_station": missing[0] if missing else None,
                                        "missing_stations_str": ", ".join(missing),  # stringa pronta
                                        "snippet": _make_snippet(text, ln, 2),
                                    },
                        )
                    )
                    continue

                    #-----------------------------------

        # ------------------------------------------------------------
        # Action-specific rule: export_yaml
        # ------------------------------------------------------------
        # This action exports a NEW CSF geometry YAML by extracting exactly TWO sections (z0, z1).
        # Therefore it requires:
        #   - stations: one station-set name only
        #   - that station-set must contain EXACTLY two Z values
        #   - output: MUST be explicitly provided (file-only action; no implicit stdout default)
        if action_name == "export_yaml":
            # Require exactly one station-set reference (e.g., stations: [station_edge])
            if len(stations_ref) != 1:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_EXPORT_YAML_STATIONS_REF_COUNT",
                        path=f"{apath}.{action_name}.stations",
                        message="Action 'export_yaml' requires exactly ONE station set name in 'stations:'.",
                        hint="Example:\n  - export_yaml:\n      stations: [station_edge]\n      output: [out/edge.yaml]\n"
                             "And station_edge must contain exactly two Z values.",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            sref = stations_ref[0]
            zvals = station_map.get(sref, [])
            if not isinstance(zvals, list) or len(zvals) != 2:
                ln = _find_key_line(text, action_name) or ln_actions
                got = len(zvals) if isinstance(zvals, list) else "?"
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_EXPORT_YAML_STATION_SIZE",
                        path=f"{TOP_KEY}.stations.{sref}",
                        message=f"Station set '{sref}' must contain exactly 2 values for 'export_yaml' (got {got}).",
                        hint="Define the station set as two numbers, e.g.:\n"
                             f"  {sref}: [0.0, 10.0]\n"
                             "or:\n"
                             f"  {sref}:\n    - 0.0\n    - 10.0",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            # Output is required for export_yaml (do NOT fall back to default stdout).
            if "output" not in payload:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_EXPORT_YAML_OUTPUT_MISSING",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'export_yaml' is missing required 'output:' (file path).",
                        hint="Example:\n  - export_yaml:\n      stations: [station_edge]\n      output: [out/edge.yaml]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            # Output is required for write_opensees_geometry (do NOT fall back to default stdout).
            if action_name == "write_opensees_geometry":
                if "output" not in payload:
                    ln = _find_key_line(text, action_name) or ln_actions
                    issues.append(
                        CSFIssues.make(
                            "CSFA_E_OPENSEES_OUTPUT_MISSING",
                            path=f"{apath}.{action_name}.output",
                            message="Action 'write_opensees_geometry' is missing required 'output:' (file path).",
                            hint="Example:\n  - write_opensees_geometry:\n      output: [out/geometry.tcl]\n      params: {n_points: 10, E_ref: 2.1e11, nu: 0.30}",
                            context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                        )
                    )
                    continue

        
        # ------------------------------------------------------------
        # Action-specific rule: volume
        # ------------------------------------------------------------
        # This action integrates per-polygon occupied volumes between exactly TWO stations (z1, z2).
        # Therefore it requires:
        #   - stations: one station-set name only
        #   - that station-set must contain EXACTLY two Z values
        if action_name == "volume":
            # Require exactly one station-set reference (e.g., stations: [station_edge])
            if len(stations_ref) != 1:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_VOLUME_STATIONS_REF_COUNT",
                        path=f"{apath}.{action_name}.stations",
                        message="Action 'volume' requires exactly ONE station set name in 'stations:'.",
                        hint="Example:\n  - volume:\n      stations: [station_edge]\n      output: [stdout, out/volume.csv]\n"
                             "And station_edge must contain exactly two Z values.",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            sref = stations_ref[0]
            zvals = station_map.get(sref, [])
            if not isinstance(zvals, list) or len(zvals) != 2:
                ln = _find_key_line(text, action_name) or ln_actions
                got = len(zvals) if isinstance(zvals, list) else "?"
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_VOLUME_STATION_SIZE",
                        path=f"{TOP_KEY}.stations.{sref}",
                        message=f"Station set '{sref}' must contain exactly 2 values for 'volume' (got {got}).",
                        hint="Define the station set as two numbers, e.g.:\n"
                             f"  {sref}: [0.0, 10.0]\n"
                             "or:\n"
                             f"  {sref}:\n    - 0.0\n    - 10.0",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

# Common: output OPTIONAL (default stdout)                     <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        output_list = payload.get("output", ["stdout"])
        if isinstance(output_list, str):
            output_list = [output_list]
        if not isinstance(output_list, list) or len(output_list) == 0:
            ln = _find_key_line(text, action_name) or ln_actions
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_OUTPUT_TYPE",
                    path=f"{apath}.{action_name}.output",
                    message=f"Action '{action_name}'.output must be a list of strings (or 'stdout').",
                    hint="Example:\n  output: [stdout, out/result.csv]",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            continue

        # Accept legacy nested form: output: [stdout, [file1, file2]]
        flat_output_list: List[Any] = []
        for o in output_list:
            flat_output_list.extend(o) if isinstance(o, list) else flat_output_list.append(o)
        output_list = flat_output_list


        
        # Special rule: plot_volume_3d is interactive-only. It must not write image files.
        # The plot is shown from the GUI window at the very end of the run (deferred plt.show()).
        if action_name == "plot_volume_3d":
            non_stdout = [o for o in output_list if isinstance(o, str) and o != "stdout"]
            if non_stdout:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_ACTION_OUTPUT_NOT_ALLOWED",
                        path=f"{apath}.{action_name}.output",
                        message=(
                            "Action 'plot_volume_3d' does not support file outputs. "
                            "Remove file paths and keep only 'stdout' (or omit 'output:' entirely)."
                        ),
                        hint="Example:\n  - plot_volume_3d:\n      params: { ... }",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
            # Always normalize to stdout to match the intended behavior.
            output_list = ["stdout"]
        # Special rule: export_yaml is FILE-ONLY and must write exactly one YAML file.
        # We enforce this here (validation), so users get a friendly message rather than a runtime failure.
        if action_name == "export_yaml":
            # stdout is not allowed for this action
            has_stdout = any(isinstance(o, str) and o == "stdout" for o in output_list)
            non_stdout = [o for o in output_list if isinstance(o, str) and o != "stdout"]

            if has_stdout:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_EXPORT_YAML_STDOUT_NOT_ALLOWED",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'export_yaml' does not allow 'stdout' in output (file-only).",
                        hint="Use only a YAML file path, e.g.:\n  output: [out/edge.yaml]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            if len(non_stdout) != 1:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_EXPORT_YAML_OUTPUT_COUNT",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'export_yaml' requires exactly ONE output file path.",
                        hint="Example:\n  output: [out/edge.yaml]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            outp = non_stdout[0]
            if not (outp.lower().endswith(".yaml") or outp.lower().endswith(".yml")):
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_EXPORT_YAML_OUTPUT_EXT",
                        path=f"{apath}.{action_name}.output[0]",
                        message="Action 'export_yaml' output must be a YAML file (*.yaml or *.yml).",
                        hint="Example:\n  output: [out/edge.yaml]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            # Normalize to a single file output (defensive).
            output_list = [outp]

        # Special rule: write_opensees_geometry is FILE-ONLY and must write exactly one Tcl file.
        # We enforce this here (validation), so users get a friendly message rather than a runtime failure.
        if action_name == "write_opensees_geometry":
            has_stdout = any(isinstance(o, str) and o == "stdout" for o in output_list)
            non_stdout = [o for o in output_list if isinstance(o, str) and o != "stdout"]

            if has_stdout:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_OPENSEES_STDOUT_NOT_ALLOWED",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'write_opensees_geometry' does not allow 'stdout' in output (file-only).",
                        hint="Use only a Tcl file path, e.g.:\n  output: [out/geometry.tcl]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            if len(non_stdout) != 1:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_OPENSEES_OUTPUT_COUNT",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'write_opensees_geometry' requires exactly ONE output file path.",
                        hint="Example:\n  output: [out/geometry.tcl]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            outp = non_stdout[0]
            if not outp.lower().endswith(".tcl"):
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_OPENSEES_OUTPUT_EXT",
                        path=f"{apath}.{action_name}.output[0]",
                        message="Action 'write_opensees_geometry' output must be a Tcl file (*.tcl).",
                        hint="Example:\n  output: [out/geometry.tcl]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            output_list = [outp]


        # Special rule: write_sap2000_geometry is FILE-ONLY and must write exactly one template file.
        # This action generates a human-readable SAP2000 "template pack" (copy/paste helper).
        # We enforce output rules here so users get a clear validation error instead of a runtime crash.
        if action_name == "write_sap2000_geometry":
            has_stdout = any(isinstance(o, str) and o == "stdout" for o in output_list)
            non_stdout = [o for o in output_list if isinstance(o, str) and o != "stdout"]

            if has_stdout:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_SAP2000_STDOUT_NOT_ALLOWED",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'write_sap2000_geometry' does not allow 'stdout' in output (file-only).",
                        hint="Use only a template file path, e.g.:\n  output: [out/model_export_template.txt]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            if len(non_stdout) != 1:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_SAP2000_OUTPUT_COUNT",
                        path=f"{apath}.{action_name}.output",
                        message="Action 'write_sap2000_geometry' requires exactly ONE output file path.",
                        hint="Example:\n  output: [out/model_export_template.txt]",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue

            outp = non_stdout[0]
            # We deliberately do NOT enforce a strict extension here, but .txt is recommended.
            output_list = [outp]
        # Validate output entries and writability
        for oi, outp in enumerate(output_list):
            if not isinstance(outp, str) or outp.strip() == "":
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_ACTION_OUTPUT_VALUE",
                        path=f"{apath}.{action_name}.output[{oi}]",
                        message=f"Action '{action_name}' has an invalid output entry at index {oi}.",
                        hint="Use 'stdout' or a valid file path.",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
                continue
            err = _validate_output_writable(outp)
            if err is not None:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_ACTION_OUTPUT_NOT_WRITABLE",
                        path=f"{apath}.{action_name}.output[{oi}]",
                        message=err,
                        hint="Create the directory or choose a writable location.",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )

        # Common: params OPTIONAL
        params = payload.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            ln = _find_key_line(text, action_name) or ln_actions
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_PARAMS_TYPE",
                    path=f"{apath}.{action_name}.params",
                    message=f"Action '{action_name}'.params must be a mapping (dictionary).",
                    hint="Example:\n  params:\n    fmt_display: '.4f'",
                    context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                )
            )
            continue

        # Per-action params validation + normalization (unknown params -> WARNING)
        ln = _find_key_line(text, action_name) or ln_actions
        p_issues, params_norm = _validate_action_params(action_name, params, filepath, text, ln)

        if action_name == "plot_section_2d":
            for k in ("show_ids", "show_weights", "show_vertex_ids"):
                if k in payload:
                    params_norm[k] = payload[k]
                    v = params_norm[k]



                   
        issues.extend(p_issues)
        params = params_norm

        # ------------------------------------------------------------
        # Action-specific fields outside params
        # ------------------------------------------------------------
        # Most action-specific options live under `params:`.
        # plot_properties is a deliberate exception: it needs a top-level
        # `properties:` list because it conceptually selects *what to plot*
        # rather than numerical parameters.
        #
        # We validate it here so that users get a friendly, YAML-snippet error
        # instead of a runtime exception.
        extra_fields: Dict[str, Any] = {}

        if action_name == "section_selected_analysis":
            # This action requires a non-empty list of property keys to extract.
            props_raw = payload.get("properties")
            properties_norm = None

            if props_raw is None:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_PROPERTIES_MISSING",
                        path=f"{apath}.{action_name}.properties",
                        message="Action 'section_selected_analysis' is missing required 'properties:' list.",
                        hint="Add at least one property key, e.g.:\n  properties: ['A', 'Ix', 'Iy']",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
            else:
                # Allow the shorthand: properties: A  (we normalize to a list)
                if isinstance(props_raw, str):
                    props_raw = [props_raw]

                if (not isinstance(props_raw, list)) or len(props_raw) == 0:
                    ln = _find_key_line(text, action_name) or ln_actions
                    issues.append(
                        CSFIssues.make(
                            "CSFA_E_PROPERTIES_TYPE",
                            path=f"{apath}.{action_name}.properties",
                            message="'properties' must be a non-empty YAML list of strings.",
                            hint="Example: properties: ['A', 'Ix', 'Iy']",
                            context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                        )
                    )
                else:
                    bad: List[str] = []
                    props_norm: List[str] = []

                    for pi, pkey in enumerate(props_raw):
                        if not isinstance(pkey, str) or pkey.strip() == "":
                            bad.append(f"<invalid at index {pi}>")
                            continue
                        if pkey not in PLOT_PROPERTIES_ALLOWED:
                            bad.append(pkey)
                            continue
                        props_norm.append(pkey)

                    if bad:
                        ln = _find_key_line(text, action_name) or ln_actions
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_PROPERTIES_UNKNOWN",
                                path=f"{apath}.{action_name}.properties",
                                message=f"Unknown/invalid property key(s) for section_selected_analysis: {bad}",
                                hint="Allowed keys: " + ", ".join(PLOT_PROPERTIES_ALLOWED),
                                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                    else:
                        properties_norm = props_norm

            if properties_norm is not None:
                extra_fields["properties"] = properties_norm

        if action_name == "plot_properties":
            props_raw = payload.get("properties")
            properties_norm = None

            if props_raw is None:
                ln = _find_key_line(text, action_name) or ln_actions
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_PROPERTIES_MISSING",
                        path=f"{apath}.{action_name}.properties",
                        message="Action 'plot_properties' is missing required 'properties:' list.",
                        hint="Add at least one property key, e.g.:\n  properties: ['A', 'Ix', 'Iy']",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
            else:
                # Allow the shorthand: properties: A  (we normalize to a list)
                if isinstance(props_raw, str):
                    props_raw = [props_raw]

                if (not isinstance(props_raw, list)) or len(props_raw) == 0:
                    ln = _find_key_line(text, action_name) or ln_actions
                    issues.append(
                        CSFIssues.make(
                            "CSFA_E_PROPERTIES_TYPE",
                            path=f"{apath}.{action_name}.properties",
                            message="'properties' must be a non-empty YAML list of strings.",
                            hint="Example: properties: ['A', 'Ix', 'Iy']",
                            context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                        )
                    )
                else:
                    bad: List[str] = []
                    props_norm: List[str] = []

                    for pi, pkey in enumerate(props_raw):
                        if not isinstance(pkey, str) or pkey.strip() == "":
                            bad.append(f"<invalid at index {pi}>")
                            continue
                        if pkey not in PLOT_PROPERTIES_ALLOWED:
                            bad.append(pkey)
                            continue
                        props_norm.append(pkey)

                    if bad:
                        ln = _find_key_line(text, action_name) or ln_actions
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_PROPERTIES_UNKNOWN",
                                path=f"{apath}.{action_name}.properties",
                                message=f"Unknown/invalid property key(s) for plot_properties: {bad}",
                                hint="Allowed keys: " + ", ".join(PLOT_PROPERTIES_ALLOWED),
                                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                    else:
                        properties_norm = props_norm

            if properties_norm is not None:
                extra_fields["properties"] = properties_norm

        if action_name == "weight_lab_zrelative":
            # This action is intentionally *text-only* and exists to inspect custom weight laws.
            # The user provides a list of expressions under the key `weith_law:` (kept OUTSIDE
            # `params:` because it is not a numerical knob; it is the actual payload to inspect).
            #
            # IMPORTANT: the key name is intentionally kept as requested ("weith_law").
            # We also accept the more correct alias "weight_law" with a WARNING.
            laws_raw = payload.get("weith_law")
            if laws_raw is None and "weight_law" in payload:
                laws_raw = payload.get("weight_law")
                issues.append(
                    CSFIssues.make(
                        "CSFA_W_WEIGHT_LAW_ALIAS",
                        path=f"{apath}.{action_name}.weight_law",
                        message="Using 'weight_law' as alias for 'weith_law'.",
                        hint="Rename 'weight_law' to 'weith_law' to match the official schema.",
                        context={},
                    )
                )

            laws_norm: Optional[List[str]] = None

            if laws_raw is None:
                issues.append(
                    CSFIssues.make(
                        "CSFA_E_WEIGHT_LAW_MISSING",
                        path=f"{apath}.{action_name}.weith_law",
                        message="Action 'weight_lab_zrelative' is missing required 'weith_law:' list.",
                        hint="Example:\n  weith_law: ['w0 + (w1-w0)*0.5*(1-np.cos(np.pi*z/L))']",
                        context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                    )
                )
            else:
                # Allow shorthand: weith_law: "np.cos(np.pi*z/L)"  (normalize to a list)
                if isinstance(laws_raw, str):
                    laws_raw = [laws_raw]

                if (not isinstance(laws_raw, list)) or len(laws_raw) == 0:
                    issues.append(
                        CSFIssues.make(
                            "CSFA_E_WEIGHT_LAW_TYPE",
                            path=f"{apath}.{action_name}.weith_law",
                            message="'weith_law' must be a non-empty YAML list of strings.",
                            hint="Example:\n  weith_law: ['np.cos(np.pi*z/L)', '1 + 0.1*z/L']",
                            context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                        )
                    )
                else:
                    bad: List[str] = []
                    tmp: List[str] = []
                    for li, expr in enumerate(laws_raw):
                        if not isinstance(expr, str) or expr.strip() == "":
                            bad.append(f"<invalid at index {li}>")
                            continue
                        tmp.append(expr.strip())

                    if bad:
                        issues.append(
                            CSFIssues.make(
                                "CSFA_E_WEIGHT_LAW_VALUE",
                                path=f"{apath}.{action_name}.weith_law",
                                message=f"Invalid empty/non-string expression(s) in 'weith_law': {bad}",
                                hint="Each entry must be a non-empty string.",
                                context={"filepath": filepath, "snippet": _make_snippet(text, ln, 1)},
                            )
                        )
                    else:
                        laws_norm = tmp

            if laws_norm is not None:
                extra_fields["weith_law"] = laws_norm
        
        normalized_actions.append(
            {
                "name": action_name,
                "stations": [str(x) for x in stations_ref],
                "output": [str(x) for x in output_list],
                "params": dict(params),
                **extra_fields,
            }
        )

    if any(i.severity == Severity.ERROR for i in issues):
        return None, issues

    normalized_root = dict(root)
    normalized_root["_stations_map"] = station_map
    normalized_root["_actions_list"] = normalized_actions
    return normalized_root, issues


# ---------------------------------------------------------------------------
# Help printing
# ---------------------------------------------------------------------------

def print_actions_help() -> None:
    _load_actions()

    """
    Print a user-facing help page for all actions and parameters.
    """
    print("CSF Actions Catalog")
    print("=" * 78)
    print("Scope / assumptions")
    print("  - CSF produces section property fields for slender-beam (Euler–Bernoulli) member models.")
    print("  - No local effects, shear deformation, or 3D continuum behavior are modeled here.")
    print("")
    print("Common YAML envelope for each action item:")
    print("  - <action_name>:")
    print("      stations: [station_set_name, ...]   # REQUIRED for most actions; FORBIDDEN for some")
    print("      output  : [stdout, path1, ...]      # OPTIONAL; default [stdout]")
    print("      params  : Ellipsis                   # OPTIONAL; action-specific")
    print("")
    print("Stations: station set names are defined under CSF_ACTIONS.stations.")
    print("  - Unless explicitly stated otherwise, station values are absolute z in the CSF field.")
    print("  - weight_lab_zrelative is the exception: station values are interpreted as relative z.")
    print("")
    print("Supported actions:")
    for name in sorted(ACTION_SPECS.keys()):
        spec = ACTION_SPECS[name]
        print("\n" + "-" * 60)
        print(f"Action: {spec.name}")
        print(f"Summary: {spec.summary}")
        print(f"Description:\n  {spec.description.replace(chr(10), chr(10)+'  ')}")

        if spec.params:
            print("\nParameters (under 'params:'):")
            for ps in spec.params:
                req = "required" if ps.required else f"optional (default {ps.default!r})"
                alias = f" (aliases: {', '.join(ps.aliases)})" if ps.aliases else ""
                print(f"  - {ps.name}: {ps.typ}, {req}{alias}")
                if ps.description:
                    print(f"      {ps.description}")
        else:
            print("\nParameters: (none defined yet)")

        print("\nMinimal YAML example:")
        print(f"  - {spec.name}:")
        if spec.name not in STATIONS_FORBIDDEN:
            print("      stations: [station_name]")
        print("      output: [stdout]")
        if spec.params:
            print("      params:")
            for ps in spec.params:
                if not ps.required:
                    print(f"        {ps.name}: {ps.default!r}")
        else:
            print("      params: {}")

    print("\nNotes:")
    print("- YAML booleans must be true/false (unquoted) to be parsed as booleans.")
    print("- Unknown params are currently WARNINGS and are ignored unless an action explicitly reads them.")
    print("- For strict validation of unknown params, add a dedicated validator stage (future work).")


# ---------------------------------------------------------------------------
# Execution engine
# ---------------------------------------------------------------------------

def _expand_station_names(stations_map: Dict[str, List[float]], station_names: List[str]) -> List[float]:
    """
    Expand a list of station set names into a single list of z-values, preserving order.

    User-friendly behavior:
    - trims station names (handles accidental spaces)
    - if a station is missing, raises a clear error listing available station names
    """
    z_all: List[float] = []
    missing: List[str] = []

    for raw_name in station_names:
        name = raw_name.strip() if isinstance(raw_name, str) else str(raw_name)
        if name not in stations_map:
            missing.append(name)
            continue
        z_all.extend(stations_map[name])

    if  missing:
        available = sorted(stations_map.keys())
        raise ValueError(
            f"Unknown station name(s): {missing}. Available stations: {available}."
        )

    return z_all



def _ensure_analysis_imports_or_error(
    issues: List[Issue],
    filepath: str,
    actions_list: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """Ensure required runtime imports exist.

    We check only what is needed for the requested actions.
    """
    ok = True

    requested: set[str] = set()
    if actions_list:
        for a in actions_list:
            n = a.get("name")
            if isinstance(n, str):
                requested.add(n)

    need_field = bool(requested)  # any action implies we need the field class import
    need_analysis = any(n in requested for n in ("section_full_analysis", "section_selected_analysis"))
    need_visualizer = any(n in requested for n in ("plot_section_2d", "plot_volume_3d", "plot_properties", "plot_weight"))
    need_weight_inspector = "weight_lab_zrelative" in requested
    need_opensees_export = "write_opensees_geometry" in requested
    need_sap2000_export = "write_sap2000_geometry" in requested

    if need_field and ContinuousSectionField is None:
        issues.append(
            CSFIssues.make(
                "CSFA_E_IMPORT",
                path="$",
                message="Cannot import ContinuousSectionField from csf.section_field.",
                hint="Check your package/module layout and imports.",
                context={"filepath": filepath},
            )
        )
        ok = False
    if need_analysis and (section_full_analysis is None or section_print_analysis is None):
        issues.append(
            CSFIssues.make(
                "CSFA_E_IMPORT",
                path="$",
                message="Cannot import section_full_analysis / section_print_analysis from csf.section_field.",
                hint="Check your package/module layout and ensure these functions exist.",
                context={"filepath": filepath},
            )
        )
        ok = False
    if need_visualizer and Visualizer is None:
        issues.append(
            CSFIssues.make(
                "CSFA_E_IMPORT",
                path="$",
                message="Cannot import Visualizer from csf.section_field.",
                hint="Check your package/module layout and ensure Visualizer exists.",
                context={"filepath": filepath},
            )
        )
        ok = False

    # weight_lab_zrelative relies on a dedicated safe evaluator helper from section_field.
    # We check it explicitly here so the user gets a friendly import error instead of a runtime crash.
    if need_weight_inspector and safe_evaluate_weight_zrelative is None:
        issues.append(
            CSFIssues.make(
                "CSFA_E_IMPORT",
                path="$",
                message="Cannot import safe_evaluate_weight_zrelative from csf.section_field.",
                hint="Ensure section_field defines safe_evaluate_weight_zrelative and it is importable.",
                context={"filepath": filepath},
            )
        )
        ok = False

    # write_opensees_geometry is defined at module level in section_field and is used by the
    # write_opensees_geometry action. We check it explicitly to avoid runtime crashes.
    if need_opensees_export and write_opensees_geometry is None:
        issues.append(
            CSFIssues.make(
                "CSFA_E_IMPORT",
                path="$",
                message="Cannot import write_opensees_geometry from csf.section_field.",
                hint="Ensure section_field defines write_opensees_geometry(field, n_points, E_ref, nu, filename) and it is importable.",
                context={"filepath": filepath},
            )
        )
        ok = False
    
    # SAP2000 template-pack exporter (sap2000_v2.write_sap2000_template_pack)
    if need_sap2000_export and write_sap2000_template_pack is None:
        issues.append(
            CSFIssues.make(
                "CSFA_E_IMPORT",
                path="$",
                message="Cannot import write_sap2000_template_pack (SAP2000 template exporter).",
                hint="Ensure sap2000_v2.py is importable (preferred: csf/sap2000_v2.py) and defines write_sap2000_template_pack(...).",
                context={"filepath": filepath},
            )
        )
        ok = False
    return ok


def _run_action_section_full_analysis(
    field: Any,
    stations_map: Dict[str, List[float]],
    action: Dict[str, Any],
) -> None:
    """
    Execute section_full_analysis action.
    """
    # Resolve fmt parameter (default from spec)
    params = action.get("params", {}) or {}
    fmt = params.get("fmt_display")
    if fmt is None:
        fmt = ACTION_SPECS["section_full_analysis"].params[0].default

    # Expand z values
    z_list = _expand_station_names(stations_map, action["stations"])

    # Collect analysis data for potential CSV outputs
    keys: List[str]
    if section_full_analysis_keys is not None:
        keys = list(section_full_analysis_keys())
    else:
        # fallback: will infer from first dict
        keys = []

    rows: List[Dict[str, Any]] = []

    # We'll build text reports (for non-CSV file outputs)
    report_blocks: List[str] = []

    for z in z_list:
        sec = field.section(float(z))
        full = section_full_analysis(sec)

        # Prepare a report block (text) by capturing stdout from section_print_analysis
        buf = io.StringIO()
        with redirect_stdout(buf):
            print(f"\n### SECTION FULL ANALYSIS @ z = {float(z)} ###")
            section_print_analysis(full, fmt=fmt)

        report_text = buf.getvalue()
        report_blocks.append(report_text)

        # Prepare row for CSV
        if not keys:
            # infer key order from dict (insertion order)
            keys = list(full.keys())
        row = {"z": float(z)}
        for k in keys:
            row[k] = full.get(k)
        rows.append(row)

    # Output routing
    outputs = action["output"]

    for outp in outputs:
        if outp == "stdout":
            # Print all reports
            for blk in report_blocks:
                print(blk, end="" if blk.endswith("\n") else "\n")
            continue

        p = Path(outp)
        # Safety: create friendly error if directory missing (should have been caught in validation)
        if not p.parent.exists():
            raise RuntimeError(f"Output directory does not exist: {p.parent}")

        if p.suffix.lower() == ".csv":
            # Write numeric table
            # Columns: z + keys
            fieldnames = ["z"] + keys
            with open(p, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for r in rows:
                    w.writerow(r)
        else:
            # Write captured report text
            with open(p, "w", encoding="utf-8") as f:
                for blk in report_blocks:
                    f.write(blk)
                    if not blk.endswith("\n"):
                        f.write("\n")




# [migrated] write_opensees_geometry runner moved to actions/write_opensees_geometry.py






def show_per_label(label):
    print(f"Label to show '{label}'")
    for num in plt.get_fignums():
        fig = plt.figure(num)
        if fig.get_label() == label:
            plt.figure(num)  # Attiva
            print(f"Label '{label}'")
            plt.show()
            return True
    print(f"Label '{label}' not found")
    return False

def _run_action_plot_properties(
    field: Any,
    stations_map: Dict[str, List[float]],
    action: Dict[str, Any],
) -> None:
    """Action: plot_properties

    Wrapper of:
        Visualizer.plot_properties(keys_to_plot=None, num_points=100)

    Key design points (per current CSFActions prototype)
    ----------------------------------------------------
    1) This action does NOT use 'stations'. It always samples between the CSF endpoints.
       That is why it is listed in STATIONS_FORBIDDEN and the validator rejects 'stations:'.

    2) Output semantics match plot_section_2d:
       - If output is omitted -> default ["stdout"] -> keep figures for the final GUI window.
       - If output contains file paths -> save to file.
       - If output does NOT contain "stdout" -> file-only (do not show, and do not set want_show_2d).

    3) The plotting window is shown only ONCE at the very end of main() (deferred plt.show()).
       However, the current Visualizer.plot_properties implementation (in section_field)
       ends with a direct plt.show(). To preserve the deferred-show protocol without
       editing section_field, we temporarily monkey-patch plt.show to a no-op during
       the call.

       This is intentionally localized and reversible:
       - we restore the original plt.show in a finally block
       - we then label the newly created figures and optionally save them

    Notes
    -----
    - This action requires a top-level YAML list 'properties:' that selects which
      property keys to plot.
    - The validator normalizes it into action["properties"].
    """
    # stations_map is unused by design (endpoints only).
    _ = stations_map

    if Visualizer is None:
        raise RuntimeError("Visualizer is not available (import failed).")

    import io

    # 1) Resolve parameters
    params = action.get("params", {}) or {}
    num_points = int(params.get("num_points", ACTION_SPECS["plot_properties"].params[0].default))

    # 2) Resolve outputs
    outputs = action.get("output")
    if outputs is None:
        outputs = ["stdout"]

    do_show = ("stdout" in outputs)
    file_outputs = [o for o in outputs if o != "stdout"]

    # 3) Resolve properties (normalized by validation)
    keys_to_plot = action.get("properties")
    if not isinstance(keys_to_plot, list) or len(keys_to_plot) == 0:
        # Should not happen after validation, but keep a friendly runtime error.
        raise RuntimeError("plot_properties requires a non-empty 'properties:' list.")

    # 4) Call Visualizer while suppressing its internal plt.show()
    viz = Visualizer(field)

    # Capture current figure numbers so we can identify what this action creates.
    before = set(plt.get_fignums())

    old_show = plt.show

    def _noop_show(*args, **kwargs):
        """Temporary replacement for plt.show() during plot_properties.

        Why: Visualizer.plot_properties currently calls plt.show() at the end.
        In the CSFActions runner we want ONE final plt.show() at the end of main().
        """
        return None

    plt.show = _noop_show
    try:
        # NOTE: Visualizer.plot_properties signature in section_field _lastv.py is:
        #   plot_properties(self, keys_to_plot=None, num_points=100)
        viz.plot_properties(keys_to_plot=keys_to_plot, num_points=num_points)
    finally:
        # Always restore original plt.show, even if plotting fails.
        plt.show = old_show

    after = set(plt.get_fignums())
    new_nums = sorted(after - before)

    # If Visualizer reused an existing figure (rare), fall back to current figure.
    if not new_nums:
        try:
            new_nums = [plt.gcf().number]
        except Exception:
            new_nums = []

    figs = [plt.figure(n) for n in new_nums]

    # Label figures so the deferred-show logic in main() can prune/show correctly.
    for fig in figs:
        fig.set_label('plot2d_show' if do_show else 'plot2d_file')

    # 5) Optional file output
    # We save a single composite image if multiple figures were created.
    # This mirrors plot_section_2d behavior and avoids requiring multiple output paths.
    if file_outputs:
        dpi = 150  # keep a stable default (can be extended later)
        spacing_px = 10

        images: List[Image.Image] = []
        for fig in figs:
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
            buf.seek(0)
            im = Image.open(buf).convert("RGB")
            im.load()
            buf.close()
            images.append(im)

        if not images:
            raise RuntimeError("No images were generated for plot_properties file output.")

        if len(images) == 1:
            composite = images[0]
        else:
            max_w = max(im.width for im in images)
            total_h = sum(im.height for im in images) + spacing_px * (len(images) - 1)
            composite = Image.new("RGB", (max_w, total_h), (255, 255, 255))
            y = 0
            for im in images:
                composite.paste(im, (0, y))
                y += im.height + spacing_px

        for out_path in file_outputs:
            outp = Path(out_path)
            if not outp.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {outp.parent}")
            composite.save(str(outp), dpi=(dpi, dpi))
            print(f"[OK] plot_properties wrote: {outp}")

    # 6) Mark that 2D figures should be shown at the end (ONLY if stdout requested)
    global want_show_2d
    if do_show:
        want_show_2d = "yes"


def _run_action_plot_weight(
    field: Any,
    stations_map: Dict[str, List[float]],
    action: Dict[str, Any],
) -> None:
    """Action: plot_weight

    Wrapper of:
        Visualizer.plot_weight(num_points=100)

    Key design points (per current CSFActions prototype)
    ----------------------------------------------------
    1) This action does NOT use 'stations'. It always samples between the CSF endpoints.
       That is why it is listed in STATIONS_FORBIDDEN and the validator rejects 'stations:'.

    2) Output semantics match plot_section_2d and plot_properties:
       - If output is omitted -> default ["stdout"] -> keep figures for the final GUI window.
       - If output contains file paths -> save to file.
       - If output does NOT contain "stdout" -> file-only (do not show, and do not set want_show_2d).

    3) The plotting window is shown only ONCE at the very end of main() (deferred plt.show()).
       However, the current Visualizer.plot_weight implementation (in section_field)
       ends with a direct plt.show(). To preserve the deferred-show protocol without
       editing section_field, we temporarily monkey-patch plt.show to a no-op during
       the call.

       This is intentionally localized and reversible:
       - we restore the original plt.show in a finally block
       - we then label the newly created figures and optionally save them

    Notes
    -----
    - plot_weight is intended to visualize the *effective weight protocol* used by
      ContinuousSectionField._interpolate_weight, including user-defined laws.
    - The action produces 1 (or more) matplotlib figure(s). We label them as:
        'plot2d_show' -> keep for the final interactive plt.show()
        'plot2d_file' -> save to file only, close before plt.show()
      This keeps compatibility with the global deferred-show pruning logic.
    """
    # stations_map is unused by design (endpoints only).
    _ = stations_map

    if Visualizer is None:
        raise RuntimeError("Visualizer is not available (import failed).")

    import io

    # 1) Resolve parameters
    params = action.get("params", {}) or {}
    num_points = int(params.get("num_points", ACTION_SPECS["plot_weight"].params[0].default))

    # 2) Resolve outputs
    outputs = action.get("output")
    if outputs is None:
        outputs = ["stdout"]

    do_show = ("stdout" in outputs)
    file_outputs = [o for o in outputs if o != "stdout"]

    # 3) Call Visualizer while suppressing its internal plt.show()
    viz = Visualizer(field)

    # Capture current figure numbers so we can identify what this action creates.
    before = set(plt.get_fignums())

    old_show = plt.show

    def _noop_show(*args, **kwargs):
        """Temporary replacement for plt.show() during plot_weight.

        Visualizer.plot_weight currently ends with plt.show() which would
        prematurely open/flush the GUI window. We need to defer that until
        the end of main().
        """
        return None

    plt.show = _noop_show
    try:
        viz.plot_weight(num_points=num_points)
    finally:
        # Always restore the original show function.
        plt.show = old_show

    # 4) Determine which figure(s) were created by this action
    after = set(plt.get_fignums())
    new_nums = sorted(after - before)

    # If Visualizer reused an existing figure (rare), fall back to current figure.
    if not new_nums:
        try:
            new_nums = [plt.gcf().number]
        except Exception:
            new_nums = []

    figs = [plt.figure(n) for n in new_nums]

    # Label figures so the deferred-show logic in main() can prune/show correctly.
    for fig in figs:
        fig.set_label('plot2d_show' if do_show else 'plot2d_file')

    # 5) Optional file output
    # We save a single composite image if multiple figures were created.
    # This mirrors plot_section_2d and plot_properties behavior.
    if file_outputs:
        dpi = 150  # stable default; can be made configurable later if needed
        spacing_px = 10

        images: List[Image.Image] = []
        for fig in figs:
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
            buf.seek(0)
            im = Image.open(buf).convert("RGB")
            im.load()
            buf.close()
            images.append(im)

        if not images:
            raise RuntimeError("No images were generated for plot_weight file output.")

        if len(images) == 1:
            composite = images[0]
        else:
            max_w = max(im.width for im in images)
            total_h = sum(im.height for im in images) + spacing_px * (len(images) - 1)
            composite = Image.new("RGB", (max_w, total_h), (255, 255, 255))
            y = 0
            for im in images:
                composite.paste(im, (0, y))
                y += im.height + spacing_px

        for out_path in file_outputs:
            outp = Path(out_path)
            if not outp.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {outp.parent}")
            composite.save(str(outp), dpi=(dpi, dpi))
            print(f"[OK] plot_weight wrote: {outp}")

    # 6) Mark that 2D figures should be shown at the end (ONLY if stdout requested)
    global want_show_2d
    if do_show:
        want_show_2d = "yes"

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

def _get_bool_param_strict(params: Dict[str, Any], name: str, default: bool, *, path: str) -> bool:
    '''
    Strict boolean parameter reader.

    Rationale
    ---------
    Using Python's builtin `bool(x)` on non-bool values is dangerous:
      - bool("False") == True   (non-empty string is truthy)
    For CSF Actions we want a non-ambiguous contract:
      - YAML booleans MUST be real booleans (true/false), not quoted strings.
    '''
    if params is None:
        return default
    if name not in params or params[name] is None:
        return default
    v = params[name]
    if isinstance(v, bool):
        return v
    raise TypeError(
        f"{path}: parameter '{name}' must be a YAML boolean (true/false), "
        f"not {type(v).__name__}={v!r}. Remove quotes if you wrote it as a string."
    )


def _load_actions() -> None:
    """Populate ACTION_RUNNERS with the set of implemented actions.

    Baseline step (low-impact):
    - Actions are still defined in this file.
    - We register them explicitly to drive a single dispatch path.

    This is a no-op after the first call.
    """
    global _ACTIONS_LOADED
    if _ACTIONS_LOADED:
        return

    def _wrap_no_debug(fn: Any) -> Any:
        """Adapter: expose a common runner signature and ignore debug_flag."""
        def _runner(field: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool = False) -> None:
            fn(field, stations_map, action)
        return _runner

    def _wrap_with_debug(fn: Any) -> Any:
        """Adapter: expose a common runner signature and forward debug_flag."""
        def _runner(field: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool = False) -> None:
            fn(field, stations_map, action, debug_flag=debug_flag)
        return _runner

    # Explicit registrations for the current monolithic baseline.
    register_action(ACTION_SPECS["section_full_analysis"], _wrap_no_debug(_run_action_section_full_analysis))

    # section_selected_analysis action migrated to actions/section_selected_analysis.py (explicit registration; no side effects).
    from actions.section_selected_analysis import register as register_section_selected_analysis  # local import to avoid import cycles
    register_section_selected_analysis(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        expand_station_names=_expand_station_names,
        section_full_analysis=section_full_analysis,
    )


    # section_area_by_weight action migrated to actions/section_area_by_weight.py (explicit registration; no side effects).
    from actions.section_area_by_weight import register as register_section_area_by_weight  # local import to avoid import cycles
    register_section_area_by_weight(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        expand_station_names=_expand_station_names,
        polygon_surface_w1_inners0=polygon_surface_w1_inners0,
    )
    from actions.volume import register as register_volume  # local import to avoid import cycles
    register_volume(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        expand_station_names=_expand_station_names,
        polygon_surface_w1_inners0=polygon_surface_w1_inners0,
        csf_weight_catalog_by_pair=csf_weight_catalog_by_pair,
        csf_weights_by_pair_at_z=csf_weights_by_pair_at_z,
    )
    # export_yaml action migrated to actions/export_yaml.py (explicit registration; no side effects).
    from actions.export_yaml import register as register_export_yaml  # local import to avoid import cycles
    register_export_yaml(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        expand_station_names=_expand_station_names,
    )
    # write_opensees_geometry action migrated to actions/write_opensees_geometry.py (explicit registration; no side effects).
    from actions.write_opensees_geometry import register as register_write_opensees_geometry  # local import to avoid import cycles
    register_write_opensees_geometry(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        write_opensees_geometry=write_opensees_geometry,
    )
    # write_sap2000_geometry action migrated to actions/write_sap2000_geometry.py (explicit registration; no side effects).
    from actions.write_sap2000_geometry import register as register_write_sap2000_geometry  # local import to avoid import cycles
    register_write_sap2000_geometry(
        register_action,
        spec=ACTION_SPECS["write_sap2000_geometry"],
        write_sap2000_template_pack=write_sap2000_template_pack,
    )
    # weight_lab_zrelative action migrated to actions/weight_lab_zrelative.py (explicit registration; no side effects).
    from actions.weight_lab_zrelative import register as register_weight_lab_zrelative  # local import to avoid import cycles
    register_weight_lab_zrelative(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        expand_station_names=_expand_station_names,
        safe_evaluate_weight_zrelative=safe_evaluate_weight_zrelative,
    )
    # plot_volume_3d action migrated to actions/plot_volume_3d.py (explicit registration; no side effects).
    from actions.plot_volume_3d import register as register_plot_volume_3d  # local import to avoid import cycles
    register_plot_volume_3d(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        Visualizer=Visualizer,
    )
    # plot_properties action migrated to actions/plot_properties.py (explicit registration; no side effects).
    from actions.plot_properties import register as register_plot_properties  # local import to avoid import cycles
    register_plot_properties(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        Visualizer=Visualizer,
    )
    # plot_weight action migrated to actions/plot_weight.py (explicit registration; no side effects).
    from actions.plot_weight import register as register_plot_weight  # local import to avoid import cycles
    register_plot_weight(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        Visualizer=Visualizer,
    )
    # plot_section_2d action migrated to actions/plot_section_2d.py (explicit registration; no side effects).
    from actions.plot_section_2d import register as register_plot_section_2d  # local import to avoid import cycles
    register_plot_section_2d(
        register_action,
        ActionSpec=ActionSpec,
        ParamSpec=ParamSpec,
        expand_station_names=_expand_station_names,
        get_bool_param_strict=_get_bool_param_strict,
        Visualizer=Visualizer,
    )

    _ACTIONS_LOADED = True


def _run_actions(field: Any, actions_root: Dict[str, Any]) -> Tuple[bool, List[Issue]]:
    """
    Execute actions sequentially.

    Returns:
      (ok, issues)
    """

    issues: List[Issue] = []

    stations_map: Dict[str, List[float]] = actions_root["_stations_map"]
    actions_list: List[Dict[str, Any]] = actions_root["_actions_list"]

    # Ensure imports needed for execution exist
    if not _ensure_analysis_imports_or_error(issues, filepath="<runtime>", actions_list=actions_list):
        return False, issues

    # Ensure the runners registry is populated (no-op after the first call).
    _load_actions()

    debug_flag = bool(actions_root.get("_debug", False))

    # Execution loop
    for idx, action in enumerate(actions_list):
        name = action["name"]
        print(f"\n=== Running action {idx+1}/{len(actions_list)}: {name} ===")

        runner = ACTION_RUNNERS.get(name)
        if runner is None:
            # Placeholder actions: stop with controlled error
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_NOT_IMPLEMENTED",
                    path=f"{TOP_KEY}.actions[{idx}].{name}",
                    message=f"Action '{name}' is not implemented yet.",
                    hint="Remove this action or implement it in CSFActions.py.",
                    context={"action": name},
                )
            )
            return False, issues

        # ---------------------------------------------------------------------
        # plot_section_2d: mirror params -> root-level keys (compatibility)
        # This allows runners that read action["show_*"] instead of action["params"]["show_*"].
        # ---------------------------------------------------------------------
        if name == "plot_section_2d":
            # No merge here: normalized params already prepared upstream.
            params = action.get("params", {}) or {}

            # Compatibility mirror for runners that still read root-level keys.
            if "show_ids" in params:
                action["show_ids"] = params["show_ids"]
            if "show_weights" in params:
                action["show_weights"] = params["show_weights"]
            if "show_vertex_ids" in params:
                action["show_vertex_ids"] = params["show_vertex_ids"]



        try:
            runner(field, stations_map, action, debug_flag=debug_flag)
        except Exception as e:
            issues.append(
                CSFIssues.make(
                    "CSFA_E_ACTION_RUNTIME",
                    path=f"{TOP_KEY}.actions[{idx}].{name}",
                    message=f"Action '{name}' failed during execution.",
                    hint="See Details for the runtime error.",
                    context={"details": str(e)},
                )
            )
            return False, issues

    return True, issues


# ---------------------------------------------------------------------------
# Geometry loading
# ---------------------------------------------------------------------------

def _load_geometry(geometry_path: Path) -> Tuple[Optional[Any], List[Issue]]:
    """
    Load CSF geometry using CSFReader.
    Always return CSFReader issues (warnings/errors) so they can be printed.
    """
    try:
        res = CSFReader().read_file(str(geometry_path))
    except Exception as e:
        return None, [
            CSFIssues.make(
                "CSF_E_IO_READ",
                path="$",
                message="Unexpected failure while reading geometry file.",
                hint="Check file permissions and format.",
                context={"details": str(e)},
            )
        ]

    # Always pass through issues from CSFReader
    issues = list(getattr(res, "issues", []) or [])
    if not getattr(res, "ok", False):
        return None, issues

    return res.field, issues


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="CSFActions",
        description="Run CSF geometry + actions from YAML files (non-Python workflow).",
        formatter_class=argparse.RawTextHelpFormatter,
    )



    parser.add_argument(
        "geometry",
        nargs="?",
        help=(
            "GEOMETRY\n"
            "  Path to the CSF geometry YAML file (input geometry).\n"
            "\n"
            "WHAT IT IS\n"
            "  - A CSF (Continuous Section Field) definition loaded/validated by CSFReader().read_file(...)\n"
            "  - It defines end sections (S0/S1), polygons, materials/weights, etc.\n"
            "\n"
            "PATH RULES\n"
            "  - Absolute or relative path (relative to the current working directory).\n"
            "  - Linux/macOS:   ./geometry.yaml   or   /abs/path/geometry.yaml\n"
            "  - Windows:       .\\geometry.yaml   or   C:\\path\\geometry.yaml\n"
            "\n"
            "IF OMITTED\n"
            "  - The program prints usage and exits.\n"
        ),
    )


    parser.add_argument(
        "actions",
        nargs="?",
        help=(
            "ACTIONS\n"
            "  Path to the CSF actions YAML file (execution plan).\n"
            "\n"
            "GOAL\n"
            "  Run CSF workflows WITHOUT writing Python.\n"
            "  The runner loads geometry.yaml, validates actions.yaml, then executes the ordered action list.\n"
            "\n"
            "REQUIRED ROOT KEY\n"
            "  CSF_ACTIONS:\n"
            "\n"
            "MINIMAL STRUCTURE\n"
            "  CSF_ACTIONS:\n"
            "    stations:\n"
            "      station_edge:  [0.0, 87.6]\n"
            "      station_dense: [0.0, 8.76, 17.52]\n"
            "    actions:\n"
            "      - section_full_analysis:\n"
            "          stations: [station_dense]\n"
            "          output: [stdout, out/full_analysis.csv]\n"
            "          params:\n"
            "            fmt_display: '.12f'\n"
            "\n"
            "COMMON ACTION FIELDS (ENVELOPE)\n"
            "  stations:\n"
            "    - Usually REQUIRED (list of station-set names).\n"
            "    - Some actions FORBID stations (see action list below).\n"
            "  output:\n"
            "    - Optional list.\n"
            "    - If the *output key is missing*, default is: ['stdout']\n"
            "    - If output exists but does NOT contain 'stdout' => file-only (no on-screen display).\n"
            "  params:\n"
            "    - Optional mapping of action-specific parameters (validated per action).\n"
            "\n"
            "IMPLEMENTED ACTIONS (CURRENT)\n"
            "  1) section_full_analysis  (stations REQUIRED)\n"
            "     - stdout: human-readable report (tables per section)\n"
            "     - *.csv : numeric table (z + analysis keys)\n"
            "     - other : captured text report\n"
            "\n"
            "  1b) section_selected_analysis (stations REQUIRED)\n"
            "     - Compute only the requested section properties at each station\n"
            "     - Requires: properties: [ ... ] (non-empty; allowed keys are the same as plot_properties)\n"
            "     - stdout: compact report (selected keys only)\n"
            "     - *.csv : numeric table (z + selected keys, order preserved)\n"
            "     - other : captured text report\n"
            "     - Optional: params.fmt_display (default '.8f')\n"
            "\n"
            "  2) plot_section_2d         (stations REQUIRED)\n"
            "     - 2D plots at each z\n"
            "     - output contains 'stdout' => keep plots for final on-screen display\n"
            "     - image file(s) => save; multiple z => single composite vertical image\n"
            "\n"
            "  3) plot_volume_3d          (stations FORBIDDEN)\n"
            "     - 3D ruled volume between endpoints\n"
            "     - Display-only (shown at end). File saving is disabled by design.\n"
            "\n"
            "  4) plot_properties         (stations FORBIDDEN)\n"
            "     - Plots selected section properties along the length\n"
            "     - Requires: properties: [ ... ] (allowed keys listed below)\n"
            "     - Optional: params.num_points (default 100)\n"
            "\n"
            "     Allowed keys + meaning:\n"
            "       A                  - Total net cross-sectional area\n"
            "       Cx                 - Horizontal centroid (X)\n"
            "       Cy                 - Vertical centroid (Y)\n"
            "       Ix                 - Second moment about centroidal X-axis\n"
            "       Iy                 - Second moment about centroidal Y-axis\n"
            "       Ixy                - Product of inertia (symmetry indicator)\n"
            "       J                  - Polar second moment (Ix + Iy)\n"
            "       I1                 - Major principal second moment\n"
            "       I2                 - Minor principal second moment\n"
            "       rx                 - Radius of gyration (about X)\n"
            "       ry                 - Radius of gyration (about Y)\n"
            "       Wx                 - Elastic section modulus about X\n"
            "       Wy                 - Elastic section modulus about Y\n"
            "       K_torsion          - Semi-empirical torsional stiffness approximation\n"
            "       Q_na               - First moment of area at neutral axis\n"
            "       J_sv               - Effective St. Venant torsional constant (J)\n"
            "       J_sv_wall          - computes the Saint-Venant torsional constant for open thin-walled walls\n"
            "       J_sv_cell          - Saint-Venant torsional constant for closed thin-walled by applying  Bredt–Batho formula\n"            
            "       J_s_vroark         - Refined J (Roark-Young thickness correction)\n"
            "       J_s_vroark_fidelity- Fidelity / reliability indicator\n"
            "\n"
            "     Example:\n"
            "       - plot_properties:\n"
            "           output: [stdout, out/properties.bmp]\n"
            "           params: {num_points: 70}\n"
            "           properties: [A, Ix, Iy, J]\n"
            "\n"
            "  5) plot_weight             (stations FORBIDDEN)\n"
            "     - Calls Visualizer.plot_weight(num_points=...)\n"
            "     - output rules same as plot_section_2d (stdout => display; otherwise file-only)\n"
            "\n"
            "  6) weight_lab_zrelative     (stations REQUIRED; TEXT-ONLY)\n"
            "     - Inspector for user weight-law formulas at RELATIVE z in [0..L]\n"
            "     - Requires: weith_law: ['expr1', 'expr2', ...]\n"
            "     - For each law, each z, and each polygon pair (p0->p1): prints evaluation\n"
            "     - file-only supported (e.g., out/weight_inspector.txt)\n"
            "\n"
                        "\n"
            "  7) section_area_by_weight    (stations REQUIRED)\n"
            "     - Computes an area breakdown grouped by ABSOLUTE weight W_abs(z).\n"
            "     - Intended for composite sections with deterministic nesting (no intersections).\n"
            "     - stdout: per-station report; *.csv: long-form table; other: captured text report.\n"
            "\n"
            "  7b) volume                   (stations REQUIRED: exactly two z values)\n     - Integrates per-polygon occupied volumes between [z1, z2] (quantity take-off).\n     - Uses polygon_surface_w1_inners0 + Gauss–Legendre quadrature.\n     - stdout: report; *.csv: one row per polygon; other: captured text report.\n     - Optional: params.n_points (default 20), params.fmt_display (default '.6g').\n     - Note: params.w_tol is accepted but currently unused (ignored).\n\n  8) export_yaml               (stations REQUIRED; FILE-ONLY)\n"
            "     - Exports a new CSF geometry YAML reconstructed from EXACTLY TWO stations [z0, z1].\n"
            "     - Requires a station set with exactly two numbers; stdout is forbidden.\n"
            "\n"
            "  9) write_opensees_geometry   (stations FORBIDDEN; FILE-ONLY)\n"
            "     - Writes an OpenSees Tcl geometry file intended as a deterministic data contract.\n"
            "     - Requires params: n_points, E_ref, nu.\n"
            "\n"
            " 10) write_sap2000_geometry    (stations OPTIONAL; FILE-ONLY)\n"
            "     - Writes a SAP2000 template-pack text file (copy/paste helper) and optional preview plot.\n"
            "     - Requires params: n_intervals, E_ref, nu. Optional: material_name, mode, include_plot, plot_filename.\n"
            "\n"
                        "\n"
            "ALIASES AND RESERVED ACTIONS\n"
            "  - weight_lab: recognized by schema for future work; execution is currently not available.\n"
            "\n"
"YAML QUICK PRIMER (VERY SHORT)\n"
            "  - Indentation matters: use SPACES (recommended 2). No tabs.\n"
            "  - Lists use '-'. Example:\n"
            "      actions:\n"
            "        - section_full_analysis:\n"
            "            ...\n"
            "  - Strings: use quotes for formulas.\n"
            "  - Booleans: true/false (lowercase).\n"
            "  - Comments start with '#'.\n"
            "\n"

            "ACTIONS\n"
            "  Path to the CSF actions YAML file (execution plan).\n"
            "\n"
            "export_yaml  (stations REQUIRED; FILE-ONLY)\n"
            "  Purpose\n"
            "    - Export a new CSF geometry YAML built from two intermediate sections.\n"
            "    - Internally calls: field.write_section(z0, z1, yaml_path)\n"
            "\n"
            "  Input rule\n"
            "    - The referenced station-set MUST contain EXACTLY TWO z values.\n"
            "      If it contains 1 or >2 values, the runner raises a friendly error.\n"
            "\n"
            "  Output rule\n"
            "    - output is REQUIRED and must contain exactly ONE YAML filepath.\n"
            "    - 'stdout' is NOT supported for this action (it is file-only).\n"
            "\n"
            "  Example\n"
            "    CSF_ACTIONS:\n"
            "      stations:\n"
            "        station_subpart: [1.0, 8.0]\n"
            "      actions:\n"
            "        - export_yaml:\n"
            "            stations: [station_subpart]\n"
            "            output: [out/station_subpart.yaml]\n"
            "\n"
            "Notes\n"
            "  - The exported YAML is validated by write_section() itself.\n"
            "  - Ensure the output directory exists (e.g., create 'out/' beforehand).\n"
            "COMMON PITFALL\n"
            "  - Duplicate YAML keys (e.g., two 'actions:' blocks) may silently overwrite earlier ones.\n"
            "    Keep 'actions:' ONLY ONCE.\n"
            "\n"
            "IF OMITTED\n"
            "  - The program prints usage and exits.\n"
            "ACTIONS\n"
                "  Path to the CSF actions YAML file (execution plan).\n"
                "\n"
                "PURPOSE\n"
                "  - Run CSF workflows WITHOUT writing Python.\n"
                "  - The runner loads geometry.yaml, validates actions.yaml, then executes actions in order.\n"
                "\n"
                "REQUIRED ROOT KEY\n"
                "  CSF_ACTIONS:\n"
                "\n"
                "MINIMAL STRUCTURE (EXAMPLE)\n"
                "  CSF_ACTIONS:\n"
                "    stations:\n"
                "      station_edge:\n"
                "        - 0.0\n"
                "        - 10.0\n"
                "    actions:\n"
                "      - section_full_analysis:\n"
                "          stations: [station_edge]\n"
                "          output: [stdout]\n"
                "\n"
                "COMMON ACTION FIELDS (ENVELOPE)\n"
                "  - stations:\n"
                "      Usually REQUIRED for actions that operate at multiple z locations.\n"
                "      Some actions FORBID stations (see action-specific notes).\n"
                "  - output:\n"
                "      Optional list. If the output key is missing, the default is: [stdout].\n"
                "      If output is present but does NOT contain 'stdout', behavior is file-only (no display).\n"
                "  - params:\n"
                "      Optional mapping with action-specific parameters (validated per action).\n"
                "\n"
                "ACTION: write_opensees_geometry (FILE-ONLY, stations FORBIDDEN)\n"
                "  WHAT IT DOES\n"
                "    - Exports an OpenSees Tcl geometry file describing a CSF member discretized along z.\n"
                "    - Internally calls:\n"
                "        write_opensees_geometry(field, n_points, E_ref=..., nu=..., filename=...)\n"
                "    - The output contains nodes, an optional geomTransf placeholder, and one Elastic section per\n"
                "      integration station (plus comments with the z stations). Your downstream OpenSees script\n"
                "      (OpenSeesPy or Tcl) is responsible for defining the final element/integration layout.\n"
                "\n"
                "  YAML SCHEMA\n"
                "    - write_opensees_geometry:\n"
                "        output:\n"
                "          - out/geometry.tcl        # REQUIRED, exactly one path; stdout is NOT allowed\n"
                "        params:\n"
                "          n_points: 10              # REQUIRED int (number of integration stations)\n"
                "          E_ref: 2.1e+11            # REQUIRED float (use e+ notation; 2.1e11 becomes a string)\n"
                "          nu: 0.30                  # REQUIRED float\n"
                "\n"
                "  RULES / GOTCHAS\n"
                "    - stations is FORBIDDEN for this action (it uses its own integration station generation).\n"
                "    - output is REQUIRED and must be a single file path (file-only). Do not include 'stdout'.\n"
                "    - Scientific notation: use 'e+NN' or 'e-NN' (example: 2.1e+11). Some YAML loaders parse\n"
                "      '2.1e11' as a string.\n"
                "    - Material assumption: the exporter uses an isotropic elastic reference.\n"
                "      If the writer derives shear modulus, it typically uses: G = E_ref / (2*(1+nu)).\n"
                "\n"
                "YAML QUICK PRIMER\n"
                "  - Indentation matters: use SPACES (recommended 2). Do NOT use tabs.\n"
                "  - Lists use '-'. Example:\n"
                "      output:\n"
                "        - stdout\n"
                "        - out/file.csv\n"
                "  - Booleans: true/false (lowercase). Numbers: 1, 1.0, 2.1e+11.\n"
                "  - Comments start with '#'.\n"
                "  - Avoid duplicate keys (e.g., two 'actions:' blocks) because YAML may overwrite silently.\n"
                "WRITE_SAP2000_GEOMETRY (action)  [SAP2000 TEMPLATE PACK]\n"
                "-------------------------------------------------------\n"
                "Purpose:\n"
                "  Generate a SAP2000 \"template pack\" text file from the current CSF field.\n"
                "  This is NOT a guaranteed importable .s2k. It is a complete, well-commented\n"
                "  DATA + COPY/PASTE pack that contains:\n"
                "    - Stations (absolute z) and section naming per station\n"
                "    - Table C: core numeric properties per station (A, Cx, Cy, Ix, Iy, Ixy, J)\n"
                "    - Candidate SAP2000 table blocks (JOINT COORDINATES, CONNECTIVITY - FRAME,\n"
                "      FRAME SECTION PROPERTIES - GENERAL, FRAME SECTION ASSIGNMENTS)\n"
                "    - A checklist of items you may still need to define in SAP2000\n"
                "\n"
                "Stations:\n"
                "  FORBIDDEN. Do NOT provide 'stations:' for this action.\n"
                "  Stations are generated internally using Lobatto-type sampling over the full\n"
                "  CSF domain [z0..z1].\n"
                "\n"
                "Output:\n"
                "  REQUIRED and file-only (stdout is NOT allowed).\n"
                "  output must be a YAML LIST with exactly one path, e.g.:\n"
                "    - write_sap2000_geometry:\n"
                "        output:\n"
                "          - out/model_export_template.txt\n"
                "        params:\n"
                "          n_intervals: 6\n"
                "          material_name: \"S355\"\n"
                "          E_ref: 2.1e+11\n"
                "          nu: 0.30\n"
                "          mode: \"BOTH\"\n"
                "          include_plot: true\n"
                "          plot_filename: \"section_variation.png\"\n"
                "\n"
                "Parameters (params:)\n"
                "  n_intervals (int, required)\n"
                "    Number of intervals along the member. The number of stations is:\n"
                "      n_stations = n_intervals + 1\n"
                "    (Includes both endpoints. Frames/segments are built between consecutive stations.)\n"
                "\n"
                "  material_name (str, required)\n"
                "    A label written into the candidate section property lines (SAP-side material name).\n"
                "\n"
                "  E_ref (float, required)\n"
                "    \"Suggested\" Young modulus printed in the template header and material notes.\n"
                "    Units are not enforced; keep your unit system consistent in SAP2000.\n"
                "\n"
                "  nu (float, required)\n"
                "    \"Suggested\" Poisson ratio printed in the template header. The template also prints:\n"
                "      G_ref = E_ref / (2*(1+nu))  (isotropic assumption)\n"
                "\n"
                "  mode (str, required)\n"
                "    One of: \"CENTROIDAL_LINE\", \"REFERENCE_LINE\", \"BOTH\".\n"
                "    - CENTROIDAL_LINE: joint coordinates follow the centroid Cx(z),Cy(z).\n"
                "    - REFERENCE_LINE: joints are on a nominal axis (X=0,Y=0); Cx,Cy are provided\n"
                "      as offsets/eccentricities (placeholder section).\n"
                "    - BOTH: prints both blocks; in SAP you must choose ONE (do not paste both JOINT tables).\n"
                "\n"
                "  include_plot (bool, required)\n"
                "    If true and matplotlib is available, writes a preview PNG of property variation.\n"
                "\n"
                "  plot_filename (str, required)\n"
                "    Path for the preview plot PNG (written only if include_plot is true).\n"
                "\n"
                "Hard-coded behavior:\n"
                "  - show_plot is forced to False (no interactive window). The preview, if enabled,\n"
                "    is saved to plot_filename only.\n"
                "\n"
                "Common pitfalls:\n"
                "  - Do not use 'stdout' in output (file-only).\n"
                "  - Use numeric scientific notation that YAML parses as a number (e.g. 2.1e+11).\n"
                "    Some YAML loaders treat '2.1e11' (missing +) as a string.\n"
                "\n"

        ),
    )



    parser.add_argument(
        "--help-actions",
        action="store_true",
        help=(
            "Print the CSF actions catalog and exit.\n"
            "\n"
            "The catalog documents the common YAML envelope and the schema of each action.\n"
            "\n"
            "Includes:\n"
            "  - action summary + detailed description\n"
            "  - whether stations are REQUIRED or FORBIDDEN\n"
            "  - parameter list with types, defaults, and aliases\n"
            "  - output behavior notes (stdout vs file-only)\n"
        ),
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Validate geometry.yaml and actions.yaml but DO NOT execute actions.\n"
            "\n"
            "Validation checks:\n"
            "  - required keys (CSF_ACTIONS, stations, actions)\n"
            "  - station references used by actions\n"
            "  - per-action schema rules (stations required/forbidden)\n"
            "  - params type checks + defaults\n"
            "  - plot_properties: property keys must be allowed\n"
            "  - weight_lab_zrelative: weith_law must be a non-empty list of non-empty strings\n"
            "\n"
            "Reporting:\n"
            "  - Errors: friendly messages + YAML snippet/caret when available\n"
            "  - Warnings: context only (no snippet)\n"
        ),
    )












    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Developer mode: enable extra diagnostics.\n"
            "\n"
            "Notes:\n"
            "  - End users should NOT use this.\n"
            "  - When enabled, actions may emit additional debug prints.\n"
            "  - Normal mode never shows raw Python tracebacks.\n"
        ),
    )

    args = parser.parse_args(argv)

    if args.help_actions:
        print_actions_help()
        return 0

    # Development defaults if user does not pass args
    geometry_path = Path(args.geometry) if args.geometry else Path("case.yaml")
    actions_path = Path(args.actions) if args.actions else Path("actions_example.yaml")
    if args.geometry is None and args.actions is None:
        print(f"[DEV] Using defaults: geometry={geometry_path}, actions={actions_path}")

    # ------------------------------------------------------------------
    # 1) Basic file checks
    # ------------------------------------------------------------------
    if not geometry_path.exists():
        print(f"[ERROR] Geometry file not found: {geometry_path}")
        print("Hint: check the file name and current working directory.")
        return 2

    if not actions_path.exists():
        print(f"[ERROR] Actions file not found: {actions_path}")
        print("Hint: check the file name and current working directory.")
        return 2

    # ------------------------------------------------------------------
    # 2) Load geometry and print issues always
    # ------------------------------------------------------------------
    field, geom_issues = _load_geometry(geometry_path)
    if geom_issues:
        print(CSFIssues.format_report(geom_issues))

    if field is None:
        print("[ERROR] Geometry could not be loaded. Fix the errors above and re-run.")
        return 1

    # Ensure we have a ContinuousSectionField object (either already loaded, or build from endpoints)
    if ContinuousSectionField is None:
        print("[ERROR] ContinuousSectionField import failed. Check your installation.")
        return 1

    if isinstance(field, ContinuousSectionField):
        csf_field = field
    elif hasattr(field, "s0") and hasattr(field, "s1"):
        csf_field = ContinuousSectionField(section0=field.s0, section1=field.s1)
    else:
        print("[ERROR] Geometry object does not look like a CSF field (missing s0/s1).")
        return 1

    print("ContinuousSectionField instantiated successfully.")

    # ------------------------------------------------------------------
    # 3) Read actions.yaml text (UTF-8)
    # ------------------------------------------------------------------
    try:
        actions_text = actions_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues = [
            CSFIssues.make(
                "CSFA_E_ENCODING",
                path="$",
                message="Actions file is not valid UTF-8.",
                hint="Save actions.yaml as UTF-8 and try again.",
                context={"filepath": str(actions_path)},
            )
        ]
        print(CSFIssues.format_report(issues))
        return 2
    except Exception as e:
        issues = [
            CSFIssues.make(
                "CSFA_E_IO_READ",
                path="$",
                message="Cannot read actions file.",
                hint="Check file permissions and path.",
                context={"filepath": str(actions_path), "details": str(e)},
            )
        ]
        print(CSFIssues.format_report(issues))
        return 2

    # ------------------------------------------------------------------
    # 4) Parse + FULL validate actions.yaml (mandatory)
    # ------------------------------------------------------------------
    doc, parse_issues = _parse_actions_yaml(actions_text, str(actions_path))
    if parse_issues:
        print(CSFIssues.format_report(parse_issues))
    if doc is None:
        print("[ERROR] Actions file could not be parsed. Fix the errors above and re-run.")
        return 1

    normalized_root, val_issues = _validate_actions_doc(doc, actions_text, str(actions_path))
    if val_issues:
        print(CSFIssues.format_report(val_issues))

    if normalized_root is None or any(i.severity == Severity.ERROR for i in val_issues):
        print("[ERROR] Actions file is not valid. Fix the errors above and re-run.")
        return 1

    print("Actions file validated successfully.")

    if args.validate_only:
        print("Validation-only mode: no actions executed.")
        return 0

    # ------------------------------------------------------------------
    # 5) Execute actions
    # ------------------------------------------------------------------
    normalized_root["_debug"] = bool(args.debug)
    ok, run_issues = _run_actions(csf_field, normalized_root)
    if run_issues:
        print(CSFIssues.format_report(run_issues))

    if not ok:
        print("[ERROR] One or more actions failed.")
        return 1
    print("All actions completed successfully.")


    try:
        # Deferred show strategy
        # - plotting actions may request interactive display via legacy globals want_show_2d / want_show_3d
        # - for modular actions that do not touch those globals, we infer intent from figure labels
        # - we prune file-only figures when interactive display is requested
        # - we then show figures sequentially with an auto-advance delay (no manual intervention)
        lis_fig = [plt.figure(n) for n in plt.get_fignums()]
        
        # Determine whether interactive display is requested.
        # Primary source: explicit global flags set by monolithic/local action handlers.
        show_2d = (want_show_2d is not None)
        show_3d = (want_show_3d is not None)

        # Compatibility source: modular actions may only label figures and not touch globals.
        # If any currently open figure is explicitly labelled as showable, enable the related
        # display channel even when the legacy global flag was not set.
        try:
            _open_figs = [plt.figure(n) for n in plt.get_fignums()]
            if not show_2d and any(((_f.get_label() or "").strip() in ("plot2d", "plot2d_show")) for _f in _open_figs):
                show_2d = True
            if not show_3d and any(((_f.get_label() or "").strip() in ("plot3d", "plot3d_show")) for _f in _open_figs):
                show_3d = True
        except Exception:
            pass
        
        if not show_2d:
            for _fig in lis_fig:
                if _fig.get_label() in ("plot2d"):
                    show_2d = True
                    break
        
        if not show_3d:
            for _fig in lis_fig:
                if _fig.get_label() in PLOT_3D_LABELS:
                    show_3d = True
                    break
        

        # Re-collect and FILTER figures according to per-action visibility labels.
        # IMPORTANT:
        # - Figures labelled as *_file are never shown.
        # - 2D display is allowed only when a 2D action explicitly requested stdout
        #   (legacy global flag) OR when a legacy labelled 2D figure is present.
        # - 3D display follows the same rule.
        # - Unlabelled figures are treated conservatively as non-showable.
        all_figs = [plt.figure(n) for n in plt.get_fignums()]
        keep_figs = []

        for _fig in all_figs:
            _label = (_fig.get_label() or "").strip()

            # 2D labelled figures
            if _label in PLOT_2D_LABELS:
                # Legacy 'plot2d' is showable only if 2D show is enabled.
                if _label == "plot2d":
                    if show_2d:
                        keep_figs.append(_fig)
                    else:
                        try:
                            plt.close(_fig)
                        except Exception:
                            pass
                    continue

                # Explicit visibility map for modular labels.
                _allowed = bool(PLOT_2D_VISIBILITY.get(_label, False))
                if show_2d and _allowed:
                    keep_figs.append(_fig)
                else:
                    try:
                        plt.close(_fig)
                    except Exception:
                        pass
                continue

            # 3D labelled figures
            if _label in PLOT_3D_LABELS:
                _allowed = bool(PLOT_3D_VISIBILITY.get(_label, False))
                if show_3d and _allowed:
                    keep_figs.append(_fig)
                else:
                    try:
                        plt.close(_fig)
                    except Exception:
                        pass
                continue

            # Any unlabelled/unknown figure is not shown by default.
            try:
                plt.close(_fig)
            except Exception:
                pass
        
        def _show_figs_sequentially(figs, *, wait_for_close: bool = True, seconds: float = 0.9) -> None:
            """Show figures sequentially.

            Behavior
            --------
            - wait_for_close=True: the next figure is shown only after the user closes the current one.
            - wait_for_close=False: the next figure is shown after `seconds` (auto-advance), and the current
              figure is closed automatically.

            Notes
            -----
            - We intentionally avoid calling a single blocking plt.show() because it shows all figures at once
              and is backend-dependent.
            - Using ion()+pause() provides predictable event processing across common backends.
            """
            # Use interactive mode + pause for event processing across backends.
            try:
                #plt.ion()
                None
            except Exception:
                pass

            for _fig in figs:

                try:
                    #plt.show(block=False)
                    None
                except Exception:
                    # Some backends may not accept block=...
                    try:
                        
                        #plt.show()
                        None
                    except Exception:
                        pass

                if wait_for_close:
                    # Wait until the user closes the current figure.
                    try:
                        while plt.fignum_exists(_fig.number):
                            plt.pause(0.1)
                    except Exception:
                        # If the backend does not support fignum_exists, fall back to a long pause.
                        plt.pause(9999.0)
                else:
                    try:
                        plt.pause(seconds)
                    except Exception:
                        pass
                    try:
                        plt.close(_fig)
                    except Exception:
                        pass

            try:
                plt.ioff()
            except Exception:
                pass

        # Show only if some action requested it; otherwise just ensure nothing is left open.
        if keep_figs and (show_2d or show_3d):
            _show_figs_sequentially(keep_figs, wait_for_close=True, seconds=0.9)
            
        else:
            # Ensure no leftover figures remain open.
            try:
                plt.close("all")
            except Exception:
                pass
        
    except Exception as e:
        raise RuntimeError(f"Plot error  {e}")
        pass
    return 0


if __name__ == "__main__":
    '''
    # Development defaults (used only if the user does NOT pass CLI args)
    DEV_GEOMETRY = "camerapole/tapered_hollow_octagon_csf_Full_L.yaml"
    DEV_ACTIONS = "camerapole/actions_camerapole.yaml"

    #DEV_GEOMETRY = "nrel_5mv/nrel_5mv.yaml"
    #DEV_ACTIONS = "nrel_5mv/actions_example.yaml"
    #DEV_GEOMETRY = "camerapole/octagon_csf_Full_L.yaml"
    #DEV_ACTIONS = "camerapole/actions_camerapole.yaml"
    #DEV_HELP    ="--validate-only"
    # If no CLI args were provided, run with development defaults.
    # Otherwise, keep normal CLI behavior.
    
    argv = None
    if len(sys.argv) == 1:
        argv = [DEV_GEOMETRY, DEV_ACTIONS]
        print(f"[DEV] Using defaults: geometry={DEV_GEOMETRY}, actions={DEV_ACTIONS}")
    
    try:
        raise SystemExit(main(argv))
    except SystemExit:
        raise
    except Exception as e:
        # Final fallback: user-friendly crash message (no traceback)
        print("[ERROR] Unexpected crash.")
        print(f"Details: {e}")
        # For development you usually do NOT want to re-raise (would show a traceback).
        # Exit with code 1 instead.
        raise SystemExit(1)
    '''
    
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print("[ERROR] Unexpected crash.")
        print(f"Details: {e}")
        raise SystemExit(1)
    

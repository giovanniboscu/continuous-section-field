# actions/section_selected_analysis.py
#
# This action module is part of the CSFActions modularization.
# It intentionally avoids importing CSFActions to prevent circular imports.
#
# CHANGE (2026-02): Added parameter `torsion_alpha_sv` (required only when 'J_sv' is requested) for the solid Saint-Venant
# torsion approximation key 'J_sv'. The action prints the chosen alpha and, when 'J_sv'
# is requested, forces:
#     J_sv = torsion_alpha_sv * (Ix + Iy)
# about the weighted centroid.
#
# NOTE: This is a modeling policy knob. It is NOT used for 'J_sv_wall' or 'J_sv_cell'.

from __future__ import annotations

import csv
import io
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


# -----------------------------------------------------------------------------
# Allowed keys + meaning (kept in one place to avoid drift between help and output)
# -----------------------------------------------------------------------------

_ALLOWED_KEYS_MEANING: Dict[str, str] = {
    "A": "Total net cross-sectional area",
    "Cx": "Horizontal centroid (X)",
    "Cy": "Vertical centroid (Y)",
    "Ix": "Second moment about centroidal X-axis",
    "Iy": "Second moment about centroidal Y-axis",
    "Ixy": "Product of inertia (symmetry indicator)",
    "J": "Polar second moment (Ix + Iy)",
    "I1": "Major principal second moment",
    "I2": "Minor principal second moment",
    "rx": "Radius of gyration (about X)",
    "ry": "Radius of gyration (about Y)",
    "Wx": "Elastic section modulus about X",
    "Wy": "Elastic section modulus about Y",
    "K_torsion": "Semi-empirical torsional stiffness approximation",
    "Q_na": "First moment of area at neutral axis",
    "J_sv": "Effective St. Venant torsional constant (J)",
    "J_sv_wall": "Saint-Venant torsional constant for open thin-walled walls",
    "J_sv_cell": "Saint-Venant torsional constant for closed thin-walled cells (Bredt–Batho)",
    "J_s_vroark": "Refined J (Roark-Young thickness correction)",
    "J_s_vroark_fidelity": "Fidelity / reliability indicator"
}


def register(
    register_action,
    *,
    ActionSpec,
    ParamSpec,
    expand_station_names,
    section_full_analysis,
) -> None:
    """Register the section_selected_analysis action (SPEC + RUN)."""

    SPEC = ActionSpec(
        name="section_selected_analysis",
        summary="Compute user-selected weighted section properties at one or more stations (report/table).",
        description=(
            "Computes only the requested property keys at each station z, preserving the user order.\n"
            "\n"
            "YAML fields\n"
            "- stations:    REQUIRED. One or more station-set names defined under CSF_ACTIONS.stations (absolute z).\n"
            "- properties: REQUIRED. List of property keys to extract (order preserved; duplicates allowed).\n"
            "- output:      OPTIONAL. Default is [stdout]. Add file paths to write reports/tables to disk.\n"
            "              If output does NOT include 'stdout', the action is file-only.\n"
            "\n"
            "Outputs\n"
            "- stdout : compact report (selected keys only).\n"
            "- *.csv  : numeric table (z + selected keys).\n"
            "- other : captured text report (written to the given path).\n"
            "\n"
            "Params\n"
            "- torsion_alpha_sv (float, REQUIRED): scaling factor used ONLY for the solid Saint-Venant torsion\n"
            "  approximation key 'J_sv'. When 'J_sv' is requested, CSF enforces:\n"
            "      J_sv = torsion_alpha_sv * (Ix + Iy)\n"
            "  about the weighted centroid. This is a modeling choice (no automatic shape recognition).\n"
            "  Typical values: 1.0 (circular solid), 0.8436 (square-like solid).\n"
            "  Not used for 'J_sv_wall' or 'J_sv_cell'.\n"
            "- fmt_display (str, OPTIONAL): Python numeric format for printed reports (default '.8f').\n"
            "\n"
            "Allowed keys + meaning:\n"
            "  A                    - Total net cross-sectional area\n  Cx                   - Horizontal centroid (X)\n  Cy                   - Vertical centroid (Y)\n  Ix                   - Second moment about centroidal X-axis\n  Iy                   - Second moment about centroidal Y-axis\n  Ixy                  - Product of inertia (symmetry indicator)\n  J                    - Polar second moment (Ix + Iy)\n  I1                   - Major principal second moment\n  I2                   - Minor principal second moment\n  rx                   - Radius of gyration (about X)\n  ry                   - Radius of gyration (about Y)\n  Wx                   - Elastic section modulus about X\n  Wy                   - Elastic section modulus about Y\n  K_torsion            - Semi-empirical torsional stiffness approximation\n  Q_na                 - First moment of area at neutral axis\n  J_sv                 - Effective St. Venant torsional constant (J)\n  J_sv_wall            - Saint-Venant torsional constant for open thin-walled walls\n  J_sv_cell            - Saint-Venant torsional constant for closed thin-walled cells (Bredt–Batho)\n  J_s_vroark           - Refined J (Roark-Young thickness correction)\n  J_s_vroark_fidelity  - Fidelity / reliability indicator\n"
        ),
        params=(
            # REQUIRED: solid torsion alpha used when 'J_sv' is requested
            ParamSpec(
                name="torsion_alpha_sv",
                required=False,
                typ="float",
                default=None,
                description=(
                    "Scaling factor used ONLY for the solid Saint-Venant torsion approximation key 'J_sv'. "
                    "When 'J_sv' is requested, CSF enforces: J_sv = torsion_alpha_sv * (Ix + Iy) "
                    "about the weighted centroid. Modeling choice; not used for 'J_sv_wall' or 'J_sv_cell'."
                ),
                aliases=("torsion_alpha_sv",),
            ),
            # OPTIONAL: display formatting
            ParamSpec(
                name="fmt_display",  # NOTE: keep spelling stable
                required=False,
                typ="str",
                default=".8f",
                description="Python format spec used to render numeric values (e.g. '.4f', '.4e').",
                aliases=("fmt_display",),
            ),
        ),
    )

    def RUN(
        field: Any,
        stations_map: Dict[str, List[float]],
        action: Dict[str, Any],
        *,
        debug_flag: bool = False,
    ) -> None:
        """Execute section_selected_analysis action."""

        params = action.get("params", {}) or {}

        # ---------------------------------------------------------------------
        # PARAMETER: torsion_alpha_sv (CONDITIONALLY REQUIRED)
        # ---------------------------------------------------------------------
        # NOTE:
        # - Only required when the user requests 'J_sv' in properties.
        # - If 'J_sv' is not requested, torsion_alpha_sv is ignored (may be omitted).
        torsion_alpha_sv = None


        # ---------------------------------------------------------------------
        # OPTIONAL parameter: fmt_display
        # ---------------------------------------------------------------------
        fmt = params.get("fmt_display")
        if fmt is None:
            # SPEC.params is a tuple: [torsion_alpha_sv, fmt_display]
            fmt = SPEC.params[1].default

        # Selected property keys
        props: List[str] = list(action.get("properties", []) or [])
        if not props:
            raise RuntimeError("section_selected_analysis: 'properties' must be a non-empty list of keys.")

        # ---------------------------------------------------------------------
        # No Conditional requirement Normalised value
        # ---------------------------------------------------------------------
        torsion_alpha_sv=1


        # Duplicate property keys are allowed; we emit a warning and keep them.
        if len(props) != len(set(props)):
            seen: set[str] = set()
            dups: List[str] = []
            for k in props:
                if k in seen and k not in dups:
                    dups.append(k)
                seen.add(k)
            print(
                "WARNING: section_selected_analysis.properties contains duplicate keys "
                f"{dups}. Duplicates will be preserved in the output order."
            )

        # Expand z values
        z_list = expand_station_names(stations_map, action["stations"])

        rows: List[Dict[str, Any]] = []
        report_blocks: List[str] = []

        def _format_value(v: Any) -> str:
            if v is None:
                return "None"
            if isinstance(v, (int, float, np.integer, np.floating)):
                try:
                    return format(float(v), fmt)
                except Exception:
                    return str(v)
            return str(v)

        for z in z_list:
            sec = field.section(float(z))

            # Compute the full analysis dictionary (single source of truth),
            # then filter (and optionally override J_sv based on torsion_alpha_sv).
            full = section_full_analysis(sec)

            # If the user requests 'J_sv', enforce the explicit alpha policy.
            if "J_sv" in props:
                ix = full.get("Ix")
                iy = full.get("Iy")
                if ix is None or iy is None:
                    raise RuntimeError(
                        "section_selected_analysis: cannot compute 'J_sv' because 'Ix' and/or 'Iy' "
                        "are missing from section_full_analysis output."
                    )
                full["J_sv"] = torsion_alpha_sv * (float(ix) + float(iy))

            buf = io.StringIO()
            with redirect_stdout(buf):
                print(f"\n### SECTION SELECTED ANALYSIS @ z = {float(z)} ###")
                print(f"torsion_alpha_sv     : {_format_value(torsion_alpha_sv)}  [Solid J_sv scaling factor]")
                for k in props:
                    meaning = _ALLOWED_KEYS_MEANING.get(k, "Unknown key (not documented)")
                    print(f"{k:20s}: {_format_value(full.get(k))}  [{meaning}]")

            report_text = buf.getvalue()
            report_blocks.append(report_text)

            # Always carry torsion_alpha_sv in the row for traceability.
            row = {"z": float(z), "torsion_alpha_sv": torsion_alpha_sv}
            for k in props:
                row[k] = full.get(k)
            rows.append(row)

        # ---------------------------------------------------------------------
        # Output routing
        # ---------------------------------------------------------------------
        outputs = action["output"]

        # Support both: output: [stdout] and output: [[...]] (defensive flatten)
        flat_outputs: List[Any] = []
        for outp in outputs:
            if isinstance(outp, list):
                flat_outputs.extend(outp)   
            else:
                flat_outputs.append(outp)

        for outp in flat_outputs:
            if outp == "stdout":
                for blk in report_blocks:
                    print(blk, end="" if blk.endswith("\n") else "\n")
                continue

            p = Path(outp)
            if not p.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {p.parent}")

            if p.suffix.lower() == ".csv":
                fieldnames = ["z", "torsion_alpha_sv"] + props
                with open(p, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=fieldnames)
                    w.writeheader()
                    for r in rows:
                        w.writerow(r)
            else:
                with open(p, "w", encoding="utf-8") as f:
                    for blk in report_blocks:
                        f.write(blk)
                        if not blk.endswith("\n"):
                            f.write("\n")

    # Register in the hub registry (single source of truth).
    register_action(SPEC, RUN)
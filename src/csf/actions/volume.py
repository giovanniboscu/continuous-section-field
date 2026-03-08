"""
actions.volume
--------------

Low-impact extraction of the 'volume' action from CSFActions.py.

Notes
- This module intentionally has NO side-effect registration to avoid circular imports.
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied "as-is" except for minimal adaptations required by dependency injection.
"""

from __future__ import annotations

import csv
import io
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, List

import numpy as np



def register(
    register_action,
    *,
    ActionSpec,
    ParamSpec,
    expand_station_names,
    volume_polygon_list_report_data,
    emit_volume_polygon_list_report,
    polygon_surface_w1_inners0=None,
    csf_weight_catalog_by_pair=None,
    csf_weights_by_pair_at_z=None,
    **_unused,
) -> None:
    """
    Register the 'volume' action.

    Notes
    -----
    - Some injected kwargs are accepted for backward compatibility but unused after consolidation.
    """
    _ = polygon_surface_w1_inners0
    _ = csf_weight_catalog_by_pair
    _ = csf_weights_by_pair_at_z

    SPEC = ActionSpec(
        name="volume",
        summary="Integrate per-polygon occupied volumes between exactly two stations.",
        description=(
            "Builds a per-polygon volume report between two stations [z1, z2].\n"
            "Volumes are computed via section_field.integrate_volume (per polygon).\n"
            "Report metadata are obtained from field inspection at z1 and z2.\n"
            "\n"
            "Note: params.w_tol is accepted but currently unused; it is printed only."
        ),
        params=(
            ParamSpec(
                name="w_tol",
                required=False,
                typ="float",
                default=0.0,
                description="Accepted for forward compatibility but currently unused (printed only).",
            ),
            ParamSpec(
                name="n_points",
                required=False,
                typ="int",
                default=20,
                description="Number of Gauss-Legendre points used by integrate_volume.",
            ),
            ParamSpec(
                name="fmt_display",
                required=False,
                typ="str",
                default="0.6f",
                description="Python format specifier used for numeric fields in the report.",
                aliases=("fmt_diplay",),  # accept legacy misspelling
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
        _ = debug_flag

        params = action.get("params", {}) or {}

        if "w_tol" in params:
            print("WARNING: volume.params.w_tol is currently unused and will be ignored.")

        w_tol = params.get("w_tol", 0.0)
        n_points = params.get("n_points", 20)
        fmt = params.get("fmt_display", params.get("fmt_diplay", "0.6f"))

        z_list = expand_station_names(stations_map, action["stations"])
        if len(z_list) != 2:
            raise ValueError(
                f"volume action requires exactly two z values after expansion (got {len(z_list)}): {z_list}"
            )

        z1 = float(z_list[0])
        z2 = float(z_list[1])

        outputs = action.get("output") or ["stdout"]
        if not isinstance(outputs, list) or not outputs:
            outputs = ["stdout"]

        report = volume_polygon_list_report_data(
            field,
            z1,
            z2,
            int(n_points),
            do_debug_check=False,
        )
        emit_volume_polygon_list_report(
            report,
            outputs=outputs,
            fmt_display=str(fmt),
            w_tol=float(w_tol) if w_tol is not None else 0.0,
        )

    register_action(SPEC, RUN)
"""
actions.section_area_by_weight
-----------------------------

Low-impact extraction of the 'section_area_by_weight' action from CSFActions.py.

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
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def register(
    register_action,
    *,
    ActionSpec,
    ParamSpec,
    expand_station_names,
    polygon_surface_w1_inners0,
) -> None:
    """
    Register the 'section_area_by_weight' action.

    Parameters are injected from the CSFActions hub to avoid importing CSFActions here.
    """

    # Action specification (copied from the hub; keep in sync with CSFActions semantics).
    SPEC = ActionSpec(
        name="section_area_by_weight",
            summary="Report per-polygon net surfaces A_net and homogenized contributions A_net*w grouped by weight at one or more stations.",
            description=(
                "Computes a per-polygon surface report at each station z using the deterministic nesting model.\n"
                "The heavy geometry logic is delegated to polygon_surface_w1_inners0(field, z).\n"
                "\n"
                "For each polygon p at z the function returns:\n"
                "- w(z): effective weight w_eff(p,z)\n"
                "- A_net: exclusive occupied surface with w(p)=1 and w(inners)=0\n"
                "- A_w: A_net * w(z)\n"
                "\n"
                "Presentation\n"
                "- group_mode='weight': rows are visually grouped by weight (weight printed once per group).\n"
                "- group_mode='id'    : rows are printed in ascending polygon id; id is the first column.\n"
                "\n"
                "Weight binning (optional)\n"
                "- If w_tol > 0, weights are binned as w_bin = round(w / w_tol) * w_tol.\n"
                "- If w_tol <= 0, grouping uses the raw weight values.\n"
                "\n"
                "YAML fields\n"
                "- stations: REQUIRED. One or more station-set names defined under CSF_ACTIONS.stations (absolute z).\n"
                "- output:   OPTIONAL. Default is [stdout]. Supports stdout + file outputs.\n"
                "            - *.csv: one row per polygon (z, id, w, s0_name, s1_name, A_net, A_w, ...).\n"
                "            - other: captured text report.\n"
                "\n"
                "Params\n"
                "- group_mode          : grouping/ordering mode for the printed report.\n"
                "- w_tol               : optional weight binning tolerance (bin width).\n"
                "- include_per_polygon : include diagnostic columns (inners, container).\n"
                "- fmt_display         : python format spec for numeric values in stdout/text reports.\n"
                "\n"
                "Modeling note (scope)\n"
                "- This is purely a sectional (transverse) diagnostic for slender-beam workflows."
            ),
            params=(
                ParamSpec(
                    name="group_mode",
                    typ="str",
                    required=False,
                    default="weight",
                    description="Report layout: 'weight' (group rows by weight; print weight once per group) or 'id' (flat table sorted by polygon id).",
                ),
                ParamSpec(
                    name="w_tol",
                    typ="float",
                    required=False,
                    default=0.0,
                    description="Optional weight binning tolerance (bin width). If > 0, weights are binned by rounding to multiples of w_tol.",
                ),
                ParamSpec(
                    name="include_per_polygon",
                    typ="bool",
                    required=False,
                    default=False,
                    description="If True, include per-polygon diagnostic columns (direct inners, container).",
                ),
                ParamSpec(
                    name="fmt_display",
                    typ="str",
                    required=False,
                    default=".6f",
                    description="Python format spec used for numeric values in the stdout/text report (e.g. '.6f', '.4e').",
                    aliases=("fmt_diplay", "fmt_display"),
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
        """
        Execute section_area_by_weight action.

        This action prints (and optionally exports) a per-polygon surface report at each station z.

        Geometry core:
          - polygon_surface_w1_inners0(field, z) -> per-polygon records with:
              idx (0-based), name, container_name, direct_inners, w (w_eff), A (A_net), A_w

        Runner responsibilities:
          - expand stations to z values
          - enrich rows with endpoint references (s0.name, s1.name) from field.inspect_section_entities(z)
          - apply optional weight binning (w_tol)
          - present rows according to group_mode ("weight" or "id")
          - route outputs (stdout / csv / text) with the standard CSFActions rules
        """
        # NOTE: debug_flag is a runner-wide flag; the geometry helper currently does not expose a debug hook.
        _ = debug_flag  # keep the signature stable without changing behavior.
        if not callable(polygon_surface_w1_inners0):
            raise RuntimeError(
                "polygon_surface_w1_inners0(field, z) is not available. "
                "Ensure it is defined/exported in csf.section_field and imported by CSFActions."
            )

        if not hasattr(field, "inspect_section_entities"):
            raise RuntimeError(
                "Field object does not implement inspect_section_entities(z). "
                "This action needs it to map each polygon to (s0.name, s1.name)."
            )

        params = action.get("params", {}) or {}
        spec = SPEC

        def _default(pname: str) -> Any:
            for ps in spec.params:
                if ps.name == pname:
                    return ps.default
            raise KeyError(pname)

        group_mode = params.get("group_mode", _default("group_mode"))
        if group_mode not in ("weight", "id"):
            raise ValueError(f"section_area_by_weight: invalid group_mode={group_mode!r}. Expected 'weight' or 'id'.")

        w_tol = params.get("w_tol", _default("w_tol"))
        include_per_polygon = params.get("include_per_polygon", _default("include_per_polygon"))

        fmt = params.get("fmt_display")
        if fmt is None:
            # Accept common misspelling alias (already normalized during validation when possible)
            fmt = params.get("fmt_diplay")
        if fmt is None:
            fmt = _default("fmt_display")

        z_list = expand_station_names(stations_map, action["stations"])

        # Output routing standard:
        # - if output is not specified, default is ["stdout"]
        outputs = action.get("output") or ["stdout"]
        if not isinstance(outputs, list) or not outputs:
            outputs = ["stdout"]

        want_stdout = ("stdout" in outputs)
        want_text_file = any((isinstance(o, str) and o != "stdout" and Path(o).suffix.lower() != ".csv") for o in outputs)
        want_csv_file = any((isinstance(o, str) and o != "stdout" and Path(o).suffix.lower() == ".csv") for o in outputs)

        report_blocks: List[str] = []
        csv_rows: List[Dict[str, Any]] = []

        def _fmt(v: Any) -> str:
            if v is None:
                return "None"
            if isinstance(v, (int, float, np.integer, np.floating)):
                try:
                    return format(float(v), fmt)
                except Exception:
                    return str(v)
            return str(v)

        def _wbin(w: float) -> float:
            # Standard binning: if w_tol > 0, snap to nearest multiple of w_tol.
            try:
                wt = float(w_tol)
            except Exception:
                wt = 0.0
            if wt > 0.0:
                return round(float(w) / wt) * wt
            return float(w)

        for z in z_list:
            zf = float(z)

            rows = polygon_surface_w1_inners0(field, zf)
            if not isinstance(rows, list):
                raise TypeError("polygon_surface_w1_inners0(field, z) must return a list of dict records.")

            # Map polygon name -> (s0_name, s1_name) using the section inspection API.
            entities = field.inspect_section_entities(zf)
            if not isinstance(entities, list):
                raise TypeError("inspect_section_entities(z) must return a list of dict records.")

            name_to_pair: Dict[str, Tuple[str, str]] = {}
            for e in entities:
                if not isinstance(e, dict):
                    raise TypeError("inspect_section_entities(z) must return a list of dict records.")
                nm = e.get("name")
                if not isinstance(nm, str) or not nm:
                    raise ValueError("inspect_section_entities(z) returned an entity with missing/invalid 'name'.")
                if nm in name_to_pair:
                    raise ValueError(f"Duplicate entity name from inspect_section_entities at z={zf}: '{nm}'.")
                s0 = e.get("s0_name")
                s1 = e.get("s1_name")
                if not isinstance(s0, str) or not s0 or not isinstance(s1, str) or not s1:
                    raise ValueError(f"Entity '{nm}' missing/invalid s0_name/s1_name at z={zf}.")
                name_to_pair[nm] = (s0, s1)

            # Enrich and validate rows.
            for r in rows:
                if not isinstance(r, dict):
                    raise TypeError("polygon_surface_w1_inners0(field, z) must return a list of dict records.")
                if "idx" not in r or "name" not in r:
                    raise ValueError("polygon_surface_w1_inners0 records must include 'idx' and 'name'.")
                nm = r["name"]
                if nm not in name_to_pair:
                    raise ValueError(
                        f"Polygon '{nm}' present in polygon_surface_w1_inners0 but missing from inspect_section_entities at z={zf}."
                    )
                s0, s1 = name_to_pair[nm]
                r["_s0_name"] = s0
                r["_s1_name"] = s1
                r["_w_bin"] = _wbin(float(r.get("w", 0.0)))

            # Sort/present.
            if group_mode == "id":
                rows_sorted = sorted(rows, key=lambda rr: int(rr["idx"]))
            else:
                # group_mode == "weight": stable ordering by (binned weight, id)
                rows_sorted = sorted(rows, key=lambda rr: (float(rr["_w_bin"]), int(rr["idx"])))

            # Totals (always over all polygons, independent of presentation).
            tot_A = 0.0
            tot_Aw = 0.0
            for r in rows_sorted:
                tot_A += float(r.get("A", 0.0))
                tot_Aw += float(r.get("A_w", 0.0))

            # Build report block if needed (stdout or text file).
            if want_stdout or want_text_file:
                max_idx = max((int(r["idx"]) for r in rows_sorted), default=0)
                id_width = max(2, len(str(max_idx)))

                buf = io.StringIO()
                with redirect_stdout(buf):
                    print(f"SECTION AREA LIST REPORT at z = {_fmt(zf)}")
                    print("=" * 80)
                    print(f"group_mode={group_mode}  w_tol={_fmt(float(w_tol) if w_tol is not None else 0.0)}")
                    print("")
                    # Header depends on the chosen layout mode.
                    if group_mode == "id":
                        if include_per_polygon:
                            print(
                                f"{'id':<6s} | {'W':>10s} | {'s0.name':<18s} | {'s1.name':<18s} | {'A_net':>12s} | {'A*w':>12s} | {'inners pols':<22s} | Container"
                            )
                        else:
                            print(
                                f"{'id':<6s} | {'W':>10s} | {'s0.name':<18s} | {'s1.name':<18s} | {'A_net':>12s} | {'A*w':>12s}"
                            )
                    else:
                        if include_per_polygon:
                            print(
                                f"{'W':>10s} | {'id':<6s} | {'s0.name':<18s} | {'s1.name':<18s} | {'A_net':>12s} | {'A*w':>12s} | {'inners pols':<22s} | Container"
                            )
                        else:
                            print(
                                f"{'W':>10s} | {'id':<6s} | {'s0.name':<18s} | {'s1.name':<18s} | {'A_net':>12s} | {'A*w':>12s}"
                            )
                    print("-" * 80)

                    last_w: Optional[float] = None
                    for r in rows_sorted:
                        idx = int(r["idx"])
                        id_str = f"[{idx:0{id_width}d}]"
                        s0 = str(r.get("_s0_name", ""))
                        s1 = str(r.get("_s1_name", ""))
                        w_show = float(r.get("_w_bin", float(r.get("w", 0.0))))
                        w_str = _fmt(w_show)

                        if group_mode == "weight":
                            # Print weight once per group; blank for subsequent rows in the same group.
                            if last_w is not None and abs(w_show - last_w) == 0.0:
                                w_cell = " " * len(w_str)
                            else:
                                w_cell = w_str
                                last_w = w_show

                            if include_per_polygon:
                                inn = r.get("direct_inners") or []
                                cont = r.get("container_name") or "[ROOT]"
                                print(
                                    f"{w_cell:>10s} | {id_str:<6s} | {s0:<18s} | {s1:<18s} | {_fmt(r.get('A')):>12s} | {_fmt(r.get('A_w')):>12s} | {str(inn):<22s} | {cont}"
                                )
                            else:
                                print(
                                    f"{w_cell:>10s} | {id_str:<6s} | {s0:<18s} | {s1:<18s} | {_fmt(r.get('A')):>12s} | {_fmt(r.get('A_w')):>12s}"
                                )
                        else:
                            # group_mode == "id": flat table, weight always shown, id is first column.
                            if include_per_polygon:
                                inn = r.get("direct_inners") or []
                                cont = r.get("container_name") or "[ROOT]"
                                print(
                                    f"{id_str:<6s} | {w_str:>10s} | {s0:<18s} | {s1:<18s} | {_fmt(r.get('A')):>12s} | {_fmt(r.get('A_w')):>12s} | {str(inn):<22s} | {cont}"
                                )
                            else:
                                print(
                                    f"{id_str:<6s} | {w_str:>10s} | {s0:<18s} | {s1:<18s} | {_fmt(r.get('A')):>12s} | {_fmt(r.get('A_w')):>12s}"
                                )

                    print("-" * 80)
                    print(f"Occupied Total Surface: {_fmt(tot_A)}")
                    print(f"Homogenized area:        {_fmt(tot_Aw)}")
                    print("")

                report_blocks.append(buf.getvalue())

            # Prepare CSV rows (one row per polygon; ordering follows group_mode).
            if want_csv_file:
                for r in rows_sorted:
                    idx = int(r["idx"])
                    w_show = float(r.get("_w_bin", float(r.get("w", 0.0))))
                    base = {
                        "z": zf,
                        "id": idx,
                        "w": w_show,
                        "s0_name": str(r.get("_s0_name", "")),
                        "s1_name": str(r.get("_s1_name", "")),
                        "A_net": float(r.get("A", 0.0)),
                        "A_w": float(r.get("A_w", 0.0)),
                    }
                    if include_per_polygon:
                        inn = r.get("direct_inners") or []
                        base["direct_inners"] = ";".join(str(x) for x in inn)
                        base["container_name"] = str(r.get("container_name") or "")
                    csv_rows.append(base)

        # Emit outputs according to standard routing rules.
        for outp in outputs:
            if outp == "stdout":
                for blk in report_blocks:
                    print(blk, end="" if blk.endswith("\n") else "\n")
                continue

            p = Path(outp)
            if not p.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {p.parent}")

            if p.suffix.lower() == ".csv":
                if include_per_polygon:
                    fieldnames = ["z", "id", "w", "s0_name", "s1_name", "A_net", "A_w", "direct_inners", "container_name"]
                else:
                    fieldnames = ["z", "id", "w", "s0_name", "s1_name", "A_net", "A_w"]
                with open(p, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=fieldnames)
                    w.writeheader()
                    for row in csv_rows:
                        w.writerow(row)
            else:
                with open(p, "w", encoding="utf-8") as f:
                    for blk in report_blocks:
                        f.write(blk)
                        if not blk.endswith("\n"):
                            f.write("\n")





    register_action(SPEC, RUN)

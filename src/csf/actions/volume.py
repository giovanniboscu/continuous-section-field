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
    polygon_surface_w1_inners0,
    csf_weight_catalog_by_pair,
    csf_weights_by_pair_at_z,
) -> None:
    """
    Register the 'volume' action.

    Parameters are injected from the CSFActions hub to avoid importing CSFActions here.
    """

    # Action specification (copied from the hub; keep in sync with CSFActions semantics).
    SPEC = ActionSpec(
        name="volume",
        summary="Integrate per-polygon occupied volumes between exactly two stations (accounting-style material quantities).",
        description=(
            "Integrates two 'volume-like' quantities for each polygon between two stations [z1, z2].\n"
            "\n"
            "Core geometry at each z is provided by polygon_surface_w1_inners0(field, z), which returns per-polygon:\n"
            "- A_net : occupied surface with the local rule w(p)=1 and w(direct inners)=0\n"
            "- A_w   : A_net * w_eff(p,z)\n"
            "\n"
            "This action integrates along z using Gauss–Legendre quadrature (n_points):\n"
            "- Volume Occupied              : V_occ = ∫ A_net(z) dz\n"
            "- Homogenized Volume Occupied  : V_hom = ∫ A_w(z) dz\n"
            "\n"
            "Report columns (0-based ids)\n"
            "- id           : polygon index (0-based, consistent with polygon_surface_w1_inners0)\n"
            "- s0.name      : polygon name in endpoint section S0 (by index)\n"
            "- s1.name      : polygon name in endpoint section S1 (by index)\n"
            "- s0.w         : weight value at the first station z1 (w(z1))\n"
            "- s1.w         : weight value at the second station z2 (w(z2))\n"
            "- weight_law   : custom weight law expression if present; otherwise 'none'\n"
            "\n"
            "Stations\n"
            "- stations: REQUIRED and MUST expand to exactly two z values (e.g., station_edge: [z1, z2]).\n"
            "\n"
            "Output\n"
            "- If output is omitted, default is [stdout].\n"
            "- stdout: prints the report.\n"
            "- *.csv : writes a single table (one row per polygon).\n"
            "- other : writes the captured text report.\n"
            "\n"
            "Notes\n"
            "- This is intended for quantity take-off / material bookkeeping, not for structural mechanics.\n"
            "- params.w_tol is accepted but currently unused; it is ignored and may emit a warning."
        ),
        params=(
            ParamSpec(
                name="w_tol",
                typ="float",
                required=False,
                default=0.0,
                description="Accepted for forward compatibility but currently unused (ignored at runtime).",
            ),
            ParamSpec(
                name="n_points",
                typ="int",
                required=False,
                default=20,
                description="Number of Gauss–Legendre quadrature points used to integrate along z (>= 1).",
            ),
            ParamSpec(
                name="fmt_display",
                typ="str",
                required=False,
                default=".6g",
                description="Python numeric format for stdout/text report values (e.g. '.6g', '.4f', '.3e').",
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
        Execute volume action.

        This action integrates, for each polygon, two longitudinal quantities over the interval [z1, z2]:

          - Volume Occupied:
                V_occ = ∫ A_net(z) dz

          - Homogenized Volume Occupied:
                V_hom = ∫ (A_net(z) * w_eff(p,z)) dz

        where (A_net, A_net*w_eff) are obtained from:
            polygon_surface_w1_inners0(field, z)

        Notes
        -----
        - Polygon ids are 0-based (consistent with polygon_surface_w1_inners0).
        - The report is intended for quantity take-off / bookkeeping, not for structural mechanics.
        """
        # NOTE: debug_flag is a runner-wide flag; this action does not currently expose internal debug hooks.
        _ = debug_flag  # keep the signature stable without changing behavior.

        if not callable(polygon_surface_w1_inners0):
            raise RuntimeError(
                "polygon_surface_w1_inners0(field, z) is not available. "
                "Ensure it is defined/exported in csf.section_field and imported by CSFActions."
            )

        if (not callable(csf_weight_catalog_by_pair)) or (not callable(csf_weights_by_pair_at_z)):
            raise RuntimeError(
                "csf_weight_catalog_by_pair(...) and csf_weights_by_pair_at_z(...) must be available in CSFActions."
            )

        if not hasattr(field, "s0") or not hasattr(field, "s1"):
            raise RuntimeError("Field object must expose endpoint sections .s0 and .s1.")

        params = action.get("params", {}) or {}
        spec = SPEC

        def _default(pname: str) -> Any:
            for ps in spec.params:
                if ps.name == pname:
                    return ps.default
            raise KeyError(pname)

        # Params
        w_tol = params.get("w_tol", _default("w_tol"))
        n_points = params.get("n_points", _default("n_points"))

        fmt = params.get("fmt_display")
        if fmt is None:
            # Accept common misspelling alias (already normalized during validation when possible)
            fmt = params.get("fmt_diplay")
        if fmt is None:
            fmt = _default("fmt_display")

        # w_tol is currently unused for this action (kept for forward compatibility).
        if "w_tol" in params:
            print("WARNING: volume.params.w_tol is currently unused and will be ignored.")

        if not isinstance(n_points, int):
            # Permit YAML floats that are integer-like (defensive)
            try:
                n_points = int(n_points)
            except Exception as e:
                raise TypeError(f"volume.params.n_points must be an int >= 1 (got {type(n_points).__name__}).") from e
        if n_points < 1:
            raise ValueError("volume.params.n_points must be >= 1.")

        # Stations: REQUIRED and must expand to exactly two absolute z values.
        z_list = expand_station_names(stations_map, action["stations"])
        if len(z_list) != 2:
            raise ValueError(
                f"volume action requires exactly two z values after expansion (got {len(z_list)}): {z_list}"
            )

        z1 = float(z_list[0])
        z2 = float(z_list[1])

        # Integration scaffold uses a positive measure.
        z_int0 = min(z1, z2)
        z_int1 = max(z1, z2)
        L = float(z_int1 - z_int0)

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

        # Endpoint references (by index, CSF homology assumption).
        p0_list = list(field.s0.polygons)
        p1_list = list(field.s1.polygons)
        if len(p0_list) != len(p1_list):
            raise ValueError(f"Endpoint polygon count mismatch: len(S0)={len(p0_list)} vs len(S1)={len(p1_list)}")

        pairs: List[PolyPair] = []
        for i, (p0, p1) in enumerate(zip(p0_list, p1_list)):
            name0 = str(getattr(p0, "name", f"poly_{i+1}"))
            name1 = str(getattr(p1, "name", f"poly_{i+1}"))
            pairs.append((name0, name1))

        # Weight information shown in the report:
        # - s0.w means w(z1) (first station)
        # - s1.w means w(z2) (second station)
        w_at_z1 = csf_weights_by_pair_at_z(field, z1)
        w_at_z2 = csf_weights_by_pair_at_z(field, z2)

        # Law label is informational only (not evaluated here).
        # We show the CUSTOM law expression if present; otherwise "none".
        catalog = csf_weight_catalog_by_pair(field, include_default_linear=False)

        # Degenerate case: zero-length interval -> zero volumes.
        V_occ = [0.0 for _ in pairs]
        V_hom = [0.0 for _ in pairs]

        if L != 0.0:
            z_mid = 0.5 * (z_int0 + z_int1)
            half_L = 0.5 * L

            xi, wi = np.polynomial.legendre.leggauss(int(n_points))

            # Integrate all polygons in one pass: O(n_points * n_polygons)
            for x, wq in zip(xi, wi):
                z = z_mid + half_L * float(x)

                rows = polygon_surface_w1_inners0(field, float(z))
                if not isinstance(rows, list):
                    raise TypeError("polygon_surface_w1_inners0(field, z) must return a list of dict records.")

                # Accumulate by idx (0-based).
                for r in rows:
                    if not isinstance(r, dict):
                        raise TypeError("polygon_surface_w1_inners0(field, z) must return a list of dict records.")
                    if "idx" not in r:
                        raise ValueError("polygon_surface_w1_inners0 records must include 'idx'.")
                    idx0 = int(r["idx"])
                    if idx0 < 0 or idx0 >= len(pairs):
                        raise ValueError(f"polygon_surface_w1_inners0 returned out-of-range idx={idx0} at z={z}.")
                    V_occ[idx0] += float(r.get("A", 0.0)) * float(wq) * half_L
                    V_hom[idx0] += float(r.get("A_w", 0.0)) * float(wq) * half_L

        # Build report block if needed (stdout or text file).
        if want_stdout or want_text_file:
            max_idx = max(range(len(pairs)), default=0)
            id_width = max(2, len(str(max_idx)))

            buf = io.StringIO()
            with redirect_stdout(buf):
                print(f"VOLUME POLYGON LIST REPORT at z={_fmt(z1)} and z={_fmt(z2)}")
                print("=" * 96)
                print(f"n_points={int(n_points)}  w_tol={_fmt(float(w_tol) if w_tol is not None else 0.0)}")
                print("")
                print(
                    f"{'id':<6s} | {'s0.w':>12s} | {'s1.w':>12s} | {'weight_law':<18s} | "
                    f"{'s0.name':<18s} | {'s1.name':<18s} | {'Volume Occupied':>18s} | {'Homogenized Volume':>20s}"
                )
                print("-" * 96)

                tot_occ = 0.0
                tot_hom = 0.0

                for i, (name0, name1) in enumerate(pairs):
                    id_str = f"[{i:0{id_width}d}]"

                    w1 = float(w_at_z1.get((name0, name1), float("nan")))
                    w2 = float(w_at_z2.get((name0, name1), float("nan")))

                    law = None
                    meta = catalog.get((name0, name1))
                    if isinstance(meta, dict):
                        law = meta.get("law")
                    law_str = "none" if law is None else str(law)

                    v_occ = float(V_occ[i])
                    v_hom = float(V_hom[i])

                    tot_occ += v_occ
                    tot_hom += v_hom

                    print(
                        f"{id_str:<6s} | {_fmt(w1):>12s} | {_fmt(w2):>12s} | {law_str:<18s} | "
                        f"{name0:<18s} | {name1:<18s} | {_fmt(v_occ):>18s} | {_fmt(v_hom):>20s}"
                    )

                    # Prepare CSV row (one per polygon)
                    if want_csv_file:
                        csv_rows.append(
                            {
                                "z1": float(z1),
                                "z2": float(z2),
                                "id": int(i),
                                "s0_w": w1,
                                "s1_w": w2,
                                "weight_law": law_str,
                                "s0_name": name0,
                                "s1_name": name1,
                                "volume_occupied": v_occ,
                                "homogenized_volume_occupied": v_hom,
                                "n_points": int(n_points),
                            }
                        )

                print("-" * 96)
                print(f"Total Occupied Volume:           {_fmt(tot_occ)}")
                print(f"Total Occupied Homogenized Volume: {_fmt(tot_hom)}")
                print("")

            report_blocks.append(buf.getvalue())

        # If we need CSV but we didn't build rows inside the report path (e.g., file-only CSV),
        # generate csv_rows now from the computed arrays.
        if want_csv_file and not csv_rows:
            for i, (name0, name1) in enumerate(pairs):
                w1 = float(w_at_z1.get((name0, name1), float("nan")))
                w2 = float(w_at_z2.get((name0, name1), float("nan")))
                meta = catalog.get((name0, name1))
                law = (meta.get("law") if isinstance(meta, dict) else None)
                law_str = "none" if law is None else str(law)
                csv_rows.append(
                    {
                        "z1": float(z1),
                        "z2": float(z2),
                        "id": int(i),
                        "s0_w": w1,
                        "s1_w": w2,
                        "weight_law": law_str,
                        "s0_name": name0,
                        "s1_name": name1,
                        "volume_occupied": float(V_occ[i]),
                        "homogenized_volume_occupied": float(V_hom[i]),
                        "n_points": int(n_points),
                    }
                )

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
                fieldnames = [
                    "z1",
                    "z2",
                    "id",
                    "s0_w",
                    "s1_w",
                    "weight_law",
                    "s0_name",
                    "s1_name",
                    "volume_occupied",
                    "homogenized_volume_occupied",
                    "n_points",
                ]
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

    # Explicit registration (no side effects at import time).
    register_action(SPEC, RUN)

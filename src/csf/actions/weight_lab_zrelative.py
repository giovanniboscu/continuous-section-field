"""
CSF Action Module: weight_lab_zrelative
======================================

Text-only inspector action for verifying custom weight-law expressions at user-provided
*relative* z stations.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- Explicit registration via register(register_action, ...).
- Keep logic as-is from the monolithic CSFActions implementation.
- No matplotlib usage (does not affect deferred-show logic).
- All comments are in English (per project convention).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from contextlib import redirect_stdout, nullcontext
from typing import Any, Dict, List


# -----------------------------------------------------------------------------
# Action SPEC (help/validation)
# -----------------------------------------------------------------------------
def _build_spec(ActionSpec: Any, ParamSpec: Any) -> Any:
    _ = ParamSpec  # unused: this action has no params; kept for signature consistency
    return ActionSpec(
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
    )


# -----------------------------------------------------------------------------
# Runner (logic copied from the monolithic implementation; minimal adaptations)
# -----------------------------------------------------------------------------
def _run(
    field: Any,
    stations_map: Dict[str, List[float]],
    action: Dict[str, Any],
    *,
    debug_flag: bool = False,
    expand_station_names: Any,
    safe_evaluate_weight_zrelative: Any,
) -> None:
    """Action: weight_lab_zrelative

    This action is *text-only*. It is meant as a "lab/inspector" to help users
    verify that a weight law formula W(z) behaves as expected.

    Why this exists
    ---------------
    In CSF, polygon weights can be controlled by user-defined laws. A "law" is
    an expression that uses:
      - w0, w1 : endpoint weights (from p0.weight, p1.weight)
      - z      : relative coordinate along the element
      - L      : total element length
      - np     : numpy (np.sin, np.cos, np.pi, ...)

    The actual evaluation is delegated to:
        safe_evaluate_weight_zrelative(formula, p0, p1, l_total=L, z0, z1, z=z, print=True)

    YAML contract (normalized by validator)
    --------------------------------------
    - stations: REQUIRED (station values are interpreted as *relative* z)
    - weith_law: REQUIRED list[str] of expressions (outside params)
    - output: optional, default ['stdout'] if the YAML key is missing

    Output semantics
    ----------------
    - stdout in output => print the inspector output to the terminal
    - file paths in output => write the same inspector text to those files
    - if output does NOT include stdout => file-only (no terminal output)

    NOTE
    ----
    This action produces NO matplotlib figures and does not affect the deferred
    plotting mechanism.
    """
    _ = debug_flag  # kept for signature compatibility; intentionally unused

    if safe_evaluate_weight_zrelative is None:
        raise RuntimeError("safe_evaluate_weight_zrelative is not available (import failed).")

    # 1) Inputs
    laws = action.get("weith_law")
    if not isinstance(laws, list) or len(laws) == 0:
        # Should never happen after validation, but keep a clear runtime error.
        raise RuntimeError("weight_lab_zrelative requires a non-empty 'weith_law' list.")

    # Stations here are interpreted as *relative* coordinates.
    z_list = expand_station_names(stations_map, action["stations"])

    # Total length L is derived from the CSF endpoints.
    try:
        L_total = float(field.s1.z) - float(field.s0.z)
    except Exception as e:
        raise RuntimeError(f"weight_lab_zrelative: cannot compute L = field.s1.z - field.s0.z: {e}")

    if L_total == 0.0:
        raise RuntimeError("weight_lab_zrelative: L is zero (field endpoints have the same z).")

    # Polygon pairing is assumed to be by index (homology assumption used throughout the project).
    try:
        polys0 = list(field.s0.polygons)
        polys1 = list(field.s1.polygons)
    except Exception as e:
        raise RuntimeError(f"weight_lab_zrelative: cannot access endpoint polygons: {e}")

    if len(polys0) != len(polys1):
        raise RuntimeError(
            f"weight_lab_zrelative: polygon count mismatch: len(S0)={len(polys0)} vs len(S1)={len(polys1)}"
        )

    # 2) Output routing
    outputs = action.get("output")
    if outputs is None:
        # Normally the validator normalizes 'output' to a list, but keep a safe fallback.
        outputs = ["stdout"]

    do_stdout = ("stdout" in outputs)
    file_outputs = [o for o in outputs if o != "stdout"]

    # If we need to write to file(s), we must capture all printed output.
    # The safe evaluator prints a multi-line report, so we redirect stdout accordingly.
    buf = io.StringIO() if file_outputs else None

    class _Tee:
        """Minimal tee stream.

        Used only when the user requests BOTH stdout and file output.
        It forwards every write() to multiple underlying streams.
        """

        def __init__(self, *streams: Any):
            self._streams = streams

        def write(self, s: str) -> int:
            for st in self._streams:
                st.write(s)
            return len(s)

        def flush(self) -> None:
            for st in self._streams:
                if hasattr(st, "flush"):
                    st.flush()

    if file_outputs and do_stdout:
        ctx = redirect_stdout(_Tee(sys.stdout, buf))  # type: ignore[arg-type]
    elif file_outputs and (not do_stdout):
        ctx = redirect_stdout(buf)  # type: ignore[arg-type]
    else:
        ctx = nullcontext()

    # 3) Run inspector
    with ctx:
        print("\n" + "=" * 78)
        print("CSF WEIGHT LAW INSPECTOR (relative z)  |  weight_lab_zrelative")
        print("=" * 78)
        print(f"L_total = {L_total:.6f}  (computed as field.s1.z - field.s0.z)")
        print(
            "Stations are interpreted as RELATIVE coordinates. "
            "It is the user's responsibility to provide z in [0, L]."
        )
        print("-" * 78)

        for li, expr in enumerate(laws, start=1):
            print(f"\n--- LAW {li}/{len(laws)} ---")
            print(f"EXPR: {expr}")

            for z in z_list:
                zf = float(z)
                if zf < 0.0 or zf > L_total:
                    print(f"[WARN] z={zf} is outside [0, L]={L_total}. (relative stations are user-defined)")

                for pi, (p0, p1) in enumerate(zip(polys0, polys1), start=1):
                    n0 = getattr(p0, "name", f"poly_{pi}")
                    n1 = getattr(p1, "name", f"poly_{pi}")
                    print(f"\n[PAIR {pi}] {n0} -> {n1} | z={zf:.6f} / L={L_total:.6f}")

                    # The evaluator is responsible for safe parsing and printing its own report.
                    z0 = field.s0.z
                    z1 = field.s1.z
                    safe_evaluate_weight_zrelative(formula=expr, p0=p0, p1=p1, z0=z0, z1=z1, z=zf, print=True)

    # 4) Write captured output to files (if any)
    if file_outputs and buf is not None:
        out_text = buf.getvalue()
        for out_path in file_outputs:
            p = Path(out_path)
            if not p.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {p.parent}")
            with open(p, "w", encoding="utf-8") as f:
                f.write(out_text)

        # Print a short status only when stdout is enabled.
        if do_stdout:
            for out_path in file_outputs:
                print(f"[OK] weight_lab_zrelative wrote: {out_path}")


# -----------------------------------------------------------------------------
# Explicit registration hook (no side effects)
# -----------------------------------------------------------------------------
def register(
    register_action: Any,
    *,
    ActionSpec: Any,
    ParamSpec: Any,
    expand_station_names: Any,
    safe_evaluate_weight_zrelative: Any,
) -> None:
    """Register this action into the shared CSFActions registry.

    All dependencies are injected explicitly from CSFActions.py to avoid import cycles.
    """
    SPEC = _build_spec(ActionSpec, ParamSpec)

    def RUN(field: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool = False) -> None:
        _run(
            field,
            stations_map,
            action,
            debug_flag=debug_flag,
            expand_station_names=expand_station_names,
            safe_evaluate_weight_zrelative=safe_evaluate_weight_zrelative,
        )

    register_action(SPEC, RUN)

"""
CSF Action Module: write_opensees_geometry
=========================================

This module contains the logic for the `write_opensees_geometry` action.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- Explicit registration via register(register_action, ...).
- Keep the action runner logic identical to the monolithic CSFActions implementation.
- This is a file-only exporter: it writes exactly one Tcl file (no stdout output).

Important
---------
- This action forbids the YAML field `stations:`. Stations are generated internally
  by the exporter from `n_points`.
"""

from __future__ import annotations

from typing import Any, Dict, List


# -----------------------------------------------------------------------------
# Action SPEC (help/validation)
# -----------------------------------------------------------------------------
def _build_spec(ActionSpec: Any, ParamSpec: Any) -> Any:
    """Build ActionSpec for write_opensees_geometry.

    NOTE: This mirrors the baseline CSFActions catalog entry to keep help/validation coherent.
    """
    return ActionSpec(
        name="write_opensees_geometry",
        summary="Export an OpenSees Tcl geometry file (sections + stations) for forceBeamColumn workflows.",
        description=(
            "Writes a Tcl file that can be consumed by OpenSees/OpenSeesPy beam models built from a station list.\n"
            "\n"
            "YAML fields\n"
            "- stations: NOT USED (forbidden). Stations are generated internally from params.\n"
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
    )


# -----------------------------------------------------------------------------
# Runner (copied from the monolithic implementation; minimal adaptations)
# -----------------------------------------------------------------------------
def _run(
    field: Any,
    stations_map: Dict[str, List[float]],
    action: Dict[str, Any],
    *,
    debug_flag: bool = False,
    write_opensees_geometry: Any,
) -> None:
    """Action: write_opensees_geometry

    Export an OpenSees Tcl geometry file (sections + station list) by calling the
    injected helper `write_opensees_geometry(...)`.

    YAML shape (validated before execution):
      - write_opensees_geometry:
          output: [out/geometry.tcl]   # required, file-only (no stdout)
          params:
            n_points: 10              # required int
            E_ref: 2.1e11             # required float
            nu: 0.30                  # required float

    Notes
    -----
    - This action does NOT use stations; 'stations:' must not be provided.
    - This action is FILE-ONLY by design: it writes exactly one Tcl file.
    - E_ref and nu are required here even if the underlying function defines defaults.
      This keeps the YAML plan explicit about the elastic reference assumptions.
    """
    _ = debug_flag  # kept for signature compatibility; intentionally unused
    _ = stations_map  # forbidden by validation; kept for signature compatibility

    if write_opensees_geometry is None:
        raise RuntimeError("write_opensees_geometry helper is not available (import failed).")

    params = action.get("params", {}) or {}
    n_points = params.get("n_points")
    E_ref = params.get("E_ref")
    nu = params.get("nu")

    output_list = action.get("output", [])
    out_files = [o for o in output_list if isinstance(o, str) and o != "stdout"]
    if len(out_files) != 1:
        # Defensive check (should not happen if validation passed).
        raise ValueError(f"write_opensees_geometry requires exactly one output Tcl path, got: {output_list}")
    tcl_path = out_files[0]

    # Delegate export to the helper function.
    # The writer is responsible for generating the correct Tcl content.
    write_opensees_geometry(
        field,
        n_points=int(n_points),
        E_ref=float(E_ref),
        nu=float(nu),
        filename=tcl_path,
    )


# -----------------------------------------------------------------------------
# Explicit registration hook (no side effects)
# -----------------------------------------------------------------------------
def register(
    register_action: Any,
    *,
    ActionSpec: Any,
    ParamSpec: Any,
    write_opensees_geometry: Any,
) -> None:
    """Register this action into the shared CSFActions registry.

    All dependencies are injected explicitly from CSFActions.py to avoid import cycles.
    """
    SPEC = _build_spec(ActionSpec, ParamSpec)

    def RUN(field: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool = False) -> None:
        _run(field, stations_map, action, debug_flag=debug_flag, write_opensees_geometry=write_opensees_geometry)

    register_action(SPEC, RUN)

"""
CSF Action Module: plot_properties
=================================

This module contains the logic for the `plot_properties` action.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- The module exposes:
    - SPEC: ActionSpec
    - RUN:  action runner (pure action logic)
    - register(register_action, ...): explicit registration hook
- The runner does NOT call plt.show(). It only creates/labels figures.
  Final GUI display is handled centrally by CSFActions' deferred-show logic.

Notes
-----
- This action does NOT use `stations:`. It samples internally between CSF endpoints.
- `properties:` must be validated/normalized by the manager before RUN is called.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


# -----------------------------------------------------------------------------
# Action SPEC (help/validation)
# -----------------------------------------------------------------------------
# IMPORTANT:
# - Keep this aligned with the baseline CSFActions-fixed.py definition.
# - This is intentionally duplicated here so the action module is self-contained.
def _build_spec(ActionSpec: Any, ParamSpec: Any) -> Any:
    return ActionSpec(
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
    )


# -----------------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------------
def _run(
    field: Any,
    stations_map: Dict[str, List[float]],
    action: Dict[str, Any],
    *,
    debug_flag: bool = False,
    SPEC: Any,
    Visualizer: Any,
) -> None:
    """
    Action: plot_properties

    Contract
    --------
    - stations_map is unused (forbidden by validation).
    - action["properties"] must be a non-empty list (normalized by validation).
    - Output behavior:
        * output omitted -> ["stdout"] -> keep figures for deferred final display
        * output includes file path(s) -> save a composite image
        * if "stdout" is NOT included -> file-only (figures are labelled as file-only)
    """
    _ = debug_flag  # intentionally unused (kept for signature compatibility)
    _ = stations_map

    if Visualizer is None:
        raise RuntimeError("Visualizer is not available (import failed).")

    # Plotting deps are required for this action.
    try:
        from PIL import Image  # type: ignore
        import matplotlib
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Missing plotting dependencies (pillow/matplotlib): {e}")

    import io

    # ----------------------------
    # 1) Resolve parameters
    # ----------------------------
    params = action.get("params", {}) or {}
    v_num_points = params.get("num_points")
    if v_num_points is None:
        num_points = int(SPEC.params[0].default)
    else:
        num_points = int(v_num_points)

    # ----------------------------
    # 2) Resolve outputs
    # ----------------------------
    outputs = action.get("output")
    if outputs is None:
        outputs = ["stdout"]

    do_show = ("stdout" in outputs)
    file_outputs = [o for o in outputs if o != "stdout"]

    # ----------------------------
    # 3) Resolve properties (already normalized by manager)
    # ----------------------------
    keys_to_plot = action.get("properties")
    if not isinstance(keys_to_plot, list) or len(keys_to_plot) == 0:
        # Should not happen after validation, but keep a friendly runtime error.
        raise RuntimeError("plot_properties requires a non-empty 'properties:' list.")


    # Optional: torsion alpha for Saint-Venant torsion scaling (only meaningful if 'J_sv' is requested).
    alpha = float(action.get("torsion_alpha_sv", 0.0))

    # ----------------------------
    # 4) Call Visualizer while suppressing its internal plt.show()
    # ----------------------------
    viz = Visualizer(field)

    # Capture current figure numbers so we can identify what this action creates.
    before = set(plt.get_fignums())

    old_show = plt.show

    def _noop_show(*args: Any, **kwargs: Any) -> None:
        """Temporary replacement for plt.show() during plot_properties.

        Why: Visualizer.plot_properties currently calls plt.show() at the end.
        In CSFActions we want ONE final display at the end of main().
        """
        return None

    plt.show = _noop_show
    try:
        # Expected Visualizer signature:
        #   plot_properties(self, keys_to_plot=None, num_points=100)
        viz.plot_properties(keys_to_plot=keys_to_plot, alpha=alpha, num_points=num_points)
    finally:
        # Always restore original plt.show, even if plotting fails.
        plt.show = old_show

    # ----------------------------
    # 5) Determine which figure(s) were created
    # ----------------------------
    after = set(plt.get_fignums())
    new_nums = sorted(after - before)

    # If Visualizer reused an existing figure (rare), fall back to current figure.
    if not new_nums:
        try:
            new_nums = [plt.gcf().number]
        except Exception:
            new_nums = []

    figs = [plt.figure(n) for n in new_nums]

    # Label figures so the deferred-show logic can prune/show correctly.
    for fig in figs:
        fig.set_label("plot2d_show" if do_show else "plot2d_file")

    # ----------------------------
    # 6) Optional file output (single composite image)
    # ----------------------------
    # Keep behavior consistent with the baseline runner:
    # - fixed dpi + vertical stacking (one output path can capture multiple figures)
    if file_outputs:
        dpi = 150  # stable default; can be made configurable later if needed
        spacing_px = 10

        images: List[Image.Image] = []
        for fig in figs:
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
            buf.seek(0)
            im = Image.open(buf).convert("RGB")
            im.load()  # force full decode before closing buffer
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


# -----------------------------------------------------------------------------
# Explicit registration hook (no side effects)
# -----------------------------------------------------------------------------
def register(
    register_action: Any,
    *,
    ActionSpec: Any,
    ParamSpec: Any,
    Visualizer: Any,
) -> None:
    """
    Register this action into the shared CSFActions registry.

    Parameters are injected explicitly from CSFActions.py to avoid:
    - importing CSFActions from here (import cycles)
    - duplicating shared helpers in multiple modules
    """
    SPEC = _build_spec(ActionSpec, ParamSpec)

    # The registry expects a runner with signature:
    #   runner(field, stations_map, action, *, debug_flag=False) -> None
    def RUN(field: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool = False) -> None:
        _run(field, stations_map, action, debug_flag=debug_flag, SPEC=SPEC, Visualizer=Visualizer)

    register_action(SPEC, RUN)
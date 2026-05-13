"""
CSF Action Module: plot_weight
=============================

This module contains the logic for the `plot_weight` action.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- The module exposes:
    - SPEC: ActionSpec
    - RUN:  action runner (only action logic)
    - register(register_action, ...): explicit registration hook
- The runner does NOT call plt.show(). It only creates/labels figures.
  Final GUI display is handled centrally by CSFActions' deferred-show logic.

Notes
-----
- This action does NOT use `stations:`. It samples internally between CSF endpoints.
- The runner temporarily monkey-patches `matplotlib.pyplot.show` to a no-op because
  the current Visualizer implementation ends with a direct `plt.show()`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


# -----------------------------------------------------------------------------
# Action SPEC (help/validation)
# -----------------------------------------------------------------------------
# IMPORTANT:
# - Keep this aligned with the baseline CSFActions ActionSpec for plot_weight.
# - This is duplicated here so the module is self-contained.
def _build_spec(ActionSpec: Any, ParamSpec: Any) -> Any:
    return ActionSpec(
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
    Action: plot_weight

    Contract
    --------
    - stations_map is unused (forbidden by validation).
    - Output behavior:
        * output omitted -> ["stdout"] -> label figures as showable
        * output includes file path(s) -> save a composite image
        * if "stdout" is NOT included -> file-only (label figures as file-only)
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
    # 3) Call Visualizer while suppressing its internal plt.show()
    # ----------------------------
    viz = Visualizer(field)

    # Capture current figure numbers so we can identify what this action creates.
    before = set(plt.get_fignums())

    old_show = plt.show

    def _noop_show(*args: Any, **kwargs: Any) -> None:
        """Temporary replacement for plt.show() during plot_weight.

        Visualizer.plot_weight currently ends with plt.show() which would
        prematurely open/flush the GUI. We defer showing until CSFActions main().
        """
        return None

    plt.show = _noop_show
    try:
        # Expected Visualizer signature:
        #   plot_weight(self, num_points=100)
        viz.plot_weight(num_points=num_points)
    finally:
        # Always restore the original show function.
        plt.show = old_show

    # ----------------------------
    # 4) Determine which figure(s) were created by this action
    # ----------------------------
    after = set(plt.get_fignums())
    new_nums = sorted(after - before)

    # If Visualizer reused an existing figure (rare), fall back to current figure.
    if not new_nums:
        try:
            new_nums = [plt.gcf().number]
        except Exception:
            new_nums = []

    # Retrieve figure objects without creating new ones.
    figs = [plt.figure(n) for n in new_nums]

    # Label figures so the deferred-show logic in CSFActions can prune/show correctly.
    for fig in figs:
        fig.set_label("plot2d_show" if do_show else "plot2d_file")

    # ----------------------------
    # 5) Optional file output
    # ----------------------------
    # We save a single composite image if multiple figures were created.
    # This mirrors plot_section_2d / plot_properties behavior.
    if file_outputs:
        dpi = 150  # stable default; can be made configurable later if needed

        if not figs:
            raise RuntimeError("No figures were generated for plot_weight file output.")

        def _sanitize_filename_fragment(text: str) -> str:
            """Return a filesystem-safe fragment for output filenames."""
            cleaned = "".join(
                ch if ch.isalnum() or ch in ("-", "_") else "_"
                for ch in text.strip()
            )
            cleaned = cleaned.strip("_")
            return cleaned or "polygon"

        def _axis_tag(ax: Any, idx: int) -> str:
            """Try to derive a polygon-related tag from axis metadata; fallback to index."""
            candidates = [
                ax.get_title().strip() if hasattr(ax, "get_title") else "",
                ax.get_ylabel().strip() if hasattr(ax, "get_ylabel") else "",
                ax.get_xlabel().strip() if hasattr(ax, "get_xlabel") else "",
            ]

            if getattr(ax, "lines", None):
                for line in ax.lines:
                    label = str(line.get_label()).strip()
                    if label and not label.startswith("_"):
                        candidates.append(label)

            for text in candidates:
                if text:
                    return _sanitize_filename_fragment(text)

            return f"poly_{idx:03d}"

        for out_path in file_outputs:
            outp = Path(out_path)
            if not outp.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {outp.parent}")

            suffix = outp.suffix or ".png"
            stem = outp.stem if outp.suffix else outp.name

            if len(figs) == 1 and len(figs[0].axes) > 1:
                fig = figs[0]

                # Force a draw so tight bounding boxes are available.
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()

                target_paths = []
                for i, ax in enumerate(fig.axes, start=1):
                    tag = _axis_tag(ax, i)
                    target_path = outp.with_name(f"{stem}__{tag}{suffix}")
                    target_paths.append(target_path)

                #print(f"DEBUG plot_weight axis export targets: {[str(p) for p in target_paths]}")

                for i, ax in enumerate(fig.axes, start=1):
                    bbox = ax.get_tightbbox(renderer).expanded(1.03, 1.08)
                    bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())

                    tag = _axis_tag(ax, i)
                    target_path = outp.with_name(f"{stem}__{tag}{suffix}")

                    fig.savefig(str(target_path), dpi=dpi, bbox_inches=bbox_inches)
                    #print(f"[OK] plot_weight wrote: {target_path}")

            else:
                target_paths = [
                    outp.with_name(f"{stem}__fig_{i:03d}{suffix}")
                    for i, _fig in enumerate(figs, start=1)
                ]

                #print(f"DEBUG plot_weight figure export targets: {[str(p) for p in target_paths]}")

                for fig, target_path in zip(figs, target_paths):
                    fig.savefig(str(target_path), dpi=dpi, bbox_inches="tight")
                    #print(f"[OK] plot_weight wrote: {target_path}")


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

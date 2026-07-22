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
    #
    plt.show = _noop_show
    try:
        # Expected Visualizer signature:
        #   plot_weight(self, num_points=100)
        #
        # In file-only mode, Visualizer.plot_weight() can create more than
        # 20 figures before control returns here. The figures are saved and
        # explicitly closed later in this runner, so suppress only the
        # intermediate Matplotlib max-open-figures warning.

        with matplotlib.rc_context({"figure.max_open_warning": 0}):
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

        def _axis_polygon_tags(ax: Any, idx: int) -> tuple[str, str]:
            """
            Return the S0/S1 polygon names represented by one plot axis.

            Visualizer.plot_weight() stores the names in the main curve label:
                "s0 <name0> - s1 <name1>"

            The y-label is used as a secondary source. A generic index is used
            only if neither metadata source is available.
            """
            if getattr(ax, "lines", None):
                for line in ax.lines:
                    label = str(line.get_label()).strip()
                    if label.startswith("s0 ") and " - s1 " in label:
                        left, right = label[3:].split(" - s1 ", 1)
                        return (
                            _sanitize_filename_fragment(left),
                            _sanitize_filename_fragment(right),
                        )

            ylabel = ax.get_ylabel().strip() if hasattr(ax, "get_ylabel") else ""
            ylabel_lines = [line.strip() for line in ylabel.splitlines() if line.strip()]
            if len(ylabel_lines) >= 2:
                s0_text = ylabel_lines[0][3:] if ylabel_lines[0].startswith("s0 ") else ylabel_lines[0]
                s1_text = ylabel_lines[1][3:] if ylabel_lines[1].startswith("s1 ") else ylabel_lines[1]
                return (
                    _sanitize_filename_fragment(s0_text),
                    _sanitize_filename_fragment(s1_text),
                )

            fallback = f"poly_{idx:03d}"
            return fallback, fallback

        for out_path in file_outputs:
            outp = Path(out_path)
            if not outp.parent.exists():
                raise RuntimeError(f"Output directory does not exist: {outp.parent}")

            suffix = outp.suffix or ".png"
            stem = outp.stem if outp.suffix else outp.name
            used_target_paths = set()
            exported_axes = 0

            # Visualizer.plot_weight() may create several figures, each containing
            # up to two polygon axes. Export every axis separately; saving one file
            # per figure would merge two polygons and omit the second polygon name
            # from the generated file list.
            for fig in figs:
                axes = list(getattr(fig, "axes", []) or [])
                if not axes:
                    continue

                # Force a draw so tight bounding boxes are available.
                fig.canvas.draw()
                renderer = fig.canvas.get_renderer()

                for ax in axes:
                    exported_axes += 1

                    bbox = ax.get_tightbbox(renderer).expanded(1.03, 1.08)
                    bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())

                    name_s0, name_s1 = _axis_polygon_tags(ax, exported_axes)
                    target_path = outp.with_name(
                        f"{stem}__{name_s0}_{name_s1}{suffix}"
                    )

                    # Never overwrite another exported polygon image if two axes
                    # happen to resolve to the same sanitized name.
                    if target_path in used_target_paths:
                        target_path = outp.with_name(
                            f"{stem}__{name_s0}_{name_s1}_{exported_axes:03d}{suffix}"
                        )
                    used_target_paths.add(target_path)

                    fig.savefig(
                        str(target_path),
                        dpi=dpi,
                        bbox_inches=bbox_inches,
                    )
                    #print(f"[OK] plot_weight wrote: {target_path}")

            if exported_axes == 0:
                raise RuntimeError("No plot axes were generated for plot_weight file output.")

    # Close figures that were created by this action when the caller did not
    # request interactive display. This prevents accumulation of open figures
    # and the Matplotlib 'more than 20 figures' warning.
    if not do_show:
        try:
            for _fig in figs:
                plt.close(_fig)
        except Exception:
            pass


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

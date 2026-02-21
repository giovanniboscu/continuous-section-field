"""
actions.plot_volume_3d
----------------------

Low-impact extraction of the 'plot_volume_3d' action from CSFActions.py.

Notes
-----
- This module intentionally has NO side-effect registration to avoid circular imports.
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied "as-is" except for minimal adaptations required by dependency injection.
- This action is interactive-only: it does not write files; it creates a 3D figure and labels it so that
  CSFActions can show it at the end of the run (deferred display).
"""

from __future__ import annotations

from typing import Any, Dict, List


# Plotting dependencies:
# - We import them here (not in CSFActions) so this action remains self-contained.
# - CSFActions will show figures at the end of the run (deferred display).
try:
    from PIL import Image  # type: ignore  # noqa: F401  (kept for consistency across plotting actions)
    import matplotlib  # noqa: F401
    import matplotlib.pyplot as plt  # type: ignore
except Exception as e:
    raise RuntimeError(f"Missing plotting dependencies (pillow/matplotlib): {e}")


def register(
    register_action,
    *,
    ActionSpec,
    ParamSpec,
    Visualizer,
) -> None:
    """Register the 'plot_volume_3d' action.

    Parameters are injected from the CSFActions hub to avoid importing CSFActions here.
    """

    SPEC = ActionSpec(
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
    )


    def RUN(
        field: Any,
        stations_map: Dict[str, List[float]],
        action: Dict[str, Any],
        *,
        debug_flag: bool = False,
    ) -> None:
        """Action runner: plot_volume_3d

        Wrapper of Visualizer.plot_volume_3d(...).

        Notes
        -----
        - Does NOT use stations (uses field endpoints z0/z1).
        - Output is interactive-only:
          - if output contains 'stdout' -> create a figure labelled for deferred display.
          - if output does NOT contain 'stdout' -> close the figure (file-only is not supported by spec).
        - The runner MUST NOT call plt.show(); CSFActions handles display at end of run.
        """
        _ = stations_map
        _ = debug_flag  # unused by this action (kept for signature consistency)

        if Visualizer is None:
            raise RuntimeError("Visualizer is not available (import failed).")

        params = action.get("params", {}) or {}

        # Defaults are taken from SPEC params (robust against hub/catalog variations).
        show_end_sections = bool(params.get("show_end_sections", SPEC.params[0].default))
        line_percent = float(params.get("line_percent", SPEC.params[1].default))
        seed = int(params.get("seed", SPEC.params[2].default))
        title_raw = params.get("title", SPEC.params[3].default)
        title = "" if title_raw is None else str(title_raw)

        # This action is validated as "stdout only" by CSFActions, but we still honor the envelope here.
        out_list = action.get("output", ["stdout"])
        if isinstance(out_list, str):
            out_list = [out_list]
        do_show = ("stdout" in out_list)

        viz = Visualizer(field)

        # Create a dedicated figure with a 3D axes.
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        viz.plot_volume_3d(
            show_end_sections=show_end_sections,
            line_percent=line_percent,
            seed=seed,
            title=title,
            ax=ax,
        )

        # Label for deferred display logic in CSFActions.
        # - plot3d_show: keep for interactive display
        # - plot3d_file: file-only (not supported here, but label is reserved for future)
        fig.set_label("plot3d_show" if do_show else "plot3d_file")

        # If the user requested file-only output (should be rejected by validation),
        # we proactively close the figure to avoid leaving GUI artifacts open.
        if not do_show:
            try:
                plt.close(fig)
            except Exception:
                pass


    register_action(SPEC, RUN)

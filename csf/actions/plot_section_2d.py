# actions/plot_section_2d.py
#
# NOTE:
# This module implements the 'plot_section_2d' action in an import-safe way:
# - No imports from CSFActions.py (avoids circular imports).
# - Explicit registration via register(register_action, ...).
# - Plotting dependencies (Pillow / Matplotlib) are imported inside RUN(...).
#
# The action produces:
# - Optional interactive display: requested ONLY when 'stdout' is in action.output.
# - Optional file output: one composite raster image stacking all stations vertically.
#
# IMPORTANT:
# This action does NOT call plt.show(). Display is deferred and handled by CSFActions.py
# after all actions have completed, to ensure sequential auto-advance display without
# manual window interaction.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def register(
    register_action,
    *,
    ActionSpec,
    ParamSpec,
    expand_station_names,
    get_bool_param_strict,
    Visualizer,
) -> None:
    """Register the action (explicit registration; no side-effects)."""

    SPEC = ActionSpec(
        name="plot_section_2d",
        summary="Plot 2D section geometry at one or more stations.",
        description=(
            "Renders a 2D plot of the cross-section polygons at each requested station z.\n"
            "\n"
            "YAML fields\n"
            "- stations: REQUIRED. One or more station-set names defined under CSF_ACTIONS.stations (absolute z).\n"
            "- output:  OPTIONAL. Default is [stdout] (show a window at end of run, if supported).\n"
            "          If one or more image file paths are provided, figures are saved to disk.\n"
            "          If multiple stations are requested AND output contains file paths, a single\n"
            "          composite image is produced (stacked vertically), for deterministic reporting.\n"
            "\n"
            "Params\n"
            "- show_ids        : include polygon indices (#0, #1, ...).\n"
            "- show_weights    : include polygon weight values in the labels/legend.\n"
            "- show_vertex_ids : label each vertex with a 1-based index (debug/diagnostic).\n"
            "- title           : optional title string; if it contains '{z}', it is formatted with z.\n"
            "- dpi             : raster DPI for saved images."
        ),
        params=(
            ParamSpec(
                name="show_ids",
                required=False,
                typ="bool",
                default=True,
                description="Show polygon indices (#0, #1, ...).",
            ),
            ParamSpec(
                name="show_weights",
                required=False,
                typ="bool",
                default=True,
                description="Show polygon weights and names in plot labels.",
            ),
            ParamSpec(
                name="show_vertex_ids",
                required=False,
                typ="bool",
                default=False,
                description="Label each polygon vertex with a 1-based index.",
            ),
            ParamSpec(
                name="title",
                required=False,
                typ="str",
                default=None,
                description="Plot title. If it contains '{z}', it will be replaced with the station value.",
            ),
            ParamSpec(
                name="dpi",
                required=False,
                typ="int",
                default=150,
                description="Rasterization DPI when saving images.",
            ),
        ),
    )

    def RUN(field: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool = False) -> None:
        """Runner for plot_section_2d (logic migrated from the monolith; behavior preserved)."""

        # Local imports keep the module importable even if optional deps are missing.
        import io

        try:
            from PIL import Image  # type: ignore
            import matplotlib  # noqa: F401  # imported to ensure matplotlib is available
            import matplotlib.pyplot as plt  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Missing plotting dependencies (pillow/matplotlib): {e}")

        # ----------------------------
        # 1) Resolve parameters
        # ----------------------------
        params = action.get("params", {}) or {}

        show_ids = get_bool_param_strict(
            params,
            "show_ids",
            SPEC.params[0].default,
            path="CSF_ACTIONS.actions.plot_section_2d.params.show_ids",
        )
        show_weights = get_bool_param_strict(
            params,
            "show_weights",
            SPEC.params[1].default,
            path="CSF_ACTIONS.actions.plot_section_2d.params.show_weights",
        )
        show_vertex_ids = get_bool_param_strict(
            params,
            "show_vertex_ids",
            SPEC.params[2].default,
            path="CSF_ACTIONS.actions.plot_section_2d.params.show_vertex_ids",
        )

        title_tpl = params.get("title", SPEC.params[3].default)
        dpi = int(params.get("dpi", SPEC.params[4].default))
        spacing_px = int(params.get("spacing_px", 10))

        # ----------------------------
        # 2) Resolve outputs
        # ----------------------------
        outputs = action.get("output")
        if outputs is None:
            outputs = ["stdout"]

        # For plot_section_2d:
        # - include 'stdout' to request deferred interactive display (handled by CSFActions.py at end)
        # - omit 'stdout' to generate files only (figures will be pruned/closed at end)
        do_show = ("stdout" in outputs)
        file_outputs = [o for o in outputs if o != "stdout"]

        # ----------------------------
        # 3) Expand stations -> z list
        # ----------------------------
        z_list = expand_station_names(stations_map, action["stations"])

        # ----------------------------
        # 4) Build one figure per station (and optionally capture images for file output)
        # ----------------------------
        if Visualizer is None:
            raise RuntimeError("Visualizer is not available (import failed).")

        viz = Visualizer(field)

        figs = []
        images: List[Image.Image] = []

        for z in z_list:
            zf = float(z)

            # Create a dedicated figure/ax so plots don't overwrite each other.
            fig, ax = plt.subplots()

            # Optional title formatting
            if isinstance(title_tpl, str):
                title = title_tpl.replace("{z}", str(zf))
            elif title_tpl is None:
                title = None
            else:
                # any other YAML type -> coerce to string
                title = str(title_tpl)

            # Delegate actual plotting to the Visualizer wrapper.
            viz.plot_section_2d(
                z=zf,
                show_ids=show_ids,
                show_weights=show_weights,
                show_vertex_ids=show_vertex_ids,
                title=title,
                ax=ax,
            )

            # Label figures so CSFActions.py can prune/show them deterministically.
            fig.set_label("plot2d_show" if do_show else "plot2d_file")
            figs.append(fig)

            # If we need a raster output file, render the figure into a PIL image now.
            if file_outputs:
                buf = io.BytesIO()

                # Use bbox_inches='tight' to keep legends/labels visible.
                # NOTE: legends outside axes are not reliably included by bbox_inches='tight' alone;
                # we pass Legend artists explicitly via bbox_extra_artists when possible.
                from matplotlib.legend import Legend  # local import, lightweight

                extra_artists = []
                try:
                    for child in ax.get_children():
                        if isinstance(child, Legend):
                            extra_artists.append(child)
                    for lg in getattr(fig, "legends", []) or []:
                        if lg not in extra_artists:
                            extra_artists.append(lg)
                except Exception:
                    extra_artists = []

                # Force a draw to ensure extents are up-to-date before savefig.
                try:
                    fig.canvas.draw()
                except Exception:
                    pass

                save_kwargs = dict(format="png", dpi=dpi, bbox_inches="tight")
                if extra_artists:
                    save_kwargs["bbox_extra_artists"] = extra_artists

                fig.savefig(buf, **save_kwargs)
                buf.seek(0)

                im = Image.open(buf).convert("RGB")
                im.load()  # force full decode before closing buffer
                buf.close()

                images.append(im)

        # ----------------------------
        # 5) Save composite image (if requested)
        # ----------------------------
        if file_outputs:
            if not images:
                raise RuntimeError("No images were generated for file output.")

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
                p = Path(out_path)
                if not p.parent.exists():
                    raise RuntimeError(f"Output directory does not exist: {p.parent}")
                composite.save(str(p), dpi=(dpi, dpi))
                print(f"[OK] plot_section_2d wrote: {p}")

        # ----------------------------
        # 6) Defer showing (always)
        # ----------------------------
        # This action never calls plt.show(). Display is handled once at the end of the run.

        # ----------------------------
        # 7) Figure lifecycle
        # ----------------------------
        # We do not close figures here; CSFActions.py will close them after sequential display
        # (or immediately if interactive display is not requested).
        _ = figs  # keep for possible future debugging/hooks

    register_action(SPEC, RUN)


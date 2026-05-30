"""
actions.write_sap2000_geometry
------------------------------

Low-impact extraction of the 'write_sap2000_geometry' action from CSFActions.py.

Design constraints
- No side-effect registration (to avoid circular imports).
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied as-is, with only the minimal adjustments needed:
  - A common runner signature that accepts debug_flag (ignored here).
  - Dependencies (write_sap2000_template_pack + the hub ActionSpec instance) are injected.

Behavioral contract (must remain stable)
- 'stations' is optional: if provided, explicit absolute stations are used; otherwise Lobatto is used.
- 'output' is REQUIRED and must be file-only: exactly one file path; 'stdout' is forbidden.
- include_plot writes the preview PNG and queues that PNG for deferred display without blocking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def register(
    register_action,
    *,
    spec,
    write_sap2000_template_pack,
) -> None:
    """
    Register the 'write_sap2000_geometry' action.

    Parameters are injected from the CSFActions hub to avoid importing CSFActions here.
    """
    SPEC = spec  # Use the hub spec to guarantee help/param defaults stay identical.

    def RUN(
        field: Any,
        stations_map: Dict[str, List[float]],
        action: Dict[str, Any],
        *,
        debug_flag: bool = False,
    ) -> None:
        """Action: export_model/write_sap2000_geometry (SAP2000 template pack)

        This action writes a *human-readable* text file designed to help users build
        a SAP2000 text-table import (or to manually copy/paste the relevant blocks).

        It intentionally does NOT claim to generate a fully importable SAP2000 .s2k
        file (SAP2000 text tables can be version-dependent, and we do not enforce
        units or SAP-side modeling assumptions here).

        YAML shape (validated before execution):
          - export_model/write_sap2000_geometry:
              output: [out/model_export_template.txt]   # required, file-only (no stdout)
              params:
                n_intervals: 6                          # required int (stations = n_intervals + 1)
                material_name: S355                     # optional (default 'S355')
                E_ref: 2.1e+11                          # required float (suggested; written in header)
                nu: 0.30                                # required float (suggested; written in header)
                mode: BOTH                              # optional: CENTROIDAL_LINE | REFERENCE_LINE | BOTH
                include_plot: true                      # optional (default True)
                plot_filename: section_variation.png    # optional (default 'section_variation.png')

        """
        # stations_map is unused by design (stations generated internally).
        _ = stations_map

        # debug_flag is accepted for signature consistency; this action does not use it.
        _ = debug_flag

        # Defensive import check (validation should have already ensured this).
        if write_sap2000_template_pack is None:
            raise RuntimeError("export_model/write_sap2000_template_pack/export_model is not available (sap2000_v2 import failed).")

        # Read and normalize parameters.
        params = action.get("params", {}) or {}

        n_intervals = params.get("n_intervals")
        E_ref = params.get("E_ref")
        nu = params.get("nu")

        # Optional parameters with defaults defined in the action spec.
        material_name = params.get("material_name")
        if material_name is None:
            # Prefer spec default if present, otherwise fall back to the historical hard default.
            try:
                d = None
                for ps in getattr(SPEC, "params", ()) or ():
                    if getattr(ps, "name", None) == "material_name":
                        d = getattr(ps, "default", None)
                        break
                material_name = d if d is not None else "S355"
            except Exception:
                material_name = "S355"
        if material_name is None:
            material_name = "S355"

        mode = params.get("mode")
        if mode is None:
            mode = "BOTH"
        mode_str = str(mode).strip()

        # Normalize common user inputs (case-insensitive).
        mode_norm = mode_str.upper()
        if mode_norm == "CENTROIDAL":
            mode_norm = "CENTROIDAL_LINE"
        if mode_norm == "REFERENCE":
            mode_norm = "REFERENCE_LINE"
        if mode_norm not in ("CENTROIDAL_LINE", "REFERENCE_LINE", "BOTH"):
            raise ValueError(f"Invalid mode='{mode_str}'. Expected CENTROIDAL_LINE, REFERENCE_LINE, or BOTH.")

        include_plot = params.get("include_plot")
        if include_plot is None:
            include_plot = True
        include_plot_bool = bool(include_plot)

        plot_filename = params.get("plot_filename")
        if plot_filename is None:
            plot_filename = "section_variation.png"
        plot_filename_str = str(plot_filename)

        # Output path (file-only).
        output_list = action.get("output", [])
        out_files = [o for o in output_list if isinstance(o, str) and o != "stdout"]
        if len(out_files) != 1:
            # Defensive check (should not happen if validation passed).
            raise ValueError(f"export_model/write_sap2000_geometry requires exactly one output template path, got: {output_list}")
        template_path = Path(out_files[0])

        # Ensure the output directory exists. We do this here (runtime) in addition to
        # the validator's basic writability checks, because users often generate the
        # destination folder as part of their workflow.
        if template_path.parent and str(template_path.parent) not in (".", ""):
            template_path.parent.mkdir(parents=True, exist_ok=True)

        # If the user asked for a plot and gave only a bare filename, save it next to the
        # template file (more predictable than saving in the current working directory).
        if include_plot_bool:
            pf = Path(plot_filename_str)
            if (not pf.is_absolute()) and (str(pf.parent) in (".", "")):
                plot_filename_str = str(template_path.parent / pf.name)
                pf = Path(plot_filename_str)

            # Ensure the preview plot directory exists too.
            if pf.parent and str(pf.parent) not in (".", ""):
                pf.parent.mkdir(parents=True, exist_ok=True)

        # Determine station source with backward-compatible precedence:
        # 1) If action 'stations' are provided (resolved by hub into stations_map), use them.
        # 2) Otherwise, use historical Lobatto generation via n_intervals.
        z_values: List[float] | None = None
        # Determine explicit stations only from action['stations'] reference,
        # not from the full stations_map container.
        action_stations = action.get("stations", [])
        if isinstance(action_stations, str):
            action_stations = [action_stations]

        if len(action_stations) == 0:
            # Backward-compatible path: no explicit stations -> Lobatto (n_intervals)
            z_values = None
        else:
            if len(action_stations) != 1:
                raise RuntimeError(
                    "export_model/write_sap2000_geometry accepts exactly one station set name in 'stations'."
                )

            sname = action_stations[0]
            if sname not in stations_map:
                raise RuntimeError(
                    f"export_model/write_sap2000_geometry: station set '{sname}' not found in resolved stations."
                )

            z_values = stations_map[sname]

            # Minimal explicit validation (clear errors, no silent fix)
            if not isinstance(z_values, list) or len(z_values) < 3:
                raise RuntimeError(
                    f"Station set '{sname}' must contain at least 3 absolute z values."
                )
            prev = None
            for i, v in enumerate(z_values):
                try:
                    zv = float(v)
                except Exception:
                    raise RuntimeError(f"Station set '{sname}' has non-numeric value at index {i}: {v!r}")
                if prev is not None and not (zv > prev):
                    raise RuntimeError(
                        f"Station set '{sname}' must be strictly increasing (index {i-1}->{i})."
                    )
                prev = zv











        # Call the generator. The function writes the template pack and (optionally) the plot file.
        # IMPORTANT:
        # - include_plot controls file generation of the preview PNG.
        # - show_plot is forced to False because write_sap2000_template_pack may call plt.show(),
        #   which blocks the later CSFActions deferred-display queue.
        # - If include_plot=True, we reopen the saved PNG as a normal Matplotlib figure and label it
        #   as plot2d_show, so CSFActions will display it at the end together with the other plots.
        try:
            import matplotlib.pyplot as plt  # type: ignore
        except Exception:
            plt = None  # type: ignore

        figs_before = set(plt.get_fignums()) if plt is not None else set()

        try:
            try:
                write_sap2000_template_pack(
                    field,
                    n_intervals=int(n_intervals) if n_intervals is not None else 20,
                    template_filename=str(template_path),
                    mode=mode_norm,  # type: ignore[arg-type]
                    material_name=str(material_name),
                    E_ref=float(E_ref),
                    nu=float(nu),
                    include_plot=include_plot_bool,
                    plot_filename=plot_filename_str,
                    show_plot=False,
                    z_values=z_values,
                )
            except TypeError:
                # Legacy compatibility: older base function without z_values argument.
                write_sap2000_template_pack(
                    field,
                    n_intervals=int(n_intervals) if n_intervals is not None else 20,
                    template_filename=str(template_path),
                    mode=mode_norm,  # type: ignore[arg-type]
                    material_name=str(material_name),
                    E_ref=float(E_ref),
                    nu=float(nu),
                    include_plot=include_plot_bool,
                    plot_filename=plot_filename_str,
                    show_plot=False,
                )
        finally:
            # Remove any unlabelled figures created internally by the generator.
            # The only interactive figure we keep/create below is the labelled preview figure.
            if plt is not None:
                for num in set(plt.get_fignums()) - figs_before:
                    try:
                        plt.close(num)
                    except Exception:
                        pass

        if include_plot_bool:
            preview_path = Path(plot_filename_str)
            if not preview_path.exists():
                raise RuntimeError(
                    f"include_plot=True but the preview image was not created: {preview_path}"
                )

            if plt is not None:
                try:
                    from PIL import Image  # type: ignore

                    im = Image.open(preview_path).convert("RGB")

                    # Display the already-saved preview image without adding
                    # Matplotlib subplot margins around it.
                    # This keeps export_model/include_plot non-blocking while
                    # showing the PNG at its natural aspect ratio in the final
                    # CSFActions deferred display.
                    w_px, h_px = im.size
                    dpi_display = 100.0
                    fig = plt.figure(figsize=(w_px / dpi_display, h_px / dpi_display), dpi=dpi_display)
                    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
                    ax.imshow(im)
                    ax.set_axis_off()
                    ax.set_position([0.0, 0.0, 1.0, 1.0])
                    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
                    fig.set_label("plot2d_show")
                    try:
                        fig.canvas.manager.set_window_title(str(preview_path.name))
                    except Exception:
                        pass
                except Exception as e:
                    raise RuntimeError(
                        f"Preview image was created but could not be prepared for display: {preview_path} ({e})"
                    )

    register_action(SPEC, RUN)

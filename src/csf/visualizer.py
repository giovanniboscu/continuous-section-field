from __future__ import annotations
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from typing import Tuple, Dict, Optional, List
import math
import random
import warnings
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
from datetime import datetime
from typing import  Union, Literal
from pathlib import Path
import io
from collections import defaultdict
from contextlib import redirect_stdout
import random as _random
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from . import _tol
from .continuous_section_field import ContinuousSectionField
from .continuous_section_field import _set_axes_equal_3d
from .section_field import section_full_analysis

def plot_section_variation(
    
    stations_data: Sequence[Dict[str, Any]],
    filename: str = "section_variation.png",
    show: bool = False,
) -> str:
    """
    Plot a quick visual preview of how a few properties vary along z.

    Notes
    -----
    - This function is optional. It only runs if matplotlib is available.
    - Units are intentionally NOT printed; they depend on the user's consistent unit system.
    - The function expects each station dict to have at least:
        'z', 'A', 'Ix', 'Iy', 'Ip'

    Parameters
    ----------
    stations_data:
        List of station dictionaries produced by _compute_station_data(...)
    filename:
        Path to save the plot image.
    show:
        If True, calls plt.show(). Otherwise it only saves.

    Returns
    -------
    str:
        The image path written to disk.

    Raises
    ------
    RuntimeError:
        If matplotlib is not available.
    """
    
    z = [st['z'] for st in stations_data]
    area = [st['A'] for st in stations_data]
    i33 = [st['Ix'] for st in stations_data]
    i22 = [st['Iy'] for st in stations_data]
    j = [st['Ip'] for st in stations_data]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Plot Area
    ax1.plot(z, area, 'o-', color='blue', label='Area')
    ax1.set_ylabel('Cross Section Area')
    ax1.grid(True, linestyle='--')
    ax1.legend()
    ax1.set_title('Variation of Geometric Properties along Z (Absolute)')

    # Plot Inertia and Polar Moment
    ax2.plot(z, i33, 's-', color='red', label='I33 (Ix)')
    ax2.plot(z, i22, 'd-', color='green', label='I22 (Iy)')
    ax2.plot(z, j, 'x--', color='purple', label='Ip')
    ax2.set_xlabel('Z coordinate')
    ax2.set_ylabel('Inertia / Polar Moment')
    ax2.grid(True, linestyle='--')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(filename)
    #print(f"[PLOT] Preview saved as '{filename}'")
    if show:
        plt.show()




class Visualizer:
    """
    Adds 2D and 3D plotting utilities on top of a ContinuousSectionField.
    """

    def __init__(self, field: ContinuousSectionField):
        self.field = field
    # ----------------------------------------------------------------------------




    def plot_weight(self, num_points=100, tol=1e-12, poly_indices_to_plot=None):
        """
        Plot w(z) per polygon pair, skipping polygons with w(z) == 0 for all sampled z.
        Skipped polygons are listed in a figure note.
        Min/Max markers are shown on each plotted curve.

        Parameters
        ----------
        num_points : int
            Number of z sample points in [s0.z, s1.z].
        tol : float
            Absolute tolerance used to classify a polygon as "zero-flat" over sampled z.
        poly_indices_to_plot : list[int] | tuple[int] | set[int] | None
            Optional explicit polygon indices to plot (0-based). Can include gaps (e.g., [0, 2, 5]).
            If provided, only indices in this list are considered, after removing zero-flat polygons.
            Indices out of range are ignored.
        """
        
        #poly_indices_to_plot=poly_indices_to_plot+1            
        z_start = self.field.s0.z
        z_end = self.field.s1.z
        z_values = np.linspace(z_start, z_end, num_points)

        num_polys = len(self.field.s0.polygons)
        poly_w_series = {i: [] for i in range(num_polys)}
        
        # Evaluate weights for every polygon index at every sampled z
        for z in z_values:
            for i in range(num_polys):
                p0 = self.field.s0.polygons[i]
                p1 = self.field.s1.polygons[i]

                if self.field.weight_laws is not None and (i + 1) in self.field.weight_laws: # 1 based i'm sorry
                    current_law = self.field.weight_laws[i + 1]
                else:
                    current_law = None
                
                zlocal= z - self.field.s0.z

                w_val = self.field._interpolate_weight(
                    p0.weight, p1.weight, zlocal, p0, p1, current_law
                )
                
                poly_w_series[i].append(float(w_val))

        # Split polygons: zero-flat vs plottable (non-zero)
        zero_polys = []
        plot_indices = []

        for i in range(num_polys):
            p0 = self.field.s0.polygons[i]
            p1 = self.field.s1.polygons[i]
            label = f"[{i}] s0:{p0.name} -> s1:{p1.name}"

            y = np.asarray(poly_w_series[i], dtype=float)
            if np.all(np.isclose(y, 0.0, atol=tol, rtol=0.0)):
                zero_polys.append(label)
            else:
                plot_indices.append(i)

        # If user provided an explicit index list, filter plot_indices accordingly
        if poly_indices_to_plot is not None:
            if not isinstance(poly_indices_to_plot, (list, tuple, set)):
                raise TypeError(
                    "poly_indices_to_plot must be a list/tuple/set of 0-based integer indices, or None."
                )

            requested = []
            for v in poly_indices_to_plot:
                if not isinstance(v, (int, np.integer)):
                    raise TypeError(
                        "poly_indices_to_plot must contain only integers (0-based polygon indices)."
                    )
                iv = int(v)
                if 0 <= iv < num_polys:
                    requested.append(iv)

            # Preserve original plotting order (by index order in plot_indices), not user list order
            requested_set = set(requested)
            plot_indices = [i for i in plot_indices if i in requested_set]

        # If nothing remains after filtering, do not plot
        if len(plot_indices) == 0:
            print("No polygons to plot after filtering (zero-flat and/or poly_indices_to_plot).")
            if zero_polys:
                print("Skipped polygons (w=0 for all sampled z):")
                for s in zero_polys:
                    print(" -", s)
            return

        # Create multiple figures, max 2 polygons per figure (keep all windows identical)
        MAX_PLOTS_PER_FIG = 2  # Max number of polygon plots per window (do not expose as a function parameter)
        FIGSIZE = (10, 2.4 * MAX_PLOTS_PER_FIG)  # Fixed size for all figures to avoid "odd last window" sizing

        n_plot = len(plot_indices)

        #print("\n=== START WEIGHT MIN/MAX REPORT ===")

        for start in range(0, n_plot, MAX_PLOTS_PER_FIG):
            # Take up to MAX_PLOTS_PER_FIG polygon indices for this figure
            chunk = plot_indices[start : start + MAX_PLOTS_PER_FIG]

            # Create a single full-height axis when only one polygon remains.
            if len(chunk) == 1:
                fig_w, ax_single = plt.subplots(1, 1, figsize=FIGSIZE, sharex=True)
                axes_w = [ax_single]
            else:
                fig_w, axes_w = plt.subplots(
                    MAX_PLOTS_PER_FIG, 1, figsize=FIGSIZE, sharex=True
                )
                axes_w = list(np.ravel(axes_w))

            for ax_pos in range(len(chunk)):
                ax = axes_w[ax_pos]

                i = chunk[ax_pos]
                p0 = self.field.s0.polygons[i]
                p1 = self.field.s1.polygons[i]
                y = np.asarray(poly_w_series[i], dtype=float)


                idx_min = int(np.argmin(y))
                idx_max = int(np.argmax(y))
                w_min, w_max = float(y[idx_min]), float(y[idx_max])
                z_min, z_max = float(z_values[idx_min]), float(z_values[idx_max])
                '''
                print(
                    f"[{i}] s0:{p0.name} -> s1:{p1.name} | "
                    f"min w={w_min:.12g} at z={z_min:.12g} | "
                    f"max w={w_max:.12g} at z={z_max:.12g}"
                )
                '''
                # Main curve
                ax.plot(z_values, y, linewidth=1.5, label=f"s0 {p0.name} - s1 {p1.name}")

                # Min/Max markers on the curve
                ax.scatter([z_min], [w_min], marker="v", s=26, zorder=3, label="min")
                ax.scatter([z_max], [w_max], marker="^", s=26, zorder=3, label="max")

                # Optional tiny text near markers
                ax.annotate(
                    f"{w_min:.4f}", (z_min, w_min),
                    textcoords="offset points", xytext=(4, -12), fontsize=7
                )
                ax.annotate(
                    f"{w_max:.4f}", (z_max, w_max),
                    textcoords="offset points", xytext=(4, 6), fontsize=7
                )

                # y-limits with a small margin for readability
                if w_max != w_min:
                    margin = (w_max - w_min) * 0.10
                else:
                    margin = max(abs(w_max) * 0.05, 0.05)
                ax.set_ylim(w_min - margin, w_max + margin)

                ax.set_ylabel(f"s0 {p0.name}\ns1 {p1.name}", fontweight="bold")
                ax.grid(True, linestyle="--", alpha=0.5)
                ax.set_title(
                    f"Weight (w) | min={w_min:.6f} @ z={z_min:.3f} | max={w_max:.6f} @ z={z_max:.3f}",
                    loc="right", fontsize=8
                )

            # Put x-label on the last active axis in this figure
            axes_w[len(chunk) - 1].set_xlabel("z")

            # Figure-level note for zero-flat polygons (repeat on each figure for consistency)
            if zero_polys:
                note = "Skipped (w=0 for all z): " + "; ".join(zero_polys)
                fig_w.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8)

            # Same title on every window
            fig_w.suptitle(
                f"Individual Polygon Weight (w) Distributions (Interpolated # {num_points} points)",
                fontweight="bold"
            )
            
            fig_w.tight_layout(rect=[0, 0.04, 1, 0.96])

        #print("=== END WEIGHT MIN/MAX REPORT ===")
        # plt.show()

    def plot_shear_weight(self, num_points=100, tol=1e-12, poly_indices_to_plot=None):
        """
        Plot w(z) per polygon pair, skipping polygons with w(z) == 0 for all sampled z.
        Skipped polygons are listed in a figure note.
        Min/Max markers are shown on each plotted curve.

        Parameters
        ----------
        num_points : int
            Number of z sample points in [s0.z, s1.z].
        tol : float
            Absolute tolerance used to classify a polygon as "zero-flat" over sampled z.
        poly_indices_to_plot : list[int] | tuple[int] | set[int] | None
            Optional explicit polygon indices to plot (0-based). Can include gaps (e.g., [0, 2, 5]).
            If provided, only indices in this list are considered, after removing zero-flat polygons.
            Indices out of range are ignored.
        """
        
        z_start = self.field.s0.z
        z_end = self.field.s1.z
        z_values = np.linspace(z_start, z_end, num_points)

        num_polys = len(self.field.s0.polygons)
        poly_w_series = {i: [] for i in range(num_polys)}
        
        # Evaluate weights for every polygon index at every sampled z
        for z in z_values:
            for i in range(num_polys):
                p0 = self.field.s0.polygons[i]
                p1 = self.field.s1.polygons[i]

                if self.field.shear_weight_laws is not None and (i) in self.field.shear_weight_laws:
                    current_shear_law = self.field.shear_weight_laws[i]
                else:
                    current_shear_law = None
                
                if self.field.weight_laws is not None and (i + 1) in self.field.weight_laws: # 1 based i'm sorry
                    current_law = self.field.weight_laws[i + 1]
                else:
                    current_law = None
                


                zlocal= z - self.field.s0.z
                


                w_val = self.field._interpolate_weight(
                    p0.weight, p1.weight, zlocal, p0, p1, current_law
                )
                

                shear_w_val = self.field._interpolate_shear_weight(w_val,
                    p0.weight, p1.weight, zlocal, p0, p1, current_shear_law
                )
                
                poly_w_series[i].append(float(shear_w_val))

        # Split polygons: zero-flat vs plottable (non-zero)
        zero_polys = []
        plot_indices = []

        for i in range(num_polys):
            p0 = self.field.s0.polygons[i]
            p1 = self.field.s1.polygons[i]
            label = f"[{i}] s0:{p0.name} -> s1:{p1.name}"

            y = np.asarray(poly_w_series[i], dtype=float)
            if np.all(np.isclose(y, 0.0, atol=tol, rtol=0.0)):
                zero_polys.append(label)
            else:
                plot_indices.append(i)

        # If user provided an explicit index list, filter plot_indices accordingly
        if poly_indices_to_plot is not None:
            if not isinstance(poly_indices_to_plot, (list, tuple, set)):
                raise TypeError(
                    "poly_indices_to_plot must be a list/tuple/set of 0-based integer indices, or None."
                )

            requested = []
            for v in poly_indices_to_plot:
                if not isinstance(v, (int, np.integer)):
                    raise TypeError(
                        "poly_indices_to_plot must contain only integers (0-based polygon indices)."
                    )
                iv = int(v)
                if 0 <= iv < num_polys:
                    requested.append(iv)

            # Preserve original plotting order (by index order in plot_indices), not user list order
            requested_set = set(requested)
            plot_indices = [i for i in plot_indices if i in requested_set]

        # If nothing remains after filtering, do not plot
        if len(plot_indices) == 0:
            print("No polygons to plot after filtering (zero-flat and/or poly_indices_to_plot).")
            if zero_polys:
                print("Skipped polygons (w=0 for all sampled z):")
                for s in zero_polys:
                    print(" -", s)
            return

        # Create multiple figures, max 2 polygons per figure (keep all windows identical)
        MAX_PLOTS_PER_FIG = 2  # Max number of polygon plots per window (do not expose as a function parameter)
        FIGSIZE = (10, 2.4 * MAX_PLOTS_PER_FIG)  # Fixed size for all figures to avoid "odd last window" sizing

        n_plot = len(plot_indices)

        #print("\n=== START WEIGHT MIN/MAX REPORT ===")

        for start in range(0, n_plot, MAX_PLOTS_PER_FIG):
            # Take up to MAX_PLOTS_PER_FIG polygon indices for this figure
            chunk = plot_indices[start : start + MAX_PLOTS_PER_FIG]

            # Create a single full-height axis when only one polygon remains.
            if len(chunk) == 1:
                fig_w, ax_single = plt.subplots(1, 1, figsize=FIGSIZE, sharex=True)
                axes_w = [ax_single]
            else:
                fig_w, axes_w = plt.subplots(
                    MAX_PLOTS_PER_FIG, 1, figsize=FIGSIZE, sharex=True
                )
                axes_w = list(np.ravel(axes_w))

            for ax_pos in range(len(chunk)):
                ax = axes_w[ax_pos]

                i = chunk[ax_pos]
                p0 = self.field.s0.polygons[i]
                p1 = self.field.s1.polygons[i]
                y = np.asarray(poly_w_series[i], dtype=float)


                idx_min = int(np.argmin(y))
                idx_max = int(np.argmax(y))
                w_min, w_max = float(y[idx_min]), float(y[idx_max])
                z_min, z_max = float(z_values[idx_min]), float(z_values[idx_max])
                if 1==2:
                  print(
                      f"[{i}] s0:{p0.name} -> s1:{p1.name} | "
                      f"min w={w_min:.12g} at z={z_min:.12g} | "
                      f"max w={w_max:.12g} at z={z_max:.12g}"
                  )
                # Main curve
                ax.plot(z_values, y, linewidth=1.5, label=f"s0 {p0.name} - s1 {p1.name}")

                # Min/Max markers on the curve
                ax.scatter([z_min], [w_min], marker="v", s=26, zorder=3, label="min")
                ax.scatter([z_max], [w_max], marker="^", s=26, zorder=3, label="max")

                # Optional tiny text near markers
                ax.annotate(
                    f"{w_min:.4f}", (z_min, w_min),
                    textcoords="offset points", xytext=(4, -12), fontsize=7
                )
                ax.annotate(
                    f"{w_max:.4f}", (z_max, w_max),
                    textcoords="offset points", xytext=(4, 6), fontsize=7
                )

                # y-limits with a small margin for readability
                if w_max != w_min:
                    margin = (w_max - w_min) * 0.10
                else:
                    margin = max(abs(w_max) * 0.05, 0.05)
                ax.set_ylim(w_min - margin, w_max + margin)

                ax.set_ylabel(f"s0 {p0.name}\ns1 {p1.name}", fontweight="bold")
                ax.grid(True, linestyle="--", alpha=0.5)
                ax.set_title(
                    f"Weight (w) | min={w_min:.6f} @ z={z_min:.3f} | max={w_max:.6f} @ z={z_max:.3f}",
                    loc="right", fontsize=8
                )

            # Put x-label on the last active axis in this figure
            axes_w[len(chunk) - 1].set_xlabel("z")

            # Figure-level note for zero-flat polygons (repeat on each figure for consistency)
            if zero_polys:
                note = "Skipped (w=0 for all z): " + "; ".join(zero_polys)
                fig_w.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8)

            # Same title on every window
            fig_w.suptitle(
                f"Individual Polygon Shear Weight (sw) Distributions (Interpolated # {num_points} points)",
                fontweight="bold"
            )
            
            fig_w.tight_layout(rect=[0, 0.04, 1, 0.96])


    # ----------------------------------------------------------------------------
  
    def plot_properties(self, keys_to_plot=None, alpha=1,title: str = "Plot Properties",num_points=100):
        """
        Plot the evolution of selected section properties along the Z-axis.

        Generic behavior for returned values:
        - If a property is scalar -> plot on left y-axis.
        - If a property returns a pair (left_value, right_value):
            * left_value  is plotted on left y-axis
            * right_value is plotted on right y-axis (twin axis)

        Title behavior:
        - Right side (top): min/max summary of left channel (same style as before)
        - Left side  (top): only t(z0), t(z1) when right channel exists

        Args:
            keys_to_plot (list[str] | None):
                Property keys to plot (e.g., ["A", "Ix", "Iy"]).
                If None, defaults to empty list.
            alpha (float):
                Passed through to section_full_analysis.
            num_points (int):
                Number of z samples between s0.z and s1.z.
        """

        if keys_to_plot is not None:
            keys_to_plot = list(dict.fromkeys(keys_to_plot))      
        keys_to_plot = [k for k in keys_to_plot if str(k).lower() != "geometry"]             
        
        # Z bounds from field endpoints
        z_start = self.field.s0.z
        z_end = self.field.s1.z

        # Keep current convention: None -> empty list
        if keys_to_plot is None:
            keys_to_plot = []

        # Early exit if no keys are requested
        if len(keys_to_plot) == 0:
            #plt.show()
            return

        # Uniform sampling along z
        z_values = np.linspace(z_start, z_end, num_points)

        # Left-axis values (main channel)
        data_series = {key: [] for key in keys_to_plot}

        # Right-axis values (secondary channel; only if property returns a pair)
        data_series_right = {key: [] for key in keys_to_plot}

        # -------------------------------------------------------------------------
        # 1) Evaluate properties at each sampled z
        # -------------------------------------------------------------------------

        # if roark not need not performed
        need_vroark = (
            "J_s_vroark" in keys_to_plot
            or "J_s_vroark_fidelity" in keys_to_plot
        )        


        for z in z_values:
            # Build section at current z
            current_section = self.field.section(z)

            # Compute all properties for current section

            props = section_full_analysis(
                current_section,
                compute_vroark=need_vroark,
            )

            for key in keys_to_plot:
                if key not in props:
                    # Keep alignment with z_values even when key is missing
                    data_series[key].append(np.nan)
                    data_series_right[key].append(np.nan)
                    continue

                raw = props[key]

                # Generic pair detection: any 2-item sequence is treated as (left, right)
                is_pair = isinstance(raw, (tuple, list, np.ndarray)) and len(raw) == 2

                if is_pair:
                    # Left channel
                    v_left = raw[0]
                    if v_left is None:
                        v_left = np.nan
                    else:
                        v_left = float(v_left)
                        if abs(v_left) < _tol.EPS_L:
                            v_left = 0.0

                    # Right channel
                    v_right = raw[1]
                    if v_right is None:
                        v_right = np.nan
                    else:
                        v_right = float(v_right)
                        if abs(v_right) < _tol.EPS_L:
                            v_right = 0.0

                    data_series[key].append(v_left)
                    data_series_right[key].append(v_right)

                else:
                    # Legacy scalar path (left only)
                    v = raw
                    if v is None:
                        v = np.nan
                    else:
                        v = float(v)
                        if abs(v) < _tol.EPS_L:
                            v = 0.0
                
                    data_series[key].append(v)
                    data_series_right[key].append(np.nan)
 

        # -------------------------------------------------------------------------
        # 2) Build one subplot per key
        # -------------------------------------------------------------------------
        num_keys = len(keys_to_plot)
        fig, axes = plt.subplots(num_keys, 1, figsize=(10, 2.2 * num_keys), sharex=True)
        fig.suptitle(str(title), fontsize=14, fontweight="bold", y=0.995)
        if num_keys == 1:
            axes = [axes]

        colors = plt.cm.viridis(np.linspace(0, 0.9, num_keys))

        # Console report header
        #print("\n=== PROPERTIES MIN/MAX REPORT ===")
        #print(f"z range: [{z_start:.6f}, {z_end:.6f}] | sampled points: {num_points}")

        for i, (key, color) in enumerate(zip(keys_to_plot, colors)):
            ax = axes[i]

            # Left channel data and finite mask
            y_left = np.asarray(data_series[key], dtype=float)
            finite_left = np.isfinite(y_left)

            # Right channel data and finite mask
            y_right = np.asarray(data_series_right[key], dtype=float)
            finite_right = np.isfinite(y_right)
            has_right = bool(np.any(finite_right))

            # Extract right-channel endpoint values (used for left top text: t(z0), t(z1))
            t_start_txt = None
            t_end_txt = None
            if has_right:
                ax_r = ax.twinx()
                ax_r.plot(z_values, y_right, linestyle="--", linewidth=1.5)
                ax_r.set_ylabel("thickness t", fontweight="bold")
                ax_r.grid(False)

                # Console min/max for right channel
                y_rf = y_right[finite_right]
                z_rf = z_values[finite_right]
                i_min_r = int(np.argmin(y_rf))
                i_max_r = int(np.argmax(y_rf))
                v_min_r = float(y_rf[i_min_r])
                v_max_r = float(y_rf[i_max_r])
                z_min_r = float(z_rf[i_min_r])
                z_max_r = float(z_rf[i_max_r])
                '''
                print(
                    f"{key} [right]: min={v_min_r:.12g} at z={z_min_r:.12g} | "
                    f"max={v_max_r:.12g} at z={z_max_r:.12g}"
                )
                '''

            # ---------------------------------------------------------------------
            # Case A: no valid left data
            # ---------------------------------------------------------------------
            if y_left.size == 0 or not np.any(finite_left):
                ax.plot(z_values, y_left, color=color, linewidth=2)
                ax.set_ylabel(key, fontweight="bold")
                ax.grid(True, linestyle=":", alpha=0.6)

                # Right-top text: status only (kept on the right)
                title_right = f"{key}: no valid left-axis data"
                ax.text(
                    0.995, 1.01, title_right,
                    transform=ax.transAxes,
                    ha="right", va="bottom",
                    fontsize=9,
                    clip_on=False
                )

                # Left-top text: t endpoints only
                if t_start_txt is not None and t_end_txt is not None:
                    title_left_t = f"t(z0)={t_start_txt:.6g}  t(z1)={t_end_txt:.6g}"
                    ax.text(
                        0.005, 1.01, title_left_t,
                        transform=ax.transAxes,
                        ha="left", va="bottom",
                        fontsize=9,
                        clip_on=False,
                        wrap=True,
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.2)
                    )

                print(f"{key}: no valid left-axis data")

                # Plot right channel if present
                if has_right:
                    ax_r = ax.twinx()
                    ax_r.plot(z_values, y_right, linestyle="--", linewidth=1.5)
                    #ax_r.set_ylabel(f"{key} (right)", fontweight="bold")
                    ax_r.grid(False)

                    # Console min/max for right channel
                    y_rf = y_right[finite_right]
                    z_rf = z_values[finite_right]
                    i_min_r = int(np.argmin(y_rf))
                    i_max_r = int(np.argmax(y_rf))
                    v_min_r = float(y_rf[i_min_r])
                    v_max_r = float(y_rf[i_max_r])
                    z_min_r = float(z_rf[i_min_r])
                    z_max_r = float(z_rf[i_max_r])
                    '''
                    print(
                        f"{key} [right]: min={v_min_r:.12g} at z={z_min_r:.12g} | "
                        f"max={v_max_r:.12g} at z={z_max_r:.12g}"
                    )
                    '''
                continue

            # ---------------------------------------------------------------------
            # Case B: valid left data
            # ---------------------------------------------------------------------
            y_lf = y_left[finite_left]
            z_lf = z_values[finite_left]

            i_min_l = int(np.argmin(y_lf))
            i_max_l = int(np.argmax(y_lf))

            v_min_l = float(y_lf[i_min_l])
            v_max_l = float(y_lf[i_max_l])
            z_min_l = float(z_lf[i_min_l])
            z_max_l = float(z_lf[i_max_l])

            # Plot left curve
            ax.plot(z_values, y_left, color=color, linewidth=2)

            # Mark min/max on left channel
            ax.scatter([z_min_l], [v_min_l], marker="v", s=26, zorder=3)
            ax.scatter([z_max_l], [v_max_l], marker="^", s=26, zorder=3)

            # Annotate left min/max values near markers
            if np.isclose(v_min_l, v_max_l):
                ax.annotate(
                    f"{v_min_l:.4g}",
                    (z_min_l, v_min_l),
                    textcoords="offset points",
                    xytext=(4, 6),
                    fontsize=7,
                )
            else:
                ax.annotate(
                    f"{v_min_l:.4g}",
                    (z_min_l, v_min_l),
                    textcoords="offset points",
                    xytext=(4, -12),
                    fontsize=7,
                )
                ax.annotate(
                    f"{v_max_l:.4g}",
                    (z_max_l, v_max_l),
                    textcoords="offset points",
                    xytext=(4, 6),
                    fontsize=7,
                )

            # Left y-axis limits with margin
            if v_max_l != v_min_l:
                margin_l = (v_max_l - v_min_l) * 0.10
            else:
                margin_l = max(abs(v_max_l) * 0.05, 0.1)
            ax.set_ylim(v_min_l - margin_l, v_max_l + margin_l)

            ax.set_ylabel(key, fontweight="bold")
            ax.grid(True, linestyle=":", alpha=0.6)

            # Right-top text: min/max summary (unchanged side)
            title_right = (
                f"{key}: min={v_min_l:.6g}@z={z_min_l:.6g}  max={v_max_l:.6g}@z={z_max_l:.6g}"
            )
            ax.text(
                0.995, 1.01, title_right,
                transform=ax.transAxes,
                ha="right", va="bottom",
                fontsize=9,
                clip_on=False
            )

            # Left-top text: only t(z0), t(z1)
            if t_start_txt is not None and t_end_txt is not None:
                title_left_t = f"t(z0)={t_start_txt:.6g}  t(z1)={t_end_txt:.6g}"
                ax.text(
                    0.0015, 1.01, title_left_t,
                    transform=ax.transAxes,
                    ha="left", va="bottom",
                    fontsize=9,
                    clip_on=False,
                    wrap=True,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.2)
                )
                            # Console min/max for left channel
            print(
                f"{key}: min={v_min_l:.12g} at z={z_min_l:.12g} | "
                f"max={v_max_l:.12g} at z={z_max_l:.12g}"
            )

            # Plot right channel if present
            if has_right:
                ax_r = ax.twinx()
                ax_r.plot(z_values, y_right, linestyle="--", linewidth=1.5)
                #ax_r.set_ylabel(f"{key} (right)", fontweight="bold")
                ax_r.grid(False)

                # Console min/max for right channel
                y_rf = y_right[finite_right]
                z_rf = z_values[finite_right]

                i_min_r = int(np.argmin(y_rf))
                i_max_r = int(np.argmax(y_rf))

                v_min_r = float(y_rf[i_min_r])
                v_max_r = float(y_rf[i_max_r])
                z_min_r = float(z_rf[i_min_r])
                z_max_r = float(z_rf[i_max_r])
                '''
                print(
                    f"{key} [right]: min={v_min_r:.12g} at z={z_min_r:.12g} | "
                    f"max={v_max_r:.12g} at z={z_max_r:.12g}"
                )
                '''

        #print("=== END PROPERTIES MIN/MAX REPORT ===\n")

        axes[-1].set_xlabel(f"Z coordinate")


        # Reserve top margin for:
        # - centered figure title (suptitle)
        # - top-left / top-right per-axis summary texts
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        #plt.show()


    def plot_section_2d(
        self,
        z: float,
        show_ids: bool = True,
        show_weights: bool = True,
        show_vertex_ids: bool = False,
        show_legenda: bool= False,
        title: Optional[str] = None,
        ax=None,
        
    ):
        """
        Draw the 2D section at a given longitudinal coordinate z.

        This implementation places the legend BELOW the plot and computes layout
        dynamically from real rendered sizes (no fixed "magic" vertical offsets).

        Why this version is robust
        --------------------------
        - Legend is anchored in FIGURE coordinates, not AXES coordinates.
        - After first draw, legend height is measured from renderer bbox.
        - Bottom subplot margin is then adjusted to reserve exactly enough space.
        - Legend is finally repositioned inside that reserved strip.

        Result:
        - No overlap between legend and axes.
        - No clipping/cut-off of legend text.
        - Works with different font sizes, DPI, and label lengths.
        """
        #print(f"DEBUG plot_section_2d {show_vertex_ids} show_ids {show_ids} ")
        # Local imports keep the method self-contained as a drop-in replacement.
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.legend_handler import HandlerTuple

        sec = self.field.section(z)

        created_new_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            created_new_fig = True
        else:
            fig = ax.figure

        # Store one color per section polygon (same order as sec.polygons).
        poly_colors = []

        # -------------------------------------------------------------------------
        # 1) Plot polygon outlines
        # -------------------------------------------------------------------------
        for idx, poly in enumerate(sec.polygons):
            xs = [p.x for p in poly.vertices]
            ys = [p.y for p in poly.vertices]

            # Close polyline only if needed.
            if len(poly.vertices) >= 2:
                x0, y0 = poly.vertices[0].x, poly.vertices[0].y
                xN, yN = poly.vertices[-1].x, poly.vertices[-1].y
                if (x0, y0) != (xN, yN):
                    xs.append(x0)
                    ys.append(y0)

            line, = ax.plot(xs, ys, linewidth=1, zorder=2)
            color = line.get_color()
            poly_colors.append(color)

            # Optional vertex numbering inside axes.
            if show_vertex_ids:
                for v_idx, v in enumerate(poly.vertices, start=0):
                    ax.text(
                        v.x,
                        v.y,
                        f" {v_idx}",
                        color=color,
                        fontsize=9,
                        fontweight="bold",
                        zorder=4,
                    )
            # Optional polygon id inside axes (placed at simple vertex-mean center)
            if show_ids and len(poly.vertices) > 0:
                cx = sum(p.x for p in poly.vertices) / float(len(poly.vertices))
                cy = sum(p.y for p in poly.vertices) / float(len(poly.vertices))
                ax.text(
                    cx,
                    cy,
                    f"ID={idx}",
                    color=color,
                    fontsize=10,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    zorder=5,
                )


        # -------------------------------------------------------------------------
        # 2) Compute container mapping (S0-aware, then remapped to current section)
        # -------------------------------------------------------------------------

        children_map = self.field.build_direct_children_map(z)

        parent_of = {}
        for parent_idx, child_idx_list in children_map.items():
            for child_idx in child_idx_list:
                parent_of[child_idx] = parent_idx

        container_id_by_sec = []
        for idx in range(len(sec.polygons)):
            if idx in parent_of:
                container_id_by_sec.append(parent_of[idx])
            else:
                container_id_by_sec.append(None)


        # -------------------------------------------------------------------------
        # 3) Reconstruct absolute weights at z from relative weights + container chain
        # -------------------------------------------------------------------------
        w_rel_z = [float(getattr(p, "weight", 0.0)) for p in sec.polygons]
        w_abs_z_cache = {}

        def _w_abs_z(i: int) -> float:
            if i in w_abs_z_cache:
                return w_abs_z_cache[i]
            parent = container_id_by_sec[i]
            if parent is None:
                w_abs_z_cache[i] = w_rel_z[i]
            else:
                w_abs_z_cache[i] = w_rel_z[i] + _w_abs_z(parent)
            return w_abs_z_cache[i]

        w_abs_z = [_w_abs_z(i) for i in range(len(sec.polygons))]
        _ = w_abs_z  # currently used by optional legend blocks only
        legend_handles = []
        legend_labels = []
        show_legenda=True
        if show_legenda and len(sec.polygons) < 20:
            # -------------------------------------------------------------------------
            # 4) Build legend entries (relative weights + container id)
            # -------------------------------------------------------------------------
            for idx, poly in enumerate(sec.polygons):
                container_id = container_id_by_sec[idx]

                # Child handle
                h_poly = Line2D([0], [0], color=poly_colors[idx], linewidth=5.0)

                # If container exists, legend handle is a tuple (child, container)
                if container_id is not None and 0 <= container_id < len(poly_colors):
                    h_container = Line2D([0], [0], color=poly_colors[container_id], linewidth=5.0)
                    legend_handles.append((h_poly, h_container))
                else:
                    legend_handles.append(h_poly)

                name = (getattr(poly, "name", None) or f"poly_{idx}").strip()

                label = (
                    f"ID={idx}  "
                    f"w={w_rel_z[idx]:g}  "
                    f"{name}  "
                    f"container={container_id if container_id is not None else 'None'}"
                )
                #print(f"DEBUG legend_label={repr(label)}")
                legend_labels.append(label)

        # -------------------------------------------------------------------------
        # 5) Axes style
        # -------------------------------------------------------------------------
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, linestyle=":", alpha=0.5, zorder=1)

        if title is None:
            title = f"Section at z={z:g}"
        ax.set_title(title)


        if ax is None:
            fig, ax = plt.subplots(constrained_layout=True)
            created_new_fig = True
        else:
            fig = ax.figure
            try:
                fig.set_constrained_layout(True)
            except Exception:
                pass


        # -------------------------------------------------------------------------
        # 6) Legend below axes (axes-anchored, no overlap with X label)
        # -------------------------------------------------------------------------
        leg = ax.legend(
            legend_handles,
            legend_labels,
            loc="upper center",                 # top-center of legend box
            bbox_to_anchor=(0.5, -0.16),        # place below axes
            bbox_transform=ax.transAxes,        # anchor in AXES coordinates
            borderaxespad=0.0,
            frameon=True,
            title="Polygons",
            handler_map={tuple: HandlerTuple(ndivide=None)},
            ncol=1,
        )

        # -------------------------------------------------------------------------
        # 7) Final draw (no manual subplots_adjust needed)
        # -------------------------------------------------------------------------
        fig.canvas.draw()

        return ax


    def plot_volume_3d(
        self,
        show_end_sections: bool = True,
        line_percent: float = 100.0,
        seed: int | str = 0,
        title: str = "Ruled volume (vertex-connection lines)",
        ax=None,
        equalize_z: bool = False,
    ):
        """
        Draw the 3D ruled "skeleton":
        - endpoint section outlines (optional)
        - straight lines connecting corresponding vertices (ruled generators)
        - ability to display only a percentage of those lines for readability

        Parameters
        ----------
        equalize_z : bool, default False
            If True, the visual box is proportional to the real data ranges
            (1 unit along Z = 1 unit along X/Y).  Achieved by passing the
            actual data ranges to ``set_box_aspect`` — no coordinates or
            axis limits are modified.  When False the plot is identical to
            the original.
        """
        thickness_line = 10
        resolution = 100
        end_factor = 1
        # alpha controls line transparency: 1.0 = fully opaque, 0.0 = fully transparent.
        alpha = 0.8
        #print(f"DEBUG plot_volume_3d :<{seed}>")
        

        if isinstance(seed, str):
            seed_str = seed.strip()
            seed_lower = seed_str.lower()

            if seed_lower == "w":
                # seed="w"  -> mode="w", resolution unchanged (default 100)
                mode = "w"
                weight_attr = "weightabs"
                seed_numeric = 1

            elif seed_lower.startswith("w") and seed_lower[1:].isdigit():
                # seed="w100", "w500", "w10000"  -> mode="w", resolution=number after w
                mode = "w"
                resolution = int(seed_lower[1:])
                weight_attr = "weightabs"
                seed_numeric = 1
            elif seed_lower == "s":
                mode = "s"
                weight_attr = "shear_weightabs"
                seed_numeric = 1
            elif seed_lower.startswith("s") and seed_lower[1:].isdigit():
                mode = "s"
                weight_attr = "shear_weightabs"
                resolution = int(seed_lower[1:])
                seed_numeric = 1                
            else:
                raise ValueError(
                    f"Unknown plot_volume_3d string mode: {seed!r}. "
                    f"Allowed formats: 'w'  or  'wN' where N is an integer (e.g. 'w100', 'w10000')."
                )

        else:
            # seed is numeric -> classic mode, color by polygon
            resolution=1
            mode = None
            seed_numeric = int(seed)


        def _line_width_for_polygon(poly, base_lw, factor=1.8):
            if len(poly.vertices) < 5:
                return base_lw * factor
            return base_lw        
        def _thickness_line_from_section_points(
            section,
            min_thickness=0.15,
            max_thickness=1.5,
            ref_points=20,
            exponent=0.5,
        ):
            """
            Compute line thickness from the total number of points in a section.

            More points -> thinner line.
            Fewer points -> thicker line.

            Parameters
            ----------
            section : Section
                Section object containing polygons.
            min_thickness : float
                Lower clamp for the line thickness.
            max_thickness : float
                Upper clamp for the line thickness.
            ref_points : int
                Reference number of points for max_thickness scaling.
            exponent : float
                Controls how fast thickness decreases as point count grows.
            """
            total_points = sum(len(poly.vertices) for poly in section.polygons)

            if total_points <= 0:
                return max_thickness

            thickness = max_thickness * (ref_points / total_points) ** exponent
            return max(min_thickness, min(thickness, max_thickness))

        def _auto_resolution_for_polygon(
            z_planes,
            weights,
            min_resolution=2,
            max_resolution=resolution,
            slope_tol=1.0,
            n=2.0,
        ):
            z_values = []
            values = []

            # Keep only numeric samples.
            # weights[i] is associated with the slice starting at z_planes[i].
            for z, w in zip(z_planes[:-1], weights):
                w_float = _to_float_or_none(w)
                if w_float is not None:
                    z_values.append(float(z))
                    values.append(w_float)

            if len(values) < 2:
                return min_resolution

            max_slope = 0.0

            # Use the maximum slope among all consecutive portions.
            for i in range(len(values) - 1):
                dz = z_values[i + 1] - z_values[i]
                if abs(dz) <= _tol.EPS_L:
                    continue

                slope = abs((values[i + 1] - values[i]) / dz)
                if slope > max_slope:
                    max_slope = slope

            # Zero slope gives the minimum resolution.
            if max_slope <= _tol.EPS_L:
                return min_resolution

            # Convert the maximum slope to a normalized percentage.
            # Here slope_tol is the slope corresponding to 100%.
            slope_percent = 100.0 * max_slope / slope_tol

            # Rule:
            # - if the maximum slope percentage is above 10%, use n * max_resolution
            # - otherwise use max_resolution
            if slope_percent > 10.0:
                resolution_local = int(np.ceil(n * max_resolution))
            else:
                resolution_local = max_resolution

            return resolution_local

        def _add_generator_segment(v0, v1, z_a, z_b, thickness_line, segment_color) -> None:

            # Interpolate the segment endpoints for the current z-slice.
            x_a, y_a, z_a_draw = _interpolate_vertex(v0, v1, z_a)
            x_b, y_b, z_b_draw = _interpolate_vertex(v0, v1, z_b)

            # Draw the 3D line segment.
            _add_edge(
                x_a,
                y_a,
                z_a_draw,
                x_b,
                y_b,
                z_b_draw,
                thickness_line,
                segment_color,
            )

        # ------------------------------------------------------------------
        # Axes initialization
        # ------------------------------------------------------------------
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
            ax.view_init(elev=15, azim=120)

        # ------------------------------------------------------------------
        # Geometry extraction
        # ------------------------------------------------------------------
        z0, z1 = self.field.z0, self.field.z1
        s0 = self.field.section(z0)
        s1 = self.field.section(z1)
        thickness_line = _thickness_line_from_section_points(s0)

        _rng = _random.Random(seed_numeric)
        cycle_colors = [
            (0.121, 0.466, 0.705),
            (1.000, 0.498, 0.054),
            (0.172, 0.627, 0.172),
            (0.839, 0.153, 0.157),
            (0.580, 0.404, 0.741),
            (0.549, 0.337, 0.294),
            (0.890, 0.467, 0.761),
            (0.498, 0.498, 0.498),
            (0.737, 0.741, 0.133),
            (0.090, 0.745, 0.811),
        ]
        _rng.shuffle(cycle_colors)
        n_colors = len(cycle_colors)
        color_counter = 0

        # ------------------------------------------------------------------
        # Edge batch accumulator
        # ------------------------------------------------------------------
        edges_by_style: dict[tuple, dict] = defaultdict(
            lambda: {"x": [], "y": [], "z": []}
        )

        def _add_edge(x0, y0, z0_, x1, y1, z1_, lw: float, color) -> None:
            # Color can be a hex string or an RGB/RGBA tuple — both are hashable.
            key = (lw, color)
            buf = edges_by_style[key]
            buf["x"].extend((x0, x1, float("nan")))
            buf["y"].extend((y0, y1, float("nan")))
            buf["z"].extend((z0_, z1_, float("nan")))

        def _add_polygon_boundary(vertices_xyz, lw: float, color) -> None:
            n = len(vertices_xyz)
            for i in range(n):
                j = (i + 1) % n
                p, q = vertices_xyz[i], vertices_xyz[j]
                _add_edge(p[0], p[1], p[2], q[0], q[1], q[2], lw, color)

        def _interpolate_vertex(v0, v1, z_value):
            # Generator lines are straight in 3D, so x and y are interpolated
            # linearly between the endpoint sections.
            if z1 == z0:
                return v0.x, v0.y, z_value

            t = (z_value - z0) / (z1 - z0)
            x = v0.x + t * (v1.x - v0.x)
            y = v0.y + t * (v1.y - v0.y)
            return x, y, z_value

        def _to_float_or_none(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def _normalize_weight(weight_value, weight_min, weight_max):
            value = _to_float_or_none(weight_value)
            if value is None:
                return 0.5
            if weight_max <= weight_min:
                return 1.0
            return max(0.0, min((value - weight_min) / (weight_max - weight_min), 1.0))

        def _get_semantic_color(base_color, weight_value, weight_min, weight_max, mode_name):
            ratio = _normalize_weight(weight_value, weight_min, weight_max)
            
            if abs(weight_max - weight_min) <= _tol.EPS_L:
                if abs(weight_max) <= _tol.EPS_L:
                    return (0.5, 0.5, 0.5, 0.9)   # void 
                else:
                    return (0.30, 0.30, 0.30, 1.0)    # constant non-void -> black

            if mode_name == "gray":
                return (ratio, ratio, ratio)

            if weight_value < 0:
                ratio = 1.0 - ratio

            if mode_name == "s":
                color_min = (0.0, 0.45, 0.0)  # green
                color_max = (1.0, 0.55, 0.0)  # orange
            else:
                color_min = (0.0, 0.0, 1.0)  # blue
                color_max = (1.0, 0.0, 0.0)  # red

            r = color_min[0] + ratio * (color_max[0] - color_min[0])
            g = color_min[1] + ratio * (color_max[1] - color_min[1])
            b = color_min[2] + ratio * (color_max[2] - color_min[2])
            
            return (r, g, b, alpha)

        # ------------------------------------------------------------------
        # End sections
        # ------------------------------------------------------------------
        if show_end_sections:
            for sec in (s0, s1):
                for poly in sec.polygons:
                    verts = poly.vertices
                    pts = [(v.x, v.y, sec.z) for v in verts]
                    color = cycle_colors[color_counter % n_colors]
                    _add_polygon_boundary(pts, lw=1.0, color=color)
                    color_counter += 1

        # ------------------------------------------------------------------
        # Build generator lines grouped by polygon.
        # ------------------------------------------------------------------
        lines_by_polygon: list[list[tuple]] = []
        polygon_base_colors: list[tuple] = []

        for poly_idx, (p0, p1) in enumerate(zip(s0.polygons, s1.polygons)):
            poly_lines = []
            for v0, v1 in zip(p0.vertices, p1.vertices):
                poly_lines.append((v0, v1))

            lines_by_polygon.append(poly_lines)
            polygon_base_colors.append(cycle_colors[(color_counter + poly_idx) % n_colors])

        # ------------------------------------------------------------------
        # Prepare the selected lines grouped by polygon.
        # ------------------------------------------------------------------
        selected_lines_by_polygon: list[list[tuple]] = [
            list(poly_lines) for poly_lines in lines_by_polygon
        ]

        # ------------------------------------------------------------------
        # Subsampling
        # ------------------------------------------------------------------
        total_lines = sum(len(poly_lines) for poly_lines in lines_by_polygon)

        if line_percent < 100.0 and total_lines > 0:
            k_total = max(
                0,
                min(int(math.ceil(total_lines * line_percent / 100.0)), total_lines),
            )

            selected_lines_by_polygon = [[] for _ in lines_by_polygon]
            eligible_polygon_indices: list[int] = []
            eligible_counts: list[int] = []

            for poly_idx, poly_lines in enumerate(lines_by_polygon):
                n = len(poly_lines)
                if n < 2:
                    selected_lines_by_polygon[poly_idx].extend(poly_lines)
                else:
                    eligible_polygon_indices.append(poly_idx)
                    eligible_counts.append(n)

            forced_count = sum(len(poly_lines) for poly_lines in selected_lines_by_polygon)
            remaining_quota = max(0, k_total - forced_count)
            eligible_total = sum(eligible_counts)

            if eligible_total > 0 and remaining_quota > 0:
                raw_quotas = [
                    (count * remaining_quota) / eligible_total
                    for count in eligible_counts
                ]
                keep_counts = [int(math.floor(q)) for q in raw_quotas]
                remaining = remaining_quota - sum(keep_counts)
                order = sorted(
                    range(len(eligible_polygon_indices)),
                    key=lambda i: raw_quotas[i] - keep_counts[i],
                    reverse=True,
                )
                for i in order[:remaining]:
                    keep_counts[i] += 1

                for local_idx, keep in enumerate(keep_counts):
                    poly_idx = eligible_polygon_indices[local_idx]
                    poly_lines = lines_by_polygon[poly_idx]
                    n = len(poly_lines)

                    if keep <= 0:
                        continue
                    if keep >= n:
                        selected_lines_by_polygon[poly_idx].extend(poly_lines)
                        continue

                    indices = [int(math.floor(j * n / keep)) for j in range(keep)]
                    for idx in indices:
                        selected_lines_by_polygon[poly_idx].append(poly_lines[idx])

        # ------------------------------------------------------------------
        # Build the z slices used to draw the generator lines.
        # ------------------------------------------------------------------
        '''
        if z1 == z0 or resolution <= 1:
            z_planes = [z0, z1]
        else:
        '''    
        dz = (z1 - z0) / resolution
        z_planes = [z0 + i * dz for i in range(resolution)]
        z_planes.append(z1)

        # ------------------------------------------------------------------
        # Precompute semantic weights per polygon and per slice.
        # ------------------------------------------------------------------
        section_cache = {}
        z_planes_by_polygon: list[list[float]] = [[] for _ in selected_lines_by_polygon]
        weights_by_polygon: list[list] = [[] for _ in selected_lines_by_polygon]
        weight_range_by_polygon: list[tuple[float, float]] = [
            (0.0, 0.0) for _ in selected_lines_by_polygon
        ]

        global_numeric_weights = []
        global_weight_min = 0.0
        global_weight_max = 0.0

        
        if mode is not None and len(z_planes) > 2:
            for slice_idx in range(len(z_planes) - 1):
                z_a = z_planes[slice_idx]
                if z_a not in section_cache:
                    section_cache[z_a] = self.field.section(z_a)

            for poly_idx, poly_lines in enumerate(selected_lines_by_polygon):

                '''
                if z1 == z0 or resolution <= 1:
                    z_planes_probe = [z0, z1]
                else:
                    dz_probe = (z1 - z0) / resolution
                    z_planes_probe = [z0 + i * dz_probe for i in range(resolution)]
                    z_planes_probe.append(z1)
                '''
                #poly_weights_probe = []
                poly_numeric_weights = []
                '''
                for slice_idx in range(len(z_planes_probe) - 1):
                    z_a = z_planes_probe[slice_idx]
                    if z_a not in section_cache:
                        section_cache[z_a] = self.field.section(z_a)

                    poly_weight = getattr(section_cache[z_a].polygons[poly_idx], "weight", None)
                    poly_weights_probe.append(poly_weight)

                    poly_weight_float = _to_float_or_none(poly_weight)
                    if poly_weight_float is not None:
                        poly_numeric_weights.append(poly_weight_float)
                '''
                resolution_local = resolution#_auto_resolution_for_polygon(z_planes_probe, poly_weights_probe)
                dz_local = (z1 - z0) / resolution_local
                z_planes_local = [z0 + i * dz_local for i in range(resolution_local)]
                z_planes_local.append(z1)

                z_planes_by_polygon[poly_idx] = z_planes_local

                poly_weights = []
                
                for slice_idx in range(len(z_planes_local) - 1):
                    z_a = z_planes_local[slice_idx]
                    if z_a not in section_cache:
                        section_cache[z_a] = self.field.section(z_a)

                    #poly_weight = getattr(section_cache[z_a].polygons[poly_idx], "weight", None)
                    #poly_weight = getattr(section_cache[z_a].polygons[poly_idx], "weightabs", None) 
                    poly_weight = getattr(section_cache[z_a].polygons[poly_idx], weight_attr, None)
                    #poly_weight = getattr(section_cache[z_a].polygons[poly_idx], "shear_weightabs", None) 
                    #
                    
                    #poly_name_debug =getattr(section_cache[z_a].polygons[poly_idx], "name", None)
                    #print(f"DEBUG poly_weight: {poly_weight} poly_name_debug: {poly_name_debug}")
                    poly_weights.append(poly_weight)
                    

                    poly_weight_float = _to_float_or_none(poly_weight)
                    if poly_weight_float is not None:
                        global_numeric_weights.append(poly_weight_float)
                        poly_numeric_weights.append(poly_weight_float)                    
                
                weights_by_polygon[poly_idx] = poly_weights

                if poly_numeric_weights:
                    weight_range_by_polygon[poly_idx] = (
                        min(poly_numeric_weights),
                        max(poly_numeric_weights),
                    )
                else:
                    weight_range_by_polygon[poly_idx] = (0.0, 0.0)
            if global_numeric_weights:
                global_weight_min = min(global_numeric_weights)
                global_weight_max = max(global_numeric_weights)
        # ------------------------------------------------------------------
        # Accumulate generator segments slice-by-slice and polygon-by-polygon.
        # ------------------------------------------------------------------

        
        if mode is None or len(z_planes) <= 2:

            for slice_idx in range(len(z_planes) - 1):
                z_a = z_planes[slice_idx]
                z_b = z_planes[slice_idx + 1]

                for poly_idx, poly_lines in enumerate(selected_lines_by_polygon):
                    if not poly_lines:
                        continue

                    base_color = polygon_base_colors[poly_idx]
                    segment_color = base_color

                    for v0, v1 in poly_lines:
                        _add_generator_segment(
                            v0,
                            v1,
                            z_a,
                            z_b,
                            thickness_line,
                            segment_color,
                        )
        else:
            max_slices = max(
                (len(zp) - 1 for zp in z_planes_by_polygon if zp),
                default=0,
            )

            for slice_idx in range(max_slices):
                for poly_idx, poly_lines in enumerate(selected_lines_by_polygon):
                    if not poly_lines:
                        continue

                    z_planes_local = z_planes_by_polygon[poly_idx]
                    if slice_idx >= len(z_planes_local) - 1:
                        continue
                    if slice_idx >= len(weights_by_polygon[poly_idx]):
                        continue

                    z_a = z_planes_local[slice_idx]
                    z_b = z_planes_local[slice_idx + 1]
                    '''
                    base_color = polygon_base_colors[poly_idx]
                    poly_weight = weights_by_polygon[poly_idx][slice_idx]
                    poly_weight_min = global_weight_min
                    poly_weight_max = global_weight_max                    
                    
                    
                    segment_color = _get_semantic_color(
                        base_color=base_color,
                        weight_value=poly_weight,
                        weight_min=global_weight_min,
                        weight_max=global_weight_max,
                        mode_name=mode,
                    )
                    '''
                    base_color = polygon_base_colors[poly_idx]
                    poly_weight = weights_by_polygon[poly_idx][slice_idx]
                    poly_weight_min, poly_weight_max = weight_range_by_polygon[poly_idx]

                    segment_color = _get_semantic_color(
                        base_color=base_color,
                        weight_value=poly_weight,
                        weight_min=poly_weight_min,
                        weight_max=poly_weight_max,
                        mode_name=mode,
                    )                    
                    
                    for v0, v1 in poly_lines:
                        _add_generator_segment(
                            v0,
                            v1,
                            z_a,
                            z_b,
                            thickness_line,
                            segment_color,
                        )
        # ------------------------------------------------------------------
        # Render phase — one ax.plot per (lw, color) bucket
        # ------------------------------------------------------------------
        for (lw, color), buf in edges_by_style.items():
            if buf["x"]:
                ax.plot(buf["x"], buf["y"], buf["z"], lw=lw, color=color)

        if mode is not None:

            if mode == "s":
                cmap = LinearSegmentedColormap.from_list(
                    "shear_green_orange",
                    [(0.0, 0.45, 0.0), (1.0, 0.55, 0.0)],
                )
            else:
                cmap = LinearSegmentedColormap.from_list(
                    "weight_blue_red",
                    [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0)],
                )

            if global_weight_min == global_weight_max:
                global_weight_min -= 0.5
                global_weight_max += 0.5

            norm = Normalize(vmin=global_weight_min, vmax=global_weight_max)
            sm = ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])

            cbar = ax.figure.colorbar(sm, ax=ax, pad=0.12, shrink=0.75)
            cbar.set_label("weight" if mode == "w" else "shear weight")


            ticks = np.linspace(global_weight_min, global_weight_max, 10)

            cbar.set_ticks(ticks)
            cbar.set_ticklabels([f"{v:.4g}" for v in ticks])


        # ------------------------------------------------------------------
        # Explicit limits
        # ------------------------------------------------------------------
        all_verts = [
            v for sec in (s0, s1) for poly in sec.polygons for v in poly.vertices
        ]
        xs = [v.x for v in all_verts]
        ys = [v.y for v in all_verts]
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(ys), max(ys))
        ax.set_zlim(z0, z1)

        # ------------------------------------------------------------------
        # Labels and title
        # ------------------------------------------------------------------
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)

        # ------------------------------------------------------------------
        # Axis scaling
        # ------------------------------------------------------------------
        if equalize_z:
            x_range = max(max(xs) - min(xs), 1e-12)
            y_range = max(max(ys) - min(ys), 1e-12)
            z_range = max(abs(z1 - z0), 1e-12)
            ax.set_box_aspect((x_range, y_range, z_range))
        else:
            _set_axes_equal_3d(ax)
        return ax

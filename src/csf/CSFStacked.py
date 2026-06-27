from __future__ import annotations
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np
import random
from typing import List, Sequence, Tuple, Optional
from .entities import Pt, Polygon, Section
from typing import Tuple
from .section_field import (
    Pt,
    Polygon,
    Section,

    section_full_analysis,
)
from .visualizer import Visualizer
from .continuous_section_field import ContinuousSectionField

@dataclass(frozen=True)
class SegmentSpec:
    """
    Generic input specification for one stacked segment.

    Attributes:
    - tag: segment identifier
    - z0, z1: global z-interval for the segment
    - polygons_s0: tuple of polygons at z0
    - polygons_s1: tuple of polygons at z1

    Notes:
    - Polygon names should be consistent between z0 and z1 for side-surface pairing.
    - For each polygon name, vertex count must match between z0 and z1.
    """
    tag: str
    z0: float
    z1: float
    polygons_s0: Tuple[Polygon, ...]
    polygons_s1: Tuple[Polygon, ...]


@dataclass
class StackSegment:
    """Runtime segment container: interval + CSF field."""
    tag: str
    z_start: float
    z_end: float
    field: ContinuousSectionField


class CSFStacked:
    """
    CSFStacked stacked container for multiple ContinuousSectionField objects.

    Design goals:
    - CSFStacked geometry (any number of polygons per section)
    - Global z dispatch
    - Internal junction sections excluded by definition
    - Explicit validation and clear errors
    """

    def __init__(self, eps_z: float = 1e-10):
        self.eps_z = float(eps_z)
        self.segments: List[StackSegment] = []

    def append(self, field: ContinuousSectionField) -> None:
        """
        Append one pre-built ContinuousSectionField to the stack.
        ...
        """
        try:
            new_z_start = float(field.s0.z)
            new_z_end = float(field.s1.z)
        except Exception as e:
            raise RuntimeError(
                f"CSFStacked.append failed while reading incoming field bounds: {e}"
            ) from e

        if new_z_end <= new_z_start:
            raise ValueError(
                f"Invalid field bounds: z_end ({new_z_end}) must be > z_start ({new_z_start})."
            )

        if self.segments:
            previous_segment = self.segments[-1]
            previous_z_end = float(previous_segment.z_end)
            z_gap = new_z_start - previous_z_end

            if z_gap < -self.eps_z:
                raise ValueError(
                    "Non-contiguous stack append: overlap or wrong order detected. "
                    f"Previous segment '{previous_segment.tag}' ends at z={previous_z_end}, "
                    f"new segment starts at z={new_z_start}, eps_z={self.eps_z}."
                )

            if z_gap > self.eps_z:
                raise ValueError(
                    "Non-contiguous stack append: gap detected. "
                    f"Previous segment '{previous_segment.tag}' ends at z={previous_z_end}, "
                    f"new segment starts at z={new_z_start}, gap={z_gap}, eps_z={self.eps_z}."
                )

        new_segment = StackSegment(
            tag=f"seg_{len(self.segments)}",
            z_start=new_z_start,
            z_end=new_z_end,
            field=field,
        )
        self.segments.append(new_segment)


    def append2(self, field: ContinuousSectionField) -> None:
        """
        Append one pre-built ContinuousSectionField to the stack.

        Stacking contract (strict, no hidden reordering):
        - The new segment must have valid local bounds (z_end > z_start).
        - If the stack is not empty, the new segment must start exactly after the
          previous segment, within ``self.eps_z`` tolerance.
        - Gaps and overlaps are rejected immediately at append time.

        Notes
        -----
        This method does not sort segments. The user-provided order is the stack order.
        """
        new_z_start = float(field.s0.z)
        new_z_end = float(field.s1.z)

        if new_z_end <= new_z_start:
            raise ValueError(
                f"Invalid field bounds: z_end ({new_z_end}) must be > z_start ({new_z_start})."
            )

        if self.segments:
            previous_segment = self.segments[-1]
            previous_z_end = float(previous_segment.z_end)
            z_gap = new_z_start - previous_z_end

            # Reject overlap / reversed insertion.
            if z_gap < -self.eps_z:
                raise ValueError(
                    "Non-contiguous stack append: overlap or wrong order detected. "
                    f"Previous segment '{previous_segment.tag}' ends at z={previous_z_end}, "
                    f"new segment starts at z={new_z_start}, eps_z={self.eps_z}."
                )

            # Reject positive gap larger than tolerance.
            if z_gap > self.eps_z:
                raise ValueError(
                    "Non-contiguous stack append: gap detected. "
                    f"Previous segment '{previous_segment.tag}' ends at z={previous_z_end}, "
                    f"new segment starts at z={new_z_start}, gap={z_gap}, eps_z={self.eps_z}."
                )

        new_segment = StackSegment(
            tag=f"seg_{len(self.segments)}",
            z_start=new_z_start,
            z_end=new_z_end,
            field=field,
        )
        self.segments.append(new_segment)

    def field_at(self, z: float, junction_side: str = "left") -> ContinuousSectionField:
        """Return the segment field mapped from global z."""
        segment = self._find_segment(z=float(z), junction_side=junction_side)
        return segment.field

    @staticmethod
    def make_field_from_polygons(
        z0: float,
        z1: float,
        polygons_s0: Sequence[Polygon],
        polygons_s1: Sequence[Polygon],
    ) -> ContinuousSectionField:
        """Create one ContinuousSectionField from two generic polygon sets."""
        if z1 <= z0:
            raise ValueError(f"Invalid segment bounds: z1 ({z1}) must be > z0 ({z0}).")
        if not polygons_s0 or not polygons_s1:
            raise ValueError("Both polygons_s0 and polygons_s1 must be non-empty.")

        s0 = Section(polygons=tuple(polygons_s0), z=float(z0))
        s1 = Section(polygons=tuple(polygons_s1), z=float(z1))
        return ContinuousSectionField(section0=s0, section1=s1)

    def build_from_specs(self, specs: List[SegmentSpec], sort_by_z: bool = False) -> None:
        """
        Build the full stack from a list of ``SegmentSpec`` objects.

        Notes
        -----
        - Specs are consumed in the provided order (stack semantics).
        - Automatic reordering is intentionally not supported.
        - Contiguity/coherence is enforced by ``append()`` for each built segment.
        """
        if sort_by_z:
            raise ValueError(
                "Automatic reordering is not supported in CSFStacked. "
                "Provide specs in the intended stack order."
            )

        self.segments = []

        for spec in specs:
            built_field = self.make_field_from_polygons(
                z0=spec.z0,
                z1=spec.z1,
                polygons_s0=spec.polygons_s0,
                polygons_s1=spec.polygons_s1,
            )
            self.append(built_field)

    def validate_contiguity(self, require_contiguity: bool = True) -> None:
        """Validate ordering, overlap, and optional strict contiguity."""
        if not self.segments:
            raise ValueError("Stack is empty. Add at least one segment.")

        for i, seg in enumerate(self.segments):
            if not (seg.z_end > seg.z_start):
                raise ValueError(f"Invalid segment '{seg.tag}': z_end must be > z_start.")

            if i == 0:
                continue

            prev = self.segments[i - 1]

            if seg.z_start < prev.z_end - self.eps_z:
                raise ValueError(
                    f"Overlap detected between '{prev.tag}' [{prev.z_start}, {prev.z_end}] "
                    f"and '{seg.tag}' [{seg.z_start}, {seg.z_end}]."
                )

            if require_contiguity and abs(seg.z_start - prev.z_end) > self.eps_z:
                raise ValueError(
                    f"Gap detected between '{prev.tag}' end={prev.z_end} and "
                    f"'{seg.tag}' start={seg.z_start}."
                )



    def _find_segment(self, z: float, junction_side: str = "left") -> StackSegment:
        if not self.segments:
            raise ValueError("Stack is empty.")

        if junction_side not in ("left", "right"):
            raise ValueError("junction_side must be 'left' or 'right'.")

        query_z = float(z)
        eps = self.eps_z

        z_min = float(self.segments[0].z_start)
        z_max = float(self.segments[-1].z_end)

        if query_z < z_min - eps or query_z > z_max + eps:
            raise ValueError(
                f"z={query_z} is outside stack domain [{z_min}, {z_max}]."
            )

        for i, seg in enumerate(self.segments):
            a = float(seg.z_start)
            b = float(seg.z_end)

            inside = (a - eps <= query_z <= b + eps)
            if not inside:
                continue

            on_left = abs(query_z - a) <= eps
            on_right = abs(query_z - b) <= eps

            # External boundaries
            if i == 0 and on_left:
                return seg

            if i == len(self.segments) - 1 and on_right:
                return seg

            # Internal left boundary of this segment
            if on_left and i > 0:
                if junction_side == "right":
                    return seg
                return self.segments[i - 1]

            # Internal right boundary of this segment
            if on_right and i < len(self.segments) - 1:
                if junction_side == "left":
                    return seg
                return self.segments[i + 1]

            # Strict interior
            return seg

        raise ValueError(
            f"z={query_z} could not be mapped to any segment "
            f"(check stack contiguity and eps_z={self.eps_z})."
        )


    def section(self, z: float, junction_side: str = "left"):
        return self.field_at(z, junction_side=junction_side).section(float(z))

    def section_full_analysis(self, z: float, junction_side: str = "left") -> float:
        sec = self.section(z, junction_side=junction_side)
        out = section_full_analysis(sec)
        return out

    def _compute_axis_bounds_with_margin(
        self,
        xs: Sequence[float],
        ys: Sequence[float],
        zs: Sequence[float],
        margin_ratio: float = 0.10,
    ):
        """
        Compute axis-aligned limits with independent margins per axis.

        Returns:
            ((xmin, xmax), (ymin, ymax), (zmin, zmax), (dx, dy, dz))
        """
        if not xs or not ys or not zs:
            raise ValueError("Empty coordinate lists: cannot compute bounds.")
        if margin_ratio < 0.0:
            raise ValueError("margin_ratio must be >= 0.")

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        zmin, zmax = min(zs), max(zs)

        dx = xmax - xmin
        dy = ymax - ymin
        dz = zmax - zmin

        if dx <= 0.0:
            cx = 0.5 * (xmin + xmax)
            xmin, xmax = cx - 0.5, cx + 0.5
            dx = 1.0
        if dy <= 0.0:
            cy = 0.5 * (ymin + ymax)
            ymin, ymax = cy - 0.5, cy + 0.5
            dy = 1.0
        if dz <= 0.0:
            cz = 0.5 * (zmin + zmax)
            zmin, zmax = cz - 0.5, cz + 0.5
            dz = 1.0

        mx = dx * margin_ratio
        my = dy * margin_ratio
        mz = dz * margin_ratio

        return (xmin - mx, xmax + mx), (ymin - my, ymax + my), (zmin - mz, zmax + mz), (dx, dy, dz)

    @staticmethod
    def _apply_box_limits(ax, bounds) -> None:
        """Apply precomputed limits and set data-proportional box aspect."""
        (xmin, xmax), (ymin, ymax), (zmin, zmax), (dx, dy, dz) = bounds
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_zlim(zmin, zmax)
        ax.set_box_aspect((dx, dy, dz))
#-----------------------------------------------------------------------------------------------
    def plot_weight(
        self,
        z: float,
        poly_indices_to_plot=None,
        num_points: int = 100,
        tol: float = 1e-12,
        junction_side: str = "left",        
    ):
        """
        Plot the weight distributions for the segment selected by global ``z``.

        Dispatch policy
        ---------------
        - The target segment is selected through ``field_at(...)`` using the same
          ``z`` and ``junction_side`` policy used by the other stacked wrappers.
        - Once the correct segment is identified, a ``Visualizer`` is instantiated
          from that field and the plotting call is delegated to it.

        Notes
        -----
        All plotting parameters are forwarded unchanged so that the stacked API
        remains aligned with the single-field plotting API.
        """
        field = self.field_at(z=float(z), junction_side=junction_side)
        vis = Visualizer(field)

        return vis.plot_weight(
            num_points=num_points,
            tol=tol,
            poly_indices_to_plot=poly_indices_to_plot,
        )


    def plot_properties(
        self,
        keys_to_plot=None,
        alpha: float = 1,
        title: str = None,
        num_points: int = 100,
        show_junctions: bool = True,
    ):
        """
        Plot selected section properties over the full CSFStacked domain.

        One continuous curve is evaluated inside each stacked segment. Internal
        junctions are kept as segment boundaries, so discontinuities are not
        hidden by interpolating across adjacent fields.

        Parameters
        ----------
        keys_to_plot : list[str] | None
            Property keys to plot, e.g. ["A", "Ix", "Iy", "Ip"].
            If None or empty, nothing is plotted.
        alpha : float
            Kept for API alignment with Visualizer.plot_properties.
        title : str | None
            Figure title. If None, a default stack-wide title is used.
        num_points : int
            Number of sample points per stacked segment.
        show_junctions : bool
            If True, draw vertical dotted lines at internal segment junctions.
        """
        import numpy as np
        import matplotlib.pyplot as plt

        if not self.segments:
            raise ValueError("Stack is empty. Add at least one segment.")
        if num_points < 2:
            raise ValueError("num_points must be >= 2.")

        if keys_to_plot is None:
            keys_to_plot = []
        else:
            keys_to_plot = list(dict.fromkeys(keys_to_plot))
            keys_to_plot = [k for k in keys_to_plot if str(k).lower() != "geometry"]

        if len(keys_to_plot) == 0:
            return None

        eps_value = 1e-12
        need_vroark = (
            "J_s_vroark" in keys_to_plot
            or "J_s_vroark_fidelity" in keys_to_plot
        )

        z_by_segment: list[np.ndarray] = []
        data_series = {key: [] for key in keys_to_plot}
        data_series_right = {key: [] for key in keys_to_plot}

        def _to_float_or_nan(value):
            if value is None:
                return np.nan
            try:
                value = float(value)
            except Exception:
                return np.nan
            if abs(value) < eps_value:
                return 0.0
            return value

        for seg in self.segments:
            z_values = np.linspace(float(seg.z_start), float(seg.z_end), num_points)
            z_by_segment.append(z_values)

            for z in z_values:
                current_section = seg.field.section(float(z))
                props = section_full_analysis(
                    current_section,
                    compute_vroark=need_vroark,
                )

                for key in keys_to_plot:
                    raw = props.get(key, None)
                    is_pair = isinstance(raw, (tuple, list, np.ndarray)) and len(raw) == 2

                    if is_pair:
                        data_series[key].append(_to_float_or_nan(raw[0]))
                        data_series_right[key].append(_to_float_or_nan(raw[1]))
                    else:
                        data_series[key].append(_to_float_or_nan(raw))
                        data_series_right[key].append(np.nan)

        z_values_all = np.concatenate(z_by_segment)
        num_keys = len(keys_to_plot)

        fig, axes = plt.subplots(
            num_keys,
            1,
            figsize=(10, 2.2 * num_keys),
            sharex=True,
        )
        if num_keys == 1:
            axes = [axes]

        if title is None:
            z_min, z_max = self.global_bounds()
            title = f"Stack Properties | z-range [{z_min:g}, {z_max:g}]"

        fig.suptitle(str(title), fontsize=14, fontweight="bold", y=0.995)
        colors = plt.cm.viridis(np.linspace(0, 0.9, num_keys))

        # Draw per-segment curves. This avoids visual interpolation across
        # internal stack junctions when a property is discontinuous.
        segment_slices = []
        start_idx = 0
        for z_segment in z_by_segment:
            end_idx = start_idx + len(z_segment)
            segment_slices.append(slice(start_idx, end_idx))
            start_idx = end_idx

        junction_z = [float(seg.z_start) for seg in self.segments[1:]]

        for i, (key, color) in enumerate(zip(keys_to_plot, colors)):
            ax = axes[i]
            y_left = np.asarray(data_series[key], dtype=float)
            y_right = np.asarray(data_series_right[key], dtype=float)

            finite_left = np.isfinite(y_left)
            finite_right = np.isfinite(y_right)
            has_right = bool(np.any(finite_right))

            for sl in segment_slices:
                ax.plot(
                    z_values_all[sl],
                    y_left[sl],
                    color=color,
                    linewidth=2,
                )

            if show_junctions:
                for zj in junction_z:
                    ax.axvline(zj, linestyle=":", linewidth=0.8, alpha=0.55)

            if has_right:
                ax_r = ax.twinx()
                for sl in segment_slices:
                    ax_r.plot(
                        z_values_all[sl],
                        y_right[sl],
                        linestyle="--",
                        linewidth=1.5,
                    )
                ax_r.set_ylabel("right", fontweight="bold")
                ax_r.grid(False)

            if y_left.size == 0 or not np.any(finite_left):
                ax.set_ylabel(key, fontweight="bold")
                ax.grid(True, linestyle=":", alpha=0.6)
                ax.text(
                    0.995,
                    1.01,
                    f"{key}: no valid left-axis data",
                    transform=ax.transAxes,
                    ha="right",
                    va="bottom",
                    fontsize=9,
                    clip_on=False,
                )
                print(f"{key}: no valid left-axis data")
                continue

            y_lf = y_left[finite_left]
            z_lf = z_values_all[finite_left]

            i_min_l = int(np.argmin(y_lf))
            i_max_l = int(np.argmax(y_lf))

            v_min_l = float(y_lf[i_min_l])
            v_max_l = float(y_lf[i_max_l])
            z_min_l = float(z_lf[i_min_l])
            z_max_l = float(z_lf[i_max_l])

            ax.scatter([z_min_l], [v_min_l], marker="v", s=26, zorder=3)
            ax.scatter([z_max_l], [v_max_l], marker="^", s=26, zorder=3)

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

            if v_max_l != v_min_l:
                margin_l = (v_max_l - v_min_l) * 0.10
            else:
                margin_l = max(abs(v_max_l) * 0.05, 0.1)
            ax.set_ylim(v_min_l - margin_l, v_max_l + margin_l)

            ax.set_ylabel(key, fontweight="bold")
            ax.grid(True, linestyle=":", alpha=0.6)

            title_right = (
                f"{key}: min={v_min_l:.6g}@z={z_min_l:.6g}  "
                f"max={v_max_l:.6g}@z={z_max_l:.6g}"
            )
            ax.text(
                0.995,
                1.01,
                title_right,
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9,
                clip_on=False,
            )

            print(
                f"{key}: min={v_min_l:.12g} at z={z_min_l:.12g} | "
                f"max={v_max_l:.12g} at z={z_max_l:.12g}"
            )

            if has_right:
                y_rf = y_right[finite_right]
                z_rf = z_values_all[finite_right]
                i_min_r = int(np.argmin(y_rf))
                i_max_r = int(np.argmax(y_rf))
                print(
                    f"{key} [right]: min={float(y_rf[i_min_r]):.12g} "
                    f"at z={float(z_rf[i_min_r]):.12g} | "
                    f"max={float(y_rf[i_max_r]):.12g} "
                    f"at z={float(z_rf[i_max_r]):.12g}"
                )

        axes[-1].set_xlabel("Z coordinate")
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        return axes

    def plot_section_2d(
        self,
        z: float,
        junction_side: str = "left",
        show_ids: bool = True,
        show_weights: bool = True,
        show_vertex_ids: bool = False,
        show_legenda: bool = False,
        title: Optional[str] = None,
        ax=None,
    ):
        """
        Plot the 2D section at global coordinate ``z`` using stacked dispatch.

        Dispatch policy
        ---------------
        - The target segment is selected through ``field_at(...)`` using the same
          ``z`` and ``junction_side`` policy already used by ``section()`` and
          ``section_full_analysis()``.
        - Once the correct segment is identified, a Visualizer is instantiated
          from that field and the call is delegated to it.

        Notes
        -----
        All plotting parameters are forwarded unchanged so that the stacked API
        stays aligned with the single-field plotting API.
        """
        field = self.field_at(z=float(z), junction_side=junction_side)
        vis = Visualizer(field)
        field = self.field_at(z=float(z), junction_side=junction_side)
        if title is None:
          title=""
        title = f"{title} z = {z} : range [{field.s0.z:g}, {field.s1.z:g}]"
        return vis.plot_section_2d(
            z=float(z),
            show_ids=show_ids,
            show_weights=show_weights,
            show_vertex_ids=show_vertex_ids,
            show_legenda=show_legenda,
            title=title,
            ax=ax,
        )


    def plot_volume_3d(
        self,
        z: float,
        junction_side: str = "left",
        show_end_sections: bool = True,
        line_percent: float = 100.0,
        seed: int = 0,
        title: str = None,
        ax=None,
        equalize_z: bool = False,
    ):
        """
        Plot the 3D ruled volume of the stacked segment selected by global ``z``.

        Dispatch policy
        ---------------
        - The target segment is selected through ``field_at(...)`` using the same
          ``z`` and ``junction_side`` policy already used by ``section()`` and
          ``plot_section_2d()``.
        - Once the correct segment is identified, a ``Visualizer`` is instantiated
          from that field and the plotting call is delegated to it.

        Notes
        -----
        All plotting parameters are forwarded unchanged so that the stacked API
        remains aligned with the single-field plotting API.
        """
        field = self.field_at(z=float(z), junction_side=junction_side)
        vis = Visualizer(field)

        if title is None:            
            field = self.field_at(z=float(z), junction_side=junction_side)
            title = f"Plot volume | z-range [{field.s0.z:g}, {field.s1.z:g}]"

        return vis.plot_volume_3d(
            show_end_sections=show_end_sections,
            line_percent=line_percent,
            seed=seed,
            title=title,
            ax=ax,
            equalize_z=equalize_z,
        )
#-----------------------------------------------------------------------------------------------
    def plot_volume_3d_global(
        self,
        title: str = None,
        line_percent: float = 100.0,
        seed: int = 1,
        margin_ratio: float = 0.10,
        display_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
        box_aspect_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
        wire: bool = False,
        colors: bool = True,
        line_width: float = 1.0,
    ):
        """
        Render the full stacked volume in one global 3D plot.

        Supported combinations:
        - wire=False, colors=True  : filled colored solids + edges
        - wire=False, colors=False : filled grayscale solids + edges
        - wire=True,  colors=True  : wireframe with per-polygon colors
        - wire=True,  colors=False : wireframe in grayscale/black

        Optimizations vs. original
        --------------------------
        - All filled faces (caps + side quads) are batched into one
          ``Poly3DCollection`` per color, replacing O(N) ``plot_surface``
          / ``plot_trisurf`` calls with a single ``add_collection3d``.
        - All edge segments of the same (linewidth, color) style are
          concatenated with NaN separators and drawn with a single
          ``ax.plot`` call, replacing O(N*M) individual calls.
        - Geometry data are accumulated as plain lists and converted to
          NumPy arrays only at render time (avoids repeated small allocs).
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import random
        from collections import defaultdict
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        # ------------------------------------------------------------------
        # Input validation  (unchanged)
        # ------------------------------------------------------------------
        if not (0.0 <= line_percent <= 100.0):
            raise ValueError("line_percent must be within [0, 100].")
        if margin_ratio < 0.0:
            raise ValueError("margin_ratio must be >= 0.")

        sx, sy, sz = display_scale
        if sx <= 0.0 or sy <= 0.0 or sz <= 0.0:
            raise ValueError("display_scale values must be > 0.")

        bx, by, bz = box_aspect_scale
        if bx <= 0.0 or by <= 0.0 or bz <= 0.0:
            raise ValueError("box_aspect_scale values must be > 0.")

        if not isinstance(wire, bool):
            raise TypeError("wire must be bool.")
        if not isinstance(colors, bool):
            raise TypeError("colors must be bool.")
        if line_width <= 0.0:
            raise ValueError("line_width must be > 0.")

        # ------------------------------------------------------------------
        # Deterministic color map  (unchanged)
        # ------------------------------------------------------------------
        rng = random.Random(seed)
        palette = [
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
        rng.shuffle(palette)

        color_map: dict[str, tuple] = {}
        color_idx = 0

        def _get_poly_color(poly_name: str) -> tuple:
            nonlocal color_idx
            if not colors:
                return (0.70, 0.70, 0.70)
            if poly_name not in color_map:
                color_map[poly_name] = palette[color_idx % len(palette)]
                color_idx += 1
            return color_map[poly_name]

        default_edge_color = (0.10, 0.10, 0.10)

        # ------------------------------------------------------------------
        # Plot initialization
        # ------------------------------------------------------------------
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=18, azim=120)
        ax.set_proj_type("persp")

        # ------------------------------------------------------------------
        # Batch accumulators
        #
        # faces_by_color : color -> list of triangles [(x,y,z), (x,y,z), (x,y,z)]
        #   Filled faces (caps + side quads) grouped by polygon color.
        #   Rendered in one Poly3DCollection per color.
        #
        # edges_by_style : (lw, color) -> {'x': list, 'y': list, 'z': list}
        #   Edge segments concatenated with NaN separators.
        #   Rendered in one ax.plot per (lw, color) style.
        #
        # all_x/y/z : flat lists for global bounds computation.
        # ------------------------------------------------------------------
        faces_by_color: dict[tuple, list] = defaultdict(list)
        edges_by_style: dict[tuple, dict] = defaultdict(lambda: {"x": [], "y": [], "z": []})

        all_x: list[float] = []
        all_y: list[float] = []
        all_z: list[float] = []

        # ------------------------------------------------------------------
        # Geometry helpers (pure accumulation — no Axes calls here)
        # ------------------------------------------------------------------
        def _add_edge(x0, y0, z0, x1, y1, z1, lw: float, color: tuple) -> None:
            """Append one segment (with NaN separator) to the edge batch."""
            key = (lw, color)
            buf = edges_by_style[key]
            buf["x"].extend((x0, x1, np.nan))
            buf["y"].extend((y0, y1, np.nan))
            buf["z"].extend((z0, z1, np.nan))

        def _add_polygon_edges(verts, lw: float, color: tuple) -> None:
            """Batch all boundary edges of a polygon."""
            n = len(verts)
            for i in range(n):
                j = (i + 1) % n
                _add_edge(
                    verts[i][0], verts[i][1], verts[i][2],
                    verts[j][0], verts[j][1], verts[j][2],
                    lw, color,
                )

        def _add_cap_faces(verts, color: tuple) -> None:
            """Fan-triangulate a cap polygon and store in the face batch."""
            n = len(verts)
            if n < 3:
                return
            v0 = verts[0]
            for i in range(1, n - 1):
                faces_by_color[color].append((v0, verts[i], verts[i + 1]))

        # ------------------------------------------------------------------
        # Main geometry accumulation loop
        # ------------------------------------------------------------------
        for seg in self.segments:
            s0 = seg.field.section(seg.z_start)
            s1 = seg.field.section(seg.z_end)

            p0_map = {p.name: p for p in s0.polygons}
            p1_map = {p.name: p for p in s1.polygons}
            common_names = sorted(set(p0_map.keys()) & set(p1_map.keys()))

            if not common_names:
                continue

            z0_plot = seg.z_start * sz
            z1_plot = seg.z_end * sz

            for name in common_names:
                p0 = p0_map[name]
                p1 = p1_map[name]
                v0 = p0.vertices
                v1 = p1.vertices

                if len(v0) != len(v1):
                    raise ValueError(
                        f"Polygon '{name}' has mismatched vertex count "
                        f"between z-start and z-end in segment '{seg.tag}'."
                    )

                #poly_color = _get_poly_color(name)
                poly_color = _get_poly_color(f"{seg.tag}::{name}")
                wire_line_color = poly_color if (wire and colors) else default_edge_color

                # Scaled coordinates (computed once per polygon)
                x0 = np.array([pt.x * sx for pt in v0], dtype=float)
                y0 = np.array([pt.y * sy for pt in v0], dtype=float)
                x1 = np.array([pt.x * sx for pt in v1], dtype=float)
                y1 = np.array([pt.y * sy for pt in v1], dtype=float)

                n = len(v0)
                zz0 = np.full(n, z0_plot, dtype=float)
                zz1 = np.full(n, z1_plot, dtype=float)

                cap0 = list(zip(x0.tolist(), y0.tolist(), zz0.tolist()))
                cap1 = list(zip(x1.tolist(), y1.tolist(), zz1.tolist()))

                cross_lw = 2.2 * line_width

                # ------------------------------------------------------
                # Caps: faces + boundary edges
                # ------------------------------------------------------
                if wire:
                    _add_polygon_edges(cap0, cross_lw, wire_line_color)
                    _add_polygon_edges(cap1, cross_lw, wire_line_color)
                else:
                    _add_cap_faces(cap0, poly_color)
                    _add_cap_faces(cap1, poly_color)
                    _add_polygon_edges(cap0, cross_lw, default_edge_color)
                    _add_polygon_edges(cap1, cross_lw, default_edge_color)

                # ------------------------------------------------------
                # Longitudinal connectors / side faces
                # ------------------------------------------------------
                if line_percent <= 0.0:
                    selected_indices: set[int] = set()
                elif line_percent >= 100.0:
                    selected_indices = set(range(n))
                else:
                    n_keep = max(1, int(np.ceil(n * line_percent / 100.0)))
                    selected_indices = set(
                        np.linspace(0, n - 1, num=n_keep, dtype=int).tolist()
                    )

                for i in range(n):
                    j = (i + 1) % n

                    a0 = cap0[i]
                    b0 = cap0[j]
                    b1 = cap1[j]
                    a1 = cap1[i]

                    if wire:
                        if i in selected_indices:
                            _add_edge(
                                a0[0], a0[1], a0[2],
                                a1[0], a1[1], a1[2],
                                0.8 * line_width, wire_line_color,
                            )
                    else:
                        # Side quad as two triangles
                        faces_by_color[poly_color].append((a0, b0, b1))
                        faces_by_color[poly_color].append((a0, b1, a1))

                        # Only longitudinal edges (avoids duplicating cap edges)
                        _add_edge(
                            a0[0], a0[1], a0[2],
                            a1[0], a1[1], a1[2],
                            0.5 * line_width, default_edge_color,
                        )
                        _add_edge(
                            b0[0], b0[1], b0[2],
                            b1[0], b1[1], b1[2],
                            0.5 * line_width, default_edge_color,
                        )

                # Bounds accumulation
                all_x += x0.tolist() + x1.tolist()
                all_y += y0.tolist() + y1.tolist()
                all_z += [z0_plot] * n + [z1_plot] * n

        # ------------------------------------------------------------------
        # Render phase: one Poly3DCollection per color
        # ------------------------------------------------------------------
        for face_color, tri_list in faces_by_color.items():
            coll = Poly3DCollection(
                tri_list,
                alpha=0.25,
                facecolor=face_color,
                edgecolor="none",
                linewidth=0.0,
                shade=False,
            )
            ax.add_collection3d(coll)

        # ------------------------------------------------------------------
        # Render phase: one ax.plot per edge style
        # ------------------------------------------------------------------
        for (lw, line_color), buf in edges_by_style.items():
            xs = buf["x"]
            if not xs:
                continue
            ax.plot(xs, buf["y"], buf["z"], "-", lw=lw, color=line_color)

        # ------------------------------------------------------------------
        # Global limits and aspect ratio  (unchanged)
        # ------------------------------------------------------------------
        if all_x and all_y and all_z:
            xmin, xmax = min(all_x), max(all_x)
            ymin, ymax = min(all_y), max(all_y)
            zmin, zmax = min(all_z), max(all_z)

            dx = max(xmax - xmin, 1e-12)
            dy = max(ymax - ymin, 1e-12)
            dz = max(zmax - zmin, 1e-12)

            ax.set_xlim(xmin - dx * margin_ratio, xmax + dx * margin_ratio)
            ax.set_ylim(ymin - dy * margin_ratio, ymax + dy * margin_ratio)
            ax.set_zlim(zmin - dz * margin_ratio, zmax + dz * margin_ratio)
            ax.set_box_aspect((dx * bx, dy * by, dz * bz))

        # ------------------------------------------------------------------
        # Labels and title  (unchanged)
        # ------------------------------------------------------------------
        ax.set_xlabel(f"X (display x{sx:.4g})" if abs(sx - 1.0) > 1e-15 else "X")
        ax.set_ylabel(f"Y (display x{sy:.4g})" if abs(sy - 1.0) > 1e-15 else "Y")
        ax.set_zlabel(f"Z (display x{sz:.4g})" if abs(sz - 1.0) > 1e-15 else "Z")


        if title:
            title3d=title
        else:
            mode = "wireframe" if wire else "solid"
            scheme = "color" if colors else "grayscale"
            title3d = f"Global 3D ({mode}, {scheme})"
        ax.set_title(title3d)

        return ax
    
    def global_bounds(self):
        """
        Return global z bounds of the stacked segments as (z_min, z_max).
        Raises if the stack is empty.
        """
        if not self.segments:
            raise ValueError("CSFStacked is empty.")
        z_min = min(seg.z_start for seg in self.segments)
        z_max = max(seg.z_end for seg in self.segments)
        return z_min, z_max

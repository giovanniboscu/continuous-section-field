from __future__ import annotations
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

from .section_field import (
    Pt,
    Polygon,
    Section,
    ContinuousSectionField,
    section_full_analysis,
    Visualizer,
)


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
        Accepts exactly one explicit argument: `field`.
        """
        z_start = float(field.s0.z)
        z_end = float(field.s1.z)

        if z_end <= z_start:
            raise ValueError(
                f"Invalid field bounds: z_end ({z_end}) must be > z_start ({z_start})."
            )

        self.segments.append(
            StackSegment(
                tag=f"seg_{len(self.segments)}",
                z_start=z_start,
                z_end=z_end,
                field=field,
            )
        )

        # Keep deterministic ordering after each append
        self.segments.sort(key=lambda s: s.z_start)

    def field_at(self, z: float, junction_side: str = "left") -> ContinuousSectionField:
        """
        Return the ContinuousSectionField at global z.

        Junction policy:
        - External boundaries are unambiguous.
        - Internal junctions are resolved explicitly by `junction_side`:
          - "left"  -> field on the left of the junction
          - "right" -> field on the right of the junction
        """
        if not self.segments:
            raise ValueError("Stack is empty.")
        if junction_side not in ("left", "right"):
            raise ValueError("junction_side must be 'left' or 'right'.")

        z = float(z)
        first = self.segments[0]
        last = self.segments[-1]

        if z < first.z_start - self.eps_z or z > last.z_end + self.eps_z:
            raise ValueError(f"z={z} is outside stack domain [{first.z_start}, {last.z_end}].")

        # External boundaries: always unambiguous
        if abs(z - first.z_start) <= self.eps_z:
            return first.field
        if abs(z - last.z_end) <= self.eps_z:
            return last.field

        # Internal junctions: explicit side selection
        for i in range(1, len(self.segments)):
            z_j = self.segments[i].z_start
            if abs(z - z_j) <= self.eps_z:
                return self.segments[i - 1].field if junction_side == "left" else self.segments[i].field

        # Regular interior point
        for seg in self.segments:
            if (z >= seg.z_start - self.eps_z) and (z <= seg.z_end + self.eps_z):
                return seg.field

        raise ValueError(f"z={z} could not be mapped to any segment.")

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

    def add_segment_spec(self, spec: SegmentSpec) -> None:
        """Build one field from spec and append it to the stack."""
        field = self.make_field_from_polygons(
            z0=spec.z0,
            z1=spec.z1,
            polygons_s0=spec.polygons_s0,
            polygons_s1=spec.polygons_s1,
        )
        self.segments.append(
            StackSegment(
                tag=spec.tag,
                z_start=float(spec.z0),
                z_end=float(spec.z1),
                field=field,
            )
        )

    def build_from_specs(self, specs: List[SegmentSpec], sort_by_z: bool = True) -> None:
        """Build full stack from a list of specs."""
        self.segments = []
        for spec in specs:
            self.add_segment_spec(spec)
        if sort_by_z:
            self.segments.sort(key=lambda s: s.z_start)

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

    def _find_segment(self, z: float) -> StackSegment:
        """
        Return the unique segment containing z with deterministic interval policy.

        Interval policy (left-open except first, always right-closed):
        - First segment:      [z_start, z_end]
        - Other segments:     (z_start, z_end]

        Consequences:
        - Global left edge and right edge are included.
        - Internal junctions are not ambiguous: they belong to the segment on the left.
        """
        if not self.segments:
            raise ValueError("Stack is empty.")

        z = float(z)

        # Fast global range check
        z_min = self.segments[0].z_start
        z_max = self.segments[-1].z_end
        if z < z_min - self.eps_z or z > z_max + self.eps_z:
            raise ValueError(f"z={z} is outside stack domain [{z_min}, {z_max}].")

        for i, seg in enumerate(self.segments):
            if i == 0:
                left_ok = z >= seg.z_start - self.eps_z
            else:
                left_ok = z > seg.z_start + self.eps_z

            right_ok = z <= seg.z_end + self.eps_z

            if left_ok and right_ok:
                return seg

        raise ValueError(f"z={z} not mapped to any segment (check contiguity/tolerance).")

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


    def plot_volume_3d_global(
        self,
        line_percent: float = 100.0,
        seed: int = 1,
        margin_ratio: float = 0.10,
        display_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
        box_aspect_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
        wire: bool = False,
        colors: bool = True,
    ):
        """
        Render the full stacked volume in one global 3D plot without Poly3DCollection.

        Supported combinations:
        - wire=False, colors=True  : filled colored solids + edges
        - wire=False, colors=False : filled grayscale solids + edges
        - wire=True,  colors=True  : wireframe with per-polygon colors
        - wire=True,  colors=False : wireframe in grayscale/black
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import random

        # -------------------------------------------------------------------------
        # Input validation
        # -------------------------------------------------------------------------
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

        # -------------------------------------------------------------------------
        # Deterministic color map by polygon name (seeded)
        # -------------------------------------------------------------------------
        rng = random.Random(seed)
        palette = [
            (0.121, 0.466, 0.705),  # blue
            (1.000, 0.498, 0.054),  # orange
            (0.172, 0.627, 0.172),  # green
            (0.839, 0.153, 0.157),  # red
            (0.580, 0.404, 0.741),  # purple
            (0.549, 0.337, 0.294),  # brown
            (0.890, 0.467, 0.761),  # pink
            (0.498, 0.498, 0.498),  # gray
            (0.737, 0.741, 0.133),  # olive
            (0.090, 0.745, 0.811),  # cyan
        ]
        rng.shuffle(palette)
        color_map: dict[str, tuple[float, float, float]] = {}
        color_idx = 0

        def _get_poly_color(poly_name: str) -> tuple[float, float, float]:
            nonlocal color_idx
            if not colors:
                return (0.70, 0.70, 0.70)  # grayscale fill
            if poly_name not in color_map:
                color_map[poly_name] = palette[color_idx % len(palette)]
                color_idx += 1
            return color_map[poly_name]

        # Edge color used for non-wire solid mode and grayscale wire mode
        default_edge_color = (0.10, 0.10, 0.10)

        # -------------------------------------------------------------------------
        # Plot init
        # -------------------------------------------------------------------------
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=18, azim=120)
        ax.set_proj_type("persp")

        all_x, all_y, all_z = [], [], []

        # -------------------------------------------------------------------------
        # Helpers
        # -------------------------------------------------------------------------
        def _plot_polygon_boundary(vertices_xyz, lw=0.6, line_color=(0.1, 0.1, 0.1)):
            """
            Draw only the true polygon boundary edges.
            """
            n = len(vertices_xyz)
            if n < 2:
                return
            xs = [p[0] for p in vertices_xyz]
            ys = [p[1] for p in vertices_xyz]
            zs = [p[2] for p in vertices_xyz]
            for i in range(n):
                j = (i + 1) % n
                ax.plot(
                    [xs[i], xs[j]],
                    [ys[i], ys[j]],
                    [zs[i], zs[j]],
                    "-",
                    lw=lw,
                    color=line_color,
                )

        def _plot_cap_filled(vertices_xyz, face_color, alpha=0.25, edge_lw=0.5):
            """
            Draw one filled cap with hidden triangulation lines, then draw true boundary.
            """
            n = len(vertices_xyz)
            if n < 3:
                _plot_polygon_boundary(vertices_xyz, lw=edge_lw, line_color=default_edge_color)
                return

            xs = np.array([p[0] for p in vertices_xyz], dtype=float)
            ys = np.array([p[1] for p in vertices_xyz], dtype=float)
            zs = np.array([p[2] for p in vertices_xyz], dtype=float)

            # Fan triangulation: (0, i, i+1)
            triangles = np.array([[0, i, i + 1] for i in range(1, n - 1)], dtype=int)

            ax.plot_trisurf(
                xs,
                ys,
                zs,
                triangles=triangles,
                color=face_color,
                alpha=alpha,
                edgecolor="none",  # hide internal diagonals
                linewidth=0.0,
                shade=False,
            )

            _plot_polygon_boundary(vertices_xyz, lw=edge_lw, line_color=default_edge_color)

        # -------------------------------------------------------------------------
        # Main rendering loop
        # -------------------------------------------------------------------------
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

                poly_color = _get_poly_color(name)

                # In wire mode with colors=True, lines use poly color.
                # Otherwise use grayscale edge color.
                wire_line_color = poly_color if (wire and colors) else default_edge_color

                cap0 = [(pt.x * sx, pt.y * sy, z0_plot) for pt in v0]
                cap1 = [(pt.x * sx, pt.y * sy, z1_plot) for pt in v1]
                cross_lw = 2.2  # thickness for transverse polygons only
                if wire:
                    _plot_polygon_boundary(cap0, lw=cross_lw, line_color=wire_line_color)
                    _plot_polygon_boundary(cap1, lw=cross_lw, line_color=wire_line_color)
                else:
                    _plot_cap_filled(cap0, face_color=poly_color, alpha=0.25, edge_lw=cross_lw)
                    _plot_cap_filled(cap1, face_color=poly_color, alpha=0.25, edge_lw=cross_lw)


                # Side faces / longitudinal connectors
                n = len(v0)
                for i in range(n):
                    j = (i + 1) % n

                    a0 = (v0[i].x * sx, v0[i].y * sy, z0_plot)
                    b0 = (v0[j].x * sx, v0[j].y * sy, z0_plot)
                    b1 = (v1[j].x * sx, v1[j].y * sy, z1_plot)
                    a1 = (v1[i].x * sx, v1[i].y * sy, z1_plot)

                    if wire:
                        # Only longitudinal segment between matching vertices
                        ax.plot(
                            [a0[0], a1[0]],
                            [a0[1], a1[1]],
                            [a0[2], a1[2]],
                            "-",
                            lw=0.8,
                            color=wire_line_color,
                        )
                    else:
                        # Filled quad (internal split hidden)
                        X = np.array([[a0[0], b0[0]], [a1[0], b1[0]]], dtype=float)
                        Y = np.array([[a0[1], b0[1]], [a1[1], b1[1]]], dtype=float)
                        Z = np.array([[a0[2], b0[2]], [a1[2], b1[2]]], dtype=float)

                        ax.plot_surface(
                            X, Y, Z,
                            color=poly_color,
                            alpha=0.25,
                            edgecolor="none",
                            linewidth=0.0,
                            shade=False,
                        )

                        # Draw only true quad edges
                        ax.plot([a0[0], b0[0]], [a0[1], b0[1]], [a0[2], b0[2]], "-", lw=0.5, color=default_edge_color)
                        ax.plot([b0[0], b1[0]], [b0[1], b1[1]], [b0[2], b1[2]], "-", lw=0.5, color=default_edge_color)
                        ax.plot([b1[0], a1[0]], [b1[1], a1[1]], [b1[2], a1[2]], "-", lw=0.5, color=default_edge_color)
                        ax.plot([a1[0], a0[0]], [a1[1], a0[1]], [a1[2], a0[2]], "-", lw=0.5, color=default_edge_color)

                # Bounds accumulation
                for pt in v0:
                    all_x.append(pt.x * sx)
                    all_y.append(pt.y * sy)
                    all_z.append(z0_plot)
                for pt in v1:
                    all_x.append(pt.x * sx)
                    all_y.append(pt.y * sy)
                    all_z.append(z1_plot)

        # -------------------------------------------------------------------------
        # Global limits and aspect
        # -------------------------------------------------------------------------
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

        ax.set_xlabel(f"X (display x{sx:.4g})" if abs(sx - 1.0) > 1e-15 else "X")
        ax.set_ylabel(f"Y (display x{sy:.4g})" if abs(sy - 1.0) > 1e-15 else "Y")
        ax.set_zlabel(f"Z (display x{sz:.4g})" if abs(sz - 1.0) > 1e-15 else "Z")

        mode = "wireframe" if wire else "solid"
        scheme = "color" if colors else "grayscale"
        ax.set_title(f"Global 3D ({mode}, {scheme})")

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


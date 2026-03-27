from __future__ import annotations
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np
import random
from typing import List, Sequence, Tuple


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
        """
        Return the stack segment mapped from global ``z``.

        Junction policy
        --------------
        - External boundaries are unambiguous and always map to the outer segments.
        - Internal junctions are handled explicitly via ``junction_side``:
            * ``"left"``  -> segment on the left of the junction
            * ``"right"`` -> segment on the right of the junction

        Notes
        -----
        This method is the single internal dispatch implementation for ``z -> segment``.
        Higher-level methods (``field_at``, ``section``, ``section_full_analysis``) must
        delegate to this method to keep junction behavior consistent.
        """
        if not self.segments:
            raise ValueError("Stack is empty.")

        if junction_side not in ("left", "right"):
            raise ValueError("junction_side must be 'left' or 'right'.")

        query_z = float(z)
        first_segment = self.segments[0]
        last_segment = self.segments[-1]
        stack_z_min = float(first_segment.z_start)
        stack_z_max = float(last_segment.z_end)

        # Global domain check with tolerance.
        if query_z < stack_z_min - self.eps_z or query_z > stack_z_max + self.eps_z:
            raise ValueError(
                f"z={query_z} is outside stack domain [{stack_z_min}, {stack_z_max}]."
            )

        # External boundaries are never ambiguous.
        if abs(query_z - stack_z_min) <= self.eps_z:
            return first_segment
        if abs(query_z - stack_z_max) <= self.eps_z:
            return last_segment

        # Internal junctions: explicit side selection.
        for segment_index in range(1, len(self.segments)):
            right_segment = self.segments[segment_index]
            left_segment = self.segments[segment_index - 1]
            junction_z = float(right_segment.z_start)

            if abs(query_z - junction_z) <= self.eps_z:
                if junction_side == "left":
                    return left_segment
                return right_segment

        # Interior (non-junction) query point.
        for current_segment in self.segments:
            segment_z_start = float(current_segment.z_start)
            segment_z_end = float(current_segment.z_end)

            strictly_inside_left = query_z > segment_z_start + self.eps_z
            strictly_inside_right = query_z < segment_z_end - self.eps_z

            if strictly_inside_left and strictly_inside_right:
                return current_segment

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





    def plot_volume_3d_global(
        self,
        title: String=None,
        line_percent: float = 100.0,
        seed: int = 1,
        margin_ratio: float = 0.10,
        display_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
        box_aspect_scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
        wire: bool = False,
        colors: bool = True,
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

                cross_lw = 2.2

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
                                0.8, wire_line_color,
                            )
                    else:
                        # Side quad as two triangles
                        faces_by_color[poly_color].append((a0, b0, b1))
                        faces_by_color[poly_color].append((a0, b1, a1))

                        # Only longitudinal edges (avoids duplicating cap edges)
                        _add_edge(
                            a0[0], a0[1], a0[2],
                            a1[0], a1[1], a1[2],
                            0.5, default_edge_color,
                        )
                        _add_edge(
                            b0[0], b0[1], b0[2],
                            b1[0], b1[1], b1[2],
                            0.5, default_edge_color,
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













    def plot_volume_3d_global2remove2(
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
        Render the full stacked volume in one global 3D plot.

        Supported combinations:
        - wire=False, colors=True  : filled colored solids + edges
        - wire=False, colors=False : filled grayscale solids + edges
        - wire=True,  colors=True  : wireframe with per-polygon colors
        - wire=True,  colors=False : wireframe in grayscale/black

        Notes
        -----
        - This implementation avoids Poly3DCollection and works with standard
          Matplotlib 3D plotting primitives.
        - In wire mode, `line_percent` controls how many longitudinal connectors
          are drawn.
        - In solid mode, the code draws filled caps and filled side quads, then
          overlays only the true geometric edges.
        """

        # ---------------------------------------------------------------------
        # Input validation
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # Deterministic color map by polygon name
        # ---------------------------------------------------------------------
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
            """
            Return a deterministic color for a polygon name.
            """
            nonlocal color_idx
            if not colors:
                return (0.70, 0.70, 0.70)
            if poly_name not in color_map:
                color_map[poly_name] = palette[color_idx % len(palette)]
                color_idx += 1
            return color_map[poly_name]

        # Default edge color used in grayscale mode and for solid-mode edges
        default_edge_color = (0.10, 0.10, 0.10)

        # ---------------------------------------------------------------------
        # Plot initialization
        # ---------------------------------------------------------------------
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=18, azim=120)
        ax.set_proj_type("persp")

        # Global bounds are accumulated while plotting
        all_x: list[float] = []
        all_y: list[float] = []
        all_z: list[float] = []

        # ---------------------------------------------------------------------
        # Helpers
        # ---------------------------------------------------------------------
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
            Draw one filled cap with hidden triangulation lines,
            then draw the true polygon boundary.
            """
            n = len(vertices_xyz)
            if n < 3:
                _plot_polygon_boundary(
                    vertices_xyz,
                    lw=edge_lw,
                    line_color=default_edge_color,
                )
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
                edgecolor="none",
                linewidth=0.0,
                shade=False,
            )

            _plot_polygon_boundary(
                vertices_xyz,
                lw=edge_lw,
                line_color=default_edge_color,
            )

        # ---------------------------------------------------------------------
        # Main rendering loop
        # ---------------------------------------------------------------------
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
                poly_color = _get_poly_color(str(seg.tag))
                # In wire mode with colors=True, lines use the polygon color.
                # Otherwise use a grayscale/black line.
                wire_line_color = poly_color if (wire and colors) else default_edge_color

                # -------------------------------------------------------------
                # Precompute scaled coordinates once per polygon
                # -------------------------------------------------------------
                x0 = np.array([pt.x * sx for pt in v0], dtype=float)
                y0 = np.array([pt.y * sy for pt in v0], dtype=float)
                x1 = np.array([pt.x * sx for pt in v1], dtype=float)
                y1 = np.array([pt.y * sy for pt in v1], dtype=float)

                cap0 = list(zip(x0, y0, np.full(len(v0), z0_plot, dtype=float)))
                cap1 = list(zip(x1, y1, np.full(len(v1), z1_plot, dtype=float)))

                cross_lw = 2.2  # thickness used for transverse polygon outlines

                if wire:
                    _plot_polygon_boundary(cap0, lw=cross_lw, line_color=wire_line_color)
                    _plot_polygon_boundary(cap1, lw=cross_lw, line_color=wire_line_color)
                else:
                    _plot_cap_filled(cap0, face_color=poly_color, alpha=0.25, edge_lw=cross_lw)
                    _plot_cap_filled(cap1, face_color=poly_color, alpha=0.25, edge_lw=cross_lw)

                # -------------------------------------------------------------
                # Longitudinal connectors / side faces
                # -------------------------------------------------------------
                n = len(v0)

                if line_percent <= 0.0:
                    selected_indices = set()
                elif line_percent >= 100.0:
                    selected_indices = set(range(n))
                else:
                    n_keep = max(1, int(np.ceil(n * line_percent / 100.0)))
                    selected_indices = set(
                        np.linspace(0, n - 1, num=n_keep, dtype=int).tolist()
                    )

                for i in range(n):
                    j = (i + 1) % n

                    a0 = (x0[i], y0[i], z0_plot)
                    b0 = (x0[j], y0[j], z0_plot)
                    b1 = (x1[j], y1[j], z1_plot)
                    a1 = (x1[i], y1[i], z1_plot)

                    if wire:
                        # In wire mode, draw only a subset of longitudinal lines
                        # according to `line_percent`.
                        if i in selected_indices:
                            ax.plot(
                                [a0[0], a1[0]],
                                [a0[1], a1[1]],
                                [a0[2], a1[2]],
                                "-",
                                lw=0.8,
                                color=wire_line_color,
                            )
                    else:
                        # Filled side quad with internal split hidden
                        X = np.array([[a0[0], b0[0]], [a1[0], b1[0]]], dtype=float)
                        Y = np.array([[a0[1], b0[1]], [a1[1], b1[1]]], dtype=float)
                        Z = np.array([[a0[2], b0[2]], [a1[2], b1[2]]], dtype=float)

                        ax.plot_surface(
                            X,
                            Y,
                            Z,
                            color=poly_color,
                            alpha=0.25,
                            edgecolor="none",
                            linewidth=0.0,
                            shade=False,
                        )

                        # Draw only the two longitudinal edges to reduce plotting cost.
                        ax.plot(
                            [a0[0], a1[0]],
                            [a0[1], a1[1]],
                            [a0[2], a1[2]],
                            "-",
                            lw=0.5,
                            color=default_edge_color,
                        )
                        ax.plot(
                            [b0[0], b1[0]],
                            [b0[1], b1[1]],
                            [b0[2], b1[2]],
                            "-",
                            lw=0.5,
                            color=default_edge_color,
                        )

                # -------------------------------------------------------------
                # Bounds accumulation
                # -------------------------------------------------------------
                all_x.extend(x0.tolist())
                all_x.extend(x1.tolist())
                all_y.extend(y0.tolist())
                all_y.extend(y1.tolist())
                all_z.extend([z0_plot] * n)
                all_z.extend([z1_plot] * n)

        # ---------------------------------------------------------------------
        # Global limits and aspect ratio
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # Labels and title
        # ---------------------------------------------------------------------
        ax.set_xlabel(f"X (display x{sx:.4g})" if abs(sx - 1.0) > 1e-15 else "X")
        ax.set_ylabel(f"Y (display x{sy:.4g})" if abs(sy - 1.0) > 1e-15 else "Y")
        ax.set_zlabel(f"Z (display x{sz:.4g})" if abs(sz - 1.0) > 1e-15 else "Z")

        mode = "wireframe" if wire else "solid"
        scheme = "color" if colors else "grayscale"
        ax.set_title(f"Global 3D ({mode}, {scheme})")

        return ax













    def plot_volume_3d_global2remove(
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

                #poly_color = _get_poly_color(name)
                poly_color = _get_poly_color(str(seg.tag))
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

                if line_percent <= 0.0:
                    selected_indices = []
                elif line_percent >= 100.0:
                    selected_indices = list(range(n))
                else:
                    n_keep = max(1, int(np.ceil(n * line_percent / 100.0)))
                    selected_indices = np.linspace(0, n - 1, num=n_keep, dtype=int).tolist()
                    selected_indices = sorted(set(selected_indices))

                for i in range(n):
                    j = (i + 1) % n

                    a0 = (v0[i].x * sx, v0[i].y * sy, z0_plot)
                    b0 = (v0[j].x * sx, v0[j].y * sy, z0_plot)
                    b1 = (v1[j].x * sx, v1[j].y * sy, z1_plot)
                    a1 = (v1[i].x * sx, v1[i].y * sy, z1_plot)

                    if wire:
                        # Draw only a subset of longitudinal lines controlled by line_percent
                        if i in selected_indices:
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

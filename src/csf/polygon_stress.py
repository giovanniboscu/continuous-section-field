"""Polygon-level stress analyses for a continuous section field.

The public functions are re-exported by :mod:`csf.section_field` so existing
imports from that module remain valid. Imports back into ``section_field``
are local to function calls to avoid a module-import cycle.
"""
from __future__ import annotations

from decimal import Decimal

import math
import weakref

from . import _tol
from .entities import Pt, Polygon, Section


def analyse_polygon_centroid_axis_shear(
    section_field,
    z: float,
    Mx: float,
    My: float,
    *,
    dz: float | None = None,
    derivative_rtol: float = 1.0e-8,
    derivative_atol: float = 1.0e-10,
    max_refinements: int = 20,
    debug: bool = False,
) -> dict[str, object]:
    """
    Compute the flexural centroid-axis shear contribution.

    The adopted reduced formulation is:

        tau_x = sigma_zz_M * dCx/dz
        tau_y = sigma_zz_M * dCy/dz

    where ``sigma_zz_M`` is the Navier stress generated only by ``Mx`` and
    ``My``. The axial-force contribution is excluded by evaluating Navier
    stresses with ``N=0``.

    The resulting centroid-axis shear field is self-equilibrated:

        integral_A(tau_x dA) = 0
        integral_A(tau_y dA) = 0

    The global centroid is calculated from the complete axial-flexural CSF
    section. Centroid values are cached per ``section_field`` and station.

    No Jourawski contribution is calculated by this function.
    """
    from .section_field import section_full_analysis

    z = float(z)
    Mx = float(Mx)
    My = float(My)
    derivative_rtol = float(derivative_rtol)
    derivative_atol = float(derivative_atol)
    max_refinements = int(max_refinements)

    z_start = float(section_field.s0.z)
    z_end = float(section_field.s1.z)

    if z_end <= z_start:
        raise ValueError("The CSF bounds must satisfy s1.z > s0.z.")

    if z < z_start or z > z_end:
        raise ValueError(
            f"z={z} is outside CSF bounds [{z_start}, {z_end}]."
        )

    if not math.isfinite(derivative_rtol) or derivative_rtol < 0.0:
        raise ValueError(
            "derivative_rtol must be finite and non-negative."
        )

    if not math.isfinite(derivative_atol) or derivative_atol < 0.0:
        raise ValueError(
            "derivative_atol must be finite and non-negative."
        )

    if derivative_rtol == 0.0 and derivative_atol == 0.0:
        raise ValueError(
            "At least one derivative tolerance must be positive."
        )

    if max_refinements < 1:
        raise ValueError("max_refinements must be >= 1.")

    length = z_end - z_start
    coordinate_tolerance = max(1.0e-14, 1.0e-12 * length)
    minimum_step = coordinate_tolerance

    # Persistent cache owned by this public function.
    centroid_cache = getattr(
        analyse_polygon_centroid_axis_shear,
        "_centroid_cache",
        None,
    )

    if centroid_cache is None:
        centroid_cache = weakref.WeakKeyDictionary()
        setattr(
            analyse_polygon_centroid_axis_shear,
            "_centroid_cache",
            centroid_cache,
        )

    field_cache = centroid_cache.get(section_field)

    if field_cache is None:
        field_cache = {}
        centroid_cache[section_field] = field_cache

    def _global_centroid(z_eval: float) -> tuple[float, float]:
        """Return the cached global axial-flexural centroid."""
        z_eval = float(z_eval)

        if z_eval not in field_cache:
            analysis = section_full_analysis(
                section_field.section(z_eval),
                compute_vroark=False,
            )

            field_cache[z_eval] = (
                float(analysis["Cx"]),
                float(analysis["Cy"]),
            )

        return field_cache[z_eval]

    def _sample_derivative(step: float) -> dict[str, object]:
        """Evaluate the centroid derivative with a second-order scheme."""
        step = float(step)

        if not math.isfinite(step) or step <= 0.0:
            raise ValueError("dz must be a finite positive number.")

        left = z - z_start
        right = z_end - z

        at_start = left <= coordinate_tolerance
        at_end = right <= coordinate_tolerance

        Cx_0, Cy_0 = _global_centroid(z)

        if not at_start and not at_end:
            h = min(step, left, right)

            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Centroid derivative step is too small at z={z}."
                )

            Cx_minus, Cy_minus = _global_centroid(z - h)
            Cx_plus, Cy_plus = _global_centroid(z + h)

            dCx_dz = (Cx_plus - Cx_minus) / (2.0 * h)
            dCy_dz = (Cy_plus - Cy_minus) / (2.0 * h)
            scheme = "central_second_order"

        elif at_start:
            h = min(step, 0.5 * right)

            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Centroid derivative step is too small at z={z}."
                )

            Cx_1, Cy_1 = _global_centroid(z + h)
            Cx_2, Cy_2 = _global_centroid(z + 2.0 * h)

            dCx_dz = (
                -3.0 * Cx_0
                + 4.0 * Cx_1
                - Cx_2
            ) / (2.0 * h)

            dCy_dz = (
                -3.0 * Cy_0
                + 4.0 * Cy_1
                - Cy_2
            ) / (2.0 * h)

            scheme = "forward_second_order"

        else:
            h = min(step, 0.5 * left)

            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Centroid derivative step is too small at z={z}."
                )

            Cx_1, Cy_1 = _global_centroid(z - h)
            Cx_2, Cy_2 = _global_centroid(z - 2.0 * h)

            dCx_dz = (
                3.0 * Cx_0
                - 4.0 * Cx_1
                + Cx_2
            ) / (2.0 * h)

            dCy_dz = (
                3.0 * Cy_0
                - 4.0 * Cy_1
                + Cy_2
            ) / (2.0 * h)

            scheme = "backward_second_order"

        return {
            "Cx": float(Cx_0),
            "Cy": float(Cy_0),
            "dCx_dz": float(dCx_dz),
            "dCy_dz": float(dCy_dz),
            "step": float(h),
            "derivative_scheme": scheme,
        }

    def _converged_derivative() -> dict[str, object]:
        """Refine the centroid derivative until both components converge."""
        previous = _sample_derivative(0.05 * length)

        for refinement in range(1, max_refinements + 1):
            next_step = 0.5 * float(previous["step"])

            if next_step <= minimum_step:
                raise RuntimeError(
                    "Global centroid derivative convergence reached the "
                    f"numerical step limit at z={z}."
                )

            current = _sample_derivative(next_step)

            old_x = float(previous["dCx_dz"])
            old_y = float(previous["dCy_dz"])
            new_x = float(current["dCx_dz"])
            new_y = float(current["dCy_dz"])

            change_x = abs(new_x - old_x)
            change_y = abs(new_y - old_y)

            tolerance_x = (
                derivative_atol
                + derivative_rtol * max(abs(new_x), abs(old_x))
            )

            tolerance_y = (
                derivative_atol
                + derivative_rtol * max(abs(new_y), abs(old_y))
            )

            if (
                change_x <= tolerance_x
                and change_y <= tolerance_y
            ):
                current.update(
                    {
                        "derivative_dz_mode": "automatic_convergence",
                        "derivative_converged": True,
                        "derivative_refinements": refinement,
                        "derivative_change_x": float(change_x),
                        "derivative_change_y": float(change_y),
                    }
                )
                return current

            previous = current

        raise RuntimeError(
            "Global centroid derivative convergence was not reached within "
            f"max_refinements={max_refinements} at z={z}."
        )

    def _scale_extrema(
        row: dict[str, object],
        *,
        scale: float,
        prefix: str,
    ) -> dict[str, float]:
        """Scale signed Navier extrema by one centroid derivative."""
        candidates = (
            (
                float(row["sigma_min"]) * scale,
                float(row["x_min"]),
                float(row["y_min"]),
            ),
            (
                float(row["sigma_max"]) * scale,
                float(row["x_max"]),
                float(row["y_max"]),
            ),
        )

        minimum = min(candidates, key=lambda item: item[0])
        maximum = max(candidates, key=lambda item: item[0])

        return {
            f"{prefix}_min": float(minimum[0]),
            f"x_{prefix}_min": float(minimum[1]),
            f"y_{prefix}_min": float(minimum[2]),
            f"{prefix}_max": float(maximum[0]),
            f"x_{prefix}_max": float(maximum[1]),
            f"y_{prefix}_max": float(maximum[2]),
        }

    if dz is None:
        derivative = _converged_derivative()
    else:
        derivative = _sample_derivative(float(dz))
        derivative.update(
            {
                "derivative_dz_mode": "explicit",
                "derivative_converged": None,
                "derivative_refinements": 0,
                "derivative_change_x": float("nan"),
                "derivative_change_y": float("nan"),
            }
        )

    dCx_dz = float(derivative["dCx_dz"])
    dCy_dz = float(derivative["dCy_dz"])

    # Only the flexural part of the Navier field is used.
    navier_rows = analyse_polygon_navier_stress(
        section_field=section_field,
        z=z,
        N=0.0,
        Mx=Mx,
        My=My,
    )

    polygon_rows: list[dict[str, object]] = []

    for navier_row in navier_rows:
        tau_x = _scale_extrema(
            navier_row,
            scale=dCx_dz,
            prefix="tau_x",
        )

        tau_y = _scale_extrema(
            navier_row,
            scale=dCy_dz,
            prefix="tau_y",
        )

        candidates = (
            (
                "x",
                "min",
                tau_x["tau_x_min"],
                tau_x["x_tau_x_min"],
                tau_x["y_tau_x_min"],
            ),
            (
                "x",
                "max",
                tau_x["tau_x_max"],
                tau_x["x_tau_x_max"],
                tau_x["y_tau_x_max"],
            ),
            (
                "y",
                "min",
                tau_y["tau_y_min"],
                tau_y["x_tau_y_min"],
                tau_y["y_tau_y_min"],
            ),
            (
                "y",
                "max",
                tau_y["tau_y_max"],
                tau_y["x_tau_y_max"],
                tau_y["y_tau_y_max"],
            ),
        )

        direction, bound, value, x_value, y_value = max(
            candidates,
            key=lambda item: abs(float(item[2])),
        )

        polygon_rows.append(
            {
                "idx": int(navier_row["idx"]),
                "name": str(navier_row["name"]),
                "weightabs": float(navier_row["weightabs"]),
                "sigma_min": float(navier_row["sigma_min"]),
                "x_sigma_min": float(navier_row["x_min"]),
                "y_sigma_min": float(navier_row["y_min"]),
                "sigma_max": float(navier_row["sigma_max"]),
                "x_sigma_max": float(navier_row["x_max"]),
                "y_sigma_max": float(navier_row["y_max"]),
                "sigma_extreme": float(navier_row["sigma_extreme"]),
                "x_sigma_extreme": float(navier_row["x"]),
                "y_sigma_extreme": float(navier_row["y"]),
                **tau_x,
                **tau_y,
                "tau_governing": float(value),
                "tau_governing_direction": str(direction),
                "tau_governing_bound": str(bound),
                "x_tau_governing": float(x_value),
                "y_tau_governing": float(y_value),
            }
        )

    section_result: dict[str, object] = {
        "z": z,
        "Mx": Mx,
        "My": My,
        "Cx": float(derivative["Cx"]),
        "Cy": float(derivative["Cy"]),
        "dCx_dz": dCx_dz,
        "dCy_dz": dCy_dz,
    }

    if debug:
        section_result.update(
            {
                "derivative_step": float(derivative["step"]),
                "derivative_scheme": str(
                    derivative["derivative_scheme"]
                ),
                "derivative_dz_mode": str(
                    derivative["derivative_dz_mode"]
                ),
                "derivative_converged": derivative[
                    "derivative_converged"
                ],
                "derivative_refinements": int(
                    derivative["derivative_refinements"]
                ),
                "derivative_change_x": float(
                    derivative["derivative_change_x"]
                ),
                "derivative_change_y": float(
                    derivative["derivative_change_y"]
                ),
            }
        )

    return {
        "section": section_result,
        "polygons": polygon_rows,
    }


def _section_active_bbox(section: Section) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []

    for poly in section.polygons:
        if not _jourawski_polygon_is_active_for_b(poly):
            continue

        for vertex in poly.vertices:
            xs.append(float(vertex.x))
            ys.append(float(vertex.y))

    if not xs or not ys:
        raise ValueError(
            "No active polygon with non-zero weightabs available for Jourawski scan."
        )

    return min(xs), max(xs), min(ys), max(ys)

def _jourawski_global_axis_scan(
    *,
    original_section: Section,
    transformed_section: Section,
    axis: str,
    coord_min: float,
    coord_max: float,
    num_subdivisions: int,
    Cx: float,
    Cy: float,
    dbx: float,
    dby: float,
) -> list[dict[str, object]]:
    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'.")

    n = int(num_subdivisions)

    if n < 1:
        raise ValueError("num_subdivisions must be >= 1.")
    
    span = float(coord_max) - float(coord_min)
    if abs(span) <= _tol.EPS_L:
        return []

    delta = span / n
    out: list[dict[str, object]] = []

    for i in range(n):
        coord = float(coord_min) + (i + 0.5) * delta
        value = _jourawski_value_at_coord(
            original_section=original_section,
            transformed_section=transformed_section,
            axis=axis,
            coord=coord,
            Cx=Cx,
            Cy=Cy,
            dbx=dbx,
            dby=dby,
        )
        if value is not None:
            out.append(value)

    return out


def _jourawski_value_at_coord(
    *,
    original_section: Section,
    transformed_section: Section,
    axis: str,
    coord: float,
    Cx: float,
    Cy: float,
    dbx: float,
    dby: float,
) -> dict[str, object] | None:
    """
    Compute the mean Jourawski stress for one global cut.

    The stress value is global for the full active cut width b_total.
    The localization is per intersected polygon segment and is stored in
    cut_segments. The grouped polygon rows then receive the same tau but their
    own segment midpoint coordinates.
    """
    b_total, cut_segments = _section_active_cut_width_and_polygons(
        section=original_section,
        axis=axis,
        coord=coord,
    )
    if abs(b_total) <= _tol.EPS_L:
        return None

    Sx_part, Sy_part = _section_partial_first_moments(
        section=transformed_section,
        axis=axis,
        coord=coord,
        Cx=Cx,
        Cy=Cy,
    )

    shear_flow = dbx * Sx_part + dby * Sy_part
    tau_reference = shear_flow / b_total


    shear_length_sum = 0.0
    for cut_segment in cut_segments:
        shear_weightabs = float(cut_segment["shear_weightabs"])
        length = float(cut_segment["length"])
        shear_length_sum += shear_weightabs * length

    if abs(shear_length_sum) <= _tol.EPS_L:
        return None

    localized_segments: list[dict[str, object]] = []
    for seg in cut_segments:
        shear_weightabs = float(seg["shear_weightabs"])
        tau_local = tau_reference * b_total * shear_weightabs / shear_length_sum

        localized = dict(seg)
        localized["tau"] = float(tau_local)
        localized["tau_factor"] = float(b_total * shear_weightabs / shear_length_sum)
        localized["shear_length_sum"] = float(shear_length_sum)
        localized_segments.append(localized)

    return {
        "tau": float(tau_reference),
        "x": float("nan"),
        "y": float("nan"),
        "coord": float(coord),
        "axis": str(axis),
        "tau_reference": float(tau_reference),
        "b_weighted": float(b_total),
        "Sx_part": float(Sx_part),
        "Sy_part": float(Sy_part),
        "cut_segments": tuple(localized_segments),
        "polygon_indices": tuple(int(seg["polygon_idx"]) for seg in localized_segments),
    }



def _section_active_cut_width_and_polygons(
    *,
    section: Section,
    axis: str,
    coord: float,
) -> tuple[float, list[dict[str, object]]]:
    """
    Return the total active cut width and one localization record per polygon.

    For axis == "y", the cut is horizontal Y = coord. The segment endpoints are
    x-like values, and the marker is placed at their length-weighted midpoint.

    For axis == "x", the cut is vertical X = coord. The segment endpoints are
    y-like values, and the marker is placed at their length-weighted midpoint.
    """
    total = 0.0
    cut_segments: list[dict[str, object]] = []

    for idx, poly in enumerate(section.polygons):
        if not _jourawski_polygon_is_active_for_b(poly):
            continue

        segments = _polygon_line_segments(poly=poly, axis=axis, coord=coord)
        if not segments:
            continue

        length = sum(abs(b - a) for a, b in segments)
        if length <= _tol.EPS_L:
            continue

        midpoint_other = sum(
            abs(b - a) * 0.5 * (float(a) + float(b))
            for a, b in segments
        ) / length

        if axis == "x":
            x_marker = float(coord)
            y_marker = float(midpoint_other)
            segment_x0 = float(coord)
            segment_y0 = float(min(min(a, b) for a, b in segments))
            segment_x1 = float(coord)
            segment_y1 = float(max(max(a, b) for a, b in segments))
        elif axis == "y":
            x_marker = float(midpoint_other)
            y_marker = float(coord)
            segment_x0 = float(min(min(a, b) for a, b in segments))
            segment_y0 = float(coord)
            segment_x1 = float(max(max(a, b) for a, b in segments))
            segment_y1 = float(coord)
        else:
            raise ValueError("axis must be 'x' or 'y'.")

        shear_weightabs = _jourawski_polygon_shear_weightabs(poly)

        total += length
        cut_segments.append(
            {
                "polygon_idx": int(idx),
                "length": float(length),
                "shear_weightabs": float(shear_weightabs),
                "x": float(x_marker),
                "y": float(y_marker),
                "segment_x0": float(segment_x0),
                "segment_y0": float(segment_y0),
                "segment_x1": float(segment_x1),
                "segment_y1": float(segment_y1),
                "segments_other": tuple((float(a), float(b)) for a, b in segments),
            }
        )

    return float(total), cut_segments


def _group_scan_values_by_polygon(
    *,
    scan_values: list[dict[str, object]],
    polygon_count: int,
) -> list[list[dict[str, object]]]:
    """
    Assign global cut values to crossed polygons with per-polygon localization.

    Each cut has one tau value. Each crossed polygon receives a localized copy
    whose x/y are the midpoint of that polygon's cut segment.
    """
    grouped: list[list[dict[str, object]]] = [[] for _ in range(int(polygon_count))]

    for value in scan_values:
        cut_segments = value.get("cut_segments", ())
        for segment in cut_segments:  # type: ignore[union-attr]
            idx = int(segment["polygon_idx"])
            if not (0 <= idx < int(polygon_count)):
                continue

            localized = dict(value)
            localized.pop("cut_segments", None)
            localized["polygon_indices"] = (idx,)
            localized["tau"] = float(segment["tau"])
            localized["tau_factor"] = float(segment["tau_factor"])
            localized["shear_weightabs"] = float(segment["shear_weightabs"])
            localized["shear_length_sum"] = float(segment["shear_length_sum"])
            localized["x"] = float(segment["x"])
            localized["y"] = float(segment["y"])
            localized["segment_length"] = float(segment["length"])
            localized["segment_x0"] = float(segment["segment_x0"])
            localized["segment_y0"] = float(segment["segment_y0"])
            localized["segment_x1"] = float(segment["segment_x1"])
            localized["segment_y1"] = float(segment["segment_y1"])

            grouped[idx].append(localized)

    return grouped


def _jourawski_polygon_shear_weightabs(poly: Polygon) -> float:
    """Return the sampled shear carrier used for local cut redistribution."""
    for attr_name in ("shear_weightabs", "shear_w"):
        if not hasattr(poly, attr_name):
            continue
        value = getattr(poly, attr_name)
        if value is None:
            continue
        value = float(value)
        if math.isfinite(value):
            return value

    return float(getattr(poly, "weightabs", getattr(poly, "weight", 0.0)))


def _jourawski_polygon_is_active_for_b(poly: Polygon) -> bool:
    weightabs = getattr(poly, "weightabs", None)
    if weightabs is None:
        return False
    weightabs = float(weightabs)
    return math.isfinite(weightabs) and abs(weightabs) > _tol.EPS_A


def _jourawski_normalized_section(section: Section) -> tuple[Section, float, list[float]]:
    weight_ref = _jourawski_reference_weightabs(section)

    transformed_polygons = []
    weight_norm_by_idx: list[float] = []

    for poly in section.polygons:
        weight_norm = float(poly.weight) / weight_ref
        weight_norm_by_idx.append(weight_norm)

        transformed_polygons.append(
            Polygon(
                vertices=poly.vertices,
                weight=weight_norm,
                name=getattr(poly, "name", None),
            )
        )

    return (
        Section(polygons=tuple(transformed_polygons), z=float(section.z)),
        float(weight_ref),
        weight_norm_by_idx,
    )


def _jourawski_reference_weightabs(section: Section) -> float:
    for poly in section.polygons:
        w = float(poly.weightabs)
        if math.isfinite(w) and w > _tol.EPS_A:
            return w

    raise ValueError("No finite non-zero polygon weight available for normalization.")


def _section_partial_first_moments(
    *,
    section: Section,
    axis: str,
    coord: float,
    Cx: float,
    Cy: float,
) -> tuple[float, float]:
    Sx_part = 0.0
    Sy_part = 0.0

    for poly in section.polygons:
        clipped = _clip_polygon_half_plane(poly=poly, axis=axis, coord=coord)
        if len(clipped) < 3:
            continue

        area_part_raw = _polygon_area_from_points(clipped)
        if abs(area_part_raw) <= _tol.EPS_A:
            continue

        clipped_poly = Polygon(
            vertices=tuple(clipped),
            weight=float(poly.weight),
            name=getattr(poly, "name", None),
        )

        from .section_field import polygon_area_centroid

        area_part, (cx_part, cy_part) = polygon_area_centroid(clipped_poly)
        if abs(area_part) <= _tol.EPS_A:
            continue

        Sx_part += area_part * (cx_part - Cx)
        Sy_part += area_part * (cy_part - Cy)

    return float(Sx_part), float(Sy_part)


def _clip_polygon_half_plane(
    *,
    poly: Polygon,
    axis: str,
    coord: float,
) -> list[Pt]:
    verts = poly.vertices
    n = len(verts)
    if n < 3:
        return []

    clipped: list[Pt] = []

    for i in range(n):
        p1 = verts[i]
        p2 = verts[(i + 1) % n]

        c1 = float(p1.x if axis == "x" else p1.y)
        c2 = float(p2.x if axis == "x" else p2.y)

        p1_in = c1 >= coord - _tol.EPS_L
        p2_in = c2 >= coord - _tol.EPS_L

        t = _cut_edge_t(c1, c2, coord)

        if p1_in and p2_in:
            clipped.append(p2)

        elif p1_in and not p2_in:
            if t is not None:
                clipped.append(_interpolate_point_on_segment(p1, p2, t))

        elif (not p1_in) and p2_in:
            if t is not None:
                clipped.append(_interpolate_point_on_segment(p1, p2, t))
            clipped.append(p2)

    return clipped

def _interpolate_point_on_segment(p1: Pt, p2: Pt, t: float) -> Pt:
    return Pt(
        float(p1.x) + float(t) * (float(p2.x) - float(p1.x)),
        float(p1.y) + float(t) * (float(p2.y) - float(p1.y)),
    )


def _polygon_area_from_points(points: list[Pt]) -> float:
    if len(points) < 3:
        return 0.0

    a2 = 0.0
    n = len(points)

    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        a2 += float(p0.x) * float(p1.y) - float(p1.x) * float(p0.y)

    return 0.5 * a2


def _cut_edge_t(c1: float, c2: float, coord: float) -> float | None:
    if abs(c1 - coord) <= _tol.EPS_L and abs(c2 - coord) <= _tol.EPS_L:
        return None

    crosses = (c1 <= coord < c2) or (c2 <= coord < c1)
    if not crosses:
        return None

    denom = c2 - c1
    if abs(denom) <= _tol.EPS_L:
        return None

    return float((coord - c1) / denom)

def _polygon_line_segments(
    *,
    poly: Polygon,
    axis: str,
    coord: float,
) -> list[tuple[float, float]]:
    verts = poly.vertices
    n = len(verts)
    if n < 3:
        return []

    values: list[float] = []

    for i in range(n):
        p1 = verts[i]
        p2 = verts[(i + 1) % n]

        c1 = float(p1.x if axis == "x" else p1.y)
        c2 = float(p2.x if axis == "x" else p2.y)
        o1 = float(p1.y if axis == "x" else p1.x)
        o2 = float(p2.y if axis == "x" else p2.x)

        t = _cut_edge_t(c1, c2, coord)
        if t is None:
            continue

        values.append(float(o1 + t * (o2 - o1)))

    values = _unique_sorted(values)
    if len(values) < 2:
        return []

    segments: list[tuple[float, float]] = []
    for a, b in zip(values[0::2], values[1::2]):
        if abs(b - a) > _tol.EPS_L:
            segments.append((float(a), float(b)))

    return segments



def _unique_sorted(values: list[float]) -> list[float]:
    values = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return []

    out = [values[0]]
    for v in values[1:]:
        if abs(v - out[-1]) > _tol.EPS_L:
            out.append(v)
    return out


def _mean_scan_tau(values: list[dict[str, object]]) -> float:
    if not values:
        return float("nan")
    tau_values = [float(v["tau"]) for v in values]
    return float(sum(tau_values) / len(tau_values))


def _empty_scan_value() -> dict[str, object]:
    return {
        "tau": float("nan"),
        "x": float("nan"),
        "y": float("nan"),
        "coord": float("nan"),
        "axis": "",
        "tau_reference": float("nan"),
        "b_weighted": float("nan"),
        "Sx_part": float("nan"),
        "Sy_part": float("nan"),
        "polygon_indices": tuple(),
        "segment_length": float("nan"),
        "segment_x0": float("nan"),
        "segment_y0": float("nan"),
        "segment_x1": float("nan"),
        "segment_y1": float("nan"),
        "shear_weightabs": float("nan"),
        "shear_length_sum": float("nan"),
        "tau_factor": float("nan"),
    }

def _min_scan_value(values: list[dict[str, object]]) -> dict[str, object]:
    if not values:
        return _empty_scan_value()
    return min(values, key=lambda r: float(r["tau"]))


def _max_scan_value(values: list[dict[str, object]]) -> dict[str, object]:
    if not values:
        return _empty_scan_value()
    return max(values, key=lambda r: float(r["tau"]))


def analyse_polygon_jourawski_shear_stress(
    section_field,
    z: float,
    Tx: float,
    Ty: float,
    *,
    num_sudx: int = 30,
    num_sudy: int = 30,
    debug: bool = False,
) -> list[dict[str, object]]:
    """
    Compute polygon-wise Jourawski shear-stress envelopes from global section scans.

    Conventions
    -----------
    - Tx is the shear component associated with My.
    - Ty is the shear component associated with Mx.
    - tau_x is evaluated from vertical cuts x = constant.
    - tau_y is evaluated from horizontal cuts y = constant.

    Scan rule
    ---------
    The scan teeth are the minimum and maximum coordinates of every polygon
    bounding box, limited to the active-section bounding box.

    Along x:
        x_teeth = sorted unique polygon xmin/xmax coordinates

    Along y:
        y_teeth = sorted unique polygon ymin/ymax coordinates

    The scan coordinates are the union of two independent schemes.

    Global uniform scan:
        num_sudx cell centres over the full active x bounding-box interval
        num_sudy cell centres over the full active y bounding-box interval

    Local one-sided tooth concentration:
        deltaX_i = interval_length_x / (2 * num_sudx**2)
        deltaY_i = interval_length_y / (2 * num_sudy**2)

    For every interval between two consecutive teeth, additional coordinates
    are placed at geometrically increasing distances:

        delta, 2*delta, 4*delta, ...

    from both interval ends. Exact tooth coordinates are not evaluated.
    Duplicate coordinates from the global and local schemes are
    tolerance-deduplicated.

    Polygon bounding boxes are used only to construct the scan coordinates.
    The Jourawski calculation, active cut width, partial first moments and
    shear-carrier redistribution remain unchanged.

    For each cut, Jourawski returns one mean shear stress over the full active
    intersection length b. That line-average value is then redistributed among
    the crossed polygon segments using their sampled shear carrier
    ``shear_weightabs`` and their actual segment length on the cut.

    For one cut:
        tau_i = tau_ref * b_total * G_i / sum(G_j * b_j)

    where G_i is the polygon ``shear_weightabs`` and b_i is the segment length
    of the same cut inside polygon i. This preserves the cut resultant:
        sum(tau_i * b_i) = tau_ref * b_total.
    """
    from .section_field import section_properties

    num_sudx = int(num_sudx)
    num_sudy = int(num_sudy)
    if num_sudx < 1:
        raise ValueError("num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("num_sudy must be >= 1.")

    section = section_field.section(float(z))
    transformed_section, weight_ref, weight_norm_by_idx = _jourawski_normalized_section(
        section
    )

    props = section_properties(transformed_section)
    A = float(props["A"])
    Cx = float(props["Cx"])
    Cy = float(props["Cy"])
    Ix = float(props["Ix"])
    Iy = float(props["Iy"])
    Ixy = float(props["Ixy"])

    if abs(A) <= _tol.EPS_A:
        raise ValueError(f"Zero transformed section area at z={float(z)}.")

    D = Ix * Iy - Ixy * Ixy
    if abs(D) <= _tol.EPS_K_ATOL:
        raise ValueError(
            f"Singular transformed bending inertia matrix at z={float(z)}."
        )

    # Same algebraic matrix used in analyse_polygon_navier_stress(), with
    # dMy/ds = Tx and dMx/ds = Ty.
    dbx = (float(Tx) * Ix - float(Ty) * Ixy) / D
    dby = (float(Ty) * Iy - float(Tx) * Ixy) / D

    xmin, xmax, ymin, ymax = _section_active_bbox(section)

    def _sorted_unique_coords(values: list[float]) -> list[float]:
        finite_values = sorted(
            float(value)
            for value in values
            if math.isfinite(float(value))
        )

        unique_values: list[float] = []
        for value in finite_values:
            if (
                not unique_values
                or abs(value - unique_values[-1]) > _tol.EPS_L
            ):
                unique_values.append(value)

        return unique_values

    def _axis_teeth(
        *,
        axis: str,
        coord_min: float,
        coord_max: float,
    ) -> list[float]:
        if axis not in ("x", "y"):
            raise ValueError("axis must be 'x' or 'y'.")

        teeth: list[float] = [float(coord_min), float(coord_max)]

        for poly in section.polygons:
            polygon_coords = [
                float(vertex.x if axis == "x" else vertex.y)
                for vertex in poly.vertices
            ]
            if not polygon_coords:
                continue

            polygon_min = min(polygon_coords)
            polygon_max = max(polygon_coords)

            # The global active-section box remains the scan domain.
            if (
                polygon_max < float(coord_min) - _tol.EPS_L
                or polygon_min > float(coord_max) + _tol.EPS_L
            ):
                continue

            teeth.append(
                min(float(coord_max), max(float(coord_min), polygon_min))
            )
            teeth.append(
                min(float(coord_max), max(float(coord_min), polygon_max))
            )

        unique_teeth = _sorted_unique_coords(teeth)

        if len(unique_teeth) < 2:
            return []

        return unique_teeth

    def _global_uniform_coords(
        *,
        coord_min: float,
        coord_max: float,
        teeth: list[float],
        resolution: int,
    ) -> list[float]:
        """
        Generate one global uniform cell-centre grid over the active axis span.

        Coordinates that coincide with a tooth within EPS_L are excluded so
        that tooth values are always approached one-sidedly.
        """
        a = float(coord_min)
        b = float(coord_max)
        span = b - a
        if span <= _tol.EPS_L:
            return []

        n = int(resolution)
        step = span / n

        coords: list[float] = []
        for k in range(n):
            coord = a + (k + 0.5) * step
            if any(abs(coord - tooth) <= _tol.EPS_L for tooth in teeth):
                continue
            coords.append(coord)

        return _sorted_unique_coords(coords)

    def _local_concentrated_coords_between_teeth(
        *,
        teeth: list[float],
        resolution: int,
    ) -> list[float]:
        """
        Generate geometrically concentrated one-sided coordinates near teeth.

        Every tooth interval [a, b] is treated independently. The nearest
        coordinate to each interval end is:

            edge_delta = max(
                (b - a) / (2 * resolution**2),
                10 * EPS_L,
            )

        Additional coordinates are placed at:

            edge_delta, 2*edge_delta, 4*edge_delta, ...

        from both ends while remaining strictly inside the interval.

        Because adjacent intervals generally have different spans, an internal
        tooth receives two independent one-sided coordinate sequences.
        """
        coords: list[float] = []
        n = int(resolution)

        for coord_0, coord_1 in zip(teeth[:-1], teeth[1:]):
            a = float(coord_0)
            b = float(coord_1)
            span = b - a
            if span <= _tol.EPS_L:
                continue

            half_span = 0.5 * span
            edge_delta = max(
                span / (2.0 * n * n),
                10.0 * _tol.EPS_L,
            )

            offset = edge_delta
            while offset < half_span - _tol.EPS_L:
                coords.append(a + offset)
                coords.append(b - offset)
                offset *= 2.0

        return _sorted_unique_coords(coords)

    def _scan_axis(
        *,
        axis: str,
        coords: list[float],
    ) -> list[dict[str, object]]:
        scan_values: list[dict[str, object]] = []

        for coord in coords:
            value = _jourawski_value_at_coord(
                original_section=section,
                transformed_section=transformed_section,
                axis=axis,
                coord=float(coord),
                Cx=Cx,
                Cy=Cy,
                dbx=dbx,
                dby=dby,
            )
            if value is not None:
                scan_values.append(value)

        return scan_values

    x_teeth = _axis_teeth(
        axis="x",
        coord_min=xmin,
        coord_max=xmax,
    )
    y_teeth = _axis_teeth(
        axis="y",
        coord_min=ymin,
        coord_max=ymax,
    )

    x_uniform_coords = _global_uniform_coords(
        coord_min=xmin,
        coord_max=xmax,
        teeth=x_teeth,
        resolution=num_sudx,
    )
    y_uniform_coords = _global_uniform_coords(
        coord_min=ymin,
        coord_max=ymax,
        teeth=y_teeth,
        resolution=num_sudy,
    )

    x_tooth_coords = _local_concentrated_coords_between_teeth(
        teeth=x_teeth,
        resolution=num_sudx,
    )
    y_tooth_coords = _local_concentrated_coords_between_teeth(
        teeth=y_teeth,
        resolution=num_sudy,
    )

    x_coords = _sorted_unique_coords(x_uniform_coords + x_tooth_coords)
    y_coords = _sorted_unique_coords(y_uniform_coords + y_tooth_coords)

    if debug:
        print(
            "[JOURAWSKI SCAN START]",
            f"z={float(z):.12e}",
            f"Tx={float(Tx):.12e}",
            f"Ty={float(Ty):.12e}",
            f"num_sudx_global_resolution={num_sudx}",
            f"num_sudy_global_resolution={num_sudy}",
            f"xmin={xmin:.12e}",
            f"xmax={xmax:.12e}",
            f"ymin={ymin:.12e}",
            f"ymax={ymax:.12e}",
            f"x_teeth={len(x_teeth)}",
            f"y_teeth={len(y_teeth)}",
            f"x_intervals={max(0, len(x_teeth) - 1)}",
            f"y_intervals={max(0, len(y_teeth) - 1)}",
            f"x_uniform_cuts={len(x_uniform_coords)}",
            f"y_uniform_cuts={len(y_uniform_coords)}",
            f"x_tooth_cuts={len(x_tooth_coords)}",
            f"y_tooth_cuts={len(y_tooth_coords)}",
            f"x_cuts_total={len(x_coords)}",
            f"y_cuts_total={len(y_coords)}",
            flush=True,
        )

    tau_x_scan = _scan_axis(
        axis="x",
        coords=x_coords,
    )
    tau_y_scan = _scan_axis(
        axis="y",
        coords=y_coords,
    )

    values_x_by_polygon = _group_scan_values_by_polygon(
        scan_values=tau_x_scan,
        polygon_count=len(section.polygons),
    )
    values_y_by_polygon = _group_scan_values_by_polygon(
        scan_values=tau_y_scan,
        polygon_count=len(section.polygons),
    )

    if not (
        len(section.polygons)
        == len(transformed_section.polygons)
        == len(weight_norm_by_idx)
        == len(section_field.s0.polygons)
    ):
        raise ValueError("Inconsistent polygon count in Jourawski section data.")

    if debug:
        print(
            "[JOURAWSKI SCAN AXIS DONE]",
            f"z={float(z):.12e}",
            "axis=x",
            f"cuts_valid={len(tau_x_scan)}",
            f"cuts_total={len(x_coords)}",
            flush=True,
        )
        print(
            "[JOURAWSKI SCAN AXIS DONE]",
            f"z={float(z):.12e}",
            "axis=y",
            f"cuts_valid={len(tau_y_scan)}",
            f"cuts_total={len(y_coords)}",
            flush=True,
        )

    rows: list[dict[str, object]] = []

    for idx, _poly in enumerate(transformed_section.polygons):
        original_poly = section.polygons[idx]
        name_s0 = str(section_field.s0.polygons[idx].name)
        weight_raw = float(original_poly.weight)
        weight_norm = float(weight_norm_by_idx[idx])

        tau_x_values = values_x_by_polygon[idx]
        tau_y_values = values_y_by_polygon[idx]

        tau_x_min = _min_scan_value(tau_x_values)
        tau_x_max = _max_scan_value(tau_x_values)
        tau_y_min = _min_scan_value(tau_y_values)
        tau_y_max = _max_scan_value(tau_y_values)

        if debug:
            print(
                "[JOURAWSKI SCAN POLYGON DONE]",
                f"z={float(z):.12e}",
                f"idx={idx}",
                f"name={name_s0}",
                f"scan_count_x={len(tau_x_values)}",
                f"scan_count_y={len(tau_y_values)}",
                f"grid_x={len(x_coords)}",
                f"grid_y={len(y_coords)}",
                flush=True,
            )

        rows.append(
            {
                "idx": int(idx),
                "name": name_s0,
                "weight": weight_raw,
                "weight_ref": float(weight_ref),
                "weight_norm": weight_norm,

                "tau_x_min": tau_x_min["tau"],
                "x_tau_x_min": tau_x_min["x"],
                "y_tau_x_min": tau_x_min["y"],

                "tau_x_max": tau_x_max["tau"],
                "x_tau_x_max": tau_x_max["x"],
                "y_tau_x_max": tau_x_max["y"],

                "tau_y_min": tau_y_min["tau"],
                "x_tau_y_min": tau_y_min["x"],
                "y_tau_y_min": tau_y_min["y"],

                "tau_y_max": tau_y_max["tau"],
                "x_tau_y_max": tau_y_max["x"],
                "y_tau_y_max": tau_y_max["y"],
                "coord_tau_y_max": tau_y_max["coord"],
                "tau_reference_y_max": tau_y_max["tau_reference"],
                "b_weighted_y_max": tau_y_max["b_weighted"],
                "Sx_part_y_max": tau_y_max["Sx_part"],
                "Sy_part_y_max": tau_y_max["Sy_part"],

                "tau_x_mean": _mean_scan_tau(tau_x_values),
                "tau_y_mean": _mean_scan_tau(tau_y_values),
                "scan_count_x": int(len(tau_x_values)),
                "scan_count_y": int(len(tau_y_values)),
                "grid_x": int(len(x_coords)),
                "grid_y": int(len(y_coords)),
                "converged_x": bool(tau_x_values),
                "converged_y": bool(tau_y_values),
                "relative_change_x": float("nan"),
                "relative_change_y": float("nan"),
            }
        )

    if debug:
        print(
            "[JOURAWSKI SCAN DONE]",
            f"z={float(z):.12e}",
            f"rows={len(rows)}",
            f"cuts_x={len(tau_x_scan)}",
            f"cuts_y={len(tau_y_scan)}",
            flush=True,
        )


    return rows


def _jourawski_v2_positive_half_plane_resultant(
    *,
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    axis: str,
    coord: float,
) -> dict[str, object]:
    """Integrate the Navier longitudinal resultant on one positive half-plane.

    For ``axis == "y"`` the retained region is ``Y >= coord``.
    For ``axis == "x"`` the retained region is ``X >= coord``.

    The integration uses the same affine Navier field as
    :func:`analyse_polygon_navier_stress` and follows the CSF occupied-region
    rule for nested polygons, so direct children are subtracted from the parent
    with the parent Navier field and are then added with their own field.
    """
    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'.")

    z = float(z)
    coord = float(coord)
    state = _navier_section_state(
        section_field=section_field,
        z=z,
        N=float(N),
        Mx=float(Mx),
        My=float(My),
    )
    section = state["section"]

    build_children = getattr(section_field, "build_direct_children_map", None)
    if build_children is None:
        children_map: dict[int, tuple[int, ...]] = {}
    else:
        raw_children = build_children(z)
        if not isinstance(raw_children, dict):
            raise TypeError("build_direct_children_map(z) must return a dict.")
        children_map = {
            int(parent_idx): tuple(int(child_idx) for child_idx in child_indices)
            for parent_idx, child_indices in raw_children.items()
        }

    n_polygons = len(section.polygons)
    total_N = 0.0
    total_area = 0.0

    for idx, poly in enumerate(section.polygons):
        clipped = _clip_polygon_half_plane(
            poly=poly,
            axis=axis,
            coord=coord,
        )
        gross = _navier_resultant_over_points(
            poly=poly,
            points=clipped,
            state=state,
        )

        occupied_N = float(gross["N"])
        occupied_area = float(gross["area"])

        for child_idx in children_map.get(idx, ()):
            if not (0 <= child_idx < n_polygons):
                raise ValueError(
                    f"Invalid child polygon index {child_idx} at z={z}."
                )
            if child_idx == idx:
                raise ValueError(f"Polygon index {idx} cannot contain itself.")

            child_poly = section.polygons[child_idx]
            clipped_child = _clip_polygon_half_plane(
                poly=child_poly,
                axis=axis,
                coord=coord,
            )
            excluded = _navier_resultant_over_points(
                poly=poly,
                points=clipped_child,
                state=state,
            )
            occupied_N -= float(excluded["N"])
            occupied_area -= float(excluded["area"])

        if abs(occupied_area) <= _tol.EPS_A:
            occupied_area = 0.0
        elif occupied_area < -_tol.EPS_A:
            raise ValueError(
                "Negative occupied half-plane area detected for polygon "
                f"idx={idx}, axis={axis}, coord={coord}, z={z}: "
                f"{occupied_area}."
            )

        total_N += occupied_N
        total_area += occupied_area

    return {
        "z": z,
        "axis": axis,
        "coord": coord,
        "N_partial": float(total_N),
        "area_partial": float(total_area),
    }


def analyse_jourawski_shear_stress_v2(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    *,
    dN_dz: float = 0.0,
    num_sudx: int = 30,
    num_sudy: int = 30,
    cut_coords_x: list[float] | tuple[float, ...] | None = None,
    cut_coords_y: list[float] | tuple[float, ...] | None = None,
    dz: float | None = None,
    debug: bool = False,
) -> dict[str, object]:
    """Compute mean shear stress on global Jourawski cuts from dN_partial/dz.

    This is a cut-resultant formulation. It does not reconstruct the complete
    two-dimensional shear-stress field and it does not redistribute the mean
    cut stress with ``shear_weight``.

    For each fixed global cut, define the positive-side Navier resultant

        N_c(z) = integral_{A_c(z)} sigma_zz dA

    with ``A_c = {X >= x_c}`` for a vertical cut and
    ``A_c = {Y >= y_c}`` for a horizontal cut. The cut shear flow is evaluated
    directly from longitudinal equilibrium as

        q_c = dN_c / dz

    and the mean stress is

        tau_mean = q_c / b_c

    where ``b_c`` is the total active intersection length of the cut at the
    requested station.

    The sign ``q_c = +dN_c/dz`` is consistent with the existing Jourawski
    convention because the retained region is always the positive half-plane.
    In a prismatic homogeneous section this reduces to the existing
    Jourawski result.

    The local section-force variation used for the derivative follows the
    existing CSF conventions

        dMy/dz = Tx
        dMx/dz = Ty

    while ``dN_dz`` is explicit and defaults to zero.

    Because ``Section(z)`` and the Navier field are reevaluated at every
    derivative station, the derivative includes changes of geometry, centroid,
    inertia and axial-flexural ``weight`` automatically.
    """
    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)
    dN_dz = float(dN_dz)
    num_sudx = int(num_sudx)
    num_sudy = int(num_sudy)

    if num_sudx < 1:
        raise ValueError("num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("num_sudy must be >= 1.")

    z_start = float(section_field.s0.z)
    z_end = float(section_field.s1.z)
    if z_end <= z_start:
        raise ValueError("The CSF bounds must satisfy s1.z > s0.z.")
    if z < z_start or z > z_end:
        raise ValueError(f"z={z} is outside CSF bounds [{z_start}, {z_end}].")

    length = z_end - z_start
    coordinate_tolerance = max(1.0e-14, 1.0e-12 * length)

    if dz is None:
        step_request = 1.0e-3 * length
    else:
        step_request = float(dz)
        if not math.isfinite(step_request) or step_request <= 0.0:
            raise ValueError("dz must be a finite positive number.")

    section = section_field.section(z)
    xmin, xmax, ymin, ymax = _section_active_bbox(section)

    def _uniform_cell_centres(a: float, b: float, n: int) -> list[float]:
        span = float(b) - float(a)
        if span <= _tol.EPS_L:
            return []
        delta = span / int(n)
        return [float(a) + (i + 0.5) * delta for i in range(int(n))]

    def _explicit_or_uniform_coords(
        values: list[float] | tuple[float, ...] | None,
        *,
        a: float,
        b: float,
        n: int,
    ) -> list[float]:
        if values is None:
            return _uniform_cell_centres(a, b, n)

        finite = sorted(float(value) for value in values if math.isfinite(float(value)))
        unique: list[float] = []
        for value in finite:
            if value < float(a) - _tol.EPS_L or value > float(b) + _tol.EPS_L:
                raise ValueError(
                    f"Cut coordinate {value} is outside active interval [{a}, {b}]."
                )
            if not unique or abs(value - unique[-1]) > _tol.EPS_L:
                unique.append(value)
        return unique

    x_coords = _explicit_or_uniform_coords(
        cut_coords_x,
        a=xmin,
        b=xmax,
        n=num_sudx,
    )
    y_coords = _explicit_or_uniform_coords(
        cut_coords_y,
        a=ymin,
        b=ymax,
        n=num_sudy,
    )

    def _force_state(z_eval: float) -> tuple[float, float, float]:
        ds = float(z_eval) - z
        return (
            N + dN_dz * ds,
            Mx + Ty * ds,
            My + Tx * ds,
        )

    def _partial_resultant(axis: str, coord: float, z_eval: float) -> float:
        N_eval, Mx_eval, My_eval = _force_state(z_eval)
        result = _jourawski_v2_positive_half_plane_resultant(
            section_field=section_field,
            z=z_eval,
            N=N_eval,
            Mx=Mx_eval,
            My=My_eval,
            axis=axis,
            coord=coord,
        )
        return float(result["N_partial"])

    def _derivative(axis: str, coord: float) -> dict[str, object]:
        left = z - z_start
        right = z_end - z
        at_start = left <= coordinate_tolerance
        at_end = right <= coordinate_tolerance

        N0 = _partial_resultant(axis, coord, z)

        if not at_start and not at_end:
            h = min(step_request, left, right)
            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Jourawski v2 derivative step is too small at z={z}."
                )
            Nm = _partial_resultant(axis, coord, z - h)
            Np = _partial_resultant(axis, coord, z + h)
            derivative = (Np - Nm) / (2.0 * h)
            scheme = "central_second_order"
            sampled = {"N_minus": Nm, "N_0": N0, "N_plus": Np}

        elif at_start:
            h = min(step_request, 0.5 * right)
            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Jourawski v2 derivative step is too small at z={z}."
                )
            N1 = _partial_resultant(axis, coord, z + h)
            N2 = _partial_resultant(axis, coord, z + 2.0 * h)
            derivative = (-3.0 * N0 + 4.0 * N1 - N2) / (2.0 * h)
            scheme = "forward_second_order"
            sampled = {"N_0": N0, "N_1": N1, "N_2": N2}

        else:
            h = min(step_request, 0.5 * left)
            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Jourawski v2 derivative step is too small at z={z}."
                )
            N1 = _partial_resultant(axis, coord, z - h)
            N2 = _partial_resultant(axis, coord, z - 2.0 * h)
            derivative = (3.0 * N0 - 4.0 * N1 + N2) / (2.0 * h)
            scheme = "backward_second_order"
            sampled = {"N_0": N0, "N_1": N1, "N_2": N2}

        return {
            "dN_partial_dz": float(derivative),
            "step": float(h),
            "derivative_scheme": scheme,
            **sampled,
        }

    def _scan(axis: str, coords: list[float]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for coord in coords:
            b_total, _segments = _section_active_cut_width_and_polygons(
                section=section,
                axis=axis,
                coord=coord,
            )
            if abs(b_total) <= _tol.EPS_L:
                continue

            derivative = _derivative(axis, coord)
            shear_flow = float(derivative["dN_partial_dz"])
            tau_mean = shear_flow / float(b_total)

            row: dict[str, object] = {
                "axis": axis,
                "coord": float(coord),
                "b_total": float(b_total),
                "shear_flow": float(shear_flow),
                "tau_mean": float(tau_mean),
                "N_partial": float(derivative["N_0"]),
            }
            if debug:
                row.update(derivative)
            rows.append(row)

        return rows

    tau_x_scan = _scan("x", x_coords)
    tau_y_scan = _scan("y", y_coords)

    if debug:
        print(
            "[JOURAWSKI V2 DONE]",
            f"z={z:.12e}",
            f"N={N:.12e}",
            f"Mx={Mx:.12e}",
            f"My={My:.12e}",
            f"Tx={Tx:.12e}",
            f"Ty={Ty:.12e}",
            f"dN_dz={dN_dz:.12e}",
            f"dz={step_request:.12e}",
            f"cuts_x={len(tau_x_scan)}",
            f"cuts_y={len(tau_y_scan)}",
            flush=True,
        )

    return {
        "section": {
            "z": z,
            "N": N,
            "Mx": Mx,
            "My": My,
            "Tx": Tx,
            "Ty": Ty,
            "dN_dz": dN_dz,
            "xmin": float(xmin),
            "xmax": float(xmax),
            "ymin": float(ymin),
            "ymax": float(ymax),
            "dz": float(step_request),
            "formulation": "jourawski_v2_cut_resultant",
            "positive_half_plane": True,
            "uses_shear_weight": False,
        },
        "tau_x_scan": tau_x_scan,
        "tau_y_scan": tau_y_scan,
    }


def _navier_section_state(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
) -> dict[str, object]:
    """Return the complete scalar state required by the general Navier formula.

    This helper centralizes the exact algebra used by
    :func:`analyse_polygon_navier_stress` so subsequent regional integrations
    (including Four-Quadrant resultants) can evaluate the same Navier field
    without duplicating its formulation.
    """
    from .section_field import section_full_analysis

    z = float(z)
    section = section_field.section(z)
    analysis = section_full_analysis(section)

    A = float(analysis["A"])
    Cx = float(analysis["Cx"])
    Cy = float(analysis["Cy"])
    Ix = float(analysis["Ix"])
    Iy = float(analysis["Iy"])
    Ixy = float(analysis["Ixy"])

    D = Ix * Iy - Ixy * Ixy
    if A == 0.0:
        raise ValueError(f"Zero section area at z={z}.")
    if D == 0.0:
        raise ValueError(f"Singular bending inertia matrix at z={z}.")

    axial = float(N) / A
    bx = (float(My) * Ix - float(Mx) * Ixy) / D
    by = (float(Mx) * Iy - float(My) * Ixy) / D

    return {
        "section": section,
        "z": z,
        "A": A,
        "Cx": Cx,
        "Cy": Cy,
        "Ix": Ix,
        "Iy": Iy,
        "Ixy": Ixy,
        "D": float(D),
        "axial": float(axial),
        "bx": float(bx),
        "by": float(by),
    }


def _navier_sigma_at_point(
    *,
    poly: Polygon,
    x: float,
    y: float,
    state: dict[str, object],
) -> float:
    """Evaluate the existing general Navier field at one polygon point."""
    weightabs = float(poly.weightabs)
    axial = float(state["axial"])
    bx = float(state["bx"])
    by = float(state["by"])
    Cx = float(state["Cx"])
    Cy = float(state["Cy"])

    return float(
        weightabs * (
            axial
            + bx * (float(x) - Cx)
            + by * (float(y) - Cy)
        )
    )



def _clip_points_half_plane(
    *,
    points: list[Pt],
    axis: str,
    coord: float,
    keep_positive: bool,
) -> list[Pt]:
    """Clip polygon points against one Cartesian half-plane.

    ``keep_positive=True`` keeps x >= coord or y >= coord.
    ``keep_positive=False`` keeps x <= coord or y <= coord.

    Boundary points are retained on both sides. This is intentional: quadrant
    boundaries have zero area, so it does not alter regional resultants and it
    keeps the clipping numerically stable at vertices lying on a cut.
    """
    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'.")

    if len(points) < 3:
        return []

    coord = float(coord)

    def _value(point: Pt) -> float:
        return float(point.x if axis == "x" else point.y)

    def _inside(value: float) -> bool:
        if keep_positive:
            return value >= coord - _tol.EPS_L
        return value <= coord + _tol.EPS_L

    clipped: list[Pt] = []

    for i, p1 in enumerate(points):
        p2 = points[(i + 1) % len(points)]
        c1 = _value(p1)
        c2 = _value(p2)
        p1_in = _inside(c1)
        p2_in = _inside(c2)

        if p1_in and p2_in:
            clipped.append(p2)
            continue

        if p1_in == p2_in:
            continue

        denom = c2 - c1
        if abs(denom) <= _tol.EPS_L:
            continue

        t = (coord - c1) / denom
        t = min(1.0, max(0.0, float(t)))
        intersection = _interpolate_point_on_segment(p1, p2, t)

        if p1_in and not p2_in:
            clipped.append(intersection)
        else:
            clipped.append(intersection)
            clipped.append(p2)

    return clipped


def _clip_polygon_quadrant(
    *,
    poly: Polygon,
    x: float,
    y: float,
    x_positive: bool,
    y_positive: bool,
) -> list[Pt]:
    """Return the polygon portion contained in one quadrant about (x, y)."""
    points = list(poly.vertices)
    points = _clip_points_half_plane(
        points=points,
        axis="x",
        coord=float(x),
        keep_positive=bool(x_positive),
    )
    if len(points) < 3:
        return []

    points = _clip_points_half_plane(
        points=points,
        axis="y",
        coord=float(y),
        keep_positive=bool(y_positive),
    )
    if len(points) < 3:
        return []

    if abs(_polygon_area_from_points(points)) <= _tol.EPS_A:
        return []

    return points


def _polygon_area_centroid_from_points(
    points: list[Pt],
) -> tuple[float, float, float]:
    """Return signed area and centroid for a clipped polygon point list."""
    if len(points) < 3:
        return 0.0, 0.0, 0.0

    a2 = 0.0
    cx_num = 0.0
    cy_num = 0.0

    for i, p0 in enumerate(points):
        p1 = points[(i + 1) % len(points)]
        cross = (
            float(p0.x) * float(p1.y)
            - float(p1.x) * float(p0.y)
        )
        a2 += cross
        cx_num += (float(p0.x) + float(p1.x)) * cross
        cy_num += (float(p0.y) + float(p1.y)) * cross

    area = 0.5 * a2
    if abs(area) <= _tol.EPS_A or abs(a2) <= 2.0 * _tol.EPS_A:
        return 0.0, 0.0, 0.0

    cx = cx_num / (3.0 * a2)
    cy = cy_num / (3.0 * a2)
    return float(area), float(cx), float(cy)


def _navier_resultant_over_points(
    *,
    poly: Polygon,
    points: list[Pt],
    state: dict[str, object],
) -> dict[str, float]:
    """Integrate the existing affine Navier field exactly over one polygon part."""
    area, cx, cy = _polygon_area_centroid_from_points(points)
    if abs(area) <= _tol.EPS_A:
        return {
            "area": 0.0,
            "cx": float("nan"),
            "cy": float("nan"),
            "N": 0.0,
        }

    sigma_at_centroid = _navier_sigma_at_point(
        poly=poly,
        x=cx,
        y=cy,
        state=state,
    )

    # The Navier field is affine inside each polygon. Therefore its exact area
    # integral equals the polygon area times its value at the polygon centroid.
    resultant = area * sigma_at_centroid

    return {
        "area": float(area),
        "cx": float(cx),
        "cy": float(cy),
        "N": float(resultant),
    }


def _navier_quadrant_resultant(
    *,
    poly: Polygon,
    state: dict[str, object],
    x: float,
    y: float,
    x_positive: bool,
    y_positive: bool,
) -> dict[str, float]:
    """Integrate the Navier field of ``poly`` over one quadrant clip."""
    clipped = _clip_polygon_quadrant(
        poly=poly,
        x=float(x),
        y=float(y),
        x_positive=bool(x_positive),
        y_positive=bool(y_positive),
    )
    return _navier_resultant_over_points(
        poly=poly,
        points=clipped,
        state=state,
    )


def analyse_navier_four_quadrant_resultants(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    x: float,
    y: float,
) -> dict[str, object]:
    """Return Navier longitudinal-force resultants in the four quadrants.

    The point ``(x, y)`` defines two fixed Cartesian cuts of the actual
    ``Section(z)``. The quadrant convention is:

        pp : X >= x, Y >= y
        mp : X <= x, Y >= y
        mm : X <= x, Y <= y
        pm : X >= x, Y <= y

    Each regional resultant is the exact area integral of the same affine
    Navier field used by :func:`analyse_polygon_navier_stress`.

    Polygon containment follows the CSF occupied-region rule:

        occupied(parent) = parent - direct_children(parent)

    Therefore a parent polygon contributes only on its physically occupied
    region, while each child contributes separately with its own ``weightabs``.
    This prevents double counting in nested multi-material sections.

    No shear equilibrium or longitudinal derivative is evaluated here. This
    function only provides the Four-Quadrant Navier resultants at one station.
    """
    z = float(z)
    x = float(x)
    y = float(y)
    N = float(N)
    Mx = float(Mx)
    My = float(My)

    state = _navier_section_state(
        section_field=section_field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
    )
    section = state["section"]

    build_children = getattr(section_field, "build_direct_children_map", None)
    if build_children is None:
        children_map: dict[int, tuple[int, ...]] = {}
    else:
        raw_children = build_children(z)
        if not isinstance(raw_children, dict):
            raise TypeError("build_direct_children_map(z) must return a dict.")
        children_map = {
            int(parent_idx): tuple(int(child_idx) for child_idx in child_indices)
            for parent_idx, child_indices in raw_children.items()
        }

    n_polygons = len(section.polygons)
    for parent_idx, child_indices in children_map.items():
        if not (0 <= parent_idx < n_polygons):
            raise ValueError(
                f"Invalid container polygon index {parent_idx} at z={z}."
            )
        for child_idx in child_indices:
            if not (0 <= child_idx < n_polygons):
                raise ValueError(
                    f"Invalid child polygon index {child_idx} at z={z}."
                )
            if child_idx == parent_idx:
                raise ValueError(
                    f"Polygon index {parent_idx} cannot contain itself."
                )

    quadrant_specs = (
        ("pp", True, True),
        ("mp", False, True),
        ("mm", False, False),
        ("pm", True, False),
    )

    totals = {key: 0.0 for key, _, _ in quadrant_specs}
    area_totals = {key: 0.0 for key, _, _ in quadrant_specs}
    polygon_rows: list[dict[str, object]] = []

    for idx, poly in enumerate(section.polygons):
        polygon_resultants: dict[str, dict[str, object]] = {}
        direct_children = children_map.get(idx, ())

        for key, x_positive, y_positive in quadrant_specs:
            gross = _navier_quadrant_resultant(
                poly=poly,
                state=state,
                x=x,
                y=y,
                x_positive=x_positive,
                y_positive=y_positive,
            )

            occupied_N = float(gross["N"])
            occupied_area = float(gross["area"])
            child_rows: list[dict[str, float | int]] = []

            # CSF occupied-region rule: subtract every direct child from the
            # parent using the PARENT Navier field. The child polygon is then
            # added normally in its own iteration with its own material weight.
            for child_idx in direct_children:
                child_poly = section.polygons[child_idx]
                clipped_child = _clip_polygon_quadrant(
                    poly=child_poly,
                    x=x,
                    y=y,
                    x_positive=x_positive,
                    y_positive=y_positive,
                )
                excluded = _navier_resultant_over_points(
                    poly=poly,
                    points=clipped_child,
                    state=state,
                )

                occupied_N -= float(excluded["N"])
                occupied_area -= float(excluded["area"])

                child_rows.append(
                    {
                        "idx": int(child_idx),
                        "area": float(excluded["area"]),
                        "N_parent_field": float(excluded["N"]),
                    }
                )

            if abs(occupied_area) <= _tol.EPS_A:
                occupied_area = 0.0
            elif occupied_area < -_tol.EPS_A:
                raise ValueError(
                    "Negative occupied quadrant area detected for polygon "
                    f"idx={idx}, quadrant={key}, z={z}: {occupied_area}."
                )

            regional = {
                "area": float(occupied_area),
                "N": float(occupied_N),
                "gross_area": float(gross["area"]),
                "gross_N": float(gross["N"]),
                "excluded_children": child_rows,
            }
            polygon_resultants[key] = regional
            totals[key] += float(occupied_N)
            area_totals[key] += float(occupied_area)

        polygon_rows.append(
            {
                "idx": int(idx),
                "name": str(section_field.s0.polygons[idx].name),
                "weightabs": float(poly.weightabs),
                "direct_children": [int(child_idx) for child_idx in direct_children],
                "quadrants": polygon_resultants,
            }
        )

    N_pp = float(totals["pp"])
    N_mp = float(totals["mp"])
    N_mm = float(totals["mm"])
    N_pm = float(totals["pm"])
    N_sum = N_pp + N_mp + N_mm + N_pm

    return {
        "section": {
            "z": z,
            "x": x,
            "y": y,
            "N": N,
            "Mx": Mx,
            "My": My,
            "Cx": float(state["Cx"]),
            "Cy": float(state["Cy"]),
        },
        "N_pp": N_pp,
        "N_mp": N_mp,
        "N_mm": N_mm,
        "N_pm": N_pm,
        "N_above": float(N_pp + N_mp),
        "N_below": float(N_pm + N_mm),
        "N_right": float(N_pp + N_pm),
        "N_left": float(N_mp + N_mm),
        "N_sum": float(N_sum),
        "N_residual": float(N_sum - N),
        "area_pp": float(area_totals["pp"]),
        "area_mp": float(area_totals["mp"]),
        "area_mm": float(area_totals["mm"]),
        "area_pm": float(area_totals["pm"]),
        "polygons": polygon_rows,
    }


def analyse_navier_four_quadrant_resultant_derivatives(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    x: float,
    y: float,
    *,
    dN_dz: float = 0.0,
    dz: float | None = None,
    derivative_rtol: float = 1.0e-8,
    derivative_atol: float = 1.0e-8,
    max_refinements: int = 20,
) -> dict[str, object]:
    """Differentiate the four Navier regional resultants along ``z``.

    The four resultants are those returned by
    :func:`analyse_navier_four_quadrant_resultants` for the fixed Cartesian
    cuts through ``(x, y)``.  At every shifted station the complete actual
    ``Section(z)`` is rebuilt, so geometry, material participation, centroid
    and inertia changes are all included in the numerical derivative.

    Only the local first derivatives of the section actions are required.
    The action path used by the finite-difference stencil is the local tangent
    path

        N(z + ds)  = N  + dN_dz * ds
        Mx(z + ds) = Mx + Ty     * ds
        My(z + ds) = My + Tx     * ds

    which follows the same CSF sign convention used by the existing
    Jourawski implementation: dMx/dz = Ty and dMy/dz = Tx.

    This function returns only longitudinal derivatives of regional normal
    force.  It does not infer or distribute local shear flows on the two
    internal quadrant boundaries.
    """
    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)
    x = float(x)
    y = float(y)
    dN_dz = float(dN_dz)
    derivative_rtol = float(derivative_rtol)
    derivative_atol = float(derivative_atol)
    max_refinements = int(max_refinements)

    scalar_values = {
        "z": z,
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
        "x": x,
        "y": y,
        "dN_dz": dN_dz,
        "derivative_rtol": derivative_rtol,
        "derivative_atol": derivative_atol,
    }
    for name, value in scalar_values.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    if derivative_rtol < 0.0:
        raise ValueError("derivative_rtol must be non-negative.")
    if derivative_atol < 0.0:
        raise ValueError("derivative_atol must be non-negative.")
    if derivative_rtol == 0.0 and derivative_atol == 0.0:
        raise ValueError(
            "At least one derivative tolerance must be positive."
        )
    if max_refinements < 1:
        raise ValueError("max_refinements must be >= 1.")

    z_start = float(section_field.s0.z)
    z_end = float(section_field.s1.z)

    if not math.isfinite(z_start) or not math.isfinite(z_end):
        raise ValueError("CSF longitudinal bounds must be finite.")
    if z_end <= z_start:
        raise ValueError("The CSF bounds must satisfy s1.z > s0.z.")
    if z < z_start or z > z_end:
        raise ValueError(
            f"z={z} is outside CSF bounds [{z_start}, {z_end}]."
        )

    length = z_end - z_start
    coordinate_tolerance = max(1.0e-14, 1.0e-12 * length)
    minimum_step = coordinate_tolerance

    quadrant_keys = ("pp", "mp", "mm", "pm")
    result_key = {
        "pp": "N_pp",
        "mp": "N_mp",
        "mm": "N_mm",
        "pm": "N_pm",
    }

    sample_cache: dict[float, dict[str, object]] = {}

    def _actions_at_delta(delta_z: float) -> tuple[float, float, float]:
        delta_z = float(delta_z)
        return (
            float(N + dN_dz * delta_z),
            float(Mx + Ty * delta_z),
            float(My + Tx * delta_z),
        )

    def _resultants_at_delta(delta_z: float) -> dict[str, object]:
        delta_z = float(delta_z)
        if delta_z in sample_cache:
            return sample_cache[delta_z]

        N_eval, Mx_eval, My_eval = _actions_at_delta(delta_z)
        result = analyse_navier_four_quadrant_resultants(
            section_field=section_field,
            z=z + delta_z,
            N=N_eval,
            Mx=Mx_eval,
            My=My_eval,
            x=x,
            y=y,
        )
        sample_cache[delta_z] = result
        return result

    def _differentiate_values(
        values: tuple[dict[str, object], ...],
        coefficients: tuple[float, ...],
        denominator: float,
    ) -> dict[str, float]:
        derivatives: dict[str, float] = {}
        for quadrant in quadrant_keys:
            key = result_key[quadrant]
            numerator = sum(
                coefficient * float(value[key])
                for value, coefficient in zip(values, coefficients)
            )
            derivatives[quadrant] = float(numerator / denominator)
        return derivatives

    def _sample_derivative(step: float) -> dict[str, object]:
        step = float(step)
        if not math.isfinite(step) or step <= 0.0:
            raise ValueError("dz must be a finite positive number.")

        left = z - z_start
        right = z_end - z
        at_start = left <= coordinate_tolerance
        at_end = right <= coordinate_tolerance

        if not at_start and not at_end:
            h = min(step, left, right)
            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Four-Quadrant derivative step is too small at z={z}."
                )

            minus = _resultants_at_delta(-h)
            plus = _resultants_at_delta(+h)
            derivatives = _differentiate_values(
                (plus, minus),
                (1.0, -1.0),
                2.0 * h,
            )
            scheme = "central_second_order"

        elif at_start:
            h = min(step, 0.5 * right)
            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Four-Quadrant derivative step is too small at z={z}."
                )

            value_0 = _resultants_at_delta(0.0)
            value_1 = _resultants_at_delta(+h)
            value_2 = _resultants_at_delta(+2.0 * h)
            derivatives = _differentiate_values(
                (value_0, value_1, value_2),
                (-3.0, 4.0, -1.0),
                2.0 * h,
            )
            scheme = "forward_second_order"

        else:
            h = min(step, 0.5 * left)
            if h <= coordinate_tolerance:
                raise ValueError(
                    f"Four-Quadrant derivative step is too small at z={z}."
                )

            value_0 = _resultants_at_delta(0.0)
            value_1 = _resultants_at_delta(-h)
            value_2 = _resultants_at_delta(-2.0 * h)
            derivatives = _differentiate_values(
                (value_0, value_1, value_2),
                (3.0, -4.0, 1.0),
                2.0 * h,
            )
            scheme = "backward_second_order"

        dN_sum_dz = float(sum(derivatives.values()))

        return {
            "dN_pp_dz": float(derivatives["pp"]),
            "dN_mp_dz": float(derivatives["mp"]),
            "dN_mm_dz": float(derivatives["mm"]),
            "dN_pm_dz": float(derivatives["pm"]),
            "dN_above_dz": float(
                derivatives["pp"] + derivatives["mp"]
            ),
            "dN_below_dz": float(
                derivatives["pm"] + derivatives["mm"]
            ),
            "dN_right_dz": float(
                derivatives["pp"] + derivatives["pm"]
            ),
            "dN_left_dz": float(
                derivatives["mp"] + derivatives["mm"]
            ),
            "dN_sum_dz": dN_sum_dz,
            "dN_residual_dz": float(dN_sum_dz - dN_dz),
            "step": float(h),
            "derivative_scheme": scheme,
        }

    def _converged_derivative() -> dict[str, object]:
        previous = _sample_derivative(0.05 * length)

        for refinement in range(1, max_refinements + 1):
            next_step = 0.5 * float(previous["step"])
            if next_step <= minimum_step:
                raise RuntimeError(
                    "Four-Quadrant derivative convergence reached the "
                    f"numerical step limit at z={z}."
                )

            current = _sample_derivative(next_step)
            converged = True
            max_change = 0.0

            for key in (
                "dN_pp_dz",
                "dN_mp_dz",
                "dN_mm_dz",
                "dN_pm_dz",
            ):
                old_value = float(previous[key])
                new_value = float(current[key])
                change = abs(new_value - old_value)
                tolerance = (
                    derivative_atol
                    + derivative_rtol
                    * max(abs(new_value), abs(old_value))
                )
                max_change = max(max_change, change)
                if change > tolerance:
                    converged = False

            if converged:
                current.update(
                    {
                        "derivative_dz_mode": "automatic_convergence",
                        "derivative_converged": True,
                        "derivative_refinements": int(refinement),
                        "derivative_max_change": float(max_change),
                    }
                )
                return current

            previous = current

        raise RuntimeError(
            "Four-Quadrant resultant derivative convergence was not reached "
            f"within max_refinements={max_refinements} at z={z}."
        )

    if dz is None:
        derivative = _converged_derivative()
    else:
        derivative = _sample_derivative(float(dz))
        derivative.update(
            {
                "derivative_dz_mode": "explicit",
                "derivative_converged": None,
                "derivative_refinements": 0,
                "derivative_max_change": float("nan"),
            }
        )

    base_resultants = _resultants_at_delta(0.0)

    derivative.update(
        {
            "section": {
                "z": z,
                "x": x,
                "y": y,
                "N": N,
                "Mx": Mx,
                "My": My,
                "Tx": Tx,
                "Ty": Ty,
                "dN_dz": dN_dz,
                "dMx_dz": Ty,
                "dMy_dz": Tx,
            },
            "N_pp": float(base_resultants["N_pp"]),
            "N_mp": float(base_resultants["N_mp"]),
            "N_mm": float(base_resultants["N_mm"]),
            "N_pm": float(base_resultants["N_pm"]),
            "N_sum": float(base_resultants["N_sum"]),
            "N_residual": float(base_resultants["N_residual"]),
        }
    )

    return derivative

# ---------------------------------------------------------------------------
# Local shear-potential closure
# ---------------------------------------------------------------------------
#
# Mechanical purpose
# ------------------
# The routines in this block recover a *local* in-plane shear-stress field from
# the longitudinal equilibrium of the complete CSF Navier stress field.
#
# The starting point is not an additional taper correction and not a modified
# section shear resultant. The source term is the actual longitudinal derivative
# of the complete physical Navier stress evaluated at a fixed spatial point:
#
#     source(x, y, z) = -partial(sigma_zz) / partial(z).
#
# The local field is closed by the minimum-complementary-energy ansatz
#
#     tau = G_like * grad(phi),
#
# which gives the scalar elliptic problem
#
#     div(G_like * grad(phi)) = -partial(sigma_zz) / partial(z).
#
# Here ``G_like`` is the polygon-level CSF shear carrier
# ``shear_weightabs``. It is intentionally kept separate from the axial-flexural
# ``weightabs`` used by Navier stress recovery.
#
# Why this is a separate API
# --------------------------
# Jourawski, Four-Quadrant equilibrium and this potential closure answer
# different questions:
#
# - Jourawski recovers a classical section-shear field from prescribed Tx, Ty.
# - Four-Quadrant differentiation gives exact *integral equilibrium data* for
#   arbitrary cuts of the complete Navier field.
# - The potential problem selects one local (tau_x, tau_y) field compatible
#   with longitudinal equilibrium and the CSF shear participation.
#
# Therefore this solver is additive at the API level, not additive at the
# stress-field level: callers should not blindly add this returned field to a
# separate Jourawski field. In the validated non-prismatic benchmark the
# potential solution already reproduces the complete reduced-equilibrium shear
# field, including the part that appears as Jourawski plus the non-prismatic
# redistribution when that special case is derived analytically.
#
# Moving geometry
# ---------------
# CSF geometry varies with z. Consequently, a material boundary seen in the
# transverse (x, y) plane has an in-plane velocity v = (dx/dz, dy/dz). The
# traction-free 3D surface condition reduces to the Neumann condition
#
#     tau . n = sigma_zz * v_n,
#
# where ``n`` is the outward unit normal of the active shear domain and
# ``v_n = v . n``.
#
# If two active material regions share a moving interface, the correct weak
# jump is
#
#     (tau_i - tau_j) . n
#         = (sigma_zz_i - sigma_zz_j) * v_n.
#
# A fixed interface has v_n = 0 and therefore reduces to continuity of normal
# shear traction. This interface term is essential for multi-material CSF
# sections whose internal boundaries move along z.
#
# Discretization
# --------------
# The occupied CSF regions are converted to a non-overlapping polygonal domain
# using exactly the same parent-minus-direct-children rule used by the
# Four-Quadrant integration. Each active region is constrained-triangulated and
# uniformly refined. A conforming P1 finite-element potential is then solved.
# Since phi is linear in each triangle, grad(phi) and therefore tau are constant
# on each triangle.
#
# Pure-Neumann gauge
# ------------------
# Each connected shear-domain component has an arbitrary additive constant in
# phi. One zero-mean gauge constraint per connected component is introduced
# with a Lagrange multiplier. The multipliers are not physical stresses; they
# only remove the algebraic nullspace. Compatibility residuals are returned
# explicitly so an incompatible load/source state is never silently hidden by
# the gauge.
#
# Validation role of Four-Quadrant
# --------------------------------
# Optional validation points do not influence the solution. After solving, the
# piecewise-constant tau field is integrated over the four half-chords through
# each point:
#
#     H_L, H_R  from tau_y on the horizontal chord,
#     V_B, V_T  from tau_x on the vertical chord.
#
# These are compared with the independent derivatives of the four Navier
# regional resultants:
#
#     dN_pp/dz =  H_R + V_T
#     dN_mp/dz =  H_L - V_T
#     dN_mm/dz = -H_L - V_B
#     dN_pm/dz = -H_R + V_B.
#
# This is an equilibrium verification, not a corrective projection.
#
# Scope
# -----
# This implementation is a reduced sectional equilibrium closure. It is not a
# replacement for a full three-dimensional elasticity solution. In particular,
# a non-zero dN/dz is deliberately rejected because a scalar axial resultant
# gradient does not uniquely specify the local axial body/surface load
# distribution required by the transverse equilibrium problem.


def _potential_polygon_geometry(poly: Polygon):
    """
    Convert one CSF polygon into a validated Shapely polygon.

    This helper performs only geometric validation. It does not apply CSF
    containment, weights or shear participation. Those operations are handled
    later so that raw polygon geometry and occupied material geometry remain
    conceptually separate.

    A zero-area, empty or self-invalid polygon cannot participate in the local
    finite-element domain and is rejected immediately.
    """
    try:
        from shapely.geometry import Polygon as ShapelyPolygon
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential() requires Shapely."
        ) from exc

    coordinates = [
        (float(point.x), float(point.y))
        for point in poly.vertices
    ]

    if len(coordinates) < 3:
        raise ValueError("A polygon requires at least three vertices.")

    geometry = ShapelyPolygon(coordinates)

    if geometry.is_empty or geometry.area <= _tol.EPS_A:
        raise ValueError("A polygon has zero or negligible geometric area.")

    if not geometry.is_valid:
        raise ValueError(
            "The local shear-potential solver requires valid polygon geometry."
        )

    return geometry


def _potential_polygon_components(geometry) -> list[object]:
    """
    Flatten a Shapely polygonal result into ordinary Polygon components.

    Difference operations used by the occupied-region construction may return
    a Polygon, MultiPolygon or GeometryCollection. The potential mesh operates
    on individual polygonal components, so this routine recursively extracts
    only polygonal pieces and ignores non-area objects such as isolated lines
    or points.
    """
    geometry_type = str(getattr(geometry, "geom_type", ""))

    if geometry_type == "Polygon":
        return [geometry]

    if geometry_type in ("MultiPolygon", "GeometryCollection"):
        components: list[object] = []
        for item in geometry.geoms:
            components.extend(_potential_polygon_components(item))
        return components

    return []


def _potential_children_map(section_field, z: float, polygon_count: int) -> dict[int, tuple[int, ...]]:
    """
    Return the direct, index-based CSF containment topology.

    The local solver follows the same structural rule used elsewhere in CSF:
    polygon names are labels only; parent/child relationships are identified by
    polygon indices. Only *direct* children are subtracted from a parent. This
    avoids double subtraction in nested hierarchies and keeps the local shear
    domain consistent with Four-Quadrant occupied-region integration.
    """
    build_children = getattr(section_field, "build_direct_children_map", None)

    if build_children is None:
        return {}

    raw_children = build_children(float(z))
    if not isinstance(raw_children, dict):
        raise TypeError("build_direct_children_map(z) must return a dict.")

    children_map = {
        int(parent_idx): tuple(
            int(child_idx)
            for child_idx in child_indices
        )
        for parent_idx, child_indices in raw_children.items()
    }

    for parent_idx, child_indices in children_map.items():
        if not (0 <= parent_idx < polygon_count):
            raise ValueError(
                f"Invalid container polygon index {parent_idx} at z={z}."
            )

        for child_idx in child_indices:
            if not (0 <= child_idx < polygon_count):
                raise ValueError(
                    f"Invalid child polygon index {child_idx} at z={z}."
                )
            if child_idx == parent_idx:
                raise ValueError(
                    f"Polygon index {parent_idx} cannot contain itself."
                )

    return children_map


def _potential_occupied_regions(section_field, z: float) -> tuple[list[dict[str, object]], object]:
    """
    Build non-overlapping occupied material regions at one station.

    The same CSF rule used by Four-Quadrant integration is applied:

        occupied(parent) = parent - direct_children(parent)

    A polygon with non-positive shear participation is treated as a void only
    when its axial-flexural participation is also negligible. A polygon that
    carries longitudinal stress but has no positive shear carrier makes the
    elliptic potential problem degenerate and is therefore rejected explicitly.
    """
    try:
        from shapely import unary_union
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential() requires Shapely."
        ) from exc

    section = section_field.section(float(z))
    polygon_count = len(section.polygons)
    if polygon_count == 0:
        raise ValueError("The section contains no polygons.")

    raw_geometry = [
        _potential_polygon_geometry(poly)
        for poly in section.polygons
    ]
    children_map = _potential_children_map(
        section_field,
        float(z),
        polygon_count,
    )

    occupied_geometry: list[object] = []

    for idx, geometry in enumerate(raw_geometry):
        children = children_map.get(idx, ())

        if children:
            child_union = unary_union([
                raw_geometry[child_idx]
                for child_idx in children
            ])

            if not geometry.buffer(_tol.EPS_L).covers(child_union):
                raise ValueError(
                    "A direct child is not geometrically contained in its "
                    f"parent at z={z}: parent index {idx}."
                )

            occupied = geometry.difference(child_union)
        else:
            occupied = geometry

        if not occupied.is_valid:
            raise ValueError(
                "Invalid occupied polygon geometry generated by containment "
                f"at z={z}, polygon index {idx}."
            )

        occupied_geometry.append(occupied)

    regions: list[dict[str, object]] = []

    for idx, (poly, geometry) in enumerate(
        zip(section.polygons, occupied_geometry)
    ):
        if geometry.is_empty or float(geometry.area) <= _tol.EPS_A:
            continue

        shear_weightabs = float(
            _jourawski_polygon_shear_weightabs(poly)
        )
        weightabs = float(getattr(poly, "weightabs", 0.0))

        if not math.isfinite(shear_weightabs):
            raise ValueError(
                f"Non-finite shear participation for polygon index {idx}."
            )

        if shear_weightabs <= _tol.EPS_A:
            if abs(weightabs) <= _tol.EPS_A:
                # A true void remains subtracted from any parent, but it is not
                # part of the elliptic shear domain.
                continue

            raise ValueError(
                "The local shear-potential problem requires positive "
                "shear_weightabs in every occupied region carrying "
                f"longitudinal stress. Polygon index {idx} has "
                f"weightabs={weightabs} and "
                f"shear_weightabs={shear_weightabs}."
            )

        regions.append(
            {
                "polygon_idx": int(idx),
                "name": str(getattr(poly, "name", "")),
                "geometry": geometry,
                "shear_weightabs": shear_weightabs,
                "weightabs": weightabs,
            }
        )

    if not regions:
        raise ValueError(
            "The section contains no occupied region with positive shear "
            "participation."
        )

    # Occupied active regions must form a partition: touching is permitted,
    # positive-area overlap is not.
    section_scale = max(
        1.0,
        *(abs(float(value))
          for geometry in raw_geometry
          for value in geometry.bounds),
    )
    overlap_tolerance = max(
        _tol.EPS_A,
        1.0e-12 * section_scale * section_scale,
    )

    for i, region_i in enumerate(regions):
        geometry_i = region_i["geometry"]

        for region_j in regions[i + 1:]:
            geometry_j = region_j["geometry"]
            overlap_area = float(
                geometry_i.intersection(geometry_j).area
            )

            if overlap_area > overlap_tolerance:
                raise ValueError(
                    "Occupied shear regions overlap by positive area. "
                    f"Polygon indices {region_i['polygon_idx']} and "
                    f"{region_j['polygon_idx']}, overlap={overlap_area}."
                )

    domain = unary_union([
        region["geometry"]
        for region in regions
    ])

    return regions, domain


def _potential_signed_triangle_area(points) -> float:
    """
    Return the signed area of one triangle.

    The sign is used only to enforce a consistent counter-clockwise orientation
    before finite-element gradients are assembled. A positive orientation makes
    the P1 gradient formulas and edge-normal conventions deterministic.
    """
    return 0.5 * float(
        (points[1][0] - points[0][0])
        * (points[2][1] - points[0][1])
        - (points[2][0] - points[0][0])
        * (points[1][1] - points[0][1])
    )


def _potential_initial_triangles(regions: list[dict[str, object]]) -> list[dict[str, object]]:
    """
    Build the initial conforming triangulation of every occupied shear region.

    Constrained Delaunay triangulation is used so polygon boundaries and holes
    remain explicit mesh edges. Every generated triangle inherits the source
    polygon index, label and ``shear_weightabs`` value. The summed triangle area
    is checked against the occupied Shapely area; a mismatch is treated as a
    mesh-construction failure rather than tolerated as numerical drift.
    """
    try:
        import numpy as np
        from shapely import constrained_delaunay_triangles
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential() requires NumPy and "
            "Shapely >= 2.1."
        ) from exc

    triangles: list[dict[str, object]] = []

    for region in regions:
        region_area = float(region["geometry"].area)
        triangulated_area = 0.0

        for component in _potential_polygon_components(
            region["geometry"]
        ):
            triangulation = constrained_delaunay_triangles(component)

            for triangle_geometry in triangulation.geoms:
                if str(triangle_geometry.geom_type) != "Polygon":
                    continue

                if not component.covers(
                    triangle_geometry.representative_point()
                ):
                    continue

                coordinates = np.asarray(
                    list(triangle_geometry.exterior.coords)[:3],
                    dtype=float,
                )

                if coordinates.shape != (3, 2):
                    raise ValueError(
                        "Unexpected constrained triangle geometry."
                    )

                signed_area = _potential_signed_triangle_area(
                    coordinates
                )

                if abs(signed_area) <= _tol.EPS_A:
                    continue

                if signed_area < 0.0:
                    coordinates = coordinates[[0, 2, 1], :]
                    signed_area = -signed_area

                triangulated_area += signed_area
                triangles.append(
                    {
                        "points": coordinates,
                        "polygon_idx": int(region["polygon_idx"]),
                        "name": str(region["name"]),
                        "shear_weightabs": float(
                            region["shear_weightabs"]
                        ),
                    }
                )

        area_tolerance = max(
            1.0e-10,
            1.0e-10 * max(1.0, region_area),
        )

        if abs(triangulated_area - region_area) > area_tolerance:
            raise RuntimeError(
                "Constrained triangulation does not reproduce occupied "
                f"area for polygon index {region['polygon_idx']}: "
                f"triangles={triangulated_area}, region={region_area}."
            )

    if not triangles:
        raise RuntimeError(
            "No triangles were generated for the local shear domain."
        )

    return triangles


def _potential_refine_triangles(
    triangles: list[dict[str, object]],
    refinements: int,
) -> list[dict[str, object]]:
    """
    Uniformly refine every triangle into four children.

    Mid-edge subdivision is used because it preserves conformity when adjacent
    parent triangles share the same merged edge. Refinement changes only the
    numerical resolution: polygon identity and shear participation are inherited
    unchanged by every child triangle.

    The hard upper bound protects callers from accidentally creating a mesh
    whose memory cost grows as 4**refinements.
    """
    import numpy as np

    refinements = int(refinements)
    if refinements < 0:
        raise ValueError("mesh_refinements must be non-negative.")
    if refinements > 8:
        raise ValueError(
            "mesh_refinements > 8 is intentionally blocked to avoid "
            "accidental excessive memory use."
        )

    current = triangles

    for _level in range(refinements):
        refined: list[dict[str, object]] = []

        for triangle in current:
            p0, p1, p2 = triangle["points"]

            m01 = 0.5 * (p0 + p1)
            m12 = 0.5 * (p1 + p2)
            m20 = 0.5 * (p2 + p0)

            children = (
                np.asarray((p0, m01, m20), dtype=float),
                np.asarray((m01, p1, m12), dtype=float),
                np.asarray((m20, m12, p2), dtype=float),
                np.asarray((m01, m12, m20), dtype=float),
            )

            for points in children:
                refined.append(
                    {
                        "points": points,
                        "polygon_idx": int(
                            triangle["polygon_idx"]
                        ),
                        "name": str(triangle["name"]),
                        "shear_weightabs": float(
                            triangle["shear_weightabs"]
                        ),
                    }
                )

        current = refined

    return current



def _potential_refine_triangles_comb_controlled(
    triangles: list[dict[str, object]],
    section_field,
    z: float,
    *,
    num_sudx: int,
    num_sudy: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """
    Conformingly refine only triangle edges that exceed the local comb spacing.

    The physical/model assumptions are unchanged.  This function controls only
    the numerical triangulation used by the existing P1 potential FEM.

    Procedure
    ---------
    1. Build the geometry-driven comb:
         - teeth depend only on CSF geometry;
         - num_sudx / num_sudy subdivide each tooth interval.
    2. For every triangle edge, compare its x/y projections with the smallest
       comb spacing crossed by that projection.
    3. Mark only edges that are too large.
    4. Split every marked edge at its midpoint.  The edge marks are global, so
       both triangles sharing an edge receive the same split and the mesh stays
       conforming.
    5. Repeat until no edge violates the comb target.

    No triangle is refined merely because another, unrelated triangle needs
    refinement.  No GFD stencil or nearest-neighbour selection is involved.
    """
    import bisect
    import numpy as np

    num_sudx = int(num_sudx)
    num_sudy = int(num_sudy)
    if num_sudx < 1:
        raise ValueError("num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("num_sudy must be >= 1.")

    grid = _potential_comb_grid(
        section_field,
        float(z),
        num_sudx=num_sudx,
        num_sudy=num_sudy,
    )
    x_coords = tuple(float(v) for v in grid["x_coords"])
    y_coords = tuple(float(v) for v in grid["y_coords"])

    if len(x_coords) < 2 or len(y_coords) < 2:
        raise RuntimeError("The geometry-driven comb has insufficient coordinates.")

    all_values = [
        float(value)
        for triangle in triangles
        for point in triangle["points"]
        for value in point
    ]
    scale = max(1.0, *(abs(value) for value in all_values))
    key_tol = max(1.0e-13, 1.0e-11 * scale)
    compare_tol = 1.0e-12 * scale

    def _point_key(point) -> tuple[int, int]:
        return (
            int(round(float(point[0]) / key_tol)),
            int(round(float(point[1]) / key_tol)),
        )

    def _edge_key(point_a, point_b):
        key_a = _point_key(point_a)
        key_b = _point_key(point_b)
        return (key_a, key_b) if key_a <= key_b else (key_b, key_a)

    def _minimum_crossed_spacing(
        coords: tuple[float, ...],
        value_a: float,
        value_b: float,
    ) -> float:
        """
        Return the smallest comb interval overlapping the projected edge span.

        A zero projection imposes no refinement requirement in that direction.
        """
        lo = min(float(value_a), float(value_b))
        hi = max(float(value_a), float(value_b))
        if hi - lo <= compare_tol:
            return float("inf")

        # First interval whose upper coordinate is greater than lo.
        start = max(0, bisect.bisect_right(coords, lo) - 1)
        # Last potentially intersected interval.
        stop = min(len(coords) - 2, bisect.bisect_left(coords, hi))

        minimum = float("inf")
        for idx in range(start, stop + 1):
            a = coords[idx]
            b = coords[idx + 1]
            if b <= lo + compare_tol or a >= hi - compare_tol:
                continue
            spacing = b - a
            if spacing > compare_tol:
                minimum = min(minimum, spacing)

        if not np.isfinite(minimum):
            # This should only occur for a projection lying numerically on a
            # comb coordinate.  Use the closest adjacent interval spacing.
            index = min(
                range(len(coords)),
                key=lambda i: abs(coords[i] - 0.5 * (lo + hi)),
            )
            candidates = []
            if index > 0:
                candidates.append(coords[index] - coords[index - 1])
            if index + 1 < len(coords):
                candidates.append(coords[index + 1] - coords[index])
            candidates = [value for value in candidates if value > compare_tol]
            if not candidates:
                raise RuntimeError("Could not determine local comb spacing.")
            minimum = min(candidates)

        return float(minimum)

    def _edge_requires_split(point_a, point_b) -> bool:
        dx = abs(float(point_b[0]) - float(point_a[0]))
        dy = abs(float(point_b[1]) - float(point_a[1]))

        hx = _minimum_crossed_spacing(
            x_coords,
            float(point_a[0]),
            float(point_b[0]),
        )
        hy = _minimum_crossed_spacing(
            y_coords,
            float(point_a[1]),
            float(point_b[1]),
        )

        split_x = np.isfinite(hx) and dx > hx + compare_tol
        split_y = np.isfinite(hy) and dy > hy + compare_tol
        return bool(split_x or split_y)

    def _oriented(points):
        points = np.asarray(points, dtype=float)
        signed_area = _potential_signed_triangle_area(points)
        if abs(signed_area) <= _tol.EPS_A:
            raise RuntimeError(
                "Controlled midpoint refinement generated a degenerate triangle."
            )
        if signed_area < 0.0:
            points = points[[0, 2, 1], :]
        return points

    def _child(parent, points):
        return {
            "points": _oriented(points),
            "polygon_idx": int(parent["polygon_idx"]),
            "name": str(parent["name"]),
            "shear_weightabs": float(parent["shear_weightabs"]),
        }

    current = list(triangles)
    history: list[dict[str, int]] = []

    # Safety only: it does not select the mesh.  Failure raises explicitly
    # rather than silently accepting a mesh that has not reached the target.
    max_passes = 30

    for refinement_pass in range(1, max_passes + 1):
        marked_edges: set[object] = set()

        for triangle in current:
            p0, p1, p2 = triangle["points"]
            for point_a, point_b in ((p0, p1), (p1, p2), (p2, p0)):
                if _edge_requires_split(point_a, point_b):
                    marked_edges.add(_edge_key(point_a, point_b))

        if not marked_edges:
            return current, {
                "strategy": "comb_controlled_conforming_midpoint",
                "num_sudx": num_sudx,
                "num_sudy": num_sudy,
                "x_teeth": int(len(grid["x_teeth"])),
                "y_teeth": int(len(grid["y_teeth"])),
                "x_comb_lines": int(len(x_coords)),
                "y_comb_lines": int(len(y_coords)),
                "passes": int(refinement_pass - 1),
                "history": tuple(history),
                "key_tolerance": float(key_tol),
            }

        refined: list[dict[str, object]] = []

        for triangle in current:
            p0, p1, p2 = triangle["points"]
            e01 = _edge_key(p0, p1) in marked_edges
            e12 = _edge_key(p1, p2) in marked_edges
            e20 = _edge_key(p2, p0) in marked_edges
            marked_count = int(e01) + int(e12) + int(e20)

            if marked_count == 0:
                refined.append(triangle)
                continue

            m01 = 0.5 * (p0 + p1)
            m12 = 0.5 * (p1 + p2)
            m20 = 0.5 * (p2 + p0)

            if marked_count == 1:
                if e01:
                    child_points = (
                        (p0, m01, p2),
                        (m01, p1, p2),
                    )
                elif e12:
                    child_points = (
                        (p1, m12, p0),
                        (m12, p2, p0),
                    )
                else:
                    child_points = (
                        (p2, m20, p1),
                        (m20, p0, p1),
                    )

            elif marked_count == 2:
                if e01 and e12:
                    child_points = (
                        (p1, m12, m01),
                        (p0, m01, m12),
                        (p0, m12, p2),
                    )
                elif e12 and e20:
                    child_points = (
                        (p2, m20, m12),
                        (p1, m12, m20),
                        (p1, m20, p0),
                    )
                else:  # e20 and e01
                    child_points = (
                        (p0, m01, m20),
                        (p2, m20, m01),
                        (p2, m01, p1),
                    )

            else:
                child_points = (
                    (p0, m01, m20),
                    (m01, p1, m12),
                    (m20, m12, p2),
                    (m01, m12, m20),
                )

            for points in child_points:
                refined.append(_child(triangle, points))

        history.append(
            {
                "pass": int(refinement_pass),
                "triangles_before": int(len(current)),
                "marked_edges": int(len(marked_edges)),
                "triangles_after": int(len(refined)),
            }
        )
        current = refined

    raise RuntimeError(
        "Comb-controlled triangle refinement did not reach its target within "
        f"{max_passes} conforming midpoint passes."
    )


def _plot_potential_mesh_controlled(
    *,
    section_field,
    z: float,
    nodes,
    connectivity,
    initial_triangle_count: int,
    refinement_info: dict[str, object],
) -> None:
    """Plot the final comb-controlled conforming P1 triangulation."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("plot_mesh=True requires Matplotlib.") from exc

    fig, ax = plt.subplots()
    ax.triplot(
        nodes[:, 0],
        nodes[:, 1],
        connectivity,
        linewidth=0.6,
    )

    section = section_field.section(float(z))
    for poly in section.polygons:
        if not poly.vertices:
            continue
        xs = [float(vertex.x) for vertex in poly.vertices]
        ys = [float(vertex.y) for vertex in poly.vertices]
        xs.append(xs[0])
        ys.append(ys[0])
        ax.plot(xs, ys, linewidth=1.4)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        "Controlled potential FEM mesh at "
        f"z={float(z):.6g} | "
        f"initial={int(initial_triangle_count)} | "
        f"passes={int(refinement_info['passes'])} | "
        f"triangles={len(connectivity)} | "
        f"nodes={len(nodes)} | "
        f"num_sudx={int(refinement_info['num_sudx'])} | "
        f"num_sudy={int(refinement_info['num_sudy'])}"
    )
    fig.tight_layout()
    plt.show()


def evaluate_navier_local_shear_potential_triangle_field(
    solution: dict[str, object],
    *,
    x: float,
    y: float,
    polygon_idx: int | None = None,
) -> dict[str, object]:
    """
    Sample the piecewise-constant P1 shear field at one physical point.

    If the point lies exactly on a shared triangle edge, all covering triangles
    of the requested polygon are averaged.  This affects only post-processing
    at a measure-zero set of points; it does not alter the FEM solution.
    """
    try:
        import numpy as np
        from shapely.geometry import Point, Polygon as ShapelyPolygon
        from shapely.strtree import STRtree
    except ImportError as exc:
        raise ImportError(
            "Triangle-field evaluation requires NumPy and Shapely."
        ) from exc

    x = float(x)
    y = float(y)
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("x and y must be finite.")

    cache = solution.get("_triangle_field_search_cache")
    if cache is None:
        triangle_rows = list(solution["triangles"])
        geometries = [
            ShapelyPolygon(
                (
                    (float(row["x0"]), float(row["y0"])),
                    (float(row["x1"]), float(row["y1"])),
                    (float(row["x2"]), float(row["y2"])),
                )
            )
            for row in triangle_rows
        ]
        cache = {
            "rows": triangle_rows,
            "geometries": geometries,
            "tree": STRtree(geometries),
        }
        solution["_triangle_field_search_cache"] = cache

    rows = cache["rows"]
    geometries = cache["geometries"]
    tree = cache["tree"]
    point = Point(x, y)

    candidate_indices = tree.query(point, predicate="intersects")
    selected = []

    for candidate_idx in np.atleast_1d(candidate_indices):
        idx = int(candidate_idx)
        row = rows[idx]
        if polygon_idx is not None and int(row["polygon_idx"]) != int(polygon_idx):
            continue
        if geometries[idx].covers(point):
            selected.append(row)

    if not selected:
        raise ValueError(
            "The requested point is not covered by the solved triangle field"
            + (
                f" for polygon_idx={int(polygon_idx)}."
                if polygon_idx is not None
                else "."
            )
        )

    return {
        "x": x,
        "y": y,
        "polygon_idx": (
            int(polygon_idx)
            if polygon_idx is not None
            else int(selected[0]["polygon_idx"])
        ),
        "triangle_count_at_point": int(len(selected)),
        "tau_x": float(
            sum(float(row["tau_x"]) for row in selected) / len(selected)
        ),
        "tau_y": float(
            sum(float(row["tau_y"]) for row in selected) / len(selected)
        ),
    }




def _potential_triangle_direct_csf_mesh(
    section_field,
    z: float,
    regions: list[dict[str, object]],
    *,
    max_triangle_area: float | None = None,
    min_angle: float | None = None,
) -> dict[str, object]:
    """
    Build the potential-FEM mesh directly from CSF polygon vertices/segments.

    Shapely is not used anywhere in this mesh-construction/classification path.

    Mesh construction
    -----------------
    1. Read the actual ``Section(z)`` CSF polygons.
    2. Build one PSLG directly from their vertices and boundary segments.
    3. Validate that constrained segments do not cross except at shared PSLG
       vertices. No automatic nodding or geometric correction is performed.
    4. Call Triangle once.
    5. Classify every returned triangle by the CSF containment hierarchy using
       its centroid. Because every CSF polygon boundary is a constrained PSLG
       edge, the centroid identifies the already-delimited face; it does not
       approximate an interface location.
    6. Keep triangles whose deepest containing CSF polygon is an active shear
       region and discard triangles belonging to void/outside faces.

    ``max_triangle_area`` and ``min_angle`` are passed directly to Triangle.
    With both set to ``None`` no size/quality refinement parameter is imposed
    by CSF.
    """
    try:
        import numpy as np
        import triangle as triangle_lib
    except ImportError as exc:
        raise ImportError(
            "Direct Triangle potential meshing requires NumPy and the "
            "'triangle' package. Install it with: pip install triangle"
        ) from exc

    z = float(z)

    if max_triangle_area is not None:
        max_triangle_area = float(max_triangle_area)
        if not math.isfinite(max_triangle_area) or max_triangle_area <= 0.0:
            raise ValueError(
                "max_triangle_area must be a positive finite value."
            )

    if min_angle is not None:
        min_angle = float(min_angle)
        if not math.isfinite(min_angle) or min_angle <= 0.0:
            raise ValueError("min_angle must be a positive finite value.")

    section = section_field.section(z)
    polygon_count = len(section.polygons)
    if polygon_count == 0:
        raise ValueError("The section contains no polygons.")

    raw_coordinates: list[list[tuple[float, float]]] = []
    coordinate_values: list[float] = []

    for polygon_idx, poly in enumerate(section.polygons):
        coords = [
            (float(point.x), float(point.y))
            for point in poly.vertices
        ]

        if len(coords) < 3:
            raise ValueError(
                f"Polygon index {polygon_idx} has fewer than three vertices."
            )

        for x_value, y_value in coords:
            if not math.isfinite(x_value) or not math.isfinite(y_value):
                raise ValueError(
                    f"Polygon index {polygon_idx} contains non-finite coordinates."
                )
            coordinate_values.extend((x_value, y_value))

        raw_coordinates.append(coords)

    coordinate_scale = max(
        1.0,
        *(abs(value) for value in coordinate_values),
    )
    vertex_tol = max(1.0e-13, 1.0e-11 * coordinate_scale)
    area_tol = max(_tol.EPS_A, 1.0e-12 * coordinate_scale * coordinate_scale)

    def _cross(ax: float, ay: float, bx: float, by: float) -> float:
        return ax * by - ay * bx

    def _signed_polygon_area(coords: list[tuple[float, float]]) -> float:
        total = 0.0
        for (x0, y0), (x1, y1) in zip(coords, coords[1:] + coords[:1]):
            total += x0 * y1 - x1 * y0
        return 0.5 * total

    # Normalize only geometrically null repetitions before building the PSLG.
    #
    # CSF polygon vertex lists may explicitly repeat the first vertex at the end
    # or may contain consecutive coincident vertices. Triangle does not need
    # either representation and would otherwise receive a zero-length segment.
    #
    # The same coordinate tolerance used later by the PSLG vertex merger is used
    # here. The polygon area is checked before/after normalization so this step
    # cannot silently alter the section geometry.
    duplicate_vertex_count = 0
    normalized_coordinates: list[list[tuple[float, float]]] = []
    raw_polygon_area: list[float] = []

    def _same_vertex(
        point_a: tuple[float, float],
        point_b: tuple[float, float],
    ) -> bool:
        return (
            abs(float(point_a[0]) - float(point_b[0])) <= vertex_tol
            and abs(float(point_a[1]) - float(point_b[1])) <= vertex_tol
        )

    for polygon_idx, coords in enumerate(raw_coordinates):
        area_before = abs(_signed_polygon_area(coords))

        cleaned: list[tuple[float, float]] = []
        for point in coords:
            if cleaned and _same_vertex(cleaned[-1], point):
                duplicate_vertex_count += 1
                continue
            cleaned.append(point)

        # An explicitly closed polygon A -> ... -> A is normalized to
        # A -> ... ; the closing segment is generated later by the PSLG builder.
        if len(cleaned) >= 2 and _same_vertex(cleaned[0], cleaned[-1]):
            cleaned.pop()
            duplicate_vertex_count += 1

        if len(cleaned) < 3:
            raise ValueError(
                "Polygon normalization left fewer than three distinct boundary "
                f"vertices: polygon index {polygon_idx}."
            )

        area_after = abs(_signed_polygon_area(cleaned))
        area_change_tol = max(
            area_tol,
            1.0e-12 * max(1.0, abs(area_before), abs(area_after)),
        )

        if abs(area_after - area_before) > area_change_tol:
            raise RuntimeError(
                "Removing coincident consecutive polygon vertices changed the "
                "polygon area beyond numerical tolerance: "
                f"polygon_idx={polygon_idx}, "
                f"area_before={area_before:.16e}, "
                f"area_after={area_after:.16e}, "
                f"difference={area_after - area_before:.16e}."
            )

        if area_after <= area_tol:
            raise ValueError(
                f"Polygon index {polygon_idx} has zero or negligible area."
            )

        normalized_coordinates.append(cleaned)
        raw_polygon_area.append(float(area_after))

    raw_coordinates = normalized_coordinates

    children_map = _potential_children_map(
        section_field,
        z,
        polygon_count,
    )

    # The direct hierarchy must be a tree/forest: one child cannot have two
    # direct parents. This is required for an unambiguous deepest-containing
    # polygon classification.
    parent_of: dict[int, int] = {}
    for parent_idx, child_indices in children_map.items():
        for child_idx in child_indices:
            existing = parent_of.get(child_idx)
            if existing is not None and existing != parent_idx:
                raise ValueError(
                    "A CSF polygon has more than one direct parent at "
                    f"z={z}: child={child_idx}, parents={existing},{parent_idx}."
                )
            parent_of[child_idx] = int(parent_idx)

    depth_cache: dict[int, int] = {}

    def _depth(polygon_idx: int, stack: tuple[int, ...] = ()) -> int:
        if polygon_idx in depth_cache:
            return depth_cache[polygon_idx]
        if polygon_idx in stack:
            raise ValueError(
                "Cycle detected in the CSF direct-containment hierarchy."
            )
        parent_idx = parent_of.get(polygon_idx)
        if parent_idx is None:
            value = 0
        else:
            value = 1 + _depth(parent_idx, stack + (polygon_idx,))
        depth_cache[polygon_idx] = int(value)
        return int(value)

    polygon_depth = [_depth(idx) for idx in range(polygon_count)]

    vertices: list[tuple[float, float]] = []
    vertex_lookup: dict[tuple[int, int], list[int]] = {}
    polygon_vertex_ids: list[list[int]] = []

    def _vertex_id(x_value: float, y_value: float) -> int:
        key = (
            int(round(x_value / vertex_tol)),
            int(round(y_value / vertex_tol)),
        )

        for existing_idx in vertex_lookup.get(key, ()):
            x_old, y_old = vertices[existing_idx]
            if (
                abs(x_old - x_value) <= vertex_tol
                and abs(y_old - y_value) <= vertex_tol
            ):
                return int(existing_idx)

        idx = len(vertices)
        vertices.append((float(x_value), float(y_value)))
        vertex_lookup.setdefault(key, []).append(idx)
        return int(idx)

    for coords in raw_coordinates:
        polygon_vertex_ids.append(
            [_vertex_id(x_value, y_value) for x_value, y_value in coords]
        )

    segment_set: set[tuple[int, int]] = set()
    segments: list[tuple[int, int]] = []

    for polygon_idx, ids in enumerate(polygon_vertex_ids):
        for node_a, node_b in zip(ids, ids[1:] + ids[:1]):
            if node_a == node_b:
                raise ValueError(
                    "A CSF polygon contains a zero-length boundary segment: "
                    f"polygon index {polygon_idx}."
                )

            key = (
                (int(node_a), int(node_b))
                if node_a < node_b
                else (int(node_b), int(node_a))
            )
            if key in segment_set:
                # Exact shared interfaces are represented once in the PSLG.
                continue
            segment_set.add(key)
            segments.append(key)

    if len(vertices) < 3 or not segments:
        raise RuntimeError("The direct CSF PSLG is empty or degenerate.")

    vertex_array = np.asarray(vertices, dtype=float)

    def _point_on_segment(
        px: float,
        py: float,
        ax: float,
        ay: float,
        bx: float,
        by: float,
    ) -> bool:
        dx = bx - ax
        dy = by - ay
        length = math.hypot(dx, dy)
        if length <= vertex_tol:
            return math.hypot(px - ax, py - ay) <= vertex_tol

        cross_value = abs(_cross(px - ax, py - ay, dx, dy))
        if cross_value > vertex_tol * max(1.0, length):
            return False

        dot = (px - ax) * dx + (py - ay) * dy
        if dot < -vertex_tol * max(1.0, length):
            return False

        squared = dx * dx + dy * dy
        if dot > squared + vertex_tol * max(1.0, length):
            return False

        return True

    def _point_in_polygon(
        x_value: float,
        y_value: float,
        coords: list[tuple[float, float]],
    ) -> bool:
        # Boundary is considered inside. Triangle centroids should not normally
        # lie on a constrained edge, but this keeps classification deterministic.
        inside = False
        count = len(coords)

        for i in range(count):
            ax, ay = coords[i]
            bx, by = coords[(i + 1) % count]

            if _point_on_segment(
                x_value, y_value, ax, ay, bx, by
            ):
                return True

            if (ay > y_value) != (by > y_value):
                x_cross = ax + (
                    (y_value - ay)
                    * (bx - ax)
                    / (by - ay)
                )
                if x_cross > x_value:
                    inside = not inside

        return bool(inside)

    def _segment_bbox(segment: tuple[int, int]) -> tuple[float, float, float, float]:
        p0 = vertex_array[segment[0]]
        p1 = vertex_array[segment[1]]
        return (
            float(min(p0[0], p1[0])),
            float(min(p0[1], p1[1])),
            float(max(p0[0], p1[0])),
            float(max(p0[1], p1[1])),
        )

    segment_bboxes = [_segment_bbox(segment) for segment in segments]

    def _proper_or_unrepresented_intersection(
        segment_a: tuple[int, int],
        segment_b: tuple[int, int],
    ) -> bool:
        a_idx, b_idx = segment_a
        c_idx, d_idx = segment_b

        a = vertex_array[a_idx]
        b = vertex_array[b_idx]
        c = vertex_array[c_idx]
        d = vertex_array[d_idx]

        r = b - a
        s = d - c
        r_length = float(np.linalg.norm(r))
        s_length = float(np.linalg.norm(s))

        denominator = _cross(float(r[0]), float(r[1]), float(s[0]), float(s[1]))
        qx = float(c[0] - a[0])
        qy = float(c[1] - a[1])
        cross_qr = _cross(qx, qy, float(r[0]), float(r[1]))
        cross_tol = vertex_tol * max(1.0, r_length, s_length)

        shared_nodes = {a_idx, b_idx}.intersection((c_idx, d_idx))

        if abs(denominator) <= cross_tol:
            if abs(cross_qr) > cross_tol:
                return False

            # Collinear. Exact duplicate segments were removed already.
            axis = 0 if abs(float(r[0])) >= abs(float(r[1])) else 1
            a0 = float(a[axis])
            a1 = float(b[axis])
            c0 = float(c[axis])
            c1 = float(d[axis])

            overlap = min(max(a0, a1), max(c0, c1)) - max(
                min(a0, a1),
                min(c0, c1),
            )

            if overlap > vertex_tol:
                return True
            return False

        t = _cross(qx, qy, float(s[0]), float(s[1])) / denominator
        u = cross_qr / denominator

        parameter_tol = 1.0e-10
        intersects = (
            -parameter_tol <= t <= 1.0 + parameter_tol
            and -parameter_tol <= u <= 1.0 + parameter_tol
        )
        if not intersects:
            return False

        # An intersection represented by the same PSLG endpoint is valid.
        t_endpoint = abs(t) <= parameter_tol or abs(t - 1.0) <= parameter_tol
        u_endpoint = abs(u) <= parameter_tol or abs(u - 1.0) <= parameter_tol

        if shared_nodes and t_endpoint and u_endpoint:
            return False

        return True

    # Explicit PSLG validation. We do not ask Triangle to repair crossings,
    # split T-junctions or reinterpret overlapping boundary segments.
    segment_count = len(segments)
    for i in range(segment_count):
        min_x_i, min_y_i, max_x_i, max_y_i = segment_bboxes[i]

        for j in range(i + 1, segment_count):
            min_x_j, min_y_j, max_x_j, max_y_j = segment_bboxes[j]

            if (
                max_x_i < min_x_j - vertex_tol
                or max_x_j < min_x_i - vertex_tol
                or max_y_i < min_y_j - vertex_tol
                or max_y_j < min_y_i - vertex_tol
            ):
                continue

            if _proper_or_unrepresented_intersection(
                segments[i],
                segments[j],
            ):
                raise RuntimeError(
                    "The direct CSF PSLG contains crossing, overlapping or "
                    "un-noded boundary segments. No automatic geometric "
                    "correction is applied. "
                    f"segment_a={segments[i]}, segment_b={segments[j]}."
                )

    triangle_input: dict[str, object] = {
        "vertices": vertex_array,
        "segments": np.asarray(segments, dtype=np.int32),
    }

    # p = PSLG. Q = quiet. No hole or region seed is passed: Triangle meshes
    # the PSLG faces it constructs, while CSF performs the semantic keep/discard
    # classification afterward.
    options = "pQ"
    if min_angle is not None:
        options += f"q{min_angle:.17g}"
    if max_triangle_area is not None:
        # Triangle's command-line-style parser expects the value following
        # ``a`` in ordinary decimal notation. Scientific notation such as
        # ``a5e-06`` is not interpreted as 5e-6 by that parser.
        #
        # Decimal(str(...)) preserves the user-supplied floating-point value
        # while ``format(..., "f")`` emits plain decimal notation:
        #     5.0e-6 -> 0.000005
        area_option = format(
            Decimal(str(float(max_triangle_area))),
            "f",
        )
        options += f"a{area_option}"

    triangle_output = triangle_lib.triangulate(
        triangle_input,
        options,
    )

    if "vertices" not in triangle_output or "triangles" not in triangle_output:
        raise RuntimeError(
            "Triangle did not return vertices and triangles for the direct CSF PSLG."
        )

    all_nodes = np.asarray(triangle_output["vertices"], dtype=float)
    all_connectivity = np.asarray(
        triangle_output["triangles"],
        dtype=int,
    )

    if (
        all_connectivity.ndim != 2
        or all_connectivity.shape[1] != 3
    ):
        raise RuntimeError("Triangle returned non-triangular connectivity.")

    active_region_by_polygon = {
        int(region["polygon_idx"]): region
        for region in regions
    }

    expected_occupied_area: dict[int, float] = {}
    for polygon_idx in active_region_by_polygon:
        child_area = sum(
            raw_polygon_area[child_idx]
            for child_idx in children_map.get(polygon_idx, ())
        )
        occupied_area = raw_polygon_area[polygon_idx] - child_area
        if occupied_area <= area_tol:
            raise RuntimeError(
                "The direct CSF occupied-area calculation is non-positive: "
                f"polygon_idx={polygon_idx}, area={occupied_area}."
            )
        expected_occupied_area[polygon_idx] = float(occupied_area)

    expected_active_area = float(sum(expected_occupied_area.values()))

    kept_connectivity: list[list[int]] = []
    kept_polygon_indices: list[int] = []
    kept_shear_weights: list[float] = []
    kept_names: list[str] = []

    kept_area_by_polygon = {
        polygon_idx: 0.0
        for polygon_idx in active_region_by_polygon
    }

    discarded_outside_count = 0
    discarded_void_count = 0
    all_triangle_area = 0.0
    kept_triangle_area = 0.0

    for triangle_idx, element in enumerate(all_connectivity):
        points = all_nodes[element]
        signed_area = _potential_signed_triangle_area(points)

        if abs(signed_area) <= _tol.EPS_A:
            raise RuntimeError(
                f"Triangle generated a degenerate element at index {triangle_idx}."
            )

        if signed_area < 0.0:
            element = element[[0, 2, 1]]
            points = all_nodes[element]
            signed_area = -signed_area

        area = float(signed_area)
        all_triangle_area += area

        centroid_x = float(np.mean(points[:, 0]))
        centroid_y = float(np.mean(points[:, 1]))

        containing = [
            polygon_idx
            for polygon_idx, coords in enumerate(raw_coordinates)
            if _point_in_polygon(
                centroid_x,
                centroid_y,
                coords,
            )
        ]

        if not containing:
            discarded_outside_count += 1
            continue

        maximum_depth = max(
            polygon_depth[polygon_idx]
            for polygon_idx in containing
        )
        deepest = [
            polygon_idx
            for polygon_idx in containing
            if polygon_depth[polygon_idx] == maximum_depth
        ]

        if len(deepest) != 1:
            raise RuntimeError(
                "Triangle centroid belongs ambiguously to multiple CSF polygons "
                "at the same containment depth: "
                f"triangle_idx={triangle_idx}, "
                f"centroid=({centroid_x:.12e}, {centroid_y:.12e}), "
                f"candidates={deepest}."
            )

        polygon_idx = int(deepest[0])
        region = active_region_by_polygon.get(polygon_idx)

        if region is None:
            discarded_void_count += 1
            continue

        kept_connectivity.append(
            [int(element[0]), int(element[1]), int(element[2])]
        )
        kept_polygon_indices.append(polygon_idx)
        kept_shear_weights.append(float(region["shear_weightabs"]))
        kept_names.append(str(region["name"]))

        kept_triangle_area += area
        kept_area_by_polygon[polygon_idx] += area

    if not kept_connectivity:
        raise RuntimeError(
            "Triangle generated no elements belonging to active CSF shear regions."
        )

    kept_connectivity_array = np.asarray(
        kept_connectivity,
        dtype=int,
    )

    # Remove nodes used only by outside/void faces and renumber active elements.
    used_old_nodes, inverse = np.unique(
        kept_connectivity_array.reshape(-1),
        return_inverse=True,
    )
    nodes = all_nodes[used_old_nodes]
    connectivity = inverse.reshape(
        kept_connectivity_array.shape
    ).astype(int)

    polygon_indices = np.asarray(
        kept_polygon_indices,
        dtype=int,
    )
    shear_weights = np.asarray(
        kept_shear_weights,
        dtype=float,
    )

    total_area_tolerance = max(
        _tol.EPS_A,
        1.0e-8 * max(1.0, abs(expected_active_area)),
    )

    if abs(kept_triangle_area - expected_active_area) > total_area_tolerance:
        raise RuntimeError(
            "Direct Triangle active-mesh area does not match the CSF occupied "
            "area: "
            f"mesh={kept_triangle_area}, expected={expected_active_area}, "
            f"difference={kept_triangle_area - expected_active_area}."
        )

    for polygon_idx, expected_area in expected_occupied_area.items():
        actual_area = float(kept_area_by_polygon[polygon_idx])
        tolerance = max(
            _tol.EPS_A,
            1.0e-8 * max(1.0, abs(expected_area)),
        )
        if abs(actual_area - expected_area) > tolerance:
            raise RuntimeError(
                "Direct Triangle area does not match one CSF occupied region: "
                f"polygon_idx={polygon_idx}, mesh={actual_area}, "
                f"expected={expected_area}, "
                f"difference={actual_area - expected_area}."
            )

    return {
        "nodes": nodes,
        "triangles": connectivity,
        "polygon_indices": polygon_indices,
        "names": kept_names,
        "shear_weights": shear_weights,
        "merge_tolerance": float(vertex_tol),
        "backend": "triangle_direct_csf_pslg",
        "triangle_options": options,
        "max_triangle_area": (
            None if max_triangle_area is None else float(max_triangle_area)
        ),
        "min_angle": (
            None if min_angle is None else float(min_angle)
        ),
        "pslg_vertex_count": int(len(vertices)),
        "pslg_segment_count": int(len(segments)),
        "normalized_duplicate_vertex_count": int(duplicate_vertex_count),
        "pslg_hole_count": 0,
        "pslg_region_seed_count": 0,
        "triangle_total_count": int(len(all_connectivity)),
        "discarded_outside_triangle_count": int(discarded_outside_count),
        "discarded_void_triangle_count": int(discarded_void_count),
        "discarded_triangle_count": int(
            discarded_outside_count + discarded_void_count
        ),
        "active_triangle_count": int(len(connectivity)),
        "all_triangle_area": float(all_triangle_area),
        "domain_area": float(expected_active_area),
        "mesh_area": float(kept_triangle_area),
    }


def _plot_potential_mesh_triangle(
    *,
    section_field,
    z: float,
    mesh: dict[str, object],
) -> None:
    """Plot the Triangle PSLG P1 mesh without altering the solve."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("plot_mesh=True requires Matplotlib.") from exc

    nodes = mesh["nodes"]
    connectivity = mesh["triangles"]

    fig, ax = plt.subplots()
    ax.triplot(
        nodes[:, 0],
        nodes[:, 1],
        connectivity,
        linewidth=0.6,
    )

    section = section_field.section(float(z))
    for poly in section.polygons:
        if not poly.vertices:
            continue
        xs = [float(vertex.x) for vertex in poly.vertices]
        ys = [float(vertex.y) for vertex in poly.vertices]
        xs.append(xs[0])
        ys.append(ys[0])
        ax.plot(xs, ys, linewidth=1.4)

    area_text = (
        "none"
        if mesh["max_triangle_area"] is None
        else f"{float(mesh['max_triangle_area']):.6g}"
    )
    angle_text = (
        "none"
        if mesh["min_angle"] is None
        else f"{float(mesh['min_angle']):.6g}"
    )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        "Triangle potential FEM mesh at "
        f"z={float(z):.6g} | "
        f"triangles={len(connectivity)} | "
        f"nodes={len(nodes)} | "
        f"PSLG vertices={int(mesh['pslg_vertex_count'])} | "
        f"max_area={area_text} | min_angle={angle_text}"
    )
    fig.tight_layout()
    plt.show()



def _potential_merge_mesh(
    triangles: list[dict[str, object]],
) -> dict[str, object]:
    """
    Merge geometrically coincident triangle vertices into global mesh nodes.

    Triangulation is performed region-by-region, so the same physical interface
    may initially contain duplicate coordinates. A scale-aware coordinate key
    merges those duplicates. This is required for displacement/potential
    continuity and for detecting two-sided material-interface edges.

    The returned arrays keep triangle-to-polygon metadata alongside connectivity
    so material participation can remain piecewise constant by CSF region.
    """
    import numpy as np

    all_coordinates = [
        float(value)
        for triangle in triangles
        for point in triangle["points"]
        for value in point
    ]
    scale = max(1.0, *(abs(value) for value in all_coordinates))
    merge_tolerance = max(1.0e-13, 1.0e-11 * scale)

    nodes: list[tuple[float, float]] = []
    node_lookup: dict[tuple[int, int], int] = {}
    connectivity: list[tuple[int, int, int]] = []
    polygon_indices: list[int] = []
    names: list[str] = []
    shear_weights: list[float] = []

    def node_id(point) -> int:
        x_value = float(point[0])
        y_value = float(point[1])
        key = (
            int(round(x_value / merge_tolerance)),
            int(round(y_value / merge_tolerance)),
        )

        existing = node_lookup.get(key)
        if existing is not None:
            x_old, y_old = nodes[existing]
            if (
                abs(x_old - x_value) <= 2.0 * merge_tolerance
                and abs(y_old - y_value) <= 2.0 * merge_tolerance
            ):
                return existing

        index = len(nodes)
        nodes.append((x_value, y_value))
        node_lookup[key] = index
        return index

    for triangle in triangles:
        ids = tuple(
            node_id(point)
            for point in triangle["points"]
        )

        if len(set(ids)) != 3:
            raise RuntimeError(
                "Degenerate triangle generated during node merging."
            )

        connectivity.append(ids)
        polygon_indices.append(int(triangle["polygon_idx"]))
        names.append(str(triangle["name"]))
        shear_weights.append(float(triangle["shear_weightabs"]))

    return {
        "nodes": np.asarray(nodes, dtype=float),
        "triangles": np.asarray(connectivity, dtype=int),
        "polygon_indices": np.asarray(
            polygon_indices,
            dtype=int,
        ),
        "names": names,
        "shear_weights": np.asarray(
            shear_weights,
            dtype=float,
        ),
        "merge_tolerance": float(merge_tolerance),
    }



def _plot_potential_mesh(
    *,
    section_field,
    z: float,
    nodes,
    connectivity,
    initial_triangle_count: int,
    mesh_refinements: int,
) -> None:
    """Plot the already-generated potential mesh without changing the solve."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "plot_mesh=True requires Matplotlib."
        ) from exc

    fig, ax = plt.subplots()

    # Draw the final triangulation that will be used by the FEM assembly.
    ax.triplot(
        nodes[:, 0],
        nodes[:, 1],
        connectivity,
        linewidth=0.6,
    )

    # Overlay the exact CSF polygon boundaries at the requested station.
    section = section_field.section(float(z))
    for poly in section.polygons:
        if not poly.vertices:
            continue
        xs = [float(vertex.x) for vertex in poly.vertices]
        ys = [float(vertex.y) for vertex in poly.vertices]
        xs.append(xs[0])
        ys.append(ys[0])
        ax.plot(xs, ys, linewidth=1.4)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        "Potential mesh at "
        f"z={float(z):.6g} | "
        f"initial={int(initial_triangle_count)} | "
        f"refinements={int(mesh_refinements)} | "
        f"triangles={len(connectivity)} | "
        f"nodes={len(nodes)}"
    )
    fig.tight_layout()
    plt.show()



def _potential_comb_grid(
    section_field,
    z: float,
    *,
    num_sudx: int,
    num_sudy: int,
) -> dict[str, object]:
    """
    Build the geometry-driven Cartesian comb used for mesh preview.

    The geometric teeth depend only on the current CSF section geometry:
    polygon bounding-box minima/maxima are collected independently along x
    and y and are retained exactly as comb boundaries.

    ``num_sudx`` and ``num_sudy`` do not generate teeth and do not define a
    global background grid.  They specify how many equal sub-intervals are
    created *between each pair of consecutive geometric teeth*:

        [x_i, x_(i+1)] -> num_sudx sub-intervals
        [y_j, y_(j+1)] -> num_sudy sub-intervals

    The purpose of this helper is only to make that geometry-driven rule
    visible before any potential-field discretization is selected.  It does
    not assemble or solve the scalar-potential PDE.
    """
    num_sudx = int(num_sudx)
    num_sudy = int(num_sudy)

    if num_sudx < 1:
        raise ValueError("num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("num_sudy must be >= 1.")

    z = float(z)
    section = section_field.section(z)
    xmin, xmax, ymin, ymax = _section_active_bbox(section)

    def _axis_teeth(
        *,
        axis: str,
        coord_min: float,
        coord_max: float,
    ) -> list[float]:
        if axis not in ("x", "y"):
            raise ValueError("axis must be 'x' or 'y'.")

        teeth: list[float] = [float(coord_min), float(coord_max)]

        for poly in section.polygons:
            polygon_coords = [
                float(vertex.x if axis == "x" else vertex.y)
                for vertex in poly.vertices
            ]
            if not polygon_coords:
                continue

            polygon_min = min(polygon_coords)
            polygon_max = max(polygon_coords)

            if (
                polygon_max < float(coord_min) - _tol.EPS_L
                or polygon_min > float(coord_max) + _tol.EPS_L
            ):
                continue

            teeth.append(
                min(float(coord_max), max(float(coord_min), polygon_min))
            )
            teeth.append(
                min(float(coord_max), max(float(coord_min), polygon_max))
            )

        return _unique_sorted(teeth)

    def _subdivide_between_teeth(
        *,
        teeth: list[float],
        subdivisions: int,
    ) -> tuple[list[float], list[float]]:
        """Subdivide every geometric tooth interval into equal sub-intervals."""
        coords: list[float] = []
        inserted: list[float] = []

        for interval_index, (coord_0, coord_1) in enumerate(
            zip(teeth[:-1], teeth[1:])
        ):
            a = float(coord_0)
            b = float(coord_1)
            span = b - a
            if span <= _tol.EPS_L:
                continue

            # Keep each geometric tooth exactly.  Interior subdivision lines
            # are generated only inside the current tooth interval.
            if interval_index == 0:
                coords.append(a)

            local_step = span / int(subdivisions)
            for k in range(1, int(subdivisions)):
                value = a + k * local_step
                coords.append(value)
                inserted.append(value)

            coords.append(b)

        return _unique_sorted(coords), _unique_sorted(inserted)

    x_teeth = _axis_teeth(
        axis="x",
        coord_min=xmin,
        coord_max=xmax,
    )
    y_teeth = _axis_teeth(
        axis="y",
        coord_min=ymin,
        coord_max=ymax,
    )

    x_coords, x_inserted = _subdivide_between_teeth(
        teeth=x_teeth,
        subdivisions=num_sudx,
    )
    y_coords, y_inserted = _subdivide_between_teeth(
        teeth=y_teeth,
        subdivisions=num_sudy,
    )

    regions, domain = _potential_occupied_regions(section_field, z)

    return {
        "z": z,
        "num_sudx": num_sudx,
        "num_sudy": num_sudy,
        "bbox": (float(xmin), float(xmax), float(ymin), float(ymax)),
        "x_teeth": tuple(float(v) for v in x_teeth),
        "y_teeth": tuple(float(v) for v in y_teeth),
        "x_tooth_intervals": max(0, len(x_teeth) - 1),
        "y_tooth_intervals": max(0, len(y_teeth) - 1),
        "x_inserted": tuple(float(v) for v in x_inserted),
        "y_inserted": tuple(float(v) for v in y_inserted),
        "x_coords": tuple(float(v) for v in x_coords),
        "y_coords": tuple(float(v) for v in y_coords),
        "background_cell_count": max(0, len(x_coords) - 1)
        * max(0, len(y_coords) - 1),
        "regions": regions,
        "domain": domain,
    }



def _potential_comb_network_nodes(
    section_field,
    z: float,
    *,
    num_sudx: int,
    num_sudy: int,
) -> dict[str, object]:
    """
    Build only the point network associated with the 2D comb.

    Two node families are generated:

    1. comb-crossing nodes:
       intersections x_comb x y_comb that belong to the occupied shear domain;

    2. polygon-intersection nodes:
       intersections between every horizontal/vertical comb line and the exact
       boundaries of the CSF polygons.

    No cells, triangles, finite elements, PDE equations or shear stresses are
    generated here.  This helper is only a geometric preview of the proposed
    point network.

    If a comb line is exactly coincident with a polygon edge, the overlap is
    represented in this preview by the endpoints of the coincident segment.
    """
    try:
        import numpy as np
        from shapely import intersects_xy
        from shapely.geometry import LineString
    except ImportError as exc:
        raise ImportError(
            "_potential_comb_network_nodes() requires NumPy and Shapely."
        ) from exc

    grid = _potential_comb_grid(
        section_field,
        float(z),
        num_sudx=int(num_sudx),
        num_sudy=int(num_sudy),
    )

    xmin, xmax, ymin, ymax = grid["bbox"]
    domain = grid["domain"]
    x_coords = np.asarray(grid["x_coords"], dtype=float)
    y_coords = np.asarray(grid["y_coords"], dtype=float)

    # Family 1: x/y comb intersections belonging to the occupied domain.
    comb_nodes: list[tuple[float, float]] = []

    for y_value in y_coords:
        y_values = np.full(x_coords.shape, float(y_value), dtype=float)
        inside = np.asarray(
            intersects_xy(domain, x_coords, y_values),
            dtype=bool,
        )
        for x_value in x_coords[inside]:
            comb_nodes.append((float(x_value), float(y_value)))

    # Family 2: intersections of every comb line with exact CSF polygon
    # boundaries.  Raw polygon boundaries are used intentionally: these are
    # the geometric boundaries/interfaces supplied by CSF.
    section = section_field.section(float(z))
    polygon_boundaries = [
        _potential_polygon_geometry(poly).boundary
        for poly in section.polygons
        if poly.vertices
    ]

    scale = max(
        1.0,
        abs(float(xmin)),
        abs(float(xmax)),
        abs(float(ymin)),
        abs(float(ymax)),
        float(xmax) - float(xmin),
        float(ymax) - float(ymin),
    )
    point_tol = max(float(_tol.EPS_L), 1.0e-12 * scale)

    polygon_node_map: dict[tuple[int, int], tuple[float, float]] = {}

    def _store_point(x_value: float, y_value: float) -> None:
        x_value = float(x_value)
        y_value = float(y_value)
        key = (
            int(round(x_value / point_tol)),
            int(round(y_value / point_tol)),
        )
        polygon_node_map.setdefault(key, (x_value, y_value))

    def _collect_points(geometry) -> None:
        if geometry.is_empty:
            return

        geom_type = str(geometry.geom_type)

        if geom_type == "Point":
            _store_point(geometry.x, geometry.y)
            return

        if geom_type == "MultiPoint":
            for item in geometry.geoms:
                _collect_points(item)
            return

        if geom_type in ("LineString", "LinearRing"):
            coordinates = list(geometry.coords)
            if coordinates:
                _store_point(*coordinates[0])
                _store_point(*coordinates[-1])
            return

        if hasattr(geometry, "geoms"):
            for item in geometry.geoms:
                _collect_points(item)

    for x_value in x_coords:
        comb_line = LineString(
            ((float(x_value), float(ymin)), (float(x_value), float(ymax)))
        )
        for boundary in polygon_boundaries:
            _collect_points(boundary.intersection(comb_line))

    for y_value in y_coords:
        comb_line = LineString(
            ((float(xmin), float(y_value)), (float(xmax), float(y_value)))
        )
        for boundary in polygon_boundaries:
            _collect_points(boundary.intersection(comb_line))

    polygon_nodes = list(polygon_node_map.values())

    return {
        "grid": grid,
        "comb_nodes": tuple(comb_nodes),
        "polygon_nodes": tuple(polygon_nodes),
    }


def plot_navier_local_shear_potential_comb_nodes(
    section_field,
    z: float,
    *,
    num_sudx: int = 20,
    num_sudy: int = 20,
) -> dict[str, object]:
    """
    Plot the proposed point network before any PDE discretization.

    The plot shows:
    - the 2D comb;
    - valid x/y comb-crossing nodes inside/on the occupied shear domain;
    - intersections between comb lines and exact CSF polygon boundaries.

    No numerical field equation is assembled or solved.
    """
    try:
        import matplotlib.pyplot as plt
        from shapely.geometry import LineString
    except ImportError as exc:
        raise ImportError(
            "plot_navier_local_shear_potential_comb_nodes() requires "
            "Matplotlib and Shapely."
        ) from exc

    network = _potential_comb_network_nodes(
        section_field,
        float(z),
        num_sudx=int(num_sudx),
        num_sudy=int(num_sudy),
    )

    grid = network["grid"]
    comb_nodes = list(network["comb_nodes"])
    polygon_nodes = list(network["polygon_nodes"])

    xmin, xmax, ymin, ymax = grid["bbox"]
    domain = grid["domain"]
    x_coords = list(grid["x_coords"])
    y_coords = list(grid["y_coords"])
    x_teeth = set(grid["x_teeth"])
    y_teeth = set(grid["y_teeth"])

    fig, ax = plt.subplots()

    def _draw_clipped_line(geometry, *, linewidth: float) -> None:
        if geometry.is_empty:
            return

        geom_type = str(geometry.geom_type)
        if geom_type in ("LineString", "LinearRing"):
            xs, ys = geometry.xy
            ax.plot(xs, ys, linewidth=linewidth)
            return

        if hasattr(geometry, "geoms"):
            for part in geometry.geoms:
                _draw_clipped_line(part, linewidth=linewidth)

    # Draw the comb only where it intersects the occupied shear domain.
    for x_value in x_coords:
        line = LineString(((float(x_value), ymin), (float(x_value), ymax)))
        clipped = domain.intersection(line)
        is_tooth = any(abs(float(x_value) - t) <= _tol.EPS_L for t in x_teeth)
        _draw_clipped_line(clipped, linewidth=0.7 if is_tooth else 0.20)

    for y_value in y_coords:
        line = LineString(((xmin, float(y_value)), (xmax, float(y_value))))
        clipped = domain.intersection(line)
        is_tooth = any(abs(float(y_value) - t) <= _tol.EPS_L for t in y_teeth)
        _draw_clipped_line(clipped, linewidth=0.7 if is_tooth else 0.20)

    # Exact CSF polygon boundaries.
    section = section_field.section(float(z))
    for poly in section.polygons:
        if not poly.vertices:
            continue
        xs = [float(vertex.x) for vertex in poly.vertices]
        ys = [float(vertex.y) for vertex in poly.vertices]
        xs.append(xs[0])
        ys.append(ys[0])
        ax.plot(xs, ys, linewidth=1.2)

    # Family 1: ordinary x/y comb intersections inside the domain.
    if comb_nodes:
        xs = [point[0] for point in comb_nodes]
        ys = [point[1] for point in comb_nodes]
        ax.scatter(
            xs,
            ys,
            s=2.0,
            marker=".",
            linewidths=0.0,
            rasterized=True,
            label="comb x/y intersections",
        )

    # Family 2: comb/polygon intersections, deliberately more visible.
    if polygon_nodes:
        xs = [point[0] for point in polygon_nodes]
        ys = [point[1] for point in polygon_nodes]
        ax.scatter(
            xs,
            ys,
            s=13.0,
            marker="x",
            linewidths=0.6,
            rasterized=True,
            label="comb/polygon intersections",
        )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        "Potential 2D comb point-network preview at "
        f"z={float(z):.6g} | "
        f"num_sudx={int(num_sudx)} | "
        f"num_sudy={int(num_sudy)} | "
        f"comb_nodes={len(comb_nodes)} | "
        f"polygon_nodes={len(polygon_nodes)}"
    )
    ax.legend()
    fig.tight_layout()
    plt.show()

    return {
        "z": float(z),
        "num_sudx": int(num_sudx),
        "num_sudy": int(num_sudy),
        "x_teeth": grid["x_teeth"],
        "y_teeth": grid["y_teeth"],
        "x_coords": grid["x_coords"],
        "y_coords": grid["y_coords"],
        "comb_node_count": len(comb_nodes),
        "polygon_node_count": len(polygon_nodes),
        "comb_nodes": tuple(comb_nodes),
        "polygon_nodes": tuple(polygon_nodes),
    }




# ---------------------------------------------------------------------------
# Comb point-network potential solver (mesh-free GFD collocation)
# ---------------------------------------------------------------------------


def _potential_comb_merge_nodes(
    network: dict[str, object],
) -> tuple[object, float]:
    """Merge the two approved comb-node families into one geometric point set."""
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "The comb potential solver requires NumPy."
        ) from exc

    grid = network["grid"]
    xmin, xmax, ymin, ymax = grid["bbox"]
    scale = max(
        1.0,
        abs(float(xmin)),
        abs(float(xmax)),
        abs(float(ymin)),
        abs(float(ymax)),
        float(xmax) - float(xmin),
        float(ymax) - float(ymin),
    )
    tolerance = max(float(_tol.EPS_L), 1.0e-12 * scale)

    merged: dict[tuple[int, int], tuple[float, float]] = {}
    for family in ("comb_nodes", "polygon_nodes"):
        for x_value, y_value in network[family]:
            x_value = float(x_value)
            y_value = float(y_value)
            key = (
                int(round(x_value / tolerance)),
                int(round(y_value / tolerance)),
            )
            merged.setdefault(key, (x_value, y_value))

    nodes = np.asarray(list(merged.values()), dtype=float)
    if nodes.ndim != 2 or nodes.shape[1] != 2 or len(nodes) == 0:
        raise RuntimeError("The comb point network contains no usable nodes.")

    return nodes, float(tolerance)


def _potential_comb_region_membership(
    *,
    nodes,
    regions: list[dict[str, object]],
    tolerance: float,
) -> tuple[list[tuple[int, ...]], list[list[int]]]:
    """Classify every physical comb node by occupied CSF region membership."""
    try:
        from shapely.geometry import Point as ShapelyPoint
        from shapely.strtree import STRtree
    except ImportError as exc:
        raise ImportError(
            "The comb potential solver requires Shapely."
        ) from exc

    geometries = [region["geometry"] for region in regions]
    tree = STRtree(geometries)

    node_regions: list[tuple[int, ...]] = []
    region_nodes: list[list[int]] = [[] for _ in regions]

    for node_idx, (x_value, y_value) in enumerate(nodes):
        point = ShapelyPoint(float(x_value), float(y_value))
        candidate_indices = tree.query(point)
        matches: list[int] = []

        for candidate in candidate_indices:
            region_idx = int(candidate)
            geometry = geometries[region_idx]
            if (
                geometry.covers(point)
                or geometry.boundary.distance(point) <= float(tolerance)
            ):
                matches.append(region_idx)

        matches = sorted(set(matches))
        node_regions.append(tuple(matches))
        for region_idx in matches:
            region_nodes[region_idx].append(int(node_idx))

    return node_regions, region_nodes


def _potential_comb_point_segment_distance(
    *,
    x: float,
    y: float,
    p0: tuple[float, float],
    p1: tuple[float, float],
) -> tuple[float, float, float]:
    """Return clamped segment parameter, distance and segment length."""
    x0, y0 = map(float, p0)
    x1, y1 = map(float, p1)
    dx = x1 - x0
    dy = y1 - y0
    length_squared = dx * dx + dy * dy
    if length_squared <= float(_tol.EPS_L) ** 2:
        return 0.0, float("inf"), 0.0

    t = ((float(x) - x0) * dx + (float(y) - y0) * dy) / length_squared
    t = min(1.0, max(0.0, float(t)))
    px = x0 + t * dx
    py = y0 + t * dy
    return (
        float(t),
        float(math.hypot(float(x) - px, float(y) - py)),
        float(math.sqrt(length_squared)),
    )


def _potential_comb_region_outward_normal(
    geometry,
    *,
    x: float,
    y: float,
    tolerance: float,
) -> tuple[float, float]:
    """
    Return the outward unit normal of one occupied region at a boundary node.

    At a geometric corner the normalized sum of all incident outward segment
    normals is used.  This is a pointwise collocation convention only; corners
    have zero boundary measure and do not alter the continuous Neumann problem.
    """
    try:
        from shapely.geometry import Point as ShapelyPoint
    except ImportError as exc:
        raise ImportError(
            "The comb potential solver requires Shapely."
        ) from exc

    incident: list[tuple[float, float]] = []
    distance_limit = max(10.0 * float(tolerance), 1.0e-14)

    for component in _potential_polygon_components(geometry):
        rings = [component.exterior, *list(component.interiors)]
        for ring in rings:
            coordinates = list(ring.coords)
            for p0, p1 in zip(coordinates[:-1], coordinates[1:]):
                _, distance, length = _potential_comb_point_segment_distance(
                    x=float(x),
                    y=float(y),
                    p0=(float(p0[0]), float(p0[1])),
                    p1=(float(p1[0]), float(p1[1])),
                )
                if distance > distance_limit or length <= float(_tol.EPS_L):
                    continue

                tx = (float(p1[0]) - float(p0[0])) / length
                ty = (float(p1[1]) - float(p0[1])) / length
                candidate_a = (ty, -tx)
                candidate_b = (-ty, tx)

                probe = max(100.0 * float(tolerance), 1.0e-9 * max(1.0, length))
                point_a = ShapelyPoint(
                    float(x) + probe * candidate_a[0],
                    float(y) + probe * candidate_a[1],
                )
                point_b = ShapelyPoint(
                    float(x) + probe * candidate_b[0],
                    float(y) + probe * candidate_b[1],
                )
                inside_a = geometry.covers(point_a)
                inside_b = geometry.covers(point_b)

                if inside_a and not inside_b:
                    outward = candidate_b
                elif inside_b and not inside_a:
                    outward = candidate_a
                else:
                    # When the probe falls too close to a corner, select the
                    # candidate whose probe is farther from the region interior.
                    distance_a = float(geometry.distance(point_a))
                    distance_b = float(geometry.distance(point_b))
                    outward = candidate_a if distance_a >= distance_b else candidate_b

                incident.append((float(outward[0]), float(outward[1])))

    if not incident:
        raise RuntimeError(
            "Could not determine an occupied-region normal at comb boundary "
            f"point ({x}, {y})."
        )

    nx = sum(value[0] for value in incident)
    ny = sum(value[1] for value in incident)
    norm = math.hypot(nx, ny)
    if norm <= 1.0e-14:
        # Opposite incident normals can occur at a degenerate geometric point.
        nx, ny = incident[0]
        norm = math.hypot(nx, ny)

    return float(nx / norm), float(ny / norm)


def _potential_comb_gfd_weights(
    *,
    query_point: tuple[float, float],
    region_node_indices,
    nodes,
    tree,
    operator: str,
    normal: tuple[float, float] | None = None,
    stencil_size: int = 12,
    max_stencil_size: int = 40,
) -> tuple[object, object, dict[str, float | int]]:
    """
    Return quadratic generalized-finite-difference weights at one point.

    A local quadratic polynomial is reconstructed from the nearest physical
    comb nodes belonging to one occupied CSF region.  The polynomial basis is

        1, xi, eta, xi^2, xi*eta, eta^2,

    with locally scaled coordinates.  The stencil is enlarged only when the
    six-term basis is rank deficient.  No cell, triangle or element-quality
    criterion enters the construction.
    """
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "The comb potential solver requires NumPy."
        ) from exc

    region_node_indices = np.asarray(region_node_indices, dtype=int)
    if len(region_node_indices) < 6:
        raise RuntimeError(
            "A quadratic comb stencil requires at least six nodes in each "
            "occupied region. Increase num_sudx/num_sudy."
        )

    initial = max(6, int(stencil_size))
    maximum = max(initial, int(max_stencil_size))
    maximum = min(maximum, len(region_node_indices))
    query = np.asarray(query_point, dtype=float)

    selected_local = None
    matrix = None
    scale = None
    rank = 0
    condition = float("inf")

    for count in range(initial, maximum + 1, 2):
        distances, local_indices = tree.query(query, k=min(count, len(region_node_indices)))
        local_indices = np.atleast_1d(local_indices).astype(int)
        global_indices = region_node_indices[local_indices]
        points = nodes[global_indices]
        delta = points - query[None, :]
        radius = float(np.max(np.linalg.norm(delta, axis=1)))
        if radius <= float(_tol.EPS_L):
            continue

        xi = delta[:, 0] / radius
        eta = delta[:, 1] / radius
        candidate_matrix = np.column_stack(
            (
                np.ones(len(global_indices)),
                xi,
                eta,
                xi * xi,
                xi * eta,
                eta * eta,
            )
        )
        candidate_rank = int(np.linalg.matrix_rank(candidate_matrix))
        if candidate_rank < 6:
            continue

        selected_local = global_indices
        matrix = candidate_matrix
        scale = radius
        rank = candidate_rank
        condition = float(np.linalg.cond(candidate_matrix))
        break

    if selected_local is None or matrix is None or scale is None:
        raise RuntimeError(
            "Could not build a full-rank quadratic comb stencil. Increase "
            "num_sudx/num_sudy or inspect the local point topology."
        )

    pseudoinverse = np.linalg.pinv(matrix, rcond=1.0e-12)

    if operator == "laplacian":
        derivative = np.asarray(
            (0.0, 0.0, 0.0, 2.0 / scale**2, 0.0, 2.0 / scale**2),
            dtype=float,
        )
    elif operator == "grad_x":
        derivative = np.asarray((0.0, 1.0 / scale, 0.0, 0.0, 0.0, 0.0), dtype=float)
    elif operator == "grad_y":
        derivative = np.asarray((0.0, 0.0, 1.0 / scale, 0.0, 0.0, 0.0), dtype=float)
    elif operator == "grad_n":
        if normal is None:
            raise ValueError("normal is required for operator='grad_n'.")
        nx, ny = map(float, normal)
        derivative = np.asarray(
            (0.0, nx / scale, ny / scale, 0.0, 0.0, 0.0),
            dtype=float,
        )
    elif operator == "value":
        derivative = np.asarray((1.0, 0.0, 0.0, 0.0, 0.0, 0.0), dtype=float)
    else:
        raise ValueError(f"Unsupported comb GFD operator: {operator!r}.")

    weights = derivative @ pseudoinverse
    return (
        selected_local,
        np.asarray(weights, dtype=float),
        {
            "stencil_size": int(len(selected_local)),
            "rank": int(rank),
            "condition": float(condition),
            "radius": float(scale),
        },
    )


def analyse_navier_local_shear_potential_comb(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    *,
    dN_dz: float = 0.0,
    dz: float | None = None,
    num_sudx: int = 5,
    num_sudy: int = 5,
    stencil_size: int = 12,
    max_stencil_size: int = 40,
    solver_atol: float = 1.0e-10,
    solver_btol: float = 1.0e-10,
    solver_maxiter: int | None = None,
) -> dict[str, object]:
    """
    Solve the CSF local shear-potential equation on the approved 2D comb points.

    Numerical method
    ----------------
    This implementation deliberately does not create triangles, quadrilateral
    cells or cut cells.  The physical nodes are exactly the union of:

    1. valid x/y comb intersections inside the occupied shear domain;
    2. intersections of x/y comb lines with CSF polygon boundaries.

    The same scalar-potential closure already used by the P1 FEM path is kept:

        tau = G_like * grad(phi)
        div(tau) = -partial(sigma_zz)/partial(z).

    The new numerical discretization is quadratic generalized finite difference
    (GFD) collocation on that point network.  Interior nodes enforce the PDE;
    external-boundary nodes enforce the moving-boundary normal-flux condition;
    two-region interface nodes enforce the established normal-flux jump.

    The local quadratic stencil starts at ``stencil_size`` nearest points in the
    same occupied CSF region and is enlarged only when the six-term polynomial
    basis is rank deficient.  This is a point-stencil choice, not a mesh-quality
    rule.  The only geometric refinement remains ``num_sudx``/``num_sudy``.

    One potential value is stored per unique physical node.  Continuity of phi
    across a two-region interface is therefore automatic.  Junctions where more
    than two active shear regions meet at exactly one collocation point are not
    silently approximated and are rejected explicitly in this first graph/GFD
    implementation.
    """
    try:
        import numpy as np
        from scipy.spatial import cKDTree
        from scipy.sparse import coo_matrix
        from scipy.sparse.linalg import lsmr
        from shapely.geometry import Point as ShapelyPoint
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential_comb() requires NumPy, "
            "SciPy and Shapely."
        ) from exc

    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)
    dN_dz = float(dN_dz)

    if abs(dN_dz) > 0.0:
        raise NotImplementedError(
            "The comb potential solver currently requires dN_dz = 0, exactly "
            "as the existing local-potential formulation."
        )

    network = _potential_comb_network_nodes(
        section_field,
        z,
        num_sudx=int(num_sudx),
        num_sudy=int(num_sudy),
    )
    grid = network["grid"]
    regions = list(grid["regions"])
    domain = grid["domain"]
    nodes, geometry_tolerance = _potential_comb_merge_nodes(network)

    node_regions, region_nodes = _potential_comb_region_membership(
        nodes=nodes,
        regions=regions,
        tolerance=geometry_tolerance,
    )

    # Remove raw-polygon intersection points that are not part of the active
    # shear domain after occupied-region construction.
    keep = [idx for idx, membership in enumerate(node_regions) if membership]
    if len(keep) != len(nodes):
        nodes = nodes[np.asarray(keep, dtype=int)]
        node_regions, region_nodes = _potential_comb_region_membership(
            nodes=nodes,
            regions=regions,
            tolerance=geometry_tolerance,
        )

    node_count = int(len(nodes))
    region_trees = []
    region_global_indices = []
    for indices in region_nodes:
        global_indices = np.asarray(indices, dtype=int)
        if len(global_indices) < 6:
            raise RuntimeError(
                "An occupied CSF region has fewer than six comb nodes. "
                "Increase num_sudx/num_sudy."
            )
        region_global_indices.append(global_indices)
        region_trees.append(cKDTree(nodes[global_indices]))

    derivative_context = _potential_derivative_context(
        section_field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
        Tx=Tx,
        Ty=Ty,
        dz=dz,
    )
    base_state = derivative_context["base_state"]

    row_indices: list[int] = []
    col_indices: list[int] = []
    matrix_values: list[float] = []
    rhs_values: list[float] = []
    equation_kind: list[str] = []
    stencil_conditions: list[float] = []
    stencil_sizes: list[int] = []

    def append_equation(
        coefficients: dict[int, float],
        rhs_value: float,
        kind: str,
    ) -> None:
        row = len(rhs_values)
        indices = list(coefficients)
        values = np.asarray([float(coefficients[idx]) for idx in indices], dtype=float)
        norm = float(np.linalg.norm(values))
        if not math.isfinite(norm) or norm <= 0.0:
            raise RuntimeError(f"Degenerate comb collocation equation: {kind}.")
        values /= norm
        rhs_scaled = float(rhs_value) / norm
        for idx, value in zip(indices, values):
            if value != 0.0:
                row_indices.append(row)
                col_indices.append(int(idx))
                matrix_values.append(float(value))
        rhs_values.append(rhs_scaled)
        equation_kind.append(str(kind))

    for node_idx, (x_value, y_value) in enumerate(nodes):
        memberships = tuple(node_regions[node_idx])
        point = ShapelyPoint(float(x_value), float(y_value))
        boundary_memberships = tuple(
            region_idx
            for region_idx in memberships
            if regions[region_idx]["geometry"].boundary.distance(point)
            <= 10.0 * geometry_tolerance
        )

        if len(memberships) > 2:
            raise NotImplementedError(
                "The comb GFD solver encountered a collocation node shared by "
                f"{len(memberships)} active regions at ({x_value}, {y_value}). "
                "Multi-region junction equations are not introduced silently."
            )

        if len(memberships) == 2:
            region_i, region_j = memberships
            normal = _potential_comb_region_outward_normal(
                regions[region_i]["geometry"],
                x=float(x_value),
                y=float(y_value),
                tolerance=geometry_tolerance,
            )

            # Orient n from region i toward region j when the local geometry is
            # not a corner. A short normal probe is enough because the regions
            # form a non-overlapping partition.
            probe = max(100.0 * geometry_tolerance, 1.0e-9)
            probe_point = ShapelyPoint(
                float(x_value) + probe * normal[0],
                float(y_value) + probe * normal[1],
            )
            if not regions[region_j]["geometry"].buffer(geometry_tolerance).covers(probe_point):
                normal = (-normal[0], -normal[1])

            coefficients: dict[int, float] = {}
            for sign, region_idx in ((+1.0, region_i), (-1.0, region_j)):
                indices, weights, diagnostics = _potential_comb_gfd_weights(
                    query_point=(float(x_value), float(y_value)),
                    region_node_indices=region_global_indices[region_idx],
                    nodes=nodes,
                    tree=region_trees[region_idx],
                    operator="grad_n",
                    normal=normal,
                    stencil_size=stencil_size,
                    max_stencil_size=max_stencil_size,
                )
                stencil_conditions.append(float(diagnostics["condition"]))
                stencil_sizes.append(int(diagnostics["stencil_size"]))
                g_like = float(regions[region_idx]["shear_weightabs"])
                for global_idx, weight in zip(indices, weights):
                    coefficients[int(global_idx)] = coefficients.get(int(global_idx), 0.0) + sign * g_like * float(weight)

            vx, vy = _potential_boundary_velocity_at_point(
                derivative_context,
                x=float(x_value),
                y=float(y_value),
                geometry_tolerance=20.0 * geometry_tolerance,
            )
            normal_velocity = vx * normal[0] + vy * normal[1]
            sigma_i = _navier_sigma_at_point(
                poly=base_state["section"].polygons[int(regions[region_i]["polygon_idx"])],
                x=float(x_value),
                y=float(y_value),
                state=base_state,
            )
            sigma_j = _navier_sigma_at_point(
                poly=base_state["section"].polygons[int(regions[region_j]["polygon_idx"])],
                x=float(x_value),
                y=float(y_value),
                state=base_state,
            )
            append_equation(
                coefficients,
                (float(sigma_i) - float(sigma_j)) * float(normal_velocity),
                "interface_flux_jump",
            )
            continue

        region_idx = int(memberships[0])
        is_boundary = bool(boundary_memberships)

        if is_boundary:
            normal = _potential_comb_region_outward_normal(
                regions[region_idx]["geometry"],
                x=float(x_value),
                y=float(y_value),
                tolerance=geometry_tolerance,
            )
            indices, weights, diagnostics = _potential_comb_gfd_weights(
                query_point=(float(x_value), float(y_value)),
                region_node_indices=region_global_indices[region_idx],
                nodes=nodes,
                tree=region_trees[region_idx],
                operator="grad_n",
                normal=normal,
                stencil_size=stencil_size,
                max_stencil_size=max_stencil_size,
            )
            stencil_conditions.append(float(diagnostics["condition"]))
            stencil_sizes.append(int(diagnostics["stencil_size"]))
            g_like = float(regions[region_idx]["shear_weightabs"])
            coefficients = {
                int(global_idx): g_like * float(weight)
                for global_idx, weight in zip(indices, weights)
            }
            vx, vy = _potential_boundary_velocity_at_point(
                derivative_context,
                x=float(x_value),
                y=float(y_value),
                geometry_tolerance=20.0 * geometry_tolerance,
            )
            normal_velocity = vx * normal[0] + vy * normal[1]
            sigma = _navier_sigma_at_point(
                poly=base_state["section"].polygons[int(regions[region_idx]["polygon_idx"])],
                x=float(x_value),
                y=float(y_value),
                state=base_state,
            )
            append_equation(
                coefficients,
                float(sigma) * float(normal_velocity),
                "external_flux",
            )
            continue

        indices, weights, diagnostics = _potential_comb_gfd_weights(
            query_point=(float(x_value), float(y_value)),
            region_node_indices=region_global_indices[region_idx],
            nodes=nodes,
            tree=region_trees[region_idx],
            operator="laplacian",
            stencil_size=stencil_size,
            max_stencil_size=max_stencil_size,
        )
        stencil_conditions.append(float(diagnostics["condition"]))
        stencil_sizes.append(int(diagnostics["stencil_size"]))
        g_like = float(regions[region_idx]["shear_weightabs"])
        coefficients = {
            int(global_idx): g_like * float(weight)
            for global_idx, weight in zip(indices, weights)
        }
        sigma_z = _potential_sigma_z_at_point(
            derivative_context,
            polygon_idx=int(regions[region_idx]["polygon_idx"]),
            x=float(x_value),
            y=float(y_value),
        )
        append_equation(coefficients, -float(sigma_z), "interior_pde")

    if len(rhs_values) != node_count:
        raise RuntimeError(
            "The comb collocation builder must create exactly one physical "
            f"equation per node; got {len(rhs_values)} equations for {node_count} nodes."
        )

    # The physical Neumann problem has one arbitrary additive constant per
    # connected shear-domain component. Add one zero-mean gauge row for each
    # Shapely polygonal component. The physical equations remain untouched;
    # LSMR solves the resulting consistent overdetermined system.
    components = _potential_polygon_components(domain)
    gauge_count = 0
    for component_idx, component in enumerate(components):
        component_nodes = [
            idx
            for idx, (x_value, y_value) in enumerate(nodes)
            if component.covers(ShapelyPoint(float(x_value), float(y_value)))
            or component.boundary.distance(ShapelyPoint(float(x_value), float(y_value)))
            <= geometry_tolerance
        ]
        if not component_nodes:
            continue
        row = len(rhs_values)
        coefficient = 1.0 / math.sqrt(float(len(component_nodes)))
        for node_idx in component_nodes:
            row_indices.append(row)
            col_indices.append(int(node_idx))
            matrix_values.append(float(coefficient))
        rhs_values.append(0.0)
        equation_kind.append(f"gauge_component_{component_idx}")
        gauge_count += 1

    matrix = coo_matrix(
        (matrix_values, (row_indices, col_indices)),
        shape=(len(rhs_values), node_count),
        dtype=float,
    ).tocsr()
    rhs = np.asarray(rhs_values, dtype=float)

    maxiter = (
        max(1000, 5 * node_count)
        if solver_maxiter is None
        else int(solver_maxiter)
    )
    solution = lsmr(
        matrix,
        rhs,
        atol=float(solver_atol),
        btol=float(solver_btol),
        maxiter=maxiter,
    )
    phi = np.asarray(solution[0], dtype=float)
    residual = matrix @ phi - rhs

    result = {
        "method": "comb_quadratic_gfd_collocation",
        "z": z,
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
        "num_sudx": int(num_sudx),
        "num_sudy": int(num_sudy),
        "node_count": node_count,
        "comb_node_count_raw": int(len(network["comb_nodes"])),
        "polygon_node_count_raw": int(len(network["polygon_nodes"])),
        "gauge_count": int(gauge_count),
        "physical_equation_count": int(node_count),
        "equation_count": int(len(rhs_values)),
        "derivative_step": float(derivative_context["step"]),
        "derivative_scheme": str(derivative_context["scheme"]),
        "solver_istop": int(solution[1]),
        "solver_iterations": int(solution[2]),
        "solver_normr": float(solution[3]),
        "solver_normar": float(solution[4]),
        "solver_conda": float(solution[6]),
        "scaled_residual_inf": float(np.max(np.abs(residual))),
        "stencil_size_min": int(min(stencil_sizes)) if stencil_sizes else 0,
        "stencil_size_max": int(max(stencil_sizes)) if stencil_sizes else 0,
        "stencil_condition_max": float(max(stencil_conditions)) if stencil_conditions else float("nan"),
        "nodes": nodes,
        "phi": phi,
        "node_regions": tuple(node_regions),
        "equation_kind": tuple(equation_kind),
        # Private evaluation data retained so arbitrary comparison points can be
        # queried without rebuilding the point network or KD-trees.
        "_regions": regions,
        "_region_global_indices": region_global_indices,
        "_region_trees": region_trees,
        "_geometry_tolerance": float(geometry_tolerance),
        "_stencil_size": int(stencil_size),
        "_max_stencil_size": int(max_stencil_size),
    }
    return result


def evaluate_navier_local_shear_potential_comb(
    result: dict[str, object],
    *,
    x: float,
    y: float,
    polygon_idx: int | None = None,
) -> dict[str, float | int]:
    """Evaluate phi, tau_x and tau_y from a solved comb/GFD potential field."""
    try:
        import numpy as np
        from shapely.geometry import Point as ShapelyPoint
    except ImportError as exc:
        raise ImportError(
            "evaluate_navier_local_shear_potential_comb() requires NumPy and Shapely."
        ) from exc

    nodes = result["nodes"]
    phi = result["phi"]
    regions = result["_regions"]
    region_global_indices = result["_region_global_indices"]
    region_trees = result["_region_trees"]
    tolerance = float(result["_geometry_tolerance"])
    point = ShapelyPoint(float(x), float(y))

    candidates = [
        region_idx
        for region_idx, region in enumerate(regions)
        if region["geometry"].covers(point)
        or region["geometry"].boundary.distance(point) <= 10.0 * tolerance
    ]

    if polygon_idx is not None:
        polygon_matches = [
            region_idx
            for region_idx in candidates
            if int(regions[region_idx]["polygon_idx"]) == int(polygon_idx)
        ]
        if polygon_matches:
            candidates = polygon_matches

    if not candidates:
        raise ValueError(
            f"Point ({x}, {y}) is outside the active comb shear domain."
        )

    region_idx = int(candidates[0])
    common_arguments = dict(
        query_point=(float(x), float(y)),
        region_node_indices=region_global_indices[region_idx],
        nodes=nodes,
        tree=region_trees[region_idx],
        stencil_size=int(result["_stencil_size"]),
        max_stencil_size=int(result["_max_stencil_size"]),
    )

    values: dict[str, float] = {}
    for operator in ("value", "grad_x", "grad_y"):
        indices, weights, _ = _potential_comb_gfd_weights(
            **common_arguments,
            operator=operator,
        )
        values[operator] = float(np.dot(weights, phi[indices]))

    g_like = float(regions[region_idx]["shear_weightabs"])
    return {
        "region_idx": int(region_idx),
        "polygon_idx": int(regions[region_idx]["polygon_idx"]),
        "phi": float(values["value"]),
        "tau_x": float(g_like * values["grad_x"]),
        "tau_y": float(g_like * values["grad_y"]),
        "shear_weightabs": float(g_like),
    }


def plot_navier_local_shear_potential_comb(
    section_field,
    z: float,
    *,
    num_sudx: int = 20,
    num_sudy: int = 20,
) -> dict[str, object]:
    """
    Plot the geometry-driven 2D comb before any potential-field discretization.

    Geometric teeth are determined only by the CSF section geometry.  Every
    interval between two consecutive teeth is then divided into ``num_sudx``
    or ``num_sudy`` equal sub-intervals along the corresponding axis.

    The comb is clipped to the occupied CSF shear domain and the exact CSF
    polygon boundaries are overlaid.  No finite-element mesh is generated and
    no potential equation is solved.
    """
    try:
        import matplotlib.pyplot as plt
        from shapely.geometry import LineString
    except ImportError as exc:
        raise ImportError(
            "plot_navier_local_shear_potential_comb() requires Matplotlib "
            "and Shapely."
        ) from exc

    grid = _potential_comb_grid(
        section_field,
        float(z),
        num_sudx=int(num_sudx),
        num_sudy=int(num_sudy),
    )

    xmin, xmax, ymin, ymax = grid["bbox"]
    domain = grid["domain"]
    x_coords = list(grid["x_coords"])
    y_coords = list(grid["y_coords"])
    x_teeth = set(grid["x_teeth"])
    y_teeth = set(grid["y_teeth"])

    fig, ax = plt.subplots()

    def _draw_clipped_line(geometry, *, linewidth: float) -> None:
        if geometry.is_empty:
            return

        geom_type = geometry.geom_type
        if geom_type in ("LineString", "LinearRing"):
            xs, ys = geometry.xy
            ax.plot(xs, ys, linewidth=linewidth)
            return

        if hasattr(geometry, "geoms"):
            for part in geometry.geoms:
                _draw_clipped_line(part, linewidth=linewidth)

    for x_value in x_coords:
        line = LineString(((float(x_value), ymin), (float(x_value), ymax)))
        clipped = domain.intersection(line)
        is_tooth = any(abs(float(x_value) - t) <= _tol.EPS_L for t in x_teeth)
        _draw_clipped_line(clipped, linewidth=1.0 if is_tooth else 0.35)

    for y_value in y_coords:
        line = LineString(((xmin, float(y_value)), (xmax, float(y_value))))
        clipped = domain.intersection(line)
        is_tooth = any(abs(float(y_value) - t) <= _tol.EPS_L for t in y_teeth)
        _draw_clipped_line(clipped, linewidth=1.0 if is_tooth else 0.35)

    # Exact CSF polygon boundaries remain visible independently of the comb.
    section = section_field.section(float(z))
    for poly in section.polygons:
        if not poly.vertices:
            continue
        xs = [float(vertex.x) for vertex in poly.vertices]
        ys = [float(vertex.y) for vertex in poly.vertices]
        xs.append(xs[0])
        ys.append(ys[0])
        ax.plot(xs, ys, linewidth=1.4)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(
        "Potential 2D comb preview at "
        f"z={float(z):.6g} | "
        f"num_sudx={int(num_sudx)} | "
        f"num_sudy={int(num_sudy)} | "
        f"x_teeth={len(x_teeth)} | "
        f"y_teeth={len(y_teeth)} | "
        f"x_lines={len(x_coords)} | "
        f"y_lines={len(y_coords)}"
    )
    fig.tight_layout()
    plt.show()

    # Do not expose Shapely objects in the public diagnostic result.
    return {
        key: value
        for key, value in grid.items()
        if key not in ("regions", "domain")
    }


def _potential_triangle_area_gradients(points):
    """
    Return triangle area and constant P1 shape-function gradients.

    For a linear triangular potential

        phi = sum_i N_i * phi_i,

    each ``grad(N_i)`` is constant. Therefore ``grad(phi)`` and the recovered
    triangle shear vector ``G_like * grad(phi)`` are constant over the element.
    Non-positive orientation is rejected because it would reverse the adopted
    geometric conventions.
    """
    import numpy as np

    x1, y1 = map(float, points[0])
    x2, y2 = map(float, points[1])
    x3, y3 = map(float, points[2])

    determinant = (
        (x2 - x1) * (y3 - y1)
        - (x3 - x1) * (y2 - y1)
    )

    if determinant <= 0.0:
        raise ValueError(
            "The potential mesh contains a non-positive triangle."
        )

    area = 0.5 * determinant
    gradients = np.asarray(
        (
            (y2 - y3, x3 - x2),
            (y3 - y1, x1 - x3),
            (y1 - y2, x2 - x1),
        ),
        dtype=float,
    ) / determinant

    return float(area), gradients


def _potential_derivative_context(
    section_field,
    *,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    dz: float | None,
) -> dict[str, object]:
    """
    Build a common second-order z-derivative stencil for stress and geometry.

    The same stencil is used for:
    - the complete Navier-stress derivative at fixed physical (x, y);
    - vertex velocities dx/dz and dy/dz used by moving-boundary conditions.

    Keeping those derivatives on one stencil is important: the domain motion
    and the stress source must represent the same local section evolution.

    The neighbouring section-action states use the established CSF tangent
    convention

        dMx/dz = Ty
        dMy/dz = Tx,

    while N is held constant in this first implementation. Interior stations
    use a second-order central difference; CSF endpoints use second-order
    one-sided formulas.

    ``dz=None`` does not perform an iterative convergence search here. It selects
    a small scale-based step (1e-5 times the CSF length). Callers that require a
    controlled derivative step can pass ``dz`` explicitly.
    """
    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)

    z_start = float(section_field.s0.z)
    z_end = float(section_field.s1.z)

    if z_end <= z_start:
        raise ValueError("The CSF bounds must satisfy s1.z > s0.z.")
    if z < z_start or z > z_end:
        raise ValueError(
            f"z={z} is outside CSF bounds [{z_start}, {z_end}]."
        )

    length = z_end - z_start
    requested_step = (
        1.0e-5 * length
        if dz is None
        else float(dz)
    )

    if (
        not math.isfinite(requested_step)
        or requested_step <= 0.0
    ):
        raise ValueError("dz must be a finite positive number.")

    coordinate_tolerance = max(
        1.0e-14,
        1.0e-12 * length,
    )

    left = z - z_start
    right = z_end - z
    at_start = left <= coordinate_tolerance
    at_end = right <= coordinate_tolerance

    if not at_start and not at_end:
        h = min(requested_step, left, right)
        offsets = (-h, +h)
        coefficients = (-1.0, +1.0)
        denominator = 2.0 * h
        scheme = "central_second_order"

    elif at_start:
        h = min(requested_step, 0.5 * right)
        offsets = (0.0, +h, +2.0 * h)
        coefficients = (-3.0, +4.0, -1.0)
        denominator = 2.0 * h
        scheme = "forward_second_order"

    else:
        h = min(requested_step, 0.5 * left)
        offsets = (0.0, -h, -2.0 * h)
        coefficients = (+3.0, -4.0, +1.0)
        denominator = 2.0 * h
        scheme = "backward_second_order"

    if h <= coordinate_tolerance:
        raise ValueError(
            f"Potential derivative step is too small at z={z}."
        )

    def actions_at_offset(
        delta_z: float,
    ) -> tuple[float, float, float]:
        return (
            float(N),
            float(Mx + Ty * delta_z),
            float(My + Tx * delta_z),
        )

    states: dict[float, dict[str, object]] = {}

    for offset in set(offsets) | {0.0}:
        N_eval, Mx_eval, My_eval = actions_at_offset(offset)
        states[float(offset)] = _navier_section_state(
            section_field=section_field,
            z=z + float(offset),
            N=N_eval,
            Mx=Mx_eval,
            My=My_eval,
        )

    base_section = states[0.0]["section"]
    polygon_count = len(base_section.polygons)

    for state in states.values():
        section = state["section"]

        if len(section.polygons) != polygon_count:
            raise ValueError(
                "Polygon count changes across the local derivative stencil."
            )

        for idx in range(polygon_count):
            if (
                len(section.polygons[idx].vertices)
                != len(base_section.polygons[idx].vertices)
            ):
                raise ValueError(
                    "Polygon vertex count changes across the local "
                    f"derivative stencil for polygon index {idx}."
                )

    vertex_velocity: list[list[tuple[float, float]]] = []

    for polygon_idx, base_poly in enumerate(base_section.polygons):
        velocities: list[tuple[float, float]] = []

        for vertex_idx in range(len(base_poly.vertices)):
            vx_numerator = 0.0
            vy_numerator = 0.0

            for offset, coefficient in zip(
                offsets,
                coefficients,
            ):
                point = states[float(offset)]["section"].polygons[
                    polygon_idx
                ].vertices[vertex_idx]

                vx_numerator += (
                    float(coefficient) * float(point.x)
                )
                vy_numerator += (
                    float(coefficient) * float(point.y)
                )

            velocities.append(
                (
                    float(vx_numerator / denominator),
                    float(vy_numerator / denominator),
                )
            )

        vertex_velocity.append(velocities)

    return {
        "z": z,
        "step": float(h),
        "scheme": scheme,
        "dz_mode": (
            "automatic_scale"
            if dz is None
            else "explicit"
        ),
        "offsets": tuple(float(value) for value in offsets),
        "coefficients": tuple(
            float(value)
            for value in coefficients
        ),
        "denominator": float(denominator),
        "states": states,
        "base_state": states[0.0],
        "vertex_velocity": vertex_velocity,
    }


def _potential_sigma_z_at_point(
    derivative_context: dict[str, object],
    *,
    polygon_idx: int,
    x: float,
    y: float,
) -> float:
    """
    Evaluate partial(sigma_zz)/partial(z) at a fixed global point.

    The point coordinates are intentionally *not* convected with a polygon.
    Each stencil station reconstructs the complete Navier state of its actual
    CSF section and evaluates that state at the same spatial (x, y). This is the
    Eulerian derivative required by the local equilibrium equation.

    Geometry variation, centroid motion, inertia variation, polygon
    ``weightabs`` variation and the local action gradients are therefore all
    differentiated together rather than introduced as separate correction
    terms.
    """
    numerator = 0.0

    for offset, coefficient in zip(
        derivative_context["offsets"],
        derivative_context["coefficients"],
    ):
        state = derivative_context["states"][float(offset)]
        poly = state["section"].polygons[int(polygon_idx)]

        sigma = _navier_sigma_at_point(
            poly=poly,
            x=float(x),
            y=float(y),
            state=state,
        )
        numerator += float(coefficient) * sigma

    return float(
        numerator / float(derivative_context["denominator"])
    )


def _potential_point_segment_parameter(
    *,
    x: float,
    y: float,
    p0: Pt,
    p1: Pt,
) -> tuple[float, float]:
    """
    Project a physical point onto one finite polygon edge.

    The clamped segment parameter is later used to interpolate the two endpoint
    velocities of that moving CSF edge. The returned distance is the geometric
    criterion used to decide whether a finite-element boundary quadrature point
    belongs to the original CSF edge.
    """
    x0 = float(p0.x)
    y0 = float(p0.y)
    dx = float(p1.x) - x0
    dy = float(p1.y) - y0
    length_squared = dx * dx + dy * dy

    if length_squared <= _tol.EPS_L * _tol.EPS_L:
        return 0.0, float("inf")

    t = (
        (float(x) - x0) * dx
        + (float(y) - y0) * dy
    ) / length_squared
    t_clamped = min(1.0, max(0.0, float(t)))

    px = x0 + t_clamped * dx
    py = y0 + t_clamped * dy
    distance = math.hypot(
        float(x) - px,
        float(y) - py,
    )

    return float(t_clamped), float(distance)


def _potential_boundary_velocity_at_point(
    derivative_context: dict[str, object],
    *,
    x: float,
    y: float,
    geometry_tolerance: float,
) -> tuple[float, float]:
    """
    Return the in-plane velocity of a physical CSF boundary/interface point.

    Vertex correspondence between the endpoint sections defines the motion of
    each CSF polygon edge. Once a mesh quadrature point is mapped back to such an
    edge, its velocity is obtained by linear interpolation between the two edge
    endpoint velocities.

    Shared material interfaces can be represented by the boundaries of two
    different polygons. In that case all matching geometric descriptions must
    predict the same physical velocity. The consistency check is deliberate:
    applying two incompatible interface motions would make the Neumann jump
    condition mechanically undefined.
    """
    section = derivative_context["base_state"]["section"]
    vertex_velocity = derivative_context["vertex_velocity"]

    candidates: list[tuple[float, float]] = []

    for polygon_idx, poly in enumerate(section.polygons):
        vertices = poly.vertices
        velocities = vertex_velocity[polygon_idx]

        for edge_idx, p0 in enumerate(vertices):
            p1 = vertices[(edge_idx + 1) % len(vertices)]
            t, distance = _potential_point_segment_parameter(
                x=float(x),
                y=float(y),
                p0=p0,
                p1=p1,
            )

            if distance > geometry_tolerance:
                continue

            v0x, v0y = velocities[edge_idx]
            v1x, v1y = velocities[
                (edge_idx + 1) % len(vertices)
            ]

            candidates.append(
                (
                    float((1.0 - t) * v0x + t * v1x),
                    float((1.0 - t) * v0y + t * v1y),
                )
            )

    if not candidates:
        raise RuntimeError(
            "Unable to map a potential-mesh boundary point to the "
            f"moving CSF polygon geometry at ({x}, {y})."
        )

    vx = sum(value[0] for value in candidates) / len(candidates)
    vy = sum(value[1] for value in candidates) / len(candidates)

    velocity_scale = max(
        1.0,
        abs(vx),
        abs(vy),
    )
    velocity_tolerance = 1.0e-7 * velocity_scale

    for candidate_vx, candidate_vy in candidates:
        if (
            abs(candidate_vx - vx) > velocity_tolerance
            or abs(candidate_vy - vy) > velocity_tolerance
        ):
            raise ValueError(
                "Inconsistent kinematics on a shared moving polygon "
                f"boundary at ({x}, {y})."
            )

    return float(vx), float(vy)


def _potential_edge_normal_from_triangle(
    *,
    p0,
    p1,
    triangle_centroid,
) -> tuple[float, float]:
    """
    Return the unit normal directed out of one adjacent triangle.

    Mesh edges are stored without orientation. The trial right-hand normal is
    therefore tested against the triangle centroid and reversed when necessary.
    On a one-sided edge this produces the outward normal of the active
    finite-element domain.
    """
    tx = float(p1[0] - p0[0])
    ty = float(p1[1] - p0[1])
    length = math.hypot(tx, ty)

    if length <= _tol.EPS_L:
        raise ValueError("Degenerate potential-mesh edge.")

    nx = ty / length
    ny = -tx / length

    midpoint_x = 0.5 * float(p0[0] + p1[0])
    midpoint_y = 0.5 * float(p0[1] + p1[1])

    to_centroid_x = float(triangle_centroid[0]) - midpoint_x
    to_centroid_y = float(triangle_centroid[1]) - midpoint_y

    if nx * to_centroid_x + ny * to_centroid_y > 0.0:
        nx = -nx
        ny = -ny

    return float(nx), float(ny)


def _potential_edge_normal_between_triangles(
    *,
    p0,
    p1,
    centroid_i,
    centroid_j,
) -> tuple[float, float]:
    """
    Return a deterministic unit normal from material side i to material side j.

    This orientation is used only to write the moving-interface jump condition
    with a consistent sign. Reversing both the normal and the i/j ordering would
    produce the same physical weak contribution.
    """
    tx = float(p1[0] - p0[0])
    ty = float(p1[1] - p0[1])
    length = math.hypot(tx, ty)

    if length <= _tol.EPS_L:
        raise ValueError("Degenerate potential-mesh interface edge.")

    nx = ty / length
    ny = -tx / length

    direction_x = float(centroid_j[0] - centroid_i[0])
    direction_y = float(centroid_j[1] - centroid_i[1])

    if nx * direction_x + ny * direction_y < 0.0:
        nx = -nx
        ny = -ny

    return float(nx), float(ny)


def _potential_mesh_edges(connectivity) -> dict[tuple[int, int], list[int]]:
    """
    Build the edge-to-adjacent-triangles topology of the conforming mesh.

    One adjacent triangle identifies an external/void boundary edge. Two
    adjacent triangles identify an internal mesh edge and may also represent a
    material interface when their polygon indices differ. More than two adjacent
    triangles would be non-manifold and is rejected.
    """
    edges: dict[tuple[int, int], list[int]] = {}

    for triangle_idx, triangle in enumerate(connectivity):
        for local_a, local_b in ((0, 1), (1, 2), (2, 0)):
            a = int(triangle[local_a])
            b = int(triangle[local_b])
            key = (a, b) if a < b else (b, a)
            edges.setdefault(key, []).append(int(triangle_idx))

    for edge, adjacent in edges.items():
        if len(adjacent) > 2:
            raise RuntimeError(
                "Non-manifold potential mesh edge "
                f"{edge} with {len(adjacent)} adjacent triangles."
            )

    return edges


def _potential_connected_components(
    *,
    node_count: int,
    connectivity,
) -> list[list[int]]:
    """
    Return the node-connected components of the active shear mesh.

    A pure-Neumann potential problem has one additive constant for each
    disconnected component. The component list is therefore used to create one
    independent zero-mean gauge equation per component rather than assuming the
    section is geometrically connected.
    """
    parent = list(range(int(node_count)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(a: int, b: int) -> None:
        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a

    for triangle in connectivity:
        a, b, c = map(int, triangle)
        union(a, b)
        union(b, c)
        union(c, a)

    grouped: dict[int, list[int]] = {}

    for node_idx in range(int(node_count)):
        grouped.setdefault(
            find(node_idx),
            [],
        ).append(node_idx)

    return list(grouped.values())


def _potential_triangle_cut_interval(
    points,
    *,
    axis: str,
    value: float,
    tolerance: float,
) -> tuple[float, float] | None:
    """
    Intersect one P1 triangle with a global horizontal or vertical validation cut.

    The local shear field is constant inside each triangle, so only the length
    of the cut segment inside that triangle is required for chord integration.
    Cuts coincident with a complete triangle edge are rejected because ownership
    would otherwise be ambiguous; validation points should be moved slightly.
    """
    if axis == "horizontal":
        coordinates = points[:, 1]
        orthogonal = points[:, 0]
    elif axis == "vertical":
        coordinates = points[:, 0]
        orthogonal = points[:, 1]
    else:
        raise ValueError(
            "axis must be 'horizontal' or 'vertical'."
        )

    values: list[float] = []

    for edge_idx in range(3):
        next_idx = (edge_idx + 1) % 3

        c0 = float(coordinates[edge_idx])
        c1 = float(coordinates[next_idx])
        o0 = float(orthogonal[edge_idx])
        o1 = float(orthogonal[next_idx])

        d0 = c0 - float(value)
        d1 = c1 - float(value)

        if abs(d0) <= tolerance and abs(d1) <= tolerance:
            raise ValueError(
                "A validation cut coincides with a potential-mesh "
                "triangle edge. Move the validation point slightly."
            )

        if abs(d0) <= tolerance:
            values.append(o0)

        if d0 * d1 < -(tolerance * tolerance):
            t = (float(value) - c0) / (c1 - c0)
            values.append(o0 + t * (o1 - o0))

    unique: list[float] = []

    for candidate in values:
        if not any(
            abs(candidate - previous) <= 10.0 * tolerance
            for previous in unique
        ):
            unique.append(float(candidate))

    if len(unique) < 2:
        return None

    return min(unique), max(unique)


def _potential_partial_chord_flows(
    triangle_rows: list[dict[str, object]],
    *,
    x: float,
    y: float,
    tolerance: float,
) -> dict[str, float]:
    """
    Integrate the recovered shear field over the four half-chords through a point.

    ``H_L`` and ``H_R`` integrate tau_y to the left and right of the point on
    the horizontal chord. ``V_B`` and ``V_T`` integrate tau_x below and above
    the point on the vertical chord.

    These four scalar flows are the quantities that enter the independent
    Four-Quadrant equilibrium identities. No fitting or correction is applied
    to them.
    """
    import numpy as np

    H_L = 0.0
    H_R = 0.0
    V_B = 0.0
    V_T = 0.0

    for row in triangle_rows:
        points = np.asarray(
            (
                (float(row["x0"]), float(row["y0"])),
                (float(row["x1"]), float(row["y1"])),
                (float(row["x2"]), float(row["y2"])),
            ),
            dtype=float,
        )

        horizontal = _potential_triangle_cut_interval(
            points,
            axis="horizontal",
            value=float(y),
            tolerance=tolerance,
        )

        if horizontal is not None:
            x0, x1 = horizontal

            left_length = (
                max(0.0, min(float(x), x1) - x0)
                if float(x) > x0
                else 0.0
            )
            right_length = (
                max(0.0, x1 - max(float(x), x0))
                if float(x) < x1
                else 0.0
            )

            H_L += float(row["tau_y"]) * left_length
            H_R += float(row["tau_y"]) * right_length

        vertical = _potential_triangle_cut_interval(
            points,
            axis="vertical",
            value=float(x),
            tolerance=tolerance,
        )

        if vertical is not None:
            y0, y1 = vertical

            bottom_length = (
                max(0.0, min(float(y), y1) - y0)
                if float(y) > y0
                else 0.0
            )
            top_length = (
                max(0.0, y1 - max(float(y), y0))
                if float(y) < y1
                else 0.0
            )

            V_B += float(row["tau_x"]) * bottom_length
            V_T += float(row["tau_x"]) * top_length

    return {
        "H_L": float(H_L),
        "H_R": float(H_R),
        "V_B": float(V_B),
        "V_T": float(V_T),
    }


def analyse_navier_local_shear_potential_triangle_mesh(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    *,
    dN_dz: float = 0.0,
    dz: float | None = None,
    max_triangle_area: float | None = None,
    min_angle: float | None = None,
    plot_mesh: bool = False,
    validation_points: tuple[tuple[float, float], ...] | None = None,
    compatibility_rtol: float = 1.0e-8,
    compatibility_atol: float = 1.0e-6,
) -> dict[str, object]:
    """
    Recover a local in-plane shear field from complete Navier equilibrium.

    Mechanical definition
    ---------------------
    At the requested station the function first constructs the complete CSF
    Navier stress field ``sigma_zz(x, y, z)`` using the physical section
    geometry, polygon ``weightabs`` values and the supplied section actions.
    Its longitudinal derivative is then evaluated at fixed global coordinates.

    The local shear field is selected through the minimum-complementary-energy
    closure

        tau = G_like * grad(phi),

    with

        div(tau) = -partial(sigma_zz) / partial(z),

    or equivalently

        div(G_like * grad(phi))
            = -partial(sigma_zz) / partial(z).

    ``G_like`` is the sampled polygon ``shear_weightabs``. It is not derived
    from ``weightabs`` inside this routine and it is not replaced by a global
    effective shear modulus.

    This formulation is deliberately based on the derivative of the *complete*
    Navier field. Centroid motion, inertia variation, material participation
    variation and action gradients are therefore already contained in the
    source. They must not be added again as independent taper or centroid
    corrections.

    Action-gradient convention
    --------------------------
    The local neighbouring action states follow the CSF convention

        dMx/dz = Ty
        dMy/dz = Tx.

    ``N`` is currently held constant. Accordingly ``dN_dz`` is accepted only
    when it is zero; see "Axial distributed loading" below.

    Occupied-region topology
    ------------------------
    The transverse domain is built with the same index-based containment rule
    used by the Four-Quadrant routines:

        occupied(parent)
            = parent - union(direct children).

    This prevents double counting of nested material polygons. A region with
    negligible ``weightabs`` and negligible ``shear_weightabs`` acts as a true
    void and remains excluded from the active domain. A region carrying Navier
    stress but having no positive shear carrier is rejected because the
    elliptic closure would be locally degenerate.

    Moving external boundaries
    --------------------------
    CSF vertex correspondence defines an in-plane boundary velocity

        v = (dx/dz, dy/dz).

    On an external moving boundary the reduced traction condition is

        tau . n = sigma_zz * v_n,

    where ``n`` is the outward unit normal and ``v_n = v . n``. A fixed external
    boundary has ``v_n = 0`` and therefore carries zero prescribed normal shear
    traction in this reduced problem.

    Moving material interfaces
    --------------------------
    When two active regions share a moving interface, the weak jump condition is

        (tau_i - tau_j) . n
            = (sigma_zz_i - sigma_zz_j) * v_n.

    Thus a fixed interface reduces automatically to continuity of normal shear
    traction. The interface velocity is checked from both polygon descriptions;
    inconsistent CSF interface kinematics raise an error instead of being
    averaged silently.

    Finite-element representation
    -----------------------------
    The actual CSF polygon vertices and boundary segments are passed directly
    to the Python ``triangle`` wrapper around Shewchuk's Triangle library as
    one PSLG. Shapely is not used for mesh construction or triangle material
    classification.

    ``max_triangle_area`` is the direct Triangle maximum-area constraint.
    ``min_angle`` is the direct Triangle minimum-angle quality constraint.
    Neither constraint is applied when its value is ``None``.

    There is no CSF post-meshing refinement loop, no nearest-neighbour stencil,
    no Triangle region seed and no Triangle hole seed. Each returned triangle
    is classified by the CSF containment hierarchy; outside/void triangles are
    discarded.

    The scalar potential uses conforming P1 triangles. Consequently
    ``grad(phi)`` and the returned ``tau_x, tau_y`` are piecewise constant by
    triangle.

    Mesh visualization
    ------------------
    When ``plot_mesh=True``, the final triangulation and the exact CSF polygon
    boundaries are displayed after mesh generation and before FEM assembly.
    The visualization is diagnostic only and does not modify the mesh, the
    assembled system or the returned solution. Matplotlib is required only
    when this option is enabled.

    Pure-Neumann compatibility and gauge
    ------------------------------------
    The local problem is Neumann-only. For every disconnected active component,
    solvability requires equality between the integrated volume source and the
    prescribed boundary/interface fluxes. The function evaluates and returns
    those compatibility residuals.

    Each connected component also has one arbitrary additive constant in
    ``phi``. A zero-mean constraint is introduced through a Lagrange multiplier
    per component. Gauge multipliers are numerical nullspace controls, not
    physical stress resultants.

    Axial distributed loading
    -------------------------
    This implementation requires ``dN_dz == 0``.

    A non-zero scalar ``dN_dz`` states only the change of the total axial
    resultant. It does not specify how the corresponding axial body load,
    surface load or transfer is distributed over the cross-section. Because
    different local distributions can produce the same resultant derivative,
    using ``dN_dz`` alone would make the local source underdetermined. The
    function therefore raises ``NotImplementedError`` rather than inventing a
    distribution.

    Optional Four-Quadrant validation
    ---------------------------------
    ``validation_points`` are diagnostic only. They are never used in assembly
    and cannot change the solution.

    At each validation point the solved triangle field is integrated on four
    half-chords to obtain

        H_L, H_R, V_B, V_T.

    These are compared with the independently differentiated Navier regional
    resultants using

        dN_pp/dz =  H_R + V_T
        dN_mp/dz =  H_L - V_T
        dN_mm/dz = -H_L - V_B
        dN_pm/dz = -H_R + V_B.

    The comparison is returned under ``validation`` and acts as an integral
    equilibrium check; no projection is performed to force agreement.

    Returned data
    -------------
    The result dictionary contains:

    - ``section``:
      station, actions, derivative convention and derivative-step metadata;
    - ``mesh``:
      Triangle PSLG controls, node/triangle counts and mesh tolerances;
    - ``resultants``:
      area-integrated ``Tx_recovered``, ``Ty_recovered`` and their differences
      from the prescribed ``Tx``, ``Ty``;
    - ``equilibrium``:
      source, boundary and interface integrals, global/component compatibility
      residuals, linear-system residual and gauge multipliers;
    - ``triangles``:
      one row per triangle with coordinates, polygon identity, area,
      ``shear_weightabs``, potential gradient and piecewise-constant
      ``tau_x, tau_y``;
    - ``validation``:
      optional Four-Quadrant half-chord comparisons.

    Interpretation and limits
    -------------------------
    This is a reduced sectional equilibrium closure, not a general
    three-dimensional elasticity solver. The recovered field is the
    complementary-energy-minimizing field within the adopted scalar-potential
    model.

    The implementation has been regression-tested so that existing Navier,
    Jourawski, centroid-axis and Four-Quadrant calculations are unchanged when
    this API is not called.

    NumPy, SciPy and Shapely >= 2.1 are imported lazily and are required only
    when this function is executed.
    """
    try:
        import numpy as np
        from scipy.sparse import bmat, csc_matrix, lil_matrix
        from scipy.sparse.linalg import spsolve
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential_triangle_mesh() requires NumPy "
            "and SciPy."
        ) from exc

    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)
    dN_dz = float(dN_dz)
    if max_triangle_area is not None:
        max_triangle_area = float(max_triangle_area)
    if min_angle is not None:
        min_angle = float(min_angle)
    plot_mesh = bool(plot_mesh)
    compatibility_rtol = float(compatibility_rtol)
    compatibility_atol = float(compatibility_atol)

    for name, value in {
        "z": z,
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
        "dN_dz": dN_dz,
        "compatibility_rtol": compatibility_rtol,
        "compatibility_atol": compatibility_atol,
    }.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    if abs(dN_dz) > max(_tol.EPS_A, 1.0e-14):
        raise NotImplementedError(
            "analyse_navier_local_shear_potential_triangle_mesh() currently requires "
            "dN_dz=0. A non-zero axial resultant gradient does not define "
            "its local load distribution."
        )

    if compatibility_rtol < 0.0 or compatibility_atol < 0.0:
        raise ValueError(
            "Compatibility tolerances must be non-negative."
        )

    if max_triangle_area is not None:
        if not math.isfinite(max_triangle_area) or max_triangle_area <= 0.0:
            raise ValueError(
                "max_triangle_area must be a positive finite value."
            )
    if min_angle is not None:
        if not math.isfinite(min_angle) or min_angle <= 0.0:
            raise ValueError("min_angle must be a positive finite value.")

    derivative_context = _potential_derivative_context(
        section_field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
        Tx=Tx,
        Ty=Ty,
        dz=dz,
    )

    regions, domain = _potential_occupied_regions(
        section_field,
        z,
    )

    mesh = _potential_triangle_direct_csf_mesh(
        section_field,
        z,
        regions,
        max_triangle_area=max_triangle_area,
        min_angle=min_angle,
    )

    nodes = mesh["nodes"]
    connectivity = mesh["triangles"]
    polygon_indices = mesh["polygon_indices"]
    shear_weights = mesh["shear_weights"]

    triangle_count = len(connectivity)
    node_count = len(nodes)

    if triangle_count == 0 or node_count == 0:
        raise RuntimeError("The potential mesh is empty.")

    if plot_mesh:
        _plot_potential_mesh_triangle(
            section_field=section_field,
            z=z,
            mesh=mesh,
        )

    stiffness = lil_matrix(
        (node_count, node_count),
        dtype=float,
    )
    rhs = np.zeros(node_count, dtype=float)

    triangle_area = np.zeros(triangle_count, dtype=float)
    triangle_gradients: list[object] = []
    triangle_centroids = np.zeros(
        (triangle_count, 2),
        dtype=float,
    )

    source_integral = 0.0

    # Three-point degree-2 quadrature. The derivative of the affine Navier field
    # is affine inside each polygon, so this exactly integrates source*N_i for
    # the present piecewise-affine source representation.
    barycentric_rule = (
        (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
        (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    )

    # Assemble the volume part of the weak problem triangle by triangle.
    #
    # For each P1 triangle:
    #   K_e = integral(G_like * grad(N)^T grad(N) dA)
    #
    # and the longitudinal-equilibrium source contributes
    #
    #   f_e = -integral(source * N dA)
    #
    # to the positive-stiffness form. The three-point rule exactly integrates
    # the present piecewise-affine source multiplied by the linear P1 basis.
    for triangle_idx, triangle in enumerate(connectivity):
        points = nodes[triangle]
        area, gradients = _potential_triangle_area_gradients(
            points
        )

        polygon_idx = int(polygon_indices[triangle_idx])
        g_like = float(shear_weights[triangle_idx])

        triangle_area[triangle_idx] = area
        triangle_gradients.append(gradients)
        triangle_centroids[triangle_idx, :] = np.mean(
            points,
            axis=0,
        )

        local_stiffness = (
            g_like
            * area
            * (gradients @ gradients.T)
        )

        for local_i in range(3):
            global_i = int(triangle[local_i])

            for local_j in range(3):
                global_j = int(triangle[local_j])
                stiffness[global_i, global_j] += float(
                    local_stiffness[
                        local_i,
                        local_j,
                    ]
                )

        local_source = np.zeros(3, dtype=float)

        for lambdas in barycentric_rule:
            lam = np.asarray(lambdas, dtype=float)
            point = lam @ points

            sigma_z = _potential_sigma_z_at_point(
                derivative_context,
                polygon_idx=polygon_idx,
                x=float(point[0]),
                y=float(point[1]),
            )
            source = -sigma_z
            quadrature_weight = area / 3.0

            source_integral += (
                quadrature_weight * source
            )
            local_source += (
                quadrature_weight * source * lam
            )

        # Positive stiffness represents -div(G grad(phi)).
        # Hence the weak volume contribution is -integral(source*N_i).
        for local_i in range(3):
            rhs[int(triangle[local_i])] -= float(
                local_source[local_i]
            )

    edges = _potential_mesh_edges(connectivity)

    # Verify that every one-sided mesh edge is truly on the boundary of the
    # active shear domain. This catches non-conforming material interfaces.
    min_x, min_y, max_x, max_y = map(
        float,
        domain.bounds,
    )
    geometry_scale = max(
        1.0,
        abs(min_x),
        abs(min_y),
        abs(max_x),
        abs(max_y),
        max_x - min_x,
        max_y - min_y,
    )
    geometry_tolerance = max(
        1.0e-10,
        1.0e-9 * geometry_scale,
    )

    boundary_flux_integral = 0.0
    interface_jump_integral = 0.0
    boundary_edge_count = 0
    interface_edge_count = 0

    base_state = derivative_context["base_state"]
    gauss_points = (
        -1.0 / math.sqrt(3.0),
        +1.0 / math.sqrt(3.0),
    )

    # Assemble geometric Neumann terms after the volume source so external
    # boundaries and material interfaces can be classified from mesh adjacency.
    #
    # A one-sided edge belongs to the boundary of the union of active shear
    # regions. A two-sided edge is internal; when its adjacent triangles carry
    # different polygon indices it is a material interface and may require the
    # moving-interface jump term.
    for edge, adjacent in edges.items():
        node_a, node_b = edge
        p0 = nodes[node_a]
        p1 = nodes[node_b]
        edge_vector = p1 - p0
        edge_length = float(np.linalg.norm(edge_vector))

        if edge_length <= _tol.EPS_L:
            raise ValueError(
                "The potential mesh contains a degenerate edge."
            )

        midpoint_x = 0.5 * float(p0[0] + p1[0])
        midpoint_y = 0.5 * float(p0[1] + p1[1])

        if len(adjacent) == 1:
            triangle_idx = int(adjacent[0])
            polygon_idx = int(
                polygon_indices[triangle_idx]
            )

            # A one-sided edge must lie on the boundary of the union of active
            # shear regions. Otherwise adjacent material meshes are non-conforming.
            try:
                from shapely.geometry import Point as ShapelyPoint
            except ImportError as exc:
                raise ImportError(
                    "analyse_navier_local_shear_potential_triangle_mesh() "
                    "requires Shapely."
                ) from exc

            if (
                domain.boundary.distance(
                    ShapelyPoint(midpoint_x, midpoint_y)
                )
                > geometry_tolerance
            ):
                raise RuntimeError(
                    "Non-conforming potential mesh detected on an "
                    "internal material boundary."
                )

            nx, ny = _potential_edge_normal_from_triangle(
                p0=p0,
                p1=p1,
                triangle_centroid=triangle_centroids[
                    triangle_idx
                ],
            )

            boundary_edge_count += 1

            for gauss_coordinate in gauss_points:
                s = 0.5 * (gauss_coordinate + 1.0)
                weight = 0.5 * edge_length

                point = (1.0 - s) * p0 + s * p1
                vx, vy = _potential_boundary_velocity_at_point(
                    derivative_context,
                    x=float(point[0]),
                    y=float(point[1]),
                    geometry_tolerance=geometry_tolerance,
                )
                normal_velocity = vx * nx + vy * ny

                sigma = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_idx
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )
                normal_flux = sigma * normal_velocity

                boundary_flux_integral += (
                    weight * normal_flux
                )
                rhs[node_a] += (
                    weight * normal_flux * (1.0 - s)
                )
                rhs[node_b] += (
                    weight * normal_flux * s
                )

        elif len(adjacent) == 2:
            triangle_i = int(adjacent[0])
            triangle_j = int(adjacent[1])
            polygon_i = int(polygon_indices[triangle_i])
            polygon_j = int(polygon_indices[triangle_j])

            if polygon_i == polygon_j:
                continue

            nx, ny = _potential_edge_normal_between_triangles(
                p0=p0,
                p1=p1,
                centroid_i=triangle_centroids[triangle_i],
                centroid_j=triangle_centroids[triangle_j],
            )

            interface_edge_count += 1

            for gauss_coordinate in gauss_points:
                s = 0.5 * (gauss_coordinate + 1.0)
                weight = 0.5 * edge_length
                point = (1.0 - s) * p0 + s * p1

                vx, vy = _potential_boundary_velocity_at_point(
                    derivative_context,
                    x=float(point[0]),
                    y=float(point[1]),
                    geometry_tolerance=geometry_tolerance,
                )
                normal_velocity = vx * nx + vy * ny

                sigma_i = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_i
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )
                sigma_j = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_j
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )

                jump_flux = (
                    (sigma_i - sigma_j)
                    * normal_velocity
                )

                interface_jump_integral += (
                    weight * jump_flux
                )
                rhs[node_a] += (
                    weight * jump_flux * (1.0 - s)
                )
                rhs[node_b] += (
                    weight * jump_flux * s
                )

    # Every connected shear component has an independent Neumann nullspace.
    # Determine connected components before solving. A pure-Neumann scalar
    # potential has one constant null mode per disconnected component, so one
    # independent gauge equation is required for each component.
    components = _potential_connected_components(
        node_count=node_count,
        connectivity=connectivity,
    )

    component_compatibility: list[dict[str, float | int]] = []
    maximum_component_residual = 0.0

    for component_idx, component_nodes in enumerate(components):
        residual = float(
            np.sum(rhs[np.asarray(component_nodes, dtype=int)])
        )
        scale = max(
            1.0,
            abs(source_integral),
            abs(boundary_flux_integral),
            abs(interface_jump_integral),
        )
        tolerance = (
            compatibility_atol
            + compatibility_rtol * scale
        )
        maximum_component_residual = max(
            maximum_component_residual,
            abs(residual),
        )

        component_compatibility.append(
            {
                "component": int(component_idx),
                "node_count": int(len(component_nodes)),
                "residual": residual,
                "tolerance": float(tolerance),
            }
        )

        if abs(residual) > tolerance:
            raise RuntimeError(
                "Local shear-potential Neumann compatibility failed "
                f"for connected component {component_idx}: "
                f"residual={residual}, tolerance={tolerance}."
            )

    # One zero-mean gauge per connected component.
    constraint = lil_matrix(
        (node_count, len(components)),
        dtype=float,
    )

    for component_idx, component_nodes in enumerate(components):
        for node_idx in component_nodes:
            constraint[int(node_idx), component_idx] = 1.0

    constraint_csc = constraint.tocsc()
    matrix_csc = stiffness.tocsc()
    zero_block = csc_matrix(
        (len(components), len(components)),
        dtype=float,
    )

    augmented = bmat(
        (
            (matrix_csc, constraint_csc),
            (constraint_csc.T, zero_block),
        ),
        format="csc",
    )
    augmented_rhs = np.concatenate(
        (
            rhs,
            np.zeros(len(components), dtype=float),
        )
    )

    # Solve the symmetric saddle-point system containing the physical
    # potential unknowns and the zero-mean gauge multipliers. Compatibility is
    # checked separately below; the gauge is never used as a hidden load
    # correction.
    solution = spsolve(
        augmented,
        augmented_rhs,
    )
    phi = np.asarray(
        solution[:node_count],
        dtype=float,
    )
    gauge_multipliers = np.asarray(
        solution[node_count:],
        dtype=float,
    )

    linear_residual = (
        augmented @ solution - augmented_rhs
    )
    linear_residual_inf = float(
        np.max(np.abs(linear_residual))
    )

    triangle_rows: list[dict[str, object]] = []
    Tx_recovered = 0.0
    Ty_recovered = 0.0

    for triangle_idx, triangle in enumerate(connectivity):
        gradients = triangle_gradients[triangle_idx]
        g_like = float(shear_weights[triangle_idx])
        gradient_phi = phi[triangle] @ gradients
        tau_x = float(g_like * gradient_phi[0])
        tau_y = float(g_like * gradient_phi[1])
        area = float(triangle_area[triangle_idx])
        points = nodes[triangle]
        centroid = triangle_centroids[triangle_idx]
        polygon_idx = int(polygon_indices[triangle_idx])

        Tx_recovered += area * tau_x
        Ty_recovered += area * tau_y

        triangle_rows.append(
            {
                "idx": int(triangle_idx),
                "polygon_idx": polygon_idx,
                "name": str(mesh["names"][triangle_idx]),
                "shear_weightabs": g_like,
                "area": area,
                "cx": float(centroid[0]),
                "cy": float(centroid[1]),
                "x0": float(points[0, 0]),
                "y0": float(points[0, 1]),
                "x1": float(points[1, 0]),
                "y1": float(points[1, 1]),
                "x2": float(points[2, 0]),
                "y2": float(points[2, 1]),
                "tau_x": tau_x,
                "tau_y": tau_y,
            }
        )

    validation_rows: list[dict[str, object]] = []

    if validation_points is not None:
        cut_tolerance = max(
            1.0e-12,
            1.0e-10 * geometry_scale,
        )

        for point_idx, point in enumerate(validation_points):
            if len(point) != 2:
                raise ValueError(
                    "Each validation point must be an (x, y) pair."
                )

            x_value = float(point[0])
            y_value = float(point[1])

            flows = _potential_partial_chord_flows(
                triangle_rows,
                x=x_value,
                y=y_value,
                tolerance=cut_tolerance,
            )

            fq = analyse_navier_four_quadrant_resultant_derivatives(
                section_field=section_field,
                z=z,
                N=N,
                Mx=Mx,
                My=My,
                Tx=Tx,
                Ty=Ty,
                x=x_value,
                y=y_value,
                dN_dz=0.0,
                dz=derivative_context["step"],
            )

            predicted = {
                "dN_pp_dz": flows["H_R"] + flows["V_T"],
                "dN_mp_dz": flows["H_L"] - flows["V_T"],
                "dN_mm_dz": -flows["H_L"] - flows["V_B"],
                "dN_pm_dz": -flows["H_R"] + flows["V_B"],
            }

            maximum_error = 0.0
            row: dict[str, object] = {
                "idx": int(point_idx),
                "x": x_value,
                "y": y_value,
                **flows,
            }

            for key, potential_value in predicted.items():
                api_value = float(fq[key])
                error = float(potential_value) - api_value
                maximum_error = max(
                    maximum_error,
                    abs(error),
                )

                row[f"{key}_potential"] = float(
                    potential_value
                )
                row[f"{key}_four_quadrant"] = api_value
                row[f"{key}_error"] = error

            row["dN_above_potential"] = float(
                flows["H_L"] + flows["H_R"]
            )
            row["dN_above_four_quadrant"] = float(
                fq["dN_above_dz"]
            )
            row["dN_right_potential"] = float(
                flows["V_B"] + flows["V_T"]
            )
            row["dN_right_four_quadrant"] = float(
                fq["dN_right_dz"]
            )
            row["max_quadrant_error"] = float(
                maximum_error
            )

            validation_rows.append(row)

    return {
        "section": {
            "z": z,
            "N": N,
            "Mx": Mx,
            "My": My,
            "Tx": Tx,
            "Ty": Ty,
            "dN_dz": 0.0,
        },
        "derivative": {
            "step": float(derivative_context["step"]),
            "scheme": str(derivative_context["scheme"]),
            "dz_mode": str(derivative_context["dz_mode"]),
        },
        "mesh": {
            "strategy": str(mesh["backend"]),
            "triangle_options": str(mesh["triangle_options"]),
            "max_triangle_area": mesh["max_triangle_area"],
            "min_angle": mesh["min_angle"],
            "pslg_vertex_count": int(mesh["pslg_vertex_count"]),
            "pslg_segment_count": int(mesh["pslg_segment_count"]),
            "normalized_duplicate_vertex_count": int(
                mesh["normalized_duplicate_vertex_count"]
            ),
            "pslg_hole_count": int(mesh["pslg_hole_count"]),
            "pslg_region_seed_count": int(mesh["pslg_region_seed_count"]),
            "triangle_total_count": int(mesh["triangle_total_count"]),
            "discarded_outside_triangle_count": int(
                mesh["discarded_outside_triangle_count"]
            ),
            "discarded_void_triangle_count": int(
                mesh["discarded_void_triangle_count"]
            ),
            "discarded_triangle_count": int(
                mesh["discarded_triangle_count"]
            ),
            "active_triangle_count": int(mesh["active_triangle_count"]),
            "domain_area": float(mesh["domain_area"]),
            "mesh_area": float(mesh["mesh_area"]),
            "node_count": int(node_count),
            "triangle_count": int(triangle_count),
            "connected_components": int(len(components)),
            "boundary_edge_count": int(boundary_edge_count),
            "interface_edge_count": int(interface_edge_count),
            "merge_tolerance": float(
                mesh["merge_tolerance"]
            ),
        },
        "resultants": {
            "Tx_recovered": float(Tx_recovered),
            "Ty_recovered": float(Ty_recovered),
            "Tx_error": float(Tx_recovered - Tx),
            "Ty_error": float(Ty_recovered - Ty),
        },
        "equilibrium": {
            "source_integral": float(source_integral),
            "external_boundary_flux_integral": float(
                boundary_flux_integral
            ),
            "interface_jump_integral": float(
                interface_jump_integral
            ),
            "global_compatibility_residual": float(
                np.sum(rhs)
            ),
            "max_component_compatibility_residual": float(
                maximum_component_residual
            ),
            "component_compatibility": component_compatibility,
            "linear_residual_inf": linear_residual_inf,
            "gauge_multipliers": tuple(
                float(value)
                for value in gauge_multipliers
            ),
        },
        "triangles": triangle_rows,
        "validation": validation_rows,
    }




def analyse_navier_local_shear_potential_controlled_mesh(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    *,
    dN_dz: float = 0.0,
    dz: float | None = None,
    num_sudx: int = 5,
    num_sudy: int = 5,
    plot_mesh: bool = False,
    validation_points: tuple[tuple[float, float], ...] | None = None,
    compatibility_rtol: float = 1.0e-8,
    compatibility_atol: float = 1.0e-6,
) -> dict[str, object]:
    """
    Recover a local in-plane shear field from complete Navier equilibrium.

    Mechanical definition
    ---------------------
    At the requested station the function first constructs the complete CSF
    Navier stress field ``sigma_zz(x, y, z)`` using the physical section
    geometry, polygon ``weightabs`` values and the supplied section actions.
    Its longitudinal derivative is then evaluated at fixed global coordinates.

    The local shear field is selected through the minimum-complementary-energy
    closure

        tau = G_like * grad(phi),

    with

        div(tau) = -partial(sigma_zz) / partial(z),

    or equivalently

        div(G_like * grad(phi))
            = -partial(sigma_zz) / partial(z).

    ``G_like`` is the sampled polygon ``shear_weightabs``. It is not derived
    from ``weightabs`` inside this routine and it is not replaced by a global
    effective shear modulus.

    This formulation is deliberately based on the derivative of the *complete*
    Navier field. Centroid motion, inertia variation, material participation
    variation and action gradients are therefore already contained in the
    source. They must not be added again as independent taper or centroid
    corrections.

    Action-gradient convention
    --------------------------
    The local neighbouring action states follow the CSF convention

        dMx/dz = Ty
        dMy/dz = Tx.

    ``N`` is currently held constant. Accordingly ``dN_dz`` is accepted only
    when it is zero; see "Axial distributed loading" below.

    Occupied-region topology
    ------------------------
    The transverse domain is built with the same index-based containment rule
    used by the Four-Quadrant routines:

        occupied(parent)
            = parent - union(direct children).

    This prevents double counting of nested material polygons. A region with
    negligible ``weightabs`` and negligible ``shear_weightabs`` acts as a true
    void and remains excluded from the active domain. A region carrying Navier
    stress but having no positive shear carrier is rejected because the
    elliptic closure would be locally degenerate.

    Moving external boundaries
    --------------------------
    CSF vertex correspondence defines an in-plane boundary velocity

        v = (dx/dz, dy/dz).

    On an external moving boundary the reduced traction condition is

        tau . n = sigma_zz * v_n,

    where ``n`` is the outward unit normal and ``v_n = v . n``. A fixed external
    boundary has ``v_n = 0`` and therefore carries zero prescribed normal shear
    traction in this reduced problem.

    Moving material interfaces
    --------------------------
    When two active regions share a moving interface, the weak jump condition is

        (tau_i - tau_j) . n
            = (sigma_zz_i - sigma_zz_j) * v_n.

    Thus a fixed interface reduces automatically to continuity of normal shear
    traction. The interface velocity is checked from both polygon descriptions;
    inconsistent CSF interface kinematics raise an error instead of being
    averaged silently.

    Finite-element representation
    -----------------------------
    Each occupied polygonal region is constrained-triangulated by Shapely.
    The initial mesh is then refined conformingly only where triangle-edge
    projections exceed the local geometry-driven comb spacing.

    ``num_sudx`` and ``num_sudy`` subdivide every interval between consecutive
    geometric teeth and therefore control the local target resolution.  There
    is no uniform 1->4 refinement level.

    The scalar potential uses conforming P1 triangles. Consequently
    ``grad(phi)`` and the returned ``tau_x, tau_y`` are piecewise constant by
    triangle.

    Mesh visualization
    ------------------
    When ``plot_mesh=True``, the final triangulation and the exact CSF polygon
    boundaries are displayed after mesh generation and before FEM assembly.
    The visualization is diagnostic only and does not modify the mesh, the
    assembled system or the returned solution. Matplotlib is required only
    when this option is enabled.

    Pure-Neumann compatibility and gauge
    ------------------------------------
    The local problem is Neumann-only. For every disconnected active component,
    solvability requires equality between the integrated volume source and the
    prescribed boundary/interface fluxes. The function evaluates and returns
    those compatibility residuals.

    Each connected component also has one arbitrary additive constant in
    ``phi``. A zero-mean constraint is introduced through a Lagrange multiplier
    per component. Gauge multipliers are numerical nullspace controls, not
    physical stress resultants.

    Axial distributed loading
    -------------------------
    This implementation requires ``dN_dz == 0``.

    A non-zero scalar ``dN_dz`` states only the change of the total axial
    resultant. It does not specify how the corresponding axial body load,
    surface load or transfer is distributed over the cross-section. Because
    different local distributions can produce the same resultant derivative,
    using ``dN_dz`` alone would make the local source underdetermined. The
    function therefore raises ``NotImplementedError`` rather than inventing a
    distribution.

    Optional Four-Quadrant validation
    ---------------------------------
    ``validation_points`` are diagnostic only. They are never used in assembly
    and cannot change the solution.

    At each validation point the solved triangle field is integrated on four
    half-chords to obtain

        H_L, H_R, V_B, V_T.

    These are compared with the independently differentiated Navier regional
    resultants using

        dN_pp/dz =  H_R + V_T
        dN_mp/dz =  H_L - V_T
        dN_mm/dz = -H_L - V_B
        dN_pm/dz = -H_R + V_B.

    The comparison is returned under ``validation`` and acts as an integral
    equilibrium check; no projection is performed to force agreement.

    Returned data
    -------------
    The result dictionary contains:

    - ``section``:
      station, actions, derivative convention and derivative-step metadata;
    - ``mesh``:
      node/triangle counts, refinement level and mesh tolerances;
    - ``resultants``:
      area-integrated ``Tx_recovered``, ``Ty_recovered`` and their differences
      from the prescribed ``Tx``, ``Ty``;
    - ``equilibrium``:
      source, boundary and interface integrals, global/component compatibility
      residuals, linear-system residual and gauge multipliers;
    - ``triangles``:
      one row per triangle with coordinates, polygon identity, area,
      ``shear_weightabs``, potential gradient and piecewise-constant
      ``tau_x, tau_y``;
    - ``validation``:
      optional Four-Quadrant half-chord comparisons.

    Interpretation and limits
    -------------------------
    This is a reduced sectional equilibrium closure, not a general
    three-dimensional elasticity solver. The recovered field is the
    complementary-energy-minimizing field within the adopted scalar-potential
    model.

    The implementation has been regression-tested so that existing Navier,
    Jourawski, centroid-axis and Four-Quadrant calculations are unchanged when
    this API is not called.

    NumPy, SciPy and Shapely >= 2.1 are imported lazily and are required only
    when this function is executed.
    """
    try:
        import numpy as np
        from scipy.sparse import bmat, csc_matrix, lil_matrix
        from scipy.sparse.linalg import spsolve
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential_controlled_mesh() requires NumPy "
            "and SciPy."
        ) from exc

    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)
    dN_dz = float(dN_dz)
    num_sudx = int(num_sudx)
    num_sudy = int(num_sudy)
    plot_mesh = bool(plot_mesh)
    compatibility_rtol = float(compatibility_rtol)
    compatibility_atol = float(compatibility_atol)

    for name, value in {
        "z": z,
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
        "dN_dz": dN_dz,
        "compatibility_rtol": compatibility_rtol,
        "compatibility_atol": compatibility_atol,
    }.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    if abs(dN_dz) > max(_tol.EPS_A, 1.0e-14):
        raise NotImplementedError(
            "analyse_navier_local_shear_potential_controlled_mesh() currently requires "
            "dN_dz=0. A non-zero axial resultant gradient does not define "
            "its local load distribution."
        )

    if compatibility_rtol < 0.0 or compatibility_atol < 0.0:
        raise ValueError(
            "Compatibility tolerances must be non-negative."
        )

    if num_sudx < 1:
        raise ValueError("num_sudx must be >= 1.")
    if num_sudy < 1:
        raise ValueError("num_sudy must be >= 1.")

    derivative_context = _potential_derivative_context(
        section_field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
        Tx=Tx,
        Ty=Ty,
        dz=dz,
    )

    regions, domain = _potential_occupied_regions(
        section_field,
        z,
    )

    initial_triangles = _potential_initial_triangles(regions)
    refined_triangles, refinement_info = (
        _potential_refine_triangles_comb_controlled(
            initial_triangles,
            section_field,
            z,
            num_sudx=num_sudx,
            num_sudy=num_sudy,
        )
    )
    mesh = _potential_merge_mesh(refined_triangles)

    nodes = mesh["nodes"]
    connectivity = mesh["triangles"]
    polygon_indices = mesh["polygon_indices"]
    shear_weights = mesh["shear_weights"]

    triangle_count = len(connectivity)
    node_count = len(nodes)

    if triangle_count == 0 or node_count == 0:
        raise RuntimeError("The potential mesh is empty.")

    if plot_mesh:
        _plot_potential_mesh_controlled(
            section_field=section_field,
            z=z,
            nodes=nodes,
            connectivity=connectivity,
            initial_triangle_count=len(initial_triangles),
            refinement_info=refinement_info,
        )

    stiffness = lil_matrix(
        (node_count, node_count),
        dtype=float,
    )
    rhs = np.zeros(node_count, dtype=float)

    triangle_area = np.zeros(triangle_count, dtype=float)
    triangle_gradients: list[object] = []
    triangle_centroids = np.zeros(
        (triangle_count, 2),
        dtype=float,
    )

    source_integral = 0.0

    # Three-point degree-2 quadrature. The derivative of the affine Navier field
    # is affine inside each polygon, so this exactly integrates source*N_i for
    # the present piecewise-affine source representation.
    barycentric_rule = (
        (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
        (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    )

    # Assemble the volume part of the weak problem triangle by triangle.
    #
    # For each P1 triangle:
    #   K_e = integral(G_like * grad(N)^T grad(N) dA)
    #
    # and the longitudinal-equilibrium source contributes
    #
    #   f_e = -integral(source * N dA)
    #
    # to the positive-stiffness form. The three-point rule exactly integrates
    # the present piecewise-affine source multiplied by the linear P1 basis.
    for triangle_idx, triangle in enumerate(connectivity):
        points = nodes[triangle]
        area, gradients = _potential_triangle_area_gradients(
            points
        )

        polygon_idx = int(polygon_indices[triangle_idx])
        g_like = float(shear_weights[triangle_idx])

        triangle_area[triangle_idx] = area
        triangle_gradients.append(gradients)
        triangle_centroids[triangle_idx, :] = np.mean(
            points,
            axis=0,
        )

        local_stiffness = (
            g_like
            * area
            * (gradients @ gradients.T)
        )

        for local_i in range(3):
            global_i = int(triangle[local_i])

            for local_j in range(3):
                global_j = int(triangle[local_j])
                stiffness[global_i, global_j] += float(
                    local_stiffness[
                        local_i,
                        local_j,
                    ]
                )

        local_source = np.zeros(3, dtype=float)

        for lambdas in barycentric_rule:
            lam = np.asarray(lambdas, dtype=float)
            point = lam @ points

            sigma_z = _potential_sigma_z_at_point(
                derivative_context,
                polygon_idx=polygon_idx,
                x=float(point[0]),
                y=float(point[1]),
            )
            source = -sigma_z
            quadrature_weight = area / 3.0

            source_integral += (
                quadrature_weight * source
            )
            local_source += (
                quadrature_weight * source * lam
            )

        # Positive stiffness represents -div(G grad(phi)).
        # Hence the weak volume contribution is -integral(source*N_i).
        for local_i in range(3):
            rhs[int(triangle[local_i])] -= float(
                local_source[local_i]
            )

    edges = _potential_mesh_edges(connectivity)

    # Verify that every one-sided mesh edge is truly on the boundary of the
    # active shear domain. This catches non-conforming material interfaces.
    min_x, min_y, max_x, max_y = map(
        float,
        domain.bounds,
    )
    geometry_scale = max(
        1.0,
        abs(min_x),
        abs(min_y),
        abs(max_x),
        abs(max_y),
        max_x - min_x,
        max_y - min_y,
    )
    geometry_tolerance = max(
        1.0e-10,
        1.0e-9 * geometry_scale,
    )

    boundary_flux_integral = 0.0
    interface_jump_integral = 0.0
    boundary_edge_count = 0
    interface_edge_count = 0

    base_state = derivative_context["base_state"]
    gauss_points = (
        -1.0 / math.sqrt(3.0),
        +1.0 / math.sqrt(3.0),
    )

    # Assemble geometric Neumann terms after the volume source so external
    # boundaries and material interfaces can be classified from mesh adjacency.
    #
    # A one-sided edge belongs to the boundary of the union of active shear
    # regions. A two-sided edge is internal; when its adjacent triangles carry
    # different polygon indices it is a material interface and may require the
    # moving-interface jump term.
    for edge, adjacent in edges.items():
        node_a, node_b = edge
        p0 = nodes[node_a]
        p1 = nodes[node_b]
        edge_vector = p1 - p0
        edge_length = float(np.linalg.norm(edge_vector))

        if edge_length <= _tol.EPS_L:
            raise ValueError(
                "The potential mesh contains a degenerate edge."
            )

        midpoint_x = 0.5 * float(p0[0] + p1[0])
        midpoint_y = 0.5 * float(p0[1] + p1[1])

        if len(adjacent) == 1:
            triangle_idx = int(adjacent[0])
            polygon_idx = int(
                polygon_indices[triangle_idx]
            )

            # A one-sided edge must lie on the boundary of the union of active
            # shear regions. Otherwise adjacent material meshes are non-conforming.
            try:
                from shapely.geometry import Point as ShapelyPoint
            except ImportError as exc:
                raise ImportError(
                    "analyse_navier_local_shear_potential_controlled_mesh() "
                    "requires Shapely."
                ) from exc

            if (
                domain.boundary.distance(
                    ShapelyPoint(midpoint_x, midpoint_y)
                )
                > geometry_tolerance
            ):
                raise RuntimeError(
                    "Non-conforming potential mesh detected on an "
                    "internal material boundary."
                )

            nx, ny = _potential_edge_normal_from_triangle(
                p0=p0,
                p1=p1,
                triangle_centroid=triangle_centroids[
                    triangle_idx
                ],
            )

            boundary_edge_count += 1

            for gauss_coordinate in gauss_points:
                s = 0.5 * (gauss_coordinate + 1.0)
                weight = 0.5 * edge_length

                point = (1.0 - s) * p0 + s * p1
                vx, vy = _potential_boundary_velocity_at_point(
                    derivative_context,
                    x=float(point[0]),
                    y=float(point[1]),
                    geometry_tolerance=geometry_tolerance,
                )
                normal_velocity = vx * nx + vy * ny

                sigma = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_idx
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )
                normal_flux = sigma * normal_velocity

                boundary_flux_integral += (
                    weight * normal_flux
                )
                rhs[node_a] += (
                    weight * normal_flux * (1.0 - s)
                )
                rhs[node_b] += (
                    weight * normal_flux * s
                )

        elif len(adjacent) == 2:
            triangle_i = int(adjacent[0])
            triangle_j = int(adjacent[1])
            polygon_i = int(polygon_indices[triangle_i])
            polygon_j = int(polygon_indices[triangle_j])

            if polygon_i == polygon_j:
                continue

            nx, ny = _potential_edge_normal_between_triangles(
                p0=p0,
                p1=p1,
                centroid_i=triangle_centroids[triangle_i],
                centroid_j=triangle_centroids[triangle_j],
            )

            interface_edge_count += 1

            for gauss_coordinate in gauss_points:
                s = 0.5 * (gauss_coordinate + 1.0)
                weight = 0.5 * edge_length
                point = (1.0 - s) * p0 + s * p1

                vx, vy = _potential_boundary_velocity_at_point(
                    derivative_context,
                    x=float(point[0]),
                    y=float(point[1]),
                    geometry_tolerance=geometry_tolerance,
                )
                normal_velocity = vx * nx + vy * ny

                sigma_i = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_i
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )
                sigma_j = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_j
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )

                jump_flux = (
                    (sigma_i - sigma_j)
                    * normal_velocity
                )

                interface_jump_integral += (
                    weight * jump_flux
                )
                rhs[node_a] += (
                    weight * jump_flux * (1.0 - s)
                )
                rhs[node_b] += (
                    weight * jump_flux * s
                )

    # Every connected shear component has an independent Neumann nullspace.
    # Determine connected components before solving. A pure-Neumann scalar
    # potential has one constant null mode per disconnected component, so one
    # independent gauge equation is required for each component.
    components = _potential_connected_components(
        node_count=node_count,
        connectivity=connectivity,
    )

    component_compatibility: list[dict[str, float | int]] = []
    maximum_component_residual = 0.0

    for component_idx, component_nodes in enumerate(components):
        residual = float(
            np.sum(rhs[np.asarray(component_nodes, dtype=int)])
        )
        scale = max(
            1.0,
            abs(source_integral),
            abs(boundary_flux_integral),
            abs(interface_jump_integral),
        )
        tolerance = (
            compatibility_atol
            + compatibility_rtol * scale
        )
        maximum_component_residual = max(
            maximum_component_residual,
            abs(residual),
        )

        component_compatibility.append(
            {
                "component": int(component_idx),
                "node_count": int(len(component_nodes)),
                "residual": residual,
                "tolerance": float(tolerance),
            }
        )

        if abs(residual) > tolerance:
            raise RuntimeError(
                "Local shear-potential Neumann compatibility failed "
                f"for connected component {component_idx}: "
                f"residual={residual}, tolerance={tolerance}."
            )

    # One zero-mean gauge per connected component.
    constraint = lil_matrix(
        (node_count, len(components)),
        dtype=float,
    )

    for component_idx, component_nodes in enumerate(components):
        for node_idx in component_nodes:
            constraint[int(node_idx), component_idx] = 1.0

    constraint_csc = constraint.tocsc()
    matrix_csc = stiffness.tocsc()
    zero_block = csc_matrix(
        (len(components), len(components)),
        dtype=float,
    )

    augmented = bmat(
        (
            (matrix_csc, constraint_csc),
            (constraint_csc.T, zero_block),
        ),
        format="csc",
    )
    augmented_rhs = np.concatenate(
        (
            rhs,
            np.zeros(len(components), dtype=float),
        )
    )

    # Solve the symmetric saddle-point system containing the physical
    # potential unknowns and the zero-mean gauge multipliers. Compatibility is
    # checked separately below; the gauge is never used as a hidden load
    # correction.
    solution = spsolve(
        augmented,
        augmented_rhs,
    )
    phi = np.asarray(
        solution[:node_count],
        dtype=float,
    )
    gauge_multipliers = np.asarray(
        solution[node_count:],
        dtype=float,
    )

    linear_residual = (
        augmented @ solution - augmented_rhs
    )
    linear_residual_inf = float(
        np.max(np.abs(linear_residual))
    )

    triangle_rows: list[dict[str, object]] = []
    Tx_recovered = 0.0
    Ty_recovered = 0.0

    for triangle_idx, triangle in enumerate(connectivity):
        gradients = triangle_gradients[triangle_idx]
        g_like = float(shear_weights[triangle_idx])
        gradient_phi = phi[triangle] @ gradients
        tau_x = float(g_like * gradient_phi[0])
        tau_y = float(g_like * gradient_phi[1])
        area = float(triangle_area[triangle_idx])
        points = nodes[triangle]
        centroid = triangle_centroids[triangle_idx]
        polygon_idx = int(polygon_indices[triangle_idx])

        Tx_recovered += area * tau_x
        Ty_recovered += area * tau_y

        triangle_rows.append(
            {
                "idx": int(triangle_idx),
                "polygon_idx": polygon_idx,
                "name": str(mesh["names"][triangle_idx]),
                "shear_weightabs": g_like,
                "area": area,
                "cx": float(centroid[0]),
                "cy": float(centroid[1]),
                "x0": float(points[0, 0]),
                "y0": float(points[0, 1]),
                "x1": float(points[1, 0]),
                "y1": float(points[1, 1]),
                "x2": float(points[2, 0]),
                "y2": float(points[2, 1]),
                "tau_x": tau_x,
                "tau_y": tau_y,
            }
        )

    validation_rows: list[dict[str, object]] = []

    if validation_points is not None:
        cut_tolerance = max(
            1.0e-12,
            1.0e-10 * geometry_scale,
        )

        for point_idx, point in enumerate(validation_points):
            if len(point) != 2:
                raise ValueError(
                    "Each validation point must be an (x, y) pair."
                )

            x_value = float(point[0])
            y_value = float(point[1])

            flows = _potential_partial_chord_flows(
                triangle_rows,
                x=x_value,
                y=y_value,
                tolerance=cut_tolerance,
            )

            fq = analyse_navier_four_quadrant_resultant_derivatives(
                section_field=section_field,
                z=z,
                N=N,
                Mx=Mx,
                My=My,
                Tx=Tx,
                Ty=Ty,
                x=x_value,
                y=y_value,
                dN_dz=0.0,
                dz=derivative_context["step"],
            )

            predicted = {
                "dN_pp_dz": flows["H_R"] + flows["V_T"],
                "dN_mp_dz": flows["H_L"] - flows["V_T"],
                "dN_mm_dz": -flows["H_L"] - flows["V_B"],
                "dN_pm_dz": -flows["H_R"] + flows["V_B"],
            }

            maximum_error = 0.0
            row: dict[str, object] = {
                "idx": int(point_idx),
                "x": x_value,
                "y": y_value,
                **flows,
            }

            for key, potential_value in predicted.items():
                api_value = float(fq[key])
                error = float(potential_value) - api_value
                maximum_error = max(
                    maximum_error,
                    abs(error),
                )

                row[f"{key}_potential"] = float(
                    potential_value
                )
                row[f"{key}_four_quadrant"] = api_value
                row[f"{key}_error"] = error

            row["dN_above_potential"] = float(
                flows["H_L"] + flows["H_R"]
            )
            row["dN_above_four_quadrant"] = float(
                fq["dN_above_dz"]
            )
            row["dN_right_potential"] = float(
                flows["V_B"] + flows["V_T"]
            )
            row["dN_right_four_quadrant"] = float(
                fq["dN_right_dz"]
            )
            row["max_quadrant_error"] = float(
                maximum_error
            )

            validation_rows.append(row)

    return {
        "section": {
            "z": z,
            "N": N,
            "Mx": Mx,
            "My": My,
            "Tx": Tx,
            "Ty": Ty,
            "dN_dz": 0.0,
        },
        "derivative": {
            "step": float(derivative_context["step"]),
            "scheme": str(derivative_context["scheme"]),
            "dz_mode": str(derivative_context["dz_mode"]),
        },
        "mesh": {
            "strategy": str(refinement_info["strategy"]),
            "initial_triangle_count": int(
                len(initial_triangles)
            ),
            "num_sudx": int(num_sudx),
            "num_sudy": int(num_sudy),
            "refinement_passes": int(refinement_info["passes"]),
            "refinement_history": refinement_info["history"],
            "x_teeth": int(refinement_info["x_teeth"]),
            "y_teeth": int(refinement_info["y_teeth"]),
            "x_comb_lines": int(refinement_info["x_comb_lines"]),
            "y_comb_lines": int(refinement_info["y_comb_lines"]),
            "node_count": int(node_count),
            "triangle_count": int(triangle_count),
            "connected_components": int(len(components)),
            "boundary_edge_count": int(boundary_edge_count),
            "interface_edge_count": int(interface_edge_count),
            "merge_tolerance": float(
                mesh["merge_tolerance"]
            ),
        },
        "resultants": {
            "Tx_recovered": float(Tx_recovered),
            "Ty_recovered": float(Ty_recovered),
            "Tx_error": float(Tx_recovered - Tx),
            "Ty_error": float(Ty_recovered - Ty),
        },
        "equilibrium": {
            "source_integral": float(source_integral),
            "external_boundary_flux_integral": float(
                boundary_flux_integral
            ),
            "interface_jump_integral": float(
                interface_jump_integral
            ),
            "global_compatibility_residual": float(
                np.sum(rhs)
            ),
            "max_component_compatibility_residual": float(
                maximum_component_residual
            ),
            "component_compatibility": component_compatibility,
            "linear_residual_inf": linear_residual_inf,
            "gauge_multipliers": tuple(
                float(value)
                for value in gauge_multipliers
            ),
        },
        "triangles": triangle_rows,
        "validation": validation_rows,
    }



def analyse_navier_local_shear_potential(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
    Tx: float,
    Ty: float,
    *,
    dN_dz: float = 0.0,
    dz: float | None = None,
    mesh_refinements: int = 4,
    plot_mesh: bool = False,
    validation_points: tuple[tuple[float, float], ...] | None = None,
    compatibility_rtol: float = 1.0e-8,
    compatibility_atol: float = 1.0e-6,
) -> dict[str, object]:
    """
    Recover a local in-plane shear field from complete Navier equilibrium.

    Mechanical definition
    ---------------------
    At the requested station the function first constructs the complete CSF
    Navier stress field ``sigma_zz(x, y, z)`` using the physical section
    geometry, polygon ``weightabs`` values and the supplied section actions.
    Its longitudinal derivative is then evaluated at fixed global coordinates.

    The local shear field is selected through the minimum-complementary-energy
    closure

        tau = G_like * grad(phi),

    with

        div(tau) = -partial(sigma_zz) / partial(z),

    or equivalently

        div(G_like * grad(phi))
            = -partial(sigma_zz) / partial(z).

    ``G_like`` is the sampled polygon ``shear_weightabs``. It is not derived
    from ``weightabs`` inside this routine and it is not replaced by a global
    effective shear modulus.

    This formulation is deliberately based on the derivative of the *complete*
    Navier field. Centroid motion, inertia variation, material participation
    variation and action gradients are therefore already contained in the
    source. They must not be added again as independent taper or centroid
    corrections.

    Action-gradient convention
    --------------------------
    The local neighbouring action states follow the CSF convention

        dMx/dz = Ty
        dMy/dz = Tx.

    ``N`` is currently held constant. Accordingly ``dN_dz`` is accepted only
    when it is zero; see "Axial distributed loading" below.

    Occupied-region topology
    ------------------------
    The transverse domain is built with the same index-based containment rule
    used by the Four-Quadrant routines:

        occupied(parent)
            = parent - union(direct children).

    This prevents double counting of nested material polygons. A region with
    negligible ``weightabs`` and negligible ``shear_weightabs`` acts as a true
    void and remains excluded from the active domain. A region carrying Navier
    stress but having no positive shear carrier is rejected because the
    elliptic closure would be locally degenerate.

    Moving external boundaries
    --------------------------
    CSF vertex correspondence defines an in-plane boundary velocity

        v = (dx/dz, dy/dz).

    On an external moving boundary the reduced traction condition is

        tau . n = sigma_zz * v_n,

    where ``n`` is the outward unit normal and ``v_n = v . n``. A fixed external
    boundary has ``v_n = 0`` and therefore carries zero prescribed normal shear
    traction in this reduced problem.

    Moving material interfaces
    --------------------------
    When two active regions share a moving interface, the weak jump condition is

        (tau_i - tau_j) . n
            = (sigma_zz_i - sigma_zz_j) * v_n.

    Thus a fixed interface reduces automatically to continuity of normal shear
    traction. The interface velocity is checked from both polygon descriptions;
    inconsistent CSF interface kinematics raise an error instead of being
    averaged silently.

    Finite-element representation
    -----------------------------
    Each occupied polygonal region is constrained-triangulated. Uniform
    refinement is then applied ``mesh_refinements`` times. The scalar potential
    uses conforming P1 triangles. Consequently ``grad(phi)`` and the returned
    ``tau_x, tau_y`` are piecewise constant by triangle.

    ``mesh_refinements`` controls only numerical resolution. It does not change
    the section model, the Navier source or the shear-participation field.

    Mesh visualization
    ------------------
    When ``plot_mesh=True``, the final triangulation and the exact CSF polygon
    boundaries are displayed after mesh generation and before FEM assembly.
    The visualization is diagnostic only and does not modify the mesh, the
    assembled system or the returned solution. Matplotlib is required only
    when this option is enabled.

    Pure-Neumann compatibility and gauge
    ------------------------------------
    The local problem is Neumann-only. For every disconnected active component,
    solvability requires equality between the integrated volume source and the
    prescribed boundary/interface fluxes. The function evaluates and returns
    those compatibility residuals.

    Each connected component also has one arbitrary additive constant in
    ``phi``. A zero-mean constraint is introduced through a Lagrange multiplier
    per component. Gauge multipliers are numerical nullspace controls, not
    physical stress resultants.

    Axial distributed loading
    -------------------------
    This implementation requires ``dN_dz == 0``.

    A non-zero scalar ``dN_dz`` states only the change of the total axial
    resultant. It does not specify how the corresponding axial body load,
    surface load or transfer is distributed over the cross-section. Because
    different local distributions can produce the same resultant derivative,
    using ``dN_dz`` alone would make the local source underdetermined. The
    function therefore raises ``NotImplementedError`` rather than inventing a
    distribution.

    Optional Four-Quadrant validation
    ---------------------------------
    ``validation_points`` are diagnostic only. They are never used in assembly
    and cannot change the solution.

    At each validation point the solved triangle field is integrated on four
    half-chords to obtain

        H_L, H_R, V_B, V_T.

    These are compared with the independently differentiated Navier regional
    resultants using

        dN_pp/dz =  H_R + V_T
        dN_mp/dz =  H_L - V_T
        dN_mm/dz = -H_L - V_B
        dN_pm/dz = -H_R + V_B.

    The comparison is returned under ``validation`` and acts as an integral
    equilibrium check; no projection is performed to force agreement.

    Returned data
    -------------
    The result dictionary contains:

    - ``section``:
      station, actions, derivative convention and derivative-step metadata;
    - ``mesh``:
      node/triangle counts, refinement level and mesh tolerances;
    - ``resultants``:
      area-integrated ``Tx_recovered``, ``Ty_recovered`` and their differences
      from the prescribed ``Tx``, ``Ty``;
    - ``equilibrium``:
      source, boundary and interface integrals, global/component compatibility
      residuals, linear-system residual and gauge multipliers;
    - ``triangles``:
      one row per triangle with coordinates, polygon identity, area,
      ``shear_weightabs``, potential gradient and piecewise-constant
      ``tau_x, tau_y``;
    - ``validation``:
      optional Four-Quadrant half-chord comparisons.

    Interpretation and limits
    -------------------------
    This is a reduced sectional equilibrium closure, not a general
    three-dimensional elasticity solver. The recovered field is the
    complementary-energy-minimizing field within the adopted scalar-potential
    model.

    The implementation has been regression-tested so that existing Navier,
    Jourawski, centroid-axis and Four-Quadrant calculations are unchanged when
    this API is not called.

    NumPy, SciPy and Shapely >= 2.1 are imported lazily and are required only
    when this function is executed.
    """
    try:
        import numpy as np
        from scipy.sparse import bmat, csc_matrix, lil_matrix
        from scipy.sparse.linalg import spsolve
    except ImportError as exc:
        raise ImportError(
            "analyse_navier_local_shear_potential() requires NumPy "
            "and SciPy."
        ) from exc

    z = float(z)
    N = float(N)
    Mx = float(Mx)
    My = float(My)
    Tx = float(Tx)
    Ty = float(Ty)
    dN_dz = float(dN_dz)
    mesh_refinements = int(mesh_refinements)
    plot_mesh = bool(plot_mesh)
    compatibility_rtol = float(compatibility_rtol)
    compatibility_atol = float(compatibility_atol)

    for name, value in {
        "z": z,
        "N": N,
        "Mx": Mx,
        "My": My,
        "Tx": Tx,
        "Ty": Ty,
        "dN_dz": dN_dz,
        "compatibility_rtol": compatibility_rtol,
        "compatibility_atol": compatibility_atol,
    }.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    if abs(dN_dz) > max(_tol.EPS_A, 1.0e-14):
        raise NotImplementedError(
            "analyse_navier_local_shear_potential() currently requires "
            "dN_dz=0. A non-zero axial resultant gradient does not define "
            "its local load distribution."
        )

    if compatibility_rtol < 0.0 or compatibility_atol < 0.0:
        raise ValueError(
            "Compatibility tolerances must be non-negative."
        )

    derivative_context = _potential_derivative_context(
        section_field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
        Tx=Tx,
        Ty=Ty,
        dz=dz,
    )

    regions, domain = _potential_occupied_regions(
        section_field,
        z,
    )

    initial_triangles = _potential_initial_triangles(regions)
    refined_triangles = _potential_refine_triangles(
        initial_triangles,
        mesh_refinements,
    )
    mesh = _potential_merge_mesh(refined_triangles)

    nodes = mesh["nodes"]
    connectivity = mesh["triangles"]
    polygon_indices = mesh["polygon_indices"]
    shear_weights = mesh["shear_weights"]

    triangle_count = len(connectivity)
    node_count = len(nodes)

    if triangle_count == 0 or node_count == 0:
        raise RuntimeError("The potential mesh is empty.")

    if plot_mesh:
        _plot_potential_mesh(
            section_field=section_field,
            z=z,
            nodes=nodes,
            connectivity=connectivity,
            initial_triangle_count=len(initial_triangles),
            mesh_refinements=mesh_refinements,
        )

    stiffness = lil_matrix(
        (node_count, node_count),
        dtype=float,
    )
    rhs = np.zeros(node_count, dtype=float)

    triangle_area = np.zeros(triangle_count, dtype=float)
    triangle_gradients: list[object] = []
    triangle_centroids = np.zeros(
        (triangle_count, 2),
        dtype=float,
    )

    source_integral = 0.0

    # Three-point degree-2 quadrature. The derivative of the affine Navier field
    # is affine inside each polygon, so this exactly integrates source*N_i for
    # the present piecewise-affine source representation.
    barycentric_rule = (
        (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
        (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    )

    # Assemble the volume part of the weak problem triangle by triangle.
    #
    # For each P1 triangle:
    #   K_e = integral(G_like * grad(N)^T grad(N) dA)
    #
    # and the longitudinal-equilibrium source contributes
    #
    #   f_e = -integral(source * N dA)
    #
    # to the positive-stiffness form. The three-point rule exactly integrates
    # the present piecewise-affine source multiplied by the linear P1 basis.
    for triangle_idx, triangle in enumerate(connectivity):
        points = nodes[triangle]
        area, gradients = _potential_triangle_area_gradients(
            points
        )

        polygon_idx = int(polygon_indices[triangle_idx])
        g_like = float(shear_weights[triangle_idx])

        triangle_area[triangle_idx] = area
        triangle_gradients.append(gradients)
        triangle_centroids[triangle_idx, :] = np.mean(
            points,
            axis=0,
        )

        local_stiffness = (
            g_like
            * area
            * (gradients @ gradients.T)
        )

        for local_i in range(3):
            global_i = int(triangle[local_i])

            for local_j in range(3):
                global_j = int(triangle[local_j])
                stiffness[global_i, global_j] += float(
                    local_stiffness[
                        local_i,
                        local_j,
                    ]
                )

        local_source = np.zeros(3, dtype=float)

        for lambdas in barycentric_rule:
            lam = np.asarray(lambdas, dtype=float)
            point = lam @ points

            sigma_z = _potential_sigma_z_at_point(
                derivative_context,
                polygon_idx=polygon_idx,
                x=float(point[0]),
                y=float(point[1]),
            )
            source = -sigma_z
            quadrature_weight = area / 3.0

            source_integral += (
                quadrature_weight * source
            )
            local_source += (
                quadrature_weight * source * lam
            )

        # Positive stiffness represents -div(G grad(phi)).
        # Hence the weak volume contribution is -integral(source*N_i).
        for local_i in range(3):
            rhs[int(triangle[local_i])] -= float(
                local_source[local_i]
            )

    edges = _potential_mesh_edges(connectivity)

    # Verify that every one-sided mesh edge is truly on the boundary of the
    # active shear domain. This catches non-conforming material interfaces.
    min_x, min_y, max_x, max_y = map(
        float,
        domain.bounds,
    )
    geometry_scale = max(
        1.0,
        abs(min_x),
        abs(min_y),
        abs(max_x),
        abs(max_y),
        max_x - min_x,
        max_y - min_y,
    )
    geometry_tolerance = max(
        1.0e-10,
        1.0e-9 * geometry_scale,
    )

    boundary_flux_integral = 0.0
    interface_jump_integral = 0.0
    boundary_edge_count = 0
    interface_edge_count = 0

    base_state = derivative_context["base_state"]
    gauss_points = (
        -1.0 / math.sqrt(3.0),
        +1.0 / math.sqrt(3.0),
    )

    # Assemble geometric Neumann terms after the volume source so external
    # boundaries and material interfaces can be classified from mesh adjacency.
    #
    # A one-sided edge belongs to the boundary of the union of active shear
    # regions. A two-sided edge is internal; when its adjacent triangles carry
    # different polygon indices it is a material interface and may require the
    # moving-interface jump term.
    for edge, adjacent in edges.items():
        node_a, node_b = edge
        p0 = nodes[node_a]
        p1 = nodes[node_b]
        edge_vector = p1 - p0
        edge_length = float(np.linalg.norm(edge_vector))

        if edge_length <= _tol.EPS_L:
            raise ValueError(
                "The potential mesh contains a degenerate edge."
            )

        midpoint_x = 0.5 * float(p0[0] + p1[0])
        midpoint_y = 0.5 * float(p0[1] + p1[1])

        if len(adjacent) == 1:
            triangle_idx = int(adjacent[0])
            polygon_idx = int(
                polygon_indices[triangle_idx]
            )

            # A one-sided edge must lie on the boundary of the union of active
            # shear regions. Otherwise adjacent material meshes are non-conforming.
            try:
                from shapely.geometry import Point as ShapelyPoint
            except ImportError as exc:
                raise ImportError(
                    "analyse_navier_local_shear_potential() "
                    "requires Shapely."
                ) from exc

            if (
                domain.boundary.distance(
                    ShapelyPoint(midpoint_x, midpoint_y)
                )
                > geometry_tolerance
            ):
                raise RuntimeError(
                    "Non-conforming potential mesh detected on an "
                    "internal material boundary."
                )

            nx, ny = _potential_edge_normal_from_triangle(
                p0=p0,
                p1=p1,
                triangle_centroid=triangle_centroids[
                    triangle_idx
                ],
            )

            boundary_edge_count += 1

            for gauss_coordinate in gauss_points:
                s = 0.5 * (gauss_coordinate + 1.0)
                weight = 0.5 * edge_length

                point = (1.0 - s) * p0 + s * p1
                vx, vy = _potential_boundary_velocity_at_point(
                    derivative_context,
                    x=float(point[0]),
                    y=float(point[1]),
                    geometry_tolerance=geometry_tolerance,
                )
                normal_velocity = vx * nx + vy * ny

                sigma = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_idx
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )
                normal_flux = sigma * normal_velocity

                boundary_flux_integral += (
                    weight * normal_flux
                )
                rhs[node_a] += (
                    weight * normal_flux * (1.0 - s)
                )
                rhs[node_b] += (
                    weight * normal_flux * s
                )

        elif len(adjacent) == 2:
            triangle_i = int(adjacent[0])
            triangle_j = int(adjacent[1])
            polygon_i = int(polygon_indices[triangle_i])
            polygon_j = int(polygon_indices[triangle_j])

            if polygon_i == polygon_j:
                continue

            nx, ny = _potential_edge_normal_between_triangles(
                p0=p0,
                p1=p1,
                centroid_i=triangle_centroids[triangle_i],
                centroid_j=triangle_centroids[triangle_j],
            )

            interface_edge_count += 1

            for gauss_coordinate in gauss_points:
                s = 0.5 * (gauss_coordinate + 1.0)
                weight = 0.5 * edge_length
                point = (1.0 - s) * p0 + s * p1

                vx, vy = _potential_boundary_velocity_at_point(
                    derivative_context,
                    x=float(point[0]),
                    y=float(point[1]),
                    geometry_tolerance=geometry_tolerance,
                )
                normal_velocity = vx * nx + vy * ny

                sigma_i = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_i
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )
                sigma_j = _navier_sigma_at_point(
                    poly=base_state["section"].polygons[
                        polygon_j
                    ],
                    x=float(point[0]),
                    y=float(point[1]),
                    state=base_state,
                )

                jump_flux = (
                    (sigma_i - sigma_j)
                    * normal_velocity
                )

                interface_jump_integral += (
                    weight * jump_flux
                )
                rhs[node_a] += (
                    weight * jump_flux * (1.0 - s)
                )
                rhs[node_b] += (
                    weight * jump_flux * s
                )

    # Every connected shear component has an independent Neumann nullspace.
    # Determine connected components before solving. A pure-Neumann scalar
    # potential has one constant null mode per disconnected component, so one
    # independent gauge equation is required for each component.
    components = _potential_connected_components(
        node_count=node_count,
        connectivity=connectivity,
    )

    component_compatibility: list[dict[str, float | int]] = []
    maximum_component_residual = 0.0

    for component_idx, component_nodes in enumerate(components):
        residual = float(
            np.sum(rhs[np.asarray(component_nodes, dtype=int)])
        )
        scale = max(
            1.0,
            abs(source_integral),
            abs(boundary_flux_integral),
            abs(interface_jump_integral),
        )
        tolerance = (
            compatibility_atol
            + compatibility_rtol * scale
        )
        maximum_component_residual = max(
            maximum_component_residual,
            abs(residual),
        )

        component_compatibility.append(
            {
                "component": int(component_idx),
                "node_count": int(len(component_nodes)),
                "residual": residual,
                "tolerance": float(tolerance),
            }
        )

        if abs(residual) > tolerance:
            raise RuntimeError(
                "Local shear-potential Neumann compatibility failed "
                f"for connected component {component_idx}: "
                f"residual={residual}, tolerance={tolerance}."
            )

    # One zero-mean gauge per connected component.
    constraint = lil_matrix(
        (node_count, len(components)),
        dtype=float,
    )

    for component_idx, component_nodes in enumerate(components):
        for node_idx in component_nodes:
            constraint[int(node_idx), component_idx] = 1.0

    constraint_csc = constraint.tocsc()
    matrix_csc = stiffness.tocsc()
    zero_block = csc_matrix(
        (len(components), len(components)),
        dtype=float,
    )

    augmented = bmat(
        (
            (matrix_csc, constraint_csc),
            (constraint_csc.T, zero_block),
        ),
        format="csc",
    )
    augmented_rhs = np.concatenate(
        (
            rhs,
            np.zeros(len(components), dtype=float),
        )
    )

    # Solve the symmetric saddle-point system containing the physical
    # potential unknowns and the zero-mean gauge multipliers. Compatibility is
    # checked separately below; the gauge is never used as a hidden load
    # correction.
    solution = spsolve(
        augmented,
        augmented_rhs,
    )
    phi = np.asarray(
        solution[:node_count],
        dtype=float,
    )
    gauge_multipliers = np.asarray(
        solution[node_count:],
        dtype=float,
    )

    linear_residual = (
        augmented @ solution - augmented_rhs
    )
    linear_residual_inf = float(
        np.max(np.abs(linear_residual))
    )

    triangle_rows: list[dict[str, object]] = []
    Tx_recovered = 0.0
    Ty_recovered = 0.0

    for triangle_idx, triangle in enumerate(connectivity):
        gradients = triangle_gradients[triangle_idx]
        g_like = float(shear_weights[triangle_idx])
        gradient_phi = phi[triangle] @ gradients
        tau_x = float(g_like * gradient_phi[0])
        tau_y = float(g_like * gradient_phi[1])
        area = float(triangle_area[triangle_idx])
        points = nodes[triangle]
        centroid = triangle_centroids[triangle_idx]
        polygon_idx = int(polygon_indices[triangle_idx])

        Tx_recovered += area * tau_x
        Ty_recovered += area * tau_y

        triangle_rows.append(
            {
                "idx": int(triangle_idx),
                "polygon_idx": polygon_idx,
                "name": str(mesh["names"][triangle_idx]),
                "shear_weightabs": g_like,
                "area": area,
                "cx": float(centroid[0]),
                "cy": float(centroid[1]),
                "x0": float(points[0, 0]),
                "y0": float(points[0, 1]),
                "x1": float(points[1, 0]),
                "y1": float(points[1, 1]),
                "x2": float(points[2, 0]),
                "y2": float(points[2, 1]),
                "tau_x": tau_x,
                "tau_y": tau_y,
            }
        )

    validation_rows: list[dict[str, object]] = []

    if validation_points is not None:
        cut_tolerance = max(
            1.0e-12,
            1.0e-10 * geometry_scale,
        )

        for point_idx, point in enumerate(validation_points):
            if len(point) != 2:
                raise ValueError(
                    "Each validation point must be an (x, y) pair."
                )

            x_value = float(point[0])
            y_value = float(point[1])

            flows = _potential_partial_chord_flows(
                triangle_rows,
                x=x_value,
                y=y_value,
                tolerance=cut_tolerance,
            )

            fq = analyse_navier_four_quadrant_resultant_derivatives(
                section_field=section_field,
                z=z,
                N=N,
                Mx=Mx,
                My=My,
                Tx=Tx,
                Ty=Ty,
                x=x_value,
                y=y_value,
                dN_dz=0.0,
                dz=derivative_context["step"],
            )

            predicted = {
                "dN_pp_dz": flows["H_R"] + flows["V_T"],
                "dN_mp_dz": flows["H_L"] - flows["V_T"],
                "dN_mm_dz": -flows["H_L"] - flows["V_B"],
                "dN_pm_dz": -flows["H_R"] + flows["V_B"],
            }

            maximum_error = 0.0
            row: dict[str, object] = {
                "idx": int(point_idx),
                "x": x_value,
                "y": y_value,
                **flows,
            }

            for key, potential_value in predicted.items():
                api_value = float(fq[key])
                error = float(potential_value) - api_value
                maximum_error = max(
                    maximum_error,
                    abs(error),
                )

                row[f"{key}_potential"] = float(
                    potential_value
                )
                row[f"{key}_four_quadrant"] = api_value
                row[f"{key}_error"] = error

            row["dN_above_potential"] = float(
                flows["H_L"] + flows["H_R"]
            )
            row["dN_above_four_quadrant"] = float(
                fq["dN_above_dz"]
            )
            row["dN_right_potential"] = float(
                flows["V_B"] + flows["V_T"]
            )
            row["dN_right_four_quadrant"] = float(
                fq["dN_right_dz"]
            )
            row["max_quadrant_error"] = float(
                maximum_error
            )

            validation_rows.append(row)

    return {
        "section": {
            "z": z,
            "N": N,
            "Mx": Mx,
            "My": My,
            "Tx": Tx,
            "Ty": Ty,
            "dN_dz": 0.0,
        },
        "derivative": {
            "step": float(derivative_context["step"]),
            "scheme": str(derivative_context["scheme"]),
            "dz_mode": str(derivative_context["dz_mode"]),
        },
        "mesh": {
            "initial_triangle_count": int(
                len(initial_triangles)
            ),
            "refinements": int(mesh_refinements),
            "node_count": int(node_count),
            "triangle_count": int(triangle_count),
            "connected_components": int(len(components)),
            "boundary_edge_count": int(boundary_edge_count),
            "interface_edge_count": int(interface_edge_count),
            "merge_tolerance": float(
                mesh["merge_tolerance"]
            ),
        },
        "resultants": {
            "Tx_recovered": float(Tx_recovered),
            "Ty_recovered": float(Ty_recovered),
            "Tx_error": float(Tx_recovered - Tx),
            "Ty_error": float(Ty_recovered - Ty),
        },
        "equilibrium": {
            "source_integral": float(source_integral),
            "external_boundary_flux_integral": float(
                boundary_flux_integral
            ),
            "interface_jump_integral": float(
                interface_jump_integral
            ),
            "global_compatibility_residual": float(
                np.sum(rhs)
            ),
            "max_component_compatibility_residual": float(
                maximum_component_residual
            ),
            "component_compatibility": component_compatibility,
            "linear_residual_inf": linear_residual_inf,
            "gauge_multipliers": tuple(
                float(value)
                for value in gauge_multipliers
            ),
        },
        "triangles": triangle_rows,
        "validation": validation_rows,
    }


def analyse_polygon_navier_stress(
    section_field,
    z: float,
    N: float,
    Mx: float,
    My: float,
) -> list[dict[str, object]]:
    """
    Compute polygon-wise signed normal stresses from the general Navier formula.

    For each polygon all vertices are checked.

    Returned stress values:
    - sigma_min      : minimum signed vertex stress in the polygon
    - sigma_max      : maximum signed vertex stress in the polygon
    - sigma_extreme  : signed vertex stress selected by largest absolute value

    The coordinates and vertex indices of all three governing values are returned.
    """
    state = _navier_section_state(
        section_field=section_field,
        z=z,
        N=N,
        Mx=Mx,
        My=My,
    )
    section = state["section"]

    rows: list[dict[str, object]] = []

    for i, poly in enumerate(section.polygons):
        name_s0 = str(section_field.s0.polygons[i].name)
        weightabs = float(poly.weightabs)

        vertex_rows: list[tuple[int, float, float, float]] = []

        for j, vertex in enumerate(poly.vertices):
            x = float(vertex.x)
            y = float(vertex.y)

            sigma = _navier_sigma_at_point(
                poly=poly,
                x=x,
                y=y,
                state=state,
            )

            vertex_rows.append((int(j), x, y, float(sigma)))

        if not vertex_rows:
            raise ValueError(f"Polygon {i} has no vertices at z={float(z)}.")

        j_min, x_min, y_min, sigma_min = min(vertex_rows, key=lambda r: r[3])
        j_max, x_max, y_max, sigma_max = max(vertex_rows, key=lambda r: r[3])
        j_ext, x_ext, y_ext, sigma_extreme = max(vertex_rows, key=lambda r: abs(r[3]))

        rows.append(
            {
                "idx": int(i),
                "name": name_s0,
                "weightabs": weightabs,

                "sigma_min": float(sigma_min),
                "vertex_index_min": int(j_min),
                "x_min": float(x_min),
                "y_min": float(y_min),

                "sigma_max": float(sigma_max),
                "vertex_index_max": int(j_max),
                "x_max": float(x_max),
                "y_max": float(y_max),

                "sigma_extreme": float(sigma_extreme),
                "vertex_index": int(j_ext),
                "x": float(x_ext),
                "y": float(y_ext),
            }
        )

    return rows

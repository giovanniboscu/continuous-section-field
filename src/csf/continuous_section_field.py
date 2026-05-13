from __future__ import annotations
import traceback
from typing import Dict, Any, Optional, List, Tuple, overload, Union, Literal
from dataclasses import dataclass
import math, random, warnings, os, sys, numbers, textwrap, re, io, dataclasses
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
import random as _random
from . import _tol


from .section_field import (
    Pt, Polygon, Section, CSFDumper, XY,
    _csf__is_finite_number, _csf__atomic_write_text, _csf__ensure_parent_dir_exists,
    _bbox_xy, _point_in_poly_inclusive, _point_on_segment_sq,
    polygon_has_self_intersections, polygon_inertia_about_origin,
    section_print_analysis, _signed_area_centroid_xy, _simple_yaml_dump, _csf__section_to_Sz_dict, CSFError,
)

from .section_field import section_full_analysis, evaluate_weight_formula, evaluate_weight_formula_zrelative, evaluate_shear_weight_formula

try:
    import yaml
except Exception:
    yaml = None
class ContinuousSectionField:
    class QuotedStr(str): pass

    CSFDumper.add_representer(
        QuotedStr,
        lambda d, s: d.represent_scalar('tag:yaml.org,2002:str', s, style="'")
    )
    
    def inspect_section_entities(self, z: float) -> List[Dict[str, Any]]:
        """
        Perform a sterile inspection of all polygon entities at longitudinal coordinate z.

        Structural rules:
        - topology is strictly index-based
        - names are labels only
        - no structural branch depends on polygon names or tags

        Returned fields:
        - idx (int)
        - name (str | None)
        - s0_name (str | None)
        - s1_name (str | None)
        - s0_weight (float)
        - s1_weight (float)
        - weight_at_z (float)
        - weight_abs_z (float)
        - weight_law (str | None)
        - area_signed (float)
        - is_container (bool)
        - direct_children (List[str | None])
        - container_idx (int | None)
        - container_name (str | None)

        Raises:
        - TypeError / ValueError only for structural issues
        """
        if not isinstance(z, (int, float)):
            raise TypeError(f"z must be a number, got {type(z).__name__}")

        sec = self.section(float(z))
        if sec is None:
            raise ValueError("self.section(z) returned None.")

        if not hasattr(sec, "polygons"):
            raise ValueError("Section object has no 'polygons' attribute.")

        polygons = sec.polygons

        s0_polygons = self.s0.polygons
        s1_polygons = self.s1.polygons

        children_map = self.build_direct_children_map(float(z))

        if not isinstance(children_map, dict):
            raise TypeError("build_direct_children_map(z) must return a dict.")

        parent_of: Dict[int, int] = {}


        for parent_idx, child_idx_list in children_map.items():
            for child_idx in child_idx_list:
                if child_idx in parent_of:
                    raise ValueError(
                        f"Polygon idx={child_idx} has multiple parents: "
                        f"{parent_of[child_idx]} and {parent_idx}"
                    )
                parent_of[child_idx] = parent_idx

        records: List[Dict[str, Any]] = []

        for idx, poly in enumerate(polygons):
            if not hasattr(poly, "weight"):
                raise ValueError(f"Polygon idx={idx} has no 'weight' attribute.")

            weight_at_z = float(poly.weight)
            weight_abs_z = float(poly.weightabs)

            shear_weight_at_z = float(poly.shear_weight) 
            shear_weight_abs_at_z = float(poly.shear_weightabs) 
            poisson = float(poly.poisson) 
            

            s0_poly = s0_polygons[idx]
            s1_poly = s1_polygons[idx]

            if not hasattr(s0_poly, "weight"):
                raise ValueError(f"S0 polygon idx={idx} has no 'weight' attribute.")
            if not hasattr(s1_poly, "weight"):
                raise ValueError(f"S1 polygon idx={idx} has no 'weight' attribute.")

            s0_weight = float(s0_poly.weight)
            s1_weight = float(s1_poly.weight)

            weight_law = None
            if self.weight_laws is not None:
                if (idx + 1) in self.weight_laws:
                    weight_law = str(self.weight_laws[idx + 1])

            area_signed, _ = _polygon_signed_area_and_centroid(poly)

            if idx in children_map:
                direct_children_idx = list(children_map[idx])
            else:
                direct_children_idx = []

            direct_children_labels: List[Optional[str]] = []
            for child_idx in direct_children_idx:
                child_poly = polygons[child_idx]
                if hasattr(child_poly, "name"):
                    direct_children_labels.append(child_poly.name)
                else:
                    direct_children_labels.append(None)

            if idx in parent_of:
                container_idx = parent_of[idx]
                container_poly = polygons[container_idx]
                if hasattr(container_poly, "name"):
                    container_name = container_poly.name
                else:
                    container_name = None
            else:
                container_idx = None
                container_name = None

            if hasattr(poly, "name"):
                name = poly.name
            else:
                name = None

            if hasattr(s0_poly, "name"):
                s0_name = s0_poly.name
            else:
                s0_name = None

            if hasattr(s1_poly, "name"):
                s1_name = s1_poly.name
            else:
                s1_name = None
            
            records.append(
                {
                    "idx": idx,
                    "name": name,
                    "s0_name": s0_name,
                    "s1_name": s1_name,
                    "s0_weight": s0_weight,
                    "s1_weight": s1_weight,
                    "weight_at_z": weight_at_z, 
                    "weight_abs_z": weight_abs_z,     
                    "shear_weight_at_z":shear_weight_at_z,
                    "shear_weight_abs_at_z":shear_weight_abs_at_z,
                    "poisson":poisson,
                    "weight_law": weight_law,
                    "area_signed": area_signed,
                    "is_container": len(direct_children_idx) > 0,
                    "direct_children": direct_children_labels,
                    "container_idx": container_idx,
                    "container_name": container_name,
                }
            )
        return records

    #---------------------------------------------------------------------------------------------------

    
    def build_direct_children_map(self, z: float) -> Dict[int, List[int]]:
        """
        Build the direct parent-to-children mapping for polygons at coordinate z.

        Structural rules:
        - polygon identity is strictly the polygon index in self.s0.polygons
        - names are never used
        - topology is expressed strictly as indices

        Output:
        - Dict[parent_idx, List[child_idx]]

        Notes:
        - The section at z is evaluated only to validate that z is admissible.
        - The containment topology is taken from the stable S0 polygon ordering.
        - Only direct children are returned.
        - Polygons with no children do not appear as keys.

        Raises:
        - TypeError if z is not numeric or if self.s0.polygons is not a valid sequence
        - ValueError for invalid topology or invalid container indices
        """
        if not isinstance(z, (int, float)):
            raise TypeError(f"z must be a number, got {type(z).__name__}")

        sec = self.section(float(z))
        if sec is None:
            raise ValueError("self.section(z) returned None.")

        if not hasattr(self.s0, "polygons"):
            raise ValueError("self.s0 has no 'polygons' attribute.")

        s0_polys = self.s0.polygons

        children_map: Dict[int, List[int]] = {}
        parent_of: Dict[int, int] = {}

        for child_idx, poly in enumerate(s0_polys):
            parent_idx = self.get_container_polygon_index(poly, child_idx)
            if parent_idx is None:
                continue

            if not isinstance(parent_idx, int):
                raise TypeError(
                    f"Container index for polygon idx={child_idx} must be int or None, "
                    f"got {type(parent_idx).__name__}"
                )

            if not (0 <= parent_idx < len(s0_polys)):
                raise ValueError(
                    f"Invalid container index {parent_idx} for polygon idx={child_idx}"
                )

            if parent_idx == child_idx:
                raise ValueError(
                    f"Polygon idx={child_idx} cannot be the container of itself."
                )

            if child_idx in parent_of:
                raise ValueError(
                    f"Polygon idx={child_idx} has multiple direct containers: "
                    f"{parent_of[child_idx]} and {parent_idx}"
                )

            parent_of[child_idx] = parent_idx

            if parent_idx not in children_map:
                children_map[parent_idx] = []

            children_map[parent_idx].append(child_idx)

        return children_map


    def get_container_polygon_index(self, poly: "Polygon", i: int):
        """
        Return the index (0-based) of the immediate container of `poly` in self.s0.polygons.

        Cached by polygon index because topology is assumed fixed.
        """
        if not hasattr(self, "_container_polygon_index_cache"):
            self._container_polygon_index_cache = {}

        if i in self._container_polygon_index_cache:

            return self._container_polygon_index_cache[i]

        result = self._get_container_polygon_index_uncached(poly, i)
        self._container_polygon_index_cache[i] = result
        return result

    def _get_container_polygon_index_uncached(self, poly: "Polygon", i: int):
        """
        Return the index (0-based) of the *immediate container* of `poly` in self.s0.polygons.
        Returns the index of the immediate container polygon (smallest-area polygon that contains `poly`),
        not the outermost/global container.
        Logic (as requested):
        1) Take polygon p (= poly).
        2) Collect all other polygons that contain p.
        3) Pick pp such that pp contains p and there is no other polygon between them
            (i.e., no q with p ⊂ q ⊂ pp). Polygons may touch (boundary counts as inside).

        Debug:
        - Enable with: self.debug_container = True
        - No global variables are used to activate debug output.

        Returns
        -------
        int | None
            Index of the immediate container polygon, or None if no container exists.
        """
        debug = bool(getattr(self, "debug_container", False))

        def _get_coincident_previous_polygon_index(i: int):
            """
            Return the index of a polygon coincident with polygon i, considering
            only previous polygons (idx < i).

            If no previous coincident polygon exists, return None.

            Coincidence is geometric boundary coincidence, even if the two polygons
            have different numbers of vertices.
            """
            polys = self.s0.polygons
            eps_l = float(getattr(self, "eps_l", _tol.EPS_L))

            def _strip_closure(verts):
                # Drop duplicated closing vertex if present.
                if len(verts) >= 2 and verts[0] == verts[-1]:
                    return verts[:-1]
                return verts

            def _point_on_segment(px, py, ax, ay, bx, by) -> bool:
                # Robust point-on-segment test with degenerate segment handling.
                abx, aby = (bx - ax), (by - ay)
                apx, apy = (px - ax), (py - ay)
                ab2 = abx * abx + aby * aby

                if ab2 <= eps_l * eps_l:
                    dx = px - ax
                    dy = py - ay
                    return (dx * dx + dy * dy) <= eps_l * eps_l

                cross = abx * apy - aby * apx
                if abs(cross) > eps_l:
                    return False

                dot = apx * abx + apy * aby
                if dot < -eps_l:
                    return False
                if dot > ab2 + eps_l:
                    return False

                return True

            def _point_on_polygon_boundary(pt, verts) -> bool:
                # Return True if pt lies on any polygon edge.
                n = len(verts)
                for k in range(n):
                    a = verts[k]
                    b = verts[(k + 1) % n]
                    if _point_on_segment(pt.x, pt.y, a.x, a.y, b.x, b.y):
                        return True
                return False

            def _poly_coincident_general(verts_a, verts_b) -> bool:
                """
                Return True if two polygons represent the same boundary, even if
                they have different numbers of vertices.
                """
                va = _strip_closure(verts_a)
                vb = _strip_closure(verts_b)

                if len(va) < 3 or len(vb) < 3:
                    return False

                for p in va:
                    if not _point_on_polygon_boundary(p, vb):
                        return False

                for p in vb:
                    if not _point_on_polygon_boundary(p, va):
                        return False

                return True

            if not (0 <= i < len(polys)):
                return None

            verts_i = _strip_closure(polys[i].vertices)
            if len(verts_i) < 3:
                return None

            # Search only previous polygons.
            for j in range(i - 1, -1, -1):
                verts_j = _strip_closure(polys[j].vertices)
                if len(verts_j) < 3:
                    continue
                if _poly_coincident_general(verts_i, verts_j):
                    return j
            return None

        def _dbg(msg: str) -> None:
            if debug:
                print(msg)

        coincident_prev_idx = _get_coincident_previous_polygon_index(i)
        if coincident_prev_idx is not None:
            return coincident_prev_idx


        polys = self.s0.polygons
        n_polys = len(polys)

        # Find the index of the same polygon in self.s0.polygons robustly.
        # We only trust 'i' if it points to the same name; otherwise we search by name.
        self_idx = None
        poly_name = getattr(poly, "name", None)
        '''
        if 0 <= i < n_polys and getattr(polys[i], "name", None) == poly_name:
            self_idx = i
        else:
            if poly_name is not None:
                for k, p in enumerate(polys):
                    if getattr(p, "name", None) == poly_name:
                        self_idx = k
                        break
            _dbg(f"[get_container_polygon_index] index mismatch: given i={i}, inferred self_idx={self_idx}, name={poly_name!r}")
        '''
        # Linear tolerance (allow per-instance override, fallback to module default)
        eps_l = float(getattr(self, "eps_l", _tol.EPS_L))
        eps_a = eps_l * eps_l  # area-like tolerance derived from eps_l

        def _strip_closure(verts):
            # If polygon is explicitly closed (last == first), drop last vertex.
            if len(verts) >= 2 and verts[0] == verts[-1]:
                return verts[:-1]
            return verts

        def _area_abs(verts) -> float:
            # Shoelace area magnitude.
            a2 = 0.0
            n = len(verts)
            for k in range(n):
                x0, y0 = verts[k].x, verts[k].y
                x1, y1 = verts[(k + 1) % n].x, verts[(k + 1) % n].y
                a2 += (x0 * y1 - x1 * y0)
            return abs(0.5 * a2)

        def _bbox(verts):
            xs = [v.x for v in verts]
            ys = [v.y for v in verts]
            return (min(xs), min(ys), max(xs), max(ys))

        def _bbox_contains(b_out, b_in) -> bool:
            # Inclusive bbox containment with tolerance.
            ox0, oy0, ox1, oy1 = b_out
            ix0, iy0, ix1, iy1 = b_in
            return (ox0 <= ix0 + eps_l and oy0 <= iy0 + eps_l and
                    ox1 >= ix1 - eps_l and oy1 >= iy1 - eps_l)

        def _point_on_segment(px, py, ax, ay, bx, by) -> bool:
            # Robust "point on segment" with degenerate segment handling.
            abx, aby = (bx - ax), (by - ay)
            apx, apy = (px - ax), (py - ay)
            ab2 = abx * abx + aby * aby

            # Degenerate edge -> treat as a point.
            if ab2 <= eps_l * eps_l:
                dx = px - ax
                dy = py - ay
                return (dx * dx + dy * dy) <= eps_l * eps_l

            # Collinearity via cross product.
            cross = abx * apy - aby * apx
            if abs(cross) > eps_l:
                return False

            # Projection check.
            dot = apx * abx + apy * aby
            if dot < -eps_l:
                return False
            if dot > ab2 + eps_l:
                return False
            return True

        def _point_in_poly(px, py, verts) -> bool:
            # Ray casting with boundary inclusion.
            inside = False
            n = len(verts)
            for k in range(n):
                x1, y1 = verts[k].x, verts[k].y
                x2, y2 = verts[(k + 1) % n].x, verts[(k + 1) % n].y

                # On-edge => inside.
                if _point_on_segment(px, py, x1, y1, x2, y2):
                    return True

                # Ray casting toggle.
                if (y1 > py) != (y2 > py):
                    x_int = x1 + (py - y1) * (x2 - x1) / (y2 - y1 + 0.0)
                    if x_int > px:
                        inside = not inside
            return inside

        def _poly_inside(inner_verts, outer_verts) -> bool:
            # Containment: all inner vertices must be inside or on boundary.
            return all(_point_in_poly(v.x, v.y, outer_verts) for v in inner_verts)

        inner_verts = _strip_closure(poly.vertices)
        if len(inner_verts) < 3:
            _dbg("[get_container_polygon_index] inner polygon degenerate (<3 vertices) -> None")
            return None

        a_inner = _area_abs(inner_verts)
        b_inner = _bbox(inner_verts)

        _dbg(f"[get_container_polygon_index] target={poly_name!r} a_inner={a_inner:.16g} bbox={b_inner}")

        # 1) Collect all container candidates of p.
        candidates = []  # list of tuples: (j, a_outer, outer_verts)
        for j, outer in enumerate(polys):
            if self_idx is not None and j == self_idx:
                continue
            if getattr(outer, "name", None) == poly_name:
                continue

            outer_verts = _strip_closure(outer.vertices)
            if len(outer_verts) < 3:
                continue

            # Fast bbox reject.
            if not _bbox_contains(_bbox(outer_verts), b_inner):
                continue

            a_outer = _area_abs(outer_verts)

            # Must be strictly larger (with tolerance).
            if a_outer <= a_inner + eps_a:
                continue

            if _poly_inside(inner_verts, outer_verts):
                candidates.append((j, a_outer, outer_verts))
                _dbg(f"  candidate j={j} name={getattr(outer,'name',None)!r} a_outer={a_outer:.16g}")

        if not candidates:
            _dbg("[get_container_polygon_index] no containers found -> None")
            return None

        # 2) Choose the immediate container:
        #    pp is a container of p such that there is no other container q with p ⊂ q ⊂ pp.
        immediate = []
        for j, a_j, v_j in candidates:
            has_between = False
            for k, a_k, v_k in candidates:
                if k == j:
                    continue
                # q is "between" if it is inside pp and is smaller than pp.
                # Under non-intersection assumptions, this captures nesting.
                if a_k < a_j - eps_a and _poly_inside(v_k, v_j):
                    has_between = True
                    _dbg(f"    reject j={j} because k={k} is between (k inside j)")
                    break
            if not has_between:
                immediate.append((j, a_j))

        if not immediate:
            # This should not happen under the stated assumptions; fall back to smallest-area container.
            best_idx = min(candidates, key=lambda t: t[1])[0]
            _dbg(f"[get_container_polygon_index] no immediate candidate (unexpected). Fallback best_idx={best_idx}")
            return best_idx

        # If multiple immediate candidates exist (should be rare), pick the smallest-area one.
        best_idx, best_area = min(immediate, key=lambda t: t[1])
        _dbg(f"[get_container_polygon_index] result best_idx={best_idx} name={getattr(polys[best_idx],'name',None)!r} a={best_area:.16g}")
        
        #print(f"DEBUG get_container_polygon_index {i} {best_idx}")
        return best_idx


    def write_section(self, z0: float, z1: float, yaml_path: str) -> None:

        def _strip_model_suffix(name: object) -> str:
            s = str(name).strip()
            at = s.find("@")
            if at == -1:
                return s
            return s[:at].strip()

        # Validate z0 e z1
        z_min, z_max = min(self.s0.z, self.s1.z), max(self.s0.z, self.s1.z)
        if not (z_min <= z0 <= z_max and z_min <= z1 <= z_max):
            bad_zs = [z for z in (z0, z1) if not (z_min <= z <= z_max)]
            raise CSFError(f"write_section: z0/z1 must be in [{z_min}, {z_max}]. Out: {bad_zs!r}")

        if not all(_csf__is_finite_number(z) for z in (z0, z1)):
            bad_zs = [z for z in (z0, z1) if not _csf__is_finite_number(z)]
            raise CSFError(f"write_section: z must be finite number. Got: {bad_zs!r}")

        yaml_path = yaml_path.strip()
        _csf__ensure_parent_dir_exists(yaml_path)

        secz0 = self.section(float(z0))
        secz1 = self.section(float(z1))

        # --- weight_laws trace only ---
        weight_laws_yaml = []
        if self.weight_laws:
            try:
                for key in self.weight_laws:
                    idx = key - 1
                    namestartlaw = _strip_model_suffix(self.s0.polygons[idx].name)
                    nameendlaw = _strip_model_suffix(self.s1.polygons[idx].name)
                    weight_laws_yaml.append(f"{namestartlaw},{nameendlaw}: {self.weight_laws[key]}")
            except CSFError:
                raise
            except Exception as e:
                raise CSFError(
                    "write_section: weight_laws failed. "
                    f"z={float(z0):.6g}, error={type(e).__name__}: {e}"
                ) from e

        # --- shear_weight_laws trace only ---
        shear_weight_laws_yaml = []

        if self.shear_weight_laws_default is not None:
            shear_weight_laws_yaml.append(str(self.shear_weight_laws_default))

        if self.shear_weight_laws:
            try:
                for key in self.shear_weight_laws:
                    idx = key
                    namestartlaw = _strip_model_suffix(self.s0.polygons[idx].name)
                    nameendlaw = _strip_model_suffix(self.s1.polygons[idx].name)
                    shear_weight_laws_yaml.append(f"{namestartlaw},{nameendlaw}: {self.shear_weight_laws[key]}")
            except CSFError:
                raise
            except Exception as e:
                raise CSFError(
                    "write_section: shear_weight_laws failed. "
                    f"z={float(z0):.6g}, error={type(e).__name__}: {e}"
                ) from e

        # --- build dict ---
        try:
            datas0 = _csf__section_to_Sz_dict(secz0, "S0")
            datas1 = _csf__section_to_Sz_dict(secz1, "S1")
        except CSFError:
            raise
        except Exception as e:
            raise CSFError(
                "write_section: failed converting Section -> Sz dict. "
                f"z={float(z1):.6g}, error={type(e).__name__}: {e}"
            ) from e

        new_data = {
            "CSF": {
                "sections": {
                    **datas0,
                    **datas1,
                }
            }
        }

        # IMPORTANT:
        # Do not serialize active weight_laws/shear_weight_laws here.
        # self.section(z) has already materialized their effect into the section weights.

        # --- serialize ---
        try:
            if "yaml" in globals() and globals().get("yaml") is not None:
                dumper = globals().get("CSFDumper", None)
                if dumper is None:
                    yml = globals()["yaml"].safe_dump(new_data, sort_keys=False)
                else:
                    yml = globals()["yaml"].dump(
                        new_data,
                        Dumper=dumper,
                        sort_keys=False,
                        allow_unicode=True,
                        indent=2,
                        default_flow_style=False,
                    )
            else:
                if "_simple_yaml_dump" not in globals() or globals().get("_simple_yaml_dump") is None:
                    raise CSFError(
                        "write_section: YAML backend unavailable."
                    )
                yml = globals()["_simple_yaml_dump"](new_data) + "\n"
        except CSFError:
            raise
        except Exception as e:
            raise CSFError(
                "write_section: YAML serialization failed. "
                f"z={float(z0):.6g}, error={type(e).__name__}: {e}"
            ) from e

        # --- append applied laws as comments only ---
        applied_laws_comments = []

        if weight_laws_yaml or shear_weight_laws_yaml:
            applied_laws_comments.append("")
            applied_laws_comments.append("# APPLIED_LAWS_TRACE:")
            applied_laws_comments.append("# Re-applying them may change the result, especially for laws using w0/w1.")
            applied_laws_comments.append("# They are kept for traceability only and must not be parsed/applied again.")

        if weight_laws_yaml:
            applied_laws_comments.append("# weight_laws:")
            for law in weight_laws_yaml:
                applied_laws_comments.append(f"#   - {law!r}")

        if shear_weight_laws_yaml:
            applied_laws_comments.append("# shear_weight_laws:")
            for law in shear_weight_laws_yaml:
                applied_laws_comments.append(f"#   - {law!r}")

        if applied_laws_comments:
            yml = yml.rstrip() + "\n" + "\n".join(applied_laws_comments) + "\n"

        # --- write ---
        try:
            _csf__atomic_write_text(yaml_path, yml)
        except Exception as e:
            raise CSFError(
                f"write_section: could not write YAML file '{yaml_path}'. "
                f"error={type(e).__name__}: {e}"
            ) from e


    # write_section

    @staticmethod
    def _section_to_dict(sec):
        poly_map = {}
        poly_names = [name for name, obj in globals().items() if isinstance(obj, Polygon)]
        for p in sec.polygons:
            key = p.name
            if key in poly_map:
                raise ValueError(f"Duplicate polygon name in section z={sec.z}: '{key}'")
            poly_map[key] = ContinuousSectionField._polygon_to_dict(p)

        return {
            "z": float(sec.z),
            "polygons": poly_map,  # <-- dict, non lista
        }

    @staticmethod
    def _pt_to_xy(pt):
        return [float(pt.x), float(pt.y)]

    @staticmethod
    def _polygon_to_dict(poly):
        if XY is not None:
            verts = [XY((float(v.x), float(v.y))) for v in poly.vertices]
        else:
            verts = [[float(v.x), float(v.y)] for v in poly.vertices]

        return {
            "weight": float(poly.weight),
            "vertices": verts,
        }

    # --------------------------------------------------------------------------------------
    


    def section_area_list_report(
        self,
        z: float,
        w_tol: float = 0.0,
        zero_w_eps: float = 0.0,
        group_mode: str = "weight",
    ) -> None:
    
        """
        Print an accountant-style area listing at section z, grouped by ABSOLUTE weight (w_abs),
        and include the two requested totals:

            Occupied Total Surface: sum(A_net)
            Homogenized area:       sum(A*w) where A*w = A_net * w_abs

        Sterile/accounting intent:
        - A_net is the polygon signed area as computed (no abs()).
        With CCW-only polygons, A_net should be positive.
        - W in the table is w_abs (absolute weight along the container chain).
        w_tol bins W for grouping/printing only; the product A*w uses the RAW w_abs.

        Parameters
        ----------
        z : float
            Longitudinal coordinate where the section is sampled.
        w_tol : float
            Grouping tolerance for weights. If > 0, weights are rounded to the nearest multiple
            of w_tol for grouping/printing purposes only.
        zero_w_eps : float
            Passed through to the underlying computation (kept for consistency with your API).
            This report's totals are defined strictly by the table columns, not by zero_w_eps.
        group_mode : str
            Currently only "weight" is supported. Kept as a label in the header.
        """
        import numpy as np

        if group_mode != "weight":
            raise ValueError("Only group_mode='weight' is supported by this report.")

        # Run the underlying sterile computation and request per-polygon records
        res = self.section_area_by_weight(
            z=float(z),
            w_tol=float(w_tol),
            include_per_polygon=True,
            debug=False,
            zero_w_eps=float(zero_w_eps),
        )

        per = res.get("per_polygon", [])
        if not per:
            print(f"SECTION AREA LIST REPORT at z = {z:g}")
            print("(No polygons found.)")
            return

        # Use S0/S1 as the stable name sources for the left/right columns
        s0_polys = self.s0.polygons
        s1_polys = self.s1.polygons
        n_polys = len(s0_polys)

        # Determine index formatting width (e.g., [03], [102])
        idx_width = max(2, len(str(max(0, n_polys - 1))))

        # Weight binning must match section_area_by_weight grouping behavior
        def _bin_weight(w: float) -> float:
            if w_tol and w_tol > 0.0:
                return round(w / w_tol) * w_tol
            return w

        # Build sortable rows: grouped weight then polygon index
        rows = []
        for rec in per:
            idx = int(rec["idx"])
            if not (0 <= idx < n_polys):
                # Strict coherence: report expects S0/S1 indexing alignment
                raise ValueError(f"Polygon index out of range in report: idx={idx}")

            w_abs_raw = float(rec["w_abs"])
            #print(f"DEBUG idx {idx} w_abs_raw {w_abs_raw}")
            w_group = _bin_weight(w_abs_raw) if (w_tol and w_tol > 0.0) else w_abs_raw

            # A_net is the sterile signed area (no abs)
            a_net = float(rec["area"])

            # A*w must use RAW w_abs (not binned), to remain faithful to "A*w" as a per-polygon product
            a_w = a_net * w_abs_raw

            s0_name = getattr(s0_polys[idx], "name", "")
            s1_name = getattr(s1_polys[idx], "name", "")

            rows.append(
                {
                    "w_group": w_group,
                    "w_abs_raw": w_abs_raw,
                    "idx": idx,
                    "s0_name": s0_name,
                    "s1_name": s1_name,
                    "a_net": a_net,
                    "a_w": a_w,
                }
            )

        rows.sort(key=lambda r: (r["w_group"], r["idx"]))

        # Totals requested by the user: defined by table columns, not by the underlying "effective" totals
        occupied_total_surface = sum(r["a_net"] for r in rows)  # Σ A_net
        homogenized_area = sum(r["a_w"] for r in rows)          # Σ (A_net * w_abs_raw)

        # Header (match the requested style as closely as possible)
        print(f"SECTION AREA LIST REPORT at z = {z:g}")
        print("=" * 80)
        print(f"group_mode={group_mode}  w_tol={w_tol:g}\n")
        print(
            f"{'W':>10} | {'id':<6} | {'s0.name':<18} | {'s1.name':<18} | "
            f"{'A_net':>12} | {'A*w':>12}"
        )
        print("-" * 90)

        # Print W only when the group changes (blank otherwise)
        last_w = None
        for r in rows:
            w_disp = r["w_group"]
            w_str = f"{w_disp:g}" if (last_w is None or w_disp != last_w) else ""
            last_w = w_disp

            idx_str = f"[{r['idx']:0{idx_width}d}]"
            print(
                f"{w_str:>10} | {idx_str:<6} | "
                f"{r['s0_name']:<18} | {r['s1_name']:<18} | "
                f"{r['a_net']:>12.6g} | {r['a_w']:>12.6g}"
            )

        print("-" * 90)

        # Totals block (accountant-style, as requested)
        print(f"Occupied Total Surface: {occupied_total_surface:.12g}")
        print(f"Homogenized area:       {homogenized_area:.12g}")
    # --------------------------------------------------------------------------------------



    def section_area_by_weight(
        self,
        z: float,
        w_tol: float = 0.0,
        include_per_polygon: bool = False,
        debug: bool = False,
        zero_w_eps: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Compute area breakdown at section z grouped by ABSOLUTE weight (w_abs).

        This implementation is strictly index-based:
        - polygon identity is the polygon index
        - names are never used for topology, matching, or grouping
        - direct-children topology is taken from S0 through build_direct_children_map(z)

        Geometric reporting rule:
        - For each polygon i, the reported geometric area is:
            area_geom_net[i] = area_geom[i] - sum(area_geom[j] for j in direct_children[i])
        - This subtraction is purely geometric and does not depend on weight.
        - Children are subtracted even if their weight is zero.

        Effective area rule:
        - The effective homogenized area is computed from the net geometric area
        of each polygon multiplied by its absolute weight sampled on the section:
            total_area = sum(area_geom_net[i] * w_abs[i])

        Args:
            z: Longitudinal coordinate where the section is sampled.
            w_tol: Grouping tolerance for absolute weights. If > 0, weights are rounded
                to the nearest multiple of w_tol for grouping purposes only.
            include_per_polygon: If True, includes detailed per-polygon data in output.
            debug: If True, prints debug information to stdout.
            zero_w_eps: Threshold for considering an absolute weight as zero when
                        computing total_area_nonzero. If |w_abs| <= zero_w_eps,
                        that polygon contribution is excluded from the nonzero sum.

        Returns:
            Dictionary containing:
            - z: Coordinate (float)
            - total_area: Effective homogenized area = sum(area_net * w_abs)
            - total_area_nonzero: Effective homogenized area excluding |w_abs| <= zero_w_eps
            - total_area_geometric: Total net geometric surface = sum(area_net)
            - groups: List of absolute-weight groups with accumulated net geometric areas
            - per_polygon: (Optional) Detailed per-polygon data
        """

        # --- 1) Sample section at z ---
        sec = self.section(z)

        if not hasattr(sec, "polygons") or sec.polygons is None:
            raise ValueError(f"Section at z={z} has no polygons.")

        if not hasattr(self.s0, "polygons") or self.s0.polygons is None:
            raise ValueError("self.s0 has no polygons.")

        n_sec = len(sec.polygons)
        n_s0 = len(self.s0.polygons)

        # This report uses the S0 index topology and therefore requires that
        # the sampled section preserves the same polygon indexing contract.
        if n_sec != n_s0:
            raise ValueError(
                f"Section at z={z} has {n_sec} polygons, but S0 has {n_s0}. "
                f"Index-based reporting requires matching polygon counts."
            )

        # --- 2) Get direct-children topology from S0 ---
        # The topology is stable and index-based. The function returns only
        # polygons that actually have direct children as keys.
        direct_children_map = self.build_direct_children_map(z)

        # Normalize the map so every polygon index exists as a key, including
        # polygons with no direct children.
        direct_children: Dict[int, List[int]] = {idx: [] for idx in range(n_s0)}

        for parent_idx, child_list in direct_children_map.items():
            if not isinstance(parent_idx, int):
                raise TypeError(
                    f"Parent index in direct-children map must be int, got {type(parent_idx).__name__}"
                )
            if not (0 <= parent_idx < n_s0):
                raise ValueError(f"Invalid parent index in direct-children map: {parent_idx}")

            for child_idx in child_list:
                if not isinstance(child_idx, int):
                    raise TypeError(
                        f"Child index in direct-children map must be int, got {type(child_idx).__name__}"
                    )
                if not (0 <= child_idx < n_s0):
                    raise ValueError(f"Invalid child index in direct-children map: {child_idx}")
                direct_children[parent_idx].append(child_idx)

        # Build the direct parent map from the children map.
        # A polygon can have at most one direct parent.
        parent_idx_map: Dict[int, Optional[int]] = {idx: None for idx in range(n_s0)}

        for parent_idx, child_list in direct_children.items():
            for child_idx in child_list:
                if parent_idx_map[child_idx] is not None:
                    raise ValueError(
                        f"Polygon idx={child_idx} has multiple direct parents: "
                        f"{parent_idx_map[child_idx]} and {parent_idx}"
                    )
                parent_idx_map[child_idx] = parent_idx

        # --- 3) Read section data directly from sampled polygons ---
        # weightabs is taken directly from the sampled section polygon.
        # No recursive reconstruction is performed.
        area_geom: Dict[int, float] = {}
        w_rel_map: Dict[int, float] = {}
        w_abs_map: Dict[int, float] = {}

        for idx, poly in enumerate(sec.polygons):
            if not hasattr(poly, "weight"):
                raise ValueError(f"Polygon idx={idx} at z={z} has no 'weight' attribute.")
            if not hasattr(poly, "weightabs"):
                raise ValueError(f"Polygon idx={idx} at z={z} has no 'weightabs' attribute.")

            signed_area, (_, _) = _polygon_signed_area_and_centroid(poly)

            area_geom[idx] = float(signed_area)
            w_rel_map[idx] = float(poly.weight)
            w_abs_map[idx] = float(poly.weightabs)

        # --- 4) Compute the net geometric area of each polygon ---
        # Each polygon contributes with its own geometric area minus the geometric
        # areas of its direct children, regardless of weight.
        area_geom_net: Dict[int, float] = {}

        for idx in range(n_sec):
            area_children = sum(area_geom[child_idx] for child_idx in direct_children[idx])
            area_geom_net[idx] = area_geom[idx] - area_children

        # --- 5) Group net geometric areas by absolute weight ---
        def bin_weight(w: float) -> float:
            """Apply optional grouping tolerance to the absolute weight."""
            if w_tol and w_tol > 0.0:
                return round(w / w_tol) * w_tol
            return w

        groups: Dict[float, Dict[str, Any]] = {}
        per_polygon_records: List[Dict[str, Any]] = []

        for idx in range(n_sec):
            w_abs_raw = w_abs_map[idx]
            w_abs_grouped = bin_weight(w_abs_raw)
            area_net = area_geom_net[idx]

            if w_abs_grouped not in groups:
                groups[w_abs_grouped] = {
                    "w": w_abs_grouped,
                    "area": 0.0,
                    "polygons": [],
                }

            groups[w_abs_grouped]["area"] += area_net
            groups[w_abs_grouped]["polygons"].append(idx)

            per_polygon_records.append(
                {
                    "idx": idx,
                    "container_idx": parent_idx_map[idx],
                    "children_idx": list(direct_children[idx]),
                    "w_rel": w_rel_map[idx],
                    "w_abs": w_abs_raw,
                    "area_geom": area_geom[idx],
                    "area": area_net,
                }
            )

        # --- 6) Compute totals ---
        total_effective = sum(
            area_geom_net[idx] * w_abs_map[idx]
            for idx in range(n_sec)
        )

        total_effective_nonzero = sum(
            area_geom_net[idx] * w_abs_map[idx]
            for idx in range(n_sec)
            if abs(w_abs_map[idx]) > float(zero_w_eps)
        )

        total_geometric = sum(area_geom_net[idx] for idx in range(n_sec))

        groups_list = sorted(groups.values(), key=lambda d: d["w"])
        effective_denom = total_effective if total_effective != 0.0 else 1.0

        for group in groups_list:
            if group["w"] != 0.0:
                group["area_fraction"] = (group["area"] * group["w"]) / effective_denom
            else:
                group["area_fraction"] = 0.0

        # --- 7) Optional debug output ---
        if debug:
            print("=" * 60)
            print(f"section_area_by_weight at z={z}")
            print("-" * 60)
            for rec in sorted(per_polygon_records, key=lambda x: x["idx"]):
                print(
                    f"  [{rec['idx']}] "
                    f"parent={rec['container_idx']} "
                    f"children={rec['children_idx']} "
                    f"w_rel={rec['w_rel']:+.6f} "
                    f"w_abs={rec['w_abs']:+.6f} "
                    f"area_geom={rec['area_geom']:+.6e} "
                    f"area_net={rec['area']:+.6e}"
                )
            print("-" * 60)
            print(f"Total geometric net surface: {total_geometric:+.6e}")
            print(f"Total effective area:        {total_effective:+.6e}")
            print(f"Total effective nonzero:     {total_effective_nonzero:+.6e}")
            print("=" * 60)

        # --- 8) Assemble output ---
        result: Dict[str, Any] = {
            "z": float(z),
            "total_area": float(total_effective),
            "total_area_nonzero": float(total_effective_nonzero),
            "total_area_geometric": float(total_geometric),
            "groups": groups_list,
        }

        if include_per_polygon:
            result["per_polygon"] = per_polygon_records

        return result

        


    # --------------------------------------------------------------------------------------

    
    def _determine_magnitude(self) -> None:
        """
        Compute a global geometric magnitude (scale) from the model's geometry and
        define tolerance values derived from that scale.

        This method is intentionally self-contained (no external helper functions),
        so it can be called once after object construction.

        It defines:
          - self.SCALE: characteristic length scale of the model
          - self._tol.EPS_L: linear/length tolerance (geometry predicates, intersections)
          - self._tol.EPS_A: area tolerance (degeneracy checks on areas, section integrals)
          - self._tol.EPS_K_ATOL / self._tol.EPS_K_RTOL: tolerances for matrix/numerical checks
        """
        # 1) Collect bounding box over all points in start/end sections
        inf = float("inf")
        min_x, min_y = inf, inf
        max_x, max_y = -inf, -inf

        # NOTE: adapt these attribute names to your internal storage.
        # The idea is: iterate over all polygons in both end sections and read their vertices.
        #
        # Expected structure (examples):
        #   self.sections["I"][obj_id][poly_id].points  -> list[(x,y)]
        #   self.sections["F"][obj_id][poly_id].points
        #
        # If your storage differs, only adjust this traversal; the rest stays the same.


        # --- Bounding box over BOTH endpoint sections (S0 and S1) ---
        # In your code:
        #   self.s0, self.s1 are Section objects
        #   section.polygons is Tuple[Polygon, ...]
        #   polygon.vertices is Tuple[Pt, ...]
        #   Pt has attributes .x and .y

        for sec in (self.s0, self.s1):
            for poly in sec.polygons:
                for v in poly.vertices:
                    x = float(v.x)
                    y = float(v.y)

                    if x < min_x: min_x = x
                    if y < min_y: min_y = y
                    if x > max_x: max_x = x
                    if y > max_y: max_y = y




        # Handle empty geometry defensively
        if min_x is inf:
            # No points found: fall back to a safe default
            dx = dy = 0.0
        else:
            dx = max_x - min_x
            dy = max_y - min_y

        # 2) Characteristic length scale.
        # Include L so long/slender members scale reasonably even with small cross-section extents.
        L = float(getattr(self, "L", 0.0))
        S = max(dx, dy, abs(L), 1.0)

        SCALE = S

        # 3) Tolerances
        #
        # _tol.EPS_L: geometric/linear tolerance.
        # Use this for: orientation tests, point-on-segment, segment intersection, etc.
        _tol.EPS_L = 1e-12 * S

        # _tol.EPS_A: area tolerance. Must scale as S^2.
        # Use this for: "area nearly zero" checks, summed areas, etc.
        _tol.EPS_A = 1e-12 * (S * S)

        # _tol.EPS_K: numerical/matrix tolerances.
        # Here it's better to keep a relative tolerance and a small absolute tolerance.
        # - RTOL controls proportional differences (scale-free).
        # - ATOL controls tiny absolute noise.
        #
        # If your matrices scale strongly with geometry/material, you can scale ATOL too,
        # but RTOL is the primary guard.
        _tol.EPS_K_RTOL = 1e-10
        _tol.EPS_K_ATOL = 1e-12 * (S ** 4)  # scales as S⁴, consistent with moment of inertia units

        # Optional: if you want a single "_tol.EPS_K" name as you wrote,
        # keep it as the absolute tolerance, and still keep RTOL separately.
        _tol.EPS_K = _tol.EPS_K_ATOL
        #print(f"SCALE {SCALE} _tol.EPS_K {_tol.EPS_K} _tol.EPS_L{_tol.EPS_L} _tol.EPS_A {_tol.EPS_A}")




    def to_dict(self, include_weight_laws=True):


        data = {
            "CSF": {
                "sections": {
                    "S0": self._section_to_dict(self.s0),
                    "S1": self._section_to_dict(self.s1),
                },
            }
        }

        if include_weight_laws:

            if self.weight_laws:
                out = []
                for idx in sorted(self.weight_laws):
                    i = idx - 1
                    n0 = self.s0.polygons[i].name
                    n1 = self.s1.polygons[i].name
                    out.append(f"{n0},{n1}: {self.weight_laws[idx]}")
                data["CSF"]["weight_laws"] = out

            shear_out = []


            if self.shear_weight_laws_default is not None:
                #shear_out.append(self.shear_weight_laws_default)
                shear_out.append(self.QuotedStr(self.shear_weight_laws_default))
            if self.shear_weight_laws:
                for idx in sorted(self.shear_weight_laws):
                    i = idx
                    n0 = self.s0.polygons[i].name
                    n1 = self.s1.polygons[i].name
                    shear_out.append(f"{n0},{n1}: {self.shear_weight_laws[idx]}")

            if shear_out:
                data["CSF"]["shear_weight_laws"] = shear_out

        return data
        


    def to_yaml(self, filepath: Optional[str] = None, include_weight_laws: bool = True) -> str:
        data = self.to_dict(include_weight_laws=include_weight_laws)
        if yaml is not None:
            yml = yaml.dump(
                data,
                Dumper=CSFDumper,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
                default_flow_style=False,
            )
        else:
            yml = _simple_yaml_dump(data) + "\n"
        #print("DEBUG yml:\n", yml)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(yml)

        return yml

    """
    Geometry-only object:
    - stores two endpoint sections (at z0 and z1)
    - returns intermediate Section at any z via linear interpolation of corresponding vertices
    """


    def get_lobatto_integration_points(self, n_points: int = 5, L: float = None) -> List[float]:
        """
        Calculates the global Z-coordinates for OpenSees integration points using 
        the Gauss-Lobatto quadrature rule.
        
        RATIONALE:
        In finite element analysis (specifically for OpenSees forceBeamColumn elements), 
        the Gauss-Lobatto rule is preferred because it includes the endpoints of the 
        interval (z=0 and z=L). This is critical for detecting anomalies at the 
        very base of the shaft (e.g., FHWA Soft Toe) or at the top connection.
        
        ALGORITHM:
        1. Generate the roots of the derivative of the (n-1)-th Legendre Polynomial.
        2. These roots (plus -1.0 and 1.0) form the abscissae in the natural 
        coordinate system [-1, 1].
        3. Map these abscissae from [-1, 1] to the physical domain [z0, z1] or [0, L].
        
        Args:
            n_points (int): Number of integration points. Must be >= 2.
            L (float, optional): Total length of the element. If None, it uses 
                                the distance between the two defined sections.
        
        Returns:
            List[float]: A list of global Z-coordinates where OpenSees will 
                        sample the section properties.
        """
        z_start = self.s0.z
        z_end = self.s1.z
        
        if n_points < 2:
            raise ValueError("Number of integration points must be at least 2 for Gauss-Lobatto.")

        # 1. Physical boundaries
        
        # Usiamo section0 e section1 come definito nel costruttore field = ContinuousSectionField(section0=s0, section1=s1)
        
        z_start = self.s0.z
        z_end = self.s1.z
        actual_L = L if L is not None else (z_end - z_start)

        # 2. Calculation of Gauss-Lobatto Abscissae in range [-1, 1]
        # For n points, we need roots of P'_{n-1}(x)
        if n_points == 2:
            abscissae = [-1.0, 1.0]
        else:
            # The internal points are the roots of the derivative of Legendre polynomial P_{n-1}
            roots = np.polynomial.legendre.Legendre.deriv(
                np.polynomial.legendre.Legendre([0]*(n_points-1) + [1])
            ).roots()
            abscissae = np.concatenate(([-1.0], roots, [1.0]))

        # 3. Mapping from [-1, 1] to [z_start, z_start + actual_L]
        z_coords = [z_start + (xi + 1.0) * (actual_L / 2.0) for xi in abscissae]
        
        # Sort to ensure numerical stability
        z_coords = sorted(z_coords)
        return z_coords



    def __init__(self, section0: Section, section1: Section):
            
        if len(section0.polygons) != len(section1.polygons):
            raise ValueError(
                f"Mismatch: section0 has {len(section0.polygons)} polygons, "
                f"but section1 has {len(section1.polygons)} polygons."
        )

        if section0.z == section1.z:
            raise ValueError("Sections must be at different z coordinates.")

        self.s0 = section0
        self.s1 = section1

        # single source of truth
        self.z0 = section0.z
        self.z1 = section1.z
        self._determine_magnitude()
        # Optional list of callables or strings for custom weight interpolation
        self.weight_laws: Optional[Dict[int, str]] = None
        self.shear_weight_laws_default: Optional[str] = None   
        self.shear_weight_laws: Optional[Dict[int, str]] = None
        self._validate_inputs()
         
    def _strip_model_tags(name: str) -> str:
        """
        Remove everything starting from @cell or @wall (case-insensitive).
        If neither tag exists, return original trimmed name.
        Examples:
          "MP1_outer@cell@t=0.05" -> "MP1_outer"
          "legA@wall@alpha=0.8"   -> "legA"
          "poly_no_tags"          -> "poly_no_tags"
        """
        s = (name or "").strip()
        # cut from first occurrence of @cell or @wall to end of string
        return re.sub(r'(?i)@(cell|wall)\b.*$', '', s).strip()

    def _strip_model_tags(self, name: str) -> str:
        """
        Normalize polygon name for matching:
        - trim spaces
        - remove everything starting from @cell, @wall, or @closed (case-insensitive)
        """
        s = str(name or "").strip()
        return re.sub(r'(?i)@(cell|wall|closed)\b.*$', '', s).strip()


    def set_shear_weight_laws(self, laws: Union[List[str], Dict[Union[int, str], str]]) -> None:
        """
        Set shear-weight variation laws.

        Rules:
        - List item without ':' is the global default shear-weight law.
        - List item with ':' is a polygon-specific shear-weight law.
        - Polygon indices are 0-based.
        - Polygon-name mapping follows the same S0/S1 homology logic used by set_weight_laws().
        """

        if not isinstance(laws, (list, dict)):
            raise ValueError("shear_weight_laws must be a list or a dictionary.")

        num_polygons = len(self.s0.polygons)

        valid_names0 = [self._strip_model_tags(p.name) for p in self.s0.polygons]
        valid_names1 = [self._strip_model_tags(p.name) for p in self.s1.polygons]

        # Reset current shear-weight laws.
        self.shear_weight_laws_default = None
        self.shear_weight_laws = {}

        normalized_map: Dict[int, str] = {}
        default_formula: Optional[str] = None

        # Parse list input.
        if isinstance(laws, list):
            for item in laws:
                if not isinstance(item, str):
                    raise ValueError(f"Critical Error: invalid shear_weight law item: {item}")

                item = item.strip()

                if not item:
                    raise ValueError("Critical Error: empty shear_weight law.")

                # Global default law.
                if ":" not in item:
                    if default_formula is not None:
                        raise ValueError(
                            "Critical Error: multiple default shear_weight laws declared."
                        )

                    default_formula = item
                    continue

                # Polygon-specific law.
                left, formula = item.split(":", 1)
                left = left.strip()
                formula = formula.strip()

                if not left:
                    raise ValueError("Critical Error: missing shear_weight law target.")

                if not formula:
                    raise ValueError(
                        f"Critical Error: empty shear_weight formula for target '{left}'."
                    )

                raw_names = [
                    self._strip_model_tags(name.strip())
                    for name in left.split(",")
                    if name.strip()
                ]

                if len(raw_names) == 2:
                    n0, n1 = raw_names

                    if n0 not in valid_names0:
                        raise KeyError(
                            f"Critical Error: Polygon '{n0}' not found in Section 0."
                        )

                    if n1 not in valid_names1:
                        raise KeyError(
                            f"Critical Error: Polygon '{n1}' not found in Section 1."
                        )

                    idx0 = valid_names0.index(n0)
                    idx1 = valid_names1.index(n1)

                    if idx0 != idx1:
                        raise ValueError(
                            f"Homology Mismatch: '{n0}' (idx {idx0}) and "
                            f"'{n1}' (idx {idx1}) must match."
                        )

                    normalized_map[idx0] = formula

                elif len(raw_names) == 1:
                    n0 = raw_names[0]

                    if n0 not in valid_names0:
                        raise KeyError(
                            f"Critical Error: Polygon '{n0}' not found."
                        )

                    idx0 = valid_names0.index(n0)
                    normalized_map[idx0] = formula

                else:
                    raise ValueError(
                        f"Critical Error: invalid shear_weight law target: '{left}'"
                    )

        # Parse dict input.
        elif isinstance(laws, dict):
            for key, formula in laws.items():
                if not isinstance(formula, str):
                    raise ValueError(
                        f"Critical Error: invalid shear_weight formula for key '{key}'."
                    )

                formula = formula.strip()

                if not formula:
                    raise ValueError(
                        f"Critical Error: empty shear_weight formula for key '{key}'."
                    )

                if isinstance(key, int):
                    idx = key

                    if idx < 0 or idx >= num_polygons:
                        raise IndexError(
                            f"Index {idx} out of range (0-{num_polygons - 1})."
                        )

                    normalized_map[idx] = formula

                elif isinstance(key, str):
                    n0 = self._strip_model_tags(key.strip())

                    if n0 not in valid_names0:
                        raise KeyError(
                            f"Critical Error: Polygon '{n0}' not found."
                        )

                    idx = valid_names0.index(n0)
                    normalized_map[idx] = formula

                else:
                    raise ValueError(
                        f"Critical Error: invalid shear_weight law key: {key}"
                    )

        z0 = self.s0.z
        z1 = self.s1.z
        L_val = z1 - z0
        z_mid = L_val / 2.0

        # Validate default law on all polygons.
        if default_formula is not None:
            for idx in range(num_polygons):
                try:
                    p0_test = self.s0.polygons[idx]
                    p1_test = self.s1.polygons[idx]
                    '''
                    evaluate_weight_formula(
                        default_formula,
                        p0_test,
                        p1_test,
                        z0=z0,
                        z1=z1,
                        zt=z_mid,
                    )
                    '''
                except Exception as e:
                    raise ValueError(
                        f"VALIDATION FAILED: The default shear_weight formula "
                        f"is not valid for polygon '{valid_names0[idx]}'.\n"
                        f"Formula: '{default_formula}'\n"
                        f"Error encountered at the midpoint: {e}"
                    )

        # Validate polygon-specific laws.
        for idx, formula in normalized_map.items():
            try:
                p0_test = self.s0.polygons[idx]
                p1_test = self.s1.polygons[idx]
                '''
                evaluate_weight_formula(
                    formula,
                    p0_test,
                    p1_test,
                    z0=z0,
                    z1=z1,
                    zt=z_mid,
                )
                '''
            except Exception as e:
                raise ValueError(
                    f"VALIDATION FAILED: The shear_weight formula for "
                    f"'{valid_names0[idx]}' is not valid.\n"
                    f"Formula: '{formula}'\n"
                    f"Error encountered at the midpoint: {e}"
                )

        # Store validated laws.
        self.shear_weight_laws_default = default_formula

        for idx, formula in normalized_map.items():
            self.shear_weight_laws[idx] = str(formula)

    #end set_shear_weight_laws 


    def set_weight_laws(self, laws: Union[List[str], Dict[Union[int, str], str]]) -> None:
        """
        Sets weight variation laws. 
        If a polygon name is not found or homology fails, it raises an error 
        to prevent falling back to default linear behavior.
        """
        if not isinstance(laws, (list, dict)):
            raise ValueError("weight_laws must be a list or a dictionary.")
        
        num_polygons = len(self.s0.polygons)
        #valid_names0 = [p.name for p in self.s0.polygons]
        #valid_names1 = [p.name for p in self.s1.polygons]
        
        # Keep original polygon names as declared in S0/S1 strip @cell @wall
        valid_names0 = [self._strip_model_tags(p.name) for p in self.s0.polygons]
        valid_names1 = [self._strip_model_tags(p.name) for p in self.s1.polygons]
        # Reset current laws 
        self.weight_laws = {}
        normalized_map = {}
        
        # 1. PARSING & STRICT TRANSLATION
        if isinstance(laws, list):
            for i, item in enumerate(laws):
                if isinstance(item, str) and ":" in item:
                    left, formula = item.split(":", 1)
                    left, formula = left.strip(), formula.strip()
                    #raw_names = [n.strip() for n in left.split(",")]
                    raw_names = [self._strip_model_tags(n) for n in left.split(",")]
                    if len(raw_names) == 2:
                        n0, n1 = raw_names
                        # STRICT CHECK: If the name does not exist, Error
                        if n0 not in valid_names0:
                            raise KeyError(f"Critical Error: Polygon '{ raw_names[0]}' not found in Section 0.")
                        if n1 not in valid_names1:
                            raise KeyError(f"Critical Error: Polygon '{raw_names[1]}' not found in Section 1.")
                        
                        idx0 = valid_names0.index(n0) + 1
                        idx1 = valid_names1.index(n1) + 1
                        
                        
                        # STRICT CHECK: Homology (must be the same polygon)
                        if idx0 != idx1:
                            raise ValueError(f"Homology Mismatch: '{n0}' (pos {idx0}) and '{n1}' (pos {idx1}) must match.")
                        
                        normalized_map[idx0] = formula
                        #print(f"DEBUG idx0 {idx0} idx1 {idx1} formula {formula}")
                    
                    elif len(raw_names) == 1:
                        n0 = raw_names[0]
                        if n0 not in valid_names0:
                            raise KeyError(f"Critical Error: Polygon '{n0}' not found.")
                        normalized_map[valid_names0.index(n0) + 1] = formula # 1 based 
                else:
                   if n0 not in valid_names0:
                       raise ValueError(f"Critical Error: Polygon '{n0}' not found.")
                   normalized_map[valid_names0.index(n0) + 1] = formula
                
                   # Positional list case
                   # if i < num_polygons:
                   #     normalized_map[i + 1] = item

        elif isinstance(laws, dict):
            raise ValueError(f"Critical Error: not valid {laws} ")
            '''
            for key, law in laws.items():
                target_idx = None
                if isinstance(key, int):
                    target_idx = key
                elif isinstance(key, str):
                    if key not in valid_names0:
                        raise KeyError(f"Critical Error: No polygon named '{key}' found.")
                    target_idx = valid_names0.index(key) + 1
                
                if target_idx is not None:
                    if target_idx < 1 or target_idx > num_polygons:
                        raise IndexError(f"Index {target_idx} out of range (1-{num_polygons}).")
                    normalized_map[target_idx] = law
            '''   

        z0, z1 = self.s0.z, self.s1.z
        L_val = z1 - z0
        z_mid = L_val / 2.0 # Actual RELATIVE Z value halfway between the sections
        
        # Compute t consistently with the interpolation formula
        # If L_val is 0 (coincident sections), t is forced to 0 to avoid division by zero
        #t_mid = (z_mid - z0) / L_val if L_val != 0 else 0.0
        
        
        for idx, formula in normalized_map.items():
                           
            if isinstance(formula, str):
                    try:
                        # Endpoint polygon references for distance calculations
                        p0_test = self.s0.polygons[idx-1]
                        p1_test = self.s1.polygons[idx-1]
                        
                        # Generation of midpoint vertices for p_mid (required for d(i,j) helper)
                        current_verts = tuple(v0.lerp(v1,z_mid,L_val) for v0, v1 in zip(p0_test.vertices, p1_test.vertices))
                        
                        # 1. Calculate the total length of the field
                        l_total = abs(self.s1.z - self.s0.z)
                        
                        try:
                            # We test the formula at mid-span (t=0.5) to verify syntax and logic
                            
                            we = evaluate_weight_formula(formula, p0_test, p1_test,z0=self.s0.z,z1=self.s1.z,zt=z_mid)
                            
                        except Exception as e:                      
                            raise ValueError(
                                f"VALIDATION FAILED: The formula for '{p0_test.name}' is not valid.\n"
                                f"Formula: '{formula}'\n"
                                f"Error encountered at the midpoint::: {e}"
                            )
                        
                    except Exception as e:
                        raise ValueError(
                            f":VALIDATION FAILED: The formula for '{valid_names0[idx-1]}' is not valid.\n"
                            f"Formula: '{formula}'\n"
                            f"Error encountered at the midpoint:- {e}"
                        )
        
        # 2. EFFECTIVE ASSIGNMENT 
        for idx, formula in normalized_map.items():

            if formula is None: continue
           
            # Save as an integer for the interpolator
            self.weight_laws[idx] = str(formula)
            #print(f"DEBUG idx {idx}")
            '''
            try:
                numeric_w = float(formula)
                if 1 <= idx <= num_polygons:
                    # Force update on s0 and s1 polygons
                    object.__setattr__(self.s0.polygons[idx-1], 'weight', numeric_w)
                    object.__setattr__(self.s1.polygons[idx-1], 'weight', numeric_w)
            except ValueError:
                # The formula is a function; it will be evaluated during interpolation
                pass
            '''
        # SUCCESS - Weight laws correctly assigned
        #print(f"SUCCESS - Weight laws correctly assigned: {self.weight_laws}")


    def _validate_inputs(self) -> None:
        if len(self.s0.polygons) != len(self.s1.polygons):
            raise ValueError("Start/end sections must have the same number of polygons.")

        for i, (p0, p1) in enumerate(zip(self.s0.polygons, self.s1.polygons)):
            if len(p0.vertices) != len(p1.vertices):
                raise ValueError(
                    f"Polygon index {i} has different vertex counts: "
                    f"{len(p0.vertices)} vs {len(p1.vertices)}"
                )
            
    def _interpolate_weight(self, w0: float, w1: float, z: float, p0: Polygon, p1: Polygon, law: Optional[str]) -> float:
        
        L_val = abs(self.s1.z - self.s0.z)
        
        if isinstance(law, str) and law.strip():
            # z is real RELATIVE not [0..1]
            # Use the existing section attributes. 
            # Based on the error, self.section1 doesn't exist. 
            # In ContinuousSectionField, endpoints are usually self.s0 and self.s1
            # Since p_current is not in the signature, we interpolate vertices 
            # locally to allow the d(i, j) helper to work at height z
            #
            
            
            #current_verts = tuple(v0.lerp(v1, z,L_val) for v0, v1 in zip(p0.vertices, p1.vertices))
            #p_current = Polygon(vertices=current_verts, weight=w0, name=p0.name) ## w0 is dummy value
            
            try:
                wcust = evaluate_weight_formula(law, p0, p1, self.s0.z,self.s1.z,zt=z)  
                return wcust
            except Exception as e:                  
                raise ValueError(
                    f"VALIDATION FAILED-: The formula for '{p0.name} '{p1.name}' is not valid.\n"
                    f"Formula: '{law}'\n"
                    f"Error encountered at the midpoint:: {e}"
                )
            
        # Default fallback: Linear Interpolation
        #
        return w0 + (w1 - w0)/L_val * z



    def _interpolate_shear_weight(self, w: float,w0: float, w1: float, z: float, p0: Polygon, p1: Polygon, law: Optional[str]) -> float:

        
        if isinstance(law, str) and law.strip():
            # z is real RELATIVE not [0..1]
            # Use the existing section attributes. 
            # Based on the error, self.section1 doesn't exist. 
            # In ContinuousSectionField, endpoints are usually self.s0 and self.s1
            # Since p_current is not in the signature, we interpolate vertices 
            # locally to allow the d(i, j) helper to work at height z
            #
            try:
                # 
                wcust = evaluate_shear_weight_formula(law, p0, p1, self.s0.z,self.s1.z,zt=z,w=w)  
                return wcust
            except Exception as e:                  
                raise ValueError(
                    f"VALIDATION FAILED-: The formula for '{p0.name} '{p1.name}' is not valid.\n"
                    f"Formula: '{law}'\n"
                    f"Error encountered at the midpoint:: {e}"
                )
            
        # Default fallback: w means G=E
        #
        return w

  
    def _to_t(self, z: float) -> float:
        z = float(z)
        if not (min(self.z0, self.z1) <= z <= max(self.z0, self.z1)):
            raise ValueError(f"z={z} is outside [{self.z0}, {self.z1}].")
        return (z - self.z0) / (self.z1 - self.z0)



    def section(self, z: float) -> Section: 
        #-----------------------------------------------------
        # helpers
        #-----------------------------------------------------
        verbose=False
        def get_shear_weight_law(self, idx: int) -> Optional[str]:
            if self.shear_weight_laws is not None:
                if idx in self.shear_weight_laws:
                    return self.shear_weight_laws[idx]
            if self.shear_weight_laws_default is not None:
                return self.shear_weight_laws_default
            return None
        
        def parse_iso(s):
            if not s:
                return -0.50
            m = re.search(r'iso\(([-\d.]+)\)', s, re.IGNORECASE)
            if m:
                return float(m.group(1))
            return float('nan')
              
        def _resolve_topology_and_t_from_names(
            p0_name: str,
            p1_name: str,
            z: float,
            z0: float,
            z1: float,
        ) -> Tuple[Optional[str], Optional[float]]:
            """
            Resolve topology tag and thickness t(z) from two polygon names.

            Design intent
            -------------
            This helper is conservative and explicit:
            - It resolves topology from tags in names (@cell, @wall, @closed).
            - It resolves thickness from @t=... with linear interpolation in z.
            - It does NOT build the final runtime name (that is delegated to a second helper).

            Topology policy
            ---------------
            - If both names define topology and they differ, raise CSFError (blocking).
            - If topology exists only on one side, keep it as constant.
            - If no topology is found on both sides, return topology=None.

            Thickness policy
            ----------------
            - If @t exists on both sides -> interpolate linearly at z.
            - If @t exists on one side only -> keep constant.
            - If @t missing on both sides -> t_value=None.
            - If resolved topology is @cell and t_value is None -> blocking CSFError.

            Parameters
            ----------
            p0_name, p1_name : str
                Polygon names at start/end stations.
            z : float
                Absolute query coordinate.
            z0, z1 : float
                Absolute bounds used for interpolation.

            Returns
            -------
            (topology_tag, t_value) : Tuple[Optional[str], Optional[float]]
                topology_tag in {'@cell', '@wall', '@closed'} or None.
                t_value as positive float or None.

            Raises
            ------
            CSFError
                On incompatible topology, invalid @t format/value, or @cell without thickness.
            """

            def _norm_name(s: str) -> str:
                """Lowercase + trim helper."""
                return str(s or "").strip().lower()

            def _extract_topology(name: str) -> Optional[str]:
                """
                Extract at most one topology tag from name.

                Valid tags:
                    @cell, @wall, @closed

                If more than one topology tag appears in the same name, raise CSFError.
                """
                low = _norm_name(name)
                has_cell = "@cell" in low
                has_wall = "@wall" in low
                has_closed = "@closed" in low

                n = int(has_cell) + int(has_wall) + int(has_closed)
                if n > 1:
                    raise CSFError(
                        f"Invalid polygon name '{name}': multiple topology tags found "
                        f"(@cell/@wall/@closed)."
                    )

                if has_cell:
                    return "@cell"
                if has_wall:
                    return "@wall"
                if has_closed:
                    return "@closed"
                return None

            def _parse_t(name: str) -> Optional[float]:
                """
                Parse @t=<number> from a name.

                Returns
                -------
                float | None
                    Positive thickness if present, otherwise None.

                Raises
                ------
                CSFError
                    If @t exists but is malformed or non-positive.
                """
                s = str(name or "")
                low = s.lower()
                token = "@t="
                i = low.find(token)
                if i < 0:
                    return None

                j = i + len(token)
                if j >= len(s):
                    raise CSFError(f"Invalid @t tag in polygon name: '{name}'")

                allowed = set("0123456789.+-eE")
                buf = []
                for ch in s[j:]:
                    if ch in allowed:
                        buf.append(ch)
                    else:
                        break

                if not buf:
                    raise CSFError(f"Invalid numeric @t value in polygon name: '{name}'")

                try:
                    t_val = float("".join(buf))
                except Exception:
                    raise CSFError(f"Invalid numeric @t value in polygon name: '{name}'")

                if t_val <= 0.0:
                    raise CSFError(f"Non-positive @t value in polygon name: '{name}'")
                return t_val

            def _interp_linear(zv: float, z0v: float, z1v: float, v0: float, v1: float) -> float:
                """
                Linear interpolation with clamped lambda in [0, 1].
                """
                dz = z1v - z0v
                if abs(dz) <= _tol.EPS_L:
                    return v0
                lam = (zv - z0v) / dz
                if lam < 0.0:
                    lam = 0.0
                elif lam > 1.0:
                    lam = 1.0
                return (1.0 - lam) * v0 + lam * v1

            # --- Resolve topology ---
            top0 = _extract_topology(p0_name)
            top1 = _extract_topology(p1_name)

            if top0 is not None and top1 is not None and top0 != top1:
                raise CSFError(
                    f"Incompatible topology tags between stations: "
                    f"'{p0_name}' ({top0}) vs '{p1_name}' ({top1})."
                )

            topology = top0 if top0 is not None else top1

            # --- Resolve thickness ---
            t0 = _parse_t(p0_name)
            t1 = _parse_t(p1_name)

            if t0 is not None and t1 is not None:
                t_val = _interp_linear(float(z), float(z0), float(z1), float(t0), float(t1))
            elif t0 is not None:
                t_val = float(t0)  # constant from S0
            elif t1 is not None:
                t_val = float(t1)  # constant from S1
            else:
                t_val = None

            # 
            if t_val is not None and t_val <= 0.0:
                raise CSFError(
                    f"Resolved non-positive thickness t={t_val} "
                    f"from '{p0_name}' -> '{p1_name}' at z={z}."
                )
            '''
            # Mandatory thickness for @cell
            if topology == "@cell" and t_val is None:
                raise CSFError(
                    f"Missing @t for @cell between '{p0_name}' and '{p1_name}'."
                )
            '''
            return topology, t_val


        def _build_interpolated_polygon_name(
            p0_name: str,
            p1_name: str,
            topology_tag: Optional[str],
            t_value: Optional[float],
        ) -> str:
            """
            Build the runtime polygon name from resolved metadata.

            Important
            ---------
            - This helper does NOT interpolate values.
            - It only formats a canonical name for the interpolated section.

            Naming policy
            -------------
            - Canonical base name is taken from S0 left-part before '@'
            (fallback to S1 if S0 base is empty).
            - Different S0/S1 base names are allowed (no blocking mismatch).
            - If topology is None -> return only base.
            - @cell requires t_value.
            - @wall / @closed accept optional t_value.

            Examples
            --------
            - base@cell@t=0.25
            - base@wall
            - base@wall@t=0.18
            - base@closed
            """

            def _left_of_at(name: str) -> str:
                """Return substring before first '@'."""
                s = str(name or "").strip()
                k = s.find("@")
                return s[:k] if k >= 0 else s

            def _fmt_t(t: float) -> str:
                """Compact numeric formatting for tags."""
                return f"{float(t):.12g}"

            base0 = _left_of_at(p0_name)
            base1 = _left_of_at(p1_name)

            # Conservative base selection: prefer S0 identity.
            base = base0 if base0 else base1
            if not base:
                raise CSFError(
                    f"Invalid polygon base name(s): '{p0_name}' / '{p1_name}'"
                )

            # No topology -> plain base name
            if topology_tag is None:
                return base

            if topology_tag == "@cell":
                
                if t_value is None:
                    raise CSFError(f"Missing @t for @cell polygon '{base}'.")
                
                return f"{base}@cell@t={_fmt_t(t_value)}"

            if topology_tag == "@wall":
                if t_value is None:
                    return f"{base}@wall"
                return f"{base}@wall@t={_fmt_t(t_value)}"

            if topology_tag == "@closed":
                if t_value is None:
                    return f"{base}@closed"
                return f"{base}@closed@t={_fmt_t(t_value)}"

            raise CSFError(
                f"Unsupported topology tag '{topology_tag}' for polygon '{base}'."
            )
        
        ### end helpers 

        # in input z is absol   ute
        origz=z-self.z0 # make origz relative
        
        #t = self._to_t(z) # normalize z 
        lenght = abs(self.z1 - self.z0)
        if z < self.z0 or z > self.z1:
            raise CSFError(f"z={z} out of bounds [{self.z0}, {self.z1}]")
        polys: List[Polygon] = []

        for i, (p0, p1) in enumerate(zip(self.s0.polygons, self.s1.polygons)):
                        
            verts = tuple(v0.lerp(v1, origz,lenght) for v0, v1 in zip(p0.vertices, p1.vertices))
            #print(f"DEBUG t {p0.name} {p1.name}")
            # keep weight/name from p0 by default
            # polys.append(Polygon(vertices=verts, weight=p0.weight, name=p0.name))

            ### interpolation here
            # Identify if a custom law exists for the current polygon index.
            # Support for both List (by index) and Dictionary (by index or by name).
            current_law = None
            shear_current_law = None
            if self.weight_laws is not None:
                current_law = self.weight_laws.get(i+1,None)# 1 based i'm sorry

            shear_current_law = get_shear_weight_law(self,idx=i)
            poisson=parse_iso(shear_current_law)
            
            # --- Weight source selection for child polygon interpolation ---
            #
            # A Polygon attribute named `weight` serves two distinct roles depending
            # on the stage of the object's lifecycle:
            #
            # STAGE 1 - First instantiation (from raw YAML input or code):
            #   `weight` holds the RAW, ABSOLUTE weight supplied by the user.
            #   At this stage `weightabs` is None because the nesting hierarchy has
            #   not yet been resolved. The Section constructor reads `weight` as the
            #   absolute value and uses it to derive both the effective (relative)
            #   weight and `weightabs` for every polygon in the hierarchy.
            #
            # STAGE 2 - Re-instantiation (from an already-resolved Section):
            #   When a Section that has already been through Stage 1 is used as the
            #   basis for a new SectionField (e.g. inside compute_saint_venant_Jv2),
            #   `weight` now contains the RELATIVE weight - i.e. the value after
            #   nesting resolution has already been applied. Using it again as an
            #   absolute weight would cause the nesting logic to run a second time
            #   on an already-resolved value, producing wrong results (observed as
            #   `weight_at_z = -1.0` for nested polygons instead of the correct 0.0).
            #
            #   At Stage 2, `weightabs` is already populated with the correct
            #   absolute weight from the first resolution pass and is therefore the
            #   reliable source to feed into interpolation.
            #
            # RESOLUTION:
            #   `weightabs is None`  ->  Stage 1: use `weight` (it IS the absolute weight)
            #   `weightabs is not None` ->  Stage 2: use `weightabs` (weight is relative)
            #
            # WHY is the attribute called `weight` and not `weightabs` from the start?
            #   At ingestion time only one weight value exists per polygon - the raw
            #   user-supplied scalar. Calling it `weight` is the most natural name at
            #   that point. The concept of "absolute vs relative" only becomes
            #   meaningful once the containment hierarchy is known, which happens
            #   inside the Section constructor. Renaming the input attribute to
            #   `weightabs` from the start would have been semantically premature and
            #   would have forced every YAML author and API caller to use a name whose
            #   meaning only becomes clear after an internal resolution step.
            #   The current design keeps the external API simple (`weight` in YAML)
            #   while using `weightabs` as the post-resolution canonical reference.


            w0 = p0.weightabs if p0.weightabs is not None else p0.weight
            w1 = p1.weightabs if p1.weightabs is not None else p1.weight
            interp_weight_child = self._interpolate_weight(w0, w1, origz, p0, p1, current_law)
            #interp_shear_weight_child = self._interpolate_shear_weight(interp_weight_child)
            interp_shear_weight_child = self._interpolate_shear_weight(
                                                    w   = interp_weight_child,
                                                    w0  = None, # not used yet
                                                    w1  = None, # not used yet
                                                    z   = origz,
                                                    p0  = p0,
                                                    p1  = p1,
                                                    law = shear_current_law,
                                                )
           
            idx_pol_parent= self.get_container_polygon_index(p0,i)
            # initialize parent
            polparent0 = None
            polparent1 = None
            parent_law = None
            shear_parent_law = None

            # default value when for parent whens not found    
            interp_weight_parent = 0 
            interp_shear_weight_parent = 0

            if idx_pol_parent is not None:
                polparent0 = self.s0.polygons[idx_pol_parent]
                polparent1 = self.s1.polygons[idx_pol_parent]
                
                if self.weight_laws is not None:
                    parent_law = self.weight_laws.get(idx_pol_parent + 1, None)# 1 base i'm sorry
                    
                shear_parent_law = get_shear_weight_law(self,idx=idx_pol_parent)

                interp_weight_parent = self._interpolate_weight(polparent0.weight, polparent1.weight, origz, polparent0, polparent1, parent_law)

                interp_shear_weight_parent = self._interpolate_shear_weight(
                                                    w   = interp_weight_parent,
                                                    w0  = None, # not used yet
                                                    w1  = None, # not used yet
                                                    z   = origz,
                                                    p0  = p0,
                                                    p1  = p1,
                                                    law = shear_parent_law,
                                                )
                
            #nameparent = polparent0.name if polparent0 is not None else "None" 
            interp_weight_relative = interp_weight_child - interp_weight_parent #this is very important 
            interp_shear_weight_relative = interp_shear_weight_child - interp_shear_weight_parent #this is very important 
            
            if verbose:
                print(f"DEBUG pol{i} : z {origz} : name {p0.name} : parent {idx_pol_parent}")
                print(f"  current_law              {current_law}")
                print(f"  parent_law               {parent_law}")
                print(f"  shear_current_law        {shear_current_law}")
                print(f"  shear_parent_law         {shear_parent_law}")
                print(f"  interp_weight_child      {interp_weight_child}")
                print(f"  interp_weight_parent     {interp_weight_parent}")
                print(f"  interp_shear_weight_child  {interp_shear_weight_child}")
                print(f"  interp_shear_weight_parent {interp_shear_weight_parent}")
                print(f"  interp_shear_weight_relative {interp_shear_weight_relative}")

            #print (f"DEBUG idx_pol_parent {idx_pol_parent}-{i} interp_weight_child {interp_weight_child} interp_weight_parent {interp_weight_parent} interp_weight_relative {interp_weight_relative} ")
            #print ("------------------------------------------------------")
            #print(f"DEBUG z {z} child {i} : name {p0.name}  interp_weight_child {interp_weight_child} current_law {current_law} : idx_pol_parent {idx_pol_parent} parent_law {parent_law} : interp_weight_parent {interp_weight_parent} : interp_weight_relative {interp_weight_relative}")
            #poly = Polygon(vertices=verts, weight=interp_weight_relative, name=p0.name)
            # Build runtime polygon metadata from both reference names.
            # We first resolve topology and thickness consistently along z
            # (including mandatory @t for @cell and optional @t for @wall),
            # then compose a normalized name for the interpolated section.
            # This centralizes tag logic in section(z) 
                
            topology_tag, t_value = _resolve_topology_and_t_from_names(
                p0_name=p0.name,
                p1_name=p1.name,
                z=z,          
                z0=self.z0,
                z1=self.z1,
            )
            if t_value:
                

                poly_name = _build_interpolated_polygon_name(
                    p0_name=p0.name,
                    p1_name=p1.name,
                    topology_tag=topology_tag,
                    t_value=t_value,
                )
            else:
                poly_name=p0.name+":"+p1.name # add both 
            #poly = Polygon(vertices=verts, weight=interp_weight_relative,weightabs=interp_weight_child,name=poly_name)
            # polygon setting 

            poly = Polygon(vertices=verts,
                            weight=interp_weight_relative,
                            weightabs=interp_weight_child,
                            shear_weight=interp_shear_weight_relative,
                            shear_weightabs=interp_shear_weight_child,
                            poisson=poisson,
                            name=poly_name
                        )

            '''
            if not re.search(r'(?i)@(cell|wall|closed)\b', str(poly.name or "")) and  polygon_has_self_intersections(poly):
                #silent
                warnings.warn(
                    f"Self-intersection detected in polygon '{poly.name}' at z={z:.3f}",
                    RuntimeWarning
                )
            '''   
            polys.append(poly)
        return Section(polygons=tuple(polys), z=float(z))

# -------------------------
# Digestor: Section properties (2D polygon-based)
# -------------------------

def _polygon_signed_area_and_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    """
    Shoelace. 
    with no weight 
    """
    verts_xy = [(v.x, v.y) for v in poly.vertices]
    A, Cx, Cy = _signed_area_centroid_xy(verts_xy)

    return A, (Cx, Cy)

def polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    # with weight
    A_signed, (Cx, Cy) = _polygon_signed_area_and_centroid(poly)
    A_mag = (A_signed) 
    return poly.weight * A_mag, (Cx, Cy)


def section_data(field: ContinuousSectionField, z: float) -> dict:
    """
    z is ABSOLUTE
    Extracts the complete geometric state and physical properties of a section 
    at a specific longitudinal coordinate (z).

    TECHNICAL SUMMARY:
    This function acts as a high-level accessor for the Continuous Section Field. 
    It performs a synchronized extraction of both the interpolated boundary 
    geometry and the corresponding integral properties (Area, First/Second Moments). 
    It provides a discrete "snapshot" of a 3D ruled solid at any point along 
    its integration path.

    WORKFLOW AND DATA ARCHITECTURE:
    1. Geometric Reconstruction:
       The function first invokes the internal Linear Interpolation (LERP) 
       mechanism to reconstruct the homogenized polygonal boundaries at 
       coordinate 'z'. This ensures topological consistency across the 
       longitudinal domain.

    2. Property Integration:
       Once the geometry is established, the 'section_properties' engine 
       is executed to compute the sectional digest. This involves:
       - Zeroth Moment: Area (A).
       - First Moments: Centroidal coordinates (Cx, Cy).
       - Second Moments: Moments of inertia (Ix, Iy, Ixy) and the Polar 
         Moment (J).

    3. Data Encapsulation:
       The results are packaged into a dictionary structure, decoupling the 
       raw geometric data (vertices/polygons) from the derived structural 
       parameters.

    APPLICABILITY:
    This function is the standard interface for structural analysis routines 
    that require local stiffness or stress evaluation at specific points 
    along a non-prismatic member.

    RETURNS:
       A dictionary containing:
       - 'section': The Section object (polygonal boundaries at z).
       - 'properties': A dictionary of computed geometric constants.
    """




    section = field.section(z)
    props = section_properties(section)

    return {
        "section": section,     # 
        "properties": props,    # A, Cx, Cy, Ix, Iy, Ixy, J
    }



def section_properties(section: Section) -> Dict[str, float]:
    """
    Computes the integral geometric properties for a composite cross-section.

    TECHNICAL SUMMARY:
    This function performs a multi-pass integration over a set of weighted 
    polygons to derive the global geometric constants. It manages homogenization 
    by algebraically summing contributions, allowing for the representation of 
    complex domains with voids or varying material densities.

    ALGORITHMIC WORKFLOW:
    1. First-Order Moments (Area and Centroid):
       - Aggregates the weighted area (A) and the first moments of area (Qx, Qy) 
         for all constituent polygons.
       - Locates the global centroid (Cx, Cy) of the composite section.

    2. Second-Order Moments (Inertia about Origin):
       - Computes the area moments of inertia (Ix, Iy) and the product of 
         inertia (Ixy) relative to the global coordinate origin (0,0).

    3. Translation of Axes (Parallel Axis Theorem):
       - Applies the Huygens-Steiner Theorem to shift the moments of inertia 
         from the global origin to the newly calculated centroidal axes:
         I_centroid = I_origin - A * d^2
       - This transformation ensures the properties are intrinsic to the 
         section's geometry, independent of the global coordinate system.

    4. Polar Moment Extraction:
       - Derives the Polar Second Moment of Area (J) about the centroid as 
         the sum of the orthogonal centroidal moments (Ix + Iy).

    RETURNS:
       A comprehensive dictionary containing:
       - 'A': Net weighted area.
       - 'Cx', 'Cy': Centroidal coordinates.
       - 'Ix', 'Iy', 'Ixy': Second moments of area about centroidal axes.
       - 'Ip': Polar moment of area.
    """
    # First pass: area + centroid
    A_tot = 0.0
    Cx_num = 0.0
    Cy_num = 0.0

    poly_cache = []
    ii=0
    for poly in section.polygons:
        ii=ii+1
        A_i, (cx_i, cy_i) = polygon_area_centroid(poly)
        A_tot += A_i
        
        Cx_num += A_i * cx_i
        Cy_num += A_i * cy_i
        poly_cache.append((poly, A_i, cx_i, cy_i))

    if abs(A_tot) < _tol.EPS_A:
        raise ValueError("Composite area is ~0;- cannot compute centroid/properties reliably. ")

    Cx = Cx_num / A_tot
    
    Cy = Cy_num / A_tot

    # Second pass: inertia about origin then shift to centroid
    Ix_o = 0.0
    Iy_o = 0.0
    Ixy_o = 0.0

    for poly, _, _, _ in poly_cache:
        ix, iy, ixy = polygon_inertia_about_origin(poly)
        Ix_o += ix
        Iy_o += iy
        Ixy_o += ixy

    # Parallel axis theorem to centroid
    Ix_c = Ix_o - A_tot * (Cy * Cy)
    Iy_c = Iy_o - A_tot * (Cx * Cx)
    Ixy_c = Ixy_o - A_tot * (Cx * Cy)

    J = Ix_c + Iy_c


    if abs(A_tot)<_tol.EPS_A:
        A_tot = 0
    if abs(Cx)<_tol.EPS_L:
        Cx = 0
    if abs(Cy)<_tol.EPS_L:
        Cy = 0
    if abs(Ix_c)<_tol.EPS_K_ATOL:
        Ix_c = 0
    if abs(Iy_c)<_tol.EPS_K_ATOL:
        Iy_c = 0
    if abs(Ixy_c)<_tol.EPS_K_ATOL:
        Ixy_c= 0
    if abs(J)<_tol.EPS_K_ATOL:
        J= 0                
    return {
        "z": section.z,
        "A": A_tot,
        "Cx": Cx,
        "Cy": Cy,
        "Ix": Ix_c,
        "Iy": Iy_c,
        "Ixy": Ixy_c,
        "Ip": J,
    }


# -------------------------
# Visualization helpers
# -------------------------

def _set_axes_equal_3d(ax) -> None:
    """
    Configures 3D axis limits to perform a 'selective zoom' and maintain 
    consistent aspect ratios for cross-sectional visualization.

    TECHNICAL SUMMARY:
    This function normalizes the viewport of a Matplotlib 3D projection. 
    It ensures that the horizontal plane (X-Y) is scaled isotropically 
    (equal aspect ratio) to prevent geometric distortion of the sections, 
    while allowing the longitudinal axis (Z) to retain its full physical 
    extent for structural context.

    ALGORITHMIC LOGIC:
    1. Limit Extraction:
       Retrieves current bounding box limits for X, Y, and Z dimensions 
       to determine the object's spatial center.

    2. Planar Isotropic Scaling:
       Calculates a maximum radius based on the spans of X and Y. By 
       applying this radius symmetrically to both horizontal axes, the 
       function ensures that circles or ellipses appear without 
       eccentricity distortion.

    3. Longitudinal Preservation:
       Unlike standard 'equal axis' commands, this logic preserves the 
       original Z-limits. This is crucial for high-aspect-ratio solids, 
       ensuring the entire height is visible within the frame.

    4. Box Aspect Ratio:
       Sets the 'box_aspect' to (1, 1, 2) to force a vertical emphasis, 
       making slender solids visually representative of their physical 
       proportions.
    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    # Calcoliamo i centri
    x_mid = sum(x_limits) / 2.0
    y_mid = sum(y_limits) / 2.0
    z_mid = sum(z_limits) / 2.0

    # Determine the maximum range for the X-Y plane only
    # (Ensures horizontal geometry fills the space without distortion)
    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    radius_xy = 0.5 * max(x_range, y_range)

    # Apply centered isotropic zoom on X and Y
    ax.set_xlim3d([x_mid - radius_xy, x_mid + radius_xy])
    ax.set_ylim3d([y_mid - radius_xy, y_mid + radius_xy])
    
    # Maintain physical Z-limits for the longitudinal axis
    ax.set_zlim3d(z_limits)

    # Force a visual box aspect to emphasize verticality
    ax.set_box_aspect((1, 1, 2))




# ============================================================
# Example: Continuous Section Field – Static Properties Demo
# ============================================================
#
# This script demonstrates how to:
# - define polygonal cross-sections,
# - interpolate them along a longitudinal axis (Z),
# - compute geometric and static properties,
# - visualize both 2D sections and the 3D ruled solid.
#
# The example uses a tapered T-section composed of:
# - a flange polygon
# - a web polygon
#
# Coordinate system:
#   X → horizontal
#   Y → vertical
#   Z → longitudinal
#
# NOTE:
# A negative centroid Y-coordinate (Cy) is expected in this example
# because most of the section area lies below the global X-axis.
#
# ============================================================


if __name__ == "__main__":
    from csf.visualizer import Visualizer
    # --------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 0)
    # --------------------------------------------------------
    # The start section is a T-shape composed of two polygons:
    # - flange (horizontal plate)
    # - web (vertical plate)


    # Define start polygons (T-Section at Z=0)
    poly0_start = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web Definition: Rectangle from (-0.2, -1.0) to (0.2, 0.2)
    # Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left (CCW)
    poly1_start = Polygon(
        vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0),  Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

    # --------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 10)
    # --------------------------------------------------------
    # The flange remains unchanged.
    # The web depth increases linearly from 1.0 to 2.5,
    # producing a tapered T-section along the Z-axis.

    poly0_end = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web becomes deeper: Y-bottom moves from -1.0 to -2.5
    # MAINTAIN CCW ORDER: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left
    poly1_end = Polygon(
        vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

      # --------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # --------------------------------------------------------
    # Each Section groups polygons and assigns a Z position.

    s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)

    # --------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.
    field = ContinuousSectionField(section0=s0, section1=s1)

    # --------------------------------------------------------
    # 5 Print Analysis
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.


    sec= field.section(10.0)
    full_analysis = section_full_analysis(sec)
    section_print_analysis(full_analysis)
    print(f"Area (A):               {full_analysis['A']:.4f}      # Net area")

    # --------------------------------------------------------
    # 6. VISUALIZATION
    # --------------------------------------------------------
    # - 2D section plot at Z = 5.0
    # - 3D ruled solid visualization
    viz = Visualizer(field)
    # Generate 2D plot for the specified slice
    viz.plot_section_2d(z=10.0)
    # Generate 3D plot of the interpolated solid
    # line_percent determines the density of the longitudinal ruled lines
    viz.plot_volume_3d(line_percent=100.0, seed=1)
    plt.show()
    


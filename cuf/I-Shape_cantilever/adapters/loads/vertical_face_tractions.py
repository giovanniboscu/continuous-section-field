# Version: CSF-CUF local vertical face tractions v03 - 2026-11-20
"""Reusable vertical global-Z tractions on selected CSF polygon faces.

Local composite adapter: the problem YAML supplies ``polygons`` (CSF names),
``upper_z_MPa`` and ``lower_z_MPa``. For each selected polygon only the named
upper/lower Y-parallel edge is loaded if its respective p_z is nonzero.

GEOMETRIC SCOPE (intentional, checked before integration):
  * Each selected CSF domain must be a finite, nondegenerate, CCW quadrilateral
    Q4 (four boundary vertices); "Q4" here is geometry, NOT a CUF Q4 FE.
  * Exactly two opposite edges must be parallel to global Y in every defining
    CSF end section, one upper and one lower at different global-Z elevations.
    The vertices preserve their ordering between S0 and S1.
  * Longitudinal tilting/tapering IS supported; the edges need not generate
    surfaces parallel to the global XY plane.
  * Loaded edges cannot have a positive-length overlap with another polygon
    boundary (no loading of shared/internal interfaces).
  * Nested/cut-out domains are not supported by this adapter.

MECHANICAL SCOPE (unchanged from independent_z_faces.py):
  * The traction direction is ALWAYS global Z, with no direction or law key.
  * p_z is signed force per unit projected XY area (N/mm^2 = MPa).
  * The physical-area traction is t=(0,0,p_z*abs(n_z)), for unit normal n.
    The quadrature therefore uses p_z*abs(normal_area_z) dt dx.
  * No point, end, normal-pressure or other surface loading is introduced.

The solver-facing build_load_vector signature is identical to the legacy one.
"""

from __future__ import annotations

import numpy as np


def _vertices(section, x: float, domain_id: int) -> np.ndarray:
    polygon = section.domain(float(x), int(domain_id))
    result = np.asarray(polygon.vertices, dtype=float)
    if result.shape != (4, 2) or not np.all(np.isfinite(result)):
        raise ValueError(
            f"CSF domain {domain_id}: the vertical-face load supports only "
            "finite Q4 polygons (exactly four vertices)"
        )
    if getattr(polygon, "excluded_vertices", ()):
        raise ValueError(
            f"CSF domain {domain_id}: nested/cut-out polygons are not supported"
        )
    area = 0.5 * (
        np.dot(result[:, 0], np.roll(result[:, 1], -1))
        - np.dot(result[:, 1], np.roll(result[:, 0], -1))
    )
    if area <= 1.0e-10:
        raise ValueError(
            f"CSF domain {domain_id}: Q4 vertices must be CCW and nondegenerate"
        )
    return result


def _upper_lower_edges(vertices: np.ndarray) -> tuple[int, int]:
    """Find upper and lower edges; no dependence on vertex-0 location."""
    edges = np.roll(vertices, -1, axis=0) - vertices
    scale = max(float(np.ptp(vertices[:, 1])), 1.0)
    horizontal = [
        i for i in range(4)
        if abs(edges[i, 1]) <= 1.0e-9 * scale
        and abs(edges[i, 0]) > 1.0e-10 * scale
    ]
    if len(horizontal) != 2:
        raise ValueError(
            "Selected Q4 polygon must have exactly two Y-parallel edges "
            "(one upper, one lower) in each CSF reference section"
        )
    a, b = horizontal
    za = 0.5 * (vertices[a, 1] + vertices[(a + 1) % 4, 1])
    zb = 0.5 * (vertices[b, 1] + vertices[(b + 1) % 4, 1])
    if abs(za - zb) <= 1.0e-10:
        raise ValueError("Selected polygon upper/lower edges have equal elevation")
    top, bottom = (a, b) if za > zb else (b, a)
    # CCW orientation also determines the sign of each outward n_z.
    if -edges[top, 0] <= 0 or -edges[bottom, 0] >= 0:
        raise ValueError(
            "Selected Q4 upper/lower edges have inconsistent CCW orientation"
        )
    return top, bottom


def _domain_names(section, x0: float) -> tuple[dict[str, int], list[str]]:
    """Resolve ORIGINAL S0 polygon names via the CSF public inspection API.

    Evaluated section domain labels may be composite strings like
    'name_S0:name_S1'; those strings must not leak into the user YAML.
    The CSF inspection API gives the stable zero-based polygon index (idx).
    The CUF domain_id is idx+1. This matches the existing library adapters.
    """
    inspect = getattr(section, "inspect_section_entities", None)
    if not callable(inspect):
        raise TypeError(
            "CSF section provider must expose inspect_section_entities(x) "
            "for name-based polygon selection"
        )
    result = {}
    listed = []
    for entity in inspect(float(x0)):
        name = entity.get("s0_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("A CSF reference polygon has no nonempty S0 name")
        if name in result:
            raise ValueError(f"Duplicate CSF S0 polygon name {name!r}")
        domain_id = int(entity["idx"]) + 1
        if not 1 <= domain_id <= section.number_of_domains(x0):
            raise ValueError("CSF polygon index outside the CUF domain count")
        result[name] = domain_id
        listed.append(name)
    return result, listed


def _check_exterior_edge(section, x: float, domain_id: int, edge: int) -> None:
    """Reject selected horizontal edges shared with another CSF polygon.

    This is an explicit check for positive-length overlap in the YZ section,
    including partial overlap. Touching a neighboring edge at a single point
    is allowed. It checks the two CSF end sections; their affine interpolation
    retains the same named polygon and homologous edge indices.
    """
    selected = _vertices(section, x, domain_id)
    a, b = selected[edge], selected[(edge + 1) % 4]
    z_selected = 0.5 * float(a[1] + b[1])
    y_min, y_max = sorted((float(a[0]), float(b[0])))
    scale = max(1.0, *(abs(v) for v in (y_min, y_max, z_selected)))
    tol = 1.0e-9 * scale

    for other_id, other in enumerate(section.domains(x), start=1):
        if other_id == domain_id:
            continue
        other_vertices = np.asarray(other.vertices, dtype=float)
        if other_vertices.ndim != 2 or other_vertices.shape[1] != 2:
            raise ValueError(f"Invalid CSF boundary for neighbor {other_id}")
        for j in range(len(other_vertices)):
            c, d = other_vertices[j], other_vertices[(j + 1) % len(other_vertices)]
            if not np.all(np.isfinite([*c, *d])):
                raise ValueError(f"Non-finite CSF boundary for neighbor {other_id}")
            if abs(float(c[1]) - z_selected) > tol or abs(float(d[1]) - z_selected) > tol:
                continue
            c_min, c_max = sorted((float(c[0]), float(d[0])))
            overlap = min(y_max, c_max) - max(y_min, c_min)
            if overlap > tol:
                raise ValueError(
                    f"Selected loaded edge of CSF domain {domain_id} at x={x:g} "
                    f"overlaps internal/shared edge of domain {other_id}; "
                    "select an external face only"
                )


class VerticalFaceTractions:
    """One load component; accepts several polygon names (not several loads)."""

    def __init__(
        self, *, polygons, upper_z, lower_z, axial_gauss=8, edge_gauss=5,
        face_gauss=5,
    ):
        if not isinstance(polygons, list) or not polygons:
            raise ValueError("problem.load.polygons must be a nonempty list of names")
        if any(not isinstance(name, str) or not name.strip() for name in polygons):
            raise ValueError("problem.load.polygons contains an invalid name")
        if len(set(polygons)) != len(polygons):
            raise ValueError("problem.load.polygons contains duplicate names")
        self.polygons = tuple(polygons)
        self.upper_z = float(upper_z)
        self.lower_z = float(lower_z)
        self.axial_gauss = int(axial_gauss)
        self.edge_gauss = int(edge_gauss)
        # Kept for compatibility with the old YAML. Just as before, face_gauss
        # is validated but NOT used in the double integral (x x edge).
        self.face_gauss = int(face_gauss)
        if not np.isfinite(self.upper_z) or not np.isfinite(self.lower_z):
            raise ValueError("Surface load values must be finite")
        if min(self.axial_gauss, self.edge_gauss, self.face_gauss) < 3:
            raise ValueError("All supplied Gauss counts must be at least 3")

    def physical_surface_tractions(self, *, section_provider, x0, x1):
        """Resolve *physical* loaded edges once for CUF and FEM3D.

        Returns (domain_id, edge_start_vertex_id, signed_pz_MPa, side).
        Names, stable topology, orientation, and external-surface tests reuse
        the existing CSF-provider selection logic.  The magnitude is per
        projected XY area; direction is always global Z.  No extra YAML keys.

        Only the loaded polygons are restricted to horizontal-edge Q4 domains;
        the numerical solvers may use any number of other valid CSF domains.
        """
        x0, x1 = float(x0), float(x1)
        if not x1 > x0:
            raise ValueError("CSF longitudinal domain requires x1 > x0")
        available, names = _domain_names(section_provider, x0)
        faces = []
        for polygon_name in self.polygons:
            if polygon_name not in available:
                raise ValueError(
                    f"Selected CSF polygon {polygon_name!r} does not exist; "
                    f"available: {', '.join(names)}"
                )
            k = available[polygon_name]
            V0 = _vertices(section_provider, x0, k)
            V1 = _vertices(section_provider, x1, k)
            if k > section_provider.number_of_domains(x1):
                raise ValueError(f"CSF polygon {polygon_name!r} disappears at S1")
            edges0 = _upper_lower_edges(V0)
            if edges0 != _upper_lower_edges(V1):
                raise ValueError(
                    f"CSF polygon {polygon_name!r} changed upper/lower edge topology"
                )
            for edge, side, pz in (
                (edges0[0], "upper", self.upper_z),
                (edges0[1], "lower", self.lower_z),
            ):
                if pz != 0.0:
                    _check_exterior_edge(section_provider, x0, k, edge)
                    _check_exterior_edge(section_provider, x1, k, edge)
                    faces.append((int(k), int(edge), float(pz), side))
        return tuple(faces)

    def build_load_vector(
        self, *, section_provider, basis, mesh, dof_layout,
        longitudinal_integrator, x0, x1,
    ):
        del longitudinal_integrator
        x0, x1 = float(x0), float(x1)
        if x1 <= x0:
            raise ValueError("x1 must be > x0")
        if basis.size != dof_layout.basis_size:
            raise ValueError("CUF basis count and DOF layout disagree")
        # The same physical edge descriptors feed both CUF and OpenSees:
        # no second surface-selection algorithm is introduced for FEM3D.
        selected_faces = self.physical_surface_tractions(
            section_provider=section_provider, x0=x0, x1=x1,
        )
        faces_by_domain = {}
        for k, edge, pz, side in selected_faces:
            faces_by_domain.setdefault(k, []).append((edge, side, pz))
        vdot = {
            k: (_vertices(section_provider, x1, k)
                - _vertices(section_provider, x0, k)) / (x1 - x0)
            for k in faces_by_domain
        }

        print(
            f"[vertical-faces] polygons={list(self.polygons)} "
            f"upper_z={self.upper_z:g} MPa lower_z={self.lower_z:g} MPa",
            flush=True,
        )
        size = int(basis.size)
        vector = np.zeros(dof_layout.total_dofs, dtype=float)
        force = np.zeros(3)
        moment = np.zeros(3)
        by_face = {"upper": np.zeros(3), "lower": np.zeros(3)}
        gx, wx = np.polynomial.legendre.leggauss(self.axial_gauss)
        gt, wt = np.polynomial.legendre.leggauss(self.edge_gauss)
        for element in mesh.elements:
            for xi, w_x in zip(gx, wx):
                x = float(element.map_to_physical(float(xi)))
                N = np.asarray(element.shape_values(float(xi)), dtype=float)
                dx = float(w_x * element.jacobian)
                for k, selected_edges in faces_by_domain.items():
                    V = _vertices(section_provider, x, k)
                    for edge, name, pz in selected_edges:
                        j = (edge + 1) % 4
                        for t, w_t in zip(gt, wt):
                            yz = 0.5 * ((1 - t) * V[edge] + (1 + t) * V[j])
                            pt = 0.5 * (V[j] - V[edge])
                            px = 0.5 * ((1 - t) * vdot[k][edge] + (1 + t) * vdot[k][j])
                            normal_area = np.array([
                                pt[0] * px[1] - pt[1] * px[0],
                                pt[1],
                                -pt[0],
                            ], dtype=float)
                            # EXACT SAME projected-area law as the original:
                            # |n_z| dS = |normal_area_z| dt dx, never p_z*dS.
                            wforce = np.array(
                                [0.0, 0.0, pz * abs(normal_area[2])], dtype=float,
                            ) * dx * float(w_t)
                            Fs = np.array([
                                basis.value(tau, float(yz[0]), float(yz[1]), x=x)
                                for tau in range(1, size + 1)
                            ], dtype=float)
                            if not np.all(np.isfinite(Fs)):
                                raise ValueError("Non-finite CUF basis evaluation")
                            for a, node in enumerate(element.node_ids):
                                for tau, ftau in enumerate(Fs, start=1):
                                    for c in range(3):
                                        idx = dof_layout.index(
                                            node=node, tau=tau, component=c,
                                        )
                                        vector[idx] += N[a] * ftau * wforce[c]
                            force += wforce
                            by_face[name] += wforce
                            moment += np.cross([x, *yz], wforce)
        print(
            f"[vertical-faces] resultant upper={by_face['upper']} N "
            f"lower={by_face['lower']} N",
            flush=True,
        )
        print(
            f"[vertical-faces] total prescribed F={force} N; M={moment} Nmm",
            flush=True,
        )
        return vector, {
            "prescribed_force_N": force,
            "prescribed_moment_Nmm": moment,
        }

    def tracked_points(self, section_provider, x):
        return ()


def build_problem(problem_type, options):
    """Factory for the v01 local composite contract (no load.type field)."""
    if problem_type != "composite":
        raise ValueError("vertical_face_tractions expects problem.type: composite")
    allowed = {
        "polygons", "upper_z_MPa", "lower_z_MPa", "axial_gauss",
        "edge_gauss", "face_gauss",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        raise ValueError(f"Unknown vertical-face load options: {unknown}")
    required = {"polygons", "upper_z_MPa", "lower_z_MPa"}
    missing = sorted(required - set(options))
    if missing:
        raise ValueError(f"Missing vertical-face load options: {missing}")
    return VerticalFaceTractions(
        polygons=options["polygons"],
        upper_z=options["upper_z_MPa"],
        lower_z=options["lower_z_MPa"],
        axial_gauss=options.get("axial_gauss", 8),
        edge_gauss=options.get("edge_gauss", 5),
        face_gauss=options.get("face_gauss", 5),
    )

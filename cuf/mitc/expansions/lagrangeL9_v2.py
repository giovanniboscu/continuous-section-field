# Version: CSF-CUF Lagrange L9 transverse expansion v2 - 2026-10-10
#
# Changelog:
# - Preserves all v1 CSF-domain and point-location validation.
# - Builds the 9 physical Lagrange points of every CSF quadrilateral.
# - Uses the standard L9 natural-node numbering from the Carrera formulation.
# - Merges coincident points on shared polygon edges/vertices.
# - Builds deterministic local-L9 -> global-tau connectivity.
# - basis.size is now the assembled global L9 point count (57 for the
#   Carrera 9-L9 C-section model).
# - Adds diagnostic access to local points, global points, and connectivity.
# - L9 shape-function values and derivatives are intentionally NOT implemented
#   yet; solver evaluation stops explicitly after topology has been validated.
#
# Scope of v2:
#   CSF geometry -> local L9 points -> assembled global transverse topology.
#
# Important:
#   This file deliberately stops if the CUF solver tries to evaluate the basis.
#   It must not silently substitute a temporary approximation for L9.

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable

import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    register_cuf_basis_plugin,
)


_PLUGIN_NAME = "lagrangeL9"
_L9_ORDER = 2
_LOCAL_L9_SIZE = 9

# Carrera L9 natural-coordinate numbering:
#
#       7 ----- 6 ----- 5
#       |               |
#       8       9       4
#       |               |
#       1 ----- 2 ----- 3
#
# alpha: left -> right, beta: bottom -> top
_L9_NATURAL_POINTS = (
    (-1.0, -1.0),  # 1
    ( 0.0, -1.0),  # 2
    ( 1.0, -1.0),  # 3
    ( 1.0,  0.0),  # 4
    ( 1.0,  1.0),  # 5
    ( 0.0,  1.0),  # 6
    (-1.0,  1.0),  # 7
    (-1.0,  0.0),  # 8
    ( 0.0,  0.0),  # 9
)


@dataclass(frozen=True)
class L9Domain:
    """Immutable geometry record for one CSF polygon used as one L9 element."""

    domain_id: int
    name: str | None
    vertices: tuple[tuple[float, float], ...]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        ys = tuple(v[0] for v in self.vertices)
        zs = tuple(v[1] for v in self.vertices)
        return min(ys), max(ys), min(zs), max(zs)


@dataclass(frozen=True)
class L9GlobalPoint:
    """One assembled transverse L9 point and all local occurrences."""

    tau: int
    y: float
    z: float
    occurrences: tuple[tuple[int, int], ...]
    # occurrences contain (domain_id, local_l9_node), both one-based.


class LagrangeL9Basis(CUFBasis):
    """Lagrange-L9 transverse expansion driven by CSF polygon domains.

    Version 2 constructs the complete assembled transverse point topology but
    deliberately does not yet evaluate L9 shape functions.
    """

    def __init__(
        self,
        *,
        section_provider: Any,
        domain_source: str,
        mapping: str,
        connectivity: str,
        boundary_tolerance: float,
        require_prismatic: bool,
    ) -> None:
        if section_provider is None:
            raise ValueError("lagrangeL9 requires a section_provider")

        self._section_provider = section_provider
        self._domain_source = str(domain_source)
        self._mapping = str(mapping)
        self._connectivity_mode = str(connectivity)
        self._boundary_tolerance = float(boundary_tolerance)
        self._require_prismatic = bool(require_prismatic)

        if self._domain_source != "csf_polygons":
            raise ValueError(
                "lagrangeL9 v2 supports domain_source='csf_polygons' only"
            )
        if self._mapping != "isoparametric":
            raise ValueError(
                "lagrangeL9 v2 supports mapping='isoparametric' only"
            )
        if self._connectivity_mode != "shared_points":
            raise ValueError(
                "lagrangeL9 v2 supports connectivity='shared_points' only"
            )
        if (
            not math.isfinite(self._boundary_tolerance)
            or self._boundary_tolerance <= 0.0
        ):
            raise ValueError(
                "lagrangeL9 boundary_tolerance must be a finite positive number"
            )

        x0, x1 = section_provider.longitudinal_domain()
        self._x0 = float(x0)
        self._x1 = float(x1)
        self._x_ref = 0.5 * (self._x0 + self._x1)

        if not (
            math.isfinite(self._x0)
            and math.isfinite(self._x1)
            and self._x1 > self._x0
        ):
            raise ValueError(
                "lagrangeL9 requires a finite CSF longitudinal domain "
                "with x_end > x_start"
            )

        self._domains = self._read_domains(self._x_ref)
        if not self._domains:
            raise ValueError("lagrangeL9 found no CSF polygon domains")

        if self._require_prismatic:
            self._verify_prismatic_geometry()

        self._coordinate_scale = max(
            1.0,
            max(
                abs(value)
                for domain in self._domains
                for vertex in domain.vertices
                for value in vertex
            ),
        )
        self._merge_tolerance = self._boundary_tolerance * self._coordinate_scale

        (
            self._local_points,
            self._connectivity,
            self._global_points,
        ) = self._build_l9_topology()

    @property
    def order(self) -> int:
        """Polynomial interpolation order of an L9 element."""
        return _L9_ORDER

    @property
    def size(self) -> int:
        """Number of assembled global transverse L9 points/functions."""
        return len(self._global_points)

    @property
    def domain_count(self) -> int:
        return len(self._domains)

    @property
    def domains(self) -> tuple[L9Domain, ...]:
        return self._domains

    @property
    def x_reference(self) -> float:
        return self._x_ref

    @property
    def local_point_count(self) -> int:
        """Raw count before assembly: 9 times the number of CSF domains."""
        return len(self._domains) * _LOCAL_L9_SIZE

    @property
    def global_points(self) -> tuple[L9GlobalPoint, ...]:
        return self._global_points

    @property
    def connectivity(self) -> tuple[tuple[int, ...], ...]:
        """Per-domain local L9 node -> one-based global tau."""
        return self._connectivity

    @property
    def local_points(self) -> tuple[tuple[tuple[float, float], ...], ...]:
        """Physical coordinates of the nine local L9 points per domain."""
        return self._local_points

    @property
    def options(self) -> dict[str, object]:
        return {
            "domain_source": self._domain_source,
            "mapping": self._mapping,
            "connectivity": self._connectivity_mode,
            "boundary_tolerance": self._boundary_tolerance,
            "require_prismatic": self._require_prismatic,
        }

    def definition(self, tau: int):
        """Return stable global L9 point identity and local occurrences."""
        point = self._global_point(tau)
        return (
            "L9_GLOBAL_POINT",
            point.y,
            point.z,
            point.occurrences,
        )

    def locate_domains(
        self,
        y: float,
        z: float,
    ) -> tuple[int, ...]:
        """Return all CSF domain ids containing the physical point."""
        y = float(y)
        z = float(z)

        if not math.isfinite(y) or not math.isfinite(z):
            raise ValueError("lagrangeL9 point coordinates must be finite")

        matches = [
            domain.domain_id
            for domain in self._domains
            if self._point_in_polygon_inclusive(y, z, domain.vertices)
        ]
        return tuple(matches)

    def locate_unique_domain(
        self,
        y: float,
        z: float,
    ) -> int | None:
        """Return unique containing domain, None outside, error on interfaces."""
        matches = self.locate_domains(y, z)

        if not matches:
            return None

        if len(matches) != 1:
            raise ValueError(
                "point lies on a shared CSF interface/vertex and therefore "
                f"belongs to multiple lagrangeL9 domains: {matches}"
            )

        return matches[0]

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """L9 evaluation is deliberately unavailable in v2."""
        self._global_point(tau)
        del y, z, x
        raise NotImplementedError(
            "lagrangeL9 v2 builds the assembled L9 topology only; "
            "L9 shape-function evaluation will be added after the 57-point "
            "connectivity has been validated"
        )

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """L9 derivatives are deliberately unavailable in v2."""
        self._global_point(tau)
        if direction not in {"y", "z"}:
            raise ValueError("direction must be 'y' or 'z'")
        del y, z, x
        raise NotImplementedError(
            "lagrangeL9 v2 builds the assembled L9 topology only; "
            "L9 derivatives will be added after topology validation"
        )

    def diagnostic_rows(self) -> tuple[dict[str, object], ...]:
        """Return per-domain geometry, local points and global connectivity."""
        rows = []
        for index, domain in enumerate(self._domains):
            y_min, y_max, z_min, z_max = domain.bounds
            rows.append(
                {
                    "domain_id": domain.domain_id,
                    "name": domain.name,
                    "vertices": domain.vertices,
                    "bounds": (y_min, y_max, z_min, z_max),
                    "local_l9_points": self._local_points[index],
                    "global_tau": self._connectivity[index],
                }
            )
        return tuple(rows)

    def topology_summary(self) -> dict[str, object]:
        """Return compact counts for the step-by-step v2 validation."""
        shared = tuple(
            point for point in self._global_points
            if len(point.occurrences) > 1
        )
        return {
            "domains": self.domain_count,
            "local_points": self.local_point_count,
            "global_points": self.size,
            "shared_global_points": len(shared),
            "connectivity": self._connectivity,
        }

    def _build_l9_topology(self):
        """Construct local physical L9 points and merge coincident points."""
        local_points = []
        connectivity = []

        global_coords: list[tuple[float, float]] = []
        global_occurrences: list[list[tuple[int, int]]] = []

        for domain in self._domains:
            points = tuple(
                self._map_reference_to_physical(domain.vertices, alpha, beta)
                for alpha, beta in _L9_NATURAL_POINTS
            )
            local_points.append(points)

            local_to_global = []
            for local_node, (y, z) in enumerate(points, start=1):
                existing = self._find_existing_global_point(
                    y,
                    z,
                    global_coords,
                )

                if existing is None:
                    global_coords.append((float(y), float(z)))
                    global_occurrences.append(
                        [(domain.domain_id, local_node)]
                    )
                    tau = len(global_coords)
                else:
                    global_occurrences[existing].append(
                        (domain.domain_id, local_node)
                    )
                    tau = existing + 1

                local_to_global.append(tau)

            connectivity.append(tuple(local_to_global))

        global_points = tuple(
            L9GlobalPoint(
                tau=index + 1,
                y=coords[0],
                z=coords[1],
                occurrences=tuple(global_occurrences[index]),
            )
            for index, coords in enumerate(global_coords)
        )

        return (
            tuple(local_points),
            tuple(connectivity),
            global_points,
        )

    def _find_existing_global_point(
        self,
        y: float,
        z: float,
        global_coords: list[tuple[float, float]],
    ) -> int | None:
        for index, (gy, gz) in enumerate(global_coords):
            if (
                abs(float(y) - gy) <= self._merge_tolerance
                and abs(float(z) - gz) <= self._merge_tolerance
            ):
                return index
        return None

    @staticmethod
    def _map_reference_to_physical(
        vertices: tuple[tuple[float, float], ...],
        alpha: float,
        beta: float,
    ) -> tuple[float, float]:
        """Bilinear isoparametric map from [-1,1]^2 to one CSF quadrilateral.

        CSF polygon vertices must be cyclically ordered as the four corners
        corresponding to natural coordinates:

            1: (-1,-1)
            3: (+1,-1)
            5: (+1,+1)
            7: (-1,+1)

        This is exactly the ordering used by the current 9-polygon benchmark
        YAML (bottom-left, bottom-right, top-right, top-left).
        """
        if len(vertices) != 4:
            raise ValueError("L9 isoparametric mapping requires four vertices")

        a = float(alpha)
        b = float(beta)

        weights = (
            0.25 * (1.0 - a) * (1.0 - b),
            0.25 * (1.0 + a) * (1.0 - b),
            0.25 * (1.0 + a) * (1.0 + b),
            0.25 * (1.0 - a) * (1.0 + b),
        )

        y = sum(w * vertices[i][0] for i, w in enumerate(weights))
        z = sum(w * vertices[i][1] for i, w in enumerate(weights))
        return float(y), float(z)

    def _global_point(self, tau: int) -> L9GlobalPoint:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")
        if not 1 <= tau <= self.size:
            raise IndexError(f"tau must be in 1..{self.size}, got {tau}")
        return self._global_points[tau - 1]

    def _read_domains(self, x: float) -> tuple[L9Domain, ...]:
        raw_domains = tuple(self._section_provider.domains(float(x)))
        result = []

        for raw in raw_domains:
            domain_id = int(raw.domain_id)

            if getattr(raw, "excluded_vertices", ()):
                raise ValueError(
                    "lagrangeL9 v2 does not support nested/excluded CSF domains; "
                    f"domain {domain_id} has excluded_vertices"
                )

            vertices = np.asarray(raw.vertices, dtype=float)

            if vertices.shape != (4, 2):
                raise ValueError(
                    "lagrangeL9 requires each CSF polygon to be a four-vertex "
                    f"quadrilateral; domain {domain_id} has shape {vertices.shape}"
                )

            if not np.all(np.isfinite(vertices)):
                raise ValueError(
                    f"lagrangeL9 domain {domain_id} has non-finite vertices"
                )

            signed_area = self._polygon_signed_area(vertices)
            scale = max(1.0, float(np.max(np.abs(vertices))))
            if abs(signed_area) <= np.finfo(float).eps * scale * scale:
                raise ValueError(
                    f"lagrangeL9 domain {domain_id} has zero polygon area"
                )

            result.append(
                L9Domain(
                    domain_id=domain_id,
                    name=getattr(raw, "name", None),
                    vertices=tuple(
                        (float(y), float(z))
                        for y, z in vertices
                    ),
                )
            )

        ids = tuple(d.domain_id for d in result)
        expected = tuple(range(1, len(result) + 1))
        if ids != expected:
            raise ValueError(
                "lagrangeL9 requires stable contiguous CSF domain ids "
                f"{expected}; received {ids}"
            )

        return tuple(result)

    def _verify_prismatic_geometry(self) -> None:
        """Require the same polygon topology and coordinates along the beam."""
        for x in (self._x0, self._x1):
            current = self._read_domains(x)

            if len(current) != len(self._domains):
                raise ValueError(
                    "lagrangeL9 benchmark requires a prismatic CSF section; "
                    f"domain count differs at x={x}"
                )

            for reference, candidate in zip(self._domains, current):
                if reference.domain_id != candidate.domain_id:
                    raise ValueError(
                        "lagrangeL9 benchmark requires stable CSF domain ids"
                    )

                ref = np.asarray(reference.vertices, dtype=float)
                cur = np.asarray(candidate.vertices, dtype=float)

                scale = max(
                    1.0,
                    float(np.max(np.abs(ref))),
                    float(np.max(np.abs(cur))),
                )
                atol = self._boundary_tolerance * scale

                if not np.allclose(ref, cur, rtol=0.0, atol=atol):
                    raise ValueError(
                        "lagrangeL9 benchmark requires a prismatic CSF section; "
                        f"domain {reference.domain_id} changes with x"
                    )

    def _point_in_polygon_inclusive(
        self,
        y: float,
        z: float,
        vertices: Iterable[tuple[float, float]],
    ) -> bool:
        vertices = tuple(vertices)

        scale = max(
            1.0,
            abs(y),
            abs(z),
            max(abs(v) for point in vertices for v in point),
        )
        tol = self._boundary_tolerance * scale

        for index, a in enumerate(vertices):
            b = vertices[(index + 1) % len(vertices)]
            if self._point_on_segment(y, z, a, b, tol):
                return True

        inside = False
        j = len(vertices) - 1

        for i in range(len(vertices)):
            yi, zi = vertices[i]
            yj, zj = vertices[j]

            crosses = (zi > z) != (zj > z)
            if crosses:
                y_cross = (yj - yi) * (z - zi) / (zj - zi) + yi
                if y < y_cross:
                    inside = not inside

            j = i

        return inside

    @staticmethod
    def _point_on_segment(
        y: float,
        z: float,
        a: tuple[float, float],
        b: tuple[float, float],
        tol: float,
    ) -> bool:
        ay, az = a
        by, bz = b

        dy = by - ay
        dz = bz - az
        py = y - ay
        pz = z - az

        cross = dy * pz - dz * py
        length = math.hypot(dy, dz)

        if length == 0.0:
            return math.hypot(py, pz) <= tol

        if abs(cross) > tol * length:
            return False

        dot = py * dy + pz * dz
        if dot < -tol * length:
            return False

        squared_length = dy * dy + dz * dz
        if dot > squared_length + tol * length:
            return False

        return True

    @staticmethod
    def _polygon_signed_area(vertices: np.ndarray) -> float:
        y = vertices[:, 0]
        z = vertices[:, 1]
        return 0.5 * float(
            np.dot(y, np.roll(z, -1))
            - np.dot(z, np.roll(y, -1))
        )


def _parse_options(options) -> dict[str, object]:
    """Validate the complete option set reserved for the final expansion."""
    if options is None:
        options = {}

    if not isinstance(options, dict):
        options = dict(options)

    supported = {
        "domain_source",
        "mapping",
        "connectivity",
        "boundary_tolerance",
        "require_prismatic",
    }
    unknown = set(options).difference(supported)

    if unknown:
        raise ValueError(
            "lagrangeL9 received unsupported cuf.basis_options: "
            f"{sorted(unknown)}"
        )

    return {
        "domain_source": str(options.get("domain_source", "csf_polygons")),
        "mapping": str(options.get("mapping", "isoparametric")),
        "connectivity": str(options.get("connectivity", "shared_points")),
        "boundary_tolerance": float(
            options.get("boundary_tolerance", 1.0e-10)
        ),
        "require_prismatic": bool(options.get("require_prismatic", True)),
    }


def _build(
    *,
    order,
    section_provider,
    continuous_section_field,
    options,
):
    """Construct the definitive Lagrange-L9 expansion object, v2 stage."""
    del continuous_section_field  # Available by contract; not needed in v2.

    if int(order) != _L9_ORDER:
        raise ValueError(
            "lagrangeL9 is the quadratic 9-point Lagrange expansion; "
            "set cuf.order: 2"
        )

    config = _parse_options(options)

    return LagrangeL9Basis(
        section_provider=section_provider,
        **config,
    )


def _section_gauss_minimum(basis) -> int:
    """Reserve the 3-point rule appropriate to quadratic L9 products."""
    if not isinstance(basis, LagrangeL9Basis):
        raise TypeError("lagrangeL9 received an incompatible basis")
    return 3


def _longitudinal_transverse_degree(basis) -> int:
    """The present prismatic L9 basis has no explicit x dependence."""
    if not isinstance(basis, LagrangeL9Basis):
        raise TypeError("lagrangeL9 received an incompatible basis")
    return 0


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name=_PLUGIN_NAME,
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=(
            _longitudinal_transverse_degree
        ),
    )
)

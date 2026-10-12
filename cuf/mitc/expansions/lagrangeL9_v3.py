# Version: CSF-CUF Lagrange L9 transverse expansion v3 - 2026-10-10
#
# Changelog:
# - Preserves the validated v2 topology:
#     9 CSF polygons -> 81 local L9 points -> 57 global transverse points.
# - Adds the quadratic L9 shape functions in natural coordinates.
# - Adds analytical derivatives with respect to alpha and beta.
# - Adds inverse bilinear isoparametric mapping from physical (y,z) to
#   natural (alpha,beta) coordinates for each CSF quadrilateral.
# - Adds analytical physical derivatives through the inverse Jacobian.
# - Global CUF functions are evaluated piecewise on the CSF polygon domains.
# - On a shared interface, function values are checked for consistency and
#   returned once (they are NOT summed).
# - Derivatives at a shared interface are intentionally rejected because a
#   C0 L9 field can have different element-side derivatives there.
#
# Scope of v3:
#   complete scalar value() and derivative() evaluation for the assembled
#   prismatic L9 transverse basis.
#
# No CUF-core changes are required.

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
    """Assembled Lagrange-L9 transverse expansion driven by CSF polygons."""

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
                "lagrangeL9 v3 supports domain_source='csf_polygons' only"
            )
        if self._mapping != "isoparametric":
            raise ValueError(
                "lagrangeL9 v3 supports mapping='isoparametric' only"
            )
        if self._connectivity_mode != "shared_points":
            raise ValueError(
                "lagrangeL9 v3 supports connectivity='shared_points' only"
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
        self._merge_tolerance = (
            self._boundary_tolerance * self._coordinate_scale
        )

        (
            self._local_points,
            self._connectivity,
            self._global_points,
        ) = self._build_l9_topology()

        # Fast global-tau -> local occurrence lookup.
        self._occurrences_by_tau = tuple(
            point.occurrences for point in self._global_points
        )

    @property
    def order(self) -> int:
        return _L9_ORDER

    @property
    def size(self) -> int:
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
        return len(self._domains) * _LOCAL_L9_SIZE

    @property
    def global_points(self) -> tuple[L9GlobalPoint, ...]:
        return self._global_points

    @property
    def connectivity(self) -> tuple[tuple[int, ...], ...]:
        return self._connectivity

    @property
    def local_points(self) -> tuple[tuple[tuple[float, float], ...], ...]:
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
        y = float(y)
        z = float(z)

        if not math.isfinite(y) or not math.isfinite(z):
            raise ValueError("lagrangeL9 point coordinates must be finite")

        return tuple(
            domain.domain_id
            for domain in self._domains
            if self._point_in_polygon_inclusive(y, z, domain.vertices)
        )

    def locate_unique_domain(
        self,
        y: float,
        z: float,
    ) -> int | None:
        matches = self.locate_domains(y, z)

        if not matches:
            return None
        if len(matches) != 1:
            raise ValueError(
                "point lies on a shared CSF interface/vertex and therefore "
                f"belongs to multiple lagrangeL9 domains: {matches}"
            )
        return matches[0]

    def natural_coordinates(
        self,
        domain_id: int,
        y: float,
        z: float,
    ) -> tuple[float, float]:
        """Return (alpha,beta) in the selected CSF quadrilateral."""
        domain = self._domain(domain_id)
        return self._inverse_isoparametric_map(
            domain.vertices,
            float(y),
            float(z),
        )

    def local_shape_values(
        self,
        alpha: float,
        beta: float,
    ) -> tuple[float, ...]:
        return tuple(
            self._l9_shape(local_node, alpha, beta)
            for local_node in range(1, _LOCAL_L9_SIZE + 1)
        )

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """Evaluate one assembled global L9 basis function.

        The present benchmark is prismatic, so x is accepted by the common CUF
        contract but does not alter the basis.
        """
        self._global_point(tau)
        del x

        y = float(y)
        z = float(z)
        containing = self.locate_domains(y, z)

        if not containing:
            # A global FE-like shape function is zero outside the section.
            return 0.0

        candidate_values = []

        for domain_id in containing:
            local_node = self._local_node_for_tau(domain_id, tau)
            if local_node is None:
                candidate_values.append(0.0)
                continue

            alpha, beta = self.natural_coordinates(domain_id, y, z)
            candidate_values.append(
                self._l9_shape(local_node, alpha, beta)
            )

        # On a shared interface the same assembled global function can be
        # represented from either adjacent element. It is one piecewise global
        # function, so never sum element-side values.
        reference = float(candidate_values[0])

        for other in candidate_values[1:]:
            scale = max(1.0, abs(reference), abs(float(other)))
            if not math.isclose(
                reference,
                float(other),
                rel_tol=0.0,
                abs_tol=100.0 * np.finfo(float).eps * scale,
            ):
                raise ValueError(
                    "lagrangeL9 assembled value is inconsistent across a "
                    f"shared interface at (y,z)=({y},{z}) for tau={tau}: "
                    f"{candidate_values}"
                )

        return reference

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """Evaluate one physical transverse derivative.

        Derivatives are element-side quantities for a C0 L9 field. Therefore
        an exactly shared interface is intentionally rejected in v3 rather than
        silently selecting or averaging one side.
        """
        self._global_point(tau)
        del x

        if direction not in {"y", "z"}:
            raise ValueError("direction must be 'y' or 'z'")

        y = float(y)
        z = float(z)
        containing = self.locate_domains(y, z)

        if not containing:
            return 0.0

        if len(containing) != 1:
            raise ValueError(
                "lagrangeL9 derivative is element-side dependent on a shared "
                f"CSF interface/vertex at (y,z)=({y},{z}); "
                f"matching domains={containing}"
            )

        domain_id = containing[0]
        local_node = self._local_node_for_tau(domain_id, tau)

        if local_node is None:
            return 0.0

        domain = self._domain(domain_id)
        alpha, beta = self._inverse_isoparametric_map(
            domain.vertices,
            y,
            z,
        )

        dN_da, dN_db = self._l9_shape_natural_derivatives(
            local_node,
            alpha,
            beta,
        )

        jacobian = self._mapping_jacobian(
            domain.vertices,
            alpha,
            beta,
        )

        # J maps natural coordinate increments to physical increments:
        #
        # [dy]   [dy/da  dy/db] [da]
        # [dz] = [dz/da  dz/db] [db]
        #
        # For gradients:
        # [dN/dy, dN/dz]^T = J^{-T} [dN/da, dN/db]^T
        det = float(np.linalg.det(jacobian))
        scale = max(1.0, float(np.max(np.abs(jacobian))))
        if abs(det) <= np.finfo(float).eps * scale * scale:
            raise ValueError(
                f"lagrangeL9 domain {domain_id} has singular isoparametric "
                f"Jacobian at alpha={alpha}, beta={beta}"
            )

        physical_gradient = np.linalg.solve(
            jacobian.T,
            np.asarray((dN_da, dN_db), dtype=float),
        )

        if direction == "y":
            return float(physical_gradient[0])
        return float(physical_gradient[1])

    def diagnostic_rows(self) -> tuple[dict[str, object], ...]:
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
        shared = tuple(
            point
            for point in self._global_points
            if len(point.occurrences) > 1
        )
        return {
            "domains": self.domain_count,
            "local_points": self.local_point_count,
            "global_points": self.size,
            "shared_global_points": len(shared),
            "connectivity": self._connectivity,
        }

    def interpolation_checks(self) -> dict[str, float]:
        """Return basic L9 reference interpolation residuals for diagnostics."""
        max_kronecker = 0.0
        max_partition = 0.0
        max_derivative_sum = 0.0

        for node, (alpha, beta) in enumerate(
            _L9_NATURAL_POINTS,
            start=1,
        ):
            values = np.asarray(
                self.local_shape_values(alpha, beta),
                dtype=float,
            )
            target = np.zeros(_LOCAL_L9_SIZE, dtype=float)
            target[node - 1] = 1.0
            max_kronecker = max(
                max_kronecker,
                float(np.max(np.abs(values - target))),
            )

        samples = (
            (-0.75, -0.25),
            (-0.20,  0.60),
            ( 0.00,  0.00),
            ( 0.35, -0.40),
            ( 0.80,  0.55),
        )

        for alpha, beta in samples:
            values = np.asarray(
                self.local_shape_values(alpha, beta),
                dtype=float,
            )
            derivatives = np.asarray(
                [
                    self._l9_shape_natural_derivatives(
                        local_node,
                        alpha,
                        beta,
                    )
                    for local_node in range(1, _LOCAL_L9_SIZE + 1)
                ],
                dtype=float,
            )
            max_partition = max(
                max_partition,
                abs(float(np.sum(values)) - 1.0),
            )
            max_derivative_sum = max(
                max_derivative_sum,
                abs(float(np.sum(derivatives[:, 0]))),
                abs(float(np.sum(derivatives[:, 1]))),
            )

        return {
            "kronecker_max_abs": max_kronecker,
            "partition_unity_max_abs": max_partition,
            "derivative_sum_max_abs": max_derivative_sum,
        }

    # ------------------------------------------------------------------
    # L9 reference interpolation
    # ------------------------------------------------------------------

    @staticmethod
    def _quadratic_lagrange_1d(
        coordinate: float,
        node_coordinate: float,
    ) -> tuple[float, float]:
        """Return quadratic 1-D Lagrange value and derivative.

        The reference nodes are -1, 0, +1.
        """
        q = float(coordinate)
        qn = float(node_coordinate)

        if qn == -1.0:
            return 0.5 * q * (q - 1.0), q - 0.5
        if qn == 0.0:
            return 1.0 - q * q, -2.0 * q
        if qn == 1.0:
            return 0.5 * q * (q + 1.0), q + 0.5

        raise ValueError(
            "L9 reference node coordinate must be -1, 0, or +1"
        )

    @classmethod
    def _l9_shape(
        cls,
        local_node: int,
        alpha: float,
        beta: float,
    ) -> float:
        if not 1 <= int(local_node) <= _LOCAL_L9_SIZE:
            raise IndexError(
                f"local L9 node must be in 1..9, got {local_node}"
            )

        alpha_node, beta_node = _L9_NATURAL_POINTS[int(local_node) - 1]
        la, _ = cls._quadratic_lagrange_1d(alpha, alpha_node)
        lb, _ = cls._quadratic_lagrange_1d(beta, beta_node)
        return float(la * lb)

    @classmethod
    def _l9_shape_natural_derivatives(
        cls,
        local_node: int,
        alpha: float,
        beta: float,
    ) -> tuple[float, float]:
        if not 1 <= int(local_node) <= _LOCAL_L9_SIZE:
            raise IndexError(
                f"local L9 node must be in 1..9, got {local_node}"
            )

        alpha_node, beta_node = _L9_NATURAL_POINTS[int(local_node) - 1]
        la, dla = cls._quadratic_lagrange_1d(alpha, alpha_node)
        lb, dlb = cls._quadratic_lagrange_1d(beta, beta_node)

        return float(dla * lb), float(la * dlb)

    # ------------------------------------------------------------------
    # Isoparametric mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _corner_shape_data(
        alpha: float,
        beta: float,
    ):
        a = float(alpha)
        b = float(beta)

        N = np.asarray(
            (
                0.25 * (1.0 - a) * (1.0 - b),
                0.25 * (1.0 + a) * (1.0 - b),
                0.25 * (1.0 + a) * (1.0 + b),
                0.25 * (1.0 - a) * (1.0 + b),
            ),
            dtype=float,
        )

        dN_da = np.asarray(
            (
                -0.25 * (1.0 - b),
                 0.25 * (1.0 - b),
                 0.25 * (1.0 + b),
                -0.25 * (1.0 + b),
            ),
            dtype=float,
        )

        dN_db = np.asarray(
            (
                -0.25 * (1.0 - a),
                -0.25 * (1.0 + a),
                 0.25 * (1.0 + a),
                 0.25 * (1.0 - a),
            ),
            dtype=float,
        )

        return N, dN_da, dN_db

    @classmethod
    def _map_reference_to_physical(
        cls,
        vertices: tuple[tuple[float, float], ...],
        alpha: float,
        beta: float,
    ) -> tuple[float, float]:
        if len(vertices) != 4:
            raise ValueError(
                "L9 isoparametric mapping requires four vertices"
            )

        coords = np.asarray(vertices, dtype=float)
        N, _, _ = cls._corner_shape_data(alpha, beta)
        physical = N @ coords
        return float(physical[0]), float(physical[1])

    @classmethod
    def _mapping_jacobian(
        cls,
        vertices: tuple[tuple[float, float], ...],
        alpha: float,
        beta: float,
    ) -> np.ndarray:
        coords = np.asarray(vertices, dtype=float)
        _, dN_da, dN_db = cls._corner_shape_data(alpha, beta)

        return np.asarray(
            (
                (
                    float(dN_da @ coords[:, 0]),
                    float(dN_db @ coords[:, 0]),
                ),
                (
                    float(dN_da @ coords[:, 1]),
                    float(dN_db @ coords[:, 1]),
                ),
            ),
            dtype=float,
        )

    def _inverse_isoparametric_map(
        self,
        vertices: tuple[tuple[float, float], ...],
        y: float,
        z: float,
    ) -> tuple[float, float]:
        """Invert the bilinear quadrilateral map by Newton iteration."""
        target = np.asarray((float(y), float(z)), dtype=float)

        # For the current rectangles/parallelograms the center is an excellent
        # initial guess. It also provides a stable start for a general convex
        # bilinear quadrilateral.
        natural = np.asarray((0.0, 0.0), dtype=float)

        tolerance = max(
            1.0e-13 * self._coordinate_scale,
            10.0 * np.finfo(float).eps * self._coordinate_scale,
        )

        for _ in range(20):
            mapped = np.asarray(
                self._map_reference_to_physical(
                    vertices,
                    natural[0],
                    natural[1],
                ),
                dtype=float,
            )
            residual = mapped - target

            if float(np.linalg.norm(residual, ord=np.inf)) <= tolerance:
                return float(natural[0]), float(natural[1])

            jacobian = self._mapping_jacobian(
                vertices,
                natural[0],
                natural[1],
            )

            det = float(np.linalg.det(jacobian))
            scale = max(1.0, float(np.max(np.abs(jacobian))))
            if abs(det) <= np.finfo(float).eps * scale * scale:
                raise ValueError(
                    "lagrangeL9 encountered a singular isoparametric mapping"
                )

            delta = np.linalg.solve(jacobian, residual)
            natural -= delta

            if not np.all(np.isfinite(natural)):
                raise ValueError(
                    "lagrangeL9 inverse isoparametric mapping became non-finite"
                )

        mapped = np.asarray(
            self._map_reference_to_physical(
                vertices,
                natural[0],
                natural[1],
            ),
            dtype=float,
        )
        residual = mapped - target

        if float(np.linalg.norm(residual, ord=np.inf)) > tolerance:
            raise ValueError(
                "lagrangeL9 inverse isoparametric mapping did not converge "
                f"for physical point (y,z)=({y},{z}); residual={residual.tolist()}"
            )

        return float(natural[0]), float(natural[1])

    # ------------------------------------------------------------------
    # Assembled topology
    # ------------------------------------------------------------------

    def _build_l9_topology(self):
        local_points = []
        connectivity = []

        global_coords: list[tuple[float, float]] = []
        global_occurrences: list[list[tuple[int, int]]] = []

        for domain in self._domains:
            points = tuple(
                self._map_reference_to_physical(
                    domain.vertices,
                    alpha,
                    beta,
                )
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

    def _local_node_for_tau(
        self,
        domain_id: int,
        tau: int,
    ) -> int | None:
        connectivity = self._connectivity[int(domain_id) - 1]
        try:
            return connectivity.index(int(tau)) + 1
        except ValueError:
            return None

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

    def _global_point(self, tau: int) -> L9GlobalPoint:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")
        if not 1 <= tau <= self.size:
            raise IndexError(
                f"tau must be in 1..{self.size}, got {tau}"
            )
        return self._global_points[tau - 1]

    def _domain(self, domain_id: int) -> L9Domain:
        if not isinstance(domain_id, int):
            raise TypeError("domain_id must be an integer")
        if not 1 <= domain_id <= len(self._domains):
            raise IndexError(
                f"domain_id must be in 1..{len(self._domains)}, got {domain_id}"
            )
        return self._domains[domain_id - 1]

    # ------------------------------------------------------------------
    # CSF geometry
    # ------------------------------------------------------------------

    def _read_domains(self, x: float) -> tuple[L9Domain, ...]:
        raw_domains = tuple(self._section_provider.domains(float(x)))
        result = []

        for raw in raw_domains:
            domain_id = int(raw.domain_id)

            if getattr(raw, "excluded_vertices", ()):
                raise ValueError(
                    "lagrangeL9 v3 does not support nested/excluded CSF domains; "
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

                if not np.allclose(
                    ref,
                    cur,
                    rtol=0.0,
                    atol=atol,
                ):
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
                y_cross = (
                    (yj - yi) * (z - zi) / (zj - zi)
                    + yi
                )
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
        "domain_source": str(
            options.get("domain_source", "csf_polygons")
        ),
        "mapping": str(
            options.get("mapping", "isoparametric")
        ),
        "connectivity": str(
            options.get("connectivity", "shared_points")
        ),
        "boundary_tolerance": float(
            options.get("boundary_tolerance", 1.0e-10)
        ),
        "require_prismatic": bool(
            options.get("require_prismatic", True)
        ),
    }


def _build(
    *,
    order,
    section_provider,
    continuous_section_field,
    options,
):
    """Construct the Lagrange-L9 expansion, v3 stage."""
    del continuous_section_field

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
    """Three Gauss points integrate quartic products on straight L9 domains."""
    if not isinstance(basis, LagrangeL9Basis):
        raise TypeError(
            "lagrangeL9 received an incompatible basis"
        )
    return 3


def _longitudinal_transverse_degree(basis) -> int:
    """The present prismatic L9 basis has no explicit x dependence."""
    if not isinstance(basis, LagrangeL9Basis):
        raise TypeError(
            "lagrangeL9 received an incompatible basis"
        )
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

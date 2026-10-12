# Version: CSF-CUF Lagrange L9 transverse expansion v1 - 2026-10-10
#
# Changelog:
# - Added the definitive "lagrangeL9" transverse-expansion plugin shell.
# - Reads the transverse domains directly from SectionProvider.
# - Requires a prismatic CSF section for the present benchmark.
# - Validates that every CSF domain is a four-vertex quadrilateral.
# - Adds deterministic inclusive point-in-polygon detection.
# - Preserves multiple matches on shared edges/vertices for later L9 assembly.
# - Stores the final expansion options that will be used by later versions.
# - L9 shape functions and derivatives are intentionally NOT implemented yet.
#
# Scope of v1:
#   geometry/domain validation only.
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


class LagrangeL9Basis(CUFBasis):
    """Lagrange-L9 transverse expansion driven by CSF polygon domains.

    Version 1 implements only the geometric foundation of the final expansion.

    Each CSF polygon is interpreted as one future L9 transverse element.
    The final global L9 connectivity is intentionally not built in this version.
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
        self._connectivity = str(connectivity)
        self._boundary_tolerance = float(boundary_tolerance)
        self._require_prismatic = bool(require_prismatic)

        if self._domain_source != "csf_polygons":
            raise ValueError(
                "lagrangeL9 v1 supports domain_source='csf_polygons' only"
            )
        if self._mapping != "isoparametric":
            raise ValueError(
                "lagrangeL9 v1 supports mapping='isoparametric' only"
            )
        if self._connectivity != "shared_points":
            raise ValueError(
                "lagrangeL9 v1 supports connectivity='shared_points' only"
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

    @property
    def order(self) -> int:
        """Polynomial interpolation order of an L9 element."""
        return _L9_ORDER

    @property
    def size(self) -> int:
        """Provisional local count; global shared-point assembly comes later.

        This value is intentionally NOT a valid final CUF basis size.
        It exists only so the object has a complete diagnostic identity in v1.
        Solver evaluation is blocked by value()/derivative().
        """
        return len(self._domains) * _LOCAL_L9_SIZE

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
    def options(self) -> dict[str, object]:
        """Return the normalized configuration retained by the expansion."""
        return {
            "domain_source": self._domain_source,
            "mapping": self._mapping,
            "connectivity": self._connectivity,
            "boundary_tolerance": self._boundary_tolerance,
            "require_prismatic": self._require_prismatic,
        }

    def definition(self, tau: int):
        """No global L9 tau definition exists yet in v1."""
        self._validate_provisional_tau(tau)
        domain_index = (tau - 1) // _LOCAL_L9_SIZE
        local_index = (tau - 1) % _LOCAL_L9_SIZE + 1
        return (
            "UNASSEMBLED_L9",
            self._domains[domain_index].domain_id,
            local_index,
        )

    def locate_domains(
        self,
        y: float,
        z: float,
    ) -> tuple[int, ...]:
        """Return all CSF domain ids containing the physical point.

        The test is inclusive of polygon boundaries.

        Therefore:
        - an interior point normally returns one domain id;
        - a point on a shared edge may return two ids;
        - a shared vertex may return more than two ids;
        - a point outside the section returns an empty tuple.

        Keeping all matches is intentional. Later L9 connectivity needs to know
        when a physical point belongs to more than one transverse element.
        """
        y = float(y)
        z = float(z)

        if not math.isfinite(y) or not math.isfinite(z):
            raise ValueError("lagrangeL9 point coordinates must be finite")

        matches = [
            domain.domain_id
            for domain in self._domains
            if self._point_in_polygon_inclusive(
                y,
                z,
                domain.vertices,
            )
        ]
        return tuple(matches)

    def locate_unique_domain(
        self,
        y: float,
        z: float,
    ) -> int | None:
        """Return the unique containing domain, None outside, error on interfaces."""
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
        """L9 evaluation is deliberately unavailable in v1."""
        self._validate_provisional_tau(tau)
        del y, z, x
        raise NotImplementedError(
            "lagrangeL9 v1 validates CSF domains and point location only; "
            "L9 shape-function evaluation will be added in the next step"
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
        """L9 derivatives are deliberately unavailable in v1."""
        self._validate_provisional_tau(tau)
        if direction not in {"y", "z"}:
            raise ValueError("direction must be 'y' or 'z'")
        del y, z, x
        raise NotImplementedError(
            "lagrangeL9 v1 validates CSF domains and point location only; "
            "L9 derivatives will be added after the local mapping is validated"
        )

    def diagnostic_rows(self) -> tuple[dict[str, object], ...]:
        """Return compact domain information useful for step-by-step tests."""
        rows = []
        for domain in self._domains:
            y_min, y_max, z_min, z_max = domain.bounds
            rows.append(
                {
                    "domain_id": domain.domain_id,
                    "name": domain.name,
                    "vertices": domain.vertices,
                    "bounds": (y_min, y_max, z_min, z_max),
                }
            )
        return tuple(rows)

    def _read_domains(self, x: float) -> tuple[L9Domain, ...]:
        raw_domains = tuple(self._section_provider.domains(float(x)))
        result = []

        for raw in raw_domains:
            domain_id = int(raw.domain_id)

            if getattr(raw, "excluded_vertices", ()):
                raise ValueError(
                    "lagrangeL9 v1 does not support nested/excluded CSF domains; "
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

            if self._polygon_signed_area(vertices) == 0.0:
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

    def _validate_provisional_tau(self, tau: int) -> None:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")
        if not 1 <= tau <= self.size:
            raise IndexError(
                f"tau must be in 1..{self.size}, got {tau}"
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

        # Boundary first, so shared interfaces are intentionally detected
        # by every adjacent polygon.
        for index, a in enumerate(vertices):
            b = vertices[(index + 1) % len(vertices)]
            if self._point_on_segment(y, z, a, b, tol):
                return True

        # Standard ray crossing for the strict interior.
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
    """Construct the definitive Lagrange-L9 expansion object, v1 stage."""
    del continuous_section_field  # Available by contract; not needed in v1.

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
    """Return the L9 minimum reserved for the completed quadratic basis.

    The full numerical verification belongs to the later shape-function step.
    No CUF solution can reach this callback successfully in v1 because
    value()/derivative() intentionally stop first if evaluation is attempted.
    """
    if not isinstance(basis, LagrangeL9Basis):
        raise TypeError(
            "lagrangeL9 received an incompatible basis"
        )
    return 3


def _longitudinal_transverse_degree(basis) -> int:
    """Prismatic L9 basis has no explicit longitudinal dependence."""
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

# Version: CSF-CUF uniform physical-surface load adapter v1.2 - 2026-09-03
# Changelog: v1.2 uses accurately rounded surface-quadrature summation and documents the FEM3D pointwise axial gauge; v1.1 resolves polygon identity through the public CSF entity API; v1.0 added the adapter.
"""
Uniform physical-surface load adapter for CSF-CUF.

Purpose
-------
This module applies a spatially uniform traction in the global ``z`` direction
to one physical lateral surface of a CSF beam model.  The traction magnitude is
specified per unit of *real surface area*.  It is not specified per unit of
projected area and it is not first converted into a line load.

The adapter is deliberately separate from ``bottom_surface_halfwave.py``.
Consequently, the existing validated half-wave adapter is not modified and
existing problem files retain their original behaviour.


User interface
--------------
The problem YAML has the following form::

    model:
      csf_yaml: ../models/model.yaml

    problem:
      type: uniform_surface_load

      surface:
        polygon_name: web
        edge_start_point_id: 0

      components:
        z: -1.0

``polygon_name`` identifies one CSF polygon.  ``edge_start_point_id`` is the
zero-based index of the first vertex of the loaded polygon edge.  The second
vertex is the next polygon vertex, using cyclic polygon ordering.  Stable CSF
topology supplies the homologous edge in every other section; the adapter does
not reproduce or second-guess that CSF responsibility.

Version 1 accepts exactly one signed component, ``components.z``.  Its units
are force per unit of physical surface area in the consistent unit system used
by the model.  A positive value acts towards global ``+z`` and a negative value
acts towards global ``-z``.  Keys ``x`` and ``y`` are intentionally rejected by
this version with an explicit error.  Keeping the ``components`` mapping in the
interface permits those directions to be added later without changing the YAML
structure.


Supported surface geometry
--------------------------
The first implementation supports a surface bounded by a horizontal straight
edge in end section S0 and its homologous horizontal straight edge in end
section S1.  Here "horizontal" means constant global transverse coordinate
``z`` along each edge, and therefore an edge parallel to global ``y``.

The two end edges may:

* have different lengths;
* have different transverse ``y`` positions; and
* lie at different global ``z`` elevations.

Different end elevations produce the intended surface inclination in the
longitudinal ``x-z`` plane.  Because both end edges are parallel to global
``y``, they define a planar ruled surface even when their lengths differ.

An unsupported non-horizontal edge is never silently projected or replaced by
another edge.  Construction stops with an error that reports both end-section
edge elevations and explains the current geometric limitation.


Physical measure and weak form
------------------------------
Let the selected edge at longitudinal coordinate ``x`` be parameterised by

    y(x, eta) = y_mid(x) + h(x) * eta,     eta in [-1, 1],
    z(x, eta) = z_edge(x),

where ``h`` is half the physical edge width.  Since the end edges may lie at
different elevations, define the constant longitudinal slope

    slope_z = (z_S1 - z_S0) / (x1 - x0).

The real surface measure factorises exactly as

    dGamma = sqrt(1 + slope_z**2) * h(x) * d_eta * dx.

For CUF expansion function ``F_tau``, the generalized load per unit global
longitudinal coordinate is therefore

    q_tau,z(x)
        = p_z * sqrt(1 + slope_z**2)
              * integral[-1,1] F_tau(y(x,eta), z_edge(x)) h(x) d_eta.

The standard solver subsequently forms

    f_i,tau,z = integral[x0,x1] N_i(x) q_tau,z(x) dx.

This is exactly the physical virtual-work term

    delta W_ext = integral[Gamma] p_z * delta u_z dGamma.

No local normal/tangential coefficients are introduced and no artificial
global ``x`` load is added.  On an inclined surface the same global traction
has a non-zero local tangential-axial projection.  That local projection is
already contained in the coordinate-invariant virtual work above.  The global
resultant remains parallel to global ``z``.


Quadrature
----------
The transverse surface integration order is selected internally.  If the CUF
expansion order is ``N``, restriction of a degree-``N`` polynomial expansion to
the supported straight edge has degree at most ``N`` in ``eta``.  An
``n``-point Gauss-Legendre rule is exact through degree ``2*n - 1``; hence the
minimum transverse number of points is

    n_eta = ceil((N + 1) / 2).

No surface quadrature parameter is exposed in the YAML.

Longitudinal integration remains the responsibility of the standard CUF
solver.  Its stiffness-driven quadrature requirement is at least as demanding
as this linear load vector for the currently supported polynomial expansion
families.  The load field returned here therefore participates in the ordinary
element-by-element longitudinal integration without introducing a second or
competing longitudinal integrator.


Constraints
-----------
For direct comparison with the reference FEM3D model, this adapter uses the
same support conditions and the same pointwise axial anchor:

* global ``y`` and ``z`` CUF amplitudes are fixed at both beam ends;
* the remaining global ``x`` rigid translation is removed by imposing
  ``u_x(0, 0, 0) = 0``.

The axial condition is a gauge fixing only.  It selects the same rigid-body
reference used by the FEM3D anchor node and does not alter the load
formulation.


Future extension
----------------
The YAML surface identifier is already suitable for a general polygon edge.
A future version may support non-horizontal or warped ruled surfaces by
replacing only the internal surface geometry and Jacobian evaluation.  Existing
``surface`` and ``components`` mappings need not change.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.problem.problem import GeneralizedLongitudinalLoad, ScalarLoadField


PROBLEM_TYPE = "uniform_surface"


def _finite_float(value: Any, *, path: str) -> float:
    """Convert one YAML scalar to a finite float and report its full path."""

    # ``bool`` is a subclass of ``int`` in Python, but accepting ``true`` as a
    # physical traction would hide a YAML authoring error.  Reject it before
    # applying the ordinary numerical conversion.
    if isinstance(value, bool):
        raise TypeError(f"{path} must be a finite number, got {value!r}")

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"{path} must be a finite number, got {value!r}"
        ) from exc

    if not math.isfinite(result):
        raise ValueError(f"{path} must be finite, got {value!r}")

    return result


def _require_mapping(value: Any, *, path: str) -> Mapping[str, Any]:
    """Require a YAML mapping while keeping validation errors user-facing."""

    if not isinstance(value, Mapping):
        raise TypeError(f"{path} must be a YAML mapping")
    return value


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    *,
    allowed: set[str],
    path: str,
) -> None:
    """Reject misspelled or not-yet-supported YAML options explicitly."""

    unknown = sorted(str(key) for key in mapping if key not in allowed)
    if unknown:
        raise ValueError(
            f"{path} contains unsupported key(s): {', '.join(unknown)}; "
            f"allowed: {', '.join(sorted(allowed))}"
        )


@dataclass(frozen=True)
class SurfaceSelector:
    """Stable user-facing identifier of one CSF polygon edge."""

    polygon_name: str
    edge_start_point_id: int

    def __post_init__(self) -> None:
        name = str(self.polygon_name).strip()
        if not name:
            raise ValueError("problem.surface.polygon_name must not be empty")
        object.__setattr__(self, "polygon_name", name)

        # Reject True/False even though bool derives from int.
        if isinstance(self.edge_start_point_id, bool) or not isinstance(
            self.edge_start_point_id, int
        ):
            raise TypeError(
                "problem.surface.edge_start_point_id must be an integer"
            )
        if self.edge_start_point_id < 0:
            raise ValueError(
                "problem.surface.edge_start_point_id must be >= 0"
            )


@dataclass(frozen=True)
class _EdgeAtSection:
    """Two consecutive physical polygon vertices at one section."""

    x: float
    start: tuple[float, float]
    end: tuple[float, float]

    @property
    def y_start(self) -> float:
        return float(self.start[0])

    @property
    def z_start(self) -> float:
        return float(self.start[1])

    @property
    def y_end(self) -> float:
        return float(self.end[0])

    @property
    def z_end(self) -> float:
        return float(self.end[1])

    @property
    def z_midpoint(self) -> float:
        return 0.5 * (self.z_start + self.z_end)

    @property
    def width(self) -> float:
        return abs(self.y_end - self.y_start)


class HorizontalRuledSurface:
    """Resolve and evaluate the restricted physical CSF surface geometry.

    Polygon-name resolution and geometric compatibility checks are performed
    once during construction.  At runtime, only the already-resolved CSF
    domain id and stable vertex indices are used.  This honours CSF's ownership
    of polygon identity and homologous point correspondence.
    """

    def __init__(
        self,
        *,
        section_provider: Any,
        selector: SurfaceSelector,
        x0: float,
        x1: float,
    ) -> None:
        self.section_provider = section_provider
        self.selector = selector
        self.x0 = float(x0)
        self.x1 = float(x1)

        if not (math.isfinite(self.x0) and math.isfinite(self.x1)):
            raise ValueError("CSF longitudinal endpoints must be finite")
        if self.x1 <= self.x0:
            raise ValueError(
                "CSF longitudinal domain must satisfy x1 > x0; "
                f"got x0={self.x0!r}, x1={self.x1!r}"
            )

        # Resolve the stable CSF polygon index once from the user-facing name.
        # CSF owns and guarantees polygon-name uniqueness, so the adapter does
        # not repeat a duplicate-name topology validation.
        self.domain_id = self._domain_id_from_name(self.x0)

        domain_s0 = self.section_provider.domain(self.x0, self.domain_id)
        vertex_count = len(domain_s0.vertices)
        if selector.edge_start_point_id >= vertex_count:
            raise IndexError(
                "problem.surface.edge_start_point_id is outside polygon "
                f"{selector.polygon_name!r}: got "
                f"{selector.edge_start_point_id}, valid range is "
                f"0..{vertex_count - 1}"
            )

        self.start_index = int(selector.edge_start_point_id)
        self.end_index = (self.start_index + 1) % vertex_count

        # CSF guarantees stable polygon topology and homologous vertex order.
        # The same two indices therefore identify the requested edge at S1 and
        # at every intermediate section.
        edge_s0 = self.edge(self.x0)
        edge_s1 = self.edge(self.x1)

        self._validate_supported_geometry(edge_s0, edge_s1)

        self.z_s0 = float(edge_s0.z_midpoint)
        self.z_s1 = float(edge_s1.z_midpoint)
        self.slope_z = (self.z_s1 - self.z_s0) / (self.x1 - self.x0)

        # dGamma/dx divided by the current transverse edge line element dy.
        # This is constant because CSF interpolates the two end elevations
        # affinely and the supported end edges are parallel to global y.
        self.inclination_factor = math.hypot(1.0, self.slope_z)

    def _domain_id_from_name(self, x: float) -> int:
        """Convert the YAML polygon name into the stable one-based domain id."""

        # The CSF inspection API is the authoritative source for polygon
        # identity.  It returns the stable zero-based index together with the
        # names declared in S0 and S1.  Runtime polygon labels are deliberately
        # ignored: no string parsing or geometric name inference is used.
        inspect_entities = getattr(
            self.section_provider,
            "inspect_section_entities",
            None,
        )
        if not callable(inspect_entities):
            raise TypeError(
                "section_provider must expose the public CSF operation "
                "inspect_section_entities(x)"
            )

        entities = inspect_entities(float(x))
        for entity in entities:
            if entity["s0_name"] == self.selector.polygon_name:
                # CSF entity indices are zero based; CUF domain ids are one
                # based.  CSF guarantees index homology between S0 and S1.
                return int(entity["idx"]) + 1

        available = [str(entity["s0_name"]) for entity in entities]
        available_text = ", ".join(available) if available else "<none>"
        raise ValueError(
            "problem.surface.polygon_name does not identify a CSF polygon: "
            f"{self.selector.polygon_name!r}; available polygon names at "
            f"S0: {available_text}"
        )

    def edge(self, x: float) -> _EdgeAtSection:
        """Return the selected homologous physical edge at coordinate ``x``."""

        x = float(x)
        domain = self.section_provider.domain(x, self.domain_id)
        vertices = domain.vertices

        # Topological consistency is a CSF invariant.  Indexing directly is
        # intentional: no per-quadrature topology scan or duplicate validation
        # is performed in this adapter.
        start_raw = vertices[self.start_index]
        end_raw = vertices[self.end_index]
        start = (float(start_raw[0]), float(start_raw[1]))
        end = (float(end_raw[0]), float(end_raw[1]))

        if not all(math.isfinite(value) for value in (*start, *end)):
            raise ValueError(
                "CSF returned non-finite coordinates for loaded edge "
                f"{self.selector.polygon_name!r}:"
                f"{self.start_index} at x={x}"
            )

        return _EdgeAtSection(x=x, start=start, end=end)

    @staticmethod
    def _horizontal_tolerance(*edges: _EdgeAtSection) -> float:
        """Return a scale-aware absolute tolerance for a geometric zero."""

        scale = max(
            1.0,
            *(
                abs(value)
                for edge in edges
                for value in (
                    edge.y_start,
                    edge.z_start,
                    edge.y_end,
                    edge.z_end,
                )
            ),
        )
        return 1.0e-10 * scale

    def _validate_supported_geometry(
        self,
        edge_s0: _EdgeAtSection,
        edge_s1: _EdgeAtSection,
    ) -> None:
        """Reject surfaces outside the intentionally narrow v1 geometry."""

        tolerance = self._horizontal_tolerance(edge_s0, edge_s1)
        dz_s0 = edge_s0.z_end - edge_s0.z_start
        dz_s1 = edge_s1.z_end - edge_s1.z_start

        horizontal_s0 = abs(dz_s0) <= tolerance
        horizontal_s1 = abs(dz_s1) <= tolerance
        if horizontal_s0 and horizontal_s1:
            return

        raise ValueError(
            "Unsupported loaded surface geometry for problem.type "
            f"{PROBLEM_TYPE!r}. Polygon {self.selector.polygon_name!r}, edge "
            f"starting at point id {self.selector.edge_start_point_id}, must "
            "be horizontal (constant global z) in both CSF end sections. "
            f"Detected S0 at x={edge_s0.x:.12g}: "
            f"z_start={edge_s0.z_start:.12g}, "
            f"z_end={edge_s0.z_end:.12g}, delta_z={dz_s0:.12g}; "
            f"S1 at x={edge_s1.x:.12g}: "
            f"z_start={edge_s1.z_start:.12g}, "
            f"z_end={edge_s1.z_end:.12g}, delta_z={dz_s1:.12g}. "
            "Different elevations between S0 and S1 are supported; "
            "non-horizontal section edges are not supported by this adapter "
            "version. The geometry was not projected or modified."
        )


class UniformPhysicalSurfaceProjector:
    """Project the uniform global-z traction onto all active CUF functions."""

    def __init__(
        self,
        *,
        surface: HorizontalRuledSurface,
        basis: Any,
        z_component: float,
    ) -> None:
        self.surface = surface
        self.basis = basis
        self.z_component = float(z_component)

        if not math.isfinite(self.z_component):
            raise ValueError("problem.components.z must be finite")

        order = getattr(basis, "order", None)
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise TypeError(
                "the active CUF basis must expose a non-negative integer order"
            )

        # ceil((N + 1) / 2), written with integer arithmetic.  This is the
        # minimum Gauss-Legendre rule exact for a degree-N polynomial along the
        # supported straight transverse edge.
        self.transverse_gauss_order = max(1, (int(order) + 2) // 2)
        points, weights = np.polynomial.legendre.leggauss(
            self.transverse_gauss_order
        )
        self._points = np.asarray(points, dtype=float)
        self._weights = np.asarray(weights, dtype=float)
        self._cache: dict[float, np.ndarray] = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        """Return ``q_tau,z(x)`` for every one-based transverse index tau."""

        x = float(x)
        cached = self._cache.get(x)
        if cached is not None:
            return cached

        edge = self.surface.edge(x)
        midpoint_y = 0.5 * (edge.y_start + edge.y_end)
        half_width = 0.5 * edge.width
        z_edge = edge.z_midpoint

        basis_size = int(self.basis.size)

        # Store every weighted Gauss contribution before reducing the
        # quadrature.  A direct repeated ``values += contribution`` reduction
        # accumulates round-off in traversal order.  On a surface symmetric
        # about y=0, that can leave tiny non-zero generalized loads for basis
        # functions whose exact integral is zero.  High-order systems may
        # amplify those symmetry-breaking residuals.
        #
        # ``math.fsum`` performs an accurately rounded reduction independently
        # for every generalized component.  It changes neither the Gauss rule
        # nor the integrand and applies no tolerance or post-hoc zeroing, so it
        # remains valid for non-symmetric loaded edges as well.
        contributions = np.empty(
            (len(self._points), basis_size),
            dtype=float,
        )

        for row, (eta, weight) in enumerate(
            zip(self._points, self._weights)
        ):
            y = midpoint_y + half_width * float(eta)

            # Pass x through the generic basis interface.  Polynomial bases
            # with fixed scaling ignore it; a future section-aware expansion
            # may legitimately use it without requiring an adapter change.
            basis_values = np.asarray(
                [
                    self.basis.value(tau, y, z_edge, x=x)
                    for tau in range(1, basis_size + 1)
                ],
                dtype=float,
            )

            contributions[row, :] = (
                float(weight) * half_width * basis_values
            )

        values = np.fromiter(
            (
                math.fsum(
                    float(value)
                    for value in contributions[:, column]
                )
                for column in range(basis_size)
            ),
            dtype=float,
            count=basis_size,
        )

        # The line integral above contains the physical current edge width.
        # Multiplication by the inclination factor converts dy*dx into the real
        # lateral-surface measure dGamma.  No projected-area convention enters
        # this calculation.
        values *= self.z_component * self.surface.inclination_factor

        if not np.all(np.isfinite(values)):
            raise ValueError(
                "uniform surface projection produced a non-finite generalized "
                f"load vector at x={x}"
            )

        values.setflags(write=False)
        self._cache[x] = values
        return values


class _ModeSurfaceLoadField(ScalarLoadField):
    """Expose one tau entry through the scalar load-field solver contract."""

    def __init__(self, projector: UniformPhysicalSurfaceProjector, tau: int):
        self.projector = projector
        self.tau = int(tau)

    def value(self, x: float) -> float:
        return float(
            self.projector.generalized_vector(float(x))[self.tau - 1]
        )


class UniformSurfaceLoadProblem:
    """Complete CUF problem using the new uniform physical-surface load."""

    def __init__(
        self,
        *,
        selector: SurfaceSelector,
        z_component: float,
    ) -> None:
        self.selector = selector
        self.z_component = float(z_component)
        self._surface: HorizontalRuledSurface | None = None

    def build_loads(
        self,
        *,
        section_provider: Any,
        basis: Any,
        x0: float,
        x1: float,
    ):
        """Create one global-z generalized load for every CUF term tau."""

        surface = HorizontalRuledSurface(
            section_provider=section_provider,
            selector=self.selector,
            x0=float(x0),
            x1=float(x1),
        )
        # Retain the resolved geometry so optional post-processing reuses the
        # same one-time polygon lookup and end-section compatibility check.
        self._surface = surface
        projector = UniformPhysicalSurfaceProjector(
            surface=surface,
            basis=basis,
            z_component=self.z_component,
        )

        loads = tuple(
            GeneralizedLongitudinalLoad(
                tau=tau,
                component="z",
                field=_ModeSurfaceLoadField(projector, tau),
            )
            for tau in range(1, int(basis.size) + 1)
        )

        return loads, projector

    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
        """Apply the bending supports and the FEM3D pointwise axial anchor.

        Global y and z amplitudes are fixed at both longitudinal ends.  The
        remaining rigid global-x translation is removed with the same anchor
        used by the reference FEM3D model: ``u_x(0, 0, 0) = 0``.
        """

        layout = assembled.dof_layout
        row_count = 4 * int(basis.size) + 1
        matrix = np.zeros((row_count, layout.total_dofs), dtype=float)
        rhs = np.zeros(row_count, dtype=float)
        row = 0

        # Fix every transverse CUF amplitude (global y and z components) at
        # both longitudinal ends.  Component numbering follows the solver's
        # established convention: 0=x, 1=y, 2=z.
        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, int(basis.size) + 1):
                    matrix[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=component,
                        ),
                    ] = 1.0
                    row += 1

        # The end supports leave one rigid global-x translation.  Match the
        # FEM3D reference exactly by anchoring the physical displacement at the
        # start section and at the section point (y, z) = (0, 0):
        #
        #     u_x(x=0, y=0, z=0) = 0.
        #
        # At the first longitudinal FE node, the physical CUF displacement is
        # the section-basis expansion sum_tau F_tau(0, 0) * q_x,tau.
        axial_anchor_factors = np.asarray(
            [
                basis.value(
                    tau,
                    0.0,
                    0.0,
                    x=float(mesh.x_start),
                )
                for tau in range(1, int(basis.size) + 1)
            ],
            dtype=float,
        )

        start_node = 0
        for tau, factor in enumerate(axial_anchor_factors, start=1):
            matrix[
                row,
                layout.index(
                    node=start_node,
                    tau=tau,
                    component=0,
                ),
            ] = float(factor)

        row += 1
        if row != row_count:
            raise RuntimeError("internal constraint-row count mismatch")

        return LinearConstraintSystem(
            matrix=matrix,
            rhs=rhs,
            constraints=tuple(None for _ in range(row_count)),
        )

    def tracked_points(self, section_provider: Any, x: float):
        """Return the two selected edge vertices for standard post-processing."""

        # The normal solver path has already constructed and validated the
        # surface in build_loads().  The fallback keeps this public method
        # usable in isolation without forcing repeated work in normal runs.
        surface = self._surface
        if surface is None:
            x0, x1 = map(float, section_provider.longitudinal_domain())
            surface = HorizontalRuledSurface(
                section_provider=section_provider,
                selector=self.selector,
                x0=x0,
                x1=x1,
            )
            self._surface = surface
        edge = surface.edge(float(x))
        return (
            ("loaded_edge_start", edge.y_start, edge.z_start),
            ("loaded_edge_end", edge.y_end, edge.z_end),
        )


def _parse_surface(options: Mapping[str, Any]) -> SurfaceSelector:
    """Parse the stable two-field physical-surface selector."""

    if "surface" not in options:
        raise ValueError("problem.surface is required")
    surface = _require_mapping(options["surface"], path="problem.surface")
    _reject_unknown_keys(
        surface,
        allowed={"polygon_name", "edge_start_point_id"},
        path="problem.surface",
    )

    missing = [
        key
        for key in ("polygon_name", "edge_start_point_id")
        if key not in surface
    ]
    if missing:
        raise ValueError(
            "problem.surface requires: polygon_name, edge_start_point_id; "
            f"missing: {', '.join(missing)}"
        )

    return SurfaceSelector(
        polygon_name=surface["polygon_name"],
        edge_start_point_id=surface["edge_start_point_id"],
    )


def _parse_z_component(options: Mapping[str, Any]) -> float:
    """Parse the only global traction component supported by version 1."""

    if "components" not in options:
        raise ValueError("problem.components is required")
    components = _require_mapping(
        options["components"], path="problem.components"
    )

    unsupported = sorted(str(key) for key in components if key != "z")
    if unsupported:
        raise ValueError(
            "problem.components contains unsupported component(s): "
            f"{', '.join(unsupported)}. This adapter version accepts only "
            "the signed global-z component 'z'."
        )
    if "z" not in components:
        raise ValueError(
            "problem.components.z is required; this adapter version accepts "
            "only a signed load in the global z direction"
        )

    return _finite_float(components["z"], path="problem.components.z")


def build_problem(problem_type: str, options: dict):
    """Standard problem-adapter entry point used by the CSF-CUF loader."""

    if problem_type != PROBLEM_TYPE:
        raise ValueError(
            f"unsupported problem.type: {problem_type!r}; expected "
            f"{PROBLEM_TYPE!r}"
        )

    options = _require_mapping(options, path="problem")
    _reject_unknown_keys(
        options,
        allowed={"surface", "components"},
        path="problem",
    )

    return UniformSurfaceLoadProblem(
        selector=_parse_surface(options),
        z_component=_parse_z_component(options),
    )


__all__ = (
    "HorizontalRuledSurface",
    "PROBLEM_TYPE",
    "SurfaceSelector",
    "UniformPhysicalSurfaceProjector",
    "UniformSurfaceLoadProblem",
    "build_problem",
)

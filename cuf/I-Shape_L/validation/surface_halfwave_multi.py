"""Global-z half-wave surface traction on one or more independent CSF edges.

Self-contained physical problem adapter: it does NOT import or load another
problem/validation adapter. It uses only the normal CSF-CUF solver interfaces.

Problem YAML accepts exactly one of:

    surface:
      polygon_name: bottom_flange
      edge_start_point_id: 0

    surfaces:
      - polygon_name: bottom_flange_left
        edge_start_point_id: 0
      - polygon_name: bottom_flange_right
        edge_start_point_id: 0

and a shared signed `amplitude`, acting in the global z direction according to

    t_z(x) = amplitude * sin(pi * (x - x0) / (x1 - x0)).

Each entry is independently identified by CSF polygon name and local edge id.
No relationship of adjacency, order, elevation, flange or edge orientation is
required between entries. Repeated entries intentionally superimpose loads.

For a single edge, the load is projected onto the transverse CUF functions
using Gauss quadrature and the actual surface measure. As in the original
surface-halfwave formulation, each selected section edge must have constant
physical z at *both* beam ends. Its z elevation may change with x; the
surface measure includes that longitudinal slope. This is a limitation of the
implemented surface law, not a restriction on arrangements of multiple edges.

Transverse end conditions: u_y = u_z = 0 at both ends for all CUF amplitudes;
one mean-axial gauge removes the remaining rigid translation, evaluated with
the actual x-dependent transverse basis at (y,z) = (0,0).
"""

from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np

from csf.cuf.adapters.problem._load_vector import assemble_distributed_load_vector
from csf.cuf.problem.point_bc import LinearConstraintSystem


PROBLEM_TYPE = "surface_halfwave_transverse_supported"


def _finite_float(value: Any, *, path: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{path} must be a finite number, got {value!r}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{path} must be a finite number, got {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{path} must be finite, got {value!r}")
    return result


class SurfaceSelector:
    """Stable, local identifier of one CSF polygon edge."""

    def __init__(self, polygon_name: str, edge_start_point_id: int) -> None:
        name = str(polygon_name).strip()
        if not name:
            raise ValueError("polygon_name must not be empty")
        if isinstance(edge_start_point_id, bool) or not isinstance(
            edge_start_point_id, int
        ):
            raise TypeError("edge_start_point_id must be a non-negative integer")
        if edge_start_point_id < 0:
            raise ValueError("edge_start_point_id must be non-negative")
        self.polygon_name = name
        self.edge_start_point_id = edge_start_point_id


class _EdgeAtSection:
    """Physical coordinates of the two vertices of a selected edge."""

    def __init__(self, *, x: float, start, end):
        self.x = float(x)
        self.y_start, self.z_start = map(float, start)
        self.y_end, self.z_end = map(float, end)

    @property
    def width(self) -> float:
        return abs(self.y_end - self.y_start)

    @property
    def z_midpoint(self) -> float:
        return 0.5 * (self.z_start + self.z_end)


class HorizontalRuledSurface:
    """Resolve a CSF edge and measure its ruled physical surface.

    CSF owns polygon identity and homologous vertices between end stations;
    therefore a polygon name and two successive vertex indices suffice to
    track one physical edge throughout the longitudinal domain.
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
        if not (
            math.isfinite(self.x0)
            and math.isfinite(self.x1)
            and self.x1 > self.x0
        ):
            raise ValueError("CSF longitudinal domain must satisfy finite x1 > x0")

        inspect = getattr(section_provider, "inspect_section_entities", None)
        if not callable(inspect):
            raise TypeError("section_provider requires inspect_section_entities(x)")

        entities = inspect(self.x0)
        match = next(
            (e for e in entities if e["s0_name"] == selector.polygon_name),
            None,
        )
        if match is None:
            available = [str(e["s0_name"]) for e in entities]
            raise ValueError(
                f"Unknown CSF polygon {selector.polygon_name!r}; "
                f"available: {available}"
            )
        self.domain_id = int(match["idx"]) + 1

        n_vertices = len(section_provider.domain(self.x0, self.domain_id).vertices)
        if selector.edge_start_point_id >= n_vertices:
            raise IndexError(
                f"Edge {selector.edge_start_point_id} is outside polygon "
                f"{selector.polygon_name!r} (0..{n_vertices - 1})"
            )
        self.start_index = selector.edge_start_point_id
        self.end_index = (self.start_index + 1) % n_vertices

        edge_s0 = self.edge(self.x0)
        edge_s1 = self.edge(self.x1)
        tolerance = 1.0e-10 * max(
            1.0,
            *(
                abs(v)
                for e in (edge_s0, edge_s1)
                for v in (e.y_start, e.y_end, e.z_start, e.z_end)
            ),
        )
        if (
            abs(edge_s0.z_end - edge_s0.z_start) > tolerance
            or abs(edge_s1.z_end - edge_s1.z_start) > tolerance
        ):
            raise ValueError(
                f"Unsupported edge geometry: {selector.polygon_name!r}, "
                f"edge {selector.edge_start_point_id}. Each selected edge "
                "must be horizontal (constant global z) at both CSF end sections; "
                "different elevations between the end sections are allowed."
            )

        self.z_s0 = edge_s0.z_midpoint
        self.z_s1 = edge_s1.z_midpoint
        self.slope_z = (self.z_s1 - self.z_s0) / (self.x1 - self.x0)
        # dGamma = sqrt(1 + (dz/dx)^2) * abs(dy) * dx for this ruled surface.
        self.inclination_factor = math.hypot(1.0, self.slope_z)

    def edge(self, x: float) -> _EdgeAtSection:
        vertices = self.section_provider.domain(float(x), self.domain_id).vertices
        selected = _EdgeAtSection(
            x=x,
            start=vertices[self.start_index],
            end=vertices[self.end_index],
        )
        if not all(
            math.isfinite(v)
            for v in (
                selected.y_start,
                selected.z_start,
                selected.y_end,
                selected.z_end,
            )
        ):
            raise ValueError("CSF returned non-finite loaded-edge coordinates")
        return selected


class HalfWavePhysicalSurfaceProjector:
    """Generalized CUF global-z load for one physical ruled surface."""

    def __init__(self, *, surface: HorizontalRuledSurface, basis: Any, amplitude: float):
        self.surface = surface
        self.basis = basis
        self.amplitude = _finite_float(amplitude, path="problem.amplitude")
        order = getattr(basis, "order", None)
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise TypeError("CUF basis must expose a non-negative integer order")
        self.transverse_gauss_order = max(1, (order + 2) // 2)
        self._points, self._weights = np.polynomial.legendre.leggauss(
            self.transverse_gauss_order
        )
        self._cache: dict[float, np.ndarray] = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        x = float(x)
        if x in self._cache:
            return self._cache[x]
        edge = self.surface.edge(x)
        midpoint_y = 0.5 * (edge.y_start + edge.y_end)
        half_width = 0.5 * edge.width
        z_edge = edge.z_midpoint
        size = int(self.basis.size)
        quadrature = np.empty((len(self._points), size), dtype=float)
        for i, (eta, weight) in enumerate(zip(self._points, self._weights)):
            y = midpoint_y + half_width * float(eta)
            quadrature[i, :] = (
                float(weight)
                * half_width
                * np.asarray(
                    [
                        self.basis.value(tau, y, z_edge, x=x)
                        for tau in range(1, size + 1)
                    ],
                    dtype=float,
                )
            )
        values = np.fromiter(
            (math.fsum(float(v) for v in quadrature[:, j]) for j in range(size)),
            dtype=float,
            count=size,
        )
        L = self.surface.x1 - self.surface.x0
        phase = math.sin(math.pi * (x - self.surface.x0) / L)
        values *= self.amplitude * phase * self.surface.inclination_factor
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Non-finite projected half-wave load at x={x}")
        values.setflags(write=False)
        self._cache[x] = values
        return values


class SumOfSurfaceProjectors:
    """Add any nonempty set of selected surface contributions independently."""

    def __init__(self, projectors):
        self.projectors = tuple(projectors)
        if not self.projectors:
            raise ValueError("At least one surface projector is required")
        self.surfaces = tuple(p.surface for p in self.projectors)
        self.basis = self.projectors[0].basis
        self.amplitude = self.projectors[0].amplitude
        self.transverse_gauss_order = max(
            p.transverse_gauss_order for p in self.projectors
        )
        self._cache: dict[float, np.ndarray] = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        x = float(x)
        if x in self._cache:
            return self._cache[x]
        contributions = [p.generalized_vector(x) for p in self.projectors]
        size = len(contributions[0])
        result = np.fromiter(
            (math.fsum(float(v[j]) for v in contributions) for j in range(size)),
            dtype=float,
            count=size,
        )
        if not np.all(np.isfinite(result)):
            raise ValueError(f"Non-finite combined half-wave load at x={x}")
        result.setflags(write=False)
        self._cache[x] = result
        return result


class _ModeField:
    """Adapt one CUF generalized load to the FE integration interface."""

    def __init__(self, projector: SumOfSurfaceProjectors, tau: int):
        self.projector = projector
        self.tau = int(tau)

    def value(self, x: float) -> float:
        return float(self.projector.generalized_vector(x)[self.tau - 1])


class SurfaceHalfWaveMultipleEdges:
    """Half-wave global-z loading with transverse end supports and axial gauge."""

    def __init__(self, *, selectors, amplitude: float):
        self.selectors = tuple(selectors)
        if not self.selectors:
            raise ValueError("At least one selected edge is required")
        self.amplitude = _finite_float(amplitude, path="problem.amplitude")
        self._resolved_key = None
        self._surfaces = None

    def _resolve_surfaces(self, section_provider: Any, x0: float, x1: float):
        key = (id(section_provider), float(x0), float(x1))
        if self._surfaces is None or key != self._resolved_key:
            self._surfaces = tuple(
                HorizontalRuledSurface(
                    section_provider=section_provider,
                    selector=selector,
                    x0=float(x0),
                    x1=float(x1),
                )
                for selector in self.selectors
            )
            self._resolved_key = key
        return self._surfaces

    def build_load_vector(
        self,
        *,
        section_provider: Any,
        basis: Any,
        mesh: Any,
        dof_layout: Any,
        longitudinal_integrator: Any,
        x0: float,
        x1: float,
    ):
        surfaces = self._resolve_surfaces(section_provider, x0, x1)
        projector = SumOfSurfaceProjectors(
            HalfWavePhysicalSurfaceProjector(
                surface=surface,
                basis=basis,
                amplitude=self.amplitude,
            )
            for surface in surfaces
        )
        fields = tuple(
            _ModeField(projector, tau)
            for tau in range(1, int(basis.size) + 1)
        )
        loads = assemble_distributed_load_vector(
            mesh=mesh,
            dof_layout=dof_layout,
            longitudinal_integrator=longitudinal_integrator,
            component="z",
            fields=fields,
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
        """Suppress u_y and u_z at both beam ends and mean axial translation."""
        layout = assembled.dof_layout
        size = int(basis.size)
        row_count = 4 * size + 1
        A = np.zeros((row_count, layout.total_dofs), dtype=float)
        b = np.zeros(row_count, dtype=float)
        row = 0
        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, size + 1):
                    A[row, layout.index(node=node, tau=tau, component=component)] = 1.0
                    row += 1

        length = float(mesh.x_end - mesh.x_start)
        if not math.isfinite(length) or length <= 0.0:
            raise ValueError("Invalid longitudinal domain")
        for element in mesh.elements:
            for tau in range(1, size + 1):
                weights = longitudinal_integrator.integrate_linear(
                    element=element,
                    load=lambda x, tau=tau: basis.value(
                        tau, 0.0, 0.0, x=float(x)
                    ),
                )
                for a, node in enumerate(element.node_ids):
                    A[row, layout.index(node=node, tau=tau, component=0)] += (
                        float(weights[a]) / length
                    )
        row += 1
        if row != row_count:
            raise RuntimeError("Constraint-row count mismatch")
        return LinearConstraintSystem(
            matrix=A, rhs=b, constraints=tuple(None for _ in range(row_count))
        )

    def tracked_points(self, section_provider: Any, x: float):
        """Report true endpoints of all edges, not a manufactured union edge."""
        x0, x1 = map(float, section_provider.longitudinal_domain())
        surfaces = self._resolve_surfaces(section_provider, x0, x1)
        if len(surfaces) == 1:
            edge = surfaces[0].edge(float(x))
            return (
                ("loaded_edge_start", edge.y_start, edge.z_start),
                ("loaded_edge_end", edge.y_end, edge.z_end),
            )
        points = []
        for i, surface in enumerate(surfaces, start=1):
            edge = surface.edge(float(x))
            points.append((f"loaded_surface_{i}_start", edge.y_start, edge.z_start))
            points.append((f"loaded_surface_{i}_end", edge.y_end, edge.z_end))
        return tuple(points)


def _parse_edge(value: Any, *, path: str) -> SurfaceSelector:
    if not isinstance(value, Mapping):
        raise TypeError(f"{path} must be a YAML mapping")
    required = {"polygon_name", "edge_start_point_id"}
    missing = required - set(value)
    unknown = set(value) - required
    if missing or unknown:
        raise ValueError(
            f"{path}: missing {sorted(missing)}; unsupported {sorted(unknown)}"
        )
    return SurfaceSelector(
        polygon_name=value["polygon_name"],
        edge_start_point_id=value["edge_start_point_id"],
    )


def build_problem(problem_type: str, options: dict):
    """Build from a single `surface` or a nonempty list of `surfaces`."""
    if problem_type != PROBLEM_TYPE:
        raise ValueError(
            f"Unsupported problem.type {problem_type!r}, expected {PROBLEM_TYPE!r}"
        )
    if not isinstance(options, Mapping):
        raise TypeError("problem options must be a YAML mapping")
    unknown = set(options) - {"surface", "surfaces", "amplitude"}
    if unknown:
        raise ValueError(f"Unsupported problem keys: {sorted(unknown)}")
    if ("surface" in options) == ("surfaces" in options):
        raise ValueError("Specify exactly one of problem.surface or problem.surfaces")

    if "surface" in options:
        selectors = (_parse_edge(options["surface"], path="problem.surface"),)
    else:
        entries = options["surfaces"]
        if not isinstance(entries, list) or not entries:
            raise TypeError("problem.surfaces must be a nonempty YAML list")
        selectors = tuple(
            _parse_edge(entry, path=f"problem.surfaces[{i}]")
            for i, entry in enumerate(entries)
        )
    return SurfaceHalfWaveMultipleEdges(
        selectors=selectors,
        amplitude=_finite_float(options.get("amplitude"), path="problem.amplitude"),
    )


__all__ = (
    "PROBLEM_TYPE",
    "SurfaceSelector",
    "HorizontalRuledSurface",
    "HalfWavePhysicalSurfaceProjector",
    "SumOfSurfaceProjectors",
    "SurfaceHalfWaveMultipleEdges",
    "build_problem",
)

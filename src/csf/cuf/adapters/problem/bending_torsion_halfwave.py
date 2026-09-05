"""
CSF-CUF bending and torsion structural problem adapter.

This module provides two related static structural problem definitions for the
CSF-CUF solver:

1. Torsion by an opposite moving load pair
2. Bending by a distributed load acting on the lower physical boundary

Both problems use a sinusoidal longitudinal half-wave distribution and obtain
the current cross-sectional geometry directly from the CSF SectionProvider.
The transverse geometry is therefore evaluated at the actual longitudinal
coordinate x and may vary continuously along the beam.

TORSION
-------

The torsional problem applies two opposite physical loads at two section
vertices determined from the current CSF geometry.

At each longitudinal coordinate x:

    - the positive point is selected on the maximum-z boundary;
    - the negative point is selected on the minimum-z boundary;
    - the CUF transverse basis is evaluated at both physical points.

For each transverse expansion term tau, the generalized load is proportional to

    F_tau(y_plus, z_plus) - F_tau(y_minus, z_minus)

and is multiplied by the longitudinal half-wave

    sin(pi * (x - x0) / L).

The load points therefore follow the actual non-prismatic section rather than
being prescribed by fixed transverse coordinates.

BENDING
-------

The bending problem applies a distributed load over the complete physical
boundary lying at the minimum-z side of the current section.

The loaded boundary is reconstructed directly from the CSF polygonal domains.
For every transverse expansion term tau, the sectional load projection is

    B_tau(x) = integral_Gamma(x) F_tau(y, z) ds

where Gamma(x) is the selected physical boundary at the current longitudinal
coordinate.

The sectional projection is evaluated by Gauss quadrature over the detected
boundary segments and is multiplied by the same longitudinal half-wave

    sin(pi * (x - x0) / L).

CUF INTERFACE
-------------

The module does not construct or modify the stiffness formulation.

Its responsibility is limited to the structural problem definition:

    physical load
        ->
    projection on the active CUF transverse basis
        ->
    GeneralizedLongitudinalLoad objects

together with the constraints required by the corresponding problem.

The module uses the standard CUF problem interfaces:

    GeneralizedLongitudinalLoad
    ScalarLoadField
    LinearConstraintSystem

and exposes the standard adapter entry point:

    build_problem(problem_type, options)

The solver therefore interacts with this module only through the common
problem-adapter contract.

CSF COUPLING
------------

Geometry is never duplicated inside this module.

All physical load locations and loaded boundaries are obtained from the active
CSF SectionProvider at the requested longitudinal coordinate x. Consequently,
the same problem definition can follow a section whose dimensions change along
the beam.

Material properties are not queried here. They remain the responsibility of
the CSF constitutive description used by the CUF assembly.

SCOPE
-----

This module groups bending and torsion problems because they share the same
general architecture:

    CSF physical geometry
        +
    physical load definition
        +
    longitudinal half-wave law
        +
    projection through F_tau
        ->
    generalized CUF loads

The current implementations also contain their corresponding support and
rigid-body/gauge constraints. These constraint conventions are part of the
implemented structural problems and should not be interpreted as universal
boundary conditions for arbitrary bending or torsion analyses.

The filename identifies the bending/torsion problem family; the specific
problem to construct is selected independently through problem.type in the YAML
configuration.
"""

from __future__ import annotations

import math
import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.problem.problem import GeneralizedLongitudinalLoad, ScalarLoadField
from csf.cuf.numerics import all_vertices, transverse_bounds


def _has_vertex(section_provider, x: float, point) -> bool:
    target_y, target_z = map(float, point)
    scale = max(1.0, abs(target_y), abs(target_z))
    tol = 1.0e-10 * scale
    for y, z in all_vertices(section_provider, x):
        if math.isclose(float(y), target_y, rel_tol=0.0, abs_tol=tol) and math.isclose(
            float(z), target_z, rel_tol=0.0, abs_tol=tol
        ):
            return True
    return False


def moving_load_points(section_provider, x: float):
    """Locate the two physical CSF vertices used by the matched torsion load pair.

    The positive point is the leftmost vertex on the maximum-z boundary.
    The negative point is the rightmost vertex on the minimum-z boundary.
    This matches the FEM3D load trajectories exactly for the non-prismatic T-section.
    """
    _, _, z_min, z_max = transverse_bounds(section_provider, x)
    vertices = tuple((float(y), float(z)) for y, z in all_vertices(section_provider, x))
    scale = max(1.0, abs(float(z_min)), abs(float(z_max)))
    tol = 1.0e-10 * scale

    top_vertices = [
        (y, z) for y, z in vertices
        if math.isclose(z, float(z_max), rel_tol=0.0, abs_tol=tol)
    ]
    bottom_vertices = [
        (y, z) for y, z in vertices
        if math.isclose(z, float(z_min), rel_tol=0.0, abs_tol=tol)
    ]

    if not top_vertices:
        raise ValueError(f"no CSF vertex found on maximum-z boundary at x={x}")
    if not bottom_vertices:
        raise ValueError(f"no CSF vertex found on minimum-z boundary at x={x}")

    point_plus = min(top_vertices, key=lambda point: point[0])
    point_minus = max(bottom_vertices, key=lambda point: point[0])

    if not _has_vertex(section_provider, x, point_plus):
        raise ValueError(f"positive load point is not a CSF vertex at x={x}: {point_plus}")
    if not _has_vertex(section_provider, x, point_minus):
        raise ValueError(f"negative load point is not a CSF vertex at x={x}: {point_minus}")
    return point_plus, point_minus


class TorsionalLinePairProjector:
    def __init__(self, *, section_provider, basis, x0: float, x1: float, amplitude: float):
        self.section_provider = section_provider
        self.basis = basis
        self.x0 = float(x0)
        self.x1 = float(x1)
        self.length = self.x1 - self.x0
        self.amplitude = float(amplitude)
        self.alpha = math.pi / self.length
        self._cache = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        x = float(x)
        if x in self._cache:
            return self._cache[x]
        point_plus, point_minus = moving_load_points(self.section_provider, x)
        y_plus, z_plus = point_plus
        y_minus, z_minus = point_minus
        F_plus = np.asarray(
            [self.basis.value(tau, y_plus, z_plus) for tau in range(1, self.basis.size + 1)],
            dtype=float,
        )
        F_minus = np.asarray(
            [self.basis.value(tau, y_minus, z_minus) for tau in range(1, self.basis.size + 1)],
            dtype=float,
        )
        phase = math.sin(self.alpha * (x - self.x0))
        values = self.amplitude * phase * (F_plus - F_minus)
        self._cache[x] = values
        return values


class ModeLineLoadField(ScalarLoadField):
    def __init__(self, projector, tau: int):
        self.projector = projector
        self.tau = int(tau)

    def value(self, x: float) -> float:
        return float(self.projector.generalized_vector(float(x))[self.tau - 1])


class CarreraTorsionHalfWaveProblem:
    """
    Initial physical problem plugin used to validate the generic variable-section path.

    It defines only loading, constraints and tracked response points. Geometry
    is always queried from the CSF SectionProvider; material is never accessed.
    """

    def __init__(self, *, amplitude: float = 1.0):
        self.amplitude = float(amplitude)

    def build_loads(self, *, section_provider, basis, x0: float, x1: float):
        projector = TorsionalLinePairProjector(
            section_provider=section_provider,
            basis=basis,
            x0=x0,
            x1=x1,
            amplitude=self.amplitude,
        )
        loads = tuple(
            GeneralizedLongitudinalLoad(
                tau=tau,
                component="z",
                field=ModeLineLoadField(projector, tau),
            )
            for tau in range(1, basis.size + 1)
        )
        return loads, projector

    def build_constraints(self, *, assembled, mesh, basis, longitudinal_integrator):
        layout = assembled.dof_layout
        row_count = 4 * basis.size + 1
        A = np.zeros((row_count, layout.total_dofs), dtype=float)
        b = np.zeros(row_count, dtype=float)
        row = 0

        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, basis.size + 1):
                    A[row, layout.index(node=node, tau=tau, component=component)] = 1.0
                    row += 1

        length = float(mesh.x_end - mesh.x_start)
        axial_gauge_factors = np.asarray(
            [
                basis.value(tau, 0.0, 0.0)
                for tau in range(1, basis.size + 1)
            ],
            dtype=float,
        )

        for element in mesh.elements:
            local = longitudinal_integrator.integrate_linear(
                element=element,
                load=lambda x: 1.0,
            )
            for a, node in enumerate(element.node_ids):
                for tau, factor in enumerate(
                    axial_gauge_factors,
                    start=1,
                ):
                    A[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=0,
                        ),
                    ] += (
                        float(local[a])
                        * float(factor)
                        / length
                    )
        row += 1

        if row != row_count:
            raise RuntimeError("internal constraint-row count mismatch")

        return LinearConstraintSystem(
            matrix=A,
            rhs=b,
            constraints=tuple(None for _ in range(row_count)),
        )

    def tracked_points(self, section_provider, x: float):
        plus, minus = moving_load_points(section_provider, float(x))
        return (
            ("positive_corner", plus[0], plus[1]),
            ("negative_corner", minus[0], minus[1]),
        )



def _lowest_boundary_segments(section_provider, x: float):
    """
    Discover boundary segments on the minimum solver-z face directly from CSF.
    """
    _, _, z_min, _ = transverse_bounds(section_provider, float(x))
    tol = 1.0e-11 * max(1.0, abs(float(z_min)))
    segments = {}

    for domain in section_provider.domains(float(x)):
        vertices = tuple((float(y), float(z)) for y, z in domain.vertices)

        for index, (y0, z0) in enumerate(vertices):
            y1, z1 = vertices[(index + 1) % len(vertices)]

            if not (
                math.isclose(z0, z_min, rel_tol=0.0, abs_tol=tol)
                and math.isclose(z1, z_min, rel_tol=0.0, abs_tol=tol)
            ):
                continue

            lo = min(y0, y1)
            hi = max(y0, y1)
            if hi - lo <= tol:
                continue

            segments[(round(lo, 12), round(hi, 12))] = (lo, hi)

    if not segments:
        raise ValueError(
            f"no CSF boundary was found on the minimum-z face at x={x}"
        )

    return float(z_min), tuple(segments.values())


def _loaded_face_factors(section_provider, basis, x: float) -> np.ndarray:
    """
    B_tau(x) = integral_Gamma(x) F_tau(y,z) ds
    on the minimum-z physical boundary.
    """
    z_face, segments = _lowest_boundary_segments(
        section_provider,
        float(x),
    )

    n_gauss = max(4, (basis.order + 2) // 2)
    xi, wi = np.polynomial.legendre.leggauss(n_gauss)
    values = np.zeros(basis.size, dtype=float)

    for y0, y1 in segments:
        midpoint = 0.5 * (y0 + y1)
        jacobian = 0.5 * (y1 - y0)

        for xig, wig in zip(xi, wi):
            y = midpoint + jacobian * float(xig)
            values += (
                float(wig)
                * jacobian
                * np.asarray(
                    [
                        basis.value(tau, y, z_face)
                        for tau in range(1, basis.size + 1)
                    ],
                    dtype=float,
                )
            )

    return values


class BendingSurfaceProjector:
    """
    Carrera-Giunta Table-9 surface load projected on the CUF basis.

    Paper P_xx^(3+) acts in paper +x. Under the adopted mapping this is
    solver -z. Longitudinal variation is the m=1 sine half-wave.
    """

    def __init__(
        self,
        *,
        section_provider,
        basis,
        x0: float,
        x1: float,
        amplitude: float,
    ):
        self.section_provider = section_provider
        self.basis = basis
        self.x0 = float(x0)
        self.x1 = float(x1)
        self.length = self.x1 - self.x0
        self.amplitude = float(amplitude)
        self.alpha = math.pi / self.length
        self._cache = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        x = float(x)

        if x in self._cache:
            return self._cache[x]

        B = _loaded_face_factors(
            self.section_provider,
            self.basis,
            x,
        )

        phase = math.sin(self.alpha * (x - self.x0))

        # Paper +x -> solver -z.
        values = -self.amplitude * phase * B

        self._cache[x] = values
        return values


class ModeSurfaceLoadField(ScalarLoadField):
    def __init__(self, projector, tau: int):
        self.projector = projector
        self.tau = int(tau)

    def value(self, x: float) -> float:
        return float(
            self.projector.generalized_vector(float(x))[self.tau - 1]
        )


class CarreraBendingBottomSurfaceHalfWaveProblem:
    """
    Carrera-Giunta Table-9 bending problem.

    Geometry of the loaded surface is queried from CSF at every x.
    """

    def __init__(self, *, amplitude: float = 1.0):
        self.amplitude = float(amplitude)

    def build_loads(
        self,
        *,
        section_provider,
        basis,
        x0: float,
        x1: float,
    ):
        projector = BendingSurfaceProjector(
            section_provider=section_provider,
            basis=basis,
            x0=x0,
            x1=x1,
            amplitude=self.amplitude,
        )

        loads = tuple(
            GeneralizedLongitudinalLoad(
                tau=tau,
                component="z",
                field=ModeSurfaceLoadField(projector, tau),
            )
            for tau in range(1, basis.size + 1)
        )

        return loads, projector

    def build_constraints(
        self,
        *,
        assembled,
        mesh,
        basis,
        longitudinal_integrator,
    ):
        layout = assembled.dof_layout
        row_count = 4 * basis.size + 1
        A = np.zeros((row_count, layout.total_dofs), dtype=float)
        b = np.zeros(row_count, dtype=float)
        row = 0

        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, basis.size + 1):
                    A[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=component,
                        ),
                    ] = 1.0
                    row += 1

        length = float(mesh.x_end - mesh.x_start)
        axial_gauge_factors = np.asarray(
            [
                basis.value(tau, 0.0, 0.0)
                for tau in range(1, basis.size + 1)
            ],
            dtype=float,
        )

        for element in mesh.elements:
            local = longitudinal_integrator.integrate_linear(
                element=element,
                load=lambda x: 1.0,
            )

            for a, node in enumerate(element.node_ids):
                for tau, factor in enumerate(
                    axial_gauge_factors,
                    start=1,
                ):
                    A[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=0,
                        ),
                    ] += (
                        float(local[a])
                        * float(factor)
                        / length
                    )

        row += 1

        if row != row_count:
            raise RuntimeError("internal constraint-row count mismatch")

        return LinearConstraintSystem(
            matrix=A,
            rhs=b,
            constraints=tuple(None for _ in range(row_count)),
        )

    def tracked_points(self, section_provider, x: float):
        z_face, segments = _lowest_boundary_segments(
            section_provider,
            float(x),
        )

        points = []

        for index, (y0, y1) in enumerate(segments, start=1):
            points.append(
                (f"loaded_face_{index}_left", y0, z_face)
            )
            points.append(
                (f"loaded_face_{index}_right", y1, z_face)
            )

        return tuple(points)


def build_problem(problem_type: str, options: dict):
    amplitude = float(options.get("amplitude", 1.0))

    if problem_type == "carrera_torsion_halfwave":
        return CarreraTorsionHalfWaveProblem(amplitude=amplitude)

    if problem_type == "carrera_bending_bottom_surface_halfwave":
        return CarreraBendingBottomSurfaceHalfWaveProblem(
            amplitude=amplitude
        )

    raise ValueError(f"unsupported problem.type: {problem_type!r}")

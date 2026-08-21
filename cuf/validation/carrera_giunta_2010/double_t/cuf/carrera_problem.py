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
    """Locate the two opposite moving boundary vertices used by this problem."""
    y_min, y_max, z_min, z_max = transverse_bounds(section_provider, x)
    point_plus = (y_min, z_max)
    point_minus = (y_max, z_min)
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
        for element in mesh.elements:
            local = longitudinal_integrator.integrate_linear(
                element=element,
                load=lambda x: 1.0,
            )
            for a, node in enumerate(element.node_ids):
                A[row, layout.index(node=node, tau=1, component=0)] += float(local[a]) / length
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
    _, _, _, z_min = transverse_bounds(section_provider, float(x))
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

        for element in mesh.elements:
            local = longitudinal_integrator.integrate_linear(
                element=element,
                load=lambda x: 1.0,
            )

            for a, node in enumerate(element.node_ids):
                A[
                    row,
                    layout.index(
                        node=node,
                        tau=1,
                        component=0,
                    ),
                ] += float(local[a]) / length

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

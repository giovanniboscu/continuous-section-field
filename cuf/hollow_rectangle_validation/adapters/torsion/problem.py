# Version: CSF-CUF hollow-rectangle torsion surface-load adapter v5 - 2026-08-27
from __future__ import annotations

import math

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.problem.problem import GeneralizedLongitudinalLoad, ScalarLoadField
from csf.cuf.numerics import transverse_bounds


def _is_void_domain(domain) -> bool:
    weightabs = getattr(domain, "weightabs", None)
    return weightabs is not None and float(weightabs) == 0.0


def _outer_vertical_segments(section_provider, x: float):
    """Return material segments on the true outer y-min and y-max faces."""
    y_min, y_max, _, _ = transverse_bounds(section_provider, float(x))
    tol = 1.0e-11 * max(1.0, abs(float(y_min)), abs(float(y_max)))
    found = {-1: {}, +1: {}}

    for domain in section_provider.domains(float(x)):
        if _is_void_domain(domain):
            continue
        vertices = tuple((float(y), float(z)) for y, z in domain.vertices)
        for index, (y0, z0) in enumerate(vertices):
            y1, z1 = vertices[(index + 1) % len(vertices)]
            for sign, face_y in ((-1, y_min), (+1, y_max)):
                if not (
                    math.isclose(y0, face_y, rel_tol=0.0, abs_tol=tol)
                    and math.isclose(y1, face_y, rel_tol=0.0, abs_tol=tol)
                ):
                    continue
                lo, hi = sorted((z0, z1))
                if hi - lo > tol:
                    found[sign][(round(lo, 12), round(hi, 12))] = (lo, hi)

    if not found[-1] or not found[+1]:
        raise ValueError(f"outer vertical material faces not found at x={x}")
    return {
        -1: (float(y_min), tuple(found[-1][k] for k in sorted(found[-1]))),
        +1: (float(y_max), tuple(found[+1][k] for k in sorted(found[+1]))),
    }


def _torsion_face_factors(section_provider, basis, x: float) -> np.ndarray:
    """Project opposite z-tractions on the two outer vertical faces."""
    faces = _outer_vertical_segments(section_provider, float(x))
    n_gauss = max(4, (int(basis.order) + 2) // 2)
    xi, wi = np.polynomial.legendre.leggauss(n_gauss)
    values = np.zeros(int(basis.size), dtype=float)

    for sign, (y_face, segments) in faces.items():
        # right face: +z; left face: -z. Net force is zero, torque is positive.
        for z0, z1 in segments:
            midpoint = 0.5 * (z0 + z1)
            jacobian = 0.5 * (z1 - z0)
            for xig, wig in zip(xi, wi):
                z = midpoint + jacobian * float(xig)
                values += sign * float(wig) * jacobian * np.asarray(
                    [
                        basis.value(tau, y_face, z)
                        for tau in range(1, int(basis.size) + 1)
                    ],
                    dtype=float,
                )
    return values


class TorsionSurfaceProjector:
    def __init__(self, *, section_provider, basis, x0, x1, amplitude):
        self.section_provider = section_provider
        self.basis = basis
        self.x0 = float(x0)
        self.x1 = float(x1)
        self.length = self.x1 - self.x0
        self.amplitude = float(amplitude)
        self._cache = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        x = float(x)
        if x not in self._cache:
            phase = math.sin(math.pi * (x - self.x0) / self.length)
            self._cache[x] = (
                self.amplitude
                * phase
                * _torsion_face_factors(self.section_provider, self.basis, x)
            )
        return self._cache[x]


class ModeSurfaceLoadField(ScalarLoadField):
    def __init__(self, projector, tau: int):
        self.projector = projector
        self.tau = int(tau)

    def value(self, x: float) -> float:
        return float(self.projector.generalized_vector(float(x))[self.tau - 1])


class HollowRectangleTorsionProblem:
    def __init__(self, *, amplitude: float = 1.0):
        self.amplitude = float(amplitude)

    def build_loads(self, *, section_provider, basis, x0: float, x1: float):
        projector = TorsionSurfaceProjector(
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
            for tau in range(1, int(basis.size) + 1)
        )
        return loads, projector

    def build_constraints(self, *, assembled, mesh, basis, longitudinal_integrator):
        """Zero transverse field at both ends plus one axial gauge equation."""
        layout = assembled.dof_layout
        row_count = 4 * int(basis.size) + 1
        A = np.zeros((row_count, layout.total_dofs), dtype=float)
        b = np.zeros(row_count, dtype=float)
        row = 0
        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, int(basis.size) + 1):
                    A[row, layout.index(node=node, tau=tau, component=component)] = 1.0
                    row += 1

        length = float(mesh.x_end - mesh.x_start)
        factors = np.asarray(
            [basis.value(tau, 0.0, 0.0) for tau in range(1, int(basis.size) + 1)],
            dtype=float,
        )
        for element in mesh.elements:
            local = longitudinal_integrator.integrate_linear(element=element, load=lambda x: 1.0)
            for a, node in enumerate(element.node_ids):
                for tau, factor in enumerate(factors, start=1):
                    A[row, layout.index(node=node, tau=tau, component=0)] += (
                        float(local[a]) * float(factor) / length
                    )
        return LinearConstraintSystem(
            matrix=A,
            rhs=b,
            constraints=tuple(None for _ in range(row_count)),
        )

    def tracked_points(self, section_provider, x: float):
        faces = _outer_vertical_segments(section_provider, float(x))
        points = []
        for sign, (y_face, segments) in faces.items():
            for index, (z0, z1) in enumerate(segments, start=1):
                points.append((f"side_{sign:+d}_{index}_bottom", y_face, z0))
                points.append((f"side_{sign:+d}_{index}_top", y_face, z1))
        return tuple(points)


def build_problem(problem_type: str, options: dict):
    if problem_type != "hollow_rectangle_torsion_side_surface_halfwave":
        raise ValueError(f"unsupported problem.type: {problem_type!r}")
    return HollowRectangleTorsionProblem(
        amplitude=float(options.get("amplitude", 1.0))
    )

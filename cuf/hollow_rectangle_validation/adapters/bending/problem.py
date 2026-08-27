# Version: CSF-CUF hollow-rectangle bottom-surface bending adapter v5 - 2026-08-27
from __future__ import annotations

import math

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.problem.problem import GeneralizedLongitudinalLoad, ScalarLoadField
from csf.cuf.numerics import transverse_bounds


def _is_void_domain(domain) -> bool:
    """Return True only for a CSF domain explicitly marked by weightabs=0."""
    weightabs = getattr(domain, "weightabs", None)
    return weightabs is not None and float(weightabs) == 0.0


def _lowest_boundary_segments(section_provider, x: float):
    """
    Find the material boundary segments on the true minimum solver-z face.

    The bounds returned by ``transverse_bounds`` are ordered as
    ``(y_min, y_max, z_min, z_max)``. Void domains are not loaded.
    """
    _, _, z_min, _ = transverse_bounds(section_provider, float(x))
    tol = 1.0e-11 * max(1.0, abs(float(z_min)))
    segments = {}

    for domain in section_provider.domains(float(x)):
        if _is_void_domain(domain):
            continue

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
            f"no material boundary was found on the minimum-z face at x={x}"
        )

    return float(z_min), tuple(
        segments[key] for key in sorted(segments)
    )


def _loaded_face_factors(section_provider, basis, x: float) -> np.ndarray:
    """Compute B_tau(x) = integral_Gamma F_tau(y,z) ds on the loaded face."""
    z_face, segments = _lowest_boundary_segments(section_provider, float(x))

    n_gauss = max(4, (int(basis.order) + 2) // 2)
    xi, wi = np.polynomial.legendre.leggauss(n_gauss)
    values = np.zeros(int(basis.size), dtype=float)

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
                        for tau in range(1, int(basis.size) + 1)
                    ],
                    dtype=float,
                )
            )

    return values


class BendingSurfaceProjector:
    """Project p0 sin(pi x/L) on the CUF basis over the bottom face."""

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

        face_factors = _loaded_face_factors(
            self.section_provider,
            self.basis,
            x,
        )
        phase = math.sin(self.alpha * (x - self.x0))

        # Positive pressure amplitude acts in solver -z.
        values = -self.amplitude * phase * face_factors
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


class HollowRectangleBendingProblem:
    """
    Simply supported hollow beam under a sinusoidal bottom-surface pressure.

    The transverse CUF amplitudes are constrained at both end sections. The
    final scalar constraint removes the free axial rigid translation without
    constraining an axial deformation mode.
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
            for tau in range(1, int(basis.size) + 1)
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
        row_count = 4 * int(basis.size) + 1
        A = np.zeros((row_count, layout.total_dofs), dtype=float)
        b = np.zeros(row_count, dtype=float)
        row = 0

        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, int(basis.size) + 1):
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
                for tau in range(1, int(basis.size) + 1)
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
                    ] += float(local[a]) * float(factor) / length

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
            points.append((f"loaded_face_{index}_left", y0, z_face))
            points.append((f"loaded_face_{index}_right", y1, z_face))
        return tuple(points)


def build_problem(problem_type: str, options: dict):
    if problem_type != "hollow_rectangle_bending_bottom_surface_halfwave":
        raise ValueError(f"unsupported problem.type: {problem_type!r}")

    return HollowRectangleBendingProblem(
        amplitude=float(options.get("amplitude", 1.0))
    )

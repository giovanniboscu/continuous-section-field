# Version: CSF-CUF local physical start-section clamp v03 - 2026-11-20
"""Full physical CUF displacement clamp on the initial CSF section.

Local constraint adapter for ``problem.type: composite``. It uses exactly
 the legacy SVD trace procedure (no change in constraint equations).

The generic composite hands the section provider and x0 to this independent
constraint component through ``bind_section_context`` when the solver calls
build_load_vector. No dependency on any load implementation is introduced.

GEOMETRIC SCOPE (unchanged from independent_z_faces.py): all CSF domains in
 the initial cross-section must be finite CCW quadrilaterals Q4, with no
 cut-outs/nested polygons, since the legacy SVD sampling uses a bilinear
 Q4 map from interior reference points to physical (y,z). Unlike the *load*,
 the clamp does not require the sampled Q4 edges to be parallel to global Y.
"""

from __future__ import annotations

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


def _shape(a, b):
    return 0.25 * np.array([
        (1 - a) * (1 - b),
        (1 + a) * (1 - b),
        (1 + a) * (1 + b),
        (1 - a) * (1 + b),
    ], dtype=float)


def _vertices(section, x, k):
    polygon = section.domain(float(x), int(k))
    V = np.asarray(polygon.vertices, dtype=float)
    if V.shape != (4, 2) or not np.all(np.isfinite(V)):
        raise ValueError(
            f"Physical start clamp requires finite Q4 domains; domain={k}"
        )
    if getattr(polygon, "excluded_vertices", ()):
        raise ValueError("Physical start clamp does not support Q4 cut-outs")
    area = 0.5 * (
        np.dot(V[:, 0], np.roll(V[:, 1], -1))
        - np.dot(V[:, 1], np.roll(V[:, 0], -1))
    )
    if area <= 1.0e-10:
        raise ValueError("Physical start clamp requires CCW nondegenerate Q4 domains")
    return V


class PhysicalStartSectionClamp:
    def __init__(self, *, location: str):
        if location != "start":
            raise ValueError(
                "physical_start_section_clamp supports only location: start"
            )
        self.section_provider = None
        self.x0 = None

    def physical_boundary_condition(self):
        """Solver-neutral physical BC also consumable by the FEM3D driver.

        Reuses the already validated clamp choice rather than repeating
        location parsing in FEM.  For solids, all 3 translations at x0 vanish.
        """
        return {"kind": "full_section_clamp", "location": "start"}

    def bind_section_context(self, *, section_provider, x0, x1):
        """Receive shared geometry from the compositor, not from the load."""
        if section_provider is None or not float(x1) > float(x0):
            raise ValueError("Invalid CSF longitudinal section context for clamp")
        self.section_provider = section_provider
        self.x0 = float(x0)

    def build_constraints(
        self, *, assembled, mesh, basis, longitudinal_integrator,
    ):
        del longitudinal_integrator, mesh
        if self.section_provider is None or self.x0 is None:
            raise RuntimeError(
                "PhysicalStartSectionClamp has no section context: "
                "the composite must call build_load_vector before build_constraints"
            )
        # Sample the physical displacement trace, not individual CUF amplitudes.
        # SVD eliminates only dependent trace directions. This retains the
        # legacy physical-clamp formulation for L9 and other valid expansions.
        m = int(basis.size)
        nside = max(7, 2 * int(np.ceil(np.sqrt(m))))
        ab = np.linspace(-0.85, 0.85, nside)
        rows = []
        for k in range(1, self.section_provider.number_of_domains(self.x0) + 1):
            V = _vertices(self.section_provider, self.x0, k)
            for a in ab:
                for b in ab:
                    y, z = _shape(a, b) @ V
                    rows.append([
                        basis.value(tau, float(y), float(z), x=self.x0)
                        for tau in range(1, m + 1)
                    ])
        B = np.asarray(rows, dtype=float)
        norms = np.linalg.norm(B, axis=0)
        scales = np.where(norms > 0, norms, 1.0)
        _, S, Vh = np.linalg.svd(B / scales, full_matrices=False)
        tol = max(B.shape) * np.finfo(float).eps * S[0] * 10
        rank = int(np.count_nonzero(S > tol))
        if rank < 1:
            raise ValueError("The left CUF displacement trace has rank zero")
        layout = assembled.dof_layout
        A = np.zeros((3 * rank, layout.total_dofs), dtype=float)
        rhs = np.zeros(3 * rank, dtype=float)
        row = 0
        for j in range(rank):
            for c in range(3):
                for tau in range(1, m + 1):
                    A[row, layout.index(node=0, tau=tau, component=c)] = (
                        Vh[j, tau - 1] * scales[tau - 1]
                    )
                row += 1
        print(
            f"[physical-start-clamp] zero-displacement rank={rank}/{m}; "
            f"constraints={3 * rank}",
            flush=True,
        )
        return LinearConstraintSystem(
            matrix=A, rhs=rhs, constraints=(None,) * len(rhs),
        )


def build_problem(problem_type, options):
    if problem_type != "composite":
        raise ValueError("physical_start_section_clamp expects problem.type: composite")
    if set(options) - {"location"}:
        raise ValueError(f"Unknown clamp options: {sorted(set(options) - {'location'})}")
    return PhysicalStartSectionClamp(location=options.get("location", "start"))

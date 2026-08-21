# OPT-09 CUF-ORDER-AWARE SECTION QUADRATURE
from __future__ import annotations

import time
import numpy as np

from csf.utils.csf_cuf import FundamentalNucleusProvider
from csf.utils.csf_cuf_sectional import SectionalCoefficientProvider

from csf_cuf_assembly import CSFCUFGlobalAssembler
from csf_cuf_augmented_solver import AugmentedSparseLinearSolver
from csf_cuf_element import CUFElementMatrixBuilder
from csf_cuf_linear_constraint import LinearConstraintAugmenter
from csf_cuf_longitudinal import GaussLegendreLongitudinalIntegrator, LongitudinalDiscretizer
from csf_cuf_problem import LongitudinalDiscretization
from csf_cuf_basis_plugins import get_cuf_basis_plugin
from csf_cuf_numerics import FixedGaussPolygonIntegrator
from csf_cuf_recovery import (
    CSFCUFDisplacementRecovery,
    CSFCUFStrainStressRecovery,
)


class CSFCUFSolution:
    """
    Solved continuous displacement field.

    Public contract
    ---------------
        u = solution(x, y, z)
        epsilon = solution.strain(x, y, z)
        sigma = solution.stress(x, y, z, domain_id)

    returning respectively

        [u_x, u_y, u_z]

        [epsilon_xx, epsilon_yy, epsilon_zz,
         gamma_yz, gamma_xz, gamma_xy]

        [sigma_xx, sigma_yy, sigma_zz,
         tau_yz, tau_xz, tau_xy]

    The algebraic CUF coefficients are compiled once when the solve finishes.
    A query does not solve, recover from sampled values, or interpolate a
    post-processed displacement profile. It directly evaluates the solved CUF
    finite-element representation at the requested physical point.
    """

    def __init__(
        self,
        *,
        mesh,
        dof_layout,
        solved_dofs,
        basis,
        constitutive_provider,
    ) -> None:
        solved_dofs = np.asarray(solved_dofs, dtype=float)

        if solved_dofs.shape != (dof_layout.total_dofs,):
            raise ValueError("solved_dofs size is inconsistent with DOF layout")
        if not np.all(np.isfinite(solved_dofs)):
            raise ValueError("solved_dofs contains non-finite values")
        if mesh.number_of_nodes != dof_layout.number_of_nodes:
            raise ValueError("mesh and DOF layout have different node counts")
        if basis.size != dof_layout.basis_size:
            raise ValueError("basis size and DOF layout basis size differ")
        if mesh.number_of_elements < 1:
            raise ValueError("continuous solution requires at least one element")

        self._basis = basis
        self._elements = tuple(mesh.elements)
        self._x_start = float(mesh.x_start)
        self._x_end = float(mesh.x_end)
        self._element_x_ends = np.asarray(
            [float(element.x_end) for element in self._elements],
            dtype=float,
        )

        # Compile the solved generalized coefficients once.
        #
        # For each longitudinal element:
        #     local_coefficients[a, tau-1, i] = q(node_a, tau, i)
        #
        # No global DOF lookup is needed during subsequent u(x,y,z) queries.
        element_coefficients = []

        for element in self._elements:
            coefficients = np.empty(
                (
                    len(element.node_ids),
                    dof_layout.basis_size,
                    3,
                ),
                dtype=float,
            )

            for local_node, global_node in enumerate(element.node_ids):
                for tau in range(1, dof_layout.basis_size + 1):
                    for component in range(3):
                        dof = dof_layout.index(
                            node=global_node,
                            tau=tau,
                            component=component,
                        )
                        coefficients[
                            local_node,
                            tau - 1,
                            component,
                        ] = solved_dofs[dof]

            coefficients.setflags(write=False)
            element_coefficients.append(coefficients)

        self._element_coefficients = tuple(element_coefficients)

        # Reuse the already validated generic recovery layer.  No strain/stress
        # formula is duplicated here: CSFCUFSolution only exposes a convenient
        # public facade over the existing recovery objects.
        self._displacement_recovery = CSFCUFDisplacementRecovery(
            mesh=mesh,
            dof_layout=dof_layout,
            solution=solved_dofs,
            basis=basis,
        )
        self._strain_stress_recovery = CSFCUFStrainStressRecovery(
            displacement_recovery=self._displacement_recovery,
            constitutive_provider=constitutive_provider,
        )

    @property
    def x_start(self) -> float:
        return self._x_start

    @property
    def x_end(self) -> float:
        return self._x_end

    def _generalized_amplitudes_at_x(self, x: float) -> np.ndarray:
        """
        Reconstruct the solved CUF generalized amplitudes at one longitudinal
        coordinate.  This is the only part of u(x,y,z) that depends on the
        longitudinal FE interpolation.
        """
        x = float(x)
        if not np.isfinite(x):
            raise ValueError("x must be finite")

        element_index = self._locate_element_index(x)
        element = self._elements[element_index]
        coefficients = self._element_coefficients[element_index]

        xi = (
            2.0
            * (x - float(element.x_start))
            / float(element.length)
            - 1.0
        )

        N = np.asarray(element.shape_values(xi), dtype=float)
        generalized_amplitudes = np.tensordot(
            N,
            coefficients,
            axes=(0, 0),
        )
        generalized_amplitudes = np.asarray(
            generalized_amplitudes,
            dtype=float,
        )

        if generalized_amplitudes.shape != (self._basis.size, 3):
            raise RuntimeError(
                "reconstructed generalized amplitudes have invalid shape"
            )
        if not np.all(np.isfinite(generalized_amplitudes)):
            raise RuntimeError(
                "reconstructed generalized amplitudes contain non-finite values"
            )

        return generalized_amplitudes

    def section_evaluator(self, x: float):
        """
        Return a callable u_x(y,z) for one fixed longitudinal coordinate x.

        The longitudinal FE reconstruction is performed exactly once.  The
        returned callable evaluates the same solved CUF field as __call__, but
        is intended for dense section post-processing where many transverse
        points share the same x.
        """
        generalized_amplitudes = self._generalized_amplitudes_at_x(x)
        generalized_amplitudes.setflags(write=False)
        basis = self._basis
        basis_size = int(basis.size)

        def evaluate_section(y: float, z: float) -> np.ndarray:
            y = float(y)
            z = float(z)
            if not np.isfinite(y) or not np.isfinite(z):
                raise ValueError("y and z must be finite")

            # OPT-04: evaluate the complete transverse basis at once.
            # Keep a generic fallback so CSFCUFSolution remains compatible
            # with CUF basis implementations that expose only scalar value().
            if hasattr(basis, "values"):
                transverse_values = np.asarray(
                    basis.values(y, z),
                    dtype=float,
                )
            else:
                transverse_values = np.fromiter(
                    (
                        float(basis.value(tau, y, z))
                        for tau in range(1, basis_size + 1)
                    ),
                    dtype=float,
                    count=basis_size,
                )

            if transverse_values.shape != (basis_size,):
                raise RuntimeError(
                    "evaluated transverse basis has invalid shape"
                )

            displacement = transverse_values @ generalized_amplitudes
            displacement = np.asarray(displacement, dtype=float)

            if displacement.shape != (3,):
                raise RuntimeError("evaluated displacement has invalid shape")
            if not np.all(np.isfinite(displacement)):
                raise RuntimeError(
                    "evaluated displacement contains non-finite values"
                )

            return displacement

        return evaluate_section

    def __call__(
        self,
        x: float,
        y: float,
        z: float,
    ) -> np.ndarray:
        """
        Evaluate the solved vector displacement field u(x,y,z).
        """
        return self.section_evaluator(float(x))(float(y), float(z))

    def strain(
        self,
        x: float,
        y: float,
        z: float,
    ) -> np.ndarray:
        """
        Evaluate the complete small-strain field epsilon(x,y,z).

        Voigt order:
            [epsilon_xx, epsilon_yy, epsilon_zz,
             gamma_yz, gamma_xz, gamma_xy]
        """
        state = self._strain_stress_recovery.strain(
            x=float(x),
            y=float(y),
            z=float(z),
        )
        strain = np.asarray(state.strain, dtype=float).copy()

        if strain.shape != (6,):
            raise RuntimeError("evaluated strain has invalid shape")
        if not np.all(np.isfinite(strain)):
            raise RuntimeError("evaluated strain contains non-finite values")

        return strain

    def stress(
        self,
        x: float,
        y: float,
        z: float,
        domain_id,
    ) -> np.ndarray:
        """
        Evaluate the complete stress field sigma(x,y,z) in one CSF material
        domain.

        Voigt order:
            [sigma_xx, sigma_yy, sigma_zz,
             tau_yz, tau_xz, tau_xy]

        ``domain_id`` remains explicit because material/topology ownership is
        provided by CSF and must not be guessed by the solver.
        """
        state = self._strain_stress_recovery.stress(
            x=float(x),
            y=float(y),
            z=float(z),
            domain_id=domain_id,
        )
        stress = np.asarray(state.stress, dtype=float).copy()

        if stress.shape != (6,):
            raise RuntimeError("evaluated stress has invalid shape")
        if not np.all(np.isfinite(stress)):
            raise RuntimeError("evaluated stress contains non-finite values")

        return stress

    def _locate_element_index(self, x: float) -> int:
        if x < self._x_start or x > self._x_end:
            raise ValueError(
                f"x={x} lies outside longitudinal domain "
                f"[{self._x_start}, {self._x_end}]"
            )

        # At an interior shared node select the element on the right.
        # At the global final point select the last element.
        index = int(np.searchsorted(self._element_x_ends, x, side="right"))

        if index >= len(self._elements):
            index = len(self._elements) - 1

        return index


def solve_case(case, model_bridge, problem, *, progress: bool = True) -> CSFCUFSolution:
    """
    Solve the CUF problem and return its continuous displacement field.

    The mechanics/numerics are unchanged. The public result of the solver is
    the callable vector function u(x,y,z).
    """
    started = time.perf_counter()

    section_provider = model_bridge.section_provider
    constitutive_provider = model_bridge.constitutive_provider
    x0, x1 = map(float, section_provider.longitudinal_domain())

    basis_plugin = get_cuf_basis_plugin(case.cuf.basis)
    if case.longitudinal.method != "finite_element":
        raise ValueError("startup engine currently supports longitudinal.method=finite_element")
    if case.section_integration.method != "fixed_gauss_polygon":
        raise ValueError(
            "startup engine currently supports section_integration.method=fixed_gauss_polygon"
        )

    basis = basis_plugin.build(
        order=case.cuf.order,
        section_provider=section_provider,
    )

    # OPT-09: each basis plugin declares the minimum section quadrature
    # required by its own approximation space. A higher order explicitly
    # requested by the case is always preserved.
    requested_section_gauss_order = int(case.section_integration.gauss_order)
    cuf_minimum_section_gauss_order = (
        basis_plugin.minimum_section_gauss_order(basis)
    )
    effective_section_gauss_order = max(
        requested_section_gauss_order,
        cuf_minimum_section_gauss_order,
    )

    if progress:
        print(
            f"[quadrature] section Gauss requested = "
            f"{requested_section_gauss_order}",
            flush=True,
        )
        print(
            f"[quadrature] section Gauss effective = "
            f"{effective_section_gauss_order}",
            flush=True,
        )
        print(
            f"[quadrature] CUF basis minimum     = "
            f"{cuf_minimum_section_gauss_order}",
            flush=True,
        )

    section_integrator = FixedGaussPolygonIntegrator(
        order=effective_section_gauss_order
    )

    sectional = SectionalCoefficientProvider(
        section_provider=section_provider,
        constitutive_provider=constitutive_provider,
        basis=basis,
        integrator=section_integrator,
        cache_enabled=True,
    )

    nucleus = FundamentalNucleusProvider(sectional)

    longitudinal_integrator = GaussLegendreLongitudinalIntegrator(
        quadrature_order=case.longitudinal.gauss_order
    )

    element_builder = CUFElementMatrixBuilder(
        nucleus=nucleus,
        integrator=longitudinal_integrator,
    )

    mesh = LongitudinalDiscretizer().build(
        section_provider=section_provider,
        discretization=LongitudinalDiscretization(
            method=case.longitudinal.method,
            elements=case.longitudinal.elements,
            order=case.longitudinal.order,
        ),
    )

    if progress:
        print(
            f"[1/4] model/basis ready: domains from CSF, M={basis.size}",
            flush=True,
        )

    loads, _problem_state = problem.build_loads(
        section_provider=section_provider,
        basis=basis,
        x0=x0,
        x1=x1,
    )

    assembled = CSFCUFGlobalAssembler(
        element_matrix_builder=element_builder,
        longitudinal_integrator=longitudinal_integrator,
    ).assemble(
        mesh=mesh,
        basis_size=basis.size,
        loads=loads,
    )

    if progress:
        print(
            f"[2/4] global assembly complete: "
            f"DOFs={assembled.dof_layout.total_dofs}",
            flush=True,
        )

    constraints = problem.build_constraints(
        assembled=assembled,
        mesh=mesh,
        basis=basis,
        longitudinal_integrator=longitudinal_integrator,
    )

    augmented = LinearConstraintAugmenter().apply(
        system=assembled,
        constraints=constraints,
    )

    algebraic = AugmentedSparseLinearSolver(
        relative_tolerance=1.0e-6,
        absolute_tolerance=1.0e-5,
        constraint_tolerance=1.0e-8,
    ).solve(augmented)

    if progress:
        print(
            "[3/4] solve complete: "
            f"equilibrium={algebraic.equilibrium_relative_residual:.3e}, "
            f"constraints={algebraic.constraint_residual_norm:.3e}",
            flush=True,
        )

    # Compile the solved field once.  Displacement remains directly callable,
    # while strain/stress are exposed through the existing generic recovery
    # layer without changing the solved mechanics.
    solution = CSFCUFSolution(
        mesh=mesh,
        dof_layout=assembled.dof_layout,
        solved_dofs=algebraic.primal,
        basis=basis,
        constitutive_provider=constitutive_provider,
    )

    elapsed = time.perf_counter() - started

    if progress:
        print(
            f"[4/4] u(x,y,z) ready: elapsed={elapsed:.3f} s",
            flush=True,
        )

    return solution

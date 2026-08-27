# Version: CSF-CUF transparent sectional split v16.1 - 2026-08-27
# OPT-09 CUF-ORDER-AWARE SECTION QUADRATURE
from __future__ import annotations

import gc
import time
import numpy as np

from csf.cuf.core.nucleus import FundamentalNucleusProvider
from csf.cuf.core.sectional import SectionalCoefficientProvider
from csf.cuf.core.sectional_geometry import SectionalGeometryProvider

from csf.cuf.solver.assembly import CSFCUFGlobalAssembler
from csf.cuf.solver.augmented_solver import AugmentedSparseLinearSolver
from csf.cuf.solver.element import CUFElementMatrixBuilder
from csf.cuf.solver.linear_constraint import LinearConstraintAugmenter
from csf.cuf.solver.longitudinal import GaussLegendreLongitudinalIntegrator, LongitudinalDiscretizer
from csf.cuf.problem.problem import LongitudinalDiscretization
from csf.cuf.core.basis_plugins import get_cuf_basis_plugin
from csf.cuf.numerics import FixedGaussPolygonIntegrator
from csf.cuf.solver.recovery import (
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



def _longitudinal_gauss_requirement(
    *,
    case,
    section_provider,
    constitutive_provider,
):
    """Estimate the polynomial degree that must be integrated along x.

    The estimate is intentionally conservative and is used only to prevent
    silent longitudinal under-integration.

    Assumptions checked here before using the estimate:
    - CSF polygon topology is unchanged between x0, xmid and x1;
    - every polygon vertex evolves affinely in x;
    - the constitutive matrix sampled on each moving domain evolves affinely
      in x.

    Under those checked assumptions, an affine variation of one transverse
    coordinate turns a tensor Maclaurin product into an x-polynomial of degree
    up to 2N; variation of both coordinates can reach 4N.  The polygon-area
    Jacobian contributes one degree per varying transverse coordinate.  An
    affine constitutive variation contributes one further degree.  Finally,
    the product of longitudinal Lagrange functions of order r contributes at
    most 2r degrees.  This is a safe upper bound; individual nucleus terms can
    have lower degree because derivatives reduce polynomial order.
    """

    x0, x1 = map(float, section_provider.longitudinal_domain())
    xm = 0.5 * (x0 + x1)

    domains0 = tuple(section_provider.domains(x0))
    domainsm = tuple(section_provider.domains(xm))
    domains1 = tuple(section_provider.domains(x1))

    if not (len(domains0) == len(domainsm) == len(domains1)):
        raise ValueError(
            "cannot estimate longitudinal Gauss order: CSF domain count "
            "changes along x"
        )

    def close(a, b):
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        scale = max(
            1.0,
            float(np.max(np.abs(a))) if a.size else 0.0,
            float(np.max(np.abs(b))) if b.size else 0.0,
        )
        return bool(np.allclose(a, b, rtol=1.0e-10, atol=1.0e-10 * scale))

    varies_y = False
    varies_z = False

    for domain_index, (d0, dm, d1) in enumerate(
        zip(domains0, domainsm, domains1),
        start=1,
    ):
        v0 = np.asarray(d0.vertices, dtype=float)
        vm = np.asarray(dm.vertices, dtype=float)
        v1 = np.asarray(d1.vertices, dtype=float)

        if v0.shape != vm.shape or v0.shape != v1.shape:
            raise ValueError(
                "cannot estimate longitudinal Gauss order: polygon vertex "
                f"topology changes in CSF domain {domain_index}"
            )
        if v0.ndim != 2 or v0.shape[1] != 2:
            raise ValueError(
                "cannot estimate longitudinal Gauss order: polygon vertices "
                "must be (y,z) pairs"
            )

        if not close(vm, 0.5 * (v0 + v1)):
            raise ValueError(
                "cannot estimate longitudinal Gauss order: CSF geometry is "
                f"not affine in x for domain {domain_index}"
            )

        varies_y = varies_y or (not close(v0[:, 0], v1[:, 0]))
        varies_z = varies_z or (not close(v0[:, 1], v1[:, 1]))

    material_varies = False

    for domain_id, (d0, dm, d1) in enumerate(
        zip(domains0, domainsm, domains1),
        start=1,
    ):
        def representative(domain):
            vertices = np.asarray(domain.vertices, dtype=float)
            return tuple(np.mean(vertices, axis=0))

        y0, z0 = representative(d0)
        ym, zm = representative(dm)
        y1, z1 = representative(d1)

        C0 = np.asarray(
            constitutive_provider.matrix(
                x=x0, domain_id=domain_id, y=y0, z=z0
            ),
            dtype=float,
        )
        Cm = np.asarray(
            constitutive_provider.matrix(
                x=xm, domain_id=domain_id, y=ym, z=zm
            ),
            dtype=float,
        )
        C1 = np.asarray(
            constitutive_provider.matrix(
                x=x1, domain_id=domain_id, y=y1, z=z1
            ),
            dtype=float,
        )

        if not close(Cm, 0.5 * (C0 + C1)):
            raise ValueError(
                "cannot estimate longitudinal Gauss order: constitutive "
                f"variation is not affine in x for domain {domain_id}"
            )

        material_varies = material_varies or (not close(C0, C1))
        
    ################################################################# 
    # here    
    # contribution of the interaction to the degree of the polynomial 
    #################################################################      
    varying_axes = int(varies_y) + int(varies_z)
    N = int(case.cuf.order)
    r = int(case.longitudinal.order)
    
    if case.cuf.basis == "scaled_maclaurin_tensor":
        # Conservative CSF-CUF variable-section estimate.
        #
        # Each basis function may contain y^N z^N. Therefore the product
        # F_tau * F_s may reach degree 2N in y and 2N in z.
        #
        # For a generally varying cross-section, both transverse coordinates
        # may vary along x. Their combined longitudinal contribution is
        # therefore bounded by 4N.
        #
        # A constant section is treated as the degenerate case and is
        # intentionally over-integrated.
        transverse_x_degree = 4 * N
    
    elif case.cuf.basis in ("scaled_maclaurin", "scaled_legendre"):
        # Conservative CSF-CUF variable-section estimate.
        #
        # For the complete-total-degree basis, F_tau * F_s has total
        # transverse degree <= 2N. When the cross-section varies along x,
        # this transverse polynomial acquires a longitudinal dependence.
        #
        # A constant section is treated as the degenerate case and is
        # intentionally over-integrated.
        transverse_x_degree = 2 * N
    
    else:
        raise ValueError(
            "automatic longitudinal Gauss-order estimation is not defined "
            f"for CUF basis {case.cuf.basis!r}"
        )
    
    # Independent contribution of the varying cross-sectional measure dOmega.
    # For the general affine CSF polygon mapping, the area Jacobian may carry
    # a longitudinal polynomial contribution up to degree 2.
    #
    # This contribution is distinct from transverse_x_degree:
    #   - transverse_x_degree accounts for the transverse polynomial changing
    #     along x because the cross-section changes;
    #   - geometry_jacobian_degree accounts for the variation of dOmega itself.
    #
    # The constant-section case is intentionally covered by the same
    # conservative upper bound.
    geometry_jacobian_degree = 2
    
    # Current constitutive variation is assumed affine in x.
    # A future user-defined/custom constitutive law must provide its own
    # longitudinal polynomial degree explicitly.
    material_degree = 1 if material_varies else 0
    
    # Product of the two longitudinal interpolation functions.
    longitudinal_shape_degree = 2 * r
    
    polynomial_degree = (
        transverse_x_degree
        + geometry_jacobian_degree
        + material_degree
        + longitudinal_shape_degree
    )
    
    # n-point Gauss-Legendre is exact through polynomial degree 2n - 1.
    minimum_gauss_order = (polynomial_degree + 2) // 2

  
        
        
        
    #####
    ###varying_axes = int(varies_y) + int(varies_z)
    ###N = int(case.cuf.order)
    ###r = int(case.longitudinal.order)
    ###
    ###if case.cuf.basis == "scaled_maclaurin_tensor":
    ###    # Each basis function can contain y^N z^N.  A product therefore has
    ###    # degree 2N in every transverse coordinate that varies with x.
    ###    transverse_x_degree = 2 * N * varying_axes
    ###elif case.cuf.basis == "scaled_maclaurin":
    ###    # Complete-total-degree basis: F_tau F_s has total degree <= 2N,
    ###    # regardless of whether one or both transverse coordinates vary.
    ###    transverse_x_degree = 2 * N if varying_axes else 0
    ###else:
    ###    raise ValueError(
    ###        "automatic longitudinal Gauss-order estimation is not defined "
    ###        f"for CUF basis {case.cuf.basis!r}"
    ###    )
    ###
    #### CSF polygon-domain contribution.
    #### Omega_CSF(x), with affine polygon-vertex variation along x, can carry
    #### a longitudinal polynomial contribution up to degree 2.
    #### The upper bound +2 is always retained, including the degenerate
    #### constant-section case, to keep the quadrature estimate conservative.
    ###geometry_degree = 2
    ###
    ###
    ###geometry_jacobian_degree = varying_axes
    ###material_degree = 1 if material_varies else 0
    ###longitudinal_shape_degree = 2 * r
    ###
    ###polynomial_degree = (
    ###    transverse_x_degree
    ###    + geometry_degree
    ###    + material_degree
    ###    + longitudinal_shape_degree
    ###)
    #### n-point Gauss-Legendre is exact through degree 2n-1.
    ###minimum_gauss_order = (polynomial_degree + 2) // 2
    ######
    
    axes = []
    if varies_y:
        axes.append("y")
    if varies_z:
        axes.append("z")
        
        
    print(f"DEBUG transverse_x_degree {transverse_x_degree} polynomial_degree {polynomial_degree} longitudinal_shape_degree {longitudinal_shape_degree}  minimum_gauss_order {minimum_gauss_order}")

    return {
        "polynomial_degree": int(polynomial_degree),
        "minimum_gauss_order": int(minimum_gauss_order),
        "varying_axes": tuple(axes),
        "material_varies": bool(material_varies),
    }

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

    sectional_geometry = SectionalGeometryProvider(
        section_provider=section_provider,
        constitutive_provider=constitutive_provider,
    )

    sectional = SectionalCoefficientProvider(
        geometry_provider=sectional_geometry,
        basis=basis,
        integrator=section_integrator,
        cache_enabled=True,
    )

    nucleus = FundamentalNucleusProvider(sectional)

    longitudinal_requirement = _longitudinal_gauss_requirement(
        case=case,
        section_provider=section_provider,
        constitutive_provider=constitutive_provider,
    )
    requested_longitudinal_gauss_order = int(case.longitudinal.gauss_order)
    minimum_longitudinal_gauss_order = int(
        longitudinal_requirement["minimum_gauss_order"]
    )
    effective_longitudinal_gauss_order = max(
        requested_longitudinal_gauss_order,
        minimum_longitudinal_gauss_order,
    )

    if progress:
        axes = longitudinal_requirement["varying_axes"]
        axes_text = ",".join(axes) if axes else "none"
        print(
            f"[quadrature] longitudinal degree estimate = "
            f"{longitudinal_requirement['polynomial_degree']}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal variation axes  = {axes_text}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal material varies = "
            f"{str(longitudinal_requirement['material_varies']).lower()}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal Gauss requested = "
            f"{requested_longitudinal_gauss_order}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal Gauss minimum   = "
            f"{minimum_longitudinal_gauss_order}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal Gauss effective = "
            f"{effective_longitudinal_gauss_order}",
            flush=True,
        )

    longitudinal_integrator = GaussLegendreLongitudinalIntegrator(
        quadrature_order=effective_longitudinal_gauss_order
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

    # MEM-02: assembly is complete.  The sectional coefficient cache and the
    # nucleus/element-builder chain are no longer consulted by constraints,
    # the algebraic solve, or recovery.  Release them before SuperLU reaches
    # its peak-memory factorization phase.  This changes object lifetime only;
    # the assembled matrix and all numerical operations are unchanged.
    sectional.clear_cache()
    del loads, _problem_state
    del element_builder, nucleus, sectional, section_integrator
    gc.collect()

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

    # The longitudinal integrator is not used after the constraint map exists.
    del longitudinal_integrator
    gc.collect()

    augmented = LinearConstraintAugmenter().apply(
        system=assembled,
        constraints=constraints,
    )

    algebraic = AugmentedSparseLinearSolver(
        equilibration_iterations=case.solver.equilibration.iterations,
    ).solve(augmented)

    if progress:
        print(
            "[3/4] solve complete",
            flush=True,
        )
        print(
            "[verification] "
            f"residual mean = {algebraic.residual_mean:.6e}",
            flush=True,
        )
        print(
            "[verification] "
            "residual standard deviation = "
            f"{algebraic.residual_standard_deviation:.6e}",
            flush=True,
        )
        print(
            "[verification] "
            f"equation-term scale = {algebraic.equation_term_scale:.6e}",
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

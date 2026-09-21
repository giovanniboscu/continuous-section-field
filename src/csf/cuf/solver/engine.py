# Version: CSF-CUF isolated longitudinal basis plugins v31 - 2026-09-21
# OPT-10 COMPILED-FIELD BASIS-OPTIONS METADATA
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
import gc
import time
from pathlib import Path
import numpy as np

from csf.cuf.core.nucleus import FundamentalNucleusProvider
from csf.cuf.core.sectional import SectionalCoefficientProvider
from csf.cuf.core.sectional_geometry import SectionalGeometryProvider

from csf.cuf.solver.assembly import (
    AssembledCSFCUFSystem,
    CSFCUFGlobalAssembler,
    build_global_dof_layout,
)
from csf.cuf.solver.augmented_solver import AugmentedSparseLinearSolver
from csf.cuf.solver.element import CUFElementMatrixBuilder
from csf.cuf.solver.linear_constraint import LinearConstraintAugmenter
from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.solver.longitudinal import (
    GaussLegendreLongitudinalIntegrator,
    LongitudinalDiscretizer,
    LongitudinalElement1D,
    LongitudinalMesh1D,
)
from csf.cuf.problem.problem import LongitudinalDiscretization
from csf.cuf.core.basis_plugins import get_cuf_basis_plugin
from csf.cuf.core.longitudinal_basis_plugins import get_longitudinal_basis_plugin
from csf.cuf.numerics import FixedGaussPolygonIntegrator
from csf.cuf.solver.recovery import (
    CSFCUFDisplacementRecovery,
    CSFCUFStrainStressRecovery,
)
from csf.cuf.solver.compiled_field import CompiledDisplacementField


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
        compiled_displacement=None,
    ) -> None:
        # Own an immutable copy of the primal coefficients. This keeps one
        # CSFCUFSolution self-contained even when several algebraic solutions
        # are produced successively from the same assembled KKT system.
        solved_dofs = np.array(solved_dofs, dtype=float, copy=True)

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

        solved_dofs.setflags(write=False)

        self._basis = basis
        self._compiled_displacement = compiled_displacement
        self._elements = tuple(mesh.elements)
        self._x_start = float(mesh.x_start)
        self._x_end = float(mesh.x_end)
        self._element_x_ends = np.asarray(
            [float(element.x_end) for element in self._elements],
            dtype=float,
        )

        # Compile the solved generalized coefficients once when no persisted
        # compiled displacement representation is available.  Supported
        # polynomial expansions already store the same element-local tensor
        # inside CompiledDisplacementField, so retaining a duplicate here
        # would waste memory after the solve.
        #
        # For each longitudinal element:
        #     local_coefficients[a, tau-1, i] = q(node_a, tau, i)
        #
        # No global DOF lookup is needed during subsequent u(x,y,z) queries.
        element_coefficients = []

        if compiled_displacement is None:
            for element in self._elements:
                coefficients = np.zeros(
                    (
                        len(element.node_ids),
                        dof_layout.basis_size,
                        3,
                    ),
                    dtype=float,
                )
                active_basis_size = dof_layout.basis_size_at_node(element.node_ids[0])

                for local_node, global_node in enumerate(element.node_ids):
                    for tau in range(1, active_basis_size + 1):
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
        if self._compiled_displacement is not None:
            return self._compiled_displacement.section_evaluator(x)

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
                    basis.values(y, z, x=x),
                    dtype=float,
                )
            else:
                transverse_values = np.fromiter(
                    (
                        float(basis.value(tau, y, z, x=x))
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


@dataclass(frozen=True)
class CSFCUFSolutionRun:
    """One solved field together with the equilibration that produced it."""

    equilibration_iterations: int
    solution: CSFCUFSolution


def _longitudinal_gauss_requirement(
    *,
    case,
    basis,
    basis_plugin,
    longitudinal_basis,
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
    the product of two longitudinal basis functions contributes at most twice
    the polynomial degree declared by the selected longitudinal plugin.  This
    is a safe upper bound; individual nucleus terms can
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


        varies_y = False
        varies_z = False


    configured_material_degree = (
        case.longitudinal.material_polynomial_degree
    )
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

        if (
            configured_material_degree is None
            and not close(Cm, 0.5 * (C0 + C1))
        ):
            raise ValueError(
                "cannot estimate longitudinal Gauss order: constitutive "
                f"variation is not affine in x for domain {domain_id}; "
                "set longitudinal.material_polynomial_degree in the case "
                "YAML to the maximum material-law degree across all polygons"
            )

        material_varies = material_varies or (not close(C0, C1))
        
    ################################################################# 
    # here    
    # contribution of the interaction to the degree of the polynomial 
    #################################################################      
    #varying_axes = int(varies_y) + int(varies_z)
    
    longitudinal_polynomial_degree = int(longitudinal_basis.polynomial_degree)
    transverse_x_degree = (
        basis_plugin.transverse_x_polynomial_degree(basis)
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
    
    # When omitted, preserve the historical automatic behavior:
    # constant material -> degree 0; affine material -> degree 1.
    # For custom/non-affine laws the user supplies the maximum polynomial
    # degree across all CSF polygons in the case YAML.
    if configured_material_degree is None:
        material_degree = 1 if material_varies else 0
        material_degree_source = "automatic"
    else:
        material_degree = int(configured_material_degree)
        material_degree_source = "configured"
    
    # Product of the two longitudinal approximation functions.  The FEM does
    # not infer this from a concrete family; the plugin declares its degree.
    longitudinal_shape_degree = 2 * longitudinal_polynomial_degree
    
    polynomial_degree = (
        transverse_x_degree
        + geometry_jacobian_degree
        + material_degree
        + longitudinal_shape_degree
    )
    
    # n-point Gauss-Legendre is exact through polynomial degree 2n - 1.
    minimum_gauss_order = (polynomial_degree + 2) // 2

  
        
        
    
    return {
        "polynomial_degree": int(polynomial_degree),
        "minimum_gauss_order": int(minimum_gauss_order),
        "material_varies": bool(material_varies),
        "material_polynomial_degree": int(material_degree),
        "material_degree_source": material_degree_source,
    }    
    

def _validate_segmented_expansion_against_mesh(*, basis, mesh) -> tuple:
    """Validate an optional segmented transverse expansion law.

    Expansion boundaries belong to the CUF expansion law, not to the user FE
    mesh.  They may lie anywhere in the longitudinal domain.  When a real
    change of transverse expansion occurs inside an FE element, the solver
    creates an internal interface partition later; the YAML FE mesh therefore
    does not need to be aligned with the expansion segmentation.

    Adjacent segments may use different transverse basis sizes.  The global
    algebraic layout and perfect-bond equations retain the local sizes exactly.
    """
    segments = getattr(basis, "segments", None)
    boundaries = getattr(basis, "boundaries", None)
    if segments is None or boundaries is None:
        return ()

    segments = tuple(segments)
    boundaries = tuple(float(value) for value in boundaries)
    if not segments or len(boundaries) != len(segments) + 1:
        raise ValueError("segmented CUF basis exposes an invalid segment law")

    x0 = float(mesh.x_start)
    x1 = float(mesh.x_end)
    tol = 1.0e-10 * max(1.0, abs(x0), abs(x1), abs(x1 - x0))
    if not np.isclose(boundaries[0], x0, rtol=0.0, atol=tol):
        raise ValueError("segmented CUF expansion does not start at the mesh domain start")
    if not np.isclose(boundaries[-1], x1, rtol=0.0, atol=tol):
        raise ValueError("segmented CUF expansion does not end at the mesh domain end")

    for left, right in zip(boundaries, boundaries[1:]):
        if not right > left + tol:
            raise ValueError("segmented CUF expansion boundaries must be strictly increasing")

    return segments


def _split_mesh_at_segment_interfaces(*, mesh, segments):
    """Create independent FE traces at real expansion changes.

    The user FE mesh is *not* required to contain expansion boundaries.  If a
    boundary with different adjacent expansion definitions falls inside an FE
    element, that element is internally partitioned at the boundary using the
    same polynomial order.  The coincident left/right interface nodes receive
    distinct global ids, producing independent generalized traces q- and q+
    for the perfect-bond equation.

    Boundaries whose adjacent expansion definitions are identical are exact
    no-ops: the original mesh is returned unchanged when all boundaries are of
    this kind.  This preserves the previous N08-N08 regression case bit for
    bit at the mesh/DOF level.
    """
    if not segments or len(segments) < 2:
        return mesh, ()

    all_interfaces = []
    for interface_index in range(len(segments) - 1):
        left = segments[interface_index]
        right = segments[interface_index + 1]
        left_key = getattr(left, "definition_key", None)
        right_key = getattr(right, "definition_key", None)
        # Same expansion on both sides: physical continuity is already C0 and
        # no independent trace/bond is required.
        if left_key is not None and right_key is not None and left_key == right_key:
            continue
        all_interfaces.append((interface_index, float(left.x_end)))

    if not all_interfaces:
        return mesh, ()

    tol = 1.0e-10 * max(
        1.0,
        abs(float(mesh.x_start)),
        abs(float(mesh.x_end)),
        abs(float(mesh.x_end) - float(mesh.x_start)),
    )
    reference_nodes = np.asarray(
        mesh.elements[0].reference_nodes,
        dtype=float,
    )
    equispaced_reference = np.linspace(
        -1.0,
        1.0,
        reference_nodes.size,
        dtype=float,
    )

    # Partition every original element only where a real expansion change lies
    # in its closed interval.  This is an internal algebraic/interface mesh;
    # it does not impose any alignment requirement on the case YAML.
    pieces = []
    for original_index, element in enumerate(mesh.elements):
        a = float(element.x_start)
        b = float(element.x_end)
        cuts = []
        for interface_index, x_interface in all_interfaces:
            if a + tol < x_interface < b - tol:
                cuts.append((x_interface, interface_index))
        cuts.sort(key=lambda item: item[0])

        bounds = [a] + [x for x, _idx in cuts] + [b]
        for piece_index in range(len(bounds) - 1):
            left_x = float(bounds[piece_index])
            right_x = float(bounds[piece_index + 1])
            split_left = None
            split_right = None
            for interface_index, x_interface in all_interfaces:
                if np.isclose(left_x, x_interface, rtol=0.0, atol=tol):
                    split_left = interface_index
                if np.isclose(right_x, x_interface, rtol=0.0, atol=tol):
                    split_right = interface_index
            pieces.append(
                (original_index, left_x, right_x, split_left, split_right)
            )

    # Original FE boundaries that are themselves expansion interfaces also
    # need independent left/right traces.  Mark them on adjacent pieces.
    normalized = []
    for original_index, left_x, right_x, split_left, split_right in pieces:
        for interface_index, x_interface in all_interfaces:
            if np.isclose(left_x, x_interface, rtol=0.0, atol=tol):
                split_left = interface_index
            if np.isclose(right_x, x_interface, rtol=0.0, atol=tol):
                split_right = interface_index
        normalized.append((original_index, left_x, right_x, split_left, split_right))
    pieces = normalized

    new_nodes = []
    new_elements = []
    interface_pairs_by_index = {}
    previous_last_node = None
    previous_right_interface = None

    for new_element_index, (_original_index, a, b, left_interface, right_interface) in enumerate(pieces):
        if np.array_equal(reference_nodes, equispaced_reference):
            coordinates_array = np.linspace(
                float(a),
                float(b),
                reference_nodes.size,
                dtype=float,
            )
        else:
            coordinates_array = (
                0.5 * (1.0 - reference_nodes) * float(a)
                + 0.5 * (1.0 + reference_nodes) * float(b)
            )
            coordinates_array[0] = float(a)
            coordinates_array[-1] = float(b)
        coordinates = tuple(float(x) for x in coordinates_array)
        local_ids = []

        if previous_last_node is None:
            first_node = len(new_nodes)
            new_nodes.append(coordinates[0])
        elif left_interface is not None:
            # Duplicate the coincident interface node: previous_last_node is
            # q-, this new node is q+.
            first_node = len(new_nodes)
            new_nodes.append(coordinates[0])
            interface_pairs_by_index[left_interface] = (
                left_interface,
                float(coordinates[0]),
                int(previous_last_node),
                int(first_node),
            )
        else:
            first_node = int(previous_last_node)

        local_ids.append(first_node)
        for coordinate in coordinates[1:]:
            local_ids.append(len(new_nodes))
            new_nodes.append(float(coordinate))

        new_elements.append(
            LongitudinalElement1D(
                index=new_element_index,
                node_ids=tuple(local_ids),
                coordinates=coordinates,
                basis=mesh.basis,
            )
        )
        previous_last_node = local_ids[-1]
        previous_right_interface = right_interface

    expected = {idx for idx, _x in all_interfaces}
    if set(interface_pairs_by_index) != expected:
        missing = sorted(expected.difference(interface_pairs_by_index))
        raise RuntimeError(
            "failed to create independent traces for segmented CUF interfaces "
            f"{missing}"
        )

    split_mesh = LongitudinalMesh1D(
        x_start=float(mesh.x_start),
        x_end=float(mesh.x_end),
        nodes=tuple(float(value) for value in new_nodes),
        elements=tuple(new_elements),
        basis=mesh.basis,
    )
    interface_pairs = tuple(
        interface_pairs_by_index[index] for index in sorted(interface_pairs_by_index)
    )
    return split_mesh, interface_pairs


def _bond_power_coefficients(basis):
    """Return a static physical y-z polynomial representation for one trace basis.

    The perfect bond is imposed on the reconstructed displacement field, not by
    matching CUF indices and not through sectional quadrature.  A basis may
    expose its exact physical power coefficients directly.  Otherwise reuse the
    same generic static-polynomial reconstruction already used by the compiled
    displacement checkpoint.
    """
    exporter = getattr(basis, "power_coefficients", None)
    if callable(exporter):
        coefficients = np.asarray(exporter(), dtype=float)
    else:
        coefficients = CompiledDisplacementField._static_transverse_power_coefficients(
            basis
        )
        if coefficients is None:
            raise TypeError(
                "longitudinal perfect bond requires each trace basis to expose "
                "a static polynomial representation through power_coefficients() "
                "or the generic compiled-field polynomial contract"
            )
        coefficients = np.asarray(coefficients, dtype=float)

    if coefficients.ndim != 3:
        raise ValueError(
            "longitudinal perfect-bond power coefficients must have shape "
            "(basis_size, y_power_count, z_power_count)"
        )
    if coefficients.shape[0] != int(basis.size):
        raise ValueError(
            "longitudinal perfect-bond power coefficients are inconsistent "
            "with basis.size"
        )
    if not np.all(np.isfinite(coefficients)):
        raise ValueError(
            "longitudinal perfect-bond power coefficients contain non-finite values"
        )
    return coefficients


def _perfect_bond_constraints(
    *,
    base_constraints,
    assembled,
    segments,
    interface_pairs,
):
    """Append strong zero-gap displacement-continuity constraints.

    At every internal longitudinal boundary x_i the left and right traces are

        u_L(y,z) = sum_tau F_tau^L(y,z) q_tau^L,
        u_R(y,z) = sum_tau F_tau^R(y,z) q_tau^R.

    The bond imposes u_L(y,z) - u_R(y,z) == 0 as an identity of the physical
    transverse polynomial field.  Both trace bases are therefore written in a
    common physical monomial representation and the coefficient of every active
    y**p z**q term is equated directly.  These are ordinary additional linear
    constraint equations, exactly like an external displacement constraint but
    with the unknown right trace replacing a prescribed value.

    No sectional quadrature, Gram matrix, eigenmodes, CSF domains, or direct
    equality of CUF coefficient indices is used.
    """
    if not interface_pairs:
        return base_constraints

    layout = assembled.dof_layout
    bond_rows = []
    bond_meta = []

    for interface_index, x_interface, left_node, right_node in interface_pairs:
        left_basis = segments[interface_index].basis
        right_basis = segments[interface_index + 1].basis
        ML = int(left_basis.size)
        MR = int(right_basis.size)

        if layout.basis_size_at_node(left_node) != ML:
            raise RuntimeError(
                "left interface trace size is inconsistent with DOF layout"
            )
        if layout.basis_size_at_node(right_node) != MR:
            raise RuntimeError(
                "right interface trace size is inconsistent with DOF layout"
            )

        left_coefficients = _bond_power_coefficients(left_basis)
        right_coefficients = _bond_power_coefficients(right_basis)

        y_count = max(
            int(left_coefficients.shape[1]),
            int(right_coefficients.shape[1]),
        )
        z_count = max(
            int(left_coefficients.shape[2]),
            int(right_coefficients.shape[2]),
        )

        # Each row below is one physical monomial coefficient of the
        # reconstructed displacement trace.  Columns are the generalized CUF
        # amplitudes on the corresponding side of the interface.
        left_map = np.zeros((y_count * z_count, ML), dtype=float)
        right_map = np.zeros((y_count * z_count, MR), dtype=float)

        left_padded = np.zeros((ML, y_count, z_count), dtype=float)
        right_padded = np.zeros((MR, y_count, z_count), dtype=float)
        left_padded[
            :, : left_coefficients.shape[1], : left_coefficients.shape[2]
        ] = left_coefficients
        right_padded[
            :, : right_coefficients.shape[1], : right_coefficients.shape[2]
        ] = right_coefficients

        left_map[:, :] = np.transpose(left_padded, (1, 2, 0)).reshape(
            y_count * z_count,
            ML,
        )
        right_map[:, :] = np.transpose(right_padded, (1, 2, 0)).reshape(
            y_count * z_count,
            MR,
        )

        jump_map = np.hstack((left_map, -right_map))
        row_norms = np.linalg.norm(jump_map, axis=1)
        active_rows = row_norms > 0.0
        jump_map = jump_map[active_rows]
        row_norms = row_norms[active_rows]

        if jump_map.shape[0] == 0:
            raise RuntimeError(
                "longitudinal perfect bond produced no displacement equations "
                f"at x={x_interface:.16g}"
            )

        # Constraint-row scaling changes neither the physical equality nor its
        # null space.  It prevents high-order physical monomial coefficients
        # from entering the KKT system at vastly different numerical scales.
        jump_map = jump_map / row_norms[:, None]

        # Do not silently drop or combine equations.  If the physical
        # coefficient equalities are linearly dependent, stop explicitly rather
        # than reintroducing a modal/SVD/eigenvalue bond formulation.
        numerical_rank = int(np.linalg.matrix_rank(jump_map))
        if numerical_rank != jump_map.shape[0]:
            raise RuntimeError(
                "longitudinal perfect-bond displacement equations are linearly "
                "dependent at "
                f"x={x_interface:.16g}: rows={jump_map.shape[0]}, "
                f"rank={numerical_rank}"
            )

        active_indices = np.flatnonzero(active_rows)
        for component in range(3):
            for local_row, flat_index in enumerate(active_indices):
                coefficient_row = jump_map[local_row]
                row = np.zeros(layout.total_dofs, dtype=float)

                for tau, coefficient in enumerate(
                    coefficient_row[:ML],
                    start=1,
                ):
                    row[
                        layout.index(
                            node=left_node,
                            tau=tau,
                            component=component,
                        )
                    ] = float(coefficient)

                for tau, coefficient in enumerate(
                    coefficient_row[ML:],
                    start=1,
                ):
                    row[
                        layout.index(
                            node=right_node,
                            tau=tau,
                            component=component,
                        )
                    ] = float(coefficient)

                y_power, z_power = divmod(int(flat_index), z_count)
                bond_rows.append(row)
                bond_meta.append((
                    "longitudinal_perfect_bond",
                    float(x_interface),
                    int(component),
                    int(y_power),
                    int(z_power),
                    int(ML),
                    int(MR),
                ))

    if not bond_rows:
        return base_constraints

    bond_matrix = np.vstack(bond_rows)
    matrix = np.vstack((np.asarray(base_constraints.matrix, dtype=float), bond_matrix))
    rhs = np.concatenate((
        np.asarray(base_constraints.rhs, dtype=float),
        np.zeros(bond_matrix.shape[0], dtype=float),
    ))
    metadata = tuple(base_constraints.constraints) + tuple(bond_meta)
    return LinearConstraintSystem(matrix=matrix, rhs=rhs, constraints=metadata)


def solve_case_runs(
    case,
    model_bridge,
    problem,
    *,
    progress: bool = True,
) -> Iterator[CSFCUFSolutionRun]:
    """Yield successful CUF solutions for the requested equilibration runs.

    Geometry, section integration, global assembly, constraints, and the KKT
    system are built once. A scalar equilibration setting yields one run. A
    YAML sequence yields one run for each successfully solved requested value.
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
        continuous_section_field=model_bridge.field,
        options=case.cuf.basis_options,
    )

    longitudinal_basis_plugin = get_longitudinal_basis_plugin(
        case.longitudinal.basis
    )
    longitudinal_basis = longitudinal_basis_plugin.build(
        order=case.longitudinal.order,
        options=case.longitudinal.basis_options,
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
        basis=basis,
        basis_plugin=basis_plugin,
        longitudinal_basis=longitudinal_basis,
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

        print(
            f"[quadrature] longitudinal degree estimate = "
            f"{longitudinal_requirement['polynomial_degree']}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal material varies = "
            f"{str(longitudinal_requirement['material_varies']).lower()}",
            flush=True,
        )
        print(
            f"[quadrature] longitudinal material degree = "
            f"{longitudinal_requirement['material_polynomial_degree']} "
            f"({longitudinal_requirement['material_degree_source']})",
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
            element_boundaries=case.longitudinal.element_boundaries,
        ),
        basis=longitudinal_basis,
    )

    expansion_segments = _validate_segmented_expansion_against_mesh(
        basis=basis,
        mesh=mesh,
    )
    mesh, expansion_interface_pairs = _split_mesh_at_segment_interfaces(
        mesh=mesh,
        segments=expansion_segments,
    )
    if expansion_segments:
        element_basis_sizes = tuple(
            int(basis.basis_at(0.5 * (element.x_start + element.x_end)).size)
            for element in mesh.elements
        )
    else:
        element_basis_sizes = tuple(int(basis.size) for _ in mesh.elements)

    if progress:
        print(
            f"[1/4] model/basis ready: domains from CSF, M={basis.size}",
            flush=True,
        )
        if expansion_segments:
            print(
                f"[expansion] longitudinal segments = {len(expansion_segments)}",
                flush=True,
            )
            for index, segment in enumerate(expansion_segments, start=1):
                print(
                    f"[expansion] segment {index}: "
                    f"x=[{float(segment.x_start):.16g}, "
                    f"{float(segment.x_end):.16g}] "
                    f"basis={segment.basis_name} M={int(segment.basis.size)}",
                    flush=True,
                )

    dof_layout = build_global_dof_layout(
        mesh=mesh,
        basis_size=int(basis.size),
        element_basis_sizes=element_basis_sizes,
    )

    stiffness = CSFCUFGlobalAssembler(
        element_matrix_builder=element_builder,
    ).assemble(
        mesh=mesh,
        dof_layout=dof_layout,
    )

    loads_started = time.perf_counter()
    load_vector, _problem_state = problem.build_load_vector(
        section_provider=section_provider,
        basis=basis,
        mesh=mesh,
        dof_layout=dof_layout,
        longitudinal_integrator=longitudinal_integrator,
        x0=x0,
        x1=x1,
    )
    print(
        f"[assembly] loads complete "
        f"elapsed={time.perf_counter() - loads_started:.1f}s",
        flush=True,
    )

    assembled = AssembledCSFCUFSystem(
        stiffness=stiffness,
        load=np.asarray(load_vector, dtype=float),
        dof_layout=dof_layout,
    )

    # MEM-02: assembly is complete.  The sectional coefficient cache and the
    # nucleus/element-builder chain are no longer consulted by constraints,
    # the algebraic solve, or recovery.  Release them before SuperLU reaches
    # its peak-memory factorization phase.  This changes object lifetime only;
    # the assembled matrix and all numerical operations are unchanged.
    sectional.clear_cache()
    del load_vector, _problem_state
    del element_builder, nucleus, sectional
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
    base_constraint_row_count = int(np.asarray(constraints.matrix).shape[0])
    constraints = _perfect_bond_constraints(
        base_constraints=constraints,
        assembled=assembled,
        segments=expansion_segments,
        interface_pairs=expansion_interface_pairs,
    )
    bond_constraint_row_count = (
        int(np.asarray(constraints.matrix).shape[0]) - base_constraint_row_count
    )

    if progress and expansion_interface_pairs:
        print(
            f"[bond] longitudinal perfect bonds = "
            f"{len(expansion_interface_pairs)}; "
            f"constraint rows added = {bond_constraint_row_count}",
            flush=True,
        )

    # The longitudinal and section integrators are not used after the
    # constraint map exists.
    del longitudinal_integrator, section_integrator
    gc.collect()

    augmented = LinearConstraintAugmenter().apply(
        system=assembled,
        constraints=constraints,
    )

    equilibration = case.solver.equilibration
    iteration_values = equilibration.iteration_values
    sweep_mode = equilibration.is_sweep

    # The scalar solver API remains unchanged. Sweep mode uses the progressive
    # multi-solve path so equilibration work is reused between checkpoints.
    solver = AugmentedSparseLinearSolver(
        equilibration_iterations=iteration_values[0],
    )
    if sweep_mode:
        algebraic_runs = solver.solve_many(
            augmented,
            equilibration_iterations=iteration_values,
        )
    else:
        def _single_algebraic_run():
            yield iteration_values[0], solver.solve(augmented)

        algebraic_runs = _single_algebraic_run()

    successful_runs = 0

    try:
        for equilibration_iterations, algebraic in algebraic_runs:
            successful_runs += 1

            if progress:
                if sweep_mode:
                    print(
                        "[3/4] solve complete: "
                        f"equilibration_iterations={equilibration_iterations}",
                        flush=True,
                    )
                else:
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

            metadata = {
                "case_name": str(case.name),
                "basis_name": str(case.cuf.basis),
                "basis_options": dict(case.cuf.basis_options),
            }
            if sweep_mode:
                metadata["equilibration_iterations"] = int(
                    equilibration_iterations
                )

            # Compile each successful solved field independently. The solution
            # owns its primal coefficients, so later solves cannot mutate it.
            compiled_displacement = CompiledDisplacementField.from_solution_data(
                mesh=mesh,
                dof_layout=assembled.dof_layout,
                solved_dofs=algebraic.primal,
                basis=basis,
                metadata=metadata,
            )

            if compiled_displacement is not None:
                case_name = str(case.name).strip()
                if not case_name or case_name != Path(case_name).name:
                    raise ValueError(
                        "case.name must be a non-empty filename-safe value "
                        "for automatic displacement checkpoints"
                    )
                checkpoint_name = (
                    f"{case_name}_eq{equilibration_iterations}.cuf.npz"
                    if sweep_mode
                    else f"{case_name}.cuf.npz"
                )
                checkpoint_path, checkpoint_hash = (
                    compiled_displacement.save_atomic(
                        case.output_dir / checkpoint_name
                    )
                )
                if progress:
                    print(
                        "[solution-checkpoint] "
                        f"saved={checkpoint_path} sha256={checkpoint_hash}",
                        flush=True,
                    )
            elif progress:
                print(
                    "[solution-checkpoint] skipped: selected expansion cannot "
                    "be compiled into the self-contained displacement checkpoint",
                    flush=True,
                )

            solution = CSFCUFSolution(
                mesh=mesh,
                dof_layout=assembled.dof_layout,
                solved_dofs=algebraic.primal,
                basis=basis,
                constitutive_provider=constitutive_provider,
                compiled_displacement=compiled_displacement,
            )

            # Drop the augmented solution before yielding the public field.
            # CSFCUFSolution owns the primal coefficients it needs.
            del algebraic
            gc.collect()

            yield CSFCUFSolutionRun(
                equilibration_iterations=int(equilibration_iterations),
                solution=solution,
            )

            del solution, compiled_displacement
            gc.collect()

    finally:
        close = getattr(algebraic_runs, "close", None)
        if callable(close):
            close()

        # Shared assembly/KKT data live across all sweep checkpoints and are
        # released only after the sequence is exhausted or explicitly closed.
        del constraints, augmented, assembled
        gc.collect()

    if successful_runs == 0:
        raise RuntimeError(
            "no equilibration setting produced a usable CUF solution"
        )

    elapsed = time.perf_counter() - started

    if progress:
        if sweep_mode:
            print(
                f"[4/4] {successful_runs} u(x,y,z) fields ready: "
                f"elapsed={elapsed:.3f} s",
                flush=True,
            )
        else:
            print(
                f"[4/4] u(x,y,z) ready: elapsed={elapsed:.3f} s",
                flush=True,
            )


def solve_case(case, model_bridge, problem, *, progress: bool = True) -> CSFCUFSolution:
    """Solve one scalar-equilibration case and return its displacement field.

    This preserves the historical public contract. Sweep cases deliberately use
    ``solve_case_runs`` so ``CSFCUFSolution`` never changes meaning or becomes a
    collection.
    """

    if case.solver.equilibration.is_sweep:
        raise ValueError(
            "solve_case() requires scalar solver.equilibration.iterations; "
            "use solve_case_runs() for an equilibration sequence"
        )

    runs = solve_case_runs(
        case,
        model_bridge,
        problem,
        progress=progress,
    )
    try:
        first = next(runs)
        try:
            next(runs)
        except StopIteration:
            pass
        else:
            raise RuntimeError(
                "scalar solve unexpectedly produced more than one solution"
            )
        return first.solution
    finally:
        runs.close()

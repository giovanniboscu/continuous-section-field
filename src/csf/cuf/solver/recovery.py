# Version: CSF-CUF isolated transverse expansion plugins v21 - 2026-08-29
"""
Generic displacement recovery for the longitudinal CSF-CUF finite-element
solution.

This module reconstructs:

    global algebraic DOFs
        -> generalized CUF amplitudes u_{i,tau}(x)
        -> complete displacement field u_i(x,y,z)

No strain/stress recovery is performed here.

No benchmark, material model, section shape, Navier specialization, or fixed
CUF basis family is introduced. The recovery depends only on:

    - the longitudinal FE mesh;
    - the global DOF layout;
    - the solved global DOF vector;
    - the generic CUFBasis API.

The same recovery therefore applies to constant or variable geometry/material
problems once a solution vector has been obtained.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.solver.assembly import GlobalDOFLayout
from csf.cuf.solver.longitudinal import (
    LongitudinalElement1D,
    LongitudinalMesh1D,
)


@dataclass(frozen=True)
class GeneralizedAmplitudeState:
    """
    Generalized CUF amplitudes at one longitudinal coordinate.

    ``values`` has shape (basis_size, 3), ordered as:
        rows    -> tau = 1 .. basis_size
        columns -> x, y, z displacement components
    """

    x: float
    values: np.ndarray


@dataclass(frozen=True)
class DisplacementState:
    """
    Complete displacement vector at one physical point.
    """

    x: float
    y: float
    z: float
    displacement: np.ndarray


class CSFCUFDisplacementRecovery:
    """
    Generic recovery of longitudinal generalized amplitudes and full
    displacement field.
    """

    def __init__(
        self,
        *,
        mesh: LongitudinalMesh1D,
        dof_layout: GlobalDOFLayout,
        solution: np.ndarray,
        basis: CUFBasis,
    ) -> None:
        if not isinstance(mesh, LongitudinalMesh1D):
            raise TypeError(
                "mesh must be a LongitudinalMesh1D"
            )

        if not isinstance(dof_layout, GlobalDOFLayout):
            raise TypeError(
                "dof_layout must be a GlobalDOFLayout"
            )

        if not isinstance(basis, CUFBasis):
            raise TypeError(
                "basis must implement CUFBasis"
            )

        solution = np.asarray(
            solution,
            dtype=float,
        )

        if solution.shape != (
            dof_layout.total_dofs,
        ):
            raise ValueError(
                "solution size is inconsistent with DOF layout"
            )

        if not np.all(np.isfinite(solution)):
            raise ValueError(
                "solution contains non-finite values"
            )

        if mesh.number_of_nodes != dof_layout.number_of_nodes:
            raise ValueError(
                "mesh and DOF layout have different node counts"
            )

        if basis.size != dof_layout.basis_size:
            raise ValueError(
                "basis size and DOF layout basis size differ"
            )

        self.mesh = mesh
        self.dof_layout = dof_layout
        self.solution = solution
        self.basis = basis

    # ------------------------------------------------------------------
    # Longitudinal generalized amplitudes
    # ------------------------------------------------------------------

    def amplitudes(
        self,
        x: float,
    ) -> GeneralizedAmplitudeState:
        """
        Recover all generalized amplitudes u_{i,tau}(x).
        """

        element, xi = self._locate_element(
            float(x)
        )

        N = element.shape_values(xi)

        values = np.zeros(
            (
                self.dof_layout.basis_size,
                3,
            ),
            dtype=float,
        )

        for local_node, global_node in enumerate(
            element.node_ids
        ):
            weight = float(N[local_node])

            for tau in range(
                1,
                self.dof_layout.basis_size + 1,
            ):
                for component in range(3):
                    dof = self.dof_layout.index(
                        node=global_node,
                        tau=tau,
                        component=component,
                    )

                    values[
                        tau - 1,
                        component,
                    ] += weight * self.solution[dof]

        return GeneralizedAmplitudeState(
            x=float(x),
            values=values,
        )

    def amplitude_derivatives(
        self,
        x: float,
    ) -> GeneralizedAmplitudeState:
        """
        Recover first longitudinal derivatives du_{i,tau}/dx.
        """

        element, xi = self._locate_element(
            float(x)
        )

        dNdx = element.shape_derivatives_physical(
            xi
        )

        values = np.zeros(
            (
                self.dof_layout.basis_size,
                3,
            ),
            dtype=float,
        )

        for local_node, global_node in enumerate(
            element.node_ids
        ):
            weight = float(dNdx[local_node])

            for tau in range(
                1,
                self.dof_layout.basis_size + 1,
            ):
                for component in range(3):
                    dof = self.dof_layout.index(
                        node=global_node,
                        tau=tau,
                        component=component,
                    )

                    values[
                        tau - 1,
                        component,
                    ] += weight * self.solution[dof]

        return GeneralizedAmplitudeState(
            x=float(x),
            values=values,
        )

    # ------------------------------------------------------------------
    # Complete displacement field
    # ------------------------------------------------------------------

    def displacement(
        self,
        *,
        x: float,
        y: float,
        z: float,
    ) -> DisplacementState:
        """
        Recover the complete displacement vector u(x,y,z).
        """

        amplitudes = self.amplitudes(x)

        displacement = np.zeros(
            3,
            dtype=float,
        )

        for tau in range(
            1,
            self.basis.size + 1,
        ):
            F_tau = float(
                self.basis.value(
                    tau,
                    float(y),
                    float(z),
                    x=float(x),
                )
            )

            displacement += (
                F_tau
                * amplitudes.values[
                    tau - 1,
                    :
                ]
            )

        return DisplacementState(
            x=float(x),
            y=float(y),
            z=float(z),
            displacement=displacement,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _locate_element(
        self,
        x: float,
    ) -> Tuple[
        LongitudinalElement1D,
        float,
    ]:
        """
        Locate the element containing x and return its reference coordinate xi.

        At an interior shared node, the element on the right is selected,
        except for the global end point where the last element is selected.
        """

        if not np.isfinite(x):
            raise ValueError("x must be finite")

        if x < self.mesh.x_start or x > self.mesh.x_end:
            raise ValueError(
                f"x={x} lies outside longitudinal domain "
                f"[{self.mesh.x_start}, {self.mesh.x_end}]"
            )

        # Global final point.
        if x == self.mesh.x_end:
            element = self.mesh.elements[-1]
            return element, 1.0

        for element in self.mesh.elements:
            if element.x_start <= x < element.x_end:
                xi = (
                    2.0
                    * (x - element.x_start)
                    / element.length
                    - 1.0
                )

                return element, float(xi)

        raise RuntimeError(
            "failed to locate an in-domain longitudinal coordinate"
        )


# =============================================================================
# Generic strain and stress recovery
# =============================================================================

from typing import Hashable

from csf.cuf.core.material import ConstitutiveProvider


@dataclass(frozen=True)
class StrainState:
    """
    Small-strain state in the CSF-CUF Voigt convention:

        [epsilon_xx,
         epsilon_yy,
         epsilon_zz,
         gamma_yz,
         gamma_xz,
         gamma_xy]

    The shear components are engineering shear strains.
    """

    x: float
    y: float
    z: float
    strain: np.ndarray


@dataclass(frozen=True)
class StressState:
    """
    Stress state in the matching Voigt convention:

        [sigma_xx,
         sigma_yy,
         sigma_zz,
         tau_yz,
         tau_xz,
         tau_xy]
    """

    x: float
    y: float
    z: float
    domain_id: Hashable
    strain: np.ndarray
    stress: np.ndarray
    constitutive_matrix: np.ndarray


class CSFCUFStrainStressRecovery:
    """
    Generic recovery of small strains and stresses.

    Kinematics
    ----------
    With

        u_i(x,y,z) = sum_tau F_tau(y,z) u_{i,tau}(x),

    the strain vector is recovered as

        epsilon_xx = sum F_tau     * u_x,tau,x
        epsilon_yy = sum F_tau,y   * u_y,tau
        epsilon_zz = sum F_tau,z   * u_z,tau

        gamma_yz   = sum (F_tau,z * u_y,tau
                        + F_tau,y * u_z,tau)

        gamma_xz   = sum (F_tau,z * u_x,tau
                        + F_tau   * u_z,tau,x)

        gamma_xy   = sum (F_tau,y * u_x,tau
                        + F_tau   * u_y,tau,x)

    Stress recovery is then exactly

        sigma = C^k(x,y,z) epsilon.

    No isotropy, homogeneity, constant section, or benchmark specialization
    is assumed.
    """

    def __init__(
        self,
        *,
        displacement_recovery: CSFCUFDisplacementRecovery,
        constitutive_provider: ConstitutiveProvider,
    ) -> None:
        if not isinstance(
            displacement_recovery,
            CSFCUFDisplacementRecovery,
        ):
            raise TypeError(
                "displacement_recovery must be a "
                "CSFCUFDisplacementRecovery"
            )

        if not isinstance(
            constitutive_provider,
            ConstitutiveProvider,
        ):
            raise TypeError(
                "constitutive_provider must implement ConstitutiveProvider"
            )

        self.displacement_recovery = displacement_recovery
        self.constitutive_provider = constitutive_provider

    def strain(
        self,
        *,
        x: float,
        y: float,
        z: float,
    ) -> StrainState:
        """
        Recover the complete 6-component small-strain vector.
        """

        amplitudes = self.displacement_recovery.amplitudes(
            float(x)
        ).values

        amplitude_dx = (
            self.displacement_recovery.amplitude_derivatives(
                float(x)
            ).values
        )

        basis = self.displacement_recovery.basis

        strain = np.zeros(
            6,
            dtype=float,
        )

        for tau in range(
            1,
            basis.size + 1,
        ):
            row = tau - 1

            F = float(
                basis.value(
                    tau,
                    float(y),
                    float(z),
                    x=float(x),
                )
            )

            Fy = float(
                basis.derivative(
                    tau,
                    "y",
                    float(y),
                    float(z),
                    x=float(x),
                )
            )

            Fz = float(
                basis.derivative(
                    tau,
                    "z",
                    float(y),
                    float(z),
                    x=float(x),
                )
            )

            ux, uy, uz = amplitudes[row, :]
            ux_x, uy_x, uz_x = amplitude_dx[row, :]

            strain[0] += F * ux_x
            strain[1] += Fy * uy
            strain[2] += Fz * uz

            strain[3] += Fz * uy + Fy * uz
            strain[4] += Fz * ux + F * uz_x
            strain[5] += Fy * ux + F * uy_x

        if not np.all(np.isfinite(strain)):
            raise RuntimeError(
                "recovered strain contains non-finite values"
            )

        return StrainState(
            x=float(x),
            y=float(y),
            z=float(z),
            strain=strain,
        )

    def stress(
        self,
        *,
        x: float,
        y: float,
        z: float,
        domain_id: Hashable,
    ) -> StressState:
        """
        Recover strain and stress in one transverse material domain.

        ``domain_id`` is explicit because a physical point may belong to a
        particular CSF sub-domain/material region. The recovery layer does not
        guess or duplicate the section-topology logic.
        """

        strain_state = self.strain(
            x=x,
            y=y,
            z=z,
        )

        C = np.asarray(
            self.constitutive_provider.matrix(
                x=float(x),
                domain_id=domain_id,
                y=float(y),
                z=float(z),
            ),
            dtype=float,
        )

        if C.shape != (6, 6):
            raise ValueError(
                "constitutive provider must return a 6-by-6 matrix"
            )

        if not np.all(np.isfinite(C)):
            raise ValueError(
                "constitutive matrix contains non-finite values"
            )

        stress = C @ strain_state.strain

        if not np.all(np.isfinite(stress)):
            raise RuntimeError(
                "recovered stress contains non-finite values"
            )

        return StressState(
            x=float(x),
            y=float(y),
            z=float(z),
            domain_id=domain_id,
            strain=strain_state.strain.copy(),
            stress=np.asarray(stress, dtype=float),
            constitutive_matrix=C,
        )

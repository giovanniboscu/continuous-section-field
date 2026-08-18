"""
Generic CUF fundamental nucleus in weak form.

This module is the mechanical consumer of the generalized sectional field J(x).

    J^{mn}_{tau,phi s,xi}(x)
        -> weak-form CUF nucleus K_ij^{tau s}(x)

The nucleus is generated from the complete 3D small-strain kinematics in Voigt
order (xx, yy, zz, yz, xz, xy).  No prismatic-section, isotropic-material,
benchmark, load, boundary-condition, or longitudinal-discretization assumption
is introduced here.

The x-independent structural definitions are kept separate from the numerical
evaluation of J(x), so the longitudinal solver can retain J(x) inside its own
quadrature.
"""

from dataclasses import dataclass
from typing import Any, Tuple


# =============================================================================
# Generic CUF fundamental nucleus in weak form
# =============================================================================

@dataclass(frozen=True)
class StrainContribution:
    """
    One kinematic contribution to a Voigt strain component.

    Parameters
    ----------
    displacement_component:
        0 -> u_x, 1 -> u_y, 2 -> u_z.

    transverse_derivative:
        None, "y", or "z", identifying the transverse factor applied to the
        CUF basis function.

    longitudinal_order:
        0 or 1, identifying whether the corresponding longitudinal amplitude
        is used directly or differentiated once with respect to x.
    """

    displacement_component: int
    transverse_derivative: str | None
    longitudinal_order: int


@dataclass(frozen=True)
class JSignature:
    """Complete generalized sectional-coefficient request."""

    tau: int
    test_derivative: str | None
    s: int
    trial_derivative: str | None
    m: int
    n: int


@dataclass(frozen=True)
class NucleusTermDefinition:
    """
    One x-independent weak-form term definition of a CUF nucleus block.

    The generalized J signature and the longitudinal derivative orders are
    structural.  The actual coefficient value J(x) is evaluated only when the
    solver requests it at a physical longitudinal coordinate.
    """

    signature: JSignature
    test_x_order: int
    trial_x_order: int


@dataclass(frozen=True)
class NucleusTerm:
    """
    One weak-form term of a CUF fundamental-nucleus block.

    ``coefficient`` is J(x) evaluated at the requested longitudinal position.
    ``test_x_order`` and ``trial_x_order`` describe the longitudinal
    derivatives acting on the virtual/test and source/trial amplitudes.
    """

    coefficient: float
    signature: JSignature
    test_x_order: int
    trial_x_order: int


@dataclass(frozen=True)
class NucleusBlock:
    """
    One K_ij^{tau s}(x) weak-form block.

    For a fully general 6x6 constitutive matrix, a block can contain several
    independent J contributions. No isotropic sparsity is assumed.
    """

    test_component: int
    trial_component: int
    terms: Tuple[NucleusTerm, ...]


class FundamentalNucleusProvider:
    """
    Build the complete CUF fundamental nucleus from generalized J coefficients.

    The construction is generated directly from the 3D small-strain
    kinematics in Voigt order

        (xx, yy, zz, yz, xz, xy)

    rather than from an isotropic hard-coded matrix pattern.

    Therefore:
    - geometry may vary with x through the SectionProvider used by J;
    - material may vary with x, y, z;
    - the constitutive matrix may be fully populated;
    - the CUF basis is arbitrary;
    - no prismatic, rectangular, isotropic, or benchmark assumption appears
      in the nucleus API.

    The returned object is a WEAK-FORM nucleus. Longitudinal integration by
    parts and strong-form discretization belong to the longitudinal solver.
    """

    # Each Voigt strain row is represented by one or more kinematic
    # contributions. The first index below is the 1-based constitutive/Voigt
    # strain index m or n.
    _STRAIN_KINEMATICS = {
        # epsilon_xx = F * u_x,x
        1: (
            StrainContribution(0, None, 1),
        ),

        # epsilon_yy = F,y * u_y
        2: (
            StrainContribution(1, "y", 0),
        ),

        # epsilon_zz = F,z * u_z
        3: (
            StrainContribution(2, "z", 0),
        ),

        # gamma_yz = F,z * u_y + F,y * u_z
        4: (
            StrainContribution(1, "z", 0),
            StrainContribution(2, "y", 0),
        ),

        # gamma_xz = F,z * u_x + F * u_z,x
        5: (
            StrainContribution(0, "z", 0),
            StrainContribution(2, None, 1),
        ),

        # gamma_xy = F,y * u_x + F * u_y,x
        6: (
            StrainContribution(0, "y", 0),
            StrainContribution(1, None, 1),
        ),
    }

    def __init__(self, sectional_coefficients: Any) -> None:
        """
        Parameters
        ----------
        sectional_coefficients:
            Any object exposing the generalized method

                J(
                    x=...,
                    tau=...,
                    test_derivative=...,
                    s=...,
                    trial_derivative=...,
                    m=...,
                    n=...
                )

            SectionalCoefficientProvider is the normal bridge implementation,
            but the loose contract also allows independent verification
            backends.
        """

        if sectional_coefficients is None:
            raise ValueError("sectional_coefficients must not be None")

        if not hasattr(sectional_coefficients, "J"):
            raise TypeError("sectional_coefficients must expose J(...)")

        self.sectional_coefficients = sectional_coefficients

    @classmethod
    def strain_kinematics(
        cls,
        voigt_index: int,
    ) -> Tuple[StrainContribution, ...]:
        """Return the generic kinematic contributions of one Voigt strain."""

        if voigt_index not in cls._STRAIN_KINEMATICS:
            raise IndexError("voigt_index must be in 1..6")

        return cls._STRAIN_KINEMATICS[voigt_index]

    def K_block_structure(
        self,
        *,
        tau: int,
        s: int,
        test_component: int,
        trial_component: int,
    ) -> Tuple[NucleusTermDefinition, ...]:
        """
        Return the x-independent structural definition of one K block.

        No sectional coefficient is evaluated here.  This is the API used by
        the longitudinal finite-element layer when J(x) must remain inside the
        longitudinal integral.
        """

        self._validate_component(test_component)
        self._validate_component(trial_component)

        definitions = []

        for m in range(1, 7):
            for test_kinematic in self.strain_kinematics(m):

                if test_kinematic.displacement_component != test_component:
                    continue

                for n in range(1, 7):
                    for trial_kinematic in self.strain_kinematics(n):

                        if (
                            trial_kinematic.displacement_component
                            != trial_component
                        ):
                            continue

                        definitions.append(
                            NucleusTermDefinition(
                                signature=JSignature(
                                    tau=tau,
                                    test_derivative=(
                                        test_kinematic.transverse_derivative
                                    ),
                                    s=s,
                                    trial_derivative=(
                                        trial_kinematic.transverse_derivative
                                    ),
                                    m=m,
                                    n=n,
                                ),
                                test_x_order=(
                                    test_kinematic.longitudinal_order
                                ),
                                trial_x_order=(
                                    trial_kinematic.longitudinal_order
                                ),
                            )
                        )

        return tuple(definitions)

    def K_block(
        self,
        *,
        x: float,
        tau: int,
        s: int,
        test_component: int,
        trial_component: int,
    ) -> NucleusBlock:
        """
        Return one fully general weak-form K_ij^{tau s}(x) block.
        """

        definitions = self.K_block_structure(
            tau=tau,
            s=s,
            test_component=test_component,
            trial_component=trial_component,
        )

        terms = []

        for definition in definitions:
            signature = definition.signature

            value = self.sectional_coefficients.J(
                x=x,
                tau=signature.tau,
                test_derivative=signature.test_derivative,
                s=signature.s,
                trial_derivative=signature.trial_derivative,
                m=signature.m,
                n=signature.n,
            )

            terms.append(
                NucleusTerm(
                    coefficient=float(value),
                    signature=signature,
                    test_x_order=definition.test_x_order,
                    trial_x_order=definition.trial_x_order,
                )
            )

        return NucleusBlock(
            test_component=test_component,
            trial_component=trial_component,
            terms=tuple(terms),
        )

    def K(
        self,
        *,
        x: float,
        tau: int,
        s: int,
    ) -> Tuple[Tuple[NucleusBlock, ...], ...]:
        """
        Return the complete 3-by-3 weak-form fundamental nucleus.

        The matrix ordering is (x, y, z) on both test and trial sides.
        """

        return tuple(
            tuple(
                self.K_block(
                    x=x,
                    tau=tau,
                    s=s,
                    test_component=i,
                    trial_component=j,
                )
                for j in range(3)
            )
            for i in range(3)
        )

    @staticmethod
    def _validate_component(component: int) -> None:
        if component not in (0, 1, 2):
            raise IndexError("displacement component must be 0, 1, or 2")

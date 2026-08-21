"""
Generic constitutive layer for the CSF-CUF bridge.

This module contains:
- ScalarField
- ConstitutiveProvider
- IsotropicEGConstitutive
- ConstitutiveMatrixTransform
- TransformedConstitutiveProvider
- condense_constitutive_matrix
- condensed_constitutive_coefficient
- CondensedCoefficientTransform
- ConstitutiveModel

It defines local constitutive data C^k(x,y,z) and theory-level constitutive
transformations independently of section geometry, CUF basis, transverse
integration, loads, boundary conditions, and longitudinal solution.

The constitutive transformation layer is intentionally generic.  A benchmark
or a beam theory may select a transformation, but this module does not infer
one from geometry, CUF order, loading, or boundary conditions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Hashable, Sequence

import numpy as np


ScalarField = Callable[[float, Hashable, float, float], float]
ConstitutiveMatrixTransform = Callable[
    [np.ndarray, float, Hashable, float, float],
    np.ndarray,
]


# =============================================================================
# Validation helpers
# =============================================================================

def _validated_constitutive_matrix(
    matrix: np.ndarray,
    *,
    name: str = "constitutive matrix",
) -> np.ndarray:
    C = np.asarray(matrix, dtype=float)

    if C.shape != (6, 6):
        raise ValueError(
            f"{name} must have shape (6, 6), got {C.shape}"
        )

    if not np.all(np.isfinite(C)):
        raise ValueError(
            f"{name} must contain only finite values"
        )

    return C


def _validated_component_indices(
    indices: Sequence[int],
    *,
    name: str,
) -> tuple[int, ...]:
    values = tuple(int(index) for index in indices)

    if not values:
        raise ValueError(f"{name} must not be empty")

    if len(set(values)) != len(values):
        raise ValueError(
            f"{name} must not contain duplicate indices"
        )

    invalid = tuple(
        index
        for index in values
        if index < 0 or index >= 6
    )
    if invalid:
        raise IndexError(
            f"{name} contains indices outside 0..5: {invalid}"
        )

    return values


# =============================================================================
# Generic constitutive reduction
# =============================================================================

def condense_constitutive_matrix(
    matrix: np.ndarray,
    *,
    retained_indices: Sequence[int],
    eliminated_indices: Sequence[int],
) -> np.ndarray:
    """
    Return the exact Schur-complement constitutive matrix.

    The full local constitutive relation is

        sigma = C epsilon.

    Split the strain/stress components into retained components ``r`` and
    eliminated components ``e``.  Imposing

        sigma_e = 0

    gives

        epsilon_e = -C_ee^{-1} C_er epsilon_r

    and therefore

        sigma_r = Q_rr epsilon_r,

    with

        Q_rr = C_rr - C_re C_ee^{-1} C_er.

    This function evaluates that algebraic reduction only.  It does not embed
    Q_rr back into a 6-by-6 matrix, does not discard solver unknowns, and does
    not select a beam theory.  Those are separate modelling decisions.

    Parameters
    ----------
    matrix:
        Full 6-by-6 local constitutive matrix in the CSF-CUF Voigt order.

    retained_indices:
        Zero-based Voigt component indices retained in the reduced relation.

    eliminated_indices:
        Zero-based Voigt component indices whose stresses are constrained to
        zero during the constitutive condensation.

    Returns
    -------
    numpy.ndarray
        Reduced matrix Q_rr, with row/column order equal to
        ``retained_indices``.
    """
    C = _validated_constitutive_matrix(matrix)

    retained = _validated_component_indices(
        retained_indices,
        name="retained_indices",
    )
    eliminated = _validated_component_indices(
        eliminated_indices,
        name="eliminated_indices",
    )

    overlap = set(retained).intersection(eliminated)
    if overlap:
        raise ValueError(
            "retained_indices and eliminated_indices must be disjoint; "
            f"overlap={tuple(sorted(overlap))}"
        )

    C_rr = C[np.ix_(retained, retained)]
    C_re = C[np.ix_(retained, eliminated)]
    C_er = C[np.ix_(eliminated, retained)]
    C_ee = C[np.ix_(eliminated, eliminated)]

    try:
        correction = C_re @ np.linalg.solve(
            C_ee,
            C_er,
        )
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "eliminated constitutive block C_ee is singular and cannot "
            "be statically condensed"
        ) from exc

    Q_rr = C_rr - correction

    if not np.all(np.isfinite(Q_rr)):
        raise ValueError(
            "condensed constitutive matrix contains non-finite values"
        )

    return np.asarray(Q_rr, dtype=float)



def condensed_constitutive_coefficient(
    matrix: np.ndarray,
    *,
    target_index: int,
    eliminated_indices: Sequence[int],
) -> float:
    """
    Return one Schur-reduced constitutive coefficient.

    Let ``t`` denote one retained strain/stress component and ``e`` the set of
    components whose stresses are constrained to zero for the constitutive
    reduction.  Then

        Q_tt = C_tt - C_te C_ee^{-1} C_et.

    Only the scalar coefficient Q_tt is returned.  No other coefficient of the
    supplied 6-by-6 constitutive matrix is changed.

    This operation is independent of beam geometry, CUF order, loading,
    boundary conditions and longitudinal discretization.  A theory that needs
    such a reduced coefficient must select it explicitly.
    """
    C = _validated_constitutive_matrix(matrix)

    target = int(target_index)
    if target < 0 or target >= 6:
        raise IndexError(
            f"target_index must be in 0..5, got {target}"
        )

    eliminated = _validated_component_indices(
        eliminated_indices,
        name="eliminated_indices",
    )

    if target in eliminated:
        raise ValueError(
            "target_index must not also be an eliminated index"
        )

    C_ee = C[np.ix_(eliminated, eliminated)]
    C_te = C[target, list(eliminated)]
    C_et = C[list(eliminated), target]

    try:
        solved = np.linalg.solve(
            C_ee,
            C_et,
        )
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "eliminated constitutive block C_ee is singular and cannot "
            "be statically condensed"
        ) from exc

    value = float(
        C[target, target]
        - C_te @ solved
    )

    if not np.isfinite(value):
        raise ValueError(
            "condensed constitutive coefficient is not finite"
        )

    return value


@dataclass(frozen=True)
class CondensedCoefficientTransform:
    """
    Explicitly replace one diagonal coefficient by its Schur-reduced value.

    Given a full matrix C, this transformation computes one scalar Q_tt through
    ``condensed_constitutive_coefficient`` and returns a copy of C in which only

        C[t,t] -> Q_tt

    is replaced.  Every other matrix entry is preserved exactly.

    The class does not infer the target or eliminated components.  They are a
    theory-level choice supplied by the caller.
    """

    target_index: int
    eliminated_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        target = int(self.target_index)
        if target < 0 or target >= 6:
            raise IndexError(
                f"target_index must be in 0..5, got {target}"
            )

        eliminated = _validated_component_indices(
            self.eliminated_indices,
            name="eliminated_indices",
        )

        if target in eliminated:
            raise ValueError(
                "target_index must not also be an eliminated index"
            )

        object.__setattr__(
            self,
            "target_index",
            target,
        )
        object.__setattr__(
            self,
            "eliminated_indices",
            eliminated,
        )

    def __call__(
        self,
        matrix: np.ndarray,
        x: float,
        domain_id: Hashable,
        y: float,
        z: float,
    ) -> np.ndarray:
        # x, domain_id, y and z are intentionally accepted because this object
        # conforms to ConstitutiveMatrixTransform.  The local matrix already
        # contains any spatial/material dependency supplied by the base provider.
        C = _validated_constitutive_matrix(matrix)

        value = condensed_constitutive_coefficient(
            C,
            target_index=self.target_index,
            eliminated_indices=self.eliminated_indices,
        )

        result = np.array(
            C,
            dtype=float,
            copy=True,
        )
        result[
            self.target_index,
            self.target_index,
        ] = value

        return result



# =============================================================================
# Constitutive provider
# =============================================================================

class ConstitutiveProvider(ABC):
    """Generic provider of local sectional constitutive data."""

    @abstractmethod
    def matrix(
        self,
        x: float,
        domain_id: Hashable,
        y: float,
        z: float,
    ) -> np.ndarray:
        """Return the local 6-by-6 constitutive matrix C^k(x, y, z)."""
        raise NotImplementedError

    def coefficient(
        self,
        x: float,
        domain_id: Hashable,
        m: int,
        n: int,
        y: float,
        z: float,
    ) -> float:
        """Return C_mn^k(x, y, z) using 1-based CUF indices."""
        if not 1 <= m <= 6:
            raise IndexError(
                f"constitutive index m must be in 1..6, got {m}"
            )
        if not 1 <= n <= 6:
            raise IndexError(
                f"constitutive index n must be in 1..6, got {n}"
            )

        C = _validated_constitutive_matrix(
            self.matrix(
                x=x,
                domain_id=domain_id,
                y=y,
                z=z,
            )
        )

        return float(C[m - 1, n - 1])



@dataclass(frozen=True)
class ConstitutiveModel:
    """
    Keep constitutive roles explicit.

    ``stiffness_provider`` supplies the constitutive coefficients used by the
    variational/nuclear stiffness construction.

    ``recovery_provider`` supplies the constitutive coefficients used when a
    theory defines direct constitutive stress recovery.

    For the ordinary unreduced case both roles may reference the same provider.
    A theory-specific reduction can instead provide distinct providers without
    changing geometry, the CUF nucleus, the sectional integrator, or the solver.

    This container introduces no rule for selecting either provider.
    """

    stiffness_provider: ConstitutiveProvider
    recovery_provider: ConstitutiveProvider

    def __post_init__(self) -> None:
        if not isinstance(
            self.stiffness_provider,
            ConstitutiveProvider,
        ):
            raise TypeError(
                "stiffness_provider must implement ConstitutiveProvider"
            )

        if not isinstance(
            self.recovery_provider,
            ConstitutiveProvider,
        ):
            raise TypeError(
                "recovery_provider must implement ConstitutiveProvider"
            )


@dataclass(frozen=True)
class TransformedConstitutiveProvider(ConstitutiveProvider):
    """
    Decorate any constitutive provider with an explicit matrix transformation.

    The wrapped provider remains responsible for the physical local material
    law C^k(x,y,z).  ``transform`` receives that matrix together with the same
    local coordinates and domain identifier, and must return a 6-by-6 matrix.

    This separates two concepts that must not be conflated:

        material law
            C^k(x,y,z)

        theory-level constitutive specialization
            T[C^k](x,y,z)

    No transformation is activated implicitly from CUF order, geometry,
    loading, or boundary conditions.
    """

    base_provider: ConstitutiveProvider
    transform: ConstitutiveMatrixTransform

    def __post_init__(self) -> None:
        if not isinstance(
            self.base_provider,
            ConstitutiveProvider,
        ):
            raise TypeError(
                "base_provider must implement ConstitutiveProvider"
            )

        if not callable(self.transform):
            raise TypeError(
                "transform must be callable"
            )

    def matrix(
        self,
        x: float,
        domain_id: Hashable,
        y: float,
        z: float,
    ) -> np.ndarray:
        x_value = float(x)
        y_value = float(y)
        z_value = float(z)

        base = _validated_constitutive_matrix(
            self.base_provider.matrix(
                x=x_value,
                domain_id=domain_id,
                y=y_value,
                z=z_value,
            ),
            name="base constitutive matrix",
        )

        transformed = self.transform(
            np.array(base, dtype=float, copy=True),
            x_value,
            domain_id,
            y_value,
            z_value,
        )

        return _validated_constitutive_matrix(
            transformed,
            name="transformed constitutive matrix",
        ).copy()


class IsotropicEGConstitutive(ConstitutiveProvider):
    """Two-field isotropic constitutive closure based on E and G."""

    def __init__(
        self,
        E_field: ScalarField,
        G_field: ScalarField,
    ) -> None:
        if not callable(E_field):
            raise TypeError(
                "E_field must be callable"
            )
        if not callable(G_field):
            raise TypeError(
                "G_field must be callable"
            )

        self._E_field = E_field
        self._G_field = G_field

    def matrix(
        self,
        x: float,
        domain_id: Hashable,
        y: float,
        z: float,
    ) -> np.ndarray:
        E = float(
            self._E_field(
                x,
                domain_id,
                y,
                z,
            )
        )
        G = float(
            self._G_field(
                x,
                domain_id,
                y,
                z,
            )
        )

        self._validate_fields(E, G)

        denominator = 3.0 * G - E
        lam = G * (E - 2.0 * G) / denominator
        normal = lam + 2.0 * G

        C = np.zeros((6, 6), dtype=float)

        C[0, 0] = normal
        C[1, 1] = normal
        C[2, 2] = normal

        C[0, 1] = C[1, 0] = lam
        C[0, 2] = C[2, 0] = lam
        C[1, 2] = C[2, 1] = lam

        C[3, 3] = G
        C[4, 4] = G
        C[5, 5] = G

        return C

    @staticmethod
    def _validate_fields(
        E: float,
        G: float,
    ) -> None:
        if not np.isfinite(E):
            raise ValueError(
                "E must be finite"
            )
        if not np.isfinite(G):
            raise ValueError(
                "G must be finite"
            )
        if E <= 0.0:
            raise ValueError(
                f"E must be positive, got {E}"
            )
        if G <= 0.0:
            raise ValueError(
                f"G must be positive, got {G}"
            )

        denominator = 3.0 * G - E
        scale = max(
            1.0,
            abs(E),
            abs(G),
        )
        tolerance = (
            np.finfo(float).eps
            * scale
        )

        if abs(denominator) <= tolerance:
            raise ValueError(
                "invalid E-G constitutive closure: 3*G - E is zero"
            )

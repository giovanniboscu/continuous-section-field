"""
CSF-CUF bridge.

This module defines the reusable interface between the Continuous Section
Field (CSF) representation and the Carrera Unified Formulation (CUF).

Initial implementation
----------------------
This first development step implements only the constitutive layer:

    CSF constitutive fields
        -> ConstitutiveProvider
        -> C^k(x, y, z)
        -> C_mn^k(x, y, z)

The CUF basis, generalized sectional coefficients J, fundamental nucleus K,
and longitudinal solver are intentionally outside this first implementation.
"""

from abc import ABC, abstractmethod
from typing import Callable, Hashable

import numpy as np


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

ScalarField = Callable[[float, Hashable, float, float], float]


# ---------------------------------------------------------------------------
# Constitutive provider
# ---------------------------------------------------------------------------

class ConstitutiveProvider(ABC):
    """
    Generic provider of sectional constitutive data for the CSF-CUF bridge.

    The provider exposes the local constitutive matrix

        C^k(x, y, z)

    associated with a sectional domain ``k``.

    Constitutive indices ``m`` and ``n`` follow the mathematical CUF
    convention and are therefore 1-based:

        m, n = 1, ..., 6

    NumPy indexing remains an internal implementation detail.
    """

    @abstractmethod
    def matrix(
        self,
        x: float,
        domain_id: Hashable,
        y: float,
        z: float,
    ) -> np.ndarray:
        """
        Return the local 6-by-6 constitutive matrix C^k(x, y, z).

        Parameters
        ----------
        x:
            Longitudinal coordinate.

        domain_id:
            Identifier of the transverse CSF domain.

        y, z:
            Transverse coordinates.

        Returns
        -------
        numpy.ndarray
            Constitutive matrix with shape (6, 6).
        """
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
        """
        Return one constitutive coefficient C_mn^k(x, y, z).

        ``m`` and ``n`` use the 1-based CUF notation.
        """

        if not 1 <= m <= 6:
            raise IndexError(
                f"constitutive index m must be in 1..6, got {m}"
            )

        if not 1 <= n <= 6:
            raise IndexError(
                f"constitutive index n must be in 1..6, got {n}"
            )

        C = self.matrix(
            x=x,
            domain_id=domain_id,
            y=y,
            z=z,
        )

        if C.shape != (6, 6):
            raise ValueError(
                "constitutive provider must return a 6-by-6 matrix"
            )

        return float(C[m - 1, n - 1])


# ---------------------------------------------------------------------------
# Isotropic E-G constitutive specialization
# ---------------------------------------------------------------------------

class IsotropicEGConstitutive(ConstitutiveProvider):
    """
    Two-field isotropic constitutive closure based on E and G.

    The two CSF fields are supplied independently:

        E = E(x, domain_id, y, z)
        G = G(x, domain_id, y, z)

    The constitutive closure is

        lambda = G * (E - 2 G) / (3 G - E)

        C11 = C22 = C33 = lambda + 2 G

        C12 = C13 = C23 = lambda

        C44 = C55 = C66 = G

    This corresponds to the constitutive specialization documented in

        docs/model/csf_cuf_sectional_constitutive_interface.md

    It is not intended to represent a fully general anisotropic material.
    """

    def __init__(
        self,
        E_field: ScalarField,
        G_field: ScalarField,
    ) -> None:
        if not callable(E_field):
            raise TypeError("E_field must be callable")

        if not callable(G_field):
            raise TypeError("G_field must be callable")

        self._E_field = E_field
        self._G_field = G_field

    def matrix(
        self,
        x: float,
        domain_id: Hashable,
        y: float,
        z: float,
    ) -> np.ndarray:
        """
        Evaluate and return C^k(x, y, z).
        """

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

        lam = (
            G
            * (E - 2.0 * G)
            / denominator
        )

        normal = lam + 2.0 * G

        C = np.zeros(
            (6, 6),
            dtype=float,
        )

        # Normal terms
        C[0, 0] = normal
        C[1, 1] = normal
        C[2, 2] = normal

        # Normal coupling terms
        C[0, 1] = lam
        C[1, 0] = lam

        C[0, 2] = lam
        C[2, 0] = lam

        C[1, 2] = lam
        C[2, 1] = lam

        # Shear terms
        C[3, 3] = G
        C[4, 4] = G
        C[5, 5] = G

        return C

    @staticmethod
    def _validate_fields(
        E: float,
        G: float,
    ) -> None:
        """
        Validate the two constitutive fields before matrix construction.
        """

        if not np.isfinite(E):
            raise ValueError("E must be finite")

        if not np.isfinite(G):
            raise ValueError("G must be finite")

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
                "invalid E-G constitutive closure: "
                "3*G - E is zero"
            )

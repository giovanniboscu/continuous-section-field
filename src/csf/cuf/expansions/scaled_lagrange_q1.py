# Version: CSF-CUF scaled Lagrange Q1 ContinuousSectionField-ready v25.1 - 2026-08-30
"""Scaled bilinear Lagrange Q1 transverse expansion."""

import math
import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    register_cuf_basis_plugin,
)
from csf.cuf.numerics import transverse_scales


# =============================================================================
# STEP 2
# Implement the CUFBasis interface
# =============================================================================

class ScaledLagrangeQ1Basis(CUFBasis):
    """
    Bilinear Lagrange Q1 basis in scaled transverse coordinates.

    The physical transverse coordinates are scaled as:

        Y = y / y_scale
        Z = z / z_scale

    The four Q1 functions correspond to the four corners of the
    reference square [-1, 1] x [-1, 1].

    Stable term ordering:

        tau = 1 -> (-1, -1)
        tau = 2 -> (+1, -1)
        tau = 3 -> (+1, +1)
        tau = 4 -> (-1, +1)

    This ordering must remain unchanged because each tau identifies
    one group of generalized displacement unknowns in the CUF system.
    """

    # Signs associated with the four reference corners.
    _SIGNS = (
        (-1.0, -1.0),
        (+1.0, -1.0),
        (+1.0, +1.0),
        (-1.0, +1.0),
    )

    def __init__(
        self,
        *,
        y_scale: float,
        z_scale: float,
    ) -> None:
        """
        Construct the Q1 basis using fixed transverse scales.

        The scales are obtained from the complete CSF model by the
        plugin builder. They are not read from the case YAML.
        """

        y_scale = float(y_scale)
        z_scale = float(z_scale)

        # A zero or invalid scale would make the scaled coordinates
        # and their derivatives undefined.
        if not math.isfinite(y_scale) or y_scale <= 0.0:
            raise ValueError(
                "y_scale must be positive and finite"
            )

        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError(
                "z_scale must be positive and finite"
            )

        self._y_scale = y_scale
        self._z_scale = z_scale

    @property
    def order(self) -> int:
        """
        Return the polynomial family order.

        This plugin implements Q1 only, so its order is always one.
        """

        return 1

    @property
    def size(self) -> int:
        """
        Return the number of transverse expansion functions.

        A bilinear Q1 basis has exactly four functions.
        """

        return 4

    @property
    def scales(self) -> tuple[float, float]:
        """Return the transverse numerical scales."""

        return self._y_scale, self._z_scale

    def power_coefficients(self) -> np.ndarray:
        """Return all Q1 functions in ascending physical y,z powers.

        This optional method opts the expansion into the generic,
        self-contained displacement-checkpoint format.  Future polynomial
        expansions can expose the same representation without changing the
        CUFBasis core interface.
        """

        coefficients = np.zeros((self.size, 2, 2), dtype=float)
        for tau, (sign_y, sign_z) in enumerate(self._SIGNS):
            coefficients[tau, :, :] = 0.25 * np.asarray(
                (
                    (1.0, sign_z / self._z_scale),
                    (
                        sign_y / self._y_scale,
                        sign_y
                        * sign_z
                        / (self._y_scale * self._z_scale),
                    ),
                ),
                dtype=float,
            )
        return coefficients

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """
        Evaluate one Q1 function at the physical point (y, z).

        The current expansion does not depend explicitly on x.
        The optional x argument is accepted to satisfy the common
        CUFBasis interface.
        """

        sy, sz = self._signs(tau)

        # Convert physical coordinates to scaled coordinates.
        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale

        # General expression for all four bilinear Q1 functions:
        #
        #     F_tau = 1/4 (1 + sy*Y) (1 + sz*Z)
        #
        return float(
            0.25
            * (1.0 + sy * Y)
            * (1.0 + sz * Z)
        )

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """
        Evaluate one physical transverse derivative.

        The factors 1/y_scale and 1/z_scale are required by the
        chain rule:

            dY/dy = 1/y_scale
            dZ/dz = 1/z_scale
        """

        sy, sz = self._signs(tau)

        Y = float(y) / self._y_scale
        Z = float(z) / self._z_scale

        if direction == "y":
            # dF_tau/dy =
            #     1/4 * sy * (1 + sz*Z) / y_scale
            return float(
                0.25
                * sy
                * (1.0 + sz * Z)
                / self._y_scale
            )

        if direction == "z":
            # dF_tau/dz =
            #     1/4 * sz * (1 + sy*Y) / z_scale
            return float(
                0.25
                * sz
                * (1.0 + sy * Y)
                / self._z_scale
            )

        raise ValueError(
            "direction must be 'y' or 'z'"
        )

    def _signs(
        self,
        tau: int,
    ) -> tuple[float, float]:
        """
        Validate tau and return its reference-corner signs.

        CUF uses one-based term numbering, so valid indices are
        tau = 1, 2, 3, 4.
        """

        if not isinstance(tau, int):
            raise TypeError(
                "tau must be an integer"
            )

        if not 1 <= tau <= self.size:
            raise IndexError(
                f"tau must be in 1..{self.size}, got {tau}"
            )

        return self._SIGNS[tau - 1]


# =============================================================================
# STEP 3
# Validate expansion-specific YAML options
# =============================================================================

def _reject_options(options):
    """
    Reject unsupported cuf.basis_options.

    The scaled Q1 implementation obtains its scales directly from the
    CSF section provider and therefore requires no user parameters.
    """

    if options:
        raise ValueError(
            "scaled_lagrange_q1 does not accept "
            "cuf.basis_options; "
            f"received {sorted(options)}"
        )


# =============================================================================
# STEP 4
# Build the basis selected by the YAML file
# =============================================================================

def _build(*, order, section_provider, continuous_section_field, options):
    """
    Construct a complete ScaledLagrangeQ1Basis instance.

    This function is called by the generic expansion registry.
    It validates the requested order, obtains the transverse scales
    from the CSF model, and returns the ready-to-use basis.
    """

    # STEP 4.1:
    # Reject expansion options because Q1 currently defines none.
    del continuous_section_field  # Available by contract; unused by this expansion.
    _reject_options(options)

    # STEP 4.2:
    # This plugin represents Q1 only.
    if not isinstance(order, int):
        raise TypeError(
            "scaled_lagrange_q1 order must be an integer"
        )

    if order != 1:
        raise ValueError(
            "scaled_lagrange_q1 requires cuf.order = 1"
        )

    # STEP 4.3:
    # Obtain fixed numerical scales from the complete CSF geometry.
    # The YAML does not need to provide these values.
    y_scale, z_scale = transverse_scales(
        section_provider
    )

    # STEP 4.4:
    # Return the concrete basis consumed by the CUF core.
    return ScaledLagrangeQ1Basis(
        y_scale=y_scale,
        z_scale=z_scale,
    )


# =============================================================================
# STEP 5
# Declare the minimum sectional quadrature order
# =============================================================================

def _section_gauss_minimum(basis):
    """
    Return the conservative minimum sectional Gauss order.

    Each Q1 function contains the terms:

        1, Y, Z, Y*Z

    A product of two Q1 functions can therefore contain Y^2*Z^2.
    A minimum order of three is retained as a conservative requirement.

    A larger order explicitly requested in the YAML is never reduced.
    """

    # Confirm that the registry passed the expected basis.
    if not isinstance(basis, ScaledLagrangeQ1Basis):
        raise TypeError(
            "scaled_lagrange_q1 received an incompatible basis"
        )

    return 3


# =============================================================================
# STEP 6
# Declare the transverse contribution to longitudinal quadrature
# =============================================================================

def _longitudinal_transverse_degree(basis):
    """
    Return the conservative longitudinal polynomial-degree contribution.

    A Q1 function contains the bilinear product Y*Z. If both transverse
    coordinates vary affinely along x, one basis function may acquire
    degree two in x. The product of two basis functions may therefore
    acquire degree four in x.

    The contribution is kept conservative for both variable and
    constant sections. This follows the behavior of the other existing
    expansion plugins.
    """

    # Confirm that the registry passed the expected basis.
    if not isinstance(basis, ScaledLagrangeQ1Basis):
        raise TypeError(
            "scaled_lagrange_q1 received an incompatible basis"
        )

    return 4


# =============================================================================
# STEP 7
# Register the expansion
# =============================================================================

register_cuf_basis_plugin(
    CUFBasisPlugin(
        # This is the exact name used in the case YAML.
        name="scaled_lagrange_q1",

        # Construct the concrete basis.
        builder=_build,

        # Provide the sectional quadrature requirement.
        section_gauss_minimum=_section_gauss_minimum,

        # Provide the longitudinal quadrature contribution.
        longitudinal_transverse_degree=(
            _longitudinal_transverse_degree
        ),
    )
)

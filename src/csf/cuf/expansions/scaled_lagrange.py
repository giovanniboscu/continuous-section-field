# Version: CSF-CUF scaled hierarchical Lagrange ContinuousSectionField-ready v25.2 - 2026-09-05
"""Scaled hierarchical Serendipity-Lagrange transverse expansion."""

import math
import numpy as np

from csf.cuf.core.basis import (
    CUFBasis,
    SerendipityLagrangeReferenceBasis,
)
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    register_cuf_basis_plugin,
)
from csf.cuf.numerics import transverse_scales


# =============================================================================
# STEP 2
# Adapt the hierarchical reference basis to scaled physical coordinates
# =============================================================================

class ScaledLagrangeBasis(CUFBasis):
    """
    Hierarchical Serendipity-Lagrange basis in scaled coordinates.

    The physical coordinates are converted to reference coordinates as:

        xi  = y / y_scale
        eta = z / z_scale

    The underlying reference basis constructs the complete hierarchy
    associated with the requested order.
    """

    def __init__(
        self,
        *,
        order: int,
        y_scale: float,
        z_scale: float,
    ) -> None:
        """Construct the scaled hierarchical basis."""

        if not isinstance(order, int):
            raise TypeError(
                "scaled_lagrange order must be an integer"
            )

        if order < 1:
            raise ValueError(
                "scaled_lagrange order must be >= 1"
            )

        y_scale = float(y_scale)
        z_scale = float(z_scale)

        if not math.isfinite(y_scale) or y_scale <= 0.0:
            raise ValueError(
                "y_scale must be positive and finite"
            )

        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError(
                "z_scale must be positive and finite"
            )

        # This object owns the hierarchical term definitions,
        # reference values, and reference derivatives.
        self._reference_basis = (
            SerendipityLagrangeReferenceBasis(order)
        )

        self._y_scale = y_scale
        self._z_scale = z_scale

        # Build the physical-coordinate power representation once.  The
        # solver-side displacement checkpoint consumes this optional generic
        # representation without knowing which concrete expansion produced
        # it.  Future polynomial expansions may expose the same
        # power_coefficients() method to opt into self-contained displacement
        # checkpoints; the CUFBasis core contract remains unchanged.
        self._power_coefficients = self._build_power_coefficients()
        self._power_coefficients.setflags(write=False)

    @property
    def order(self) -> int:
        """Return the hierarchy order requested by the YAML file."""

        return self._reference_basis.order

    @property
    def size(self) -> int:
        """Return the total number of transverse expansion functions."""

        return self._reference_basis.size

    @property
    def scales(self) -> tuple[float, float]:
        """Return the fixed transverse coordinate scales."""

        return self._y_scale, self._z_scale

    def definition(self, tau: int):
        """Return the hierarchical definition associated with tau."""

        return self._reference_basis.definition(tau)

    def power_coefficients(self) -> np.ndarray:
        """Return F_tau coefficients in ascending physical powers of y and z.

        The returned array has shape ``(size, order + 1, order + 1)`` and
        follows

            F_tau(y,z) = sum_{p,q} coefficients[tau-1,p,q] y**p z**q.

        This optional expansion-owned export is used only to create a
        self-contained displacement checkpoint.  It is deliberately outside
        the CUFBasis core interface so future non-polynomial expansions can
        choose a different checkpoint representation without changing core.
        """

        return self._power_coefficients.copy()

    @staticmethod
    def _reference_polynomial(order: int, *, reverse: bool = False):
        """Return p_order(mu) or p_order(-mu) in ascending powers.

        This representation is needed only by the optional physical-power
        checkpoint export.  The solver itself evaluates the reference
        polynomial directly from its roots in ``core.basis``.

        Coefficients are accumulated in extended precision before the final
        float64 cast.  The checkpoint must ultimately contain monomial
        coefficients, but coefficient construction should not add avoidable
        float64 roundoff.
        """

        roots = np.linspace(-1.0, 1.0, int(order), dtype=np.longdouble)
        coefficients = np.asarray((1.0,), dtype=np.longdouble)

        # Ascending powers: multiply successively by (mu - root).
        for root in roots:
            coefficients = np.convolve(
                coefficients,
                np.asarray((-root, 1.0), dtype=np.longdouble),
            )

        if reverse:
            coefficients = coefficients * np.power(
                np.longdouble(-1.0),
                np.arange(coefficients.size),
            )

        return np.asarray(coefficients, dtype=float)

    def _build_power_coefficients(self) -> np.ndarray:
        """Compile every hierarchy term into physical y,z power coefficients."""

        count = self.order + 1
        coefficients = np.zeros((self.size, count, count), dtype=float)

        for tau in range(1, self.size + 1):
            kind, r, side, n, m = self.definition(tau)

            if kind == "I":
                corner_signs = (
                    (-1.0, -1.0),
                    (+1.0, -1.0),
                    (+1.0, +1.0),
                    (-1.0, +1.0),
                )
                sign_y, sign_z = corner_signs[side - 1]
                reference = 0.25 * np.outer(
                    np.asarray((1.0, sign_y)),
                    np.asarray((1.0, sign_z)),
                )
            elif kind in ("IIA", "IIB"):
                if side == 1:
                    reference = 0.5 * np.outer(
                        self._reference_polynomial(r),
                        np.asarray((1.0, -1.0)),
                    )
                elif side == 2:
                    reference = 0.5 * np.outer(
                        np.asarray((1.0, +1.0)),
                        self._reference_polynomial(r),
                    )
                elif side == 3:
                    reference = 0.5 * np.outer(
                        self._reference_polynomial(r, reverse=True),
                        np.asarray((1.0, +1.0)),
                    )
                elif side == 4:
                    reference = 0.5 * np.outer(
                        np.asarray((1.0, -1.0)),
                        self._reference_polynomial(r, reverse=True),
                    )
                else:
                    raise RuntimeError("invalid SL edge index")
            elif kind == "III":
                reference = np.outer(
                    self._reference_polynomial(n),
                    self._reference_polynomial(m),
                )
            else:
                raise RuntimeError(
                    f"unsupported SL function type {kind!r}"
                )

            rows, columns = reference.shape
            y_scaling = np.power(
                self._y_scale,
                -np.arange(rows, dtype=float),
            )
            z_scaling = np.power(
                self._z_scale,
                -np.arange(columns, dtype=float),
            )
            coefficients[tau - 1, :rows, :columns] = (
                reference
                * y_scaling[:, None]
                * z_scaling[None, :]
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
        Evaluate one basis function at physical coordinates.

        The current expansion uses fixed global scales and therefore
        does not depend explicitly on x.
        """

        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        return float(
            self._reference_basis.value(
                tau,
                xi,
                eta,
            )
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

        The reference derivatives are converted through:

            d/dy = (1/y_scale) d/dxi
            d/dz = (1/z_scale) d/deta
        """

        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        if direction == "y":
            derivative_xi = (
                self._reference_basis.derivative(
                    tau,
                    "y",
                    xi,
                    eta,
                )
            )

            return float(
                derivative_xi / self._y_scale
            )

        if direction == "z":
            derivative_eta = (
                self._reference_basis.derivative(
                    tau,
                    "z",
                    xi,
                    eta,
                )
            )

            return float(
                derivative_eta / self._z_scale
            )

        raise ValueError(
            "direction must be 'y' or 'z'"
        )


# =============================================================================
# STEP 3
# Validate expansion-specific YAML options
# =============================================================================

def _reject_options(options):
    """
    Reject unsupported cuf.basis_options.

    The expansion obtains its transverse scales directly from the CSF
    geometry and currently requires no expansion-specific parameters.
    """

    if options:
        raise ValueError(
            "scaled_lagrange does not accept "
            "cuf.basis_options; "
            f"received {sorted(options)}"
        )


# =============================================================================
# STEP 4
# Build the basis selected by the YAML file
# =============================================================================

def _build(*, order, section_provider, continuous_section_field, options):
    """
    Construct a complete ScaledLagrangeBasis instance.

    This builder is called by the generic plugin registry.
    """

    # No expansion-specific YAML options are currently supported.
    del continuous_section_field  # Available by contract; unused by this expansion.
    _reject_options(options)

    # The hierarchy starts at order one.
    if not isinstance(order, int):
        raise TypeError(
            "scaled_lagrange order must be an integer"
        )

    if order < 1:
        raise ValueError(
            "scaled_lagrange order must be >= 1"
        )

    # Obtain fixed scales from the complete CSF geometry.
    y_scale, z_scale = transverse_scales(
        section_provider
    )

    return ScaledLagrangeBasis(
        order=order,
        y_scale=y_scale,
        z_scale=z_scale,
    )


# =============================================================================
# STEP 5
# Declare the minimum sectional quadrature order
# =============================================================================

def _section_gauss_minimum(basis):
    """
    Return a conservative sectional Gauss order.

    At hierarchy order N, the edge functions may contain a polynomial
    of degree N multiplied by a transverse linear factor.

    Products of two basis functions can therefore reach total degree:

        2 * (N + 1)

    During polygon slicing, the affine integration bounds may add one
    further degree to the outer one-dimensional integrand.

    An (N + 2)-point Gauss-Legendre rule is exact through degree:

        2 * (N + 2) - 1 = 2*N + 3

    The selected rule is therefore conservative for the polynomial
    products used by the sectional CUF nuclei.
    """

    if not isinstance(basis, ScaledLagrangeBasis):
        raise TypeError(
            "scaled_lagrange received an incompatible basis"
        )

    return int(basis.order) + 2


# =============================================================================
# STEP 6
# Declare the transverse contribution to longitudinal quadrature
# =============================================================================

def _longitudinal_transverse_degree(basis):
    """
    Return the conservative longitudinal degree contribution.

    An edge function of hierarchy order N can contain a polynomial
    contribution of total degree N + 1 in the transverse coordinates.

    If the physical transverse coordinates vary affinely along x,
    one basis function may therefore acquire longitudinal degree N + 1.

    A product of two basis functions may reach:

        2 * (N + 1)

    This contribution is combined by the solver with the independent
    geometry, material, and longitudinal finite-element contributions.
    """

    if not isinstance(basis, ScaledLagrangeBasis):
        raise TypeError(
            "scaled_lagrange received an incompatible basis"
        )

    return 2 * (int(basis.order) + 1)


# =============================================================================
# STEP 7
# Register the expansion
# =============================================================================

register_cuf_basis_plugin(
    CUFBasisPlugin(
        # This exact identifier is used in the YAML file.
        name="scaled_lagrange",

        # Construct the concrete scaled hierarchy.
        builder=_build,

        # Declare the minimum sectional integration order.
        section_gauss_minimum=_section_gauss_minimum,

        # Declare the longitudinal polynomial-degree contribution.
        longitudinal_transverse_degree=(
            _longitudinal_transverse_degree
        ),
    )
)

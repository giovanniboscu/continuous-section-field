# Version: CSF-CUF scaled hierarchical Lagrange plugin v26 - 2026-09-30
"""Plugin interface for the scaled hierarchical Serendipity-Lagrange basis."""

from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin
from csf.cuf.numerics import ScaledLagrangeBasis, transverse_scales


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

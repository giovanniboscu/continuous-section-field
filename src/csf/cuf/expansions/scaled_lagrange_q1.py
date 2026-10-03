# Version: CSF-CUF scaled Lagrange Q1 plugin v26 - 2026-09-30
"""Plugin interface for the scaled bilinear Lagrange Q1 basis."""

from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin
from csf.cuf.numerics import ScaledLagrangeQ1Basis, transverse_scales


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

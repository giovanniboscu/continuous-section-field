# Version: CSF-CUF scaled Maclaurin ContinuousSectionField-ready v25.1 - 2026-08-30
"""Registration of the validated complete scaled Maclaurin expansion."""

from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin
from csf.cuf.numerics import ScaledMaclaurinBasis, transverse_scales


def _reject_options(options):
    if options:
        raise ValueError(
            "scaled_maclaurin does not accept cuf.basis_options; "
            f"received {sorted(options)}"
        )


def _build(*, order, section_provider, continuous_section_field, options):
    del continuous_section_field  # Available by contract; unused by this expansion.
    _reject_options(options)
    y_scale, z_scale = transverse_scales(section_provider)
    return ScaledMaclaurinBasis(
        int(order),
        y_scale=y_scale,
        z_scale=z_scale,
    )


def _section_gauss_minimum(basis):
    return int(basis.order) + 1


def _longitudinal_transverse_degree(basis):
    return 2 * int(basis.order)


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_maclaurin",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=_longitudinal_transverse_degree,
    )
)

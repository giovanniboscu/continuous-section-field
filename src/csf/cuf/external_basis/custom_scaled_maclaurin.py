# Version: CSF-CUF external transverse basis v1 - 2026-09-29
"""External-file example equivalent to the existing scaled_maclaurin plugin.

Select this FILE in cuf.basis; no installation or built-in registry edit is
needed. The shared plugin name intentionally demonstrates isolation from the
internal scaled_maclaurin registration. This example changes loading only,
not the basis formula, scaling, derivatives, or quadrature requirements.

Replace the builder and the two numerical-requirement functions to provide
another expansion, retaining the existing CUFBasisPlugin contract.
"""
from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin
from csf.cuf.numerics import ScaledMaclaurinBasis, transverse_scales


def _build(*, order, section_provider, continuous_section_field, options):
    del continuous_section_field  # Available, just as for internal plugins.
    if options:
        raise ValueError(
            "this scaled_maclaurin example does not accept cuf.basis_options; "
            f"received {sorted(options)}"
        )
    y_scale, z_scale = transverse_scales(section_provider)
    return ScaledMaclaurinBasis(
        int(order), y_scale=y_scale, z_scale=z_scale
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

# Version: CSF-CUF scaled Taylor plugin v2 - 2026-09-30
"""Plugin interface for the complete shifted/scaled Taylor basis."""

import math

from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin
from csf.cuf.numerics import ScaledTaylorBasis, transverse_scales


def _parse_options(options):
    options = dict(options)
    allowed = {"y_center", "z_center"}
    unknown = sorted(set(options) - allowed)
    if unknown:
        raise ValueError(
            "scaled_taylor received unsupported cuf.basis_options: "
            f"{unknown}"
        )

    y_center = float(options.get("y_center", 0.0))
    z_center = float(options.get("z_center", 0.0))
    if not math.isfinite(y_center):
        raise ValueError("scaled_taylor y_center must be finite")
    if not math.isfinite(z_center):
        raise ValueError("scaled_taylor z_center must be finite")
    return y_center, z_center


def _build(*, order, section_provider, continuous_section_field, options):
    del continuous_section_field  # Available by contract; unused here.
    y_center, z_center = _parse_options(options)
    y_scale, z_scale = transverse_scales(section_provider)
    return ScaledTaylorBasis(
        int(order),
        y_scale=y_scale,
        z_scale=z_scale,
        y_center=y_center,
        z_center=z_center,
    )


def _section_gauss_minimum(basis):
    return int(basis.order) + 1


def _longitudinal_transverse_degree(basis):
    return 2 * int(basis.order)


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_taylor",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=_longitudinal_transverse_degree,
    )
)

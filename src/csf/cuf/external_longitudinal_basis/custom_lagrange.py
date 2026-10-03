# Version: CSF-CUF external longitudinal basis example v1 - 2026-09-30
"""External-file example equivalent to the built-in longitudinal Lagrange basis.

Select this file in ``longitudinal.basis``. The example intentionally reuses
exactly the existing built-in numerical basis so that changing only the loading
mechanism does not change the longitudinal approximation.
"""
from csf.cuf.core.longitudinal_basis_plugins import (
    LongitudinalBasisPlugin,
    register_longitudinal_basis_plugin,
)
from csf.cuf.longitudinal_expansions.lagrange import LagrangeLongitudinalBasis


def _build(*, order, options):
    if options:
        raise ValueError(
            "this custom Lagrange example does not accept "
            "longitudinal.basis_options; "
            f"received {sorted(options)}"
        )
    return LagrangeLongitudinalBasis(int(order))


register_longitudinal_basis_plugin(
    LongitudinalBasisPlugin(
        name="lagrange",
        builder=_build,
    )
)

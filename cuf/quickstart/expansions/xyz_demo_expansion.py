"""Minimal CUF demonstration: F = (1, y, z, x*y*z).

This is a fixed four-term example, not a complete convergence basis.
"""

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin


class XYZDemoBasis(CUFBasis):
    @property
    def order(self) -> int:
        return 1

    @property
    def size(self) -> int:
        return 4

    @staticmethod
    def _check_tau(tau: int) -> None:
        if not isinstance(tau, int) or not 1 <= tau <= 4:
            raise IndexError("tau must be an integer in 1..4")

    @staticmethod
    def _require_x(x: float | None) -> float:
        if x is None:
            raise ValueError("xyz_demo requires the longitudinal coordinate x")
        return float(x)

    def value(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        self._check_tau(tau)
        if tau == 1:
            return 1.0
        if tau == 2:
            return float(y)
        if tau == 3:
            return float(z)
        return self._require_x(x) * float(y) * float(z)

    def derivative(
        self, tau: int, direction: str, y: float, z: float,
        *, x: float | None = None
    ) -> float:
        self._check_tau(tau)
        if direction == "y":
            if tau == 2:
                return 1.0
            return self._require_x(x) * float(z) if tau == 4 else 0.0
        if direction == "z":
            if tau == 3:
                return 1.0
            return self._require_x(x) * float(y) if tau == 4 else 0.0
        raise ValueError("direction must be 'y' or 'z'")

    def longitudinal_derivative(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        self._check_tau(tau)
        return float(y) * float(z) if tau == 4 else 0.0


def _build(*, order, section_provider, continuous_section_field, options):
    # The example has one fixed four-term bilinear transverse level.
    if not isinstance(order, int) or order != 1:
        raise ValueError("xyz_demo accepts only order: 1")
    if options:
        raise ValueError("xyz_demo does not accept basis_options")
    return XYZDemoBasis()


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="xyz_demo",
        builder=_build,
        section_gauss_minimum=lambda basis: 3,
        # Conservative for affine section variation plus explicit x*y*z.
        longitudinal_transverse_degree=lambda basis: 6,
    )
)


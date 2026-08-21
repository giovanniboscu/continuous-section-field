"""Pluggable transverse-basis selection for the CSF-CUF runtime.

The solver engine depends only on this registry, not on a concrete CUF basis.
The current validated basis remains ``scaled_maclaurin`` and is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from csf.cuf.numerics import ScaledMaclaurinBasis, transverse_scales


BasisBuilder = Callable[..., object]
SectionGaussMinimum = Callable[[object], int]


@dataclass(frozen=True)
class CUFBasisPlugin:
    """Runtime descriptor for one transverse CUF basis implementation."""

    name: str
    builder: BasisBuilder
    section_gauss_minimum: SectionGaussMinimum

    def build(self, *, order: int, section_provider):
        return self.builder(
            order=order,
            section_provider=section_provider,
        )

    def minimum_section_gauss_order(self, basis) -> int:
        value = int(self.section_gauss_minimum(basis))
        if value < 1:
            raise ValueError(
                f"CUF basis plugin {self.name!r} returned an invalid "
                f"minimum section Gauss order {value}"
            )
        return value


def _build_scaled_maclaurin(*, order: int, section_provider):
    y_scale, z_scale = transverse_scales(section_provider)
    return ScaledMaclaurinBasis(
        int(order),
        y_scale=y_scale,
        z_scale=z_scale,
    )


def _scaled_maclaurin_section_gauss_minimum(basis) -> int:
    # OPT-09 requirement for the current scaled complete Maclaurin basis.
    # F_tau * F_s can reach total degree 2N. With polygon slicing, the
    # resulting outer polynomial can reach degree 2N+1, so an n-point
    # Gauss-Legendre rule requires n >= N+1.
    return int(basis.order) + 1


_PLUGINS: Dict[str, CUFBasisPlugin] = {}


def register_cuf_basis_plugin(plugin: CUFBasisPlugin, *, replace: bool = False) -> None:
    """Register a transverse CUF basis implementation by name."""
    if not isinstance(plugin, CUFBasisPlugin):
        raise TypeError("plugin must be a CUFBasisPlugin")

    name = str(plugin.name).strip()
    if not name:
        raise ValueError("CUF basis plugin name must be non-empty")

    if name in _PLUGINS and not replace:
        raise ValueError(f"CUF basis plugin {name!r} is already registered")

    _PLUGINS[name] = plugin


def get_cuf_basis_plugin(name: str) -> CUFBasisPlugin:
    """Return the registered plugin for ``name``."""
    key = str(name).strip()
    try:
        return _PLUGINS[key]
    except KeyError as exc:
        available = ", ".join(available_cuf_basis_plugins()) or "<none>"
        raise ValueError(
            f"unsupported CUF basis {key!r}; available basis plugins: {available}"
        ) from exc


def available_cuf_basis_plugins() -> Tuple[str, ...]:
    """Return registered basis names in deterministic order."""
    return tuple(sorted(_PLUGINS))


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_maclaurin",
        builder=_build_scaled_maclaurin,
        section_gauss_minimum=_scaled_maclaurin_section_gauss_minimum,
    )
)

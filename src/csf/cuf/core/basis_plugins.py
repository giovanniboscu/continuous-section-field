# Version: CSF-CUF expansion ContinuousSectionField context v25.1 - 2026-08-30
"""Registry and runtime contract for isolated transverse CUF expansions.

Concrete expansion implementations live outside this module and register
themselves through :func:`register_cuf_basis_plugin`.  Discovery is lazy so
importing the registry never creates a dependency on a concrete basis class.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import pkgutil
from typing import Callable, Dict, Tuple


BasisBuilder = Callable[..., object]
SectionGaussMinimum = Callable[[object], int]
LongitudinalTransverseDegree = Callable[[object], int]


@dataclass(frozen=True)
class CUFBasisPlugin:
    """Runtime descriptor for one transverse CUF basis implementation."""

    name: str
    builder: BasisBuilder
    section_gauss_minimum: SectionGaussMinimum
    longitudinal_transverse_degree: LongitudinalTransverseDegree

    def build(
        self,
        *,
        order: int,
        section_provider,
        continuous_section_field,
        options=None,
    ):
        """Build a basis with access to the complete CSF field context.

        Simple expansions may ignore ``continuous_section_field``.
        Section-aware expansions can retain it and query the complete
        ContinuousSectionField at the longitudinal coordinate passed to
        their runtime basis evaluation.
        """
        if continuous_section_field is None:
            raise ValueError("continuous_section_field must not be None")
        return self.builder(
            order=order,
            section_provider=section_provider,
            continuous_section_field=continuous_section_field,
            options={} if options is None else dict(options),
        )

    def minimum_section_gauss_order(self, basis) -> int:
        value = int(self.section_gauss_minimum(basis))
        if value < 1:
            raise ValueError(
                f"CUF basis plugin {self.name!r} returned an invalid "
                f"minimum section Gauss order {value}"
            )
        return value

    def transverse_x_polynomial_degree(self, basis) -> int:
        value = int(self.longitudinal_transverse_degree(basis))
        if value < 0:
            raise ValueError(
                f"CUF basis plugin {self.name!r} returned an invalid "
                f"longitudinal transverse degree {value}"
            )
        return value


_PLUGINS: Dict[str, CUFBasisPlugin] = {}
_DISCOVERY_COMPLETE = False


def discover_cuf_basis_plugins() -> None:
    """Import every built-in expansion module exactly once.

    Each module owns its builder, numerical requirements, and registration.
    Adding a new module below :mod:`csf.cuf.expansions` therefore requires no
    change to this registry or to the solver engine.
    """
    global _DISCOVERY_COMPLETE
    if _DISCOVERY_COMPLETE:
        return

    package = importlib.import_module("csf.cuf.expansions")
    for module_info in pkgutil.iter_modules(
        package.__path__,
        package.__name__ + ".",
    ):
        importlib.import_module(module_info.name)

    _DISCOVERY_COMPLETE = True


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
    discover_cuf_basis_plugins()
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
    discover_cuf_basis_plugins()
    return tuple(sorted(_PLUGINS))

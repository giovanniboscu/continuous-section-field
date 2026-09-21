# Version: CSF-CUF isolated longitudinal basis plugins v1 - 2026-09-21
"""Registry for isolated longitudinal approximation-basis plugins."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import pkgutil
from typing import Callable, Dict, Tuple

from csf.cuf.core.longitudinal_basis import LongitudinalBasis


LongitudinalBasisBuilder = Callable[..., LongitudinalBasis]


@dataclass(frozen=True)
class LongitudinalBasisPlugin:
    """Build one longitudinal basis without coupling it to FEM internals."""

    name: str
    builder: LongitudinalBasisBuilder

    def build(self, *, order: int, options=None) -> LongitudinalBasis:
        basis = self.builder(
            order=int(order),
            options={} if options is None else dict(options),
        )
        if not isinstance(basis, LongitudinalBasis):
            raise TypeError(
                f"longitudinal basis plugin {self.name!r} returned "
                f"{type(basis).__name__}, expected LongitudinalBasis"
            )
        return basis


_PLUGINS: Dict[str, LongitudinalBasisPlugin] = {}
_DISCOVERY_COMPLETE = False


def discover_longitudinal_basis_plugins() -> None:
    """Import every built-in longitudinal expansion module exactly once."""
    global _DISCOVERY_COMPLETE
    if _DISCOVERY_COMPLETE:
        return

    package = importlib.import_module("csf.cuf.longitudinal_expansions")
    for module_info in pkgutil.iter_modules(
        package.__path__,
        package.__name__ + ".",
    ):
        importlib.import_module(module_info.name)

    _DISCOVERY_COMPLETE = True


def register_longitudinal_basis_plugin(
    plugin: LongitudinalBasisPlugin,
    *,
    replace: bool = False,
) -> None:
    """Register one longitudinal basis implementation by YAML name."""
    if not isinstance(plugin, LongitudinalBasisPlugin):
        raise TypeError("plugin must be a LongitudinalBasisPlugin")

    name = str(plugin.name).strip()
    if not name:
        raise ValueError("longitudinal basis plugin name must be non-empty")

    if name in _PLUGINS and not replace:
        raise ValueError(
            f"longitudinal basis plugin {name!r} is already registered"
        )

    _PLUGINS[name] = plugin


def get_longitudinal_basis_plugin(name: str) -> LongitudinalBasisPlugin:
    """Return the registered longitudinal plugin for ``name``."""
    discover_longitudinal_basis_plugins()
    key = str(name).strip()
    try:
        return _PLUGINS[key]
    except KeyError as exc:
        available = ", ".join(available_longitudinal_basis_plugins()) or "<none>"
        raise ValueError(
            f"unsupported longitudinal basis {key!r}; available basis plugins: "
            f"{available}"
        ) from exc


def available_longitudinal_basis_plugins() -> Tuple[str, ...]:
    """Return registered longitudinal basis names in deterministic order."""
    discover_longitudinal_basis_plugins()
    return tuple(sorted(_PLUGINS))

# Version: CSF-CUF external longitudinal basis v1 - 2026-09-30
"""File-path loading for longitudinal basis plugins.

An external Python file uses the existing
``register_longitudinal_basis_plugin()`` API. Its registrations are captured
locally instead of being published in the built-in name registry. Exactly one
registered plugin identifies the file's result.

This is import isolation, not a security sandbox: only load trusted Python.
"""
from __future__ import annotations

from contextvars import ContextVar
import hashlib
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
from threading import RLock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from csf.cuf.core.longitudinal_basis_plugins import LongitudinalBasisPlugin


_REGISTRATION_TARGET: ContextVar[
    dict[str, LongitudinalBasisPlugin] | None
] = ContextVar(
    "csf_cuf_external_longitudinal_basis_registration_target",
    default=None,
)
_EXTERNAL_PLUGINS: dict[Path, LongitudinalBasisPlugin] = {}
_LOADING_PATHS: set[Path] = set()
_LOAD_LOCK = RLock()
_MODULE_PREFIX = "_csf_cuf_external_longitudinal_basis_"


def is_external_longitudinal_basis_reference(reference: str | Path) -> bool:
    """Distinguish a file reference from a registered basis name."""
    if isinstance(reference, Path):
        return True
    text = str(reference).strip()
    path = Path(text)
    return (
        path.is_absolute()
        or path.suffix.lower() == ".py"
        or "/" in text
        or "\\" in text
        or text in (".", "..", "~")
    )


def _external_path(reference: str | Path, base: Path | None = None) -> Path:
    path = Path(str(reference).strip()).expanduser()
    if base is not None and not path.is_absolute():
        path = Path(base) / path
    return path.resolve()


def resolve_longitudinal_basis_reference(base: Path, reference: Any) -> str:
    """Resolve ``longitudinal.basis`` paths relative to the case YAML.

    Parsing only resolves the path. The external module is not imported and
    file existence is not checked until the plugin is requested at runtime.
    Built-in registry names are returned unchanged.
    """
    if is_external_longitudinal_basis_reference(reference):
        return str(_external_path(reference, base))
    return str(reference)


def longitudinal_basis_registration_target(
    builtin_registry: dict[str, LongitudinalBasisPlugin],
) -> dict[str, LongitudinalBasisPlugin]:
    """Select the registry used by the existing registration function."""
    target = _REGISTRATION_TARGET.get()
    return builtin_registry if target is None else target


def load_external_longitudinal_basis_plugin(
    reference: str | Path,
) -> LongitudinalBasisPlugin:
    """Load one trusted external longitudinal basis source file.

    The file must register exactly one ``LongitudinalBasisPlugin`` through the
    normal ``register_longitudinal_basis_plugin()`` API. Registrations are
    captured locally, so an external plugin cannot replace a built-in plugin.
    """
    # Complete built-in imports before local registration capture is enabled.
    from csf.cuf.core.longitudinal_basis_plugins import (
        discover_longitudinal_basis_plugins,
    )

    discover_longitudinal_basis_plugins()
    path = _external_path(reference)

    with _LOAD_LOCK:
        if path in _EXTERNAL_PLUGINS:
            return _EXTERNAL_PLUGINS[path]
        if not path.is_file():
            raise FileNotFoundError(
                f"external longitudinal basis file not found: {path}"
            )
        if path in _LOADING_PATHS:
            raise ImportError(
                f"circular external longitudinal basis import: {path}"
            )

        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()
        module_name = _MODULE_PREFIX + digest
        loader = importlib.machinery.SourceFileLoader(module_name, str(path))
        spec = importlib.util.spec_from_file_location(
            module_name,
            path,
            loader=loader,
        )
        if spec is None or spec.loader is None:
            raise ImportError(
                f"cannot create an external longitudinal basis loader: {path}"
            )

        module = importlib.util.module_from_spec(spec)
        registered: dict[str, LongitudinalBasisPlugin] = {}
        token = _REGISTRATION_TARGET.set(registered)
        _LOADING_PATHS.add(path)
        sys.modules[module_name] = module
        success = False
        try:
            try:
                spec.loader.exec_module(module)
            except Exception as exc:
                raise ImportError(
                    f"failed to import external longitudinal basis {path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if len(registered) != 1:
                names = ", ".join(sorted(registered)) or "<none>"
                raise ValueError(
                    f"external longitudinal basis file {path} must register "
                    "exactly one LongitudinalBasisPlugin via "
                    "register_longitudinal_basis_plugin(); "
                    f"registered {len(registered)}: {names}"
                )

            plugin = next(iter(registered.values()))
            if not callable(getattr(plugin, "builder", None)):
                raise TypeError(
                    f"external longitudinal basis {path}: plugin "
                    f"{plugin.name!r} requires a callable builder"
                )

            _EXTERNAL_PLUGINS[path] = plugin
            success = True
            return plugin
        finally:
            _REGISTRATION_TARGET.reset(token)
            _LOADING_PATHS.discard(path)
            if not success:
                sys.modules.pop(module_name, None)

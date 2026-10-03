# Version: CSF-CUF external transverse basis v1 - 2026-09-29
"""File-path loading for transverse CUF basis plugins only.

An external Python file uses the existing register_cuf_basis_plugin() API.
Its registrations are captured locally, rather than published in the built-in
name registry. Exactly one registered plugin identifies the file's result.
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
    from csf.cuf.core.basis_plugins import CUFBasisPlugin


_REGISTRATION_TARGET: ContextVar[dict[str, CUFBasisPlugin] | None] = ContextVar(
    "csf_cuf_external_basis_registration_target", default=None
)
_EXTERNAL_PLUGINS: dict[Path, CUFBasisPlugin] = {}
_LOADING_PATHS: set[Path] = set()
_LOAD_LOCK = RLock()
_MODULE_PREFIX = "_csf_cuf_external_basis_"


def is_external_cuf_basis_reference(reference: str | Path) -> bool:
    """Distinguish a file reference from a registered name without importing.

    Bare names remain registry keys. A .py suffix, a path separator, or a
    pathlib.Path object explicitly selects a file; ./custom_basis therefore
    also supports Python source without a filename extension.
    """
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
    # Keep native platform path rules and case. Never lowercase a pathname.
    path = Path(str(reference).strip()).expanduser()
    if base is not None and not path.is_absolute():
        path = Path(base) / path
    return path.resolve()


def resolve_cuf_basis_reference(base: Path, reference: Any) -> str:
    """Resolve top-level cuf.basis paths relative to the owning case YAML.

    No module is executed and no file existence check is performed while
    parsing the YAML. Historical internal-name values remain unchanged.
    """
    if is_external_cuf_basis_reference(reference):
        return str(_external_path(reference, base))
    return str(reference)


def cuf_basis_registration_target(
    builtin_registry: dict[str, CUFBasisPlugin],
) -> dict[str, CUFBasisPlugin]:
    """Select the registry for the existing registration function.

    Context-local capture prevents an external module's register(...,
    replace=True) from overwriting a built-in plugin. Nested external imports
    each receive a separate target; the parent target is restored afterwards.
    """
    target = _REGISTRATION_TARGET.get()
    return builtin_registry if target is None else target


def load_external_cuf_basis_plugin(reference: str | Path) -> CUFBasisPlugin:
    """Load one trusted external Python source file, once per resolved path.

    All builder/context/quadrature behavior belongs to CUFBasisPlugin and is
    left unchanged. Absolute and YAML-resolved paths work from any cwd. Direct
    Python callers may also pass relative paths, interpreted from their cwd.

    Modules may use ordinary imports from installed/importable packages. This
    loader does not change sys.path or turn a source file into a package.
    Successful imports follow normal process-lifetime caching semantics;
    restart the process after editing an already imported plugin.
    """
    # Complete built-in imports BEFORE enabling local registration capture.
    # A copied built-in module can then import its usual dependencies safely.
    from csf.cuf.core.basis_plugins import discover_cuf_basis_plugins

    discover_cuf_basis_plugins()
    path = _external_path(reference)
    with _LOAD_LOCK:
        if path in _EXTERNAL_PLUGINS:
            return _EXTERNAL_PLUGINS[path]
        if not path.is_file():
            raise FileNotFoundError(f"external CUF basis file not found: {path}")
        if path in _LOADING_PATHS:
            raise ImportError(f"circular external CUF basis import: {path}")

        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()
        module_name = _MODULE_PREFIX + digest
        # Explicit SourceFileLoader also permits ./custom_basis (no suffix).
        loader = importlib.machinery.SourceFileLoader(module_name, str(path))
        spec = importlib.util.spec_from_file_location(
            module_name, path, loader=loader
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot create an external CUF basis loader: {path}")

        module = importlib.util.module_from_spec(spec)
        registered: dict[str, CUFBasisPlugin] = {}
        token = _REGISTRATION_TARGET.set(registered)
        _LOADING_PATHS.add(path)
        # dataclasses and normal module introspection require this entry during
        # execution, not only after the import has succeeded.
        sys.modules[module_name] = module
        success = False
        try:
            try:
                spec.loader.exec_module(module)
            except Exception as exc:
                raise ImportError(
                    f"failed to import external CUF basis {path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if len(registered) != 1:
                names = ", ".join(sorted(registered)) or "<none>"
                raise ValueError(
                    f"external CUF basis file {path} must register exactly one "
                    f"CUFBasisPlugin via register_cuf_basis_plugin(); "
                    f"registered {len(registered)}: {names}"
                )
            plugin = next(iter(registered.values()))
            for attribute in (
                "builder", "section_gauss_minimum", "longitudinal_transverse_degree"
            ):
                if not callable(getattr(plugin, attribute)):
                    raise TypeError(
                        f"external CUF basis {path}: plugin {plugin.name!r} "
                        f"requires a callable {attribute}"
                    )
            _EXTERNAL_PLUGINS[path] = plugin
            success = True
            return plugin
        finally:
            _REGISTRATION_TARGET.reset(token)
            _LOADING_PATHS.discard(path)
            if not success:
                # Failed imports are retryable and cannot leave a partially
                # initialized entry visible under this loader's module name.
                sys.modules.pop(module_name, None)

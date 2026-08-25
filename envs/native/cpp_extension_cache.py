"""Shared deterministic staging and process-cache mechanics for CPU extensions."""

from __future__ import annotations

import hashlib
from pathlib import Path
import os
import tempfile
from types import ModuleType
from typing import Sequence


_LOADED_MODULES: dict[tuple[str, str, str, str], ModuleType] = {}


class CppExtensionUnavailable(RuntimeError):
    """Raised when PyTorch's extension loader cannot be imported."""


class CppExtensionLoadFailed(RuntimeError):
    """Raised when PyTorch's extension loader rejects a prepared extension."""


def resolve_build_root(
    build_root: str | Path | None, *, environment_variable: str, default_name: str
) -> Path:
    """Resolve one backend's explicit or environment-configured build root."""

    if build_root is not None:
        return Path(build_root).expanduser().resolve()
    configured = os.environ.get(environment_variable)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / default_name


def load_source_keyed_extension(
    *,
    cache_namespace: str,
    identity: str,
    root: Path,
    build_directory_name: str,
    source: Path,
    staged_source_name: str,
    module_name: str,
    compiler_flags: Sequence[str],
    verbose: bool,
) -> ModuleType:
    """Stage one source byte-for-byte, then build or reuse its CPU module."""

    source_bytes = source.read_bytes()
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    cache_key = cache_namespace, identity, str(root), source_digest
    cached = _LOADED_MODULES.get(cache_key)
    if cached is not None:
        return cached

    # Include the independently observed source digest even when a caller
    # accidentally supplies a stale ABI identity.  PyTorch caches imported
    # modules by name, so both the directory and name must change with source.
    source_key = source_digest[:16]
    build_directory = root / build_directory_name / f"source_{source_key}"
    build_directory.mkdir(parents=True, exist_ok=True)
    staged_source = build_directory / staged_source_name
    if not staged_source.exists() or staged_source.read_bytes() != source_bytes:
        staged_source.write_bytes(source_bytes)

    try:
        from torch.utils.cpp_extension import load
    except (ImportError, OSError) as error:  # pragma: no cover - deployment path
        raise CppExtensionUnavailable from error
    try:
        module = load(
            name=f"{module_name}_{source_key}",
            sources=[str(staged_source)],
            extra_cflags=list(compiler_flags),
            build_directory=str(build_directory),
            with_cuda=False,
            is_python_module=True,
            verbose=verbose,
        )
    except Exception as error:  # cpp_extension exposes toolchain-specific errors
        raise CppExtensionLoadFailed from error
    _LOADED_MODULES[cache_key] = module
    return module

"""Source-keyed loader for the TEST-only SGSP RSCF Gate A C++ host."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from types import ModuleType
from typing import Final

import numpy as np

from envs.native.cpp_extension_cache import (
    CppExtensionLoadFailed,
    CppExtensionUnavailable,
    load_source_keyed_extension,
    resolve_build_root,
)

from .contract import ABI_TAG, NATIVE_THREADS, validate_fixture_batch


_SOURCE: Final = Path(__file__).resolve().parent / "native" / "rscf_gate_a_host.cpp"
_CACHE_NAMESPACE: Final = "sgsp_rscf_gate_a"
_BUILD_DIRECTORY_NAME: Final = "sgsp_rscf_gate_a"
_STAGED_SOURCE_NAME: Final = "rscf_gate_a_host.cpp"
_MODULE_STEM: Final = "sgsp_rscf_gate_a_native"
_BUILD_ENVIRONMENT_VARIABLE: Final = "HMASD_SGSP_RSCF_GATE_A_BUILD_ROOT"
_DEFAULT_BUILD_ROOT: Final = "hmasd_sgsp_rscf_gate_a_native"
_LOAD_LOCK: Final = threading.RLock()
_MODULES: dict[str, ModuleType] = {}

_INPUT_ORDER: Final = (
    "n_agents",
    "roles",
    "origin_slot",
    "focal_index",
    "forced_action",
    "factual_actions",
    "initial_fifo_basin",
    "initial_fifo_time",
    "initial_previous_action",
    "initial_previous_success",
    "initial_hidden",
    "event_times",
    "action_tape",
    "detection_tape",
    "uplink_tape",
    "base_tape",
)
_OUTPUT_SPECS: Final = {
    "terminal_return": np.dtype(np.float64),
    "audit_digest": np.dtype(np.uint64),
    "transition_count": np.dtype(np.int32),
    "decision_count": np.dtype(np.int32),
    "delivery_count": np.dtype(np.int32),
    "waste_count": np.dtype(np.int32),
    "scan_count": np.dtype(np.int32),
    "hidden_code_sum": np.dtype(np.int64),
    "forced_action_count": np.dtype(np.int32),
    "factual_teammate_count": np.dtype(np.int32),
}


class RSCFGateANativeUnavailable(RuntimeError):
    """The exact Gate A native host could not be loaded or verified."""


def _compiler_flags() -> tuple[str, ...]:
    if os.name == "nt":
        return ("/O2", "/std:c++17", "/EHsc", "/fp:precise")
    return ("-O3", "-std=c++17", "-ffp-contract=off", "-fno-fast-math")


def _source_sha256() -> str:
    try:
        return hashlib.sha256(_SOURCE.read_bytes()).hexdigest()
    except OSError as error:
        raise RSCFGateANativeUnavailable(f"native source is unavailable: {_SOURCE}") from error


def _expose_environment_ninja() -> None:
    """Make the exact interpreter's Ninja wheel visible without activation."""
    if shutil.which("ninja") is not None:
        return
    try:
        import ninja
    except (ImportError, OSError) as error:
        raise RSCFGateANativeUnavailable(
            "the exact project interpreter has no usable Ninja executable"
        ) from error
    bin_directory = str(Path(ninja.BIN_DIR).resolve())
    executable = Path(bin_directory) / ("ninja.exe" if os.name == "nt" else "ninja")
    if not executable.is_file():
        raise RSCFGateANativeUnavailable(
            f"the exact project interpreter's Ninja executable is absent: {executable}"
        )
    os.environ["PATH"] = bin_directory + os.pathsep + os.environ.get("PATH", "")


def _expose_windows_msvc() -> None:
    """Load the installed x64 Build Tools environment into this process only."""
    if os.name != "nt" or shutil.which("cl") is not None:
        return
    vswhere = Path(
        os.environ.get(
            "ProgramFiles(x86)", "C:/Program Files (x86)"
        )
    ) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        raise RSCFGateANativeUnavailable("Visual Studio Build Tools discovery is unavailable")
    try:
        installation_lines = subprocess.check_output(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            text=True,
            errors="strict",
        ).splitlines()
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        raise RSCFGateANativeUnavailable("Visual Studio Build Tools discovery failed") from error
    if not installation_lines:
        raise RSCFGateANativeUnavailable("no x64 Visual Studio Build Tools installation was found")
    vcvars = Path(installation_lines[-1].strip()) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not vcvars.is_file():
        raise RSCFGateANativeUnavailable(f"vcvars64.bat is unavailable: {vcvars}")
    try:
        import ctypes

        required = ctypes.windll.kernel32.GetShortPathNameW(str(vcvars), None, 0)
        short_buffer = ctypes.create_unicode_buffer(required)
        written = ctypes.windll.kernel32.GetShortPathNameW(
            str(vcvars), short_buffer, required
        )
    except (AttributeError, OSError, ValueError) as error:
        raise RSCFGateANativeUnavailable("vcvars64 short-path resolution failed") from error
    if required == 0 or written == 0:
        raise RSCFGateANativeUnavailable("vcvars64 short-path resolution failed")
    try:
        environment_lines = subprocess.check_output(
            ["cmd.exe", "/d", "/c", f"call {short_buffer.value} >nul && set"],
            text=True,
            errors="strict",
        ).splitlines()
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        raise RSCFGateANativeUnavailable("vcvars64 environment initialization failed") from error
    for line in environment_lines:
        if "=" not in line or line.startswith("="):
            continue
        name, value = line.split("=", 1)
        os.environ[name] = value
    if shutil.which("cl") is None:
        raise RSCFGateANativeUnavailable("vcvars64 did not expose the x64 C++ compiler")


def _resolved_root(build_root: Path | None) -> Path:
    return resolve_build_root(
        build_root,
        environment_variable=_BUILD_ENVIRONMENT_VARIABLE,
        default_name=_DEFAULT_BUILD_ROOT,
    )


def _expected_identity(build_root: Path | None) -> dict[str, object]:
    source_sha256 = _source_sha256()
    root = _resolved_root(build_root)
    flags = _compiler_flags()
    build_payload = json.dumps(
        {
            "abi_tag": ABI_TAG,
            "compiler_flags": flags,
            "native_threads": NATIVE_THREADS,
            "source_sha256": source_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "abi_tag": ABI_TAG,
        "source_sha256": source_sha256,
        "source_key": source_sha256[:16],
        "build_identity_sha256": hashlib.sha256(build_payload).hexdigest(),
        "compiler_flags": list(flags),
        "native_threads": NATIVE_THREADS,
        "host_kind": "TEST_ONLY_DETERMINISTIC_FULL_SUFFIX",
        "language_standard": "C++17",
        "build_root": str(root),
    }


def _verify_module(module: ModuleType, expected: dict[str, object]) -> None:
    expected_module_name = f"{_MODULE_STEM}_{expected['source_key']}"
    if module.__name__ != expected_module_name:
        raise RSCFGateANativeUnavailable(
            f"stale/source-key module mismatch: {module.__name__!r} != {expected_module_name!r}"
        )
    try:
        compiled = dict(module.compiled_identity())
    except Exception as error:
        raise RSCFGateANativeUnavailable("native module exposes no valid compiled identity") from error
    required = {
        "abi_tag": expected["abi_tag"],
        "native_threads": expected["native_threads"],
        "host_kind": expected["host_kind"],
        "language_standard": expected["language_standard"],
    }
    if compiled != required:
        raise RSCFGateANativeUnavailable(
            f"native ABI/build identity mismatch: observed={compiled!r}, expected={required!r}"
        )


def load_native_host(build_root: Path | None = None) -> ModuleType:
    """Build or reuse the exact source-keyed TEST host, failing closed."""
    with _LOAD_LOCK:
        _expose_environment_ninja()
        _expose_windows_msvc()
        expected = _expected_identity(build_root)
        root_key = str(expected["build_root"])
        cached = _MODULES.get(root_key)
        if cached is not None:
            _verify_module(cached, expected)
            return cached
        try:
            module = load_source_keyed_extension(
                cache_namespace=_CACHE_NAMESPACE,
                identity=str(expected["build_identity_sha256"]),
                root=Path(root_key),
                build_directory_name=_BUILD_DIRECTORY_NAME,
                source=_SOURCE,
                staged_source_name=_STAGED_SOURCE_NAME,
                module_name=_MODULE_STEM,
                compiler_flags=tuple(expected["compiler_flags"]),
                verbose=False,
            )
        except (CppExtensionUnavailable, CppExtensionLoadFailed, OSError) as error:
            raise RSCFGateANativeUnavailable("unable to load exact Gate A native host") from error
        _verify_module(module, expected)
        _MODULES[root_key] = module
        return module


def _validate_native_output(output: object, width: int) -> dict[str, np.ndarray]:
    if not isinstance(output, dict):
        raise RSCFGateANativeUnavailable("native host returned a non-dict output")
    if set(output) != set(_OUTPUT_SPECS):
        raise RSCFGateANativeUnavailable(
            f"native output keys differ: observed={sorted(output)}, expected={sorted(_OUTPUT_SPECS)}"
        )
    checked: dict[str, np.ndarray] = {}
    for name, dtype in _OUTPUT_SPECS.items():
        value = output[name]
        if not isinstance(value, np.ndarray):
            raise RSCFGateANativeUnavailable(f"native output {name} is not an ndarray")
        if value.dtype != dtype or value.shape != (width,) or not value.flags.c_contiguous:
            raise RSCFGateANativeUnavailable(
                f"native output {name} violates dtype/shape/contiguity contract"
            )
        if np.issubdtype(dtype, np.floating) and not bool(np.isfinite(value).all()):
            raise RSCFGateANativeUnavailable(f"native output {name} contains non-finite values")
        checked[name] = value
    return checked


def native_suffix_batch(
    batch: dict[str, np.ndarray], build_root: Path | None = None
) -> dict[str, np.ndarray]:
    """Validate and run one canonical materialized TEST fixture batch."""
    validate_fixture_batch(batch)
    width = int(batch["n_agents"].shape[0])
    module = load_native_host(build_root)
    try:
        raw = module.run_suffix_batch(*(batch[name] for name in _INPUT_ORDER))
    except Exception as error:
        raise RSCFGateANativeUnavailable("native suffix execution rejected the ABI payload") from error
    return _validate_native_output(raw, width)


def native_identity(build_root: Path | None = None) -> dict[str, object]:
    """Return the verified source/ABI/build identity of the loaded TEST host."""
    expected = _expected_identity(build_root)
    module = load_native_host(build_root)
    _verify_module(module, expected)
    return expected

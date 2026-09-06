"""Fail-closed source-keyed binding for the exact TBCFV C++ host.

The Python code here only marshals deterministic fixture structs.  It never
executes a host transition and never falls back to :mod:`host_oracle`.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Iterable, Mapping, Sequence

import numpy as np

from .host_oracle import (
    BEACONS,
    CLAIM_PERIOD,
    HORIZON,
    MAX_AGENTS,
    EpisodeTape,
    EventInput,
    FixtureSpec,
    PublicObservation,
    Snapshot,
    StepInput,
)


_SOURCE = Path(__file__).with_name("native") / "tbcfv_backend.cpp"
NATIVE_ABI_VERSION = 2
FIXTURE_MAGIC = 0x52434C4554424347
SUPPORTED_BATCH_WIDTHS = (1, 8, 32)
MSVC_COMPILE_FLAGS = (
    "/nologo",
    "/std:c++17",
    "/O2",
    "/EHsc",
    "/LD",
    "/fp:strict",
)
POSIX_COMPILE_FLAGS = (
    "-std=c++17",
    "-O2",
    "-fexceptions",
    "-shared",
    "-fPIC",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-fno-unsafe-math-optimizations",
)


class NativeBackendError(RuntimeError):
    """The exact native source/toolchain/runtime ABI boundary failed closed."""


class _FixtureInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi", ctypes.c_int32),
        ("initial_n", ctypes.c_int32),
        ("after_n", ctypes.c_int32),
        ("event_condition", ctypes.c_int32),
        ("omega_plus", ctypes.c_int32),
        ("kappa_plus", ctypes.c_int32),
        ("initial_keys", ctypes.c_int32 * MAX_AGENTS),
        ("initial_positions", ctypes.c_int32 * MAX_AGENTS),
        ("after_keys", ctypes.c_int32 * MAX_AGENTS),
        ("after_positions", ctypes.c_int32 * MAX_AGENTS),
    ]


class _StepInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi", ctypes.c_int32),
        ("claim_count", ctypes.c_int32),
        ("claims", ctypes.c_int32 * MAX_AGENTS),
    ]


class _EventInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi", ctypes.c_int32),
        ("newcomer_count", ctypes.c_int32),
        ("newcomer_positions", ctypes.c_int32 * MAX_AGENTS),
    ]


class _Snapshot(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int32),
        ("terminal", ctypes.c_int32),
        ("tick", ctypes.c_int32),
        ("agent_count", ctypes.c_int32),
        ("event_input_required", ctypes.c_int32),
        ("claim_required", ctypes.c_int32),
        ("roster_event", ctypes.c_int32),
        ("new_epoch", ctypes.c_int32),
        ("positions", ctypes.c_int32 * MAX_AGENTS),
        # Runtime row-linkage metadata only; excluded from public/model input.
        ("transport_keys", ctypes.c_int32 * MAX_AGENTS),
        ("angular_ranks", ctypes.c_int32 * MAX_AGENTS),
        ("previous_displacements", ctypes.c_int32 * MAX_AGENTS),
        ("newcomers", ctypes.c_int32 * MAX_AGENTS),
        ("current_claims", ctypes.c_int32 * MAX_AGENTS),
        ("beacon_positions", ctypes.c_int32 * BEACONS),
        ("demands", ctypes.c_int32 * BEACONS),
        ("last_coverage", ctypes.c_int32 * BEACONS),
        ("tau", ctypes.c_int32),
        ("last_u", ctypes.c_double),
        ("last_fragmentation", ctypes.c_double),
        ("accumulated_u", ctypes.c_double),
        ("accumulated_post_u", ctypes.c_double),
        ("accumulated_fragmentation", ctypes.c_double),
        ("endpoint_u", ctypes.c_double),
        ("endpoint_f", ctypes.c_double),
        ("endpoint_y", ctypes.c_double),
    ]


class _SemanticAddressInput(ctypes.Structure):
    _fields_ = [
        ("run_block", ctypes.c_int64),
        ("parameter_entry", ctypes.c_char_p),
        ("arm_only_variable", ctypes.c_char_p),
        ("cell", ctypes.c_char_p),
        ("update_or_scenario", ctypes.c_int64),
        ("physical_tick", ctypes.c_int64),
        ("roster_event_integer", ctypes.c_int64),
        ("roster_event_string", ctypes.c_char_p),
        ("roster_event_is_integer", ctypes.c_int32),
        ("physical_agent_integer", ctypes.c_int64),
        ("physical_agent_string", ctypes.c_char_p),
        ("physical_agent_is_integer", ctypes.c_int32),
        ("draw_kind", ctypes.c_char_p),
        ("draw_index", ctypes.c_int64),
    ]


_SEMANTIC_FIELDS = frozenset(
    {
        "run_block",
        "parameter_entry",
        "arm_only_variable",
        "cell",
        "update_or_scenario",
        "physical_tick",
        "roster_event",
        "physical_agent",
        "draw_kind",
        "draw_index",
    }
)


@functools.lru_cache(maxsize=256)
def _semantic_ascii(value: str, field: str) -> bytes:
    try:
        payload = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"semantic {field} must be ASCII") from exc
    if any(byte < 0x20 or byte >= 0x7F or byte in (0x22, 0x5C) for byte in payload):
        raise ValueError(f"semantic {field} requires an unescaped safe ASCII value")
    return payload


def native_source_sha256() -> str:
    """Hash currently visible source bytes; intentionally not memoized."""
    try:
        source_bytes = _SOURCE.read_bytes()
    except OSError as exc:
        raise NativeBackendError("native TBCFV source is unavailable") from exc
    return hashlib.sha256(source_bytes).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    try:
        result = subprocess.run(
            [
                str(locator),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise NativeBackendError("Visual Studio discovery failed") from exc
    installation = Path(result.stdout.strip())
    if not installation.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    candidates = tuple(
        path
        for path in (_vs_installation() / "VC" / "Tools" / "MSVC").glob(
            "*/bin/Hostx64/x64/cl.exe"
        )
        if path.is_file()
    )
    if not candidates:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")

    def version(path: Path) -> tuple[int, ...]:
        try:
            return tuple(int(part) for part in path.parents[3].name.split("."))
        except ValueError:
            return (0,)

    return max(candidates, key=version).resolve()


def _posix_compiler_path() -> Path:
    for name in ("g++", "clang++"):
        located = shutil.which(name)
        if located:
            return Path(located).resolve()
    raise NativeBackendError("g++ and clang++ are unavailable")


def _posix_toolchain_identity() -> dict[str, object]:
    compiler = _posix_compiler_path()
    try:
        probe = subprocess.run(
            [str(compiler), "--version"], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise NativeBackendError("POSIX compiler identity probe failed") from exc
    version_text = "\n".join(
        line.strip()
        for line in (probe.stdout + "\n" + probe.stderr).splitlines()
        if line.strip()
    )
    if probe.returncode != 0 or not version_text:
        raise NativeBackendError("POSIX compiler identity could not be verified")
    stat = compiler.stat()
    return {
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256_file(compiler),
        "compiler_size": stat.st_size,
        "compiler_mtime_ns": stat.st_mtime_ns,
        "compiler_version_output": version_text,
        "compile_flags": list(POSIX_COMPILE_FLAGS),
    }


def _posix_compile_artifact(
    *, cache: Path, snapshot: Path, toolchain: dict[str, object]
) -> Path:
    artifact = cache / "tbcfv_backend.so"
    if artifact.is_file():
        return artifact
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    candidate = cache / f"tbcfv_backend.{suffix}.so"
    command = [
        str(toolchain["compiler_path"]),
        *POSIX_COMPILE_FLAGS,
        str(snapshot),
        "-o",
        str(candidate),
    ]
    result = subprocess.run(command, cwd=cache, capture_output=True, text=True)
    if result.returncode != 0 or not candidate.is_file():
        raise NativeBackendError(
            f"native TBCFV compilation failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    try:
        os.replace(candidate, artifact)
    except OSError:
        if not artifact.is_file():
            raise
        candidate.unlink(missing_ok=True)
    return artifact


@functools.lru_cache(maxsize=1)
def native_toolchain_identity() -> dict[str, object]:
    """Freeze the process toolchain identity used by every loaded build key."""
    if os.name != "nt":
        return _posix_toolchain_identity()
    compiler = _compiler_path()
    try:
        probe = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    except OSError as exc:
        raise NativeBackendError("MSVC identity probe failed") from exc
    version_text = "\n".join(
        line.strip()
        for line in (probe.stdout + "\n" + probe.stderr).splitlines()
        if line.strip()
    )
    if "Microsoft" not in version_text or "C/C++" not in version_text:
        raise NativeBackendError("MSVC identity could not be verified")
    stat = compiler.stat()
    return {
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256_file(compiler),
        "compiler_size": stat.st_size,
        "compiler_mtime_ns": stat.st_mtime_ns,
        "compiler_version_output": version_text,
        "compile_flags": list(MSVC_COMPILE_FLAGS),
    }


def native_runtime_abi_identity() -> dict[str, object]:
    return {
        "implementation": sys.implementation.name,
        "cache_tag": sys.implementation.cache_tag,
        "python_version": tuple(sys.version_info[:3]),
        "pointer_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
        "byteorder": sys.byteorder,
        "machine": platform.machine(),
        "fixture_input_size": ctypes.sizeof(_FixtureInput),
        "step_input_size": ctypes.sizeof(_StepInput),
        "event_input_size": ctypes.sizeof(_EventInput),
        "snapshot_size": ctypes.sizeof(_Snapshot),
    }


def _runtime_digest() -> str:
    identity = native_runtime_abi_identity()
    digest = hashlib.sha256(b"RCLE-TBCFV-RUNTIME-ABI-v1\0")
    for key in sorted(identity):
        encoded = f"{key}={identity[key]!r}".encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _resolved_build_root(build_root: str | Path | None) -> Path:
    root = (
        Path(tempfile.gettempdir()) / "hmasd_rcle_tbcfv_native"
        if build_root is None
        else Path(build_root)
    )
    return root.expanduser().resolve()


def _visible_material(build_root: str | Path | None) -> tuple[tuple[str, ...], bytes, Path]:
    try:
        source_bytes = _SOURCE.read_bytes()
    except OSError as exc:
        raise NativeBackendError("native TBCFV source is unavailable") from exc
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    resolved = _resolved_build_root(build_root)
    compile_flags = MSVC_COMPILE_FLAGS if os.name == "nt" else POSIX_COMPILE_FLAGS
    visible_key = (
        source_digest,
        _runtime_digest(),
        str(NATIVE_ABI_VERSION),
        f"{FIXTURE_MAGIC:016x}",
        *compile_flags,
        str(resolved),
    )
    return visible_key, source_bytes, resolved


def _final_build_key(visible_key: tuple[str, ...], toolchain: dict[str, object]) -> str:
    digest = hashlib.sha256(b"RCLE-TBCFV-NATIVE-BUILD-v1\0")
    for item in visible_key:
        encoded = item.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    for item in (
        str(toolchain["compiler_path"]),
        str(toolchain["compiler_sha256"]),
        str(toolchain["compiler_version_output"]),
    ):
        encoded = item.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def native_build_key(*, build_root: str | Path | None = None) -> str:
    visible_key, _, _ = _visible_material(build_root)
    return _final_build_key(visible_key, native_toolchain_identity())


def _source_snapshot(cache: Path, source_bytes: bytes) -> Path:
    snapshot = cache / "tbcfv_backend.source.cpp"
    if snapshot.is_file():
        if snapshot.read_bytes() != source_bytes:
            raise NativeBackendError("build-key source snapshot mismatch")
        return snapshot
    candidate = cache / f"tbcfv_backend.source.{os.getpid()}.{threading.get_ident()}.tmp"
    with candidate.open("wb") as stream:
        stream.write(source_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(candidate, snapshot)
    finally:
        candidate.unlink(missing_ok=True)
    if snapshot.read_bytes() != source_bytes:
        raise NativeBackendError("published source snapshot mismatch")
    return snapshot


def _compile_artifact(
    *, build_key: str, source_bytes: bytes, build_root: Path, toolchain: dict[str, object]
) -> Path:
    cache = build_root / build_key
    cache.mkdir(parents=True, exist_ok=True)
    snapshot = _source_snapshot(cache, source_bytes)
    if os.name != "nt":
        return _posix_compile_artifact(
            cache=cache, snapshot=snapshot, toolchain=toolchain
        )
    artifact = cache / "tbcfv_backend.dll"
    if artifact.is_file():
        return artifact
    installation = _vs_installation()
    vcvars = installation / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not vcvars.is_file():
        raise NativeBackendError("vcvars64.bat is unavailable")
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    obj = cache / f"tbcfv_backend.{suffix}.obj"
    candidate = cache / f"tbcfv_backend.{suffix}.dll"
    pdb = cache / f"tbcfv_backend.{suffix}.pdb"
    implib = cache / f"tbcfv_backend.{suffix}.lib"
    command = (
        f'call "{vcvars}" >nul && "{toolchain["compiler_path"]}" '
        f'{" ".join(MSVC_COMPILE_FLAGS)} "{snapshot}" /Fo:"{obj}" '
        f'/link /OUT:"{candidate}" /PDB:"{pdb}" /IMPLIB:"{implib}"'
    )
    result = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not candidate.is_file():
        raise NativeBackendError(
            f"native TBCFV compilation failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    try:
        os.replace(candidate, artifact)
    except OSError:
        if not artifact.is_file():
            raise
        candidate.unlink(missing_ok=True)
    finally:
        for path in (obj, pdb, implib, cache / f"tbcfv_backend.{suffix}.exp"):
            path.unlink(missing_ok=True)
    return artifact


def _configure_library(library: ctypes.CDLL) -> ctypes.CDLL:
    library.rcle_tbcfv_abi_version.argtypes = []
    library.rcle_tbcfv_abi_version.restype = ctypes.c_int32
    library.rcle_tbcfv_fixture_magic.argtypes = []
    library.rcle_tbcfv_fixture_magic.restype = ctypes.c_uint64
    for symbol in (
        "rcle_tbcfv_sizeof_fixture_input",
        "rcle_tbcfv_sizeof_step_input",
        "rcle_tbcfv_sizeof_event_input",
        "rcle_tbcfv_sizeof_snapshot",
        "rcle_tbcfv_sizeof_semantic_address_input",
    ):
        function = getattr(library, symbol)
        function.argtypes = []
        function.restype = ctypes.c_size_t
    if library.rcle_tbcfv_abi_version() != NATIVE_ABI_VERSION:
        raise NativeBackendError("native ABI version mismatch")
    if library.rcle_tbcfv_fixture_magic() != FIXTURE_MAGIC:
        raise NativeBackendError("native fixture magic mismatch")
    observed = (
        library.rcle_tbcfv_sizeof_fixture_input(),
        library.rcle_tbcfv_sizeof_step_input(),
        library.rcle_tbcfv_sizeof_event_input(),
        library.rcle_tbcfv_sizeof_snapshot(),
        library.rcle_tbcfv_sizeof_semantic_address_input(),
    )
    expected = (
        ctypes.sizeof(_FixtureInput),
        ctypes.sizeof(_StepInput),
        ctypes.sizeof(_EventInput),
        ctypes.sizeof(_Snapshot),
        ctypes.sizeof(_SemanticAddressInput),
    )
    if observed != expected:
        raise NativeBackendError(f"native struct-size mismatch: {observed!r} != {expected!r}")
    library.rcle_tbcfv_reset_batch.argtypes = [
        ctypes.POINTER(_FixtureInput),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(_Snapshot),
    ]
    library.rcle_tbcfv_reset_batch.restype = ctypes.c_int32
    library.rcle_tbcfv_step_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(_StepInput),
        ctypes.c_int32,
        ctypes.POINTER(_Snapshot),
    ]
    library.rcle_tbcfv_step_batch.restype = ctypes.c_int32
    library.rcle_tbcfv_apply_event_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(_EventInput),
        ctypes.c_int32,
        ctypes.POINTER(_Snapshot),
    ]
    library.rcle_tbcfv_apply_event_batch.restype = ctypes.c_int32
    library.rcle_tbcfv_close_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_int32,
    ]
    library.rcle_tbcfv_close_batch.restype = ctypes.c_int32
    library.rcle_tbcfv_semantic_uniform_words.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(_SemanticAddressInput),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    library.rcle_tbcfv_semantic_uniform_words.restype = ctypes.c_int32
    library.rcle_tbcfv_semantic_claims.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(_SemanticAddressInput),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32),
    ]
    library.rcle_tbcfv_semantic_claims.restype = ctypes.c_int32
    library.rcle_tbcfv_semantic_claims_compact.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int64,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32),
    ]
    library.rcle_tbcfv_semantic_claims_compact.restype = ctypes.c_int32
    library.rcle_tbcfv_materialize_fixtures.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int64,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.c_int32,
        ctypes.POINTER(_FixtureInput),
    ]
    library.rcle_tbcfv_materialize_fixtures.restype = ctypes.c_int32
    library.rcle_tbcfv_materialize_events.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int64,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(ctypes.c_int64),
        ctypes.POINTER(_Snapshot),
        ctypes.POINTER(_FixtureInput),
        ctypes.c_int32,
        ctypes.POINTER(_EventInput),
    ]
    library.rcle_tbcfv_materialize_events.restype = ctypes.c_int32
    library.rcle_tbcfv_scripted_actions.argtypes = [
        ctypes.POINTER(_Snapshot),
        ctypes.c_int32,
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(_StepInput),
    ]
    library.rcle_tbcfv_scripted_actions.restype = ctypes.c_int32
    return library


_LIBRARY_LOCK = threading.RLock()
_WARM_LIBRARIES: dict[tuple[str, ...], tuple[str, Path, ctypes.CDLL]] = {}


def _require_for_material(
    visible_key: tuple[str, ...], source_bytes: bytes, build_root: Path
) -> tuple[str, Path, ctypes.CDLL]:
    with _LIBRARY_LOCK:
        warm = _WARM_LIBRARIES.get(visible_key)
        if warm is not None:
            return warm
        toolchain = native_toolchain_identity()
        build_key = _final_build_key(visible_key, toolchain)
        artifact = _compile_artifact(
            build_key=build_key,
            source_bytes=source_bytes,
            build_root=build_root,
            toolchain=toolchain,
        )
        try:
            library = _configure_library(ctypes.CDLL(str(artifact)))
        except (OSError, AttributeError) as exc:
            raise NativeBackendError("native artifact load/ABI probe failed") from exc
        result = (build_key, artifact, library)
        _WARM_LIBRARIES[visible_key] = result
        return result


def require_cpp_batched_backend(
    *, build_root: str | Path | None = None
) -> ctypes.CDLL:
    """Build/load the exact DLL; source changes invalidate the warm key."""
    visible_key, source_bytes, resolved = _visible_material(build_root)
    return _require_for_material(visible_key, source_bytes, resolved)[2]


class NativeBackendBinding:
    """One immutable source-keyed DLL handle shared by a complete runner chain."""

    __slots__ = ("build_key", "library", "source_sha256")

    def __init__(self, source_sha256: str, build_key: str, library: ctypes.CDLL) -> None:
        self.source_sha256 = source_sha256
        self.build_key = build_key
        self.library = library


def bind_native_backend(*, build_root: str | Path | None = None) -> NativeBackendBinding:
    visible_key, source_bytes, resolved = _visible_material(build_root)
    build_key, _, library = _require_for_material(visible_key, source_bytes, resolved)
    return NativeBackendBinding(hashlib.sha256(source_bytes).hexdigest(), build_key, library)


def _library_for(
    binding: NativeBackendBinding | None, build_root: str | Path | None
) -> ctypes.CDLL:
    if binding is not None:
        if not isinstance(binding, NativeBackendBinding) or build_root is not None:
            raise ValueError("native binding and build_root are mutually exclusive")
        return binding.library
    return bind_native_backend(build_root=build_root).library


def native_abi_identity(*, build_root: str | Path | None = None) -> dict[str, int]:
    library = require_cpp_batched_backend(build_root=build_root)
    return {
        "abi_version": int(library.rcle_tbcfv_abi_version()),
        "fixture_magic": int(library.rcle_tbcfv_fixture_magic()),
        "fixture_input_size": int(library.rcle_tbcfv_sizeof_fixture_input()),
        "step_input_size": int(library.rcle_tbcfv_sizeof_step_input()),
        "event_input_size": int(library.rcle_tbcfv_sizeof_event_input()),
        "snapshot_size": int(library.rcle_tbcfv_sizeof_snapshot()),
    }


def native_artifact_identity(
    *, build_root: str | Path | None = None
) -> dict[str, object]:
    visible_key, source_bytes, resolved = _visible_material(build_root)
    started = time.perf_counter()
    build_key, artifact, library = _require_for_material(visible_key, source_bytes, resolved)
    elapsed = time.perf_counter() - started
    if not artifact.is_file():
        raise NativeBackendError("native artifact disappeared after load")
    stat = artifact.stat()
    return {
        "path": str(artifact),
        "sha256": _sha256_file(artifact),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "build_key": build_key,
        "resolved_build_root": str(resolved),
        "runtime_abi": native_runtime_abi_identity(),
        "toolchain": native_toolchain_identity(),
        "abi": {
            "abi_version": int(library.rcle_tbcfv_abi_version()),
            "fixture_magic": int(library.rcle_tbcfv_fixture_magic()),
            "fixture_input_size": int(library.rcle_tbcfv_sizeof_fixture_input()),
            "step_input_size": int(library.rcle_tbcfv_sizeof_step_input()),
            "event_input_size": int(library.rcle_tbcfv_sizeof_event_input()),
            "snapshot_size": int(library.rcle_tbcfv_sizeof_snapshot()),
        },
        "load_seconds": elapsed,
    }


def _fixture_input(fixture: FixtureSpec) -> _FixtureInput:
    fixture.validate()
    result = _FixtureInput()
    result.magic = FIXTURE_MAGIC
    result.abi = NATIVE_ABI_VERSION
    result.initial_n = len(fixture.initial_keys)
    result.after_n = len(fixture.after_keys)
    result.event_condition = fixture.event_condition
    result.omega_plus = fixture.omega_plus
    result.kappa_plus = fixture.kappa_plus
    for array in (
        result.initial_keys,
        result.initial_positions,
        result.after_keys,
        result.after_positions,
    ):
        for index in range(MAX_AGENTS):
            array[index] = -1
    for index, value in enumerate(fixture.initial_keys):
        result.initial_keys[index] = value
    for index, value in enumerate(fixture.initial_positions):
        result.initial_positions[index] = value
    for index, value in enumerate(fixture.after_keys):
        result.after_keys[index] = value
    for index, value in enumerate(fixture.after_positions):
        result.after_positions[index] = value
    return result


def _fixture_spec(value: _FixtureInput) -> FixtureSpec:
    fixture = FixtureSpec(
        initial_keys=tuple(int(value.initial_keys[index]) for index in range(value.initial_n)),
        initial_positions=tuple(
            int(value.initial_positions[index]) for index in range(value.initial_n)
        ),
        after_keys=tuple(int(value.after_keys[index]) for index in range(value.after_n)),
        after_positions=tuple(
            int(value.after_positions[index]) for index in range(value.after_n)
        ),
        event_condition=int(value.event_condition),
        omega_plus=int(value.omega_plus),
        kappa_plus=int(value.kappa_plus),
    )
    fixture.validate()
    return fixture


def _step_input(action: StepInput) -> _StepInput:
    result = _StepInput()
    result.magic = FIXTURE_MAGIC
    result.abi = NATIVE_ABI_VERSION
    result.claim_count = len(action.claims)
    for index in range(MAX_AGENTS):
        result.claims[index] = -1
    if len(action.claims) > MAX_AGENTS:
        raise ValueError("a claim row cannot exceed twelve agents")
    for index, claim in enumerate(action.claims):
        if type(claim) is not int:
            raise TypeError("claims must be exact ints")
        result.claims[index] = claim
    return result


def _event_input(event: EventInput) -> _EventInput:
    result = _EventInput()
    result.magic = FIXTURE_MAGIC
    result.abi = NATIVE_ABI_VERSION
    result.newcomer_count = len(event.newcomer_positions)
    for index in range(MAX_AGENTS):
        result.newcomer_positions[index] = -1
    if len(event.newcomer_positions) > MAX_AGENTS:
        raise ValueError("an event input cannot exceed twelve newcomer positions")
    for index, position in enumerate(event.newcomer_positions):
        if type(position) is not int:
            raise TypeError("newcomer positions must be exact ints")
        result.newcomer_positions[index] = position
    return result


def _event_spec(value: _EventInput) -> EventInput:
    return EventInput(
        tuple(
            int(value.newcomer_positions[index])
            for index in range(value.newcomer_count)
        )
    )


def _snapshot(value: _Snapshot) -> Snapshot:
    if value.status != 0:
        raise NativeBackendError(f"native snapshot status was {value.status}")
    n = int(value.agent_count)
    terminal = bool(value.terminal)
    return Snapshot(
        tick=int(value.tick),
        terminal=terminal,
        event_input_required=bool(value.event_input_required),
        claim_required=bool(value.claim_required),
        roster_event=bool(value.roster_event),
        new_epoch=bool(value.new_epoch),
        positions=tuple(int(value.positions[index]) for index in range(n)),
        transport_keys=tuple(int(value.transport_keys[index]) for index in range(n)),
        angular_ranks=tuple(int(value.angular_ranks[index]) for index in range(n)),
        previous_displacements=tuple(
            int(value.previous_displacements[index]) for index in range(n)
        ),
        newcomers=tuple(bool(value.newcomers[index]) for index in range(n)),
        current_claims=tuple(int(value.current_claims[index]) for index in range(n)),
        beacon_positions=tuple(int(item) for item in value.beacon_positions),
        demands=tuple(int(item) for item in value.demands),
        last_coverage=tuple(int(item) for item in value.last_coverage),
        last_u=None if value.last_u < 0.0 else float(value.last_u),
        last_fragmentation=(
            None if value.last_fragmentation < 0.0 else float(value.last_fragmentation)
        ),
        accumulated_u=float(value.accumulated_u),
        accumulated_post_u=float(value.accumulated_post_u),
        accumulated_fragmentation=float(value.accumulated_fragmentation),
        tau=int(value.tau) if terminal else None,
        U=float(value.endpoint_u) if terminal else None,
        F=float(value.endpoint_f) if terminal else None,
        Y=float(value.endpoint_y) if terminal else None,
    )


class _NativeSnapshotView:
    """Lazy candidate-local view over one immutable native output row."""

    __slots__ = ("_cache", "_value")

    def __init__(self, value: _Snapshot) -> None:
        if value.status != 0:
            raise NativeBackendError(f"native snapshot status was {value.status}")
        self._value = value
        self._cache: dict[str, tuple[int, ...]] = {}

    @property
    def agent_count(self) -> int: return int(self._value.agent_count)
    @property
    def tick(self) -> int: return int(self._value.tick)
    @property
    def terminal(self) -> bool: return bool(self._value.terminal)
    @property
    def event_input_required(self) -> bool: return bool(self._value.event_input_required)
    @property
    def claim_required(self) -> bool: return bool(self._value.claim_required)
    @property
    def roster_event(self) -> bool: return bool(self._value.roster_event)
    @property
    def new_epoch(self) -> bool: return bool(self._value.new_epoch)

    def _agent_ints(self, field: str) -> tuple[int, ...]:
        cached = self._cache.get(field)
        if cached is not None:
            return cached
        values = getattr(self._value, field)
        result = tuple(int(values[index]) for index in range(self.agent_count))
        self._cache[field] = result
        return result

    def _beacon_ints(self, field: str) -> tuple[int, ...]:
        cached = self._cache.get(field)
        if cached is not None:
            return cached
        values = getattr(self._value, field)
        result = tuple(int(values[index]) for index in range(BEACONS))
        self._cache[field] = result
        return result

    @property
    def positions(self) -> tuple[int, ...]: return self._agent_ints("positions")
    @property
    def transport_keys(self) -> tuple[int, ...]: return self._agent_ints("transport_keys")
    @property
    def angular_ranks(self) -> tuple[int, ...]: return self._agent_ints("angular_ranks")
    @property
    def previous_displacements(self) -> tuple[int, ...]: return self._agent_ints("previous_displacements")
    @property
    def newcomers(self) -> tuple[bool, ...]:
        return tuple(bool(value) for value in self._agent_ints("newcomers"))
    @property
    def current_claims(self) -> tuple[int, ...]: return self._agent_ints("current_claims")
    @property
    def beacon_positions(self) -> tuple[int, ...]:
        return self._beacon_ints("beacon_positions")
    @property
    def demands(self) -> tuple[int, ...]:
        return self._beacon_ints("demands")
    @property
    def last_coverage(self) -> tuple[int, ...]:
        return self._beacon_ints("last_coverage")
    @property
    def last_u(self) -> float | None:
        return None if self._value.last_u < 0.0 else float(self._value.last_u)
    @property
    def last_fragmentation(self) -> float | None:
        return None if self._value.last_fragmentation < 0.0 else float(self._value.last_fragmentation)
    @property
    def accumulated_u(self) -> float: return float(self._value.accumulated_u)
    @property
    def accumulated_post_u(self) -> float: return float(self._value.accumulated_post_u)
    @property
    def accumulated_fragmentation(self) -> float: return float(self._value.accumulated_fragmentation)
    @property
    def tau(self) -> int | None: return None if self._value.tau < 0 else int(self._value.tau)
    @property
    def U(self) -> float | None: return float(self._value.endpoint_u) if self.terminal else None
    @property
    def F(self) -> float | None: return float(self._value.endpoint_f) if self.terminal else None
    @property
    def Y(self) -> float | None: return float(self._value.endpoint_y) if self.terminal else None

    def public_observation(self) -> PublicObservation:
        if self.event_input_required:
            raise RuntimeError("pre-event tick-24 state is lifecycle metadata, not actor input")
        return PublicObservation(
            tick=self.tick,
            claim_required=self.claim_required,
            roster_event=self.roster_event,
            new_epoch=self.new_epoch,
            positions=self.positions,
            angular_ranks=self.angular_ranks,
            previous_displacements=self.previous_displacements,
            newcomers=self.newcomers,
            beacon_positions=self.beacon_positions,
            demands=self.demands,
        )


def _semantic_input_rows(
    addresses: Sequence[Mapping[str, object]],
) -> tuple[ctypes.Array[_SemanticAddressInput], tuple[bytes, ...]]:
    if not addresses or len(addresses) > 65_536:
        raise ValueError("semantic address batch must contain 1..65536 rows")
    encoded: list[bytes] = []

    def text(value: object, field: str) -> bytes:
        if not isinstance(value, str):
            raise ValueError(f"semantic {field} must be a string")
        payload = _semantic_ascii(value, field)
        encoded.append(payload)
        return payload

    def integer(value: object, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"semantic {field} must be an integer")
        if value < -(1 << 63) or value >= (1 << 63):
            raise ValueError(f"semantic {field} is outside int64")
        return value

    rows: list[_SemanticAddressInput] = []
    for address in addresses:
        if set(address) != _SEMANTIC_FIELDS:
            raise ValueError("semantic native address inventory differs")
        roster = address["roster_event"]
        physical = address["physical_agent"]
        roster_is_integer = isinstance(roster, int) and not isinstance(roster, bool)
        physical_is_integer = isinstance(physical, int) and not isinstance(physical, bool)
        rows.append(
            _SemanticAddressInput(
                run_block=integer(address["run_block"], "run_block"),
                parameter_entry=text(address["parameter_entry"], "parameter_entry"),
                arm_only_variable=text(address["arm_only_variable"], "arm_only_variable"),
                cell=text(address["cell"], "cell"),
                update_or_scenario=integer(address["update_or_scenario"], "update_or_scenario"),
                physical_tick=integer(address["physical_tick"], "physical_tick"),
                roster_event_integer=(integer(roster, "roster_event") if roster_is_integer else 0),
                roster_event_string=(b"" if roster_is_integer else text(roster, "roster_event")),
                roster_event_is_integer=int(roster_is_integer),
                physical_agent_integer=(integer(physical, "physical_agent") if physical_is_integer else 0),
                physical_agent_string=(b"" if physical_is_integer else text(physical, "physical_agent")),
                physical_agent_is_integer=int(physical_is_integer),
                draw_kind=text(address["draw_kind"], "draw_kind"),
                draw_index=integer(address["draw_index"], "draw_index"),
            )
        )
    return (_SemanticAddressInput * len(rows))(*rows), tuple(encoded)


def semantic_uniform_words(
    key: bytes,
    addresses: Sequence[Mapping[str, object]],
    *,
    build_root: str | Path | None = None,
    binding: NativeBackendBinding | None = None,
) -> tuple[int, ...]:
    """Evaluate exact canonical HMAC-SHA256 address words in one native call."""

    if type(key) is not bytes or len(key) != 32:
        raise ValueError("semantic uniform key must contain exactly 32 bytes")
    rows, keepalive = _semantic_input_rows(addresses)
    key_buffer = (ctypes.c_uint8 * 32).from_buffer_copy(key)
    outputs = (ctypes.c_uint64 * len(rows))()
    library = _library_for(binding, build_root)
    status = library.rcle_tbcfv_semantic_uniform_words(
        key_buffer, rows, len(rows), outputs
    )
    _ = keepalive
    if status != 0:
        raise NativeBackendError(f"native semantic uniform batch failed with status {status}")
    return tuple(int(value) for value in outputs)


def semantic_claims(
    key: bytes,
    addresses: Sequence[Mapping[str, object]],
    probabilities: np.ndarray,
    *,
    build_root: str | Path | None = None,
    binding: NativeBackendBinding | None = None,
) -> tuple[int, ...]:
    """Evaluate exact semantic words and the frozen sequential six-way choice."""

    if type(key) is not bytes or len(key) != 32:
        raise ValueError("semantic claim key must contain exactly 32 bytes")
    rows, keepalive = _semantic_input_rows(addresses)
    values = np.asarray(probabilities)
    if values.dtype != np.float64 or values.ndim != 2 or values.shape != (len(rows), BEACONS):
        raise ValueError("semantic claim probabilities must be contiguous float64 [rows,6]")
    values = np.ascontiguousarray(values)
    key_buffer = (ctypes.c_uint8 * 32).from_buffer_copy(key)
    outputs = (ctypes.c_int32 * len(rows))()
    library = _library_for(binding, build_root)
    status = library.rcle_tbcfv_semantic_claims(
        key_buffer,
        rows,
        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        len(rows),
        outputs,
    )
    _ = keepalive
    if status != 0:
        raise NativeBackendError(f"native semantic claim batch failed with status {status}")
    return tuple(int(value) for value in outputs)


def semantic_claims_compact(
    key: bytes,
    run_block: int,
    cell_codes: np.ndarray,
    update_or_scenarios: np.ndarray,
    roster_events: np.ndarray,
    physical_agents: np.ndarray,
    physical_ticks: np.ndarray,
    probabilities: np.ndarray,
    *,
    build_root: str | Path | None = None,
    binding: NativeBackendBinding | None = None,
) -> tuple[int, ...]:
    """Candidate-frozen compact actor-claim address and selection kernel."""

    if type(key) is not bytes or len(key) != 32:
        raise ValueError("semantic claim key must contain exactly 32 bytes")
    columns = [
        np.ascontiguousarray(cell_codes, dtype=np.int32),
        np.ascontiguousarray(update_or_scenarios, dtype=np.int64),
        np.ascontiguousarray(roster_events, dtype=np.int64),
        np.ascontiguousarray(physical_agents, dtype=np.int64),
        np.ascontiguousarray(physical_ticks, dtype=np.int64),
    ]
    count = int(columns[0].size)
    if count < 1 or any(column.ndim != 1 or column.size != count for column in columns):
        raise ValueError("compact semantic claim columns must be aligned nonempty vectors")
    values = np.ascontiguousarray(probabilities)
    if values.dtype != np.float64 or values.shape != (count, BEACONS):
        raise ValueError("compact semantic claim probabilities must be float64 [rows,6]")
    key_buffer = (ctypes.c_uint8 * 32).from_buffer_copy(key)
    outputs = np.empty(count, dtype=np.int32)
    library = _library_for(binding, build_root)
    status = library.rcle_tbcfv_semantic_claims_compact(
        key_buffer,
        run_block,
        columns[0].ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
        columns[1].ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
        columns[2].ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
        columns[3].ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
        columns[4].ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        count,
        outputs.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
    )
    if status != 0:
        raise NativeBackendError(f"compact native semantic claim batch failed with status {status}")
    return tuple(int(value) for value in outputs)


def materialize_fixtures_compact(
    key: bytes,
    run_block: int,
    cell_codes: np.ndarray,
    update_or_scenarios: np.ndarray,
    episode_rows: np.ndarray,
    *,
    build_root: str | Path | None = None,
    binding: NativeBackendBinding | None = None,
) -> tuple[FixtureSpec, ...]:
    """Materialize the frozen reset semantic addresses and fixtures in C++."""

    if type(key) is not bytes or len(key) != 32:
        raise ValueError("fixture semantic key must contain exactly 32 bytes")
    cells = np.ascontiguousarray(cell_codes, dtype=np.int32)
    updates = np.ascontiguousarray(update_or_scenarios, dtype=np.int64)
    rows = np.ascontiguousarray(episode_rows, dtype=np.int64)
    width = int(cells.size)
    if width not in SUPPORTED_BATCH_WIDTHS or any(
        column.ndim != 1 or column.size != width for column in (updates, rows)
    ):
        raise ValueError("fixture semantic columns differ from a supported native width")
    key_buffer = (ctypes.c_uint8 * 32).from_buffer_copy(key)
    outputs = (_FixtureInput * width)()
    library = _library_for(binding, build_root)
    status = library.rcle_tbcfv_materialize_fixtures(
        key_buffer,
        run_block,
        cells.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
        updates.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
        rows.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
        width,
        outputs,
    )
    if status != 0:
        raise NativeBackendError(f"native fixture materialization failed with status {status}")
    return tuple(_fixture_spec(output) for output in outputs)


class NativeBatch:
    """One exact-width native interactive batch with explicit close."""

    def __init__(
        self,
        library: ctypes.CDLL,
        handles: ctypes.Array[ctypes.c_void_p],
        snapshots: ctypes.Array[_Snapshot],
        *,
        packed_views: bool = False,
    ) -> None:
        self._library = library
        self._handles = handles
        self._raw_snapshots = snapshots
        self._packed_views = packed_views
        self._snapshots = self._convert_snapshots(snapshots)
        self._closed = False

    def _convert_snapshots(self, outputs: ctypes.Array[_Snapshot]) -> tuple[object, ...]:
        converter = _NativeSnapshotView if self._packed_views else _snapshot
        return tuple(converter(output) for output in outputs)

    @property
    def width(self) -> int:
        return len(self._handles)

    @property
    def snapshots(self) -> tuple[object, ...]:
        return self._snapshots

    @property
    def closed(self) -> bool:
        return self._closed

    def step(self, actions: Sequence[StepInput]) -> tuple[Snapshot, ...]:
        if self._closed:
            raise NativeBackendError("cannot step a closed native batch")
        materialized = tuple(actions)
        if len(materialized) != self.width:
            raise ValueError("action batch width does not match the native host batch")
        inputs = (_StepInput * self.width)(*(_step_input(action) for action in materialized))
        outputs = (_Snapshot * self.width)()
        status = self._library.rcle_tbcfv_step_batch(
            self._handles, inputs, self.width, outputs
        )
        if status != 0:
            raise NativeBackendError(f"native TBCFV step failed with status {status}")
        converted = self._convert_snapshots(outputs)
        self._raw_snapshots = outputs
        self._snapshots = converted
        return converted

    def apply_event(self, events: Sequence[EventInput]) -> tuple[Snapshot, ...]:
        """Install all t=24 event inputs atomically before claims are accepted."""
        if self._closed:
            raise NativeBackendError("cannot apply an event to a closed native batch")
        materialized = tuple(events)
        if len(materialized) != self.width:
            raise ValueError("event batch width does not match the native host batch")
        inputs = (_EventInput * self.width)(*(_event_input(event) for event in materialized))
        outputs = (_Snapshot * self.width)()
        status = self._library.rcle_tbcfv_apply_event_batch(
            self._handles, inputs, self.width, outputs
        )
        if status != 0:
            raise NativeBackendError(f"native TBCFV event failed with status {status}")
        converted = self._convert_snapshots(outputs)
        self._raw_snapshots = outputs
        self._snapshots = converted
        return converted

    def scripted_actions(
        self,
        package_code: int,
        previous_claims: Sequence[Sequence[int]],
        survivors: Sequence[Sequence[bool]],
        first_or_epoch: Sequence[bool],
        active_churn: Sequence[bool],
        post_event_claim_index: Sequence[int],
    ) -> tuple[StepInput, ...]:
        """Evaluate one exact frozen scripted claim clock natively."""

        if self._closed:
            raise NativeBackendError("cannot act on a closed native batch")
        lane_sequences = (previous_claims, survivors)
        if any(len(sequence) != self.width for sequence in lane_sequences) or any(
            len(sequence) != self.width
            for sequence in (first_or_epoch, active_churn, post_event_claim_index)
        ):
            raise ValueError("scripted action batch columns do not match native width")
        previous = np.full((self.width, MAX_AGENTS), -1, dtype=np.int32)
        survivor = np.zeros((self.width, MAX_AGENTS), dtype=np.uint8)
        for lane, snapshot in enumerate(self._snapshots):
            count = len(snapshot.positions)
            if len(previous_claims[lane]) != count or len(survivors[lane]) != count:
                raise ValueError("scripted action roster columns do not align")
            previous[lane, :count] = np.asarray(previous_claims[lane], dtype=np.int32)
            survivor[lane, :count] = np.asarray(survivors[lane], dtype=np.uint8)
        first = np.ascontiguousarray(first_or_epoch, dtype=np.uint8)
        churn = np.ascontiguousarray(active_churn, dtype=np.uint8)
        post = np.ascontiguousarray(post_event_claim_index, dtype=np.int32)
        outputs = (_StepInput * self.width)()
        status = self._library.rcle_tbcfv_scripted_actions(
            self._raw_snapshots,
            self.width,
            package_code,
            previous.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
            survivor.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            first.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            churn.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            post.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
            outputs,
        )
        if status != 0:
            raise NativeBackendError(f"native scripted action batch failed with status {status}")
        return tuple(
            StepInput(tuple(int(output.claims[index]) for index in range(output.claim_count)))
            for output in outputs
        )

    def materialize_events_compact(
        self,
        key: bytes,
        run_block: int,
        cell_codes: np.ndarray,
        update_or_scenarios: np.ndarray,
        episode_rows: np.ndarray,
        fixtures: Sequence[FixtureSpec],
    ) -> tuple[EventInput, ...]:
        """Materialize exact t=24 event positions against current native snapshots."""

        if type(key) is not bytes or len(key) != 32:
            raise ValueError("event semantic key must contain exactly 32 bytes")
        cells = np.ascontiguousarray(cell_codes, dtype=np.int32)
        updates = np.ascontiguousarray(update_or_scenarios, dtype=np.int64)
        rows = np.ascontiguousarray(episode_rows, dtype=np.int64)
        if any(column.ndim != 1 or column.size != self.width for column in (cells, updates, rows)):
            raise ValueError("event semantic columns do not align with native width")
        materialized = tuple(fixtures)
        if len(materialized) != self.width:
            raise ValueError("event fixture inventory does not align with native width")
        fixture_inputs = (_FixtureInput * self.width)(
            *(_fixture_input(fixture) for fixture in materialized)
        )
        outputs = (_EventInput * self.width)()
        key_buffer = (ctypes.c_uint8 * 32).from_buffer_copy(key)
        status = self._library.rcle_tbcfv_materialize_events(
            key_buffer,
            run_block,
            cells.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
            updates.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
            rows.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
            self._raw_snapshots,
            fixture_inputs,
            self.width,
            outputs,
        )
        if status != 0:
            raise NativeBackendError(f"native event materialization failed with status {status}")
        return tuple(_event_spec(output) for output in outputs)

    def close(self) -> None:
        if self._closed:
            raise NativeBackendError("native batch is already closed")
        status = self._library.rcle_tbcfv_close_batch(self._handles, self.width)
        if status != 0:
            raise NativeBackendError(f"native TBCFV close failed with status {status}")
        self._closed = True

    def __enter__(self) -> "NativeBatch":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if not self._closed:
            self.close()


def reset_native_batch(
    fixtures: Iterable[FixtureSpec], *, build_root: str | Path | None = None,
    packed_views: bool = False,
    binding: NativeBackendBinding | None = None,
) -> NativeBatch:
    materialized = tuple(fixtures)
    width = len(materialized)
    if width not in SUPPORTED_BATCH_WIDTHS:
        raise ValueError(f"supported native batch widths are {SUPPORTED_BATCH_WIDTHS}")
    inputs = (_FixtureInput * width)(*(_fixture_input(fixture) for fixture in materialized))
    handles = (ctypes.c_void_p * width)()
    outputs = (_Snapshot * width)()
    library = _library_for(binding, build_root)
    status = library.rcle_tbcfv_reset_batch(inputs, width, handles, outputs)
    if status != 0:
        raise NativeBackendError(f"native TBCFV reset failed with status {status}")
    return NativeBatch(library, handles, outputs, packed_views=packed_views)


def run_native_trace_batch(
    cases: Iterable[EpisodeTape], *, build_root: str | Path | None = None
) -> tuple[tuple[Snapshot, ...], ...]:
    """Run fixed fixture tapes through C++; no Python transition is available."""
    materialized = tuple(cases)
    width = len(materialized)
    if width not in SUPPORTED_BATCH_WIDTHS:
        raise ValueError(f"supported native batch widths are {SUPPORTED_BATCH_WIDTHS}")
    for case in materialized:
        case.validate()
    batch = reset_native_batch((case.fixture for case in materialized), build_root=build_root)
    traces: list[list[Snapshot]] = [[snapshot] for snapshot in batch.snapshots]
    try:
        clock_index = 0
        for tick in range(HORIZON):
            actions: list[StepInput] = []
            for case in materialized:
                if tick % CLAIM_PERIOD == 0:
                    actions.append(StepInput(tuple(case.claims_by_clock[clock_index])))
                else:
                    actions.append(StepInput.no_claims())
            if tick % CLAIM_PERIOD == 0:
                clock_index += 1
            snapshots = batch.step(actions)
            if snapshots[0].event_input_required:
                if not all(snapshot.event_input_required for snapshot in snapshots):
                    raise NativeBackendError("native event lifecycle diverged across batch lanes")
                snapshots = batch.apply_event(
                    tuple(EventInput(case.event_newcomer_positions) for case in materialized)
                )
            for trace, snapshot in zip(traces, snapshots):
                trace.append(snapshot)
    finally:
        if not batch.closed:
            batch.close()
    return tuple(tuple(trace) for trace in traces)


def backend_contract() -> dict[str, object]:
    return {
        "candidate_local_boundary": "RCLE-TBCFV-R04 full native host",
        "shared_component_alias": None,
        "backend": "cpp",
        "abi_version": NATIVE_ABI_VERSION,
        "fixture_magic": FIXTURE_MAGIC,
        "supported_batch_widths": list(SUPPORTED_BATCH_WIDTHS),
        "interactive_reset_step_terminal": True,
        "event_time_newcomer_position_input": True,
        "stable_physical_agent_transport_keys": True,
        "transport_keys_actor_model_visible": False,
        "public_observation_excludes_transport_keys": True,
        "source_toolchain_runtime_abi_build_root_keyed": True,
        "process_local_warm_cache": True,
        "python_oracle": "TEST-only",
        "python_fallback": False,
        "rng": False,
    }

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
import subprocess
import sys
import tempfile
import threading
import time
from typing import Iterable, Sequence

from .host_oracle import (
    BEACONS,
    CLAIM_PERIOD,
    HORIZON,
    MAX_AGENTS,
    EpisodeTape,
    EventInput,
    FixtureSpec,
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


@functools.lru_cache(maxsize=1)
def native_toolchain_identity() -> dict[str, object]:
    """Freeze the process toolchain identity used by every loaded build key."""
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
    visible_key = (
        source_digest,
        _runtime_digest(),
        str(NATIVE_ABI_VERSION),
        f"{FIXTURE_MAGIC:016x}",
        *MSVC_COMPILE_FLAGS,
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
    )
    expected = (
        ctypes.sizeof(_FixtureInput),
        ctypes.sizeof(_StepInput),
        ctypes.sizeof(_EventInput),
        ctypes.sizeof(_Snapshot),
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


class NativeBatch:
    """One exact-width native interactive batch with explicit close."""

    def __init__(
        self,
        library: ctypes.CDLL,
        handles: ctypes.Array[ctypes.c_void_p],
        snapshots: tuple[Snapshot, ...],
    ) -> None:
        self._library = library
        self._handles = handles
        self._snapshots = snapshots
        self._closed = False

    @property
    def width(self) -> int:
        return len(self._handles)

    @property
    def snapshots(self) -> tuple[Snapshot, ...]:
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
        converted = tuple(_snapshot(output) for output in outputs)
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
        converted = tuple(_snapshot(output) for output in outputs)
        self._snapshots = converted
        return converted

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
    fixtures: Iterable[FixtureSpec], *, build_root: str | Path | None = None
) -> NativeBatch:
    materialized = tuple(fixtures)
    width = len(materialized)
    if width not in SUPPORTED_BATCH_WIDTHS:
        raise ValueError(f"supported native batch widths are {SUPPORTED_BATCH_WIDTHS}")
    inputs = (_FixtureInput * width)(*(_fixture_input(fixture) for fixture in materialized))
    handles = (ctypes.c_void_p * width)()
    outputs = (_Snapshot * width)()
    library = require_cpp_batched_backend(build_root=build_root)
    status = library.rcle_tbcfv_reset_batch(inputs, width, handles, outputs)
    if status != 0:
        raise NativeBackendError(f"native TBCFV reset failed with status {status}")
    return NativeBatch(library, handles, tuple(_snapshot(output) for output in outputs))


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

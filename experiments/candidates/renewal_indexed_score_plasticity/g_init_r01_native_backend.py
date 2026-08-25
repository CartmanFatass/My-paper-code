"""Source/runtime-ABI-keyed ctypes binding for the R01 full environment host.

The C++ session owns reset, hidden-sector state, schedule progression, step and
terminal lifecycle.  Python supplies already materialized policy actions and
exact event outcomes/identity tokens.  There is no Python production fallback.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Iterable, Sequence


NATIVE_ABI_VERSION = 1
FIXTURE_MAGIC = 0x5253504752314E31
MAX_BATCH_WIDTH = 32
SHARED_COMPONENT = "risp.g_init_reach.r01.full_host"
TEST_NAMESPACE = "TEST/RISP-G-INIT-REACH/CERTIFICATE-FIXTURE/V1"
MSVC_COMPILE_FLAGS = ("/nologo", "/std:c++17", "/O2", "/EHsc", "/LD", "/fp:strict")
_SOURCE = Path(__file__).with_name("g_init_r01_native_backend.cpp")


class NativeBackendError(RuntimeError):
    pass


class _ResetInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("schedule_id", ctypes.c_int32),
        ("prefix_bits", ctypes.c_int32),
        ("init_event_token", ctypes.c_uint64),
        ("init_prefix", ctypes.c_uint64 * 16),
    ]


class _StepInput(ctypes.Structure):
    _fields_ = [
        ("action", ctypes.c_int32),
        ("prefix_bits", ctypes.c_int32),
        ("action_event_token", ctypes.c_uint64),
        ("motion_event_token", ctypes.c_uint64),
        ("ack_event_token", ctypes.c_uint64),
        ("motion_prefix", ctypes.c_uint64 * 2),
        ("ack_prefix", ctypes.c_uint64 * 2),
    ]


class _ExtendedStepInput(ctypes.Structure):
    _fields_ = [
        ("action", ctypes.c_int32),
        ("prefix_bits", ctypes.c_int32),
        ("action_event_token", ctypes.c_uint64),
        ("motion_event_token", ctypes.c_uint64),
        ("ack_event_token", ctypes.c_uint64),
        ("motion_prefix", ctypes.c_uint64 * 16),
        ("ack_prefix", ctypes.c_uint64 * 16),
    ]


class _TransitionOutput(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_int32)
        for name in (
            "status", "schedule_id", "renewal", "tau", "duration",
            "sector_before", "sector_after", "action", "ack_sign", "utility",
            "terminal", "next_tau", "next_duration", "init_events_consumed",
            "action_events_consumed", "motion_events_consumed", "ack_events_consumed",
        )
    ] + [
        (name, ctypes.c_uint64)
        for name in (
            "init_event_token", "action_event_token", "motion_event_token", "ack_event_token",
        )
    ]


@dataclass(frozen=True)
class MaterializedReset:
    schedule_id: int
    init_prefix: int
    init_event_token: int


@dataclass(frozen=True)
class MaterializedStep:
    action: int
    motion_prefix: int
    ack_prefix: int
    action_event_token: int
    motion_event_token: int
    ack_event_token: int


def _integer(value: object, name: str, lower: int, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    result = int(value)
    if not lower <= result <= upper:
        raise ValueError(f"{name} must be in [{lower}, {upper}]")
    return result


def _token(value: object, name: str) -> int:
    return _integer(value, name, 0, (1 << 64) - 1)


def _reset_input(value: MaterializedReset) -> _ResetInput:
    if not isinstance(value, MaterializedReset):
        raise TypeError("reset fixtures must be MaterializedReset values")
    item = _ResetInput(); item.magic = FIXTURE_MAGIC; item.abi_version = NATIVE_ABI_VERSION
    item.schedule_id = _integer(value.schedule_id, "schedule_id", 0, 4); item.prefix_bits = 1024
    item.init_event_token = _token(value.init_event_token, "init_event_token")
    raw = _integer(value.init_prefix, "init_prefix", 0, (1 << 1024) - 1)
    for index in range(15, -1, -1): item.init_prefix[index] = raw & ((1 << 64) - 1); raw >>= 64
    return item


def _validated_step(value: MaterializedStep) -> tuple[int, int, int, int, int, int]:
    if not isinstance(value, MaterializedStep):
        raise TypeError("step fixtures must be MaterializedStep values")
    return (
        _integer(value.action, "action", 0, 2),
        _token(value.action_event_token, "action_event_token"),
        _token(value.motion_event_token, "motion_event_token"),
        _token(value.ack_event_token, "ack_event_token"),
        _integer(value.motion_prefix, "motion_prefix", 0, (1 << 1024) - 1),
        _integer(value.ack_prefix, "ack_prefix", 0, (1 << 1024) - 1),
    )


def _step_input(value: MaterializedStep) -> _StepInput:
    action, action_token, motion_token, ack_token, motion, ack = _validated_step(value)
    item = _StepInput()
    item.action = action; item.prefix_bits = 128
    item.action_event_token = action_token; item.motion_event_token = motion_token; item.ack_event_token = ack_token
    for raw, target in ((motion >> 896, item.motion_prefix), (ack >> 896, item.ack_prefix)):
        for index in range(1, -1, -1):
            target[index] = raw & ((1 << 64) - 1)
            raw >>= 64
    return item


def _extended_step_input(value: MaterializedStep) -> _ExtendedStepInput:
    action, action_token, motion_token, ack_token, motion, ack = _validated_step(value)
    item = _ExtendedStepInput()
    item.action = action; item.prefix_bits = 1024
    item.action_event_token = action_token; item.motion_event_token = motion_token; item.ack_event_token = ack_token
    for raw, target in ((motion, item.motion_prefix), (ack, item.ack_prefix)):
        for index in range(15, -1, -1):
            target[index] = raw & ((1 << 64) - 1)
            raw >>= 64
    return item


def _output(value: _TransitionOutput) -> dict[str, int | bool]:
    return {
        "status": int(value.status), "schedule_id": int(value.schedule_id),
        "renewal": int(value.renewal), "tau": int(value.tau),
        "duration": int(value.duration), "sector_before": int(value.sector_before),
        "sector_after": int(value.sector_after), "action": int(value.action),
        "ack_sign": int(value.ack_sign), "utility": int(value.utility),
        "terminal": bool(value.terminal), "next_tau": int(value.next_tau),
        "next_duration": int(value.next_duration),
        "init_events_consumed": int(value.init_events_consumed),
        "action_events_consumed": int(value.action_events_consumed),
        "motion_events_consumed": int(value.motion_events_consumed),
        "ack_events_consumed": int(value.ack_events_consumed),
        "init_event_token": int(value.init_event_token),
        "action_event_token": int(value.action_event_token),
        "motion_event_token": int(value.motion_event_token),
        "ack_event_token": int(value.ack_event_token),
    }


def source_sha256() -> str:
    return hashlib.sha256(_SOURCE.read_bytes()).hexdigest()


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    result = subprocess.run(
        [str(locator), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        check=True, capture_output=True, text=True,
    )
    installation = Path(result.stdout.strip())
    if not installation.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    candidates = tuple((_vs_installation() / "VC" / "Tools" / "MSVC").glob("*/bin/Hostx64/x64/cl.exe"))
    files = tuple(path for path in candidates if path.is_file())
    if not files:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")
    return max(files, key=lambda path: path.stat().st_mtime_ns).resolve()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@functools.lru_cache(maxsize=1)
def native_toolchain_identity() -> dict[str, object]:
    compiler = _compiler_path()
    version = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    version_text = "\n".join(line.strip() for line in (version.stdout + "\n" + version.stderr).splitlines() if line.strip())
    if "Microsoft" not in version_text or "C/C++" not in version_text:
        raise NativeBackendError("MSVC version identity could not be read")
    stat = compiler.stat()
    return {
        "compiler_path": str(compiler), "compiler_sha256": _sha256_file(compiler),
        "compiler_size": stat.st_size, "compiler_mtime_ns": stat.st_mtime_ns,
        "compiler_version_output": version_text, "compile_flags": list(MSVC_COMPILE_FLAGS),
    }


def runtime_abi_identity() -> dict[str, object]:
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag,
        "machine": platform.machine(), "byteorder": sys.byteorder,
        "pointer_bytes": ctypes.sizeof(ctypes.c_void_p),
        "abi_version": NATIVE_ABI_VERSION,
        "struct_sizes": {
            "reset_input": ctypes.sizeof(_ResetInput),
            "step_input": ctypes.sizeof(_StepInput),
            "extended_step_input": ctypes.sizeof(_ExtendedStepInput),
            "transition_output": ctypes.sizeof(_TransitionOutput),
        },
    }


def _native_build_key_for(source_digest: str, runtime_abi: dict[str, object], toolchain: dict[str, object]) -> str:
    payload = {
        "schema": "RISP-G-INIT-REACH-R01-NATIVE-BUILD-KEY-V1",
        "source_sha256": source_digest, "toolchain": toolchain,
        "runtime_abi": runtime_abi,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def native_build_key() -> str:
    return _native_build_key_for(source_sha256(), runtime_abi_identity(), native_toolchain_identity())


def _loader_cache_key_for(*, source_digest: str, runtime_abi: dict[str, object], toolchain: dict[str, object], build_root: str | Path | None) -> tuple[str, str]:
    root = Path(tempfile.gettempdir()) / "hmasd_risp_g_init_r01_native" if build_root is None else Path(build_root)
    return str(root.resolve()), _native_build_key_for(source_digest, runtime_abi, toolchain)


def _current_loader_cache_key(build_root: str | Path | None = None) -> tuple[str, str]:
    return _loader_cache_key_for(
        source_digest=source_sha256(), runtime_abi=runtime_abi_identity(),
        toolchain=native_toolchain_identity(), build_root=build_root,
    )


def _compiled_path(cache_key: tuple[str, str]) -> Path:
    root_value, build_key = cache_key
    cache = Path(root_value) / build_key
    dll = cache / "g_init_r01_native_backend.dll"
    if dll.is_file():
        return dll
    cache.mkdir(parents=True, exist_ok=True)
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    obj = cache / "g_init_r01_native_backend.obj"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /link /OUT:"{dll}"'
    )
    completed = subprocess.run(
        command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache, capture_output=True, text=True,
    )
    if completed.returncode != 0 or not dll.is_file():
        raise NativeBackendError(
            f"native backend compilation failed ({completed.returncode}):\n{completed.stdout}\n{completed.stderr}"
        )
    return dll


def _configure_library(library: ctypes.CDLL) -> ctypes.CDLL:
    library.risp_g_init_r01_abi_version.argtypes = []
    library.risp_g_init_r01_abi_version.restype = ctypes.c_int32
    library.risp_g_init_r01_fixture_magic.argtypes = []
    library.risp_g_init_r01_fixture_magic.restype = ctypes.c_uint64
    library.risp_g_init_r01_max_width.argtypes = []
    library.risp_g_init_r01_max_width.restype = ctypes.c_int32
    for name in ("reset_input", "step_input", "extended_step_input", "transition_output"):
        function = getattr(library, f"risp_g_init_r01_sizeof_{name}")
        function.argtypes = []
        function.restype = ctypes.c_size_t
    library.risp_g_init_r01_interactive_reset_batch.argtypes = [
        ctypes.POINTER(_ResetInput), ctypes.c_int32, ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(_TransitionOutput),
    ]
    library.risp_g_init_r01_interactive_reset_batch.restype = ctypes.c_int32
    library.risp_g_init_r01_interactive_step_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(_StepInput), ctypes.c_int32,
        ctypes.POINTER(_TransitionOutput),
    ]
    library.risp_g_init_r01_interactive_step_batch.restype = ctypes.c_int32
    library.risp_g_init_r01_interactive_step_batch_extended.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(_ExtendedStepInput), ctypes.c_int32,
        ctypes.POINTER(_TransitionOutput),
    ]
    library.risp_g_init_r01_interactive_step_batch_extended.restype = ctypes.c_int32
    library.risp_g_init_r01_interactive_close_batch.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_int32]
    library.risp_g_init_r01_interactive_close_batch.restype = ctypes.c_int32
    expected_sizes = runtime_abi_identity()["struct_sizes"]
    observed = {
        name: int(getattr(library, f"risp_g_init_r01_sizeof_{name}")())
        for name in ("reset_input", "step_input", "extended_step_input", "transition_output")
    }
    if library.risp_g_init_r01_abi_version() != NATIVE_ABI_VERSION:
        raise NativeBackendError("native backend ABI version mismatch")
    if library.risp_g_init_r01_fixture_magic() != FIXTURE_MAGIC:
        raise NativeBackendError("native backend fixture magic mismatch")
    if library.risp_g_init_r01_max_width() != MAX_BATCH_WIDTH:
        raise NativeBackendError("native backend width declaration mismatch")
    if observed != expected_sizes:
        raise NativeBackendError(f"native struct-size mismatch: {observed} != {expected_sizes}")
    return library


_LOADED_LIBRARIES: dict[tuple[str, str], ctypes.CDLL] = {}


def require_cpp_batched_backend(build_root: str | Path | None = None) -> ctypes.CDLL:
    """Compile/load the exact backend with a process-local warm cache."""
    key = _current_loader_cache_key(build_root)
    cached = _LOADED_LIBRARIES.get(key)
    if cached is not None:
        return cached
    loaded = _configure_library(ctypes.CDLL(str(_compiled_path(key))))
    _LOADED_LIBRARIES[key] = loaded
    return loaded


def clear_process_local_cache_for_tests() -> None:
    _LOADED_LIBRARIES.clear()


def native_artifact_identity(build_root: str | Path | None = None) -> dict[str, object]:
    started = time.perf_counter()
    library = require_cpp_batched_backend(build_root)
    load_seconds = time.perf_counter() - started
    path = Path(vars(library)["_name"]).resolve()
    return {
        "schema": "RISP-G-INIT-REACH-R01-NATIVE-ARTIFACT-IDENTITY-V1",
        "artifact_path": str(path), "artifact_sha256": _sha256_file(path),
        "artifact_size": path.stat().st_size, "build_key": native_build_key(),
        "source_path": str(_SOURCE.resolve()), "source_sha256": source_sha256(),
        "toolchain": native_toolchain_identity(), "runtime_abi": runtime_abi_identity(),
        "abi_version": NATIVE_ABI_VERSION, "batch_widths": [1, 8, 32],
        "full_reset_step_cpp": True, "python_interactive_call_loop": True,
        "python_materialized_event_adapter": True, "python_environment_state": False,
        "python_reset_step_transition": False, "python_fallback": False,
        "load_seconds": load_seconds,
    }


class NativeInteractiveBatch:
    """One authoritative native reset-to-terminal batch session."""

    def __init__(self, resets: Iterable[MaterializedReset], *, build_root: str | Path | None = None) -> None:
        materialized = tuple(resets)
        width = len(materialized)
        if width < 1 or width > MAX_BATCH_WIDTH:
            raise ValueError(f"native batch width must be in [1, {MAX_BATCH_WIDTH}]")
        inputs = (_ResetInput * width)(*(_reset_input(value) for value in materialized))
        self._handles = (ctypes.c_uint64 * width)()
        outputs = (_TransitionOutput * width)()
        self._library = require_cpp_batched_backend(build_root)
        status = self._library.risp_g_init_r01_interactive_reset_batch(inputs, width, self._handles, outputs)
        if status != 0:
            raise NativeBackendError(f"native reset batch rejected inputs with status {status}")
        self._width = width
        self._open = True
        self._active_lanes = list(range(width))
        self._extended_fallback_count = 0
        self.initial = tuple(_output(value) for value in outputs)

    @property
    def width(self) -> int:
        return self._width

    @property
    def active_lanes(self) -> tuple[int, ...]:
        return tuple(self._active_lanes)

    @property
    def extended_fallback_count(self) -> int:
        return self._extended_fallback_count

    def step(self, rows: Iterable[MaterializedStep]) -> tuple[dict[str, int | bool], ...]:
        if not self._open:
            raise NativeBackendError("native batch session is closed")
        if not self._active_lanes:
            raise NativeBackendError("native batch lifecycle is already terminal")
        if len(self._active_lanes) != self._width:
            raise NativeBackendError("heterogeneous batch requires step_active")
        return self.step_active(tuple(range(self._width)), rows)

    def step_active(self, lane_indices: Iterable[int], rows: Iterable[MaterializedStep]) -> tuple[dict[str, int | bool], ...]:
        if not self._open:
            raise NativeBackendError("native batch session is closed")
        lanes = tuple(lane_indices)
        materialized = tuple(rows)
        if not lanes or len(materialized) != len(lanes):
            raise ValueError("one materialized step is required per native lane")
        if any(isinstance(lane, bool) or not isinstance(lane, int) for lane in lanes):
            raise TypeError("lane indices must be integers")
        if len(set(lanes)) != len(lanes) or any(lane not in self._active_lanes for lane in lanes):
            raise ValueError("lane indices must be unique active lanes")
        width = len(lanes)
        handles = (ctypes.c_uint64 * width)(*(self._handles[lane] for lane in lanes))
        inputs = (_StepInput * width)(*(_step_input(value) for value in materialized))
        outputs = (_TransitionOutput * width)()
        status = self._library.risp_g_init_r01_interactive_step_batch(
            handles, inputs, width, outputs,
        )
        if status in (24, 25):
            # The compact interval could contain a rational boundary.  The
            # failed call is precommit, so retry the identical whole batch
            # with the remaining exact prefix material and identities.
            extended = (_ExtendedStepInput * width)(*(_extended_step_input(value) for value in materialized))
            status = self._library.risp_g_init_r01_interactive_step_batch_extended(
                handles, extended, width, outputs,
            )
            self._extended_fallback_count += 1
        if status != 0:
            raise NativeBackendError(f"native step batch rejected inputs or lifecycle with status {status}")
        result = tuple(_output(value) for value in outputs)
        terminal_lanes = {lane for lane, output in zip(lanes, result) if output["terminal"]}
        self._active_lanes = [lane for lane in self._active_lanes if lane not in terminal_lanes]
        return result

    def close(self) -> None:
        if not self._open:
            return
        status = self._library.risp_g_init_r01_interactive_close_batch(self._handles, self._width)
        if status != 0:
            raise NativeBackendError(f"native close batch rejected lifecycle with status {status}")
        self._open = False

    def __enter__(self) -> "NativeInteractiveBatch":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def production_preflight(*, batch_width: int, build_root: str | Path | None = None) -> dict[str, object]:
    """Require both the local artifact and the shared production registry."""
    _integer(batch_width, "batch_width", 1, MAX_BATCH_WIDTH)
    local = native_artifact_identity(build_root)
    from envs.native import production_backend as shared

    component = getattr(shared, "RISP_G_INIT_REACH_R01_FULL_HOST", SHARED_COMPONENT)
    admitted = shared.require_cpp_batched_production(
        component, backend="cpp", batch_width=batch_width, build_root=build_root,
    )
    if admitted.get("full_reset_step_cpp") is not True or admitted.get("python_fallback") is not False:
        raise NativeBackendError("shared guard did not admit the exact full C++ host")
    return {"schema": "RISP-G-INIT-REACH-R01-PRODUCTION-PREFLIGHT-V1", "local": local, "shared": admitted}


def fixture_event_token(identity: Sequence[object]) -> int:
    """TEST-only stable identity token; never a random draw or production root."""
    payload = json.dumps([TEST_NAMESPACE, *identity], ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def fixture_draw_prefix(identity: Sequence[object]) -> int:
    payload = json.dumps([TEST_NAMESPACE, "DRAW", *identity], ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return int.from_bytes(hashlib.shake_256(payload).digest(128), "big")


def python_fixture_outcome(*, sector: int, duration: int, action: int, motion_prefix: int, ack_prefix: int) -> tuple[int, int]:
    """Exact-integer TEST oracle for the raw-prefix native law."""
    _integer(sector, "sector", 0, 2); _integer(duration, "duration", 4, 12); _integer(action, "action", 0, 2)
    motion = _integer(motion_prefix, "motion_prefix", 0, (1 << 1024) - 1)
    ack = _integer(ack_prefix, "ack_prefix", 0, (1 << 1024) - 1)
    power15, power16 = 15**duration, 16**duration
    denominator = 3 * power16
    masses = [power16 + 2 * power15 if candidate == sector else power16 - power15 for candidate in range(3)]
    scale = 1 << 1024
    cumulative = 0
    next_sector = -1
    for candidate in range(2):
        cumulative += masses[candidate]
        if (motion + 1) * denominator <= scale * cumulative:
            next_sector = candidate; break
        if motion * denominator < scale * cumulative:
            raise NativeBackendError("TEST motion prefix does not resolve at 1024 bits")
    if next_sector < 0:
        next_sector = 2
    numerator = 4 if action == next_sector else 1
    if (ack + 1) * 5 <= scale * numerator:
        sign = 1
    elif ack * 5 < scale * numerator:
        raise NativeBackendError("TEST ACK prefix does not resolve at 1024 bits")
    else:
        sign = -1
    return next_sector, sign


def python_fixture_initial_sector(init_prefix: int) -> int:
    prefix = _integer(init_prefix, "init_prefix", 0, (1 << 1024) - 1); scale = 1 << 1024
    if (prefix + 1) * 3 <= scale: return 0
    if prefix * 3 < scale: raise NativeBackendError("TEST init prefix unresolved")
    if (prefix + 1) * 3 <= 2 * scale: return 1
    if prefix * 3 < 2 * scale: raise NativeBackendError("TEST init prefix unresolved")
    return 2

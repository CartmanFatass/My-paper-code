"""Source/toolchain/runtime-ABI keyed ctypes loader for the TBCC full host.

The C++ library is authoritative for setup composition, latent graph state,
plant transitions, holds, absorption, reward, and endpoint counters.  This
module only validates/materializes fixed-width inputs and manages opaque native
sessions.  There is no Python transition or fallback path.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Iterable

from .config import (
    FIXTURE_MAGIC,
    FUNCTIONAL_BATCH_WIDTHS,
    MAX_BATCH_WIDTH,
    MAX_HOLD_TICKS,
    MSVC_COMPILE_FLAGS,
    NATIVE_ABI_VERSION,
)
from .host_types import HostOutput, RenewalLane, ResetLane, materialize_rows

_SOURCE = Path(__file__).with_name("native") / "tbcc_backend.cpp"
_BUILD_ROOT = Path(tempfile.gettempdir()) / "hmasd_scdmp_tbcc_r02_native"


class NativeBackendError(RuntimeError):
    """The exact candidate native boundary rejected an input or lifecycle."""


class _ResetInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("event_0", ctypes.c_int32),
        ("event_1", ctypes.c_int32),
        ("k_initial", ctypes.c_int32),
        ("k_after", ctypes.c_int32),
        ("switch_tick", ctypes.c_int32),
        ("active", ctypes.c_int32),
        ("initial_v", ctypes.c_double),
        ("initial_y", ctypes.c_double),
        ("initial_phi", ctypes.c_double),
    ]


class _RenewalInput(ctypes.Structure):
    _fields_ = [
        ("active", ctypes.c_int32),
        ("action", ctypes.c_int32),
        ("eta_v", ctypes.c_double * MAX_HOLD_TICKS),
        ("eta_y", ctypes.c_double * MAX_HOLD_TICKS),
        ("eta_omega", ctypes.c_double * MAX_HOLD_TICKS),
    ]


class _HostOutput(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int32),
        ("advanced", ctypes.c_int32),
        ("active", ctypes.c_int32),
        ("terminal", ctypes.c_int32),
        ("ticks_advanced", ctypes.c_int32),
        ("n", ctypes.c_int32),
        ("hold_k", ctypes.c_int32),
        ("next_k", ctypes.c_int32),
        ("safe_dock", ctypes.c_int32),
        ("timeout", ctypes.c_int32),
        ("cable_overload", ctypes.c_int32),
        ("gantry_contact", ctypes.c_int32),
        ("attitude_loss", ctypes.c_int32),
        ("formation_loss", ctypes.c_int32),
        ("observation", ctypes.c_double * 18),
        ("reward_sum", ctypes.c_double),
        ("energy_sum", ctypes.c_double),
        ("energy_ticks", ctypes.c_int32),
        ("dock_tick", ctypes.c_int32),
        ("last_hold_reward_count", ctypes.c_int32),
        ("last_hold_rewards", ctypes.c_double * MAX_HOLD_TICKS),
    ]


class _SetupFixtureInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("event_0", ctypes.c_int32),
        ("event_1", ctypes.c_int32),
    ]


class _SetupFixtureOutput(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int32),
        ("p", ctypes.c_int32 * 4),
        ("q", ctypes.c_int32),
    ]


class _PrimitiveFixtureInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("q", ctypes.c_int32),
        ("n", ctypes.c_int32),
        ("x", ctypes.c_double),
        ("v", ctypes.c_double),
        ("y", ctypes.c_double),
        ("w", ctypes.c_double),
        ("phi", ctypes.c_double),
        ("omega", ctypes.c_double),
        ("z", ctypes.c_double * 4),
        ("formation", ctypes.c_double),
        ("prior_a", ctypes.c_int32),
        ("prior_r", ctypes.c_int32 * 4),
        ("action", ctypes.c_int32),
        ("eta_v", ctypes.c_double),
        ("eta_y", ctypes.c_double),
        ("eta_omega", ctypes.c_double),
    ]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_source_sha256() -> str:
    return _sha256_file(_SOURCE)


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    completed = subprocess.run(
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
    installation = Path(completed.stdout.strip())
    if not installation.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    candidates = tuple(
        path
        for path in (_vs_installation() / "VC/Tools/MSVC").glob("*/bin/Hostx64/x64/cl.exe")
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
    compiler = _compiler_path()
    probe = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    version_text = "\n".join(
        line.strip()
        for line in (probe.stdout + "\n" + probe.stderr).splitlines()
        if line.strip()
    )
    if "Microsoft" not in version_text or "C/C++" not in version_text:
        raise NativeBackendError("MSVC compiler identity could not be read")
    return {
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256_file(compiler),
        "compiler_version_output": version_text,
        "compile_flags": list(MSVC_COMPILE_FLAGS),
    }


def runtime_abi_identity() -> dict[str, object]:
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag,
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "pointer_bytes": ctypes.sizeof(ctypes.c_void_p),
        "abi_version": NATIVE_ABI_VERSION,
        "struct_sizes": {
            "reset_input": ctypes.sizeof(_ResetInput),
            "renewal_input": ctypes.sizeof(_RenewalInput),
            "host_output": ctypes.sizeof(_HostOutput),
            "setup_fixture_input": ctypes.sizeof(_SetupFixtureInput),
            "setup_fixture_output": ctypes.sizeof(_SetupFixtureOutput),
            "primitive_fixture_input": ctypes.sizeof(_PrimitiveFixtureInput),
        },
    }


def _build_key(source_digest: str, toolchain: dict[str, object], runtime: dict[str, object]) -> str:
    payload = {
        "schema": "SCDMP-TBCC-R02-NATIVE-BUILD-KEY-V1",
        "source_sha256": source_digest,
        "toolchain": toolchain,
        "runtime_abi": runtime,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def native_build_key() -> str:
    return _build_key(native_source_sha256(), native_toolchain_identity(), runtime_abi_identity())


def _compiled_path(build_key: str) -> Path:
    cache = _BUILD_ROOT / build_key
    dll = cache / "tbcc_backend.dll"
    if dll.is_file():
        return dll
    cache.mkdir(parents=True, exist_ok=True)
    vcvars = _vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    unique = f"{os.getpid()}_{time.time_ns()}"
    obj = cache / f"tbcc_backend_{unique}.obj"
    staged = cache / f"tbcc_backend_{unique}.dll"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /Fe:"{staged}"'
    )
    completed = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache,
        capture_output=True,
        text=True,
    )
    try:
        if completed.returncode != 0 or not staged.is_file():
            raise NativeBackendError(
                f"TBCC native compilation failed ({completed.returncode}):\n"
                f"{completed.stdout}\n{completed.stderr}"
            )
        if dll.is_file():
            staged.unlink()
        else:
            os.replace(staged, dll)
    finally:
        obj.unlink(missing_ok=True)
        staged.unlink(missing_ok=True)
    return dll


def _configure_library(library: ctypes.CDLL) -> ctypes.CDLL:
    library.tbcc_r02_abi_version.argtypes = []
    library.tbcc_r02_abi_version.restype = ctypes.c_int32
    library.tbcc_r02_fixture_magic.argtypes = []
    library.tbcc_r02_fixture_magic.restype = ctypes.c_uint64
    library.tbcc_r02_max_width.argtypes = []
    library.tbcc_r02_max_width.restype = ctypes.c_int32
    structure_types = {
        "reset_input": _ResetInput,
        "renewal_input": _RenewalInput,
        "host_output": _HostOutput,
        "setup_fixture_input": _SetupFixtureInput,
        "setup_fixture_output": _SetupFixtureOutput,
        "primitive_fixture_input": _PrimitiveFixtureInput,
    }
    observed_sizes: dict[str, int] = {}
    for name, structure in structure_types.items():
        function = getattr(library, f"tbcc_r02_sizeof_{name}")
        function.argtypes = []
        function.restype = ctypes.c_size_t
        observed_sizes[name] = int(function())
        if observed_sizes[name] != ctypes.sizeof(structure):
            raise NativeBackendError(f"native ABI size mismatch for {name}")
    if int(library.tbcc_r02_abi_version()) != NATIVE_ABI_VERSION:
        raise NativeBackendError("native ABI version mismatch")
    if int(library.tbcc_r02_fixture_magic()) != FIXTURE_MAGIC:
        raise NativeBackendError("native fixture magic mismatch")
    if int(library.tbcc_r02_max_width()) != MAX_BATCH_WIDTH:
        raise NativeBackendError("native maximum width mismatch")
    library.tbcc_r02_reset_batch.argtypes = [
        ctypes.POINTER(_ResetInput),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(_HostOutput),
    ]
    library.tbcc_r02_reset_batch.restype = ctypes.c_int32
    library.tbcc_r02_renew_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(_RenewalInput),
        ctypes.c_int32,
        ctypes.POINTER(_HostOutput),
    ]
    library.tbcc_r02_renew_batch.restype = ctypes.c_int32
    library.tbcc_r02_close_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_int32,
    ]
    library.tbcc_r02_close_batch.restype = ctypes.c_int32
    library.tbcc_r02_test_setup_batch.argtypes = [
        ctypes.POINTER(_SetupFixtureInput),
        ctypes.c_int32,
        ctypes.POINTER(_SetupFixtureOutput),
    ]
    library.tbcc_r02_test_setup_batch.restype = ctypes.c_int32
    library.tbcc_r02_test_primitive.argtypes = [
        ctypes.POINTER(_PrimitiveFixtureInput),
        ctypes.POINTER(_HostOutput),
    ]
    library.tbcc_r02_test_primitive.restype = ctypes.c_int32
    return library


# The first key deliberately omits toolchain discovery.  After one load, an
# unchanged source/runtime pair returns the CDLL without re-entering vswhere.
_LOADED_BY_SOURCE_RUNTIME: dict[str, tuple[str, ctypes.CDLL]] = {}


def _source_runtime_key() -> tuple[str, str]:
    source = native_source_sha256()
    runtime = runtime_abi_identity()
    digest = hashlib.sha256(
        json.dumps(
            {"source": source, "runtime": runtime},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return source, digest


def require_cpp_batched_backend(*, build_root: str | Path | None = None) -> ctypes.CDLL:
    """Load the exact candidate DLL; overrides and Python fallback are forbidden."""

    if build_root is not None:
        raise ValueError("the TBCC source-keyed loader has one fixed candidate build root")
    source_digest, fast_key = _source_runtime_key()
    cached = _LOADED_BY_SOURCE_RUNTIME.get(fast_key)
    if cached is not None:
        return cached[1]
    build_key = _build_key(source_digest, native_toolchain_identity(), runtime_abi_identity())
    library = _configure_library(ctypes.CDLL(str(_compiled_path(build_key))))
    _LOADED_BY_SOURCE_RUNTIME[fast_key] = (build_key, library)
    return library


def clear_process_local_cache_for_tests() -> None:
    """Clear only Python's CDLL map; compiled artifacts remain durable."""

    _LOADED_BY_SOURCE_RUNTIME.clear()


def native_artifact_identity() -> dict[str, object]:
    started = time.perf_counter()
    library = require_cpp_batched_backend()
    load_seconds = time.perf_counter() - started
    path = Path(vars(library)["_name"]).resolve()
    return {
        "schema": "SCDMP-TBCC-R02-NATIVE-ARTIFACT-IDENTITY-V1",
        "component": "scdmp.tbcc_order_value.r02.full_host",
        "host": "QUAD-UAV-PALLET-GANTRY-24P5M-v1",
        "artifact_path": str(path),
        "artifact_sha256": _sha256_file(path),
        "artifact_size": path.stat().st_size,
        "source_path": str(_SOURCE.resolve()),
        "source_sha256": native_source_sha256(),
        "build_key": native_build_key(),
        "toolchain": native_toolchain_identity(),
        "runtime_abi": runtime_abi_identity(),
        "abi_version": NATIVE_ABI_VERSION,
        "fixture_magic": FIXTURE_MAGIC,
        "max_batch_width": MAX_BATCH_WIDTH,
        "functional_batch_widths": list(FUNCTIONAL_BATCH_WIDTHS),
        "full_reset_step_cpp": True,
        "python_environment_state": False,
        "python_plant_transition": False,
        "python_fallback": False,
        "load_seconds": load_seconds,
    }


def _reset_input(value: ResetLane) -> _ResetInput:
    if not isinstance(value, ResetLane):
        raise TypeError("reset rows must be ResetLane values")
    value.validate()
    return _ResetInput(
        FIXTURE_MAGIC,
        NATIVE_ABI_VERSION,
        value.middle_events[0],
        value.middle_events[1],
        value.k_initial,
        value.resolved_k_after,
        value.resolved_switch_tick,
        int(value.active),
        float(value.initial_v),
        float(value.initial_y),
        float(value.initial_phi),
    )


def _renewal_input(value: RenewalLane) -> _RenewalInput:
    value.validate()
    return _RenewalInput(
        int(value.active),
        value.action,
        (ctypes.c_double * MAX_HOLD_TICKS)(*value.eta_v),
        (ctypes.c_double * MAX_HOLD_TICKS)(*value.eta_y),
        (ctypes.c_double * MAX_HOLD_TICKS)(*value.eta_omega),
    )


def _output(value: _HostOutput) -> HostOutput:
    if value.status != 0:
        raise NativeBackendError(f"native lane returned status {value.status}")
    reward_count = int(value.last_hold_reward_count)
    reward_trace = tuple(float(item) for item in value.last_hold_rewards)
    if reward_count != int(value.ticks_advanced):
        raise NativeBackendError("native reward-trace count does not equal ticks_advanced")
    if not 0 <= reward_count <= MAX_HOLD_TICKS:
        raise NativeBackendError("native reward-trace count exceeds ABI capacity")
    if any(not math.isfinite(item) for item in reward_trace):
        raise NativeBackendError("native reward trace contains a nonfinite value")
    if any(item != 0.0 for item in reward_trace[reward_count:]):
        raise NativeBackendError("native reward trace has a noncanonical inactive tail")
    return HostOutput(
        advanced=bool(value.advanced),
        active=bool(value.active),
        terminal=bool(value.terminal),
        ticks_advanced=int(value.ticks_advanced),
        tick=int(value.n),
        hold_k=int(value.hold_k),
        next_k=int(value.next_k),
        observation=tuple(float(item) for item in value.observation),
        safe_dock=bool(value.safe_dock),
        timeout=bool(value.timeout),
        cable_overload=bool(value.cable_overload),
        gantry_contact=bool(value.gantry_contact),
        attitude_loss=bool(value.attitude_loss),
        formation_loss=bool(value.formation_loss),
        cumulative_reward=float(value.reward_sum),
        cumulative_energy=float(value.energy_sum),
        energy_ticks=int(value.energy_ticks),
        dock_tick=None if value.dock_tick < 0 else int(value.dock_tick),
        last_hold_reward_count=reward_count,
        last_hold_rewards=reward_trace,
    )


class NativeBatch:
    """One opaque fixed-width native session preserving original lane positions."""

    def __init__(self, resets: Iterable[ResetLane]) -> None:
        materialized = tuple(resets)
        width = len(materialized)
        if width < 1 or width > MAX_BATCH_WIDTH:
            raise ValueError(f"native batch width must be in [1, {MAX_BATCH_WIDTH}]")
        inputs = (_ResetInput * width)(*(_reset_input(value) for value in materialized))
        handles = (ctypes.c_uint64 * width)()
        outputs = (_HostOutput * width)()
        library = require_cpp_batched_backend()
        status = int(library.tbcc_r02_reset_batch(inputs, width, handles, outputs))
        if status != 0:
            raise NativeBackendError(f"native reset rejected the complete batch with status {status}")
        self._library = library
        self._handles = handles
        self._width = width
        self._open = True
        self.initial = tuple(_output(value) for value in outputs)
        self._last = self.initial

    @property
    def width(self) -> int:
        return self._width

    @property
    def active_lanes(self) -> tuple[int, ...]:
        return tuple(index for index, output in enumerate(self._last) if output.active)

    def renew(self, rows: Iterable[RenewalLane]) -> tuple[HostOutput, ...]:
        if not self._open:
            raise NativeBackendError("native TBCC session is closed")
        materialized = materialize_rows(rows)
        if len(materialized) != self._width:
            raise ValueError("renewal batch must preserve the reset width and lane positions")
        inputs = (_RenewalInput * self._width)(*(_renewal_input(value) for value in materialized))
        outputs = (_HostOutput * self._width)()
        status = int(
            self._library.tbcc_r02_renew_batch(
                self._handles, inputs, self._width, outputs
            )
        )
        if status != 0:
            raise NativeBackendError(f"native renewal rejected the complete batch with status {status}")
        self._last = tuple(_output(value) for value in outputs)
        return self._last

    step = renew

    def close(self) -> None:
        if not self._open:
            return
        status = int(self._library.tbcc_r02_close_batch(self._handles, self._width))
        if status != 0:
            raise NativeBackendError(f"native close rejected the session with status {status}")
        self._open = False

    def __enter__(self) -> "NativeBatch":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def public_first_renewal_observation(reset: ResetLane) -> tuple[float, ...]:
    """Return the public native reset observation; latent graph state is omitted."""

    with NativeBatch((reset,)) as batch:
        return batch.initial[0].observation


def test_only_setup_composition(events: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, ...], int], ...]:
    """TEST-only native fixture endpoint; never used by production sessions."""

    materialized = tuple(events)
    if not materialized:
        raise ValueError("setup fixture batch must be nonempty")
    inputs = (_SetupFixtureInput * len(materialized))(
        *(
            _SetupFixtureInput(FIXTURE_MAGIC, NATIVE_ABI_VERSION, event[0], event[1])
            for event in materialized
        )
    )
    outputs = (_SetupFixtureOutput * len(materialized))()
    status = int(
        require_cpp_batched_backend().tbcc_r02_test_setup_batch(
            inputs, len(materialized), outputs
        )
    )
    if status != 0:
        raise NativeBackendError(f"native TEST setup fixture rejected batch with status {status}")
    return tuple((tuple(int(item) for item in value.p), int(value.q)) for value in outputs)


def test_only_primitive(
    *,
    q: int,
    tick: int,
    x: float,
    v: float,
    y: float,
    w: float,
    phi: float,
    omega: float,
    z: tuple[float, float, float, float],
    formation: float,
    prior_a: int,
    prior_r: tuple[int, int, int, int],
    action: int,
    eta_v: float,
    eta_y: float,
    eta_omega: float,
) -> HostOutput:
    """TEST-only one-tick native fixture endpoint for absorption conformance."""

    item = _PrimitiveFixtureInput()
    item.magic = FIXTURE_MAGIC
    item.abi_version = NATIVE_ABI_VERSION
    item.q = q
    item.n = tick
    item.x = x
    item.v = v
    item.y = y
    item.w = w
    item.phi = phi
    item.omega = omega
    item.z[:] = z
    item.formation = formation
    item.prior_a = prior_a
    item.prior_r[:] = prior_r
    item.action = action
    item.eta_v = eta_v
    item.eta_y = eta_y
    item.eta_omega = eta_omega
    output = _HostOutput()
    status = int(require_cpp_batched_backend().tbcc_r02_test_primitive(item, output))
    if status != 0:
        raise NativeBackendError(f"native TEST primitive fixture rejected input with status {status}")
    return _output(output)

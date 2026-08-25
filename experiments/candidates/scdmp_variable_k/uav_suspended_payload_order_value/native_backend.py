"""Source-keyed ctypes loader for the exact batched C++ SCDMP UAV host.

Compilation, loading, ABI, namespace, and execution failures are surfaced.
There is deliberately no Python fallback in this module.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import math
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Iterable

from .config import FIXTURE_MAGIC, HORIZON, MAX_QUERIES, FixtureInput
from .host_types import (
    MissionEndpoint,
    MissionResult,
    PublicObservation,
    RenewalAccounting,
    RenewalTransition,
    SetupSnapshot,
    TickRecord,
)


_SOURCE = Path(__file__).with_name("native") / "uav_sp_order_value_backend.cpp"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SCIENCE_CARD_PATH = (
    _REPOSITORY_ROOT
    / "docs"
    / "research"
    / "candidates"
    / "semigroup_consistent_duration_model_policy"
    / "SCDMP_UAV_SUSPENDED_PAYLOAD_ORDER_VALUE_SCIENCE_CARD_REVISION_02_20260820.md"
)
SCIENCE_CARD_SHA256 = "96f736738222623bbfd302942293f416151582abbb369d6e49c91aa418d8c367"
NATIVE_ABI_VERSION = 2
MSVC_COMPILE_FLAGS = (
    "/nologo",
    "/std:c++17",
    "/O2",
    "/EHsc",
    "/LD",
    "/fp:strict",
)


class NativeBackendError(RuntimeError):
    pass


class _Input(ctypes.Structure):
    _fields_ = [
        ("fixture_magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int),
        ("event_order", ctypes.c_int),
        ("regime", ctypes.c_int),
        ("switch_tick", ctypes.c_int),
        ("initial_v", ctypes.c_double),
        ("initial_phi", ctypes.c_double),
        ("actions", ctypes.c_int * MAX_QUERIES),
        ("eta_v", ctypes.c_double * HORIZON),
        ("eta_omega", ctypes.c_double * HORIZON),
    ]


class _ResetInput(ctypes.Structure):
    _fields_ = [
        ("fixture_magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int),
        ("event_order", ctypes.c_int),
        ("regime", ctypes.c_int),
        ("switch_tick", ctypes.c_int),
        ("initial_v", ctypes.c_double),
        ("initial_phi", ctypes.c_double),
        ("eta_v", ctypes.c_double * HORIZON),
        ("eta_omega", ctypes.c_double * HORIZON),
    ]


class _Tick(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_int)
        for name in ("tick", "k", "queried", "action_code", "u1", "u2", "u3")
    ] + [
        (name, ctypes.c_double)
        for name in (
            "x_before",
            "x_after",
            "v_after",
            "phi_after",
            "omega_after",
            "z_after",
            "f_after",
            "tau1_after",
            "tau2_after",
            "tau3_after",
            "reward",
            "effort",
        )
    ] + [
        (name, ctypes.c_int)
        for name in ("overload", "swing", "formation", "delivery", "timeout", "terminal")
    ]


class _Output(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int),
        ("event_order", ctypes.c_int),
        ("regime", ctypes.c_int),
        ("switch_tick", ctypes.c_int),
        ("initial_observation", ctypes.c_double * 14),
        ("hidden_d", ctypes.c_double),
        ("mode", ctypes.c_int),
        ("token_first", ctypes.c_int),
        ("token_second", ctypes.c_int),
        ("chronology_q", ctypes.c_double),
        ("allocated_slots", ctypes.c_int),
        ("integrated_ticks", ctypes.c_int),
        ("masked_slots", ctypes.c_int),
        ("policy_queries", ctypes.c_int),
        ("delivery", ctypes.c_int),
        ("timeout", ctypes.c_int),
        ("physical_failure", ctypes.c_int),
        ("overload", ctypes.c_int),
        ("swing", ctypes.c_int),
        ("formation", ctypes.c_int),
        ("terminal_tick", ctypes.c_int),
        ("delivery_time_seconds", ctypes.c_double),
        ("completion_time_seconds", ctypes.c_double),
        ("cumulative_reward", ctypes.c_double),
        ("mean_active_effort", ctypes.c_double),
        ("final_x", ctypes.c_double),
        ("final_v", ctypes.c_double),
        ("final_phi", ctypes.c_double),
        ("final_omega", ctypes.c_double),
        ("final_z", ctypes.c_double),
        ("final_f", ctypes.c_double),
        ("final_tau1", ctypes.c_double),
        ("final_tau2", ctypes.c_double),
        ("final_tau3", ctypes.c_double),
        ("ticks", _Tick * HORIZON),
    ]


class _RenewalOutput(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int),
        ("event_order", ctypes.c_int),
        ("regime", ctypes.c_int),
        ("switch_tick", ctypes.c_int),
        ("public_observation", ctypes.c_double * 14),
        ("token_first", ctypes.c_int),
        ("token_second", ctypes.c_int),
        ("chronology_q", ctypes.c_double),
        ("realized_duration", ctypes.c_int),
        ("primitive_reward_count", ctypes.c_int),
        ("primitive_rewards", ctypes.c_double * 14),
        ("reward_sum", ctypes.c_double),
        ("terminal", ctypes.c_int),
        ("delivery", ctypes.c_int),
        ("timeout", ctypes.c_int),
        ("physical_failure", ctypes.c_int),
        ("overload", ctypes.c_int),
        ("swing", ctypes.c_int),
        ("formation", ctypes.c_int),
        ("allocated_slots", ctypes.c_int),
        ("integrated_ticks", ctypes.c_int),
        ("masked_slots", ctypes.c_int),
        ("policy_queries", ctypes.c_int),
        ("terminal_tick", ctypes.c_int),
        ("delivery_time_seconds", ctypes.c_double),
        ("completion_time_seconds", ctypes.c_double),
        ("cumulative_reward", ctypes.c_double),
        ("mean_active_effort", ctypes.c_double),
    ]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def science_card_identity() -> dict[str, object]:
    if not SCIENCE_CARD_PATH.is_file():
        raise NativeBackendError(f"immutable SCDMP science card is missing: {SCIENCE_CARD_PATH}")
    digest = _sha256_file(SCIENCE_CARD_PATH)
    if digest != SCIENCE_CARD_SHA256:
        raise NativeBackendError("immutable SCDMP science card SHA-256 differs from revision 02")
    return {
        "path": str(SCIENCE_CARD_PATH.resolve()),
        "sha256": digest,
        "size": SCIENCE_CARD_PATH.stat().st_size,
    }


def native_source_sha256() -> str:
    return _sha256_file(_SOURCE)


def source_sha256() -> str:
    """Aggregate exact native source and immutable science-card identity."""

    card = science_card_identity()
    digest = hashlib.sha256()
    digest.update(b"SCDMP-UAV-SP-R02-SOURCE-IDENTITY-v2\0")
    for label, value in (
        ("native/uav_sp_order_value_backend.cpp", native_source_sha256()),
        (str(SCIENCE_CARD_PATH.relative_to(_REPOSITORY_ROOT)).replace("\\", "/"), str(card["sha256"])),
    ):
        encoded_label = label.encode("utf-8")
        digest.update(len(encoded_label).to_bytes(4, "big"))
        digest.update(encoded_label)
        digest.update(value.encode("ascii"))
    return digest.hexdigest()


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
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
    installation = Path(result.stdout.strip())
    if not installation.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    root = _vs_installation() / "VC" / "Tools" / "MSVC"
    candidates = tuple(root.glob("*/bin/Hostx64/x64/cl.exe"))
    candidates = tuple(path for path in candidates if path.is_file())
    if not candidates:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")

    def version(path: Path) -> tuple[int, ...]:
        try:
            return tuple(int(part) for part in path.parents[3].name.split("."))
        except ValueError:
            return (0,)

    return max(candidates, key=version)


@functools.lru_cache(maxsize=1)
def native_toolchain_identity() -> dict[str, object]:
    compiler = _compiler_path().resolve()
    probe = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    output = "\n".join(
        line.strip()
        for line in (probe.stdout + "\n" + probe.stderr).splitlines()
        if line.strip()
    )
    if "Microsoft" not in output or "C/C++" not in output:
        raise NativeBackendError("MSVC compiler identity could not be read")
    stat = compiler.stat()
    return {
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256_file(compiler),
        "compiler_size": stat.st_size,
        "compiler_mtime_ns": stat.st_mtime_ns,
        "compiler_version_output": output,
        "compile_flags": list(MSVC_COMPILE_FLAGS),
        "abi_version": NATIVE_ABI_VERSION,
    }


@functools.lru_cache(maxsize=1)
def native_build_key() -> str:
    toolchain = native_toolchain_identity()
    digest = hashlib.sha256()
    digest.update(b"SCDMP-UAV-SP-ORDER-VALUE-R02-NATIVE-BUILD-v1\0")
    digest.update(source_sha256().encode("ascii"))
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS:
        encoded = flag.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    digest.update(NATIVE_ABI_VERSION.to_bytes(4, "big"))
    return digest.hexdigest()


def _compiled_path() -> Path:
    cache = Path(tempfile.gettempdir()) / "hmasd_scdmp_uav_sp_r02_native" / native_build_key()
    dll = cache / "uav_sp_order_value_backend.dll"
    if dll.is_file():
        return dll
    cache.mkdir(parents=True, exist_ok=True)
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    obj = cache / "uav_sp_order_value_backend.obj"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /link /OUT:"{dll}"'
    )
    result = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dll.is_file():
        raise NativeBackendError(
            f"native SCDMP UAV host compilation failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return dll


@functools.lru_cache(maxsize=1)
def require_cpp_batched_backend() -> ctypes.CDLL:
    """Compile/load the exact source-keyed DLL or raise; never fall back."""

    library = ctypes.CDLL(str(_compiled_path()))
    library.scdmp_uav_sp_abi_version.argtypes = []
    library.scdmp_uav_sp_abi_version.restype = ctypes.c_int
    if library.scdmp_uav_sp_abi_version() != NATIVE_ABI_VERSION:
        raise NativeBackendError("SCDMP UAV native backend ABI mismatch")
    size_witnesses = {
        "reset_input": (_ResetInput, "scdmp_uav_sp_sizeof_reset_input"),
        "full_input": (_Input, "scdmp_uav_sp_sizeof_full_input"),
        "tick": (_Tick, "scdmp_uav_sp_sizeof_tick"),
        "renewal_output": (_RenewalOutput, "scdmp_uav_sp_sizeof_renewal_output"),
        "full_output": (_Output, "scdmp_uav_sp_sizeof_full_output"),
    }
    for label, (structure, symbol) in size_witnesses.items():
        function = getattr(library, symbol)
        function.argtypes = []
        function.restype = ctypes.c_size_t
        native_size = int(function())
        python_size = ctypes.sizeof(structure)
        if native_size != python_size:
            raise NativeBackendError(
                f"SCDMP UAV {label} ABI size mismatch: native={native_size}, ctypes={python_size}"
            )
    library.scdmp_uav_sp_run_batch.argtypes = [
        ctypes.POINTER(_Input),
        ctypes.c_int,
        ctypes.POINTER(_Output),
    ]
    library.scdmp_uav_sp_run_batch.restype = ctypes.c_int
    library.scdmp_uav_sp_reset_batch.argtypes = [
        ctypes.POINTER(_ResetInput),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(_RenewalOutput),
    ]
    library.scdmp_uav_sp_reset_batch.restype = ctypes.c_int
    library.scdmp_uav_sp_renew_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(_RenewalOutput),
    ]
    library.scdmp_uav_sp_renew_batch.restype = ctypes.c_int
    library.scdmp_uav_sp_close_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_int,
    ]
    library.scdmp_uav_sp_close_batch.restype = ctypes.c_int
    return library


def abi_size_identity() -> dict[str, int]:
    library = require_cpp_batched_backend()
    return {
        "reset_input": int(library.scdmp_uav_sp_sizeof_reset_input()),
        "full_input": int(library.scdmp_uav_sp_sizeof_full_input()),
        "tick": int(library.scdmp_uav_sp_sizeof_tick()),
        "renewal_output": int(library.scdmp_uav_sp_sizeof_renewal_output()),
        "full_output": int(library.scdmp_uav_sp_sizeof_full_output()),
    }


def native_artifact_identity() -> dict[str, object]:
    """Return exact source/build/artifact identity without running a host tick."""

    path = (
        Path(tempfile.gettempdir())
        / "hmasd_scdmp_uav_sp_r02_native"
        / native_build_key()
        / "uav_sp_order_value_backend.dll"
    )
    cached = path.is_file()
    started = time.perf_counter()
    library = require_cpp_batched_backend()
    elapsed = time.perf_counter() - started
    if library.scdmp_uav_sp_abi_version() != NATIVE_ABI_VERSION or not path.is_file():
        raise NativeBackendError("native artifact failed exact path/ABI verification")
    stat = path.stat()
    return {
        "artifact_path": str(path.resolve()),
        "artifact_sha256": _sha256_file(path),
        "artifact_size": stat.st_size,
        "artifact_mtime_ns": stat.st_mtime_ns,
        "source_sha256": source_sha256(),
        "native_source_sha256": native_source_sha256(),
        "science_card": science_card_identity(),
        "build_key": native_build_key(),
        "abi_version": NATIVE_ABI_VERSION,
        "abi_sizes": abi_size_identity(),
        "binding_kind": "ctypes_cdll",
        "python_fallback": False,
        "first_compile_seconds": None if cached else elapsed,
        "compile_time_status": "cache_present_unknown" if cached else "measured_first_compile",
    }


def _native_input(fixture: FixtureInput) -> _Input:
    fixture.validate()
    item = _Input()
    item.fixture_magic = FIXTURE_MAGIC
    item.abi_version = NATIVE_ABI_VERSION
    item.event_order = int(fixture.event_order)
    item.regime = int(fixture.regime)
    item.switch_tick = fixture.switch_tick
    item.initial_v = fixture.initial_v
    item.initial_phi = fixture.initial_phi
    for index, value in enumerate(fixture.actions):
        item.actions[index] = value
    for index in range(HORIZON):
        item.eta_v[index] = fixture.eta_v[index]
        item.eta_omega[index] = fixture.eta_omega[index]
    return item


def _reset_input(fixture: FixtureInput) -> _ResetInput:
    fixture.validate()
    item = _ResetInput()
    item.fixture_magic = FIXTURE_MAGIC
    item.abi_version = NATIVE_ABI_VERSION
    item.event_order = int(fixture.event_order)
    item.regime = int(fixture.regime)
    item.switch_tick = fixture.switch_tick
    item.initial_v = fixture.initial_v
    item.initial_phi = fixture.initial_phi
    for index in range(HORIZON):
        item.eta_v[index] = fixture.eta_v[index]
        item.eta_omega[index] = fixture.eta_omega[index]
    return item


def _native_bool(value: int, label: str) -> bool:
    if value not in (0, 1):
        raise NativeBackendError(f"native {label} is not binary")
    return bool(value)


def _decode_native_tokens(first: int, second: int) -> tuple[str, str]:
    registry = {0: "RETENSION", 1: "CROSSWIND"}
    if first not in registry or second not in registry or first == second:
        raise NativeBackendError("native setup token fields are invalid")
    return (registry[first], registry[second])


def _validate_metadata(
    fixture: FixtureInput,
    *,
    event_order: int,
    regime: int,
    switch_tick: int,
    token_first: int,
    token_second: int,
    chronology_q: float,
) -> tuple[str, str]:
    if (
        event_order != int(fixture.event_order)
        or regime != int(fixture.regime)
        or switch_tick != fixture.switch_tick
    ):
        raise NativeBackendError("native result metadata differs from its fixture input")
    tokens = _decode_native_tokens(token_first, token_second)
    if tokens != fixture.event_order.tokens:
        raise NativeBackendError("native setup token fields disagree with event_order")
    if chronology_q != fixture.event_order.q:
        raise NativeBackendError("native chronology surface disagrees with event_order")
    return tokens


def _tick(record: _Tick) -> TickRecord:
    for label in ("queried", "overload", "swing", "formation", "delivery", "timeout", "terminal"):
        _native_bool(int(getattr(record, label)), f"tick.{label}")
    if record.k not in (4, 6, 10, 14) or not 0 <= record.action_code < 27:
        raise NativeBackendError("native tick has an invalid k or action code")
    expected_command = (
        record.action_code // 9,
        (record.action_code // 3) % 3,
        record.action_code % 3,
    )
    if (record.u1, record.u2, record.u3) != expected_command:
        raise NativeBackendError("native tick action code and command differ")
    floating = (
        record.x_before, record.x_after, record.v_after, record.phi_after,
        record.omega_after, record.z_after, record.f_after, record.tau1_after,
        record.tau2_after, record.tau3_after, record.reward, record.effort,
    )
    if not all(math.isfinite(value) for value in floating):
        raise NativeBackendError("native tick contains a nonfinite value")
    return TickRecord(
        tick=record.tick,
        k=record.k,
        policy_queried=bool(record.queried),
        action_code=record.action_code,
        command=(record.u1, record.u2, record.u3),
        x_before=record.x_before,
        x_after=record.x_after,
        v_after=record.v_after,
        phi_after=record.phi_after,
        omega_after=record.omega_after,
        z_after=record.z_after,
        f_after=record.f_after,
        tensions_after=(record.tau1_after, record.tau2_after, record.tau3_after),
        reward=record.reward,
        effort=record.effort,
        overload=bool(record.overload),
        swing=bool(record.swing),
        formation=bool(record.formation),
        delivery=bool(record.delivery),
        timeout=bool(record.timeout),
        terminal=bool(record.terminal),
    )


def _result(fixture: FixtureInput, output: _Output) -> MissionResult:
    if output.status != 0:
        raise NativeBackendError(f"native SCDMP UAV output status was {output.status}")
    tokens = _validate_metadata(
        fixture,
        event_order=output.event_order,
        regime=output.regime,
        switch_tick=output.switch_tick,
        token_first=output.token_first,
        token_second=output.token_second,
        chronology_q=output.chronology_q,
    )
    for label in ("delivery", "timeout", "physical_failure", "overload", "swing", "formation"):
        _native_bool(int(getattr(output, label)), label)
    if (
        output.allocated_slots != HORIZON
        or not 1 <= output.integrated_ticks <= HORIZON
        or output.masked_slots != HORIZON - output.integrated_ticks
        or not 1 <= output.policy_queries <= MAX_QUERIES
        or output.terminal_tick != output.integrated_ticks
    ):
        raise NativeBackendError("native terminal workload/count shape is invalid")
    physical = bool(output.overload or output.swing or output.formation)
    if bool(output.physical_failure) != physical:
        raise NativeBackendError("native physical-failure aggregate differs from indicators")
    if sum((bool(output.delivery), bool(output.timeout), physical)) != 1:
        raise NativeBackendError("native terminal outcome is not exactly one delivery/timeout/failure")
    expected_hidden = 0.55 if fixture.event_order.value == 0 else 0.0
    if output.mode != 1 or output.hidden_d != expected_hidden:
        raise NativeBackendError("native setup private-state audit differs from exact event map")
    finite = tuple(output.initial_observation) + (
        output.hidden_d, output.delivery_time_seconds, output.completion_time_seconds,
        output.cumulative_reward, output.mean_active_effort, output.final_x, output.final_v,
        output.final_phi, output.final_omega, output.final_z, output.final_f,
        output.final_tau1, output.final_tau2, output.final_tau3,
    )
    if not all(math.isfinite(value) for value in finite):
        raise NativeBackendError("native terminal output contains a nonfinite value")
    if (bool(output.delivery) and output.delivery_time_seconds < 0.0) or (
        not bool(output.delivery) and output.delivery_time_seconds != -1.0
    ):
        raise NativeBackendError("native delivery-time sentinel is invalid")
    observation = PublicObservation(*tuple(output.initial_observation))
    setup = SetupSnapshot(
        public=observation,
        hidden_d_fixture_audit=output.hidden_d,
        mode=output.mode,
        event_tokens=tokens,
        chronology_q=output.chronology_q,
    )
    trace = tuple(_tick(output.ticks[index]) for index in range(output.integrated_ticks))
    if any(record.tick != index for index, record in enumerate(trace)):
        raise NativeBackendError("native trace ticks are not contiguous from zero")
    if any(record.terminal for record in trace[:-1]) or not trace[-1].terminal:
        raise NativeBackendError("native trace does not have one final terminal record")
    if sum(record.policy_queried for record in trace) != output.policy_queries:
        raise NativeBackendError("native query counter differs from the trace")
    last = trace[-1]
    if (
        last.delivery != bool(output.delivery)
        or last.timeout != bool(output.timeout)
        or last.overload != bool(output.overload)
        or last.swing != bool(output.swing)
        or last.formation != bool(output.formation)
        or (last.x_after, last.v_after, last.phi_after, last.omega_after,
            last.z_after, last.f_after, *last.tensions_after)
        != (output.final_x, output.final_v, output.final_phi, output.final_omega,
            output.final_z, output.final_f, output.final_tau1, output.final_tau2,
            output.final_tau3)
    ):
        raise NativeBackendError("native endpoint fields differ from the final trace record")
    if not math.isclose(
        sum(record.reward for record in trace), output.cumulative_reward,
        rel_tol=0.0, abs_tol=2e-12,
    ):
        raise NativeBackendError("native cumulative reward differs from the trace")
    endpoint = MissionEndpoint(
        allocated_slots=output.allocated_slots,
        integrated_ticks=output.integrated_ticks,
        masked_post_absorption_slots=output.masked_slots,
        policy_queries=output.policy_queries,
        delivery=bool(output.delivery),
        timeout=bool(output.timeout),
        physical_failure=bool(output.physical_failure),
        overload=bool(output.overload),
        swing=bool(output.swing),
        formation=bool(output.formation),
        terminal_tick=output.terminal_tick,
        delivery_time_seconds=(output.delivery_time_seconds if output.delivery else None),
        completion_time_seconds=output.completion_time_seconds,
        cumulative_reward=output.cumulative_reward,
        mean_active_effort=output.mean_active_effort,
        final_x=output.final_x,
        final_v=output.final_v,
        final_phi=output.final_phi,
        final_omega=output.final_omega,
        final_z=output.final_z,
        final_f=output.final_f,
        final_tensions=(output.final_tau1, output.final_tau2, output.final_tau3),
        hidden_d_fixture_audit=output.hidden_d,
        mode=output.mode,
    )
    return MissionResult(setup=setup, trace=trace, endpoint=endpoint)


def _renewal_transition(fixture: FixtureInput, output: _RenewalOutput) -> RenewalTransition:
    if output.status != 0:
        raise NativeBackendError(f"native renewal output status was {output.status}")
    tokens = _validate_metadata(
        fixture,
        event_order=output.event_order,
        regime=output.regime,
        switch_tick=output.switch_tick,
        token_first=output.token_first,
        token_second=output.token_second,
        chronology_q=output.chronology_q,
    )
    for label in ("terminal", "delivery", "timeout", "physical_failure", "overload", "swing", "formation"):
        _native_bool(int(getattr(output, label)), f"renewal.{label}")
    if (
        output.allocated_slots != HORIZON
        or not 0 <= output.integrated_ticks <= HORIZON
        or not 0 <= output.policy_queries <= MAX_QUERIES
        or not 0 <= output.realized_duration <= 14
        or output.primitive_reward_count != output.realized_duration
    ):
        raise NativeBackendError("native renewal workload/count shape is invalid")
    terminal = bool(output.terminal)
    expected_masked = HORIZON - output.integrated_ticks if terminal else 0
    if output.masked_slots != expected_masked:
        raise NativeBackendError("native renewal masked-slot count is invalid")
    physical = bool(output.overload or output.swing or output.formation)
    if bool(output.physical_failure) != physical:
        raise NativeBackendError("native renewal physical-failure aggregate differs")
    if terminal:
        if sum((bool(output.delivery), bool(output.timeout), physical)) != 1:
            raise NativeBackendError("terminal renewal lacks one exact terminal outcome")
        if output.terminal_tick != output.integrated_ticks:
            raise NativeBackendError("terminal renewal tick differs from integrated count")
    elif any((output.delivery, output.timeout, output.physical_failure, output.terminal_tick)):
        raise NativeBackendError("active renewal carries a terminal-only field")
    rewards = tuple(output.primitive_rewards[: output.primitive_reward_count])
    unused = tuple(output.primitive_rewards[output.primitive_reward_count :])
    finite = tuple(output.public_observation) + rewards + (
        output.reward_sum, output.delivery_time_seconds, output.completion_time_seconds,
        output.cumulative_reward, output.mean_active_effort,
    )
    if not all(math.isfinite(value) for value in finite) or any(value != 0.0 for value in unused):
        raise NativeBackendError("native renewal contains nonfinite or nonzero unused data")
    if not math.isclose(sum(rewards), output.reward_sum, rel_tol=0.0, abs_tol=2e-12):
        raise NativeBackendError("native renewal reward sum differs from primitive rewards")
    if output.delivery:
        if output.delivery_time_seconds < 0.0 or output.completion_time_seconds != output.delivery_time_seconds:
            raise NativeBackendError("delivered renewal has invalid completion time")
    elif terminal:
        if output.delivery_time_seconds != -1.0 or output.completion_time_seconds != 42.0:
            raise NativeBackendError("unsuccessful terminal renewal has invalid completion time")
    elif output.delivery_time_seconds != -1.0 or output.completion_time_seconds != -1.0:
        raise NativeBackendError("active renewal exposes terminal completion time")
    accounting = RenewalAccounting(
        allocated_slots=output.allocated_slots,
        integrated_ticks=output.integrated_ticks,
        masked_post_absorption_slots=output.masked_slots,
        policy_queries=output.policy_queries,
        terminal_tick=output.terminal_tick if terminal else None,
        delivery_time_seconds=output.delivery_time_seconds if output.delivery else None,
        completion_time_seconds=output.completion_time_seconds if terminal else None,
        cumulative_reward=output.cumulative_reward,
        mean_active_effort=output.mean_active_effort,
    )
    return RenewalTransition(
        public=PublicObservation(*tuple(output.public_observation)),
        event_tokens=tokens,
        chronology_q=output.chronology_q,
        realized_duration=output.realized_duration,
        primitive_rewards=rewards,
        reward=output.reward_sum,
        terminal=terminal,
        delivery=bool(output.delivery),
        timeout=bool(output.timeout),
        physical_failure=physical,
        overload=bool(output.overload),
        swing=bool(output.swing),
        formation=bool(output.formation),
        accounting=accounting,
    )


class NativeRenewalBatch:
    """Opaque-state batched native renewal session for deterministic fixtures."""

    def __init__(
        self,
        fixtures: tuple[FixtureInput, ...],
        handles: ctypes.Array[ctypes.c_void_p],
    ) -> None:
        self._fixtures = fixtures
        self._handles = handles
        self._terminal = [False] * len(fixtures)
        self._closed = False
        self._lock = threading.RLock()

    @property
    def batch_width(self) -> int:
        return len(self._fixtures)

    @property
    def active(self) -> tuple[bool, ...]:
        with self._lock:
            return tuple(not terminal for terminal in self._terminal)

    def advance(self, actions: Iterable[int | None]) -> tuple[RenewalTransition, ...]:
        with self._lock:
            if self._closed:
                raise NativeBackendError("native renewal batch is closed")
            materialized = tuple(actions)
            if len(materialized) != self.batch_width:
                raise ValueError("renewal action count must equal the fixed batch width")
            encoded: list[int] = []
            for index, (action, terminal) in enumerate(zip(materialized, self._terminal)):
                if terminal:
                    if action is not None:
                        raise ValueError(f"terminal batch member {index} forbids a post-absorption action")
                    encoded.append(-1)
                else:
                    if isinstance(action, bool) or not isinstance(action, int) or not 0 <= action < 27:
                        raise ValueError(f"active batch member {index} requires one action code in [0,27)")
                    encoded.append(action)
            native_actions = (ctypes.c_int * self.batch_width)(*encoded)
            outputs = (_RenewalOutput * self.batch_width)()
            status = require_cpp_batched_backend().scdmp_uav_sp_renew_batch(
                self._handles, native_actions, self.batch_width, outputs
            )
            if status != 0:
                raise NativeBackendError(f"native SCDMP UAV renewal batch failed with status {status}")
            try:
                converted = tuple(
                    _renewal_transition(fixture, output)
                    for fixture, output in zip(self._fixtures, outputs)
                )
            except BaseException as conversion_error:
                try:
                    self._close_locked()
                except BaseException as close_error:
                    raise NativeBackendError(
                        "native renewal output validation failed and state close also failed"
                    ) from ExceptionGroup(
                        "native renewal conversion/close failures",
                        [conversion_error, close_error],
                    )
                raise
            self._terminal = [item.terminal for item in converted]
            return converted

    def close(self) -> None:
        with self._lock:
            self._close_locked()

    def _close_locked(self) -> None:
        if self._closed:
            return
        try:
            status = require_cpp_batched_backend().scdmp_uav_sp_close_batch(
                self._handles, self.batch_width
            )
        finally:
            # Even a native close anomaly must make reuse impossible.
            self._closed = True
        if status != 0:
            raise NativeBackendError(f"native SCDMP UAV state close failed with status {status}")

    def __enter__(self) -> "NativeRenewalBatch":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        if getattr(self, "_closed", True):
            return
        try:
            self.close()
        except Exception:
            pass


def reset_native_renewal_batch(
    fixtures: Iterable[FixtureInput],
) -> tuple[NativeRenewalBatch, tuple[RenewalTransition, ...]]:
    """Reset an opaque native batch and return controller-facing initial surfaces."""

    materialized = tuple(fixtures)
    if not materialized:
        raise ValueError("native renewal batch must be nonempty")
    inputs = (_ResetInput * len(materialized))(*(_reset_input(item) for item in materialized))
    handles = (ctypes.c_void_p * len(materialized))()
    outputs = (_RenewalOutput * len(materialized))()
    status = require_cpp_batched_backend().scdmp_uav_sp_reset_batch(
        inputs, len(materialized), handles, outputs
    )
    if status != 0:
        raise NativeBackendError(f"native SCDMP UAV reset batch failed with status {status}")
    batch = NativeRenewalBatch(materialized, handles)
    try:
        starts = tuple(
            _renewal_transition(fixture, output)
            for fixture, output in zip(materialized, outputs)
        )
        if any(
            start.realized_duration != 0
            or start.accounting.integrated_ticks != 0
            or start.accounting.policy_queries != 0
            or start.terminal
            for start in starts
        ):
            raise NativeBackendError("native reset returned a noninitial renewal surface")
    except BaseException:
        batch.close()
        raise
    return batch, starts


def run_native_batch(fixtures: Iterable[FixtureInput]) -> tuple[MissionResult, ...]:
    """Execute one nonempty fixture batch through the single native boundary."""

    materialized = tuple(fixtures)
    if not materialized:
        raise ValueError("native full-host batch must be nonempty")
    inputs = (_Input * len(materialized))(*(_native_input(item) for item in materialized))
    outputs = (_Output * len(materialized))()
    status = require_cpp_batched_backend().scdmp_uav_sp_run_batch(
        inputs, len(materialized), outputs
    )
    if status != 0:
        raise NativeBackendError(f"native SCDMP UAV batch failed with status {status}")
    return tuple(_result(fixture, output) for fixture, output in zip(materialized, outputs))

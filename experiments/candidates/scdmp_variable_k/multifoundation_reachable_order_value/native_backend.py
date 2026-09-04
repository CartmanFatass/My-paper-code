"""Isolated native snapshot/clone host for SCDMP-MF-RS-MK-ORDER-VALUE-B01.

The C++ data plane preserves the QUAD-UAV-PALLET-GANTRY tick, action, reward,
absorption, and external-hold semantics.  Python owns only validation, complete
POD byte transport, treatment-common tape addressing, and batched policy calls.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Iterable

from .native_state import (
    ALLOWED_K,
    BranchEvaluation,
    DisturbanceHold,
    HORIZON_TICKS,
    HR_ASSIGNMENT,
    HostOutput,
    MAX_BATCH_WIDTH,
    MAX_HOLD_TICKS,
    NativeState,
    RH_ASSIGNMENT,
    ReachableTwins,
    SourceScanReceipt,
    SourceCandidateWitness,
    SourceRenewalWitness,
    TapeAddress,
    TapeNamespace,
    TARGET_TICKS,
    BatchedPolicy,
    validate_actions,
)
from .contracts import RunManifest, STATE_SPECS, TRAINING_SEEDS, StateSpec
from .rng import (
    development_tape_address, materialize_disturbance_tape, source_reset_values,
    source_tape_address,
)

_ABI_VERSION = 3
_MAGIC = 0x4D4652534D4B3031
_ORDER_HR = 1
_ORDER_RH = 2
_SOURCE = Path(__file__).with_name("native") / "mf_rs_native.cpp"
_BUILD_ROOT = Path(tempfile.gettempdir()) / "hmasd_scdmp_mf_rs_mk_native"
_COMPILE_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/W4")
_BUILD_RECEIPT_SCHEMA = "SCDMP_MF_RS_NATIVE_BUILD_V1"
_BUILD_RECEIPT_NAME = "build-receipt.json"


class NativeBackendError(RuntimeError):
    """The isolated native ABI rejected a state, input, or lifecycle fact."""


class ReachableStatePanelNotEstablished(RuntimeError):
    """Valid bounded-support diagnosis after all eight source candidates."""

    def __init__(
        self, receipts: tuple[SourceScanReceipt, ...],
        witnesses: tuple[SourceCandidateWitness, ...] = (),
    ) -> None:
        super().__init__("all eight source tapes failed to reach an eligible target boundary")
        self.receipts = receipts
        self.transitions = sum(row.transitions for row in receipts)
        self.policy_queries = sum(row.policy_queries for row in receipts)
        self.witnesses = witnesses


class _ResetInput(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("k", ctypes.c_int32),
        ("active", ctypes.c_int32),
        ("pre_event_q", ctypes.c_int32),
        ("initial_v", ctypes.c_double),
        ("initial_y", ctypes.c_double),
        ("initial_phi", ctypes.c_double),
    ]


class _StepInput(ctypes.Structure):
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


class _NativeState(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("event_phase", ctypes.c_int32),
        ("event_order", ctypes.c_int32),
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
        ("p", ctypes.c_int32 * 4),
        ("q", ctypes.c_int32),
        ("n", ctypes.c_int32),
        ("current_k", ctypes.c_int32),
        ("enabled", ctypes.c_int32),
        ("terminal", ctypes.c_int32),
        ("safe_dock", ctypes.c_int32),
        ("timeout", ctypes.c_int32),
        ("cable_overload", ctypes.c_int32),
        ("gantry_contact", ctypes.c_int32),
        ("attitude_loss", ctypes.c_int32),
        ("formation_loss", ctypes.c_int32),
        ("reward_sum", ctypes.c_double),
        ("energy_sum", ctypes.c_double),
        ("energy_ticks", ctypes.c_int32),
        ("dock_tick", ctypes.c_int32),
        ("cached", _HostOutput),
    ]


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    completed = subprocess.run(
        [str(locator), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = Path(completed.stdout.strip())
    if not root.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return root


def _compiler_path() -> Path:
    candidates = tuple((_vs_installation() / "VC/Tools/MSVC").glob("*/bin/Hostx64/x64/cl.exe"))
    if not candidates:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")
    return max(candidates, key=lambda path: path.parents[3].name).resolve()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: dict[str, object]) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise NativeBackendError("native build binding is not canonical JSON") from error


def _compiler_version(compiler: Path) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [str(compiler), "/Bv"], capture_output=True, check=False,
        )
    except OSError as error:
        raise NativeBackendError("the selected compiler version cannot be measured") from error
    direct = bytes(completed.stdout) + bytes(completed.stderr)
    if not direct:
        raise NativeBackendError("the selected compiler returned no direct version evidence")
    return {
        "command": [str(compiler), "/Bv"],
        "returncode": int(completed.returncode),
        "output_sha256": _sha256_bytes(direct),
        "output_utf8": direct.decode("utf-8", errors="replace"),
    }


def _direct_build_facts() -> dict[str, object]:
    try:
        source = _SOURCE.resolve(strict=True)
        source_bytes = source.read_bytes()
        compiler = _compiler_path().resolve(strict=True)
        compiler_bytes = compiler.read_bytes()
    except OSError as error:
        raise NativeBackendError("native source or compiler bytes cannot be measured") from error
    return {
        "schema": _BUILD_RECEIPT_SCHEMA,
        "native_cpp_source": {
            "resolved_path": str(source),
            "byte_size": len(source_bytes),
            "sha256": _sha256_bytes(source_bytes),
        },
        "compiler": {
            "resolved_executable": str(compiler),
            "byte_size": len(compiler_bytes),
            "sha256": _sha256_bytes(compiler_bytes),
            "version": _compiler_version(compiler),
        },
        "compile_flags": list(_COMPILE_FLAGS),
        "compile_argument_template": [
            str(compiler), *_COMPILE_FLAGS, str(source),
            "/Fo:{staging}/mf_rs_native.obj", "/Fe:{staging}/mf_rs_native.dll",
        ],
        "runtime_architecture": {
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "pointer_bits": 8 * ctypes.sizeof(ctypes.c_void_p),
            "python_cache_tag": sys.implementation.cache_tag,
            "compiler_target": "x64",
        },
    }


def _build_key(facts: dict[str, object]) -> str:
    return _sha256_bytes(_canonical_json(facts))


def _read_build_receipt(cache: Path, facts: dict[str, object]) -> dict[str, object]:
    expected_key = _build_key(facts)
    if cache.name != expected_key:
        raise NativeBackendError("native cache path does not match the direct build key")
    receipt_path = cache / _BUILD_RECEIPT_NAME
    dll = cache / "mf_rs_native.dll"
    try:
        encoded = receipt_path.read_bytes()
        receipt = json.loads(encoded.decode("utf-8"))
        dll_bytes = dll.read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise NativeBackendError("native cache receipt or DLL is unavailable") from error
    if not isinstance(receipt, dict) or _canonical_json(receipt) != encoded:
        raise NativeBackendError("native build receipt is not canonical direct JSON")
    expected = {
        "schema": _BUILD_RECEIPT_SCHEMA,
        "cache_key_sha256": expected_key,
        "build_facts": facts,
        "dll": {
            "basename": "mf_rs_native.dll",
            "byte_size": len(dll_bytes),
            "sha256": _sha256_bytes(dll_bytes),
        },
    }
    if receipt != expected:
        raise NativeBackendError("native build receipt, cache key, or DLL bytes differ")
    if dll.resolve(strict=True).parent != cache.resolve(strict=True):
        raise NativeBackendError("native DLL resolved outside its keyed cache directory")
    return receipt


def _compile_into(staging: Path, facts: dict[str, object]) -> None:
    vcvars = _vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    compiler = Path(str(facts["compiler"]["resolved_executable"]))
    obj = staging / "mf_rs_native.obj"
    dll = staging / "mf_rs_native.dll"
    command = (
        f'call "{vcvars}" >nul && "{compiler}" {" ".join(_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /Fe:"{dll}"'
    )
    completed = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=staging,
        capture_output=True,
        text=True,
    )
    try:
        if completed.returncode != 0 or not dll.is_file():
            raise NativeBackendError(
                f"MF-RS native compilation failed ({completed.returncode}):\n"
                f"{completed.stdout}\n{completed.stderr}"
            )
    finally:
        obj.unlink(missing_ok=True)


def _compiled_path() -> Path:
    facts = _direct_build_facts()
    key = _build_key(facts)
    cache = _BUILD_ROOT / key
    dll = cache / "mf_rs_native.dll"
    if cache.exists():
        _read_build_receipt(cache, facts)
        return dll
    _BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{key}.", dir=_BUILD_ROOT))
    try:
        _compile_into(staging, facts)
        dll_bytes = (staging / "mf_rs_native.dll").read_bytes()
        receipt = {
            "schema": _BUILD_RECEIPT_SCHEMA,
            "cache_key_sha256": key,
            "build_facts": facts,
            "dll": {
                "basename": "mf_rs_native.dll",
                "byte_size": len(dll_bytes),
                "sha256": _sha256_bytes(dll_bytes),
            },
        }
        try:
            with (staging / _BUILD_RECEIPT_NAME).open("xb") as stream:
                stream.write(_canonical_json(receipt))
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as error:
            raise NativeBackendError("native build receipt publication is create-only") from error
        try:
            staging.rename(cache)
            staging = cache
        except FileExistsError:
            pass
    finally:
        if staging != cache:
            shutil.rmtree(staging, ignore_errors=True)
    _read_build_receipt(cache, facts)
    return dll


def _configure(library: ctypes.CDLL) -> ctypes.CDLL:
    library.mf_rs_abi_version.argtypes = []
    library.mf_rs_abi_version.restype = ctypes.c_int32
    library.mf_rs_magic.argtypes = []
    library.mf_rs_magic.restype = ctypes.c_uint64
    library.mf_rs_max_width.argtypes = []
    library.mf_rs_max_width.restype = ctypes.c_int32
    for suffix, ctype in (
        ("reset_input", _ResetInput), ("step_input", _StepInput),
        ("host_output", _HostOutput), ("native_state", _NativeState),
    ):
        function = getattr(library, f"mf_rs_sizeof_{suffix}")
        function.argtypes = []
        function.restype = ctypes.c_size_t
        if int(function()) != ctypes.sizeof(ctype):
            raise NativeBackendError(f"native ABI size mismatch for {suffix}")
    if int(library.mf_rs_abi_version()) != _ABI_VERSION:
        raise NativeBackendError("native ABI version mismatch")
    if int(library.mf_rs_magic()) != _MAGIC:
        raise NativeBackendError("native state magic mismatch")
    if int(library.mf_rs_max_width()) != MAX_BATCH_WIDTH:
        raise NativeBackendError("native maximum width mismatch")
    library.mf_rs_reset_batch.argtypes = [
        ctypes.POINTER(_ResetInput), ctypes.c_int32,
        ctypes.POINTER(_NativeState), ctypes.POINTER(_HostOutput),
    ]
    library.mf_rs_reset_batch.restype = ctypes.c_int32
    library.mf_rs_validate_state_batch.argtypes = [ctypes.POINTER(_NativeState), ctypes.c_int32]
    library.mf_rs_validate_state_batch.restype = ctypes.c_int32
    library.mf_rs_step_batch.argtypes = [
        ctypes.POINTER(_NativeState), ctypes.POINTER(_StepInput), ctypes.c_int32,
        ctypes.POINTER(_HostOutput),
    ]
    library.mf_rs_step_batch.restype = ctypes.c_int32
    library.mf_rs_apply_order_batch.argtypes = [
        ctypes.POINTER(_NativeState), ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(_HostOutput),
    ]
    library.mf_rs_apply_order_batch.restype = ctypes.c_int32
    library.mf_rs_verify_transition.argtypes = [
        ctypes.POINTER(_NativeState), ctypes.POINTER(_StepInput), ctypes.POINTER(_NativeState),
        ctypes.POINTER(_NativeState), ctypes.POINTER(_HostOutput),
    ]
    library.mf_rs_verify_transition.restype = ctypes.c_int32
    return library


@functools.lru_cache(maxsize=1)
def require_native_backend() -> ctypes.CDLL:
    return _configure(ctypes.CDLL(str(_compiled_path())))


def native_abi_identity() -> dict[str, object]:
    """Return the loaded ABI3 together with its revalidated build binding."""

    library = require_native_backend()
    library_path = Path(str(vars(library).get("_name", ""))).resolve(strict=True)
    build_binding = _read_build_receipt(library_path.parent, _direct_build_facts())
    return {
        "abi_version": int(library.mf_rs_abi_version()),
        "magic": int(library.mf_rs_magic()),
        "max_batch_width": int(library.mf_rs_max_width()),
        "struct_sizes": {
            "reset_input": int(library.mf_rs_sizeof_reset_input()),
            "step_input": int(library.mf_rs_sizeof_step_input()),
            "host_output": int(library.mf_rs_sizeof_host_output()),
            "native_state": int(library.mf_rs_sizeof_native_state()),
        },
        "python_struct_sizes": {
            "reset_input": ctypes.sizeof(_ResetInput),
            "step_input": ctypes.sizeof(_StepInput),
            "host_output": ctypes.sizeof(_HostOutput),
            "native_state": ctypes.sizeof(_NativeState),
        },
        "compiled_library_resolved_path": str(library_path),
        "build_receipt_resolved_path": str((library_path.parent / _BUILD_RECEIPT_NAME).resolve(strict=True)),
        "build_binding": build_binding,
    }


def _host_output(value: _HostOutput) -> HostOutput:
    if value.status != 0:
        raise NativeBackendError(f"native lane returned status {value.status}")
    count = int(value.last_hold_reward_count)
    if count != int(value.ticks_advanced) or not 0 <= count <= MAX_HOLD_TICKS:
        raise NativeBackendError("native reward-trace count is inconsistent")
    tail = tuple(float(item) for item in value.last_hold_rewards)
    if any(item != 0.0 for item in tail[count:]):
        raise NativeBackendError("native reward-trace inactive tail is noncanonical")
    return HostOutput(
        advanced=bool(value.advanced), active=bool(value.active), terminal=bool(value.terminal),
        ticks_advanced=int(value.ticks_advanced), tick=int(value.n), hold_k=int(value.hold_k),
        next_k=int(value.next_k), observation=tuple(float(item) for item in value.observation),
        safe_dock=bool(value.safe_dock), timeout=bool(value.timeout),
        cable_overload=bool(value.cable_overload), gantry_contact=bool(value.gantry_contact),
        attitude_loss=bool(value.attitude_loss), formation_loss=bool(value.formation_loss),
        cumulative_reward=float(value.reward_sum), cumulative_energy=float(value.energy_sum),
        energy_ticks=int(value.energy_ticks), dock_tick=None if value.dock_tick < 0 else int(value.dock_tick),
        last_hold_rewards=tail[:count],
    )


def _state_bytes(value: _NativeState) -> bytes:
    return ctypes.string_at(ctypes.addressof(value), ctypes.sizeof(value))


def _state_from_bytes(payload: bytes) -> _NativeState:
    if not isinstance(payload, bytes):
        raise TypeError("native state payload must be bytes")
    if len(payload) != ctypes.sizeof(_NativeState):
        raise ValueError("native state payload has the wrong direct-byte length")
    return _NativeState.from_buffer_copy(payload)


def _typed_state(value: _NativeState) -> NativeState:
    if value.event_phase == 0 and value.event_order == 0:
        phase, order = "PRE_EVENT", None
    elif value.event_phase == 1 and value.event_order == _ORDER_HR:
        phase, order = "POST_EVENT", "HR"
    elif value.event_phase == 1 and value.event_order == _ORDER_RH:
        phase, order = "POST_EVENT", "RH"
    else:
        raise NativeBackendError("native event phase/order is invalid")
    return NativeState(
        state_bytes=_state_bytes(value),
        output=_host_output(value.cached),
        event_phase=phase,
        event_order=order,
        latent_assignment=tuple(int(item) for item in value.p),
        latent_q=int(value.q),
    )


def _step_input(action: int, row: DisturbanceHold, active: bool) -> _StepInput:
    row.validate()
    return _StepInput(
        int(active), int(action),
        (ctypes.c_double * MAX_HOLD_TICKS)(*row.eta_v),
        (ctypes.c_double * MAX_HOLD_TICKS)(*row.eta_y),
        (ctypes.c_double * MAX_HOLD_TICKS)(*row.eta_omega),
    )


def verify_native_transition(
    *,
    pre_state_bytes: bytes,
    action: int,
    active: bool,
    disturbance_hold: DisturbanceHold,
    expected_post_state_bytes: bytes,
) -> dict[str, object]:
    """Purely measure one ABI3 transition without mutating the source POD.

    This technical verifier allocates only local ctypes POD copies.  It does not
    construct ``NativeSession``, address a tape, create RNG state, or publish a
    scientific artifact.
    """

    if not isinstance(active, bool):
        raise TypeError("native transition active flag must be bool")
    validate_actions((action,), 1)
    source = _state_from_bytes(pre_state_bytes)
    expected = _state_from_bytes(expected_post_state_bytes)
    step = _step_input(action, disturbance_hold, active)
    measured = _NativeState()
    output = _HostOutput()
    source_before = _state_bytes(source)
    abi = native_abi_identity()  # Revalidates cache key, receipt, and DLL bytes.
    status = int(require_native_backend().mf_rs_verify_transition(
        ctypes.byref(source), ctypes.byref(step), ctypes.byref(expected),
        ctypes.byref(measured), ctypes.byref(output),
    ))
    if _state_bytes(source) != source_before:
        raise NativeBackendError("native transition verifier mutated its source POD")
    if status not in (0, 4):
        raise NativeBackendError(f"native transition verifier rejected input with status {status}")
    measured_bytes = _state_bytes(measured)
    measured_output = _host_output(output)
    return {
        "schema": "SCDMP_MF_RS_NATIVE_TRANSITION_VERIFICATION_V1",
        "matched": status == 0,
        "native_status": status,
        "abi_version": int(abi["abi_version"]),
        "build_cache_key_sha256": str(abi["build_binding"]["cache_key_sha256"]),
        "action": action,
        "active": active,
        "disturbance_hold_sha256": _sha256_bytes(struct.pack(
            "<39d", *(disturbance_hold.eta_v + disturbance_hold.eta_y + disturbance_hold.eta_omega),
        )),
        "pre_state_sha256": _sha256_bytes(source_before),
        "expected_post_state_sha256": _sha256_bytes(expected_post_state_bytes),
        "measured_post_state_sha256": _sha256_bytes(measured_bytes),
        "measured_tick": measured_output.tick,
        "measured_terminal": measured_output.terminal,
        "measured_ticks_advanced": measured_output.ticks_advanced,
    }


class NativeSession:
    """Fixed-width complete-state native session with direct clone/restore."""

    def __init__(self, states: ctypes.Array[_NativeState], outputs: tuple[HostOutput, ...]) -> None:
        self._states = states
        self._width = len(states)
        self._outputs = outputs

    @classmethod
    def reset(
        cls, *, width: int, k: int, pre_event_q: int, initial_v: float = 0.015,
        initial_y: float = 0.0, initial_phi: float = 0.0,
    ) -> "NativeSession":
        if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= MAX_BATCH_WIDTH:
            raise ValueError(f"native batch width must be in [1, {MAX_BATCH_WIDTH}]")
        if isinstance(k, bool) or k not in ALLOWED_K:
            raise ValueError("k must be 7 or 13")
        if isinstance(pre_event_q, bool) or pre_event_q not in (0, 1):
            raise ValueError("pre_event_q must be the frozen cell bit")
        inputs = (_ResetInput * width)(*(
            _ResetInput(_MAGIC, _ABI_VERSION, k, 1, pre_event_q, initial_v, initial_y, initial_phi)
            for _ in range(width)
        ))
        states = (_NativeState * width)()
        raw_outputs = (_HostOutput * width)()
        status = int(require_native_backend().mf_rs_reset_batch(inputs, width, states, raw_outputs))
        if status != 0:
            raise NativeBackendError(f"native reset rejected batch with status {status}")
        return cls(states, tuple(_host_output(item) for item in raw_outputs))

    @classmethod
    def from_states(cls, states: Iterable[NativeState]) -> "NativeSession":
        materialized = tuple(states)
        if not materialized:
            raise ValueError("native state batch must be nonempty")
        return cls.from_state_bytes(tuple(item.state_bytes for item in materialized))

    @classmethod
    def from_state_bytes(cls, payloads: Iterable[bytes]) -> "NativeSession":
        materialized = tuple(payloads)
        if not 1 <= len(materialized) <= MAX_BATCH_WIDTH:
            raise ValueError(f"native batch width must be in [1, {MAX_BATCH_WIDTH}]")
        states = (_NativeState * len(materialized))(*(_state_from_bytes(item) for item in materialized))
        status = int(require_native_backend().mf_rs_validate_state_batch(states, len(materialized)))
        if status != 0:
            raise NativeBackendError(f"native state validation failed with status {status}")
        outputs = tuple(_host_output(item.cached) for item in states)
        return cls(states, outputs)

    @property
    def width(self) -> int:
        return self._width

    @property
    def outputs(self) -> tuple[HostOutput, ...]:
        return self._outputs

    def state_bytes(self) -> tuple[bytes, ...]:
        return tuple(_state_bytes(item) for item in self._states)

    def states(self) -> tuple[NativeState, ...]:
        return tuple(_typed_state(item) for item in self._states)

    def latent_assignments(self) -> tuple[tuple[int, int, int, int], ...]:
        return tuple(tuple(int(value) for value in item.p) for item in self._states)

    def step(
        self,
        actions: Iterable[int],
        rows: Iterable[DisturbanceHold],
        *,
        active: Iterable[bool] | None = None,
    ) -> tuple[HostOutput, ...]:
        materialized_actions = tuple(actions)
        materialized_rows = tuple(rows)
        active_rows = (True,) * self._width if active is None else tuple(active)
        if len(materialized_rows) != self._width or len(active_rows) != self._width:
            raise ValueError("native step must preserve width and lane positions")
        validate_actions(materialized_actions, self._width)
        inputs = (_StepInput * self._width)(*(
            _step_input(action, row, bool(enabled))
            for action, row, enabled in zip(materialized_actions, materialized_rows, active_rows, strict=True)
        ))
        raw_outputs = (_HostOutput * self._width)()
        status = int(require_native_backend().mf_rs_step_batch(
            self._states, inputs, self._width, raw_outputs
        ))
        if status != 0:
            raise NativeBackendError(f"native step rejected batch with status {status}")
        self._outputs = tuple(_host_output(item) for item in raw_outputs)
        return self._outputs

    def apply_orders(self, orders: Iterable[str]) -> tuple[HostOutput, ...]:
        materialized = tuple(orders)
        if len(materialized) != self._width:
            raise ValueError("order batch must preserve width and lane positions")
        try:
            codes = (ctypes.c_int32 * self._width)(*(
                _ORDER_HR if item == "HR" else _ORDER_RH if item == "RH" else (_raise_order())
                for item in materialized
            ))
        except TypeError:
            raise ValueError("order must be HR or RH") from None
        raw_outputs = (_HostOutput * self._width)()
        status = int(require_native_backend().mf_rs_apply_order_batch(
            self._states, codes, self._width, raw_outputs
        ))
        if status != 0:
            raise NativeBackendError(f"native event/sentinel application failed with status {status}")
        self._outputs = tuple(_host_output(item) for item in raw_outputs)
        return self._outputs


def _raise_order() -> int:
    raise TypeError("invalid order")


def _public_bytes(output: HostOutput) -> bytes:
    return struct.pack("<18d", *output.observation)


def _tape_sha256(rows: tuple[DisturbanceHold, ...]) -> str:
    direct = b"".join(
        struct.pack("<39d", *(row.eta_v + row.eta_y + row.eta_omega)) for row in rows
    )
    return hashlib.sha256(direct).hexdigest()


def _persistent_bytes(payload: bytes) -> bytes:
    state = _state_from_bytes(payload)
    state.event_phase = 0
    state.event_order = 0
    for index, value in enumerate((1, 2, 3, 4)):
        state.p[index] = value
    state.q = 0
    ctypes.memset(ctypes.byref(state.cached), 0, ctypes.sizeof(state.cached))
    return _state_bytes(state)


def persistent_normalized_bytes(payload: bytes) -> bytes:
    """Normalize only registered event/latent/cache fields for twin equality."""

    return _persistent_bytes(payload)


def disturbance_tape_sha256(rows: tuple[DisturbanceHold, ...]) -> str:
    return _tape_sha256(rows)


def construct_reachable_twins(
    *,
    run_manifest: RunManifest,
    state_spec: StateSpec,
    prefix_policy: BatchedPolicy,
) -> ReachableTwins:
    """Select the first legal source boundary under the sealed p/q law."""

    if state_spec not in STATE_SPECS:
        raise ValueError("state_spec must be one row of the six-state checkerboard")
    if not isinstance(run_manifest, RunManifest):
        raise TypeError("reachable-state construction requires the sealed run manifest")
    run_manifest.validate()
    if getattr(prefix_policy, "foundation_seed", None) != state_spec.source_seed:
        raise ValueError("prefix policy is not bound to the checkerboard source foundation")
    state_id = state_spec.cell
    k = state_spec.k
    target_tick = state_spec.target_tick
    source_seed = state_spec.source_seed
    pre_event_q = run_manifest.q_by_cell[STATE_SPECS.index(state_spec)]
    selected = None
    receipts = []
    witnesses = []
    total_transitions = 0
    total_policy_queries = 0
    for tape_index in range(8):
        address = source_tape_address(state_spec, tape_index)
        tape = materialize_disturbance_tape(address)
        initial_v, initial_y, initial_phi = source_reset_values(address)
        common = NativeSession.reset(
            width=1, k=k, pre_event_q=pre_event_q,
            initial_v=initial_v, initial_y=initial_y, initial_phi=initial_phi,
        )
        reset_state_bytes = common.state_bytes()[0]
        renewal_witnesses = []
        transitions = 0
        policy_queries = 0
        renewal_steps = 0
        eligible = False
        terminal = False
        for renewal_index, row in enumerate(tape):
            pre_state_bytes = common.state_bytes()[0]
            observations = (common.outputs[0].observation,)
            actions = tuple(prefix_policy(observations))
            validate_actions(actions, 1)
            policy_queries += 1
            renewal_steps += 1
            output = common.step(actions, (row,))[0]
            renewal_witnesses.append(SourceRenewalWitness(
                tape_index, renewal_index, struct.pack("<18d", *observations[0]),
                actions[0], pre_state_bytes, common.state_bytes()[0],
            ))
            transitions += output.ticks_advanced
            if output.terminal:
                terminal = True
                break
            if output.tick >= target_tick and output.tick + k <= HORIZON_TICKS:
                eligible = True
                selected = (
                    tape_index, address, tape, common, output, renewal_index,
                )
                break
        total_transitions += transitions
        total_policy_queries += policy_queries
        receipt = SourceScanReceipt(
            tape_index, eligible, renewal_steps, transitions, policy_queries, terminal,
        )
        receipts.append(receipt)
        witnesses.append(SourceCandidateWitness(
            tape_index, address, (initial_v, initial_y, initial_phi), _tape_sha256(tape),
            reset_state_bytes, tuple(renewal_witnesses), receipt,
        ))
        if selected is not None:
            break
    if selected is None:
        raise ReachableStatePanelNotEstablished(tuple(receipts), tuple(witnesses))
    (
        selected_tape_index, address, tape, common, output, renewal_index,
    ) = selected

    source_snapshot = common.state_bytes()[0]
    source_state = common.states()[0]
    if source_state.latent_assignment != (1, 2, 3, 4) or source_state.latent_q != pre_event_q:
        raise NativeBackendError("source p/q differs from the sealed pre-event law")
    twins_session = NativeSession.from_state_bytes((source_snapshot, source_snapshot))
    twins_session.apply_orders(("HR", "RH"))
    hr, rh = twins_session.states()
    hr_public = _public_bytes(hr.output)
    rh_public = _public_bytes(rh.output)
    if hr_public != rh_public:
        raise NativeBackendError("HR/RH actor-visible public observations are not direct-byte equal")
    if hr.latent_assignment != HR_ASSIGNMENT or rh.latent_assignment != RH_ASSIGNMENT:
        raise NativeBackendError("native event composition returned an unexpected latent assignment")
    if hr.latent_assignment == rh.latent_assignment:
        raise NativeBackendError("native twin assignments did not differ")
    if hr.latent_q != 1 or rh.latent_q != 0:
        raise NativeBackendError("native twin q overwrite differs")
    persistent_equal = (
        _persistent_bytes(source_snapshot) == _persistent_bytes(hr.state_bytes)
        == _persistent_bytes(rh.state_bytes)
    )
    if not persistent_equal:
        raise NativeBackendError("LEVEL_RELEASE changed persistent source/twin state")
    source_address = address
    return ReachableTwins(
        state_id=state_id, k=k, target_tick=target_tick, boundary_tick=output.tick,
        source_seed=source_seed, source_address=source_address, source_tape=tape,
        pre_event_p=source_state.latent_assignment, pre_event_q=pre_event_q,
        source_snapshot_bytes=source_snapshot,
        hr=hr, rh=rh, hr_public_bytes=hr_public, rh_public_bytes=rh_public,
        hr_assignment=hr.latent_assignment, rh_assignment=rh.latent_assignment,
        eligible=True, selected_tape_index=selected_tape_index,
        source_renewal_index=renewal_index, source_scan_receipts=tuple(receipts),
        persistent_twin_bytes_equal=persistent_equal,
        transitions=total_transitions, policy_queries=total_policy_queries,
        source_candidate_witnesses=tuple(witnesses),
    )


def evaluate_twin_branches(
    twins: ReachableTwins,
    *,
    forced_actions: tuple[int, int],
    evaluation_address: object,
    foundation_policy: BatchedPolicy,
) -> BranchEvaluation:
    """Execute one forced hold per twin, then one immutable batched policy."""

    if not isinstance(twins, ReachableTwins) or not twins.eligible:
        raise TypeError("branch evaluation requires eligible ReachableTwins")
    validate_actions(forced_actions, 2)
    if isinstance(evaluation_address, TapeAddress):
        if evaluation_address.namespace is TapeNamespace.HELDOUT:
            raise ValueError("held-out permit is required before evaluation")
        address = evaluation_address
    else:
        from .artifacts import validate_heldout_permit
        permit_state_id, address, tape = validate_heldout_permit(evaluation_address)
        if permit_state_id != twins.state_id:
            raise ValueError("held-out permit state differs from the reachable twins")
    if address.namespace is TapeNamespace.SOURCE:
        raise ValueError("branch evaluation rejects the SOURCE tape namespace")
    if isinstance(evaluation_address, TapeAddress):
        canonical = {
            development_tape_address(twins.state_id, tape) for tape in range(8)
        }
        if address not in canonical:
            raise ValueError("development tape address is outside the canonical eight blocks")
        tape = materialize_disturbance_tape(address)
    if address == twins.source_address:
        raise ValueError("branch evaluation tape address overlaps the source rollout")
    if getattr(foundation_policy, "foundation_seed", None) not in TRAINING_SEEDS:
        raise ValueError("evaluation policy is not bound to a prescribed foundation")
    session = NativeSession.from_states((twins.hr, twins.rh))
    # Evaluation is a fresh addressed stream from the frozen twin, not a
    # continuation of the SOURCE prefix stream.
    tape_index = 0
    if tape_index >= len(tape):
        raise RuntimeError("evaluation tape exhausted before forced twin hold")
    outputs = session.step(forced_actions, (tape[tape_index], tape[tape_index]))
    transitions_by_lane = [item.ticks_advanced for item in outputs]
    transitions = sum(transitions_by_lane)
    renewal_steps = 1
    policy_queries = 0
    policy_queries_by_lane = [0, 0]
    policy_batch_calls = 0
    tape_index += 1

    while any(not item.terminal for item in outputs):
        if tape_index >= len(tape):
            raise RuntimeError("evaluation tape exhausted before full-mission termination")
        active_indices = tuple(index for index, item in enumerate(outputs) if not item.terminal)
        visible = tuple(outputs[index].observation for index in active_indices)
        selected = tuple(foundation_policy(visible))
        validate_actions(selected, len(active_indices))
        policy_queries += len(active_indices)
        for index in active_indices:
            policy_queries_by_lane[index] += 1
        policy_batch_calls += 1
        actions = [0, 0]
        for index, action in zip(active_indices, selected, strict=True):
            actions[index] = action
        active = tuple(index in active_indices for index in range(2))
        outputs = session.step(tuple(actions), (tape[tape_index], tape[tape_index]), active=active)
        transitions += sum(outputs[index].ticks_advanced for index in active_indices)
        for index in active_indices:
            transitions_by_lane[index] += outputs[index].ticks_advanced
        renewal_steps += 1
        tape_index += 1

    failure = sum(item.failure for item in outputs)
    counts = {
        "total": 2,
        "safe_dock": sum(item.safe_dock for item in outputs),
        "failure": failure,
        "timeout": sum(item.timeout for item in outputs),
        "cable_overload": sum(item.cable_overload for item in outputs),
        "gantry_contact": sum(item.gantry_contact for item in outputs),
        "attitude_loss": sum(item.attitude_loss for item in outputs),
        "formation_loss": sum(item.formation_loss for item in outputs),
    }
    return BranchEvaluation(
        outputs=outputs,
        raw_returns=tuple(item.cumulative_reward for item in outputs),
        costs=tuple(item.cumulative_energy for item in outputs),
        terminal_counts=counts,
        width=2,
        forced_holds=2,
        policy_queries=policy_queries,
        policy_batch_calls=policy_batch_calls,
        renewal_steps=renewal_steps,
        transitions=transitions,
        policy_queries_by_lane=tuple(policy_queries_by_lane),
        transitions_by_lane=tuple(transitions_by_lane),
    )


__all__ = [
    "NativeBackendError", "NativeSession", "ReachableStatePanelNotEstablished", "construct_reachable_twins",
    "disturbance_tape_sha256", "evaluate_twin_branches", "native_abi_identity",
    "persistent_normalized_bytes", "require_native_backend", "verify_native_transition",
]

"""Source-keyed C++20 batched interactive host for DISH RBHR r05.

Only the explicit TEST/nonproduction constructor is available in this module.
The future activity entry point fails closed until a separate Root lease object
is supplied by the operational lifecycle.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Mapping

import numpy as np

from .contracts import fixture_family
from .native_backend import _toolchain, _vs_installation, artifact_identity as gate_artifact_identity
from .production_contract import (
    COMPONENT,
    PREACTIVITY_NAMESPACE,
    PreactivityAuthority,
    ProductionContractError,
    refuse_without_root_lease,
)


ABI_VERSION = 4
TEST_MASTER = hashlib.sha256(b"TEST/DISH-RBHR-R05/PRODUCTION-PREACTIVITY/RNG/V1").digest()
_SOURCE = Path(__file__).with_name("native") / "rbhr_production_backend.cpp"
_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/fp:strict", "/W4")


class ProductionBackendError(RuntimeError):
    pass


class _ResetInput(ctypes.Structure):
    _fields_ = [("fixture_key", ctypes.c_uint64), ("master", ctypes.c_uint8 * 32)] + [
        (name, ctypes.c_int32)
        for name in (
            "test_mode", "package", "reflection", "initial_owner", "qa_owner", "k_initial",
            "k_new", "switch_tick", "tau_d_tick", "phase", "route_speed",
            "turn_magnitude_deg", "turn_sign", "initial_ux", "initial_uy",
            "block", "split", "schedule", "accepted_slot", "candidate_attempt", "lane", "cycle",
            "arm_substream", "degradation_flag", "fork_branch", "episode",
        )
    ]


class _StepInput(ctypes.Structure):
    _fields_ = [
        ("raw_action", ctypes.c_double * 4),
        ("prediction_mean", ctypes.c_double * 8),
        ("prediction_covariance", ctypes.c_double * 32),
        ("service_q", ctypes.c_double * 20),
        ("controller_hidden", ctypes.c_double * 512),
        ("prepare", ctypes.c_int32 * 2),
        ("commit", ctypes.c_int32 * 2),
        ("promotion_alpha", ctypes.c_double),
    ]


class _State(ctypes.Structure):
    _fields_ = [
        *[(name, ctypes.c_int32) for name in (
            "initialized", "terminal", "tick", "package", "reflection", "initial_owner", "owner",
            "service_epoch", "next_payload_sequence", "handover_used", "k_active", "k_new", "k_epoch",
            "countdown", "pending_switch", "switch_tick", "tau_d_tick", "route_speed", "turn_magnitude_deg",
            "turn_sign", "prepare_latched", "warmup", "pending_intent", "intent_owner", "intent_epoch",
            "intent_next_sequence", "intent_k_epoch", "intent_certificate", "intent_origin_tick",
        )],
        ("source_exists", ctypes.c_int32 * 2), ("source_sequence", ctypes.c_int32 * 2),
        ("source_tick", ctypes.c_int32 * 2),
        *[(name, ctypes.c_int32) for name in (
            "pending_source_exists", "pending_source_sequence", "pending_source_tick", "base_exists",
            "base_source_sequence", "base_source_tick", "base_relay_tick", "pending_relay_exists",
            "pending_relay_source_sequence", "pending_relay_source_tick", "pending_relay_tick",
            "pending_relay_epoch", "pending_relay_sequence", "pending_relay_sender",
        )],
        ("partner_present", ctypes.c_int32 * 2), ("partner_tick", ctypes.c_int32 * 2),
        *[(name, ctypes.c_int32) for name in (
            "invalid_commit", "token_gap", "dual_owner", "dual_payload", "buffer_clear",
            "command_slew_breach", "separation_breach", "service_ticks",
        )],
        ("master", ctypes.c_uint8 * 32),
        *[(name, ctypes.c_int32) for name in (
            "block", "split", "schedule", "accepted_slot", "candidate_attempt", "lane", "cycle",
            "arm_substream", "degradation_flag", "fork_branch", "episode",
        )],
        ("protocol_bytes", ctypes.c_uint64),
        ("p", ctypes.c_double * 4), ("v", ctypes.c_double * 4),
        ("a", ctypes.c_double * 4), ("battery", ctypes.c_double * 2),
        ("wind", ctypes.c_double * 2), ("filter_mean", ctypes.c_double * 8),
        ("filter_covariance", ctypes.c_double * 32), ("source_z", ctypes.c_double * 8),
        ("source_first_margin", ctypes.c_double * 2), ("pending_source_z", ctypes.c_double * 4),
        ("pending_source_margin", ctypes.c_double * 2), ("base_z", ctypes.c_double * 4),
        ("base_first_margin", ctypes.c_double), ("base_second_margin", ctypes.c_double),
        ("pending_relay_z", ctypes.c_double * 4), ("pending_relay_first_margin", ctypes.c_double),
        ("pending_relay_second_margin", ctypes.c_double), ("last_radio_margin", ctypes.c_double * 6),
        ("controller_hidden", ctypes.c_double * 512),
        ("min_separation", ctypes.c_double), ("total_energy", ctypes.c_double),
        ("test_mode", ctypes.c_int32), ("lineage_lock", ctypes.c_int32 * 2),
        ("lineage_sequence", ctypes.c_int32 * 2),
        ("pending_snapshot", ctypes.c_int32), ("pending_snapshot_sender", ctypes.c_int32),
        ("pending_snapshot_sequence", ctypes.c_int32), ("pending_snapshot_tick", ctypes.c_int32),
        ("snapshot_accepted", ctypes.c_int32), ("snapshot_tick", ctypes.c_int32),
        ("readiness_accepted", ctypes.c_int32), ("readiness_tick", ctypes.c_int32),
        ("readiness_snapshot_tick", ctypes.c_int32), ("application_reason", ctypes.c_int32),
        ("cas_applied", ctypes.c_int32), ("actuator_owner", ctypes.c_int32),
        ("protocol_wire_hash", ctypes.c_uint64), ("protocol_wire_messages", ctypes.c_uint64),
        ("pending_readiness", ctypes.c_int32), ("pending_readiness_tick", ctypes.c_int32),
        ("intent_readiness_tick", ctypes.c_int32), ("intent_snapshot_tick", ctypes.c_int32),
        ("pending_snapshot_margin", ctypes.c_double), ("pending_readiness_margin", ctypes.c_double),
        ("pending_intent_margin", ctypes.c_double), ("intent_alpha", ctypes.c_double),
        ("pending_snapshot_payload", ctypes.c_double * 18),
        ("accepted_snapshot_payload", ctypes.c_double * 18),
        ("pending_readiness_candidate", ctypes.c_double * 2),
        ("accepted_readiness_candidate", ctypes.c_double * 2),
    ]


class _StepOutput(ctypes.Structure):
    _fields_ = [
        ("actor", ctypes.c_double * 216), ("critic", ctypes.c_double * 58),
        ("service", ctypes.c_int32), ("renew", ctypes.c_int32),
        ("terminal", ctypes.c_int32), ("owner", ctypes.c_int32),
        ("service_epoch", ctypes.c_int32), ("next_payload_sequence", ctypes.c_int32),
        ("handover_used", ctypes.c_int32), ("invalid_commit", ctypes.c_int32),
        ("token_gap", ctypes.c_int32), ("dual_owner", ctypes.c_int32),
        ("dual_payload", ctypes.c_int32), ("buffer_clear", ctypes.c_int32),
        ("command_slew_breach", ctypes.c_int32), ("separation_breach", ctypes.c_int32),
        ("tick", ctypes.c_int32), ("protocol_bytes", ctypes.c_uint64),
        ("min_separation", ctypes.c_double), ("total_energy", ctypes.c_double),
        ("snapshot_accepted", ctypes.c_int32), ("readiness_accepted", ctypes.c_int32),
        ("application_reason", ctypes.c_int32), ("cas_applied", ctypes.c_int32),
        ("actuator_owner", ctypes.c_int32),
        ("protocol_wire_hash", ctypes.c_uint64), ("protocol_wire_messages", ctypes.c_uint64),
        ("snapshot_payload", ctypes.c_double * 18),
        ("readiness_candidate", ctypes.c_double * 2),
        ("snapshot_delivery_mask", ctypes.c_int32),
        ("readiness_delivery_mask", ctypes.c_int32), ("version_match", ctypes.c_int32),
    ]


class _ForkOutput(ctypes.Structure):
    _fields_ = [
        ("real_state", _State), ("sham_state", _State),
        ("real_telemetry_sha256", ctypes.c_uint8 * 32),
        ("sham_telemetry_sha256", ctypes.c_uint8 * 32),
        ("byte_identical_telemetry", ctypes.c_int32),
    ]


class _ScriptOutput(ctypes.Structure):
    _fields_ = [("raw_action", ctypes.c_double * 4), ("transfer", ctypes.c_int32), ("score", ctypes.c_double)]


class _QualificationOutput(ctypes.Structure):
    _fields_ = [
        ("eligible", ctypes.c_int32), ("origin_tick", ctypes.c_int32),
        ("stratum", ctypes.c_int32), ("real_service_ticks", ctypes.c_int32),
        ("retain_service_ticks", ctypes.c_int32),
        ("opportunities_checked", ctypes.c_int32), ("rejection_mask", ctypes.c_int32),
        ("advantage", ctypes.c_double),
    ]


class _ProtocolAuditOutput(ctypes.Structure):
    _fields_ = [
        ("message_count", ctypes.c_int32), ("all_integrity_verified", ctypes.c_int32),
        ("all_tamper_rejected", ctypes.c_int32), ("sizes", ctypes.c_uint32 * 8),
        ("aggregate_sha256", ctypes.c_uint8 * 32),
    ]


class _ProtocolTransitionOutput(ctypes.Structure):
    _fields_ = [
        ("source_lineage_preserved", ctypes.c_int32), ("locks_released", ctypes.c_int32),
        ("cas_applied", ctypes.c_int32), ("application_reason", ctypes.c_int32),
        ("owner_before", ctypes.c_int32), ("owner_after", ctypes.c_int32),
        ("service_epoch_after", ctypes.c_int32), ("actuator_owner_after", ctypes.c_int32),
        ("recurrent_promotion_verified", ctypes.c_int32),
        ("protocol_wire_hash", ctypes.c_uint64), ("protocol_wire_messages", ctypes.c_uint64),
    ]


_LOCK = threading.RLock()
_LOADED: dict[str, ctypes.CDLL] = {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha256() -> str:
    return _sha256(_SOURCE)


def _build_material() -> tuple[str, bytes]:
    source = _SOURCE.read_bytes()
    toolchain = _toolchain()
    digest = hashlib.sha256()
    digest.update(b"DISH-RBHR-R05-PRODUCTION-HOST-v1\0")
    digest.update(hashlib.sha256(source).digest())
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    digest.update(ABI_VERSION.to_bytes(4, "big"))
    for flag in _FLAGS:
        digest.update(flag.encode("ascii") + b"\0")
    return digest.hexdigest(), source


def _artifact_path(key: str) -> Path:
    return Path(tempfile.gettempdir()) / "hmasd_dish_rbhr_r05_production" / key / "rbhr_production_backend.dll"


def _compile(key: str, source: bytes) -> Path:
    target = _artifact_path(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot = target.parent / "rbhr_production_backend.source.cpp"
    if snapshot.is_file() and snapshot.read_bytes() != source:
        raise ProductionBackendError("source-key snapshot differs")
    if not snapshot.is_file():
        temporary = snapshot.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
        with temporary.open("wb") as stream:
            stream.write(source); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, snapshot)
    if target.is_file():
        return target
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    obj = target.parent / f"rbhr_production_backend.{suffix}.obj"
    candidate = target.parent / f"rbhr_production_backend.{suffix}.dll"
    command = f'call "{vcvars}" >nul && cl {" ".join(_FLAGS)} "{snapshot}" /Fo:"{obj}" /link /OUT:"{candidate}"'
    result = subprocess.run(command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"), cwd=target.parent, capture_output=True, text=True)
    if result.returncode != 0 or not candidate.is_file():
        raise ProductionBackendError(f"native compilation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    try:
        os.replace(candidate, target)
    except OSError:
        if not target.is_file():
            raise
        candidate.unlink(missing_ok=True)
    finally:
        obj.unlink(missing_ok=True)
    return target


def _configure(lib: ctypes.CDLL) -> ctypes.CDLL:
    lib.dish_rbhr_prod_abi_version.argtypes = []; lib.dish_rbhr_prod_abi_version.restype = ctypes.c_int32
    size_names = (
        "reset_input", "step_input", "state", "step_output", "fork_output", "script_output",
        "qualification_output",
        "protocol_audit_output",
        "protocol_transition_output",
    )
    observed = [lib.dish_rbhr_prod_abi_version()]
    for name in size_names:
        function = getattr(lib, f"dish_rbhr_prod_{name}_size")
        function.argtypes = []; function.restype = ctypes.c_uint64; observed.append(function())
    expected = [ABI_VERSION, *map(ctypes.sizeof, (
        _ResetInput, _StepInput, _State, _StepOutput, _ForkOutput, _ScriptOutput,
        _QualificationOutput,
        _ProtocolAuditOutput,
        _ProtocolTransitionOutput,
    ))]
    if observed != expected:
        raise ProductionBackendError(f"production ABI differs: observed={observed}, expected={expected}")
    lib.dish_rbhr_prod_reset_batch.argtypes = [ctypes.POINTER(_ResetInput), ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_prod_step_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_prod_rollout_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_prod_clone_real_sham_batch.argtypes = [ctypes.POINTER(_State), ctypes.c_uint64, ctypes.POINTER(_ForkOutput)]
    lib.dish_rbhr_prod_script_batch.argtypes = [ctypes.POINTER(_State), ctypes.c_uint64, ctypes.POINTER(_ScriptOutput)]
    lib.dish_rbhr_prod_scan_candidate_batch.argtypes = [
        ctypes.POINTER(_ResetInput), ctypes.c_uint64, ctypes.POINTER(_QualificationOutput),
    ]
    lib.dish_rbhr_prod_protocol_audit.argtypes = [ctypes.POINTER(_ProtocolAuditOutput)]
    lib.dish_rbhr_prod_protocol_audit.restype = ctypes.c_int32
    lib.dish_rbhr_prod_protocol_transition_probe.argtypes = [ctypes.POINTER(_ProtocolTransitionOutput)]
    lib.dish_rbhr_prod_protocol_transition_probe.restype = ctypes.c_int32
    lib.dish_rbhr_prod_rng_words_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
    ]
    for name in (
        "reset_batch", "step_batch", "rollout_batch", "clone_real_sham_batch",
        "script_batch", "scan_candidate_batch", "rng_words_batch",
    ):
        getattr(lib, f"dish_rbhr_prod_{name}").restype = ctypes.c_int32
    return lib


def require_cpp_batched_production_backend() -> ctypes.CDLL:
    key, source = _build_material()
    with _LOCK:
        if key not in _LOADED:
            _LOADED[key] = _configure(ctypes.CDLL(str(_compile(key, source))))
        return _LOADED[key]


def artifact_identity() -> dict[str, object]:
    key, source = _build_material(); path = _artifact_path(key); existed = path.is_file(); started = time.perf_counter(); lib = require_cpp_batched_production_backend()
    gate = gate_artifact_identity()
    return {
        "component": COMPONENT,
        "artifact": str(path),
        "artifact_sha256": _sha256(path),
        "artifact_bytes": path.stat().st_size,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "build_key": key,
        "load_seconds": time.perf_counter() - started,
        "cache_present_before": existed,
        "abi_version": lib.dish_rbhr_prod_abi_version(),
        "abi_sizes": {
            "reset_input": ctypes.sizeof(_ResetInput), "step_input": ctypes.sizeof(_StepInput),
            "state": ctypes.sizeof(_State), "step_output": ctypes.sizeof(_StepOutput),
            "fork_output": ctypes.sizeof(_ForkOutput), "script_output": ctypes.sizeof(_ScriptOutput),
            "qualification_output": ctypes.sizeof(_QualificationOutput),
            "protocol_audit_output": ctypes.sizeof(_ProtocolAuditOutput),
            "protocol_transition_output": ctypes.sizeof(_ProtocolTransitionOutput),
        },
        "accepted_native_rng_generator_service": gate,
        "full_reset_step_cpp": True,
        "python_environment_fallback": False,
    }


class NativeBatch:
    """Persistent native state with NumPy-backed batch inputs and no scalar loop."""

    def __init__(self, resets: tuple[_ResetInput, ...]) -> None:
        width = len(resets)
        if width <= 0:
            raise ProductionBackendError("width must be positive")
        self.width = width
        self._states = (_State * width)()
        self._outputs = (_StepOutput * width)()
        reset_array = (_ResetInput * width)()
        for index, reset in enumerate(resets):
            reset_array[index] = reset
        code = require_cpp_batched_production_backend().dish_rbhr_prod_reset_batch(reset_array, width, self._states, self._outputs)
        if code:
            raise ProductionBackendError(f"native reset rejected batch ({code})")

    @classmethod
    def test_only(cls, width: int, authority: PreactivityAuthority) -> "NativeBatch":
        authority.require_test_only()
        return cls(_test_reset_inputs(width))

    def step(self, rows: np.ndarray) -> Mapping[str, np.ndarray]:
        expected = np.dtype(_StepInput)
        values = np.ascontiguousarray(rows, dtype=expected)
        if values.shape != (self.width,):
            raise ProductionBackendError("step rows must be one structured row per lane")
        pointer = values.ctypes.data_as(ctypes.POINTER(_StepInput))
        code = require_cpp_batched_production_backend().dish_rbhr_prod_step_batch(self._states, pointer, self.width, self._outputs)
        if code:
            raise ProductionBackendError(f"native step rejected batch ({code})")
        raw = np.frombuffer(self._outputs, dtype=np.dtype(_StepOutput), count=self.width)
        return {
            "actor": raw["actor"].reshape(self.width, 4, 54).copy(),
            "critic": raw["critic"].reshape(self.width, 58).copy(),
            "service": raw["service"].copy(),
            "renew": raw["renew"].copy(),
            "terminal": raw["terminal"].copy(),
            "owner": raw["owner"].copy(),
            "tick": raw["tick"].copy(),
            "protocol_bytes": raw["protocol_bytes"].copy(),
            "total_energy": raw["total_energy"].copy(),
            "snapshot_accepted": raw["snapshot_accepted"].copy(),
            "readiness_accepted": raw["readiness_accepted"].copy(),
            "application_reason": raw["application_reason"].copy(),
            "cas_applied": raw["cas_applied"].copy(),
            "actuator_owner": raw["actuator_owner"].copy(),
            "protocol_wire_hash": raw["protocol_wire_hash"].copy(),
            "protocol_wire_messages": raw["protocol_wire_messages"].copy(),
            "snapshot_payload": raw["snapshot_payload"].copy(),
            "readiness_candidate": raw["readiness_candidate"].copy(),
            "snapshot_delivery_mask": raw["snapshot_delivery_mask"].copy(),
            "readiness_delivery_mask": raw["readiness_delivery_mask"].copy(),
            "version_match": raw["version_match"].copy(),
        }

    def rollout(self, rows: np.ndarray) -> Mapping[str, np.ndarray]:
        expected = np.dtype(_StepInput)
        values = np.ascontiguousarray(rows, dtype=expected)
        if values.ndim != 2 or values.shape[1] != self.width:
            raise ProductionBackendError("rollout rows must be [ticks,width]")
        steps = values.shape[0]
        outputs = (_StepOutput * (steps * self.width))()
        pointer = values.ctypes.data_as(ctypes.POINTER(_StepInput))
        code = require_cpp_batched_production_backend().dish_rbhr_prod_rollout_batch(
            self._states, pointer, steps, self.width, outputs
        )
        if code:
            raise ProductionBackendError(f"native rollout rejected batch ({code})")
        raw = np.frombuffer(outputs, dtype=np.dtype(_StepOutput), count=steps * self.width).reshape(steps, self.width)
        return {
            "actor": raw["actor"].reshape(steps, self.width, 4, 54).copy(),
            "critic": raw["critic"].reshape(steps, self.width, 58).copy(),
            "service": raw["service"].copy(),
            "renew": raw["renew"].copy(),
            "terminal": raw["terminal"].copy(),
            "owner": raw["owner"].copy(),
            "service_epoch": raw["service_epoch"].copy(),
            "next_payload_sequence": raw["next_payload_sequence"].copy(),
            "handover_used": raw["handover_used"].copy(),
            "invalid_commit": raw["invalid_commit"].copy(),
            "tick": raw["tick"].copy(),
            "protocol_bytes": raw["protocol_bytes"].copy(),
            "total_energy": raw["total_energy"].copy(),
            "snapshot_accepted": raw["snapshot_accepted"].copy(),
            "readiness_accepted": raw["readiness_accepted"].copy(),
            "application_reason": raw["application_reason"].copy(),
            "cas_applied": raw["cas_applied"].copy(),
            "actuator_owner": raw["actuator_owner"].copy(),
            "protocol_wire_hash": raw["protocol_wire_hash"].copy(),
            "protocol_wire_messages": raw["protocol_wire_messages"].copy(),
            "snapshot_payload": raw["snapshot_payload"].copy(),
            "readiness_candidate": raw["readiness_candidate"].copy(),
            "snapshot_delivery_mask": raw["snapshot_delivery_mask"].copy(),
            "readiness_delivery_mask": raw["readiness_delivery_mask"].copy(),
            "version_match": raw["version_match"].copy(),
        }

    def clone_real_sham(self) -> np.ndarray:
        outputs = (_ForkOutput * self.width)()
        code = require_cpp_batched_production_backend().dish_rbhr_prod_clone_real_sham_batch(self._states, self.width, outputs)
        if code:
            raise ProductionBackendError(f"native fork clone rejected state ({code})")
        return np.frombuffer(outputs, dtype=np.dtype(_ForkOutput), count=self.width).copy()

    def scripted_actions(self) -> np.ndarray:
        outputs = (_ScriptOutput * self.width)()
        code = require_cpp_batched_production_backend().dish_rbhr_prod_script_batch(self._states, self.width, outputs)
        if code:
            raise ProductionBackendError(f"native script rejected state ({code})")
        return np.frombuffer(outputs, dtype=np.dtype(_ScriptOutput), count=self.width).copy()


def empty_step_rows(width: int) -> np.ndarray:
    rows = np.zeros(width, dtype=np.dtype(_StepInput))
    for offset in (0, 5, 10, 15, 16, 21, 26, 31):
        rows["prediction_covariance"][:, offset] = 4.0
    rows["service_q"] = 0.8
    rows["promotion_alpha"] = 1.0
    return rows


def TestNativeBatch(width: int, authority: PreactivityAuthority) -> NativeBatch:
    """Compatibility factory for the exact preactivity-only constructor."""

    return NativeBatch.test_only(width, authority)


def TestProtocolNativeBatch(width: int, authority: PreactivityAuthority) -> NativeBatch:
    """Controlled TEST-only batch that exercises the natural protocol path."""

    authority.require_test_only()
    return NativeBatch(_protocol_test_reset_inputs(width))


def _test_reset_inputs(width: int, *, attempt_offset: int = 0, test_mode: int = 1) -> tuple[_ResetInput, ...]:
    if width <= 0 or attempt_offset < 0 or attempt_offset + width > 100_000:
        raise ProductionBackendError("TEST candidate range is outside the frozen cap")
    resets: list[_ResetInput] = []
    for index, fixture in enumerate(fixture_family(width)):
        attempt = attempt_offset + index
        resets.append(_ResetInput(
            fixture.fixture_key, (ctypes.c_uint8 * 32).from_buffer_copy(TEST_MASTER),
            test_mode, fixture.package, fixture.reflection,
            fixture.initial_owner, (index >> 2) & 1, fixture.k_initial, fixture.k_new,
            fixture.switch_tick, fixture.tau_d_tick, fixture.phase,
            fixture.route_speed, fixture.turn_magnitude_deg, fixture.turn_sign,
            fixture.initial_ux, fixture.initial_uy,
            index % 24, 1, (0, 1, 2, 3, 4)[index % 5], index % 48, attempt,
            index % 32, 0, 0, 0, 0, index,
        ))
    return tuple(resets)


def _protocol_test_reset_inputs(width: int) -> tuple[_ResetInput, ...]:
    if width <= 0:
        raise ProductionBackendError("protocol TEST width must be positive")
    return tuple(
        _ResetInput(
            0xD15A900000000000 + index,
            (ctypes.c_uint8 * 32).from_buffer_copy(TEST_MASTER),
            2, 0, 1, index % 2, (index >> 2) & 1, 4, 4, 500, 0, 0, 4, 25, 1, 40, 120,
            index % 24, 1, 0, index % 48, index, index % 32, 0, 0, 0, 0, index,
        )
        for index in range(width)
    )


def scan_test_candidate_attempts(
    width: int,
    authority: PreactivityAuthority,
    *,
    attempt_offset: int = 0,
    clear_channel_fixture: bool = False,
) -> np.ndarray:
    """Run the native 20-tick-law/50-tick assay on TEST-only candidates.

    This validates the production scanner without creating a scientific master,
    accepted coordinate, or result.  The returned rows contain only TEST assay
    classifications and resource-relevant candidate accounting.
    """

    authority.require_test_only()
    resets = _test_reset_inputs(
        width, attempt_offset=attempt_offset, test_mode=2 if clear_channel_fixture else 1,
    )
    reset_array = (_ResetInput * width)(*resets)
    outputs = (_QualificationOutput * width)()
    code = require_cpp_batched_production_backend().dish_rbhr_prod_scan_candidate_batch(
        reset_array, width, outputs
    )
    if code:
        raise ProductionBackendError(f"native candidate scanner rejected batch ({code})")
    return np.frombuffer(outputs, dtype=np.dtype(_QualificationOutput), count=width).copy()


def scan_production_candidate_attempts(
    rows: tuple[Mapping[str, object], ...], *, authority: object | None,
) -> np.ndarray:
    """Run only the frozen native candidate assay under scanner-only authority."""

    refuse_without_root_lease(authority)
    require_scanner = getattr(authority, "require_scanner_active", None)
    if not callable(require_scanner):
        raise ProductionContractError("Root binding is not scanner-only authority")
    require_scanner()
    if not rows:
        raise ProductionContractError("scanner batch must be nonempty")
    validate_rows = getattr(authority, "validate_scanner_rows", None)
    if not callable(validate_rows):
        raise ProductionContractError("scanner authority lacks row binding")
    validate_rows(rows)
    scalar_names = [name for name, _ in _ResetInput._fields_ if name != "master"]
    resets: list[_ResetInput] = []
    for row in rows:
        try:
            values = [int(row[name]) for name in scalar_names]
            master_value = row["master"]
            master_bytes = bytes.fromhex(master_value) if isinstance(master_value, str) else bytes(master_value)
        except (KeyError, TypeError, ValueError) as error:
            raise ProductionContractError("scanner reset row schema differs") from error
        if len(master_bytes) != 32 or values[1] != 0:
            raise ProductionContractError("scanner reset row is not bound activity mode")
        resets.append(_ResetInput(values[0], (ctypes.c_uint8 * 32).from_buffer_copy(master_bytes), *values[1:]))
    reset_array = (_ResetInput * len(resets))(*resets)
    outputs = (_QualificationOutput * len(resets))()
    code = require_cpp_batched_production_backend().dish_rbhr_prod_scan_candidate_batch(
        reset_array, len(resets), outputs,
    )
    if code:
        raise ProductionBackendError(f"native production candidate scanner rejected batch ({code})")
    return np.frombuffer(outputs, dtype=np.dtype(_QualificationOutput), count=len(resets)).copy()


def native_protocol_audit() -> dict[str, object]:
    output = _ProtocolAuditOutput()
    code = require_cpp_batched_production_backend().dish_rbhr_prod_protocol_audit(ctypes.byref(output))
    if code:
        raise ProductionBackendError(f"native protocol audit failed ({code})")
    return {
        "schema": "DISH_RBHR_R05_NATIVE_PROTOCOL_AUDIT_V1",
        "message_count": int(output.message_count),
        "wire_sizes": list(map(int, output.sizes)),
        "all_integrity_verified": bool(output.all_integrity_verified),
        "all_tamper_rejected": bool(output.all_tamper_rejected),
        "aggregate_sha256": bytes(output.aggregate_sha256).hex(),
        "test_only": True, "question_relevant_output": False,
    }


def native_protocol_transition_probe() -> dict[str, object]:
    output = _ProtocolTransitionOutput()
    code = require_cpp_batched_production_backend().dish_rbhr_prod_protocol_transition_probe(ctypes.byref(output))
    if code:
        raise ProductionBackendError(f"native protocol transition probe failed ({code})")
    return {
        "schema": "DISH_RBHR_R05_NATIVE_PROTOCOL_TRANSITION_PROBE_V1",
        **{name: bool(getattr(output, name)) for name in (
            "source_lineage_preserved", "locks_released", "cas_applied",
            "recurrent_promotion_verified",
        )},
        "application_reason": int(output.application_reason),
        "owner_before": int(output.owner_before), "owner_after": int(output.owner_after),
        "service_epoch_after": int(output.service_epoch_after),
        "actuator_owner_after": int(output.actuator_owner_after),
        "protocol_wire_hash": int(output.protocol_wire_hash),
        "protocol_wire_messages": int(output.protocol_wire_messages),
        "test_only": True, "question_relevant_output": False,
    }


def native_natural_protocol_trace(*, width: int = 8, steps: int = 32) -> dict[str, object]:
    """Run reset-to-CAS through ordinary native delivery/transmission steps."""

    if steps < 16:
        raise ProductionBackendError("natural protocol trace is too short")
    batch = NativeBatch(_protocol_test_reset_inputs(width))
    rows = np.repeat(empty_step_rows(width)[None, :], steps, axis=0)
    rows["prepare"] = 1; rows["commit"] = 1; rows["promotion_alpha"] = 1.0
    output = batch.rollout(rows)
    digest = hashlib.sha256()
    for name in (
        "snapshot_accepted", "readiness_accepted", "cas_applied", "application_reason",
        "owner", "service_epoch", "actuator_owner", "protocol_wire_hash",
        "protocol_wire_messages", "snapshot_payload", "readiness_candidate",
        "snapshot_delivery_mask", "readiness_delivery_mask", "version_match",
    ):
        digest.update(name.encode("ascii") + b"\0")
        digest.update(np.ascontiguousarray(output[name]).tobytes())
    reasons, reason_counts = np.unique(output["application_reason"], return_counts=True)
    return {
        "schema": "DISH_RBHR_R05_NATIVE_NATURAL_PROTOCOL_TRACE_V1",
        "width": width, "steps": steps,
        "snapshot_accepted": bool(np.any(output["snapshot_accepted"])),
        "readiness_accepted": bool(np.any(output["readiness_accepted"])),
        "snapshot_delivery_count": int(np.count_nonzero(output["snapshot_delivery_mask"])),
        "readiness_delivery_count": int(np.count_nonzero(output["readiness_delivery_mask"])),
        "version_match_count": int(np.count_nonzero(output["version_match"])),
        "cas_applied_count": int(np.count_nonzero(output["cas_applied"])),
        "nonzero_application_reason_count": int(np.count_nonzero(output["application_reason"])),
        "application_reason_counts": {str(int(reason)): int(count) for reason, count in zip(reasons, reason_counts)},
        "owner_epoch_actuator_consistent": bool(np.all(output["owner"] == output["actuator_owner"])),
        "wire_messages": int(output["protocol_wire_messages"][-1].sum()),
        "trace_sha256": digest.hexdigest(),
        "test_only": True, "question_relevant_output": False,
    }


def rng_words_test_native(addresses: tuple[str, ...], authority: PreactivityAuthority) -> tuple[int, ...]:
    authority.require_test_only()
    if not addresses:
        raise ProductionBackendError("RNG request must be nonempty")
    encoded = tuple(address.encode("utf-8") for address in addresses)
    if any(not value.startswith(b"DISH/RBHR/R05/") or len(value) > 4096 for value in encoded):
        raise ProductionBackendError("RNG address is outside the frozen r05 namespace")
    offsets: list[int] = []; cursor = 0
    for value in encoded:
        offsets.append(cursor); cursor += len(value)
    blob = b"".join(encoded)
    master = (ctypes.c_uint8 * 32).from_buffer_copy(TEST_MASTER)
    offset_values = (ctypes.c_uint64 * len(encoded))(*offsets)
    lengths = (ctypes.c_uint64 * len(encoded))(*(len(value) for value in encoded))
    outputs = (ctypes.c_uint64 * len(encoded))()
    code = require_cpp_batched_production_backend().dish_rbhr_prod_rng_words_batch(
        master, blob, offset_values, lengths, len(encoded), outputs
    )
    if code:
        raise ProductionBackendError(f"native RNG rejected addresses ({code})")
    return tuple(map(int, outputs))


def open_production_batch(*, authority: object | None, width: int) -> NativeBatch:
    refuse_without_root_lease(authority)
    if getattr(authority, "component", None) != COMPONENT:
        raise ProductionContractError("Root lease component differs")
    reset_rows = getattr(authority, "native_reset_rows", None)
    if not callable(reset_rows):
        raise ProductionContractError("Root lease binding lacks coordinate-bound native reset rows")
    raw_rows = tuple(reset_rows(width=width))
    if len(raw_rows) != width:
        raise ProductionContractError("coordinate-bound reset row count differs")
    resets: list[_ResetInput] = []
    scalar_names = [name for name, _ in _ResetInput._fields_ if name != "master"]
    for row in raw_rows:
        if not isinstance(row, Mapping):
            raise ProductionContractError("coordinate-bound reset row is not a mapping")
        try:
            values = [int(row[name]) for name in scalar_names]
            master_value = row["master"]
            master_bytes = bytes.fromhex(master_value) if isinstance(master_value, str) else bytes(master_value)
            if len(master_bytes) != 32:
                raise ValueError("master length")
        except (KeyError, TypeError, ValueError) as error:
            raise ProductionContractError("coordinate-bound reset row schema differs") from error
        if values[1] != 0:
            raise ProductionContractError("production reset row is not activity mode")
        resets.append(_ResetInput(values[0], (ctypes.c_uint8 * 32).from_buffer_copy(master_bytes), *values[1:]))
    return NativeBatch(tuple(resets))


__all__ = [
    "PREACTIVITY_NAMESPACE", "NativeBatch", "ProductionBackendError", "TestNativeBatch", "TestProtocolNativeBatch",
    "artifact_identity", "empty_step_rows", "native_natural_protocol_trace", "native_protocol_audit", "native_protocol_transition_probe", "open_production_batch", "rng_words_test_native",
    "require_cpp_batched_production_backend", "scan_test_candidate_attempts", "scan_production_candidate_attempts", "source_sha256",
]

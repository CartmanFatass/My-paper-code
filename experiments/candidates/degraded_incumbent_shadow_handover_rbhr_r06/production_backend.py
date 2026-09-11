"""Source-keyed C++20 batched interactive host for DISH RBHR r06.

Only the explicit TEST/nonproduction constructor is available in this module.
The future activity entry point fails closed until a separate Root lease object
is supplied by the operational lifecycle.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Mapping

import numpy as np

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.native_backend import (
    _toolchain, _vs_installation, artifact_identity as retained_gate_artifact_identity,
)
from .production_contract import (
    COMPONENT,
    TEST_NAMESPACE,
    R06ContractError,
    TestAuthority,
    refuse_activity,
)
from .production_population import TEST_MASTER, address, complete_evaluation_coordinates, test_uniform


ABI_VERSION = 1
_SOURCE = Path(__file__).with_name("native") / "rbhr_r06_production_backend.cpp"
_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/fp:strict", "/W4")
_POSIX_FLAGS = (
    "-std=c++20", "-O2", "-shared", "-fPIC", "-fno-fast-math",
    "-ffp-contract=off", "-frounding-math", "-Wall",
)


class ProductionBackendError(RuntimeError):
    pass


def decode_promotion_source_receipt(payload: bytes) -> Mapping[str, int]:
    raw = bytes(payload)
    if len(raw) != 24:
        raise ProductionBackendError("promotion-source receipt size differs")
    value = {
        "version": raw[0], "source_mode": raw[1], "cas_applied": raw[2],
        "retained_by_design": raw[3], "owner_before": raw[4], "owner_after": raw[5],
        "actuator_after": raw[6], "reserved": raw[7],
        "tick": int.from_bytes(raw[8:12], "little"),
        "service_epoch_after": int.from_bytes(raw[12:14], "little"),
        "next_payload_sequence": int.from_bytes(raw[14:18], "little"),
        "k_epoch": int.from_bytes(raw[18:20], "little"),
        "intent_origin_tick": int.from_bytes(raw[20:24], "little"),
    }
    if value["version"] != 1 or value["reserved"] != 0 or value["source_mode"] not in (0, 1, 2):
        raise ProductionBackendError("promotion-source receipt schema differs")
    return value


class _ResetInput(ctypes.Structure):
    _fields_ = [("fixture_key", ctypes.c_uint64), ("master", ctypes.c_uint8 * 32)] + [
        (name, ctypes.c_int32)
        for name in (
            "test_mode", "package", "reflection", "initial_owner", "qa_owner", "k_initial",
            "k_new", "switch_tick", "tau_d_tick", "phase", "route_speed",
            "turn_magnitude_deg", "turn_sign", "initial_ux", "initial_uy",
            "block", "split", "schedule", "evaluation_slot", "lane", "cycle",
            "arm_substream", "degradation_flag", "mask_enabled", "fork_branch", "episode",
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
        ("arm_mode", ctypes.c_int32),
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
            "block", "split", "schedule", "evaluation_slot", "lane", "cycle",
            "arm_substream", "degradation_flag", "mask_enabled", "fork_branch", "episode",
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


class _PromotionSourceForkOutput(ctypes.Structure):
    _fields_ = [
        ("retain_state", _State), ("transfer_copy_state", _State),
        ("transfer_shadow_state", _State),
        ("retain_observation", _StepOutput),
        ("transfer_copy_observation", _StepOutput),
        ("transfer_shadow_observation", _StepOutput),
        ("retain_receipt", ctypes.c_uint8 * 24),
        ("transfer_copy_receipt", ctypes.c_uint8 * 24),
        ("transfer_shadow_receipt", ctypes.c_uint8 * 24),
        *[(name, ctypes.c_int32) for name in (
            "linearization_owner", "linearization_intent_owner",
            "linearization_service_epoch", "linearization_intent_epoch",
            "linearization_next_payload_sequence", "linearization_intent_next_sequence",
            "linearization_k_epoch", "linearization_intent_k_epoch",
            "linearization_intent_origin_tick", "linearization_snapshot_tick",
            "linearization_readiness_tick", "linearization_readiness_snapshot_tick",
            "linearization_intent_snapshot_tick", "linearization_intent_readiness_tick",
        )],
        ("linearization_lineage_lock", ctypes.c_int32 * 2),
        ("linearization_lineage_sequence", ctypes.c_int32 * 2),
        ("linearization_controller_hidden", ctypes.c_double * 512),
        ("parent_byte_immutable", ctypes.c_int32),
        ("combined_predicate_valid", ctypes.c_int32),
        ("retain_cas_applied", ctypes.c_int32),
        ("transfer_copy_cas_applied", ctypes.c_int32),
        ("transfer_shadow_cas_applied", ctypes.c_int32),
        ("retained_by_design", ctypes.c_int32),
        ("application_latency_ticks", ctypes.c_int32),
        ("receipt_bytes", ctypes.c_int32),
        ("retain_alpha", ctypes.c_double),
        ("transfer_copy_alpha", ctypes.c_double),
        ("transfer_shadow_alpha", ctypes.c_double),
        ("transaction_energy", ctypes.c_double),
    ]


class _PhysicsTick(ctypes.Structure):
    _fields_ = [
        ("gx", ctypes.c_double), ("gy", ctypes.c_double),
        ("gvx", ctypes.c_double), ("gvy", ctypes.c_double),
        ("camera_z", ctypes.c_double * 4),
        ("camera_present", ctypes.c_int32 * 2),
        ("radio", ctypes.c_double * 6),
        ("source_noise", ctypes.c_double * 4),
        ("wind_eta", ctypes.c_double * 2),
    ]


class _B01PreparedTick(ctypes.Structure):
    _fields_ = [
        ("state", _State), ("observation", _StepOutput),
        ("physics", _PhysicsTick),
        ("snapshot_delivered", ctypes.c_int32),
        ("readiness_delivered", ctypes.c_int32),
        ("origin_valid", ctypes.c_int32),
    ]


class _B01RecurrentHandoff(ctypes.Structure):
    _fields_ = [("controller_hidden", ctypes.c_double * 512)]


class _PassiveLabelOutput(ctypes.Structure):
    _fields_ = [
        ("target", ctypes.c_double * 4), ("links", ctypes.c_double * 8),
        ("missing", ctypes.c_int32 * 4), ("q_labels", ctypes.c_int32 * 20),
        ("q_mask", ctypes.c_int32), ("next_mask", ctypes.c_int32),
        ("q_copy_index", ctypes.c_int32),
    ]


class _ScriptOutput(ctypes.Structure):
    _fields_ = [("raw_action", ctypes.c_double * 4), ("transfer", ctypes.c_int32), ("score", ctypes.c_double)]


class _RecoveryWitnessOutput(ctypes.Structure):
    _fields_ = [
        ("origin_exists", ctypes.c_int32), ("origin_tick", ctypes.c_int32),
        ("real_service_ticks", ctypes.c_int32), ("retain_service_ticks", ctypes.c_int32),
        ("opportunities_checked", ctypes.c_int32), ("rejection_mask", ctypes.c_int32),
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


def _decode_step_outputs(outputs: object, width: int) -> Mapping[str, np.ndarray]:
    raw = np.frombuffer(outputs, dtype=np.dtype(_StepOutput), count=width)
    return {
        "actor": raw["actor"].reshape(width, 4, 54).copy(),
        "critic": raw["critic"].reshape(width, 58).copy(),
        **{name: raw[name].copy() for name in (
            "service", "renew", "terminal", "owner", "service_epoch",
            "next_payload_sequence", "handover_used", "invalid_commit", "token_gap",
            "dual_owner", "dual_payload", "buffer_clear", "command_slew_breach",
            "separation_breach", "tick", "protocol_bytes", "min_separation",
            "total_energy", "snapshot_accepted", "readiness_accepted",
            "application_reason", "cas_applied", "actuator_owner",
            "protocol_wire_hash", "protocol_wire_messages", "snapshot_payload",
            "readiness_candidate", "snapshot_delivery_mask", "readiness_delivery_mask",
            "version_match",
        )},
    }


def _ordinary_decision_observation(
    decoded: Mapping[str, np.ndarray], countdown: np.ndarray,
) -> dict[str, np.ndarray]:
    """Operational renew is [countdown==0]; raw completed-transition flag is renew_completed."""
    raw = np.asarray(decoded["renew"])
    observation = dict(decoded)
    observation["renew_completed"] = np.array(raw, copy=True)
    observation["renew"] = np.asarray(np.asarray(countdown) == 0, dtype=raw.dtype)
    return observation


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha256() -> str:
    return _sha256(_SOURCE)


def _production_toolchain() -> Mapping[str, object]:
    if os.name == "nt":
        return _toolchain()
    compiler = Path(shutil.which("c++")).resolve()
    result = subprocess.run(
        [str(compiler), "--version"], check=True, capture_output=True, text=True,
    )
    return {
        "compiler": str(compiler), "compiler_sha256": _sha256(compiler),
        "version": result.stdout.strip(), "flags": list(_POSIX_FLAGS),
    }


def _build_material() -> tuple[str, bytes]:
    source = _SOURCE.read_bytes()
    toolchain = _production_toolchain()
    digest = hashlib.sha256()
    digest.update(b"DISH-RBHR-R06-PRODUCTION-HOST-v1\0")
    digest.update(hashlib.sha256(source).digest())
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    digest.update(ABI_VERSION.to_bytes(4, "big"))
    for flag in toolchain["flags"]:
        digest.update(flag.encode("ascii") + b"\0")
    return digest.hexdigest(), source


def _artifact_path(key: str) -> Path:
    suffix = ".dll" if os.name == "nt" else ".so"
    return Path(tempfile.gettempdir()) / "hmasd_dish_rbhr_r06_production" / key / f"rbhr_r06_production_backend{suffix}"


def _compile(key: str, source: bytes) -> Path:
    target = _artifact_path(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot = target.parent / "rbhr_r06_production_backend.source.cpp"
    if snapshot.is_file() and snapshot.read_bytes() != source:
        raise ProductionBackendError("source-key snapshot differs")
    if not snapshot.is_file():
        temporary = snapshot.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
        with temporary.open("wb") as stream:
            stream.write(source); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, snapshot)
    if target.is_file():
        return target
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    candidate = target.parent / f"rbhr_r06_production_backend.{suffix}{target.suffix}"
    if os.name == "nt":
        vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
        obj = target.parent / f"rbhr_r06_production_backend.{suffix}.obj"
        command: str | list[str] = f'call "{vcvars}" >nul && cl {" ".join(_FLAGS)} "{snapshot}" /Fo:"{obj}" /link /OUT:"{candidate}"'
        result = subprocess.run(command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"), cwd=target.parent, capture_output=True, text=True)
    else:
        toolchain = _production_toolchain()
        obj = None
        command = [str(toolchain["compiler"]), *toolchain["flags"], str(snapshot), "-o", str(candidate)]
        result = subprocess.run(command, cwd=target.parent, capture_output=True, text=True)
    if result.returncode != 0 or not candidate.is_file():
        raise ProductionBackendError(f"native compilation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    try:
        os.replace(candidate, target)
    except OSError:
        if not target.is_file():
            raise
        candidate.unlink(missing_ok=True)
    finally:
        if obj is not None:
            obj.unlink(missing_ok=True)
    return target


def _configure(lib: ctypes.CDLL) -> ctypes.CDLL:
    lib.dish_rbhr_r06_prod_abi_version.argtypes = []; lib.dish_rbhr_r06_prod_abi_version.restype = ctypes.c_int32
    size_names = (
        "reset_input", "step_input", "state", "step_output", "fork_output", "passive_label_output", "script_output", "recovery_witness_output", "protocol_audit_output",
        "protocol_transition_output", "promotion_source_fork_output",
    )
    observed = [lib.dish_rbhr_r06_prod_abi_version()]
    for name in size_names:
        function = getattr(lib, f"dish_rbhr_r06_prod_{name}_size")
        function.argtypes = []; function.restype = ctypes.c_uint64; observed.append(function())
    expected = [ABI_VERSION, *map(ctypes.sizeof, (
        _ResetInput, _StepInput, _State, _StepOutput, _ForkOutput, _PassiveLabelOutput, _ScriptOutput, _RecoveryWitnessOutput, _ProtocolAuditOutput,
        _ProtocolTransitionOutput, _PromotionSourceForkOutput,
    ))]
    if observed != expected:
        raise ProductionBackendError(f"production ABI differs: observed={observed}, expected={expected}")
    for name, expected_size in (
        ("b01_prepared_tick", ctypes.sizeof(_B01PreparedTick)),
        ("b01_recurrent_handoff", ctypes.sizeof(_B01RecurrentHandoff)),
    ):
        function = getattr(lib, f"dish_rbhr_r06_prod_{name}_size")
        function.argtypes = []; function.restype = ctypes.c_uint64
        if function() != expected_size:
            raise ProductionBackendError(f"private B01 ABI differs: {name}")
    lib.dish_rbhr_r06_prod_reset_batch.argtypes = [ctypes.POINTER(_ResetInput), ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_r06_prod_reset_selected_batch.argtypes = [ctypes.POINTER(_ResetInput), ctypes.POINTER(ctypes.c_int32), ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_r06_prod_step_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_r06_prod_rollout_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_r06_prod_passive_labels_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.POINTER(_PassiveLabelOutput)]
    lib.dish_rbhr_r06_prod_first_application_valid_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32)]
    lib.dish_rbhr_r06_prod_clone_promotion_source_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.POINTER(_PromotionSourceForkOutput)]
    lib.dish_rbhr_r06_prod_b01_prepare_batch.argtypes = [ctypes.POINTER(_State), ctypes.c_uint64, ctypes.POINTER(_B01PreparedTick)]
    lib.dish_rbhr_r06_prod_b01_complete_batch.argtypes = [ctypes.POINTER(_B01PreparedTick), ctypes.POINTER(_StepInput), ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepOutput)]
    lib.dish_rbhr_r06_prod_b01_clone_prepared_batch.argtypes = [ctypes.POINTER(_B01PreparedTick), ctypes.POINTER(_B01RecurrentHandoff), ctypes.c_uint64, ctypes.POINTER(_PromotionSourceForkOutput)]
    lib.dish_rbhr_r06_prod_b01_test_fixture_batch.argtypes = [ctypes.c_int32, ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepOutput)]
    lib.clone_promotion_source_batch.argtypes = [ctypes.POINTER(_State), ctypes.POINTER(_StepInput), ctypes.c_size_t, ctypes.POINTER(_PromotionSourceForkOutput)]
    lib.clone_promotion_source_batch.restype = ctypes.c_int32
    lib.dish_rbhr_r06_prod_source_factored_test_fixture_batch.argtypes = [ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepInput)]
    lib.dish_rbhr_r06_prod_source_factored_test_mismatch_fixture_batch.argtypes = [ctypes.c_int32, ctypes.c_uint64, ctypes.POINTER(_State), ctypes.POINTER(_StepInput)]
    lib.dish_rbhr_r06_prod_clone_real_sham_batch.argtypes = [ctypes.POINTER(_State), ctypes.c_uint64, ctypes.POINTER(_ForkOutput)]
    lib.dish_rbhr_r06_prod_script_batch.argtypes = [ctypes.POINTER(_State), ctypes.c_uint64, ctypes.POINTER(_ScriptOutput)]
    lib.dish_rbhr_r06_prod_recovery_witness_batch.argtypes = [ctypes.POINTER(_ResetInput), ctypes.c_uint64, ctypes.POINTER(_RecoveryWitnessOutput)]
    lib.dish_rbhr_r06_prod_protocol_audit.argtypes = [ctypes.POINTER(_ProtocolAuditOutput)]
    lib.dish_rbhr_r06_prod_protocol_audit.restype = ctypes.c_int32
    lib.dish_rbhr_r06_prod_protocol_transition_probe.argtypes = [ctypes.POINTER(_ProtocolTransitionOutput)]
    lib.dish_rbhr_r06_prod_protocol_transition_probe.restype = ctypes.c_int32
    lib.dish_rbhr_r06_prod_rng_words_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64),
    ]
    for name in (
        "reset_batch", "reset_selected_batch", "step_batch", "rollout_batch", "passive_labels_batch", "first_application_valid_batch", "clone_real_sham_batch",
        "script_batch", "recovery_witness_batch", "rng_words_batch",
        "clone_promotion_source_batch", "source_factored_test_fixture_batch",
        "source_factored_test_mismatch_fixture_batch", "b01_prepare_batch",
        "b01_complete_batch", "b01_clone_prepared_batch", "b01_test_fixture_batch",
    ):
        getattr(lib, f"dish_rbhr_r06_prod_{name}").restype = ctypes.c_int32
    return lib


def require_cpp_batched_production_backend() -> ctypes.CDLL:
    key, source = _build_material()
    with _LOCK:
        if key not in _LOADED:
            _LOADED[key] = _configure(ctypes.CDLL(str(_compile(key, source))))
        return _LOADED[key]


def artifact_identity() -> dict[str, object]:
    key, source = _build_material(); path = _artifact_path(key); existed = path.is_file(); started = time.perf_counter(); lib = require_cpp_batched_production_backend()
    if os.name == "nt":
        gate = retained_gate_artifact_identity()
    else:
        gate = {
            "schema": "DISH_RBHR_R06_NATIVE_RNG_GENERATOR_SERVICE_IDENTITY_V1",
            "component": COMPONENT,
            "artifact": str(path),
            "artifact_sha256": _sha256(path),
            "artifact_bytes": path.stat().st_size,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "build_key": key,
            "cache_present_before": existed,
            "abi_version": lib.dish_rbhr_r06_prod_abi_version(),
            "rng_entry_point": "dish_rbhr_r06_prod_rng_words_batch",
            "toolchain": _production_toolchain(),
            "python_fallback": False,
        }
    return {
        "component": COMPONENT,
        "artifact": str(path),
        "artifact_sha256": _sha256(path),
        "artifact_bytes": path.stat().st_size,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "build_key": key,
        "load_seconds": time.perf_counter() - started,
        "cache_present_before": existed,
        "abi_version": lib.dish_rbhr_r06_prod_abi_version(),
        "abi_sizes": {
            "reset_input": ctypes.sizeof(_ResetInput), "step_input": ctypes.sizeof(_StepInput),
            "state": ctypes.sizeof(_State), "step_output": ctypes.sizeof(_StepOutput),
            "fork_output": ctypes.sizeof(_ForkOutput), "passive_label_output": ctypes.sizeof(_PassiveLabelOutput),
            "script_output": ctypes.sizeof(_ScriptOutput),
            "recovery_witness_output": ctypes.sizeof(_RecoveryWitnessOutput),
            "protocol_audit_output": ctypes.sizeof(_ProtocolAuditOutput),
            "protocol_transition_output": ctypes.sizeof(_ProtocolTransitionOutput),
            "promotion_source_fork_output": ctypes.sizeof(_PromotionSourceForkOutput),
        },
        "accepted_native_rng_generator_service": gate,
        "full_reset_step_cpp": True,
        "python_environment_fallback": False,
    }


class B01PreparedBatch:
    """Immutable normal-mode state after arrivals and before application policy/CAS."""

    def __init__(self, values: object, width: int) -> None:
        self._values = values
        self.width = width

    def snapshot_bytes(self) -> bytes:
        return bytes(self._values)

    def observe(self) -> Mapping[str, np.ndarray]:
        raw = np.frombuffer(self._values, dtype=np.dtype(_B01PreparedTick), count=self.width)
        outputs = (_StepOutput * self.width)()
        for index in range(self.width):
            outputs[index] = _StepOutput.from_buffer_copy(raw[index]["observation"].tobytes())
        return _decode_step_outputs(outputs, self.width)

    @property
    def origin_valid(self) -> np.ndarray:
        raw = np.frombuffer(self._values, dtype=np.dtype(_B01PreparedTick), count=self.width)
        return raw["origin_valid"].astype(bool, copy=True)


class NativeBatch:
    """Persistent native state with NumPy-backed batch inputs and no scalar loop."""

    library = None

    def __init__(self, resets: tuple[_ResetInput, ...], *, library=None) -> None:
        self.library = library
        width = len(resets)
        if width <= 0:
            raise ProductionBackendError("width must be positive")
        self.width = width
        self._states = (_State * width)()
        self._outputs = (_StepOutput * width)()
        reset_array = (_ResetInput * width)()
        for index, reset in enumerate(resets):
            reset_array[index] = reset
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_reset_batch(reset_array, width, self._states, self._outputs)
        if code:
            raise ProductionBackendError(f"native reset rejected batch ({code})")

    def observe(self) -> Mapping[str, np.ndarray]:
        """Copy the current reset/step boundary without advancing native state."""
        decoded = _decode_step_outputs(self._outputs, self.width)
        countdown = np.frombuffer(
            self._states, dtype=np.dtype(_State), count=self.width,
        )["countdown"]
        return _ordinary_decision_observation(decoded, countdown)

    def reset_selected(self, mask: np.ndarray, rows: tuple[Mapping[str, object], ...]) -> Mapping[str, np.ndarray]:
        selected = np.asarray(mask, dtype=np.int32)
        if selected.shape != (self.width,) or len(rows) != self.width:
            raise ProductionBackendError("selected reset inventory differs")
        scalar_names = [name for name, _ in _ResetInput._fields_ if name != "master"]
        reset_array = (_ResetInput * self.width)()
        for index, row in enumerate(rows):
            values = [int(row[name]) for name in scalar_names]
            raw_master = row["master"]
            master = bytes.fromhex(raw_master) if isinstance(raw_master, str) else bytes(raw_master)
            if len(master) != 32 or values[1] != 0:
                raise ProductionBackendError("selected reset row differs")
            reset_array[index] = _ResetInput(values[0], (ctypes.c_uint8 * 32).from_buffer_copy(master), *values[1:])
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_reset_selected_batch(
            reset_array, selected.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
            self.width, self._states, self._outputs,
        )
        if code:
            raise ProductionBackendError(f"native selected reset rejected batch ({code})")
        return self.observe()

    @classmethod
    def test_only(cls, width: int, authority: TestAuthority) -> "NativeBatch":
        authority.require_test_only()
        return cls(_test_reset_inputs(width))

    @classmethod
    def _from_states(cls, states: tuple[_State, ...]) -> "NativeBatch":
        if not states:
            raise ProductionBackendError("fork state batch is empty")
        value = cls.__new__(cls); value.width = len(states)
        value._states = (_State * value.width)(); value._outputs = (_StepOutput * value.width)()
        for index, state in enumerate(states):
            value._states[index] = state
        return value

    @classmethod
    def from_snapshot_bytes(cls, payload: bytes) -> "NativeBatch":
        raw = bytes(payload)
        unit = ctypes.sizeof(_State) + ctypes.sizeof(_StepOutput)
        if not raw or len(raw) % unit:
            raise ProductionBackendError("native snapshot byte count differs")
        width = len(raw) // unit
        value = cls.__new__(cls); value.width = width
        state_bytes = raw[:width * ctypes.sizeof(_State)]
        output_bytes = raw[width * ctypes.sizeof(_State):]
        value._states = (_State * width).from_buffer_copy(state_bytes)
        value._outputs = (_StepOutput * width).from_buffer_copy(output_bytes)
        return value

    def snapshot_bytes(self) -> bytes:
        return bytes(self._states) + bytes(self._outputs)

    def prepare_b01_tick(self) -> B01PreparedBatch:
        prepared = (_B01PreparedTick * self.width)()
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_b01_prepare_batch(
            self._states, self.width, prepared,
        )
        if code:
            raise ProductionBackendError(f"native B01 prepare rejected batch ({code})")
        return B01PreparedBatch(prepared, self.width)

    def complete_b01_tick(
        self, prepared: B01PreparedBatch, rows: np.ndarray,
    ) -> Mapping[str, np.ndarray]:
        if prepared.width != self.width:
            raise ProductionBackendError("B01 prepared width differs")
        values = np.ascontiguousarray(rows, dtype=np.dtype(_StepInput))
        if values.shape != (self.width,):
            raise ProductionBackendError("B01 completion rows differ")
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_b01_complete_batch(
            prepared._values, values.ctypes.data_as(ctypes.POINTER(_StepInput)), self.width,
            self._states, self._outputs,
        )
        if code:
            raise ProductionBackendError(f"native B01 completion rejected batch ({code})")
        return self.observe()

    def clone_b01_prepared_batches(
        self, prepared: B01PreparedBatch, hidden: np.ndarray,
    ) -> tuple[Mapping[str, "NativeBatch"], Mapping[str, Mapping[str, np.ndarray]], Mapping[str, object]]:
        if prepared.width != self.width:
            raise ProductionBackendError("B01 prepared clone width differs")
        recurrent = np.asarray(hidden, dtype=np.float64)
        if recurrent.shape != (self.width, 4, 128):
            raise ProductionBackendError("B01 recurrent handoff shape differs")
        if not np.isfinite(recurrent).all() or np.any(np.abs(recurrent) > 1.0):
            raise ProductionBackendError("B01 recurrent handoff values differ")
        handoffs = (_B01RecurrentHandoff * self.width)()
        flat = recurrent.reshape(self.width, 512)
        for index in range(self.width):
            handoffs[index] = _B01RecurrentHandoff(
                (ctypes.c_double * 512)(*map(float, flat[index]))
            )
        outputs = (_PromotionSourceForkOutput * self.width)()
        code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_b01_clone_prepared_batch(
            prepared._values, handoffs, self.width, outputs,
        )
        if code:
            raise ProductionBackendError(f"native B01 prepared clone rejected batch ({code})")
        raw = np.frombuffer(outputs, dtype=np.dtype(_PromotionSourceForkOutput), count=self.width).copy()
        if not (
            np.all(raw["retain_cas_applied"] == 0)
            and np.all(raw["transfer_copy_cas_applied"] == 1)
            and np.all(raw["transfer_shadow_cas_applied"] == 1)
            and np.all(raw["transaction_energy"] == 0.48)
        ):
            raise ProductionBackendError("native B01 branch contract differs")
        names = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
        state_fields = ("retain_state", "transfer_copy_state", "transfer_shadow_state")
        observation_fields = ("retain_observation", "transfer_copy_observation", "transfer_shadow_observation")
        receipt_fields = ("retain_receipt", "transfer_copy_receipt", "transfer_shadow_receipt")
        batches: dict[str, NativeBatch] = {}
        observations: dict[str, Mapping[str, np.ndarray]] = {}
        receipts: dict[str, tuple[bytes, ...]] = {}
        branch_hidden: dict[str, np.ndarray] = {}
        branch_prepared: dict[str, B01PreparedBatch] = {}
        for mode, name, state_field, observation_field, receipt_field in zip(
            range(3), names, state_fields, observation_fields, receipt_fields,
        ):
            states = tuple(_State.from_buffer_copy(raw[index][state_field].tobytes()) for index in range(self.width))
            batch = NativeBatch._from_states(states)
            branch_outputs = (_StepOutput * self.width)()
            for index in range(self.width):
                branch_outputs[index] = _StepOutput.from_buffer_copy(raw[index][observation_field].tobytes())
                batch._outputs[index] = branch_outputs[index]
            batches[name] = batch
            observations[name] = _decode_step_outputs(branch_outputs, self.width)
            tokens = (_B01PreparedTick * self.width)()
            for index in range(self.width):
                tokens[index].state = states[index]
                tokens[index].observation = branch_outputs[index]
                tokens[index].physics = prepared._values[index].physics
                tokens[index].snapshot_delivered = prepared._values[index].snapshot_delivered
                tokens[index].readiness_delivered = prepared._values[index].readiness_delivered
                tokens[index].origin_valid = 0
            branch_prepared[name] = B01PreparedBatch(tokens, self.width)
            receipts[name] = tuple(bytes(raw[index][receipt_field]) for index in range(self.width))
            if any(decode_promotion_source_receipt(value)["source_mode"] != mode for value in receipts[name]):
                raise ProductionBackendError("native B01 receipt mode differs")
            branch_hidden[name] = np.stack([
                np.asarray(raw[index][state_field]["controller_hidden"], dtype=np.float64).reshape(4, 128)
                for index in range(self.width)
            ])
        return batches, observations, {
            "raw_receipts": receipts, "branch_hidden": branch_hidden,
            "branch_prepared": branch_prepared, "materialized_before_policy_forward": True,
        }

    def step(self, rows: np.ndarray) -> Mapping[str, np.ndarray]:
        expected = np.dtype(_StepInput)
        values = np.ascontiguousarray(rows, dtype=expected)
        if values.shape != (self.width,):
            raise ProductionBackendError("step rows must be one structured row per lane")
        pointer = values.ctypes.data_as(ctypes.POINTER(_StepInput))
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_step_batch(self._states, pointer, self.width, self._outputs)
        if code:
            raise ProductionBackendError(f"native step rejected batch ({code})")
        return self.observe()

    def rollout(self, rows: np.ndarray) -> Mapping[str, np.ndarray]:
        expected = np.dtype(_StepInput)
        values = np.ascontiguousarray(rows, dtype=expected)
        if values.ndim != 2 or values.shape[1] != self.width:
            raise ProductionBackendError("rollout rows must be [ticks,width]")
        steps = values.shape[0]
        outputs = (_StepOutput * (steps * self.width))()
        pointer = values.ctypes.data_as(ctypes.POINTER(_StepInput))
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_rollout_batch(
            self._states, pointer, steps, self.width, outputs
        )
        if code:
            raise ProductionBackendError(f"native rollout rejected batch ({code})")
        raw = np.frombuffer(outputs, dtype=np.dtype(_StepOutput), count=steps * self.width).reshape(steps, self.width)
        decoded = {
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
            "token_gap": raw["token_gap"].copy(),
            "dual_owner": raw["dual_owner"].copy(),
            "dual_payload": raw["dual_payload"].copy(),
            "buffer_clear": raw["buffer_clear"].copy(),
            "command_slew_breach": raw["command_slew_breach"].copy(),
            "separation_breach": raw["separation_breach"].copy(),
            "tick": raw["tick"].copy(),
            "protocol_bytes": raw["protocol_bytes"].copy(),
            "total_energy": raw["total_energy"].copy(),
            "min_separation": raw["min_separation"].copy(),
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
        # Per-tick current countdown is actor feature 42; `_states` holds only the final lane.
        return _ordinary_decision_observation(decoded, decoded["actor"][:, :, 0, 42])

    def passive_labels(self, rows: np.ndarray) -> Mapping[str, np.ndarray]:
        values = np.ascontiguousarray(rows, dtype=np.dtype(_StepInput))
        if values.shape != (self.width,):
            raise ProductionBackendError("passive-label step rows differ")
        outputs = (_PassiveLabelOutput * self.width)()
        code = (self.library or require_cpp_batched_production_backend()).dish_rbhr_r06_prod_passive_labels_batch(
            self._states, values.ctypes.data_as(ctypes.POINTER(_StepInput)), self.width, outputs,
        )
        if code:
            raise ProductionBackendError(f"native passive labels rejected batch ({code})")
        raw = np.frombuffer(outputs, dtype=np.dtype(_PassiveLabelOutput), count=self.width)
        return {
            "target": raw["target"].copy(),
            "links": raw["links"].reshape(self.width, 4, 2).copy(),
            "missing": raw["missing"].copy(), "q_labels": raw["q_labels"].copy(),
            "q_mask": raw["q_mask"].astype(bool, copy=True),
            "next_mask": raw["next_mask"].astype(bool, copy=True),
            "q_copy_index": raw["q_copy_index"].copy(),
        }

    def clone_real_sham(self) -> np.ndarray:
        outputs = (_ForkOutput * self.width)()
        code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_clone_real_sham_batch(self._states, self.width, outputs)
        if code:
            raise ProductionBackendError(f"native fork clone rejected state ({code})")
        return np.frombuffer(outputs, dtype=np.dtype(_ForkOutput), count=self.width).copy()

    def clone_promotion_source(self, rows: np.ndarray) -> np.ndarray:
        """Validate and clone RETAIN/COPY/SHADOW in one nonmutating native call."""

        values = np.ascontiguousarray(rows, dtype=np.dtype(_StepInput))
        if values.shape != (self.width,):
            raise ProductionBackendError("promotion-source rows differ")
        before = bytes(self._states)
        outputs = (_PromotionSourceForkOutput * self.width)()
        code = require_cpp_batched_production_backend().clone_promotion_source_batch(
            self._states, values.ctypes.data_as(ctypes.POINTER(_StepInput)), self.width, outputs,
        )
        if code:
            raise ProductionBackendError(f"native promotion-source clone rejected batch ({code})")
        if bytes(self._states) != before:
            raise ProductionBackendError("native promotion-source clone mutated parent")
        raw = np.frombuffer(outputs, dtype=np.dtype(_PromotionSourceForkOutput), count=self.width).copy()
        if not np.all(raw["parent_byte_immutable"] == 1):
            raise ProductionBackendError("native promotion-source immutability witness differs")
        if not np.all(raw["combined_predicate_valid"] == 1):
            raise ProductionBackendError("native promotion-source predicate witness differs")
        exact = (
            np.all(raw["retain_cas_applied"] == 0) and
            np.all(raw["transfer_copy_cas_applied"] == 1) and
            np.all(raw["transfer_shadow_cas_applied"] == 1) and
            np.all(raw["retained_by_design"] == 1) and
            np.all(raw["application_latency_ticks"] == 1) and
            np.all(raw["receipt_bytes"] == 24) and
            np.all(raw["retain_alpha"] == -1.0) and
            np.all(raw["transfer_copy_alpha"] == 0.0) and
            np.all(raw["transfer_shadow_alpha"] == 1.0) and
            np.all(raw["transaction_energy"] == 0.48)
        )
        if not exact:
            raise ProductionBackendError("native promotion-source transaction contract differs")
        for index in range(self.width):
            for field in ("retain_state", "transfer_copy_state", "transfer_shadow_state"):
                branch = raw[index][field]
                parent = self._states[index]
                if (int(branch["tick"]) != parent.tick or
                        int(branch["protocol_bytes"]) - parent.protocol_bytes != 24 or
                        abs(float(branch["total_energy"]) - parent.total_energy - 0.48) > 1e-12):
                    raise ProductionBackendError("native promotion-source equal transaction accounting differs")
        return raw

    def clone_promotion_source_batches(
        self, rows: np.ndarray,
    ) -> tuple[Mapping[str, "NativeBatch"], Mapping[str, Mapping[str, np.ndarray]], Mapping[str, object]]:
        current = np.ascontiguousarray(rows, dtype=np.dtype(_StepInput))
        raw = self.clone_promotion_source(current)
        names = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
        state_fields = ("retain_state", "transfer_copy_state", "transfer_shadow_state")
        observation_fields = ("retain_observation", "transfer_copy_observation", "transfer_shadow_observation")
        batches = {}
        for name, state_field, observation_field in zip(names, state_fields, observation_fields):
            batch = NativeBatch._from_states(tuple(
                _State.from_buffer_copy(raw[index][state_field].tobytes()) for index in range(self.width)
            ))
            for index in range(self.width):
                batch._outputs[index] = _StepOutput.from_buffer_copy(raw[index][observation_field].tobytes())
            batches[name] = batch
        observations = {}
        for name, field in zip(names, observation_fields):
            output = np.ascontiguousarray(raw[field])
            observations[name] = {
                "actor": output["actor"].reshape(self.width, 4, 54).copy(),
                "critic": output["critic"].reshape(self.width, 58).copy(),
                **{key: output[key].copy() for key in (
                    "owner", "service_epoch", "next_payload_sequence", "handover_used",
                    "invalid_commit", "tick", "protocol_bytes", "min_separation", "total_energy",
                    "snapshot_accepted", "readiness_accepted", "application_reason", "cas_applied",
                    "actuator_owner", "protocol_wire_messages", "version_match",
                )},
            }
        raw_receipt_fields = ("retain_receipt", "transfer_copy_receipt", "transfer_shadow_receipt")
        raw_receipts = {
            name: tuple(bytes(raw[index][field]) for index in range(self.width))
            for name, field in zip(names, raw_receipt_fields)
        }
        for index in range(self.width):
            lane_receipts = tuple(raw_receipts[name][index] for name in names)
            if any(len(value) != 24 for value in lane_receipts):
                raise ProductionBackendError("promotion-source raw receipt size differs")
            state = self._states[index]; row = raw[index]
            direct_fields = {
                "linearization_owner": state.owner,
                "linearization_intent_owner": state.intent_owner,
                "linearization_service_epoch": state.service_epoch,
                "linearization_intent_epoch": state.intent_epoch,
                "linearization_next_payload_sequence": state.next_payload_sequence,
                "linearization_intent_next_sequence": state.intent_next_sequence,
                "linearization_k_epoch": state.k_epoch,
                "linearization_intent_k_epoch": state.intent_k_epoch,
                "linearization_intent_origin_tick": state.intent_origin_tick,
                "linearization_snapshot_tick": state.snapshot_tick,
                "linearization_readiness_tick": state.readiness_tick,
                "linearization_readiness_snapshot_tick": state.readiness_snapshot_tick,
                "linearization_intent_snapshot_tick": state.intent_snapshot_tick,
                "linearization_intent_readiness_tick": state.intent_readiness_tick,
            }
            if any(int(row[name]) != int(value) for name, value in direct_fields.items()):
                raise ProductionBackendError("promotion-source direct linearization tuple differs")
            if (not np.array_equal(row["linearization_lineage_lock"], np.asarray(state.lineage_lock)) or
                    not np.array_equal(row["linearization_lineage_sequence"], np.asarray(state.lineage_sequence)) or
                    not np.array_equal(row["linearization_controller_hidden"], current["controller_hidden"][index])):
                raise ProductionBackendError("promotion-source direct lineage or recurrent tuple differs")
            for mode, name, branch_field in zip(range(3), names, state_fields):
                receipt = decode_promotion_source_receipt(raw_receipts[name][index]); branch = raw[index][branch_field]
                expected_cas = 0 if mode == 0 else 1; expected_retained = 1 if mode == 0 else 0
                if (
                    receipt["source_mode"] != mode or receipt["cas_applied"] != expected_cas or
                    receipt["retained_by_design"] != expected_retained or
                    receipt["owner_before"] != state.owner or receipt["owner_after"] != int(branch["owner"]) or
                    receipt["actuator_after"] != int(branch["actuator_owner"]) or
                    receipt["tick"] != int(branch["tick"]) or
                    receipt["service_epoch_after"] != int(branch["service_epoch"]) or
                    receipt["next_payload_sequence"] != int(branch["next_payload_sequence"]) or
                    receipt["k_epoch"] != int(branch["k_epoch"]) or
                    receipt["intent_origin_tick"] != state.intent_origin_tick
                ):
                    raise ProductionBackendError("promotion-source receipt/state semantics differ")
        state_observation_fields = (
            "owner", "service_epoch", "next_payload_sequence", "handover_used", "invalid_commit",
            "tick", "protocol_bytes", "min_separation", "total_energy", "snapshot_accepted",
            "readiness_accepted", "application_reason", "cas_applied", "actuator_owner",
            "protocol_wire_messages",
        )
        for state_field, observation_field in zip(state_fields, observation_fields):
            for index in range(self.width):
                state = raw[index][state_field]; observation = raw[index][observation_field]
                if any(state[name] != observation[name] for name in state_observation_fields):
                    raise ProductionBackendError("native promotion-source observation/state binding differs")
        metadata = {
            "raw_receipts": raw_receipts,
            "linearization_tuples": tuple({
                "owner": int(raw[index]["linearization_owner"]),
                "intent_owner": int(raw[index]["linearization_intent_owner"]),
                "service_epoch": int(raw[index]["linearization_service_epoch"]),
                "intent_epoch": int(raw[index]["linearization_intent_epoch"]),
                "next_payload_sequence": int(raw[index]["linearization_next_payload_sequence"]),
                "intent_next_sequence": int(raw[index]["linearization_intent_next_sequence"]),
                "k_epoch": int(raw[index]["linearization_k_epoch"]),
                "intent_k_epoch": int(raw[index]["linearization_intent_k_epoch"]),
                "intent_origin_tick": int(raw[index]["linearization_intent_origin_tick"]),
                "snapshot_tick": int(raw[index]["linearization_snapshot_tick"]),
                "readiness_tick": int(raw[index]["linearization_readiness_tick"]),
                "readiness_snapshot_tick": int(raw[index]["linearization_readiness_snapshot_tick"]),
                "intent_snapshot_tick": int(raw[index]["linearization_intent_snapshot_tick"]),
                "intent_readiness_tick": int(raw[index]["linearization_intent_readiness_tick"]),
                "lineage_lock": tuple(map(int, raw[index]["linearization_lineage_lock"])),
                "lineage_sequence": tuple(map(int, raw[index]["linearization_lineage_sequence"])),
                "controller_hidden": tuple(map(float, raw[index]["linearization_controller_hidden"])),
            } for index in range(self.width)),
            "parent_byte_immutable": True, "combined_predicate_valid": True,
            "application_latency_ticks": 1, "receipt_bytes": 24,
            "transaction_energy": 0.48,
            "retained_by_design": {"RETAIN": 1, "TRANSFER_COPY": 0, "TRANSFER_SHADOW": 0},
            "cas_applied": {"RETAIN": 0, "TRANSFER_COPY": 1, "TRANSFER_SHADOW": 1},
            "materialized_before_policy_forward": True,
        }
        return batches, observations, metadata

    def first_application_valid(self, rows: np.ndarray) -> np.ndarray:
        values = np.ascontiguousarray(rows, dtype=np.dtype(_StepInput))
        if values.shape != (self.width,):
            raise ProductionBackendError("application-predicate rows differ")
        outputs = (ctypes.c_int32 * self.width)()
        code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_first_application_valid_batch(
            self._states, values.ctypes.data_as(ctypes.POINTER(_StepInput)), self.width, outputs,
        )
        if code:
            raise ProductionBackendError(f"native application predicate rejected batch ({code})")
        return np.frombuffer(outputs, dtype=np.int32, count=self.width).astype(bool, copy=True)

    def clone_real_sham_batches(self) -> tuple["NativeBatch", "NativeBatch", Mapping[str, object]]:
        raw = self.clone_real_sham()
        real = tuple(raw[index]["real_state"] for index in range(self.width))
        sham = tuple(raw[index]["sham_state"] for index in range(self.width))
        telemetry_equal = bool(np.all(raw["byte_identical_telemetry"] == 1))
        if not telemetry_equal or not np.array_equal(raw["real_telemetry_sha256"], raw["sham_telemetry_sha256"]):
            raise ProductionBackendError("REAL/SHAM transaction telemetry differs")
        digest = hashlib.sha256(np.ascontiguousarray(raw["real_telemetry_sha256"]).tobytes()).hexdigest()
        return NativeBatch._from_states(real), NativeBatch._from_states(sham), {
            "transaction_telemetry_byte_identical": True, "transaction_telemetry_sha256": digest,
        }

    def select(self, mask: np.ndarray) -> "NativeBatch":
        selected = np.flatnonzero(np.asarray(mask, dtype=bool))
        if selected.size == 0:
            raise ProductionBackendError("native state selection is empty")
        return NativeBatch._from_states(tuple(self._states[int(index)] for index in selected))

    def scripted_actions(self) -> np.ndarray:
        outputs = (_ScriptOutput * self.width)()
        code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_script_batch(self._states, self.width, outputs)
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


def TestNativeBatch(width: int, authority: TestAuthority) -> NativeBatch:
    """Compatibility factory for the exact preactivity-only constructor."""

    return NativeBatch.test_only(width, authority)


def TestProtocolNativeBatch(width: int, authority: TestAuthority) -> NativeBatch:
    """Controlled TEST-only batch that exercises the natural protocol path."""

    authority.require_test_only()
    return NativeBatch(_protocol_test_reset_inputs(width))


def source_factored_test_fixture(
    width: int, authority: TestAuthority,
) -> tuple[NativeBatch, np.ndarray]:
    """Return a native-owned application-boundary fixture for conformance only."""

    authority.require_test_only()
    if width <= 0 or width > 32:
        raise ProductionBackendError("source-factored TEST width differs")
    states = (_State * width)(); rows = (_StepInput * width)()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_source_factored_test_fixture_batch(
        width, states, rows,
    )
    if code:
        raise ProductionBackendError(f"native source-factored fixture rejected batch ({code})")
    batch = NativeBatch._from_states(tuple(states[index] for index in range(width)))
    values = np.frombuffer(rows, dtype=np.dtype(_StepInput), count=width).copy()
    return batch, values


def source_factored_mismatch_test_fixture(
    width: int, mismatch: int, authority: TestAuthority,
) -> tuple[NativeBatch, np.ndarray]:
    """Native-owned invalid linearization fixtures; Python never edits host fields."""

    authority.require_test_only()
    if width <= 0 or width > 32 or mismatch not in tuple(range(1, 25)):
        raise ProductionBackendError("source-factored mismatch TEST fixture differs")
    states = (_State * width)(); rows = (_StepInput * width)()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_source_factored_test_mismatch_fixture_batch(
        mismatch, width, states, rows,
    )
    if code:
        raise ProductionBackendError(f"native source-factored mismatch fixture rejected ({code})")
    return (
        NativeBatch._from_states(tuple(states[index] for index in range(width))),
        np.frombuffer(rows, dtype=np.dtype(_StepInput), count=width).copy(),
    )


def b01_production_test_fixture(width: int, *, origin_valid: bool = True) -> NativeBatch:
    """Fixed TEST fixture whose native state is normal production mode."""

    if width <= 0 or width > 32:
        raise ProductionBackendError("B01 TEST width differs")
    states = (_State * width)(); outputs = (_StepOutput * width)()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_b01_test_fixture_batch(
        int(origin_valid), width, states, outputs,
    )
    if code:
        raise ProductionBackendError(f"native B01 TEST fixture rejected batch ({code})")
    batch = NativeBatch._from_states(tuple(states[index] for index in range(width)))
    for index in range(width):
        batch._outputs[index] = outputs[index]
    return batch


def _test_reset_inputs(width: int, *, test_mode: int = 1) -> tuple[_ResetInput, ...]:
    coordinates = complete_evaluation_coordinates()
    if width <= 0 or width > len(coordinates):
        raise ProductionBackendError("r06 TEST population width differs")
    resets: list[_ResetInput] = []
    authority = TestAuthority()
    for coordinate in coordinates[:width]:
        phase_address = address(
            purpose="K_SCHEDULE", block=coordinate.block, split=coordinate.split,
            regime=coordinate.regime, schedule=coordinate.schedule,
            evaluation_slot=None, field="PHASE_OFFSET", draw_index=0,
        )
        phase_offset = int(coordinate.k_pair[0] * test_uniform(phase_address, authority))
        fixture_key = int.from_bytes(hashlib.sha256(
            TEST_MASTER + b"\0" + coordinate.canonical_key().encode("ascii")
        ).digest()[:8], "big")
        resets.append(_ResetInput(
            fixture_key, (ctypes.c_uint8 * 32).from_buffer_copy(TEST_MASTER),
            test_mode, ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK").index(coordinate.regime),
            coordinate.reflection, coordinate.initial_owner, coordinate.qa_owner,
            coordinate.k_pair[0], coordinate.k_pair[1], coordinate.switch_tick,
            coordinate.tau_d_tick, coordinate.phase(phase_offset), coordinate.route_speed,
            coordinate.turn_magnitude_deg, coordinate.turn_sign,
            coordinate.initial_ux, coordinate.initial_uy, coordinate.block,
            1 if coordinate.split == "CLAIM" else 2,
            ("K4", "K8", "K12", "K4_TO_K12", "K12_TO_K4").index(coordinate.schedule),
            coordinate.evaluation_slot, -1, -1, 0, 0, 1, 0, -1,
        ))
    return tuple(resets)


def _protocol_test_reset_inputs(width: int) -> tuple[_ResetInput, ...]:
    if width <= 0:
        raise ProductionBackendError("protocol TEST width must be positive")
    return _test_reset_inputs(width, test_mode=2)


def recovery_witness_test_rows(width: int, authority: TestAuthority) -> np.ndarray:
    """Exercise retained recovery-witness diagnostics without selecting population."""

    authority.require_test_only()
    resets = _test_reset_inputs(width, test_mode=2)
    reset_array = (_ResetInput * width)(*resets)
    outputs = (_RecoveryWitnessOutput * width)()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_recovery_witness_batch(
        reset_array, width, outputs,
    )
    if code:
        raise ProductionBackendError(f"native recovery witness rejected TEST batch ({code})")
    return np.frombuffer(outputs, dtype=np.dtype(_RecoveryWitnessOutput), count=width).copy()


def native_protocol_audit() -> dict[str, object]:
    output = _ProtocolAuditOutput()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_protocol_audit(ctypes.byref(output))
    if code:
        raise ProductionBackendError(f"native protocol audit failed ({code})")
    return {
        "schema": "DISH_RBHR_R06_NATIVE_PROTOCOL_AUDIT_V1",
        "message_count": int(output.message_count),
        "wire_sizes": list(map(int, output.sizes)),
        "all_integrity_verified": bool(output.all_integrity_verified),
        "all_tamper_rejected": bool(output.all_tamper_rejected),
        "aggregate_sha256": bytes(output.aggregate_sha256).hex(),
        "test_only": True, "question_relevant_output": False,
    }


def native_protocol_transition_probe() -> dict[str, object]:
    output = _ProtocolTransitionOutput()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_protocol_transition_probe(ctypes.byref(output))
    if code:
        raise ProductionBackendError(f"native protocol transition probe failed ({code})")
    return {
        "schema": "DISH_RBHR_R06_NATIVE_PROTOCOL_TRANSITION_PROBE_V1",
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


def flow_local_native_abi_self_audit() -> dict[str, object]:
    """Compile/load r06 only and exercise the nonmutating fork predicate."""

    lib = require_cpp_batched_production_backend()
    batch = TestProtocolNativeBatch(4, TestAuthority())
    rows = empty_step_rows(4)
    flags = batch.first_application_valid(rows)
    labels = batch.passive_labels(rows)
    degraded = _test_reset_inputs(1)[0]
    mask_off = _ResetInput.from_buffer_copy(bytes(degraded)); mask_off.mask_enabled = 0
    paired = NativeBatch((degraded, mask_off)); paired.step(empty_step_rows(2))
    paired_randomness = bool(
        np.array_equal(np.asarray(paired._states[0].wind), np.asarray(paired._states[1].wind))
        and np.array_equal(np.asarray(paired._states[0].pending_source_z), np.asarray(paired._states[1].pending_source_z))
    )
    return {
        "schema": "DISH_RBHR_R06_E1_NATIVE_ABI_FLOW_LOCAL_SELF_AUDIT_V1",
        "abi_version": int(lib.dish_rbhr_r06_prod_abi_version()),
        "source_sha256": source_sha256(),
        "reset_input_bytes": ctypes.sizeof(_ResetInput),
        "step_input_bytes": ctypes.sizeof(_StepInput),
        "state_bytes": ctypes.sizeof(_State),
        "step_output_bytes": ctypes.sizeof(_StepOutput),
        "first_application_predicate_callable": flags.shape == (4,),
        "fixture_has_no_application": not bool(np.any(flags)),
        "passive_target_shape": list(labels["target"].shape),
        "passive_link_shape": list(labels["links"].shape),
        "passive_q_shape": list(labels["q_labels"].shape),
        "passive_label_shapes_exact": (
            labels["target"].shape == (4, 4) and labels["links"].shape == (4, 4, 2)
            and labels["missing"].shape == (4, 4) and labels["q_labels"].shape == (4, 20)
        ),
        "mask_on_off_pair_shared_randomness": paired_randomness,
        "test_only": True, "scientific_master": False, "identity": False,
        "coordinate": False, "tape": False, "activity": False,
        "question_relevant_output": False,
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
        "schema": "DISH_RBHR_R06_NATIVE_NATURAL_PROTOCOL_TRACE_V1",
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


def rng_words_native(master_value: bytes, addresses: tuple[str, ...]) -> tuple[int, ...]:
    if not addresses:
        raise ProductionBackendError("RNG request must be nonempty")
    raw_master = bytes(master_value)
    if len(raw_master) != 32:
        raise ProductionBackendError("native RNG master must be exactly 256 bits")
    encoded = tuple(address.encode("utf-8") for address in addresses)
    if any(not value.startswith(b"DISH/RBHR/R06/") or len(value) > 4096 for value in encoded):
        raise ProductionBackendError("RNG address is outside the frozen r06 namespace")
    offsets: list[int] = []; cursor = 0
    for value in encoded:
        offsets.append(cursor); cursor += len(value)
    blob = b"".join(encoded)
    master = (ctypes.c_uint8 * 32).from_buffer_copy(raw_master)
    offset_values = (ctypes.c_uint64 * len(encoded))(*offsets)
    lengths = (ctypes.c_uint64 * len(encoded))(*(len(value) for value in encoded))
    outputs = (ctypes.c_uint64 * len(encoded))()
    code = require_cpp_batched_production_backend().dish_rbhr_r06_prod_rng_words_batch(
        master, blob, offset_values, lengths, len(encoded), outputs
    )
    if code:
        raise ProductionBackendError(f"native RNG rejected addresses ({code})")
    return tuple(map(int, outputs))


def rng_words_test_native(addresses: tuple[str, ...], authority: TestAuthority) -> tuple[int, ...]:
    authority.require_test_only()
    return rng_words_native(TEST_MASTER, addresses)


def native_batch_from_rows(rows: tuple[Mapping[str, object], ...], *, library=None) -> NativeBatch:
    if not rows:
        raise R06ContractError("native production reset rows are empty")
    scalar_names = [name for name, _ in _ResetInput._fields_ if name != "master"]
    resets = []
    for row in rows:
        try:
            values = [int(row[name]) for name in scalar_names]
            raw_master = row["master"]
            master = bytes.fromhex(raw_master) if isinstance(raw_master, str) else bytes(raw_master)
        except (KeyError, TypeError, ValueError) as error:
            raise R06ContractError("native reset row schema differs") from error
        if len(master) != 32 or values[1] != 0:
            raise R06ContractError("native reset row is not production mode")
        resets.append(_ResetInput(values[0], (ctypes.c_uint8 * 32).from_buffer_copy(master), *values[1:]))
    return NativeBatch(tuple(resets), library=library)


def open_production_batch(*, authority: object | None, width: int) -> NativeBatch:
    require = getattr(authority, "require_active", None)
    if not callable(require):
        refuse_activity(authority)
    require()
    if getattr(authority, "component", None) != COMPONENT:
        raise R06ContractError("Root lease component differs")
    reset_rows = getattr(authority, "native_reset_rows", None)
    if not callable(reset_rows):
        raise R06ContractError("lease lacks nonfixture native reset rows")
    raw_rows = tuple(reset_rows(width=width))
    if len(raw_rows) != width:
        raise R06ContractError("lease reset row count differs")
    return native_batch_from_rows(raw_rows)


__all__ = [
    "TEST_NAMESPACE", "B01PreparedBatch", "NativeBatch", "ProductionBackendError", "TestNativeBatch", "TestProtocolNativeBatch",
    "artifact_identity", "b01_production_test_fixture", "empty_step_rows", "flow_local_native_abi_self_audit", "native_batch_from_rows", "native_natural_protocol_trace", "native_protocol_audit", "native_protocol_transition_probe", "open_production_batch", "rng_words_native", "rng_words_test_native",
    "recovery_witness_test_rows", "require_cpp_batched_production_backend", "source_sha256",
]

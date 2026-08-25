"""FOLR A1: deterministic S03-payload to first-kernel mediation probe.

This direction-local module deliberately bypasses the historical eight-arm
FOLR executor.  It binds one registered cell, captures one common pre-write
snapshot, and obtains exactly the six kernels frozen by the A1 brief.  Branch
identity is artifact provenance only; the runtime sees neither a branch label
nor a branch-conditioned history.

The load-bearing execution device is :class:`FirstKernelComplete`.  The sink
delegates the target's complete masked-logit/softmax capture to the existing
``KernelCaptureSink`` and immediately raises the sentinel.  Consequently the
authoritative transaction has committed and the terminal S03 hook has run,
but action selection, action RNG, opportunity RNG, token ledgers, and every
later owner forward remain unreachable.
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from ha_ctse_process.variable_roster_event_types import MembershipTransaction

from experiments.candidates.folr_core import branch_snapshot as bs
from experiments.candidates.folr_core import registration as reg
from experiments.candidates.folr_core import reset_manifest as rm
from experiments.candidates.folr_core import s03_binding as sb

RAW_OUTPUT_BINDING = "folr_core.s03_payload_kernel_mediation.v1"
REGISTERED_CELL_IDENTIFIER = "folr_s03_constructed_sensitivity_v1"
REGISTERED_TARGET = ("owner_t", 0)
REGISTERED_SHADOW = ("owner_q", 0)
HORIZON = 1
K_SEARCH = 1

K_B0_P0 = "K_(0<-0)"
K_B0_P1 = "K_(0<-1)"
K_B1_P0 = "K_(1<-0)"
K_B1_P1 = "K_(1<-1)"
K_RESET_0 = "K_reset_0"
K_RESET_1 = "K_reset_1"

ARM_SPECS: tuple[tuple[str, int, str | None, bool], ...] = (
    (K_B0_P0, 0, sb.PAYLOAD_ZERO, False),
    (K_B0_P1, 0, sb.PAYLOAD_ONE, False),
    (K_B1_P0, 1, sb.PAYLOAD_ZERO, False),
    (K_B1_P1, 1, sb.PAYLOAD_ONE, False),
    (K_RESET_0, 0, None, True),
    (K_RESET_1, 1, None, True),
)
ARM_NAMES = tuple(spec[0] for spec in ARM_SPECS)

PREREQUISITE_UNAVAILABLE_OR_INVALID = "PREREQUISITE_UNAVAILABLE_OR_INVALID"
BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE = "BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE"
RESET_DOES_NOT_ERASE = "RESET_DOES_NOT_ERASE"
NO_S03_PAYLOAD_EFFECT = "NO_S03_PAYLOAD_EFFECT"
S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED = "S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED"
DECISIONS = (
    PREREQUISITE_UNAVAILABLE_OR_INVALID,
    BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE,
    RESET_DOES_NOT_ERASE,
    NO_S03_PAYLOAD_EFFECT,
    S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED,
)

FULL_ACTIVITY_COUNTS = {
    "cells": 1,
    "complete_kernel_readouts": 6,
    "policy_forwards": 6,
    "lifecycle_transactions_started": 6,
    "environment_episodes": 0,
    "environment_transitions": 0,
    "hypothetical_transitions": 0,
    "learner_calls": 0,
    "trainer_calls": 0,
    "optimizer_updates": 0,
    "return_evaluations": 0,
}
ZERO_ACTIVITY_COUNTS = {
    "cells": 0,
    "complete_kernel_readouts": 0,
    "policy_forwards": 0,
    "lifecycle_transactions_started": 0,
    "environment_episodes": 0,
    "environment_transitions": 0,
    "hypothetical_transitions": 0,
    "learner_calls": 0,
    "trainer_calls": 0,
    "optimizer_updates": 0,
    "return_evaluations": 0,
}


class PrerequisiteInvalid(RuntimeError):
    """Raised before any kernel observation when the exact cell cannot bind."""

    def __init__(self, message: str, *, checks: Mapping[str, bool] | None = None) -> None:
        super().__init__(message)
        self.checks = dict(checks or {})


class FirstKernelComplete(BaseException):
    """Exact control-flow sentinel raised after one complete target kernel."""

    def __init__(self, sink: "SentinelKernelCaptureSink") -> None:
        super().__init__("the first complete target kernel has been captured")
        self.sink = sink


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_repo_root(),
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise PrerequisiteInvalid("source commit identity is unavailable") from exc


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _array_record(value: Any) -> dict[str, Any]:
    array = np.asarray(value, dtype=np.float32)
    little = np.ascontiguousarray(array.astype(np.dtype("<f4"), copy=False))
    payload = little.tobytes(order="C")
    return {
        "dtype": "float32",
        "byte_order": "little-endian",
        "shape": list(little.shape),
        "values": little.tolist(),
        "bytes_base64": base64.b64encode(payload).decode("ascii"),
        "bytes_sha256": _sha256_bytes(payload),
        "typed_vector_sha256": sb.vector_digest(little),
    }


def _decode_array(record: Mapping[str, Any]) -> np.ndarray:
    if record.get("dtype") != "float32" or record.get("byte_order") != "little-endian":
        raise ValueError("kernel array is not complete little-endian float32")
    shape = tuple(int(value) for value in record.get("shape", ()))
    raw = base64.b64decode(str(record.get("bytes_base64", "")), validate=True)
    if _sha256_bytes(raw) != record.get("bytes_sha256"):
        raise ValueError("kernel array byte digest mismatch")
    array = np.frombuffer(raw, dtype=np.dtype("<f4")).reshape(shape).copy()
    if sb.vector_digest(array) != record.get("typed_vector_sha256"):
        raise ValueError("kernel array typed digest mismatch")
    values = np.asarray(record.get("values"), dtype=np.float32)
    if values.shape != array.shape or values.tobytes() != array.tobytes():
        raise ValueError("kernel array values do not losslessly match its bytes")
    return array


def _rng_record(core: Any) -> dict[str, Any]:
    return {
        name: deepcopy(getattr(core, name).bit_generator.state)
        for name in bs.RNG_FIELDS
    }


def _rng_digests(states: Mapping[str, Any]) -> dict[str, str]:
    return {name: bs.digest_of(state) for name, state in states.items()}


def _lineage_record(core: Any) -> dict[str, Any]:
    return {
        key: {
            "status": record.status,
            "membership_epoch": int(record.membership_epoch),
            "policy_version": int(record.policy_version),
            "is_genuine_join": bool(record.is_genuine_join),
            "is_rejoin": bool(record.is_rejoin),
        }
        for key, record in sorted(core.records.items())
    }


def _clock_record(core: Any) -> dict[str, int]:
    return {
        "physical_time": int(core.physical_time),
        "policy_version": int(core.policy_version),
    }


def _ledger_record(core: Any) -> dict[str, int]:
    return {
        "high_ledger": len(core.high_ledger),
        "closed_event_rows": len(core.closed_event_rows),
        "low_ledger": len(core.low_ledger),
        "low_chunk_boundaries": len(core.low_chunk_boundaries),
    }


def _transaction(manifest: rm.ResetManifest, *, physical_time: int) -> MembershipTransaction:
    pre = rm.boundary_snapshot(manifest, physical_time=physical_time, frontier=())
    post = rm.boundary_snapshot(
        manifest,
        physical_time=physical_time,
        frontier=tuple(manifest.frontier),
    )
    return MembershipTransaction(pre, (), post)


@dataclass
class HookWitness:
    target_lifecycle_key: str
    payload_slot: str | None
    expected_payload: np.ndarray
    calls: int = 0
    before_digest: str | None = None
    after_digest: str | None = None
    clock: dict[str, int] | None = None
    lineage_digest: str | None = None

    def __call__(self, core: Any) -> None:
        self.calls += 1
        if self.calls != 1:
            raise RuntimeError("the S03 intervention hook ran more than once")
        target = core.records[self.target_lifecycle_key]
        self.before_digest = sb.vector_digest(target.high_hidden)
        target.high_hidden = np.asarray(self.expected_payload, dtype=np.float32).copy()
        self.after_digest = sb.vector_digest(target.high_hidden)
        self.clock = _clock_record(core)
        self.lineage_digest = bs.digest_of(_lineage_record(core))


class SentinelKernelCaptureSink(sb.KernelCaptureSink):
    """Capture exactly one full target kernel and terminate the arm."""

    def __init__(self, *, core: Any, expected_payload: np.ndarray, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.core = core
        self.expected_payload = np.asarray(expected_payload, dtype=np.float32).copy()
        self.capture_calls = 0
        self.observed_payload_digest: str | None = None
        self.capture_clock: dict[str, int] | None = None
        self.capture_lineage_digest: str | None = None

    def capture(self, **kwargs: Any) -> sb.DirectKernel | None:
        before = len(self.captures)
        kernel = super().capture(**kwargs)
        if kernel is None:
            return None
        self.capture_calls += 1
        if self.capture_calls != 1 or len(self.captures) != before + 1:
            raise RuntimeError("target kernel capture cardinality exceeded one")
        payload = np.asarray(kwargs["preimage"]["pre_token_high_hidden"], dtype=np.float32)
        if payload.tobytes() != self.expected_payload.tobytes():
            raise RuntimeError("the target readout did not receive the intended S03 payload")
        self.observed_payload_digest = sb.vector_digest(payload)
        self.capture_clock = _clock_record(self.core)
        self.capture_lineage_digest = bs.digest_of(_lineage_record(self.core))
        raise FirstKernelComplete(self)


def _positive_registered_witness(registration: reg.Registration) -> bool:
    column = registration.weight_witness["skill_head_focal_column"]
    return (
        list(column) == [1.0, -1.0, 0.0]
        and float(registration.analytic_logit_separation) > 0.0
        and bool(
            registration.weight_witness["focal_gru_output"][
                "replication_matches_the_executed_cell"
            ]
        )
    )


def _admit_registration(
    registration: reg.Registration,
    *,
    source_commit: str,
    technical_only: bool,
) -> dict[str, Any]:
    expected_identifier = (
        registration.cell_identifier if technical_only else REGISTERED_CELL_IDENTIFIER
    )
    expected_target = (
        registration.binding.target_lifecycle_key,
        int(registration.binding.target_membership_epoch),
    )
    expected_shadow = (
        registration.binding.shadow_lifecycle_key,
        int(registration.binding.shadow_membership_epoch),
    )
    current_identity = reg.actor_path_source_identity()
    checks = {
        "cell_identifier_exact": registration.cell_identifier == expected_identifier,
        "development_mode_matches": bool(registration.development_only) == bool(technical_only),
        "registered_target_exact": technical_only or expected_target == REGISTERED_TARGET,
        "registered_shadow_exact": technical_only or expected_shadow == REGISTERED_SHADOW,
        "binding_target_matches_manifest": (
            registration.binding.target_lifecycle_key
            == registration.manifest.target_lifecycle_key
        ),
        "binding_epoch_matches_manifest": (
            int(registration.binding.target_membership_epoch)
            == int(registration.manifest.owner(registration.binding.target_lifecycle_key).membership_epoch)
        ),
        "positive_weight_witness": _positive_registered_witness(registration),
        "legal_action_vector_complete": (
            tuple(registration.manifest.legal_action_support.shape)
            == (int(registration.manifest.architecture["n_skills"]),)
        ),
        "at_least_two_legal_actions": int(np.count_nonzero(registration.manifest.legal_action_support)) >= 2,
        "all_registered_actions_legal": bool(np.all(registration.manifest.legal_action_support)),
        "target_first_teacher_order": (
            tuple(registration.manifest.target_token_order)[0]
            == registration.binding.target_lifecycle_key
        ),
        "teacher_actions_cover_frontier": set(registration.teacher_actions)
        == set(registration.manifest.frontier),
        "model_digest_matches_weight_witness": (
            sb.model_state_digest(rm.construct_reset_runtime(registration.manifest).commitment_model)
            == registration.weight_witness["model_state_digest"]
        ),
        "scientific_graph_identity_matches_registration": (
            current_identity["scientific_graph_fingerprint"]
            == registration.source_identity["scientific_graph_fingerprint"]
            and current_identity["torch_version"] == registration.source_identity["torch_version"]
            and current_identity["numpy_version"] == registration.source_identity["numpy_version"]
        ),
        "source_commit_matches_head": technical_only or source_commit == _git_head(),
    }
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise PrerequisiteInvalid(
            "registration admission failed: " + ", ".join(failed),
            checks=checks,
        )
    return {
        "checks": checks,
        "cell_identifier": registration.cell_identifier,
        "registration_digest": registration.registration_digest(),
        "binding_manifest_digest": registration.binding.manifest_digest(),
        "reset_manifest_digest": registration.manifest.digest(),
        "target": list(expected_target),
        "shadow": list(expected_shadow),
        "frontier": list(registration.manifest.frontier),
        "target_token_order": list(registration.manifest.target_token_order),
        "legal_action_support": registration.manifest.legal_action_support.tolist(),
        "analytic_logit_separation": float(registration.analytic_logit_separation),
        "skill_head_focal_column": list(registration.weight_witness["skill_head_focal_column"]),
        "model_state_digest": registration.weight_witness["model_state_digest"],
        "source_identity": current_identity,
    }


def _run_arm(
    registration: reg.Registration,
    *,
    common_snapshot: bs.CoreSnapshot,
    name: str,
    source_branch: int,
    payload_slot: str | None,
    reset: bool,
) -> dict[str, Any]:
    manifest = registration.manifest
    source = rm.construct_reset_runtime(manifest)
    bs.restore(source, common_snapshot)
    source_snapshot_digest = bs.capture(source).digest()

    if reset:
        core = rm.construct_reset_runtime(manifest)
        payload = registration.binding.payload(sb.PAYLOAD_NEUTRAL)
        hook: HookWitness | None = None
    else:
        core = rm.construct_reset_runtime(manifest)
        bs.restore(core, common_snapshot)
        payload = registration.binding.payload(str(payload_slot))
        hook = HookWitness(
            target_lifecycle_key=registration.binding.target_lifecycle_key,
            payload_slot=payload_slot,
            expected_payload=payload,
        )
        core.install_preframe_intervention(hook)

    runtime_snapshot_digest = bs.capture(core).digest()
    model_before = sb.model_state_digest(core.commitment_model)
    rng_before = _rng_record(core)
    ledgers_before = _ledger_record(core)
    lineage_before = _lineage_record(core)
    clock_before = _clock_record(core)
    pending_before = core.pending_membership_transaction is not None
    target = registration.binding.target_lifecycle_key
    target_before = core.records[target]
    target_before_record = {
        "owner_lifecycle_key": target,
        "membership_epoch": int(target_before.membership_epoch),
        "status": target_before.status,
        "high_hidden_digest": sb.vector_digest(target_before.high_hidden),
    }

    sink = SentinelKernelCaptureSink(
        core=core,
        expected_payload=payload,
        binding=registration.binding,
        model_digest=model_before,
        snapshot_digest=source_snapshot_digest,
        target_only=True,
    )
    core.install_kernel_capture(sink)
    sentinel_caught = False
    try:
        core.apply_transaction(
            _transaction(manifest, physical_time=int(core.physical_time)),
            teacher_order=tuple(manifest.target_token_order),
            teacher_actions=dict(registration.teacher_actions),
        )
    except FirstKernelComplete as signal:
        if signal.sink is not sink:
            raise RuntimeError("a foreign first-kernel sentinel crossed the arm")
        sentinel_caught = True
    if not sentinel_caught:
        raise RuntimeError("the authoritative transaction returned without the first-kernel sentinel")

    kernel = sink.first()
    rng_after = _rng_record(core)
    ledgers_after = _ledger_record(core)
    lineage_after = _lineage_record(core)
    clock_after = _clock_record(core)
    model_after = sb.model_state_digest(core.commitment_model)
    target_after = core.records[target]
    exact_payload_digest = sb.vector_digest(payload)
    legal = np.asarray(manifest.legal_action_support, dtype=np.bool_)
    runtime_attribute_names = tuple(sorted(vars(core)))
    forbidden_runtime_branch_attrs = tuple(
        value
        for value in runtime_attribute_names
        if "branch" in value.lower() or "source_identity" in value.lower()
    )

    return {
        "name": name,
        "arm_kind": "complete_reset" if reset else "target_s03_transplant",
        "source_branch_identity": int(source_branch),
        "source_branch_identity_role": "artifact_provenance_only",
        "payload_slot": sb.PAYLOAD_NEUTRAL if reset else payload_slot,
        "common_source_snapshot_digest": source_snapshot_digest,
        "runtime_prewrite_snapshot_digest": runtime_snapshot_digest,
        "intervention_digest": bs.digest_of(
            {
                "target": [target, int(registration.binding.target_membership_epoch)],
                "payload_slot": sb.PAYLOAD_NEUTRAL if reset else payload_slot,
                "payload_digest": exact_payload_digest,
                "kind": "complete_reset" if reset else "terminal_s03_write",
            }
        ),
        "kernel": {
            "owner_lifecycle_key": kernel.owner_lifecycle_key,
            "membership_epoch": int(kernel.membership_epoch),
            "token_position": int(kernel.token_position),
            "masked_logits": _array_record(kernel.masked_logits),
            "probabilities": _array_record(kernel.probabilities),
            "actor_preimage_digest_excluding_only_s03": kernel.actor_preimage_digest,
            "model_state_digest": kernel.model_state_digest,
            "common_snapshot_digest": kernel.common_snapshot_digest,
            "binding_manifest_digest": kernel.intervention_manifest_digest,
        },
        "witnesses": {
            "sentinel_caught": sentinel_caught,
            "kernel_capture_count": int(sink.capture_calls),
            "kernel_producing_policy_forwards": int(sink.capture_calls),
            "target_payload_digest_at_capture": sink.observed_payload_digest,
            "expected_target_payload_digest": exact_payload_digest,
            "complete_legal_mask": legal.tolist(),
            "complete_probability_vector": (
                tuple(kernel.probabilities.shape) == tuple(legal.shape)
                and bool(np.all(np.isfinite(kernel.probabilities)))
                and bool(np.all(kernel.probabilities[~legal] == 0.0))
                and bool(np.isclose(float(np.sum(kernel.probabilities, dtype=np.float64)), 1.0, rtol=0.0, atol=1e-6))
            ),
            "target_before": target_before_record,
            "target_after_capture": {
                "owner_lifecycle_key": target,
                "membership_epoch": int(target_after.membership_epoch),
                "status": target_after.status,
                "high_hidden_digest": sb.vector_digest(target_after.high_hidden),
            },
            "clock_before": clock_before,
            "clock_at_hook": None if hook is None else hook.clock,
            "clock_at_capture": sink.capture_clock,
            "clock_after_capture": clock_after,
            "lineage_digest_before": bs.digest_of(lineage_before),
            "lineage_digest_at_hook": None if hook is None else hook.lineage_digest,
            "lineage_digest_at_capture": sink.capture_lineage_digest,
            "lineage_digest_after_capture": bs.digest_of(lineage_after),
            "hook_calls": 0 if hook is None else int(hook.calls),
            "hook_timing": (
                "complete_reset_neutral_no_hook"
                if hook is None
                else "after_membership_trial_commit_before_first_target_logits"
            ),
            "hook_before_payload_digest": None if hook is None else hook.before_digest,
            "hook_after_payload_digest": None if hook is None else hook.after_digest,
            "rng_state_digests_before": _rng_digests(rng_before),
            "rng_state_digests_after": _rng_digests(rng_after),
            "rng_states_unchanged": _rng_digests(rng_before) == _rng_digests(rng_after),
            "ledgers_before": ledgers_before,
            "ledgers_after": ledgers_after,
            "ledgers_unchanged": ledgers_before == ledgers_after,
            "pending_membership_transaction_before": pending_before,
            "pending_membership_transaction_after": core.pending_membership_transaction is not None,
            "action_selection_reached": False,
            "cached_action_or_kernel_crossing": False,
            "slot_local_buffer_crossing": False,
            "forbidden_branch_runtime_attributes": list(forbidden_runtime_branch_attrs),
            "branch_identity_injected_into_runtime": bool(forbidden_runtime_branch_attrs),
            "model_state_digest_before": model_before,
            "model_state_digest_after": model_after,
            "model_parameters_unchanged": model_before == model_after,
            "reset_target_neutral": (not reset) or exact_payload_digest == sb.vector_digest(registration.binding.payload(sb.PAYLOAD_NEUTRAL)),
        },
    }


def total_variation(left: Sequence[float], right: Sequence[float]) -> float:
    """Exact requested statistic over the complete probability vectors."""
    a = np.asarray(left, dtype=np.float32)
    b = np.asarray(right, dtype=np.float32)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("TV requires two complete probability vectors of one shape")
    return float(0.5 * np.sum(np.abs(a.astype(np.float64) - b.astype(np.float64))))


def classify(
    *,
    prerequisite_valid: bool,
    completed_admission_valid: bool,
    fixed_payload_nulls: Sequence[float],
    within_branch_payload_tvs: Sequence[float],
    reset_tv: float,
) -> str:
    """Frozen precedence, with no epsilon or materiality threshold."""
    if not prerequisite_valid:
        return PREREQUISITE_UNAVAILABLE_OR_INVALID
    if not completed_admission_valid or any(float(value) != 0.0 for value in fixed_payload_nulls):
        return BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE
    if float(reset_tv) != 0.0:
        return RESET_DOES_NOT_ERASE
    if all(float(value) == 0.0 for value in within_branch_payload_tvs):
        return NO_S03_PAYLOAD_EFFECT
    return S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED


def _completed_admission(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    witnesses = [arm["witnesses"] for arm in arms.values()]
    actor_preimages = {
        arm["kernel"]["actor_preimage_digest_excluding_only_s03"]
        for arm in arms.values()
    }
    common_snapshots = {arm["common_source_snapshot_digest"] for arm in arms.values()}
    model_digests = {arm["kernel"]["model_state_digest"] for arm in arms.values()}
    legal_masks = {tuple(arm["witnesses"]["complete_legal_mask"]) for arm in arms.values()}
    clocks = {
        json.dumps(arm["witnesses"]["clock_at_capture"], sort_keys=True)
        for arm in arms.values()
    }
    lineages = {arm["witnesses"]["lineage_digest_at_capture"] for arm in arms.values()}
    checks = {
        "exact_arm_roster": tuple(arms) == ARM_NAMES,
        "one_common_source_snapshot": len(common_snapshots) == 1,
        "one_model_state": len(model_digests) == 1,
        "one_non_s03_actor_preimage": len(actor_preimages) == 1,
        "one_legal_mask": len(legal_masks) == 1,
        "one_capture_clock": len(clocks) == 1,
        "one_capture_lineage": len(lineages) == 1,
        "all_target_first": all(arm["kernel"]["token_position"] == 0 for arm in arms.values()),
        "all_owner_epoch_exact": all(
            arm["kernel"]["owner_lifecycle_key"] == next(iter(arms.values()))["kernel"]["owner_lifecycle_key"]
            and arm["kernel"]["membership_epoch"] == next(iter(arms.values()))["kernel"]["membership_epoch"]
            for arm in arms.values()
        ),
        "all_complete_vectors": all(w["complete_probability_vector"] for w in witnesses),
        "all_single_forward": all(w["kernel_capture_count"] == 1 and w["kernel_producing_policy_forwards"] == 1 for w in witnesses),
        "all_sentinels_exact": all(w["sentinel_caught"] for w in witnesses),
        "all_payloads_exact": all(w["target_payload_digest_at_capture"] == w["expected_target_payload_digest"] for w in witnesses),
        "all_rng_unchanged": all(w["rng_states_unchanged"] for w in witnesses),
        "all_ledgers_unchanged": all(w["ledgers_unchanged"] for w in witnesses),
        "all_pending_absent": all(not w["pending_membership_transaction_before"] and not w["pending_membership_transaction_after"] for w in witnesses),
        "no_action_selection": all(not w["action_selection_reached"] for w in witnesses),
        "no_cached_path": all(not w["cached_action_or_kernel_crossing"] and not w["slot_local_buffer_crossing"] for w in witnesses),
        "branch_metadata_not_in_runtime": all(not w["branch_identity_injected_into_runtime"] for w in witnesses),
        "all_models_unchanged": all(w["model_parameters_unchanged"] for w in witnesses),
        "reset_neutral": all(arms[name]["witnesses"]["reset_target_neutral"] for name in (K_RESET_0, K_RESET_1)),
        "transplant_hook_once": all(arms[name]["witnesses"]["hook_calls"] == 1 for name in ARM_NAMES[:4]),
        "reset_hook_absent": all(arms[name]["witnesses"]["hook_calls"] == 0 for name in (K_RESET_0, K_RESET_1)),
    }
    return {"checks": checks, "all_pass": all(checks.values())}


def _zero_prerequisite_analysis(artifact: Mapping[str, Any]) -> dict[str, Any]:
    admission = artifact.get("prerequisite_admission", {})
    if admission.get("all_pass") is not False:
        raise ValueError("zero-arm artifact requires failed prerequisite admission")
    if not str(admission.get("error", "")).strip():
        raise ValueError("zero-arm prerequisite artifact omits its failure reason")
    identity = admission.get("identity", {})
    required_identity = {
        "cell_identifier",
        "registration_digest",
        "binding_manifest_digest",
        "reset_manifest_digest",
        "target",
        "shadow",
        "frontier",
        "legal_action_support",
        "model_state_digest",
        "source_identity",
    }
    if set(identity) != required_identity:
        raise ValueError("zero-arm prerequisite artifact omits exact cell/config identity")
    if artifact.get("scientific_activity_counts") != ZERO_ACTIVITY_COUNTS:
        raise ValueError("zero-arm prerequisite artifact has nonzero or incomplete activity")
    return {
        "completed_admission": {
            "checks": {},
            "all_pass": False,
            "not_applicable_before_readout": True,
        },
        "contrasts": {
            "formula": "0.5*sum(abs(p-q)) over complete float32 probability vectors",
            "fixed_payload_nulls": None,
            "within_branch_payload": None,
            "reset": None,
            "not_applicable_before_readout": True,
        },
        "decision": PREREQUISITE_UNAVAILABLE_OR_INVALID,
        "decision_precedence": list(DECISIONS),
        "no_materiality_threshold_or_epsilon": True,
        "sample_or_monte_carlo_used": False,
    }


def analyze_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    arms = artifact.get("arms", {})
    if not arms:
        return _zero_prerequisite_analysis(artifact)
    if tuple(arms) != ARM_NAMES:
        raise ValueError("artifact must contain the exact ordered six-arm roster")
    if artifact.get("prerequisite_admission", {}).get("all_pass") is not True:
        raise ValueError("a failed prerequisite must stop before every arm")
    probabilities = {
        name: _decode_array(arms[name]["kernel"]["probabilities"])
        for name in ARM_NAMES
    }
    contrasts = {
        "formula": "0.5*sum(abs(p-q)) over complete float32 probability vectors",
        "fixed_payload_nulls": {
            "payload_0": total_variation(probabilities[K_B0_P0], probabilities[K_B1_P0]),
            "payload_1": total_variation(probabilities[K_B0_P1], probabilities[K_B1_P1]),
        },
        "within_branch_payload": {
            "branch_0": total_variation(probabilities[K_B0_P0], probabilities[K_B0_P1]),
            "branch_1": total_variation(probabilities[K_B1_P0], probabilities[K_B1_P1]),
        },
        "reset": total_variation(probabilities[K_RESET_0], probabilities[K_RESET_1]),
    }
    completed = _completed_admission(arms)
    decision = classify(
        prerequisite_valid=bool(artifact.get("prerequisite_admission", {}).get("all_pass")),
        completed_admission_valid=bool(completed["all_pass"]),
        fixed_payload_nulls=tuple(contrasts["fixed_payload_nulls"].values()),
        within_branch_payload_tvs=tuple(contrasts["within_branch_payload"].values()),
        reset_tv=float(contrasts["reset"]),
    )
    return {
        "completed_admission": completed,
        "contrasts": contrasts,
        "decision": decision,
        "decision_precedence": list(DECISIONS),
        "no_materiality_threshold_or_epsilon": True,
        "sample_or_monte_carlo_used": False,
    }


def validate_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    if artifact.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("unexpected FOLR A1 raw output binding")
    arms = artifact.get("arms", {})
    if not arms:
        recomputed = analyze_artifact(artifact)
        if artifact.get("analysis") != recomputed:
            raise ValueError("stored prerequisite analysis is not canonical")
        if artifact.get("decision") != PREREQUISITE_UNAVAILABLE_OR_INVALID:
            raise ValueError("zero-arm artifact must use the prerequisite terminal")
        if bool(artifact.get("scientific_terminal_admitted")) == bool(
            artifact.get("technical_only")
        ):
            raise ValueError("technical-only/scientific-terminal admission flags disagree")
        return {
            "valid": True,
            "decision": PREREQUISITE_UNAVAILABLE_OR_INVALID,
            "arm_count": 0,
            "policy_forwards": 0,
            "environment_transitions": 0,
        }
    if tuple(arms) != ARM_NAMES or len(set(arms)) != 6:
        raise ValueError("not exactly the frozen six distinct arms")
    for name in ARM_NAMES:
        logits = _decode_array(arms[name]["kernel"]["masked_logits"])
        probabilities = _decode_array(arms[name]["kernel"]["probabilities"])
        legal = np.asarray(arms[name]["witnesses"]["complete_legal_mask"], dtype=np.bool_)
        if logits.ndim != 1 or probabilities.ndim != 1 or logits.shape != legal.shape or probabilities.shape != legal.shape:
            raise ValueError(f"{name} does not contain one complete legal-action kernel")
    if artifact.get("scientific_activity_counts") != FULL_ACTIVITY_COUNTS:
        raise ValueError("scientific activity counts violate the frozen cap")
    recomputed = analyze_artifact(artifact)
    if artifact.get("analysis") != recomputed:
        raise ValueError("stored TV/admission/decision analysis is not canonical")
    structural = recomputed["completed_admission"]["checks"]
    for name in ("exact_arm_roster", "all_complete_vectors", "all_single_forward", "all_sentinels_exact"):
        if not structural[name]:
            raise ValueError(f"completed six-arm artifact violates structural invariant {name}")
    if artifact.get("decision") != recomputed["decision"]:
        raise ValueError("stored decision does not follow frozen precedence")
    if bool(artifact.get("scientific_terminal_admitted")) == bool(artifact.get("technical_only")):
        raise ValueError("technical-only/scientific-terminal admission flags disagree")
    return {
        "valid": True,
        "decision": recomputed["decision"],
        "arm_count": 6,
        "policy_forwards": 6,
        "environment_transitions": 0,
        "completed_admission_supported": recomputed["completed_admission"]["all_pass"],
    }


def _prerequisite_identity(registration: reg.Registration) -> dict[str, Any]:
    """Cell/config identity retained even when admission stops before readout."""
    return {
        "cell_identifier": registration.cell_identifier,
        "registration_digest": registration.registration_digest(),
        "binding_manifest_digest": registration.binding.manifest_digest(),
        "reset_manifest_digest": registration.manifest.digest(),
        "target": [
            registration.binding.target_lifecycle_key,
            int(registration.binding.target_membership_epoch),
        ],
        "shadow": [
            registration.binding.shadow_lifecycle_key,
            int(registration.binding.shadow_membership_epoch),
        ],
        "frontier": list(registration.manifest.frontier),
        "legal_action_support": registration.manifest.legal_action_support.tolist(),
        "model_state_digest": registration.weight_witness["model_state_digest"],
        "source_identity": dict(registration.source_identity),
    }


def run_probe(
    *,
    registration: reg.Registration,
    source_commit: str,
    run_id: str,
    technical_only: bool,
) -> dict[str, Any]:
    """Execute the exact six constant-size deterministic kernel readouts."""
    try:
        admission = _admit_registration(
            registration,
            source_commit=str(source_commit),
            technical_only=bool(technical_only),
        )
    except PrerequisiteInvalid as exc:
        failed: dict[str, Any] = {
            "raw_output_binding": RAW_OUTPUT_BINDING,
            "direction": "CAND-VAP-FOLR-CORE@constructive-revision-v6",
            "assignment": "FOLR-A1-S03-PAYLOAD-KERNEL-MEDIATION",
            "source_commit": str(source_commit),
            "run_id": str(run_id),
            "technical_only": bool(technical_only),
            "scientific_terminal_admitted": not bool(technical_only),
            "probe_boundary": {
                "horizon": HORIZON,
                "k_search": K_SEARCH,
                "one_exact_cell": registration.cell_identifier,
                "branch_identity_is_provenance_metadata_only": True,
                "environment_or_trajectory_executed": False,
            },
            "prerequisite_admission": {
                "all_pass": False,
                "checks": dict(exc.checks),
                "failed_checks": sorted(
                    name for name, passed in exc.checks.items() if not passed
                ),
                "error": str(exc),
                "identity": _prerequisite_identity(registration),
            },
            "arms": {},
            "scientific_activity_counts": dict(ZERO_ACTIVITY_COUNTS),
            "decision": PREREQUISITE_UNAVAILABLE_OR_INVALID,
        }
        failed["analysis"] = analyze_artifact(failed)
        validate_artifact(failed)
        return failed

    origin = rm.construct_reset_runtime(registration.manifest)
    common_snapshot = bs.capture(origin)
    common_digest = common_snapshot.digest()
    arms = {
        name: _run_arm(
            registration,
            common_snapshot=common_snapshot,
            name=name,
            source_branch=source_branch,
            payload_slot=payload_slot,
            reset=reset,
        )
        for name, source_branch, payload_slot, reset in ARM_SPECS
    }
    artifact: dict[str, Any] = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "direction": "CAND-VAP-FOLR-CORE@constructive-revision-v6",
        "assignment": "FOLR-A1-S03-PAYLOAD-KERNEL-MEDIATION",
        "source_commit": str(source_commit),
        "run_id": str(run_id),
        "technical_only": bool(technical_only),
        "scientific_terminal_admitted": not bool(technical_only),
        "probe_boundary": {
            "horizon": HORIZON,
            "k_search": K_SEARCH,
            "one_exact_cell": registration.cell_identifier,
            "branch_identity_is_provenance_metadata_only": True,
            "environment_or_trajectory_executed": False,
        },
        "prerequisite_admission": {"all_pass": True, **admission},
        "common_prewrite_snapshot_digest": common_digest,
        "arms": arms,
        "scientific_activity_counts": dict(FULL_ACTIVITY_COUNTS),
        "exclusions": {
            "learner": True,
            "trainer": True,
            "optimizer": True,
            "return_evaluation": True,
            "sample_or_monte_carlo": True,
            "cell_search": True,
            "rescue": True,
            "extra_arms": True,
        },
    }
    artifact["analysis"] = analyze_artifact(artifact)
    artifact["decision"] = artifact["analysis"]["decision"]
    validate_artifact(artifact)
    return artifact


def write_json(artifact: Mapping[str, Any], path: str | pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def load_json(path: str | pathlib.Path) -> dict[str, Any]:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

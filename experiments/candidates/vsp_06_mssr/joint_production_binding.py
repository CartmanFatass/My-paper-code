"""VSP06-A1 registered production binding and legal-history witness.

The result-bearing A probe exposed by :func:`registered_probe` constructs the
registered production factories but performs zero policy/runtime activity.
The dynamic helper
:func:`build_legal_matched_support_witness` exists solely for focused technical
tests: it drives two legal ``apply_transaction`` histories and is deliberately
not called by the CLI/probe.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process import dynamic_roster_supplied_executor as production_runtime
from ha_ctse_process.variable_roster_event import (
    ACTIVE,
    JOIN,
    MSSR_JOINT_PRODUCTION_ACTION_PATH,
    REJOIN,
    TEMPORARY_LEAVE,
    TERMINAL_LEAVE,
)
from ha_ctse_process.variable_roster_event_types import (
    BoundaryMember,
    BoundarySnapshot,
    MembershipDelta,
    MembershipTransaction,
)


RAW_OUTPUT_BINDING = "vsp_06_mssr.joint_production_binding.a1.v1"
CANDIDATE = "CAND-VSP-06-MSSR@adversarial-revision-v8"
ESTABLISHED = "A1_JOINT_PRODUCTION_BINDING_AND_MATCHED_SUPPORT_WITNESS_ESTABLISHED"
NO_SINGLE_PATH = "A1_COMPONENTS_EXIST_BUT_NO_SINGLE_REGISTERED_PRODUCTION_PATH"
NO_WITNESS = "A1_PRODUCTION_PATH_BOUND_BUT_LEGAL_MATCHED_SUPPORT_WITNESS_ABSENT"
PROVENANCE_OR_CONTEXT_FAILURE = "A1_PROVENANCE_OR_CURRENT_CONTEXT_EQUALITY_FAILS_CLOSED"
INVALID = "A1_TECHNICAL_PACKAGE_INVALID"

OWNER = "owner"
HISTORICAL_SOURCE = "historical_source"
CURRENT_SOURCE = "current_source"

COMMON_OWNER_OBS = np.asarray([0.25, 0.5, -0.25], dtype=np.float32)
COMMON_SOURCE_OBS = np.asarray([0.0, 0.5, 0.5], dtype=np.float32)
POSITIVE_HISTORY_SOURCE_OBS = np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
NEGATIVE_HISTORY_SOURCE_OBS = np.asarray([-1.0, 0.0, 0.0], dtype=np.float32)
HISTORY_OWNER_OBS = np.asarray([1.0, 0.0, 0.0], dtype=np.float32)

LEGAL_HISTORY_PLAN = (
    "JOIN owner + historical_source; production action writes authenticated P",
    "TEMPORARY_LEAVE owner + TERMINAL_LEAVE historical_source + JOIN current_source",
    "REJOIN owner; selective route retains P, renews F, and uses common current source",
)


def _plain(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        array = value.detach().cpu().contiguous().numpy()
        return {
            "kind": "tensor",
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "bytes": array.tobytes().hex(),
        }
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        return {
            "kind": "ndarray",
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "bytes": array.tobytes().hex(),
        }
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def _bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


@dataclass(frozen=True)
class _CaptureRowFields:
    logits: np.ndarray
    probabilities: np.ndarray
    preimage_digest: str

    def row_fields(self) -> dict[str, Any]:
        return {
            "direct_masked_logits": self.logits.copy(),
            "direct_probabilities": self.probabilities.copy(),
            "actor_preimage_digest": self.preimage_digest,
        }


class _ProductionDecisionCapture:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def capture(
        self,
        *,
        owner_lifecycle_key: str,
        membership_epoch: int,
        token_position: int,
        masked_logits: torch.Tensor,
        probabilities: torch.Tensor,
        preimage: Mapping[str, Any],
    ) -> _CaptureRowFields:
        partition = dict(preimage.get("mssr_spf_partition", {}))
        if set(partition) != {"S", "P", "F", "owners", "production_action_path"}:
            raise RuntimeError("registered MSSR production decision omitted S/P/F")
        non_p_partition = {key: value for key, value in partition.items() if key != "P"}
        non_p_preimage = dict(preimage)
        non_p_preimage["mssr_spf_partition"] = non_p_partition
        context = {
            "owner_lifecycle_key": owner_lifecycle_key,
            "membership_epoch": int(membership_epoch),
            "token_position": int(token_position),
            "preimage_without_P": non_p_preimage,
        }
        logits = masked_logits.detach().cpu().numpy().copy()
        probs = probabilities.detach().cpu().numpy().copy()
        row = {
            "owner_lifecycle_key": owner_lifecycle_key,
            "membership_epoch": int(membership_epoch),
            "token_position": int(token_position),
            "production_action_path": partition["production_action_path"],
            "partition_owners": tuple(partition["owners"]),
            "authenticated_p_hex": _bytes(partition["P"]).hex(),
            "authenticated_p_digest": _digest(partition["P"]),
            "S_digest": _digest(partition["S"]),
            "F_digest": _digest(partition["F"]),
            "current_non_p_context_hex": _bytes(context).hex(),
            "current_non_p_context_digest": _digest(context),
            "full_masked_logits": tuple(float(value) for value in logits.reshape(-1)),
            "full_probabilities": tuple(float(value) for value in probs.reshape(-1)),
            "masked_logits_digest": _digest(logits),
            "probabilities_digest": _digest(probs),
            "sampled_order": tuple(preimage["sampled_order"]),
            "active_lifecycle_keys": tuple(preimage["active_lifecycle_keys"]),
            "exact_legal_mask_digest": _digest(preimage["legal_mask"]),
            "current_observations_digest": _digest(preimage["observations"]),
        }
        self.rows.append(row)
        return _CaptureRowFields(logits, probs, row["current_non_p_context_digest"])


def _registered_factories() -> tuple[Any | None, Any | None]:
    return (
        getattr(production_runtime, "make_mssr_joint_model_owner", None),
        getattr(production_runtime, "make_mssr_joint_runtime_core", None),
    )


def _factory_triplet() -> tuple[dict[str, Any], Any | None, Any | None, Any | None]:
    """Construct only through the registered production factory API."""

    model_factory, runtime_factory = _registered_factories()
    if not callable(model_factory) or not callable(runtime_factory):
        return (
            {
                "factory_available": False,
                "factory_identity": False,
                "path_bound": False,
                "factory_error": "registered MSSR production factory API is absent",
            },
            None,
            None,
            None,
        )
    try:
        model_owner = model_factory("cpu")
        left = runtime_factory(
            model_owner, environment_index=0, episode_id=60809
        )
        right = runtime_factory(
            model_owner, environment_index=0, episode_id=60809
        )
    except Exception as exc:  # fail-closed evidence, never a local fallback
        return (
            {
                "factory_available": True,
                "factory_identity": False,
                "path_bound": False,
                "factory_error": f"{type(exc).__name__}: {exc}",
            },
            None,
            None,
            None,
        )
    factory_identity = bool(
        left.commitment_model is model_owner.commitment_model
        and right.commitment_model is model_owner.commitment_model
        and left.event_critic is model_owner.event_critic
        and right.event_critic is model_owner.event_critic
        and int(left.environment_index) == int(right.environment_index) == 0
        and int(left.rng_episode_id) == int(right.rng_episode_id) == 60809
    )
    path_bound = bool(
        model_owner.production_action_path
        == left.production_action_path
        == right.production_action_path
        == MSSR_JOINT_PRODUCTION_ACTION_PATH
    )
    return (
        {
            "factory_available": True,
            "factory_identity": factory_identity,
            "path_bound": path_bound,
            "factory_error": None,
        },
        model_owner,
        left,
        right,
    )


def _expanded(values: np.ndarray, dimension: int) -> np.ndarray:
    result = np.zeros(int(dimension), dtype=np.float32)
    count = min(int(dimension), int(values.shape[0]))
    result[:count] = values[:count]
    return result


def _member(
    core: Any,
    key: str,
    epoch: int,
    observation: np.ndarray,
) -> BoundaryMember:
    return BoundaryMember.make(
        key,
        epoch,
        _expanded(observation, core.obs_dim),
        _expanded(observation, core.critic_member_dim),
        obs_dim=core.obs_dim,
        critic_member_dim=core.critic_member_dim,
    )


def _snapshot(
    core: Any,
    rows: Sequence[tuple[str, int, np.ndarray]],
    *,
    frontier: Sequence[str] = (),
) -> BoundarySnapshot:
    return BoundarySnapshot.make(
        core.physical_time,
        tuple(_member(core, *row) for row in rows),
        np.zeros(core.critic_global_dim, dtype=np.float32),
        critic_global_dim=core.critic_global_dim,
        frontier=tuple(frontier),
    )


def _empty_snapshot(core: Any) -> BoundarySnapshot:
    return BoundarySnapshot.make(
        core.physical_time,
        (),
        np.zeros(core.critic_global_dim, dtype=np.float32),
        critic_global_dim=core.critic_global_dim,
    )


def _drive_history(
    core: Any,
    historical_source_observation: np.ndarray,
) -> dict[str, Any]:
    initial_rows = (
        (OWNER, 0, HISTORY_OWNER_OBS),
        (HISTORICAL_SOURCE, 0, historical_source_observation),
    )
    core.apply_transaction(
        MembershipTransaction(
            _empty_snapshot(core),
            (
                MembershipDelta(JOIN, OWNER, 0),
                MembershipDelta(JOIN, HISTORICAL_SOURCE, 0),
            ),
            _snapshot(core, initial_rows, frontier=(OWNER, HISTORICAL_SOURCE)),
        ),
        teacher_order=(OWNER, HISTORICAL_SOURCE),
        teacher_actions={OWNER: 0, HISTORICAL_SOURCE: 1},
    )
    source_row = core.records[OWNER].partner_interaction_history.rows[-1]

    core.apply_transaction(
        MembershipTransaction(
            _snapshot(core, initial_rows),
            (
                MembershipDelta(TEMPORARY_LEAVE, OWNER, 0),
                MembershipDelta(TERMINAL_LEAVE, HISTORICAL_SOURCE, 0),
                MembershipDelta(JOIN, CURRENT_SOURCE, 0),
            ),
            _snapshot(
                core,
                ((CURRENT_SOURCE, 0, COMMON_SOURCE_OBS),),
                frontier=(CURRENT_SOURCE,),
            ),
        ),
        teacher_order=(CURRENT_SOURCE,),
        teacher_actions={CURRENT_SOURCE: 2},
    )

    capture = _ProductionDecisionCapture()
    core.install_kernel_capture(capture)
    current_rows = (
        (OWNER, 1, COMMON_OWNER_OBS),
        (CURRENT_SOURCE, 0, COMMON_SOURCE_OBS),
    )
    final_result = core.apply_transaction(
        MembershipTransaction(
            _snapshot(
                core,
                ((CURRENT_SOURCE, 0, COMMON_SOURCE_OBS),),
            ),
            (MembershipDelta(REJOIN, OWNER, 0),),
            _snapshot(core, current_rows, frontier=(OWNER,)),
        ),
        teacher_order=(OWNER,),
        deterministic_policy=True,
    )
    core.install_kernel_capture(None)
    if len(capture.rows) != 1:
        raise RuntimeError("matched-support history did not reach one owner decision")
    row = capture.rows[0]
    if len(final_result.token_rows) != 1:
        raise RuntimeError("matched-support decision emitted the wrong token count")
    selected_action = int(final_result.token_rows[0].combined_action)
    kernel_argmax = int(np.argmax(np.asarray(row["full_masked_logits"])))
    row["selected_action"] = selected_action
    row["kernel_argmax"] = kernel_argmax
    row["action_from_full_kernel"] = selected_action == kernel_argmax
    row["teacher_action_used"] = False
    return {
        "decision": row,
        "historical_write": {
            "episode_id": source_row.episode_id,
            "owner_lifecycle_key": source_row.owner_lifecycle_key,
            "membership_epoch": source_row.membership_epoch,
            "partner_lifecycle_key": source_row.partner_lifecycle_key,
            "event_index": source_row.event_index,
            "prior_p": source_row.prior_p,
            "payload": source_row.payload,
            "next_p": source_row.next_p,
            "writer_policy_version": source_row.writer_policy_version,
        },
        "legal_history": LEGAL_HISTORY_PLAN,
        "final_owner_status": core.records[OWNER].status,
        "final_owner_epoch": core.records[OWNER].membership_epoch,
        "production_path": core.production_action_path,
    }


def build_legal_matched_support_witness() -> dict[str, Any]:
    """Run the fixed focused-test witness; never called by the A probe CLI."""

    factory, _owner, left_core, right_core = _factory_triplet()
    evidence: dict[str, Any] = {
        "package_valid": True,
        **factory,
        "legal_histories": False,
        "retained_support_present": False,
        "provenance_authenticated": False,
        "current_non_p_context_byte_equal": False,
        "authenticated_p_byte_different": False,
        "action_from_full_kernel": False,
    }
    left = right = None
    if factory["factory_identity"] and factory["path_bound"]:
        try:
            left = _drive_history(left_core, POSITIVE_HISTORY_SOURCE_OBS)
            right = _drive_history(right_core, NEGATIVE_HISTORY_SOURCE_OBS)
            left_decision = left["decision"]
            right_decision = right["decision"]
            evidence.update(
                {
                    "legal_histories": all(
                        row["final_owner_status"] == ACTIVE
                        and row["final_owner_epoch"] == 1
                        for row in (left, right)
                    ),
                    "retained_support_present": True,
                    "provenance_authenticated": all(
                        row["historical_write"]["owner_lifecycle_key"] == OWNER
                        and row["historical_write"]["partner_lifecycle_key"]
                        == HISTORICAL_SOURCE
                        for row in (left, right)
                    ),
                    "current_non_p_context_byte_equal": (
                        left_decision["current_non_p_context_hex"]
                        == right_decision["current_non_p_context_hex"]
                    ),
                    "authenticated_p_byte_different": (
                        left_decision["authenticated_p_hex"]
                        != right_decision["authenticated_p_hex"]
                    ),
                    "action_from_full_kernel": all(
                        row["decision"]["action_from_full_kernel"]
                        and not row["decision"]["teacher_action_used"]
                        for row in (left, right)
                    ),
                }
            )
        except Exception as exc:
            evidence["package_valid"] = False
            evidence["witness_error"] = f"{type(exc).__name__}: {exc}"
    branch = classify_retained_evidence(evidence)
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "candidate": CANDIDATE,
        "branch": branch,
        "evidence": evidence,
        "left": left,
        "right": right,
        "scope": "focused implementation test only; not the registered A probe",
    }


RETAINED_EVIDENCE_FIELDS = {
    "package_valid",
    "factory_available",
    "factory_identity",
    "path_bound",
    "legal_histories",
    "retained_support_present",
    "provenance_authenticated",
    "current_non_p_context_byte_equal",
    "authenticated_p_byte_different",
    "action_from_full_kernel",
}


def classify_retained_evidence(evidence: Mapping[str, Any]) -> str:
    """Authoritative five-branch precedence over retained technical evidence."""

    if not isinstance(evidence, Mapping) or not RETAINED_EVIDENCE_FIELDS.issubset(
        evidence
    ):
        return INVALID
    if any(not isinstance(evidence[name], bool) for name in RETAINED_EVIDENCE_FIELDS):
        return INVALID
    if not evidence["package_valid"]:
        return INVALID
    if not (
        evidence["factory_available"]
        and evidence["factory_identity"]
        and evidence["path_bound"]
    ):
        return NO_SINGLE_PATH
    if not (
        evidence["legal_histories"]
        and evidence["retained_support_present"]
        and evidence["authenticated_p_byte_different"]
    ):
        return NO_WITNESS
    if not (
        evidence["provenance_authenticated"]
        and evidence["current_non_p_context_byte_equal"]
    ):
        return PROVENANCE_OR_CONTEXT_FAILURE
    if not evidence["action_from_full_kernel"]:
        return INVALID
    return ESTABLISHED


def registered_probe(
    retained_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct the real factories but execute no policy or environment."""

    factory, _owner, _left, _right = _factory_triplet()
    evidence = {
        "package_valid": True,
        "factory_available": bool(factory["factory_available"]),
        "factory_identity": bool(factory["factory_identity"]),
        "path_bound": bool(factory["path_bound"]),
        "legal_histories": False,
        "retained_support_present": False,
        "provenance_authenticated": False,
        "current_non_p_context_byte_equal": False,
        "authenticated_p_byte_different": False,
        "action_from_full_kernel": False,
    }
    if retained_evidence is not None:
        retained_body = retained_evidence.get("evidence")
        if (
            retained_evidence.get("raw_output_binding") != RAW_OUTPUT_BINDING
            or retained_evidence.get("candidate") != CANDIDATE
            or not isinstance(retained_body, Mapping)
        ):
            evidence["package_valid"] = False
        else:
            evidence.update(dict(retained_body))
        # Factory/path facts are always freshly observed, never trusted from a
        # supplied receipt.
        evidence.update(
            {
                "factory_available": bool(factory["factory_available"]),
                "factory_identity": bool(factory["factory_identity"]),
                "path_bound": bool(factory["path_bound"]),
            }
        )
    branch = classify_retained_evidence(evidence)
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "candidate": CANDIDATE,
        "branch": branch,
        "registered_production_path": MSSR_JOINT_PRODUCTION_ACTION_PATH,
        "factory_observation": factory,
        "retained_evidence": evidence,
        "legal_history_plan": list(LEGAL_HISTORY_PLAN),
        "focused_dynamic_witness": {
            "callable": "build_legal_matched_support_witness",
            "test_locator": (
                "tests/experiments/candidates/vsp_06_mssr/"
                "test_joint_production_binding.py"
            ),
            "executed_by_registered_probe": False,
        },
        "activity_counts": {
            "environment_transitions": 0,
            "policy_calls": 0,
            "learner_calls": 0,
            "trainer_calls": 0,
            "optimizer_calls": 0,
            "evaluation_calls": 0,
            "environment_rng_draws": 0,
            "action_rng_draws": 0,
        },
        "technical_factory_constructions": {
            "model_owner": 1 if factory["factory_identity"] else 0,
            "runtime_cores": 2 if factory["factory_identity"] else 0,
        },
        "limitations": (
            "The registered probe constructs the production factories but "
            "executes no policy. Without separately retained focused-test "
            "evidence it fails closed rather than claiming matched support. "
            "No MSSR algorithm effect is established."
        ),
    }


__all__ = [
    "build_legal_matched_support_witness",
    "classify_retained_evidence",
    "registered_probe",
    "ESTABLISHED",
    "NO_SINGLE_PATH",
    "NO_WITNESS",
    "PROVENANCE_OR_CONTEXT_FAILURE",
    "INVALID",
]

"""Exact VSP02-A2 crossed physical-value support certificate.

The registered object is frozen in a manifest before any value cell is
constructed.  Runtime evaluation is finite rational enumeration only: there
are no environment episodes, policy calls, stochastic draws, learners, or
model fitting in this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from fractions import Fraction
from typing import Mapping

from experiments.candidates.vsp_02 import owner_action_responsive_lifecycle as a1


A2_SCHEMA_VERSION = 1
A2_ASSIGNMENT_ID = "VSP02-A2-CROSSED-PHYSICAL-VALUE-SUPPORT"
A2_CANDIDATE = "CAND-VSP-02@adversarial-revision-v8"
A2_RESOURCE_CLASS = "A_READONLY_OR_ZERO_RUNTIME"

BRANCH_PRECEDENCE = (
    "A2_INVALID_CONTRACT_OR_INFORMATION_LEAK",
    "A2_CUE_OR_ACTION_SUPPORT_ABSENT",
    "A2_REGISTERED_STRICT_CROSSING_SUPPORTED",
    "A2_REVERSED_STRICT_CROSSING",
    "A2_NONZERO_BUT_NOT_CROSSED",
    "A2_BOTH_DELTAS_ZERO",
)

ACTIVITY_ZERO_FIELDS = (
    "environment_transitions",
    "policy_calls",
    "learner_calls",
    "trainer_calls",
    "optimizer_updates",
    "evaluation_episodes",
    "model_fits",
    "stochastic_draws",
    "retries",
    "rescues",
    "sweeps",
    "b_runs",
    "c_runs",
    "formal_compute_runs",
)

CELL_KEYS = (
    "X_b=1|RELEASE",
    "X_b=1|HOLD",
    "X_b=0|RELEASE",
    "X_b=0|HOLD",
)

CUE_SOURCE_FIELDS = ("public_cutoff_request",)
CUE_FORBIDDEN_FIELDS = frozenset(
    {
        "future_termination",
        "future_reward",
        "hidden_tape",
        "realized_end_cause",
        "treatment",
        "branch",
        "q_value",
        "delta",
    }
)


class CueState(str, Enum):
    X1 = "X_b=1"
    X0 = "X_b=0"


OwnerAction = a1.OwnerAction


@dataclass(frozen=True)
class PhysicalTape:
    tape_id: str
    cue: CueState
    public_cutoff_request: bool
    weight: Fraction
    continuation_reward: Fraction
    natural_close_reward: Fraction = Fraction(0)


@dataclass(frozen=True)
class CellResult:
    cue: CueState
    action: OwnerAction
    q_value: Fraction
    target: Fraction
    score: Fraction
    tape_id: str
    tape_weight: Fraction
    registered_action_propensity: Fraction
    observation: Mapping[str, object]
    lifecycle: Mapping[str, object]
    reward_sequence: tuple[Fraction, ...]


FROZEN_TAPES = (
    PhysicalTape(
        tape_id="VSP02-A2-PUBLIC-CUTOFF-REQUEST",
        cue=CueState.X1,
        public_cutoff_request=True,
        weight=Fraction(1, 2),
        continuation_reward=Fraction(-1),
    ),
    PhysicalTape(
        tape_id="VSP02-A2-PUBLIC-PRODUCTIVE-WINDOW",
        cue=CueState.X0,
        public_cutoff_request=False,
        weight=Fraction(1, 2),
        continuation_reward=Fraction(2),
    ),
)


def _q(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _fraction(value: object) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, str):
        parsed = Fraction(value)
        if _q(parsed) == value:
            return parsed
    raise ValueError(f"not a canonical exact rational: {value!r}")


def frozen_contract() -> dict[str, object]:
    """Return the prospective contract; it intentionally contains no Q or delta."""

    candidate = a1.candidate_contract()
    owner = a1.default_owner()
    return {
        "contract_id": "VSP02-A2-PUBLIC-CUTOFF-PHYSICAL-V1",
        "reward": {
            "release_physical_settlement": Fraction(1),
            "hold_continuation_by_public_state": {
                CueState.X1.value: Fraction(-1),
                CueState.X0.value: Fraction(2),
            },
            "natural_close_reward": Fraction(0),
            "lifecycle_event_bonus": Fraction(0),
        },
        "transition": {
            "decision_clock": 1,
            "release_next_phase": a1.Phase.ENDED_RELEASE.value,
            "hold_intermediate_phase": a1.Phase.ACTIVE.value,
            "hold_close_clock": 2,
            "hold_close_phase": a1.Phase.ENDED_NATURAL.value,
            "terminal_precedence": list(a1.TERMINAL_PRECEDENCE),
        },
        "discount": Fraction(1, 2),
        "horizon": candidate.horizon,
        "continuation_policy": "AFTER_FORCED_HOLD_COMMIT_ONE_FROZEN_PRIMITIVE_THEN_NATURAL_CLOSE",
        "partner_policy": "FROZEN_PARTNER_NOOP_V1",
        "primitive_policy": candidate.primitive_policy,
        "owner": {
            "owner_id": owner.owner_id,
            "owner_epoch": owner.owner_epoch,
            "behavior_version": owner.behavior_version,
        },
        "lifecycle": {
            "source": "VSP02-A1-OWNER-ACTION-RESPONSIVE-LIFECYCLE",
            "backend": candidate.backend.value,
            "release_has_stopping_edge": candidate.release_has_stopping_edge,
            "reward_contract_boundary": candidate.reward_contract,
            "command_alphabet": list(candidate.command_alphabet),
            "command_bandwidth_bits": candidate.command_bandwidth_bits,
        },
        "cue": {
            "registered_labels": [CueState.X1.value, CueState.X0.value],
            "source_fields": list(CUE_SOURCE_FIELDS),
            "mapping": {"true": CueState.X1.value, "false": CueState.X0.value},
            "observation_clock": 0,
            "decision_clock": 1,
            "forbidden_fields": sorted(CUE_FORBIDDEN_FIELDS),
            "semantics": "prospective public cutoff request; never relabeled",
        },
        "target_score": {
            "target": "exact discounted physical return under the forced action",
            "score": "the same exact physical return, with no fit or bootstrap",
        },
        "matched_exogenous_tapes": [
            {
                "tape_id": tape.tape_id,
                "cue": tape.cue.value,
                "public_cutoff_request": tape.public_cutoff_request,
                "weight": tape.weight,
                "continuation_reward": tape.continuation_reward,
                "natural_close_reward": tape.natural_close_reward,
                "future_terminal": False,
                "future_interrupt": False,
                "owner_departure": False,
            }
            for tape in FROZEN_TAPES
        ],
    }


def frozen_support_design() -> dict[str, object]:
    return {
        "cue_probability": {
            CueState.X1.value: Fraction(1, 2),
            CueState.X0.value: Fraction(1, 2),
        },
        "forced_action_propensity": {
            key: Fraction(1, 2) for key in CELL_KEYS
        },
        "joint_support": {key: Fraction(1, 4) for key in CELL_KEYS},
        "evaluation": "exact forced-action enumeration; no stochastic draw",
    }


def build_a2_manifest(
    *, source_revision: str, run_id: str, technical_only: bool
) -> dict[str, object]:
    return {
        "schema_version": A2_SCHEMA_VERSION,
        "artifact_kind": "vsp02_a2_frozen_manifest",
        "assignment_id": A2_ASSIGNMENT_ID,
        "candidate": A2_CANDIDATE,
        "evidence_level": "A",
        "formal": False,
        "resource_class": A2_RESOURCE_CLASS,
        "pool_units": 0,
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": technical_only,
        "frozen_contract": frozen_contract(),
        "support_design": frozen_support_design(),
        "required_cells": list(CELL_KEYS),
        "terminal_branch_precedence": list(BRANCH_PRECEDENCE),
        "registered_invocation_cap": 1,
        "retry_permitted": False,
    }


def validate_a2_manifest(manifest: object) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ("manifest is not an object",)
    issues: list[str] = []
    fixed = {
        "schema_version": A2_SCHEMA_VERSION,
        "artifact_kind": "vsp02_a2_frozen_manifest",
        "assignment_id": A2_ASSIGNMENT_ID,
        "candidate": A2_CANDIDATE,
        "evidence_level": "A",
        "formal": False,
        "resource_class": A2_RESOURCE_CLASS,
        "pool_units": 0,
        "registered_invocation_cap": 1,
        "retry_permitted": False,
    }
    for key, expected in fixed.items():
        if manifest.get(key) != expected:
            issues.append(f"{key} mismatch")
    for key in ("source_revision", "run_id"):
        if not isinstance(manifest.get(key), str) or not manifest.get(key):
            issues.append(f"{key} must be a nonempty string")
    if not isinstance(manifest.get("technical_only"), bool):
        issues.append("technical_only must be boolean")
    canonical = build_a2_manifest(
        source_revision=str(manifest.get("source_revision", "")),
        run_id=str(manifest.get("run_id", "")),
        technical_only=bool(manifest.get("technical_only")),
    )
    for key in (
        "frozen_contract",
        "support_design",
        "required_cells",
        "terminal_branch_precedence",
    ):
        if json_ready(manifest.get(key)) != json_ready(canonical[key]):
            issues.append(f"{key} mismatch")
    forbidden_result_keys = {"q_values", "deltas", "branch", "result"}
    leaked = sorted(forbidden_result_keys & set(manifest))
    if leaked:
        issues.append(f"prospective manifest contains result keys: {leaked}")
    return tuple(issues)


def _dependency_contract_checks() -> dict[str, bool]:
    candidate = a1.candidate_contract()
    owner = a1.default_owner()
    world = a1.default_world()
    return {
        "a1_candidate_release_edge_preserved": candidate.release_has_stopping_edge is True,
        "a1_horizon_preserved": candidate.horizon == 4,
        "a1_primitive_policy_preserved": candidate.primitive_policy == "FROZEN_PRIMITIVE_V1",
        "owner_epoch_and_version_frozen": (
            owner.owner_id == "owner-A"
            and owner.owner_epoch == 17
            and owner.behavior_version == a1.CURRENT_BEHAVIOR_VERSION == 8
            and owner.member_epoch in world.authoritative_membership
        ),
        "terminal_precedence_preserved": a1.TERMINAL_PRECEDENCE
        == ("TERMINAL", "INTERRUPT", "AUTHORIZED_RELEASE", "NATURAL", "HORIZON"),
        "cue_source_is_predecision_only": not (set(CUE_SOURCE_FIELDS) & CUE_FORBIDDEN_FIELDS),
        "cue_labels_prospectively_fixed": tuple(tape.cue for tape in FROZEN_TAPES)
        == (CueState.X1, CueState.X0),
        "matched_tapes_positive_and_normalized": (
            all(tape.weight > 0 for tape in FROZEN_TAPES)
            and sum((tape.weight for tape in FROZEN_TAPES), Fraction(0)) == 1
        ),
    }


def _fresh_claimed(tape: PhysicalTape) -> tuple[a1.LifecycleRecord, a1.AuthorityToken, a1.WorldView]:
    token = a1.default_owner()
    world = a1.default_world()
    claimed = a1.claim(
        a1.LifecycleRecord(f"vsp02-a2-{tape.cue.value}", slot_id=3),
        token,
        world,
        physical_clock=0,
    )
    if not claimed.accepted:
        raise AssertionError("canonical A2 claim unexpectedly rejected")
    return claimed.record, token, world


def _evaluate_cell(tape: PhysicalTape, action: OwnerAction) -> CellResult:
    record, token, world = _fresh_claimed(tape)
    observation = a1.predecision_observation(
        record,
        world,
        opaque_post_claim_cue=tape.cue.value,
    )
    first = a1.apply_boundary(
        record,
        contract=a1.candidate_contract(),
        action=action,
        command_token=token,
        world=world,
        boundary_index=1,
        physical_clock=1,
        tape=a1.PairedTape(tape.tape_id),
        release_id=f"{tape.tape_id}-release",
    ).record
    if action is OwnerAction.RELEASE:
        rewards = (Fraction(1),)
        final = first
    else:
        final = a1.apply_boundary(
            first,
            contract=a1.candidate_contract(),
            action=OwnerAction.HOLD,
            command_token=token,
            world=world,
            boundary_index=2,
            physical_clock=2,
            tape=a1.PairedTape(tape.tape_id, natural=True),
            release_id=f"{tape.tape_id}-unused-release",
        ).record
        rewards = (tape.continuation_reward, tape.natural_close_reward)
    gamma = Fraction(1, 2)
    q_value = sum(
        (gamma**offset) * reward for offset, reward in enumerate(rewards)
    )
    return CellResult(
        cue=tape.cue,
        action=action,
        q_value=q_value,
        target=q_value,
        score=q_value,
        tape_id=tape.tape_id,
        tape_weight=tape.weight,
        registered_action_propensity=Fraction(1, 2),
        observation={
            "cue": tape.cue.value,
            "public_cutoff_request": tape.public_cutoff_request,
            "observation_clock": 0,
            "decision_clock": 1,
            "a1_observation_firewall_valid": a1.observation_firewall_valid(observation),
            "a1_observation": asdict(observation),
        },
        lifecycle={
            "owner_id": token.owner_id,
            "owner_epoch": token.owner_epoch,
            "behavior_version": token.behavior_version,
            "predecision_phase": record.phase.value,
            "postdecision_phase": first.phase.value,
            "final_phase": final.phase.value,
            "final_end_cause": final.end_cause.value if final.end_cause else None,
            "command_log": final.command_log,
            "release_ledger": final.release_ledger,
        },
        reward_sequence=rewards,
    )


def _cell_support_valid(cell: CellResult) -> bool:
    expected_post = (
        a1.Phase.ENDED_RELEASE.value
        if cell.action is OwnerAction.RELEASE
        else a1.Phase.ACTIVE.value
    )
    expected_final = (
        a1.Phase.ENDED_RELEASE.value
        if cell.action is OwnerAction.RELEASE
        else a1.Phase.ENDED_NATURAL.value
    )
    return bool(
        cell.tape_weight > 0
        and cell.registered_action_propensity > 0
        and cell.lifecycle["postdecision_phase"] == expected_post
        and cell.lifecycle["final_phase"] == expected_final
        and cell.observation["a1_observation_firewall_valid"] is True
    )


def _report_values(report: Mapping[str, object]) -> tuple[dict[str, Fraction], dict[str, Fraction]]:
    raw_cells = report.get("q_values")
    raw_deltas = report.get("deltas")
    if not isinstance(raw_cells, Mapping) or set(raw_cells) != set(CELL_KEYS):
        raise ValueError("four-cell domain mismatch")
    if not isinstance(raw_deltas, Mapping) or set(raw_deltas) != {"Delta_1", "Delta_0"}:
        raise ValueError("delta domain mismatch")
    cells = {key: _fraction(raw_cells[key]) for key in CELL_KEYS}
    deltas = {key: _fraction(raw_deltas[key]) for key in ("Delta_1", "Delta_0")}
    recomputed = {
        "Delta_1": cells["X_b=1|RELEASE"] - cells["X_b=1|HOLD"],
        "Delta_0": cells["X_b=0|RELEASE"] - cells["X_b=0|HOLD"],
    }
    if deltas != recomputed:
        raise ValueError("registered delta mismatch")
    return cells, deltas


def classify_a2(report: Mapping[str, object]) -> str:
    contract = report.get("contract_checks")
    if not isinstance(contract, Mapping) or not contract or not all(
        value is True for value in contract.values()
    ):
        return BRANCH_PRECEDENCE[0]
    if json_ready(report.get("frozen_physical_object")) != json_ready(frozen_contract()):
        return BRANCH_PRECEDENCE[0]
    try:
        cells, deltas = _report_values(report)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return BRANCH_PRECEDENCE[0]
    cell_records = report.get("cells")
    if not isinstance(cell_records, Mapping) or set(cell_records) != set(CELL_KEYS):
        return BRANCH_PRECEDENCE[0]
    try:
        for key in CELL_KEYS:
            cell = cell_records[key]
            if not isinstance(cell, Mapping):
                raise ValueError("cell record is not an object")
            cue, action = key.split("|", 1)
            observation = cell.get("observation")
            lifecycle = cell.get("lifecycle")
            if not isinstance(observation, Mapping) or not isinstance(lifecycle, Mapping):
                raise ValueError("cell witness missing")
            expected_post = "ENDED_RELEASE" if action == "RELEASE" else "ACTIVE"
            expected_final = "ENDED_RELEASE" if action == "RELEASE" else "ENDED_NATURAL"
            if not (
                json_ready(cell.get("cue")) == cue
                and json_ready(cell.get("action")) == action
                and _fraction(cell.get("q_value")) == cells[key]
                and _fraction(cell.get("target")) == cells[key]
                and _fraction(cell.get("score")) == cells[key]
                and observation.get("cue") == cue
                and observation.get("observation_clock") == 0
                and observation.get("decision_clock") == 1
                and observation.get("a1_observation_firewall_valid") is True
                and lifecycle.get("owner_id") == "owner-A"
                and lifecycle.get("owner_epoch") == 17
                and lifecycle.get("behavior_version") == 8
                and lifecycle.get("postdecision_phase") == expected_post
                and lifecycle.get("final_phase") == expected_final
            ):
                raise ValueError("cell witness mismatch")
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return BRANCH_PRECEDENCE[0]
    support = report.get("support")
    if not isinstance(support, Mapping):
        return BRANCH_PRECEDENCE[1]
    witnesses = support.get("witnesses")
    cue_probability = support.get("cue_probability")
    action_propensity = support.get("forced_action_propensity")
    try:
        support_present = bool(
            isinstance(witnesses, Mapping)
            and set(witnesses) == set(CELL_KEYS)
            and all(isinstance(witnesses[key], Mapping) and witnesses[key].get("legal") is True for key in CELL_KEYS)
            and isinstance(cue_probability, Mapping)
            and set(cue_probability) == {CueState.X1.value, CueState.X0.value}
            and all(_fraction(cue_probability[cue.value]) > 0 for cue in CueState)
            and isinstance(action_propensity, Mapping)
            and set(action_propensity) == set(CELL_KEYS)
            and all(_fraction(action_propensity[key]) > 0 for key in CELL_KEYS)
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        support_present = False
    if not support_present:
        return BRANCH_PRECEDENCE[1]
    delta_1, delta_0 = deltas["Delta_1"], deltas["Delta_0"]
    if delta_1 > 0 and delta_0 < 0:
        return BRANCH_PRECEDENCE[2]
    if delta_1 < 0 and delta_0 > 0:
        return BRANCH_PRECEDENCE[3]
    if delta_1 != 0 or delta_0 != 0:
        return BRANCH_PRECEDENCE[4]
    return BRANCH_PRECEDENCE[5]


def run_physical_value_audit(manifest: Mapping[str, object]) -> dict[str, object]:
    issues = validate_a2_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    cells = {
        f"{tape.cue.value}|{action.value}": _evaluate_cell(tape, action)
        for tape in FROZEN_TAPES
        for action in OwnerAction
    }
    q_values = {key: cells[key].q_value for key in CELL_KEYS}
    deltas = {
        "Delta_1": q_values["X_b=1|RELEASE"] - q_values["X_b=1|HOLD"],
        "Delta_0": q_values["X_b=0|RELEASE"] - q_values["X_b=0|HOLD"],
    }
    support_design = frozen_support_design()
    report: dict[str, object] = {
        "frozen_physical_object": manifest["frozen_contract"],
        "contract_checks": _dependency_contract_checks(),
        "support": {
            "cue_probability": support_design["cue_probability"],
            "forced_action_propensity": support_design["forced_action_propensity"],
            "joint_support": support_design["joint_support"],
            "witnesses": {
                key: {
                    "legal": _cell_support_valid(cell),
                    "tape_id": cell.tape_id,
                    "tape_weight": cell.tape_weight,
                    "action_propensity": cell.registered_action_propensity,
                    "cue": cell.cue.value,
                    "action": cell.action.value,
                    "owner_id": cell.lifecycle["owner_id"],
                    "owner_epoch": cell.lifecycle["owner_epoch"],
                    "behavior_version": cell.lifecycle["behavior_version"],
                    "postdecision_phase": cell.lifecycle["postdecision_phase"],
                    "final_phase": cell.lifecycle["final_phase"],
                }
                for key, cell in cells.items()
            },
        },
        "q_values": q_values,
        "deltas": deltas,
        "cells": {key: asdict(cells[key]) for key in CELL_KEYS},
        "nonclaims": [
            "learner support or learner superiority",
            "B execution or B support",
            "C support",
            "escrow or adaptive superiority",
            "promotion, retirement, or formal readiness",
        ],
    }
    report["branch"] = classify_a2(report)
    return report


def zero_activity(*, registered_a_invocations: int) -> dict[str, int]:
    return {
        "registered_a_invocations": registered_a_invocations,
        "exact_fraction_cells": 4,
        **{name: 0 for name in ACTIVITY_ZERO_FIELDS},
    }


def run_a2_probe(manifest: Mapping[str, object]) -> dict[str, object]:
    report = run_physical_value_audit(manifest)
    technical_only = bool(manifest["technical_only"])
    return {
        "schema_version": A2_SCHEMA_VERSION,
        "artifact_kind": "vsp02_a2_crossed_physical_value_support_result",
        "manifest": dict(manifest),
        "branch": report["branch"],
        "report": report,
        "activity": zero_activity(registered_a_invocations=0 if technical_only else 1),
    }


def validate_a2_artifact(artifact: object) -> tuple[str, ...]:
    if not isinstance(artifact, Mapping):
        return ("artifact is not an object",)
    issues: list[str] = []
    if artifact.get("schema_version") != A2_SCHEMA_VERSION:
        issues.append("schema_version mismatch")
    if artifact.get("artifact_kind") != "vsp02_a2_crossed_physical_value_support_result":
        issues.append("artifact_kind mismatch")
    manifest = artifact.get("manifest")
    manifest_issues = validate_a2_manifest(manifest)
    issues.extend(manifest_issues)
    report = artifact.get("report")
    if not isinstance(report, Mapping):
        issues.append("report missing")
    else:
        classified = classify_a2(report)
        if report.get("branch") != classified or artifact.get("branch") != classified:
            issues.append("branch/classifier mismatch")
    activity = artifact.get("activity")
    if not isinstance(activity, Mapping):
        issues.append("activity missing")
    else:
        technical_only = isinstance(manifest, Mapping) and manifest.get("technical_only") is True
        if activity.get("registered_a_invocations") != (0 if technical_only else 1):
            issues.append("registered_a_invocations mismatch")
        if activity.get("exact_fraction_cells") != 4:
            issues.append("exact_fraction_cells mismatch")
        for field in ACTIVITY_ZERO_FIELDS:
            if activity.get(field) != 0:
                issues.append(f"{field} must be zero")
    if isinstance(manifest, Mapping) and not manifest_issues:
        expected = run_a2_probe(manifest)
        if json_ready(artifact) != json_ready(expected):
            issues.append("artifact differs from deterministic canonical reconstruction")
    return tuple(issues)


def json_ready(value: object) -> object:
    if isinstance(value, Fraction):
        return _q(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [json_ready(item) for item in value]
    return value

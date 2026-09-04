"""VSP05-A3 one-shot offline audit of the accepted A1 retained rows.

This module never imports or invokes the environment, proposal policy, executor,
learner, trainer, or optimizer.  It binds one immutable A1 JSON artifact, labels
every retained real row using the actual incumbent as the completion subject,
and fails closed when the retained trace lacks a required behavioral object.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


CANDIDATE_ID = "CAND-VSP-05@adversarial-revision-v7"
TREATMENT_ID = "VSP05-A3-TYPED-COMPLETION-SUBJECT-RETAINED-ROW-AUDIT"
SCHEMA_VERSION = 1
EXPECTED_INPUT_RELATIVE_PATH = (
    "logs/vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json"
)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_INPUT_PATH = (PROJECT_ROOT / EXPECTED_INPUT_RELATIVE_PATH).resolve()
EXPECTED_INPUT_SHA256 = (
    "d4ba7e00ae65c4f0cfd6f84b37c300e9e580868c42bd3c3f02eff20b0b3a3f2e"
)
EXPECTED_SOURCE_COMMIT = "1a09bccf9bd64c756865531bc55a871afa286dd3"
EXPECTED_RESULT_COMMIT = "9f3c57f809a0c0ee11868e025adbeea762832a46"
EXPECTED_REAL_ROWS = 15_971
EXPECTED_STATIC_ROWS = 47_913

CELLS = (
    "REFERENCE",
    "THRESHOLD_MID",
    "THRESHOLD_NEAR_GATE",
    "DRIVE_HIGH",
    "STEP_HIGH",
    "DRIVE_STEP_HIGH",
)
TASK_SEEDS = (68101, 68102, 68103)
LIFECYCLE_CATEGORIES = ("JOIN", "REJOIN", "SURVIVOR")
SKILLS = (0, 1, 2)
TARGET_CLASSES = (
    "INELIGIBLE",
    "TARGET_GATE_NEGATIVE",
    "TARGET_POSITIVE",
    "TARGET_TYPED_ALIAS",
)
SHAM_CLASSES = (
    "INELIGIBLE",
    "SHAM_GATE_NEGATIVE",
    "SHAM_POSITIVE",
    "SHAM_TYPED_ALIAS",
)
EXPECTED_DESCRIPTIVE_COUNTS = {
    "complete_population": 15_971,
    "eligible": 13_379,
    "target_positive": 12_939,
    "target_typed_alias": 217,
    "sham_positive": 0,
    "sham_typed_alias": 141,
}
TERMINAL_BRANCHES = (
    "A3_INVALID_CONTRACT",
    "A3_NO_TWO_SIDED_TARGET_SUPPORT",
    "A3_GATE_NULL_SUFFICIENT_OR_TYPED_SHAM_EQUIVALENT",
    "A3_BEHAVIORALLY_PASSIVE",
    "A3_EXPOSURE_MATCHED_COMPARATOR_REQUIRED",
    "A3_SEPARATE_B_QUESTION_ASKABLE",
)


class ContractViolation(ValueError):
    """A fail-closed source, row, or result contract violation."""


@dataclass(frozen=True)
class SourceBinding:
    path: str
    sha256: str
    bytes_read: int


@dataclass
class _EpochState:
    incumbent: int | None = None
    epoch_index: int = 0
    initialized: bool = False
    target_latch: bool = False
    target_pending_q: int | None = None
    sham_latch: bool = False
    sham_pending_q: int | None = None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractViolation(message)


def _is_bool(value: Any) -> bool:
    return type(value) is bool


def _is_exact_registered_input_path(path: Path) -> bool:
    return path.resolve().as_posix().lower() == EXPECTED_INPUT_PATH.as_posix().lower()


def load_bound_input(
    path: str | Path,
    *,
    expected_sha256: str = EXPECTED_INPUT_SHA256,
    enforce_registered_path: bool = True,
) -> tuple[dict[str, Any], SourceBinding]:
    """Read the source once, bind its bytes, then parse the exact JSON object."""

    source = Path(path)
    if enforce_registered_path:
        _require(
            _is_exact_registered_input_path(source),
            f"input path is not the registered A1 raw path: {source}",
        )
    try:
        payload_bytes = source.read_bytes()
    except OSError as exc:
        raise ContractViolation(f"registered A1 raw input unavailable: {exc}") from exc
    actual_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    _require(
        actual_sha256 == expected_sha256,
        f"accepted A1 raw SHA mismatch: {actual_sha256} != {expected_sha256}",
    )
    try:
        parsed = json.loads(payload_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractViolation(f"accepted A1 raw input is not valid JSON: {exc}") from exc
    _require(isinstance(parsed, dict), "accepted A1 raw root must be an object")
    return parsed, SourceBinding(str(source.resolve()), actual_sha256, len(payload_bytes))


def _classification(row: Mapping[str, Any], skill: int) -> tuple[bool, bool]:
    table = row.get("all_skill_classification")
    _require(isinstance(table, Mapping), "row lacks all_skill_classification")
    _require(set(table) == {"0", "1", "2"}, "all-skill classification domain drifted")
    receipt = table.get(str(skill))
    _require(isinstance(receipt, Mapping), f"classification for skill {skill} is absent")
    _require(set(receipt) == {"gate", "strict_truth"}, "classification fields drifted")
    gate = receipt["gate"]
    truth = receipt["strict_truth"]
    _require(_is_bool(gate) and _is_bool(truth), "gate/truth values must be booleans")
    _require(not truth or gate, "strict truth must imply its same-subject gate")
    return gate, truth


def _validate_row(row: Mapping[str, Any], index: int) -> None:
    required = {
        "real_frontier_id",
        "capture_boundary",
        "cell",
        "task_seed",
        "episode_index",
        "episode_id",
        "environment_step",
        "physical_time",
        "completed_primitive_transitions_at_capture",
        "lifecycle_key",
        "event_rank",
        "lifecycle_category",
        "committed_record_present",
        "incumbent_present",
        "incumbent_skill",
        "actual_proposal",
        "different_successor",
        "actual_proposal_gate",
        "actual_proposal_strict_truth",
        "all_skill_classification",
        "complete_mask",
        "real_reachable_evidence",
    }
    missing = sorted(required - set(row))
    _require(not missing, f"row {index} lacks required fields: {missing}")
    _require(row["capture_boundary"] == "POST_MEMBERSHIP_PRE_POLICY", "capture boundary drifted")
    _require(row["cell"] in CELLS, "row cell left the accepted domain")
    _require(row["task_seed"] in TASK_SEEDS, "row seed left the accepted domain")
    _require(row["lifecycle_category"] in LIFECYCLE_CATEGORIES, "lifecycle category drifted")
    _require(row["committed_record_present"] is True, "row is not post-membership committed")
    _require(row["real_reachable_evidence"] is True, "non-real row entered retained population")
    _require(
        int(row["environment_step"]) == int(row["physical_time"])
        == int(row["completed_primitive_transitions_at_capture"]),
        "pre-policy temporal binding drifted",
    )
    i = row["incumbent_skill"]
    q = row["actual_proposal"]
    _require(i is None or i in SKILLS, "incumbent left the accepted skill domain")
    _require(q in SKILLS, "proposal left the accepted skill domain")
    _require(_is_bool(row["incumbent_present"]), "incumbent_present must be boolean")
    _require(bool(row["incumbent_present"]) == (i is not None), "incumbent presence disagrees with i")
    _require((i is None) == (row["lifecycle_category"] == "JOIN"), "JOIN/incumbent meaning drifted")
    expected_d = i is not None and q != i
    _require(row["different_successor"] is expected_d, "different-successor flag drifted")
    for skill in SKILLS:
        _classification(row, skill)
    g_q, t_q = _classification(row, q)
    _require(row["actual_proposal_gate"] is g_q, "proposal gate disagrees with all-skill table")
    _require(row["actual_proposal_strict_truth"] is t_q, "proposal truth disagrees with all-skill table")
    mask = row["complete_mask"]
    _require(isinstance(mask, Mapping), "complete_mask must be an object")
    for field in ("incumbent_present", "different_successor", "actual_proposal_gate", "truth_actual_proposal"):
        _require(field in mask and _is_bool(mask[field]), f"complete_mask lacks boolean {field}")
    _require(mask["incumbent_present"] is row["incumbent_present"], "mask incumbent drifted")
    _require(mask["different_successor"] is row["different_successor"], "mask D drifted")
    _require(mask["actual_proposal_gate"] is g_q, "mask q gate drifted")
    _require(mask["truth_actual_proposal"] is t_q, "mask q truth drifted")


def validate_retained_population(
    raw: Mapping[str, Any],
    *,
    expected_rows: int = EXPECTED_REAL_ROWS,
    strict_accepted_identity: bool = True,
) -> list[Mapping[str, Any]]:
    """Independently validate completeness, identity, row order, and row semantics."""

    if strict_accepted_identity:
        _require(raw.get("candidate_id") == CANDIDATE_ID, "candidate identity drifted")
        _require(raw.get("treatment_id") == "VSP05-A1-TRUTH-REACHABILITY-DECOMPOSITION", "A1 treatment identity drifted")
        _require(raw.get("config_name") == "full", "A1 input is not the accepted full configuration")
        _require(raw.get("code_revision") == EXPECTED_SOURCE_COMMIT, "A1 source commit drifted")
        _require(raw.get("formal") is False, "A1 formal flag drifted")
    rows = raw.get("real_frontier_rows")
    _require(isinstance(rows, list), "real_frontier_rows is unavailable")
    _require(len(rows) == expected_rows, f"retained real-row count drifted: {len(rows)} != {expected_rows}")
    ids: set[str] = set()
    prior_order: dict[tuple[str, int, int], int] = {}
    lineage_ranks: dict[tuple[str, int, int, str], int] = {}
    for index, row in enumerate(rows):
        _require(isinstance(row, Mapping), f"row {index} is not an object")
        _validate_row(row, index)
        row_id = str(row["real_frontier_id"])
        _require(row_id not in ids, f"duplicate retained row identity: {row_id}")
        ids.add(row_id)
        episode_key = (str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]))
        current = int(row["environment_step"])
        previous = prior_order.get(episode_key)
        _require(previous is None or current >= previous, "retained row temporal order drifted")
        prior_order[episode_key] = current
        lineage = (*episode_key, str(row["lifecycle_key"]))
        expected_rank = lineage_ranks.get(lineage, 0) + 1
        _require(int(row["event_rank"]) == expected_rank, "lifecycle event rank is missing, duplicated, or reordered")
        lineage_ranks[lineage] = expected_rank
    static_rows = raw.get("static_hypothetical_incumbent_rows")
    if strict_accepted_identity:
        _require(isinstance(static_rows, list), "accepted A1 static-row container is absent")
        _require(len(static_rows) == EXPECTED_STATIC_ROWS, "accepted A1 static-row count drifted")
    return rows


def _row_labels(row: Mapping[str, Any]) -> dict[str, Any]:
    i = row["incumbent_skill"]
    q = int(row["actual_proposal"])
    eligible = i is not None and q != int(i)
    g_i = t_i = False
    if i is not None:
        g_i, t_i = _classification(row, int(i))
    g_q, t_q = _classification(row, q)
    if not eligible:
        target_class = "INELIGIBLE"
        sham_class = "INELIGIBLE"
    else:
        target_class = (
            "TARGET_POSITIVE" if g_i and t_i else
            "TARGET_TYPED_ALIAS" if g_i else
            "TARGET_GATE_NEGATIVE"
        )
        sham_class = (
            "SHAM_POSITIVE" if g_q and t_q else
            "SHAM_TYPED_ALIAS" if g_q else
            "SHAM_GATE_NEGATIVE"
        )
    return {
        "i": i,
        "q": q,
        "eligible": eligible,
        "G_i": g_i,
        "T_i": t_i,
        "G_q": g_q,
        "T_q": t_q,
        "target_class": target_class,
        "sham_class": sham_class,
    }


def _derive_epoch_bookkeeping(
    rows: Sequence[Mapping[str, Any]], labels: Sequence[MutableMapping[str, Any]]
) -> dict[str, Any]:
    states: dict[tuple[str, int, int, str], _EpochState] = {}
    target_first_latches = sham_first_latches = 0
    target_latched_rows = sham_latched_rows = 0
    pending_target_rows = pending_sham_rows = 0
    epochs: set[tuple[str, int, int, str, int]] = set()
    for row, label in zip(rows, labels):
        lineage = (
            str(row["cell"]), int(row["task_seed"]), int(row["episode_id"]),
            str(row["lifecycle_key"]),
        )
        state = states.setdefault(lineage, _EpochState())
        i = label["i"]
        if not state.initialized or state.incumbent != i:
            state.epoch_index += 1
            state.incumbent = i
            state.initialized = True
            state.target_latch = False
            state.target_pending_q = None
            state.sham_latch = False
            state.sham_pending_q = None
        epochs.add((*lineage, state.epoch_index))
        label["incumbent_epoch"] = state.epoch_index
        label["target_latch_before"] = state.target_latch
        label["sham_latch_before"] = state.sham_latch
        if label["eligible"] and label["G_i"] and not state.target_latch:
            state.target_latch = True
            state.target_pending_q = int(label["q"])
            target_first_latches += 1
        if label["eligible"] and label["G_q"] and not state.sham_latch:
            state.sham_latch = True
            state.sham_pending_q = int(label["q"])
            sham_first_latches += 1
        label["derived_target_completion_latch"] = state.target_latch
        label["derived_target_pending_q"] = state.target_pending_q
        label["derived_sham_completion_latch"] = state.sham_latch
        label["derived_sham_pending_q"] = state.sham_pending_q
        target_latched_rows += state.target_latch
        sham_latched_rows += state.sham_latch
        pending_target_rows += state.target_pending_q is not None
        pending_sham_rows += state.sham_pending_q is not None
    return {
        "derivation_kind": "OFFLINE_DERIVED_BOOKKEEPING_NOT_RUNTIME_OBSERVATION",
        "incumbent_epochs": len(epochs),
        "target_first_latches": target_first_latches,
        "target_latched_rows": target_latched_rows,
        "target_pending_rows": pending_target_rows,
        "sham_first_latches": sham_first_latches,
        "sham_latched_rows": sham_latched_rows,
        "sham_pending_rows": pending_sham_rows,
        "idempotent_within_epoch": True,
    }


def _count_classes(labels: Iterable[Mapping[str, Any]], field: str, domain: Sequence[str]) -> dict[str, int]:
    counts = Counter(str(label[field]) for label in labels)
    return {value: int(counts[value]) for value in domain}


def _marginal(
    rows: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    domain: Sequence[tuple[Any, ...]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for values in domain:
        selected = [
            label for row, label in zip(rows, labels)
            if all(row[field] == value for field, value in zip(fields, values))
        ]
        output.append({
            **{field: value for field, value in zip(fields, values)},
            "rows": len(selected),
            "target_classes": _count_classes(selected, "target_class", TARGET_CLASSES),
            "sham_classes": _count_classes(selected, "sham_class", SHAM_CLASSES),
        })
    return output


def _zero_bearing_tables(
    rows: Sequence[Mapping[str, Any]], labels: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    return {
        "by_cell": _marginal(rows, labels, ("cell",), tuple((x,) for x in CELLS)),
        "by_seed": _marginal(rows, labels, ("task_seed",), tuple((x,) for x in TASK_SEEDS)),
        "by_cell_seed": _marginal(
            rows, labels, ("cell", "task_seed"),
            tuple((cell, seed) for cell in CELLS for seed in TASK_SEEDS),
        ),
        "by_lifecycle_category": _marginal(
            rows, labels, ("lifecycle_category",),
            tuple((x,) for x in LIFECYCLE_CATEGORIES),
        ),
        "by_incumbent_i": _marginal(
            rows, labels, ("incumbent_skill",), ((None,), (0,), (1,), (2,)),
        ),
        "by_proposal_q": _marginal(
            rows, labels, ("actual_proposal",), tuple((x,) for x in SKILLS),
        ),
        "joint_target_sham_class": [
            {
                "target_class": target,
                "sham_class": sham,
                "count": sum(
                    label["target_class"] == target and label["sham_class"] == sham
                    for label in labels
                ),
            }
            for target in TARGET_CLASSES for sham in SHAM_CLASSES
        ],
    }


def _group_key(row: Mapping[str, Any], label: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        label["i"], label["q"], row["lifecycle_category"], label["eligible"],
        label["G_i"], label["G_q"], label["derived_target_completion_latch"],
        label["derived_target_pending_q"], label["derived_sham_completion_latch"],
        label["derived_sham_pending_q"],
    )


GROUP_FIELDS = (
    "i", "q", "current_membership_category", "D", "G_i", "G_q",
    "gate_derived_target_latch", "gate_derived_target_pending_q",
    "gate_derived_sham_latch", "gate_derived_sham_pending_q",
)
NULL_EXCLUDED_FIELDS = (
    "row/seed/episode/time keys",
    "arbitrary trace memory",
    "strict truth",
    "reward",
    "future outcome/state/action",
)
CANONICAL_NULL_FIELDS = (
    "i", "q", "current_membership_category", "D", "G_i",
    "gate_derived_completion_latch", "gate_derived_pending_q",
)
CANONICAL_CONTROLLER_TEXT = (
    "retain actual incumbent i; queue unchanged logged q; latch from E and G_i "
    "alone; preserve q until the existing actual handoff allowlist commits it; "
    "change executor identity only after commit"
)


def _finite_categorical_reduction(
    rows: Sequence[Mapping[str, Any]], labels: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    witnesses: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row, label in zip(rows, labels):
        if not label["eligible"]:
            continue
        key = _group_key(row, label)
        grouped[key].append(label)
        if len(witnesses[key]) < 4:
            witnesses[key].append(str(row["real_frontier_id"]))
    table: list[dict[str, Any]] = []
    mixed = 0
    for key in sorted(grouped, key=lambda item: tuple("" if x is None else str(x) for x in item)):
        members = grouped[key]
        counts = _count_classes(members, "target_class", TARGET_CLASSES)
        present = [name for name, count in counts.items() if count]
        is_mixed = len(present) > 1
        mixed += is_mixed
        table.append({
            **dict(zip(GROUP_FIELDS, key)),
            "rows": len(members),
            "target_classes": counts,
            "mixed_target_partition": is_mixed,
            "row_identity_witnesses": witnesses[key],
        })
    return {
        "permitted_fields": list(GROUP_FIELDS),
        "causally_prior_actual_handoff_flags_available": [],
        "missing_handoff_flags_imputed": False,
        "excluded_fields": list(NULL_EXCLUDED_FIELDS),
        "groups": table,
        "group_count": len(table),
        "mixed_group_count": mixed,
        "reproduces_complete_target_partition": bool(table) and mixed == 0,
        "mixed_groups_are_non_reducibility_witnesses": True,
    }


def _canonical_gate_controller_null(
    rows: Sequence[Mapping[str, Any]], labels: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    fields = CANONICAL_NULL_FIELDS
    outputs: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    witnesses: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for row, label in zip(rows, labels):
        if not label["eligible"]:
            continue
        output = (
            label["i"], label["q"], row["lifecycle_category"], label["eligible"],
            label["G_i"], label["derived_target_completion_latch"],
            label["derived_target_pending_q"],
        )
        outputs[output][str(label["target_class"])] += 1
        if len(witnesses[output]) < 4:
            witnesses[output].append(str(row["real_frontier_id"]))
    rows_out = []
    for output in sorted(outputs, key=lambda item: tuple("" if x is None else str(x) for x in item)):
        counts = {name: int(outputs[output][name]) for name in TARGET_CLASSES}
        rows_out.append({
            **dict(zip(fields, output)),
            "controller_output": (
                "RETAIN_I_QUEUE_Q_LATCHED" if output[5]
                else "RETAIN_I_QUEUE_Q_UNLATCHED"
            ),
            "target_classes": counts,
            "mixed_target_partition": sum(value > 0 for value in counts.values()) > 1,
            "row_identity_witnesses": witnesses[output],
        })
    reproduces = bool(rows_out) and not any(row["mixed_target_partition"] for row in rows_out)
    return {
        "controller": CANONICAL_CONTROLLER_TEXT,
        "permitted_fields": list(fields),
        "truth_reward_future_fields_used": False,
        "output_partition": rows_out,
        "reproduces_complete_target_partition": reproduces,
    }


ROW_BEHAVIOR_FIELDS = {
    "observed_pending_q": "pending_successor_skill",
    "observed_completion_latch": "completion_latch_state",
    "actual_commit_to_q": "actual_commit_to_proposal",
    "post_commit_incumbent_q": "post_commit_incumbent_skill",
    "first_supplied_executor_q_input_and_primitive": "first_subsequent_supplied_executor",
}


def _behavioral_addressability(
    raw: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], labels: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    missing: dict[str, Any] = {}
    for semantic_object, field in ROW_BEHAVIOR_FIELDS.items():
        present = sum(field in row for row in rows)
        if present == 0:
            missing[semantic_object] = {
                "required_field": field,
                "rows_present": present,
                "minimum_rows_required": 1,
                "status": "MISSING_RETAINED_OBSERVABLE",
            }
    handoff = raw.get("handoff_contract")
    latch_necessary = (
        isinstance(handoff, Mapping)
        and handoff.get("completion_latch_necessary_commit_input") is True
    )
    if not latch_necessary:
        missing["necessary_latch_input_witness"] = {
            "required_object": "handoff_contract.completion_latch_necessary_commit_input=true",
            "status": "MISSING_RETAINED_OBSERVABLE",
        }
    witnesses: list[dict[str, Any]] = []
    if not missing:
        for row, label in zip(rows, labels):
            executor = row["first_subsequent_supplied_executor"]
            if not isinstance(executor, Mapping):
                continue
            if (
                label["eligible"]
                and row["pending_successor_skill"] == label["q"]
                and row["completion_latch_state"] is True
                and row["actual_commit_to_proposal"] is True
                and row["post_commit_incumbent_skill"] == label["q"]
                and executor.get("skill_input") == label["q"]
                and executor.get("primitive_command") is not None
            ):
                witnesses.append({
                    "real_frontier_id": row["real_frontier_id"],
                    "pre_commit_i": label["i"],
                    "pending_q": label["q"],
                    "post_commit_i": row["post_commit_incumbent_skill"],
                    "executor_skill_input": executor["skill_input"],
                    "primitive_command": executor["primitive_command"],
                    "proves_truth_or_learner_causation": False,
                })
    return {
        "required_observables_complete": not missing,
        "missing_object_witnesses": missing,
        "actual_commit_to_executor_witness_count": len(witnesses),
        "actual_commit_to_executor_witnesses": witnesses[:16],
        "completion_latch_is_necessary_handoff_input": latch_necessary,
        "derived_latch_is_observed_witness": False,
    }


def _descriptive_counts(labels: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "complete_population": len(labels),
        "eligible": sum(label["eligible"] for label in labels),
        "target_positive": sum(label["target_class"] == "TARGET_POSITIVE" for label in labels),
        "target_typed_alias": sum(label["target_class"] == "TARGET_TYPED_ALIAS" for label in labels),
        "target_gate_negative": sum(label["target_class"] == "TARGET_GATE_NEGATIVE" for label in labels),
        "sham_positive": sum(label["sham_class"] == "SHAM_POSITIVE" for label in labels),
        "sham_typed_alias": sum(label["sham_class"] == "SHAM_TYPED_ALIAS" for label in labels),
        "sham_gate_negative": sum(label["sham_class"] == "SHAM_GATE_NEGATIVE" for label in labels),
        "ineligible": sum(label["target_class"] == "INELIGIBLE" for label in labels),
        "ineligible_join": sum(
            label["target_class"] == "INELIGIBLE" and label["i"] is None
            for label in labels
        ),
    }


def _choose_terminal_branch(
    *,
    contract_failures: Sequence[Mapping[str, Any]],
    counts: Mapping[str, int],
    target_sham_identical: bool,
    canonical_null: Mapping[str, Any],
    categorical_null: Mapping[str, Any],
    behavior: Mapping[str, Any],
) -> str:
    if contract_failures or not behavior["required_observables_complete"]:
        return TERMINAL_BRANCHES[0]
    if counts["target_positive"] == 0 or counts["target_typed_alias"] == 0:
        return TERMINAL_BRANCHES[1]
    if (
        target_sham_identical
        or canonical_null["reproduces_complete_target_partition"]
        or categorical_null["reproduces_complete_target_partition"]
    ):
        return TERMINAL_BRANCHES[2]
    if (
        behavior["actual_commit_to_executor_witness_count"] == 0
        or not behavior["completion_latch_is_necessary_handoff_input"]
    ):
        return TERMINAL_BRANCHES[3]
    if counts["sham_positive"] == 0 or counts["sham_typed_alias"] == 0:
        return TERMINAL_BRANCHES[4]
    return TERMINAL_BRANCHES[5]


def audit_retained_rows(
    raw: Mapping[str, Any],
    *,
    source_binding: SourceBinding,
    expected_rows: int = EXPECTED_REAL_ROWS,
    strict_accepted_identity: bool = True,
) -> dict[str, Any]:
    """Perform the deterministic audit without acquiring or reconstructing data."""

    rows = validate_retained_population(
        raw, expected_rows=expected_rows, strict_accepted_identity=strict_accepted_identity
    )
    labels: list[MutableMapping[str, Any]] = [dict(_row_labels(row)) for row in rows]
    bookkeeping = _derive_epoch_bookkeeping(rows, labels)
    counts = _descriptive_counts(labels)
    contract_failures: list[dict[str, Any]] = []
    if strict_accepted_identity:
        for name, expected in EXPECTED_DESCRIPTIVE_COUNTS.items():
            if counts[name] != expected:
                contract_failures.append({
                    "kind": "DESCRIPTIVE_COUNT_DRIFT",
                    "field": name,
                    "expected": expected,
                    "actual": counts[name],
                })
    target_sham_identical = all(
        label["target_class"].replace("TARGET_", "")
        == label["sham_class"].replace("SHAM_", "")
        for label in labels
    )
    canonical_null = _canonical_gate_controller_null(rows, labels)
    categorical_null = _finite_categorical_reduction(rows, labels)
    descriptive_contract_failures = list(contract_failures)
    behavior = _behavioral_addressability(raw, rows, labels)
    if not behavior["required_observables_complete"]:
        contract_failures.append({
            "kind": "REQUIRED_BEHAVIORAL_OBSERVABLES_MISSING",
            "missing_objects": sorted(behavior["missing_object_witnesses"]),
        })
    branch = _choose_terminal_branch(
        contract_failures=contract_failures,
        counts=counts,
        target_sham_identical=target_sham_identical,
        canonical_null=canonical_null,
        categorical_null=categorical_null,
        behavior=behavior,
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A3_RETAINED_ROW_OFFLINE_AUDIT",
        "stage": "post_a2_descriptive_audit",
        "evidence_level": "A_POST_OUTCOME_DESCRIPTIVE",
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "source_binding": {
            "path": source_binding.path,
            "sha256": source_binding.sha256,
            "bytes_read": source_binding.bytes_read,
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "accepted_result_commit": EXPECTED_RESULT_COMMIT,
            "real_rows_read": len(rows),
            "static_hypothetical_rows_used_as_reachable_evidence": 0,
        },
        "label_definition": {
            "completion_subject": "actual_persisted_incumbent_i",
            "proposal": "unchanged_logged_q",
            "eligibility": "F and I and q != i",
            "target_positive": "E and G_i and T_i",
            "target_typed_alias": "E and G_i and not T_i",
            "sham_positive": "E and G_q and T_q",
            "sham_typed_alias": "E and G_q and not T_q",
            "q_subject_aliases_relabelled_as_i_subject": 0,
            "future_or_outcome_fields_used": [],
        },
        "descriptive_counts": counts,
        "expected_count_receipt": {
            "accepted_expectation_applied": strict_accepted_identity,
            "expected": EXPECTED_DESCRIPTIVE_COUNTS if strict_accepted_identity else None,
            "finite_categorical_reduction_observed_after_epoch_derivation": {
                "group_count": categorical_null["group_count"],
                "mixed_group_count": categorical_null["mixed_group_count"],
            },
            "matched": not descriptive_contract_failures,
            "failures": descriptive_contract_failures,
            "q_subject_alias_141_preserved_not_relabelled": counts["sham_typed_alias"] == 141,
        },
        "same_subject_truth_gate_integrity": {
            "all_strict_truth_implies_same_subject_gate": True,
            "fresh_i_subject_labels_recomputed_from_all_skill_classification": True,
            "fresh_q_subject_labels_recomputed_from_all_skill_classification": True,
        },
        "derived_bookkeeping": bookkeeping,
        "canonical_gate_controller_null": canonical_null,
        "finite_categorical_reduction": categorical_null,
        "target_sham_partitions_identical": target_sham_identical,
        "zero_bearing_tables": _zero_bearing_tables(rows, labels),
        "behavioral_addressability": behavior,
        "contract_failures": contract_failures,
        "terminal_branch": branch,
        "branch_precedence_applied": list(TERMINAL_BRANCHES),
        "audit_activity": {
            "registered_offline_audits": 1,
            "new_trace_passes": 0,
            "environment_episodes": 0,
            "environment_transitions": 0,
            "hypothetical_transitions": 0,
            "proposal_calls": 0,
            "executor_calls": 0,
            "learner_calls": 0,
            "trainer_calls": 0,
            "optimizer_updates": 0,
            "evaluations": 0,
            "retries_or_recoveries": 0,
        },
        "claim_boundary": (
            "post-A2 descriptive reanalysis of exactly the accepted A1 retained real rows; "
            "not independent confirmation, A1/A2 repair, learner-route reactivation, or a B design"
        ),
        "scientific_disposition": None,
        "successor_selected": False,
    }
    validate_audit_result(
        result,
        expected_rows=expected_rows,
        strict_accepted_identity=strict_accepted_identity,
        recomputation_rows=rows,
        recomputation_labels=labels,
    )
    return result


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    _require(set(value) == expected, f"{name} fields drifted")


def _require_nonnegative_int(value: Any, name: str) -> int:
    _require(type(value) is int and value >= 0, f"{name} must be a nonnegative integer")
    return int(value)


def _validate_class_partition(
    value: Any, domain: Sequence[str], expected_total: int, name: str
) -> dict[str, int]:
    _require(isinstance(value, Mapping), f"{name} is absent")
    _require_exact_keys(value, set(domain), name)
    counts = {
        key: _require_nonnegative_int(value[key], f"{name}.{key}")
        for key in domain
    }
    _require(sum(counts.values()) == expected_total, f"{name} total drifted")
    return counts


def _expected_behavior_missing_receipts() -> dict[str, Any]:
    receipts = {
        semantic: {
            "required_field": field,
            "rows_present": 0,
            "minimum_rows_required": 1,
            "status": "MISSING_RETAINED_OBSERVABLE",
        }
        for semantic, field in ROW_BEHAVIOR_FIELDS.items()
    }
    receipts["necessary_latch_input_witness"] = {
        "required_object": "handoff_contract.completion_latch_necessary_commit_input=true",
        "status": "MISSING_RETAINED_OBSERVABLE",
    }
    return receipts


def _validate_zero_bearing_tables(
    value: Any, counts: Mapping[str, int], expected_rows: int
) -> None:
    _require(isinstance(value, Mapping), "zero-bearing tables are absent")
    domains: dict[str, tuple[tuple[str, ...], tuple[tuple[Any, ...], ...]]] = {
        "by_cell": (("cell",), tuple((x,) for x in CELLS)),
        "by_seed": (("task_seed",), tuple((x,) for x in TASK_SEEDS)),
        "by_cell_seed": (
            ("cell", "task_seed"),
            tuple((cell, seed) for cell in CELLS for seed in TASK_SEEDS),
        ),
        "by_lifecycle_category": (
            ("lifecycle_category",), tuple((x,) for x in LIFECYCLE_CATEGORIES),
        ),
        "by_incumbent_i": (("incumbent_skill",), ((None,), (0,), (1,), (2,))),
        "by_proposal_q": (("actual_proposal",), tuple((x,) for x in SKILLS)),
    }
    _require_exact_keys(value, set(domains) | {"joint_target_sham_class"}, "zero-bearing tables")
    target_totals = {
        "INELIGIBLE": counts["ineligible"],
        "TARGET_GATE_NEGATIVE": counts["target_gate_negative"],
        "TARGET_POSITIVE": counts["target_positive"],
        "TARGET_TYPED_ALIAS": counts["target_typed_alias"],
    }
    sham_totals = {
        "INELIGIBLE": counts["ineligible"],
        "SHAM_GATE_NEGATIVE": counts["sham_gate_negative"],
        "SHAM_POSITIVE": counts["sham_positive"],
        "SHAM_TYPED_ALIAS": counts["sham_typed_alias"],
    }
    validated_marginals: dict[str, dict[tuple[Any, ...], Mapping[str, Any]]] = {}
    for table_name, (fields, domain) in domains.items():
        table = value[table_name]
        _require(isinstance(table, list), f"{table_name} is not a table")
        _require(len(table) == len(domain), f"{table_name} zero-bearing domain size drifted")
        seen: set[tuple[Any, ...]] = set()
        table_rows = 0
        target_aggregate = Counter({key: 0 for key in TARGET_CLASSES})
        sham_aggregate = Counter({key: 0 for key in SHAM_CLASSES})
        expected_fields = set(fields) | {"rows", "target_classes", "sham_classes"}
        for index, entry in enumerate(table):
            _require(isinstance(entry, Mapping), f"{table_name}[{index}] is not an object")
            _require_exact_keys(entry, expected_fields, f"{table_name}[{index}]")
            key = tuple(entry[field] for field in fields)
            _require(key not in seen, f"{table_name} contains a duplicate stratum")
            seen.add(key)
            row_count = _require_nonnegative_int(entry["rows"], f"{table_name}[{index}].rows")
            target = _validate_class_partition(
                entry["target_classes"], TARGET_CLASSES, row_count,
                f"{table_name}[{index}].target_classes",
            )
            sham = _validate_class_partition(
                entry["sham_classes"], SHAM_CLASSES, row_count,
                f"{table_name}[{index}].sham_classes",
            )
            table_rows += row_count
            target_aggregate.update(target)
            sham_aggregate.update(sham)
        _require(seen == set(domain), f"{table_name} zero-bearing domain drifted")
        _require(table_rows == expected_rows, f"{table_name} row total drifted")
        _require(dict(target_aggregate) == target_totals, f"{table_name} target totals drifted")
        _require(dict(sham_aggregate) == sham_totals, f"{table_name} sham totals drifted")
        validated_marginals[table_name] = {
            tuple(entry[field] for field in fields): entry for entry in table
        }

    cell_seed = validated_marginals["by_cell_seed"]
    for cell in CELLS:
        entries = [cell_seed[(cell, seed)] for seed in TASK_SEEDS]
        expected_cell = validated_marginals["by_cell"][(cell,)]
        _require(
            expected_cell["rows"] == sum(entry["rows"] for entry in entries)
            and expected_cell["target_classes"] == {
                name: sum(entry["target_classes"][name] for entry in entries)
                for name in TARGET_CLASSES
            }
            and expected_cell["sham_classes"] == {
                name: sum(entry["sham_classes"][name] for entry in entries)
                for name in SHAM_CLASSES
            },
            "by_cell does not reconcile with by_cell_seed",
        )
    for seed in TASK_SEEDS:
        entries = [cell_seed[(cell, seed)] for cell in CELLS]
        expected_seed = validated_marginals["by_seed"][(seed,)]
        _require(
            expected_seed["rows"] == sum(entry["rows"] for entry in entries)
            and expected_seed["target_classes"] == {
                name: sum(entry["target_classes"][name] for entry in entries)
                for name in TARGET_CLASSES
            }
            and expected_seed["sham_classes"] == {
                name: sum(entry["sham_classes"][name] for entry in entries)
                for name in SHAM_CLASSES
            },
            "by_seed does not reconcile with by_cell_seed",
        )
    join = validated_marginals["by_lifecycle_category"][("JOIN",)]
    _require(
        join["target_classes"]["INELIGIBLE"] == join["rows"]
        and join["sham_classes"]["INELIGIBLE"] == join["rows"]
        and counts["ineligible_join"] == join["rows"],
        "ineligible_join does not equal the JOIN lifecycle stratum",
    )

    joint = value["joint_target_sham_class"]
    joint_domain = {(target, sham) for target in TARGET_CLASSES for sham in SHAM_CLASSES}
    _require(isinstance(joint, list), "joint target/sham table is absent")
    _require(len(joint) == len(joint_domain), "joint target/sham zero-bearing domain size drifted")
    seen_joint: set[tuple[str, str]] = set()
    target_joint = Counter({key: 0 for key in TARGET_CLASSES})
    sham_joint = Counter({key: 0 for key in SHAM_CLASSES})
    for index, entry in enumerate(joint):
        _require(isinstance(entry, Mapping), f"joint target/sham row {index} is not an object")
        _require_exact_keys(
            entry, {"target_class", "sham_class", "count"},
            f"joint target/sham row {index}",
        )
        key = (entry["target_class"], entry["sham_class"])
        _require(key not in seen_joint, "joint target/sham table contains a duplicate stratum")
        seen_joint.add(key)
        cell_count = _require_nonnegative_int(entry["count"], f"joint target/sham row {index}.count")
        target_joint[key[0]] += cell_count
        sham_joint[key[1]] += cell_count
    _require(seen_joint == joint_domain, "joint target/sham zero-bearing domain drifted")
    _require(dict(target_joint) == target_totals, "joint target totals drifted")
    _require(dict(sham_joint) == sham_totals, "joint sham totals drifted")


def _validate_null_receipts(
    canonical: Any, categorical: Any, eligible_rows: int
) -> None:
    _require(isinstance(canonical, Mapping), "canonical controller null is absent")
    _require_exact_keys(
        canonical,
        {
            "controller", "permitted_fields", "truth_reward_future_fields_used",
            "output_partition", "reproduces_complete_target_partition",
        },
        "canonical controller null",
    )
    _require(canonical["permitted_fields"] == list(CANONICAL_NULL_FIELDS), "canonical null fields drifted")
    _require(canonical["controller"] == CANONICAL_CONTROLLER_TEXT, "canonical controller text drifted")
    _require(canonical["truth_reward_future_fields_used"] is False, "canonical null used protected fields")
    outputs = canonical["output_partition"]
    _require(isinstance(outputs, list), "canonical null output partition is absent")
    canonical_total = 0
    canonical_mixed = 0
    canonical_target = Counter({key: 0 for key in TARGET_CLASSES})
    canonical_keys: set[tuple[Any, ...]] = set()
    canonical_projection: dict[tuple[Any, ...], dict[str, int]] = {}
    output_fields = set(CANONICAL_NULL_FIELDS) | {
        "controller_output", "target_classes", "mixed_target_partition",
        "row_identity_witnesses",
    }
    for index, entry in enumerate(outputs):
        _require(isinstance(entry, Mapping), f"canonical null row {index} is not an object")
        _require_exact_keys(entry, output_fields, f"canonical null row {index}")
        key = tuple(entry[field] for field in CANONICAL_NULL_FIELDS)
        _require(key not in canonical_keys, "canonical null contains a duplicate output")
        canonical_keys.add(key)
        row_total = sum(
            _require_nonnegative_int(entry["target_classes"].get(name), f"canonical null row {index}.{name}")
            for name in TARGET_CLASSES
        ) if isinstance(entry["target_classes"], Mapping) else -1
        target = _validate_class_partition(
            entry["target_classes"], TARGET_CLASSES, row_total,
            f"canonical null row {index}.target_classes",
        )
        _require(row_total > 0 and target["INELIGIBLE"] == 0, "canonical null row is not eligible support")
        is_mixed = sum(value > 0 for value in target.values()) > 1
        _require(entry["mixed_target_partition"] is is_mixed, "canonical null mixed flag drifted")
        latch = entry["gate_derived_completion_latch"]
        pending = entry["gate_derived_pending_q"]
        _require(_is_bool(latch), "canonical null latch must be boolean")
        _require((pending in SKILLS) if latch else pending is None, "canonical null pending/latch receipt drifted")
        expected_output = "RETAIN_I_QUEUE_Q_LATCHED" if latch else "RETAIN_I_QUEUE_Q_UNLATCHED"
        _require(entry["controller_output"] == expected_output, "canonical controller output drifted")
        witnesses = entry["row_identity_witnesses"]
        _require(
            isinstance(witnesses, list) and 0 < len(witnesses) <= 4
            and all(isinstance(item, str) for item in witnesses),
            "canonical null row witnesses drifted",
        )
        canonical_total += row_total
        canonical_mixed += is_mixed
        canonical_target.update(target)
        canonical_projection[key] = target
    _require(canonical_total == eligible_rows, "canonical null eligible total drifted")
    expected_reproduction = bool(outputs) and canonical_mixed == 0
    _require(
        canonical["reproduces_complete_target_partition"] is expected_reproduction,
        "canonical null reproduction receipt drifted",
    )

    _require(isinstance(categorical, Mapping), "finite categorical reduction is absent")
    _require_exact_keys(
        categorical,
        {
            "permitted_fields", "causally_prior_actual_handoff_flags_available",
            "missing_handoff_flags_imputed", "excluded_fields", "groups", "group_count",
            "mixed_group_count", "reproduces_complete_target_partition",
            "mixed_groups_are_non_reducibility_witnesses",
        },
        "finite categorical reduction",
    )
    _require(categorical["permitted_fields"] == list(GROUP_FIELDS), "categorical null fields drifted")
    _require(
        categorical["causally_prior_actual_handoff_flags_available"] == []
        and categorical["missing_handoff_flags_imputed"] is False,
        "categorical null handoff-flag receipt drifted",
    )
    _require(categorical["excluded_fields"] == list(NULL_EXCLUDED_FIELDS), "categorical null exclusions drifted")
    _require(categorical["mixed_groups_are_non_reducibility_witnesses"] is True, "categorical witness meaning drifted")
    groups = categorical["groups"]
    _require(isinstance(groups, list), "categorical groups are absent")
    group_fields = set(GROUP_FIELDS) | {
        "rows", "target_classes", "mixed_target_partition", "row_identity_witnesses",
    }
    group_keys: set[tuple[Any, ...]] = set()
    categorical_total = 0
    categorical_mixed = 0
    categorical_target = Counter({key: 0 for key in TARGET_CLASSES})
    categorical_projection: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    for index, entry in enumerate(groups):
        _require(isinstance(entry, Mapping), f"categorical group {index} is not an object")
        _require_exact_keys(entry, group_fields, f"categorical group {index}")
        key = tuple(entry[field] for field in GROUP_FIELDS)
        _require(key not in group_keys, "categorical reduction contains a duplicate group")
        group_keys.add(key)
        row_count = _require_nonnegative_int(entry["rows"], f"categorical group {index}.rows")
        _require(row_count > 0, "categorical group has no support")
        target = _validate_class_partition(
            entry["target_classes"], TARGET_CLASSES, row_count,
            f"categorical group {index}.target_classes",
        )
        _require(target["INELIGIBLE"] == 0, "categorical group contains ineligible rows")
        is_mixed = sum(value > 0 for value in target.values()) > 1
        _require(entry["mixed_target_partition"] is is_mixed, "categorical mixed flag drifted")
        for prefix in ("target", "sham"):
            latch = entry[f"gate_derived_{prefix}_latch"]
            pending = entry[f"gate_derived_{prefix}_pending_q"]
            _require(_is_bool(latch), f"categorical {prefix} latch must be boolean")
            _require((pending in SKILLS) if latch else pending is None, f"categorical {prefix} pending/latch drifted")
        witnesses = entry["row_identity_witnesses"]
        _require(
            isinstance(witnesses, list) and 0 < len(witnesses) <= 4
            and all(isinstance(item, str) for item in witnesses),
            "categorical group witnesses drifted",
        )
        categorical_total += row_count
        categorical_mixed += is_mixed
        categorical_target.update(target)
        projection_key = (
            entry["i"], entry["q"], entry["current_membership_category"], entry["D"],
            entry["G_i"], entry["gate_derived_target_latch"],
            entry["gate_derived_target_pending_q"],
        )
        categorical_projection[projection_key].update(target)
    _require(categorical_total == eligible_rows, "categorical null eligible total drifted")
    _require(categorical["group_count"] == len(groups), "categorical group-count receipt drifted")
    _require(categorical["mixed_group_count"] == categorical_mixed, "categorical mixed-count receipt drifted")
    expected_categorical_reproduction = bool(groups) and categorical_mixed == 0
    _require(
        categorical["reproduces_complete_target_partition"] is expected_categorical_reproduction,
        "categorical null reproduction receipt drifted",
    )
    _require(dict(canonical_target) == dict(categorical_target), "null target totals disagree")
    _require(
        set(canonical_projection) == set(categorical_projection),
        "categorical-to-canonical projection fields disagree",
    )
    for key, target in canonical_projection.items():
        _require(
            target == {name: int(categorical_projection[key][name]) for name in TARGET_CLASSES},
            "categorical-to-canonical projection counts disagree",
        )


def validate_audit_result(
    result: Mapping[str, Any],
    *,
    expected_rows: int = EXPECTED_REAL_ROWS,
    strict_accepted_identity: bool = True,
    recomputation_rows: Sequence[Mapping[str, Any]] | None = None,
    recomputation_labels: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    """Independently reject mutations of every protected serialized receipt."""

    identities = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A3_RETAINED_ROW_OFFLINE_AUDIT",
        "stage": "post_a2_descriptive_audit",
        "evidence_level": "A_POST_OUTCOME_DESCRIPTIVE",
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
    }
    for field, expected in identities.items():
        _require(result.get(field) == expected, f"protected result identity drifted: {field}")

    source = result.get("source_binding")
    _require(isinstance(source, Mapping), "source binding receipt is absent")
    _require_exact_keys(
        source,
        {
            "path", "sha256", "bytes_read", "source_commit", "accepted_result_commit",
            "real_rows_read", "static_hypothetical_rows_used_as_reachable_evidence",
        },
        "source binding receipt",
    )
    _require_nonnegative_int(source["bytes_read"], "source bytes_read")
    _require(source["real_rows_read"] == expected_rows, "source retained-row count drifted")
    _require(
        source["static_hypothetical_rows_used_as_reachable_evidence"] == 0,
        "static hypothetical rows entered reachable evidence",
    )
    if strict_accepted_identity:
        _require(
            _is_exact_registered_input_path(Path(str(source["path"]))),
            "accepted source path drifted",
        )
        _require(source["sha256"] == EXPECTED_INPUT_SHA256, "accepted source SHA drifted")
        _require(source["source_commit"] == EXPECTED_SOURCE_COMMIT, "accepted source commit drifted")
        _require(
            source["accepted_result_commit"] == EXPECTED_RESULT_COMMIT,
            "accepted result commit drifted",
        )

    activity = result.get("audit_activity")
    _require(isinstance(activity, Mapping), "audit activity receipt is absent")
    zero_activity = {
        "new_trace_passes", "environment_episodes", "environment_transitions",
        "hypothetical_transitions", "proposal_calls", "executor_calls",
        "learner_calls", "trainer_calls", "optimizer_updates", "evaluations",
        "retries_or_recoveries",
    }
    _require_exact_keys(activity, zero_activity | {"registered_offline_audits"}, "audit activity receipt")
    _require(activity["registered_offline_audits"] == 1, "audit is not one-shot")
    for name in zero_activity:
        _require(activity[name] == 0, f"prohibited activity is nonzero: {name}")

    counts = result.get("descriptive_counts")
    _require(isinstance(counts, Mapping), "descriptive counts are absent")
    count_fields = {
        "complete_population", "eligible", "target_positive", "target_typed_alias",
        "target_gate_negative", "sham_positive", "sham_typed_alias",
        "sham_gate_negative", "ineligible", "ineligible_join",
    }
    _require_exact_keys(counts, count_fields, "descriptive counts")
    for name in count_fields:
        _require_nonnegative_int(counts[name], f"descriptive_counts.{name}")
    _require(counts["complete_population"] == expected_rows, "complete population count drifted")
    _require(
        counts["eligible"]
        == counts["target_positive"] + counts["target_typed_alias"] + counts["target_gate_negative"],
        "target classes do not partition eligibility",
    )
    _require(
        counts["eligible"]
        == counts["sham_positive"] + counts["sham_typed_alias"] + counts["sham_gate_negative"],
        "sham classes do not partition eligibility",
    )
    _require(
        counts["complete_population"] == counts["eligible"] + counts["ineligible"],
        "eligible and ineligible rows do not partition the population",
    )
    if strict_accepted_identity:
        for name, expected in EXPECTED_DESCRIPTIVE_COUNTS.items():
            _require(counts[name] == expected, f"accepted descriptive count drifted: {name}")

    label_definition = result.get("label_definition")
    _require(
        label_definition == {
            "completion_subject": "actual_persisted_incumbent_i",
            "proposal": "unchanged_logged_q",
            "eligibility": "F and I and q != i",
            "target_positive": "E and G_i and T_i",
            "target_typed_alias": "E and G_i and not T_i",
            "sham_positive": "E and G_q and T_q",
            "sham_typed_alias": "E and G_q and not T_q",
            "q_subject_aliases_relabelled_as_i_subject": 0,
            "future_or_outcome_fields_used": [],
        },
        "protected label definition drifted",
    )
    _require(
        result.get("same_subject_truth_gate_integrity") == {
            "all_strict_truth_implies_same_subject_gate": True,
            "fresh_i_subject_labels_recomputed_from_all_skill_classification": True,
            "fresh_q_subject_labels_recomputed_from_all_skill_classification": True,
        },
        "same-subject truth/gate integrity receipt drifted",
    )

    derived = result.get("derived_bookkeeping")
    _require(isinstance(derived, Mapping), "derived bookkeeping receipt is absent")
    derived_count_fields = {
        "incumbent_epochs", "target_first_latches", "target_latched_rows",
        "target_pending_rows", "sham_first_latches", "sham_latched_rows",
        "sham_pending_rows",
    }
    _require_exact_keys(
        derived,
        derived_count_fields | {"derivation_kind", "idempotent_within_epoch"},
        "derived bookkeeping receipt",
    )
    _require(
        derived["derivation_kind"] == "OFFLINE_DERIVED_BOOKKEEPING_NOT_RUNTIME_OBSERVATION",
        "derived bookkeeping kind drifted",
    )
    _require(derived["idempotent_within_epoch"] is True, "derived bookkeeping idempotence drifted")
    for name in derived_count_fields:
        _require_nonnegative_int(derived[name], f"derived_bookkeeping.{name}")
    _require(derived["target_pending_rows"] == derived["target_latched_rows"], "target pending/latch totals drifted")
    _require(derived["sham_pending_rows"] == derived["sham_latched_rows"], "sham pending/latch totals drifted")
    _require(derived["target_latched_rows"] <= expected_rows, "target latch rows exceed population")
    _require(derived["sham_latched_rows"] <= expected_rows, "sham latch rows exceed population")

    contract_failures = result.get("contract_failures")
    _require(
        isinstance(contract_failures, list)
        and all(isinstance(item, Mapping) for item in contract_failures),
        "contract failure receipt is malformed",
    )
    receipt = result.get("expected_count_receipt")
    _require(isinstance(receipt, Mapping), "expected-count receipt is absent")
    _require_exact_keys(
        receipt,
        {
            "accepted_expectation_applied", "expected",
            "finite_categorical_reduction_observed_after_epoch_derivation", "matched",
            "failures", "q_subject_alias_141_preserved_not_relabelled",
        },
        "expected-count receipt",
    )
    _require(receipt["accepted_expectation_applied"] is strict_accepted_identity, "count expectation mode drifted")
    expected_count_receipt = EXPECTED_DESCRIPTIVE_COUNTS if strict_accepted_identity else None
    _require(receipt["expected"] == expected_count_receipt, "accepted expected counts drifted")
    descriptive_failures = [
        dict(item) for item in contract_failures
        if item.get("kind") == "DESCRIPTIVE_COUNT_DRIFT"
    ]
    _require(receipt["failures"] == descriptive_failures, "descriptive failure receipt drifted")
    _require(receipt["matched"] is (not descriptive_failures), "descriptive matched receipt drifted")
    _require(
        receipt["q_subject_alias_141_preserved_not_relabelled"]
        is (counts["sham_typed_alias"] == 141),
        "q-subject alias preservation receipt drifted",
    )

    canonical = result.get("canonical_gate_controller_null")
    categorical = result.get("finite_categorical_reduction")
    _validate_null_receipts(canonical, categorical, counts["eligible"])
    _require(
        (recomputation_rows is None) == (recomputation_labels is None),
        "null recomputation inputs must be supplied together",
    )
    if recomputation_rows is not None and recomputation_labels is not None:
        _require(
            canonical == _canonical_gate_controller_null(recomputation_rows, recomputation_labels),
            "serialized canonical null disagrees with in-memory recomputation",
        )
        _require(
            categorical == _finite_categorical_reduction(recomputation_rows, recomputation_labels),
            "serialized categorical null disagrees with in-memory recomputation",
        )
    finite_receipt = receipt["finite_categorical_reduction_observed_after_epoch_derivation"]
    _require(
        finite_receipt == {
            "group_count": categorical["group_count"],
            "mixed_group_count": categorical["mixed_group_count"],
        },
        "post-derivation categorical count receipt drifted",
    )

    _validate_zero_bearing_tables(result.get("zero_bearing_tables"), counts, expected_rows)
    joint = result["zero_bearing_tables"]["joint_target_sham_class"]
    partitions_identical = all(
        entry["count"] == 0
        or entry["target_class"].replace("TARGET_", "")
        == entry["sham_class"].replace("SHAM_", "")
        for entry in joint
    )
    _require(
        result.get("target_sham_partitions_identical") is partitions_identical,
        "target/sham identity receipt drifted",
    )

    behavior = result.get("behavioral_addressability")
    _require(isinstance(behavior, Mapping), "behavioral addressability receipt is absent")
    _require_exact_keys(
        behavior,
        {
            "required_observables_complete", "missing_object_witnesses",
            "actual_commit_to_executor_witness_count", "actual_commit_to_executor_witnesses",
            "completion_latch_is_necessary_handoff_input", "derived_latch_is_observed_witness",
        },
        "behavioral addressability receipt",
    )
    missing = behavior["missing_object_witnesses"]
    _require(isinstance(missing, Mapping), "missing-observable witness map is absent")
    _require(behavior["required_observables_complete"] is (not missing), "observable completeness flag drifted")
    _require(behavior["derived_latch_is_observed_witness"] is False, "derived latch was relabelled observed")
    _require(_is_bool(behavior["completion_latch_is_necessary_handoff_input"]), "latch-input flag is not boolean")
    witness_count = _require_nonnegative_int(
        behavior["actual_commit_to_executor_witness_count"], "behavior witness count"
    )
    witnesses = behavior["actual_commit_to_executor_witnesses"]
    _require(isinstance(witnesses, list), "behavior witness table is absent")
    _require(len(witnesses) <= min(16, witness_count), "behavior witness count/table disagree")
    if strict_accepted_identity:
        _require(missing == _expected_behavior_missing_receipts(), "accepted missing-observable witnesses drifted")
        _require(behavior["required_observables_complete"] is False, "accepted observables were fabricated complete")
        _require(behavior["completion_latch_is_necessary_handoff_input"] is False, "accepted latch input was fabricated")
        _require(witness_count == 0 and witnesses == [], "accepted commit/executor witness was fabricated")
    missing_failure = [
        item for item in contract_failures
        if item.get("kind") == "REQUIRED_BEHAVIORAL_OBSERVABLES_MISSING"
    ]
    if missing:
        _require(
            missing_failure == [{
                "kind": "REQUIRED_BEHAVIORAL_OBSERVABLES_MISSING",
                "missing_objects": sorted(missing),
            }],
            "missing-observable contract failure receipt drifted",
        )
    else:
        _require(not missing_failure, "complete observables retain a missing-object failure")

    _require(result.get("branch_precedence_applied") == list(TERMINAL_BRANCHES), "branch precedence receipt drifted")
    recomputed_branch = _choose_terminal_branch(
        contract_failures=contract_failures,
        counts=counts,
        target_sham_identical=partitions_identical,
        canonical_null=canonical,
        categorical_null=categorical,
        behavior=behavior,
    )
    _require(result.get("terminal_branch") == recomputed_branch, "terminal branch precedence drifted")


def invalid_contract_result(path: str | Path, reason: str) -> dict[str, Any]:
    """Return a serializable fail-closed artifact when source binding cannot begin."""

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A3_RETAINED_ROW_OFFLINE_AUDIT",
        "stage": "post_a2_descriptive_audit",
        "evidence_level": "A_POST_OUTCOME_DESCRIPTIVE",
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "source_binding": {"path": str(path), "status": "INVALID"},
        "contract_failures": [{"kind": "SOURCE_BINDING_OR_ROW_CONTRACT", "detail": reason}],
        "terminal_branch": "A3_INVALID_CONTRACT",
        "branch_precedence_applied": list(TERMINAL_BRANCHES),
        "audit_activity": {
            "registered_offline_audits": 1,
            "new_trace_passes": 0,
            "environment_episodes": 0,
            "environment_transitions": 0,
            "hypothetical_transitions": 0,
            "proposal_calls": 0,
            "executor_calls": 0,
            "learner_calls": 0,
            "trainer_calls": 0,
            "optimizer_updates": 0,
            "evaluations": 0,
            "retries_or_recoveries": 0,
        },
        "claim_boundary": "invalid source/row contract; no scientific or successor conclusion",
        "scientific_disposition": None,
        "successor_selected": False,
    }


def run_registered_audit(input_path: str | Path) -> dict[str, Any]:
    try:
        raw, binding = load_bound_input(input_path)
        return audit_retained_rows(raw, source_binding=binding)
    except ContractViolation as exc:
        return invalid_contract_result(input_path, str(exc))


def write_result_once(path: str | Path, result: Mapping[str, Any]) -> None:
    """Publish one canonical JSON artifact without overwriting an earlier result."""

    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite one-shot A3 artifact: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dict(result), indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        # Hard-link installation is same-filesystem and fails if a concurrent
        # writer created the destination; unlike replace(), it cannot overwrite
        # an earlier one-shot artifact.
        os.link(temporary, destination)
        temporary.unlink()
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help=f"exact accepted input: {EXPECTED_INPUT_RELATIVE_PATH}")
    parser.add_argument("--output", required=True, help="new one-shot A3 JSON artifact")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_registered_audit(args.input)
    write_result_once(args.output, result)
    print(json.dumps({
        "output": str(Path(args.output)),
        "terminal_branch": result["terminal_branch"],
        "real_rows_read": result.get("source_binding", {}).get("real_rows_read", 0),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

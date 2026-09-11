"""Canonical B1 training/resource/mechanical assembly from direct raw facts.

This layer does not run an experiment and does not accept caller pass/fail
booleans.  Facts absent from worker/admission/telemetry/policy evidence are an
upstream instrumentation gap, never an inferred success.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any, Mapping, Sequence

import torch

from . import addressing
from .artifact import canonical_json_bytes
from .b0 import ARMS
from .b1_contract import B1_RESOURCE_CAPS, B1_RUN_NAME, B1_SEEDS
from .b1_mechanical import compute_raw_competence
from .b1_policy_records import ARM_ORDER
from .b1_training_records import (
    TrainingExposureRecords,
    TrainingRecordError,
    merge_training_exposure_slices,
)
from .contract import Action, DECISION_ACTION_MASK, EPISODE_TRANSITIONS, OPPORTUNITY_COUNT
from .host import DynamicHost
from .ppo import PPOConfig, config_digest, ordered_episode_indices
# The frozen caps (4 GiB RSS, 2 GiB scratch, 512 MiB durable, 120 min wall) are
# recorded budgets under the section-11 recast; a measured exceedance is
# published, not refused.  The wall cap alone stops a run, at the slot boundary.
# `RECORDED_BUDGET_CAPS` therefore does not refuse inside the assembly.
from .telemetry import RECORDED_BUDGET_CAPS, TelemetryError, validate_telemetry


ASSEMBLY_SCHEMA = "cbsc_omrc_b01_b1_metrics_training_assembly_v1"
FORMAL_ARM_SEED_ORDER = tuple((seed, arm) for seed in B1_SEEDS for arm in ARMS)
_ACTION_NAMES = ("SERVE", "REFRESH", "SAFE_FALLBACK")
_DIRECT_FIELDS = frozenset(
    {
        "active_modes",
        "reset_records",
        "checkpoint_records",
        "learner_visibility_records",
    }
)
_ADMISSION_FIELDS = frozenset(
    {
        "attempt_order",
        "attempt_id",
        "run_name",
        "seed",
        "arm",
        "receipt_sha256",
        "available_physical_bytes",
        "effective_available_bytes",
    }
)
_TELEMETRY_FIELDS = frozenset(
    {"attempt_order", "attempt_id", "run_name", "seed", "arm", "measurement"}
)
_RAW_FACT_FIELDS = frozenset(
    {
        "inventories", "resources", "digest_bindings", "tape_bindings",
        "work_bindings", "fp32_records", "numeric_records", "reset_records",
        "adaptation_records", "checkpoint_records", "learner_visibility_records",
        "legal_action_records", "twin_records", "literal_records",
    }
)
_MATERIALIZED_DIGEST_FIELDS = frozenset(
    {
        "name", "expected_sha256", "actual_sha256",
        "expected_byte_count", "actual_byte_count",
    }
)
_PENDING_DIGEST_BINDINGS = {
    "status": "PENDING_MATERIALIZATION_REREAD",
    "records": [],
}
_AUDIT_FIELDS = frozenset(
    {
        "run_order", "attempt_order", "seed_or_minus_one", "arm_or_minus_one",
        "audit_code", "authority_type", "source_table", "source_key_range",
        "source_raw_slice", "fact_name", "expected", "observed",
        "expected_sha256", "actual_sha256", "binding_status",
        "source_relative_path", "json_pointer", "source_file_sha256",
        "payload_shape", "payload_dtype", "payload_nonzero_count",
    }
)
_SOURCE_DESCRIPTOR_FIELDS = frozenset(
    {"source_relative_path", "source_file_sha256", "raw_json_pointer"}
)
_MATERIALIZED_TABLE_BINDING_FIELDS = frozenset(
    {
        "source_table", "actual_sha256", "actual_row_count",
        "actual_first_key", "actual_last_key",
    }
)
_TABLE_AUDIT_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "training_decisions": (
        "run_order", "seed", "arm_order", "training_episode_id", "opportunity_id"
    ),
    "training_episodes": ("run_order", "seed", "arm_order", "training_episode_id"),
    "optimizer_steps": (
        "run_order", "seed", "arm_order", "rollout_update", "ppo_epoch", "minibatch_index"
    ),
    "resource_admissions": (
        "run_order", "invocation_kind", "original_slot_index", "attempt_order",
        "seed", "arm_order",
    ),
    "telemetry": (
        "run_order", "invocation_kind", "original_slot_index", "attempt_order",
        "seed", "arm_order",
    ),
    "raw_competence": ("seed",),
    "policy_decisions": (
        "run_order", "seed", "checkpoint_update", "split_order", "tape_id",
        "opportunity_id", "arm_order",
    ),
    "per_tape_curves": ("run_order", "seed", "split_order", "tape_id", "arm_order"),
    "evaluator_decision_truth": (
        "run_order", "seed", "split_order", "tape_id", "opportunity_id"
    ),
    "motif_twin_index": ("run_order", "seed", "tape_id", "pair_id", "member_role"),
}
_REPLAY_RESOURCE_FIELDS = frozenset({"resource_admissions", "telemetry"})
_REPLAY_BASE_FIELDS = frozenset({
    "run_order", "invocation_kind", "original_slot_index", "attempt_order",
    "seed", "arm_order", "run_name", "arm", "attempt_id",
    "slice_start_update", "slice_stop_update",
})
_REPLAY_ADMISSION_FIELDS = _REPLAY_BASE_FIELDS | frozenset({
    "receipt_sha256", "bound_admission_relative_path", "raw_receipt_relative_path",
    "raw_receipt_sha256", "available_physical_bytes", "effective_available_bytes",
})
_REPLAY_TELEMETRY_FIELDS = _REPLAY_BASE_FIELDS | frozenset({
    "measurement", "telemetry_relative_path", "telemetry_sha256",
})


class B1MetricsTrainingAssemblyError(ValueError):
    """Canonical training/mechanical inputs are absent or contradictory."""


def _sequence(value: object, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise B1MetricsTrainingAssemblyError(f"{name} must be a sequence")
    return value


def _digest(value: object, name: str, length: int = 64) -> str:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1MetricsTrainingAssemblyError(f"{name} must be lowercase hexadecimal")
    return value


def _fraction(value: object, name: str) -> Fraction:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"numerator", "denominator"}
        or type(value["numerator"]) is not int
        or type(value["denominator"]) is not int
        or value["denominator"] <= 0
    ):
        raise B1MetricsTrainingAssemblyError(f"{name} is not an exact fraction")
    return Fraction(value["numerator"], value["denominator"])


def _ratio(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _bits_hex(value: object, name: str) -> str:
    if type(value) is str:
        if len(value) == 8 and all(character in "0123456789abcdef" for character in value):
            return value
    elif type(value) is int and 0 <= value < 2**32:
        return f"{value:08x}"
    raise B1MetricsTrainingAssemblyError(f"{name} is not an exact FP32 word")


def _key_text(*values: object) -> str:
    return "|".join(str(value) for value in values)


def _slot_identity(group: Sequence[Mapping[str, Any]]) -> tuple[int, str]:
    if not group:
        raise B1MetricsTrainingAssemblyError("raw slice group is empty")
    first = group[0]
    identity = (first.get("seed"), first.get("arm"))
    if type(identity[0]) is not int or identity[1] not in ARMS:
        raise B1MetricsTrainingAssemblyError("raw slice arm-seed identity differs")
    if any((raw.get("seed"), raw.get("arm")) != identity for raw in group):
        raise B1MetricsTrainingAssemblyError("raw slice group contains mixed arm-seed identities")
    return identity  # type: ignore[return-value]


def _validate_group_shapes(
    raw_groups: Sequence[Sequence[Mapping[str, Any]]], *, test_only: bool
) -> list[tuple[int, str]]:
    identities = [_slot_identity(group) for group in raw_groups]
    if test_only:
        if not identities or tuple(identities) != FORMAL_ARM_SEED_ORDER[: len(identities)]:
            raise B1MetricsTrainingAssemblyError("TEST_ONLY arm-seed groups must be a canonical prefix")
    elif tuple(identities) != FORMAL_ARM_SEED_ORDER:
        raise B1MetricsTrainingAssemblyError("formal arm-seed group shape differs from 12 fixed slots")
    return identities


def _training_chunk(value: object) -> TrainingExposureRecords:
    if not isinstance(value, Mapping) or set(value) != {
        "training_decisions", "training_episodes", "optimizer_steps"
    }:
        raise B1MetricsTrainingAssemblyError("raw slice training_records schema differs")
    rows: list[tuple[dict[str, Any], ...]] = []
    for name in ("training_decisions", "training_episodes", "optimizer_steps"):
        table = value[name]
        if not isinstance(table, list) or any(not isinstance(row, Mapping) for row in table):
            raise B1MetricsTrainingAssemblyError(f"{name} is not a raw row list")
        rows.append(tuple(dict(row) for row in table))
    return TrainingExposureRecords(*rows)


def _merge_training_group(
    group: Sequence[Mapping[str, Any]], identity: tuple[int, str], *, test_only: bool,
) -> TrainingExposureRecords:
    expected_start = 0
    chunks: list[TrainingExposureRecords] = []
    attempt_id: str | None = None
    for raw in group:
        if (
            raw.get("run_name") != B1_RUN_NAME
            or raw.get("scientific_branch") is not None
            or (raw.get("seed"), raw.get("arm")) != identity
        ):
            raise B1MetricsTrainingAssemblyError("raw slice run/science identity differs")
        if attempt_id is None:
            attempt_id = raw.get("attempt_id")
        if type(attempt_id) is not str or not attempt_id or raw.get("attempt_id") != attempt_id:
            raise B1MetricsTrainingAssemblyError("raw slice attempt identity differs")
        interval = raw.get("slice")
        if not isinstance(interval, Mapping) or set(interval) != {"start_update", "stop_update"}:
            raise B1MetricsTrainingAssemblyError("raw slice interval schema differs")
        start, stop = interval["start_update"], interval["stop_update"]
        if type(start) is not int or type(stop) is not int or start != expected_start or stop <= start:
            raise B1MetricsTrainingAssemblyError("raw slice interval contains a gap/overlap")
        chunks.append(_training_chunk(raw.get("training_records")))
        expected_start = stop
    if expected_start != 48:
        raise B1MetricsTrainingAssemblyError("arm-seed training slice coverage does not reach update 48")
    if test_only:
        merged = TrainingExposureRecords(
            tuple(row for chunk in chunks for row in chunk.training_decisions),
            tuple(row for chunk in chunks for row in chunk.training_episodes),
            tuple(row for chunk in chunks for row in chunk.optimizer_steps),
        )
        decision_keys = sorted(
            (row.get("training_episode_id"), row.get("opportunity_id"))
            for row in merged.training_decisions
        )
        episode_ids = sorted(row.get("training_episode_id") for row in merged.training_episodes)
        step_keys = sorted(
            (row.get("rollout_update"), row.get("ppo_epoch"), row.get("minibatch_index"))
            for row in merged.optimizer_steps
        )
        if (
            decision_keys != [
                (update, opportunity)
                for update in range(48) for opportunity in range(OPPORTUNITY_COUNT)
            ]
            or episode_ids != list(range(48))
            or step_keys != [
                (update, epoch, 0) for update in range(48) for epoch in range(4)
            ]
        ):
            raise B1MetricsTrainingAssemblyError(
                "TEST_ONLY training records must be exactly 48 updates x 1 episode"
            )
        return merged
    try:
        return merge_training_exposure_slices(
            chunks, start_update=0, stop_update=48, require_full_b1=True
        )
    except TrainingRecordError as exc:
        raise B1MetricsTrainingAssemblyError("arm-seed training records are incomplete") from exc


def _validate_admission(
    value: object, *, attempt_order: int, attempt_id: str, seed: int, arm: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != _ADMISSION_FIELDS:
        raise B1MetricsTrainingAssemblyError("direct admission fact fields differ")
    row = dict(value)
    if row["attempt_order"] != attempt_order:
        raise B1MetricsTrainingAssemblyError("direct admission attempt_order differs")
    if (
        row["attempt_id"] != attempt_id
        or row["run_name"] != B1_RUN_NAME
        or row["seed"] != seed
        or row["arm"] != arm
    ):
        raise B1MetricsTrainingAssemblyError("direct admission invocation identity differs")
    _digest(row["receipt_sha256"], "admission receipt digest")
    for field in ("available_physical_bytes", "effective_available_bytes"):
        if type(row[field]) is not int or row[field] < 0:
            raise B1MetricsTrainingAssemblyError(f"admission {field} is not a measured byte count")
    return row


def _validate_telemetry_fact(
    value: object, *, attempt_order: int, attempt_id: str, seed: int, arm: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != _TELEMETRY_FIELDS:
        raise B1MetricsTrainingAssemblyError("direct telemetry fact fields differ")
    row = dict(value)
    if row["attempt_order"] != attempt_order:
        raise B1MetricsTrainingAssemblyError("direct telemetry attempt_order differs")
    if (
        row["attempt_id"] != attempt_id
        or row["run_name"] != B1_RUN_NAME
        or row["seed"] != seed
        or row["arm"] != arm
    ):
        raise B1MetricsTrainingAssemblyError("direct telemetry invocation identity differs")
    # Section-11 recast, owner decisions 3 and 7 (2026-09-02): the resource
    # caps are recorded budgets, so a measured exceedance is published rather
    # than refused here.  Only the wall cap stops a run, and it stops it at the
    # slot boundary in `b1._load_slot_evidence`.  The measurement itself is
    # still required to be a complete, finite, nonzero-work record, because the
    # work reconciliation below is a §4 integrity item.
    try:
        row["measurement"] = validate_telemetry(
            row["measurement"], caps=RECORDED_BUDGET_CAPS, allow_missing=True
        )
    except (TypeError, TelemetryError) as exc:
        raise B1MetricsTrainingAssemblyError("direct telemetry measurement is invalid") from exc
    return row


def _validate_policy_replay_resources(
    value: object, *, attempt_id: str, test_only: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if value is None:
        if test_only:
            return [], [], []
        raise B1MetricsTrainingAssemblyError(
            "UPSTREAM_INSTRUMENTATION_GAP: formal policy replay resource witness is absent"
        )
    if not isinstance(value, Mapping) or frozenset(value) != _REPLAY_RESOURCE_FIELDS:
        raise B1MetricsTrainingAssemblyError("policy replay resource schema differs")
    admissions_value = value["resource_admissions"]
    telemetry_value = value["telemetry"]
    if not isinstance(admissions_value, list) or not isinstance(telemetry_value, list):
        raise B1MetricsTrainingAssemblyError("policy replay resource coverage differs")
    if len(admissions_value) != len(telemetry_value) or not admissions_value:
        raise B1MetricsTrainingAssemblyError("policy replay resource coverage differs")
    if not test_only and len(admissions_value) != len(FORMAL_ARM_SEED_ORDER):
        raise B1MetricsTrainingAssemblyError("formal policy replay resource coverage differs")
    admissions: list[dict[str, Any]] = []
    telemetry_rows: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []
    admission_slots = [
        row.get("original_slot_index") if isinstance(row, Mapping) else None
        for row in admissions_value
    ]
    telemetry_slots = [
        row.get("original_slot_index") if isinstance(row, Mapping) else None
        for row in telemetry_value
    ]
    if (
        any(type(slot) is not int for slot in (*admission_slots, *telemetry_slots))
        or admission_slots != sorted(admission_slots)
        or telemetry_slots != sorted(telemetry_slots)
    ):
        raise B1MetricsTrainingAssemblyError("policy replay resource order differs")
    previous_slot = -1
    for admission_value, telemetry_fact in zip(
        admissions_value, telemetry_value, strict=True
    ):
        if (
            not isinstance(admission_value, Mapping)
            or frozenset(admission_value) != _REPLAY_ADMISSION_FIELDS
            or not isinstance(telemetry_fact, Mapping)
            or frozenset(telemetry_fact) != _REPLAY_TELEMETRY_FIELDS
        ):
            raise B1MetricsTrainingAssemblyError(
                "policy replay resource row schema differs"
            )
        admission = dict(admission_value)
        telemetry = dict(telemetry_fact)
        slot = admission["original_slot_index"]
        if type(slot) is not int or not 0 <= slot < len(FORMAL_ARM_SEED_ORDER):
            raise B1MetricsTrainingAssemblyError("policy replay resource identity differs")
        if slot <= previous_slot:
            raise B1MetricsTrainingAssemblyError("policy replay resource order differs")
        previous_slot = slot
        seed, arm = FORMAL_ARM_SEED_ORDER[slot]
        arm_order = ARM_ORDER[arm]
        expected_base = {
            "run_order": 0, "invocation_kind": "POLICY_REPLAY",
            "original_slot_index": slot, "attempt_order": 0,
            "seed": seed, "arm_order": arm_order, "run_name": B1_RUN_NAME,
            "arm": arm, "attempt_id": attempt_id,
            "slice_start_update": None, "slice_stop_update": None,
        }
        if any(
            admission.get(field) != expected
            or telemetry.get(field) != expected
            for field, expected in expected_base.items()
        ):
            raise B1MetricsTrainingAssemblyError("policy replay resource identity differs")
        for field in (
            "receipt_sha256", "raw_receipt_sha256",
        ):
            _digest(admission[field], f"policy replay {field}")
        for field in (
            "bound_admission_relative_path", "raw_receipt_relative_path",
            "telemetry_relative_path",
        ):
            row = admission if field in admission else telemetry
            path = row[field]
            if (
                type(path) is not str or not path or "\\" in path
                or path.startswith("/") or any(
                    part in {"", ".", ".."} for part in path.split("/")
                )
            ):
                raise B1MetricsTrainingAssemblyError(
                    "policy replay resource relative path differs"
                )
        for field in ("available_physical_bytes", "effective_available_bytes"):
            if type(admission[field]) is not int or admission[field] < 4 * 1024**3:
                raise B1MetricsTrainingAssemblyError(
                    "policy replay admission available memory differs"
                )
        try:
            measurement = validate_telemetry(
                telemetry["measurement"], caps=RECORDED_BUDGET_CAPS, allow_missing=True
            )
        except (TypeError, TelemetryError) as exc:
            raise B1MetricsTrainingAssemblyError(
                "policy replay telemetry measurement differs"
            ) from exc
        telemetry["measurement"] = measurement
        admissions.append(admission)
        telemetry_rows.append(telemetry)
        resources.append({
            "invocation_id": f"POLICY_REPLAY:{slot:02d}",
            "physical_available_bytes": admission["available_physical_bytes"],
            "effective_available_bytes": admission["effective_available_bytes"],
            "measurement_complete": measurement["measurement_complete"],
            "wall_seconds": measurement["end_to_end_wall_seconds"],
            "peak_rss_bytes": measurement["process_tree_peak_rss_bytes"],
            "scratch_peak_bytes": measurement["scratch_high_water_bytes"],
            "durable_peak_bytes": measurement["durable_high_water_bytes"],
        })
    if not test_only and previous_slot != len(FORMAL_ARM_SEED_ORDER) - 1:
        raise B1MetricsTrainingAssemblyError("formal policy replay resource coverage differs")
    return admissions, telemetry_rows, resources


def _validate_test_only_raw_profile(
    truths: list[object], policies: list[object], curves: list[object]
) -> None:
    expected_truth = {
        (seed, split_order, 0, opportunity)
        for seed in B1_SEEDS for split_order in (1, 2) for opportunity in range(24)
    }
    observed_truth = [
        (row.get("seed"), row.get("split_order"), row.get("tape_id"), row.get("opportunity_id"))
        for row in truths if isinstance(row, Mapping) and row.get("run_order") == 0
    ]
    expected_policy = {
        (seed, checkpoint, split_order, 0, opportunity, 1)
        for seed in B1_SEEDS for checkpoint in (0, 12, 24, 48)
        for split_order in (1, 2) for opportunity in range(24)
    }
    observed_policy = [
        (row.get("seed"), row.get("checkpoint_update"), row.get("split_order"),
         row.get("tape_id"), row.get("opportunity_id"), row.get("arm_order"))
        for row in policies if isinstance(row, Mapping) and row.get("run_order") == 0
    ]
    expected_curves = {(seed, split_order, 0, 1) for seed in B1_SEEDS for split_order in (1, 2)}
    observed_curves = [
        (row.get("seed"), row.get("split_order"), row.get("tape_id"), row.get("arm_order"))
        for row in curves if isinstance(row, Mapping) and row.get("run_order") == 0
    ]
    if (
        len(observed_truth) != len(set(observed_truth))
        or set(observed_truth) != expected_truth
        or len(observed_policy) != len(set(observed_policy))
        or set(observed_policy) != expected_policy
        or len(observed_curves) != len(set(observed_curves))
        or set(observed_curves) != expected_curves
    ):
        raise B1MetricsTrainingAssemblyError(
            "TEST_ONLY RAW profile must be exactly 3 seeds x 4 checkpoints x 2 tapes"
        )


def _competence_inputs(
    shared_tables: Mapping[str, object], policy_tables: Mapping[str, object],
    *, test_only: bool,
) -> list[dict[str, Any]]:
    truths = shared_tables.get("evaluator_decision_truth")
    policies = policy_tables.get("policy_decisions")
    curves = policy_tables.get("per_tape_curves")
    for value, name in (
        (truths, "evaluator_decision_truth"),
        (policies, "policy_decisions"),
        (curves, "per_tape_curves"),
    ):
        if not isinstance(value, list):
            raise B1MetricsTrainingAssemblyError(f"{name} is absent")
    if test_only:
        _validate_test_only_raw_profile(truths, policies, curves)
    truth_index: dict[tuple[int, int, int], Mapping[str, Any]] = {}
    policy_index: dict[tuple[int, int, int], Mapping[str, Any]] = {}
    curve_index: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in truths:  # type: ignore[union-attr]
        if not isinstance(row, Mapping):
            raise B1MetricsTrainingAssemblyError("truth table contains a non-record")
        if row.get("run_order") == 0 and row.get("split_order") == 1:
            key = (row.get("seed"), row.get("tape_id"), row.get("opportunity_id"))
            if key in truth_index:
                raise B1MetricsTrainingAssemblyError("terminal stochastic truth key duplicated")
            truth_index[key] = row  # type: ignore[index]
    for row in policies:  # type: ignore[union-attr]
        if not isinstance(row, Mapping):
            raise B1MetricsTrainingAssemblyError("policy table contains a non-record")
        if (
            row.get("run_order") == 0 and row.get("arm_order") == ARM_ORDER["RAW-GRU"]
            and row.get("checkpoint_update") == 48 and row.get("split_order") == 1
        ):
            key = (row.get("seed"), row.get("tape_id"), row.get("opportunity_id"))
            if key in policy_index:
                raise B1MetricsTrainingAssemblyError("terminal RAW policy key duplicated")
            policy_index[key] = row  # type: ignore[index]
    for row in curves:  # type: ignore[union-attr]
        if not isinstance(row, Mapping):
            raise B1MetricsTrainingAssemblyError("curve table contains a non-record")
        if row.get("run_order") == 0 and row.get("arm_order") == 1 and row.get("split_order") == 1:
            key = (row.get("seed"), row.get("tape_id"))
            if key in curve_index:
                raise B1MetricsTrainingAssemblyError("terminal RAW curve key duplicated")
            curve_index[key] = row  # type: ignore[index]

    output: list[dict[str, Any]] = []
    tape_ids = (0,) if test_only else tuple(range(32))
    for seed in B1_SEEDS:
        tapes: list[dict[str, Any]] = []
        for tape_id in tape_ids:
            curve = curve_index.get((seed, tape_id))
            if curve is None or "episode_return_update_48" not in curve:
                raise B1MetricsTrainingAssemblyError("RAW checkpoint-48 same-tape curve is absent")
            raw_return = _fraction(curve["episode_return_update_48"], "RAW terminal return")
            decisions: list[dict[str, Any]] = []
            refresh_return = Fraction(0)
            safe_return = Fraction(0)
            for opportunity_id in range(24):
                key = (seed, tape_id, opportunity_id)
                truth, policy = truth_index.get(key), policy_index.get(key)
                if truth is None or policy is None:
                    raise B1MetricsTrainingAssemblyError(
                        "RAW competence truth/policy terminal decision is absent"
                    )
                selected, oracle = policy.get("selected_action"), truth.get("oracle_action")
                if selected not in (0, 1, 2) or oracle not in (0, 1, 2):
                    raise B1MetricsTrainingAssemblyError("RAW competence action code differs")
                if type(truth.get("access_gated")) is not bool:
                    raise B1MetricsTrainingAssemblyError(
                        "RAW competence access_gated fact is absent/non-Boolean"
                    )
                actor_bits = policy.get("actor_logits_fp32_bits")
                if not isinstance(actor_bits, list) or len(actor_bits) != 4:
                    raise B1MetricsTrainingAssemblyError("RAW actor logit bits are absent")
                refresh_return += _fraction(truth.get("refresh_total_value"), "refresh value")
                safe_return += _fraction(truth.get("safe_fallback_total_value"), "safe value")
                decisions.append({
                    "opportunity_id": opportunity_id,
                    "selected_action": _ACTION_NAMES[selected],
                    "oracle_action": _ACTION_NAMES[oracle],
                    "request_active": truth.get("request_active"),
                    "access_mode": "GATED" if truth.get("access_gated") is True else "OPEN",
                    "presented_body_native_neutral": truth.get("presented_body_native_neutral"),
                    "address_match_truth": truth.get("address_match_truth"),
                    "payload_source_match_truth": truth.get("payload_source_match_truth"),
                    "content_match_truth": truth.get("content_match_truth"),
                    "owner_match_truth": truth.get("owner_match_truth"),
                    "epoch_match_truth": truth.get("epoch_match_truth"),
                    "legal_action_mask": deepcopy(policy.get("legal_action_mask")),
                    "actor_logits_fp32_bits": [
                        _bits_hex(word, "RAW actor logit") for word in actor_bits
                    ],
                    "critic_value_fp32_bits": _bits_hex(
                        policy.get("critic_value_fp32_bits"), "RAW critic value"
                    ),
                    "selected_action_log_probability_fp32_bits": _bits_hex(
                        policy.get("selected_action_log_probability_fp32_bits"),
                        "RAW selected log probability",
                    ),
                })
            tapes.append({
                "tape_id": tape_id,
                "raw_return": _ratio(raw_return),
                "always_refresh_return": _ratio(refresh_return),
                "always_safe_return": _ratio(safe_return),
                "decisions": decisions,
            })
        output.append({
            "seed": seed, "checkpoint_update": 48,
            "split": "EVAL_STOCHASTIC", "tapes": tapes,
        })
    return output


def reconstruct_raw_competence_from_tables(
    tables: Mapping[str, object], *, test_only: bool,
) -> list[dict[str, Any]]:
    """Independently rebuild the three RAW gates from their canonical tables."""

    inputs = _competence_inputs(tables, tables, test_only=test_only)
    return [compute_raw_competence(record) for record in inputs]


def _direct_mechanical(raw: Mapping[str, Any], prefix: str) -> Mapping[str, Any]:
    direct = raw.get("mechanical_direct")
    if not isinstance(direct, Mapping) or frozenset(direct) != _DIRECT_FIELDS:
        raise B1MetricsTrainingAssemblyError(
            "UPSTREAM_INSTRUMENTATION_GAP: mechanical_direct must record active_modes, "
            "recurrent reset bits, checkpoint roundtrip, and learner visibility"
        )
    if not isinstance(direct["active_modes"], list):
        raise B1MetricsTrainingAssemblyError(
            "UPSTREAM_INSTRUMENTATION_GAP: mechanical_direct.active_modes is absent"
        )
    for name in ("reset_records", "checkpoint_records", "learner_visibility_records"):
        if not isinstance(direct[name], list) or not direct[name]:
            raise B1MetricsTrainingAssemblyError(
                f"UPSTREAM_INSTRUMENTATION_GAP: mechanical_direct.{name} is absent"
            )
    return direct


def _raw_facts(
    *,
    raw_groups: Sequence[Sequence[Mapping[str, Any]]],
    identities: Sequence[tuple[int, str]],
    merged: Sequence[TrainingExposureRecords],
    admission_rows: Sequence[Mapping[str, Any]],
    telemetry_rows: Sequence[Mapping[str, Any]],
    shared_tables: Mapping[str, object],
    policy_tables: Mapping[str, object],
    test_only: bool,
) -> dict[str, Any]:
    episodes_per_update = 1 if test_only else 8
    adam_steps_per_update = 4 if test_only else 16
    slot_keys = [_key_text(0, seed, ARM_ORDER[arm]) for seed, arm in identities]
    decisions = [row for records in merged for row in records.training_decisions]
    episodes = [row for records in merged for row in records.training_episodes]
    steps = [row for records in merged for row in records.optimizer_steps]
    expected_decision_keys = [
        _key_text(0, seed, ARM_ORDER[arm], episode, opportunity)
        for seed, arm in identities
        for episode in range(48 * episodes_per_update)
        for opportunity in range(24)
    ]
    expected_episode_keys = [
        _key_text(0, seed, ARM_ORDER[arm], episode)
        for seed, arm in identities for episode in range(48 * episodes_per_update)
    ]
    expected_step_keys = [
        _key_text(0, seed, ARM_ORDER[arm], update, epoch, minibatch)
        for seed, arm in identities for update in range(48)
        for epoch in range(4) for minibatch in range(adam_steps_per_update // 4)
    ]
    observed_decision_keys = [
        _key_text(row["run_order"], row["seed"], row["arm_order"],
                  row["training_episode_id"], row["opportunity_id"])
        for row in decisions
    ]
    observed_episode_keys = [
        _key_text(row["run_order"], row["seed"], row["arm_order"], row["training_episode_id"])
        for row in episodes
    ]
    observed_step_keys = [
        _key_text(row["run_order"], row["seed"], row["arm_order"],
                  row["rollout_update"], row["ppo_epoch"], row["minibatch_index"])
        for row in steps
    ]
    inventories = [
        {"name": "arm-seed-slots", "expected_keys": slot_keys, "observed_keys": slot_keys},
        {"name": "training-decisions", "expected_keys": expected_decision_keys,
         "observed_keys": observed_decision_keys},
        {"name": "training-episodes", "expected_keys": expected_episode_keys,
         "observed_keys": observed_episode_keys},
        {"name": "optimizer-steps", "expected_keys": expected_step_keys,
         "observed_keys": observed_step_keys},
    ]

    resources: list[dict[str, Any]] = []
    for admission, telemetry in zip(admission_rows, telemetry_rows, strict=True):
        measurement = telemetry["measurement"]
        if admission["invocation_kind"] == "TRAINING_SLICE":
            invocation = (
                f"TRAINING_SLICE:{admission['original_slot_index']:02d}:"
                f"{admission['attempt_order']:02d}"
            )
        else:
            invocation = f"POLICY_REPLAY:{admission['original_slot_index']:02d}"
        resources.append({
            "invocation_id": invocation,
            "physical_available_bytes": admission["available_physical_bytes"],
            "effective_available_bytes": admission["effective_available_bytes"],
            "measurement_complete": measurement["measurement_complete"],
            "wall_seconds": measurement["end_to_end_wall_seconds"],
            "peak_rss_bytes": measurement["process_tree_peak_rss_bytes"],
            "scratch_peak_bytes": measurement["scratch_high_water_bytes"],
            "durable_peak_bytes": measurement["durable_high_water_bytes"],
        })

    tape_bindings: list[dict[str, str]] = []
    work_bindings: list[dict[str, Any]] = []
    fp32_records: list[dict[str, Any]] = []
    numeric_records: list[dict[str, Any]] = []
    reset_records: list[dict[str, Any]] = []
    adaptation_records: list[dict[str, Any]] = []
    checkpoint_records: list[dict[str, Any]] = []
    visibility_records: list[dict[str, Any]] = []
    literal_records: list[dict[str, Any]] = []
    expected_config = config_digest(PPOConfig())
    expected_source: str | None = None
    expected_commit: str | None = None
    seed_tape_digest: dict[int, str] = {}
    telemetry_index: dict[tuple[int, int], list[Mapping[str, Any]]] = defaultdict(list)
    for row in telemetry_rows:
        if row["invocation_kind"] == "TRAINING_SLICE":
            telemetry_index[(row["seed"], row["arm_order"])].append(row)
    for group_index, (group, (seed, arm), records) in enumerate(
        zip(raw_groups, identities, merged, strict=True)
    ):
        arm_order = ARM_ORDER[arm]
        train_episodes = train_transitions = eval_episodes = eval_transitions = 0
        for slice_index, raw in enumerate(group):
            prefix = f"{seed}:{arm_order}:{slice_index}"
            binding = raw.get("full_bindings")
            counts = raw.get("slice_counts")
            if not isinstance(binding, Mapping) or not isinstance(counts, Mapping):
                raise B1MetricsTrainingAssemblyError("raw binding/work counts are absent")
            observed_config = _digest(binding.get("ppo_configuration_digest"), "PPO config digest")
            literal_records.append({
                "audit_code": f"{prefix}:ppo-config-binding",
                "expected": expected_config, "observed": observed_config,
            })
            tape_digest = _digest(binding.get("full_training_tape_digest"), "training tape digest")
            seed_tape_digest.setdefault(seed, tape_digest)
            tape_bindings.append({
                "name": f"{prefix}:cross-arm-training-tape",
                "expected_sha256": seed_tape_digest[seed],
                "observed_sha256": tape_digest,
            })
            for name in ("train_episodes", "train_transitions", "evaluation_episodes", "evaluation_transitions"):
                if type(counts.get(name)) is not int or counts[name] < 0:
                    raise B1MetricsTrainingAssemblyError("raw slice count is absent/noninteger")
            train_episodes += counts["train_episodes"]
            train_transitions += counts["train_transitions"]
            eval_episodes += counts["evaluation_episodes"]
            eval_transitions += counts["evaluation_transitions"]
            direct = _direct_mechanical(raw, prefix)
            active_modes = list(direct["active_modes"])
            for row in direct["reset_records"]:
                reset_records.append(dict(row))
            for row in direct["checkpoint_records"]:
                checkpoint_records.append(dict(row))
            for row in direct["learner_visibility_records"]:
                visibility_records.append(dict(row))
            for evaluation in raw.get("evaluations", []):
                heldout = evaluation.get("heldout_state_observations") if isinstance(evaluation, Mapping) else None
                required = {
                    "model_digest_before", "model_digest_after",
                    "optimizer_digest_before", "optimizer_digest_after",
                }
                if not isinstance(heldout, Mapping) or not required <= set(heldout):
                    raise B1MetricsTrainingAssemblyError(
                        "UPSTREAM_INSTRUMENTATION_GAP: adaptation-free before/after digests absent"
                    )
                adaptation_records.append({
                    "name": f"{prefix}:eval:{evaluation.get('update')}",
                    "model_sha256_before": heldout["model_digest_before"],
                    "model_sha256_after": heldout["model_digest_after"],
                    "optimizer_sha256_before": heldout["optimizer_digest_before"],
                    "optimizer_sha256_after": heldout["optimizer_digest_after"],
                })
            observed_source = _digest(
                binding.get("source_conformance_sha256"), "source_conformance_sha256"
            )
            commit = _digest(binding.get("implementation_commit"), "implementation_commit", 40)
            expected_source = observed_source if expected_source is None else expected_source
            expected_commit = commit if expected_commit is None else expected_commit
            literal_records.extend([
                {"audit_code": f"{prefix}:source-binding", "expected": expected_source,
                 "observed": observed_source},
                {"audit_code": f"{prefix}:commit-binding", "expected": expected_commit,
                 "observed": commit},
                {"audit_code": f"{prefix}:run", "expected": B1_RUN_NAME,
                 "observed": raw.get("run_name")},
                {"audit_code": f"{prefix}:seed", "expected": seed, "observed": raw.get("seed")},
                {"audit_code": f"{prefix}:arm", "expected": arm, "observed": raw.get("arm")},
            ])
            for step in records.optimizer_steps:
                if step["rollout_update"] < raw["slice"]["start_update"] or step["rollout_update"] >= raw["slice"]["stop_update"]:
                    continue
                for field in (
                    "actor_loss_fp32_bits", "value_loss_fp32_bits", "entropy_fp32_bits",
                    "total_loss_fp32_bits", "preclip_gradient_norm_fp32_bits",
                    "postclip_gradient_norm_fp32_bits",
                ):
                    fp32_records.append({
                        "name": f"{prefix}:{field}:{step['optimizer_step_count']}",
                        "dtype": "float32", "fp32_bits": step[field],
                        "active_modes": active_modes,
                    })
        work_bindings.extend([
            {"name": f"{seed}:{arm_order}:train-episodes",
             "expected_count": 48 * episodes_per_update,
             "observed_count": train_episodes},
            {"name": f"{seed}:{arm_order}:train-transitions",
             "expected_count": 48 * episodes_per_update * EPISODE_TRANSITIONS,
             "observed_count": train_transitions},
            {"name": f"{seed}:{arm_order}:evaluation-episodes", "expected_count": 256,
             "observed_count": eval_episodes},
            {"name": f"{seed}:{arm_order}:evaluation-transitions", "expected_count": 38_912,
             "observed_count": eval_transitions},
            {"name": f"{seed}:{arm_order}:training-decision-rows",
             "expected_count": 48 * episodes_per_update * OPPORTUNITY_COUNT,
             "observed_count": len(records.training_decisions)},
            {"name": f"{seed}:{arm_order}:optimizer-rows",
             "expected_count": 48 * adam_steps_per_update,
             "observed_count": len(records.optimizer_steps)},
        ])
        for row in records.training_decisions:
            numeric_records.extend([
                {"name": f"decision-logp:{seed}:{arm_order}:{row['training_episode_id']}:{row['opportunity_id']}",
                 "value": row["selected_log_probability"]},
                {"name": f"opportunity-return:{seed}:{arm_order}:{row['training_episode_id']}:{row['opportunity_id']}",
                 "value": row["opportunity_return"]},
            ])

    policy_rows = policy_tables.get("policy_decisions")
    if not isinstance(policy_rows, list):
        raise B1MetricsTrainingAssemblyError("policy_decisions are absent")
    policy_mode_rows = policy_tables.get("execution_mode_records")
    if not isinstance(policy_mode_rows, list) or not policy_mode_rows:
        raise B1MetricsTrainingAssemblyError(
            "UPSTREAM_INSTRUMENTATION_GAP: policy execution_mode_records are absent"
        )
    policy_modes: dict[tuple[int, int, int, int], list[str]] = {}
    for row in policy_mode_rows:
        if not isinstance(row, Mapping) or set(row) != {
            "run_order", "seed", "arm_order", "checkpoint_update", "active_modes"
        } or not isinstance(row["active_modes"], list):
            raise B1MetricsTrainingAssemblyError(
                "UPSTREAM_INSTRUMENTATION_GAP: policy execution mode record differs"
            )
        key = (row["run_order"], row["seed"], row["arm_order"], row["checkpoint_update"])
        if key in policy_modes:
            raise B1MetricsTrainingAssemblyError("policy execution mode key is duplicated")
        policy_modes[key] = list(row["active_modes"])
    legal_action_records = [
        {
            "name": f"train:{row['seed']}:{row['arm_order']}:{row['training_episode_id']}:{row['opportunity_id']}",
            "selected_action_index": row["selected_action"] + 1,
            "legal_action_mask": deepcopy(row["legal_mask"]),
        }
        for row in decisions
    ]
    for index, row in enumerate(policy_rows):
        if not isinstance(row, Mapping):
            raise B1MetricsTrainingAssemblyError("policy decision contains a non-record")
        legal_action_records.append({
            "name": f"policy:{index}",
            "selected_action_index": row.get("selected_action", -1) + 1,
            "legal_action_mask": deepcopy(row.get("legal_action_mask")),
        })
        mode_key = (
            row.get("run_order"), row.get("seed"), row.get("arm_order"),
            row.get("checkpoint_update"),
        )
        if mode_key not in policy_modes:
            raise B1MetricsTrainingAssemblyError(
                "UPSTREAM_INSTRUMENTATION_GAP: policy FP32 execution mode fact is absent"
            )
        active_modes = policy_modes[mode_key]
        for word_index, word in enumerate(row.get("actor_logits_fp32_bits", [])):
            fp32_records.append({
                "name": f"policy:{index}:logit:{word_index}", "dtype": "float32",
                "fp32_bits": _bits_hex(word, "policy actor logit"),
                "active_modes": active_modes,
            })
        for field in ("critic_value_fp32_bits", "selected_action_log_probability_fp32_bits"):
            fp32_records.append({
                "name": f"policy:{index}:{field}", "dtype": "float32",
                "fp32_bits": _bits_hex(row.get(field), field),
                "active_modes": active_modes,
            })

    motif_rows = shared_tables.get("motif_twin_index")
    if not isinstance(motif_rows, list) or not motif_rows:
        raise B1MetricsTrainingAssemblyError("motif_twin_index direct rows are absent")
    member_groups: dict[str, list[str]] = defaultdict(list)
    family_by_pair: dict[str, int] = {}
    for row in motif_rows:
        if not isinstance(row, Mapping) or type(row.get("pair_id")) is not str:
            raise B1MetricsTrainingAssemblyError("motif twin row differs")
        member_groups[row["pair_id"]].append(row.get("member_role"))
        family_by_pair[row["pair_id"]] = row.get("motif_family")
    twin_records = []
    for pair_id in sorted(member_groups):
        expected = ["GAP1", "GAP6"] if family_by_pair[pair_id] == 7 else ["A", "B"]
        twin_records.append({
            "pair_id": pair_id, "expected_members": expected,
            "observed_members": member_groups[pair_id],
        })

    if not all((inventories, resources, tape_bindings, work_bindings,
                fp32_records, numeric_records, reset_records, adaptation_records,
                checkpoint_records, visibility_records, legal_action_records,
                twin_records, literal_records)):
        raise B1MetricsTrainingAssemblyError(
            "UPSTREAM_INSTRUMENTATION_GAP: one or more direct mechanical fact categories are empty"
        )
    return {
        "inventories": inventories,
        "resources": resources,
        "digest_bindings": deepcopy(_PENDING_DIGEST_BINDINGS),
        "tape_bindings": tape_bindings,
        "work_bindings": work_bindings,
        "fp32_records": fp32_records,
        "numeric_records": numeric_records,
        "reset_records": reset_records,
        "adaptation_records": adaptation_records,
        "checkpoint_records": checkpoint_records,
        "learner_visibility_records": visibility_records,
        "legal_action_records": legal_action_records,
        "twin_records": twin_records,
        "literal_records": literal_records,
    }


from .b1_metrics_artifact import _canonical_key  # canonical publication ordering


def _table_audit_rows(
    authority_tables: Mapping[str, list[Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for table, key_fields in _TABLE_AUDIT_KEY_FIELDS.items():
        source = authority_tables.get(table)
        if not isinstance(source, list) or not source:
            raise B1MetricsTrainingAssemblyError(
                f"audit authority source table is absent: {table}"
            )
        if any(not isinstance(row, Mapping) or any(field not in row for field in key_fields) for row in source):
            raise B1MetricsTrainingAssemblyError(
                f"audit authority key fields differ: {table}"
            )
        # Order exactly as the publication orders it.  canonicalize_metrics_table_order
        # and _validate_rows both sort by _canonical_key, which decodes composite
        # and categorical key values -- notably a string ``pair_id`` such as
        # "21101:0:10", which sorts numerically there but lexically as a raw
        # string.  motif_twin_index is the one authority table carrying such a
        # key, so sorting raw tuples here produced an expected_sha256 over a byte
        # order the publication never writes, and every formal assembly refused
        # with "materialized table reread binding differs: motif_twin_index".
        # The reported first/last key stay RAW, because
        # _materialized_audit_authority_records reads them straight out of the
        # materialized row.
        ordered = sorted(source, key=lambda row: _canonical_key(row, key_fields))
        keys = [_canonical_key(row, key_fields) for row in ordered]
        raw_keys = [tuple(row[field] for field in key_fields) for row in ordered]
        if len(keys) != len(set(keys)):
            raise B1MetricsTrainingAssemblyError(
                f"audit authority table key duplicated: {table}"
            )
        payload = b"".join(canonical_json_bytes(row) + b"\n" for row in ordered)
        rows.append({
            "run_order": 0, "attempt_order": 0,
            "seed_or_minus_one": -1, "arm_or_minus_one": -1,
            "audit_code": f"TABLE:{table}",
            "authority_type": "CANONICAL_TABLE_AUTHORITY",
            "source_table": table,
            "source_key_range": {
                "key_fields": list(key_fields),
                "first_key": list(raw_keys[0]), "last_key": list(raw_keys[-1]),
            },
            "source_raw_slice": None, "fact_name": None,
            "expected": {"row_count": len(ordered)}, "observed": None,
            "expected_sha256": hashlib.sha256(payload).hexdigest(),
            "actual_sha256": None,
            "binding_status": "PENDING_MATERIALIZED_TABLE_REREAD",
            "source_relative_path": None, "json_pointer": None,
            "source_file_sha256": None, "payload_shape": None,
            "payload_dtype": None, "payload_nonzero_count": None,
        })
    return rows


def _json_pointer_get(value: object, pointer: str) -> object:
    if type(pointer) is not str or not pointer.startswith("/"):
        raise B1MetricsTrainingAssemblyError("audit JSON pointer differs")
    current = value
    try:
        for raw_part in pointer.split("/")[1:]:
            part = raw_part.replace("~1", "/").replace("~0", "~")
            if isinstance(current, list):
                current = current[int(part)]
            elif isinstance(current, Mapping):
                current = current[part]
            else:
                raise KeyError(part)
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise B1MetricsTrainingAssemblyError(
            f"audit JSON pointer cannot be resolved: {pointer}"
        ) from exc
    return current


def _payload_shape(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    if not value:
        return [0]
    child_shapes = [_payload_shape(item) for item in value]
    return [len(value), *child_shapes[0]] if all(
        shape == child_shapes[0] for shape in child_shapes
    ) else [len(value)]


def _payload_dtype(value: object) -> str:
    leaves: set[str] = set()

    def descend(item: object) -> None:
        if isinstance(item, Mapping):
            for child in item.values():
                descend(child)
        elif isinstance(item, list):
            for child in item:
                descend(child)
        elif item is None:
            leaves.add("null")
        elif type(item) is bool:
            leaves.add("bool")
        elif type(item) is int:
            leaves.add("int")
        elif type(item) is float:
            leaves.add("float64-json")
        elif type(item) is str and len(item) == 8 and all(
            character in "0123456789abcdef" for character in item
        ):
            leaves.add("fp32-bits-hex")
        elif type(item) is str:
            leaves.add("string")
        else:
            leaves.add(type(item).__name__)

    descend(value)
    return "+".join(sorted(leaves)) if leaves else "empty"


def _payload_nonzero_count(value: object) -> int:
    if isinstance(value, Mapping):
        return sum(_payload_nonzero_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(_payload_nonzero_count(item) for item in value)
    if value is None or value is False:
        return 0
    if type(value) in (int, float):
        return int(value != 0)
    if type(value) is str and len(value) == 8 and all(
        character in "0123456789abcdef" for character in value
    ):
        return int(struct.unpack(">f", bytes.fromhex(value))[0] != 0.0)
    return int(bool(value))


def _source_descriptor(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or frozenset(value) != _SOURCE_DESCRIPTOR_FIELDS:
        raise B1MetricsTrainingAssemblyError("raw source descriptor schema differs")
    relative = value["source_relative_path"]
    pointer = value["raw_json_pointer"]
    if (
        type(relative) is not str or not relative or "\\" in relative
        or relative.startswith("/") or any(
            part in {"", ".", ".."} for part in relative.split("/")
        )
        or not relative.endswith("/result.json.gz")
    ):
        raise B1MetricsTrainingAssemblyError("raw source relative path differs")
    if type(pointer) is not str or pointer != "/raw_evidence":
        raise B1MetricsTrainingAssemblyError("raw source JSON pointer differs")
    return {
        "source_relative_path": relative,
        "source_file_sha256": _digest(
            value["source_file_sha256"], "raw source file SHA"
        ),
        "raw_json_pointer": pointer,
    }


def _synthetic_test_sources(
    raw_groups: Sequence[Sequence[Mapping[str, Any]]],
) -> list[list[dict[str, str]]]:
    output: list[list[dict[str, str]]] = []
    for group_index, group in enumerate(raw_groups):
        descriptors: list[dict[str, str]] = []
        for attempt_order, raw in enumerate(group):
            wrapper = {"raw_evidence": raw}
            payload = canonical_json_bytes(wrapper) + b"\n"
            descriptors.append({
                "source_relative_path": (
                    f"workers/{group_index:02d}-seed-{raw['seed']}-{raw['arm']}/"
                    f"slice-{raw['slice']['start_update']:02d}-"
                    f"{raw['slice']['stop_update']:02d}/result.json"
                ),
                "source_file_sha256": hashlib.sha256(payload).hexdigest(),
                "raw_json_pointer": "/raw_evidence",
            })
        output.append(descriptors)
    return output


def _validate_source_groups(
    value: object,
    raw_groups: Sequence[Sequence[Mapping[str, Any]]],
) -> list[list[dict[str, str]]]:
    groups = list(_sequence(value, "raw_source_groups"))
    if len(groups) != len(raw_groups):
        raise B1MetricsTrainingAssemblyError("raw source group inventory differs")
    output: list[list[dict[str, str]]] = []
    seen: set[tuple[str, str]] = set()
    for group_index, (sources, raw_group) in enumerate(
        zip(groups, raw_groups, strict=True)
    ):
        source_values = list(_sequence(sources, "raw source group"))
        if len(source_values) != len(raw_group):
            raise B1MetricsTrainingAssemblyError("raw source slice inventory differs")
        validated = [_source_descriptor(source) for source in source_values]
        for source, raw in zip(validated, raw_group, strict=True):
            interval = raw["slice"]
            expected_relative = (
                f"workers/{group_index:02d}-seed-{raw['seed']}-{raw['arm']}/"
                f"slice-{interval['start_update']:02d}-{interval['stop_update']:02d}/"
                "result.json"
            )
            if source["source_relative_path"] != expected_relative + ".gz":
                raise B1MetricsTrainingAssemblyError(
                    "raw source path differs from exact worker invocation"
                )
            key = (source["source_relative_path"], source["raw_json_pointer"])
            if key in seen:
                raise B1MetricsTrainingAssemblyError("raw source descriptor is duplicated")
            seen.add(key)
        output.append(validated)
    return output


def _pointer_audit_row(
    *, source: Mapping[str, Any], provenance: Mapping[str, str],
    json_pointer: str, audit_code: str, fact_name: str,
    expected: object, observed: object,
) -> dict[str, Any]:
    expected_sha = hashlib.sha256(canonical_json_bytes(expected)).hexdigest()
    actual_sha = hashlib.sha256(canonical_json_bytes(observed)).hexdigest()
    return {
        "run_order": 0, "attempt_order": source["attempt_order"],
        "seed_or_minus_one": source["seed"],
        "arm_or_minus_one": source["arm_order"],
        "audit_code": audit_code, "authority_type": "DIRECT_RAW_FACT",
        "source_table": None, "source_key_range": None,
        "source_raw_slice": dict(source), "fact_name": fact_name,
        "expected": None, "observed": None,
        "expected_sha256": expected_sha, "actual_sha256": actual_sha,
        "binding_status": (
            "DIRECT_RAW_FACT" if expected_sha == actual_sha
            else "DIRECT_RAW_FACT_ADVERSE"
        ),
        "source_relative_path": provenance["source_relative_path"],
        "json_pointer": json_pointer,
        "source_file_sha256": provenance["source_file_sha256"],
        "payload_shape": _payload_shape(observed),
        "payload_dtype": _payload_dtype(observed),
        "payload_nonzero_count": _payload_nonzero_count(observed),
    }


def _direct_audit_rows(
    raw_groups: Sequence[Sequence[Mapping[str, Any]]],
    source_groups: Sequence[Sequence[Mapping[str, str]]],
    *, test_only: bool,
) -> list[dict[str, Any]]:
    episodes_per_update = 1 if test_only else 8
    rows: list[dict[str, Any]] = []
    expected_config = config_digest(PPOConfig())
    expected_source: str | None = None
    expected_commit: str | None = None
    seed_tapes: dict[int, str] = {}
    for group, provenance_group in zip(raw_groups, source_groups, strict=True):
        for attempt_order, (raw, provenance) in enumerate(
            zip(group, provenance_group, strict=True)
        ):
            seed, arm = raw["seed"], raw["arm"]
            interval = raw["slice"]
            source = {
                "attempt_id": raw["attempt_id"], "seed": seed,
                "arm_order": ARM_ORDER[arm],
                "slice_start_update": interval["start_update"],
                "slice_stop_update": interval["stop_update"],
                "attempt_order": attempt_order,
            }
            base = f"S{seed}:A{ARM_ORDER[arm]}:I{attempt_order}"
            pointer_root = provenance["raw_json_pointer"]

            def add(
                suffix: str, code: str, fact_name: str,
                expected: object, observed: object,
            ) -> None:
                rows.append(_pointer_audit_row(
                    source=source, provenance=provenance,
                    json_pointer=f"{pointer_root}{suffix}",
                    audit_code=f"{base}:{code}", fact_name=fact_name,
                    expected=expected, observed=observed,
                ))

            direct = raw["mechanical_direct"]
            add(
                "/mechanical_direct/active_modes", "MODE:0", "active_modes",
                [], direct["active_modes"],
            )
            for index, record in enumerate(direct["reset_records"]):
                add(
                    f"/mechanical_direct/reset_records/{index}/observed_fp32_bits",
                    f"RESET:{index}", record.get("name", f"reset-{index}"),
                    record.get("expected_fp32_bits"),
                    record.get("observed_fp32_bits"),
                )
            for index, record in enumerate(direct["checkpoint_records"]):
                name = record.get("name", f"checkpoint-{index}")
                add(
                    f"/mechanical_direct/checkpoint_records/{index}/loaded_sha256",
                    f"CHECKPOINT:{index}:BYTES", f"{name}:bytes",
                    record.get("saved_sha256"), record.get("loaded_sha256"),
                )
                add(
                    f"/mechanical_direct/checkpoint_records/{index}/restored_parameter_sha256",
                    f"CHECKPOINT:{index}:PARAMETER", f"{name}:parameter",
                    record.get("expected_parameter_sha256"),
                    record.get("restored_parameter_sha256"),
                )
            for index, record in enumerate(direct["learner_visibility_records"]):
                add(
                    f"/mechanical_direct/learner_visibility_records/{index}/visible_fields",
                    f"VISIBILITY:{index}",
                    record.get("name", f"visibility-{index}"),
                    record.get("allowed_fields"), record.get("visible_fields"),
                )
            binding = raw["full_bindings"]
            observed_source = binding.get("source_conformance_sha256")
            observed_commit = binding.get("implementation_commit")
            expected_source = observed_source if expected_source is None else expected_source
            expected_commit = observed_commit if expected_commit is None else expected_commit
            literal_pairs = (
                ("RUN", "/run_name", B1_RUN_NAME, raw.get("run_name")),
                ("SEED", "/seed", seed, raw.get("seed")),
                ("ARM", "/arm", arm, raw.get("arm")),
                (
                    "CONFIG", "/full_bindings/ppo_configuration_digest",
                    expected_config, binding.get("ppo_configuration_digest"),
                ),
                (
                    "SOURCE", "/full_bindings/source_conformance_sha256",
                    expected_source, observed_source,
                ),
                (
                    "COMMIT", "/full_bindings/implementation_commit",
                    expected_commit, observed_commit,
                ),
            )
            for name, suffix, expected, observed in literal_pairs:
                add(suffix, f"LITERAL:{name}", name.lower(), expected, observed)
            tape = binding.get("full_training_tape_digest")
            seed_tapes.setdefault(seed, tape)
            add(
                "/full_bindings/full_training_tape_digest", "TAPE:0",
                "full_training_tape_digest", seed_tapes[seed], tape,
            )
            start, stop = interval["start_update"], interval["stop_update"]
            checkpoints = ([0] if start == 0 else []) + [
                checkpoint for checkpoint in (12, 24, 48) if start < checkpoint <= stop
            ]
            for name, expected in (
                ("train_transitions", (stop - start) * episodes_per_update * 152),
                ("evaluation_transitions", len(checkpoints) * 64 * 152),
            ):
                add(
                    f"/slice_counts/{name}", f"WORK:{name.upper()}", name,
                    expected, raw["slice_counts"].get(name),
                )
            for index, evaluation in enumerate(raw.get("evaluations", [])):
                heldout = evaluation.get("heldout_state_observations", {})
                prefix = f"/evaluations/{index}/heldout_state_observations"
                update = evaluation.get("update")
                add(
                    f"{prefix}/model_digest_after", f"ADAPTATION:{index}:MODEL",
                    f"evaluation-{update}:model",
                    heldout.get("model_digest_before"),
                    heldout.get("model_digest_after"),
                )
                add(
                    f"{prefix}/optimizer_digest_after",
                    f"ADAPTATION:{index}:OPTIMIZER",
                    f"evaluation-{update}:optimizer",
                    heldout.get("optimizer_digest_before"),
                    heldout.get("optimizer_digest_after"),
                )
    return rows


def _json_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _exact_fp32(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise B1MetricsTrainingAssemblyError(
            "ROLLOUT_AUDIT_ADVERSE:REWARD_LEDGER_MISMATCH:non-numeric reward"
        )
    numeric = float(value)
    if not math.isfinite(numeric):
        raise B1MetricsTrainingAssemblyError(
            "ROLLOUT_AUDIT_ADVERSE:REWARD_LEDGER_MISMATCH:nonfinite reward"
        )
    return struct.unpack(">f", struct.pack(">f", numeric))[0]


def _rollout_adverse(
    code: str, source: Mapping[str, Any], detail: str,
) -> None:
    identity = _key_text(
        source["seed"], source["arm_order"], source["attempt_order"],
        source["slice_start_update"], source["slice_stop_update"], detail,
    )
    raise B1MetricsTrainingAssemblyError(
        f"ROLLOUT_AUDIT_ADVERSE:{code}:{identity}"
    )


def _require_rollout_equal(
    code: str, source: Mapping[str, Any], detail: str,
    expected: object, observed: object,
) -> None:
    if observed != expected:
        _rollout_adverse(code, source, detail)


def _rollout_source(
    raw: Mapping[str, Any], attempt_order: int,
) -> dict[str, Any]:
    interval = raw["slice"]
    return {
        "attempt_id": raw["attempt_id"], "seed": raw["seed"],
        "arm_order": ARM_ORDER[raw["arm"]],
        "slice_start_update": interval["start_update"],
        "slice_stop_update": interval["stop_update"],
        "attempt_order": attempt_order,
    }


def _rollout_rng_audit_rows(
    *, raw_groups: Sequence[Sequence[Mapping[str, Any]]],
    merged: Sequence[TrainingExposureRecords],
    source_groups: Sequence[Sequence[Mapping[str, str]]],
    test_only: bool,
) -> list[dict[str, Any]]:
    """Rebuild every training tape/RNG/ledger/order fact from frozen primitives."""

    rows: list[dict[str, Any]] = []
    decision_rows = list(range(12, EPISODE_TRANSITIONS, 6))
    forced_wait_rows = [
        row for row in range(EPISODE_TRANSITIONS) if row not in decision_rows
    ]
    empty_order_digest = hashlib.sha256(b"").hexdigest()
    episodes_per_update = 1 if test_only else 8
    minibatches_per_epoch = 1 if test_only else 4
    for group, exposure, provenance_group in zip(
        raw_groups, merged, source_groups, strict=True
    ):
        seed, arm = _slot_identity(group)
        host = DynamicHost(B1_RUN_NAME, seed)
        arm_order = ARM_ORDER[arm]
        decisions = {
            (row["training_episode_id"], row["opportunity_id"]): row
            for row in exposure.training_decisions
        }
        episodes = {
            row["training_episode_id"]: row for row in exposure.training_episodes
        }
        optimizer = {
            (row["rollout_update"], row["ppo_epoch"], row["minibatch_index"]): row
            for row in exposure.optimizer_steps
        }
        order_digest = empty_order_digest
        full_tape_records: list[dict[str, Any]] = []
        full_uniform_records: list[dict[str, Any]] = []
        last_update = -1
        for attempt_order, (raw, provenance) in enumerate(
            zip(group, provenance_group, strict=True)
        ):
            source = _rollout_source(raw, attempt_order)
            interval = raw["slice"]
            start, stop = interval["start_update"], interval["stop_update"]
            raw_rollouts = raw.get("rollouts")
            if (
                not isinstance(raw_rollouts, list)
                or len(raw_rollouts) != stop - start
                or any(not isinstance(record, Mapping) for record in raw_rollouts)
            ):
                _rollout_adverse(
                    "ROLLOUT_RECORD_SCHEMA_MISMATCH", source, "rollout-inventory"
                )
            for offset, update in enumerate(range(start, stop)):
                record = raw_rollouts[offset]
                _require_rollout_equal(
                    "ROLLOUT_UPDATE_COVERAGE_MISMATCH", source, f"update-{update}",
                    (update, update + 1),
                    (record.get("update_before"), record.get("update_after")),
                )
                if update != last_update + 1:
                    _rollout_adverse(
                        "ROLLOUT_UPDATE_COVERAGE_MISMATCH", source, f"update-{update}"
                    )
                last_update = update
                tapes = tuple(
                    host.build_stochastic(addressing.TRAIN, episode_id)
                    for episode_id in range(
                        update * episodes_per_update,
                        (update + 1) * episodes_per_update,
                    )
                )
                expected_tapes = [
                    {
                        "identity": vars(tape.identity),
                        "primitive_digest_observed": tape.primitive_digest,
                        "draw_digest_observed": tape.generation_audit.draw_digest,
                        "draw_count_observed": tape.generation_audit.draw_count,
                    }
                    for tape in tapes
                ]
                _require_rollout_equal(
                    "TRAIN_TAPE_MISMATCH", source, f"update-{update}",
                    expected_tapes, record.get("tapes"),
                )
                full_tape_records.extend(
                    {
                        "identity": vars(tape.identity),
                        "primitive_digest": tape.primitive_digest,
                    }
                    for tape in tapes
                )

                expected_uniforms: list[dict[str, Any]] = []
                for tape in tapes:
                    for opportunity in range(OPPORTUNITY_COUNT):
                        address = addressing.action_address(
                            B1_RUN_NAME, seed, tape.identity.episode_id, opportunity
                        )
                        expected_uniforms.append({
                            "episode_id": tape.identity.episode_id,
                            "opportunity_index": opportunity,
                            "address": list(address),
                            "u64": addressing.u64(address),
                        })
                raw_rollout = record.get("raw_rollout")
                if not isinstance(raw_rollout, Mapping):
                    _rollout_adverse(
                        "ROLLOUT_RECORD_SCHEMA_MISMATCH", source, f"update-{update}:raw"
                    )
                observed_uniforms = raw_rollout.get("uniforms")
                if (
                    not isinstance(observed_uniforms, list)
                    or len(observed_uniforms) != episodes_per_update * OPPORTUNITY_COUNT
                ):
                    _rollout_adverse(
                        "ACTION_UNIFORM_IDENTITY_MISMATCH", source,
                        f"update-{update}:inventory",
                    )
                for uniform_index, (expected, observed) in enumerate(
                    zip(expected_uniforms, observed_uniforms, strict=True)
                ):
                    if not isinstance(observed, Mapping):
                        _rollout_adverse(
                            "ACTION_UNIFORM_IDENTITY_MISMATCH", source,
                            f"update-{update}:uniform-{uniform_index}",
                        )
                    _require_rollout_equal(
                        "ACTION_UNIFORM_IDENTITY_MISMATCH", source,
                        f"update-{update}:uniform-{uniform_index}",
                        (expected["episode_id"], expected["opportunity_index"]),
                        (observed.get("episode_id"), observed.get("opportunity_index")),
                    )
                    _require_rollout_equal(
                        "ACTION_ADDRESS_MISMATCH", source,
                        f"update-{update}:uniform-{uniform_index}",
                        expected["address"], observed.get("address"),
                    )
                    _require_rollout_equal(
                        "ACTION_U64_MISMATCH", source,
                        f"update-{update}:uniform-{uniform_index}",
                        expected["u64"], observed.get("u64"),
                    )
                expected_chunk_digest = _json_sha256(expected_uniforms)
                _require_rollout_equal(
                    "ACTION_CHUNK_DIGEST_MISMATCH", source, f"update-{update}",
                    expected_chunk_digest, record.get("chunk_action_uniform_digest"),
                )
                full_uniform_records.extend(expected_uniforms)

                expected_consumption = [decision_rows[:] for _ in tapes]
                _require_rollout_equal(
                    "ACTION_CONSUMPTION_MISMATCH", source, f"update-{update}",
                    expected_consumption, raw_rollout.get("uniforms_consumed_rows"),
                )
                _require_rollout_equal(
                    "FORCED_WAIT_MISMATCH", source, f"update-{update}",
                    [forced_wait_rows[:] for _ in tapes],
                    raw_rollout.get("forced_wait_rows"),
                )
                _require_rollout_equal(
                    "TERMINAL_ROW_MISMATCH", source, f"update-{update}",
                    [[EPISODE_TRANSITIONS - 1] for _ in tapes],
                    raw_rollout.get("terminated_rows"),
                )
                _require_rollout_equal(
                    "OBSERVATION_SHAPE_MISMATCH", source, f"update-{update}",
                    [episodes_per_update, EPISODE_TRANSITIONS, 168],
                    raw_rollout.get("observation_shape"),
                )

                action_traces = raw_rollout.get("actions")
                reward_traces = raw_rollout.get("rewards")
                if (
                    not isinstance(action_traces, list)
                    or len(action_traces) != episodes_per_update
                    or not isinstance(reward_traces, list)
                    or len(reward_traces) != episodes_per_update
                ):
                    _rollout_adverse(
                        "ROLLOUT_RECORD_SCHEMA_MISMATCH", source,
                        f"update-{update}:action-reward-inventory",
                    )
                for episode_offset, tape in enumerate(tapes):
                    action_trace = action_traces[episode_offset]
                    reward_trace = reward_traces[episode_offset]
                    if not isinstance(action_trace, Mapping) or not isinstance(reward_trace, Mapping):
                        _rollout_adverse(
                            "ROLLOUT_RECORD_SCHEMA_MISMATCH", source,
                            f"update-{update}:episode-{episode_offset}",
                        )
                    identity = vars(tape.identity)
                    _require_rollout_equal(
                        "ROLLOUT_IDENTITY_MISMATCH", source,
                        f"update-{update}:episode-{episode_offset}:action",
                        identity, action_trace.get("identity"),
                    )
                    _require_rollout_equal(
                        "ROLLOUT_IDENTITY_MISMATCH", source,
                        f"update-{update}:episode-{episode_offset}:reward",
                        identity, reward_trace.get("identity"),
                    )
                    observed_actions = action_trace.get("decision_actions")
                    if not isinstance(observed_actions, list) or len(observed_actions) != 24:
                        _rollout_adverse(
                            "ACTION_TRACE_MISMATCH", source,
                            f"update-{update}:episode-{episode_offset}",
                        )
                    expected_decision_rewards: list[float] = []
                    expected_settlement_rewards: list[float] = []
                    expected_action_names: list[str] = []
                    reward_tensor = torch.zeros(EPISODE_TRANSITIONS, dtype=torch.float32)
                    action_counts = [0, 0, 0]
                    for opportunity in range(OPPORTUNITY_COUNT):
                        decision = decisions[(tape.identity.episode_id, opportunity)]
                        _require_rollout_equal(
                            "TRAINING_DECISION_JOIN_MISMATCH", source,
                            f"update-{update}:episode-{episode_offset}:opportunity-{opportunity}",
                            (update, update, list(DECISION_ACTION_MASK)),
                            (
                                decision["rollout_update"], decision["policy_version"],
                                decision["legal_mask"],
                            ),
                        )
                        selected = decision["selected_action"]
                        if type(selected) is not int or not 0 <= selected < 3:
                            _rollout_adverse(
                                "ACTION_TRACE_MISMATCH", source,
                                f"update-{update}:episode-{episode_offset}:opportunity-{opportunity}",
                            )
                        action = Action(selected + 1)
                        expected_action_names.append(action.name)
                        _require_rollout_equal(
                            "ACTION_TRACE_MISMATCH", source,
                            f"update-{update}:episode-{episode_offset}:opportunity-{opportunity}",
                            action.name, observed_actions[opportunity],
                        )
                        ledger = tape.evaluator().ledger(opportunity, action)
                        decision_reward = _exact_fp32(ledger.decision_reward)
                        settlement_reward = _exact_fp32(ledger.settlement_reward)
                        opportunity_return = _exact_fp32(
                            decision_reward + settlement_reward
                        )
                        expected_decision_rewards.append(decision_reward)
                        expected_settlement_rewards.append(settlement_reward)
                        reward_tensor[12 + 6 * opportunity] = decision_reward
                        reward_tensor[13 + 6 * opportunity] = settlement_reward
                        action_counts[selected] += 1
                        _require_rollout_equal(
                            "REWARD_LEDGER_MISMATCH", source,
                            f"update-{update}:episode-{episode_offset}:opportunity-{opportunity}",
                            (decision_reward, settlement_reward, opportunity_return),
                            (
                                decision["decision_reward"],
                                decision["settlement_reward"],
                                decision["opportunity_return"],
                            ),
                        )
                    _require_rollout_equal(
                        "REWARD_LEDGER_MISMATCH", source,
                        f"update-{update}:episode-{episode_offset}:raw",
                        (
                            expected_decision_rewards,
                            expected_settlement_rewards,
                            [],
                        ),
                        (
                            reward_trace.get("decision_rewards"),
                            reward_trace.get("settlement_rewards"),
                            reward_trace.get("nonzero_outside_ledger_rows"),
                        ),
                    )
                    episode = episodes[tape.identity.episode_id]
                    _require_rollout_equal(
                        "EPISODE_LEDGER_MISMATCH", source,
                        f"update-{update}:episode-{episode_offset}",
                        (
                            update, update,
                            float(reward_tensor.sum(dtype=torch.float32).item()),
                            *action_counts,
                        ),
                        (
                            episode["rollout_update"], episode["policy_version"],
                            episode["episode_return"],
                            episode["action_count_serve"],
                            episode["action_count_refresh"],
                            episode["action_count_safe_fallback"],
                        ),
                    )

                for epoch in range(4):
                    if test_only:
                        order, addresses = (0,), ()
                    else:
                        order, addresses = ordered_episode_indices(
                            B1_RUN_NAME, seed, update, epoch,
                            address_u64=addressing.u64,
                        )
                    payload = {
                        "update": update, "epoch": epoch, "order": list(order),
                        "addresses": [list(address) for address in addresses],
                    }
                    encoded = json.dumps(
                        payload, ensure_ascii=True, separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8")
                    order_digest = hashlib.sha256(
                        bytes.fromhex(order_digest) + encoded
                    ).hexdigest()
                    for minibatch in range(minibatches_per_epoch):
                        selected = order if test_only else order[2 * minibatch : 2 * minibatch + 2]
                        step = optimizer[(update, epoch, minibatch)]
                        _require_rollout_equal(
                            "MINIBATCH_ORDER_ROWS_MISMATCH", source,
                            f"update-{update}:epoch-{epoch}:minibatch-{minibatch}",
                            [update * episodes_per_update + index for index in selected],
                            step["ordered_episode_ids"],
                        )
                _require_rollout_equal(
                    "MINIBATCH_ORDER_CHAIN_MISMATCH", source, f"update-{update}",
                    order_digest, record.get("minibatch_order_digest_after"),
                )
                expected_counters = {
                    "rollout_updates": update + 1,
                    "adam_steps": (update + 1) * 4 * minibatches_per_epoch,
                    "train_episodes": (update + 1) * episodes_per_update,
                    "train_transitions": (
                        (update + 1) * episodes_per_update * EPISODE_TRANSITIONS
                    ),
                    "train_decisions": (
                        (update + 1) * episodes_per_update * OPPORTUNITY_COUNT
                    ),
                }
                _require_rollout_equal(
                    "TRAINING_COUNTER_MISMATCH", source, f"update-{update}",
                    expected_counters, record.get("counters_after"),
                )
                last_step = optimizer[(update, 3, minibatches_per_epoch - 1)]
                _require_rollout_equal(
                    "MODEL_PARAMETER_CHAIN_MISMATCH", source, f"update-{update}",
                    last_step["parameter_sha256_after_step"],
                    record.get("model_parameter_digest_after"),
                )
                try:
                    _digest(
                        record.get("optimizer_digest_after"),
                        f"rollout {update} optimizer digest",
                    )
                except B1MetricsTrainingAssemblyError:
                    _rollout_adverse(
                        "OPTIMIZER_DIGEST_SCHEMA_MISMATCH", source,
                        f"update-{update}",
                    )
                rows.append(_pointer_audit_row(
                    source=source, provenance=provenance,
                    json_pointer=(
                        f"{provenance['raw_json_pointer']}/rollouts/{offset}"
                    ),
                    audit_code=(
                        f"S{seed}:A{arm_order}:I{attempt_order}:ROLLOUT:{update}"
                    ),
                    fact_name=f"rollout-update-{update}",
                    expected=record, observed=record,
                ))

            final_rollout = raw_rollouts[-1]
            final_pairs = (
                ("FINAL_COUNTER_MISMATCH", "final_counters", "counters_after"),
                (
                    "FINAL_MODEL_PARAMETER_MISMATCH",
                    "final_model_parameter_digest", "model_parameter_digest_after",
                ),
                (
                    "FINAL_OPTIMIZER_MISMATCH",
                    "final_optimizer_digest", "optimizer_digest_after",
                ),
                (
                    "FINAL_MINIBATCH_ORDER_MISMATCH",
                    "final_minibatch_order_digest", "minibatch_order_digest_after",
                ),
            )
            for code, top_field, rollout_field in final_pairs:
                _require_rollout_equal(
                    code, source, f"slice-{start}-{stop}",
                    final_rollout.get(rollout_field), raw.get(top_field),
                )

        if last_update != 47:
            _rollout_adverse(
                "ROLLOUT_UPDATE_COVERAGE_MISMATCH", _rollout_source(group[-1], len(group) - 1),
                "formal-0-47",
            )
        expected_tape_digest = _json_sha256(full_tape_records)
        expected_action_digest = _json_sha256(full_uniform_records)
        for attempt_order, (raw, provenance) in enumerate(
            zip(group, provenance_group, strict=True)
        ):
            source = _rollout_source(raw, attempt_order)
            binding = raw.get("full_bindings")
            if not isinstance(binding, Mapping):
                _rollout_adverse(
                    "FULL_PANEL_BINDING_MISMATCH", source, "full-bindings"
                )
            _require_rollout_equal(
                "FULL_TRAINING_TAPE_DIGEST_MISMATCH", source, "full-panel",
                expected_tape_digest, binding.get("full_training_tape_digest"),
            )
            _require_rollout_equal(
                "FULL_ACTION_UNIFORM_DIGEST_MISMATCH", source, "full-panel",
                expected_action_digest, binding.get("full_action_uniform_digest"),
            )
            rows.append(_pointer_audit_row(
                source=source, provenance=provenance,
                json_pointer=f"{provenance['raw_json_pointer']}/full_bindings",
                audit_code=(
                    f"S{seed}:A{arm_order}:I{attempt_order}:ROLLOUT:FULL_PANEL"
                ),
                fact_name="full-training-panel-bindings",
                expected=binding, observed=binding,
            ))
    return rows


def _audit_rows(
    *, raw_groups: Sequence[Sequence[Mapping[str, Any]]],
    source_groups: Sequence[Sequence[Mapping[str, str]]],
    authority_tables: Mapping[str, list[Mapping[str, Any]]],
    rollout_audit_rows: Sequence[Mapping[str, Any]],
    test_only: bool,
) -> list[dict[str, Any]]:
    rows = [
        *_table_audit_rows(authority_tables),
        *_direct_audit_rows(raw_groups, source_groups, test_only=test_only),
        *(dict(row) for row in rollout_audit_rows),
    ]
    rows.sort(key=lambda row: (
        row["run_order"], row["attempt_order"], row["seed_or_minus_one"],
        row["arm_or_minus_one"], row["audit_code"],
    ))
    keys = [
        (row["run_order"], row["attempt_order"], row["seed_or_minus_one"],
         row["arm_or_minus_one"], row["audit_code"])
        for row in rows
    ]
    if len(keys) != len(set(keys)) or any(frozenset(row) != _AUDIT_FIELDS for row in rows):
        raise B1MetricsTrainingAssemblyError("audit authority key/schema differs")
    return rows


def finalize_audit_table_bindings(
    audit_rows: Sequence[Mapping[str, Any]],
    materialized_table_records: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Bind audit table references only to independently reread materialized bytes."""

    if not isinstance(audit_rows, Sequence) or isinstance(audit_rows, (str, bytes, bytearray)):
        raise B1MetricsTrainingAssemblyError("audit authority rows must be a sequence")
    rows = [dict(row) for row in audit_rows]
    if any(frozenset(row) != _AUDIT_FIELDS for row in rows):
        raise B1MetricsTrainingAssemblyError("audit authority row schema differs")
    table_rows = {
        row["source_table"]: row
        for row in rows if row["authority_type"] == "CANONICAL_TABLE_AUTHORITY"
    }
    if (
        not isinstance(materialized_table_records, list)
        or any(
            not isinstance(record, Mapping)
            or frozenset(record) != _MATERIALIZED_TABLE_BINDING_FIELDS
            for record in materialized_table_records
        )
    ):
        raise B1MetricsTrainingAssemblyError("materialized table binding schema differs")
    materialized = {record["source_table"]: record for record in materialized_table_records}
    if (
        len(materialized) != len(materialized_table_records)
        or set(materialized) != set(table_rows)
    ):
        raise B1MetricsTrainingAssemblyError(
            "materialized table inventory does not cover audit authority coverage"
        )
    for table, audit in table_rows.items():
        actual = materialized[table]
        expected_range = audit["source_key_range"]
        if (
            _digest(actual["actual_sha256"], f"{table} materialized SHA")
            != audit["expected_sha256"]
            or actual["actual_row_count"] != audit["expected"]["row_count"]
            or actual["actual_first_key"] != expected_range["first_key"]
            or actual["actual_last_key"] != expected_range["last_key"]
        ):
            raise B1MetricsTrainingAssemblyError(
                f"materialized table reread binding differs: {table}"
            )
        audit["observed"] = {"row_count": actual["actual_row_count"]}
        audit["actual_sha256"] = actual["actual_sha256"]
        audit["binding_status"] = "BOUND_MATERIALIZED_TABLE_REREAD"
    return rows


def finalize_audit_pointer_bindings(
    audit_rows: Sequence[Mapping[str, Any]], source_root: str | Path,
) -> list[dict[str, Any]]:
    """Reread every direct raw pointer from its exact worker-result bytes."""

    if not isinstance(audit_rows, Sequence) or isinstance(
        audit_rows, (str, bytes, bytearray)
    ):
        raise B1MetricsTrainingAssemblyError("audit authority rows must be a sequence")
    rows = [dict(row) for row in audit_rows]
    if any(frozenset(row) != _AUDIT_FIELDS for row in rows):
        raise B1MetricsTrainingAssemblyError("audit authority row schema differs")
    root = Path(source_root).resolve(strict=True)
    documents: dict[str, tuple[bytes, Mapping[str, Any]]] = {}
    direct_rows = [row for row in rows if row["authority_type"] == "DIRECT_RAW_FACT"]
    if not direct_rows:
        raise B1MetricsTrainingAssemblyError("direct raw pointer inventory is empty")
    for row in direct_rows:
        relative = row["source_relative_path"]
        pointer = row["json_pointer"]
        if (
            type(relative) is not str or type(pointer) is not str
            or type(row["source_file_sha256"]) is not str
            or not relative.endswith("/result.json.gz")
            or not pointer.startswith("/raw_evidence/")
        ):
            raise B1MetricsTrainingAssemblyError("direct raw pointer schema differs")
        if relative not in documents:
            source = (root / relative).resolve(strict=True)
            try:
                source.relative_to(root)
            except ValueError as exc:
                raise B1MetricsTrainingAssemblyError(
                    "direct raw source escapes source root"
                ) from exc
            try:
                stored = source.read_bytes()
                payload = gzip.decompress(stored)
            except (OSError, EOFError) as exc:
                raise B1MetricsTrainingAssemblyError(
                    "direct raw worker result is unreadable"
                ) from exc
            if hashlib.sha256(payload).hexdigest() != row["source_file_sha256"]:
                raise B1MetricsTrainingAssemblyError("direct raw source file SHA differs")
            try:
                document = json.loads(payload.decode("ascii"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise B1MetricsTrainingAssemblyError(
                    "direct raw worker result is unreadable"
                ) from exc
            if (
                not isinstance(document, Mapping)
                or set(document) != {"schema", "raw_evidence", "scientific_branch"}
                or type(document["schema"]) is not str or not document["schema"]
                or document["scientific_branch"] is not None
                or not isinstance(document["raw_evidence"], Mapping)
                or canonical_json_bytes(document) + b"\n" != payload
            ):
                raise B1MetricsTrainingAssemblyError(
                    "direct raw worker result wrapper differs"
                )
            documents[relative] = (payload, document)
        payload, document = documents[relative]
        if hashlib.sha256(payload).hexdigest() != row["source_file_sha256"]:
            raise B1MetricsTrainingAssemblyError("direct raw source file SHA differs")
        raw = document["raw_evidence"]
        identity = row["source_raw_slice"]
        interval = raw.get("slice") if isinstance(raw, Mapping) else None
        if (
            not isinstance(identity, Mapping) or not isinstance(interval, Mapping)
            or raw.get("attempt_id") != identity.get("attempt_id")
            or raw.get("seed") != identity.get("seed")
            or raw.get("arm") not in ARM_ORDER
            or ARM_ORDER[raw["arm"]] != identity.get("arm_order")
            or interval.get("start_update") != identity.get("slice_start_update")
            or interval.get("stop_update") != identity.get("slice_stop_update")
        ):
            raise B1MetricsTrainingAssemblyError(
                "direct raw worker result identity differs"
            )
        observed = _json_pointer_get(document, pointer)
        observed_sha = hashlib.sha256(canonical_json_bytes(observed)).hexdigest()
        if observed_sha != row["actual_sha256"]:
            raise B1MetricsTrainingAssemblyError(
                "direct raw JSON pointer payload SHA differs"
            )
        if (
            _payload_shape(observed) != row["payload_shape"]
            or _payload_dtype(observed) != row["payload_dtype"]
            or _payload_nonzero_count(observed) != row["payload_nonzero_count"]
        ):
            raise B1MetricsTrainingAssemblyError(
                "direct raw JSON pointer payload metadata differs"
            )
        _digest(row["expected_sha256"], "direct raw expected payload SHA")
        if row["binding_status"] not in {
            "DIRECT_RAW_FACT", "DIRECT_RAW_FACT_ADVERSE"
        }:
            raise B1MetricsTrainingAssemblyError(
                "direct raw pointer pre-reread status differs"
            )
        row["binding_status"] = (
            "BOUND_SOURCE_REREAD" if row["expected_sha256"] == observed_sha
            else "BOUND_SOURCE_REREAD_ADVERSE"
        )
    return rows


def _materialized_digest_rows(value: object, category: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise B1MetricsTrainingAssemblyError(
            "finalization requires three direct materialized digest inventories"
        )
    output: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, Mapping) or frozenset(row) != _MATERIALIZED_DIGEST_FIELDS:
            raise B1MetricsTrainingAssemblyError(
                f"{category} materialized digest record schema differs"
            )
        name = row["name"]
        if type(name) is not str or not name or name.strip() != name:
            raise B1MetricsTrainingAssemblyError(
                f"{category} materialized digest name differs"
            )
        expected_sha = _digest(row["expected_sha256"], f"{category} expected SHA")
        actual_sha = _digest(row["actual_sha256"], f"{category} actual SHA")
        expected_bytes = row["expected_byte_count"]
        actual_bytes = row["actual_byte_count"]
        if (
            type(expected_bytes) is not int or expected_bytes < 0
            or type(actual_bytes) is not int or actual_bytes < 0
        ):
            raise B1MetricsTrainingAssemblyError(
                f"{category} materialized byte count differs"
            )
        prefix = f"{category}:{name}"
        output.extend([
            {
                "name": f"{prefix}:sha256",
                "expected_sha256": expected_sha,
                "observed_sha256": actual_sha,
            },
            {
                "name": f"{prefix}:byte-count",
                "expected_sha256": hashlib.sha256(
                    str(expected_bytes).encode("ascii")
                ).hexdigest(),
                "observed_sha256": hashlib.sha256(
                    str(actual_bytes).encode("ascii")
                ).hexdigest(),
            },
        ])
    return output


def finalize_materialized_raw_facts(
    prepublication_raw_facts: Mapping[str, Any],
    *,
    table_digest_records: list[Mapping[str, Any]],
    artifact_digest_records: list[Mapping[str, Any]],
    checkpoint_digest_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind only bytes reread after materialization into final mechanical facts."""

    if (
        not isinstance(prepublication_raw_facts, Mapping)
        or frozenset(prepublication_raw_facts) != _RAW_FACT_FIELDS
        or prepublication_raw_facts.get("digest_bindings") != _PENDING_DIGEST_BINDINGS
    ):
        raise B1MetricsTrainingAssemblyError(
            "prepublication raw facts are not pending materialization reread"
        )
    bindings = [
        *_materialized_digest_rows(table_digest_records, "table"),
        *_materialized_digest_rows(artifact_digest_records, "artifact"),
        *_materialized_digest_rows(checkpoint_digest_records, "checkpoint"),
    ]
    names = [row["name"] for row in bindings]
    if len(names) != len(set(names)):
        raise B1MetricsTrainingAssemblyError("materialized digest record name is duplicated")
    finalized = deepcopy(dict(prepublication_raw_facts))
    finalized["digest_bindings"] = bindings
    return finalized


def assemble_b1_metrics_training(
    *,
    raw_slice_groups: Sequence[Sequence[Mapping[str, Any]]],
    raw_source_groups: Sequence[Sequence[Mapping[str, Any]]] | None = None,
    admission_groups: Sequence[Sequence[Mapping[str, Any]]],
    telemetry_groups: Sequence[Sequence[Mapping[str, Any]]],
    policy_replay_resources: Mapping[str, object] | None = None,
    shared_tables: Mapping[str, object],
    policy_tables: Mapping[str, object],
    test_only: bool = False,
) -> dict[str, Any]:
    """Assemble direct training/resource/mechanical tables without interpretation."""

    if type(test_only) is not bool:
        raise B1MetricsTrainingAssemblyError("test_only must be a bool")
    raw_groups = list(_sequence(raw_slice_groups, "raw_slice_groups"))
    admission_values = list(_sequence(admission_groups, "admission_groups"))
    telemetry_values = list(_sequence(telemetry_groups, "telemetry_groups"))
    if len(raw_groups) != len(admission_values) or len(raw_groups) != len(telemetry_values):
        raise B1MetricsTrainingAssemblyError("raw/admission/telemetry group inventory differs")
    if not isinstance(shared_tables, Mapping) or not isinstance(policy_tables, Mapping):
        raise B1MetricsTrainingAssemblyError("shared/policy tables must be mappings")
    identities = _validate_group_shapes(raw_groups, test_only=test_only)
    if raw_source_groups is None:
        if not test_only:
            raise B1MetricsTrainingAssemblyError(
                "UPSTREAM_INSTRUMENTATION_GAP: formal raw worker result path/SHA/pointer "
                "descriptors are absent"
            )
        source_groups = _synthetic_test_sources(raw_groups)
    else:
        source_groups = _validate_source_groups(raw_source_groups, raw_groups)
    merged = [
        _merge_training_group(group, identity, test_only=test_only)
        for group, identity in zip(raw_groups, identities, strict=True)
    ]

    admission_rows: list[dict[str, Any]] = []
    telemetry_rows: list[dict[str, Any]] = []
    attempt_ids = {raw[0].get("attempt_id") for raw in raw_groups}
    if len(attempt_ids) != 1 or not all(type(value) is str and value for value in attempt_ids):
        raise B1MetricsTrainingAssemblyError("assembly must bind one exact attempt_id")
    attempt_id = next(iter(attempt_ids))
    for group_index, ((seed, arm), raw_group, admission_group, telemetry_group) in enumerate(
        zip(identities, raw_groups, admission_values, telemetry_values, strict=True)
    ):
        if len(raw_group) != len(admission_group) or len(raw_group) != len(telemetry_group):
            raise B1MetricsTrainingAssemblyError("per-slot invocation fact inventory differs")
        for invocation_order, (admission, telemetry) in enumerate(
            zip(admission_group, telemetry_group, strict=True)
        ):
            admitted = _validate_admission(
                admission, attempt_order=invocation_order,
                attempt_id=attempt_id, seed=seed, arm=arm
            )
            measured = _validate_telemetry_fact(
                telemetry, attempt_order=invocation_order,
                attempt_id=attempt_id, seed=seed, arm=arm
            )
            raw = raw_group[invocation_order]
            interval = raw.get("slice")
            counts = raw.get("slice_counts")
            if not isinstance(interval, Mapping) or not isinstance(counts, Mapping):
                raise B1MetricsTrainingAssemblyError("raw slice work identity is absent")
            for field in ("train_transitions", "evaluation_transitions"):
                if type(counts.get(field)) is not int or counts[field] < 0:
                    raise B1MetricsTrainingAssemblyError("raw slice work count differs")
            raw_slice_work = counts["train_transitions"] + counts["evaluation_transitions"]
            admission_rows.append({
                "run_order": 0, "invocation_kind": "TRAINING_SLICE",
                "original_slot_index": group_index,
                "attempt_order": admitted["attempt_order"],
                "seed": seed, "arm_order": ARM_ORDER[arm], "run_name": B1_RUN_NAME,
                "arm": arm, "attempt_id": attempt_id,
                "slice_start_update": interval["start_update"],
                "slice_stop_update": interval["stop_update"],
                "receipt_sha256": admitted["receipt_sha256"],
                "available_physical_bytes": admitted["available_physical_bytes"],
                "effective_available_bytes": admitted["effective_available_bytes"],
            })
            telemetry_rows.append({
                "run_order": 0, "invocation_kind": "TRAINING_SLICE",
                "original_slot_index": group_index,
                "attempt_order": measured["attempt_order"],
                "seed": seed, "arm_order": ARM_ORDER[arm], "run_name": B1_RUN_NAME,
                "arm": arm, "attempt_id": attempt_id,
                "slice_start_update": interval["start_update"],
                "slice_stop_update": interval["stop_update"],
                "measurement": measured["measurement"],
            })
    replay_admissions, replay_telemetry, _ = _validate_policy_replay_resources(
        policy_replay_resources, attempt_id=attempt_id, test_only=test_only
    )
    admission_rows.extend(replay_admissions)
    telemetry_rows.extend(replay_telemetry)
    invocation_kind_order = {"TRAINING_SLICE": 0, "POLICY_REPLAY": 1}
    invocation_key = lambda row: (
        row["run_order"], invocation_kind_order[row["invocation_kind"]],
        row["original_slot_index"], row["attempt_order"], row["seed"], row["arm_order"],
    )
    admission_rows.sort(key=invocation_key)
    telemetry_rows.sort(key=invocation_key)

    training_decisions = sorted(
        (dict(row) for records in merged for row in records.training_decisions),
        key=lambda row: (row["run_order"], row["seed"], row["arm_order"],
                         row["training_episode_id"], row["opportunity_id"]),
    )
    training_episodes = sorted(
        (dict(row) for records in merged for row in records.training_episodes),
        key=lambda row: (row["run_order"], row["seed"], row["arm_order"], row["training_episode_id"]),
    )
    optimizer_steps = sorted(
        (dict(row) for records in merged for row in records.optimizer_steps),
        key=lambda row: (row["run_order"], row["seed"], row["arm_order"],
                         row["rollout_update"], row["ppo_epoch"], row["minibatch_index"]),
    )
    competence_inputs = _competence_inputs(
        shared_tables, policy_tables, test_only=test_only
    )
    raw_facts = _raw_facts(
        raw_groups=raw_groups, identities=identities, merged=merged,
        admission_rows=admission_rows, telemetry_rows=telemetry_rows,
        shared_tables=shared_tables, policy_tables=policy_tables,
        test_only=test_only,
    )
    raw_competence = [compute_raw_competence(record) for record in competence_inputs]
    rollout_audits = _rollout_rng_audit_rows(
        raw_groups=raw_groups, merged=merged, source_groups=source_groups,
        test_only=test_only,
    )
    authority_tables = {
        "training_decisions": training_decisions,
        "training_episodes": training_episodes,
        "optimizer_steps": optimizer_steps,
        "resource_admissions": admission_rows,
        "telemetry": telemetry_rows,
        "raw_competence": raw_competence,
        "policy_decisions": list(policy_tables["policy_decisions"]),
        "per_tape_curves": list(policy_tables["per_tape_curves"]),
        "evaluator_decision_truth": list(shared_tables["evaluator_decision_truth"]),
        "motif_twin_index": list(shared_tables["motif_twin_index"]),
    }
    audits = _audit_rows(
        raw_groups=raw_groups, source_groups=source_groups,
        authority_tables=authority_tables,
        rollout_audit_rows=rollout_audits,
        test_only=test_only,
    )
    tables = {
        "training_decisions": training_decisions,
        "training_episodes": training_episodes,
        "optimizer_steps": optimizer_steps,
        "resource_admissions": admission_rows,
        "telemetry": telemetry_rows,
        "audits": audits,
        "raw_competence": deepcopy(raw_competence),
    }
    return {
        "schema": ASSEMBLY_SCHEMA,
        "test_only": test_only,
        "attempt_id": attempt_id,
        "tables": tables,
        "prepublication_raw_facts": raw_facts,
        "raw_competence_inputs": competence_inputs,
        "prepublication_status": {
            "status": "PENDING_MATERIALIZATION_REREAD",
            "mechanical_attempt_complete": False,
            "mechanical_conformance_pass": False,
            "scientific_packet_readable": False,
            "publication_digests": None,
        },
        "raw_competence_truth_authority": not test_only,
        "formal_readiness_authority": not test_only,
        "audit_row_count": len(audits),
        "upstream_instrumentation_gaps": [],
    }


__all__ = [
    "ASSEMBLY_SCHEMA",
    "B1MetricsTrainingAssemblyError",
    "FORMAL_ARM_SEED_ORDER",
    "assemble_b1_metrics_training",
    "finalize_audit_pointer_bindings",
    "finalize_audit_table_bindings",
    "finalize_materialized_raw_facts",
    "reconstruct_raw_competence_from_tables",
]

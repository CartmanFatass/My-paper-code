"""Read-only validator and permanent tombstone for the consumed CRTO K8 census.

Importing this module does not load the tape builder, legacy host, G16 bridge,
learner, Torch, checkpoint, pilot, or production execution surfaces.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Mapping, Sequence

from .config import (
    AUDIT_HORIZON,
    MATERIAL_ADVANTAGE_THRESHOLD,
    MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM,
    PEAK_RSS_BYTES,
    SUPPORT_CENSUS_EPISODES_PER_SLOT,
    SUPPORT_CENSUS_CLAIM_CEILING,
    SUPPORT_CENSUS_CONSUMED_ATTEMPT,
    SUPPORT_CENSUS_COMMIT_CPU_HEADROOM_SECONDS,
    SUPPORT_CENSUS_COMMIT_IO_READ_HEADROOM_BYTES,
    SUPPORT_CENSUS_COMMIT_IO_WRITE_HEADROOM_BYTES,
    SUPPORT_CENSUS_COMMIT_RSS_HEADROOM_BYTES,
    SUPPORT_CENSUS_COMMIT_WALL_HEADROOM_SECONDS,
    SUPPORT_CENSUS_FIRST_EPISODE,
    SUPPORT_CENSUS_FRESH_EXECUTION_ENABLED,
    SUPPORT_CENSUS_LAUNCH_RUN_ID,
    SUPPORT_CENSUS_LIFECYCLE,
    SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
    SUPPORT_CENSUS_OBJECT_ID,
    SUPPORT_CENSUS_PERFORMANCE_DISPOSITION,
    SUPPORT_CENSUS_RNG_NAMESPACE,
    SUPPORT_CENSUS_SLOTS,
    SUPPORT_CENSUS_TERMINAL_DISPOSITION,
    SUPPORT_CENSUS_TOMBSTONE_REASON,
    SupportCensusConsumedError,
    WALL_SECONDS,
    refuse_consumed_support_census,
)
from .contracts import ACTION_ORDER, Split


FORMAT = "CRTO_K8_FIRST_BOUNDARY_SUPPORT_CENSUS_V1"
OBSERVATION_FORMAT = "CRTO_K8_FIRST_BOUNDARY_SUPPORT_OBSERVATION_V1"
SELECTION_LAW = "PRIMITIVE_TIME_THEN_ENVIRONMENT_SLOT_FIRST_LEGAL_DISCRETIONARY"
RECEIPT_NAME = "support_census_receipt.json"
PUBLICATION_MARKER_NAME = "PUBLICATION_COMPLETE.json"
PERFORMANCE_REASON = (
    "MAX_393216_MATERIALIZATION_PLUS_INDEPENDENT_FULL_REPLAY_STEPS_LT_OBSERVED_484096_"
    "SUPPORT_STOP_AND_NO_TORCH_OR_MODEL"
)
INDEPENDENT_REPLAY_MODE = "INDEPENDENT_CANONICAL_REBUILD_FULL_G16_REPLAY"
RUNTIME_MEASUREMENT_CUTOFF = "AFTER_FINAL_DUAL_STAGING_FSYNC_BEFORE_COMMIT_RENAMES"
COMMIT_HEADROOM = {
    "wall_seconds": SUPPORT_CENSUS_COMMIT_WALL_HEADROOM_SECONDS,
    "cpu_seconds": SUPPORT_CENSUS_COMMIT_CPU_HEADROOM_SECONDS,
    "peak_rss_bytes": SUPPORT_CENSUS_COMMIT_RSS_HEADROOM_BYTES,
    "io_read_bytes": SUPPORT_CENSUS_COMMIT_IO_READ_HEADROOM_BYTES,
    "io_write_bytes": SUPPORT_CENSUS_COMMIT_IO_WRITE_HEADROOM_BYTES,
}

DISPOSITION_FEASIBLE = "CENSUS_SUPPORT_FEASIBLE"
DISPOSITION_KEEP_MINIMUM_FAIL = "CENSUS_KEEP_WITNESS_BUT_KEEP_MINIMUM_FAIL"
DISPOSITION_REPLAN_MINIMUM_FAIL = "CENSUS_KEEP_MINIMUM_PASS_REPLAN_MINIMUM_FAIL"
DISPOSITION_NO_KEEP = "CENSUS_NO_KEEP_WITNESS_ON_FIXED_TARGET"

_BOUNDARY_ABSENT_KEYS = frozenset({"row_present", "scripted_history_transitions"})
_SPEC_KEYS = frozenset({
    "episode_index", "episode_seed", "regime", "event", "event_onset",
    "replanning_cost",
})
_BOUNDARY_KEYS = frozenset({
    "row_present", "scripted_history_transitions", "primitive_time",
    "environment_slot", "elapsed_horizon", "previous_option", "legal_mask", "g16",
    "denominator", "branches", "keep_g16", "max_replacement_g16",
    "maximizing_replacement", "advantage", "material_class",
})
_BRANCH_KEYS = frozenset({
    "printed_index", "action", "selected_option", "intervention_charge",
    "intervention_charge_step", "g16", "steps", "terminal_state",
})
_STEP_KEYS = frozenset({
    "primitive_time", "k", "event_active", "physical_queues_before",
    "deployable_queues_before", "buffers_before", "arrivals", "relay_capacity",
    "tracked", "delivered", "overflow", "energy_spent", "decision_charge", "reward",
    "physical_queues_after", "buffers_after", "decisions",
})
_DECISION_KEYS = frozenset({
    "agent", "kind", "previous_option", "selected_option", "changed", "charge",
    "age_before", "age_after_decision", "switch_time", "reanchored",
})
_TERMINAL_KEYS = frozenset({
    "primitive_time", "queues", "buffers", "locations", "energies", "options",
    "option_ages", "current_k", "terminal_potential",
})
_RUNTIME_KEYS = frozenset({
    "workers", "threads_per_worker", "base_episode_count",
    "charged_base_primitive_team_steps", "scripted_history_transitions",
    "actual_common_future_branch_count", "actual_common_future_steps",
    "materialization_base_episode_count",
    "materialization_charged_base_primitive_team_steps",
    "materialization_scripted_history_transitions",
    "materialization_common_future_branch_count",
    "materialization_common_future_steps",
    "validation_base_episode_count", "validation_charged_base_primitive_team_steps",
    "validation_scripted_history_transitions",
    "validation_common_future_branch_count", "validation_common_future_steps",
    "actual_total_charged_primitive_team_steps", "primitive_team_step_ceiling",
    "wall_seconds", "wall_ceiling_seconds", "peak_rss_bytes", "peak_rss_ceiling_bytes",
    "cpu_seconds", "cpu_occupancy_fraction", "scratch_high_water_bytes",
    "durable_high_water_bytes", "io_read_bytes", "io_write_bytes",
    "measurement_cutoff", "commit_tail_excluded", "commit_headroom",
    "final_candidate_staging_rehearsal_observed",
})
_ACTIVITY_KEYS = frozenset({
    "support_tapes_materialized", "support_boundaries_materialized",
    "materialization_support_tapes", "validation_support_tapes",
    "materialization_support_boundaries", "validation_support_boundaries",
    "common_future_rollouts", "materialization_common_future_rollouts",
    "validation_common_future_rollouts", "learner_models_constructed",
    "predictor_models_constructed", "gate_models_constructed", "optimizer_updates",
    "checkpoints", "true_residual_activity", "deranged_activity",
    "final_namespace_reads", "pilot_namespace_reads",
})
_INDEPENDENT_REPLAY_KEYS = frozenset({
    "mode", "rebuilt_tapes", "scenario_spec_direct_matches",
    "array_raw_byte_direct_matches", "raw_bytes_compared_per_side",
    "complete_boundary_provenance_direct_matches", "tape_array_inventory",
})
TAPE_ARRAY_INVENTORY = (
    {"field": "initial_locations", "dtype": "int8", "shape": [4], "raw_byte_length": 4},
    {"field": "arrival_hot_coin", "dtype": "int8", "shape": [256], "raw_byte_length": 256},
    {"field": "arrival_cold_coin", "dtype": "int8", "shape": [256], "raw_byte_length": 256},
    {
        "field": "relay_capacity_coin", "dtype": "int8", "shape": [256, 2],
        "raw_byte_length": 512,
    },
    {
        "field": "option_uniform", "dtype": "float64", "shape": [256, 4],
        "raw_byte_length": 8192,
    },
    {
        "field": "rate_control_uniform", "dtype": "float64", "shape": [256, 4],
        "raw_byte_length": 8192,
    },
)
_MINIMUM_AVAILABLE_BYTES = 4 * 1024**3


class SupportCensusError(ValueError):
    """The support receipt is incomplete, malformed, or outside its registration."""


def _is_int(value: object) -> bool:
    return type(value) is int


def _finite(value: object) -> bool:
    return type(value) in (int, float) and not isinstance(value, bool) and math.isfinite(value)


def _require_keys(value: object, keys: frozenset[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != keys:
        observed = set(value) if isinstance(value, Mapping) else set()
        raise SupportCensusError(f"{label} key inventory mismatch: {sorted(observed ^ keys)}")
    return value


def _validate_resource_receipt(receipt: Mapping[str, object]) -> tuple[str, ...]:
    """Validate the persisted memory receipt without importing execution preflight."""

    issues: list[str] = []
    if receipt.get("schema_version") != 1:
        issues.append("shared resource receipt schema_version must equal 1")
    if receipt.get("minimum_available_bytes") != _MINIMUM_AVAILABLE_BYTES:
        issues.append("shared resource receipt does not bind the exact 4-GiB floor")
    for field in ("available_physical_bytes", "effective_available_bytes"):
        value = receipt.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < _MINIMUM_AVAILABLE_BYTES
        ):
            issues.append(f"shared resource receipt {field} is absent or below 4 GiB")
    if receipt.get("physical_floor_pass") is not True:
        issues.append("shared resource receipt physical floor did not pass")
    if receipt.get("effective_floor_pass") is not True:
        issues.append("shared resource receipt effective floor did not pass")
    if receipt.get("passed") is not True:
        issues.append("shared resource receipt final admission did not pass")
    reasons = receipt.get("failure_reasons")
    if not isinstance(reasons, list) or reasons:
        issues.append("shared resource receipt contains missing or nonempty failure reasons")
    return tuple(issues)


def _validate_run_resource_receipt(receipt: Mapping[str, object]) -> tuple[str, ...]:
    """Validate the persisted run estimate without importing execution preflight."""

    issues: list[str] = []
    expected = {
        "workers": 1,
        "threads_per_worker": 1,
        "minimum_available_bytes": _MINIMUM_AVAILABLE_BYTES,
    }
    for field, expected_value in expected.items():
        if receipt.get(field) != expected_value:
            issues.append(
                f"shared assess-run receipt {field} must equal {expected_value}"
            )
    estimate = receipt.get("estimate")
    if not isinstance(estimate, Mapping):
        issues.append("shared assess-run receipt estimate is missing")
    else:
        try:
            wall = float(estimate.get("wall_seconds", -1))
            peak = float(estimate.get("peak_memory_gib", -1))
        except (TypeError, ValueError):
            wall = peak = -1.0
        if wall != 7_200.0:
            issues.append("shared assess-run wall estimate must equal 7,200 seconds")
        if peak != 2.0:
            issues.append("shared assess-run peak estimate must equal 2 GiB")
    if receipt.get("physical_floor_pass") is not True:
        issues.append("shared assess-run physical 4-GiB floor did not pass")
    if receipt.get("effective_floor_pass") is not True:
        issues.append("shared assess-run effective 4-GiB floor did not pass")
    if (
        receipt.get("memory_floor_pass") is not True
        or receipt.get("memory_safe") is not True
    ):
        issues.append("shared assess-run memory admission did not pass")
    return tuple(issues)


def _expected_tapes(slot: int) -> tuple[object, ...]:
    refuse_consumed_support_census()


def _expected_tape(slot: int, episode_index: int) -> object:
    refuse_consumed_support_census()


def registered_support_tapes(slot: int) -> tuple[object, ...]:
    """Return the create-once registered tape tuple used by execution and validation."""

    refuse_consumed_support_census()


def _observed_tape_array_inventory(tape: object) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for expected in TAPE_ARRAY_INVENTORY:
        array = getattr(tape, str(expected["field"]))
        inventory.append({
            "field": expected["field"],
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "raw_byte_length": int(array.nbytes),
        })
    return inventory


def _compare_independently_rebuilt_tape(original: object, rebuilt: object) -> None:
    expected_inventory = [dict(item) for item in TAPE_ARRAY_INVENTORY]
    if (
        _observed_tape_array_inventory(original) != expected_inventory
        or _observed_tape_array_inventory(rebuilt) != expected_inventory
        or _spec_record(original) != _spec_record(rebuilt)
    ):
        raise SupportCensusError(
            "independently rebuilt support tape shape, dtype, byte length, or spec drifted"
        )
    for item in TAPE_ARRAY_INVENTORY:
        field = str(item["field"])
        if getattr(original, field).tobytes(order="C") != getattr(
            rebuilt, field
        ).tobytes(order="C"):
            raise SupportCensusError(
                "independently rebuilt support tape raw bytes differ from first construction"
            )


def _spec_record(tape: object) -> dict[str, object]:
    spec = tape.spec
    return {
        "episode_index": int(spec.episode_index),
        "episode_seed": int(spec.episode_seed),
        "regime": spec.regime.value,
        "event": spec.event.value,
        "event_onset": int(spec.event_onset),
        "replanning_cost": float(spec.replanning_cost),
    }


def _classify(advantage: float) -> str:
    if advantage <= -MATERIAL_ADVANTAGE_THRESHOLD:
        return "KEEP"
    if advantage >= MATERIAL_ADVANTAGE_THRESHOLD:
        return "REPLAN"
    return "MIDDLE"


def _complete_boundary_summary(boundary: Mapping[str, object]) -> dict[str, object]:
    result = dict(boundary)
    if result.get("row_present") is not True:
        return result
    legal_mask = result["legal_mask"]
    g16 = result["g16"]
    replacements = [index for index in range(1, 8) if legal_mask[index]]
    maximizing = max(replacements, key=lambda index: (g16[index], -index))
    keep = float(g16[0])
    maximum = float(g16[maximizing])
    advantage = maximum - keep
    result.update({
        "keep_g16": keep,
        "max_replacement_g16": maximum,
        "maximizing_replacement": maximizing,
        "advantage": advantage,
        "material_class": _classify(advantage),
    })
    return result


def _boundary_scan_record(boundary: Mapping[str, object]) -> dict[str, object]:
    if boundary.get("row_present") is False:
        return {
            "row_present": False,
            "scripted_history_transitions": int(boundary["scripted_history_transitions"]),
        }
    return {
        "row_present": True,
        "scripted_history_transitions": int(boundary["scripted_history_transitions"]),
        "primitive_time": int(boundary["primitive_time"]),
        "environment_slot": int(boundary["environment_slot"]),
        "elapsed_horizon": int(boundary["elapsed_horizon"]),
        "previous_option": int(boundary["previous_option"]),
        "legal_printed_indices": [
            index for index, present in enumerate(boundary["legal_mask"]) if present
        ],
    }


def materialize_support_observation(
    tape: object,
    *,
    slot: int,
    ledger: object | None = None,
) -> dict[str, object]:
    """Materialize one always-present member of the exact fixed census target."""

    refuse_consumed_support_census()


def validate_support_full_replay(
    observations: Sequence[Mapping[str, object]], *, ledger: object,
) -> dict[str, object]:
    """Independently rebuild every tape and replay every exact G16 before publication."""

    refuse_consumed_support_census()


def _validate_int_pair(value: object, label: str) -> None:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(not _is_int(item) or item < 0 for item in value)
    ):
        raise SupportCensusError(f"{label} must be an exact integer pair")


def _validate_decision(value: object, expected_agent: int) -> Mapping[str, object]:
    decision = _require_keys(value, _DECISION_KEYS, "decision provenance")
    if decision["agent"] != expected_agent:
        raise SupportCensusError("decision provenance is not in environment-slot order")
    if decision["kind"] not in {"NONE", "INITIAL", "DISCRETIONARY", "FORCED_RENEWAL"}:
        raise SupportCensusError("decision kind is invalid")
    for field in ("selected_option", "age_before", "age_after_decision"):
        if not _is_int(decision[field]):
            raise SupportCensusError(f"decision {field} is not an integer")
    if not 0 <= decision["selected_option"] < 7:
        raise SupportCensusError("selected option is outside printed host options")
    previous = decision["previous_option"]
    if previous is not None and (not _is_int(previous) or not 0 <= previous < 7):
        raise SupportCensusError("previous option is invalid")
    if any(type(decision[field]) is not bool for field in ("changed", "switch_time", "reanchored")):
        raise SupportCensusError("decision boolean provenance is malformed")
    if not _finite(decision["charge"]) or decision["charge"] < 0:
        raise SupportCensusError("decision charge is invalid")
    return decision


def _validate_terminal(value: object, expected_time: int) -> Mapping[str, object]:
    terminal = _require_keys(value, _TERMINAL_KEYS, "terminal state")
    if terminal["primitive_time"] != expected_time or terminal["current_k"] != 8:
        raise SupportCensusError("terminal time or K drifted")
    for field in ("queues", "buffers"):
        _validate_int_pair(terminal[field], f"terminal {field}")
        if any(value > 64 for value in terminal[field]):
            raise SupportCensusError(f"terminal {field} exceeds fixed host capacity")
    for field, length in (("locations", 4), ("options", 4), ("option_ages", 4)):
        if not isinstance(terminal[field], list) or len(terminal[field]) != length or any(
            not _is_int(item) for item in terminal[field]
        ):
            raise SupportCensusError(f"terminal {field} is malformed")
    if not isinstance(terminal["energies"], list) or len(terminal["energies"]) != 4 or any(
        not _finite(item) or not 0.0 <= float(item) <= 32.0
        for item in terminal["energies"]
    ):
        raise SupportCensusError("terminal energies are malformed")
    if (
        any(not 0 <= int(item) <= 2 for item in terminal["locations"])
        or any(not 0 <= int(item) < 7 for item in terminal["options"])
        or any(int(item) < 0 for item in terminal["option_ages"])
    ):
        raise SupportCensusError("terminal location/option/age values are outside host bounds")
    if not _finite(terminal["terminal_potential"]):
        raise SupportCensusError("terminal potential is nonfinite")
    expected_potential = -0.02 * (
        sum(terminal["queues"]) + sum(terminal["buffers"])
    ) - 0.01 * sum(32.0 - float(energy) for energy in terminal["energies"])
    if abs(float(terminal["terminal_potential"]) - expected_potential) > 1e-12:
        raise SupportCensusError("terminal potential does not recompute from terminal state")
    return terminal


def _expected_exogenous_step(tape: object, primitive_time: int) -> tuple[bool, list[int], list[int]]:
    event = tape.spec.event.value
    active = event != "NONE" and tape.spec.event_onset <= primitive_time < (
        tape.spec.event_onset + 32
    )
    hot = int(tape.initial_hot_lane)
    if active and event in {"UNANNOUNCED-DIFFERENTIAL", "CUED-DIFFERENTIAL"}:
        hot = 1 - hot
    cold = 1 - hot
    arrivals = [0, 0]
    arrivals[hot] = 1 + int(tape.arrival_hot_coin[primitive_time])
    arrivals[cold] = int(tape.arrival_cold_coin[primitive_time])
    capacity = [
        1 + int(tape.relay_capacity_coin[primitive_time, lane]) for lane in range(2)
    ]
    return active, arrivals, capacity


def _validate_branch(
    value: object,
    *,
    boundary_time: int,
    target_agent: int,
    previous_option: int,
    printed_index: int,
    replanning_cost: float,
    elapsed_horizon: int,
    event_class: str,
) -> tuple[float, tuple[object, ...]]:
    branch = _require_keys(value, _BRANCH_KEYS, "branch provenance")
    expected_option = previous_option if printed_index == 0 else printed_index - 1
    expected_action = ACTION_ORDER[printed_index]
    expected_charge = 0.0 if printed_index == 0 else 0.05 + replanning_cost
    if (
        branch["printed_index"] != printed_index
        or branch["action"] != expected_action
        or branch["selected_option"] != expected_option
        or branch["intervention_charge_step"] != 0
        or not _finite(branch["intervention_charge"])
        or abs(branch["intervention_charge"] - expected_charge) > 1e-12
    ):
        raise SupportCensusError("printed branch action or charge-once binding drifted")
    steps = branch["steps"]
    if not isinstance(steps, list) or len(steps) != AUDIT_HORIZON:
        raise SupportCensusError("every common-future branch must contain exactly 16 steps")
    rewards: list[float] = []
    previous_queues: list[int] | None = None
    previous_buffers: list[int] | None = None
    first_other_decisions: tuple[object, ...] | None = None
    previous_selected: list[int] | None = None
    previous_age_after: list[int] | None = None
    common_exogenous: list[tuple[object, ...]] = []
    for offset, raw_step in enumerate(steps):
        step = _require_keys(raw_step, _STEP_KEYS, "branch step")
        if step["primitive_time"] != boundary_time + offset or step["k"] != 8:
            raise SupportCensusError("branch step time or K drifted")
        if type(step["event_active"]) is not bool:
            raise SupportCensusError("branch event activity is not boolean")
        for field in (
            "physical_queues_before", "deployable_queues_before", "buffers_before",
            "arrivals", "relay_capacity", "tracked", "delivered",
            "physical_queues_after", "buffers_after",
        ):
            _validate_int_pair(step[field], f"step {field}")
        if (
            any(value > 64 for field in (
                "physical_queues_before", "deployable_queues_before", "buffers_before",
                "physical_queues_after", "buffers_after",
            ) for value in step[field])
            or any(value not in (1, 2) for value in step["relay_capacity"])
            or any(value > 2 for value in step["arrivals"])
            or not 1 <= sum(step["arrivals"]) <= 3
            or sum(step["tracked"]) + sum(step["delivered"]) > 4
        ):
            raise SupportCensusError("step physical state is outside fixed host bounds")
        if not _is_int(step["overflow"]) or step["overflow"] < 0:
            raise SupportCensusError("step overflow is invalid")
        for field in ("energy_spent", "decision_charge", "reward"):
            if not _finite(step[field]):
                raise SupportCensusError(f"step {field} is nonfinite")
        if float(step["energy_spent"]) < 0:
            raise SupportCensusError("step energy spent is negative")
        common_exogenous.append((
            step["event_active"], tuple(step["arrivals"]), tuple(step["relay_capacity"]),
        ))
        deployable_offset = 4 if (
            event_class == "COMMON-SENSOR" and step["event_active"] is True
        ) else 0
        expected_deployable = [
            min(64, int(value) + deployable_offset)
            for value in step["physical_queues_before"]
        ]
        if step["deployable_queues_before"] != expected_deployable:
            raise SupportCensusError("deployable queue does not recompute from physical state")
        if any(
            int(step["tracked"][lane]) > int(step["physical_queues_before"][lane])
            or int(step["delivered"][lane]) > int(step["buffers_before"][lane])
            or int(step["delivered"][lane]) > int(step["relay_capacity"][lane])
            for lane in range(2)
        ):
            raise SupportCensusError("tracked or delivered work exceeds available state/capacity")
        raw_queues = [
            int(step["physical_queues_before"][lane])
            - int(step["tracked"][lane]) + int(step["arrivals"][lane])
            for lane in range(2)
        ]
        raw_buffers = [
            int(step["buffers_before"][lane])
            - int(step["delivered"][lane]) + int(step["tracked"][lane])
            for lane in range(2)
        ]
        expected_overflow = sum(max(value - 64, 0) for value in raw_queues + raw_buffers)
        if (
            step["physical_queues_after"] != [min(value, 64) for value in raw_queues]
            or step["buffers_after"] != [min(value, 64) for value in raw_buffers]
            or step["overflow"] != expected_overflow
        ):
            raise SupportCensusError("queue/buffer/overflow transition arithmetic drifted")
        if previous_queues is not None and step["physical_queues_before"] != previous_queues:
            raise SupportCensusError("branch queue provenance is not step-contiguous")
        if previous_buffers is not None and step["buffers_before"] != previous_buffers:
            raise SupportCensusError("branch buffer provenance is not step-contiguous")
        previous_queues = step["physical_queues_after"]
        previous_buffers = step["buffers_after"]
        decisions = step["decisions"]
        if not isinstance(decisions, list) or len(decisions) != 4:
            raise SupportCensusError("step must contain four decisions")
        typed = [_validate_decision(item, agent) for agent, item in enumerate(decisions)]
        selected = [int(item["selected_option"]) for item in typed]
        ages_after = [int(item["age_after_decision"]) for item in typed]
        for agent, decision in enumerate(typed):
            previous = decision["previous_option"]
            if previous is None or decision["kind"] == "INITIAL":
                raise SupportCensusError("common-future decision is outside initialized K8 law")
            changed = int(decision["selected_option"]) != int(previous)
            if decision["changed"] is not changed or decision["switch_time"] is not False:
                raise SupportCensusError("decision change/switch provenance is inconsistent")
            if previous_selected is not None and (
                previous != previous_selected[agent]
                or decision["age_before"] != previous_age_after[agent] + 1
            ):
                raise SupportCensusError("decision option/age provenance is not step-contiguous")
            if decision["kind"] == "NONE":
                expected_decision_charge = 0.0
                expected_age_after = int(decision["age_before"])
                expected_reanchored = False
                if changed:
                    raise SupportCensusError("NONE decision changed its option")
            elif decision["kind"] == "DISCRETIONARY":
                expected_decision_charge = 0.0 if not changed else 0.05 + replanning_cost
                expected_age_after = 0 if changed else int(decision["age_before"])
                expected_reanchored = changed
            else:
                expected_decision_charge = 0.05 + (replanning_cost if changed else 0.0)
                expected_age_after = 0
                expected_reanchored = True
            if (
                abs(float(decision["charge"]) - expected_decision_charge) > 1e-12
                or decision["age_after_decision"] != expected_age_after
                or decision["reanchored"] is not expected_reanchored
            ):
                raise SupportCensusError("decision charge/age/reanchor law drifted")
        previous_selected = selected
        previous_age_after = ages_after
        if abs(sum(float(item["charge"]) for item in typed) - float(step["decision_charge"])) > 1e-12:
            raise SupportCensusError("step decision charge disagrees with decision provenance")
        expected_reward = (
            sum(step["delivered"])
            - 0.02 * (sum(step["physical_queues_after"]) + sum(step["buffers_after"]))
            - 2.0 * int(step["overflow"])
            - 0.01 * float(step["energy_spent"])
            - float(step["decision_charge"])
        )
        if abs(float(step["reward"]) - expected_reward) > 1e-12:
            raise SupportCensusError("step reward does not recompute from physical provenance")
        if offset == 0:
            target = typed[target_agent]
            if (
                target["kind"] != "DISCRETIONARY"
                or target["previous_option"] != previous_option
                or target["selected_option"] != expected_option
                or abs(float(target["charge"]) - expected_charge) > 1e-12
                or target["age_before"] != elapsed_horizon
                or target["changed"] != (printed_index != 0)
                or target["age_after_decision"] != (
                    elapsed_horizon if printed_index == 0 else 0
                )
                or target["reanchored"] != (printed_index != 0)
                or target["switch_time"] is not False
            ):
                raise SupportCensusError("boundary target action/charge was not applied exactly once")
            first_other_decisions = tuple(
                tuple(sorted(item.items())) for agent, item in enumerate(typed)
                if agent != target_agent
            )
        rewards.append(float(step["reward"]))
    terminal = _validate_terminal(branch["terminal_state"], boundary_time + AUDIT_HORIZON)
    assert previous_queues is not None and previous_buffers is not None
    assert first_other_decisions is not None
    if terminal["queues"] != previous_queues or terminal["buffers"] != previous_buffers:
        raise SupportCensusError("terminal queue/buffer state differs from the last branch step")
    assert previous_selected is not None and previous_age_after is not None
    if (
        terminal["options"] != previous_selected
        or terminal["option_ages"] != [value + 1 for value in previous_age_after]
    ):
        raise SupportCensusError("terminal option/age state differs from the last decision step")
    denominator_g16 = branch["g16"]
    if not _finite(denominator_g16):
        raise SupportCensusError("branch G16 is nonfinite")
    return_value = sum((0.99 ** offset) * reward for offset, reward in enumerate(rewards))
    return (
        return_value + (0.99 ** AUDIT_HORIZON) * float(terminal["terminal_potential"]),
        (
            tuple(steps[0]["physical_queues_before"]),
            tuple(steps[0]["deployable_queues_before"]),
            tuple(steps[0]["buffers_before"]),
            first_other_decisions,
            tuple(common_exogenous),
        ),
    )


def _validate_boundary(
    value: object,
    *,
    replanning_cost: float,
    event_class: str,
) -> tuple[str | None, float | None, int, int | None]:
    if not isinstance(value, Mapping):
        raise SupportCensusError("boundary observation must be an object")
    if value.get("row_present") is False:
        boundary = _require_keys(value, _BOUNDARY_ABSENT_KEYS, "absent boundary")
        if boundary["scripted_history_transitions"] != 256:
            raise SupportCensusError("absent boundary must record the complete 256-step scan")
        return None, None, 0, None
    boundary = _require_keys(value, _BOUNDARY_KEYS, "retained boundary")
    if boundary["row_present"] is not True:
        raise SupportCensusError("row_present must be an exact boolean")
    primitive_time = boundary["primitive_time"]
    target_agent = boundary["environment_slot"]
    elapsed = boundary["elapsed_horizon"]
    previous = boundary["previous_option"]
    if (
        not _is_int(primitive_time)
        or not 0 <= primitive_time <= 256 - AUDIT_HORIZON
        or boundary["scripted_history_transitions"] != primitive_time
        or not _is_int(target_agent)
        or not 0 <= target_agent < 4
        or elapsed not in (4, 8, 12, 16)
        or not _is_int(previous)
        or not 0 <= previous < 7
    ):
        raise SupportCensusError("retained boundary coordinates are malformed")
    legal = boundary["legal_mask"]
    g16 = boundary["g16"]
    if (
        not isinstance(legal, list) or len(legal) != 8
        or any(type(item) is not bool for item in legal)
        or legal[0] is not True
        or sum(legal[1:]) < 1
        or not isinstance(g16, list) or len(g16) != 8
    ):
        raise SupportCensusError("legal printed action inventory is malformed")
    for index in range(8):
        if legal[index] and not _finite(g16[index]):
            raise SupportCensusError("legal G16 must be finite")
        if not legal[index] and g16[index] is not None:
            raise SupportCensusError("illegal G16 must be null")
    denominator = boundary["denominator"]
    if not _is_int(denominator) or denominator < 1:
        raise SupportCensusError("G16 denominator must be a positive integer")
    indices = [index for index, present in enumerate(legal) if present]
    branches = boundary["branches"]
    if not isinstance(branches, list) or len(branches) != len(indices):
        raise SupportCensusError("branch inventory disagrees with the legal mask")
    common_first_state: tuple[object, ...] | None = None
    for branch, index in zip(branches, indices):
        numerator, first_state = _validate_branch(
            branch,
            boundary_time=primitive_time,
            target_agent=target_agent,
            previous_option=previous,
            printed_index=index,
            replanning_cost=replanning_cost,
            elapsed_horizon=int(elapsed),
            event_class=event_class,
        )
        if common_first_state is None:
            common_first_state = first_state
        elif first_state != common_first_state:
            raise SupportCensusError(
                "branches do not share one predecision state and aligned simultaneous actions"
            )
        derived = numerator / denominator
        if abs(derived - float(g16[index])) > 1e-12 or abs(
            derived - float(branch["g16"])
        ) > 1e-12:
            raise SupportCensusError("G16 does not replay from its 16-step provenance")
    replacements = indices[1:]
    maximizing = max(replacements, key=lambda index: (float(g16[index]), -index))
    keep = float(g16[0])
    maximum = float(g16[maximizing])
    advantage = maximum - keep
    material_class = _classify(advantage)
    if (
        not _finite(boundary["keep_g16"])
        or abs(float(boundary["keep_g16"]) - keep) > 1e-12
        or not _finite(boundary["max_replacement_g16"])
        or abs(float(boundary["max_replacement_g16"]) - maximum) > 1e-12
        or boundary["maximizing_replacement"] != maximizing
        or not _finite(boundary["advantage"])
        or abs(float(boundary["advantage"]) - advantage) > 1e-12
        or boundary["material_class"] != material_class
    ):
        raise SupportCensusError("recorded advantage/classification is not exactly derived")
    return material_class, advantage, len(indices), int(elapsed)


def _validate_observation(
    value: object,
    *,
    expected_slot: int,
    expected_episode: int,
) -> tuple[str | None, float | None, int, int | None, float]:
    keys = frozenset({
        "format", "object_id", "rng_namespace", "slot", "split", "regime",
        "episode_index", "population_ordinal", "spec", "boundary_scan", "boundary",
    })
    observation = _require_keys(value, keys, "support observation")
    spec = _require_keys(observation["spec"], _SPEC_KEYS, "support scenario spec")
    if (
        spec["episode_index"] != expected_episode
        or not _is_int(spec["episode_seed"])
        or spec["episode_seed"] < 0
        or spec["regime"] != "K8"
        or spec["event"] not in {
            "NONE", "UNANNOUNCED-DIFFERENTIAL", "CUED-DIFFERENTIAL", "COMMON-SENSOR",
        }
        or spec["event_onset"] not in (50, 66, 82, 98, 146, 162, 178, 194)
        or spec["replanning_cost"] not in (0.25, 4.0)
    ):
        raise SupportCensusError("support scenario spec is outside the fixed K8 crossed cells")
    if (
        observation["format"] != OBSERVATION_FORMAT
        or observation["object_id"] != SUPPORT_CENSUS_OBJECT_ID
        or observation["rng_namespace"] != SUPPORT_CENSUS_RNG_NAMESPACE
        or observation["slot"] != expected_slot
        or observation["split"] != Split.EVALUATION.value
        or observation["regime"] != "K8"
        or observation["episode_index"] != expected_episode
        or observation["population_ordinal"] != (
            expected_slot * SUPPORT_CENSUS_EPISODES_PER_SLOT
            + expected_episode - SUPPORT_CENSUS_FIRST_EPISODE
        )
    ):
        raise SupportCensusError("observation registration coordinates drifted")
    boundary = observation["boundary"]
    if observation["boundary_scan"] != _boundary_scan_record(boundary):
        raise SupportCensusError("boundary scan record disagrees with the retained provenance")
    material, advantage, branches, elapsed = _validate_boundary(
        boundary,
        replanning_cost=float(spec["replanning_cost"]),
        event_class=str(spec["event"]),
    )
    return material, advantage, branches, elapsed, float(spec["replanning_cost"])


def _cell_key(elapsed: int, cost: float) -> str:
    return f"h{elapsed}/cost{cost:.2f}"


def _validate_crossed_spec_population(observations: Sequence[Mapping[str, object]]) -> None:
    expected_cells = {
        (event, cost, onset)
        for event in (
            "NONE", "UNANNOUNCED-DIFFERENTIAL", "CUED-DIFFERENTIAL", "COMMON-SENSOR",
        )
        for cost in (0.25, 4.0)
        for onset in (50, 66, 82, 98, 146, 162, 178, 194)
    }
    for slot in SUPPORT_CENSUS_SLOTS:
        begin = slot * SUPPORT_CENSUS_EPISODES_PER_SLOT
        rows = observations[begin:begin + SUPPORT_CENSUS_EPISODES_PER_SLOT]
        cells = {
            (
                row["spec"]["event"], row["spec"]["replanning_cost"],
                row["spec"]["event_onset"],
            )
            for row in rows
        }
        seed_offsets = {
            int(row["spec"]["episode_seed"]) - int(row["spec"]["episode_index"])
            for row in rows
        }
        if cells != expected_cells or len(seed_offsets) != 1:
            raise SupportCensusError(
                f"slot {slot} does not contain one complete fixed K8 crossed manifest"
            )


def _empty_cell_counts() -> dict[str, int]:
    return {
        _cell_key(elapsed, cost): 0
        for elapsed in (4, 8, 12, 16)
        for cost in (0.25, 4.0)
    }


def _validate_runtime(
    value: object,
    *,
    transitions: int,
    branches: int,
) -> dict[str, object]:
    runtime = dict(_require_keys(value, _RUNTIME_KEYS, "support runtime"))
    base_episodes = len(SUPPORT_CENSUS_SLOTS) * SUPPORT_CENSUS_EPISODES_PER_SLOT
    base_steps = base_episodes * 256
    common_steps = branches * AUDIT_HORIZON
    actual_total = 2 * base_steps + 2 * common_steps
    exact = {
        "workers": 1,
        "threads_per_worker": 1,
        "base_episode_count": 2 * base_episodes,
        "charged_base_primitive_team_steps": 2 * base_steps,
        "scripted_history_transitions": 2 * transitions,
        "actual_common_future_branch_count": 2 * branches,
        "actual_common_future_steps": 2 * common_steps,
        "materialization_base_episode_count": base_episodes,
        "materialization_charged_base_primitive_team_steps": base_steps,
        "materialization_scripted_history_transitions": transitions,
        "materialization_common_future_branch_count": branches,
        "materialization_common_future_steps": common_steps,
        "validation_base_episode_count": base_episodes,
        "validation_charged_base_primitive_team_steps": base_steps,
        "validation_scripted_history_transitions": transitions,
        "validation_common_future_branch_count": branches,
        "validation_common_future_steps": common_steps,
        "actual_total_charged_primitive_team_steps": actual_total,
        "primitive_team_step_ceiling": SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS,
        "wall_ceiling_seconds": WALL_SECONDS,
        "peak_rss_ceiling_bytes": PEAK_RSS_BYTES,
        "measurement_cutoff": RUNTIME_MEASUREMENT_CUTOFF,
        "commit_tail_excluded": True,
        "commit_headroom": COMMIT_HEADROOM,
    }
    if any(runtime.get(field) != expected for field, expected in exact.items()):
        raise SupportCensusError("runtime work/resource registration drifted")
    for field in (
        "wall_seconds", "cpu_seconds", "cpu_occupancy_fraction",
    ):
        if not _finite(runtime[field]) or runtime[field] < 0:
            raise SupportCensusError(f"runtime {field} is invalid")
    for field in (
        "peak_rss_bytes", "scratch_high_water_bytes", "durable_high_water_bytes",
        "io_read_bytes", "io_write_bytes",
    ):
        if not _is_int(runtime[field]) or runtime[field] < 0:
            raise SupportCensusError(f"runtime {field} is invalid")
    observed = _require_keys(
        runtime["final_candidate_staging_rehearsal_observed"],
        frozenset({
            "wall_seconds", "cpu_seconds", "peak_rss_bytes",
            "io_read_bytes", "io_write_bytes",
        }),
        "full staging rehearsal observation",
    )
    for field in ("wall_seconds", "cpu_seconds"):
        if not _finite(observed[field]) or observed[field] < 0:
            raise SupportCensusError(f"rehearsal {field} is invalid")
    for field in ("peak_rss_bytes", "io_read_bytes", "io_write_bytes"):
        if not _is_int(observed[field]) or observed[field] < 0:
            raise SupportCensusError(f"rehearsal {field} is invalid")
    if any(
        observed[field] > runtime[field]
        for field in (
            "wall_seconds", "cpu_seconds", "peak_rss_bytes",
            "io_read_bytes", "io_write_bytes",
        )
    ):
        raise SupportCensusError("precommit runtime bound understates its full staging rehearsal")
    if (
        runtime["wall_seconds"] > (
            WALL_SECONDS - SUPPORT_CENSUS_COMMIT_WALL_HEADROOM_SECONDS
        )
        or runtime["cpu_seconds"] > (
            WALL_SECONDS - SUPPORT_CENSUS_COMMIT_CPU_HEADROOM_SECONDS
        )
        or runtime["peak_rss_bytes"] > (
            PEAK_RSS_BYTES - SUPPORT_CENSUS_COMMIT_RSS_HEADROOM_BYTES
        )
        or runtime["cpu_occupancy_fraction"] > 1.0
        or actual_total > SUPPORT_CENSUS_MAX_PRIMITIVE_TEAM_STEPS
    ):
        raise SupportCensusError("support census exceeded its frozen resource envelope")
    return runtime


def _validate_support_run_receipt(value: object) -> None:
    if not isinstance(value, Mapping):
        raise SupportCensusError("support run assessment must be an object")
    if _validate_run_resource_receipt(value):
        raise SupportCensusError("fresh same-envelope run assessment is invalid")
    estimate = value.get("estimate")
    if (
        value.get("direction_id") != "commitment_residual_triggered_options"
        or value.get("run_id") != SUPPORT_CENSUS_LAUNCH_RUN_ID
        or not isinstance(estimate, Mapping)
        or estimate.get("basis") != "CRTO prospective frozen one-worker CPU envelope"
    ):
        raise SupportCensusError("run assessment is not bound to the support census launch")


def _disposition(slot_summaries: Sequence[Mapping[str, object]]) -> str:
    global_keep = sum(int(summary["counts"]["KEEP"]) for summary in slot_summaries)
    if global_keep == 0:
        return DISPOSITION_NO_KEEP
    if any(
        int(summary["counts"]["KEEP"]) < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM
        for summary in slot_summaries
    ):
        return DISPOSITION_KEEP_MINIMUM_FAIL
    if any(
        int(summary["counts"]["REPLAN"]) < MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM
        for summary in slot_summaries
    ):
        return DISPOSITION_REPLAN_MINIMUM_FAIL
    return DISPOSITION_FEASIBLE


def _validate_independent_replay(value: object) -> dict[str, object]:
    record = dict(_require_keys(
        value, _INDEPENDENT_REPLAY_KEYS, "independent support replay",
    ))
    expected_count = len(SUPPORT_CENSUS_SLOTS) * SUPPORT_CENSUS_EPISODES_PER_SLOT
    per_tape_bytes = sum(
        int(item["raw_byte_length"]) for item in TAPE_ARRAY_INVENTORY
    )
    expected = {
        "mode": INDEPENDENT_REPLAY_MODE,
        "rebuilt_tapes": expected_count,
        "scenario_spec_direct_matches": expected_count,
        "array_raw_byte_direct_matches": expected_count * len(TAPE_ARRAY_INVENTORY),
        "raw_bytes_compared_per_side": expected_count * per_tape_bytes,
        "complete_boundary_provenance_direct_matches": expected_count,
        "tape_array_inventory": [dict(item) for item in TAPE_ARRAY_INVENTORY],
    }
    if record != expected:
        raise SupportCensusError("independent full replay record is incomplete or altered")
    return record


def summarize_support_census(
    observations: Sequence[Mapping[str, object]],
    *,
    independent_replay: Mapping[str, object],
    resource_receipt: Mapping[str, object],
    run_resource_receipt: Mapping[str, object],
    runtime: Mapping[str, object],
) -> dict[str, object]:
    """Strictly summarize the complete canonical 8x64 population."""

    refuse_consumed_support_census()
    if _validate_resource_receipt(resource_receipt):
        raise SupportCensusError("fresh 4-GiB resource receipt is invalid")
    _validate_support_run_receipt(run_resource_receipt)
    replay_record = _validate_independent_replay(independent_replay)
    expected_count = len(SUPPORT_CENSUS_SLOTS) * SUPPORT_CENSUS_EPISODES_PER_SLOT
    if not isinstance(observations, Sequence) or len(observations) != expected_count:
        raise SupportCensusError("support census requires exactly 512 ordered observations")
    _validate_crossed_spec_population(observations)
    slot_data: dict[int, dict[str, object]] = {}
    global_counts = Counter({"KEEP": 0, "MIDDLE": 0, "REPLAN": 0})
    global_advantages: list[float] = []
    keep_witnesses: list[dict[str, object]] = []
    total_branches = 0
    transitions = 0
    for ordinal, observation in enumerate(observations):
        slot, offset = divmod(ordinal, SUPPORT_CENSUS_EPISODES_PER_SLOT)
        episode = SUPPORT_CENSUS_FIRST_EPISODE + offset
        material, advantage, branches, elapsed, cost = _validate_observation(
            observation, expected_slot=slot, expected_episode=episode,
        )
        state = slot_data.setdefault(slot, {
            "counts": Counter({"KEEP": 0, "MIDDLE": 0, "REPLAN": 0}),
            "advantages": [], "retained": 0, "branches": 0,
            "cell_counts": _empty_cell_counts(),
        })
        boundary = observation["boundary"]
        transitions += int(boundary["scripted_history_transitions"])
        state["branches"] += branches
        total_branches += branches
        if material is None:
            continue
        state["retained"] += 1
        state["counts"][material] += 1
        global_counts[material] += 1
        assert advantage is not None and elapsed is not None
        state["advantages"].append(advantage)
        global_advantages.append(advantage)
        state["cell_counts"][_cell_key(elapsed, cost)] += 1
        if material == "KEEP":
            keep_witnesses.append(deepcopy(dict(observation)))
    summaries: list[dict[str, object]] = []
    for slot in SUPPORT_CENSUS_SLOTS:
        state = slot_data[slot]
        retained = int(state["retained"])
        if retained < 48:
            raise SupportCensusError(
                f"slot {slot} retained {retained}/64 boundaries; support census is incomplete"
            )
        advantages = state["advantages"]
        summaries.append({
            "slot": slot,
            "assigned_tapes": SUPPORT_CENSUS_EPISODES_PER_SLOT,
            "retained_boundaries": retained,
            "absent_boundaries": SUPPORT_CENSUS_EPISODES_PER_SLOT - retained,
            "counts": dict(state["counts"]),
            "advantage_extrema": {
                "minimum": min(advantages),
                "maximum": max(advantages),
            },
            "elapsed_horizon_cost_cell_counts": dict(state["cell_counts"]),
            "common_future_branches": int(state["branches"]),
        })
    runtime_record = _validate_runtime(runtime, transitions=transitions, branches=total_branches)
    activity = {
        "support_tapes_materialized": 2 * expected_count,
        "support_boundaries_materialized": 2 * sum(
            int(summary["retained_boundaries"]) for summary in summaries
        ),
        "materialization_support_tapes": expected_count,
        "validation_support_tapes": expected_count,
        "materialization_support_boundaries": sum(
            int(summary["retained_boundaries"]) for summary in summaries
        ),
        "validation_support_boundaries": sum(
            int(summary["retained_boundaries"]) for summary in summaries
        ),
        "common_future_rollouts": 2 * total_branches,
        "materialization_common_future_rollouts": total_branches,
        "validation_common_future_rollouts": total_branches,
        "learner_models_constructed": 0,
        "predictor_models_constructed": 0,
        "gate_models_constructed": 0,
        "optimizer_updates": 0,
        "checkpoints": 0,
        "true_residual_activity": 0,
        "deranged_activity": 0,
        "final_namespace_reads": 0,
        "pilot_namespace_reads": 0,
    }
    payload = {
        "format": FORMAT,
        "object_id": SUPPORT_CENSUS_OBJECT_ID,
        "rng_namespace": SUPPORT_CENSUS_RNG_NAMESPACE,
        "claim_ceiling": SUPPORT_CENSUS_CLAIM_CEILING,
        "slots": list(SUPPORT_CENSUS_SLOTS),
        "split": Split.EVALUATION.value,
        "regime": "K8",
        "first_episode_index": SUPPORT_CENSUS_FIRST_EPISODE,
        "episodes_per_slot": SUPPORT_CENSUS_EPISODES_PER_SLOT,
        "population_order": "SLOT_THEN_EPISODE_INDEX",
        "selection_law": SELECTION_LAW,
        "material_advantage_threshold": MATERIAL_ADVANTAGE_THRESHOLD,
        "minimum_rows_per_material_stratum": MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM,
        "slot_summaries": summaries,
        "global_counts": dict(global_counts),
        "global_advantage_extrema": {
            "minimum": min(global_advantages),
            "maximum": max(global_advantages),
        },
        "keep_witnesses": keep_witnesses,
        "observations": deepcopy([dict(item) for item in observations]),
        "independent_replay": replay_record,
        "disposition": _disposition(summaries),
        "resource_receipt": deepcopy(dict(resource_receipt)),
        "run_resource_receipt": deepcopy(dict(run_resource_receipt)),
        "runtime": runtime_record,
        "performance": {
            "disposition": SUPPORT_CENSUS_PERFORMANCE_DISPOSITION,
            "bounded_support_census_only": True,
            "raw_pilot_object": False,
            "reason": PERFORMANCE_REASON,
        },
        "activity": activity,
    }
    validate_support_census(payload)
    return payload


def validate_support_census(payload: Mapping[str, object]) -> dict[str, object]:
    """Recompute every registration, G16, count, witness, and disposition."""

    keys = frozenset({
        "format", "object_id", "rng_namespace", "claim_ceiling", "slots", "split",
        "regime", "first_episode_index", "episodes_per_slot", "population_order",
        "selection_law", "material_advantage_threshold",
        "minimum_rows_per_material_stratum", "slot_summaries", "global_counts",
        "global_advantage_extrema", "keep_witnesses", "observations", "disposition",
        "independent_replay", "resource_receipt", "run_resource_receipt", "runtime",
        "performance", "activity",
    })
    value = dict(_require_keys(payload, keys, "support census receipt"))
    expected_constants = {
        "format": FORMAT,
        "object_id": SUPPORT_CENSUS_OBJECT_ID,
        "rng_namespace": SUPPORT_CENSUS_RNG_NAMESPACE,
        "claim_ceiling": SUPPORT_CENSUS_CLAIM_CEILING,
        "slots": list(SUPPORT_CENSUS_SLOTS),
        "split": Split.EVALUATION.value,
        "regime": "K8",
        "first_episode_index": SUPPORT_CENSUS_FIRST_EPISODE,
        "episodes_per_slot": SUPPORT_CENSUS_EPISODES_PER_SLOT,
        "population_order": "SLOT_THEN_EPISODE_INDEX",
        "selection_law": SELECTION_LAW,
        "material_advantage_threshold": MATERIAL_ADVANTAGE_THRESHOLD,
        "minimum_rows_per_material_stratum": MINIMUM_K8_ROWS_PER_MATERIAL_STRATUM,
    }
    if any(value.get(field) != expected for field, expected in expected_constants.items()):
        raise SupportCensusError("support census registration constants drifted")
    if _validate_resource_receipt(value["resource_receipt"]):
        raise SupportCensusError("embedded resource receipt is invalid")
    _validate_support_run_receipt(value["run_resource_receipt"])
    value["independent_replay"] = _validate_independent_replay(
        value["independent_replay"]
    )
    if value["performance"] != {
        "disposition": SUPPORT_CENSUS_PERFORMANCE_DISPOSITION,
        "bounded_support_census_only": True,
        "raw_pilot_object": False,
        "reason": PERFORMANCE_REASON,
    }:
        raise SupportCensusError("support census performance disposition drifted")
    observations = value["observations"]
    if not isinstance(observations, list) or len(observations) != 512:
        raise SupportCensusError("receipt does not contain the complete 512-row population")
    _validate_crossed_spec_population(observations)
    derived_summaries: list[dict[str, object]] = []
    derived_witnesses: list[dict[str, object]] = []
    global_counts = Counter({"KEEP": 0, "MIDDLE": 0, "REPLAN": 0})
    all_advantages: list[float] = []
    transitions = 0
    total_branches = 0
    for slot in SUPPORT_CENSUS_SLOTS:
        counts = Counter({"KEEP": 0, "MIDDLE": 0, "REPLAN": 0})
        advantages: list[float] = []
        cells = _empty_cell_counts()
        retained = 0
        slot_branches = 0
        for offset in range(SUPPORT_CENSUS_EPISODES_PER_SLOT):
            ordinal = slot * SUPPORT_CENSUS_EPISODES_PER_SLOT + offset
            observation = observations[ordinal]
            material, advantage, branches, elapsed, cost = _validate_observation(
                observation,
                expected_slot=slot,
                expected_episode=SUPPORT_CENSUS_FIRST_EPISODE + offset,
            )
            transitions += int(observation["boundary"]["scripted_history_transitions"])
            slot_branches += branches
            total_branches += branches
            if material is None:
                continue
            retained += 1
            counts[material] += 1
            global_counts[material] += 1
            assert advantage is not None and elapsed is not None
            advantages.append(advantage)
            all_advantages.append(advantage)
            cells[_cell_key(elapsed, cost)] += 1
            if material == "KEEP":
                derived_witnesses.append(deepcopy(dict(observation)))
        if retained < 48:
            raise SupportCensusError(f"slot {slot} fails the frozen 48/64 availability floor")
        derived_summaries.append({
            "slot": slot,
            "assigned_tapes": SUPPORT_CENSUS_EPISODES_PER_SLOT,
            "retained_boundaries": retained,
            "absent_boundaries": SUPPORT_CENSUS_EPISODES_PER_SLOT - retained,
            "counts": dict(counts),
            "advantage_extrema": {"minimum": min(advantages), "maximum": max(advantages)},
            "elapsed_horizon_cost_cell_counts": cells,
            "common_future_branches": slot_branches,
        })
    expected_extrema = {"minimum": min(all_advantages), "maximum": max(all_advantages)}
    if value["slot_summaries"] != derived_summaries:
        raise SupportCensusError("slot summaries do not recompute from full observations")
    if value["global_counts"] != dict(global_counts):
        raise SupportCensusError("global material counts do not recompute")
    if value["global_advantage_extrema"] != expected_extrema:
        raise SupportCensusError("global A extrema do not recompute")
    if value["keep_witnesses"] != derived_witnesses:
        raise SupportCensusError("KEEP witness certificates are missing, extra, or altered")
    if (
        value["disposition"] != _disposition(derived_summaries)
        or value["disposition"] != SUPPORT_CENSUS_TERMINAL_DISPOSITION
    ):
        raise SupportCensusError("scientific disposition violates the frozen priority order")
    runtime = _validate_runtime(value["runtime"], transitions=transitions, branches=total_branches)
    expected_activity = {
        "support_tapes_materialized": 1024,
        "support_boundaries_materialized": 2 * sum(
            int(summary["retained_boundaries"]) for summary in derived_summaries
        ),
        "materialization_support_tapes": 512,
        "validation_support_tapes": 512,
        "materialization_support_boundaries": sum(
            int(summary["retained_boundaries"]) for summary in derived_summaries
        ),
        "validation_support_boundaries": sum(
            int(summary["retained_boundaries"]) for summary in derived_summaries
        ),
        "common_future_rollouts": 2 * total_branches,
        "materialization_common_future_rollouts": total_branches,
        "validation_common_future_rollouts": total_branches,
        "learner_models_constructed": 0,
        "predictor_models_constructed": 0,
        "gate_models_constructed": 0,
        "optimizer_updates": 0,
        "checkpoints": 0,
        "true_residual_activity": 0,
        "deranged_activity": 0,
        "final_namespace_reads": 0,
        "pilot_namespace_reads": 0,
    }
    activity = _require_keys(value["activity"], _ACTIVITY_KEYS, "support activity")
    if dict(activity) != expected_activity:
        raise SupportCensusError("support-only activity counters drifted")
    value["runtime"] = runtime
    return value


def _encoded(payload: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SupportCensusError("support receipt is not finite JSON") from error


def prepare_support_census_publication(
    output_root: Path,
    result_path: Path,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Validate, encode, write, and fsync both targets without making either visible."""

    refuse_consumed_support_census()
    validated = validate_support_census(payload)
    encoded = _encoded(validated)
    output = Path(output_root).resolve()
    result = Path(result_path).resolve()
    if output.exists() or result.exists():
        raise FileExistsError("support census publication requires two fresh targets")
    if output == result or output in result.parents:
        raise SupportCensusError("external result must be outside the direction output root")
    output.parent.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name + ".stage.", dir=output.parent))
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=result.name + ".", suffix=".tmp", dir=result.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        receipt = stage / RECEIPT_NAME
        with receipt.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        with temporary.open("wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        marker = {
            "format": "CRTO_SUPPORT_CENSUS_DUAL_PUBLICATION_V1",
            "object_id": SUPPORT_CENSUS_OBJECT_ID,
            "complete": True,
            "commit_law": "EXTERNAL_RESULT_FIRST_DIRECTION_ROOT_SECOND",
            "receipt": RECEIPT_NAME,
        }
        with (stage / PUBLICATION_MARKER_NAME).open("x", encoding="utf-8") as stream:
            json.dump(marker, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if receipt.read_bytes() != temporary.read_bytes():
            raise SupportCensusError("staged direction and external receipts differ")
        if output.exists() or result.exists():
            raise FileExistsError("support census target appeared during create-only publication")
        return {
            "output": output,
            "result": result,
            "stage": stage,
            "temporary": temporary,
            "payload": validated,
            "staged_bytes": (
                receipt.stat().st_size
                + temporary.stat().st_size
                + (stage / PUBLICATION_MARKER_NAME).stat().st_size
            ),
        }
    except BaseException:
        if stage.exists():
            if stage.parent != output.parent or not stage.name.startswith(output.name + ".stage."):
                raise RuntimeError("refusing to clean an unexpected support staging path")
            shutil.rmtree(stage)
        if temporary.exists():
            temporary.unlink()
        raise


def discard_prepared_support_publication(prepared: Mapping[str, object]) -> None:
    refuse_consumed_support_census()
    stage = Path(prepared["stage"])
    temporary = Path(prepared["temporary"])
    output = Path(prepared["output"])
    if stage.exists():
        if stage.parent != output.parent or not stage.name.startswith(output.name + ".stage."):
            raise RuntimeError("refusing to clean an unexpected support staging path")
        shutil.rmtree(stage)
    if temporary.exists():
        temporary.unlink()


def commit_prepared_support_publication(prepared: Mapping[str, object]) -> dict[str, object]:
    """Perform only the external-first/direction-second commit renames."""

    refuse_consumed_support_census()
    output = Path(prepared["output"])
    result = Path(prepared["result"])
    stage = Path(prepared["stage"])
    temporary = Path(prepared["temporary"])
    payload = prepared["payload"]
    os.rename(temporary, result)
    # If the second rename fails, the external receipt is an uncommitted orphan
    # because the direction-root marker never appears.
    os.rename(stage, output)
    return payload  # type: ignore[return-value]


def publish_support_census_create_only(
    output_root: Path,
    result_path: Path,
    payload: Mapping[str, object],
    *,
    before_commit: object | None = None,
) -> dict[str, object]:
    refuse_consumed_support_census()
    prepared = prepare_support_census_publication(output_root, result_path, payload)
    try:
        if before_commit is not None:
            before_commit()
    except BaseException:
        discard_prepared_support_publication(prepared)
        raise
    return commit_prepared_support_publication(prepared)


def support_census_tombstone() -> dict[str, object]:
    """Return the immutable terminal record without touching execution state."""

    return {
        "object_id": SUPPORT_CENSUS_OBJECT_ID,
        "lifecycle": SUPPORT_CENSUS_LIFECYCLE,
        "terminal_disposition": SUPPORT_CENSUS_TERMINAL_DISPOSITION,
        "consumed_attempt": SUPPORT_CENSUS_CONSUMED_ATTEMPT,
        "fresh_execution_enabled": SUPPORT_CENSUS_FRESH_EXECUTION_ENABLED,
        "reason": SUPPORT_CENSUS_TOMBSTONE_REASON,
    }


def load_consumed_support_census(path: str | Path) -> dict[str, object]:
    """Read and purely validate an already-published consumed-object receipt."""

    try:
        decoded = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SupportCensusError("consumed support receipt is unreadable") from error
    if not isinstance(decoded, Mapping):
        raise SupportCensusError("consumed support receipt must be a JSON object")
    return validate_support_census(decoded)


__all__ = [
    "SupportCensusConsumedError",
    "SupportCensusError",
    "load_consumed_support_census",
    "support_census_tombstone",
    "validate_support_census",
]

"""Strict checkpoint codecs for the variable-roster event runtime."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from ha_ctse_process.variable_roster_event import (
    CHECKPOINT_SCHEMA_VERSION,
    EVENT_ARCHITECTURE_SCHEMA_VERSION,
    EVENT_CONTROLLER,
    OPPORTUNITY_K0,
    OPPORTUNITY_SCHEDULE_NAME,
    SNAPSHOT_CAPABILITY_NAME,
    SNAPSHOT_CAPABILITY_VERSION,
    VECTOR_CHECKPOINT_SCHEMA_VERSION,
    VECTOR_RUNTIME_FIELDS,
    VariableRosterEventCore,
)


def _event_checkpoint_header(core: VariableRosterEventCore) -> dict[str, Any]:
    return {
        "architecture_mode": core.architecture_mode,
        "event_architecture_schema_version": EVENT_ARCHITECTURE_SCHEMA_VERSION,
        "opportunity_schedule_name": OPPORTUNITY_SCHEDULE_NAME,
        "k0": OPPORTUNITY_K0,
        "snapshot_capability_name": SNAPSHOT_CAPABILITY_NAME,
        "snapshot_capability_version": SNAPSHOT_CAPABILITY_VERSION,
        "architecture_state": core.architecture_state(),
    }


def _validate_shared_vector_cores(
    model_owner: VariableRosterEventCore,
    cores: Sequence[VariableRosterEventCore],
) -> tuple[VariableRosterEventCore, ...]:
    rows = tuple(cores)
    if not rows:
        raise ValueError("vector event checkpoint requires at least one runtime")
    if any(core.architecture_state() != model_owner.architecture_state() for core in rows):
        raise ValueError("vector event checkpoint architecture mismatch")
    if any(core.architecture_mode != model_owner.architecture_mode for core in rows):
        raise ValueError("vector event checkpoint mode mismatch")
    if tuple(core.environment_index for core in rows) != tuple(range(len(rows))):
        raise ValueError("vector event checkpoint environment indices are not canonical")
    for core in rows:
        if (
            core.commitment_model is not model_owner.commitment_model
            or core.event_critic is not model_owner.event_critic
            or core.low_actor is not model_owner.low_actor
            or core.low_critic is not model_owner.low_critic
        ):
            raise ValueError("vector event runtimes do not share one parameter graph")
    return rows


def vector_event_checkpoint_payload(
    *,
    model_owner: VariableRosterEventCore,
    cores: Sequence[VariableRosterEventCore],
    collector_snapshot: Mapping[str, Any],
    current_boundaries: Sequence[Mapping[str, Any]],
    optimizer_states: Mapping[str, Any],
    normalizer_states: Mapping[str, Any],
    counters: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one strict schema-3 checkpoint for a complete vector boundary."""

    rows = _validate_shared_vector_cores(model_owner, cores)
    boundaries = tuple(deepcopy(dict(value)) for value in current_boundaries)
    if len(boundaries) != len(rows):
        raise ValueError("vector event checkpoint boundary count mismatch")
    optimizer_value = deepcopy(dict(optimizer_states))
    normalizer_value = deepcopy(dict(normalizer_states))
    if set(optimizer_value) != {"high", "low"}:
        raise ValueError("vector event checkpoint requires high/low optimizers")
    if set(normalizer_value) != {"high", "low"}:
        raise ValueError("vector event checkpoint requires high/low normalizers")
    counter_value = deepcopy(dict(counters))
    required_counters = {
        "total_steps",
        "update_idx",
        "high_optimizer_steps",
        "low_optimizer_steps",
        "next_episode_id",
        "intrinsic_applied_count",
    }
    if set(counter_value) != required_counters:
        raise ValueError("vector event checkpoint counter schema mismatch")
    snapshot_value = deepcopy(dict(collector_snapshot))
    if snapshot_value.get("snapshot_capability_name") != SNAPSHOT_CAPABILITY_NAME or int(
        snapshot_value.get("snapshot_capability_version", -1)
    ) != SNAPSHOT_CAPABILITY_VERSION:
        raise ValueError("vector collector snapshot capability mismatch")
    runtime_payloads = []
    for core, boundary in zip(rows, boundaries):
        full_bundle = core.checkpoint_payload(
            collector_snapshot=snapshot_value,
            current_observation_state_boundary=boundary,
            optimizer_states=optimizer_value,
            normalizer_states=normalizer_value,
            pending_membership_transaction=core.pending_membership_transaction,
        )["event_architecture"]
        runtime_payloads.append(
            {name: deepcopy(full_bundle[name]) for name in VECTOR_RUNTIME_FIELDS}
        )
    bundle = {
        **_event_checkpoint_header(model_owner),
        "vector_checkpoint_schema_version": VECTOR_CHECKPOINT_SCHEMA_VERSION,
        "num_envs": len(rows),
        "runtime_state_absent_for_fresh_eval": False,
        "commitment_model_state": deepcopy(model_owner.commitment_model.state_dict()),
        "event_critic_state": deepcopy(model_owner.event_critic.state_dict()),
        "low_actor_state": deepcopy(model_owner.low_actor.state_dict()),
        "low_critic_state": deepcopy(model_owner.low_critic.state_dict()),
        "runtime_payloads": runtime_payloads,
        "collector_snapshot": snapshot_value,
        "optimizer_states": optimizer_value,
        "normalizer_states": normalizer_value,
        "counters": counter_value,
    }
    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "high_controller": EVENT_CONTROLLER,
        "event_architecture": bundle,
    }


class _ValidatedNoOpCollector:
    def restore_event_runtime(self, snapshot: Mapping[str, Any]) -> None:
        value = dict(snapshot)
        if value.get("snapshot_capability_name") != SNAPSHOT_CAPABILITY_NAME or int(
            value.get("snapshot_capability_version", -1)
        ) != SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("runtime payload collector capability mismatch")


def restore_vector_event_checkpoint(
    payload: Mapping[str, Any],
    *,
    model_owner: VariableRosterEventCore,
    cores: Sequence[VariableRosterEventCore],
    collector: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Strictly restore one complete vector event checkpoint."""

    value = dict(payload)
    if int(value.get("checkpoint_schema_version", -1)) != CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("vector event resume requires checkpoint schema 3")
    if value.get("high_controller") != EVENT_CONTROLLER:
        raise ValueError("vector event checkpoint controller mismatch")
    bundle = value.get("event_architecture")
    if not isinstance(bundle, Mapping):
        raise ValueError("vector event checkpoint is missing event_architecture")
    if "event_semantic" in bundle:
        raise ValueError("non-Iteration-5 vector checkpoint rejects semantic bundle")
    required = {
        *set(_event_checkpoint_header(model_owner)),
        "vector_checkpoint_schema_version",
        "num_envs",
        "runtime_state_absent_for_fresh_eval",
        "commitment_model_state",
        "event_critic_state",
        "low_actor_state",
        "low_critic_state",
        "runtime_payloads",
        "collector_snapshot",
        "optimizer_states",
        "normalizer_states",
        "counters",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise ValueError(f"vector event checkpoint is missing mandatory fields: {missing}")
    if bool(bundle["runtime_state_absent_for_fresh_eval"]):
        raise ValueError("model-only fresh-evaluation checkpoint cannot resume live state")
    header = _event_checkpoint_header(model_owner)
    for name, expected in header.items():
        actual = bundle[name]
        mismatch = (
            dict(actual) != dict(expected)
            if isinstance(expected, Mapping)
            else actual != expected
        )
        if mismatch:
            raise ValueError(f"vector event checkpoint header mismatch: {name}")
    rows = _validate_shared_vector_cores(model_owner, cores)
    if int(bundle["vector_checkpoint_schema_version"]) != VECTOR_CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("vector event checkpoint schema mismatch")
    if int(bundle["num_envs"]) != len(rows):
        raise ValueError("vector event checkpoint environment count mismatch")
    runtime_payloads = list(bundle["runtime_payloads"])
    if len(runtime_payloads) != len(rows):
        raise ValueError("vector event runtime payload count mismatch")
    collector_snapshot = deepcopy(dict(bundle["collector_snapshot"]))
    if collector_snapshot.get("snapshot_capability_name") != SNAPSHOT_CAPABILITY_NAME or int(
        collector_snapshot.get("snapshot_capability_version", -1)
    ) != SNAPSHOT_CAPABILITY_VERSION:
        raise ValueError("vector collector snapshot capability mismatch")
    first_optimizer: dict[str, Any] | None = None
    first_normalizer: dict[str, Any] | None = None
    for index, (core, runtime_payload) in enumerate(zip(rows, runtime_payloads)):
        if not isinstance(runtime_payload, Mapping) or set(runtime_payload) != VECTOR_RUNTIME_FIELDS:
            raise ValueError("vector event runtime field schema mismatch")
        runtime_bundle = {
            **header,
            "commitment_model_state": bundle["commitment_model_state"],
            "event_critic_state": bundle["event_critic_state"],
            "low_actor_state": bundle["low_actor_state"],
            "low_critic_state": bundle["low_critic_state"],
            "optimizer_states": bundle["optimizer_states"],
            "normalizer_states": bundle["normalizer_states"],
            **deepcopy(dict(runtime_payload)),
            "collector_active_presentation": deepcopy(
                collector_snapshot.get("collector_active_presentation")
            ),
            "collector_pending_command_response_state": deepcopy(
                collector_snapshot.get("collector_pending_command_response_state")
            ),
            "worker_environment_snapshot": deepcopy(
                collector_snapshot.get("worker_environment_snapshot")
            ),
            "environment_rng_state": deepcopy(
                collector_snapshot.get("environment_rng_state")
            ),
            "collector_snapshot": collector_snapshot,
        }
        optimizers, normalizers = core.restore_checkpoint_payload(
            {
                "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
                "high_controller": EVENT_CONTROLLER,
                "event_architecture": runtime_bundle,
            },
            collector=collector if index == 0 else _ValidatedNoOpCollector(),
        )
        if first_optimizer is None:
            first_optimizer = optimizers
            first_normalizer = normalizers
    assert first_optimizer is not None and first_normalizer is not None
    if set(first_optimizer) != {"high", "low"} or set(first_normalizer) != {
        "high",
        "low",
    }:
        raise ValueError("vector event restored optimizer/normalizer schema mismatch")
    counters = deepcopy(dict(bundle["counters"]))
    if set(counters) != {
        "total_steps",
        "update_idx",
        "high_optimizer_steps",
        "low_optimizer_steps",
        "next_episode_id",
        "intrinsic_applied_count",
    }:
        raise ValueError("vector event restored counter schema mismatch")
    return first_optimizer, first_normalizer, counters


def event_model_only_checkpoint_payload(
    *,
    model_owner: VariableRosterEventCore,
    normalizer_states: Mapping[str, Any],
    total_steps: int,
    update_idx: int,
) -> dict[str, Any]:
    normalizers = deepcopy(dict(normalizer_states))
    if set(normalizers) != {"high", "low"}:
        raise ValueError("fresh evaluation requires exact high/low normalizers")
    bundle = {
        **_event_checkpoint_header(model_owner),
        "runtime_state_absent_for_fresh_eval": True,
        "commitment_model_state": deepcopy(model_owner.commitment_model.state_dict()),
        "event_critic_state": deepcopy(model_owner.event_critic.state_dict()),
        "low_actor_state": deepcopy(model_owner.low_actor.state_dict()),
        "low_critic_state": deepcopy(model_owner.low_critic.state_dict()),
        "normalizer_states": normalizers,
        "total_steps": int(total_steps),
        "update_idx": int(update_idx),
    }
    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "high_controller": EVENT_CONTROLLER,
        "event_architecture": bundle,
    }


def restore_event_model_only_checkpoint(
    payload: Mapping[str, Any],
    *,
    model_owner: VariableRosterEventCore,
) -> tuple[dict[str, Any], int, int]:
    value = dict(payload)
    if int(value.get("checkpoint_schema_version", -1)) != CHECKPOINT_SCHEMA_VERSION or value.get(
        "high_controller"
    ) != EVENT_CONTROLLER:
        raise ValueError("fresh evaluation requires an event schema-3 checkpoint")
    bundle = value.get("event_architecture")
    if not isinstance(bundle, Mapping):
        raise ValueError("fresh evaluation checkpoint is missing event_architecture")
    if "event_semantic" in bundle:
        raise ValueError("non-Iteration-5 fresh checkpoint rejects semantic bundle")
    required = {
        *set(_event_checkpoint_header(model_owner)),
        "runtime_state_absent_for_fresh_eval",
        "commitment_model_state",
        "event_critic_state",
        "low_actor_state",
        "low_critic_state",
        "normalizer_states",
        "total_steps",
        "update_idx",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise ValueError(f"fresh evaluation checkpoint is missing fields: {missing}")
    if not bool(bundle["runtime_state_absent_for_fresh_eval"]):
        raise ValueError("fresh evaluation checkpoint must explicitly omit runtime state")
    header = _event_checkpoint_header(model_owner)
    for name, expected in header.items():
        actual = bundle[name]
        mismatch = (
            dict(actual) != dict(expected)
            if isinstance(expected, Mapping)
            else actual != expected
        )
        if mismatch:
            raise ValueError(f"fresh evaluation checkpoint header mismatch: {name}")
    model_owner.commitment_model.load_state_dict(bundle["commitment_model_state"], strict=True)
    model_owner.event_critic.load_state_dict(bundle["event_critic_state"], strict=True)
    model_owner.low_actor.load_state_dict(bundle["low_actor_state"], strict=True)
    model_owner.low_critic.load_state_dict(bundle["low_critic_state"], strict=True)
    normalizers = deepcopy(dict(bundle["normalizer_states"]))
    if set(normalizers) != {"high", "low"}:
        raise ValueError("fresh evaluation normalizer schema mismatch")
    return normalizers, int(bundle["total_steps"]), int(bundle["update_idx"])

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import fields
import hashlib

import numpy as np
import torch

from ha_ctse_process import event_commitment_rng, event_commitment_types
from ha_ctse_process import event_held_commitment_link
from ha_ctse_process.noncalendar_commitment_testbed import (
    EVENT_SEED,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    MARK_SEED,
    OPPORTUNITY_SEED,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
)


def test_direct_type_owners_preserve_identity_fields_and_arm_state() -> None:
    owned = (
        "SegmentRecord",
        "LifecycleState",
        "CollectionCursor",
        "EventTrajectory",
        "CommitmentArm",
        "TrainingState",
    )
    for name in owned:
        assert getattr(event_held_commitment_link, name) is getattr(
            event_commitment_types, name
        )

    assert tuple(field.name for field in fields(event_commitment_types.SegmentRecord)) == (
        "episode_id", "key", "membership_epoch", "segment_id",
        "start_active_step", "end_active_step", "censored", "close_reason",
        "opportunity_count",
    )
    assert tuple(field.name for field in fields(event_commitment_types.LifecycleState)) == (
        "membership_epoch", "z", "q", "segment_id",
        "segment_start_active_step", "active_steps",
        "non_create_opportunities", "spell_opportunity_count",
    )
    assert tuple(field.name for field in fields(event_commitment_types.CollectionCursor)) == (
        "episode_ids", "ledgers", "environments", "hidden", "lifecycles",
        "segments",
    )
    assert tuple(field.name for field in fields(event_commitment_types.TrainingState)) == (
        "arm", "replicate", "profile", "seed_map", "completed_update",
        "next_episode_id", "base_optimizer_steps", "event_optimizer_steps",
        "pending_cursor", "rngs",
    )
    state = event_commitment_types.TrainingState("EHC", 3)
    assert state.profile == "train"
    assert state.seed_map == {} and state.rngs == {}
    assert state.completed_update == state.next_episode_id == 0
    assert state.base_optimizer_steps == state.event_optimizer_steps == 0
    assert state.pending_cursor is None

    before = torch.get_rng_state().clone()
    try:
        torch.manual_seed(98_765)
        first = event_commitment_types.CommitmentArm("DUM")
        torch.manual_seed(98_765)
        second = event_commitment_types.CommitmentArm("DUM")
    finally:
        torch.set_rng_state(before)
    assert first.base_parameter_count == second.base_parameter_count == 14_980
    assert first.added_parameter_count == second.added_parameter_count == 1_608
    assert first.state_dict().keys() == second.state_dict().keys()
    assert all(
        torch.equal(first.state_dict()[name], second.state_dict()[name])
        for name in first.state_dict()
    )


def test_direct_rng_owner_preserves_seed_payload_replay_and_binding() -> None:
    replicate = 2
    expected = {
        "ledger": TRAIN_TASK_SEED + 2000,
        "order": TRAIN_ORDER_SEED + 2000,
        "primitive": TRAIN_ACTION_SEED + 2000,
        "opportunity": OPPORTUNITY_SEED + 2000,
        "event": EVENT_SEED + 2000,
        "mark": MARK_SEED + 2000,
    }
    assert event_commitment_rng.authoritative_seed_map("train", replicate) == expected
    assert event_commitment_rng.authoritative_seed_map("iid", replicate) == (
        expected | {"ledger": IID_EVAL_TASK_SEED + 2000}
    )
    assert event_commitment_rng.authoritative_seed_map("held_out", replicate) == (
        expected | {"ledger": HELD_OUT_EVAL_TASK_SEED + 2000}
    )
    state = event_commitment_rng.make_training_state("EHC", replicate)
    assert type(state) is event_commitment_types.TrainingState
    assert tuple(state.rngs) == event_commitment_rng.RNG_NAMES
    starts = event_commitment_rng.owned_rng_states(state)

    schedule = [{
        "stream": "primitive",
        "operation": "random",
        "dtype": "float32",
        "shape": [2, 3],
        "coordinates": {"episode_ids": [8, 9], "time": 4},
    }]
    arrays, end_state = event_commitment_rng.replay_rng_schedule_arrays(
        starts["primitive"], schedule, seed=state.seed_map["primitive"]
    )
    assert arrays[0].dtype == np.float32 and arrays[0].shape == (2, 3)
    assert end_state == event_commitment_rng.replay_rng_schedule_end_state(
        starts["primitive"], schedule, seed=state.seed_map["primitive"]
    )
    context = {"arm": "EHC", "replicate": replicate, "update": 0}
    binding = event_commitment_rng.make_rng_binding(
        context=context,
        stream="primitive",
        seed=state.seed_map["primitive"],
        start_state=starts["primitive"],
        draw_schedule=schedule,
        expected_end_state=end_state,
    )
    assert event_commitment_rng.validate_rng_binding(
        binding,
        expected_context=context,
        expected_stream="primitive",
        expected_seed=state.seed_map["primitive"],
        expected_start_state=starts["primitive"],
    ) == (True, end_state)
    corrupted = deepcopy(binding)
    corrupted["unexpected"] = True
    assert event_commitment_rng.validate_rng_binding(
        corrupted,
        expected_context=context,
        expected_stream="primitive",
        expected_seed=state.seed_map["primitive"],
        expected_start_state=starts["primitive"],
    ) == (False, None)

    source = np.asarray([[1.25, -0.0], [3.5, 9.0]], dtype=np.float64)[:, ::-1]
    payload = event_commitment_rng._float32_payload(source)
    canonical = np.ascontiguousarray(source, dtype=np.float32).tobytes(order="C")
    assert payload["bytes_b64"] == base64.b64encode(canonical).decode("ascii")
    assert payload["sha256"] == hashlib.sha256(canonical).hexdigest()

    rng_functions = (
        "authoritative_seed_map", "make_training_state", "owned_rng_states",
        "collection_rng_schedules", "replay_rng_schedule_end_state",
        "replay_rng_schedule_arrays", "make_rng_binding", "validate_rng_binding",
    )
    for name in rng_functions:
        assert getattr(event_held_commitment_link, name) is getattr(
            event_commitment_rng, name
        )

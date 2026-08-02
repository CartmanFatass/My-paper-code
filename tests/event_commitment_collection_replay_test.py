from __future__ import annotations

import torch

from ha_ctse_process import event_held_commitment_link
from ha_ctse_process.event_commitment_collector import collect_trajectory
from ha_ctse_process.event_commitment_replay import (
    ReplayOutput,
    replay_trajectory,
    validate_replay,
)
from ha_ctse_process.event_commitment_rng import make_training_state
from ha_ctse_process.noncalendar_commitment_testbed import (
    FORMAL_EXECUTION_BACKEND,
    require_registered_backend,
)


def test_collection_and_replay_have_unique_direct_owners() -> None:
    assert collect_trajectory.__module__ == (
        "ha_ctse_process.event_commitment_collector"
    )
    assert ReplayOutput.__module__ == "ha_ctse_process.event_commitment_replay"
    assert replay_trajectory.__module__ == (
        "ha_ctse_process.event_commitment_replay"
    )
    assert validate_replay.__module__ == (
        "ha_ctse_process.event_commitment_replay"
    )
    assert event_held_commitment_link.collect_trajectory is collect_trajectory
    assert event_held_commitment_link.validate_replay is validate_replay


def test_minimal_deterministic_collection_replay_parity() -> None:
    require_registered_backend(FORMAL_EXECUTION_BACKEND)
    device = torch.device(FORMAL_EXECUTION_BACKEND)
    arms, _, _ = event_held_commitment_link.initialize_arms(device)
    arm = arms["EHC"]

    first = collect_trajectory(
        arm,
        make_training_state("EHC", 0),
        device=device,
        episode_ids=(0,),
        max_steps=16,
        deterministic=True,
    )
    second = collect_trajectory(
        arm,
        make_training_state("EHC", 0),
        device=device,
        episode_ids=(0,),
        max_steps=16,
        deterministic=True,
    )

    for name in (
        "actions",
        "old_log_probs",
        "old_values",
        "hidden_after",
        "event_kind",
        "event_inputs",
        "event_categorical_actions",
        "event_u",
        "event_new_z",
        "event_old_cat_logp",
        "event_old_mark_component_logp",
        "event_old_joint_logp",
    ):
        assert torch.equal(getattr(first, name), getattr(second, name))

    replay, report = validate_replay(arm, first, device=device)
    assert isinstance(replay, ReplayOutput)
    assert report["passed"] and not report["failures"]

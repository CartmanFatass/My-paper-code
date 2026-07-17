from __future__ import annotations

import torch

from ha_ctse_process.dynamic_roster_direct import (
    LEARNING_RATE,
    MODEL_INITIALIZATION_SEED,
    PPO_PASSES,
    REPLAY_TOLERANCE,
    TRAIN_LEDGER_SEED,
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
    hidden_lifecycle_contract_valid,
    load_checkpoint,
    maximum_state_difference,
    model_state_copy,
    nested_state_maximum_difference,
    optimize_direct_update,
    replay_direct_trajectory,
    replay_errors,
    save_checkpoint,
)
from ha_ctse_process.dynamic_roster_testbed import make_dynamic_roster_ledger


def test_stage_b_direct_replay_hidden_and_optimizer_contract(tmp_path) -> None:
    torch.manual_seed(MODEL_INITIALIZATION_SEED)
    model = DirectPrimitiveARPolicy()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    initial_state = model_state_copy(model)
    trajectory = collect_direct_trajectory(
        model,
        ledger_ids=(0, 1),
        ledger_seed=TRAIN_LEDGER_SEED,
        device=torch.device("cpu"),
    )

    assert trajectory.environment_steps == 160
    assert trajectory.active_token_count == 640
    replay = replay_direct_trajectory(
        model, trajectory, device=torch.device("cpu")
    )
    errors = replay_errors(replay, trajectory)
    assert all(value <= REPLAY_TOLERANCE for value in errors.values())
    assert hidden_lifecycle_contract_valid(trajectory)

    for env_index, episode_id in enumerate(trajectory.ledger_ids):
        ledger = make_dynamic_roster_ledger(
            episode_id, master_seed=TRAIN_LEDGER_SEED
        )
        for key in ledger.temporary_leave:
            frozen = trajectory.hidden_after[19, env_index, key]
            assert torch.equal(trajectory.hidden_before[20, env_index, key], frozen)
            assert torch.equal(trajectory.hidden_after[39, env_index, key], frozen)
            assert torch.equal(trajectory.hidden_before[40, env_index, key], frozen)
        for key in (4, 5):
            assert torch.equal(
                trajectory.hidden_before[40, env_index, key],
                torch.zeros_like(trajectory.hidden_before[40, env_index, key]),
            )

    metrics = optimize_direct_update(
        model,
        optimizer,
        trajectory,
        device=torch.device("cpu"),
        ppo_passes=PPO_PASSES,
    )
    assert metrics["optimizer_steps"] == PPO_PASSES
    assert metrics["finite_update"] == 1.0
    assert maximum_state_difference(initial_state, model_state_copy(model)) > 0.0

    checkpoint = tmp_path / "direct.pt"
    save_checkpoint(
        checkpoint,
        model=model,
        optimizer=optimizer,
        completed_updates=1,
        next_ledger_id=2,
    )
    restored = DirectPrimitiveARPolicy()
    restored_optimizer = torch.optim.Adam(
        restored.parameters(), lr=LEARNING_RATE
    )
    bundle = load_checkpoint(
        checkpoint, model=restored, optimizer=restored_optimizer
    )
    assert bundle["schema_version"] == 3
    assert bundle["completed_updates"] == 1
    assert bundle["next_ledger_id"] == 2
    assert maximum_state_difference(
        model_state_copy(model), model_state_copy(restored)
    ) == 0.0
    assert nested_state_maximum_difference(
        bundle["optimizer_state"], restored_optimizer.state_dict()
    ) == 0.0

    continuation = collect_direct_trajectory(
        model,
        ledger_ids=(2, 3),
        ledger_seed=TRAIN_LEDGER_SEED,
        device=torch.device("cpu"),
    )
    uninterrupted_metrics = optimize_direct_update(
        model,
        optimizer,
        continuation,
        device=torch.device("cpu"),
        ppo_passes=PPO_PASSES,
    )
    resumed_metrics = optimize_direct_update(
        restored,
        restored_optimizer,
        continuation,
        device=torch.device("cpu"),
        ppo_passes=PPO_PASSES,
    )
    assert uninterrupted_metrics == resumed_metrics
    assert maximum_state_difference(
        model_state_copy(model), model_state_copy(restored)
    ) == 0.0
    assert nested_state_maximum_difference(
        optimizer.state_dict(), restored_optimizer.state_dict()
    ) == 0.0

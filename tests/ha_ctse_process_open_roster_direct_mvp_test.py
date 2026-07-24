from __future__ import annotations

import numpy as np
import pytest
import torch

from scripts import run_open_roster_direct_g5 as runner

from ha_ctse_process.dynamic_roster_direct import (
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
    evaluate_direct_policy,
    optimize_direct_update,
    replay_direct_trajectory,
    replay_errors,
)
from ha_ctse_process.dynamic_roster_testbed import (
    HORIZON,
    OBSERVATION_DIM,
    constructive_actions,
)
from ha_ctse_process.open_roster_direct_mvp import (
    HELDOUT_CAPACITY,
    HELDOUT_PROFILES,
    TRAIN_CAPACITY,
    TRAIN_LEDGER_SEED,
    TRAIN_PROFILES,
    OpenRosterDynamicEnv,
    make_open_roster_heldout_ledger,
    make_open_roster_training_ledger,
    open_roster_lifecycle_contract_valid,
)


def test_open_roster_profiles_have_constructive_utility_one() -> None:
    ledgers = [
        make_open_roster_training_ledger(index)
        for index in range(len(TRAIN_PROFILES))
    ] + [
        make_open_roster_heldout_ledger(index)
        for index in range(len(HELDOUT_PROFILES))
    ]
    for ledger in ledgers:
        environment = OpenRosterDynamicEnv(ledger)
        while environment.time < HORIZON:
            view = environment.observe()
            environment.step(constructive_actions(environment, view))
        outcome = environment.outcome()
        expected_roster = tuple(
            count
            for count in ledger.profile.phase_counts
            for _ in range(20)
        )
        assert outcome.utility == 1.0
        assert outcome.roster_sizes == expected_roster
        assert outcome.short_required_total == ledger.expected_short_requirement


def test_direct_policy_is_invariant_to_extra_inactive_capacity() -> None:
    torch.manual_seed(551)
    model = DirectPrimitiveARPolicy()
    active_keys = (0, 2, 4, 6)
    base_observations = torch.randn(1, TRAIN_CAPACITY, OBSERVATION_DIM)
    wide_observations = torch.randn(1, HELDOUT_CAPACITY, OBSERVATION_DIM)
    wide_observations[:, :TRAIN_CAPACITY] = base_observations
    base_mask = torch.zeros(1, TRAIN_CAPACITY, dtype=torch.bool)
    wide_mask = torch.zeros(1, HELDOUT_CAPACITY, dtype=torch.bool)
    base_mask[:, active_keys] = True
    wide_mask[:, active_keys] = True
    base_order = torch.full((1, TRAIN_CAPACITY), -1, dtype=torch.long)
    wide_order = torch.full((1, HELDOUT_CAPACITY), -1, dtype=torch.long)
    base_order[0, : len(active_keys)] = torch.tensor(active_keys)
    wide_order[0, : len(active_keys)] = torch.tensor(active_keys)
    base_hidden = torch.randn(1, TRAIN_CAPACITY, model.hidden_dim)
    wide_hidden = torch.randn(1, HELDOUT_CAPACITY, model.hidden_dim)
    wide_hidden[:, :TRAIN_CAPACITY] = base_hidden

    base = model.forward_step(
        observations=base_observations,
        active_mask=base_mask,
        order=base_order,
        hidden=base_hidden,
        deterministic=True,
    )
    wide = model.forward_step(
        observations=wide_observations,
        active_mask=wide_mask,
        order=wide_order,
        hidden=wide_hidden,
        deterministic=True,
    )
    assert torch.equal(base.actions[:, active_keys], wide.actions[:, active_keys])
    assert torch.allclose(
        base.token_log_probs[:, active_keys],
        wide.token_log_probs[:, active_keys],
        atol=1.0e-7,
        rtol=0.0,
    )
    assert torch.allclose(base.value, wide.value, atol=1.0e-7, rtol=0.0)
    assert torch.allclose(
        base.next_hidden[:, active_keys],
        wide.next_hidden[:, active_keys],
        atol=1.0e-7,
        rtol=0.0,
    )


def test_open_roster_collection_replay_update_and_heldout_width() -> None:
    torch.manual_seed(552)
    device = torch.device("cpu")
    model = DirectPrimitiveARPolicy().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=3.0e-4)
    trajectory = collect_direct_trajectory(
        model,
        ledger_ids=(0, 1, 2),
        ledger_seed=TRAIN_LEDGER_SEED,
        device=device,
        ledger_factory=make_open_roster_training_ledger,
        environment_factory=OpenRosterDynamicEnv,
    )
    assert trajectory.observations.shape == (
        HORIZON,
        3,
        TRAIN_CAPACITY,
        OBSERVATION_DIM,
    )
    assert open_roster_lifecycle_contract_valid(
        trajectory, ledger_seed=TRAIN_LEDGER_SEED
    )
    errors = replay_errors(
        replay_direct_trajectory(model, trajectory, device=device), trajectory
    )
    assert max(errors.values()) <= 1.0e-6
    metrics = optimize_direct_update(
        model, optimizer, trajectory, device=device, ppo_passes=1
    )
    assert metrics["finite_update"] == 1.0
    heldout = evaluate_direct_policy(
        model,
        episode_ids=(0, 1, 2, 3),
        deterministic=True,
        device=device,
        ledger_factory=make_open_roster_heldout_ledger,
        environment_factory=OpenRosterDynamicEnv,
    )
    assert heldout["utility"].shape == (4,)
    assert np.all(np.isfinite(heldout["utility"]))


def test_open_roster_nonformal_pipeline_and_fail_closed_analysis(tmp_path) -> None:
    run_root = tmp_path / "exercise"
    result = runner.exercise(run_root=run_root)
    assert result["formal"] is False
    assert result["operational_valid"] is True
    assert result["branch"] == "NONFORMAL_OPEN_ROSTER_G5_EXERCISE_COMPLETE"

    training = runner._read_json(run_root / "train_manifest.json")
    training["runtime"]["torch_threads"] = 2
    runner._write_json(run_root / "train_manifest.json", training)
    rejected = runner.analyze(run_root=run_root)
    assert rejected["operational_valid"] is False
    assert rejected["branch"] == "INVALID_OPEN_ROSTER_DIRECT_G5"


def test_formal_g5_counts_and_token_are_frozen(tmp_path) -> None:
    with pytest.raises(ValueError, match="authorization token"):
        runner.train(
            run_root=tmp_path / "bad_token",
            source_commit="not-used",
            formal=True,
            authorization_token="wrong",
            replicates=runner.FORMAL_REPLICATES,
            updates=runner.FORMAL_UPDATES,
            num_envs=runner.FORMAL_NUM_ENVS,
            eval_episodes=runner.FORMAL_EVAL_EPISODES,
        )

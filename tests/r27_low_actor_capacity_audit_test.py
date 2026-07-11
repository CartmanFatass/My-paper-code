from __future__ import annotations

import numpy as np
import pytest
import torch

from ha_ctse_process.low_actor_capacity_audit import (
    CapacitySnapshotBatch,
    cluster_bootstrap_difference,
    evaluate_static_checkpoint,
    forward_actor_snapshot,
    gate_static_family,
    grouped_reset_split,
    read_capacity_snapshot_shards,
    write_capacity_snapshot_shard,
)
from ha_ctse_process.standalone_agent import StrictHMASDMAPPOLowLevelPolicy


def make_snapshots(
    *, resets: int = 10, rows_per_reset: int = 4
) -> CapacitySnapshotBatch:
    reset_id = np.repeat(np.arange(resets, dtype=np.int64), rows_per_reset)
    rows = int(reset_id.size)
    return CapacitySnapshotBatch(
        observation=np.arange(rows * 6, dtype=np.float32).reshape(rows, 6) / 10.0,
        actor_hidden=np.arange(rows * 8, dtype=np.float32).reshape(rows, 8) / 20.0,
        natural_skill=np.arange(rows, dtype=np.int64) % 4,
        previous_skill=(np.arange(rows, dtype=np.int64) + 1) % 4,
        duration_idx=np.arange(rows, dtype=np.int64) % 4,
        skill_age=np.arange(rows, dtype=np.int64) % 9,
        episode_done_mask=np.zeros(rows, dtype=np.bool_),
        reset_id=reset_id,
        reset_seed=27000 + reset_id,
        episode_id=reset_id.copy(),
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        checkpoint_id=np.full(rows, "arm0_final"),
        checkpoint_update=np.full(rows, 32, dtype=np.int64),
    )


def test_snapshot_shard_roundtrip_preserves_every_field(tmp_path):
    expected = make_snapshots()
    write_capacity_snapshot_shard(tmp_path / "reset_0000.npz", expected)

    actual = read_capacity_snapshot_shards(tmp_path)

    for field in CapacitySnapshotBatch.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(actual, field), getattr(expected, field))


def test_grouped_split_is_deterministic_and_never_leaks_resets():
    batch = make_snapshots(resets=10)

    first = grouped_reset_split(batch.reset_id, seed=27011)
    second = grouped_reset_split(batch.reset_id, seed=27011)

    for field in ("train", "validation", "test"):
        np.testing.assert_array_equal(getattr(first, field), getattr(second, field))
    assert first.train_reset_ids == second.train_reset_ids
    assert first.validation_reset_ids == second.validation_reset_ids
    assert first.test_reset_ids == second.test_reset_ids
    assert set(first.train_reset_ids).isdisjoint(first.validation_reset_ids)
    assert set(first.train_reset_ids).isdisjoint(first.test_reset_ids)
    assert set(first.validation_reset_ids).isdisjoint(first.test_reset_ids)
    assert len(first.train_reset_ids) == 6
    assert len(first.validation_reset_ids) == 2
    assert len(first.test_reset_ids) == 2


def test_reset_cluster_bootstrap_is_deterministic_and_positive():
    reset_ids = np.repeat(np.arange(8, dtype=np.int64), 4)
    active = np.linspace(0.2, 0.8, reset_ids.size)
    inactive = active - 0.1

    first = cluster_bootstrap_difference(
        active, inactive, reset_ids, reps=500, seed=27012
    )
    second = cluster_bootstrap_difference(
        active, inactive, reset_ids, reps=500, seed=27012
    )

    assert first == second
    assert first.lower > 0.0


def test_snapshot_rejects_nonfinite_hidden_state(tmp_path):
    batch = make_snapshots()
    batch.actor_hidden[3, 2] = np.nan

    with pytest.raises(ValueError, match="actor_hidden contains non-finite"):
        write_capacity_snapshot_shard(tmp_path / "bad.npz", batch)


def make_continuous_actor() -> StrictHMASDMAPPOLowLevelPolicy:
    torch.manual_seed(27020)
    return StrictHMASDMAPPOLowLevelPolicy(
        obs_dim=6,
        state_dim=7,
        n_skills=4,
        num_team_codes=2,
        action_dim=4,
        hidden_dim=8,
        action_space_type="continuous",
        continuous_action_distribution="tanh_gaussian",
        actor_condition_on_team_code=False,
        device="cpu",
    ).eval()


def test_detached_forward_matches_live_actor_distribution():
    actor = make_continuous_actor()
    obs = torch.randn(5, 6)
    skills = torch.tensor([0, 1, 2, 3, 0])
    hidden = torch.randn(5, 8)

    result = forward_actor_snapshot(
        actor, obs, skills, hidden, inactive_film=False
    )
    with torch.no_grad():
        actions, _, _, _, live_hidden, _ = actor.act(
            obs,
            skills,
            hidden.clone(),
            torch.zeros(5, 7),
            torch.zeros(5, dtype=torch.long),
            torch.zeros(5, 8),
            deterministic=True,
        )

    torch.testing.assert_close(
        result.deterministic_action, actions, atol=1e-6, rtol=1e-6
    )
    torch.testing.assert_close(
        result.new_hidden, live_hidden, atol=1e-6, rtol=1e-6
    )
    assert not result.action_mean.requires_grad


def test_identity_film_has_zero_skill_pair_separation():
    actor = make_continuous_actor()
    batch = make_snapshots(resets=10)

    report = evaluate_static_checkpoint(
        actor,
        batch,
        checkpoint_id="fixture",
        bootstrap_reps=200,
        bootstrap_seed=27021,
    )

    assert report["inactive_control"]["max_abs_symmetric_kl"] <= 1e-8
    assert report["inactive_control"]["max_stdmean_distance"] <= 1e-8


def test_static_family_requires_two_of_three_agreement():
    passing = {
        "status": "PASS",
        "zero_h": {"pass": True, "mean_skl": 0.03},
        "rollout_h": {"pass": True, "mean_skl": 0.03},
        "hidden_retention_ratio": 0.8,
    }
    failing = {
        "status": "FAIL",
        "zero_h": {"pass": False, "mean_skl": 0.0},
        "rollout_h": {"pass": False, "mean_skl": 0.0},
        "hidden_retention_ratio": 0.0,
    }

    family = gate_static_family([passing, passing, failing])

    assert family["zero_h_pass"] is True
    assert family["rollout_h_pass"] is True
    assert family["recurrent_washout"] is False

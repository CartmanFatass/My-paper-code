"""Non-rollout checks only. The selected eight episodes run inside B01 itself."""
import math

import numpy as np
import torch
from torch import nn

from experiments.candidates.vsp_03.vsp03_b01.b01 import (
    Model, metrics, objective, return_to_go, scales, tapes, vectors, write_json,
)


def test_paired_initialization_and_trainable_prior():
    treatment, generic = Model(1, "T"), Model(1, "G")
    tv, gv = vectors(treatment), vectors(generic)
    assert {key: value.numel() for key, value in tv.items()} == {
        "actor": 1314, "critic": 257, "total": 1571}
    for key, value in generic.state_dict().items():
        if key not in ("direct_b", "actor.4.bias"):
            assert torch.equal(value, treatment.state_dict()[key])
    x = torch.zeros(2, 6)
    x[1, 5] = 1
    torch.testing.assert_close(treatment.logits(x).sigmoid(), torch.tensor([0.25, 0.75]))
    torch.testing.assert_close(generic.logits(x).sigmoid(), torch.tensor([0.5, 0.5]))
    assert all(p.requires_grad and p.dtype == torch.float32 for p in treatment.parameters())
    assert scales(treatment, tv)["total"]["displacement_l2"] == 0
    assert torch.equal(gv["critic"], tv["critic"])


def test_mc_excludes_sunk_waiting_and_keeps_final_eight_ticks():
    # Episode 0 succeeds at t8, 1 never submits, 2 fails at t4.
    units = np.array([182, -40, -14], dtype=np.int64)
    ids = np.array([0, 0, 1, 2])
    times = np.array([0, 8, 32, 4])
    np.testing.assert_allclose(return_to_go(units, ids, times), [0.91, 0.95, -0.04, -0.05])


class ConstantHeads(nn.Module):
    def __init__(self):
        super().__init__()
        self.logit = nn.Parameter(torch.tensor(0.0))
        self.value = nn.Parameter(torch.tensor(0.2))

    def logits(self, x):
        return self.logit.expand(len(x))

    def critic(self, x):
        return self.value.expand(len(x), 1)


def test_episode_actor_reduction_valid_row_critic_and_detached_advantage():
    model = ConstantHeads()
    batch = {"x": np.zeros((3, 6), dtype=np.float32), "episodes": 2,
             "returns": np.array([1, 0, -0.2], dtype=np.float32),
             "actions": np.array([1, 0, 1], dtype=np.float32)}
    loss, info = objective(model, batch, 64)
    error = np.array([0.8, -0.2, -0.4])
    expected_actor = math.log(2) * error.sum() / 2
    expected_critic = 0.5 * np.mean(error ** 2)
    assert abs(info["actor_loss"] - expected_actor) < 1e-6
    assert abs(info["critic_loss"] - expected_critic) < 1e-6
    loss.backward()
    # Critic gradient contains only the MSE term; actor advantage is detached.
    torch.testing.assert_close(model.value.grad, torch.tensor(-error.mean(), dtype=torch.float32))
    expected_policy = -np.sum((batch["actions"] - 0.5) * error) / 2
    torch.testing.assert_close(model.logit.grad, torch.tensor(expected_policy, dtype=torch.float32))
    assert info["entropy_coefficient"] == 0
    _, first = objective(model, batch, 1)
    assert first["entropy_coefficient"] == 0.01
    assert abs(first["entropy_per_episode"] - 3 * math.log(2) / 2) < 1e-6


def test_addressed_tapes_do_not_depend_on_batch_partition():
    whole = tapes(1, 100, 7, 3)
    partitioned = np.concatenate([tapes(1, 100, 7, 1), tapes(1, 100, 8, 2)])
    assert whole.shape == (3, 40)
    assert np.array_equal(whole, partitioned)
    assert not np.array_equal(whole, tapes(1, 328, 7, 3))


def test_primary_component_publication_without_simulation(tmp_path):
    rows = [{"return": 0.93, "success": 1, "attempt": 1, "failed_attempt": 0,
             "non_submission": 0, "waiting_ticks": 4, "departures": 2,
             "reentries": 1, "pre_submit_departures": 1, "pre_submit_reentries": 1}]
    summary = metrics(rows)
    assert summary["submitted_after_reentry"] == {"episodes": 1, "mean_return": 0.93}
    assert write_json(tmp_path / "summary.json", summary) == summary

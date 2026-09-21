from __future__ import annotations

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.frozen_mean_gate_b08.engine import Gate, freeze_foundation
from experiments.candidates.ucope.paired_branch_credit_b10.collection import (
    FocalCase, collect_pair, schedule,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


class CoupledFixture(SyntheticAdapter):
    """Non-UAV test system: each agent observes its next neighbor's position."""

    def _obs(self):
        obs = super()._obs()
        obs[:, 3:6] = np.roll(self.positions, -1, axis=0) / 1000.0
        return obs


class FixedFeedback(torch.nn.Module):
    """Handwritten weights, no learned/checkpoint policy and no optimization."""

    def forward(self, features, hidden):
        assert not bool(features[..., -1].any()), "ordinary foundation phase must stay zero"
        following = 0.5 * hidden + 0.1 * features[..., :1].expand_as(hidden)
        raw = (0.7 * features[..., 104:107] + 0.6 * features[..., 3:6]
               - 0.3 * features[..., :3] + following[..., :3] + 0.01)
        return raw, following, following


class FixedCritic(torch.nn.Module):
    def forward(self, features):
        return features.sum() * 0 + 2.0


def _collect(mode="paired", tick=1, horizon=5, common_seed=101, focal_seed=102, env=None):
    counts = {}
    result = collect_pair(
        env if env is not None else CoupledFixture(7, horizon),
        freeze_foundation(FixedFeedback()), Gate("agreement", 11), FixedCritic(),
        horizon=horizon, case=FocalCase(tick, 0), mode=mode, reset_seed=77,
        common_seed=common_seed, focal_seed=focal_seed, check=lambda: None, counts=counts,
    )
    return result, counts


def test_paired_rollouts_preserve_prefix_then_follow_each_own_reactions():
    global_before = torch.get_rng_state().clone()
    result, counts = _collect()
    assert torch.equal(global_before, torch.get_rng_state())
    left, right = result["episodes"]
    assert result["eligible"]
    assert result["sampled_keep"].tolist() == [True, False]
    assert torch.equal(left["context"][:2], right["context"][:2])
    assert torch.equal(left["commands"][1, 0], left["commands"][0, 0])
    assert torch.equal(right["commands"][1, 0], right["context"][1, 0, 107:110])
    assert not left["eligible"][2, 0] and right["eligible"][2, 0]
    assert not left["keep"][2, 0]  # KEEP really forces a fresh command next tick.
    assert torch.equal(left["commands"][2, 0], left["context"][2, 0, 107:110])
    assert not torch.equal(left["context"][2:, 0, 110:174], right["context"][2:, 0, 110:174])
    assert not torch.equal(left["context"][2:, 4], right["context"][2:, 4])
    expected = torch.stack([ep["reward"][1:].sum() / 5 for ep in result["episodes"]])
    torch.testing.assert_close(result["suffix_returns"], expected, rtol=0, atol=0)
    assert result["baseline"].item() == pytest.approx(2 / 5)
    assert counts == {
        "common_uniform_values": 25, "focal_uniform_values": 2,
        "reset_calls": 2, "foundation_forward_calls": 10, "gate_forward_calls": 10,
        "critic_forward_calls": 10, "team_steps": 10, "completed_episodes": 2,
        "completed_pairs": 1, "eligible_pairs": 1,
    }


def test_ineligible_scheduled_case_is_retained_without_resampling():
    # Choose a fixture seed by inspecting RNG only, never environment outcomes.
    seed = next(s for s in range(10) if torch.rand(
        (4, 5), generator=torch.Generator().manual_seed(s)
    )[1, 0] < 0.5)
    result, counts = _collect(tick=2, horizon=4, common_seed=seed)
    assert not result["eligible"] and counts["eligible_pairs"] == 0
    assert counts["team_steps"] == 8 and counts["completed_pairs"] == 1
    for key in result["episodes"][0]:
        assert torch.equal(result["episodes"][0][key], result["episodes"][1][key])
    assert result["suffix_returns"][0] == result["suffix_returns"][1]


def test_factual_focal_draws_are_independent_and_addressed_separately():
    differing = next(s for s in range(30) if (torch.rand(
        (2,), generator=torch.Generator().manual_seed(s)
    ) < 0.5).unique().numel() == 2)
    result, counts = _collect(mode="factual", focal_seed=differing)
    assert torch.equal(result["sampled_keep"], result["focal_uniforms"] < 0.5)
    repeat, _ = _collect(mode="factual", focal_seed=differing)
    for left, right in zip(result["episodes"], repeat["episodes"]):
        for key in left:
            assert torch.equal(left[key], right[key])
    assert counts["team_steps"] == 10


def test_last_tick_keeps_its_real_credit_and_no_unobserved_suffix_is_added():
    # Horizon two makes tick one both guaranteed eligible and the final tick.
    result, counts = _collect(tick=1, horizon=2)
    expected = torch.stack([ep["reward"][-1] / 2 for ep in result["episodes"]])
    assert result["eligible"] and result["sampled_keep"].tolist() == [True, False]
    assert torch.equal(result["suffix_returns"], expected)
    assert counts["team_steps"] == 4


def test_schedule_does_not_touch_global_rng_and_rejects_reset_or_invalid_agent():
    before = np.random.get_state()
    cases = schedule(100, 256, 17)
    after = np.random.get_state()
    assert cases == schedule(100, 256, 17)
    assert before[0] == after[0] and np.array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    assert all(1 <= case.tick <= 255 and 0 <= case.agent <= 4 for case in cases)
    for case in (FocalCase(0, 0), FocalCase(256, 0), FocalCase(1, 5), FocalCase(True, 0)):
        with pytest.raises(ValueError):
            case.validate(256)


def test_different_prefix_is_a_failure_not_a_counterfactual_pair():
    class BadReset(CoupledFixture):
        def reset(self, seed=None):
            self.resets = getattr(self, "resets", 0) + 1
            return super().reset(seed=seed + self.resets)

    with pytest.raises(RuntimeError, match="prefix mismatch"):
        _collect(env=BadReset(7, 5))


def test_paired_collector_needs_no_unused_critic_but_factual_reference_does():
    arguments = dict(
        env=CoupledFixture(7, 3), foundation=freeze_foundation(FixedFeedback()),
        gate=Gate("agreement", 11), critic=None, horizon=3, case=FocalCase(1, 0),
        reset_seed=77, common_seed=101, focal_seed=102, check=lambda: None, counts={},
    )
    result = collect_pair(mode="paired", **arguments)
    assert result["eligible"] and result["baseline"].item() == 0.0
    assert "critic_forward_calls" not in arguments["counts"]
    before = dict(arguments["counts"])
    with pytest.raises(ValueError, match="pre-outcome critic"):
        collect_pair(mode="factual", **arguments)
    assert before == arguments["counts"]

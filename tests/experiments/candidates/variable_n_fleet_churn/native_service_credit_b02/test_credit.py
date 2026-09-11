"""Synthetic targets and result-reading checks: no model, RNG or environment run."""

import copy

import pytest
import torch

from experiments.candidates.variable_n_fleet_churn.native_service_credit_b02.learning import interval_rewards, gae_interval
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.training import gae_terminal, normalize_advantages
from experiments.candidates.variable_n_fleet_churn_n7_direct_b01.experiment import readout, publish_json, cost_projection


def episode():
    failed = [0, 20, 35, 60, 60, 60, 60]
    total = [0, 25, 55, 90, 130, 175, 220]
    return dict(service_counters=[[failed[j], min(j, 3) * 40, total[j], j * 60] for j in range(7)],
                fail_endpoint=[60, 120], total_endpoint=[220, 360], J_ext=.5 * 60 / 120 + .5 * 220 / 360)


def test_native_interval_endpoints_and_failure_window():
    row = episode()
    rewards = interval_rewards([row])[0]
    expected = torch.tensor([.5 * f / 120 + .5 * t / 360
                             for f, t in zip([20, 15, 25, 0, 0, 0], [25, 30, 35, 40, 45, 45])], dtype=torch.float64)
    torch.testing.assert_close(rewards, expected)
    assert abs(float(rewards.sum()) - row["J_ext"]) < 1e-9
    assert bool((rewards[3:] > 0).all())  # Total service survives the failed-zone cutoff.
    broken = copy.deepcopy(row)
    broken["service_counters"][4][0] += 1
    with pytest.raises(AssertionError):
        interval_rewards([broken])
    broken = copy.deepcopy(row)
    broken["service_counters"][0][2] = 1
    with pytest.raises(AssertionError):
        interval_rewards([broken])
    broken = copy.deepcopy(row)
    broken["total_endpoint"][1] = 350
    with pytest.raises(AssertionError):
        interval_rewards([broken])


def test_gae_keeps_terminal_null_and_distinguishes_temporal_targets():
    values = torch.tensor([[.1, -.2, .3, .4, -.5, .6], [.2, .2, .2, .2, .2, .2]],
                          dtype=torch.float64, requires_grad=True)
    rewards = interval_rewards([episode(), episode()])
    terminal = torch.zeros_like(rewards)
    terminal[:, -1] = rewards.sum(1)
    unchanged = gae_terminal(values, terminal[:, -1])
    supplied = gae_interval(values, terminal)
    for left, right in zip(unchanged, supplied):
        torch.testing.assert_close(left, right)
        assert not right.requires_grad
    advantage, target = gae_interval(values, rewards)
    # Independent expanded weighted-TD formula, including a nonzero last old value.
    next_values = torch.cat((values.detach()[:, 1:], torch.zeros((2, 1), dtype=torch.float64)), dim=1)
    deltas = rewards + next_values - values.detach()
    expanded = torch.stack([sum(.95 ** (k - j) * deltas[:, k] for k in range(j, 6))
                            for j in range(6)], dim=1)
    torch.testing.assert_close(advantage, expanded)
    torch.testing.assert_close(target, expanded + values.detach())
    assert not torch.allclose(advantage, unchanged[0])
    normalized = normalize_advantages(advantage)
    assert not torch.allclose(target, normalized + values.detach())
    assert torch.equal(normalize_advantages(torch.ones((2, 6))), torch.zeros((2, 6)))


def test_primary_round_tradeoffs_publication_and_two_arm_cost(tmp_path):
    rows = []
    for arm in ("INTERVAL", "TERMINAL", "BCRH"):
        for label in (("fixed",) if arm == "BCRH" else ("initial", "midpoint", "final")):
            for world in range(4):
                recovery = .2 + .01 * world
                if arm == "INTERVAL" and label == "midpoint":
                    recovery += .5  # A better middle checkpoint must not replace final.
                if arm == "INTERVAL" and label == "final":
                    recovery += .03 if world < 2 else -.01
                rows.append(dict(arm=arm, checkpoint=label, world=world, zone=1 + world // 2,
                                 R_fail_60=recovery, U_total=.4, U_intact=.5,
                                 J_ext=.5 * recovery + .2))
    result = readout(rows, ("INTERVAL", "TERMINAL"), .02)
    primary = next(row for row in result["contrasts"] if row["name"] == "INTERVAL_minus_TERMINAL")
    assert primary["strata"]["all"]["R_fail_60"]["mean"] == pytest.approx(.01)
    assert primary["strata"]["2"]["R_fail_60"]["mean"] == pytest.approx(-.01)
    assert result["mei_absolute"] == .02 and result["primary_checkpoint"] == "final"
    restored, _ = publish_json(tmp_path / "summary.json", result)
    assert restored == result
    arms = ("INTERVAL", "TERMINAL")
    curve = [dict(arm=arm, episodes=32, collection_seconds=3.2, update=dict(seconds=2.0)) for arm in arms]
    evaluations = [dict(arm=arm, episodes=64, seconds=6.4) for arm in arms]
    config = dict(rounds=64, eval_episodes=64, projection_cap=600)
    cost = cost_projection(config, 1., [1.], curve, evaluations, dict(episodes=64, seconds=10.),
                           1., 1., 1., arms)
    assert set(cost["per_arm"]) == set(arms)
    assert cost["cap_seconds"] == 600
    for arm in arms:
        assert cost["per_arm"][arm]["projected_seconds"] == pytest.approx(2048 * .1 + 64 * 2 + 192 * .1)

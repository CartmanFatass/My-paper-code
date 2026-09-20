"""Scalar gate information, gradient, credit and initialization checks."""

import numpy as np
import torch

from experiments.candidates.ucope.reactive_rate_b03.scalar import (
    ScalarGate,
    scalar_actor,
)
from experiments.candidates.ucope.reactive_rate_b03 import study
from experiments.candidates.ucope.reactive_renewal_b01 import reactive
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    arm_copy,
    generator,
    templates,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts


def test_scalar_gate_broadcasts_without_reading_any_input_value():
    gate = ScalarGate()
    with torch.no_grad():
        gate.logits.copy_(torch.tensor([0.75, -0.25]))
    first = torch.randn(7, 67)
    second = torch.randn(7, 67) * 1000
    expected = torch.tensor([0.75, -0.25]).expand(7, 2)
    torch.testing.assert_close(gate(first), expected, rtol=0, atol=0)
    torch.testing.assert_close(gate(second), expected, rtol=0, atol=0)
    assert gate(torch.randn(2, 3, 67)).shape == (2, 3, 2)
    assert sum(parameter.numel() for parameter in gate.parameters()) == 2


def test_eligible_gate_gradient_moves_logits_without_recurrent_gradient():
    common = templates(9921)
    actor, _ = scalar_actor(common)
    recurrent = torch.randn(5, 64, requires_grad=True)
    previous = torch.randn(5, 3)
    mean = torch.zeros(5, 3, requires_grad=True)
    eligible = torch.ones(5, dtype=torch.bool)
    branches = torch.tensor([0, 0, 0, 0, 1])
    fresh = torch.zeros(5, dtype=torch.bool)
    logp = reactive.row_log_probs(
        actor,
        mean,
        recurrent,
        previous,
        eligible,
        branches,
        torch.zeros(5, 3),
        fresh,
    )
    (-logp.sum()).backward()
    assert actor.duration.logits.grad is not None
    assert actor.duration.logits.grad.abs().sum() > 0
    assert recurrent.grad is None
    assert mean.grad is not None and not mean.grad.any()


def test_scalar_keep_timing_replay_and_terminal_credit(monkeypatch):
    torch.set_num_threads(1)
    actor, critic = scalar_actor(templates(9921))
    with torch.no_grad():
        actor.duration.logits.copy_(torch.tensor([1000.0, -1000.0]))
    counts = new_counts(renewal=True, short=True)
    episodes = []
    emitted = []
    for episode_index in range(2):
        episodes.append(
            reactive.collect_episode(
                SyntheticAdapter(19, 8),
                actor,
                critic,
                8,
                90 + episode_index,
                generator(21 + episode_index),
                generator(31 + episode_index),
                {"arm": "B", "phase": "train", "episode": episode_index},
                lambda: None,
                counts,
                emitted.append,
            )
        )
    rollout = {
        key: torch.stack([episode[key] for episode in episodes])
        for key in episodes[0]
    }
    mean, recurrent = learner.recurrent_outputs(actor, rollout, 4)
    replayed = reactive.row_log_probs(
        actor,
        mean,
        recurrent,
        rollout["previous"],
        rollout["eligible"],
        rollout["branches"],
        rollout["u"],
        rollout["fresh"],
    )
    torch.testing.assert_close(replayed, rollout["logp"], rtol=2e-5, atol=2e-6)
    assert rollout["eligible"].sum() == 40
    assert (rollout["eligible"] & ~rollout["fresh"]).sum() == 40
    assert rollout["eligible"][:, -1].all()

    targets = learner.returns_to_go(rollout["reward"])
    expected = targets - rollout["value"]
    expected = (expected - expected.mean()) / (expected.std(unbiased=False) + 1e-8)
    observed = []
    original = reactive.clipped_policy_loss

    def capture(new_logp, old_logp, advantage, mask):
        torch.testing.assert_close(advantage, expected)
        assert mask.all()
        observed.append(mask.clone())
        return original(new_logp, old_logp, advantage, mask)

    monkeypatch.setattr(reactive, "clipped_policy_loss", capture)
    reactive.update(
        actor,
        critic,
        learner.optimizer_for(actor, critic),
        episodes,
        4,
        lambda: None,
        counts,
    )
    assert len(observed) == 4
    assert counts["final_gate_credit_decisions"] == 10


def test_common_initialization_and_offpath_r_identity():
    master = 8921
    base = master * 100000
    common = templates(master)
    global_rng_before_b = torch.random.get_rng_state().clone()
    historical_r = arm_copy(
        common, True, duration_head_seed=base + 12, freeze_duration=False
    )
    selected_r = study.make_arm(common, "R", base)
    selected_b = study.make_arm(common, "B", base)
    assert torch.equal(global_rng_before_b, torch.random.get_rng_state())
    for expected, actual in zip(historical_r, selected_r):
        assert expected.state_dict().keys() == actual.state_dict().keys()
        for name, value in expected.state_dict().items():
            torch.testing.assert_close(value, actual.state_dict()[name], rtol=0, atol=0)

    r_actor, r_critic = selected_r
    b_actor, b_critic = selected_b
    for module_r, module_b in (
        (r_actor.encoder, b_actor.encoder),
        (r_actor.gru, b_actor.gru),
        (r_actor.mean, b_actor.mean),
        (r_critic, b_critic),
    ):
        for name, value in module_r.state_dict().items():
            torch.testing.assert_close(value, module_b.state_dict()[name], rtol=0, atol=0)
    torch.testing.assert_close(r_actor.log_std, b_actor.log_std, rtol=0, atol=0)
    torch.testing.assert_close(
        r_actor.duration(torch.randn(4, 67)).softmax(-1),
        torch.full((4, 2), 0.5),
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        b_actor.duration(torch.randn(4, 67)).softmax(-1),
        torch.full((4, 2), 0.5),
        rtol=0,
        atol=0,
    )
    assert sum(p.numel() for p in r_actor.duration.parameters()) == 2242
    assert sum(p.numel() for p in b_actor.duration.parameters()) == 2


def test_scalar_exposure_has_no_dormant_layers_or_zero_norm_ratio():
    actor, critic = scalar_actor(templates(9921))
    initial = study.snapshot(actor, critic)
    with torch.no_grad():
        actor.duration.logits.copy_(torch.tensor([0.2, -0.2]))
    result = study.exposure(initial, actor, critic)
    assert result["duration"]["parameters"] == 2
    assert result["duration_scalar"]["parameters"] == 2
    assert result["duration"]["initial_norm"] == 0
    assert result["duration"]["displacement"] > 0
    assert result["duration"]["relative_displacement"] is None
    assert "duration_hidden" not in result and "duration_final" not in result

import json

import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    DENSE,
    REL,
    build_pair,
    parameter_summary,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.runner import (
    prospective_native_command,
    publish_fixture,
    run_pair,
    run_fixture_pair,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss,
    update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import joint_terms


def test_parameter_match_and_common_initial_policy():
    pair = build_pair(8201)
    assert parameter_summary(pair) == {
        REL: {"actor": 69079, "branch": 2768},
        DENSE: {"actor": 69079, "branch": 2768},
    }
    assert all(torch.equal(pair[k][0].encoder.raw.weight, pair["common"][0].encoder.weight)
               for k in (REL, DENSE))
    assert all(torch.equal(pair[REL][0].branch_parameters[i],
                           torch.zeros_like(pair[REL][0].branch_parameters[i]))
               for i in (2,))
    assert all(torch.equal(pair[DENSE][0].branch_parameters[i],
                           torch.zeros_like(pair[DENSE][0].branch_parameters[i]))
               for i in (2,))
    assert torch.equal(pair[DENSE][0].encoder.hidden.bias,
                       torch.zeros_like(pair[DENSE][0].encoder.hidden.bias))
    observations = torch.randn(3, 1, 108)
    hidden = torch.zeros(1, 1, 64)
    rel_mean, rel_recurrent, _ = pair[REL][0](observations, hidden)
    dense_mean, dense_recurrent, _ = pair[DENSE][0](observations, hidden)
    assert torch.equal(rel_mean, dense_mean)
    assert torch.equal(rel_recurrent, dense_recurrent)
    assert pair[REL][0].duration is None
    assert pair[DENSE][0].duration is None


def test_relation_padding_uses_fixed_denominator():
    pair = build_pair(8201)
    encoder = pair[REL][0].encoder
    with torch.no_grad():
        encoder.raw.weight.zero_()
        encoder.raw.bias.zero_()
        encoder.user_map.weight.zero_()
        encoder.user_map.weight[0, 0] = 1.0
        encoder.context.weight.zero_()
        encoder.context.weight[0, 0] = 1.0
    observations = torch.zeros(1, 108)
    observations[0, 3] = 1.0
    output = encoder(observations)
    assert torch.allclose(output[0, 0], torch.tanh(torch.tensor(1.0)) / 20,
                          atol=1e-7, rtol=0)
    observations[0, 3] = 0.0
    assert torch.equal(encoder(observations), torch.zeros_like(output))


def test_branch_is_connected_after_projection_moves():
    pair = build_pair(8201)
    actor = pair[REL][0]
    with torch.no_grad():
        actor.encoder.context.weight[0, 0] = 1.0
    observations = torch.zeros(2, 108)
    observations[0, 3] = 1.0
    observations.requires_grad_()
    loss = actor.encoder(observations).sum()
    loss.backward()
    assert actor.encoder.context.weight.grad is not None
    assert actor.encoder.user_map.weight.grad is not None
    assert float(actor.encoder.user_map.weight.grad.abs().sum()) > 0


def test_source_agent_compound_credit_shape_is_preserved():
    pair = build_pair(8201)
    actor = pair[REL][0]
    mean, recurrent, _ = actor(torch.zeros(5, 1, 108), torch.zeros(1, 1, 64))
    mean, recurrent = mean[:, 0], recurrent[:, 0]
    actions = torch.zeros(5, 3)
    durations = torch.zeros(5, dtype=torch.long)
    mask = torch.ones(5, dtype=torch.bool)
    logp, entropy = joint_terms(actor, mean, recurrent, actions, durations, mask, mask,
                                ratio_grouping="agent_compound")
    assert logp.shape == (5,)
    assert entropy.shape == ()
    assert torch.isfinite(logp).all()
    assert torch.isfinite(entropy).all()
    new_logp = torch.zeros(2, 3, 5)
    old_logp = torch.zeros(2, 3, 5)
    advantage = torch.ones(2, 3)
    velocity_mask = torch.ones(2, 3, 5, dtype=torch.bool)
    assert clipped_policy_loss(new_logp, old_logp, advantage,
                               velocity_mask=velocity_mask).item() == -5.0


def test_rng_isolation_and_fixture_publication(tmp_path):
    torch.manual_seed(123)
    expected = torch.rand(4)
    torch.manual_seed(123)
    summary = run_fixture_pair(seed=8201, horizon=8, train_episodes=2, eval_episodes=2)
    observed = torch.rand(4)
    assert torch.equal(expected, observed)
    assert summary["status"] == "COMPLETE"
    assert summary["scientific_invocation"] is False
    assert len(summary["rows"]) == 8
    assert summary["parameter_summary"][REL]["branch"] == 2768
    assert summary["parameter_summary"][DENSE]["branch"] == 2768
    path = publish_fixture(tmp_path / "summary.json", summary)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["mode"] == "ENGINEERING_FIXTURE"
    assert loaded["scientific_invocation"] is False


def test_native_binding_is_literal_and_nonexecuting():
    command = prospective_native_command()
    assert "--native --master 8201 --output /home/wu/hmasd-worktrees/" in command
    assert "agent-task run " in command
    assert "--arm-cap 1800 --pair-cap 3600" in command
    assert "admit-memory" in command
    assert "agent-task" in command


def test_runner_fixture_reaches_publication_path(tmp_path):
    summary = run_pair(8201, tmp_path / "pair", fixture=True,
                       horizon=8, train_episodes=2, eval_episodes=2)
    assert summary["mode"] == "ENGINEERING_FIXTURE"
    assert summary["primary"]["complete"] is True
    assert summary["primary"]["hover_complete"] is True
    assert summary["scientific_invocation"] is False
    assert (tmp_path / "pair" / "summary.json").exists()

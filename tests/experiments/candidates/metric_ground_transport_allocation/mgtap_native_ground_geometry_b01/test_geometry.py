import json
import os
from pathlib import Path
import shlex
import subprocess

import pytest
import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    DENSE,
    REL,
    build_pair,
    parameter_summary,
    geometry_snapshot,
    geometry_exposure,
)
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.runner import (
    prospective_native_binding,
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
        encoder.uav_map.weight.zero_()
        encoder.uav_map.weight[0, 0] = 1.0
        encoder.context.weight.zero_()
        encoder.context.weight[0, 0] = 1.0
        encoder.context.weight[1, 20] = 1.0
    observations = torch.zeros(1, 108)
    observations[0, 3] = 1.0
    observations[0, 63] = 1.0
    output = encoder(observations)
    assert torch.allclose(output[0, 0], torch.tanh(torch.tensor(1.0)) / 20,
                          atol=1e-7, rtol=0)
    assert torch.allclose(output[0, 1], torch.tanh(torch.tensor(1.0)) / 10,
                          atol=1e-7, rtol=0)
    observations.zero_()
    assert torch.equal(encoder(observations), torch.zeros_like(output))


@pytest.mark.parametrize("kind", [REL, DENSE])
def test_branch_is_connected_after_projection_moves(kind):
    pair = build_pair(8201)
    actor, critic = pair[kind]
    initial = geometry_snapshot(actor, critic)
    observations = torch.linspace(-.7, .8, 2 * 5 * 108).reshape(2, 5, 108)
    mask = torch.ones(2, 5, dtype=torch.bool)

    def velocity_loss():
        mean, recurrent, _ = actor(observations, torch.zeros(1, 5, 64))
        logp, _ = joint_terms(actor, mean, recurrent, torch.full_like(mean, .3),
                             torch.zeros(2, 5, dtype=torch.long), mask, mask,
                             ratio_grouping="agent_compound")
        return -logp.sum(-1).mean()

    velocity_loss().backward()
    assert actor.encoder.context.weight.grad.abs().sum() > 0
    assert all(torch.count_nonzero(p.grad) == 0 for p in actor.branch_parameters[:-1])
    actor.zero_grad()
    with torch.no_grad():
        actor.encoder.context.weight.fill_(.03)
    velocity_loss().backward()
    assert all(p.grad is not None and p.grad.abs().sum() > 0 for p in actor.branch_parameters)
    movement = geometry_exposure(initial, actor, critic)
    assert movement["branch_projection"]["displacement"] > 0
    assert movement["branch_projection"]["relative_displacement"] is None
    assert movement["recurrent"]["displacement"] == movement["critic"]["displacement"] == 0


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


@pytest.mark.parametrize("master", [8201, 8202])
def test_native_binding_is_literal_and_nonexecuting(master, tmp_path):
    binding = prospective_native_binding(master, "5ce038e4aa6130be48b9cd17095470c6bde65d39")
    ssh = shlex.split(binding["command"])
    supervisor = shlex.split(ssh[2])
    assert ssh[:2] == ["ssh", "hmasd-wsl-node"]
    assert supervisor == ["/usr/local/bin/agent-task", "run", binding["handle"], "bash", binding["wrapper_path"]]
    # agent-task flattens argv and evals it once. No nested bash -lc survives that.
    assert shlex.split(" ".join(supervisor[3:])) == ["bash", binding["wrapper_path"]]
    assert "\r" not in binding["wrapper"] and "<" not in binding["wrapper"]
    assert f"--native --master {master} --output {binding['output']} --arm-cap 1800 --pair-cap 3600" in binding["wrapper"]
    assert "admit-memory" in binding["wrapper"] and " && " in binding["wrapper"]
    wrapper = tmp_path / "wrapper.sh"
    wrapper.write_bytes(binding["wrapper"].encode())
    bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe" if os.name == "nt" else Path("/bin/bash")
    subprocess.run([str(bash), "-n", str(wrapper)], check=True, timeout=10)


def test_runner_fixture_reaches_publication_path(tmp_path):
    summary = run_pair(8201, tmp_path / "pair", fixture=True,
                       horizon=8, train_episodes=2, eval_episodes=2)
    assert summary["mode"] == "ENGINEERING_FIXTURE"
    assert summary["primary"]["complete"] is True
    assert summary["primary"]["hover_complete"] is True
    assert summary["scientific_invocation"] is False
    assert summary["counts"]["rollouts"] == 2
    assert summary["counts"]["optimizer_steps"] == 8
    assert (tmp_path / "pair" / "summary.json").exists()

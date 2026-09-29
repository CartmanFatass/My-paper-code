import hashlib
import io

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_message_content.b05 import model, study
from experiments.candidates.uav_message_content.b05.channel import ForecastChannel, endpoints, packet_for
from experiments.candidates.uav_message_content.b05.collector import collect_episode
from experiments.candidates.uav_message_content import read_b05 as reader
from experiments.candidates.uav_message_content.read_b05 import contrast, longest_zero_interval, read_trace


class NativeInfoFixture(SyntheticAdapter):
    def step(self, actions):
        raw, reward, terminated, truncated, info = super().step(actions)
        connections = np.zeros((5, 50), dtype=bool)
        connections[0, :7] = True
        sinr = np.full((5, 50), 20., dtype=np.float64)
        physical = .014 * 7 + .3 * ((20 - 3) / 30)
        info["rewards_dict"] = {agent: physical / 5 for agent in AGENTS}
        for agent in AGENTS:
            info["infos_dict"][agent]["global"].update(connections=connections.copy(), sinr_matrix=sinr.copy())
        return raw, reward, terminated, truncated, info


def checkpoint(monkeypatch):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(779)
        actor, critic = BaseActor(), BaseCritic()
    content = io.BytesIO()
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm="B", master=19451,
                    input_size=171, critic_size=451, inherited_sha256=model.SOURCE_INHERITED_SHA256), content)
    value = content.getvalue()
    digest = hashlib.sha256(value).hexdigest()
    monkeypatch.setattr(model, "SOURCE_SHA256", digest)
    monkeypatch.setattr(study, "SOURCE_SHA256", digest)
    return value, digest


def test_same_history_zero_residual_and_detached_actual_rollout(monkeypatch):
    torch.set_num_threads(1)
    content, digest = checkpoint(monkeypatch)
    episodes = {}
    rows = {}
    for arm in ("M_G", "M_O"):
        actor, critic = model.build_arm(19601, arm)
        model.load_warm_start(actor, critic, content, digest)
        row = []
        episodes[arm] = collect_episode(
            NativeInfoFixture(0, 32), actor, critic, arm, 32, 84, 184, generator(284),
            dict(phase="train", episode=0), study.new_counts(), row.append,
        )
        rows[arm] = row[0]
    assert torch.equal(episodes["M_G"]["u"], episodes["M_O"]["u"])
    assert torch.equal(episodes["M_G"]["logp"], episodes["M_O"]["logp"])
    assert torch.equal(episodes["M_G"]["obs"][..., :171], episodes["M_O"]["obs"][..., :171])
    assert torch.count_nonzero(episodes["M_G"]["obs"][..., 171:]) == 0
    assert torch.count_nonzero(episodes["M_O"]["obs"][..., 171:]) > 0
    for episode in episodes.values():
        assert all(not value.requires_grad for value in episode.values())
        assert torch.equal(episode["obs"][1:, :, 104:107], episode["u"][:-1].tanh())
        assert not torch.count_nonzero(episode["obs"][0, :, 104:107])
    assert rows["M_G"]["correction_max"] == rows["M_O"]["correction_max"] == 0
    assert set(episodes["M_O"]) == {"obs", "hidden", "critic", "u", "logp", "value", "reward"}


def test_qualified_first_sample_forecast_and_expiry():
    ordinary, cv = endpoints(np.array((.99, .5, .01)), np.array((1., 0., -1.)), np.array((-1., 1., 1.)), 10)
    np.testing.assert_allclose(ordinary, (.73, .77, 1.), atol=1e-7)
    np.testing.assert_allclose(cv, (1., .5, 0.), atol=1e-7)
    terminal, _ = endpoints(np.array((.99, .5, .01)), np.array((1., 0., -1.)), np.ones(3), 1)
    np.testing.assert_array_equal(terminal, (1., .5, 0.))
    channel = ForecastChannel(17, 32)
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[:, :3] = .4
    for t in range(32):
        channel.begin_tick()
        if t == 0:
            charge, due = channel.resolve_payload(0, packet_for(raw, 0, np.array((.2, .3, .4))))
            assert charge == .001 and due in (1, 5)
        if t == 10:
            assert not np.any(channel.forecasts)
            assert channel.records[1, 0, 7] == 1
        channel.advance()
    assert channel.accepted == channel.delivered == 1


@pytest.mark.parametrize("arm", ("B40", "M_G", "M_O"))
def test_full_writer_reader_composition_and_native_metrics(tmp_path, monkeypatch, arm):
    torch.set_num_threads(1)
    content, digest = checkpoint(monkeypatch)
    if arm == "B40":
        actor, critic = model.load_base(content, digest)
    else:
        actor, critic = model.build_arm(19601, arm)
        model.load_warm_start(actor, critic, content, digest)
        with torch.no_grad():
            actor.residual_output.weight.fill_(.03)
            actor.residual_output.bias.fill_(.01)
    before = {key: value.clone() for key, value in actor.state_dict().items()}
    counts, rows = study.new_counts(), []
    collect_episode(
        NativeInfoFixture(0, 256), actor, critic, arm, 256, 1960002000, 1960007000, generator(1960003000),
        dict(phase="final_eval", arm=arm, master=19451 if arm == "B40" else 19601,
             episode=0, motion_seed=1960003000), counts, rows.append, raw_path=tmp_path / "final.npz",
    )
    result = read_trace(rows[0], arm)
    assert result["levels"]["J_net"] == pytest.approx(.267)
    assert result["levels"]["zero_service_steps"] == result["levels"]["longest_zero_service"] == 0
    assert result["density_max_abs_error"] < 1e-5
    assert counts["behavior_critic_forward_calls"] == counts["evaluation_optimizer_steps"] == 0
    assert counts["diagnostic_forward_calls"] == (256 if arm == "M_O" else 0)
    assert all(torch.equal(before[key], value) for key, value in actor.state_dict().items())
    with np.load(rows[0]["raw"]) as data:
        np.testing.assert_array_equal(data["connected_users"].sum(1), data["served_users"])
        assert data["packet"].shape == (256, 10)
        if arm != "B40":
            assert result["residual"]["correction_rms"] > 0
        if arm == "M_O":
            assert result["response_rms"] > 0
        else:
            assert not np.any(data["packet"][:, 7:])


def test_miniature_fixed_batch_counts_and_parameter_invariants(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    content, digest = checkpoint(monkeypatch)
    source = tmp_path / "parent.pt"
    source.write_bytes(content)
    result = study.run_batch(tmp_path / "batch", "synthetic-source", source, digest,
                             factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=1)
    assert result["status"] == "COMPLETE", result
    assert result["actual"]["fit_started"] == 6
    assert result["actual"]["team_steps"] == 608
    assert result["actual"]["optimizer_steps"] == result["actual"]["actor_optimizer_steps"] == result["actual"]["critic_optimizer_steps"] == 24
    assert result["actual"]["behavior_critic_forward_calls"] == 384
    assert result["actual"]["diagnostic_forward_calls"] == 96
    initial_by_master = {}
    monkeypatch.setattr(reader, "BOUND_SHA", digest)
    _, parent = reader.checkpoint_arrays(source)
    for cell in result["cells"]:
        assert cell["exposure"]["base_actor"]["displacement"] == 0
        assert cell["exposure"]["residual_output"]["displacement"] > 0
        assert cell["after_eval_tensor_sha256"] == cell["final_tensor_sha256"]
        master = cell["master"]
        if master in initial_by_master:
            assert initial_by_master[master] == cell["initial_tensor_sha256"]
        initial_by_master[master] = cell["initial_tensor_sha256"]
        assert reader.read_checkpoints(cell, parent)["base_matches_canonical"]
        assert reader.read_updates(cell)["ppo_records"] == 4
    assert result["b40"]["initial_base_sha256"] == result["cells"][0]["initial_tensor_sha256"]["base_actor"]
    with pytest.raises(FileExistsError):
        study.run_batch(tmp_path / "batch", "synthetic-source", source, digest,
                         factory=lambda seed: NativeInfoFixture(seed, 32), horizon=32, train=2, evaluation=1)


def test_training_unit_and_service_tail_readers():
    first = {master: [dict(J_net=float(index + block)) for index in range(32)]
             for block, master in enumerate((19601, 19602, 19603))}
    second = {master: [dict(J_net=float(index)) for index in range(32)] for master in first}
    result = contrast(first, second, "J_net")
    assert result["per_continuation_mean"] == [0., 1., 2.]
    assert result["conditional_training"]["df"] == 2
    assert result["deployment_average_over_blocks"]["df"] == 31
    assert result["mean"] == 1
    assert longest_zero_interval([0, 0, 1, 0, 0, 0]) == 3
    assert longest_zero_interval([0] * 256) == 256
    assert longest_zero_interval([1] * 256) == 0

import hashlib
import io

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import AGENTS, SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import optimizer_for
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_message_content.b04 import model
from experiments.candidates.uav_message_content.b04.channel import ForecastChannel, packet_for
from experiments.candidates.uav_message_content.b04.learner import (
    cache_timing, collect_episode, update_motion, update_predictor,
)
from experiments.candidates.uav_message_content.b04 import study
from experiments.candidates.uav_message_content.b04.study import new_counts


class NativeInfoFixture(SyntheticAdapter):
    def reset(self, seed=None):
        raw, info = super().reset(seed)
        self.trajectory = [raw[:, :3].copy()]
        return raw, info

    def step(self, actions):
        raw, reward, terminated, truncated, info = super().step(actions)
        self.trajectory.append(raw[:, :3].copy())
        connections = np.zeros((5, 50), dtype=bool)
        connections[0, :7] = True
        sinr = np.full((5, 50), 20, dtype=np.float64)
        physical = .014 * 7 + .3 * ((20 - 3) / 30)
        info["rewards_dict"] = {agent: physical / 5 for agent in AGENTS}
        for agent in AGENTS:
            info["infos_dict"][agent]["global"].update(
                connections=connections.copy(), sinr_matrix=sinr.copy())
        return raw, reward, terminated, truncated, info


def _checkpoint():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(779)
        actor, critic = BaseActor(), BaseCritic()
    stream = io.BytesIO()
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                    arm="B", master=19451, input_size=171, critic_size=451,
                    inherited_sha256=model.SOURCE_INHERITED_SHA256), stream)
    return actor, critic, stream.getvalue()


def test_warm_start_digest_metadata_and_exact_old_sequence(monkeypatch):
    old_actor, old_critic, checkpoint = _checkpoint()
    digest = hashlib.sha256(checkpoint).hexdigest()
    monkeypatch.setattr(model, "SOURCE_SHA256", digest)
    actor, critic, _ = model.build_arm(19501, "F")
    model.load_warm_start(actor, critic, checkpoint, digest)
    with pytest.raises(ValueError, match="digest"):
        model.load_warm_start(actor, critic, checkpoint + b"x", digest)
    invalid = io.BytesIO()
    state = torch.load(io.BytesIO(checkpoint), weights_only=True)
    state["master"] = 19452
    torch.save(state, invalid)
    bad = invalid.getvalue()
    monkeypatch.setattr(model, "SOURCE_SHA256", hashlib.sha256(bad).hexdigest())
    with pytest.raises(ValueError, match="metadata"):
        model.load_warm_start(actor, critic, bad, hashlib.sha256(bad).hexdigest())
    rng = np.random.default_rng(5)
    x = torch.from_numpy(rng.normal(size=(37, 5, 171)).astype(np.float32))
    tail = torch.from_numpy(rng.normal(size=(37, 5, 15)).astype(np.float32))
    h = torch.from_numpy(rng.normal(size=(1, 5, 64)).astype(np.float32))
    new, rec, hn = actor(torch.cat((x, tail), -1), h)
    original, old_rec, old_hn = old_actor(x, h)
    assert torch.equal(new, original)
    assert torch.equal(rec, old_rec)
    assert torch.equal(hn, old_hn)
    cx = torch.from_numpy(rng.normal(size=(13, 451)).astype(np.float32))
    ct = torch.from_numpy(rng.normal(size=(13, 75)).astype(np.float32))
    assert torch.equal(critic(torch.cat((cx, ct), -1)), old_critic(cx))


def test_first_sample_then_central_and_reachable_bounds():
    p = torch.tensor((.99, .5, .01))
    sampled = torch.tensor((1., 0., -1.))
    central = torch.tensor((-1., 1., 1.))
    first, ordinary, cv, predicted = model.endpoints(p, sampled, central, 10)
    assert torch.allclose(first, torch.tensor((1., .5, 0.)))
    assert torch.allclose(ordinary, torch.tensor((.73, .77, 1.)))
    assert torch.allclose(cv, torch.tensor((1., .5, 0.)))
    assert torch.equal(predicted, ordinary)
    _, _, _, high = model.endpoints(p, sampled, central, 10, torch.full((3,), 100.))
    lower = torch.clamp(first - 9 * torch.as_tensor(model.D), min=0)
    upper = torch.clamp(first + 9 * torch.as_tensor(model.D), max=1)
    assert torch.all(high >= lower) and torch.all(high <= upper)
    _, last, _, last_f = model.endpoints(p, sampled, central, 1, torch.ones(3))
    assert torch.equal(last, first) and torch.equal(last_f, first)


def test_packet_transport_and_terminal_expiry():
    channel = ForecastChannel(17, horizon=32)
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[:, :3] = .4
    first_good = channel.good
    for t in range(32):
        before = channel.delivered
        channel.begin_tick()
        assert channel.delivered >= before
        base, tail = channel.features_with_tail()
        assert base.shape == (5, 63) and tail.shape == (5, 15)
        assert channel.records.shape == (5, 5, 10)
        if t == 0:
            packet = packet_for(raw, 0, np.array((.2, .3, .4)))
            assert packet.shape == (10,) and packet[5] == 0
            cost, due = channel.resolve_payload(0, packet)
            assert cost == .001 and due == (1 if first_good else 5)
        channel.advance()
    assert channel.attempts == 1
    age, lead = cache_timing(channel.records, 31, 32)
    assert np.all(lead[age >= 10] == 0)
    assert np.all(channel.forecasts == 0)


def test_detached_labels_updates_rng_and_eval_telemetry(tmp_path):
    torch.set_num_threads(1)
    before_rng = torch.random.get_rng_state().clone()
    o_actor, o_critic, _ = model.build_arm(19501, "O")
    f_actor, f_critic, predictor = model.build_arm(19501, "F")
    assert torch.equal(torch.random.get_rng_state(), before_rng)
    assert all(torch.equal(a, b) for a, b in zip(o_actor.parameters(), f_actor.parameters()))
    assert all(torch.equal(a, b) for a, b in zip(o_critic.parameters(), f_critic.parameters()))
    assert all(torch.count_nonzero(p) == 0 for p in predictor.output.parameters())
    rows_o, rows_f = [], []
    counts_o, counts_f = new_counts(), new_counts()
    episodes, labels = [], []
    for e in range(2):
        o_episode, _ = collect_episode(NativeInfoFixture(0, 32), o_actor, o_critic, None,
            "O", 32, 80 + e, 180 + e, generator(999),
            dict(phase="train", episode=e), counts_o, rows_o.append, lambda: None)
        f_env = NativeInfoFixture(0, 32)
        f_episode, f_labels = collect_episode(f_env, f_actor, f_critic,
            predictor, "F", 32, 80 + e, 180 + e, generator(999),
            dict(phase="train", episode=e), counts_f, rows_f.append, lambda: None)
        assert torch.equal(o_episode["u"], f_episode["u"])
        assert torch.equal(o_episode["obs"][..., :171], f_episode["obs"][..., :171])
        assert torch.equal(o_episode["obs"][..., 171:], f_episode["obs"][..., 171:])
        assert torch.equal(o_episode["logp"], f_episode["logp"])
        assert all(not value.requires_grad for value in f_labels.values())
        channel = ForecastChannel(180 + e, 32)
        eligible = []
        for t in range(32):
            channel.begin_tick()
            sender = t % 5
            k = min(10, 32 - t)
            _, due = channel.resolve_payload(sender, packet_for(
                np.zeros((5, 104), dtype=np.float32), sender, np.zeros(3)))
            if due < 32:
                eligible.append((t, sender, k))
            channel.advance()
        assert len(f_labels["context"]) == len(eligible)
        for i, (sent, sender, k) in enumerate(eligible):
            assert torch.equal(f_labels["target"][i],
                               torch.from_numpy(f_env.trajectory[sent + k][sender]))
            assert int(f_labels["horizon"][i]) == k
            assert torch.equal(f_labels["context"][i, 64:67],
                               torch.from_numpy(f_env.trajectory[sent][sender]))
        episodes.append(f_episode)
        labels.append(f_labels)
    old_predictor = [p.detach().clone() for p in predictor.parameters()]
    old_actor = [p.detach().clone() for p in f_actor.parameters()]
    update_predictor(predictor, torch.optim.Adam(predictor.parameters(), lr=3e-4),
                     labels, counts_f, lambda: None)
    assert counts_f["predictor_updates"] == 4
    assert counts_f["predictor_rows"] == 4 * counts_f["eligible_labels"]
    assert any(not torch.equal(a, b) for a, b in zip(old_predictor, predictor.parameters()))
    assert all(torch.equal(a, b) for a, b in zip(old_actor, f_actor.parameters()))
    update_motion(f_actor, f_critic, optimizer_for(f_actor, f_critic), episodes,
                  counts_f, lambda: None)
    assert counts_f["optimizer_steps"] == 4
    assert counts_f["replayed_actor_rows"] == 4 * 2 * 32 * 5
    before_eval = [p.detach().clone() for p in f_actor.parameters()]
    eval_rows = []
    raw_path = tmp_path / "final.npz"
    collect_episode(NativeInfoFixture(0, 32), f_actor, f_critic, predictor, "F", 32,
                    90, 190, generator(1090), dict(phase="final_eval", episode=0),
                    counts_f, eval_rows.append, lambda: None, raw_path=raw_path)
    assert counts_f["evaluation_optimizer_steps"] == 0
    assert all(torch.equal(a, b) for a, b in zip(before_eval, f_actor.parameters()))
    assert counts_f["diagnostic_forward_calls"] == 32
    with np.load(raw_path) as data:
        assert data["connected_users"].shape == (32, 50)
        assert np.all(data["connected_users"].sum(1) == data["served_users"])
        assert data["position"].shape == (33, 5, 3)
        assert data["initial_state"].shape == (116,)
        assert data["records"].shape == (32, 5, 5, 13)
        assert np.all(np.isfinite(data["shadow_central_motion"]))
        assert np.all(data["cache_remaining_lead"] >= 0)


def test_synthetic_batch_count_and_panel_contract(tmp_path, monkeypatch):
    _, _, checkpoint = _checkpoint()
    digest = hashlib.sha256(checkpoint).hexdigest()
    monkeypatch.setattr(model, "SOURCE_SHA256", digest)
    monkeypatch.setattr(study, "SOURCE_SHA256", digest)
    source = tmp_path / "B19451.pt"
    source.write_bytes(checkpoint)
    result = study.run_batch(tmp_path / "batch", "synthetic-sha", source, digest,
                             factory=lambda seed: NativeInfoFixture(seed, 32),
                             horizon=32, train=2, evaluation=1)
    assert result["status"] == "COMPLETE", result.get("limits", result.get("reduction"))
    assert result["reduction"]["complete"]
    assert [(c["master"], c["arm"]) for c in result["cells"]] == [
        (m, a) for m in study.MASTERS for a in study.ARMS]
    assert result["actual"]["native_step_calls"] == 9 * 3 * 32 + 32
    assert result["actual"]["predictor_updates"] == 3 * 4
    assert result["actual"]["optimizer_steps"] == 9 * 4
    assert result["actual"]["diagnostic_forward_calls"] == 6 * 32
    assert result["b0"]["counts"]["evaluation_optimizer_steps"] == 0
    with np.load(result["cells"][0]["rows"][0]["raw"]) as data:
        assert np.all(data["ordinary_endpoint"] == 0)
        assert np.all(data["sampled_cv_endpoint"] == 0)
        assert np.all(data["forecast_endpoint"] == 0)


@pytest.mark.parametrize("arm", ("G", "O", "F", "B0"))
def test_independent_reader_reconstructs_full_episode(tmp_path, arm):
    from experiments.candidates.uav_message_content.read_b04 import read_trace

    torch.set_num_threads(1)
    if arm == "B0":
        actor, critic, _ = _checkpoint()
        predictor = None
    else:
        actor, critic, predictor = model.build_arm(19501, arm)
    rows, counts = [], new_counts()
    raw_path = tmp_path / f"{arm}.npz"
    collect_episode(NativeInfoFixture(0, 256), actor, critic, predictor, arm, 256,
                    1950002000, 1950007000, generator(1950003000),
                    dict(phase="final_eval", arm=arm, master=19451 if arm == "B0" else 19501,
                         episode=0, motion_seed=1950003000), counts, rows.append,
                    lambda: None, raw_path=raw_path)
    reading = read_trace(rows[0], arm)
    assert reading["delivered"] + reading["censored"] == 256
    assert reading["connected_bits_bytes"] == 256 * 50
    assert reading["levels"]["J_net"] == pytest.approx(.267)
    assert counts["evaluation_optimizer_steps"] == 0

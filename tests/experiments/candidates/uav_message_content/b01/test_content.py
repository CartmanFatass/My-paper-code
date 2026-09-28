import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.uav_message_content.b01 import learner as content_learner
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import payloads
from experiments.candidates.uav_message_content.b01.channel import ContentChannel, Sightings, hand_payload
from experiments.candidates.uav_message_content.b01.learner import (
    collect_episode, content_can_affect_later_action, native_service, update,
)
from experiments.candidates.uav_message_content.b01.model import (
    action_terms, build_arm, sample_content, snapshot,
)
from experiments.candidates.uav_message_content.b01.study import new_counts, reduction, run_arm
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import optimizer_for
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, tanh_log_prob


TECH_MASTER = 99123


def test_payloads_moments_and_seven_float_budget():
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[0, :3] = (.4, .5, .2)
    raw[0, 3:9] = (.1, .2, .4, -.1, -.2, .4)
    sightings = Sightings()
    sightings.observe(raw)
    assert np.array_equal(hand_payload("C", raw, 0, sightings), payloads(raw)[0])
    first = sightings.payload(raw, 0)
    assert first.shape == (7,) and first.dtype == np.float32
    assert first[3:5] == pytest.approx([.4, .5])
    assert first[5] == pytest.approx(math.sqrt(.05 / 2))
    assert first[6] == pytest.approx(.1)
    raw[0, 3:63] = 0
    sightings.observe(raw)
    assert sightings.payload(raw, 0)[6] == pytest.approx(.05)
    for _ in range(5):
        sightings.observe(raw)
    assert np.array_equal(sightings.payload(raw, 0)[3:], np.zeros(4))
    assert sightings.payload(raw, 0)[6] == 0
    assert len(Sightings().history[0]) == 0


def test_fixed_rr_delivery_fee_and_terminal_mask():
    channel = ContentChannel(TECH_MASTER)
    packet = np.arange(7, dtype=np.float32) / 7
    channel.good = True
    fee, due = channel.resolve_payload(0, packet)
    assert fee == .001 and due == 1 and channel.accepted == 1
    channel.advance()
    channel.begin_tick()
    assert channel.delivered == 1
    assert np.array_equal(channel.records[1, 0, :7], packet)
    assert channel.records[0, 0, 7] == 0
    assert content_can_affect_later_action(254, 1, 256)
    assert not content_can_affect_later_action(255, 1, 256)
    assert not content_can_affect_later_action(251, 5, 256)
    channel.t = 255
    channel.pending[:] = False
    channel.good = False
    _, due = channel.resolve_payload(0, packet)
    assert due == 260 and channel.accepted == 2
    with pytest.raises(ValueError):
        channel.resolve_payload(1, np.ones(8))


def test_compound_density_gaussian_entropy_and_private_stream():
    actor, critic = build_arm(TECH_MASTER, "L")
    plain, plain_critic = build_arm(TECH_MASTER, "C")
    assert torch.equal(snapshot(actor, critic)["motion_receiver"],
                       snapshot(plain, plain_critic)["motion_receiver"])
    assert torch.equal(snapshot(actor, critic)["critic"],
                       snapshot(plain, plain_critic)["critic"])
    assert actor.content.weight.shape == (7, 64)
    assert sum(p.numel() for p in actor.content.parameters()) + actor.content_log_std.numel() == 462
    mean = torch.zeros(1, 5, 3)
    recurrent = torch.zeros(1, 5, 64)
    motion = torch.full((1, 5, 3), .25)
    content = torch.zeros(1, 5, 7)
    content[0, 2] = torch.tensor([.4] * 7)
    mask = torch.zeros(1, 5, dtype=torch.bool)
    mask[0, 2] = True
    logp, entropy = action_terms(actor, mean, recurrent, motion, content, mask)
    motion_lp = tanh_log_prob(motion, mean, actor.log_std)
    message_lp = tanh_log_prob(content, actor.content(recurrent), actor.content_log_std)
    assert torch.allclose(logp, motion_lp + torch.where(mask, message_lp, 0))
    gaussian = .5 * math.log(2 * math.pi * math.e)
    assert float(entropy) == pytest.approx(5 * 3 * gaussian + 7 * gaussian)
    assert float(entropy) != pytest.approx(5 * 3 * gaussian + 7 * gaussian - float(content[0, 2].tanh().abs().sum()))
    mask.zero_()
    _, censored_entropy = action_terms(actor, mean, recurrent, motion, content, mask)
    assert float(censored_entropy) == pytest.approx(5 * 3 * gaussian)
    motion_rng = generator(TECH_MASTER + 1)
    control_rng = generator(TECH_MASTER + 1)
    content_rng = generator(TECH_MASTER + 2)
    first_motion = torch.randn(3, generator=motion_rng)
    sample_content(actor, recurrent[0], 2, content_rng)
    second_motion = torch.randn(3, generator=motion_rng)
    assert torch.equal(first_motion, torch.randn(3, generator=control_rng))
    assert torch.equal(second_motion, torch.randn(3, generator=control_rng))


def test_delayed_team_return_reaches_content_head():
    actor, _ = build_arm(TECH_MASTER, "L")
    recurrent = torch.zeros(1, 5, 64)
    recurrent[0, 0, 0] = 1
    content = torch.zeros(1, 5, 7)
    content[0, 0] = torch.tensor([.2] * 7)
    mask = torch.zeros(1, 5, dtype=torch.bool)
    mask[0, 0] = True
    # A reward after the one-tick arrival contributes to the send-time return.
    reward = torch.tensor([[0., 1.]])
    send_return = reward.flip(-1).cumsum(-1).flip(-1)[0, 0]
    logp, _ = action_terms(actor, torch.zeros(1, 5, 3), recurrent,
                           torch.zeros(1, 5, 3), content, mask)
    (-logp[0, 0] * send_return).backward()
    assert actor.content.weight.grad is not None
    assert float(actor.content.weight.grad.abs().sum()) > 0
    assert actor.content_log_std.grad is not None


def test_short_synthetic_fit_replay_and_eval_isolation(tmp_path):
    actor, critic = build_arm(TECH_MASTER, "L")
    counts = new_counts()
    env = SyntheticAdapter(TECH_MASTER, horizon=32)
    rows = []
    motion_rng, content_rng = generator(TECH_MASTER + 21), generator(TECH_MASTER + 22)
    episodes = []
    for e in range(2):
        episodes.append(collect_episode(env, actor, critic, "L", 32,
            TECH_MASTER + 1000 + e, TECH_MASTER + 6000 + e,
            motion_rng, content_rng, dict(arm="L", master=TECH_MASTER, phase="train", episode=e),
            counts, rows.append, lambda: None))
    before = snapshot(actor, critic)["content_head"]
    records = update(actor, critic, optimizer_for(actor, critic), episodes, counts, lambda: None)
    assert len(records) == 4 and counts["optimizer_steps"] == 4
    assert counts["replayed_actor_rows"] == 2 * 32 * 5 * 4
    assert any(row["grad_groups"]["content_head"] > 0 for row in records)
    assert not torch.equal(before, snapshot(actor, critic)["content_head"])
    training_state = motion_rng.get_state().clone(), content_rng.get_state().clone()
    collect_episode(env, actor, critic, "L", 32, TECH_MASTER + 2000,
        TECH_MASTER + 7000, generator(TECH_MASTER + 3000), generator(TECH_MASTER + 4000),
        dict(arm="L", master=TECH_MASTER, phase="final_eval", episode=0),
        counts, rows.append, lambda: None, tmp_path / "eval.npz")
    assert torch.equal(training_state[0], motion_rng.get_state())
    assert torch.equal(training_state[1], content_rng.get_state())
    assert counts["evaluation_optimizer_steps"] == 0
    with np.load(tmp_path / "eval.npz") as data:
        assert data["actor_input"].shape == (32, 5, 171)
        assert data["packet"].shape == (32, 7)
        assert data["action"].shape == (32, 5, 3)
        due = int(data["due"][0])
        assert due < 32
        assert np.array_equal(data["actor_input"][due, 1, 121:128], data["packet"][0])
        np.testing.assert_allclose(data["packet"][0], np.tanh(data["pre_tanh_content"][0]),
                                   rtol=1e-6, atol=1e-7)


def test_replay_keeps_behavior_packets_after_head_change(monkeypatch):
    actor, critic = build_arm(TECH_MASTER, "L")
    env = SyntheticAdapter(TECH_MASTER, horizon=32)
    counts = new_counts()
    motion_rng, content_rng = generator(TECH_MASTER + 21), generator(TECH_MASTER + 22)
    episodes = [collect_episode(env, actor, critic, "L", 32,
        TECH_MASTER + 1000 + e, TECH_MASTER + 6000 + e, motion_rng, content_rng,
        dict(arm="L", master=TECH_MASTER, phase="train", episode=e),
        counts, lambda row: None, lambda: None) for e in range(2)]
    behavior_obs = torch.stack([episode["obs"] for episode in episodes])
    rollout = {key: torch.stack([episode[key] for episode in episodes]) for key in episodes[0]}
    old_logp = rollout["logp"].clone()
    for e, episode in enumerate(episodes):
        channel = ContentChannel(TECH_MASTER + 6000 + e)
        due = 1 if channel.good else 5
        assert torch.equal(episode["obs"][due, 1, 121:128],
                           episode["content_u"][0, 0].tanh())

    with torch.no_grad():
        actor.content.bias.fill_(2.0)
        mean, recurrent = recurrent_outputs(actor, rollout, 32)
        current_logp, _ = action_terms(actor, mean, recurrent, rollout["u"],
                                       rollout["content_u"], rollout["content_mask"])
    mask = rollout["content_mask"]
    assert torch.any((current_logp[mask] - old_logp[mask]).abs() > 1e-4)
    assert torch.allclose(current_logp[~mask], old_logp[~mask])

    def forbid_draw(*args, **kwargs):
        pytest.fail("replay must not sample or encode a new behavior packet")

    monkeypatch.setattr(content_learner, "sample_content", forbid_draw)
    monkeypatch.setattr(content_learner, "sample_actions", forbid_draw)
    captured_inputs, recomputed = [], []
    hook = actor.register_forward_pre_hook(
        lambda module, inputs: captured_inputs.append(inputs[0].detach().clone()))
    original_terms = content_learner.action_terms

    def capture_terms(*args):
        logp, entropy = original_terms(*args)
        recomputed.append(logp.detach().clone())
        return logp, entropy

    monkeypatch.setattr(content_learner, "action_terms", capture_terms)
    try:
        update(actor, critic, optimizer_for(actor, critic), episodes, counts, lambda: None)
    finally:
        hook.remove()
    expected_input = behavior_obs.permute(1, 0, 2, 3).reshape(32, 10, 171)
    assert len(captured_inputs) == len(recomputed) == 4
    assert all(torch.equal(value, expected_input) for value in captured_inputs)
    assert torch.allclose(recomputed[0], current_logp)
    assert torch.equal(behavior_obs, torch.stack([episode["obs"] for episode in episodes]))


def test_small_full_lifecycle_and_failure_frontier(tmp_path):
    def factory(seed):
        return SyntheticAdapter(seed, horizon=32)

    summaries = [run_arm(TECH_MASTER, arm, tmp_path / arm, factory=factory,
                         horizon=32, train=2, evaluation=1) for arm in ("C", "H", "L")]
    result = summaries[2]
    assert result["status"] == "COMPLETE"
    assert result["counts"]["fit_started"] == 1
    assert result["counts"]["team_steps"] == 128
    assert result["counts"]["optimizer_steps"] == 4
    assert result["counts"]["evaluation_optimizer_steps"] == 0
    assert (tmp_path / "L" / "initial.pt").exists()
    assert (tmp_path / "L" / "final.pt").exists()
    assert len(list((tmp_path / "L" / "raw").glob("*.npz"))) == 2
    assert reduction(summaries, expected=1, horizon=32, train=2)["complete"]

    calls = 0
    def stop():
        nonlocal calls
        calls += 1
        if calls > 12:
            raise RuntimeError("technical stop")

    partial = run_arm(TECH_MASTER, "C", tmp_path / "partial", factory=factory,
                      horizon=32, train=2, evaluation=1, check=stop)
    assert partial["status"] == "INCOMPLETE"
    assert "technical stop" in partial["limits"][0]
    assert partial["counts"]["team_steps"] > 0
    assert (tmp_path / "partial" / "summary.json").exists()


def test_cli_rejects_unadmitted_invocation_before_output(tmp_path):
    runner = Path(__file__).resolve().parents[5] / "experiments/candidates/uav_message_content/b01/run.py"
    for extra in ([], ["--seed", "19432"]):
        output = tmp_path / ("bad_seed" if extra else "no_admission")
        completed = subprocess.run([sys.executable, str(runner), "--out", str(output),
                                    "--launch-sha", "0" * 40, *extra],
                                   capture_output=True, text=True, check=False)
        assert completed.returncode != 0
        assert not output.exists()


def test_reduction_adverse_and_missingness():
    rows = []
    for arm, score in (("C", .2), ("H", .1), ("L", .05)):
        item = dict(arm=arm, status="COMPLETE", master=TECH_MASTER, counts=new_counts(),
                    initial_tensor_sha256={"motion_receiver": "same", "critic": "same"}, rows=[])
        item["counts"].update(train_episodes=2, initial_eval_episodes=1, final_eval_episodes=1,
            train_team_steps=64, initial_eval_team_steps=32, final_eval_team_steps=32,
            fit_started=1, optimizer_steps=4, rollouts=1, replayed_actor_rows=1280,
            broadcasts=128, attempts=128, team_steps=128, motion_samples=640,
            content_samples=128 if arm == "L" else 0,
            delivered_packets=124, censored_packets=4)
        for phase, length in (("train", 2), ("initial_eval", 1), ("final_eval", 1)):
            for episode in range(length):
                item["rows"].append(dict(phase=phase, episode=episode,
                reset_seed=episode+1, channel_seed=episode+2, steps=32,
                initial_scene_sha256="scene", channel_sequence_sha256="channel",
                J_net=score, J_physical=score+.001, served_users_per_tick=score*50,
                Q=score, charge_per_tick=.001, attempts=32, accepted_packets=32,
                collided_attempts=0, delivered_packets=31, pending_at_end=1))
        rows.append(item)
    answer = reduction(rows, expected=1, horizon=32, train=2)
    assert answer["complete"]
    assert answer["comparisons"]["L-C"]["final_eval"]["J_net"]["adverse"] == 1
    assert answer["comparisons"]["L-C"]["final_eval"]["J_net"]["worst_loss"] == pytest.approx(-.15)
    rows[2]["counts"]["optimizer_steps"] = 3
    assert reduction(rows, expected=1, horizon=32, train=2)["reading"] == "INCOMPLETE"


def test_native_one_step_service_and_output(tmp_path):
    env = make_real(TECH_MASTER + 1000)
    actor, critic = build_arm(TECH_MASTER, "C")
    rows, counts = [], new_counts()
    collect_episode(env, actor, critic, "C", 1, TECH_MASTER + 2000,
        TECH_MASTER + 7000, generator(TECH_MASTER + 3000), generator(TECH_MASTER + 4000),
        dict(arm="C", master=TECH_MASTER, phase="initial_eval", episode=0),
        counts, rows.append, lambda: None, tmp_path / "native.npz")
    assert counts["native_step_calls"] == counts["team_steps"] == 1
    assert rows[0]["Q"] is not None
    assert rows[0]["J_physical"] == pytest.approx(.7 * rows[0]["served_users_per_tick"] / 50 + .3 * rows[0]["Q"])

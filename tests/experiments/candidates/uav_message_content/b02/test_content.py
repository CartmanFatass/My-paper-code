import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import payloads
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import build_arm as build_cadc
from experiments.candidates.uav_message_content.b02 import learner as content_learner
from experiments.candidates.uav_message_content.b02.channel import ContentChannel, Sightings, hand_payload
from experiments.candidates.uav_message_content.b02.learner import (
    collect_episode, content_can_affect_later_action, update,
)
from experiments.candidates.uav_message_content.b02.model import (
    SCALAR_ACTOR_COLUMNS, SCALAR_CRITIC_COLUMNS, action_terms, build_arm,
    load_warm_start, sample_content, snapshot,
)
from experiments.candidates.uav_message_content.b02.study import (
    ARMS, MASTERS, new_counts, run_arm, run_batch, validate_cells,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import optimizer_for, recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, tanh_log_prob


def checkpoint(tmp_path):
    actor, critic = build_cadc(19431, "RR")
    with torch.no_grad():
        actor.encoder.context.weight.fill_(.01)
    state = dict(actor=actor.state_dict(), critic=critic.state_dict(), arm="C",
                 master=19431, input_size=171, critic_size=451)
    buffer = io.BytesIO()
    torch.save(state, buffer)
    data = buffer.getvalue()
    path = tmp_path / "source.pt"
    path.write_bytes(data)
    return path, data, hashlib.sha256(data).hexdigest(), actor, critic


def test_packet_fields_spread_and_channel():
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[0, :3] = (.4, .5, .2)
    raw[0, 3:9] = (.1, .2, .4, -.1, -.2, .4)
    sightings = Sightings()
    sightings.observe(raw)
    base = payloads(raw)[0]
    assert np.array_equal(hand_payload("B", raw, 0, sightings), base)
    ordinary = hand_payload("O", raw, 0, sightings)
    assert np.array_equal(ordinary[[0, 1, 2, 3, 4, 6]], base[[0, 1, 2, 3, 4, 6]])
    assert ordinary[5] == pytest.approx(math.sqrt(.1))
    learned = hand_payload("L", raw, 0, sightings, .37)
    assert np.array_equal(learned[[0, 1, 2, 3, 4, 6]], base[[0, 1, 2, 3, 4, 6]])
    assert learned[5] == pytest.approx(.37)
    raw[0, 3:63] = 0
    for _ in range(5):
        sightings.observe(raw)
    assert sightings.spread(0) == 0
    assert Sightings().spread(0) == 0
    channel = ContentChannel(191)
    channel.good = True
    fee, due = channel.resolve_payload(0, learned)
    assert (fee, due) == (.001, 1)
    channel.advance()
    channel.begin_tick()
    np.testing.assert_array_equal(channel.records[1, 0, :7], learned)
    assert content_can_affect_later_action(254, 1, 256)
    assert not content_can_affect_later_action(255, 1, 256)
    assert not content_can_affect_later_action(251, 5, 256)


def test_digest_metadata_initial_function_and_zeroed_column_gradients(tmp_path):
    _, data, digest, old_actor, old_critic = checkpoint(tmp_path)
    actors = []
    for arm in ARMS:
        actor, critic = build_arm(MASTERS[0], arm)
        with pytest.raises(ValueError, match="digest"):
            load_warm_start(actor, critic, data, "0" * 64)
        load_warm_start(actor, critic, data, digest)
        assert torch.count_nonzero(actor.encoder.raw.weight[:, SCALAR_ACTOR_COLUMNS]) == 0
        assert torch.count_nonzero(actor.encoder.hidden.weight[:, SCALAR_ACTOR_COLUMNS]) == 0
        assert torch.count_nonzero(critic.network[0].weight[:, SCALAR_CRITIC_COLUMNS]) == 0
        for key, source in old_actor.state_dict().items():
            actual = actor.state_dict()[key]
            if key in ("encoder.raw.weight", "encoder.hidden.weight"):
                source = source.clone()
                source[:, SCALAR_ACTOR_COLUMNS] = 0
            assert torch.equal(actual, source), key
        for key, source in old_critic.state_dict().items():
            actual = critic.state_dict()[key]
            if key == "network.0.weight":
                source = source.clone()
                source[:, SCALAR_CRITIC_COLUMNS] = 0
            assert torch.equal(actual, source), key
        x = torch.randn(7, 5, 171, generator=generator(17))
        x[:, :, SCALAR_ACTOR_COLUMNS] = torch.rand(7, 5, 5, generator=generator(18))
        baseline = x.clone()
        baseline[:, :, SCALAR_ACTOR_COLUMNS] = 0
        with torch.no_grad():
            before = old_actor(baseline, torch.zeros(1, 5, 64))[0]
            after = actor(x, torch.zeros(1, 5, 64))[0]
        torch.testing.assert_close(after, before, rtol=0, atol=0)
        cx = torch.randn(7, 451, generator=generator(19))
        cx[:, SCALAR_CRITIC_COLUMNS] = 1
        baseline_cx = cx.clone()
        baseline_cx[:, SCALAR_CRITIC_COLUMNS] = 0
        with torch.no_grad():
            torch.testing.assert_close(critic(cx), old_critic(baseline_cx), rtol=0, atol=0)
        actors.append((actor, critic))
    for actor, critic in actors:
        actor.zero_grad()
        critic.zero_grad()
        x = torch.zeros(1, 5, 171)
        x[:, :, SCALAR_ACTOR_COLUMNS] = 1
        cx = torch.zeros(451)
        cx[list(SCALAR_CRITIC_COLUMNS)] = 1
        (actor(x, torch.zeros(1, 5, 64))[0].sum() + critic(cx)).backward()
        assert actor.encoder.raw.weight.grad[:, SCALAR_ACTOR_COLUMNS].abs().sum() > 0
        assert actor.encoder.hidden.weight.grad[:, SCALAR_ACTOR_COLUMNS].abs().sum() > 0
        assert critic.network[0].weight.grad[:, SCALAR_CRITIC_COLUMNS].abs().sum() > 0
    assert sum(p.numel() for p in actors[-1][0].content.parameters()) + 1 == 66


def test_scalar_density_credit_and_rng():
    actor, _ = build_arm(MASTERS[0], "L")
    recurrent = torch.zeros(1, 5, 64)
    recurrent[0, 0, 0] = 1
    mean = torch.zeros(1, 5, 3)
    motion = torch.zeros(1, 5, 3)
    content = torch.zeros(1, 5, 1)
    content[0, 0, 0] = .4
    mask = torch.zeros(1, 5, dtype=torch.bool)
    mask[0, 0] = True
    lp, entropy = action_terms(actor, mean, recurrent, motion, content, mask)
    expected = tanh_log_prob(motion, mean, actor.log_std)
    expected += torch.where(mask, tanh_log_prob(content, actor.content(recurrent),
                                                actor.content_log_std) + math.log(2), 0)
    torch.testing.assert_close(lp, expected)
    assert float(entropy) == pytest.approx(16 * .5 * math.log(2 * math.pi * math.e))
    (-lp[:, 0]).sum().backward()
    assert actor.content.weight.grad.abs().sum() > 0
    assert actor.content_log_std.grad.abs().sum() > 0
    motion_rng, control_rng, content_rng = generator(20), generator(20), generator(21)
    before = torch.randn(3, generator=motion_rng)
    pre, scalar = sample_content(actor, recurrent[0], 0, content_rng)
    after = torch.randn(3, generator=motion_rng)
    assert scalar.item() == pytest.approx((1 + math.tanh(pre.item())) / 2)
    assert 0 <= scalar.item() <= 1
    assert torch.equal(before, torch.randn(3, generator=control_rng))
    assert torch.equal(after, torch.randn(3, generator=control_rng))


def test_short_synthetic_replay_and_eval_trace(tmp_path, monkeypatch):
    _, data, digest, _, _ = checkpoint(tmp_path)
    actor, critic = build_arm(MASTERS[0], "L")
    load_warm_start(actor, critic, data, digest)
    env = SyntheticAdapter(1, horizon=32)
    counts, rows = new_counts(), []
    motion_rng, content_rng = generator(22), generator(23)
    episodes = [
        collect_episode(env, actor, critic, "L", 32, 100 + e, 200 + e,
                        motion_rng, content_rng,
                        dict(arm="L", master=MASTERS[0], phase="train", episode=e),
                        counts, rows.append, lambda: None)
        for e in range(2)]
    original = torch.stack([episode["obs"] for episode in episodes])
    motion_state, content_state = motion_rng.get_state().clone(), content_rng.get_state().clone()
    eval_path = tmp_path / "eval.npz"
    collect_episode(env, actor, critic, "L", 32, 300, 400,
                    generator(500), generator(600),
                    dict(arm="L", master=MASTERS[0], phase="initial_eval", episode=0),
                    counts, rows.append, lambda: None, eval_path)
    assert torch.equal(motion_rng.get_state(), motion_state)
    assert torch.equal(content_rng.get_state(), content_state)
    assert counts["diagnostic_forward_calls"] == 32
    assert rows[-1]["scalar_response_rms"] == 0
    with np.load(eval_path) as trace:
        assert trace["packet"].shape == (32, 7)
        assert trace["pre_tanh_content"].shape == (32, 1)
        assert trace["scalar_response_rms"].shape == (32,)
        assert trace["actor_input"].shape == (32, 5, 171)
        due = int(trace["due"][0])
        np.testing.assert_array_equal(trace["actor_input"][due, 1, 121:128],
                                      trace["packet"][0])
    with torch.no_grad():
        actor.content.bias.fill_(2)

    def forbidden(*args, **kwargs):
        pytest.fail("PPO replay sampled a new packet or motion")

    monkeypatch.setattr(content_learner, "sample_content", forbidden)
    monkeypatch.setattr(content_learner, "sample_actions", forbidden)
    seen = []
    hook = actor.register_forward_pre_hook(lambda module, inputs: seen.append(inputs[0].clone()))
    try:
        records = update(actor, critic, optimizer_for(actor, critic),
                         episodes, counts, lambda: None)
    finally:
        hook.remove()
    assert len(records) == 4 and counts["optimizer_steps"] == 4
    assert counts["replayed_actor_rows"] == 1280
    expected = original.permute(1, 0, 2, 3).reshape(32, 10, 171)
    assert len(seen) == 4 and all(torch.equal(value, expected) for value in seen)


def test_small_batch_counts_streams_and_partial_frontier(tmp_path):
    checkpoint_path, _, digest, _, _ = checkpoint(tmp_path)
    with pytest.raises(ValueError, match="digest"):
        run_batch(tmp_path / "bad_digest", "1" * 40, checkpoint_path, "0" * 64)
    assert not (tmp_path / "bad_digest").exists()
    def factory(seed):
        return SyntheticAdapter(seed, horizon=32)

    result = run_batch(tmp_path / "batch", "1" * 40, checkpoint_path, digest,
                       factory=factory, horizon=32, train=2, evaluation=1)
    assert result["status"] == "COMPLETE", result["limits"]
    assert [(c["master"], c["arm"]) for c in result["cells"]] == [
        (m, a) for m in MASTERS for a in ARMS]
    assert result["actual"]["team_steps"] == 9 * 128
    assert result["actual"]["optimizer_steps"] == 9 * 4
    assert result["actual"]["diagnostic_forward_calls"] == 9 * 64
    assert validate_cells(result["cells"], horizon=32, train=2, evaluation=1)["complete"]
    identities = [c["rows"][0]["action_sequence_sha256"] for c in result["cells"]]
    assert len(set(identities)) == 1
    for cell in result["cells"]:
        folder = Path(cell["directory"])
        assert len(cell["rows"]) == 2
        assert len((folder / "episodes.jsonl").read_text().splitlines()) == 4
        updates = [json.loads(line) for line in (folder / "updates.jsonl").read_text().splitlines()]
        assert [(u["rollout"], u["epoch"]) for u in updates] == [(0, e) for e in range(4)]
        assert all(Path(cell[key]["path"]).exists() for key in ("initial_checkpoint", "final_checkpoint"))
    calls = 0
    def stop():
        nonlocal calls
        calls += 1
        if calls > 40:
            raise RuntimeError("technical stop")
    partial = run_arm(MASTERS[0], "B", tmp_path / "partial", checkpoint_path.read_bytes(),
                      digest, factory=factory, horizon=32, train=2, evaluation=1, check=stop)
    assert partial["status"] == "INCOMPLETE"
    assert "technical stop" in partial["limits"][0]
    assert partial["counts"]["team_steps"] > 0
    assert (tmp_path / "partial" / "summary.json").exists()

    def failing_factory(seed):
        raise RuntimeError("constructor stop")
    failed = run_batch(tmp_path / "failed_batch", "1" * 40, checkpoint_path, digest,
                       factory=failing_factory, horizon=32, train=2, evaluation=1)
    assert failed["status"] == "INCOMPLETE"
    assert len(failed["cells"]) == 1
    assert failed["cells"][0]["counts"]["fit_started"] == 0
    assert not (tmp_path / "failed_batch" / str(MASTERS[0]) / "O").exists()


def test_cli_rejects_unadmitted_invocation_before_output(tmp_path):
    runner = Path(__file__).resolve().parents[5] / "experiments/candidates/uav_message_content/b02/run.py"
    output = tmp_path / "unadmitted"
    invocation = [sys.executable, str(runner), "--out", str(output),
                  "--launch-sha", "0" * 40, "--seed", "19451",
                  "--checkpoint", "/home/wu/hmasd-inputs/uav_message_content-b02-C-456832fa.pt",
                  "--checkpoint-sha256",
                  "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad"]
    process = subprocess.run(invocation, capture_output=True, text=True, check=False)
    assert process.returncode != 0
    assert not output.exists()

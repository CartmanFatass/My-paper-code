import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch
from torch import nn

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Critic, build_arm as build_cadc,
)
from experiments.candidates.uav_message_content.b03.channel import ContentChannel, Sightings, hand_payload
from experiments.candidates.uav_message_content.b03.model import (
    INHERITED_SHA256, actor_state_sha256, load_asset, sample_content,
)
from experiments.candidates.uav_message_content.b03.study import (
    ARMS, BASE, counts_template, run_batch, validate_assets,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator


def fixture_assets(tmp_path):
    root = tmp_path / "assets"
    root.mkdir()
    specifications = {}
    masters = dict(C=19431, B=19451, O=19452, L=19452)
    for label in ARMS:
        actor, critic = build_cadc(19431, "RR")
        with torch.no_grad():
            actor.encoder.raw.weight[:, 126] = .03125
            actor.encoder.hidden.weight[:, 126] = -.0625
            critic.network[0].weight[:, 154] = .125
        if label == "L":
            actor.content = nn.Linear(64, 1)
            actor.content_log_std = nn.Parameter(torch.zeros(1))
            with torch.no_grad():
                actor.content.weight.fill_(.125)
                actor.content.bias.fill_(.25)
        state = dict(actor=actor.state_dict(), critic=critic.state_dict(),
                     arm=label, master=masters[label], input_size=171,
                     critic_size=451)
        if label != "C":
            state["inherited_sha256"] = INHERITED_SHA256
        buffer = io.BytesIO()
        torch.save(state, buffer)
        data = buffer.getvalue()
        (root / f"{label}.pt").write_bytes(data)
        specifications[label] = dict(master=masters[label], bytes=len(data),
                                     sha256=hashlib.sha256(data).hexdigest())
    return root, specifications


def synthetic_factory(seed):
    return SyntheticAdapter(seed, horizon=32)


def test_strict_asset_loading_preserves_all_saved_tensors(tmp_path, monkeypatch):
    root, specifications = fixture_assets(tmp_path)
    for label in ARMS:
        before_rng = torch.random.get_rng_state().clone()
        actor, source = load_asset(label, root, specification=specifications)
        assert torch.equal(torch.random.get_rng_state(), before_rng)
        assert source["sha256"] == specifications[label]["sha256"]
        assert not actor.training
        assert not any(p.requires_grad for p in actor.parameters())
        assert torch.all(actor.encoder.raw.weight[:, 126] == .03125)
        assert torch.all(actor.encoder.hidden.weight[:, 126] == -.0625)
        saved = torch.load(root / f"{label}.pt", weights_only=True)
        for key, tensor in saved["actor"].items():
            assert torch.equal(actor.state_dict()[key], tensor), (label, key)
        assert len(actor_state_sha256(actor)) == 64
    data = (root / "B.pt").read_bytes()
    (root / "B.pt").write_bytes(data + b"x")
    with pytest.raises(ValueError, match="bytes/digest"):
        load_asset("B", root, specification=specifications)
    (root / "B.pt").write_bytes(data)
    state = torch.load(io.BytesIO(data), weights_only=True)
    state["master"] = 999
    buffer = io.BytesIO()
    torch.save(state, buffer)
    bad = buffer.getvalue()
    (root / "B.pt").write_bytes(bad)
    spec = {**specifications, "B": dict(master=19451, bytes=len(bad),
                                        sha256=hashlib.sha256(bad).hexdigest())}
    with pytest.raises(ValueError, match="metadata"):
        load_asset("B", root, specification=spec)

    def forbidden_forward(*args, **kwargs):
        pytest.fail("critic forward is forbidden in frozen evaluation")
    monkeypatch.setattr(Critic, "forward", forbidden_forward)
    actor, _ = load_asset("L", root, specification=specifications)
    assert actor is not None


def test_packet_order_and_private_rng(tmp_path):
    root, specifications = fixture_assets(tmp_path)
    actor, _ = load_asset("L", root, specification=specifications)
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[0, :3] = (.4, .5, .2)
    raw[0, 3:9] = (.1, .2, .4, -.1, -.2, .4)
    sightings = Sightings()
    sightings.observe(raw)
    c = hand_payload("C", raw, 0, sightings)
    b = hand_payload("B", raw, 0, sightings)
    o = hand_payload("O", raw, 0, sightings)
    assert np.array_equal(c, b)
    assert np.array_equal(o[[0, 1, 2, 3, 4, 6]], c[[0, 1, 2, 3, 4, 6]])
    assert o[5] > 0
    motion, control, content = generator(101), generator(101), generator(102)
    first = torch.randn(3, generator=motion)
    _, scalar = sample_content(actor, torch.ones(5, 64), 0, content)
    second = torch.randn(3, generator=motion)
    assert 0 <= scalar.item() <= 1
    assert torch.equal(first, torch.randn(3, generator=control))
    assert torch.equal(second, torch.randn(3, generator=control))
    l = hand_payload("L", raw, 0, sightings, scalar.item())
    assert np.array_equal(l[[0, 1, 2, 3, 4, 6]], c[[0, 1, 2, 3, 4, 6]])
    channel = ContentChannel(404)
    channel.good = True
    fee, due = channel.resolve_payload(0, l)
    assert (fee, due) == (.001, 1)
    channel.advance()
    channel.begin_tick()
    np.testing.assert_array_equal(channel.records[1, 0, :7], l)


def test_full_128_episode_synthetic_frontier_and_freeze(tmp_path, monkeypatch):
    root, specifications = fixture_assets(tmp_path)
    forward_calls = []
    from experiments.candidates.uav_message_content.b03 import study
    original_load = study.load_asset

    def counted_load(*args, **kwargs):
        actor, source = original_load(*args, **kwargs)
        actor.register_forward_hook(lambda *_: forward_calls.append(1))
        return actor, source

    monkeypatch.setattr(study, "load_asset", counted_load)
    result = run_batch(tmp_path / "output", "a" * 40, root,
                       factory=synthetic_factory, horizon=32, episodes=32,
                       specification=specifications)
    assert result["status"] == "COMPLETE", result["limits"]
    assert len(result["assets"]) == 4
    assert result["actual"]["eval_episodes"] == 128
    assert result["actual"]["team_steps"] == 4096
    assert result["actual"]["motion_samples"] == 20480
    assert result["actual"]["content_samples"] == 1024
    assert result["actual"]["actor_forward_calls"] == 4096
    assert result["actual"]["critic_forward_calls"] == 0
    assert result["actual"]["diagnostic_forward_calls"] == 0
    assert result["actual"]["fits"] == result["actual"]["optimizer_steps"] == 0
    assert len(forward_calls) == 4096
    assert validate_assets(result["assets"], horizon=32, episodes=32)["complete"]
    for cell in result["assets"]:
        assert cell["initial_actor_sha256"] == cell["final_actor_sha256"]
        assert len(cell["rows"]) == 32
        assert len((Path(cell["directory"]) / "episodes.jsonl").read_text().splitlines()) == 32
        assert cell["resources"]["wall_seconds"] >= 0
        row = cell["rows"][0]
        assert (row["reset_seed"], row["channel_seed"], row["motion_seed"],
                row["content_seed"]) == (BASE + 2000, BASE + 7000,
                                         BASE + 3000, BASE + 4000)
        with np.load(row["raw"]) as trace:
            assert set(trace.files) == {
                "actor_input", "pre_tanh_motion", "action", "packet",
                "pre_tanh_content", "due", "good", "deliveries",
                "reward_physical", "reward_net", "served_users", "Q",
                "records", "pending_after_send", "sender"}
            assert trace["actor_input"].shape == (32, 5, 171)
            assert trace["packet"].shape == (32, 7)
            assert trace["pre_tanh_content"].shape == (32, 1)
            due = int(trace["due"][0])
            np.testing.assert_array_equal(trace["actor_input"][due, 1, 121:128],
                                          trace["packet"][0])
    assert not any(cell["counts"]["optimizer_steps"] for cell in result["assets"])


def test_partial_batch_stops_without_replacement(tmp_path):
    root, specifications = fixture_assets(tmp_path)
    constructors = 0
    def failing_factory(seed):
        nonlocal constructors
        constructors += 1
        if constructors == 2:
            raise RuntimeError("constructor stop")
        return SyntheticAdapter(seed, horizon=32)

    result = run_batch(tmp_path / "partial", "a" * 40, root,
                       factory=failing_factory, horizon=32, episodes=1,
                       specification=specifications)
    assert result["status"] == "INCOMPLETE"
    assert len(result["assets"]) == 2
    assert result["assets"][0]["counts"]["eval_episodes"] == 1
    assert result["assets"][1]["counts"]["eval_episodes"] == 0
    assert result["actual"]["fits"] == result["actual"]["optimizer_steps"] == 0
    assert not (tmp_path / "partial" / "O").exists()
    saved = json.loads((tmp_path / "partial" / "summary.json").read_text())
    assert saved["assets"][1]["status"] == "INCOMPLETE"
    assert "constructor stop" in saved["assets"][1]["limits"][0]


def test_cli_admission_precedes_assets_and_output(tmp_path):
    runner = Path(__file__).resolve().parents[5] / "experiments/candidates/uav_message_content/b03/run.py"
    invocation = [sys.executable, str(runner), "--out",
                  "/home/wu/projects/HMASD/runs/uav_message_content/b03_frozen_assets",
                  "--launch-sha", "0" * 40, "--seed", "19461",
                  "--assets-root", "/home/wu/hmasd-inputs/uav_message_content-b03"]
    process = subprocess.run(invocation, capture_output=True, text=True, check=False)
    assert process.returncode != 0
    assert "admission" in (process.stderr + process.stdout).lower()
    assert not (tmp_path / "output").exists()

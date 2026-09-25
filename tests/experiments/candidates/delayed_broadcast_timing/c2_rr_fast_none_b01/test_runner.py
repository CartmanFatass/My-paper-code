"""Technical checks only: distinct reset/channel/motion seeds and no production fit."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import build_arm, sample_actions
from experiments.candidates.delayed_broadcast_timing.c2_rr_fast_none_b01 import runner as c2
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator


TECH = c2.Spec(episodes=1, horizon=2, reset_base=941_210_000,
               channel_base=941_220_000, motion_base=941_230_000,
               send_base=941_240_000, production=False)


def _asset(tmp_path: Path) -> tuple[Path, str, str]:
    actor, critic = build_arm(c2.MASTER, "RR")
    state = {"actor": actor.state_dict(), "critic": critic.state_dict(),
             "arm": "RR", "master": c2.MASTER, "input_size": 171, "critic_size": 451}
    data = io.BytesIO()
    torch.save(state, data)
    payload = data.getvalue()
    archive = tmp_path / "synthetic.pt.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        member = tarfile.TarInfo(c2.MEMBER)
        member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
    return archive, hashlib.sha256(archive.read_bytes()).hexdigest(), hashlib.sha256(payload).hexdigest()


def _read_trace(output: Path, row: dict) -> list[dict]:
    path = output / row["trace"]["path"]
    assert path.stat().st_size == row["trace"]["bytes"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["trace"]["sha256"]
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_send_laws_slot_good_pending_and_delivery_before_action():
    channel = Channel(941_220_123)
    channel.good = False
    channel.t = 3
    assert c2.send_request("RR", channel).tolist() == [False, False, False, True, False]
    assert not c2.send_request("FAST_ONLY", channel).any()
    assert not c2.send_request("NONE", channel).any()
    channel.good = True
    assert c2.send_request("FAST_ONLY", channel).tolist() == [False, False, False, True, False]
    channel.pending[3] = True
    assert not c2.send_request("RR", channel).any()
    assert not c2.send_request("FAST_ONLY", channel).any()
    channel.pending[3] = False
    channel.t = 0
    channel.good = True
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[0, :3] = (.2, .3, .4)
    assert channel.resolve(c2.send_request("RR", channel), raw) == pytest.approx(.001)
    assert channel.pending[0]
    channel.advance()
    assert channel.records[1, 0, 7] == 0
    channel.begin_tick()
    assert not channel.pending[0]
    assert channel.records[1, 0, 7] == 1
    assert channel.records[1, 0, :3].tolist() == pytest.approx([.2, .3, .4])
    assert channel.features()[1, -50:-40][7] == 1  # receiver-1 cache, sender-0 validity
    assert channel.delivered == 1
    slow = Channel(941_220_124)
    slow.t = 255
    slow.good = False
    slow.resolve(c2.send_request("RR", slow), raw)
    slow.advance()
    assert slow.accepted == 1 and slow.delivered == 0
    assert len(slow.inflight) == 1 and slow.inflight[0][2] == 260
    assert int(slow.pending.sum()) == 1  # censored at H256, never delivered later
    gaps = c2._gaps([[([3, 7] if (receiver, sender) == (1, 0) else [])
                     for sender in range(5)] for receiver in range(5)], 10)
    witness = next(row for row in gaps["per_receiver_sender"]
                   if row["receiver"] == 1 and row["sender"] == 0)
    assert (witness["initial_censored_ticks"], witness["between_updates_ticks"],
            witness["terminal_censored_ticks"]) == (3, [4], 3)
    with pytest.raises(ValueError, match="unknown"):
        c2.send_request("OTHER", channel)


def test_strict_frozen_asset_identity_and_shape(tmp_path):
    state, identity = c2.load_asset()
    assert identity["archive"]["sha256"] == c2.ARCHIVE_SHA256
    assert identity["member"] == {"path": c2.MEMBER, "bytes": 463293,
                                   "sha256": c2.MEMBER_SHA256}
    assert identity["actor_parameters"] == 39942
    assert identity["critic_parameters"] == 74497
    assert c2._source_identity(True) == c2.SOURCE_SHA256
    archive, archive_sha, member_sha = _asset(tmp_path)
    with pytest.raises(ValueError, match="archive SHA256"):
        c2.load_asset(archive, archive_sha="0" * 64, member_sha=member_sha)
    with pytest.raises(ValueError, match="member SHA256"):
        c2.load_asset(archive, archive_sha=archive_sha, member_sha="0" * 64)
    state["actor"]["log_std"] = torch.zeros(4)
    data = io.BytesIO(); torch.save(state, data)
    payload = data.getvalue()
    bad = tmp_path / "bad-shape.tar.gz"
    with tarfile.open(bad, "w:gz") as bundle:
        member = tarfile.TarInfo(c2.MEMBER); member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
    with pytest.raises(ValueError, match="tensor contract"):
        c2.load_asset(bad, archive_sha=hashlib.sha256(bad.read_bytes()).hexdigest(),
                      member_sha=hashlib.sha256(payload).hexdigest())


def test_native_three_rule_path_rng_rewards_and_reductions(tmp_path):
    archive, archive_sha, member_sha = _asset(tmp_path)
    output = tmp_path / "technical_c2"
    summary = c2.run(output, "a" * 40, {"sha": "a" * 40}, spec=TECH,
                     factory=make_real, asset=archive,
                     archive_sha=archive_sha, member_sha=member_sha)
    assert summary["status"] == "complete"
    assert summary["counts"]["fits"] == summary["counts"]["optimizer_steps"] == 0
    assert summary["counts"]["training_storage_calls"] == 0
    assert summary["counts"]["complete_episodes"] == 3
    assert summary["counts"]["completed_team_steps"] == 6
    assert summary["counts"]["native_steps_returned"] == 6
    assert summary["counts"]["durably_traced_ticks"] == 6
    assert summary["counts"]["actor_calls"] == 6
    assert summary["counts"]["motion_decisions"] == 30
    assert summary["pairwise"].keys() == {"FAST_ONLY_minus_RR", "FAST_ONLY_minus_NONE", "RR_minus_NONE"}
    assert all(check["unchanged"] for check in summary["model_checks"])
    assert summary["raw_trace_count"] == 3
    assert set(summary["rule_summaries"]) == set(c2.ARMS)
    config = json.loads((output / "config.json").read_text())
    assert config["runtime"]["python_executable"] == sys.executable
    assert config["runtime"]["numpy_version"] == np.__version__
    assert config["runtime"]["torch_version"] == torch.__version__
    assert config["runtime"]["torch_threads"] == 1
    assert config["runtime"]["torch_interop_threads"] == 1
    assert set(config["runtime"]["blas_thread_environment"]) == {
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"}
    rows = summary["rows"]
    assert len({rows[rule][0]["initial_state_sha256"] for rule in c2.ARMS}) == 1
    assert len({rows[rule][0]["channel_good_sequence_sha256"] for rule in c2.ARMS}) == 1
    for rule in c2.ARMS:
        row = rows[rule][0]
        trace = _read_trace(output, row)
        assert [part["type"] for part in trace] == ["initial", "tick", "tick", "terminal"]
        for name, details in trace[0]["initial"]["native_scene"].items():
            array = np.asarray(details["values"], dtype=np.dtype(details["dtype"]))
            assert list(array.shape) == details["shape"]
            assert c2.sha256(array.tobytes()) == details["sha256"]
            assert row["initial_native_scene_sha256"][name] == details["sha256"]
        observed_channel = [tick["channel_good"] for tick in trace[1:3]]
        assert row["channel_good_sequence_sha256"] == c2.sha256(
            np.asarray(observed_channel, dtype=np.uint8).tobytes())
        assert trace[-1]["unused_send_rng_unchanged"]
        assert len(trace[-1]["receive_update_gaps"]["per_receiver_sender"]) == 20
        assert row["packet_delay_ticks"]["count"] == row["delivered"]
        assert row["attempted"] == row["accepted"] + row["collided"]
        assert row["accepted"] == row["delivered"] + row["censored"]
        assert row["action_time_cache"]["valid_peer_entries"] + row["action_time_cache"]["missing_peer_entries"] == 40
        for tick in trace[1:3]:
            np.testing.assert_allclose(np.asarray(tick["post_native_uav_positions"]).reshape(-1),
                                       np.asarray(tick["post_state"])[:15], rtol=0, atol=5e-5)
            connections = np.asarray(tick["connections"], dtype=bool)
            sinr = np.asarray(tick["sinr_db"])
            served, coverage, quality = c2._service(connections, sinr)
            assert served == tick["served_users"]
            assert tick["J_physical"] == pytest.approx(sum(tick["native_rewards"].values()))
            assert tick["J_physical"] == pytest.approx(.7 * coverage + .3 * quality)
            assert tick["J_net"] == pytest.approx(tick["J_physical"] - tick["fee"])
            assert tick["fee"] == pytest.approx(.001 * sum(tick["requested"]))
        assert row["J_net"] == pytest.approx(sum(t["J_net"] for t in trace[1:3]) / 2)
    # Independent exact first-step replay of the source sampled motion primitive.
    rr_ticks = _read_trace(output, rows["RR"][0])[1:3]
    state, _ = c2.load_asset(archive, archive_sha=archive_sha, member_sha=member_sha)
    actor, _ = c2._fresh_models(state)
    hidden = torch.zeros(1, 5, 64)
    motion_rng = generator(TECH.motion_base)
    send_rng = generator(TECH.send_base)
    with torch.no_grad():
        for tick in rr_ticks:
            mean, recurrent, hidden = actor(torch.tensor(tick["actor_input"], dtype=torch.float32)[None],
                                             hidden)
            eligible = torch.tensor([not bool(value) for value in tick["pending_at_action"]])
            u, sends = sample_actions(actor, mean[0], recurrent[0], eligible,
                                      tick["t"], motion_rng, send_rng)
            np.testing.assert_array_equal(u.numpy(), np.asarray(tick["raw_motion"], dtype=np.float32))
            assert sends.numpy().tolist() == [bool(v) for v in tick["requested"]]
            assert c2._tensor_digest(hidden) == tick["hidden_after_sha256"]
            assert c2._tensor_digest(motion_rng.get_state()) == tick["motion_rng_after_sha256"]
    assert json.loads((output / "summary.json").read_text())["status"] == "complete"


def test_reduction_all_pairwise_signed_effects_and_identity_refusal():
    spec = c2.Spec(episodes=2, horizon=1, production=False)
    def row(rule, index, score):
        return {"episode": index, "initial_state_sha256": f"world{index}",
                "initial_raw_sha256": f"raw{index}", "channel_good_sequence_sha256": "same",
                "initial_native_scene_sha256": {"uav_positions": f"native{index}"},
                **{key: score for key in ("J_net", "J_physical", "served_users_per_tick",
                                          "coverage", "quality", "fee_per_tick", "mean_height")}}
    rows = {"RR": [row("RR", 0, 1), row("RR", 1, 3)],
            "FAST_ONLY": [row("FAST_ONLY", 0, 2), row("FAST_ONLY", 1, 2)],
            "NONE": [row("NONE", 0, 0), row("NONE", 1, 4)]}
    reduced = c2._pairwise(rows, spec)
    assert reduced["FAST_ONLY_minus_RR"]["J_net"] == {
        "per_world": [1, -1], "mean": 0, "positive": 1, "adverse": 1,
        "zero": 0, "adverse_worlds": [1]}
    assert reduced["FAST_ONLY_minus_NONE"]["J_net"]["per_world"] == [2, -2]
    assert reduced["RR_minus_NONE"]["J_net"]["per_world"] == [1, -1]
    rows["NONE"][0]["channel_good_sequence_sha256"] = "different"
    with pytest.raises(ValueError, match="exogenous identity"):
        c2._pairwise(rows, spec)
    rows["NONE"][0]["channel_good_sequence_sha256"] = "same"
    rows["NONE"].pop()
    with pytest.raises(ValueError, match="incomplete panel"):
        c2._pairwise(rows, spec)


def test_failed_native_step_keeps_partial_frontier_without_pairwise(tmp_path):
    archive, archive_sha, member_sha = _asset(tmp_path)
    constructed = 0
    class FailSecond:
        def __init__(self, delegate): self.delegate = delegate
        @property
        def env(self): return self.delegate.env
        def reset(self, **kwargs): return self.delegate.reset(**kwargs)
        def close(self): return self.delegate.close()
        def step(self, actions):
            raw, reward, terminated, truncated, info = self.delegate.step(actions)
            info.pop("infos_dict")  # Native step returned; following decomposition fails.
            return raw, reward, terminated, truncated, info
    def factory(seed):
        nonlocal constructed
        constructed += 1
        real = make_real(seed)
        return FailSecond(real) if constructed == 2 else real
    output = tmp_path / "technical_failure"
    with pytest.raises(KeyError, match="infos_dict"):
        c2.run(output, "b" * 40, {"sha": "b" * 40}, spec=TECH,
               factory=factory, asset=archive, archive_sha=archive_sha,
               member_sha=member_sha)
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "failed" and summary["pairwise"] is None
    assert len(summary["rows"]["RR"]) == 1
    assert summary["rows"]["FAST_ONLY"] == summary["rows"]["NONE"] == []
    assert summary["counts"]["complete_episodes"] == 1
    assert summary["counts"]["completed_team_steps"] == TECH.horizon
    assert summary["counts"]["native_steps_returned"] == TECH.horizon + 1
    assert summary["counts"]["durably_traced_ticks"] == TECH.horizon
    assert summary["counts"]["actor_calls"] == TECH.horizon + 1
    assert summary["counts"]["motion_decisions"] == 5 * (TECH.horizon + 1)
    assert summary["active"]["rule"] == "FAST_ONLY"
    assert summary["active"]["native_steps_returned"] == 1
    assert summary["active"]["durably_traced_ticks"] == 0
    partial = output / "raw/fast_only_episode_00.jsonl.partial"
    assert partial.exists()
    assert summary["active"]["partial_trace"] == {
        "path": "raw/fast_only_episode_00.jsonl.partial", "bytes": partial.stat().st_size}
    assert [json.loads(line)["type"] for line in partial.read_text().splitlines()] == ["initial"]


def test_abrupt_exit_keeps_completed_prefix_and_fsynced_partial_trace(tmp_path):
    archive, archive_sha, member_sha = _asset(tmp_path)
    output = tmp_path / "technical_abrupt"
    script = r'''
import os, sys
from pathlib import Path
from experiments.candidates.delayed_broadcast_timing.c2_rr_fast_none_b01.runner import Spec, run
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
constructed = 0
class ExitAfterNativeStep:
    def __init__(self, delegate): self.delegate = delegate
    @property
    def env(self): return self.delegate.env
    def reset(self, **kwargs): return self.delegate.reset(**kwargs)
    def step(self, actions):
        self.delegate.step(actions)
        os._exit(23)
    def close(self): return self.delegate.close()
def factory(seed):
    global constructed
    constructed += 1
    delegate = make_real(seed)
    return ExitAfterNativeStep(delegate) if constructed == 2 else delegate
spec = Spec(episodes=1, horizon=2, reset_base=942_210_000,
            channel_base=942_220_000, motion_base=942_230_000,
            send_base=942_240_000, production=False)
run(Path(sys.argv[1]), "c" * 40, {"sha": "c" * 40}, spec=spec,
    factory=factory, asset=Path(sys.argv[2]), archive_sha=sys.argv[3],
    member_sha=sys.argv[4])
'''
    process = subprocess.run([sys.executable, "-c", script, str(output), str(archive),
                              archive_sha, member_sha], capture_output=True, text=True,
                             timeout=60)
    assert process.returncode == 23, process.stderr
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "incomplete" and summary["pairwise"] is None
    assert len(summary["rows"]["RR"]) == 1
    assert summary["rows"]["FAST_ONLY"] == summary["rows"]["NONE"] == []
    assert summary["counts"]["completed_team_steps"] == 2
    assert summary["active"]["rule"] == "FAST_ONLY"
    assert "raw/*.jsonl.partial" in summary["counter_semantics"]["hard_exit"]
    partial = output / "raw/fast_only_episode_00.jsonl.partial"
    assert summary["active"]["partial_trace"]["path"] == "raw/fast_only_episode_00.jsonl.partial"
    assert summary["active"]["partial_trace"]["bytes"] == 0  # pre-header committed summary
    assert [json.loads(line)["type"] for line in partial.read_text().splitlines()] == ["initial"]


def test_cli_refuses_seed_and_imports_no_science_before_admission(tmp_path):
    script = c2.ROOT / "scripts/run_delayed_broadcast_timing_b01.py"
    command = [sys.executable, str(script), "--seed", "1", "--launch-sha", "a" * 40,
               "--out", str(tmp_path / c2.TAG)]
    refused = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert refused.returncode != 0 and "requires seed 9302" in refused.stderr
    existing = tmp_path / c2.TAG
    existing.mkdir()
    (existing / "summary.json").write_text("{}")
    wrong_output = subprocess.run([sys.executable, str(script), "--seed", "9302",
                                   "--launch-sha", "a" * 40, "--out", str(existing)],
                                  capture_output=True, text=True, timeout=20)
    assert wrong_output.returncode != 0 and "existing C2 scientific output" in wrong_output.stderr
    (existing / "summary.json").unlink()
    blocker = r'''
import importlib.abc, runpy, sys
class Reject(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "torch" or fullname.startswith("torch.") or \
           fullname == "numpy" or fullname.startswith("numpy.") or \
           fullname.startswith("experiments.") or fullname.startswith("envs."):
            raise RuntimeError("scientific import before admission: " + fullname)
        return None
sys.meta_path.insert(0, Reject())
sys.argv = [sys.argv[1], "--seed", "9302", "--launch-sha", "a" * 40,
            "--out", sys.argv[2]]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except Exception as error:
    assert "missing HMASD admission" in str(error), repr(error)
else:
    raise AssertionError("unguarded CLI")
assert "torch" not in sys.modules and "numpy" not in sys.modules
'''
    checked = subprocess.run([sys.executable, "-c", blocker, str(script),
                              str(tmp_path / c2.TAG)], capture_output=True, text=True, timeout=20)
    assert checked.returncode == 0, checked.stderr

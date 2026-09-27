"""B02 resume: finish a fit from a saved checkpoint (load_model + re-seeded worlds and sampling)."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg
from experiments.candidates.energy_relay_benchmark.b02 import training as tr
from experiments.candidates.uav_service_auxiliary.b01.native import optimizer_steps
from scripts import run_energy_relay_benchmark_b02 as entry

MODULES = ("skill_coordinator", "skill_discoverer")
OUTPUT_FILES = ("summary.json", "config.json", "progress.jsonl", "checkpoints")


def _spec(**changes):
    """3 rollouts of 2 x 12, a checkpoint after every rollout: schedule (1, 2, 3)."""
    spec = replace(cfg.B02Spec(), seed=317757, rollouts=3, rollout_length=12, episode_length=12,
                   hidden_size=32, gru_hidden_size=32, ppo_epochs=1,
                   checkpoint_every_transitions=24)
    return replace(spec, **changes)


class _Messages(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.messages: list[tuple[str, str]] = []

    def emit(self, record):
        self.messages.append((record.levelname, record.getMessage()))


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """run_a: the full tiny fit.  run_b: resumed from run_a's c01 with seams observed."""
    root = tmp_path_factory.mktemp("b02_resume")
    spec = _spec()
    torch.set_num_threads(1)
    summary_a = tr.run_training(out=root / "run_a", launch_sha="sha-a", spec=spec,
                                device_name="cpu", threads=1, argv=["test"])
    source = root / "run_a" / "checkpoints" / "c01"
    seen = {"make_env": [], "reset": [], "loaded": None}
    original_make_env, original_resumed = tr.make_env, tr.resumed_agent

    def make_env(config, seed):
        env = original_make_env(config, seed)
        seen["make_env"].append(int(seed))
        reset = env.reset

        def observed_reset(*args, **kwargs):
            seen["reset"].append(kwargs.get("seed"))
            return reset(*args, **kwargs)

        env.reset = observed_reset
        return env

    def resumed_agent(config, record, agent_pt, **kwargs):
        seen["seed"] = kwargs["seed"]
        agent, identity = original_resumed(config, record, agent_pt, **kwargs)
        stored = torch.load(agent_pt, map_location="cpu", weights_only=False)
        modules = {}
        for name in MODULES:
            saved, loaded = stored[name], getattr(agent, name).state_dict()
            modules[name] = (saved.keys() == loaded.keys()
                             and all(torch.equal(saved[key].cpu(), loaded[key].cpu())
                                     for key in saved))
        norms = {"coordinator": agent.value_norm_coordinator,
                 "discoverer": agent.value_norm_discoverer}
        valuenorm = {name: all(np.array_equal(np.asarray(saved[key]),
                                              np.asarray(getattr(norms[name], key)))
                               for key in ("mean", "var", "count"))
                     for name, saved in stored["valuenorm_state"].items()}
        seen["loaded"] = {
            "optimizer_steps": optimizer_steps(agent), "identity": identity, "modules": modules,
            "valuenorm": valuenorm,
            "dual": agent.scenario7_safety_dual_state == stored["scenario7_safety_dual_state"],
            "progress": agent.training_progress == stored["training_progress"],
            "sampler": (agent.rollout_buffer.get_sampler_rng_state(), agent.rollout_sampler_seed),
            "saved_sampler": stored["rollout_sampler_rng"]["streams"]["main_rollout"]}
        return agent, identity

    handler = _Messages()
    logger = logging.getLogger("HMASD")
    level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(tr, "make_env", make_env)
            patch.setattr(tr, "resumed_agent", resumed_agent)
            summary_b = tr.run_training(out=root / "run_b", launch_sha="sha-b", spec=spec,
                                        device_name="cpu", threads=1, argv=["test"],
                                        resume_from=source, resume_source_sha="sha-a")
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
    return dict(root=root, spec=spec, summary_a=summary_a, summary_b=summary_b, source=source,
                seen=seen, messages=handler.messages)


def test_resume_continues_rollouts_transitions_and_checkpoints(runs):
    spec, a, b = runs["spec"], runs["summary_a"], runs["summary_b"]
    out_b = runs["root"] / "run_b"
    schedule = cfg.checkpoint_rollouts(spec)
    record = json.loads((runs["source"] / "record.json").read_text())
    assert schedule == (1, 2, 3) and record["checkpoint"] == "c01" and record["rollout"] == 1
    assert a["status"] == b["status"] == "COMPLETE"
    assert [r["rollout"] for r in b["rollouts"]] == [2, 3]
    assert [r["transitions"] for r in b["rollouts"]] == [48, 72]
    assert b["counts"]["transitions"] == spec.transitions == 72 and b["counts"]["rollouts"] == 3
    assert b["counts"]["checkpoints"] == len(schedule) + 1
    assert b["counts"]["native_episodes"] == sum(len(r["episodes_completed"])
                                                 for r in b["rollouts"])
    assert sorted(b["checkpoints"]) == ["c02", "c03"]
    assert sorted(p.name for p in (out_b / "checkpoints").iterdir()) == ["c02", "c03"]
    assert [b["checkpoints"][c]["transitions"] for c in ("c02", "c03")] == [48, 72]
    for name in ("c02", "c03"):
        written = json.loads((out_b / "checkpoints" / name / "record.json").read_text())
        assert written["checkpoint"] == name and written["launch_sha"] == "sha-b"
        assert written["config"] == record["config"]
    # Adam steps per update are data-independent: the resumed learner ends where run_a ended.
    assert b["optimizer_steps"] == a["optimizer_steps"]
    assert b["rollouts"][0]["optimizer_steps"] == a["rollouts"][1]["optimizer_steps"]
    rows = [json.loads(line) for line in (out_b / "progress.jsonl").read_text().splitlines()]
    assert [row["event"]["rollout"] for row in rows if row["event"]["event"] == "rollout"] == [2, 3]
    assert rows[-1]["event"] == {"event": "training_exit", "status": "COMPLETE"}
    # Every intermediate record of a completed fit passes the pre-load config refusal.
    for name in ("c01", "c02"):
        tr.read_resume_checkpoint(runs["root"] / "run_a" / "checkpoints" / name, spec,
                                  cfg.make_b02_config(spec))


def test_load_restores_the_recorded_learner_exactly(runs):
    record = json.loads((runs["source"] / "record.json").read_text())
    loaded = runs["seen"]["loaded"]
    assert loaded["optimizer_steps"] == record["optimizer_steps"]
    assert loaded["optimizer_steps"]["low_actor"] > 0
    assert loaded["identity"]["policy_fingerprint"] == record["policy_fingerprint"]
    assert loaded["modules"] == {name: True for name in MODULES}   # no missing/unexpected keys
    assert loaded["valuenorm"] == {"coordinator": True, "discoverer": True}
    assert loaded["dual"] and loaded["progress"]
    state, seed = loaded["sampler"]
    assert state == loaded["saved_sampler"]["state"] and seed == loaded["saved_sampler"]["seed"]
    assert runs["summary_b"]["initialization"]["rollout_sampler_state"] == state
    messages = [text for _, text in runs["messages"]]
    assert any("已恢复Discoverer Actor和Critic优化器状态" in text for text in messages)
    assert any("已恢复Coordinator优化器状态" in text for text in messages)
    assert not any("跳过恢复" in text for text in messages)


def test_resume_block_and_seeds(runs):
    spec, b = runs["spec"], runs["summary_b"]
    out_b = runs["root"] / "run_b"
    config = json.loads((out_b / "config.json").read_text())
    assert config["resume"] == b["resume"]
    block = b["resume"]
    record = json.loads((runs["source"] / "record.json").read_text())
    assert block["resume_seed"] == spec.seed + record["rollout"] == 317758
    assert (block["checkpoint"], block["rollout"], block["transitions"]) == ("c01", 1, 24)
    assert block["source_launch_sha"] == "sha-a"
    assert block["agent_pt_sha256"] == record["agent_pt_sha256"]
    assert block["policy_fingerprint"] == record["policy_fingerprint"]
    assert block["source_checkpoint_dir"] == str(runs["source"])
    assert block["restored"] == list(tr.RESUME_RESTORED)
    assert block["re_seeded"] == list(tr.RESUME_RE_SEEDED)
    assert not (out_b / "checkpoints" / "c00").exists()
    seen = runs["seen"]
    assert seen["seed"] == block["resume_seed"]
    lanes = [block["resume_seed"] + lane for lane in range(spec.lanes)]
    assert seen["make_env"] == lanes
    # First resets carry resume_seed + lane; episode-end resets continue the env stream (None).
    assert seen["reset"][:spec.lanes] == lanes
    assert all(value is None for value in seen["reset"][spec.lanes:])
    assert len(seen["reset"]) > spec.lanes
    episodes = [row for r in b["rollouts"] for row in r["episodes_completed"]]
    assert sorted({row["episode"] for row in episodes if row["lane"] == 0})[0] == 0


def _refused(tmp_path, spec, source, **kwargs):
    out = tmp_path / "refused"
    threads = torch.get_num_threads()
    with pytest.raises((ValueError, RuntimeError, FileExistsError)) as caught:
        tr.run_training(out=out, launch_sha="sha-c", spec=spec, device_name="cpu",
                        threads=threads + 2, argv=["test"], resume_from=source, **kwargs)
    assert not out.exists()
    assert torch.get_num_threads() == threads   # refused before any torch effect
    return caught.value


def _copy(runs, tmp_path, name="c01", **record_changes):
    target = tmp_path / "copy" / name
    shutil.copytree(runs["root"] / "run_a" / "checkpoints" / name, target)
    if record_changes:
        path = target / "record.json"
        record = json.loads(path.read_text())
        record.update(record_changes)
        path.write_text(json.dumps(record))
    return target


def test_resume_refusals(runs, tmp_path):
    spec = runs["spec"]
    error = _refused(tmp_path, spec, _copy(runs, tmp_path / "a", agent_pt_sha256="0" * 64))
    assert "SHA-256" in str(error)
    error = _refused(tmp_path, _spec(ppo_epochs=2), runs["source"])
    assert "config differs" in str(error) and "ppo_epochs" in str(error)
    error = _refused(tmp_path, spec, _copy(runs, tmp_path / "b", programme="other"))
    assert "is not" in str(error)
    error = _refused(tmp_path, spec, _copy(runs, tmp_path / "c", object_id="OTHER"))
    assert "is not" in str(error)
    error = _refused(tmp_path, spec, _copy(runs, tmp_path / "d", training_seed=spec.seed + 1))
    assert "training_seed" in str(error)
    endpoint = runs["root"] / "run_a" / "checkpoints" / "c03"
    assert "before the endpoint" in str(_refused(tmp_path, spec, endpoint))
    assert "scheduled" in str(_refused(tmp_path, spec,
                                       runs["root"] / "run_a" / "checkpoints" / "c00"))
    error = _refused(tmp_path, spec, _copy(runs, tmp_path / "e", checkpoint="c02"))
    assert "disagrees" in str(error)
    error = _refused(tmp_path, spec, runs["source"], resume_source_sha="sha-other")
    assert "launch_sha" in str(error)
    with pytest.raises(ValueError, match="only meaningful"):
        tr.run_training(out=tmp_path / "refused", launch_sha="x", spec=spec, device_name="cpu",
                        resume_source_sha="sha-a")
    assert not (tmp_path / "refused").exists()
    # A non-fresh out is refused before anything is added to it.
    busy = tmp_path / "busy"
    busy.mkdir()
    (busy / "config.json").write_text("{}")
    with pytest.raises(FileExistsError):
        tr.run_training(out=busy, launch_sha="x", spec=spec, device_name="cpu",
                        resume_from=runs["source"])
    assert sorted(p.name for p in busy.iterdir()) == ["config.json"]
    assert (busy / "config.json").read_text() == "{}"


def test_collect_and_train_refuses_bad_offsets(runs):
    spec = runs["spec"]
    for kwargs in (dict(start_rollout=-1), dict(start_rollout=spec.rollouts),
                   dict(start_transitions=-1)):
        with pytest.raises(ValueError):
            tr.collect_and_train(None, cfg.make_b02_config(spec), spec, **kwargs)


def test_runner_accepts_resume_arguments():
    args = entry.parse_args(["train", "--seed", "925031", "--launch-sha", "s", "--out", "o",
                             "--resume-from", "ckpt/c03", "--resume-source-sha", "abc"])
    assert str(args.resume_from) == "ckpt/c03" and args.resume_source_sha == "abc"
    plain = entry.parse_args(["train", "--seed", "925031", "--launch-sha", "s", "--out", "o"])
    assert plain.resume_from is None and plain.resume_source_sha is None
    for bad in (["train", "--seed", "915031", "--launch-sha", "s", "--out", "o",
                 "--resume-from", "ckpt/c03"],
                ["train", "--seed", "925031", "--launch-sha", "s", "--out", "o",
                 "--resume-source-sha", "abc"]):
        with pytest.raises(SystemExit):
            entry.parse_args(bad)


def test_runner_passes_resume_arguments_after_admission(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    calls = []
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: {"sha": "s"})
    monkeypatch.setattr(tr, "run_training", lambda **kwargs: calls.append(kwargs) or {})
    entry.main(["train", "--seed", "925031", "--launch-sha", "s", "--out", str(tmp_path / "o"),
                "--device", "cpu", "--resume-from", str(tmp_path / "c03"),
                "--resume-source-sha", "abc"])
    (call,) = calls
    assert call["resume_from"] == tmp_path / "c03" and call["resume_source_sha"] == "abc"
    assert call["spec"] == cfg.production_spec(925031)

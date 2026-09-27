"""Short correctness fixtures for the fixed BC study; no scientific panel seeds."""

from __future__ import annotations

import json
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_imitation.b01 import study


def _episode(length: int, *, value: float = 0.0):
    obs = np.full((length, 8, 3), value, dtype=np.float32)
    state = np.arange(length * 2, dtype=np.float32).reshape(length, 2)
    return {"observations_t": obs, "state_t": state,
            "proposal_t": np.zeros((length, 8, 4), dtype=np.float32),
            "submitted_t": np.ones((length, 8, 4), dtype=np.float32),
            "mode": np.zeros((length, 8), dtype=bool)}


def test_fixed_worlds_and_held_cadence():
    study.validate_worlds()
    assert not set(study.TRAIN_WORLDS) & set(study.EVAL_WORLDS)
    episode = _episode(12)
    episode["observations_t"][:, :, 0] = np.arange(12)[:, None]
    held = study.held_input(episode, 9, 12)
    assert np.all(held[0, :, :2] == episode["state_t"][0])
    assert np.all(held[1, :, :2] == episode["state_t"][10])
    assert np.all(held[2, :, :2] == episode["state_t"][10])
    assert np.array_equal(held[0, 0, -8:], np.eye(8)[0])
    assert np.array_equal(held[0, 7, -8:], np.eye(8)[7])


def test_padding_loss_mask_and_episode_start_reset():
    left, right = _episode(3), _episode(1, value=4)
    obs, target, valid, active = study._chunk([left, right], 0, 3, torch.device("cpu"))
    assert obs.shape == (3, 16, 2 + 8 * 3 + 8 + 3)
    assert valid.sum().item() == 32
    assert valid[0].sum().item() == 16
    assert valid[1].sum().item() == 8
    assert valid[2].sum().item() == 8
    assert not valid[1:, 8:].any()
    assert not active.any()
    assert target[0, 0].sum() == 0


def test_native_actor_reconstruction_and_checkpoint(tmp_path, monkeypatch):
    """One unrelated seed-41/H12 world crosses the held t=10 boundary."""
    from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
    from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
    from experiments.candidates.energy_relay_benchmark.b02.configuration import apply_set_switch
    from experiments.candidates.uav_service_auxiliary.b01.native import make_env, seed_everything
    from hmasd.agent import HMASDAgent

    torch.set_num_threads(1)
    config = apply_set_switch(ev.make_eval_config(12, 41))
    config.ordinary_completed_segments = False
    assert not config.use_obsnorm and not config.use_statenorm
    assert config.continuous_action_distribution == "tanh_gaussian"
    seed_everything(41, torch.device("cpu"))
    agent = HMASDAgent(config, log_dir=str(tmp_path), device=torch.device("cpu"))
    agent.train(False)
    env = make_env(config, 41)
    observer = study.TeacherObserver()
    try:
        _row, trace = ev.evaluate_world(ev.PolicyController(agent), env, config, 41,
                                        PRODUCTION_PARAMS, observer=observer)
    finally:
        env.close()
    episode = observer.as_arrays()
    episode["mode"] = trace["mode"]
    assert len(episode["state_t"]) == 12
    assert np.any(np.abs(episode["proposal_t"] - np.tanh(episode["proposal_t"])) > 1e-6)
    hidden = study._initial_hidden(config, 1, torch.device("cpu"))
    predictions = []
    with torch.no_grad():
        for start in (0, 10):
            stop = min(start + 10, 12)
            obs, _target, _valid, _active = study._chunk([episode], start, stop, torch.device("cpu"))
            actions, hidden = study._actor_forward(agent.skill_discoverer.actor, obs, hidden,
                                                   reset=(start == 0))
            predictions.append(actions.cpu().numpy().reshape(stop - start, 8, 4))
    np.testing.assert_allclose(np.concatenate(predictions), episode["proposal_t"],
                               rtol=1e-5, atol=1e-5)

    checkpoint_root = tmp_path / "checkpoints"
    checkpoint_root.mkdir()
    saved = study._save_checkpoint(agent, config, tmp_path, "initial", "a" * 40, 0, 0)
    path = checkpoint_root / "initial" / "agent.pt"
    assert saved["record"]["agent_pt_sha256"] == study.sha256_file(path)
    from experiments.candidates.energy_relay_benchmark.b01.evaluation import WorldTask
    task = WorldTask(controller="L", seed=41, params=PRODUCTION_PARAMS, horizon=12,
                     policy_seed=41, threads=1, checkpoint=str(path),
                     checkpoint_record=str(path.parent / "record.json"))
    restored_config = ev.learner_eval_config(ev.make_eval_config(12, 41), saved["record"])
    restored, identity = ev.load_learner_policy(task, saved["record"], restored_config,
                                                 torch.device("cpu"), str(tmp_path))
    assert identity["policy_fingerprint"] == saved["record"]["policy_fingerprint"]
    assert json.loads((path.parent / "record.json").read_text())["agent_pt_sha256"] == study.sha256_file(path)
    monkeypatch.setattr(study, "HORIZON", 12)
    monkeypatch.setattr(study, "TRAIN_WORLDS", (41,))
    raw = tmp_path / "raw" / "teacher_train"
    raw.mkdir(parents=True)
    np.savez_compressed(raw / "41.npz", **episode)
    (tmp_path / "logs").mkdir(exist_ok=True)
    replay_summary = {"counts": {"replay_agent_transitions": 0}}
    reading = study._replay_checkpoint(tmp_path, saved, "teacher_train", replay_summary)
    assert reading["overall"]["agent_steps"] == 12 * 8
    assert reading["shield_inactive"]["agent_steps"] + reading["shield_active"]["agent_steps"] == 12 * 8
    assert reading["overall"]["mse"] < 1e-10


def test_native_teacher_worker_writes_one_complete_raw_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "HORIZON", 12)
    monkeypatch.setattr(study, "TRAIN_WORLDS", (41,))
    (tmp_path / "logs").mkdir()
    (tmp_path / "raw" / "teacher_train").mkdir(parents=True)
    row = study._world(study.Job("teacher_train", 41), str(tmp_path))
    assert row["actual_length"] == 12 and row["optimizer_updates"] == 0
    path = tmp_path / row["raw"]["path"]
    assert row["raw"]["sha256"] == study.sha256_file(path)
    episode = study._load_episode(path)
    assert episode["proposal_t"].shape == (12, 8, 4)
    json.dumps(row, allow_nan=False, default=study._bad_json)


def test_synthetic_fit_actor_only_and_early_tails(tmp_path, monkeypatch):
    from experiments.candidates.energy_relay_benchmark.b02.training import new_agent

    torch.set_num_threads(1)
    config = study.make_config(horizon=12)
    seeds = (41, 42, 43, 44)
    monkeypatch.setattr(study, "TRAIN_WORLDS", seeds)
    monkeypatch.setattr(study, "EPOCHS", 2)
    monkeypatch.setattr(study, "CHUNK", 2)
    (tmp_path / "logs").mkdir()
    raw = tmp_path / "raw" / "teacher_train"
    raw.mkdir(parents=True)
    for seed, length in zip(seeds, (3, 1, 2, 2)):
        ep = _episode(length)
        # Match the actual native dimensions, with bounded synthetic proposal labels.
        ep["observations_t"] = np.zeros((length, 8, config.obs_dim), dtype=np.float32)
        ep["state_t"] = np.zeros((length, config.state_dim), dtype=np.float32)
        ep["proposal_t"][:] = 0.25
        np.savez_compressed(raw / f"{seed}.npz", **ep)
    agent, _identity = new_agent(config, device=torch.device("cpu"),
                                 log_dir=tmp_path / "logs", seed=41)
    summary = {"counts": {"optimizer_updates": 0, "agent_transition_exposures": 0}}
    result = study._fit(agent, config, tmp_path, summary)
    assert result["updates"] == 4
    assert result["agent_transition_exposures"] == 2 * 8 * (3 + 1 + 2 + 2)
    assert result["actor_parameter_l2_movement"] > 0
    assert result["finite_gradients"] and result["logstd_unchanged"]
    assert result["critic_coordinator_normalizers_unchanged"]
    from experiments.candidates.energy_relay_benchmark.b01 import evaluation as ev
    from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
    (tmp_path / "checkpoints").mkdir()
    saved = study._save_checkpoint(agent, config, tmp_path, "final", "a" * 40,
                                   result["updates"], result["agent_transition_exposures"])
    record = saved["record"]
    path = tmp_path / "checkpoints" / "final" / "agent.pt"
    task = ev.WorldTask(controller="L", seed=41, params=PRODUCTION_PARAMS, horizon=12,
                        policy_seed=study.MODEL_SEED, threads=1, checkpoint=str(path),
                        checkpoint_record=str(path.parent / "record.json"))
    eval_config = ev.learner_eval_config(ev.make_eval_config(12, study.MODEL_SEED), record)
    restored, identity = ev.load_learner_policy(task, record, eval_config,
                                                 torch.device("cpu"), str(tmp_path / "logs"))
    assert identity["policy_fingerprint"] == record["policy_fingerprint"]
    assert study.optimizer_steps(restored)["low_actor"] == result["updates"]


@pytest.mark.parametrize("error", [RuntimeError("native exception"),
                                   BrokenProcessPool("worker died")])
def test_failed_panel_retains_unknown_work(tmp_path, monkeypatch, error):
    submitted = []
    class Immediate:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def submit(self, func, job, out):
            from concurrent.futures import Future
            submitted.append(job.seed)
            future = Future()
            future.set_exception(error)
            return future
    monkeypatch.setattr(study, "ProcessPoolExecutor", Immediate)
    (tmp_path / "per_world").mkdir()
    summary = {"started_at_monotonic": study.time.perf_counter(),
               "counts": {"environment_transitions": 0, "environment_transitions_upper_bound": 0,
                          "environment_transitions_exact": True,
                          "failed_worlds_unknown_environment_work": 0,
                          "native_episodes_completed": 0,
                          "episodes_completed": 0, "episodes_failed": 0},
               "failures": [], "panels": {}, "costs": {}}
    jobs = [study.Job("teacher_train", seed) for seed in study.TRAIN_WORLDS[:5]]
    assert not study._run_panel(tmp_path, jobs, summary)
    row = summary["panels"]["teacher_train"]["rows"][0]
    assert row["failed"] and str(error) in row["failure"]
    assert len(submitted) == study.WORKERS
    assert summary["panels"]["teacher_train"]["unattempted"] == len(jobs) - study.WORKERS
    counts = summary["counts"]
    assert counts["environment_transitions"] == 0
    assert counts["environment_transitions_upper_bound"] == study.WORKERS * study.HORIZON
    assert counts["failed_worlds_unknown_environment_work"] == study.WORKERS
    assert not counts["environment_transitions_exact"]
    assert counts["episodes_failed"] == study.WORKERS


@pytest.mark.parametrize("fail_at", [1, study.WORKERS + 1])
def test_submit_rejection_drains_accepted_futures_without_retry(tmp_path, monkeypatch, fail_at):
    from concurrent.futures import Future

    submitted = []
    class RejectingPool:
        def __init__(self, *args, **kwargs):
            self.pending = []
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def submit(self, _func, job, _out):
            submitted.append(job.seed)
            if len(submitted) == fail_at:
                for future in self.pending:
                    future.set_exception(BrokenProcessPool("accepted worker died"))
                raise BrokenProcessPool("submit rejected")
            future = Future()
            if len(submitted) == 1:
                future.set_result({"panel": job.panel, "seed": job.seed, "failed": False,
                                   "native_episode_complete": True, "actual_length": 12})
            else:
                self.pending.append(future)
            return future

    monkeypatch.setattr(study, "ProcessPoolExecutor", RejectingPool)
    (tmp_path / "per_world").mkdir()
    summary = {"started_at_monotonic": study.time.perf_counter(),
               "counts": {"environment_transitions": 0, "environment_transitions_upper_bound": 0,
                          "environment_transitions_exact": True,
                          "failed_worlds_unknown_environment_work": 0,
                          "native_episodes_completed": 0,
                          "episodes_completed": 0, "episodes_failed": 0},
               "failures": [], "panels": {}, "costs": {}}
    jobs = [study.Job("teacher_train", seed)
            for seed in study.TRAIN_WORLDS[:study.WORKERS + 2]]
    assert not study._run_panel(tmp_path, jobs, summary)
    assert len(submitted) == fail_at
    submission = [failure for failure in summary["failures"]
                  if failure.get("stage") == "submission"]
    assert len(submission) == 1 and submission[0]["seed"] == submitted[-1]
    assert submission[0]["episode_attempted"] is False
    panel = summary["panels"]["teacher_train"]
    assert panel["unattempted"] == len(jobs) - len(panel["rows"])
    assert submitted[-1] not in {row["seed"] for row in panel["rows"]}
    counts = summary["counts"]
    if fail_at == 1:
        assert panel["rows"] == [] and panel["unattempted"] == len(jobs)
        assert counts["environment_transitions"] == 0
        assert counts["environment_transitions_exact"]
    else:
        assert len(panel["rows"]) == study.WORKERS
        assert counts["environment_transitions"] == 12
        assert counts["episodes_completed"] == 1
        assert counts["episodes_failed"] == study.WORKERS - 1
        assert counts["failed_worlds_unknown_environment_work"] == study.WORKERS - 1
        assert counts["environment_transitions_upper_bound"] == (
            12 + (study.WORKERS - 1) * study.HORIZON)
        assert not counts["environment_transitions_exact"]


def test_raw_write_failure_preserves_native_episode_and_known_steps(tmp_path, monkeypatch):
    seed = study.TRAIN_WORLDS[0]
    native_row = {"seed": seed, "actual_length": 12, "raw_native_J": 3.25,
                  "terminal_type": "truncated", "failed": False}
    monkeypatch.setattr(study.ev, "evaluate_task", lambda *_args, **_kwargs:
                        {"row": native_row, "arrays": {}, "observation": {}})
    def fail_write(*_args, **_kwargs):
        raise OSError("raw file write failed")
    monkeypatch.setattr(study.np, "savez_compressed", fail_write)
    (tmp_path / "raw" / "teacher_train").mkdir(parents=True)
    (tmp_path / "logs").mkdir()
    failed_row = study._world(study.Job("teacher_train", seed), str(tmp_path))
    assert failed_row["failed"] and failed_row["failure_stage"] == "raw_write"
    assert failed_row["native_episode_complete"] is True
    assert failed_row["actual_length"] == 12
    assert failed_row["raw_native_J"] == 3.25
    assert "raw" not in failed_row

    class Immediate:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def submit(self, *_args):
            from concurrent.futures import Future
            future = Future()
            future.set_result(failed_row)
            return future
    monkeypatch.setattr(study, "ProcessPoolExecutor", Immediate)
    (tmp_path / "per_world").mkdir()
    summary = {"started_at_monotonic": study.time.perf_counter(),
               "counts": {"environment_transitions": 0, "environment_transitions_upper_bound": 0,
                          "environment_transitions_exact": True,
                          "failed_worlds_unknown_environment_work": 0,
                          "native_episodes_completed": 0,
                          "episodes_completed": 0, "episodes_failed": 0},
               "failures": [], "panels": {}, "costs": {}}
    assert not study._run_panel(tmp_path, [study.Job("teacher_train", seed)], summary)
    counts = summary["counts"]
    assert counts["environment_transitions"] == 12
    assert counts["environment_transitions_upper_bound"] == 12
    assert counts["environment_transitions_exact"]
    assert counts["native_episodes_completed"] == 1
    assert counts["episodes_completed"] == 0 and counts["episodes_failed"] == 1
    assert summary["panels"]["teacher_train"]["rows"][0]["raw_native_J"] == 3.25


def test_runner_admission_precedes_science_import(monkeypatch, tmp_path):
    from experiments.candidates.energy_relay_imitation import run_b01
    import scripts.hmasd_admission as admission
    marker = []
    def refuse(*_args, **_kwargs):
        marker.append("admission")
        raise RuntimeError("refused")
    monkeypatch.setattr(admission, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="refused"):
        run_b01.main(["--out", str(tmp_path / "output"), "--launch-sha", "a" * 40])
    assert marker == ["admission"]
    assert not (tmp_path / "output").exists()


def _launcher_output(out):
    out.mkdir()
    for name in ("launch-manifest.json", "launch-status.json", "admission-preflight.json",
                 "stdout.log", "stderr.log"):
        (out / name).write_text("{}\n")
    (out / ".hmasd-launch-abc123.tmp").write_text("pending atomic status\n")


def test_admitted_runner_accepts_native_launcher_metadata(tmp_path, monkeypatch):
    from experiments.candidates.energy_relay_imitation import run_b01
    import scripts.hmasd_admission as admission

    out = tmp_path / "output"
    _launcher_output(out)
    sha = "a" * 40
    monkeypatch.setattr(admission, "require_admission", lambda *_args, **_kwargs: {"sha": sha})
    for name in study.THREAD_ENV:
        monkeypatch.setenv(name, "8")
    observed = []
    def stop_before_worlds(output, jobs, summary):
        observed.append((output, len(jobs)))
        return False
    monkeypatch.setattr(study, "_run_panel", stop_before_worlds)
    assert run_b01.main(["--out", str(out), "--launch-sha", sha]) == 1
    assert observed == [(out, 32)]
    assert json.loads((out / "summary.json").read_text())["status"] == "FAILED"
    assert json.loads((out / "config.json").read_text())["thread_environment"] == {
        name: "1" for name in study.THREAD_ENV}
    for name in ("launch-manifest.json", "launch-status.json", "admission-preflight.json",
                 "stdout.log", "stderr.log"):
        assert (out / name).read_text() == "{}\n"
    assert (out / ".hmasd-launch-abc123.tmp").read_text() == "pending atomic status\n"


def test_atomic_launcher_temp_disappearing_after_listing_is_allowed(tmp_path, monkeypatch):
    from experiments.candidates.energy_relay_imitation import run_b01
    import scripts.hmasd_admission as admission

    out = tmp_path / "output"
    _launcher_output(out)
    sha = "a" * 40
    monkeypatch.setattr(admission, "require_admission", lambda *_args, **_kwargs: {"sha": sha})
    monkeypatch.setattr(study, "_run_panel", lambda *_args: False)
    real_lstat = Path.lstat
    def disappearing_lstat(self):
        if self.name == ".hmasd-launch-abc123.tmp":
            raise FileNotFoundError(self)
        return real_lstat(self)
    monkeypatch.setattr(Path, "lstat", disappearing_lstat)
    assert run_b01.main(["--out", str(out), "--launch-sha", sha]) == 1
    assert json.loads((out / "summary.json").read_text())["status"] == "FAILED"


@pytest.mark.parametrize("name", sorted(study.SCIENTIFIC_OUTPUTS))
def test_admitted_runner_refuses_existing_science_output(tmp_path, monkeypatch, name):
    from experiments.candidates.energy_relay_imitation import run_b01
    import scripts.hmasd_admission as admission

    out = tmp_path / "output"
    _launcher_output(out)
    existing = out / name
    if name in {"raw", "checkpoints", "logs", "per_world"}:
        existing.mkdir()
    else:
        existing.write_text("prior result\n")
    sha = "a" * 40
    monkeypatch.setattr(admission, "require_admission", lambda *_args, **_kwargs: {"sha": sha})
    with pytest.raises(FileExistsError, match="prior or unknown content"):
        run_b01.main(["--out", str(out), "--launch-sha", sha])
    assert existing.exists()
    assert not (out / "teacher_train").exists()

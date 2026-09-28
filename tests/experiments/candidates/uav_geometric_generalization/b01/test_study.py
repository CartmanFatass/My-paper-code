from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    PolicyController, WorldTask, evaluate_task, evaluate_world, learner_eval_config,
    make_eval_config, sample_seed,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_geometric_generalization import run_b01
from experiments.candidates.uav_geometric_generalization.b01 import study
from experiments.candidates.uav_geometric_generalization.b01.symmetry import (
    D4, inverse_actions, transform_observations, transform_state,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

CHECKPOINT = Path(__file__).resolve().parents[5] / "runs/energy_relay_benchmark/b02_s1_set_a01r/checkpoints/c06"


def test_entry_admission_precedes_checkpoint_access(monkeypatch, tmp_path):
    import scripts.hmasd_admission

    def refusal(*args, **kwargs):
        raise RuntimeError("test admission refusal")

    monkeypatch.setattr(scripts.hmasd_admission, "require_admission", refusal)
    with pytest.raises(RuntimeError, match="test admission refusal"):
        run_b01.main(["--out", str(tmp_path / "never-created"), "--launch-sha", "abc",
                      "--checkpoint-dir", str(tmp_path / "missing-checkpoint")])
    assert not (tmp_path / "never-created").exists()


@pytest.mark.parametrize("xy,frame", [
    ((.1, .1), D4.ROT180), ((.9, .1), D4.MIRROR_Y),
    ((.1, .9), D4.MIRROR_X), ((.9, .9), D4.IDENTITY),
])
def test_corner_rule_and_fixed_frame(xy, frame):
    class RecordingAgent:
        device = "cpu"

        def reset_env_state(self, lane):
            self.inputs = []

        def step(self, state, obs, steps, done, **kwargs):
            self.inputs.append((state.copy(), obs.copy(), steps.copy(), done.copy()))
            actions = np.tile(np.array([.2, -.3, .4, .6], np.float32), (1, 8, 1))
            return actions, None, None

    observations = np.zeros((8, 365), dtype=np.float32)
    observations[:, :2] = xy
    state = np.zeros(306, dtype=np.float32)
    agent = RecordingAgent()
    controller = study.CanonicalController(agent, canonical=True)
    controller.reset()
    action = controller.propose(observations, state, 0, np.ones(1, bool), np.zeros(8, bool))
    assert controller.frame == frame
    np.testing.assert_array_equal(agent.inputs[0][1][0], transform_observations(observations, frame))
    np.testing.assert_array_equal(agent.inputs[0][0][0], transform_state(state, frame))
    np.testing.assert_array_equal(action[:, 2:], np.tile([.4, .6], (8, 1)).astype(np.float32))
    observations[:, :2] = (1-observations[:, :2])
    controller.propose(observations, state, 11, np.zeros(1, bool), np.zeros(8, bool))
    assert controller.frame == frame
    controller.reset()
    controller.propose(observations, state, 0, np.ones(1, bool), np.zeros(8, bool))
    assert controller.frame == study.northeast_frame(observations)


@pytest.mark.parametrize("mode", ["deterministic", "stochastic"])
def test_p_matches_original_native_evaluator(mode, tmp_path):
    if not (CHECKPOINT / "agent.pt").exists():
        pytest.skip("retained c06 checkpoint is not present on this test host")
    torch.set_num_threads(1)
    horizon, seed = 24, 952001
    record = study.checkpoint_record(CHECKPOINT)
    config = learner_eval_config(make_eval_config(horizon, study.POLICY_SEED), record)
    job = {"program": f"P_{mode}", "seed": seed}
    controller, agent, _ = study.learned_controller(config, record, CHECKPOINT, job, str(tmp_path))
    env = make_env(config, seed)
    try:
        _, actual = evaluate_world(controller, env, config, seed, PRODUCTION_PARAMS)
    finally:
        env.close()
    task = WorldTask(
        controller="L", seed=seed, params=PRODUCTION_PARAMS, horizon=horizon,
        policy_seed=study.POLICY_SEED, threads=1, checkpoint=str(CHECKPOINT / "agent.pt"),
        checkpoint_record=str(CHECKPOINT / "record.json"), action_mode=mode,
        draw=0 if mode == "stochastic" else None, log_dir=str(tmp_path),
        expected_checkpoint_sha256=study.CHECKPOINT_SHA256,
        expected_policy_fingerprint=study.POLICY_FINGERPRINT)
    expected = evaluate_task(task)["arrays"]
    assert actual.keys() == expected.keys()
    for name in actual:
        np.testing.assert_array_equal(actual[name], expected[name], err_msg=name)
    assert all(p.grad is None for p in agent.skill_discoverer.actor.parameters())


def test_c_recurrent_and_snapshot_history_matches_fixed_frame_reference(tmp_path):
    if not (CHECKPOINT / "agent.pt").exists():
        pytest.skip("retained c06 checkpoint is not present on this test host")
    torch.set_num_threads(1)
    record = study.checkpoint_record(CHECKPOINT)
    config = learner_eval_config(make_eval_config(24, study.POLICY_SEED), record)
    job = {"program": "C_deterministic", "seed": 952001}
    candidate, agent, _ = study.learned_controller(config, record, CHECKPOINT, job, str(tmp_path))
    _, reference_agent, _ = study.learned_controller(
        config, record, CHECKPOINT, {"program": "P_deterministic", "seed": 952001}, str(tmp_path))
    reference = PolicyController(reference_agent, deterministic=True)
    candidate.reset()
    reference.reset()
    generator = np.random.default_rng(4511)
    state = generator.uniform(0, 1, 306).astype(np.float32)
    observations = generator.uniform(0, 1, (8, 365)).astype(np.float32)
    observations[:, :2] = .1
    frame = D4.ROT180
    held = None
    for step in range(12):
        done = np.asarray([step == 0])
        modes = np.zeros(8, bool)
        transformed_obs = transform_observations(observations, frame)
        transformed_state = transform_state(state, frame)
        expected = inverse_actions(reference.propose(transformed_obs, transformed_state,
                                                     step, done, modes), frame)
        actual = candidate.propose(observations, state, step, done, modes)
        np.testing.assert_array_equal(actual, expected)
        np.testing.assert_array_equal(agent.actor_hidden_np, reference_agent.actor_hidden_np)
        np.testing.assert_array_equal(agent._central_snapshot_states,
                                      reference_agent._central_snapshot_states)
        if step in (0, 10):
            held = transformed_state.copy()
        np.testing.assert_array_equal(agent._central_snapshot_states[0], held)
        observations = generator.uniform(0, 1, (8, 365)).astype(np.float32)
        state = generator.uniform(0, 1, 306).astype(np.float32)
    assert candidate.frame == D4.ROT180
    assert np.linalg.norm(agent.actor_hidden_np) > 0


def test_extra_readings_censor_never_served_and_use_fixed_clock():
    n = 1200
    metrics = np.zeros((n, len(study.TRACE_FIELDS)))
    steps = {"metrics": metrics, "mode": np.zeros((n, 8), bool),
             "battery": np.full((n, 8), .11), "own_xyz": np.zeros((n, 8, 3))}
    observed = {"physical_displacement": np.zeros((n, 8, 3))}
    row = study.extra_readings(steps, observed)
    assert row["first_service_step"] is None
    assert row["first_service_censored_wait"] == n
    assert not row["served_by_step60"]
    metrics[1000:, study.QOS] = 1
    row = study.extra_readings(steps, observed)
    assert row["qos_first1000"] == 0
    assert row["qos_after1000"] == 1
    assert row["first_service_step"] == 1000


def test_fixed_plan_and_incomplete_no_contrasts():
    jobs = study.plan()
    assert len(jobs) == 80 and len({job["seed"] for job in jobs}) == 16
    assert study.HORIZON * len(jobs) == 240000
    summary = study.summarize([])
    assert summary["status"] == "incomplete"
    assert not summary["contrasts"]
    assert summary["fits"] == summary["optimizer_updates"] == 0


@pytest.mark.parametrize("program", ["C_stochastic", "H_central10"])
def test_worker_native_output_contract(program, monkeypatch, tmp_path):
    if not (CHECKPOINT / "agent.pt").exists():
        pytest.skip("retained c06 checkpoint is not present on this test host")
    job = {"program": program, "seed": 952001, "job_key": f"{program}/952001"}
    monkeypatch.setattr(study, "HORIZON", 24)
    monkeypatch.setattr(study, "plan", lambda: [job])
    (tmp_path / "raw").mkdir()
    (tmp_path / "logs").mkdir()
    row = study.worker((job, str(tmp_path), str(CHECKPOINT)))
    assert row["status"] == "completed", row
    assert row["actual_length"] == row["inference_calls"] == 24
    assert row["qos_after1000"] is None
    assert row["worker_cpu_seconds"] > 0
    with np.load(tmp_path / row["raw_path"], allow_pickle=False) as trace:
        assert trace["proposal"].shape == (24, 8, 4)
        assert trace["reward"].sum() == row["raw_native_J"]
        assert trace["physical_displacement"].shape == (24, 8, 3)


def test_missing_tail_metric_is_not_imputed_as_zero(monkeypatch):
    monkeypatch.setattr(study, "WORLDS", (1, 2))
    monkeypatch.setattr(study, "CONTRAST_FIELDS", ("qos_after1000",))
    rows = [{"program": program, "seed": seed, "qos_after1000": value}
            for program, seed, value in (("C", 1, None), ("P", 1, .2),
                                         ("C", 2, .7), ("P", 2, .2))]
    row = study.paired(rows, "C", "P")["qos_after1000"]
    assert row["paired_seeds"] == [2]
    assert row["mean"] == pytest.approx(.5)
    assert row["ci95"] is None


def test_complete_summary_uses_the_fixed_paired_worlds_and_refuses_a_missing_row():
    rows = []
    for job in study.plan():
        candidate = job["program"].startswith("C_")
        row = {field: float(candidate) for field in study.CONTRAST_FIELDS}
        row.update(job, status="completed", actual_length=study.HORIZON,
                   input_before_entry=False, zero_service=False,
                   episode_minimum_battery_ratio=.11, terminal_type="truncated")
        rows.append(row)
    summary = study.summarize(rows)
    assert summary["status"] == "complete"
    assert summary["completed_transitions"] == 240000
    delta = summary["contrasts"]["C-P_stochastic"]["raw_native_J"]
    assert delta["mean"] == 1 and delta["ci95"] == [1, 1]
    assert delta["paired_seeds"] == list(study.WORLDS)
    assert not study.summarize(rows[:-1])["contrasts"]
    assert study.summarize(rows[:-1] + [rows[0]])["status"] == "incomplete"


def test_worker_failure_retains_observed_count_without_a_surrogate_result(monkeypatch, tmp_path):
    def fail_before_env(path):
        raise ValueError("deliberate unavailable checkpoint")

    monkeypatch.setattr(study, "checkpoint_record", fail_before_env)
    (tmp_path / "raw").mkdir()
    (tmp_path / "logs").mkdir()
    row = study.worker((study.plan()[0], str(tmp_path), str(tmp_path / "missing")))
    assert row["status"] == "failed"
    assert row["partial_observed_steps"] == 0
    assert "deliberate unavailable checkpoint" in row["error"]
    assert "raw_native_J" not in row
    assert len(list((tmp_path / "raw").glob("*.progress.json"))) == 1

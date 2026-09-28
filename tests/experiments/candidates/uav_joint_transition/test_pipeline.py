from __future__ import annotations

from functools import partial
import json

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world, make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_radio_placement.b01.placement import PlacementController
from experiments.candidates.uav_radio_placement.b01.runner import PlacementObserver
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_joint_transition import training, runner, run_b01
from experiments.candidates.uav_joint_transition.constants import *
from experiments.candidates.uav_joint_transition.controllers import FEATURE_DIM
from experiments.candidates.uav_joint_transition.macro_env import NativeMacroEnv
from experiments.candidates.uav_joint_transition.policy import PathPolicy
from experiments.candidates.uav_joint_transition.readout import summarize, PAIR_HASHES


def test_selected_exposure_and_seeds():
    assert len(TRAIN_SEEDS) == 64
    assert sorted(lane_seeds(0)+lane_seeds(1)) == list(TRAIN_SEEDS)
    assert not set(TRAIN_SEEDS) & set(EVAL_SEEDS)
    assert POLICY_SEED not in set(TRAIN_SEEDS) | set(EVAL_SEEDS)
    assert len(evaluation_plan()) == 32
    assert ARMS == ("L", "O", "R", "P")
    assert TOTAL_MACRO_STEPS*30+len(evaluation_plan())*HORIZON == 288000
    assert 32*4*2 == OPTIMIZER_STEPS == 256
    assert training.PPO_PARAMS["gamma"] == 1.0 and training.PPO_PARAMS["ent_coef"] == 0


def test_native_macro_D_identity_complete_records_and_exhaustion(tmp_path):
    torch.set_num_threads(1)
    seed = 62999001
    (tmp_path/"training").mkdir()
    macro = NativeMacroEnv((seed,), horizon=60, out=tmp_path)
    try:
        first, info = macro.reset(seed=999)
        assert first.shape == (FEATURE_DIM,) and info["world_seed"] == seed
        with pytest.raises(RuntimeError, match="unfinished"):
            macro.reset()
        total = 0.0
        for index in range(2):
            obs, reward, done, truncated, info = macro.step(np.zeros(8, dtype=np.int64))
            total += reward
            assert done == (index == 1) and not truncated and not info["TimeLimit.truncated"]
            assert info["macro_native_steps"] == 30 and np.isfinite(obs).all()
        assert info["native_truncated"] and not info["native_terminated"]
        assert total == pytest.approx(sum(macro.rewards), abs=1e-12)
        native_rewards = np.asarray(macro.rewards)
        native_metrics = np.asarray(macro.metrics)
        hashes = macro.observer.digests()
        assert info["native_episode"]["service_snapshot_calls"] > 0
        assert info["native_episode"]["proposal_different_from_current_state_D_member_ticks"] == 0
        final, meta = macro.reset()
        assert not final.any() and meta == {"schedule_exhausted": True}
        with pytest.raises(RuntimeError, match="ended"):
            macro.step(np.zeros(8, dtype=np.int64))
        progress = json.loads((tmp_path/"training/lane0.progress.json").read_text())
        assert not progress["current_controller_work"]
        assert progress["completed_controller_work"]["service_snapshot_calls"] == info["native_episode"]["service_snapshot_calls"]
        assert macro.counts()["native_steps"] == 60
    finally:
        macro.close()
    config = make_eval_config(60, POLICY_SEED)
    env, model = make_env(config, seed), make_env(config, 0)
    try:
        model.reset(seed=0)
        observer = PlacementObserver(env.env)
        _, arrays = evaluate_world(PlacementController("R", env, model), env, config, seed,
                                  PRODUCTION_PARAMS, observer=observer)
        np.testing.assert_array_equal(native_rewards, arrays["reward"])
        np.testing.assert_array_equal(native_metrics, arrays["metrics"])
        assert observer.digests() == hashes
    finally:
        env.close()
        model.close()


def short_lane(lane):
    torch.set_num_threads(1)
    return NativeMacroEnv((62999101+lane,), lane=lane, horizon=60)


def test_actual_subprocess_audit_requested_actions_no_bootstrap(tmp_path, monkeypatch):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv
    monkeypatch.setattr(training, "ROLLOUT_STEPS", 2)
    monkeypatch.setattr(training, "HORIZON", 60)
    (tmp_path/"training").mkdir()
    torch.set_num_threads(1)
    vec = SubprocVecEnv([partial(short_lane, i) for i in range(2)], start_method="spawn")
    try:
        params = training.PPO_PARAMS | {"n_steps": 2, "batch_size": 4, "n_epochs": 1}
        model = PPO(PathPolicy, vec, **params, policy_kwargs={"net_arch": {"pi": [128, 128], "vf": [128, 128]},
                                                          "activation_fn": torch.nn.Tanh})
        with torch.no_grad():
            model.policy.value_net.bias.fill_(123.0)
        audit = training.TrainingAudit(tmp_path)
        model.learn(total_timesteps=4, callback=audit)
        assert audit.rollouts == audit.loss_rows == 1 and audit.native_steps == 120
        assert audit.exposure_rows == 4 and training.optimizer_steps(model.policy) == 1
        assert all(row["exhausted"] for row in vec.env_method("counts"))
        exposures = [json.loads(line) for line in (tmp_path/"training/exposure.jsonl").read_text().splitlines()]
        assert all(len(row["requested_modes"]) == 8 for row in exposures)
        assert np.isfinite(model.rollout_buffer.returns).all()
    finally:
        vec.close()


def test_readout_rejects_missing_duplicate_unpaired_or_short_world():
    seeds = (1, 2)
    jobs = [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"} for arm in ARMS for seed in seeds]
    keys = [job["job_key"] for job in jobs]
    rows = [job | {"status": "completed", "actual_length": 3000, "raw_native_J": float(ARMS.index(job["arm"])),
                   "qos_per_step": .1*ARMS.index(job["arm"]), "episode_minimum_battery_ratio": .2,
                   **{name: str(job["seed"]) for name in PAIR_HASHES}} for job in jobs]
    result = summarize(rows, seeds, keys)
    assert result["status"] == "complete"
    assert result["contrasts"]["L_minus_O"]["metrics"]["raw_native_J"]["mean"] == -1
    for broken in (rows[:-1], rows+[rows[0]], [rows[0] | {"actual_length": 30}]+rows[1:],
                   [rows[0] | {PAIR_HASHES[0]: "changed"}]+rows[1:]):
        result = summarize(broken, seeds, keys)
        assert result["status"] == "incomplete" and result["contrasts"] == {}


def test_real_ordinary_and_reference_output_binding(tmp_path):
    (tmp_path/"raw").mkdir()
    rows = [runner.simulate_world({"arm": arm, "seed": 62999201, "job_key": f"{arm}/62999201"},
                                 tmp_path, config=make_eval_config(30, POLICY_SEED))
            for arm in ("O", "R", "P")]
    assert all(row["status"] == "completed" for row in rows), rows
    assert all(row["actual_length"] == 30 for row in rows)
    assert all(len({row[field] for row in rows}) == 1 for field in PAIR_HASHES)
    assert rows[0]["transition_snapshot_calls"] > 0
    assert rows[1]["transition_snapshot_calls"] == 0
    assert rows[2]["planner_windows"] == 3
    for row in rows:
        with np.load(tmp_path/row["raw_path"], allow_pickle=False) as raw:
            assert raw["physical_xyz_m"].shape == (31, 8, 3)
            assert raw["metrics"].shape[0] == 30


def test_failed_fit_preserves_cost_and_does_not_evaluate(tmp_path, monkeypatch):
    def failed(out):
        (out/"training").mkdir()
        result = {"status": "incomplete", "fits_started": 1, "recorded_native_step_lower_bound": 120,
                  "recorded_controller_work_lower_bound": {"service_snapshot_calls": 400, "prediction_team_ticks": 3000},
                  "worker_cpu_seconds_sum": 1.0, "worker_wall_seconds_sum": 2.0}
        (out/"training.json").write_text(json.dumps(result))
        return result
    monkeypatch.setattr(runner, "train", failed)
    monkeypatch.setattr(runner, "execute_bounded", lambda *args, **kwargs: pytest.fail("failed fit launched evaluation"))
    result = runner.run(tmp_path/"batch", "test-only")
    assert result["status"] == "incomplete" and result["known_native_step_lower_bound"] == 120
    assert result["service_snapshot_calls"] == 400 and result["submitted_jobs"] == []
    assert len(result["unstarted_jobs"]) == 32 and result["contrasts"] == {}
    assert (tmp_path/"batch/manifest.json").exists()


def test_entry_rejects_before_scientific_artifacts(tmp_path, monkeypatch):
    import scripts.hmasd_admission
    monkeypatch.setattr(scripts.hmasd_admission, "require_admission",
                        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("admission rejected")))
    with pytest.raises(RuntimeError, match="admission rejected"):
        run_b01.main(["--out", str(tmp_path/"absent"), "--seed", "62092801", "--launch-sha", "test-only"])
    assert not (tmp_path/"absent").exists()

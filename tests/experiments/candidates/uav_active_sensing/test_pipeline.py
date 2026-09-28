from __future__ import annotations

from functools import partial
import json

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world, make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_active_sensing import batch, run_b02, training
from experiments.candidates.uav_active_sensing import macro_env as macro_module
from experiments.candidates.uav_active_sensing.controllers import FEATURE_DIM, SensingController
from experiments.candidates.uav_active_sensing.macro_env import (
    EVAL_SEEDS, POLICY_SEED, TRAIN_SEEDS, NativeMacroEnv, lane_seeds,
)
from experiments.candidates.uav_active_sensing.readout import ARMS, summarize
from experiments.candidates.uav_information_value.b02.controller import StationPriorController
from experiments.candidates.uav_active_sensing.policy import SemanticPolicy
from experiments.candidates.uav_service_auxiliary.b01.native import _rng_state, make_env


def test_fixed_counts_seeds_and_comparators():
    assert len(TRAIN_SEEDS) == 160
    assert set().union(*(set(lane_seeds(i)) for i in range(4))) == set(TRAIN_SEEDS)
    assert all(len(lane_seeds(i)) == 40 for i in range(4))
    assert not set(TRAIN_SEEDS) & set(EVAL_SEEDS)
    assert not set(EVAL_SEEDS) & {POLICY_SEED}
    assert len(batch.plan()) == 64
    assert ARMS == ("L0", "L1", "A", "R50")
    assert training.PPO_PARAMS["gamma"] == 1
    assert training.TOTAL_MACRO_STEPS == 16000
    assert training.OPTIMIZER_STEPS == 1600
    assert training.TOTAL_MACRO_STEPS * 30 + len(batch.plan()) * 3000 == 672000
    assert training.PPO_PARAMS["ent_coef"] == 0
    with pytest.raises(ValueError):
        lane_seeds(4)


def test_native_macro_matches_lawful_prior_service_and_exhaustion(monkeypatch):
    torch.set_num_threads(1)
    seed = 28179001
    macro = NativeMacroEnv((seed,), horizon=60)
    try:
        first, info = macro.reset(seed=12345)
        assert info["world_seed"] == seed
        assert first.shape == (FEATURE_DIM,)
        observed_displacements = []
        original_step = macro.native.step

        def tracked_step(actions):
            before = macro.native.env.uav_positions.copy()
            result = original_step(actions)
            observed_displacements.append(np.linalg.norm(macro.native.env.uav_positions - before, axis=1))
            return result

        monkeypatch.setattr(macro.native, "step", tracked_step)
        with pytest.raises(RuntimeError, match="before its end"):
            macro.reset()
        rewards = []
        for index in range(2):
            obs, reward, terminated, truncated, info = macro.step(0)
            rewards.append(reward)
            assert np.isfinite(obs).all()
            assert truncated is False
            assert info["TimeLimit.truncated"] is False
            assert info["macro_native_steps"] == 30
            assert terminated == (index == 1)
        assert info["native_truncated"] is True
        assert info["native_terminated"] is False
        assert sum(rewards) == pytest.approx(sum(macro.rewards), abs=1e-12)
        native_rewards = np.asarray(macro.rewards)
        native_metrics = np.asarray(macro.metrics)
        native_modes = np.asarray(macro.steps["mode"])
        np.testing.assert_array_equal(macro.steps["actual_travel_m"], observed_displacements)
        assert len(observed_displacements) == 60 and np.sum(observed_displacements[-1]) > 0
        assert info["native_episode"]["actual_team_travel_m"] == pytest.approx(np.sum(observed_displacements))
        assert macro.counts()["native_steps"] == 60
        terminal_obs, info = macro.reset(seed=999)
        assert info == {"schedule_exhausted": True}
        assert not np.any(terminal_obs)
        with pytest.raises(RuntimeError, match="ended"):
            macro.step(0)
        assert macro.counts()["episodes_started"] == 1
    finally:
        macro.close()
    config = make_eval_config(60, POLICY_SEED)
    env = make_env(config, seed)
    try:
        row, arrays = evaluate_world(StationPriorController(), env, config, seed, PRODUCTION_PARAMS)
    finally:
        env.close()
    assert row["actual_length"] == 60
    np.testing.assert_array_equal(native_rewards, arrays["reward"])
    np.testing.assert_array_equal(native_metrics, arrays["metrics"])
    np.testing.assert_array_equal(native_modes, arrays["mode"])


def test_observer_is_read_only_and_preserves_native_rng():
    torch.set_num_threads(1)
    seed = 28179002
    traces, states = [], []
    for observed in (False, True):
        config = make_eval_config(60, POLICY_SEED)
        env = make_env(config, seed)
        try:
            observer = batch.SensingObserver(env.env) if observed else None
            row, arrays = evaluate_world(SensingController("H"), env, config, seed,
                                          PRODUCTION_PARAMS, observer=observer)
            traces.append((row, arrays))
            states.append(_rng_state())
            if observed:
                assert len(observer.visible) == 60
                assert observer.arrays()["sense_visible_post"].shape == (60, 30)
                assert np.all(np.diff(observer.seen_counts) >= 0)
        finally:
            env.close()
    for key in traces[0][1]:
        np.testing.assert_array_equal(traces[0][1][key], traces[1][1][key])
    assert states[0]["python"] == states[1]["python"]
    np.testing.assert_array_equal(states[0]["numpy"][1], states[1]["numpy"][1])
    assert states[0]["numpy"][2:] == states[1]["numpy"][2:]
    assert torch.equal(states[0]["torch"], states[1]["torch"])


def test_second_lane_world_reconstructs_seeded_bs_and_native_path(monkeypatch):
    torch.set_num_threads(1)
    seeds = (28179201, 28179202)
    constructed = []
    original_factory = macro_module.make_env

    def tracked_factory(config, seed):
        constructed.append(seed)
        return original_factory(config, seed)

    monkeypatch.setattr(macro_module, "make_env", tracked_factory)
    macro = NativeMacroEnv(seeds, horizon=30)
    try:
        macro.reset()
        first_bs = macro.native.env.ground_bs_positions.copy()
        macro.step(0)
        macro.reset()
        second_obs = macro.observations.copy()
        second_bs = macro.native.env.ground_bs_positions.copy()
        macro.step(0)
        second_rewards = np.asarray(macro.rewards)
        second_metrics = np.asarray(macro.metrics)
        macro.reset()
        assert macro.exhausted
        assert constructed == list(seeds)
    finally:
        macro.close()
    config = make_eval_config(30, POLICY_SEED)
    fresh = make_env(config, seeds[1])
    try:
        observations, _ = fresh.reset(seed=seeds[1])
        np.testing.assert_array_equal(second_bs, fresh.env.ground_bs_positions)
        np.testing.assert_array_equal(second_obs, observations)
        assert not np.array_equal(first_bs, second_bs)
        _, arrays = evaluate_world(StationPriorController(), fresh, config, seeds[1], PRODUCTION_PARAMS)
        np.testing.assert_array_equal(second_rewards, arrays["reward"])
        np.testing.assert_array_equal(second_metrics, arrays["metrics"])
    finally:
        fresh.close()


def short_lane(lane):
    torch.set_num_threads(1)
    return NativeMacroEnv((28179101 + lane,), lane=lane, horizon=60)


def test_sb3_subprocess_complete_rollout_no_bootstrap_and_save_load(tmp_path, monkeypatch):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv

    # Exercise the actual audit with short nonpanel native fixtures, not a scientific fit.
    monkeypatch.setattr(training, "ROLLOUT_STEPS", 2)
    monkeypatch.setattr(training, "HORIZON", 60)
    (tmp_path / "training").mkdir()
    torch.set_num_threads(1)
    vec = SubprocVecEnv([partial(short_lane, i) for i in range(4)], start_method="spawn")
    try:
        params = training.PPO_PARAMS | {"n_steps": 2, "batch_size": 8, "n_epochs": 1}
        model = PPO(SemanticPolicy, vec, **params,
                    policy_kwargs={"net_arch": {"pi": [128, 128], "vf": [128, 128]},
                                   "activation_fn": torch.nn.Tanh, "ortho_init": True})
        with torch.no_grad():
            model.policy.value_net.bias.fill_(123.0)
        audit = training.TrainingAudit(tmp_path)
        model.learn(total_timesteps=8, callback=audit)
        assert audit.rollouts == audit.loss_rows == 1
        assert audit.native_steps == 240
        assert audit.exposure_rows == 8
        exposure = [json.loads(line) for line in (tmp_path / "training" / "exposure.jsonl").read_text().splitlines()]
        assert all(row["service_probability"] == .5 for row in exposure)
        assert all(info["native_truncated"] and not info["native_terminated"] for info in audit.locals["infos"])
        assert json.loads((tmp_path / "training" / "updates.jsonl").read_text())["optimizer_steps"] == 1
        assert training.optimizer_steps(model.policy) == 1
        counts = vec.env_method("counts")
        assert all(row["native_steps"] == 60 and row["episodes_started"] == 1 and row["exhausted"] for row in counts)
        features = np.zeros((4, FEATURE_DIM), dtype=np.float32)
        expected, _ = model.predict(features, deterministic=True)
        model.save(tmp_path / "policy.zip")
        loaded = PPO.load(tmp_path / "policy.zip", device="cpu")
        assert training.fingerprint(model.policy) == training.fingerprint(loaded.policy)
        actual, _ = loaded.predict(features, deterministic=True)
        np.testing.assert_array_equal(expected, actual)
        assert np.isfinite(loaded.policy.predict_values(torch.from_numpy(features)).detach().numpy()).all()
    finally:
        vec.close()


def fake_rows():
    jobs = [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"} for seed in (1, 2) for arm in ARMS]
    rows = [job | {"status": "completed", "actual_length": 3000, "terminal_type": "truncated",
                   "raw_native_J": 10.0 + ARMS.index(job["arm"]) + job["seed"],
                   "qos_per_step": .2 + .01 * ARMS.index(job["arm"]), "zero_service": False}
            for job in jobs]
    return jobs, rows


def test_readout_requires_complete_same_world_panel():
    jobs, rows = fake_rows()
    result = summarize(rows, jobs)
    assert result["status"] == "complete"
    assert result["contrasts"]["raw_native_J"]["L1-L0"]["mean"] == 1
    assert result["n_train"] == 1
    assert summarize(rows[:-1], jobs)["contrasts"] == {}
    short = [dict(row) for row in rows]
    short[0]["actual_length"] = 30
    assert summarize(short, jobs)["status"] == "incomplete"
    assert summarize(short, jobs)["contrasts"] == {}
    with pytest.raises(ValueError, match="duplicate"):
        summarize(rows + [rows[0]], jobs)


def test_failed_training_prevents_evaluation_and_preserves_cost(tmp_path, monkeypatch):
    def failed(out):
        (out / "training").mkdir()
        result = {"status": "incomplete", "fits_started": 1, "recorded_native_step_lower_bound": 120}
        (out / "training.json").write_text(json.dumps(result))
        return result

    monkeypatch.setattr(batch, "train", failed)
    monkeypatch.setattr(batch, "execute_bounded", lambda *args, **kwargs: pytest.fail("failed fit launched evaluation"))
    result = batch.run(tmp_path / "batch", "test-only")
    assert result["status"] == "incomplete"
    assert result["known_native_step_lower_bound"] == 120
    assert result["contrasts"] == {}
    assert result["submitted_jobs"] == []
    assert len(result["unstarted_jobs"]) == 64
    assert (tmp_path / "batch" / "manifest.json").exists()


def test_entry_requires_admission_before_scientific_outputs(tmp_path, monkeypatch):
    import scripts.hmasd_admission

    def rejected(*args, **kwargs):
        raise RuntimeError("test admission rejection")

    monkeypatch.setattr(scripts.hmasd_admission, "require_admission", rejected)
    with pytest.raises(RuntimeError, match="admission rejection"):
        run_b02.main(["--out", str(tmp_path / "absent"), "--launch-sha", "test-only"])
    assert not (tmp_path / "absent").exists()

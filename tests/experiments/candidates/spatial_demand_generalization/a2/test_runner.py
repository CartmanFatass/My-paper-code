"""Prospective A2 schedule and real tiny native-path checks."""

from dataclasses import replace
import json

import numpy as np

from experiments.candidates.spatial_demand_generalization.a2.adapter import make_envs
from experiments.candidates.spatial_demand_generalization.a2 import runner as a2


def test_fixed_schedule_and_production_counts():
    assert a2.PRODUCTION_SPEC.horizon == 500
    assert a2.PRODUCTION_SPEC.train_lanes == 16
    assert a2.PRODUCTION_SPEC.rollouts == 45
    for r in range(45):
        u = a2.training_families("U", r, 16)
        m = a2.training_families("M", r, 16)
        assert u == ("uniform",) * 16
        assert m.count("uniform") == m.count("cluster") == 8
        assert all(m[lane] == ("uniform" if (lane + r) % 16 < 8 else "cluster")
                   for lane in range(16))
    assert all(sum(a2.training_families("M", r, 16)[lane] == "uniform"
                   for r in range(45)) in (21, 22, 23, 24) for lane in range(16))
    counts = a2._expected_arm_counts(a2.SCHEDULES["U"], a2.PRODUCTION_SPEC)
    reused = a2._expected_arm_counts(a2.SCHEDULES["M"], a2.PRODUCTION_SPEC,
                                     common_stage0=True)
    assert counts["training_team_steps"] + reused["training_team_steps"] == 720_000
    assert counts["evaluation_team_steps"] + reused["evaluation_team_steps"] == 144_000
    assert counts["training_uav_steps"] + reused["training_uav_steps"] + \
        counts["evaluation_uav_steps"] + reused["evaluation_uav_steps"] == 5_184_000


def test_native_family_worlds_and_common_seed_geometry():
    seeds = [270000001, 270000002, 270000003]
    envs = make_envs(a2.EVALUATION_ORDER, seeds, 10)
    try:
        pairs = [env.reset(seed=seed) for env, seed in zip(envs, seeds)]
        for family, env, pair in zip(a2.EVALUATION_ORDER, envs, pairs):
            assert env.env.env.user_distribution == family
            assert pair[0].shape == (6, 104)
            assert pair[1]["state"].shape == (133,)
            assert env.env.env.max_connections == 10
        copy = make_envs(("uniform",), seeds[:1], 10)
        try:
            observation, info = copy[0].reset(seed=seeds[0])
            np.testing.assert_array_equal(observation, pairs[0][0])
            np.testing.assert_array_equal(info["state"], pairs[0][1]["state"])
            np.testing.assert_array_equal(copy[0].env.env.user_positions,
                                          envs[0].env.env.user_positions)
        finally:
            copy[0].close()
    finally:
        for env in envs:
            env.close()


def _tiny_spec():
    return replace(a2.PRODUCTION_SPEC, horizon=20, train_lanes=16, eval_lanes=2,
                   rollouts=2, panels=(0, 2), hidden_size=32, n_heads=4,
                   n_layers=1, ppo_epochs=1, sequence_batch_size=4)


def _fault_spec():
    return replace(_tiny_spec(), horizon=10, train_lanes=2)


def test_real_small_batch_storage_update_and_eval_isolation(tmp_path):
    out = tmp_path / a2.TAG
    entry_checks = []

    def observe_runtime_entries(agent):
        original_step = agent.step
        calls = 0

        def audited_step(states, observations, steps, dones, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 21:
                assert np.array_equal(steps, np.zeros(16, dtype=np.int64))
                assert np.array_equal(dones, np.ones(16, dtype=bool))
                assert not np.any(agent.rollout_buffer.env_lengths)
                for name in ("actor_hidden_np", "critic_hidden_np"):
                    hidden = getattr(agent, name)
                    assert hidden is None or not np.any(hidden)
                entry_checks.append(True)
            return original_step(states, observations, steps, dones, *args, **kwargs)

        agent.step = audited_step

    code = a2.run_batch(out, "technical-sha", {"sha": "technical-sha"},
                        spec=_tiny_spec(), technical_seed=270000101,
                        schedules={"U": (6, 6), "M": (6, 6)},
                        agent_setup_hook=observe_runtime_entries)
    assert code == 0, (out / "error.txt").read_text() if (out / "error.txt").exists() else ""
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete"
    assert summary["counts"]["training_team_steps"] == 1_280
    assert summary["counts"]["evaluation_team_steps"] == 360
    assert summary["counts"]["evaluation_optimizer_calls"] == 0
    assert all(value for key, value in summary["initial_identity"].items()
               if key.endswith("_equal"))
    assert summary["common_training_world_identity"]["all_equal"]
    assert len(entry_checks) == 2
    assert set(summary["readings"]["by_family"]) == set(a2.EVALUATION_ORDER)
    panel = json.loads((out / "U/panel_stage02_hotspot.json").read_text())
    with np.load(out / "U/raw/trace_stage02_hotspot.npz", allow_pickle=False) as trace:
        j = 6 * trace["scalar_reward"].mean(axis=0)
        native_j = (.7 * trace["coverage_reward"] + .3 * trace["quality_reward"]
                    - trace["energy_penalty"]).mean(axis=0)
        served = trace["connections"].any(axis=2).sum(axis=2).mean(axis=0)
        eligible = trace["eligible_links"].any(axis=2).sum(axis=2).mean(axis=0)
        np.testing.assert_allclose(j, native_j, atol=1e-7, rtol=1e-6)
        np.testing.assert_allclose(j, panel["J"], atol=1e-7, rtol=1e-6)
        np.testing.assert_allclose(served, panel["service_arrays"]["S_served_users_per_step"])
        np.testing.assert_allclose(eligible, panel["service_arrays"]["E_eligible_users_per_step"])
    for arm in ("U", "M"):
        row = json.loads((out / arm / "summary.json").read_text())
        assert row["counts"]["updates"] == 2
        expected_families = {"U": (640, 0), "M": (320, 320)}[arm]
        assert tuple(row["training_exposure_by_family"][family]["team_steps"]
                     for family in ("uniform", "cluster")) == expected_families
        with np.load(out / arm / "raw/training_reset_r01_n6.npz", allow_pickle=False) as scene:
            assert tuple(scene["families"]) == a2.training_families(arm, 0, 16)
        with np.load(out / arm / "raw/training_reset_r02_n6.npz", allow_pickle=False) as scene:
            assert tuple(scene["families"]) == a2.training_families(arm, 1, 16)
        assert row["optimizer_calls"]["discoverer_actor"] > 0
        assert row["optimizer_calls"]["discoverer_critic"] > 0
        assert row["optimizer_calls"]["discoverer_actor"] == sum(
            rollout["sampler"]["recurrent_minibatches"] for rollout in row["rollouts"])
        assert all(rollout["sampler"]["dropped_time_tail_steps"] == 0
                   for rollout in row["rollouts"])
        assert row["counts"]["evaluation_storage_calls"] == 0
        assert all(value for key, value in row["stage_isolation"]["2"].items()
                   if key.endswith("_preserved"))
        assert len(row["training_reset_scenes"]) == 2
        assert len(row["boundaries"]) == 1
        assert row["boundaries"][0]["runtime_reset_lanes"] == 16
        assert all(value for key, value in row["boundaries"][0].items()
                   if key.endswith("_preserved"))
        training_rows = [json.loads(line) for line in
                         (out / arm / "raw/training.jsonl").read_text().splitlines()]
        assert len(training_rows) == 2
        for training_row in training_rows:
            motion = training_row["action_motion_telemetry"]
            assert motion["policy_output_unchanged"] and motion["old_logprob_unchanged"]
            assert motion["diagnostic_rng_unchanged"]


def test_fault_retains_reset_before_step_and_partial_counts(tmp_path):
    out = tmp_path / a2.TAG

    def fail_after_step(event):
        raise RuntimeError("injected after first native step")

    code = a2.run_batch(out, "technical-sha", {"sha": "technical-sha"},
                        spec=_fault_spec(), technical_seed=270000102,
                        schedules={"U": (6, 6), "M": (6, 6)},
                        training_step_hook=fail_after_step)
    assert code == 1
    summary = json.loads((out / "summary.json").read_text())
    u = json.loads((out / "U/summary.json").read_text())
    assert summary["status"] == "failed" and summary["arms"]["M"]["status"] == "unstarted"
    assert u["counts"]["training_team_steps"] == 1
    assert u["incomplete_rollout"]["phase"].endswith("failed")
    assert (out / "U/raw/training_reset_r01_n6.npz").exists()
    assert u["training_reset_scenes"][0]["sha256"] == a2.b15.file_sha256(
        out / "U/raw/training_reset_r01_n6.npz")


def test_pre_step_fault_keeps_actual_reset_and_zero_fit(tmp_path):
    out = tmp_path / a2.TAG

    def reject_first_policy_step(agent):
        def failed_step(*args, **kwargs):
            raise RuntimeError("injected before first transition")
        agent.step = failed_step

    code = a2.run_batch(out, "technical-sha", {"sha": "technical-sha"},
                        spec=_fault_spec(), technical_seed=270000103,
                        schedules={"U": (6, 6), "M": (6, 6)},
                        agent_setup_hook=reject_first_policy_step)
    assert code == 1
    summary = json.loads((out / "summary.json").read_text())
    u = json.loads((out / "U/summary.json").read_text())
    assert summary["status"] == "failed"
    assert u["counts"]["training_team_steps"] == u["counts"]["fits"] == 0
    assert u["incomplete_rollout"]["phase"].endswith("failed")
    scene = out / "U/raw/training_reset_r01_n6.npz"
    assert scene.exists() and u["training_reset_scenes"][0]["sha256"] == a2.b15.file_sha256(scene)

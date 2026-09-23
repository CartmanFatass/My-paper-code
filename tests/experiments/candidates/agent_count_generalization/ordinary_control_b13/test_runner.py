"""Focused checks for the fixed B13 four-policy common evaluator."""
from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.action_law_b02.probe import (
    _normalizer_record,
    restore_checkpoint,
)
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.ordinary_control_b13 import runner
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    digest_agent,
    optimizer_counts,
    reset_all,
    save_checkpoint,
    seed_rng,
)
from scripts import run_agent_count_ordinary_control_b13 as entry


TECH_FIT = replace(
    DEFAULT_SPEC, horizon=10, train_lanes=2, eval_lanes=32, rollouts=1,
    panels=(1,), test_ns=(8, 6), hidden_size=16, n_heads=2, n_layers=1,
    ppo_epochs=1, sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1,
)


def _technical_config(arm: str, lanes: int, n: int, seed: int, root: Path):
    envs = make_envs(lanes, 71_000, n, TECH_FIT.horizon)
    try:
        seed_rng(seed)
        config = make_config(arm, envs, seed, TECH_FIT)
        if arm == "SET":
            config.lambda_l = config.lambda_l_initial = config.lambda_l_final = .05
            config.use_entropy_annealing = False
            config.use_entropy_targets = False
            config.validate_config()
        return config
    finally:
        for env in envs:
            env.close()


def _technical_payload(arm: str, tmp_path: Path):
    seed = 8101 if arm == "H6" else 8102
    config = _technical_config(arm, 16, 6, seed, tmp_path)
    seed_rng(seed)
    agent = build_agent(config, str(tmp_path / f"source_{arm}"))
    checkpoint_root = tmp_path / f"checkpoint_{arm}"
    checkpoint_root.mkdir()
    record = save_checkpoint(agent, checkpoint_root, 45, config, "technical-source")
    checkpoint = checkpoint_root / record["path"]
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    summary = {"config": config_dict(config)}
    asset = runner.AssetSpec(
        arm.lower(), arm, seed, f"technical_{arm}", "technical-source", "technical", "cell",
        "0" * 64, record["sha256"], record["bytes"], digest_agent(agent),
    )
    return asset, summary, payload, checkpoint, agent


def _restored_target(arm: str, lanes: int, n: int, seed: int, payload: dict, root: Path):
    config = _technical_config(arm, lanes, n, seed, root)
    seed_rng(seed + lanes + n)
    target = build_agent(config, str(root / f"target_{arm}_{lanes}_{n}"))
    restore_checkpoint(target, payload)
    return target


def test_fixed_assets_worlds_exposure_and_hashes():
    assert [(asset.key, asset.arm, asset.seed) for asset in runner.ASSETS] == [
        ("s1", "SET", 963201), ("s2", "SET", 963401),
        ("h1", "H6", 942201), ("h2", "H6", 952201),
    ]
    assert [asset.checkpoint_sha256 for asset in runner.ASSETS] == [
        "36f6bc8afbc414df1f84c2b414180821bf30e14b90d7f44928db35ce2ab74c0a",
        "34987032207299209832a9fcaa6dcd807a3cc00e5b4682725a8b52d0ca89c8d3",
        "98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343",
        "6d71f3023e5593a801b4d618f7eece93df1a15575f8a71d769566190ba6498df",
    ]
    assert runner._world_seed(8) == 1_645_800
    assert runner._world_seed(6) == 1_645_600
    assert runner._expected_counts(runner.DEFAULT_SPEC) == {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": 8, "evaluation_team_steps": 128000,
        "evaluation_uav_steps": 896000, "evaluation_episodes": 256,
        "evaluation_resets": 256, "batched_policy_step_calls": 4000,
        "h6_coordinator_batched_calls": 200, "h6_lane_assignments": 6400,
    }


def test_bad_checkpoint_hash_is_rejected_before_deserialization(tmp_path):
    bad = tmp_path / "checkpoint.pt"
    bad.write_bytes(b"not a checkpoint")
    paths = {asset.key: bad for asset in runner.ASSETS}
    with pytest.raises(ValueError, match="checkpoint byte-size mismatch for s1"):
        runner.load_assets(paths)


def test_local_bound_assets_use_original_configs_and_strictly_restore(tmp_path):
    run_root = runner.REPOSITORY_ROOT / "runs" / "agent_count_generalization"
    checkpoints = {asset.key: run_root / asset.tag / "checkpoint_45.pt" for asset in runner.ASSETS}
    if not all(path.is_file() for path in checkpoints.values()):
        pytest.skip("bound native checkpoint files are staged only for B13 execution/review")
    records = runner.load_assets(
        checkpoints, restore_log_root=tmp_path / "restore_logs", construction_seed=17,
    )
    observed_entropy = {}
    for record in records:
        for n in runner.EVALUATION_ORDER:
            evidence = record.restore_validation[n]
            config = evidence["config"]
            assert evidence["restored_digest"] == record.spec.final_digest
            assert not any(evidence["rollout_storage_env_lengths"])
            observed_entropy.setdefault(record.spec.key, (
                float(config["lambda_l_initial"]), float(config["lambda_l_final"]),
                bool(config["use_entropy_annealing"]), bool(config["use_entropy_targets"]),
            ))
    assert observed_entropy["h1"] == (.05, .01, False, False)
    assert observed_entropy["h2"] == (.05, .05, False, False)
    assert observed_entropy["s1"] == observed_entropy["s2"] == (.05, .05, False, False)


@pytest.mark.parametrize("arm", ["H6", "SET"])
@pytest.mark.parametrize("damage", ["identity", "config", "module", "normalizer"])
def test_payload_identity_config_module_and_normalizer_rejections(tmp_path, arm, damage):
    asset, summary, payload, _checkpoint, _agent = _technical_payload(arm, tmp_path)
    damaged = copy.deepcopy(payload)
    if damage == "identity":
        damaged["rollout"] = 44
    elif damage == "config":
        damaged["config"]["seed"] += 1
    elif damage == "module":
        damaged["modules"].pop(next(iter(damaged["modules"])))
    else:
        damaged["normalizers"].pop("obs_norm")
    with pytest.raises(ValueError, match={
        "identity": "identity/stage", "config": "checkpoint/source config",
        "module": "module set", "normalizer": "normalizer set",
    }[damage]):
        runner._validate_payload(asset, damaged, summary)


@pytest.mark.parametrize("arm", ["H6", "SET"])
def test_strict_restore_recovers_both_arm_module_sets_and_normalizers(tmp_path, arm):
    asset, summary, payload, _checkpoint, source = _technical_payload(arm, tmp_path)
    runner._validate_payload(asset, payload, summary)
    target = _restored_target(arm, 32, 8, asset.seed, payload, tmp_path)
    assert digest_agent(target) == digest_agent(source) == asset.final_digest
    assert _normalizer_record(target) == _normalizer_record(source)
    expected = (
        {"skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"}
        if arm == "H6" else {"skill_coordinator", "skill_discoverer"}
    )
    assert set(payload["modules"]) == expected


def _coordinator_output(agent, states, observations):
    with torch.no_grad():
        return agent.skill_coordinator.assign_and_value_batch(
            torch.as_tensor(states), torch.as_tensor(observations), deterministic=True,
        )


def _ten_steps(agent, states, observations, *, counted):
    counter = runner._InferenceCounter(agent, "H6", agent.config.n_agents) if counted else None
    actions, choices = [], []
    steps = np.zeros(states.shape[0], dtype=np.int64)
    dones = np.zeros(states.shape[0], dtype=bool)
    try:
        with torch.no_grad():
            for t in range(10):
                action, _logp, data = agent.step(
                    states, observations, steps, dones, deterministic=True,
                    return_step_data=True, build_infos=False,
                )
                if counter is not None:
                    counter.observe_choices(data)
                actions.append(action.copy())
                choices.append((data["team_skills"].copy(), data["agent_skills"].copy()))
                steps += 1
        evidence = counter.finish(runner.EvalSpec(horizon=10, eval_lanes=32, torch_threads=1)) \
            if counter is not None else None
        return actions, choices, evidence
    finally:
        if counter is not None:
            counter.close()


def test_h6_deterministic_16_to_32_batch_and_counters_are_observational(tmp_path):
    asset, _summary, payload, _checkpoint, source = _technical_payload("H6", tmp_path)
    target16 = _restored_target("H6", 16, 6, asset.seed, payload, tmp_path)
    target32 = _restored_target("H6", 32, 6, asset.seed, payload, tmp_path)
    envs16 = make_envs(16, 72_000, 6, 10)
    envs32 = make_envs(32, 72_000, 6, 10)
    try:
        states16, observations16 = reset_all(envs16)
        states32, observations32 = reset_all(envs32)
        assert np.array_equal(states16, states32[:16])
        assert np.array_equal(observations16, observations32[:16])
        out16 = _coordinator_output(target16, states16, observations16)
        out32 = _coordinator_output(target32, states32, observations32)
        assert torch.equal(out16["team_skills"], out32["team_skills"][:16])
        assert torch.equal(out16["agent_skills"], out32["agent_skills"][:16])
        assert torch.allclose(out16["Z_logits"], out32["Z_logits"][:16], atol=1e-6, rtol=1e-6)
        for left, right in zip(out16["z_logits"], out32["z_logits"]):
            assert torch.allclose(left, right[:16], atol=1e-6, rtol=1e-6)

        for lane in range(16):
            target16.reset_env_state(lane)
        for lane in range(32):
            target32.reset_env_state(lane)
        seed_rng(8811)
        a16, _, d16 = target16.step(
            states16, observations16, np.zeros(16, dtype=np.int64),
            np.zeros(16, dtype=bool), deterministic=True, return_step_data=True, build_infos=False,
        )
        seed_rng(8811)
        a32, _, d32 = target32.step(
            states32, observations32, np.zeros(32, dtype=np.int64),
            np.zeros(32, dtype=bool), deterministic=True, return_step_data=True, build_infos=False,
        )
        assert a32.shape == (32, 6, 3)
        assert np.allclose(a16, a32[:16], atol=1e-6, rtol=1e-6)
        assert np.array_equal(d16["team_skills"], d32["team_skills"][:16])
        assert np.array_equal(d16["agent_skills"], d32["agent_skills"][:16])

        baseline = _restored_target("H6", 32, 6, asset.seed, payload, tmp_path)
        instrumented = _restored_target("H6", 32, 6, asset.seed, payload, tmp_path)
        before = digest_agent(instrumented)
        optimizer_calls, hooks = optimizer_counts(instrumented)
        seed_rng(9911)
        baseline_actions, baseline_choices, _ = _ten_steps(
            baseline, states32, observations32, counted=False,
        )
        baseline_rng = runner._rng_digest()
        seed_rng(9911)
        counted_actions, counted_choices, evidence = _ten_steps(
            instrumented, states32, observations32, counted=True,
        )
        counted_rng = runner._rng_digest()
        for hook in hooks:
            hook.remove()
        assert all(np.array_equal(left, right) for left, right in zip(baseline_actions, counted_actions))
        assert all(
            np.array_equal(lt, rt) and np.array_equal(li, ri)
            for (lt, li), (rt, ri) in zip(baseline_choices, counted_choices)
        )
        assert baseline_rng == counted_rng
        assert evidence["coordinator_batched_calls"] == 1
        assert evidence["coordinator_rows"] == 32
        assert evidence["decoder_team_calls"] == 1
        assert evidence["decoder_individual_calls"] == 6
        assert evidence["decoder_individual_rows"] == 192
        assert evidence["team_selections"] == 32
        assert evidence["individual_selections"] == 192
        assert len(instrumented.env_timers) == 32
        assert not any(optimizer_calls.values())
        assert digest_agent(instrumented) == before == asset.final_digest
        assert not np.any(instrumented.rollout_buffer.env_lengths)
        assert digest_agent(source) == asset.final_digest
    finally:
        for env in (*envs16, *envs32):
            env.close()


def _panel(key: str, n: int, offset: float) -> dict:
    worlds = [100 * n + i for i in range(3)]
    base = np.asarray([offset, offset + 1.0, offset - .5], dtype=np.float64)
    coverage = .4 + .01 * base
    quality = .2 + .02 * base
    penalty = .05 + .005 * base
    j = .7 * coverage + .3 * quality - penalty
    service = 50.0 * coverage
    eligible = service + np.asarray([1.0, 2.0, 3.0])
    return {
        "asset_key": key, "test_n": n, "world_seeds": worlds,
        "J": j.tolist(), "scalar_returns": (j * 500 / n).tolist(),
        "component_means": {
            "coverage_reward": coverage.tolist(), "quality_reward": quality.tolist(),
            "energy_penalty": penalty.tolist(), "total_reward": j.tolist(),
        },
        "service_arrays": {
            "E_eligible_users_per_step": eligible.tolist(),
            "S_served_users_per_step": service.tolist(),
            "U_eligible_unserved_users_per_step": (eligible - service).tolist(),
        },
    }


def test_complete_four_contrasts_and_algebraic_dependence():
    panels = []
    for n in (8, 6):
        for key, offset in (("s1", 0.0), ("s2", .25), ("h1", 1.0), ("h2", -.5)):
            panels.append(_panel(key, n, offset))
    result = runner.compute_readings(panels, (8, 6))
    assert result["cross_n_aggregate"] is None
    for n in (8, 6):
        row = result["by_test_n"][str(n)]
        assert set(row["absolute"]) == {"s1", "s2", "h1", "h2"}
        assert set(row["h6_minus_set_contrasts"]) == {
            "h1_minus_s1", "h1_minus_s2", "h2_minus_s1", "h2_minus_s2",
        }
        for contrast in row["h6_minus_set_contrasts"].values():
            assert set(contrast) == {"J", "C", "Q", "P", "E", "S", "U"}
            assert len(contrast["J"]["per_world"]) == 3
            assert set(contrast["J"]["signs"]) == {"positive", "zero", "negative"}
        assert all(
            value["all_within_roundoff_bound"]
            and value["max_abs_residual"] <= value["max_roundoff_bound"]
            for value in row["algebraic_dependence"].values()
        )
        assert set(row["worst_paired_J_S_losses"]["h1_minus_s2"]) == {"J", "S"}


def test_non_dyadic_four_contrast_residual_is_bounded_not_required_exact_zero():
    values = {"h1": .1, "s1": .2, "h2": .3, "s2": .4}
    panels = []
    for n in (8, 6):
        for key, value in values.items():
            row = _panel(key, n, value)
            row["J"] = [value, value, value]
            panels.append(row)
    result = runner.compute_readings(panels, (8, 6))
    for n in (8, 6):
        identity = result["by_test_n"][str(n)]["algebraic_dependence"]["J"]
        assert identity["max_abs_residual"] > 0.0
        assert identity["all_within_roundoff_bound"]
        assert identity["max_abs_residual"] <= identity["max_roundoff_bound"]


def test_set_reproduction_requires_all_arrays_and_integer_trace_exact():
    row = _panel("s1", 8, 0.0)
    row["status"] = "complete"
    trace = {
        "initial_states": np.zeros((3, 2), dtype=np.float32),
        "initial_observations": np.zeros((3, 8, 2), dtype=np.float32),
        "connections": np.zeros((2, 3, 8, 50), dtype=bool),
        "scalar_reward": np.zeros((2, 3), dtype=np.float64),
    }
    reference_panel = copy.deepcopy(row)
    record = SimpleNamespace(
        spec=SimpleNamespace(key="s1"), reference_panels={8: reference_panel},
        reference_traces={8: copy.deepcopy(trace)}, reference_identities={8: {"bound": True}},
    )
    matched = runner.compare_set_reproduction(row, trace, record, 8)
    assert matched["all_match"]
    trace["initial_states"][0, 0] = np.float32(1e-8)
    initial_mismatch = runner.compare_set_reproduction(row, trace, record, 8)
    assert not initial_mismatch["all_match"]
    initial_check = initial_mismatch["numeric_trace_arrays"]["initial_states"]
    assert not initial_check["match"] and initial_check["rule"] == "exact array equality"
    assert initial_check["max_abs_difference"] == pytest.approx(1e-8)
    trace["initial_states"][0, 0] = 0.0
    trace["connections"][0, 0, 0, 0] = True
    mismatch = runner.compare_set_reproduction(row, trace, record, 8)
    assert not mismatch["all_match"]
    assert not mismatch["numeric_trace_arrays"]["connections"]["match"]


def test_real_evaluate_policy_with_synthetic_runtime_writes_trace_counts_and_failure(
    monkeypatch, tmp_path,
):
    n, lanes, horizon = 8, 2, 10
    eval_spec = runner.EvalSpec(horizon=horizon, eval_lanes=lanes, torch_threads=1)
    coverage, quality, penalty = .4, .2, .05
    total = .7 * coverage + .3 * quality - penalty
    scalar = total / n

    class Decoder(torch.nn.Module):
        def forward(self, encoded_state, encoded_observations, *args, **kwargs):
            return torch.zeros(encoded_state.shape[0], 2)

    class FakeAgent:
        def __init__(self):
            self.config = SimpleNamespace(
                n_agents=n, n_uavs=n, n_users=50, n_Z=2, n_z=2,
                lambda_l=.05, lambda_l_initial=.05, lambda_l_final=.05,
                use_entropy_annealing=False, use_entropy_targets=False,
            )
            self.skill_coordinator = SimpleNamespace(
                encoder=torch.nn.Identity(), skill_decoder=Decoder(),
            )
            self.rollout_buffer = SimpleNamespace(env_lengths=np.zeros(lanes, dtype=np.int64))
            self.runtime_steps = 0
            for name in runner.NORMALIZERS:
                setattr(self, name, None)

        def train(self, _mode):
            return self

        def reset_env_state(self, _lane):
            return None

        def store_transition_batch(self, *args, **kwargs):
            raise AssertionError("unreachable original storage method")

        def step(
            self, states, observations, steps, dones, deterministic,
            return_step_data, build_infos,
        ):
            selected = (np.asarray(steps) % 10 == 0) | np.asarray(dones, dtype=bool)
            if selected.any():
                encoded = self.skill_coordinator.encoder(torch.as_tensor(states[selected]))
                selected_obs = torch.as_tensor(observations[selected])
                self.skill_coordinator.skill_decoder(encoded, selected_obs)
                for index in range(n):
                    self.skill_coordinator.skill_decoder(
                        encoded, selected_obs, step=index + 1,
                    )
            self.runtime_steps += 1
            data = {
                "skill_changed": selected,
                "team_skills": np.zeros(lanes, dtype=np.int64),
                "agent_skills": np.zeros((lanes, n), dtype=np.int64),
            }
            return np.zeros((lanes, n, 3), dtype=np.float32), None, data

    class FakeEnv:
        def __init__(self):
            sinr = np.full((n, 50), -1.0, dtype=np.float64)
            sinr[:, :25] = .1
            connections = np.zeros((n, 50), dtype=bool)
            connections[0, :10] = True
            connections[1, 10:20] = True
            sinr[connections] = 6.0
            self.native = SimpleNamespace(
                n_uavs=n, n_users=50, max_connections=10, min_sinr=0.0,
                sinr_matrix=sinr, connections=connections,
                uav_positions=np.tile(np.asarray([0.0, 0.0, 100.0]), (n, 1)),
                height_range=(50.0, 150.0),
            )
            self.env = SimpleNamespace(env=self.native)
            self.t = 0

        def reset(self):
            self.t = 0
            return np.zeros((n, 104), dtype=np.float32), {
                "state": np.zeros(133, dtype=np.float32),
            }

        def step(self, _actions):
            self.t += 1
            info = {
                "next_state": np.zeros(133, dtype=np.float32),
                "reward_components": {"reward_info": {
                    "coverage_reward": coverage, "quality_reward": quality,
                    "energy_penalty": penalty, "total_reward": total,
                }},
            }
            return (
                np.zeros((n, 104), dtype=np.float32), scalar,
                self.t == horizon, False, info,
            )

        def close(self):
            return None

    config = FakeAgent().config
    monkeypatch.setattr(runner, "make_envs", lambda count, *_args: [FakeEnv() for _ in range(count)])
    monkeypatch.setattr(runner, "_make_eval_config", lambda *_args: config)
    monkeypatch.setattr(runner, "build_agent", lambda *_args: FakeAgent())
    monkeypatch.setattr(runner, "restore_checkpoint", lambda *_args: None)
    monkeypatch.setattr(runner, "digest_agent", lambda _agent: "stable")
    monkeypatch.setattr(
        runner, "runtime_state_digest", lambda agent: f"runtime-{agent.runtime_steps}",
    )

    worlds = list(range(runner._world_seed(n), runner._world_seed(n) + lanes))
    reference_panel = {
        "world_seeds": worlds, "J": [total] * lanes,
        "scalar_returns": [horizon * scalar] * lanes,
        "component_means": {
            "coverage_reward": [coverage] * lanes, "quality_reward": [quality] * lanes,
            "energy_penalty": [penalty] * lanes, "total_reward": [total] * lanes,
        },
    }
    reference_trace = runner.b11._new_trace(eval_spec, n)
    reference_trace["initial_states"] = np.zeros((lanes, 133), dtype=np.float32)
    reference_trace["initial_observations"] = np.zeros((lanes, n, 104), dtype=np.float32)
    probe_env = FakeEnv()
    parts = {
        "coverage_reward": coverage, "quality_reward": quality,
        "energy_penalty": penalty, "total_reward": total,
    }
    for t in range(horizon):
        for lane in range(lanes):
            runner.b11._observe_post_transition(
                reference_trace, t, lane, probe_env, scalar, parts, n,
            )
    record = SimpleNamespace(
        spec=SimpleNamespace(key="s1", arm="SET", seed=1, final_digest="stable"),
        payload={}, reference_panels={n: reference_panel},
        reference_traces={n: reference_trace},
        reference_identities={n: {"panel": "synthetic", "trace": "synthetic"}},
    )
    counts = {"steps": 0, "episodes": 0, "calls": 0, "resets": 0}

    def progress(steps, episodes, _n, calls, resets):
        counts["steps"] += steps
        counts["episodes"] += episodes
        counts["calls"] += calls
        counts["resets"] += resets

    row = runner.evaluate_policy(record, n, tmp_path, eval_spec, 17, progress)
    assert row["status"] == "complete" and row["original_reproduction"]["all_match"]
    assert Path(row["trace"]["path"]).is_file()
    assert counts == {"steps": 20, "episodes": 2, "calls": 10, "resets": 2}
    assert row["inference_counts"]["coordinator_batched_calls"] == 1
    assert row["inference_counts"]["decoder_team_rows"] == lanes
    assert row["inference_counts"]["decoder_individual_rows"] == lanes * n
    assert row["inference_counts"]["set_snapshot_lane_refreshes"] == lanes
    assert row["training_storage_calls"] == 0
    assert not any(row["optimizer_calls"].values())
    assert not any(row["rollout_storage_env_lengths"])

    record.reference_traces[n] = copy.deepcopy(reference_trace)
    record.reference_traces[n]["initial_observations"][0, 0, 0] = np.float32(1e-8)
    with pytest.raises(runner.PanelFailure) as failure:
        runner.evaluate_policy(record, n, tmp_path, eval_spec, 17)
    failed = failure.value.row
    assert failed["status"] == "failed"
    check = failed["original_reproduction"]["numeric_trace_arrays"]["initial_observations"]
    assert not check["match"] and check["rule"] == "exact array equality"
    assert check["max_abs_difference"] == pytest.approx(1e-8)


def test_reproduction_failure_stops_before_h6_and_preserves_partial_row(monkeypatch, tmp_path):
    fake_records = [SimpleNamespace(
        spec=asset, summary_identity={"path": str(tmp_path / f"{asset.key}.json")},
        checkpoint=tmp_path / f"{asset.key}.pt", reference_identities={},
        restore_validation={},
    ) for asset in runner.ASSETS]
    monkeypatch.setattr(runner, "load_assets", lambda *_a, **_k: fake_records)
    monkeypatch.setattr(runner, "_input_identities", lambda _records: {"stable": True})

    calls = []

    def fail_s1(record, n, out, spec, construction_seed, progress):
        calls.append((record.spec.key, n))
        progress(1, 0, n, 1, spec.eval_lanes)
        row = {
            "status": "failed", "asset_key": record.spec.key, "arm": record.spec.arm,
            "seed": record.spec.seed, "policy_stage": 45, "test_n": n,
            "world_seeds": list(range(runner._world_seed(n), runner._world_seed(n) + spec.eval_lanes)),
            "J": [0.0] * spec.eval_lanes,
            "failure": "ValueError: injected SET reproduction mismatch",
            "original_reproduction": {"all_match": False},
        }
        raise runner.PanelFailure(row["failure"], row)

    out = tmp_path / runner.TAG
    assert runner.run_study(
        out, "technical", {"sha": "technical"},
        {asset.key: tmp_path / asset.key for asset in runner.ASSETS}, 17,
        committed_sources=False, evaluate_fn=fail_s1,
    ) == 1
    result = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert calls == [("s1", 8)]
    assert result["status"] == "failed" and result["readings"] is None
    assert len(result["panels"]) == 1
    assert result["panels"][0]["original_reproduction"] == {"all_match": False}
    assert result["counts"]["evaluation_team_steps"] == 1
    assert result["counts"]["evaluation_uav_steps"] == 8
    assert (out / "error.txt").is_file()


def test_cli_admission_precedes_runner_and_binds_four_paths(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        entry, "require_admission",
        lambda *_a, **_k: calls.append("admit") or {"sha": "x"},
    )
    paths = {key: tmp_path / f"{key}.pt" for key in ("s1", "s2", "h1", "h2")}
    result = entry.main([
        "--seed", "17", "--launch-sha", "x", "--out", str(tmp_path / runner.TAG),
        "--s1-checkpoint", str(paths["s1"]), "--s2-checkpoint", str(paths["s2"]),
        "--h1-checkpoint", str(paths["h1"]), "--h2-checkpoint", str(paths["h2"]),
    ], run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 9)
    assert result == 9 and calls[0] == "admit"
    args, kwargs = calls[1]
    assert args[4] == 17
    assert list(args[3]) == ["s1", "s2", "h1", "h2"]
    assert kwargs["command_start"] == entry.COMMAND_START


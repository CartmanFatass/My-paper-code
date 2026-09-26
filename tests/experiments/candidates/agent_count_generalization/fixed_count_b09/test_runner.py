"""Focused technical checks for the fixed B09 count-scalar evaluator."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.action_law_b02.probe import restore_checkpoint
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC, make_config
from experiments.candidates.agent_count_generalization.fixed_count_b09 import runner
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    digest_agent,
    native_components,
    optimizer_counts,
    reset_all,
    save_checkpoint,
    seed_rng,
)
from scripts import run_agent_count_fixed_count_b09 as entry


TECH_FIT = replace(
    DEFAULT_SPEC,
    horizon=12,
    train_lanes=2,
    eval_lanes=2,
    rollouts=1,
    panels=(0, 1),
    hidden_size=16,
    n_heads=2,
    n_layers=1,
    ppo_epochs=1,
    sequence_batch_size=4,
    coordinator_batch_size=2,
    torch_threads=1,
)
TECH_EVAL = runner.EvalSpec(horizon=12, eval_lanes=2, torch_threads=1)
OPTIMIZERS = (
    "coordinator", "discoverer_actor", "discoverer_critic",
    "team_discriminator", "individual_discriminator",
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config(arm: str, seed: int, n: int):
    envs = make_envs(TECH_EVAL.eval_lanes, runner._world_seed(n), n, TECH_EVAL.horizon)
    try:
        config = make_config(arm, envs, seed, TECH_FIT)
        config.lambda_l = config.lambda_l_initial = config.lambda_l_final = .05
        config.use_entropy_annealing = False
        config.use_entropy_targets = False
        config.validate_config()
        return config
    finally:
        for env in envs:
            env.close()


def _baseline_panel(payload: dict, arm: str, seed: int, n: int, root: Path) -> dict:
    world_seed = runner._world_seed(n)
    seed_rng(world_seed + 51)
    envs = make_envs(TECH_EVAL.eval_lanes, world_seed, n, TECH_EVAL.horizon)
    target, hooks = None, []
    try:
        config = _config(arm, seed, n)
        target = build_agent(config, str(root / "baseline_logs" / arm / str(n)))
        restore_checkpoint(target, payload)
        for lane in range(TECH_EVAL.eval_lanes):
            target.reset_env_state(lane)
        calls, hooks = optimizer_counts(target)
        states, observations = reset_all(envs)
        steps = np.zeros(TECH_EVAL.eval_lanes, dtype=np.int64)
        dones = np.zeros(TECH_EVAL.eval_lanes, dtype=bool)
        returns = np.zeros(TECH_EVAL.eval_lanes, dtype=np.float64)
        parts = {name: np.zeros(TECH_EVAL.eval_lanes, dtype=np.float64) for name in COMPONENTS}
        action_min, action_max = float("inf"), float("-inf")
        with torch.no_grad():
            for _t in range(TECH_EVAL.horizon):
                actions, _, _data = target.step(
                    states, observations, steps, dones, deterministic=True,
                    return_step_data=True, build_infos=False,
                )
                executed = np.clip(actions, -1.0, 1.0)
                action_min = min(action_min, float(executed.min()))
                action_max = max(action_max, float(executed.max()))
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    obs, reward, terminated, truncated, info = env.step(executed[lane])
                    dones[lane] = bool(terminated or truncated)
                    returns[lane] += reward
                    native = native_components(info, reward, n)
                    for name in COMPONENTS:
                        parts[name][lane] += native[name]
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                states, observations = np.stack(next_states), np.stack(next_observations)
                steps += 1
        means = {name: value / TECH_EVAL.horizon for name, value in parts.items()}
        j = n * returns / TECH_EVAL.horizon
        return {
            "after_rollout": 45,
            "training_team_steps": 45 * TECH_FIT.train_lanes * TECH_FIT.horizon,
            "test_n": n,
            "world_seeds": list(range(world_seed, world_seed + TECH_EVAL.eval_lanes)),
            "execution_law": "clip",
            "status": "complete",
            "steps": TECH_EVAL.eval_lanes * TECH_EVAL.horizon,
            "episodes": TECH_EVAL.eval_lanes,
            "J": j.tolist(),
            "scalar_returns": returns.tolist(),
            "component_means": runner.jsonable(means),
            "optimizer_calls": calls.copy(),
            "frozen_weights_and_normalizers": True,
            "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
            "config": runner.b08._config_record(config),
        }
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        del target


def _make_asset(root: Path, key: str, arm: str, seed: int, shift: float):
    tag = f"technical_b09_{key}"
    source = f"technical-source-{key}"
    config = _config(arm, seed, 6)
    seed_rng(seed)
    agent = build_agent(config, str(root / "agent_logs" / key))
    try:
        norm = agent.value_norm_discoverer
        norm.mean = np.asarray(2.0 + shift)
        norm.var = np.asarray(3.0 + abs(shift))
        norm.count = 11.0
        with torch.no_grad():
            next(agent.skill_discoverer.actor.parameters()).add_(shift)
        final_digest = digest_agent(agent)
        checkpoint_root = root / "checkpoints" / tag
        checkpoint_root.mkdir(parents=True)
        checkpoint_record = save_checkpoint(agent, checkpoint_root, 45, config, source)
    finally:
        del agent
    checkpoint = checkpoint_root / checkpoint_record["path"]
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    run_root = root / "summaries" / tag
    panels, panel_hashes = [], []
    for n in TECH_EVAL.test_ns:
        panel = _baseline_panel(payload, arm, seed, n, root)
        panel_path = run_root / f"panel_45_n{n}.json"
        _write(panel_path, panel)
        panels.append(panel)
        panel_hashes.append(_sha(panel_path))
    initial_digest = ("1" if key == "h6" else "2") * 64
    checkpoint00_digest = ("3" if key == "h6" else "4") * 64
    summary = {
        "schema": 1,
        "object_id": f"technical-object-{key}",
        "direction": "agent_count_generalization",
        "cell": {"key": f"{key}_l05", "tag": tag, "arm": arm, "law": "clip",
                 "seed": seed, "lambda_l": .05},
        "arm": arm,
        "training_action_law": "clip",
        "seed": seed,
        "tag": tag,
        "launch_sha": source,
        "status": "complete",
        "fit_started": True,
        "spec": runner.jsonable(vars(TECH_FIT)),
        "config": runner.b08._config_record(config),
        "observed_initial_parameter_normalizer_digest": initial_digest,
        "checkpoints": [
            {"path": "checkpoint_00.pt", "sha256": checkpoint00_digest, "bytes": 123},
            checkpoint_record,
        ],
        "panels": panels,
    }
    summary_path = run_root / "summary.json"
    _write(summary_path, summary)
    asset = runner.AssetSpec(
        key, arm, seed, tag, source, summary["object_id"], f"{key}_l05",
        _sha(summary_path), checkpoint00_digest, 123,
        checkpoint_record["sha256"], checkpoint_record["bytes"],
        initial_digest, final_digest, tuple(panel_hashes),
    )
    return asset, checkpoint


@pytest.fixture(scope="module")
def technical_assets(tmp_path_factory):
    root = tmp_path_factory.mktemp("fixed-count-b09-assets")
    made = (
        _make_asset(root, "h6", "H6", 952201, .005),
        _make_asset(root, "set", "SET", 953201, -.007),
    )
    return root, tuple(item[0] for item in made), {item[0].key: item[1] for item in made}


@pytest.fixture(scope="module")
def completed_study(tmp_path_factory, technical_assets):
    root, assets, checkpoints = technical_assets
    out = tmp_path_factory.mktemp("fixed-count-b09-study") / runner.TAG
    assert runner.run_study(
        out, "technical-b09", {"sha": "technical-b09"}, checkpoints,
        assets=assets, eval_spec=TECH_EVAL, summary_root=root / "summaries",
        committed_sources=False,
    ) == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), root


def test_fixed_assets_scalar_worlds_and_counts_are_exact():
    assert runner.FIXED_COUNT_SCALAR == .75
    assert [(a.key, a.arm, a.seed, a.checkpoint_bytes) for a in runner.ASSETS] == [
        ("h6", "H6", 952201, 23073626),
        ("set", "SET", 953201, 20968771),
    ]
    assert runner._world_seed(8) == 1_545_800
    assert runner._expected_counts(runner.DEFAULT_SPEC) == {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": 6,
        "evaluation_team_steps": 48000, "evaluation_uav_steps": 288000,
        "evaluation_episodes": 96, "evaluation_resets": 96,
        "actual_batched_policy_step_calls": 3000,
        "set_actor_shadow_forwards": 1000,
        "h6_coordinator_shadow_forwards": 100,
        "shadow_environment_steps": 0,
        "reused_original_evaluation_steps": 0,
    }


@pytest.mark.parametrize("arm,site_count", [("H6", 1), ("SET", 2)])
def test_instance_hooks_replace_only_scalar_and_cleanup(tmp_path, arm, site_count):
    n = 4
    config = _config(arm, 952201 if arm == "H6" else 953201, n)
    agent = build_agent(config, str(tmp_path / arm))
    intervention = runner.CountScalarIntervention(agent, arm, n)
    try:
        assert len(intervention.targets) == site_count
        for name, layer in intervention.targets.items():
            index = intervention.sites[name]["scalar_index"]
            value = torch.randn(3, layer.in_features)
            value[:, index] = n / 8.0
            before = value.clone()
            captured = []
            observer = layer.register_forward_pre_hook(
                lambda _module, args: captured.append(args[0].detach().clone())
            )
            layer(value)
            observer.remove()
            assert torch.equal(value, before)
            assert torch.equal(captured[0][:, index], torch.full((3,), .75))
            assert torch.equal(captured[0][:, :index], before[:, :index])
            assert torch.equal(captured[0][:, index + 1:], before[:, index + 1:])
        calls = {key: row["actual_calls"] for key, row in intervention.sites.items()}
    finally:
        intervention.close()
    for name, layer in intervention.targets.items():
        index = intervention.sites[name]["scalar_index"]
        value = torch.randn(1, layer.in_features)
        value[:, index] = n / 8.0
        layer(value)
    assert calls == {key: 1 for key in calls}
    assert {key: row["actual_calls"] for key, row in intervention.sites.items()} == calls


def test_native_final_restore_n6_identity_and_shadow_isolation(completed_study):
    out, result, _root = completed_study
    assert result["status"] == "complete" and result["zero_fit"]
    assert result["counts"] == runner._expected_counts(TECH_EVAL)
    assert len(result["panels"]) == 6
    for row in result["panels"]:
        assert row["policy_stage"] == row["world_panel_stage"] == 45
        assert row["prior_training_team_steps"] == runner.PRIOR_TRAINING_TEAM_STEPS
        assert row["restored_digest_matches_original_final"]
        assert row["parameter_normalizer_digest_before"] == row["parameter_normalizer_digest_after"]
        assert row["normalizers_before"] == row["normalizers_after"]
        assert row["runtime_evolved"] and not any(row["optimizer_calls"].values())
        assert row["global_rng_isolation"]["preserved"]
        assert row["intervention"]["site_count"] == (2 if row["arm"] == "SET" else 1)
        for site in row["intervention"]["sites"].values():
            assert site["other_columns_unchanged"] and site["input_was_cloned"]
            assert site["replacement_values"] == [.75]
        if row["test_n"] == 6:
            assert row["n6_original_array_identity"]["all_exact"]
            assert row["set_actor_shadow"] is None and row["h6_coordinator_shadow"] is None
        elif row["arm"] == "SET":
            shadow = row["set_actor_shadow"]
            assert shadow["actual_forwards"] == shadow["shadow_forwards"] == TECH_EVAL.horizon
            assert shadow["runtime_preserved"] and shadow["inputs_preserved"]
            assert shadow["parameters_normalizers_preserved"] and shadow["rng_preserved"]
        else:
            shadow = row["h6_coordinator_shadow"]
            assert shadow["actual_selection_forwards"] == shadow["shadow_selection_forwards"] == 2
            assert shadow["autoregressive_prefix_verified"]
            assert shadow["prefix_lengths"] == list(range(row["test_n"]))
            assert shadow["runtime_preserved"] and shadow["inputs_preserved"]
            assert shadow["parameters_normalizers_preserved"] and shadow["rng_preserved"]
        if row["arm"] == "SET" and row["test_n"] in (4, 8):
            assert row["set_actor_shadow"]["held_snapshot_expected_refresh_steps"] == [0, 10]
            assert row["set_actor_shadow"]["held_snapshot_refresh_steps"] == [0, 10]
            assert row["set_actor_shadow"]["held_snapshot_stable_between_reselections"]
        filename = f"panel_{row['asset_key']}_policy45_fixed075_world45_n{row['test_n']}.json"
        assert (out / filename).is_file()
    assert result["source_hashes_unchanged"] and result["input_identities_unchanged"]


def test_set_shadow_metrics_preserve_hidden_only_and_clipping_absorption_cases():
    telemetry = runner._new_set_shadow()
    raw_actual = np.asarray([[2.0, .2], [-2.0, -.1]])
    raw_shadow = np.asarray([[3.0, .2], [-4.0, -.1]])
    hidden_actual = np.zeros((2, 3))
    hidden_shadow = np.ones((2, 3))
    raw_changed = runner._accumulate_difference(telemetry, "raw", raw_actual, raw_shadow)
    clipped_changed = runner._accumulate_difference(
        telemetry, "clipped", np.clip(raw_actual, -1, 1), np.clip(raw_shadow, -1, 1)
    )
    hidden_changed = runner._accumulate_difference(
        telemetry, "next_hidden", hidden_actual, hidden_shadow
    )
    assert raw_changed and hidden_changed and not clipped_changed
    assert telemetry["raw_changed_coordinates"] == 2
    assert telemetry["clipped_changed_coordinates"] == 0
    assert telemetry["next_hidden_changed_coordinates"] == 6


def test_h6_shadow_uses_its_own_different_autoregressive_prefix(monkeypatch):
    class Decoder(torch.nn.Module):
        def forward(self, *_args, **_kwargs):
            return torch.zeros(2, 6)

    class Coordinator:
        def __init__(self):
            self.skill_decoder = Decoder()

        def assign_and_value_batch(self, state, observations, deterministic):
            assert deterministic
            team = torch.ones(state.shape[0], dtype=torch.long)
            skills = torch.zeros(state.shape[0], observations.shape[1], dtype=torch.long)
            self.skill_decoder(state[:, None, :], observations)
            for index in range(observations.shape[1]):
                prefix = skills[:, :index] if index else None
                self.skill_decoder(
                    state[:, None, :], observations, team, prefix,
                    step=index + 1,
                    agent_specific_query=observations[:, index:index + 1],
                )
                updated = skills.clone()
                updated[:, index] = index + 1
                skills = updated
            return {"team_skills": team, "agent_skills": skills}

    class Agent:
        device = torch.device("cpu")
        config = type("Config", (), {"n_agents": 4})()
        skill_coordinator = Coordinator()

        @staticmethod
        def _normalize_states(value):
            return value

        @staticmethod
        def _normalize_observations(value):
            return value

    class Intervention:
        @contextmanager
        def original_shadow(self):
            yield

    monkeypatch.setattr(runner, "runtime_state_digest", lambda _agent: "runtime")
    monkeypatch.setattr(runner, "digest_agent", lambda _agent: "model")
    monkeypatch.setattr(runner, "_normalizer_record", lambda _agent: {"norm": "fixed"})
    telemetry = runner._new_h6_shadow()
    runner._run_h6_shadow(
        Agent(), Intervention(), np.zeros((2, 7), dtype=np.float32),
        np.zeros((2, 4, 5), dtype=np.float32), np.asarray([True, True]),
        {"team_skills": np.zeros(2, dtype=int),
         "agent_skills": np.zeros((2, 4), dtype=int)},
        telemetry, step_index=0,
    )
    assert telemetry["autoregressive_prefix_verified"]
    assert telemetry["prefix_lengths"] == [0, 1, 2, 3]
    assert telemetry["team_choice_disagreements"] == 2
    assert telemetry["individual_choice_disagreements"] == 8
    assert telemetry["selection_comparisons"][0]["shadow_individual"] == [
        [1, 2, 3, 4], [1, 2, 3, 4]
    ]


def test_readings_are_independent_and_h6_damage_can_make_positive_gamma(completed_study):
    _out, result, source_root = completed_study
    current = {(row["asset_key"], row["test_n"]): row for row in result["panels"]}
    tags = {asset["key"]: asset["tag"] for asset in result["assets"]}
    originals = {
        (asset, n): _read(
            source_root / "summaries" / tags[asset] / f"panel_45_n{n}.json"
        )
        for asset in ("h6", "set") for n in TECH_EVAL.test_ns
    }

    def raw(row, quantity):
        return np.asarray(row["J"] if quantity == "J" else row["component_means"][quantity])

    for n in TECH_EVAL.test_ns:
        for quantity in ("J", *COMPONENTS):
            ho = raw(originals[("h6", n)], quantity)
            so = raw(originals[("set", n)], quantity)
            hc = raw(current[("h6", n)], quantity)
            sc = raw(current[("set", n)], quantity)
            observed = result["readings"]["by_test_n"][str(n)]["quantities"][quantity]
            assert observed["package_effects"]["F_SET_mean"] == pytest.approx((sc - so).mean())
            assert observed["package_effects"]["F_H6_mean"] == pytest.approx((hc - ho).mean())
            assert observed["selectivity"]["Gamma_mean"] == pytest.approx(
                ((sc - so) - (hc - ho)).mean()
            )
            assert observed["package_gaps"]["identity_max_abs_residual"] < 1e-15
    for quantity in ("J", *COMPONENTS):
        u = result["readings"]["U_equal_weight_N4_N8"][quantity]
        expected = {}
        for label, rows, asset in (
            ("H6_original", originals, "h6"),
            ("H6_clamped", current, "h6"),
            ("SET_original", originals, "set"),
            ("SET_clamped", current, "set"),
        ):
            expected[label] = float(np.mean([
                raw(rows[(asset, n)], quantity).mean() for n in (4, 8)
            ]))
            assert u[f"{label}_mean"] == pytest.approx(expected[label])
        f_set = expected["SET_clamped"] - expected["SET_original"]
        f_h6 = expected["H6_clamped"] - expected["H6_original"]
        assert u["F_SET_mean"] == pytest.approx(f_set)
        assert u["F_H6_mean"] == pytest.approx(f_h6)
        assert u["Gamma_mean"] == pytest.approx(f_set - f_h6)
    damage = runner._quantity_reading(
        np.asarray([10.0]), np.asarray([7.0]), np.asarray([5.0]), np.asarray([4.0])
    )
    assert damage["package_effects"]["F_SET_mean"] == -1.0
    assert damage["package_effects"]["F_H6_mean"] == -3.0
    assert damage["selectivity"]["Gamma_mean"] == 2.0


@pytest.mark.parametrize("failure", ["checkpoint_hash", "payload_stage", "payload_config", "panel"])
def test_wrong_asset_stage_config_or_panel_is_rejected(technical_assets, tmp_path, failure):
    root, assets, checkpoints = technical_assets
    asset = assets[0]
    candidate = asset
    checkpoint = checkpoints[asset.key]
    summary_root = root / "summaries"
    if failure == "checkpoint_hash":
        candidate = replace(asset, checkpoint_sha256="0" * 64)
    elif failure in {"payload_stage", "payload_config"}:
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        if failure == "payload_stage":
            payload["rollout"] = 0
        else:
            payload["config"]["count_arm"] = "SET"
        checkpoint = tmp_path / "mutated.pt"
        torch.save(payload, checkpoint)
        candidate = replace(asset, checkpoint_sha256=_sha(checkpoint),
                            checkpoint_bytes=checkpoint.stat().st_size)
        summary = _read(root / "summaries" / asset.tag / "summary.json")
        summary["checkpoints"][1].update(
            sha256=candidate.checkpoint_sha256, bytes=candidate.checkpoint_bytes
        )
        summary_root = tmp_path / "summaries"
        summary_path = summary_root / asset.tag / "summary.json"
        _write(summary_path, summary)
        candidate = replace(candidate, summary_sha256=_sha(summary_path))
        for n in TECH_EVAL.test_ns:
            source = root / "summaries" / asset.tag / f"panel_45_n{n}.json"
            target = summary_root / asset.tag / source.name
            target.write_bytes(source.read_bytes())
    else:
        summary_root = tmp_path / "summaries"
        source_root = root / "summaries" / asset.tag
        target_root = summary_root / asset.tag
        target_root.mkdir(parents=True)
        for source in source_root.iterdir():
            (target_root / source.name).write_bytes(source.read_bytes())
        panel_path = target_root / "panel_45_n4.json"
        panel = _read(panel_path)
        panel["world_seeds"][0] += 1
        _write(panel_path, panel)
        hashes = list(asset.final_panel_sha256)
        hashes[0] = _sha(panel_path)
        candidate = replace(asset, final_panel_sha256=tuple(hashes))
    with pytest.raises(ValueError):
        runner.load_assets(
            {candidate.key: checkpoint}, assets=(candidate,), summary_root=summary_root,
            committed_sources=False, eval_spec=TECH_EVAL,
            restore_log_root=tmp_path / "restore_logs",
        )


def test_partial_failure_retains_actual_resets_calls_steps_and_stage(technical_assets, tmp_path):
    root, assets, checkpoints = technical_assets

    def fail_after_returns(record, n, out, eval_spec, progress):
        progress(0, 0, n, 0, eval_spec.eval_lanes, 0, 0)
        progress(0, 0, n, 1, 0, 0, 0)
        progress(0, 0, n, 0, 0, 0, 1)
        progress(1, 0, n, 0, 0, 0, 0)
        raise RuntimeError("injected finite partial failure")

    out = tmp_path / runner.TAG
    assert runner.run_study(
        out, "technical-b09", {"sha": "technical-b09"}, checkpoints,
        assets=assets, eval_spec=TECH_EVAL, summary_root=root / "summaries",
        committed_sources=False, evaluate_fn=fail_after_returns,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["readings"] is None
    assert result["counts"]["evaluation_resets"] == TECH_EVAL.eval_lanes
    assert result["counts"]["evaluation_episodes"] == 0
    assert result["counts"]["actual_batched_policy_step_calls"] == 1
    assert result["counts"]["h6_coordinator_shadow_forwards"] == 1
    assert result["counts"]["evaluation_team_steps"] == 1
    assert result["counts"]["evaluation_uav_steps"] == 4
    row = result["panels"][0]
    assert row["status"] == "failed" and row["policy_stage"] == 45
    assert row["world_panel_stage"] == 45 and row["test_n"] == 4


def test_reset_count_advances_per_successful_lane_before_later_failure():
    class Env:
        def __init__(self, fails=False):
            self.fails = fails

        def reset(self):
            if self.fails:
                raise RuntimeError("later lane reset failed")
            return np.zeros(2), {"state": np.zeros(3)}

    counts = {"resets": 0}

    def progress(_steps, _episodes, _n, _calls, resets, _set, _h6):
        counts["resets"] += resets

    with pytest.raises(RuntimeError, match="later lane"):
        runner._reset_envs_counted([Env(), Env(fails=True), Env()], 4, progress)
    assert counts["resets"] == 1


def test_n6_comparability_failure_retains_measured_arrays_and_field_differences(
    technical_assets, tmp_path,
):
    root, assets, checkpoints = technical_assets

    def fail_n6(record, n, out, eval_spec, progress):
        if n == 4:
            return {
                "status": "complete", "asset_key": record.spec.key,
                "arm": record.spec.arm, "seed": record.spec.seed,
                "policy_stage": 45, "world_panel_stage": 45, "test_n": n,
                "world_seeds": record.final_panels[n]["world_seeds"],
                "initial_world_digests": [],
            }
        measured = json.loads(json.dumps(record.final_panels[n]))
        measured.update(
            status="complete", asset_key=record.spec.key, arm=record.spec.arm,
            seed=record.spec.seed, policy_stage=45, world_panel_stage=45,
            prior_training_team_steps=runner.PRIOR_TRAINING_TEAM_STEPS,
        )
        measured["J"][0] += .125
        measured["n6_original_array_identity"] = runner._n6_identity(
            measured, record.final_panels[n]
        )
        runner.write_json(
            out / f"panel_{record.spec.key}_policy45_fixed075_world45_n{n}.json",
            measured,
        )
        raise ValueError("B09 N6 unchanged-feature arrays differ from original final45")

    out = tmp_path / runner.TAG
    assert runner.run_study(
        out, "technical-b09", {"sha": "technical-b09"}, checkpoints,
        assets=assets, eval_spec=TECH_EVAL, summary_root=root / "summaries",
        committed_sources=False, evaluate_fn=fail_n6,
    ) == 1
    result = _read(out / "summary.json")
    retained = result["panels"][1]
    assert retained["status"] == "failed" and retained["test_n"] == 6
    assert retained["J"] and retained["component_means"]
    identity = retained["n6_original_array_identity"]
    assert not identity["all_exact"]
    assert not identity["J"]["exact"] and identity["J"]["max_abs_difference"] == .125
    assert identity["scalar_returns"]["exact"]


def test_cli_admission_precedes_science_and_has_no_sweep(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        entry, "require_admission",
        lambda *_a, **_k: calls.append("admit") or {"sha": "abc"},
    )

    def run_fn(*args, **kwargs):
        calls.append((args, kwargs))
        return 29

    out = tmp_path / runner.TAG
    args = ["--launch-sha", "abc", "--out", str(out),
            "--h6-checkpoint", str(tmp_path / "h6.pt"),
            "--set-checkpoint", str(tmp_path / "set.pt")]
    assert entry.main(args, run_fn=run_fn) == 29
    assert calls[0] == "admit" and calls[1][0][0] == out.resolve()
    with pytest.raises(SystemExit):
        entry.main(args + ["--fixed-count", ".5"], run_fn=run_fn)

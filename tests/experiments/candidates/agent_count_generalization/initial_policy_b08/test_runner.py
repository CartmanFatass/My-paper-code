"""Focused technical checks for the fixed B08 checkpoint-00 evaluator."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC, make_config
from experiments.candidates.agent_count_generalization.initial_policy_b08 import runner
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    digest_agent,
    save_checkpoint,
    seed_rng,
)
from scripts import run_agent_count_initial_policy_b08 as entry


TECH_FIT = replace(
    DEFAULT_SPEC,
    horizon=3,
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
TECH_EVAL = runner.EvalSpec(horizon=3, eval_lanes=2, torch_threads=1)


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


def _make_asset(root: Path, key: str, arm: str, seed: int, shift: float):
    tag = f"technical_b08_{key}"
    source = f"technical-source-{key}"
    config = _config(arm, seed, 6)
    seed_rng(seed)
    agent = build_agent(config, str(root / "agent_logs" / key))
    try:
        normalizer = agent.value_norm_discoverer
        normalizer.mean = np.asarray(1.5 + shift)
        normalizer.var = np.asarray(2.0 + abs(shift))
        normalizer.count = 9.0
        if shift:
            with torch.no_grad():
                next(agent.skill_discoverer.actor.parameters()).add_(shift)
        initial_digest = digest_agent(agent)
        checkpoint_root = root / "checkpoints" / tag
        checkpoint_root.mkdir(parents=True)
        checkpoint_record = save_checkpoint(agent, checkpoint_root, 0, config, source)
    finally:
        del agent
    checkpoint = checkpoint_root / checkpoint_record["path"]
    final_panels = []
    final_hashes = []
    run_root = root / "summaries" / tag
    for n in TECH_EVAL.test_ns:
        coverage = np.asarray([.22 + .01 * n + .003 * i + shift
                               for i in range(TECH_EVAL.eval_lanes)])
        quality = np.asarray([.11 + .002 * i - shift / 2 for i in range(TECH_EVAL.eval_lanes)])
        penalty = np.asarray([.04 + .001 * i + abs(shift) / 3
                              for i in range(TECH_EVAL.eval_lanes)])
        total = .7 * coverage + .3 * quality - penalty
        panel_config = _config(arm, seed, n)
        panel = {
            "after_rollout": 45,
            "training_team_steps": 45 * TECH_FIT.train_lanes * TECH_FIT.horizon,
            "test_n": n,
            "world_seeds": list(range(runner._world_seed(n), runner._world_seed(n) + TECH_EVAL.eval_lanes)),
            "execution_law": "clip",
            "status": "complete",
            "steps": TECH_EVAL.eval_lanes * TECH_EVAL.horizon,
            "episodes": TECH_EVAL.eval_lanes,
            "J": total.tolist(),
            "scalar_returns": (total * TECH_EVAL.horizon / n).tolist(),
            "component_means": {
                "coverage_reward": coverage.tolist(), "quality_reward": quality.tolist(),
                "energy_penalty": penalty.tolist(), "total_reward": total.tolist(),
            },
            "optimizer_calls": {name: 0 for name in (
                "coordinator", "discoverer_actor", "discoverer_critic",
                "team_discriminator", "individual_discriminator",
            )},
            "frozen_weights_and_normalizers": True,
            "executed_action_bounds": {"minimum": -.8, "maximum": .9},
            "config": runner._config_record(panel_config),
        }
        panel_path = run_root / f"panel_45_n{n}.json"
        _write(panel_path, panel)
        final_panels.append(panel)
        final_hashes.append(_sha(panel_path))
    final_digest = ("a" if key == "h6" else "b") * 64
    summary = {
        "schema": 1, "object_id": f"technical-object-{key}",
        "direction": "agent_count_generalization",
        "cell": {"key": f"{key}_l05", "tag": tag, "arm": arm, "law": "clip",
                 "seed": seed, "lambda_l": .05},
        "arm": arm, "training_action_law": "clip", "seed": seed, "tag": tag,
        "launch_sha": source, "status": "complete", "fit_started": True,
        "spec": runner.jsonable(vars(TECH_FIT)), "config": runner._config_record(config),
        "observed_initial_parameter_normalizer_digest": initial_digest,
        "checkpoints": [checkpoint_record, {
            "path": "checkpoint_45.pt", "sha256": final_digest,
            "bytes": checkpoint.stat().st_size,
        }],
        "panels": final_panels,
    }
    summary_path = run_root / "summary.json"
    _write(summary_path, summary)
    asset = runner.AssetSpec(
        key, arm, seed, tag, source, summary["object_id"], f"{key}_l05",
        _sha(summary_path), checkpoint_record["sha256"], checkpoint_record["bytes"],
        final_digest, checkpoint.stat().st_size, initial_digest, tuple(final_hashes),
    )
    return asset, checkpoint


@pytest.fixture(scope="module")
def technical_assets(tmp_path_factory):
    root = tmp_path_factory.mktemp("initial-policy-b08-assets")
    made = (
        _make_asset(root, "h6", "H6", 952201, .0),
        _make_asset(root, "set", "SET", 953201, .015),
    )
    return root, tuple(item[0] for item in made), {item[0].key: item[1] for item in made}


@pytest.fixture(scope="module")
def completed_study(tmp_path_factory, technical_assets):
    root, assets, checkpoints = technical_assets
    out = tmp_path_factory.mktemp("initial-policy-b08-study") / runner.TAG
    assert runner.run_study(
        out, "technical-b08", {"sha": "technical-b08"}, checkpoints,
        assets=assets, eval_spec=TECH_EVAL, summary_root=root / "summaries",
        committed_sources=False,
    ) == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), root


def test_fixed_assets_stages_worlds_and_counts_are_exact():
    assert [(a.key, a.arm, a.seed, a.checkpoint00_bytes) for a in runner.ASSETS] == [
        ("h6", "H6", 952201, 23073626), ("set", "SET", 953201, 20968771),
    ]
    assert runner.POLICY_STAGE == 0 and runner.WORLD_PANEL_STAGE == 45
    assert runner._world_seed(8) == 1_545_800
    assert runner._expected_counts(runner.DEFAULT_SPEC) == {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": 6, "evaluation_team_steps": 48000,
        "evaluation_uav_steps": 288000, "evaluation_episodes": 96,
        "evaluation_resets": 96, "batched_policy_step_calls": 3000,
        "reused_final_evaluation_steps": 0,
    }


def test_native_checkpoint00_restore_is_frozen_and_world45_is_separate(completed_study):
    out, result, _root = completed_study
    assert result["status"] == "complete" and result["zero_fit"]
    assert result["policy_stage"] == 0 and result["world_panel_stage"] == 45
    assert result["prior_training_exposure"] == 0
    assert result["counts"] == runner._expected_counts(TECH_EVAL)
    assert len(result["panels"]) == 6
    for row in result["panels"]:
        assert row["policy_stage"] == 0 and row["prior_training_team_steps"] == 0
        assert row["world_panel_stage"] == 45
        assert row["world_seeds"][0] == runner._world_seed(row["test_n"])
        assert row["restored_digest_matches_original_initial"]
        assert row["parameter_normalizer_digest_before"] == row["parameter_normalizer_digest_after"]
        assert row["normalizers_before"] == row["normalizers_after"]
        assert row["normalizers_before"]["value_norm_discoverer"]["fields"]["mean"]["value"] != 0
        assert row["runtime_evolved"]
        assert not any(row["optimizer_calls"].values()) and row["frozen_weights_and_normalizers"]
        assert row["global_rng_isolation"]["preserved"] and row["diagnostics_rng_unchanged"]
        assert row["executed_action_bounds"]["minimum"] >= -1.0
        assert row["executed_action_bounds"]["maximum"] <= 1.0
        filename = f"panel_{row['asset_key']}_policy0_world45_n{row['test_n']}.json"
        assert (out / filename).is_file()
    assert all(value["both_policies_match"]
               for value in result["initial_state_observation_matches"].values())
    assert result["source_hashes_unchanged"] and result["input_identities_unchanged"]
    assert all(not asset["checkpoint45_identity_only"]["loaded_or_evaluated"]
               for asset in result["assets"])


def test_readings_join_raw_initial_panels_to_independent_final_files(completed_study):
    _out, result, source_root = completed_study
    current = {(row["asset_key"], row["test_n"]): row for row in result["panels"]}
    source_tags = {asset["key"]: asset["tag"] for asset in result["assets"]}
    finals = {
        (asset, n): _read(
            source_root / "summaries" / source_tags[asset] / f"panel_45_n{n}.json"
        )
        for asset in ("h6", "set") for n in TECH_EVAL.test_ns
    }

    def raw(row, quantity):
        return np.asarray(row["J"] if quantity == "J" else row["component_means"][quantity])

    for n in TECH_EVAL.test_ns:
        for quantity in ("J", *runner.COMPONENTS):
            h0 = raw(current[("h6", n)], quantity)
            s0 = raw(current[("set", n)], quantity)
            h45 = raw(finals[("h6", n)], quantity)
            s45 = raw(finals[("set", n)], quantity)
            observed = result["readings"]["by_test_n"][str(n)]["quantities"][quantity]
            assert observed["absolute"]["H0_mean"] == pytest.approx(h0.mean())
            assert observed["absolute"]["H45_mean"] == pytest.approx(h45.mean())
            assert observed["absolute"]["S0_mean"] == pytest.approx(s0.mean())
            assert observed["absolute"]["S45_mean"] == pytest.approx(s45.mean())
            assert observed["self_gains"]["I_H_mean"] == pytest.approx((h45 - h0).mean())
            assert observed["self_gains"]["I_S_mean"] == pytest.approx((s45 - s0).mean())
            assert observed["package_gaps"]["D0_mean"] == pytest.approx((h0 - s0).mean())
            assert observed["package_gaps"]["D45_mean"] == pytest.approx((h45 - s45).mean())
            delta = (h45 - h0) - (s45 - s0)
            assert observed["difference_of_self_gains"]["Delta_mean"] == pytest.approx(delta.mean())
            assert observed["difference_of_self_gains"]["identity_max_abs_residual"] < 1e-15
        coverage = result["readings"]["by_test_n"][str(n)]["quantities"]["coverage_reward"]
        assert coverage["users_per_step"]["H0_mean"] == pytest.approx(
            50 * coverage["absolute"]["H0_mean"]
        )
    for quantity in ("J", *runner.COMPONENTS):
        u = result["readings"]["U_equal_weight_N4_N8"][quantity]
        expected_u = {}
        for label, asset, stage in (
            ("H0", "h6", 0), ("S0", "set", 0),
            ("H45", "h6", 45), ("S45", "set", 45),
        ):
            rows = current if stage == 0 else finals
            expected_u[label] = float(np.mean([
                raw(rows[(asset, n)], quantity).mean() for n in (4, 8)
            ]))
            assert u[f"{label}_mean"] == pytest.approx(expected_u[label])
        assert u["I_H_mean"] == pytest.approx(expected_u["H45"] - expected_u["H0"])
        assert u["I_S_mean"] == pytest.approx(expected_u["S45"] - expected_u["S0"])
        assert u["D0_mean"] == pytest.approx(expected_u["H0"] - expected_u["S0"])
        assert u["D45_mean"] == pytest.approx(expected_u["H45"] - expected_u["S45"])
        assert u["Delta_mean"] == pytest.approx(
            (expected_u["H45"] - expected_u["H0"])
            - (expected_u["S45"] - expected_u["S0"])
        )


def test_self_gains_are_preserved_before_delta_for_both_sign_counterexamples():
    negative = runner._quantity_reading(
        np.asarray([10.0]), np.asarray([8.0]), np.asarray([10.0]), np.asarray([5.0]),
    )
    assert negative["self_gains"]["I_H_mean"] == -2.0
    assert negative["self_gains"]["I_S_mean"] == -5.0
    assert negative["difference_of_self_gains"]["Delta_mean"] == 3.0
    positive = runner._quantity_reading(
        np.asarray([0.0]), np.asarray([1.0]), np.asarray([0.0]), np.asarray([2.0]),
    )
    assert positive["self_gains"]["I_H_mean"] == 1.0
    assert positive["self_gains"]["I_S_mean"] == 2.0
    assert positive["difference_of_self_gains"]["Delta_mean"] == -1.0


@pytest.mark.parametrize("failure", ["summary_source", "checkpoint_hash", "payload_stage", "payload_config", "panel"])
def test_wrong_identity_stage_config_or_panel_is_rejected_before_evaluation(
    technical_assets, tmp_path, failure,
):
    root, assets, checkpoints = technical_assets
    asset = assets[0]
    candidate = asset
    candidate_root = root / "summaries"
    candidate_checkpoint = checkpoints[asset.key]
    if failure == "checkpoint_hash":
        candidate = replace(asset, checkpoint00_sha256="0" * 64)
    elif failure in {"payload_stage", "payload_config"}:
        payload = torch.load(candidate_checkpoint, map_location="cpu", weights_only=True)
        payload["rollout"] = 1 if failure == "payload_stage" else 0
        if failure == "payload_config":
            payload["config"]["count_arm"] = "SET"
        candidate_checkpoint = tmp_path / "mutated.pt"
        torch.save(payload, candidate_checkpoint)
        candidate = replace(asset, checkpoint00_sha256=_sha(candidate_checkpoint),
                            checkpoint00_bytes=candidate_checkpoint.stat().st_size)
        summary = _read(root / "summaries" / asset.tag / "summary.json")
        summary["checkpoints"][0].update(
            sha256=candidate.checkpoint00_sha256, bytes=candidate.checkpoint00_bytes,
        )
        candidate_root = tmp_path / "summaries"
        summary_path = candidate_root / asset.tag / "summary.json"
        _write(summary_path, summary)
        candidate = replace(candidate, summary_sha256=_sha(summary_path))
        for n in TECH_EVAL.test_ns:
            source = root / "summaries" / asset.tag / f"panel_45_n{n}.json"
            target = candidate_root / asset.tag / source.name
            target.write_bytes(source.read_bytes())
    else:
        candidate_root = tmp_path / "summaries"
        source_run = root / "summaries" / asset.tag
        target_run = candidate_root / asset.tag
        target_run.mkdir(parents=True)
        for source in source_run.iterdir():
            (target_run / source.name).write_bytes(source.read_bytes())
        if failure == "summary_source":
            summary_path = target_run / "summary.json"
            summary = _read(summary_path)
            summary["launch_sha"] = "wrong"
            _write(summary_path, summary)
            candidate = replace(asset, summary_sha256=_sha(summary_path))
        else:
            panel_path = target_run / "panel_45_n4.json"
            panel = _read(panel_path)
            panel["after_rollout"] = 0
            _write(panel_path, panel)
            hashes = list(asset.final_panel_sha256)
            hashes[0] = _sha(panel_path)
            candidate = replace(asset, final_panel_sha256=tuple(hashes))
    with pytest.raises(ValueError):
        runner.load_assets(
            {candidate.key: candidate_checkpoint}, assets=(candidate,),
            summary_root=candidate_root, committed_sources=False, eval_spec=TECH_EVAL,
            restore_log_root=tmp_path / "restore_logs",
        )


def test_partial_failure_keeps_stage_labels_and_actual_finite_counts(technical_assets, tmp_path):
    root, assets, checkpoints = technical_assets

    def fail_after_returns(record, n, out, eval_spec, progress):
        progress(0, 0, n, 0, eval_spec.eval_lanes)
        progress(0, 0, n, 1, 0)
        progress(1, 0, n, 0, 0)
        raise RuntimeError("injected finite partial failure")

    out = tmp_path / runner.TAG
    assert runner.run_study(
        out, "technical-b08", {"sha": "technical-b08"}, checkpoints,
        assets=assets, eval_spec=TECH_EVAL, summary_root=root / "summaries",
        committed_sources=False, evaluate_fn=fail_after_returns,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["readings"] is None
    assert result["counts"]["evaluation_team_steps"] == 1
    assert result["counts"]["evaluation_uav_steps"] == 4
    assert result["counts"]["batched_policy_step_calls"] == 1
    assert result["counts"]["evaluation_resets"] == TECH_EVAL.eval_lanes
    assert result["counts"]["evaluation_episodes"] == 0
    assert result["counts"]["panels"] == 0
    row = result["panels"][0]
    assert row["status"] == "failed" and row["policy_stage"] == 0
    assert row["prior_training_team_steps"] == 0 and row["world_panel_stage"] == 45
    assert row["test_n"] == 4 and all(np.isfinite(list(result["counts"].values())))


def test_cli_admission_precedes_scientific_runner_and_exposes_no_stage_tuning(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "abc"})

    def run_fn(*args, **kwargs):
        calls.append((args, kwargs))
        return 31

    out = tmp_path / runner.TAG
    args = ["--launch-sha", "abc", "--out", str(out),
            "--h6-checkpoint", str(tmp_path / "h6.pt"),
            "--set-checkpoint", str(tmp_path / "set.pt")]
    assert entry.main(args, run_fn=run_fn) == 31
    assert calls[0] == "admit"
    assert calls[1][0][0] == out.resolve()
    assert set(calls[1][0][3]) == {"h6", "set"}
    with pytest.raises(SystemExit):
        entry.main(args + ["--policy-stage", "45"], run_fn=run_fn)

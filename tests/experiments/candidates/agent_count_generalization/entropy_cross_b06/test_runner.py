"""Technical checks for the fixed B06 zero-fit cross-panel evaluator."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.entropy_cross_b06 import runner
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import save_checkpoint, seed_rng
from scripts import run_agent_count_entropy_cross_b06 as entry


TECH_FIT = replace(
    DEFAULT_SPEC,
    horizon=3,
    train_lanes=1,
    eval_lanes=1,
    hidden_size=16,
    n_heads=2,
    n_layers=1,
    ppo_epochs=1,
    sequence_batch_size=4,
    coordinator_batch_size=2,
    torch_threads=1,
)
TECH_CROSS = runner.CrossSpec(horizon=3, eval_lanes=1, torch_threads=1)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _config_for(seed: int, coefficient: float, n: int):
    envs = make_envs(TECH_CROSS.eval_lanes, runner.PANELS["A"] + 45_000 + 100 * n,
                     n, TECH_CROSS.horizon)
    try:
        config = make_config("SET", envs, seed, TECH_FIT)
        config.lambda_l = config.lambda_l_initial = config.lambda_l_final = coefficient
        config.use_entropy_annealing = False
        config.use_entropy_targets = False
        config.validate_config()
        return config
    finally:
        for env in envs:
            env.close()


def _make_asset(root: Path, key: str, pair: str, coefficient: float, seed: int, shift: float):
    tag = f"technical_{key}"
    source = f"technical-source-{key}"
    config = _config_for(seed, coefficient, 6)
    seed_rng(seed)
    agent = build_agent(config, str(root / "logs" / key))
    try:
        agent.value_norm_discoverer.mean = np.asarray(1.25 + shift)
        agent.value_norm_discoverer.var = np.asarray(2.5 + abs(shift))
        agent.value_norm_discoverer.count = 7.0
        if shift:
            with torch.no_grad():
                next(agent.skill_discoverer.actor.parameters()).add_(shift)
        (root / tag).mkdir(parents=True, exist_ok=True)
        checkpoint_record = save_checkpoint(agent, root / tag, 45, config, source)
    finally:
        del agent
    checkpoint = root / tag / checkpoint_record["path"]
    panels = []
    historical_panel = pair
    for n in TECH_CROSS.test_ns:
        panel_config = _config_for(seed, coefficient, n)
        panels.append({
            "after_rollout": 45,
            "test_n": n,
            "status": "complete",
            "world_seeds": list(range(
                runner.PANELS[historical_panel] + 45_000 + 100 * n,
                runner.PANELS[historical_panel] + 45_000 + 100 * n + TECH_CROSS.eval_lanes,
            )),
            "config": config_dict(panel_config),
        })
    summary = {
        "schema": 1,
        "object_id": f"technical-object-{key}",
        "direction": "agent_count_generalization",
        "cell": {"key": key, "tag": tag, "seed": seed, "arm": "SET", "law": "clip",
                 "lambda_l": coefficient},
        "arm": "SET",
        "training_action_law": "clip",
        "seed": seed,
        "tag": tag,
        "launch_sha": source,
        "status": "complete",
        "fit_started": True,
        "spec": runner.jsonable(vars(TECH_FIT)),
        "config": config_dict(config),
        "panels": panels,
        "checkpoints": [checkpoint_record],
    }
    placeholder = runner.AssetSpec(
        key, pair, historical_panel, seed, tag, source, "", checkpoint_record["sha256"],
        checkpoint_record["bytes"], summary["object_id"], key, coefficient,
    )
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    loaded = runner.LoadedAsset(placeholder, checkpoint, summary, {}, payload, TECH_FIT)
    scratch = root / "historical_scratch"
    for panel in panels:
        evaluated = runner.evaluate_policy(
            loaded, historical_panel, panel["test_n"], scratch, TECH_CROSS,
        )
        panel.update(evaluated)
        panel["after_rollout"] = 45
    summary_path = root / "summaries" / tag / "summary.json"
    _write(summary_path, summary)
    asset = replace(placeholder, summary_sha256=_sha(summary_path))
    return asset, checkpoint


@pytest.fixture(scope="module")
def technical_assets(tmp_path_factory):
    root = tmp_path_factory.mktemp("entropy-cross-b06-assets")
    definitions = (
        ("a_l05", "A", .05, 943201, 0.0),
        ("a_l0", "A", 0.0, 943201, .002),
        ("b_l05", "B", .05, 953201, -.002),
        ("b_l0", "B", 0.0, 953201, .004),
    )
    made = [_make_asset(root, *definition) for definition in definitions]
    return root, tuple(item[0] for item in made), {
        asset.key: checkpoint for asset, checkpoint in made
    }


@pytest.fixture(scope="module")
def completed_cross(tmp_path_factory, technical_assets):
    root, assets, checkpoints = technical_assets
    out = tmp_path_factory.mktemp("entropy-cross-b06-run") / runner.TAG
    code = runner.run_study(
        out, "technical-b06", {"sha": "technical-b06"}, checkpoints,
        assets=assets, cross=TECH_CROSS, summary_root=root / "summaries",
        committed_summaries=False,
    )
    assert code == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json")


def test_fixed_assets_panels_and_exposure_are_exact():
    assert [(a.key, a.policy_pair, a.historical_panel, a.seed, a.lambda_l) for a in runner.ASSETS] == [
        ("a_l05", "A", "A", 943201, .05),
        ("a_l0", "A", "A", 943201, 0.0),
        ("b_l05", "B", "B", 953201, .05),
        ("b_l0", "B", "B", 953201, 0.0),
    ]
    assert runner.PANELS == {"A": 1_200_000, "B": 1_500_000}
    assert runner._expected_counts(runner.DEFAULT_SPEC) == {
        "training_team_steps": 0, "optimizer_updates": 0, "panels": 24,
        "evaluation_team_steps": 192000, "evaluation_episodes": 384,
        "uav_steps": 1152000, "batched_policy_step_calls": 12000,
    }


def test_native_restore_replay_reset_freeze_and_both_off_diagonals(completed_cross):
    out, result = completed_cross
    assert result["status"] == "complete" and result["zero_fit"]
    assert result["counts"] == runner._expected_counts(TECH_CROSS)
    assert len(result["panels"]) == 24
    assert [row["phase"] for row in result["panels"][:12]] == ["diagonal"] * 12
    assert [row["phase"] for row in result["panels"][12:]] == ["off_diagonal"] * 12
    assert {(row["policy_pair"], row["evaluation_panel"]) for row in result["panels"]} == {
        ("A", "A"), ("A", "B"), ("B", "A"), ("B", "B")
    }
    for row in result["panels"]:
        assert not any(row["optimizer_calls"].values())
        assert row["frozen_weights_and_normalizers"]
        assert row["parameter_normalizer_digest_before"] == row["parameter_normalizer_digest_after"]
        assert row["normalizers_before"] == row["normalizers_after"]
        assert row["normalizers_before"]["value_norm_discoverer"]["fields"]["mean"]["value"] != 0.0
        assert row["diagnostics_rng_unchanged"]
        assert row["world_seeds"][0] == runner.PANELS[row["evaluation_panel"]] + 45_000 + 100 * row["test_n"]
        filename = f"panel_{row['phase']}_{row['asset_key']}_on_{row['evaluation_panel']}_n{row['test_n']}.json"
        assert (out / filename).is_file()
        if row["phase"] == "diagonal":
            assert row["historical_replay"]["all_absolute_outputs_match"]
    assert all(item["all_four_policies_match"]
               for item in result["initial_state_observation_matches"].values())
    assert (out / "config.json").is_file()


@pytest.mark.parametrize("failure", ["summary_hash", "identity", "config", "checkpoint_hash"])
def test_asset_identity_hash_and_config_fail_before_evaluation(technical_assets, tmp_path, failure):
    root, assets, checkpoints = technical_assets
    asset = assets[0]
    paths = {asset.key: checkpoints[asset.key]}
    if failure == "summary_hash":
        candidate = replace(asset, summary_sha256="0" * 64)
    elif failure == "checkpoint_hash":
        candidate = replace(asset, checkpoint_sha256="0" * 64)
    else:
        source = root / "summaries" / asset.tag / "summary.json"
        summary = _read(source)
        if failure == "identity":
            summary["seed"] += 1
        else:
            summary["config"]["hidden_size"] += 1
        alternate = tmp_path / asset.tag / "summary.json"
        _write(alternate, summary)
        root = tmp_path
        candidate = replace(asset, summary_sha256=_sha(alternate))
    with pytest.raises(ValueError):
        runner.load_assets(
            paths, assets=(candidate,), summary_root=root / "summaries" if failure in {
                "summary_hash", "checkpoint_hash"
            } else root,
            committed_summaries=False, cross=TECH_CROSS,
        )


def test_component_mismatch_is_rejected_even_when_native_J_cancels():
    current = {
        "world_seeds": [1], "scalar_returns": [2.0], "J": [3.0],
        "component_means": {name: [float(index)] for index, name in enumerate(runner.COMPONENTS)},
    }
    historical = json.loads(json.dumps(current))
    historical["component_means"]["coverage_reward"][0] += 1.0
    historical["component_means"]["quality_reward"][0] -= 7.0 / 3.0
    replay = runner.compare_diagonal(current, historical)
    assert not replay["all_absolute_outputs_match"]
    assert not replay["fields"]["component_means.coverage_reward"]["within_fixed_tolerance"]
    assert not replay["fields"]["component_means.quality_reward"]["within_fixed_tolerance"]


def test_failed_diagonal_stops_before_any_off_diagonal(technical_assets, tmp_path):
    root, assets, checkpoints = technical_assets
    calls = []

    def mismatch(record, panel, n, out, cross, progress):
        calls.append((record.spec.key, panel, n))
        row = runner.evaluate_policy(record, panel, n, out, cross, progress)
        row["component_means"]["coverage_reward"][0] += 1.0
        return row

    out = tmp_path / runner.TAG
    assert runner.run_study(
        out, "technical-b06", {"sha": "technical-b06"}, checkpoints,
        assets=assets, cross=TECH_CROSS, summary_root=root / "summaries",
        committed_summaries=False, evaluate_fn=mismatch,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and len(result["panels"]) == 1
    rejected = result["panels"][0]
    assert rejected["status"] == "failed_replay"
    assert not rejected["historical_replay"]["all_absolute_outputs_match"]
    assert rejected["historical_replay"]["fields"]
    assert result["counts"]["panels"] == 1
    assert result["counts"]["evaluation_team_steps"] == TECH_CROSS.horizon
    assert result["counts"]["batched_policy_step_calls"] == TECH_CROSS.horizon
    assert calls == [("a_l05", "A", 4)]


def test_mid_panel_failure_retains_identity_and_actual_partial_counts(technical_assets, tmp_path, monkeypatch):
    root, assets, checkpoints = technical_assets
    native_components = runner.native_components
    returned_steps = []

    def reject_second_returned_transition(info, reward, n):
        returned_steps.append(n)
        if len(returned_steps) == 2:
            raise ValueError("injected returned-output failure")
        return native_components(info, reward, n)

    monkeypatch.setattr(runner, "native_components", reject_second_returned_transition)
    out = tmp_path / runner.TAG
    assert runner.run_study(
        out, "technical-b06", {"sha": "technical-b06"}, checkpoints,
        assets=assets, cross=TECH_CROSS, summary_root=root / "summaries",
        committed_summaries=False,
    ) == 1
    result = _read(out / "summary.json")
    assert returned_steps == [4, 4]
    assert result["status"] == "failed"
    assert result["counts"]["panels"] == 0
    assert result["counts"]["evaluation_team_steps"] == 2
    assert result["counts"]["uav_steps"] == 8
    assert result["counts"]["batched_policy_step_calls"] == 2
    assert result["counts"]["evaluation_episodes"] == 0
    assert result["panels"] == [{
        "status": "failed", "phase": "diagonal", "asset_key": "a_l05",
        "policy_pair": "A", "coefficient": .05, "evaluation_panel": "A",
        "test_n": 4,
        "world_seeds": [runner.PANELS["A"] + 45_000 + 400],
        "failure": "ValueError: injected returned-output failure",
    }]


def test_contrasts_are_independently_recomputed_and_same_sign_can_have_zero_T(completed_cross):
    _out, result = completed_cross
    indexed = {(r["asset_key"], r["evaluation_panel"], r["test_n"]): r for r in result["panels"]}
    sources = {"a": ("a_l0", "a_l05", "A"), "x": ("a_l0", "a_l05", "B"),
               "y": ("b_l0", "b_l05", "A"), "z": ("b_l0", "b_l05", "B")}
    for n in TECH_CROSS.test_ns:
        raw = {
            cell: float(np.mean(np.asarray(indexed[(zero, panel, n)]["J"]) -
                                np.asarray(indexed[(l05, panel, n)]["J"])))
            for cell, (zero, l05, panel) in sources.items()
        }
        a, x, y, z = (raw[key] for key in ("a", "x", "y", "z"))
        expected = {
            "R": ((a + x) / 2) - ((y + z) / 2),
            "C": ((a + y) / 2) - ((x + z) / 2),
            "T": (a - x) - (y - z),
        }
        actual = result["contrasts"]["by_test_n"][str(n)]
        for field, value in {**raw, **expected}.items():
            assert actual[field] == pytest.approx(value)
    u_raw = {}
    for cell, (zero, l05, panel) in sources.items():
        raw_n = []
        for n in (4, 8):
            raw_n.append(float(np.mean(
                np.asarray(indexed[(zero, panel, n)]["J"])
                - np.asarray(indexed[(l05, panel, n)]["J"])
            )))
        u_raw[cell] = float(np.mean(raw_n))
    a, x, y, z = (u_raw[key] for key in ("a", "x", "y", "z"))
    u = result["contrasts"]["U_equal_weight_N4_N8"]
    assert u["R"] == pytest.approx(((a + x) - (y + z)) / 2)
    assert u["C"] == pytest.approx(((a + y) - (x + z)) / 2)
    assert u["T"] == pytest.approx(a - x - y + z)
    a, z = .055540524660, -.045630407894
    midpoint = (a + z) / 2
    counterexample = runner._rct({"a": a, "x": midpoint, "y": midpoint, "z": z})
    assert midpoint > 0 and counterexample["T"] == pytest.approx(0.0, abs=1e-15)
    assert counterexample["R_plus_C_identity_residual"] == pytest.approx(0.0, abs=1e-15)
    assert counterexample["R_minus_C_identity_residual"] == pytest.approx(0.0, abs=1e-15)


def test_cli_requires_admission_and_exposes_only_four_fixed_checkpoints(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(entry, "require_admission", lambda *_args, **_kwargs: calls.append("admit") or {"sha": "abc"})

    def run_fn(out, sha, admission, checkpoints, **kwargs):
        calls.append((out, sha, admission, checkpoints, kwargs))
        return 17

    out = tmp_path / runner.TAG
    args = ["--launch-sha", "abc", "--out", str(out)]
    for key in ("a-l05", "a-l0", "b-l05", "b-l0"):
        args.extend((f"--{key}-checkpoint", str(tmp_path / f"{key}.pt")))
    assert entry.main(args, run_fn=run_fn) == 17
    assert calls[0] == "admit"
    assert set(calls[1][3]) == {"a_l05", "a_l0", "b_l05", "b_l0"}
    with pytest.raises(SystemExit):
        entry.main(args + ["--seed", "1"], run_fn=run_fn)

from __future__ import annotations

import builtins
from copy import copy
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.agent_count_generalization.fresh_world_deployment_b17 import runner as b17


RUN_ROOT = b17.REPOSITORY_ROOT / "runs" / b17.DIRECTION


@pytest.fixture(scope="module")
def loaded_assets():
    return b17.load_assets(RUN_ROOT, restore_log_root=None)


def test_all_six_bound_assets_validate_and_reject_corruption(loaded_assets, tmp_path):
    assert [record.spec.key for record in loaded_assets] == list(b17.POLICY_ORDER)
    assert {record.spec.arm for record in loaded_assets} == {"LOCAL1", "H6"}
    for record in loaded_assets:
        assert record.identities["checkpoint"]["sha256"] == record.spec.hash_for("checkpoint")
        assert record.summary["counts"]["training_team_steps"] == 360_000

    path = tmp_path / "changed.bin"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        b17._read_bound(path, "0" * 64)

    record = loaded_assets[0]
    payload = copy(record.payload)
    payload["modules"] = dict(record.payload["modules"])
    payload["modules"].pop("skill_coordinator")
    with pytest.raises(ValueError, match="module set mismatch"):
        b17._validate_payload(record.spec, payload, record.summary)


def test_true_program_strict_restore_both_programs_all_actual_rosters(loaded_assets, tmp_path):
    spec = b17.DEFAULT_SPEC
    for record in (loaded_assets[0], loaded_assets[1]):
        evidence = b17._strict_restore(
            record, spec, tmp_path / "restore", strict_contract=True,
        )
        assert set(evidence) == {8, 6, 4}
        assert {row["restored_digest"] for row in evidence.values()} == {
            record.spec.final_digest
        }
        assert all(row["buffer_initial"]["env_lengths"] == [0] * 32 for row in evidence.values())
        assert all(row["outer_rng_isolation"]["preserved"] for row in evidence.values())


@pytest.mark.parametrize("asset_index", [0, 1], ids=["local1", "h6"])
def test_reduced_native_panel_preserves_temporal_trace_and_freezes_learning(
    loaded_assets, tmp_path, asset_index,
):
    spec = b17.EvalSpec(test_ns=(4,), horizon=20, eval_lanes=1, torch_threads=4)
    row, trace = b17.evaluate_panel(
        loaded_assets[asset_index], 4, "fresh", tmp_path, spec,
        strict_contract=False,
    )
    assert row["status"] == "complete"
    assert row["training_storage_calls"] == 0
    assert not any(row["optimizer_calls"].values())
    assert row["frozen_weights_and_normalizers"]
    assert row["parameter_normalizer_digest_before"] == row["parameter_normalizer_digest_after"]
    assert row["inference_counts"]["actor_calls"] == 20
    assert row["inference_counts"]["critic_calls"] == 20
    assert row["inference_counts"]["snapshot_refresh_calls"] == 0
    assert np.flatnonzero(trace["skill_changed"][:, 0]).tolist() == [0, 10]
    assert trace["terminated"].shape == (20, 1)
    assert trace["next_states"].shape == (20, 1, 133)
    assert trace["raw_actions"].shape == trace["executed_actions"].shape == (20, 1, 4, 3)
    assert trace["uav_positions"].shape == (20, 1, 4, 3)
    assert trace["user_positions"].shape == (20, 1, 50, 2)
    assert np.all(trace["served_user_counts"] <= 40)
    assert row["global_rng_isolation"]["preserved"]


def test_mid_panel_failure_preserves_partial_trace_and_progress(loaded_assets, tmp_path, monkeypatch):
    original = b17.b11._observe_post_transition
    calls = 0

    def fail_on_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("fixture native identity violation")
        return original(*args, **kwargs)

    monkeypatch.setattr(b17.b11, "_observe_post_transition", fail_on_second)
    spec = b17.EvalSpec(test_ns=(4,), horizon=20, eval_lanes=1, torch_threads=4)
    with pytest.raises(b17.PanelFailure) as caught:
        b17.evaluate_panel(
            loaded_assets[0], 4, "fresh", tmp_path, spec, strict_contract=False,
        )
    row = caught.value.row
    assert row["status"] == "failed"
    assert row["steps"] == 2
    assert row["completed_full_timesteps"] == 1
    assert row["policy_step_calls"] == 2
    assert row["partial_trace_validity"]["completed_transition_rows"] == 2
    assert Path(row["partial_trace"]["path"]).is_file()
    assert row["inference_counts_partial"]["actor_calls"] == 2
    assert "fixture native identity violation" in row["failure"]


def test_replay_comparison_distinguishes_exact_and_tolerant_arrays():
    integers = np.array([1, 2, 3], dtype=np.int16)
    assert b17.compare_array(integers, integers.copy(), exact=True)["match"]
    changed = integers.copy()
    changed[1] = 4
    result = b17.compare_array(changed, integers, exact=True)
    assert not result["match"]
    assert result["first_out_of_tolerance"] == [1]

    reference = np.array([0.25, -0.5], dtype=np.float32)
    within = reference + np.array([5e-8, 0.0], dtype=np.float32)
    tolerant = b17.compare_array(within, reference, exact=False)
    assert tolerant["match"] and not tolerant["exact_equal"]
    outside = reference + np.array([2e-5, 0.0], dtype=np.float32)
    failed = b17.compare_array(outside, reference, exact=False)
    assert not failed["match"] and failed["first_out_of_tolerance"] == [0]
    dtype_changed = b17.compare_array(reference.astype(np.float64), reference, exact=False)
    assert not dtype_changed["match"]


def test_replay_mismatch_stops_before_every_fresh_call_without_retry(
    loaded_assets, tmp_path, monkeypatch,
):
    calls = []
    monkeypatch.setattr(b17, "load_assets", lambda *args, **kwargs: loaded_assets)
    monkeypatch.setattr(b17, "_source_hashes", lambda: {"fixture": "stable"})
    monkeypatch.setattr(b17, "_input_identities", lambda records: {"fixture": {"stable": True}})
    monkeypatch.setattr(
        b17, "compare_replay",
        lambda row, trace, record: {
            "all_match": False,
            "trace_arrays": {"states": {"match": False, "first_out_of_tolerance": [0, 0, 0]}},
        },
    )

    def mismatch(record, n, phase, out, eval_spec, progress, **kwargs):
        calls.append((record.spec.key, n, phase))
        progress(7, 0, n, 2, 1)
        trace_path = out / f"fixture_{record.spec.key}_{phase}_{n}.npz"
        initial_states = np.zeros((eval_spec.eval_lanes, 133), dtype=np.float32)
        initial_observations = np.zeros((eval_spec.eval_lanes, n, 104), dtype=np.float32)
        np.savez(trace_path, initial_states=initial_states, initial_observations=initial_observations)
        return ({
            "status": "complete", "phase": phase, "asset_key": record.spec.key,
            "arm": record.spec.arm, "block": record.spec.block, "test_n": n,
            "world_seeds": list(range(b17.OLD_WORLD_SEED,
                                      b17.OLD_WORLD_SEED + eval_spec.eval_lanes)),
            "steps": 7, "episodes": 0, "resets": 1, "policy_step_calls": 2,
            "training_storage_calls": 1, "optimizer_calls": {"discoverer_actor": 2},
            "trace": {"path": str(trace_path)},
        }, {"initial_states": initial_states, "initial_observations": initial_observations})

    out = tmp_path / b17.TAG
    result = b17.run_study(
        out, "a" * 40, {"sha": "a" * 40}, RUN_ROOT, b17.PROTOCOL_SEED,
        eval_spec=b17.EvalSpec(test_ns=(8, 6, 4), horizon=20, eval_lanes=1),
        strict_contract=False, evaluate_fn=mismatch,
    )
    assert result == 1
    assert calls == [("b1_local1", 8, "replay")]
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["fresh_panels"] == []
    assert summary["fresh_interaction_started"] is False
    assert summary["replay_panels"][0]["replay_comparison"]["all_match"] is False
    assert Path(summary["replay_panels"][0]["trace"]["path"]).is_file()
    assert summary["counts"]["replay_team_steps"] == 7
    assert summary["counts"]["evaluation_team_steps"] == 7
    assert summary["counts"]["replay_uav_steps"] == 56
    assert summary["counts"]["evaluation_uav_steps"] == 56
    assert summary["counts"]["training_storage_calls"] == 1
    assert summary["counts"]["evaluation_optimizer_calls"] == 2
    assert "old replay arrays failed" in summary["failure"]
    assert (out / "error.txt").is_file()


def test_partial_fresh_failure_accounts_phase_costs_and_prohibited_calls(
    loaded_assets, tmp_path, monkeypatch,
):
    calls = []
    monkeypatch.setattr(b17, "load_assets", lambda *args, **kwargs: loaded_assets)
    monkeypatch.setattr(b17, "_source_hashes", lambda: {"fixture": "stable"})
    monkeypatch.setattr(b17, "_input_identities", lambda records: {"fixture": {"stable": True}})
    monkeypatch.setattr(
        b17, "compare_replay", lambda row, trace, record: {"all_match": True},
    )

    def evaluate(record, n, phase, out, eval_spec, progress, **kwargs):
        calls.append((record.spec.key, n, phase))
        trace_path = out / f"fixture_{record.spec.key}_{phase}_{n}.npz"
        initial_states = np.zeros((eval_spec.eval_lanes, 133), dtype=np.float32)
        initial_observations = np.zeros((eval_spec.eval_lanes, n, 104), dtype=np.float32)
        np.savez(trace_path, initial_states=initial_states, initial_observations=initial_observations)
        trace = {"initial_states": initial_states, "initial_observations": initial_observations}
        if phase == "replay":
            progress(3, 0, n, 1, 1)
            return ({
                "status": "complete", "phase": phase, "asset_key": record.spec.key,
                "arm": record.spec.arm, "block": record.spec.block, "test_n": n,
                "world_seeds": list(range(b17.OLD_WORLD_SEED,
                                          b17.OLD_WORLD_SEED + eval_spec.eval_lanes)),
                "steps": 3, "episodes": 0, "resets": 1, "policy_step_calls": 1,
                "training_storage_calls": 0, "optimizer_calls": {},
                "trace": {"path": str(trace_path)},
            }, trace)
        progress(2, 0, n, 1, 1)
        row = {
            "status": "failed", "failure": "fixture partial fresh failure",
            "phase": phase, "asset_key": record.spec.key, "arm": record.spec.arm,
            "block": record.spec.block, "test_n": n, "steps": 2,
            "episodes": 0, "resets": 1, "policy_step_calls": 1,
            "training_storage_calls": 1,
            "optimizer_calls": {"discoverer_actor": 1, "discoverer_critic": 2},
            "partial_trace": {"path": str(trace_path)},
        }
        raise b17.PanelFailure(row["failure"], row)

    out = tmp_path / b17.TAG
    result = b17.run_study(
        out, "a" * 40, {"sha": "a" * 40}, RUN_ROOT, b17.PROTOCOL_SEED,
        eval_spec=b17.EvalSpec(test_ns=(8, 6, 4), horizon=20, eval_lanes=1),
        strict_contract=False, evaluate_fn=evaluate,
    )
    assert result == 1
    assert calls == [
        (key, 8, "replay") for key in b17.POLICY_ORDER
    ] + [("b1_local1", 8, "fresh")]
    summary = json.loads((out / "summary.json").read_text())
    assert summary["counts"]["replay_panels"] == 6
    assert summary["counts"]["fresh_panels"] == 0
    assert summary["counts"]["panels"] == 6
    assert summary["counts"]["replay_team_steps"] == 18
    assert summary["counts"]["fresh_team_steps"] == 2
    assert summary["counts"]["evaluation_team_steps"] == 20
    assert summary["counts"]["replay_uav_steps"] == 144
    assert summary["counts"]["fresh_uav_steps"] == 16
    assert summary["counts"]["evaluation_uav_steps"] == 160
    assert summary["counts"]["training_storage_calls"] == 1
    assert summary["counts"]["evaluation_optimizer_calls"] == 3
    assert summary["fresh_panels"][0]["partial_trace"]["path"]
    assert summary["failure"].endswith("fixture partial fresh failure")


def _panel(key: str, block: int, arm: str, n: int, offset: float) -> dict:
    worlds = list(range(b17.FRESH_WORLD_SEEDS[n], b17.FRESH_WORLD_SEEDS[n] + 2))
    base = np.array([10.0 + offset, 12.0 + offset])
    return {
        "asset_key": key, "block": block, "arm": arm, "test_n": n,
        "world_seeds": worlds, "J": base.tolist(),
        "component_means": {
            "coverage_reward": (base / 50).tolist(),
            "quality_reward": (base / 30).tolist(),
            "energy_penalty": (base / 100).tolist(),
        },
        "service_arrays": {
            "E_eligible_users_per_step": (base + 20).tolist(),
            "S_served_users_per_step": base.tolist(),
            "U_eligible_unserved_users_per_step": np.full(2, 20.0).tolist(),
        },
    }


def test_reducer_keeps_n_blocks_adverse_worlds_and_old_new_gaps(loaded_assets):
    panels = []
    for block in (1, 2, 3):
        for n in (8, 6, 4):
            panels.append(_panel(f"b{block}_local1", block, "LOCAL1", n, 1.0))
            panels.append(_panel(f"b{block}_h6", block, "H6", n, 0.0))
    # One paired world loses J and S while its block mean remains positive.
    panels[12]["J"][0] = panels[13]["J"][0] - 0.25
    panels[12]["service_arrays"]["S_served_users_per_step"][0] = (
        panels[13]["service_arrays"]["S_served_users_per_step"][0] - 0.5
    )
    readings = b17.compute_readings(panels, loaded_assets, (8, 6, 4))
    assert set(readings["blocks"]) == {"1", "2", "3"}
    assert set(readings["by_n_descriptive_block_mean_dispersion"]) == {"8", "6", "4"}
    assert readings["blocks"]["3"]["8"]["adverse_J_or_S_worlds"]
    assert set(readings["blocks"]["1"]["new_minus_old_LOCAL1_minus_H6_gap"]) == {"8", "6"}
    assert "pooled-N" in readings["scope"]


def test_declared_production_cost_totals():
    counts = b17._expected_counts(b17.DEFAULT_SPEC)
    assert counts == {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_updates": 0, "replay_panels": 6, "fresh_panels": 18,
        "panels": 24, "replay_team_steps": 96_000, "fresh_team_steps": 288_000,
        "evaluation_team_steps": 384_000, "replay_uav_steps": 768_000,
        "fresh_uav_steps": 1_728_000, "evaluation_uav_steps": 2_496_000,
        "evaluation_episodes": 768, "evaluation_resets": 768,
        "batched_policy_step_calls": 12_000, "training_storage_calls": 0,
        "evaluation_optimizer_calls": 0,
    }


def test_production_cli_satisfies_native_kernel_guard_contract():
    from scripts.hmasd_launch import _validate_guard_contract

    _validate_guard_contract(
        b17.REPOSITORY_ROOT / "scripts/run_agent_count_fresh_world_deployment_b17.py",
        b17.DIRECTION,
    )


def test_cli_admits_before_candidate_import_and_passes_only_fixed_bindings(tmp_path, monkeypatch):
    from scripts import run_agent_count_fresh_world_deployment_b17 as cli

    events = []
    monkeypatch.setattr(cli, "require_admission", lambda *args, **kwargs: (
        events.append("admission") or {"sha": "a" * 40}
    ))
    original_import = builtins.__import__

    def observed_import(name, *args, **kwargs):
        if name == "experiments.candidates.agent_count_generalization.fresh_world_deployment_b17.runner":
            events.append("candidate_import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", observed_import)
    captured = {}

    def fake_run(*args, **kwargs):
        captured["args"], captured["kwargs"] = args, kwargs
        return 17

    out = tmp_path / cli.TAG
    result = cli.main([
        "--seed", str(cli.PROTOCOL_SEED), "--launch-sha", "a" * 40,
        "--out", str(out), "--input-root", str(RUN_ROOT),
    ], run_fn=fake_run)
    assert result == 17
    assert events[:2] == ["admission", "candidate_import"]
    assert captured["args"][3] == RUN_ROOT.resolve()
    assert captured["args"][4] == cli.PROTOCOL_SEED

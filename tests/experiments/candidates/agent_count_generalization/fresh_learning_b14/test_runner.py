"""Focused actual-path checks for the fixed B14 fresh H6/SET learning block."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.fresh_learning_b14 import runner
from scripts import run_agent_count_fresh_learning_b14 as entry


TECH_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=(8, 6), horizon=20, train_lanes=2,
    eval_lanes=2, rollouts=1, panels=(0, 1), hidden_size=16, n_heads=2,
    n_layers=1, ppo_epochs=1, sequence_batch_size=4,
    coordinator_batch_size=2, torch_threads=1,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as source:
        return {name: source[name].copy() for name in source.files}


def _run_cell(root: Path, cell: runner.TrainingCell, *, evaluate_initial: bool):
    transitions = []

    def instrument(agent):
        with torch.no_grad():
            agent.skill_discoverer.actor.act.action_out.logstd._bias.fill_(2.0)
        original = agent.store_transition_batch

        def store(*args, **kwargs):
            result = original(*args, **kwargs)
            t = int(kwargs["rollout_step_idx"])
            transitions.append({
                "t": t,
                "states": np.asarray(kwargs["states"]).copy(),
                "next_states": np.asarray(kwargs["next_states"]).copy(),
                "actions": np.asarray(kwargs["actions"]).copy(),
                "old_log_probs": np.asarray(kwargs["step_data"]["action_logprobs"]).copy(),
                "dones": np.asarray(kwargs["dones"]).copy(),
                "stored_actions": agent.rollout_buffer.actions[t].copy(),
                "stored_log_probs": agent.rollout_buffer.log_probs[t].copy(),
                "stored_dones": agent.rollout_buffer.dones[t].copy(),
                "storage_masks": agent.rollout_buffer.masks[t].copy(),
            })
            return result

        agent.store_transition_batch = store

    out = root / cell.tag
    assert runner.run_fit(
        out, cell, "technical-b14", {"sha": "technical-b14"}, TECH_SPEC,
        agent_setup_hook=instrument, evaluate_initial=evaluate_initial,
    ) == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), transitions


@pytest.fixture(scope="module")
def completed_cells(tmp_path_factory):
    root = tmp_path_factory.mktemp("fresh-learning-b14")
    return {
        cell.key: _run_cell(root, cell, evaluate_initial=True)
        for cell in runner.CELLS
    }


def test_fixed_contract_production_exposures_and_no_b07_b05_dependency():
    assert runner.OBJECT_ID == "s1_fresh_learning_b14"
    assert [(cell.key, cell.arm, cell.seed, cell.train_n, cell.tag) for cell in runner.CELLS] == [
        ("h6", "H6", 974201, 6, "s1_fresh_learning_b14_h6_s974201"),
        ("set", "SET", 974201, 6, "s1_fresh_learning_b14_set_s974201"),
    ]
    assert runner.TRAINING_ENV_SEED_BASE == 1_974_200
    assert runner.WORLD_SEED_BASES == {8: 1_645_800, 6: 1_645_600}
    assert runner.spec_for(runner.CELL_BY_KEY["h6"]) == replace(
        DEFAULT_SPEC, train_n=6, test_ns=(8, 6), eval_lanes=32, panels=(0, 45),
    )
    assert runner._expected_counts(runner.spec_for(runner.CELL_BY_KEY["set"])) == {
        "fits": 1, "training_team_steps": 360_000, "stored_team_steps": 360_000,
        "training_uav_steps": 2_160_000, "training_episodes": 720,
        "terminal_resets": 720, "updates": 45, "training_policy_step_calls": 22_500,
        "panels": 4, "evaluation_team_steps": 64_000,
        "evaluation_uav_steps": 448_000, "evaluation_episodes": 128,
        "evaluation_resets": 128, "evaluation_policy_step_calls": 2_000,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }
    assert runner._expected_optimizer_calls(runner.CELL_BY_KEY["h6"]) == {
        "coordinator": 675, "discoverer_actor": 101_250, "discoverer_critic": 101_250,
        "team_discriminator": 675, "individual_discriminator": 2_700,
    }
    assert runner._expected_optimizer_calls(runner.CELL_BY_KEY["set"]) == {
        "coordinator": 0, "discoverer_actor": 101_250, "discoverer_critic": 101_250,
        "team_discriminator": 0, "individual_discriminator": 0,
    }
    source_names = set(runner._source_hashes())
    assert not any("entropy_b05" in name or "bounded_package_b07" in name for name in source_names)


def test_both_real_collect_store_update_paths_and_initialization(completed_cells):
    initial_digests = {}
    for key, (_out, result, transitions) in completed_cells.items():
        cell = runner.CELL_BY_KEY[key]
        assert result["status"] == "complete" and result["fit_started"]
        assert result["object_id"] == runner.OBJECT_ID
        assert result["cell"] == {
            "key": cell.key, "arm": cell.arm, "tag": cell.tag, "seed": 974201,
            "train_n": 6, "law": "clip", "lambda_l": .05,
        }
        assert result["config"]["seed"] == 974201
        assert result["config"]["count_arm"] == cell.arm
        assert result["config"]["use_central_snapshot_in_flat_actor"] == (cell.arm == "SET")
        assert result["counts"] == runner._expected_counts(TECH_SPEC)
        assert result["training_world_seeds"] == [1_974_200, 1_974_201]
        assert len(transitions) == TECH_SPEC.horizon
        for transition in transitions:
            assert np.array_equal(transition["actions"], transition["stored_actions"])
            assert np.array_equal(transition["old_log_probs"], transition["stored_log_probs"])
            assert np.all(transition["storage_masks"])
        assert transitions[-1]["dones"].all()
        assert transitions[-1]["stored_dones"].all()
        assert not transitions[0]["dones"].any()
        rollout = result["rollouts"][0]
        witness = rollout["action_motion_telemetry"]["first_overrange_witness"]
        assert witness is not None and witness["stored_action_exact"]
        assert witness["stored_old_logprob_exact"]
        assert np.max(np.abs(witness["raw_action"])) > 1
        assert np.max(np.abs(witness["executed_action"])) <= 1
        assert result["optimizer_calls"]["discoverer_actor"] > 0
        assert result["optimizer_calls"]["discoverer_critic"] > 0
        assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
        assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0
        ownership = result["initialization"]["target_optimizer_ownership"]
        assert all(
            row is None or (
                row["target_parameters_exactly_once"]
                and row["no_canonical_parameters"] and row["state_is_empty"]
            )
            for row in ownership.values()
        )
        initial_digests[key] = result["observed_initial_parameter_normalizer_digest"]
        if cell.arm == "H6":
            assert result["initialization"]["method"] == (
                "native_h6_construction_no_cross_architecture_copy"
            )
            assert all(result["optimizer_calls"][name] > 0 for name in (
                "coordinator", "team_discriminator", "individual_discriminator",
            ))
        else:
            assert result["initialization"]["method"] == (
                "canonical_n6_sync_to_fresh_true_n_target"
            )
            assert result["initialization"]["canonical_n"] == 6
            assert all(result["optimizer_calls"][name] == 0 for name in (
                "coordinator", "team_discriminator", "individual_discriminator",
            ))
    assert initial_digests["h6"] != initial_digests["set"]


def test_symmetric_stage_panels_traces_inference_and_reset_scenes(completed_cells):
    reset_traces = {}
    evaluation_initial = {}
    for key, (out, result, transitions) in completed_cells.items():
        cell = runner.CELL_BY_KEY[key]
        assert [row["path"] for row in result["checkpoints"]] == [
            "checkpoint_00.pt", "checkpoint_01.pt",
        ]
        assert [(row["policy_stage"], row["test_n"]) for row in result["panels"]] == [
            (0, 8), (0, 6), (1, 8), (1, 6),
        ]
        assert set(result["stage_isolation"]) == {"0", "1"}
        for isolation in result["stage_isolation"].values():
            assert all(
                value for name, value in isolation.items() if name.endswith("_preserved")
            )
            assert isolation["training_mode_preserved"]
            assert isolation["buffer_content_digest_preserved"]
            assert isolation["buffer_env_lengths_preserved"]
            assert isolation["buffer_last_t_per_env_preserved"]
        evaluation_initial[key] = {}
        for row in result["panels"]:
            assert row["world_seeds"] == list(range(
                runner.WORLD_SEED_BASES[row["test_n"]],
                runner.WORLD_SEED_BASES[row["test_n"]] + TECH_SPEC.eval_lanes,
            ))
            assert row["runtime_seed"] == runner.WORLD_SEED_BASES[row["test_n"]] + 51
            assert row["frozen_weights_and_normalizers"]
            assert row["training_storage_calls"] == 0
            assert not any(row["optimizer_calls"].values())
            assert row["executed_action_bounds"]["minimum"] >= -1
            assert row["executed_action_bounds"]["maximum"] <= 1
            assert row["runtime_evolved"] and row["post_transition_semantics"]
            panel_path = out / f"panel_stage{row['policy_stage']:02d}_n{row['test_n']}.json"
            trace_path = out / f"trace_stage{row['policy_stage']:02d}_n{row['test_n']}.npz"
            assert panel_path.is_file() and trace_path.is_file()
            trace = _load_npz(trace_path)
            assert trace["raw_actions"].shape == (
                TECH_SPEC.horizon, TECH_SPEC.eval_lanes, row["test_n"], 3,
            )
            assert np.all(trace["executed_actions"] >= -1)
            assert np.all(trace["executed_actions"] <= 1)
            assert trace["states"].shape == (TECH_SPEC.horizon, TECH_SPEC.eval_lanes, 133)
            assert trace["observations"].shape == (
                TECH_SPEC.horizon, TECH_SPEC.eval_lanes, row["test_n"], 104,
            )
            evaluation_initial[key][(row["policy_stage"], row["test_n"])] = (
                trace["initial_states"], trace["initial_observations"],
            )
            inference = row["inference_counts"]
            assert inference["coordinator_batched_calls"] == 2
            assert inference["coordinator_rows"] == 4
            assert inference["decoder_team_calls"] == 2
            assert inference["decoder_individual_calls"] == 2 * row["test_n"]
            if cell.arm == "SET":
                assert inference["team_choice_counts"][0] == 4
                assert inference["set_snapshot_refresh_steps"] == 2
                assert inference["set_snapshot_lane_refreshes"] == 4
            else:
                assert inference["set_snapshot_refresh_steps"] is None
        training_inference = result["training_inference_counts"]
        assert training_inference["coordinator_batched_calls"] == 2
        assert training_inference["coordinator_rows"] == 4
        assert training_inference["decoder_individual_calls"] == 12
        if cell.arm == "SET":
            assert training_inference["team_choice_counts"][0] == 4
            assert training_inference["set_snapshot_refresh_steps"] == 2
        reset_traces[key] = _load_npz(out / "training_reset_scenes.npz")
        assert result["training_reset_trace"]["reset_calls_per_lane"] == 2
        assert not np.array_equal(transitions[-1]["next_states"], reset_traces[key]["states"][1])
        assert set(result["stage_readings"]["by_test_n"]) == {"8", "6"}
    for name in ("states", "observations", "uav_positions", "user_positions", "rng_sha256"):
        assert np.array_equal(reset_traces["h6"][name], reset_traces["set"][name])
    for stage in (0, 1):
        for n in (8, 6):
            assert np.array_equal(
                evaluation_initial["h6"][(stage, n)][0],
                evaluation_initial["set"][(stage, n)][0],
            )
            assert np.array_equal(
                evaluation_initial["h6"][(stage, n)][1],
                evaluation_initial["set"][(stage, n)][1],
            )


@pytest.mark.parametrize("key", ["h6", "set"])
def test_initial_evaluation_has_no_training_effect(completed_cells, tmp_path, key):
    cell = runner.CELL_BY_KEY[key]
    with_initial_out, with_initial, _transitions = completed_cells[key]
    without_out, without_initial, _without_transitions = _run_cell(
        tmp_path / key, cell, evaluate_initial=False,
    )
    assert set(with_initial["stage_isolation"]["0"]) >= {
        "parameter_normalizer_digest_preserved", "runtime_digest_preserved",
        "global_rng_digest_preserved", "sampler_rng_digest_preserved",
        "optimizer_state_digest_preserved", "training_environment_digest_preserved",
        "training_mode_preserved", "buffer_content_digest_preserved",
        "buffer_env_lengths_preserved", "buffer_last_t_per_env_preserved",
    }
    assert without_initial["initial_evaluation_enabled"] is False
    assert [(row["policy_stage"], row["test_n"]) for row in without_initial["panels"]] == [
        (1, 8), (1, 6),
    ]
    assert with_initial["final_parameter_normalizer_digest"] == without_initial[
        "final_parameter_normalizer_digest"
    ]
    assert with_initial["optimizer_calls"] == without_initial["optimizer_calls"]
    assert with_initial["training_inference_counts"] == without_initial[
        "training_inference_counts"
    ]
    left = _load_npz(with_initial_out / "training_reset_scenes.npz")
    right = _load_npz(without_out / "training_reset_scenes.npz")
    assert left.keys() == right.keys()
    assert all(np.array_equal(left[name], right[name]) for name in left)
    assert (with_initial_out / "training.jsonl").read_text().splitlines()[0].split(
        '"rollout_wall_seconds"'
    )[0] == (without_out / "training.jsonl").read_text().splitlines()[0].split(
        '"rollout_wall_seconds"'
    )[0]


def test_failure_accounting_source_identity_and_cli(monkeypatch, tmp_path):
    cell = runner.CELL_BY_KEY["h6"]

    def stop(event):
        if event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected B14 transition failure")

    out = tmp_path / "failure" / cell.tag
    assert runner.run_fit(
        out, cell, "technical-failure", {"sha": "technical-failure"}, TECH_SPEC,
        training_step_hook=stop, evaluate_initial=False,
    ) == 1
    failed = _read(out / "summary.json")
    assert failed["status"] == "failed" and failed["fit_started"]
    assert failed["counts"]["training_team_steps"] == 1
    assert failed["counts"]["training_uav_steps"] == 6
    assert failed["counts"]["stored_team_steps"] == 0
    assert failed["counts"]["updates"] == 0
    assert failed["incomplete_rollout"]["phase"] == "collecting_failed"
    assert failed["incomplete_rollout"]["action_motion_telemetry_partial"]["team_steps"] == 1
    assert failed["source_hashes_unchanged"]
    required = {
        "experiments/candidates/agent_count_generalization/fresh_learning_b14/runner.py",
        "scripts/run_agent_count_fresh_learning_b14.py",
        "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        "experiments/candidates/agent_count_generalization/ordinary_control_b13/runner.py",
    }
    assert required <= failed["source_hashes_before"].keys()

    calls = []
    monkeypatch.setattr(
        entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "x"},
    )
    set_cell = runner.CELL_BY_KEY["set"]
    result = entry.main([
        "--cell", "set", "--seed", "974201", "--launch-sha", "x",
        "--out", str(tmp_path / set_cell.tag),
    ], run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 7)
    assert result == 7 and calls[0] == "admit"
    args, kwargs = calls[1]
    assert args[1] == set_cell and args[2] == "x" and args[3] == {"sha": "x"}
    assert kwargs["command_start"] == entry.COMMAND_START

    calls.clear()
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main([
            "--cell", "h6", "--seed", "974201", "--launch-sha", "wrong",
            "--out", str(tmp_path / cell.tag),
        ])
    assert calls == ["admit"]
    calls.clear()
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "h6", "--seed", "963401", "--launch-sha", "x",
            "--out", str(tmp_path / cell.tag),
        ])
    assert calls == []
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "h6", "--seed", "974201", "--launch-sha", "x",
            "--out", str(tmp_path / "s1_bounded_package_b07_h6_l05_s952201"),
        ])
    assert calls == []

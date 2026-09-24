"""Focused actual-path checks for the three fixed B16 LOCAL1 cells."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner
from scripts import run_agent_count_local_ordinary_b16 as entry
from scripts.hmasd_admission import ENVIRONMENT_KEY


TECH_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=(8, 6), horizon=20, train_lanes=2,
    eval_lanes=2, rollouts=1, panels=(0, 1), hidden_size=16, n_heads=2,
    n_layers=1, ppo_epochs=1, sequence_batch_size=4,
    coordinator_batch_size=2, torch_threads=1,
)
PRODUCTION_CELLS = tuple(runner.CELLS)
PRODUCTION_CELL_BY_KEY = dict(runner.CELL_BY_KEY)
PRODUCTION_WORLD_SEED_BASES = dict(runner.WORLD_SEED_BASES)
TECH_WORLD_SEED_BASES = {8: 8_945_800, 6: 8_945_600}
TECH_CELL = replace(
    PRODUCTION_CELL_BY_KEY["b1_local1"], key="tech_b1_local1", seed=8_994_101,
    tag="technical_b16_b1_local1_s8994101", training_env_seed_base=8_994_100,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as source:
        return {name: source[name].copy() for name in source.files}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_cell(root: Path, *, evaluate_initial: bool = True):
    transitions = []
    actor_input_widths = []
    construction = {}

    def instrument(agent):
        construction.update(
            actor_base=type(agent.skill_discoverer.actor.base).__name__,
            critic_base=type(agent.skill_discoverer.critic.base).__name__,
            use_central_snapshot=agent.use_central_snapshot,
            buffer_central_snapshot=agent.rollout_buffer.central_snapshot,
            actor_parameter_ids={id(p) for p in agent.skill_discoverer.actor.parameters()},
            actor_optimizer_ids={
                id(p) for group in agent.discoverer_actor_optimizer.param_groups
                for p in group["params"]
            },
            critic_parameter_ids={id(p) for p in agent.skill_discoverer.critic.parameters()},
            critic_optimizer_ids={
                id(p) for group in agent.discoverer_critic_optimizer.param_groups
                for p in group["params"]
            },
        )
        agent.skill_discoverer.actor.base.register_forward_pre_hook(
            lambda _module, args: actor_input_widths.append(int(args[0].shape[-1]))
        )
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
                "team_skills": np.asarray(kwargs["step_data"]["team_skills"]).copy(),
                "agent_skills": np.asarray(kwargs["step_data"]["agent_skills"]).copy(),
                "skill_changed": np.asarray(kwargs["step_data"]["skill_changed"]).copy(),
                "dones": np.asarray(kwargs["dones"]).copy(),
                "input_actor_hidden": agent.prev_actor_hidden_np[:TECH_SPEC.train_lanes].copy(),
                "stored_actions": agent.rollout_buffer.actions[t].copy(),
                "stored_log_probs": agent.rollout_buffer.log_probs[t].copy(),
                "stored_dones": agent.rollout_buffer.dones[t].copy(),
            })
            return result

        agent.store_transition_batch = store

    out = root / TECH_CELL.tag
    assert runner.run_fit(
        out, TECH_CELL, "technical-b16", {"sha": "technical-b16"}, TECH_SPEC,
        agent_setup_hook=instrument, evaluate_initial=evaluate_initial,
    ) == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), transitions, actor_input_widths, construction


@pytest.fixture(scope="module")
def completed_cell(tmp_path_factory):
    root = tmp_path_factory.mktemp("local-ordinary-b16")
    patcher = pytest.MonkeyPatch()
    patcher.setattr(runner, "CELLS", PRODUCTION_CELLS + (TECH_CELL,))
    patcher.setattr(
        runner, "CELL_BY_KEY", {**PRODUCTION_CELL_BY_KEY, TECH_CELL.key: TECH_CELL},
    )
    patcher.setattr(runner, "WORLD_SEED_BASES", TECH_WORLD_SEED_BASES)
    try:
        yield _run_cell(root)
    finally:
        patcher.undo()


def test_fixed_cells_and_production_exposure_contract():
    assert runner.OBJECT_ID == "s1_local_ordinary_b16"
    assert [
        (cell.key, cell.arm, cell.seed, cell.block, cell.training_env_seed_base, cell.tag)
        for cell in PRODUCTION_CELLS
    ] == [
        ("b1_local1", "LOCAL1", 994101, 1, 2_994_100,
         "s1_local_ordinary_b16_b1_local1_s994101"),
        ("b2_local1", "LOCAL1", 994102, 2, 2_994_200,
         "s1_local_ordinary_b16_b2_local1_s994102"),
        ("b3_local1", "LOCAL1", 994103, 3, 2_994_300,
         "s1_local_ordinary_b16_b3_local1_s994103"),
    ]
    assert PRODUCTION_WORLD_SEED_BASES == {8: 1_945_800, 6: 1_945_600}
    for cell in PRODUCTION_CELLS:
        assert runner.spec_for(cell) == replace(
            DEFAULT_SPEC, train_n=6, test_ns=(8, 6), eval_lanes=32, panels=(0, 45),
        )
    spec = runner.spec_for(PRODUCTION_CELL_BY_KEY["b1_local1"])
    assert runner.b15._expected_counts(spec) == {
        "fits": 1, "training_team_steps": 360_000, "stored_team_steps": 360_000,
        "training_uav_steps": 2_160_000, "training_episodes": 720,
        "terminal_resets": 720, "updates": 45, "training_policy_step_calls": 22_500,
        "panels": 4, "evaluation_team_steps": 64_000,
        "evaluation_uav_steps": 448_000, "evaluation_episodes": 128,
        "evaluation_resets": 128, "evaluation_policy_step_calls": 2_000,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }
    assert runner._expected_optimizer_calls(PRODUCTION_CELLS[0]) == {
        "coordinator": 0, "discoverer_actor": 101_250,
        "discoverer_critic": 101_250, "team_discriminator": 0,
        "individual_discriminator": 0,
    }
    assert sum(runner._expected_optimizer_calls(cell)["discoverer_actor"] for cell in PRODUCTION_CELLS) == 303_750


def test_real_local_collection_replay_update_and_terminal_successor(completed_cell):
    out, result, transitions, actor_input_widths, construction = completed_cell
    assert result["status"] == "complete" and result["fit_started"]
    assert result["config"]["count_arm"] == "LOCAL1"
    assert result["config"]["algorithm"] == "mappo"
    assert result["config"]["n_z"] == result["config"]["n_Z"] == 1
    assert result["config"]["num_team_codes"] == 1
    assert result["config"]["k"] == 10
    assert result["config"]["use_central_snapshot_in_flat_actor"] is False
    assert result["config"]["disable_high_level_training"] is True
    assert result["config"]["disable_discriminator_training"] is True
    assert result["config"]["disable_discriminator_rewards"] is True
    assert result["initialization"]["method"] == (
        "fresh_true_n_local1_construction_no_cross_architecture_copy"
    )
    assert result["initialization"]["actor_input_width"] == 104
    assert result["initialization"]["actor_base_type"] == "MLPBase"
    assert result["initialization"]["critic_base_type"] == "StateSetEncoder"
    assert result["initialization"]["actor_has_trainable_film"]
    assert result["initialization"]["actor_has_gru"]
    assert result["initialization"]["central_snapshot_enabled"] is False
    assert construction["actor_base"] == "MLPBase"
    assert construction["critic_base"] == "StateSetEncoder"
    assert construction["use_central_snapshot"] is False
    assert construction["buffer_central_snapshot"] is False
    assert construction["actor_parameter_ids"] == construction["actor_optimizer_ids"]
    assert construction["critic_parameter_ids"] == construction["critic_optimizer_ids"]
    assert actor_input_widths and set(actor_input_widths) == {104}

    assert len(transitions) == TECH_SPEC.horizon
    assert all(np.all(row["team_skills"] == 0) for row in transitions)
    assert all(np.all(row["agent_skills"] == 0) for row in transitions)
    assert transitions[0]["skill_changed"].all()
    assert transitions[10]["skill_changed"].all()
    assert np.count_nonzero(transitions[0]["input_actor_hidden"]) == 0
    assert np.count_nonzero(transitions[1]["input_actor_hidden"]) > 0
    assert np.count_nonzero(transitions[10]["input_actor_hidden"]) > 0
    for transition in transitions:
        assert np.array_equal(transition["actions"], transition["stored_actions"])
        assert np.array_equal(transition["old_log_probs"], transition["stored_log_probs"])
    assert transitions[-1]["dones"].all()
    assert transitions[-1]["stored_dones"].all()
    reset_trace = _load_npz(out / "training_reset_scenes.npz")
    assert not np.array_equal(transitions[-1]["next_states"], reset_trace["states"][1])

    witness = result["rollouts"][0]["action_motion_telemetry"]["first_overrange_witness"]
    assert witness is not None and witness["stored_action_exact"]
    assert witness["stored_old_logprob_exact"]
    assert np.max(np.abs(witness["raw_action"])) > 1
    assert np.max(np.abs(witness["executed_action"])) <= 1
    assert result["optimizer_calls"]["discoverer_actor"] > 0
    assert result["optimizer_calls"]["discoverer_critic"] > 0
    assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
    assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0
    assert all(result["optimizer_calls"][name] == 0 for name in (
        "coordinator", "team_discriminator", "individual_discriminator",
    ))
    ownership = result["initialization"]["target_optimizer_ownership"]
    assert all(
        row is None or (
            row["target_parameters_exactly_once"]
            and row["no_canonical_parameters"] and row["state_is_empty"]
        )
        for row in ownership.values()
    )


def test_strict_across_n_panels_snapshot_zero_and_evaluation_isolation(completed_cell):
    out, result, _transitions, _actor_input_widths, _construction = completed_cell
    assert [row["path"] for row in result["checkpoints"]] == [
        "checkpoint_00.pt", "checkpoint_01.pt",
    ]
    assert [(row["policy_stage"], row["test_n"]) for row in result["panels"]] == [
        (0, 8), (0, 6), (1, 8), (1, 6),
    ]
    assert set(result["stage_isolation"]) == {"0", "1"}
    for isolation in result["stage_isolation"].values():
        assert all(value for name, value in isolation.items() if name.endswith("_preserved"))
    for row in result["panels"]:
        assert row["world_seeds"] == list(range(
            TECH_WORLD_SEED_BASES[row["test_n"]],
            TECH_WORLD_SEED_BASES[row["test_n"]] + TECH_SPEC.eval_lanes,
        ))
        assert row["runtime_seed"] == TECH_WORLD_SEED_BASES[row["test_n"]] + 51
        assert row["config"]["count_arm"] == "LOCAL1"
        assert row["config"]["n_agents"] == row["test_n"]
        assert row["config"]["use_central_snapshot_in_flat_actor"] is False
        expected_digest = (
            result["observed_initial_parameter_normalizer_digest"]
            if row["policy_stage"] == 0
            else result["final_parameter_normalizer_digest"]
        )
        assert row["parameter_normalizer_digest_before"] == expected_digest
        assert row["frozen_weights_and_normalizers"]
        assert row["training_storage_calls"] == 0
        assert not any(row["optimizer_calls"].values())
        assert row["inference_counts"]["team_choice_counts"] == [4]
        assert row["inference_counts"]["individual_choice_counts"] == [4 * row["test_n"]]
        assert row["inference_counts"]["set_snapshot_refresh_steps"] == 0
        assert row["inference_counts"]["set_snapshot_lane_refreshes"] == 0
        assert row["executed_action_bounds"]["minimum"] >= -1
        assert row["executed_action_bounds"]["maximum"] <= 1
        trace_path = out / f"trace_stage{row['policy_stage']:02d}_n{row['test_n']}.npz"
        trace = _load_npz(trace_path)
        assert row["trace"]["sha256"] == _sha256(trace_path)
        assert trace["states"].shape == (TECH_SPEC.horizon, TECH_SPEC.eval_lanes, 133)
        assert trace["observations"].shape == (
            TECH_SPEC.horizon, TECH_SPEC.eval_lanes, row["test_n"], 104,
        )
        assert np.all(trace["executed_actions"] >= -1)
        assert np.all(trace["executed_actions"] <= 1)
    assert result["training_inference_counts"]["team_choice_counts"] == [4]
    assert result["training_inference_counts"]["individual_choice_counts"] == [24]
    assert result["training_inference_counts"]["set_snapshot_refresh_steps"] == 0
    assert result["training_inference_counts"]["set_snapshot_lane_refreshes"] == 0
    assert result["evaluation_inference_counts"]["set_snapshot_refresh_steps"] == 0
    assert result["evaluation_inference_counts"]["set_snapshot_lane_refreshes"] == 0
    assert set(result["stage_readings"]["by_test_n"]) == {"8", "6"}
    assert result["resources"]["artifact_bytes_excluding_summary"] > 0
    assert result["resources"]["artifact_files_excluding_summary"] > 0
    assert result["source_hashes_before"] == result["source_hashes_after"]


def test_initial_evaluation_has_no_training_effect(completed_cell, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "CELLS", PRODUCTION_CELLS + (TECH_CELL,))
    monkeypatch.setattr(runner, "WORLD_SEED_BASES", TECH_WORLD_SEED_BASES)
    with_initial_out, with_initial, *_ = completed_cell
    without_out, without_initial, *_ = _run_cell(
        tmp_path / "without-initial", evaluate_initial=False,
    )
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


def test_transition_failure_is_retained_and_counts_started_fit(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "CELLS", PRODUCTION_CELLS + (TECH_CELL,))
    monkeypatch.setattr(runner, "WORLD_SEED_BASES", TECH_WORLD_SEED_BASES)

    def stop(event):
        if event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected B16 transition failure")

    out = tmp_path / "failure" / TECH_CELL.tag
    assert runner.run_fit(
        out, TECH_CELL, "technical-failure", {"sha": "technical-failure"},
        TECH_SPEC, training_step_hook=stop, evaluate_initial=False,
    ) == 1
    failed = _read(out / "summary.json")
    assert failed["status"] == "failed" and failed["fit_started"]
    assert failed["counts"]["fits"] == 1
    assert failed["counts"]["training_team_steps"] == 1
    assert failed["counts"]["training_uav_steps"] == 6
    assert failed["counts"]["stored_team_steps"] == 0
    assert failed["counts"]["updates"] == 0
    assert failed["incomplete_rollout"]["phase"] == "collecting_failed"
    assert failed["incomplete_rollout"]["action_motion_telemetry_partial"]["team_steps"] == 1
    assert failed["source_hashes_unchanged"]
    assert "injected B16 transition failure" in failed["failure"]


def test_stage0_failure_does_not_count_a_started_fit(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "CELLS", PRODUCTION_CELLS + (TECH_CELL,))
    monkeypatch.setattr(runner, "WORLD_SEED_BASES", TECH_WORLD_SEED_BASES)
    original_make_envs = runner.make_envs

    class FailOnStep:
        def __init__(self, env):
            self._env = env

        def __getattr__(self, name):
            return getattr(self._env, name)

        def step(self, _actions):
            raise RuntimeError("injected B16 stage0 failure")

    def make_envs(lanes, seed, n, horizon):
        envs = original_make_envs(lanes, seed, n, horizon)
        if seed == TECH_WORLD_SEED_BASES[8] and n == 8:
            envs[0] = FailOnStep(envs[0])
        return envs

    monkeypatch.setattr(runner, "make_envs", make_envs)
    out = tmp_path / "stage0-failure" / TECH_CELL.tag
    assert runner.run_fit(
        out, TECH_CELL, "technical-stage0-failure",
        {"sha": "technical-stage0-failure"}, TECH_SPEC, evaluate_initial=True,
    ) == 1
    failed = _read(out / "summary.json")
    assert failed["status"] == "failed" and not failed["fit_started"]
    assert failed["counts"]["fits"] == 0
    assert failed["counts"]["training_team_steps"] == 0
    assert failed["counts"]["stored_team_steps"] == 0
    assert failed["counts"]["updates"] == 0
    assert failed["counts"]["evaluation_resets"] == TECH_SPEC.eval_lanes
    assert failed["counts"]["evaluation_policy_step_calls"] == 1
    assert failed["counts"]["evaluation_team_steps"] == 0
    assert failed["panels"][0]["status"] == "failed"
    assert "injected B16 stage0 failure" in failed["panels"][0]["failure"]


def test_cli_validates_bindings_before_native_admission(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "x"},
    )
    for key, (seed, tag) in entry.CELL_BINDINGS.items():
        calls.clear()
        result = entry.main([
            "--cell", key, "--seed", str(seed), "--launch-sha", "x",
            "--out", str(tmp_path / tag),
        ], run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 7)
        assert result == 7 and calls[0] == "admit"
        args, kwargs = calls[1]
        assert args[1] == PRODUCTION_CELL_BY_KEY[key]
        assert args[2] == "x" and args[3] == {"sha": "x"}
        assert kwargs["command_start"] == entry.COMMAND_START

    calls.clear()
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "b1_local1", "--seed", "994102", "--launch-sha", "x",
            "--out", str(tmp_path / PRODUCTION_CELL_BY_KEY["b1_local1"].tag),
        ])
    assert calls == []
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "b1_local1", "--seed", "994101", "--launch-sha", "x",
            "--out", str(tmp_path / "wrong-tag"),
        ])
    assert calls == []
    calls.clear()
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main([
            "--cell", "b1_local1", "--seed", "994101", "--launch-sha", "wrong",
            "--out", str(tmp_path / PRODUCTION_CELL_BY_KEY["b1_local1"].tag),
        ])
    assert calls == ["admit"]


def test_direct_cli_refuses_without_admission_before_creating_output(tmp_path):
    out = tmp_path / "s1_local_ordinary_b16_b1_local1_s994101"
    environment = dict(os.environ)
    environment.pop(ENVIRONMENT_KEY, None)
    result = subprocess.run(
        [sys.executable, str(Path(entry.__file__).resolve()),
         "--cell", "b1_local1", "--seed", "994101",
         "--launch-sha", "0" * 40, "--out", str(out)],
        cwd=entry.ROOT, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()

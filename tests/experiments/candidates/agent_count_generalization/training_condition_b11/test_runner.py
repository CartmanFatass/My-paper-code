"""Focused native checks for the fixed B11 SET training-condition runner."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.runner import COMPONENTS, digest_agent, seed_rng
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner
from scripts import run_agent_count_training_condition_b11 as entry


TECH_BASE = replace(
    DEFAULT_SPEC, horizon=20, train_lanes=2, eval_lanes=2, rollouts=1,
    panels=(1,), test_ns=(8, 6), hidden_size=16, n_heads=2, n_layers=1,
    ppo_epochs=1, sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_actual_config(cell: runner.TrainingCell, root: Path):
    spec = runner.spec_for(cell, TECH_BASE)
    envs = make_envs(spec.train_lanes, runner.TRAINING_ENV_SEED_BASE, cell.train_n, spec.horizon)
    try:
        seed_rng(cell.seed)
        return runner.make_b11_config(cell, envs, spec), spec
    finally:
        for env in envs:
            env.close()


def test_fixed_cells_exposure_and_world_contract():
    assert [(cell.key, cell.train_n, cell.seed, cell.tag) for cell in runner.CELLS] == [
        ("t6", 6, 963201, "s1_training_condition_b11_t6_s963201"),
        ("t8", 8, 963201, "s1_training_condition_b11_t8_s963201"),
    ]
    assert runner._panel_world_seed(8) == 1_645_800
    assert runner._panel_world_seed(6) == 1_645_600
    assert runner._expected_counts(runner.spec_for(runner.CELL_BY_KEY["t8"])) == {
        "fits": 1, "training_team_steps": 360000, "stored_team_steps": 360000,
        "training_agent_rows": 2880000, "training_episodes": 720,
        "terminal_resets": 720, "updates": 45, "training_policy_step_calls": 22500,
        "panels": 2, "evaluation_team_steps": 32000, "evaluation_uav_steps": 224000,
        "evaluation_episodes": 64, "evaluation_resets": 64,
        "evaluation_policy_step_calls": 1000, "evaluation_storage_calls": 0,
        "evaluation_optimizer_calls": 0,
    }
    assert runner._expected_production_optimizer_calls(runner.CELL_BY_KEY["t6"])[
        "discoverer_actor"
    ] == 101250
    assert runner._expected_production_optimizer_calls(runner.CELL_BY_KEY["t8"])[
        "discoverer_critic"
    ] == 135000


def test_common_initialization_exact_across_true_n_and_preserves_rng(tmp_path):
    records, agents = {}, []
    for key in ("t6", "t8"):
        cell = runner.CELL_BY_KEY[key]
        config, _spec = _make_actual_config(cell, tmp_path)
        seed_rng(cell.seed)
        agent, record = runner.construct_common_initialized_agent(
            config, tmp_path / key,
        )
        agents.append(agent)
        records[key] = record
        assert agent.training
        assert int(agent.config.n_agents) == cell.train_n
        assert int(agent.rollout_buffer.n_agents) == cell.train_n
        assert record["returned_rng_digest"] == record["canonical_post_initialization_rng_digest"]
        assert all(
            row is None or (
                row["target_parameters_exactly_once"]
                and row["no_canonical_parameters"]
                and row["state_is_empty"]
            )
            for row in record["target_optimizer_ownership"].values()
        )
    assert records["t6"]["tensor_manifest"] == records["t8"]["tensor_manifest"]
    assert records["t6"]["normalizers"] == records["t8"]["normalizers"]
    assert records["t6"]["parameter_normalizer_digest"] == records["t8"][
        "parameter_normalizer_digest"
    ]
    assert records["t6"]["target_initial_buffer"]["sampler_state"] == records["t8"][
        "target_initial_buffer"
    ]["sampler_state"]
    assert records["t6"]["canonical_post_initialization_rng_digest"] == records["t8"][
        "canonical_post_initialization_rng_digest"
    ]
    assert digest_agent(agents[0]) == digest_agent(agents[1])


def test_strict_sync_copies_nondefault_normalizer_to_true_n_target(tmp_path):
    cell = runner.CELL_BY_KEY["t8"]
    config, _spec = _make_actual_config(cell, tmp_path)
    calls = 0

    def build(config_value, log_dir):
        nonlocal calls
        from experiments.candidates.agent_count_generalization.models import build_agent
        calls += 1
        agent = build_agent(config_value, log_dir)
        if calls == 1:
            agent.value_norm_discoverer.mean = np.asarray(2.5)
            agent.value_norm_discoverer.var = np.asarray(3.75)
            agent.value_norm_discoverer.count = 19.0
        return agent

    seed_rng(cell.seed)
    target, record = runner.construct_common_initialized_agent(config, tmp_path, build_fn=build)
    assert float(target.value_norm_discoverer.mean) == 2.5
    assert float(target.value_norm_discoverer.var) == 3.75
    assert float(target.value_norm_discoverer.count) == 19.0
    assert record["normalizers"]["value_norm_discoverer"]["count"] == 19.0


@pytest.fixture(scope="module")
def completed_cells(tmp_path_factory):
    root = tmp_path_factory.mktemp("training-condition-b11")
    results = {}
    for cell in runner.CELLS:
        out = root / cell.tag
        spec = runner.spec_for(cell, TECH_BASE)
        assert runner.run_fit(
            out, cell, "technical-b11", {"sha": "technical-b11"}, spec,
        ) == 0, (out / "summary.json").read_text(encoding="utf-8")
        results[cell.key] = (out, _read(out / "summary.json"))
    return results


def test_real_collect_store_update_final_only_and_common_initialization(completed_cells):
    t6 = completed_cells["t6"][1]
    t8 = completed_cells["t8"][1]
    for key, (out, result) in completed_cells.items():
        cell = runner.CELL_BY_KEY[key]
        spec = runner.spec_for(cell, TECH_BASE)
        assert result["status"] == "complete" and result["fit_started"]
        assert result["counts"] == runner._expected_counts(spec)
        assert [row["path"] for row in result["checkpoints"]] == [
            "checkpoint_00.pt", "checkpoint_01.pt",
        ]
        assert [row["test_n"] for row in result["panels"]] == [8, 6]
        assert not (out / "panel_00_n8.json").exists()
        assert len((out / "training.jsonl").read_text(encoding="utf-8").splitlines()) == 1
        rollout = result["rollouts"][0]
        assert rollout["action_motion_telemetry"]["old_logprob_unchanged"]
        assert rollout["action_motion_telemetry"]["policy_output_unchanged"]
        assert rollout["action_motion_telemetry"]["executed_min"] >= -1
        assert rollout["action_motion_telemetry"]["executed_max"] <= 1
        assert result["optimizer_calls"]["discoverer_actor"] > 0
        assert result["optimizer_calls"]["discoverer_critic"] > 0
        assert result["optimizer_calls"]["discoverer_actor"] == cell.train_n
        assert result["optimizer_calls"]["discoverer_critic"] == cell.train_n
        assert all(result["optimizer_calls"][name] == 0 for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        ))
        assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
        assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0
        assert result["final_evaluation_learner_isolation"]["model_preserved"]
        assert result["final_evaluation_learner_isolation"]["runtime_preserved"]
        assert result["final_evaluation_learner_isolation"]["global_rng_preserved"]
        for row in result["panels"]:
            assert row["frozen_weights_and_normalizers"]
            assert not any(row["optimizer_calls"].values())
            assert row["training_storage_calls"] == 0
            assert row["runtime_evolved"]
            assert row["post_transition_semantics"]
            assert row["max_connections_per_uav"] == 10
            assert row["n_users"] == 50
            assert Path(row["trace"]["path"]).is_file()
    assert t6["common_initialization"]["tensor_manifest"] == t8["common_initialization"][
        "tensor_manifest"
    ]
    assert t6["observed_initial_parameter_normalizer_digest"] == t8[
        "observed_initial_parameter_normalizer_digest"
    ]


def test_saved_traces_recompute_native_service_components_and_world_identity(completed_cells):
    initial_by_cell = {}
    for key, (_out, result) in completed_cells.items():
        initial_by_cell[key] = {}
        for panel in result["panels"]:
            n = panel["test_n"]
            with np.load(panel["trace"]["path"], allow_pickle=False) as trace:
                arrays = {name: trace[name] for name in trace.files}
            initial_by_cell[key][n] = (
                arrays["initial_states"], arrays["initial_observations"],
            )
            connections = arrays["connections"]
            eligible = arrays["eligible_links"]
            served = connections.any(axis=-2).sum(axis=-1)
            eligible_users = eligible.any(axis=-2)
            unserved = (eligible_users & ~connections.any(axis=-2)).sum(axis=-1)
            assert np.array_equal(served, arrays["served_user_counts"])
            assert np.array_equal(eligible_users.sum(axis=-1), arrays["eligible_user_counts"])
            assert np.array_equal(unserved, arrays["eligible_unserved_user_counts"])
            assert np.all(connections.sum(axis=-2) <= 1)
            assert np.all(connections.sum(axis=-1) <= 10)
            coverage = served / 50.0
            quality = arrays["connected_quality_sum"] / np.maximum(served, 1)
            low, high = panel["height_range"]
            penalty = ((arrays["uav_heights"].mean(axis=-1) - low) / (high - low)) * .1
            assert np.allclose(coverage, arrays["coverage_reward"], atol=1e-10, rtol=0)
            assert np.allclose(quality, arrays["quality_reward"], atol=1e-10, rtol=0)
            assert np.allclose(penalty, arrays["energy_penalty"], atol=1e-10, rtol=0)
            native_j = .7 * coverage + .3 * quality - penalty
            assert np.allclose(native_j, arrays["total_reward"], atol=1e-10, rtol=0)
            assert np.allclose(
                native_j.mean(axis=0), np.asarray(panel["J"]), atol=1e-7, rtol=1e-6,
            )
            assert np.allclose(
                arrays["scalar_reward"].sum(axis=0) * n / TECH_BASE.horizon,
                np.asarray(panel["J"]), atol=1e-7, rtol=1e-6,
            )
            for component in COMPONENTS:
                assert np.allclose(
                    arrays[component].mean(axis=0),
                    np.asarray(panel["component_means"][component]), atol=1e-10, rtol=0,
                )
            evidence = panel["eligibility_service"]
            assert np.allclose(
                arrays["eligible_user_counts"].mean(axis=0),
                evidence["eligible_users_per_step"], atol=0, rtol=0,
            )
            assert np.allclose(
                arrays["served_user_counts"].mean(axis=0),
                evidence["served_users_per_step"], atol=0, rtol=0,
            )
    for n in (8, 6):
        assert np.array_equal(initial_by_cell["t6"][n][0], initial_by_cell["t8"][n][0])
        assert np.array_equal(initial_by_cell["t6"][n][1], initial_by_cell["t8"][n][1])


def test_partial_training_failure_retains_actual_counts_and_rollout(tmp_path):
    cell = runner.CELL_BY_KEY["t6"]
    spec = runner.spec_for(cell, TECH_BASE)

    def stop(row):
        if row["t"] == 0 and row["lane"] == 0:
            raise RuntimeError("injected transition boundary")

    out = tmp_path / cell.tag
    assert runner.run_fit(
        out, cell, "technical-failure", {"sha": "technical-failure"}, spec,
        training_step_hook=stop,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["counts"]["fits"] == 1
    assert result["counts"]["training_team_steps"] == 1
    assert result["counts"]["training_agent_rows"] == cell.train_n
    assert result["counts"]["stored_team_steps"] == 0
    assert result["counts"]["training_policy_step_calls"] == 1
    assert result["incomplete_rollout"]["phase"] == "collecting_failed"
    assert result["incomplete_rollout"]["action_motion_telemetry_partial"]["team_steps"] == 1
    assert (out / "error.txt").is_file()


def test_cell_spec_and_existing_output_refusals_precede_fit(tmp_path):
    cell = runner.CELL_BY_KEY["t6"]
    with pytest.raises(ValueError, match="matching output tag"):
        runner.run_fit(
            tmp_path / "wrong", cell, "x", {"sha": "x"}, runner.spec_for(cell, TECH_BASE),
        )
    with pytest.raises(ValueError, match="actual train N"):
        runner.run_fit(
            tmp_path / cell.tag, cell, "x", {"sha": "x"},
            replace(runner.spec_for(cell, TECH_BASE), train_n=8),
        )


def test_cli_admission_and_fixed_cell_surface(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "x"})
    cell = runner.CELL_BY_KEY["t8"]
    result = entry.main(
        ["--cell", "t8", "--seed", "963201", "--launch-sha", "x", "--out", str(tmp_path / cell.tag)],
        run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 9,
    )
    assert result == 9 and calls[0] == "admit"
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "t7", "--seed", "963201", "--launch-sha", "x",
            "--out", str(tmp_path / "x"),
        ])

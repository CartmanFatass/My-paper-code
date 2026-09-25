"""Focused native checks for the fixed B12 training-block recurrence runner."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.runner import digest_agent, seed_rng
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11
from experiments.candidates.agent_count_generalization.training_recurrence_b12 import runner
from scripts import run_agent_count_training_recurrence_b12 as entry


TECH_BASE = replace(
    DEFAULT_SPEC, horizon=20, train_lanes=2, eval_lanes=2, rollouts=1,
    panels=(1,), test_ns=(8, 6), hidden_size=16, n_heads=2, n_layers=1,
    ppo_epochs=1, sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_actual_config(cell, root: Path, module=runner):
    spec = module.spec_for(cell, TECH_BASE)
    envs = make_envs(spec.train_lanes, module.TRAINING_ENV_SEED_BASE, cell.train_n, spec.horizon)
    try:
        seed_rng(cell.seed)
        make_config = (
            module.make_b12_config if hasattr(module, "make_b12_config") else module.make_b11_config
        )
        return make_config(cell, envs, spec), spec
    finally:
        for env in envs:
            env.close()


def test_fixed_cells_new_training_addresses_and_production_exposure(tmp_path):
    assert runner.OBJECT_ID == "s1_training_recurrence_b12"
    assert [(cell.key, cell.train_n, cell.seed, cell.tag) for cell in runner.CELLS] == [
        ("t6", 6, 963401, "s1_training_recurrence_b12_t6_s963401"),
        ("t8", 8, 963401, "s1_training_recurrence_b12_t8_s963401"),
    ]
    assert runner.TRAINING_ENV_SEED_BASE == 964401
    assert b11.TRAINING_ENV_SEED_BASE == 964201
    assert b11._panel_world_seed(8) == 1_645_800
    assert b11._panel_world_seed(6) == 1_645_600
    assert runner.spec_for(runner.CELL_BY_KEY["t6"]).train_lanes == 16
    assert runner.spec_for(runner.CELL_BY_KEY["t6"]).horizon == 500
    assert runner.spec_for(runner.CELL_BY_KEY["t6"]).rollouts == 45
    expected = b11._expected_counts(runner.spec_for(runner.CELL_BY_KEY["t8"]))
    assert expected["training_team_steps"] == 360_000
    assert expected["training_agent_rows"] == 2_880_000
    assert expected["evaluation_team_steps"] == 32_000
    assert expected["evaluation_uav_steps"] == 224_000
    assert b11._expected_production_optimizer_calls(runner.CELL_BY_KEY["t6"])[
        "discoverer_actor"
    ] == 101_250
    assert b11._expected_production_optimizer_calls(runner.CELL_BY_KEY["t8"])[
        "discoverer_critic"
    ] == 135_000

    fresh = make_envs(2, runner.TRAINING_ENV_SEED_BASE, 6, 20)
    old = make_envs(2, b11.TRAINING_ENV_SEED_BASE, 6, 20)
    try:
        assert [env.env.env.seed_val for env in fresh] == [964401, 964402]
        assert [env.env.env.seed_val for env in old] == [964201, 964202]
        fresh_initial = [env.reset()[1]["state"] for env in fresh]
        old_initial = [env.reset()[1]["state"] for env in old]
        assert any(not np.array_equal(new, prior) for new, prior in zip(fresh_initial, old_initial))
    finally:
        for env in [*fresh, *old]:
            env.close()


def test_new_seed_is_common_across_arms_and_fresh_from_b11(tmp_path):
    records, agents = {}, []
    for key in ("t6", "t8"):
        cell = runner.CELL_BY_KEY[key]
        config, _spec = _make_actual_config(cell, tmp_path)
        assert int(config.seed) == 963401
        seed_rng(cell.seed)
        agent, record = runner.construct_common_initialized_agent(config, tmp_path / key)
        agents.append(agent)
        records[key] = record
        assert int(agent.config.n_agents) == cell.train_n
        assert int(agent.rollout_buffer.n_agents) == cell.train_n
        assert record["actual_config"]["seed"] == 963401
        assert record["canonical_config"]["seed"] == 963401
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
    assert records["t6"]["target_initial_buffer"]["sampler_state"] == records["t8"][
        "target_initial_buffer"
    ]["sampler_state"]
    assert records["t6"]["target_initial_buffer"]["sampler_seed"] == records["t8"][
        "target_initial_buffer"
    ]["sampler_seed"]
    assert records["t6"]["canonical_post_initialization_rng_digest"] == records["t8"][
        "canonical_post_initialization_rng_digest"
    ]
    assert digest_agent(agents[0]) == digest_agent(agents[1])

    old_cell = b11.CELL_BY_KEY["t6"]
    old_config, _old_spec = _make_actual_config(old_cell, tmp_path, module=b11)
    seed_rng(old_cell.seed)
    old_agent, old_record = b11.construct_common_initialized_agent(old_config, tmp_path / "b11")
    assert old_record["actual_config"]["seed"] == 963201
    assert records["t6"]["parameter_normalizer_digest"] != old_record[
        "parameter_normalizer_digest"
    ]
    assert records["t6"]["tensor_manifest"] != old_record["tensor_manifest"]
    assert records["t6"]["target_initial_buffer"]["sampler_state"] != old_record[
        "target_initial_buffer"
    ]["sampler_state"]
    assert records["t6"]["target_initial_buffer"]["sampler_seed"] != old_record[
        "target_initial_buffer"
    ]["sampler_seed"]
    assert records["t6"]["canonical_post_initialization_rng_digest"] != old_record[
        "canonical_post_initialization_rng_digest"
    ]
    assert digest_agent(agents[0]) != digest_agent(old_agent)


@pytest.fixture(scope="module")
def completed_cells(tmp_path_factory):
    root = tmp_path_factory.mktemp("training-recurrence-b12")
    results = {}
    for cell in runner.CELLS:
        out = root / cell.tag
        spec = runner.spec_for(cell, TECH_BASE)
        assert runner.run_fit(
            out, cell, "technical-b12", {"sha": "technical-b12"}, spec,
        ) == 0, (out / "summary.json").read_text(encoding="utf-8")
        results[cell.key] = (out, _read(out / "summary.json"))
    return results


def test_real_collect_store_update_and_final_evaluation_contract(completed_cells):
    initial = {}
    evaluation_initial = {}
    for key, (out, result) in completed_cells.items():
        cell = runner.CELL_BY_KEY[key]
        spec = runner.spec_for(cell, TECH_BASE)
        assert result["status"] == "complete" and result["fit_started"]
        assert result["object_id"] == runner.OBJECT_ID
        assert result["seed"] == 963401 and result["tag"] == cell.tag
        assert result["launch_sha"] == "technical-b12"
        assert result["training_world_seeds"] == [964401, 964402]
        assert result["config"]["seed"] == 963401
        assert result["common_initialization"]["target_initial_buffer"]["n_agents"] == cell.train_n
        assert result["counts"] == b11._expected_counts(spec)
        assert [row["path"] for row in result["checkpoints"]] == [
            "checkpoint_00.pt", "checkpoint_01.pt",
        ]
        assert [row["test_n"] for row in result["panels"]] == [8, 6]
        assert [row["world_seeds"] for row in result["panels"]] == [
            [1_645_800, 1_645_801], [1_645_600, 1_645_601],
        ]
        assert not (out / "panel_00_n8.json").exists()
        assert len((out / "training.jsonl").read_text(encoding="utf-8").splitlines()) == 1
        rollout = result["rollouts"][0]
        assert rollout["action_motion_telemetry"]["old_logprob_unchanged"]
        assert rollout["action_motion_telemetry"]["policy_output_unchanged"]
        assert rollout["action_motion_telemetry"]["executed_min"] >= -1
        assert rollout["action_motion_telemetry"]["executed_max"] <= 1
        assert result["optimizer_calls"]["discoverer_actor"] == cell.train_n
        assert result["optimizer_calls"]["discoverer_critic"] == cell.train_n
        assert all(result["optimizer_calls"][name] == 0 for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        ))
        assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
        assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0
        assert all(result["final_evaluation_learner_isolation"][name] for name in (
            "model_preserved", "runtime_preserved", "global_rng_preserved",
        ))
        initial[key] = result["common_initialization"]
        evaluation_initial[key] = {}
        for panel in result["panels"]:
            assert panel["frozen_weights_and_normalizers"]
            assert not any(panel["optimizer_calls"].values())
            assert panel["training_storage_calls"] == 0
            assert panel["runtime_evolved"] and panel["post_transition_semantics"]
            assert panel["max_connections_per_uav"] == 10 and panel["n_users"] == 50
            assert Path(panel["trace"]["path"]).is_file()
            with np.load(panel["trace"]["path"], allow_pickle=False) as trace:
                evaluation_initial[key][panel["test_n"]] = (
                    trace["initial_states"].copy(), trace["initial_observations"].copy(),
                )
    assert initial["t6"]["tensor_manifest"] == initial["t8"]["tensor_manifest"]
    assert initial["t6"]["target_initial_buffer"]["sampler_state"] == initial["t8"][
        "target_initial_buffer"
    ]["sampler_state"]
    for n in (8, 6):
        assert np.array_equal(
            evaluation_initial["t6"][n][0], evaluation_initial["t8"][n][0],
        )
        assert np.array_equal(
            evaluation_initial["t6"][n][1], evaluation_initial["t8"][n][1],
        )


def test_output_source_identity_includes_b12_and_reused_b11(completed_cells):
    required = {
        "experiments/candidates/agent_count_generalization/training_recurrence_b12/__init__.py",
        "experiments/candidates/agent_count_generalization/training_recurrence_b12/runner.py",
        "scripts/run_agent_count_training_recurrence_b12.py",
        "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        "scripts/run_agent_count_training_condition_b11.py",
    }
    for _out, result in completed_cells.values():
        assert result["source_hashes_unchanged"]
        assert result["source_hashes_before"] == result["source_hashes_after"]
        assert required <= result["source_hashes_before"].keys()


def test_cell_spec_existing_output_and_cli_admission_refusals(monkeypatch, tmp_path):
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

    calls = []
    monkeypatch.setattr(
        entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "x"},
    )
    t8 = runner.CELL_BY_KEY["t8"]
    result = entry.main(
        ["--cell", "t8", "--seed", "963401", "--launch-sha", "x",
         "--out", str(tmp_path / t8.tag)],
        run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 9,
    )
    assert result == 9 and calls[0] == "admit"
    args, kwargs = calls[1]
    assert args[1] == t8 and args[2] == "x" and args[3] == {"sha": "x"}
    assert kwargs["command_start"] == entry.COMMAND_START

    calls.clear()
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main([
            "--cell", "t6", "--seed", "963401", "--launch-sha", "wrong",
            "--out", str(tmp_path / cell.tag),
        ])
    assert calls == ["admit"]

    calls.clear()
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "t6", "--seed", "963201", "--launch-sha", "x",
            "--out", str(tmp_path / cell.tag),
        ])
    assert calls == []
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "t6", "--seed", "963401", "--launch-sha", "x",
            "--out", str(tmp_path / b11.CELL_BY_KEY["t6"].tag),
        ])
    assert calls == []
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "t7", "--seed", "963401", "--launch-sha", "x",
            "--out", str(tmp_path / "x"),
        ])

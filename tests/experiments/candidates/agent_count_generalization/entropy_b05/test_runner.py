"""Focused checks for the fixed fresh-world B05 SET entropy pair."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import types

import numpy as np
import pytest

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.entropy_b05 import runner
from scripts import run_agent_count_entropy_b05 as entry


TECH_SPEC = replace(
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
    sequence_batch_size=16,
    coordinator_batch_size=2,
    torch_threads=1,
)
TECHNICAL_SHA = "technical-b05-same-source"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(path: Path) -> runner.ControlBinding:
    return runner.ControlBinding(path=path, sha256=_sha256(path))


@pytest.fixture(scope="module")
def completed_pair(tmp_path_factory):
    root = tmp_path_factory.mktemp("entropy-b05-pair")
    captured = {}
    results = {}
    control_path = None
    for cell in runner.CELLS:
        replay_actions = []

        def capture_replay(agent, *, sink=replay_actions):
            original = agent.skill_discoverer.actor.evaluate_actions

            def wrapped(_actor, observations, initial_hxs, actions, masks, skills):
                sink.append(actions.detach().cpu().numpy().copy())
                return original(observations, initial_hxs, actions, masks, skills)

            agent.skill_discoverer.actor.evaluate_actions = types.MethodType(
                wrapped, agent.skill_discoverer.actor
            )

        out = root / cell.tag
        binding = _binding(control_path) if control_path is not None else None
        assert runner.run_fit(
            out, cell, TECHNICAL_SHA, {"sha": TECHNICAL_SHA}, TECH_SPEC,
            control_binding=binding, agent_setup_hook=capture_replay,
        ) == 0, (out / "summary.json").read_text(encoding="utf-8")
        results[cell.key] = _read(out / "summary.json")
        captured[cell.key] = replay_actions
        if cell.key == "set_l05":
            control_path = out / "summary.json"
    return root, results, captured


def test_fixed_cells_and_production_contract_are_exact():
    assert [
        (cell.index, cell.key, cell.arm, cell.law, cell.seed, cell.tag, cell.lambda_l)
        for cell in runner.CELLS
    ] == [
        (1, "set_l05", "SET", "clip", 953201,
         "s1_entropy_b05_set_l05_s953201", .05),
        (2, "set_l0", "SET", "clip", 953201,
         "s1_entropy_b05_set_l0_s953201", 0.0),
    ]
    assert runner.EVALUATION_SEED_BASE == 1_500_000
    assert runner._expected_set_optimizer_calls(DEFAULT_SPEC) == {
        "coordinator": 0,
        "discoverer_actor": 101250,
        "discoverer_critic": 101250,
        "team_discriminator": 0,
        "individual_discriminator": 0,
    }
    assert DEFAULT_SPEC == replace(
        DEFAULT_SPEC,
        train_n=6, test_ns=(4, 6, 8), horizon=500, train_lanes=16,
        eval_lanes=16, rollouts=45, panels=(0, 15, 30, 45), torch_threads=4,
        ppo_epochs=15, sequence_batch_size=32,
    )


def test_tiny_pair_uses_actual_coefficients_and_complete_learner_path(completed_pair):
    _root, results, replay = completed_pair
    for cell in runner.CELLS:
        result = results[cell.key]
        assert result["status"] == "complete" and result["fit_started"]
        assert result["counts"] == runner._expected_counts(TECH_SPEC)
        assert result["training_world_seeds"] == [953201, 953202]
        assert result["evaluation_seed_base"] == 1_500_000
        assert result["config"]["lambda_l"] == cell.lambda_l
        assert result["config"]["lambda_l_initial"] == cell.lambda_l
        assert result["config"]["lambda_l_final"] == cell.lambda_l
        assert not result["config"]["use_entropy_targets"]
        assert not result["config"]["use_entropy_annealing"]
        assert result["effective_entropy_contract"] == {
            "config_lambda_l": cell.lambda_l,
            "effective_lambda_l": cell.lambda_l,
            "lambda_l_initial": cell.lambda_l,
            "lambda_l_final": cell.lambda_l,
            "entropy_targets_enabled": False,
            "entropy_annealing_enabled": False,
        }
        assert result["entropy_measurement"] == {
            "analytic_raw_gaussian": "sum(log_sigma)+1.5*log(2*pi*e)",
            "aligned_exposure": "rollout r uses before-update value; after45 is final policy",
            "analytic_raw_entropy_is_clipped_action_entropy": False,
            "legacy_action_entropy_at_lambda0_is_measurement": False,
        }
        assert result["logstd_optimizer_contract"] == {
            "requires_grad": True, "included_exactly_once": True,
        }
        assert result["initial_raw_sigma"] == [1.0, 1.0, 1.0]
        assert result["initial_raw_log_sigma"] == [0.0, 0.0, 0.0]
        rollout = result["rollouts"][0]
        assert rollout["analytic_raw_entropy_before_update"] > 4.0
        assert rollout["analytic_raw_entropy_after_update"] > 0.0
        assert np.any(np.asarray(rollout["raw_log_sigma_after_update"]) != 0.0)
        assert rollout["optimizer_delta"]["discoverer_actor"] > 0
        assert rollout["optimizer_delta"]["discoverer_critic"] > 0
        assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
        assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0
        assert not any(result["optimizer_calls"][name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        ))
        witness = rollout["action_motion_telemetry"]["first_overrange_witness"]
        assert witness["stored_action_exact"] and witness["stored_old_logprob_exact"]
        assert np.max(np.abs(witness["raw_action"])) > 1.0
        assert np.max(np.abs(witness["executed_action"])) <= 1.0
        assert replay[cell.key]
        assert any(np.max(np.abs(actions)) > 1.0 for actions in replay[cell.key])
        for panel in result["panels"]:
            assert panel["world_seeds"][0] == (
                1_500_000 + 1000 * panel["after_rollout"] + 100 * panel["test_n"]
            )
            assert panel["config"]["lambda_l"] == cell.lambda_l
            assert not any(panel["optimizer_calls"].values())
            assert panel["frozen_weights_and_normalizers"]
            assert panel["executed_action_bounds"]["minimum"] >= -1.0
            assert panel["executed_action_bounds"]["maximum"] <= 1.0
            components = panel["component_means"]
            native_j = (
                .7 * np.asarray(components["coverage_reward"])
                + .3 * np.asarray(components["quality_reward"])
                - np.asarray(components["energy_penalty"])
            )
            assert np.allclose(panel["J"], native_j, atol=1e-7, rtol=1e-6)
        pooled = result["pooled_action_motion_telemetry"]
        assert pooled["full_rollouts_1_through_45"]["rollout_count"] == 1
        assert pooled["late_rollouts_31_through_45"]["rollout_count"] == 0

    assert results["set_l05"]["rollouts"][0]["losses"]["action_entropy"] != 0.0
    assert results["set_l0"]["rollouts"][0]["losses"]["action_entropy"] == 0.0


def test_zero_binds_same_source_initialization_and_pre_update_outputs(completed_pair):
    _root, results, _replay = completed_pair
    control = results["set_l05"]
    zero = results["set_l0"]
    binding = zero["control_binding"]
    assert binding["required"]
    assert binding["summary_bytes_match"] and binding["identity_match"]
    assert binding["spec_match"] and binding["evaluation_seed_base_match"]
    assert binding["training_worlds_match"] and binding["counts_match"]
    assert binding["panel_worlds_match"] and binding["panel_payloads_valid"]
    assert binding["optimizer_contract_match"] and binding["rollout_optimizer_totals_match"]
    assert binding["config_match_apart_from_declared_coefficient_fields"]
    assert binding["initial_digest_match"] and binding["pre_update_match"]
    assert binding["initial_per_world_outputs_match"]
    assert binding["first_pre_update_collection_match"]
    assert zero["launch_sha"] == control["launch_sha"] == TECHNICAL_SHA
    assert zero["observed_initial_parameter_normalizer_digest"] == control[
        "observed_initial_parameter_normalizer_digest"
    ]
    assert zero["control_comparisons"]
    assert zero["final_control_comparison"]["scope"] == (
        "fresh within-SET set_l0 minus set_l05; no H6 or Q comparison"
    )
    assert control["control_comparisons"] == []
    assert control["final_control_comparison"] is None


def test_primary_eu_and_world_signs_are_independently_recomputed(completed_pair):
    _root, results, _replay = completed_pair
    control = results["set_l05"]
    zero = results["set_l0"]
    final = zero["final_control_comparison"]
    comparison_rows = {
        row["test_n"]: row for row in zero["control_comparisons"]
        if row["after_rollout"] == 1
    }
    zero_panels = {
        row["test_n"]: row for row in zero["panels"] if row["after_rollout"] == 1
    }
    control_panels = {
        row["test_n"]: row for row in control["panels"] if row["after_rollout"] == 1
    }
    assert set(comparison_rows) == set(zero_panels) == set(control_panels) == {4, 6, 8}
    independent = {}
    for n, row in comparison_rows.items():
        zero_panel, control_panel = zero_panels[n], control_panels[n]
        assert zero_panel["world_seeds"] == control_panel["world_seeds"] == row["world_seeds"]
        zero_j = np.asarray(zero_panel["J"])
        control_j = np.asarray(control_panel["J"])
        differences = zero_j - control_j
        independent[n] = float(differences.mean())
        assert row["set_l0_J_per_world"] == zero_j.tolist()
        assert row["set_l05_control_J_per_world"] == control_j.tolist()
        assert row["E_J_set_l0_minus_set_l05_per_world"] == differences.tolist()
        assert row["E_J_set_l0_minus_set_l05_mean"] == pytest.approx(differences.mean())
        assert row["positive_world_count"] == int(np.count_nonzero(differences > 0))
        assert row["zero_world_count"] == int(np.count_nonzero(differences == 0))
        assert row["negative_world_count"] == int(np.count_nonzero(differences < 0))
        for component in ("coverage_reward", "quality_reward", "energy_penalty", "total_reward"):
            zero_values = np.asarray(zero_panel["component_means"][component])
            control_values = np.asarray(control_panel["component_means"][component])
            component_row = row["component_comparisons"][component]
            assert component_row["set_l0_per_world"] == zero_values.tolist()
            assert component_row["set_l05_control_per_world"] == control_values.tolist()
            assert component_row["set_l0_minus_set_l05_per_world"] == (
                zero_values - control_values
            ).tolist()
            assert component_row["set_l0_minus_set_l05_mean"] == pytest.approx(
                (zero_values - control_values).mean()
            )
    assert final["E_U_equal_weight_N4_N8"] == pytest.approx(
        (independent[4] + independent[8]) / 2
    )
    n6 = final["by_test_n"]["6"]
    assert final["n6_no_observed_J_or_coverage_cost"] == (
        n6["E_J_set_l0_minus_set_l05_mean"] >= 0
        and n6["delta_coverage_set_l0_minus_set_l05_mean"] >= 0
    )


def _mutated_binding(tmp_path: Path, source: Path, name: str, mutate) -> runner.ControlBinding:
    payload = _read(source)
    mutate(payload)
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return _binding(path)


@pytest.mark.parametrize(
    ("name", "mutate", "failure"),
    [
        ("incomplete", lambda value: value.__setitem__("status", "training"),
         "status/source/object/cell identity"),
        ("foreign_source", lambda value: value.__setitem__("launch_sha", "old-source"),
         "status/source/object/cell identity"),
        ("old_object", lambda value: value.__setitem__("object_id", "s1_entropy_b04"),
         "status/source/object/cell identity"),
        ("seed", lambda value: value.__setitem__("seed", 943201),
         "status/source/object/cell identity"),
        ("world", lambda value: value["panels"][0]["world_seeds"].__setitem__(0, 1_200_400),
         "panels/rollouts/checkpoints/optimizer contract"),
        ("count", lambda value: value["counts"].__setitem__("updates", 0),
         "spec/world/count contract"),
        ("missing_final_payload", lambda value: value["panels"][-1].pop("J"),
         "panels/rollouts/checkpoints/optimizer contract"),
        ("optimizer_count", lambda value: value["optimizer_calls"].__setitem__(
            "discoverer_actor", value["optimizer_calls"]["discoverer_actor"] + 1
         ), "panels/rollouts/checkpoints/optimizer contract"),
        ("coefficient", lambda value: value["config"].__setitem__("lambda_l", 0.0),
         "panels/rollouts/checkpoints/optimizer contract"),
        ("config", lambda value: value["config"].__setitem__("gamma", .5),
         "panels/rollouts/checkpoints/optimizer contract"),
    ],
)
def test_mutated_foreign_or_incomplete_control_refuses_before_fit(
    tmp_path, completed_pair, name, mutate, failure,
):
    root, _results, _replay = completed_pair
    source = root / runner.CELLS[0].tag / "summary.json"
    binding = _mutated_binding(tmp_path, source, name, mutate)
    cell = runner.CELL_BY_KEY["set_l0"]
    out = tmp_path / name / cell.tag
    assert runner.run_fit(
        out, cell, TECHNICAL_SHA, {"sha": TECHNICAL_SHA}, TECH_SPEC,
        control_binding=binding,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and not result["fit_started"]
    assert failure in result["failure"]
    assert not any(result["counts"].values())


def test_hash_and_pre_update_collection_mismatch_keep_honest_counts(
    tmp_path, completed_pair,
):
    root, _results, _replay = completed_pair
    source = root / runner.CELLS[0].tag / "summary.json"
    cell = runner.CELL_BY_KEY["set_l0"]
    bad_hash = runner.ControlBinding(source, "0" * 64)
    hash_out = tmp_path / "hash" / cell.tag
    assert runner.run_fit(
        hash_out, cell, TECHNICAL_SHA, {"sha": TECHNICAL_SHA}, TECH_SPEC,
        control_binding=bad_hash,
    ) == 1
    hashed = _read(hash_out / "summary.json")
    assert not hashed["fit_started"] and not any(hashed["counts"].values())
    assert not hashed["control_binding"]["summary_bytes_match"]

    def change_collection(value):
        value["rollouts"][0]["training_scalar_returns"][0] += 1.0

    changed = _mutated_binding(tmp_path, source, "pre-update", change_collection)
    out = tmp_path / "pre-update" / cell.tag
    assert runner.run_fit(
        out, cell, TECHNICAL_SHA, {"sha": TECHNICAL_SHA}, TECH_SPEC,
        control_binding=changed,
    ) == 1
    result = _read(out / "summary.json")
    assert result["fit_started"] and result["counts"]["training_team_steps"] == 24
    assert result["counts"]["stored_team_steps"] == 24
    assert result["counts"]["updates"] == 0
    assert result["control_binding"]["initial_per_world_outputs_match"]
    assert not result["control_binding"]["first_pre_update_collection_match"]
    assert result["incomplete_rollout"]["phase"] == "updating_failed"


def test_cli_admission_precedes_candidate_import_and_fixes_pair_arguments(
    tmp_path, monkeypatch,
):
    calls = []

    def refuse(*_args, **_kwargs):
        calls.append("admission")
        raise RuntimeError("not admitted")

    monkeypatch.setattr(entry, "require_admission", refuse)
    l05 = runner.CELL_BY_KEY["set_l05"]
    with pytest.raises(RuntimeError, match="not admitted"):
        entry.main([
            "--cell", l05.key, "--seed", "953201", "--launch-sha", "technical", "--out",
            str(tmp_path / l05.tag),
        ], run_fn=lambda *_args, **_kwargs: calls.append("run"))
    assert calls == ["admission"]
    assert not (tmp_path / l05.tag).exists()

    l0 = runner.CELL_BY_KEY["set_l0"]
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", l0.key, "--seed", "953201", "--launch-sha", "technical", "--out",
            str(tmp_path / l0.tag),
        ])
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", l05.key, "--seed", "953201", "--launch-sha", "technical", "--out",
            str(tmp_path / l05.tag), "--control-summary", str(tmp_path / "x"),
            "--control-sha256", "0" * 64,
        ])
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", l0.key, "--seed", "953201", "--launch-sha", "technical", "--out",
            str(tmp_path / l0.tag), "--control-summary", str(tmp_path / "x"),
            "--control-sha256", "BAD",
        ])
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", l05.key, "--seed", "953201", "--launch-sha", "technical", "--out",
            str(tmp_path / l05.tag), "--lambda-l", "0.1",
        ])
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", l05.key, "--seed", "953202", "--launch-sha", "technical", "--out",
            str(tmp_path / l05.tag),
        ])


def test_frozen_b03_b04_sources_remain_byte_exact():
    root = Path(__file__).resolve().parents[5]
    expected = {
        "experiments/candidates/agent_count_generalization/action_law_b03/runner.py":
            "d9ed78a5dd6faeb1017747d46a428dc61d40929133dd17478348841bb1a03ddb",
        "scripts/run_agent_count_action_law_training_b03.py":
            "0c84bc8fc300cad2707ddad85514d8f4cd8b23100e4a31510ff6bb053d18a849",
        "experiments/candidates/agent_count_generalization/entropy_b04/runner.py":
            "4af9b4f1a0ae8e432414f206c9dbdb2effcc00c567c1201766114875d23a8c1a",
        "scripts/run_agent_count_entropy_b04.py":
            "5dcd60012988149e4926ee7a0339653b0a90567b30229bedbb5171ca97e6b54f",
    }
    for relative, digest in expected.items():
        assert _sha256(root / relative) == digest

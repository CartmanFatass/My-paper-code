"""Focused checks for the fixed B04 entropy-coefficient discriminator."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import types

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.entropy_b04 import runner
from scripts import run_agent_count_entropy_b04 as entry


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


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(path: Path) -> runner.ControlBinding:
    summary = _read(path)
    return runner.ControlBinding(
        path=path,
        sha256=_sha256(path),
        tag=summary["tag"],
        cell_key=summary["cell"]["key"],
        expected_initial_digest=summary[
            "observed_initial_parameter_normalizer_digest"
        ],
    )


@pytest.fixture(scope="module")
def tiny_controls(tmp_path_factory):
    root = tmp_path_factory.mktemp("entropy-b04-controls")
    h6_raw = b03.CELL_BY_KEY["h6_raw"]
    raw_out = root / h6_raw.tag
    assert b03.run_fit(
        raw_out, h6_raw, runner.CONTROL_SOURCE_SHA,
        {"sha": runner.CONTROL_SOURCE_SHA},
        None, TECH_SPEC,
    ) == 0
    h6_digest = _read(raw_out / "summary.json")[
        "observed_initial_parameter_normalizer_digest"
    ]

    controls = {}
    for key, expected in (("h6_clip", h6_digest), ("set_clip", None)):
        cell = b03.CELL_BY_KEY[key]
        out = root / cell.tag
        assert b03.run_fit(
            out, cell, runner.CONTROL_SOURCE_SHA, {"sha": runner.CONTROL_SOURCE_SHA},
            expected, TECH_SPEC,
        ) == 0
        controls[cell.arm] = _binding(out / "summary.json")
    return controls


@pytest.fixture(scope="module")
def completed_b04(tmp_path_factory, tiny_controls):
    root = tmp_path_factory.mktemp("entropy-b04-complete")
    results = {}
    replay_actions = {}
    for cell in runner.CELLS:
        captured = []

        def capture_replay(agent, *, sink=captured):
            original = agent.skill_discoverer.actor.evaluate_actions

            def wrapped(_actor, observations, initial_hxs, actions, masks, skills):
                sink.append(actions.detach().cpu().numpy().copy())
                return original(observations, initial_hxs, actions, masks, skills)

            agent.skill_discoverer.actor.evaluate_actions = types.MethodType(
                wrapped, agent.skill_discoverer.actor
            )

        out = root / cell.tag
        assert runner.run_fit(
            out, cell, "technical-b04", {"sha": "technical-b04"}, TECH_SPEC,
            control_binding=tiny_controls[cell.arm],
            agent_setup_hook=capture_replay,
        ) == 0, (out / "summary.json").read_text(encoding="utf-8")
        results[cell.key] = _read(out / "summary.json")
        replay_actions[cell.key] = captured
    return results, replay_actions


def test_fixed_cells_and_production_defaults_are_exact():
    assert [
        (cell.index, cell.key, cell.arm, cell.law, cell.seed, cell.tag,
         cell.control_tag, cell.control_cell_key, cell.control_summary_sha256,
         cell.expected_initial_digest)
        for cell in runner.CELLS
    ] == [
        (
            1, "h6_zero", "H6", "clip", 942201,
            "s1_entropy_b04_h6_zero_s942201",
            "s1_action_law_b03_h6_clip_s942201", "h6_clip",
            "55a994c81f49a9b97b52efa4ddaea82579e1068ea3a7ddbd11c8b7645bf88921",
            "50f3d5305a2d6a94a1543d7b5111654c7b154f4a9c1b71b59474c4deb36038ac",
        ),
        (
            2, "set_zero", "SET", "clip", 943201,
            "s1_entropy_b04_set_zero_s943201",
            "s1_action_law_b03_set_clip_s943201", "set_clip",
            "2621fc884d2d6a9ea909ee4f483b4df1c2d9d6f8767826ef730b952a360422e3",
            "8f19743fe8fd5a09aa998bf90ab73bdbc3de599a8f58b791610fbb628d2f97c2",
        ),
    ]
    assert DEFAULT_SPEC == replace(
        DEFAULT_SPEC,
        train_n=6,
        test_ns=(4, 6, 8),
        horizon=500,
        train_lanes=16,
        eval_lanes=16,
        rollouts=45,
        panels=(0, 15, 30, 45),
        torch_threads=4,
    )


def test_production_controls_are_exact_complete_artifacts_without_rng_use():
    before = runner._rng_digest()
    for cell in runner.CELLS:
        binding = runner.production_control_binding(cell)
        record = {}
        control = runner._read_control(binding, cell, record)
        assert control["status"] == "complete"
        assert record["summary_bytes_match"]
        assert record["identity_match"]
        assert record["control_initial_digest_match"]
    assert runner._rng_digest() == before


def test_native_tiny_h6_and_set_preserve_storage_update_and_eval(completed_b04):
    results, replay_actions = completed_b04
    for key, result in results.items():
        assert result["status"] == "complete" and result["fit_started"]
        assert result["counts"] == {
            "training_team_steps": 24,
            "stored_team_steps": 24,
            "training_episodes": 2,
            "terminal_resets": 2,
            "updates": 1,
            "evaluation_team_steps": 144,
            "evaluation_episodes": 12,
        }
        assert result["config"]["lambda_l"] == 0.0
        assert result["config"]["lambda_l_initial"] == 0.0
        assert result["config"]["lambda_l_final"] == 0.0
        assert not result["config"]["use_entropy_targets"]
        assert not result["config"]["use_entropy_annealing"]
        assert result["effective_entropy_contract"] == {
            "config_lambda_l": 0.0,
            "effective_lambda_l": 0.0,
            "entropy_targets_enabled": False,
            "entropy_annealing_enabled": False,
        }
        assert result["logstd_optimizer_contract"] == {
            "requires_grad": True, "included_exactly_once": True,
        }
        assert result["initial_raw_sigma"] == [1.0, 1.0, 1.0]
        assert result["initial_raw_log_sigma"] == [0.0, 0.0, 0.0]
        assert result["initial_analytic_raw_entropy"] > 4.0
        rollout = result["rollouts"][0]
        assert rollout["losses"]["action_entropy"] == 0.0
        assert rollout["analytic_raw_entropy_before_update"] > 4.0
        assert rollout["analytic_raw_entropy_after_update"] > 0.0
        assert np.any(np.asarray(rollout["raw_log_sigma_after_update"]) != 0.0)
        assert rollout["optimizer_delta"]["discoverer_actor"] > 0
        assert rollout["optimizer_delta"]["discoverer_critic"] > 0
        assert result["parameter_motion"]["discoverer_actor"]["delta_l2"] > 0
        assert result["parameter_motion"]["discoverer_critic"]["delta_l2"] > 0

        binding = result["control_binding"]
        assert binding["pre_update_match"]
        assert binding["initial_per_world_outputs_match"]
        assert binding["first_pre_update_collection_match"]
        assert binding["config_differences_excluding_treatment"] == {}
        assert len(result["control_comparisons"]) == 6
        assert result["final_control_comparison"]["after_rollout"] == 1
        assert result["final_control_comparison"]["unseen_n4_n8_equal_weight_E_J"] is not None
        motion = rollout["action_motion_telemetry"]
        witness = motion["first_overrange_witness"]
        assert witness["stored_action_exact"] and witness["stored_old_logprob_exact"]
        assert np.max(np.abs(witness["raw_action"])) > 1.0
        assert np.max(np.abs(witness["executed_action"])) <= 1.0
        assert replay_actions[key]
        assert any(np.max(np.abs(actions)) > 1.0 for actions in replay_actions[key])
        for panel in result["panels"]:
            assert panel["status"] == "complete"
            assert panel["config"]["lambda_l"] == 0.0
            assert not panel["config"]["use_entropy_targets"]
            assert not panel["config"]["use_entropy_annealing"]
            assert not any(panel["optimizer_calls"].values())
            assert panel["executed_action_bounds"]["minimum"] >= -1.0
            assert panel["executed_action_bounds"]["maximum"] <= 1.0

    h6 = results["h6_zero"]
    assert all(h6["optimizer_calls"][name] > 0 for name in (
        "coordinator", "team_discriminator", "individual_discriminator",
    ))
    set_result = results["set_zero"]
    assert not any(set_result["optimizer_calls"][name] for name in (
        "coordinator", "team_discriminator", "individual_discriminator",
    ))


def test_control_mismatch_refuses_before_first_update(tmp_path, tiny_controls):
    cell = runner.CELL_BY_KEY["set_zero"]
    control = _read(tiny_controls[cell.arm].path)
    control["rollouts"][0]["training_scalar_returns"][0] += 1.0
    changed = tmp_path / "changed-control.json"
    changed.write_text(json.dumps(control, indent=2) + "\n", encoding="utf-8")
    binding = runner.ControlBinding(
        path=changed,
        sha256=_sha256(changed),
        tag=control["tag"],
        cell_key=control["cell"]["key"],
        expected_initial_digest=control[
            "observed_initial_parameter_normalizer_digest"
        ],
    )
    out = tmp_path / cell.tag
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, TECH_SPEC,
        control_binding=binding,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["fit_started"]
    assert result["counts"]["training_team_steps"] == 24
    assert result["counts"]["stored_team_steps"] == 24
    assert result["counts"]["updates"] == 0
    assert result["control_binding"]["initial_per_world_outputs_match"]
    assert not result["control_binding"]["first_pre_update_collection_match"]
    assert result["incomplete_rollout"]["phase"] == "updating_failed"


def test_hash_mismatch_and_partial_failure_keep_exact_accounting(tmp_path, tiny_controls):
    cell = runner.CELL_BY_KEY["h6_zero"]
    valid = tiny_controls[cell.arm]
    bad = replace(valid, sha256="0" * 64)
    out = tmp_path / "hash" / cell.tag
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, TECH_SPEC,
        control_binding=bad,
    ) == 1
    result = _read(out / "summary.json")
    assert result["counts"] == {
        "training_team_steps": 0, "stored_team_steps": 0,
        "training_episodes": 0, "terminal_resets": 0, "updates": 0,
        "evaluation_team_steps": 0, "evaluation_episodes": 0,
    }
    assert not result["control_binding"]["summary_bytes_match"]

    def fail_at_three(event):
        if event["summary"]["counts"]["training_team_steps"] == 3:
            raise RuntimeError("injected step-three failure")

    partial_out = tmp_path / "partial" / cell.tag
    assert runner.run_fit(
        partial_out, cell, "technical", {"sha": "technical"}, TECH_SPEC,
        control_binding=valid, training_step_hook=fail_at_three,
    ) == 1
    partial = _read(partial_out / "summary.json")
    assert partial["counts"]["training_team_steps"] == 3
    assert partial["counts"]["stored_team_steps"] == 2
    assert partial["counts"]["updates"] == 0
    evidence = partial["incomplete_rollout"]
    assert evidence["phase"] == "collecting_failed"
    assert evidence["action_motion_telemetry_partial"]["team_steps"] == 3
    assert evidence["entropy_observed_after_failure"]["valid"]
    assert evidence["entropy_observed_after_failure"]["analytic_raw_entropy"] > 4.0


def test_rollout_two_collection_failure_reports_zero_optimizer_delta(tmp_path):
    spec = replace(TECH_SPEC, rollouts=2, panels=(0,))
    control_cell = b03.CELL_BY_KEY["set_clip"]
    control_out = tmp_path / "control" / control_cell.tag
    assert b03.run_fit(
        control_out, control_cell, runner.CONTROL_SOURCE_SHA,
        {"sha": runner.CONTROL_SOURCE_SHA}, None, spec,
    ) == 0
    binding = _binding(control_out / "summary.json")
    cell = runner.CELL_BY_KEY["set_zero"]

    def fail_in_second_collection(event):
        if event["summary"]["counts"]["training_team_steps"] == 27:
            raise RuntimeError("injected rollout-two collection failure")

    out = tmp_path / "candidate" / cell.tag
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, spec,
        control_binding=binding, training_step_hook=fail_in_second_collection,
    ) == 1
    result = _read(out / "summary.json")
    assert result["counts"]["updates"] == 1
    assert result["counts"]["training_team_steps"] == 27
    evidence = result["incomplete_rollout"]
    assert evidence["rollout"] == 2 and evidence["phase"] == "collecting_failed"
    assert evidence["optimizer_calls_observed"]["discoverer_actor"] > 0
    assert evidence["optimizer_delta_observed"]["discoverer_actor"] == 0
    assert evidence["optimizer_delta_observed"]["discoverer_critic"] == 0


def test_nonfinite_post_step_failure_publishes_json_safe_partial(tmp_path, tiny_controls):
    cell = runner.CELL_BY_KEY["set_zero"]

    def corrupt_after_real_actor_step(agent):
        optimizer = agent.discoverer_actor_optimizer
        original_step = optimizer.step

        def failing_step(*args, **kwargs):
            result = original_step(*args, **kwargs)
            with torch.no_grad():
                agent.skill_discoverer.actor.act.action_out.logstd._bias[0] = float("nan")
            raise RuntimeError("injected nonfinite post-step failure")

        optimizer.step = failing_step

    out = tmp_path / cell.tag
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, TECH_SPEC,
        control_binding=tiny_controls[cell.arm], agent_setup_hook=corrupt_after_real_actor_step,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["last_boundary"] == "failed"
    evidence = result["incomplete_rollout"]
    assert evidence["optimizer_calls_observed"]["discoverer_actor"] > 0
    snapshot = evidence["entropy_observed_after_failure"]
    assert not snapshot["valid"]
    assert snapshot["raw_log_sigma"][0] is None
    assert snapshot["raw_sigma"][0] is None
    assert snapshot["analytic_raw_entropy"] is None
    assert snapshot["missing_reason"] == "nonfinite_or_wrong_width_logstd_after_failure"


def test_cli_admission_precedes_candidate_import_and_exposes_no_tuning(tmp_path, monkeypatch):
    calls = []

    def refuse(*_args, **_kwargs):
        calls.append("admission")
        raise RuntimeError("not admitted")

    monkeypatch.setattr(entry, "require_admission", refuse)
    cell = runner.CELL_BY_KEY["h6_zero"]
    out = tmp_path / cell.tag
    with pytest.raises(RuntimeError, match="not admitted"):
        entry.main([
            "--cell", cell.key, "--launch-sha", "technical", "--out", str(out),
        ], run_fn=lambda *_args, **_kwargs: calls.append("run"))
    assert calls == ["admission"]
    assert not out.exists()
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", cell.key, "--launch-sha", "technical", "--out", str(out),
            "--lambda-l", "0.1",
        ])


def test_frozen_b03_sources_remain_byte_exact():
    root = Path(__file__).resolve().parents[5]
    assert _sha256(
        root / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py"
    ) == "d9ed78a5dd6faeb1017747d46a428dc61d40929133dd17478348841bb1a03ddb"
    assert _sha256(
        root / "scripts/run_agent_count_action_law_training_b03.py"
    ) == "0c84bc8fc300cad2707ddad85514d8f4cd8b23100e4a31510ff6bb053d18a849"

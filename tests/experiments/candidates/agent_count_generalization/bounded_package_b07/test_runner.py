"""Focused checks for the fixed B07 fresh H6 bounded-package fit."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC, config_dict, make_config
from experiments.candidates.agent_count_generalization.entropy_b05 import runner as b05
from experiments.candidates.agent_count_generalization.bounded_package_b07 import runner
from scripts import run_agent_count_bounded_package_b07 as entry


TECH_SPEC = replace(
    DEFAULT_SPEC,
    horizon=10,
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


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _set_config(n: int, spec=TECH_SPEC) -> dict:
    world = runner._panel_world_seed(0, n)
    envs = make_envs(spec.eval_lanes if n != spec.train_n else spec.train_lanes,
                     world, n, spec.horizon)
    try:
        config = make_config("SET", envs, 953201, spec)
        config.lambda_l = config.lambda_l_initial = config.lambda_l_final = .05
        config.use_entropy_annealing = False
        config.use_entropy_targets = False
        config.validate_config()
        return {
            **config_dict(config),
            "lambda_l_initial": .05,
            "lambda_l_final": .05,
            "use_entropy_annealing": False,
            "use_entropy_targets": False,
        }
    finally:
        for env in envs:
            env.close()


def _make_control(root: Path, spec=TECH_SPEC):
    tag = "technical_b07_set_control"
    source_sha = "technical-b05-source"
    checkpoint = root / f"checkpoint_{spec.rollouts:02d}.pt"
    checkpoint.write_bytes(b"immutable technical SET checkpoint identity")
    checkpoint_sha = _sha(checkpoint)
    training_config = _set_config(6, spec)
    panels = []
    for rollout in spec.panels:
        for n in spec.test_ns:
            worlds = list(range(
                runner._panel_world_seed(rollout, n),
                runner._panel_world_seed(rollout, n) + spec.eval_lanes,
            ))
            coverage = np.asarray([.30 + .01 * rollout + .005 * n + .001 * i
                                   for i in range(spec.eval_lanes)])
            quality = np.asarray([.10 + .002 * i for i in range(spec.eval_lanes)])
            penalty = np.asarray([.05 + .001 * i for i in range(spec.eval_lanes)])
            total = .7 * coverage + .3 * quality - penalty
            returns = total * spec.horizon / n
            panels.append({
                "after_rollout": rollout,
                "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                "test_n": n,
                "world_seeds": worlds,
                "execution_law": "clip",
                "status": "complete",
                "steps": spec.eval_lanes * spec.horizon,
                "episodes": spec.eval_lanes,
                "J": total.tolist(),
                "scalar_returns": returns.tolist(),
                "component_means": {
                    "coverage_reward": coverage.tolist(),
                    "quality_reward": quality.tolist(),
                    "energy_penalty": penalty.tolist(),
                    "total_reward": total.tolist(),
                },
                "optimizer_calls": b05._expected_set_optimizer_calls(spec, rollouts=0),
                "frozen_weights_and_normalizers": True,
                "executed_action_bounds": {"minimum": -.75, "maximum": .8},
                "config": _set_config(n, spec),
            })
    summary = {
        "schema": 1,
        "object_id": "technical-b05-object",
        "direction": "agent_count_generalization",
        "cell": {"key": "set_l05", "tag": tag, "seed": 953201, "arm": "SET",
                 "law": "clip", "lambda_l": .05},
        "arm": "SET",
        "training_action_law": "clip",
        "seed": 953201,
        "tag": tag,
        "launch_sha": source_sha,
        "status": "complete",
        "fit_started": True,
        "spec": runner.jsonable(vars(spec)),
        "config": training_config,
        "counts": b05._expected_counts(spec),
        "training_world_seeds": list(range(953201, 953201 + spec.train_lanes)),
        "evaluation_seed_base": runner.EVALUATION_SEED_BASE,
        "panels": panels,
        "checkpoints": [{"path": checkpoint.name, "sha256": checkpoint_sha,
                         "bytes": checkpoint.stat().st_size}],
    }
    summary_path = root / "summaries" / tag / "summary.json"
    _write(summary_path, summary)
    control = runner.ControlSpec(
        tag=tag,
        object_id=summary["object_id"],
        source_sha=source_sha,
        seed=953201,
        summary_sha256=_sha(summary_path),
        checkpoint_name=checkpoint.name,
        checkpoint_sha256=checkpoint_sha,
        checkpoint_bytes=checkpoint.stat().st_size,
    )
    return control, checkpoint, summary_path


@pytest.fixture(scope="module")
def technical_control(tmp_path_factory):
    root = tmp_path_factory.mktemp("bounded-package-b07-control")
    control, checkpoint, summary = _make_control(root)
    return root, control, checkpoint, summary


@pytest.fixture(scope="module")
def completed_fit(tmp_path_factory, technical_control):
    root, control, checkpoint, _summary = technical_control
    out = tmp_path_factory.mktemp("bounded-package-b07-fit") / runner.TAG

    def force_overrange(agent):
        with torch.no_grad():
            agent.skill_discoverer.actor.act.action_out.logstd._bias.fill_(2.0)

    assert runner.run_fit(
        out, "technical-b07", {"sha": "technical-b07"}, checkpoint, TECH_SPEC,
        control=control, summary_root=root / "summaries", committed_control_summary=False,
        agent_setup_hook=force_overrange,
    ) == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json")


def test_fixed_cell_control_worlds_and_production_counts_are_exact():
    assert vars(runner.CELL) == {
        "key": "h6_l05", "arm": "H6", "law": "clip", "seed": 952201,
        "tag": runner.TAG, "lambda_l": .05,
    }
    assert runner._panel_world_seed(45, 8) == 1_545_800
    assert runner._expected_counts(DEFAULT_SPEC) == {
        "training_team_steps": 360000,
        "stored_team_steps": 360000,
        "training_uav_steps": 2160000,
        "training_episodes": 720,
        "terminal_resets": 720,
        "updates": 45,
        "training_policy_step_calls": 22500,
        "evaluation_team_steps": 96000,
        "evaluation_episodes": 192,
        "evaluation_uav_steps": 576000,
        "evaluation_policy_step_calls": 6000,
    }
    assert runner._expected_h6_optimizer_calls() == {
        "coordinator": 675, "discoverer_actor": 101250, "discoverer_critic": 101250,
        "team_discriminator": 675, "individual_discriminator": 2700,
    }


def test_native_fit_is_fresh_h6_constant_entropy_and_uses_all_learning_paths(completed_fit):
    _out, result = completed_fit
    assert result["status"] == "complete" and result["fit_started"]
    assert not result["pretrained_checkpoint_loaded"]
    assert result["expected_old_initial_digest"] is None
    assert len(result["observed_initial_parameter_normalizer_digest"]) == 64
    assert result["effective_entropy_contract"] == {
        "lambda_l": .05, "lambda_l_initial": .05, "lambda_l_final": .05,
        "entropy_annealing_enabled": False, "entropy_targets_enabled": False,
    }
    assert result["counts"] == runner._expected_counts(TECH_SPEC)
    assert len(result["rollouts"]) == 1
    rollout = result["rollouts"][0]
    witness = rollout["action_motion_telemetry"]["first_overrange_witness"]
    assert witness is not None and witness["stored_action_exact"] and witness["stored_old_logprob_exact"]
    assert np.max(np.abs(witness["raw_action"])) > 1.0
    assert np.max(np.abs(witness["executed_action"])) <= 1.0
    for name in ("coordinator", "discoverer_actor", "discoverer_critic",
                 "team_discriminator", "individual_discriminator"):
        assert result["optimizer_calls"][name] > 0
        assert result["parameter_motion"][name]["delta_l2"] > 0
    assert result["initial_raw_sigma"] != result["final_raw_sigma"]
    assert [row["path"] for row in result["checkpoints"]] == ["checkpoint_00.pt", "checkpoint_01.pt"]


def test_cross_n_evaluation_is_frozen_reset_and_rng_isolated(completed_fit):
    out, result = completed_fit
    assert len(result["panels"]) == len(TECH_SPEC.panels) * len(TECH_SPEC.test_ns)
    assert len(result["control_comparisons"]) == len(result["panels"])
    for row in result["panels"]:
        assert row["status"] == "complete"
        assert row["world_seeds"][0] == runner._panel_world_seed(row["after_rollout"], row["test_n"])
        assert row["steps"] == TECH_SPEC.eval_lanes * TECH_SPEC.horizon
        assert row["episodes"] == TECH_SPEC.eval_lanes
        assert row["policy_step_calls"] == TECH_SPEC.horizon
        assert row["strict_sync_digest_match"] and row["frozen_weights_and_normalizers"]
        assert row["target_parameter_normalizer_digest_before"] == row[
            "target_parameter_normalizer_digest_after"
        ]
        assert row["diagnostics_rng_unchanged"] and not any(row["optimizer_calls"].values())
        isolation = row["learner_isolation"]
        assert isolation["parameters_and_normalizers_preserved"]
        assert isolation["runtime_preserved"] and isolation["global_rng_preserved"]
        assert isolation["parameter_normalizer_digest_before"] == isolation[
            "parameter_normalizer_digest_after"
        ]
        assert isolation["runtime_digest_before"] == isolation["runtime_digest_after"]
        assert isolation["global_rng_digest_before"] == isolation["global_rng_digest_after"]
        assert row["executed_action_bounds"]["minimum"] >= -1.0
        assert row["executed_action_bounds"]["maximum"] <= 1.0
        assert (out / f"panel_{row['after_rollout']:02d}_n{row['test_n']}.json").is_file()
    assert result["source_hashes_unchanged"] and result["control_inputs_unchanged"]
    assert result["control_identity_before"]["checkpoint_loaded"] is False


def test_native_units_and_control_differences_are_independently_recomputed(completed_fit):
    _out, result = completed_fit
    panel_by_key = {(p["after_rollout"], p["test_n"]): p for p in result["panels"]}
    for comparison in result["control_comparisons"]:
        key = (comparison["after_rollout"], comparison["test_n"])
        panel = panel_by_key[key]
        components = panel["component_means"]
        native_j = (
            .7 * np.asarray(components["coverage_reward"])
            + .3 * np.asarray(components["quality_reward"])
            - np.asarray(components["energy_penalty"])
        )
        assert np.allclose(panel["J"], native_j)
        raw_delta = np.asarray(comparison["h6_J_per_world"]) - np.asarray(
            comparison["set_l05_J_per_world"]
        )
        assert comparison["h6_minus_set_J_per_world"] == pytest.approx(raw_delta.tolist())
        assert comparison["h6_minus_set_J_mean"] == pytest.approx(raw_delta.mean())
        coverage = comparison["component_comparisons"]["coverage_reward"]
        independent_coverage = np.asarray(coverage["h6_per_world"]) - np.asarray(
            coverage["set_l05_per_world"]
        )
        assert coverage["served_users_per_step_difference"] == pytest.approx(
            50 * independent_coverage.mean()
        )
    final = result["final_control_comparison"]
    raw = {n: next(row["h6_minus_set_J_mean"] for row in result["control_comparisons"]
                   if row["after_rollout"] == 1 and row["test_n"] == n) for n in (4, 6, 8)}
    assert final["D_U_equal_weight_N4_N8"] == pytest.approx((raw[4] + raw[8]) / 2)


@pytest.mark.parametrize("mutation", ["identity", "spec", "worlds", "checkpoint_hash"])
def test_wrong_control_is_rejected_before_fresh_agent_construction(
    technical_control, tmp_path, mutation,
):
    root, control, checkpoint, source_summary = technical_control
    summary = _read(source_summary)
    candidate_checkpoint = checkpoint
    if mutation == "identity":
        summary["seed"] += 1
    elif mutation == "spec":
        summary["spec"]["hidden_size"] += 1
    elif mutation == "worlds":
        summary["panels"][0]["world_seeds"][0] += 1
    else:
        candidate_checkpoint = tmp_path / "wrong.pt"
        candidate_checkpoint.write_bytes(checkpoint.read_bytes() + b"changed")
    summary_path = tmp_path / control.tag / "summary.json"
    _write(summary_path, summary)
    candidate_control = replace(control, summary_sha256=_sha(summary_path))
    constructed = []
    out = tmp_path / "out" / runner.TAG
    assert runner.run_fit(
        out, "technical-b07", {"sha": "technical-b07"}, candidate_checkpoint, TECH_SPEC,
        control=candidate_control, summary_root=tmp_path,
        committed_control_summary=False, agent_setup_hook=lambda _agent: constructed.append(True),
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and not result["fit_started"]
    assert not constructed and result["counts"] == {key: 0 for key in runner._expected_counts(TECH_SPEC)}


def test_mid_collection_failure_preserves_actual_counts_and_evidence(technical_control, tmp_path):
    root, control, checkpoint, _summary = technical_control

    def fail_after_first_transition(event):
        if event["rollout"] == 1 and event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected collection failure")

    out = tmp_path / runner.TAG
    assert runner.run_fit(
        out, "technical-b07", {"sha": "technical-b07"}, checkpoint, TECH_SPEC,
        control=control, summary_root=root / "summaries", committed_control_summary=False,
        training_step_hook=fail_after_first_transition,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["fit_started"]
    assert result["counts"]["training_policy_step_calls"] == 1
    assert result["counts"]["training_team_steps"] == 1
    assert result["counts"]["training_uav_steps"] == TECH_SPEC.train_n
    assert result["counts"]["stored_team_steps"] == 0
    assert result["counts"]["updates"] == 0
    partial = result["incomplete_rollout"]
    assert partial["rollout"] == 1 and partial["phase"] == "collecting_failed"
    assert partial["action_motion_telemetry_partial"]["team_steps"] == 1
    assert result["control_identity_after"]["checkpoint"]["sha256"] == control.checkpoint_sha256


def test_second_rollout_collection_failure_reports_zero_failed_rollout_optimizer_delta(tmp_path):
    spec = replace(TECH_SPEC, rollouts=2, panels=(0, 2))
    control_root = tmp_path / "control"
    control_root.mkdir()
    control, checkpoint, _summary = _make_control(control_root, spec)

    def fail_in_second_collection(event):
        if event["rollout"] == 2 and event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected rollout-two collection failure")

    out = tmp_path / "fit" / runner.TAG
    assert runner.run_fit(
        out, "technical-b07", {"sha": "technical-b07"}, checkpoint, spec,
        control=control, summary_root=control_root / "summaries",
        committed_control_summary=False, training_step_hook=fail_in_second_collection,
    ) == 1
    result = _read(out / "summary.json")
    assert result["counts"]["updates"] == 1
    partial = result["incomplete_rollout"]
    assert partial["rollout"] == 2 and partial["phase"] == "collecting_failed"
    assert partial["optimizer_calls_observed"]["discoverer_actor"] > 0
    for name in ("coordinator", "discoverer_actor", "discoverer_critic",
                 "team_discriminator", "individual_discriminator"):
        assert partial["optimizer_delta_observed"][name] == 0


def test_nonfinite_post_optimizer_failure_publishes_json_safe_entropy(
    technical_control, tmp_path,
):
    root, control, checkpoint, _summary = technical_control

    def corrupt_after_real_actor_step(agent):
        optimizer = agent.discoverer_actor_optimizer
        original_step = optimizer.step

        def failing_step(*args, **kwargs):
            result = original_step(*args, **kwargs)
            with torch.no_grad():
                agent.skill_discoverer.actor.act.action_out.logstd._bias[0] = float("nan")
            raise RuntimeError("injected nonfinite post-step failure")

        optimizer.step = failing_step

    out = tmp_path / runner.TAG
    assert runner.run_fit(
        out, "technical-b07", {"sha": "technical-b07"}, checkpoint, TECH_SPEC,
        control=control, summary_root=root / "summaries", committed_control_summary=False,
        agent_setup_hook=corrupt_after_real_actor_step,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and result["last_boundary"] == "failed"
    snapshot = result["incomplete_rollout"]["entropy_observed_after_failure"]
    assert not snapshot["valid"]
    assert snapshot["raw_log_sigma"][0] is None and snapshot["raw_sigma"][0] is None
    assert snapshot["analytic_raw_entropy"] is None
    assert snapshot["missing_reason"] == "nonfinite_or_wrong_width_logstd_after_failure"


def test_cli_admits_before_fixed_runner_and_rejects_tuning(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "abc"})

    def run_fn(*args, **kwargs):
        calls.append((args, kwargs))
        return 23

    out = tmp_path / runner.TAG
    args = ["--seed", "952201", "--launch-sha", "abc", "--out", str(out),
            "--set-checkpoint", str(tmp_path / "set.pt")]
    assert entry.main(args, run_fn=run_fn) == 23
    assert calls[0] == "admit"
    assert calls[1][0][0] == out.resolve()
    with pytest.raises(SystemExit):
        entry.main(args + ["--lambda-l", "0"], run_fn=run_fn)

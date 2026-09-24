"""Focused real-update checks for the fixed B18 paired roster batch."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.ordinary_roster_training_b18 import runner
from scripts import run_agent_count_ordinary_roster_training_b18 as entry
from scripts.hmasd_admission import ENVIRONMENT_KEY


TECH_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=runner.EVALUATION_ORDER,
    horizon=20, train_lanes=2, eval_lanes=2, rollouts=4, panels=(0, 4),
    hidden_size=16, n_heads=2, n_layers=1, ppo_epochs=1,
    sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1,
)
TECH_SCHEDULES = {"F": (6, 6, 6, 6), "M": (4, 6, 8, 4)}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def completed_batch(tmp_path_factory):
    root = tmp_path_factory.mktemp("ordinary-roster-training-b18")
    observations = []
    arm_index = {"value": -1}

    def instrument(agent):
        arm_index["value"] += 1
        arm = ("F", "M")[arm_index["value"]]
        original = agent.store_transition_batch

        def store(*args, **kwargs):
            if int(kwargs["rollout_step_idx"]) == 0:
                observations.append({
                    "arm": arm, "n": int(agent.config.n_agents),
                    "buffer_n": int(agent.rollout_buffer.n_agents),
                    "action_n": int(np.asarray(kwargs["actions"]).shape[1]),
                    "input_hidden_zero": bool(
                        np.count_nonzero(agent.prev_actor_hidden_np[:TECH_SPEC.train_lanes]) == 0
                    ),
                    "input_critic_hidden_zero": bool(
                        np.count_nonzero(agent.prev_critic_hidden_np[:TECH_SPEC.train_lanes]) == 0
                    ),
                })
            return original(*args, **kwargs)

        agent.store_transition_batch = store

    out = root / runner.TAG
    code = runner.run_batch(
        out, "technical-b18", {"sha": "technical-b18"}, TECH_SPEC,
        schedules=TECH_SCHEDULES, agent_setup_hook=instrument,
    )
    assert code == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), observations


def test_fixed_production_contract_and_optimizer_math():
    assert runner.OBJECT_ID == "s1_ordinary_roster_training_b18"
    assert runner.TAG == entry.TAG == "s1_ordinary_roster_training_b18_b1_s1004101"
    assert runner.SEED == entry.SEED == 1_004_101
    assert runner.TRAINING_WORLD_BASE == 3_044_100
    assert runner.EVALUATION_ORDER == (5, 7, 6, 4, 8)
    assert runner.WORLD_SEED_BASES == {
        4: 2_245_400, 5: 2_245_500, 6: 2_245_600,
        7: 2_245_700, 8: 2_245_800,
    }
    assert runner.SCHEDULES == {"F": (6,) * 45, "M": (4, 6, 8) * 15}
    assert runner.PRODUCTION_SPEC == replace(
        DEFAULT_SPEC, train_n=6, test_ns=(5, 7, 6, 4, 8), eval_lanes=32,
        panels=(0, 45),
    )
    per_update = {
        n: 15 * ((16 * n * (500 // 10) + 32 - 1) // 32)
        for n in (4, 6, 8)
    }
    assert per_update == {4: 1500, 6: 2250, 8: 3000}
    assert sum(per_update[n] for n in runner.SCHEDULES["F"]) == 101_250
    assert sum(per_update[n] for n in runner.SCHEDULES["M"]) == 101_250
    expected = runner._expected_arm_counts(runner.SCHEDULES["M"], runner.PRODUCTION_SPEC)
    assert expected["training_team_steps"] == 360_000
    assert expected["training_uav_steps"] == 2_160_000
    assert expected["evaluation_team_steps"] == 160_000
    assert expected["evaluation_uav_steps"] == 960_000


def test_real_updates_boundaries_sampler_and_terminal_successors(completed_batch):
    out, batch, first_rows = completed_batch
    assert batch["status"] == "complete"
    assert batch["counts"]["fits"] == 2
    assert [(row["arm"], row["n"]) for row in first_rows] == [
        ("F", 6), ("F", 6), ("F", 6), ("F", 6),
        ("M", 4), ("M", 6), ("M", 8), ("M", 4),
    ]
    assert all(row["n"] == row["buffer_n"] == row["action_n"] for row in first_rows)
    assert all(row["input_hidden_zero"] and row["input_critic_hidden_zero"] for row in first_rows)

    for arm, schedule in TECH_SCHEDULES.items():
        result = _read(out / arm / "summary.json")
        assert result["status"] == "complete" and result["fit_started"]
        assert (out / arm / "config.json").is_file()
        assert [row["n"] for row in result["rollouts"]] == list(schedule)
        for n in sorted(set(schedule)):
            count = schedule.count(n)
            exposure = result["training_exposure_by_n"][str(n)]
            assert exposure["rollouts_started"] == exposure["rollouts_updated"] == count
            assert exposure["team_steps"] == exposure["stored_team_steps"] == count * 40
            assert exposure["uav_steps"] == count * 40 * n
            assert exposure["episodes"] == count * 2
            assert exposure["outer_updates_complete"] == count
            assert exposure["recurrent_minibatches_yielded"] == count * n
            assert exposure["sampled_sequences_yielded"] == count * n * 4
            assert exposure["short_sequence_tail_batches"] == 0
            assert exposure["dropped_time_tail_steps"] == 0
            assert exposure["discoverer_actor_optimizer_calls"] == count * n
            assert exposure["discoverer_critic_optimizer_calls"] == count * n
        expected_boundary_count = TECH_SPEC.rollouts - 1 + int(schedule[0] != 6)
        assert len(result["boundaries"]) == expected_boundary_count
        for boundary in result["boundaries"]:
            assert boundary["buffer_replaced"] and boundary["buffer_empty"]
            assert boundary["parameter_objects_preserved"]
            assert boundary["parameter_values_preserved"]
            assert boundary["optimizer_objects_preserved"]
            assert boundary["optimizer_state_preserved"]
            assert boundary["normalizers_preserved"]
            assert boundary["global_rng_preserved"]
            assert boundary["sampler_rng_preserved"]
            assert boundary["shared_value_head_n_agents"] == boundary["new_n"]
            assert boundary["config_n_agents"] == boundary["new_n"]
            assert boundary["buffer_n_agents"] == boundary["new_n"]
        for row in result["rollouts"]:
            expected_batches = row["n"]
            assert row["sampler"]["recurrent_minibatches"] == expected_batches
            assert row["sampler"]["sequence_batch_sizes"] == [4] * expected_batches
            assert row["sampler"]["short_tail_batches"] == 0
            assert row["sampler"]["observed_time_chunk_length"] == 10
            assert row["sampler"]["num_actual_time_steps"] == 20
            assert row["sampler"]["effective_time_steps"] == 20
            assert row["sampler"]["dropped_time_tail_steps"] == 0
            assert set(row["sampler"]["time_chunk_lengths"]) == {10}
            assert row["optimizer_delta"]["discoverer_actor"] == expected_batches
            assert row["optimizer_delta"]["discoverer_critic"] == expected_batches
        with np.load(out / arm / "training_reset_scenes.npz", allow_pickle=False) as trace:
            assert trace["rollout"].tolist() == [1, 2, 3, 4]
            assert trace["n"].tolist() == list(schedule)
            assert trace["lane_world_seeds"].tolist() == [
                [runner.TRAINING_WORLD_BASE + 100 * rollout + lane for lane in range(2)]
                for rollout in range(1, 5)
            ]
        assert result["counts"]["training_episodes"] == 8
        assert "terminal_resets" not in result["counts"]


def test_initial_identity_worlds_evaluation_and_readings(completed_batch):
    out, batch, _ = completed_batch
    identity = batch["initial_identity"]
    assert identity["parameter_normalizer_digest_equal"]
    assert identity["tensor_manifest_equal"]
    assert identity["normalizers_equal"]
    assert identity["full_initial_evaluation_traces_equal"]
    assert batch["common_n6_training_world_identity"]["all_equal"]
    assert [row["rollout"] for row in batch["common_n6_training_world_identity"][
        "matched_rollouts"
    ]] == [2]
    assert set(batch["readings"]["by_test_n"]) == {"4", "5", "6", "7", "8"}
    assert set(batch["readings"]["primary_signs"]) == {"D5J", "D5S", "D7J", "D7S"}
    assert batch["readings"]["cross_n_aggregate"] is None
    for arm in ("F", "M"):
        result = _read(out / arm / "summary.json")
        assert [(row["policy_stage"], row["test_n"]) for row in result["panels"]] == [
            (stage, n) for stage in (0, 4) for n in runner.EVALUATION_ORDER
        ]
        for n in runner.EVALUATION_ORDER:
            initial = next(row for row in result["panels"] if row["policy_stage"] == 0 and row["test_n"] == n)
            final = next(row for row in result["panels"] if row["policy_stage"] == 4 and row["test_n"] == n)
            assert initial["world_seeds"] == final["world_seeds"]
            assert initial["initial_world_identity"] == final["initial_world_identity"]
            assert initial["training_storage_calls"] == final["training_storage_calls"] == 0
            assert not any(initial["optimizer_calls"].values())
            assert not any(final["optimizer_calls"].values())
            with np.load(out / arm / f"trace_stage00_n{n}.npz", allow_pickle=False) as trace:
                assert trace["initial_uav_positions"].shape == (TECH_SPEC.eval_lanes, n, 3)
                assert trace["initial_user_positions"].shape == (TECH_SPEC.eval_lanes, 50, 2)


def test_partial_failure_retains_counts_worlds_and_unstarted_arm(tmp_path):
    out = tmp_path / runner.TAG

    def fail(event):
        if event["arm"] == "F" and event["rollout"] == 1 and event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected B18 transition failure")

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-b18-failure", {"sha": "technical-b18-failure"}, one,
        schedules={"F": (6,), "M": (4,)}, training_step_hook=fail,
    ) == 1
    batch = _read(out / "summary.json")
    f = _read(out / "F/summary.json")
    m = _read(out / "M/summary.json")
    assert batch["status"] == "failed"
    assert f["status"] == "failed" and f["fit_started"]
    assert f["counts"]["fits"] == 1
    assert f["counts"]["training_team_steps"] == 1
    assert f["counts"]["stored_team_steps"] == 0
    assert f["training_reset_trace"]["partial"]
    exposure = f["training_exposure_by_n"]["6"]
    assert exposure["rollouts_started"] == 1 and exposure["rollouts_updated"] == 0
    assert exposure["team_steps"] == 1 and exposure["uav_steps"] == 6
    assert exposure["stored_team_steps"] == exposure["episodes"] == 0
    assert exposure["outer_updates_complete"] == 0
    assert (out / "F/training_reset_scenes.npz").is_file()
    assert m["status"] == "unstarted" and not m["fit_started"]
    assert batch["counts"]["fits"] == 1
    assert batch["counts"]["training_team_steps"] == 1


def test_mid_update_failure_retains_live_sampler_audit(tmp_path):
    out = tmp_path / runner.TAG

    def instrument(agent):
        fired = {"value": False}

        def fail_after_step(_optimizer, _args, _kwargs):
            if not fired["value"]:
                fired["value"] = True
                raise RuntimeError("injected B18 optimizer failure")

        agent.discoverer_actor_optimizer.register_step_post_hook(fail_after_step)

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-b18-update-failure", {"sha": "technical-b18-update-failure"}, one,
        schedules={"F": (6,), "M": (4,)}, agent_setup_hook=instrument,
    ) == 1
    failed = _read(out / "F/summary.json")
    assert failed["status"] == "failed" and failed["fit_started"]
    audit = failed["incomplete_rollout"]["sampler_audit_partial"]
    assert audit["status"] == "running"
    assert audit["recurrent_minibatches"] == 1
    assert audit["sequence_batch_sizes"] == [4]
    assert audit["time_chunk_lengths"] == [10]
    assert audit["num_actual_time_steps"] == 20
    assert audit["effective_time_steps"] == 20
    assert audit["dropped_time_tail_steps"] == 0
    exposure = failed["training_exposure_by_n"]["6"]
    assert exposure["rollouts_started"] == 1 and exposure["rollouts_updated"] == 0
    assert exposure["team_steps"] == exposure["stored_team_steps"] == 40
    assert exposure["uav_steps"] == 240 and exposure["episodes"] == 2
    assert exposure["outer_updates_complete"] == 0
    assert exposure["recurrent_minibatches_yielded"] == 1
    assert exposure["sampled_sequences_yielded"] == 4
    assert exposure["short_sequence_tail_batches"] == 0
    assert "injected B18 optimizer failure" in failed["failure"]


def test_later_collection_failure_uses_current_rollout_optimizer_baseline(tmp_path):
    out = tmp_path / runner.TAG

    def fail(event):
        if event["arm"] == "F" and event["rollout"] == 2 and event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected B18 rollout2 collection failure")

    two = replace(TECH_SPEC, rollouts=2, panels=(0, 2))
    assert runner.run_batch(
        out, "technical-b18-rollout2-failure", {"sha": "technical-b18-rollout2-failure"}, two,
        schedules={"F": (6, 6), "M": (4, 6)}, training_step_hook=fail,
    ) == 1
    failed = _read(out / "F/summary.json")
    exposure = failed["training_exposure_by_n"]["6"]
    assert exposure["rollouts_started"] == 2 and exposure["rollouts_updated"] == 1
    assert exposure["team_steps"] == 41 and exposure["stored_team_steps"] == 40
    assert exposure["uav_steps"] == 246 and exposure["episodes"] == 2
    assert exposure["outer_updates_complete"] == 1
    assert exposure["discoverer_actor_optimizer_calls"] == 6
    assert exposure["discoverer_critic_optimizer_calls"] == 6
    assert failed["incomplete_rollout"]["optimizer_delta_observed"]["discoverer_actor"] == 0


def test_collected_publish_failure_keeps_current_optimizer_baseline(tmp_path, monkeypatch):
    out = tmp_path / runner.TAG
    original = runner.write_json
    fired = False

    def fail_collected_publish(path, value):
        nonlocal fired
        if not fired and value.get("last_boundary") == "rollout 2 N=6 collected":
            fired = True
            raise OSError("injected B18 collected publish failure")
        return original(path, value)

    monkeypatch.setattr(runner, "write_json", fail_collected_publish)
    two = replace(TECH_SPEC, rollouts=2, panels=(0, 2))
    assert runner.run_batch(
        out, "technical-b18-publish-failure", {"sha": "technical-b18-publish-failure"}, two,
        schedules={"F": (6, 6), "M": (4, 6)},
    ) == 1
    failed = _read(out / "F/summary.json")
    exposure = failed["training_exposure_by_n"]["6"]
    assert fired and failed["status"] == "failed"
    assert exposure["team_steps"] == exposure["stored_team_steps"] == 80
    assert exposure["outer_updates_complete"] == 1
    assert exposure["discoverer_actor_optimizer_calls"] == 6
    assert exposure["discoverer_critic_optimizer_calls"] == 6
    assert failed["incomplete_rollout"]["optimizer_delta_observed"]["discoverer_actor"] == 0
    assert "injected B18 collected publish failure" in failed["failure"]


def test_post_update_failure_does_not_double_count_optimizer_calls(tmp_path):
    out = tmp_path / runner.TAG

    def instrument(agent):
        original = agent.clear_buffers

        def fail_after_clear():
            original()
            raise RuntimeError("injected B18 post-update clear failure")

        agent.clear_buffers = fail_after_clear

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-b18-post-update-failure", {"sha": "technical-b18-post-update-failure"}, one,
        schedules={"F": (6,), "M": (4,)}, agent_setup_hook=instrument,
    ) == 1
    failed = _read(out / "F/summary.json")
    exposure = failed["training_exposure_by_n"]["6"]
    assert exposure["rollouts_started"] == exposure["rollouts_updated"] == 1
    assert exposure["outer_updates_complete"] == 1
    assert exposure["recurrent_minibatches_yielded"] == 6
    assert exposure["discoverer_actor_optimizer_calls"] == 6
    assert exposure["discoverer_critic_optimizer_calls"] == 6
    assert failed["incomplete_rollout"]["optimizer_calls_accounted"]["discoverer_actor"] == 6
    assert failed["incomplete_rollout"]["optimizer_delta_observed"]["discoverer_actor"] == 6
    assert "injected B18 post-update clear failure" in failed["failure"]


def test_admission_artifacts_allowed_but_scientific_output_refused(tmp_path):
    allowed = tmp_path / runner.TAG
    allowed.mkdir()
    for name in ("launch-manifest.json", "launch-status.json", "admission-preflight.json",
                 "stdout.log", "stderr.log"):
        (allowed / name).write_text("{}\n", encoding="utf-8")
    # Fail immediately in the arm hook; reaching it proves admission-owned files were accepted.
    def fail(_agent):
        raise RuntimeError("accepted launch artifacts")
    assert runner.run_batch(
        allowed, "technical-artifacts", {"sha": "technical-artifacts"},
        replace(TECH_SPEC, rollouts=1, panels=(0, 1)),
        schedules={"F": (6,), "M": (4,)}, agent_setup_hook=fail,
    ) == 1
    refused = tmp_path / "other" / runner.TAG
    refused.mkdir(parents=True)
    (refused / "config.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="existing B18 scientific output"):
        runner.run_batch(
            refused, "x", {"sha": "x"}, replace(TECH_SPEC, rollouts=1, panels=(0, 1)),
            schedules={"F": (6,), "M": (4,)},
        )


def test_cli_admits_before_candidate_import_and_direct_cli_refuses(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        entry, "require_admission", lambda *_a, **_k: calls.append("admit") or {"sha": "x"},
    )
    result = entry.main([
        "--seed", str(entry.SEED), "--launch-sha", "x",
        "--out", str(tmp_path / entry.TAG),
    ], run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 7)
    assert result == 7 and calls[0] == "admit"
    args, kwargs = calls[1]
    assert args[1] == "x" and args[2] == {"sha": "x"}
    assert kwargs["command_start"] == entry.COMMAND_START

    out = tmp_path / "direct" / entry.TAG
    environment = dict(os.environ)
    environment.pop(ENVIRONMENT_KEY, None)
    process = subprocess.run(
        [sys.executable, str(Path(entry.__file__).resolve()),
         "--seed", str(entry.SEED), "--launch-sha", "0" * 40, "--out", str(out)],
        cwd=entry.ROOT, env=environment, capture_output=True, text=True, timeout=30,
    )
    assert process.returncode != 0
    assert "missing HMASD admission" in process.stderr
    assert not out.exists()

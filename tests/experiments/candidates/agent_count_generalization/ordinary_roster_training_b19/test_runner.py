"""Focused real-update checks for the fixed B19 paired roster batch."""
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

from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.ordinary_roster_training_b19 import runner
from scripts import run_agent_count_ordinary_roster_training_b19 as entry
from scripts.hmasd_admission import ENVIRONMENT_KEY


TECH_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=runner.EVALUATION_ORDER,
    horizon=20, train_lanes=2, eval_lanes=2, rollouts=4, panels=(0, 4),
    hidden_size=16, n_heads=2, n_layers=1, ppo_epochs=1,
    sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1,
)
TECH_SEED = 9_191_019
COMPLETED_SPEC = replace(TECH_SPEC, torch_threads=4)
TECH_SCHEDULES = {"F": (6, 6, 6, 6), "M": (4, 6, 8, 4)}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_training_stream_prefix(arm_out: Path, summary: dict) -> None:
    identity = summary["training_stream"]
    stream = arm_out / identity["path"]
    prefix = stream.read_bytes()[:identity["bytes"]]
    assert len(prefix) == identity["bytes"]
    assert hashlib.sha256(prefix).hexdigest() == identity["sha256"]
    assert len(prefix.splitlines()) == identity["completed_rows"]
    assert identity["completed_rows"] == len(summary["rollouts"])


@pytest.fixture(scope="module")
def completed_batch(tmp_path_factory):
    root = tmp_path_factory.mktemp("ordinary-roster-training-b19")
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
        out, "technical-b19", {"sha": "technical-b19"}, COMPLETED_SPEC,
        technical_seed=TECH_SEED, schedules=TECH_SCHEDULES, agent_setup_hook=instrument,
    )
    assert code == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json"), observations


def test_fixed_production_contract_and_optimizer_math():
    assert runner.OBJECT_ID == "s1_ordinary_roster_training_b19"
    assert runner.TAG == entry.TAG == "s1_ordinary_roster_training_b19_b1_s1015101"
    assert runner.SEED == entry.SEED == 1_015_101
    assert runner.TRAINING_WORLD_BASE == 3_145_100
    assert runner.EVALUATION_ORDER == (5, 7, 6)
    assert runner.WORLD_SEED_BASES == {5: 2_345_500, 7: 2_345_700, 6: 2_345_600}
    assert runner.SCHEDULES == {"F": (6,) * 45, "M": (4, 6, 8) * 15}
    assert runner.PRODUCTION_SPEC == replace(
        DEFAULT_SPEC, train_n=6, test_ns=(5, 7, 6), eval_lanes=32,
        panels=(0, 45),
    )
    per_update = {
        n: 15 * ((16 * n * (500 // 10) + 32 - 1) // 32)
        for n in (4, 6, 8)
    }
    assert per_update == {4: 1500, 6: 2250, 8: 3000}
    assert sum(per_update[n] for n in runner.SCHEDULES["F"]) == 101_250
    assert sum(per_update[n] for n in runner.SCHEDULES["M"]) == 101_250
    expected = runner._expected_arm_counts(
        runner.SCHEDULES["M"], runner.PRODUCTION_SPEC, common_stage0=True,
    )
    assert expected["training_team_steps"] == 360_000
    assert expected["training_uav_steps"] == 2_160_000
    assert expected["evaluation_team_steps"] == 48_000
    assert expected["evaluation_uav_steps"] == 288_000


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
        assert result["spec"]["torch_threads"] == 4
        assert (out / arm / "config.json").is_file()
        _assert_training_stream_prefix(out / arm, result)
        raw_init = result["initialization"]["raw"]
        init_path = out / arm / raw_init["path"]
        assert init_path.stat().st_size == raw_init["bytes"]
        assert hashlib.sha256(init_path.read_bytes()).hexdigest() == raw_init["sha256"]
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
        raw_rows = [json.loads(line) for line in (out / arm / "raw/training.jsonl").read_text().splitlines()]
        assert len(raw_rows) == len(result["rollouts"])
        for row in raw_rows:
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
        assert len(result["training_reset_scenes"]) == 4
        for rollout, n in enumerate(schedule, start=1):
            record = result["training_reset_scenes"][rollout - 1]
            path = out / arm / record["path"]
            assert record["sha256"] == runner.b15.file_sha256(path)
            with np.load(path, allow_pickle=False) as trace:
                assert int(trace["rollout"]) == rollout
                assert int(trace["n"]) == n
                assert trace["lane_world_seeds"].tolist() == [
                    runner.TRAINING_WORLD_BASE + 10_000_000 + 100 * rollout + lane
                    for lane in range(2)
                ]
                assert trace["observations"].shape[1] == n
        assert result["counts"]["training_episodes"] == 8
        assert "terminal_resets" not in result["counts"]


def test_initial_identity_worlds_evaluation_and_readings(completed_batch):
    out, batch, _ = completed_batch
    identity = batch["initial_identity"]
    assert all(value for key, value in identity.items() if key.endswith("_equal"))
    assert identity["common_stage0_reused_without_new_steps"]
    assert batch["counts"]["panels"] == 9
    assert batch["counts"]["evaluation_team_steps"] == 9 * TECH_SPEC.eval_lanes * TECH_SPEC.horizon
    assert batch["counts"]["evaluation_episodes"] == 9 * TECH_SPEC.eval_lanes
    assert batch["counts"]["evaluation_storage_calls"] == 0
    assert batch["counts"]["evaluation_optimizer_calls"] == 0
    assert batch["common_n6_training_world_identity"]["all_equal"]
    assert [row["rollout"] for row in batch["common_n6_training_world_identity"][
        "matched_rollouts"
    ]] == [2]
    assert set(batch["readings"]["by_test_n"]) == {"5", "6", "7"}
    assert set(batch["readings"]["primary_signs"]) == {"D5J", "D5S", "D7J", "D7S"}
    assert batch["readings"]["cross_n_aggregate"] is None
    for arm in ("F", "M"):
        result = _read(out / arm / "summary.json")
        stages = (0, 4) if arm == "F" else (4,)
        assert [(row["policy_stage"], row["test_n"]) for row in result["panels"]] == [
            (stage, n) for stage in stages for n in runner.EVALUATION_ORDER
        ]
        for n in runner.EVALUATION_ORDER:
            initial = next(row for row in _read(out / "F/summary.json")["panels"]
                           if row["policy_stage"] == 0 and row["test_n"] == n)
            final = next(row for row in result["panels"] if row["policy_stage"] == 4 and row["test_n"] == n)
            assert initial["world_seeds"] == final["world_seeds"]
            assert initial["initial_world_identity"] == final["initial_world_identity"]
            assert initial["training_storage_calls"] == final["training_storage_calls"] == 0
            assert not any(initial["optimizer_calls"].values())
            assert not any(final["optimizer_calls"].values())
            with np.load(out / "F/raw" / f"trace_stage00_n{n}.npz", allow_pickle=False) as trace:
                assert trace["initial_uav_positions"].shape == (TECH_SPEC.eval_lanes, n, 3)
                assert trace["initial_user_positions"].shape == (TECH_SPEC.eval_lanes, 50, 2)
            assert initial["world_seeds"] == [
                runner.WORLD_SEED_BASES[n] + 10_000_000 + lane
                for lane in range(TECH_SPEC.eval_lanes)
            ]
            assert final["trace"]["relative_to_arm"].startswith("raw/")
        assert result["source_hashes_unchanged"]
        assert (out / arm / "raw/initialization.json").is_file()
    assert not list((out / "M/raw").glob("trace_stage00_*.npz"))
    assert _read(out / "M/summary.json")["common_stage0"]["new_environment_steps"] == 0


def test_partial_failure_retains_counts_worlds_and_unstarted_arm(tmp_path):
    out = tmp_path / runner.TAG

    def fail(event):
        if event["arm"] == "F" and event["rollout"] == 1 and event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected B19 transition failure")

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-b19-failure", {"sha": "technical-b19-failure"}, one,
        technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)}, training_step_hook=fail,
    ) == 1
    batch = _read(out / "summary.json")
    f = _read(out / "F/summary.json")
    m = _read(out / "M/summary.json")
    assert batch["status"] == "failed"
    assert f["status"] == "failed" and f["fit_started"]
    assert f["counts"]["fits"] == 1
    assert f["counts"]["training_team_steps"] == 1
    assert "training_stream" not in f
    assert f["counts"]["stored_team_steps"] == 0
    assert len(f["training_reset_scenes"]) == 1
    exposure = f["training_exposure_by_n"]["6"]
    assert exposure["rollouts_started"] == 1 and exposure["rollouts_updated"] == 0
    assert exposure["team_steps"] == 1 and exposure["uav_steps"] == 6
    assert exposure["stored_team_steps"] == exposure["episodes"] == 0
    assert exposure["outer_updates_complete"] == 0
    assert (out / "F" / f["training_reset_scenes"][0]["path"]).is_file()
    assert m["status"] == "unstarted" and not m["fit_started"]
    assert batch["counts"]["fits"] == 1
    assert batch["counts"]["training_team_steps"] == 1


def test_first_training_policy_exception_publishes_zero_step_failure(tmp_path):
    out = tmp_path / runner.TAG

    def instrument(agent):
        def fail_first_step(*_args, **_kwargs):
            raise RuntimeError("injected B19 first training policy failure")

        agent.step = fail_first_step

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-first-step", {"sha": "technical-first-step"}, one,
        technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)},
        agent_setup_hook=instrument,
    ) == 1
    batch = _read(out / "summary.json")
    f = _read(out / "F/summary.json")
    m = _read(out / "M/summary.json")
    assert batch["status"] == f["status"] == "failed"
    assert f["counts"]["training_team_steps"] == 0
    assert f["counts"]["stored_team_steps"] == 0
    assert f["counts"]["updates"] == 0
    assert not f["fit_started"]
    assert m["status"] == "unstarted" and not m["fit_started"]
    assert f["incomplete_rollout"]["phase"] == "collecting_failed"
    motion = f["incomplete_rollout"]["_telemetry"]
    assert motion["team_steps"] == 0
    assert motion["executed_min"] is None and motion["executed_max"] is None
    assert motion["raw_coordinate_violations"]["denominator"] == 0
    json.dumps(batch, allow_nan=False)
    json.dumps(f, allow_nan=False)


def test_mid_update_failure_retains_live_sampler_audit(tmp_path):
    out = tmp_path / runner.TAG

    def instrument(agent):
        fired = {"value": False}

        def fail_after_step(_optimizer, _args, _kwargs):
            if not fired["value"]:
                fired["value"] = True
                raise RuntimeError("injected B19 optimizer failure")

        agent.discoverer_actor_optimizer.register_step_post_hook(fail_after_step)

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-b19-update-failure", {"sha": "technical-b19-update-failure"}, one,
        technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)}, agent_setup_hook=instrument,
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
    assert "injected B19 optimizer failure" in failed["failure"]


def test_later_collection_failure_uses_current_rollout_optimizer_baseline(tmp_path):
    out = tmp_path / runner.TAG

    def fail(event):
        if event["arm"] == "F" and event["rollout"] == 2 and event["t"] == 0 and event["lane"] == 0:
            raise RuntimeError("injected B19 rollout2 collection failure")

    two = replace(TECH_SPEC, rollouts=2, panels=(0, 2))
    assert runner.run_batch(
        out, "technical-b19-rollout2-failure", {"sha": "technical-b19-rollout2-failure"}, two,
        technical_seed=TECH_SEED, schedules={"F": (6, 6), "M": (4, 6)}, training_step_hook=fail,
    ) == 1
    failed = _read(out / "F/summary.json")
    _assert_training_stream_prefix(out / "F", failed)
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
            raise OSError("injected B19 collected publish failure")
        return original(path, value)

    monkeypatch.setattr(runner, "write_json", fail_collected_publish)
    two = replace(TECH_SPEC, rollouts=2, panels=(0, 2))
    assert runner.run_batch(
        out, "technical-b19-publish-failure", {"sha": "technical-b19-publish-failure"}, two,
        technical_seed=TECH_SEED, schedules={"F": (6, 6), "M": (4, 6)},
    ) == 1
    failed = _read(out / "F/summary.json")
    exposure = failed["training_exposure_by_n"]["6"]
    assert fired and failed["status"] == "failed"
    assert exposure["team_steps"] == exposure["stored_team_steps"] == 80
    assert exposure["outer_updates_complete"] == 1
    assert exposure["discoverer_actor_optimizer_calls"] == 6
    assert exposure["discoverer_critic_optimizer_calls"] == 6
    assert failed["incomplete_rollout"]["optimizer_delta_observed"]["discoverer_actor"] == 0
    assert "injected B19 collected publish failure" in failed["failure"]


@pytest.mark.parametrize("phase", ["reset complete", "collecting"])
def test_reset_boundary_publish_failure_keeps_prior_optimizer_baseline(tmp_path, monkeypatch, phase):
    out = tmp_path / runner.TAG
    original = runner.write_json
    fired = False

    def fail_boundary(path, value):
        nonlocal fired
        if not fired and value.get("last_boundary") == f"rollout 2 N=6 {phase}":
            fired = True
            raise OSError(f"injected B19 {phase} publish failure")
        return original(path, value)

    monkeypatch.setattr(runner, "write_json", fail_boundary)
    two = replace(TECH_SPEC, rollouts=2, panels=(0, 2))
    assert runner.run_batch(
        out, f"technical-{phase}", {"sha": f"technical-{phase}"}, two,
        technical_seed=TECH_SEED, schedules={"F": (6, 6), "M": (4, 6)},
    ) == 1
    failed = _read(out / "F/summary.json")
    exposure = failed["training_exposure_by_n"]["6"]
    assert fired and failed["status"] == "failed"
    assert exposure["rollouts_started"] == 2 and exposure["rollouts_updated"] == 1
    assert exposure["discoverer_actor_optimizer_calls"] == 6
    assert exposure["discoverer_critic_optimizer_calls"] == 6
    assert failed["incomplete_rollout"]["optimizer_delta_observed"]["discoverer_actor"] == 0
    assert failed["incomplete_rollout"]["phase"] == phase.replace(" ", "_") + "_failed"
    assert len(failed["training_reset_scenes"]) == 2


def test_post_update_failure_does_not_double_count_optimizer_calls(tmp_path):
    out = tmp_path / runner.TAG

    def instrument(agent):
        original = agent.clear_buffers

        def fail_after_clear():
            original()
            raise RuntimeError("injected B19 post-update clear failure")

        agent.clear_buffers = fail_after_clear

    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    assert runner.run_batch(
        out, "technical-b19-post-update-failure", {"sha": "technical-b19-post-update-failure"}, one,
        technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)}, agent_setup_hook=instrument,
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
    assert "injected B19 post-update clear failure" in failed["failure"]


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
        technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)}, agent_setup_hook=fail,
    ) == 1
    refused = tmp_path / "other" / runner.TAG
    refused.mkdir(parents=True)
    (refused / "config.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="existing B19 scientific output"):
        runner.run_batch(
            refused, "x", {"sha": "x"}, replace(TECH_SPEC, rollouts=1, panels=(0, 1)),
            technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)},
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


def test_initial_runtime_mismatch_stops_m_before_training(tmp_path, monkeypatch):
    original = runner._initialization
    built = 0

    def changed(arm, config, out):
        nonlocal built
        agent, evidence = original(arm, config, out)
        built += 1
        if built == 2:
            evidence["runtime_digest"] = "injected-mismatch"
        return agent, evidence

    monkeypatch.setattr(runner, "_initialization", changed)
    one = replace(TECH_SPEC, rollouts=1, panels=(0, 1))
    out = tmp_path / runner.TAG
    assert runner.run_batch(
        out, "technical-identity", {"sha": "technical-identity"}, one,
        technical_seed=TECH_SEED, schedules={"F": (6,), "M": (4,)},
    ) == 1
    batch = _read(out / "summary.json")
    m = _read(out / "M/summary.json")
    assert batch["status"] == "failed"
    assert m["status"] == "failed" and not m["fit_started"]
    assert m["counts"]["training_team_steps"] == 0
    assert m["counts"]["panels"] == 0
    assert "runtime_digest mismatch" in m["failure"]


def test_reset_records_survive_abrupt_child_exit(tmp_path):
    out = tmp_path / runner.TAG
    script = """
import os
import sys
from dataclasses import replace
from pathlib import Path
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.ordinary_roster_training_b19 import runner
spec = replace(DEFAULT_SPEC, train_n=6, test_ns=runner.EVALUATION_ORDER,
               horizon=20, train_lanes=2, eval_lanes=2, rollouts=2, panels=(0, 2),
               hidden_size=16, n_heads=2, n_layers=1, ppo_epochs=1,
               sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1)
def stop(event):
    if event['arm'] == 'F' and event['rollout'] == 2 and event['t'] == 0 and event['lane'] == 0:
        os._exit(93)
runner.run_batch(Path(sys.argv[1]), 'technical-abrupt', {'sha': 'technical-abrupt'},
                 spec, technical_seed=9191019,
                 schedules={'F': (6, 6), 'M': (4, 6)}, training_step_hook=stop)
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(out)], cwd=entry.ROOT,
        capture_output=True, text=True, timeout=60,
    )
    assert process.returncode == 93, process.stderr
    for rollout in (1, 2):
        path = out / "F/raw" / f"training_reset_r{rollout:02d}_n6.npz"
        assert path.is_file()
        with np.load(path, allow_pickle=False) as trace:
            assert int(trace["rollout"]) == rollout
            assert trace["states"].shape[0] == 2
            assert trace["observations"].shape[1] == 6
    f = _read(out / "F/summary.json")
    assert f["last_boundary"] == "rollout 2 N=6 collecting"
    assert len(f["training_reset_scenes"]) == 2
    assert len(f["rollouts"]) == 1
    assert len((out / "F/raw/training.jsonl").read_text().splitlines()) == 1
    _assert_training_stream_prefix(out / "F", f)
    # A later unacknowledged append cannot change the recorded complete prefix.
    with (out / "F/raw/training.jsonl").open("ab") as stream:
        stream.write(b'{"unacknowledged":true}\n')
    _assert_training_stream_prefix(out / "F", f)
    assert not (out / "M").exists()


def test_source_mismatch_and_existing_cli_output_refuse_before_science(tmp_path, monkeypatch):
    out = tmp_path / runner.TAG
    with pytest.raises(ValueError, match="launch SHA disagrees"):
        runner.run_batch(out, "wrong", {"sha": "right"}, TECH_SPEC,
                         technical_seed=TECH_SEED, schedules=TECH_SCHEDULES)
    assert not out.exists()
    out.mkdir()
    (out / "summary.json").write_text("{}\n", encoding="utf-8")
    called = False

    def admit(*_args, **_kwargs):
        nonlocal called
        called = True
        return {"sha": "x"}

    monkeypatch.setattr(entry, "require_admission", admit)
    with pytest.raises(SystemExit):
        entry.main(["--seed", str(entry.SEED), "--launch-sha", "x", "--out", str(out)])
    assert not called

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import pytest
import torch

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC as SOURCE_DEFAULT_SPEC,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    save_checkpoint,
    seed_rng,
)
from experiments.candidates.load_critical_member_generalization.load_probe import probe
from experiments.candidates.load_critical_member_generalization.load_probe.scenes import (
    make_native_scene,
    matched_world,
)
from scripts import run_load_critical_member_probe_b01 as entry


TECH_SOURCE_SPEC = replace(
    SOURCE_DEFAULT_SPEC,
    hidden_size=16,
    n_heads=2,
    n_layers=1,
    ppo_epochs=1,
    sequence_batch_size=16,
    coordinator_batch_size=16,
)
TECH_PROBE_SPEC = probe.ProbeSpec(
    cells=probe.CELLS,
    world_ids=(0,),
    horizon=12,
    source_num_envs=16,
    torch_threads=1,
)
TWO_WORLD_SPEC = replace(TECH_PROBE_SPEC, world_ids=(0, 1), horizon=2)


def _env(n: int, *, horizon: int = 12):
    native = make_native_scene(n_uavs=n, capacity=10, world_id=0, horizon=horizon)
    return CountAdapter(ParallelToArrayAdapter(native, seed=17))


def _commit(repository: Path, message: str = "fixture") -> None:
    paths = [
        f"runs/{probe.SOURCE_DIRECTION}/{tag}/summary.json"
        for _arm, _seed, tag in probe.SOURCE_POLICIES
    ]
    subprocess.run(["git", "-C", str(repository), "add", "--", *paths], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-m", message, "--", *paths],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.fixture(scope="module")
def source_fixture(tmp_path_factory):
    root = tmp_path_factory.mktemp("load-probe-sources")
    repository = root / "repository"
    checkpoints = root / "checkpoints"
    repository.mkdir()
    checkpoints.mkdir()
    subprocess.run(["git", "-C", str(repository), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.name", "Fixture"], check=True
    )

    for index, (arm, seed, tag) in enumerate(probe.SOURCE_POLICIES, start=1):
        seed_rng(seed)
        train_env = _env(6)
        config = make_config(arm, [train_env] * 16, seed, TECH_SOURCE_SPEC)
        agent = build_agent(config, str(root / "source-logs" / arm.lower()))
        checkpoint_dir = checkpoints / tag
        checkpoint_dir.mkdir()
        checkpoint_record = save_checkpoint(
            agent, checkpoint_dir, 45, config, probe.PRODUCER_SHA
        )

        panels = []
        for n in (4, 6, 8):
            panel_env = _env(n)
            panel_config = make_config(arm, [panel_env] * 16, seed, TECH_SOURCE_SPEC)
            panels.append(
                {
                    "after_rollout": 45,
                    "test_n": n,
                    "status": "complete",
                    "steps": 8_000,
                    "episodes": 16,
                    "config": config_dict(panel_config),
                }
            )
            panel_env.close()

        summary = {
            "schema": 1,
            "object_id": probe.SOURCE_OBJECT_ID,
            "direction": probe.SOURCE_DIRECTION,
            "cell": {
                "index": index,
                "key": f"{arm.lower()}_clip",
                "arm": arm,
                "law": "clip",
                "seed": seed,
                "tag": tag,
                "initial_digest_source": None,
            },
            "arm": arm,
            "training_action_law": "clip",
            "seed": seed,
            "tag": tag,
            "launch_sha": probe.PRODUCER_SHA,
            "status": "complete",
            "fit_started": True,
            "spec": vars(TECH_SOURCE_SPEC),
            "panels": panels,
            "checkpoints": [checkpoint_record],
            "counts": {
                "training_team_steps": 360_000,
                "stored_team_steps": 360_000,
                "training_episodes": 720,
                "terminal_resets": 720,
                "updates": 45,
                "evaluation_team_steps": 96_000,
                "evaluation_episodes": 192,
            },
            "evaluation_action_law": "clip",
            "config": config_dict(config),
            "initial_digest_matches_expected": True,
            "final_parameter_normalizer_digest": probe.digest_agent(agent),
        }
        summary_path = (
            repository / "runs" / probe.SOURCE_DIRECTION / tag / "summary.json"
        )
        summary_path.parent.mkdir(parents=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        train_env.close()
    _commit(repository)
    return {
        "repository": repository,
        "summaries": repository / "runs" / probe.SOURCE_DIRECTION,
        "checkpoints": checkpoints,
    }


@pytest.fixture(scope="module")
def completed_probe(tmp_path_factory, source_fixture):
    out = tmp_path_factory.mktemp("load-probe-complete") / "attempt"
    out.mkdir()
    # A native launcher creates control files before the entry starts.
    (out / "launch-manifest.json").write_text("{}\n", encoding="utf-8")
    started = time.perf_counter()
    assert probe.run_probe_impl(
        out,
        source_fixture["checkpoints"],
        "technical-fixture",
        {"sha": "technical-fixture"},
        TECH_PROBE_SPEC,
        tracked_summary_root=source_fixture["summaries"],
        repository_root=source_fixture["repository"],
    ) == 0
    return out, json.loads((out / "summary.json").read_text()), time.perf_counter() - started


@pytest.fixture(scope="module")
def two_world_probe(tmp_path_factory, source_fixture):
    out = tmp_path_factory.mktemp("load-probe-two-world") / "attempt"
    out.mkdir()
    assert probe.run_probe_impl(
        out,
        source_fixture["checkpoints"],
        "technical-fixture",
        {"sha": "technical-fixture"},
        TWO_WORLD_SPEC,
        tracked_summary_root=source_fixture["summaries"],
        repository_root=source_fixture["repository"],
    ) == 0
    return out, json.loads((out / "summary.json").read_text())


def test_complete_actual_h6_set_paths_cover_k10_all_rosters_and_fixed_cells(completed_probe):
    out, summary, _elapsed = completed_probe
    assert summary["status"] == "complete"
    assert summary["counts"] == {
        "fits": 0,
        "training_team_steps": 0,
        "training_episodes": 0,
        "updates": 0,
        "optimizer_calls": 0,
        "evaluation_team_steps": 120,
        "evaluation_episodes": 10,
        "completed_cells": 10,
        "completed_worlds": 10,
        "technical_input_checks": 2,
    }
    assert {(row["arm"], row["test_n"], row["capacity"]) for row in summary["cells"]} == {
        (arm, n, capacity)
        for arm in ("H6", "SET")
        for n, capacity in probe.CELLS
    }
    for cell in summary["cells"]:
        assert cell["config"]["num_envs"] == 16
        assert cell["active_inference_rows"] == 1
        assert cell["config"]["k"] == 10
        assert cell["steps"] == 12 and cell["episodes"] == 1
        assert not any(cell["optimizer_calls"].values())
        assert cell["model_normalizer_digest_before"] == cell["model_normalizer_digest_after"]
        assert cell["checkpoint_sha256_before"] == cell["checkpoint_sha256_after"]
        world = cell["worlds"][0]
        assert world["runtime_seed"] == probe.runtime_seed(0, cell["test_n"])
        assert world["capacity_identity_applicable_all"]
        assert world["capacity_identity_holds_all_applicable"]
        trace = probe._load_trace(out, world["trace"])
        assert trace["raw_actions"].shape == (12, cell["test_n"], 3)
        assert trace["observations"].shape == (13, cell["test_n"], 104)
        assert trace["encoded_states"].shape == (13, 133)
        assert trace["native_positions"].dtype == np.float64
        assert len(trace["runtime_after_action"]) == 12

    assert len(summary["capacity_pairs"]) == 4
    assert all(row["exact_same_policy_capacity_trajectories"] for row in summary["capacity_pairs"])
    assert all(row["height_cancels"] for row in summary["capacity_pairs"])
    assert any(row["delta_mean_served"]["mean"] > 0 for row in summary["capacity_pairs"])


def test_each_trace_binds_its_declared_world_across_arms_rosters_and_capacities(
    two_world_probe,
):
    out, summary = two_world_probe
    assert summary["counts"]["evaluation_team_steps"] == 40
    assert summary["counts"]["evaluation_episodes"] == 20
    assert summary["counts"]["completed_worlds"] == 20

    expected = {world_id: matched_world(world_id) for world_id in (0, 1)}
    assert not np.array_equal(expected[0].user_positions, expected[1].user_positions)
    assert not np.array_equal(expected[0].uav_positions, expected[1].uav_positions)

    seen = {}
    for cell in summary["cells"]:
        for row in cell["worlds"]:
            trace = probe._load_trace(out, row["trace"])
            world = expected[row["world_id"]]
            initial_users = trace["native_user_positions"][0]
            initial_uavs = trace["native_positions"][0]
            assert initial_users.dtype == np.float64
            assert initial_uavs.dtype == np.float64
            assert np.array_equal(initial_users, world.user_positions)
            assert np.array_equal(initial_uavs, world.uav_positions[: cell["test_n"]])
            seen.setdefault((row["world_id"], cell["test_n"]), []).append(
                (initial_users, initial_uavs)
            )

    # Every arm/capacity realization of a given world and roster has identical
    # initial physical geometry; roster changes retain the declared UAV prefix.
    for rows in seen.values():
        assert all(np.array_equal(rows[0][0], users) for users, _uavs in rows[1:])
        assert all(np.array_equal(rows[0][1], uavs) for _users, uavs in rows[1:])


def test_output_reduction_keeps_world_differences_and_component_decompositions(completed_probe):
    _out, summary, _elapsed = completed_probe
    aggregates = summary["aggregates"]
    assert aggregates["world_ids"] == [0]
    assert set(aggregates["gaps"]) == {
        "N4_c10",
        "N4_c20",
        "N8_c5",
        "N8_c10",
        "N6_c10",
    }
    assert set(aggregates["D_N"]) == {"4", "8"}
    assert set(aggregates["D_N"]["4"]) == {"D", "component_D"}
    assert set(aggregates["matched_total_capacity_cross_N_residual"]) == {"40", "80"}
    assert set(aggregates["same_c10_secondary_contrast"]) == {
        "N6_minus_N4",
        "N8_minus_N6",
        "N8_minus_N4",
    }
    for gap in aggregates["gaps"].values():
        value = gap["H6_minus_SET"]["values"][0]
        parts = gap["component_gaps"]
        expected = (
            0.7 * parts["coverage_reward"]["values"][0]
            + 0.3 * parts["quality_reward"]["values"][0]
            - parts["energy_penalty"]["values"][0]
        )
        assert value == pytest.approx(expected, rel=1e-6, abs=1e-7)


def _copied_sources(tmp_path: Path, source_fixture):
    repository = tmp_path / "repository"
    checkpoints = tmp_path / "checkpoints"
    shutil.copytree(source_fixture["repository"], repository)
    shutil.copytree(source_fixture["checkpoints"], checkpoints)
    return repository, repository / "runs" / probe.SOURCE_DIRECTION, checkpoints


def test_source_summary_must_be_complete_committed_and_worktree_identical(tmp_path, source_fixture):
    repository, summaries, checkpoints = _copied_sources(tmp_path, source_fixture)
    arm, seed, tag = probe.SOURCE_POLICIES[0]
    path = summaries / tag / "summary.json"
    summary = json.loads(path.read_text())
    summary["status"] = "failed"
    path.write_text(json.dumps(summary, indent=2) + "\n")
    with pytest.raises(ValueError, match="working bytes differ"):
        probe.load_source_policy(
            checkpoints,
            probe.SourcePolicy(arm, seed, tag),
            tracked_summary_root=summaries,
            repository_root=repository,
        )
    _commit(repository, "incomplete")
    with pytest.raises(ValueError, match="status mismatch"):
        probe.load_source_policy(
            checkpoints,
            probe.SourcePolicy(arm, seed, tag),
            tracked_summary_root=summaries,
            repository_root=repository,
        )


def test_checkpoint_digest_payload_and_reconstructed_config_fail_closed(tmp_path, source_fixture):
    repository, summaries, checkpoints = _copied_sources(tmp_path, source_fixture)
    arm, seed, tag = probe.SOURCE_POLICIES[0]
    checkpoint = checkpoints / tag / "checkpoint_45.pt"
    with checkpoint.open("ab") as stream:
        stream.write(b"tamper")
    with pytest.raises(ValueError, match="byte-size mismatch"):
        probe.load_source_policy(
            checkpoints,
            probe.SourcePolicy(arm, seed, tag),
            tracked_summary_root=summaries,
            repository_root=repository,
        )

    shutil.rmtree(checkpoints)
    shutil.copytree(source_fixture["checkpoints"], checkpoints)
    summary_path = summaries / tag / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["panels"][-3]["config"]["num_envs"] = 15
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    _commit(repository, "bad panel config")
    record = probe.load_source_policy(
        checkpoints,
        probe.SourcePolicy(arm, seed, tag),
        tracked_summary_root=summaries,
        repository_root=repository,
    )
    out = tmp_path / "bad-config-out"
    out.mkdir()
    with pytest.raises(ValueError, match="differs from final N=4 panel"):
        probe.evaluate_cell(
            record,
            4,
            10,
            out,
            replace(TECH_PROBE_SPEC, cells=((4, 10),)),
            progress=lambda *_: None,
        )

    record["payload"]["modules"].pop(next(iter(record["payload"]["modules"])))
    with pytest.raises(ValueError, match="module set mismatch"):
        probe.evaluate_cell(
            record,
            6,
            10,
            out,
            replace(TECH_PROBE_SPEC, cells=((6, 10),)),
            progress=lambda *_: None,
        )


def test_checkpoint_payload_schema_refuses_even_with_updated_external_digest(
    tmp_path, source_fixture
):
    repository, summaries, checkpoints = _copied_sources(tmp_path, source_fixture)
    arm, seed, tag = probe.SOURCE_POLICIES[1]
    checkpoint = checkpoints / tag / "checkpoint_45.pt"
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    payload.pop("usage")
    torch.save(payload, checkpoint)
    summary_path = summaries / tag / "summary.json"
    summary = json.loads(summary_path.read_text())
    record = next(row for row in summary["checkpoints"] if row["path"] == "checkpoint_45.pt")
    record["bytes"] = checkpoint.stat().st_size
    record["sha256"] = probe.file_sha256(checkpoint)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    _commit(repository, "payload schema attack")
    with pytest.raises(ValueError, match="payload schema"):
        probe.load_source_policy(
            checkpoints,
            probe.SourcePolicy(arm, seed, tag),
            tracked_summary_root=summaries,
            repository_root=repository,
        )


def test_restored_model_digest_must_match_completed_source(tmp_path, source_fixture):
    repository, summaries, checkpoints = _copied_sources(tmp_path, source_fixture)
    arm, seed, tag = probe.SOURCE_POLICIES[0]
    summary_path = summaries / tag / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["final_parameter_normalizer_digest"] = "0" * 64
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    _commit(repository, "wrong final digest")
    record = probe.load_source_policy(
        checkpoints,
        probe.SourcePolicy(arm, seed, tag),
        tracked_summary_root=summaries,
        repository_root=repository,
    )
    out = tmp_path / "digest-out"
    out.mkdir()
    with pytest.raises(ValueError, match="restored model/normalizer digest"):
        probe.evaluate_cell(
            record,
            4,
            10,
            out,
            replace(TECH_PROBE_SPEC, cells=((4, 10),)),
            progress=lambda *_: None,
        )


def test_injected_post_step_failure_retains_count_and_partial_trace(tmp_path, source_fixture):
    out = tmp_path / "partial-attempt"
    out.mkdir()

    def fail_after_third(event):
        if event["steps_completed"] == 3:
            raise RuntimeError("injected post-step diagnostic boundary")

    assert probe.run_probe_impl(
        out,
        source_fixture["checkpoints"],
        "technical-fixture",
        {"sha": "technical-fixture"},
        TECH_PROBE_SPEC,
        tracked_summary_root=source_fixture["summaries"],
        repository_root=source_fixture["repository"],
        after_step=fail_after_third,
    ) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["counts"]["evaluation_team_steps"] == 3
    assert summary["counts"]["evaluation_episodes"] == 0
    assert summary["cells"][0]["steps"] == 3
    assert summary["cells"][0]["status"] == "failed"
    assert "injected post-step" in summary["cells"][0]["failure"]
    partial = summary["cells"][0]["worlds"][0]
    assert partial["status"] == "failed" and partial["steps"] == 3
    trace = probe._load_trace(out, partial["trace"])
    assert trace["raw_actions"].shape[0] == 3
    assert trace["scalar_reward"].shape[0] == 2
    assert "injected post-step" in summary["failure"]


def test_world_two_failure_retains_completed_world_count(tmp_path, source_fixture):
    out = tmp_path / "world-two-failure"
    out.mkdir()

    def fail_in_second_world(event):
        if event["world_id"] == 1 and event["steps_completed"] == 1:
            raise RuntimeError("injected world-two failure")

    assert probe.run_probe_impl(
        out,
        source_fixture["checkpoints"],
        "technical-fixture",
        {"sha": "technical-fixture"},
        replace(TWO_WORLD_SPEC, cells=((4, 10),)),
        tracked_summary_root=source_fixture["summaries"],
        repository_root=source_fixture["repository"],
        after_step=fail_in_second_world,
    ) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["counts"]["evaluation_team_steps"] == 3
    assert summary["counts"]["evaluation_episodes"] == 1
    assert summary["counts"]["completed_worlds"] == 1
    cell = summary["cells"][0]
    assert cell["status"] == "failed"
    assert "injected world-two failure" in cell["failure"]
    assert [row["status"] for row in cell["worlds"]] == ["complete", "failed"]
    assert cell["worlds"][0]["episode_complete"] is True
    assert cell["worlds"][1]["episode_complete"] is False


def test_failure_after_terminal_step_preserves_native_episode_count(tmp_path, source_fixture):
    out = tmp_path / "terminal-step-failure"
    out.mkdir()

    def fail_after_terminal(event):
        assert event["terminal_observed"] is True
        raise RuntimeError("injected after terminal")

    assert probe.run_probe_impl(
        out,
        source_fixture["checkpoints"],
        "technical-fixture",
        {"sha": "technical-fixture"},
        replace(TECH_PROBE_SPEC, cells=((4, 10),), horizon=1),
        tracked_summary_root=source_fixture["summaries"],
        repository_root=source_fixture["repository"],
        after_step=fail_after_terminal,
    ) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["counts"]["evaluation_team_steps"] == 1
    assert summary["counts"]["evaluation_episodes"] == 1
    assert summary["counts"]["completed_worlds"] == 0
    cell = summary["cells"][0]
    assert cell["status"] == "failed"
    world = cell["worlds"][0]
    assert world["status"] == "failed"
    assert world["steps"] == 1
    assert world["episode_complete"] is True
    assert world["native_terminal_observed"] is True
    trace = probe._load_trace(out, world["trace"])
    assert trace["raw_actions"].shape[0] == 1
    assert trace["scalar_reward"].shape[0] == 0


def test_entry_refuses_before_import_or_output_when_admission_fails(tmp_path, monkeypatch):
    calls = []

    def refuse(*_args, **_kwargs):
        calls.append("admission")
        raise RuntimeError("not admitted")

    monkeypatch.setattr(entry, "require_admission", refuse)
    out = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="not admitted"):
        entry.main(
            [
                "--out",
                str(out),
                "--checkpoint-root",
                str(tmp_path / "checkpoints"),
                "--launch-sha",
                "sha",
            ]
        )
    assert calls == ["admission"]
    assert not out.exists()


def test_entry_matches_source_preimport_thread_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "require_admission", lambda *_args, **_kwargs: {"sha": "sha"})
    captured = {}

    def fake_run(*_args, **_kwargs):
        captured.update(
            {
                name: entry.os.environ[name]
                for name in (
                    "OMP_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            }
        )
        return 0

    monkeypatch.setattr(probe, "run_probe", fake_run)
    assert entry.main(
        [
            "--out",
            str(tmp_path / "out"),
            "--checkpoint-root",
            str(tmp_path / "checkpoints"),
            "--launch-sha",
            "sha",
        ]
    ) == 0
    assert set(captured.values()) == {"1"}


def test_identity_reasons_are_not_truncated_to_runtime_digest_width():
    reason = json.dumps(["x" * 100, "y" * 100])
    trace = probe._trace_from_lists(
        {"identity_reasons": [reason], "runtime_before_action": ["a" * 64]}
    )
    assert trace["identity_reasons"][0] == reason
    assert trace["identity_reasons"].dtype.itemsize > 64 * 4
    assert trace["runtime_before_action"].dtype.itemsize == 64 * 4


def test_existing_scientific_outputs_refuse_but_launcher_controls_are_allowed(tmp_path):
    out = tmp_path / "attempt"
    out.mkdir()
    (out / "launch-manifest.json").write_text("{}\n")
    probe._refuse_existing_scientific_outputs(out)
    (out / "trace_old.npz").write_bytes(b"old")
    with pytest.raises(ValueError, match="existing scientific outputs"):
        probe._refuse_existing_scientific_outputs(out)

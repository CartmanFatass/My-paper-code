from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import scripts.audit_r27_forced_trajectory_effect as cli
from ha_ctse_process import r27_g2_analysis as analysis
from ha_ctse_process.r27_g2_collector import (
    R27G2ResetArtifact,
    build_branch_specs,
)


def test_collect_parser_exposes_only_registered_single_reset_contract():
    args = cli.parse_args(
        [
            "collect-reset",
            "--checkpoint",
            cli.REGISTERED_CHECKPOINTS["arm0_final"]["path"],
            "--checkpoint-id",
            "arm0_final",
            "--checkpoint-update",
            "32",
            "--reset-id",
            "63",
            "--output-dir",
            "logs/r27_fixture",
        ]
    )

    assert args.command == "collect-reset"
    assert args.device == "cuda"
    assert args.n_agents == 6
    assert args.scenario == "energy"
    assert args.preset == "S7-S1"
    assert args.reset_id == 63


def test_scientific_contract_binds_exact_checkpoints_and_budget():
    assert tuple(cli.REGISTERED_CHECKPOINTS) == (
        "arm0_update25",
        "arm0_update30",
        "arm0_final",
    )
    assert cli.SCIENTIFIC_CONTRACT["environment_steps_per_checkpoint"] == 708000
    assert cli.SCIENTIFIC_CONTRACT["environment_steps_total"] == 2124000
    assert cli.SCIENTIFIC_CONTRACT["branches_per_reset"] == 55
    assert cli.SCIENTIFIC_CONTRACT["duration_candidates"] == [1, 2, 3, 4]
    assert cli.SCIENTIFIC_CONTRACT["default_reset_worker_limit"] == 64
    assert cli.SCIENTIFIC_CONTRACT["allowed_reset_worker_limit"] == [2, 64]
    assert cli.SCIENTIFIC_CONTRACT["checkpoint_slots"] == cli.REGISTERED_CHECKPOINTS


def test_registered_checkpoint_path_accepts_data_disk_cache_suffix():
    registered = cli.REGISTERED_CHECKPOINTS["arm0_final"]["path"]
    remote = "/root/autodl-tmp/HMASD/checkpoint_dist/" + registered.removeprefix(
        "dist/"
    )
    assert cli._path_matches_registered(remote, registered)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("device", "cpu", "device must equal"),
        ("reset_id", 64, "reset-id must be"),
        ("checkpoint_update", 31, "checkpoint update"),
        ("scenario", "base", "scenario must equal"),
    ],
)
def test_collect_validation_fails_closed_before_runtime(field, value, message):
    registered = cli.REGISTERED_CHECKPOINTS["arm0_final"]
    args = SimpleNamespace(
        checkpoint=registered["path"],
        checkpoint_id="arm0_final",
        checkpoint_update=registered["update"],
        reset_id=0,
        config="ha_ctse_process.config",
        scenario="energy",
        preset="S7-S1",
        n_agents=6,
        device="cuda",
    )
    setattr(args, field, value)

    with pytest.raises((ValueError, RuntimeError), match=message):
        cli.validate_collect_args(args)


def test_aggregate_parser_requires_explicit_checkpoint_order():
    args = cli.parse_args(
        [
            "aggregate",
            "--run-root",
            "logs/r27_g2_fixture",
            "--checkpoint-ids",
            *cli.CHECKPOINT_IDS,
        ]
    )
    assert tuple(args.checkpoint_ids) == cli.CHECKPOINT_IDS


def test_validate_run_rechecks_every_reset_before_aggregate(monkeypatch):
    reset_calls = []

    def fake_validate_reset(args):
        reset_calls.append((args.checkpoint_id, args.reset_id, args.manifest))
        return {"scientific_status": "OK"}

    aggregate_calls = []
    rebuild_calls = []

    def fake_rebuild(args):
        rebuild_calls.append((args.run_root, tuple(args.checkpoint_ids)))
        return {"status": "FAIL"}

    def fake_validate_aggregate(args):
        aggregate_calls.append(args.run_root)
        return {
            "scientific_status": "FAIL",
            "classification": "FAIL_BEHAVIOR_FAMILY",
            "json": f"{args.run_root}/report.json",
            "markdown": f"{args.run_root}/report.md",
        }

    monkeypatch.setattr(cli, "run_validate_reset", fake_validate_reset)
    monkeypatch.setattr(cli, "run_aggregate", fake_rebuild)
    monkeypatch.setattr(cli, "run_validate_aggregate", fake_validate_aggregate)

    result = cli.run_validate_run(SimpleNamespace(run_root="logs/r27_fixture"))

    assert len(reset_calls) == 3 * 64
    assert reset_calls[0][:2] == ("arm0_update25", 0)
    assert reset_calls[-1][:2] == ("arm0_final", 63)
    assert len(rebuild_calls) == 1
    assert Path(rebuild_calls[0][0]) == Path("logs/r27_fixture")
    assert rebuild_calls[0][1] == cli.CHECKPOINT_IDS
    assert len(aggregate_calls) == 1
    assert Path(aggregate_calls[0]) == Path("logs/r27_fixture")
    assert result["valid"] is True
    assert result["validated_resets"] == 192
    assert result["reset_status_counts"] == {
        "OK": 192,
        "EXCLUDED": 0,
        "INVALID": 0,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("checkpoint_path", "wrong/location.pt", "checkpoint path mismatch"),
        ("checkpoint_file_nonempty", False, "missing or empty"),
    ],
)
def test_validate_reset_requires_registered_nonempty_checkpoint_slot(
    tmp_path, field, value, message
):
    checkpoint_id = "arm0_final"
    registered = cli.REGISTERED_CHECKPOINTS[checkpoint_id]
    manifest = {
        "status": "INVALID",
        "invalid_reasons": ["fixture invalid"],
        "excluded_reason": None,
        "artifact": None,
        "reset_id": 0,
        "checkpoint_id": checkpoint_id,
        "checkpoint_update": registered["update"],
        "checkpoint_path": registered["path"],
        "checkpoint_file_nonempty": True,
        "device": "cuda",
        "scientific_contract": cli.SCIENTIFIC_CONTRACT,
    }
    manifest[field] = value
    manifest_path = tmp_path / "reset_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(cli.R27G2ContractError, match=message):
        cli.run_validate_reset(
            SimpleNamespace(
                manifest=str(manifest_path),
                checkpoint_id=checkpoint_id,
                reset_id=0,
            )
        )


def test_validate_aggregate_requires_complete_inventory_and_exact_markdown(
    tmp_path,
):
    run_root = tmp_path / "run"
    manifest_paths = []
    for checkpoint_id in cli.CHECKPOINT_IDS:
        for reset_id in range(64):
            manifest_path = (
                run_root
                / checkpoint_id
                / "resets"
                / f"reset_{reset_id:02d}"
                / "reset_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "status": "INVALID",
                        "artifact": None,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_paths.append(manifest_path)
    count = cli._validate_reset_inventory(run_root)
    report = {
        "status": "FAIL",
        "classification": "FAIL_BEHAVIOR_FAMILY",
        "scientific_contract": cli.SCIENTIFIC_CONTRACT,
        "checkpoints": [
            {"checkpoint_id": checkpoint_id} for checkpoint_id in cli.CHECKPOINT_IDS
        ],
        "reset_evidence_count": count,
    }
    json_path = run_root / "r27_g2_forced_trajectory_effect.json"
    markdown_path = run_root / "r27_g2_forced_trajectory_effect.md"

    def write_report(value):
        json_path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        markdown_path.write_text(cli._markdown(value), encoding="utf-8")

    write_report(report)
    result = cli.run_validate_aggregate(SimpleNamespace(run_root=str(run_root)))
    assert result["valid"] is True

    markdown_path.write_text("nonempty but stale\n", encoding="utf-8")
    with pytest.raises(cli.R27G2ContractError, match="does not match JSON"):
        cli.run_validate_aggregate(SimpleNamespace(run_root=str(run_root)))

    invalid_pair = dict(report, status="PASS")
    write_report(invalid_pair)
    with pytest.raises(cli.R27G2ContractError, match="combination is invalid"):
        cli.run_validate_aggregate(SimpleNamespace(run_root=str(run_root)))

    write_report(report)
    extra_manifest = (
        run_root
        / cli.CHECKPOINT_IDS[0]
        / "resets"
        / "reset_99"
        / "reset_manifest.json"
    )
    extra_manifest.parent.mkdir(parents=True, exist_ok=True)
    extra_manifest.write_text("{}\n", encoding="utf-8")
    with pytest.raises(cli.R27G2ContractError, match="inventory/path mismatch"):
        cli.run_validate_aggregate(SimpleNamespace(run_root=str(run_root)))


def make_adapter_fixture():
    checkpoint_id = "arm0_final"
    registered = cli.REGISTERED_CHECKPOINTS[checkpoint_id]
    roster = np.array([0, 1, 2, 3, 0, 1], dtype=np.int64)
    base = R27G2ResetArtifact.allocate(
        reset_id=0,
        prefix_steps=50,
        obs_dim=7,
        hidden_dim=3,
        state_dim=9,
        branches=build_branch_specs(roster),
    )
    base.prefix_skill[:] = roster
    base.branch_completed[:] = True
    base.step_valid[:] = True
    base.runtime_restored_equal[:] = True
    base.replay_global_rng_equal[:] = True
    base.replay_info_equal[:] = True
    base.replay_environment_equal[:] = True
    base.replay_environment_rng_equal[:] = True
    base.frozen_runtime_unchanged[:] = True
    base.environment_rng_equal_reference[:] = True
    base.identity_actor_equal[:] = True
    base.identity_critic_equal[:] = True
    base.identity_info_equal[:] = True
    base.identity_environment_equal[:] = True
    base.module_state_equal[...] = True
    base.value_norm_state_equal[...] = True
    base.global_rng_unchanged[:] = True
    artifacts = []
    manifests = []
    for reset_id in range(64):
        artifact = copy.copy(base)
        artifact.reset_id = np.asarray(reset_id, dtype=np.int64)
        artifact.reset_seed = np.asarray(reset_id + 1, dtype=np.int64)
        artifacts.append(artifact)
        manifests.append(
            {
                "status": "OK",
                "invalid_reasons": [],
                "excluded_reason": None,
                "calibration_complete": True,
                "reset_id": reset_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_update": registered["update"],
                "checkpoint_path": registered["path"],
                "checkpoint_file_nonempty": True,
                "module_state_equal": True,
                "value_norm_state_equal": True,
                "loaded_value_norm_equal": True,
                "device": "cuda",
                "scientific_contract": cli.SCIENTIFIC_CONTRACT,
            }
        )
    return checkpoint_id, artifacts, manifests


def test_raw_artifact_adapter_builds_frozen_gate_shapes_and_support():
    checkpoint_id, artifacts, manifests = make_adapter_fixture()
    typed, calibration, descriptive = cli._derive_checkpoint_analysis_input(
        checkpoint_id, artifacts, manifests
    )

    assert typed.validity.passed
    assert typed.gate_a.active_pair_skl.shape == (64, 6, 6)
    assert typed.gate_b1.active_pair_skl.shape == (64, 6, 4, 50, 6)
    assert typed.gate_b2.d_hold.shape == (64, 6, 3)
    assert typed.gate_b3.features.shape == (64, 6, 4, 12)
    assert typed.gate_c.e_hold.shape == (64, 6, 3)
    assert typed.support.hold_cell_present.all()
    assert typed.support.pair_contrast_present.all()
    assert calibration["rows"] == 19200
    assert calibration["ddof"] == 0
    assert calibration["standard_deviation_floor"] == 1e-3
    assert descriptive["available"]
    assert set(descriptive["focal_local_observation_effect"]) == {
        "H20",
        "H40",
        "H50",
    }


def test_raw_artifact_adapter_preserves_invalid_precedence():
    checkpoint_id, artifacts, manifests = make_adapter_fixture()
    manifests[7] = dict(manifests[7])
    manifests[7]["status"] = "INVALID"
    manifests[7]["invalid_reasons"] = ["fixture parity failure"]

    typed, _calibration, descriptive = cli._derive_checkpoint_analysis_input(
        checkpoint_id, artifacts, manifests
    )

    assert not typed.validity.passed
    assert any("fixture parity failure" in item for item in typed.validity.failures)
    assert descriptive["available"] is False
    result = analysis.analyze_checkpoint(typed, bootstrap_reps=10)
    assert result.decision.status == "INVALID"


def test_excluded_status_requires_exact_recorded_event():
    checkpoint_id, artifacts, manifests = make_adapter_fixture()
    artifact = copy.deepcopy(artifacts[3])
    manifest = dict(manifests[3])
    manifest["status"] = "EXCLUDED"
    manifest["excluded_reason"] = "branch=2 step=5 terminated=True truncated=False focal_failure=False"
    artifact.step_valid[:] = False
    artifact.step_valid[:2] = True
    artifact.step_valid[2, :5] = True
    artifact.branch_completed[:] = False
    artifact.branch_completed[:2] = True
    artifact.terminated[2, 4] = True
    artifacts[3] = artifact
    manifests[3] = manifest

    typed, _calibration, _descriptive = cli._derive_checkpoint_analysis_input(
        checkpoint_id, artifacts, manifests
    )
    assert typed.validity.passed
    assert typed.support.reset_ids.size == 63

    malformed = dict(manifest)
    malformed["excluded_reason"] = "fixture without matching event"
    failures = cli._status_evidence_failures(
        malformed, artifact, context="reset 3"
    )
    assert any("reason/event mismatch" in item for item in failures)


def test_all_excluded_support_reports_zero_not_placeholder_one():
    checkpoint_id, artifacts, manifests = make_adapter_fixture()
    for reset_id in range(64):
        artifact = copy.copy(artifacts[reset_id])
        artifact.step_valid = np.zeros_like(artifact.step_valid)
        artifact.step_valid[0, 0] = True
        artifact.branch_completed = np.zeros_like(artifact.branch_completed)
        artifact.terminated = np.zeros_like(artifact.terminated)
        artifact.terminated[0, 0] = True
        artifacts[reset_id] = artifact
        manifests[reset_id] = dict(manifests[reset_id])
        manifests[reset_id]["status"] = "EXCLUDED"
        manifests[reset_id]["excluded_reason"] = (
            "branch=0 step=1 terminated=True truncated=False focal_failure=False"
        )

    typed, _calibration, _descriptive = cli._derive_checkpoint_analysis_input(
        checkpoint_id, artifacts, manifests
    )
    assert typed.support.reset_ids.size == 0
    assert typed.support.hold_cell_present.shape == (0, 6, 4)
    result = analysis.analyze_checkpoint(typed, bootstrap_reps=10)
    assert result.support.valid_resets == 0
    assert result.decision.status == "UNDERPOWERED"


def test_all_invalid_precedes_zero_support_underpowered():
    checkpoint_id, artifacts, manifests = make_adapter_fixture()
    for reset_id in range(64):
        manifests[reset_id] = dict(manifests[reset_id])
        manifests[reset_id]["status"] = "INVALID"
        manifests[reset_id]["invalid_reasons"] = ["fixture invalid evidence"]

    typed, _calibration, descriptive = cli._derive_checkpoint_analysis_input(
        checkpoint_id, artifacts, manifests
    )
    result = analysis.analyze_checkpoint(typed, bootstrap_reps=10)
    assert result.support.valid_resets == 0
    assert result.decision.status == "INVALID"
    assert descriptive["available"] is False

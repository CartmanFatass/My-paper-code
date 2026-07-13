from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.analyze_r28_g1_family import (
    FamilyEvidenceError,
    FamilyUnderpoweredError,
    NON_R28_ALGORITHM_FALSE,
    NON_R28_ALGORITHM_MODES,
    NON_R28_ALGORITHM_ZERO,
    NON_R28_ARG_FALSE,
    NON_R28_TRAINING_FALSE,
    NON_R28_TRAINING_ZERO,
    SEEDS,
    _pooled_cluster_mean,
    _r26_delta,
    final_task_summary,
    normalized_run_manifest,
    r26_cluster_rows,
    training_guard_summary,
    validate_disabled_reward_contract,
    validate_execution_contract,
)
from ha_ctse_process.r28_g1_reward import ARMS, FINAL_CHECKPOINT_PATH


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_status(path: Path, **fields: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{name}={value}\n" for name, value in fields.items()),
        encoding="utf-8",
    )


def _execution_contract(tmp_path: Path) -> tuple[Path, Path]:
    run_root = tmp_path / "run"
    scorer_path = tmp_path / "r28_g0_scorer_final.pt"
    marker_path = run_root / "topology" / "topology_passed.json"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        json.dumps(
            {
                "status": "PASS",
                "device": "cuda",
                "source_checkpoint": tmp_path / FINAL_CHECKPOINT_PATH,
                "scorer_path": str(scorer_path),
                "arms": list(ARMS),
                "concurrent_workers": 3,
                "num_envs_per_worker": 16,
                "rollout_length": 500,
                "topology_total_timesteps": 1_008_000,
                "measured_batch_seconds": 10,
                "projected_training_hours": 2.0,
                "revised_end_to_end_hours": [6.0, 10.0],
                "serial_fallback": False,
            },
            default=str,
        ),
        encoding="utf-8",
    )
    _write_status(
        run_root / "topology" / "runner_status.txt",
        state="succeeded",
        phase="topology",
        concurrent_workers=3,
        measured_batch_seconds=10,
        topology_marker=marker_path,
        device="cuda",
    )
    _write_status(
        run_root / "run_status.txt",
        state="succeeded",
        phase="run",
        completed_runs=9,
        concurrent_arms=3,
        total_timesteps=1_160_000,
    )
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = run_root / "runs" / arm / f"seed{seed}"
            _write_status(
                run_dir / "runner_status.txt",
                state="succeeded",
                phase="run",
                arm=arm,
                seed=seed,
                device="cuda",
                total_timesteps=1_160_000,
                final_checkpoint=run_dir / "standalone_process_core_final.pt",
                exit_code=0,
            )
    return run_root, scorer_path


def _disabled_reward_evidence() -> tuple[dict[str, object], dict[str, object]]:
    algorithm: dict[str, object] = {
        **{name: False for name in NON_R28_ALGORITHM_FALSE},
        **{name: 0.0 for name in NON_R28_ALGORITHM_ZERO},
        **NON_R28_ALGORITHM_MODES,
    }
    training: dict[str, object] = {
        **{name: False for name in NON_R28_TRAINING_FALSE},
        **{name: 0.0 for name in NON_R28_TRAINING_ZERO},
    }
    args: dict[str, object] = {
        **{name: False for name in NON_R28_ARG_FALSE},
        "p2_recovery_reward_coef": None,
        "assignment_actionability_coef": None,
    }
    manifest: dict[str, object] = {
        "args": args,
        "algorithm_config": algorithm,
        "training_config": training,
        "model_config": {},
        "physical_env_config": {},
        "env_runtime_spec": {},
        "agent_runtime_spec": {},
    }
    checkpoint: dict[str, object] = {
        "enable_prototype_disc_reward": False,
        "enable_team_disc_reward": False,
        "enable_team_transition_reward": False,
        "enable_assignment_actionability_reward": False,
        "z_entropy_floor_enabled": False,
        "team_disc_coef": 0.0,
        "team_transition_coef": 0.0,
        "assignment_actionability_coef": 0.0,
        "z_entropy_floor_coef": 0.0,
    }
    return manifest, checkpoint


def _training_rows() -> list[dict[str, object]]:
    return [
        {
            "update": update,
            "total_steps": 1_000_000 + 8_000 * (update - 32),
            "r28_g1_active": 1,
            "r28_g1_arm_code": 0,
            "r28_g1_reward_applied_steps": 0,
            "r28_g1_support_kill_switch_event": 0,
            "r28_g1_ratio_kill_switch_event": 0,
            "r28_g1_reward_env_ratio": 0.01,
        }
        for update in range(33, 53)
    ]


def test_r26_delta_selects_best_control_within_each_cluster() -> None:
    rows = [
        {"real_reward": 0.5, "probe_only": 0.4, "sham_reward": 0.0},
        {"real_reward": 0.5, "probe_only": 0.0, "sham_reward": 0.4},
    ]
    assert _r26_delta(rows) == pytest.approx(0.1)


def test_pooled_sidecar_statistic_weights_clusters_by_row_count() -> None:
    rows = [
        {"s_real_sum": 10.0, "count": 10.0},
        {"s_real_sum": 0.0, "count": 1.0},
    ]
    assert _pooled_cluster_mean(rows, "s_real_sum") == pytest.approx(10.0 / 11.0)


def test_training_guard_requires_exact_exposure_and_columns(tmp_path: Path) -> None:
    path = tmp_path / "run" / "metrics" / "train_updates.csv"
    rows = _training_rows()
    _write_csv(path, rows)
    summary = training_guard_summary(tmp_path / "run", arm="probe_only")
    assert summary["updates"] == 20.0
    assert summary["final_total_steps"] == 1_160_000.0

    _write_csv(path, rows[:-1])
    with pytest.raises(FamilyEvidenceError, match="update/step exposure"):
        training_guard_summary(tmp_path / "run", arm="probe_only")

    missing = _training_rows()
    for row in missing:
        del row["r28_g1_support_kill_switch_event"]
    _write_csv(path, missing)
    with pytest.raises(FamilyEvidenceError, match="required CSV field"):
        training_guard_summary(tmp_path / "run", arm="probe_only")


def test_r26_invalid_and_underpowered_never_enter_bootstrap() -> None:
    invalid = {
        ("probe_only", 28031): {
            "valid": True,
            "gate": {"status": "INVALID"},
            "heldout_row_correctness": [
                {"reset_id": 0, "full_correct": True, "prior_correct": False}
            ],
        }
    }
    with pytest.raises(FamilyEvidenceError, match="invalid"):
        r26_cluster_rows(invalid)

    underpowered = {
        ("probe_only", 28031): {
            "valid": True,
            "underpowered": True,
            "gate": {"status": "UNDERPOWERED"},
        }
    }
    with pytest.raises(FamilyUnderpoweredError, match="underpowered"):
        r26_cluster_rows(underpowered)


def test_final_task_summary_requires_both_complete_evaluations(tmp_path: Path) -> None:
    rows = []
    for step in (1_080_000, 1_160_000):
        for episode in range(20):
            rows.append(
                {
                    "total_steps": step,
                    "episode": episode,
                    "action_mode_code": 0,
                    "reward": 1.0,
                    "zero_throughput_episode_flag": 0.0,
                }
            )
    path = tmp_path / "run" / "metrics" / "eval_episodes.csv"
    _write_csv(path, rows)
    assert final_task_summary(tmp_path / "run")["total_steps"] == 1_160_000.0

    _write_csv(path, rows[:20])
    with pytest.raises(FamilyEvidenceError, match="evaluations are not exactly"):
        final_task_summary(tmp_path / "run")

    missing = [
        {key: value for key, value in row.items() if key != "zero_throughput_episode_flag"}
        for row in rows
    ]
    _write_csv(path, missing)
    with pytest.raises(FamilyEvidenceError, match="required CSV field"):
        final_task_summary(tmp_path / "run")


def test_execution_contract_requires_topology_and_concurrent_batch_status(
    tmp_path: Path,
) -> None:
    run_root, scorer_path = _execution_contract(tmp_path)
    validate_execution_contract(run_root, scorer_path)

    _write_status(
        run_root / "run_status.txt",
        state="succeeded",
        phase="run",
        completed_runs=9,
        concurrent_arms=2,
        total_timesteps=1_160_000,
    )
    with pytest.raises(FamilyEvidenceError, match="concurrent_arms"):
        validate_execution_contract(run_root, scorer_path)


def test_execution_contract_rejects_serial_topology_marker(tmp_path: Path) -> None:
    run_root, scorer_path = _execution_contract(tmp_path)
    marker_path = run_root / "topology" / "topology_passed.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["serial_fallback"] = True
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    with pytest.raises(FamilyEvidenceError, match="serial_fallback"):
        validate_execution_contract(run_root, scorer_path)


def test_normalized_manifest_allows_only_registered_identity_paths() -> None:
    manifest, _checkpoint = _disabled_reward_evidence()
    manifest.update({"mode": "train", "total_steps": 1_160_000, "update_idx": 52})
    args = manifest["args"]
    assert isinstance(args, dict)
    args.update(
        {
            "seed": 28031,
            "r28_g1_arm": "probe_only",
            "log_dir": "/data/run/probe_only/seed28031",
            "r24_qd_export_dir": "/data/run/probe_only/seed28031/r24_qd_windows",
        }
    )
    algorithm = manifest["algorithm_config"]
    training = manifest["training_config"]
    model = manifest["model_config"]
    assert isinstance(algorithm, dict) and isinstance(training, dict) and isinstance(model, dict)
    algorithm["r24_qd_export_dir"] = "/data/run/probe_only/seed28031/r24_qd_windows"
    training["r28_g1_arm"] = "probe_only"
    model["hidden_size"] = 256

    other = json.loads(json.dumps(manifest))
    other["args"]["seed"] = 28032
    other["args"]["r28_g1_arm"] = "real_reward"
    other["args"]["log_dir"] = "/data/run/real_reward/seed28032"
    other["args"]["r24_qd_export_dir"] = "/data/run/real_reward/seed28032/r24_qd_windows"
    other["algorithm_config"]["r24_qd_export_dir"] = (
        "/data/run/real_reward/seed28032/r24_qd_windows"
    )
    other["training_config"]["r28_g1_arm"] = "real_reward"
    assert normalized_run_manifest(manifest) == normalized_run_manifest(other)

    other["model_config"]["hidden_size"] = 128
    assert normalized_run_manifest(manifest) != normalized_run_manifest(other)


def test_disabled_reward_contract_is_explicit_and_fail_closed() -> None:
    manifest, checkpoint = _disabled_reward_evidence()
    validate_disabled_reward_contract(manifest, checkpoint, label="test")

    algorithm = manifest["algorithm_config"]
    assert isinstance(algorithm, dict)
    algorithm["team_disc_coef"] = 0.01
    with pytest.raises(FamilyEvidenceError, match="team_disc_coef"):
        validate_disabled_reward_contract(manifest, checkpoint, label="test")

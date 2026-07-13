"""Collect and read the R28 forced-execution support transport probe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.r27_g2_collector import (  # noqa: E402
    N_SKILLS,
    prefix_steps_for_reset,
)
from ha_ctse_process.r27_g2_runtime import (  # noqa: E402
    R27G2ContractError,
    configure_deterministic_cuda,
)
from ha_ctse_process.r28_g1_reward import (  # noqa: E402
    DURATION_STEPS,
    FrozenR28G1Reward,
    OOD_KILL_FRACTION,
    SUPPORT_FEATURE_NAMES,
)
from ha_ctse_process.r28_support_transport import (  # noqa: E402
    EXPERIMENT_ID,
    MODES,
    R28SupportTransportArtifact,
    SCHEMA,
    collect_support_transport_reset,
)
from scripts.audit_r27_forced_trajectory_effect import (  # noqa: E402
    REGISTERED_CHECKPOINTS,
    _configure_agent,
    _path_matches_registered,
)


FINAL_CHECKPOINT_ID = "arm0_final"
FINAL_SLOT = REGISTERED_CHECKPOINTS[FINAL_CHECKPOINT_ID]
RESET_IDS = tuple(range(64))
MIN_PAIRED_PER_CELL = 48


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--scorer", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--preset", default="S7-S1")
    parser.add_argument("--n-agents", dest="n_agents", type=int, default=6)
    parser.add_argument("--device", default="cuda")


def _validate_source(args: argparse.Namespace) -> None:
    if str(args.device).lower() != "cuda":
        raise ValueError("R28 support transport requires CUDA")
    if not _path_matches_registered(args.checkpoint, FINAL_SLOT["path"]):
        raise ValueError("checkpoint is not the registered R25 arm0 final source")
    if not Path(args.checkpoint).is_file():
        raise FileNotFoundError(args.checkpoint)
    if not Path(args.scorer).is_file():
        raise FileNotFoundError(args.scorer)


def run_collect_reset(args: argparse.Namespace) -> dict[str, Any]:
    _validate_source(args)
    reset_id = int(args.reset_id)
    if reset_id not in RESET_IDS:
        raise ValueError("reset-id must be in 0..63")
    configure_deterministic_cuda(args.device)
    args.checkpoint_id = FINAL_CHECKPOINT_ID
    args.checkpoint_update = int(FINAL_SLOT["update"])
    (
        _config,
        _metadata,
        agent,
        env_factory,
        total_steps,
        loaded_update,
        loaded_value_norm_equal,
    ) = _configure_agent(args)
    if (
        int(total_steps) != int(FINAL_SLOT["total_steps"])
        or int(loaded_update) != int(FINAL_SLOT["update"])
        or not bool(loaded_value_norm_equal)
    ):
        raise R27G2ContractError("R28 transport source checkpoint state mismatch")
    scorer = FrozenR28G1Reward(
        arm="probe_only",
        scorer_path=args.scorer,
        actor_base=agent.low.actor_base,
        device=args.device,
    )
    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "reset_manifest.json"
    try:
        artifact = collect_support_transport_reset(
            env_factory=env_factory,
            agent=agent,
            scorer=scorer,
            reset_id=reset_id,
        )
        artifact_path = artifact.write(output_dir / f"reset_{reset_id:04d}.npz")
        paired = artifact.feature_valid[0] & artifact.feature_valid[1]
        manifest = {
            "experiment_id": EXPERIMENT_ID,
            "schema": SCHEMA,
            "status": "OK",
            "reset_id": reset_id,
            "reset_seed": reset_id + 1,
            "focal_agent": int(artifact.focal_agent),
            "checkpoint_id": FINAL_CHECKPOINT_ID,
            "checkpoint_update": int(loaded_update),
            "checkpoint_total_steps": int(total_steps),
            "checkpoint_path": str(Path(args.checkpoint)),
            "scorer_path": str(Path(args.scorer)),
            "device": str(args.device),
            "environment_steps": int(
                prefix_steps_for_reset(reset_id)
                + 2 * N_SKILLS * (prefix_steps_for_reset(reset_id) + 50)
            ),
            "policy_updates": 0,
            "reward_applied_steps": 0,
            "paired_windows": int(np.sum(paired)),
            "artifact": artifact_path.name,
        }
        _write_json(manifest_path, manifest)
    except Exception as error:
        _write_json(
            manifest_path,
            {
                "experiment_id": EXPERIMENT_ID,
                "schema": SCHEMA,
                "status": "INVALID",
                "reset_id": reset_id,
                "checkpoint_id": FINAL_CHECKPOINT_ID,
                "error": f"{type(error).__name__}: {error}",
            },
        )
        raise
    return {**manifest, "manifest": str(manifest_path)}


def _artifact_for_manifest(manifest_path: Path) -> tuple[dict[str, Any], R28SupportTransportArtifact]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("experiment_id") != EXPERIMENT_ID or manifest.get("status") != "OK":
        raise R27G2ContractError(f"invalid transport reset manifest: {manifest_path}")
    artifact_name = manifest.get("artifact")
    if not isinstance(artifact_name, str):
        raise R27G2ContractError(f"transport artifact missing: {manifest_path}")
    return manifest, R28SupportTransportArtifact.read(manifest_path.parent / artifact_name)


def _mode_metrics(
    artifacts: Sequence[R28SupportTransportArtifact], mode_id: int
) -> dict[str, Any]:
    support_rows: list[bool] = []
    ratios: list[float] = []
    abs_z_rows: list[np.ndarray] = []
    cells: dict[str, dict[str, float | int]] = {}
    for label in range(N_SKILLS):
        for duration_id, duration_steps in enumerate(DURATION_STEPS):
            paired_support: list[bool] = []
            for artifact in artifacts:
                paired = bool(
                    artifact.feature_valid[0, label, duration_id]
                    and artifact.feature_valid[1, label, duration_id]
                )
                if not paired:
                    continue
                paired_support.append(bool(artifact.support[mode_id, label, duration_id]))
                support_rows.append(bool(artifact.support[mode_id, label, duration_id]))
                ratios.append(
                    float(artifact.support_distance_ratio[mode_id, label, duration_id])
                )
                abs_z_rows.append(artifact.support_abs_z[mode_id, label, duration_id])
            key = f"label{label}_duration{duration_steps}"
            cells[key] = {
                "paired_rows": len(paired_support),
                "ood_fraction": (
                    float(np.mean(~np.asarray(paired_support, dtype=np.bool_)))
                    if paired_support
                    else 1.0
                ),
            }
    support_array = np.asarray(support_rows, dtype=np.bool_)
    ratio_array = np.asarray(ratios, dtype=np.float64)
    abs_z = np.asarray(abs_z_rows, dtype=np.float64)
    return {
        "paired_rows": int(support_array.size),
        "ood_fraction": float(np.mean(~support_array)) if support_array.size else 1.0,
        "distance_ratio_mean": float(np.mean(ratio_array)) if ratio_array.size else None,
        "distance_ratio_p95": (
            float(np.quantile(ratio_array, 0.95, method="linear"))
            if ratio_array.size
            else None
        ),
        "mean_abs_z": {
            name: float(np.mean(abs_z[:, index]))
            for index, name in enumerate(SUPPORT_FEATURE_NAMES)
        }
        if abs_z.size
        else {},
        "cells": cells,
    }


def classify_transport(
    mode_metrics: dict[str, dict[str, Any]], min_paired: int
) -> tuple[str, str, str]:
    deterministic = mode_metrics["deterministic"]
    stochastic = mode_metrics["stochastic"]
    deterministic_cells_pass = all(
        float(cell["ood_fraction"]) <= OOD_KILL_FRACTION
        for cell in deterministic["cells"].values()
    )
    stochastic_cells_pass = all(
        float(cell["ood_fraction"]) <= OOD_KILL_FRACTION
        for cell in stochastic["cells"].values()
    )
    if int(min_paired) < MIN_PAIRED_PER_CELL:
        return (
            "UNDERPOWERED",
            "UNDERPOWERED_PAIRED_SUPPORT",
            "add paired support only under the unchanged contract",
        )
    if (
        float(deterministic["ood_fraction"]) > OOD_KILL_FRACTION
        or not deterministic_cells_pass
    ):
        return (
            "INVALID",
            "INVALID_DETERMINISTIC_SOURCE_REPLICATION",
            "repair only the source-replay or scorer evidence path",
        )
    if (
        float(stochastic["ood_fraction"]) <= OOD_KILL_FRACTION
        and stochastic_cells_pass
    ):
        return (
            "PASS",
            "PASS_STOCHASTIC_SUPPORT_TRANSPORT",
            "test forced hold versus natural renewal under matched stochastic execution",
        )
    return (
        "FAIL",
        "FAIL_STOCHASTIC_SUPPORT_TRANSPORT",
        "retire forced-deterministic support as an online reward target",
    )


def run_aggregate(args: argparse.Namespace) -> dict[str, Any]:
    run_root = Path(args.run_root)
    artifacts: list[R28SupportTransportArtifact] = []
    manifests: list[dict[str, Any]] = []
    for reset_id in RESET_IDS:
        manifest_path = run_root / "resets" / f"reset_{reset_id:02d}" / "reset_manifest.json"
        manifest, artifact = _artifact_for_manifest(manifest_path)
        if int(manifest.get("reset_id", -1)) != reset_id or artifact.reset_id != reset_id:
            raise R27G2ContractError("transport reset identity/order mismatch")
        if not (
            artifact.replay_equal.all()
            and artifact.global_rng_unchanged[artifact.step_valid].all()
            and artifact.module_state_equal
            and artifact.value_norm_state_equal
        ):
            raise R27G2ContractError("transport reset validity invariant failed")
        manifests.append(manifest)
        artifacts.append(artifact)

    mode_metrics = {
        mode: _mode_metrics(artifacts, mode_id)
        for mode_id, mode in enumerate(MODES)
    }
    min_paired = min(
        int(cell["paired_rows"])
        for mode in mode_metrics.values()
        for cell in mode["cells"].values()
    )
    deterministic = mode_metrics["deterministic"]
    stochastic = mode_metrics["stochastic"]
    scientific_status, classification, next_action = classify_transport(
        mode_metrics, min_paired
    )

    report = {
        "experiment_id": EXPERIMENT_ID,
        "scientific_status": scientific_status,
        "classification": classification,
        "causal_edge": (
            "R27-proven forced skill regime -> support-compatible action process "
            "under on-policy state visitation"
        ),
        "checkpoint_id": FINAL_CHECKPOINT_ID,
        "reset_ids": list(RESET_IDS),
        "focal_agent_rule": "reset_id % 6",
        "modes": list(MODES),
        "environment_steps": int(sum(item["environment_steps"] for item in manifests)),
        "policy_updates": 0,
        "reward_applied_steps": 0,
        "support_ood_threshold": OOD_KILL_FRACTION,
        "minimum_paired_rows_per_label_duration": MIN_PAIRED_PER_CELL,
        "observed_minimum_paired_rows_per_label_duration": min_paired,
        "mode_metrics": mode_metrics,
        "next_action": next_action,
    }
    report_path = run_root / "r28_support_transport.json"
    _write_json(report_path, report)
    markdown_path = run_root / "r28_support_transport.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# R28 Forced-Execution Support Transport",
                "",
                f"- Status: `{scientific_status}`",
                f"- Classification: `{classification}`",
                f"- Deterministic OOD: `{deterministic['ood_fraction']:.6f}`",
                f"- Stochastic OOD: `{stochastic['ood_fraction']:.6f}`",
                f"- Minimum paired rows/cell: `{min_paired}`",
                f"- Environment steps: `{report['environment_steps']}`",
                "- Policy updates / reward-applied steps: `0 / 0`",
                f"- Next action: {next_action}.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {**report, "json": str(report_path), "markdown": str(markdown_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect = subparsers.add_parser("collect-reset")
    _source_args(collect)
    collect.add_argument("--reset-id", required=True, type=int)
    collect.add_argument("--output-dir", required=True)
    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--run-root", required=True)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main() -> None:
    args = parse_args()
    result = run_collect_reset(args) if args.command == "collect-reset" else run_aggregate(args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Frozen family decision for the three-arm R28-G1 continuation."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
import zipfile
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.r27_g2_analysis import late_action_features  # noqa: E402
from ha_ctse_process.r28_g0_target import (  # noqa: E402
    CONTEXT_WIDTH,
    DURATION_STEPS,
    HEAD_INPUT_WIDTH,
    N_AGENTS,
    N_SKILLS,
    STREAM_WIDTH,
)
from ha_ctse_process.r28_g1_reward import (  # noqa: E402
    ARMS,
    FINAL_CHECKPOINT_ID,
    FINAL_CHECKPOINT_PATH,
    FrozenHead,
    FrozenR28G1Reward,
    R28G1ContractError,
    fixed_point_free_derangement,
)


SEEDS = (28031, 28032, 28033)
R26_BOOTSTRAP_SEED = 28034
S_REAL_BOOTSTRAP_SEED = 28035
S_DELTA_BOOTSTRAP_SEED = 28036
BOOTSTRAP_REPS = 10_000
FINAL_TOTAL_STEPS = 1_160_000
FINAL_UPDATE = 52
EXPECTED_UPDATES = tuple(range(33, FINAL_UPDATE + 1))
EXPECTED_EVAL_STEPS = (1_080_000, FINAL_TOTAL_STEPS)
R26_SEEDS = {
    "split": 26011,
    "model": 26012,
    "null": 26013,
    "bootstrap": 26014,
}
EXPECTED_TEST_RESETS = {0, 5, 7, 8, 17, 18, 25, 32, 39, 49, 54, 58}
MANIFEST_SECTIONS = (
    "algorithm_config",
    "training_config",
    "model_config",
    "physical_env_config",
    "env_runtime_spec",
    "agent_runtime_spec",
)
NON_R28_ALGORITHM_FALSE = (
    "enable_prototype_disc_reward",
    "enable_team_disc_reward",
    "enable_team_transition_reward",
    "enable_assignment_actionability_reward",
    "enable_g_info_objective",
    "enable_skill_forcing_reward",
    "skill_forcing_reward_on",
    "skill_effect_reward_on",
    "use_topology_potential_shaping",
    "p2_recovery_credit_reward_on",
    "use_process_reward_for_discoverer",
)
NON_R28_TRAINING_FALSE = (
    "duration_entropy_floor_enabled",
    "z_entropy_floor_enabled",
)
NON_R28_ALGORITHM_ZERO = (
    "prototype_disc_reward_coef",
    "team_disc_coef",
    "team_transition_coef",
    "assignment_actionability_coef",
    "transition_skill_reward_coef",
    "outcome_residual_reward_coef",
    "topology_role_reward_coef",
    "topology_potential_coef",
    "p2_recovery_reward_coef",
    "skill_effect_ctrl_coef",
    "skill_effect_use_coef",
    "skill_force_disc_coef",
    "skill_force_effect_coef",
    "skill_force_duration_entropy_coef",
    "g_info_coef_skill",
    "g_info_coef_duration",
    "g_info_coef_edit",
    "situation_hazard_reward_coef",
)
NON_R28_TRAINING_ZERO = (
    "duration_entropy_floor_coef",
    "z_entropy_floor_coef",
)
NON_R28_ALGORITHM_MODES = {
    "process_reward_mode": "none",
    "process_reward_injection": "none",
    "outcome_residual_injection": "none",
    "topology_role_injection": "none",
    "topology_potential_injection": "none",
    "skill_effect_reward_injection": "none",
    "skill_force_reward_injection": "none",
}
NON_R28_ARG_FALSE = (
    "enable_prototype_disc_reward",
    "enable_team_disc_reward",
    "enable_team_transition_reward",
    "enable_assignment_actionability_reward",
    "enable_g_info_objective",
    "enable_skill_forcing_reward",
    "enable_skill_effect_reward",
    "enable_p2_recovery_reward",
    "enable_topology_potential_shaping",
    "enable_duration_entropy_floor",
    "enable_z_entropy_floor",
)


class FamilyEvidenceError(ValueError):
    pass


class FamilyUnderpoweredError(FamilyEvidenceError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FamilyEvidenceError(f"missing JSON evidence: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FamilyEvidenceError(f"JSON evidence is not an object: {path}")
    return value


def _finite(name: str, value: Any, shape: tuple[int, ...] | None = None) -> np.ndarray:
    result = np.asarray(value)
    if shape is not None and result.shape != shape:
        raise FamilyEvidenceError(f"{name} shape {result.shape} != {shape}")
    if result.size and not np.issubdtype(result.dtype, np.number):
        raise FamilyEvidenceError(f"{name} is not numeric")
    result = result.astype(np.float32, copy=False)
    if result.size and not np.isfinite(result).all():
        raise FamilyEvidenceError(f"{name} contains non-finite values")
    return result


def bootstrap_statistic(
    rows: list[dict[str, float]],
    *,
    statistic,
    seed: int,
    reps: int = BOOTSTRAP_REPS,
) -> dict[str, float | int]:
    if not rows:
        raise FamilyUnderpoweredError("cluster bootstrap has no rows")
    estimate = float(statistic(rows))
    if not np.isfinite(estimate):
        raise FamilyEvidenceError("cluster bootstrap estimate is non-finite")
    rng = np.random.default_rng(int(seed))
    values = np.empty(int(reps), dtype=np.float64)
    for index in range(int(reps)):
        sampled = rng.integers(0, len(rows), size=len(rows))
        values[index] = float(statistic([rows[int(item)] for item in sampled]))
    if not np.isfinite(values).all():
        raise FamilyEvidenceError("cluster bootstrap samples are non-finite")
    return {
        "estimate": estimate,
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
        "clusters": len(rows),
        "reps": int(reps),
        "seed": int(seed),
    }


def r26_cluster_rows(reports: dict[tuple[str, int], dict[str, Any]]) -> list[dict[str, float]]:
    per_arm: dict[tuple[str, int, int], float] = {}
    for (arm, seed), report in reports.items():
        gate = report.get("gate")
        status = str(gate.get("status")) if isinstance(gate, Mapping) else ""
        if status == "UNDERPOWERED" or report.get("underpowered") is True:
            raise FamilyUnderpoweredError(
                f"{arm}/seed{seed} R26 analysis is underpowered"
            )
        if status == "INVALID" or report.get("valid") is not True:
            raise FamilyEvidenceError(f"{arm}/seed{seed} R26 analysis is invalid")
        evidence = report.get("heldout_row_correctness")
        if not isinstance(evidence, list) or not evidence:
            raise FamilyEvidenceError(f"{arm}/seed{seed} lacks held-out row correctness")
        buckets: dict[int, list[float]] = {}
        for row in evidence:
            if not isinstance(row, Mapping):
                raise FamilyEvidenceError("R26 held-out row is malformed")
            reset_id = int(row["reset_id"])
            buckets.setdefault(reset_id, []).append(
                float(bool(row["full_correct"])) - float(bool(row["prior_correct"]))
            )
        for reset_id, values in buckets.items():
            per_arm[(arm, int(seed), reset_id)] = float(np.mean(values))

    result: list[dict[str, float]] = []
    for seed in SEEDS:
        common = set.intersection(
            *[
                {
                    reset
                    for (candidate, candidate_seed, reset), _value in per_arm.items()
                    if candidate == arm and candidate_seed == seed
                }
                for arm in ARMS
            ]
        )
        for reset_id in sorted(common):
            result.append(
                {
                    "seed": float(seed),
                    "reset_id": float(reset_id),
                    **{
                        arm: per_arm[(arm, seed, reset_id)]
                        for arm in ARMS
                    },
                }
            )
    if not result:
        raise FamilyUnderpoweredError("R26 arms share no (seed,test_reset) clusters")
    return result


def _r26_delta(rows: list[dict[str, float]]) -> float:
    return float(
        np.mean(
            [
                row["real_reward"]
                - max(row["probe_only"], row["sham_reward"])
                for row in rows
            ]
        )
    )


def _pooled_cluster_mean(rows: list[dict[str, float]], sum_field: str) -> float:
    count = float(sum(row["count"] for row in rows))
    if count <= 0.0:
        raise FamilyUnderpoweredError("pooled sidecar bootstrap has zero rows")
    return float(sum(row[sum_field] for row in rows) / count)


def _load_scorer(path: Path, device: torch.device):
    try:
        payload = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, Mapping):
        raise FamilyEvidenceError("G0 scorer payload is malformed")
    FrozenR28G1Reward._validate_payload(payload)
    heads = {
        name: FrozenHead.from_payload(name, payload["heads"][name], device)
        for name in ("q_full", "q_context", "q_pre")
    }
    envelope = payload["support_envelope"]
    means = _finite("support means", envelope["means"], (4, 4, 12))
    variances = _finite("support variances", envelope["variances"], (4, 4, 12))
    thresholds = _finite("support thresholds", envelope["thresholds"], (4, 4))
    if np.any(variances <= 0.0):
        raise FamilyEvidenceError("support variances are not positive")
    if np.any(thresholds < 0.0):
        raise FamilyEvidenceError("support thresholds are negative")
    if not np.isclose(float(envelope.get("future_ood_kill_fraction", -1.0)), 0.20):
        raise FamilyEvidenceError("support OOD kill fraction drifted from 0.20")
    return heads, means, variances, thresholds


def _sidecar_arrays(
    directory: Path,
    *,
    expected_seed: int,
    expected_checkpoint_id: str,
) -> dict[str, np.ndarray]:
    paths = sorted(directory.glob("reset_*.npz"))
    if len(paths) != 64:
        raise FamilyEvidenceError(f"{directory} requires exactly 64 sidecar shards")
    fields = (
        "label",
        "duration_idx",
        "agent_id",
        "episode_step_start",
        "phi0",
        "pre_actions",
        "post_actions",
        "pre_valid",
        "reset_id",
        "reset_seed",
        "episode_id",
        "env_id",
        "checkpoint_id",
        "checkpoint_update",
    )
    pieces: dict[str, list[np.ndarray]] = {field: [] for field in fields}
    for expected_reset_id, path in enumerate(paths):
        if path.name != f"reset_{expected_reset_id:04d}.npz":
            raise FamilyEvidenceError(f"sidecar shard name sequence drifted: {path}")
        with np.load(path, allow_pickle=False) as shard:
            if str(np.asarray(shard["schema"]).item()) != "r28-g1-natural-sidecar-v1":
                raise FamilyEvidenceError(f"sidecar schema mismatch: {path}")
            rows = int(np.asarray(shard["label"]).size)
            for field in fields:
                value = np.asarray(shard[field])
                if int(value.shape[0]) != rows:
                    raise FamilyEvidenceError(f"{path} field {field} row mismatch")
                pieces[field].append(value)
            reset_ids = np.asarray(shard["reset_id"], dtype=np.int64)
            if rows and not np.all(reset_ids == expected_reset_id):
                raise FamilyEvidenceError(f"sidecar reset identity mismatch: {path}")
            reset_seeds = np.asarray(shard["reset_seed"], dtype=np.int64)
            if rows and not np.all(reset_seeds == int(expected_seed) + expected_reset_id):
                raise FamilyEvidenceError(f"sidecar reset seed mismatch: {path}")
    result = {
        field: np.concatenate(values, axis=0) if values else np.zeros(0)
        for field, values in pieces.items()
    }
    rows = int(result["label"].size)
    if rows == 0:
        raise FamilyUnderpoweredError(f"sidecar has no natural rows: {directory}")
    if result["phi0"].shape != (rows, 256):
        raise FamilyEvidenceError("sidecar phi0 width mismatch")
    if result["pre_actions"].shape != (rows, 10, 4) or result["post_actions"].shape != (rows, 10, 4):
        raise FamilyEvidenceError("sidecar deterministic-action shape mismatch")
    if not (
        np.isfinite(np.asarray(result["phi0"], dtype=np.float32)).all()
        and np.isfinite(np.asarray(result["pre_actions"], dtype=np.float32)).all()
        and np.isfinite(np.asarray(result["post_actions"], dtype=np.float32)).all()
    ):
        raise FamilyEvidenceError("sidecar contains non-finite model evidence")
    if not np.all(np.asarray(result["checkpoint_update"], dtype=np.int64) == FINAL_UPDATE):
        raise FamilyEvidenceError("sidecar checkpoint update is not 52")
    if not np.all(np.asarray(result["checkpoint_id"]).astype(str) == expected_checkpoint_id):
        raise FamilyEvidenceError("sidecar checkpoint identity mismatch")
    if not np.all(np.asarray(result["env_id"], dtype=np.int64) == 0):
        raise FamilyEvidenceError("sidecar env identity is not the frozen single collector env")
    episode_steps = np.asarray(result["episode_step_start"], dtype=np.int64)
    if np.any((episode_steps < 0) | (episode_steps >= 500)):
        raise FamilyEvidenceError("sidecar episode step lies outside [0,500)")
    return result


def score_sidecar(
    directory: Path,
    *,
    test_reset_ids: set[int],
    heads: dict[str, FrozenHead],
    support_means: np.ndarray,
    support_variances: np.ndarray,
    support_thresholds: np.ndarray,
    device: torch.device,
    expected_seed: int,
    expected_checkpoint_id: str,
) -> dict[str, Any]:
    arrays = _sidecar_arrays(
        directory,
        expected_seed=expected_seed,
        expected_checkpoint_id=expected_checkpoint_id,
    )
    labels = np.asarray(arrays["label"], dtype=np.int64)
    durations = np.asarray(arrays["duration_idx"], dtype=np.int64)
    agents = np.asarray(arrays["agent_id"], dtype=np.int64)
    resets = np.asarray(arrays["reset_id"], dtype=np.int64)
    updates = np.asarray(arrays["checkpoint_update"], dtype=np.int64)
    mask = np.asarray(arrays["pre_valid"], dtype=np.bool_) & np.isin(
        resets, np.asarray(sorted(test_reset_ids), dtype=np.int64)
    )
    if not np.any(mask):
        raise FamilyUnderpoweredError("sidecar has no pre-valid held-out rows")
    labels = labels[mask]
    durations = durations[mask]
    agents = agents[mask]
    resets = resets[mask]
    updates = updates[mask]
    phi0 = _finite("sidecar phi0", arrays["phi0"][mask], (int(np.sum(mask)), 256))
    pre = late_action_features(_finite("sidecar pre", arrays["pre_actions"][mask]))
    post = late_action_features(_finite("sidecar post", arrays["post_actions"][mask]))
    phases = np.minimum(
        np.asarray(arrays["episode_step_start"], dtype=np.int64)[mask] // 100,
        2,
    )
    if np.any((labels < 0) | (labels >= N_SKILLS)) or np.any(
        (durations < 0) | (durations >= len(DURATION_STEPS))
    ):
        raise FamilyEvidenceError("sidecar label/duration lies outside the frozen contract")
    if np.any((agents < 0) | (agents >= N_AGENTS)):
        raise FamilyEvidenceError("sidecar agent lies outside the frozen contract")
    context = np.concatenate(
        (
            phi0,
            np.eye(N_AGENTS, dtype=np.float32)[agents],
            np.eye(4, dtype=np.float32)[durations],
            np.eye(3, dtype=np.float32)[phases],
        ),
        axis=1,
    )
    if context.shape[1] != CONTEXT_WIDTH:
        raise FamilyEvidenceError("sidecar context width mismatch")

    support = np.zeros(labels.size, dtype=np.bool_)
    for index in range(labels.size):
        distance = float(
            np.sum(
                np.square(post[index] - support_means[durations[index], labels[index]])
                / support_variances[durations[index], labels[index]]
            )
        )
        if not np.isfinite(distance):
            raise FamilyEvidenceError("sidecar support distance is non-finite")
        support[index] = distance <= support_thresholds[durations[index], labels[index]]
    ood_fraction = float(np.mean(~support))

    post_t = torch.as_tensor(post, dtype=torch.float32, device=device)
    pre_t = torch.as_tensor(pre, dtype=torch.float32, device=device)
    context_t = torch.as_tensor(context, dtype=torch.float32, device=device)
    with torch.no_grad():
        log_probs = {
            "q_full": heads["q_full"].log_probs(torch.cat((post_t, context_t), dim=1)).cpu().numpy(),
            "q_context": heads["q_context"].log_probs(
                torch.cat((torch.zeros_like(post_t), context_t), dim=1)
            ).cpu().numpy(),
            "q_pre": heads["q_pre"].log_probs(torch.cat((pre_t, context_t), dim=1)).cpu().numpy(),
        }
    if not all(np.isfinite(value).all() for value in log_probs.values()):
        raise FamilyEvidenceError("sidecar frozen head produced non-finite scores")
    sham = np.full(labels.size, -1, dtype=np.int64)
    rewardable = np.zeros(labels.size, dtype=np.bool_)
    row_ids = np.arange(labels.size, dtype=np.int64)
    for update in np.unique(updates):
        for agent in range(N_AGENTS):
            for duration in range(4):
                group = row_ids[
                    support
                    & (updates == update)
                    & (agents == agent)
                    & (durations == duration)
                ]
                if group.size == 0:
                    continue
                counts = np.bincount(labels[group], minlength=N_SKILLS)
                if np.any(counts == 0) or int(np.max(counts)) > group.size // 2:
                    continue
                sham[group] = fixed_point_free_derangement(
                    labels[group],
                    policy_update=int(update),
                    agent_id=agent,
                    duration_id=duration,
                )
                rewardable[group] = True
    if not np.any(rewardable):
        raise FamilyUnderpoweredError("sidecar has no balanced in-support rewardable group")
    indices = row_ids[rewardable]
    real_labels = labels[indices]
    sham_labels = sham[indices]
    s_real = log_probs["q_full"][indices, real_labels] - np.maximum(
        log_probs["q_context"][indices, real_labels],
        log_probs["q_pre"][indices, real_labels],
    )
    s_sham = log_probs["q_full"][indices, sham_labels] - np.maximum(
        log_probs["q_context"][indices, sham_labels],
        log_probs["q_pre"][indices, sham_labels],
    )
    if not (np.isfinite(s_real).all() and np.isfinite(s_sham).all()):
        raise FamilyEvidenceError("sidecar frozen scores are non-finite")
    cluster_rows: list[dict[str, float]] = []
    for reset in np.unique(resets[indices]):
        cluster = indices[resets[indices] == reset]
        positions = np.searchsorted(indices, cluster)
        cluster_rows.append(
            {
                "reset_id": float(reset),
                "s_real": float(np.mean(s_real[positions])),
                "s_delta": float(np.mean(s_real[positions] - s_sham[positions])),
                "s_real_sum": float(np.sum(s_real[positions])),
                "s_delta_sum": float(np.sum(s_real[positions] - s_sham[positions])),
                "count": float(positions.size),
            }
        )
    return {
        "structural_rows": int(labels.size),
        "in_support_rows": int(np.sum(support)),
        "rewardable_rows": int(np.sum(rewardable)),
        "ood_fraction": ood_fraction,
        "mean_s_real": float(np.mean(s_real)),
        "mean_s_real_minus_sham": float(np.mean(s_real - s_sham)),
        "clusters": cluster_rows,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FamilyEvidenceError(f"missing CSV evidence: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: Mapping[str, str], name: str) -> float:
    text = row.get(name)
    if text in (None, ""):
        raise FamilyEvidenceError(f"required CSV field {name} is missing")
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise FamilyEvidenceError(f"CSV field {name} is not numeric") from exc
    if not np.isfinite(value):
        raise FamilyEvidenceError(f"CSV field {name} is non-finite")
    return value


def _same_path(left: Any, right: Any) -> bool:
    if not left or not right:
        return False
    return Path(str(left)).resolve() == Path(str(right)).resolve()


def _registered_source_path(value: Any) -> bool:
    source_path = str(value or "").replace("\\", "/")
    return source_path == FINAL_CHECKPOINT_PATH or source_path.endswith(
        f"/{FINAL_CHECKPOINT_PATH}"
    )


def _load_status(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FamilyEvidenceError(f"missing runner status: {path}")
    result: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if "=" not in line:
            raise FamilyEvidenceError(f"malformed runner status line {path}:{line_number}")
        name, value = line.split("=", 1)
        name = name.strip()
        if not name or name in result:
            raise FamilyEvidenceError(f"duplicate/empty runner status key {path}:{line_number}")
        result[name] = value.strip()
    if not result:
        raise FamilyEvidenceError(f"empty runner status: {path}")
    return result


def _require_status_fields(
    status: Mapping[str, str], expected: Mapping[str, str], *, label: str
) -> None:
    for name, value in expected.items():
        if status.get(name) != value:
            raise FamilyEvidenceError(
                f"{label} status {name}={status.get(name)!r}, expected {value!r}"
            )


def validate_execution_contract(run_root: Path, scorer_path: Path) -> None:
    marker_path = run_root / "topology" / "topology_passed.json"
    marker = _load_json(marker_path)
    exact_marker = {
        "status": "PASS",
        "device": "cuda",
        "arms": list(ARMS),
        "concurrent_workers": 3,
        "num_envs_per_worker": 16,
        "rollout_length": 500,
        "topology_total_timesteps": 1_008_000,
        "serial_fallback": False,
    }
    for name, expected in exact_marker.items():
        if marker.get(name) != expected:
            raise FamilyEvidenceError(
                f"topology marker {name}={marker.get(name)!r}, expected {expected!r}"
            )
    if not _registered_source_path(marker.get("source_checkpoint")):
        raise FamilyEvidenceError("topology marker source checkpoint path drifted")
    if not _same_path(marker.get("scorer_path"), scorer_path):
        raise FamilyEvidenceError("topology marker scorer path drifted")
    measured = marker.get("measured_batch_seconds")
    if isinstance(measured, bool) or not isinstance(measured, int) or measured <= 0:
        raise FamilyEvidenceError("topology marker measured batch time is invalid")
    projected = marker.get("projected_training_hours")
    revised = marker.get("revised_end_to_end_hours")
    if (
        isinstance(projected, bool)
        or not isinstance(projected, (int, float))
        or not np.isfinite(float(projected))
        or float(projected) <= 0.0
    ):
        raise FamilyEvidenceError("topology marker projected training time is invalid")
    if not isinstance(revised, list) or len(revised) != 2:
        raise FamilyEvidenceError("topology marker revised wall-clock range is invalid")
    try:
        revised_low, revised_high = (float(item) for item in revised)
    except (TypeError, ValueError) as exc:
        raise FamilyEvidenceError("topology marker revised wall-clock range is invalid") from exc
    if not (
        np.isfinite(revised_low)
        and np.isfinite(revised_high)
        and 0.0 < revised_low <= revised_high
    ):
        raise FamilyEvidenceError("topology marker revised wall-clock range is invalid")

    topology_status = _load_status(run_root / "topology" / "runner_status.txt")
    _require_status_fields(
        topology_status,
        {
            "state": "succeeded",
            "phase": "topology",
            "concurrent_workers": "3",
            "device": "cuda",
            "measured_batch_seconds": str(measured),
        },
        label="topology",
    )
    if not _same_path(topology_status.get("topology_marker"), marker_path):
        raise FamilyEvidenceError("topology status marker path drifted")

    batch_status = _load_status(run_root / "run_status.txt")
    _require_status_fields(
        batch_status,
        {
            "state": "succeeded",
            "phase": "run",
            "completed_runs": "9",
            "concurrent_arms": "3",
            "total_timesteps": str(FINAL_TOTAL_STEPS),
        },
        label="training batch",
    )
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = run_root / "runs" / arm / f"seed{seed}"
            status = _load_status(run_dir / "runner_status.txt")
            _require_status_fields(
                status,
                {
                    "state": "succeeded",
                    "phase": "run",
                    "arm": arm,
                    "seed": str(seed),
                    "device": "cuda",
                    "total_timesteps": str(FINAL_TOTAL_STEPS),
                    "exit_code": "0",
                },
                label=f"{arm}/seed{seed}",
            )
            if not _same_path(
                status.get("final_checkpoint"),
                run_dir / "standalone_process_core_final.pt",
            ):
                raise FamilyEvidenceError(
                    f"{arm}/seed{seed} status final checkpoint path drifted"
                )


def normalized_run_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    try:
        normalized = json.loads(json.dumps(dict(manifest), sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise FamilyEvidenceError("run manifest is not JSON-normalizable") from exc
    args = normalized.get("args")
    if not isinstance(args, dict):
        raise FamilyEvidenceError("run manifest args are missing")
    for section_name in MANIFEST_SECTIONS:
        if not isinstance(normalized.get(section_name), dict):
            raise FamilyEvidenceError(f"run manifest section {section_name} is missing")
    args["seed"] = "<SEED>"
    args["r28_g1_arm"] = "<R28_ARM>"
    args["log_dir"] = "<LOG_DIR>"
    if args.get("r24_qd_export_dir"):
        args["r24_qd_export_dir"] = "<LOG_DIR>"
    normalized["training_config"]["r28_g1_arm"] = "<R28_ARM>"
    if normalized["algorithm_config"].get("r24_qd_export_dir"):
        normalized["algorithm_config"]["r24_qd_export_dir"] = "<LOG_DIR>"
    return normalized


def _require_false_fields(
    values: Mapping[str, Any], fields: tuple[str, ...], *, label: str
) -> None:
    for name in fields:
        if values.get(name) is not False:
            raise FamilyEvidenceError(
                f"{label} non-R28 flag {name} is not explicitly false"
            )


def _require_zero_fields(
    values: Mapping[str, Any], fields: tuple[str, ...], *, label: str
) -> None:
    for name in fields:
        value = values.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not np.isfinite(float(value))
            or float(value) != 0.0
        ):
            raise FamilyEvidenceError(
                f"{label} non-R28 coefficient {name} is not explicitly zero"
            )


def validate_disabled_reward_contract(
    manifest: Mapping[str, Any], checkpoint: Mapping[str, Any], *, label: str
) -> None:
    args = manifest.get("args")
    algorithm = manifest.get("algorithm_config")
    training = manifest.get("training_config")
    if not isinstance(args, Mapping) or not isinstance(algorithm, Mapping) or not isinstance(
        training, Mapping
    ):
        raise FamilyEvidenceError(f"{label} reward-contract manifest sections are missing")
    _require_false_fields(algorithm, NON_R28_ALGORITHM_FALSE, label=label)
    _require_false_fields(training, NON_R28_TRAINING_FALSE, label=label)
    _require_false_fields(args, NON_R28_ARG_FALSE, label=f"{label} CLI")
    _require_zero_fields(algorithm, NON_R28_ALGORITHM_ZERO, label=label)
    _require_zero_fields(training, NON_R28_TRAINING_ZERO, label=label)
    for name, expected in NON_R28_ALGORITHM_MODES.items():
        if algorithm.get(name) != expected:
            raise FamilyEvidenceError(
                f"{label} non-R28 mode {name}={algorithm.get(name)!r}, expected {expected!r}"
            )
    for name in ("p2_recovery_reward_coef", "assignment_actionability_coef"):
        value = args.get(name)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not np.isfinite(float(value))
            or float(value) != 0.0
        ):
            raise FamilyEvidenceError(f"{label} CLI coefficient {name} is not disabled")
    _require_false_fields(
        checkpoint,
        (
            "enable_prototype_disc_reward",
            "enable_team_disc_reward",
            "enable_team_transition_reward",
            "enable_assignment_actionability_reward",
            "z_entropy_floor_enabled",
        ),
        label=f"{label} checkpoint",
    )
    _require_zero_fields(
        checkpoint,
        (
            "team_disc_coef",
            "team_transition_coef",
            "assignment_actionability_coef",
            "z_entropy_floor_coef",
        ),
        label=f"{label} checkpoint",
    )


def validate_run_identity(
    run_dir: Path,
    *,
    arm: str,
    seed: int,
    scorer_path: Path,
) -> tuple[str, dict[str, Any]]:
    manifest = _load_json(run_dir / "metadata" / "run_manifest.json")
    args = manifest.get("args")
    if not isinstance(args, Mapping):
        raise FamilyEvidenceError(f"{run_dir} run manifest args are missing")
    expected_args = {
        "seed": int(seed),
        "preset": "S7-S1",
        "scenario": "energy",
        "device": "cuda",
        "collector_backend": "subproc",
        "num_envs": 16,
        "rollout_length": 500,
        "skill_interval": 10,
        "low_ppo_epochs": 15,
        "total_timesteps": FINAL_TOTAL_STEPS,
        "eval_interval": 80_000,
        "eval_episodes": 20,
        "eval_action_mode": "deterministic",
        "r28_g1_arm": arm,
    }
    for name, expected in expected_args.items():
        if args.get(name) != expected:
            raise FamilyEvidenceError(
                f"{arm}/seed{seed} run arg {name}={args.get(name)!r}, expected {expected!r}"
            )
    if not _registered_source_path(args.get("resume_from")):
        raise FamilyEvidenceError(f"{arm}/seed{seed} source checkpoint path drifted")
    if not _same_path(args.get("r28_g1_scorer_path"), scorer_path):
        raise FamilyEvidenceError(f"{arm}/seed{seed} scorer path drifted")
    if not _same_path(args.get("log_dir"), run_dir):
        raise FamilyEvidenceError(f"{arm}/seed{seed} log directory drifted")
    algorithm = manifest.get("algorithm_config")
    if not isinstance(algorithm, Mapping):
        raise FamilyEvidenceError(f"{arm}/seed{seed} algorithm manifest is missing")
    expected_qd_dir = run_dir / "r24_qd_windows"
    for output_path in (args.get("r24_qd_export_dir"), algorithm.get("r24_qd_export_dir")):
        if output_path and not _same_path(output_path, expected_qd_dir):
            raise FamilyEvidenceError(f"{arm}/seed{seed} R24 export log path drifted")
    if int(manifest.get("total_steps", -1)) != FINAL_TOTAL_STEPS or int(
        manifest.get("update_idx", -1)
    ) != FINAL_UPDATE:
        raise FamilyEvidenceError(f"{arm}/seed{seed} run manifest exposure is incomplete")

    checkpoint_path = run_dir / "standalone_process_core_final.pt"
    if not checkpoint_path.is_file():
        raise FamilyEvidenceError(f"missing final checkpoint: {checkpoint_path}")
    try:
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    except TypeError:
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if not isinstance(checkpoint, Mapping):
        raise FamilyEvidenceError(f"final checkpoint is malformed: {checkpoint_path}")
    exact_checkpoint = {
        "total_steps": FINAL_TOTAL_STEPS,
        "update_idx": FINAL_UPDATE,
        "r28_g1_arm": arm,
        "n_agents": 6,
        "n_skills": 4,
        "action_space_type": "continuous",
        "use_recurrent_low_level": True,
        "low_level_architecture": "strict_hmasd_mappo",
        "skill_interval": 10,
    }
    for name, expected in exact_checkpoint.items():
        if checkpoint.get(name) != expected:
            raise FamilyEvidenceError(
                f"{arm}/seed{seed} checkpoint {name} drifted from {expected!r}"
            )
    if tuple(int(item) for item in checkpoint.get("duration_candidates", ())) != (1, 2, 3, 4):
        raise FamilyEvidenceError(f"{arm}/seed{seed} checkpoint durations drifted")
    continuation = checkpoint.get("r28_g1")
    if not isinstance(continuation, Mapping):
        raise FamilyEvidenceError(f"{arm}/seed{seed} lacks R28 continuation state")
    expected_continuation = {
        "arm": arm,
        "source_total_steps": 1_000_000,
        "source_update_idx": 32,
        "source_checkpoint_id": FINAL_CHECKPOINT_ID,
    }
    for name, expected in expected_continuation.items():
        if continuation.get(name) != expected:
            raise FamilyEvidenceError(
                f"{arm}/seed{seed} continuation {name} drifted from {expected!r}"
            )
    if not isinstance(continuation.get("frozen_actor_base"), Mapping):
        raise FamilyEvidenceError(f"{arm}/seed{seed} frozen actor base is missing")
    if not _same_path(continuation.get("scorer_path"), scorer_path):
        raise FamilyEvidenceError(f"{arm}/seed{seed} continuation scorer path drifted")
    validate_disabled_reward_contract(
        manifest,
        checkpoint,
        label=f"{arm}/seed{seed}",
    )
    return f"r28_g1_{arm}_seed{seed}_final", manifest


def training_guard_summary(run_dir: Path, *, arm: str) -> dict[str, float]:
    rows = _read_csv(run_dir / "metrics" / "train_updates.csv")
    if not rows:
        raise FamilyEvidenceError(f"training update CSV is empty: {run_dir}")
    updates = [int(_float(row, "update")) for row in rows]
    total_steps = [int(_float(row, "total_steps")) for row in rows]
    expected_steps = [1_000_000 + 8_000 * (update - 32) for update in EXPECTED_UPDATES]
    if updates != list(EXPECTED_UPDATES) or total_steps != expected_steps:
        raise FamilyEvidenceError(f"{run_dir} update/step exposure is not 33..52 / +160k")
    arm_code = float(ARMS.index(arm))
    if any(_float(row, "r28_g1_active") != 1.0 for row in rows):
        raise FamilyEvidenceError(f"{run_dir} contains an inactive R28 update")
    if any(_float(row, "r28_g1_arm_code") != arm_code for row in rows):
        raise FamilyEvidenceError(f"{run_dir} R28 arm code mismatch")
    if arm == "probe_only" and any(
        _float(row, "r28_g1_reward_applied_steps") != 0.0 for row in rows
    ):
        raise FamilyEvidenceError(f"{run_dir} probe-only arm injected reward")
    return {
        "support_kill_switch_events": float(
            sum(_float(row, "r28_g1_support_kill_switch_event") for row in rows)
        ),
        "ratio_kill_switch_events": float(
            sum(_float(row, "r28_g1_ratio_kill_switch_event") for row in rows)
        ),
        "max_reward_env_ratio": float(
            max(_float(row, "r28_g1_reward_env_ratio") for row in rows)
        ),
        "updates": float(len(rows)),
        "final_total_steps": float(total_steps[-1]),
    }


def final_task_summary(run_dir: Path) -> dict[str, float]:
    rows = _read_csv(run_dir / "metrics" / "eval_episodes.csv")
    if not rows:
        raise FamilyEvidenceError(f"evaluation CSV is empty: {run_dir}")
    grouped: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(int(_float(row, "total_steps")), []).append(row)
    if tuple(sorted(grouped)) != EXPECTED_EVAL_STEPS:
        raise FamilyEvidenceError(f"{run_dir} evaluations are not exactly +80k and +160k")
    for step in EXPECTED_EVAL_STEPS:
        current = grouped[step]
        if len(current) != 20:
            raise FamilyEvidenceError(f"{run_dir} evaluation {step} has {len(current)} episodes")
        if sorted(int(_float(row, "episode")) for row in current) != list(range(20)):
            raise FamilyEvidenceError(f"{run_dir} evaluation {step} episode identities drifted")
        if any(_float(row, "action_mode_code") != 0.0 for row in current):
            raise FamilyEvidenceError(f"{run_dir} evaluation {step} was not deterministic")
    final = grouped[FINAL_TOTAL_STEPS]
    return {
        "total_steps": float(FINAL_TOTAL_STEPS),
        "return_mean": float(np.mean([_float(row, "reward") for row in final])),
        "zero_throughput_episode_fraction": float(
            np.mean([_float(row, "zero_throughput_episode_flag") for row in final])
        ),
    }


def validate_collection_manifest(
    evidence_dir: Path,
    *,
    arm: str,
    seed: int,
    checkpoint_id: str,
    checkpoint_path: Path,
) -> dict[str, Any]:
    manifest = _load_json(evidence_dir / "r26_windows" / "collector_manifest.json")
    if manifest.get("status") == "UNDERPOWERED":
        raise FamilyUnderpoweredError(f"{arm}/seed{seed} R26 collection is underpowered")
    if manifest.get("status") != "OK":
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 collection status is invalid")
    exact = {
        "base_seed": seed,
        "checkpoint_id": checkpoint_id,
        "checkpoint_update": FINAL_UPDATE,
        "skill_interval": 10,
        "episode_max_steps": 500,
        "device": "cuda",
        "policy_parameters_unchanged": True,
    }
    for name, expected in exact.items():
        if manifest.get(name) != expected:
            raise FamilyEvidenceError(
                f"{arm}/seed{seed} collector {name} drifted from {expected!r}"
            )
    if not _same_path(manifest.get("checkpoint"), checkpoint_path):
        raise FamilyEvidenceError(f"{arm}/seed{seed} collector checkpoint path drifted")
    if manifest.get("reset_seeds") != list(range(seed, seed + 64)):
        raise FamilyEvidenceError(f"{arm}/seed{seed} collector reset seeds drifted")
    stats = manifest.get("stats")
    if not isinstance(stats, Mapping) or int(stats.get("resets", -1)) != 64:
        raise FamilyEvidenceError(f"{arm}/seed{seed} collector did not complete 64 resets")
    sidecar = manifest.get("r28_sidecar")
    if not isinstance(sidecar, Mapping) or sidecar.get("enabled") is not True:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R28 sidecar was not enabled")
    if sidecar.get("schema") != "r28-g1-natural-sidecar-v1":
        raise FamilyEvidenceError(f"{arm}/seed{seed} R28 sidecar schema drifted")
    metadata = manifest.get("checkpoint_metadata")
    if not isinstance(metadata, Mapping):
        raise FamilyEvidenceError(f"{arm}/seed{seed} collector checkpoint metadata is missing")
    if int(metadata.get("total_steps", -1)) != FINAL_TOTAL_STEPS or int(
        metadata.get("update_idx", -1)
    ) != FINAL_UPDATE:
        raise FamilyEvidenceError(f"{arm}/seed{seed} collector read the wrong exposure")
    continuation = metadata.get("r28_g1")
    if not isinstance(continuation, Mapping) or continuation.get("arm") != arm:
        raise FamilyEvidenceError(f"{arm}/seed{seed} collector arm identity drifted")
    return manifest


def validate_r26_report(
    report: Mapping[str, Any],
    *,
    arm: str,
    seed: int,
    checkpoint_id: str,
) -> set[int]:
    gate = report.get("gate")
    if not isinstance(gate, Mapping):
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 gate is missing")
    status = str(gate.get("status"))
    if status == "UNDERPOWERED" or report.get("underpowered") is True:
        raise FamilyUnderpoweredError(f"{arm}/seed{seed} R26 analysis is underpowered")
    if status == "INVALID" or report.get("valid") is not True:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 analysis is invalid")
    if status not in {"PASS", "MIXED", "FAIL"}:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 status {status!r} is unknown")
    if report.get("checkpoint_id") != checkpoint_id or int(
        report.get("checkpoint_update", -1)
    ) != FINAL_UPDATE:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 checkpoint identity drifted")
    if report.get("seeds") != R26_SEEDS:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 fit/bootstrap seeds drifted")
    thresholds = report.get("thresholds")
    if not isinstance(thresholds, Mapping) or float(
        thresholds.get("accuracy_gain_min", float("nan"))
    ) != 0.05 or float(
        thresholds.get("normalized_label_entropy_min", float("nan"))
    ) != 0.8:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 frozen thresholds drifted")
    split = report.get("split")
    if not isinstance(split, Mapping) or int(split.get("seed", -1)) != R26_SEEDS["split"]:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 split identity drifted")
    test_resets = {int(item) for item in split.get("test_reset_ids", [])}
    if test_resets != EXPECTED_TEST_RESETS:
        raise FamilyEvidenceError(f"{arm}/seed{seed} R26 test reset set drifted")
    heldout = report.get("heldout_row_correctness")
    if not isinstance(heldout, list) or not heldout:
        raise FamilyEvidenceError(f"{arm}/seed{seed} lacks held-out row correctness")
    observed_resets: set[int] = set()
    for index, row in enumerate(heldout):
        if not isinstance(row, Mapping):
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out row is malformed")
        if int(row.get("test_row", -1)) != index:
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out row order drifted")
        if type(row.get("full_correct")) is not bool or type(
            row.get("prior_correct")
        ) is not bool:
            raise FamilyEvidenceError(f"{arm}/seed{seed} correctness values are not boolean")
        reset_id = int(row.get("reset_id", -1))
        observed_resets.add(reset_id)
        if reset_id not in test_resets or int(row.get("reset_seed", -1)) != seed + reset_id:
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out reset identity drifted")
        if row.get("checkpoint_id") != checkpoint_id or int(
            row.get("checkpoint_update", -1)
        ) != FINAL_UPDATE:
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out checkpoint drifted")
        if int(row.get("env_id", -1)) != 0:
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out env identity drifted")
        if not 0 <= int(row.get("agent_id", -1)) < N_AGENTS:
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out agent identity drifted")
        if not 0 <= int(row.get("duration_idx", -1)) < len(DURATION_STEPS):
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out duration drifted")
        if not 0 <= int(row.get("label", -1)) < N_SKILLS:
            raise FamilyEvidenceError(f"{arm}/seed{seed} held-out label drifted")
    if observed_resets != test_resets:
        raise FamilyEvidenceError(f"{arm}/seed{seed} held-out reset coverage is incomplete")
    return test_resets


def analyze_family(run_root: Path, scorer_path: Path, device: torch.device) -> dict[str, Any]:
    reports: dict[tuple[str, int], dict[str, Any]] = {}
    sidecars: dict[tuple[str, int], dict[str, Any]] = {}
    guards: dict[tuple[str, int], dict[str, float]] = {}
    tasks: dict[tuple[str, int], dict[str, float]] = {}
    validate_execution_contract(run_root, scorer_path)
    heads, means, variances, thresholds = _load_scorer(scorer_path, device)
    canonical_manifest: dict[str, Any] | None = None
    canonical_identity = ""
    for arm in ARMS:
        for seed in SEEDS:
            run_dir = run_root / "runs" / arm / f"seed{seed}"
            checkpoint_id, manifest = validate_run_identity(
                run_dir,
                arm=arm,
                seed=seed,
                scorer_path=scorer_path,
            )
            normalized_manifest = normalized_run_manifest(manifest)
            if canonical_manifest is None:
                canonical_manifest = normalized_manifest
                canonical_identity = f"{arm}/seed{seed}"
            elif normalized_manifest != canonical_manifest:
                raise FamilyEvidenceError(
                    f"{arm}/seed{seed} normalized run manifest differs from "
                    f"{canonical_identity} outside registered seed/arm/log-path fields"
                )
            evidence_dir = run_root / "evidence" / arm / f"seed{seed}"
            validate_collection_manifest(
                evidence_dir,
                arm=arm,
                seed=seed,
                checkpoint_id=checkpoint_id,
                checkpoint_path=run_dir / "standalone_process_core_final.pt",
            )
            report = _load_json(evidence_dir / "r26_analysis" / "r26_g1_behavior.json")
            reports[(arm, seed)] = report
            test_resets = validate_r26_report(
                report,
                arm=arm,
                seed=seed,
                checkpoint_id=checkpoint_id,
            )
            sidecars[(arm, seed)] = score_sidecar(
                evidence_dir / "r26_windows" / "r28_sidecar",
                test_reset_ids=test_resets,
                heads=heads,
                support_means=means,
                support_variances=variances,
                support_thresholds=thresholds,
                device=device,
                expected_seed=seed,
                expected_checkpoint_id=checkpoint_id,
            )
            guards[(arm, seed)] = training_guard_summary(run_dir, arm=arm)
            tasks[(arm, seed)] = final_task_summary(run_dir)

    r26_rows = r26_cluster_rows(reports)
    r26_interval = bootstrap_statistic(
        r26_rows,
        statistic=_r26_delta,
        seed=R26_BOOTSTRAP_SEED,
    )
    real_sidecar_clusters: list[dict[str, float]] = []
    for seed in SEEDS:
        for row in sidecars[("real_reward", seed)]["clusters"]:
            real_sidecar_clusters.append({"seed": float(seed), **row})
    s_real_interval = bootstrap_statistic(
        real_sidecar_clusters,
        statistic=lambda rows: _pooled_cluster_mean(rows, "s_real_sum"),
        seed=S_REAL_BOOTSTRAP_SEED,
    )
    s_delta_interval = bootstrap_statistic(
        real_sidecar_clusters,
        statistic=lambda rows: _pooled_cluster_mean(rows, "s_delta_sum"),
        seed=S_DELTA_BOOTSTRAP_SEED,
    )

    natural_pass_counts = {
        arm: sum(
            str(reports[(arm, seed)].get("gate", {}).get("status")) == "PASS"
            for seed in SEEDS
        )
        for arm in ARMS
    }
    entropies = {
        str(seed): float(reports[("real_reward", seed)].get("normalized_label_entropy", 0.0))
        for seed in SEEDS
    }
    safety: dict[str, Any] = {}
    safety_ok = True
    for seed in SEEDS:
        probe = tasks[("probe_only", seed)]
        sham = tasks[("sham_reward", seed)]
        control_arm = (
            "probe_only"
            if probe["return_mean"] >= sham["return_mean"]
            else "sham_reward"
        )
        control = tasks[(control_arm, seed)]
        real = tasks[("real_reward", seed)]
        return_regression = (
            control["return_mean"] - real["return_mean"]
        ) / max(abs(control["return_mean"]), 1e-8)
        zero_worsening = (
            real["zero_throughput_episode_fraction"]
            - control["zero_throughput_episode_fraction"]
        )
        seed_ok = return_regression <= 0.10 and zero_worsening <= 0.10
        safety_ok = safety_ok and seed_ok
        safety[str(seed)] = {
            "control_arm": control_arm,
            "control_return": control["return_mean"],
            "real_return": real["return_mean"],
            "return_regression_fraction": return_regression,
            "control_zero_throughput_episode_fraction": control[
                "zero_throughput_episode_fraction"
            ],
            "real_zero_throughput_episode_fraction": real[
                "zero_throughput_episode_fraction"
            ],
            "zero_throughput_worsening": zero_worsening,
            "pass": seed_ok,
        }

    guard_ok = all(
        row["support_kill_switch_events"] == 0.0
        and row["ratio_kill_switch_events"] == 0.0
        and row["max_reward_env_ratio"] <= 0.05
        for row in guards.values()
    )
    ood_ok = all(row["ood_fraction"] <= 0.20 for row in sidecars.values())
    checks = {
        "natural_real_at_least_two": natural_pass_counts["real_reward"] >= 2,
        "natural_probe_fewer_than_two": natural_pass_counts["probe_only"] < 2,
        "natural_sham_fewer_than_two": natural_pass_counts["sham_reward"] < 2,
        "r26_delta_estimate_at_least_005": float(r26_interval["estimate"]) >= 0.05,
        "r26_delta_lower_above_zero": float(r26_interval["lower"]) > 0.0,
        "s_real_lower_above_zero": float(s_real_interval["lower"]) > 0.0,
        "s_real_minus_sham_lower_above_zero": float(s_delta_interval["lower"]) > 0.0,
        "all_sidecar_ood_at_most_020": ood_ok,
        "all_reward_guards_clean": guard_ok,
        "real_label_entropy_at_least_080": all(value >= 0.80 for value in entropies.values()),
        "task_safety_all_seeds": safety_ok,
    }
    if all(checks.values()):
        status = "PASS"
    elif (
        natural_pass_counts["real_reward"] > 0
        and float(s_real_interval["estimate"]) > 0.0
        and float(s_delta_interval["estimate"]) > 0.0
    ):
        status = "MIXED"
    else:
        status = "FAIL"
    return {
        "experiment_id": "EXP-20260713-r28-g1-causal-skill-forcing-reward",
        "status": status,
        "classification": status,
        "run_root": str(run_root),
        "scorer_path": str(scorer_path),
        "device": str(device),
        "arms": list(ARMS),
        "seeds": list(SEEDS),
        "bootstrap_reps": BOOTSTRAP_REPS,
        "natural_pass_counts": natural_pass_counts,
        "r26_full_minus_prior_delta": r26_interval,
        "r28_s_real": s_real_interval,
        "r28_s_real_minus_sham": s_delta_interval,
        "sidecars": {
            f"{arm}/seed{seed}": sidecars[(arm, seed)]
            for arm in ARMS
            for seed in SEEDS
        },
        "training_guards": {
            f"{arm}/seed{seed}": guards[(arm, seed)]
            for arm in ARMS
            for seed in SEEDS
        },
        "task_safety": safety,
        "real_normalized_label_entropy": entropies,
        "checks": checks,
        "next_action": {
            "PASS": "design one separate long-run verification; do not promote team or async claims",
            "FAIL": "retire this forcing target and complete the R26/R27/R28 failure review",
            "MIXED": "review one causal disagreement; no new module or long run",
        }[status],
    }


def write_reports(output_dir: Path, result: Mapping[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "r28_g1_family.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# R28-G1 Frozen Family Decision",
        "",
        f"- Status: **{result.get('status', 'INVALID')}**",
        f"- R26 pass counts: `{json.dumps(result.get('natural_pass_counts', {}), sort_keys=True)}`",
        f"- R26 delta: `{json.dumps(result.get('r26_full_minus_prior_delta', {}), sort_keys=True)}`",
        f"- R28 s_real: `{json.dumps(result.get('r28_s_real', {}), sort_keys=True)}`",
        f"- R28 s_real-s_sham: `{json.dumps(result.get('r28_s_real_minus_sham', {}), sort_keys=True)}`",
        "",
        "## Checks",
        "",
    ]
    for name, passed in result.get("checks", {}).items():
        lines.append(f"- {'PASS' if passed else 'FAIL'}: `{name}`")
    lines.extend(["", "## Next action", "", str(result.get("next_action", ""))])
    (output_dir / "r28_g1_family.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run_root", required=True)
    parser.add_argument("--scorer_path", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--device", default="cuda")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("R28-G1 family analysis requires CUDA")
    try:
        result = analyze_family(Path(args.run_root), Path(args.scorer_path), device)
    except FamilyUnderpoweredError as exc:
        result = {
            "experiment_id": "EXP-20260713-r28-g1-causal-skill-forcing-reward",
            "status": "UNDERPOWERED",
            "classification": "UNDERPOWERED",
            "error": str(exc),
            "next_action": "repeat support collection only with the frozen target and thresholds",
        }
    except FamilyEvidenceError as exc:
        result = {
            "experiment_id": "EXP-20260713-r28-g1-causal-skill-forcing-reward",
            "status": "INVALID",
            "classification": "INVALID",
            "error": str(exc),
            "next_action": "repair the evidence path/instrument and repeat the unchanged gate once",
        }
    except (
        KeyError,
        TypeError,
        ValueError,
        OSError,
        pickle.UnpicklingError,
        zipfile.BadZipFile,
        R28G1ContractError,
    ) as exc:
        result = {
            "experiment_id": "EXP-20260713-r28-g1-causal-skill-forcing-reward",
            "status": "INVALID",
            "classification": "INVALID",
            "error": f"{type(exc).__name__}: {exc}",
            "next_action": "repair the evidence path/instrument and repeat the unchanged gate once",
        }
    write_reports(Path(args.output_dir), result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

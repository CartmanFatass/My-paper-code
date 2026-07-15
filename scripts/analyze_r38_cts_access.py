"""Evaluate and decide the registered R38 CTS environment-access gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260715-r38-cts-access"
CONFIG_MODULE = "ha_ctse_process.config_r38_two_timescale_sparse"
SCENARIO = "cooperative_two_timescale_sparse"
TRAIN_SEED = 39_031
TOTAL_TIMESTEPS = 320_000
EXPECTED_UPDATES = 100
RESET_SEEDS = tuple(range(139_031, 139_287))
ACTION_RNG_SEED = 49_031
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 59_031
R38_CTS_METRIC_FIELDS = (
    "r38_short_duty_complete",
    "r38_long_duty_complete",
    "r38_full_cycle_success",
    "r38_anchor_streak_max",
    "r38_shuttle_stage_max",
    "r38_sparse_reward",
)
INDICATOR_FIELDS = R38_CTS_METRIC_FIELDS[:3]
RANDOM_CSV_FIELDS = (
    "episode",
    "reset_seed",
    "reward",
    "length",
    "terminated_flag",
    "truncated_flag",
    *R38_CTS_METRIC_FIELDS,
)


def paired_bootstrap_ci(mappo, random, *, repetitions: int, seed: int):
    paired = np.asarray(mappo, dtype=np.float64) - np.asarray(random, dtype=np.float64)
    if paired.shape != (256,) or not np.all(np.isfinite(paired)):
        raise ValueError("paired bootstrap requires exactly 256 finite episode pairs")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, paired.size, size=(repetitions, paired.size))
    means = paired[draws].mean(axis=1)
    return (
        float(paired.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


def decide_result(m0: bool, m1: bool, m2: bool) -> str:
    if not m0:
        return "INVALID_R38_IMPLEMENTATION"
    if not m1 or not m2:
        return "FAIL_R38_CTS_ACCESS"
    return "PASS_R38_CTS_ACCESS"


def add_reason(reasons: list[str], message: str) -> None:
    if message not in reasons:
        reasons.append(message)


def require_nonnegative_integer(value: object, *, field: str) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field} must be a finite nonnegative integer, got {value!r}"
        ) from exc
    if not math.isfinite(number) or number < 0.0 or not number.is_integer():
        raise ValueError(
            f"{field} must be a finite nonnegative integer, got {value!r}"
        )
    return int(number)


def validated_integer_column(
    rows: list[dict[str, float]],
    field: str,
    *,
    label: str,
    reasons: list[str],
) -> list[int | None]:
    values: list[int | None] = []
    for row_index, row in enumerate(rows):
        context = f"{label} row {row_index} {field}"
        try:
            values.append(
                require_nonnegative_integer(row.get(field), field=context)
            )
        except ValueError as exc:
            add_reason(reasons, str(exc))
            values.append(None)
    return values


def validate_zero_count_fields(
    rows: list[dict[str, float]],
    fields: tuple[str, ...],
    *,
    label: str,
    reasons: list[str],
) -> dict[str, int]:
    totals = {field: 0 for field in fields}
    for row_index, row in enumerate(rows):
        for field in fields:
            context = f"{label} row {row_index} {field}"
            try:
                count = require_nonnegative_integer(row.get(field), field=context)
            except ValueError as exc:
                add_reason(reasons, str(exc))
                continue
            totals[field] += count
            if count != 0:
                add_reason(reasons, f"{context}={count} != 0")
    return totals


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def load_numeric_csv(
    path: Path, *, text_fields: tuple[str, ...] = ()
) -> tuple[list[dict[str, float]], tuple[str, ...]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        if not fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        for row_number, raw in enumerate(reader, start=2):
            row: dict[str, float] = {}
            for field, value in raw.items():
                if field is None or field in text_fields or value in (None, ""):
                    continue
                try:
                    number = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"non-numeric metric {field!r} at {path}:{row_number}"
                    ) from exc
                if not math.isfinite(number):
                    raise ValueError(
                        f"non-finite metric {field!r} at {path}:{row_number}"
                    )
                row[field] = number
            rows.append(row)
    return rows, fieldnames


def write_numeric_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(RANDOM_CSV_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in RANDOM_CSV_FIELDS})


def resolved_path(value: object, repo_root: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def require_fields(
    rows: list[dict[str, float]],
    fieldnames: tuple[str, ...],
    required: tuple[str, ...],
    label: str,
    reasons: list[str],
) -> None:
    for field in required:
        if field not in fieldnames:
            add_reason(reasons, f"{label} CSV is missing field {field}")
        elif any(field not in row for row in rows):
            add_reason(reasons, f"{label} CSV has a row missing field {field}")


def values_match(actual: object, expected: object) -> bool:
    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual is expected
    if isinstance(expected, float):
        try:
            return math.isclose(
                float(actual), expected, rel_tol=1e-12, abs_tol=1e-12
            )
        except (TypeError, ValueError):
            return False
    return actual == expected


def check_expected(
    payload: object,
    expected: dict[str, object],
    label: str,
    reasons: list[str],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        add_reason(reasons, f"{label} is not an object")
        return {}
    for field, expected_value in expected.items():
        actual = payload.get(field)
        if isinstance(expected_value, int) and not isinstance(expected_value, bool):
            try:
                actual_integer = require_nonnegative_integer(
                    actual, field=f"{label} {field}"
                )
            except ValueError as exc:
                add_reason(reasons, str(exc))
                continue
            if actual_integer != expected_value:
                add_reason(
                    reasons,
                    f"{label} {field}={actual_integer!r} != {expected_value!r}",
                )
            continue
        if not values_match(actual, expected_value):
            add_reason(
                reasons,
                f"{label} {field}={actual!r} != {expected_value!r}",
            )
    return payload


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    import torch

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, dict):
        raise ValueError(f"checkpoint root is not an object: {path}")
    return payload


def check_optimizer_lr(
    checkpoint: dict[str, Any],
    field: str,
    expected: float,
    label: str,
    reasons: list[str],
) -> None:
    optimizer = checkpoint.get(field)
    groups = optimizer.get("param_groups") if isinstance(optimizer, dict) else None
    if not isinstance(groups, list) or not groups:
        add_reason(reasons, f"{label} checkpoint is missing {field} parameter groups")
        return
    lrs = [group.get("lr") for group in groups if isinstance(group, dict)]
    if len(lrs) != len(groups) or any(not values_match(lr, expected) for lr in lrs):
        add_reason(reasons, f"{label} checkpoint {field} learning rates are not {expected}")


EXPECTED_ALGORITHM_CONFIG = {
    "algorithm": "r38_cts_constant_code_recurrent_mappo",
    "constant_skill_no_high": True,
    "r38_world_size": 6.0,
    "r38_action_scale": 0.5,
    "r38_zone_radius": 0.75,
    "r38_anchor_required_steps": 40,
    "r38_shuttle_stages": 4,
    "alice_bob_semantic_reward_enabled": False,
    "aem_joint_novelty_enabled": False,
    "r31_effect_mode": "off",
    "transition_skill_reward_coef": 0.0,
    "process_reward_injection": "none",
    "outcome_residual_injection": "none",
    "topology_role_injection": "none",
    "topology_potential_injection": "none",
    "skill_effect_reward_injection": "none",
    "skill_force_reward_injection": "none",
    "lr_discoverer_actor": 3e-4,
    "lr_discoverer_critic": 3e-4,
    "use_recurrent_low_level": True,
    "use_centralized_low_value": True,
    "use_low_value_norm": True,
    "low_rnn_hidden_size": 64,
    "low_sequence_length": 20,
    "low_sequence_batch_size": 64,
    "low_ppo_epochs": 5,
    "low_gae_lambda": 0.95,
    "low_value_clip": 0.2,
    "low_value_loss_coef": 1.0,
    "low_clip_epsilon": 0.2,
    "low_max_grad_norm": 0.5,
}

EXPECTED_TRAINING_CONFIG = {
    "gamma": 0.99,
    "low_gae_lambda": 0.95,
    "low_clip_epsilon": 0.2,
    "low_value_clip": 0.2,
    "low_value_loss_coef": 1.0,
    "low_entropy_coef": 0.01,
    "low_max_grad_norm": 0.5,
    "low_sequence_length": 20,
    "low_sequence_batch_size": 64,
    "low_ppo_epochs": 5,
    "ppo_epochs": 5,
}

EXPECTED_MODEL_CONFIG = {
    "obs_dim": 10,
    "state_dim": 10,
    "action_dim": 2,
    "n_agents": 2,
    "n_uavs": 2,
}

EXPECTED_PHYSICAL_CONFIG = {
    "scenario": SCENARIO,
    "max_steps": 200,
    "episode_length": 200,
    "n_agents": 2,
    "n_uavs": 2,
}


def validate_manifest_config(
    manifest: dict[str, Any], label: str, reasons: list[str]
) -> None:
    check_expected(
        manifest.get("algorithm_config"),
        EXPECTED_ALGORITHM_CONFIG,
        f"{label} algorithm_config",
        reasons,
    )
    check_expected(
        manifest.get("training_config"),
        EXPECTED_TRAINING_CONFIG,
        f"{label} training_config",
        reasons,
    )
    check_expected(
        manifest.get("model_config"),
        EXPECTED_MODEL_CONFIG,
        f"{label} model_config",
        reasons,
    )
    check_expected(
        manifest.get("physical_env_config"),
        EXPECTED_PHYSICAL_CONFIG,
        f"{label} physical_env_config",
        reasons,
    )
    check_expected(
        manifest.get("env_runtime_spec"),
        {"obs_dim": 10, "state_dim": 10, "action_dim": 2, "n_uavs": 2},
        f"{label} env_runtime_spec",
        reasons,
    )
    check_expected(
        manifest.get("agent_runtime_spec"),
        {
            "obs_dim": 10,
            "action_dim": 2,
            "n_agents": 2,
            "high_controller": "r30_fixed_clock_ar_edit",
            "constant_skill_no_high": True,
            "device": "cuda",
            "use_recurrent_low_level": True,
            "low_rnn_hidden_size": 64,
        },
        f"{label} agent_runtime_spec",
        reasons,
    )


def evaluate_uniform_random() -> tuple[list[dict[str, float]], dict[str, Any], list[str]]:
    from ha_ctse_process.config_r38_two_timescale_sparse import Config
    from ha_ctse_process.env_factory import EnvSpec, make_env

    env = make_env(
        Config,
        EnvSpec(scenario=SCENARIO, seed=RESET_SEEDS[0], scale_mode="eval"),
    )()
    action_rng = np.random.default_rng(49_031)
    rows: list[dict[str, float]] = []
    reasons: list[str] = []
    action_count = 0
    all_actions_finite = True
    all_step_metrics_finite = True
    max_abs_intrinsic_reward = 0.0
    try:
        for episode, reset_seed in enumerate(RESET_SEEDS):
            env.reset(seed=reset_seed)
            episode_reward = 0.0
            episode_length = 0
            terminated = False
            truncated = False
            final_metrics = {field: float("nan") for field in R38_CTS_METRIC_FIELDS}
            while not (terminated or truncated):
                actions = action_rng.uniform(-1.0, 1.0, size=(2, 2)).astype(np.float32)
                action_count += actions.size
                if not np.all(np.isfinite(actions)):
                    all_actions_finite = False
                    add_reason(reasons, "uniform-random evaluator produced a non-finite action")
                _, reward, terminated, truncated, info = env.step(actions)
                episode_length += 1
                reward_value = float(reward)
                if not math.isfinite(reward_value):
                    all_step_metrics_finite = False
                    add_reason(reasons, "uniform-random evaluator produced non-finite reward")
                else:
                    episode_reward += reward_value
                reward_info = info.get("reward_info") if isinstance(info, dict) else None
                if not isinstance(reward_info, dict):
                    reward_info = {}
                    add_reason(reasons, "uniform-random evaluator omitted reward_info")
                for field in R38_CTS_METRIC_FIELDS:
                    try:
                        value = float(reward_info[field])
                    except (KeyError, TypeError, ValueError):
                        value = float("nan")
                    if not math.isfinite(value):
                        all_step_metrics_finite = False
                        add_reason(reasons, f"uniform-random evaluator has non-finite {field}")
                    final_metrics[field] = value
                try:
                    intrinsic = float(reward_info["intrinsic_reward"])
                except (KeyError, TypeError, ValueError):
                    intrinsic = float("nan")
                if not math.isfinite(intrinsic):
                    all_step_metrics_finite = False
                    add_reason(reasons, "uniform-random evaluator has non-finite intrinsic_reward")
                else:
                    max_abs_intrinsic_reward = max(max_abs_intrinsic_reward, abs(intrinsic))
                    if abs(intrinsic) > 1e-12:
                        add_reason(reasons, "uniform-random evaluator has nonzero intrinsic reward")
                full = final_metrics["r38_full_cycle_success"]
                if math.isfinite(reward_value) and abs(reward_value) > 1e-12 and full != 1.0:
                    add_reason(reasons, "uniform-random evaluator paid reward before full success")
                if episode_length >= 200 and not (terminated or truncated):
                    add_reason(reasons, "uniform-random episode did not end at the 200-step horizon")
                    break
            rows.append(
                {
                    "episode": float(episode),
                    "reset_seed": float(reset_seed),
                    "reward": float(episode_reward),
                    "length": float(episode_length),
                    "terminated_flag": float(bool(terminated)),
                    "truncated_flag": float(bool(truncated)),
                    **final_metrics,
                }
            )
    finally:
        env.close()
    audit = {
        "action_rng_seed": ACTION_RNG_SEED,
        "action_draw_count": action_count,
        "single_continuous_action_rng": True,
        "all_actions_finite": all_actions_finite,
        "all_step_metrics_finite": all_step_metrics_finite,
        "max_abs_intrinsic_reward": max_abs_intrinsic_reward,
    }
    return rows, audit, reasons


def validate_policy_rows(
    rows: list[dict[str, float]],
    fieldnames: tuple[str, ...],
    label: str,
    reasons: list[str],
    *,
    mappo: bool,
) -> dict[str, Any]:
    required = (
        "episode",
        "reset_seed",
        "reward",
        "length",
        "terminated_flag",
        "truncated_flag",
        *R38_CTS_METRIC_FIELDS,
    )
    if mappo:
        required = ("total_steps", "action_mode_code", *required)
    require_fields(rows, fieldnames, required, label, reasons)
    if len(rows) != 256:
        add_reason(reasons, f"{label} has {len(rows)} rows instead of 256")
    episodes = validated_integer_column(
        rows, "episode", label=label, reasons=reasons
    )
    reset_order = validated_integer_column(
        rows, "reset_seed", label=label, reasons=reasons
    )
    if episodes != list(range(256)):
        add_reason(reasons, f"{label} episode order is not exactly 0..255")
    if reset_order != list(RESET_SEEDS):
        add_reason(reasons, f"{label} reset order is not exactly registered")
    valid_reset_seeds = [value for value in reset_order if value is not None]
    if len(set(valid_reset_seeds)) != 256 or set(valid_reset_seeds) != set(RESET_SEEDS):
        add_reason(reasons, f"{label} does not have 256 unique registered reset seeds")
    if mappo:
        total_steps = validated_integer_column(
            rows, "total_steps", label=label, reasons=reasons
        )
        if any(value != TOTAL_TIMESTEPS for value in total_steps):
            add_reason(reasons, "MAPPO evaluation is not entirely at 320000 steps")
        if any(abs(row.get("action_mode_code", -1.0) - 1.0) > 1e-12 for row in rows):
            add_reason(reasons, "MAPPO evaluation is not entirely stochastic")

    terminal_semantics_valid = True
    reward_semantics_valid = True
    metric_ranges_valid = True
    for episode, row in enumerate(rows):
        if any(field not in row for field in required):
            continue
        reward = row["reward"]
        try:
            length = require_nonnegative_integer(
                row["length"], field=f"{label} row {episode} length"
            )
        except ValueError as exc:
            add_reason(reasons, str(exc))
            length = None
            terminal_semantics_valid = False
        terminated = row["terminated_flag"]
        truncated = row["truncated_flag"]
        short = row["r38_short_duty_complete"]
        long = row["r38_long_duty_complete"]
        full = row["r38_full_cycle_success"]
        sparse = row["r38_sparse_reward"]
        anchor = row["r38_anchor_streak_max"]
        shuttle = row["r38_shuttle_stage_max"]
        if any(value not in (0.0, 1.0) for value in (short, long, full, sparse, terminated, truncated)):
            metric_ranges_valid = False
        if not (0.0 <= anchor <= 200.0 and float(anchor).is_integer()):
            metric_ranges_valid = False
        if not (0.0 <= shuttle <= 4.0 and float(shuttle).is_integer()):
            metric_ranges_valid = False
        if abs(reward - full) > 1e-12 or abs(sparse - full) > 1e-12:
            reward_semantics_valid = False
        if full == 1.0:
            if (
                terminated != 1.0
                or truncated != 0.0
                or length is None
                or not (1 <= length <= 200)
            ):
                terminal_semantics_valid = False
        else:
            if terminated != 0.0 or truncated != 1.0 or length != 200:
                terminal_semantics_valid = False
        if full == 1.0 and (short != 1.0 or long != 1.0):
            metric_ranges_valid = False
        if terminated == 1.0 and truncated == 1.0:
            terminal_semantics_valid = False
    if not reward_semantics_valid:
        add_reason(reasons, f"{label} reward is not exactly the full-success indicator")
    if not terminal_semantics_valid:
        add_reason(reasons, f"{label} success termination or failure truncation semantics are wrong")
    if not metric_ranges_valid:
        add_reason(reasons, f"{label} CTS metric ranges or implications are invalid")
    return {
        "row_count": len(rows),
        "unique_reset_seed_count": len(set(valid_reset_seeds)),
        "reset_order_registered": reset_order == list(RESET_SEEDS),
        "reward_semantics_valid": reward_semantics_valid,
        "terminal_semantics_valid": terminal_semantics_valid,
        "metric_ranges_valid": metric_ranges_valid,
    }


def finite_mean(rows: list[dict[str, float]], field: str) -> float | None:
    values = np.asarray([row.get(field, np.nan) for row in rows], dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)):
        return None
    return float(values.mean())


def finite_sum(rows: list[dict[str, float]], field: str) -> float | None:
    values = np.asarray([row.get(field, np.nan) for row in rows], dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)):
        return None
    return float(values.sum())


def finite_max(rows: list[dict[str, float]], field: str) -> float | None:
    values = np.asarray([row.get(field, np.nan) for row in rows], dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)):
        return None
    return float(values.max())


def summarize_policy(rows: list[dict[str, float]]) -> dict[str, Any]:
    terminated_sum = finite_sum(rows, "terminated_flag")
    truncated_sum = finite_sum(rows, "truncated_flag")
    full_success_sum = finite_sum(rows, "r38_full_cycle_success")
    try:
        first_reset_seed = (
            require_nonnegative_integer(
                rows[0].get("reset_seed"), field="summary first reset seed"
            )
            if rows
            else None
        )
    except ValueError:
        first_reset_seed = None
    try:
        last_reset_seed = (
            require_nonnegative_integer(
                rows[-1].get("reset_seed"), field="summary last reset seed"
            )
            if rows
            else None
        )
    except ValueError:
        last_reset_seed = None
    try:
        terminated_count = (
            require_nonnegative_integer(
                terminated_sum, field="summary terminated count"
            )
            if terminated_sum is not None
            else None
        )
    except ValueError:
        terminated_count = None
    try:
        truncated_count = (
            require_nonnegative_integer(
                truncated_sum, field="summary truncated count"
            )
            if truncated_sum is not None
            else None
        )
    except ValueError:
        truncated_count = None
    try:
        full_success_count = (
            require_nonnegative_integer(
                full_success_sum, field="summary full success count"
            )
            if full_success_sum is not None
            else None
        )
    except ValueError:
        full_success_count = None
    return {
        "evaluation_episodes": len(rows),
        "reset_seed_first": first_reset_seed,
        "reset_seed_last": last_reset_seed,
        "mean_reward": finite_mean(rows, "reward"),
        "mean_length": finite_mean(rows, "length"),
        "terminated_count": terminated_count,
        "truncated_count": truncated_count,
        "rates": {field: finite_mean(rows, field) for field in INDICATOR_FIELDS},
        "full_success_count": full_success_count,
        "anchor_streak_max": finite_max(rows, "r38_anchor_streak_max"),
        "shuttle_stage_max": finite_max(rows, "r38_shuttle_stage_max"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    mappo_root = run_root / "runs" / "constant_code_mappo" / "seed39031"
    neutral_init_checkpoint = (
        run_root
        / "init"
        / "neutral_cts_seed39031"
        / "standalone_process_core_final.pt"
    )
    final_checkpoint = mappo_root / "standalone_process_core_final.pt"
    invalid_reasons: list[str] = []

    random_rows, random_action_audit, random_reasons = evaluate_uniform_random()
    for reason in random_reasons:
        add_reason(invalid_reasons, reason)
    random_csv_path = run_root / "result" / "r38_uniform_random_eval_episodes.csv"
    write_numeric_csv(random_csv_path, random_rows)

    train_rows: list[dict[str, float]] = []
    train_fields: tuple[str, ...] = ()
    mappo_rows: list[dict[str, float]] = []
    mappo_fields: tuple[str, ...] = ()
    manifest: dict[str, Any] = {}
    init_manifest: dict[str, Any] = {}
    checkpoint: dict[str, Any] = {}
    init_checkpoint: dict[str, Any] = {}
    for label, loader, path in (
        (
            "training updates",
            lambda target: load_numeric_csv(target),
            mappo_root / "metrics" / "train_updates.csv",
        ),
        (
            "MAPPO evaluation",
            lambda target: load_numeric_csv(target, text_fields=("checkpoint",)),
            mappo_root / "metrics" / "eval_episodes.csv",
        ),
        ("training manifest", load_json, mappo_root / "metadata" / "run_manifest.json"),
        (
            "neutral manifest",
            load_json,
            neutral_init_checkpoint.parent / "metadata" / "run_manifest.json",
        ),
        ("final checkpoint", load_checkpoint, final_checkpoint),
        ("neutral checkpoint", load_checkpoint, neutral_init_checkpoint),
    ):
        try:
            loaded = loader(path)
        except Exception as exc:
            add_reason(invalid_reasons, f"unable to read {label}: {exc}")
            continue
        if label == "training updates":
            train_rows, train_fields = loaded
        elif label == "MAPPO evaluation":
            mappo_rows, mappo_fields = loaded
        elif label == "training manifest":
            manifest = loaded
        elif label == "neutral manifest":
            init_manifest = loaded
        elif label == "final checkpoint":
            checkpoint = loaded
        else:
            init_checkpoint = loaded

    if init_manifest:
        check_expected(
            init_manifest,
            {"total_steps": 0, "update_idx": 0},
            "neutral manifest",
            invalid_reasons,
        )
        init_args = check_expected(
            init_manifest.get("args"),
            {
                "config": CONFIG_MODULE,
                "scenario": SCENARIO,
                "seed": TRAIN_SEED,
                "n_agents": 2,
                "collector_backend": "sync",
                "num_envs": 1,
                "rollout_length": 200,
                "skill_interval": 10,
                "total_timesteps": 0,
                "eval_interval": 0,
                "eval_episodes": 1,
                "eval_max_steps": 200,
                "eval_action_mode": "stochastic",
                "save_interval": 0,
                "checkpoint_keep_last": 1,
                "plot_interval": 0,
                "high_controller": "r30_fixed_clock_ar_edit",
                "device": "cuda",
            },
            "neutral manifest args",
            invalid_reasons,
        )
        if init_args.get("resume_from") not in (None, ""):
            add_reason(invalid_reasons, "neutral initialization unexpectedly resumed")
        validate_manifest_config(init_manifest, "neutral manifest", invalid_reasons)

    if manifest:
        check_expected(
            manifest,
            {"total_steps": TOTAL_TIMESTEPS, "update_idx": EXPECTED_UPDATES},
            "training manifest",
            invalid_reasons,
        )
        train_args = check_expected(
            manifest.get("args"),
            {
                "config": CONFIG_MODULE,
                "scenario": SCENARIO,
                "seed": TRAIN_SEED,
                "n_agents": 2,
                "device": "cuda",
                "collector_backend": "subproc",
                "collector_start_method": "spawn",
                "num_envs": 16,
                "rollout_length": 200,
                "skill_interval": 10,
                "total_timesteps": TOTAL_TIMESTEPS,
                "eval_interval": TOTAL_TIMESTEPS,
                "eval_episodes": 256,
                "eval_action_mode": "stochastic",
                "eval_max_steps": 200,
                "save_interval": 0,
                "checkpoint_keep_last": 1,
                "plot_interval": 0,
                "high_controller": "r30_fixed_clock_ar_edit",
            },
            "training manifest args",
            invalid_reasons,
        )
        resume_path = resolved_path(train_args.get("resume_from"), repo_root)
        if resume_path != neutral_init_checkpoint.resolve():
            add_reason(
                invalid_reasons,
                f"training resume checkpoint {resume_path} != registered neutral checkpoint",
            )
        validate_manifest_config(manifest, "training manifest", invalid_reasons)

    if init_checkpoint:
        check_expected(
            init_checkpoint,
            {
                "total_steps": 0,
                "update_idx": 0,
                "config_name": CONFIG_MODULE,
                "scenario": SCENARIO,
                "n_agents": 2,
                "skill_interval": 10,
                "high_controller": "r30_fixed_clock_ar_edit",
                "use_recurrent_low_level": True,
            },
            "neutral checkpoint",
            invalid_reasons,
        )
        check_optimizer_lr(
            init_checkpoint,
            "low_actor_opt",
            3e-4,
            "neutral",
            invalid_reasons,
        )
        check_optimizer_lr(
            init_checkpoint,
            "low_critic_opt",
            3e-4,
            "neutral",
            invalid_reasons,
        )

    if checkpoint:
        check_expected(
            checkpoint,
            {
                "total_steps": TOTAL_TIMESTEPS,
                "update_idx": EXPECTED_UPDATES,
                "config_name": CONFIG_MODULE,
                "scenario": SCENARIO,
                "n_agents": 2,
                "skill_interval": 10,
                "high_controller": "r30_fixed_clock_ar_edit",
                "use_recurrent_low_level": True,
            },
            "final checkpoint",
            invalid_reasons,
        )
        check_optimizer_lr(
            checkpoint,
            "low_actor_opt",
            3e-4,
            "final",
            invalid_reasons,
        )
        check_optimizer_lr(
            checkpoint,
            "low_critic_opt",
            3e-4,
            "final",
            invalid_reasons,
        )

    required_train_fields = (
        "update",
        "total_steps",
        "low_sequence_chunks",
        "r30_high_rows",
        "r30_decision_rows",
        "process_segments",
        "low_skill_usage_entropy",
        "low_team_usage_entropy",
        "combined_intrinsic_env_ratio",
    )
    require_fields(
        train_rows,
        train_fields,
        required_train_fields,
        "training updates",
        invalid_reasons,
    )
    if len(train_rows) != EXPECTED_UPDATES:
        add_reason(
            invalid_reasons,
            f"training has {len(train_rows)} outer updates instead of {EXPECTED_UPDATES}",
        )
    update_ids = validated_integer_column(
        train_rows, "update", label="training updates", reasons=invalid_reasons
    )
    if update_ids != list(range(1, EXPECTED_UPDATES + 1)):
        add_reason(invalid_reasons, "outer update indices are not exactly 1..100")
    expected_steps = list(range(3_200, TOTAL_TIMESTEPS + 1, 3_200))
    actual_steps = validated_integer_column(
        train_rows,
        "total_steps",
        label="training updates",
        reasons=invalid_reasons,
    )
    if actual_steps != expected_steps:
        add_reason(invalid_reasons, "outer update environment-step sequence is not exact")
    low_sequence_chunks = validated_integer_column(
        train_rows,
        "low_sequence_chunks",
        label="training updates",
        reasons=invalid_reasons,
    )
    low_update_count = sum(
        value is not None and value > 0 for value in low_sequence_chunks
    )
    if low_update_count != EXPECTED_UPDATES:
        add_reason(
            invalid_reasons,
            f"low update count {low_update_count} != {EXPECTED_UPDATES}",
        )
    zero_count_totals = validate_zero_count_fields(
        train_rows,
        ("r30_high_rows", "r30_decision_rows", "process_segments"),
        label="training updates",
        reasons=invalid_reasons,
    )
    high_update_count = (
        zero_count_totals["r30_high_rows"]
        + zero_count_totals["r30_decision_rows"]
    )
    process_update_count = zero_count_totals["process_segments"]
    if any(
        abs(row.get("low_skill_usage_entropy", math.inf)) > 1e-12
        for row in train_rows
    ):
        add_reason(invalid_reasons, "active skill code was not constant")
    if any(
        abs(row.get("low_team_usage_entropy", math.inf)) > 1e-12
        for row in train_rows
    ):
        add_reason(invalid_reasons, "active team code was not constant")

    intrinsic_fields = sorted(
        field
        for field in train_fields
        if field.endswith("reward_applied_steps")
        or field.endswith("reward_active")
        or field.endswith("reward_env_ratio")
        or field
        in {
            "combined_intrinsic_env_ratio",
            "aem_bonus_applied_steps",
            "aem_bonus_sum",
            "aem_bonus_max",
        }
    )
    nonzero_intrinsic_fields = [
        field
        for field in intrinsic_fields
        if any(abs(row.get(field, 0.0)) > 1e-12 for row in train_rows)
    ]
    if nonzero_intrinsic_fields:
        add_reason(
            invalid_reasons,
            "nonzero intrinsic reward evidence: " + ",".join(nonzero_intrinsic_fields),
        )

    mappo_audit = validate_policy_rows(
        mappo_rows,
        mappo_fields,
        "MAPPO evaluation",
        invalid_reasons,
        mappo=True,
    )
    random_audit = validate_policy_rows(
        random_rows,
        RANDOM_CSV_FIELDS,
        "uniform-random evaluation",
        invalid_reasons,
        mappo=False,
    )
    mappo_reset_order = validated_integer_column(
        mappo_rows,
        "reset_seed",
        label="MAPPO evaluation",
        reasons=invalid_reasons,
    )
    random_reset_order = validated_integer_column(
        random_rows,
        "reset_seed",
        label="uniform-random evaluation",
        reasons=invalid_reasons,
    )
    reset_order_matches = mappo_reset_order == random_reset_order == list(RESET_SEEDS)
    if not reset_order_matches:
        add_reason(invalid_reasons, "MAPPO and random reset order does not match")

    m0 = not invalid_reasons
    rates: dict[str, float] = {}
    full_success_count = 0
    paired_cis: dict[str, tuple[float, float, float]] = {}
    block_successes: list[int] = []
    m1 = False
    m2 = False
    if m0:
        mappo_arrays = {
            field: np.asarray([row[field] for row in mappo_rows], dtype=np.float64)
            for field in INDICATOR_FIELDS
        }
        random_arrays = {
            field: np.asarray([row[field] for row in random_rows], dtype=np.float64)
            for field in INDICATOR_FIELDS
        }
        rates = {field: float(values.mean()) for field, values in mappo_arrays.items()}
        mappo_full = mappo_arrays["r38_full_cycle_success"]
        full_success_count = require_nonnegative_integer(
            mappo_full.sum(), field="MAPPO full success count"
        )
        paired_cis = {
            field: paired_bootstrap_ci(
                mappo_arrays[field],
                random_arrays[field],
                repetitions=BOOTSTRAP_REPETITIONS,
                seed=BOOTSTRAP_SEED,
            )
            for field in INDICATOR_FIELDS
        }
        m1 = (
            rates["r38_short_duty_complete"] >= 0.10
            and rates["r38_long_duty_complete"] >= 0.05
            and rates["r38_full_cycle_success"] > 0.10
            and full_success_count >= 26
            and all(ci[1] > 0.0 for ci in paired_cis.values())
        )
        block_successes = [
            require_nonnegative_integer(
                mappo_full[start : start + 64].sum(),
                field=f"MAPPO full success block {start // 64} count",
            )
            for start in range(0, 256, 64)
        ]
        m2 = sum(count >= 1 for count in block_successes) >= 3
    status = decide_result(m0, m1, m2)

    paired_comparison = {
        "direction": "constant_code_mappo_minus_uniform_random",
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "indicators": {
            field: {
                "estimate": ci[0],
                "lower": ci[1],
                "upper": ci[2],
            }
            for field, ci in paired_cis.items()
        },
    }
    m0_payload = {
        "passed": bool(m0),
        "invalid_reasons": invalid_reasons,
        "outer_update_count": len(train_rows),
        "low_update_count": low_update_count,
        "high_update_count": high_update_count,
        "process_update_count": process_update_count,
        "high_process_count_totals": zero_count_totals,
        "intrinsic_fields_checked": intrinsic_fields,
        "nonzero_intrinsic_fields": nonzero_intrinsic_fields,
        "mappo_evaluation": mappo_audit,
        "uniform_random_evaluation": random_audit,
        "random_action_audit": random_action_audit,
        "reset_order_matches": reset_order_matches,
    }
    m1_payload = {
        "passed": bool(m1),
        "thresholds": {
            "short_duty_rate_min": 0.10,
            "long_duty_rate_min": 0.05,
            "full_success_rate_strict_min": 0.10,
            "full_success_count_min": 26,
            "all_paired_ci_lower_strict_min": 0.0,
        },
        "mappo_rates": rates,
        "mappo_full_success_count": full_success_count,
        "paired_cis": paired_comparison["indicators"],
    }
    m2_payload = {
        "passed": bool(m2),
        "block_size": 64,
        "required_blocks_with_success": 3,
        "block_success_counts": block_successes,
    }
    if status == "PASS_R38_CTS_ACCESS":
        decision_payload = {
            "status": status,
            "conclusion": "CTS is accessible to ordinary constant-code recurrent MAPPO",
            "next_action": "register one shared-fixed-k versus per-agent-lifetime mechanism gate",
        }
    elif status == "FAIL_R38_CTS_ACCESS":
        decision_payload = {
            "status": status,
            "conclusion": "the valid CTS access gate failed M1 or M2",
            "next_action": "retire the benchmark without rescue",
        }
    else:
        decision_payload = {
            "status": status,
            "conclusion": "the implementation contract is invalid",
            "next_action": "fix only the concrete wiring defect and rerun the unchanged contract",
        }

    evaluation_contract = {
        "mappo_action_mode": "stochastic",
        "mappo_eval_episodes": 256,
        "uniform_random_action_rng_seed": ACTION_RNG_SEED,
        "uniform_random_action_distribution": "uniform[-1,1] float32 shape (2,2)",
        "paired_reset_seeds": list(RESET_SEEDS),
        "paired_bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "paired_bootstrap_seed": BOOTSTRAP_SEED,
        "repeatability_blocks": [[start, start + 63] for start in range(0, 256, 64)],
    }
    mappo_summary = summarize_policy(mappo_rows)
    mappo_summary.update(
        {
            "run_root": str(mappo_root),
            "final_checkpoint": str(final_checkpoint),
            "train_update_rows": len(train_rows),
        }
    )
    random_summary = summarize_policy(random_rows)
    random_summary.update(
        {
            "evaluation_csv": str(random_csv_path),
            "action_audit": random_action_audit,
        }
    )
    result = {
        "experiment_id": "EXP-20260715-r38-cts-access",
        "status": status,
        "scope": "single-seed environment-access gate; not algorithm efficacy evidence",
        "train_seed": 39031,
        "total_timesteps": 320000,
        "neutral_init_checkpoint": str(neutral_init_checkpoint),
        "implementation_valid": bool(m0),
        "invalid_reasons": invalid_reasons,
        "evaluation_contract": evaluation_contract,
        "policies": {"constant_code_mappo": mappo_summary, "uniform_random": random_summary},
        "paired_comparison": paired_comparison,
        "gates": {"M0": m0_payload, "M1": m1_payload, "M2": m2_payload},
        "decision": decision_payload,
    }
    result_path = run_root / "result" / "r38_cts_access.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = result_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    temporary_path.replace(result_path)
    print(result_path)


if __name__ == "__main__":
    main()

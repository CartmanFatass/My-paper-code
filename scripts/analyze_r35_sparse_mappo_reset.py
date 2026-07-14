"""Analyze the paired sparse Alice--Bob R35 reset gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean

import numpy as np


ARMS = ("constant_code_mappo", "reward_pure_r30")
CYCLE_FIELD = "alice_bob_cycle_success_rate"
COLLECTION_FIELD = "alice_bob_targets_completed"
ZERO_CYCLE_FIELD = "alice_bob_zero_cycle_episode_flag"
COVERAGE_FIELDS = (
    "alice_bob_joint_position_coverage_ratio",
    "alice_bob_joint_position_coverage",
    "alice_bob_joint_position_coverage_fraction",
    "joint_position_coverage",
)


def load_numeric_csv(path: Path) -> tuple[list[dict[str, float]], tuple[str, ...]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        for raw in reader:
            row: dict[str, float] = {}
            for key, value in raw.items():
                if key is None or value in (None, ""):
                    continue
                try:
                    number = float(value)
                except ValueError:
                    continue
                if math.isfinite(number):
                    row[key] = number
            rows.append(row)
    return rows, fieldnames


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"manifest is not an object: {path}")
    return payload


def resolved_path(value: object, base: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def find_coverage_field(fieldnames: tuple[str, ...]) -> str | None:
    return next((name for name in COVERAGE_FIELDS if name in fieldnames), None)


def all_zero(rows: list[dict[str, float]], field: str, tolerance: float = 1e-12) -> bool:
    return all(abs(float(row.get(field, 0.0))) <= tolerance for row in rows)


def summarize_arm(
    arm_root: Path,
    *,
    repo_root: Path,
    init_checkpoint: Path,
    total_timesteps: int,
    expected_updates: int,
    eval_episodes: int,
    expected_config: str,
    require_zero_high_rows: bool,
) -> tuple[dict, dict[int, dict[str, float]], list[str]]:
    train, train_fields = load_numeric_csv(arm_root / "metrics" / "train_updates.csv")
    evaluation, eval_fields = load_numeric_csv(
        arm_root / "metrics" / "eval_episodes.csv"
    )
    manifest = load_manifest(arm_root / "metadata" / "run_manifest.json")
    train.sort(key=lambda row: row.get("update", -1.0))

    reasons: list[str] = []
    latest_eval_step = max(
        (int(row.get("total_steps", -1)) for row in evaluation), default=-1
    )
    final_eval = [
        row for row in evaluation if int(row.get("total_steps", -1)) == latest_eval_step
    ]
    by_episode: dict[int, dict[str, float]] = {}
    for row in final_eval:
        episode = int(row.get("episode", -1))
        if episode in by_episode:
            reasons.append(f"duplicate final evaluation episode {episode}")
        by_episode[episode] = row

    coverage_field = find_coverage_field(eval_fields)
    if coverage_field is None:
        reasons.append(
            "final evaluation CSV is missing an Alice--Bob joint-position coverage field"
        )
    required_eval_fields = (
        CYCLE_FIELD,
        COLLECTION_FIELD,
        ZERO_CYCLE_FIELD,
        "reward",
        "action_mode_code",
    )
    for field in required_eval_fields:
        if field not in eval_fields:
            reasons.append(f"final evaluation CSV is missing {field}")
        elif any(field not in row for row in final_eval):
            reasons.append(f"one or more final evaluation rows omit {field}")
    if coverage_field is not None and any(
        coverage_field not in row for row in final_eval
    ):
        reasons.append(
            f"one or more final evaluation rows omit {coverage_field}"
        )

    if len(train) != expected_updates:
        reasons.append(f"train row count {len(train)} != {expected_updates}")
    expected_update_ids = list(range(1, expected_updates + 1))
    update_ids = [int(row.get("update", -1)) for row in train]
    if update_ids != expected_update_ids:
        reasons.append("training update indices are not exactly 1..expected_updates")
    final_train_steps = int(train[-1].get("total_steps", -1)) if train else -1
    if final_train_steps != total_timesteps:
        reasons.append(f"final train steps {final_train_steps} != {total_timesteps}")
    if latest_eval_step != total_timesteps:
        reasons.append(f"final eval steps {latest_eval_step} != {total_timesteps}")
    if len(final_eval) != eval_episodes:
        reasons.append(f"final eval rows {len(final_eval)} != {eval_episodes}")
    if set(by_episode) != set(range(eval_episodes)):
        reasons.append("final evaluation episode indices are not exactly 0..eval_episodes-1")

    low_update_rows = sum(
        1 for row in train if float(row.get("low_sequence_chunks", 0.0)) > 0.0
    )
    if low_update_rows != expected_updates:
        reasons.append(f"low update rows {low_update_rows} != {expected_updates}")

    intrinsic_fields = sorted(
        field for field in train_fields if field.endswith("reward_applied_steps")
    )
    nonzero_intrinsic_fields = [
        field for field in intrinsic_fields if not all_zero(train, field)
    ]
    if "combined_intrinsic_env_ratio" in train_fields and not all_zero(
        train, "combined_intrinsic_env_ratio"
    ):
        nonzero_intrinsic_fields.append("combined_intrinsic_env_ratio")
    if nonzero_intrinsic_fields:
        reasons.append(
            "intrinsic reward reached policy updates: "
            + ",".join(sorted(set(nonzero_intrinsic_fields)))
        )

    sparse_reward_exact = all(
        abs(float(row.get("reward", float("inf"))) - float(row.get(COLLECTION_FIELD, 0.0)))
        <= 1e-9
        for row in final_eval
    )
    if not sparse_reward_exact:
        reasons.append("evaluation reward is not exact sparse collection count")
    if any(abs(float(row.get("action_mode_code", -1.0)) - 1.0) > 1e-12 for row in final_eval):
        reasons.append("final evaluation is not stochastic")
    if any(
        abs(
            float(row.get(ZERO_CYCLE_FIELD, float("inf")))
            - float(float(row.get(CYCLE_FIELD, float("nan"))) <= 0.0)
        )
        > 1e-12
        for row in final_eval
    ):
        reasons.append("zero-cycle episode flag disagrees with cycle success")

    args = manifest.get("args") if isinstance(manifest.get("args"), dict) else {}
    algorithm = (
        manifest.get("algorithm_config")
        if isinstance(manifest.get("algorithm_config"), dict)
        else {}
    )
    runtime = (
        manifest.get("agent_runtime_spec")
        if isinstance(manifest.get("agent_runtime_spec"), dict)
        else {}
    )
    resume_path = resolved_path(args.get("resume_from"), repo_root)
    if resume_path != init_checkpoint:
        reasons.append(f"resume checkpoint {resume_path} != common init {init_checkpoint}")
    if str(args.get("config", "")) != expected_config:
        reasons.append(f"config {args.get('config')!r} != {expected_config!r}")
    if str(args.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
        reasons.append("CLI high controller is not r30_fixed_clock_ar_edit")
    if str(runtime.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
        reasons.append("runtime high controller is not r30_fixed_clock_ar_edit")
    if int(args.get("num_envs", -1)) != 16:
        reasons.append("num_envs is not 16")
    if int(args.get("rollout_length", -1)) != 80:
        reasons.append("rollout_length is not 80")
    if int(args.get("total_timesteps", -1)) != total_timesteps:
        reasons.append("manifest total_timesteps differs from the gate")
    if str(args.get("collector_backend", "")) != "subproc":
        reasons.append("collector backend is not subproc")
    if str(args.get("collector_start_method", "")) != "spawn":
        reasons.append("collector start method is not spawn")
    if str(args.get("device", "")) != "cuda":
        reasons.append("device is not cuda")
    if int(args.get("save_interval", -1)) != 0:
        reasons.append("save_interval is not zero")
    if int(algorithm.get("low_ppo_epochs", -1)) != 5:
        reasons.append("low_ppo_epochs is not 5")
    if int(algorithm.get("low_sequence_batch_size", -1)) != 64:
        reasons.append("low_sequence_batch_size is not 64")
    if bool(algorithm.get("alice_bob_semantic_reward_enabled", True)):
        reasons.append("Alice--Bob semantic reward is enabled")
    if abs(float(algorithm.get("transition_skill_reward_coef", float("inf")))) > 1e-12:
        reasons.append("transition-skill reward coefficient is nonzero")

    periodic_checkpoints = sorted(arm_root.glob("standalone_process_core_update_*.pt"))
    final_checkpoint = arm_root / "standalone_process_core_final.pt"
    if periodic_checkpoints:
        reasons.append("periodic checkpoints were written despite save-only-final contract")
    if not final_checkpoint.is_file():
        reasons.append("final checkpoint is missing")

    high_decision_rows = sum(float(row.get("r30_decision_rows", 0.0)) for row in train)
    high_update_rows = sum(float(row.get("r30_high_rows", 0.0)) for row in train)
    if require_zero_high_rows and (
        abs(high_decision_rows) > 1e-12 or abs(high_update_rows) > 1e-12
    ):
        reasons.append("constant-code arm produced high decision or high update rows")
    constant_mode = bool(algorithm.get("constant_skill_no_high", False))
    if constant_mode != require_zero_high_rows:
        reasons.append(
            "constant_skill_no_high does not match the registered arm identity"
        )

    final_cycle = [float(row.get(CYCLE_FIELD, float("nan"))) for row in final_eval]
    final_coverage = (
        [float(row.get(coverage_field, float("nan"))) for row in final_eval]
        if coverage_field is not None
        else []
    )
    summary = {
        "arm_root": str(arm_root),
        "config": str(args.get("config", "")),
        "resume_from": str(resume_path) if resume_path is not None else None,
        "train_updates": len(train),
        "low_updates": low_update_rows,
        "final_train_steps": final_train_steps,
        "final_eval_steps": latest_eval_step,
        "final_eval_episodes": len(final_eval),
        "coverage_field": coverage_field,
        "cycle_success_mean": fmean(final_cycle) if final_cycle else None,
        "joint_position_coverage_mean": (
            fmean(final_coverage) if final_coverage else None
        ),
        "episodes_with_collection": sum(
            float(row.get(COLLECTION_FIELD, 0.0)) > 0.0 for row in final_eval
        ),
        "zero_cycle_fraction": (
            fmean(float(row.get(ZERO_CYCLE_FIELD, float("nan"))) for row in final_eval)
            if final_cycle
            else None
        ),
        "sparse_reward_exact": sparse_reward_exact,
        "intrinsic_reward_fields_checked": intrinsic_fields,
        "nonzero_intrinsic_fields": sorted(set(nonzero_intrinsic_fields)),
        "high_decision_rows": high_decision_rows,
        "high_update_rows": high_update_rows,
        "constant_skill_no_high": constant_mode,
        "periodic_checkpoint_count": len(periodic_checkpoints),
        "final_checkpoint": str(final_checkpoint),
        "valid": not reasons,
        "invalid_reasons": reasons,
    }
    return summary, by_episode, reasons


def interval(samples: np.ndarray, observed: float) -> dict[str, float]:
    return {
        "mean": float(observed),
        "lower": float(np.quantile(samples, 0.025)),
        "upper": float(np.quantile(samples, 0.975)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--init-checkpoint", required=True)
    parser.add_argument("--seed", type=int, default=36_031)
    parser.add_argument("--total-timesteps", type=int, default=320_000)
    parser.add_argument("--expected-updates", type=int, default=250)
    parser.add_argument("--eval-episodes", type=int, default=64)
    parser.add_argument("--bootstrap-repetitions", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=40_036_031)
    args = parser.parse_args()
    if args.bootstrap_repetitions != 10_000:
        parser.error("R35 fixes --bootstrap-repetitions at 10000")
    if args.bootstrap_seed != 40_036_031:
        parser.error("R35 fixes --bootstrap-seed at 40036031")

    run_root = Path(args.run_root).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    init_checkpoint = Path(args.init_checkpoint).resolve()
    expected_configs = {
        "constant_code_mappo": "ha_ctse_process.config_alice_bob_sparse_mappo",
        "reward_pure_r30": "ha_ctse_process.config_alice_bob_asymmetric",
    }

    summaries: dict[str, dict] = {}
    episode_rows: dict[str, dict[int, dict[str, float]]] = {}
    all_reasons: list[str] = []
    if not init_checkpoint.is_file():
        all_reasons.append(f"common init checkpoint is missing: {init_checkpoint}")
    init_manifest_path = init_checkpoint.parent / "metadata" / "run_manifest.json"
    if not init_manifest_path.is_file():
        all_reasons.append(f"common init manifest is missing: {init_manifest_path}")
    else:
        init_manifest = load_manifest(init_manifest_path)
        init_args = (
            init_manifest.get("args")
            if isinstance(init_manifest.get("args"), dict)
            else {}
        )
        init_runtime = (
            init_manifest.get("agent_runtime_spec")
            if isinstance(init_manifest.get("agent_runtime_spec"), dict)
            else {}
        )
        if int(init_manifest.get("total_steps", -1)) != 0:
            all_reasons.append("common init checkpoint is not a 0-step checkpoint")
        if int(init_manifest.get("update_idx", -1)) != 0:
            all_reasons.append("common init checkpoint has a nonzero update index")
        if str(init_args.get("config", "")) != "ha_ctse_process.config_alice_bob_asymmetric":
            all_reasons.append("common init did not use the reward-pure R30 config")
        if str(init_runtime.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
            all_reasons.append("common init did not use the R30 controller stack")
    for arm in ARMS:
        summary, rows, reasons = summarize_arm(
            run_root / "runs" / arm / f"seed{args.seed}",
            repo_root=repo_root,
            init_checkpoint=init_checkpoint,
            total_timesteps=args.total_timesteps,
            expected_updates=args.expected_updates,
            eval_episodes=args.eval_episodes,
            expected_config=expected_configs[arm],
            require_zero_high_rows=arm == "constant_code_mappo",
        )
        summaries[arm] = summary
        episode_rows[arm] = rows
        all_reasons.extend(f"{arm}: {reason}" for reason in reasons)

    implementation_valid = not all_reasons
    comparison: dict[str, object] = {}
    access = {
        "max_arm_cycle_success_mean": None,
        "paired_episode_indices_with_collection_in_either_arm": 0,
        "cycle_success_floor": 0.05,
        "collection_episode_floor": 10,
        "passed": False,
    }
    status = "INVALID_R35_IMPLEMENTATION"

    if implementation_valid:
        constant_rows = episode_rows["constant_code_mappo"]
        r30_rows = episode_rows["reward_pure_r30"]
        episode_ids = list(range(args.eval_episodes))
        cycle_difference = np.asarray(
            [
                constant_rows[idx][CYCLE_FIELD] - r30_rows[idx][CYCLE_FIELD]
                for idx in episode_ids
            ],
            dtype=np.float64,
        )
        constant_coverage_field = summaries["constant_code_mappo"]["coverage_field"]
        r30_coverage_field = summaries["reward_pure_r30"]["coverage_field"]
        coverage_difference = np.asarray(
            [
                constant_rows[idx][constant_coverage_field]
                - r30_rows[idx][r30_coverage_field]
                for idx in episode_ids
            ],
            dtype=np.float64,
        )
        zero_cycle_difference = np.asarray(
            [
                constant_rows[idx][ZERO_CYCLE_FIELD]
                - r30_rows[idx][ZERO_CYCLE_FIELD]
                for idx in episode_ids
            ],
            dtype=np.float64,
        )
        rng = np.random.default_rng(args.bootstrap_seed)
        sample_indices = rng.integers(
            0,
            args.eval_episodes,
            size=(args.bootstrap_repetitions, args.eval_episodes),
        )
        cycle_samples = cycle_difference[sample_indices].mean(axis=1)
        coverage_samples = coverage_difference[sample_indices].mean(axis=1)
        zero_cycle_samples = zero_cycle_difference[sample_indices].mean(axis=1)
        cycle_ci = interval(cycle_samples, float(cycle_difference.mean()))
        coverage_ci = interval(coverage_samples, float(coverage_difference.mean()))
        zero_cycle_ci = interval(
            zero_cycle_samples, float(zero_cycle_difference.mean())
        )
        comparison = {
            "direction": "constant_code_mappo_minus_reward_pure_r30",
            "cycle_success": cycle_ci,
            "joint_position_coverage": coverage_ci,
            "zero_cycle_fraction": zero_cycle_ci,
            "bootstrap_repetitions": args.bootstrap_repetitions,
            "bootstrap_seed": args.bootstrap_seed,
        }

        max_cycle = max(
            float(summaries[arm]["cycle_success_mean"]) for arm in ARMS
        )
        union_collection_count = sum(
            constant_rows[idx][COLLECTION_FIELD] > 0.0
            or r30_rows[idx][COLLECTION_FIELD] > 0.0
            for idx in episode_ids
        )
        access_passed = max_cycle >= 0.05 and union_collection_count >= 10
        access.update(
            {
                "max_arm_cycle_success_mean": max_cycle,
                "paired_episode_indices_with_collection_in_either_arm": int(
                    union_collection_count
                ),
                "passed": access_passed,
            }
        )

        noninferior = bool(
            cycle_ci["lower"] > -0.10
            and coverage_ci["lower"] > -0.05
            and zero_cycle_ci["upper"] < 0.10
        )
        clear_r30_superiority = bool(
            cycle_ci["upper"] < -0.10
            or coverage_ci["upper"] < -0.05
            or zero_cycle_ci["lower"] > 0.10
        )
        if not access_passed:
            status = "NO_ACCESS_R35_UNRESOLVED"
        elif noninferior:
            status = "PASS_R35_MAPPO_NONINFERIOR"
        elif clear_r30_superiority:
            status = "FAIL_R35_MAPPO_INFERIOR"
        else:
            status = "MIXED_R35_NO_REPLACEMENT"

    result = {
        "experiment_id": "EXP-20260715-r35-sparse-mappo-reset",
        "status": status,
        "scope": "single-seed sparse Alice--Bob baseline reset gate",
        "seed": args.seed,
        "total_timesteps_per_arm": args.total_timesteps,
        "common_init_checkpoint": str(init_checkpoint),
        "implementation_valid": implementation_valid,
        "invalid_reasons": all_reasons,
        "arms": summaries,
        "access_floor": access,
        "paired_comparison": comparison,
        "decision_thresholds": {
            "cycle_success_lower": -0.10,
            "joint_position_coverage_lower": -0.05,
            "zero_cycle_fraction_upper": 0.10,
        },
    }
    output_dir = run_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "r35_sparse_mappo_reset.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(output_path)


if __name__ == "__main__":
    main()

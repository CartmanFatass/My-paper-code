"""Summarize one paired Alice--Bob R30 mechanism screen."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean, pstdev


ARMS = ("adaptive_keep_set", "shared_k_refresh")
EVAL_FIELDS = (
    "reward",
    "length",
    "alice_bob_targets_completed",
    "alice_bob_cycle_success_rate",
    "alice_bob_button_occupancy_fraction",
    "alice_bob_target_contact_fraction",
    "alice_bob_joint_coordination_fraction",
    "alice_bob_button_switch_count",
)
OBSERVED_FIELDS = (
    "alice_bob_r30_observed_button_keep_rate",
    "alice_bob_r30_observed_target_set_rate",
    "alice_bob_r30_observed_cycle_action_match_rate",
)
TRANSITION_FIELDS = (
    "transition_skill_acc",
    "transition_skill_context_acc",
    "transition_skill_residual_mi_mean",
    "transition_skill_residual_mi_positive_frac",
    "transition_skill_reward_active",
    "transition_skill_reward_mean",
)


def load_csv(path: Path) -> list[dict[str, float]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
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
    return rows


def values(rows: list[dict[str, float]], field: str) -> list[float]:
    return [row[field] for row in rows if field in row and math.isfinite(row[field])]


def mean(rows: list[dict[str, float]], field: str) -> float | None:
    items = values(rows, field)
    return fmean(items) if items else None


def total(rows: list[dict[str, float]], field: str) -> float:
    return float(sum(values(rows, field)))


def weighted_mean(
    rows: list[dict[str, float]], field: str, weight_field: str
) -> float | None:
    pairs = [
        (row[field], row[weight_field])
        for row in rows
        if field in row and weight_field in row and row[weight_field] > 0.0
    ]
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0.0:
        return None
    return float(sum(value * weight for value, weight in pairs) / denominator)


def stats(rows: list[dict[str, float]], field: str) -> dict[str, float | None]:
    items = values(rows, field)
    return {
        "mean": fmean(items) if items else None,
        "std": pstdev(items) if len(items) > 1 else (0.0 if items else None),
    }


def normalized_entropy(counts: list[float]) -> float:
    count_sum = sum(counts)
    if count_sum <= 0.0:
        return 0.0
    shares = [count / count_sum for count in counts]
    return float(
        -sum(share * math.log(share) for share in shares if share > 0.0)
        / math.log(len(counts))
    )


def summarize_arm(
    arm_root: Path,
    *,
    total_timesteps: int,
    expected_updates: int,
    eval_episodes: int,
    n_agents: int,
) -> tuple[dict, bool]:
    train = load_csv(arm_root / "metrics" / "train_updates.csv")
    evaluation = load_csv(arm_root / "metrics" / "eval_episodes.csv")
    train.sort(key=lambda row: row.get("total_steps", -1.0))
    latest_eval_step = max((row.get("total_steps", -1.0) for row in evaluation), default=-1.0)
    final_eval = [row for row in evaluation if row.get("total_steps") == latest_eval_step]
    late_count = max(1, math.ceil(len(train) * 0.25))
    late = train[-late_count:]

    decision_rows = [row for row in train if row.get("r30_decision_rows", 0.0) > 0.0]
    replay_errors = values(train, "r30_replay_logp_max_error")
    replay_error = max(replay_errors, default=float("inf"))
    tokens_exact = bool(decision_rows) and all(
        abs(row.get("r30_tokens_per_decision", float("inf")) - n_agents) <= 1e-9
        for row in decision_rows
    )

    spell_counts = {
        "gt_4k0": total(late, "r30_spell_gt_4k0_count"),
        "le_4k0": total(late, "r30_spell_le_4k0_count"),
    }
    normal_decisions = total(late, "r30_normal_decision_rows")
    full_sync_sets = total(late, "r30_full_sync_set_rows")
    switch_counts = [
        total(late, f"r30_switch_skill_{skill}_count") for skill in range(4)
    ]
    switch_sum = sum(switch_counts)

    observed_rows = total(late, "alice_bob_r30_observed_cycle_metric_rows")
    transition_samples = total(late, "transition_skill_samples")
    transition_available = total(late, "transition_skill_available_samples")
    summary = {
        "arm_root": str(arm_root),
        "train_updates": len(train),
        "final_train_steps": int(train[-1].get("total_steps", -1)) if train else -1,
        "final_eval_steps": int(latest_eval_step),
        "final_eval_episodes": len(final_eval),
        "evaluation": {field: stats(final_eval, field) for field in EVAL_FIELDS},
        "wiring": {
            "decision_rows": total(train, "r30_decision_rows"),
            "continuation_rows": total(train, "r30_continuation_rows"),
            "tokens_per_decision_exact": tokens_exact,
            "continuation_actor_tokens": total(train, "r30_continuation_actor_tokens"),
            "replay_logp_max_error": replay_error,
        },
        "late_quarter": {
            "updates": len(late),
            "spell_counts": spell_counts,
            "normal_decision_rows": normal_decisions,
            "full_sync_set_rows": full_sync_sets,
            "full_sync_set_rate": (
                full_sync_sets / normal_decisions if normal_decisions > 0.0 else None
            ),
            "switch_skill_counts": switch_counts,
            "switch_skill_entropy_norm": normalized_entropy(switch_counts),
            "switch_skill_min_share": (
                min(count / switch_sum for count in switch_counts)
                if switch_sum > 0.0
                else 0.0
            ),
            "observed_cycle_rows": observed_rows,
            "observed_behavior": {
                field: weighted_mean(
                    late, field, "alice_bob_r30_observed_cycle_metric_rows"
                )
                for field in OBSERVED_FIELDS
            },
            "low_skill_usage_entropy": mean(late, "low_skill_usage_entropy"),
            "transition_skill_samples": transition_samples,
            "transition_skill_available_samples": transition_available,
            "transition_skill": {
                field: weighted_mean(late, field, "transition_skill_samples")
                for field in TRANSITION_FIELDS
            },
            "semantic_shortcut_hard_stop_triggered": max(
                values(late, "semantic_shortcut_hard_stop_triggered"), default=0.0
            ),
        },
    }
    valid = bool(
        len(train) == expected_updates
        and summary["final_train_steps"] == total_timesteps
        and summary["final_eval_steps"] == total_timesteps
        and len(final_eval) == eval_episodes
        and tokens_exact
        and replay_error <= 1e-5
        and summary["wiring"]["continuation_actor_tokens"] == 0.0
        and transition_samples > 0.0
    )
    return summary, valid


def nested_mean(summary: dict, path: tuple[str, ...]) -> float | None:
    value = summary
    for key in path:
        value = value[key]
    if isinstance(value, dict):
        value = value.get("mean")
    return float(value) if value is not None else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--seed", type=int, default=30031)
    parser.add_argument("--total-timesteps", type=int, default=64_000)
    parser.add_argument("--expected-updates", type=int, default=50)
    parser.add_argument("--eval-episodes", type=int, default=40)
    parser.add_argument("--n-agents", type=int, default=2)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    summaries: dict[str, dict] = {}
    validity: dict[str, bool] = {}
    for arm in ARMS:
        summaries[arm], validity[arm] = summarize_arm(
            run_root / "runs" / arm / f"seed{args.seed}",
            total_timesteps=args.total_timesteps,
            expected_updates=args.expected_updates,
            eval_episodes=args.eval_episodes,
            n_agents=args.n_agents,
        )

    comparison_paths = {
        field: ("evaluation", field) for field in EVAL_FIELDS
    }
    comparison_paths.update(
        {field: ("late_quarter", "observed_behavior", field) for field in OBSERVED_FIELDS}
    )
    comparison = {}
    for field, path in comparison_paths.items():
        adaptive = nested_mean(summaries["adaptive_keep_set"], path)
        shared = nested_mean(summaries["shared_k_refresh"], path)
        comparison[field] = (
            adaptive - shared if adaptive is not None and shared is not None else None
        )

    implementation_valid = all(validity.values())
    result = {
        "experiment_id": "EXP-20260714-r30-alice-bob-paired-64k",
        "status": "COMPLETE" if implementation_valid else "INVALID_RUN",
        "scope": "single paired Alice--Bob mechanism seed; not S7 or efficacy evidence",
        "seed": args.seed,
        "total_timesteps_per_arm": args.total_timesteps,
        "implementation_valid": implementation_valid,
        "arm_validity": validity,
        "arms": summaries,
        "adaptive_minus_shared": comparison,
    }
    output_dir = run_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alice_bob_pair.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(output_path)


if __name__ == "__main__":
    main()

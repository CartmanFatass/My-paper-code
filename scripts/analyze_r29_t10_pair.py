"""Summarize the single-seed R29-T10 pair and prepare an external-review question."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


ARMS = ("probe_only", "real_reward")
SOURCE_STEPS = 1_000_000
FINAL_STEPS = 1_320_000
LATE_UPDATES = 10


def load_csv(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, float] = {}
            for key, value in raw.items():
                if key is None or value in (None, ""):
                    continue
                try:
                    row[key] = float(value)
                except ValueError:
                    continue
            rows.append(row)
    return rows


def finite_mean(values: list[float]) -> float:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    return float(np.mean(array)) if array.size else float("nan")


def paired_bootstrap(values: np.ndarray, seed: int = 29101) -> dict[str, float]:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 1 or data.size == 0 or not np.isfinite(data).all():
        return {"mean": float("nan"), "lower": float("nan"), "upper": float("nan")}
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, data.size, size=(10_000, data.size))
    means = data[draws].mean(axis=1)
    return {
        "mean": float(np.mean(data)),
        "lower": float(np.quantile(means, 0.025)),
        "upper": float(np.quantile(means, 0.975)),
    }


def metric(rows: list[dict[str, float]], name: str) -> np.ndarray:
    return np.asarray([row.get(name, float("nan")) for row in rows], dtype=np.float64)


def final_eval(rows: list[dict[str, float]]) -> dict[str, float]:
    final_rows = [row for row in rows if int(row.get("total_steps", -1)) == FINAL_STEPS]
    names = (
        "reward",
        "coverage",
        "qos",
        "throughput",
        "zero_throughput_step_fraction",
        "zero_throughput_episode_flag",
        "backhaul_connected_step_fraction",
    )
    return {
        name: finite_mean([row.get(name, float("nan")) for row in final_rows])
        for name in names
    } | {"episodes": float(len(final_rows))}


def r26_summary(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    gate = report.get("gate") if isinstance(report.get("gate"), dict) else {}
    primary = report.get("primary_bootstrap") if isinstance(report.get("primary_bootstrap"), dict) else {}
    return {
        "status": str(gate.get("status", "INVALID")),
        "reasons": list(gate.get("reasons", [])),
        "rows": int(report.get("rows", 0)),
        "normalized_label_entropy": float(report.get("normalized_label_entropy", float("nan"))),
        "full_minus_prior_accuracy": float(report.get("full_minus_prior_accuracy", float("nan"))),
        "behavior_post_minus_pre_accuracy": float(
            report.get("behavior_post_minus_pre_accuracy", float("nan"))
        ),
        "primary_bootstrap": primary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--seed", type=int, default=29031)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    output_dir = run_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    train: dict[str, list[dict[str, float]]] = {}
    evaluations: dict[str, dict[str, float]] = {}
    r26: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arm_root = run_root / "runs" / arm / f"seed{args.seed}"
        arm_rows = [
            row
            for row in load_csv(arm_root / "metrics" / "train_updates.csv")
            if int(row.get("total_steps", -1)) > SOURCE_STEPS
        ]
        arm_rows.sort(key=lambda row: row.get("total_steps", -1.0))
        train[arm] = arm_rows
        evaluations[arm] = final_eval(
            load_csv(arm_root / "metrics" / "eval_episodes.csv")
        )
        r26[arm] = r26_summary(
            run_root
            / "evidence"
            / arm
            / "analysis"
            / "r26_g1_behavior.json"
        )

    common_steps = sorted(
        set(int(row["total_steps"]) for row in train["probe_only"])
        & set(int(row["total_steps"]) for row in train["real_reward"])
    )
    late_steps = common_steps[-LATE_UPDATES:]
    late: dict[str, list[dict[str, float]]] = {}
    for arm in ARMS:
        by_step = {int(row["total_steps"]): row for row in train[arm]}
        late[arm] = [by_step[step] for step in late_steps]

    raw_difference = (
        metric(late["real_reward"], "r29_action_info_raw_mean")
        - metric(late["probe_only"], "r29_action_info_raw_mean")
    )
    raw_bootstrap = paired_bootstrap(raw_difference)
    skill_differences = {
        str(skill): finite_mean(
            list(
                metric(late["real_reward"], f"r29_action_info_skill_{skill}_mean")
                - metric(late["probe_only"], f"r29_action_info_skill_{skill}_mean")
            )
        )
        for skill in range(4)
    }

    training_summary: dict[str, Any] = {}
    for arm in ARMS:
        all_rows = train[arm]
        late_rows = late[arm]
        training_summary[arm] = {
            "updates": len(all_rows),
            "first_total_steps": int(all_rows[0].get("total_steps", -1)) if all_rows else -1,
            "final_total_steps": int(all_rows[-1].get("total_steps", -1)) if all_rows else -1,
            "late_r29_t10_mean": finite_mean(
                list(metric(late_rows, "r29_action_info_raw_mean"))
            ),
            "late_r29_t10_abs_mean": finite_mean(
                list(metric(late_rows, "r29_action_info_raw_abs_mean"))
            ),
            "late_skill_entropy": finite_mean(list(metric(late_rows, "skill_usage_entropy"))),
            "max_reward_env_ratio": float(
                np.nanmax(metric(all_rows, "r29_action_info_reward_env_ratio"))
            ),
            "max_likelihood_error": float(
                np.nanmax(metric(all_rows, "r29_action_info_likelihood_max_abs_error"))
            ),
            "total_complete_segments": float(
                np.nansum(metric(all_rows, "r29_action_info_segments"))
            ),
            "late_symmetric_kl": finite_mean(
                list(metric(late_rows, "r29_action_info_symmetric_kl_mean"))
            ),
            "late_symmetric_kl_mean_component": finite_mean(
                list(
                    metric(
                        late_rows,
                        "r29_action_info_symmetric_kl_mean_component",
                    )
                )
            ),
            "late_symmetric_kl_variance_component": finite_mean(
                list(
                    metric(
                        late_rows,
                        "r29_action_info_symmetric_kl_variance_component",
                    )
                )
            ),
        }

    probe_reward = evaluations["probe_only"]["reward"]
    real_reward = evaluations["real_reward"]["reward"]
    relative_reward_degradation = (probe_reward - real_reward) / max(abs(probe_reward), 1e-8)
    zero_throughput_worsening = (
        evaluations["real_reward"]["zero_throughput_step_fraction"]
        - evaluations["probe_only"]["zero_throughput_step_fraction"]
    )
    r26_full_gain = (
        r26["real_reward"]["full_minus_prior_accuracy"]
        - r26["probe_only"]["full_minus_prior_accuracy"]
    )

    implementation_valid = bool(
        all(summary["updates"] == 40 for summary in training_summary.values())
        and all(summary["final_total_steps"] == FINAL_STEPS for summary in training_summary.values())
        and all(summary["max_likelihood_error"] <= 2e-5 for summary in training_summary.values())
        and all(summary["total_complete_segments"] > 0 for summary in training_summary.values())
        and all(evaluations[arm]["episodes"] == 20 for arm in ARMS)
        and all(r26[arm]["rows"] > 0 for arm in ARMS)
    )
    score_pass = bool(
        raw_bootstrap["mean"] >= 0.05
        and raw_bootstrap["lower"] > 0.0
        and all(value >= 0.0 for value in skill_differences.values())
    )
    r26_pass = bool(
        r26["real_reward"]["status"] == "PASS"
        and r26["probe_only"]["status"] != "PASS"
        and r26_full_gain >= 0.05
    )
    safety_pass = bool(
        training_summary["real_reward"]["late_skill_entropy"] >= 0.8
        and training_summary["real_reward"]["max_reward_env_ratio"] <= 0.05
        and relative_reward_degradation <= 0.10
        and zero_throughput_worsening <= 0.10
    )
    if not implementation_valid:
        status = "INVALID"
    elif score_pass and r26_pass and safety_pass:
        status = "PRELIMINARY_PASS"
    elif (score_pass or r26_pass) and safety_pass:
        status = "PRELIMINARY_MIXED"
    else:
        status = "PRELIMINARY_FAIL"

    result = {
        "experiment_id": "EXP-20260714-r29-t10-paired-320k",
        "status": status,
        "scope": "single paired seed; not a three-seed scientific conclusion",
        "seed": args.seed,
        "source_steps": SOURCE_STEPS,
        "additional_steps_per_arm": FINAL_STEPS - SOURCE_STEPS,
        "late_update_steps": late_steps,
        "training": training_summary,
        "r29_t10_real_minus_probe": {
            "paired_late_update_bootstrap": raw_bootstrap,
            "per_skill_late_means": skill_differences,
        },
        "r26": r26,
        "r26_real_minus_probe_full_minus_prior_accuracy": r26_full_gain,
        "task_evaluation": evaluations,
        "task_relative_reward_degradation": relative_reward_degradation,
        "zero_throughput_step_fraction_worsening": zero_throughput_worsening,
        "gates": {
            "implementation_valid": implementation_valid,
            "score_pass": score_pass,
            "r26_transfer_pass": r26_pass,
            "safety_pass": safety_pass,
        },
    }
    json_path = output_dir / "r29_t10_pair.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    markdown = f"""# R29-T10 Paired 320K Result

- Status: **{status}**
- Scope: one paired seed (`{args.seed}`), 320K additional environment steps per arm.
- R29-T10 late mean difference (real - probe): `{raw_bootstrap['mean']:.6f}`;
  paired-update 95% interval `[{raw_bootstrap['lower']:.6f}, {raw_bootstrap['upper']:.6f}]`.
- Per-skill late differences: `{json.dumps(skill_differences, sort_keys=True)}`.
- R26 status: probe `{r26['probe_only']['status']}`, real `{r26['real_reward']['status']}`;
  full-minus-prior gain `{r26_full_gain:.6f}`.
- Real reward/env ratio maximum: `{training_summary['real_reward']['max_reward_env_ratio']:.6f}`.
- Real late skill entropy: `{training_summary['real_reward']['late_skill_entropy']:.6f}`.
- Task reward relative degradation: `{relative_reward_degradation:.6f}`.
- Zero-throughput step-fraction worsening: `{zero_throughput_worsening:.6f}`.
- Gate flags: `{json.dumps(result['gates'], sort_keys=True)}`.

This result is preliminary because there is only one paired seed. The paired
update bootstrap measures late training-update variation, not independent-seed
uncertainty and not the reset-level bootstrap requested for a final family claim.
"""
    (output_dir / "r29_t10_pair.md").write_text(markdown, encoding="utf-8")

    question = f"""# HMASD R29-T10 Result Review and Next-Route Decision

You previously reviewed pointwise R29 and recommended R29-T10: fixed-candidate
recurrent replay over each complete natural skill lifetime, a uniform four-code
mixture, final-10-action block likelihood, detached coefficient 0.05, clip 0.05,
and one low-level endpoint reward.

We implemented that exact core change and ran the user-authorized preliminary
pair from the same R25 arm0 1M checkpoint: `probe_only` versus `real_reward`,
seed {args.seed}, 16 environments per arm, CUDA, 40 rollout/PPO updates, 320K
additional environment steps per arm, and 15 low PPO epochs. Both arms compute
the same scorer; only the real arm receives its reward. Final natural-process
evidence uses the unchanged R26 64-reset analyzer, and task safety uses 20
deterministic episodes.

The machine summary classified the pair as **{status}**. Important numbers:

- late R29-T10 real-minus-probe mean `{raw_bootstrap['mean']:.6f}`, paired-update
  95% interval `[{raw_bootstrap['lower']:.6f}, {raw_bootstrap['upper']:.6f}]`;
- per-skill late differences `{json.dumps(skill_differences, sort_keys=True)}`;
- R26 probe/real statuses `{r26['probe_only']['status']}` / `{r26['real_reward']['status']}`;
- R26 full-minus-prior real-minus-probe gain `{r26_full_gain:.6f}`;
- real late skill entropy `{training_summary['real_reward']['late_skill_entropy']:.6f}`;
- real maximum reward/env ratio `{training_summary['real_reward']['max_reward_env_ratio']:.6f}`;
- task reward relative degradation `{relative_reward_degradation:.6f}` and
  zero-throughput step-fraction worsening `{zero_throughput_worsening:.6f}`;
- likelihood parity maximum probe/real
  `{training_summary['probe_only']['max_likelihood_error']:.3e}` /
  `{training_summary['real_reward']['max_likelihood_error']:.3e}`;
- late symmetric KL mean/variance components in the real arm
  `{training_summary['real_reward']['late_symmetric_kl_mean_component']:.6f}` /
  `{training_summary['real_reward']['late_symmetric_kl_variance_component']:.6f}`.

Read the attached raw JSON/CSV/R26 reports and code before deciding. The single
seed and late-update bootstrap are explicitly not enough for a final efficacy
claim. Choose exactly one next route:

1. **PROMOTE** the unchanged pair to the remaining preregistered seeds 29032 and
   29033;
2. **MODIFY ONCE**, naming one causal defect, one minimal algorithm change, and
   one falsifiable comparator; or
3. **RETIRE** the R29 density-ratio reward family and state the negative
   constraint it establishes.

Also state which conclusions remain prohibited and whether the observed
mean-versus-variance KL split changes your mechanism diagnosis. Do not propose a
coefficient sweep, threshold relaxation, new semantic classifier reward, or
task-specific intrinsic reward.
"""
    (output_dir / "GPT5_6_PRO_QUESTION.md").write_text(question, encoding="utf-8")
    print(f"RESULT_JSON={json_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()

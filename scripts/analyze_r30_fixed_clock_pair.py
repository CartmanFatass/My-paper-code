"""Read the four preregistered R30 mechanism-gate metric families."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SOURCE_STEPS = 1_000_000
FINAL_STEPS = 1_320_000
EXPECTED_UPDATES = 40
LATE_UPDATES = 10
N_AGENTS = 6
N_SKILLS = 4
ARMS = ("legacy_duration", "r30_fixed_clock_ar_edit")


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


def values(rows: list[dict[str, float]], name: str) -> np.ndarray:
    return np.asarray([row.get(name, float("nan")) for row in rows], dtype=np.float64)


def finite_mean(items: np.ndarray) -> float:
    finite = np.asarray(items, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    return float(np.mean(finite)) if finite.size else float("nan")


def final_eval(rows: list[dict[str, float]]) -> dict[str, float]:
    final_rows = [row for row in rows if int(row.get("total_steps", -1)) == FINAL_STEPS]
    return {
        "episodes": float(len(final_rows)),
        "reward": finite_mean(values(final_rows, "reward")),
        "zero_throughput_step_fraction": finite_mean(
            values(final_rows, "zero_throughput_step_fraction")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--seed", type=int, default=30031)
    parser.add_argument("--r30-arm-root")
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    output_dir = run_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    train: dict[str, list[dict[str, float]]] = {}
    evaluation: dict[str, dict[str, float]] = {}
    arm_roots: dict[str, Path] = {}
    for arm in ARMS:
        if arm == "r30_fixed_clock_ar_edit" and args.r30_arm_root:
            arm_root = Path(args.r30_arm_root).resolve()
        else:
            arm_root = run_root / "runs" / arm / f"seed{args.seed}"
        arm_roots[arm] = arm_root
        arm_rows = [
            row
            for row in load_csv(arm_root / "metrics" / "train_updates.csv")
            if int(row.get("total_steps", -1)) > SOURCE_STEPS
        ]
        arm_rows.sort(key=lambda row: row.get("total_steps", -1.0))
        train[arm] = arm_rows
        evaluation[arm] = final_eval(
            load_csv(arm_root / "metrics" / "eval_episodes.csv")
        )

    r30_rows = train["r30_fixed_clock_ar_edit"]
    late = r30_rows[-LATE_UPDATES:]
    exposure_valid = all(
        len(train[arm]) == EXPECTED_UPDATES
        and int(train[arm][-1].get("total_steps", -1)) == FINAL_STEPS
        and evaluation[arm]["episodes"] == 20.0
        for arm in ARMS
    )
    token_rows = [row for row in r30_rows if row.get("r30_decision_rows", 0.0) > 0.0]
    tokens_exact = bool(
        token_rows
        and all(
            abs(row.get("r30_tokens_per_decision", float("nan")) - N_AGENTS) <= 1e-9
            for row in token_rows
        )
    )
    replay_error = float(np.nanmax(values(r30_rows, "r30_replay_logp_max_error")))
    continuation_rows = float(np.nansum(values(r30_rows, "r30_continuation_rows")))
    continuation_actor_tokens = float(
        np.nansum(values(r30_rows, "r30_continuation_actor_tokens"))
    )
    m1 = bool(
        exposure_valid
        and tokens_exact
        and replay_error <= 1e-5
        and continuation_rows > 0.0
        and continuation_actor_tokens == 0.0
    )

    spell_gt = float(np.nansum(values(late, "r30_spell_gt_4k0_count")))
    spell_le = float(np.nansum(values(late, "r30_spell_le_4k0_count")))
    spell_total = spell_gt + spell_le
    spell_gt_share = spell_gt / spell_total if spell_total > 0.0 else 0.0
    spell_le_share = spell_le / spell_total if spell_total > 0.0 else 0.0
    lifetime_breadth = min(spell_gt_share, spell_le_share)
    m2 = bool(spell_total > 0.0 and lifetime_breadth >= 0.05)

    normal_rows = float(np.nansum(values(late, "r30_normal_decision_rows")))
    full_sync_rows = float(np.nansum(values(late, "r30_full_sync_set_rows")))
    full_sync_rate = full_sync_rows / normal_rows if normal_rows > 0.0 else 1.0
    skill_counts = np.asarray(
        [
            np.nansum(values(late, f"r30_switch_skill_{skill}_count"))
            for skill in range(N_SKILLS)
        ],
        dtype=np.float64,
    )
    switch_total = float(np.sum(skill_counts))
    if switch_total > 0.0:
        skill_shares = skill_counts / switch_total
        positive = skill_shares[skill_shares > 0.0]
        switch_entropy = float(-np.sum(positive * np.log(positive)) / math.log(N_SKILLS))
        switch_share_min = float(np.min(skill_shares))
    else:
        skill_shares = np.zeros(N_SKILLS, dtype=np.float64)
        switch_entropy = 0.0
        switch_share_min = 0.0
    m3 = bool(
        normal_rows > 0.0
        and full_sync_rate <= 0.50
        and switch_entropy >= 0.80
        and switch_share_min >= 0.05
    )

    legacy_reward = evaluation["legacy_duration"]["reward"]
    r30_reward = evaluation["r30_fixed_clock_ar_edit"]["reward"]
    relative_reward_degradation = (legacy_reward - r30_reward) / max(
        abs(legacy_reward), 1e-8
    )
    zero_throughput_worsening = (
        evaluation["r30_fixed_clock_ar_edit"]["zero_throughput_step_fraction"]
        - evaluation["legacy_duration"]["zero_throughput_step_fraction"]
    )
    m4 = bool(
        np.isfinite(relative_reward_degradation)
        and np.isfinite(zero_throughput_worsening)
        and relative_reward_degradation <= 0.10
        and zero_throughput_worsening <= 0.10
    )

    if not m1:
        status = "INVALID_IMPLEMENTATION"
    elif not (m2 and m3):
        status = "MECHANISM_FAIL"
    elif not m4:
        status = "TASK_SAFETY_FAIL"
    else:
        status = "PRELIMINARY_PASS_R30_MECHANISM"

    result: dict[str, Any] = {
        "experiment_id": "EXP-20260714-r30-fixed-clock-paired-320k",
        "status": status,
        "scope": "single paired mechanism seed; not parity or long-run evidence",
        "seed": args.seed,
        "source_steps": SOURCE_STEPS,
        "additional_steps_per_arm": FINAL_STEPS - SOURCE_STEPS,
        "arm_roots": {arm: str(path) for arm, path in arm_roots.items()},
        "updates_per_arm": {arm: len(train[arm]) for arm in ARMS},
        "gates": {"M1": m1, "M2": m2, "M3": m3, "M4": m4},
        "M1_token_contract": {
            "exposure_valid": exposure_valid,
            "tokens_per_decision_exact": tokens_exact,
            "replay_logp_max_error": replay_error,
            "continuation_rows": continuation_rows,
            "continuation_actor_tokens": continuation_actor_tokens,
        },
        "M2_lifetime_breadth": {
            "late_updates": len(late),
            "eligible_events": spell_total,
            "gt_4k0_count": spell_gt,
            "le_4k0_count": spell_le,
            "gt_4k0_share": spell_gt_share,
            "le_4k0_share": spell_le_share,
            "minimum_share": lifetime_breadth,
        },
        "M3_async_skill_supply": {
            "normal_decision_rows": normal_rows,
            "full_sync_set_rows": full_sync_rows,
            "full_sync_set_rate": full_sync_rate,
            "switch_count": switch_total,
            "switch_skill_counts": skill_counts.tolist(),
            "switch_skill_shares": skill_shares.tolist(),
            "switch_skill_entropy_norm": switch_entropy,
            "switch_skill_share_min": switch_share_min,
        },
        "M4_task_safety": {
            "evaluation": evaluation,
            "relative_reward_degradation": relative_reward_degradation,
            "zero_throughput_step_fraction_worsening": zero_throughput_worsening,
        },
    }
    json_path = output_dir / "r30_fixed_clock_pair.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    markdown = f"""# R30 Fixed-Clock Paired 320K Result

- Status: **{status}**
- Scope: one paired seed (`{args.seed}`), 320K additional transitions per arm.
- M1 token/replay: `{m1}`; tokens exact `{tokens_exact}`, replay max error
  `{replay_error:.3e}`, continuation rows `{continuation_rows:.0f}`, continuation
  actor tokens `{continuation_actor_tokens:.0f}`.
- M2 lifetime breadth: `{m2}`; `T>4k0` / `T<=4k0` counts
  `{spell_gt:.0f}` / `{spell_le:.0f}`, minimum share `{lifetime_breadth:.6f}`.
- M3 asynchronous supply: `{m3}`; full-sync SET rate `{full_sync_rate:.6f}`,
  switch-skill entropy `{switch_entropy:.6f}`, minimum skill share
  `{switch_share_min:.6f}`.
- M4 task safety: `{m4}`; relative reward degradation
  `{relative_reward_degradation:.6f}`, zero-throughput worsening
  `{zero_throughput_worsening:.6f}`.

This gate does not establish HMASD parity, semantic differentiation, long-run
stability, task improvement, or a MAT/HAPPO monotonic-improvement theorem.
"""
    (output_dir / "r30_fixed_clock_pair.md").write_text(markdown, encoding="utf-8")

    question = f"""# HMASD R30 Mechanism Result: Route Decision

You previously returned `MODIFY R30`. The accepted corrections were implemented:
deterministic expected bridge context, one prefix-independent high critic,
per-environment fixed clocks with critic-only PPO-boundary continuations, a
separate HighCheckBuffer, and one combined KEEP/SET token ratio.

We ran the preregistered reward-pure pair from the same R25 arm0 1M checkpoint:
legacy discrete duration `(1,2,3,4)` versus corrected R30, seed {args.seed}, 16
environments, CUDA, 40 matched updates and 320K additional transitions per arm.
Rollout length 501 intentionally exercises non-check-aligned continuation.

Machine status: **{status}**.

- M1 `{m1}`: replay error `{replay_error:.3e}`, continuation rows
  `{continuation_rows:.0f}`, continuation actor tokens `{continuation_actor_tokens:.0f}`.
- M2 `{m2}`: late long/short eligible counts `{spell_gt:.0f}` / `{spell_le:.0f}`,
  minimum share `{lifetime_breadth:.6f}`.
- M3 `{m3}`: full-sync SET `{full_sync_rate:.6f}`, normalized switch-skill
  entropy `{switch_entropy:.6f}`, minimum switch-skill share `{switch_share_min:.6f}`.
- M4 `{m4}`: reward degradation `{relative_reward_degradation:.6f}` and
  zero-throughput worsening `{zero_throughput_worsening:.6f}`.

Read the result JSON, experiment contract, R30 design, and implementation before
answering. Choose one route consistent with the preregistered branches:

1. accept R30 as the next temporal controller and specify the smallest
   reward-off realized-effect diagnostic;
2. retire the current R30 formulation because M2/M3/M4 falsified it; or
3. if and only if M1 is invalid, name the single implementation defect to repair
   under the unchanged gate.

Do not propose keep entropy, a duration/penalty/coefficient sweep, sampled team
intent, semantic reward inside the high return, or claims of parity, task
improvement, long-run stability, reduced joint action space, or MAT theorem.
"""
    (output_dir / "GPT5_6_PRO_QUESTION.md").write_text(question, encoding="utf-8")
    print(f"RESULT_JSON={json_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()

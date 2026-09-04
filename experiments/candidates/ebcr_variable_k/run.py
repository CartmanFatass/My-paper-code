from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from .analysis import analyze_seed_cells, summarize_episodes
from .config import (
    BASE_SEEDS, CONCLUSION_CELLS, DECLARED_BUDGETS, FIXED_ARMS, FIXED_KS,
    LEARNED_ARMS, PPO, PRODUCTION_CONFIG, SELECTION_SEEDS, TRAIN_DURATIONS,
    UNIQUE_EVALUATION_ARMS, VALIDATION_DURATIONS, RunConfig,
)
from .controls import shuffled_schedule, yoked_schedules
from .host import EpisodeResult, ExogenousEpisode, balance_report, generate_episode, run_episode
from .models import PPOHazardLearner

ARTIFACT_KIND = "EBCR_B1_VARIABLE_K_REGISTERED_RESULT"
TREATMENT = "EBCR-B1-VARIABLE-K-COOPERATIVE-RENEWAL-v1"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def _rss_bytes() -> int:
    try:
        import psutil
        return int(psutil.Process().memory_info().rss)
    except (ImportError, OSError):
        return 0


def _check_caps(started: float, peak_rss: int, ticks: int, config: RunConfig) -> int:
    elapsed = time.perf_counter() - started
    rss = _rss_bytes()
    peak_rss = max(peak_rss, rss)
    if elapsed > config.wall_seconds:
        raise RuntimeError("registered wall-time cap breached before complete output")
    if peak_rss and peak_rss > config.peak_rss_bytes:
        raise RuntimeError("registered peak-RSS cap breached before complete output")
    if ticks > config.total_tick_cap:
        raise RuntimeError("registered total team-tick cap breached")
    return peak_rss


def select_fixed_k(config: RunConfig, dummy_actor: PPOHazardLearner) -> tuple[int, dict[str, object], int]:
    returns: dict[int, list[float]] = {k: [] for k in FIXED_KS}
    ticks = 0
    for selection_seed in SELECTION_SEEDS:
        episode_counter = 0
        for duration in VALIDATION_DURATIONS:
            for joint in (False, True):
                for repeat in range(config.selection_episodes_per_cell):
                    exogenous = generate_episode(
                        seed=selection_seed, episode=episode_counter,
                        namespace="validation_selection", cell=f"D{duration}_{'ON' if joint else 'OFF'}",
                        durations=(duration,), noise=0.10, joint_mismatch=joint,
                        horizon=config.horizon,
                    )
                    for k in FIXED_KS:
                        returns[k].append(run_episode(
                            exogenous, arm=f"FIXED-{k}", actor=dummy_actor
                        ).normalized_return)
                        ticks += config.horizon
                    episode_counter += 1
    means = {k: float(np.mean(values)) for k, values in returns.items()}
    selected = max(FIXED_KS, key=lambda k: (means[k], k))
    return selected, {
        "selection_seeds": list(SELECTION_SEEDS),
        "episodes_per_duration_mismatch_cell": config.selection_episodes_per_cell,
        "mean_validation_return": {str(k): means[k] for k in FIXED_KS},
        "tie_rule": "larger k", "selected_k": selected,
    }, ticks


def _training_episode(seed: int, episode: int, config: RunConfig) -> ExogenousEpisode:
    joint = bool(episode % 2)
    return generate_episode(
        seed=seed, episode=episode, namespace="paired_training",
        cell=f"TRAIN_{'ON' if joint else 'OFF'}", durations=TRAIN_DURATIONS,
        noise=0.05, joint_mismatch=joint, horizon=config.horizon,
    )


def train_seed(
    seed: int, config: RunConfig, checkpoint_root: Path,
) -> tuple[dict[str, PPOHazardLearner], dict[str, object], dict[str, object], int]:
    learners = {arm: PPOHazardLearner(seed) for arm in LEARNED_ARMS}
    collected: dict[str, list[EpisodeResult]] = {arm: [] for arm in LEARNED_ARMS}
    for episode in range(config.training_episodes):
        exogenous = _training_episode(seed, episode, config)
        for arm in LEARNED_ARMS:
            learner = learners[arm]
            collected[arm].append(run_episode(
                exogenous, arm=arm, actor=learner,
                critic_value=learner.critic_value, collect_training=True,
            ))
    diagnostics: dict[str, object] = {}
    activity_arms: dict[str, object] = {}
    for arm, learner in learners.items():
        update = learner.update(collected[arm], base_seed=seed, arm=arm, config=config)
        checkpoint_path = checkpoint_root / f"seed_{seed}" / f"{arm}.pt"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(learner.checkpoint(), checkpoint_path)
        by_cell: dict[str, list[EpisodeResult]] = defaultdict(list)
        for episode, row in enumerate(collected[arm]):
            by_cell[_training_episode(seed, episode, config).cell].append(row)
        diagnostics[arm] = {
            "ppo": update.__dict__,
            "actor_parameter_count": learner.actor_parameter_count,
            "critic_parameter_count": learner.critic_parameter_count,
            "by_phase_cell": {
                cell: {
                    **summarize_episodes(rows),
                    "hazard_entropy_by_role": [
                        float(np.mean([
                            record.entropy[role]
                            for episode_row in rows for record in episode_row.training_records
                            if record.policy_mask[role]
                        ])) for role in range(2)
                    ],
                } for cell, rows in by_cell.items()
            },
            "checkpoint": str(checkpoint_path),
        }
        first = collected[arm][0]
        activity_arms[arm] = {
            "complete_episode_ticks": len(first.training_records),
            "hazard_actions_by_role": [
                int(sum(record.actions[role] for record in first.training_records)) for role in range(2)
            ],
            "policy_eligible_records": int(sum(record.policy_mask.sum() for record in first.training_records)),
            "ordinary_renewals": list(first.ordinary_renewals),
            "optimizer_steps_in_valid_update": update.optimizer_steps,
        }
    activity = {
        "criterion": (
            "both learned arms used their first complete paired 128-tick episodes in a valid PPO "
            "optimizer update and emitted hazard/action/count records"
        ),
        "reached": all(
            row["complete_episode_ticks"] == config.horizon and row["optimizer_steps_in_valid_update"] > 0
            for row in activity_arms.values()
        ),
        "base_seed": seed, "paired_training_episode": 0, "arms": activity_arms,
    }
    ticks = len(LEARNED_ARMS) * config.training_episodes * config.horizon
    return learners, diagnostics, activity, ticks


def _panel_episodes(
    *, seed: int, tempo: str, joint: bool, count: int, config: RunConfig,
    safety: bool, episode_offset: int,
) -> list[ExogenousEpisode]:
    durations, noise = CONCLUSION_CELLS[tempo]
    namespace = "paired_safety_panel" if safety else "paired_conclusion_panel"
    return [
        generate_episode(
            seed=seed, episode=episode_offset + repeat, namespace=namespace,
            cell=f"{tempo}_{'ON' if joint else 'OFF'}", durations=durations,
            noise=noise, joint_mismatch=joint, horizon=config.horizon, safety=safety,
        ) for repeat in range(count)
    ]


def evaluate_seed_panel(
    seed: int, learners: dict[str, PPOHazardLearner], config: RunConfig, *, safety: bool,
) -> tuple[dict[str, dict[str, dict[str, object]]], dict[str, object], int]:
    per_arm_cell: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    eligibility: dict[str, object] = {}
    ticks = 0
    count = config.safety_episodes_per_cell if safety else config.primary_episodes_per_cell
    cell_index = 0
    for tempo in CONCLUSION_CELLS:
        for joint in (False, True):
            cell = f"{tempo}_{'ON' if joint else 'OFF'}"
            episodes = _panel_episodes(
                seed=seed, tempo=tempo, joint=joint, count=count, config=config,
                safety=safety, episode_offset=cell_index * count,
            )
            rows: dict[str, list[EpisodeResult]] = defaultdict(list)
            coord_sources: list[EpisodeResult] = []
            for exogenous in episodes:
                for fixed in FIXED_ARMS:
                    rows[fixed].append(run_episode(
                        exogenous, arm=fixed, actor=learners["COORD"]
                    ))
                    ticks += config.horizon
                local = run_episode(exogenous, arm="LOCAL", actor=learners["LOCAL"])
                coord = run_episode(exogenous, arm="COORD", actor=learners["COORD"])
                oracle = run_episode(exogenous, arm="STAGE-ORACLE", actor=learners["COORD"])
                rows["LOCAL"].append(local)
                rows["COORD"].append(coord)
                rows["STAGE-ORACLE"].append(oracle)
                coord_sources.append(coord)
                ticks += 3 * config.horizon
            yokes = yoked_schedules(episodes, coord_sources)
            shuffle_reasons: dict[str, int] = defaultdict(int)
            yoke_reasons: dict[str, int] = defaultdict(int)
            for index, (exogenous, source) in enumerate(zip(episodes, coord_sources)):
                schedule, eligible, reason = shuffled_schedule(source, exogenous)
                shuffle_reasons[reason] += 1
                if eligible:
                    rows["COORD-SHUFFLE"].append(run_episode(
                        exogenous, arm="COORD-SHUFFLE", schedule=schedule,
                        actor=learners["COORD"],
                    ))
                    rows["COORD-SHUFFLE-REFERENCE"].append(source)
                    ticks += config.horizon
                yoke, yoke_eligible, yoke_reason, _donor = yokes[index]
                yoke_reasons[yoke_reason] += 1
                if yoke_eligible and yoke is not None:
                    rows["COORD-YOKED"].append(run_episode(
                        exogenous, arm="COORD-YOKED", schedule=yoke,
                        actor=learners["COORD"],
                    ))
                    rows["COORD-YOKED-REFERENCE"].append(source)
                    ticks += config.horizon
            eligibility[cell] = {
                "exogenous_balance": balance_report(episodes),
                "COORD-SHUFFLE": {
                    "eligible": len(rows["COORD-SHUFFLE"]), "total": count,
                    "rate": len(rows["COORD-SHUFFLE"]) / count,
                    "reasons": dict(shuffle_reasons),
                },
                "COORD-YOKED": {
                    "eligible": len(rows["COORD-YOKED"]), "total": count,
                    "rate": len(rows["COORD-YOKED"]) / count,
                    "reasons": dict(yoke_reasons),
                },
            }
            for arm, arm_rows in rows.items():
                per_arm_cell[arm][cell] = summarize_episodes(arm_rows)
            cell_index += 1
    return dict(per_arm_cell), eligibility, ticks


def _registered_budget_facts(config: RunConfig) -> dict[str, int]:
    training = len(config.base_seeds) * len(LEARNED_ARMS) * config.training_episodes * config.horizon
    selection = len(SELECTION_SEEDS) * len(VALIDATION_DURATIONS) * 2 * config.selection_episodes_per_cell * len(FIXED_KS) * config.horizon
    maximum_panel = len(config.base_seeds) * 8 * (
        config.primary_episodes_per_cell + config.safety_episodes_per_cell
    ) * 9 * config.horizon
    return {
        "training_team_ticks": training,
        "fixed_selection_team_ticks": selection,
        "maximum_panel_team_ticks": maximum_panel,
        "maximum_evaluation_team_ticks": selection + maximum_panel,
        "maximum_total_team_ticks": training + selection + maximum_panel,
    }


def _decision_statements(
    analysis: dict[str, object], *, timing_identifying: bool,
    safety_failures: list[dict[str, object]],
) -> dict[str, object]:
    contrasts: dict[str, Any] = analysis["paired_contrasts"]  # type: ignore[assignment]
    adaptive: dict[str, dict[str, dict[str, object]]] = {}
    for arm in LEARNED_ARMS:
        comparison = contrasts.get(f"{arm}_minus_FIXED-BEST", {})
        adaptive[arm] = {}
        for estimand, name, threshold in (("P", "performance", 0.02), ("W", "robustness", 0.03)):
            row = comparison.get(estimand, {})
            adaptive[arm][name] = {
                "estimand": estimand, "mean_threshold": threshold,
                "requires_positive_95pct_lcb": True,
                "observed": row,
                "supported": bool(row and row["lower"] is not None
                                  and row["lower"] > 0.0 and row["mean"] >= threshold),
            }
    cooperative: dict[str, dict[str, object]] = {}
    for estimand, name in (("P", "performance"), ("W", "robustness")):
        separations = {
            label: contrasts.get(label, {}).get(estimand, {}) for label in (
                "COORD_minus_LOCAL", "COORD_minus_COORD-SHUFFLE", "COORD_minus_COORD-YOKED"
            )
        }
        separation_supported = all(
            row and row["lower"] is not None and row["lower"] > 0.0 and row["mean"] >= 0.01
            for row in separations.values()
        )
        cooperative[name] = {
            "coord_variable_k_benefit": adaptive["COORD"][name]["supported"],
            "mean_separation_threshold": 0.01,
            "paired_separations": separations,
            "local_and_timing_separations_supported": separation_supported,
            "timing_control_eligibility_at_least_90pct_every_cell": timing_identifying,
            "zero_emergency_or_cap_failures": not safety_failures,
            "supported": bool(
                adaptive["COORD"][name]["supported"] and separation_supported
                and timing_identifying and not safety_failures
            ),
        }
    return {"variable_k": adaptive, "cooperative_renewal": cooperative}


def _collect_safety_failures(
    all_safety: dict[str, object], config: RunConfig,
) -> list[dict[str, object]]:
    """Fail closed on both unsafe observations and missing safety-panel coverage."""
    failures: list[dict[str, object]] = []
    expected_cells = tuple(
        f"{tempo}_{mode}"
        for tempo in CONCLUSION_CELLS
        for mode in ("OFF", "ON")
    )
    for seed in config.base_seeds:
        arms: dict[str, dict[str, dict[str, object]]] = all_safety.get(  # type: ignore[assignment]
            str(seed), {}
        )
        for arm in UNIQUE_EVALUATION_ARMS:
            cells = arms.get(arm, {})
            for cell in expected_cells:
                summary = cells.get(cell, {})
                observed = int(summary.get("episodes", 0))
                if observed != config.safety_episodes_per_cell:
                    failures.append({
                        "seed": str(seed), "arm": arm, "cell": cell,
                        "reason": "incomplete_safety_panel_coverage",
                        "observed_episodes": observed,
                        "expected_episodes": config.safety_episodes_per_cell,
                    })
                    continue
                if (
                    float(summary["emergency_immediate_rate"]) != 1.0
                    or int(summary["cap_violations"]) != 0
                ):
                    failures.append({
                        "seed": str(seed), "arm": arm, "cell": cell,
                        "reason": "emergency_or_cap_failure",
                    })
    return failures


def exercise(*, output_root: Path, result_path: Path, config: RunConfig = PRODUCTION_CONFIG) -> dict[str, object]:
    if output_root.exists():
        raise FileExistsError("exercise requires a fresh output root")
    if result_path.exists():
        raise FileExistsError("result path already exists")
    if config.horizon > 128:
        raise ValueError("internal configurations may bound but not enlarge the registered horizon")
    budget_facts = _registered_budget_facts(config)
    if config.registered:
        if budget_facts["training_team_ticks"] != DECLARED_BUDGETS["training_team_ticks"]:
            raise RuntimeError("production training budget changed")
        if budget_facts["maximum_evaluation_team_ticks"] > config.evaluation_tick_cap:
            raise RuntimeError("production evaluation plan exceeds cap")
        if budget_facts["maximum_total_team_ticks"] > config.total_tick_cap:
            raise RuntimeError("production total plan exceeds cap")
    output_root.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    peak_rss = _rss_bytes()
    actual_ticks = 0
    torch.set_num_threads(config.cpu_workers)
    dummy_actor = PPOHazardLearner(0)
    selected_k, selection, selection_ticks = select_fixed_k(config, dummy_actor)
    selected_arm = f"FIXED-{selected_k}"
    actual_ticks += selection_ticks
    peak_rss = _check_caps(started, peak_rss, actual_ticks, config)
    all_primary: dict[int, dict[str, dict[str, dict[str, object]]]] = {}
    all_safety: dict[str, object] = {}
    training_diagnostics: dict[str, object] = {}
    eligibility: dict[str, object] = {}
    activity: dict[str, object] | None = None
    for seed in config.base_seeds:
        learners, diagnostics, seed_activity, training_ticks = train_seed(
            seed, config, output_root / "checkpoints"
        )
        training_diagnostics[str(seed)] = diagnostics
        actual_ticks += training_ticks
        if activity is None:
            activity = seed_activity
            _write_json(output_root / "activity_start.json", activity)
        primary, primary_eligibility, primary_ticks = evaluate_seed_panel(
            seed, learners, config, safety=False
        )
        safety_rows, safety_eligibility, safety_ticks = evaluate_seed_panel(
            seed, learners, config, safety=True
        )
        all_primary[seed] = primary
        all_safety[str(seed)] = safety_rows
        eligibility[str(seed)] = {
            "primary": primary_eligibility, "safety": safety_eligibility,
        }
        actual_ticks += primary_ticks + safety_ticks
        peak_rss = _check_caps(started, peak_rss, actual_ticks, config)
    if not activity or not activity["reached"]:
        raise RuntimeError("scientific activity witness was not reached")
    evaluation_ticks = actual_ticks - budget_facts["training_team_ticks"]
    if config.registered and evaluation_ticks > config.evaluation_tick_cap:
        raise RuntimeError("actual evaluation team ticks exceed registered cap")
    control_rates = [
        record[control]["rate"]
        for seed_rows in eligibility.values()
        for record in seed_rows["primary"].values()
        for control in ("COORD-SHUFFLE", "COORD-YOKED")
    ]
    all_controls_identifying = all(rate >= 0.90 for rate in control_rates)
    analysis = analyze_seed_cells(all_primary, selected_fixed_arm=selected_arm)
    for rows in all_primary.values():
        rows["FIXED-BEST"] = {
            cell: dict(summary) for cell, summary in rows[selected_arm].items()
        }
    for rows in all_safety.values():
        rows["FIXED-BEST"] = {
            cell: dict(summary) for cell, summary in rows[selected_arm].items()
        }
    hindsight = {
        str(seed): {
            cell: max(float(rows[arm][cell]["mean_return"]) for arm in FIXED_ARMS)
            for cell in next(iter(rows.values()))
        } for seed, rows in all_primary.items()
    }
    safety_failures = _collect_safety_failures(all_safety, config)
    decision_statements = _decision_statements(
        analysis, timing_identifying=all_controls_identifying,
        safety_failures=safety_failures,
    )
    elapsed = time.perf_counter() - started
    result: dict[str, object] = {
        "artifact_kind": ARTIFACT_KIND, "treatment": TREATMENT,
        "production_defaults": config.registered,
        "configuration": config.__dict__, "ppo": PPO,
        "declared_budgets": DECLARED_BUDGETS,
        "planned_budget_facts": budget_facts,
        "actual_budgets": {
            "training_team_ticks": budget_facts["training_team_ticks"],
            "evaluation_team_ticks": evaluation_ticks,
            "total_team_ticks": actual_ticks,
            "wall_seconds": elapsed, "peak_rss_bytes": peak_rss,
            "cpu_workers": config.cpu_workers,
        },
        "fixed_grid_selection": selection,
        "selected_fixed_arm": selected_arm,
        "scientific_activity": activity,
        "training_diagnostics": training_diagnostics,
        "primary_seed_cell_metrics": {str(seed): rows for seed, rows in all_primary.items()},
        "safety_seed_cell_metrics": all_safety,
        "control_eligibility": eligibility,
        "primary_timing_controls_identifying": all_controls_identifying,
        "analysis": analysis,
        "registered_decision_statements": decision_statements,
        "test_cell_hindsight_fixed_grid_envelope": hindsight,
        "safety_failures": safety_failures,
        "material_anomalies": ([] if all_controls_identifying else [
            "At least one primary timing-control cell is below 90% schedule eligibility."
        ]) + ([] if not safety_failures else ["At least one safety-panel arm/cell failed emergency or cap accounting."]),
        "claim_ceiling": (
            "Constructed two-agent binary-skill exogenous-switch host, registered features, PPO, "
            "fixed grid, timing controls, oracle, caps, safety override, seeds and eight conclusion cells only."
        ),
    }
    _write_json(output_root / "raw_result.json", result)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run EBCR-B1 train/evaluate/analyze")
    parser.add_argument("action", choices=("exercise",))
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    result = exercise(
        output_root=args.output_root.resolve(), result_path=args.result.resolve(),
        config=PRODUCTION_CONFIG,
    )
    print(json.dumps({
        "result": str(args.result.resolve()),
        "activity_reached": result["scientific_activity"]["reached"],
        "selected_fixed_arm": result["selected_fixed_arm"],
        "total_team_ticks": result["actual_budgets"]["total_team_ticks"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

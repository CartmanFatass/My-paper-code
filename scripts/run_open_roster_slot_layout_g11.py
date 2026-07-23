"""Evaluate frozen G8 policies under isomorphic lifecycle-slot layouts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    collect_direct_trajectory,
    evaluate_direct_policy,
    make_action_uniforms,
    maximum_state_difference,
    model_state_copy,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_high_churn_g9 import (
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)
from ha_ctse_process.open_roster_slot_layout_g11 import (
    DENSE_LAYOUT,
    LAYOUTS,
    LOGICAL_CAPACITY,
    make_layout_factory,
    make_layout_ledger,
    remap_uniforms,
)
from scripts import run_open_roster_high_churn_g9 as core


ALGORITHM_ID = "SLOT_LAYOUT_INVARIANCE_G11"
AUTHORIZATION_TOKEN = "AUTHORIZE_SLOT_LAYOUT_INVARIANCE_G11_FORMAL_CPU_V1"
INVALID_BRANCH = "INVALID_SLOT_LAYOUT_INVARIANCE_G11"
NONFORMAL_BRANCH = "NONFORMAL_SLOT_LAYOUT_G11_EXERCISE_COMPLETE"
FORMAL_REPLICATES = 3
FORMAL_EVAL_EPISODES = 64
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
LEDGER_SEED = 2_681_000
ACTION_SEED_BASE = 2_781_000
BOOTSTRAP_SEED = 2_881_011
DENSE_ACCESS_FLOOR = 0.90
MINIMUM_LAYOUT_REPLICATE_FLOOR = 0.85
LAYOUT_STOCHASTIC_MEAN_FLOOR = 0.80
DEFAULT_G8_RUN_ROOT = core.DEFAULT_G8_RUN_ROOT


def select_result_branch(metrics: dict[str, Any]) -> str:
    if float(metrics["dense48_deterministic_utility_ci95"][0]) < DENSE_ACCESS_FLOOR:
        return "NO_DENSE_LAYOUT_ACCESS_G11"
    mismatch_branches = (
        ("reverse48", "REVERSE_SLOT_DEPENDENCE_G11"),
        ("sparse96", "SPARSE_SLOT_DEPENDENCE_G11"),
        ("affine_padded128", "PADDING_SLOT_DEPENDENCE_G11"),
    )
    for layout, branch in mismatch_branches:
        if int(metrics[f"{layout}_paired_outcome_mismatch_count"]) != 0:
            return branch
    if (
        float(metrics["layout_min_replicate_mean"])
        < MINIMUM_LAYOUT_REPLICATE_FLOOR
        or float(metrics["layout_stochastic_mean"])
        < LAYOUT_STOCHASTIC_MEAN_FLOOR
    ):
        return "UNSTABLE_SLOT_LAYOUT_G11"
    return "SLOT_LAYOUT_INVARIANT_G11"


def _activate_contract() -> None:
    core.ALGORITHM_ID = ALGORITHM_ID
    core.AUTHORIZATION_TOKEN = AUTHORIZATION_TOKEN
    core.INVALID_BRANCH = INVALID_BRANCH
    core.NONFORMAL_BRANCH = NONFORMAL_BRANCH
    core.FORMAL_REPLICATES = FORMAL_REPLICATES
    core.FORMAL_EVAL_EPISODES = FORMAL_EVAL_EPISODES
    core.FORMAL_BOOTSTRAP_REPETITIONS = FORMAL_BOOTSTRAP_REPETITIONS
    core.ACTION_SEED_BASE = ACTION_SEED_BASE
    core.BOOTSTRAP_SEED = BOOTSTRAP_SEED


_activate_contract()

_read_json = core._read_json
_write_json = core._write_json
_model = core._model
train = core.train


def _source_controls() -> dict[str, Any]:
    rows = []
    dense = make_layout_ledger(0, master_seed=LEDGER_SEED, layout=DENSE_LAYOUT)
    for layout in LAYOUTS:
        ledger = make_layout_ledger(0, master_seed=LEDGER_SEED, layout=layout)
        environment = HighChurnEnv(ledger)
        while environment.time < HORIZON:
            view = environment.observe()
            environment.step(constructive_actions(environment, view))
        outcome = environment.outcome()
        core.configure_runtime(ACTION_SEED_BASE)
        trajectory = collect_direct_trajectory(
            _model(),
            ledger_ids=(0,),
            ledger_seed=LEDGER_SEED,
            action_seed=ACTION_SEED_BASE,
            device=torch.device("cpu"),
            ledger_factory=make_layout_factory(layout),
            environment_factory=HighChurnEnv,
        )
        mapped_priorities_exact = all(
            np.array_equal(
                getattr(ledger, field)[:, physical],
                getattr(dense, field)[:, logical],
            )
            for field in (
                "owner_priorities",
                "presentation_priorities",
                "direct_frontier_priorities",
            )
            for logical, physical in enumerate(layout.logical_to_physical)
        )
        rows.append(
            {
                "layout": layout.name,
                "capacity": layout.capacity,
                "mapping": list(layout.logical_to_physical),
                "mapping_injective": len(set(layout.logical_to_physical))
                == LOGICAL_CAPACITY,
                "wave_arrivals_exact": ledger.wave_arrivals == dense.wave_arrivals,
                "mapped_priorities_exact": mapped_priorities_exact,
                "roster_sizes": list(outcome.roster_sizes),
                "expected_roster_sizes": list(
                    expected_roster_schedule(ledger.profile)
                ),
                "short_required_total": outcome.short_required_total,
                "expected_short_requirement": ledger.expected_short_requirement,
                "constructive_utility": outcome.utility,
                "lifecycle_contract_valid": high_churn_lifecycle_contract_valid(
                    trajectory,
                    ledger_seed=LEDGER_SEED,
                    ledger_factory=make_layout_factory(layout),
                ),
            }
        )
    return {
        "rows": rows,
        "all_layouts_present": {row["layout"] for row in rows}
        == {layout.name for layout in LAYOUTS},
        "all_mappings_injective": all(row["mapping_injective"] for row in rows),
        "all_wave_arrivals_exact": all(row["wave_arrivals_exact"] for row in rows),
        "all_priorities_isomorphic": all(
            row["mapped_priorities_exact"] for row in rows
        ),
        "all_roster_schedules_exact": all(
            row["roster_sizes"] == row["expected_roster_sizes"] for row in rows
        ),
        "all_requirements_exact": all(
            row["short_required_total"] == row["expected_short_requirement"]
            for row in rows
        ),
        "all_constructive_utility_one": all(
            row["constructive_utility"] == 1.0 for row in rows
        ),
        "all_lifecycle_contracts_valid": all(
            row["lifecycle_contract_valid"] for row in rows
        ),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if training.get("status") != "COMPLETE":
        raise ValueError("G11 evaluation requires complete checkpoint import")
    eval_episodes = int(training["counts"]["eval_episodes"])
    episode_ids = tuple(range(eval_episodes))
    cells: list[dict[str, Any]] = []
    for row in training["replicate_results"]:
        replicate = int(row["replicate"])
        core.configure_runtime(ACTION_SEED_BASE + replicate)
        model, _bundle = core._load_final(run_root / row["checkpoint"])
        logical_uniforms = make_action_uniforms(
            episode_ids,
            lifecycle_capacity=LOGICAL_CAPACITY,
            action_seed=ACTION_SEED_BASE + replicate,
        )
        for layout in LAYOUTS:
            factory = make_layout_factory(layout)
            for deterministic in (True, False):
                before = model_state_copy(model)
                values = evaluate_direct_policy(
                    model,
                    episode_ids=episode_ids,
                    deterministic=deterministic,
                    device=torch.device("cpu"),
                    ledger_seed=LEDGER_SEED,
                    action_seed=ACTION_SEED_BASE + replicate,
                    uniforms=(
                        None
                        if deterministic
                        else remap_uniforms(logical_uniforms, layout)
                    ),
                    ledger_factory=factory,
                    environment_factory=HighChurnEnv,
                )
                difference = maximum_state_difference(
                    before, model_state_copy(model)
                )
                cells.append(
                    {
                        "replicate": replicate,
                        "checkpoint": "g8_final",
                        "layout": layout.name,
                        "capacity": layout.capacity,
                        "deterministic": deterministic,
                        "episode_ids": list(episode_ids),
                        "profile_names": [
                            f"oscillating_scale_churn_8_edits__{layout.name}"
                        ]
                        * eval_episodes,
                        "persistent": values["persistent"].tolist(),
                        "short": values["short"].tolist(),
                        "utility": values["utility"].tolist(),
                        "persistent_mean": values["persistent_mean"],
                        "short_mean": values["short_mean"],
                        "utility_mean": values["utility_mean"],
                        "model_state_maximum_difference": difference,
                        "model_state_unchanged_exact": difference == 0.0,
                    }
                )
    result = {
        "schema_version": 1,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": bool(training["formal"]),
        "source_commit": training["source_commit"],
        "runtime": core._runtime_identity(),
        "source_controls": _source_controls(),
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _evaluation_errors(
    training: dict[str, Any], evaluation: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if evaluation.get("algorithm") != ALGORITHM_ID or evaluation.get("status") != "COMPLETE":
        errors.append("evaluation identity/status mismatch")
    if evaluation.get("source_commit") != training.get("source_commit") or bool(
        evaluation.get("formal")
    ) != bool(training.get("formal")):
        errors.append("evaluation source/formal mismatch")
    if not core._runtime_valid(evaluation.get("runtime")):
        errors.append("evaluation runtime mismatch")
    controls = evaluation.get("source_controls", {})
    control_flags = (
        "all_layouts_present",
        "all_mappings_injective",
        "all_wave_arrivals_exact",
        "all_priorities_isomorphic",
        "all_roster_schedules_exact",
        "all_requirements_exact",
        "all_constructive_utility_one",
        "all_lifecycle_contracts_valid",
    )
    if (
        not isinstance(controls, dict)
        or len(controls.get("rows", [])) != len(LAYOUTS)
        or any(controls.get(flag) is not True for flag in control_flags)
    ):
        errors.append("slot-layout source controls failed")
    else:
        rows = controls["rows"]
        if {row.get("layout") for row in rows} != {
            layout.name for layout in LAYOUTS
        }:
            errors.append("slot-layout source-control inventory mismatch")
        for row in rows:
            layout = next(
                (item for item in LAYOUTS if item.name == row.get("layout")),
                None,
            )
            if layout is None:
                continue
            ledger = make_layout_ledger(
                0, master_seed=LEDGER_SEED, layout=layout
            )
            schedule = list(expected_roster_schedule(ledger.profile))
            if (
                row.get("capacity") != layout.capacity
                or row.get("mapping") != list(layout.logical_to_physical)
                or row.get("mapping_injective") is not True
                or row.get("wave_arrivals_exact") is not True
                or row.get("mapped_priorities_exact") is not True
                or row.get("roster_sizes") != schedule
                or row.get("expected_roster_sizes") != schedule
                or row.get("short_required_total")
                != ledger.expected_short_requirement
                or row.get("expected_short_requirement")
                != ledger.expected_short_requirement
                or float(row.get("constructive_utility", math.nan)) != 1.0
                or row.get("lifecycle_contract_valid") is not True
            ):
                errors.append("slot-layout source-control row mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list):
        errors.append("evaluation cell inventory missing")
        return errors
    replicates = int(training["counts"]["replicates"])
    expected = {
        (replicate, layout.name, deterministic)
        for replicate in range(replicates)
        for layout in LAYOUTS
        for deterministic in (True, False)
    }
    actual = {
        (cell.get("replicate"), cell.get("layout"), cell.get("deterministic"))
        for cell in cells
    }
    if actual != expected or len(cells) != len(expected):
        errors.append("evaluation cell inventory mismatch")
    eval_episodes = int(training["counts"]["eval_episodes"])
    layout_by_name = {layout.name: layout for layout in LAYOUTS}
    for cell in cells:
        layout = layout_by_name.get(cell.get("layout"))
        if cell.get("checkpoint") != "g8_final" or layout is None:
            errors.append("evaluation layout/checkpoint mismatch")
            continue
        if cell.get("capacity") != layout.capacity:
            errors.append("evaluation capacity mismatch")
        if cell.get("episode_ids") != list(range(eval_episodes)):
            errors.append("evaluation episode inventory mismatch")
        if cell.get("profile_names") != [
            f"oscillating_scale_churn_8_edits__{layout.name}"
        ] * eval_episodes:
            errors.append("evaluation profile inventory mismatch")
        if (
            cell.get("model_state_unchanged_exact") is not True
            or float(cell.get("model_state_maximum_difference", math.nan)) != 0.0
        ):
            errors.append("evaluation changed model state")
        for name in ("persistent", "short", "utility"):
            values = cell.get(name)
            if not isinstance(values, list) or len(values) != eval_episodes:
                errors.append(f"{name} array length mismatch")
                continue
            if any(
                not math.isfinite(float(value))
                or float(value) < 0.0
                or float(value) > 1.0
                for value in values
            ):
                errors.append(f"{name} array domain mismatch")
            if values and not math.isclose(
                float(np.mean(np.asarray(values, dtype=np.float64))),
                float(cell.get(f"{name}_mean", math.nan)),
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                errors.append(f"{name} mean mismatch")
    return errors


def _paired_mismatch_count(
    cells: list[dict[str, Any]], *, layout: str
) -> int:
    total = 0
    for replicate in range(max(int(cell["replicate"]) for cell in cells) + 1):
        for deterministic in (True, False):
            dense = next(
                cell
                for cell in cells
                if cell["replicate"] == replicate
                and cell["layout"] == DENSE_LAYOUT.name
                and cell["deterministic"] is deterministic
            )
            transformed = next(
                cell
                for cell in cells
                if cell["replicate"] == replicate
                and cell["layout"] == layout
                and cell["deterministic"] is deterministic
            )
            dense_values = np.stack(
                [dense["persistent"], dense["short"], dense["utility"]], axis=1
            )
            transformed_values = np.stack(
                [
                    transformed["persistent"],
                    transformed["short"],
                    transformed["utility"],
                ],
                axis=1,
            )
            total += int(np.any(dense_values != transformed_values, axis=1).sum())
    return total


def analyze(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    errors = core._training_errors(training, run_root) + _evaluation_errors(
        training, evaluation
    )
    operational_valid = not errors
    metrics: dict[str, Any] = {}
    branch = INVALID_BRANCH
    if operational_valid:
        cells = evaluation["cells"]
        deterministic_means = []
        stochastic_means = []
        for layout in LAYOUTS:
            layout_deterministic = [
                float(cell["utility_mean"])
                for cell in cells
                if cell["layout"] == layout.name and cell["deterministic"]
            ]
            metrics[f"{layout.name}_deterministic_utility_ci95"] = (
                core._bootstrap_replicate_ci(layout_deterministic)
            )
            deterministic_means.extend(layout_deterministic)
            stochastic_means.extend(
                float(cell["utility_mean"])
                for cell in cells
                if cell["layout"] == layout.name and not cell["deterministic"]
            )
        for layout in LAYOUTS[1:]:
            metrics[f"{layout.name}_paired_outcome_mismatch_count"] = (
                _paired_mismatch_count(cells, layout=layout.name)
            )
        metrics["layout_min_replicate_mean"] = min(deterministic_means)
        metrics["layout_stochastic_mean"] = float(np.mean(stochastic_means))
        branch = (
            select_result_branch(metrics)
            if bool(training["formal"])
            else NONFORMAL_BRANCH
        )
    result = {
        "schema_version": 1,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE",
        "formal": bool(training.get("formal")),
        "source_commit": training.get("source_commit"),
        "operational_valid": operational_valid,
        "operational_errors": errors,
        "metrics": metrics,
        "thresholds": {
            "dense_deterministic_lcb_floor": DENSE_ACCESS_FLOOR,
            "paired_outcome_mismatch_count": 0,
            "minimum_layout_replicate_mean_floor": MINIMUM_LAYOUT_REPLICATE_FLOOR,
            "layout_stochastic_mean_floor": LAYOUT_STOCHASTIC_MEAN_FLOOR,
        },
        "bootstrap_seed": BOOTSTRAP_SEED,
        "branch": branch,
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, g8_run_root: Path = DEFAULT_G8_RUN_ROOT) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit="NONFORMAL_WORKTREE",
        formal=False,
        authorization_token=None,
        g8_run_root=g8_run_root,
        replicates=1,
        eval_episodes=4,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token", default=None)
    parser.add_argument("--g8-run-root", type=Path, default=DEFAULT_G8_RUN_ROOT)
    parser.add_argument("--replicates", type=int, default=FORMAL_REPLICATES)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "train":
        if args.source_commit is None:
            raise ValueError("train requires --source-commit")
        result = train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            g8_run_root=args.g8_run_root,
            replicates=args.replicates,
            eval_episodes=args.eval_episodes,
        )
    elif args.mode == "evaluate":
        result = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        result = analyze(run_root=args.run_root)
    else:
        result = exercise(run_root=args.run_root, g8_run_root=args.g8_run_root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

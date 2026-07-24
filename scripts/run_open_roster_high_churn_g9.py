"""Import G8 finals, evaluate high-frequency churn, and analyze G9."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import re
import shutil
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    LEARNING_RATE,
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
    evaluate_direct_policy,
    load_checkpoint,
    maximum_state_difference,
    model_state_copy,
    state_dict_finite,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, constructive_actions
from ha_ctse_process.open_roster_high_churn_g9 import (
    DOMAIN_PROFILES,
    LEDGER_FACTORIES,
    HighChurnEnv,
    expected_roster_schedule,
    high_churn_lifecycle_contract_valid,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = "HIGH_FREQUENCY_ROSTER_CHURN_G9"
AUTHORIZATION_TOKEN = "AUTHORIZE_HIGH_FREQUENCY_ROSTER_CHURN_G9_FORMAL_CPU_V1"
INVALID_BRANCH = "INVALID_HIGH_FREQUENCY_CHURN_G9"
NONFORMAL_BRANCH = "NONFORMAL_HIGH_FREQUENCY_CHURN_G9_EXERCISE_COMPLETE"
G8_ALGORITHM_ID = "PREFIX_NORMALIZED_OPEN_ROSTER_G8"
G8_SOURCE_COMMIT = "fcce714c296c55f3dcb5a0c0ee11090b393c26ba"
G8_AUTHORIZATION_TOKEN = "AUTHORIZE_PREFIX_NORMALIZED_OPEN_ROSTER_G8_FORMAL_CPU_V1"
G8_BRANCH = "USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8"
G8_REPRESENTATION = {
    "active_aggregation": "sum",
    "count_coordinate": "log1p",
    "autoregressive_prefix": "active_fraction",
}
G8_RUN_RELATIVE = Path("logs/formal_open_roster_prefix_g8_cpu_20260723_fcce714_r1")
DEFAULT_G8_RUN_ROOT = PROJECT_ROOT / G8_RUN_RELATIVE
G8_UPDATES = 250
G8_NUM_ENVS = 8
G8_PPO_PASSES = 4
G8_EVAL_EPISODES = 128
FORMAL_REPLICATES = 3
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
DOMAIN_LEDGER_SEEDS = {
    "repeated_rejoin": 1_981_000,
    "load_proximal": 1_981_100,
    "mixed_churn": 1_981_200,
}
ACTION_SEED_BASE = 2_081_000
BOOTSTRAP_SEED = 2_181_009
DOMAIN_FLOORS = {
    "repeated_rejoin": 0.90,
    "load_proximal": 0.90,
    "mixed_churn": 0.90,
}
MINIMUM_MIXED_REPLICATE_FLOOR = 0.85
MIXED_STOCHASTIC_MEAN_FLOOR = 0.80
EXPECTED_EVENT_COUNT = 8
REQUIRE_UNIQUE_PROFILES = False
REQUIRED_EVENT_OPERATIONS = (
    "temporarily_left",
    "rejoined",
    "joined",
    "terminally_left",
)
EXPECTED_TORCH = "2.7.0+cpu"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def configure_runtime(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _runtime_valid(runtime: Any) -> bool:
    return bool(
        isinstance(runtime, dict)
        and runtime.get("backend") == "cpu"
        and runtime.get("torch") == EXPECTED_TORCH
        and runtime.get("torch_threads") == 1
        and Path(str(runtime.get("python", ""))).resolve()
        == Path(sys.executable).resolve()
    )


def _model() -> DirectPrimitiveARPolicy:
    return DirectPrimitiveARPolicy(autoregressive_prefix="active_fraction")


def _validate_g8_provenance(g8_run_root: Path) -> dict[str, Any]:
    training = _read_json(g8_run_root / "train_manifest.json")
    analysis = _read_json(g8_run_root / "analysis_result.json")
    expected_counts = {
        "replicates": FORMAL_REPLICATES,
        "updates": G8_UPDATES,
        "num_envs": G8_NUM_ENVS,
        "eval_episodes": G8_EVAL_EPISODES,
        "ppo_passes": G8_PPO_PASSES,
        "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
    }
    if (
        training.get("algorithm") != G8_ALGORITHM_ID
        or training.get("status") != "COMPLETE"
        or training.get("formal") is not True
        or training.get("source_commit") != G8_SOURCE_COMMIT
        or training.get("authorization_token") != G8_AUTHORIZATION_TOKEN
        or training.get("representation") != G8_REPRESENTATION
        or training.get("counts") != expected_counts
        or not _runtime_valid(training.get("runtime"))
    ):
        raise ValueError("G8 training provenance mismatch")
    if (
        analysis.get("algorithm") != G8_ALGORITHM_ID
        or analysis.get("status") != "COMPLETE"
        or analysis.get("formal") is not True
        or analysis.get("source_commit") != G8_SOURCE_COMMIT
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("branch") != G8_BRANCH
    ):
        raise ValueError("G8 analysis provenance mismatch")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != FORMAL_REPLICATES:
        raise ValueError("G8 replicate inventory mismatch")
    for replicate, row in enumerate(rows):
        if (
            row.get("replicate") != replicate
            or row.get("completed_updates") != G8_UPDATES
            or row.get("optimizer_steps") != G8_UPDATES * G8_PPO_PASSES
            or row.get("finite_updates") is not True
            or row.get("lifecycle_contract_valid") is not True
            or not (g8_run_root / str(row.get("final_checkpoint", ""))).is_file()
        ):
            raise ValueError("G8 replicate provenance mismatch")
    return {
        "algorithm": G8_ALGORITHM_ID,
        "source_commit": G8_SOURCE_COMMIT,
        "authorization_token": G8_AUTHORIZATION_TOKEN,
        "analysis_branch": G8_BRANCH,
        "representation": G8_REPRESENTATION,
        "runtime": training["runtime"],
        "counts": expected_counts,
        "run_root": str(g8_run_root.resolve()),
        "replicate_rows": rows,
    }


def _load_final(path: Path) -> tuple[DirectPrimitiveARPolicy, dict[str, Any]]:
    model = _model()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    bundle = load_checkpoint(path, model=model, optimizer=optimizer)
    if (
        int(bundle["completed_updates"]) != G8_UPDATES
        or int(bundle["next_ledger_id"]) != G8_UPDATES * G8_NUM_ENVS
        or not state_dict_finite(bundle["model_state"])
    ):
        raise ValueError("G8 final checkpoint contract mismatch")
    return model, bundle


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    g8_run_root: Path,
    replicates: int,
    eval_episodes: int,
) -> dict[str, Any]:
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("formal G9 authorization token mismatch")
        if replicates != FORMAL_REPLICATES or eval_episodes != FORMAL_EVAL_EPISODES:
            raise ValueError("formal G9 counts differ from the frozen contract")
        if re.fullmatch(r"[0-9a-f]{40}", str(source_commit)) is None:
            raise ValueError("formal G9 source commit must be full lowercase SHA-1")
    if replicates <= 0 or replicates > FORMAL_REPLICATES or eval_episodes <= 0:
        raise ValueError("G9 counts are invalid")
    configure_runtime(ACTION_SEED_BASE)
    provenance = _validate_g8_provenance(g8_run_root)
    run_root.mkdir(parents=True, exist_ok=False)
    checkpoint_root = run_root / "checkpoints"
    checkpoint_root.mkdir()
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for replicate in range(replicates):
        source_row = provenance["replicate_rows"][replicate]
        source_path = g8_run_root / source_row["final_checkpoint"]
        source_model, _source_bundle = _load_final(source_path)
        source_state = model_state_copy(source_model)
        target_path = checkpoint_root / f"replicate_{replicate}_g8_final.pt"
        shutil.copy2(source_path, target_path)
        copied_model, _copied_bundle = _load_final(target_path)
        copy_difference = maximum_state_difference(
            source_state, model_state_copy(copied_model)
        )
        if copy_difference != 0.0:
            raise ValueError("G9 checkpoint copy changed model state")
        rows.append(
            {
                "replicate": replicate,
                "checkpoint": str(target_path.relative_to(run_root)),
                "completed_updates": G8_UPDATES,
                "optimizer_steps": 0,
                "finite_model": True,
                "source_model_copy_maximum_difference": copy_difference,
                "g8_seeds": source_row["seeds"],
            }
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": bool(formal),
        "authorization_token": authorization_token,
        "source_commit": str(source_commit),
        "runtime": _runtime_identity(),
        "training_operation": "none_frozen_g8_checkpoint_import",
        "optimizer_steps": 0,
        "g8_provenance": {key: value for key, value in provenance.items() if key != "replicate_rows"},
        "counts": {
            "replicates": replicates,
            "eval_episodes": eval_episodes,
            "bootstrap_repetitions": (
                FORMAL_BOOTSTRAP_REPETITIONS if formal else 200
            ),
        },
        "replicate_results": rows,
        "wall_seconds": time.perf_counter() - started,
    }
    _write_json(run_root / "train_manifest.json", result)
    return result


def _event_signature(profile: Any) -> list[dict[str, Any]]:
    return [
        {
            "time": int(event.time),
            "temporarily_left": list(event.temporarily_left),
            "rejoined": list(event.rejoined),
            "joined": list(event.joined),
            "terminally_left": list(event.terminally_left),
        }
        for event in profile.events
    ]


def _source_controls(*, episode_ids: tuple[int, ...]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    lifecycle_rows: list[dict[str, Any]] = []
    for domain in DOMAIN_PROFILES:
        factory = LEDGER_FACTORIES[domain]
        for episode_id in episode_ids:
            ledger = factory(episode_id, master_seed=DOMAIN_LEDGER_SEEDS[domain])
            profile = ledger.profile
            environment = HighChurnEnv(ledger)
            while environment.time < HORIZON:
                view = environment.observe()
                environment.step(constructive_actions(environment, view))
            outcome = environment.outcome()
            expected_schedule = expected_roster_schedule(profile)
            rows.append(
                {
                    "domain": domain,
                    "episode_id": episode_id,
                    "profile": profile.name,
                    "event_count": len(profile.events),
                    "event_signature": _event_signature(profile),
                    "utility": outcome.utility,
                    "roster_sizes": list(outcome.roster_sizes),
                    "expected_roster_sizes": list(expected_schedule),
                    "short_required_total": outcome.short_required_total,
                    "expected_short_requirement": ledger.expected_short_requirement,
                }
            )
        configure_runtime(2_281_000)
        trajectory = collect_direct_trajectory(
            _model(),
            ledger_ids=(episode_ids[0],),
            ledger_seed=DOMAIN_LEDGER_SEEDS[domain],
            action_seed=ACTION_SEED_BASE,
            device=torch.device("cpu"),
            ledger_factory=factory,
            environment_factory=HighChurnEnv,
        )
        lifecycle_rows.append(
            {
                "domain": domain,
                "valid": high_churn_lifecycle_contract_valid(
                    trajectory,
                    ledger_seed=DOMAIN_LEDGER_SEEDS[domain],
                    ledger_factory=factory,
                ),
            }
        )
    return {
        "rows": rows,
        "lifecycle_rows": lifecycle_rows,
        "all_constructive_utility_one": all(row["utility"] == 1.0 for row in rows),
        "all_roster_schedules_exact": all(
            row["roster_sizes"] == row["expected_roster_sizes"] for row in rows
        ),
        "all_actual_wave_requirements_exact": all(
            row["short_required_total"] == row["expected_short_requirement"]
            for row in rows
        ),
        "all_event_counts_exact": all(
            row["event_count"] == EXPECTED_EVENT_COUNT for row in rows
        ),
        "all_lifecycle_states_exact": all(row["valid"] for row in lifecycle_rows),
        "all_profile_names_unique": (
            not REQUIRE_UNIQUE_PROFILES
            or len({row["profile"] for row in rows}) == len(rows)
        ),
        "all_event_operation_types_present": all(
            any(event[name] for row in rows for event in row["event_signature"])
            for name in REQUIRED_EVENT_OPERATIONS
        ),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if training.get("status") != "COMPLETE":
        raise ValueError("G9 evaluation requires complete import")
    eval_episodes = int(training["counts"]["eval_episodes"])
    episode_ids = tuple(range(eval_episodes))
    cells: list[dict[str, Any]] = []
    for row in training["replicate_results"]:
        replicate = int(row["replicate"])
        configure_runtime(ACTION_SEED_BASE + replicate)
        model, _bundle = _load_final(run_root / row["checkpoint"])
        for domain, factory in LEDGER_FACTORIES.items():
            for deterministic in (True, False):
                before = model_state_copy(model)
                values = evaluate_direct_policy(
                    model,
                    episode_ids=episode_ids,
                    deterministic=deterministic,
                    device=torch.device("cpu"),
                    ledger_seed=DOMAIN_LEDGER_SEEDS[domain],
                    action_seed=ACTION_SEED_BASE + replicate,
                    ledger_factory=factory,
                    environment_factory=HighChurnEnv,
                )
                difference = maximum_state_difference(before, model_state_copy(model))
                cells.append(
                    {
                        "replicate": replicate,
                        "checkpoint": "g8_final",
                        "domain": domain,
                        "deterministic": deterministic,
                        "episode_ids": list(episode_ids),
                        "profile_names": [
                            factory(
                                episode_id,
                                master_seed=DOMAIN_LEDGER_SEEDS[domain],
                            ).profile.name
                            for episode_id in episode_ids
                        ],
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
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": bool(training["formal"]),
        "source_commit": training["source_commit"],
        "runtime": _runtime_identity(),
        "source_controls": _source_controls(episode_ids=episode_ids),
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _training_errors(training: dict[str, Any], run_root: Path) -> list[str]:
    errors: list[str] = []
    if training.get("algorithm") != ALGORITHM_ID or training.get("status") != "COMPLETE":
        errors.append("training identity/status mismatch")
    if training.get("training_operation") != "none_frozen_g8_checkpoint_import" or training.get("optimizer_steps") != 0:
        errors.append("zero-training contract mismatch")
    if not _runtime_valid(training.get("runtime")):
        errors.append("training runtime mismatch")
    counts = training.get("counts", {})
    if bool(training.get("formal")):
        if training.get("authorization_token") != AUTHORIZATION_TOKEN:
            errors.append("authorization token mismatch")
        if re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit", ""))) is None:
            errors.append("source commit mismatch")
        if counts != {
            "replicates": FORMAL_REPLICATES,
            "eval_episodes": FORMAL_EVAL_EPISODES,
            "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
        }:
            errors.append("formal count contract mismatch")
    provenance = training.get("g8_provenance", {})
    if (
        provenance.get("algorithm") != G8_ALGORITHM_ID
        or provenance.get("source_commit") != G8_SOURCE_COMMIT
        or provenance.get("authorization_token") != G8_AUTHORIZATION_TOKEN
        or provenance.get("analysis_branch") != G8_BRANCH
        or provenance.get("representation") != G8_REPRESENTATION
        or not _runtime_valid(provenance.get("runtime"))
        or provenance.get("counts")
        != {
            "replicates": FORMAL_REPLICATES,
            "updates": G8_UPDATES,
            "num_envs": G8_NUM_ENVS,
            "eval_episodes": G8_EVAL_EPISODES,
            "ppo_passes": G8_PPO_PASSES,
            "bootstrap_repetitions": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    ):
        errors.append("G8 provenance mismatch")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(counts.get("replicates", -1)):
        errors.append("imported replicate inventory mismatch")
        return errors
    for replicate, row in enumerate(rows):
        if (
            row.get("replicate") != replicate
            or row.get("completed_updates") != G8_UPDATES
            or row.get("optimizer_steps") != 0
            or row.get("finite_model") is not True
            or float(row.get("source_model_copy_maximum_difference", math.nan)) != 0.0
            or not (run_root / str(row.get("checkpoint", ""))).is_file()
        ):
            errors.append("imported checkpoint mismatch")
    return errors


def _evaluation_errors(training: dict[str, Any], evaluation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if evaluation.get("algorithm") != ALGORITHM_ID or evaluation.get("status") != "COMPLETE":
        errors.append("evaluation identity/status mismatch")
    if evaluation.get("source_commit") != training.get("source_commit") or bool(evaluation.get("formal")) != bool(training.get("formal")):
        errors.append("evaluation source/formal mismatch")
    if not _runtime_valid(evaluation.get("runtime")):
        errors.append("evaluation runtime mismatch")
    controls = evaluation.get("source_controls", {})
    eval_episodes = int(training["counts"]["eval_episodes"])
    if (
        not isinstance(controls, dict)
        or len(controls.get("rows", [])) != len(DOMAIN_PROFILES) * eval_episodes
        or not controls.get("all_constructive_utility_one")
        or not controls.get("all_roster_schedules_exact")
        or not controls.get("all_actual_wave_requirements_exact")
        or not controls.get("all_event_counts_exact")
        or not controls.get("all_lifecycle_states_exact")
        or not controls.get("all_profile_names_unique")
        or not controls.get("all_event_operation_types_present")
    ):
        errors.append("source controls failed")
    else:
        expected_control_rows = {}
        for domain in DOMAIN_PROFILES:
            for episode_id in range(eval_episodes):
                ledger = LEDGER_FACTORIES[domain](
                    episode_id, master_seed=DOMAIN_LEDGER_SEEDS[domain]
                )
                profile = ledger.profile
                expected_control_rows[(domain, episode_id)] = {
                    "profile": profile.name,
                    "event_count": len(profile.events),
                    "event_signature": _event_signature(profile),
                    "roster_sizes": list(expected_roster_schedule(profile)),
                    "expected_short_requirement": ledger.expected_short_requirement,
                }
        observed_control_rows = controls["rows"]
        if {
            (row.get("domain"), row.get("episode_id"))
            for row in observed_control_rows
        } != set(expected_control_rows):
            errors.append("source-control domain inventory mismatch")
        for row in observed_control_rows:
            expected_row = expected_control_rows.get(
                (row.get("domain"), row.get("episode_id"))
            )
            if expected_row is None:
                continue
            if (
                row.get("profile") != expected_row["profile"]
                or row.get("event_count") != expected_row["event_count"]
                or row.get("event_signature") != expected_row["event_signature"]
                or row.get("roster_sizes") != expected_row["roster_sizes"]
                or row.get("expected_roster_sizes")
                != expected_row["roster_sizes"]
                or row.get("short_required_total")
                != expected_row["expected_short_requirement"]
                or row.get("expected_short_requirement")
                != expected_row["expected_short_requirement"]
                or float(row.get("utility", math.nan)) != 1.0
            ):
                errors.append("source-control row mismatch")
        lifecycle_rows = controls.get("lifecycle_rows")
        if not isinstance(lifecycle_rows, list) or {
            (row.get("domain"), row.get("valid")) for row in lifecycle_rows
        } != {(domain, True) for domain in DOMAIN_PROFILES}:
            errors.append("source-control lifecycle inventory mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list):
        errors.append("evaluation cell inventory missing")
        return errors
    replicates = int(training["counts"]["replicates"])
    expected = {
        (replicate, domain, deterministic)
        for replicate in range(replicates)
        for domain in DOMAIN_FLOORS
        for deterministic in (True, False)
    }
    actual = {
        (cell.get("replicate"), cell.get("domain"), cell.get("deterministic"))
        for cell in cells
    }
    if actual != expected or len(cells) != len(expected):
        errors.append("evaluation cell inventory mismatch")
    for cell in cells:
        if not cell.get("model_state_unchanged_exact") or float(cell.get("model_state_maximum_difference", math.nan)) != 0.0:
            errors.append("evaluation changed model state")
        domain = cell.get("domain")
        if cell.get("checkpoint") != "g8_final":
            errors.append("evaluation checkpoint label mismatch")
        if cell.get("episode_ids") != list(range(eval_episodes)):
            errors.append("evaluation episode inventory mismatch")
        expected_profiles = (
            [
                LEDGER_FACTORIES[domain](
                    episode_id, master_seed=DOMAIN_LEDGER_SEEDS[domain]
                ).profile.name
                for episode_id in range(eval_episodes)
            ]
            if domain in DOMAIN_PROFILES
            else None
        )
        if cell.get("profile_names") != expected_profiles:
            errors.append("evaluation profile inventory mismatch")
        for name in ("persistent", "short", "utility"):
            values = cell.get(name)
            if not isinstance(values, list) or len(values) != eval_episodes:
                errors.append(f"{name} array length mismatch")
                continue
            if any(not math.isfinite(float(value)) or float(value) < 0.0 or float(value) > 1.0 for value in values):
                errors.append(f"{name} array domain mismatch")
            if values and not math.isclose(
                float(np.mean(np.asarray(values, dtype=np.float64))),
                float(cell.get(f"{name}_mean", math.nan)),
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                errors.append(f"{name} mean mismatch")
    return errors


def _bootstrap_replicate_ci(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, array.size, size=(FORMAL_BOOTSTRAP_REPETITIONS, array.size))
    estimates = array[indices].mean(axis=1)
    return [float(np.quantile(estimates, 0.025)), float(array.mean()), float(np.quantile(estimates, 0.975))]


def select_result_branch(metrics: dict[str, Any]) -> str:
    if float(metrics["repeated_rejoin_deterministic_utility_ci95"][0]) < DOMAIN_FLOORS["repeated_rejoin"]:
        return "NO_REPEATED_REJOIN_ACCESS_G9"
    if float(metrics["load_proximal_deterministic_utility_ci95"][0]) < DOMAIN_FLOORS["load_proximal"]:
        return "NO_LOAD_PROXIMAL_CHURN_ACCESS_G9"
    if float(metrics["mixed_churn_deterministic_utility_ci95"][0]) < DOMAIN_FLOORS["mixed_churn"]:
        return "NO_MIXED_CHURN_ACCESS_G9"
    if (
        float(metrics["mixed_churn_min_replicate_mean"]) < MINIMUM_MIXED_REPLICATE_FLOOR
        or float(metrics["mixed_churn_stochastic_mean"]) < MIXED_STOCHASTIC_MEAN_FLOOR
    ):
        return "UNSTABLE_HIGH_FREQUENCY_CHURN_G9"
    return "ROBUST_HIGH_FREQUENCY_CHURN_G9"


def analyze(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    errors = _training_errors(training, run_root) + _evaluation_errors(training, evaluation)
    operational_valid = not errors
    metrics: dict[str, Any] = {}
    branch = INVALID_BRANCH
    if operational_valid:
        cells = evaluation["cells"]
        for domain in DOMAIN_FLOORS:
            means = [
                float(cell["utility_mean"])
                for cell in cells
                if cell["domain"] == domain and cell["deterministic"]
            ]
            metrics[f"{domain}_deterministic_utility_ci95"] = _bootstrap_replicate_ci(means)
        mixed = [
            float(cell["utility_mean"])
            for cell in cells
            if cell["domain"] == "mixed_churn" and cell["deterministic"]
        ]
        mixed_stochastic = [
            float(cell["utility_mean"])
            for cell in cells
            if cell["domain"] == "mixed_churn" and not cell["deterministic"]
        ]
        metrics.update(
            {
                "mixed_churn_replicate_means": mixed,
                "mixed_churn_min_replicate_mean": min(mixed),
                "mixed_churn_stochastic_mean": float(np.mean(mixed_stochastic)),
            }
        )
        branch = (
            select_result_branch(metrics)
            if bool(training["formal"])
            else NONFORMAL_BRANCH
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE",
        "formal": bool(training.get("formal")),
        "source_commit": training.get("source_commit"),
        "operational_valid": operational_valid,
        "operational_errors": errors,
        "metrics": metrics,
        "thresholds": {
            "domain_deterministic_lcb_floors": DOMAIN_FLOORS,
            "minimum_mixed_replicate_mean_floor": MINIMUM_MIXED_REPLICATE_FLOOR,
            "mixed_stochastic_mean_floor": MIXED_STOCHASTIC_MEAN_FLOOR,
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

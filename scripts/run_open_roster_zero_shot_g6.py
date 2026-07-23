"""Import, evaluate and analyze frozen G5 checkpoints under G6 stress."""

from __future__ import annotations

import argparse
from dataclasses import asdict
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
    MODEL_INITIALIZATION_SEED,
    POLICY_ACTION_SEED,
    TRAIN_LEDGER_SEED,
    DirectPrimitiveARPolicy,
    evaluate_direct_policy,
    load_checkpoint,
    maximum_state_difference,
    model_state_copy,
    nested_state_maximum_difference,
    state_dict_finite,
)
from ha_ctse_process.dynamic_roster_testbed import (
    ACTIVE,
    HORIZON,
    TEMPORARILY_ABSENT,
    TERMINAL,
    constructive_actions,
)
from ha_ctse_process.open_roster_zero_shot_g6 import (
    COUNT_SCALE_PROFILES,
    DOMAIN_PROFILES,
    EVENT_TIME_PROFILES,
    JOINT_PROFILES,
    LEDGER_FACTORIES,
    ZeroShotStressEnv,
)


SCHEMA_VERSION = 1
ALGORITHM_ID = "OPEN_ROSTER_ZERO_SHOT_SCALE_G6"
AUTHORIZATION_TOKEN = "AUTHORIZE_OPEN_ROSTER_ZERO_SHOT_SCALE_G6_FORMAL_CPU_V1"
G5_ALGORITHM_ID = "OPEN_ROSTER_DIRECT_MVP_G5"
G5_SOURCE_COMMIT = "4b38eae5abbaeccbab6d53e3eb8f50bd28b957a9"
G5_BRANCH = "USABLE_OPEN_ROSTER_DIRECT_G5"
G5_AUTHORIZATION_TOKEN = "AUTHORIZE_OPEN_ROSTER_DIRECT_MVP_G5_FORMAL_CPU_V1"
G5_RUN_RELATIVE = Path("logs/formal_open_roster_direct_g5_cpu_20260723_4b38eae_r1")
DEFAULT_G5_RUN_ROOT = PROJECT_ROOT / G5_RUN_RELATIVE
FORMAL_REPLICATES = 3
G5_COMPLETED_UPDATES = 250
G5_NUM_ENVS = 8
G5_PPO_PASSES = 4
FORMAL_EVAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
EXERCISE_EVAL_EPISODES = 4
EXERCISE_BOOTSTRAP_REPETITIONS = 200
COUNT_SCALE_LEDGER_SEED = 1_061_000
EVENT_TIME_LEDGER_SEED = 1_061_100
JOINT_LEDGER_SEED = 1_061_200
DOMAIN_LEDGER_SEEDS = {
    "count_scale": COUNT_SCALE_LEDGER_SEED,
    "event_time": EVENT_TIME_LEDGER_SEED,
    "joint": JOINT_LEDGER_SEED,
}
ACTION_SEED_BASE = 1_161_000
BOOTSTRAP_SEED = 1_261_006
COUNT_SCALE_FLOOR = 0.90
EVENT_TIME_FLOOR = 0.90
JOINT_FLOOR = 0.90
MINIMUM_JOINT_REPLICATE_FLOOR = 0.85
JOINT_STOCHASTIC_MEAN_FLOOR = 0.80
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


def _expected_g5_manifest_seeds(replicate: int) -> dict[str, int]:
    return {
        "model": 551_000 + int(replicate),
        "train_ledger": 651_000 + int(replicate),
        "action": 751_000 + int(replicate),
        "evaluation": 851_000 + int(replicate),
    }


def _embedded_rng_constants(bundle: dict[str, Any]) -> dict[str, int]:
    return {
        "model_initialization_seed": int(bundle["model_initialization_seed"]),
        "train_ledger_seed": int(bundle["train_ledger_seed"]),
        "policy_action_seed": int(bundle["policy_action_seed"]),
    }


def _strict_load_final_checkpoint(path: Path) -> tuple[dict[str, Any], dict[str, torch.Tensor]]:
    configure_runtime(MODEL_INITIALIZATION_SEED)
    model = DirectPrimitiveARPolicy()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    bundle = load_checkpoint(path, model=model, optimizer=optimizer)
    state = model_state_copy(model)
    if int(bundle.get("completed_updates", -1)) != G5_COMPLETED_UPDATES:
        raise ValueError("G5 provenance checkpoint completed_updates mismatch")
    if not state_dict_finite(state):
        raise ValueError("G5 provenance checkpoint model is non-finite")
    return bundle, state


def _validate_g5_provenance(g5_run_root: Path) -> dict[str, Any]:
    """Validate the entire closed G5 package before materializing any G6 file."""

    try:
        training_path = g5_run_root / "train_manifest.json"
        analysis_path = g5_run_root / "analysis_result.json"
        training = _read_json(training_path)
        analysis = _read_json(analysis_path)
        expected_counts = {
            "replicates": FORMAL_REPLICATES,
            "updates": G5_COMPLETED_UPDATES,
            "num_envs": G5_NUM_ENVS,
            "eval_episodes": FORMAL_EVAL_EPISODES,
            "ppo_passes": G5_PPO_PASSES,
        }
        if not (
            training.get("algorithm") == G5_ALGORITHM_ID
            and training.get("stage") == "train"
            and training.get("status") == "COMPLETE"
            and training.get("formal") is True
            and training.get("authorization_token") == G5_AUTHORIZATION_TOKEN
            and training.get("source_commit") == G5_SOURCE_COMMIT
            and training.get("counts") == expected_counts
        ):
            raise ValueError("training identity/counts mismatch")
        runtime = training.get("runtime")
        if not isinstance(runtime, dict) or not (
            runtime.get("backend") == "cpu"
            and runtime.get("torch") == EXPECTED_TORCH
            and runtime.get("torch_threads") == 1
        ):
            raise ValueError("training runtime mismatch")
        if not (
            analysis.get("algorithm") == G5_ALGORITHM_ID
            and analysis.get("stage") == "analyze"
            and analysis.get("status") == "COMPLETE"
            and analysis.get("formal") is True
            and analysis.get("source_commit") == G5_SOURCE_COMMIT
            and analysis.get("operational_valid") is True
            and analysis.get("branch") == G5_BRANCH
        ):
            raise ValueError("analysis identity/result mismatch")
        rows = training.get("replicate_results")
        if not isinstance(rows, list) or len(rows) != FORMAL_REPLICATES:
            raise ValueError("replicate inventory mismatch")
        checked: list[dict[str, Any]] = []
        for replicate, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError("replicate row is not an object")
            expected_relative = f"checkpoints\\replicate_{replicate}_final.pt"
            if not (
                row.get("replicate") == replicate
                and row.get("seeds") == _expected_g5_manifest_seeds(replicate)
                and row.get("final_checkpoint") == expected_relative
                and row.get("optimizer_steps") == G5_COMPLETED_UPDATES * G5_PPO_PASSES
                and row.get("finite_updates") is True
                and row.get("lifecycle_contract_valid") is True
            ):
                raise ValueError(f"replicate {replicate} manifest mismatch")
            source_checkpoint = g5_run_root / Path(expected_relative)
            bundle, _ = _strict_load_final_checkpoint(source_checkpoint)
            embedded = _embedded_rng_constants(bundle)
            expected_embedded = {
                "model_initialization_seed": MODEL_INITIALIZATION_SEED,
                "train_ledger_seed": TRAIN_LEDGER_SEED,
                "policy_action_seed": POLICY_ACTION_SEED,
            }
            if embedded != expected_embedded:
                raise ValueError(f"replicate {replicate} embedded RNG mismatch")
            checked.append(
                {
                    "replicate": replicate,
                    "source_checkpoint": source_checkpoint,
                    "g5_manifest_seeds": dict(row["seeds"]),
                    "checkpoint_embedded_rng_constants": embedded,
                    "completed_updates": int(bundle["completed_updates"]),
                }
            )
    except (KeyError, OSError, TypeError, ValueError) as error:
        if isinstance(error, ValueError) and str(error).startswith("G5 provenance"):
            raise
        raise ValueError(f"G5 provenance validation failed: {error}") from error
    return {
        "training": training,
        "analysis": analysis,
        "checked_replicates": checked,
    }


def _source_commit_valid(source_commit: str, *, formal: bool) -> bool:
    if source_commit == G5_SOURCE_COMMIT:
        return False
    if not formal and source_commit == "NONFORMAL_WORKTREE":
        return True
    return re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    g5_run_root: Path,
    eval_episodes: int,
    replicate_count: int | None = None,
) -> dict[str, Any]:
    """Strictly import frozen G5 finals; this function performs zero training."""

    if formal and authorization_token != AUTHORIZATION_TOKEN:
        raise ValueError("formal G6 authorization token mismatch")
    if not _source_commit_valid(str(source_commit), formal=bool(formal)):
        raise ValueError("G6 source commit must be valid and distinct from G5 training source")
    if formal and int(eval_episodes) != FORMAL_EVAL_EPISODES:
        raise ValueError("formal G6 eval episodes differ from the frozen contract")
    if int(eval_episodes) <= 0:
        raise ValueError("G6 eval episodes must be positive")
    requested_replicates = (
        FORMAL_REPLICATES if formal else 1
    ) if replicate_count is None else int(replicate_count)
    if requested_replicates <= 0 or requested_replicates > FORMAL_REPLICATES:
        raise ValueError("G6 imported replicate count is invalid")
    if formal and requested_replicates != FORMAL_REPLICATES:
        raise ValueError("formal G6 requires all three G5 replicates")
    if formal and g5_run_root.resolve() != DEFAULT_G5_RUN_ROOT.resolve():
        raise ValueError("formal G6 requires the exact registered G5 run root")

    provenance = _validate_g5_provenance(g5_run_root)
    run_root.mkdir(parents=True, exist_ok=False)
    checkpoint_root = run_root / "checkpoints"
    checkpoint_root.mkdir()
    started = time.perf_counter()
    replicate_rows: list[dict[str, Any]] = []
    for checked in provenance["checked_replicates"][:requested_replicates]:
        replicate = int(checked["replicate"])
        destination = checkpoint_root / f"replicate_{replicate}_g5_final.pt"
        shutil.copy2(checked["source_checkpoint"], destination)
        bundle, state = _strict_load_final_checkpoint(destination)
        source_bundle, _ = _strict_load_final_checkpoint(checked["source_checkpoint"])
        if nested_state_maximum_difference(source_bundle, bundle) != 0.0:
            raise RuntimeError("G6 checkpoint materialization differs from G5 source")
        replicate_rows.append(
            {
                "replicate": replicate,
                "checkpoint": str(destination.relative_to(run_root)),
                "completed_updates": int(bundle["completed_updates"]),
                "finite_model": bool(state_dict_finite(state)),
                "optimizer_steps": 0,
                "g5_manifest_seeds": checked["g5_manifest_seeds"],
                "checkpoint_embedded_rng_constants": checked[
                    "checkpoint_embedded_rng_constants"
                ],
                "manifest_and_embedded_rng_distinguished": (
                    checked["g5_manifest_seeds"]["model"]
                    != checked["checkpoint_embedded_rng_constants"][
                        "model_initialization_seed"
                    ]
                ),
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": bool(formal),
        "authorization_token": authorization_token,
        "source_commit": str(source_commit),
        "runtime": _runtime_identity(),
        "training_operation": "none_frozen_g5_checkpoint_import",
        "optimizer_steps": 0,
        "counts": {
            "replicates": requested_replicates,
            "eval_episodes": int(eval_episodes),
            "bootstrap_repetitions": (
                FORMAL_BOOTSTRAP_REPETITIONS
                if formal
                else EXERCISE_BOOTSTRAP_REPETITIONS
            ),
        },
        "g5_provenance": {
            "run_root": str(g5_run_root.resolve()),
            "algorithm": G5_ALGORITHM_ID,
            "source_commit": G5_SOURCE_COMMIT,
            "authorization_token": G5_AUTHORIZATION_TOKEN,
            "train_status": "COMPLETE",
            "train_runtime": {
                "backend": "cpu",
                "torch": EXPECTED_TORCH,
                "torch_threads": 1,
            },
            "train_counts": {
                "replicates": FORMAL_REPLICATES,
                "updates": G5_COMPLETED_UPDATES,
                "num_envs": G5_NUM_ENVS,
            },
            "analysis_status": "COMPLETE",
            "analysis_operational_valid": True,
            "analysis_branch": G5_BRANCH,
        },
        "replicate_results": replicate_rows,
        "wall_seconds": time.perf_counter() - started,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _expected_roster_schedule(profile: Any) -> list[int]:
    return [profile.active_count_at(time) for time in range(HORIZON)]


def _source_controls() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for domain, profiles in DOMAIN_PROFILES.items():
        factory = LEDGER_FACTORIES[domain]
        ledger_seed = DOMAIN_LEDGER_SEEDS[domain]
        for episode_id, profile in enumerate(profiles):
            ledger = factory(episode_id, master_seed=ledger_seed)
            environment = ZeroShotStressEnv(ledger)
            observed_events: dict[int, dict[str, list[int]]] = {}
            lifecycle_states_exact = True
            while environment.time < HORIZON:
                view = environment.observe()
                change = view.membership_change
                if any(
                    (
                        change.joined,
                        change.temporarily_left,
                        change.rejoined,
                        change.terminally_left,
                    )
                ):
                    observed_events[view.time] = {
                        "joined": list(change.joined),
                        "temporarily_left": list(change.temporarily_left),
                        "rejoined": list(change.rejoined),
                        "terminally_left": list(change.terminally_left),
                    }
                if view.time == 0:
                    lifecycle_states_exact &= all(
                        environment.lifecycles[key].status == ACTIVE
                        and environment.lifecycles[key].membership_epoch == 0
                        for key in ledger.initial_join
                    )
                elif view.time == profile.membership_event_times[0]:
                    lifecycle_states_exact &= all(
                        environment.lifecycles[key].status == TEMPORARILY_ABSENT
                        for key in ledger.temporary_leave
                    )
                elif view.time == profile.membership_event_times[1]:
                    lifecycle_states_exact &= all(
                        environment.lifecycles[key].status == ACTIVE
                        and environment.lifecycles[key].membership_epoch == 1
                        for key in ledger.temporary_leave
                    ) and all(
                        environment.lifecycles[key].status == ACTIVE
                        and environment.lifecycles[key].membership_epoch == 0
                        for key in ledger.genuine_join
                    )
                elif view.time == profile.membership_event_times[2]:
                    lifecycle_states_exact &= all(
                        environment.lifecycles[key].status == TERMINAL
                        for key in ledger.terminal_leave
                    )
                environment.step(constructive_actions(environment, view))
            outcome = environment.outcome()
            temporary_time, expansion_time, terminal_time = profile.membership_event_times
            events_exact = observed_events == {
                0: {
                    "joined": list(ledger.initial_join),
                    "temporarily_left": [],
                    "rejoined": [],
                    "terminally_left": [],
                },
                temporary_time: {
                    "joined": [],
                    "temporarily_left": list(ledger.temporary_leave),
                    "rejoined": [],
                    "terminally_left": [],
                },
                expansion_time: {
                    "joined": list(ledger.genuine_join),
                    "temporarily_left": [],
                    "rejoined": list(ledger.temporary_leave),
                    "terminally_left": [],
                },
                terminal_time: {
                    "joined": [],
                    "temporarily_left": [],
                    "rejoined": [],
                    "terminally_left": list(ledger.terminal_leave),
                },
            }
            expected_schedule = _expected_roster_schedule(profile)
            expected_requirement = sum(
                profile.active_count_at(arrival) - 1 for arrival in ledger.wave_arrivals
            )
            rows.append(
                {
                    "domain": domain,
                    "profile": profile.name,
                    "utility": float(outcome.utility),
                    "roster_sizes": list(outcome.roster_sizes),
                    "expected_roster_sizes": expected_schedule,
                    "wave_arrivals": list(ledger.wave_arrivals),
                    "short_required_total": int(outcome.short_required_total),
                    "expected_short_requirement_from_actual_waves": int(
                        expected_requirement
                    ),
                    "membership_events_exact": bool(events_exact),
                    "lifecycle_states_exact": bool(lifecycle_states_exact),
                    "terminal_lifecycle_destruction_valid": all(
                        environment.lifecycles[key].status == TERMINAL
                        for key in ledger.terminal_leave
                    ),
                }
            )
    return {
        "rows": rows,
        "all_constructive_utility_one": all(row["utility"] == 1.0 for row in rows),
        "all_roster_schedules_exact": all(
            row["roster_sizes"] == row["expected_roster_sizes"] for row in rows
        ),
        "all_actual_wave_requirements_exact": all(
            row["short_required_total"]
            == row["expected_short_requirement_from_actual_waves"]
            for row in rows
        ),
        "all_membership_events_exact": all(
            row["membership_events_exact"] for row in rows
        ),
        "all_lifecycle_states_exact": all(
            row["lifecycle_states_exact"] for row in rows
        ),
        "all_terminal_lifecycles_destroyed": all(
            row["terminal_lifecycle_destruction_valid"] for row in rows
        ),
    }


def _checkpoint_errors(training: dict[str, Any], run_root: Path) -> list[str]:
    errors: list[str] = []
    rows = training.get("replicate_results")
    counts = training.get("counts")
    expected_count = counts.get("replicates") if isinstance(counts, dict) else None
    if not isinstance(rows, list) or len(rows) != expected_count:
        return ["imported checkpoint inventory mismatch"]
    for expected_replicate, row in enumerate(rows):
        try:
            if not isinstance(row, dict) or row.get("replicate") != expected_replicate:
                raise ValueError("replicate identity mismatch")
            expected_checkpoint = f"checkpoints\\replicate_{expected_replicate}_g5_final.pt"
            if row.get("checkpoint") != expected_checkpoint:
                raise ValueError("imported checkpoint path mismatch")
            checkpoint = run_root / str(row["checkpoint"])
            bundle, state = _strict_load_final_checkpoint(checkpoint)
            if (
                int(bundle["completed_updates"]) != G5_COMPLETED_UPDATES
                or row.get("completed_updates") != G5_COMPLETED_UPDATES
            ):
                raise ValueError("completed_updates mismatch")
            if not state_dict_finite(state) or row.get("finite_model") is not True:
                raise ValueError("model finiteness mismatch")
            if row.get("optimizer_steps") != 0:
                raise ValueError("nonzero optimizer exposure")
            if row.get("g5_manifest_seeds") != _expected_g5_manifest_seeds(expected_replicate):
                raise ValueError("G5 manifest seed mismatch")
            if row.get("checkpoint_embedded_rng_constants") != _embedded_rng_constants(bundle):
                raise ValueError("embedded RNG constant mismatch")
            if row.get("manifest_and_embedded_rng_distinguished") is not True:
                raise ValueError("manifest/embedded RNG distinction missing")
            provenance = training.get("g5_provenance", {})
            source = (
                Path(str(provenance["run_root"]))
                / "checkpoints"
                / f"replicate_{expected_replicate}_final.pt"
            )
            source_bundle, _ = _strict_load_final_checkpoint(source)
            if nested_state_maximum_difference(source_bundle, bundle) != 0.0:
                raise ValueError("materialized checkpoint differs from G5 source")
        except (KeyError, OSError, TypeError, ValueError) as error:
            errors.append(f"replicate {expected_replicate} import invalid: {error}")
    return errors


def _training_errors(training: dict[str, Any], run_root: Path) -> list[str]:
    errors: list[str] = []
    if not (
        training.get("schema_version") == SCHEMA_VERSION
        and training.get("algorithm") == ALGORITHM_ID
        and training.get("stage") == "train"
        and training.get("status") == "COMPLETE"
    ):
        errors.append("training identity/status mismatch")
    if training.get("training_operation") != "none_frozen_g5_checkpoint_import":
        errors.append("training operation is not frozen import")
    if training.get("optimizer_steps") != 0:
        errors.append("training performed optimizer steps")
    formal = training.get("formal") is True
    counts = training.get("counts", {})
    if formal and not (
        training.get("authorization_token") == AUTHORIZATION_TOKEN
        and counts.get("replicates") == FORMAL_REPLICATES
        and counts.get("eval_episodes") == FORMAL_EVAL_EPISODES
        and counts.get("bootstrap_repetitions") == FORMAL_BOOTSTRAP_REPETITIONS
    ):
        errors.append("formal authorization/count contract mismatch")
    if not isinstance(training.get("source_commit"), str) or not _source_commit_valid(
        training["source_commit"], formal=formal
    ):
        errors.append("G6 source identity is invalid or conflated with G5")
    runtime = training.get("runtime", {})
    if not (
        runtime.get("backend") == "cpu"
        and runtime.get("torch") == EXPECTED_TORCH
        and runtime.get("torch_threads") == 1
    ):
        errors.append("runtime is not frozen CPU torch one-thread")
    provenance = training.get("g5_provenance", {})
    expected_provenance = {
        "algorithm": G5_ALGORITHM_ID,
        "source_commit": G5_SOURCE_COMMIT,
        "authorization_token": G5_AUTHORIZATION_TOKEN,
        "train_status": "COMPLETE",
        "train_runtime": {
            "backend": "cpu",
            "torch": EXPECTED_TORCH,
            "torch_threads": 1,
        },
        "train_counts": {
            "replicates": FORMAL_REPLICATES,
            "updates": G5_COMPLETED_UPDATES,
            "num_envs": G5_NUM_ENVS,
        },
        "analysis_status": "COMPLETE",
        "analysis_operational_valid": True,
        "analysis_branch": G5_BRANCH,
    }
    for key, value in expected_provenance.items():
        if provenance.get(key) != value:
            errors.append(f"G5 provenance {key} mismatch")
    try:
        g5_root = Path(str(provenance["run_root"]))
        _validate_g5_provenance(g5_root)
        if formal and g5_root.resolve() != DEFAULT_G5_RUN_ROOT.resolve():
            errors.append("formal G5 run root mismatch")
    except (KeyError, OSError, TypeError, ValueError) as error:
        errors.append(f"live G5 provenance unavailable: {error}")
    errors.extend(_checkpoint_errors(training, run_root))
    return errors


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_errors(training, run_root)
    if errors:
        raise ValueError("G6 evaluation rejected invalid import: " + "; ".join(errors))
    configure_runtime(ACTION_SEED_BASE)
    episode_count = int(training["counts"]["eval_episodes"])
    episode_ids = tuple(range(episode_count))
    cells: list[dict[str, Any]] = []
    for imported in training["replicate_results"]:
        replicate = int(imported["replicate"])
        configure_runtime(ACTION_SEED_BASE + replicate)
        model = DirectPrimitiveARPolicy()
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
        bundle = load_checkpoint(
            run_root / imported["checkpoint"], model=model, optimizer=optimizer
        )
        if int(bundle["completed_updates"]) != G5_COMPLETED_UPDATES:
            raise ValueError("G6 evaluation loaded non-final G5 checkpoint")
        for domain in ("count_scale", "event_time", "joint"):
            factory = LEDGER_FACTORIES[domain]
            profiles = DOMAIN_PROFILES[domain]
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
                    environment_factory=ZeroShotStressEnv,
                )
                after = model_state_copy(model)
                state_difference = maximum_state_difference(before, after)
                cells.append(
                    {
                        "replicate": replicate,
                        "checkpoint": "final",
                        "domain": domain,
                        "deterministic": deterministic,
                        "ledger_seed": DOMAIN_LEDGER_SEEDS[domain],
                        "action_seed": ACTION_SEED_BASE + replicate,
                        "episode_ids": list(episode_ids),
                        "profile_names": [
                            profiles[index % len(profiles)].name
                            for index in episode_ids
                        ],
                        "persistent": values["persistent"].tolist(),
                        "short": values["short"].tolist(),
                        "utility": values["utility"].tolist(),
                        "persistent_mean": values["persistent_mean"],
                        "short_mean": values["short_mean"],
                        "utility_mean": values["utility_mean"],
                        "model_state_maximum_difference": state_difference,
                        "model_state_unchanged_exact": state_difference == 0.0,
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
        "source_controls": _source_controls(),
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _evaluation_errors(
    training: dict[str, Any], evaluation: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if not (
        evaluation.get("schema_version") == SCHEMA_VERSION
        and evaluation.get("algorithm") == ALGORITHM_ID
        and evaluation.get("stage") == "evaluate"
        and evaluation.get("status") == "COMPLETE"
    ):
        errors.append("evaluation identity/status mismatch")
    if evaluation.get("source_commit") != training.get("source_commit"):
        errors.append("train/evaluate source mismatch")
    if evaluation.get("formal") != training.get("formal"):
        errors.append("train/evaluate formal identity mismatch")
    runtime = evaluation.get("runtime", {})
    if not (
        runtime.get("backend") == "cpu"
        and runtime.get("torch") == EXPECTED_TORCH
        and runtime.get("torch_threads") == 1
    ):
        errors.append("evaluation runtime mismatch")
    controls = evaluation.get("source_controls", {})
    for name in (
        "all_constructive_utility_one",
        "all_roster_schedules_exact",
        "all_actual_wave_requirements_exact",
        "all_membership_events_exact",
        "all_lifecycle_states_exact",
        "all_terminal_lifecycles_destroyed",
    ):
        if controls.get(name) is not True:
            errors.append(f"source control {name} failed")
    expected_labels = {
        (domain, profile.name)
        for domain, profiles in DOMAIN_PROFILES.items()
        for profile in profiles
    }
    rows = controls.get("rows")
    if not isinstance(rows, list) or {
        (row.get("domain"), row.get("profile"))
        for row in rows
        if isinstance(row, dict)
    } != expected_labels:
        errors.append("source control profile inventory mismatch")

    replicate_count = int(training.get("counts", {}).get("replicates", -1))
    episode_count = int(training.get("counts", {}).get("eval_episodes", -1))
    cells = evaluation.get("cells")
    expected_cells = {
        (replicate, domain, deterministic)
        for replicate in range(replicate_count)
        for domain in ("count_scale", "event_time", "joint")
        for deterministic in (True, False)
    }
    if not isinstance(cells, list):
        return errors + ["evaluation cells are not a list"]
    inventory = {
        (row.get("replicate"), row.get("domain"), row.get("deterministic"))
        for row in cells
        if isinstance(row, dict)
    }
    if len(cells) != len(expected_cells) or inventory != expected_cells:
        errors.append("evaluation cell inventory mismatch")
    for index, row in enumerate(cells):
        try:
            domain = str(row["domain"])
            profiles = DOMAIN_PROFILES[domain]
            if row.get("checkpoint") != "final":
                raise ValueError("non-final checkpoint cell")
            if row.get("ledger_seed") != DOMAIN_LEDGER_SEEDS[domain]:
                raise ValueError("ledger seed mismatch")
            if row.get("action_seed") != ACTION_SEED_BASE + int(row["replicate"]):
                raise ValueError("action seed mismatch")
            if row.get("episode_ids") != list(range(episode_count)):
                raise ValueError("episode labels mismatch")
            expected_profiles = [
                profiles[episode % len(profiles)].name
                for episode in range(episode_count)
            ]
            if row.get("profile_names") != expected_profiles:
                raise ValueError("profile labels mismatch")
            for metric in ("persistent", "short", "utility"):
                values = row.get(metric)
                if not isinstance(values, list) or len(values) != episode_count:
                    raise ValueError(f"{metric} array length mismatch")
                array = np.asarray(values)
                if (
                    array.dtype.kind not in "fiu"
                    or not np.all(np.isfinite(array))
                    or np.any(array < 0.0)
                    or np.any(array > 1.0)
                ):
                    raise ValueError(f"{metric} array domain mismatch")
                if not math.isclose(
                    float(np.mean(array)),
                    float(row[f"{metric}_mean"]),
                    rel_tol=0.0,
                    abs_tol=1.0e-15,
                ):
                    raise ValueError(f"{metric} mean mismatch")
            if not (
                row.get("model_state_unchanged_exact") is True
                and row.get("model_state_maximum_difference") == 0.0
            ):
                raise ValueError("model state changed during evaluation")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"evaluation cell {index} invalid: {error}")
    return errors


def _bootstrap_replicate_ci(
    values: list[float], *, repetitions: int
) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(
        0, len(array), size=(int(repetitions), len(array)), dtype=np.int64
    )
    means = array[indices].mean(axis=1)
    return [
        float(np.quantile(means, 0.025)),
        float(array.mean()),
        float(np.quantile(means, 0.975)),
    ]


def select_result_branch(metrics: dict[str, Any]) -> str:
    """Apply the frozen first-match absolute-usability G6 gates."""

    if float(metrics["count_scale_deterministic_utility_ci95"][0]) < COUNT_SCALE_FLOOR:
        return "NO_COUNT_SCALE_TRANSPORT_G6"
    if float(metrics["event_time_deterministic_utility_ci95"][0]) < EVENT_TIME_FLOOR:
        return "NO_EVENT_TIME_TRANSPORT_G6"
    if float(metrics["joint_deterministic_utility_ci95"][0]) < JOINT_FLOOR:
        return "NO_JOINT_SCALE_TIME_TRANSPORT_G6"
    if (
        float(metrics["joint_min_replicate_mean"])
        < MINIMUM_JOINT_REPLICATE_FLOOR
        or float(metrics["joint_stochastic_mean"])
        < JOINT_STOCHASTIC_MEAN_FLOOR
    ):
        return "UNSTABLE_ZERO_SHOT_TRANSPORT_G6"
    return "ROBUST_ZERO_SHOT_OPEN_ROSTER_G6"


def analyze(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    errors = _training_errors(training, run_root)
    errors.extend(_evaluation_errors(training, evaluation))
    metrics: dict[str, Any] = {}
    if not errors:
        cells = evaluation["cells"]
        repetitions = int(training["counts"]["bootstrap_repetitions"])
        deterministic_means: dict[str, list[float]] = {}
        for domain in ("count_scale", "event_time", "joint"):
            deterministic_means[domain] = [
                float(row["utility_mean"])
                for row in cells
                if row["domain"] == domain and row["deterministic"] is True
            ]
        joint_stochastic = [
            float(row["utility_mean"])
            for row in cells
            if row["domain"] == "joint" and row["deterministic"] is False
        ]
        joint_means = deterministic_means["joint"]
        metrics = {
            "count_scale_deterministic_utility_ci95": _bootstrap_replicate_ci(
                deterministic_means["count_scale"], repetitions=repetitions
            ),
            "event_time_deterministic_utility_ci95": _bootstrap_replicate_ci(
                deterministic_means["event_time"], repetitions=repetitions
            ),
            "joint_deterministic_utility_ci95": _bootstrap_replicate_ci(
                joint_means, repetitions=repetitions
            ),
            "joint_replicate_means": joint_means,
            "joint_min_replicate_mean": min(joint_means),
            "joint_stochastic_mean": float(np.mean(joint_stochastic)),
        }
    operational_valid = not errors
    formal = training.get("formal") is True
    if not operational_valid:
        branch = "INVALID_OPEN_ROSTER_ZERO_SHOT_G6"
    elif not formal:
        branch = "NONFORMAL_OPEN_ROSTER_G6_EXERCISE_COMPLETE"
    else:
        branch = select_result_branch(metrics)
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE" if operational_valid else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "operational_valid": operational_valid,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "thresholds": {
            "count_scale_deterministic_lcb_floor": COUNT_SCALE_FLOOR,
            "event_time_deterministic_lcb_floor": EVENT_TIME_FLOOR,
            "joint_deterministic_lcb_floor": JOINT_FLOOR,
            "minimum_joint_replicate_mean_floor": MINIMUM_JOINT_REPLICATE_FLOOR,
            "joint_stochastic_mean_floor": JOINT_STOCHASTIC_MEAN_FLOOR,
        },
        "bootstrap_seed": BOOTSTRAP_SEED,
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, g5_run_root: Path = DEFAULT_G5_RUN_ROOT) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit="NONFORMAL_WORKTREE",
        formal=False,
        authorization_token=None,
        g5_run_root=g5_run_root,
        eval_episodes=EXERCISE_EVAL_EPISODES,
        replicate_count=1,
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
    parser.add_argument("--g5-run-root", type=Path, default=None)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "train":
        if args.source_commit is None:
            raise ValueError("train requires --source-commit")
        if args.g5_run_root is None:
            raise ValueError("train requires --g5-run-root")
        value = train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=bool(args.formal),
            authorization_token=args.authorization_token,
            g5_run_root=args.g5_run_root,
            eval_episodes=args.eval_episodes,
        )
    elif args.mode == "evaluate":
        value = evaluate(run_root=args.run_root)
    elif args.mode == "analyze":
        value = analyze(run_root=args.run_root)
    else:
        value = exercise(
            run_root=args.run_root,
            g5_run_root=(
                DEFAULT_G5_RUN_ROOT if args.g5_run_root is None else args.g5_run_root
            ),
        )
    print(
        json.dumps(
            {
                "algorithm": value.get("algorithm"),
                "stage": value.get("stage"),
                "status": value.get("status"),
                "branch": value.get("branch"),
                "formal": value.get("formal"),
                "run_root": str(args.run_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

"""Evaluate and analyze the frozen zero-training G34-P0 process contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_roster_random_process_g34 as source
from scripts import run_runtime_capacity_continuous_roster_g32 as g32_runner
from envs.continuous_roster import runtime_capacity as roster_env


SCHEMA_VERSION = 2
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = "AUTHORIZE_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_FORMAL_CPU_V1"
G32_SOURCE_COMMIT = "fbce3609b11353634d1b4acb20cb27372de40bf2"

INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34"
SOURCE_INVALID_BRANCH = "SOURCE_OR_CONTROL_INVALID_RANDOM_PROCESS_G34"
DEPENDENCE_BRANCH = "FIXED_SCHEDULE_OR_PROCESS_DEPENDENCE_G34"
SUPPORTED_BRANCH = "SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34"
UNDERPOWERED_BRANCH = "UNDERPOWERED_RANDOM_PROCESS_G34"
NONFORMAL_BRANCH = "NONFORMAL_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_EXERCISE_COMPLETE"

CONSTRUCTIVE_RANDOM = "CONSTRUCTIVE_RANDOM"
FINAL_RANDOM_DET = "FINAL_RANDOM_DET"
FINAL_RANDOM_STOCH = "FINAL_RANDOM_STOCH"
ZERO_RANDOM_DET = "ZERO_RANDOM_DET"
FINAL_FIXED_DET = "FINAL_FIXED_DET"
FINAL_FIXED_STOCH = "FINAL_FIXED_STOCH"
FINAL_RANDOM_TIME_ROTATED = "FINAL_RANDOM_TIME_ROTATED"
FINAL_RANDOM_REACTIVE_ABLATION = "FINAL_RANDOM_REACTIVE_ABLATION"

UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
CONSTRUCTIVE_TOLERANCE = 2e-7
FORMAL_REPLICATES = 3
FORMAL_EPISODES = 128
FORMAL_BOOTSTRAP_REPETITIONS = 10_000
EXERCISE_REPLICATES = 1
EXERCISE_EPISODES = 4


def configure_runtime(seed: int = source.BOOTSTRAP_SEED) -> None:
    torch.set_num_threads(1)
    torch.manual_seed(int(seed))


def _runtime_identity() -> dict[str, object]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _configuration(*, formal: bool) -> dict[str, object]:
    replicates = FORMAL_REPLICATES if formal else EXERCISE_REPLICATES
    episodes = FORMAL_EPISODES if formal else EXERCISE_EPISODES
    cells_per_replicate = 20
    return {
        "replicates": replicates,
        "episodes_per_capacity_replicate": episodes,
        "bootstrap_resamples": FORMAL_BOOTSTRAP_REPETITIONS if formal else 0,
        "configured_capacities": list(source.CAPACITIES),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "real_transitions_per_episode": roster_env.HORIZON,
        "total_real_episode_transitions": (
            replicates * cells_per_replicate * episodes * roster_env.HORIZON
        ),
        "checkpoint_selection": "exact_G32_zero_and_final_only",
        "checkpoint_training_change": "forbidden",
        "evaluation_optimizer_steps": 0,
        "episode_exclusions": "none",
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }


def _validate_checkpoint_source(checkpoint_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    training = _read_json(checkpoint_root / "train_manifest.json")
    evaluation = _read_json(checkpoint_root / "evaluation_manifest.json")
    result = _read_json(checkpoint_root / "analysis_result.json")
    errors = g32_runner._artifact_errors(checkpoint_root, training, evaluation)
    if errors:
        raise ValueError("G34 checkpoint source invalid: " + " | ".join(errors))
    if (
        training.get("formal") is not True
        or training.get("source_commit") != G32_SOURCE_COMMIT
        or result.get("operational_valid") is not True
        or result.get("branch") != g32_runner.USABLE_BRANCH
    ):
        raise ValueError("G34 requires exact usable formal G32 checkpoint source")
    return training, g32_runner._configuration(formal=True)


def _load_model(
    checkpoint_root: Path,
    training: Mapping[str, Any],
    configuration: dict[str, Any],
    *,
    replicate: int,
    kind: str,
    capacity: int,
) -> torch.nn.Module:
    row = training["replicate_results"][replicate]
    model, _ = g32_runner._load_checkpoint(
        checkpoint_root / row[f"{kind}_checkpoint"],
        source_commit=G32_SOURCE_COMMIT,
        formal=True,
        replicate=replicate,
        kind=kind,
        configuration=configuration,
        member_capacity=capacity,
    )
    return model


def _state_digest(model: torch.nn.Module) -> str:
    return g32_runner._state_digest(g32_runner._copy_state(model))


def _source_inventory(
    replicate: int, capacity: int, episode_count: int
) -> tuple[tuple[source.RandomProcessLedger, ...], dict[str, object]]:
    processes = source.make_process_ledgers(
        replicate=replicate, capacity=capacity, episode_count=episode_count
    )
    inventory = {
        "replicate": replicate,
        "capacity": capacity,
        "processes": [
            {
                "local_episode_id": row.local_episode_id,
                "episode_id": row.episode_id,
                "profile": row.profile.name,
                "event_times": list(row.event_times),
                "event_order": list(row.event_order),
                "count_trajectory": list(row.count_trajectory),
                "random_expected_roster_sizes": list(row.expected_roster_sizes),
                "fixed_expected_roster_sizes": list(row.base.expected_roster_sizes),
                "temporarily_absent": list(row.base.temporarily_absent),
                "fresh_join": list(row.base.fresh_join),
                "terminal_leave": list(row.base.terminal_leave),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }
    return processes, inventory


def _constructive_cell(
    replicate: int,
    capacity: int,
    processes: Sequence[source.RandomProcessLedger],
) -> dict[str, object]:
    return {
        "replicate": replicate,
        "capacity": capacity,
        "cell": CONSTRUCTIVE_RANDOM,
        "checkpoint": "constructive",
        "process": "random",
        "deterministic": True,
        "intervention": "none",
        "optimizer_steps": 0,
        "state_before": None,
        "state_after": None,
        "lifecycle_valid": True,
        "episodes": list(source.evaluate_constructive(processes)),
    }


def _model_cell(
    replicate: int,
    capacity: int,
    cell: str,
    model: torch.nn.Module,
    processes: Sequence[source.RandomProcessLedger],
    *,
    checkpoint: str,
    process_kind: str,
    deterministic: bool,
    intervention: str = "none",
) -> dict[str, object]:
    before = _state_digest(model)
    episodes, lifecycle_valid = source.evaluate_model(
        model,
        processes=processes,
        action_seed=source.ACTION_SEED_BASE + replicate,
        process_kind=process_kind,
        deterministic=deterministic,
        intervention=intervention,
    )
    return {
        "replicate": replicate,
        "capacity": capacity,
        "cell": cell,
        "checkpoint": checkpoint,
        "process": process_kind,
        "deterministic": deterministic,
        "intervention": intervention,
        "optimizer_steps": 0,
        "state_before": before,
        "state_after": _state_digest(model),
        "lifecycle_valid": lifecycle_valid,
        "episodes": list(episodes),
    }


def evaluate(
    *,
    run_root: Path,
    checkpoint_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G34 source commit must be a full lowercase Git identity")
    if formal and authorization_token != AUTHORIZATION_TOKEN:
        raise ValueError("G34 formal authorization token mismatch")
    if not formal and authorization_token is not None:
        raise ValueError("G34 nonformal evaluation cannot carry formal authority")
    configure_runtime()
    training, g32_configuration = _validate_checkpoint_source(checkpoint_root)
    configuration = _configuration(formal=formal)
    replicate_count = int(configuration["replicates"])
    episode_count = int(configuration["episodes_per_capacity_replicate"])
    cells: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    for replicate in range(replicate_count):
        for capacity in source.CAPACITIES:
            processes, inventory = _source_inventory(replicate, capacity, episode_count)
            inventories.append(inventory)
            cells.append(_constructive_cell(replicate, capacity, processes))
            final_model = _load_model(
                checkpoint_root,
                training,
                g32_configuration,
                replicate=replicate,
                kind="final",
                capacity=capacity,
            )
            zero_model = _load_model(
                checkpoint_root,
                training,
                g32_configuration,
                replicate=replicate,
                kind="zero",
                capacity=capacity,
            )
            cells.extend(
                (
                    _model_cell(replicate, capacity, FINAL_RANDOM_DET, final_model, processes, checkpoint="final", process_kind="random", deterministic=True),
                    _model_cell(replicate, capacity, FINAL_RANDOM_STOCH, final_model, processes, checkpoint="final", process_kind="random", deterministic=False),
                    _model_cell(replicate, capacity, ZERO_RANDOM_DET, zero_model, processes, checkpoint="zero", process_kind="random", deterministic=True),
                    _model_cell(replicate, capacity, FINAL_FIXED_DET, final_model, processes, checkpoint="final", process_kind="fixed", deterministic=True),
                    _model_cell(replicate, capacity, FINAL_FIXED_STOCH, final_model, processes, checkpoint="final", process_kind="fixed", deterministic=False),
                )
            )
            if capacity == 8:
                cells.extend(
                    (
                        _model_cell(replicate, capacity, FINAL_RANDOM_TIME_ROTATED, final_model, processes, checkpoint="final", process_kind="random", deterministic=True, intervention="time_rotated"),
                        _model_cell(replicate, capacity, FINAL_RANDOM_REACTIVE_ABLATION, final_model, processes, checkpoint="final", process_kind="random", deterministic=True, intervention="reactive"),
                    )
                )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "authorization_token": authorization_token,
        "source_commit": source_commit,
        "checkpoint_root": str(checkpoint_root.resolve()),
        "checkpoint_source_commit": G32_SOURCE_COMMIT,
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "source_controls": source.source_controls(),
        "source_inventory": inventories,
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _expected_cell_contracts(capacity: int) -> dict[str, dict[str, object]]:
    contracts = {
        CONSTRUCTIVE_RANDOM: {
            "checkpoint": "constructive",
            "process": "random",
            "deterministic": True,
            "intervention": "none",
        },
        FINAL_RANDOM_DET: {
            "checkpoint": "final",
            "process": "random",
            "deterministic": True,
            "intervention": "none",
        },
        FINAL_RANDOM_STOCH: {
            "checkpoint": "final",
            "process": "random",
            "deterministic": False,
            "intervention": "none",
        },
        ZERO_RANDOM_DET: {
            "checkpoint": "zero",
            "process": "random",
            "deterministic": True,
            "intervention": "none",
        },
        FINAL_FIXED_DET: {
            "checkpoint": "final",
            "process": "fixed",
            "deterministic": True,
            "intervention": "none",
        },
        FINAL_FIXED_STOCH: {
            "checkpoint": "final",
            "process": "fixed",
            "deterministic": False,
            "intervention": "none",
        },
    }
    if capacity == 8:
        contracts.update(
            {
                FINAL_RANDOM_TIME_ROTATED: {
                    "checkpoint": "final",
                    "process": "random",
                    "deterministic": True,
                    "intervention": "time_rotated",
                },
                FINAL_RANDOM_REACTIVE_ABLATION: {
                    "checkpoint": "final",
                    "process": "random",
                    "deterministic": True,
                    "intervention": "reactive",
                },
            }
        )
    return contracts


def _expected_cell_names(capacity: int) -> set[str]:
    return set(_expected_cell_contracts(capacity))


def _trace_evidence(episode: Mapping[str, Any]) -> dict[str, object]:
    rewards = np.asarray(episode["reward_trace"], dtype=np.float64)
    if (
        rewards.shape != (roster_env.HORIZON,)
        or not np.isfinite(rewards).all()
        or np.any((rewards < 0.0) | (rewards > 1.0))
    ):
        raise ValueError("G34 reward trace mismatch")
    event_times = tuple(int(value) for value in episode["event_times"])
    event_order = tuple(str(value) for value in episode["event_order"])
    if len(event_times) != 4 or len(event_order) != 4:
        raise ValueError("G34 event trace identity mismatch")
    windows = {
        edit: float(rewards[time : time + 4].mean())
        for time, edit in zip(event_times, event_order)
    }
    boundaries = (0, *event_times, roster_env.HORIZON)
    segments = tuple(
        float(rewards[left:right].mean())
        for left, right in zip(boundaries, boundaries[1:])
    )
    roster_values = episode["roster_size_trace"]
    if (
        not isinstance(roster_values, list)
        or len(roster_values) != roster_env.HORIZON
        or any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in roster_values
        )
    ):
        raise ValueError("G34 roster trace mismatch")
    return {
        "utility": float(rewards.mean()),
        "minimum_step_utility": float(rewards.min()),
        "minimum_event_window_utility": min(windows.values()),
        "minimum_process_segment_utility": min(segments),
        "event_window_utility": windows,
        "process_segment_utility": segments,
        "roster_size_trace": tuple(int(value) for value in roster_values),
    }


def _summary_matches_trace(
    episode: Mapping[str, Any], trace: Mapping[str, Any]
) -> bool:
    scalar_fields = (
        "utility",
        "minimum_step_utility",
        "minimum_event_window_utility",
        "minimum_process_segment_utility",
    )
    if any(
        not np.isclose(
            float(episode[field]), float(trace[field]), rtol=0.0, atol=1e-12
        )
        for field in scalar_fields
    ):
        return False
    serialized_windows = episode.get("event_window_utility")
    trace_windows = trace["event_window_utility"]
    if (
        not isinstance(serialized_windows, dict)
        or set(serialized_windows) != set(trace_windows)
        or any(
            not np.isclose(
                float(serialized_windows[key]),
                float(trace_windows[key]),
                rtol=0.0,
                atol=1e-12,
            )
            for key in trace_windows
        )
    ):
        return False
    serialized_segments = np.asarray(
        episode.get("process_segment_utility", []), dtype=np.float64
    )
    return bool(
        serialized_segments.shape == (5,)
        and np.isfinite(serialized_segments).all()
        and np.allclose(
            serialized_segments,
            np.asarray(trace["process_segment_utility"], dtype=np.float64),
            rtol=0.0,
            atol=1e-12,
        )
    )


def _artifact_errors(
    evaluation: Mapping[str, Any], checkpoint_root: Path
) -> list[str]:
    errors: list[str] = []
    formal = bool(evaluation.get("formal"))
    configuration = _configuration(formal=formal)
    checkpoint_training: dict[str, Any] | None = None
    checkpoint_configuration: dict[str, Any] | None = None
    try:
        checkpoint_training, checkpoint_configuration = _validate_checkpoint_source(
            checkpoint_root
        )
    except (KeyError, TypeError, ValueError, OSError) as error:
        errors.append(str(error))
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source.source_controls()
        or evaluation.get("checkpoint_source_commit") != G32_SOURCE_COMMIT
        or evaluation.get("checkpoint_root") != str(checkpoint_root.resolve())
    ):
        errors.append("G34 evaluation identity mismatch")
    runtime = evaluation.get("runtime", {})
    if (
        runtime.get("backend") != "cpu"
        or runtime.get("torch_threads") != 1
        or runtime.get("torch") != str(torch.__version__)
    ):
        errors.append("G34 runtime mismatch")
    if re.fullmatch(r"[0-9a-f]{40}", str(evaluation.get("source_commit"))) is None:
        errors.append("G34 source commit invalid")
    if formal and evaluation.get("authorization_token") != AUTHORIZATION_TOKEN:
        errors.append("G34 formal authorization mismatch")
    if not formal and evaluation.get("authorization_token") is not None:
        errors.append("G34 nonformal authority mismatch")
    replicate_count = int(configuration["replicates"])
    episode_count = int(configuration["episodes_per_capacity_replicate"])
    expected_checkpoint_digests: dict[tuple[int, int, str], str] = {}
    if checkpoint_training is not None and checkpoint_configuration is not None:
        for replicate in range(replicate_count):
            for capacity in source.CAPACITIES:
                for checkpoint_kind in ("zero", "final"):
                    try:
                        expected_model = _load_model(
                            checkpoint_root,
                            checkpoint_training,
                            checkpoint_configuration,
                            replicate=replicate,
                            kind=checkpoint_kind,
                            capacity=capacity,
                        )
                        expected_checkpoint_digests[
                            (replicate, capacity, checkpoint_kind)
                        ] = _state_digest(expected_model)
                    except (KeyError, TypeError, ValueError, OSError) as error:
                        errors.append(str(error))
    expected_inventory: list[dict[str, object]] = []
    for replicate in range(replicate_count):
        for capacity in source.CAPACITIES:
            _, inventory = _source_inventory(replicate, capacity, episode_count)
            expected_inventory.append(inventory)
    if evaluation.get("source_inventory") != expected_inventory:
        errors.append("G34 source inventory mismatch")
    cells = evaluation.get("cells", [])
    if not isinstance(cells, list) or len(cells) != replicate_count * 20:
        errors.append("G34 evaluation cell inventory mismatch")
        return errors
    observed: set[tuple[int, int, str]] = set()
    inventories = {
        (row["replicate"], row["capacity"]): row["processes"]
        for row in expected_inventory
    }
    for cell in cells:
        try:
            replicate = int(cell["replicate"])
            capacity = int(cell["capacity"])
            name = str(cell["cell"])
            key = (replicate, capacity, name)
            if (
                replicate not in range(replicate_count)
                or capacity not in source.CAPACITIES
                or name not in _expected_cell_names(capacity)
                or key in observed
            ):
                raise ValueError("G34 cell identity mismatch")
            observed.add(key)
            contract = _expected_cell_contracts(capacity)[name]
            if (
                cell.get("checkpoint") != contract["checkpoint"]
                or cell.get("process") != contract["process"]
                or cell.get("deterministic") is not contract["deterministic"]
                or cell.get("intervention") != contract["intervention"]
            ):
                raise ValueError("G34 cell route mismatch")
            if cell.get("optimizer_steps") != 0 or cell.get("lifecycle_valid") is not True:
                raise ValueError("G34 lifecycle or zero-step mismatch")
            if name == CONSTRUCTIVE_RANDOM:
                if cell.get("state_before") is not None or cell.get("state_after") is not None:
                    raise ValueError("G34 constructive state identity mismatch")
            else:
                expected_digest = expected_checkpoint_digests.get(
                    (replicate, capacity, str(contract["checkpoint"]))
                )
                if (
                    expected_digest is None
                    or cell.get("state_before") != expected_digest
                    or cell.get("state_after") != expected_digest
                ):
                    raise ValueError("G34 checkpoint binding mismatch")
            episodes = cell["episodes"]
            if not isinstance(episodes, list) or len(episodes) != episode_count:
                raise ValueError("G34 episode inventory mismatch")
            expected_processes = inventories[(replicate, capacity)]
            for index, episode in enumerate(episodes):
                expected_process = expected_processes[index]
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != expected_process["episode_id"]
                    or episode.get("profile") != expected_process["profile"]
                    or episode.get("event_times") != expected_process["event_times"]
                    or episode.get("event_order") != expected_process["event_order"]
                    or episode.get("count_trajectory")
                    != expected_process["count_trajectory"]
                    or episode.get("signature") != expected_process["signature"]
                ):
                    raise ValueError("G34 episode support or pairing mismatch")
                trace = _trace_evidence(episode)
                roster_field = (
                    "random_expected_roster_sizes"
                    if contract["process"] == "random"
                    else "fixed_expected_roster_sizes"
                )
                if (
                    trace["roster_size_trace"]
                    != tuple(expected_process[roster_field])
                    or episode.get("roster_sizes_valid") is not True
                ):
                    raise ValueError("G34 roster trace evidence mismatch")
                if not _summary_matches_trace(episode, trace):
                    raise ValueError("G34 serialized summary mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    expected_keys = {
        (replicate, capacity, name)
        for replicate in range(replicate_count)
        for capacity in source.CAPACITIES
        for name in _expected_cell_names(capacity)
    }
    if observed != expected_keys:
        errors.append("G34 cell key set mismatch")
    return errors


def _cell_map(evaluation: Mapping[str, Any]) -> dict[tuple[int, int, str], Mapping[str, Any]]:
    return {
        (int(row["replicate"]), int(row["capacity"]), str(row["cell"])): row
        for row in evaluation["cells"]
    }


def _metric_arrays(
    evaluation: Mapping[str, Any],
    cell_name: str,
    metric: str,
    *,
    capacities: Sequence[int] = source.CAPACITIES,
) -> dict[int, np.ndarray]:
    configuration = evaluation["configuration"]
    replicates = int(configuration["replicates"])
    cells = _cell_map(evaluation)
    result: dict[int, np.ndarray] = {}
    for capacity in capacities:
        result[capacity] = np.asarray(
            [
                [
                    _trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, cell_name)]["episodes"]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
    return result


def _event_metric_arrays(
    evaluation: Mapping[str, Any],
    cell_name: str,
    event_type: str,
    *,
    capacities: Sequence[int] = source.CAPACITIES,
) -> dict[int, np.ndarray]:
    if event_type not in {"L", "R", "J", "T"}:
        raise ValueError("G34 unknown event type")
    configuration = evaluation["configuration"]
    replicates = int(configuration["replicates"])
    cells = _cell_map(evaluation)
    return {
        capacity: np.asarray(
            [
                [
                    _trace_evidence(episode)["event_window_utility"][event_type]
                    for episode in cells[(replicate, capacity, cell_name)]["episodes"]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in capacities
    }


def _bootstrap_plan(
    *, replicates: int, episodes: int, repetitions: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(source.BOOTSTRAP_SEED)
    replicate_draws = rng.integers(
        0, replicates, size=(repetitions, replicates), dtype=np.int16
    )
    episode_draws = rng.integers(
        0,
        episodes,
        size=(repetitions, replicates, len(source.CAPACITIES), episodes),
        dtype=np.int16,
    )
    return replicate_draws, episode_draws


def _hierarchical_ci(
    values: Mapping[int, np.ndarray],
    *,
    selected_capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    replicate_draws, episode_draws = plan
    totals = np.zeros(len(replicate_draws), dtype=np.float64)
    count = 0
    for capacity in selected_capacities:
        array = np.asarray(values[capacity], dtype=np.float64)
        capacity_index = source.CAPACITIES.index(capacity)
        for slot in range(replicate_draws.shape[1]):
            replicate = replicate_draws[:, slot]
            episodes = episode_draws[:, slot, capacity_index]
            totals += array[replicate[:, None], episodes].sum(axis=1)
            count += array.shape[1]
    distribution = totals / count
    return [float(value) for value in np.percentile(distribution, (2.5, 50.0, 97.5))]


def _difference(
    left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]
) -> dict[int, np.ndarray]:
    capacities = set(left) & set(right)
    return {capacity: left[capacity] - right[capacity] for capacity in capacities}


def _annotation(
    control: Mapping[int, np.ndarray],
    primary: Mapping[int, np.ndarray],
    plan: tuple[np.ndarray, np.ndarray],
) -> dict[str, object]:
    utility_ci = _hierarchical_ci(control, selected_capacities=(8,), plan=plan)
    difference_ci = _hierarchical_ci(
        _difference(control, primary), selected_capacities=(8,), plan=plan
    )
    if utility_ci[0] >= UTILITY_FLOOR and difference_ci[0] >= PROCESS_MARGIN:
        classification = "SUFFICIENT"
    elif utility_ci[2] < UTILITY_FLOOR or difference_ci[2] < PROCESS_MARGIN:
        classification = "LOAD_BEARING"
    else:
        classification = "UNDERPOWERED"
    return {
        "utility_ci95": utility_ci,
        "control_minus_primary_ci95": difference_ci,
        "classification": classification,
    }


def select_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_structural_valid"]) or bool(metrics["fixed_control_confident_fail"]):
        return SOURCE_INVALID_BRANCH
    if bool(metrics["fixed_control_pass"]) and bool(metrics["random_confident_fail"]):
        return DEPENDENCE_BRANCH
    if bool(metrics["fixed_control_pass"]) and bool(metrics["random_pass"]):
        return SUPPORTED_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(
    *, run_root: Path, checkpoint_root: Path, require_formal: bool = False
) -> dict[str, Any]:
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(evaluation.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G34 analysis requires formal evaluation artifacts")
    configure_runtime()
    errors = _artifact_errors(evaluation, checkpoint_root)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        cells = _cell_map(evaluation)
        constructive_valid = all(
            min(
                float(_trace_evidence(episode)[field])
                for episode in cell["episodes"]
                for field in (
                    "utility",
                    "minimum_step_utility",
                    "minimum_event_window_utility",
                    "minimum_process_segment_utility",
                )
            )
            >= 1.0 - CONSTRUCTIVE_TOLERANCE
            for (replicate, capacity, name), cell in cells.items()
            if name == CONSTRUCTIVE_RANDOM
        )
        source_structural_valid = constructive_valid and all(
            cell["lifecycle_valid"] is True for cell in cells.values()
        )
        metrics.update(
            {
                "constructive_source_valid": constructive_valid,
                "source_structural_valid": source_structural_valid,
            }
        )
        if formal:
            configuration = evaluation["configuration"]
            plan = _bootstrap_plan(
                replicates=int(configuration["replicates"]),
                episodes=int(configuration["episodes_per_capacity_replicate"]),
                repetitions=int(configuration["bootstrap_resamples"]),
            )
            random_u = _metric_arrays(evaluation, FINAL_RANDOM_DET, "utility")
            random_e = _metric_arrays(evaluation, FINAL_RANDOM_DET, "minimum_event_window_utility")
            random_p = _metric_arrays(evaluation, FINAL_RANDOM_DET, "minimum_process_segment_utility")
            random_stoch = _metric_arrays(evaluation, FINAL_RANDOM_STOCH, "utility")
            zero_u = _metric_arrays(evaluation, ZERO_RANDOM_DET, "utility")
            fixed_u = _metric_arrays(evaluation, FINAL_FIXED_DET, "utility")
            fixed_stoch = _metric_arrays(evaluation, FINAL_FIXED_STOCH, "utility")
            process_delta = _difference(random_u, fixed_u)
            learned_delta = _difference(random_u, zero_u)
            random_ci = {
                capacity: _hierarchical_ci(random_u, selected_capacities=(capacity,), plan=plan)
                for capacity in source.CAPACITIES
            }
            event_ci = {
                capacity: _hierarchical_ci(random_e, selected_capacities=(capacity,), plan=plan)
                for capacity in source.CAPACITIES
            }
            segment_ci = {
                capacity: _hierarchical_ci(random_p, selected_capacities=(capacity,), plan=plan)
                for capacity in source.CAPACITIES
            }
            process_ci = {
                capacity: _hierarchical_ci(process_delta, selected_capacities=(capacity,), plan=plan)
                for capacity in source.CAPACITIES
            }
            event_type_arrays = {
                event_type: _event_metric_arrays(
                    evaluation, FINAL_RANDOM_DET, event_type
                )
                for event_type in ("L", "R", "J", "T")
            }
            event_type_ci = {
                capacity: {
                    event_type: _hierarchical_ci(
                        event_type_arrays[event_type],
                        selected_capacities=(capacity,),
                        plan=plan,
                    )
                    for event_type in ("L", "R", "J", "T")
                }
                for capacity in source.CAPACITIES
            }
            fixed_ci = {
                capacity: _hierarchical_ci(fixed_u, selected_capacities=(capacity,), plan=plan)
                for capacity in source.CAPACITIES
            }
            learned_ci = _hierarchical_ci(
                learned_delta, selected_capacities=source.CAPACITIES, plan=plan
            )
            random_stoch_ci = _hierarchical_ci(
                random_stoch, selected_capacities=source.CAPACITIES, plan=plan
            )
            fixed_stoch_ci = _hierarchical_ci(
                fixed_stoch, selected_capacities=source.CAPACITIES, plan=plan
            )
            minimum_random_replicate = min(
                float(np.concatenate([random_u[capacity][replicate] for capacity in source.CAPACITIES]).mean())
                for replicate in range(FORMAL_REPLICATES)
            )
            minimum_fixed_replicate = min(
                float(np.concatenate([fixed_u[capacity][replicate] for capacity in source.CAPACITIES]).mean())
                for replicate in range(FORMAL_REPLICATES)
            )
            fixed_pass = (
                all(fixed_ci[capacity][0] >= UTILITY_FLOOR for capacity in source.CAPACITIES)
                and fixed_stoch_ci[0] >= STOCHASTIC_FLOOR
                and minimum_fixed_replicate >= MINIMUM_REPLICATE_FLOOR
            )
            fixed_confident_fail = (
                any(fixed_ci[capacity][2] < UTILITY_FLOOR for capacity in source.CAPACITIES)
                or fixed_stoch_ci[2] < STOCHASTIC_FLOOR
                or minimum_fixed_replicate < MINIMUM_REPLICATE_FLOOR
            )
            random_pass = (
                all(random_ci[capacity][0] >= UTILITY_FLOOR for capacity in source.CAPACITIES)
                and all(event_ci[capacity][0] >= EVENT_FLOOR for capacity in source.CAPACITIES)
                and all(segment_ci[capacity][0] >= SEGMENT_FLOOR for capacity in source.CAPACITIES)
                and all(process_ci[capacity][0] >= PROCESS_MARGIN for capacity in source.CAPACITIES)
                and learned_ci[0] > 0.0
                and random_stoch_ci[0] >= STOCHASTIC_FLOOR
                and minimum_random_replicate >= MINIMUM_REPLICATE_FLOOR
            )
            random_confident_fail = (
                any(random_ci[capacity][2] < UTILITY_FLOOR for capacity in source.CAPACITIES)
                or any(event_ci[capacity][2] < EVENT_FLOOR for capacity in source.CAPACITIES)
                or any(segment_ci[capacity][2] < SEGMENT_FLOOR for capacity in source.CAPACITIES)
                or any(process_ci[capacity][2] < PROCESS_MARGIN for capacity in source.CAPACITIES)
                or learned_ci[2] <= 0.0
                or random_stoch_ci[2] < STOCHASTIC_FLOOR
                or minimum_random_replicate < MINIMUM_REPLICATE_FLOOR
            )
            time_control = _metric_arrays(
                evaluation,
                FINAL_RANDOM_TIME_ROTATED,
                "utility",
                capacities=(8,),
            )
            reactive_control = _metric_arrays(
                evaluation,
                FINAL_RANDOM_REACTIVE_ABLATION,
                "utility",
                capacities=(8,),
            )
            metrics.update(
                {
                    "random_utility_ci95": random_ci,
                    "random_event_window_ci95": event_ci,
                    "random_event_type_window_ci95": event_type_ci,
                    "random_process_segment_ci95": segment_ci,
                    "random_minus_fixed_ci95": process_ci,
                    "fixed_utility_ci95": fixed_ci,
                    "learned_gain_ci95": learned_ci,
                    "random_stochastic_pooled_ci95": random_stoch_ci,
                    "fixed_stochastic_pooled_ci95": fixed_stoch_ci,
                    "minimum_random_deterministic_replicate_mean": minimum_random_replicate,
                    "minimum_fixed_reference_replicate_mean": minimum_fixed_replicate,
                    "fixed_control_pass": fixed_pass,
                    "fixed_control_confident_fail": fixed_confident_fail,
                    "random_pass": random_pass,
                    "random_confident_fail": random_confident_fail,
                    "time_rotated_annotation": _annotation(time_control, random_u, plan),
                    "reactive_ablation_annotation": _annotation(reactive_control, random_u, plan),
                }
            )
    if formal and not errors:
        branch = select_result_branch(metrics)
    else:
        branch = INVALID_BRANCH if errors else NONFORMAL_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": evaluation.get("source_commit"),
        "checkpoint_source_commit": G32_SOURCE_COMMIT,
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "thresholds": {
            "utility_floor": UTILITY_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "process_noninferiority_margin": PROCESS_MARGIN,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "constructive_tolerance": CONSTRUCTIVE_TOLERANCE,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(
    *, run_root: Path, checkpoint_root: Path, source_commit: str
) -> dict[str, Any]:
    evaluate(
        run_root=run_root,
        checkpoint_root=checkpoint_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
    )
    return analyze(run_root=run_root, checkpoint_root=checkpoint_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--require-formal", action="store_true")
    args = parser.parse_args()
    if args.mode == "evaluate":
        value = evaluate(
            run_root=args.run_root,
            checkpoint_root=args.checkpoint_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
        )
    elif args.mode == "analyze":
        value = analyze(
            run_root=args.run_root,
            checkpoint_root=args.checkpoint_root,
            require_formal=args.require_formal,
        )
    else:
        value = exercise(
            run_root=args.run_root,
            checkpoint_root=args.checkpoint_root,
            source_commit=args.source_commit or "0" * 40,
        )
    print(
        json.dumps(
            {
                "algorithm": ALGORITHM_ID,
                "stage": value["stage"],
                "status": value["status"],
                "branch": value.get("branch"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

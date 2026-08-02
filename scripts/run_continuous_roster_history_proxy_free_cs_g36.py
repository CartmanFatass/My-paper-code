"""Evaluate and analyze the frozen zero-training G36 history-proxy contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process import continuous_roster_history_proxy_free_cs_g36 as source
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from envs.continuous_roster import runtime_capacity as roster_env
from scripts import run_continuous_roster_random_process_g34 as g34_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
G35_SOURCE_ID = "CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_P0"
G35_BRANCH = "CURRENT_STATE_REDUCTION_SUFFICIENT_G35"
G35_CHECKPOINT_SOURCE_COMMIT = "f626dfd8a345ef670e08e601344b67e28ffb3563"
AUTHORIZATION_TOKEN = "CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_FORMAL_AUTHORIZATION_V1"
INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36"
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REGISTERED_ACCESS_FAILURE_G36"
SUFFICIENT_BRANCH = "HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36"
LOAD_BEARING_BRANCH = "HISTORY_PROXY_BUNDLE_LOAD_BEARING_G36"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_HISTORY_PROXY_G36"
NONFORMAL_BRANCH = "NONFORMAL_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_COMPLETE"
NON_EXECUTABLE_BRANCH = "NON_EXECUTABLE_EVIDENCE_DESIGN"

FORMAL_REPLICATES = 3
FORMAL_EPISODES = 128
EXERCISE_REPLICATES = 1
EXERCISE_EPISODES = 8
FORMAL_BOOTSTRAP_RESAMPLES = 10_000
EXERCISE_BOOTSTRAP_RESAMPLES = 250
HORIZON = 48
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
BOOTSTRAP_SEED = 10_362_036
UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
PROXY_MARGIN = 0.05
CELLS = (
    ("CS_HISTORY_FREE_FIXED_DET", "fixed", True),
    ("CS_HISTORY_FREE_FIXED_STOCH", "fixed", False),
    ("CS_HISTORY_FREE_RANDOM_DET", "random", True),
    ("CS_HISTORY_FREE_RANDOM_STOCH", "random", False),
)


def configure_runtime(seed: int) -> None:
    torch.set_num_threads(1)
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("G36 JSON artifact must be an object")
    return value


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_equivalent(left: object, right: object) -> bool:
    def canonical(value: object) -> str:
        return json.dumps(
            json.loads(json.dumps(value)),
            sort_keys=True,
            separators=(",", ":"),
        )

    return canonical(left) == canonical(right)


def _runtime_identity() -> dict[str, object]:
    return {"backend": "cpu", "torch_threads": int(torch.get_num_threads()), "torch": str(torch.__version__)}


def _configuration(*, formal: bool) -> dict[str, object]:
    replicates = FORMAL_REPLICATES if formal else EXERCISE_REPLICATES
    episodes = FORMAL_EPISODES if formal else EXERCISE_EPISODES
    bootstrap = FORMAL_BOOTSTRAP_RESAMPLES if formal else EXERCISE_BOOTSTRAP_RESAMPLES
    return {
        "formal": formal, "replicates": replicates, "capacities": list(g34.CAPACITIES),
        "intervention_cells_per_capacity": 4, "total_new_cells": replicates * len(g34.CAPACITIES) * 4,
        "evaluation_episodes_per_cell": episodes, "evaluation_episodes": replicates * len(g34.CAPACITIES) * 4 * episodes,
        "horizon": HORIZON, "evaluation_transitions": replicates * len(g34.CAPACITIES) * 4 * episodes * HORIZON,
        "optimizer_steps": 0, "bootstrap_resamples": bootstrap, "K_search": 0,
        "hypothetical_trajectory_count": 0, "hypothetical_transitions": 0,
        "nested_rollout": False, "replanning": False,
    }


def _bootstrap_plan(*, formal: bool, replicates: int, episodes: int, repetitions: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(BOOTSTRAP_SEED + (0 if formal else source.NONFORMAL_SEED_OFFSET))
    return (
        rng.integers(0, replicates, size=(repetitions, replicates), dtype=np.int16),
        rng.integers(0, episodes, size=(repetitions, replicates, len(g34.CAPACITIES), episodes), dtype=np.int16),
    )


def _hierarchical_ci(values: Mapping[int, np.ndarray], *, capacities: Sequence[int], plan: tuple[np.ndarray, np.ndarray]) -> list[float]:
    replicate_draws, episode_draws = plan
    totals = np.zeros(len(replicate_draws), dtype=np.float64)
    count = 0
    for capacity in capacities:
        array = np.asarray(values[capacity], dtype=np.float64)
        capacity_index = g34.CAPACITIES.index(capacity)
        for slot in range(replicate_draws.shape[1]):
            selected_replicates = replicate_draws[:, slot]
            selected_episodes = episode_draws[:, slot, capacity_index]
            totals += array[selected_replicates[:, None], selected_episodes].sum(axis=1)
            count += array.shape[1]
    return [float(value) for value in np.percentile(totals / count, (2.5, 50.0, 97.5))]


def _minimum_replicate_mean(values: Mapping[int, np.ndarray]) -> float:
    replicates = next(iter(values.values())).shape[0]
    return min(float(np.concatenate([values[capacity][replicate] for capacity in g34.CAPACITIES]).mean()) for replicate in range(replicates))


def select_g36_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["registered_source_access_valid"]):
        return SOURCE_FAILURE_BRANCH
    if bool(metrics["intervention_access_pass"]) and bool(metrics["proxy_noninferior"]):
        return SUFFICIENT_BRANCH
    if bool(metrics["intervention_access_confident_fail"]) or bool(metrics["material_proxy_loss"]):
        return LOAD_BEARING_BRANCH
    return UNDERPOWERED_BRANCH


def _nonnegative_finite_seconds(value: object) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not np.isfinite(value)
        or value < 0.0
    ):
        raise ValueError("G36 stage timing invalid")
    return float(value)


def _validate_formal_preflight(
    preflight_root: Path | None, *, source_commit: str, g35_root: Path
) -> None:
    if preflight_root is None:
        raise ValueError("G36 formal evaluation requires a matching preflight")
    root = Path(preflight_root)
    evaluation_path = root / "evaluation_manifest.json"
    analysis_path = root / "analysis_result.json"
    evaluation = _read_json(evaluation_path)
    result = _read_json(analysis_path)
    validation_errors = _evaluation_errors(root, evaluation, g35_root=g35_root)
    if validation_errors:
        raise ValueError(
            "G36 formal preflight artifacts are invalid: "
            + " | ".join(validation_errors)
        )
    evaluation_seconds = _nonnegative_finite_seconds(
        evaluation.get("stage_wall_time_seconds")
    )
    analysis_seconds = _nonnegative_finite_seconds(
        result.get("stage_wall_time_seconds")
    )
    projection = 1.25 * (48.0 * evaluation_seconds + 40.0 * analysis_seconds)
    stored_projection = result.get("formal_projection_seconds")
    projection_matches = (
        isinstance(stored_projection, (int, float))
        and not isinstance(stored_projection, bool)
        and np.isfinite(stored_projection)
        and bool(np.isclose(stored_projection, projection, rtol=0.0, atol=1e-9))
    )
    _, g35_evaluation, g35_analysis = _g35_reference(g35_root)
    configuration = evaluation["configuration"]
    plan = _bootstrap_plan(
        formal=False,
        replicates=int(configuration["replicates"]),
        episodes=int(configuration["evaluation_episodes_per_cell"]),
        repetitions=int(configuration["bootstrap_resamples"]),
    )
    expected_metrics = {
        "operational_valid": True,
        "registered_source_access_valid": bool(
            g35_analysis["operational_valid"]
            and g35_analysis["branch"] == G35_BRANCH
            and g35_analysis["metrics"]["arm_access"][g35.CS_ARM]["access_pass"]
        ),
        **_access_and_noninferiority(g35_evaluation, evaluation, plan),
    }
    if (
        evaluation.get("formal") is not False
        or evaluation.get("source_commit") != source_commit
        or evaluation.get("configuration") != _configuration(formal=False)
        or result.get("schema_version") != SCHEMA_VERSION
        or result.get("algorithm") != ALGORITHM_ID
        or result.get("source_id") != source.SOURCE_ID
        or result.get("stage") != "analyze"
        or result.get("status") != "COMPLETE"
        or result.get("formal") is not False
        or result.get("source_commit") != source_commit
        or result.get("operational_valid") is not True
        or result.get("operational_errors") != []
        or result.get("branch") != NONFORMAL_BRANCH
        or not _json_equivalent(result.get("metrics"), expected_metrics)
        or result.get("evaluation_manifest_digest") != _artifact_digest(evaluation_path)
        or result.get("formal_wall_clock_cap_seconds") != FORMAL_WALL_CLOCK_CAP_SECONDS
        or not projection_matches
        or result.get("formal_projection_executable") is not True
        or projection > FORMAL_WALL_CLOCK_CAP_SECONDS
        or evaluation_seconds + analysis_seconds > NONFORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G36 formal preflight is invalid")


def _g35_reference(g35_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    training = _read_json(g35_root / "train_manifest.json")
    evaluation = _read_json(g35_root / "evaluation_manifest.json")
    analysis = _read_json(g35_root / "analysis_result.json")
    errors = g35_runner._training_errors(g35_root, training) + g35_runner._evaluation_errors(g35_root, training, evaluation)
    if errors:
        raise ValueError("G36 G35 artifact invalid: " + " | ".join(errors))
    configuration = evaluation.get("configuration", {})
    plan = g35_runner._bootstrap_plan(
        formal=True,
        replicates=int(configuration.get("replicates", 0)),
        episodes=int(configuration.get("evaluation_episodes_per_cell", 0)),
        repetitions=int(configuration.get("bootstrap_resamples", 0)),
    )
    cs_access = g35_runner._arm_access(evaluation, g35.CS_ARM, plan)
    if (
        training.get("formal") is not True or training.get("source_id") != G35_SOURCE_ID
        or training.get("source_commit") != G35_CHECKPOINT_SOURCE_COMMIT
        or evaluation.get("formal") is not True
        or evaluation.get("source_commit") != G35_CHECKPOINT_SOURCE_COMMIT
        or analysis.get("schema_version") != g35_runner.SCHEMA_VERSION
        or analysis.get("algorithm") != g35_runner.ALGORITHM_ID
        or analysis.get("source_id") != G35_SOURCE_ID
        or analysis.get("stage") != "analyze"
        or analysis.get("status") != "COMPLETE"
        or analysis.get("formal") is not True or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("branch") != G35_BRANCH
        or analysis.get("source_commit") != G35_CHECKPOINT_SOURCE_COMMIT
        or analysis.get("training_manifest_digest") != _artifact_digest(g35_root / "train_manifest.json")
        or analysis.get("evaluation_manifest_digest") != _artifact_digest(g35_root / "evaluation_manifest.json")
        or not _json_equivalent(
            analysis.get("metrics", {}).get("arm_access", {}).get(g35.CS_ARM),
            cs_access,
        )
        or cs_access.get("access_pass") is not True
    ):
        raise ValueError("G36 exact formal G35 binding mismatch")
    _nonnegative_finite_seconds(analysis.get("stage_wall_time_seconds"))
    return training, evaluation, analysis


def _load_cs_checkpoint(g35_root: Path, training: Mapping[str, Any], *, replicate: int, capacity: int) -> tuple[g35.G35MatchedStateCarryPolicy, str]:
    configuration = training["configuration"]
    arm = training["replicate_results"][replicate]["arms"][g35.CS_ARM]
    model, _ = g35_runner._load_checkpoint(
        g35_root / str(arm["final_checkpoint"]), source_commit=str(training["source_commit"]),
        formal=True, replicate=replicate, arm=g35.CS_ARM, kind="final",
        configuration=configuration, seeds=g35.seed_block(replicate, formal=True), member_capacity=capacity,
    )
    digest = g35_runner._state_digest(model)
    return model, digest


def _g35_cells(evaluation: Mapping[str, Any]) -> dict[tuple[int, int, str, str], Mapping[str, Any]]:
    return g35_runner._cell_map(evaluation)


def _registered_array(
    evaluation: Mapping[str, Any], *, cell_name: str, metric: str,
    replicates: int, episodes: int,
) -> dict[int, np.ndarray]:
    cells = _g35_cells(evaluation)
    return {
        capacity: np.asarray(
            [
                [
                    g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[
                        (replicate, capacity, g35.CS_ARM, cell_name)
                    ]["episodes"][:episodes]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _intervention_array(evaluation: Mapping[str, Any], *, cell_name: str, metric: str) -> dict[int, np.ndarray]:
    cells = {(int(row["replicate"]), int(row["capacity"]), str(row["cell"])): row for row in evaluation["cells"]}
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray([[g34_runner._trace_evidence(episode)[metric] for episode in cells[(replicate, capacity, cell_name)]["episodes"]] for replicate in range(replicates)], dtype=np.float64)
        for capacity in g34.CAPACITIES
    }


def _difference(left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]) -> dict[int, np.ndarray]:
    return {capacity: left[capacity] - right[capacity] for capacity in left}


def _access_and_noninferiority(g35_evaluation: Mapping[str, Any], evaluation: Mapping[str, Any], plan: tuple[np.ndarray, np.ndarray]) -> dict[str, Any]:
    configuration = evaluation["configuration"]
    replicates = int(configuration["replicates"])
    episodes = int(configuration["evaluation_episodes_per_cell"])
    fixed = _intervention_array(evaluation, cell_name="CS_HISTORY_FREE_FIXED_DET", metric="utility")
    fixed_stoch = _intervention_array(evaluation, cell_name="CS_HISTORY_FREE_FIXED_STOCH", metric="utility")
    random = _intervention_array(evaluation, cell_name="CS_HISTORY_FREE_RANDOM_DET", metric="utility")
    random_stoch = _intervention_array(evaluation, cell_name="CS_HISTORY_FREE_RANDOM_STOCH", metric="utility")
    event = _intervention_array(evaluation, cell_name="CS_HISTORY_FREE_RANDOM_DET", metric="minimum_event_window_utility")
    segment = _intervention_array(evaluation, cell_name="CS_HISTORY_FREE_RANDOM_DET", metric="minimum_process_segment_utility")
    fixed_ci = {capacity: _hierarchical_ci(fixed, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    random_ci = {capacity: _hierarchical_ci(random, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    event_ci = {capacity: _hierarchical_ci(event, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    segment_ci = {capacity: _hierarchical_ci(segment, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    process_ci = {capacity: _hierarchical_ci(_difference(random, fixed), capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES}
    fixed_stoch_ci = _hierarchical_ci(fixed_stoch, capacities=g34.CAPACITIES, plan=plan)
    random_stoch_ci = _hierarchical_ci(random_stoch, capacities=g34.CAPACITIES, plan=plan)
    registered = {
        "fixed": _registered_array(g35_evaluation, cell_name=g35_runner.FINAL_FIXED_DET, metric="utility", replicates=replicates, episodes=episodes),
        "random": _registered_array(g35_evaluation, cell_name=g35_runner.FINAL_RANDOM_DET, metric="utility", replicates=replicates, episodes=episodes),
        "fixed_stoch": _registered_array(g35_evaluation, cell_name=g35_runner.FINAL_FIXED_STOCH, metric="utility", replicates=replicates, episodes=episodes),
        "random_stoch": _registered_array(g35_evaluation, cell_name=g35_runner.FINAL_RANDOM_STOCH, metric="utility", replicates=replicates, episodes=episodes),
        "event": _registered_array(g35_evaluation, cell_name=g35_runner.FINAL_RANDOM_DET, metric="minimum_event_window_utility", replicates=replicates, episodes=episodes),
        "segment": _registered_array(g35_evaluation, cell_name=g35_runner.FINAL_RANDOM_DET, metric="minimum_process_segment_utility", replicates=replicates, episodes=episodes),
    }
    deltas = {"fixed": _difference(registered["fixed"], fixed), "random": _difference(registered["random"], random), "fixed_stoch": _difference(registered["fixed_stoch"], fixed_stoch), "random_stoch": _difference(registered["random_stoch"], random_stoch), "event": _difference(registered["event"], event), "segment": _difference(registered["segment"], segment)}
    delta_ci = {name: ({capacity: _hierarchical_ci(values, capacities=(capacity,), plan=plan) for capacity in g34.CAPACITIES} if name in ("fixed", "random", "event", "segment") else _hierarchical_ci(values, capacities=g34.CAPACITIES, plan=plan)) for name, values in deltas.items()}
    primary_ci = _hierarchical_ci(deltas["random"], capacities=g34.CAPACITIES, plan=plan)
    access_pass = all(fixed_ci[c][0] >= UTILITY_FLOOR and random_ci[c][0] >= UTILITY_FLOOR and event_ci[c][0] >= EVENT_FLOOR and segment_ci[c][0] >= SEGMENT_FLOOR and process_ci[c][0] >= PROCESS_MARGIN for c in g34.CAPACITIES) and fixed_stoch_ci[0] >= STOCHASTIC_FLOOR and random_stoch_ci[0] >= STOCHASTIC_FLOOR and _minimum_replicate_mean(fixed) >= MINIMUM_REPLICATE_FLOOR and _minimum_replicate_mean(random) >= MINIMUM_REPLICATE_FLOOR
    access_fail = any(fixed_ci[c][2] < UTILITY_FLOOR or random_ci[c][2] < UTILITY_FLOOR or event_ci[c][2] < EVENT_FLOOR or segment_ci[c][2] < SEGMENT_FLOOR or process_ci[c][2] < PROCESS_MARGIN for c in g34.CAPACITIES) or fixed_stoch_ci[2] < STOCHASTIC_FLOOR or random_stoch_ci[2] < STOCHASTIC_FLOOR or _minimum_replicate_mean(fixed) < MINIMUM_REPLICATE_FLOOR or _minimum_replicate_mean(random) < MINIMUM_REPLICATE_FLOOR
    noninferior = all(delta_ci[name][c][2] <= PROXY_MARGIN for name in ("fixed", "random", "event", "segment") for c in g34.CAPACITIES) and delta_ci["fixed_stoch"][2] <= PROXY_MARGIN and delta_ci["random_stoch"][2] <= PROXY_MARGIN and primary_ci[2] <= PROXY_MARGIN
    material_loss = primary_ci[0] > PROXY_MARGIN or any(delta_ci[name][c][0] > PROXY_MARGIN for name in ("fixed", "random", "event", "segment") for c in g34.CAPACITIES) or delta_ci["fixed_stoch"][0] > PROXY_MARGIN or delta_ci["random_stoch"][0] > PROXY_MARGIN
    return {"fixed_utility_ci95": fixed_ci, "fixed_stochastic_pooled_ci95": fixed_stoch_ci, "minimum_fixed_deterministic_replicate_mean": _minimum_replicate_mean(fixed), "random_utility_ci95": random_ci, "random_event_window_ci95": event_ci, "random_process_segment_ci95": segment_ci, "random_minus_fixed_ci95": process_ci, "random_stochastic_pooled_ci95": random_stoch_ci, "minimum_random_deterministic_replicate_mean": _minimum_replicate_mean(random), "registered_minus_intervention_ci95": delta_ci, "primary_delta_hp_ci95": primary_ci, "intervention_access_pass": bool(access_pass), "intervention_access_confident_fail": bool(access_fail), "proxy_noninferior": bool(noninferior), "material_proxy_loss": bool(material_loss)}


def evaluate(*, run_root: Path, g35_root: Path, source_commit: str, formal: bool, authorization_token: str | None = None, preflight_root: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G36 evaluation requires an integrated source commit")
    configure_runtime(
        BOOTSTRAP_SEED + (0 if formal else source.NONFORMAL_SEED_OFFSET)
    )
    preflight_binding: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G36 formal evaluation requires dedicated authority token")
        _validate_formal_preflight(
            preflight_root, source_commit=source_commit, g35_root=g35_root
        )
        assert preflight_root is not None
        preflight_binding = {
            "source_commit": source_commit,
            "evaluation_manifest_digest": _artifact_digest(preflight_root / "evaluation_manifest.json"),
            "analysis_result_digest": _artifact_digest(preflight_root / "analysis_result.json"),
        }
    elif authorization_token is not None or preflight_root is not None:
        raise ValueError("G36 nonformal evaluation cannot carry formal authority")
    configuration = _configuration(formal=formal)
    training, g35_evaluation, g35_analysis = _g35_reference(g35_root)
    bank = source.G36HistoryProxyDonorBank.build()
    cells: list[dict[str, Any]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            model, checkpoint_digest = _load_cs_checkpoint(g35_root, training, replicate=replicate, capacity=capacity)
            processes = g35.make_process_ledgers(replicate=replicate, capacity=capacity, episode_count=int(configuration["evaluation_episodes_per_cell"]), formal=True)
            tape = source.G36HistoryProxyTape(bank, replicate=replicate, capacity=capacity, formal=formal)
            for name, process_kind, deterministic in CELLS:
                before = g35_runner._state_digest(model)
                episodes, audit = source.evaluate_g36_history_proxy(model, processes=processes, action_seed=g35.seed_block(replicate, formal=True)["evaluation_action"], process_kind=process_kind, deterministic=deterministic, tape=tape)
                after = g35_runner._state_digest(model)
                cells.append({"replicate": replicate, "capacity": capacity, "arm": g35.CS_ARM, "cell": name, "process": process_kind, "deterministic": deterministic, "checkpoint": "final", "checkpoint_digest": checkpoint_digest, "state_before": before, "state_after": after, "optimizer_steps": 0, "episodes": list(episodes), "audit": audit})
    manifest = {"schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID, "source_id": source.SOURCE_ID, "stage": "evaluate", "status": "COMPLETE", "formal": formal, "source_commit": source_commit, "authorization_token": authorization_token, "preflight_root": str(preflight_root.resolve()) if preflight_root is not None else None, "preflight_binding": preflight_binding, "runtime": _runtime_identity(), "configuration": configuration, "g35_root": str(g35_root.resolve()), "g35_binding": {"source_id": G35_SOURCE_ID, "branch": G35_BRANCH, "checkpoint_source_commit": G35_CHECKPOINT_SOURCE_COMMIT, "training_manifest_digest": _artifact_digest(g35_root / "train_manifest.json"), "evaluation_manifest_digest": _artifact_digest(g35_root / "evaluation_manifest.json"), "analysis_result_digest": _artifact_digest(g35_root / "analysis_result.json")}, "g35_analysis": {"branch": g35_analysis["branch"], "operational_valid": g35_analysis["operational_valid"], "cs_access_pass": g35_analysis["metrics"]["arm_access"][g35.CS_ARM]["access_pass"]}, "donor_bank_active_counts": list(bank.supported_active_counts), "cells": cells, "stage_wall_time_seconds": time.perf_counter() - started}
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _evaluation_errors(run_root: Path, evaluation: Mapping[str, Any], *, g35_root: Path) -> list[str]:
    errors: list[str] = []
    serialized_g35_root = evaluation.get("g35_root")
    if (
        not isinstance(serialized_g35_root, str)
        or not serialized_g35_root.strip()
        or not Path(serialized_g35_root).is_absolute()
        or Path(serialized_g35_root).resolve() != g35_root.resolve()
    ):
        return ["G36 serialized G35 root mismatch"]
    try:
        training, _, g35_analysis = _g35_reference(g35_root)
    except (OSError, KeyError, TypeError, ValueError) as error:
        return [str(error)]
    formal_value = evaluation.get("formal")
    if not isinstance(formal_value, bool):
        return ["G36 evaluation formal flag mismatch"]
    formal = formal_value
    configuration = _configuration(formal=formal)
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("configuration") != configuration
        or re.fullmatch(r"[0-9a-f]{40}", str(evaluation.get("source_commit", ""))) is None
    ):
        errors.append("G36 evaluation identity mismatch")
        return errors
    binding = evaluation.get("g35_binding")
    expected_binding = {
        "source_id": G35_SOURCE_ID,
        "branch": G35_BRANCH,
        "checkpoint_source_commit": G35_CHECKPOINT_SOURCE_COMMIT,
        "training_manifest_digest": _artifact_digest(g35_root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(g35_root / "evaluation_manifest.json"),
        "analysis_result_digest": _artifact_digest(g35_root / "analysis_result.json"),
    }
    expected_g35_analysis = {
        "branch": g35_analysis["branch"],
        "operational_valid": g35_analysis["operational_valid"],
        "cs_access_pass": g35_analysis["metrics"]["arm_access"][g35.CS_ARM]["access_pass"],
    }
    if (
        binding != expected_binding
        or evaluation.get("g35_analysis") != expected_g35_analysis
        or evaluation.get("runtime") != _runtime_identity()
    ):
        return ["G36 G35 binding/runtime mismatch"]
    try:
        _nonnegative_finite_seconds(evaluation.get("stage_wall_time_seconds"))
    except ValueError as error:
        errors.append(str(error))
    preflight_binding = evaluation.get("preflight_binding")
    if formal:
        serialized_preflight_root = evaluation.get("preflight_root")
        if (
            evaluation.get("authorization_token") != AUTHORIZATION_TOKEN
            or not isinstance(serialized_preflight_root, str)
            or not serialized_preflight_root.strip()
            or not Path(serialized_preflight_root).is_absolute()
        ):
            return ["G36 formal authority/preflight binding mismatch"]
        preflight_root = Path(serialized_preflight_root)
        expected_preflight_binding = {
            "source_commit": evaluation.get("source_commit"),
            "evaluation_manifest_digest": _artifact_digest(preflight_root / "evaluation_manifest.json"),
            "analysis_result_digest": _artifact_digest(preflight_root / "analysis_result.json"),
        }
        if preflight_binding != expected_preflight_binding:
            return ["G36 formal authority/preflight binding mismatch"]
        try:
            _validate_formal_preflight(
                preflight_root,
                source_commit=str(evaluation["source_commit"]),
                g35_root=g35_root,
            )
        except (OSError, KeyError, TypeError, ValueError) as error:
            return [f"G36 formal preflight invalid: {error}"]
    elif (
        preflight_binding is not None
        or evaluation.get("preflight_root") is not None
        or evaluation.get("authorization_token") is not None
    ):
        return ["G36 nonformal authority binding mismatch"]
    bank = source.G36HistoryProxyDonorBank.build()
    if evaluation.get("donor_bank_active_counts") != list(bank.supported_active_counts):
        return ["G36 donor-bank support mismatch"]
    expected_keys = {(replicate, capacity, name) for replicate in range(int(configuration["replicates"])) for capacity in g34.CAPACITIES for name, _, _ in CELLS}
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(configuration["total_new_cells"]):
        return ["G36 evaluation cell inventory mismatch"]
    observed: set[tuple[int, int, str]] = set()
    proxy_digests: dict[tuple[int, int, str], tuple[str, ...]] = {}
    action_digests: dict[tuple[int, int, str], str] = {}
    roster_traces: dict[tuple[int, int, str], tuple[tuple[int, ...], ...]] = {}
    for cell in cells:
        try:
            key = (int(cell["replicate"]), int(cell["capacity"]), str(cell["cell"]))
            expected = next(row for row in CELLS if row[0] == key[2])
            if key in observed or key not in expected_keys or cell.get("arm") != g35.CS_ARM or cell.get("process") != expected[1] or cell.get("deterministic") is not expected[2] or cell.get("checkpoint") != "final" or cell.get("optimizer_steps") != 0 or cell.get("state_before") != cell.get("state_after"):
                raise ValueError("G36 cell route/checkpoint mismatch")
            model, digest = _load_cs_checkpoint(g35_root, training, replicate=key[0], capacity=key[1])
            del model
            if cell.get("checkpoint_digest") != digest or cell.get("state_before") != digest:
                raise ValueError("G36 checkpoint binding mismatch")
            audit = cell["audit"]
            if any(audit.get(name) != 0 for name in ("actual_age_read_count", "actual_previous_action_read_count", "actual_actor_time_read_count", "critic_transform_count", "proxy_tape_target_history_read_count", "checkpoint_update_count")) or audit.get("lifecycle_valid") is not True:
                raise ValueError("G36 actor-only/history audit mismatch")
            episodes = cell["episodes"]
            if not isinstance(episodes, list) or len(episodes) != int(configuration["evaluation_episodes_per_cell"]):
                raise ValueError("G36 episode inventory mismatch")
            episode_proxy_digests = audit.get("proxy_tape_episode_digests")
            action_noise_digest = audit.get("action_noise_digest")
            if (
                not isinstance(episode_proxy_digests, list)
                or len(episode_proxy_digests) != len(episodes)
                or any(re.fullmatch(r"[0-9a-f]{64}", str(value)) is None for value in episode_proxy_digests)
                or re.fullmatch(r"[0-9a-f]{64}", str(action_noise_digest)) is None
            ):
                raise ValueError("G36 proxy/action digest inventory mismatch")
            expected_processes = g35.make_process_ledgers(
                replicate=key[0], capacity=key[1],
                episode_count=int(configuration["evaluation_episodes_per_cell"]), formal=True,
            )
            traces: list[tuple[int, ...]] = []
            for index, episode in enumerate(episodes):
                expected_process = expected_processes[index]
                trace = g34_runner._trace_evidence(episode)
                expected_roster = expected_process.expected_roster_sizes if expected[1] == "random" else expected_process.base.expected_roster_sizes
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != expected_process.episode_id
                    or episode.get("profile") != expected_process.profile.name
                    or episode.get("event_times") != list(expected_process.event_times)
                    or episode.get("event_order") != list(expected_process.event_order)
                    or episode.get("count_trajectory") != list(expected_process.count_trajectory)
                    or episode.get("signature") != repr(expected_process.signature)
                    or trace["roster_size_trace"] != tuple(expected_roster)
                    or episode.get("roster_sizes_valid") is not True
                    or not g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G36 trace evidence mismatch")
                traces.append(trace["roster_size_trace"])
            expected_noise = roster_env.make_action_noise(
                (row.episode_id for row in expected_processes),
                action_seed=g35.seed_block(key[0], formal=True)["evaluation_action"],
                member_capacity=key[1],
            )
            expected_action_digest = hashlib.sha256(
                np.ascontiguousarray(expected_noise).tobytes()
            ).hexdigest()
            if action_noise_digest != expected_action_digest:
                raise ValueError("G36 action-noise coupling mismatch")
            proxy_digests[key] = tuple(str(value) for value in episode_proxy_digests)
            action_digests[key] = str(action_noise_digest)
            roster_traces[key] = tuple(traces)
            observed.add(key)
        except (KeyError, StopIteration, TypeError, ValueError) as error:
            errors.append(str(error))
    if observed != expected_keys:
        errors.append("G36 evaluation cell key set mismatch")
    if not errors:
        for replicate in range(int(configuration["replicates"])):
            for capacity in g34.CAPACITIES:
                fixed_det = (replicate, capacity, "CS_HISTORY_FREE_FIXED_DET")
                fixed_stoch = (replicate, capacity, "CS_HISTORY_FREE_FIXED_STOCH")
                random_det = (replicate, capacity, "CS_HISTORY_FREE_RANDOM_DET")
                random_stoch = (replicate, capacity, "CS_HISTORY_FREE_RANDOM_STOCH")
                if (
                    proxy_digests[fixed_det] != proxy_digests[fixed_stoch]
                    or proxy_digests[random_det] != proxy_digests[random_stoch]
                    or len({action_digests[key] for key in (fixed_det, fixed_stoch, random_det, random_stoch)}) != 1
                ):
                    errors.append("G36 paired proxy/action reuse mismatch")
                    continue
                for episode_index, (fixed_trace, random_trace) in enumerate(
                    zip(roster_traces[fixed_det], roster_traces[random_det])
                ):
                    if (
                        fixed_trace == random_trace
                        and proxy_digests[fixed_det][episode_index]
                        != proxy_digests[random_det][episode_index]
                    ):
                        errors.append("G36 fixed/random proxy reuse mismatch")
                        break
    return errors


def analyze(*, run_root: Path, g35_root: Path, require_formal: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(evaluation.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G36 analysis requires formal artifacts")
    configure_runtime(BOOTSTRAP_SEED + (0 if formal else source.NONFORMAL_SEED_OFFSET))
    errors = _evaluation_errors(run_root, evaluation, g35_root=g35_root)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        _, g35_evaluation, g35_analysis = _g35_reference(g35_root)
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(formal=formal, replicates=int(configuration["replicates"]), episodes=int(configuration["evaluation_episodes_per_cell"]), repetitions=int(configuration["bootstrap_resamples"]))
        access = _access_and_noninferiority(g35_evaluation, evaluation, plan)
        metrics.update({"registered_source_access_valid": bool(g35_analysis["operational_valid"] and g35_analysis["branch"] == G35_BRANCH and g35_analysis["metrics"]["arm_access"][g35.CS_ARM]["access_pass"]), **access})
    analysis_seconds = time.perf_counter() - started
    evaluation_seconds = float(evaluation.get("stage_wall_time_seconds", float("nan")))
    projection = 1.25 * (48.0 * evaluation_seconds + 40.0 * analysis_seconds) if not formal and not errors else None
    executable = projection is not None and np.isfinite(projection) and projection <= FORMAL_WALL_CLOCK_CAP_SECONDS and evaluation_seconds + analysis_seconds <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
    branch = INVALID_BRANCH if errors else (select_g36_result_branch(metrics) if formal else (NONFORMAL_BRANCH if executable else NON_EXECUTABLE_BRANCH))
    result = {"schema_version": SCHEMA_VERSION, "algorithm": ALGORITHM_ID, "source_id": source.SOURCE_ID, "stage": "analyze", "status": "COMPLETE" if not errors else "INVALID", "formal": formal, "source_commit": evaluation.get("source_commit"), "operational_valid": not errors, "operational_errors": errors, "branch": branch, "metrics": metrics, "evaluation_manifest_digest": _artifact_digest(run_root / "evaluation_manifest.json"), "stage_wall_time_seconds": analysis_seconds, "formal_projection_seconds": projection, "formal_projection_executable": executable, "formal_wall_clock_cap_seconds": FORMAL_WALL_CLOCK_CAP_SECONDS}
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, g35_root: Path, source_commit: str) -> dict[str, Any]:
    evaluate(run_root=run_root, g35_root=g35_root, source_commit=source_commit, formal=False)
    return analyze(run_root=run_root, g35_root=g35_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--g35-root", type=Path, required=True)
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--require-formal", action="store_true")
    args = parser.parse_args()
    if args.mode == "evaluate":
        value = evaluate(run_root=args.run_root, g35_root=args.g35_root, source_commit=args.source_commit, formal=args.formal, authorization_token=args.authorization_token, preflight_root=args.preflight_root)
    elif args.mode == "analyze":
        value = analyze(run_root=args.run_root, g35_root=args.g35_root, require_formal=args.require_formal)
    else:
        value = exercise(run_root=args.run_root, g35_root=args.g35_root, source_commit=args.source_commit)
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""Evaluate and analyze the frozen zero-training G37 coherence contract."""

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

from ha_ctse_process import continuous_roster_history_proxy_coherence_g37 as source
from ha_ctse_process import continuous_roster_history_proxy_free_cs_g36 as g36
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from envs.continuous_roster import runtime_capacity as roster_env
from scripts import run_continuous_roster_history_proxy_free_cs_g36 as g36_runner
from scripts import run_continuous_roster_random_process_g34 as g34_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = source.ALGORITHM_ID
G36_SOURCE_ID = g36.SOURCE_ID
G36_SOURCE_COMMIT = "8f1cd60068426ac2c0a35ef2d9f4d624b1a01c04"
G36_BRANCH = "HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36"
G36_EVALUATION_SHA256 = "03b6ae2bca6f284524b442bd642dd306b8a8db7e6103d177e6982bfeea864bf6"
G36_ANALYSIS_SHA256 = "0243133c102645f3310104f9b3371e21880714740ec9d8f7fa1527f38199b4ae"
AUTHORIZATION_TOKEN = "CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_FORMAL_AUTHORIZATION_V1"
INVALID_BRANCH = "INVALID_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37"
SOURCE_FAILURE_BRANCH = "SOURCE_OR_G36_REFERENCE_FAILURE_G37"
SUFFICIENT_BRANCH = "FACTORIZED_HISTORY_PROXY_SUFFICIENT_G37"
LOAD_BEARING_BRANCH = "JOINT_DONOR_COHERENCE_LOAD_BEARING_G37"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37"
NONFORMAL_BRANCH = "NONFORMAL_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_COMPLETE"
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
BOOTSTRAP_SEED = 10_364_037
UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
COHERENCE_MARGIN = 0.05
CELLS = (
    ("CS_FACTORIZED_FIXED_DET", "fixed", True),
    ("CS_FACTORIZED_FIXED_STOCH", "fixed", False),
    ("CS_FACTORIZED_RANDOM_DET", "random", True),
    ("CS_FACTORIZED_RANDOM_STOCH", "random", False),
)
JOINT_CELL = {
    "CS_FACTORIZED_FIXED_DET": "CS_HISTORY_FREE_FIXED_DET",
    "CS_FACTORIZED_FIXED_STOCH": "CS_HISTORY_FREE_FIXED_STOCH",
    "CS_FACTORIZED_RANDOM_DET": "CS_HISTORY_FREE_RANDOM_DET",
    "CS_FACTORIZED_RANDOM_STOCH": "CS_HISTORY_FREE_RANDOM_STOCH",
}


def configure_runtime(seed: int) -> None:
    torch.set_num_threads(1)
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("G37 JSON artifact must be an object")
    return value


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_equivalent(left: object, right: object) -> bool:
    def canonical(value: object) -> str:
        return json.dumps(
            json.loads(json.dumps(value)), sort_keys=True, separators=(",", ":")
        )

    return canonical(left) == canonical(right)


def _runtime_identity() -> dict[str, object]:
    return {
        "backend": "cpu",
        "torch_threads": int(torch.get_num_threads()),
        "torch": str(torch.__version__),
    }


def _configuration(*, formal: bool) -> dict[str, object]:
    replicates = FORMAL_REPLICATES if formal else EXERCISE_REPLICATES
    episodes = FORMAL_EPISODES if formal else EXERCISE_EPISODES
    bootstrap = (
        FORMAL_BOOTSTRAP_RESAMPLES if formal else EXERCISE_BOOTSTRAP_RESAMPLES
    )
    return {
        "formal": formal,
        "replicates": replicates,
        "capacities": list(g34.CAPACITIES),
        "factorized_cells_per_capacity": 4,
        "total_new_cells": replicates * len(g34.CAPACITIES) * 4,
        "evaluation_episodes_per_cell": episodes,
        "evaluation_episodes": replicates
        * len(g34.CAPACITIES)
        * 4
        * episodes,
        "horizon": HORIZON,
        "evaluation_transitions": replicates
        * len(g34.CAPACITIES)
        * 4
        * episodes
        * HORIZON,
        "optimizer_steps": 0,
        "bootstrap_resamples": bootstrap,
        "K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }


def _bootstrap_plan(
    *, formal: bool, replicates: int, episodes: int, repetitions: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(
        BOOTSTRAP_SEED + (0 if formal else source.NONFORMAL_SEED_OFFSET)
    )
    return (
        rng.integers(0, replicates, size=(repetitions, replicates), dtype=np.int16),
        rng.integers(
            0,
            episodes,
            size=(repetitions, replicates, len(g34.CAPACITIES), episodes),
            dtype=np.int16,
        ),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray],
    *,
    capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    return g36_runner._hierarchical_ci(values, capacities=capacities, plan=plan)


def _minimum_replicate_mean(values: Mapping[int, np.ndarray]) -> float:
    return g36_runner._minimum_replicate_mean(values)


def _difference(
    left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]
) -> dict[int, np.ndarray]:
    return g36_runner._difference(left, right)


def select_g37_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or not bool(metrics["g36_reference_valid"]):
        return SOURCE_FAILURE_BRANCH
    if bool(metrics["factorized_access_pass"]) and bool(
        metrics["coherence_noninferior"]
    ):
        return SUFFICIENT_BRANCH
    if bool(metrics["factorized_access_confident_fail"]) or bool(
        metrics["material_coherence_loss"]
    ):
        return LOAD_BEARING_BRANCH
    return UNDERPOWERED_BRANCH


def _nonnegative_finite_seconds(value: object) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not np.isfinite(value)
        or value < 0.0
    ):
        raise ValueError("G37 stage timing invalid")
    return float(value)


def _donor_bank_digest(bank: g36.G36HistoryProxyDonorBank) -> str:
    digest = hashlib.sha256()
    for count in bank.supported_active_counts:
        digest.update(int(count).to_bytes(2, "little", signed=False))
        digest.update(np.ascontiguousarray(bank.snapshots(count)).tobytes())
    return digest.hexdigest()


def _expected_action_noise_digest(
    *, replicate: int, capacity: int, episode_count: int
) -> str:
    processes = g35.make_process_ledgers(
        replicate=replicate,
        capacity=capacity,
        episode_count=episode_count,
        formal=True,
    )
    noise = roster_env.make_action_noise(
        (row.episode_id for row in processes),
        action_seed=g35.seed_block(replicate, formal=True)["evaluation_action"],
        member_capacity=capacity,
    )
    return hashlib.sha256(np.ascontiguousarray(noise).tobytes()).hexdigest()


def _g36_reference(
    g36_root: Path, g35_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    evaluation_path = g36_root / "evaluation_manifest.json"
    analysis_path = g36_root / "analysis_result.json"
    evaluation = _read_json(evaluation_path)
    analysis = _read_json(analysis_path)
    errors = g36_runner._evaluation_errors(
        g36_root, evaluation, g35_root=g35_root
    )
    if errors:
        raise ValueError("G37 G36 artifact invalid: " + " | ".join(errors))
    configuration = evaluation.get("configuration", {})
    _, g35_evaluation, g35_analysis = g36_runner._g35_reference(g35_root)
    plan = g36_runner._bootstrap_plan(
        formal=True,
        replicates=int(configuration.get("replicates", 0)),
        episodes=int(configuration.get("evaluation_episodes_per_cell", 0)),
        repetitions=int(configuration.get("bootstrap_resamples", 0)),
    )
    expected_metrics = {
        "operational_valid": True,
        "registered_source_access_valid": bool(
            g35_analysis["operational_valid"]
            and g35_analysis["branch"] == g36_runner.G35_BRANCH
            and g35_analysis["metrics"]["arm_access"][g35.CS_ARM]["access_pass"]
        ),
        **g36_runner._access_and_noninferiority(
            g35_evaluation, evaluation, plan
        ),
    }
    if (
        evaluation.get("formal") is not True
        or evaluation.get("source_id") != G36_SOURCE_ID
        or evaluation.get("source_commit") != G36_SOURCE_COMMIT
        or evaluation.get("configuration") != g36_runner._configuration(formal=True)
        or _artifact_digest(evaluation_path) != G36_EVALUATION_SHA256
        or _artifact_digest(analysis_path) != G36_ANALYSIS_SHA256
        or analysis.get("schema_version") != g36_runner.SCHEMA_VERSION
        or analysis.get("algorithm") != g36_runner.ALGORITHM_ID
        or analysis.get("source_id") != G36_SOURCE_ID
        or analysis.get("stage") != "analyze"
        or analysis.get("status") != "COMPLETE"
        or analysis.get("formal") is not True
        or analysis.get("source_commit") != G36_SOURCE_COMMIT
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("branch") != G36_BRANCH
        or analysis.get("evaluation_manifest_digest") != G36_EVALUATION_SHA256
        or not _json_equivalent(analysis.get("metrics"), expected_metrics)
    ):
        raise ValueError("G37 exact formal G36 reference binding mismatch")
    return evaluation, analysis


def _joint_array(
    evaluation: Mapping[str, Any],
    *,
    cell_name: str,
    metric: str,
    replicates: int,
    episodes: int,
) -> dict[int, np.ndarray]:
    cells = {
        (int(row["replicate"]), int(row["capacity"]), str(row["cell"])): row
        for row in evaluation["cells"]
    }
    return {
        capacity: np.asarray(
            [
                [
                    g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, cell_name)][
                        "episodes"
                    ][:episodes]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _factorized_array(
    evaluation: Mapping[str, Any], *, cell_name: str, metric: str
) -> dict[int, np.ndarray]:
    cells = {
        (int(row["replicate"]), int(row["capacity"]), str(row["cell"])): row
        for row in evaluation["cells"]
    }
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray(
            [
                [
                    g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, cell_name)][
                        "episodes"
                    ]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _access_and_noninferiority(
    g36_evaluation: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    plan: tuple[np.ndarray, np.ndarray],
) -> dict[str, Any]:
    configuration = evaluation["configuration"]
    replicates = int(configuration["replicates"])
    episodes = int(configuration["evaluation_episodes_per_cell"])
    factorized = {
        "fixed": _factorized_array(
            evaluation, cell_name="CS_FACTORIZED_FIXED_DET", metric="utility"
        ),
        "fixed_stoch": _factorized_array(
            evaluation,
            cell_name="CS_FACTORIZED_FIXED_STOCH",
            metric="utility",
        ),
        "random": _factorized_array(
            evaluation, cell_name="CS_FACTORIZED_RANDOM_DET", metric="utility"
        ),
        "random_stoch": _factorized_array(
            evaluation,
            cell_name="CS_FACTORIZED_RANDOM_STOCH",
            metric="utility",
        ),
        "event": _factorized_array(
            evaluation,
            cell_name="CS_FACTORIZED_RANDOM_DET",
            metric="minimum_event_window_utility",
        ),
        "segment": _factorized_array(
            evaluation,
            cell_name="CS_FACTORIZED_RANDOM_DET",
            metric="minimum_process_segment_utility",
        ),
    }
    joint = {
        "fixed": _joint_array(
            g36_evaluation,
            cell_name="CS_HISTORY_FREE_FIXED_DET",
            metric="utility",
            replicates=replicates,
            episodes=episodes,
        ),
        "fixed_stoch": _joint_array(
            g36_evaluation,
            cell_name="CS_HISTORY_FREE_FIXED_STOCH",
            metric="utility",
            replicates=replicates,
            episodes=episodes,
        ),
        "random": _joint_array(
            g36_evaluation,
            cell_name="CS_HISTORY_FREE_RANDOM_DET",
            metric="utility",
            replicates=replicates,
            episodes=episodes,
        ),
        "random_stoch": _joint_array(
            g36_evaluation,
            cell_name="CS_HISTORY_FREE_RANDOM_STOCH",
            metric="utility",
            replicates=replicates,
            episodes=episodes,
        ),
        "event": _joint_array(
            g36_evaluation,
            cell_name="CS_HISTORY_FREE_RANDOM_DET",
            metric="minimum_event_window_utility",
            replicates=replicates,
            episodes=episodes,
        ),
        "segment": _joint_array(
            g36_evaluation,
            cell_name="CS_HISTORY_FREE_RANDOM_DET",
            metric="minimum_process_segment_utility",
            replicates=replicates,
            episodes=episodes,
        ),
    }
    fixed_ci = {
        capacity: _hierarchical_ci(
            factorized["fixed"], capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    random_ci = {
        capacity: _hierarchical_ci(
            factorized["random"], capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    event_ci = {
        capacity: _hierarchical_ci(
            factorized["event"], capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    segment_ci = {
        capacity: _hierarchical_ci(
            factorized["segment"], capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    process_ci = {
        capacity: _hierarchical_ci(
            _difference(factorized["random"], factorized["fixed"]),
            capacities=(capacity,),
            plan=plan,
        )
        for capacity in g34.CAPACITIES
    }
    fixed_stoch_ci = _hierarchical_ci(
        factorized["fixed_stoch"], capacities=g34.CAPACITIES, plan=plan
    )
    random_stoch_ci = _hierarchical_ci(
        factorized["random_stoch"], capacities=g34.CAPACITIES, plan=plan
    )
    deltas = {
        name: _difference(joint[name], factorized[name])
        for name in joint
    }
    delta_ci = {
        name: (
            {
                capacity: _hierarchical_ci(
                    values, capacities=(capacity,), plan=plan
                )
                for capacity in g34.CAPACITIES
            }
            if name in ("fixed", "random", "event", "segment")
            else _hierarchical_ci(values, capacities=g34.CAPACITIES, plan=plan)
        )
        for name, values in deltas.items()
    }
    primary_ci = _hierarchical_ci(
        deltas["random"], capacities=g34.CAPACITIES, plan=plan
    )
    access_pass = (
        all(
            fixed_ci[c][0] >= UTILITY_FLOOR
            and random_ci[c][0] >= UTILITY_FLOOR
            and event_ci[c][0] >= EVENT_FLOOR
            and segment_ci[c][0] >= SEGMENT_FLOOR
            and process_ci[c][0] >= PROCESS_MARGIN
            for c in g34.CAPACITIES
        )
        and fixed_stoch_ci[0] >= STOCHASTIC_FLOOR
        and random_stoch_ci[0] >= STOCHASTIC_FLOOR
        and _minimum_replicate_mean(factorized["fixed"])
        >= MINIMUM_REPLICATE_FLOOR
        and _minimum_replicate_mean(factorized["random"])
        >= MINIMUM_REPLICATE_FLOOR
    )
    access_fail = (
        any(
            fixed_ci[c][2] < UTILITY_FLOOR
            or random_ci[c][2] < UTILITY_FLOOR
            or event_ci[c][2] < EVENT_FLOOR
            or segment_ci[c][2] < SEGMENT_FLOOR
            or process_ci[c][2] < PROCESS_MARGIN
            for c in g34.CAPACITIES
        )
        or fixed_stoch_ci[2] < STOCHASTIC_FLOOR
        or random_stoch_ci[2] < STOCHASTIC_FLOOR
        or _minimum_replicate_mean(factorized["fixed"])
        < MINIMUM_REPLICATE_FLOOR
        or _minimum_replicate_mean(factorized["random"])
        < MINIMUM_REPLICATE_FLOOR
    )
    noninferior = (
        all(
            delta_ci[name][c][2] <= COHERENCE_MARGIN
            for name in ("fixed", "random", "event", "segment")
            for c in g34.CAPACITIES
        )
        and delta_ci["fixed_stoch"][2] <= COHERENCE_MARGIN
        and delta_ci["random_stoch"][2] <= COHERENCE_MARGIN
        and primary_ci[2] <= COHERENCE_MARGIN
    )
    material_loss = (
        primary_ci[0] > COHERENCE_MARGIN
        or any(
            delta_ci[name][c][0] > COHERENCE_MARGIN
            for name in ("fixed", "random", "event", "segment")
            for c in g34.CAPACITIES
        )
        or delta_ci["fixed_stoch"][0] > COHERENCE_MARGIN
        or delta_ci["random_stoch"][0] > COHERENCE_MARGIN
    )
    return {
        "fixed_utility_ci95": fixed_ci,
        "fixed_stochastic_pooled_ci95": fixed_stoch_ci,
        "minimum_fixed_deterministic_replicate_mean": _minimum_replicate_mean(
            factorized["fixed"]
        ),
        "random_utility_ci95": random_ci,
        "random_event_window_ci95": event_ci,
        "random_process_segment_ci95": segment_ci,
        "random_minus_fixed_ci95": process_ci,
        "random_stochastic_pooled_ci95": random_stoch_ci,
        "minimum_random_deterministic_replicate_mean": _minimum_replicate_mean(
            factorized["random"]
        ),
        "joint_minus_factorized_ci95": delta_ci,
        "primary_delta_coh_ci95": primary_ci,
        "factorized_access_pass": bool(access_pass),
        "factorized_access_confident_fail": bool(access_fail),
        "coherence_noninferior": bool(noninferior),
        "material_coherence_loss": bool(material_loss),
    }


def _validate_formal_preflight(
    preflight_root: Path | None,
    *,
    source_commit: str,
    g35_root: Path,
    g36_root: Path,
) -> None:
    if preflight_root is None:
        raise ValueError("G37 formal evaluation requires a matching preflight")
    root = Path(preflight_root)
    evaluation_path = root / "evaluation_manifest.json"
    analysis_path = root / "analysis_result.json"
    evaluation = _read_json(evaluation_path)
    result = _read_json(analysis_path)
    errors = _evaluation_errors(
        root, evaluation, g35_root=g35_root, g36_root=g36_root
    )
    if errors:
        raise ValueError("G37 formal preflight artifacts are invalid: " + " | ".join(errors))
    evaluation_seconds = _nonnegative_finite_seconds(
        evaluation.get("stage_wall_time_seconds")
    )
    analysis_seconds = _nonnegative_finite_seconds(
        result.get("stage_wall_time_seconds")
    )
    projection = 1.25 * (48.0 * evaluation_seconds + 40.0 * analysis_seconds)
    g36_evaluation, _ = _g36_reference(g36_root, g35_root)
    configuration = evaluation["configuration"]
    plan = _bootstrap_plan(
        formal=False,
        replicates=int(configuration["replicates"]),
        episodes=int(configuration["evaluation_episodes_per_cell"]),
        repetitions=int(configuration["bootstrap_resamples"]),
    )
    expected_metrics = {
        "operational_valid": True,
        "source_valid": True,
        "g36_reference_valid": True,
        **_access_and_noninferiority(g36_evaluation, evaluation, plan),
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
        or result.get("evaluation_manifest_digest")
        != _artifact_digest(evaluation_path)
        or not np.isclose(
            float(result.get("formal_projection_seconds", float("nan"))),
            projection,
            rtol=0.0,
            atol=1e-9,
        )
        or result.get("formal_projection_executable") is not True
        or projection > FORMAL_WALL_CLOCK_CAP_SECONDS
        or evaluation_seconds + analysis_seconds > NONFORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G37 formal preflight is invalid")


def evaluate(
    *,
    run_root: Path,
    g35_root: Path,
    g36_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None = None,
    preflight_root: Path | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G37 evaluation requires an integrated source commit")
    configure_runtime(
        BOOTSTRAP_SEED + (0 if formal else source.NONFORMAL_SEED_OFFSET)
    )
    preflight_binding: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G37 formal evaluation requires dedicated authority token")
        _validate_formal_preflight(
            preflight_root,
            source_commit=source_commit,
            g35_root=g35_root,
            g36_root=g36_root,
        )
        assert preflight_root is not None
        preflight_binding = {
            "source_commit": source_commit,
            "evaluation_manifest_digest": _artifact_digest(
                preflight_root / "evaluation_manifest.json"
            ),
            "analysis_result_digest": _artifact_digest(
                preflight_root / "analysis_result.json"
            ),
        }
    elif authorization_token is not None or preflight_root is not None:
        raise ValueError("G37 nonformal evaluation cannot carry formal authority")
    configuration = _configuration(formal=formal)
    g36_evaluation, g36_analysis = _g36_reference(g36_root, g35_root)
    training, _, _ = g36_runner._g35_reference(g35_root)
    bank = g36.G36HistoryProxyDonorBank.build()
    cells: list[dict[str, Any]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            model, checkpoint_digest = g36_runner._load_cs_checkpoint(
                g35_root, training, replicate=replicate, capacity=capacity
            )
            processes = g35.make_process_ledgers(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=True,
            )
            tape = source.G37FactorizedHistoryProxyTape(
                bank, replicate=replicate, capacity=capacity, formal=formal
            )
            for name, process_kind, deterministic in CELLS:
                before = g35_runner._state_digest(model)
                episodes, audit = source.evaluate_g37_factorized_history_proxy(
                    model,
                    processes=processes,
                    action_seed=g35.seed_block(replicate, formal=True)[
                        "evaluation_action"
                    ],
                    process_kind=process_kind,
                    deterministic=deterministic,
                    tape=tape,
                )
                after = g35_runner._state_digest(model)
                cells.append(
                    {
                        "replicate": replicate,
                        "capacity": capacity,
                        "arm": g35.CS_ARM,
                        "cell": name,
                        "process": process_kind,
                        "deterministic": deterministic,
                        "checkpoint": "final",
                        "checkpoint_digest": checkpoint_digest,
                        "state_before": before,
                        "state_after": after,
                        "optimizer_steps": 0,
                        "episodes": list(episodes),
                        "audit": audit,
                    }
                )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "authorization_token": authorization_token,
        "preflight_root": (
            str(preflight_root.resolve()) if preflight_root is not None else None
        ),
        "preflight_binding": preflight_binding,
        "runtime": _runtime_identity(),
        "configuration": configuration,
        "g35_root": str(g35_root.resolve()),
        "g36_root": str(g36_root.resolve()),
        "g36_binding": {
            "source_id": G36_SOURCE_ID,
            "source_commit": G36_SOURCE_COMMIT,
            "branch": G36_BRANCH,
            "evaluation_manifest_digest": G36_EVALUATION_SHA256,
            "analysis_result_digest": G36_ANALYSIS_SHA256,
        },
        "g36_analysis": {
            "branch": g36_analysis["branch"],
            "operational_valid": g36_analysis["operational_valid"],
            "intervention_access_pass": g36_analysis["metrics"][
                "intervention_access_pass"
            ],
        },
        "donor_bank_active_counts": list(bank.supported_active_counts),
        "donor_bank_digest": _donor_bank_digest(bank),
        "cells": cells,
        "stage_wall_time_seconds": time.perf_counter() - started,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _evaluation_errors(
    run_root: Path,
    evaluation: Mapping[str, Any],
    *,
    g35_root: Path,
    g36_root: Path,
) -> list[str]:
    errors: list[str] = []
    for field, expected_root in (("g35_root", g35_root), ("g36_root", g36_root)):
        serialized = evaluation.get(field)
        if (
            not isinstance(serialized, str)
            or not serialized.strip()
            or not Path(serialized).is_absolute()
            or Path(serialized).resolve() != expected_root.resolve()
        ):
            return [f"G37 serialized {field} mismatch"]
    try:
        g36_evaluation, g36_analysis = _g36_reference(g36_root, g35_root)
        training, _, _ = g36_runner._g35_reference(g35_root)
    except (OSError, KeyError, TypeError, ValueError) as error:
        return [str(error)]
    formal_value = evaluation.get("formal")
    if not isinstance(formal_value, bool):
        return ["G37 evaluation formal flag mismatch"]
    formal = formal_value
    configuration = _configuration(formal=formal)
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("configuration") != configuration
        or re.fullmatch(r"[0-9a-f]{40}", str(evaluation.get("source_commit", "")))
        is None
    ):
        return ["G37 evaluation identity mismatch"]
    expected_binding = {
        "source_id": G36_SOURCE_ID,
        "source_commit": G36_SOURCE_COMMIT,
        "branch": G36_BRANCH,
        "evaluation_manifest_digest": G36_EVALUATION_SHA256,
        "analysis_result_digest": G36_ANALYSIS_SHA256,
    }
    expected_analysis = {
        "branch": g36_analysis["branch"],
        "operational_valid": g36_analysis["operational_valid"],
        "intervention_access_pass": g36_analysis["metrics"][
            "intervention_access_pass"
        ],
    }
    if (
        evaluation.get("g36_binding") != expected_binding
        or evaluation.get("g36_analysis") != expected_analysis
        or evaluation.get("runtime") != _runtime_identity()
    ):
        return ["G37 G36 binding/runtime mismatch"]
    try:
        _nonnegative_finite_seconds(evaluation.get("stage_wall_time_seconds"))
    except ValueError as error:
        errors.append(str(error))
    if formal:
        serialized_preflight = evaluation.get("preflight_root")
        if (
            evaluation.get("authorization_token") != AUTHORIZATION_TOKEN
            or not isinstance(serialized_preflight, str)
            or not serialized_preflight.strip()
            or not Path(serialized_preflight).is_absolute()
        ):
            return ["G37 formal authority/preflight binding mismatch"]
        preflight_root = Path(serialized_preflight)
        expected_preflight = {
            "source_commit": evaluation.get("source_commit"),
            "evaluation_manifest_digest": _artifact_digest(
                preflight_root / "evaluation_manifest.json"
            ),
            "analysis_result_digest": _artifact_digest(
                preflight_root / "analysis_result.json"
            ),
        }
        if evaluation.get("preflight_binding") != expected_preflight:
            return ["G37 formal authority/preflight binding mismatch"]
        try:
            _validate_formal_preflight(
                preflight_root,
                source_commit=str(evaluation["source_commit"]),
                g35_root=g35_root,
                g36_root=g36_root,
            )
        except (OSError, KeyError, TypeError, ValueError) as error:
            return [f"G37 formal preflight invalid: {error}"]
    elif (
        evaluation.get("authorization_token") is not None
        or evaluation.get("preflight_root") is not None
        or evaluation.get("preflight_binding") is not None
    ):
        return ["G37 nonformal authority binding mismatch"]
    bank = g36.G36HistoryProxyDonorBank.build()
    if (
        evaluation.get("donor_bank_active_counts")
        != list(bank.supported_active_counts)
        or evaluation.get("donor_bank_digest") != _donor_bank_digest(bank)
    ):
        return ["G37 donor-bank identity mismatch"]
    expected_keys = {
        (replicate, capacity, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for name, _, _ in CELLS
    }
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(
        configuration["total_new_cells"]
    ):
        return ["G37 evaluation cell inventory mismatch"]
    joint_cells = {
        (int(row["replicate"]), int(row["capacity"]), str(row["cell"])): row
        for row in g36_evaluation["cells"]
    }
    observed: set[tuple[int, int, str]] = set()
    proxy_digests: dict[tuple[int, int, str], tuple[str, ...]] = {}
    action_digests: dict[tuple[int, int, str], str] = {}
    roster_traces: dict[tuple[int, int, str], tuple[tuple[int, ...], ...]] = {}
    for cell in cells:
        try:
            key = (int(cell["replicate"]), int(cell["capacity"]), str(cell["cell"]))
            expected = next(row for row in CELLS if row[0] == key[2])
            if (
                key in observed
                or key not in expected_keys
                or cell.get("arm") != g35.CS_ARM
                or cell.get("process") != expected[1]
                or cell.get("deterministic") is not expected[2]
                or cell.get("checkpoint") != "final"
                or cell.get("optimizer_steps") != 0
                or cell.get("state_before") != cell.get("state_after")
            ):
                raise ValueError("G37 cell route/checkpoint mismatch")
            model, digest = g36_runner._load_cs_checkpoint(
                g35_root, training, replicate=key[0], capacity=key[1]
            )
            del model
            if cell.get("checkpoint_digest") != digest or cell.get("state_before") != digest:
                raise ValueError("G37 checkpoint binding mismatch")
            audit = cell["audit"]
            if (
                any(
                    audit.get(name) != 0
                    for name in (
                        "actual_age_read_count",
                        "actual_previous_action_read_count",
                        "actual_actor_time_read_count",
                        "critic_transform_count",
                        "proxy_tape_target_history_read_count",
                        "checkpoint_update_count",
                    )
                )
                or audit.get("lifecycle_valid") is not True
            ):
                raise ValueError("G37 actor-only/history audit mismatch")
            episodes = cell["episodes"]
            if not isinstance(episodes, list) or len(episodes) != int(
                configuration["evaluation_episodes_per_cell"]
            ):
                raise ValueError("G37 episode inventory mismatch")
            episode_proxy = audit.get("proxy_tape_episode_digests")
            action_digest = audit.get("action_noise_digest")
            if (
                not isinstance(episode_proxy, list)
                or len(episode_proxy) != len(episodes)
                or any(
                    re.fullmatch(r"[0-9a-f]{64}", str(value)) is None
                    for value in episode_proxy
                )
                or re.fullmatch(r"[0-9a-f]{64}", str(action_digest)) is None
            ):
                raise ValueError("G37 factorized/action digest inventory mismatch")
            processes = g35.make_process_ledgers(
                replicate=key[0],
                capacity=key[1],
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=True,
            )
            traces: list[tuple[int, ...]] = []
            for index, episode in enumerate(episodes):
                process = processes[index]
                trace = g34_runner._trace_evidence(episode)
                expected_roster = (
                    process.expected_roster_sizes
                    if expected[1] == "random"
                    else process.base.expected_roster_sizes
                )
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != process.episode_id
                    or episode.get("profile") != process.profile.name
                    or episode.get("event_times") != list(process.event_times)
                    or episode.get("event_order") != list(process.event_order)
                    or episode.get("count_trajectory") != list(process.count_trajectory)
                    or episode.get("signature") != repr(process.signature)
                    or trace["roster_size_trace"] != tuple(expected_roster)
                    or episode.get("roster_sizes_valid") is not True
                    or not g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G37 trace evidence mismatch")
                traces.append(trace["roster_size_trace"])
            joint = joint_cells[(key[0], key[1], JOINT_CELL[key[2]])]
            expected_action_digest = _expected_action_noise_digest(
                replicate=key[0],
                capacity=key[1],
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
            )
            if action_digest != expected_action_digest:
                raise ValueError("G37 G36 action-noise pairing mismatch")
            if (
                int(configuration["evaluation_episodes_per_cell"])
                == FORMAL_EPISODES
                and action_digest != joint["audit"]["action_noise_digest"]
            ):
                raise ValueError("G37 formal G36 action-noise digest mismatch")
            proxy_digests[key] = tuple(str(value) for value in episode_proxy)
            action_digests[key] = str(action_digest)
            roster_traces[key] = tuple(traces)
            observed.add(key)
        except (KeyError, StopIteration, TypeError, ValueError) as error:
            errors.append(str(error))
    if observed != expected_keys:
        errors.append("G37 evaluation cell key set mismatch")
    if not errors:
        for replicate in range(int(configuration["replicates"])):
            for capacity in g34.CAPACITIES:
                fixed_det = (replicate, capacity, "CS_FACTORIZED_FIXED_DET")
                fixed_stoch = (replicate, capacity, "CS_FACTORIZED_FIXED_STOCH")
                random_det = (replicate, capacity, "CS_FACTORIZED_RANDOM_DET")
                random_stoch = (replicate, capacity, "CS_FACTORIZED_RANDOM_STOCH")
                keys = (fixed_det, fixed_stoch, random_det, random_stoch)
                if (
                    proxy_digests[fixed_det] != proxy_digests[fixed_stoch]
                    or proxy_digests[random_det] != proxy_digests[random_stoch]
                    or len({action_digests[key] for key in keys}) != 1
                ):
                    errors.append("G37 paired factorized/action reuse mismatch")
                    continue
                for index, (fixed_trace, random_trace) in enumerate(
                    zip(roster_traces[fixed_det], roster_traces[random_det])
                ):
                    if (
                        fixed_trace == random_trace
                        and proxy_digests[fixed_det][index]
                        != proxy_digests[random_det][index]
                    ):
                        errors.append("G37 fixed/random factorized tape reuse mismatch")
                        break
    return errors


def analyze(
    *,
    run_root: Path,
    g35_root: Path,
    g36_root: Path,
    require_formal: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(evaluation.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G37 analysis requires formal artifacts")
    configure_runtime(
        BOOTSTRAP_SEED + (0 if formal else source.NONFORMAL_SEED_OFFSET)
    )
    errors = _evaluation_errors(
        run_root, evaluation, g35_root=g35_root, g36_root=g36_root
    )
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        g36_evaluation, _ = _g36_reference(g36_root, g35_root)
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        metrics.update(
            {
                "source_valid": True,
                "g36_reference_valid": True,
                **_access_and_noninferiority(g36_evaluation, evaluation, plan),
            }
        )
    analysis_seconds = time.perf_counter() - started
    evaluation_seconds = float(
        evaluation.get("stage_wall_time_seconds", float("nan"))
    )
    projection = (
        1.25 * (48.0 * evaluation_seconds + 40.0 * analysis_seconds)
        if not formal and not errors
        else None
    )
    executable = bool(
        projection is not None
        and np.isfinite(projection)
        and projection <= FORMAL_WALL_CLOCK_CAP_SECONDS
        and evaluation_seconds + analysis_seconds
        <= NONFORMAL_WALL_CLOCK_CAP_SECONDS
    )
    branch = (
        INVALID_BRANCH
        if errors
        else (
            select_g37_result_branch(metrics)
            if formal
            else (NONFORMAL_BRANCH if executable else NON_EXECUTABLE_BRANCH)
        )
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": evaluation.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "evaluation_manifest_digest": _artifact_digest(
            run_root / "evaluation_manifest.json"
        ),
        "stage_wall_time_seconds": analysis_seconds,
        "formal_projection_seconds": projection,
        "formal_projection_executable": executable,
        "formal_wall_clock_cap_seconds": FORMAL_WALL_CLOCK_CAP_SECONDS,
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(
    *,
    run_root: Path,
    g35_root: Path,
    g36_root: Path,
    source_commit: str,
) -> dict[str, Any]:
    evaluate(
        run_root=run_root,
        g35_root=g35_root,
        g36_root=g36_root,
        source_commit=source_commit,
        formal=False,
    )
    return analyze(run_root=run_root, g35_root=g35_root, g36_root=g36_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--g35-root", type=Path, required=True)
    parser.add_argument("--g36-root", type=Path, required=True)
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--require-formal", action="store_true")
    args = parser.parse_args()
    if args.mode == "evaluate":
        value = evaluate(
            run_root=args.run_root,
            g35_root=args.g35_root,
            g36_root=args.g36_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            preflight_root=args.preflight_root,
        )
    elif args.mode == "analyze":
        value = analyze(
            run_root=args.run_root,
            g35_root=args.g35_root,
            g36_root=args.g36_root,
            require_formal=args.require_formal,
        )
    else:
        value = exercise(
            run_root=args.run_root,
            g35_root=args.g35_root,
            g36_root=args.g36_root,
            source_commit=args.source_commit,
        )
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

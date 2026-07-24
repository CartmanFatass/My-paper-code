"""Run the bounded dual-source G18 fast/slow credit screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.separated_credit_g18 import (
    SeparatedCreditPolicy,
    attach_credit_baselines,
    collect_battery_trajectory,
    evaluate_battery_policy,
    optimize_separated_update,
)
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = "ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18"
GAMMA = 0.99
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
PPO_PASSES = 2
NUM_ENVS = 8
G17_UPDATES = 100
G18_UPDATES = 300
G17_EVAL_EPISODES = 48

SEEDS = {
    "g17": {
        "model": 2_018_000,
        "ledger": 2_028_000,
        "action": 2_038_000,
        "evaluation_ledger": 2_048_000,
        "evaluation_action": 2_058_000,
    },
    "g18": {
        "model": 2_118_000,
        "action": 2_138_000,
    },
}

REPLAY_TOLERANCE = 1e-6
G17_UTILITY_FLOOR = 0.90
G17_GAIN_FLOOR = 0.10
G17_MINIMUM_EPISODE_FLOOR = 0.80
G17_CORRELATION_FLOOR = 0.90
G17_MAE_CEILING = 0.05
G18_UTILITY_FLOOR = 0.95
G18_GAIN_FLOOR = 0.10
G18_SPIKE_UTILITY_FLOOR = 0.90
G18_ROTATING_EFFORT_SHARE_FLOOR = 0.75

INVALID_BRANCH = "INVALID_ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18"
NO_G17_BRANCH = "NONFORMAL_NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18"
NO_G18_ACCESS_BRANCH = "NONFORMAL_NO_DELAYED_ACCESS_CRITIC_ISOLATED_G18"
NO_G18_MECHANISM_BRANCH = "NONFORMAL_NO_DELAYED_MECHANISM_CRITIC_ISOLATED_G18"
PROMISING_BRANCH = "NONFORMAL_ACTOR_CRITIC_ISOLATED_CREDIT_PROMISING_G18"


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


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _source_dimensions(source: str) -> tuple[int, int, int, int]:
    if source == "g17":
        return (
            g17_source.OBSERVATION_DIM,
            g17_source.CRITIC_STATE_DIM,
            g17_source.CAPACITY,
            g17_source.ACTION_DIM,
        )
    if source == "g18":
        return (
            battery_source.OBSERVATION_DIM,
            battery_source.CRITIC_STATE_DIM,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        )
    raise ValueError(f"unknown separated-credit source: {source}")


def make_model(source: str) -> SeparatedCreditPolicy:
    observation_dim, critic_state_dim, capacity, action_dim = _source_dimensions(
        source
    )
    model = SeparatedCreditPolicy(
        observation_dim,
        critic_state_dim,
        member_capacity=capacity,
        action_dim=action_dim,
        hidden_dim=HIDDEN_DIM,
        current_observation_residual=True,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def _copy_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }


def _maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(left[name] - right[name])).item())
        for name in left
    )


def _save_checkpoint(
    path: Path,
    *,
    source: str,
    source_commit: str,
    completed_updates: int,
    model: SeparatedCreditPolicy,
) -> None:
    torch.save(
        {
            "schema_version": SCHEMA_VERSION,
            "algorithm": ALGORITHM_ID,
            "formal": False,
            "source": source,
            "source_commit": source_commit,
            "completed_updates": int(completed_updates),
            "configuration": _configuration(),
            "model_state": model.state_dict(),
        },
        path,
    )


def _load_checkpoint(
    path: Path,
    *,
    source: str,
    source_commit: str,
    completed_updates: int,
) -> SeparatedCreditPolicy:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    expected = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "formal": False,
        "source": source,
        "source_commit": source_commit,
        "completed_updates": int(completed_updates),
        "configuration": _configuration(),
    }
    if not isinstance(payload, dict):
        raise ValueError("G18 separated-credit checkpoint is not a dictionary")
    for name, value in expected.items():
        if payload.get(name) != value:
            raise ValueError(f"G18 separated-credit checkpoint {name} mismatch")
    g17_runner.configure_runtime(SEEDS[source]["model"])
    model = make_model(source)
    model.load_state_dict(payload["model_state"])
    return model


def _configuration() -> dict[str, Any]:
    return {
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        "ppo_passes": PPO_PASSES,
        "num_envs": NUM_ENVS,
        "g17_updates": G17_UPDATES,
        "g18_updates": G18_UPDATES,
        "g17_eval_episodes": G17_EVAL_EPISODES,
        "current_observation_residual": True,
        "successor_weight": 1.0,
        "actor_channel_combination": "independent_normalization_equal_weight",
        "slow_critic": "state_only_actor_gradient_isolated",
    }


def _collect_trajectory(
    source: str,
    model: SeparatedCreditPolicy,
    *,
    episode_ids: tuple[int, ...],
) -> Any:
    if source == "g17":
        raw = g17_source.collect_trajectory(
            model,
            episode_ids=episode_ids,
            ledger_seed=SEEDS[source]["ledger"],
            action_seed=SEEDS[source]["action"],
            device=torch.device("cpu"),
            profiles=g17_source.TRAIN_PROFILES,
        )
        return attach_credit_baselines(
            model, raw, device=torch.device("cpu")
        )
    return collect_battery_trajectory(
        model,
        episode_ids=episode_ids,
        action_seed=SEEDS[source]["action"],
        device=torch.device("cpu"),
    )


def _trajectory_contract_valid(source: str, trajectory: Any) -> bool:
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    if int(torch.count_nonzero(inactive_actions)) != 0:
        return False
    if not all(
        bool(torch.isfinite(row).all())
        for row in (
            trajectory.observations,
            trajectory.critic_states,
            trajectory.actions,
            trajectory.pre_tanh_actions,
            trajectory.old_log_probs,
            trajectory.old_values,
            trajectory.old_immediate_baselines,
            trajectory.old_successor_baselines,
            trajectory.rewards,
        )
    ):
        return False
    for ledger, outcome in zip(trajectory.ledgers, trajectory.outcomes):
        if source == "g17":
            if outcome.roster_sizes != ledger.expected_roster_sizes:
                return False
        elif outcome.roster_sizes != (
            4,
            4,
            4,
            4,
            4,
            4,
            2,
            2,
            2,
            2,
            4,
            4,
        ):
            return False
    return True


def _train_source(
    *,
    run_root: Path,
    source: str,
    source_commit: str,
    updates: int,
) -> dict[str, Any]:
    g17_runner.configure_runtime(SEEDS[source]["model"])
    model = make_model(source)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    zero_state = _copy_state(model)
    checkpoint_root = run_root / "checkpoints"
    zero_path = checkpoint_root / f"{source}_zero.pt"
    final_path = checkpoint_root / f"{source}_final.pt"
    _save_checkpoint(
        zero_path,
        source=source,
        source_commit=source_commit,
        completed_updates=0,
        model=model,
    )
    maximum_errors: dict[str, float] = {}
    finite = True
    lifecycle_valid = True
    active_rows = 0
    for update in range(int(updates)):
        first_episode = update * NUM_ENVS
        episode_ids = tuple(range(first_episode, first_episode + NUM_ENVS))
        trajectory = _collect_trajectory(
            source, model, episode_ids=episode_ids
        )
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(
            source, trajectory
        )
        metrics = optimize_separated_update(
            model,
            optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=PPO_PASSES,
            gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_errors[name] = max(
                    maximum_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count
        _write_json(
            run_root / "progress.json",
            {
                "phase": "train",
                "source": source,
                "update": update + 1,
                "updates": int(updates),
            },
        )
    _save_checkpoint(
        final_path,
        source=source,
        source_commit=source_commit,
        completed_updates=updates,
        model=model,
    )
    return {
        "source": source,
        "updates": int(updates),
        "environment_steps": int(
            updates
            * NUM_ENVS
            * (g17_source.HORIZON if source == "g17" else battery_source.HORIZON)
        ),
        "optimizer_steps": int(updates * PPO_PASSES),
        "active_rows": int(active_rows),
        "zero_checkpoint": str(zero_path.relative_to(run_root)),
        "final_checkpoint": str(final_path.relative_to(run_root)),
        "maximum_replay_errors": maximum_errors,
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "finite_updates": bool(finite),
        "parameter_drift": _maximum_state_difference(
            zero_state, _copy_state(model)
        ),
        "parameter_count": model.parameter_count,
        "seeds": SEEDS[source],
    }


def train(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G18 screen requires an integrated source commit")
    run_root.mkdir(parents=True, exist_ok=False)
    (run_root / "checkpoints").mkdir()
    g17_runner.configure_runtime(SEEDS["g17"]["model"])
    started = time.perf_counter()
    rows = [
        _train_source(
            run_root=run_root,
            source="g17",
            source_commit=source_commit,
            updates=G17_UPDATES,
        ),
        _train_source(
            run_root=run_root,
            source="g18",
            source_commit=source_commit,
            updates=G18_UPDATES,
        ),
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": False,
        "source_commit": source_commit,
        "runtime": _runtime_identity(),
        "configuration": _configuration(),
        "source_results": rows,
        "wall_seconds": float(time.perf_counter() - started),
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _g17_cell(model: SeparatedCreditPolicy, *, domain: str) -> dict[str, Any]:
    profiles = (
        g17_source.TRAIN_PROFILES
        if domain == "iid"
        else g17_source.HELDOUT_PROFILES
    )
    outcomes = g17_source.evaluate_policy(
        model,
        episode_ids=range(G17_EVAL_EPISODES),
        ledger_seed=SEEDS["g17"]["evaluation_ledger"],
        action_seed=SEEDS["g17"]["evaluation_action"],
        device=torch.device("cpu"),
        profiles=profiles,
        deterministic=True,
    )
    utilities = [float(outcome.utility) for outcome in outcomes]
    return {
        "domain": domain,
        "utility": utilities,
        "utility_mean": float(np.mean(utilities)),
        "minimum_episode": float(np.min(utilities)),
    }


def evaluate(*, run_root: Path) -> dict[str, Any]:
    training = _read_json(run_root / "train_manifest.json")
    if (
        training.get("algorithm") != ALGORITHM_ID
        or training.get("status") != "COMPLETE"
        or training.get("formal") is not False
    ):
        raise ValueError("G18 evaluation requires complete nonformal training")
    source_commit = str(training["source_commit"])
    by_source = {row["source"]: row for row in training["source_results"]}
    cells: list[dict[str, Any]] = []
    for checkpoint_kind in ("zero", "final"):
        row = by_source["g17"]
        model = _load_checkpoint(
            run_root / row[f"{checkpoint_kind}_checkpoint"],
            source="g17",
            source_commit=source_commit,
            completed_updates=(0 if checkpoint_kind == "zero" else G17_UPDATES),
        )
        for domain in ("iid", "heldout"):
            cells.append(
                {
                    "source": "g17",
                    "checkpoint": checkpoint_kind,
                    **_g17_cell(model, domain=domain),
                }
            )
        if checkpoint_kind == "final":
            cells.append(
                {
                    "source": "g17",
                    "checkpoint": "final",
                    "domain": "mapping",
                    **g17_runner._mapping_diagnostic(
                        model,
                        episode_ids=tuple(range(G17_EVAL_EPISODES)),
                        ledger_seed=SEEDS["g17"]["evaluation_ledger"],
                    ),
                }
            )

    for checkpoint_kind in ("zero", "final"):
        row = by_source["g18"]
        model = _load_checkpoint(
            run_root / row[f"{checkpoint_kind}_checkpoint"],
            source="g18",
            source_commit=source_commit,
            completed_updates=(0 if checkpoint_kind == "zero" else G18_UPDATES),
        )
        cells.append(
            {
                "source": "g18",
                "checkpoint": checkpoint_kind,
                "slot_rows": evaluate_battery_policy(
                    model, device=torch.device("cpu")
                ),
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": False,
        "source_commit": source_commit,
        "runtime": _runtime_identity(),
        "source_controls": {
            "g17": g17_runner._source_controls(),
            "g18": battery_source.run_information_gate(),
        },
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def select_result_branch(metrics: dict[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    g17_ok = (
        float(metrics["g17_iid_mean"]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_heldout_mean"]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_gain_mean"]) >= G17_GAIN_FLOOR
        and float(metrics["g17_minimum_episode"])
        >= G17_MINIMUM_EPISODE_FLOOR
        and float(metrics["g17_effort_correlation"])
        >= G17_CORRELATION_FLOOR
        and float(metrics["g17_mix_correlation"]) >= G17_CORRELATION_FLOOR
        and float(metrics["g17_effort_mae"]) <= G17_MAE_CEILING
        and float(metrics["g17_mix_mae"]) <= G17_MAE_CEILING
    )
    if not g17_ok:
        return NO_G17_BRANCH
    g18_access = (
        float(metrics["g18_utility_mean"]) >= G18_UTILITY_FLOOR
        and float(metrics["g18_minimum_slot_utility"]) >= G18_UTILITY_FLOOR
        and float(metrics["g18_gain_mean"]) >= G18_GAIN_FLOOR
        and float(metrics["g18_minimum_spike_utility"])
        >= G18_SPIKE_UTILITY_FLOOR
    )
    if not g18_access:
        return NO_G18_ACCESS_BRANCH
    if (
        float(metrics["g18_minimum_rotating_effort_share"])
        < G18_ROTATING_EFFORT_SHARE_FLOOR
    ):
        return NO_G18_MECHANISM_BRANCH
    return PROMISING_BRANCH


def _only_cell(cells: list[dict[str, Any]], **criteria: str) -> dict[str, Any]:
    matches = [
        row
        for row in cells
        if all(row.get(name) == value for name, value in criteria.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"G18 cell inventory mismatch: {criteria}")
    return matches[0]


def analyze(
    *, run_root: Path, require_formal: bool = False
) -> dict[str, Any]:
    if require_formal:
        raise ValueError("formal analysis requires formal artifacts")
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    errors: list[str] = []
    for artifact in (training, evaluation):
        if artifact.get("algorithm") != ALGORITHM_ID:
            errors.append("algorithm mismatch")
        if artifact.get("status") != "COMPLETE":
            errors.append("artifact incomplete")
        if artifact.get("formal") is not False:
            errors.append("screen artifacts must be nonformal")
        if artifact.get("source_commit") != training.get("source_commit"):
            errors.append("source commit mismatch")
        runtime = artifact.get("runtime", {})
        if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
            errors.append("runtime identity mismatch")
    if training.get("configuration") != _configuration():
        errors.append("configuration mismatch")
    rows = training.get("source_results", [])
    if {row.get("source") for row in rows} != {"g17", "g18"}:
        errors.append("training source inventory mismatch")
    for row in rows:
        if not bool(row.get("finite_updates")):
            errors.append(f"{row.get('source')} non-finite update")
        if not bool(row.get("lifecycle_contract_valid")):
            errors.append(f"{row.get('source')} lifecycle contract invalid")
        if float(row.get("parameter_drift", 0.0)) <= 0.0:
            errors.append(f"{row.get('source')} parameter did not move")
        replay_values = row.get("maximum_replay_errors", {}).values()
        if not replay_values or max(float(value) for value in replay_values) > REPLAY_TOLERANCE:
            errors.append(f"{row.get('source')} replay mismatch")
    controls = evaluation.get("source_controls", {})
    if not bool(controls.get("g17", {}).get("constructive_access_valid")):
        errors.append("G17 source access control failed")
    if controls.get("g18", {}).get("branch") != battery_source.PASS_BRANCH:
        errors.append("G18 information gate control failed")

    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        cells = evaluation["cells"]
        g17_iid = _only_cell(
            cells, source="g17", checkpoint="final", domain="iid"
        )
        g17_heldout = _only_cell(
            cells, source="g17", checkpoint="final", domain="heldout"
        )
        g17_zero = _only_cell(
            cells, source="g17", checkpoint="zero", domain="heldout"
        )
        mapping = _only_cell(
            cells, source="g17", checkpoint="final", domain="mapping"
        )
        g18_final = _only_cell(cells, source="g18", checkpoint="final")
        g18_zero = _only_cell(cells, source="g18", checkpoint="zero")
        final_slot_rows = g18_final["slot_rows"]
        zero_slot_rows = g18_zero["slot_rows"]
        final_utilities = np.asarray(
            [row["utility"] for row in final_slot_rows], dtype=np.float64
        )
        zero_utilities = np.asarray(
            [row["utility"] for row in zero_slot_rows], dtype=np.float64
        )
        expected_roster = [4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 4, 4]
        if len(final_slot_rows) != len(battery_source.GATE_SLOT_ORDERS):
            errors.append("G18 slot inventory mismatch")
        if not all(
            bool(row["inactive_action_zero"])
            and row["roster_sizes"] == expected_roster
            for row in final_slot_rows
        ):
            errors.append("G18 evaluation lifecycle contract invalid")
        metrics.update(
            {
                "g17_iid_mean": float(g17_iid["utility_mean"]),
                "g17_heldout_mean": float(g17_heldout["utility_mean"]),
                "g17_gain_mean": float(
                    g17_heldout["utility_mean"] - g17_zero["utility_mean"]
                ),
                "g17_minimum_episode": min(
                    float(g17_iid["minimum_episode"]),
                    float(g17_heldout["minimum_episode"]),
                ),
                "g17_effort_correlation": float(mapping["effort_correlation"]),
                "g17_mix_correlation": float(mapping["mix_correlation"]),
                "g17_effort_mae": float(mapping["effort_mae"]),
                "g17_mix_mae": float(mapping["mix_mae"]),
                "g18_utility_mean": float(final_utilities.mean()),
                "g18_minimum_slot_utility": float(final_utilities.min()),
                "g18_gain_mean": float(
                    (final_utilities - zero_utilities).mean()
                ),
                "g18_minimum_spike_utility": min(
                    float(row["spike_utility"]) for row in final_slot_rows
                ),
                "g18_minimum_rotating_effort_share": min(
                    float(row["low_rotating_effort_share"])
                    for row in final_slot_rows
                ),
                "maximum_replay_error": max(
                    float(value)
                    for row in rows
                    for value in row["maximum_replay_errors"].values()
                ),
                "operational_valid": not errors,
            }
        )
    branch = select_result_branch(metrics)
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": False,
        "source_commit": training.get("source_commit"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "thresholds": {
            "g17_utility_floor": G17_UTILITY_FLOOR,
            "g17_gain_floor": G17_GAIN_FLOOR,
            "g17_minimum_episode_floor": G17_MINIMUM_EPISODE_FLOOR,
            "g17_correlation_floor": G17_CORRELATION_FLOOR,
            "g17_mae_ceiling": G17_MAE_CEILING,
            "g18_utility_floor": G18_UTILITY_FLOOR,
            "g18_gain_floor": G18_GAIN_FLOOR,
            "g18_spike_utility_floor": G18_SPIKE_UTILITY_FLOOR,
            "g18_rotating_effort_share_floor": G18_ROTATING_EFFORT_SHARE_FLOOR,
            "replay_tolerance": REPLAY_TOLERANCE,
        },
        "interpretation": (
            "bounded dual-source screen only; not formal or UAV evidence"
        ),
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "analyze"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    arguments = parser.parse_args()
    if arguments.mode == "train":
        value = train(
            run_root=arguments.run_root,
            source_commit=str(arguments.source_commit or ""),
        )
    elif arguments.mode == "evaluate":
        value = evaluate(run_root=arguments.run_root)
    else:
        value = analyze(run_root=arguments.run_root)
    print(
        json.dumps(
            {
                "algorithm": value["algorithm"],
                "stage": value["stage"],
                "status": value["status"],
                "formal": value["formal"],
                "run_root": str(arguments.run_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

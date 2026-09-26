"""B11 zero-fit crossing of frozen B09 whole tables and external laws."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from time import perf_counter
from typing import Any

import numpy as np

from experiments.candidates.skill_teammate_drift_learning.fixed_radial_b10 import (
    study as b10,
)
from experiments.candidates.skill_teammate_drift_learning.native_joint_b09 import (
    study as b09,
)


LAW_NAMES = ("source", "target")
TABLE_NAMES = ("source", "target")
CELLS = tuple(
    (law_id, table_id, f"{LAW_NAMES[law_id]}_law_{TABLE_NAMES[table_id]}_table")
    for law_id in range(2)
    for table_id in range(2)
)
STREAM = 3
PHASE = 3

EXPOSURE_KEYS = b09.EXPOSURE_KEYS


@dataclass(frozen=True)
class Config:
    episodes: int = 16
    steps: int = 64
    n_uavs: int = 3
    n_users: int = 1
    area_size: float = 1000.0
    height_range: tuple[float, float] = (50.0, 150.0)
    max_speed: float = 30.0
    time_step: float = 1.0
    min_sinr: float = 0.0
    max_connections: int = 10
    stream: int = STREAM
    phase: int = PHASE


PRODUCTION_CONFIG = Config()
TINY_CONFIG = Config(episodes=1, steps=2)


def validate_config(config: Config) -> None:
    if config not in (PRODUCTION_CONFIG, TINY_CONFIG):
        raise ValueError("B11 permits only its frozen production or declared tiny config")


def load_frozen_state(
    input_root: Any,
    seed: int,
    *,
    expected_root_artifacts_sha256: str,
) -> dict[str, Any]:
    """Use the sealed B10 loader, including its inherited marginal construction."""
    return b10.load_frozen_state(
        input_root,
        seed,
        expected_root_artifacts_sha256=expected_root_artifacts_sha256,
    )


def _stack(records: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    if not records:
        raise ValueError("cannot stack empty B11 records")
    keys = set(records[0])
    if any(set(record) != keys for record in records):
        raise RuntimeError("B11 record schemas differ")
    return {key: np.asarray([record[key] for record in records]) for key in records[0]}


def _cell_label(law_id: int, table_id: int) -> str:
    return f"{LAW_NAMES[law_id]}_law_{TABLE_NAMES[table_id]}_table"


def _sample_sd(values: np.ndarray) -> float | None:
    if values.size < 2:
        return None
    return float(np.std(values, ddof=1))


def _contrast(values: np.ndarray) -> dict[str, Any]:
    return {
        "paired_world_adapter_returns": values.tolist(),
        "base_mean_adapter_return": float(np.mean(values)),
        "paired_world_team_returns": (3.0 * values).tolist(),
        "base_mean_team_return": float(3.0 * np.mean(values)),
        "paired_world_sample_standard_deviation": _sample_sd(values),
    }


def reduce_episode_returns(
    trajectories: dict[str, np.ndarray], config: Config
) -> dict[str, Any]:
    returns: dict[str, list[float]] = {}
    team_returns: dict[str, list[float]] = {}
    for law_id, table_id, label in CELLS:
        adapter_values = []
        team_values = []
        for episode in range(config.episodes):
            rows = (
                (trajectories["law_id"] == law_id)
                & (trajectories["table_id"] == table_id)
                & (trajectories["episode"] == episode)
            )
            if int(rows.sum()) != config.steps:
                raise RuntimeError("incomplete law/table episode in B11 trajectory")
            adapter_values.append(float(trajectories["adapter_reward"][rows].sum()))
            team_values.append(float(trajectories["team_reward"][rows].sum()))
        returns[label] = adapter_values
        team_returns[label] = team_values

    arrays = {key: np.asarray(value, dtype=np.float64) for key, value in returns.items()}
    d_source = arrays[_cell_label(0, 0)] - arrays[_cell_label(0, 1)]
    d_target = arrays[_cell_label(1, 1)] - arrays[_cell_label(1, 0)]
    interaction = d_source + d_target
    paired_worlds = [
        {
            "episode": episode,
            **{label: float(arrays[label][episode]) for _, _, label in CELLS},
            "D_source": float(d_source[episode]),
            "D_target": float(d_target[episode]),
            "interaction_sum": float(interaction[episode]),
        }
        for episode in range(config.episodes)
    ]
    return {
        "episode_adapter_returns": returns,
        "episode_team_returns": team_returns,
        "base_mean_adapter_returns": {
            label: float(np.mean(value)) for label, value in arrays.items()
        },
        "paired_worlds": paired_worlds,
        "contrasts": {
            "D_source": _contrast(d_source),
            "D_target": _contrast(d_target),
            "interaction_sum": _contrast(interaction),
        },
        "interaction_definition": "D_source + D_target (not one half of the sum)",
    }


def reduce_blocks(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if [int(block["seed"]) for block in blocks] != [95401, 95402, 95403]:
        raise ValueError("B11 root reduction requires fixed bases in order")
    contrast_names = ("D_source", "D_target", "interaction_sum")
    result: dict[str, Any] = {
        "primary": ["D_source", "D_target"],
        "secondary": "interaction_sum",
        "interaction_definition": "D_source + D_target (not one half of the sum)",
        "base_means": {},
        "paired_world_values_by_base": {},
        "per_base_paired_world_sample_standard_deviations": {},
        "equal_weight_three_base_means": {},
        "conditional_fixed_base_monte_carlo_standard_errors": {},
        "conditional_uncertainty_scope": "deployment worlds conditional on the three exposed frozen bases (six tables); excludes learning uncertainty",
        "no_threshold_confidence_interval_or_claim_rule": True,
        "cell_base_means": {},
        "cell_paired_world_returns_by_base": {},
        "equal_weight_three_base_cell_means": {},
    }
    for _, _, label in CELLS:
        cell_values = [
            list(block["reduction"]["episode_adapter_returns"][label])
            for block in blocks
        ]
        cell_base_means = [
            float(block["reduction"]["base_mean_adapter_returns"][label])
            for block in blocks
        ]
        result["cell_paired_world_returns_by_base"][label] = cell_values
        result["cell_base_means"][label] = cell_base_means
        result["equal_weight_three_base_cell_means"][label] = float(
            np.mean(cell_base_means)
        )
    for name in contrast_names:
        paired = [
            list(block["reduction"]["contrasts"][name]["paired_world_adapter_returns"])
            for block in blocks
        ]
        if any(len(values) != 16 for values in paired):
            raise ValueError("B11 production reduction requires 16 paired worlds per base")
        base_means = [
            float(block["reduction"]["contrasts"][name]["base_mean_adapter_return"])
            for block in blocks
        ]
        sample_sds = [
            float(
                block["reduction"]["contrasts"][name][
                    "paired_world_sample_standard_deviation"
                ]
            )
            for block in blocks
        ]
        result["base_means"][name] = base_means
        result["paired_world_values_by_base"][name] = paired
        result["per_base_paired_world_sample_standard_deviations"][name] = sample_sds
        result["equal_weight_three_base_means"][name] = float(np.mean(base_means))
        result["conditional_fixed_base_monte_carlo_standard_errors"][name] = sqrt(
            sum(sd * sd / 16.0 for sd in sample_sds) / 9.0
        )
    return result


def _cell_diagnostics(
    trajectories: dict[str, np.ndarray], law_id: int, table_id: int
) -> dict[str, Any]:
    rows = (trajectories["law_id"] == law_id) & (
        trajectories["table_id"] == table_id
    )
    positions = trajectories["after_positions"][rows]
    radii = np.linalg.norm(positions[:, :, :2] - b09.USER_POSITION, axis=2)
    connections = trajectories["after_connections"][rows]
    components = trajectories["reward_components"][rows]
    return {
        "actual_ticks": int(rows.sum()),
        "served_ticks": int(np.any(connections, axis=(1, 2)).sum()),
        "unserved_ticks": int((~np.any(connections, axis=(1, 2))).sum()),
        "service_owner_tick_counts": connections.sum(axis=(0, 2)).astype(int).tolist(),
        "coverage_component_sum": float(components[:, 0].sum()),
        "quality_component_sum": float(components[:, 1].sum()),
        "energy_component_sum": float(components[:, 2].sum()),
        "minimum_radius_by_agent": radii.min(axis=0).tolist(),
        "maximum_radius_by_agent": radii.max(axis=0).tolist(),
    }


def _occupancy_regret_diagnostics(
    planning: dict[str, np.ndarray], law_id: int, actual_table_id: int
) -> dict[str, Any]:
    rows = (planning["law_id"] == law_id) & (
        planning["actual_table_id"] == actual_table_id
    )
    choices = planning["candidate_choices"][rows]
    regrets = planning["candidate_true_regrets_after_choice"][rows]
    matched = law_id
    mismatched = 1 - law_id
    deltas = regrets[:, mismatched] - regrets[:, matched]
    disagreements = choices[:, 0] != choices[:, 1]
    return {
        "law_id": law_id,
        "actual_table_id": actual_table_id,
        "states": int(rows.sum()),
        "same_state_mismatched_minus_matched_regrets": deltas.tolist(),
        "mean_same_state_mismatched_minus_matched_regret": float(np.mean(deltas)),
        "candidate_disagreements": int(disagreements.sum()),
        "disagreement_mismatched_minus_matched_regrets": deltas[disagreements].tolist(),
        "matched_better_count": int((deltas > 0.0).sum()),
        "matched_equal_count": int((deltas == 0.0).sum()),
        "matched_worse_count": int((deltas < 0.0).sum()),
        "matched_better_on_disagreement_count": int(
            ((deltas > 0.0) & disagreements).sum()
        ),
        "matched_equal_on_disagreement_count": int(
            ((deltas == 0.0) & disagreements).sum()
        ),
        "matched_worse_on_disagreement_count": int(
            ((deltas < 0.0) & disagreements).sum()
        ),
    }


def _validate_pairing(
    trajectories: dict[str, np.ndarray],
    planning: dict[str, np.ndarray],
    config: Config,
) -> dict[str, int]:
    for episode in range(config.episodes):
        initial = (trajectories["episode"] == episode) & (
            trajectories["tick"] == 0
        )
        if int(initial.sum()) != 4 or not np.array_equal(
            trajectories["pre_positions"][initial],
            np.repeat(trajectories["pre_positions"][initial][0:1], 4, axis=0),
        ):
            raise RuntimeError("B11 cells do not share their declared initial geometry")
        for table_id in range(2):
            rows = (
                (planning["episode"] == episode)
                & (planning["tick"] == 0)
                & (planning["actual_table_id"] == table_id)
            )
            if int(rows.sum()) != 2 or not np.array_equal(
                planning["candidate_choices"][rows][0],
                planning["candidate_choices"][rows][1],
            ):
                raise RuntimeError(
                    "B11 first-state frozen-table choices depend on the external law"
                )
        for tick in range(config.steps):
            rows = (trajectories["episode"] == episode) & (
                trajectories["tick"] == tick
            )
            if (
                int(rows.sum()) != 4
                or np.unique(trajectories["rng_address"][rows], axis=0).shape[0]
                != 1
                or np.unique(trajectories["external_uniform"][rows]).size != 1
            ):
                raise RuntimeError("B11 law/table cells do not share their RNG slot")
            for law_id in range(2):
                law_rows = rows & (trajectories["law_id"] == law_id)
                if (
                    int(law_rows.sum()) != 2
                    or np.unique(trajectories["joint_row"][law_rows]).size != 1
                    or not np.array_equal(
                        trajectories["after_positions"][law_rows][0, 1:],
                        trajectories["after_positions"][law_rows][1, 1:],
                    )
                ):
                    raise RuntimeError(
                        "B11 within-law teammate innovations or paths are not paired"
                    )
    return {
        "common_initial_geometries": config.episodes,
        "common_uniform_slots": config.episodes * config.steps,
        "within_law_paired_teammate_ticks": 2 * config.episodes * config.steps,
        "first_state_table_choice_cross_law_equalities": 2 * config.episodes,
    }


def run_evaluation(
    config: Config,
    rng_seed: int,
    frozen: dict[str, Any],
    *,
    exposure: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Run all four law/table cells without constructing or querying a learner."""
    validate_config(config)
    if int(frozen["seed"]) not in (95401, 95402, 95403):
        raise ValueError("frozen state must be one of the three B09 bases")
    if exposure is None:
        exposure = {key: 0 for key in EXPOSURE_KEYS}
    if set(exposure) != set(EXPOSURE_KEYS) or any(exposure.values()):
        raise ValueError("exposure must be a fresh complete B11 counter")

    probabilities = np.asarray(
        frozen["state"]["final_probabilities"], dtype=np.float64
    ).copy()
    if probabilities.shape != (2, 4):
        raise ValueError("B11 requires both B09 final probability rows")
    frozen_guard = {key: value.copy() for key, value in frozen["state"].items()}
    started = perf_counter()
    trajectory_records: list[dict[str, Any]] = []
    planner_records: list[dict[str, Any]] = []
    initializations = []

    for law_id, table_id, label in CELLS:
        for episode in range(config.episodes):
            adapter, observations, geometry_slots, environment_seed = b09._make_adapter(
                config,
                int(rng_seed),
                config.stream,
                config.phase,
                episode,
                config.steps,
                exposure,
            )
            initializations.append(
                {
                    "cell": label,
                    "law_id": law_id,
                    "table_id": table_id,
                    "episode": episode,
                    "environment_seed": environment_seed,
                    "geometry_slots": geometry_slots.tolist(),
                    "initial_positions": adapter.env.uav_positions.tolist(),
                }
            )
            for tick in range(config.steps):
                table = b09.response_table(adapter, exposure)
                scalar_table = table["adapter_reward"]
                candidate_values = np.stack(
                    (scalar_table @ probabilities[0], scalar_table @ probabilities[1])
                )
                candidate_choices = np.asarray(
                    [int(values[1] > values[0]) for values in candidate_values],
                    dtype=np.int8,
                )
                focal_bit = int(candidate_choices[table_id])

                # The true law is consulted only after both frozen-table choices are fixed.
                true_values = scalar_table @ b09.TRUE_Q[law_id]
                candidate_regrets = np.max(true_values) - true_values[candidate_choices]
                planner_index = len(planner_records)
                planner = {
                    "trajectory_index": len(trajectory_records),
                    "law_id": law_id,
                    "actual_table_id": table_id,
                    "episode": episode,
                    "tick": tick,
                    "source_probabilities": probabilities[0].copy(),
                    "target_probabilities": probabilities[1].copy(),
                    "candidate_values": candidate_values,
                    "candidate_choices": candidate_choices,
                    "selected_focal_bit": focal_bit,
                    "true_law_values_after_choices": true_values,
                    "candidate_true_chosen_values_after_choice": true_values[
                        candidate_choices
                    ],
                    "candidate_true_regrets_after_choice": candidate_regrets,
                    "actual_true_chosen_value_after_choice": float(true_values[focal_bit]),
                    "actual_true_regret_after_choice": float(
                        np.max(true_values) - true_values[focal_bit]
                    ),
                }
                planner.update(
                    {f"response_{key}": value for key, value in table.items()}
                )
                planner_records.append(planner)

                external_uniform = b09._slot(
                    int(rng_seed), 2, config.stream, config.phase, episode, tick
                )
                row = b09._sample_row(b09.TRUE_Q[law_id], external_uniform)
                teammate_bits = np.asarray([row // 2, row % 2], dtype=np.int8)
                command_bits = np.asarray(
                    [focal_bit, *teammate_bits], dtype=np.int8
                )
                pre_positions = adapter.env.uav_positions.copy()
                actions = b09.commands_from_bits(pre_positions, command_bits)
                decoded_bits, decoded_row = b09.decode_teammate_row(
                    pre_positions, actions
                )
                if decoded_row != row or not np.array_equal(
                    decoded_bits, teammate_bits
                ):
                    raise RuntimeError("issued B11 commands decode to a different row")
                physical, observations = b09._step_record(
                    adapter, observations, actions
                )
                b09._increment(exposure, "evaluation_native_step_calls")
                b10._selected_branch_matches(physical, table, focal_bit, row)
                trajectory_records.append(
                    {
                        **physical,
                        "stream": config.stream,
                        "phase": config.phase,
                        "law_id": law_id,
                        "table_id": table_id,
                        "episode": episode,
                        "tick": tick,
                        "rng_address": np.asarray(
                            [rng_seed, config.stream, config.phase, episode, tick],
                            dtype=np.int64,
                        ),
                        "environment_seed": environment_seed,
                        "geometry_slots": geometry_slots.copy(),
                        "external_uniform": external_uniform,
                        "focal_bit": focal_bit,
                        "teammate_bits": decoded_bits,
                        "joint_row": decoded_row,
                        "planner_record_index": planner_index,
                        "terminal_id": episode if physical["terminated"] else -1,
                    }
                )

    for key, before in frozen_guard.items():
        np.testing.assert_array_equal(frozen["state"][key], before)
    trajectories = _stack(trajectory_records)
    planning = _stack(planner_records)
    pairing_checks = _validate_pairing(trajectories, planning, config)
    reduction = reduce_episode_returns(trajectories, config)

    actual_steps = len(CELLS) * config.episodes * config.steps
    planner_calls = 8 * actual_steps
    constructors = len(CELLS) * config.episodes
    expected_exposure = {
        "native_constructors": constructors,
        "implicit_constructor_resets": constructors,
        "logical_episode_initializations": constructors,
        "custom_geometry_channel_refreshes": constructors,
        "deep_copies": planner_calls,
        "training_native_step_calls": 0,
        "evaluation_native_step_calls": actual_steps,
        "planner_native_step_calls": planner_calls,
    }
    if exposure != expected_exposure:
        raise RuntimeError(f"B11 exposure mismatch: {exposure} != {expected_exposure}")

    cell_diagnostics = {
        label: _cell_diagnostics(trajectories, law_id, table_id)
        for law_id, table_id, label in CELLS
    }
    occupancy_regret_diagnostics = {
        label: _occupancy_regret_diagnostics(planning, law_id, table_id)
        for law_id, table_id, label in CELLS
    }
    per_cell_cost = {
        label: {
            "actual_native_step_calls": config.episodes * config.steps,
            "planner_native_step_calls": 8 * config.episodes * config.steps,
            "response_tables": config.episodes * config.steps,
            "source_table_q_vectors": config.episodes * config.steps,
            "target_table_q_vectors": config.episodes * config.steps,
            "source_table_candidate_choices": config.episodes * config.steps,
            "target_table_candidate_choices": config.episodes * config.steps,
            "actual_focal_policy_choices": config.episodes * config.steps,
        }
        for _, _, label in CELLS
    }
    summary = {
        "seed": int(frozen["seed"]),
        "rng_master_seed": int(rng_seed),
        "frozen_base_seed": int(frozen["seed"]),
        "status": "COMPLETE",
        "config": asdict(config),
        "cells": [label for _, _, label in CELLS],
        "frozen_source_probabilities": probabilities[0].tolist(),
        "frozen_target_probabilities": probabilities[1].tolist(),
        "frozen_state_digests": frozen["verified_digests"],
        "counts": {
            "new_fits": 0,
            "training_observations": 0,
            "count_updates": 0,
            "gradient_calls": 0,
            "actor_value_network_forwards": 0,
            "learner_probability_queries": 0,
            "loaded_fixed_states": 1,
            "loaded_source_probability_views": 1,
            "loaded_target_probability_views": 1,
            "loader_unused_marginal_product_views": 1,
            "evaluation_episodes": constructors,
            "evaluation_team_steps": actual_steps,
            "response_tables": actual_steps,
            "source_table_q_vectors": actual_steps,
            "target_table_q_vectors": actual_steps,
            "source_table_candidate_choices": actual_steps,
            "target_table_candidate_choices": actual_steps,
            "actual_focal_policy_choices": actual_steps,
            "true_law_q_vectors_after_choices": actual_steps,
            "candidate_true_chosen_values_after_choice": 2 * actual_steps,
            "candidate_true_regrets_after_choice": 2 * actual_steps,
            "actual_true_chosen_values_after_choice": actual_steps,
            "actual_true_regrets_after_choice": actual_steps,
            "external_innovation_draw_calls": actual_steps,
            "unique_external_innovation_addresses": config.episodes * config.steps,
            "native_constructors": constructors,
            "implicit_constructor_resets": constructors,
            "logical_episode_initializations": constructors,
            "custom_geometry_channel_refreshes": constructors,
            "actual_native_step_calls": actual_steps,
            "planning_native_step_calls": planner_calls,
            "deep_copies": planner_calls,
            "total_native_step_calls": actual_steps + planner_calls,
        },
        "per_cell_cost": per_cell_cost,
        "cell_diagnostics": cell_diagnostics,
        "occupancy_regret_diagnostics": occupancy_regret_diagnostics,
        "pairing_checks": pairing_checks,
        "episode_initializations": initializations,
        "reduction": reduction,
        "historical_input_cost": {
            "source_object": "B09 final64",
            "fits": 1,
            "source_observations": 64,
            "target_observations": 64,
            "recorded_counts": frozen["b09_recorded_counts"],
            "role": "already incurred sealed input cost; excluded from B11 new exposure",
        },
        "compute_wall_seconds": perf_counter() - started,
        "compute_wall_scope": "four law/table deployments, cloned eight-branch planning, actual native trajectories, and reductions",
        "information_contract": "both frozen B09 final64 whole-table rows select candidates; true law is used only for external generation and post-choice diagnosis",
    }
    return {
        "summary": summary,
        "trajectory": trajectories,
        "planning": planning,
        "frozen_state": {key: value.copy() for key, value in frozen["state"].items()},
        "actual_exposure": dict(exposure),
    }

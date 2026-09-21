"""B10 read-only deployment evaluation over frozen B09 final states."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from experiments.candidates.skill_teammate_drift_learning.native_joint_b09 import (
    study as b09,
)


POLICIES = ("J_emp", "M_proj", "IN", "OUT")
STREAM = 2
PHASE = 2
TARGET_VERSION = 1
EXPECTED_B09_PLAN_SOURCE = "ee2d70c69abc0c5a45881da6e74937a7ac166689"

EXPOSURE_KEYS = (
    "native_constructors",
    "implicit_constructor_resets",
    "logical_episode_initializations",
    "custom_geometry_channel_refreshes",
    "deep_copies",
    "training_native_step_calls",
    "evaluation_native_step_calls",
    "planner_native_step_calls",
)


@dataclass(frozen=True)
class Config:
    episodes: int = 4
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
        raise ValueError("B10 permits only its frozen production or declared tiny config")


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        arrays = {key: archive[key].copy() for key in archive.files}
    for value in arrays.values():
        value.setflags(write=False)
    return arrays


def _validate_frozen_arrays(state: dict[str, np.ndarray]) -> None:
    required = {
        "initial_counts",
        "initial_probabilities",
        "initial_updates",
        "initial_probability_queries",
        "final_counts",
        "final_probabilities",
        "final_updates",
        "final_probability_queries",
        "snapshot_target_observations",
        "snapshot_counts",
        "snapshot_probabilities",
        "snapshot_updates",
    }
    if set(state) != required:
        raise ValueError("B09 frozen state keys differ from the sealed schema")
    if state["final_counts"].shape != (2, 4):
        raise ValueError("B09 final count shape mismatch")
    if not np.array_equal(state["final_updates"], [64, 64]):
        raise ValueError("B09 final state is not the declared 64/64 state")
    expected = (state["final_counts"] + 0.5) / (
        state["final_counts"].sum(axis=1, keepdims=True) + 2.0
    )
    if not np.array_equal(state["final_probabilities"], expected):
        raise ValueError("B09 final probabilities do not match sealed counts")
    if not np.array_equal(state["snapshot_target_observations"], [16, 64]):
        raise ValueError("B09 snapshot identities mismatch")
    for final_key, snapshot_key in (
        ("final_counts", "snapshot_counts"),
        ("final_probabilities", "snapshot_probabilities"),
        ("final_updates", "snapshot_updates"),
    ):
        if not np.array_equal(state[final_key], state[snapshot_key][-1]):
            raise ValueError(f"B09 final state differs from final64: {final_key}")
    if any(array.dtype == object for array in state.values()):
        raise ValueError("B09 frozen state contains object arrays")


def load_frozen_state(
    input_root: Path,
    seed: int,
    *,
    expected_root_artifacts_sha256: str,
) -> dict[str, Any]:
    """Load one final64 state through both B09 artifact manifests."""
    input_root = Path(input_root)
    root_manifest_path = input_root / "artifacts.json"
    if _sha256(root_manifest_path) != expected_root_artifacts_sha256:
        raise ValueError("B09 root artifact-manifest digest mismatch")
    root_manifest = json.loads(root_manifest_path.read_text())
    root_summary_path = input_root / "summary.json"
    source_manifest_path = input_root / "source-manifest.json"
    for path in (root_summary_path, source_manifest_path):
        key = path.relative_to(input_root).as_posix()
        if root_manifest.get(key) != _sha256(path):
            raise ValueError(f"B09 root artifact digest mismatch: {key}")
    root_summary = json.loads(root_summary_path.read_text())
    if (
        root_summary.get("status") != "COMPLETE"
        or root_summary.get("seeds") != [95401, 95402, 95403]
        or root_summary.get("completed_fits") != 3
        or root_summary.get("plan_source") != EXPECTED_B09_PLAN_SOURCE
    ):
        raise ValueError("B09 root result identity mismatch")
    source_manifest = json.loads(source_manifest_path.read_text())
    if source_manifest.get("plan_source") != EXPECTED_B09_PLAN_SOURCE:
        raise ValueError("B09 source manifest plan identity mismatch")

    block = input_root / f"seed_{int(seed)}"
    manifest_path = block / "artifacts.json"
    manifest_key = manifest_path.relative_to(input_root).as_posix()
    if root_manifest.get(manifest_key) != _sha256(manifest_path):
        raise ValueError("B09 per-seed artifact-manifest digest mismatch")
    manifest = json.loads(manifest_path.read_text())
    summary_path = block / "summary.json"
    state_path = block / "state.npz"
    verified = {
        "artifacts.json": _sha256(manifest_path),
        "summary.json": _sha256(summary_path),
        "state.npz": _sha256(state_path),
    }
    for name in ("summary.json", "state.npz"):
        if manifest.get(name) != verified[name]:
            raise ValueError(f"B09 per-seed artifact digest mismatch: {name}")
        root_key = (block / name).relative_to(input_root).as_posix()
        if root_manifest.get(root_key) != verified[name]:
            raise ValueError(f"B09 root-to-seed digest mismatch: {root_key}")
    summary = json.loads(summary_path.read_text())
    if (
        summary.get("seed") != int(seed)
        or summary.get("status") != "COMPLETE"
        or summary.get("fits") != 1
        or summary.get("plan_source") != EXPECTED_B09_PLAN_SOURCE
        or summary.get("config", {}).get("source_steps") != 64
        or summary.get("config", {}).get("target_steps") != 64
        or summary.get("config", {}).get("snapshot_steps") != [16, 64]
    ):
        raise ValueError("B09 per-seed result identity mismatch")
    state = _load_npz(state_path)
    _validate_frozen_arrays(state)
    return {
        "seed": int(seed),
        "state": state,
        "target_probabilities": state["final_probabilities"][TARGET_VERSION].copy(),
        "projected_probabilities": b09.marginal_product(
            state["final_probabilities"][TARGET_VERSION]
        ),
        "verified_digests": verified,
        "b09_launch_sha": summary["launch_sha"],
        "b09_plan_source": summary["plan_source"],
        "b09_recorded_counts": summary["counts"],
        "b09_source_manifest": source_manifest,
    }


def _stack(records: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    if not records:
        raise ValueError("cannot stack empty records")
    keys = set(records[0])
    if any(set(record) != keys for record in records):
        raise RuntimeError("record schemas differ")
    return {key: np.asarray([record[key] for record in records]) for key in records[0]}


def _selected_branch_matches(
    physical: dict[str, Any], table: dict[str, np.ndarray], focal: int, row: int
) -> None:
    keys = (
        "issued_actions",
        "after_positions",
        "after_observations",
        "after_connections",
        "after_sinr",
        "adapter_reward",
        "team_reward",
        "reward_components",
        "terminated",
        "truncated",
        "terminal_agents",
        "truncated_agents",
    )
    for key in keys:
        if not np.array_equal(physical[key], table[key][focal, row]):
            raise RuntimeError(f"selected planner branch differs from actual: {key}")


def _policy_diagnostics(
    trajectories: dict[str, np.ndarray], policy_index: int
) -> dict[str, Any]:
    rows = trajectories["policy_index"] == policy_index
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
        "final_radius_by_episode_and_agent": radii.reshape(-1, trajectories["tick"][rows].max() + 1, 3)[:, -1].tolist(),
    }


def reduce_episode_returns(
    trajectories: dict[str, np.ndarray], config: Config
) -> dict[str, Any]:
    returns: dict[str, list[float]] = {}
    team_returns: dict[str, list[float]] = {}
    for policy_index, policy in enumerate(POLICIES):
        adapter_values = []
        team_values = []
        for episode in range(config.episodes):
            rows = (trajectories["policy_index"] == policy_index) & (
                trajectories["episode"] == episode
            )
            if int(rows.sum()) != config.steps:
                raise RuntimeError("incomplete policy episode in B10 trajectory")
            adapter_values.append(float(trajectories["adapter_reward"][rows].sum()))
            team_values.append(float(trajectories["team_reward"][rows].sum()))
        returns[policy] = adapter_values
        team_returns[policy] = team_values
    contrasts = {}
    for name, left, right in (
        ("J_minus_IN", "J_emp", "IN"),
        ("J_minus_OUT", "J_emp", "OUT"),
        ("J_minus_M", "J_emp", "M_proj"),
        ("M_minus_OUT", "M_proj", "OUT"),
    ):
        paired = (np.asarray(returns[left]) - np.asarray(returns[right])).tolist()
        contrasts[name] = {
            "paired_episode_adapter_returns": paired,
            "base_mean_adapter_return": float(np.mean(paired)),
            "paired_episode_team_returns": (3.0 * np.asarray(paired)).tolist(),
            "base_mean_team_return": float(3.0 * np.mean(paired)),
        }
    return {
        "episode_adapter_returns": returns,
        "episode_team_returns": team_returns,
        "base_mean_adapter_returns": {
            policy: float(np.mean(values)) for policy, values in returns.items()
        },
        "contrasts": contrasts,
    }


def reduce_blocks(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if [int(block["seed"]) for block in blocks] != [95401, 95402, 95403]:
        raise ValueError("B10 root reduction requires fixed bases in order")
    result: dict[str, Any] = {
        "primary": ["J_minus_IN", "J_minus_OUT"],
        "secondary": ["J_minus_M", "M_minus_OUT"],
        "equal_weight_three_base_means": {},
        "base_means": {},
        "paired_episode_values_by_base": {},
        "no_threshold_selection_or_confidence_claim": True,
    }
    for contrast in ("J_minus_IN", "J_minus_OUT", "J_minus_M", "M_minus_OUT"):
        base_values = [
            float(block["reduction"]["contrasts"][contrast]["base_mean_adapter_return"])
            for block in blocks
        ]
        result["base_means"][contrast] = base_values
        result["equal_weight_three_base_means"][contrast] = float(np.mean(base_values))
        result["paired_episode_values_by_base"][contrast] = [
            block["reduction"]["contrasts"][contrast][
                "paired_episode_adapter_returns"
            ]
            for block in blocks
        ]
    return result


def run_evaluation(
    config: Config,
    seed: int,
    frozen: dict[str, Any],
    *,
    exposure: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Run four deployment policies without constructing or updating a learner."""
    validate_config(config)
    if int(frozen["seed"]) not in (95401, 95402, 95403):
        raise ValueError("frozen state must be one of the three B09 bases")
    if exposure is None:
        exposure = {key: 0 for key in EXPOSURE_KEYS}
    if set(exposure) != set(EXPOSURE_KEYS) or any(exposure.values()):
        raise ValueError("exposure must be a fresh complete B10 counter")
    joint = np.asarray(frozen["target_probabilities"], dtype=np.float64).copy()
    projected = np.asarray(frozen["projected_probabilities"], dtype=np.float64).copy()
    np.testing.assert_array_equal(projected, b09.marginal_product(joint))
    frozen_guard = {
        key: value.copy() for key, value in frozen["state"].items()
    }
    started = perf_counter()
    trajectory_records: list[dict[str, Any]] = []
    planner_records: list[dict[str, Any]] = []
    initializations = []

    for policy_index, policy in enumerate(POLICIES):
        for episode in range(config.episodes):
            adapter, observations, geometry_slots, environment_seed = b09._make_adapter(
                config,
                int(seed),
                config.stream,
                config.phase,
                episode,
                config.steps,
                exposure,
            )
            initializations.append(
                {
                    "policy": policy,
                    "episode": episode,
                    "environment_seed": environment_seed,
                    "geometry_slots": geometry_slots.tolist(),
                    "initial_positions": adapter.env.uav_positions.tolist(),
                }
            )
            for tick in range(config.steps):
                planner_index = -1
                if policy in ("J_emp", "M_proj"):
                    table = b09.response_table(adapter, exposure)
                    joint_values = table["adapter_reward"] @ joint
                    projected_values = table["adapter_reward"] @ projected
                    choices = np.array(
                        [
                            int(joint_values[1] > joint_values[0]),
                            int(projected_values[1] > projected_values[0]),
                        ],
                        dtype=np.int8,
                    )
                    focal_bit = int(choices[policy_index])
                    true_values = table["adapter_reward"] @ b09.TARGET_Q
                    planner_index = len(planner_records)
                    planner = {
                        "trajectory_index": len(trajectory_records),
                        "policy_index": policy_index,
                        "episode": episode,
                        "tick": tick,
                        "joint_probabilities": joint.copy(),
                        "projected_probabilities": projected.copy(),
                        "joint_values": joint_values,
                        "projected_values": projected_values,
                        "choices": choices,
                        "selected_focal_bit": focal_bit,
                        "true_values_after_choice": true_values,
                        "true_chosen_value_after_choice": float(true_values[focal_bit]),
                        "true_regret_after_choice": float(
                            np.max(true_values) - true_values[focal_bit]
                        ),
                    }
                    planner.update({f"response_{key}": value for key, value in table.items()})
                    planner_records.append(planner)
                elif policy == "IN":
                    focal_bit = 1
                else:
                    focal_bit = 0

                external_uniform = b09._slot(
                    int(seed), 2, config.stream, config.phase, episode, tick
                )
                row = b09._sample_row(b09.TARGET_Q, external_uniform)
                teammate_bits = np.array([row // 2, row % 2], dtype=np.int8)
                command_bits = np.array([focal_bit, *teammate_bits], dtype=np.int8)
                pre_positions = adapter.env.uav_positions.copy()
                actions = b09.commands_from_bits(pre_positions, command_bits)
                decoded_bits, decoded_row = b09.decode_teammate_row(
                    pre_positions, actions
                )
                if decoded_row != row or not np.array_equal(decoded_bits, teammate_bits):
                    raise RuntimeError("issued B10 commands decode to a different row")
                physical, observations = b09._step_record(adapter, observations, actions)
                b09._increment(exposure, "evaluation_native_step_calls")
                if planner_index >= 0:
                    _selected_branch_matches(physical, table, focal_bit, row)
                trajectory_records.append(
                    {
                        **physical,
                        "stream": config.stream,
                        "phase": config.phase,
                        "policy_index": policy_index,
                        "episode": episode,
                        "tick": tick,
                        "rng_address": np.array(
                            [seed, config.stream, config.phase, episode, tick],
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
    reduction = reduce_episode_returns(trajectories, config)
    actual_steps = len(POLICIES) * config.episodes * config.steps
    response_tables = 2 * config.episodes * config.steps
    planner_calls = 8 * response_tables
    expected_exposure = {
        "native_constructors": len(POLICIES) * config.episodes,
        "implicit_constructor_resets": len(POLICIES) * config.episodes,
        "logical_episode_initializations": len(POLICIES) * config.episodes,
        "custom_geometry_channel_refreshes": len(POLICIES) * config.episodes,
        "deep_copies": planner_calls,
        "training_native_step_calls": 0,
        "evaluation_native_step_calls": actual_steps,
        "planner_native_step_calls": planner_calls,
    }
    if exposure != expected_exposure:
        raise RuntimeError(f"B10 exposure mismatch: {exposure} != {expected_exposure}")
    policy_diagnostics = {
        policy: _policy_diagnostics(trajectories, index)
        for index, policy in enumerate(POLICIES)
    }
    per_policy_cost = {
        policy: {
            "actual_native_step_calls": config.episodes * config.steps,
            "planner_native_step_calls": (
                8 * config.episodes * config.steps
                if policy in ("J_emp", "M_proj")
                else 0
            ),
            "response_tables": (
                config.episodes * config.steps
                if policy in ("J_emp", "M_proj")
                else 0
            ),
            "joint_q_vectors": (
                config.episodes * config.steps
                if policy in ("J_emp", "M_proj")
                else 0
            ),
            "projected_q_vectors": (
                config.episodes * config.steps
                if policy in ("J_emp", "M_proj")
                else 0
            ),
            "focal_policy_choices": config.episodes * config.steps,
        }
        for policy in POLICIES
    }
    summary = {
        "seed": int(seed),
        "frozen_base_seed": int(frozen["seed"]),
        "status": "COMPLETE",
        "config": asdict(config),
        "policies": list(POLICIES),
        "frozen_target_probabilities": joint.tolist(),
        "frozen_marginal_product": projected.tolist(),
        "frozen_state_digests": frozen["verified_digests"],
        "counts": {
            "new_fits": 0,
            "training_observations": 0,
            "count_updates": 0,
            "gradient_calls": 0,
            "actor_value_network_forwards": 0,
            "learner_probability_queries": 0,
            "loaded_fixed_states": 1,
            "loaded_target_probability_views": 1,
            "frozen_projection_constructions": 1,
            "projection_equivalence_calculations": 1,
            "total_marginal_projection_calculations": 2,
            "evaluation_episodes": len(POLICIES) * config.episodes,
            "evaluation_team_steps": actual_steps,
            "response_tables": response_tables,
            "joint_q_vectors": response_tables,
            "projected_q_vectors": response_tables,
            "joint_choices": response_tables,
            "projected_choices": response_tables,
            "actual_focal_policy_choices": actual_steps,
            "J_emp_deployment_choices": config.episodes * config.steps,
            "M_proj_deployment_choices": config.episodes * config.steps,
            "fixed_IN_choice_assignments": config.episodes * config.steps,
            "fixed_OUT_choice_assignments": config.episodes * config.steps,
            "true_q_vectors_after_choice": response_tables,
            "true_chosen_values_after_choice": response_tables,
            "true_regrets_after_choice": response_tables,
            "external_innovation_draw_calls": actual_steps,
            "unique_external_innovation_addresses": config.episodes * config.steps,
            "native_constructors": len(POLICIES) * config.episodes,
            "implicit_constructor_resets": len(POLICIES) * config.episodes,
            "logical_episode_initializations": len(POLICIES) * config.episodes,
            "custom_geometry_channel_refreshes": len(POLICIES) * config.episodes,
            "actual_native_step_calls": actual_steps,
            "planning_native_step_calls": planner_calls,
            "deep_copies": planner_calls,
            "total_native_step_calls": actual_steps + planner_calls,
        },
        "per_policy_cost": per_policy_cost,
        "policy_diagnostics": policy_diagnostics,
        "episode_initializations": initializations,
        "reduction": reduction,
        "historical_input_cost": {
            "source_object": "B09 final64",
            "fits": 1,
            "source_observations": 64,
            "target_observations": 64,
            "recorded_counts": frozen["b09_recorded_counts"],
            "role": "already incurred sealed input cost; excluded from B10 new exposure",
        },
        "compute_wall_seconds": perf_counter() - started,
        "compute_wall_scope": "four fixed deployment policies, J/M cloned one-step planning, actual native trajectories, and reductions",
        "information_contract": "read-only B09 final64 target probability view; true q is external generation and post-choice diagnosis only",
    }
    return {
        "summary": summary,
        "trajectory": trajectories,
        "planning": planning,
        "frozen_state": {key: value.copy() for key, value in frozen["state"].items()},
        "actual_exposure": dict(exposure),
    }

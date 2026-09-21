"""B09 empirical joint law versus its marginal projection on native Scenario1."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import hashlib
import json
from time import perf_counter
from typing import Any

import numpy as np

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario1 import UAVBaseStationEnv


SOURCE_Q = np.array([0.1, 0.4, 0.4, 0.1], dtype=np.float64)
TARGET_Q = np.array([0.4, 0.1, 0.1, 0.4], dtype=np.float64)
TRUE_Q = np.stack((SOURCE_Q, TARGET_Q))
VIEWS = ("J_emp", "M_proj")
USER_POSITION = np.array([500.0, 500.0], dtype=np.float64)
PRIOR_CELL_MASS = 0.5
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
    source_steps: int = 64
    target_steps: int = 64
    snapshot_steps: tuple[int, int] = (16, 64)
    evaluation_episodes: int = 4
    evaluation_steps: int = 64
    n_uavs: int = 3
    n_users: int = 1
    area_size: float = 1000.0
    height_range: tuple[float, float] = (50.0, 150.0)
    max_speed: float = 30.0
    time_step: float = 1.0
    min_sinr: float = 0.0
    max_connections: int = 10


PRODUCTION_CONFIG = Config()
TINY_CONFIG = Config(
    source_steps=2,
    target_steps=2,
    snapshot_steps=(1, 2),
    evaluation_episodes=1,
    evaluation_steps=2,
)


def validate_config(config: Config) -> None:
    if config not in (PRODUCTION_CONFIG, TINY_CONFIG):
        raise ValueError("B09 permits only its frozen production or declared tiny config")


class JointLawLearner:
    """Two independent version-specific Dirichlet frequency tables."""

    def __init__(self) -> None:
        self.counts = np.zeros((2, 4), dtype=np.int64)
        self.updates = np.zeros(2, dtype=np.int64)
        self.probability_queries = 0

    def predict(self, version: int) -> np.ndarray:
        if version not in (0, 1):
            raise ValueError("version must be zero or one")
        self.probability_queries += 1
        counts = self.counts[version]
        return (counts + PRIOR_CELL_MASS) / (counts.sum() + 4 * PRIOR_CELL_MASS)

    def observe(self, version: int, row: int) -> None:
        if version not in (0, 1) or row not in (0, 1, 2, 3):
            raise ValueError("invalid version or joint-command row")
        self.counts[version, row] += 1
        self.updates[version] += 1

    def export_state(self) -> dict[str, np.ndarray]:
        probabilities = np.stack((self.predict(0), self.predict(1)))
        return {
            "counts": self.counts.copy(),
            "probabilities": probabilities,
            "updates": self.updates.copy(),
            "probability_queries": np.array(
                [self.probability_queries], dtype=np.int64
            ),
        }


def marginal_product(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if probabilities.shape != (4,) or not np.isfinite(probabilities).all():
        raise ValueError("joint probabilities must be a finite four-vector")
    if np.any(probabilities < 0.0) or not np.isclose(probabilities.sum(), 1.0):
        raise ValueError("joint probabilities must form a distribution")
    first_one = probabilities[2] + probabilities[3]
    second_one = probabilities[1] + probabilities[3]
    return np.array(
        [
            (1 - first_one) * (1 - second_one),
            (1 - first_one) * second_one,
            first_one * (1 - second_one),
            first_one * second_one,
        ],
        dtype=np.float64,
    )


def joint_contrast(probabilities: np.ndarray) -> float:
    probabilities = np.asarray(probabilities, dtype=np.float64)
    return float(probabilities[0] - probabilities[1] - probabilities[2])


def _rng(seed: int, *address: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([int(seed), *map(int, address)]))


def _increment(exposure: dict[str, int] | None, key: str, amount: int = 1) -> None:
    if exposure is not None:
        exposure[key] = int(exposure.get(key, 0)) + amount


def _slot(seed: int, category: int, stream: int, phase: int, episode: int, tick: int) -> float:
    return float(_rng(seed, category, stream, phase, episode, tick).random())


def _geometry(seed: int, stream: int, phase: int, episode: int) -> tuple[np.ndarray, np.ndarray]:
    generator = _rng(seed, 1, stream, phase, episode)
    slots = generator.random(7)
    rotation = 2.0 * np.pi * slots[0]
    radii = 75.0 + 10.0 * slots[1:4]
    jitters = -np.pi / 36.0 + (np.pi / 18.0) * slots[4:7]
    positions = np.empty((3, 3), dtype=np.float64)
    for index in range(3):
        angle = rotation + 2.0 * np.pi * index / 3.0 + jitters[index]
        positions[index] = [
            USER_POSITION[0] + radii[index] * np.cos(angle),
            USER_POSITION[1] + radii[index] * np.sin(angle),
            50.0,
        ]
    return positions, slots


def _make_adapter(
    config: Config,
    seed: int,
    stream: int,
    phase: int,
    episode: int,
    steps: int,
    exposure: dict[str, int] | None = None,
):
    environment_seed = int(
        _rng(seed, 4, stream, phase, episode).integers(0, 2**31 - 1)
    )
    environment = UAVBaseStationEnv(
        n_uavs=config.n_uavs,
        n_users=config.n_users,
        area_size=config.area_size,
        height_range=config.height_range,
        max_speed=config.max_speed,
        time_step=config.time_step,
        max_steps=steps,
        user_distribution="uniform",
        channel_model="free_space",
        seed=environment_seed,
        min_sinr=config.min_sinr,
        max_connections=config.max_connections,
        coverage_weight=0.7,
        quality_weight=0.3,
        step_path_loss_cache=True,
        channel_backend="vectorized",
    )
    _increment(exposure, "native_constructors")
    _increment(exposure, "implicit_constructor_resets")
    adapter = ParallelToArrayAdapter(environment, seed=environment_seed)
    positions, geometry_slots = _geometry(seed, stream, phase, episode)
    environment.uav_positions[...] = positions
    environment.user_positions[...] = USER_POSITION[None, :]
    environment.current_step = 0
    environment.agents = environment.possible_agents.copy()
    environment._begin_path_loss_step()
    environment._update_channel_state()
    _increment(exposure, "logical_episode_initializations")
    _increment(exposure, "custom_geometry_channel_refreshes")
    observations = adapter._dict_to_array(
        {agent: environment._get_observation(agent) for agent in environment.agents}
    ).astype(np.float32)
    return adapter, observations, geometry_slots, environment_seed


def _outward_vectors(positions: np.ndarray) -> np.ndarray:
    result = np.empty((3, 2), dtype=np.float64)
    for index, position in enumerate(np.asarray(positions, dtype=np.float64)):
        displacement = position[:2] - USER_POSITION
        radius = float(np.linalg.norm(displacement))
        if radius <= 1e-12:
            angle = 2.0 * np.pi * index / 3.0
            result[index] = [np.cos(angle), np.sin(angle)]
        else:
            result[index] = displacement / radius
    return result


def commands_from_bits(positions: np.ndarray, bits: np.ndarray) -> np.ndarray:
    bits = np.asarray(bits, dtype=np.int8)
    if bits.shape != (3,) or not np.isin(bits, (0, 1)).all():
        raise ValueError("command bits must be a binary three-vector")
    directions = _outward_vectors(positions)
    signs = np.where(bits == 0, 1.0, -1.0)
    actions = np.zeros((3, 3), dtype=np.float32)
    actions[:, :2] = (directions * signs[:, None]).astype(np.float32)
    return actions


def decode_teammate_row(positions: np.ndarray, issued_actions: np.ndarray) -> tuple[np.ndarray, int]:
    actions = np.asarray(issued_actions, dtype=np.float32)
    if actions.shape != (3, 3):
        raise ValueError("issued actions must have shape (3, 3)")
    outward = _outward_vectors(positions)
    bits = np.empty(2, dtype=np.int8)
    for output, agent in enumerate((1, 2)):
        dot = float(actions[agent, :2] @ outward[agent])
        if abs(dot) <= 0.5 or actions[agent, 2] != 0.0:
            raise ValueError("issued teammate command is not a declared radial command")
        bits[output] = int(dot < 0.0)
    expected = commands_from_bits(
        positions, np.array([0, bits[0], bits[1]], dtype=np.int8)
    )
    if not np.array_equal(expected[1:], actions[1:]):
        raise ValueError("decoded teammate bits do not reproduce issued commands")
    return bits, int(2 * bits[0] + bits[1])


def _sample_row(probabilities: np.ndarray, uniform: float) -> int:
    cumulative = np.cumsum(np.asarray(probabilities, dtype=np.float64))
    return int(np.searchsorted(cumulative, uniform, side="right"))


def _components(info: dict[str, Any]) -> np.ndarray:
    values = info["reward_info"]
    return np.array(
        [
            values["coverage_reward"],
            values["quality_reward"],
            values["energy_penalty"],
            values["total_reward"],
        ],
        dtype=np.float64,
    )


def _rng_state_bytes(generator: Any) -> bytes:
    if hasattr(generator, "bit_generator"):
        return json.dumps(
            generator.bit_generator.state, sort_keys=True, default=lambda x: np.asarray(x).tolist()
        ).encode()
    state = generator.get_state()
    return b"|".join(
        (
            state[0].encode(),
            np.asarray(state[1]).tobytes(),
            str(state[2:]).encode(),
        )
    )


def native_state_digest(adapter: ParallelToArrayAdapter) -> np.ndarray:
    environment = adapter.env
    digest = hashlib.sha256()
    for value in (
        environment.uav_positions,
        environment.user_positions,
        environment.connections,
        environment.sinr_matrix,
        np.array([environment.current_step], dtype=np.int64),
    ):
        array = np.ascontiguousarray(value)
        digest.update(str(array.dtype).encode())
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
    digest.update(_rng_state_bytes(environment.np_random))
    digest.update(_rng_state_bytes(adapter.np_random))
    return np.frombuffer(digest.digest(), dtype=np.uint8).copy()


def _step_record(adapter: ParallelToArrayAdapter, observations: np.ndarray, actions: np.ndarray):
    environment = adapter.env
    pre_positions = environment.uav_positions.copy()
    pre_connections = environment.connections.copy()
    pre_sinr = environment.sinr_matrix.copy()
    next_observations, scalar_reward, terminated, truncated, info = adapter.step(actions)
    team_reward = float(scalar_reward) * environment.n_uavs
    components = _components(info)
    if not np.isclose(team_reward, components[3], rtol=0.0, atol=1e-12):
        raise RuntimeError("adapter scalar and physical team reward do not reconcile")
    terminal_agents = np.array(
        [info["terminations_dict"][agent] for agent in adapter.agents], dtype=np.bool_
    )
    truncated_agents = np.array(
        [info["truncations_dict"][agent] for agent in adapter.agents], dtype=np.bool_
    )
    return {
        "pre_positions": pre_positions,
        "pre_observations": observations.copy(),
        "pre_connections": pre_connections,
        "pre_sinr": pre_sinr,
        "issued_actions": actions.copy(),
        "after_positions": environment.uav_positions.copy(),
        "after_observations": next_observations.copy(),
        "after_connections": environment.connections.copy(),
        "after_sinr": environment.sinr_matrix.copy(),
        "adapter_reward": float(scalar_reward),
        "team_reward": team_reward,
        "reward_components": components,
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "terminal_agents": terminal_agents,
        "truncated_agents": truncated_agents,
    }, next_observations


def _stack(records: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    keys = records[0]
    if any(set(record) != set(keys) for record in records):
        raise RuntimeError("record schemas differ")
    return {key: np.asarray([record[key] for record in records]) for key in keys}


def response_table(
    adapter: ParallelToArrayAdapter, exposure: dict[str, int] | None = None
) -> dict[str, np.ndarray]:
    source_digest = native_state_digest(adapter)
    records = []
    positions = adapter.env.uav_positions.copy()
    for focal_bit in (0, 1):
        for row in range(4):
            teammate_bits = np.array([row // 2, row % 2], dtype=np.int8)
            bits = np.array([focal_bit, *teammate_bits], dtype=np.int8)
            actions = commands_from_bits(positions, bits)
            clone = copy.deepcopy(adapter)
            _increment(exposure, "deep_copies")
            clone_pre_digest = native_state_digest(clone)
            if not np.array_equal(clone_pre_digest, source_digest):
                raise RuntimeError("planner clone does not start at the source native state")
            observations = clone._dict_to_array(
                {agent: clone.env._get_observation(agent) for agent in clone.env.agents}
            ).astype(np.float32)
            record, _ = _step_record(clone, observations, actions)
            _increment(exposure, "planner_native_step_calls")
            record.update(
                focal_bit=focal_bit,
                teammate_row=row,
                command_bits=bits,
                clone_pre_digest=clone_pre_digest,
            )
            records.append(record)
    if not np.array_equal(native_state_digest(adapter), source_digest):
        raise RuntimeError("hypothetical planner branches mutated the live native state")
    stacked = _stack(records)
    result = {
        "source_state_digest": source_digest,
        "source_state_unchanged": np.array([True], dtype=np.bool_),
    }
    for key, value in stacked.items():
        result[key] = value.reshape(2, 4, *value.shape[1:])
    return result


def nominal_response_table() -> dict[str, np.ndarray]:
    """Eight declared physics branches at radius 80, producing radii 50/110."""
    config = Config(source_steps=2, target_steps=2, snapshot_steps=(1, 2), evaluation_episodes=1, evaluation_steps=2)
    adapter, observations, _, _ = _make_adapter(config, 95991, 2, 0, 0, 1)
    angles = 2.0 * np.pi * np.arange(3) / 3.0
    adapter.env.uav_positions[...] = np.column_stack(
        (
            USER_POSITION[0] + 80.0 * np.cos(angles),
            USER_POSITION[1] + 80.0 * np.sin(angles),
            np.full(3, 50.0),
        )
    )
    adapter.env.user_positions[...] = USER_POSITION[None, :]
    adapter.env._begin_path_loss_step()
    adapter.env._update_channel_state()
    return response_table(adapter)


def _training(
    config: Config,
    seed: int,
    learner: JointLawLearner,
    exposure: dict[str, int] | None,
):
    records: list[dict[str, Any]] = []
    snapshots: dict[int, dict[str, np.ndarray]] = {}
    episode_metadata = []
    for version, steps in ((0, config.source_steps), (1, config.target_steps)):
        adapter, observations, geometry_slots, environment_seed = _make_adapter(
            config, seed, 0, version, 0, steps, exposure
        )
        episode_metadata.append(
            {
                "version": version,
                "environment_seed": environment_seed,
                "geometry_slots": geometry_slots.tolist(),
                "initial_positions": adapter.env.uav_positions.tolist(),
            }
        )
        for tick in range(steps):
            probabilities = learner.predict(version)
            projected = marginal_product(probabilities)
            counts_before = learner.counts.copy()
            external_uniform = _slot(seed, 2, 0, version, 0, tick)
            focal_uniform = _slot(seed, 3, 0, version, 0, tick)
            row = _sample_row(TRUE_Q[version], external_uniform)
            teammate_bits = np.array([row // 2, row % 2], dtype=np.int8)
            focal_bit = int(focal_uniform >= 0.5)
            command_bits = np.array([focal_bit, *teammate_bits], dtype=np.int8)
            pre_positions = adapter.env.uav_positions.copy()
            actions = commands_from_bits(pre_positions, command_bits)
            decoded_bits, decoded_row = decode_teammate_row(pre_positions, actions)
            if decoded_row != row or not np.array_equal(decoded_bits, teammate_bits):
                raise RuntimeError("actual issued commands decode to a different label")
            physical, observations = _step_record(adapter, observations, actions)
            _increment(exposure, "training_native_step_calls")
            learner.observe(version, decoded_row)
            record = {
                **physical,
                "stream": 0,
                "version": version,
                "episode": 0,
                "tick": tick,
                "rng_address": np.array([seed, 0, version, 0, tick], dtype=np.int64),
                "external_uniform": external_uniform,
                "focal_uniform": focal_uniform,
                "focal_bit": focal_bit,
                "teammate_bits": decoded_bits,
                "joint_row": decoded_row,
                "probabilities_before": probabilities,
                "projected_probabilities_before": projected,
                "counts_before": counts_before,
                "counts_after": learner.counts.copy(),
                "joint_log_loss": -np.log(probabilities[decoded_row]),
                "projected_log_loss": -np.log(projected[decoded_row]),
                "terminal_id": version if physical["terminated"] else -1,
            }
            records.append(record)
            target_observations = tick + 1
            if version == 1 and target_observations in config.snapshot_steps:
                snapshots[target_observations] = learner.export_state()
    if set(snapshots) != set(config.snapshot_steps):
        raise RuntimeError("training omitted a declared target snapshot")
    return _stack(records), snapshots, episode_metadata


def _evaluation(
    config: Config,
    seed: int,
    snapshots: dict[int, dict[str, np.ndarray]],
    exposure: dict[str, int] | None,
):
    records: list[dict[str, Any]] = []
    episode_rows = []
    episode_metadata = []
    snapshot_guard = {
        step: {key: value.copy() for key, value in state.items()}
        for step, state in snapshots.items()
    }
    for snapshot_step in config.snapshot_steps:
        frozen_counts = snapshots[snapshot_step]["counts"].copy()
        joint = snapshots[snapshot_step]["probabilities"][1].copy()
        projected = marginal_product(joint)
        for view_index, view in enumerate(VIEWS):
            distribution = joint if view == "J_emp" else projected
            for episode in range(config.evaluation_episodes):
                adapter, observations, geometry_slots, environment_seed = _make_adapter(
                    config, seed, 1, 2, episode, config.evaluation_steps, exposure
                )
                episode_metadata.append(
                    {
                        "snapshot_step": snapshot_step,
                        "view": view,
                        "episode": episode,
                        "environment_seed": environment_seed,
                        "geometry_slots": geometry_slots.tolist(),
                        "initial_positions": adapter.env.uav_positions.tolist(),
                    }
                )
                cumulative_adapter = 0.0
                cumulative_team = 0.0
                for tick in range(config.evaluation_steps):
                    table = response_table(adapter, exposure)
                    scalar_table = table["adapter_reward"]
                    joint_values = scalar_table @ joint
                    projected_values = scalar_table @ projected
                    choices = np.array(
                        [int(joint_values[1] > joint_values[0]), int(projected_values[1] > projected_values[0])],
                        dtype=np.int8,
                    )
                    focal_bit = int(choices[view_index])
                    # True q is used only after the focal choice is fixed.
                    true_values = scalar_table @ TARGET_Q
                    true_optimal = float(np.max(true_values))
                    external_uniform = _slot(seed, 2, 1, 2, episode, tick)
                    row = _sample_row(TARGET_Q, external_uniform)
                    teammate_bits = np.array([row // 2, row % 2], dtype=np.int8)
                    command_bits = np.array([focal_bit, *teammate_bits], dtype=np.int8)
                    pre_positions = adapter.env.uav_positions.copy()
                    actions = commands_from_bits(pre_positions, command_bits)
                    decoded_bits, decoded_row = decode_teammate_row(pre_positions, actions)
                    if decoded_row != row or not np.array_equal(decoded_bits, teammate_bits):
                        raise RuntimeError("evaluation issued commands decode incorrectly")
                    physical, observations = _step_record(adapter, observations, actions)
                    _increment(exposure, "evaluation_native_step_calls")
                    cumulative_adapter += physical["adapter_reward"]
                    cumulative_team += physical["team_reward"]
                    record = {
                        **physical,
                        "stream": 1,
                        "snapshot_step": snapshot_step,
                        "view": view_index,
                        "episode": episode,
                        "tick": tick,
                        "rng_address": np.array([seed, 1, 2, episode, tick], dtype=np.int64),
                        "external_uniform": external_uniform,
                        "teammate_bits": decoded_bits,
                        "joint_row": decoded_row,
                        "focal_bit": focal_bit,
                        "frozen_counts": frozen_counts,
                        "joint_probabilities": joint,
                        "projected_probabilities": projected,
                        "response_adapter_reward": table["adapter_reward"],
                        "response_team_reward": table["team_reward"],
                        "response_after_positions": table["after_positions"],
                        "response_after_observations": table["after_observations"],
                        "response_after_connections": table["after_connections"],
                        "response_after_sinr": table["after_sinr"],
                        "response_reward_components": table["reward_components"],
                        "response_terminated": table["terminated"],
                        "response_truncated": table["truncated"],
                        "response_terminal_agents": table["terminal_agents"],
                        "response_truncated_agents": table["truncated_agents"],
                        "response_issued_actions": table["issued_actions"],
                        "response_command_bits": table["command_bits"],
                        "response_clone_pre_digest": table["clone_pre_digest"],
                        "response_source_state_digest": table["source_state_digest"],
                        "response_source_state_unchanged": table["source_state_unchanged"][0],
                        "joint_values": joint_values,
                        "projected_values": projected_values,
                        "joint_choice": choices[0],
                        "projected_choice": choices[1],
                        "true_values_after_choice": true_values,
                        "true_chosen_value_after_choice": true_values[focal_bit],
                        "true_one_step_regret_after_choice": true_optimal - true_values[focal_bit],
                        "terminal_id": episode if physical["terminated"] else -1,
                    }
                    records.append(record)
                episode_rows.append(
                    {
                        "snapshot_step": snapshot_step,
                        "view": view,
                        "episode": episode,
                        "cumulative_adapter_reward": cumulative_adapter,
                        "cumulative_team_reward": cumulative_team,
                    }
                )
    for step, state in snapshots.items():
        for key, before in snapshot_guard[step].items():
            if not np.array_equal(state[key], before):
                raise RuntimeError(f"snapshot mutation detected at {step}/{key}")
    return _stack(records), episode_rows, episode_metadata


def reduce_episode_returns(config: Config, episode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_snapshot = {}
    for snapshot_step in config.snapshot_steps:
        values = {view: {} for view in VIEWS}
        teams = {view: {} for view in VIEWS}
        for row in episode_rows:
            if row["snapshot_step"] == snapshot_step:
                values[row["view"]][row["episode"]] = row["cumulative_adapter_reward"]
                teams[row["view"]][row["episode"]] = row["cumulative_team_reward"]
        expected = set(range(config.evaluation_episodes))
        if any(set(values[view]) != expected for view in VIEWS):
            raise RuntimeError("episode reduction is incomplete")
        paired = [values["J_emp"][episode] - values["M_proj"][episode] for episode in sorted(expected)]
        team_paired = [teams["J_emp"][episode] - teams["M_proj"][episode] for episode in sorted(expected)]
        by_snapshot[str(snapshot_step)] = {
            "J_emp_cumulative_adapter_rewards": [values["J_emp"][episode] for episode in sorted(expected)],
            "M_proj_cumulative_adapter_rewards": [values["M_proj"][episode] for episode in sorted(expected)],
            "paired_J_minus_M_adapter_returns": paired,
            "mean_J_minus_M_adapter_return": float(np.mean(paired)),
            "paired_J_minus_M_team_returns": team_paired,
            "mean_J_minus_M_team_return": float(np.mean(team_paired)),
            "role": "primary" if snapshot_step == config.snapshot_steps[-1] else "descriptive",
        }
    return {
        "primary_snapshot_target_observations": config.snapshot_steps[-1],
        "by_snapshot": by_snapshot,
        "independent_units": "three training histories; episodes, snapshots, and views are nested",
        "no_threshold_or_selection": True,
    }


def run_block(
    config: Config, seed: int, exposure: dict[str, int] | None = None
) -> dict[str, Any]:
    validate_config(config)
    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    started = perf_counter()
    learner = JointLawLearner()
    initial = learner.export_state()
    if exposure is not None:
        for key in EXPOSURE_KEYS:
            exposure.setdefault(key, 0)
    training, snapshots, training_episodes = _training(
        config, int(seed), learner, exposure
    )
    evaluation, episode_rows, evaluation_episodes = _evaluation(
        config, int(seed), snapshots, exposure
    )
    final = learner.export_state()
    for snapshot in snapshots.values():
        if np.shares_memory(snapshot["counts"], learner.counts):
            raise RuntimeError("snapshot is not frozen")
    reductions = reduce_episode_returns(config, episode_rows)
    training_steps = config.source_steps + config.target_steps
    if len(training["tick"]) != training_steps:
        raise RuntimeError("training trace length disagrees with the frozen config")
    evaluation_actual_steps = len(evaluation["tick"])
    expected_evaluation_steps = (
        len(config.snapshot_steps)
        * len(VIEWS)
        * config.evaluation_episodes
        * config.evaluation_steps
    )
    if evaluation_actual_steps != expected_evaluation_steps:
        raise RuntimeError("evaluation trace length disagrees with the frozen config")
    planner_steps = int(np.prod(evaluation["response_adapter_reward"].shape))
    if planner_steps != 8 * evaluation_actual_steps:
        raise RuntimeError("response-table trace does not contain eight branches per decision")
    logical_episodes = len(training_episodes) + len(evaluation_episodes)
    expected_exposure = {
        "native_constructors": logical_episodes,
        "implicit_constructor_resets": logical_episodes,
        "logical_episode_initializations": logical_episodes,
        "custom_geometry_channel_refreshes": logical_episodes,
        "deep_copies": planner_steps,
        "training_native_step_calls": training_steps,
        "evaluation_native_step_calls": evaluation_actual_steps,
        "planner_native_step_calls": planner_steps,
    }
    if exposure is not None and exposure != expected_exposure:
        raise RuntimeError(
            f"observed native exposure disagrees with traces: {exposure} != {expected_exposure}"
        )
    state_export_probability_queries = 2 * (2 + len(config.snapshot_steps))
    if int(final["probability_queries"][0]) != training_steps + state_export_probability_queries:
        raise RuntimeError("learner probability-query accounting mismatch")
    state = {
        **{f"initial_{key}": value for key, value in initial.items()},
        **{f"final_{key}": value for key, value in final.items()},
        "snapshot_target_observations": np.array(config.snapshot_steps, dtype=np.int64),
        "snapshot_counts": np.stack([snapshots[step]["counts"] for step in config.snapshot_steps]),
        "snapshot_probabilities": np.stack([snapshots[step]["probabilities"] for step in config.snapshot_steps]),
        "snapshot_updates": np.stack([snapshots[step]["updates"] for step in config.snapshot_steps]),
    }
    summary = {
        "seed": int(seed),
        "config": asdict(config),
        "status": "COMPLETE",
        "fits": 1,
        "learner": "two version-specific four-cell Dirichlet tables, mass 0.5 per cell",
        "views": list(VIEWS),
        "information_contract": "external B-owned mixture probabilities are not exposed to the focal learner",
        "counts": {
            "training_team_steps": training_steps,
            "observed_joint_labels": training_steps,
            "preupdate_probability_queries": training_steps,
            "initial_probability_export_queries": 2,
            "snapshot_probability_export_queries": 2 * len(config.snapshot_steps),
            "final_probability_export_queries": 2,
            "state_export_probability_queries": state_export_probability_queries,
            "total_learner_probability_queries": training_steps
            + state_export_probability_queries,
            "training_marginal_projection_constructions": training_steps,
            "evaluation_frozen_projection_constructions": len(config.snapshot_steps),
            "summary_projection_diagnostics": len(config.snapshot_steps) + 1,
            "joint_log_loss_terms": training_steps,
            "projected_log_loss_terms": training_steps,
            "count_updates": training_steps,
            "evaluation_episodes": logical_episodes - 2,
            "evaluation_team_steps": evaluation_actual_steps,
            "planner_native_step_calls": planner_steps,
            "evaluation_response_tables": evaluation_actual_steps,
            "evaluation_joint_q_vectors": evaluation_actual_steps,
            "evaluation_projected_q_vectors": evaluation_actual_steps,
            "evaluation_joint_choices": evaluation_actual_steps,
            "evaluation_projected_choices": evaluation_actual_steps,
            "evaluation_true_q_vectors_after_choice": evaluation_actual_steps,
            "evaluation_true_chosen_values_after_choice": evaluation_actual_steps,
            "evaluation_true_regrets_after_choice": evaluation_actual_steps,
            "evaluation_count_updates": 0,
            "real_team_ticks": training_steps + evaluation_actual_steps,
            "native_step_calls": training_steps + evaluation_actual_steps + planner_steps,
            "native_constructors": logical_episodes,
            "implicit_constructor_resets": logical_episodes,
            "logical_episode_initializations": logical_episodes,
            "custom_geometry_channel_refreshes": logical_episodes,
            "deep_copies": planner_steps,
            "gradient_calls": 0,
            "actor_value_network_forwards": 0,
            "external_innovation_draws": training_steps + evaluation_actual_steps,
            "focal_uniform_collection_draws": training_steps,
        },
        "snapshot_contrasts": {
            str(step): {
                "joint": joint_contrast(snapshots[step]["probabilities"][1]),
                "marginal_product": joint_contrast(
                    marginal_product(snapshots[step]["probabilities"][1])
                ),
            }
            for step in config.snapshot_steps
        },
        "truth_contrasts": {
            "source_joint": joint_contrast(SOURCE_Q),
            "target_joint": joint_contrast(TARGET_Q),
            "target_marginal_product": joint_contrast(marginal_product(TARGET_Q)),
        },
        "external_world_joint_laws": {
            "source_version0": SOURCE_Q.tolist(),
            "target_version1": TARGET_Q.tolist(),
            "role": "external generation and after-choice diagnostics only",
        },
        "reductions": reductions,
        "episode_returns": episode_rows,
        "training_episode_initializations": training_episodes,
        "evaluation_episode_initializations": evaluation_episodes,
        "compute_wall_seconds": perf_counter() - started,
        "compute_wall_scope": "one learner, native training, cloned one-step planning, actual evaluation, and reductions",
        "no_standard_hmasd_claim": True,
    }
    return {
        "summary": summary,
        "training": training,
        "evaluation": evaluation,
        "state": state,
        "actual_exposure": dict(exposure) if exposure is not None else expected_exposure,
    }

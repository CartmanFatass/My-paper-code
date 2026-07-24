"""Frozen core for the UAV temporary-service-loss G1 experiment.

The module is deliberately isolated from the ordinary HMASD trainers.  It
adds an exogenous service-availability overlay to Scenario 7/S1, a matched
continuous recurrent actor-critic, and the small collection/replay/checkpoint
surface consumed by the G1 runner.  It does not add reward terms or expose a
future loss schedule to either learned arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import copy
import math
import multiprocessing as mp
from multiprocessing.connection import Connection
from pathlib import Path
import traceback
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment
import torch
from torch import nn

from ha_ctse_process.continuous_roster_policy import (
    ContinuousRosterPolicy,
    ContinuousStepOutput,
)
from config_1 import Config
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv


PHYSICAL_UAVS = 8
ACTION_DIM = 4
HORIZON = 500
REJOIN_WINDOW = 60
QOS_TARGET = 0.90

FIXED_MASK_REC = "FIXED_MASK_REC"
PREFIX_NORMALIZED_OPEN_ROSTER = "PREFIX_NORMALIZED_OPEN_ROSTER"
ROUTING_MODES = frozenset({FIXED_MASK_REC, PREFIX_NORMALIZED_OPEN_ROSTER})

GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
PPO_PASSES = 4
CHECKPOINT_SCHEMA_VERSION = 1


class LossCell(str, Enum):
    IID_SINGLE = "IID_SINGLE"
    LATE_LONG_SINGLE = "LATE_LONG_SINGLE"
    OVERLAPPING_DOUBLE = "OVERLAPPING_DOUBLE"
    NO_DISTURBANCE = "NO_DISTURBANCE"


@dataclass(frozen=True, order=True)
class LossInterval:
    owner: int
    onset: int
    duration: int

    def __post_init__(self) -> None:
        if not 0 <= int(self.owner) < PHYSICAL_UAVS:
            raise ValueError("loss owner is outside the eight-UAV fleet")
        if int(self.onset) < 0 or int(self.duration) <= 0:
            raise ValueError("loss onset and duration must be positive-support values")
        if int(self.onset) + int(self.duration) > HORIZON:
            raise ValueError("loss interval exceeds the physical horizon")

    @property
    def rejoin(self) -> int:
        return int(self.onset) + int(self.duration)

    def contains(self, physical_step: int) -> bool:
        return int(self.onset) <= int(physical_step) < self.rejoin


@dataclass(frozen=True)
class UAVLossLedger:
    cell: LossCell
    episode_id: int
    intervals: tuple[LossInterval, ...]

    def __post_init__(self) -> None:
        cell = LossCell(self.cell)
        object.__setattr__(self, "cell", cell)
        expected = {
            LossCell.NO_DISTURBANCE: 0,
            LossCell.IID_SINGLE: 1,
            LossCell.LATE_LONG_SINGLE: 1,
            LossCell.OVERLAPPING_DOUBLE: 2,
        }[cell]
        if len(self.intervals) != expected:
            raise ValueError("loss ledger interval count does not match its cell")
        if len({entry.owner for entry in self.intervals}) != len(self.intervals):
            raise ValueError("one physical owner cannot have two registered losses")
        if cell is LossCell.IID_SINGLE:
            entry = self.intervals[0]
            if not (120 <= entry.onset <= 240 and 30 <= entry.duration <= 60):
                raise ValueError("IID_SINGLE ledger is outside registered support")
        elif cell is LossCell.LATE_LONG_SINGLE:
            entry = self.intervals[0]
            if not (280 <= entry.onset <= 330 and 70 <= entry.duration <= 100):
                raise ValueError("LATE_LONG_SINGLE ledger is outside registered support")
        elif cell is LossCell.OVERLAPPING_DOUBLE:
            first, second = self.intervals
            if not (
                140 <= first.onset <= 200
                and 10 <= second.onset - first.onset <= 20
                and 50 <= first.duration <= 80
                and 50 <= second.duration <= 80
            ):
                raise ValueError("OVERLAPPING_DOUBLE ledger is outside registered support")

    def active_mask(self, physical_step: int) -> np.ndarray:
        mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        for entry in self.intervals:
            if entry.contains(physical_step):
                mask[entry.owner] = False
        return mask

    @property
    def ledger_id(self) -> str:
        entries = ",".join(
            f"{item.owner}:{item.onset}:{item.duration}" for item in self.intervals
        )
        return f"{self.cell.value}/{int(self.episode_id)}/{entries}"


def _integer(namespace: Sequence[int], low: int, high: int) -> int:
    rng = np.random.default_rng(np.random.SeedSequence([int(x) for x in namespace]))
    return int(rng.integers(int(low), int(high) + 1))


def make_uav_loss_ledger(
    cell: LossCell | str,
    episode_id: int,
    *,
    ledger_seed: int,
) -> UAVLossLedger:
    """Sample an exact immutable ledger with independent field namespaces."""

    chosen = LossCell(cell)
    episode = int(episode_id)
    base = (int(ledger_seed), episode)
    if chosen is LossCell.NO_DISTURBANCE:
        intervals: tuple[LossInterval, ...] = ()
    elif chosen is LossCell.IID_SINGLE:
        intervals = (
            LossInterval(
                owner=_integer((*base, 1), 0, PHYSICAL_UAVS - 1),
                onset=_integer((*base, 2), 120, 240),
                duration=_integer((*base, 3), 30, 60),
            ),
        )
    elif chosen is LossCell.LATE_LONG_SINGLE:
        intervals = (
            LossInterval(
                owner=_integer((*base, 1), 0, PHYSICAL_UAVS - 1),
                onset=_integer((*base, 2), 280, 330),
                duration=_integer((*base, 3), 70, 100),
            ),
        )
    else:
        first_owner = _integer((*base, 1), 0, PHYSICAL_UAVS - 1)
        second_rank = _integer((*base, 4), 0, PHYSICAL_UAVS - 2)
        second_owner = second_rank + int(second_rank >= first_owner)
        first_onset = _integer((*base, 2), 140, 200)
        intervals = (
            LossInterval(
                owner=first_owner,
                onset=first_onset,
                duration=_integer((*base, 3), 50, 80),
            ),
            LossInterval(
                owner=second_owner,
                onset=first_onset + _integer((*base, 5), 10, 20),
                duration=_integer((*base, 6), 50, 80),
            ),
        )
    return UAVLossLedger(cell=chosen, episode_id=episode, intervals=intervals)


@dataclass(frozen=True)
class UAVCurrentView:
    observations: np.ndarray
    active_mask: np.ndarray
    critic_state: np.ndarray
    physical_positions: np.ndarray
    physical_step: int


@dataclass(frozen=True)
class UAVTransition:
    view: UAVCurrentView
    reward: float
    qos_satisfaction_ratio: float
    terminated: bool
    truncated: bool
    executed_action_mask: np.ndarray


class UAVTemporaryServiceLossEnv(UAVEnergyAwareRelayEnv):
    """Scenario-7/S1 with deterministic ledger-driven service availability."""

    def __init__(
        self,
        ledger: UAVLossLedger,
        environment_seed: int,
        env_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.loss_ledger = ledger
        self.environment_seed = int(environment_seed)
        self._reset_namespace_rngs(self.environment_seed)
        self._service_active_mask = np.ones(PHYSICAL_UAVS, dtype=np.bool_)
        self._last_mask_step = -1
        kwargs = dict(env_kwargs or {})
        unsupported = set(kwargs).difference({"render_mode"})
        if unsupported:
            raise ValueError(
                "env_kwargs cannot override frozen S7-S1 science fields: "
                + ", ".join(sorted(unsupported))
            )
        config = Config("S7-S1")
        super().__init__(config=config, seed=self.environment_seed, **kwargs)
        if self.n_uavs != PHYSICAL_UAVS or self.action_dim != ACTION_DIM:
            raise RuntimeError("S7-S1 temporary-loss wrapper requires physical width 8/action 4")

    @staticmethod
    def _namespace_random_state(seed: int, namespace: int) -> np.random.RandomState:
        derived = np.random.SeedSequence([int(seed), int(namespace)]).generate_state(1)[0]
        return np.random.RandomState(int(derived))

    def _reset_namespace_rngs(self, seed: int) -> None:
        # Namespace 1 owns initial physical state, 2 user generation/motion,
        # and 3 channel randomness.  Ledger and action sources live outside the
        # environment and therefore cannot advance any of these streams.
        self._initial_rng = self._namespace_random_state(seed, 1)
        self._user_rng = self._namespace_random_state(seed, 2)
        self._channel_rng = self._namespace_random_state(seed, 3)

    def _with_namespace_rng(self, attribute: str, method: Any, *args: Any, **kwargs: Any):
        previous = getattr(self, "np_random", None)
        self.np_random = getattr(self, attribute)
        try:
            return method(*args, **kwargs)
        finally:
            if previous is not None:
                self.np_random = previous

    def _init_ground_bs(self):
        return self._with_namespace_rng("_initial_rng", super()._init_ground_bs)

    def _init_uav_positions(self):
        return self._with_namespace_rng("_initial_rng", super()._init_uav_positions)

    def _init_charging_stations(self, randomize: bool | None = None):
        return self._with_namespace_rng(
            "_initial_rng", super()._init_charging_stations, randomize
        )

    def _generate_user_positions(self):
        return self._with_namespace_rng("_user_rng", super()._generate_user_positions)

    def _init_user_velocities(self):
        return self._with_namespace_rng("_user_rng", super()._init_user_velocities)

    def _initialize_user_waypoints_rpgm(self):
        return self._with_namespace_rng(
            "_user_rng", super()._initialize_user_waypoints_rpgm
        )

    def _move_users(self):
        return self._with_namespace_rng("_user_rng", super()._move_users)

    def _update_channel_state(self):
        return self._with_namespace_rng("_channel_rng", super()._update_channel_state)

    def _compute_link_sinr(self, tx_type, tx_idx, rx_type, rx_idx, rx_power):
        """S7-S1 link SINR with service-lost UAVs absent as interferers."""

        interference_radius = self._compute_interference_radius()
        interference_powers_linear: list[float] = []
        if rx_type == "uav":
            rx_pos = self.uav_positions[rx_idx]
        elif rx_type == "ground_bs":
            rx_pos = self.ground_bs_positions[rx_idx]
        else:
            rx_pos = None

        if rx_pos is not None:
            for interferer in range(self.n_uavs):
                if self._is_uav_unavailable(interferer):
                    continue
                if (tx_type == "uav" and interferer == tx_idx) or (
                    rx_type == "uav" and interferer == rx_idx
                ):
                    continue
                interferer_pos = self.uav_positions[interferer]
                if self._compute_distance(interferer_pos, rx_pos) > interference_radius:
                    continue
                if rx_type == "uav":
                    path_loss = self._compute_air_to_air_path_loss(interferer_pos, rx_pos)
                else:
                    path_loss = self._compute_air_to_ground_path_loss(interferer_pos, rx_pos)
                received_linear = 10 ** ((self.tx_power - path_loss) / 10)
                interference_powers_linear.append(
                    received_linear * self.aclr_linear if self.use_fdma else received_linear
                )

        interference_plus_noise = self._noise_power_linear_mw() + np.sum(
            interference_powers_linear
        )
        return rx_power - 10 * np.log10(interference_plus_noise)

    def _compute_uav_to_user_sinr(
        self, uav_idx, user_idx, rx_power, step_cache=None
    ):
        """S7-S1 access-link SINR with no emission from lost service rows."""

        if step_cache is None:
            step_cache = self._current_step_communication_cache()
        interference_radius = self._compute_interference_radius()
        user_pos = self.user_positions[user_idx]
        interference_powers_linear: list[float] = []
        for interferer in range(self.n_uavs):
            if interferer == uav_idx or self._is_uav_unavailable(interferer):
                continue
            interferer_pos = self.uav_positions[interferer]
            if self._compute_distance(interferer_pos, user_pos) > interference_radius:
                continue
            path_loss = self._cached_user_path_loss(
                interferer, user_idx, step_cache=step_cache
            )
            received_linear = 10 ** ((self.tx_power - path_loss) / 10)
            interference_powers_linear.append(
                received_linear * self.aclr_linear if self.use_fdma else received_linear
            )

        interference_plus_noise = self._noise_power_linear_mw() + np.sum(
            interference_powers_linear
        )
        return rx_power - 10 * np.log10(interference_plus_noise)

    @property
    def service_active_mask(self) -> np.ndarray:
        self._synchronize_service_mask()
        return self._service_active_mask.copy()

    def _is_uav_unavailable(self, uav_idx: int) -> bool:
        service = getattr(self, "_service_active_mask", None)
        if service is not None and not bool(service[int(uav_idx)]):
            return True
        return super()._is_uav_unavailable(uav_idx)

    def _communication_unavailable_mask(self) -> np.ndarray:
        unavailable = super()._communication_unavailable_mask()
        service = getattr(self, "_service_active_mask", None)
        if service is not None:
            unavailable |= ~np.asarray(service, dtype=bool)
        return unavailable

    def _is_uav_motion_disabled(self, uav_idx: int) -> bool:
        service = getattr(self, "_service_active_mask", None)
        if service is not None and not bool(service[int(uav_idx)]):
            return True
        return super()._is_uav_motion_disabled(uav_idx)

    def _update_uav_failures(self) -> None:
        # The registered source is separate from Scenario-7's stochastic S4
        # failure process and must not consume its RNG or cutoff penalty path.
        self.uav_failure_timers[:] = 0
        self.uav_failed[:] = False

    def _synchronize_service_mask(self, *, force: bool = False) -> bool:
        step = int(getattr(self, "current_step", 0))
        if not force and step == self._last_mask_step:
            return False
        new_mask = self.loss_ledger.active_mask(step)
        changed = not np.array_equal(new_mask, self._service_active_mask)
        self._service_active_mask = new_mask
        self._last_mask_step = step
        if changed and hasattr(self, "connections"):
            self._update_channel_state()
            self._update_uav_connections()
            self._compute_routing_paths()
        return changed

    def reset(self, seed: int | None = None, options: Any = None):
        actual_seed = self.environment_seed if seed is None else int(seed)
        self._reset_namespace_rngs(actual_seed)
        observations, infos = super().reset(seed=actual_seed, options=options)
        self._last_mask_step = -1
        mask_changed = self._synchronize_service_mask(force=True)
        if mask_changed or bool(getattr(self, "_disable_step_view_reuse", False)):
            observations = {agent: self._get_observation(agent) for agent in self.agents}
            observations = self._update_observations_dict(observations)
        return observations, infos

    def _actor_observation(
        self, owner: int, raw_observation: np.ndarray | None = None
    ) -> np.ndarray:
        """Faithful S7-S1 local observation with only owner leakage removed."""

        if raw_observation is None:
            raw_observation = self._get_observation(
                self.possible_agents[int(owner)]
            )["obs"]
        raw = np.asarray(raw_observation, dtype=np.float32).copy()
        if raw.shape != (self.obs_dim,):
            raise RuntimeError("raw S7-S1 actor observation width drifted")
        own = np.asarray(self.uav_positions[owner], dtype=np.float64)
        height_span = max(float(self.height_range[1] - self.height_range[0]), 1.0)
        active_peers = [
            peer
            for peer in np.flatnonzero(self._service_active_mask)
            if int(peer) != int(owner)
        ]
        active_peers.sort(
            key=lambda peer: (
                float(np.linalg.norm(self.uav_positions[peer] - own)),
                float((self.uav_positions[peer] - own)[0]),
                float((self.uav_positions[peer] - own)[1]),
                float((self.uav_positions[peer] - own)[2]),
            )
        )

        # Replace the raw nearest-UAV field, which otherwise considers an
        # inactive physical peer.
        raw[3:6] = 0.0
        if active_peers:
            relative = self.uav_positions[active_peers[0]] - own
            raw[3:6] = (
                float(np.linalg.norm(relative)) / self.area_size,
                relative[0] / self.area_size,
                relative[1] / self.area_size,
            )

        user_fields = 7 if self.predictive_handover else (6 if self.enable_soft_handover else 5)
        peer_start = 3 + 3 + 5 + self.max_observed_users * user_fields
        peer_stop = peer_start + self.max_observed_uavs * 4
        raw[peer_start:peer_stop] = 0.0
        local_active = [
            peer
            for peer in active_peers
            if np.linalg.norm(self.uav_positions[peer] - own) <= self.observation_radius
        ][: self.max_observed_uavs]
        for row, peer in enumerate(local_active):
            relative = np.asarray(self.uav_positions[peer] - own, dtype=np.float64)
            normalized_sinr = np.clip(
                (self._compute_uav_to_uav_sinr(owner, peer) + 10.0) / 50.0,
                0.0,
                1.0,
            )
            start = peer_start + row * 4
            raw[start : start + 4] = (
                relative[0] / self.area_size,
                relative[1] / self.area_size,
                (relative[2] - self.height_range[0]) / height_span,
                normalized_sinr,
            )

        # Repack the fixed eight owner-indexed energy records as self first,
        # then anonymous active peers in the same current ordering.  The S1
        # values and station tail remain byte-for-byte raw semantics.
        base_width = self.obs_dim - self.energy_obs_extra_dim
        energy_start = base_width
        energy_stop = energy_start + self.max_energy_observed_uavs * self.energy_uav_obs_dim
        owner_records = raw[energy_start:energy_stop].reshape(
            self.max_energy_observed_uavs, self.energy_uav_obs_dim
        ).copy()
        anonymous = np.zeros_like(owner_records)
        presentation = [int(owner), *active_peers]
        for row, peer in enumerate(presentation[: self.max_energy_observed_uavs]):
            anonymous[row] = owner_records[peer]
        raw[energy_start:energy_stop] = anonymous.reshape(-1)
        return raw

    def _build_current_view(
        self,
        *,
        raw_observations: Mapping[str, Mapping[str, np.ndarray]] | None = None,
        critic_state: np.ndarray | None = None,
    ) -> UAVCurrentView:
        observations = np.zeros((PHYSICAL_UAVS, self.obs_dim), dtype=np.float32)
        for owner in np.flatnonzero(self._service_active_mask):
            raw = None
            if raw_observations is not None:
                raw = raw_observations[self.possible_agents[int(owner)]]["obs"]
            observations[owner] = self._actor_observation(int(owner), raw)
        if critic_state is None:
            critic_state = self._get_state()
        return UAVCurrentView(
            observations=observations,
            active_mask=self._service_active_mask.copy(),
            critic_state=np.asarray(critic_state, dtype=np.float32).copy(),
            physical_positions=np.asarray(self.uav_positions, dtype=np.float64).copy(),
            physical_step=int(self.current_step),
        )

    def current_view(self) -> UAVCurrentView:
        self._synchronize_service_mask()
        return self._build_current_view()

    def step(self, actions: np.ndarray) -> UAVTransition:
        self._synchronize_service_mask()
        dense_actions = np.asarray(actions, dtype=np.float32)
        if dense_actions.shape != (PHYSICAL_UAVS, ACTION_DIM):
            raise ValueError("temporary-loss action must have shape [8, 4]")
        if not np.isfinite(dense_actions).all() or np.any(np.abs(dense_actions) > 1.0):
            raise ValueError("temporary-loss action must be finite and within [-1, 1]")
        executed_mask = self._service_active_mask.copy()
        before = np.asarray(self.uav_positions, dtype=np.float64).copy()
        action_dict = {
            agent: dense_actions[index].copy()
            for index, agent in enumerate(self.possible_agents)
            if executed_mask[index]
        }
        raw_observations, rewards, terminations, truncations, infos = super().step(
            action_dict
        )
        if not np.array_equal(self.uav_positions[~executed_mask], before[~executed_mask]):
            raise RuntimeError("inactive UAV position changed during service loss")
        if not np.array_equal(
            np.asarray(self.last_actual_velocities)[~executed_mask],
            np.zeros((int((~executed_mask).sum()), 3), dtype=float),
        ):
            raise RuntimeError("inactive UAV velocity was not exactly zero")
        reward = float(np.mean(tuple(rewards.values()))) if rewards else 0.0
        first_info = infos.get(self.possible_agents[0], {})
        reward_info = first_info.get("reward_info", {})
        qos = float(reward_info.get("qos_satisfaction_ratio", 0.0))
        terminated = bool(all(terminations.values())) if terminations else False
        truncated = bool(all(truncations.values())) if truncations else False
        mask_changed = self._synchronize_service_mask(force=True)
        reuse_step_outputs = not mask_changed and not bool(
            getattr(self, "_disable_step_view_reuse", False)
        )
        next_state = first_info.get("next_state") if reuse_step_outputs else None
        return UAVTransition(
            view=self._build_current_view(
                raw_observations=raw_observations if reuse_step_outputs else None,
                critic_state=next_state,
            ),
            reward=reward,
            qos_satisfaction_ratio=qos,
            terminated=terminated,
            truncated=truncated,
            executed_action_mask=executed_mask,
        )


def make_uav_environment(
    ledger: UAVLossLedger,
    environment_seed: int,
    env_kwargs: Mapping[str, Any] | None = None,
) -> UAVTemporaryServiceLossEnv:
    return UAVTemporaryServiceLossEnv(ledger, environment_seed, env_kwargs)


def _view_payload(view: UAVCurrentView) -> dict[str, Any]:
    return {
        "observations": view.observations,
        "active_mask": view.active_mask,
        "critic_state": view.critic_state,
        "physical_positions": view.physical_positions,
        "physical_step": view.physical_step,
    }


def _worker_main(connection: Connection) -> None:
    environment: UAVTemporaryServiceLossEnv | None = None
    no_reallocation = NoReallocationController()
    constructive_controller: FullLedgerConstructiveController | None = None
    try:
        connection.send({"ok": True, "kind": "ready"})
        while True:
            request = connection.recv()
            command = request.get("command")
            if command == "reset":
                if environment is not None:
                    environment.close()
                environment = make_uav_environment(
                    request["ledger"], request["environment_seed"], request.get("env_kwargs")
                )
                environment.reset()
                no_reallocation.reset()
                constructive_controller = FullLedgerConstructiveController(
                    environment.loss_ledger
                )
                connection.send({"ok": True, "view": _view_payload(environment.current_view())})
            elif command == "step":
                if environment is None:
                    raise RuntimeError("worker step requested before reset")
                transition = environment.step(request["actions"])
                connection.send(
                    {
                        "ok": True,
                        "view": _view_payload(transition.view),
                        "reward": transition.reward,
                        "qos": transition.qos_satisfaction_ratio,
                        "terminated": transition.terminated,
                        "truncated": transition.truncated,
                        "executed_action_mask": transition.executed_action_mask,
                    }
                )
            elif command == "controller_step":
                if environment is None:
                    raise RuntimeError("worker controller step requested before reset")
                active_mask = environment.service_active_mask
                physical_positions = np.asarray(
                    environment.uav_positions, dtype=np.float64
                ).copy()
                kind = request["kind"]
                if kind == "constructive":
                    if constructive_controller is None:
                        raise RuntimeError("constructive controller was not reset")
                    actions = constructive_controller.act(
                        physical_positions=physical_positions,
                        user_positions=environment.user_positions,
                        ground_bs_positions=environment.ground_bs_positions,
                        active_mask=active_mask,
                        max_speed=environment.max_speed,
                        max_vertical_speed=environment.max_vertical_speed_mps,
                        time_step=environment.time_step,
                        height_range=environment.height_range,
                    )
                elif kind == "no_reallocation":
                    # This branch is deliberately ledger-blind.  It sees only
                    # the same current mask and physical state as an ordinary
                    # evaluation controller.
                    candidate_targets = constructive_target_layout(
                        physical_positions=physical_positions,
                        user_positions=environment.user_positions,
                        ground_bs_positions=environment.ground_bs_positions,
                        active_mask=active_mask,
                        height_range=environment.height_range,
                    )
                    actions = no_reallocation.act_for_layout(
                        candidate_targets=candidate_targets,
                        physical_positions=physical_positions,
                        active_mask=active_mask,
                        max_speed=environment.max_speed,
                        max_vertical_speed=environment.max_vertical_speed_mps,
                        time_step=environment.time_step,
                    )
                else:
                    raise ValueError(f"unknown UAV controller kind: {kind!r}")
                transition = environment.step(actions)
                connection.send(
                    {
                        "ok": True,
                        "view": _view_payload(transition.view),
                        "reward": transition.reward,
                        "qos": transition.qos_satisfaction_ratio,
                        "terminated": transition.terminated,
                        "truncated": transition.truncated,
                        "executed_action_mask": transition.executed_action_mask,
                    }
                )
            elif command == "spec":
                if environment is None:
                    raise RuntimeError("worker spec requested before reset")
                connection.send(
                    {
                        "ok": True,
                        "observation_dim": int(
                            environment.current_view().observations.shape[-1]
                        ),
                        "critic_state_dim": int(environment._get_state().size),
                        "physical_width": PHYSICAL_UAVS,
                        "action_dim": ACTION_DIM,
                    }
                )
            elif command == "close":
                if environment is not None:
                    environment.close()
                connection.send({"ok": True, "kind": "closed"})
                return
            else:
                raise ValueError(f"unknown UAV worker command: {command!r}")
    except BaseException:
        try:
            connection.send({"ok": False, "traceback": traceback.format_exc()})
        finally:
            if environment is not None:
                environment.close()
    finally:
        connection.close()


def _stack_views(payloads: Sequence[Mapping[str, Any]]) -> UAVCurrentView:
    return UAVCurrentView(
        observations=np.stack([row["observations"] for row in payloads]),
        active_mask=np.stack([row["active_mask"] for row in payloads]),
        critic_state=np.stack([row["critic_state"] for row in payloads]),
        physical_positions=np.stack([row["physical_positions"] for row in payloads]),
        physical_step=int(payloads[0]["physical_step"]),
    )


class PersistentUAVVectorEnv:
    """Persistent spawn workers; policy inference and optimization stay local."""

    def __init__(
        self,
        ledgers: Sequence[UAVLossLedger],
        environment_seeds: Sequence[int],
        *,
        env_kwargs: Mapping[str, Any] | None = None,
        start_method: str = "spawn",
    ) -> None:
        if not ledgers or len(ledgers) != len(environment_seeds):
            raise ValueError("vector environment requires aligned non-empty episode rows")
        self.count = len(ledgers)
        self.env_kwargs = dict(env_kwargs or {})
        context = mp.get_context(start_method)
        self._connections: list[Connection] = []
        self._processes: list[mp.Process] = []
        self._closed = False
        for index in range(self.count):
            parent, child = context.Pipe()
            process = context.Process(
                target=_worker_main,
                args=(child,),
                name=f"uav-g1-env-{index}",
            )
            process.start()
            child.close()
            self._connections.append(parent)
            self._processes.append(process)
        self._receive_all()
        self._view = self.reset(ledgers=ledgers, environment_seeds=environment_seeds)

    def _receive_all(self) -> list[dict[str, Any]]:
        replies: list[dict[str, Any]] = []
        for index, connection in enumerate(self._connections):
            try:
                reply = connection.recv()
            except (EOFError, BrokenPipeError) as error:
                raise RuntimeError(f"UAV worker {index} exited without a terminal reply") from error
            if not reply.get("ok", False):
                raise RuntimeError(f"UAV worker {index} failed:\n{reply.get('traceback', '')}")
            replies.append(reply)
        return replies

    @property
    def current_view(self) -> UAVCurrentView:
        return self._view

    def reset(
        self,
        *,
        ledgers: Sequence[UAVLossLedger],
        environment_seeds: Sequence[int],
    ) -> UAVCurrentView:
        if len(ledgers) != self.count or len(environment_seeds) != self.count:
            raise ValueError("vector reset row count changed")
        for connection, ledger, seed in zip(self._connections, ledgers, environment_seeds):
            connection.send(
                {
                    "command": "reset",
                    "ledger": ledger,
                    "environment_seed": int(seed),
                    "env_kwargs": self.env_kwargs,
                }
            )
        replies = self._receive_all()
        self._view = _stack_views([reply["view"] for reply in replies])
        return self._view

    def spec(self) -> dict[str, int]:
        for connection in self._connections:
            connection.send({"command": "spec"})
        replies = self._receive_all()
        specs = [{key: value for key, value in row.items() if key != "ok"} for row in replies]
        if any(spec != specs[0] for spec in specs[1:]):
            raise RuntimeError("vector worker specifications differ")
        return specs[0]

    def step(self, actions: np.ndarray) -> tuple[UAVCurrentView, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        values = np.asarray(actions, dtype=np.float32)
        if values.shape != (self.count, PHYSICAL_UAVS, ACTION_DIM):
            raise ValueError("vector action shape mismatch")
        for connection, row in zip(self._connections, values):
            connection.send({"command": "step", "actions": row})
        replies = self._receive_all()
        self._view = _stack_views([reply["view"] for reply in replies])
        return (
            self._view,
            np.asarray([reply["reward"] for reply in replies], dtype=np.float32),
            np.asarray([reply["qos"] for reply in replies], dtype=np.float64),
            np.asarray([reply["terminated"] or reply["truncated"] for reply in replies], dtype=np.bool_),
            np.stack([reply["executed_action_mask"] for reply in replies]),
        )

    def controller_step(
        self, kind: str
    ) -> tuple[UAVCurrentView, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if kind not in {"constructive", "no_reallocation"}:
            raise ValueError("unknown UAV evaluation controller")
        expected_mask = self._view.active_mask.copy()
        for connection in self._connections:
            connection.send({"command": "controller_step", "kind": kind})
        replies = self._receive_all()
        executed = np.stack([reply["executed_action_mask"] for reply in replies])
        if not np.array_equal(executed, expected_mask):
            raise RuntimeError("controller execution mask differs from pre-action service mask")
        self._view = _stack_views([reply["view"] for reply in replies])
        return (
            self._view,
            np.asarray([reply["reward"] for reply in replies], dtype=np.float32),
            np.asarray([reply["qos"] for reply in replies], dtype=np.float64),
            np.asarray([reply["terminated"] or reply["truncated"] for reply in replies], dtype=np.bool_),
            executed,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for connection, process in zip(self._connections, self._processes):
            if process.is_alive():
                try:
                    connection.send({"command": "close"})
                except (BrokenPipeError, EOFError):
                    pass
        for connection, process in zip(self._connections, self._processes):
            if process.is_alive():
                try:
                    reply = connection.recv()
                    if not reply.get("ok", False):
                        raise RuntimeError(reply.get("traceback", "UAV worker close failed"))
                except EOFError:
                    pass
            process.join(timeout=10.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)
            connection.close()

    def __enter__(self) -> "PersistentUAVVectorEnv":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()


class MatchedContinuousRecurrentPolicy(ContinuousRosterPolicy):
    """One matched tanh-Gaussian actor-critic with selectable row routing."""

    def __init__(
        self,
        observation_dim: int,
        critic_state_dim: int,
        *,
        hidden_dim: int = 64,
        routing_mode: str,
    ) -> None:
        if routing_mode not in ROUTING_MODES:
            raise ValueError("unknown UAV G1 routing mode")
        super().__init__(
            observation_dim,
            critic_state_dim,
            member_capacity=PHYSICAL_UAVS,
            action_dim=ACTION_DIM,
            hidden_dim=hidden_dim,
        )
        self.routing_mode = routing_mode


@dataclass
class UAVTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    critic_states: torch.Tensor
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    dones: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    qos: np.ndarray
    ledger_ids: tuple[str, ...]

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


def make_action_noise(
    episode_ids: Iterable[int],
    *,
    action_seed: int,
    horizon: int = HORIZON,
) -> np.ndarray:
    rows = []
    for episode_id in episode_ids:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(action_seed), int(episode_id), 0])
        )
        rows.append(rng.standard_normal((int(horizon), PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32))
    if not rows:
        raise ValueError("action noise requires at least one episode")
    return np.stack(rows, axis=1)


def collect_uav_trajectory(
    model: MatchedContinuousRecurrentPolicy,
    vector_env: PersistentUAVVectorEnv,
    *,
    episode_ids: Sequence[int],
    action_seed: int,
    device: torch.device,
    horizon: int = HORIZON,
) -> UAVTrajectory:
    if len(episode_ids) != vector_env.count:
        raise ValueError("episode IDs do not align with vector workers")
    noise = make_action_noise(episode_ids, action_seed=action_seed, horizon=horizon)
    hidden = torch.zeros(
        (vector_env.count, PHYSICAL_UAVS, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    rows: dict[str, list[torch.Tensor]] = {
        name: []
        for name in (
            "observations",
            "active_mask",
            "critic_states",
            "actions",
            "pre_tanh_actions",
            "old_log_probs",
            "old_values",
            "rewards",
            "dones",
            "hidden_before",
            "hidden_after",
            "prefix_action_sums",
        )
    }
    qos_rows: list[np.ndarray] = []
    view = vector_env.current_view
    model.eval()
    with torch.no_grad():
        for time in range(int(horizon)):
            observations = torch.as_tensor(view.observations, device=device)
            active_mask = torch.as_tensor(view.active_mask, device=device)
            critic_state = torch.as_tensor(view.critic_state, device=device)
            hidden_before = hidden.clone()
            output = model.forward_step(
                observations=observations,
                active_mask=active_mask,
                critic_state=critic_state,
                hidden=hidden,
                sampling_noise=torch.as_tensor(noise[time], device=device),
            )
            next_view, rewards, qos, dones, executed_mask = vector_env.step(
                output.actions.detach().cpu().numpy()
            )
            if not np.array_equal(executed_mask, view.active_mask):
                raise RuntimeError("collected likelihood mask differs from executed service mask")
            rows["observations"].append(observations.cpu())
            rows["active_mask"].append(active_mask.cpu())
            rows["critic_states"].append(critic_state.cpu())
            rows["actions"].append(output.actions.cpu())
            rows["pre_tanh_actions"].append(output.pre_tanh_actions.cpu())
            rows["old_log_probs"].append(output.token_log_probs.cpu())
            rows["old_values"].append(output.value.cpu())
            rows["rewards"].append(torch.as_tensor(rewards))
            rows["dones"].append(torch.as_tensor(dones))
            rows["hidden_before"].append(hidden_before.cpu())
            rows["hidden_after"].append(output.next_hidden.cpu())
            rows["prefix_action_sums"].append(output.prefix_action_sums.cpu())
            qos_rows.append(qos)
            hidden = output.next_hidden
            view = next_view
    return UAVTrajectory(
        observations=torch.stack(rows["observations"]),
        active_mask=torch.stack(rows["active_mask"]),
        critic_states=torch.stack(rows["critic_states"]),
        actions=torch.stack(rows["actions"]),
        pre_tanh_actions=torch.stack(rows["pre_tanh_actions"]),
        old_log_probs=torch.stack(rows["old_log_probs"]),
        old_values=torch.stack(rows["old_values"]),
        rewards=torch.stack(rows["rewards"]),
        dones=torch.stack(rows["dones"]),
        hidden_before=torch.stack(rows["hidden_before"]),
        hidden_after=torch.stack(rows["hidden_after"]),
        prefix_action_sums=torch.stack(rows["prefix_action_sums"]),
        qos=np.stack(qos_rows),
        ledger_ids=tuple(str(value) for value in episode_ids),
    )


def evaluate_uav_policy(
    model: MatchedContinuousRecurrentPolicy,
    vector_env: PersistentUAVVectorEnv,
    *,
    episode_ids: Sequence[int],
    action_seed: int,
    device: torch.device,
    deterministic: bool,
    horizon: int = HORIZON,
) -> np.ndarray:
    """Run paired batched learned evaluation and return QoS as [time, episode]."""

    if len(episode_ids) != vector_env.count:
        raise ValueError("evaluation episode IDs do not align with vector workers")
    noise = None if deterministic else make_action_noise(
        episode_ids, action_seed=action_seed, horizon=horizon
    )
    hidden = torch.zeros(
        (vector_env.count, PHYSICAL_UAVS, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    view = vector_env.current_view
    qos_rows: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for time in range(int(horizon)):
            kwargs: dict[str, Any]
            if deterministic:
                kwargs = {"deterministic": True}
            else:
                assert noise is not None
                kwargs = {"sampling_noise": torch.as_tensor(noise[time], device=device)}
            output = model.forward_step(
                observations=torch.as_tensor(view.observations, device=device),
                active_mask=torch.as_tensor(view.active_mask, device=device),
                critic_state=torch.as_tensor(view.critic_state, device=device),
                hidden=hidden,
                **kwargs,
            )
            expected_mask = view.active_mask.copy()
            view, _rewards, qos, _dones, executed_mask = vector_env.step(
                output.actions.detach().cpu().numpy()
            )
            if not np.array_equal(executed_mask, expected_mask):
                raise RuntimeError("evaluation likelihood mask differs from executed service mask")
            hidden = output.next_hidden
            qos_rows.append(qos)
    return np.stack(qos_rows)


def evaluate_uav_controller(
    vector_env: PersistentUAVVectorEnv,
    *,
    kind: str,
    horizon: int = HORIZON,
) -> np.ndarray:
    """Run a paired batched evaluation-only physical controller."""

    qos_rows: list[np.ndarray] = []
    for _ in range(int(horizon)):
        _view, _rewards, qos, _dones, _executed = vector_env.controller_step(kind)
        qos_rows.append(qos)
    return np.stack(qos_rows)


@dataclass
class UAVReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor


def replay_uav_trajectory(
    model: MatchedContinuousRecurrentPolicy,
    trajectory: UAVTrajectory,
    *,
    device: torch.device,
    detach_initial_hidden: bool = True,
) -> UAVReplay:
    horizon, batch = trajectory.rewards.shape
    hidden = trajectory.hidden_before[0].to(device)
    if detach_initial_hidden:
        hidden = hidden.detach()
    output_rows: list[ContinuousStepOutput] = []
    for time in range(horizon):
        output = model.forward_step(
            observations=trajectory.observations[time].to(device),
            active_mask=trajectory.active_mask[time].to(device),
            critic_state=trajectory.critic_states[time].to(device),
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time].to(device),
        )
        output_rows.append(output)
        hidden = output.next_hidden
        if trajectory.dones[time].any():
            done = trajectory.dones[time].to(device).view(batch, 1, 1)
            hidden = torch.where(done, torch.zeros_like(hidden), hidden)
    return UAVReplay(
        log_probs=torch.stack([row.token_log_probs for row in output_rows]),
        entropies=torch.stack([row.token_entropies for row in output_rows]),
        values=torch.stack([row.value for row in output_rows]),
        hidden_after=torch.stack([row.next_hidden for row in output_rows]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in output_rows]),
        active_mask=trajectory.active_mask.to(device),
    )


def replay_errors(replay: UAVReplay, trajectory: UAVTrajectory) -> dict[str, float]:
    mask = replay.active_mask
    token = torch.abs(replay.log_probs - trajectory.old_log_probs.to(replay.log_probs.device))
    joint = torch.abs(
        torch.where(
            mask,
            replay.log_probs - trajectory.old_log_probs.to(replay.log_probs.device),
            0.0,
        ).sum(dim=-1)
    )
    inactive_logp = torch.where(mask, 0.0, replay.log_probs).abs()
    return {
        "logp_max_error": float(token[mask].max().detach().cpu()),
        "joint_logp_max_error": float(joint.max().detach().cpu()),
        "value_max_error": float(
            torch.abs(replay.values - trajectory.old_values.to(replay.values.device)).max().detach().cpu()
        ),
        "hidden_max_error": float(
            torch.abs(replay.hidden_after - trajectory.hidden_after.to(replay.hidden_after.device)).max().detach().cpu()
        ),
        "prefix_max_error": float(
            torch.abs(
                replay.prefix_action_sums
                - trajectory.prefix_action_sums.to(replay.prefix_action_sums.device)
            ).max().detach().cpu()
        ),
        "inactive_logp_max_abs": float(inactive_logp.max().detach().cpu()),
    }


def compute_gae(
    rewards: torch.Tensor,
    values: torch.Tensor,
    dones: torch.Tensor,
    *,
    gamma: float = GAMMA,
    gae_lambda: float = GAE_LAMBDA,
) -> tuple[torch.Tensor, torch.Tensor]:
    advantages = torch.zeros_like(rewards)
    running = torch.zeros(rewards.shape[1], dtype=rewards.dtype, device=rewards.device)
    next_value = torch.zeros_like(running)
    for time in range(rewards.shape[0] - 1, -1, -1):
        nonterminal = (~dones[time]).to(rewards.dtype)
        delta = rewards[time] + gamma * next_value * nonterminal - values[time]
        running = delta + gamma * gae_lambda * nonterminal * running
        advantages[time] = running
        next_value = values[time]
    return advantages, advantages + values


def ppo_loss(
    replay: UAVReplay,
    trajectory: UAVTrajectory,
    advantages: torch.Tensor,
    returns: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_log_probs = trajectory.old_log_probs.to(device)
    old_values = trajectory.old_values.to(device)
    normalized_advantage = (advantages.to(device) - advantages.mean()) / (
        advantages.std(unbiased=False) + 1e-8
    )
    ratio = torch.exp(replay.log_probs - old_log_probs)
    expanded = normalized_advantage.unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    policy_loss = -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()
    entropy = (
        torch.where(mask, replay.entropies, 0.0).sum(dim=-1) / active_count
    ).mean()
    clipped = old_values + torch.clamp(replay.values - old_values, -VALUE_CLIP, VALUE_CLIP)
    value_loss = torch.maximum(
        torch.square(replay.values - returns.to(device)),
        torch.square(clipped - returns.to(device)),
    ).mean()
    total = policy_loss + VALUE_COEFFICIENT * value_loss - ENTROPY_COEFFICIENT * entropy
    clip_fraction = (
        torch.where(mask, (torch.abs(ratio - 1.0) > PPO_CLIP).to(ratio.dtype), 0.0).sum()
        / mask.sum().clamp_min(1)
    )
    return total, {
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "entropy": entropy,
        "clip_fraction": clip_fraction,
    }


def optimize_uav_update(
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: UAVTrajectory,
    *,
    device: torch.device,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, float]:
    advantages, returns = compute_gae(
        trajectory.rewards.to(device), trajectory.old_values.to(device), trajectory.dones.to(device)
    )
    model.train()
    replay = replay_uav_trajectory(model, trajectory, device=device)
    with torch.no_grad():
        errors = replay_errors(replay, trajectory)
    totals = {name: 0.0 for name in ("policy_loss", "value_loss", "entropy", "clip_fraction", "gradient_norm")}
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_uav_trajectory(model, trajectory, device=device)
        loss, metrics = ppo_loss(replay, trajectory, advantages, returns)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CLIP)
        finite = finite and bool(torch.isfinite(loss)) and bool(torch.isfinite(gradient_norm))
        optimizer.step()
        for name in ("policy_loss", "value_loss", "entropy", "clip_fraction"):
            totals[name] += float(metrics[name].detach().cpu())
        totals["gradient_norm"] += float(gradient_norm.detach().cpu())
    for name in totals:
        totals[name] /= float(ppo_passes)
    totals.update(errors)
    totals["finite_update"] = float(finite)
    totals["optimizer_steps"] = float(ppo_passes)
    return totals


def event_mask(ledger: UAVLossLedger, *, horizon: int = HORIZON) -> np.ndarray:
    mask = np.zeros(int(horizon), dtype=np.bool_)
    for entry in ledger.intervals:
        mask[entry.onset : min(entry.rejoin, horizon)] = True
    return mask


def rejoin_mask(ledger: UAVLossLedger, *, horizon: int = HORIZON) -> np.ndarray:
    mask = np.zeros(int(horizon), dtype=np.bool_)
    for entry in ledger.intervals:
        mask[entry.rejoin : min(entry.rejoin + REJOIN_WINDOW, horizon)] = True
    return mask


def compute_episode_metrics(qos: Sequence[float], ledger: UAVLossLedger) -> dict[str, float | None]:
    values = np.asarray(qos, dtype=np.float64)
    if values.shape != (HORIZON,) or not np.isfinite(values).all():
        raise ValueError("episode QoS must be one finite 500-step row")
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("QoS satisfaction ratio is outside [0, 1]")
    loss = event_mask(ledger)
    rejoin = rejoin_mask(ledger)
    affected = loss | rejoin
    deficit = np.maximum(0.0, QOS_TARGET - values) / QOS_TARGET
    j_event = 1.0 if not affected.any() else 1.0 - float(deficit[affected].mean())
    ordinary = ~affected
    if not ordinary.any():
        raise ValueError("registered ledger left no ordinary metric support")
    return {
        "J_event": j_event,
        "Q_ordinary": float(values[ordinary].mean()),
        "J_rejoin": None if not rejoin.any() else 1.0 - float(deficit[rejoin].mean()),
    }


def cell_access(j_event: float, q_ordinary: float) -> float:
    return min(float(j_event) / 0.80, float(q_ordinary) / 0.90)


def hierarchical_paired_bootstrap(
    paired_values: np.ndarray,
    *,
    resamples: int = 10_000,
    seed: int,
) -> tuple[float, float, float]:
    """Bootstrap [paired replicate, paired episode] rows without breaking pairs."""

    values = np.asarray(paired_values, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] <= 0 or values.shape[1] <= 0:
        raise ValueError("hierarchical bootstrap requires [replicate, episode]")
    rng = np.random.default_rng(int(seed))
    estimates = np.empty(int(resamples), dtype=np.float64)
    replicate_count, episode_count = values.shape
    for index in range(int(resamples)):
        replicate_indices = rng.integers(0, replicate_count, size=replicate_count)
        replicate_means = np.empty(replicate_count, dtype=np.float64)
        for row, replicate in enumerate(replicate_indices):
            episodes = rng.integers(0, episode_count, size=episode_count)
            replicate_means[row] = values[replicate, episodes].mean()
        estimates[index] = replicate_means.mean()
    return (
        float(np.quantile(estimates, 0.025)),
        float(values.mean()),
        float(np.quantile(estimates, 0.975)),
    )


def deterministic_service_centroids(
    user_positions: np.ndarray,
    cluster_count: int,
    *,
    iterations: int = 30,
) -> np.ndarray:
    """Pure deterministic k-means used by the registered feasibility layout."""

    users = np.asarray(user_positions, dtype=np.float64)
    if users.ndim != 2 or users.shape[1] < 2 or users.shape[0] <= 0:
        raise ValueError("service-centroid planner requires non-empty user positions")
    count = int(cluster_count)
    if not 1 <= count <= users.shape[0]:
        raise ValueError("service-centroid count is outside user support")
    user_xy = users[:, :2]
    seed_indices = np.linspace(0, user_xy.shape[0] - 1, count, dtype=int)
    centroids = user_xy[seed_indices].copy()
    for _ in range(int(iterations)):
        distances = np.sum(
            (user_xy[:, None, :] - centroids[None, :, :]) ** 2, axis=2
        )
        labels = np.argmin(distances, axis=1)
        updated = np.asarray(
            [
                user_xy[labels == cluster].mean(axis=0)
                if np.any(labels == cluster)
                else centroids[cluster]
                for cluster in range(count)
            ],
            dtype=np.float64,
        )
        if np.allclose(updated, centroids):
            break
        centroids = updated
    return centroids


def constructive_target_slots(
    *,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    active_count: int,
    relay_count: int | None = None,
    height_range: Sequence[float] = (50.0, 200.0),
) -> np.ndarray:
    """Return anonymous relay/service targets for one active fleet size."""

    count = int(active_count)
    if count < 2:
        raise ValueError("constructive layout requires at least two active UAVs")
    users = np.asarray(user_positions, dtype=np.float64)
    bases = np.asarray(ground_bs_positions, dtype=np.float64)
    relays = min(2, max(1, count - 1)) if relay_count is None else int(relay_count)
    if not 1 <= relays < count:
        raise ValueError("relay target count must leave at least one service target")
    service_count = count - relays
    centroids = deterministic_service_centroids(users, service_count)
    base = bases[:, :2].mean(axis=0)
    service_center = centroids.mean(axis=0)
    height = float(height_range[0])
    targets = np.empty((count, 3), dtype=np.float64)
    for rank in range(relays):
        fraction = (rank + 1.0) / (relays + 1.0)
        xy = (1.0 - fraction) * base + fraction * service_center
        targets[rank] = (xy[0], xy[1], height)
    for index, centroid in enumerate(centroids, start=relays):
        targets[index] = (centroid[0], centroid[1], height)
    return targets


def minimum_distance_target_assignment(
    *,
    physical_positions: np.ndarray,
    owners: Sequence[int],
    target_positions: np.ndarray,
) -> dict[int, int]:
    """Deterministically assign owners to anonymous targets with minimum travel."""

    positions = np.asarray(physical_positions, dtype=np.float64)
    owner_array = np.asarray(tuple(int(owner) for owner in owners), dtype=np.int64)
    targets = np.asarray(target_positions, dtype=np.float64)
    if positions.shape != (PHYSICAL_UAVS, 3):
        raise ValueError("minimum-distance assignment physical shape mismatch")
    if targets.shape != (owner_array.size, 3) or owner_array.size == 0:
        raise ValueError("minimum-distance assignment target count mismatch")
    cost = np.linalg.norm(
        positions[owner_array, None, :] - targets[None, :, :], axis=2
    )
    # Stable sub-nanometre lexicographic tie break; it cannot change a physical
    # minimum at the experiment's metre scale.
    tie = (
        np.arange(owner_array.size)[:, None] * owner_array.size
        + np.arange(owner_array.size)[None, :]
    ) * 1e-12
    rows, columns = linear_sum_assignment(cost + tie)
    return {int(owner_array[row]): int(column) for row, column in zip(rows, columns)}


def minimum_travel_time_target_assignment(
    *,
    physical_positions: np.ndarray,
    owners: Sequence[int],
    target_positions: np.ndarray,
    horizontal_step: float,
    vertical_step: float,
) -> tuple[dict[int, int], float]:
    """Assign anonymous targets by the physical controller's travel clock."""

    positions = np.asarray(physical_positions, dtype=np.float64)
    owner_array = np.asarray(tuple(int(owner) for owner in owners), dtype=np.int64)
    targets = np.asarray(target_positions, dtype=np.float64)
    if positions.shape != (PHYSICAL_UAVS, 3):
        raise ValueError("travel-time assignment physical shape mismatch")
    if targets.shape != (owner_array.size, 3) or owner_array.size == 0:
        raise ValueError("travel-time assignment target count mismatch")
    horizontal = np.linalg.norm(
        positions[owner_array, None, :2] - targets[None, :, :2], axis=2
    ) / max(float(horizontal_step), 1e-8)
    vertical = np.abs(
        positions[owner_array, None, 2] - targets[None, :, 2]
    ) / max(float(vertical_step), 1e-8)
    cost = np.maximum(horizontal, vertical)
    tie = (
        np.arange(owner_array.size)[:, None] * owner_array.size
        + np.arange(owner_array.size)[None, :]
    ) * 1e-12
    rows, columns = linear_sum_assignment(cost + tie)
    assignment = {
        int(owner_array[row]): int(column) for row, column in zip(rows, columns)
    }
    return assignment, float(cost[rows, columns].max())


def contract_targets_to_reachability(
    *,
    physical_positions: np.ndarray,
    owners: Sequence[int],
    target_positions: np.ndarray,
    travel_steps: int,
    horizontal_step: float,
    vertical_step: float,
) -> tuple[np.ndarray, dict[int, int], float]:
    """Maximally retain a layout while making every assigned target reachable."""

    positions = np.asarray(physical_positions, dtype=np.float64)
    targets = np.asarray(target_positions, dtype=np.float64)
    owner_array = np.asarray(tuple(int(owner) for owner in owners), dtype=np.int64)
    anchor = positions[owner_array].mean(axis=0)

    def candidate(scale: float) -> tuple[np.ndarray, dict[int, int], float]:
        contracted = anchor[None, :] + float(scale) * (targets - anchor[None, :])
        assignment, required = minimum_travel_time_target_assignment(
            physical_positions=positions,
            owners=owner_array,
            target_positions=contracted,
            horizontal_step=horizontal_step,
            vertical_step=vertical_step,
        )
        return contracted, assignment, required

    ideal, assignment, required = candidate(1.0)
    if required <= int(travel_steps):
        return ideal, assignment, 1.0
    low, high = 0.0, 1.0
    for _ in range(40):
        midpoint = 0.5 * (low + high)
        _targets, _assignment, midpoint_required = candidate(midpoint)
        if midpoint_required <= int(travel_steps):
            low = midpoint
        else:
            high = midpoint
    contracted, assignment, _required = candidate(low)
    return contracted, assignment, float(low)


def constructive_target_layout(
    *,
    physical_positions: np.ndarray,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    active_mask: np.ndarray,
    height_range: Sequence[float] = (50.0, 200.0),
) -> np.ndarray:
    """Pure six-service/two-relay (or active-count analogue) target planner."""

    positions = np.asarray(physical_positions, dtype=np.float64)
    users = np.asarray(user_positions, dtype=np.float64)
    bases = np.asarray(ground_bs_positions, dtype=np.float64)
    mask = np.asarray(active_mask, dtype=np.bool_)
    if positions.shape != (PHYSICAL_UAVS, 3) or mask.shape != (PHYSICAL_UAVS,):
        raise ValueError("constructive controller physical shape mismatch")
    active = np.flatnonzero(mask)
    targets = positions.copy()
    if active.size == 0:
        return targets
    slots = constructive_target_slots(
        user_positions=users,
        ground_bs_positions=bases,
        active_count=active.size,
        height_range=height_range,
    )
    assignment = minimum_distance_target_assignment(
        physical_positions=positions,
        owners=active,
        target_positions=slots,
    )
    for owner, target_index in assignment.items():
        targets[owner] = slots[target_index]
    return targets


def actions_toward_targets(
    *,
    physical_positions: np.ndarray,
    target_positions: np.ndarray,
    active_mask: np.ndarray,
    max_speed: float,
    max_vertical_speed: float,
    time_step: float,
) -> np.ndarray:
    positions = np.asarray(physical_positions, dtype=np.float64)
    targets = np.asarray(target_positions, dtype=np.float64)
    mask = np.asarray(active_mask, dtype=np.bool_)
    if positions.shape != (PHYSICAL_UAVS, 3) or targets.shape != positions.shape:
        raise ValueError("target-action physical shape mismatch")
    actions = np.zeros((PHYSICAL_UAVS, ACTION_DIM), dtype=np.float32)
    horizontal_scale = max(float(max_speed) * float(time_step), 1e-8)
    vertical_scale = max(float(max_vertical_speed) * float(time_step), 1e-8)
    delta = targets - positions
    actions[mask, :2] = np.clip(delta[mask, :2] / horizontal_scale, -1.0, 1.0)
    actions[mask, 2] = np.clip(delta[mask, 2] / vertical_scale, -1.0, 1.0)
    return actions


def constructive_actions(
    *,
    physical_positions: np.ndarray,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    active_mask: np.ndarray,
    max_speed: float,
    time_step: float,
    max_vertical_speed: float = 5.0,
    height_range: Sequence[float] = (50.0, 200.0),
) -> np.ndarray:
    """Evaluation-only action toward the current constructive target layout."""

    targets = constructive_target_layout(
        physical_positions=physical_positions,
        user_positions=user_positions,
        ground_bs_positions=ground_bs_positions,
        active_mask=active_mask,
        height_range=height_range,
    )
    return actions_toward_targets(
        physical_positions=physical_positions,
        target_positions=targets,
        active_mask=active_mask,
        max_speed=max_speed,
        max_vertical_speed=max_vertical_speed,
        time_step=time_step,
    )


class FullLedgerConstructiveController:
    """Evaluation-only pre-positioning controller with complete-ledger access."""

    uses_complete_ledger = True

    def __init__(
        self,
        ledger: UAVLossLedger,
        *,
        relay_count: int = 2,
        contract_for_reachability: bool = True,
    ) -> None:
        self.ledger = ledger
        unavailable_owners = {entry.owner for entry in ledger.intervals}
        self.protected_owners = tuple(
            owner for owner in range(PHYSICAL_UAVS) if owner not in unavailable_owners
        )
        self.affected_owners = tuple(sorted(unavailable_owners))
        if len(self.protected_owners) < 2:
            raise ValueError("constructive ledger leaves too few persistent service owners")
        if not 1 <= int(relay_count) < len(self.protected_owners):
            raise ValueError("constructive relay count is outside survivor support")
        self.relay_count = int(relay_count)
        self.contract_for_reachability = bool(contract_for_reachability)
        self._protected_assignment: dict[int, int] | None = None
        self._protected_targets: np.ndarray | None = None
        self._affected_targets: dict[int, np.ndarray] | None = None
        self.reachability_scale: float | None = None

    def act(
        self,
        *,
        physical_positions: np.ndarray,
        user_positions: np.ndarray,
        ground_bs_positions: np.ndarray,
        active_mask: np.ndarray,
        max_speed: float,
        max_vertical_speed: float,
        time_step: float,
        height_range: Sequence[float] = (50.0, 200.0),
    ) -> np.ndarray:
        positions = np.asarray(physical_positions, dtype=np.float64)
        mask = np.asarray(active_mask, dtype=np.bool_)
        if self._protected_assignment is None:
            ideal_slots = constructive_target_slots(
                user_positions=user_positions,
                ground_bs_positions=ground_bs_positions,
                active_count=len(self.protected_owners),
                relay_count=self.relay_count,
                height_range=height_range,
            )
            horizontal_step = float(max_speed) * float(time_step)
            vertical_step = float(max_vertical_speed) * float(time_step)
            if self.contract_for_reachability and self.ledger.intervals:
                lead_steps = min(entry.onset for entry in self.ledger.intervals)
                (
                    self._protected_targets,
                    self._protected_assignment,
                    self.reachability_scale,
                ) = contract_targets_to_reachability(
                    physical_positions=positions,
                    owners=self.protected_owners,
                    target_positions=ideal_slots,
                    travel_steps=lead_steps,
                    horizontal_step=horizontal_step,
                    vertical_step=vertical_step,
                )
            else:
                self._protected_targets = ideal_slots
                self._protected_assignment, _required = (
                    minimum_travel_time_target_assignment(
                        physical_positions=positions,
                        owners=self.protected_owners,
                        target_positions=ideal_slots,
                        horizontal_step=horizontal_step,
                        vertical_step=vertical_step,
                    )
                )
                self.reachability_scale = 1.0

            # A loss-affected owner is constrained to an ordinary all-fleet
            # service centroid.  Its target is fixed before onset, its physical
            # position is frozen by the environment during loss, and the same
            # service target is restored immediately on rejoin.
            self._affected_targets = {}
            if self.affected_owners:
                ordinary_slots = constructive_target_slots(
                    user_positions=user_positions,
                    ground_bs_positions=ground_bs_positions,
                    active_count=PHYSICAL_UAVS,
                    relay_count=self.relay_count,
                    height_range=height_range,
                )
                service_slots = ordinary_slots[self.relay_count :]
                affected = np.asarray(self.affected_owners, dtype=np.int64)
                cost = np.linalg.norm(
                    positions[affected, None, :] - service_slots[None, :, :], axis=2
                )
                tie = (
                    np.arange(affected.size)[:, None] * service_slots.shape[0]
                    + np.arange(service_slots.shape[0])[None, :]
                ) * 1e-12
                rows, columns = linear_sum_assignment(cost + tie)
                self._affected_targets = {
                    int(affected[row]): service_slots[column].copy()
                    for row, column in zip(rows, columns)
                }
        targets = positions.copy()
        for owner, target_index in self._protected_assignment.items():
            targets[owner] = self._protected_targets[target_index]
        for owner, target in self._affected_targets.items():
            targets[owner] = target

        return actions_toward_targets(
            physical_positions=positions,
            target_positions=targets,
            active_mask=mask,
            max_speed=max_speed,
            max_vertical_speed=max_vertical_speed,
            time_step=time_step,
        )


class NoReallocationController:
    """Latch the last all-active action/layout target through a disturbance."""

    uses_complete_ledger = False

    def __init__(self) -> None:
        self._latched: np.ndarray | None = None
        self._latched_targets: np.ndarray | None = None
        self._frozen = False

    def reset(self) -> None:
        self._latched = None
        self._latched_targets = None
        self._frozen = False

    def act(self, candidate_actions: np.ndarray, active_mask: np.ndarray) -> np.ndarray:
        candidate = np.asarray(candidate_actions, dtype=np.float32)
        mask = np.asarray(active_mask, dtype=np.bool_)
        if candidate.shape != (PHYSICAL_UAVS, ACTION_DIM) or mask.shape != (PHYSICAL_UAVS,):
            raise ValueError("no-reallocation control shape mismatch")
        if not bool(mask.all()):
            self._frozen = True
        if self._latched is None or (not self._frozen and bool(mask.all())):
            self._latched = candidate.copy()
        result = self._latched.copy()
        result[~mask] = 0.0
        return result

    def act_for_layout(
        self,
        *,
        candidate_targets: np.ndarray,
        physical_positions: np.ndarray,
        active_mask: np.ndarray,
        max_speed: float,
        max_vertical_speed: float,
        time_step: float,
    ) -> np.ndarray:
        mask = np.asarray(active_mask, dtype=np.bool_)
        targets = np.asarray(candidate_targets, dtype=np.float64)
        if targets.shape != (PHYSICAL_UAVS, 3) or mask.shape != (PHYSICAL_UAVS,):
            raise ValueError("no-reallocation target shape mismatch")
        if not bool(mask.all()):
            self._frozen = True
        if self._latched_targets is None or (not self._frozen and bool(mask.all())):
            self._latched_targets = targets.copy()
        return actions_toward_targets(
            physical_positions=physical_positions,
            target_positions=self._latched_targets,
            active_mask=mask,
            max_speed=max_speed,
            max_vertical_speed=max_vertical_speed,
            time_step=time_step,
        )


def model_state_copy(model: nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def maximum_state_difference(left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        (float(torch.max(torch.abs(left[key] - right[key]))) for key in left),
        default=0.0,
    )


def save_uav_checkpoint(
    path: Path,
    *,
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    completed_updates: int,
    next_episode_id: int,
    seed_contract: Mapping[str, int],
    action_rng_state: Mapping[str, Any] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "kind": "uav_temporary_service_loss_g1",
            "routing_mode": model.routing_mode,
            "observation_dim": model.observation_dim,
            "critic_state_dim": model.critic_state_dim,
            "hidden_dim": model.hidden_dim,
            "completed_updates": int(completed_updates),
            "next_episode_id": int(next_episode_id),
            "seed_contract": {str(key): int(value) for key, value in seed_contract.items()},
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "torch_rng_state": torch.get_rng_state(),
            "action_rng_state": copy.deepcopy(action_rng_state),
        },
        path,
    )


def load_uav_checkpoint(
    path: Path,
    *,
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    expected_seed_contract: Mapping[str, int],
) -> dict[str, Any]:
    bundle = torch.load(path, map_location="cpu", weights_only=False)
    required = {
        "schema_version",
        "kind",
        "routing_mode",
        "observation_dim",
        "critic_state_dim",
        "hidden_dim",
        "completed_updates",
        "next_episode_id",
        "seed_contract",
        "model_state",
        "optimizer_state",
        "torch_rng_state",
        "action_rng_state",
    }
    if set(bundle) != required:
        raise ValueError("UAV G1 checkpoint key set mismatch")
    if bundle["schema_version"] != CHECKPOINT_SCHEMA_VERSION or bundle["kind"] != "uav_temporary_service_loss_g1":
        raise ValueError("UAV G1 checkpoint schema/kind mismatch")
    architecture = (
        bundle["routing_mode"],
        int(bundle["observation_dim"]),
        int(bundle["critic_state_dim"]),
        int(bundle["hidden_dim"]),
    )
    expected_architecture = (
        model.routing_mode,
        model.observation_dim,
        model.critic_state_dim,
        model.hidden_dim,
    )
    if architecture != expected_architecture:
        raise ValueError("UAV G1 checkpoint architecture/routing mismatch")
    expected_seeds = {str(key): int(value) for key, value in expected_seed_contract.items()}
    if bundle["seed_contract"] != expected_seeds:
        raise ValueError("UAV G1 checkpoint seed contract mismatch")
    model.load_state_dict(bundle["model_state"], strict=True)
    optimizer.load_state_dict(bundle["optimizer_state"])
    device = next(model.parameters()).device
    for state in optimizer.state.values():
        for key, value in state.items():
            if isinstance(value, torch.Tensor):
                state[key] = value.to(device)
    torch.set_rng_state(bundle["torch_rng_state"])
    return bundle

"""Lightweight continuous-service dynamic-roster proxy for G17.

This is a fresh toy carrier.  It shares lifecycle-row policy mechanics with
the accepted open-roster line but does not reuse the retired spatial task, the
Generic-SHORT source, UAV physics, rewards, observations or checkpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import torch

from ha_ctse_process.continuous_roster_policy import (
    ContinuousRosterPolicy,
    ContinuousStepOutput,
)


CAPACITY = 8
ACTION_DIM = 2
OBSERVATION_DIM = 10
CRITIC_STATE_DIM = 6
HORIZON = 48
EVENT_TIMES = (12, 24, 36)

GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50


@dataclass(frozen=True)
class RosterProfile:
    name: str
    initial_count: int
    temporary_leave_count: int
    fresh_join_count: int
    terminal_leave_count: int

    def validate(self) -> None:
        values = (
            self.initial_count,
            self.temporary_leave_count,
            self.fresh_join_count,
            self.terminal_leave_count,
        )
        if min(values) <= 0:
            raise ValueError("G17 profile counts must be positive")
        if self.temporary_leave_count >= self.initial_count:
            raise ValueError("G17 temporary leave would empty or exceed the roster")
        if self.initial_count + self.fresh_join_count > CAPACITY:
            raise ValueError("G17 profile exceeds lifecycle capacity")
        if self.terminal_leave_count >= self.initial_count + self.fresh_join_count:
            raise ValueError("G17 terminal leave would empty the roster")

    @property
    def segment_counts(self) -> tuple[int, int, int, int]:
        return (
            self.initial_count,
            self.initial_count - self.temporary_leave_count,
            self.initial_count + self.fresh_join_count,
            self.initial_count + self.fresh_join_count - self.terminal_leave_count,
        )


TRAIN_PROFILES = (
    RosterProfile("train_4_3_6_5", 4, 1, 2, 1),
    RosterProfile("train_5_3_7_6", 5, 2, 2, 1),
    RosterProfile("train_6_4_8_6", 6, 2, 2, 2),
)
HELDOUT_PROFILES = (
    RosterProfile("heldout_3_2_5_4", 3, 1, 2, 1),
    RosterProfile("heldout_6_3_8_5", 6, 3, 2, 3),
)


def _rng(master_seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([int(master_seed), int(episode_id), int(stream)])
    )


@dataclass(frozen=True)
class ContinuousServiceLedger:
    episode_id: int
    profile: RosterProfile
    initial_keys: tuple[int, ...]
    temporarily_absent: tuple[int, ...]
    fresh_join: tuple[int, ...]
    terminal_leave: tuple[int, ...]
    capacities: np.ndarray
    load: np.ndarray
    target_mix: np.ndarray
    presentation_priority: np.ndarray
    expected_roster_sizes: tuple[int, ...]

    def validate(self) -> None:
        self.profile.validate()
        if self.initial_keys != tuple(range(self.profile.initial_count)):
            raise ValueError("G17 initial lifecycle inventory mismatch")
        if self.fresh_join != tuple(
            range(
                self.profile.initial_count,
                self.profile.initial_count + self.profile.fresh_join_count,
            )
        ):
            raise ValueError("G17 fresh lifecycle inventory mismatch")
        if len(set(self.temporarily_absent)) != self.profile.temporary_leave_count:
            raise ValueError("G17 temporary lifecycle inventory mismatch")
        if not set(self.temporarily_absent).issubset(self.initial_keys):
            raise ValueError("G17 temporary leave references a non-initial lifecycle")
        post_join = set(self.initial_keys) | set(self.fresh_join)
        if len(set(self.terminal_leave)) != self.profile.terminal_leave_count:
            raise ValueError("G17 terminal lifecycle inventory mismatch")
        if not set(self.terminal_leave).issubset(post_join):
            raise ValueError("G17 terminal leave references an unknown lifecycle")
        if np.asarray(self.capacities).shape != (CAPACITY, ACTION_DIM):
            raise ValueError("G17 capability matrix shape mismatch")
        if np.asarray(self.load).shape != (HORIZON,):
            raise ValueError("G17 load shape mismatch")
        if np.asarray(self.target_mix).shape != (HORIZON,):
            raise ValueError("G17 target-mix shape mismatch")
        if np.asarray(self.presentation_priority).shape != (HORIZON, CAPACITY):
            raise ValueError("G17 presentation-priority shape mismatch")
        for name in ("capacities", "load", "target_mix", "presentation_priority"):
            if not np.isfinite(np.asarray(getattr(self, name))).all():
                raise ValueError(f"G17 {name} contains a non-finite value")
        if np.any((self.load < 0.30) | (self.load > 0.70)):
            raise ValueError("G17 load left registered support")
        if np.any((self.target_mix < 0.25) | (self.target_mix > 0.75)):
            raise ValueError("G17 target mix left registered support")
        if len(self.expected_roster_sizes) != HORIZON:
            raise ValueError("G17 expected roster schedule length mismatch")
        expected = tuple(
            count
            for count in self.profile.segment_counts
            for _ in range(HORIZON // 4)
        )
        if self.expected_roster_sizes != expected:
            raise ValueError("G17 expected roster schedule mismatch")


def make_ledger(
    episode_id: int,
    *,
    master_seed: int,
    profiles: Sequence[RosterProfile] = TRAIN_PROFILES,
) -> ContinuousServiceLedger:
    profile_rows = tuple(profiles)
    if not profile_rows:
        raise ValueError("G17 ledger requires at least one profile")
    profile = profile_rows[int(episode_id) % len(profile_rows)]
    profile.validate()
    initial = tuple(range(profile.initial_count))
    fresh = tuple(
        range(profile.initial_count, profile.initial_count + profile.fresh_join_count)
    )
    temporary = tuple(
        sorted(
            int(value)
            for value in _rng(master_seed, episode_id, 0).choice(
                initial, size=profile.temporary_leave_count, replace=False
            )
        )
    )
    terminal_support = np.asarray(initial + fresh, dtype=np.int64)
    terminal = tuple(
        sorted(
            int(value)
            for value in _rng(master_seed, episode_id, 1).choice(
                terminal_support, size=profile.terminal_leave_count, replace=False
            )
        )
    )
    capacities = _rng(master_seed, episode_id, 2).uniform(
        0.75, 1.25, size=(CAPACITY, ACTION_DIM)
    ).astype(np.float32)
    # Four-step demand blocks are long enough for recurrence to observe
    # continuity but change independently of every membership event.
    demand_blocks = HORIZON // 4
    load = np.repeat(
        _rng(master_seed, episode_id, 3).uniform(0.30, 0.70, size=demand_blocks),
        4,
    ).astype(np.float32)
    target_mix = np.repeat(
        _rng(master_seed, episode_id, 4).uniform(0.25, 0.75, size=demand_blocks),
        4,
    ).astype(np.float32)
    priority = _rng(master_seed, episode_id, 5).random(
        (HORIZON, CAPACITY), dtype=np.float32
    )
    expected = tuple(
        count for count in profile.segment_counts for _ in range(HORIZON // 4)
    )
    ledger = ContinuousServiceLedger(
        episode_id=int(episode_id),
        profile=profile,
        initial_keys=initial,
        temporarily_absent=temporary,
        fresh_join=fresh,
        terminal_leave=terminal,
        capacities=capacities,
        load=load,
        target_mix=target_mix,
        presentation_priority=priority,
        expected_roster_sizes=expected,
    )
    ledger.validate()
    return ledger


@dataclass(frozen=True)
class MembershipChange:
    joined: tuple[int, ...] = ()
    temporarily_left: tuple[int, ...] = ()
    rejoined: tuple[int, ...] = ()
    terminally_left: tuple[int, ...] = ()


@dataclass(frozen=True)
class ContinuousServiceView:
    time: int
    observations: np.ndarray
    active_mask: np.ndarray
    critic_state: np.ndarray
    membership_change: MembershipChange
    load: float
    target_mix: float


@dataclass(frozen=True)
class ContinuousServiceOutcome:
    utility: float
    minimum_step_utility: float
    segment_utilities: tuple[float, ...]
    roster_sizes: tuple[int, ...]
    reward_trace: tuple[float, ...]


class ContinuousServiceRosterEnv:
    """Fresh 48-step continuous two-service allocation carrier."""

    def __init__(self, ledger: ContinuousServiceLedger):
        ledger.validate()
        self.ledger = ledger
        self.time = 0
        self.active = np.zeros(CAPACITY, dtype=np.bool_)
        self.active[np.asarray(ledger.initial_keys, dtype=np.int64)] = True
        self.age = np.zeros(CAPACITY, dtype=np.int64)
        self.previous_actions = np.zeros((CAPACITY, ACTION_DIM), dtype=np.float32)
        self.reward_trace: list[float] = []
        self.roster_sizes: list[int] = []
        self._prepared_time: int | None = None
        self._membership_change = MembershipChange(joined=ledger.initial_keys)
        self._terminated = False

    def _prepare_membership(self) -> None:
        if self._prepared_time == self.time:
            return
        change = MembershipChange()
        if self.time == EVENT_TIMES[0]:
            keys = self.ledger.temporarily_absent
            self.active[np.asarray(keys, dtype=np.int64)] = False
            change = MembershipChange(temporarily_left=keys)
        elif self.time == EVENT_TIMES[1]:
            rejoined = self.ledger.temporarily_absent
            joined = self.ledger.fresh_join
            self.active[np.asarray(rejoined + joined, dtype=np.int64)] = True
            self.previous_actions[np.asarray(joined, dtype=np.int64)] = 0.0
            self.age[np.asarray(joined, dtype=np.int64)] = 0
            change = MembershipChange(joined=joined, rejoined=rejoined)
        elif self.time == EVENT_TIMES[2]:
            keys = self.ledger.terminal_leave
            self.active[np.asarray(keys, dtype=np.int64)] = False
            change = MembershipChange(terminally_left=keys)
        self._membership_change = change
        self._prepared_time = self.time

    def observe(self) -> ContinuousServiceView:
        if self._terminated or self.time >= HORIZON:
            raise RuntimeError("G17 cannot observe a terminal environment")
        self._prepare_membership()
        active_count = int(self.active.sum())
        if active_count <= 0:
            raise RuntimeError("G17 source produced an empty active roster")
        observations = np.zeros((CAPACITY, OBSERVATION_DIM), dtype=np.float32)
        load = float(self.ledger.load[self.time])
        target_mix = float(self.ledger.target_mix[self.time])
        active_keys = np.flatnonzero(self.active)
        observations[active_keys, 0:2] = self.ledger.capacities[active_keys]
        observations[active_keys, 2] = self.ledger.presentation_priority[
            self.time, active_keys
        ]
        observations[active_keys, 3] = load
        observations[active_keys, 4] = target_mix
        observations[active_keys, 5] = active_count / CAPACITY
        observations[active_keys, 6] = self.age[active_keys] / HORIZON
        observations[active_keys, 7:9] = (
            self.previous_actions[active_keys] + 1.0
        ) / 2.0
        observations[active_keys, 9] = self.time / (HORIZON - 1)
        aggregate = self.ledger.capacities[active_keys].sum(axis=0)
        critic_state = np.asarray(
            (
                load,
                target_mix,
                aggregate[0] / CAPACITY,
                aggregate[1] / CAPACITY,
                active_count / CAPACITY,
                self.time / (HORIZON - 1),
            ),
            dtype=np.float32,
        )
        return ContinuousServiceView(
            time=self.time,
            observations=observations,
            active_mask=self.active.copy(),
            critic_state=critic_state,
            membership_change=self._membership_change,
            load=load,
            target_mix=target_mix,
        )

    def step(self, actions: np.ndarray) -> tuple[float, bool, dict[str, float]]:
        if self._terminated:
            raise RuntimeError("G17 cannot step a terminal environment")
        view = self.observe()
        values = np.asarray(actions, dtype=np.float32)
        if values.shape != (CAPACITY, ACTION_DIM) or not np.isfinite(values).all():
            raise ValueError("G17 action shape/finite contract mismatch")
        if np.any(values < -1.0) or np.any(values > 1.0):
            raise ValueError("G17 action left tanh support")
        if np.count_nonzero(values[~view.active_mask]) != 0:
            raise ValueError("G17 inactive lifecycle received a physical action")
        keys = np.flatnonzero(view.active_mask)
        effort = (values[keys, 0] + 1.0) / 2.0
        mix = (values[keys, 1] + 1.0) / 2.0
        capacities = self.ledger.capacities[keys]
        served = np.asarray(
            (
                np.sum(effort * mix * capacities[:, 0], dtype=np.float64),
                np.sum(effort * (1.0 - mix) * capacities[:, 1], dtype=np.float64),
            )
        )
        aggregate = capacities.sum(axis=0, dtype=np.float64)
        target = np.asarray(
            (
                view.load * view.target_mix * aggregate[0],
                view.load * (1.0 - view.target_mix) * aggregate[1],
            )
        )
        relative_error = np.abs(served - target) / np.maximum(target, 1e-8)
        utility = float(np.clip(1.0 - relative_error.mean(), 0.0, 1.0))
        self.previous_actions[keys] = values[keys]
        self.age[keys] += 1
        self.reward_trace.append(utility)
        self.roster_sizes.append(len(keys))
        self.time += 1
        self._prepared_time = None
        self._membership_change = MembershipChange()
        self._terminated = self.time == HORIZON
        return utility, self._terminated, {
            "service_utility": utility,
            "service_0": float(served[0]),
            "service_1": float(served[1]),
            "target_0": float(target[0]),
            "target_1": float(target[1]),
        }

    def outcome(self) -> ContinuousServiceOutcome:
        if not self._terminated or len(self.reward_trace) != HORIZON:
            raise RuntimeError("G17 outcome requires a complete episode")
        rewards = np.asarray(self.reward_trace, dtype=np.float64)
        segments = tuple(
            float(rewards[start : start + HORIZON // 4].mean())
            for start in range(0, HORIZON, HORIZON // 4)
        )
        return ContinuousServiceOutcome(
            utility=float(rewards.mean()),
            minimum_step_utility=float(rewards.min()),
            segment_utilities=segments,
            roster_sizes=tuple(self.roster_sizes),
            reward_trace=tuple(self.reward_trace),
        )


def constructive_actions(view: ContinuousServiceView) -> np.ndarray:
    actions = np.zeros((CAPACITY, ACTION_DIM), dtype=np.float32)
    actions[view.active_mask, 0] = np.float32(2.0 * view.load - 1.0)
    actions[view.active_mask, 1] = np.float32(2.0 * view.target_mix - 1.0)
    return actions


@dataclass
class ContinuousRosterTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    critic_states: torch.Tensor
    actions: torch.Tensor
    pre_tanh_actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    outcomes: tuple[ContinuousServiceOutcome, ...]
    ledgers: tuple[ContinuousServiceLedger, ...]

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


def make_action_noise(
    episode_ids: Iterable[int], *, action_seed: int
) -> np.ndarray:
    rows = []
    for episode_id in episode_ids:
        rows.append(
            _rng(action_seed, int(episode_id), 90)
            .standard_normal((HORIZON, CAPACITY, ACTION_DIM))
            .astype(np.float32)
        )
    if not rows:
        raise ValueError("G17 action noise requires an episode")
    return np.stack(rows, axis=1)


def collect_trajectory(
    model: ContinuousRosterPolicy,
    *,
    episode_ids: Iterable[int],
    ledger_seed: int,
    action_seed: int,
    device: torch.device,
    profiles: Sequence[RosterProfile] = TRAIN_PROFILES,
    deterministic: bool = False,
) -> ContinuousRosterTrajectory:
    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("G17 collection requires at least one episode")
    ledgers = tuple(
        make_ledger(value, master_seed=ledger_seed, profiles=profiles) for value in ids
    )
    environments = tuple(ContinuousServiceRosterEnv(ledger) for ledger in ledgers)
    batch = len(ids)
    noise = make_action_noise(ids, action_seed=action_seed)
    hidden = torch.zeros(
        (batch, CAPACITY, model.hidden_dim), dtype=torch.float32, device=device
    )
    shapes = {
        "observations": (HORIZON, batch, CAPACITY, OBSERVATION_DIM),
        "active_mask": (HORIZON, batch, CAPACITY),
        "critic_states": (HORIZON, batch, CRITIC_STATE_DIM),
        "actions": (HORIZON, batch, CAPACITY, ACTION_DIM),
        "pre_tanh_actions": (HORIZON, batch, CAPACITY, ACTION_DIM),
        "old_log_probs": (HORIZON, batch, CAPACITY),
        "old_values": (HORIZON, batch),
        "rewards": (HORIZON, batch),
        "hidden_before": (HORIZON, batch, CAPACITY, model.hidden_dim),
        "hidden_after": (HORIZON, batch, CAPACITY, model.hidden_dim),
        "prefix_action_sums": (HORIZON, batch, CAPACITY, ACTION_DIM),
    }
    rows: dict[str, torch.Tensor] = {}
    for name, shape in shapes.items():
        dtype = torch.bool if name == "active_mask" else torch.float32
        rows[name] = torch.empty(shape, dtype=dtype)

    model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            views = tuple(environment.observe() for environment in environments)
            observations = torch.as_tensor(
                np.stack([view.observations for view in views]), device=device
            )
            active_mask = torch.as_tensor(
                np.stack([view.active_mask for view in views]), device=device
            )
            critic_states = torch.as_tensor(
                np.stack([view.critic_state for view in views]), device=device
            )
            hidden_before = hidden.clone()
            arguments = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_state": critic_states,
                "hidden": hidden,
            }
            if deterministic:
                output = model.forward_step(**arguments, deterministic=True)
            else:
                output = model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time], device=device),
                )
            rewards = np.empty(batch, dtype=np.float32)
            action_values = output.actions.detach().cpu().numpy()
            for env_index, environment in enumerate(environments):
                reward, _terminal, _info = environment.step(action_values[env_index])
                rewards[env_index] = reward
            values = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_states": critic_states,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": output.value,
                "rewards": torch.as_tensor(rewards, device=device),
                "hidden_before": hidden_before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
            }
            for name, value in values.items():
                rows[name][time].copy_(value.detach().cpu())
            hidden = output.next_hidden

    return ContinuousRosterTrajectory(
        **rows,
        outcomes=tuple(environment.outcome() for environment in environments),
        ledgers=ledgers,
    )


def evaluate_policy(
    model: ContinuousRosterPolicy,
    *,
    episode_ids: Iterable[int],
    ledger_seed: int,
    action_seed: int,
    device: torch.device,
    profiles: Sequence[RosterProfile],
    deterministic: bool,
) -> tuple[ContinuousServiceOutcome, ...]:
    """Evaluate without allocating or persisting a training trajectory."""

    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("G17 evaluation requires at least one episode")
    environments = tuple(
        ContinuousServiceRosterEnv(
            make_ledger(value, master_seed=ledger_seed, profiles=profiles)
        )
        for value in ids
    )
    noise = make_action_noise(ids, action_seed=action_seed)
    hidden = torch.zeros(
        (len(ids), CAPACITY, model.hidden_dim), dtype=torch.float32, device=device
    )
    model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            views = tuple(environment.observe() for environment in environments)
            arguments = {
                "observations": torch.as_tensor(
                    np.stack([view.observations for view in views]), device=device
                ),
                "active_mask": torch.as_tensor(
                    np.stack([view.active_mask for view in views]), device=device
                ),
                "critic_state": torch.as_tensor(
                    np.stack([view.critic_state for view in views]), device=device
                ),
                "hidden": hidden,
            }
            if deterministic:
                output = model.forward_step(**arguments, deterministic=True)
            else:
                output = model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time], device=device),
                )
            actions = output.actions.detach().cpu().numpy()
            for env_index, environment in enumerate(environments):
                environment.step(actions[env_index])
            hidden = output.next_hidden
    return tuple(environment.outcome() for environment in environments)


@dataclass
class ContinuousRosterReplay:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_action_sums: torch.Tensor
    active_mask: torch.Tensor


def replay_trajectory(
    model: ContinuousRosterPolicy,
    trajectory: ContinuousRosterTrajectory,
    *,
    device: torch.device,
) -> ContinuousRosterReplay:
    hidden = trajectory.hidden_before[0].to(device)
    outputs: list[ContinuousStepOutput] = []
    for time in range(HORIZON):
        output = model.forward_step(
            observations=trajectory.observations[time].to(device),
            active_mask=trajectory.active_mask[time].to(device),
            critic_state=trajectory.critic_states[time].to(device),
            hidden=hidden,
            teacher_pre_tanh=trajectory.pre_tanh_actions[time].to(device),
        )
        outputs.append(output)
        hidden = output.next_hidden
    return ContinuousRosterReplay(
        log_probs=torch.stack([row.token_log_probs for row in outputs]),
        entropies=torch.stack([row.token_entropies for row in outputs]),
        values=torch.stack([row.value for row in outputs]),
        hidden_after=torch.stack([row.next_hidden for row in outputs]),
        prefix_action_sums=torch.stack([row.prefix_action_sums for row in outputs]),
        active_mask=trajectory.active_mask.to(device),
    )


def replay_errors(
    replay: ContinuousRosterReplay, trajectory: ContinuousRosterTrajectory
) -> dict[str, float]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_logp = trajectory.old_log_probs.to(device)
    return {
        "logp_max_error": float(torch.abs(replay.log_probs - old_logp)[mask].max().detach().cpu()),
        "joint_logp_max_error": float(
            torch.abs(torch.where(mask, replay.log_probs - old_logp, 0.0).sum(dim=-1))
            .max()
            .detach()
            .cpu()
        ),
        "value_max_error": float(
            torch.abs(replay.values - trajectory.old_values.to(device)).max().detach().cpu()
        ),
        "hidden_max_error": float(
            torch.abs(replay.hidden_after - trajectory.hidden_after.to(device)).max().detach().cpu()
        ),
        "prefix_max_error": float(
            torch.abs(
                replay.prefix_action_sums - trajectory.prefix_action_sums.to(device)
            )
            .max()
            .detach()
            .cpu()
        ),
        "inactive_logp_max_abs": float(
            torch.where(mask, 0.0, replay.log_probs).abs().max().detach().cpu()
        ),
    }


def compute_gae(
    rewards: torch.Tensor,
    values: torch.Tensor,
    *,
    gamma: float = GAMMA,
    gae_lambda: float = GAE_LAMBDA,
) -> tuple[torch.Tensor, torch.Tensor]:
    if rewards.shape != values.shape or rewards.ndim != 2:
        raise ValueError("G17 GAE expects matching [time, batch] tensors")
    advantages = torch.zeros_like(rewards)
    running = torch.zeros(rewards.shape[1], dtype=rewards.dtype, device=rewards.device)
    next_value = torch.zeros_like(running)
    time_count = int(rewards.shape[0])
    for time in range(time_count - 1, -1, -1):
        continuation = 0.0 if time == time_count - 1 else 1.0
        delta = rewards[time] + float(gamma) * next_value * continuation - values[time]
        running = (
            delta
            + float(gamma) * float(gae_lambda) * continuation * running
        )
        advantages[time] = running
        next_value = values[time]
    return advantages, advantages + values


def ppo_loss(
    replay: ContinuousRosterReplay,
    trajectory: ContinuousRosterTrajectory,
    advantages: torch.Tensor,
    returns: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    device = replay.log_probs.device
    mask = replay.active_mask
    old_logp = trajectory.old_log_probs.to(device)
    old_values = trajectory.old_values.to(device)
    normalized = (advantages.to(device) - advantages.mean()) / (
        advantages.std(unbiased=False) + 1e-8
    )
    ratio = torch.exp(replay.log_probs - old_logp)
    expanded = normalized.unsqueeze(-1)
    surrogate = torch.minimum(
        ratio * expanded,
        torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * expanded,
    )
    active_count = mask.sum(dim=-1).clamp_min(1)
    policy = -(
        torch.where(mask, surrogate, 0.0).sum(dim=-1) / active_count
    ).mean()
    entropy = (
        torch.where(mask, replay.entropies, 0.0).sum(dim=-1) / active_count
    ).mean()
    clipped = old_values + torch.clamp(
        replay.values - old_values, -VALUE_CLIP, VALUE_CLIP
    )
    value = torch.maximum(
        torch.square(replay.values - returns.to(device)),
        torch.square(clipped - returns.to(device)),
    ).mean()
    total = policy + VALUE_COEFFICIENT * value - ENTROPY_COEFFICIENT * entropy
    clip_fraction = (
        torch.where(mask, (torch.abs(ratio - 1.0) > PPO_CLIP).to(ratio.dtype), 0.0).sum()
        / mask.sum().clamp_min(1)
    )
    return total, {
        "policy_loss": policy,
        "value_loss": value,
        "entropy": entropy,
        "clip_fraction": clip_fraction,
    }


def optimize_update(
    model: ContinuousRosterPolicy,
    optimizer: torch.optim.Optimizer,
    trajectory: ContinuousRosterTrajectory,
    *,
    device: torch.device,
    ppo_passes: int,
    gamma: float = GAMMA,
    gae_lambda: float = GAE_LAMBDA,
) -> dict[str, float]:
    advantages, returns = compute_gae(
        trajectory.rewards.to(device),
        trajectory.old_values.to(device),
        gamma=float(gamma),
        gae_lambda=float(gae_lambda),
    )
    model.train()
    replay = replay_trajectory(model, trajectory, device=device)
    with torch.no_grad():
        errors = replay_errors(replay, trajectory)
    totals = {
        name: 0.0
        for name in (
            "policy_loss",
            "value_loss",
            "entropy",
            "clip_fraction",
            "gradient_norm",
        )
    }
    finite = True
    for pass_index in range(int(ppo_passes)):
        if pass_index:
            replay = replay_trajectory(model, trajectory, device=device)
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

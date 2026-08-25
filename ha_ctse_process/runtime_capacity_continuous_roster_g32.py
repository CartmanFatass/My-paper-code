"""Training orchestration for the capacity-independent continuous-roster source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


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
    outcomes: tuple[roster_env.CapacityRosterOutcome, ...]
    ledgers: tuple[roster_env.CapacityRosterLedger, ...]
    terminal_hidden_reset_mask: torch.Tensor

    @property
    def active_token_count(self) -> int:
        return int(self.active_mask.sum().item())


def _delete_terminal_hidden(
    hidden: torch.Tensor, views: Sequence[roster_env.CapacityRosterView]
) -> None:
    for batch_index, view in enumerate(views):
        keys = view.membership_change.terminally_left
        if keys:
            hidden[batch_index, list(keys)] = 0.0


def collect_trajectory(
    model: ContinuousRosterPolicy, *, episode_ids: Iterable[int], ledger_seed: int,
    action_seed: int, device: torch.device,
    profiles: Sequence[roster_env.RosterProfile] = roster_env.TRAIN_PROFILES,
) -> ContinuousRosterTrajectory:
    ids = tuple(int(value) for value in episode_ids)
    profile_rows = tuple(profiles)
    if not ids or not profile_rows:
        raise ValueError("G32 collection requires episodes and profiles")
    capacity = profile_rows[0].member_capacity
    if any(row.member_capacity != capacity for row in profile_rows) or model.member_capacity != capacity:
        raise ValueError("G32 collection capacity mismatch")
    ledgers = tuple(roster_env.make_ledger(
        episode, master_seed=ledger_seed,
        profile=profile_rows[episode % len(profile_rows)],
    ) for episode in ids)
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    batch = len(ids)
    noise = roster_env.make_action_noise(
        ids, action_seed=action_seed, member_capacity=capacity
    )
    hidden = torch.zeros((batch, capacity, model.hidden_dim), device=device)
    shapes = {
        "observations": (roster_env.HORIZON, batch, capacity, roster_env.OBSERVATION_DIM),
        "active_mask": (roster_env.HORIZON, batch, capacity),
        "critic_states": (roster_env.HORIZON, batch, roster_env.CRITIC_STATE_DIM),
        "actions": (roster_env.HORIZON, batch, capacity, roster_env.ACTION_DIM),
        "pre_tanh_actions": (roster_env.HORIZON, batch, capacity, roster_env.ACTION_DIM),
        "old_log_probs": (roster_env.HORIZON, batch, capacity),
        "old_values": (roster_env.HORIZON, batch),
        "rewards": (roster_env.HORIZON, batch),
        "hidden_before": (roster_env.HORIZON, batch, capacity, model.hidden_dim),
        "hidden_after": (roster_env.HORIZON, batch, capacity, model.hidden_dim),
        "prefix_action_sums": (roster_env.HORIZON, batch, capacity, roster_env.ACTION_DIM),
        "terminal_hidden_reset_mask": (roster_env.HORIZON, batch, capacity),
    }
    rows = {
        name: torch.empty(
            shape,
            dtype=torch.bool
            if name in ("active_mask", "terminal_hidden_reset_mask")
            else torch.float32,
        )
        for name, shape in shapes.items()
    }
    model.eval()
    with torch.no_grad():
        for time in range(roster_env.HORIZON):
            views = tuple(env.observe() for env in envs)
            terminal_reset = torch.zeros(
                (batch, capacity), dtype=torch.bool, device=device
            )
            for batch_index, view in enumerate(views):
                if view.membership_change.terminally_left:
                    terminal_reset[
                        batch_index, list(view.membership_change.terminally_left)
                    ] = True
            _delete_terminal_hidden(hidden, views)
            observations = torch.as_tensor(
                np.stack([row.observations for row in views]), device=device
            )
            active = torch.as_tensor(
                np.stack([row.active_mask for row in views]), device=device
            )
            critic = torch.as_tensor(
                np.stack([row.critic_state for row in views]), device=device
            )
            before = hidden.clone()
            output = model.forward_step(
                observations=observations,
                active_mask=active,
                critic_state=critic,
                hidden=hidden,
                sampling_noise=torch.as_tensor(noise[time], device=device),
            )
            rewards = np.asarray([
                env.step(output.actions[index].detach().cpu().numpy())[0]
                for index, env in enumerate(envs)
            ], dtype=np.float32)
            values = {
                "observations": observations,
                "active_mask": active,
                "critic_states": critic,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": output.value,
                "rewards": torch.as_tensor(rewards, device=device),
                "hidden_before": before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
                "terminal_hidden_reset_mask": terminal_reset,
            }
            for name, value in values.items():
                rows[name][time].copy_(value.detach().cpu())
            hidden = output.next_hidden
    return ContinuousRosterTrajectory(
        **rows,
        outcomes=tuple(env.outcome() for env in envs),
        ledgers=ledgers,
    )


def evaluate_policy(
    model: ContinuousRosterPolicy, *, episode_ids: Iterable[int], ledger_seed: int,
    action_seed: int, device: torch.device,
    profiles: Sequence[roster_env.RosterProfile], deterministic: bool,
) -> tuple[roster_env.CapacityRosterOutcome, ...]:
    ids = tuple(int(value) for value in episode_ids)
    profile_rows = tuple(profiles)
    if (
        not ids
        or not profile_rows
        or any(row.member_capacity != model.member_capacity for row in profile_rows)
    ):
        raise ValueError("G32 evaluation episode/capacity mismatch")
    envs = tuple(
        roster_env.RuntimeCapacityRosterEnv(
            roster_env.make_ledger(
                episode,
                master_seed=ledger_seed,
                profile=profile_rows[episode % len(profile_rows)],
            )
        )
        for episode in ids
    )
    capacity = model.member_capacity
    noise = roster_env.make_action_noise(
        ids, action_seed=action_seed, member_capacity=capacity
    )
    hidden = torch.zeros((len(ids), capacity, model.hidden_dim), device=device)
    model.eval()
    with torch.no_grad():
        for time in range(roster_env.HORIZON):
            views = tuple(env.observe() for env in envs)
            _delete_terminal_hidden(hidden, views)
            arguments = {
                "observations": torch.as_tensor(
                    np.stack([row.observations for row in views]), device=device
                ),
                "active_mask": torch.as_tensor(
                    np.stack([row.active_mask for row in views]), device=device
                ),
                "critic_state": torch.as_tensor(
                    np.stack([row.critic_state for row in views]), device=device
                ),
                "hidden": hidden,
            }
            output = (
                model.forward_step(**arguments, deterministic=True)
                if deterministic
                else model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time], device=device),
                )
            )
            for index, env in enumerate(envs):
                env.step(output.actions[index].detach().cpu().numpy())
            hidden = output.next_hidden
    return tuple(env.outcome() for env in envs)


def source_controls() -> dict[str, object]:
    profiles = (
        roster_env.PADDING_CAPACITY_8,
        roster_env.PADDING_CAPACITY_12,
        roster_env.SMALL_CAPACITY_6,
        roster_env.LARGE_CAPACITY_12,
    )
    rows = []
    for profile in profiles:
        ledger = roster_env.make_ledger(
            0, master_seed=10_326_099, profile=profile
        )
        environment = roster_env.RuntimeCapacityRosterEnv(ledger)
        for _ in range(roster_env.HORIZON):
            view = environment.observe()
            environment.step(roster_env.constructive_actions(view))
        outcome = environment.outcome()
        rows.append({
            "profile": profile.name,
            "member_capacity": profile.member_capacity,
            "minimum_step_utility": outcome.minimum_step_utility,
            "roster_sizes": list(outcome.roster_sizes),
            "expected_roster_sizes": list(ledger.expected_roster_sizes),
        })
    return {
        "horizon": roster_env.HORIZON,
        "event_times": list(roster_env.EVENT_TIMES),
        "action_dim": roster_env.ACTION_DIM,
        "observation_dim": roster_env.OBSERVATION_DIM,
        "critic_state_dim": roster_env.CRITIC_STATE_DIM,
        "train_profiles": [row.name for row in roster_env.TRAIN_PROFILES],
        "evaluation_profiles": [
            roster_env.PADDING_CAPACITY_8.name,
            roster_env.PADDING_CAPACITY_12.name,
            roster_env.SMALL_CAPACITY_6.name,
            roster_env.LARGE_CAPACITY_12.name,
        ],
        "capacity_normalization": "none",
        "member_rng": "episode_member_owned_streams",
        "uav_fields": [],
        "constructive_rows": rows,
        "constructive_access_valid": min(
            float(row["minimum_step_utility"]) for row in rows
        ) >= 1.0 - 2e-7,
        "all_roster_schedules_exact": all(
            row["roster_sizes"] == row["expected_roster_sizes"] for row in rows
        ),
    }

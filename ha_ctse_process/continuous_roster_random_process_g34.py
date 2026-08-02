"""Bounded held-out membership-process source for G34-P0."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


ALGORITHM_ID = "CONTINUOUS_ROSTER_RANDOM_PROCESS_G34"
SOURCE_ID = "CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0"
CAPACITIES = (6, 8, 12)
EVENT_ORDERS = (("L", "R", "J", "T"), ("L", "J", "R", "T"), ("J", "L", "R", "T"))
BASE_LEDGER_SEED_BASE = 10_340_000
PROCESS_SEED_BASE = 10_341_000
ACTION_SEED_BASE = 10_342_000
BOOTSTRAP_SEED = 10_343_034
EPISODES_PER_CELL = 128
TIME_ROTATION = 17

TIME_TUPLES = tuple(
    row
    for row in combinations(
        (time for time in range(5, 44) if time % 4 != 0), 4
    )
    if all(right - left >= 5 for left, right in zip(row, row[1:]))
)


def episode_address(capacity: int, local_episode_id: int) -> int:
    if capacity not in CAPACITIES or not 0 <= int(local_episode_id) < EPISODES_PER_CELL:
        raise ValueError("G34 episode address outside registered support")
    return 10_000 * int(capacity) + int(local_episode_id)


def _process_rng(
    replicate: int, capacity: int, local_episode_id: int, stream: int
) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence(
            [PROCESS_SEED_BASE + int(replicate), int(capacity), int(local_episode_id), int(stream)]
        )
    )


def _balanced_assignments(
    categories: Sequence[object], *, replicate: int, capacity: int, stream: int
) -> tuple[object, ...]:
    if len(categories) != 3 or not 0 <= int(replicate) < 3:
        raise ValueError("G34 balanced assignment requires three categories and replicates")
    counts = [43, 43, 43]
    counts[int(replicate) % 3] = 42
    episode_order = sorted(
        range(EPISODES_PER_CELL),
        key=lambda episode: (
            int(_process_rng(replicate, capacity, episode, stream).integers(0, 2**63)),
            episode,
        ),
    )
    assigned: list[object | None] = [None] * EPISODES_PER_CELL
    offset = 0
    for category, count in zip(categories, counts):
        for episode in episode_order[offset : offset + count]:
            assigned[episode] = category
        offset += count
    if offset != EPISODES_PER_CELL or any(value is None for value in assigned):
        raise RuntimeError("G34 balanced assignment did not close")
    return tuple(assigned)  # type: ignore[arg-type]


def _time_assignments(*, replicate: int, capacity: int) -> tuple[tuple[int, ...], ...]:
    unused = list(TIME_TUPLES)
    rows: list[tuple[int, ...]] = []
    for episode in range(EPISODES_PER_CELL):
        rng = _process_rng(replicate, capacity, episode, 0)
        rows.append(unused.pop(int(rng.integers(0, len(unused)))))
    return tuple(rows)


def _profile_assignments(
    *, replicate: int, capacity: int
) -> tuple[roster_env.RosterProfile, ...]:
    if capacity == 6:
        return (roster_env.SMALL_CAPACITY_6,) * EPISODES_PER_CELL
    if capacity == 12:
        return (roster_env.LARGE_CAPACITY_12,) * EPISODES_PER_CELL
    if capacity == 8:
        return _balanced_assignments(
            roster_env.TRAIN_PROFILES, replicate=replicate, capacity=capacity, stream=2
        )  # type: ignore[return-value]
    raise ValueError("G34 capacity outside registered support")


@dataclass(frozen=True)
class RandomProcessLedger:
    base: roster_env.CapacityRosterLedger
    local_episode_id: int
    event_times: tuple[int, int, int, int]
    event_order: tuple[str, str, str, str]
    expected_roster_sizes: tuple[int, ...]
    count_trajectory: tuple[int, ...]

    @property
    def episode_id(self) -> int:
        return self.base.episode_id

    @property
    def member_capacity(self) -> int:
        return self.base.member_capacity

    @property
    def profile(self) -> roster_env.RosterProfile:
        return self.base.profile

    @property
    def signature(self) -> tuple[object, ...]:
        return (
            self.event_times,
            self.event_order,
            self.profile.name,
            self.base.temporarily_absent,
            self.base.fresh_join,
            self.base.terminal_leave,
        )

    def validate(self) -> None:
        self.base.validate()
        if self.event_times not in TIME_TUPLES or self.event_order not in EVENT_ORDERS:
            raise ValueError("G34 event support mismatch")
        if self.episode_id != episode_address(self.member_capacity, self.local_episode_id):
            raise ValueError("G34 episode identity mismatch")
        expected_sizes, trajectory = _expected_roster_schedule(self.base, self.event_times, self.event_order)
        if self.expected_roster_sizes != expected_sizes or self.count_trajectory != trajectory:
            raise ValueError("G34 active-count schedule mismatch")


def _apply_edit(active: set[int], base: roster_env.CapacityRosterLedger, edit: str) -> None:
    if edit == "L":
        cohort = set(base.temporarily_absent)
        if not cohort.issubset(active):
            raise ValueError("G34 temporary leave cohort inactive")
        active.difference_update(cohort)
    elif edit == "R":
        cohort = set(base.temporarily_absent)
        if cohort & active:
            raise ValueError("G34 rejoin cohort did not leave")
        active.update(cohort)
    elif edit == "J":
        cohort = set(base.fresh_join)
        if cohort & active:
            raise ValueError("G34 fresh cohort already active")
        active.update(cohort)
    elif edit == "T":
        cohort = set(base.terminal_leave)
        if not cohort.issubset(active):
            raise ValueError("G34 terminal cohort inactive")
        active.difference_update(cohort)
    else:
        raise ValueError("G34 unknown lifecycle edit")
    if not active or len(active) > base.member_capacity:
        raise ValueError("G34 edit emptied or overflowed roster")


def _expected_roster_schedule(
    base: roster_env.CapacityRosterLedger,
    event_times: tuple[int, int, int, int],
    event_order: tuple[str, str, str, str],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    active = set(base.initial_keys)
    counts = [len(active)]
    schedule: list[int] = []
    edits = dict(zip(event_times, event_order))
    for time in range(roster_env.HORIZON):
        if time in edits:
            _apply_edit(active, base, edits[time])
            counts.append(len(active))
        schedule.append(len(active))
    return tuple(schedule), tuple(counts)


def make_process_ledgers(
    *, replicate: int, capacity: int, episode_count: int = EPISODES_PER_CELL
) -> tuple[RandomProcessLedger, ...]:
    if not 0 <= int(replicate) < 3 or capacity not in CAPACITIES:
        raise ValueError("G34 replicate or capacity outside registered support")
    if not 1 <= int(episode_count) <= EPISODES_PER_CELL:
        raise ValueError("G34 episode count outside registered support")
    times = _time_assignments(replicate=replicate, capacity=capacity)
    orders = _balanced_assignments(
        EVENT_ORDERS, replicate=replicate, capacity=capacity, stream=1
    )
    profiles = _profile_assignments(replicate=replicate, capacity=capacity)
    rows: list[RandomProcessLedger] = []
    for local_episode in range(int(episode_count)):
        base = roster_env.make_ledger(
            episode_address(capacity, local_episode),
            master_seed=BASE_LEDGER_SEED_BASE + int(replicate),
            profile=profiles[local_episode],
        )
        expected, trajectory = _expected_roster_schedule(
            base, times[local_episode], orders[local_episode]  # type: ignore[arg-type]
        )
        row = RandomProcessLedger(
            base=base,
            local_episode_id=local_episode,
            event_times=times[local_episode],
            event_order=orders[local_episode],  # type: ignore[arg-type]
            expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate()
        rows.append(row)
    if len({row.signature for row in rows}) != len(rows):
        raise ValueError("G34 process signatures must be unique")
    return tuple(rows)


class RandomProcessRosterEnv(roster_env.RuntimeCapacityRosterEnv):
    def __init__(self, process: RandomProcessLedger):
        process.validate()
        super().__init__(process.base)
        self.process = process

    def _prepare_membership(self) -> None:
        if self._prepared_time == self.time:
            return
        change = roster_env.MembershipChange()
        by_time = dict(zip(self.process.event_times, self.process.event_order))
        edit = by_time.get(self.time)
        if edit == "L":
            keys = self.ledger.temporarily_absent
            self.active[np.asarray(keys)] = False
            change = roster_env.MembershipChange(temporarily_left=keys)
        elif edit == "R":
            keys = self.ledger.temporarily_absent
            self.active[np.asarray(keys)] = True
            change = roster_env.MembershipChange(rejoined=keys)
        elif edit == "J":
            keys = self.ledger.fresh_join
            self.active[np.asarray(keys)] = True
            self.previous_actions[np.asarray(keys)] = 0.0
            self.age[np.asarray(keys)] = 0
            change = roster_env.MembershipChange(joined=keys)
        elif edit == "T":
            keys = self.ledger.terminal_leave
            self.active[np.asarray(keys)] = False
            change = roster_env.MembershipChange(terminally_left=keys)
        self._change = change
        self._prepared_time = self.time


def _episode_metrics(
    process: RandomProcessLedger,
    outcome: roster_env.CapacityRosterOutcome,
    *,
    expected_roster_sizes: tuple[int, ...] | None = None,
) -> dict[str, object]:
    rewards = np.asarray(outcome.reward_trace, dtype=np.float64)
    windows = {
        edit: float(rewards[time : time + 4].mean())
        for time, edit in zip(process.event_times, process.event_order)
    }
    boundaries = (0, *process.event_times, roster_env.HORIZON)
    segments = tuple(
        float(rewards[left:right].mean())
        for left, right in zip(boundaries, boundaries[1:])
    )
    return {
        "local_episode_id": process.local_episode_id,
        "episode_id": process.episode_id,
        "profile": process.profile.name,
        "event_times": list(process.event_times),
        "event_order": list(process.event_order),
        "count_trajectory": list(process.count_trajectory),
        "signature": repr(process.signature),
        "utility": float(rewards.mean()),
        "minimum_step_utility": float(rewards.min()),
        "minimum_event_window_utility": min(windows.values()),
        "minimum_process_segment_utility": min(segments),
        "event_window_utility": windows,
        "process_segment_utility": list(segments),
        "reward_trace": [float(value) for value in rewards],
        "roster_size_trace": [int(value) for value in outcome.roster_sizes],
        "roster_sizes_valid": outcome.roster_sizes
        == (expected_roster_sizes or process.expected_roster_sizes),
    }


def evaluate_constructive(
    processes: Sequence[RandomProcessLedger],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for process in processes:
        env = RandomProcessRosterEnv(process)
        while env.time < roster_env.HORIZON:
            view = env.observe()
            env.step(roster_env.constructive_actions(view))
        rows.append(_episode_metrics(process, env.outcome()))
    return tuple(rows)


def evaluate_model(
    model: ContinuousRosterPolicy,
    *,
    processes: Sequence[RandomProcessLedger],
    action_seed: int,
    process_kind: str,
    deterministic: bool,
    intervention: str = "none",
    device: torch.device = torch.device("cpu"),
) -> tuple[tuple[dict[str, object], ...], bool]:
    if process_kind not in ("random", "fixed"):
        raise ValueError("G34 process kind must be random or fixed")
    if intervention not in ("none", "time_rotated", "reactive"):
        raise ValueError("G34 unknown intervention")
    if intervention != "none" and (process_kind != "random" or model.member_capacity != 8):
        raise ValueError("G34 interventions are capacity-8 random-process only")
    rows = tuple(processes)
    if not rows or any(row.member_capacity != model.member_capacity for row in rows):
        raise ValueError("G34 model/process capacity mismatch")
    envs = tuple(
        RandomProcessRosterEnv(row)
        if process_kind == "random"
        else roster_env.RuntimeCapacityRosterEnv(row.base)
        for row in rows
    )
    ids = tuple(row.episode_id for row in rows)
    noise = roster_env.make_action_noise(
        ids, action_seed=int(action_seed), member_capacity=model.member_capacity
    )
    hidden = torch.zeros((len(rows), model.member_capacity, model.hidden_dim), device=device)
    frozen_hidden: list[dict[int, torch.Tensor]] = [dict() for _ in rows]
    frozen_age: list[dict[int, int]] = [dict() for _ in rows]
    frozen_previous_actions: list[dict[int, np.ndarray]] = [dict() for _ in rows]
    lifecycle_valid = True
    model.eval()
    with torch.no_grad():
        for time in range(roster_env.HORIZON):
            views = tuple(env.observe() for env in envs)
            if intervention == "reactive":
                hidden.zero_()
            for index, view in enumerate(views):
                for key in view.membership_change.temporarily_left:
                    frozen_hidden[index][key] = hidden[index, key].clone()
                    frozen_age[index][key] = int(envs[index].age[key])
                    frozen_previous_actions[index][key] = envs[index].previous_actions[
                        key
                    ].copy()
                for key, value in frozen_hidden[index].items():
                    if key not in view.membership_change.rejoined and not bool(view.active_mask[key]):
                        lifecycle_valid &= bool(torch.equal(hidden[index, key], value))
                        lifecycle_valid &= int(envs[index].age[key]) == frozen_age[index][key]
                        lifecycle_valid &= bool(
                            np.array_equal(
                                envs[index].previous_actions[key],
                                frozen_previous_actions[index][key],
                            )
                        )
                for key in view.membership_change.rejoined:
                    lifecycle_valid &= bool(
                        torch.equal(hidden[index, key], frozen_hidden[index][key])
                    )
                    lifecycle_valid &= int(envs[index].age[key]) == frozen_age[index][key]
                    lifecycle_valid &= bool(
                        np.array_equal(
                            envs[index].previous_actions[key],
                            frozen_previous_actions[index][key],
                        )
                    )
                    frozen_hidden[index].pop(key)
                    frozen_age[index].pop(key)
                    frozen_previous_actions[index].pop(key)
                for key in view.membership_change.joined:
                    lifecycle_valid &= bool(torch.count_nonzero(hidden[index, key]) == 0)
                    lifecycle_valid &= envs[index].age[key] == 0
                    lifecycle_valid &= not np.count_nonzero(envs[index].previous_actions[key])
            g32._delete_terminal_hidden(hidden, views)
            for index, view in enumerate(views):
                for key in view.membership_change.terminally_left:
                    lifecycle_valid &= bool(torch.count_nonzero(hidden[index, key]) == 0)
            observations = np.stack([view.observations for view in views])
            critic = np.stack([view.critic_state for view in views])
            if intervention == "time_rotated":
                rotated = np.float32(((time + TIME_ROTATION) % roster_env.HORIZON) / (roster_env.HORIZON - 1))
                observations = observations.copy()
                critic = critic.copy()
                observations[:, :, 9] = np.where(
                    np.stack([view.active_mask for view in views]), rotated, 0.0
                )
                critic[:, 5] = rotated
            elif intervention == "reactive":
                observations = observations.copy()
                observations[:, :, 6] = 0.0
                observations[:, :, 7:9] = np.where(
                    np.stack([view.active_mask for view in views])[:, :, None], 0.5, 0.0
                )
            active = torch.as_tensor(
                np.stack([view.active_mask for view in views]), device=device
            )
            arguments = {
                "observations": torch.as_tensor(observations, device=device),
                "active_mask": active,
                "critic_state": torch.as_tensor(critic, device=device),
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
            lifecycle_valid &= bool(
                torch.equal(output.next_hidden[~active], hidden[~active])
            )
            for index, env in enumerate(envs):
                env.step(output.actions[index].detach().cpu().numpy())
            hidden = output.next_hidden
    lifecycle_valid &= not any(frozen_hidden)
    lifecycle_valid &= not any(frozen_age)
    lifecycle_valid &= not any(frozen_previous_actions)
    metrics = tuple(
        _episode_metrics(
            process,
            env.outcome(),
            expected_roster_sizes=(
                process.expected_roster_sizes
                if process_kind == "random"
                else process.base.expected_roster_sizes
            ),
        )
        for process, env in zip(rows, envs)
    )
    return metrics, bool(lifecycle_valid)


def source_controls() -> dict[str, object]:
    return {
        "source_id": SOURCE_ID,
        "horizon": roster_env.HORIZON,
        "capacities": list(CAPACITIES),
        "event_count": 4,
        "event_orders": [list(row) for row in EVENT_ORDERS],
        "fixed_event_times": list(roster_env.EVENT_TIMES),
        "fixed_event_process": ["L", "R+J", "T"],
        "time_tuple_count": len(TIME_TUPLES),
        "time_minimum": 5,
        "time_maximum": 43,
        "minimum_separation": 5,
        "load_boundary_modulus_excluded": 4,
        "episodes_per_capacity_replicate": EPISODES_PER_CELL,
        "base_ledger_seed_base": BASE_LEDGER_SEED_BASE,
        "process_seed_base": PROCESS_SEED_BASE,
        "action_seed_base": ACTION_SEED_BASE,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
    }

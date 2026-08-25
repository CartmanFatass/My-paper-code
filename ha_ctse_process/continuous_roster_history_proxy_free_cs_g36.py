"""Frozen source-valid, actor-only history-proxy intervention for G36-P0."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy


ALGORITHM_ID = "CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36"
SOURCE_ID = "CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0"
DONOR_NAMESPACES = (0, 1, 2)
DONOR_CAPACITIES = g34.CAPACITIES
DONOR_PROCESSES = ("fixed", "random")
DONOR_EPISODES_PER_CAPACITY_PROCESS_NAMESPACE = 128
DONOR_BASE_LEDGER_SEED_BASE = 10_360_000
DONOR_PROCESS_SEED_BASE = 10_360_100
PROXY_ASSIGNMENT_SEED_BASE = 10_361_000
NONFORMAL_SEED_OFFSET = 900_000
BUNDLE_WIDTH = 4


def _profiles(*, namespace: int, capacity: int, process_seed: int) -> tuple[roster_env.RosterProfile, ...]:
    return g35._profile_assignments(  # type: ignore[attr-defined]
        replicate=namespace, capacity=capacity, process_seed=process_seed
    )


def _random_ledgers(*, namespace: int, capacity: int) -> tuple[g34.RandomProcessLedger, ...]:
    process_seed = DONOR_PROCESS_SEED_BASE + namespace
    times = g35._time_assignments(capacity=capacity, process_seed=process_seed)  # type: ignore[attr-defined]
    orders = g35._balanced_assignments(  # type: ignore[attr-defined]
        g34.EVENT_ORDERS, replicate=namespace, capacity=capacity,
        process_seed=process_seed, stream=1,
    )
    profiles = _profiles(namespace=namespace, capacity=capacity, process_seed=process_seed)
    rows: list[g34.RandomProcessLedger] = []
    for local_episode in range(DONOR_EPISODES_PER_CAPACITY_PROCESS_NAMESPACE):
        base = roster_env.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=DONOR_BASE_LEDGER_SEED_BASE + namespace,
            profile=profiles[local_episode],
        )
        expected, count_trajectory = g34._expected_roster_schedule(  # type: ignore[attr-defined]
            base, times[local_episode], orders[local_episode]
        )
        row = g34.RandomProcessLedger(
            base=base, local_episode_id=local_episode,
            event_times=times[local_episode], event_order=orders[local_episode],
            expected_roster_sizes=expected, count_trajectory=count_trajectory,
        )
        row.validate()
        rows.append(row)
    return tuple(rows)


def _fixed_ledgers(*, namespace: int, capacity: int) -> tuple[roster_env.CapacityRosterLedger, ...]:
    profiles = _profiles(
        namespace=namespace, capacity=capacity,
        process_seed=DONOR_PROCESS_SEED_BASE + namespace,
    )
    return tuple(
        roster_env.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=DONOR_BASE_LEDGER_SEED_BASE + namespace,
            profile=profiles[local_episode],
        )
        for local_episode in range(DONOR_EPISODES_PER_CAPACITY_PROCESS_NAMESPACE)
    )


def _event_map(ledger: roster_env.CapacityRosterLedger | g34.RandomProcessLedger) -> dict[int, str]:
    if isinstance(ledger, g34.RandomProcessLedger):
        return dict(zip(ledger.event_times, ledger.event_order))
    return dict(zip(roster_env.EVENT_TIMES, ("L", "RJ", "T")))


def _apply_donor_edit(
    active: np.ndarray, age: np.ndarray, previous_actions: np.ndarray,
    base: roster_env.CapacityRosterLedger, edit: str,
) -> None:
    if edit == "L":
        active[np.asarray(base.temporarily_absent)] = False
    elif edit == "R":
        active[np.asarray(base.temporarily_absent)] = True
    elif edit == "J":
        keys = np.asarray(base.fresh_join)
        active[keys] = True
        age[keys] = 0
        previous_actions[keys] = 0.0
    elif edit == "RJ":
        rejoined = np.asarray(base.temporarily_absent)
        joined = np.asarray(base.fresh_join)
        active[rejoined] = True
        active[joined] = True
        age[joined] = 0
        previous_actions[joined] = 0.0
    elif edit == "T":
        active[np.asarray(base.terminal_leave)] = False
    else:
        raise ValueError("G36 donor lifecycle edit mismatch")
    if not np.any(active):
        raise ValueError("G36 donor source produced an empty roster")


def _donor_snapshots(ledger: roster_env.CapacityRosterLedger | g34.RandomProcessLedger) -> tuple[tuple[int, np.ndarray], ...]:
    base = ledger.base if isinstance(ledger, g34.RandomProcessLedger) else ledger
    active = np.zeros(base.member_capacity, dtype=bool)
    active[np.asarray(base.initial_keys)] = True
    age = np.zeros(base.member_capacity, dtype=np.int64)
    previous_actions = np.zeros((base.member_capacity, roster_env.ACTION_DIM), dtype=np.float32)
    events = _event_map(ledger)
    rows: list[tuple[int, np.ndarray]] = []
    for time in range(roster_env.HORIZON):
        edit = events.get(time)
        if edit is not None:
            _apply_donor_edit(active, age, previous_actions, base, edit)
        keys = np.flatnonzero(active)
        bundle = np.empty((len(keys), BUNDLE_WIDTH), dtype=np.float32)
        bundle[:, 0] = age[keys] / float(roster_env.HORIZON)
        bundle[:, 1:3] = (previous_actions[keys] + 1.0) / 2.0
        bundle[:, 3] = time / float(roster_env.HORIZON - 1)
        if not np.isfinite(bundle).all() or np.any(bundle < 0.0) or np.any(bundle > 1.0):
            raise ValueError("G36 donor bundle support mismatch")
        rows.append((len(keys), bundle))
        previous_actions[keys, 0] = np.float32(2.0 * base.load[time] - 1.0)
        previous_actions[keys, 1] = np.float32(2.0 * base.target_mix[time] - 1.0)
        age[keys] += 1
    return tuple(rows)


@dataclass(frozen=True)
class G36HistoryProxyDonorBank:
    """Full donor-roster snapshots grouped exclusively by current active count."""

    _by_count: Mapping[int, np.ndarray]

    @classmethod
    @lru_cache(maxsize=1)
    def build(cls) -> "G36HistoryProxyDonorBank":
        grouped: dict[int, list[np.ndarray]] = defaultdict(list)
        for namespace in DONOR_NAMESPACES:
            for capacity in DONOR_CAPACITIES:
                for process in DONOR_PROCESSES:
                    ledgers: Sequence[roster_env.CapacityRosterLedger | g34.RandomProcessLedger]
                    ledgers = (
                        _fixed_ledgers(namespace=namespace, capacity=capacity)
                        if process == "fixed"
                        else _random_ledgers(namespace=namespace, capacity=capacity)
                    )
                    for ledger in ledgers:
                        for count, bundle in _donor_snapshots(ledger):
                            grouped[count].append(bundle)
        frozen = {count: np.stack(rows).astype(np.float32, copy=False) for count, rows in grouped.items()}
        if not frozen or any(value.ndim != 3 or value.shape[1] != count or value.shape[2] != BUNDLE_WIDTH for count, value in frozen.items()):
            raise ValueError("G36 donor bank construction mismatch")
        return cls(frozen)

    @property
    def supported_active_counts(self) -> tuple[int, ...]:
        return tuple(sorted(self._by_count))

    def snapshots(self, active_count: int) -> np.ndarray:
        try:
            return self._by_count[int(active_count)]
        except KeyError as error:
            raise ValueError("G36 donor bank missing active count") from error


class G36HistoryProxyTape:
    """Episode-addressed source-independent snapshot selection and permutation."""

    def __init__(self, bank: G36HistoryProxyDonorBank, *, replicate: int, capacity: int, formal: bool) -> None:
        if not 0 <= int(replicate) < 3 or capacity not in g34.CAPACITIES:
            raise ValueError("G36 proxy tape identity outside registered support")
        self.bank = bank
        self.replicate = int(replicate)
        self.capacity = int(capacity)
        self.seed = PROXY_ASSIGNMENT_SEED_BASE + self.replicate + (0 if formal else NONFORMAL_SEED_OFFSET)
        self._cache: dict[tuple[int, int, int], np.ndarray] = {}
        self.target_history_read_count = 0

    def bundle_for(self, *, episode_id: int, physical_call_position: int, active_mask: np.ndarray) -> np.ndarray:
        mask = np.asarray(active_mask, dtype=bool)
        if mask.shape != (self.capacity,):
            raise ValueError("G36 proxy tape active-mask shape mismatch")
        active_count = int(mask.sum())
        if active_count not in self.bank.supported_active_counts:
            raise ValueError("G36 proxy tape donor bank missing active count")
        key = (int(episode_id), int(physical_call_position), active_count)
        cached = self._cache.get(key)
        if cached is None:
            rng = np.random.default_rng(np.random.SeedSequence([self.seed, self.capacity, *key]))
            source = self.bank.snapshots(active_count)
            selected = source[int(rng.integers(0, len(source)))]
            cached = selected[rng.permutation(active_count)].copy()
            self._cache[key] = cached
        result = np.zeros((self.capacity, BUNDLE_WIDTH), dtype=np.float32)
        result[np.flatnonzero(mask)] = cached
        return result


def apply_g36_actor_history_proxy_transform(
    observations: np.ndarray, active_mask: np.ndarray, bundles: np.ndarray,
) -> tuple[np.ndarray, dict[str, int]]:
    """Replace only actor 6:10; no critic or target-history input is accepted."""
    actor = np.asarray(observations, dtype=np.float32)
    mask = np.asarray(active_mask, dtype=bool)
    proxy = np.asarray(bundles, dtype=np.float32)
    if actor.ndim != 3 or actor.shape[2] != roster_env.OBSERVATION_DIM or mask.shape != actor.shape[:2] or proxy.shape != (*actor.shape[:2], BUNDLE_WIDTH):
        raise ValueError("G36 actor transform shape mismatch")
    # The protected active-row coordinates are deliberately neither validated nor
    # copied: even a finite-value check would be an actual target-history read.
    if not np.isfinite(actor[:, :, :6]).all() or not np.isfinite(proxy).all():
        raise ValueError("G36 actor transform finite-value mismatch")
    if np.any(actor[~mask]) or np.any(proxy[~mask]) or np.any(proxy[mask] < 0.0) or np.any(proxy[mask] > 1.0):
        raise ValueError("G36 actor transform inactive/support mismatch")
    result = np.zeros_like(actor)
    result[:, :, :6] = actor[:, :, :6]
    result[mask, 6:10] = proxy[mask]
    return result, {
        "actual_age_read_count": 0,
        "actual_previous_action_read_count": 0,
        "actual_actor_time_read_count": 0,
        "critic_transform_count": 0,
    }


def build_g36_actor_input_without_history(
    source_observations: Sequence[np.ndarray],
    active_mask: np.ndarray,
    bundles: np.ndarray,
) -> tuple[np.ndarray, dict[str, int]]:
    """Construct actor input while never materializing source coordinates 6:10."""
    mask = np.asarray(active_mask, dtype=bool)
    proxy = np.asarray(bundles, dtype=np.float32)
    if not source_observations:
        raise ValueError("G36 actor input source inventory mismatch")
    public = np.stack(
        [np.asarray(row[:, :6], dtype=np.float32) for row in source_observations]
    )
    if (
        public.shape != (*mask.shape, 6)
        or proxy.shape != (*mask.shape, BUNDLE_WIDTH)
    ):
        raise ValueError("G36 actor input public-prefix shape mismatch")
    actor = np.zeros((*mask.shape, roster_env.OBSERVATION_DIM), dtype=np.float32)
    actor[:, :, :6] = public
    return apply_g36_actor_history_proxy_transform(actor, mask, proxy)


def evaluate_g36_history_proxy(
    model: ContinuousRosterPolicy, *, processes: Sequence[g34.RandomProcessLedger], action_seed: int,
    process_kind: str, deterministic: bool, tape: G36HistoryProxyTape,
    device: torch.device = torch.device("cpu"),
) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
    """Evaluate one intervention cell without changing source, critic, action RNG, or checkpoint."""
    if process_kind not in ("fixed", "random") or not processes:
        raise ValueError("G36 evaluation process mismatch")
    rows = tuple(processes)
    if any(row.member_capacity != model.member_capacity or row.member_capacity != tape.capacity for row in rows):
        raise ValueError("G36 evaluation capacity mismatch")
    envs = tuple(g34.RandomProcessRosterEnv(row) if process_kind == "random" else roster_env.RuntimeCapacityRosterEnv(row.base) for row in rows)
    noise = roster_env.make_action_noise((row.episode_id for row in rows), action_seed=action_seed, member_capacity=model.member_capacity)
    hidden = torch.zeros((len(rows), model.member_capacity, model.hidden_dim), device=device)
    audit: dict[str, int] | None = None
    lifecycle_valid = True
    proxy_hashes = [hashlib.sha256() for _ in rows]
    action_noise_digest = hashlib.sha256(
        np.ascontiguousarray(noise).tobytes()
    ).hexdigest()
    model.eval()
    with torch.no_grad():
        for time in range(roster_env.HORIZON):
            views = tuple(env.observe() for env in envs)
            g32._delete_terminal_hidden(hidden, views)
            active_mask = np.stack([view.active_mask for view in views])
            bundles = np.stack([tape.bundle_for(episode_id=row.episode_id, physical_call_position=time, active_mask=view.active_mask) for row, view in zip(rows, views)])
            for episode_index, bundle in enumerate(bundles):
                proxy_hashes[episode_index].update(
                    np.ascontiguousarray(bundle[active_mask[episode_index]]).tobytes()
                )
            transformed, step_audit = build_g36_actor_input_without_history(
                tuple(view.observations for view in views), active_mask, bundles
            )
            if audit is None:
                audit = step_audit
            elif step_audit != audit:
                raise ValueError("G36 actor transform audit mismatch")
            active = torch.as_tensor(active_mask, device=device)
            arguments: dict[str, Any] = {
                "observations": torch.as_tensor(transformed, device=device), "active_mask": active,
                "critic_state": torch.as_tensor(np.stack([view.critic_state for view in views]), device=device),
                "hidden": hidden,
            }
            output = model.forward_step(**arguments, deterministic=True) if deterministic else model.forward_step(**arguments, sampling_noise=torch.as_tensor(noise[time], device=device))
            lifecycle_valid &= bool(
                torch.equal(output.next_hidden[~active], hidden[~active])
                and torch.count_nonzero(output.next_hidden).item() == 0
                and all(
                    np.array_equal(
                        transformed[index, :, :6], view.observations[:, :6]
                    )
                    for index, view in enumerate(views)
                )
                and not np.any(transformed[~active_mask])
            )
            for index, env in enumerate(envs):
                env.step(output.actions[index].detach().cpu().numpy())
            hidden = output.next_hidden
    metrics = tuple(g34._episode_metrics(row, env.outcome(), expected_roster_sizes=(row.expected_roster_sizes if process_kind == "random" else row.base.expected_roster_sizes)) for row, env in zip(rows, envs))
    if audit is None:
        raise ValueError("G36 actor transform audit was not exercised")
    return metrics, {
        **audit,
        "checkpoint_update_count": 0,
        "lifecycle_valid": bool(lifecycle_valid),
        "proxy_tape_target_history_read_count": tape.target_history_read_count,
        "proxy_tape_episode_digests": [row.hexdigest() for row in proxy_hashes],
        "action_noise_digest": action_noise_digest,
    }

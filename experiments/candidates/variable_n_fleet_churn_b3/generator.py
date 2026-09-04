from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .config import EVAL_SCHEDULES, REGISTERED, TRAIN_SCHEDULES
from .rng import generator, opaque_handle
from typing import Callable

from .solver import CertificateMiss, certify_shared_histories


@dataclass(frozen=True)
class World:
    seed: int
    split: str
    schedule_index: int
    raw_index: int
    retained_index: int
    schedule: tuple[int, int]
    mass: str
    geometry: str
    churn: str
    handles: tuple[str, ...]
    capacities: np.ndarray
    demand: np.ndarray
    previous_roles: dict[str, int]
    new_handles: frozenset[str]
    tie_ranks: dict[str, int]
    certificates: dict[str, object]

    @property
    def n(self) -> int:
        return len(self.handles)

    @property
    def event(self) -> str:
        return "JOIN" if self.schedule[1] > self.schedule[0] else "DROP"

    def observation(self, order: list[int] | None = None) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
        order = list(range(self.n)) if order is None else list(order)
        handles = [self.handles[i] for i in order]
        agents = np.zeros((self.n, 9), dtype=np.float32)
        agents[:, :3] = self.capacities[order]
        for row, handle in enumerate(handles):
            if handle in self.previous_roles:
                agents[row, 3 + int(self.previous_roles[handle])] = 1.0
                agents[row, 7] = 1.0
            else:
                agents[row, 8] = 1.0
        tasks = np.concatenate((np.eye(3, dtype=np.float32), self.demand[:, None].astype(np.float32)), axis=1)
        global_row = np.asarray(
            [float(self.event == "JOIN"), float(self.event == "DROP"), np.log1p(self.n) / np.log(16.0)],
            dtype=np.float32,
        )
        return handles, agents, tasks, global_row


@dataclass(frozen=True)
class RetainedPanel:
    seed: int
    split: str
    schedule_index: int
    raw_index: int
    retained_index: int
    worlds: dict[tuple[str, str, str], World]
    certificate_calls: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class SeedBanks:
    seed: int
    training: dict[int, tuple[RetainedPanel, ...]]
    conclusion: dict[int, tuple[RetainedPanel, ...]]
    ledger: tuple[dict[str, object], ...]


def _block_matrix(mass: np.ndarray, geometry: str) -> np.ndarray:
    coefficients = np.asarray(
        [[.80, .10, .10], [.10, .80, .10], [.10, .10, .80]] if geometry == "SEPARABLE"
        else [[.48, .48, .04], [.48, .04, .48], [.04, .48, .48]], dtype=np.float64,
    )
    return coefficients * mass[None, :]


def _raw_variants(seed: int, split: str, schedule_index: int, raw_index: int, schedule: tuple[int, int]):
    pre_n, post_n = schedule
    blocks = max(pre_n, post_n) // 3
    demand_order = generator(seed, split, schedule_index, raw_index, "demand-permutation").permutation(3)
    demand = np.asarray((.95, 1.00, 1.05), dtype=np.float64)[demand_order]
    handles = tuple(
        opaque_handle(seed, split, schedule_index * 1000 + raw_index, block, row)
        for block in range(blocks) for row in range(3)
    )
    geometry_caps: dict[str, np.ndarray] = {}
    for geometry in ("SEPARABLE", "COUPLED"):
        rows = []
        for block in range(blocks):
            q = np.asarray([
                generator(seed, split, schedule_index, raw_index, "block-mass", block, task).uniform(.28, .36)
                for task in range(3)
            ])
            rows.append(_block_matrix(q * demand, geometry))
        geometry_caps[geometry] = np.concatenate(rows, axis=0)
    pre_handles = handles[:pre_n]
    post_handles = handles[:post_n]
    variants: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for mass in ("FIXED", "REAL"):
        for geometry in ("SEPARABLE", "COUPLED"):
            raw = geometry_caps[geometry]
            pre = raw[:pre_n].copy()  # FIXED pre-event capacity is intentionally raw.
            post = raw[:post_n].copy()
            if mass == "FIXED":
                post *= (1.25 * demand / post.sum(axis=0))[None, :]
            variants[f"{mass}-{geometry}"] = (pre, post)
    new_handles = frozenset(post_handles[pre_n:post_n]) if post_n > pre_n else frozenset()
    tie_ranks = {handle: rank for rank, handle in enumerate(post_handles)}
    return pre_handles, post_handles, demand, new_handles, tie_ranks, variants


def build_raw_panel(
    seed: int, split: str, schedule_index: int, raw_index: int, schedule: tuple[int, int], retained_index: int,
) -> tuple[RetainedPanel | None, list[dict[str, object]]]:
    pre_h, post_h, demand, new_handles, tie_ranks, variants = _raw_variants(
        seed, split, schedule_index, raw_index, schedule,
    )
    try:
        certificate = certify_shared_histories(pre_h, post_h, demand, variants)
    except CertificateMiss as miss:
        return None, miss.calls
    if certificate is None:
        # A completed 24-call routine whose qualification inequalities miss.
        return None, []
    survivors = set(pre_h).intersection(post_h)
    worlds: dict[tuple[str, str, str], World] = {}
    for mass_label, prefix in (("FIXED_MASS", "FIXED"), ("REAL_MASS", "REAL")):
        for geometry in ("SEPARABLE", "COUPLED"):
            variant = f"{prefix}-{geometry}"
            post_cap = variants[variant][1]
            values = certificate.by_variant[variant]
            for churn, short in (("KEEP_OPTIMAL", "KEEP"), ("SWITCH_REQUIRED", "SWITCH")):
                full_history = certificate.keep_history if short == "KEEP" else certificate.switch_history
                history = {h: int(full_history[h]) for h in survivors}
                cert = {
                    "unrestricted_ceiling": float(values[f"R_{short}"]),
                    "unrestricted_ceiling_assignment": dict(values[f"R_{short}_assignment"]),
                    "all_survivors_kept_ceiling": float(values[f"K_{short}"]),
                    "keep_gap": float(values[f"R_{short}"]) - float(values[f"K_{short}"]),
                    "S_star": float(values["S_star"]),
                    "certificate_calls_for_raw_base": 24,
                }
                worlds[(mass_label, geometry, churn)] = World(
                    seed, split, schedule_index, raw_index, retained_index, schedule,
                    mass_label, geometry, churn, post_h, post_cap.copy(), demand.copy(), history,
                    new_handles, dict(tie_ranks), cert,
                )
    return RetainedPanel(seed, split, schedule_index, raw_index, retained_index,
                         worlds, tuple(certificate.calls)), certificate.calls


def _scan_schedule(seed: int, split: str, schedule_index: int, schedule: tuple[int, int],
                   raw_cap: int, target: int, progress_guard: Callable[[], None] | None = None,
                   ) -> tuple[tuple[RetainedPanel, ...], list[dict[str, object]]]:
    retained: list[RetainedPanel] = []
    ledger: list[dict[str, object]] = []
    for raw_index in range(raw_cap):
        if progress_guard is not None:
            progress_guard()
        panel, calls = build_raw_panel(seed, split, schedule_index, raw_index, schedule, len(retained))
        ledger.append({
            "seed": seed, "split": split, "schedule_index": schedule_index,
            "schedule": f"{schedule[0]}->{schedule[1]}", "raw_index": raw_index,
            "certificate_success": panel is not None, "logical_calls": len(calls), "calls": calls,
        })
        if panel is not None:
            retained.append(panel)
            if len(retained) == target:
                break
    if len(retained) != target:
        raise RuntimeError(
            f"preactivity bank infeasibility seed={seed} split={split} schedule_index={schedule_index}: "
            f"retained={len(retained)} required={target} raw_cap={raw_cap}"
        )
    return tuple(retained), ledger


def build_seed_banks(seed: int, progress_guard: Callable[[], None] | None = None) -> SeedBanks:
    training: dict[int, tuple[RetainedPanel, ...]] = {}
    conclusion: dict[int, tuple[RetainedPanel, ...]] = {}
    ledger: list[dict[str, object]] = []
    for index, schedule in enumerate(TRAIN_SCHEDULES):
        training[index], part = _scan_schedule(
            seed, "training", index, schedule, REGISTERED.training_raw_cap, REGISTERED.training_successes,
            progress_guard,
        )
        ledger.extend(part)
    for index, schedule in enumerate(EVAL_SCHEDULES):
        conclusion[index], part = _scan_schedule(
            seed, "conclusion", index, schedule, REGISTERED.conclusion_raw_cap, REGISTERED.conclusion_successes,
            progress_guard,
        )
        ledger.extend(part)
    return SeedBanks(seed, training, conclusion, tuple(ledger))


def training_row_order(world: World, action_replica: int) -> list[int]:
    return list(generator(
        world.seed, "training", world.schedule_index, world.raw_index,
        "agent-row-order", action_replica,
    ).permutation(world.n))


def conclusion_row_order(world: World, replica: int) -> list[int]:
    ascending = sorted(range(world.n), key=lambda row: world.tie_ranks[world.handles[row]])
    if replica == 0:
        return ascending
    if replica == 1:
        return list(reversed(ascending))
    permutation = generator(
        world.seed, "conclusion", world.schedule_index, world.raw_index,
        "agent-row-order", replica,
    ).permutation(world.n)
    return [ascending[int(i)] for i in permutation]

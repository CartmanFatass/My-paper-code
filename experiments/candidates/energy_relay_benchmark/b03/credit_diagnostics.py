"""Zero-fit removal-difference probe under H_central (``credit-diagnostics`` phase, CPU).

H_central exactly as the ``stake-sizing`` phase runs it (``b03/stake_sizing.py``: H1, production
shield, ``STAKE_SPEC`` horizon and evaluator seed), **hungarian** assignment mode only, on the
development worlds 955001-955032, with a per-step observer passed as ``observer=`` to
``b01.evaluation.evaluate_world``.  Nothing is trained.

``RemovalProbeObserver`` reads only the raw ``UAVEnergyAwareRelayEnv`` (``env.env``) and never
mutates it.  Every step it records the collection wall; every ``PROBE_EVERY``-th step it records

- the live QoS from the reward's own stored fields (``last_delivered_traffic_bps /
  last_user_demand_bps``), each user's server (argmax of the reward's ``delivered_by_uav``,
  first index on ties, users with rate > 0), per-UAV served traffic and path hops
  (``routing_paths``), R1 (the UAV is an intermediate node of another UAV's path) and R2 (the
  UAV's current plan target is a relay row of the last H_central plan), the relay-hop traffic
  and user shares (users whose server's path has >= 2 hops);
- on deep copies of the raw env: the QoS recomputed after channel/connections/routing
  (``qos_copy_baseline``) and, for each UAV i, the same recompute with ``uav_battery_ratios[i] =
  0`` (``qos_removed[i]``); ``D[i] = qos_live - qos_removed[i]``.

Two record-only bit-identity layers: (a) the phase's hungarian panel against Stage 1's recorded
H_central panel (``stake_sizing.consistency_check``); (b) ``BIT_IDENTITY_WORLD`` run twice more
in the runner process: plain (``stake_sizing.evaluate_stake_task``, no observer) and with
``RawProbeObserver`` (``_static_qos_with_unavailable_uavs([i])`` on the live env at every step);
``reward`` and ``own_xyz`` are compared plain vs the phase's run and plain vs raw probe.

Outputs under ``<out>/credit-diagnostics/``: ``config.json``, ``summary.json``,
``progress.jsonl``, ``panels/hungarian.json``, ``traces/hungarian.npz`` (``trace_arrays``),
``traces/credit_hungarian.npz`` (probe arrays) and ``bit_identity.json``.
"""

from __future__ import annotations

import copy
import math
import multiprocessing
import os
import resource
import sys
import tempfile
import time
from contextlib import nullcontext
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    CONTROLLER_INFORMATION,
    PLAN_SOURCE,
    REFERENCE_INFORMATION,
    TRACE_TIMING,
    UnobservedRegime,
    aggregate,
    evaluate_world,
    make_env,
    make_eval_config,
    sha256_file,
    trace_arrays,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    N_UAVS,
    PRODUCTION_PARAMS,
    FeedbackParams,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import HeuristicParams
from experiments.candidates.energy_relay_benchmark.b01.native import (
    HOLDOUT_WORLD_FLOOR,
    _progress,
    check_resources,
)
from experiments.candidates.uav_service_auxiliary.b09.persistence import write_summary

from . import stake_sizing as ss
from .assignment_modes import AssignmentModeController
from .stake_sizing import (
    CONSISTENCY_TOLERANCE,
    MODE_RULES,
    RECORDED_PANEL,
    REPO_ROOT,
    STAKE_CONTROLLER,
    STAKE_WORLDS,
    StakeTask,
    _git_head,
    _stake_heuristic,
    consistency_check,
    paired_block,
)

OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B03-CREDIT-DIAGNOSTICS"
CREDIT_PHASE = "credit-diagnostics"
PROBE_EVERY = 10
PROBE_MODE = "hungarian"
BIT_IDENTITY_WORLD = 955001
SPARSITY_THRESHOLD = 0.01
RHO_LARGE = 0.25
DECLARED_MAX_SLOWDOWN = 1.5
RULE_THRESHOLDS = {"relay_hop_share": (0.10, 0.25), "relay_ratio_R1": 2.0,
                   "sparsity_available": 0.80}
COMPARED_FIELDS = ("reward", "own_xyz")
DEFINITIONS = {
    "qos_live": "mean(raw.last_delivered_traffic_bps / raw.last_user_demand_bps) (reward fields)",
    "recompute": ("deepcopy(raw); _update_channel_state(); _update_uav_connections(); "
                  "_compute_routing_paths(); rates = _calculate_end_to_end_user_rates()[0]; "
                  "demand = _current_user_qos_demand_bps(); mean(minimum(rates, demand)/demand)"),
    "qos_removed[i]": "recompute on a fresh deep copy with uav_battery_ratios[i] = 0.0",
    "D[i]": "qos_live - qos_removed[i]",
    "server": ("argmax_i delivered_by_uav[i, u] (first index on ties) for users with rate > 0; "
               "delivered_by_uav from last_access_capacity_bps / last_backhaul_capacities_bps "
               "with the env's scale = min(1, backhaul / max(access_sum, 1e-8))"),
    "path_hops[i]": "len(routing_paths[i][0]) - 1, 0 without a path",
    "R1": "UAV i appears as ('uav', i) at index >= 1 of another UAV's routing path",
    "R2": ("controller.heuristic.last_plan['targets'][i] finite and exactly equal to a "
           "priority row whose kind is 'relay'"),
    "relay_hop_traffic_share": ("sum of last_delivered_traffic_bps over users whose server has "
                                "path_hops >= 2 / sum over all users (NaN if 0)"),
    "relay_hop_user_share": ("users with delivered > 0 whose server has path_hops >= 2 / users "
                             "with delivered > 0 (NaN if 0)"),
    "relay_vs_other_uav_steps": ("relay = flag & available; other = ~flag & available; flagged "
                                 "but unavailable UAV-steps are counted separately"),
    "rho_t": "(sum_i D_i - qos_live) / qos_live over probe steps with qos_live > 0",
    "collection_wall_s[t]": ("perf_counter at on_step(t) entry - perf_counter at on_step(t-1) "
                             "exit; NaN at step 0 (excludes the probe)"),
    "probe_wall_s": "wall of the nine deep copies and recomputes of one probe step",
}
# Probe arrays per step (in-memory float64; saved dtype in ``PROBE_DTYPES``).
STEP_KEYS = ("probe_step", "qos_live", "qos_copy_baseline", "relay_hop_traffic_share",
             "relay_hop_user_share", "total_delivered_bps", "relay_hop_traffic_bps",
             "relay_hop_users", "delivered_users", "probe_wall_s")
UAV_KEYS = ("qos_removed", "D", "available", "served_traffic_bps", "path_hops",
            "is_intermediate", "relay_slot")
PROBE_DTYPES = {"probe_step": np.int32, "path_hops": np.int8, "available": np.bool_,
                "is_intermediate": np.bool_, "relay_slot": np.bool_,
                "relay_hop_users": np.int16, "delivered_users": np.int16,
                "probe_wall_s": np.float64, "collection_wall_s": np.float64}


# ----------------------------------------------------------------------------- probe pieces

def delivered_by_uav(access_bps, backhaul_bps) -> np.ndarray:
    """``_calculate_end_to_end_user_rates``' delivered_by_uav from its stored capacities."""
    access = np.asarray(access_bps, dtype=np.float64)
    backhaul = np.asarray(backhaul_bps, dtype=np.float64)
    delivered = np.zeros_like(access)
    for uav in range(access.shape[0]):
        access_sum = float(np.sum(access[uav]))
        if access_sum <= 0.0 or backhaul[uav] <= 0.0:
            continue
        scale = min(1.0, backhaul[uav] / max(access_sum, 1e-8))
        delivered[uav] = scale * access[uav]
    return delivered


def user_servers(delivered: np.ndarray) -> np.ndarray:
    """Server UAV per user (first index on ties); -1 for users with rate <= 0."""
    delivered = np.asarray(delivered, dtype=np.float64)
    if delivered.shape[0] == 0:
        return np.full(delivered.shape[1], -1, dtype=np.int64)
    servers = np.argmax(delivered, axis=0).astype(np.int64)
    servers[~(np.max(delivered, axis=0) > 0.0)] = -1
    return servers


def path_structure(routing_paths: dict, n_uavs: int) -> tuple[np.ndarray, np.ndarray]:
    """(path_hops, is_intermediate) from ``routing_paths[uav] = (path, capacity)``."""
    hops = np.zeros(n_uavs, dtype=np.int64)
    intermediate = np.zeros(n_uavs, dtype=bool)
    for uav in range(n_uavs):
        record = routing_paths.get(uav)
        path = record[0] if record else None
        hops[uav] = len(path) - 1 if path else 0
    for owner, record in routing_paths.items():
        path = record[0] if record else None
        for node in (path or [])[1:]:
            if node[0] == "uav" and int(node[1]) != int(owner) and 0 <= int(node[1]) < n_uavs:
                intermediate[int(node[1])] = True
    return hops, intermediate


def relay_slot_mask(last_plan: dict | None, n_uavs: int) -> np.ndarray:
    """R2: the UAV's plan target is finite and exactly a relay row of the plan's priority."""
    mask = np.zeros(n_uavs, dtype=bool)
    if last_plan is None:
        return mask
    targets = np.asarray(last_plan["targets"], dtype=np.float64)
    priority = np.asarray(last_plan["priority"], dtype=np.float64).reshape(-1, 2)
    relay_rows = [priority[row] for row, kind in enumerate(last_plan["kinds"]) if kind == "relay"]
    for uav in range(min(n_uavs, len(targets))):
        target = targets[uav]
        if np.all(np.isfinite(target)) and any(np.array_equal(target, row) for row in relay_rows):
            mask[uav] = True
    return mask


def relay_hop_shares(delivered_traffic_bps, servers, path_hops) -> dict[str, float]:
    """Relay-hop traffic/user shares: users whose server's path has >= 2 hops."""
    delivered = np.asarray(delivered_traffic_bps, dtype=np.float64)
    servers = np.asarray(servers, dtype=np.int64)
    hops = np.asarray(path_hops)
    has_server = servers >= 0
    relay_user = np.zeros(delivered.shape, dtype=bool)
    relay_user[has_server] = hops[servers[has_server]] >= 2
    total = float(np.sum(delivered))
    relay_traffic = float(np.sum(delivered[relay_user]))
    served = delivered > 0.0
    delivered_users = int(np.sum(served))
    relay_users = int(np.sum(served & relay_user))
    return {"relay_hop_traffic_share": relay_traffic / total if total > 0.0 else math.nan,
            "relay_hop_user_share": (relay_users / delivered_users if delivered_users
                                     else math.nan),
            "total_delivered_bps": total, "relay_hop_traffic_bps": relay_traffic,
            "relay_hop_users": relay_users, "delivered_users": delivered_users}


def served_traffic(delivered_traffic_bps, servers, n_uavs: int) -> np.ndarray:
    delivered = np.asarray(delivered_traffic_bps, dtype=np.float64)
    servers = np.asarray(servers, dtype=np.int64)
    served = np.zeros(n_uavs, dtype=np.float64)
    for uav in range(n_uavs):
        served[uav] = float(np.sum(delivered[servers == uav]))
    return served


def recomputed_qos(raw_copy) -> float:
    """QoS of a (copied) raw env after the channel/connections/routing/rates recompute."""
    raw_copy._update_channel_state()
    raw_copy._update_uav_connections()
    raw_copy._compute_routing_paths()
    rates = raw_copy._calculate_end_to_end_user_rates()[0]
    demand = raw_copy._current_user_qos_demand_bps()
    return float(np.mean(np.minimum(rates, demand) / demand))


def removal_qos(raw, n_uavs: int) -> tuple[float, np.ndarray]:
    """(qos_copy_baseline, qos_removed[i]) on nine deep copies; ``raw`` is never touched."""
    baseline = recomputed_qos(copy.deepcopy(raw))
    removed = np.empty(n_uavs, dtype=np.float64)
    for uav in range(n_uavs):
        raw_copy = copy.deepcopy(raw)
        raw_copy.uav_battery_ratios[uav] = 0.0
        removed[uav] = recomputed_qos(raw_copy)
    return baseline, removed


def probe_raw(raw, controller, step: int) -> dict[str, Any]:
    """One probe step on the raw env (read-only on ``raw``)."""
    n_uavs = int(raw.n_uavs)
    delivered_traffic = np.asarray(raw.last_delivered_traffic_bps, dtype=np.float64)
    qos_live = float(np.mean(delivered_traffic / np.asarray(raw.last_user_demand_bps,
                                                            dtype=np.float64)))
    servers = user_servers(delivered_by_uav(raw.last_access_capacity_bps,
                                            raw.last_backhaul_capacities_bps))
    hops, intermediate = path_structure(raw.routing_paths, n_uavs)
    plan = getattr(getattr(controller, "heuristic", None), "last_plan", None)
    record: dict[str, Any] = {
        "probe_step": int(step), "qos_live": qos_live,
        "available": ~np.asarray(raw._communication_unavailable_mask(), dtype=bool).copy(),
        "served_traffic_bps": served_traffic(delivered_traffic, servers, n_uavs),
        "path_hops": hops, "is_intermediate": intermediate,
        "relay_slot": relay_slot_mask(plan, n_uavs),
    }
    record.update(relay_hop_shares(delivered_traffic, servers, hops))
    started = time.perf_counter()
    baseline, removed = removal_qos(raw, n_uavs)
    record.update(probe_wall_s=time.perf_counter() - started, qos_copy_baseline=baseline,
                  qos_removed=removed, D=qos_live - removed)
    return record


class RemovalProbeObserver:
    """``evaluate_world`` observer: collection wall every step, removal probe every k-th."""

    def __init__(self, env, probe_every: int = PROBE_EVERY):
        self.raw = env.env
        self.probe_every = int(probe_every)
        if self.probe_every < 1:
            raise ValueError("probe_every must be positive")
        self.collection_wall_s: list[float] = []
        self.records: list[dict[str, Any]] = []
        self._last_exit: float | None = None

    def attach(self, controller):
        return nullcontext()

    def on_step(self, *, t, controller, **_unused) -> None:
        entry = time.perf_counter()
        self.collection_wall_s.append(math.nan if self._last_exit is None
                                      else entry - self._last_exit)
        if int(t) % self.probe_every == 0:
            self.records.append(probe_raw(self.raw, controller, int(t)))
        self._last_exit = time.perf_counter()

    @property
    def baseline_mismatch_steps(self) -> int:
        return int(sum(record["qos_copy_baseline"] != record["qos_live"]
                       for record in self.records))

    def as_arrays(self) -> dict[str, np.ndarray]:
        """Stacked probe records (float64 / bool / int64) plus ``collection_wall_s``."""
        n_uavs = int(self.raw.n_uavs)
        arrays: dict[str, np.ndarray] = {}
        for key in STEP_KEYS:
            values = [record[key] for record in self.records]
            dtype = np.int64 if key in ("probe_step", "relay_hop_users", "delivered_users") \
                else np.float64
            arrays[key] = np.asarray(values, dtype=dtype).reshape(len(values))
        for key in UAV_KEYS:
            values = [record[key] for record in self.records]
            dtype = (bool if key in ("available", "is_intermediate", "relay_slot")
                     else np.int64 if key == "path_hops" else np.float64)
            arrays[key] = np.asarray(values, dtype=dtype).reshape(len(values), n_uavs)
        arrays["collection_wall_s"] = np.asarray(self.collection_wall_s, dtype=np.float64)
        return arrays


class RawProbeObserver:
    """Bit-identity layer (b): ``_static_qos_with_unavailable_uavs([i])`` on the live env at
    every step (a perturbation probe; its values are not readings)."""

    def __init__(self, env, n_uavs: int = N_UAVS):
        self.raw = env.env
        self.n_uavs = int(n_uavs)
        self.calls = 0
        self.wall_s = 0.0

    def attach(self, controller):
        return nullcontext()

    def on_step(self, **_unused) -> None:
        started = time.perf_counter()
        for uav in range(self.n_uavs):
            self.raw._static_qos_with_unavailable_uavs([uav])
        self.calls += self.n_uavs
        self.wall_s += time.perf_counter() - started


# ----------------------------------------------------------------------------- worker

@dataclass(frozen=True)
class CreditTask:
    """Picklable description of one world (hungarian mode; the observer is built in-worker)."""

    seed: int
    params: FeedbackParams
    horizon: int
    policy_seed: int
    threads: int
    heuristic: HeuristicParams
    log_dir: str | None = None
    controller: str = STAKE_CONTROLLER
    probe_every: int = PROBE_EVERY


def _run_hungarian_world(task: CreditTask, make_observer: Callable | None):
    """``evaluate_stake_task``'s body (mode ``hungarian``) with ``observer=`` passed through."""
    started = time.perf_counter()
    torch.set_num_threads(int(task.threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B01 requires Torch FP32 default dtype")
    config = make_eval_config(task.horizon, task.policy_seed)
    observer = None
    with tempfile.TemporaryDirectory(prefix="b01-agent-logs-", dir=task.log_dir):
        env = make_env(config, task.seed)
        try:
            if task.heuristic is None:
                raise ValueError("heuristic controller requires HeuristicParams")
            controller = AssignmentModeController(task.heuristic, env, PROBE_MODE)
            observer = make_observer(env) if make_observer is not None else None
            labels = dict(
                controller_information=REFERENCE_INFORMATION.get(
                    task.controller, CONTROLLER_INFORMATION[task.heuristic.information]),
                plan_source=(PLAN_SOURCE if task.heuristic.information == "central"
                             else "legal-observation"),
            )
            try:
                row, arrays = evaluate_world(controller, env, config, task.seed, task.params,
                                             observer=observer)
            except UnobservedRegime as exc:
                # Recorded, never silently skipped: the world is marked failed.
                row, arrays = {"seed": int(task.seed), "failed": True,
                               "failure": f"UnobservedRegime: {exc}", **labels}, {}
            else:
                row.update(
                    failed=False, **labels,
                    plan_input_steps=len(controller.plan_input_steps),
                    search_replans=len(controller.search_replan_steps),
                    replans=-(-row["actual_length"] // task.heuristic.replan_period),
                )
        finally:
            env.close()
    row.update(controller=task.controller, enter_margin=task.params.enter_margin,
               exit_margin=task.params.exit_margin,
               wall_seconds=time.perf_counter() - started,
               worker_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
               action_mode="deterministic")
    row["assignment_mode"] = PROBE_MODE
    return row, arrays, observer


def _finite_mean(values) -> float | None:
    values = np.asarray(values, dtype=np.float64).ravel()
    values = values[np.isfinite(values)]
    return float(values.mean()) if values.size else None


def evaluate_credit_task(task: CreditTask) -> dict[str, Any]:
    """Module-level worker: the hungarian stake worker with ``RemovalProbeObserver``."""
    row, arrays, observer = _run_hungarian_world(
        task, lambda env: RemovalProbeObserver(env, task.probe_every))
    probe = observer.as_arrays() if observer is not None else None
    records = observer.records if observer is not None else []
    row.update(probe_every=int(task.probe_every), probe_steps=len(records),
               baseline_mismatch_steps=(observer.baseline_mismatch_steps
                                        if observer is not None else 0),
               probe_wall_mean_s=_finite_mean([r["probe_wall_s"] for r in records]),
               collection_wall_mean_s=(_finite_mean(observer.collection_wall_s)
                                       if observer is not None else None))
    return {"row": row, "arrays": arrays, "probe": None if row.get("failed") else probe}


def run_credit_tasks(tasks: Iterable[CreditTask], workers: int, *,
                     on_result: Callable[[dict[str, Any]], None] | None = None
                     ) -> list[dict[str, Any]]:
    """``run_stake_tasks`` over ``evaluate_credit_task``: serial or spawn pool; ordered by seed."""
    tasks = list(tasks)
    results = []
    if int(workers) <= 1 or len(tasks) <= 1:
        for task in tasks:
            result = evaluate_credit_task(task)
            results.append(result)
            if on_result is not None:
                on_result(result)
    else:
        context = multiprocessing.get_context("spawn")
        with context.Pool(processes=min(int(workers), len(tasks))) as pool:
            for result in pool.imap(evaluate_credit_task, tasks, chunksize=1):
                results.append(result)
                if on_result is not None:
                    on_result(result)
    return sorted(results, key=lambda item: item["row"]["seed"])


def credit_trace_arrays(results: list[dict[str, Any]], worlds, horizon: int,
                        probe_every: int) -> dict[str, np.ndarray]:
    """Probe arrays with a leading world axis (``worlds`` order); failed or absent worlds and
    padding past a world's last probe are NaN (float), -1 (int) or False (bool)."""
    worlds = [int(seed) for seed in worlds]
    n_worlds, n_probes = len(worlds), -(-int(horizon) // int(probe_every))
    by_seed = {int(result["row"]["seed"]): result for result in results}

    def empty(shape, key):
        dtype = PROBE_DTYPES.get(key, np.float32)
        if dtype is np.bool_:
            return np.zeros(shape, dtype=bool)
        if np.issubdtype(dtype, np.integer):
            return np.full(shape, -1, dtype=dtype)
        return np.full(shape, np.nan, dtype=dtype)

    arrays = {key: empty((n_worlds, n_probes), key) for key in STEP_KEYS}
    arrays.update({key: empty((n_worlds, n_probes, N_UAVS), key) for key in UAV_KEYS})
    arrays["collection_wall_s"] = empty((n_worlds, int(horizon)), "collection_wall_s")
    failed = np.ones(n_worlds, dtype=bool)
    counts = np.zeros(n_worlds, dtype=np.int32)
    for index, seed in enumerate(worlds):
        result = by_seed.get(seed)
        probe = None if result is None or result["row"].get("failed") else result.get("probe")
        if probe is None:
            continue
        failed[index] = False
        count = min(len(probe["probe_step"]), n_probes)
        counts[index] = count
        for key in STEP_KEYS + UAV_KEYS:
            arrays[key][index, :count] = probe[key][:count]
        steps = min(len(probe["collection_wall_s"]), int(horizon))
        arrays["collection_wall_s"][index, :steps] = probe["collection_wall_s"][:steps]
    arrays.update(worlds=np.asarray(worlds, dtype=np.int64), failed=failed, probe_count=counts,
                  probe_every=np.asarray(int(probe_every), dtype=np.int32))
    return arrays


# ----------------------------------------------------------------------------- readings

def _clean(value):
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def world_block(per_world: list) -> dict[str, Any]:
    """Per-world values with the mean and SE (sd ddof 1 / sqrt(n)) as ``paired_block`` does."""
    cleaned = [_clean(value) for value in per_world]
    block = paired_block(cleaned, count_label="worlds_above_zero", count_sign="positive")
    return {"mean": block["paired_mean"], "se": block["paired_se"],
            "n_worlds": block["n_worlds"], "per_world": cleaned}


def _ratio(numerator, denominator):
    numerator, denominator = _clean(numerator), _clean(denominator)
    if numerator is None or denominator is None or denominator == 0.0:
        return None
    return numerator / denominator


def _abs_stats(values: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    magnitude = np.abs(values)
    if not values.size:
        return {"n_uav_steps": 0, "mean_abs": None, "median_abs": None, "q90_abs": None,
                "q99_abs": None, "sparsity": None, "fraction_negative": None}
    return {"n_uav_steps": int(values.size), "mean_abs": float(magnitude.mean()),
            "median_abs": float(np.median(magnitude)),
            "q90_abs": float(np.quantile(magnitude, 0.90)),
            "q99_abs": float(np.quantile(magnitude, 0.99)),
            "sparsity": float(np.mean(magnitude < SPARSITY_THRESHOLD)),
            "fraction_negative": float(np.mean(values < 0.0))}


def _stats_with_worlds(per_world_values: list[np.ndarray | None]) -> dict[str, Any]:
    pooled = [values for values in per_world_values if values is not None]
    block = {"pooled": _abs_stats(np.concatenate(pooled) if pooled else np.zeros(0))}
    per_world = [None if values is None else _abs_stats(values) for values in per_world_values]
    for key in ("mean_abs", "median_abs", "q90_abs", "q99_abs", "sparsity", "fraction_negative"):
        block[f"per_world_{key}"] = world_block(
            [None if stats is None else stats[key] for stats in per_world])
    return block


def _relay_stats(D, available, flag) -> dict[str, Any]:
    magnitude = np.abs(np.asarray(D, dtype=np.float64))
    relay = flag & available
    other = ~flag & available
    total = float(magnitude.sum())
    mean_relay = float(magnitude[relay].mean()) if relay.any() else None
    mean_other = float(magnitude[other].mean()) if other.any() else None
    return {"mean_abs_relay": mean_relay, "mean_abs_other_available": mean_other,
            "ratio": _ratio(mean_relay, mean_other), "relay_uav_steps": int(relay.sum()),
            "other_available_uav_steps": int(other.sum()),
            "flagged_unavailable_uav_steps": int((flag & ~available).sum()),
            "d_mass_share": (float(magnitude[relay].sum()) / total) if total > 0.0 else None}


def _quantile(values: np.ndarray, q: float):
    return float(np.quantile(values, q)) if values.size else None


def credit_readings(probes: list[dict[str, np.ndarray] | None], worlds) -> dict[str, Any]:
    """Readings from per-world probe arrays aligned with ``worlds`` (None = failed world)."""
    worlds = [int(seed) for seed in worlds]
    if len(probes) != len(worlds):
        raise ValueError("one probe entry per world is required")
    live = [p for p in probes if p is not None]

    def pooled(key):
        return (np.concatenate([np.asarray(p[key]) for p in live]) if live
                else np.zeros(0))

    def per_world(function):
        return [None if p is None or len(p["probe_step"]) == 0 else function(p) for p in probes]

    readings: dict[str, Any] = {
        "worlds": worlds, "failed_worlds": [seed for seed, p in zip(worlds, probes) if p is None],
        "n_probe_steps": int(sum(len(p["probe_step"]) for p in live)),
        "sparsity_threshold": SPARSITY_THRESHOLD,
    }
    # Relay-hop traffic and user shares.
    total = pooled("total_delivered_bps")
    readings["relay_hop_traffic_share"] = {
        "pooled_traffic_weighted": (float(pooled("relay_hop_traffic_bps").sum() / total.sum())
                                    if total.size and total.sum() > 0 else None),
        "per_world_step_mean": world_block(
            per_world(lambda p: _finite_mean(p["relay_hop_traffic_share"]))),
    }
    delivered_users = pooled("delivered_users")
    readings["relay_hop_user_share"] = {
        "pooled_user_weighted": (float(pooled("relay_hop_users").sum() / delivered_users.sum())
                                 if delivered_users.size and delivered_users.sum() > 0 else None),
        "per_world_step_mean": world_block(
            per_world(lambda p: _finite_mean(p["relay_hop_user_share"]))),
    }
    # R1 prevalence.
    intermediate = pooled("is_intermediate").reshape(-1, N_UAVS).astype(bool)
    readings["r1_any_share"] = {
        "pooled": float(intermediate.any(axis=1).mean()) if intermediate.size else None,
        "per_world_step_mean": world_block(
            per_world(lambda p: float(np.asarray(p["is_intermediate"]).any(axis=1).mean()))),
    }
    readings["r1_mean_count"] = {
        "pooled": float(intermediate.sum(axis=1).mean()) if intermediate.size else None,
        "per_world_step_mean": world_block(
            per_world(lambda p: float(np.asarray(p["is_intermediate"]).sum(axis=1).mean()))),
    }
    # |D| distribution over available and over all UAV-steps.

    def world_values(p, mask_key):
        if p is None:
            return None
        D = np.asarray(p["D"], dtype=np.float64)
        if mask_key is None:
            return D.ravel()
        return D[np.asarray(p[mask_key], dtype=bool)]

    readings["abs_D"] = {"available": _stats_with_worlds([world_values(p, "available")
                                                          for p in probes]),
                         "all": _stats_with_worlds([world_values(p, None) for p in probes])}
    # Relay UAV-steps (R1, R2) against the other available UAV-steps.
    D_all = pooled("D").reshape(-1, N_UAVS)
    available_all = pooled("available").reshape(-1, N_UAVS).astype(bool)
    for label, key in (("R1", "is_intermediate"), ("R2", "relay_slot")):
        flag_all = pooled(key).reshape(-1, N_UAVS).astype(bool)
        block = {"pooled": _relay_stats(D_all, available_all, flag_all)}
        per = [None if p is None else _relay_stats(np.asarray(p["D"]),
                                                   np.asarray(p["available"], dtype=bool),
                                                   np.asarray(p[key], dtype=bool))
               for p in probes]
        for field in ("mean_abs_relay", "mean_abs_other_available", "ratio", "relay_uav_steps",
                      "d_mass_share"):
            block[f"per_world_{field}"] = world_block(
                [None if stats is None else stats[field] for stats in per])
        readings[f"relay_{label}"] = block
    # Additive residual rho_t.

    def rho(p):
        qos = np.asarray(p["qos_live"], dtype=np.float64)
        positive = qos > 0.0
        return (np.asarray(p["D"], dtype=np.float64)[positive].sum(axis=1)
                - qos[positive]) / qos[positive]

    rho_world = [None if p is None else rho(p) for p in probes]
    rho_all = (np.concatenate([r for r in rho_world if r is not None])
               if any(r is not None for r in rho_world) else np.zeros(0))
    q25, q75 = _quantile(rho_all, 0.25), _quantile(rho_all, 0.75)
    readings["additive_residual_rho"] = {
        "n_probe_steps": int(rho_all.size), "median": _quantile(rho_all, 0.5),
        "q25": q25, "q75": q75, "iqr": None if q25 is None else q75 - q25,
        "mean": float(rho_all.mean()) if rho_all.size else None,
        "fraction_abs_above": float(np.mean(np.abs(rho_all) > RHO_LARGE)) if rho_all.size else None,
        "abs_threshold": RHO_LARGE,
        "per_world_median": world_block([None if r is None or not r.size else float(np.median(r))
                                         for r in rho_world]),
    }
    # Cost.
    probe_wall = _finite_mean(pooled("probe_wall_s"))
    collection_wall = _finite_mean(pooled("collection_wall_s"))
    readings["cost"] = {
        "mean_probe_wall_s": probe_wall, "mean_collection_wall_s_per_step": collection_wall,
        "slowdown_per_step_probe": (None if _ratio(probe_wall, collection_wall) is None
                                    else 1.0 + _ratio(probe_wall, collection_wall)),
        "slowdown_every_10": (None if _ratio(probe_wall, collection_wall) is None
                              else 1.0 + _ratio(probe_wall, 10.0 * collection_wall)),
        "declared_max_slowdown": DECLARED_MAX_SLOWDOWN,
        "per_world_mean_probe_wall_s": world_block(
            per_world(lambda p: _finite_mean(p["probe_wall_s"]))),
        "per_world_mean_collection_wall_s": world_block(
            [None if p is None else _finite_mean(p["collection_wall_s"]) for p in probes]),
    }
    readings["baseline_mismatch_steps"] = int(sum(
        int(np.sum(np.asarray(p["qos_copy_baseline"]) != np.asarray(p["qos_live"])))
        for p in live))
    readings["rule_inputs"] = {
        "relay_hop_share": {
            "observed_pooled_traffic_weighted":
                readings["relay_hop_traffic_share"]["pooled_traffic_weighted"],
            "observed_per_world_step_mean":
                readings["relay_hop_traffic_share"]["per_world_step_mean"]["mean"],
            "thresholds": list(RULE_THRESHOLDS["relay_hop_share"])},
        "relay_ratio_R1": {"observed_pooled": readings["relay_R1"]["pooled"]["ratio"],
                           "observed_per_world_mean": readings["relay_R1"]["per_world_ratio"]["mean"],
                           "threshold": RULE_THRESHOLDS["relay_ratio_R1"]},
        "sparsity_available": {
            "observed_pooled": readings["abs_D"]["available"]["pooled"]["sparsity"],
            "observed_per_world_mean":
                readings["abs_D"]["available"]["per_world_sparsity"]["mean"],
            "threshold": RULE_THRESHOLDS["sparsity_available"]},
    }
    return readings


# ----------------------------------------------------------------------------- bit identity

def trajectory_comparison(reference: dict[str, np.ndarray], other: dict[str, np.ndarray],
                          fields=COMPARED_FIELDS) -> dict[str, Any]:
    """Per field: exact identity, max |difference| and the first differing step."""
    result: dict[str, Any] = {}
    for field in fields:
        a = np.asarray(reference[field], dtype=np.float64)
        b = np.asarray(other[field], dtype=np.float64)
        entry: dict[str, Any] = {"shape_reference": list(a.shape), "shape_other": list(b.shape)}
        steps = min(len(a), len(b))
        same = (a[:steps] == b[:steps]) | (np.isnan(a[:steps]) & np.isnan(b[:steps]))
        differs = ~same.reshape(steps, -1).all(axis=1) if steps else np.zeros(0, dtype=bool)
        first = int(np.argmax(differs)) if differs.any() else None
        if first is None and a.shape != b.shape:
            first = steps
        delta = np.abs(a[:steps] - b[:steps])
        entry.update(identical=bool(a.shape == b.shape and same.all()),
                     max_abs_difference=_clean(np.nanmax(delta)) if delta.size else 0.0,
                     first_differing_step=first)
        result[field] = entry
    result["identical"] = all(result[field]["identical"] for field in fields)
    return result


def world_bit_identity(phase_results: list[dict[str, Any]], *, seed: int, params, horizon: int,
                       policy_seed: int, threads: int, heuristic, log_dir: str | None
                       ) -> dict[str, Any]:
    """Layer (b) on one world: plain vs phase (deep-copy probe) and plain vs raw probe."""
    common = dict(seed=int(seed), params=params, horizon=int(horizon),
                  policy_seed=int(policy_seed), threads=int(threads), heuristic=heuristic,
                  log_dir=log_dir)
    block: dict[str, Any] = {
        "world": int(seed), "scope": "one world (BIT_IDENTITY_WORLD); not a panel-wide check",
        "fields": list(COMPARED_FIELDS),
        "plain": "stake_sizing.evaluate_stake_task, mode hungarian, no observer",
        "raw_probe": ("RawProbeObserver: raw._static_qos_with_unavailable_uavs([i]) for "
                      "i = 0..7 on the live env at every step"),
    }
    started = time.perf_counter()
    plain = ss.evaluate_stake_task(StakeTask(mode=PROBE_MODE, **common))
    block["plain_wall_s"] = time.perf_counter() - started
    started = time.perf_counter()
    raw_row, raw_arrays, observer = _run_hungarian_world(CreditTask(**common), RawProbeObserver)
    block.update(raw_probe_run_wall_s=time.perf_counter() - started,
                 raw_probe_calls=observer.calls if observer is not None else 0,
                 raw_probe_wall_s=observer.wall_s if observer is not None else 0.0)
    phase = next((result for result in phase_results
                  if int(result["row"]["seed"]) == int(seed)), None)
    block["qos_per_step"] = {"plain": plain["row"].get("qos_per_step"),
                             "phase": None if phase is None else phase["row"].get("qos_per_step"),
                             "raw_probe": raw_row.get("qos_per_step")}
    if plain["row"].get("failed"):
        reason = f"plain run failed: {plain['row'].get('failure')}"
        return block | {"deepcopy_probe_trajectory_neutral": None,
                        "raw_probe_trajectory_neutral": None, "reason": reason}
    if phase is None or phase["row"].get("failed"):
        block.update(deepcopy_probe_trajectory_neutral=None,
                     deepcopy_probe_comparison={"reason": "world absent from or failed in the "
                                                          "phase panel"})
    else:
        comparison = trajectory_comparison(plain["arrays"], phase["arrays"])
        block.update(deepcopy_probe_trajectory_neutral=comparison["identical"],
                     deepcopy_probe_comparison=comparison)
    if raw_row.get("failed"):
        block.update(raw_probe_trajectory_neutral=None,
                     raw_probe_comparison={"reason": f"raw probe run failed: "
                                                     f"{raw_row.get('failure')}"})
    else:
        comparison = trajectory_comparison(plain["arrays"], raw_arrays)
        block.update(raw_probe_trajectory_neutral=comparison["identical"],
                     raw_probe_comparison=comparison)
    return block


# ----------------------------------------------------------------------------- runner phase

def run_credit_diagnostics(*, out: Path, launch_sha: str, workers: int, threads: int,
                           worlds=STAKE_WORLDS, argv=None) -> dict[str, Any]:
    worlds = tuple(int(seed) for seed in worlds)
    if not worlds or len(set(worlds)) != len(worlds):
        raise ValueError("worlds must be a non-empty tuple of distinct seeds")
    held = [seed for seed in worlds if seed >= HOLDOUT_WORLD_FLOOR]
    if held:
        raise ValueError(f"credit diagnostics may not evaluate hold-out worlds {held}")
    probe_every = int(PROBE_EVERY)
    spec = replace(ss.STAKE_SPEC, workers=int(workers), threads=int(threads))
    check_resources(spec)
    heuristic = _stake_heuristic()
    params = PRODUCTION_PARAMS
    root = Path(out) / CREDIT_PHASE
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"credit-diagnostics output already exists: {root}")
    for name in ("panels", "traces", "logs"):
        (root / name).mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    config = {
        "object_id": OBJECT_ID, "phase": CREDIT_PHASE, "launch_sha": launch_sha,
        "git_head": _git_head(), "argv": list(sys.argv if argv is None else argv),
        "controller": STAKE_CONTROLLER, "assignment_mode": PROBE_MODE,
        "assignment_rule": MODE_RULES[PROBE_MODE], "worlds": list(worlds),
        "horizon": spec.horizon, "policy_seed": spec.policy_seed, "workers": spec.workers,
        "threads": spec.threads, "os_cpu_count": os.cpu_count(), "device": "cpu",
        "action_mode": "deterministic", "planned_episodes": len(worlds),
        "bit_identity_episodes": 2, "heuristic": heuristic.record(), "params": asdict(params),
        "params_label": params.label, "plan_source": PLAN_SOURCE,
        "probe_every": probe_every, "sparsity_threshold": SPARSITY_THRESHOLD,
        "rho_abs_threshold": RHO_LARGE, "declared_max_slowdown": DECLARED_MAX_SLOWDOWN,
        "rule_thresholds": {key: (list(value) if isinstance(value, tuple) else value)
                            for key, value in RULE_THRESHOLDS.items()},
        "definitions": DEFINITIONS, "bit_identity_world": BIT_IDENTITY_WORLD,
        "compared_fields": list(COMPARED_FIELDS),
        "recorded_panel": RECORDED_PANEL, "consistency_tolerance": CONSISTENCY_TOLERANCE,
        "trace_timing": TRACE_TIMING,
        "horizon_policy_seed_source": "stake_sizing.STAKE_SPEC (B01Spec defaults)",
    }
    write_summary(root / "config.json", config)
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "phase": CREDIT_PHASE, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "assignment_mode": PROBE_MODE, "worlds": list(worlds),
        "planned_episodes": len(worlds), "workers": spec.workers, "threads": spec.threads,
        "probe_every": probe_every,
        "counts": {"episodes_completed": 0, "steps": 0, "failed_worlds": 0, "new_fits": 0,
                   "probe_steps": 0, "baseline_mismatch_steps": 0, "bit_identity_episodes": 0},
        "panels": {}, "artifacts": {"config.json": sha256_file(root / "config.json")},
    }
    write_summary(root / "summary.json", summary)
    _progress(root, {"event": "run_start", "phase": CREDIT_PHASE, "mode": PROBE_MODE,
                     "worlds": len(worlds), "workers": spec.workers, "threads": spec.threads,
                     "probe_every": probe_every})
    try:
        tasks = [CreditTask(seed=seed, params=params, horizon=spec.horizon,
                            policy_seed=spec.policy_seed, threads=spec.threads,
                            heuristic=heuristic, log_dir=str(root / "logs"),
                            probe_every=probe_every)
                 for seed in worlds]

        def advance(result):
            row = result["row"]
            counts = summary["counts"]
            counts["episodes_completed"] += 1
            counts["steps"] += int(row.get("actual_length", 0))
            counts["failed_worlds"] += int(bool(row.get("failed")))
            counts["probe_steps"] += int(row.get("probe_steps", 0))
            counts["baseline_mismatch_steps"] += int(row.get("baseline_mismatch_steps", 0))
            _progress(root, {"event": "world_end", "mode": PROBE_MODE, "seed": row["seed"],
                             "failed": bool(row.get("failed")),
                             "qos_per_step": row.get("qos_per_step"),
                             "probe_steps": row.get("probe_steps"),
                             "baseline_mismatch_steps": row.get("baseline_mismatch_steps"),
                             "wall": row.get("wall_seconds"),
                             "episodes_completed": counts["episodes_completed"]})

        phase_started = time.perf_counter()
        results = run_credit_tasks(tasks, spec.workers, on_result=advance)
        rows = [result["row"] for result in results]
        panel = {"controller": STAKE_CONTROLLER, "assignment_mode": PROBE_MODE,
                 "assignment_rule": MODE_RULES[PROBE_MODE], "params": asdict(params),
                 "heuristic": heuristic.record(), "worlds": list(worlds), "rows": rows,
                 "aggregate": aggregate(rows),
                 "failed_worlds": [row["seed"] for row in rows if row.get("failed")],
                 "probe_every": probe_every,
                 "wall_seconds": time.perf_counter() - phase_started}
        panel_path = root / "panels" / f"{PROBE_MODE}.json"
        write_summary(panel_path, panel)
        trace_path = root / "traces" / f"{PROBE_MODE}.npz"
        np.savez_compressed(trace_path, **trace_arrays(results))
        credit_path = root / "traces" / f"credit_{PROBE_MODE}.npz"
        np.savez_compressed(credit_path, **credit_trace_arrays(results, worlds, spec.horizon,
                                                               probe_every))
        for path in (panel_path, trace_path, credit_path):
            summary["artifacts"][str(path.relative_to(root))] = sha256_file(path)
        summary["panels"][PROBE_MODE] = {
            "mean_qos_per_step": panel["aggregate"].get("mean_qos_per_step"),
            "mean_raw_native_J": panel["aggregate"].get("mean_raw_native_J"),
            "failed_worlds": panel["failed_worlds"], "wall_seconds": panel["wall_seconds"]}
        by_seed = {int(result["row"]["seed"]): result for result in results}
        summary["readings"] = credit_readings(
            [None if by_seed.get(seed) is None else by_seed[seed].get("probe") for seed in worlds],
            worlds)
        write_summary(root / "summary.json", summary)
        _progress(root, {"event": "bit_identity_start", "world": BIT_IDENTITY_WORLD})
        bit_started = time.perf_counter()
        panel_check = consistency_check(rows, worlds, heuristic, REPO_ROOT / RECORDED_PANEL)
        world_check = world_bit_identity(results, seed=BIT_IDENTITY_WORLD, params=params,
                                         horizon=spec.horizon, policy_seed=spec.policy_seed,
                                         threads=spec.threads, heuristic=heuristic,
                                         log_dir=str(root / "logs"))
        summary["counts"]["bit_identity_episodes"] = 2
        bit_identity = {
            "record_only": True,
            "panel_consistency": panel_check,
            "hungarian_matches_recorded": panel_check["hungarian_matches_recorded"],
            "world": world_check,
            "deepcopy_probe_trajectory_neutral": world_check.get(
                "deepcopy_probe_trajectory_neutral"),
            "raw_probe_trajectory_neutral": world_check.get("raw_probe_trajectory_neutral"),
            "wall_seconds": time.perf_counter() - bit_started,
        }
        write_summary(root / "bit_identity.json", bit_identity)
        summary["artifacts"]["bit_identity.json"] = sha256_file(root / "bit_identity.json")
        summary["bit_identity"] = bit_identity
        _progress(root, {"event": "bit_identity_end",
                         "hungarian_matches_recorded": bit_identity["hungarian_matches_recorded"],
                         "deepcopy_probe_trajectory_neutral":
                             bit_identity["deepcopy_probe_trajectory_neutral"],
                         "raw_probe_trajectory_neutral":
                             bit_identity["raw_probe_trajectory_neutral"],
                         "wall_seconds": bit_identity["wall_seconds"]})
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        summary.update(wall_seconds=time.perf_counter() - started,
                       peak_rss_kib={"runner": int(own.ru_maxrss),
                                     "largest_worker": int(children.ru_maxrss)},
                       torch_threads_parent=torch.get_num_threads())
        write_summary(root / "summary.json", summary)
        _progress(root, {"event": "run_end", "status": summary["status"],
                         "failure": summary["failure"], "wall_seconds": summary["wall_seconds"]})

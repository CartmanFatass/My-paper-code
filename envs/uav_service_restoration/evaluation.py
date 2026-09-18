"""Independent evaluation: counterfactual references and a strict recovery definition.

Three service traces are computed over the **same** exogenous demand and the same network
configuration:

``healthy``
    the terrestrial network with no events and no UAVs;
``failed``
    the terrestrial network with this episode's events and no UAVs;
``controller``
    the same failed network with the evaluated controller flying.

The **affected set** is defined by the difference between ``healthy`` and ``failed``.  It
is computed without ever looking at the evaluated controller, so it cannot drift to
flatter a policy.

Recovery is declared only when the controller's delivered rate over the affected set
reaches ``rho`` times the healthy terrestrial reference at the same instant and holds for
``recovery_sustain_s`` of simulated time.  Intervals where the healthy reference delivers
nothing are marked not-applicable rather than divided through.  Automatic site repair
never counts as UAV recovery: when a repair precedes the threshold being met, the episode
is censored with that reason and the improvement over the no-UAV reference *with the same
repair* is reported alongside.

These counterfactuals exist for offline evaluation only.  They are not observations, not
state, and not reward shaping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from . import network as net
from . import scheduler as sched
from .config import EnvConfig
from .events import EventSchedule, schedule_from_events
from .metrics import EpisodeAccumulator
from .types import EpisodeDescriptor

_NOT_APPLICABLE = "not_applicable"


@dataclass
class ServiceTrace:
    """Piecewise-constant offered and delivered rates over an episode."""

    start_s: np.ndarray
    duration_s: np.ndarray
    offered_mbps: np.ndarray
    delivered_mbps: np.ndarray

    def integral_mbit(self, values: np.ndarray) -> np.ndarray:
        return np.sum(values * self.duration_s[:, None], axis=0)

    @property
    def offered_mbit(self) -> np.ndarray:
        return self.integral_mbit(self.offered_mbps)

    @property
    def delivered_mbit(self) -> np.ndarray:
        return self.integral_mbit(self.delivered_mbps)

    def rate_at(self, time_s: float, values: np.ndarray) -> np.ndarray:
        index = int(np.searchsorted(self.start_s, float(time_s), side="right")) - 1
        if index < 0:
            index = 0
        if index >= self.start_s.shape[0]:
            index = self.start_s.shape[0] - 1
        return values[index]


def trace_from_accumulator(accumulator: EpisodeAccumulator, offered: np.ndarray | None = None) -> ServiceTrace:
    """Build a trace from a rollout's accumulator series."""

    series = accumulator.delivered_series_mbps
    if not series:
        empty = np.zeros((0, accumulator.n_demand_points), dtype=np.float64)
        return ServiceTrace(
            start_s=np.zeros(0, dtype=np.float64),
            duration_s=np.zeros(0, dtype=np.float64),
            offered_mbps=empty,
            delivered_mbps=empty,
        )
    starts = np.asarray([item[0] for item in series], dtype=np.float64)
    durations = np.asarray([item[1] for item in series], dtype=np.float64)
    delivered = np.stack([item[2] for item in series])
    if offered is None:
        offered = np.zeros_like(delivered)
    return ServiceTrace(
        start_s=starts,
        duration_s=durations,
        offered_mbps=np.asarray(offered, dtype=np.float64),
        delivered_mbps=delivered,
    )


def simulate_no_uav_trace(
    config: EnvConfig,
    source: Any,
    episode: EpisodeDescriptor,
    schedule: EventSchedule,
    layout: Any,
    demand_positions_m: np.ndarray,
) -> ServiceTrace:
    """Evaluate the network model with **no UAVs** over the episode's time grid.

    No PettingZoo environment is constructed: with no UAV there is no motion, so the
    integration reduces to applying the active exogenous state on each subinterval and
    solving the same fixed scheduler.  The subinterval grid matches the environment's -
    event boundaries, source-demand boundaries, then ``physics_dt_s`` substeps - so the
    traces are directly comparable instant by instant.
    """

    interval_ms = int(round(float(source.metadata().interval_duration_s) * 1000.0))
    duration_s = float(config.episode.duration_s)
    decision_dt = float(config.episode.decision_dt_s)
    physics_dt = float(config.episode.physics_dt_s)
    no_uavs = np.zeros((0, 3), dtype=np.float64)

    starts: list[float] = []
    durations: list[float] = []
    offered_rows: list[np.ndarray] = []
    delivered_rows: list[np.ndarray] = []

    n_steps = int(round(duration_s / decision_dt))
    for step in range(n_steps):
        t0 = step * decision_dt
        t1 = t0 + decision_dt
        demand_edges = _demand_boundaries(episode.start_utc_ms, interval_ms, t0, t1)
        edges = sorted({t0, t1} | set(schedule.boundaries_within(t0, t1)) | set(demand_edges))
        for left, right in zip(edges[:-1], edges[1:]):
            span = float(right) - float(left)
            if span <= 0.0:
                continue
            n_sub = max(1, int(np.ceil(span / physics_dt - 1e-9)))
            h = span / n_sub
            for index in range(n_sub):
                sub_start = float(left) + index * h
                site_states = schedule.site_states(sub_start)
                timestamp = int(episode.start_utc_ms + int(round(sub_start * 1000.0)))
                frame = source.read_interval(episode, timestamp)
                demand = layout.aggregate_demand(frame.demand_mbps)
                overlay = config.source.event_overlay
                if overlay is not None and float(overlay.start_s) <= sub_start < float(
                    overlay.end_s
                ):
                    indices = np.asarray(overlay.cell_indices, dtype=np.int64)
                    valid = indices[(indices >= 0) & (indices < demand.shape[0])]
                    demand = demand.copy()
                    demand[valid] *= float(overlay.peak_gain)
                snapshot = net.build_snapshot(
                    config.network, site_states, no_uavs, demand_positions_m, demand
                )
                result = sched.solve_or_raise(snapshot, config.scheduler)
                starts.append(sub_start)
                durations.append(h)
                offered_rows.append(demand)
                delivered_rows.append(result.delivered_mbps_per_demand)

    return ServiceTrace(
        start_s=np.asarray(starts, dtype=np.float64),
        duration_s=np.asarray(durations, dtype=np.float64),
        offered_mbps=np.stack(offered_rows) if offered_rows else np.zeros((0, 0)),
        delivered_mbps=np.stack(delivered_rows) if delivered_rows else np.zeros((0, 0)),
    )


def _demand_boundaries(
    start_utc_ms: int, interval_ms: int, start_s: float, end_s: float
) -> list[float]:
    first_ms = int(np.ceil((start_utc_ms + start_s * 1000.0) / interval_ms)) * interval_ms
    found: list[float] = []
    cursor = first_ms
    while True:
        offset = (cursor - start_utc_ms) / 1000.0
        if offset >= end_s - 1e-12:
            break
        if offset > start_s + 1e-12:
            found.append(float(offset))
        cursor += interval_ms
    return found


def healthy_schedule(schedule: EventSchedule) -> EventSchedule:
    """The same network with no events: the healthy terrestrial reference."""

    return schedule_from_events((), schedule.n_sites)


def affected_demand_mask(
    healthy: ServiceTrace, failed: ServiceTrace, min_gap_mbit: float = 1e-6
) -> np.ndarray:
    """Demand points the failure actually harmed, defined without the evaluated policy."""

    gap = healthy.delivered_mbit - failed.delivered_mbit
    return gap > float(min_gap_mbit)


def recovery_report(
    config: EnvConfig,
    healthy: ServiceTrace,
    failed: ServiceTrace,
    controller: ServiceTrace,
    schedule: EventSchedule,
    affected: np.ndarray,
) -> dict[str, Any]:
    """Recovery time, censoring flag and censoring reason for the affected set."""

    rho = float(config.evaluation.recovery_fraction_rho)
    sustain = float(config.evaluation.recovery_sustain_s)
    failure_start = schedule.first_capability_loss_time_s()
    repair_times = [
        float(event.end_s) for event in schedule.events if event.end_s is not None
    ]
    first_repair = min(repair_times) if repair_times else None

    if failure_start is None:
        return {
            "applicable": False,
            "reason": "no capability loss in this episode",
            "recovery_time_s": None,
            "censored": False,
            "censoring_reason": None,
            "first_repair_s": None,
        }
    if not affected.any():
        return {
            "applicable": False,
            "reason": "the failure harmed no demand point in the healthy reference",
            "recovery_time_s": None,
            "censored": False,
            "censoring_reason": None,
            "first_repair_s": first_repair,
        }

    times = controller.start_s
    healthy_rate = np.asarray(
        [float(healthy.rate_at(t, healthy.delivered_mbps)[affected].sum()) for t in times]
    )
    controller_rate = np.asarray(
        [float(controller.delivered_mbps[index][affected].sum()) for index in range(times.shape[0])]
    )
    applicable = healthy_rate > 0.0
    meets = np.zeros(times.shape[0], dtype=bool)
    meets[applicable] = controller_rate[applicable] >= rho * healthy_rate[applicable] - 1e-12
    # Not-applicable instants neither confirm nor break a sustained window.
    meets[~applicable] = True

    recovery_time: float | None = None
    for index, time_s in enumerate(times):
        if time_s < failure_start - 1e-9:
            continue
        if not meets[index]:
            continue
        if not applicable[index]:
            # An instant with no healthy demand on the affected set carries no evidence
            # of restoration, so it may bridge a sustain window but may not open one.
            continue
        end = float(time_s) + sustain
        window = (times >= float(time_s) - 1e-9) & (times < end - 1e-9)
        if not window.any():
            # Not enough remaining simulated time to confirm the sustain requirement.
            break
        if bool(meets[window].all()):
            recovery_time = float(time_s)
            break

    censored = recovery_time is None
    reason: str | None = None
    if censored:
        if first_repair is not None:
            reason = "repaired_before_recovery_threshold_reached"
        elif times.size and float(times[-1]) + float(controller.duration_s[-1]) < failure_start:
            reason = "episode_ended_before_failure"
        else:
            reason = "threshold_not_reached_within_episode"
    elif first_repair is not None and recovery_time is not None and recovery_time >= first_repair:
        censored = True
        reason = "threshold_first_met_after_automatic_repair"
        recovery_time = None

    improvement = {
        "controller_delivered_mbit_affected": float(controller.delivered_mbit[affected].sum()),
        "failed_no_uav_delivered_mbit_affected": float(failed.delivered_mbit[affected].sum()),
        "healthy_delivered_mbit_affected": float(healthy.delivered_mbit[affected].sum()),
    }
    improvement["improvement_over_no_uav_mbit"] = (
        improvement["controller_delivered_mbit_affected"]
        - improvement["failed_no_uav_delivered_mbit_affected"]
    )
    gap = (
        improvement["healthy_delivered_mbit_affected"]
        - improvement["failed_no_uav_delivered_mbit_affected"]
    )
    improvement["fraction_of_lost_service_restored"] = (
        float(improvement["improvement_over_no_uav_mbit"] / gap) if gap > 0.0 else float("nan")
    )

    return {
        "applicable": True,
        "recovery_fraction_rho": rho,
        "recovery_sustain_s": sustain,
        "failure_start_s": float(failure_start),
        "first_repair_s": first_repair,
        "recovery_time_s": recovery_time,
        "time_to_recovery_s": (
            None if recovery_time is None else float(recovery_time - failure_start)
        ),
        "censored": bool(censored),
        "censoring_reason": reason,
        "n_affected_points": int(affected.sum()),
        "not_applicable_instants": int((~applicable).sum()),
        **improvement,
    }


def evaluate_rollout(
    config: EnvConfig,
    env: Any,
    accumulator: EpisodeAccumulator,
    offered_series: np.ndarray,
) -> dict[str, Any]:
    """Assemble the full evaluation record for one finished rollout.

    ``env`` supplies the demand source, the episode descriptor, the event schedule and the
    demand-point layout that the rollout actually used, so the references are computed
    against the identical exogenous world.
    """

    schedule = env.event_schedule
    diagnostics = env.get_privileged_diagnostics()
    episode = env.episode_descriptor
    layout = env.demand_layout
    demand_positions = net.demand_positions_from_xy(layout.positions_m, 0.0)

    failed = simulate_no_uav_trace(
        config, env.demand_source, episode, schedule, layout, demand_positions
    )
    healthy = simulate_no_uav_trace(
        config,
        env.demand_source,
        episode,
        healthy_schedule(schedule),
        layout,
        demand_positions,
    )
    controller = trace_from_accumulator(accumulator, offered_series)
    affected = affected_demand_mask(healthy, failed)

    offered_total = float(controller.offered_mbit.sum())
    return {
        "episode": {
            "episode_id": diagnostics["episode_id"],
            "split": diagnostics["split"],
            "dataset_hash": diagnostics["dataset_hash"],
            "is_real_activity_data": diagnostics["source_metadata"]["is_real_activity_data"],
            "provenance": (
                "real_activity_derived"
                if diagnostics["source_metadata"]["is_real_activity_data"]
                else "fixture_based"
            ),
        },
        "exogenous_events": diagnostics["exogenous_events"],
        "references": {
            "healthy_no_uav_delivered_mbit": float(healthy.delivered_mbit.sum()),
            "failed_no_uav_delivered_mbit": float(failed.delivered_mbit.sum()),
            "controller_delivered_mbit": float(controller.delivered_mbit.sum()),
            "offered_mbit": offered_total,
            "healthy_satisfaction": (
                float(healthy.delivered_mbit.sum() / offered_total)
                if offered_total > 0.0
                else float("nan")
            ),
            "failed_satisfaction": (
                float(failed.delivered_mbit.sum() / offered_total)
                if offered_total > 0.0
                else float("nan")
            ),
            "controller_satisfaction": (
                float(controller.delivered_mbit.sum() / offered_total)
                if offered_total > 0.0
                else float("nan")
            ),
        },
        "affected_points": [int(index) for index in np.flatnonzero(affected)],
        "recovery": recovery_report(config, healthy, failed, controller, schedule, affected),
        "episode_summary": accumulator.summary(),
        "calibration_summary": diagnostics["calibration_summary"],
    }


def rollout_controller(
    env: Any,
    controller: Any,
    *,
    seed: int | None = None,
    options: dict | None = None,
) -> dict[str, Any]:
    """Forward-only rollout of a diagnostic controller.  No optimizer, no gradients.

    Returns the evaluation record, including the counterfactual references and the
    recovery verdict.
    """

    config = env.config
    controller.reset()
    env.reset(seed=seed, options=options)
    rewards: list[float] = []
    while env.agents:
        view = env.get_current_state()
        actions = controller.act(view, list(env.agents))
        _, reward, _, _, _ = env.step(actions)
        rewards.append(float(next(iter(reward.values()))) if reward else 0.0)
    accumulator = env.accumulator
    offered_rows = [
        np.asarray(row, dtype=np.float64) for row in accumulator.offered_series_mbps
    ]
    record = evaluate_rollout(
        config,
        env,
        accumulator,
        np.stack(offered_rows) if offered_rows else np.zeros((0, 0)),
    )
    record["controller"] = {
        "name": getattr(controller, "name", type(controller).__name__),
        "information_condition": config.observations.mode,
        "reward_sum": float(np.sum(rewards)),
        "reward_mean": float(np.mean(rewards)) if rewards else float("nan"),
        "optimizer_updates": 0,
    }
    return record

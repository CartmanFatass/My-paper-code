"""Same-information joint rolling ordinary planner for ``uav_service_restoration_v0``.

Information
-----------
Reads **only** the ``view`` mapping from ``env.get_current_state()`` plus the static
``EnvConfig`` (network, radio models, scheduler, dynamics).  It never calls
``get_privileged_diagnostics()``, never reads the event schedule, the demand source or the
true current demand.  This is the same information condition as
``envs.uav_service_restoration.baselines.BackhaulAwareGreedyController``.

Planning model (one decision step)
----------------------------------
* Demand estimate for the LP: the telemetry-reported offered rate on slots whose report is
  valid (``telemetry_demand_observed``), 0 elsewhere.  The environment's own solve feeds the
  full offered vector to an LP containing live terrestrial sites *and* UAVs; the planner
  mirrors that, so a capacity-limited live site is not credited twice.  Lost-coverage slots
  (the greedy's ``_unmet_estimate`` inference) are covered automatically: their last-known
  offered demand is in the vector and the reported site capability removes the dead site.
  The greedy's ``_unmet_estimate`` (imported, unmodified) is used only for candidate
  ranking and for the "nothing to do" short circuit.
* Site states: rebuilt from ``telemetry_site_capability`` with the greedy's ``> 0.5``
  thresholds for the two booleans and the reported scales; a site whose report is not valid
  is treated as fully down (as the greedy's live-gateway rule does).
* UAV positions: each UAV at its candidate hover target, at the greedy's common clipped
  altitude.
* Value: ``delivered_mbps_total`` of ``scheduler.solve_or_raise`` (``scheduler.solve`` plus
  the same status/residual checks the environment applies) on
  ``network.build_snapshot`` - the construction the environment uses.  A candidate whose
  snapshot or solve fails (size limit, solver failure, residual) scores ``-inf``; the
  rollout never crashes on a candidate.

Search
------
Candidates per UAV: "stay" (current xy) plus the top-K demand slots by the greedy's
``min(unmet, backhaul)`` score.  Start from the greedy's own assignment (duplicated here
exactly, including wrap-around), then coordinate ascent: for each UAV in order try every
candidate holding the others fixed and keep the best joint LP value; sweep until no change
or ``max_sweeps``.  Ties within ``value_rel_tol`` go to smaller total xy travel distance, and
a tie move is never accepted below the start's value, so the returned value is never below
the greedy start.  Joint assignments are cached within a step, so ``n_lp_solves`` counts
actual solves.

Idle fallback (DM revision): after the ascent, each UAV on "stay" whose removal leaves
the joint LP value unchanged (within ``value_rel_tol``) is assigned the greedy's slot for
that UAV, unless another UAV already targets that slot or the joint value would drop
(beyond ``value_rel_tol``, and never below the greedy start's value).  One extra solve per
such check; the step record carries the count and the value before/after.

Executor: unit velocity toward the target xy, z request 0 (the greedy's executor); "stay"
requests zero velocity.  With no live gateway or no estimated unmet demand the planner
returns zero actions, as the greedy does.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from envs.uav_service_restoration import network as net
from envs.uav_service_restoration import scheduler as sched
from envs.uav_service_restoration.baselines import BackhaulAwareGreedyController
from envs.uav_service_restoration.config import EnvConfig
from envs.uav_service_restoration.dynamics import ACTION_DIM
from envs.uav_service_restoration.radio import capacity_mbps
from envs.uav_service_restoration.types import (
    SchedulerSizeLimitError,
    SchedulerSolveError,
    SiteState,
)

#: Candidate code for "hold the current horizontal position".
STAY = -1


def _zero_actions(agents: list[str]) -> dict[str, np.ndarray]:
    return {agent: np.zeros(ACTION_DIM, dtype=np.float32) for agent in agents}


def _unit_towards(source_xy: np.ndarray, target_xy: np.ndarray) -> np.ndarray:
    # Identical to baselines._unit_towards.
    delta = np.asarray(target_xy, dtype=np.float64) - np.asarray(source_xy, dtype=np.float64)
    norm = float(np.linalg.norm(delta))
    if norm < 1e-9:
        return np.zeros(2, dtype=np.float64)
    return delta / norm


def site_states_from_view(view: dict[str, Any]) -> tuple[SiteState, ...]:
    """Telemetry-reported site capability as ``SiteState`` objects (stale -> down)."""

    capability = np.asarray(view["telemetry_site_capability"], dtype=np.float64).reshape(-1, 4)
    observed = np.asarray(view["telemetry_site_observed"], dtype=bool)
    states: list[SiteState] = []
    for index in range(capability.shape[0]):
        if not observed[index]:
            states.append(SiteState(False, False, 0.0, 0.0))
            continue
        vector = capability[index]
        states.append(
            SiteState(
                radio_up=bool(vector[0] > 0.5),
                core_link_up=bool(vector[1] > 0.5),
                access_capacity_scale=float(vector[2]),
                backhaul_capacity_scale=float(vector[3]),
            )
        )
    return tuple(states)


def lp_demand_from_view(view: dict[str, Any]) -> np.ndarray:
    """Estimated offered rate per slot for the planner's LP (unobserved slots = 0)."""

    offered = np.asarray(view["telemetry_demand_offered_mbps"], dtype=np.float64)
    observed = np.asarray(view["telemetry_demand_observed"], dtype=bool)
    return np.where(observed, np.maximum(offered, 0.0), 0.0)


class JointRollingLPController:
    """Joint placement by coordinate ascent on the fixed scheduler's LP value."""

    name = "joint_rolling_lp"

    def __init__(
        self,
        config: EnvConfig,
        *,
        top_k: int = 8,
        max_sweeps: int = 2,
        min_unmet_mbps: float = 1e-6,
        value_rel_tol: float = 1e-6,
    ) -> None:
        if int(top_k) < 1:
            raise ValueError("top_k must be >= 1")
        if int(max_sweeps) < 0:
            raise ValueError("max_sweeps must be >= 0")
        if not float(value_rel_tol) >= 0.0:
            raise ValueError("value_rel_tol must be non-negative")
        self._config = config
        self._top_k = int(top_k)
        self._max_sweeps = int(max_sweeps)
        self._min_unmet = float(min_unmet_mbps)
        self._rel_tol = float(value_rel_tol)
        # Reused (not modified) for the exact greedy semantics of the unmet estimate and
        # the live-gateway rule.
        self._greedy = BackhaulAwareGreedyController(config, min_unmet_mbps=min_unmet_mbps)
        self._backhaul_model = config.network.radio_models["site_uav_backhaul"]
        self.step_diagnostics: list[dict[str, Any]] = []

    # ------------------------------------------------------------------------------
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "top_k": self._top_k,
            "max_sweeps": self._max_sweeps,
            "min_unmet_mbps": self._min_unmet,
            "value_rel_tol": self._rel_tol,
        }

    def reset(self) -> None:
        self.step_diagnostics = []

    # ------------------------------------------------------------------------------
    def greedy_plan(self, view: dict[str, Any], n_uavs: int) -> dict[str, Any]:
        """The backhaul-aware greedy's scoring and assignment, duplicated exactly.

        Returns ``{"status": ..., "targets": [...], "order": [...], "altitude": ...}``;
        ``targets`` is empty unless ``status == "planned"``.
        """

        positions = np.asarray(view["uav_positions"], dtype=np.float64).reshape(-1, 3)
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        unmet = self._greedy._unmet_estimate(view)
        gateways = self._greedy._live_gateway_positions(view)
        if gateways.shape[0] == 0:
            return {"status": "no_live_gateway", "targets": [], "order": [], "altitude": None}
        if not (unmet > self._min_unmet).any():
            return {"status": "no_estimated_unmet", "targets": [], "order": [], "altitude": None}
        altitude = float(np.clip(
            positions[:, 2].mean(),
            self._config.dynamics.altitude_range_m[0],
            self._config.dynamics.altitude_range_m[1],
        ))
        candidate = np.zeros((demand_xy.shape[0], 3), dtype=np.float64)
        candidate[:, :2] = demand_xy
        candidate[:, 2] = altitude
        gateway_distance = np.sqrt(
            np.sum((candidate[:, None, :] - gateways[None, :, :]) ** 2, axis=-1)
        )
        backhaul = capacity_mbps(gateway_distance, self._backhaul_model).max(axis=1)
        score = np.minimum(unmet, backhaul)
        score = np.where(unmet > self._min_unmet, score, 0.0)
        order = [int(index) for index in np.argsort(-score, kind="stable") if score[index] > 0.0]
        if not order:
            return {"status": "no_positive_score", "targets": [], "order": [], "altitude": altitude}
        targets: list[int] = []
        assigned: set[int] = set()
        for index in range(int(n_uavs)):
            target = None
            for slot in order:
                if slot not in assigned:
                    target = slot
                    break
            if target is None:
                target = order[index % len(order)]
            else:
                assigned.add(target)
            targets.append(int(target))
        return {"status": "planned", "targets": targets, "order": order, "altitude": altitude}

    # ------------------------------------------------------------------------------
    def _positions_for(
        self,
        assignment: tuple[int, ...],
        current_xy: np.ndarray,
        demand_xy: np.ndarray,
        altitude: float,
    ) -> np.ndarray:
        positions = np.zeros((len(assignment), 3), dtype=np.float64)
        for index, target in enumerate(assignment):
            positions[index, :2] = current_xy[index] if target == STAY else demand_xy[target]
            positions[index, 2] = altitude
        return positions

    @staticmethod
    def _travel(
        assignment: tuple[int, ...], current_xy: np.ndarray, demand_xy: np.ndarray
    ) -> float:
        total = 0.0
        for index, target in enumerate(assignment):
            if target == STAY:
                continue
            total += float(np.linalg.norm(demand_xy[target] - current_xy[index]))
        return total

    def evaluate_assignment(
        self, view: dict[str, Any], assignment: tuple[int, ...], altitude: float
    ) -> tuple[float, str]:
        """LP value (Mbps) of one joint assignment; ``-inf`` with a reason on failure."""

        current_xy = np.asarray(view["uav_positions"], dtype=np.float64).reshape(-1, 3)[:, :2]
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        positions = self._positions_for(assignment, current_xy, demand_xy, altitude)
        return self._solve(
            site_states_from_view(view),
            positions,
            net.demand_positions_from_xy(demand_xy, 0.0),
            lp_demand_from_view(view),
        )

    def _solve(
        self,
        site_states: tuple[SiteState, ...],
        positions: np.ndarray,
        demand_positions: np.ndarray,
        demand: np.ndarray,
    ) -> tuple[float, str]:
        try:
            snapshot = net.build_snapshot(
                self._config.network, site_states, positions, demand_positions, demand
            )
            result = sched.solve_or_raise(snapshot, self._config.scheduler)
        except SchedulerSizeLimitError as error:
            return float("-inf"), f"size_limit: {error}"
        except SchedulerSolveError as error:
            return float("-inf"), f"solve_error: {error}"
        return float(result.delivered_mbps_total), "ok"

    # ------------------------------------------------------------------------------
    def plan(self, view: dict[str, Any], n_uavs: int) -> dict[str, Any]:
        """Run the bounded joint search; returns the step's diagnostic record."""

        started = time.perf_counter()
        record: dict[str, Any] = {
            "decision_step": int(view.get("current_step", -1)),
            "time_s": float(view.get("physical_time_s", float("nan"))),
        }
        greedy = self.greedy_plan(view, n_uavs)
        record["status"] = greedy["status"]
        if greedy["status"] != "planned":
            record.update(
                n_lp_solves=0,
                n_lp_failures=0,
                candidate_slots=[],
                start_targets=[],
                chosen_targets=[],
                start_value_mbps=None,
                best_value_mbps=None,
                ascent_targets=[],
                n_zero_marginal_stay=0,
                n_fallback=0,
                fallback_uavs=[],
                value_before_fallback_mbps=None,
                value_after_fallback_mbps=None,
                sweeps=0,
                travel_distance_m=0.0,
                wall_s=time.perf_counter() - started,
            )
            return record

        altitude = float(greedy["altitude"])
        current_xy = np.asarray(view["uav_positions"], dtype=np.float64).reshape(-1, 3)[:, :2]
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        site_states = site_states_from_view(view)
        demand_positions = net.demand_positions_from_xy(demand_xy, 0.0)
        demand = lp_demand_from_view(view)
        candidates = [STAY] + list(greedy["order"][: self._top_k])

        cache: dict[tuple[int, ...], float] = {}
        failures: list[str] = []

        def value_of(assignment: tuple[int, ...]) -> float:
            if assignment not in cache:
                positions = self._positions_for(assignment, current_xy, demand_xy, altitude)
                value, reason = self._solve(site_states, positions, demand_positions, demand)
                if reason != "ok":
                    failures.append(reason)
                cache[assignment] = value
            return cache[assignment]

        start = tuple(int(target) for target in greedy["targets"])
        start_value = value_of(start)
        best = start
        best_value = start_value
        best_distance = self._travel(start, current_xy, demand_xy)
        sweeps = 0
        for _ in range(self._max_sweeps):
            sweeps += 1
            changed = False
            for uav in range(len(best)):
                for option in candidates:
                    if option == best[uav]:
                        continue
                    trial = best[:uav] + (option,) + best[uav + 1:]
                    value = value_of(trial)
                    distance = self._travel(trial, current_xy, demand_xy)
                    if self._accept(value, distance, best_value, best_distance, start_value):
                        best, best_value, best_distance = trial, value, distance
                        changed = True
            if not changed:
                break

        # Idle fallback (DM revision): a UAV left on "stay" whose removal leaves the joint
        # LP value unchanged pre-positions at the greedy's slot for that UAV, provided no
        # other UAV already targets that slot and the joint value does not drop.
        ascent_targets = list(best)
        value_before_fallback = best_value
        fallback_uavs: list[int] = []
        zero_marginal_stay: list[int] = []
        removal_cache: dict[tuple[int, tuple[int, ...]], float] = {}

        def value_without(assignment: tuple[int, ...], uav: int) -> float:
            key = (uav, assignment)
            if key not in removal_cache:
                positions = self._positions_for(assignment, current_xy, demand_xy, altitude)
                positions = np.delete(positions, uav, axis=0)
                value, reason = self._solve(site_states, positions, demand_positions, demand)
                if reason != "ok":
                    failures.append(reason)
                removal_cache[key] = value
            return removal_cache[key]

        for uav in range(len(best)):
            if best[uav] != STAY or not np.isfinite(best_value):
                continue
            tol = self._rel_tol * max(1.0, abs(best_value))
            without = value_without(best, uav)
            if not (np.isfinite(without) and without >= best_value - tol):
                continue
            zero_marginal_stay.append(uav)
            slot = int(greedy["targets"][uav])
            if any(best[other] == slot for other in range(len(best)) if other != uav):
                continue
            trial = best[:uav] + (slot,) + best[uav + 1:]
            value = value_of(trial)
            # "Lowers" uses the ascent's tie tolerance; never below the greedy start.
            if np.isfinite(value) and value >= best_value - tol and value >= start_value:
                best, best_value = trial, value
                best_distance = self._travel(best, current_xy, demand_xy)
                fallback_uavs.append(uav)

        record.update(
            n_lp_solves=len(cache) + len(removal_cache),
            n_lp_failures=len(failures),
            lp_failure_reasons=sorted(set(failures))[:5],
            candidate_slots=[int(slot) for slot in candidates if slot != STAY],
            start_targets=list(start),
            chosen_targets=list(best),
            chosen_target_xy=self._positions_for(best, current_xy, demand_xy, altitude)[
                :, :2
            ].tolist(),
            altitude_m=altitude,
            start_value_mbps=start_value,
            best_value_mbps=best_value,
            ascent_targets=ascent_targets,
            n_zero_marginal_stay=len(zero_marginal_stay),
            n_fallback=len(fallback_uavs),
            fallback_uavs=fallback_uavs,
            value_before_fallback_mbps=value_before_fallback,
            value_after_fallback_mbps=best_value,
            lp_demand_total_mbps=float(demand.sum()),
            sweeps=sweeps,
            travel_distance_m=float(best_distance),
            wall_s=time.perf_counter() - started,
        )
        return record

    def _accept(
        self,
        value: float,
        distance: float,
        best_value: float,
        best_distance: float,
        start_value: float,
    ) -> bool:
        if not np.isfinite(value):
            return False
        if not np.isfinite(best_value):
            return True
        tol = self._rel_tol * max(1.0, abs(best_value))
        if value > best_value + tol:
            return True
        # Tie within tolerance: prefer less travel, but never drop below the start value,
        # so the search cannot return worse than the greedy assignment it began from.
        return (
            value >= best_value - tol
            and value >= start_value
            and distance < best_distance - 1e-9
        )

    # ------------------------------------------------------------------------------
    def act(self, view: dict[str, Any], agents: list[str]) -> dict[str, np.ndarray]:
        record = self.plan(view, len(agents))
        self.step_diagnostics.append(record)
        if record["status"] != "planned":
            return _zero_actions(agents)
        positions = np.asarray(view["uav_positions"], dtype=np.float64).reshape(-1, 3)
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        actions: dict[str, np.ndarray] = {}
        for index, agent in enumerate(agents):
            target = record["chosen_targets"][index]
            if target == STAY:
                actions[agent] = np.zeros(ACTION_DIM, dtype=np.float32)
                continue
            direction = _unit_towards(positions[index, :2], demand_xy[target])
            actions[agent] = np.asarray([direction[0], direction[1], 0.0], dtype=np.float32)
        return actions

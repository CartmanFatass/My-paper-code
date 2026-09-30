"""Cell b04, arm B0 (coupled_host_joint_skills_stage1): the frozen planner deploying on lawful
sightings from spawn.  Zero fits, no learner, no search policy.

Authority: ``docs/research/candidates/coupled_host_joint_skills_stage1/NOTES.md``, entry "2A census
READ ... pre-declaration of cell b04 (B0)".  Reused, not rewritten:
``coupled_host_replan_timing.event_host`` (host), ``rules.d2_planner`` (D2's two-search cold
procedure on a shadow, live state asserted unchanged), ``rules.rollout`` (the straight-line
executor), ``planner.assign_targets``.

Host.  ``make_static_host`` = ``make_event_host(world, event_override={"t_e": NO_EVENT_T_E})``:
the event is drawn at reset (its own RNG stream) but ``t_e`` lies beyond every horizon, so the
host is D2's static coupled host; the harness asserts after every rollout that no event applied
and that ``user_positions`` is byte-identical to the reset copy.

Information contract (arm B0, ``B0Arm``):

* Sightings: at the decision for call ``t`` (state after call ``t - 1``; ``t = 0``: the reset
  state) every UAV ``i`` sees the users ``env._get_local_users(i)`` returns (the host's
  SINR >= min_sinr rule, uncapped).  All six views are pooled INSTANTLY into one team map
  (privileged pooling, upper-bounds every forwarding rule).  ``team_sightings`` is the only
  reader of ``env.user_positions`` in the arm and reads it row by row, visible rows only.
* Map: user -> latest observed (step, x, y); users never seen are absent.
* Trigger: plan when >= ``TRIGGER_NEW_KNOWN`` users are in the map but not in the last planned
  map (the planned map starts empty, so the first plan is the same rule with >= 3 known).
  Every planner call counts toward ``MAX_REPLANS``; a trigger at the cap is recorded
  (``cap_hit``), not executed.
* Plan: ``rules.d2_planner`` (flat + relay searches, ``budget`` each, ``default_rng(world)``) on
  a base host holding ONLY the known users (``known_users_host``, ``SHADOW_USER_SET``); the
  targets are matched by ``assign_targets`` from the UAVs' current positions and govern call
  ``t`` onward.  Before the first plan the UAVs hold at spawn.

Reference F (harness, full information): the frozen planner on all 50 users from the reset
state, same procedure and executor (``regression_rollout``); it must equal the sealed gate
record (``b01_gate_dev_a01/worlds/<w>.json``: relay layout, whole C_bh series, all-500 mean).
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import static_evaluate
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    FINAL_WINDOW,
    K_CANDIDATES,
    assign_targets,
    cluster_layout,
)
from experiments.candidates.coupled_host_replan_timing.event_host import (
    EventCoupledRelayHost,
    make_event_host,
)
from experiments.candidates.coupled_host_replan_timing.rules import (
    PLANNER_BUDGET,
    d2_planner,
    rollout,
)

DIRECTION = "coupled_host_joint_skills_stage1"
NO_EVENT_T_E = 10 ** 9            # event step beyond every horizon: the event never applies
TRIGGER_NEW_KNOWN = 3             # users newly known since the last planned map (NOTES b04)
MAX_REPLANS = 20                  # pricing bound on planner calls (first plan included); the
                                  # declared cap 5 bound in probe world 1024 (NOTES b04 launch entry)
MIN_KNOWN_FOR_SEARCH = max(K_CANDIDATES)   # planner k-means needs >= 6 users; fewer -> error
READING_STEPS = (0, 100, 250, 500)
VIEW_CAP_REPORTED = 20            # host obs vector cap; sightings are uncapped, only counted
SHADOW_USER_SET = ("known users only: deep copy of the live host with n_users = n_known and "
                   "user_positions = the known users' latest sighted xy (index order), channel "
                   "state recomputed by static_evaluate; unknown users are absent from k-means, "
                   "association and reward; the host's own contract reward normalises C_bh by "
                   "n_known (not by 50)")
POOLING = ("instant: at each decision the union of all six UAVs' env._get_local_users views "
           "enters the team map (latest xy per user)")
CLOCK = ("decision for call t reads the state after call t - 1 (t = 0: reset state); a plan "
         "made there governs call t; users_known at k in {0, 100, 250} = after pooling the "
         "state at the start of call k; at the horizon (500) = after pooling the terminal state "
         "(one extra pooling, no plan)")
HOLD_RULE = "before the first plan every UAV's target is its spawn position (zero action)"


# ============================================================ host


def make_static_host(world_seed: int, area_size: int = 5000) -> EventCoupledRelayHost:
    """D2's coupled host with no event: the single-event host with ``t_e`` beyond any horizon."""
    return make_event_host(world_seed, area_size=area_size,
                           event_override={"t_e": NO_EVENT_T_E})


def assert_static(env: EventCoupledRelayHost, users0: np.ndarray, what: str) -> None:
    if env.event_applied:
        raise AssertionError(f"{what}: an event applied on the static host")
    if np.asarray(env.user_positions).tobytes() != np.asarray(users0).tobytes():
        raise AssertionError(f"{what}: user positions changed during the run")


# ============================================================ information rights (audit screen)


def team_sightings(env: EventCoupledRelayHost) -> tuple[dict[int, tuple[float, float]], list[int]]:
    """Pooled sightings {user: (x, y)} of all UAVs and the per-UAV view sizes.

    The ONLY read of ``env.user_positions`` in the arm: one row per user some UAV's
    ``_get_local_users`` returns (never a whole-array read).
    """
    positions = env.user_positions
    out: dict[int, tuple[float, float]] = {}
    views: list[int] = []
    for uav in range(env.n_uavs):
        visible = [int(u) for u, _sinr in env._get_local_users(uav)]
        views.append(len(visible))
        for user in visible:
            if user not in out:
                row = positions[user]
                out[user] = (float(row[0]), float(row[1]))
    return out, views


class TeamMap:
    """User -> latest observed (step, x, y); users never sighted are absent."""

    def __init__(self) -> None:
        self.latest: dict[int, tuple[int, float, float]] = {}

    def update(self, sightings: dict[int, tuple[float, float]], step: int) -> list[int]:
        """Place every sighted user at this step's xy; returns the users new to the map."""
        new = []
        for user, (x, y) in sightings.items():
            if user not in self.latest:
                new.append(int(user))
            if user not in self.latest or int(step) >= self.latest[user][0]:
                self.latest[int(user)] = (int(step), float(x), float(y))
        return sorted(new)

    def known(self) -> list[int]:
        return sorted(self.latest)

    def users_xy(self) -> tuple[list[int], np.ndarray]:
        users = self.known()
        xy = np.array([[self.latest[u][1], self.latest[u][2]] for u in users], dtype=float)
        return users, xy.reshape(len(users), 2)


def known_users_host(env: EventCoupledRelayHost, users_xy: np.ndarray) -> EventCoupledRelayHost:
    """Planning base holding ONLY the known users (``SHADOW_USER_SET``); ``env`` is untouched."""
    users_xy = np.array(users_xy, dtype=float, copy=True).reshape(-1, 2)
    base = copy.deepcopy(env)
    base.n_users = int(users_xy.shape[0])
    base.user_positions = users_xy
    base.event = None                       # the base never steps; no event record is carried
    base._post_event_users = None
    static_evaluate(base, np.array(env.uav_positions, dtype=float), allow_a2a=bool(env.a2a_enabled))
    if base.connections.shape != (base.n_uavs, base.n_users):
        raise AssertionError("known-user base: connection matrix not rebuilt for the known users")
    return base


def plan_on_known(env: EventCoupledRelayHost, users_xy: np.ndarray, world: int, budget: int):
    """D2's cold procedure on the known users; returns (relay, flat)."""
    if users_xy.shape[0] < MIN_KNOWN_FOR_SEARCH:
        raise ValueError(f"{users_xy.shape[0]} known users < {MIN_KNOWN_FOR_SEARCH}: the frozen "
                         "planner's k-means (k up to 6) cannot run")
    base = known_users_host(env, users_xy)
    return d2_planner(base, np.array(base.user_positions, copy=True), int(world), int(budget))


class B0Arm:
    """Per-step decision rule of arm B0; ``targets`` is ``rollout``'s ``targets_fn``."""

    def __init__(self, env: EventCoupledRelayHost, world: int, budget: int,
                 max_replans: int = MAX_REPLANS) -> None:
        if int(env.current_step) != 0:
            raise AssertionError("B0 starts at the reset state")
        if int(max_replans) < 1:
            raise ValueError("max_replans must be >= 1")
        self.env, self.world, self.budget = env, int(world), int(budget)
        self.max_replans = int(max_replans)
        self.spawn = np.array(env.uav_positions, dtype=float, copy=True)
        self.current = self.spawn.copy()
        self.map = TeamMap()
        self.planned: set[int] = set()
        self.plans: list[dict[str, Any]] = []
        self.cap_hit_steps: list[int] = []
        self.evaluations = 0
        self.known_at: dict[str, list[int]] = {}
        self.first_known_step: dict[int, int] = {}
        self.views_over_cap = 0
        self.hold_steps = 0

    def _observe(self, step: int) -> None:
        sightings, views = team_sightings(self.env)
        self.views_over_cap += sum(v > VIEW_CAP_REPORTED for v in views)
        for user in self.map.update(sightings, step):
            self.first_known_step[user] = int(step)

    def targets(self, t: int) -> np.ndarray:
        t = int(t)
        self._observe(t)
        if t in READING_STEPS:
            self.known_at[str(t)] = self.map.known()
        new = sorted(set(self.map.latest) - self.planned)
        if len(new) >= TRIGGER_NEW_KNOWN:
            if len(self.plans) < self.max_replans:
                self._plan(t, new)
            else:
                self.cap_hit_steps.append(t)
        if not self.plans:
            self.hold_steps += 1
        return self.current

    def _plan(self, t: int, new: list[int]) -> None:
        users, xy = self.map.users_xy()
        relay, flat = plan_on_known(self.env, xy, self.world, self.budget)
        layout = np.asarray(relay.positions_xyz, dtype=float)
        self.current = layout[assign_targets(np.asarray(self.env.uav_positions, dtype=float), layout)]
        used = int(flat.evaluations) + int(relay.evaluations)
        self.evaluations += used
        self.planned = set(users)
        self.plans.append({"decision_step": t, "first_call_with_new_targets": t,
                           "n_known": len(users), "newly_known": len(new), "evaluations": used,
                           "static_contract_reward_on_known": float(relay.contract_reward),
                           "targets_xyz": self.current.tolist()})

    def finish(self, t_end: int) -> None:
        """Pool the terminal state for the horizon reading (no plan)."""
        self._observe(int(t_end))
        self.known_at[str(int(t_end))] = self.map.known()

    def record(self) -> dict[str, Any]:
        return {
            "max_replans": int(self.max_replans),
            "replans": len(self.plans),
            "trigger_steps": [p["decision_step"] for p in self.plans],
            "plans": self.plans,
            "evaluations_used": int(self.evaluations),
            "cap_hit": bool(self.cap_hit_steps),
            "cap_hit_trigger_steps": len(self.cap_hit_steps),
            "first_cap_hit_step": self.cap_hit_steps[0] if self.cap_hit_steps else None,
            "hold_steps_before_first_plan": int(self.hold_steps),
            "known_users_at": self.known_at,
            "first_known_step": {str(u): s for u, s in sorted(self.first_known_step.items())},
            "views_over_obs_cap": int(self.views_over_cap),
        }


# ============================================================ harness (truth used for set-up/reporting)


def run_b0(env: EventCoupledRelayHost, world: int, budget: int,
           horizon: int, max_replans: int = MAX_REPLANS) -> tuple[dict[str, Any], dict[str, Any]]:
    """Arm B0 on a freshly reset static host (not reset here); returns (rollout, arm record)."""
    arm = B0Arm(env, world, budget, max_replans=max_replans)
    result = rollout(env, arm.targets, 0, int(horizon))
    arm.finish(result["t_end"])
    return result, arm.record()


def regression_rollout(env: EventCoupledRelayHost, world: int, budget: int,
                       horizon: int) -> dict[str, Any]:
    """F: the frozen planner on all users from the reset state, the same executor."""
    initial = np.array(env.uav_positions, dtype=float, copy=True)
    users = np.array(env.user_positions, dtype=float, copy=True)
    relay, flat = d2_planner(env, users, int(world), int(budget))
    sites = np.asarray(relay.positions_xyz, dtype=float)
    perm = assign_targets(initial, sites)
    keep = sites[perm]
    result = rollout(env, lambda t: keep, 0, int(horizon), final_targets=keep)
    return {"sites_xyz": sites, "permutation": perm.tolist(), "targets_xyz": keep,
            "evaluations": int(flat.evaluations) + int(relay.evaluations), **result}


def series_means(series: list[float]) -> dict[str, float | None]:
    """All-horizon and final-100 means, computed as ``planner._summarise`` does."""
    array = np.asarray(series, dtype=float)
    tail = array[-FINAL_WINDOW:]
    return {"all_mean": float(array.mean()) if array.size else None,
            "final_100_mean": float(tail.mean()) if tail.size else None}


def gate_reference(gate: dict[str, Any]) -> dict[str, Any]:
    relay = gate["closed_loop"]["closed_loop_relay"]
    return {"all_mean": float(relay["coverage_backhauled_mean_all"]),
            "final_100_mean": float(relay["coverage_backhauled_mean_final100"]),
            "series": list(relay["series"]["coverage_backhauled"]),
            "sites_xyz": gate["static"]["P_relay"]["positions_xyz"],
            "initial_positions_xyz": gate["initial_positions_xyz"],
            "user_positions_xy": gate["user_positions_xy"]}


def check_regression(world: int, reg: dict[str, Any], reg_means: dict[str, Any],
                     initial: np.ndarray, users: np.ndarray, gate: dict[str, Any]) -> None:
    """Exact equality of the regression rollout with the sealed gate record (raises)."""
    ref = gate_reference(gate)
    checks = {
        "initial_positions": np.array_equal(initial, np.asarray(ref["initial_positions_xyz"])),
        "user_positions": np.array_equal(users, np.asarray(ref["user_positions_xy"])),
        "relay_sites": np.array_equal(reg["sites_xyz"], np.asarray(ref["sites_xyz"])),
        "series": reg["coverage_backhauled"] == ref["series"],
        "all_mean": reg_means["all_mean"] == ref["all_mean"],
        "final_100_mean": reg_means["final_100_mean"] == ref["final_100_mean"],
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise AssertionError(f"world {world}: regression differs from the gate record: {failed} "
                             f"(regression all_mean {reg_means['all_mean']!r}, gate {ref['all_mean']!r})")


def clusters_of(users: list[int], membership: np.ndarray) -> list[int]:
    return sorted({int(membership[u]) for u in users})


def run_world_b04(world: int, budget: int = PLANNER_BUDGET, horizon: int | None = None,
                  area_size: int = 5000, gate: dict[str, Any] | None = None,
                  timer: Callable | None = None, max_replans: int = MAX_REPLANS) -> dict[str, Any]:
    """Regression rollout (F) and arm B0 on one world, each on its own fresh static host."""
    timer = timer or (lambda f, *a, **k: (f(*a, **k), {}))
    world = int(world)
    timing: dict[str, Any] = {}

    env_r = make_static_host(world, area_size)
    env_r.reset(seed=world)
    horizon = int(env_r.max_steps if horizon is None else horizon)
    initial = np.array(env_r.uav_positions, dtype=float, copy=True)
    users0 = np.array(env_r.user_positions, dtype=float, copy=True)
    membership = cluster_layout(env_r)["membership"]
    reg, timing["regression"] = timer(regression_rollout, env_r, world, budget, horizon)
    assert_static(env_r, users0, "regression")
    reg_means = series_means(reg["coverage_backhauled"])
    if gate is not None:
        check_regression(world, reg, reg_means, initial, users0, gate)

    env_b = make_static_host(world, area_size)
    env_b.reset(seed=world)
    if not (np.array_equal(env_b.uav_positions, initial) and np.array_equal(env_b.user_positions, users0)):
        raise AssertionError("the two fresh hosts differ at reset")
    (result, rec), timing["b0"] = timer(run_b0, env_b, world, budget, horizon, max_replans)
    assert_static(env_b, users0, "B0")
    if result["t_end"] != horizon:
        raise AssertionError("B0 rollout ended early")
    b0_means = series_means(result["coverage_backhauled"])

    known_at = rec.pop("known_users_at")
    all_clusters = sorted({int(c) for c in membership})
    final_known = known_at[str(horizon)]
    readings = {
        "users_known": {k: len(v) for k, v in known_at.items()},
        "clusters_known": {k: len(clusters_of(v, membership)) for k, v in known_at.items()},
        "never_seen_clusters": [c for c in all_clusters if c not in clusters_of(final_known, membership)],
        "never_seen_users": int(len(users0) - len(final_known)),
    }
    if gate is not None:
        ref = gate_reference(gate)
        F, F100, F_source = ref["all_mean"], ref["final_100_mean"], "gate"
    else:
        F, F100, F_source = reg_means["all_mean"], reg_means["final_100_mean"], "regression"
    return {
        "world": world, "horizon": horizon, "budget": int(budget), "area_size": int(area_size),
        "F": {"source": F_source, "all_mean": F, "final_100_mean": F100,
              "gate_all_mean": None if gate is None else gate_reference(gate)["all_mean"],
              "regression_all_mean": reg_means["all_mean"],
              "regression_final_100_mean": reg_means["final_100_mean"],
              "regression_equals_gate": None if gate is None else True,
              "regression_evaluations": reg["evaluations"]},
        "B0": {**b0_means, **readings, **rec, "cpu_s": timing["b0"].get("cpu_s"),
               "coverage_backhauled": result["coverage_backhauled"],
               "known_users_at": known_at},
        "stakes": {"s_info0": float(F - b0_means["all_mean"]),
                   "s_info0_final100": float(F100 - b0_means["final_100_mean"])},
        "timing": timing,
    }

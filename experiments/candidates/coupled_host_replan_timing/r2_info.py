"""R2 (coupled_host_replan_timing): lawful-information re-planning arms, zero fits.

Pre-declaration and DM decisions: ``docs/research/candidates/coupled_host_replan_timing/NOTES.md``
("Pre-declaration -- ... R2" and "Owner resumed ... R2 starts").  Same event host, pre-event plan
and shared prefix as R1-lite (``rules.prefix_and_snapshot``); three arms continue from their own
deep copy of the snapshot taken at the start of step call ``t_e``:

* ``unshared``: the decision end re-plans from its own facts only;
* ``shared``:   every UAV forwards all facts it holds one hop per step along the host's actual
  UAV-UAV routing links; the decision end re-plans from own + received facts;
* ``D``:        privileged reference -- at the first step any UAV's own facts show a user
  > 100 m from the old map, the true post-event users are granted (``grant_truth``, the only
  truth accessor) and the cold procedure runs once; before that D is KEEP;
* ``shared_wide`` (R3): ``shared`` with one change, the forwarding neighbours: routing edges
  UNION mutually visible UAV pairs under the host's own UAV-UAV visibility rule
  (``env._get_local_uavs``, SINR >= min_sinr with interference; ``WIDE_FORWARDING_LINKS``).

INFORMATION RIGHTS (the audit screen is ``facts_for_uav`` .. ``InfoArm.targets``):

* Fact = (user, x, y, observation step, observer) for every user ``env._get_local_users(i)``
  returns for UAV ``i`` (the host's SINR >= min_sinr visibility rule, uncapped -- the obs vector
  truncates to ``max_observed_users``; the fact list does not, see ``VIEW_CAP_REPORTED``).
  ``env.user_positions`` is indexed ONLY by those visible indices.
* Clock: rollout calls ``targets(t)`` before step call ``t``; the host state is then the one after
  call ``t - 1``, so facts carry step ``t - 1`` and a decision taken on them governs call ``t``.
  The host's view first shows the event after call ``t_e``; the earliest reaction is call
  ``t_e + 1``.  The arms never read the event record, ``t_e``, the cluster or the new coordinates
  and never use the step counter as information (labels only).
* Holdings start empty at the branch.  Pre-event facts would equal the old map bit for bit
  (users are static before the event; the harness asserts ``snapshot.user_positions == old map``),
  so they can neither move a map entry nor fire a trigger: starting at the branch is exact.
* Forwarding (shared): ``H_t(a) = H_{t-1}(a) U own_t(a) U (U_{b in N_t(a)} H_{t-1}(b))`` with
  ``N_t`` the symmetrised consecutive UAV-UAV pairs of ``env.routing_paths`` in the state that
  produced step ``t``'s facts (``FORWARDING_LINKS``).  A fact observed by ``b`` at step ``s``
  reaches a neighbour at ``s + 1``: as many steps as hops.  Lossless, no content selection.
  Representation: each UAV stores, per user, the fact with the largest observation step.  This is
  exact for every quantity the arms use -- the map is the latest-step fact per user, and "latest
  of a union" = "latest of the latests", so the per-step recurrence gives the same map as holding
  every fact; same-step facts about one user carry identical xy (both read
  ``user_positions[u]`` at that step).  It is a storage form, not a message compression.
* Map: old map (pre-event positions of all users, known at t = 0) with each user that has a held
  fact placed at that fact's xy; users without a fact keep their old-map row (retention; absence
  from a view moves nobody).  ``map_fact_step`` (the step of the fact behind each row, None =
  never observed) is the unobserved-since flag.
* Trigger (unshared/shared): ``>= TRIGGER_K`` users whose map xy differs from the last PLANNED map
  by ``> MOVE_THRESHOLD_M`` -> cold procedure (``rules.d2_planner``, flat + relay searches at
  ``budget`` each, ``default_rng(world)``) on a shadow whose users are the MAP; UAVs matched by
  ``assign_targets`` from their current positions; planned map := map.  At most ``MAX_REPLANS``
  re-plans per world per arm; a trigger at the cap is recorded (``cap_hit``), not executed.
* Decision end: the gateway of the held pre-event deployment -- the UAV with the shortest
  ``routing_paths`` path in the snapshot state at the branch point (the state R1-lite's warm rule
  reads its routing from); unrouted = +inf, ties -> lower index; no routed UAV -> lower index with
  ``decision_end_reason = "no routed uav"`` (``DECISION_END_RULE``; DM decision replacing t = 0).
"""

from __future__ import annotations

import copy
import math
from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import static_evaluate
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    assign_targets,
    cluster_layout,
)
from experiments.candidates.coupled_host_replan_timing.event_host import (
    EventCoupledRelayHost,
    cluster_routing_facts,
)
from experiments.candidates.coupled_host_replan_timing.rules import (
    PLANNER_BUDGET,
    d2_planner,
    prefix_and_snapshot,
    rollout,
    shadow_host,
    state_fingerprint,
    assert_unchanged,
    window_metrics,
)

ARMS = ("unshared", "shared", "D")          # R2 arms, the runner's default
ALL_ARMS = ARMS + ("shared_wide",)         # R3 adds one arm; selected explicitly (--arms)
TRIGGER_K = 3                      # users moved vs the last planned map (DM decision, NOTES 22:20)
MOVE_THRESHOLD_M = 100.0           # strict: distance > 100 m
MAX_REPLANS = 3                    # per world per arm (pricing bound)
FORWARDING_LINKS = ("consecutive UAV-UAV node pairs of env.routing_paths (the host's actual "
                    "backhaul routes of that step), symmetrised; not the wider SINR adjacency "
                    "env.uav_connections")
DECISION_END_RULE = ("shortest len(env.routing_paths[i]) in the branch-point snapshot (held "
                     "pre-event deployment); unrouted = +inf; ties -> lower index; no routed UAV "
                     "-> lower index, decision_end_reason = 'no routed uav'")
WIDE_FORWARDING_LINKS = ("R3: FORWARDING_LINKS UNION {(a, b): b in visible_uavs(a) and a in "
                         "visible_uavs(b)}, visible_uavs(i) = env._get_local_uavs(i) (the host's "
                         "UAV-UAV SINR >= min_sinr rule with interference); mutual visibility "
                         "required, one-way visibility gives no edge; re-read every step")
VIEW_CAP_REPORTED = 20             # host obs vector cap (max_observed_users); facts are uncapped,
                                   # views above it are only counted


# ============================================================ information rights (audit screen)


def facts_for_uav(env: EventCoupledRelayHost, uav: int, step: int) -> dict[int, tuple]:
    """Own facts of ``uav`` at ``step``: {user: (step, x, y, observer)} for VISIBLE users only."""
    visible = [int(u) for u, _sinr in env._get_local_users(int(uav))]
    positions = np.asarray(env.user_positions, dtype=float)
    return {u: (int(step), float(positions[u, 0]), float(positions[u, 1]), int(uav)) for u in visible}


def routing_links(env: EventCoupledRelayHost) -> list[set[int]]:
    """Neighbours per UAV along the host's actual routing paths this step (both directions)."""
    neighbours: list[set[int]] = [set() for _ in range(env.n_uavs)]
    for path in env.routing_paths.values():
        uavs = [int(node) for kind, node in path if kind == "uav"]
        for a, b in zip(uavs, uavs[1:]):
            neighbours[a].add(b)
            neighbours[b].add(a)
    return neighbours


def visible_uavs(env: EventCoupledRelayHost, uav: int) -> list[int]:
    """UAVs ``uav`` can hear this step under the host's own UAV-UAV visibility rule."""
    return [int(j) for j, _sinr in env._get_local_uavs(int(uav))]


def wide_links(env: EventCoupledRelayHost,
               routing: list[set[int]] | None = None) -> list[set[int]]:
    """Routing edges UNION mutually visible UAV pairs this step (R3's forwarding neighbours)."""
    routing = routing_links(env) if routing is None else routing
    visible = [set(visible_uavs(env, i)) for i in range(env.n_uavs)]
    neighbours = [set(n) for n in routing]
    for a in range(env.n_uavs):
        for b in visible[a]:
            if b != a and a in visible[b]:
                neighbours[a].add(b)
                neighbours[b].add(a)
    return neighbours


def merge(held: dict[int, tuple], incoming: dict[int, tuple]) -> list[int]:
    """Add ``incoming`` facts; a user's held fact is replaced only by a strictly later one."""
    updated = []
    for user, fact in incoming.items():
        if user not in held or fact[0] > held[user][0]:
            held[user] = fact
            updated.append(user)
    return updated


def forward(holdings: list[dict], own: list[dict], links: list[set[int]]) -> list[dict]:
    """One synchronous step: H_t(a) = H_{t-1}(a) + own_t(a) + H_{t-1}(b) for b in N_t(a)."""
    new = [dict(h) for h in holdings]
    for a in range(len(holdings)):
        merge(new[a], own[a])
        for b in sorted(links[a]):
            merge(new[a], holdings[b])
    return new


def map_from(old_map: np.ndarray, held: dict[int, tuple]) -> np.ndarray:
    """Old map with each user that has a held fact at its (latest) observed xy; others retained."""
    out = np.array(old_map, dtype=float, copy=True)
    for user, (_step, x, y, _observer) in held.items():
        out[user] = (x, y)
    return out


def moved_users(current: np.ndarray, reference: np.ndarray,
                threshold: float = MOVE_THRESHOLD_M) -> list[int]:
    """Users whose xy differs from ``reference`` by more than ``threshold`` metres."""
    distance = np.linalg.norm(np.asarray(current, dtype=float) - np.asarray(reference, dtype=float), axis=1)
    return [int(u) for u in np.flatnonzero(distance > threshold)]


def shows_change(facts: dict[int, tuple], old_map: np.ndarray,
                 threshold: float = MOVE_THRESHOLD_M) -> list[int]:
    """Users whose fact places them more than ``threshold`` from the old map."""
    return sorted(u for u, (_s, x, y, _o) in facts.items()
                  if math.hypot(x - old_map[u, 0], y - old_map[u, 1]) > threshold)


def grant_truth(env: EventCoupledRelayHost) -> np.ndarray:
    """The ONLY truth access of the arms: D's grant of the true post-event users."""
    return env.post_event_user_positions()


class InfoArm:
    """Per-step decision rule of one arm; ``targets`` is ``rollout``'s ``targets_fn``."""

    def __init__(self, arm: str, env: EventCoupledRelayHost, keep_targets: np.ndarray,
                 old_map: np.ndarray, decision_end: int, world: int, budget: int) -> None:
        if arm not in ALL_ARMS:
            raise ValueError(f"unknown arm {arm!r}")
        self.arm, self.env, self.world, self.budget = arm, env, int(world), int(budget)
        self.old_map = np.array(old_map, dtype=float, copy=True)
        self.de = int(decision_end)
        self.current = np.array(keep_targets, dtype=float, copy=True)
        self.planned_map = self.old_map.copy()
        self.holdings: list[dict[int, tuple]] = [{} for _ in range(env.n_uavs)]
        self.first_change_per_uav: list[int | None] = [None] * env.n_uavs
        self.first_change_de: int | None = None
        self.changed_arrivals: dict[int, dict[str, int]] = {}
        self.triggers: list[dict[str, Any]] = []
        self.cap_hit_steps: list[int] = []
        self.evaluations = 0
        self.truth_grants: list[int] = []
        self.link_counts: list[int] = []
        self.wide_link_counts: list[int] = []  # shared_wide only
        self.views_over_cap = 0

    def targets(self, t: int) -> np.ndarray:
        env, s = self.env, int(t) - 1          # state = after call t - 1: facts of step s
        own = [facts_for_uav(env, i, s) for i in range(env.n_uavs)]
        links = routing_links(env)
        self.views_over_cap += sum(len(f) > VIEW_CAP_REPORTED for f in own)
        self.link_counts.append(sum(len(n) for n in links) // 2)
        for i, facts in enumerate(own):        # per-UAV detection (reporting; D's trigger)
            if self.first_change_per_uav[i] is None and shows_change(facts, self.old_map):
                self.first_change_per_uav[i] = s
        if self.arm == "shared":
            self.holdings = forward(self.holdings, own, links)
        elif self.arm == "shared_wide":
            wide = wide_links(env, links)
            self.wide_link_counts.append(sum(len(n) for n in wide) // 2)
            self.holdings = forward(self.holdings, own, wide)
        else:                                  # unshared and D: own facts only
            for i in range(env.n_uavs):
                merge(self.holdings[i], own[i])
        held = self.holdings[self.de]
        for u in shows_change(held, self.old_map):
            if u not in self.changed_arrivals:
                self.changed_arrivals[u] = {"obs_step": held[u][0], "arrival_step": s,
                                            "observer": held[u][3]}
        if self.first_change_de is None and self.changed_arrivals:
            self.first_change_de = s
        if self.arm == "D":
            if not self.truth_grants and any(v is not None for v in self.first_change_per_uav):
                self.truth_grants.append(s)
                self._replan(grant_truth(env), s, t, moved=None)
            return self.current
        current_map = map_from(self.old_map, held)
        moved = moved_users(current_map, self.planned_map)
        if len(moved) >= TRIGGER_K:
            if len(self.triggers) < MAX_REPLANS:
                self._replan(current_map, s, t, moved=moved)
                self.planned_map = current_map
            else:
                self.cap_hit_steps.append(s)
        return self.current

    def _replan(self, users_xy: np.ndarray, s: int, t: int, moved: list[int] | None) -> None:
        relay, flat = d2_planner(self.env, users_xy, self.world, self.budget)  # shadow; live asserted
        layout = np.asarray(relay.positions_xyz, dtype=float)
        self.current = layout[assign_targets(np.asarray(self.env.uav_positions, dtype=float), layout)]
        used = int(flat.evaluations) + int(relay.evaluations)
        self.evaluations += used
        self.triggers.append({"fact_step": int(s), "first_call_with_new_targets": int(t),
                              "moved_users": moved, "evaluations": used,
                              "targets_xyz": self.current.tolist()})

    def record(self) -> dict[str, Any]:
        links = np.asarray(self.link_counts, dtype=float)
        out = {
            "arm": self.arm, "decision_end": self.de,
            "first_change_step_per_uav": list(self.first_change_per_uav),
            "first_change_step_at_decision_end": self.first_change_de,
            "detection_step_any_uav": min((v for v in self.first_change_per_uav if v is not None),
                                          default=None),
            "changed_fact_arrivals_at_decision_end": {str(u): v for u, v in sorted(self.changed_arrivals.items())},
            "trigger_steps": [{k: tr[k] for k in ("fact_step", "first_call_with_new_targets")}
                              for tr in self.triggers],
            "triggers": self.triggers, "replans": len(self.triggers),
            "evaluations_used": int(self.evaluations),
            "cap_hit": bool(self.cap_hit_steps), "cap_hit_trigger_steps": len(self.cap_hit_steps),
            "first_cap_hit_step": self.cap_hit_steps[0] if self.cap_hit_steps else None,
            "truth_grant_steps": list(self.truth_grants),
            "map_fact_step_at_decision_end": {str(u): f[0] for u, f in sorted(self.holdings[self.de].items())},
            "routing_links": {"mean": float(links.mean()) if links.size else None,
                              "min": int(links.min()) if links.size else None,
                              "steps_with_zero_links": int(np.sum(links == 0))},
            "views_over_obs_cap": int(self.views_over_cap),
        }
        if self.arm == "shared_wide":
            wide = np.asarray(self.wide_link_counts, dtype=float)
            out["wide_links"] = {"mean": float(wide.mean()) if wide.size else None,
                                 "min": int(wide.min()) if wide.size else None,
                                 "steps_with_zero_links": int(np.sum(wide == 0))}
            out["wide_edges_added_mean"] = float((wide - links).mean()) if wide.size else None
            out["wide_link_counts_per_step"] = [int(v) for v in self.wide_link_counts]
            out["routing_link_counts_per_step"] = [int(v) for v in self.link_counts]
        return out


# ============================================================ harness (truth used for set-up/reporting)


def gateway_uav(env: EventCoupledRelayHost) -> int:
    """Shortest ``routing_paths`` path in the env's current state (unrouted = +inf, ties -> lower)."""
    lengths = [len(env.routing_paths[i]) if i in env.routing_paths else math.inf
               for i in range(env.n_uavs)]
    return int(min(range(env.n_uavs), key=lambda i: (lengths[i], i)))


def run_arm(snapshot: EventCoupledRelayHost, arm: str, keep_targets: np.ndarray,
            old_map: np.ndarray, decision_end: int, world: int, budget: int,
            horizon: int) -> tuple[dict[str, Any], dict[str, Any], EventCoupledRelayHost]:
    """One arm on its own deep copy of the snapshot, R1-lite's straight-line executor."""
    env = copy.deepcopy(snapshot)
    controller = InfoArm(arm, env, keep_targets, old_map, decision_end, world, budget)
    result = rollout(env, controller.targets, int(env.current_step), horizon)
    return result, controller.record(), env


def run_world_r2(env: EventCoupledRelayHost, budget: int = PLANNER_BUDGET,
                 arms: tuple[str, ...] = ARMS, horizon: int | None = None,
                 timer: Callable | None = None) -> dict[str, Any]:
    """Pre-event plan + shared prefix (as R1-lite ``run_world``), then the R2 arms."""
    timer = timer or (lambda f, *a, **k: (f(*a, **k), {}))
    world = int(env.world_seed)
    horizon = int(env.max_steps if horizon is None else horizon)
    timing: dict[str, Any] = {}
    env.reset(seed=world)
    initial = np.array(env.uav_positions, dtype=float, copy=True)
    old_map = np.array(env.user_positions, dtype=float, copy=True)
    reset_gateway = gateway_uav(env)                  # record only (the superseded t = 0 rule)
    routed_at_reset = sorted(int(i) for i in env.routing_paths)
    (relay0, _flat0), timing["pre_event_plan"] = timer(d2_planner, env, old_map, world, budget)
    sites = np.asarray(relay0.positions_xyz, dtype=float)
    keep_targets = sites[assign_targets(initial, sites)]
    deployed = shadow_host(env, old_map)
    static_evaluate(deployed, keep_targets, allow_a2a=True)
    deployed_gateway = gateway_uav(deployed) if deployed.routing_paths else None
    (prefix, snapshot), timing["pre_event_prefix"] = timer(
        prefix_and_snapshot, env, keep_targets, world, horizon)
    t_e = int(snapshot.current_step)
    decision_end = gateway_uav(snapshot)              # held pre-event deployment at the branch point
    routed_at_snapshot = sorted(int(i) for i in snapshot.routing_paths)
    decision_end_reason = ("shortest routing path at the branch-point snapshot" if routed_at_snapshot
                           else "no routed uav")
    if not np.array_equal(snapshot.user_positions, old_map):
        raise AssertionError("users moved before the event: starting holdings empty is not exact")
    event = snapshot.event_info                       # reporting only
    membership = cluster_layout(snapshot)["membership"]
    routing = cluster_routing_facts(snapshot, int(event["cluster"]), membership)
    snap_fp = state_fingerprint(snapshot)
    pre_cov = prefix["coverage_backhauled"]
    record: dict[str, Any] = {
        "world": world, "t_e": t_e, "horizon": horizon, "budget": int(budget),
        "cluster": int(event["cluster"]), "routing_class": routing["class"],
        "decision_end": decision_end, "decision_end_reason": decision_end_reason,
        "routed_uavs_at_snapshot": routed_at_snapshot,
        "reset_gateway": reset_gateway, "routed_uavs_at_reset": routed_at_reset,
        "deployed_layout_gateway": deployed_gateway,
        "pre_event_mean": float(np.mean(pre_cov)),
        "keep_targets_xyz": keep_targets.tolist(), "arms": {},
    }
    for arm in arms:
        (result, rec, arm_env), timing[arm] = timer(
            run_arm, snapshot, arm, keep_targets, old_map, decision_end, world, budget, horizon)
        if not arm_env.event_applied or arm_env.event.get("applied_in_step_call") != t_e:
            raise AssertionError(f"{arm}: the event was not applied in step call t_e")
        metrics = window_metrics(pre_cov, result["coverage_backhauled"])
        record["arms"][arm] = {"post_event_mean": metrics["post_event_mean"],
                               "all_mean": metrics["all_mean"], **rec,
                               "cpu_s": timing[arm].get("cpu_s"),
                               "post_event_coverage_backhauled": result["coverage_backhauled"]}
    assert_unchanged(snapshot, snap_fp, "the R2 arms")
    detections = {rec["detection_step_any_uav"] for rec in record["arms"].values()}
    if len(detections) > 1:  # every arm is KEEP until the first detection, so this is shared
        raise AssertionError(f"world {world}: first detection differs across arms {detections}")
    record["timing"] = timing
    return record


def stakes(post: dict[str, float], cold: float | None) -> dict[str, float | None]:
    """Per-world stakes on the post-event window (cold = R1-lite reference F); ``delta_adj`` =
    shared_wide - shared only when the run has the shared_wide arm (R2 rows unchanged)."""
    def diff(a, b):
        return None if a is None or b is None else float(a - b)
    return {"delta_share": diff(post.get("shared"), post.get("unshared")),
            "s_info_unshared": diff(cold, post.get("unshared")),
            "s_info_shared": diff(cold, post.get("shared")),
            "d_minus_shared": diff(post.get("D"), post.get("shared")),
            "d_minus_unshared": diff(post.get("D"), post.get("unshared")),
            **({"delta_adj": diff(post.get("shared_wide"), post.get("shared"))}
               if "shared_wide" in post else {})}

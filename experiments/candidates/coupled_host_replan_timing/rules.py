"""R1-lite zero-fit rules on the single-event coupled host (coupled_host_replan_timing).

All rules are full-information and deterministic given the world seed; none draws randomness
beyond D2's planner rule (``numpy.random.default_rng(world)``, a fresh instance per search, as in
``run_gate.py`` / ``menus.compute_menu``).  Every rule flies D2's straight-line executor
(``planner.straight_line_actions``: straight at max_speed, land exactly, hold on arrival).

Episode structure (one world):

1. Pre-event plan = D2's ``P_relay`` exactly as ``run_gate.py`` / ``menus.compute_menu`` build it:
   ``P_flat = search_placement(A2A off, budget, default_rng(world))``, then ``P_relay =
   search_placement(A2A on, budget, default_rng(world), extra_candidates=[P_flat])``; the UAV
   -> site assignment is ``assign_targets(initial, P_relay)`` (min-makespan permutation search),
   giving the UAV-indexed pre-event targets ``keep_targets``.
2. Pre-event prefix, shared by every rule: steps ``0 .. t_e - 1`` toward ``keep_targets``, executed
   once; the host is then deep-copied (``snapshot``) at the start of step ``t_e`` (before the event,
   which the host applies inside that step call).  Every rule and every grid rollout continues
   from its own deep copy of the snapshot, so the prefix (actions and C_bh trace) is identical
   across rules by construction.  At run time ``KEEP`` (prefix + branch) is additionally compared
   bit for bit with an un-branched ``closed_loop_execute`` of D2 on a fresh copy of the event host.
3. At the decision for step ``t_e`` every rule sees the post-event users via
   ``host.post_event_user_positions()`` (full information) and the UAV positions at the start of
   step ``t_e``.  Every re-plan search runs on a *shadow* (a deep copy of the snapshot whose
   ``user_positions`` are the post-event users) and the snapshot's state fingerprint (UAV and user
   positions, step counter, RandomState state, event flag, connections, routing) is asserted
   unchanged after each search.

Rules (post-event targets; the pre-event targets are ``keep_targets`` for all):

* ``keep``: ``keep_targets`` held for the whole episode.
* ``cold`` (SET-now): D2's pre-event planner procedure re-run from scratch on the post-event users
  (flat + relay searches, ``budget`` each, ``default_rng(world)`` fresh per search);
  ``assign_targets`` from the UAV positions at ``t_e``.
* ``warm`` (SET, held re-placement; ``warm_rule``): full ``budget`` for a restricted descent.
  The movable UAVs are those ``event_host.cluster_routing_facts`` finds from the PRE-EVENT ACTUAL
  association/routing (the host state at the end of step ``t_e - 1``): the servers of the
  relocated cluster's users whose plurality cluster it is, plus relays of their paths used by no
  other served UAV.  Every other UAV keeps its pre-event target (the UAV-site assignment is held;
  no global re-assignment) -- a definitional property of ``warm``.  The movable rows are
  re-placed by a restricted copy of the planner's descent (same moves, stage schedule
  100 -> 50 -> 25 m xy and +-50 m z, strict improvement else plateau-potential tie-break, top-3
  starts, budget split equally) that moves only the movable rows; starts: the held rows and, for
  ``n = 0 .. min(m - 1, max_hops)`` relays, the service UAV at the new cluster's member mean,
  ``n`` relays at ``relay_distances`` on the BS -> centre line and any remaining movable UAVs at
  the centre (100 m height, the planner's geometry).  The movable UAVs are then matched to the
  re-placed rows by ``assign_targets`` among themselves.

  Empty movable set (classes ``unserved`` / ``shared_only``; ``chain``, ``direct`` and
  ``unrouted`` always have a movable primary server; the fallback runs whenever the set is
  empty): ``fallback_movable`` tries each of the six UAVs in index order as the single movable
  UAV, its site re-placed for the new cluster by the same restricted descent *without* the held
  start (per-candidate budget ``FALLBACK_CANDIDATE_BUDGET`` = 500, total 3000), and scores each by
  its static contract reward.  The best candidate (ties: lower index) is adopted only if its
  static reward exceeds the held layout's by more than ``IMPROVEMENT_TOL``; otherwise the movable
  set stays empty, warm == KEEP and ``warm_equals_keep`` is recorded with the reason.
* ``seeded``: ``search_placement(A2A on, budget, default_rng(world), extra_candidates=[pre-event
  P_relay sites])`` (the cold search seeded with the current layout); UAVs matched by
  ``assign_targets`` from the positions at ``t_e`` (all UAVs may move).  Reported like ``cold``.

No selection between rules happens anywhere; every rule is its own row.

The departure *small grid* (``run_grid``, a separate pass over an existing warm result): for each
of the 2^6 subsets of UAVs allowed to depart and each delay ``d`` in ``GRID_DELAYS``, the departing
UAVs switch together from their pre-event target to warm SET's target at step ``t_e + d`` and the
others keep their pre-event targets; 192 entries per world.  Two entries whose per-UAV switch
schedules coincide (a departing UAV whose warm target equals its pre-event target switches
nothing) are the same rollout bit for bit and are executed once (``unique_rollouts`` recorded).
The all-depart, delay-0 entry is warm SET and the empty subset is KEEP; both identities are
asserted against the warm/KEEP series of the input run.
"""

from __future__ import annotations

import copy
import itertools
from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import static_evaluate
from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
    ARRIVAL_TOL_M,
    IMPROVEMENT_TOL,
    N_STARTS,
    POTENTIAL_TOL,
    SERVICE_HEIGHT_M,
    XY_STEPS_M,
    Z_STEP_M,
    _clip_positions,
    assign_targets,
    closed_loop_execute,
    cluster_layout,
    max_routable_relays,
    plateau_potential,
    relay_distances,
    search_placement,
    straight_line_actions,
)
from experiments.candidates.coupled_host_replan_timing.event_host import (
    EventCoupledRelayHost,
    cluster_routing_facts,
)

PLANNER_BUDGET = 3000
GRID_DELAYS = (0, 20, 50)
RULES = ("keep", "cold", "warm", "seeded")
FALLBACK_CANDIDATE_BUDGET = 500


# ------------------------------------------------------------------------------ state guards


def state_fingerprint(env: EventCoupledRelayHost) -> dict[str, Any]:
    """Bytes of the live episode state a planning call must not touch."""
    rs = env.np_random.get_state()
    return {
        "uav_positions": np.asarray(env.uav_positions).tobytes(),
        "user_positions": np.asarray(env.user_positions).tobytes(),
        "current_step": int(env.current_step),
        "np_random": (rs[0], np.asarray(rs[1]).tobytes(), int(rs[2]), int(rs[3]), float(rs[4])),
        "event_applied": bool(env.event_applied),
        "connections": np.asarray(env.connections).tobytes(),
        "uav_connections": np.asarray(env.uav_connections).tobytes(),
        "routing_paths": repr(sorted((int(k), list(v)) for k, v in env.routing_paths.items())),
        "a2a_enabled": bool(env.a2a_enabled),
    }


def assert_unchanged(env: EventCoupledRelayHost, before: dict[str, Any], what: str) -> None:
    after = state_fingerprint(env)
    changed = [key for key in before if before[key] != after[key]]
    if changed:
        raise AssertionError(f"{what} mutated the live host state: {changed}")


def shadow_host(env: EventCoupledRelayHost, users_xy: np.ndarray) -> EventCoupledRelayHost:
    """A planning copy of ``env`` whose users are ``users_xy`` (the live env is never touched)."""
    shadow = copy.deepcopy(env)
    shadow.user_positions = np.array(users_xy, dtype=float, copy=True)
    return shadow


# ------------------------------------------------------------------------------ planners


def d2_planner(env: EventCoupledRelayHost, users_xy: np.ndarray, world: int, budget: int):
    """D2's P_relay procedure (run_gate.py / menus.compute_menu) on a shadow with ``users_xy``."""
    before = state_fingerprint(env)
    shadow = shadow_host(env, users_xy)
    flat = search_placement(shadow, False, int(budget), np.random.default_rng(int(world)))
    relay = search_placement(shadow, True, int(budget), np.random.default_rng(int(world)),
                             extra_candidates=[flat.positions_xyz],
                             extra_kind="flat_result_incumbent")
    assert_unchanged(env, before, "d2_planner")
    return relay, flat


def static_value(env: EventCoupledRelayHost, users_xy: np.ndarray, positions: np.ndarray) -> dict[str, float]:
    """Static contract reward / C_bh of UAV-indexed ``positions`` on ``users_xy`` (on a shadow)."""
    before = state_fingerprint(env)
    info = static_evaluate(shadow_host(env, users_xy), np.asarray(positions, dtype=float), allow_a2a=True)
    assert_unchanged(env, before, "static_value")
    return {"contract_reward": float(info["contract_reward"]),
            "coverage_backhauled": float(info["coverage_backhauled"])}


def replacement_candidates(env: EventCoupledRelayHost, layout: np.ndarray, movable: list[int],
                           centre_xy: np.ndarray) -> list[dict[str, Any]]:
    """Starts of the held re-placement: the held layout, then n = 0..min(m-1, max_hops) relays."""
    layout = np.asarray(layout, dtype=float)
    out = [{"kind": "held", "positions_xyz": layout.copy()}]
    m = len(movable)
    if m == 0:
        return out
    bs_xy = np.asarray(env.ground_bs_positions[0, :2], dtype=float)
    delta = np.asarray(centre_xy, dtype=float) - bs_xy
    distance = float(np.linalg.norm(delta))
    unit = delta / distance if distance > 0 else np.zeros(2)
    for n_relays in range(0, min(m - 1, max_routable_relays(env)) + 1):
        rows = [[centre_xy[0], centre_xy[1], SERVICE_HEIGHT_M]]
        for along in relay_distances(distance, n_relays):
            xy = bs_xy + along * unit
            rows.append([xy[0], xy[1], SERVICE_HEIGHT_M])
        while len(rows) < m:
            rows.append([centre_xy[0], centre_xy[1], SERVICE_HEIGHT_M])
        positions = layout.copy()
        positions[list(movable)] = np.asarray(rows, dtype=float)
        out.append({"kind": f"replace_relays_{n_relays}",
                    "positions_xyz": _clip_positions(env, positions)})
    seen: set[bytes] = set()
    kept = []
    for candidate in out:
        key = np.round(candidate["positions_xyz"], 6).tobytes()
        if key not in seen:
            seen.add(key)
            kept.append(candidate)
    return kept


def held_site_replacement(env: EventCoupledRelayHost, users_xy: np.ndarray, layout: np.ndarray,
                          movable: list[int], centre_xy: np.ndarray, budget: int,
                          xy_steps: tuple[float, ...] = XY_STEPS_M,
                          include_held_start: bool = True) -> dict[str, Any]:
    """Restricted planner descent: only ``movable`` rows of the UAV-indexed ``layout`` move.

    Mirrors ``planner.search_placement``'s descent (moves +-x, +-y by the stage step and +-z by
    50 m per UAV in index order; strict improvement of the contract reward, else plateau-potential
    decrease on equal reward; 100 -> 50 -> 25 m stages; top-``N_STARTS`` starts, budget split
    equally, remainder to the first) on a shadow host.  Never uses more than ``budget``
    evaluations; returns the best start's layout (ties: the earlier start).  With
    ``include_held_start=False`` the held layout is not a start (the movable rows begin at the
    new cluster), as in the empty-set fallback.
    """
    before = state_fingerprint(env)
    shadow = shadow_host(env, users_xy)
    movable = sorted(int(u) for u in movable)
    evaluations = 0

    def evaluate(positions: np.ndarray):
        nonlocal evaluations
        info = static_evaluate(shadow, positions, allow_a2a=True)
        evaluations += 1
        return float(info["contract_reward"]), plateau_potential(shadow, True), info

    candidates = replacement_candidates(env, layout, movable, centre_xy)
    if not include_held_start:
        if not movable:
            raise ValueError("an empty movable set needs the held start")
        candidates = [c for c in candidates if c["kind"] != "held"]
    budget = int(budget)
    if budget < 1:
        raise ValueError("budget must be >= 1")
    evaluated = candidates[: min(len(candidates), budget)]
    for candidate in evaluated:
        reward, potential, info = evaluate(candidate["positions_xyz"])
        candidate.update(contract_reward=reward, potential=potential,
                         coverage_backhauled=float(info["coverage_backhauled"]))
    ranked = sorted(range(len(evaluated)),
                    key=lambda i: (-evaluated[i]["contract_reward"], i))[:N_STARTS]
    if not movable:
        ranked = ranked[:1]
    remaining = budget - evaluations
    shares = [remaining // len(ranked) + (1 if s < remaining % len(ranked) else 0)
              for s in range(len(ranked))]
    best = None
    starts = []
    for s, index in enumerate(ranked):
        candidate = evaluated[index]
        position = np.array(candidate["positions_xyz"], dtype=float)
        reward, potential = candidate["contract_reward"], candidate["potential"]
        coverage = candidate["coverage_backhauled"]
        limit = evaluations + shares[s]
        stage_index, converged, used_before = 0, not movable, evaluations
        while movable and evaluations < limit:
            moved = False
            step = xy_steps[stage_index]
            moves = ((step, 0.0, 0.0), (-step, 0.0, 0.0), (0.0, step, 0.0), (0.0, -step, 0.0),
                     (0.0, 0.0, Z_STEP_M), (0.0, 0.0, -Z_STEP_M))
            for uav in movable:
                for move in moves:
                    if evaluations >= limit:
                        break
                    trial = position.copy()
                    trial[uav] += move
                    trial = _clip_positions(shadow, trial)
                    if np.array_equal(trial, position):
                        continue
                    trial_reward, trial_potential, info = evaluate(trial)
                    if (trial_reward > reward + IMPROVEMENT_TOL
                            or (abs(trial_reward - reward) <= IMPROVEMENT_TOL
                                and trial_potential < potential - POTENTIAL_TOL)):
                        position, reward, potential = trial, trial_reward, trial_potential
                        coverage = float(info["coverage_backhauled"])
                        moved = True
                if evaluations >= limit:
                    break
            if evaluations >= limit:
                break
            if not moved:
                if stage_index + 1 < len(xy_steps):
                    stage_index += 1
                else:
                    converged = True
                    break
        record = {"start": s, "kind": candidate["kind"], "start_reward": candidate["contract_reward"],
                  "final_reward": reward, "share": shares[s],
                  "evaluations": evaluations - used_before, "converged": converged}
        starts.append(record)
        if best is None or reward > best["reward"] + IMPROVEMENT_TOL:
            best = {"reward": reward, "coverage": coverage, "position": position, "record": record}
    assert best is not None
    held_rows = [u for u in range(len(layout)) if u not in movable]
    if not np.array_equal(best["position"][held_rows], np.asarray(layout, dtype=float)[held_rows]):
        raise AssertionError("held re-placement moved a held row")
    assert_unchanged(env, before, "held_site_replacement")
    return {"positions_xyz": best["position"], "contract_reward": float(best["reward"]),
            "coverage_backhauled": float(best["coverage"]), "evaluations": int(evaluations),
            "budget": budget, "movable": movable, "starts": starts,
            "candidates": [{"kind": c["kind"], "contract_reward": c.get("contract_reward")}
                           for c in candidates]}


def match_movable(positions_te: np.ndarray, held_targets: np.ndarray, new_layout: np.ndarray,
                  movable: list[int]) -> np.ndarray:
    """UAV-indexed targets: held rows unchanged; movable UAVs matched to the movable rows of
    ``new_layout`` by the planner's min-makespan permutation search among themselves."""
    targets = np.array(held_targets, dtype=float, copy=True)
    movable = sorted(int(u) for u in movable)
    if movable:
        rows = np.asarray(new_layout, dtype=float)[movable]
        perm = assign_targets(np.asarray(positions_te, dtype=float)[movable], rows)
        targets[movable] = rows[perm]
    return targets


def fallback_movable(env: EventCoupledRelayHost, users_xy: np.ndarray, layout: np.ndarray,
                     centre_xy: np.ndarray,
                     per_candidate_budget: int = FALLBACK_CANDIDATE_BUDGET) -> dict[str, Any]:
    """Empty movable set: try each UAV in turn as the single UAV re-placed for the new cluster.

    Candidate ``u``: ``held_site_replacement(movable=[u], include_held_start=False)`` at
    ``per_candidate_budget``.  Adopted: the best static contract reward (ties: lower index), only
    if it exceeds the held layout's static reward by more than ``IMPROVEMENT_TOL``.
    """
    held_value = static_value(env, users_xy, layout)["contract_reward"]
    records, best = [], None
    for uav in range(env.n_uavs):
        result = held_site_replacement(env, users_xy, layout, [uav], centre_xy,
                                       per_candidate_budget, include_held_start=False)
        records.append({"uav": uav, "contract_reward": result["contract_reward"],
                        "evaluations": result["evaluations"]})
        if (result["contract_reward"] > held_value + IMPROVEMENT_TOL
                and (best is None or result["contract_reward"] > best[1]["contract_reward"] + IMPROVEMENT_TOL)):
            best = (uav, result)
    return {"held_contract_reward": held_value, "per_candidate_budget": int(per_candidate_budget),
            "candidates": records, "chosen_uav": None if best is None else int(best[0]),
            "result": None if best is None else best[1],
            "evaluations": int(sum(r["evaluations"] for r in records))}


def warm_rule(env: EventCoupledRelayHost, users_xy: np.ndarray, keep_targets: np.ndarray,
              positions_te: np.ndarray, facts: dict[str, Any], centre_xy: np.ndarray,
              budget: int = PLANNER_BUDGET,
              fallback_budget: int = FALLBACK_CANDIDATE_BUDGET) -> dict[str, Any]:
    """warm SET's UAV-indexed targets (held re-placement; see the module doc).

    ``env`` is the live snapshot (never mutated), ``facts`` the pre-event routing facts of the
    relocated cluster.  Non-movable UAVs keep ``keep_targets`` rows exactly.
    """
    keep_targets = np.asarray(keep_targets, dtype=float)
    movable = [int(u) for u in facts["movable_uavs"]]
    record: dict[str, Any] = {"movable_source": "pre_event_routing", "fallback": None}
    result = None
    if movable:
        result = held_site_replacement(env, users_xy, keep_targets, movable, centre_xy, budget)
    else:
        fallback = fallback_movable(env, users_xy, keep_targets, centre_xy, fallback_budget)
        record["fallback"] = {k: v for k, v in fallback.items() if k != "result"}
        if fallback["chosen_uav"] is not None:
            movable, result = [fallback["chosen_uav"]], fallback["result"]
            record["movable_source"] = "fallback_single_uav"
        else:
            record["movable_source"] = "empty"
    targets = (match_movable(positions_te, keep_targets, result["positions_xyz"], movable)
               if movable else keep_targets.copy())
    held_rows = [u for u in range(len(keep_targets)) if u not in movable]
    if not np.array_equal(targets[held_rows], keep_targets[held_rows]):
        raise AssertionError("warm moved a non-movable UAV")
    equals_keep = bool(np.array_equal(targets, keep_targets))
    reason = None
    if equals_keep:
        reason = ("empty movable set: no single-UAV candidate beat the held layout's static reward"
                  if not movable else "the re-placement kept every movable row")
    record.update({
        "targets": targets, "movable_uavs": movable, "warm_equals_keep": equals_keep,
        "warm_equals_keep_reason": reason,
        "evaluations": int((result["evaluations"] if (result is not None and facts["movable_uavs"]) else 0)
                           + (record["fallback"]["evaluations"] if record["fallback"] else 0)),
        "search": None if result is None else {
            "contract_reward": result["contract_reward"], "evaluations": result["evaluations"],
            "budget": result["budget"], "starts": result["starts"],
            "start_candidates": result["candidates"]},
        **{f"static_{k}": v for k, v in static_value(env, users_xy, targets).items()},
    })
    return record


# ------------------------------------------------------------------------------ execution


def rollout(env: EventCoupledRelayHost, targets_fn: Callable[[int], np.ndarray], t_start: int,
            t_end: int, final_targets: np.ndarray | None = None,
            record_actions: bool = False) -> dict[str, Any]:
    """Step ``env`` from its current step ``t_start`` to ``t_end`` with the straight-line rule.

    ``targets_fn(t)`` returns the UAV-indexed assigned targets for step ``t``.  ``arrival_step`` is
    the first step at which every UAV sat (within ``ARRIVAL_TOL_M``) on ``final_targets`` and those
    were the assigned targets.  The returned team reward is checked against ``reward_info``.
    """
    if int(env.current_step) != int(t_start):
        raise AssertionError(f"rollout starts at {t_start} but the host is at {env.current_step}")
    stride = float(env.max_speed) * float(env.time_step)
    coverage: list[float] = []
    reward: list[float] = []
    actions_log: list[np.ndarray] = []
    arrival = None
    for t in range(int(t_start), int(t_end)):
        assigned = np.asarray(targets_fn(t), dtype=float).reshape(env.n_uavs, 3)
        actions, distance = straight_line_actions(env.uav_positions, assigned, stride)
        if (arrival is None and final_targets is not None
                and np.array_equal(assigned, final_targets) and np.all(distance <= ARRIVAL_TOL_M)):
            arrival = t
        if record_actions:
            actions_log.append(actions.copy())
        _obs, rewards, terminations, _tr, _info = env.step(
            {agent: actions[i] for i, agent in enumerate(env.agents)})
        info = env.reward_info
        team = sum(float(rewards[agent]) for agent in env.agents)
        if not np.isclose(team, info["contract_reward"], rtol=0, atol=1e-9):
            raise AssertionError(f"step {t}: team reward {team} != {info['contract_reward']}")
        coverage.append(float(info["coverage_backhauled"]))
        reward.append(float(info["contract_reward"]))
        if all(terminations.values()):
            break
    out = {"coverage_backhauled": coverage, "contract_reward": reward, "arrival_step": arrival,
           "t_start": int(t_start), "t_end": int(t_start) + len(coverage)}
    if record_actions:
        out["actions"] = actions_log
    return out


def window_metrics(pre: list[float], post: list[float]) -> dict[str, Any]:
    """Per-world window means (the per-world value first; cross-world means are taken later)."""
    pre_a, post_a = np.asarray(pre, dtype=float), np.asarray(post, dtype=float)
    pre_mean = float(pre_a.mean()) if pre_a.size else None
    return {
        "post_event_mean": float(post_a.mean()) if post_a.size else None,
        "all_mean": float(np.concatenate([pre_a, post_a]).mean()),
        "pre_event_mean": pre_mean,
        "transition_loss_steps": (int(np.sum(post_a < pre_mean)) if pre_mean is not None else None),
        "post_event_steps": int(post_a.size),
    }


def prefix_and_snapshot(env: EventCoupledRelayHost, keep_targets: np.ndarray, world: int,
                        horizon: int) -> tuple[dict[str, Any], EventCoupledRelayHost]:
    """Reset, run the shared pre-event prefix (steps 0..t_e-1) and deep-copy the host at t_e."""
    env.reset(seed=int(world))
    t_e = int(env.event["t_e"])
    if not 0 < t_e < horizon:
        raise ValueError(f"t_e {t_e} outside (0, {horizon})")
    prefix = rollout(env, lambda t: keep_targets, 0, t_e, final_targets=keep_targets,
                     record_actions=True)
    if prefix["t_end"] != t_e or env.event_applied:
        raise AssertionError("the prefix did not stop at the start of step t_e")
    return prefix, copy.deepcopy(env)


def branch(snapshot: EventCoupledRelayHost, targets_fn, final_targets, horizon: int) -> dict[str, Any]:
    env = copy.deepcopy(snapshot)
    t_e = int(snapshot.current_step)
    result = rollout(env, targets_fn, t_e, horizon, final_targets=final_targets)
    if not env.event_applied or env.event.get("applied_in_step_call") != t_e:
        raise AssertionError("the event was not applied in step call t_e")
    return result


def run_world(env: EventCoupledRelayHost, budget: int = PLANNER_BUDGET,
              rules: tuple[str, ...] = RULES, horizon: int | None = None,
              timer: Callable | None = None) -> dict[str, Any]:
    """KEEP / cold / warm / seeded on one world; returns the JSON-ready world record."""
    timer = timer or (lambda f, *a, **k: (f(*a, **k), {}))
    world = int(env.world_seed)
    horizon = int(env.max_steps if horizon is None else horizon)
    rules = tuple(rules)
    unknown = set(rules) - set(RULES)
    if unknown:
        raise ValueError(f"unknown rules {sorted(unknown)}")
    timing: dict[str, Any] = {}

    # ---- pre-event plan and shared prefix
    env.reset(seed=world)
    initial = np.array(env.uav_positions, dtype=float, copy=True)
    pre_users = np.array(env.user_positions, dtype=float, copy=True)
    (relay0, flat0), timing["pre_event_plan"] = timer(d2_planner, env, pre_users, world, budget)
    sites = np.asarray(relay0.positions_xyz, dtype=float)
    perm0 = assign_targets(initial, sites)
    keep_targets = sites[perm0]
    (prefix, snapshot), timing["pre_event_prefix"] = timer(
        prefix_and_snapshot, env, keep_targets, world, horizon)
    t_e = int(snapshot.current_step)
    event = snapshot.event_info
    membership = cluster_layout(snapshot)["membership"]
    cluster = int(event["cluster"])
    positions_te = np.array(snapshot.uav_positions, dtype=float, copy=True)
    post_users = snapshot.post_event_user_positions()
    snap_fp = state_fingerprint(snapshot)

    # routing facts: actual state at the end of step t_e - 1, and the static sites (secondary)
    facts_actual = cluster_routing_facts(snapshot, cluster, membership)
    shadow_sites = shadow_host(snapshot, pre_users)
    static_evaluate(shadow_sites, keep_targets, allow_a2a=True)
    facts_static = cluster_routing_facts(shadow_sites, cluster, membership)
    pre_arrived = bool(np.all(np.linalg.norm(positions_te - keep_targets, axis=1) <= ARRIVAL_TOL_M))
    event["pre_event_routing"] = facts_actual
    event["pre_event_routing_static_sites"] = facts_static
    event["routing_class"] = facts_actual["class"]
    event["chain_served"] = facts_actual["chain_served"]
    event["routing_actual_equals_static"] = (
        facts_actual["class"] == facts_static["class"]
        and facts_actual["movable_uavs"] == facts_static["movable_uavs"])
    event["pre_event_arrived_at_t_e"] = pre_arrived

    pre_cov = prefix["coverage_backhauled"]
    record: dict[str, Any] = {
        "world": world, "t_e": t_e, "horizon": horizon, "budget": int(budget),
        "event_info": event,
        "pre_event": {
            "P_relay_sites_xyz": sites.tolist(), "P_relay_static_contract_reward": relay0.contract_reward,
            "P_relay_static_coverage_backhauled": relay0.coverage_backhauled,
            "P_flat_static_contract_reward": flat0.contract_reward,
            "initial_positions_xyz": initial.tolist(), "permutation": perm0.tolist(),
            "keep_targets_xyz": keep_targets.tolist(), "positions_at_t_e_xyz": positions_te.tolist(),
            "coverage_backhauled": pre_cov, "contract_reward": prefix["contract_reward"],
            "pre_event_mean": float(np.mean(pre_cov)), "arrival_step": prefix["arrival_step"],
        },
        "rules": {},
    }

    def finish(name: str, targets: np.ndarray, result: dict[str, Any], extra: dict[str, Any]):
        metrics = window_metrics(pre_cov, result["coverage_backhauled"])
        record["rules"][name] = {
            **metrics, "arrival_step": result["arrival_step"],
            "post_event_contract_reward_mean": float(np.mean(result["contract_reward"])),
            "targets_xyz": np.asarray(targets).tolist(),
            "moved_uavs": [int(u) for u in range(env.n_uavs)
                           if not np.array_equal(targets[u], keep_targets[u])],
            "post_event_coverage_backhauled": result["coverage_backhauled"],
            **extra}

    # ---- KEEP (+ un-branched check against D2's closed_loop_execute on a fresh copy)
    if "keep" in rules:
        keep, timing["keep"] = timer(branch, snapshot, lambda t: keep_targets, keep_targets, horizon)
        reference_env = copy.deepcopy(env)
        reference, timing["keep_unbranched_check"] = timer(
            closed_loop_execute, reference_env, sites, max_steps=horizon)
        joined = pre_cov + keep["coverage_backhauled"]
        if (reference["series"]["coverage_backhauled"] != joined
                or reference["series"]["contract_reward"] != prefix["contract_reward"] + keep["contract_reward"]
                or reference["target_permutation"] != perm0.tolist()):
            raise AssertionError(f"world {world}: branched KEEP differs from the un-branched episode")
        finish("keep", keep_targets, keep, {"unbranched_check": "equal bit for bit"})

    # ---- cold SET-now
    if "cold" in rules:
        def cold_plan():
            relay, flat = d2_planner(snapshot, post_users, world, budget)
            layout = np.asarray(relay.positions_xyz, dtype=float)
            return relay, flat, layout[assign_targets(positions_te, layout)]
        (relay_c, flat_c, cold_targets), t_plan = timer(cold_plan)
        cold, t_roll = timer(branch, snapshot, lambda t: keep_targets if t < t_e else cold_targets,
                             cold_targets, horizon)
        timing["cold"] = {"plan": t_plan, "rollout": t_roll}
        finish("cold", cold_targets, cold, {
            "static_contract_reward": relay_c.contract_reward,
            "static_coverage_backhauled": relay_c.coverage_backhauled,
            "evaluations": [int(flat_c.evaluations), int(relay_c.evaluations)],
            "budget_per_search": int(budget)})

    # ---- warm SET (held re-placement)
    if "warm" in rules:
        centre = np.asarray(post_users[np.asarray(event["members"])], dtype=float).mean(axis=0)
        warm_rec, t_plan = timer(warm_rule, snapshot, post_users, keep_targets, positions_te,
                                 facts_actual, centre, budget)
        warm_targets = warm_rec.pop("targets")
        warm, t_roll = timer(branch, snapshot, lambda t: keep_targets if t < t_e else warm_targets,
                             warm_targets, horizon)
        timing["warm"] = {"plan": t_plan, "rollout": t_roll}
        finish("warm", warm_targets, warm, {**warm_rec, "new_centre_member_mean_xy": centre.tolist(),
                                            "budget": int(budget),
                                            "fallback_candidate_budget": FALLBACK_CANDIDATE_BUDGET})

    # ---- seeded (cold search seeded with the pre-event layout; all UAVs may move)
    if "seeded" in rules:
        def seeded_plan():
            before = state_fingerprint(snapshot)
            result = search_placement(shadow_host(snapshot, post_users), True, int(budget),
                                      np.random.default_rng(world), extra_candidates=[sites],
                                      extra_kind="pre_event_layout_incumbent")
            assert_unchanged(snapshot, before, "seeded search")
            layout = np.asarray(result.positions_xyz, dtype=float)
            return result, layout[assign_targets(positions_te, layout)]
        (seeded_res, seeded_targets), t_plan = timer(seeded_plan)
        seeded, t_roll = timer(branch, snapshot, lambda t: keep_targets if t < t_e else seeded_targets,
                               seeded_targets, horizon)
        timing["seeded"] = {"plan": t_plan, "rollout": t_roll}
        finish("seeded", seeded_targets, seeded, {
            "static_contract_reward": seeded_res.contract_reward,
            "static_coverage_backhauled": seeded_res.coverage_backhauled,
            "evaluations": int(seeded_res.evaluations), "budget": int(budget),
            "best_start_kind": seeded_res.best_start["kind"]})

    assert_unchanged(snapshot, snap_fp, "the rules")
    record["stakes"] = stakes(record["rules"])
    record["timing"] = timing
    return record


def stakes(rules: dict[str, Any]) -> dict[str, float | None]:
    """Per-world stakes on the post-event window scale."""
    post = {name: rules[name]["post_event_mean"] for name in rules}
    out: dict[str, float | None] = {
        "S_switch": post["warm"] - post["keep"] if {"warm", "keep"} <= set(post) else None,
        "S_cold": post["warm"] - post["cold"] if {"warm", "cold"} <= set(post) else None,
        "S_seeded": post["seeded"] - post["keep"] if {"seeded", "keep"} <= set(post) else None,
    }
    return out


# ------------------------------------------------------------------------------ grid


def grid_entries(n_uavs: int = 6, delays: tuple[int, ...] = GRID_DELAYS):
    """(mask, subset, delay) in enumeration order: mask ascending, then the delays in order."""
    for mask in range(2 ** n_uavs):
        subset = [u for u in range(n_uavs) if mask >> u & 1]
        for delay in delays:
            yield mask, subset, int(delay)


def run_grid(env: EventCoupledRelayHost, world_record: dict[str, Any],
             delays: tuple[int, ...] = GRID_DELAYS, dedupe: bool = True) -> dict[str, Any]:
    """The departure small grid over an existing warm result (``world_record`` from ``run_world``)."""
    world = int(world_record["world"])
    horizon = int(world_record["horizon"])
    keep_targets = np.asarray(world_record["pre_event"]["keep_targets_xyz"], dtype=float)
    warm = world_record["rules"]["warm"]
    warm_targets = np.asarray(warm["targets_xyz"], dtype=float)
    prefix, snapshot = prefix_and_snapshot(env, keep_targets, world, horizon)
    t_e = int(snapshot.current_step)
    if t_e != int(world_record["t_e"]) or prefix["coverage_backhauled"] != world_record["pre_event"]["coverage_backhauled"]:
        raise AssertionError(f"world {world}: the re-run prefix differs from the input run")
    pre_cov = prefix["coverage_backhauled"]
    changed = [u for u in range(env.n_uavs) if not np.array_equal(warm_targets[u], keep_targets[u])]
    cache: dict[Any, dict[str, Any]] = {}
    table = []
    for mask, subset, delay in grid_entries(env.n_uavs, delays):
        effective = tuple(u for u in subset if u in changed)
        key = (effective, delay if effective else None) if dedupe else (mask, delay)
        if key not in cache:
            switched = keep_targets.copy()
            switched[list(effective)] = warm_targets[list(effective)]
            start = t_e + delay

            def targets_fn(t, start=start, switched=switched):
                return switched if t >= start else keep_targets
            final = switched if start < horizon else keep_targets
            result = branch(snapshot, targets_fn, final, horizon)
            cache[key] = {**window_metrics(pre_cov, result["coverage_backhauled"]),
                          "arrival_step": result["arrival_step"],
                          "_series": result["coverage_backhauled"]}
        entry = cache[key]
        table.append({"mask": mask, "subset": subset, "delay": delay,
                      "post_event_mean": entry["post_event_mean"],
                      "all_mean": entry["all_mean"],
                      "transition_loss_steps": entry["transition_loss_steps"],
                      "arrival_step": entry["arrival_step"]})
    full = 2 ** env.n_uavs - 1
    all_zero = cache[((tuple(changed), 0 if changed else None) if dedupe else (full, 0))]
    if all_zero["_series"] != warm["post_event_coverage_backhauled"]:
        raise AssertionError(f"world {world}: all-depart delay-0 grid entry differs from warm SET")
    if "keep" in world_record["rules"]:
        for delay in delays:
            empty = cache[(((), None) if dedupe else (0, delay))]
            if empty["_series"] != world_record["rules"]["keep"]["post_event_coverage_backhauled"]:
                raise AssertionError(f"world {world}: empty-subset grid entry differs from KEEP")
    best = max(range(len(table)), key=lambda i: (table[i]["post_event_mean"], -i))
    ordinary = {name: world_record["rules"][name]["post_event_mean"]
                for name in RULES if name in world_record["rules"]}
    best_ordinary = max(ordinary.values())
    return {
        "world": world, "t_e": t_e, "grid_delays": list(delays), "entries": len(table),
        "unique_rollouts": len(cache), "changed_uavs": changed,
        "best": {**table[best], "index": int(best)},
        "table": table,
        "identities": {"all_depart_delay0_equals_warm": True,
                       "empty_subset_equals_keep": "keep" in world_record["rules"]},
        "ordinary_post_event_means": ordinary,
        "room": float(table[best]["post_event_mean"] - best_ordinary),
        "room_definition": "grid best post-event C_bh - max(post-event C_bh of the ordinary rules "
                           "present in the input run)",
    }

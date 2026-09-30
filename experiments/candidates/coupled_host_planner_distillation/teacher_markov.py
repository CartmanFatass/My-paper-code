"""Markov teacher T_M (coupled_host_planner_distillation, cell b01 piece 2, zero fit).

Authority: ``docs/research/candidates/coupled_host_planner_distillation/NOTES.md``, entry
"REVISED PRE-DECLARATION" (commit d62bb0bb1), items 2-7 and 10, and the piece-2 L0 scope note.

T_M is a function of the student's inputs (the pooled known map and the six UAV positions):

1. pooling: every host step (every ``rules.rollout`` call of ``targets``) the six UAVs'
   ``_get_local_users`` views enter the team map (``B4.team_sightings``, the only reader of user
   positions; latest xy per user); once more at the terminal state (no decision);
2. decisions only at ``t % MACRO_K == 0`` (state after call ``t - 1``), held for 10 host steps by
   piece 1's ``macro_hold`` (bit-identical hold semantics);
3. at a decision: fewer than ``B4.MIN_KNOWN_FOR_SEARCH`` (6) known users -> every target is the
   UAV's spawn position (hold).  Else, if the known SET (frozenset of user ids) differs from the
   set of the last plan (or no plan exists yet) -> ``layout = B4.plan_on_known(env, known_xy,
   seed, budget)`` with the CONSTANT planner seed ``seed`` (the planner's ``world`` argument is
   only its RNG seed; the world id is never passed), cached by the known set.  Else (set
   unchanged) the cached layout is reused.  Either way the UAV-indexed targets are
   ``layout[B4.assign_targets(current positions, layout)]`` -- re-assignment at every decision
   (critic item 7 / L0 scope); ``assignment_changed`` records whether the permutation differs
   from the previous decision's on the same layout.  No planner-call cap (none is declared for
   T_M).
4. labelled decisions: at every re-plan, {step, known set, 168 shared features, positions,
   layouts for ``label_seeds``}; the control seed's layout is the first entry and is the one used
   for control (not recomputed); the other seeds are planned on the same known xy in the same
   decision (their CPU is kept apart from the control planner CPU).

Every planner call (``B4.plan_on_known`` / ``B4.assign_targets`` / ``B4.team_sightings``) goes
through the module attribute so tests can monkeypatch them.
"""

from __future__ import annotations

import time
from typing import Any, Sequence

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import MACRO_K, N_UAVS
from experiments.candidates.coupled_host_planner_distillation import teacher as T
from experiments.candidates.coupled_host_replan_timing.rules import PLANNER_BUDGET, rollout

HORIZON = T.HORIZON
SHARED_FEATURE_DIM = T.FEATURE_DIM - N_UAVS          # 168: the 174-float encoding without ego
CONTROL_SEED = 0
POOLING = ("every host step (every rollout call of targets_fn) and once at the terminal state: "
           "the union of all six UAVs' env._get_local_users views enters the team map "
           "(latest xy per user)")
TRIGGER = ("re-plan iff the pooled known set (frozenset of user ids) differs from the set of the "
           "last plan (or no plan exists yet) and >= 6 users are known; layout cached by the "
           "known set; targets = layout[assign_targets(current positions, layout)] at every "
           "decision")
HOLD_RULE = ("targets decided at t % 10 == 0 are held for 10 host steps; while fewer than 6 users "
             "are known every UAV's target is its spawn position")
ASSIGNMENT_CHANGED = ("on a cache-hit decision: the assign_targets permutation differs from the "
                      "previous decision's permutation (same cached layout); None on re-plan and "
                      "hold decisions")


def features_shared(team_map: "B4.TeamMap", uav_positions_xyz: np.ndarray) -> np.ndarray:
    """The student's shared input: ``teacher.features`` without the ego one-hot (168 floats)."""
    return T.features(team_map, uav_positions_xyz, 0)[:SHARED_FEATURE_DIM]


class TeacherMarkov:
    """T_M; ``targets`` is ``rules.rollout``'s ``targets_fn`` (pools every call)."""

    def __init__(self, env, world: int, budget: int = PLANNER_BUDGET, seed: int = CONTROL_SEED,
                 trigger: str = "known_set", label_seeds: Sequence[int] | None = None,
                 record: bool = True, macro_k: int = MACRO_K) -> None:
        if int(env.current_step) != 0:
            raise AssertionError("T_M starts at the reset state")
        if trigger != "known_set":
            raise ValueError(f"unknown trigger {trigger!r} (only 'known_set' is declared)")
        self.env, self.world, self.budget, self.seed = env, int(world), int(budget), int(seed)
        if label_seeds is None:
            label_seeds = (self.seed,)
        self.label_seeds = tuple(int(s) for s in label_seeds)
        if not self.label_seeds or self.label_seeds[0] != self.seed:
            raise ValueError("label_seeds must start with the control seed")
        if len(set(self.label_seeds)) != len(self.label_seeds):
            raise ValueError("label_seeds must be distinct")
        self.trigger, self.record_labels, self.macro_k = trigger, bool(record), int(macro_k)
        self.spawn = np.array(env.uav_positions, dtype=float, copy=True)
        self.map = B4.TeamMap()
        self.cache: dict[frozenset, np.ndarray] = {}
        self.plan_set: frozenset | None = None
        self.layout: np.ndarray | None = None
        self.perm: np.ndarray | None = None
        self.plans: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.labelled: list[dict[str, Any]] = []
        self.evaluations = 0
        self.hold_steps = 0
        self.observe_calls = 0
        self.cpu = {"planner_s": 0.0, "label_planner_s": 0.0, "assign_s": 0.0}
        self._held = T.macro_hold(self.decide, self.macro_k)

    # ---------------------------------------------------------------- per host step

    def _observe(self, step: int) -> None:
        sightings, _views = B4.team_sightings(self.env)
        self.map.update(sightings, step)
        self.observe_calls += 1

    def targets(self, t: int) -> np.ndarray:
        t = int(t)
        self._observe(t)
        out = self._held(t)
        if self.layout is None:
            self.hold_steps += 1
        return out

    # ---------------------------------------------------------------- decisions

    def decide(self, t: int) -> np.ndarray:
        """One decision at the state after call ``t - 1`` (pooled through call ``t``'s observe)."""
        t = int(t)
        if t % self.macro_k:
            raise AssertionError(f"decision at step {t} is not a macro boundary")
        positions = np.array(self.env.uav_positions, dtype=float, copy=True)
        known = frozenset(self.map.latest)
        entry: dict[str, Any] = {"step": t, "n_known": len(known), "hold": False, "replanned": False,
                                 "cache_hit": False, "assignment_changed": None, "evaluations": 0}
        if len(known) < B4.MIN_KNOWN_FOR_SEARCH:
            if self.layout is not None:                     # the map never shrinks
                raise AssertionError("known set shrank below 6 after a plan")
            entry["hold"] = True
            targets = self.spawn.copy()
        else:
            if self.plan_set is None or known != self.plan_set:
                entry["evaluations"] = self._plan(t, known, positions)
                entry["replanned"] = True
            else:
                entry["cache_hit"] = True
            c0 = time.process_time()
            perm = np.asarray(B4.assign_targets(positions, self.layout), dtype=int)
            self.cpu["assign_s"] += time.process_time() - c0
            if entry["cache_hit"]:
                entry["assignment_changed"] = bool(not np.array_equal(perm, self.perm))
            self.perm = perm
            targets = np.array(self.layout[perm], dtype=float, copy=True)
            if entry["replanned"] and self.record_labels:
                self.labelled[-1]["targets"] = targets.copy()
        entry["targets"] = targets.copy()
        self.decisions.append(entry)
        return targets

    def _plan(self, t: int, known: frozenset, positions: np.ndarray) -> int:
        users, xy = self.map.users_xy()
        if frozenset(users) != known:
            raise AssertionError("known set and map users disagree")
        if known in self.cache:                              # the map only grows: a set never recurs
            raise AssertionError("a previously planned known set recurred")
        layouts: list[np.ndarray] = []
        used = 0
        for k, seed in enumerate(self.label_seeds):
            c0 = time.process_time()
            relay, flat = B4.plan_on_known(self.env, xy, seed, self.budget)
            dt = time.process_time() - c0
            layout = np.array(relay.positions_xyz, dtype=float, copy=True).reshape(N_UAVS, 3)
            layouts.append(layout)
            evaluations = int(flat.evaluations) + int(relay.evaluations)
            if k == 0:
                self.cpu["planner_s"] += dt
                used = evaluations
                control = {"evaluations": evaluations, "planner_cpu_s": dt,
                           "static_contract_reward_on_known": float(relay.contract_reward)}
            else:
                self.cpu["label_planner_s"] += dt
        self.evaluations += used
        self.layout, self.plan_set = layouts[0], known
        self.cache[known] = layouts[0]
        self.plans.append({"decision_step": t, "n_known": len(users), **control})
        if self.record_labels:
            self.labelled.append({
                "step": t, "known": sorted(int(u) for u in users),
                "features": features_shared(self.map, positions),
                "positions": positions.copy(),
                "seeds": list(self.label_seeds),
                "layouts": np.stack(layouts)})
        return used

    def finish(self, t_end: int) -> None:
        """Pool the terminal state (no decision)."""
        self._observe(int(t_end))

    def record(self) -> dict[str, Any]:
        cache_hits = sum(d["cache_hit"] for d in self.decisions)
        return {
            "seed": self.seed, "label_seeds": list(self.label_seeds), "trigger": self.trigger,
            "planner_calls": len(self.plans), "plan_steps": [p["decision_step"] for p in self.plans],
            "plans": self.plans, "evaluations_used": int(self.evaluations),
            "cache_hits": int(cache_hits),
            "assignment_changes": int(sum(bool(d["assignment_changed"]) for d in self.decisions)),
            "hold_decisions": int(sum(d["hold"] for d in self.decisions)),
            "hold_steps": int(self.hold_steps), "users_known_terminal": len(self.map.latest),
            "decisions": len(self.decisions), "labelled_decisions": len(self.labelled),
            "observe_calls": int(self.observe_calls),
        }


def run_markov(env, world: int, budget: int = PLANNER_BUDGET, seed: int = CONTROL_SEED,
               horizon: int = HORIZON, label_seeds: Sequence[int] | None = None,
               record: bool = True) -> tuple[dict[str, Any], TeacherMarkov]:
    """T_M closed loop on a freshly reset host (not reset here); returns (rollout, teacher)."""
    teacher = TeacherMarkov(env, world, budget, seed=seed, label_seeds=label_seeds, record=record)
    result = rollout(env, teacher.targets, 0, int(horizon))
    teacher.finish(result["t_end"])
    return result, teacher


def run_markov_episode(world: int, budget: int = PLANNER_BUDGET, seed: int = CONTROL_SEED,
                       horizon: int = HORIZON, label_seeds: Sequence[int] | None = None,
                       record: bool = True, replay_check: bool = True) -> dict[str, Any]:
    """T_M on a fresh static host (``B4.make_static_host``, ``reset(seed=world)``).

    ``world`` selects the host only; the planner seed is ``seed``.  Returns the all-500 / final-100
    C_bh, the per-decision record, labelled decisions (seed layouts [K, 6, 3]), the CPU split
    (control planner / label planners / assignment / rest) and the replay check: the recorded
    per-decision targets replayed alone on a second fresh host must reproduce the C_bh and reward
    series bit for bit.
    """
    world = int(world)
    env = B4.make_static_host(world)
    env.reset(seed=world)
    T.check_host_constants(env)
    users0 = np.array(env.user_positions, dtype=float, copy=True)
    c0 = time.process_time()
    result, teacher = run_markov(env, world, budget, seed, horizon, label_seeds, record)
    cpu_total = time.process_time() - c0
    B4.assert_static(env, users0, "T_M")
    if result["t_end"] != int(horizon):
        raise AssertionError("T_M rollout ended early")
    targets = np.stack([d["targets"] for d in teacher.decisions])
    if targets.shape != (int(horizon) // MACRO_K, N_UAVS, 3):
        raise AssertionError(f"targets shape {targets.shape}")
    replay = None
    if replay_check:
        env_r = B4.make_static_host(world)
        env_r.reset(seed=world)
        rep = T.replay_labels(env_r, targets, horizon)
        replay = {"series_identical": rep["coverage_backhauled"] == result["coverage_backhauled"],
                  "contract_reward_identical": rep["contract_reward"] == result["contract_reward"]}
        if not (replay["series_identical"] and replay["contract_reward_identical"]):
            raise AssertionError(f"world {world}: target replay differs from the T_M closed loop")
    means = B4.series_means(result["coverage_backhauled"])
    layouts = (np.concatenate([l["layouts"].reshape(-1, 3) for l in teacher.labelled])
               if teacher.labelled else np.zeros((0, 3)))
    cpu = dict(teacher.cpu)
    return {
        "world": world, "horizon": int(horizon), "budget": int(budget), "seed": int(seed),
        "label_seeds": list(teacher.label_seeds),
        "all_mean": means["all_mean"], "final_100_mean": means["final_100_mean"],
        "coverage_backhauled": result["coverage_backhauled"],
        "decisions": teacher.decisions, "targets": targets, "labelled": teacher.labelled,
        "teacher": teacher.record(),
        "layout_box_faces": T.box_face_counts(layouts),
        "layouts_z_all_50": bool(layouts.size and np.all(layouts[:, 2] == T.Z_LOW_M)),
        "replay": replay,
        "cpu_s": {"planner": cpu["planner_s"], "label_planner": cpu["label_planner_s"],
                  "assign": cpu["assign_s"],
                  "rest": cpu_total - cpu["planner_s"] - cpu["label_planner_s"] - cpu["assign_s"],
                  "total": cpu_total},
    }

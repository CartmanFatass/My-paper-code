"""Teacher T_10 (coupled_host_planner_distillation, cell b01 piece 1, zero fit).

Authority: ``docs/research/candidates/coupled_host_planner_distillation/NOTES.md``, entry
"PRE-DECLARATION" (commit 1c443afa9), and the b01 L0 scope note.

T_10 is arm B0 of ``coupled_host_joint_skills_stage1.b04_lawful_sensing`` expressed at the macro
interface (``adapter.MACRO_K`` = 10 host steps per macro decision, 50 decisions per 500-step
episode).  Reused, not rewritten: ``B4.team_sightings`` (the only reader of user positions),
``B4.TeamMap``, ``B4.plan_on_known`` (D2's two-search cold procedure on the known users only),
``B4.assign_targets``, ``B4.make_static_host`` and ``rules.rollout`` (the straight-line executor).
The three B4 functions are called through the module attribute so that tests can monkeypatch them
exactly as ``test_b04_lawful_sensing`` does.

Rule at the decision for call ``t`` with ``t % MACRO_K == 0`` (state after call ``t - 1``):

1. pool: the six UAVs' ``_get_local_users`` views enter the team map (latest xy per user).
   Pooling happens at macro decisions only (the L0 scope), not at every host step as in B0;
2. trigger: if >= ``B4.TRIGGER_NEW_KNOWN`` users are in the map but not in the last planned map,
   plan (``B4.plan_on_known``, budget per search, ``default_rng(world)``) unless ``max_replans``
   planner calls were already made (then the trigger is recorded as a cap hit);
3. the targets are the plan's sites matched to the UAVs' current positions by
   ``B4.assign_targets`` (UAV-indexed); before the first plan every UAV's target is its spawn
   position;
4. the targets are held for the next ``MACRO_K`` host steps.

Macro hold.  ``rollout(env, teacher.targets, 0, horizon)`` with ``targets(t)`` returning the same
array for every ``t`` in ``[10 m, 10 m + 9]`` is an exact macro hold: ``rules.rollout``'s
``planner.straight_line_actions`` performs the same arithmetic in the same order as the macro
adapter's ``goto_actions`` (``MacroContractAdapter.step_targets`` re-applies the go-to rule each
host step toward the held targets), so no separate hold loop is needed.  The replay check
(``replay_labels``) re-runs a fresh host on the recorded labels alone and must reproduce the
teacher's C_bh series bit for bit.

Student features (``features``): 174 floats per UAV, see its docstring.  Labels are the held
targets in box coordinates (metres), 6 x 3 per decision.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import MACRO_K, N_UAVS, N_USERS
from experiments.candidates.coupled_host_replan_timing.rules import PLANNER_BUDGET, rollout

DIRECTION = "coupled_host_planner_distillation"
HORIZON = 500
N_DECISIONS = HORIZON // MACRO_K            # 50
AREA_M = 5000.0                              # feature normalisation (asserted against the host)
Z_LOW_M, Z_SPAN_M = 50.0, 100.0              # host height_range (50, 150)
USER_BLOCK = 3                               # [known flag, x / 5000, y / 5000]
UAV_BLOCK = 3                                # [x / 5000, y / 5000, (z - 50) / 100]
FEATURE_DIM = N_USERS * USER_BLOCK + N_UAVS * UAV_BLOCK + N_UAVS   # 150 + 18 + 6 = 174
BOX_FACE_TOL_M = 1e-9
POOLING = ("at macro decisions only (t % 10 == 0, and once at the terminal state): the union of "
           "all six UAVs' env._get_local_users views enters the team map (latest xy per user); "
           "B0 pooled at every host step")
HOLD_RULE = ("targets decided at t % 10 == 0 are held for 10 host steps; before the first plan "
             "every UAV's target is its spawn position")


# ============================================================ student features


def features(team_map: "B4.TeamMap", uav_positions_xyz: np.ndarray, ego: int) -> np.ndarray:
    """Student input for UAV ``ego``: a float64 vector of ``FEATURE_DIM`` = 174.

    * ``[0, 150)``: 50 users in index order, ``[known, x / 5000, y / 5000]``; a user in the team
      map has ``known = 1`` and its latest sighted xy; an unknown user is ``[0, 0, 0]``.
    * ``[150, 168)``: the six UAVs in index order, ``[x / 5000, y / 5000, (z - 50) / 100]``
      (true positions: the team's own state).
    * ``[168, 174)``: one-hot of ``ego``.

    Pure: reads ``team_map.latest`` and the given positions only; never touches a host.
    """
    uav = np.asarray(uav_positions_xyz, dtype=np.float64).reshape(-1, 3)
    if uav.shape != (N_UAVS, 3):
        raise ValueError(f"uav_positions_xyz must be ({N_UAVS}, 3), got {uav.shape}")
    ego = int(ego)
    if not 0 <= ego < N_UAVS:
        raise ValueError(f"ego must lie in [0, {N_UAVS})")
    out = np.zeros(FEATURE_DIM, dtype=np.float64)
    for user, (_step, x, y) in team_map.latest.items():
        user = int(user)
        if not 0 <= user < N_USERS:
            raise ValueError(f"user index {user} outside [0, {N_USERS})")
        base = user * USER_BLOCK
        out[base] = 1.0
        out[base + 1] = float(x) / AREA_M
        out[base + 2] = float(y) / AREA_M
    base = N_USERS * USER_BLOCK
    block = np.column_stack([uav[:, 0] / AREA_M, uav[:, 1] / AREA_M, (uav[:, 2] - Z_LOW_M) / Z_SPAN_M])
    out[base: base + N_UAVS * UAV_BLOCK] = block.reshape(-1)
    out[base + N_UAVS * UAV_BLOCK + ego] = 1.0
    return out


def team_features(team_map: "B4.TeamMap", uav_positions_xyz: np.ndarray) -> np.ndarray:
    """``features`` for every ego: (6, 174)."""
    return np.stack([features(team_map, uav_positions_xyz, ego) for ego in range(N_UAVS)])


def box_face_counts(labels_xyz: np.ndarray, area: float = AREA_M,
                    height_range: tuple[float, float] = (Z_LOW_M, Z_LOW_M + Z_SPAN_M)) -> dict[str, int]:
    """Label components lying on each face of the target box (the tanh pre-image is infinite there)."""
    labels = np.asarray(labels_xyz, dtype=np.float64).reshape(-1, 3)
    faces = {"x_low": (0, 0.0), "x_high": (0, area), "y_low": (1, 0.0), "y_high": (1, area),
             "z_low": (2, float(height_range[0])), "z_high": (2, float(height_range[1]))}
    out = {name: int(np.sum(np.abs(labels[:, axis] - value) <= BOX_FACE_TOL_M))
           for name, (axis, value) in faces.items()}
    out["labels"] = int(labels.shape[0])
    out["labels_on_any_face"] = int(np.sum(np.any(
        [np.abs(labels[:, axis] - value) <= BOX_FACE_TOL_M for axis, value in faces.values()], axis=0)))
    return out


# ============================================================ macro hold


def macro_hold(decide: Callable[[int], np.ndarray], macro_k: int = MACRO_K) -> Callable[[int], np.ndarray]:
    """``rollout`` targets_fn: ``decide(t)`` is called only at ``t % macro_k == 0``; held otherwise."""
    held: dict[str, Any] = {"targets": None, "t": None}

    def targets_fn(t: int) -> np.ndarray:
        t = int(t)
        if t % macro_k == 0:
            held["targets"] = np.array(decide(t), dtype=np.float64, copy=True).reshape(N_UAVS, 3)
            held["t"] = t
        elif held["targets"] is None or t - held["t"] >= macro_k:
            raise AssertionError(f"step {t}: no macro decision holds (last at {held['t']})")
        return held["targets"]

    return targets_fn


# ============================================================ teacher


class TeacherT10:
    """B0's procedure at the macro interface; ``targets`` is ``rollout``'s ``targets_fn``."""

    def __init__(self, env, world: int, budget: int = PLANNER_BUDGET,
                 max_replans: int = B4.MAX_REPLANS, record: bool = True,
                 macro_k: int = MACRO_K) -> None:
        if int(env.current_step) != 0:
            raise AssertionError("T_10 starts at the reset state")
        if int(max_replans) < 1:
            raise ValueError("max_replans must be >= 1")
        self.env, self.world, self.budget = env, int(world), int(budget)
        self.max_replans, self.record_features, self.macro_k = int(max_replans), bool(record), int(macro_k)
        self.spawn = np.array(env.uav_positions, dtype=float, copy=True)
        self.current = self.spawn.copy()
        self.map = B4.TeamMap()
        self.planned: set[int] = set()
        self.plans: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.cap_hit_steps: list[int] = []
        self.evaluations = 0
        self.cpu = {"planner_s": 0.0, "assign_s": 0.0}
        self.targets = macro_hold(self.decide, self.macro_k)

    def _observe(self, step: int) -> list[int]:
        sightings, _views = B4.team_sightings(self.env)
        return self.map.update(sightings, step)

    def decide(self, t: int) -> np.ndarray:
        """One macro decision at the state after call ``t - 1``; returns the UAV-indexed targets."""
        t = int(t)
        if t % self.macro_k:
            raise AssertionError(f"decision at step {t} is not a macro boundary")
        self._observe(t)
        positions = np.array(self.env.uav_positions, dtype=float, copy=True)
        new = sorted(set(self.map.latest) - self.planned)
        planned = cap_hit = False
        evaluations = 0
        if len(new) >= B4.TRIGGER_NEW_KNOWN:
            if len(self.plans) < self.max_replans:
                evaluations = self._plan(t, new, positions)
                planned = True
            else:
                cap_hit = True
                self.cap_hit_steps.append(t)
        entry: dict[str, Any] = {
            "step": t, "n_known": len(self.map.latest), "newly_known_since_plan": len(new),
            "planned": planned, "cap_hit": cap_hit, "evaluations": int(evaluations),
            "planner_calls": len(self.plans), "targets": self.current.copy()}
        if self.record_features:
            entry["features"] = team_features(self.map, positions)
        self.decisions.append(entry)
        return self.current

    def _plan(self, t: int, new: list[int], positions: np.ndarray) -> int:
        users, xy = self.map.users_xy()
        c0 = time.process_time()
        relay, flat = B4.plan_on_known(self.env, xy, self.world, self.budget)
        c1 = time.process_time()
        layout = np.asarray(relay.positions_xyz, dtype=float)
        self.current = layout[B4.assign_targets(positions, layout)]
        c2 = time.process_time()
        self.cpu["planner_s"] += c1 - c0
        self.cpu["assign_s"] += c2 - c1
        used = int(flat.evaluations) + int(relay.evaluations)
        self.evaluations += used
        self.planned = set(users)
        self.plans.append({"decision_step": t, "n_known": len(users), "newly_known": len(new),
                           "evaluations": used, "planner_cpu_s": c1 - c0,
                           "static_contract_reward_on_known": float(relay.contract_reward),
                           "targets_xyz": self.current.tolist()})
        return used

    def finish(self, t_end: int) -> None:
        """Pool the terminal state for the horizon reading (no plan, no decision)."""
        self._observe(int(t_end))

    def record(self) -> dict[str, Any]:
        return {
            "max_replans": self.max_replans, "planner_calls": len(self.plans),
            "trigger_steps": [p["decision_step"] for p in self.plans], "plans": self.plans,
            "evaluations_used": int(self.evaluations), "cap_hit": bool(self.cap_hit_steps),
            "cap_hit_trigger_steps": len(self.cap_hit_steps),
            "hold_decisions_before_first_plan": int(sum(1 for d in self.decisions if d["planner_calls"] == 0)),
            "users_known_terminal": len(self.map.latest), "decisions": len(self.decisions),
        }


def run_teacher(env, world: int, budget: int = PLANNER_BUDGET, horizon: int = HORIZON,
                max_replans: int = B4.MAX_REPLANS, record: bool = True) -> tuple[dict[str, Any], TeacherT10]:
    """T_10 closed loop on a freshly reset host (not reset here); returns (rollout, teacher)."""
    teacher = TeacherT10(env, world, budget, max_replans=max_replans, record=record)
    result = rollout(env, teacher.targets, 0, int(horizon))
    teacher.finish(result["t_end"])
    return result, teacher


def replay_labels(env, labels: np.ndarray, horizon: int, macro_k: int = MACRO_K) -> dict[str, Any]:
    """Replay recorded per-decision targets ``labels`` [decisions, 6, 3] on a freshly reset host."""
    labels = np.asarray(labels, dtype=np.float64)
    return rollout(env, macro_hold(lambda t: labels[t // macro_k], macro_k), 0, int(horizon))


def check_host_constants(env) -> None:
    if float(env.area_size) != AREA_M or tuple(map(float, env.height_range)) != (Z_LOW_M, Z_LOW_M + Z_SPAN_M):
        raise AssertionError(f"feature constants assume area 5000 and heights (50, 150); host has "
                             f"{env.area_size}, {env.height_range}")
    if int(env.n_uavs) != N_UAVS or int(env.n_users) != N_USERS:
        raise AssertionError("feature layout assumes 6 UAVs and 50 users")


def run_teacher_episode(world: int, budget: int = PLANNER_BUDGET, horizon: int = HORIZON,
                        record: bool = True, max_replans: int = B4.MAX_REPLANS,
                        replay_check: bool = True) -> dict[str, Any]:
    """T_10 on a fresh static host (``B4.make_static_host``, ``reset(seed=world)``).

    Returns the all-500 / final-100 C_bh, the per-decision record (step, features [6, 174] when
    ``record``, targets [6, 3], planner calls, evaluations), and CPU seconds (process time) split
    into planner calls (``plan_on_known``), assignment and the rest.  With ``replay_check`` a
    second fresh host replays the labels alone and must reproduce the C_bh series exactly.
    """
    world = int(world)
    env = B4.make_static_host(world)
    env.reset(seed=world)
    check_host_constants(env)
    users0 = np.array(env.user_positions, dtype=float, copy=True)
    c0 = time.process_time()
    result, teacher = run_teacher(env, world, budget, horizon, max_replans=max_replans, record=record)
    cpu_total = time.process_time() - c0
    B4.assert_static(env, users0, "T_10")
    if result["t_end"] != int(horizon):
        raise AssertionError("T_10 rollout ended early")
    labels = np.stack([d["targets"] for d in teacher.decisions])
    if labels.shape != (int(horizon) // MACRO_K, N_UAVS, 3):
        raise AssertionError(f"labels shape {labels.shape}")
    replay = None
    if replay_check:
        env_r = B4.make_static_host(world)
        env_r.reset(seed=world)
        rep = replay_labels(env_r, labels, horizon)
        replay = {"series_identical": rep["coverage_backhauled"] == result["coverage_backhauled"],
                  "contract_reward_identical": rep["contract_reward"] == result["contract_reward"]}
        if not (replay["series_identical"] and replay["contract_reward_identical"]):
            raise AssertionError(f"world {world}: label replay differs from the teacher closed loop")
    means = B4.series_means(result["coverage_backhauled"])
    planner_s, assign_s = teacher.cpu["planner_s"], teacher.cpu["assign_s"]
    return {
        "world": world, "horizon": int(horizon), "budget": int(budget),
        "all_mean": means["all_mean"], "final_100_mean": means["final_100_mean"],
        "coverage_backhauled": result["coverage_backhauled"],
        "decisions": teacher.decisions, "labels": labels,
        "teacher": teacher.record(),
        "label_box_faces": box_face_counts(labels),
        "replay": replay,
        "cpu_s": {"planner": planner_s, "assign": assign_s,
                  "rest": cpu_total - planner_s - assign_s, "total": cpu_total},
    }

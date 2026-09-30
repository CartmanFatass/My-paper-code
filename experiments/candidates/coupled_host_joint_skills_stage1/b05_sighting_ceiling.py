"""Cell b05 (coupled_host_joint_skills_stage1): ceiling-first lawful-sighting measurement.
Arms B0 / L / D_100 on the static coupled host; zero fits, no learner, no search policy.

Authority: ``docs/research/candidates/coupled_host_joint_skills_stage1/NOTES.md``, entry "Cell b05 --
PRE-DECLARATION".  Reused, not rewritten: ``b04_lawful_sensing`` (static host, ``B0Arm`` with its
sightings, team map, >= 3-new trigger, cap, hold rule and planner call; ``run_world_b04`` for the
gate regression F and arm B0), ``rules.rollout`` (straight-line executor),
``planner.backhauled_users_mask`` (reader-side split only).

Arms (each on its own freshly reset static host):

* ``B0`` -- b04's arm, run by ``run_world_b04``; its all-500 ``coverage_backhauled`` series and its
  ``first_known_step`` must equal the committed b04 reference run (``check_b0_reference``, raises).
* ``L`` (``LArm``) -- B0 plus a clock re-plan on the current known map at the decisions for the
  calls in ``CLOCK_STEPS``, whether or not the trigger fired; a clock re-plan on an unchanged map
  is performed and counted.  The >= 3-new trigger stays active between clock calls.  At most one
  planner call per decision: when the trigger also holds at a clock decision, the single call is
  recorded as ``kind = "clock"`` with ``trigger_fired = True`` (``CLOCK_PLAN_RULE``).  Clock and
  trigger calls count toward the same cap ``MAX_REPLANS``; a call due at the cap is recorded
  (``cap_hits`` with its kind), not executed.
* ``D_100`` (``D100Arm``) -- L plus a one-time privileged grant at the decision for call
  ``GRANT_STEP``: the HARNESS calls ``grant_truth(arm, users_xy, step)`` with the true positions
  of all users (read from the reset host before the rollout); the arm never reads
  ``env.user_positions`` outside b04's sighting accessor.  The arm pools its lawful sightings of
  that decision first, then applies the grant (every user placed at its true xy, sighted users
  included -- users are static, so identical), then takes the clock re-plan on the full map
  (``assign_targets`` from the current UAV positions).  Later clock calls run on the full map; the
  trigger cannot fire again (no unknown user remains).  Recorded as ``privileged_grant``.

Readings (``run_world_b05``): per arm all-500 / final-100 C_bh; stakes ``c_ceil = D100 - L``,
``delta_l = L - B0``, ``f_minus_d100 = F - D100`` (F = the sealed gate value) and their final-100
versions; reader-side split flag ``f_backhauls_ge5_never_sighted`` from the gate layout (never
used by an arm).
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1 import b04_lawful_sensing as B4
from experiments.candidates.coupled_host_joint_skills_stage1.host import static_evaluate
from experiments.candidates.coupled_host_joint_skills_stage1.planner import backhauled_users_mask
from experiments.candidates.coupled_host_replan_timing.event_host import EventCoupledRelayHost
from experiments.candidates.coupled_host_replan_timing.rules import PLANNER_BUDGET, rollout

DIRECTION = B4.DIRECTION
CLOCK_STEPS = (100, 200, 300, 400)     # decisions for these calls always re-plan (arms L, D_100)
GRANT_STEP = 100                       # D_100's one-time privileged grant (first clock decision)
MAX_REPLANS = B4.MAX_REPLANS           # 20, trigger and clock calls together (unchanged from b04)
SPLIT_MIN_NEVER_SIGHTED = 5            # reader-side split: F backhauls >= 5 never-sighted users
FOCUS_WORLDS = (1008, 1011, 1029, 1031)  # DM addition: the four ~.2-.3 worlds (reading only)
ARMS = ("B0", "L", "D100")
CLOCK_PLAN_RULE = ("one planner call per decision: at a clock decision the call is kind 'clock' "
                   "(trigger_fired records whether the >= 3-new trigger also held); between clock "
                   "decisions the trigger fires kind 'trigger'; both kinds count toward the cap")
GRANT_RULE = ("D_100: at the decision for call 100 the harness grants the true xy of all users "
              "(one time; read from the reset host before the rollout); the arm pools its lawful "
              "sightings of that decision, then places every user at its true xy, then takes the "
              "call-100 clock re-plan on the full map (assign_targets from current UAV positions); "
              "the arm itself never reads env.user_positions outside the sighting accessor")
SPLIT_RULE = ("reader-side only: users backhauled (planner.backhauled_users_mask) by the gate's "
              "static P_relay layout under static_evaluate on a freshly reset host, intersected "
              "with the users absent from the b04 reference B0 first_known_step; flag = count >= 5")


# ============================================================ arms


class LArm(B4.B0Arm):
    """B0 plus clock re-plans at ``clock_steps`` (same trigger, cap, hold rule and planner call)."""

    def __init__(self, env: EventCoupledRelayHost, world: int, budget: int,
                 max_replans: int = MAX_REPLANS,
                 clock_steps: tuple[int, ...] = CLOCK_STEPS) -> None:
        super().__init__(env, world, budget, max_replans=max_replans)
        steps = tuple(int(s) for s in clock_steps)
        if not steps or sorted(set(steps)) != list(steps) or steps[0] < 0:
            raise ValueError("clock_steps must be distinct, increasing and non-negative")
        self.clock_steps = steps
        self.cap_hits: list[dict[str, Any]] = []

    def _before_decision(self, t: int) -> None:
        """Hook between pooling and the decision (D_100 applies its grant here)."""

    def targets(self, t: int) -> np.ndarray:
        t = int(t)
        self._observe(t)
        self._before_decision(t)
        if t in B4.READING_STEPS:
            self.known_at[str(t)] = self.map.known()
        new = sorted(set(self.map.latest) - self.planned)
        trigger = len(new) >= B4.TRIGGER_NEW_KNOWN
        clock = t in self.clock_steps
        if clock or trigger:
            kind = "clock" if clock else "trigger"
            if len(self.plans) < self.max_replans:
                self._plan(t, new, kind=kind, trigger_fired=trigger)
            else:
                self.cap_hit_steps.append(t)
                self.cap_hits.append({"step": t, "kind": kind, "trigger_fired": trigger})
        if not self.plans:
            self.hold_steps += 1
        return self.current

    def _plan(self, t: int, new: list[int], kind: str = "trigger",
              trigger_fired: bool = True) -> None:
        super()._plan(t, new)
        self.plans[-1]["kind"] = kind
        self.plans[-1]["trigger_fired"] = bool(trigger_fired)

    def record(self) -> dict[str, Any]:
        rec = super().record()
        kinds = [p["kind"] for p in self.plans]
        rec.update({
            "clock_steps": list(self.clock_steps),
            "plan_steps": [p["decision_step"] for p in self.plans],
            "trigger_steps": [p["decision_step"] for p in self.plans if p["kind"] == "trigger"],
            "clock_plan_steps": [p["decision_step"] for p in self.plans if p["kind"] == "clock"],
            "replans_by_kind": {"trigger": kinds.count("trigger"), "clock": kinds.count("clock")},
            "cap_hits": list(self.cap_hits),
        })
        return rec


class D100Arm(LArm):
    """L plus a one-time privileged grant of all users' true xy at ``grant_step`` (harness-fed)."""

    def __init__(self, env: EventCoupledRelayHost, world: int, budget: int,
                 max_replans: int = MAX_REPLANS, clock_steps: tuple[int, ...] = CLOCK_STEPS,
                 grant_step: int = GRANT_STEP) -> None:
        super().__init__(env, world, budget, max_replans=max_replans, clock_steps=clock_steps)
        if int(grant_step) not in self.clock_steps:
            raise ValueError("the grant step must be a clock step (the grant is followed by the "
                             "clock re-plan on the full map)")
        self.grant_step = int(grant_step)
        self._pending_grant: tuple[int, np.ndarray] | None = None
        self.grant: dict[str, Any] | None = None

    def _before_decision(self, t: int) -> None:
        if self._pending_grant is None:
            if t == self.grant_step and self.grant is None:
                raise AssertionError(f"D_100: no grant delivered at the decision for call {t}")
            return
        step, xy = self._pending_grant
        if step != t:
            raise AssertionError(f"D_100: grant for step {step} pending at decision {t}")
        self._pending_grant = None
        before = set(self.map.latest)
        moved = 0
        for user in range(xy.shape[0]):
            x, y = float(xy[user, 0]), float(xy[user, 1])
            prior = self.map.latest.get(user)
            if prior is not None and (prior[1], prior[2]) != (x, y):
                moved += 1
            self.map.latest[user] = (int(t), x, y)
        self.grant = {"step": int(t), "users": int(xy.shape[0]),
                      "newly_known": int(xy.shape[0] - len(before & set(range(xy.shape[0])))),
                      "known_before": int(len(before)),
                      "sighted_xy_differing_from_truth": int(moved)}

    def record(self) -> dict[str, Any]:
        rec = super().record()
        rec["privileged_grant"] = None if self.grant is None else dict(self.grant)
        rec["grant_rule"] = GRANT_RULE
        return rec


def grant_truth(arm: D100Arm, users_xy: np.ndarray, step: int) -> None:
    """Harness -> arm: the one-time privileged grant (the arm's only truth, applied at ``step``)."""
    if not isinstance(arm, D100Arm):
        raise TypeError("only the D_100 reference arm holds a truth grant")
    if arm.grant is not None or arm._pending_grant is not None:
        raise AssertionError("D_100's grant is one-time")
    if int(step) != arm.grant_step:
        raise AssertionError(f"grant at step {step}, declared {arm.grant_step}")
    xy = np.array(users_xy, dtype=float, copy=True).reshape(-1, 2)
    arm._pending_grant = (int(step), xy)


# ============================================================ harness (truth used for set-up/reporting)


def run_arm(env: EventCoupledRelayHost, arm_cls: type, world: int, budget: int, horizon: int,
            max_replans: int = MAX_REPLANS, users_truth: np.ndarray | None = None,
            **arm_kwargs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """One arm (L or D_100) on a freshly reset static host; ``users_truth`` feeds D_100's grant."""
    arm = arm_cls(env, world, budget, max_replans=max_replans, **arm_kwargs)
    if isinstance(arm, D100Arm):
        if users_truth is None:
            raise ValueError("D_100 needs the harness's users_truth")
        truth = np.array(users_truth, dtype=float, copy=True)

        def targets_fn(t: int) -> np.ndarray:
            if int(t) == arm.grant_step:
                grant_truth(arm, truth, int(t))
            return arm.targets(t)
    else:
        if users_truth is not None:
            raise ValueError("only D_100 receives a truth grant")
        targets_fn = arm.targets
    result = rollout(env, targets_fn, 0, int(horizon))
    arm.finish(result["t_end"])
    return result, arm.record()


def check_b0_reference(world: int, b0: dict[str, Any], reference: dict[str, Any]) -> None:
    """B0 of this run vs the committed b04 reference world record (exact; raises)."""
    ref = reference["B0"]
    checks = {
        "world": int(reference["world"]) == int(world),
        "series": list(b0["coverage_backhauled"]) == list(ref["coverage_backhauled"]),
        "all_mean": b0["all_mean"] == ref["all_mean"],
        "first_known_step": b0["first_known_step"] == ref["first_known_step"],
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise AssertionError(f"world {world}: B0 differs from the b04 reference run: {failed} "
                             f"(this run all_mean {b0['all_mean']!r}, reference {ref['all_mean']!r})")


def split_flag(world: int, gate: dict[str, Any], reference: dict[str, Any],
               area_size: int = 5000) -> dict[str, Any]:
    """Reader-side split (``SPLIT_RULE``); never seen by an arm."""
    env = B4.make_static_host(int(world), area_size)
    env.reset(seed=int(world))
    users0 = np.array(env.user_positions, dtype=float, copy=True)
    if not np.array_equal(users0, np.asarray(gate["user_positions_xy"], dtype=float)):
        raise AssertionError(f"world {world}: reset users differ from the gate record")
    layout = np.asarray(gate["static"]["P_relay"]["positions_xyz"], dtype=float)
    static_evaluate(env, layout, allow_a2a=bool(env.a2a_enabled))
    mask = backhauled_users_mask(env)
    sighted = {int(u) for u in reference["B0"]["first_known_step"]}
    never = sorted(set(range(int(env.n_users))) - sighted)
    f_never = [u for u in never if bool(mask[u])]
    return {"never_sighted_users": len(never), "f_backhauled_users": int(mask.sum()),
            "f_backhauled_never_sighted": len(f_never),
            "f_backhauls_ge5_never_sighted": len(f_never) >= SPLIT_MIN_NEVER_SIGHTED}


def compact_plans(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"kind": p.get("kind", "trigger"), "step": p["decision_step"], "n_known": p["n_known"],
             "evaluations": p["evaluations"], "trigger_fired": p.get("trigger_fired", True)}
            for p in plans]


def run_world_b05(world: int, budget: int = PLANNER_BUDGET, gate: dict[str, Any] | None = None,
                  reference_world_record: dict[str, Any] | None = None, horizon: int | None = None,
                  area_size: int = 5000, timer: Callable | None = None,
                  max_replans: int = MAX_REPLANS) -> dict[str, Any]:
    """F regression + B0 (``run_world_b04``), then L and D_100 on their own fresh static hosts."""
    if gate is None or reference_world_record is None:
        raise ValueError("b05 needs the sealed gate record and the b04 reference world record")
    timer = timer or (lambda f, *a, **k: (f(*a, **k), {}))
    world = int(world)
    b04 = B4.run_world_b04(world, budget, horizon=horizon, area_size=area_size, gate=gate,
                           timer=timer, max_replans=max_replans)
    horizon = int(b04["horizon"])
    b0 = b04["B0"]
    check_b0_reference(world, b0, reference_world_record)
    timing = dict(b04["timing"])

    arms: dict[str, dict[str, Any]] = {}
    arms["B0"] = {"all_mean": b0["all_mean"], "final_100_mean": b0["final_100_mean"],
                  "coverage_backhauled": list(b0["coverage_backhauled"]),
                  "plans": compact_plans(b0["plans"]), "replans": b0["replans"],
                  "replans_by_kind": {"trigger": b0["replans"], "clock": 0},
                  "evaluations_used": b0["evaluations_used"], "cap_hit": b0["cap_hit"],
                  "cpu_s": timing["b0"].get("cpu_s"),
                  "record": {k: v for k, v in b0.items()
                             if k not in ("coverage_backhauled", "all_mean", "final_100_mean")}}
    users0 = None
    for name, cls in (("L", LArm), ("D100", D100Arm)):
        env = B4.make_static_host(world, area_size)
        env.reset(seed=world)
        users_now = np.array(env.user_positions, dtype=float, copy=True)   # harness set-up read
        if users0 is None:
            users0 = users_now
            if not np.array_equal(users0, np.asarray(gate["user_positions_xy"], dtype=float)):
                raise AssertionError(f"world {world}: reset users differ from the gate record")
        elif not np.array_equal(users_now, users0):
            raise AssertionError("the fresh hosts differ at reset")
        truth = users_now if cls is D100Arm else None
        (result, rec), timing[name] = timer(run_arm, env, cls, world, budget, horizon,
                                            max_replans, truth)
        B4.assert_static(env, users0, name)
        if result["t_end"] != horizon:
            raise AssertionError(f"{name} rollout ended early")
        means = B4.series_means(result["coverage_backhauled"])
        known_at = rec.pop("known_users_at")
        arms[name] = {**means, "coverage_backhauled": result["coverage_backhauled"],
                      "plans": compact_plans(rec["plans"]), "replans": rec["replans"],
                      "replans_by_kind": rec["replans_by_kind"],
                      "evaluations_used": rec["evaluations_used"], "cap_hit": rec["cap_hit"],
                      "cpu_s": timing[name].get("cpu_s"),
                      "users_known": {k: len(v) for k, v in known_at.items()},
                      "record": rec}
    first_clock = min(CLOCK_STEPS)
    for a, b in (("B0", "L"), ("L", "D100")):
        if arms[a]["coverage_backhauled"][:first_clock] != arms[b]["coverage_backhauled"][:first_clock]:
            raise AssertionError(f"world {world}: {a} and {b} differ before call {first_clock}")

    F, F100 = float(b04["F"]["all_mean"]), float(b04["F"]["final_100_mean"])
    B, L, D = (arms[k]["all_mean"] for k in ARMS)
    B100, L100, D100 = (arms[k]["final_100_mean"] for k in ARMS)
    stakes = {"c_ceil": float(D - L), "delta_l": float(L - B), "f_minus_d100": float(F - D),
              "c_ceil_final100": float(D100 - L100), "delta_l_final100": float(L100 - B100),
              "f_minus_d100_final100": float(F100 - D100),
              "s_info0": b04["stakes"]["s_info0"], "s_info0_final100": b04["stakes"]["s_info0_final100"]}
    return {"world": world, "horizon": horizon, "budget": int(budget), "area_size": int(area_size),
            "F": b04["F"], "arms": arms, "stakes": stakes,
            "split": split_flag(world, gate, reference_world_record, area_size),
            "focus_world": world in FOCUS_WORLDS,
            "b0_equals_reference": True, "pre_clock_series_identical": True,
            "timing": timing}

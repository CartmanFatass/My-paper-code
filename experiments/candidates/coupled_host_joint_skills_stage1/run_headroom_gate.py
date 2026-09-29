#!/usr/bin/env python3
"""T-G: D1' zero-fit headroom gate on the coupled host (coupled_host_joint_skills_stage1).

D1' = a learned bounded offset around the closed-loop anchor ``P_relay^on``.  This runner is
the cheapest refuting run for it: no learner, no fit, ordinary search only.

Kill rule (declared in the DM's L0 before any reading):

    D1' is NOT bought  iff  mean_w H_static(w) <= 0.02 (C_bh)  AND  mean_w H_corr(w) <= 0.01.

The rule is read in exact arithmetic (DM addendum): C_bh = backhauled users / n_users, so every
H is formed from integer backhauled-user counts (``reward_info["backhauled_users"]``; the
closed-loop series' C_bh values are converted back to counts and checked to be integral),
summed over worlds (and steps) and divided once, as a ``fractions.Fraction``; no tolerance.
The correction sweep and the kill rule read one scale: backhauled users (C_bh).

Per world w (dev panel 1000-1031, area 5000 by default):

0. Reproduction (before anything else, over every requested world): ``make_host(w)``; the flat
   search then the relay search with the flat layout as incumbent, exactly as ``run_gate.py``
   (budget 3,000, ``numpy.random.default_rng(w)`` fresh per search); P_relay and P_flat
   positions, contract reward, C_bh and evaluations must equal the sealed
   ``<reference-dir>/worlds/<w>.json`` bit for bit, and the anchor's closed-loop 500-step mean
   C_bh and r (``planner.closed_loop_execute`` on the P_relay targets, host contract env) must
   equal the sealed ``closed_loop_relay`` values.  Any mismatch stops the run with exit code 4
   before any output is written.  The sha256 of each reference file is recorded.
1. ``H_static(w)`` = static r and C_bh of P_relay searched at a 10x budget (30,000
   evaluations, 6 starts, xy step schedule 100 -> 50 -> 25 -> 10 m; same rng derivation, same
   candidate list, same flat incumbent) minus the sealed P_relay at 3,000.  The schedule
   extends the reference one as a prefix and the 6 starts include the reference's top 3, so
   H_static on r is >= 0 by construction (every sealed dev search evaluated all candidates);
   H_static on C_bh can be negative (the search maximises r).  The kill rule reads C_bh
   (the backhauled-user count difference / n_users).
2. ``H_corr(w)`` = closed-loop 500-step mean C_bh of "anchor + ordinary correction" minus the
   anchor's closed-loop mean C_bh.  Executor: ``planner.retargeting_closed_loop_execute`` (the
   ``closed_loop_execute`` reset, min-makespan assignment and straight-line action rule, via
   ``planner.straight_line_actions``).  Correction (``local_target_sweep``) at every step
   t % 10 == 0 (t = 0 included, 50 decisions): on a separate evaluation host of the same world
   (``static_evaluate`` mutates its env, so it never runs on the episode env; the users are
   static and asserted equal), evaluate the current assigned targets once, then for each UAV in
   index order evaluate the 26 offsets of its target on the grid {-25, 0, +25} m x
   {-25, 0, +25} m x {-50, 0, +50} m (z step = the planner's ``Z_STEP_M``; clipped to the arena
   and height range, offsets that clip back onto the current target skipped) with the other
   UAVs at their current targets, and move that UAV's target to the best offset if it strictly
   increases the static backhauled-user count (the C_bh numerator, the kill rule's scale; ties
   -> first offset in grid order).  Feasible set (D1'): each UAV's target stays within a 300 m
   xy disc around its anchor target (the P_relay target it was assigned at t = 0) and within
   |dz| <= 50 m of the anchor height, at every decision; offsets that would leave the set are
   skipped (not evaluated).  <= 1 + 6 * 26 = 157 static evaluations per decision; the 300 cap
   is enforced.  The maximum drift from the anchor is recorded.  ``H_corr_r_diagnostic`` (the
   same difference on the contract reward r) is descriptive only.

Outputs under ``--out``: ``worlds/<w>.json`` and ``summary.json`` (per-world H values,
mean/SD/min/max, kill-rule reading, evaluations, wall/CPU seconds, reference digests, launch
sha).  Zero fits; no seed of its own (rng derivations as in ``run_gate.py``).

Admission (``scripts/hmasd_launch.py``) precedes every environment import and every output.
``--smoke-no-admission`` exists only for engineering smoke runs: it is refused unless every
world lies outside the declared dev (1000-1031) and hold-out (2000-2031) panels and ``--out``
resolves under this checkout's ``temp/``; smoke runs may shrink the budgets and point
``--reference-dir`` at a ``run_gate.py`` smoke output.  An admitted run uses the declared
budgets (3,000 / 30,000 / 6 starts).  ``--reference-dir`` is resolved against the checkout that
holds ``runs/`` (a ``--snapshot`` source worktree is mapped back to it).
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.coupled_host_joint_skills_stage1.run_gate import (  # noqa: E402
    _cpu_seconds,
    _git,
    _mean_sd,
    _panel_name,
    _smoke_refusal,
    _utc_now,
    parse_worlds,
    write_json,
)

DIRECTION = "coupled_host_joint_skills_stage1"
SCIENTIFIC_OUTPUTS = ("summary.json", "worlds")
SNAPSHOT_PARENT = "hmasd-launch-sources"
DEFAULT_REFERENCE_DIR = "runs/coupled_host_joint_skills_stage1/b01_gate_dev_a01"

DECLARED_BUDGET = 3000
DECLARED_HEADROOM_BUDGET = 30000
DECLARED_HEADROOM_STARTS = 6
HEADROOM_EXTRA_XY_STEP_M = 10.0

CORRECTION_PERIOD = 10
CORRECTION_XY_STEP_M = 25.0
CORRECTION_Z_STEP_M = 50.0  # planner.Z_STEP_M (asserted at import time in main)
CORRECTION_MAX_EVALUATIONS = 300
FEASIBLE_XY_RADIUS_M = 300.0
FEASIBLE_ABS_DZ_M = 50.0
CORRECTION_OFFSETS = tuple(
    (dx * CORRECTION_XY_STEP_M, dy * CORRECTION_XY_STEP_M, dz * CORRECTION_Z_STEP_M)
    for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
    if (dx, dy, dz) != (0, 0, 0))

KILL_H_STATIC_CBH = Fraction(2, 100)
KILL_H_CORR = Fraction(1, 100)
KILL_RULE = ("D1' NOT bought iff mean H_static (C_bh) <= 0.02 AND mean H_corr (C_bh) <= 0.01, "
             "exact rational arithmetic on backhauled-user counts")


class ReferenceMismatch(RuntimeError):
    """The existing planner call does not reproduce the sealed reference layouts."""


# ------------------------------------------------------------------------------ paths


def canonical_data_root(path: Path) -> Path:
    """Map a ``--snapshot`` source worktree (``<checkout>/.git/hmasd-launch-sources/<id>``) to the
    checkout holding ``runs/``; any other path is returned unchanged (as collect_commitments.py)."""
    path = Path(path)
    parts = path.parts
    for index in range(len(parts) - 2):
        if parts[index] == ".git" and parts[index + 1] == SNAPSHOT_PARENT:
            return Path(*parts[:index])
    return path


DATA_ROOT = canonical_data_root(ROOT)


def resolve_input(path: Path) -> Path:
    """Relative inputs resolve against the checkout holding ``runs/``; absolute paths inside a
    snapshot worktree are mapped back to that checkout."""
    path = Path(path)
    if not path.is_absolute():
        return (DATA_ROOT / path).resolve()
    parts = path.parts
    for index in range(len(parts) - 3):
        if parts[index] == ".git" and parts[index + 1] == SNAPSHOT_PARENT:
            return Path(*parts[:index], *parts[index + 3:]).resolve()
    return path.resolve()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# ------------------------------------------------------------------------------ helpers


def _timed(function, *args, **kwargs):
    cpu0 = _cpu_seconds()["total_s"]
    wall0 = time.perf_counter()
    value = function(*args, **kwargs)
    return value, {"wall_s": time.perf_counter() - wall0, "cpu_s": _cpu_seconds()["total_s"] - cpu0}


def coverage_counts(values, n_users: int) -> list[int]:
    """C_bh values (backhauled / n_users) back to integer backhauled-user counts, checked."""
    counts = []
    for value in values:
        scaled = float(value) * int(n_users)
        count = int(round(scaled))
        if abs(scaled - count) > 1e-6 or count / int(n_users) != float(value):
            raise AssertionError(f"C_bh {value!r} is not a count over {n_users} users")
        counts.append(count)
    return counts


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def kill_reading(static_count_diffs: list[int], corr_count_diff_sums: list[int], steps: list[int],
                 n_users: int) -> dict[str, Any]:
    """The kill rule in exact arithmetic.

    ``static_count_diffs[w]`` = backhauled users of the 10x layout - of the reference layout;
    ``corr_count_diff_sums[w]`` = sum over the ``steps[w]`` closed-loop steps of (corrected -
    anchor) backhauled users.  mean H_static = sum_w d_w / (W n_users); mean H_corr = (1/W)
    sum_w S_w / (T_w n_users).
    """
    worlds = len(static_count_diffs)
    if worlds == 0 or worlds != len(corr_count_diff_sums) or worlds != len(steps):
        raise ValueError("kill_reading needs one entry per world")
    mean_static = Fraction(sum(int(d) for d in static_count_diffs), worlds * int(n_users))
    mean_corr = sum((Fraction(int(s), int(t) * int(n_users))
                     for s, t in zip(corr_count_diff_sums, steps)), Fraction(0)) / worlds
    not_bought = mean_static <= KILL_H_STATIC_CBH and mean_corr <= KILL_H_CORR
    return {
        "statement": KILL_RULE,
        "H_static_cbh_threshold": fraction_text(KILL_H_STATIC_CBH),
        "H_corr_threshold": fraction_text(KILL_H_CORR),
        "mean_H_static_cbh_exact": fraction_text(mean_static),
        "mean_H_corr_exact": fraction_text(mean_corr),
        "mean_H_static_cbh": float(mean_static),
        "mean_H_corr": float(mean_corr),
        "static_condition_met": bool(mean_static <= KILL_H_STATIC_CBH),
        "corr_condition_met": bool(mean_corr <= KILL_H_CORR),
        "d1prime_not_bought": bool(not_bought),
    }


def inside_feasible_set(target, anchor) -> bool:
    """D1' feasible set: xy within FEASIBLE_XY_RADIUS_M of the anchor, |dz| <= FEASIBLE_ABS_DZ_M."""
    import numpy as np

    delta = np.asarray(target, dtype=float) - np.asarray(anchor, dtype=float)
    return bool(np.hypot(delta[0], delta[1]) <= FEASIBLE_XY_RADIUS_M
                and abs(delta[2]) <= FEASIBLE_ABS_DZ_M)


def local_target_sweep(eval_env, assigned, anchor=None,
                       max_evaluations: int = CORRECTION_MAX_EVALUATIONS):
    """One ordinary correction decision on ``eval_env`` (never the episode env).

    Evaluates the assigned targets (row i = UAV i's target) once, then per UAV in index order
    the ``CORRECTION_OFFSETS`` of its target with the others at their current targets, and
    moves it to the best offset if that strictly increases the static backhauled-user count
    (A2A on, the host contract; the C_bh numerator).  Offsets whose target would leave the D1'
    feasible set around ``anchor`` (row i = UAV i's anchor target; default: ``assigned``) are
    skipped without evaluation.  Returns (new targets, record).
    """
    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1.host import static_evaluate
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import _clip_positions

    current = np.array(assigned, dtype=float).reshape(eval_env.n_uavs, 3)
    anchor = current.copy() if anchor is None else np.array(anchor, dtype=float).reshape(current.shape)
    if not all(inside_feasible_set(current[i], anchor[i]) for i in range(eval_env.n_uavs)):
        raise ValueError("the assigned targets already lie outside the feasible set")
    worst_case = 1 + eval_env.n_uavs * len(CORRECTION_OFFSETS)
    if worst_case > int(max_evaluations):
        raise ValueError(f"sweep needs up to {worst_case} evaluations > cap {max_evaluations}")
    info = static_evaluate(eval_env, current, allow_a2a=True)
    evaluations = 1
    before = {"backhauled_users": int(info["backhauled_users"]),
              "contract_reward": float(info["contract_reward"])}
    count, reward = before["backhauled_users"], before["contract_reward"]
    moves: list[dict[str, Any]] = []
    skipped_infeasible = 0
    for uav in range(eval_env.n_uavs):
        best = None
        for offset_index, offset in enumerate(CORRECTION_OFFSETS):
            trial = current.copy()
            trial[uav] += offset
            trial = _clip_positions(eval_env, trial)
            if np.array_equal(trial, current):
                continue
            if not inside_feasible_set(trial[uav], anchor[uav]):
                skipped_infeasible += 1
                continue
            if evaluations >= int(max_evaluations):
                raise RuntimeError("correction evaluation cap reached")
            trial_info = static_evaluate(eval_env, trial, allow_a2a=True)
            evaluations += 1
            trial_count = int(trial_info["backhauled_users"])
            if best is None or trial_count > best[0]:
                best = (trial_count, float(trial_info["contract_reward"]), trial, offset_index)
        if best is not None and best[0] > count:
            count, reward, current = best[0], best[1], best[2]
            moves.append({"uav": int(uav), "offset_m": [float(v) for v in CORRECTION_OFFSETS[best[3]]],
                          "backhauled_users": count})
    drift = current - anchor
    record = {"evaluations": int(evaluations), "moves": moves,
              "skipped_infeasible": int(skipped_infeasible),
              "static_before": before,
              "static_after": {"backhauled_users": count, "contract_reward": reward},
              "max_xy_drift_m": float(np.max(np.hypot(drift[:, 0], drift[:, 1]))),
              "max_abs_dz_m": float(np.max(np.abs(drift[:, 2])))}
    return current, record


def load_reference(reference_dir: Path, world: int) -> tuple[dict[str, Any], str, Path]:
    path = reference_dir / "worlds" / f"{int(world)}.json"
    if not path.is_file():
        raise ReferenceMismatch(f"world {world}: no sealed reference {path}")
    return json.loads(path.read_text(encoding="utf-8")), file_sha256(path), path


def _compare(world: int, label: str, found: Any, sealed: Any, problems: list[str]) -> None:
    import numpy as np

    if isinstance(sealed, list):
        equal = np.array_equal(np.asarray(found, dtype=float), np.asarray(sealed, dtype=float))
    else:
        equal = found == sealed
    if not equal:
        problems.append(f"world {world}: {label} reproduced {found!r} != sealed {sealed!r}")


def reproduce_reference(world: int, area_size: int, budget: int, reference: dict[str, Any]):
    """The run_gate.py planner call for one world, checked bit for bit against ``reference``."""
    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1.host import make_host
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
        closed_loop_execute,
        search_placement,
    )

    problems: list[str] = []
    _compare(world, "world", int(reference.get("world", -1)), int(world), problems)
    _compare(world, "area_size", int(area_size), reference.get("area_size"), problems)
    _compare(world, "P_relay budget", int(budget), reference["static"]["P_relay"].get("budget"), problems)
    _compare(world, "P_flat budget", int(budget), reference["static"]["P_flat"].get("budget"), problems)
    if problems:
        raise ReferenceMismatch("; ".join(problems))
    env = make_host(world, area_size=area_size)
    initial = env.uav_positions.copy()
    flat = search_placement(env, False, budget, np.random.default_rng(world))
    relay = search_placement(env, True, budget, np.random.default_rng(world),
                             extra_candidates=[flat.positions_xyz],
                             extra_kind="flat_result_incumbent")
    _compare(world, "initial_positions_xyz", initial.tolist(), reference["initial_positions_xyz"], problems)
    for name, result in (("P_relay", relay), ("P_flat", flat)):
        sealed = reference["static"][name]
        _compare(world, f"{name}.positions_xyz", result.positions_xyz.tolist(), sealed["positions_xyz"], problems)
        for key in ("contract_reward", "coverage_backhauled", "evaluations"):
            _compare(world, f"{name}.{key}", getattr(result, key), sealed[key], problems)
    if problems:
        raise ReferenceMismatch("; ".join(problems))
    anchor = closed_loop_execute(env, relay.positions_xyz)
    sealed_cl = reference["closed_loop"]["closed_loop_relay"]
    for key in ("coverage_backhauled_mean_all", "contract_reward_mean_all"):
        _compare(world, f"closed_loop_relay.{key}", anchor[key], sealed_cl[key], problems)
    if problems:
        raise ReferenceMismatch("; ".join(problems))
    return env, flat, relay, anchor


def measure_headroom(world: int, area_size: int, env, flat, relay, anchor,
                     headroom_budget: int, headroom_starts: int) -> dict[str, Any]:
    """H_static and H_corr for one world whose reference was reproduced."""
    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1.host import make_host
    from experiments.candidates.coupled_host_joint_skills_stage1.planner import (
        XY_STEPS_M,
        retargeting_closed_loop_execute,
        search_placement,
    )

    xy_steps = tuple(XY_STEPS_M) + (HEADROOM_EXTRA_XY_STEP_M,)
    wide, t_wide = _timed(search_placement, env, True, headroom_budget, np.random.default_rng(world),
                          n_starts=headroom_starts, extra_candidates=[flat.positions_xyz],
                          extra_kind="flat_result_incumbent", xy_steps_m=xy_steps)

    eval_env = make_host(world, area_size=area_size)
    if eval_env is env:
        raise AssertionError("the correction must not evaluate on the episode env")
    decisions: list[dict[str, Any]] = []
    state: dict[str, Any] = {}

    def correction(t: int, assigned):
        if not np.array_equal(eval_env.user_positions, env.user_positions):
            raise AssertionError(f"world {world} t={t}: evaluation host users differ")
        if t == 0:
            state["anchor"] = np.array(assigned, dtype=float)  # the P_relay targets as assigned
        new, record = local_target_sweep(eval_env, assigned, anchor=state["anchor"])
        record["t"] = int(t)
        decisions.append(record)
        return new

    corrected, t_corr = _timed(retargeting_closed_loop_execute, env, relay.positions_xyz,
                               correction, CORRECTION_PERIOD)
    if not np.array_equal(eval_env.user_positions, env.user_positions):
        raise AssertionError(f"world {world}: evaluation host users differ after the episode")
    correction_evaluations = [d["evaluations"] for d in decisions]
    if max(correction_evaluations) > CORRECTION_MAX_EVALUATIONS:
        raise AssertionError("correction evaluation cap exceeded")
    if not np.array_equal(np.asarray(corrected["targets_xyz"], dtype=float)[corrected["target_permutation"]],
                          state["anchor"]):
        raise AssertionError(f"world {world}: correction anchor != executor's assigned P_relay targets")
    drift = np.asarray(corrected["final_target_drift_from_anchor_m"], dtype=float)
    max_xy_drift = max(d["max_xy_drift_m"] for d in decisions)
    max_abs_dz = max(d["max_abs_dz_m"] for d in decisions)
    if max_xy_drift > FEASIBLE_XY_RADIUS_M or max_abs_dz > FEASIBLE_ABS_DZ_M:
        raise AssertionError(f"world {world}: correction left the feasible set")

    n_users = int(env.n_users)
    wide_count, relay_count = int(wide.info["backhauled_users"]), int(relay.info["backhauled_users"])
    if coverage_counts([wide.coverage_backhauled, relay.coverage_backhauled], n_users) != [wide_count, relay_count]:
        raise AssertionError(f"world {world}: static C_bh disagrees with the backhauled-user count")
    corrected_counts = coverage_counts(corrected["series"]["coverage_backhauled"], n_users)
    anchor_counts = coverage_counts(anchor["series"]["coverage_backhauled"], n_users)
    if len(corrected_counts) != len(anchor_counts):
        raise AssertionError(f"world {world}: episode lengths differ")
    steps = len(anchor_counts)
    static_diff = wide_count - relay_count
    corr_diff_sum = sum(corrected_counts) - sum(anchor_counts)
    return {
        "H_static_cbh": float(Fraction(static_diff, n_users)),
        "H_static_cbh_exact": fraction_text(Fraction(static_diff, n_users)),
        "H_static_backhauled_user_diff": int(static_diff),
        "H_static_r": wide.contract_reward - relay.contract_reward,
        "H_corr": float(Fraction(corr_diff_sum, steps * n_users)),
        "H_corr_exact": fraction_text(Fraction(corr_diff_sum, steps * n_users)),
        "H_corr_backhauled_user_step_diff_sum": int(corr_diff_sum),
        "steps": int(steps),
        "n_users": n_users,
        "H_corr_r_diagnostic": corrected["contract_reward_mean_all"] - anchor["contract_reward_mean_all"],
        "reference_static": {"contract_reward": relay.contract_reward,
                             "coverage_backhauled": relay.coverage_backhauled,
                             "evaluations": relay.evaluations},
        "headroom_static": {"contract_reward": wide.contract_reward,
                            "coverage_backhauled": wide.coverage_backhauled,
                            "evaluations": wide.evaluations, "converged": wide.converged,
                            "positions_xyz": wide.positions_xyz.tolist(),
                            "best_start": wide.best_start, "starts": wide.starts,
                            "xy_steps_m": list(xy_steps), "budget": int(headroom_budget),
                            "n_starts": int(headroom_starts)},
        "anchor_closed_loop": {key: anchor[key] for key in (
            "coverage_backhauled_mean_all", "coverage_backhauled_mean_final100",
            "contract_reward_mean_all", "contract_reward_mean_final100", "arrival_step",
            "association_change_count", "backhaul_loss_events")},
        "corrected_closed_loop": {key: corrected[key] for key in (
            "coverage_backhauled_mean_all", "coverage_backhauled_mean_final100",
            "contract_reward_mean_all", "contract_reward_mean_final100", "arrival_step",
            "association_change_count", "backhaul_loss_events", "final_assigned_xyz",
            "final_target_drift_from_anchor_m", "final_max_distance_to_target_m",
            "target_permutation", "steps")}
        | {"series": corrected["series"]},
        "correction": {
            "decisions": decisions,
            "decision_count": len(decisions),
            "decisions_with_moves": sum(bool(d["moves"]) for d in decisions),
            "evaluations_total": int(sum(correction_evaluations)),
            "evaluations_max_per_decision": int(max(correction_evaluations)),
            "final_max_drift_m": float(drift.max()),
            "max_xy_drift_m": float(max_xy_drift),
            "max_abs_dz_m": float(max_abs_dz),
            "skipped_infeasible_total": int(sum(d["skipped_infeasible"] for d in decisions)),
        },
        "timing": {"headroom_search": t_wide, "corrected_closed_loop": t_corr},
    }


# ------------------------------------------------------------------------------ CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_headroom_gate.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--worlds", nargs="+", default=["1000-1031"],
                        help="world (reset) seeds: integers and inclusive ranges a-b")
    parser.add_argument("--area-size", type=int, default=5000)
    parser.add_argument("--budget", type=int, default=DECLARED_BUDGET,
                        help="reference budget (must equal the sealed reference's)")
    parser.add_argument("--headroom-budget", type=int, default=DECLARED_HEADROOM_BUDGET)
    parser.add_argument("--headroom-starts", type=int, default=DECLARED_HEADROOM_STARTS)
    parser.add_argument("--reference-dir", type=Path, default=Path(DEFAULT_REFERENCE_DIR),
                        help="run_gate.py output holding worlds/<w>.json; relative paths resolve "
                             "against the checkout holding runs/")
    parser.add_argument("--out", required=True, type=Path, help="output directory")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting existing scientific outputs in --out")
    parser.add_argument("--smoke-no-admission", action="store_true",
                        help="engineering smoke only: non-panel worlds and --out under temp/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        worlds = parse_worlds(args.worlds)
    except ValueError as exc:
        parser.error(str(exc))
    if args.budget < 3:
        parser.error("--budget must be >= 3")
    if args.headroom_budget < args.budget or args.headroom_starts < 3:
        parser.error("--headroom-budget must be >= --budget and --headroom-starts >= 3")
    if not args.smoke_no_admission and (
            args.budget, args.headroom_budget, args.headroom_starts) != (
            DECLARED_BUDGET, DECLARED_HEADROOM_BUDGET, DECLARED_HEADROOM_STARTS):
        parser.error("an admitted run uses the declared budgets 3000 / 30000 / 6 starts")

    if args.smoke_no_admission:
        refusal = _smoke_refusal(worlds, Path(args.out))
        if refusal:
            print(f"error: {refusal}", file=sys.stderr)
            return 2
        admission: Any = "skipped (engineering smoke: non-panel worlds, temp output)"
    else:
        # Admission precedes environment imports and any output.
        from scripts.hmasd_admission import require_admission

        admission = dict(require_admission(__file__, direction="coupled_host_joint_skills_stage1"))

    started_utc = _utc_now()
    started = time.perf_counter()

    import numpy as np

    from experiments.candidates.coupled_host_joint_skills_stage1 import planner
    from experiments.candidates.coupled_host_joint_skills_stage1.host import HOST_CONTRACT_KWARGS

    if planner.Z_STEP_M != CORRECTION_Z_STEP_M:
        raise AssertionError("CORRECTION_Z_STEP_M must equal planner.Z_STEP_M")

    out = Path(args.out)
    existing = [name for name in SCIENTIFIC_OUTPUTS if (out / name).exists()]
    if existing and not args.force:
        print(f"error: {out} already holds scientific output {existing}; pass --force",
              file=sys.stderr)
        return 2
    reference_dir = resolve_input(args.reference_dir)

    # Phase 0: reproduce every sealed reference before anything else.
    reproduced: dict[int, tuple] = {}
    reference_digests: dict[str, str] = {}
    phase0_timing: dict[int, dict[str, float]] = {}
    try:
        for world in worlds:
            reference, digest, _path = load_reference(reference_dir, world)
            reference_digests[str(world)] = digest
            value, timing = _timed(reproduce_reference, world, args.area_size, args.budget, reference)
            reproduced[world] = value
            phase0_timing[world] = timing
            del reference
            print(f"world={world} reference reproduced ({timing['wall_s']:.1f}s)", flush=True)
    except ReferenceMismatch as exc:
        print(f"error: reference not reproduced: {exc}", file=sys.stderr)
        return 4

    out.mkdir(parents=True, exist_ok=True)  # the launcher pre-creates the output root
    rows: list[dict[str, Any]] = []
    for world in worlds:
        cpu0 = _cpu_seconds()["total_s"]
        wall0 = time.perf_counter()
        env, flat, relay, anchor = reproduced[world]
        measured = measure_headroom(world, args.area_size, env, flat, relay, anchor,
                                    args.headroom_budget, args.headroom_starts)
        measured["timing"]["reproduction"] = phase0_timing[world]
        measured["timing"]["headroom_total"] = {"wall_s": time.perf_counter() - wall0,
                                                "cpu_s": _cpu_seconds()["total_s"] - cpu0}
        row = {"world": int(world), "area_size": int(args.area_size),
               "reference_sha256": reference_digests[str(world)]} | measured
        write_json(out / "worlds" / f"{int(world)}.json", row, indent=None)
        reproduced[world] = None  # release the env and search results
        rows.append(row)
        print(f"world={world} H_static(C_bh)={row['H_static_cbh']:+.4f} "
              f"H_static(r)={row['H_static_r']:+.4f} H_corr={row['H_corr']:+.4f} "
              f"evals={row['headroom_static']['evaluations']}+"
              f"{row['correction']['evaluations_total']} "
              f"wall={row['timing']['headroom_total']['wall_s']:.1f}s", flush=True)

    h_static = _mean_sd([row["H_static_cbh"] for row in rows])
    h_corr = _mean_sd([row["H_corr"] for row in rows])
    n_users_set = {row["n_users"] for row in rows}
    if len(n_users_set) != 1:
        raise AssertionError("worlds differ in n_users")
    kill = kill_reading([row["H_static_backhauled_user_diff"] for row in rows],
                        [row["H_corr_backhauled_user_step_diff_sum"] for row in rows],
                        [row["steps"] for row in rows], n_users_set.pop())
    not_bought = kill["d1prime_not_bought"]

    def timing_stats(component: str) -> dict[str, Any]:
        return {"wall_s": _mean_sd([row["timing"][component]["wall_s"] for row in rows]),
                "cpu_s": _mean_sd([row["timing"][component]["cpu_s"] for row in rows])}

    summary: dict[str, Any] = {
        "tool": "coupled_host_joint_skills_stage1.run_headroom_gate",
        "task": "T-G D1' zero-fit headroom gate",
        "direction": DIRECTION,
        "admission": admission,
        "launch_sha": (admission.get("sha") if isinstance(admission, dict) else None),
        "git_head": _git("rev-parse", "HEAD"),
        "training_fits_performed": 0,
        "worlds": worlds,
        "panel": _panel_name(worlds),
        "area_size": int(args.area_size),
        "host_contract_kwargs": HOST_CONTRACT_KWARGS,
        "reference": {
            "dir": str(reference_dir),
            "budget": int(args.budget),
            "reproduced_bit_for_bit": True,
            "checked": ["initial_positions_xyz", "P_relay/P_flat positions_xyz, contract_reward, "
                        "coverage_backhauled, evaluations",
                        "closed_loop_relay coverage_backhauled_mean_all, contract_reward_mean_all"],
            "world_sha256": reference_digests,
        },
        "rng_derivations": {
            "planner": "numpy.random.default_rng(world), fresh instance for each search "
                       "(reference flat, reference relay, headroom relay)",
            "correction": "none (deterministic sweep)",
        },
        "headroom_search": {
            "budget": int(args.headroom_budget),
            "n_starts": int(args.headroom_starts),
            "xy_steps_m": list(planner.XY_STEPS_M) + [HEADROOM_EXTRA_XY_STEP_M],
            "z_step_m": planner.Z_STEP_M,
            "extra_candidate": "the reproduced 3,000-budget P_flat layout (flat_result_incumbent)",
        },
        "correction": {
            "period_steps": CORRECTION_PERIOD,
            "xy_step_m": CORRECTION_XY_STEP_M,
            "z_step_m": CORRECTION_Z_STEP_M,
            "offsets": "3x3x3 grid minus identity, 26 per UAV, order dx, dy, dz in (-, 0, +)",
            "rule": "per UAV in index order (Gauss-Seidel): best offset by static backhauled-user "
                    "count (A2A on; the C_bh numerator, the kill rule's scale), moved iff strictly "
                    "more users than the current layout; ties -> first offset in grid order",
            "feasible_set": {"xy_radius_m": FEASIBLE_XY_RADIUS_M, "abs_dz_m": FEASIBLE_ABS_DZ_M,
                             "around": "each UAV's anchor target (P_relay target assigned at t = 0)",
                             "infeasible_offsets": "skipped, not evaluated"},
            "max_evaluations_per_decision_cap": CORRECTION_MAX_EVALUATIONS,
            "evaluation_env": "separate make_host(world) instance; users asserted equal",
            "executor": "planner.retargeting_closed_loop_execute (straight_line_actions)",
        },
        "kill_rule": kill,
        "H_static_cbh": h_static,
        "H_static_r": _mean_sd([row["H_static_r"] for row in rows]),
        "H_corr": h_corr,
        "H_corr_r_diagnostic": _mean_sd([row["H_corr_r_diagnostic"] for row in rows]),
        "per_world": [
            {"world": row["world"], "H_static_cbh": row["H_static_cbh"],
             "H_static_r": row["H_static_r"], "H_corr": row["H_corr"],
             "H_corr_r_diagnostic": row["H_corr_r_diagnostic"],
             "headroom_evaluations": row["headroom_static"]["evaluations"],
             "correction_evaluations": row["correction"]["evaluations_total"],
             "correction_decisions_with_moves": row["correction"]["decisions_with_moves"],
             "H_static_cbh_exact": row["H_static_cbh_exact"], "H_corr_exact": row["H_corr_exact"],
             "correction_max_xy_drift_m": row["correction"]["max_xy_drift_m"],
             "correction_max_abs_dz_m": row["correction"]["max_abs_dz_m"],
             "wall_s": row["timing"]["headroom_total"]["wall_s"]
             + row["timing"]["reproduction"]["wall_s"],
             "cpu_s": row["timing"]["headroom_total"]["cpu_s"]
             + row["timing"]["reproduction"]["cpu_s"]}
            for row in rows],
        "evaluations": {
            "reference_per_world": {"P_relay": _mean_sd([r["reference_static"]["evaluations"] for r in rows])},
            "headroom_search": _mean_sd([r["headroom_static"]["evaluations"] for r in rows]),
            "correction_total_per_world": _mean_sd([r["correction"]["evaluations_total"] for r in rows]),
            "correction_max_per_decision": max(r["correction"]["evaluations_max_per_decision"]
                                               for r in rows) if rows else None,
        },
        "timing_per_world": {component: timing_stats(component) for component in (
            "reproduction", "headroom_search", "corrected_closed_loop", "headroom_total")},
        "cpu_seconds": _cpu_seconds(),
        "interpreter": {"executable": sys.executable, "numpy": np.__version__},
        "arguments": sys.argv[1:] if argv is None else list(argv),
        "start_utc": started_utc,
        "end_utc": _utc_now(),
        "wall_clock_s": time.perf_counter() - started,
    }
    write_json(out / "summary.json", summary)
    print(f"mean H_static(C_bh)={kill['mean_H_static_cbh_exact']} mean H_corr={kill['mean_H_corr_exact']} "
          f"d1prime_not_bought={not_bought}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

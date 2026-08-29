"""Selection, support, paired inference, and frozen branching for ONLGR B3."""

from __future__ import annotations

import itertools
import math
from typing import Iterable, Mapping, Sequence

import numpy as np
_T_QUANTILES: dict[tuple[float, int], float] = {
    (0.975, 15): 2.1314495455597757,
    (0.95, 15): 1.7530503556925735,
}


def _student_t_ppf(probability: float, degrees_of_freedom: int) -> float:
    for (known_probability, known_degrees), quantile in _T_QUANTILES.items():
        if (
            degrees_of_freedom == known_degrees
            and math.isclose(probability, known_probability, rel_tol=0.0, abs_tol=1e-15)
        ):
            return quantile
    raise RuntimeError(
        "scipy is not installed and this frozen B3 analysis only carries the registered "
        f"t quantile for p={probability!r}, df={degrees_of_freedom!r}"
    )

from .config import BRANCHES, MATERIAL_MARGIN, ROOTS
from .host import EpisodeResult
from .policies import FixedPolicy, exposure_bin, select_best


def summarize_root(episodes: Iterable[EpisodeResult]) -> dict[str, object]:
    rows = tuple(episodes)
    if not rows:
        raise ValueError("cannot summarize an empty root")
    identities = [identity.key for row in rows for identity in row.identity_rows]
    legal = {"low": 0, "high": 0}
    event_free = {"low": 0, "high": 0}
    actions = {"low": {"KEEP": 0, "REFRESH-SAME": 0, "REBIND": 0},
               "high": {"KEEP": 0, "REFRESH-SAME": 0, "REBIND": 0}}
    for row in rows:
        prior_voluntary_event = {0: False, 1: False}
        for exposure, action, role, initial in row.legal_action_rows:
            if initial:
                continue
            label = exposure_bin(exposure)
            legal[label] += 1
            name = ("KEEP", "REFRESH-SAME", "REBIND")[action]
            actions[label][name] += 1
            # Reachability is event-free when no earlier post-startup voluntary
            # event has occurred for this episode/role.  The first-event row
            # itself is reached event-free; only subsequent rows are excluded.
            event_free[label] += int(not prior_voluntary_event[role])
            if action > 0:
                prior_voluntary_event[role] = True
    event_count = sum(actions[label][name] for label in actions for name in ("REFRESH-SAME", "REBIND"))
    legal_count = sum(legal.values())
    direct = float(np.mean([row.normalized_return for row in rows], dtype=np.float64))
    service = float(np.mean([row.service for row in rows], dtype=np.float64))
    cost = float(np.mean([row.action_cost for row in rows], dtype=np.float64))
    iid_exact = all(
        tuple(record[0] for record in row.iid_draw_records) == tuple(range(len(row.iid_draw_records)))
        and tuple(record[1] for record in row.iid_draw_records) == row.routine_boundary_ticks
        and tuple(record[2] for record in row.iid_draw_records) == row.iid_interval_draws
        for row in rows
    )
    return {
        "root": rows[0].seed,
        "policy_id": rows[0].policy_id,
        "episodes": len(rows),
        "team_ticks": sum(row.physics_ticks for row in rows),
        "direct_return": direct,
        "service": service,
        "action_cost": cost,
        "decomposition_exact": abs(direct - (service - cost)) <= 1e-12,
        "legal_rows": legal,
        "event_free_legal_rows": event_free,
        "actions": actions,
        "voluntary_non_keep_events": event_count,
        "activity": event_count / legal_count if legal_count else 0.0,
        "conditional_refresh_proportion": (
            sum(actions[label]["REFRESH-SAME"] for label in actions) / event_count if event_count else None
        ),
        "conditional_rebind_proportion": (
            sum(actions[label]["REBIND"] for label in actions) / event_count if event_count else None
        ),
        "mean_plan_tenure": sum(row.plan_age_sum for row in rows) / (2.0 * sum(row.physics_ticks for row in rows)),
        "reward_service_cost_exact": all(row.reward_service_cost_exact for row in rows),
        "identity_unique": len(identities) == len(set(identities)) and all(row.identity_unique for row in rows),
        "post_action_iid_ordering_exact": iid_exact,
        "terminal_censoring_exact": all(row.terminal_boundary_absent for row in rows),
        "exposure_range_exact": all(0 < exposure <= 32 for row in rows for exposure, *_ in row.legal_action_rows),
        "episode_identity_unique": len({(row.namespace, row.seed, row.episode_index) for row in rows}) == len(rows),
    }


def exact_paired_sign_flip_pvalue(values: Iterable[float]) -> float:
    array = np.asarray(tuple(values), dtype=np.float64)
    if array.size == 0:
        raise ValueError("sign-flip test requires values")
    observed = abs(float(array.mean()))
    exceed = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(array)):
        permuted = float(np.mean(array * np.asarray(signs, dtype=np.float64)))
        exceed += abs(permuted) >= observed - 1e-15
    return exceed / float(2 ** len(array))


def paired_summary(values: Iterable[float]) -> dict[str, object]:
    array = np.asarray(tuple(values), dtype=np.float64)
    if array.size < 2:
        raise ValueError("paired inference requires at least two roots")
    mean = float(array.mean())
    standard_error = float(array.std(ddof=1) / math.sqrt(array.size))
    two_sided = _student_t_ppf(0.975, array.size - 1) * standard_error
    one_sided = _student_t_ppf(0.95, array.size - 1) * standard_error
    return {
        "n": int(array.size),
        "mean": mean,
        "standard_error": standard_error,
        "two_sided_95_interval": {"lower": mean - two_sided, "upper": mean + two_sided},
        "one_sided_95_lower": mean - one_sided,
        "one_sided_95_upper": mean + one_sided,
        "exact_paired_sign_flip_p_value": exact_paired_sign_flip_pvalue(array),
        "leave_one_root_out_means": tuple(float(np.delete(array, index).mean()) for index in range(array.size)),
        "root_values": tuple(float(value) for value in array),
    }


def contrast_summary(
    candidate: Mapping[int, Mapping[str, object]], comparator: Mapping[int, Mapping[str, object]],
    roots: Sequence[int] = ROOTS,
) -> dict[str, object]:
    components: dict[str, object] = {}
    for key in ("direct_return", "service", "action_cost"):
        differences = [float(candidate[root][key]) - float(comparator[root][key]) for root in roots]
        components[key] = paired_summary(differences)
    root_rows = tuple({
        "root": int(root),
        "direct_return": float(candidate[root]["direct_return"]) - float(comparator[root]["direct_return"]),
        "service": float(candidate[root]["service"]) - float(comparator[root]["service"]),
        "action_cost": float(candidate[root]["action_cost"]) - float(comparator[root]["action_cost"]),
    } for root in roots)
    return {"components": components, "root_differences": root_rows}


def support_and_shell_conformance(
    candidate: Mapping[int, Mapping[str, object]],
    shell: Mapping[int, Mapping[str, object]], roots: Sequence[int] = ROOTS,
) -> dict[str, object]:
    bin_facts: dict[str, object] = {}
    bin_passes: list[bool] = []
    for label in ("low", "high"):
        legal_by_root = {root: int(candidate[root]["legal_rows"][label]) for root in roots}
        event_free_by_root = {root: int(candidate[root]["event_free_legal_rows"][label]) for root in roots}
        contributing = {root: count for root, count in legal_by_root.items() if count > 0}
        pooled = sum(contributing.values())
        max_share = max(contributing.values(), default=0) / pooled if pooled else 1.0
        event_free_roots = sum(count > 0 for count in event_free_by_root.values())
        pooled_event_free = sum(event_free_by_root.values())
        fact = {
            "roots_with_legal_occupancy": len(contributing),
            "legal_rows_by_root": legal_by_root,
            "every_contributing_root_at_least_25": bool(contributing) and min(contributing.values()) >= 25,
            "pooled_legal_rows": pooled,
            "maximum_root_contribution": max_share,
            "roots_with_event_free_reachability": event_free_roots,
            "event_free_rows_by_root": event_free_by_root,
            "pooled_event_free_legal_rows": pooled_event_free,
        }
        fact["pass"] = bool(
            len(contributing) >= 12
            and fact["every_contributing_root_at_least_25"]
            and pooled >= 300
            and max_share <= 0.20
            and event_free_roots >= 12
            and pooled_event_free > 200
        )
        bin_facts[label] = fact
        bin_passes.append(bool(fact["pass"]))

    candidate_events = {
        label: sum(
            int(candidate[root]["actions"][label]["REFRESH-SAME"])
            + int(candidate[root]["actions"][label]["REBIND"])
            for root in roots
        ) for label in ("low", "high")
    }
    candidate_legal = sum(int(candidate[root]["legal_rows"][label]) for root in roots for label in ("low", "high"))
    shell_legal = sum(int(shell[root]["legal_rows"][label]) for root in roots for label in ("low", "high"))
    total_candidate_events = sum(candidate_events.values())
    total_shell_events = sum(int(shell[root]["voluntary_non_keep_events"]) for root in roots)
    candidate_activity = total_candidate_events / candidate_legal if candidate_legal else 0.0
    shell_activity = total_shell_events / shell_legal if shell_legal else 0.0
    activity_tolerance = max(0.01, 0.10 * candidate_activity)

    def marks(rows: Mapping[int, Mapping[str, object]]) -> tuple[int, int]:
        refresh = sum(
            int(rows[root]["actions"][label]["REFRESH-SAME"])
            for root in roots for label in ("low", "high")
        )
        rebind = sum(
            int(rows[root]["actions"][label]["REBIND"])
            for root in roots for label in ("low", "high")
        )
        return refresh, rebind

    candidate_marks = marks(candidate)
    shell_marks = marks(shell)
    candidate_refresh = candidate_marks[0] / sum(candidate_marks) if sum(candidate_marks) else None
    shell_refresh = shell_marks[0] / sum(shell_marks) if sum(shell_marks) else None
    mark_difference = (
        abs(candidate_refresh - shell_refresh)
        if candidate_refresh is not None and shell_refresh is not None else math.inf
    )
    candidate_event_pass = bool(
        total_candidate_events > 100
        and all(value > 20 for value in candidate_events.values())
        and candidate_activity > 0.02
    )
    shell_pass = bool(
        abs(shell_activity - candidate_activity) <= activity_tolerance
        and mark_difference <= 0.05
    )
    return {
        "bins": bin_facts,
        "candidate": {
            "voluntary_non_keep_events": total_candidate_events,
            "events_by_bin": candidate_events,
            "legal_opportunities": candidate_legal,
            "activity": candidate_activity,
            "pass": candidate_event_pass,
        },
        "shell": {
            "voluntary_non_keep_events": total_shell_events,
            "legal_opportunities": shell_legal,
            "activity": shell_activity,
            "activity_tolerance": activity_tolerance,
            "activity_difference": abs(shell_activity - candidate_activity),
            "candidate_conditional_refresh": candidate_refresh,
            "shell_conditional_refresh": shell_refresh,
            "conditional_mark_difference": mark_difference,
            "pass": shell_pass,
        },
        "pass": all(bin_passes) and candidate_event_pass and shell_pass,
    }


def discovery_heterogeneity_facts(
    stratified: Sequence[FixedPolicy], selected: FixedPolicy,
    metrics: Mapping[str, Mapping[int, Mapping[str, float]]], roots: Sequence[int] = ROOTS,
) -> dict[str, object]:
    leave_one_out: list[dict[str, object]] = []
    for omitted in roots:
        retained = tuple(root for root in roots if root != omitted)
        choice = select_best(stratified, metrics, retained)
        leave_one_out.append({
            "omitted_root": int(omitted), "policy_id": choice.policy_id,
            "p_low": choice.p_low, "p_high": choice.p_high,
            "separation": choice.separation,
            "monotone_separated": choice.separation >= 0.10,
        })
    best_mean = float(np.mean([
        float(metrics[selected.policy_id][root]["direct_return"]) for root in roots
    ], dtype=np.float64))
    near_optimal = []
    for policy in stratified:
        mean = float(np.mean([
            float(metrics[policy.policy_id][root]["direct_return"]) for root in roots
        ], dtype=np.float64))
        if best_mean - mean <= MATERIAL_MARGIN:
            near_optimal.append({
                "policy_id": policy.policy_id, "p_low": policy.p_low, "p_high": policy.p_high,
                "separation": policy.separation, "mean_direct_return": mean,
                "homogeneous": policy.p_low == policy.p_high,
                "weak_or_nonmonotone": policy.separation < 0.10,
            })
    stable_count = sum(bool(row["monotone_separated"]) for row in leave_one_out)
    near_set_clean = not any(bool(row["homogeneous"] or row["weak_or_nonmonotone"]) for row in near_optimal)
    return {
        "leave_one_root_out_selections": tuple(leave_one_out),
        "monotone_separated_count": stable_count,
        "near_optimal_margin": MATERIAL_MARGIN,
        "near_optimal_set": tuple(near_optimal),
        "near_optimal_set_excludes_homogeneous_and_weak": near_set_clean,
    }


def decide_branch(
    *, valid: bool, contrasts: Mapping[str, Mapping[str, object]],
    candidate: FixedPolicy, grid: Sequence[float], heterogeneity: Mapping[str, object],
) -> tuple[str, dict[str, object]]:
    required = ("global_lambda", "keep", "shell")
    direct = {name: contrasts[name]["components"]["direct_return"] for name in contrasts}
    headroom_pass = valid and all(float(direct[name]["one_sided_95_lower"]) > MATERIAL_MARGIN for name in required)
    bounded_no = valid and not headroom_pass and any(
        float(direct[name]["one_sided_95_upper"]) < MATERIAL_MARGIN for name in required
    )
    gate1 = {
        "evaluated": valid,
        "margin": MATERIAL_MARGIN,
        "component_lower_bounds": {name: direct[name]["one_sided_95_lower"] for name in required},
        "component_upper_bounds": {name: direct[name]["one_sided_95_upper"] for name in required},
        "status": "HEADROOM_PASS" if headroom_pass else "BOUNDED_NO_HEADROOM" if bounded_no else "HEADROOM_UNRESOLVED",
    }
    gate2_checks: dict[str, bool] = {}
    if headroom_pass:
        assert candidate.p_low is not None and candidate.p_high is not None
        gate2_checks = {
            "beats_global_p": float(direct["global_p"]["one_sided_95_lower"]) > MATERIAL_MARGIN,
            "selected_monotone_separation": candidate.p_high - candidate.p_low >= 0.10,
            "loo_stability": int(heterogeneity["monotone_separated_count"]) >= 12,
            "near_optimal_set_clean": bool(heterogeneity["near_optimal_set_excludes_homogeneous_and_weak"]),
            "selected_not_outer_grid": candidate.p_low not in (grid[0], grid[-1]) and candidate.p_high not in (grid[0], grid[-1]),
        }
    gate2 = {"evaluated": headroom_pass, "checks": gate2_checks, "pass": headroom_pass and all(gate2_checks.values())}
    if not valid:
        branch = "INVALID"
    elif bounded_no:
        branch = "BOUNDED_NO_HEADROOM"
    elif not headroom_pass:
        branch = "HEADROOM_UNRESOLVED"
    elif gate2["pass"]:
        branch = "HEADROOM_AND_EXPOSURE_HETEROGENEITY"
    else:
        branch = "HEADROOM_WITHOUT_IDENTIFIED_EXPOSURE_HETEROGENEITY"
    return branch, {
        "gate_1": gate1,
        "gate_2": gate2,
        "branches": {name: name == branch for name in BRANCHES},
    }

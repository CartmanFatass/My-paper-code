"""Registered summaries, paired inference, and completeness checks."""

from __future__ import annotations

from collections import Counter
import math
from typing import Iterable

import numpy as np

from .config import HELDOUT_SCHEDULES, LEARNED_ARMS, SEEDS
from .host import EpisodeResult

T975 = {7: 2.364624252}
T95 = {7: 1.894578605}
T9875 = {7: 2.841244249}


def student_interval(values: Iterable[float], confidence: float = 0.95) -> dict[str, float | int | None]:
    array = np.asarray(tuple(values), dtype=np.float64)
    if array.size < 2:
        return {"n": int(array.size), "mean": float(array.mean()) if array.size else None,
                "standard_error": None, "lower": None, "upper": None, "confidence": confidence}
    mean = float(array.mean())
    error = float(array.std(ddof=1) / math.sqrt(array.size))
    if confidence == 0.975:
        critical = T9875.get(array.size - 1, 2.241402728)
    elif confidence == 0.95:
        critical = T975.get(array.size - 1, 1.959963985)
    elif confidence == 0.90:
        critical = T95.get(array.size - 1, 1.644853627)
    else:
        raise ValueError("only registered 90%, 95%, and 97.5% intervals are supported")
    return {"n": int(array.size), "mean": mean, "standard_error": error,
            "lower": mean - critical * error, "upper": mean + critical * error,
            "confidence": confidence}


def _entropy(probabilities: list[float]) -> float | None:
    if not probabilities:
        return None
    p = np.clip(np.asarray(probabilities), 1e-12, 1 - 1e-12)
    return float(np.mean(-(p * np.log(p) + (1 - p) * np.log1p(-p))))


def _binary_entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -(probability * math.log(probability)
             + (1.0 - probability) * math.log1p(-probability))


def summarize_episodes(rows: Iterable[EpisodeResult]) -> dict[str, object]:
    episodes = list(rows)
    if not episodes:
        return {"episodes": 0}
    ticks = sum(r.physics_ticks for r in episodes)
    probability_rows = [row for r in episodes for row in r.probability_diagnostic_rows]
    eligible_probability_rows = [row for row in probability_rows if row[4]]
    event_p = [row[2] for row in eligible_probability_rows]
    mark_p = [row[3] for row in eligible_probability_rows]
    cue_rows = [(row[0], row[1], row[2], row[3]) for row in eligible_probability_rows]
    risk_rows = [row for r in episodes for role in r.risk_rows for row in role]
    post_startup_risk_rows = [row for row in risk_rows if not row[2]]
    dwells = Counter(v for r in episodes for role in r.inter_event_dwells for v in role)
    overshoots = Counter(v for r in episodes for role in r.lease_overshoots for v in role)
    def counts(field: str, role: int) -> list[int]:
        return [sum(getattr(r, field)[role][action] for r in episodes) for action in range(3)]
    def cause_counts(cause: str, kind: str, role: int) -> list[int]:
        return [sum(r.action_counts_by_cause[cause][kind][role][action] for r in episodes)
                for action in range(3)]
    cue_summary: dict[str, object] = {}
    for role, role_name in enumerate(("T", "R")):
        for label, predicate in (("LOW", lambda x: x < 0.5), ("HIGH", lambda x: x >= 0.5)):
            selected = [(u, rho) for r, cue, u, rho in cue_rows if r == role and predicate(cue)]
            cue_summary[f"{role_name}_{label}"] = {
                "count": len(selected),
                "mean_event_probability": float(np.mean([x[0] for x in selected])) if selected else None,
                "mean_mark_probability": float(np.mean([x[1] for x in selected])) if selected else None,
            }
    latencies = [v / 1e6 for r in episodes for v in r.decision_latencies_ns]
    boundary_audits = [record for r in episodes for record in r.boundary_audit_records]
    entropy_by_role: dict[str, object] = {}
    for role, role_name in enumerate(("T", "R")):
        role_rows = [row for row in probability_rows if row[0] == role]
        event_components = [_binary_entropy(u) if eligible else 0.0
                            for _r, _cue, u, _rho, eligible, _cause in role_rows]
        mark_components = [_binary_entropy(rho) if eligible else 0.0
                           for _r, _cue, _u, rho, eligible, _cause in role_rows]
        applied = [u * _binary_entropy(rho) if eligible else 0.0
                   for _r, _cue, u, rho, eligible, _cause in role_rows]
        entropy_by_role[role_name] = {
            "diagnostic_rows": len(role_rows),
            "eligible_policy_rows": sum(row[4] for row in role_rows),
            "zero_entropy_masked_or_forced_rows": sum(not row[4] for row in role_rows),
            "event_entropy": float(np.mean(event_components)) if role_rows else None,
            "conditional_mark_entropy": float(np.mean(mark_components)) if role_rows else None,
            "applied_u_times_mark_entropy": float(np.mean(applied)) if role_rows else None,
        }
    event_entropy_components = [
        _binary_entropy(row[2]) if row[4] else 0.0 for row in probability_rows
    ]
    conditional_mark_entropy_components = [
        _binary_entropy(row[3]) if row[4] else 0.0 for row in probability_rows
    ]
    applied_mark_entropy_components = [
        row[2] * _binary_entropy(row[3]) if row[4] else 0.0
        for row in probability_rows
    ]
    event_entropy = (
        float(np.mean(event_entropy_components)) if probability_rows else None
    )
    conditional_mark_entropy = (
        float(np.mean(conditional_mark_entropy_components)) if probability_rows else None
    )
    applied_mark_entropy = (
        float(np.mean(applied_mark_entropy_components)) if probability_rows else None
    )
    def survival(rows: list[tuple[int, int, bool]]) -> dict[str, object]:
        return {
            str(exposure): {
            "opportunities": sum(e == exposure for e, _event, _initial in rows),
            "event_free": sum(e == exposure and not event for e, event, _initial in rows),
            "event_free_fraction": (
                sum(e == exposure and not event for e, event, _initial in rows)
                / sum(e == exposure for e, _event, _initial in rows)
            ),
            }
            for exposure in sorted({e for e, _event, _initial in rows})
        }
    survival_by_exposure = survival(risk_rows)
    post_startup_survival_by_exposure = survival(post_startup_risk_rows)
    observed_exposure_by_role = [
        sum(r.initial_anchor_observed_exposure[i] + r.post_startup_eligible_exposure[i]
            for r in episodes) for i in range(2)
    ]
    post_startup_exposure_by_role = [
        sum(r.post_startup_eligible_exposure[i] for r in episodes) for i in range(2)
    ]
    post_startup_events_by_role = [
        sum(r.post_startup_voluntary_events[i] for r in episodes) for i in range(2)
    ]
    mean_action_cost = float(np.mean([
        r.iid_action_cost_episode for r in episodes
    ], dtype=np.float64))
    mean_service = float(np.mean([
        r.iid_service_episode for r in episodes
    ], dtype=np.float64))
    direct_mean_return = float(np.mean([
        r.iid_return_episode_direct for r in episodes
    ], dtype=np.float64))
    recomposed_mean_return = mean_service - mean_action_cost
    mean_return = (
        recomposed_mean_return
        if episodes[0].schedule == "RAND-IID-4-16-32" else direct_mean_return
    )
    aggregate_residual = direct_mean_return - recomposed_mean_return
    aggregate_tolerance = 1e-12 + 1e-10 * max(
        abs(direct_mean_return), abs(recomposed_mean_return),
    )
    episode_decomposition_rows = [{
        "episode_index": r.episode_index,
        "iid_service_episode": r.iid_service_episode,
        "iid_action_cost_episode": r.iid_action_cost_episode,
        "iid_return_episode_direct": r.iid_return_episode_direct,
        "iid_return_episode_recomposed": r.iid_return_episode_recomposed,
        "iid_return_episode_residual": r.iid_return_episode_residual,
        "iid_return_episode_tolerance": r.iid_return_episode_tolerance,
        "iid_return_episode_decomposition_ok": r.iid_return_episode_decomposition_ok,
    } for r in episodes]
    episode_failures = [
        row for row in episode_decomposition_rows
        if not row["iid_return_episode_decomposition_ok"]
    ]
    worst_episode = max(
        episode_decomposition_rows,
        key=lambda row: abs(float(row["iid_return_episode_residual"])),
    )
    return {
        "episodes": len(episodes),
        "mean_return": mean_return,
        "within_cell_episode_uncertainty": {
            "n": len(episodes),
            "mean": float(np.mean([r.normalized_return for r in episodes])),
            "standard_error": (
                float(np.std([r.normalized_return for r in episodes], ddof=1) / math.sqrt(len(episodes)))
                if len(episodes) >= 2 else None
            ),
        },
        "iid_decomposition_definition": "R_IID := S_IID - C_IID",
        "iid_decomposition_atol": 1e-12,
        "iid_decomposition_rtol": 1e-10,
        "iid_accumulation_dtype": "float64",
        "iid_accumulation_method": (
            "numpy.float64 episode sums followed by numpy.float64 episode means; "
            "claim-bearing return recomposed from retained service and explicit action cost"
        ),
        "iid_episode_decomposition": episode_decomposition_rows,
        "S_IID": mean_service,
        "C_IID": mean_action_cost,
        "R_IID": recomposed_mean_return,
        "R_IID_direct": direct_mean_return,
        "R_IID_direct_residual": aggregate_residual,
        "R_IID_direct_tolerance": aggregate_tolerance,
        "R_IID_direct_decomposition_ok": abs(aggregate_residual) <= aggregate_tolerance,
        "iid_episode_decomposition_fail_count": len(episode_failures),
        "iid_max_abs_episode_decomposition_residual": abs(float(
            worst_episode["iid_return_episode_residual"]
        )),
        "iid_worst_episode_decomposition_index": worst_episode["episode_index"],
        "iid_seed_arm_decomposition_ok": (
            abs(aggregate_residual) <= aggregate_tolerance and not episode_failures
        ),
        "attempted_actions_by_role": {role: counts("attempted_actions", i) for i, role in enumerate(("T", "R"))},
        "executed_actions_by_role": {role: counts("executed_actions", i) for i, role in enumerate(("T", "R"))},
        "stochastic_actions_by_role": {
            role: counts("stochastic_actions", i) for i, role in enumerate(("T", "R"))
        },
        "initial_anchor_stochastic_actions_by_role": {
            role: counts("initial_anchor_stochastic_actions", i)
            for i, role in enumerate(("T", "R"))
        },
        "poststartup_stochastic_actions_by_role": {
            role: counts("poststartup_stochastic_actions", i)
            for i, role in enumerate(("T", "R"))
        },
        "initial_anchor_legal_routine_rows_by_role": [
            sum(r.initial_anchor_legal_routine_rows[i] for r in episodes)
            for i in range(2)
        ],
        "poststartup_legal_routine_rows_by_role": [
            sum(r.poststartup_legal_routine_rows[i] for r in episodes)
            for i in range(2)
        ],
        "action_counts_by_cause_role": {
            cause: {
                role: {kind: cause_counts(cause, kind, i) for kind in ("attempted", "executed")}
                for i, role in enumerate(("T", "R"))
            } for cause in ("ROUTINE_CALLBACK", "SAFETY_BYPASS")
        },
        "voluntary_event_count_by_role": [sum(r.voluntary_events[i] for r in episodes) for i in range(2)],
        "policy_eligible_exposure_by_role": [
            sum(r.eligible_exposure[i] for r in episodes) for i in range(2)
        ],
        "observed_eligible_physical_exposure_by_role": observed_exposure_by_role,
        "eligible_exposure_by_role": observed_exposure_by_role,
        "voluntary_events_per_eligible_tick_by_role": [
            sum(r.voluntary_events[i] for r in episodes) / max(1, observed_exposure_by_role[i])
            for i in range(2)
        ],
        "post_startup_voluntary_events_per_eligible_tick_by_role": [
            post_startup_events_by_role[i] / max(1, post_startup_exposure_by_role[i])
            for i in range(2)
        ],
        "initial_anchor": {
            "flag": "initial_anchor_action",
            "actions": len(episodes) * 2,
            "e_policy_by_role": [
                sum(r.initial_anchor_policy_exposure[i] for r in episodes) for i in range(2)
            ],
            "e_observed_by_role": [
                sum(r.initial_anchor_observed_exposure[i] for r in episodes) for i in range(2)
            ],
            "e_virtual_by_role": [
                sum(r.initial_anchor_virtual_exposure[i] for r in episodes) for i in range(2)
            ],
        },
        "event_rate_diagnostic_panels": {
            "startup_inclusive": {
                "event_free_survival_by_policy_exposure": survival_by_exposure,
                "observed_eligible_physical_exposure_by_role": observed_exposure_by_role,
            },
            "post_startup": {
                "event_free_survival_by_policy_exposure": post_startup_survival_by_exposure,
                "observed_eligible_physical_exposure_by_role": post_startup_exposure_by_role,
            },
        },
        "event_free_survival_fraction_by_role": [
            1.0 - sum(r.voluntary_events[i] for r in episodes) /
            max(1, sum(r.legal_routine_boundaries[i] for r in episodes)) for i in range(2)
        ],
        "event_free_survival_by_eligible_exposure": survival_by_exposure,
        "post_startup_event_free_survival_by_eligible_exposure": post_startup_survival_by_exposure,
        "lease_masked_fraction_by_role": [
            sum(r.masked_routine_boundaries[i] for r in episodes) /
            max(1, sum(r.masked_routine_boundaries[i] + r.legal_routine_boundaries[i] for r in episodes))
            for i in range(2)
        ],
        "legal_routine_boundaries_by_role": [sum(r.legal_routine_boundaries[i] for r in episodes) for i in range(2)],
        "lease_grid_overshoot_histogram": dict(sorted(overshoots.items())),
        "physical_inter_event_dwell_histogram": dict(sorted(dwells.items())),
        "event_entropy": event_entropy,
        "mark_entropy": conditional_mark_entropy,
        "conditional_mark_entropy": conditional_mark_entropy,
        "applied_u_times_mark_entropy": applied_mark_entropy,
        "marked_entropy": (
            event_entropy + applied_mark_entropy
            if event_entropy is not None and applied_mark_entropy is not None else None
        ),
        "marked_entropy_by_role": entropy_by_role,
        "event_probability_saturation": {
            "below_0.01": sum(p < 0.01 for p in event_p) / max(1, len(event_p)),
            "above_0.99": sum(p > 0.99 for p in event_p) / max(1, len(event_p)),
        },
        "cue_conditioned_probabilities": {
            "eligible_policy_rows_only": cue_summary,
            "eligible_policy_row_count": len(eligible_probability_rows),
            "dummy_or_forced_row_count": len(probability_rows) - len(eligible_probability_rows),
            "dummy_or_forced_rows_by_cause": dict(sorted(Counter(
                row[5] for row in probability_rows if not row[4]
            ).items())),
        },
        "mean_mismatch_to_rebind_latency": float(np.mean([
            v for r in episodes for v in r.mismatch_rebind_latencies
        ])) if any(r.mismatch_rebind_latencies for r in episodes) else None,
        "stale_binding_ticks": sum(r.stale_binding_ticks for r in episodes),
        "mean_plan_age": sum(r.plan_age_sum for r in episodes) / (2 * ticks),
        "mean_service": mean_service,
        "action_downtime_ticks": sum(r.action_downtime_ticks for r in episodes),
        "action_cost": sum(r.action_cost for r in episodes),
        "mean_action_cost": mean_action_cost,
        "return_service_cost_decomposition_error": abs(aggregate_residual),
        "return_service_cost_decomposition_exact": (
            abs(aggregate_residual) <= aggregate_tolerance and not episode_failures
        ),
        "observed_reward_exposure_ledger": {
            "episode_rows": len(episodes),
            "exposure_rows": sum(r.exposure_ledger_rows for r in episodes),
            "action_before_service_boundary_rows": sum(
                r.action_before_service_boundary_rows for r in episodes
            ),
            "action_changed_service_value_rows": sum(
                r.action_changed_service_value_rows for r in episodes
            ),
            "segment_owned_ticks": sum(r.segment_owned_ticks for r in episodes),
            "exposure_closed_form_exact": all(
                r.exposure_closed_form_exact for r in episodes
            ),
            "action_before_service_exact": all(
                r.action_before_service_exact for r in episodes
            ),
            "reward_service_cost_tick_exact": all(
                r.reward_service_cost_exact for r in episodes
            ),
            "segment_ownership_exact": all(
                r.segment_ownership_exact for r in episodes
            ),
            "terminal_boundary_absent": all(
                r.terminal_boundary_absent for r in episodes
            ),
        },
        "forced_safety_count": sum(r.forced_safety_count for r in episodes),
        "same_tick_safety_rate": sum(r.safety_same_tick for r in episodes) / len(episodes),
        "safety_violations": sum(r.safety_violations for r in episodes),
        "safety_expected_action_matches": all(
            r.safety_expected_action == r.safety_affected_action for r in episodes
            if r.safety_expected_action is not None
        ),
        "affected_safety_actions": {
            str(k): v for k, v in Counter(r.safety_affected_action for r in episodes).items()
        },
        "unaffected_safety_actions": {
            str(k): v for k, v in Counter(r.safety_unaffected_action for r in episodes).items()
        },
        "resource": {
            "actor_calls": sum(r.actor_calls for r in episodes),
            "critic_calls": sum(r.critic_calls for r in episodes),
            "messages": sum(r.messages for r in episodes),
            "bits": sum(r.transmitted_bits for r in episodes),
            "physics_ticks": ticks,
            "joint_policy_bearing_boundary_rows": sum(
                int(record.policy_mask.sum() > 0) for r in episodes for record in r.training_records
            ),
            "agent_policy_bearing_rows": sum(
                int(record.policy_mask.sum()) for r in episodes for record in r.training_records
            ),
            "decision_latency_ms_p50": float(np.percentile(latencies, 50)) if latencies else None,
            "decision_latency_ms_p95": float(np.percentile(latencies, 95)) if latencies else None,
        },
        "identity": {
            "schema": ["episode_id", "agent_role", "owner_epoch", "own_boundary_index", "behavior_version"],
            "rows": sum(r.identity_rows for r in episodes),
            "unique_within_every_episode": all(r.identity_unique for r in episodes),
            "schema_valid_every_episode": all(r.identity_schema_valid for r in episodes),
        },
        "boundary_audit": {
            "records": len(boundary_audits),
            "initial_anchor_action_records": sum(
                record.initial_anchor_action for record in boundary_audits
            ),
            "identity_unique": (
                len(boundary_audits) == len({record.identity for record in boundary_audits})
            ),
            "prospective_cause_counts": dict(sorted(Counter(
                record.prospective_cause for record in boundary_audits
            ).items())),
            "action_counts": dict(sorted(Counter(
                record.action for record in boundary_audits
            ).items())),
            "post_action_ending_counts": dict(sorted(Counter(
                record.post_action_ending for record in boundary_audits
            ).items())),
            "ending_valid_for_cause_and_action": all(
                record.post_action_ending == (
                    "FORCED_SAFETY_REFRESH"
                    if record.prospective_cause == "SAFETY_BYPASS" and record.action == "REFRESH-SAME"
                    else "FORCED_SAFETY_REBIND"
                    if record.prospective_cause == "SAFETY_BYPASS" and record.action == "REBIND"
                    else "CONTINUED_KEEP"
                    if record.prospective_cause == "ROUTINE_CALLBACK" and record.action == "KEEP"
                    else "ENDED_REFRESH_SAME"
                    if record.prospective_cause == "ROUTINE_CALLBACK" and record.action == "REFRESH-SAME"
                    else "ENDED_REBIND"
                ) for record in boundary_audits
            ),
        },
        "switch_twin_audit": {
            "switches": sum(len(r.switch_audits) for r in episodes),
            "records": [audit for r in episodes for audit in r.switch_audits],
            "all_inputs_equal": all(
                bool(a["actor_inputs_equal_before_branch"]) for r in episodes for a in r.switch_audits
            ),
            "all_logits_probabilities_equal": all(
                bool(a["logits_and_probabilities_equal_before_branch"]) for r in episodes for a in r.switch_audits
            ),
            "all_common_uniform_actions_equal": all(
                bool(a["common_uniform_actions_equal_before_branch"]) for r in episodes for a in r.switch_audits
            ),
            "all_current_rewards_equal": all(
                bool(a["current_reward_equal_before_branch"]) for r in episodes for a in r.switch_audits
            ),
            "next_interval_never_input": all(
                not bool(a["next_interval_was_actor_or_rng_input"]) for r in episodes for a in r.switch_audits
            ),
        },
        "iid_interval_audit": {
            "interval_draw_counts": dict(sorted(Counter(
                interval for r in episodes for interval in r.iid_interval_draws
            ).items())),
            "draws_emitted": sum(len(r.iid_interval_draws) for r in episodes),
            "routine_boundaries_realized": sum(len(r.routine_boundary_ticks) for r in episodes),
            "each_draw_after_one_realized_routine_boundary": all(
                len(r.iid_interval_draws) == len(r.routine_boundary_ticks)
                for r in episodes if r.schedule == "RAND-IID-4-16-32"
            ),
            "terminal_censored_durations": [
                r.iid_terminal_censored_duration for r in episodes
                if r.iid_terminal_censored_duration is not None
            ],
            "no_boundary_at_H": all(
                256 not in r.routine_boundary_ticks for r in episodes
            ),
        },
    }


def primary_analysis(native: dict[str, dict[str, dict[str, dict[str, object]]]]) -> dict[str, object]:
    seed_estimands: dict[str, dict[str, dict[str, float]]] = {}
    for seed in SEEDS:
        seed_rows = native[str(seed)]
        seed_estimands[str(seed)] = {}
        for arm in LEARNED_ARMS:
            means = [float(seed_rows[arm][cell]["mean_return"]) for cell in HELDOUT_SCHEDULES]
            seed_estimands[str(seed)][arm] = {"P": float(np.mean(means)), "W": min(means)}
    intervals = {
        arm: {estimand: student_interval(seed_estimands[str(seed)][arm][estimand] for seed in SEEDS)
              for estimand in ("P", "W")} for arm in LEARNED_ARMS
    }
    contrasts: dict[str, object] = {}
    cell_contrasts: dict[str, object] = {}
    for left, right in (("ONLGR", "RAW-BOUNDARY-LEASE"),
                        ("ONLGR", "TIMING-ONLY-ONLGR")):
        label = f"{left}_minus_{right}"
        contrasts[label] = {
            estimand: student_interval(
                (seed_estimands[str(seed)][left][estimand] - seed_estimands[str(seed)][right][estimand]
                 for seed in SEEDS),
                confidence=0.95,
            ) for estimand in ("P", "W")
        }
        cell_contrasts[label] = {
            schedule: student_interval(
                float(native[str(seed)][left][schedule]["mean_return"])
                - float(native[str(seed)][right][schedule]["mean_return"])
                for seed in SEEDS
            ) for schedule in HELDOUT_SCHEDULES
        }
    raw = contrasts["ONLGR_minus_RAW-BOUNDARY-LEASE"]
    adjusted = {
        estimand: student_interval((
            seed_estimands[str(seed)]["ONLGR"][estimand]
            - seed_estimands[str(seed)]["RAW-BOUNDARY-LEASE"][estimand]
            for seed in SEEDS
        ), confidence=0.975) for estimand in ("P", "W")
    }
    sensitivities = {
        estimand: paired_sensitivities(tuple(
            seed_estimands[str(seed)]["ONLGR"][estimand]
            - seed_estimands[str(seed)]["RAW-BOUNDARY-LEASE"][estimand]
            for seed in SEEDS
        )) for estimand in ("P", "W")
    }
    support = {
        "P": bool(raw["P"]["mean"] >= 0.02 and adjusted["P"]["lower"] > 0.0),
        "W": bool(raw["W"]["mean"] >= 0.03 and adjusted["W"]["lower"] > 0.0),
    }
    return {"seed_estimands": seed_estimands, "estimand_intervals": intervals,
            "paired_contrasts": contrasts, "paired_schedule_contrasts": cell_contrasts,
            "bonferroni_97_5pct_primary_intervals": adjusted,
            "paired_sensitivity": sensitivities,
            "registered_primary_support": support,
            }


def paired_sensitivities(values: tuple[float, ...]) -> dict[str, object]:
    array = np.asarray(values, dtype=np.float64)
    observed = abs(float(array.mean()))
    exceed = 0
    for mask in range(1 << len(values)):
        signs = np.asarray([1.0 if mask & (1 << i) else -1.0 for i in range(len(values))])
        exceed += abs(float(np.mean(array * signs))) >= observed
    return {
        "exact_two_sided_sign_flip_p": exceed / (1 << len(values)),
        "sign_flip_condition": "conditional_on_sign_exchangeability_and_observed_effect_magnitudes",
        "observed_effect_magnitudes": [abs(float(value)) for value in array],
        "leave_one_seed_out_means": [
            float(np.delete(array, i).mean()) for i in range(len(values))
        ],
    }


def iid_analysis(iid: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    seed_returns = {
        str(seed): {arm: float(iid[str(seed)][arm]["mean_return"]) for arm in LEARNED_ARMS}
        for seed in SEEDS
    }
    contrasts: dict[str, object] = {}
    for right, margin, label in (
        ("RAW-BOUNDARY-LEASE", 0.02, "schedule_identity_free_link"),
        ("TIMING-ONLY-ONLGR", 0.02, "marked_policy_content_access_beyond_task_content_blind_ablation"),
    ):
        values = tuple(
            seed_returns[str(seed)]["ONLGR"] - seed_returns[str(seed)][right]
            for seed in SEEDS
        )
        interval = student_interval(values, 0.95)
        contrasts[f"ONLGR_minus_{right}"] = {
            "interval": interval, "materiality_margin": margin,
            "gate": bool(interval["mean"] >= margin and interval["lower"] > 0.0),
            "interpretation": label, "sensitivity": paired_sensitivities(values),
        }
    decomposition_conformant = all(
        bool(iid[str(seed)][arm]["iid_seed_arm_decomposition_ok"])
        for seed in SEEDS for arm in LEARNED_ARMS
    )
    return {
        "seed_returns": seed_returns, "contrasts": contrasts,
        "iid_reward_decomposition_conformant": decomposition_conformant,
    }


def validate_primary_completeness(
    *, native: dict[str, object], safety: dict[str, object], checkpoints: dict[str, object],
    partition: dict[str, object], fixed_rate: dict[str, object], resources: dict[str, object],
) -> list[str]:
    missing: list[str] = []
    for seed in SEEDS:
        for arm in LEARNED_ARMS:
            if str(seed) not in checkpoints or arm not in checkpoints[str(seed)]:
                missing.append(f"checkpoint:{seed}:{arm}")
            for schedule in HELDOUT_SCHEDULES:
                if not (((native.get(str(seed), {}) or {}).get(arm, {}) or {}).get(schedule)):  # type: ignore[union-attr]
                    missing.append(f"native:{seed}:{arm}:{schedule}")
                if not (((safety.get(str(seed), {}) or {}).get(arm, {}) or {}).get(schedule)):  # type: ignore[union-attr]
                    missing.append(f"safety:{seed}:{arm}:{schedule}")
        if not (partition.get(str(seed), {}) or {}).get("cells"):  # type: ignore[union-attr]
            missing.append(f"partition:{seed}")
    if not fixed_rate.get("selected"):
        missing.append("fixed_rate_selection")
    for key in ("wall_seconds", "peak_rss_bytes", "actual_team_ticks"):
        if key not in resources:
            missing.append(f"resource:{key}")
    return missing

"""Complete-package analyzer for the sole frozen B2 paired IID contrast."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
import math
from typing import Iterable, Mapping

import numpy as np
import torch
from scipy.stats import t as student_t

from .config import (
    ARMS, DIAGNOSTIC_GRID, HORIZON, IID_EPISODES_PER_ARM_SEED,
    KEEP_EPISODES_PER_ARM_SEED, REVISION, SAFETY_EPISODES_PER_ARM_SEED,
    SEEDS, TRAIN_EPISODES_PER_ARM_SEED, registered_work,
)
from .host import EpisodeResult, timing_features
from .models import B2Learner, analytic_probability, analytic_probability_jacobian, initialization_report


def student_interval(values: Iterable[float]) -> dict[str, float | int]:
    array = np.asarray(tuple(values), dtype=np.float64)
    if array.size < 2:
        raise ValueError("Student interval requires at least two values")
    mean = float(array.mean())
    standard_error = float(array.std(ddof=1) / math.sqrt(array.size))
    half_width = float(student_t.ppf(0.975, array.size - 1) * standard_error)
    return {
        "n": int(array.size), "mean": mean, "standard_error": standard_error,
        "lower": mean - half_width, "upper": mean + half_width,
    }


def exact_paired_sign_flip_pvalue(values: Iterable[float]) -> float:
    array = np.asarray(tuple(values), dtype=np.float64)
    observed = abs(float(array.mean()))
    exceed = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(array)):
        exceed += abs(float(np.mean(array * np.asarray(signs)))) >= observed - 1e-15
    return exceed / float(2 ** len(array))


def _hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _distribution(rows: list[dict[str, object]], key: str) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    result: dict[str, object] = {}
    for value, group in sorted(grouped.items()):
        rates = np.asarray([float(row["lambda"]) for row in group], dtype=np.float64)
        probabilities = np.asarray([float(row["event_probability"]) for row in group], dtype=np.float64)
        entropies = np.asarray([float(row["marked_entropy"]) for row in group], dtype=np.float64)
        result[value] = {
            "n": len(group), "lambda_mean": float(rates.mean()),
            "lambda_standard_deviation": float(rates.std(ddof=0)),
            "lambda_minimum": float(rates.min()), "lambda_maximum": float(rates.max()),
            "event_probability_mean": float(probabilities.mean()),
            "event_probability_standard_deviation": float(probabilities.std(ddof=0)),
            "marked_entropy_mean": float(entropies.mean()),
        }
    return result


def summarize_panel(episodes: Iterable[EpisodeResult]) -> dict[str, object]:
    rows = list(episodes)
    if not rows:
        raise ValueError("cannot summarize an empty B2 panel")
    returns = tuple(float(row.normalized_return) for row in rows)
    actions = np.zeros((2, 3), dtype=np.int64)
    legal = np.zeros(2, dtype=np.int64)
    masks = np.zeros(2, dtype=np.int64)
    for row in rows:
        actions += np.asarray(row.poststartup_stochastic_actions, dtype=np.int64)
        legal += np.asarray(row.poststartup_legal_rows, dtype=np.int64)
        masks += np.asarray(row.masked_routine_rows, dtype=np.int64)
    rate_rows = [dict(rate) for row in rows for rate in row.rate_rows]
    for rate in rate_rows:
        probability = float(rate["event_probability"])
        if probability <= 0.0 or probability >= 1.0:
            bernoulli_entropy = 0.0
        else:
            bernoulli_entropy = -probability * math.log(probability) - (1.0 - probability) * math.log1p(-probability)
        rate["marked_entropy"] = bernoulli_entropy + probability * math.log(2.0)
        features = tuple(float(value) for value in rate["timing_features"])
        rate["plan_age"] = int(round(features[0] * 64))
        rate["lease_remaining"] = int(round(features[1] * 12))
        rate["busy"] = int(round(features[2] * 2))
        rate["preceding_delta"] = int(round(features[5] * 32))
    iid_ordinal_exact = all(
        tuple(record[0] for record in row.iid_draw_records) == tuple(range(len(row.iid_draw_records)))
        and tuple(record[1] for record in row.iid_draw_records) == row.routine_boundary_ticks
        and tuple(record[2] for record in row.iid_draw_records) == row.iid_interval_draws
        for row in rows if row.schedule == "RAND-IID-4-16-32"
    )
    identity_schema_valid = all(
        identity.episode_id and identity.agent_role in ("T", "R")
        and identity.owner_epoch >= 0 and identity.own_boundary_index >= 0
        and identity.behavior_version
        and identity.cause in ("ROUTINE_CALLBACK", "SAFETY_BYPASS")
        and identity.action in ("KEEP", "REFRESH-SAME", "REBIND")
        for row in rows for identity in row.identity_rows
    )
    return {
        "episodes": len(rows), "physics_ticks": sum(row.physics_ticks for row in rows),
        "mean_return": float(np.mean(returns)), "episode_return_interval": student_interval(returns),
        "mean_service": float(np.mean([row.service for row in rows])),
        "mean_action_cost": float(np.mean([row.action_cost for row in rows])),
        "poststartup_legal_rows_by_role": tuple(int(value) for value in legal),
        "poststartup_legal_rows": int(legal.sum()),
        "poststartup_stochastic_actions_by_role": tuple(tuple(int(v) for v in role) for role in actions),
        "poststartup_stochastic_actions": tuple(int(value) for value in actions.sum(axis=0)),
        "masked_routine_rows": tuple(int(value) for value in masks),
        "eligible_exposure": tuple(int(sum(row.eligible_exposure[role] for row in rows)) for role in range(2)),
        "iid_draw_count": sum(len(row.iid_interval_draws) for row in rows),
        "iid_draw_counts": {
            str(interval): sum(row.iid_interval_draws.count(interval) for row in rows)
            for interval in (4, 16, 32)
        },
        "iid_draw_ordinal_and_after_action_rule_exact": iid_ordinal_exact,
        "iid_draw_filtration": {
            "counter_domain": "ONLGR_B2_REV02/RAND_IID_NEXT_K",
            "coordinates_only": ("B2 seed", "episode_index", "global_routine_draw_ordinal"),
            "draw_after_current_action": True,
            "visible_history_action_state_reward_prior_intervals_excluded": True,
        },
        "reward_service_cost_exact": all(row.reward_service_cost_exact for row in rows),
        "segment_ownership_exact": all(row.segment_ownership_exact for row in rows),
        "terminal_boundary_absent": all(row.terminal_boundary_absent for row in rows),
        "identity_unique": all(row.identity_unique for row in rows),
        "identity_schema_valid": identity_schema_valid,
        "identity_rows": sum(len(row.identity_rows) for row in rows),
        "actor_calls": sum(row.actor_calls for row in rows),
        "critic_calls": sum(row.critic_calls for row in rows),
        "messages": sum(row.messages for row in rows),
        "transmitted_bits": sum(row.transmitted_bits for row in rows),
        "latency_ns": tuple(value for row in rows for value in row.decision_latencies_ns),
        "safety_forced_count": sum(row.safety_forced_count for row in rows),
        "safety_violations": sum(row.safety_violations for row in rows),
        "safety_score_factors": sum(row.safety_policy_score_factors for row in rows),
        "safety_affected_clock_exact": all(
            row.safety_tick is None or row.safety_affected_clock_advanced for row in rows
        ),
        "safety_unaffected_clock_exact": all(
            row.safety_tick is None or not row.safety_unaffected_clock_advanced for row in rows
        ),
        "safety_response_rows": tuple({
            "episode": row.episode_index, "tick": row.safety_tick,
            "coincident_routine": row.safety_coincident_routine,
            "affected_agent": row.safety_affected_agent,
            "expected_action": row.safety_expected_action,
            "affected_action": row.safety_affected_action,
            "unaffected_action": row.safety_unaffected_action,
            "draws_at_safety": sum(record[1] == row.safety_tick for record in row.iid_draw_records),
        } for row in rows if row.safety_tick is not None),
        "fixed_conditional_mark_probability": 0.5,
        "rate_const_effective_actor_inputs_exact_zero": (
            all(set(rate["effective_actor_input"]) <= {0.0} for rate in rate_rows)
            if rows[0].arm == "RATE-CONST" else None
        ),
        "rate_const_lambda_exactly_equal_across_actor_rows": (
            all(float(rate["lambda"]) == float(rate_rows[0]["lambda"]) for rate in rate_rows)
            if rows[0].arm == "RATE-CONST" and rate_rows else None
        ),
        "rate_distributions": {
            "by_exposure": _distribution(rate_rows, "exposure"),
            "by_plan_age": _distribution(rate_rows, "plan_age"),
            "by_busy_state": _distribution(rate_rows, "busy"),
            "by_preceding_interval": _distribution(rate_rows, "preceding_delta"),
            "by_role": _distribution(rate_rows, "role"),
        },
        "event_free_survival_rows": tuple(value for row in rows for value in row.event_free_survival_rows),
        "voluntary_event_ticks": tuple(
            value for row in rows for role in row.voluntary_event_ticks for value in role
        ),
        "inter_event_dwells": tuple(value for row in rows for role in row.inter_event_dwells for value in role),
        "stale_binding_ticks": sum(row.stale_binding_ticks for row in rows),
        "plan_age_sum": sum(row.plan_age_sum for row in rows),
        "downtime_ticks": sum(row.downtime_ticks for row in rows),
        "physics_ledger_sha256": _hash(tuple(row.physics_ledger for row in rows)),
        "interval_ledger_sha256": _hash(tuple(row.iid_interval_draws for row in rows)),
        "dummy_call_ledger_sha256": _hash(tuple(row.dummy_call_ledger for row in rows)),
    }


def diagnostic_grid(learner: B2Learner) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for age, delta, exposure in DIAGNOSTIC_GRID:
        feature = timing_features(
            age=age, lease_expiry=0, busy=0, tick=0, cause="ROUTINE_CALLBACK",
            delta=delta, exposure=exposure,
        )
        logits, rates, probabilities = learner.policy(
            feature[None, :], np.asarray([exposure], dtype=np.float64),
        )
        rows.append({
            "plan_age": age, "delta": delta, "exposure": exposure,
            "features": tuple(float(value) for value in feature),
            "lambda": float(rates[0]), "event_probability": float(probabilities[0]),
            "logit": float(logits[0]),
        })
    lambdas = np.asarray([row["lambda"] for row in rows], dtype=np.float64)
    return {
        "rows": tuple(rows), "count": len(rows), "lambda_range": float(np.ptp(lambdas)),
        "lambda_standard_deviation": float(lambdas.std(ddof=0)),
        "rate_const_exact_equality": bool(np.all(lambdas == lambdas[0])) if learner.arm == "RATE-CONST" else None,
    }


def probability_jacobian_conformance() -> dict[str, object]:
    cases = ((-8.0, 1.0), (-3.2, 4.0), (-1.0, 8.0), (0.0, 16.0), (3.0, 32.0))
    max_probability_error = max_jacobian_error = 0.0
    for logit, exposure in cases:
        g = torch.tensor(logit, dtype=torch.float64, requires_grad=True)
        e = torch.tensor(exposure, dtype=torch.float64, requires_grad=True)
        event = -torch.expm1(-torch.nn.functional.softplus(g) * e)
        probabilities = torch.stack((1.0 - event, 0.5 * event, 0.5 * event))
        jacobian_rows = []
        for index in range(3):
            jacobian_rows.append(torch.autograd.grad(
                probabilities[index], (g, e), retain_graph=index < 2,
            ))
        expected_event = float(analytic_probability(logit, exposure))
        expected_probabilities = (1.0 - expected_event, 0.5 * expected_event, 0.5 * expected_event)
        expected_dg, expected_de = analytic_probability_jacobian(logit, exposure)
        expected_jacobian = (
            (-expected_dg, -expected_de),
            (0.5 * expected_dg, 0.5 * expected_de),
            (0.5 * expected_dg, 0.5 * expected_de),
        )
        max_probability_error = max(max_probability_error, *(
            abs(float(actual) - expected) for actual, expected in zip(
                probabilities, expected_probabilities, strict=True,
            )
        ))
        max_jacobian_error = max(max_jacobian_error, *(
            abs(float(actual) - expected)
            for row, expected_row in zip(jacobian_rows, expected_jacobian, strict=True)
            for actual, expected in zip(row, expected_row, strict=True)
        ))
    return {
        "absolute_tolerance": 1e-10, "maximum_probability_error": max_probability_error,
        "maximum_jacobian_error": max_jacobian_error,
        "passes": max(max_probability_error, max_jacobian_error) <= 1e-10,
    }


def decision_branches(
    *, package_valid: bool, mark_support_ok: bool, differences: Iterable[float],
) -> dict[str, object]:
    values = tuple(float(value) for value in differences)
    interval = student_interval(values)
    statistical_gate = interval["mean"] >= 0.02 and interval["lower"] > 0.0
    retain = bool(package_valid and mark_support_ok and statistical_gate)
    absorb = bool(package_valid and mark_support_ok and not statistical_gate)
    inconclusive = bool(package_valid and not mark_support_ok)
    return {
        "PACKAGE_VALID": bool(package_valid), "MARK_SUPPORT_OK": bool(mark_support_ok),
        "material_positive_gate": bool(statistical_gate), "RETAIN_RATE_FLEX": retain,
        "ABSORB_TO_GLOBAL_RATE": absorb,
        "INCONCLUSIVE_INSUFFICIENT_VOLUNTARY_SUPPORT": inconclusive,
        "NO_SCIENTIFIC_BRANCH_INCOMPLETE_PACKAGE": not package_valid,
    }


PANEL_MANDATORY_FIELDS = frozenset({
    "episodes", "physics_ticks", "mean_return", "episode_return_interval", "mean_service",
    "mean_action_cost", "poststartup_legal_rows_by_role", "poststartup_legal_rows",
    "poststartup_stochastic_actions_by_role", "poststartup_stochastic_actions",
    "masked_routine_rows", "eligible_exposure", "iid_draw_count", "iid_draw_counts",
    "iid_draw_ordinal_and_after_action_rule_exact", "iid_draw_filtration",
    "reward_service_cost_exact", "segment_ownership_exact", "terminal_boundary_absent",
    "identity_unique", "identity_schema_valid", "identity_rows", "actor_calls", "critic_calls",
    "messages", "transmitted_bits", "latency_ns", "safety_forced_count", "safety_violations",
    "safety_score_factors", "safety_affected_clock_exact", "safety_unaffected_clock_exact",
    "safety_response_rows", "fixed_conditional_mark_probability", "rate_distributions",
    "rate_const_effective_actor_inputs_exact_zero",
    "rate_const_lambda_exactly_equal_across_actor_rows", "event_free_survival_rows",
    "voluntary_event_ticks", "inter_event_dwells", "stale_binding_ticks", "plan_age_sum",
    "downtime_ticks", "physics_ledger_sha256", "interval_ledger_sha256",
    "dummy_call_ledger_sha256",
    "checkpoint_learned_state_sha256",
})
GRID_MANDATORY_FIELDS = frozenset({
    "rows", "count", "lambda_range", "lambda_standard_deviation", "rate_const_exact_equality",
    "checkpoint_learned_state_sha256",
})
TRAINING_MANDATORY_FIELDS = frozenset({
    "episodes", "physics_ticks", "actor_calls", "critic_calls", "messages", "transmitted_bits",
    "identity_rows", "identity_unique_within_episodes", "identity_schema_valid",
    "reward_service_cost_exact", "segment_ownership_exact", "terminal_boundary_absent",
    "latency_call_count", "latency_sum_ns", "latency_max_ns", "actor_parameter_count",
    "critic_parameter_count", "completed_updates", "optimizer_steps", "update_facts",
    "per_update_work_facts",
})
CHECKPOINT_MANDATORY_FIELDS = frozenset({
    "artifact_kind", "revision", "seed", "arm", "source_identity", "learned_state_sha256",
    "path", "sha256_before_evaluation",
    "sha256_after_evaluation", "immutable_before_after", "completed_updates",
    "actor_parameter_count", "critic_parameter_count", "source_identity_exact", "envelope_valid",
})
UPDATE_FACT_MANDATORY_FIELDS = frozenset({
    "update_index", "optimizer_steps", "complete_episodes", "boundary_rows",
    "genuine_joint_policy_rows", "episodes_by_schedule", "actor_joint_rows_by_schedule",
    "behavior_log_probabilities_cached_before_epochs", "behavior_critic_values_cached_before_epochs",
    "advantages_cached_before_epochs", "lambda_returns_cached_before_epochs",
    "caches_unchanged_all_epochs", "terminal_behavior_value", "actor_global_scale",
    "advantage_normalization", "value_clipping", "value_coefficient_applications",
})
TRAINING_UPDATE_WORK_MANDATORY_FIELDS = frozenset({
    "episodes", "physics_ticks", "actor_calls", "critic_calls", "messages", "transmitted_bits",
    "identity_rows", "identity_unique_within_episodes", "identity_schema_valid",
    "reward_service_cost_exact", "segment_ownership_exact", "terminal_boundary_absent",
    "latency_call_count", "latency_sum_ns", "latency_max_ns", "actor_parameter_count",
    "critic_parameter_count",
})
GRID_ROW_MANDATORY_FIELDS = frozenset({
    "plan_age", "delta", "exposure", "features", "lambda", "event_probability", "logit",
})
RATE_DISTRIBUTION_MANDATORY_FIELDS = frozenset({
    "n", "lambda_mean", "lambda_standard_deviation", "lambda_minimum", "lambda_maximum",
    "event_probability_mean", "event_probability_standard_deviation", "marked_entropy_mean",
})
SAFETY_RESPONSE_MANDATORY_FIELDS = frozenset({
    "episode", "tick", "coincident_routine", "affected_agent", "expected_action",
    "affected_action", "unaffected_action", "draws_at_safety",
})


def _record_missing_fields(
    missing: list[str], *, prefix: str, value: Mapping[str, object], required: frozenset[str],
) -> None:
    missing.extend(f"{prefix}.{field}" for field in sorted(required - set(value)))


def analyze_complete_package(
    *, panels: Mapping[str, Mapping[str, Mapping[str, object]]],
    checkpoints: Mapping[str, Mapping[str, object]],
    training: Mapping[str, Mapping[str, object]], source_identity_exact: bool,
    atomic_frontier_exact: bool, keep_pairing: Mapping[str, bool],
    expected_source_identity: Mapping[str, object],
) -> dict[str, object]:
    missing: list[str] = []
    iid_cells: dict[str, dict[str, object]] = {}
    safety_cells: dict[str, dict[str, object]] = {}
    keep_cells: dict[str, dict[str, object]] = {}
    grid_cells: dict[str, dict[str, object]] = {}
    for seed in SEEDS:
        key = str(seed)
        for arm in ARMS:
            coordinate = f"{seed}:{arm}"
            checkpoint = checkpoints.get(key, {}).get(arm)
            train = training.get(key, {}).get(arm)
            iid = panels.get("iid", {}).get(key, {}).get(arm)
            safety = panels.get("safety", {}).get(key, {}).get(arm)
            keep = panels.get("keep", {}).get(key, {}).get(arm)
            grid = panels.get("grid", {}).get(key, {}).get(arm)
            for name, value in (("checkpoint", checkpoint), ("training", train), ("iid", iid),
                                ("safety", safety), ("keep", keep), ("grid", grid)):
                if value is None:
                    missing.append(f"{name}:{coordinate}")
            if iid is not None:
                iid_cells.setdefault(key, {})[arm] = iid
                _record_missing_fields(missing, prefix=f"iid:{coordinate}", value=iid, required=PANEL_MANDATORY_FIELDS)
                if int(iid.get("episodes", -1)) != IID_EPISODES_PER_ARM_SEED:
                    missing.append(f"iid_count:{coordinate}")
            if safety is not None:
                safety_cells.setdefault(key, {})[arm] = safety
                _record_missing_fields(missing, prefix=f"safety:{coordinate}", value=safety, required=PANEL_MANDATORY_FIELDS)
                if int(safety.get("episodes", -1)) != SAFETY_EPISODES_PER_ARM_SEED:
                    missing.append(f"safety_count:{coordinate}")
            if keep is not None:
                keep_cells.setdefault(key, {})[arm] = keep
                _record_missing_fields(missing, prefix=f"keep:{coordinate}", value=keep, required=PANEL_MANDATORY_FIELDS)
                if int(keep.get("episodes", -1)) != KEEP_EPISODES_PER_ARM_SEED:
                    missing.append(f"keep_count:{coordinate}")
            if grid is not None:
                grid_cells.setdefault(key, {})[arm] = grid
                _record_missing_fields(missing, prefix=f"grid:{coordinate}", value=grid, required=GRID_MANDATORY_FIELDS)
                if int(grid.get("count", -1)) != 20:
                    missing.append(f"grid_count:{coordinate}")
            if train is not None and int(train.get("episodes", -1)) != TRAIN_EPISODES_PER_ARM_SEED:
                missing.append(f"training_count:{coordinate}")
            if train is not None:
                _record_missing_fields(missing, prefix=f"training:{coordinate}", value=train, required=TRAINING_MANDATORY_FIELDS)
            if checkpoint is not None and int(checkpoint.get("completed_updates", -1)) != 8:
                missing.append(f"checkpoint_updates:{coordinate}")
            if checkpoint is not None:
                _record_missing_fields(
                    missing, prefix=f"checkpoint:{coordinate}", value=checkpoint,
                    required=CHECKPOINT_MANDATORY_FIELDS,
                )

    support_cells: dict[str, dict[str, object]] = {}
    for seed in SEEDS:
        key = str(seed)
        for arm in ARMS:
            cell = iid_cells.get(key, {}).get(arm, {})
            legal = int(cell.get("poststartup_legal_rows", -1))
            actions = tuple(cell.get("poststartup_stochastic_actions", ()))
            passed = legal >= 64 and len(actions) == 3 and all(int(value) >= 4 for value in actions)
            support_cells.setdefault(key, {})[arm] = {
                "poststartup_legal_rows": legal, "actions_KEEP_REFRESH_REBIND": actions,
                "passes_64_4_4_4": passed,
            }
    mark_support_ok = bool(support_cells) and all(
        bool(support_cells[str(seed)][arm]["passes_64_4_4_4"]) for seed in SEEDS for arm in ARMS
    )

    conformance = {
        "source_and_card_identity_exact": bool(source_identity_exact),
        "atomic_frontier_exact": bool(atomic_frontier_exact),
        "probability_and_full_jacobian": probability_jacobian_conformance()["passes"],
        "all_iid_draw_ordinals_exact": all(
            bool(iid_cells.get(str(seed), {}).get(arm, {}).get("iid_draw_ordinal_and_after_action_rule_exact"))
            for seed in SEEDS for arm in ARMS
        ),
        "all_safety_exact": all(
            int(safety_cells.get(str(seed), {}).get(arm, {}).get("safety_forced_count", -1)) == 16
            and int(safety_cells.get(str(seed), {}).get(arm, {}).get("safety_violations", -1)) == 0
            and int(safety_cells.get(str(seed), {}).get(arm, {}).get("safety_score_factors", -1)) == 0
            and bool(safety_cells.get(str(seed), {}).get(arm, {}).get("safety_affected_clock_exact"))
            and bool(safety_cells.get(str(seed), {}).get(arm, {}).get("safety_unaffected_clock_exact"))
            and all(
                int(row.get("draws_at_safety", -1)) == int(bool(row.get("coincident_routine")))
                for row in safety_cells.get(str(seed), {}).get(arm, {}).get("safety_response_rows", ())
            )
            and len(safety_cells.get(str(seed), {}).get(arm, {}).get("safety_response_rows", ())) == 16
            and sum(
                int(row.get("affected_agent") == 0)
                for row in safety_cells.get(str(seed), {}).get(arm, {}).get("safety_response_rows", ())
            ) == 8
            and sum(
                int(row.get("affected_agent") == 1)
                for row in safety_cells.get(str(seed), {}).get(arm, {}).get("safety_response_rows", ())
            ) == 8
            for seed in SEEDS for arm in ARMS
        ),
        "all_keep_replays_paired_equal": all(bool(keep_pairing.get(str(seed))) for seed in SEEDS),
        "all_const_grid_rates_exactly_equal": all(
            bool(grid_cells.get(str(seed), {}).get("RATE-CONST", {}).get("rate_const_exact_equality"))
            for seed in SEEDS
        ),
        "all_const_actor_inputs_zero_and_rates_equal": all(
            bool(panels.get(panel, {}).get(str(seed), {}).get("RATE-CONST", {}).get(
                "rate_const_effective_actor_inputs_exact_zero"
            ))
            and bool(panels.get(panel, {}).get(str(seed), {}).get("RATE-CONST", {}).get(
                "rate_const_lambda_exactly_equal_across_actor_rows"
            ))
            for panel in ("iid", "safety", "keep") for seed in SEEDS
        ),
        "fixed_rho_exact": all(
            float(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get(
                "fixed_conditional_mark_probability", -1.0
            )) == 0.5
            for panel in ("iid", "safety", "keep") for seed in SEEDS for arm in ARMS
        ),
        "ppo_behavior_caches_and_work_exact": all(
            int(training.get(str(seed), {}).get(arm, {}).get("optimizer_steps", -1)) == 32
            and len(training.get(str(seed), {}).get(arm, {}).get("update_facts", ())) == 8
            and all(
                int(fact.get("optimizer_steps", -1)) == 4
                and int(fact.get("complete_episodes", -1)) == 32
                and fact.get("episodes_by_schedule") == {schedule: 8 for schedule in (
                    "CONST-8", "CONST-24", "MID-8-TO-24", "MID-24-TO-8"
                )}
                and bool(fact.get("behavior_log_probabilities_cached_before_epochs"))
                and bool(fact.get("behavior_critic_values_cached_before_epochs"))
                and bool(fact.get("advantages_cached_before_epochs"))
                and bool(fact.get("lambda_returns_cached_before_epochs"))
                and bool(fact.get("caches_unchanged_all_epochs"))
                and fact.get("advantage_normalization") is False
                and fact.get("value_clipping") is False
                and int(fact.get("value_coefficient_applications", -1)) == 1
                for fact in training.get(str(seed), {}).get(arm, {}).get("update_facts", ())
            )
            for seed in SEEDS for arm in ARMS
        ),
        "actor_and_critic_shapes_matched": all(
            checkpoints.get(str(seed), {}).get("RATE-FLEX", {}).get("actor_parameter_count")
            == checkpoints.get(str(seed), {}).get("RATE-CONST", {}).get("actor_parameter_count")
            and checkpoints.get(str(seed), {}).get("RATE-FLEX", {}).get("critic_parameter_count")
            == checkpoints.get(str(seed), {}).get("RATE-CONST", {}).get("critic_parameter_count")
            for seed in SEEDS
        ),
        "checkpoint_envelopes_and_hashes_exact": all(
            checkpoints.get(str(seed), {}).get(arm, {}).get("artifact_kind")
            == "ONLGR_B2_SOLE_FINAL_CHECKPOINT"
            and checkpoints.get(str(seed), {}).get(arm, {}).get("revision") == REVISION
            and checkpoints.get(str(seed), {}).get(arm, {}).get("seed") == seed
            and checkpoints.get(str(seed), {}).get(arm, {}).get("arm") == arm
            and checkpoints.get(str(seed), {}).get(arm, {}).get("source_identity")
            == dict(expected_source_identity)
            and isinstance(checkpoints.get(str(seed), {}).get(arm, {}).get("learned_state_sha256"), str)
            and len(checkpoints.get(str(seed), {}).get(arm, {}).get("learned_state_sha256", "")) == 64
            and bool(checkpoints.get(str(seed), {}).get(arm, {}).get("source_identity_exact"))
            and bool(checkpoints.get(str(seed), {}).get(arm, {}).get("envelope_valid"))
            and checkpoints.get(str(seed), {}).get(arm, {}).get("completed_updates") == 8
            and isinstance(checkpoints.get(str(seed), {}).get(arm, {}).get("sha256_before_evaluation"), str)
            and len(checkpoints.get(str(seed), {}).get(arm, {}).get("sha256_before_evaluation", "")) == 64
            and checkpoints.get(str(seed), {}).get(arm, {}).get("sha256_before_evaluation")
            == checkpoints.get(str(seed), {}).get(arm, {}).get("sha256_after_evaluation")
            and bool(checkpoints.get(str(seed), {}).get(arm, {}).get("immutable_before_after"))
            for seed in SEEDS for arm in ARMS
        ),
        "all_reports_bound_to_exact_learned_state": all(
            panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get(
                "checkpoint_learned_state_sha256"
            ) == checkpoints.get(str(seed), {}).get(arm, {}).get("learned_state_sha256")
            for panel in ("iid", "safety", "keep") for seed in SEEDS for arm in ARMS
        ) and all(
            grid_cells.get(str(seed), {}).get(arm, {}).get("checkpoint_learned_state_sha256")
            == checkpoints.get(str(seed), {}).get(arm, {}).get("learned_state_sha256")
            for seed in SEEDS for arm in ARMS
        ),
        "training_reports_and_exact_work": all(
            int(training.get(str(seed), {}).get(arm, {}).get("episodes", -1)) == 256
            and int(training.get(str(seed), {}).get(arm, {}).get("physics_ticks", -1)) == 65536
            and int(training.get(str(seed), {}).get(arm, {}).get("actor_calls", -1)) == 11136
            and int(training.get(str(seed), {}).get(arm, {}).get("critic_calls", -1)) == 5568
            and int(training.get(str(seed), {}).get(arm, {}).get("messages", -1)) == 131072
            and int(training.get(str(seed), {}).get(arm, {}).get("transmitted_bits", -1)) == 262144
            and int(training.get(str(seed), {}).get(arm, {}).get("optimizer_steps", -1)) == 32
            and len(training.get(str(seed), {}).get(arm, {}).get("per_update_work_facts", ())) == 8
            and bool(training.get(str(seed), {}).get(arm, {}).get("identity_unique_within_episodes"))
            and bool(training.get(str(seed), {}).get(arm, {}).get("identity_schema_valid"))
            and bool(training.get(str(seed), {}).get(arm, {}).get("reward_service_cost_exact"))
            and bool(training.get(str(seed), {}).get(arm, {}).get("segment_ownership_exact"))
            and bool(training.get(str(seed), {}).get(arm, {}).get("terminal_boundary_absent"))
            for seed in SEEDS for arm in ARMS
        ),
        "training_cross_arm_work_matched": all(
            all(
                training.get(str(seed), {}).get("RATE-FLEX", {}).get(field)
                == training.get(str(seed), {}).get("RATE-CONST", {}).get(field)
                for field in (
                    "episodes", "physics_ticks", "actor_calls", "critic_calls", "messages",
                    "transmitted_bits", "identity_rows", "actor_parameter_count",
                    "critic_parameter_count", "optimizer_steps",
                )
            ) for seed in SEEDS
        ),
        "all_panel_reports_and_cross_arm_work_exact": all(
            all(
                field in panels.get(panel, {}).get(str(seed), {}).get(arm, {})
                for field in PANEL_MANDATORY_FIELDS
            )
            and all(
                panels.get(panel, {}).get(str(seed), {}).get("RATE-FLEX", {}).get(field)
                == panels.get(panel, {}).get(str(seed), {}).get("RATE-CONST", {}).get(field)
                for field in ("episodes", "physics_ticks", "actor_calls", "critic_calls", "messages", "transmitted_bits", "identity_rows")
            )
            for panel in ("iid", "safety", "keep") for seed in SEEDS for arm in ARMS
        ),
        "panel_identity_decomposition_terminal_exact": all(
            bool(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("identity_unique"))
            and bool(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("identity_schema_valid"))
            and bool(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("reward_service_cost_exact"))
            and bool(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("segment_ownership_exact"))
            and bool(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("terminal_boundary_absent"))
            for panel in ("iid", "safety", "keep") for seed in SEEDS for arm in ARMS
        ),
        "required_rate_and_diagnostic_reports_present": all(
            isinstance(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("rate_distributions"), dict)
            and all(
                key in panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("rate_distributions", {})
                for key in ("by_exposure", "by_plan_age", "by_busy_state", "by_preceding_interval", "by_role")
            )
            and all(
                isinstance(group, dict) and bool(group)
                and all(
                    isinstance(summary, dict) and RATE_DISTRIBUTION_MANDATORY_FIELDS <= set(summary)
                    for summary in group.values()
                )
                for group in panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("rate_distributions", {}).values()
            )
            and len(grid_cells.get(str(seed), {}).get(arm, {}).get("rows", ())) == 20
            and all(
                isinstance(row, dict) and GRID_ROW_MANDATORY_FIELDS <= set(row)
                for row in grid_cells.get(str(seed), {}).get(arm, {}).get("rows", ())
            )
            for panel in ("iid", "safety", "keep") for seed in SEEDS for arm in ARMS
        ),
        "nested_mandatory_reports_exact": all(
            {"n", "mean", "standard_error", "lower", "upper"}
            <= set(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("episode_return_interval", {}))
            and int(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("episode_return_interval", {}).get("n", -1))
            == int(panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("episodes", -2))
            and panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("iid_draw_filtration", {}).get(
                "draw_after_current_action"
            ) is True
            and panels.get(panel, {}).get(str(seed), {}).get(arm, {}).get("iid_draw_filtration", {}).get(
                "visible_history_action_state_reward_prior_intervals_excluded"
            ) is True
            for panel in ("iid", "safety", "keep") for seed in SEEDS for arm in ARMS
        ) and all(
            all(
                isinstance(row, dict) and SAFETY_RESPONSE_MANDATORY_FIELDS <= set(row)
                for row in safety_cells.get(str(seed), {}).get(arm, {}).get("safety_response_rows", ())
            ) for seed in SEEDS for arm in ARMS
        ) and all(
            all(
                isinstance(fact, dict) and UPDATE_FACT_MANDATORY_FIELDS <= set(fact)
                for fact in training.get(str(seed), {}).get(arm, {}).get("update_facts", ())
            )
            and all(
                isinstance(fact, dict) and TRAINING_UPDATE_WORK_MANDATORY_FIELDS <= set(fact)
                and int(fact.get("episodes", -1)) == 32
                and int(fact.get("physics_ticks", -1)) == 8192
                and int(fact.get("actor_calls", -1)) == 1392
                and int(fact.get("critic_calls", -1)) == 696
                and int(fact.get("messages", -1)) == 16384
                and int(fact.get("transmitted_bits", -1)) == 32768
                for fact in training.get(str(seed), {}).get(arm, {}).get("per_update_work_facts", ())
            )
            for seed in SEEDS for arm in ARMS
        ),
        "all_reward_and_segment_facts_exact": all(
            bool(iid_cells.get(str(seed), {}).get(arm, {}).get("reward_service_cost_exact"))
            and bool(iid_cells.get(str(seed), {}).get(arm, {}).get("segment_ownership_exact"))
            for seed in SEEDS for arm in ARMS
        ),
        "registered_work_exact": sum(
            int(training.get(str(seed), {}).get(arm, {}).get("physics_ticks", -1))
            + int(iid_cells.get(str(seed), {}).get(arm, {}).get("physics_ticks", -1))
            + int(safety_cells.get(str(seed), {}).get(arm, {}).get("physics_ticks", -1))
            + int(keep_cells.get(str(seed), {}).get(arm, {}).get("physics_ticks", -1))
            for seed in SEEDS for arm in ARMS
        ) == registered_work()["total_team_ticks"],
    }
    package_valid = not missing and all(conformance.values())
    failed_conformance = tuple(name for name, passed in conformance.items() if not passed)
    r_iid = {
        str(seed): {
            arm: float(iid_cells[str(seed)][arm]["mean_return"]) for arm in ARMS
        } for seed in SEEDS
    } if not missing else {}
    differences = tuple(
        r_iid[str(seed)]["RATE-FLEX"] - r_iid[str(seed)]["RATE-CONST"] for seed in SEEDS
    ) if r_iid else tuple(0.0 for _ in SEEDS)
    paired = student_interval(differences)
    branches = decision_branches(
        package_valid=package_valid, mark_support_ok=mark_support_ok, differences=differences,
    )
    leave_one_out = {
        str(seed): float(np.mean([value for index, value in enumerate(differences) if index != position]))
        for position, seed in enumerate(SEEDS)
    }
    return {
        "artifact_kind": "ONLGR_B2_COMPLETE_ANALYSIS", "revision": REVISION,
        "PACKAGE_VALID": package_valid, "MARK_SUPPORT_OK": mark_support_ok,
        "missing_facts": tuple(missing), "failed_conformance": failed_conformance,
        "anomalies": tuple((*missing, *failed_conformance)), "conformance": conformance,
        "support_cells": support_cells, "R_IID": r_iid,
        "paired_difference_RATE_FLEX_minus_RATE_CONST": {
            "by_seed": {str(seed): differences[index] for index, seed in enumerate(SEEDS)},
            "student_t_95_interval": paired,
            "exact_paired_sign_flip_p_value": exact_paired_sign_flip_pvalue(differences),
            "leave_one_seed_out_point_estimates": leave_one_out,
        },
        "branches": branches, "diagnostic_grids": grid_cells,
        "initialization": initialization_report(),
        "probability_jacobian_conformance": probability_jacobian_conformance(),
        "iid_seed_arm_metrics": iid_cells, "safety_seed_arm_metrics": safety_cells,
        "keep_seed_arm_metrics": keep_cells, "training_seed_arm_facts": training,
        "checkpoint_facts": checkpoints, "registered_work": registered_work(),
        "strongest_remaining_alternative": (
            "Generic finite-budget functional flexibility or optimization geometry in the larger "
            "input-dependent function class, combined with this host's reward/lease/callback geometry."
        ),
    }

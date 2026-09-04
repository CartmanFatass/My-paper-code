"""Exact policy audit and fresh paired sampled evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from fractions import Fraction
import math
from types import SimpleNamespace
from typing import Any

from .contract import CONTEXTS, K_EVAL, MARKS, TARGET_CONTEXT_ID, context_id
from .model import tensors_for_record
from .oracle import build_oracle, direct_probe, expected_tail, joint_count_probability, optimal_tail, posterior_short, tail_q
from .host import execute_policy_episode


def _torch():
    import torch
    return torch


def _context_record(context):
    link, p, cost = context
    return SimpleNamespace(link=link, reliability=p, total_cost=cost)


def _scores(scorer, pairs):
    torch = _torch()
    x = torch.stack([pair[0] for pair in pairs])
    z = torch.stack([pair[1] for pair in pairs])
    with torch.no_grad():
        values = scorer(x, z)
    if values.dtype != torch.float32 or not torch.isfinite(values).all().item():
        raise ValueError("nonfinite/non-FP32 evaluation score")
    return tuple(float(value) for value in values.tolist())


@dataclass(frozen=True)
class PolicyEvaluation:
    arm_id: str
    seed_id: str
    fold_id: int
    root_update: int
    root_actions: dict[str, str]
    root_selected_labels: dict[str, str]
    tail_periods: dict[str, dict[str, int]]
    root_scores: dict[str, dict[str, float]]
    tail_scores: dict[str, dict[str, dict[str, float]]]
    all_finite: bool
    all_unique: bool
    oracle_root_match: bool
    max_regret: float
    minimum_tail_agreement: float
    target_delta_acquisition: float | None
    direct_probe_component: float | None
    competence_pass: bool
    acquisition_pass: bool
    exact_policy_evaluations: int
    sampled_evaluation_episodes: int
    sampled_evaluation_transitions: int
    sampled_external_return_sum: float
    sampled_context_diagnostics: dict[str, dict[str, float | int]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_policy(root, tail, *, arm_id: str, seed_id: str, fold_id: int, root_update: int, sampled_episodes: int) -> PolicyEvaluation:
    oracle = build_oracle()
    roots: dict[str, str] = {}
    root_labels: dict[str, str] = {}
    tails: dict[str, dict[str, int]] = {}
    root_scores = {}
    tail_scores = {}
    unique = True
    finite = True
    regrets = []
    agreements = []
    learned_values = {}
    for context in CONTEXTS:
        link, p, cost = context
        cell = context_id(context)
        record = _context_record(context)
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in K_EVAL))
        pairs = [tensors_for_record(record, stage="root", action_probe=True, period=0, belief=0.5)]
        pairs += [tensors_for_record(record, stage="root", action_probe=False, period=period, belief=0.5) for period in K_EVAL]
        values = _scores(root, pairs)
        root_scores[cell] = dict(zip(labels, values))
        ranked = sorted((value, -index, label) for index, (label, value) in enumerate(zip(labels, values)))
        finite &= all(math.isfinite(value) for value in values)
        unique &= ranked[-1][0] != ranked[-2][0]
        selected = ranked[-1][2]
        root_labels[cell] = selected
        roots[cell] = "PROBE" if selected == "PROBE" else "IMMEDIATE"
        tails[cell] = {}
        tail_scores[cell] = {}
        agreement = Fraction(0)
        learned_tail_value = Fraction(0)
        for count in range(7):
            belief = posterior_short(link, p, count)
            pairs = [tensors_for_record(record, stage="tail", action_probe=False, period=period, belief=float(belief)) for period in K_EVAL]
            values = _scores(tail, pairs)
            tail_scores[cell][str(count)] = {str(period): value for period, value in zip(K_EVAL, values)}
            ranked = sorted((value, -index, period) for index, (period, value) in enumerate(zip(K_EVAL, values)))
            finite &= all(math.isfinite(value) for value in values)
            unique &= ranked[-1][0] != ranked[-2][0]
            selected_period = ranked[-1][2]
            tails[cell][str(count)] = selected_period
            mass = joint_count_probability("SHORT", p, count) + joint_count_probability("LONG", p, count)
            learned_tail_value += mass * expected_tail(selected_period, belief)
            agreement += mass * int(selected_period == optimal_tail(K_EVAL, belief)[0])
        baseline = oracle[cell]["baseline"]
        immediate_value = expected_tail(int(selected.split(":")[1]), Fraction(1, 2)) if selected != "PROBE" else None
        probe_value = learned_tail_value + direct_probe(cost)
        learned = probe_value if selected == "PROBE" else immediate_value
        learned_values[cell] = learned
        optimum = max(oracle[cell]["baseline"], oracle[cell]["probe_value"])
        regrets.append(optimum - learned)
        agreements.append(agreement)
    oracle_vector = {cell: row["action"] for cell, row in oracle.items()}
    oracle_match = roots == oracle_vector
    max_regret = max(regrets)
    minimum_agreement = min(agreements)
    competence = bool(finite and unique and oracle_match and max_regret <= Fraction(1, 50) and minimum_agreement >= Fraction(19, 20))
    sample = sampled_policy_diagnostics(root_labels, tails, seed_id=seed_id, fold_id=fold_id, root_update=root_update, episodes_per_context=sampled_episodes)
    return PolicyEvaluation(
        arm_id,
        seed_id,
        fold_id,
        root_update,
        roots,
        root_labels,
        tails,
        root_scores,
        tail_scores,
        finite,
        unique,
        oracle_match,
        float(max_regret),
        float(minimum_agreement),
        None,
        None,
        competence,
        False,
        len(CONTEXTS),
        len(CONTEXTS) * sampled_episodes,
        sample["transitions"],
        sample["external_return_sum"],
        sample["contexts"],
    )


def enforce_conditional_acquisition(evaluations: tuple[PolicyEvaluation, ...], *, final_root_update: int, support_limited: dict[str, bool] | None = None) -> tuple[PolicyEvaluation, ...]:
    """Expose acquisition only after both final fold policies establish seed competence."""
    final = {(item.arm_id, item.seed_id, item.fold_id): item for item in evaluations if item.root_update == final_root_update}
    support_limited = support_limited or {}
    qualified = {
        (arm, seed): not support_limited.get(seed, False) and all(final[(arm, seed, fold)].competence_pass for fold in (0, 1))
        for arm, seed, _fold in final
    }
    conditioned = []
    for item in evaluations:
        if item.root_update != final_root_update or not qualified.get((item.arm_id, item.seed_id), False):
            conditioned.append(replace(item, target_delta_acquisition=None, direct_probe_component=None, acquisition_pass=False))
        else:
            audit = audit_policy_choices(item.root_selected_labels, item.tail_periods)
            acquisition = bool(
                item.competence_pass
                and audit["root_actions"][TARGET_CONTEXT_ID] == "PROBE"
                and audit["target_delta_acquisition"] > 0
                and audit["direct_probe_component"] < 0
                and all(action == "IMMEDIATE" for cell, action in audit["root_actions"].items() if cell != TARGET_CONTEXT_ID)
            )
            conditioned.append(replace(
                item,
                target_delta_acquisition=audit["target_delta_acquisition"],
                direct_probe_component=audit["direct_probe_component"],
                acquisition_pass=acquisition,
            ))
    return tuple(conditioned)


def audit_policy_choices(root_labels, tail_periods) -> dict[str, Any]:
    oracle = build_oracle()
    root_actions = {}
    regrets = []
    agreements = []
    learned_values = {}
    for context in CONTEXTS:
        link, p, cost = context
        cell = context_id(context)
        label = root_labels[cell]
        root_actions[cell] = "PROBE" if label == "PROBE" else "IMMEDIATE"
        learned_tail = Fraction(0)
        agreement = Fraction(0)
        for count in range(7):
            belief = posterior_short(link, p, count)
            period = tail_periods[cell][str(count)]
            mass = joint_count_probability("SHORT", p, count) + joint_count_probability("LONG", p, count)
            learned_tail += mass * expected_tail(period, belief)
            agreement += mass * int(period == optimal_tail(K_EVAL, belief)[0])
        value = learned_tail + direct_probe(cost) if label == "PROBE" else expected_tail(int(label.split(":")[1]), Fraction(1, 2))
        learned_values[cell] = value
        regrets.append(max(oracle[cell]["baseline"], oracle[cell]["probe_value"]) - value)
        agreements.append(agreement)
    return {
        "root_actions": root_actions,
        "oracle_root_match": root_actions == {cell: row["action"] for cell, row in oracle.items()},
        "max_regret": float(max(regrets)),
        "minimum_tail_agreement": float(min(agreements)),
        "target_delta_acquisition": float(learned_values[TARGET_CONTEXT_ID] - oracle[TARGET_CONTEXT_ID]["baseline"]),
        "direct_probe_component": float(oracle[TARGET_CONTEXT_ID]["direct_probe"]),
    }


def sampled_policy_diagnostics(root_labels, tail_periods, *, seed_id: str, fold_id: int, root_update: int, episodes_per_context: int) -> dict[str, Any]:
    """Fresh paired environment roots; RNG keys intentionally omit arm identity."""
    total = 0.0
    transitions = 0
    diagnostics = {}
    for context in CONTEXTS:
        cell = context_id(context)
        returns = []
        probe_count = 0
        context_transitions = 0
        for index in range(episodes_per_context):
            label = root_labels[cell]
            probe = label == "PROBE"
            execution = execute_policy_episode(
                context,
                ancestry=(seed_id, fold_id, root_update),
                episode_index=index,
                root_action="PROBE" if probe else "IMMEDIATE",
                immediate_period=None if probe else int(label.split(":")[1]),
                tail_selector=(lambda count, cell=cell: tail_periods[cell][str(count)]) if probe else None,
                evaluation=True,
            )
            total += execution.external_return
            returns.append(execution.external_return)
            probe_count += int(probe)
            context_transitions += execution.transition_count
        transitions += context_transitions
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1) if len(returns) > 1 else 0.0
        half_width = 1.96 * math.sqrt(variance / len(returns))
        diagnostics[cell] = {
            "episodes": len(returns),
            "transitions": context_transitions,
            "external_return_sum": sum(returns),
            "external_return_mean": mean,
            "probe_count": probe_count,
            "probe_rate": probe_count / len(returns),
            "diagnostic_ci95_low": mean - half_width,
            "diagnostic_ci95_high": mean + half_width,
        }
    return {"external_return_sum": total, "transitions": transitions, "contexts": diagnostics}


def sampled_policy_return(root_labels, tail_periods, *, seed_id: str, fold_id: int, root_update: int, episodes_per_context: int) -> float:
    return sampled_policy_diagnostics(
        root_labels, tail_periods, seed_id=seed_id, fold_id=fold_id,
        root_update=root_update, episodes_per_context=episodes_per_context,
    )["external_return_sum"]


def validate_policy_evaluation(item: PolicyEvaluation, *, config, acquisition_eligible: bool) -> PolicyEvaluation:
    cells = {context_id(context) for context in CONTEXTS}
    if item.arm_id not in config.arms or item.seed_id not in config.seed_ids or item.fold_id not in (0, 1) or item.root_update not in config.evaluation_root_updates:
        raise ValueError("evaluation identity/progress mismatch")
    if set(item.root_scores) != cells or set(item.root_selected_labels) != cells or set(item.root_actions) != cells or set(item.tail_scores) != cells or set(item.tail_periods) != cells:
        raise ValueError("evaluation context inventory mismatch")
    finite = True
    unique = True
    for cell in cells:
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in K_EVAL))
        scores = item.root_scores[cell]
        if set(scores) != set(labels) or any(type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value) for value in scores.values()):
            raise ValueError("evaluation root score inventory mismatch")
        ranked = sorted((scores[label], -index, label) for index, label in enumerate(labels))
        unique &= ranked[-1][0] != ranked[-2][0]
        finite &= all(math.isfinite(value) for value in scores.values())
        if item.root_selected_labels[cell] != ranked[-1][2] or item.root_actions[cell] != ("PROBE" if ranked[-1][2] == "PROBE" else "IMMEDIATE"):
            raise ValueError("evaluation root choice/score mismatch")
        if set(item.tail_scores[cell]) != {str(count) for count in range(7)} or set(item.tail_periods[cell]) != {str(count) for count in range(7)}:
            raise ValueError("evaluation tail count inventory mismatch")
        for count in range(7):
            scores = item.tail_scores[cell][str(count)]
            if set(scores) != {str(period) for period in K_EVAL} or any(type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value) for value in scores.values()):
                raise ValueError("evaluation tail score inventory mismatch")
            ranked = sorted((scores[str(period)], -index, period) for index, period in enumerate(K_EVAL))
            unique &= ranked[-1][0] != ranked[-2][0]
            finite &= all(math.isfinite(value) for value in scores.values())
            if item.tail_periods[cell][str(count)] != ranked[-1][2]:
                raise ValueError("evaluation tail choice/score mismatch")
    audit = audit_policy_choices(item.root_selected_labels, item.tail_periods)
    if item.all_finite != finite or item.all_unique != unique or item.oracle_root_match != audit["oracle_root_match"]:
        raise ValueError("evaluation finite/unique/oracle summary mismatch")
    if abs(item.max_regret - audit["max_regret"]) > 1e-12 or abs(item.minimum_tail_agreement - audit["minimum_tail_agreement"]) > 1e-12:
        raise ValueError("evaluation exact competence metric mismatch")
    competent = bool(finite and unique and audit["oracle_root_match"] and audit["max_regret"] <= 1 / 50 and audit["minimum_tail_agreement"] >= 19 / 20)
    if item.competence_pass != competent:
        raise ValueError("evaluation competence predicate mismatch")
    if acquisition_eligible:
        expected_acquisition = bool(
            competent and audit["root_actions"][TARGET_CONTEXT_ID] == "PROBE"
            and audit["target_delta_acquisition"] > 0 and audit["direct_probe_component"] < 0
            and all(action == "IMMEDIATE" for cell, action in audit["root_actions"].items() if cell != TARGET_CONTEXT_ID)
        )
        if item.target_delta_acquisition != audit["target_delta_acquisition"] or item.direct_probe_component != audit["direct_probe_component"] or item.acquisition_pass != expected_acquisition:
            raise ValueError("evaluation conditional acquisition mismatch")
    elif item.target_delta_acquisition is not None or item.direct_probe_component is not None or item.acquisition_pass:
        raise ValueError("acquisition leaked before final two-fold competence")
    expected_sample = sampled_policy_diagnostics(
        item.root_selected_labels, item.tail_periods, seed_id=item.seed_id, fold_id=item.fold_id,
        root_update=item.root_update, episodes_per_context=config.sampled_evaluation_episodes,
    )
    if item.exact_policy_evaluations != len(CONTEXTS) or item.sampled_evaluation_episodes != len(CONTEXTS) * config.sampled_evaluation_episodes:
        raise ValueError("evaluation activity count mismatch")
    if item.sampled_evaluation_transitions != expected_sample["transitions"] or item.sampled_external_return_sum != expected_sample["external_return_sum"] or item.sampled_context_diagnostics != expected_sample["contexts"]:
        raise ValueError("sampled evaluation diagnostic mismatch")
    return item

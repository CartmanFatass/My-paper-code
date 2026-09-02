"""Independent odd/even exact evaluation plus paired sampled diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import math
from types import SimpleNamespace
from typing import Any

from .contract import CONTEXTS, K_EVAL, K_TRAIN, context_id
from .host import execute_episode
from .model import basis_for_record
from .oracle import build_oracle, count_mass, direct_probe, expected_tail, optimal_tail, posterior_short


def _torch():
    import torch
    return torch


def _record(context, belief=Fraction(1, 2)):
    link, reliability, cost = context
    return SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=belief)


def _score(model, matrix):
    torch = _torch()
    with torch.no_grad(): values = model(torch.stack(matrix))
    if values.dtype != torch.float32 or not torch.isfinite(values).all().item():
        raise ValueError("evaluation scores are nonfinite/non-FP32")
    return tuple(float(item) for item in values.tolist())


def _fraction_record(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


@dataclass(frozen=True)
class SupportEvaluation:
    arm_id: str
    seed_id: str
    fold_id: int
    root_update: int
    support: str
    periods: tuple[int, ...]
    root_scores: dict[str, dict[str, float]]
    tail_scores: dict[str, dict[str, dict[str, float]]]
    root_selected: dict[str, str]
    tail_selected: dict[str, dict[str, int]]
    all_scores_finite: bool
    all_choices_unique: bool
    root_vector: dict[str, str]
    oracle_root_vector: dict[str, str]
    root_hamming: int
    maximum_expected_regret: dict[str, int]
    minimum_tail_agreement: dict[str, int]
    competence: bool
    odd_near: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self); value["periods"] = list(self.periods); return value

    @property
    def regret_fraction(self) -> Fraction:
        return Fraction(self.maximum_expected_regret["numerator"], self.maximum_expected_regret["denominator"])

    @property
    def agreement_fraction(self) -> Fraction:
        return Fraction(self.minimum_tail_agreement["numerator"], self.minimum_tail_agreement["denominator"])


@dataclass(frozen=True)
class CheckpointEvaluation:
    arm_id: str
    seed_id: str
    fold_id: int
    root_update: int
    odd: SupportEvaluation
    even: SupportEvaluation
    sampled: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"arm_id": self.arm_id, "seed_id": self.seed_id, "fold_id": self.fold_id, "root_update": self.root_update, "odd": self.odd.to_dict(), "even": self.even.to_dict(), "sampled": self.sampled}


def evaluate_support(root, tail, *, arm_id: str, seed_id: str, fold_id: int, root_update: int, periods: tuple[int, ...]) -> SupportEvaluation:
    if periods == K_TRAIN: support = "odd"
    elif periods == K_EVAL: support = "even"
    else: raise ValueError("evaluation support drift")
    oracle = build_oracle(periods)
    root_scores, tail_scores, root_selected, tail_selected, root_vector = {}, {}, {}, {}, {}
    finite = unique = True
    regrets, agreements = [], []
    for context in CONTEXTS:
        link, reliability, cost = context; cell = context_id(context); record = _record(context)
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in periods))
        root_features = [basis_for_record(record, stage="root", period=0, action_probe=True)] + [basis_for_record(record, stage="root", period=period, action_probe=False) for period in periods]
        values = _score(root, root_features); root_scores[cell] = dict(zip(labels, values))
        ranked = sorted((value, -index, label) for index, (label, value) in enumerate(zip(labels, values)))
        unique &= ranked[-1][0] != ranked[-2][0]; finite &= all(math.isfinite(value) for value in values)
        selected = ranked[-1][2]; root_selected[cell] = selected; root_vector[cell] = "PROBE" if selected == "PROBE" else "IMMEDIATE"
        tail_scores[cell], tail_selected[cell] = {}, {}
        learned_probe, agreement = Fraction(0), Fraction(0)
        for count in range(7):
            belief = posterior_short(link, reliability, count); tail_record = _record(context, belief)
            candidates = [basis_for_record(tail_record, stage="tail", period=period) for period in periods]
            tail_values = _score(tail, candidates)
            tail_scores[cell][str(count)] = {str(period): value for period, value in zip(periods, tail_values)}
            ranked_tail = sorted((value, -index, period) for index, (period, value) in enumerate(zip(periods, tail_values)))
            unique &= ranked_tail[-1][0] != ranked_tail[-2][0]; finite &= all(math.isfinite(value) for value in tail_values)
            selected_period = ranked_tail[-1][2]; tail_selected[cell][str(count)] = selected_period
            mass = count_mass("SHORT", reliability, count) + count_mass("LONG", reliability, count)
            learned_probe += mass * expected_tail(selected_period, belief)
            agreement += mass * int(selected_period == optimal_tail(periods, belief)[0])
        learned_probe += direct_probe(cost)
        learned = learned_probe if selected == "PROBE" else expected_tail(int(selected.split(":")[1]), Fraction(1, 2))
        regrets.append(max(oracle[cell]["baseline"], oracle[cell]["probe_value"]) - learned); agreements.append(agreement)
    oracle_vector = {cell: row["action"] for cell, row in oracle.items()}
    hamming = sum(root_vector[cell] != oracle_vector[cell] for cell in oracle_vector)
    regret, agreement = max(regrets), min(agreements)
    competence = bool(finite and unique and hamming == 0 and regret <= Fraction(1, 50) and agreement >= Fraction(19, 20))
    near = bool(support == "odd" and finite and unique and hamming <= 1 and regret <= Fraction(1, 25) and agreement >= Fraction(9, 10))
    return SupportEvaluation(arm_id, seed_id, fold_id, root_update, support, periods, root_scores, tail_scores, root_selected, tail_selected, finite, unique, root_vector, oracle_vector, hamming, _fraction_record(regret), _fraction_record(agreement), competence, near)


def sampled_diagnostics(even: SupportEvaluation, *, episodes_per_context: int) -> dict[str, Any]:
    contexts = {}; total_transitions = 0
    for context in CONTEXTS:
        cell = context_id(context); values = []; probe_count = 0; transitions = 0
        for index in range(episodes_per_context):
            label = even.root_selected[cell]; probe = label == "PROBE"
            execution = execute_episode(context, ancestry=(even.seed_id, even.fold_id, even.root_update), episode_index=index, root_action="PROBE" if probe else "IMMEDIATE", support=K_EVAL, immediate_period=None if probe else int(label.split(":")[1]), tail_selector=(lambda count, cell=cell: even.tail_selected[cell][str(count)]) if probe else None, evaluation=True)
            values.append(execution.external_return); probe_count += int(probe); transitions += execution.transition_count
        contexts[cell] = {"episodes": len(values), "transitions": transitions, "return_sum": sum(values), "probe_count": probe_count}
        total_transitions += transitions
    return {"episodes": len(CONTEXTS) * episodes_per_context, "transitions": total_transitions, "contexts": contexts}


def evaluate_checkpoint(root, tail, *, arm_id: str, seed_id: str, fold_id: int, root_update: int, sampled_episodes: int) -> CheckpointEvaluation:
    odd = evaluate_support(root, tail, arm_id=arm_id, seed_id=seed_id, fold_id=fold_id, root_update=root_update, periods=K_TRAIN)
    even = evaluate_support(root, tail, arm_id=arm_id, seed_id=seed_id, fold_id=fold_id, root_update=root_update, periods=K_EVAL)
    return CheckpointEvaluation(arm_id, seed_id, fold_id, root_update, odd, even, sampled_diagnostics(even, episodes_per_context=sampled_episodes))


def validate_support_evaluation(item: SupportEvaluation) -> SupportEvaluation:
    periods = K_TRAIN if item.support == "odd" else K_EVAL if item.support == "even" else None
    if periods is None or item.periods != periods:
        raise ValueError("support evaluation identity mismatch")
    cells = {context_id(context) for context in CONTEXTS}
    mappings = (item.root_scores, item.tail_scores, item.root_selected, item.tail_selected, item.root_vector, item.oracle_root_vector)
    if any(set(mapping) != cells for mapping in mappings):
        raise ValueError("support evaluation context inventory mismatch")
    oracle = build_oracle(periods); finite = unique = True; regrets = []; agreements = []
    for context in CONTEXTS:
        link, reliability, cost = context; cell = context_id(context)
        labels = ("PROBE", *(f"IMMEDIATE:{period}" for period in periods)); scores = item.root_scores[cell]
        if set(scores) != set(labels) or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) for value in scores.values()):
            raise ValueError("root score inventory mismatch")
        ranked = sorted((scores[label], -index, label) for index, label in enumerate(labels)); unique &= ranked[-1][0] != ranked[-2][0]; finite &= all(math.isfinite(v) for v in scores.values())
        selected = ranked[-1][2]
        if item.root_selected[cell] != selected or item.root_vector[cell] != ("PROBE" if selected == "PROBE" else "IMMEDIATE"):
            raise ValueError("root score/choice mismatch")
        learned_probe, agreement = Fraction(0), Fraction(0)
        if set(item.tail_scores[cell]) != {str(count) for count in range(7)} or set(item.tail_selected[cell]) != {str(count) for count in range(7)}:
            raise ValueError("tail count inventory mismatch")
        for count in range(7):
            scores = item.tail_scores[cell][str(count)]
            if set(scores) != {str(period) for period in periods} or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) for value in scores.values()):
                raise ValueError("tail score inventory mismatch")
            ranked_tail = sorted((scores[str(period)], -index, period) for index, period in enumerate(periods)); unique &= ranked_tail[-1][0] != ranked_tail[-2][0]; finite &= all(math.isfinite(v) for v in scores.values())
            selected_period = ranked_tail[-1][2]
            if item.tail_selected[cell][str(count)] != selected_period: raise ValueError("tail score/choice mismatch")
            belief = posterior_short(link, reliability, count); mass = count_mass("SHORT", reliability, count) + count_mass("LONG", reliability, count)
            learned_probe += mass * expected_tail(selected_period, belief); agreement += mass * int(selected_period == optimal_tail(periods, belief)[0])
        learned_probe += direct_probe(cost)
        learned = learned_probe if selected == "PROBE" else expected_tail(int(selected.split(":")[1]), Fraction(1, 2))
        regrets.append(max(oracle[cell]["baseline"], oracle[cell]["probe_value"]) - learned); agreements.append(agreement)
    oracle_vector = {cell: row["action"] for cell, row in oracle.items()}; hamming = sum(item.root_vector[cell] != oracle_vector[cell] for cell in cells); regret = max(regrets); agreement = min(agreements)
    competence = bool(finite and unique and hamming == 0 and regret <= Fraction(1, 50) and agreement >= Fraction(19, 20))
    near = bool(item.support == "odd" and finite and unique and hamming <= 1 and regret <= Fraction(1, 25) and agreement >= Fraction(9, 10))
    if item.oracle_root_vector != oracle_vector or item.all_scores_finite != finite or item.all_choices_unique != unique or item.root_hamming != hamming or item.regret_fraction != regret or item.agreement_fraction != agreement or item.competence != competence or item.odd_near != near:
        raise ValueError("support evaluation exact summary mismatch")
    return item

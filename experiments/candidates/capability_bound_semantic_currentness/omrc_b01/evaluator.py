"""Adaptation-free, evaluator-only diagnostics for CBSC-OMRC-B01.

This module is the only B0 runtime surface that turns the private evaluator
view of an :class:`EpisodeTape` into validity, oracle, regret, or motif
records.  It deliberately accepts chosen actions rather than model objects or
observations, keeping evaluator truth outside the learner data path.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from typing import Any, Sequence

from .contract import Action, OPPORTUNITY_COUNT
from .tapes import EpisodeTape


class EvaluationError(ValueError):
    """Raised when an action record cannot be evaluated on a frozen tape."""


def _action(value: int | Action) -> Action:
    try:
        action = value if isinstance(value, Action) else Action(value)
    except (TypeError, ValueError) as exc:
        raise EvaluationError("evaluation action is outside the frozen action set") from exc
    if action is Action.WAIT:
        raise EvaluationError("WAIT is illegal at evaluator decision rows")
    return action


def _fraction_record(value: Fraction) -> dict[str, int | float]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "float": float(value),
    }


def evaluate_episode(
    tape: EpisodeTape, decision_actions: Sequence[int | Action]
) -> dict[str, Any]:
    """Recompute exact return, unique-oracle regret, and action diagnostics."""

    if not isinstance(tape, EpisodeTape):
        raise EvaluationError("evaluation requires an EpisodeTape")
    if len(decision_actions) != OPPORTUNITY_COUNT:
        raise EvaluationError("evaluation requires exactly 24 decision actions")
    evaluator = tape.evaluator()
    chosen_return = Fraction(0)
    oracle_return = Fraction(0)
    counts: Counter[str] = Counter()
    decisions: list[dict[str, Any]] = []
    for opportunity, raw_action in enumerate(decision_actions):
        action = _action(raw_action)
        truth = evaluator.truth(opportunity)
        oracle = truth.oracle_action
        ledger = evaluator.ledger(opportunity, action)
        oracle_ledger = evaluator.ledger(opportunity, oracle)
        chosen_return += ledger.undiscounted_total
        oracle_return += oracle_ledger.undiscounted_total
        counts["oracle_action_correct"] += int(action is oracle)
        counts["invalid_serve"] += int(action is Action.SERVE and not truth.valid)
        counts["missed_serve"] += int(oracle is Action.SERVE and action is not Action.SERVE)
        counts["unnecessary_refresh"] += int(
            action is Action.REFRESH and oracle is not Action.REFRESH
        )
        counts["missed_refresh"] += int(
            oracle is Action.REFRESH and action is not Action.REFRESH
        )
        counts["inactive_fallback"] += int(
            not truth.decision.request_active and action is Action.SAFE_FALLBACK
        )
        decisions.append(
            {
                "opportunity_index": opportunity,
                "action": action.name,
                "oracle_action": oracle.name,
                "valid": truth.valid,
                "request_active": truth.decision.request_active,
                "decision_reward": _fraction_record(ledger.decision_reward),
                "settlement_reward": _fraction_record(ledger.settlement_reward),
                "regret": _fraction_record(
                    oracle_ledger.undiscounted_total - ledger.undiscounted_total
                ),
                "motif_family": truth.motif_family,
                "motif_side": truth.motif_side,
                "designated_comparison": truth.designated_comparison,
            }
        )
    regret = oracle_return - chosen_return
    return {
        "identity": {
            "run_name": tape.identity.run_name,
            "seed": tape.identity.seed,
            "split": tape.identity.split,
            "episode_id": tape.identity.episode_id,
        },
        "return": _fraction_record(chosen_return),
        "oracle_return": _fraction_record(oracle_return),
        "oracle_regret": _fraction_record(regret),
        "action_counts": {action.name: sum(d["action"] == action.name for d in decisions) for action in Action if action is not Action.WAIT},
        "diagnostic_counts": {
            name: counts[name]
            for name in (
                "oracle_action_correct",
                "invalid_serve",
                "missed_serve",
                "unnecessary_refresh",
                "missed_refresh",
                "inactive_fallback",
            )
        },
        "decisions": decisions,
    }


def aggregate_evaluations(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate without dropping the individual held-out episode records."""

    if not records:
        raise EvaluationError("at least one evaluation record is required")
    totals = Counter()
    action_totals = Counter()
    for record in records:
        if len(record.get("decisions", ())) != OPPORTUNITY_COUNT:
            raise EvaluationError("an evaluation record is incomplete")
        totals.update(record["diagnostic_counts"])
        action_totals.update(record["action_counts"])
    return {
        "complete": True,
        "episode_count": len(records),
        "decision_count": len(records) * OPPORTUNITY_COUNT,
        "mean_return": sum(record["return"]["float"] for record in records) / len(records),
        "mean_oracle_regret": sum(
            record["oracle_regret"]["float"] for record in records
        )
        / len(records),
        "action_counts": dict(action_totals),
        "diagnostic_counts": dict(totals),
        "episodes": list(records),
    }

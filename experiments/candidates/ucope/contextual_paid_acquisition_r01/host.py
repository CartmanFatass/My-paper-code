"""Finite host and primitive-ledger construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Mapping

from .contract import K_TRAIN, MARK_COUNT, SEED_SLOTS, TOTAL_COSTS, as_fraction, context_id, validate_context
from .oracle import posterior_short, tail_energy, tail_q, tail_time
from .rng import bernoulli
from .schema import PlanEntry, PrimitiveLedger


@dataclass(frozen=True)
class EpisodeRecord:
    index: int
    seed_slot: str
    context_id: str
    link: str
    reliability: str
    total_cost: str
    regime: str
    actual_marks: tuple[str, ...]
    displayed_regime: str
    displayed_marks: tuple[str, ...]
    displayed_short_count: int
    root_action: str
    period: int
    primitive_ledger: PrimitiveLedger
    tail_return: float
    immediate_return: float
    unshaped_return: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _marks(regime: str, reliability: Fraction, namespace: str, seed_slot: str, index: int) -> tuple[str, ...]:
    if regime not in ("SHORT", "LONG"):
        raise ValueError("mark regime must be SHORT or LONG")
    probability_short = reliability if regime == "SHORT" else 1 - reliability
    return tuple(
        "SHORT" if bernoulli(float(probability_short), namespace, seed_slot, index, mark) else "LONG"
        for mark in range(MARK_COUNT)
    )


def primitive_probe_components(actual_marks: tuple[str, ...], total_cost: Fraction) -> tuple[Fraction, Fraction, Fraction]:
    if len(actual_marks) != MARK_COUNT or any(mark not in ("SHORT", "LONG") for mark in actual_marks):
        raise ValueError("actual tape must contain exactly six binary marks")
    if total_cost not in TOTAL_COSTS:
        raise ValueError("probe cost outside frozen population")
    service = Fraction(2, 25) * Fraction(actual_marks.count("SHORT"), MARK_COUNT)
    time = -Fraction(3, 100)
    energy = -(total_cost - Fraction(3, 100))
    return service, time, energy


def simulate_episode(
    seed_slot: str,
    context: Mapping[str, Any],
    entry: PlanEntry,
    regime: str,
    display_regime: str | None = None,
) -> EpisodeRecord:
    """Materialize one deterministic episode from an exogenous indexed plan entry."""
    if regime not in ("SHORT", "LONG"):
        raise ValueError("regime must be SHORT or LONG")
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown frozen seed slot")
    validate_context(context)
    if not isinstance(entry, PlanEntry) or type(entry.index) is not int or entry.index < 0:
        raise ValueError("malformed plan entry")
    if context.get("link") not in ("LINKED", "SEVERED"):
        raise ValueError("unknown linkage")
    if entry.root_action not in ("PROBE", "IMMEDIATE"):
        raise ValueError("unknown root action")
    if type(entry.period) is not int or not 1 <= entry.period <= 9:
        raise ValueError("period outside 1..9")
    p = as_fraction(context["reliability"])
    cost = as_fraction(context["total_cost"])
    cell_id = context_id(context)
    actual_marks = _marks(regime, p, "mark-uniform", seed_slot, entry.index)
    if context["link"] == "LINKED":
        if display_regime is not None and display_regime != regime:
            raise ValueError("LINKED display regime must equal actual regime")
        displayed_regime = regime
        displayed_marks = actual_marks
    else:
        if display_regime not in ("SHORT", "LONG"):
            raise ValueError("SEVERED materialization requires an independent balanced display regime")
        displayed_regime = display_regime
        displayed_marks = _marks(displayed_regime, p, "display-mark", seed_slot, entry.index)
    displayed_count = displayed_marks.count("SHORT")
    if entry.root_action == "PROBE":
        probe_service, probe_time, probe_energy = primitive_probe_components(actual_marks, cost)
    else:
        probe_service = probe_time = probe_energy = Fraction(0)
    service = 1.0 if bernoulli(float(tail_q(regime, entry.period)), "tail-service", seed_slot, entry.index, entry.period) else 0.0
    time = float(tail_time(entry.period))
    energy = float(tail_energy(entry.period))
    tail_value = service + time + energy
    ledger = PrimitiveLedger(
        tail_service=service,
        tail_time=time,
        tail_energy=energy,
        probe_service=float(probe_service),
        probe_time=float(probe_time),
        probe_energy=float(probe_energy),
        executed_probe_count=1 if entry.root_action == "PROBE" else 0,
        executed_probe_mark_count=MARK_COUNT if entry.root_action == "PROBE" else 0,
        executed_probe_time_units=2 if entry.root_action == "PROBE" else 0,
        executed_tail_commit_count=1,
        executed_tail_period_units=entry.period,
    )
    unshaped = ledger.total
    return EpisodeRecord(
        index=entry.index,
        seed_slot=seed_slot,
        context_id=cell_id,
        link=str(context["link"]),
        reliability=str(p),
        total_cost=str(cost),
        regime=regime,
        actual_marks=actual_marks,
        displayed_regime=displayed_regime,
        displayed_marks=displayed_marks,
        displayed_short_count=displayed_count,
        root_action=entry.root_action,
        period=entry.period,
        primitive_ledger=ledger,
        tail_return=tail_value,
        immediate_return=tail_value if entry.root_action == "IMMEDIATE" else 0.0,
        unshaped_return=unshaped,
    )


def belief_for_record(record: Mapping[str, Any]) -> Fraction:
    required = {"link", "reliability", "displayed_short_count"}
    if not isinstance(record, Mapping) or not required <= set(record):
        raise ValueError("belief record missing required fields")
    link = record["link"]
    if link == "SEVERED":
        return Fraction(1, 2)
    if link != "LINKED":
        raise ValueError("unknown linkage")
    p = as_fraction(record["reliability"])
    count = record["displayed_short_count"]
    if type(count) is not int or not 0 <= count <= 6:
        raise ValueError("displayed count outside 0..6")
    return posterior_short(p, count)


def validate_episode_record(record: EpisodeRecord) -> EpisodeRecord:
    if not isinstance(record, EpisodeRecord):
        raise ValueError("episode must be an EpisodeRecord")
    if record.root_action not in ("PROBE", "IMMEDIATE") or record.period not in K_TRAIN:
        raise ValueError("episode action/period outside behavior law")
    if len(record.actual_marks) != MARK_COUNT or len(record.displayed_marks) != MARK_COUNT:
        raise ValueError("episode mark-count drift")
    if any(mark not in ("SHORT", "LONG") for mark in (*record.actual_marks, *record.displayed_marks)):
        raise ValueError("episode mark alphabet drift")
    ledger = record.primitive_ledger
    expected_probe = 1 if record.root_action == "PROBE" else 0
    if (ledger.executed_probe_count, ledger.executed_probe_mark_count, ledger.executed_probe_time_units) != (expected_probe, MARK_COUNT * expected_probe, 2 * expected_probe):
        raise ValueError("probe event counters do not reconcile")
    if ledger.executed_tail_commit_count != 1 or ledger.executed_tail_period_units != record.period:
        raise ValueError("tail event counters do not reconcile")
    if abs(ledger.tail_total - record.tail_return) > 1e-12 or abs(ledger.total - record.unshaped_return) > 1e-12:
        raise ValueError("primitive ledger return reconciliation mismatch")
    if record.root_action == "IMMEDIATE" and any((ledger.probe_service, ledger.probe_time, ledger.probe_energy)):
        raise ValueError("immediate action executed probe primitives")
    return record

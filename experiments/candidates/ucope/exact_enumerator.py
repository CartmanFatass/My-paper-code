"""Exact 16-history UCOPE count-state discriminator.

All arithmetic is rational.  This candidate-local module performs no training,
task-return rollout, acquisition, retirement, or partner adaptation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from fractions import Fraction
from itertools import product
import json


S = "S"
L = "L"
PERIODS = (S, L)


class Terminal(str, Enum):
    PASS = "PASS_NARROW_COUNT_STATE_RELEVANCE"
    STOP = "STOP_OR_PARK_COUNT_INFORMATION_ROUTE"


@dataclass(frozen=True)
class NominalPeriod:
    name: str
    effective: str
    duration: int
    execution_law: bytes


@dataclass(frozen=True)
class Trial:
    index: int
    cell: str
    limit: int
    forced_nominal: str | None


@dataclass(frozen=True)
class HazardTable:
    s_given_s: Fraction
    s_given_l: Fraction
    l_given_s: Fraction
    l_given_l: Fraction

    def probability(self, theta: str, period: str) -> Fraction:
        return {
            (S, S): self.s_given_s,
            (S, L): self.s_given_l,
            (L, S): self.l_given_s,
            (L, L): self.l_given_l,
        }[(theta, period)]


@dataclass(frozen=True)
class Family:
    version: str
    cells: tuple[str, str]
    weights: tuple[Fraction, Fraction]
    nominals: tuple[NominalPeriod, ...]
    trials: tuple[Trial, ...]
    structural_support: tuple[tuple[str, str], ...]
    hazards: HazardTable
    prior_s: Fraction
    horizon: int
    persistent_theta: bool

    def nominal(self, name: str) -> NominalPeriod:
        return next(item for item in self.nominals if item.name == name)


@dataclass(frozen=True)
class Ledger:
    version: str
    opportunities: tuple[int, int, int, int]
    hits: tuple[int, int, int, int]

    @classmethod
    def empty(cls, version: str) -> "Ledger":
        return cls(version, (0, 0, 0, 0), (0, 0, 0, 0))


@dataclass(frozen=True)
class Row:
    bits: tuple[int, int, int, int]
    outcomes: tuple[str | None, ...]
    ledger: Ledger
    rho: Fraction
    hazard_s: Fraction
    hazard_l: Fraction
    ucope_s: Fraction
    ucope_l: Fraction
    cb_auc_s: Fraction
    cb_auc_l: Fraction
    cb_auc_action: str
    sg_rate_action: str
    action: str
    expected_auc: Fraction
    margin: Fraction
    prior_probability: Fraction


@dataclass(frozen=True)
class AuditResult:
    terminal: Terminal
    rows: tuple[Row, ...]
    expected_ucope_auc: Fraction
    expected_cb_auc: Fraction
    delta_auc: Fraction
    invariants: tuple[tuple[str, bool], ...]

    def to_bytes(self) -> bytes:
        payload = {
            "delta_auc": _fraction(self.delta_auc),
            "expected_cb_auc": _fraction(self.expected_cb_auc),
            "expected_ucope_auc": _fraction(self.expected_ucope_auc),
            "invariants": {name: passed for name, passed in self.invariants},
            "rows": [_row_payload(row) for row in self.rows],
            "terminal": self.terminal.value,
        }
        return json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")


def build_family(
    *,
    cells: tuple[str, str] = ("c1", "c2"),
    homogeneous_hazards: bool = False,
    split_long_alias: bool = True,
) -> Family:
    half = Fraction(1, 2)
    hazards = (
        HazardTable(half, half, half, half)
        if homogeneous_hazards
        else HazardTable(
            Fraction(9, 10),
            Fraction(1, 10),
            Fraction(1, 10),
            Fraction(9, 10),
        )
    )
    long_law = b"effective-long-execution-law"
    nominals = (
        NominalPeriod("s", S, 1, b"effective-short-execution-law"),
        NominalPeriod("ell", L, 2, long_law),
        NominalPeriod("ell_prime", L, 2, long_law),
    )
    long_trials = ("ell", "ell_prime") if split_long_alias else ("ell", "ell")
    trials = (
        Trial(1, cells[0], 3, "s"),
        Trial(2, cells[1], 3, "s"),
        Trial(3, cells[0], 3, long_trials[0]),
        Trial(4, cells[1], 3, long_trials[1]),
        Trial(5, cells[0], 3, None),
    )
    support = tuple((period, cell) for period in PERIODS for cell in cells)
    return Family(
        version="ucope-family-v1",
        cells=cells,
        weights=(half, half),
        nominals=nominals,
        trials=trials,
        structural_support=support,
        hazards=hazards,
        prior_s=half,
        horizon=3,
        persistent_theta=True,
    )


def validate_family(family: Family) -> tuple[str, ...]:
    issues: list[str] = []
    if not family.version or len(set(family.cells)) != 2:
        issues.append("family version and two anonymous cells must be fixed")
    if family.weights != (Fraction(1, 2), Fraction(1, 2)):
        issues.append("cell weights must both equal 1/2")
    roster = tuple((item.name, item.effective, item.duration) for item in family.nominals)
    if roster != (("s", S, 1), ("ell", L, 2), ("ell_prime", L, 2)):
        issues.append("effective-period quotient must be {s}->S, {ell,ell_prime}->L")
    elif family.nominal("ell").execution_law != family.nominal("ell_prime").execution_law:
        issues.append("ell and ell_prime are not execution-law aliases")
    expected_trials = (
        (1, family.cells[0], 3, "s"),
        (2, family.cells[1], 3, "s"),
        (3, family.cells[0], 3, family.trials[2].forced_nominal),
        (4, family.cells[1], 3, family.trials[3].forced_nominal),
        (5, family.cells[0], 3, None),
    )
    actual_trials = tuple(
        (trial.index, trial.cell, trial.limit, trial.forced_nominal)
        for trial in family.trials
    )
    if actual_trials != expected_trials:
        issues.append("five-trial pre-outcome tape is malformed")
    long_names = (family.trials[2].forced_nominal, family.trials[3].forced_nominal)
    if any(name not in ("ell", "ell_prime") for name in long_names):
        issues.append("long trials must use only registered aliases")
    expected_support = tuple(
        (period, cell) for period in PERIODS for cell in family.cells
    )
    if family.structural_support != expected_support:
        issues.append("Qstr must be the complete structural-only support table")
    if family.prior_s != Fraction(1, 2) or family.horizon != 3:
        issues.append("prior and physical horizon are not frozen")
    if family.persistent_theta is not True:
        issues.append("Theta must persist through the five-trial block")
    for theta in PERIODS:
        for period in PERIODS:
            value = family.hazards.probability(theta, period)
            if value < 0 or value > 1:
                issues.append("hazards must lie in [0,1]")
    return tuple(issues)


def update_ledger(
    family: Family,
    ledger: Ledger,
    trial: Trial,
    observed_hit: bool | None,
) -> Ledger:
    """Apply one immutable, version-closed observation; None is censoring."""

    if ledger.version != family.version:
        raise ValueError("ledger/family version mismatch")
    if trial.forced_nominal is None:
        raise ValueError("the choice trial cannot update the forced ledger")
    nominal = family.nominal(trial.forced_nominal)
    if observed_hit is None:
        return ledger
    if type(observed_hit) is not bool:
        raise TypeError("observed_hit must be bool or None")
    if nominal.duration > trial.limit or (
        nominal.effective,
        trial.cell,
    ) not in family.structural_support:
        return ledger
    slot = _slot(family, nominal.effective, trial.cell)
    opportunities, hits = list(ledger.opportunities), list(ledger.hits)
    opportunities[slot] += 1
    hits[slot] += int(observed_hit)
    return Ledger(ledger.version, tuple(opportunities), tuple(hits))


def posterior(family: Family, ledger: Ledger, *, independent_redraw: bool = False) -> Fraction:
    if ledger.version != family.version:
        raise ValueError("ledger/family version mismatch")
    if independent_redraw:
        return family.prior_s
    likelihood_s = _likelihood(family, ledger, S)
    likelihood_l = _likelihood(family, ledger, L)
    numerator = family.prior_s * likelihood_s
    denominator = numerator + (1 - family.prior_s) * likelihood_l
    if denominator == 0:
        raise ValueError("history has zero probability under both latent states")
    return numerator / denominator


def enumerate_histories(
    family: Family,
    *,
    independent_redraw: bool = False,
    history_order: tuple[tuple[int, int, int, int], ...] | None = None,
) -> tuple[Row, ...]:
    issues = validate_family(family)
    if issues:
        raise ValueError("; ".join(issues))
    histories = history_order or tuple(product((0, 1), repeat=4))
    rows = [_evaluate_history(family, bits, independent_redraw) for bits in histories]
    return tuple(sorted(rows, key=lambda row: row.bits))


def run_registered_audit() -> AuditResult:
    family = build_family()
    rows = enumerate_histories(family)
    h_s = _find(rows, (1, 1, 0, 0))
    h_l = _find(rows, (0, 0, 1, 1))
    expected = sum(row.prior_probability * row.expected_auc for row in rows)
    expected_cb = sum(
        row.prior_probability
        * (row.cb_auc_s if row.cb_auc_action == S else row.cb_auc_l)
        for row in rows
    )

    homogeneous_rows = enumerate_histories(build_family(homogeneous_hazards=True))
    redraw_rows = enumerate_histories(family, independent_redraw=True)
    merged_rows = enumerate_histories(build_family(split_long_alias=False))
    reversed_rows = enumerate_histories(
        family, history_order=tuple(reversed(tuple(product((0, 1), repeat=4))))
    )
    renamed_rows = enumerate_histories(build_family(cells=("anon_b", "anon_a")))

    ledger = Ledger.empty(family.version)
    censored = update_ledger(family, ledger, family.trials[0], None)
    mismatch_closed = False
    try:
        update_ledger(family, Ledger.empty("wrong-version"), family.trials[0], True)
    except ValueError:
        mismatch_closed = True

    invariants = (
        ("effective_period_quotient", validate_family(family) == ()),
        ("matched_history_h_s", h_s.action == S and h_s.rho == Fraction(6561, 6562)),
        ("matched_history_h_l", h_l.action == L and h_l.rho == Fraction(1, 6562)),
        ("h_s_margin", h_s.margin == Fraction(11153, 6562)),
        ("h_l_margin", h_l.margin == Fraction(4591, 6562)),
        ("cb_auc_matched_actions", h_s.cb_auc_action == S and h_l.cb_auc_action == S),
        ("exact_expected_auc", expected == Fraction(26571, 20000)),
        ("exact_delta_auc", expected - expected_cb == Fraction(6571, 20000)),
        ("homogeneous_boundary", _boundary_zero(homogeneous_rows)),
        ("independent_redraw_boundary", _boundary_zero(redraw_rows)),
        ("alias_split_merge", _signatures(rows) == _signatures(merged_rows)),
        ("censor_is_unknown", censored == ledger),
        ("pre_outcome_tape", all("outcome" not in field.name for field in fields(Trial))),
        ("state_clone_order", _signatures(rows) == _signatures(reversed_rows)),
        ("recurrence_version_closure", family.persistent_theta and mismatch_closed),
        ("partner_label_permutation", _signatures(rows) == _signatures(renamed_rows)),
    )
    passed = all(value for _, value in invariants)
    return AuditResult(
        terminal=Terminal.PASS if passed else Terminal.STOP,
        rows=rows,
        expected_ucope_auc=expected,
        expected_cb_auc=expected_cb,
        delta_auc=expected - expected_cb,
        invariants=invariants,
    )


def _evaluate_history(
    family: Family,
    bits: tuple[int, int, int, int],
    independent_redraw: bool,
) -> Row:
    if len(bits) != 4 or any(bit not in (0, 1) for bit in bits):
        raise ValueError("history must contain four binary outcomes")
    ledger = Ledger.empty(family.version)
    for trial, bit in zip(family.trials[:4], bits):
        ledger = update_ledger(family, ledger, trial, bool(bit))
    rho = posterior(family, ledger, independent_redraw=independent_redraw)
    hazard_s = rho * family.hazards.s_given_s + (1 - rho) * family.hazards.l_given_s
    hazard_l = rho * family.hazards.s_given_l + (1 - rho) * family.hazards.l_given_l
    ucope_s, ucope_l = 2 * hazard_s, hazard_l
    action = S if ucope_s >= ucope_l else L
    prior_hazard_s = (
        family.prior_s * family.hazards.s_given_s
        + (1 - family.prior_s) * family.hazards.l_given_s
    )
    prior_hazard_l = (
        family.prior_s * family.hazards.s_given_l
        + (1 - family.prior_s) * family.hazards.l_given_l
    )
    cb_s, cb_l = 2 * prior_hazard_s, prior_hazard_l
    cb_action = S if cb_s >= cb_l else L
    sg_rate_action = S if hazard_s >= hazard_l else L
    selected, other = (ucope_s, ucope_l) if action == S else (ucope_l, ucope_s)
    return Row(
        bits=bits,
        outcomes=tuple(trial.cell if bit else None for trial, bit in zip(family.trials, bits)),
        ledger=ledger,
        rho=rho,
        hazard_s=hazard_s,
        hazard_l=hazard_l,
        ucope_s=ucope_s,
        ucope_l=ucope_l,
        cb_auc_s=cb_s,
        cb_auc_l=cb_l,
        cb_auc_action=cb_action,
        sg_rate_action=sg_rate_action,
        action=action,
        expected_auc=selected,
        margin=selected - other,
        prior_probability=_prior_probability(family, ledger),
    )


def _likelihood(family: Family, ledger: Ledger, theta: str) -> Fraction:
    value = Fraction(1)
    for period in PERIODS:
        probability = family.hazards.probability(theta, period)
        for cell in family.cells:
            slot = _slot(family, period, cell)
            hits = ledger.hits[slot]
            opportunities = ledger.opportunities[slot]
            value *= probability**hits * (1 - probability) ** (opportunities - hits)
    return value


def _prior_probability(family: Family, ledger: Ledger) -> Fraction:
    return (
        family.prior_s * _likelihood(family, ledger, S)
        + (1 - family.prior_s) * _likelihood(family, ledger, L)
    )


def _slot(family: Family, period: str, cell: str) -> int:
    return PERIODS.index(period) * 2 + family.cells.index(cell)


def _find(rows: tuple[Row, ...], bits: tuple[int, int, int, int]) -> Row:
    return next(row for row in rows if row.bits == bits)


def _boundary_zero(rows: tuple[Row, ...]) -> bool:
    expected = sum(row.prior_probability * row.expected_auc for row in rows)
    return all(row.action == S for row in rows) and expected == Fraction(1)


def _signatures(rows: tuple[Row, ...]) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            row.bits,
            row.ledger.opportunities,
            row.ledger.hits,
            row.rho,
            row.hazard_s,
            row.hazard_l,
            row.action,
            row.expected_auc,
        )
        for row in rows
    )


def _row_payload(row: Row) -> dict[str, object]:
    return {
        "CB_AUC": {S: _fraction(row.cb_auc_s), L: _fraction(row.cb_auc_l)},
        "CB_AUC_action": row.cb_auc_action,
        "E": list(row.ledger.opportunities),
        "N": list(row.ledger.hits),
        "SG_RATE_action": row.sg_rate_action,
        "UCOPE": {S: _fraction(row.ucope_s), L: _fraction(row.ucope_l)},
        "action": row.action,
        "expected_fifth_trial_AUC": _fraction(row.expected_auc),
        "hazards": {S: _fraction(row.hazard_s), L: _fraction(row.hazard_l)},
        "history": list(row.outcomes),
        "history_bits": list(row.bits),
        "margin": _fraction(row.margin),
        "prior_probability": _fraction(row.prior_probability),
        "rho": _fraction(row.rho),
    }


def _fraction(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )

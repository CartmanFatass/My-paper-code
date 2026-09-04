"""Exact 16-history UCOPE count-state discriminator.

All arithmetic is rational.  This candidate-local module performs no training,
task-return rollout, acquisition, retirement, or partner adaptation.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from enum import Enum
from fractions import Fraction
from itertools import product
import json
import inspect
import re


S = "S"
L = "L"
PERIODS = (S, L)


class Terminal(str, Enum):
    PASS = "PASS_NARROW_COUNT_STATE_RELEVANCE"
    STOP = "STOP_OR_PARK_COUNT_INFORMATION_ROUTE"


class A1Branch(str, Enum):
    INVALID_MANIFEST = "A1_INVALID_MANIFEST"
    INVALID_ENUMERATION = "A1_INVALID_ENUMERATION"
    SCIENTIFIC_STOP = "A1_SCIENTIFIC_STOP"
    SUPPORTED = "A1_COUNT_STATE_DECISION_RELEVANCE_SUPPORTED"


A1_ASSIGNMENT_ID = "UCOPE-A1-COUNT-STATE-EXACT-ENUMERATION"
A1_CANDIDATE = "CAND-VSP-07-UCOPE@adversarial-revision-v6"
A1_SCHEMA_VERSION = 1
A1_MODES = ("primary", "homogeneous", "independent_redraw")
A1_CANONICAL_HISTORIES = tuple(product((0, 1), repeat=4))
A1_STOP_IDS = (
    "S01_NO_REGISTERED_PERSISTENCE_LAW",
    "S02_SWITCH_REQUIRES_VERSION_POOLING",
    "S03_MATCHED_NONCOUNT_STATE_OR_EXPOSURE_FAILS",
    "S04_HOMOGENEOUS_BOUNDARY_REMAINS_COUNT_SENSITIVE",
    "S05_INDEPENDENT_REDRAW_RETAINS_HISTORY_DEPENDENCE",
    "S06_ALIAS_SPLIT_MERGE_CHANGES_OUTPUT",
    "S07_SEPARATION_REQUIRES_CENSOR_AS_FAILURE",
    "S08_IDENTITY_PERMUTATION_CHANGES_ACTION",
    "S09_BEATS_ONLY_SG_RATE_NOT_CB_AUC",
    "S10_ENUMERATED_AUC_GAIN_NONPOSITIVE",
    "S11_SWITCH_DISAPPEARS_AFTER_NONCOUNT_STATE_CANONICALIZATION",
    "S12_REQUIRES_RETIREMENT_ONLINE_UPDATE_REWARD_OR_POSTOUTCOME_FILTER",
)
A1_ACTIVITY_KEYS = (
    "environment_transitions",
    "policy_calls",
    "learner_calls",
    "trainer_calls",
    "optimizer_calls",
    "evaluation_calls",
    "stochastic_draws",
    "seeds",
    "gradients",
    "retirement_actions",
    "task_return_observations",
)
_REVISION_RE = re.compile(r"[0-9a-f]{40}")
_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_FRACTION_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?")
A1_JOINT_NUMERATORS = {
    "0000": (81, 81),
    "0001": (9, 729),
    "0010": (9, 729),
    "0011": (1, 6561),
    "0100": (729, 9),
    "0101": (81, 81),
    "0110": (81, 81),
    "0111": (9, 729),
    "1000": (729, 9),
    "1001": (81, 81),
    "1010": (81, 81),
    "1011": (9, 729),
    "1100": (6561, 1),
    "1101": (729, 9),
    "1110": (729, 9),
    "1111": (81, 81),
}
A1_D_VALUES = {
    -2: ("1/6562", "657/6562", "5905/6562", "657/3281", "5905/6562", L, "4591/6562"),
    -1: ("1/82", "9/82", "73/82", "9/41", "73/82", L, "55/82"),
    0: ("1/2", "1/2", "1/2", "1", "1/2", S, "1/2"),
    1: ("81/82", "73/82", "9/82", "73/41", "9/82", S, "137/82"),
    2: ("6561/6562", "5905/6562", "657/6562", "5905/3281", "657/6562", S, "11153/6562"),
}


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
        # Preserve the acquisition-certificate consumer's pre-A1 accessor names.
        name = {"ell": "long_a", "ell_prime": "long_b"}.get(name, name)
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
        NominalPeriod("long_a", L, 2, long_law),
        NominalPeriod("long_b", L, 2, long_law),
    )
    long_trials = ("long_a", "long_b") if split_long_alias else ("long_a", "long_a")
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
        weights=(Fraction(1), Fraction(1)),
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
    if family.weights != (Fraction(1), Fraction(1)):
        issues.append("cell weights must both equal 1")
    roster = tuple((item.name, item.effective, item.duration) for item in family.nominals)
    if roster != (("s", S, 1), ("long_a", L, 2), ("long_b", L, 2)):
        issues.append("effective-period quotient must be {s}->S, {long_a,long_b}->L")
    elif family.nominal("long_a").execution_law != family.nominal("long_b").execution_law:
        issues.append("long_a and long_b are not execution-law aliases")
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
    if any(name not in ("long_a", "long_b") for name in long_names):
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
    # Frozen secondary comparator: structural mass-per-cost at cold start.
    # It is count blind in this family and therefore shares CB-AUC's scores.
    sg_rate_action = S
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


# A1 registered-probe surface.  The older dataclasses and audit above remain a
# direct dependency of acquisition_park_certificate; A1 projects their exact
# arithmetic into a source-bound, fail-closed artifact contract.


def build_a1_manifest(
    *, source_revision: str, run_id: str, technical_only: bool = False
) -> dict[str, object]:
    """Build the only frozen A1 configuration accepted by the probe."""

    return {
        "artifact_kind": "ucope_a1_count_state_exact_enumeration_manifest",
        "schema_version": A1_SCHEMA_VERSION,
        "assignment_id": A1_ASSIGNMENT_ID,
        "candidate": A1_CANDIDATE,
        "scientific_stage": "derivation",
        "treatment": "A",
        "formal": False,
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": technical_only,
        "family": {
            "cells": ["c1", "c2"],
            "cell_weights": ["1", "1"],
            "raw_periods": ["s", "long_a", "long_b"],
            "effective_quotient": {"s": S, "long_a": L, "long_b": L},
            "durations": {S: 1, L: 2},
            "horizon": 3,
            "latent_regimes": ["THETA_S", "THETA_L"],
            "prior": {"THETA_S": "1/2", "THETA_L": "1/2"},
            "persistent_through_trial": 5,
            "hazards": {
                "THETA_S": {S: "9/10", L: "1/10"},
                "THETA_L": {S: "1/10", L: "9/10"},
            },
            "pre_outcome_tape": [
                {"trial": 1, "cell": "c1", "limit": 3, "period": "s"},
                {"trial": 2, "cell": "c2", "limit": 3, "period": "s"},
                {"trial": 3, "cell": "c1", "limit": 3, "period": "long_a"},
                {"trial": 4, "cell": "c2", "limit": 3, "period": "long_b"},
                {"trial": 5, "cell": "c1", "limit": 3, "period": "DECISION"},
            ],
            "trial_5_structural_support": {"c1": {S: 1, L: 1}, "c2": {S: 0, L: 0}},
            "canonical_tie_order": [S, L],
        },
        "comparators": {
            "primary": "CB-AUC",
            "secondary": "SG-RATE",
            "cb_auc_scores": {S: "1", L: "1/2"},
        },
        "modes": list(A1_MODES),
        "caps": {
            "canonical_histories_per_mode": 16,
            "regime_conditioned_rational_cells": 96,
            "random_samples": 0,
            "seeds": 0,
        },
        "excluded_score_and_key_labels": [
            "partner_id",
            "roster_slot",
            "owner_epoch",
            "message_source",
            "policy_identity",
        ],
        "required_zero_activity": list(A1_ACTIVITY_KEYS),
    }


def validate_a1_manifest(manifest: object) -> tuple[str, ...]:
    issues: list[str] = []
    if _contains_float(manifest):
        issues.append("manifest contains float/epsilon arithmetic")
    if not isinstance(manifest, dict):
        return (*issues, "manifest must be an object")
    source_revision = manifest.get("source_revision")
    run_id = manifest.get("run_id")
    technical_only = manifest.get("technical_only")
    if not isinstance(source_revision, str) or _REVISION_RE.fullmatch(source_revision) is None:
        issues.append("source_revision must be a frozen lowercase 40-hex revision")
    if not isinstance(run_id, str) or _RUN_ID_RE.fullmatch(run_id) is None:
        issues.append("run_id is not a frozen portable identifier")
    if type(technical_only) is not bool:
        issues.append("technical_only must be a boolean")
    dynamic_fields_valid = (
        isinstance(source_revision, str)
        and _REVISION_RE.fullmatch(source_revision) is not None
        and isinstance(run_id, str)
        and _RUN_ID_RE.fullmatch(run_id) is not None
        and type(technical_only) is bool
    )
    if dynamic_fields_valid:
        expected = build_a1_manifest(
            source_revision=source_revision,
            run_id=run_id,
            technical_only=technical_only,
        )
        if manifest != expected:
            issues.append("manifest is non-total or contradicts a frozen A1 literal")
    return tuple(issues)


def zero_activity() -> dict[str, int]:
    return {name: 0 for name in A1_ACTIVITY_KEYS}


def select_a1_branch(
    *,
    manifest_errors: tuple[str, ...] = (),
    enumeration_errors: tuple[str, ...] = (),
    stop_failures: tuple[str, ...] = (),
    technical_only: bool = False,
) -> tuple[A1Branch | None, str | None]:
    """Apply the frozen precedence and the canonical lowest S failure."""

    if technical_only:
        return None, None
    if manifest_errors:
        return A1Branch.INVALID_MANIFEST, None
    if enumeration_errors:
        return A1Branch.INVALID_ENUMERATION, None
    unknown = tuple(item for item in stop_failures if item not in A1_STOP_IDS)
    if unknown:
        return A1Branch.INVALID_ENUMERATION, None
    if stop_failures:
        first = min(stop_failures, key=A1_STOP_IDS.index)
        return A1Branch.SCIENTIFIC_STOP, first
    return A1Branch.SUPPORTED, None


def run_a1_probe(
    manifest: object, *, activity: dict[str, int] | None = None
) -> dict[str, object]:
    """Produce one deterministic artifact; callers own its one-shot lifecycle."""

    manifest_errors = validate_a1_manifest(manifest)
    technical_only = bool(
        isinstance(manifest, dict) and manifest.get("technical_only") is True
    )
    observed_activity = zero_activity() if activity is None else dict(activity)
    activity_errors = _validate_activity(observed_activity)
    if technical_only:
        branch, first = select_a1_branch(technical_only=True)
        return {
            "artifact_kind": "ucope_a1_technical_exercise",
            "schema_version": A1_SCHEMA_VERSION,
            "manifest": manifest,
            "branch": branch,
            "first_failure_id": first,
            "scientific_terminal_admitted": False,
            "activity": observed_activity,
            "manifest_errors": list(manifest_errors),
            "exercise_checks": {
                "manifest_valid": not manifest_errors,
                "zero_activity": not activity_errors,
                "artifact_roundtrip_ready": not manifest_errors and not activity_errors,
            },
        }
    if manifest_errors:
        branch, first = select_a1_branch(manifest_errors=manifest_errors)
        return {
            "artifact_kind": "ucope_a1_count_state_exact_enumeration_result",
            "schema_version": A1_SCHEMA_VERSION,
            "manifest": manifest,
            "branch": branch.value,
            "first_failure_id": first,
            "scientific_terminal_admitted": False,
            "activity": observed_activity,
            "manifest_errors": list(manifest_errors),
        }

    evidence = _build_a1_evidence(activity=observed_activity)
    return _assemble_a1_result(
        manifest=manifest,
        evidence=evidence,
        activity=observed_activity,
    )


def _assemble_a1_result(
    *,
    manifest: dict[str, object],
    evidence: dict[str, object],
    activity: dict[str, int],
) -> dict[str, object]:
    """Freeze one branch from retained evidence and self-contained diagnostics."""

    activity_errors = _validate_activity(activity)
    enumeration_errors = activity_errors + _validate_generated_evidence(
        evidence, expected_activity=activity
    )
    stop_failures = _stop_failures(evidence) if not enumeration_errors else ()
    branch, first = select_a1_branch(
        enumeration_errors=enumeration_errors, stop_failures=stop_failures
    )
    return {
        "artifact_kind": "ucope_a1_count_state_exact_enumeration_result",
        "schema_version": A1_SCHEMA_VERSION,
        "manifest": manifest,
        "branch": branch.value,
        "first_failure_id": first,
        "scientific_terminal_admitted": branch
        in (A1Branch.SCIENTIFIC_STOP, A1Branch.SUPPORTED),
        "activity": activity,
        "manifest_errors": [],
        "enumeration_errors": list(enumeration_errors),
        "stop_failures": list(stop_failures),
        **evidence,
    }


def validate_a1_artifact(payload: object) -> tuple[str, ...]:
    """Validate retained payload only; never re-enumerate after a branch exists."""

    issues: list[str] = []
    if _contains_float(payload):
        issues.append("artifact contains float/epsilon arithmetic")
    if not isinstance(payload, dict):
        return (*issues, "artifact must be an object")
    manifest = payload.get("manifest")
    manifest_errors = validate_a1_manifest(manifest)
    if manifest_errors:
        issues.extend(f"manifest: {item}" for item in manifest_errors)
        return tuple(issues)
    assert isinstance(manifest, dict)
    if manifest["technical_only"]:
        activity = payload.get("activity")
        activity_errors = _validate_activity(activity)
        expected_keys = {
            "artifact_kind",
            "schema_version",
            "manifest",
            "branch",
            "first_failure_id",
            "scientific_terminal_admitted",
            "activity",
            "manifest_errors",
            "exercise_checks",
        }
        if set(payload) != expected_keys:
            issues.append("technical-only artifact schema differs from the frozen projection")
        if payload.get("branch") is not None or payload.get("scientific_terminal_admitted") is not False:
            issues.append("technical-only artifact admitted a scientific terminal")
        if any(key in payload for key in ("primary", "boundaries", "aggregates")):
            issues.append("technical-only artifact materialized result-bearing evidence")
        expected_checks = {
            "manifest_valid": True,
            "zero_activity": not activity_errors,
            "artifact_roundtrip_ready": not activity_errors,
        }
        if (
            payload.get("artifact_kind") != "ucope_a1_technical_exercise"
            or payload.get("schema_version") != A1_SCHEMA_VERSION
            or payload.get("first_failure_id") is not None
            or payload.get("manifest_errors") != []
            or payload.get("exercise_checks") != expected_checks
        ):
            issues.append("technical-only artifact differs from the retained literal contract")
        issues.extend(activity_errors)
        return tuple(issues)

    expected_keys = {
        "artifact_kind",
        "schema_version",
        "manifest",
        "branch",
        "first_failure_id",
        "scientific_terminal_admitted",
        "activity",
        "manifest_errors",
        "enumeration_errors",
        "stop_failures",
        "primary",
        "boundaries",
        "matched_histories",
        "matched_noncount_state_witness",
        "alias_projection_witness",
        "identity_projection_witness",
        "persistence_witness",
        "version_closure_witness",
        "forbidden_dependency_witness",
        "invariants",
        "resource_accounting",
    }
    if set(payload) != expected_keys:
        issues.append("registered artifact schema differs from the frozen retained payload")
    activity = payload.get("activity")
    activity_errors = _validate_activity(activity)
    evidence = {
        key: payload.get(key)
        for key in (
            "primary",
            "boundaries",
            "matched_histories",
            "matched_noncount_state_witness",
            "alias_projection_witness",
            "identity_projection_witness",
            "persistence_witness",
            "version_closure_witness",
            "forbidden_dependency_witness",
            "invariants",
            "resource_accounting",
        )
    }
    enumeration_errors = activity_errors + _validate_generated_evidence(
        evidence, expected_activity=activity if isinstance(activity, dict) else None
    )
    stop_failures = _stop_failures(evidence) if not enumeration_errors else ()
    branch, first = select_a1_branch(
        enumeration_errors=enumeration_errors, stop_failures=stop_failures
    )
    expected_admitted = branch in (A1Branch.SCIENTIFIC_STOP, A1Branch.SUPPORTED)
    if (
        payload.get("artifact_kind")
        != "ucope_a1_count_state_exact_enumeration_result"
        or payload.get("schema_version") != A1_SCHEMA_VERSION
        or payload.get("manifest_errors") != []
        or payload.get("enumeration_errors") != list(enumeration_errors)
        or payload.get("stop_failures") != list(stop_failures)
        or payload.get("branch") != branch.value
        or payload.get("first_failure_id") != first
        or payload.get("scientific_terminal_admitted") is not expected_admitted
    ):
        issues.append("artifact branch or retained validation fields violate frozen precedence")
    return tuple(issues)


def _build_a1_evidence(
    *, activity: dict[str, int] | None = None
) -> dict[str, object]:
    """Enumerate exactly the three frozen modes and derive all other witnesses."""

    observed_activity = zero_activity() if activity is None else dict(activity)
    family = build_family()
    primary = enumerate_histories(family)
    homogeneous_family = build_family(homogeneous_hazards=True)
    homogeneous = enumerate_histories(homogeneous_family)
    redraw = enumerate_histories(family, independent_redraw=True)
    modes = {
        "primary": _mode_payload("primary", family, primary),
        "homogeneous": _mode_payload("homogeneous", homogeneous_family, homogeneous),
        "independent_redraw": _mode_payload("independent_redraw", family, redraw),
    }
    empty = Ledger.empty(family.version)
    limit_one_l = Trial(1, family.cells[0], 1, "long_a")
    censored_l = update_ledger(family, empty, limit_one_l, None)
    observed_s = update_ledger(
        family, empty, Trial(1, family.cells[0], 1, "s"), True
    )
    mixed_version_update = "ACCEPTED"
    try:
        update_ledger(
            family, Ledger.empty("mixed-executor-generation"), family.trials[0], True
        )
    except ValueError:
        mixed_version_update = "REJECTED"
    primary_mode = modes["primary"]
    alias_witness = _alias_projection_witness(family, primary_mode)
    identity_witness = _identity_projection_witness(modes["primary"]["rows"])
    matched_state_witness = _matched_noncount_state_witness(
        family,
        primary_mode["rows"][12],
        primary_mode["rows"][3],
    )
    censor_witness = _censor_projection_witness(
        primary_mode=primary_mode,
        before=empty,
        after=censored_l,
        observed_s=observed_s,
    )
    version_witness = {
        "family_generation": family.version,
        "mixed_ledger_generation": "mixed-executor-generation",
        "mixed_version_update": mixed_version_update,
    }
    forbidden_dependency_witness = _forbidden_dependency_witness(observed_activity)
    evidence = {
        "primary": modes["primary"],
        "boundaries": {
            "homogeneous": modes["homogeneous"],
            "independent_redraw": modes["independent_redraw"],
            "censor": censor_witness,
        },
        "matched_histories": {
            "HS": primary_mode["rows"][12],
            "HL": primary_mode["rows"][3],
        },
        "matched_noncount_state_witness": matched_state_witness,
        "alias_projection_witness": alias_witness,
        "identity_projection_witness": identity_witness,
        "persistence_witness": {
            "registered_family_version": family.version,
            "theta_scope": "ONE_FIVE_TRIAL_BLOCK",
            "persistent_through_trial_5": family.persistent_theta,
        },
        "version_closure_witness": version_witness,
        "forbidden_dependency_witness": forbidden_dependency_witness,
        "resource_accounting": {
            "history_rows": 48,
            "unique_histories_reused": 16,
            "regime_conditioned_rational_cells": 96,
        },
    }
    evidence["invariants"] = _derive_a1_invariants(evidence, observed_activity)
    return evidence


def _alias_projection_witness(
    family: Family, primary_mode: dict[str, object]
) -> dict[str, object]:
    split_raw = ("s", "s", "long_a", "long_b")
    merged_raw = ("s", "s", "long_a", "long_a")

    def project(raw: tuple[str, ...]) -> dict[str, object]:
        return {
            "effective_tape": [family.nominal(name).effective for name in raw],
            "durations": [family.nominal(name).duration for name in raw],
            "execution_laws": [
                family.nominal(name).execution_law.decode("ascii") for name in raw
            ],
            "downstream_primary_canonical_json": _canonical_text(primary_mode),
        }

    split_projection = project(split_raw)
    merged_projection = project(merged_raw)
    return {
        "split_raw_tape": list(split_raw),
        "merged_raw_tape": list(merged_raw),
        "split_projection": split_projection,
        "merged_projection": merged_projection,
        "byte_equal": _canonical_bytes(split_projection)
        == _canonical_bytes(merged_projection),
    }


def _identity_free_projection(
    rows: list[dict[str, object]], identity_labels: dict[str, str]
) -> bytes:
    if set(identity_labels) != {
        "partner_id",
        "roster_slot",
        "owner_epoch",
        "message_source",
        "policy_identity",
    }:
        raise ValueError("identity projection requires every excluded label")
    # Labels are intentionally consumed only by the boundary interface and are
    # never copied into the row/value projection.
    return _canonical_bytes(rows)


def _identity_projection_witness(rows: list[dict[str, object]]) -> dict[str, object]:
    base = {
        "partner_id": "partner-A",
        "roster_slot": "slot-0",
        "owner_epoch": "epoch-4",
        "message_source": "source-A",
        "policy_identity": "policy-A",
    }
    permuted = {
        "partner_id": "partner-Z",
        "roster_slot": "slot-9",
        "owner_epoch": "epoch-99",
        "message_source": "source-Z",
        "policy_identity": "policy-Z",
    }
    forbidden = set(base)
    identity_fields_absent = not any(
        _contains_any_key(row, forbidden) for row in rows
    )
    base_projection = _identity_free_projection(rows, base)
    permuted_projection = _identity_free_projection(rows, permuted)
    return {
        "excluded_labels": sorted(forbidden),
        "base_labels": base,
        "permuted_labels": permuted,
        "projected_row_fields": sorted(rows[0]) if rows else [],
        "base_projection_canonical_json": base_projection.decode("utf-8"),
        "permuted_projection_canonical_json": permuted_projection.decode("utf-8"),
        "identity_fields_absent": identity_fields_absent,
        "byte_equal": base_projection == permuted_projection,
    }


def _matched_noncount_state_witness(
    family: Family, h_s: dict[str, object], h_l: dict[str, object]
) -> dict[str, object]:
    if h_s["E"] != h_l["E"]:
        raise ValueError("matched rows do not share the exposure ledger")
    noncount_state = _frozen_noncount_state(family, exposure=h_s["E"])
    hs_state = json.loads(json.dumps(noncount_state, sort_keys=True))
    hl_state = json.loads(json.dumps(noncount_state, sort_keys=True))
    return {
        "HS": {
            "noncount_state": hs_state,
            "N": dict(h_s["N"]),
            "E": dict(h_s["E"]),
            "rho": h_s["rho"],
        },
        "HL": {
            "noncount_state": hl_state,
            "N": dict(h_l["N"]),
            "E": dict(h_l["E"]),
            "rho": h_l["rho"],
        },
        "noncount_state_bytes_equal": _canonical_bytes(hs_state)
        == _canonical_bytes(hl_state),
        "count_and_posterior_differ": (
            h_s["N"] != h_l["N"] and h_s["rho"] != h_l["rho"]
        ),
    }


def _frozen_noncount_state(
    family: Family, *, exposure: dict[str, object]
) -> dict[str, object]:
    return {
        "current_opportunity": {
            "trial": 5,
            "eligible_cell": "c1",
            "administrative_limit": 3,
        },
        "uncovered_set": ["c1"],
        "horizon": family.horizon,
        "Q_str": {"c1": {S: 1, L: 1}, "c2": {S: 0, L: 0}},
        "costs": {S: 1, L: 2},
        "censor_law": {
            "limit_3": {
                "period_S": "BINARY_FIRST_HIT",
                "period_L": "BINARY_FIRST_HIT",
            },
            "limit_1": {"period_S": "OBSERVED_AT_T1", "period_L": "CENSOR"},
        },
        "exposure_ledger": {
            "slots": [1, 1, 1, 1],
            "pooled": dict(exposure),
        },
        "forced_action_sequence": [S, S, L, L],
        "executor_generation": family.version,
        "partner_policy_generation": "ucope-partner-policy-generation-v1",
        "noncount_recurrent_state": {"encoding": "canonical-empty", "bytes": ""},
        "noncount_policy_state": {"encoding": "canonical-empty", "bytes": ""},
    }


def _forbidden_dependency_witness(activity: dict[str, int]) -> dict[str, object]:
    module = inspect.getmodule(_forbidden_dependency_witness)
    if module is None:
        raise RuntimeError("cannot resolve exact_enumerator module for AST witness")
    tree = ast.parse(inspect.getsource(module))
    observed_imports: set[str] = set()
    observed_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            observed_imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            observed_imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            name = _ast_call_name(node.func)
            if name:
                observed_calls.add(name)
    forbidden_import_roots = {
        "gym",
        "numpy",
        "random",
        "torch",
    }
    forbidden_call_tokens = {
        "environment_step",
        "evaluate",
        "learner_step",
        "optimizer_step",
        "policy_forward",
        "retire",
        "task_reward",
        "trainer_step",
    }
    forbidden_imports_present = sorted(
        name for name in observed_imports if name.split(".")[0] in forbidden_import_roots
    )
    forbidden_calls_present = sorted(
        name
        for name in observed_calls
        if name.split(".")[-1] in forbidden_call_tokens
    )
    tape_fields = [field.name for field in fields(Trial)]
    return {
        "activity": dict(activity),
        "all_required_activity_zero": _validate_activity(activity) == (),
        "observed_imports": sorted(observed_imports),
        "observed_calls": sorted(observed_calls),
        "forbidden_import_roots": sorted(forbidden_import_roots),
        "forbidden_call_tokens": sorted(forbidden_call_tokens),
        "forbidden_imports_present": forbidden_imports_present,
        "forbidden_calls_present": forbidden_calls_present,
        "forbidden_surface_absent": not forbidden_imports_present
        and not forbidden_calls_present,
        "pre_outcome_tape_fields": tape_fields,
        "postoutcome_filter_absent": all(
            "outcome" not in field_name.lower() for field_name in tape_fields
        ),
    }


def _ast_call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _ast_call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _censor_projection_witness(
    *,
    primary_mode: dict[str, object],
    before: Ledger,
    after: Ledger,
    observed_s: Ledger,
) -> dict[str, object]:
    before_projection = _canonical_text(primary_mode)
    after_projection = _canonical_text(primary_mode)
    return {
        "administrative_limit": 1,
        "S_at_t1": "HIT",
        "L_at_t1": "CENSOR",
        "L_binary_denominator_increment": sum(after.opportunities)
        - sum(before.opportunities),
        "S_binary_denominator_increment": sum(observed_s.opportunities)
        - sum(before.opportunities),
        "ledger_before": {
            "E": list(before.opportunities),
            "N": list(before.hits),
        },
        "ledger_after_L_censor": {
            "E": list(after.opportunities),
            "N": list(after.hits),
        },
        "primary_before_canonical_json": before_projection,
        "primary_after_canonical_json": after_projection,
        "primary_bytes_equal": before_projection.encode("utf-8")
        == after_projection.encode("utf-8"),
    }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _canonical_text(value: object) -> str:
    return _canonical_bytes(value).decode("utf-8")


def _contains_any_key(value: object, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in keys or _contains_any_key(item, keys) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_any_key(item, keys) for item in value)
    return False


def _mode_payload(
    mode: str, family: Family, rows: tuple[Row, ...]
) -> dict[str, object]:
    expected_ucope = sum(
        weight
        * _conditional_auc(family, row.action, theta)
        for row in rows
        for theta, weight in _mode_joint_weights(mode, family, row).items()
    )
    expected_cb = sum(
        weight
        * _conditional_auc(family, row.cb_auc_action, theta)
        for row in rows
        for theta, weight in _mode_joint_weights(mode, family, row).items()
    )
    expected_terminal = sum(
        weight
        * family.hazards.probability(theta, row.action)
        for row in rows
        for theta, weight in _mode_joint_weights(mode, family, row).items()
    )
    expected_terminal_cb = sum(
        weight
        * family.hazards.probability(theta, row.cb_auc_action)
        for row in rows
        for theta, weight in _mode_joint_weights(mode, family, row).items()
    )
    per_regime_auc = {
        _theta_name(theta): _fraction(
            2
            * sum(
                _mode_joint_weights(mode, family, row)[theta]
                * _conditional_auc(family, row.action, theta)
                for row in rows
            )
        )
        for theta in (S, L)
    }
    return {
        "mode": mode,
        "rows": [_a1_row_payload(row, family, mode=mode) for row in rows],
        "aggregates": {
            "UCOPE_expected_auc": _fraction(expected_ucope),
            "CB_AUC_expected_auc": _fraction(expected_cb),
            "AUC_gain_over_CB_AUC": _fraction(expected_ucope - expected_cb),
            "UCOPE_terminal_coverage": _fraction(expected_terminal),
            "CB_AUC_terminal_coverage": _fraction(expected_terminal_cb),
            "terminal_coverage_gain": _fraction(expected_terminal - expected_terminal_cb),
            "UCOPE_conditional_auc_by_regime": per_regime_auc,
        },
    }


def _a1_row_payload(
    row: Row, family: Family, *, mode: str = "primary"
) -> dict[str, object]:
    joint = _mode_joint_weights(mode, family, row)
    n_s = row.ledger.hits[0] + row.ledger.hits[1]
    n_l = row.ledger.hits[2] + row.ledger.hits[3]
    return {
        "history_bits": "".join(str(bit) for bit in row.bits),
        "N": {S: n_s, L: n_l},
        "E": {S: 2, L: 2},
        "joint_regime_weights": {
            "THETA_S": _fraction(joint[S]),
            "THETA_L": _fraction(joint[L]),
        },
        "history_weight": _fraction(joint[S] + joint[L]),
        "rho": _fraction(row.rho),
        "predictive_hazards": {S: _fraction(row.hazard_s), L: _fraction(row.hazard_l)},
        "UCOPE_scores": {S: _fraction(row.ucope_s), L: _fraction(row.ucope_l)},
        "UCOPE_action": row.action,
        "UCOPE_margin": _fraction(row.margin),
        "CB_AUC_scores": {S: _fraction(row.cb_auc_s), L: _fraction(row.cb_auc_l)},
        "CB_AUC_action": row.cb_auc_action,
        "SG_RATE_scores": {S: "1", L: "1/2"},
        "SG_RATE_action": row.sg_rate_action,
        "conditional_trial_5_auc": {
            "THETA_S": _fraction(_conditional_auc(family, row.action, S)),
            "THETA_L": _fraction(_conditional_auc(family, row.action, L)),
        },
    }


def _joint_weights(family: Family, ledger: Ledger) -> dict[str, Fraction]:
    return {
        S: family.prior_s * _likelihood(family, ledger, S),
        L: (1 - family.prior_s) * _likelihood(family, ledger, L),
    }


def _mode_joint_weights(
    mode: str, family: Family, row: Row
) -> dict[str, Fraction]:
    if mode == "independent_redraw":
        half_history_weight = _prior_probability(family, row.ledger) / 2
        return {S: half_history_weight, L: half_history_weight}
    if mode in ("primary", "homogeneous"):
        return _joint_weights(family, row.ledger)
    raise ValueError(f"unknown A1 mode: {mode}")


def _conditional_auc(family: Family, action: str, theta: str) -> Fraction:
    multiplier = family.horizon - (1 if action == S else 2)
    return multiplier * family.hazards.probability(theta, action)


def _theta_name(theta: str) -> str:
    return "THETA_S" if theta == S else "THETA_L"


def _boundary_mode_zero(mode: dict[str, object]) -> bool:
    rows = mode["rows"]
    aggregates = mode["aggregates"]
    return (
        all(row["UCOPE_action"] == S and row["CB_AUC_action"] == S for row in rows)
        and aggregates["AUC_gain_over_CB_AUC"] == "0"
    )


def _derive_a1_invariants(
    evidence: dict[str, object], activity: dict[str, int]
) -> dict[str, bool]:
    primary = evidence["primary"]
    boundaries = evidence["boundaries"]
    rows = primary["rows"]
    matched = evidence["matched_histories"]
    matched_state = evidence["matched_noncount_state_witness"]
    alias = evidence["alias_projection_witness"]
    identity = evidence["identity_projection_witness"]
    persistence = evidence["persistence_witness"]
    version = evidence["version_closure_witness"]
    forbidden = evidence["forbidden_dependency_witness"]
    history_order = ["".join(map(str, bits)) for bits in A1_CANONICAL_HISTORIES]
    primary_joint_sum = sum(
        _parse_fraction_text(weight)
        for row in rows
        for weight in row["joint_regime_weights"].values()
    )
    auxiliary_accounting = evidence["resource_accounting"]
    return {
        "S01_registered_persistence_law": persistence.get(
            "persistent_through_trial_5"
        )
        is True,
        "S02_version_pooling_rejected": version.get("mixed_version_update")
        == "REJECTED",
        "S03_matched_noncount_state_and_exposure": matched_state.get(
            "noncount_state_bytes_equal"
        )
        is True
        and matched_state.get("count_and_posterior_differ") is True,
        "S04_homogeneous_zero_effect": _boundary_mode_zero(
            boundaries["homogeneous"]
        ),
        "S05_independent_redraw_zero_effect": _boundary_mode_zero(
            boundaries["independent_redraw"]
        ),
        "S06_alias_split_merge_invariant": alias.get("byte_equal") is True,
        "S07_censor_is_distinct_from_failure": boundaries["censor"].get(
            "L_binary_denominator_increment"
        )
        == 0
        and boundaries["censor"].get("primary_bytes_equal") is True,
        "S08_identity_permutation_invariant": identity.get("byte_equal") is True,
        "S09_primary_comparator_is_cb_auc": all(
            row.get("CB_AUC_action") == S for row in rows
        )
        and primary["aggregates"].get("CB_AUC_expected_auc") == "1",
        "S10_primary_auc_gain_positive": _parse_fraction_text(
            primary["aggregates"]["AUC_gain_over_CB_AUC"]
        )
        > 0,
        "S11_count_only_matched_switch": matched["HS"].get("UCOPE_action") == S
        and matched["HL"].get("UCOPE_action") == L
        and matched_state.get("noncount_state_bytes_equal") is True,
        "S12_no_forbidden_dependency": _validate_activity(activity) == ()
        and forbidden.get("activity") == activity
        and forbidden.get("all_required_activity_zero") is True
        and forbidden.get("forbidden_surface_absent") is True
        and forbidden.get("postoutcome_filter_absent") is True,
        "canonical_history_order": [row.get("history_bits") for row in rows]
        == history_order,
        "joint_weight_numerators_sum": primary_joint_sum == 1,
        "exact_regime_conditioned_cells": auxiliary_accounting
        == {
            "history_rows": 48,
            "unique_histories_reused": 16,
            "regime_conditioned_rational_cells": 96,
        },
        "exposure_is_pre_outcome": all(
            row.get("E") == {S: 2, L: 2} for row in rows
        ),
        "tape_has_no_outcome_field": all(
            "outcome" not in field_name.lower()
            for field_name in forbidden.get("pre_outcome_tape_fields", [])
        ),
        "score_and_key_are_identity_free": identity.get(
            "identity_fields_absent"
        )
        is True
        and identity.get("byte_equal") is True,
    }


def _parse_fraction_text(value: object) -> Fraction:
    if not isinstance(value, str) or _FRACTION_RE.fullmatch(value) is None:
        raise ValueError(f"not a canonical rational string: {value!r}")
    return Fraction(value)


def _stop_failures(evidence: dict[str, object]) -> tuple[str, ...]:
    invariants = evidence["invariants"]
    mapping = (
        ("S01_NO_REGISTERED_PERSISTENCE_LAW", "S01_registered_persistence_law"),
        ("S02_SWITCH_REQUIRES_VERSION_POOLING", "S02_version_pooling_rejected"),
        ("S03_MATCHED_NONCOUNT_STATE_OR_EXPOSURE_FAILS", "S03_matched_noncount_state_and_exposure"),
        ("S04_HOMOGENEOUS_BOUNDARY_REMAINS_COUNT_SENSITIVE", "S04_homogeneous_zero_effect"),
        ("S05_INDEPENDENT_REDRAW_RETAINS_HISTORY_DEPENDENCE", "S05_independent_redraw_zero_effect"),
        ("S06_ALIAS_SPLIT_MERGE_CHANGES_OUTPUT", "S06_alias_split_merge_invariant"),
        ("S07_SEPARATION_REQUIRES_CENSOR_AS_FAILURE", "S07_censor_is_distinct_from_failure"),
        ("S08_IDENTITY_PERMUTATION_CHANGES_ACTION", "S08_identity_permutation_invariant"),
        ("S09_BEATS_ONLY_SG_RATE_NOT_CB_AUC", "S09_primary_comparator_is_cb_auc"),
        ("S10_ENUMERATED_AUC_GAIN_NONPOSITIVE", "S10_primary_auc_gain_positive"),
        ("S11_SWITCH_DISAPPEARS_AFTER_NONCOUNT_STATE_CANONICALIZATION", "S11_count_only_matched_switch"),
        ("S12_REQUIRES_RETIREMENT_ONLINE_UPDATE_REWARD_OR_POSTOUTCOME_FILTER", "S12_no_forbidden_dependency"),
    )
    return tuple(stop_id for stop_id, name in mapping if invariants.get(name) is not True)


def _validate_evidence(evidence: object) -> tuple[str, ...]:
    """Validate serialized evidence against frozen literal tables, without rerun."""

    return _validate_generated_evidence(evidence, expected_activity=zero_activity())


def _validate_generated_evidence(
    evidence: object, *, expected_activity: dict[str, int] | None
) -> tuple[str, ...]:
    if _contains_float(evidence):
        return ("enumeration contains float/epsilon arithmetic",)
    if not isinstance(evidence, dict):
        return ("enumeration evidence must be an object",)
    primary = evidence.get("primary")
    boundaries = evidence.get("boundaries")
    if not isinstance(primary, dict) or not isinstance(boundaries, dict):
        return ("enumeration evidence is incomplete",)
    rows = primary.get("rows")
    if not isinstance(rows, list):
        return ("primary rows are absent",)
    histories = [row.get("history_bits") for row in rows if isinstance(row, dict)]
    expected_histories = ["".join(map(str, bits)) for bits in A1_CANONICAL_HISTORIES]
    issues: list[str] = []
    if histories != expected_histories:
        issues.append("primary history set/order is missing, duplicate, or drifted")
    if not _all_rational_strings(evidence):
        issues.append("rational field has noncanonical or non-rational encoding")
    if len(rows) == 16:
        for row, bits in zip(rows, A1_CANONICAL_HISTORIES):
            expected = _expected_primary_row(bits)
            if row != expected:
                issues.append(
                    f"primary row {''.join(map(str, bits))} differs from frozen exact table"
                )
    expected_primary_aggregates = {
        "UCOPE_expected_auc": "26571/20000",
        "CB_AUC_expected_auc": "1",
        "AUC_gain_over_CB_AUC": "6571/20000",
        "UCOPE_terminal_coverage": "1097/1250",
        "CB_AUC_terminal_coverage": "1/2",
        "terminal_coverage_gain": "236/625",
        "UCOPE_conditional_auc_by_regime": {
            "THETA_S": "179371/100000",
            "THETA_L": "86339/100000",
        },
    }
    if primary.get("mode") != "primary" or primary.get("aggregates") != expected_primary_aggregates:
        issues.append("primary aggregate/comparator projection differs from frozen values")
    _validate_boundary_literal(
        issues,
        boundaries.get("homogeneous"),
        mode="homogeneous",
    )
    _validate_boundary_literal(
        issues,
        boundaries.get("independent_redraw"),
        mode="independent_redraw",
    )
    family = build_family()
    empty = Ledger.empty(family.version)
    expected_censor = _censor_projection_witness(
        primary_mode=primary,
        before=empty,
        after=empty,
        observed_s=update_ledger(
            family, empty, Trial(1, family.cells[0], 1, "s"), True
        ),
    )
    if boundaries.get("censor") != expected_censor:
        issues.append("censor boundary treats censor as failure or changes the primary result")
    if len(rows) == 16:
        expected_matched_state = _matched_noncount_state_witness(
            family, rows[12], rows[3]
        )
        if evidence.get("matched_noncount_state_witness") != expected_matched_state:
            issues.append("matched non-count state witness is absent or drifted")
        expected_alias = _alias_projection_witness(family, primary)
        if evidence.get("alias_projection_witness") != expected_alias:
            issues.append("alias split/merge structural projection is absent or drifted")
        expected_identity = _identity_projection_witness(rows)
        if evidence.get("identity_projection_witness") != expected_identity:
            issues.append("identity-free canonical byte projection is absent or drifted")
    expected_persistence = {
        "registered_family_version": family.version,
        "theta_scope": "ONE_FIVE_TRIAL_BLOCK",
        "persistent_through_trial_5": True,
    }
    if evidence.get("persistence_witness") != expected_persistence:
        issues.append("registered persistence witness is absent or contradicts the manifest")
    version = evidence.get("version_closure_witness")
    if (
        not isinstance(version, dict)
        or set(version)
        != {
            "family_generation",
            "mixed_ledger_generation",
            "mixed_version_update",
        }
        or version.get("family_generation") != family.version
        or version.get("mixed_ledger_generation") != "mixed-executor-generation"
        or version.get("mixed_version_update") not in {"REJECTED", "ACCEPTED"}
    ):
        issues.append("version-closure witness is absent or structurally invalid")
    if expected_activity is None:
        issues.append("artifact activity is unavailable for S12 validation")
    else:
        expected_forbidden = _forbidden_dependency_witness(expected_activity)
        if evidence.get("forbidden_dependency_witness") != expected_forbidden:
            issues.append("forbidden-dependency/zero-activity witness is absent or drifted")
    invariants = evidence.get("invariants")
    expected_invariant_keys = {
        "S01_registered_persistence_law",
        "S02_version_pooling_rejected",
        "S03_matched_noncount_state_and_exposure",
        "S04_homogeneous_zero_effect",
        "S05_independent_redraw_zero_effect",
        "S06_alias_split_merge_invariant",
        "S07_censor_is_distinct_from_failure",
        "S08_identity_permutation_invariant",
        "S09_primary_comparator_is_cb_auc",
        "S10_primary_auc_gain_positive",
        "S11_count_only_matched_switch",
        "S12_no_forbidden_dependency",
        "canonical_history_order",
        "joint_weight_numerators_sum",
        "exact_regime_conditioned_cells",
        "exposure_is_pre_outcome",
        "tape_has_no_outcome_field",
        "score_and_key_are_identity_free",
    }
    if not isinstance(invariants, dict) or set(invariants) != expected_invariant_keys:
        issues.append("invariant table is incomplete or contains unknown predicates")
    elif expected_activity is not None:
        try:
            derived_invariants = _derive_a1_invariants(evidence, expected_activity)
        except (KeyError, TypeError, ValueError) as error:
            issues.append(f"invariant derivation failed from retained evidence: {error}")
        else:
            if invariants != derived_invariants:
                issues.append("recorded predicates differ from retained-evidence derivation")
            auxiliary_names = expected_invariant_keys - {
                name for name in expected_invariant_keys if name.startswith("S")
            }
            if any(derived_invariants[name] is not True for name in auxiliary_names):
                issues.append("non-scientific enumeration identity or resource invariant failed")
    accounting = evidence.get("resource_accounting")
    if accounting != {
        "history_rows": 48,
        "unique_histories_reused": 16,
        "regime_conditioned_rational_cells": 96,
    }:
        issues.append("resource accounting exceeds or differs from the frozen cap")
    matched = evidence.get("matched_histories")
    if not isinstance(matched, dict) or len(rows) != 16:
        issues.append("matched-history projection is absent")
    elif matched != {"HS": rows[12], "HL": rows[3]}:
        issues.append("matched HS/HL projection differs from the primary rows")
    return tuple(issues)


def _expected_primary_row(bits: tuple[int, int, int, int]) -> dict[str, object]:
    bit_string = "".join(map(str, bits))
    n_s, n_l = sum(bits[:2]), sum(bits[2:])
    joint_s, joint_l = A1_JOINT_NUMERATORS[bit_string]
    rho, h_s, h_l, score_s, score_l, action, margin = A1_D_VALUES[n_s - n_l]
    conditional = (
        {"THETA_S": "9/5", "THETA_L": "1/5"}
        if action == S
        else {"THETA_S": "1/10", "THETA_L": "9/10"}
    )
    return {
        "history_bits": bit_string,
        "N": {S: n_s, L: n_l},
        "E": {S: 2, L: 2},
        "joint_regime_weights": {
            "THETA_S": _fraction(Fraction(joint_s, 20000)),
            "THETA_L": _fraction(Fraction(joint_l, 20000)),
        },
        "history_weight": _fraction(Fraction(joint_s + joint_l, 20000)),
        "rho": rho,
        "predictive_hazards": {S: h_s, L: h_l},
        "UCOPE_scores": {S: score_s, L: score_l},
        "UCOPE_action": action,
        "UCOPE_margin": margin,
        "CB_AUC_scores": {S: "1", L: "1/2"},
        "CB_AUC_action": S,
        "SG_RATE_scores": {S: "1", L: "1/2"},
        "SG_RATE_action": S,
        "conditional_trial_5_auc": conditional,
    }


def _validate_boundary_literal(
    issues: list[str],
    boundary: object,
    *,
    mode: str,
) -> None:
    if not isinstance(boundary, dict):
        issues.append(f"{mode} boundary is absent")
        return
    rows = boundary.get("rows")
    if not isinstance(rows, list) or len(rows) != 16:
        issues.append(f"{mode} boundary does not retain all 16 histories")
        return
    expected_rows = []
    for bits in A1_CANONICAL_HISTORIES:
        bit_string = "".join(map(str, bits))
        n_s, n_l = sum(bits[:2]), sum(bits[2:])
        if mode == "independent_redraw":
            joint_s, joint_l = A1_JOINT_NUMERATORS[bit_string]
            half_history = Fraction(joint_s + joint_l, 40000)
            weights = {
                "THETA_S": _fraction(half_history),
                "THETA_L": _fraction(half_history),
            }
            history_weight = _fraction(Fraction(joint_s + joint_l, 20000))
            conditional = {"THETA_S": "9/5", "THETA_L": "1/5"}
        else:
            weights = {"THETA_S": "1/32", "THETA_L": "1/32"}
            history_weight = "1/16"
            conditional = {"THETA_S": "1", "THETA_L": "1"}
        expected_rows.append(
            {
                "history_bits": bit_string,
                "N": {S: n_s, L: n_l},
                "E": {S: 2, L: 2},
                "joint_regime_weights": weights,
                "history_weight": history_weight,
                "rho": "1/2",
                "predictive_hazards": {S: "1/2", L: "1/2"},
                "UCOPE_scores": {S: "1", L: "1/2"},
                "UCOPE_action": S,
                "UCOPE_margin": "1/2",
                "CB_AUC_scores": {S: "1", L: "1/2"},
                "CB_AUC_action": S,
                "SG_RATE_scores": {S: "1", L: "1/2"},
                "SG_RATE_action": S,
                "conditional_trial_5_auc": conditional,
            }
        )
    conditional_aggregate = (
        {"THETA_S": "9/5", "THETA_L": "1/5"}
        if mode == "independent_redraw"
        else {"THETA_S": "1", "THETA_L": "1"}
    )
    expected_aggregates = {
        "UCOPE_expected_auc": "1",
        "CB_AUC_expected_auc": "1",
        "AUC_gain_over_CB_AUC": "0",
        "UCOPE_terminal_coverage": "1/2",
        "CB_AUC_terminal_coverage": "1/2",
        "terminal_coverage_gain": "0",
        "UCOPE_conditional_auc_by_regime": conditional_aggregate,
    }
    if boundary != {"mode": mode, "rows": expected_rows, "aggregates": expected_aggregates}:
        issues.append(f"{mode} boundary retains count dependence or literal drift")


def _validate_activity(activity: object) -> tuple[str, ...]:
    if not isinstance(activity, dict) or set(activity) != set(A1_ACTIVITY_KEYS):
        return ("activity counters are incomplete or contain unknown keys",)
    if any(type(value) is not int or value != 0 for value in activity.values()):
        return ("registered A1 requires every activity counter to equal zero",)
    return ()


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(key) or _contains_float(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _all_rational_strings(value: object, key: str | None = None) -> bool:
    rational_keys = {
        "THETA_S",
        "THETA_L",
        S,
        L,
        "history_weight",
        "rho",
        "UCOPE_margin",
        "UCOPE_expected_auc",
        "CB_AUC_expected_auc",
        "AUC_gain_over_CB_AUC",
        "UCOPE_terminal_coverage",
        "CB_AUC_terminal_coverage",
        "terminal_coverage_gain",
    }
    if isinstance(value, dict):
        return all(_all_rational_strings(item, str(name)) for name, item in value.items())
    if isinstance(value, list):
        return all(_all_rational_strings(item, key) for item in value)
    if key in rational_keys and isinstance(value, str):
        return _FRACTION_RE.fullmatch(value) is not None
    return True

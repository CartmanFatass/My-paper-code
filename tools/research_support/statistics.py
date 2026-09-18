"""Statistical reductions whose unit of evidence is explicit.

Why this module exists: the failure mode it is built against is not a wrong formula, it is
a *right* formula applied to the wrong unit.  Two hundred evaluation episodes of one
training fit look like two hundred samples to any array library, so a naive mean over rows
reports a confidence interval about a policy class when the evidence covers exactly one
fit.  Plan section 7.3 rule 1 therefore fixes the default independent unit as the training
replicate: episodes of a replicate are aggregated first with declared weights, and only
replicate-level outcomes are summarised.  Adding more episodes to one replicate buys
precision about that fit, never a second fit.

The other invariants encoded here, each from plan 7.3:

* one independent fit has no cross-fit SD/SE/CI at all (rule 2).  A point estimate is not
  an interval of width zero, so those fields are absent with a reason rather than 0.0;
* an interval is a labelled working model: Student-t over unit means, or an explicitly
  selected replicate bootstrap with its own RNG (rule 3).  The paired bootstrap resamples
  matching blocks together by bootstrapping the paired differences;
* pairing needs real evidence.  Matching seed numbers are not a design (rule 4), so that
  token produces a refusal plus an unpaired fallback, not a paired p-value;
* every invalid, missing or non-finite source row is counted before reduction (rule 5).
  There is no silent ``dropna``;
* zero empirical variance is degenerate, not certainty, and an undefined ratio or a
  near-zero denominator is absent, not zero (rule 6);
* raw differences keep their original sign, ``a - b`` (rule 7);
* recovery keeps automatic repair, episode end and technical failure apart, reports the
  deadline fraction with explicit censoring counts, and labels a recovered-only mean as
  conditional.  No Kaplan-Meier: automatic repair is a competing event, not harmless
  independent censoring (plan 7.3, Recovery paragraph).

SciPy usage is pinned to what the installed version actually exposes.  Verified against
scipy 1.15.2 in this environment::

    scipy.stats.bootstrap(data, statistic, *, n_resamples=9999, batch=None,
                          vectorized=None, paired=False, axis=0, confidence_level=0.95,
                          alternative='two-sided', method='BCa', bootstrap_result=None,
                          rng=None)

Two consequences.  The RNG keyword is ``rng`` (not ``random_state``), and it is passed an
independent ``numpy.random.default_rng(seed)`` so bootstrap resampling never draws from -
or perturbs - a scientific RNG stream.  The interval type used is ``percentile`` rather
than the SciPy default ``BCa``: with the two-to-five replicates these reductions actually
see, the BCa acceleration estimate is unstable, and on zero-variance input BCa returns a
``nan`` interval (verified), which would be reported as "unavailable" when the honest
answer is "degenerate".  The interval type is recorded in the notes of every bootstrap
reduction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from scipy import stats as scipy_stats

from .catalog import MetricDefinition, try_metric_definition
from .records import Measured, MetricRecord, Validity

# --------------------------------------------------------------------------------------
# Declared vocabularies and thresholds
# --------------------------------------------------------------------------------------

#: Which :class:`~tools.research_support.records.MetricRecord` field carries the identity
#: of the independent unit, and the ``unit_kind`` token it maps to.  The default is the
#: training replicate; ``episode`` and ``world`` are available for explicitly conditional
#: summaries, which must be labelled as such by the caller.
UNIT_FIELD_TO_KIND: dict[str, str] = {
    "training_replicate_id": "training_replicate",
    "episode_id": "episode",
    "world_id": "world",
}

#: Pairing evidence tokens and whether each one permits a paired analysis.
PAIRING_EVIDENCE: dict[str, bool] = {
    # The two arms ran on the same identified exogenous world.
    "verified_world_identity": True,
    # A declared experimental design pairs the units (e.g. a within-replicate ablation).
    "verified_design": True,
    # Same seed integer, unverified downstream stream identity: not a design (rule 4).
    "matching_seed_number_only": False,
    # No evidence offered.
    "none": False,
}

#: Interval types supported by :func:`reduce_units` / :func:`paired_difference`.
CI_METHODS = frozenset({"student_t", "replicate_bootstrap"})

#: Bootstrap interval type actually requested from SciPy; see the module docstring.
BOOTSTRAP_INTERVAL_TYPE = "percentile"

#: Denominator magnitude at or below which a ratio is undefined rather than large.
NEAR_ZERO_DENOMINATOR = 1e-12

#: Below this many units the sample size is stated in the notes so it cannot be missed.
SMALL_N_THRESHOLD = 5

#: Relative slack when testing a value against a declared valid domain, so float noise on
#: a boundary (a ratio of 1 + 1e-16) is not reported as out-of-domain data.
_DOMAIN_TOLERANCE = 1e-9

#: Outcome vocabulary for one episode's recovery observation.
RECOVERY_OUTCOMES = (
    "recovered",
    "censored_episode_end",
    "censored_automatic_repair",
    "technical_failure",
    "never_affected",
)


# --------------------------------------------------------------------------------------
# Result records
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class UnitValue:
    """One independent unit's aggregated outcome.

    ``n_episodes`` and ``n_invalid_episodes`` stay attached to the unit because the
    precision of a replicate-level value and the evidence for the claim are different
    quantities: a replicate evaluated on 200 episodes still contributes one unit.
    """

    unit_id: str
    value: Measured
    n_episodes: int
    n_invalid_episodes: int
    weights_note: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "value": self.value.to_json(),
            "n_episodes": int(self.n_episodes),
            "n_invalid_episodes": int(self.n_invalid_episodes),
            "weights_note": self.weights_note,
        }


@dataclass(frozen=True)
class UnitAggregation:
    """Per-unit outcomes for one metric, with the exclusions that produced them.

    ``excluded`` is filled *before* any reduction, keyed by reason, so a reader can see
    that e.g. eleven rows were invalid rather than discovering a quietly smaller n.
    """

    metric_name: str
    unit_kind: str
    units: tuple[UnitValue, ...]
    excluded: dict[str, int]
    n_source_rows: int
    notes: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "unit_kind": self.unit_kind,
            "units": [unit.to_json() for unit in self.units],
            "excluded": {key: int(count) for key, count in sorted(self.excluded.items())},
            "n_excluded_rows": int(sum(self.excluded.values())),
            "n_source_rows": int(self.n_source_rows),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class Reduction:
    """Summary over independent units.

    ``ci_method`` is ``"unavailable"`` whenever no interval was computed, which is the
    honest state for a single fit: the fields are absent with a reason instead of
    collapsing to the point estimate.
    """

    metric_name: str
    unit_kind: str
    n_units: int
    point: Measured
    sd: Measured
    se: Measured
    ci_low: Measured
    ci_high: Measured
    ci_method: str
    ci_level: float
    degenerate_variance: bool
    excluded: dict[str, int]
    per_unit: tuple[UnitValue, ...]
    notes: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "unit_kind": self.unit_kind,
            "n_units": int(self.n_units),
            "point": self.point.to_json(),
            "sd": self.sd.to_json(),
            "se": self.se.to_json(),
            "ci_low": self.ci_low.to_json(),
            "ci_high": self.ci_high.to_json(),
            "ci_method": self.ci_method,
            "ci_level": float(self.ci_level),
            "degenerate_variance": bool(self.degenerate_variance),
            "excluded": {key: int(count) for key, count in sorted(self.excluded.items())},
            "per_unit": [unit.to_json() for unit in self.per_unit],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PairedReduction:
    """Summary of the paired difference ``a - b`` over matched units.

    ``pairing_status`` is part of the result rather than an argument check, because a
    refused pairing still has to be *reported*: the caller receives the refusal, the
    reason, and an unpaired fallback it may show instead.
    """

    metric_name: str
    n_pairs: int
    pairing_status: str
    point: Measured
    sd: Measured
    se: Measured
    ci_low: Measured
    ci_high: Measured
    ci_method: str
    ci_level: float
    unmatched_a: tuple[str, ...]
    unmatched_b: tuple[str, ...]
    incomplete_pairs: int
    degenerate_variance: bool
    notes: tuple[str, ...]
    fallback_unpaired: Reduction | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "n_pairs": int(self.n_pairs),
            "pairing_status": self.pairing_status,
            "point": self.point.to_json(),
            "sd": self.sd.to_json(),
            "se": self.se.to_json(),
            "ci_low": self.ci_low.to_json(),
            "ci_high": self.ci_high.to_json(),
            "ci_method": self.ci_method,
            "ci_level": float(self.ci_level),
            "unmatched_a": list(self.unmatched_a),
            "unmatched_b": list(self.unmatched_b),
            "incomplete_pairs": int(self.incomplete_pairs),
            "degenerate_variance": bool(self.degenerate_variance),
            "notes": list(self.notes),
            "fallback_unpaired": (
                None if self.fallback_unpaired is None else self.fallback_unpaired.to_json()
            ),
        }


# --------------------------------------------------------------------------------------
# Small shared helpers
# --------------------------------------------------------------------------------------


def _bump(counter: dict[str, int], key: str, amount: int = 1) -> None:
    counter[key] = counter.get(key, 0) + amount


def _dedup(items: Sequence[str]) -> tuple[str, ...]:
    """Order-preserving de-duplication, so a per-row note appears once per aggregation."""

    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _in_domain(defn: MetricDefinition | None, value: float) -> bool:
    """Domain test with a relative tolerance on the declared bounds."""

    if defn is None:
        return True
    low, high = defn.valid_domain
    scale = max(1.0, abs(float(low or 0.0)), abs(float(high or 0.0)))
    slack = _DOMAIN_TOLERANCE * scale
    if low is not None and value < float(low) - slack:
        return False
    if high is not None and value > float(high) + slack:
        return False
    return True


@dataclass(frozen=True)
class _Row:
    """One admitted source row, already resolved to a unit, a key and a weight."""

    unit_id: str
    within_key: str
    value: Any
    weight: float


def _weights_note(weights: Mapping[str, float] | None, rows: Sequence[_Row]) -> str:
    if weights is None:
        return f"equal weights over {len(rows)} contributing rows"
    total = float(sum(row.weight for row in rows))
    return (
        f"declared weights over {len(rows)} contributing rows; total weight {total:.6g}"
    )


def _prepare_rows(
    records: Sequence[MetricRecord],
    *,
    metric_name: str,
    unit_field: str,
    defn: MetricDefinition | None,
    weights: Mapping[str, float] | None,
    numeric: bool,
    excluded: dict[str, int],
    per_unit_invalid: dict[str, int],
    notes: list[str],
    prefix: str = "",
) -> tuple[list[_Row], int]:
    """Select and validate the rows of one metric, counting every refusal.

    Returns the admitted rows and the number of source rows that named this metric. Each
    refusal increments ``excluded`` under a reason key, and - when the offending row could
    still be attributed to a unit - ``per_unit_invalid`` for that unit.
    """

    rows: list[_Row] = []
    n_scanned = 0
    for index, record in enumerate(records):
        if record.metric_name != metric_name:
            continue
        n_scanned += 1
        raw_unit_id = getattr(record, unit_field, None)
        if raw_unit_id is None:
            _bump(excluded, f"{prefix}missing_unit_id")
            continue
        unit_id = str(raw_unit_id)

        measured = record.value
        if measured.validity is not Validity.OK:
            reason = measured.reason or "unspecified"
            _bump(excluded, f"{prefix}validity:{measured.validity.value}:{reason}")
            _bump(per_unit_invalid, unit_id)
            continue

        row_unit = record.unit or measured.unit
        if defn is not None and row_unit is not None and row_unit != defn.unit:
            _bump(excluded, f"{prefix}unit_mismatch")
            _bump(per_unit_invalid, unit_id)
            notes.append(
                f"unit_mismatch:{metric_name}: row unit {row_unit!r} does not match the "
                f"declared unit {defn.unit!r}; the row was excluded rather than converted"
            )
            continue

        value: Any = measured.value
        if numeric:
            if not _is_number(value):
                _bump(excluded, f"{prefix}non_numeric_value")
                _bump(per_unit_invalid, unit_id)
                continue
            value = float(value)
            if not math.isfinite(value):  # defensive: Measured already refuses these
                _bump(excluded, f"{prefix}non_finite_value")
                _bump(per_unit_invalid, unit_id)
                continue
            if not _in_domain(defn, value):
                _bump(excluded, f"{prefix}out_of_valid_domain")
                _bump(per_unit_invalid, unit_id)
                notes.append(
                    f"out_of_valid_domain:{metric_name}: at least one row fell outside the "
                    f"declared domain {defn.valid_domain if defn else None} and was excluded"
                )
                continue

        weight_key = record.world_id if record.world_id is not None else record.episode_id
        if weights is None:
            weight = 1.0
        else:
            if weight_key is None or str(weight_key) not in weights:
                # Declared weights describe a prespecified evaluation set; a row outside it
                # is not silently given weight 1, it is reported as outside the set.
                _bump(excluded, f"{prefix}no_declared_weight")
                _bump(per_unit_invalid, unit_id)
                continue
            weight = float(weights[str(weight_key)])
            if not math.isfinite(weight) or weight <= 0.0:
                _bump(excluded, f"{prefix}invalid_weight")
                _bump(per_unit_invalid, unit_id)
                continue

        within_key = record.episode_id or record.world_id or f"row:{index}"
        rows.append(_Row(unit_id, str(within_key), value, weight))
    return rows, n_scanned


def _group(rows: Sequence[_Row]) -> dict[str, list[_Row]]:
    grouped: dict[str, list[_Row]] = {}
    for row in rows:
        grouped.setdefault(row.unit_id, []).append(row)
    return grouped


def _mean_sd_se(values: np.ndarray) -> tuple[float, float, float]:
    """Point estimate, sample SD (``ddof=1``) and its standard error."""

    n = int(values.size)
    point = float(np.mean(values))
    sd = float(np.std(values, ddof=1))
    se = sd / math.sqrt(n)
    return point, sd, se


def _student_t_interval(point: float, se: float, n_units: int, ci_level: float) -> tuple[float, float]:
    """Two-sided Student-t interval over unit means with ``n_units - 1`` degrees of freedom."""

    critical = float(scipy_stats.t.ppf(0.5 + ci_level / 2.0, df=n_units - 1))
    half_width = critical * se
    return point - half_width, point + half_width


def _bootstrap_interval(
    values: np.ndarray,
    *,
    ci_level: float,
    rng_seed: int | None,
    n_resamples: int,
) -> tuple[float | None, float | None, float | None, list[str]]:
    """Percentile bootstrap over units with an independent RNG.

    Returns ``(low, high, bootstrap_se, notes)``; the bounds are ``None`` when SciPy could
    not produce a finite interval, which is reported as unavailable rather than as zero.
    """

    notes: list[str] = []
    rng = np.random.default_rng(rng_seed)
    result = scipy_stats.bootstrap(
        (values,),
        np.mean,
        n_resamples=int(n_resamples),
        confidence_level=float(ci_level),
        method=BOOTSTRAP_INTERVAL_TYPE,
        rng=rng,
    )
    low = float(result.confidence_interval.low)
    high = float(result.confidence_interval.high)
    boot_se = float(result.standard_error)
    notes.append(
        f"bootstrap: scipy.stats.bootstrap, method={BOOTSTRAP_INTERVAL_TYPE}, "
        f"n_resamples={int(n_resamples)}, rng=numpy.random.default_rng({rng_seed!r})"
    )
    if rng_seed is None:
        notes.append(
            "rng_seed=None: the bootstrap interval is not reproducible; record a seed "
            "before publishing the interval"
        )
    if math.isfinite(boot_se):
        notes.append(f"bootstrap_standard_error={boot_se:.6g}")
    if not (math.isfinite(low) and math.isfinite(high)):
        notes.append(
            "bootstrap returned a non-finite interval; reported as unavailable rather "
            "than forced to the point estimate"
        )
        return None, None, (boot_se if math.isfinite(boot_se) else None), notes
    return low, high, (boot_se if math.isfinite(boot_se) else None), notes


def _validate_ci_args(ci_method: str, ci_level: float, n_resamples: int) -> None:
    if ci_method not in CI_METHODS:
        raise ValueError(
            f"unknown ci_method {ci_method!r}; expected one of {sorted(CI_METHODS)}"
        )
    if not 0.0 < float(ci_level) < 1.0:
        raise ValueError(f"ci_level must lie in (0, 1); got {ci_level!r}")
    if int(n_resamples) < 1:
        raise ValueError(f"n_resamples must be positive; got {n_resamples!r}")


# --------------------------------------------------------------------------------------
# Episodes -> independent units
# --------------------------------------------------------------------------------------


def aggregate_episodes_to_units(
    records: Sequence[MetricRecord],
    *,
    metric_name: str,
    unit_field: str = "training_replicate_id",
    weights: Mapping[str, float] | None = None,
    catalog_lookup: Callable[[str], MetricDefinition | None] | None = None,
) -> UnitAggregation:
    """Aggregate a metric's rows into one value per independent unit.

    This is the step that fixes the statistical unit (plan 7.3 rule 1). Rows are grouped by
    ``unit_field`` - the training replicate by default - and combined with the reducer the
    catalog declares for the metric:

    ``mean``/``sum``    weighted by the declared weights (equal weights by default);
    ``median``          unweighted median of the unit's rows, since a weighted median of
                        two or three evaluation worlds is not better defined than the
                        weights are;
    ``ratio_of_sums``   recomputed as ``sum(numerator) / sum(denominator)`` from the
                        component rows when they are present, and only otherwise from the
                        per-episode ratios, with a note saying so;
    ``categorical``     not averaged: a unit whose rows disagree gets an absent value.

    ``weights`` maps a within-unit key - the ``world_id`` when present, otherwise the
    ``episode_id`` - to a positive weight. When weights are declared, a row whose key is
    not in the mapping is *excluded and counted* rather than given weight 1, because
    declared weights describe a prespecified evaluation set.
    """

    lookup = catalog_lookup if catalog_lookup is not None else try_metric_definition
    unit_kind = UNIT_FIELD_TO_KIND.get(unit_field)
    if unit_kind is None:
        raise ValueError(
            f"unsupported unit_field {unit_field!r}; expected one of "
            f"{sorted(UNIT_FIELD_TO_KIND)}"
        )

    defn = lookup(metric_name)
    notes: list[str] = []
    if defn is None:
        notes.append(
            f"metric_not_in_catalog:{metric_name}: reduced with a plain weighted mean and "
            "no declared unit, direction or valid domain; register a definition before "
            "publishing this number"
        )
    reducer = defn.reducer if defn is not None else "mean"

    if reducer == "ratio_of_sums" and defn is not None:
        return _aggregate_ratio(
            records,
            defn=defn,
            unit_field=unit_field,
            unit_kind=unit_kind,
            weights=weights,
            lookup=lookup,
            notes=notes,
        )

    excluded: dict[str, int] = {}
    per_unit_invalid: dict[str, int] = {}
    numeric = reducer != "categorical"
    rows, n_source_rows = _prepare_rows(
        records,
        metric_name=metric_name,
        unit_field=unit_field,
        defn=defn,
        weights=weights,
        numeric=numeric,
        excluded=excluded,
        per_unit_invalid=per_unit_invalid,
        notes=notes,
    )

    units: list[UnitValue] = []
    grouped = _group(rows)
    for unit_id in sorted(set(grouped) | set(per_unit_invalid)):
        unit_rows = grouped.get(unit_id, [])
        n_episodes = len({row.within_key for row in unit_rows})
        n_invalid = per_unit_invalid.get(unit_id, 0)
        if not unit_rows:
            units.append(
                UnitValue(
                    unit_id=unit_id,
                    value=Measured.absent(
                        Validity.NOT_RECORDED, "no_usable_rows_for_unit"
                    ),
                    n_episodes=0,
                    n_invalid_episodes=n_invalid,
                    weights_note=None,
                )
            )
            continue
        value = _reduce_within_unit(unit_rows, reducer=reducer, defn=defn, notes=notes)
        units.append(
            UnitValue(
                unit_id=unit_id,
                value=value,
                n_episodes=n_episodes,
                n_invalid_episodes=n_invalid,
                weights_note=f"{reducer}; {_weights_note(weights, unit_rows)}",
            )
        )

    if reducer == "sum":
        counts = {unit.n_episodes for unit in units if unit.n_episodes}
        if len(counts) > 1:
            notes.append(
                "extensive_reducer_with_unequal_row_counts: this metric is summed within a "
                f"unit and the units contributed {sorted(counts)} rows, so their totals are "
                "not on a common scale; compare only units evaluated on the same set"
            )

    return UnitAggregation(
        metric_name=metric_name,
        unit_kind=unit_kind,
        units=tuple(units),
        excluded=excluded,
        n_source_rows=n_source_rows,
        notes=_dedup(notes),
    )


def _reduce_within_unit(
    rows: Sequence[_Row],
    *,
    reducer: str,
    defn: MetricDefinition | None,
    notes: list[str],
) -> Measured:
    """Combine one unit's rows according to the declared reducer."""

    unit_label = defn.unit if defn is not None else None

    if reducer == "categorical":
        labels = {row.value for row in rows}
        if len(labels) == 1:
            # Carried as text on purpose: a skill identifier is a label, and keeping it out
            # of the float domain is what stops a later mean over units from producing
            # "skill 2.4" (plan 7.3 rule 9).
            return Measured.ok(str(next(iter(labels))), unit=unit_label)
        notes.append(
            "categorical_metric_not_averaged: a unit's rows carry different labels; the "
            "unit has no single value, because averaging identifiers is meaningless "
            "(plan 7.3 rule 9)"
        )
        return Measured.absent(
            Validity.NOT_APPLICABLE, "categorical_metric_not_averaged", unit=unit_label
        )

    values = np.asarray([float(row.value) for row in rows], dtype=np.float64)
    weights = np.asarray([row.weight for row in rows], dtype=np.float64)

    if reducer == "median":
        if float(weights.min()) != float(weights.max()):
            notes.append(
                "median_ignores_declared_weights: the declared weights are unequal, but a "
                "median is computed unweighted; use a mean reducer if the weights must act"
            )
        return Measured.ok(float(np.median(values)), unit=unit_label)

    total_weight = float(weights.sum())
    if reducer == "sum":
        return Measured.ok(float(np.sum(values * weights)), unit=unit_label)

    # Default and "mean": weighted mean.
    if total_weight <= 0.0:
        return Measured.absent(Validity.INVALID, "zero_total_weight", unit=unit_label)
    return Measured.ok(float(np.sum(values * weights) / total_weight), unit=unit_label)


def _aggregate_ratio(
    records: Sequence[MetricRecord],
    *,
    defn: MetricDefinition,
    unit_field: str,
    unit_kind: str,
    weights: Mapping[str, float] | None,
    lookup: Callable[[str], MetricDefinition | None],
    notes: list[str],
) -> UnitAggregation:
    """Recompute a ratio metric from summed components, or say why it could not be.

    Averaging per-episode ratios and dividing summed volumes are different estimators and
    disagree whenever the denominators differ, so the fallback path is always announced.
    """

    excluded: dict[str, int] = {}
    per_unit_invalid: dict[str, int] = {}

    numerator = defn.numerator or ""
    denominator = defn.denominator or ""
    has_numerator_rows = any(record.metric_name == numerator for record in records)
    has_denominator_rows = any(record.metric_name == denominator for record in records)

    if not (has_numerator_rows and has_denominator_rows):
        missing = [
            name
            for name, present in ((numerator, has_numerator_rows), (denominator, has_denominator_rows))
            if not present
        ]
        notes.append(
            f"ratio_averaged_from_per_episode_values:{defn.name}: no rows for "
            f"{', '.join(missing)}, so each unit value is a weighted mean of per-episode "
            "ratios instead of sum(numerator)/sum(denominator); the two differ whenever the "
            "denominators differ (plan 7.3: ratios are recomputed from denominators where "
            "possible)"
        )
        rows, n_source_rows = _prepare_rows(
            records,
            metric_name=defn.name,
            unit_field=unit_field,
            defn=defn,
            weights=weights,
            numeric=True,
            excluded=excluded,
            per_unit_invalid=per_unit_invalid,
            notes=notes,
        )
        units: list[UnitValue] = []
        grouped = _group(rows)
        for unit_id in sorted(set(grouped) | set(per_unit_invalid)):
            unit_rows = grouped.get(unit_id, [])
            n_invalid = per_unit_invalid.get(unit_id, 0)
            if not unit_rows:
                units.append(
                    UnitValue(
                        unit_id=unit_id,
                        value=Measured.absent(
                            Validity.NOT_RECORDED, "no_usable_rows_for_unit"
                        ),
                        n_episodes=0,
                        n_invalid_episodes=n_invalid,
                    )
                )
                continue
            value = _reduce_within_unit(unit_rows, reducer="mean", defn=defn, notes=notes)
            units.append(
                UnitValue(
                    unit_id=unit_id,
                    value=value,
                    n_episodes=len({row.within_key for row in unit_rows}),
                    n_invalid_episodes=n_invalid,
                    weights_note=(
                        "mean of per-episode ratios (components unavailable); "
                        f"{_weights_note(weights, unit_rows)}"
                    ),
                )
            )
        return UnitAggregation(
            metric_name=defn.name,
            unit_kind=unit_kind,
            units=tuple(units),
            excluded=excluded,
            n_source_rows=n_source_rows,
            notes=_dedup(notes),
        )

    numerator_rows, n_numerator = _prepare_rows(
        records,
        metric_name=numerator,
        unit_field=unit_field,
        defn=lookup(numerator),
        weights=weights,
        numeric=True,
        excluded=excluded,
        per_unit_invalid=per_unit_invalid,
        notes=notes,
        prefix="numerator:",
    )
    denominator_rows, n_denominator = _prepare_rows(
        records,
        metric_name=denominator,
        unit_field=unit_field,
        defn=lookup(denominator),
        weights=weights,
        numeric=True,
        excluded=excluded,
        per_unit_invalid=per_unit_invalid,
        notes=notes,
        prefix="denominator:",
    )
    notes.append(
        f"ratio_recomputed_from_sums:{defn.name} = sum({numerator}) / sum({denominator}) "
        "within each unit"
    )

    numerator_by_unit = _group(numerator_rows)
    denominator_by_unit = _group(denominator_rows)
    units = []
    unit_ids = sorted(set(numerator_by_unit) | set(denominator_by_unit) | set(per_unit_invalid))
    for unit_id in unit_ids:
        num_rows = numerator_by_unit.get(unit_id, [])
        den_rows = denominator_by_unit.get(unit_id, [])
        n_episodes = len(
            {row.within_key for row in num_rows} | {row.within_key for row in den_rows}
        )
        n_invalid = per_unit_invalid.get(unit_id, 0)
        weights_note = (
            f"ratio of summed {numerator} over summed {denominator}; "
            f"{_weights_note(weights, list(num_rows) + list(den_rows))}"
        )

        if not den_rows:
            value = Measured.absent(
                Validity.UNKNOWN, "ratio_denominator_rows_absent", unit=defn.unit
            )
        else:
            den_sum = float(sum(row.weight * float(row.value) for row in den_rows))
            if abs(den_sum) <= NEAR_ZERO_DENOMINATOR:
                # Rule 6: an undefined ratio is absent, never 0.0 and never "fully served".
                value = Measured.absent(
                    Validity.INVALID, "zero_denominator", unit=defn.unit
                )
            elif not num_rows:
                value = Measured.absent(
                    Validity.UNKNOWN, "ratio_numerator_rows_absent", unit=defn.unit
                )
            else:
                num_sum = float(sum(row.weight * float(row.value) for row in num_rows))
                ratio = num_sum / den_sum
                if not _in_domain(defn, ratio):
                    notes.append(
                        f"ratio_out_of_valid_domain:{defn.name}: unit {unit_id} recomputed "
                        f"to {ratio:.6g}, outside {defn.valid_domain}; the components "
                        "disagree with the declared semantics and the value is not reported"
                    )
                    value = Measured.absent(
                        Validity.INVALID, "recomputed_ratio_out_of_valid_domain",
                        unit=defn.unit,
                    )
                else:
                    value = Measured.ok(ratio, unit=defn.unit)

        units.append(
            UnitValue(
                unit_id=unit_id,
                value=value,
                n_episodes=n_episodes,
                n_invalid_episodes=n_invalid,
                weights_note=weights_note,
            )
        )

    return UnitAggregation(
        metric_name=defn.name,
        unit_kind=unit_kind,
        units=tuple(units),
        excluded=excluded,
        n_source_rows=n_numerator + n_denominator,
        notes=_dedup(notes),
    )


# --------------------------------------------------------------------------------------
# Units -> summary
# --------------------------------------------------------------------------------------


def reduce_units(
    aggregation: UnitAggregation,
    *,
    ci_method: str = "student_t",
    ci_level: float = 0.95,
    rng_seed: int | None = None,
    n_resamples: int = 9999,
) -> Reduction:
    """Summarise independent units: mean, cross-unit SD/SE and a labelled interval.

    Units enter the summary with equal weight: they are the independent replicates, and a
    replicate evaluated on more episodes is a more precisely measured unit, not a heavier
    one. Units whose value is absent are excluded and counted, never treated as zero.
    """

    _validate_ci_args(ci_method, ci_level, n_resamples)

    notes = list(aggregation.notes)
    excluded = dict(aggregation.excluded)
    metric_name = aggregation.metric_name
    unit_kind = aggregation.unit_kind

    usable: list[UnitValue] = []
    non_numeric: list[UnitValue] = []
    for unit in aggregation.units:
        if unit.value.validity is not Validity.OK:
            reason = unit.value.reason or "unspecified"
            _bump(excluded, f"unit_value_absent:{unit.value.validity.value}:{reason}")
            continue
        if _is_number(unit.value.value):
            usable.append(unit)
        else:
            non_numeric.append(unit)

    unit_label = next(
        (unit.value.unit for unit in aggregation.units if unit.value.unit is not None), None
    )

    def _unavailable(reason: str, *, point: Measured) -> Reduction:
        absent = Measured.absent(Validity.NOT_APPLICABLE, reason, unit=unit_label)
        return Reduction(
            metric_name=metric_name,
            unit_kind=unit_kind,
            n_units=len(usable),
            point=point,
            sd=absent,
            se=absent,
            ci_low=absent,
            ci_high=absent,
            ci_method="unavailable",
            ci_level=float(ci_level),
            degenerate_variance=False,
            excluded=excluded,
            per_unit=tuple(aggregation.units),
            notes=_dedup(notes),
        )

    if non_numeric and not usable:
        labels = sorted({str(unit.value.value) for unit in non_numeric})
        notes.append(
            "non_numeric_unit_values_not_averaged: the units carry labels "
            f"({', '.join(labels)}); report them as counts per category, not as a mean "
            "(plan 7.3 rule 9)"
        )
        return _unavailable(
            "non_numeric_unit_values_not_averaged",
            point=Measured.absent(
                Validity.NOT_APPLICABLE, "non_numeric_unit_values_not_averaged",
                unit=unit_label,
            ),
        )
    if non_numeric:
        _bump(excluded, "unit_value_non_numeric", len(non_numeric))
        notes.append(
            f"unit_value_non_numeric: {len(non_numeric)} unit(s) carry a non-numeric value "
            "and were excluded from the mean"
        )

    if not usable:
        notes.append(
            f"no_usable_units: every unit value for {metric_name} was absent; the excluded "
            "counts carry the reasons"
        )
        return _unavailable(
            "no_usable_units",
            point=Measured.absent(Validity.NOT_RECORDED, "no_usable_units", unit=unit_label),
        )

    values = np.asarray([float(unit.value.value) for unit in usable], dtype=np.float64)
    n_units = int(values.size)

    if n_units == 1:
        # Rule 2: one fit gives an observed performance, not an interval of width zero.
        notes.append(
            "single_independent_fit: cross-fit SD, SE and CI are unavailable with one "
            f"{unit_kind}; report evaluation variability separately and label it as "
            "conditional on this fit"
        )
        absent = Measured.absent(
            Validity.NOT_APPLICABLE, "single_independent_fit", unit=unit_label
        )
        return Reduction(
            metric_name=metric_name,
            unit_kind=unit_kind,
            n_units=1,
            point=Measured.ok(float(values[0]), unit=unit_label),
            sd=absent,
            se=absent,
            ci_low=absent,
            ci_high=absent,
            ci_method="unavailable",
            ci_level=float(ci_level),
            degenerate_variance=False,
            excluded=excluded,
            per_unit=tuple(aggregation.units),
            notes=_dedup(notes),
        )

    point, sd, se = _mean_sd_se(values)
    degenerate = sd == 0.0
    if n_units < SMALL_N_THRESHOLD:
        notes.append(f"small_n: n_units={n_units} ({unit_kind}); the interval is wide and "
                     "its coverage rests on the working model, not on the data")
    if degenerate:
        notes.append(
            "degenerate_variance: the units have zero empirical variance, so the interval "
            "has zero width; that is a degenerate sample, not evidence of certainty "
            "(plan 7.3 rule 6)"
        )

    ci_low_value: float | None
    ci_high_value: float | None
    if ci_method == "student_t":
        ci_low_value, ci_high_value = _student_t_interval(point, se, n_units, ci_level)
        notes.append(
            f"ci: Student-t over {n_units} {unit_kind} means, df={n_units - 1}, "
            f"ddof=1, level={ci_level:.3f}"
        )
    else:
        ci_low_value, ci_high_value, _boot_se, boot_notes = _bootstrap_interval(
            values, ci_level=ci_level, rng_seed=rng_seed, n_resamples=n_resamples
        )
        notes.extend(boot_notes)

    if ci_low_value is None or ci_high_value is None:
        ci_low = Measured.absent(
            Validity.INVALID, "bootstrap_interval_unavailable", unit=unit_label
        )
        ci_high = ci_low
        method_label = ci_method
    else:
        ci_low = Measured.ok(float(ci_low_value), unit=unit_label)
        ci_high = Measured.ok(float(ci_high_value), unit=unit_label)
        method_label = ci_method

    return Reduction(
        metric_name=metric_name,
        unit_kind=unit_kind,
        n_units=n_units,
        point=Measured.ok(point, unit=unit_label),
        sd=Measured.ok(sd, unit=unit_label),
        se=Measured.ok(se, unit=unit_label),
        ci_low=ci_low,
        ci_high=ci_high,
        ci_method=method_label,
        ci_level=float(ci_level),
        degenerate_variance=bool(degenerate),
        excluded=excluded,
        per_unit=tuple(aggregation.units),
        notes=_dedup(notes),
    )


# --------------------------------------------------------------------------------------
# Paired difference
# --------------------------------------------------------------------------------------


def paired_difference(
    a: UnitAggregation,
    b: UnitAggregation,
    *,
    pairing_evidence: str,
    ci_method: str = "student_t",
    ci_level: float = 0.95,
    rng_seed: int | None = None,
    n_resamples: int = 9999,
) -> PairedReduction:
    """Summarise the per-unit difference ``a - b`` when the pairing is actually evidenced.

    ``pairing_evidence`` must be one of :data:`PAIRING_EVIDENCE`. ``verified_world_identity``
    and ``verified_design`` permit a paired analysis; ``matching_seed_number_only`` and
    ``none`` are refused (plan 7.3 rule 4: matching seed numbers are not a design), and the
    result then carries ``fallback_unpaired``, an ordinary unpaired reduction over ``a``,
    so the caller has something honest to display.

    Differences keep the raw sign ``a - b`` (rule 7). No orientation by "improvement" is
    applied here; a display that wants one must state the transformation itself.
    """

    _validate_ci_args(ci_method, ci_level, n_resamples)
    if pairing_evidence not in PAIRING_EVIDENCE:
        raise ValueError(
            f"unknown pairing_evidence {pairing_evidence!r}; expected one of "
            f"{sorted(PAIRING_EVIDENCE)}"
        )
    if a.metric_name != b.metric_name:
        raise ValueError(
            f"cannot pair different metrics: {a.metric_name!r} vs {b.metric_name!r}"
        )

    metric_name = a.metric_name
    notes: list[str] = [f"pairing_evidence={pairing_evidence}", "difference sign is a - b"]
    a_units = {unit.unit_id: unit for unit in a.units}
    b_units = {unit.unit_id: unit for unit in b.units}
    unmatched_a = tuple(sorted(set(a_units) - set(b_units)))
    unmatched_b = tuple(sorted(set(b_units) - set(a_units)))

    unit_label = next(
        (unit.value.unit for unit in (*a.units, *b.units) if unit.value.unit is not None),
        None,
    )

    def _refuse(status: str, reason: str, message: str) -> PairedReduction:
        absent = Measured.absent(Validity.NOT_APPLICABLE, reason, unit=unit_label)
        notes.append(message)
        fallback = reduce_units(
            a,
            ci_method=ci_method,
            ci_level=ci_level,
            rng_seed=rng_seed,
            n_resamples=n_resamples,
        )
        return PairedReduction(
            metric_name=metric_name,
            n_pairs=0,
            pairing_status=status,
            point=absent,
            sd=absent,
            se=absent,
            ci_low=absent,
            ci_high=absent,
            ci_method="unavailable",
            ci_level=float(ci_level),
            unmatched_a=unmatched_a,
            unmatched_b=unmatched_b,
            incomplete_pairs=0,
            degenerate_variance=False,
            notes=_dedup(notes),
            fallback_unpaired=fallback,
        )

    if not PAIRING_EVIDENCE[pairing_evidence]:
        status = (
            "pairing_unverified"
            if pairing_evidence == "matching_seed_number_only"
            else "unpaired"
        )
        if pairing_evidence == "matching_seed_number_only":
            message = (
                "pairing refused: matching seed numbers are not a verified matching rule - "
                "the same integer does not make two runs share an exogenous world or a "
                "stream identity (plan 7.3 rule 4). Reporting an unpaired summary over a "
                "instead; supply verified_world_identity or verified_design to pair."
            )
        else:
            message = (
                "pairing refused: no pairing evidence was offered, so the units are treated "
                "as unpaired and an unpaired summary over a is reported instead "
                "(plan 7.3 rule 4)."
            )
        return _refuse(status, f"pairing_refused:{pairing_evidence}", message)

    if a.unit_kind != b.unit_kind:
        return _refuse(
            "unpaired",
            "pairing_refused:unit_kind_mismatch",
            "pairing refused: the two aggregations use different statistical units "
            f"({a.unit_kind} vs {b.unit_kind}), so their unit ids do not denote the same "
            "objects.",
        )

    matched_ids = sorted(set(a_units) & set(b_units))
    differences: list[float] = []
    incomplete = 0
    for unit_id in matched_ids:
        value_a = a_units[unit_id].value
        value_b = b_units[unit_id].value
        if (
            value_a.validity is not Validity.OK
            or value_b.validity is not Validity.OK
            or not _is_number(value_a.value)
            or not _is_number(value_b.value)
        ):
            incomplete += 1
            continue
        differences.append(float(value_a.value) - float(value_b.value))

    if unmatched_a or unmatched_b or incomplete:
        notes.append(
            f"incomplete pairing: {len(unmatched_a)} unit(s) only in a, "
            f"{len(unmatched_b)} only in b, {incomplete} matched pair(s) with an absent "
            "value; the complete-pair subset below is not the full batch (plan 7.3 rule 5)"
        )

    n_pairs = len(differences)
    if n_pairs == 0:
        absent = Measured.absent(Validity.NOT_RECORDED, "no_complete_pairs", unit=unit_label)
        notes.append("no complete pairs remained after matching")
        return PairedReduction(
            metric_name=metric_name,
            n_pairs=0,
            pairing_status="verified",
            point=absent,
            sd=absent,
            se=absent,
            ci_low=absent,
            ci_high=absent,
            ci_method="unavailable",
            ci_level=float(ci_level),
            unmatched_a=unmatched_a,
            unmatched_b=unmatched_b,
            incomplete_pairs=incomplete,
            degenerate_variance=False,
            notes=_dedup(notes),
            fallback_unpaired=None,
        )

    diffs = np.asarray(differences, dtype=np.float64)
    point = float(np.mean(diffs))

    if n_pairs == 1:
        notes.append(
            "single_pair: one matched pair gives an observed difference, not an interval "
            "(plan 7.3 rule 2)"
        )
        absent = Measured.absent(Validity.NOT_APPLICABLE, "single_pair", unit=unit_label)
        return PairedReduction(
            metric_name=metric_name,
            n_pairs=1,
            pairing_status="verified",
            point=Measured.ok(point, unit=unit_label),
            sd=absent,
            se=absent,
            ci_low=absent,
            ci_high=absent,
            ci_method="unavailable",
            ci_level=float(ci_level),
            unmatched_a=unmatched_a,
            unmatched_b=unmatched_b,
            incomplete_pairs=incomplete,
            degenerate_variance=False,
            notes=_dedup(notes),
            fallback_unpaired=None,
        )

    point, sd, se = _mean_sd_se(diffs)
    degenerate = sd == 0.0
    if n_pairs < SMALL_N_THRESHOLD:
        notes.append(f"small_n: n_pairs={n_pairs}")
    if degenerate:
        notes.append(
            "degenerate_variance: every pair produced the same difference, so the interval "
            "has zero width; a degenerate sample is not proof of certainty"
        )

    if ci_method == "student_t":
        low, high = _student_t_interval(point, se, n_pairs, ci_level)
        notes.append(
            f"ci: Student-t over {n_pairs} paired differences, df={n_pairs - 1}, "
            f"ddof=1, level={ci_level:.3f}"
        )
    else:
        # A paired bootstrap must resample matching blocks together. Bootstrapping the
        # differences does exactly that: one resampled index draws both arms of a pair.
        # (scipy 1.15.2 also offers paired=True over two samples; it is equivalent here and
        # was verified to give the same interval for the same seed.)
        low, high, _boot_se, boot_notes = _bootstrap_interval(
            diffs, ci_level=ci_level, rng_seed=rng_seed, n_resamples=n_resamples
        )
        notes.extend(boot_notes)
        notes.append(
            "paired bootstrap: matched blocks are resampled together by bootstrapping the "
            "per-pair differences"
        )

    if low is None or high is None:
        ci_low = Measured.absent(
            Validity.INVALID, "bootstrap_interval_unavailable", unit=unit_label
        )
        ci_high = ci_low
    else:
        ci_low = Measured.ok(float(low), unit=unit_label)
        ci_high = Measured.ok(float(high), unit=unit_label)

    return PairedReduction(
        metric_name=metric_name,
        n_pairs=n_pairs,
        pairing_status="verified",
        point=Measured.ok(point, unit=unit_label),
        sd=Measured.ok(sd, unit=unit_label),
        se=Measured.ok(se, unit=unit_label),
        ci_low=ci_low,
        ci_high=ci_high,
        ci_method=ci_method,
        ci_level=float(ci_level),
        unmatched_a=unmatched_a,
        unmatched_b=unmatched_b,
        incomplete_pairs=incomplete,
        degenerate_variance=bool(degenerate),
        notes=_dedup(notes),
        fallback_unpaired=None,
    )


# --------------------------------------------------------------------------------------
# Recovery
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RecoveryOutcome:
    """One episode's recovery observation.

    The outcome vocabulary keeps apart the three ways an episode can end without a UAV
    recovery: the episode simply ended, an automatic site repair restored service first (a
    competing event, not harmless censoring), or the run failed technically and carries no
    observation at all. A non-recovered outcome may not carry a time: the constructor
    refuses it, because an unrecovered episode with ``time_to_recovery_s = 0`` is the exact
    fabrication plan 7.3 forbids.
    """

    episode_id: str
    outcome: str
    time_to_recovery_s: Measured
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in RECOVERY_OUTCOMES:
            raise ValueError(
                f"unknown recovery outcome {self.outcome!r}; expected one of "
                f"{list(RECOVERY_OUTCOMES)}"
            )
        measured = self.time_to_recovery_s
        if self.outcome != "recovered" and measured.validity is Validity.OK:
            raise ValueError(
                f"{self.episode_id}: outcome {self.outcome!r} must not carry a "
                "time_to_recovery_s value; an unrecovered episode has no recovery time"
            )
        if measured.validity is Validity.OK and not _is_number(measured.value):
            raise ValueError(
                f"{self.episode_id}: time_to_recovery_s must be numeric when present"
            )

    def to_json(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "outcome": self.outcome,
            "time_to_recovery_s": self.time_to_recovery_s.to_json(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RecoverySummary:
    """Outcome mix, deadline fraction and a conditional recovered-only mean."""

    n_episodes: int
    outcomes_by_kind: dict[str, int]
    recovery_fraction_at_deadline: Measured
    deadline_s: float
    conditional_mean_recovered_s: Measured
    notes: tuple[str, ...]
    per_episode: tuple[RecoveryOutcome, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "n_episodes": int(self.n_episodes),
            "outcomes_by_kind": {k: int(v) for k, v in self.outcomes_by_kind.items()},
            "recovery_fraction_at_deadline": self.recovery_fraction_at_deadline.to_json(),
            "deadline_s": float(self.deadline_s),
            "conditional_mean_recovered_s": self.conditional_mean_recovered_s.to_json(),
            "notes": list(self.notes),
            "per_episode": [outcome.to_json() for outcome in self.per_episode],
        }


def recovery_outcome_from_report(
    report: Mapping[str, Any], *, episode_id: str
) -> RecoveryOutcome:
    """Map ``envs/uav_service_restoration/evaluation.py:recovery_report()`` onto an outcome.

    Written here so the censoring taxonomy is translated once instead of being re-derived
    by every caller. The mapping follows that module's own reasons:
    ``repaired_before_recovery_threshold_reached`` and
    ``threshold_first_met_after_automatic_repair`` are automatic-repair censoring;
    ``episode_ended_before_failure`` and ``threshold_not_reached_within_episode`` are
    episode-end censoring; ``applicable=False`` means the failure harmed nothing, which is
    ``never_affected`` rather than a failure to recover. Technical failure is not something
    ``recovery_report`` can express, so it is never produced here; a runner that lost an
    episode constructs that outcome itself.
    """

    if not report.get("applicable", False):
        return RecoveryOutcome(
            episode_id=episode_id,
            outcome="never_affected",
            time_to_recovery_s=Measured.absent(
                Validity.NOT_APPLICABLE, "episode_not_affected", unit="s"
            ),
            reason=str(report.get("reason") or "not_applicable"),
        )
    time_value = report.get("time_to_recovery_s")
    censoring_reason = report.get("censoring_reason")
    if not report.get("censored", False) and time_value is not None:
        return RecoveryOutcome(
            episode_id=episode_id,
            outcome="recovered",
            time_to_recovery_s=Measured.from_float(time_value, unit="s"),
            reason=None,
        )
    repair_reasons = {
        "repaired_before_recovery_threshold_reached",
        "threshold_first_met_after_automatic_repair",
    }
    outcome = (
        "censored_automatic_repair"
        if censoring_reason in repair_reasons
        else "censored_episode_end"
    )
    return RecoveryOutcome(
        episode_id=episode_id,
        outcome=outcome,
        time_to_recovery_s=Measured.absent(
            Validity.NOT_APPLICABLE, str(censoring_reason or "censored"), unit="s"
        ),
        reason=str(censoring_reason) if censoring_reason is not None else None,
    )


def recovery_summary(
    outcomes: Sequence[RecoveryOutcome], *, deadline_s: float
) -> RecoverySummary:
    """Describe a set of recovery observations without inventing a survival model.

    ``recovery_fraction_at_deadline`` counts episodes recovered within ``deadline_s`` over
    the affected episodes whose outcome is determinable (recovered or censored). Episodes
    the failure never affected are outside the question; technically failed episodes carry
    no observation, so they are excluded from the denominator *and* the notes state both
    the exclusion and the fraction that including them as unrecovered would give, so the
    choice is visible instead of buried.

    ``conditional_mean_recovered_s`` averages recovered episodes only. That is a mean
    conditional on recovery, not an expected recovery time, and the notes say so. No
    Kaplan-Meier estimate is produced: automatic repair is a competing event that can
    restore service the UAVs did not, so treating it as independent censoring would bias
    the result in the policy's favour.
    """

    if not math.isfinite(float(deadline_s)) or float(deadline_s) <= 0.0:
        raise ValueError(f"deadline_s must be a positive finite time; got {deadline_s!r}")

    deadline = float(deadline_s)
    counts: dict[str, int] = {kind: 0 for kind in RECOVERY_OUTCOMES}
    recovered_times: list[float] = []
    recovered_without_time = 0
    recovered_by_deadline = 0

    for outcome in outcomes:
        counts[outcome.outcome] = counts.get(outcome.outcome, 0) + 1
        if outcome.outcome != "recovered":
            continue
        measured = outcome.time_to_recovery_s
        if measured.validity is not Validity.OK:
            recovered_without_time += 1
            continue
        time_value = float(measured.value)
        recovered_times.append(time_value)
        if time_value <= deadline:
            recovered_by_deadline += 1

    n_episodes = len(outcomes)
    n_technical = counts["technical_failure"]
    determinable = (
        counts["recovered"]
        + counts["censored_episode_end"]
        + counts["censored_automatic_repair"]
    )

    notes: list[str] = [
        f"deadline_s={deadline:.6g}",
        "recovery_fraction_at_deadline = episodes recovered within the deadline / affected "
        "episodes with a determinable outcome; censoring counts are in outcomes_by_kind",
        "censored_automatic_repair is a competing event, not harmless independent "
        "censoring: no Kaplan-Meier or survival estimate is implied (plan 7.3 Recovery)",
        "censored and never_affected episodes are retained with no recovery time; an "
        "unrecovered episode is never recorded as 0 s",
    ]

    if determinable == 0:
        fraction = Measured.absent(
            Validity.NOT_APPLICABLE, "no_affected_episodes_with_determinable_outcome"
        )
        notes.append(
            "no affected episode had a determinable outcome, so the deadline fraction is "
            "unavailable rather than 0.0"
        )
    else:
        fraction = Measured.ok(recovered_by_deadline / determinable, unit="ratio")

    if n_technical:
        including = recovered_by_deadline / (determinable + n_technical)
        notes.append(
            f"excluded {n_technical} technical_failure episode(s) from the denominator "
            "because they carry no observation; counting them as not recovered would give "
            f"{including:.6g} instead"
        )
    if recovered_without_time:
        notes.append(
            f"{recovered_without_time} recovered episode(s) carry no time_to_recovery_s; "
            "they count as affected but cannot count towards the deadline numerator"
        )
    if counts["never_affected"]:
        notes.append(
            f"{counts['never_affected']} episode(s) were never affected by a capability "
            "loss and are outside the recovery question, not failures to recover"
        )

    if recovered_times:
        conditional = Measured.ok(float(np.mean(recovered_times)), unit="s")
        notes.append(
            "conditional_mean_recovered_s is CONDITIONAL on recovery: it averages the "
            f"{len(recovered_times)} recovered episode(s) only and excludes "
            f"{counts['censored_episode_end'] + counts['censored_automatic_repair']} "
            "censored episode(s); it is not an expected recovery time, and it falls as "
            "fewer slow episodes manage to recover"
        )
    else:
        conditional = Measured.absent(
            Validity.NOT_APPLICABLE, "no_recovered_episodes_with_a_time", unit="s"
        )
        notes.append(
            "no recovered episode carried a time, so the conditional mean is unavailable "
            "rather than 0.0"
        )

    return RecoverySummary(
        n_episodes=n_episodes,
        outcomes_by_kind=counts,
        recovery_fraction_at_deadline=fraction,
        deadline_s=deadline,
        conditional_mean_recovered_s=conditional,
        notes=_dedup(notes),
        per_episode=tuple(outcomes),
    )

"""Finite Headland-90 rate maps, selectors, aliases, and schema checks.

This module is deliberately construction-only.  It enumerates exact rational
controllers and compares caller-supplied summaries; it has no coordinate
encoder, hash-to-random-word function, simulator hook, or output writer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import math
import struct

from .config import ControllerSpec, DT, PRODUCTION_NAMESPACE
from .event_transform import event_transform as _event_transform


Q = tuple(Fraction(i, 8) for i in range(8))
FLEX_INTERCEPTS = tuple(Fraction(i, 8) for i in (1, 3, 5, 7))
FLEX_SLOPE = Fraction(1, 8)
STRATA = ("S", "L")
LOGICAL_HELD_OUT_TAGS = (
    "GLOBAL-BEST",
    "TWO-STRATUM/C*",
    "FLEX-CONTAIN",
    "C_S<-L",
    "C_L<-S",
)
COORDINATE_FIELDS = (
    "namespace",
    "split",
    "replicate",
    "block",
    "class",
    "template",
    "tick",
    "stream",
    "lane",
)
COUNTER_STREAMS = (
    "target_lateral",
    "wind_T",
    "wind_R",
    "sensor_x",
    "sensor_y",
    "shadow_TR",
    "shadow_RB",
    "link_TR",
    "link_RB",
    "action",
)
def _fraction(value: Fraction | int | str | float) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("rate-map input must be finite")
        return Fraction(str(value))
    return Fraction(value)


def lookup_controller(q_short: Fraction | int, q_long: Fraction | int) -> ControllerSpec:
    q_s, q_l = _fraction(q_short), _fraction(q_long)
    if q_s not in Q or q_l not in Q:
        raise ValueError("lookup rates must belong to Q")
    return ControllerSpec.lookup(int(8 * q_s), int(8 * q_l))


def coefficient_tuple(controller: ControllerSpec) -> tuple[Fraction, ...]:
    if controller.explicit is not None:
        raise ValueError("explicit conformance tapes are not finite-registry controllers")
    return tuple(
        Fraction(getattr(controller, name), 8)
        for name in (
            "alpha_short",
            "alpha_long",
            "beta_short",
            "beta_long",
            "gamma_short",
            "gamma_long",
        )
    )


def is_lookup(controller: ControllerSpec) -> bool:
    return controller.explicit is None and coefficient_tuple(controller)[2:] == (Fraction(0),) * 4


def is_timing_member(controller: ControllerSpec) -> bool:
    return controller.explicit is None and not is_lookup(controller)


def controller_rate_fraction(
    controller: ControllerSpec,
    stratum: str,
    remaining_fraction: Fraction | int | str | float,
    age_fraction: Fraction | int | str | float,
) -> Fraction:
    if controller.explicit is not None:
        raise ValueError("explicit conformance tapes do not define a generic finite rate map")
    if stratum not in STRATA:
        raise ValueError(f"unknown stratum: {stratum!r}")
    remaining = _fraction(remaining_fraction)
    age = _fraction(age_fraction)
    if not Fraction(0) <= remaining <= Fraction(1):
        raise ValueError("remaining fraction must lie in [0,1]")
    if not Fraction(0) <= age <= Fraction(1):
        raise ValueError("age fraction must lie in [0,1]")
    coefficients = coefficient_tuple(controller)
    if stratum == "S":
        alpha, beta, gamma = coefficients[0], coefficients[2], coefficients[4]
    else:
        alpha, beta, gamma = coefficients[1], coefficients[3], coefficients[5]
    value = alpha + beta * (remaining - Fraction(1, 2)) + gamma * (
        age - Fraction(1, 2)
    )
    return min(Fraction(7, 8), max(Fraction(0), value))


def controller_rate(
    controller: ControllerSpec,
    stratum: str,
    remaining_fraction: Fraction | int | str | float,
    age_fraction: Fraction | int | str | float,
) -> float:
    return float(controller_rate_fraction(controller, stratum, remaining_fraction, age_fraction))


FLEX_SLOPE_PATTERNS = (
    (FLEX_SLOPE, FLEX_SLOPE, Fraction(0), Fraction(0)),
    (-FLEX_SLOPE, -FLEX_SLOPE, Fraction(0), Fraction(0)),
    (FLEX_SLOPE, -FLEX_SLOPE, Fraction(0), Fraction(0)),
    (-FLEX_SLOPE, FLEX_SLOPE, Fraction(0), Fraction(0)),
    (Fraction(0), Fraction(0), FLEX_SLOPE, FLEX_SLOPE),
    (Fraction(0), Fraction(0), -FLEX_SLOPE, -FLEX_SLOPE),
    (Fraction(0), Fraction(0), FLEX_SLOPE, -FLEX_SLOPE),
    (Fraction(0), Fraction(0), -FLEX_SLOPE, FLEX_SLOPE),
)


LOOKUP_REGISTRY = tuple(lookup_controller(q_s, q_l) for q_s in Q for q_l in Q)
TIMING_REGISTRY = tuple(
    ControllerSpec(
        int(8 * alpha_s), int(8 * alpha_l), int(8 * beta_s), int(8 * beta_l),
        int(8 * gamma_s), int(8 * gamma_l),
    )
    for alpha_s in FLEX_INTERCEPTS
    for alpha_l in FLEX_INTERCEPTS
    for beta_s, beta_l, gamma_s, gamma_l in FLEX_SLOPE_PATTERNS
)
CONTROLLER_REGISTRY = LOOKUP_REGISTRY + TIMING_REGISTRY
CONTROLLER_ORDINAL = {controller: ordinal for ordinal, controller in enumerate(CONTROLLER_REGISTRY)}

if len(LOOKUP_REGISTRY) != 64 or len(TIMING_REGISTRY) != 128:
    raise AssertionError("Headland-90 registry cardinality differs from the frozen card")
if len(CONTROLLER_REGISTRY) != 192 or len(set(CONTROLLER_REGISTRY)) != 192:
    raise AssertionError("Headland-90 registry is not an exact 192-member set")


@dataclass(frozen=True)
class _MeanRow:
    coordinate: bytes
    event_lambda: float


class CanonicalNeumaierMean:
    """Factory-only proof of one coordinate-ordered binary64 Neumaier mean."""

    __slots__ = ("_value", "_row_count", "_order_digest", "_content_digest", "_sealed")

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("use canonical_neumaier_mean(rows)")

    @classmethod
    def _create(
        cls, *, value: float, row_count: int, order_digest: str, content_digest: str
    ) -> "CanonicalNeumaierMean":
        instance = object.__new__(cls)
        object.__setattr__(instance, "_value", value)
        object.__setattr__(instance, "_row_count", row_count)
        object.__setattr__(instance, "_order_digest", order_digest)
        object.__setattr__(instance, "_content_digest", content_digest)
        object.__setattr__(instance, "_sealed", True)
        return instance

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("canonical Neumaier means are immutable")

    @property
    def value(self) -> float:
        return self._value

    @property
    def row_count(self) -> int:
        return self._row_count

    @property
    def order_digest(self) -> str:
        return self._order_digest

    @property
    def content_digest(self) -> str:
        return self._content_digest

    def validate(self) -> None:
        if (
            getattr(self, "_sealed", False) is not True
            or not isinstance(getattr(self, "_value", None), float)
            or not math.isfinite(self._value)
            or self._value < 0.0
            or not isinstance(getattr(self, "_row_count", None), int)
            or self._row_count <= 0
            or not isinstance(getattr(self, "_order_digest", None), str)
            or len(self._order_digest) != 64
            or not isinstance(getattr(self, "_content_digest", None), str)
            or len(self._content_digest) != 64
        ):
            raise ValueError("invalid canonical Neumaier mean proof")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CanonicalNeumaierMean) and (
            self.value,
            self.row_count,
            self.order_digest,
            self.content_digest,
        ) == (other.value, other.row_count, other.order_digest, other.content_digest)

    def __hash__(self) -> int:
        return hash((self.value, self.row_count, self.order_digest, self.content_digest))

    def __repr__(self) -> str:
        return (
            "CanonicalNeumaierMean("
            f"value={self.value!r}, row_count={self.row_count!r}, "
            f"order_digest={self.order_digest!r}, content_digest={self.content_digest!r})"
        )


def canonical_neumaier_mean(
    rows: Iterable[tuple[bytes, float]],
) -> CanonicalNeumaierMean:
    """Sort unique coordinate rows and divide one compensated sum exactly once."""

    normalized: list[_MeanRow] = []
    for coordinate, event_lambda in rows:
        if not isinstance(coordinate, bytes) or not coordinate:
            raise TypeError("mean rows require nonempty encoded coordinate bytes")
        if not isinstance(event_lambda, float):
            raise TypeError("event_lambda must be a binary64 float")
        if not math.isfinite(event_lambda) or event_lambda < 0.0:
            raise ValueError("event_lambda must be finite and nonnegative")
        normalized.append(_MeanRow(coordinate, event_lambda))
    if not normalized:
        raise ValueError("canonical mean requires at least one opportunity row")
    ordered = tuple(sorted(normalized, key=lambda row: row.coordinate))
    if len({row.coordinate for row in ordered}) != len(ordered):
        raise ValueError("encoded opportunity coordinates must be unique")

    order_hasher = hashlib.sha256(b"ONLGR-HEADLAND90-MEAN-LAMBDA-ORDER-v1\0")
    content_hasher = hashlib.sha256(b"ONLGR-HEADLAND90-MEAN-LAMBDA-CONTENT-v1\0")
    total = 0.0
    compensation = 0.0
    for row in ordered:
        framed = len(row.coordinate).to_bytes(8, "big") + row.coordinate
        order_hasher.update(framed)
        content_hasher.update(framed)
        content_hasher.update(struct.pack(">d", row.event_lambda))
        next_total = total + row.event_lambda
        if abs(total) >= abs(row.event_lambda):
            compensation += (total - next_total) + row.event_lambda
        else:
            compensation += (row.event_lambda - next_total) + total
        total = next_total
    value = (total + compensation) / len(ordered)
    return CanonicalNeumaierMean._create(
        value=value,
        row_count=len(ordered),
        order_digest=order_hasher.hexdigest(),
        content_digest=content_hasher.hexdigest(),
    )


class OrderedNeumaierAccumulator:
    """Streaming equivalent for rows already in strict encoded-coordinate order."""

    __slots__ = (
        "_total", "_compensation", "_row_count", "_previous", "_order_hasher",
        "_content_hasher", "_closed",
    )

    def __init__(self) -> None:
        self._total = 0.0
        self._compensation = 0.0
        self._row_count = 0
        self._previous: bytes | None = None
        self._order_hasher = hashlib.sha256(b"ONLGR-HEADLAND90-MEAN-LAMBDA-ORDER-v1\0")
        self._content_hasher = hashlib.sha256(b"ONLGR-HEADLAND90-MEAN-LAMBDA-CONTENT-v1\0")
        self._closed = False

    def add(self, coordinate: bytes, event_lambda: float) -> None:
        if self._closed:
            raise RuntimeError("ordered Neumaier accumulator is already finalized")
        if not isinstance(coordinate, bytes) or not coordinate:
            raise TypeError("mean rows require nonempty encoded coordinate bytes")
        if self._previous is not None and coordinate <= self._previous:
            raise ValueError("encoded opportunity coordinates must be strictly increasing")
        if not isinstance(event_lambda, float):
            raise TypeError("event_lambda must be a binary64 float")
        if not math.isfinite(event_lambda) or event_lambda < 0.0:
            raise ValueError("event_lambda must be finite and nonnegative")
        framed = len(coordinate).to_bytes(8, "big") + coordinate
        self._order_hasher.update(framed)
        self._content_hasher.update(framed)
        self._content_hasher.update(struct.pack(">d", event_lambda))
        next_total = self._total + event_lambda
        if abs(self._total) >= abs(event_lambda):
            self._compensation += (self._total - next_total) + event_lambda
        else:
            self._compensation += (event_lambda - next_total) + self._total
        self._total = next_total
        self._row_count += 1
        self._previous = coordinate

    def finalize(self) -> CanonicalNeumaierMean:
        if self._closed:
            raise RuntimeError("ordered Neumaier accumulator is already finalized")
        if self._row_count == 0:
            raise ValueError("canonical mean requires at least one opportunity row")
        self._closed = True
        return CanonicalNeumaierMean._create(
            value=(self._total + self._compensation) / self._row_count,
            row_count=self._row_count,
            order_digest=self._order_hasher.hexdigest(),
            content_digest=self._content_hasher.hexdigest(),
        )


@dataclass(frozen=True)
class CalibrationSummary:
    """Selector inputs computed elsewhere from one complete calibration panel."""

    mean_value: Fraction
    tail_value: Fraction
    voluntary_updates: int
    mean_lambda: CanonicalNeumaierMean | None = None

    def __post_init__(self) -> None:
        for name in ("mean_value", "tail_value"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
                raise TypeError(f"{name} must be an exact int or Fraction, never float")
            exact = Fraction(value)
            if not Fraction(0) <= exact <= Fraction(1):
                raise ValueError(f"{name} must lie in [0,1]")
            object.__setattr__(self, name, exact)
        if isinstance(self.voluntary_updates, bool) or not isinstance(self.voluntary_updates, int):
            raise TypeError("voluntary update count must be an integer")
        if self.voluntary_updates < 0:
            raise ValueError("voluntary update count must be nonnegative")
        if self.mean_lambda is not None:
            if not isinstance(self.mean_lambda, CanonicalNeumaierMean):
                raise TypeError("mean lambda must be a canonical proof-carrying Neumaier mean")
            self.mean_lambda.validate()


def rate_lambda(q: Fraction | int) -> float:
    """Return the authoritative correctly-rounded binary64 lambda table value."""

    return _event_transform(_fraction(q))[1]


def event_probability(q: Fraction | int, eligible_seconds: Fraction | float = DT) -> float:
    """Return the frozen one-opportunity probability for the exact 0.25 s row."""

    if _fraction(eligible_seconds) != Fraction(1, 4):
        raise ValueError("Headland-90 legal opportunities have exactly Delta_t=0.25 s")
    return _event_transform(_fraction(q))[2]


def _require_summaries(
    summaries: Mapping[ControllerSpec, CalibrationSummary],
    candidates: Sequence[ControllerSpec],
    selector: str,
) -> None:
    missing = tuple(controller for controller in candidates if controller not in summaries)
    if missing:
        raise ValueError(f"{selector} requires every frozen candidate summary; missing {len(missing)}")


def select_global(
    summaries: Mapping[ControllerSpec, CalibrationSummary],
) -> ControllerSpec:
    candidates = tuple(lookup_controller(q, q) for q in Q)
    _require_summaries(summaries, candidates, "GLOBAL-BEST")
    return min(
        candidates,
        key=lambda controller: (
            -summaries[controller].mean_value,
            -summaries[controller].tail_value,
            summaries[controller].voluntary_updates,
            Fraction(controller.alpha_short, 8),
        ),
    )


def select_two_stratum(
    summaries: Mapping[ControllerSpec, CalibrationSummary],
) -> ControllerSpec:
    _require_summaries(summaries, LOOKUP_REGISTRY, "TWO-STRATUM")
    return min(
        LOOKUP_REGISTRY,
        key=lambda controller: (
            -summaries[controller].mean_value,
            -summaries[controller].tail_value,
            summaries[controller].voluntary_updates,
            rate_lambda(Fraction(controller.alpha_short, 8))
            + rate_lambda(Fraction(controller.alpha_long, 8)),
            controller.alpha_short,
            controller.alpha_long,
        ),
    )


def select_flex(
    summaries: Mapping[ControllerSpec, CalibrationSummary],
) -> ControllerSpec:
    _require_summaries(summaries, CONTROLLER_REGISTRY, "FLEX-CONTAIN")
    for controller in CONTROLLER_REGISTRY:
        if summaries[controller].mean_lambda is None:
            raise ValueError("FLEX-CONTAIN requires an opportunity-row mean lambda for every candidate")
    return min(
        CONTROLLER_REGISTRY,
        key=lambda controller: (
            -summaries[controller].mean_value,
            -summaries[controller].tail_value,
            summaries[controller].voluntary_updates,
            summaries[controller].mean_lambda.value,
            coefficient_tuple(controller),
        ),
    )


AUDIT_GRID = tuple(
    (stratum, remaining, age)
    for stratum in STRATA
    for remaining in (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1))
    for age in (Fraction(0), Fraction(1, 8), Fraction(1, 4), Fraction(1, 2), Fraction(1))
)


def algebraically_distinct(flex: ControllerSpec, two: ControllerSpec) -> bool:
    if not is_lookup(two):
        raise ValueError("TWO controller must be a lookup member")
    return any(
        abs(controller_rate_fraction(flex, *row) - controller_rate_fraction(two, *row))
        >= Fraction(1, 32)
        for row in AUDIT_GRID
    )


@dataclass(frozen=True)
class OpportunityRecord:
    stratum: str
    remaining_fraction: Fraction
    age_fraction: Fraction
    delta_seconds: Fraction = Fraction(1, 4)


@dataclass(frozen=True)
class RealizedDistinctness:
    row_fraction: Fraction
    time_weighted_absolute_difference: Fraction
    distinct: bool


def realized_support_distinctness(
    flex: ControllerSpec,
    two: ControllerSpec,
    flex_records: Iterable[OpportunityRecord],
    two_records: Iterable[OpportunityRecord],
) -> RealizedDistinctness:
    records = tuple(flex_records) + tuple(two_records)  # disjoint tags; multiplicities retained
    if not records:
        return RealizedDistinctness(Fraction(0), Fraction(0), False)
    differences: list[Fraction] = []
    weights: list[Fraction] = []
    for record in records:
        if record.delta_seconds <= 0:
            raise ValueError("opportunity-row duration must be positive")
        difference = abs(
            controller_rate_fraction(
                flex, record.stratum, record.remaining_fraction, record.age_fraction
            )
            - controller_rate_fraction(
                two, record.stratum, record.remaining_fraction, record.age_fraction
            )
        )
        differences.append(difference)
        weights.append(record.delta_seconds)
    row_fraction = Fraction(sum(value >= Fraction(1, 32) for value in differences), len(records))
    weighted = sum(weight * difference for weight, difference in zip(weights, differences)) / sum(weights)
    return RealizedDistinctness(
        row_fraction,
        weighted,
        row_fraction >= Fraction(1, 10) and weighted >= Fraction(1, 64),
    )


@dataclass(frozen=True)
class AliasLedgerEntry:
    logical_tag: str
    registry_ordinal: int
    physical_map_id: str
    exact_aliases: tuple[str, ...]


def identity_preserving_alias_ledger(
    *, global_best: ControllerSpec, two_stratum: ControllerSpec, flex: ControllerSpec
) -> tuple[AliasLedgerEntry, ...]:
    if global_best not in CONTROLLER_ORDINAL or not is_lookup(global_best):
        raise ValueError("GLOBAL-BEST must be an exact registry lookup member")
    if global_best.alpha_short != global_best.alpha_long:
        raise ValueError("GLOBAL-BEST must be a diagonal constant map")
    if two_stratum not in CONTROLLER_ORDINAL or not is_lookup(two_stratum):
        raise ValueError("TWO-STRATUM must be an exact registry lookup member")
    if flex not in CONTROLLER_ORDINAL:
        raise ValueError("FLEX-CONTAIN must be an exact registry member")
    selected = (
        global_best,
        two_stratum,
        flex,
        ControllerSpec.lookup(two_stratum.alpha_long, two_stratum.alpha_long),
        ControllerSpec.lookup(two_stratum.alpha_short, two_stratum.alpha_short),
    )
    aliases = {
        controller: tuple(
            tag for tag, candidate in zip(LOGICAL_HELD_OUT_TAGS, selected) if candidate == controller
        )
        for controller in selected
    }
    return tuple(
        AliasLedgerEntry(
            logical_tag=tag,
            registry_ordinal=CONTROLLER_ORDINAL[controller],
            physical_map_id=f"theta-{CONTROLLER_ORDINAL[controller]:03d}",
            exact_aliases=aliases[controller],
        )
        for tag, controller in zip(LOGICAL_HELD_OUT_TAGS, selected)
    )


def coordinate_schema_facts() -> dict[str, object]:
    """Return schema identity only; this does not encode or materialize a coordinate."""

    return {
        "namespace": PRODUCTION_NAMESPACE,
        "fields": list(COORDINATE_FIELDS),
        "field_encoding": "decimal-or-UTF8 prefixed by decimal byte length and colon",
        "field_joiner": "|",
        "digest": "SHA-256",
        "uniform_rule": "(uint32_big_endian(digest[0:4])+0.5)/2^32",
        "normal_rule": "fixed Box-Muller; lower-address uniform is radius input",
        "streams": list(COUNTER_STREAMS),
        "controller_identity_in_key": False,
        "mutable_cursor": False,
        "splits": {"CAL": 48, "C1": [0, 23], "C2": [24, 47], "HOLD": 128},
        "blocks_per_replicate": 20,
    }


def validate_coordinate_schema(schema: Mapping[str, object]) -> tuple[str, ...]:
    expected = coordinate_schema_facts()
    issues: list[str] = []
    if dict(schema) != expected:
        issues.append("coordinate schema differs from the frozen card")
    forbidden_material = {
        "coordinates",
        "coordinate_rows",
        "counter_words",
        "uniform_values",
        "normal_values",
        "draws",
        "cells",
        "trajectories",
    }
    if forbidden_material.intersection(schema):
        issues.append("coordinate schema contains materialized coordinate or random-word data")
    return tuple(issues)


def assert_registry_conformance() -> None:
    expected_lookup = tuple(lookup_controller(q_s, q_l) for q_s in Q for q_l in Q)
    if CONTROLLER_REGISTRY[:64] != expected_lookup:
        raise AssertionError("lookup registry order differs from exact tuple order")
    expected_timing = tuple(
        ControllerSpec(
            int(8 * alpha_s), int(8 * alpha_l), *(int(8 * value) for value in pattern)
        )
        for alpha_s in FLEX_INTERCEPTS
        for alpha_l in FLEX_INTERCEPTS
        for pattern in FLEX_SLOPE_PATTERNS
    )
    if TIMING_REGISTRY != expected_timing:
        raise AssertionError("timing registry order differs from intercept/pattern order")
    if validate_coordinate_schema(coordinate_schema_facts()):
        raise AssertionError("coordinate schema identity is not self-conforming")

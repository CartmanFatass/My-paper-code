"""Address-complete planning and mechanical execution seams for VNFC R02 A0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .fixtures import ARMS, FIXTURES


PRESENTATIONS = ("canonical", "reverse", "cyclic", "seed_fixed_random")
WITNESS_PRESENTATIONS = ("canonical", "reverse")
PRIMITIVES = ("DUPLICATE_TIE", "NEXTAFTER_STRICT", "FIXED_PREFIX_NULL")
STATE_KINDS = ("t0", "later_fixed_or_acquiring", "diagnostic_null_tie")
PREDICATE_NAMES = (
    "canonical_tensor_bytes_and_inverse_map_equal",
    "public_rows_legality_fixed_opaque_support_copermuted",
    "aligned_forward_probability_and_cdf_equal",
    "fixed_null_prefix_and_key_removal_equal",
    "within_arm_gradient_and_optimizer_equal",
    "mapr_direct_zero_residual_containment",
    "undeclared_numeric_channels_absent",
    "source_law_dependency_seed_fixture_address_identity",
)


class PanelError(ValueError):
    pass


@dataclass(frozen=True)
class Descriptor:
    roster_size: int
    failed_zone: int
    state_kind: str


@dataclass(frozen=True)
class TopLevelRow:
    address: str
    kind: str
    presentation: str
    fixture: str | None
    arm: str

    @property
    def token_addresses(self) -> tuple[str, ...]:
        return tuple(f"{self.address}/TOKEN/{token}" for token in range(4))


@dataclass(frozen=True)
class Evaluation:
    comparison_key: str
    top_address: str
    presentation: str
    arm: str
    clone_ordinal: int

    @property
    def replay_address(self) -> str:
        return f"{self.top_address}/REPLAY"

    @property
    def gradient_address(self) -> str:
        return f"{self.top_address}/GRADIENT"

    @property
    def optimizer_address(self) -> str:
        return f"{self.top_address}/OPTIMIZER"


@dataclass(frozen=True)
class PrimitiveTokenPlan:
    primitive: str
    token: int
    support: tuple[int | None, ...]
    fixed: bool

    @property
    def candidate_count(self) -> int:
        return len(self.support)

    @property
    def cdf_count(self) -> int:
        return 0 if self.fixed else 5 * len(self.support) + 3


def descriptors() -> tuple[Descriptor, ...]:
    rows = tuple(Descriptor(n, zone, state) for n in (3, 5, 7) for zone in (1, 2) for state in STATE_KINDS)
    if len(rows) != 18:
        raise AssertionError("descriptor inventory differs")
    return rows


def main_rows() -> tuple[TopLevelRow, ...]:
    return tuple(
        TopLevelRow(
            f"MAIN/N{row.roster_size}/Z{row.failed_zone}/{row.state_kind}/{presentation}/{fixture}/{arm}",
            "MAIN", presentation, fixture, arm,
        )
        for row in descriptors()
        for presentation in PRESENTATIONS
        for fixture in FIXTURES
        for arm in ARMS
    )


def witness_rows() -> tuple[TopLevelRow, ...]:
    return tuple(
        TopLevelRow(f"WITNESS/N5_REVERSE/{presentation}/{arm}", "WITNESS", presentation, None, arm)
        for presentation in WITNESS_PRESENTATIONS for arm in ARMS
    )


def primitive_rows() -> tuple[TopLevelRow, ...]:
    return tuple(
        TopLevelRow(f"PRIMITIVE/{primitive}/{presentation}/{arm}", "PRIMITIVE", presentation, None, arm)
        for primitive in PRIMITIVES for presentation in WITNESS_PRESENTATIONS for arm in ARMS
    )


def all_top_rows() -> tuple[TopLevelRow, ...]:
    rows = main_rows() + witness_rows() + primitive_rows()
    if len(rows) != 304 or len({row.address for row in rows}) != 304:
        raise AssertionError("top-level A0 inventory differs")
    return rows


def comparison_key(row: TopLevelRow) -> str:
    parts = row.address.split("/")
    if row.kind == "MAIN":
        return "/".join((parts[0], parts[1], parts[2], parts[3], parts[5], parts[6]))
    if row.kind == "WITNESS":
        return f"WITNESS/N5_REVERSE/{row.arm}"
    raise PanelError("primitive rows have no optimizer comparison key")


def evaluations() -> tuple[Evaluation, ...]:
    rows: list[Evaluation] = []
    grouped: dict[str, list[TopLevelRow]] = {}
    for row in main_rows() + witness_rows():
        grouped.setdefault(comparison_key(row), []).append(row)
    if len(grouped) != 74:
        raise AssertionError("logical group-arm inventory differs")
    for key in sorted(grouped):
        group = sorted(grouped[key], key=lambda item: (PRESENTATIONS.index(item.presentation), item.address))
        for clone_ordinal, row in enumerate(group):
            rows.append(Evaluation(key, row.address, row.presentation, row.arm, clone_ordinal))
    if len(rows) != 292 or len({row.top_address for row in rows}) != 292:
        raise AssertionError("presentation optimizer evaluation inventory differs")
    return tuple(rows)


def primitive_token_plans(primitive: str) -> tuple[PrimitiveTokenPlan, ...]:
    if primitive in ("DUPLICATE_TIE", "NEXTAFTER_STRICT"):
        return (
            PrimitiveTokenPlan(primitive, 0, (1, 2, None), False),
            PrimitiveTokenPlan(primitive, 1, (None,), False),
            PrimitiveTokenPlan(primitive, 2, (None,), False),
            PrimitiveTokenPlan(primitive, 3, (None,), False),
        )
    if primitive == "FIXED_PREFIX_NULL":
        return (
            PrimitiveTokenPlan(primitive, 0, (1,), True),
            PrimitiveTokenPlan(primitive, 1, (2, 3, None), False),
            PrimitiveTokenPlan(primitive, 2, (3, None), False),
            PrimitiveTokenPlan(primitive, 3, (3, None), False),
        )
    raise PanelError("unknown primitive")


def primitive_child_counts() -> dict[str, int]:
    candidate_count = 0
    cdf_count = 0
    token_count = 0
    for primitive in PRIMITIVES:
        plans = primitive_token_plans(primitive)
        candidate_count += 4 * sum(row.candidate_count for row in plans)
        cdf_count += 4 * sum(row.cdf_count for row in plans)
        token_count += 4 * len(plans)
    result = {"token_records": token_count, "candidate_children": candidate_count, "cdf_children": cdf_count}
    if result != {"token_records": 48, "candidate_children": 80, "cdf_children": 512}:
        raise AssertionError("primitive child inventory differs")
    return result


def candidate_label(candidate: int | None) -> str:
    return "NULL" if candidate is None else str(candidate)


def primitive_candidate_addresses() -> frozenset[str]:
    addresses = set()
    for row in primitive_rows():
        primitive = row.address.split("/")[1]
        for token in primitive_token_plans(primitive):
            token_address = f"{row.address}/TOKEN/{token.token}"
            addresses.update(f"{token_address}/CANDIDATE/{candidate_label(candidate)}" for candidate in token.support)
    if len(addresses) != 80:
        raise AssertionError("primitive candidate addresses differ")
    return frozenset(addresses)


def expected_cdf_probe_names(candidate_count: int) -> tuple[tuple[int, str], ...]:
    rows: list[tuple[int, str]] = []
    for edge in range(candidate_count + 1):
        rows.extend((edge, name) for name in ("EXACT", "NEXTAFTER_LOWER", "NEXTAFTER_UPPER"))
        if edge > 0:
            rows.append((edge, "PRODUCTION_WORD_BELOW"))
        if edge < candidate_count:
            rows.append((edge, "PRODUCTION_WORD_ABOVE"))
    if len(rows) != 5 * candidate_count + 3:
        raise AssertionError("CDF probe formula differs")
    return tuple(rows)


def primitive_cdf_addresses() -> frozenset[str]:
    addresses = set()
    for row in primitive_rows():
        primitive = row.address.split("/")[1]
        for token in primitive_token_plans(primitive):
            if token.fixed:
                continue
            token_address = f"{row.address}/TOKEN/{token.token}"
            addresses.update(
                f"{token_address}/CDF/{edge}/{probe}"
                for edge, probe in expected_cdf_probe_names(len(token.support))
            )
    if len(addresses) != 512:
        raise AssertionError("primitive CDF addresses differ")
    return frozenset(addresses)


def validate_clone_independence(records: Sequence[Mapping[str, object]]) -> None:
    expected = evaluations()
    if len(records) != len(expected):
        raise PanelError("optimizer evaluation count differs")
    for record, plan in zip(records, expected):
        required = {"comparison_key", "top_address", "prestate_digest", "source_prestate_digest", "clone_ordinal"}
        if set(record) != required:
            raise PanelError("clone identity record schema differs")
        if record["comparison_key"] != plan.comparison_key or record["top_address"] != plan.top_address or record["clone_ordinal"] != plan.clone_ordinal:
            raise PanelError("clone identity address differs")
        if record["prestate_digest"] != record["source_prestate_digest"]:
            raise PanelError("presentation evaluation was not cloned from identical prestate")


def all_predicates_true(predicates: Mapping[str, object]) -> bool:
    return set(predicates) == set(PREDICATE_NAMES) and all(predicates[name] is True for name in PREDICATE_NAMES)

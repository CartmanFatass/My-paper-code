"""Deterministic non-scientific fixtures for the bounded r05 measurement."""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Final, Iterable

from .contracts import (
    ANALYTIC_KINDS,
    ANALYTIC_STATE_COUNT,
    Q_E,
    REGISTERED_N,
    TEST_NAMESPACE,
    TEST_SCHEMA,
)
from .native_backend import AnalyticState, NumericFixture


_SCALE: Final[int] = 10**18


def _bits(value: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def _numeric(
    kind: int,
    input_value: float,
    expected_bits: int,
    lower_num: int,
    upper_num: int,
    *,
    precision_bits: int,
) -> NumericFixture:
    return NumericFixture(
        TEST_SCHEMA,
        kind,
        _bits(input_value),
        expected_bits,
        0,
        1,
        lower_num,
        _SCALE,
        upper_num,
        _SCALE,
        1,
        precision_bits,
    )


def numeric_fixture_bank() -> tuple[NumericFixture, ...]:
    """One closed fixture for every named function and binary256S operation."""

    rows = [
        _numeric(0, -0.8, 0x3FDCC1CE4581DB89, 449328964117221591, 449328964117221592, precision_bits=160),
        _numeric(0, -0.4, 0x3FE57343067270EE, 670320046035639300, 670320046035639301, precision_bits=160),
        _numeric(0, 0.5, 0x3FFA61298E1E069C, 1648721270700128146, 1648721270700128147, precision_bits=160),
        _numeric(1, 2.0, 0x3FE62E42FEFA39EF, 693147180559945309, 693147180559945310, precision_bits=160),
        _numeric(2, 0.5, 0x3FDEAEE8744B05F0, 479425538604203000, 479425538604203001, precision_bits=192),
        _numeric(3, 0.5, 0x3FEC1528065B7D50, 877582561890372716, 877582561890372717, precision_bits=192),
        _numeric(4, 0.5, 0x3FDD9353D7568AF3, 462117157260009758, 462117157260009759, precision_bits=160),
        _numeric(5, 0.5, 0x3FE3EB2FD4D34391, 622459331201854564, 622459331201854565, precision_bits=160),
        _numeric(6, 3.5, 0x3FF3373018970A36, 1200973602347074224, 1200973602347074225, precision_bits=224),
        _numeric(7, 2.0, 0x3FDB0EE6072093CE, 422784335098467139, 422784335098467140, precision_bits=224),
        _numeric(8, 2.0, 0x3FE4A34CC4A60FA6, 644934066848226436, 644934066848226437, precision_bits=256),
        _numeric(9, 2.0, 0x3FF6A09E667F3BCD, 1414213562373095048, 1414213562373095049, precision_bits=160),
        _numeric(10, 0.5, 0x3FE62E42FEFA39EF, 693147180559945309, 693147180559945310, precision_bits=256),
    ]
    exact = (
        (11, 1.0, 0x3FF0000000000000, 2**54 + 1, 2**54),
        (12, 1.0, 0x3FF0000000000000, 2**53 + 1, 2**53),
        (13, 1.0, 0x3FF0000000000001, 2**54 + 3, 2**54),
        (14, 1.5, 0x3FF8000000000000, 3, 2),
        (15, 1.5, 0x3FF0000000000000, 3, 2),
        (16, 0.25, 0x3FE0000000000000, 1, 4),
        (17, 1.0, 0x3FE0000000000000, 1, 2),
        (18, 0.0, 0x3FF0000000000000, 0, 1),
    )
    for kind, input_value, expected, num, den in exact:
        rows.append(
            NumericFixture(
                TEST_SCHEMA,
                kind,
                _bits(input_value),
                expected,
                num,
                den,
                0,
                1,
                0,
                1,
                0,
                256,
            )
        )
    return tuple(rows)


def numeric_batch(width: int) -> tuple[NumericFixture, ...]:
    bank = numeric_fixture_bank()
    return tuple(bank[index % len(bank)] for index in range(width))


def analytic_states() -> tuple[AnalyticState, ...]:
    """Return exactly 4,096 states, balanced over N and eight proof strata."""

    rows: list[AnalyticState] = []
    for index in range(ANALYTIC_STATE_COUNT):
        n_agents = REGISTERED_N[index % len(REGISTERED_N)]
        kind = (index // len(REGISTERED_N)) % len(ANALYTIC_KINDS)
        variant = index // (len(REGISTERED_N) * len(ANALYTIC_KINDS))
        threshold = Q_E // 16 + (variant % 1024)
        rows.append(
            AnalyticState(
                TEST_SCHEMA,
                n_agents,
                kind,
                variant,
                Q_E,
                threshold,
            )
        )
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class SyntheticChainFixture:
    namespace: str
    row: int
    n_agents: int
    layout: str
    boundary_mask: tuple[int, int]
    residual_multiplier: int
    reassociation_direction: int
    analyzer_branch_fixture: int
    event_sufficient_fixture: bool


def synthetic_chain_fixtures() -> tuple[SyntheticChainFixture, ...]:
    """Thirty-two explicit metadata fixtures; none is a scientific episode."""

    rows: list[SyntheticChainFixture] = []
    for row in range(32):
        n_agents = REGISTERED_N[row % 4]
        layout = ("TEST-IID", "TEST-CLUSTER")[(row // 4) % 2]
        rows.append(
            SyntheticChainFixture(
                namespace=TEST_NAMESPACE,
                row=row,
                n_agents=n_agents,
                layout=layout,
                boundary_mask=(1 if row % 3 == 0 else 0, 1 if row % 5 == 0 else 0),
                residual_multiplier=row % 2,
                reassociation_direction=1 if row % 2 == 0 else -1,
                analyzer_branch_fixture=1 + (row % 15),
                event_sufficient_fixture=row % 7 != 0,
            )
        )
    return tuple(rows)


def state_records(rows: Iterable[AnalyticState]) -> tuple[tuple[int, ...], ...]:
    return tuple(
        (
            int(row.schema),
            int(row.n_agents),
            int(row.kind),
            int(row.variant),
            int(row.q_e),
            int(row.relay_threshold),
        )
        for row in rows
    )


def states_from_records(records: Iterable[tuple[int, ...]]) -> tuple[AnalyticState, ...]:
    return tuple(AnalyticState(*record) for record in records)


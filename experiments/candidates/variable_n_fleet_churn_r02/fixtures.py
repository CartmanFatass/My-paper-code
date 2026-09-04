"""Fresh, deterministic fixtures for the VNFC R02 A0 conformance panel.

This module deliberately contains no random initializer and imports no native host.
The real host constructors are reached only through :func:`load_real_adapter`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from operator import mul
from typing import Callable, Mapping, Protocol, Sequence


MAPR_PARAMETER_SHAPES: dict[str, tuple[int, ...]] = {
    "agent.0.weight": (64, 38), "agent.0.bias": (64,),
    "agent.1.weight": (64, 64), "agent.1.bias": (64,),
    "zone.0.weight": (32, 15), "zone.0.bias": (32,),
    "zone.1.weight": (32, 32), "zone.1.bias": (32,),
    "global.0.weight": (16, 4), "global.0.bias": (16,),
    "global.1.weight": (16, 16), "global.1.bias": (16,),
    "token.embedding": (4, 16), "null.embedding": (64,),
    "score.0.weight": (128, 288), "score.0.bias": (128,),
    "score.1.weight": (64, 128), "score.1.bias": (64,),
    "score.out.weight": (1, 64), "score.out.bias": (1,),
    "critic.0.weight": (128, 208), "critic.0.bias": (128,),
    "critic.1.weight": (64, 128), "critic.1.bias": (64,),
    "critic.out.weight": (1, 64), "critic.out.bias": (1,),
}

RESIDUAL_PARAMETER_SHAPES: dict[str, tuple[int, ...]] = {
    "residual.0.weight": (128, 400), "residual.0.bias": (128,),
    "residual.1.weight": (64, 128), "residual.1.bias": (64,),
    "residual.out.weight": (1, 64), "residual.out.bias": (1,),
}

FIXTURES = ("F_ZERO_TIE_V1", "F_DYADIC_DENSE_V1")
ARMS = ("MAPR", "DIRECT")
ENTITY_TYPES = (
    (1, 1, 2), (2, 0, 2), (3, 1, 1), (4, 0, 1),
    (5, 1, 2), (6, 0, 2), (7, 1, 1), (8, 0, 1),
)
FAILED_ENTITY = {
    (3, 1): 1, (3, 2): 3, (5, 1): 1,
    (5, 2): 5, (7, 1): 1, (7, 2): 5,
}


class FixtureError(ValueError):
    """The requested fixture differs from the frozen R02 A0 object."""


@dataclass(frozen=True)
class FlatParameter:
    name: str
    shape: tuple[int, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != _size(self.shape):
            raise FixtureError(f"parameter size differs: {self.name}")


@dataclass(frozen=True)
class ParameterFixture:
    fixture: str
    arm: str
    tensors: tuple[FlatParameter, ...]

    def by_name(self) -> dict[str, FlatParameter]:
        return {tensor.name: tensor for tensor in self.tensors}


@dataclass(frozen=True)
class ActualPathFixturePlan:
    roster_size: int
    failed_zone: int
    state_kind: str
    entity_rows: tuple[tuple[int, int, int], ...]
    failed_entity: int
    demand_1: tuple[int, ...]
    demand_2: tuple[int, ...]
    blocked_1: tuple[int, ...]
    blocked_2: tuple[int, ...]
    post_commands: tuple[tuple[None, None, None, None], ...]
    native_batch_presentations: tuple[str, ...]


@dataclass(frozen=True)
class HostCall:
    ordinal: int
    roster_size: int
    failed_zone: int
    state_family: str
    operation: str
    batch_width: int = 8
    unique_presentation_surfaces: int = 4
    duplicates_per_surface: int = 2
    duplicate_exact_required: bool = True
    primary_only: bool = True
    result_bearing: bool = False


class ActualPathAdapter(Protocol):
    """Effectful adapter used only by the formal A0 route."""

    def construct_cell(
        self,
        plans: Sequence[ActualPathFixturePlan],
        presentations: Mapping[str, tuple[int, ...]],
    ) -> Mapping[str, object]: ...

    def host_call_ledger(self) -> Sequence[Mapping[str, object]]: ...


@dataclass(frozen=True)
class FreshCellIdentity:
    opaque_rank_by_entity: tuple[tuple[int, int], ...]
    presentations: tuple[tuple[str, tuple[int, ...]], ...]


def _size(shape: Sequence[int]) -> int:
    return reduce(mul, shape, 1)


def _zeros(count: int) -> tuple[float, ...]:
    return (0.0,) * count


def _dyadic_values(start: int, count: int, modulus: int, offset: int, power: int) -> tuple[float, ...]:
    scale = 2.0 ** power
    return tuple(((index % modulus) - offset) * scale for index in range(start, start + count))


def mapr_fixture(name: str) -> ParameterFixture:
    if name not in FIXTURES:
        raise FixtureError("unknown MAPR fixture")
    tensors: list[FlatParameter] = []
    ordinal = 0
    for parameter_name in sorted(MAPR_PARAMETER_SHAPES):
        shape = MAPR_PARAMETER_SHAPES[parameter_name]
        count = _size(shape)
        values = _zeros(count) if name == "F_ZERO_TIE_V1" else _dyadic_values(ordinal, count, 257, 128, -12)
        tensors.append(FlatParameter(parameter_name, shape, values))
        ordinal += count
    return ParameterFixture(name, "MAPR", tuple(tensors))


def direct_fixture(name: str) -> ParameterFixture:
    base = mapr_fixture(name)
    tensors = [FlatParameter(f"base.{row.name}", row.shape, row.values) for row in base.tensors]
    ordinal = 0
    for parameter_name in sorted(RESIDUAL_PARAMETER_SHAPES):
        shape = RESIDUAL_PARAMETER_SHAPES[parameter_name]
        count = _size(shape)
        if parameter_name in ("residual.out.weight", "residual.out.bias"):
            values = _zeros(count)
        else:
            values = _dyadic_values(ordinal, count, 251, 125, -13)
            ordinal += count
        tensors.append(FlatParameter(parameter_name, shape, values))
    return ParameterFixture(name, "DIRECT", tuple(sorted(tensors, key=lambda row: row.name)))


def parameter_fixture(name: str, arm: str) -> ParameterFixture:
    if arm == "MAPR":
        return mapr_fixture(name)
    if arm == "DIRECT":
        return direct_fixture(name)
    raise FixtureError("unknown arm")


def actual_path_fixture_plan(roster_size: int, failed_zone: int, state_kind: str) -> ActualPathFixturePlan:
    if (roster_size, failed_zone) not in FAILED_ENTITY:
        raise FixtureError("actual-path cell differs")
    if state_kind not in ("t0", "later_fixed_or_acquiring", "diagnostic_null_tie"):
        raise FixtureError("actual-path state kind differs")
    demand = [2] * 12
    blocked = [1] * 12
    if state_kind == "diagnostic_null_tie":
        demand[6] = 1
        blocked[6] = 0
    return ActualPathFixturePlan(
        roster_size=roster_size,
        failed_zone=failed_zone,
        state_kind=state_kind,
        entity_rows=ENTITY_TYPES[:roster_size + 1],
        failed_entity=FAILED_ENTITY[(roster_size, failed_zone)],
        demand_1=tuple(demand), demand_2=tuple(demand),
        blocked_1=tuple(blocked), blocked_2=tuple(blocked),
        post_commands=((None, None, None, None),) * 6,
        native_batch_presentations=(
            "canonical", "canonical", "reverse", "reverse",
            "cyclic", "cyclic", "seed_fixed_random", "seed_fixed_random",
        ),
    )


def all_actual_path_fixture_plans() -> tuple[ActualPathFixturePlan, ...]:
    return tuple(
        actual_path_fixture_plan(n, zone, state)
        for n in (3, 5, 7)
        for zone in (1, 2)
        for state in ("t0", "later_fixed_or_acquiring", "diagnostic_null_tie")
    )


def fresh_cell_identity(roster_size: int, failed_zone: int) -> FreshCellIdentity:
    """Plan the fresh opaque order and four held-fixed active presentations."""
    from .rng import a0_opaque_ranks, a0_presentations

    plan = actual_path_fixture_plan(roster_size, failed_zone, "t0")
    pre_loss = tuple(row[0] for row in plan.entity_rows)
    ranks = a0_opaque_ranks(pre_loss, roster_size, failed_zone)
    survivors = tuple(entity for entity in pre_loss if entity != plan.failed_entity)
    canonical = tuple(sorted(survivors, key=ranks.__getitem__))
    presentations = a0_presentations(canonical, roster_size, failed_zone)
    return FreshCellIdentity(
        tuple(sorted(ranks.items())),
        tuple((name, presentations[name]) for name in ("canonical", "reverse", "cyclic", "seed_fixed_random")),
    )


def expected_host_call_ledger() -> tuple[HostCall, ...]:
    rows: list[HostCall] = []
    for n in (3, 5, 7):
        for zone in (1, 2):
            for operation in ("reset", "bcrh", "step"):
                rows.append(HostCall(len(rows) + 1, n, zone, "t0_and_later", operation))
            rows.append(HostCall(len(rows) + 1, n, zone, "diagnostic", "reset"))
    if len(rows) != 24:
        raise AssertionError("frozen host-call ledger differs")
    return tuple(rows)


def validate_host_call_ledger(rows: Sequence[Mapping[str, object] | HostCall]) -> None:
    expected = tuple(row.__dict__ for row in expected_host_call_ledger())
    actual = tuple(row.__dict__ if isinstance(row, HostCall) else dict(row) for row in rows)
    if actual != expected:
        raise FixtureError("actual native host-call ledger differs from the frozen 24 calls")


def witness_parameter_fixture(
    tensor_formula: Callable[[tuple[int, ...], int], Sequence[float]],
) -> ParameterFixture:
    """Build the witness using a source-bound tensor formula.

    A pure Python ``math.sin`` substitution is deliberately impossible here.
    Tests may inject a structural fake, but only the real builder below supplies
    the frozen witness bits.
    """
    rows: list[FlatParameter] = []
    for k, (name, shape) in enumerate(MAPR_PARAMETER_SHAPES.items()):
        values = tuple(float(value) for value in tensor_formula(shape, k))
        if len(values) != _size(shape):
            raise FixtureError("source-bound witness tensor formula returned the wrong shape")
        if name == "score.out.weight":
            mutable = [0.0] * len(values)
            mutable[0] = 1.0
            mutable[1] = float.fromhex("0x1.acb103c2a2888p-3")
            values = tuple(mutable)
        rows.append(FlatParameter(name, shape, values))
    return ParameterFixture("WITNESS_N5_REVERSE", "MAPR", tuple(rows))


def source_bound_witness_parameter_fixture() -> ParameterFixture:
    """Materialize the exact committed CPU-float64 torch witness on the real route."""
    import torch

    def tensor_formula(shape: tuple[int, ...], k: int) -> Sequence[float]:
        tensor = 0.09 * torch.sin(
            torch.arange(_size(shape), dtype=torch.float64, device="cpu").reshape(shape)
            * 0.137 + 0.23 + k * 0.071
        )
        return tensor.reshape(-1).tolist()

    return witness_parameter_fixture(tensor_formula)


def load_real_adapter() -> ActualPathAdapter:
    """Load the committed read-only constructors only on the formal real route."""
    from .real_adapter import load_committed_adapter

    return load_committed_adapter()

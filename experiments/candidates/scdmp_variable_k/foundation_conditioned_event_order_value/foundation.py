"""FCEOV-owned competent order-erased foundation contracts."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import math
from typing import Protocol, Sequence, runtime_checkable

from scipy.stats import beta
import torch
from torch import Tensor, nn
import torch.nn.functional as F

from .contracts import (
    COMPETENCE_EPISODES,
    FAILURE_LABELS,
    FoundationGate,
    GRAPHS,
)
from .rng import AddressRNG
from .training import initial_public_draws


class FoundationContractError(ValueError):
    pass


@runtime_checkable
class InitializationUniformSource(Protocol):
    def initialization_uniforms(
        self, *, replicate: int, arm: str, tensor_name: str, count: int
    ) -> Sequence[float]: ...


class _ExactAffine(nn.Module):
    """Affine storage with no implicit library RNG initialization."""

    def __init__(self, in_features: int, out_features: int) -> None:
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.empty((out_features, in_features), dtype=torch.float32))
        self.bias = nn.Parameter(torch.empty((out_features,), dtype=torch.float32))

    def forward(self, value: Tensor) -> Tensor:
        return F.linear(value, self.weight, self.bias)


def _xavier(layer: _ExactAffine, source: InitializationUniformSource, name: str) -> None:
    count = layer.out_features * layer.in_features
    uniforms = tuple(source.initialization_uniforms(
        replicate=0, arm="FOUNDATION", tensor_name=f"{name}.weight", count=count
    ))
    if len(uniforms) != count or any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        or not 0 <= item < 1
        for item in uniforms
    ):
        raise FoundationContractError("initialization source returned invalid uniforms")
    bound = torch.tensor(
        math.sqrt(6.0 / (layer.in_features + layer.out_features)), dtype=torch.float32
    )
    values = torch.tensor(uniforms, dtype=torch.float32).reshape(layer.out_features, layer.in_features)
    with torch.no_grad():
        layer.weight.copy_((2.0 * values - 1.0) * bound)
        layer.bias.zero_()


class _Network(nn.Module):
    def __init__(self, widths: tuple[int, ...], source: InitializationUniformSource, prefix: str) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            _ExactAffine(left, right) for left, right in zip(widths, widths[1:])
        )
        for index, layer in enumerate(self.layers):
            _xavier(layer, source, f"{prefix}.layers.{index}")

    def forward(self, value: Tensor) -> Tensor:
        for layer in self.layers[:-1]:
            value = F.silu(layer(value))
        return self.layers[-1](value)


@dataclass(frozen=True, slots=True)
class FoundationOutput:
    logits: Tensor
    value: Tensor


class FoundationActorCritic(nn.Module):
    """One fresh float32 18-96-96 actor and critic, with no order/q path."""

    def __init__(self, initialization_source: InitializationUniformSource) -> None:
        super().__init__()
        if not isinstance(initialization_source, InitializationUniformSource):
            raise TypeError("an address-stable initialization source is required")
        self.actor = _Network((18, 96, 96, 18), initialization_source, "actor")
        self.critic = _Network((18, 96, 96, 1), initialization_source, "critic")
        if sum(value.numel() for value in self.parameters()) != 24_115:
            raise RuntimeError("foundation parameter count differs from the registered architecture")

    def forward(self, observation: Tensor) -> FoundationOutput:
        if observation.dtype != torch.float32 or observation.ndim < 2 or observation.shape[-1] != 18:
            raise FoundationContractError("foundation observation must be float32 [...,18]")
        if not bool(torch.isfinite(observation).all()):
            raise FoundationContractError("foundation observation must be finite")
        return FoundationOutput(self.actor(observation), self.critic(observation).squeeze(-1))


def materialize_foundation(source: InitializationUniformSource) -> FoundationActorCritic:
    return FoundationActorCritic(source)


def lexicographic_argmax(logits: Tensor) -> Tensor:
    if logits.dtype != torch.float32 or logits.shape[-1] != 18 or not bool(torch.isfinite(logits).all()):
        raise FoundationContractError("foundation logits must be finite float32 [...,18]")
    # torch.argmax returns the first index at a tie.
    return torch.argmax(logits, dim=-1)


@dataclass(frozen=True, slots=True)
class TensorState:
    name: str
    dtype: str
    shape: tuple[int, ...]
    data: bytes


def direct_tensor_state(model: nn.Module) -> tuple[TensorState, ...]:
    """Return direct tensor bytes, shapes and names without derived identity."""

    return tuple(
        TensorState(name, str(value.dtype), tuple(value.shape), value.detach().cpu().contiguous().numpy().tobytes())
        for name, value in model.state_dict().items()
    )


class FrozenFoundation(nn.Module):
    def __init__(self, source: FoundationActorCritic) -> None:
        super().__init__()
        self.actor = copy.deepcopy(source.actor).eval()
        for value in self.actor.parameters():
            value.requires_grad_(False)
        self._state = direct_tensor_state(self.actor)

    def forward(self, observation: Tensor) -> Tensor:
        return self.actor(observation)

    def validate_immutable(self) -> None:
        if direct_tensor_state(self.actor) != self._state:
            raise FoundationContractError("frozen foundation actor changed")


def freeze_foundation(model: FoundationActorCritic) -> FrozenFoundation:
    if not isinstance(model, FoundationActorCritic):
        raise TypeError("only an FCEOV FoundationActorCritic can be frozen")
    return FrozenFoundation(model)


@dataclass(frozen=True, slots=True)
class CompetenceMission:
    mission: int
    graph: str
    graph_mission: int
    initialization_address: tuple[object, ...]
    disturbance_address_prefix: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class CompetenceRecord:
    mission: int
    graph: str
    complete: bool
    safe_dock: bool
    failures: tuple[str, ...] = ()


COMPETENCE_INITIAL_DOMAIN = "foundation-competence-initialization"
COMPETENCE_DISTURBANCE_DOMAIN = "foundation-competence-disturbance"
COMPETENCE_DISTURBANCE_MAGNITUDES = {
    "eta_v": 0.003,
    "eta_y": 0.002,
    "eta_omega": 0.004,
}


def competence_inventory() -> tuple[CompetenceMission, ...]:
    return tuple(
        CompetenceMission(
            index,
            GRAPHS[index % 2],
            index // 2,
            (COMPETENCE_INITIAL_DOMAIN, GRAPHS[index % 2], index // 2),
            (COMPETENCE_DISTURBANCE_DOMAIN, GRAPHS[index % 2], index // 2),
        )
        for index in range(COMPETENCE_EPISODES)
    )


def _validate_competence_mission(mission: CompetenceMission) -> None:
    if not isinstance(mission, CompetenceMission):
        raise FoundationContractError("competence RNG requires a CompetenceMission")
    if (
        isinstance(mission.mission, bool)
        or not isinstance(mission.mission, int)
        or not 0 <= mission.mission < COMPETENCE_EPISODES
        or mission != competence_inventory()[mission.mission]
    ):
        raise FoundationContractError("competence RNG mission differs from the fixed inventory")


def competence_initial_draws(
    source: AddressRNG, mission: CompetenceMission
) -> tuple[float, float, float]:
    _validate_competence_mission(mission)
    if not isinstance(source, AddressRNG):
        raise TypeError("competence initial state requires the addressed FCEOV RNG")
    domain, *address = mission.initialization_address
    return initial_public_draws(
        tuple(
            source.uniform53(str(domain), tuple(address) + (component,))
            for component in ("v", "y", "phi")
        )
    )


def competence_disturbance(
    source: AddressRNG,
    mission: CompetenceMission,
    *,
    tick: int,
    component: str,
) -> float:
    _validate_competence_mission(mission)
    if not isinstance(source, AddressRNG):
        raise TypeError("competence disturbance requires the addressed FCEOV RNG")
    if isinstance(tick, bool) or not isinstance(tick, int) or not 0 <= tick < 364:
        raise FoundationContractError("competence disturbance tick is outside the horizon")
    if component not in COMPETENCE_DISTURBANCE_MAGNITUDES:
        raise FoundationContractError("competence disturbance component differs")
    domain, *prefix = mission.disturbance_address_prefix
    magnitude = COMPETENCE_DISTURBANCE_MAGNITUDES[component]
    address = tuple(prefix) + (tick, component)
    return magnitude if source.bernoulli(0.5, domain=str(domain), address=address) else -magnitude


def validate_competence_rng_contract() -> dict[str, int]:
    inventory = competence_inventory()
    initialization = tuple(row.initialization_address for row in inventory)
    disturbances = tuple(row.disturbance_address_prefix for row in inventory)
    if len(set(initialization)) != COMPETENCE_EPISODES:
        raise RuntimeError("competence initial-state addresses are not unique")
    if len(set(disturbances)) != COMPETENCE_EPISODES:
        raise RuntimeError("competence disturbance addresses are not unique")
    for left, right in zip(inventory[::2], inventory[1::2]):
        if left.graph == right.graph:
            raise RuntimeError("competence graph inventory is not balanced")
        if (
            left.initialization_address == right.initialization_address
            or left.disturbance_address_prefix == right.disturbance_address_prefix
        ):
            raise RuntimeError("competence RNG must not pair tapes across graphs")
    domains = {
        COMPETENCE_INITIAL_DOMAIN,
        COMPETENCE_DISTURBANCE_DOMAIN,
        "foundation-initialization",
        "foundation-training-initial-state",
        "foundation-training-disturbance",
        "foundation-training-categorical",
        "foundation-minibatch",
        "assay-disturbance",
    }
    if len(domains) != 8:
        raise RuntimeError("competence RNG namespaces are not disjoint")
    return {
        "initial_state_addresses": len(initialization),
        "disturbance_prefixes": len(disturbances),
        "domains": len(domains),
    }


COMPETENCE_ALPHA = 0.05 / 7.0


def exact_binomial_bound(successes: int, n: int, *, side: str) -> float:
    """Exact one-sided Clopper-Pearson bound."""

    if isinstance(successes, bool) or isinstance(n, bool) or not 0 <= successes <= n or n < 1:
        raise FoundationContractError("binomial counts are invalid")
    if side == "lower":
        return 0.0 if successes == 0 else float(beta.ppf(COMPETENCE_ALPHA, successes, n - successes + 1))
    if side == "upper":
        return 1.0 if successes == n else float(beta.ppf(1.0 - COMPETENCE_ALPHA, successes + 1, n - successes))
    raise FoundationContractError("binomial side must be lower or upper")


def analyze_competence(records: Sequence[CompetenceRecord]) -> FoundationGate:
    rows = tuple(records)
    expected = competence_inventory()
    if len(rows) != COMPETENCE_EPISODES:
        return FoundationGate(False, False, (), math.nan, ())
    for row in rows:
        if not isinstance(row, CompetenceRecord):
            raise FoundationContractError("competence rows must be CompetenceRecord values")
        if isinstance(row.mission, bool) or not isinstance(row.mission, int):
            raise FoundationContractError("competence mission IDs must be integers")
        if not isinstance(row.graph, str):
            raise FoundationContractError("competence graph labels must be strings")
        if not isinstance(row.complete, bool) or not isinstance(row.safe_dock, bool):
            raise FoundationContractError("competence endpoint flags must be bool")
        if (
            not isinstance(row.failures, tuple)
            or len(set(row.failures)) != len(row.failures)
            or any(not isinstance(label, str) for label in row.failures)
        ):
            raise FoundationContractError("competence failure labels differ")
    if tuple((row.mission, row.graph) for row in rows) != tuple((row.mission, row.graph) for row in expected):
        raise FoundationContractError("competence mission inventory differs")
    if any(not row.complete for row in rows):
        return FoundationGate(False, False, (), math.nan, ())
    if any(row.safe_dock and row.failures for row in rows):
        raise FoundationContractError("safe docking and physical failure cannot coexist")
    if any(label not in FAILURE_LABELS for row in rows for label in row.failures):
        raise FoundationContractError("unregistered physical failure label")
    graph_bounds = tuple(
        (graph, exact_binomial_bound(sum(row.safe_dock for row in rows if row.graph == graph), 60, side="lower"))
        for graph in GRAPHS
    )
    pooled = exact_binomial_bound(sum(row.safe_dock for row in rows), 120, side="lower")
    failure_bounds = tuple(
        (label, exact_binomial_bound(sum(label in row.failures for row in rows), 120, side="upper"))
        for label in FAILURE_LABELS
    )
    passed = (
        all(value > 0.72 for _, value in graph_bounds)
        and pooled > 0.84
        and all(value < 0.10 for _, value in failure_bounds)
    )
    return FoundationGate(True, passed, graph_bounds, pooled, failure_bounds)


__all__ = [
    "CompetenceMission", "CompetenceRecord", "FoundationActorCritic", "FoundationContractError",
    "FoundationOutput", "FrozenFoundation", "InitializationUniformSource", "TensorState",
    "analyze_competence", "competence_disturbance", "competence_initial_draws",
    "competence_inventory", "direct_tensor_state", "exact_binomial_bound",
    "freeze_foundation", "lexicographic_argmax", "materialize_foundation",
    "validate_competence_rng_contract",
]

"""Independent float32 foundation actor/critic for SCDMP MF-RS-MK."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import math
from typing import Mapping, Protocol, Sequence, runtime_checkable

import torch
from torch import Tensor, nn
import torch.nn.functional as F

from .contracts import (
    COMPETENCE_MISSIONS_PER_CELL,
    GRAPHS,
    K_VALUES,
    ORDERED_BRANCHES,
    TRAINING_SEEDS,
)


class FoundationContractError(ValueError):
    pass


@runtime_checkable
class InitializationUniformSource(Protocol):
    def initialization_uniforms(
        self, *, replicate: int, arm: str, tensor_name: str, count: int
    ) -> Sequence[float]: ...


class _ExactAffine(nn.Module):
    """Affine layer whose parameters never pass through library RNG state."""

    def __init__(self, in_features: int, out_features: int) -> None:
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.empty((out_features, in_features), dtype=torch.float32))
        self.bias = nn.Parameter(torch.empty((out_features,), dtype=torch.float32))

    def forward(self, value: Tensor) -> Tensor:
        return F.linear(value, self.weight, self.bias)


def _initialize(layer: _ExactAffine, source: InitializationUniformSource, name: str) -> None:
    count = layer.in_features * layer.out_features
    uniforms = tuple(
        source.initialization_uniforms(
            replicate=0,
            arm="FOUNDATION",
            tensor_name=f"{name}.weight",
            count=count,
        )
    )
    if len(uniforms) != count or any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        or not 0.0 <= item < 1.0
        for item in uniforms
    ):
        raise FoundationContractError("initialization source returned invalid uniforms")
    bound = torch.tensor(
        math.sqrt(6.0 / (layer.in_features + layer.out_features)), dtype=torch.float32
    )
    values = torch.tensor(uniforms, dtype=torch.float32).reshape(
        layer.out_features, layer.in_features
    )
    with torch.no_grad():
        layer.weight.copy_((2.0 * values - 1.0) * bound)
        layer.bias.zero_()


class _Network(nn.Module):
    def __init__(
        self, widths: tuple[int, ...], source: InitializationUniformSource, prefix: str
    ) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            _ExactAffine(left, right) for left, right in zip(widths, widths[1:])
        )
        for index, layer in enumerate(self.layers):
            _initialize(layer, source, f"{prefix}.layers.{index}")

    def forward(self, value: Tensor) -> Tensor:
        for layer in self.layers[:-1]:
            value = F.silu(layer(value))
        return self.layers[-1](value)


@dataclass(frozen=True, slots=True)
class FoundationOutput:
    logits: Tensor
    value: Tensor


class FoundationActorCritic(nn.Module):
    """Graph/order-erased 18-96-96 actor and critic in float32."""

    def __init__(self, initialization_source: InitializationUniformSource) -> None:
        super().__init__()
        if not isinstance(initialization_source, InitializationUniformSource):
            raise TypeError("an address-stable initialization source is required")
        seed = getattr(initialization_source, "seed", None)
        if seed not in TRAINING_SEEDS:
            raise FoundationContractError("foundation initialization must be bound to a prescribed seed")
        self.foundation_seed = int(seed)
        self.actor = _Network((18, 96, 96, 18), initialization_source, "actor")
        self.critic = _Network((18, 96, 96, 1), initialization_source, "critic")
        if sum(value.numel() for value in self.parameters()) != 24_115:
            raise RuntimeError("foundation parameter count differs from the frozen architecture")

    def forward(self, observation: Tensor) -> FoundationOutput:
        if (
            not isinstance(observation, Tensor)
            or observation.dtype != torch.float32
            or observation.ndim < 2
            or observation.shape[-1] != 18
            or not bool(torch.isfinite(observation).all())
        ):
            raise FoundationContractError("observation must be finite float32 [...,18]")
        return FoundationOutput(
            logits=self.actor(observation),
            value=self.critic(observation).squeeze(-1),
        )


def materialize_foundation(source: InitializationUniformSource) -> FoundationActorCritic:
    return FoundationActorCritic(source)


def lexicographic_argmax(logits: Tensor) -> Tensor:
    if (
        logits.dtype != torch.float32
        or logits.shape[-1] != 18
        or not bool(torch.isfinite(logits).all())
    ):
        raise FoundationContractError("logits must be finite float32 [...,18]")
    return torch.argmax(logits, dim=-1)


@dataclass(frozen=True, slots=True)
class TensorState:
    name: str
    dtype: str
    shape: tuple[int, ...]
    data: bytes


def direct_tensor_state(model: nn.Module) -> tuple[TensorState, ...]:
    return tuple(
        TensorState(
            name=name,
            dtype=str(value.dtype),
            shape=tuple(value.shape),
            data=value.detach().cpu().contiguous().numpy().tobytes(),
        )
        for name, value in model.state_dict().items()
    )


class FrozenFoundationActor(nn.Module):
    def __init__(self, source: FoundationActorCritic) -> None:
        super().__init__()
        if not isinstance(source, FoundationActorCritic):
            raise TypeError("only an MF-RS-MK foundation can be frozen")
        self.foundation_seed = source.foundation_seed
        self.actor = copy.deepcopy(source.actor).eval()
        for parameter in self.actor.parameters():
            parameter.requires_grad_(False)
        self._expected = direct_tensor_state(self.actor)

    def forward(self, observation: Tensor) -> Tensor:
        return self.actor(observation)

    def validate_immutable(self) -> None:
        if direct_tensor_state(self.actor) != self._expected:
            raise FoundationContractError("frozen foundation actor changed")


def freeze_foundation_actor(model: FoundationActorCritic) -> FrozenFoundationActor:
    return FrozenFoundationActor(model)


class ImmutableBatchedFoundationPolicy:
    """Seed-bound tuple-observation adapter used by the native batch host."""

    def __init__(self, actor: FrozenFoundationActor) -> None:
        if not isinstance(actor, FrozenFoundationActor):
            raise TypeError("native policy requires a frozen foundation actor")
        self.actor = actor
        self.foundation_seed = actor.foundation_seed

    def __call__(self, observations: tuple[tuple[float, ...], ...]) -> tuple[int, ...]:
        self.actor.validate_immutable()
        value = torch.tensor(observations, dtype=torch.float32)
        if value.ndim != 2 or value.shape[1] != 18 or not bool(torch.isfinite(value).all()):
            raise FoundationContractError("native policy observations must be finite [batch,18]")
        with torch.no_grad():
            actions = lexicographic_argmax(self.actor(value)).tolist()
        self.actor.validate_immutable()
        return tuple(int(action) for action in actions)


FAILURE_FAMILIES = (
    "boundary_contact",
    "cable_overload",
    "swing_envelope_loss",
    "formation_loss",
)


@dataclass(frozen=True, slots=True)
class CompetenceRecord:
    seed: int
    graph: str
    k: int
    mission: int
    terminal: bool
    finite: bool
    evaluator_valid: bool
    safe_dock: bool
    failures: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompetenceCell:
    seed: int
    graph: str
    k: int
    count: int
    safe_docks: int
    terminal_finite_valid: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class FoundationCompetence:
    seed: int
    safe_docks: int
    failure_counts: tuple[tuple[str, int], ...]
    passed: bool


@dataclass(frozen=True, slots=True)
class CompetenceGate:
    complete: bool
    passed: bool
    cells: tuple[CompetenceCell, ...]
    foundations: tuple[FoundationCompetence, ...]


def analyze_competence(records: Sequence[CompetenceRecord]) -> CompetenceGate:
    """Apply the exact B eligibility counts without confidence inference."""

    rows = tuple(records)
    expected_addresses = {
        (seed, graph, k, mission)
        for seed in TRAINING_SEEDS
        for graph in GRAPHS
        for k in K_VALUES
        for mission in range(COMPETENCE_MISSIONS_PER_CELL)
    }
    addresses = []
    for row in rows:
        if not isinstance(row, CompetenceRecord):
            raise FoundationContractError("competence inventory contains an untyped record")
        if (
            row.seed not in TRAINING_SEEDS
            or row.graph not in GRAPHS
            or row.k not in K_VALUES
            or isinstance(row.mission, bool)
            or not isinstance(row.mission, int)
            or not 0 <= row.mission < COMPETENCE_MISSIONS_PER_CELL
            or any(label not in FAILURE_FAMILIES for label in row.failures)
            or len(set(row.failures)) != len(row.failures)
            or row.safe_dock and bool(row.failures)
        ):
            raise FoundationContractError("competence record differs from the frozen address/schema")
        if any(
            not isinstance(value, bool)
            for value in (row.terminal, row.finite, row.evaluator_valid, row.safe_dock)
        ):
            raise FoundationContractError("competence validity fields must be booleans")
        addresses.append((row.seed, row.graph, row.k, row.mission))
    if (
        len(rows) != len(expected_addresses)
        or len(set(addresses)) != len(addresses)
        or set(addresses) != expected_addresses
    ):
        raise FoundationContractError("competence requires exactly 32 missions in every seed/graph/k cell")

    cells = []
    for seed in TRAINING_SEEDS:
        for graph in GRAPHS:
            for k in K_VALUES:
                selected = tuple(
                    row for row in rows if (row.seed, row.graph, row.k) == (seed, graph, k)
                )
                valid = all(row.terminal and row.finite and row.evaluator_valid for row in selected)
                safe = sum(row.safe_dock for row in selected)
                cells.append(CompetenceCell(
                    seed,
                    graph,
                    k,
                    len(selected),
                    safe,
                    valid,
                    valid and safe >= 24,
                ))
    foundations = []
    for seed in TRAINING_SEEDS:
        selected = tuple(row for row in rows if row.seed == seed)
        seed_cells = tuple(cell for cell in cells if cell.seed == seed)
        failures = tuple(
            (label, sum(label in row.failures for row in selected))
            for label in FAILURE_FAMILIES
        )
        safe = sum(row.safe_dock for row in selected)
        passed = (
            all(cell.passed for cell in seed_cells)
            and safe >= 109
            and all(count <= 12 for _, count in failures)
        )
        foundations.append(FoundationCompetence(seed, safe, failures, passed))
    result = CompetenceGate(True, all(row.passed for row in foundations), tuple(cells), tuple(foundations))
    return result


def classify_ordered_branch(branch_truth: Mapping[str, bool]) -> str:
    """Return the first true Pro branch under the prospectively frozen order."""

    if not isinstance(branch_truth, Mapping) or any(
        name not in ORDERED_BRANCHES or not isinstance(value, bool)
        for name, value in branch_truth.items()
    ):
        raise FoundationContractError("branch predicates must use only the eight Pro branch names")
    for name in ORDERED_BRANCHES:
        if branch_truth.get(name, False):
            return name
    raise FoundationContractError("no ordered result branch predicate is true")


__all__ = [
    "CompetenceCell", "CompetenceGate", "CompetenceRecord", "FAILURE_FAMILIES",
    "FoundationActorCritic", "FoundationCompetence", "FoundationContractError", "FoundationOutput",
    "FrozenFoundationActor", "ImmutableBatchedFoundationPolicy", "InitializationUniformSource", "TensorState",
    "analyze_competence", "classify_ordered_branch", "direct_tensor_state",
    "freeze_foundation_actor", "lexicographic_argmax",
    "materialize_foundation",
]

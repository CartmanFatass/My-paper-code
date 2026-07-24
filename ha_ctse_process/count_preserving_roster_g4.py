"""Count-preserving roster G4 source, matched editors, and event-level PPO."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import blake2b
from itertools import permutations
import math
import os
from pathlib import Path
import re
import time
from typing import Any, Iterable, Sequence

import torch
from torch import Tensor, nn


SOURCE_FAMILY = "COUNT_PRESERVING_ROSTER_G4"
SOURCE_CONTROL_SCHEMA = "count_preserving_roster_g4_source_controls_v1"
CHECKPOINT_SCHEMA = "count_preserving_roster_g4_checkpoint_v1"
PASS_SOURCE_CONTROL = "PASS_COUNT_PRESERVING_ROSTER_G4_SOURCE_CONTROL"
FAIL_SOURCE_CONTROL = "FAIL_COUNT_PRESERVING_ROSTER_G4_SOURCE_CONTROL"

ARM_NAMES = ("TEAM_REC", "ROSTER_ATTN", "ROSTER_SUM")
EFFECTS = (0, 1, 2, 3)
EVENT_KINDS = ("JOIN", "RENEW", "TERMINAL_REPLACE")
PROFILES = (
    "train",
    "iid",
    "heldout_cardinality",
    "heldout_gap",
    "heldout_joint",
)
QUERY_WIDTH = 13
ROSTER_TOKEN_WIDTH = 7
HISTORY_WIDTH = 10
CRITIC_WIDTH = 17
HIDDEN_WIDTH = 32

LEARNING_RATE = 3e-4
GAMMA = 0.99
GAE_LAMBDA = 0.95
PPO_CLIP = 0.20
VALUE_CLIP = 0.20
VALUE_COEFFICIENT = 0.50
ENTROPY_COEFFICIENT = 0.01
GRADIENT_CLIP = 0.50
PPO_PASSES = 4

_ATOMIC_REPLACE_ATTEMPTS = 100
_ATOMIC_REPLACE_DELAY_SECONDS = 0.05


def _unique_permutations(values: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(set(permutations(values))))


DEMAND_SUPPORT: dict[int, tuple[tuple[int, int, int, int], ...]] = {
    2: _unique_permutations((1, 1, 0, 0)),
    3: tuple(
        sorted(
            set(_unique_permutations((2, 1, 0, 0)))
            | set(_unique_permutations((1, 1, 1, 0)))
        )
    ),
    4: tuple(
        sorted(
            set(_unique_permutations((3, 1, 0, 0)))
            | set(_unique_permutations((2, 2, 0, 0)))
            | set(_unique_permutations((2, 1, 1, 0)))
            | {(1, 1, 1, 1)}
        )
    ),
}


@dataclass(frozen=True, slots=True)
class ProfileContract:
    active_counts: tuple[int, ...]
    ages: tuple[int, ...]
    gaps: tuple[int, ...]
    duties: tuple[int, ...]


PROFILE_CONTRACTS = {
    "train": ProfileContract((2, 3), (1, 2, 3), (0, 1, 2), (3, 5)),
    "iid": ProfileContract((2, 3), (1, 2, 3), (0, 1, 2), (3, 5)),
    "heldout_cardinality": ProfileContract((4,), (1, 3), (0, 2), (5, 7)),
    "heldout_gap": ProfileContract((2, 3), (8, 16), (8, 16), (8, 12)),
    "heldout_joint": ProfileContract((4,), (8, 16), (8, 16), (8, 12)),
}


@dataclass(frozen=True, slots=True)
class SeedRegistry:
    model: int = 485101
    source: int = 485201
    membership: int = 485301
    nuisance: int = 485401
    action: int = 485501
    evaluation: int = 485601
    audit: int = 485701
    bootstrap: int = 485801
    replicate_offset: int = 1000


def _checked_nonnegative_int(name: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _counter_index(seed: int, domain: str, base_id: int, modulo: int) -> int:
    _checked_nonnegative_int("seed", seed)
    _checked_nonnegative_int("base_id", base_id)
    if type(modulo) is not int or modulo <= 0:
        raise ValueError("modulo must be a positive integer")
    digest = blake2b(
        f"{seed}:{domain}:{base_id}".encode("ascii"), digest_size=8
    ).digest()
    return int.from_bytes(digest, "little") % modulo


@dataclass(frozen=True, slots=True)
class StandingRecordSpec:
    effect: int
    age: int
    service_duration: int
    rejoined: bool
    physical_slot: int

    def __post_init__(self) -> None:
        if type(self.effect) is not int or self.effect not in EFFECTS:
            raise ValueError("standing effect is outside support")
        if type(self.age) is not int or self.age <= 0:
            raise ValueError("record age must be positive")
        if type(self.service_duration) is not int or self.service_duration <= 0:
            raise ValueError("service duration must be positive")
        if type(self.rejoined) is not bool:
            raise TypeError("rejoined must be an exact boolean")
        if type(self.physical_slot) is not int or not 0 <= self.physical_slot < 4:
            raise ValueError("physical slot is outside support")

    @property
    def token(self) -> tuple[float, ...]:
        one_hot = tuple(float(index == self.effect) for index in EFFECTS)
        return one_hot + (
            float(self.age / 16.0),
            float(self.service_duration / 12.0),
            float(self.rejoined),
        )


@dataclass(frozen=True, slots=True)
class UsefulEffectEpisodeSpec:
    profile: str
    base_id: int
    active_count: int
    demand: tuple[int, int, int, int]
    deficit: int
    standing_records: tuple[StandingRecordSpec, ...]
    event_kind: str
    previous_effect: int | None
    gap: int
    nuisance: tuple[int, ...]
    duty: int

    def __post_init__(self) -> None:
        if self.profile not in PROFILES:
            raise ValueError("unknown source profile")
        _checked_nonnegative_int("base_id", self.base_id)
        if self.active_count not in PROFILE_CONTRACTS[self.profile].active_counts:
            raise ValueError("active count is outside profile support")
        if self.demand not in DEMAND_SUPPORT[self.active_count]:
            raise ValueError("demand is outside the complete registered support")
        if type(self.deficit) is not int or not 0 <= self.deficit < len(EFFECTS):
            raise ValueError("deficit effect is outside support")
        if self.demand[self.deficit] <= 0:
            raise ValueError("deficit must be a positive-demand effect")
        if len(self.standing_records) != self.active_count - 1:
            raise ValueError("standing-record count does not match active count")
        if len({record.physical_slot for record in self.standing_records}) != len(
            self.standing_records
        ):
            raise ValueError("standing physical slots collide")
        if self.event_kind not in EVENT_KINDS:
            raise ValueError("editor event kind is outside support")
        if self.event_kind == "RENEW":
            if self.previous_effect not in EFFECTS:
                raise ValueError("RENEW requires a previous effect")
        elif self.previous_effect is not None:
            raise ValueError("fresh editor events cannot expose a previous effect")
        contract = PROFILE_CONTRACTS[self.profile]
        if self.gap not in contract.gaps or self.duty not in contract.duties:
            raise ValueError("gap or duty is outside profile support")
        if len(self.nuisance) != self.gap or any(value not in (-1, 1) for value in self.nuisance):
            raise ValueError("nuisance schedule is malformed")

    @property
    def standing_counts(self) -> tuple[int, int, int, int]:
        counts = [0, 0, 0, 0]
        for record in self.standing_records:
            counts[record.effect] += 1
        return tuple(counts)  # type: ignore[return-value]

    @property
    def query(self) -> tuple[float, ...]:
        demand = tuple(float(value / 4.0) for value in self.demand)
        event = tuple(float(self.event_kind == value) for value in EVENT_KINDS)
        active = (float(self.active_count / 4.0),)
        previous = tuple(
            float(self.previous_effect == value) if self.previous_effect is not None else 0.0
            for value in EFFECTS
        )
        return demand + event + active + previous + (float(self.previous_effect is not None),)

    @property
    def roster_tokens(self) -> tuple[tuple[float, ...], ...]:
        return tuple(record.token for record in self.standing_records)

    @property
    def history_tokens(self) -> tuple[tuple[float, ...], ...]:
        rows: list[tuple[float, ...]] = []

        def event_row(
            event_index: int,
            *,
            effect: int | None,
            elapsed: float,
            nuisance: float = 0.0,
        ) -> tuple[float, ...]:
            event = tuple(float(index == event_index) for index in range(4))
            effect_row = tuple(float(effect == index) if effect is not None else 0.0 for index in EFFECTS)
            return event + effect_row + (float(elapsed), float(nuisance))

        for record in self.standing_records:
            rows.append(
                event_row(
                    0,
                    effect=record.effect,
                    elapsed=min(record.age, 16) / 16.0,
                )
            )
            if record.rejoined:
                rows.append(
                    event_row(
                        1,
                        effect=record.effect,
                        elapsed=min(record.service_duration, 12) / 12.0,
                    )
                )
                rows.append(
                    event_row(
                        2,
                        effect=record.effect,
                        elapsed=min(record.age, 16) / 16.0,
                    )
                )
        for index, sign in enumerate(self.nuisance):
            rows.append(
                event_row(
                    3,
                    effect=None,
                    elapsed=(index + 1) / 16.0,
                    nuisance=float(sign),
                )
            )
        return tuple(rows)

    @property
    def critic(self) -> tuple[float, ...]:
        return self.query + tuple(float(value / 4.0) for value in self.standing_counts)

    def utility(self, selected_effect: int) -> float:
        if type(selected_effect) is not int or selected_effect not in EFFECTS:
            raise ValueError("selected effect is outside support")
        service = list(self.standing_counts)
        service[selected_effect] += 1
        served = sum(min(service[index], self.demand[index]) for index in EFFECTS)
        return float(served / self.active_count)

    @property
    def action_utilities(self) -> tuple[float, float, float, float]:
        return tuple(self.utility(effect) for effect in EFFECTS)  # type: ignore[return-value]

    def intervene_roster(self) -> tuple["UsefulEffectEpisodeSpec", int]:
        """Fill the natural deficit and create one different missing effect."""

        candidates = [
            (index, record)
            for index, record in enumerate(self.standing_records)
            if record.effect != self.deficit and self.demand[record.effect] > 0
        ]
        if not candidates:
            raise ValueError("source lacks a legal roster intervention target")
        index, target = min(candidates, key=lambda item: (item[1].effect, item[0]))
        new_missing = target.effect
        records = list(self.standing_records)
        records[index] = replace(target, effect=self.deficit)
        return replace(self, standing_records=tuple(records)), new_missing


def _profile_components(
    profile: str, base_id: int, *, source_seed: int
) -> tuple[int, tuple[int, int, int, int], int, str, int | None, int, int]:
    if profile not in PROFILE_CONTRACTS:
        raise ValueError("unknown source profile")
    contract = PROFILE_CONTRACTS[profile]
    cells = tuple(
        (active_count, demand, deficit, event_kind)
        for active_count in contract.active_counts
        for demand in DEMAND_SUPPORT[active_count]
        for deficit, value in enumerate(demand)
        if value > 0
        for event_kind in EVENT_KINDS
    )
    rotation = source_seed % len(cells)
    active_count, demand, deficit, event_kind = cells[
        (base_id + rotation) % len(cells)
    ]
    previous_effect = (
        EFFECTS[_counter_index(source_seed, f"{profile}:previous", base_id, len(EFFECTS))]
        if event_kind == "RENEW"
        else None
    )
    gap = contract.gaps[
        _counter_index(source_seed, f"{profile}:gap", base_id, len(contract.gaps))
    ]
    duty = contract.duties[
        _counter_index(source_seed, f"{profile}:duty", base_id, len(contract.duties))
    ]
    return active_count, demand, deficit, event_kind, previous_effect, gap, duty


def _build_episode_spec(
    profile: str,
    *,
    base_id: int,
    active_count: int,
    demand: tuple[int, int, int, int],
    deficit: int,
    event_kind: str,
    previous_effect: int | None,
    gap: int,
    duty: int,
    seed_registry: SeedRegistry,
) -> UsefulEffectEpisodeSpec:
    contract = PROFILE_CONTRACTS[profile]
    standing_effects: list[int] = []
    for effect, count in enumerate(demand):
        standing_effects.extend([effect] * (count - int(effect == deficit)))
    ordered = tuple(
        sorted(
            enumerate(standing_effects),
            key=lambda item: _counter_index(
                seed_registry.membership,
                f"{profile}:standing-order:{item[0]}:{item[1]}",
                base_id,
                2**31 - 1,
            ),
        )
    )
    permuted_effects = tuple(value for _, value in ordered)
    available_slots = list(range(4))
    available_slots.sort(
        key=lambda slot: _counter_index(
            seed_registry.membership,
            f"{profile}:slot:{slot}",
            base_id,
            2**31 - 1,
        )
    )
    records: list[StandingRecordSpec] = []
    for index, effect in enumerate(permuted_effects):
        age = contract.ages[
            _counter_index(
                seed_registry.membership,
                f"{profile}:age:{index}",
                base_id,
                len(contract.ages),
            )
        ]
        duration = contract.duties[
            _counter_index(
                seed_registry.membership,
                f"{profile}:record-duty:{index}",
                base_id,
                len(contract.duties),
            )
        ]
        rejoined = bool(
            _counter_index(
                seed_registry.membership,
                f"{profile}:rejoin:{index}",
                base_id,
                2,
            )
        )
        records.append(
            StandingRecordSpec(
                effect=effect,
                age=age,
                service_duration=duration,
                rejoined=rejoined,
                physical_slot=available_slots[index],
            )
        )
    nuisance = tuple(
        (-1, 1)[
            _counter_index(
                seed_registry.nuisance,
                f"{profile}:nuisance:{index}",
                base_id,
                2,
            )
        ]
        for index in range(gap)
    )
    return UsefulEffectEpisodeSpec(
        profile=profile,
        base_id=base_id,
        active_count=active_count,
        demand=demand,
        deficit=deficit,
        standing_records=tuple(records),
        event_kind=event_kind,
        previous_effect=previous_effect,
        gap=gap,
        nuisance=nuisance,
        duty=duty,
    )


def make_episode_spec(
    profile: str,
    *,
    base_id: int,
    seed_registry: SeedRegistry = SeedRegistry(),
) -> UsefulEffectEpisodeSpec:
    base_id = _checked_nonnegative_int("base_id", base_id)
    active_count, demand, deficit, event_kind, previous_effect, gap, duty = _profile_components(
        profile, base_id, source_seed=seed_registry.source
    )
    return _build_episode_spec(
        profile,
        base_id=base_id,
        active_count=active_count,
        demand=demand,
        deficit=deficit,
        event_kind=event_kind,
        previous_effect=previous_effect,
        gap=gap,
        duty=duty,
        seed_registry=seed_registry,
    )


def make_deficit_mates(
    profile: str,
    *,
    base_id: int,
    seed_registry: SeedRegistry = SeedRegistry(),
) -> tuple[UsefulEffectEpisodeSpec, ...]:
    base_id = _checked_nonnegative_int("base_id", base_id)
    active_count, demand, _deficit, event_kind, previous_effect, gap, duty = _profile_components(
        profile, base_id, source_seed=seed_registry.source
    )
    return tuple(
        _build_episode_spec(
            profile,
            base_id=base_id,
            active_count=active_count,
            demand=demand,
            deficit=deficit,
            event_kind=event_kind,
            previous_effect=previous_effect,
            gap=gap,
            duty=duty,
            seed_registry=seed_registry,
        )
        for deficit, value in enumerate(demand)
        if value > 0
    )


def analytic_no_roster_utility(active_count: int, support_size: int) -> float:
    if active_count not in (2, 3, 4):
        raise ValueError("active count is outside support")
    if type(support_size) is not int or not 2 <= support_size <= active_count:
        raise ValueError("positive-demand support size is outside support")
    return float(1.0 - (support_size - 1) / (support_size * active_count))


def evaluate_source_controls() -> dict[str, Any]:
    rows = 0
    oracle = []
    bayes: dict[str, float] = {}
    duplicate = False
    zero_label = False
    exact_standing = True
    for active_count in (2, 3, 4):
        for demand in DEMAND_SUPPORT[active_count]:
            positives = tuple(index for index, value in enumerate(demand) if value > 0)
            duplicate = duplicate or max(demand) > 1
            zero_label = zero_label or any(value == 0 for value in demand)
            bayes[f"N{active_count}:S{len(positives)}"] = analytic_no_roster_utility(
                active_count, len(positives)
            )
            for deficit in positives:
                rows += 1
                standing = list(demand)
                standing[deficit] -= 1
                utility = sum(
                    min(standing[index] + int(index == deficit), demand[index])
                    for index in EFFECTS
                ) / active_count
                oracle.append(float(utility))
                exact_standing = exact_standing and sum(standing) == active_count - 1
    controls = {
        "complete_demand_cell_count": rows,
        "constructive_oracle_utility": min(oracle),
        "analytic_no_roster_utility": bayes,
        "duplicate_demand_present": duplicate,
        "zero_demand_label_present": zero_label,
        "standing_counts_exact": exact_standing,
    }
    all_checks = (
        rows > 0
        and controls["constructive_oracle_utility"] == 1.0
        and duplicate
        and zero_label
        and exact_standing
        and all(0.0 < value < 1.0 for value in bayes.values())
    )
    return {
        "schema": SOURCE_CONTROL_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "formal": False,
        "result": PASS_SOURCE_CONTROL if all_checks else FAIL_SOURCE_CONTROL,
        "all_source_checks": all_checks,
        **controls,
    }


@dataclass(frozen=True, slots=True)
class PackedSpecs:
    query: Tensor
    critic: Tensor
    roster_tokens: Tensor
    roster_mask: Tensor
    history: Tensor
    history_mask: Tensor
    action_utilities: Tensor
    optimal_effect: Tensor
    specs: tuple[UsefulEffectEpisodeSpec, ...]

    def with_reversed_roster_tokens(self) -> "PackedSpecs":
        tokens = self.roster_tokens.clone()
        for row in range(tokens.shape[0]):
            count = int(self.roster_mask[row].sum())
            tokens[row, :count] = torch.flip(tokens[row, :count], dims=(0,))
        return replace(self, roster_tokens=tokens)


def pack_specs(specs: Sequence[UsefulEffectEpisodeSpec]) -> PackedSpecs:
    normalized = tuple(specs)
    if not normalized:
        raise ValueError("at least one source spec is required")
    if any(type(spec) is not UsefulEffectEpisodeSpec for spec in normalized):
        raise TypeError("every source item must be an exact episode spec")
    batch = len(normalized)
    max_roster = max(len(spec.roster_tokens) for spec in normalized)
    max_history = max(len(spec.history_tokens) for spec in normalized)
    query = torch.tensor([spec.query for spec in normalized], dtype=torch.float32)
    critic = torch.tensor([spec.critic for spec in normalized], dtype=torch.float32)
    roster = torch.zeros(batch, max_roster, ROSTER_TOKEN_WIDTH)
    roster_mask = torch.zeros(batch, max_roster, dtype=torch.bool)
    history = torch.zeros(batch, max_history, HISTORY_WIDTH)
    history_mask = torch.zeros(batch, max_history, dtype=torch.bool)
    for row, spec in enumerate(normalized):
        roster_count = len(spec.roster_tokens)
        history_count = len(spec.history_tokens)
        roster[row, :roster_count] = torch.tensor(spec.roster_tokens)
        roster_mask[row, :roster_count] = True
        history[row, :history_count] = torch.tensor(spec.history_tokens)
        history_mask[row, :history_count] = True
    return PackedSpecs(
        query=query,
        critic=critic,
        roster_tokens=roster,
        roster_mask=roster_mask,
        history=history,
        history_mask=history_mask,
        action_utilities=torch.tensor(
            [spec.action_utilities for spec in normalized], dtype=torch.float32
        ),
        optimal_effect=torch.tensor(
            [spec.deficit for spec in normalized], dtype=torch.long
        ),
        specs=normalized,
    )


def roster_effect_counts(packed: PackedSpecs) -> Tensor:
    """Exact permutation-invariant standing-effect multiplicities."""

    if packed.roster_tokens.shape[-1] != ROSTER_TOKEN_WIDTH:
        raise ValueError("roster tokens have the wrong width")
    mask = packed.roster_mask.unsqueeze(-1)
    return (packed.roster_tokens[..., : len(EFFECTS)] * mask).sum(dim=1)


class UsefulEffectRosterPolicy(nn.Module):
    """Same complete module inventory for every learned arm."""

    def __init__(self) -> None:
        super().__init__()
        self.query_encoder = nn.Linear(QUERY_WIDTH, HIDDEN_WIDTH)
        self.token_encoder = nn.Linear(ROSTER_TOKEN_WIDTH, HIDDEN_WIDTH)
        self.roster_query = nn.Linear(HIDDEN_WIDTH, HIDDEN_WIDTH, bias=False)
        self.team_recurrent = nn.GRUCell(HISTORY_WIDTH, HIDDEN_WIDTH)
        self.base_head = nn.Linear(HIDDEN_WIDTH, len(EFFECTS))
        self.roster_treatment = nn.Linear(HIDDEN_WIDTH, len(EFFECTS), bias=False)
        self.team_treatment = nn.Linear(HIDDEN_WIDTH, len(EFFECTS), bias=False)
        self.critic_encoder = nn.Linear(CRITIC_WIDTH, HIDDEN_WIDTH)
        self.value_head = nn.Sequential(
            nn.Linear(HIDDEN_WIDTH, HIDDEN_WIDTH),
            nn.Tanh(),
            nn.Linear(HIDDEN_WIDTH, 1),
        )

    def _query_features(self, query: Tensor) -> Tensor:
        if query.shape[-1] != QUERY_WIDTH:
            raise ValueError("query has the wrong width")
        return torch.tanh(self.query_encoder(query))

    def _roster_context(self, query_features: Tensor, packed: PackedSpecs) -> Tensor:
        if packed.roster_tokens.shape[-1] != ROSTER_TOKEN_WIDTH:
            raise ValueError("roster tokens have the wrong width")
        tokens = torch.tanh(self.token_encoder(packed.roster_tokens))
        attention_query = self.roster_query(query_features).unsqueeze(1)
        scores = (tokens * attention_query).sum(dim=-1) / math.sqrt(HIDDEN_WIDTH)
        scores = scores.masked_fill(~packed.roster_mask, float("-inf"))
        weights = torch.softmax(scores, dim=-1)
        return (weights.unsqueeze(-1) * tokens).sum(dim=1)

    def _count_preserving_roster_context(self, packed: PackedSpecs) -> Tensor:
        """Retain learned token features while exposing absolute effect counts."""

        if packed.roster_tokens.shape[-1] != ROSTER_TOKEN_WIDTH:
            raise ValueError("roster tokens have the wrong width")
        mask = packed.roster_mask.unsqueeze(-1)
        encoded = torch.tanh(self.token_encoder(packed.roster_tokens))
        accumulation_mask = mask.to(dtype=torch.float64)
        denominator = accumulation_mask.sum(dim=1).clamp_min(1)
        learned_mean = (
            (encoded.to(dtype=torch.float64) * accumulation_mask).sum(dim=1)
            / denominator
        ).to(dtype=encoded.dtype)
        effect_counts = roster_effect_counts(packed)
        context = learned_mean.clone()
        context[:, : len(EFFECTS)] = context[:, : len(EFFECTS)] + effect_counts
        return context

    def _team_context(self, packed: PackedSpecs) -> Tensor:
        if packed.history.shape[-1] != HISTORY_WIDTH:
            raise ValueError("history tokens have the wrong width")
        hidden = torch.zeros(
            packed.history.shape[0],
            HIDDEN_WIDTH,
            dtype=packed.history.dtype,
            device=packed.history.device,
        )
        for index in range(packed.history.shape[1]):
            candidate = self.team_recurrent(packed.history[:, index], hidden)
            hidden = torch.where(
                packed.history_mask[:, index].unsqueeze(-1), candidate, hidden
            )
        return hidden

    def edit_logits(self, arm: str, packed: PackedSpecs) -> Tensor:
        if arm not in ARM_NAMES:
            raise ValueError("unknown useful-effect arm")
        query = self._query_features(packed.query)
        base = self.base_head(query)
        if arm == "TEAM_REC":
            return base + self.team_treatment(self._team_context(packed))
        if arm == "ROSTER_ATTN":
            return base + self.roster_treatment(self._roster_context(query, packed))
        return base + self.roster_treatment(
            self._count_preserving_roster_context(packed)
        )

    def values(self, packed: PackedSpecs) -> Tensor:
        if packed.critic.shape[-1] != CRITIC_WIDTH:
            raise ValueError("critic input has the wrong width")
        encoded = torch.tanh(self.critic_encoder(packed.critic))
        return self.value_head(encoded).squeeze(-1)


@dataclass(slots=True)
class ArmState:
    arm: str
    replicate: int
    source_commit: str
    model: UsefulEffectRosterPolicy
    optimizer: torch.optim.Optimizer
    action_generator: torch.Generator
    optimizer_steps: int = 0
    completed_updates: int = 0
    episodes_completed: int = 0


@dataclass(frozen=True, slots=True)
class ArmBatch:
    arm: str
    packed: PackedSpecs
    actions: Tensor
    old_logp: Tensor
    old_values: Tensor
    rewards: Tensor
    advantages: Tensor
    returns: Tensor


def _generator(seed: int) -> torch.Generator:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return generator


def initialize_matched_arms(
    *,
    replicate: int,
    source_commit: str,
    seed_registry: SeedRegistry = SeedRegistry(),
) -> dict[str, ArmState]:
    replicate = _checked_nonnegative_int("replicate", replicate)
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source_commit must be an exact lowercase Git identity")
    model_seed = seed_registry.model + replicate * seed_registry.replicate_offset
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(model_seed)
        reference = UsefulEffectRosterPolicy()
    states: dict[str, ArmState] = {}
    action_seed = seed_registry.action + replicate * seed_registry.replicate_offset
    for arm in ARM_NAMES:
        model = deepcopy(reference)
        states[arm] = ArmState(
            arm=arm,
            replicate=replicate,
            source_commit=source_commit,
            model=model,
            optimizer=torch.optim.Adam(model.parameters(), lr=LEARNING_RATE),
            action_generator=_generator(action_seed),
        )
    return states


def collect_arm_batch(state: ArmState, packed: PackedSpecs) -> ArmBatch:
    if state.arm not in ARM_NAMES:
        raise ValueError("state arm is outside support")
    with torch.no_grad():
        logits = state.model.edit_logits(state.arm, packed)
        probabilities = torch.softmax(logits, dim=-1)
        actions = torch.multinomial(
            probabilities, 1, generator=state.action_generator
        ).squeeze(-1)
        logp = torch.log_softmax(logits, dim=-1).gather(
            -1, actions.unsqueeze(-1)
        ).squeeze(-1)
        values = state.model.values(packed)
        rewards = packed.action_utilities.gather(
            -1, actions.unsqueeze(-1)
        ).squeeze(-1)
        returns = rewards.clone()
        advantages = returns - values
    state.episodes_completed += len(packed.specs)
    return ArmBatch(
        arm=state.arm,
        packed=packed,
        actions=actions,
        old_logp=logp,
        old_values=values,
        rewards=rewards,
        advantages=advantages,
        returns=returns,
    )


def _replay(model: UsefulEffectRosterPolicy, batch: ArmBatch) -> tuple[Tensor, Tensor, Tensor]:
    logits = model.edit_logits(batch.arm, batch.packed)
    log_probs = torch.log_softmax(logits, dim=-1)
    selected = log_probs.gather(-1, batch.actions.unsqueeze(-1)).squeeze(-1)
    entropy = -(log_probs.exp() * log_probs).sum(dim=-1)
    values = model.values(batch.packed)
    return selected, values, entropy


def replay_errors(model: UsefulEffectRosterPolicy, batch: ArmBatch) -> dict[str, float]:
    with torch.no_grad():
        logp, values, _ = _replay(model, batch)
    return {
        "logp": float((logp - batch.old_logp).abs().max()),
        "value": float((values - batch.old_values).abs().max()),
    }


def _gradient_norm(parameters: Iterable[nn.Parameter]) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is not None:
            total += float(parameter.grad.detach().pow(2).sum())
    return math.sqrt(total)


def _module_parameters(model: UsefulEffectRosterPolicy, prefixes: tuple[str, ...]) -> Iterable[nn.Parameter]:
    for name, parameter in model.named_parameters():
        if name.startswith(prefixes):
            yield parameter


def optimize_arm_batch(
    state: ArmState, batch: ArmBatch, *, passes: int = PPO_PASSES
) -> dict[str, float | int]:
    if batch.arm != state.arm:
        raise ValueError("batch/state arm mismatch")
    if type(passes) is not int or passes <= 0:
        raise ValueError("passes must be positive")
    errors = replay_errors(state.model, batch)
    if max(errors.values()) > 1e-6:
        raise ValueError(f"stored-draw replay mismatch: {errors}")
    forbidden_prefixes = {
        "TEAM_REC": ("token_encoder", "roster_query", "roster_treatment"),
        "ROSTER_ATTN": ("team_recurrent", "team_treatment"),
        "ROSTER_SUM": ("roster_query", "team_recurrent", "team_treatment"),
    }[state.arm]
    maximum_gradient = 0.0
    maximum_forbidden = 0.0
    advantage = (batch.advantages - batch.advantages.mean()) / (
        batch.advantages.std(unbiased=False) + 1e-8
    )
    for _ in range(passes):
        logp, values, entropy = _replay(state.model, batch)
        ratio = torch.exp(logp - batch.old_logp)
        policy_loss = -torch.minimum(
            ratio * advantage,
            ratio.clamp(1.0 - PPO_CLIP, 1.0 + PPO_CLIP) * advantage,
        ).mean()
        clipped_values = batch.old_values + (values - batch.old_values).clamp(
            -VALUE_CLIP, VALUE_CLIP
        )
        value_loss = 0.5 * torch.maximum(
            (values - batch.returns).pow(2),
            (clipped_values - batch.returns).pow(2),
        ).mean()
        loss = (
            policy_loss
            + VALUE_COEFFICIENT * value_loss
            - ENTROPY_COEFFICIENT * entropy.mean()
        )
        if not torch.isfinite(loss):
            raise ValueError("PPO loss is not finite")
        state.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        maximum_gradient = max(
            maximum_gradient, _gradient_norm(state.model.parameters())
        )
        forbidden = _gradient_norm(
            _module_parameters(state.model, forbidden_prefixes)
        )
        maximum_forbidden = max(maximum_forbidden, forbidden)
        if forbidden != 0.0:
            raise ValueError("gradient escaped into an unused treatment path")
        torch.nn.utils.clip_grad_norm_(state.model.parameters(), GRADIENT_CLIP)
        state.optimizer.step()
        state.optimizer_steps += 1
    state.completed_updates += 1
    return {
        "optimizer_steps": passes,
        "maximum_gradient": maximum_gradient,
        "maximum_forbidden_gradient": maximum_forbidden,
        "replay_logp_error": errors["logp"],
        "replay_value_error": errors["value"],
    }


def _atomic_torch_save(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    torch.save(payload, temporary)
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(_ATOMIC_REPLACE_DELAY_SECONDS)


def save_arm_checkpoint(path: Path, state: ArmState) -> None:
    _atomic_torch_save(
        Path(path),
        {
            "schema": CHECKPOINT_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "source_commit": state.source_commit,
            "arm": state.arm,
            "replicate": state.replicate,
            "model": state.model.state_dict(),
            "optimizer": state.optimizer.state_dict(),
            "action_generator": state.action_generator.get_state(),
            "optimizer_steps": state.optimizer_steps,
            "completed_updates": state.completed_updates,
            "episodes_completed": state.episodes_completed,
        },
    )


def load_arm_checkpoint(
    path: Path, state: ArmState, *, source_commit: str
) -> None:
    payload = torch.load(Path(path), map_location="cpu", weights_only=False)
    if type(payload) is not dict or payload.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("checkpoint schema mismatch")
    if payload.get("source_family") != SOURCE_FAMILY:
        raise ValueError("checkpoint source family mismatch")
    if payload.get("source_commit") != source_commit or source_commit != state.source_commit:
        raise ValueError("checkpoint source commit mismatch")
    if payload.get("arm") != state.arm or payload.get("replicate") != state.replicate:
        raise ValueError("checkpoint arm/replicate mismatch")
    state.model.load_state_dict(payload["model"], strict=True)
    state.optimizer.load_state_dict(payload["optimizer"])
    state.action_generator.set_state(payload["action_generator"])
    for name in ("optimizer_steps", "completed_updates", "episodes_completed"):
        value = payload.get(name)
        if type(value) is not int or value < 0:
            raise ValueError(f"checkpoint {name} is invalid")
        setattr(state, name, value)

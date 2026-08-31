"""Small, explicit schemas shared by support, checkpoints, and complete results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping
import json


def jsonable(value: Any) -> Any:
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class PrimitiveLedger:
    tail_service: float
    tail_time: float
    tail_energy: float
    probe_service: float
    probe_time: float
    probe_energy: float
    executed_probe_count: int
    executed_probe_mark_count: int
    executed_probe_time_units: int
    executed_tail_commit_count: int
    executed_tail_period_units: int

    @property
    def total(self) -> float:
        return self.tail_total + self.probe_total

    @property
    def tail_total(self) -> float:
        return self.tail_service + self.tail_time + self.tail_energy

    @property
    def probe_total(self) -> float:
        return self.probe_service + self.probe_time + self.probe_energy


@dataclass(frozen=True)
class PlanEntry:
    index: int
    root_action: str
    period: int


@dataclass(frozen=True)
class FixedBehaviorPlan:
    contract_id: str
    seed_slot: str
    context_id: str
    mode: str
    entries: tuple[PlanEntry, ...]


@dataclass(frozen=True)
class SupportCertificate:
    schema_version: int
    contract_id: str
    mode: str
    episodes_per_context: int
    seed_slots: tuple[str, ...]
    context_ids: tuple[str, ...]
    contract_spec: dict[str, Any]
    materialized_files: dict[str, Any]
    seed_context_counts: dict[str, Any]
    complete: bool
    optimizer_updates: int = 0


@dataclass(frozen=True)
class CheckpointRecord:
    schema_version: int
    contract_id: str
    seed_slot: str
    feature_names: tuple[str, ...]
    completed_batches: int
    optimizer_updates: int
    mode: str


@dataclass(frozen=True)
class SeedEvaluation:
    seed_slot: str
    checkpoint_record: dict[str, Any]
    result_eligible: bool
    action_vector: dict[str, str]
    root_selected_actions: dict[str, str]
    tail_selected_periods: dict[str, dict[str, int]]
    root_scores: dict[str, dict[str, float]]
    tail_scores: dict[str, dict[str, dict[str, float]]]
    cell_evidence: dict[str, dict[str, Any]]
    oracle_action_vector: dict[str, str]
    max_regret: float
    forced_probe_tail_agreement: float
    cell_tail_agreement: dict[str, float]
    root_unique: bool
    min_root_margin: float
    tail_unique: bool
    min_tail_margin: float
    target_flip: bool
    signed_specificity: float


@dataclass(frozen=True)
class BeliefResult:
    schema_version: int
    contract_id: str
    phase: str
    preflight_record: dict[str, Any]
    preflight_mode: str
    checkpoint_records: dict[str, Any]
    seed_evaluations: tuple[SeedEvaluation, ...]
    competence_pass: bool
    competent_seed_count: int
    acquisition_all_flips: bool
    specificity_lower_bound: float
    acquisition_pass: bool
    complete: bool
    representation_conclusion: str = "NONE"
    claim_ceiling: str = "FINITE_HOST_CONTEXTUAL_PAID_ACQUISITION_ONLY"


def dataclass_from_json(cls: type, value: Mapping[str, Any]):
    fields = getattr(cls, "__dataclass_fields__", {})
    return cls(**{key: value[key] for key in fields if key in value})

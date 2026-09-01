"""Frozen observable and configuration for the R01 three-arm scout."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Mapping
import hashlib
import json

OBJECT_ID = "UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01"
SCHEMA_VERSION = 1
RNG_VERSION = "UCOPE_SCOUT_R01_COUNTER_V1"
ARM_IDS = ("MT-XF-FLEX", "FT-XF-FLEX", "FT-XF-BC")
FLEX_ARMS = frozenset(("MT-XF-FLEX", "FT-XF-FLEX"))
K_TRAIN = (1, 3, 5, 7, 9)
K_EVAL = (2, 4, 6, 8)
MARKS = 6
HORIZON = 12
BATCH_SIZE = 256
CONTEXTS = tuple(
    (link, p, cost)
    for link in ("LINKED", "SEVERED")
    for p in (Fraction(13, 20), Fraction(17, 20))
    for cost in (Fraction(9, 100), Fraction(7, 50))
)
B1_SEEDS = tuple(f"ucope-scout-r01-b1-fresh-{index:02d}" for index in range(3))
ASSESS_SEEDS = ("ucope-scout-r01-assess-fresh-00",)
CONSUMED_SEED_PREFIX = "cpa-r01-fresh-slot-"
CHECKPOINT_ROOT_UPDATES = (40, 80, 160, 320)
TARGET_CONTEXT_ID = "LINKED-p17_20-c9_100"
DTYPE = "float32"
OPTIMIZER = {
    "name": "AdamW",
    "lr": 3e-4,
    "betas": (0.9, 0.999),
    "eps": 1e-8,
    "weight_decay": 0.0,
    "gradient_clip": 1.0,
}


class ContractError(ValueError):
    """Raised before stateful work when the frozen observable drifts."""


@dataclass(frozen=True)
class RunBinding:
    """Prospective source/manifest/assessment identity shared by all persisted layers."""

    binding_schema: str
    binding_kind: str
    manifest_digest: str
    source_aggregate: str
    assessment_digest: str

    @classmethod
    def assess(cls, source_aggregate: str) -> "RunBinding":
        payload = f"{OBJECT_ID}|ASSESS|{source_aggregate}".encode("utf-8")
        return cls(
            "UCOPE_SCOUT_R01_RUN_BINDING_V1",
            "ASSESS_SOURCE",
            hashlib.sha256(f"{OBJECT_ID}|ASSESS_MANIFEST".encode("utf-8")).hexdigest(),
            source_aggregate,
            hashlib.sha256(payload).hexdigest(),
        ).validate("ASSESS")

    @classmethod
    def b1(cls, *, manifest_digest: str, source_aggregate: str, assessment_digest: str) -> "RunBinding":
        return cls("UCOPE_SCOUT_R01_RUN_BINDING_V1", "B1_ADMITTED", manifest_digest, source_aggregate, assessment_digest).validate("B1")

    def validate(self, mode: str) -> "RunBinding":
        if self.binding_schema != "UCOPE_SCOUT_R01_RUN_BINDING_V1":
            raise ContractError("run binding schema drift")
        expected_kind = "B1_ADMITTED" if mode == "B1" else "ASSESS_SOURCE"
        if self.binding_kind != expected_kind:
            raise ContractError("run binding kind/mode mismatch")
        for name in ("manifest_digest", "source_aggregate", "assessment_digest"):
            value = getattr(self, name)
            if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ContractError(f"run binding {name} must be lowercase SHA-256")
        return self

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_value(cls, value: "RunBinding | Mapping[str, Any]", mode: str) -> "RunBinding":
        if isinstance(value, cls):
            return value.validate(mode)
        if not isinstance(value, Mapping) or set(value) != set(cls.__dataclass_fields__):
            raise ContractError("run binding field inventory mismatch")
        return cls(**value).validate(mode)


def context_id(context: tuple[str, Fraction, Fraction]) -> str:
    link, p, cost = context
    return f"{link}-p{p.numerator}_{p.denominator}-c{cost.numerator}_{cost.denominator}"


@dataclass(frozen=True)
class ScoutConfig:
    """One named frozen run. B1 is scientific; ASSESS is explicitly A/RECON."""

    run_id: str
    mode: str
    seed_ids: tuple[str, ...]
    episodes_per_context: int
    tail_updates: int
    root_updates: int
    evaluation_root_updates: tuple[int, ...]
    sampled_evaluation_episodes: int
    batch_size: int = BATCH_SIZE
    arms: tuple[str, ...] = ARM_IDS
    object_id: str = OBJECT_ID
    rng_version: str = RNG_VERSION

    @classmethod
    def b1(cls) -> "ScoutConfig":
        return cls(
            run_id="ucope-scout-r01-b1",
            mode="B1",
            seed_ids=B1_SEEDS,
            episodes_per_context=5_120,
            tail_updates=160,
            root_updates=320,
            evaluation_root_updates=CHECKPOINT_ROOT_UPDATES,
            sampled_evaluation_episodes=64,
        ).validate()

    @classmethod
    def assess(cls) -> "ScoutConfig":
        return cls(
            run_id="ucope-scout-r01-assess-r01",
            mode="ASSESS",
            seed_ids=ASSESS_SEEDS,
            episodes_per_context=320,
            tail_updates=8,
            root_updates=16,
            evaluation_root_updates=(8, 16),
            sampled_evaluation_episodes=8,
        ).validate()

    def validate(self) -> "ScoutConfig":
        if self.object_id != OBJECT_ID or self.rng_version != RNG_VERSION:
            raise ContractError("object/RNG identity drift")
        if self.mode not in {"B1", "ASSESS"}:
            raise ContractError("mode must be B1 or ASSESS")
        if not self.run_id or self.arms != ARM_IDS:
            raise ContractError("run identity or arm order drift")
        if not self.seed_ids or len(set(self.seed_ids)) != len(self.seed_ids):
            raise ContractError("seed identifiers must be nonempty and unique")
        if any(seed.startswith(CONSUMED_SEED_PREFIX) for seed in self.seed_ids):
            raise ContractError("consumed BELIEF seed namespace is forbidden")
        exact_ints = (
            self.episodes_per_context,
            self.tail_updates,
            self.root_updates,
            self.sampled_evaluation_episodes,
            self.batch_size,
        )
        if any(type(value) is not int or value <= 0 for value in exact_ints):
            raise ContractError("positive exact integer workload fields required")
        if self.episodes_per_context % 20:
            raise ContractError("episodes/context must preserve complete ten-strata blocks in both folds")
        if self.batch_size != BATCH_SIZE:
            raise ContractError("batch size drift")
        if self.root_updates != 2 * self.tail_updates:
            raise ContractError("root/tail update ratio must be exactly two")
        if (
            not self.evaluation_root_updates
            or tuple(sorted(set(self.evaluation_root_updates))) != self.evaluation_root_updates
            or self.evaluation_root_updates[-1] != self.root_updates
            or any(type(value) is not int or value <= 0 for value in self.evaluation_root_updates)
        ):
            raise ContractError("evaluation roots must be unique, ordered, positive, and include final")
        if self.mode == "B1":
            canonical_b1 = {
                "run_id": "ucope-scout-r01-b1",
                "mode": "B1",
                "seed_ids": B1_SEEDS,
                "episodes_per_context": 5_120,
                "tail_updates": 160,
                "root_updates": 320,
                "evaluation_root_updates": CHECKPOINT_ROOT_UPDATES,
                "sampled_evaluation_episodes": 64,
                "batch_size": BATCH_SIZE,
                "arms": ARM_IDS,
                "object_id": OBJECT_ID,
                "rng_version": RNG_VERSION,
            }
            if self.__dict__ != canonical_b1:
                raise ContractError("B1 configuration drift")
        if self.mode == "ASSESS":
            canonical = {
                "run_id": "ucope-scout-r01-assess-r01",
                "mode": "ASSESS",
                "seed_ids": ASSESS_SEEDS,
                "episodes_per_context": 320,
                "tail_updates": 8,
                "root_updates": 16,
                "evaluation_root_updates": (8, 16),
                "sampled_evaluation_episodes": 8,
                "batch_size": BATCH_SIZE,
                "arms": ARM_IDS,
                "object_id": OBJECT_ID,
                "rng_version": RNG_VERSION,
            }
            if self.__dict__ != canonical:
                raise ContractError("ASSESS configuration drift")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["seed_ids"] = list(self.seed_ids)
        value["evaluation_root_updates"] = list(self.evaluation_root_updates)
        value["arms"] = list(self.arms)
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ScoutConfig":
        if not isinstance(value, Mapping) or set(value) != set(cls.__dataclass_fields__):
            raise ContractError("configuration field inventory mismatch")
        converted = dict(value)
        for name in ("seed_ids", "evaluation_root_updates", "arms"):
            if not isinstance(converted[name], (list, tuple)):
                raise ContractError(f"{name} must be a sequence")
            converted[name] = tuple(converted[name])
        return cls(**converted).validate()


def validate_host_opportunity_map() -> dict[str, Any]:
    """Import-free exact check of the frozen host opportunity structure."""
    from .oracle import build_oracle

    oracle = build_oracle()
    direct = {context_id(c): oracle[context_id(c)]["direct_probe"] for c in CONTEXTS}
    positive = [cell for cell, row in oracle.items() if row["net_acquisition"] > 0]
    if any(value >= 0 for value in direct.values()) or positive != [TARGET_CONTEXT_ID]:
        raise ContractError("host opportunity map is absent")
    if any(not row["unique"] for row in oracle.values()):
        raise ContractError("host oracle contains a tie")
    return {"valid": True, "target_context_id": TARGET_CONTEXT_ID, "contexts": len(CONTEXTS)}


def expected_activity_totals(config: ScoutConfig) -> dict[str, int]:
    """Exact result-blind activity totals implied by a frozen config."""
    config.validate()
    seeds = len(config.seed_ids)
    policies = len(config.arms) * seeds * 2
    checkpoints = policies * len(config.evaluation_root_updates)
    return {
        "environment_episodes": seeds * len(CONTEXTS) * config.episodes_per_context,
        "environment_transitions": seeds * len(CONTEXTS) * config.episodes_per_context * 5,
        "root_rows": seeds * len(CONTEXTS) * config.episodes_per_context,
        "tail_rows": seeds * len(CONTEXTS) * config.episodes_per_context // 2,
        "root_optimizer_updates": policies * config.root_updates,
        "tail_optimizer_updates": policies * config.tail_updates,
        "root_example_exposures": policies * config.root_updates * config.batch_size,
        "tail_example_exposures": policies * config.tail_updates * config.batch_size,
        "exact_policy_evaluations": checkpoints * len(CONTEXTS),
        "sampled_evaluation_episodes": checkpoints * len(CONTEXTS) * config.sampled_evaluation_episodes,
        "checkpoint_writes": checkpoints,
        "policies_completed": policies,
    }


def expected_work(config: ScoutConfig) -> dict[str, int]:
    config.validate()
    return {
        "seed_count": len(config.seed_ids),
        "context_count": len(CONTEXTS),
        "arm_count": len(config.arms),
        "fold_policies_per_arm_seed": 2,
        "episodes_per_context": config.episodes_per_context,
        "batch_size": config.batch_size,
        "tail_updates_per_policy": config.tail_updates,
        "root_updates_per_policy": config.root_updates,
        "evaluation_checkpoint_count": len(config.evaluation_root_updates),
        "sampled_episodes_per_context_checkpoint": config.sampled_evaluation_episodes,
    }


def expected_parameter_counts() -> dict[str, int]:
    residual = (9 * 64 + 64) + (64 * 64 + 64) + (64 * 1 + 1)
    return {"MT-XF-FLEX": residual * 2 + 7 + 5, "FT-XF-FLEX": residual * 2 + 7 + 5, "FT-XF-BC": 12}

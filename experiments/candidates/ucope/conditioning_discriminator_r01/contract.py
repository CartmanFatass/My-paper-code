"""Immutable Pro literals for the R01 invertible-conditioning discriminator."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Mapping

OBJECT_ID = "UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01"
EVIDENCE_CLASS = "B/EXPLORE"
ARM_IDS = ("FT-XF-BC-RAW", "FT-XF-BC-WHITENED")
SEED_IDS = tuple(f"ucope-bc-conditioning-r01-fresh-{index:02d}" for index in range(3))
CONTEXTS = tuple(
    (link, reliability, cost)
    for link in ("LINKED", "SEVERED")
    for reliability in (Fraction(13, 20), Fraction(17, 20))
    for cost in (Fraction(9, 100), Fraction(7, 50))
)
K_TRAIN = (1, 3, 5, 7, 9)
K_EVAL = (2, 4, 6, 8)
FOLD_IDS = (0, 1)
TEN_STRATA = tuple(
    (action, period)
    for action in ("PROBE", "IMMEDIATE")
    for period in K_TRAIN
)
EPISODES_PER_CONTEXT = 5_120
BATCH_SIZE = 256
TAIL_BASIS_DIM = 5
ROOT_BASIS_DIM = 7
TRAINABLE_COEFFICIENTS = TAIL_BASIS_DIM + ROOT_BASIS_DIM
TAIL_UPDATES = 160
ROOT_UPDATES = 320
CHECKPOINT_ROOT_UPDATES = (40, 80, 160, 320)
DTYPE = "float32"
LOSS = "squared_regression"
RNG_VERSION = "UCOPE_BC_CONDITIONING_R01_COUNTER_V1"
SCHEMA_VERSION = 1
MARKS = 6
HORIZON = 12
SAMPLED_EVALUATION_EPISODES = 64
TARGET_CONTEXT_ID = "LINKED-p17_20-c9_100"
SCIENTIFIC_RUN_ID = "ucope-bc-conditioning-r01-result-01"
ASSESS_SEED_IDS = ("ucope-bc-conditioning-r01-assess-technical-00",)


class ContractError(ValueError):
    """Raised before stateful work when a frozen Pro literal drifts."""


@dataclass(frozen=True)
class OptimizerContract:
    """Exact FP32 AdamW and clipping contract shared by both arms."""

    name: str = "AdamW"
    learning_rate: float = 3e-4
    betas: tuple[float, float] = (0.9, 0.999)
    epsilon: float = 1e-8
    weight_decay: float = 0.0
    gradient_norm_clip: float = 1.0

    def validate(self) -> "OptimizerContract":
        if self != OptimizerContract():
            raise ContractError("optimizer contract drift")
        return self


@dataclass(frozen=True)
class ConditioningConfig:
    """One exact, immutable R01 configuration; no runner/artifact fields."""

    object_id: str = OBJECT_ID
    evidence_class: str = EVIDENCE_CLASS
    arms: tuple[str, str] = ARM_IDS
    seed_ids: tuple[str, str, str] = SEED_IDS
    contexts: tuple[tuple[str, Fraction, Fraction], ...] = CONTEXTS
    k_train: tuple[int, ...] = K_TRAIN
    k_eval: tuple[int, ...] = K_EVAL
    fold_ids: tuple[int, int] = FOLD_IDS
    ten_strata: tuple[tuple[str, int], ...] = TEN_STRATA
    episodes_per_context: int = EPISODES_PER_CONTEXT
    batch_size: int = BATCH_SIZE
    tail_basis_dim: int = TAIL_BASIS_DIM
    root_basis_dim: int = ROOT_BASIS_DIM
    trainable_coefficients: int = TRAINABLE_COEFFICIENTS
    dtype: str = DTYPE
    loss: str = LOSS
    optimizer: OptimizerContract = OptimizerContract()
    tail_updates: int = TAIL_UPDATES
    root_updates: int = ROOT_UPDATES
    checkpoint_root_updates: tuple[int, ...] = CHECKPOINT_ROOT_UPDATES

    @classmethod
    def r01(cls) -> "ConditioningConfig":
        return cls().validate()

    def validate(self) -> "ConditioningConfig":
        canonical = ConditioningConfig()
        if self != canonical:
            raise ContractError("R01 conditioning configuration drift")
        self.optimizer.validate()
        if len(self.contexts) != 8 or len(set(self.contexts)) != 8:
            raise ContractError("context inventory drift")
        if self.trainable_coefficients != self.tail_basis_dim + self.root_basis_dim:
            raise ContractError("coefficient inventory drift")
        return self

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contexts"] = [
            [link, [reliability.numerator, reliability.denominator], [cost.numerator, cost.denominator]]
            for link, reliability, cost in self.contexts
        ]
        value["optimizer"]["betas"] = list(self.optimizer.betas)
        for name in ("arms", "seed_ids", "k_train", "k_eval", "fold_ids", "ten_strata", "checkpoint_root_updates"):
            value[name] = [list(item) if isinstance(item, tuple) else item for item in value[name]]
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConditioningConfig":
        if not isinstance(value, Mapping) or set(value) != set(cls.__dataclass_fields__):
            raise ContractError("configuration field inventory mismatch")
        converted = dict(value)
        try:
            converted["contexts"] = tuple(
                (item[0], Fraction(*item[1]), Fraction(*item[2])) for item in converted["contexts"]
            )
            for name in ("arms", "seed_ids", "k_train", "k_eval", "fold_ids", "checkpoint_root_updates"):
                converted[name] = tuple(converted[name])
            converted["ten_strata"] = tuple(tuple(item) for item in converted["ten_strata"])
            optimizer = dict(converted["optimizer"])
            optimizer["betas"] = tuple(optimizer["betas"])
            converted["optimizer"] = OptimizerContract(**optimizer)
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError("invalid configuration encoding") from exc
        return cls(**converted).validate()


@dataclass(frozen=True)
class WorkloadConfig:
    """Internal execution shape; only ``science`` carries result authority."""

    mode: str
    run_id: str
    seed_ids: tuple[str, ...]
    episodes_per_context: int
    tail_updates: int
    root_updates: int
    checkpoint_root_updates: tuple[int, ...]
    sampled_evaluation_episodes: int
    batch_size: int = BATCH_SIZE
    arms: tuple[str, ...] = ARM_IDS

    @classmethod
    def science(cls) -> "WorkloadConfig":
        return cls(
            "SCIENCE", SCIENTIFIC_RUN_ID, SEED_IDS, EPISODES_PER_CONTEXT,
            TAIL_UPDATES, ROOT_UPDATES, CHECKPOINT_ROOT_UPDATES,
            SAMPLED_EVALUATION_EPISODES,
        ).validate()

    @classmethod
    def assess(cls) -> "WorkloadConfig":
        return cls(
            "ASSESS", "ucope-bc-conditioning-r01-assessment-03", ASSESS_SEED_IDS,
            40, 2, 4, (2, 4), 2,
        ).validate()

    @classmethod
    def test(cls) -> "WorkloadConfig":
        return cls(
            "TEST", "ucope-bc-conditioning-r01-test-only", ("ucope-bc-conditioning-r01-test-only-00",),
            40, 2, 4, (2, 4), 2,
        ).validate()

    def validate(self) -> "WorkloadConfig":
        canonical = {"SCIENCE": WorkloadConfig.science, "ASSESS": WorkloadConfig.assess, "TEST": WorkloadConfig.test}
        if self.mode not in canonical:
            raise ContractError("workload mode drift")
        # Avoid factory recursion by comparing literal mode-specific payloads.
        expected = {
            "SCIENCE": (SCIENTIFIC_RUN_ID, SEED_IDS, EPISODES_PER_CONTEXT, TAIL_UPDATES, ROOT_UPDATES, CHECKPOINT_ROOT_UPDATES, SAMPLED_EVALUATION_EPISODES),
            "ASSESS": ("ucope-bc-conditioning-r01-assessment-03", ASSESS_SEED_IDS, 40, 2, 4, (2, 4), 2),
            "TEST": ("ucope-bc-conditioning-r01-test-only", ("ucope-bc-conditioning-r01-test-only-00",), 40, 2, 4, (2, 4), 2),
        }[self.mode]
        observed = (self.run_id, self.seed_ids, self.episodes_per_context, self.tail_updates, self.root_updates, self.checkpoint_root_updates, self.sampled_evaluation_episodes)
        if observed != expected or self.batch_size != BATCH_SIZE or self.arms != ARM_IDS:
            raise ContractError("workload configuration drift")
        if self.episodes_per_context % 20 or self.root_updates != 2 * self.tail_updates:
            raise ContractError("workload schedule drift")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        for name in ("seed_ids", "checkpoint_root_updates", "arms"):
            value[name] = list(value[name])
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkloadConfig":
        if not isinstance(value, Mapping) or set(value) != set(cls.__dataclass_fields__):
            raise ContractError("workload field inventory mismatch")
        converted = dict(value)
        for name in ("seed_ids", "checkpoint_root_updates", "arms"):
            converted[name] = tuple(converted[name])
        return cls(**converted).validate()


def context_id(context: tuple[str, Fraction, Fraction]) -> str:
    link, reliability, cost = context
    return f"{link}-p{reliability.numerator}_{reliability.denominator}-c{cost.numerator}_{cost.denominator}"


def expected_counts(config: WorkloadConfig) -> dict[str, int]:
    config.validate()
    seeds = len(config.seed_ids)
    policies = len(config.arms) * seeds * len(FOLD_IDS)
    checkpoints = policies * len(config.checkpoint_root_updates)
    return {
        "environment_episodes": seeds * len(CONTEXTS) * config.episodes_per_context,
        "environment_transitions": seeds * len(CONTEXTS) * config.episodes_per_context * 5,
        "root_rows": seeds * len(CONTEXTS) * config.episodes_per_context,
        "tail_rows": seeds * len(CONTEXTS) * config.episodes_per_context // 2,
        "policies": policies,
        "checkpoints": checkpoints,
        "tail_optimizer_updates": policies * config.tail_updates,
        "root_optimizer_updates": policies * config.root_updates,
        "tail_example_exposures": policies * config.tail_updates * config.batch_size,
        "root_example_exposures": policies * config.root_updates * config.batch_size,
        "target_materialization_events": policies,
        "target_materialization_rows": policies * config.episodes_per_context * 4,
        "exact_support_evaluations": checkpoints * 2,
        "sampled_evaluation_episodes": 0 if config.mode == "ASSESS" else checkpoints * len(CONTEXTS) * config.sampled_evaluation_episodes,
    }

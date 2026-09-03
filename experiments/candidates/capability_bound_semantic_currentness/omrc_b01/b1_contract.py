"""Immutable public planning contract for CBSC-OMRC-B1.

This module contains no execution, artifact, or scientific-analysis behavior.
It only makes the frozen B1 exposure observable and rejects construction that
would change that exposure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from .addressing import B1_RUN
from .b0 import ARMS
from .telemetry import (
    DURABLE_CAP_BYTES,
    PEAK_RSS_CAP_BYTES,
    SCRATCH_CAP_BYTES,
    ResourceCaps,
)


class B1ContractError(ValueError):
    """A public B1 plan or request differs from the frozen contract."""


B1_RUN_NAME = B1_RUN
B1_SEEDS = (21101, 21121, 21143)
B1_TRAIN_EPISODE_IDS = tuple(range(384))
B1_ROLLOUT_UPDATES = 48
B1_PPO_EPOCHS = 4
B1_MINIBATCHES_PER_EPOCH = 4
B1_MINIBATCH_EPISODE_COUNT = 2
B1_OPTIMIZER_STEPS_PER_ARM_SEED = 768
B1_CHECKPOINT_UPDATES = (0, 12, 24, 48)
B1_EVAL_STOCHASTIC_IDS = tuple(range(32))
B1_EVAL_MOTIF_IDS = tuple(range(32))
B1_WALL_CAP_SECONDS = 7_200.0
B1_RESOURCE_CAPS = ResourceCaps(
    wall_seconds=B1_WALL_CAP_SECONDS,
    process_tree_peak_rss_bytes=PEAK_RSS_CAP_BYTES,
    scratch_high_water_bytes=SCRATCH_CAP_BYTES,
    durable_high_water_bytes=DURABLE_CAP_BYTES,
)
B1_OBJECT_DURABLE_CAP_BYTES = DURABLE_CAP_BYTES
B1_BOUND_ADMISSION_SCHEMA = "cbsc_omrc_b01_b1_bound_admission_v1"
B1_LEDGER_SCHEMA = "cbsc_omrc_b01_b1_attempt_incident_ledger_v1"
B1_LEDGER_PUBLICATION_MODE = "CREATE_ONLY"
B1_RESUME_CHECKPOINT_SCHEMA = "cbsc_omrc_b01_b1_resume_checkpoint_binding_v1"
B1_RESUME_UPDATES = (0, 12, 24)
B1_SLOT_ORDER = tuple((seed, arm) for seed in B1_SEEDS for arm in ARMS)
B1_SLOT_COUNT = 12
B1_OBJECT_ID = "CBSC-OMRC-B01"
B1_INNOVATOR_SELECTION_REQUEST_ID = "cbsc-online-b-innovator-20260901-01"
B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH = (
    "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
    "capability_bound_semantic_currentness/"
    "cbsc-online-b-innovator-20260901-01/RESPONSE.md"
)
B1_INNOVATOR_SELECTION_RESPONSE_SHA256 = (
    "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
)
B1_LITERAL_BINDING_REQUEST_ID = "cbsc-online-b-innovator-20260901-02"
B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH = (
    "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
    "capability_bound_semantic_currentness/"
    "cbsc-online-b-innovator-20260901-02/RESPONSE.md"
)
B1_METRICS_ONLY_REQUEST_ID = "cbsc-online-b-innovator-20260901-03"
B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH = (
    "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
    "capability_bound_semantic_currentness/"
    "cbsc-online-b-innovator-20260901-03/RESPONSE.md"
)
B1_METRICS_ONLY_SPEC_RELATIVE_PATH = (
    "docs/research/candidates/capability_bound_semantic_currentness/"
    "CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md"
)
B1_METRICS_ONLY_RESPONSE_SHA256 = (
    "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
)
B1_LITERAL_BINDING_RESPONSE_SHA256 = (
    "e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844"
)


class B1SlotStatus(str, Enum):
    PENDING = "PENDING"
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"

_COUNTS_PER_ARM_SEED = {
    "train_episodes": 384,
    "train_transitions": 58_368,
    "train_decisions": 9_216,
    "rollout_updates": 48,
    "ppo_epochs_per_rollout": 4,
    "minibatches_per_epoch": 4,
    "optimizer_steps": 768,
    "checkpoint_count": 4,
    "evaluation_episodes_per_checkpoint": 64,
    "evaluation_transitions_per_checkpoint": 9_728,
    "evaluation_decisions_per_checkpoint": 1_536,
    "evaluation_episodes": 256,
    "evaluation_transitions": 38_912,
    "evaluation_decisions": 6_144,
}


def _require_exact(name: str, actual: object, expected: object) -> None:
    if type(actual) is not type(expected) or actual != expected:
        raise B1ContractError(f"{name} differs from the frozen B1 contract")


@dataclass(frozen=True)
class B1Plan:
    run_name: str = B1_RUN_NAME
    seeds: tuple[int, ...] = B1_SEEDS
    arms: tuple[str, ...] = ARMS
    train_episode_ids: tuple[int, ...] = B1_TRAIN_EPISODE_IDS
    rollout_updates: int = B1_ROLLOUT_UPDATES
    ppo_epochs: int = B1_PPO_EPOCHS
    minibatches_per_epoch: int = B1_MINIBATCHES_PER_EPOCH
    minibatch_episode_count: int = B1_MINIBATCH_EPISODE_COUNT
    optimizer_steps_per_arm_seed: int = B1_OPTIMIZER_STEPS_PER_ARM_SEED
    checkpoint_updates: tuple[int, ...] = B1_CHECKPOINT_UPDATES
    eval_stochastic_ids: tuple[int, ...] = B1_EVAL_STOCHASTIC_IDS
    eval_motif_ids: tuple[int, ...] = B1_EVAL_MOTIF_IDS
    resource_caps: ResourceCaps = B1_RESOURCE_CAPS
    object_durable_cap_bytes: int = B1_OBJECT_DURABLE_CAP_BYTES
    object_id: str = B1_OBJECT_ID
    innovator_selection_request_id: str = B1_INNOVATOR_SELECTION_REQUEST_ID
    innovator_selection_archive_path: str = B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH
    innovator_selection_response_sha256: str = B1_INNOVATOR_SELECTION_RESPONSE_SHA256
    literal_binding_request_id: str = B1_LITERAL_BINDING_REQUEST_ID
    literal_binding_archive_path: str = B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH
    metrics_only_spec_path: str = B1_METRICS_ONLY_SPEC_RELATIVE_PATH
    metrics_only_request_id: str = B1_METRICS_ONLY_REQUEST_ID
    metrics_only_archive_path: str = B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH
    metrics_only_response_sha256: str = B1_METRICS_ONLY_RESPONSE_SHA256
    literal_binding_response_sha256: str = B1_LITERAL_BINDING_RESPONSE_SHA256
    scientific_branch: None = None

    def __post_init__(self) -> None:
        expected = (
            ("run_name", self.run_name, B1_RUN_NAME),
            ("seeds", self.seeds, B1_SEEDS),
            ("arms", self.arms, ARMS),
            ("train_episode_ids", self.train_episode_ids, B1_TRAIN_EPISODE_IDS),
            ("rollout_updates", self.rollout_updates, B1_ROLLOUT_UPDATES),
            ("ppo_epochs", self.ppo_epochs, B1_PPO_EPOCHS),
            (
                "minibatches_per_epoch",
                self.minibatches_per_epoch,
                B1_MINIBATCHES_PER_EPOCH,
            ),
            (
                "minibatch_episode_count",
                self.minibatch_episode_count,
                B1_MINIBATCH_EPISODE_COUNT,
            ),
            (
                "optimizer_steps_per_arm_seed",
                self.optimizer_steps_per_arm_seed,
                B1_OPTIMIZER_STEPS_PER_ARM_SEED,
            ),
            ("checkpoint_updates", self.checkpoint_updates, B1_CHECKPOINT_UPDATES),
            ("eval_stochastic_ids", self.eval_stochastic_ids, B1_EVAL_STOCHASTIC_IDS),
            ("eval_motif_ids", self.eval_motif_ids, B1_EVAL_MOTIF_IDS),
            ("resource_caps", self.resource_caps, B1_RESOURCE_CAPS),
            (
                "object_durable_cap_bytes",
                self.object_durable_cap_bytes,
                B1_OBJECT_DURABLE_CAP_BYTES,
            ),
            ("object_id", self.object_id, B1_OBJECT_ID),
            (
                "innovator_selection_request_id",
                self.innovator_selection_request_id,
                B1_INNOVATOR_SELECTION_REQUEST_ID,
            ),
            (
                "innovator_selection_archive_path",
                self.innovator_selection_archive_path,
                B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "innovator_selection_response_sha256",
                self.innovator_selection_response_sha256,
                B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
            ),
            (
                "literal_binding_request_id",
                self.literal_binding_request_id,
                B1_LITERAL_BINDING_REQUEST_ID,
            ),
            (
                "literal_binding_archive_path",
                self.literal_binding_archive_path,
                B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "metrics_only_spec_path",
                self.metrics_only_spec_path,
                B1_METRICS_ONLY_SPEC_RELATIVE_PATH,
            ),
            (
                "metrics_only_request_id",
                self.metrics_only_request_id,
                B1_METRICS_ONLY_REQUEST_ID,
            ),
            (
                "metrics_only_archive_path",
                self.metrics_only_archive_path,
                B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "metrics_only_response_sha256",
                self.metrics_only_response_sha256,
                B1_METRICS_ONLY_RESPONSE_SHA256,
            ),
            (
                "literal_binding_response_sha256",
                self.literal_binding_response_sha256,
                B1_LITERAL_BINDING_RESPONSE_SHA256,
            ),
            ("scientific_branch", self.scientific_branch, None),
        )
        for name, actual, literal in expected:
            _require_exact(name, actual, literal)

    @property
    def counts_per_arm_seed(self) -> dict[str, int]:
        return dict(_COUNTS_PER_ARM_SEED)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_name": self.run_name,
            "seeds": list(self.seeds),
            "arms": list(self.arms),
            "train_episode_ids": list(self.train_episode_ids),
            "rollout_updates": self.rollout_updates,
            "ppo_epochs": self.ppo_epochs,
            "minibatches_per_epoch": self.minibatches_per_epoch,
            "minibatch_episode_count": self.minibatch_episode_count,
            "optimizer_steps_per_arm_seed": self.optimizer_steps_per_arm_seed,
            "checkpoint_updates": list(self.checkpoint_updates),
            "eval_stochastic_ids": list(self.eval_stochastic_ids),
            "eval_motif_ids": list(self.eval_motif_ids),
            "counts_per_arm_seed": self.counts_per_arm_seed,
            "resource_caps": self.resource_caps.as_dict(),
            "object_durable_cap_bytes": self.object_durable_cap_bytes,
            "object_id": self.object_id,
            "innovator_selection_request_id": self.innovator_selection_request_id,
            "innovator_selection_archive_path": self.innovator_selection_archive_path,
            "innovator_selection_response_sha256": self.innovator_selection_response_sha256,
            "literal_binding_request_id": self.literal_binding_request_id,
            "literal_binding_archive_path": self.literal_binding_archive_path,
            "metrics_only_spec_path": self.metrics_only_spec_path,
            "metrics_only_request_id": self.metrics_only_request_id,
            "metrics_only_archive_path": self.metrics_only_archive_path,
            "metrics_only_response_sha256": self.metrics_only_response_sha256,
            "literal_binding_response_sha256": self.literal_binding_response_sha256,
            "scientific_branch": self.scientific_branch,
        }


def _require_nonempty_string(name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise B1ContractError(f"{name} must be a nonempty exact string")
    return value


def _require_lower_hex(name: str, value: object, length: int) -> str:
    text = _require_nonempty_string(name, value)
    if len(text) != length or any(character not in "0123456789abcdef" for character in text):
        raise B1ContractError(f"{name} must be {length} lowercase hexadecimal characters")
    return text


def _require_absolute_path(name: str, value: object, *, json_file: bool = False) -> Path:
    if not isinstance(value, Path) or not value.is_absolute():
        raise B1ContractError(f"{name} must be an absolute pathlib.Path")
    if json_file and value.suffix != ".json":
        raise B1ContractError(f"{name} must identify a JSON receipt")
    return value


@dataclass(frozen=True)
class B1ArmSeedRequest:
    """One exact B1 arm-seed engineering invocation, with bound admission identity."""

    plan: B1Plan
    attempt_id: str
    arm: str
    seed: int
    train_episode_ids: tuple[int, ...]
    checkpoint_updates: tuple[int, ...]
    eval_stochastic_ids: tuple[int, ...]
    eval_motif_ids: tuple[int, ...]
    scratch_root: Path
    durable_root: Path
    admission_schema: str
    admission_receipt_path: Path
    admission_receipt_sha256: str
    implementation_commit: str
    source_conformance_sha256: str
    resource_caps: ResourceCaps
    scientific_branch: None = None

    def __post_init__(self) -> None:
        if type(self.plan) is not B1Plan:
            raise B1ContractError("plan must be the exact immutable B1Plan type")
        self.plan.__post_init__()
        _require_nonempty_string("attempt_id", self.attempt_id)
        if type(self.arm) is not str or self.arm not in ARMS:
            raise B1ContractError("arm is not one of the four frozen B1 arms")
        if type(self.seed) is not int or self.seed not in B1_SEEDS:
            raise B1ContractError("seed is not one of the three frozen B1 seeds")
        for name, actual, literal in (
            ("train_episode_ids", self.train_episode_ids, B1_TRAIN_EPISODE_IDS),
            ("checkpoint_updates", self.checkpoint_updates, B1_CHECKPOINT_UPDATES),
            ("eval_stochastic_ids", self.eval_stochastic_ids, B1_EVAL_STOCHASTIC_IDS),
            ("eval_motif_ids", self.eval_motif_ids, B1_EVAL_MOTIF_IDS),
            ("admission_schema", self.admission_schema, B1_BOUND_ADMISSION_SCHEMA),
            ("resource_caps", self.resource_caps, B1_RESOURCE_CAPS),
            ("scientific_branch", self.scientific_branch, None),
        ):
            _require_exact(name, actual, literal)
        scratch = _require_absolute_path("scratch_root", self.scratch_root)
        durable = _require_absolute_path("durable_root", self.durable_root)
        receipt = _require_absolute_path(
            "admission_receipt_path", self.admission_receipt_path, json_file=True
        )
        resolved = {scratch.resolve(strict=False), durable.resolve(strict=False), receipt.resolve(strict=False)}
        if len(resolved) != 3:
            raise B1ContractError("scratch, durable, and admission receipt paths must be distinct")
        _require_lower_hex("admission_receipt_sha256", self.admission_receipt_sha256, 64)
        _require_lower_hex("implementation_commit", self.implementation_commit, 40)
        _require_lower_hex("source_conformance_sha256", self.source_conformance_sha256, 64)

    @property
    def run_name(self) -> str:
        return self.plan.run_name

    @property
    def admission_binding(self) -> dict[str, str | int]:
        return {
            "schema": self.admission_schema,
            "attempt_id": self.attempt_id,
            "run_name": self.run_name,
            "arm": self.arm,
            "seed": self.seed,
            "implementation_commit": self.implementation_commit,
            "source_conformance_sha256": self.source_conformance_sha256,
            "bound_receipt_path": str(self.admission_receipt_path.resolve(strict=False)),
            "bound_receipt_sha256": self.admission_receipt_sha256,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.as_dict(),
            "attempt_id": self.attempt_id,
            "run_name": self.run_name,
            "arm": self.arm,
            "seed": self.seed,
            "train_episode_ids": list(self.train_episode_ids),
            "checkpoint_updates": list(self.checkpoint_updates),
            "eval_stochastic_ids": list(self.eval_stochastic_ids),
            "eval_motif_ids": list(self.eval_motif_ids),
            "scratch_root": str(self.scratch_root.resolve(strict=False)),
            "durable_root": str(self.durable_root.resolve(strict=False)),
            "admission_binding": self.admission_binding,
            "resource_caps": self.resource_caps.as_dict(),
            "scientific_branch": self.scientific_branch,
        }


@dataclass(frozen=True)
class B1LedgerBinding:
    """Facts shared by every slot and resumable checkpoint in one attempt."""

    attempt_id: str
    run_name: str
    implementation_commit: str
    source_conformance_sha256: str
    configuration_sha256: str
    laws_sha256: str
    b0_manifest_sha256: str
    b0_manifest_bytes: int
    b0_reviewed_receipt_sha256: str
    b0_inventory_sha256: str
    b0_file_count: int
    b0_total_bytes: int
    object_id: str = B1_OBJECT_ID
    innovator_selection_request_id: str = B1_INNOVATOR_SELECTION_REQUEST_ID
    innovator_selection_archive_path: str = B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH
    innovator_selection_response_sha256: str = B1_INNOVATOR_SELECTION_RESPONSE_SHA256
    literal_binding_request_id: str = B1_LITERAL_BINDING_REQUEST_ID
    literal_binding_archive_path: str = B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH
    literal_binding_response_sha256: str = B1_LITERAL_BINDING_RESPONSE_SHA256
    metrics_only_request_id: str = B1_METRICS_ONLY_REQUEST_ID
    metrics_only_archive_path: str = B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH
    metrics_only_response_sha256: str = B1_METRICS_ONLY_RESPONSE_SHA256

    def __post_init__(self) -> None:
        _require_nonempty_string("attempt_id", self.attempt_id)
        _require_exact("run_name", self.run_name, B1_RUN_NAME)
        _require_lower_hex("implementation_commit", self.implementation_commit, 40)
        _require_lower_hex("source_conformance_sha256", self.source_conformance_sha256, 64)
        _require_lower_hex("configuration_sha256", self.configuration_sha256, 64)
        _require_lower_hex("laws_sha256", self.laws_sha256, 64)
        _require_lower_hex("b0_manifest_sha256", self.b0_manifest_sha256, 64)
        if type(self.b0_manifest_bytes) is not int or self.b0_manifest_bytes <= 0:
            raise B1ContractError("b0_manifest_bytes must be a positive integer")
        _require_lower_hex(
            "b0_reviewed_receipt_sha256", self.b0_reviewed_receipt_sha256, 64
        )
        _require_lower_hex("b0_inventory_sha256", self.b0_inventory_sha256, 64)
        if type(self.b0_file_count) is not int or self.b0_file_count <= 0:
            raise B1ContractError("b0_file_count must be a positive integer")
        if type(self.b0_total_bytes) is not int or self.b0_total_bytes <= 0:
            raise B1ContractError("b0_total_bytes must be a positive integer")
        for name, actual, expected in (
            ("object_id", self.object_id, B1_OBJECT_ID),
            (
                "innovator_selection_request_id",
                self.innovator_selection_request_id,
                B1_INNOVATOR_SELECTION_REQUEST_ID,
            ),
            (
                "innovator_selection_archive_path",
                self.innovator_selection_archive_path,
                B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "innovator_selection_response_sha256",
                self.innovator_selection_response_sha256,
                B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
            ),
            (
                "literal_binding_request_id",
                self.literal_binding_request_id,
                B1_LITERAL_BINDING_REQUEST_ID,
            ),
            (
                "literal_binding_archive_path",
                self.literal_binding_archive_path,
                B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "literal_binding_response_sha256",
                self.literal_binding_response_sha256,
                B1_LITERAL_BINDING_RESPONSE_SHA256,
            ),
            (
                "metrics_only_request_id",
                self.metrics_only_request_id,
                B1_METRICS_ONLY_REQUEST_ID,
            ),
            (
                "metrics_only_archive_path",
                self.metrics_only_archive_path,
                B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "metrics_only_response_sha256",
                self.metrics_only_response_sha256,
                B1_METRICS_ONLY_RESPONSE_SHA256,
            ),
        ):
            _require_exact(name, actual, expected)

    def as_dict(self) -> dict[str, str]:
        return {
            "attempt_id": self.attempt_id,
            "run_name": self.run_name,
            "implementation_commit": self.implementation_commit,
            "source_conformance_sha256": self.source_conformance_sha256,
            "configuration_sha256": self.configuration_sha256,
            "laws_sha256": self.laws_sha256,
            "b0_manifest_sha256": self.b0_manifest_sha256,
            "b0_manifest_bytes": self.b0_manifest_bytes,
            "b0_reviewed_receipt_sha256": self.b0_reviewed_receipt_sha256,
            "b0_inventory_sha256": self.b0_inventory_sha256,
            "b0_file_count": self.b0_file_count,
            "b0_total_bytes": self.b0_total_bytes,
            "object_id": self.object_id,
            "innovator_selection_request_id": self.innovator_selection_request_id,
            "innovator_selection_archive_path": self.innovator_selection_archive_path,
            "innovator_selection_response_sha256": self.innovator_selection_response_sha256,
            "literal_binding_request_id": self.literal_binding_request_id,
            "literal_binding_archive_path": self.literal_binding_archive_path,
            "literal_binding_response_sha256": self.literal_binding_response_sha256,
            "metrics_only_request_id": self.metrics_only_request_id,
            "metrics_only_archive_path": self.metrics_only_archive_path,
            "metrics_only_response_sha256": self.metrics_only_response_sha256,
        }


def _require_slot_identity(slot_index: object, seed: object, arm: object) -> None:
    if type(slot_index) is not int or slot_index < 0 or slot_index >= B1_SLOT_COUNT:
        raise B1ContractError("slot_index is outside the frozen 12-slot ledger")
    if (seed, arm) != B1_SLOT_ORDER[slot_index]:
        raise B1ContractError("slot identity differs from frozen seed-major order")


def _require_relative_checkpoint_path(value: object) -> str:
    text = _require_nonempty_string("checkpoint_relative_path", value)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".pt" or path.as_posix() != text:
        raise B1ContractError("checkpoint_relative_path must be a confined POSIX .pt path")
    return text


@dataclass(frozen=True)
class B1ResumeCheckpointBinding:
    """Non-bare identity envelope for one resumable incomplete-slot checkpoint."""

    binding: B1LedgerBinding
    slot_index: int
    seed: int
    arm: str
    completed_rollout_updates: int
    checkpoint_relative_path: str
    checkpoint_sha256: str
    order_chain_sha256: str
    schema: str = B1_RESUME_CHECKPOINT_SCHEMA

    def __post_init__(self) -> None:
        if type(self.binding) is not B1LedgerBinding:
            raise B1ContractError("resume checkpoint binding must be a B1LedgerBinding")
        self.binding.__post_init__()
        _require_exact("resume checkpoint schema", self.schema, B1_RESUME_CHECKPOINT_SCHEMA)
        _require_slot_identity(self.slot_index, self.seed, self.arm)
        if (
            type(self.completed_rollout_updates) is not int
            or self.completed_rollout_updates not in B1_RESUME_UPDATES
        ):
            raise B1ContractError("resume checkpoint update is not a frozen 0/12/24 boundary")
        _require_relative_checkpoint_path(self.checkpoint_relative_path)
        _require_lower_hex("checkpoint_sha256", self.checkpoint_sha256, 64)
        _require_lower_hex("order_chain_sha256", self.order_chain_sha256, 64)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "binding": self.binding.as_dict(),
            "slot_index": self.slot_index,
            "seed": self.seed,
            "arm": self.arm,
            "completed_rollout_updates": self.completed_rollout_updates,
            "checkpoint_relative_path": self.checkpoint_relative_path,
            "checkpoint_sha256": self.checkpoint_sha256,
            "order_chain_sha256": self.order_chain_sha256,
        }


@dataclass(frozen=True)
class B1SlotLedgerEntry:
    """One immutable slot state in the canonical seed-major attempt ledger."""

    binding: B1LedgerBinding
    slot_index: int
    seed: int
    arm: str
    status: B1SlotStatus
    raw_result_sha256: str | None = None
    admission_sha256: str | None = None
    telemetry_sha256: str | None = None
    files_sha256: str | None = None
    incident_sha256: str | None = None
    resume_checkpoint: B1ResumeCheckpointBinding | None = None

    def __post_init__(self) -> None:
        if type(self.binding) is not B1LedgerBinding:
            raise B1ContractError("slot binding must be a B1LedgerBinding")
        self.binding.__post_init__()
        _require_slot_identity(self.slot_index, self.seed, self.arm)
        if type(self.status) is not B1SlotStatus:
            raise B1ContractError("slot status must be COMPLETE, PENDING, or INCOMPLETE")
        evidence = (
            self.raw_result_sha256,
            self.admission_sha256,
            self.telemetry_sha256,
            self.files_sha256,
        )
        if self.status is B1SlotStatus.PENDING:
            if any(value is not None for value in evidence) or self.incident_sha256 is not None or self.resume_checkpoint is not None:
                raise B1ContractError("PENDING slot must not contain evidence or resume state")
        elif self.status is B1SlotStatus.COMPLETE:
            if self.incident_sha256 is not None or self.resume_checkpoint is not None:
                raise B1ContractError("COMPLETE slot must not contain incident or resume state")
            if any(value is None for value in evidence):
                raise B1ContractError("COMPLETE slot requires raw/admission/telemetry/files SHA")
            for name, value in zip(
                ("raw_result_sha256", "admission_sha256", "telemetry_sha256", "files_sha256"),
                evidence,
            ):
                _require_lower_hex(name, value, 64)
        else:
            if any(value is not None for value in evidence):
                raise B1ContractError("INCOMPLETE slot cannot masquerade as COMPLETE evidence")
            _require_lower_hex("incident_sha256", self.incident_sha256, 64)
            if self.resume_checkpoint is None:
                return
            if type(self.resume_checkpoint) is not B1ResumeCheckpointBinding:
                raise B1ContractError(
                    "INCOMPLETE resume checkpoint must be absent or canonically bound"
                )
            resume = self.resume_checkpoint
            if (
                resume.binding != self.binding
                or resume.slot_index != self.slot_index
                or resume.seed != self.seed
                or resume.arm != self.arm
            ):
                raise B1ContractError("resume checkpoint binding differs from its incomplete slot")

    def as_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.as_dict(),
            "slot_index": self.slot_index,
            "seed": self.seed,
            "arm": self.arm,
            "status": self.status.value,
            "raw_result_sha256": self.raw_result_sha256,
            "admission_sha256": self.admission_sha256,
            "telemetry_sha256": self.telemetry_sha256,
            "files_sha256": self.files_sha256,
            "incident_sha256": self.incident_sha256,
            "resume_checkpoint": (
                None if self.resume_checkpoint is None else self.resume_checkpoint.as_dict()
            ),
        }


@dataclass(frozen=True)
class B1AttemptLedger:
    """Complete immutable 12-slot ledger snapshot for create-only publication."""

    schema: str
    publication_mode: str
    binding: B1LedgerBinding
    slots: tuple[B1SlotLedgerEntry, ...]

    def __post_init__(self) -> None:
        validate_b1_attempt_ledger(self)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "publication_mode": self.publication_mode,
            "binding": self.binding.as_dict(),
            "slot_order": [
                {"slot_index": index, "seed": seed, "arm": arm}
                for index, (seed, arm) in enumerate(B1_SLOT_ORDER)
            ],
            "slots": [slot.as_dict() for slot in self.slots],
        }


def validate_b1_attempt_ledger(value: B1AttemptLedger) -> B1AttemptLedger:
    if type(value) is not B1AttemptLedger:
        raise B1ContractError("attempt ledger must be the immutable canonical type")
    _require_exact("attempt ledger schema", value.schema, B1_LEDGER_SCHEMA)
    _require_exact(
        "attempt ledger publication mode",
        value.publication_mode,
        B1_LEDGER_PUBLICATION_MODE,
    )
    if type(value.binding) is not B1LedgerBinding:
        raise B1ContractError("attempt ledger binding must be a B1LedgerBinding")
    value.binding.__post_init__()
    if type(value.slots) is not tuple or len(value.slots) != B1_SLOT_COUNT:
        raise B1ContractError("attempt ledger requires exactly 12 seed-major slots")
    incomplete = 0
    previous_status_rank = -1
    status_rank = {
        B1SlotStatus.COMPLETE: 0,
        B1SlotStatus.INCOMPLETE: 1,
        B1SlotStatus.PENDING: 2,
    }
    for position, slot in enumerate(value.slots):
        if type(slot) is not B1SlotLedgerEntry:
            raise B1ContractError("attempt ledger slots must be immutable canonical entries")
        slot.__post_init__()
        expected_seed, expected_arm = B1_SLOT_ORDER[position]
        if (
            slot.slot_index != position
            or slot.seed != expected_seed
            or slot.arm != expected_arm
        ):
            raise B1ContractError("attempt ledger slots differ from frozen seed-major order")
        if slot.binding != value.binding:
            raise B1ContractError("attempt ledger refuses cross-source slot mixing")
        current_status_rank = status_rank[slot.status]
        if current_status_rank < previous_status_rank:
            raise B1ContractError(
                "attempt ledger status progression must be COMPLETE*, INCOMPLETE?, PENDING*"
            )
        previous_status_rank = current_status_rank
        incomplete += int(slot.status is B1SlotStatus.INCOMPLETE)
    if incomplete > 1:
        raise B1ContractError("attempt ledger permits at most one INCOMPLETE slot")
    return value


__all__ = [
    "B1ArmSeedRequest",
    "B1AttemptLedger",
    "B1_BOUND_ADMISSION_SCHEMA",
    "B1_CHECKPOINT_UPDATES",
    "B1_EVAL_MOTIF_IDS",
    "B1_EVAL_STOCHASTIC_IDS",
    "B1_OBJECT_DURABLE_CAP_BYTES",
    "B1_OPTIMIZER_STEPS_PER_ARM_SEED",
    "B1_LEDGER_PUBLICATION_MODE",
    "B1_LEDGER_SCHEMA",
    "B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH",
    "B1_INNOVATOR_SELECTION_REQUEST_ID",
    "B1_INNOVATOR_SELECTION_RESPONSE_SHA256",
    "B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH",
    "B1_LITERAL_BINDING_REQUEST_ID",
    "B1_METRICS_ONLY_RESPONSE_SHA256",
    "B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH",
    "B1_METRICS_ONLY_REQUEST_ID",
    "B1_METRICS_ONLY_SPEC_RELATIVE_PATH",
    "B1_LITERAL_BINDING_RESPONSE_SHA256",
    "B1_OBJECT_ID",
    "B1LedgerBinding",
    "B1Plan",
    "B1_RESOURCE_CAPS",
    "B1_ROLLOUT_UPDATES",
    "B1_RUN_NAME",
    "B1_RESUME_CHECKPOINT_SCHEMA",
    "B1_RESUME_UPDATES",
    "B1ResumeCheckpointBinding",
    "B1_SEEDS",
    "B1_SLOT_COUNT",
    "B1_SLOT_ORDER",
    "B1SlotLedgerEntry",
    "B1SlotStatus",
    "B1_TRAIN_EPISODE_IDS",
    "B1_WALL_CAP_SECONDS",
    "B1ContractError",
    "validate_b1_attempt_ledger",
]

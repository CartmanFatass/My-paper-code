"""Exact arm-seed recurrent-PPO execution and resume seam for OMRC B1.

The module emits raw engineering evidence.  It does not aggregate endpoints,
choose a branch, or publish a B1 result artifact.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Mapping, Sequence

import torch

from . import addressing
from .b1_contract import (
    B1_CHECKPOINT_UPDATES,
    B1_EVAL_MOTIF_IDS,
    B1_EVAL_STOCHASTIC_IDS,
    B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
    B1_INNOVATOR_SELECTION_REQUEST_ID,
    B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
    B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
    B1_LITERAL_BINDING_REQUEST_ID,
    B1_LITERAL_BINDING_RESPONSE_SHA256,
    B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
    B1_METRICS_ONLY_REQUEST_ID,
    B1_METRICS_ONLY_RESPONSE_SHA256,
    B1_OBJECT_ID,
    B1ArmSeedRequest,
    B1ContractError,
)
from .b1_runtime_audit import (
    ALLOWED_LEARNER_FIELDS,
    B1RuntimeAuditError,
    ModelResetObserver,
    build_mechanical_direct,
    checkpoint_roundtrip_record,
    observe_learner_visibility,
    require_frozen_execution_modes,
)
from .b1_training_records import (
    TrainingExposureRecords,
    build_training_exposure_records,
    merge_training_exposure_slices,
)
from .checkpoint import (
    _validate_payload as _validate_recurrent_checkpoint,
    capture_checkpoint,
    model_parameter_digest_from_state,
    restore_checkpoint,
)
from .engine import (
    _ADAPTERS,
    _evaluate_heldout,
    _optimizer_digest,
    _project_panel,
    _rollout_from_panel,
    _tape_primitive_digest,
    _training_action_uniforms,
)
from .host import DynamicHost
from .model import OBJECT_ID, CommonRecurrentActorCritic, model_parameter_digest
from .contract import EPISODE_TRANSITIONS
from .ppo import (
    EPISODES_PER_ROLLOUT,
    PPOConfig,
    RecurrentPPOTrainer,
    config_digest,
    make_adam,
)
from .tapes import EpisodeTape


B1_CHECKPOINT_SCHEMA = "cbsc_omrc_b01_b1_checkpoint_envelope_v1"
B1_RAW_EVIDENCE_SCHEMA = "cbsc_omrc_b01_b1_arm_seed_slice_raw_evidence_v1"
_ENVELOPE_KEYS = frozenset({"schema", "binding", "recurrent_ppo_checkpoint"})
_BINDING_KEYS = frozenset(
    {
        "object_id",
        "attempt_id",
        "run_name",
        "arm",
        "seed",
        "completed_rollout_updates",
        "train_episode_ids_sha256",
        "full_training_tape_digest",
        "full_action_uniform_digest",
        "ppo_configuration_digest",
        "implementation_commit",
        "source_conformance_sha256",
        "innovator_selection_request_id",
        "innovator_selection_archive_path",
        "innovator_selection_response_sha256",
        "literal_binding_request_id",
        "literal_binding_archive_path",
        "literal_binding_response_sha256",
        "metrics_only_request_id",
        "metrics_only_archive_path",
        "metrics_only_response_sha256",
    }
)


class B1EngineError(ValueError):
    """A B1 slice or persistent-state binding is not exact."""


@dataclass(frozen=True)
class B1SliceCounts:
    """Exact work newly produced by one checkpoint-bounded invocation."""

    rollout_updates: int
    train_episodes: int
    train_transitions: int
    evaluation_checkpoints: int
    evaluation_episodes: int
    evaluation_transitions: int

    @property
    def scientific_work_transitions(self) -> int:
        return self.train_transitions + self.evaluation_transitions


def b1_slice_counts(start_update: int, stop_update: int, *, fresh: bool) -> B1SliceCounts:
    """Count only training and held-out work created by this slice."""

    checkpoint_updates = b1_slice_checkpoint_updates(
        start_update, stop_update, fresh=fresh
    )
    rollout_updates = stop_update - start_update
    train_episodes = rollout_updates * EPISODES_PER_ROLLOUT
    evaluation_episodes_per_checkpoint = len(B1_EVAL_STOCHASTIC_IDS) + len(
        B1_EVAL_MOTIF_IDS
    )
    evaluation_episodes = len(checkpoint_updates) * evaluation_episodes_per_checkpoint
    return B1SliceCounts(
        rollout_updates=rollout_updates,
        train_episodes=train_episodes,
        train_transitions=train_episodes * EPISODE_TRANSITIONS,
        evaluation_checkpoints=len(checkpoint_updates),
        evaluation_episodes=evaluation_episodes,
        evaluation_transitions=evaluation_episodes * EPISODE_TRANSITIONS,
    )


def b1_slice_checkpoint_updates(
    start_update: int, stop_update: int, *, fresh: bool
) -> tuple[int, ...]:
    """Return checkpoints evaluated by this invocation, including resumed update zero."""

    if type(fresh) is not bool:
        raise B1EngineError("fresh must be a bool")
    if start_update not in B1_CHECKPOINT_UPDATES or stop_update not in B1_CHECKPOINT_UPDATES:
        raise B1EngineError("slice endpoints must be frozen B1 checkpoint boundaries")
    if stop_update <= start_update or (fresh and start_update != 0):
        raise B1EngineError("slice work interval is invalid")
    return tuple(
        ([0] if start_update == 0 else [])
        + [
            checkpoint
            for checkpoint in B1_CHECKPOINT_UPDATES
            if start_update < checkpoint <= stop_update
        ]
    )


def build_stage_measurements(
    counts: B1SliceCounts,
    *,
    train_wall_seconds: float,
    train_cpu_seconds: float,
    evaluation_wall_seconds: float,
    evaluation_cpu_seconds: float,
) -> list[dict[str, Any]]:
    """Build the exact list shape validated by ``ProcessTreeMonitor`` telemetry."""

    if not isinstance(counts, B1SliceCounts):
        raise B1EngineError("stage measurements require B1SliceCounts")
    measurements = (
        ("train", train_wall_seconds, train_cpu_seconds, counts.train_transitions),
        (
            "evaluate",
            evaluation_wall_seconds,
            evaluation_cpu_seconds,
            counts.evaluation_transitions,
        ),
    )
    stages: list[dict[str, Any]] = []
    for stage, wall, cpu, transitions in measurements:
        if (
            isinstance(wall, bool)
            or isinstance(cpu, bool)
            or float(wall) <= 0.0
            or float(cpu) <= 0.0
            or transitions <= 0
        ):
            raise B1EngineError(f"{stage} stage measurement must report positive work")
        stages.append(
            {
                "stage": stage,
                "wall_seconds": float(wall),
                "cpu_seconds": float(cpu),
                "transitions": transitions,
                "transitions_per_second": transitions / float(wall),
            }
        )
    return stages


def _sha256_jsonable(value: object) -> str:
    import json

    encoded = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _require_digest(name: str, value: object, length: int = 64) -> str:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1EngineError(f"{name} must be {length} lowercase hexadecimal characters")
    return value


@dataclass(frozen=True)
class B1CheckpointBinding:
    """All immutable facts required to continue one arm-seed path exactly."""

    object_id: str
    attempt_id: str
    run_name: str
    arm: str
    seed: int
    completed_rollout_updates: int
    train_episode_ids_sha256: str
    full_training_tape_digest: str
    full_action_uniform_digest: str
    ppo_configuration_digest: str
    implementation_commit: str
    source_conformance_sha256: str
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
        if self.object_id != OBJECT_ID or self.object_id != B1_OBJECT_ID:
            raise B1EngineError("checkpoint object identity differs")
        if not self.attempt_id or self.run_name != addressing.B1_RUN:
            raise B1EngineError("checkpoint attempt/run identity differs")
        if self.arm not in _ADAPTERS or type(self.seed) is not int:
            raise B1EngineError("checkpoint arm/seed identity differs")
        if self.completed_rollout_updates not in B1_CHECKPOINT_UPDATES:
            raise B1EngineError("checkpoint update is not a frozen B1 checkpoint boundary")
        for name in (
            "train_episode_ids_sha256",
            "full_training_tape_digest",
            "full_action_uniform_digest",
            "ppo_configuration_digest",
            "source_conformance_sha256",
        ):
            _require_digest(name.replace("_", " "), getattr(self, name))
        _require_digest("implementation commit", self.implementation_commit, 40)
        for name, actual, expected in (
            (
                "innovator selection request",
                self.innovator_selection_request_id,
                B1_INNOVATOR_SELECTION_REQUEST_ID,
            ),
            (
                "innovator selection archive",
                self.innovator_selection_archive_path,
                B1_INNOVATOR_SELECTION_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "innovator selection response",
                self.innovator_selection_response_sha256,
                B1_INNOVATOR_SELECTION_RESPONSE_SHA256,
            ),
            (
                "literal binding request",
                self.literal_binding_request_id,
                B1_LITERAL_BINDING_REQUEST_ID,
            ),
            (
                "literal binding archive",
                self.literal_binding_archive_path,
                B1_LITERAL_BINDING_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "literal binding response",
                self.literal_binding_response_sha256,
                B1_LITERAL_BINDING_RESPONSE_SHA256,
            ),
            (
                "metrics-only request",
                self.metrics_only_request_id,
                B1_METRICS_ONLY_REQUEST_ID,
            ),
            (
                "metrics-only archive",
                self.metrics_only_archive_path,
                B1_METRICS_ONLY_ARCHIVE_RELATIVE_PATH,
            ),
            (
                "metrics-only response",
                self.metrics_only_response_sha256,
                B1_METRICS_ONLY_RESPONSE_SHA256,
            ),
        ):
            if type(actual) is not str or actual != expected:
                raise B1EngineError(f"checkpoint {name} identity differs")

    @classmethod
    def from_request(
        cls,
        request: B1ArmSeedRequest,
        *,
        completed_rollout_updates: int,
        full_training_tape_digest: str,
        full_action_uniform_digest: str,
    ) -> "B1CheckpointBinding":
        request.__post_init__()
        return cls(
            object_id=OBJECT_ID,
            attempt_id=request.attempt_id,
            run_name=request.run_name,
            arm=request.arm,
            seed=request.seed,
            completed_rollout_updates=completed_rollout_updates,
            train_episode_ids_sha256=_sha256_jsonable(list(request.train_episode_ids)),
            full_training_tape_digest=full_training_tape_digest,
            full_action_uniform_digest=full_action_uniform_digest,
            ppo_configuration_digest=config_digest(PPOConfig()),
            implementation_commit=request.implementation_commit,
            source_conformance_sha256=request.source_conformance_sha256,
            innovator_selection_request_id=request.plan.innovator_selection_request_id,
            innovator_selection_archive_path=request.plan.innovator_selection_archive_path,
            innovator_selection_response_sha256=request.plan.innovator_selection_response_sha256,
            literal_binding_request_id=request.plan.literal_binding_request_id,
            literal_binding_archive_path=request.plan.literal_binding_archive_path,
            literal_binding_response_sha256=request.plan.literal_binding_response_sha256,
            metrics_only_request_id=request.plan.metrics_only_request_id,
            metrics_only_archive_path=request.plan.metrics_only_archive_path,
            metrics_only_response_sha256=request.plan.metrics_only_response_sha256,
        )


def _new_trainer(seed: int) -> RecurrentPPOTrainer:
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    return RecurrentPPOTrainer(
        model,
        run_name=addressing.B1_RUN,
        seed=seed,
        optimizer=make_adam(model),
        address_u64=addressing.u64,
    )


def _validate_envelope(value: Mapping[str, Any]) -> B1CheckpointBinding:
    if not isinstance(value, Mapping) or frozenset(value) != _ENVELOPE_KEYS:
        raise B1EngineError("B1 checkpoint envelope schema is incomplete or extended")
    if value["schema"] != B1_CHECKPOINT_SCHEMA:
        raise B1EngineError("B1 checkpoint envelope schema differs")
    raw_binding = value["binding"]
    if not isinstance(raw_binding, Mapping) or frozenset(raw_binding) != _BINDING_KEYS:
        raise B1EngineError("B1 checkpoint binding schema is incomplete or extended")
    try:
        binding = B1CheckpointBinding(**raw_binding)
        _validate_recurrent_checkpoint(value["recurrent_ppo_checkpoint"])
    except (TypeError, ValueError) as exc:
        if isinstance(exc, B1EngineError):
            raise
        raise B1EngineError("B1 recurrent-PPO checkpoint is invalid") from exc
    inner = value["recurrent_ppo_checkpoint"]
    identity = inner["identity"]
    if (
        identity["run_name"] != binding.run_name
        or identity["arm"] != binding.arm
        or identity["seed"] != binding.seed
        or identity["completed_rollout_updates"] != binding.completed_rollout_updates
    ):
        raise B1EngineError("B1 envelope/inner checkpoint identity mismatch")
    digests = inner["digests"]
    if (
        digests["training_tape"] != binding.full_training_tape_digest
        or digests["action_uniform"] != binding.full_action_uniform_digest
        or digests["configuration"] != binding.ppo_configuration_digest
    ):
        raise B1EngineError("B1 envelope/inner checkpoint digest mismatch")
    return binding


def capture_b1_checkpoint(
    trainer: RecurrentPPOTrainer, binding: B1CheckpointBinding
) -> dict[str, Any]:
    """Capture model, Adam, counters, order chain, and immutable B1 bindings."""

    if (
        trainer.run_name != binding.run_name
        or trainer.seed != binding.seed
        or trainer.counters.rollout_updates != binding.completed_rollout_updates
        or config_digest(trainer.config) != binding.ppo_configuration_digest
    ):
        raise B1EngineError("trainer state differs from the B1 checkpoint binding")
    inner = capture_checkpoint(
        trainer,
        arm=binding.arm,
        training_tape_digest=binding.full_training_tape_digest,
        action_uniform_digest=binding.full_action_uniform_digest,
    )
    envelope = {
        "schema": B1_CHECKPOINT_SCHEMA,
        "binding": asdict(binding),
        "recurrent_ppo_checkpoint": inner,
    }
    _validate_envelope(envelope)
    return envelope


def save_b1_checkpoint(path: str | Path, envelope: Mapping[str, Any]) -> None:
    """Atomically claim a new B1 checkpoint path without replacement."""

    _validate_envelope(envelope)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"B1 checkpoint already exists: {destination}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".hmasd-b1-", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as stream:
            torch.save(dict(envelope), stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_b1_checkpoint(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("rb") as stream:
        try:
            envelope = torch.load(stream, map_location="cpu", weights_only=True)
        except TypeError:  # pragma: no cover - older PyTorch compatibility
            stream.seek(0)
            envelope = torch.load(stream, map_location="cpu")
    _validate_envelope(envelope)
    return dict(envelope)


def restore_b1_checkpoint(
    envelope: Mapping[str, Any],
    trainer: RecurrentPPOTrainer,
    *,
    request: B1ArmSeedRequest,
    expected_update: int,
    full_training_tape_digest: str,
    full_action_uniform_digest: str,
) -> None:
    """Validate every continuation fact before mutating trainer state."""

    actual = _validate_envelope(envelope)
    expected = B1CheckpointBinding.from_request(
        request,
        completed_rollout_updates=expected_update,
        full_training_tape_digest=full_training_tape_digest,
        full_action_uniform_digest=full_action_uniform_digest,
    )
    differences: list[str] = []
    labels = {
        "completed_rollout_updates": "update",
        "full_training_tape_digest": "training tape",
        "full_action_uniform_digest": "action uniform",
        "source_conformance_sha256": "source",
    }
    for field_name in _BINDING_KEYS:
        if getattr(actual, field_name) != getattr(expected, field_name):
            differences.append(labels.get(field_name, field_name.replace("_", " ")))
    if differences:
        raise B1EngineError(
            "checkpoint resume binding mismatch: " + ", ".join(sorted(differences))
        )
    restore_checkpoint(
        envelope["recurrent_ppo_checkpoint"],
        trainer,
        expected_arm=request.arm,
        expected_training_tape_digest=full_training_tape_digest,
        expected_action_uniform_digest=full_action_uniform_digest,
    )


def audit_b1_checkpoint(
    path: Path,
    *,
    saved_bytes: bytes,
    request: B1ArmSeedRequest,
    expected_update: int,
    full_training_tape_digest: str,
    full_action_uniform_digest: str,
    expected_trainer: RecurrentPPOTrainer,
) -> dict[str, str]:
    """Strictly reread and restore one checkpoint without mutating production state."""

    if (
        not isinstance(path, Path)
        or not isinstance(saved_bytes, bytes)
        or not saved_bytes
        or not isinstance(expected_trainer, RecurrentPPOTrainer)
    ):
        raise B1RuntimeAuditError("checkpoint audit input differs")
    production_parameter_before = model_parameter_digest(expected_trainer.model)
    production_optimizer_before = _optimizer_digest(expected_trainer)
    production_counters_before = asdict(expected_trainer.counters)
    production_order_before = expected_trainer.minibatch_order_digest
    rng_before = torch.random.get_rng_state().clone()
    try:
        envelope = load_b1_checkpoint(path)
        loaded_bytes = path.read_bytes()
        fresh = _new_trainer(request.seed)
        restore_b1_checkpoint(
            envelope,
            fresh,
            request=request,
            expected_update=expected_update,
            full_training_tape_digest=full_training_tape_digest,
            full_action_uniform_digest=full_action_uniform_digest,
        )
        restored_parameter = model_parameter_digest(fresh.model)
        restored_optimizer = _optimizer_digest(fresh)
    except Exception as exc:
        raise B1RuntimeAuditError("checkpoint strict fresh restore failed") from exc
    if (
        restored_optimizer != production_optimizer_before
        or asdict(fresh.counters) != production_counters_before
        or fresh.minibatch_order_digest != production_order_before
    ):
        raise B1RuntimeAuditError("checkpoint fresh optimizer/counter/order restore differs")
    if (
        model_parameter_digest(expected_trainer.model) != production_parameter_before
        or _optimizer_digest(expected_trainer) != production_optimizer_before
        or asdict(expected_trainer.counters) != production_counters_before
        or expected_trainer.minibatch_order_digest != production_order_before
    ):
        raise B1RuntimeAuditError("checkpoint audit mutated production trainer")
    if not torch.equal(torch.random.get_rng_state(), rng_before):
        raise B1RuntimeAuditError("checkpoint audit changed torch RNG state")
    return checkpoint_roundtrip_record(
        f"checkpoint-{request.arm}-{request.seed}-update-{expected_update}",
        saved_bytes=saved_bytes,
        loaded_bytes=loaded_bytes,
        expected_parameter_sha256=production_parameter_before,
        restored_parameter_sha256=restored_parameter,
    )


def _receipt_is_bound(request: B1ArmSeedRequest) -> None:
    path = request.admission_receipt_path
    if not path.is_file():
        raise B1EngineError("arm-seed memory admission receipt is absent")
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != request.admission_receipt_sha256:
        raise B1EngineError("arm-seed memory admission receipt digest differs")


def _tape_records(tapes: Sequence[EpisodeTape]) -> list[dict[str, Any]]:
    return [
        {
            "identity": asdict(tape.identity),
            "primitive_digest_observed": tape.primitive_digest,
            "draw_digest_observed": tape.generation_audit.draw_digest,
            "draw_count_observed": tape.generation_audit.draw_count,
        }
        for tape in tapes
    ]


class LiteralB1ArmSeedEngine:
    """One-process, one-thread exact B1 arm-seed recurrent-PPO engine."""

    worker_count = 1
    threads_per_worker = 1
    checkpoint_updates = B1_CHECKPOINT_UPDATES
    source_paths = (
        "docs/research/candidates/capability_bound_semantic_currentness/DIRECTION.md",
        "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md",
        "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/__init__.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/addressing.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/artifact.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b0.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_contract.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_engine.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_runtime_audit.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_training_records.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_worker.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/checkpoint.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/contract.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/engine.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/evaluator.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/host.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ledger.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/model.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/state.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/tapes.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/telemetry.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/token.py",
    )

    @staticmethod
    def _validate_slice(
        start_update: int, stop_update: int, resume_checkpoint: Path | None
    ) -> None:
        if start_update not in B1_CHECKPOINT_UPDATES or stop_update not in B1_CHECKPOINT_UPDATES:
            raise B1EngineError("slice endpoints must be frozen B1 checkpoint boundaries")
        if stop_update <= start_update:
            raise B1EngineError("slice stop update must be after start update")
        if resume_checkpoint is None and start_update != 0:
            raise B1EngineError("a fresh B1 slice must start at update 0")
        if resume_checkpoint is not None and not isinstance(resume_checkpoint, Path):
            raise B1EngineError("resume checkpoint must be a pathlib.Path")

    def run_slice(
        self,
        request: B1ArmSeedRequest,
        *,
        start_update: int,
        stop_update: int,
        resume_checkpoint: Path | None,
    ) -> Mapping[str, Any]:
        """Run one exact checkpoint-bounded slice and return raw evidence only."""

        try:
            request.__post_init__()
        except B1ContractError as exc:
            raise B1EngineError("B1 arm-seed request differs from contract") from exc
        self._validate_slice(start_update, stop_update, resume_checkpoint)
        _receipt_is_bound(request)
        adapter_factory = _ADAPTERS[request.arm]

        host = DynamicHost(request.run_name, request.seed)
        train_tapes = tuple(
            host.build_stochastic(addressing.TRAIN, episode_id)
            for episode_id in request.train_episode_ids
        )
        full_training_tape_digest = _tape_primitive_digest(train_tapes)
        _, full_action_uniform_digest, _ = _training_action_uniforms(
            train_tapes, request.run_name, request.seed
        )
        eval_tapes = tuple(
            host.build_stochastic(addressing.EVAL_STOCHASTIC, episode_id)
            for episode_id in request.eval_stochastic_ids
        ) + tuple(host.build_motif(tape_id) for tape_id in request.eval_motif_ids)

        original_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        try:
            trainer = _new_trainer(request.seed)
            active_modes = require_frozen_execution_modes(trainer.model)
            resume_envelope: Mapping[str, Any] | None = None
            if resume_checkpoint is not None:
                resume_envelope = load_b1_checkpoint(resume_checkpoint)
                restore_b1_checkpoint(
                    resume_envelope,
                    trainer,
                    request=request,
                    expected_update=start_update,
                    full_training_tape_digest=full_training_tape_digest,
                    full_action_uniform_digest=full_action_uniform_digest,
                )

            checkpoint_records: list[dict[str, Any]] = []
            evaluation_records: list[dict[str, Any]] = []
            rollout_records: list[dict[str, Any]] = []
            training_record_chunks: list[TrainingExposureRecords] = []
            reset_records: list[dict[str, Any]] = []
            mechanical_checkpoint_records: list[dict[str, Any]] = []
            learner_visibility_records: list[dict[str, Any]] = []
            train_wall_seconds = 0.0
            train_cpu_seconds = 0.0
            evaluation_wall_seconds = 0.0
            evaluation_cpu_seconds = 0.0

            def checkpoint_and_evaluate(
                update: int,
                *,
                existing_path: Path | None = None,
                existing_checkpoint: Mapping[str, Any] | None = None,
            ) -> None:
                nonlocal evaluation_wall_seconds, evaluation_cpu_seconds
                stage_wall = time.perf_counter()
                stage_cpu = time.process_time()
                binding = B1CheckpointBinding.from_request(
                    request,
                    completed_rollout_updates=update,
                    full_training_tape_digest=full_training_tape_digest,
                    full_action_uniform_digest=full_action_uniform_digest,
                )
                if (existing_path is None) != (existing_checkpoint is None):
                    raise B1EngineError("existing checkpoint path/payload must be paired")
                if existing_checkpoint is None:
                    checkpoint = capture_b1_checkpoint(trainer, binding)
                    path = request.durable_root / f"checkpoint-update-{update}.pt"
                    save_b1_checkpoint(path, checkpoint)
                else:
                    checkpoint = existing_checkpoint
                    path = existing_path
                    if path is None or path.name != f"checkpoint-update-{update}.pt":
                        raise B1EngineError("resumed checkpoint path identity differs")
                    if checkpoint["binding"] != asdict(binding):
                        raise B1EngineError("resumed checkpoint binding differs at evaluation")
                checkpoint_bytes = path.read_bytes()
                observations, work = _project_panel(eval_tapes, adapter_factory)
                learner_visibility_records.append(
                    observe_learner_visibility(
                        f"eval-update-{update}:learner-input",
                        observations,
                        episode_count=len(eval_tapes),
                        visible_fields=ALLOWED_LEARNER_FIELDS,
                    )
                )
                optimizer_before = _optimizer_digest(trainer)
                with ModelResetObserver(
                    trainer.model,
                    name=f"eval-update-{update}:h0",
                    records=reset_records,
                ):
                    actions, heldout_state = _evaluate_heldout(
                        eval_tapes, observations, trainer.model
                    )
                optimizer_after = _optimizer_digest(trainer)
                if optimizer_before != optimizer_after:
                    raise B1EngineError("held-out evaluation changed optimizer state")
                if existing_checkpoint is not None and path.read_bytes() != checkpoint_bytes:
                    raise B1EngineError("resumed checkpoint bytes changed during evaluation")
                mechanical_checkpoint_records.append(
                    audit_b1_checkpoint(
                        path,
                        saved_bytes=checkpoint_bytes,
                        request=request,
                        expected_update=update,
                        full_training_tape_digest=full_training_tape_digest,
                        full_action_uniform_digest=full_action_uniform_digest,
                        expected_trainer=trainer,
                    )
                )
                checkpoint_records.append(
                    {
                        "update": update,
                        "relative_path": path.name,
                        "sha256": hashlib.sha256(checkpoint_bytes).hexdigest(),
                        "byte_count": len(checkpoint_bytes),
                        "binding": asdict(binding),
                        "counters": dict(checkpoint["recurrent_ppo_checkpoint"]["counters"]),
                        "digests": dict(checkpoint["recurrent_ppo_checkpoint"]["digests"]),
                        "model_parameter_digest": model_parameter_digest_from_state(
                            checkpoint["recurrent_ppo_checkpoint"]["model_state"]
                        ),
                    }
                )
                evaluation_records.append(
                    {
                        "update": update,
                        "actions": actions,
                        "heldout_state_observations": {
                            **heldout_state,
                            "optimizer_digest_before": optimizer_before,
                            "optimizer_digest_after": optimizer_after,
                        },
                        "adapter_work_receipt": asdict(work),
                    }
                )
                evaluation_wall_seconds += time.perf_counter() - stage_wall
                evaluation_cpu_seconds += time.process_time() - stage_cpu

            if start_update == 0:
                checkpoint_and_evaluate(
                    0,
                    existing_path=resume_checkpoint,
                    existing_checkpoint=resume_envelope,
                )
            for update in range(start_update, stop_update):
                stage_wall = time.perf_counter()
                stage_cpu = time.process_time()
                tapes = train_tapes[update * 8 : (update + 1) * 8]
                observations, work = _project_panel(tapes, adapter_factory)
                learner_visibility_records.append(
                    observe_learner_visibility(
                        f"train-update-{update}:learner-input",
                        observations,
                        episode_count=len(tapes),
                        visible_fields=ALLOWED_LEARNER_FIELDS,
                    )
                )
                with ModelResetObserver(
                    trainer.model,
                    name=f"train-update-{update}:collect-h0",
                    records=reset_records,
                ):
                    rollout, raw_rollout, chunk_action_digest = _rollout_from_panel(
                        tapes,
                        observations,
                        trainer.model,
                        run_name=request.run_name,
                        seed=request.seed,
                    )
                with ModelResetObserver(
                    trainer.model,
                    name=f"train-update-{update}:ppo-h0",
                    records=reset_records,
                ):
                    losses = trainer.train_rollout(rollout)
                training_records = build_training_exposure_records(
                    run_name=request.run_name,
                    seed=request.seed,
                    arm=request.arm,
                    rollout_update=update,
                    rollout=rollout,
                    optimizer_steps=losses,
                )
                training_record_chunks.append(training_records)
                rollout_records.append(
                    {
                        "update_before": update,
                        "update_after": update + 1,
                        "tapes": _tape_records(tapes),
                        "raw_rollout": raw_rollout,
                        "chunk_action_uniform_digest": chunk_action_digest,
                        "adapter_work_receipt": asdict(work),
                        "counters_after": asdict(trainer.counters),
                        "model_parameter_digest_after": model_parameter_digest(trainer.model),
                        "optimizer_digest_after": _optimizer_digest(trainer),
                        "minibatch_order_digest_after": trainer.minibatch_order_digest,
                    }
                )
                train_wall_seconds += time.perf_counter() - stage_wall
                train_cpu_seconds += time.process_time() - stage_cpu
                if trainer.counters.rollout_updates in B1_CHECKPOINT_UPDATES:
                    checkpoint_and_evaluate(trainer.counters.rollout_updates)
            if trainer.counters.rollout_updates != stop_update:
                raise B1EngineError("slice stopped at an unexpected rollout update")
            slice_counts = b1_slice_counts(
                start_update, stop_update, fresh=resume_checkpoint is None
            )
            if (
                len(rollout_records) != slice_counts.rollout_updates
                or len(evaluation_records) != slice_counts.evaluation_checkpoints
            ):
                raise B1EngineError("observed slice work differs from its frozen boundaries")
            stage_measurements = build_stage_measurements(
                slice_counts,
                train_wall_seconds=train_wall_seconds,
                train_cpu_seconds=train_cpu_seconds,
                evaluation_wall_seconds=evaluation_wall_seconds,
                evaluation_cpu_seconds=evaluation_cpu_seconds,
            )
            training_records = merge_training_exposure_slices(
                training_record_chunks,
                start_update=start_update,
                stop_update=stop_update,
            )
            mechanical_direct = build_mechanical_direct(
                active_modes=active_modes,
                reset_records=reset_records,
                checkpoint_records=mechanical_checkpoint_records,
                learner_visibility_records=learner_visibility_records,
            )
            return {
                "schema": B1_RAW_EVIDENCE_SCHEMA,
                "attempt_id": request.attempt_id,
                "run_name": request.run_name,
                "arm": request.arm,
                "seed": request.seed,
                "slice": {"start_update": start_update, "stop_update": stop_update},
                "full_bindings": {
                    "train_episode_ids_sha256": _sha256_jsonable(
                        list(request.train_episode_ids)
                    ),
                    "full_training_tape_digest": full_training_tape_digest,
                    "full_action_uniform_digest": full_action_uniform_digest,
                    "ppo_configuration_digest": config_digest(trainer.config),
                    "implementation_commit": request.implementation_commit,
                    "source_conformance_sha256": request.source_conformance_sha256,
                },
                "train_tapes": _tape_records(train_tapes),
                "evaluation_tapes": _tape_records(eval_tapes),
                "rollouts": rollout_records,
                "training_records": training_records.canonical_dict(),
                "mechanical_direct": mechanical_direct,
                "checkpoints_created": checkpoint_records,
                "evaluations": evaluation_records,
                "final_counters": asdict(trainer.counters),
                "final_model_parameter_digest": model_parameter_digest(trainer.model),
                "final_optimizer_digest": _optimizer_digest(trainer),
                "final_minibatch_order_digest": trainer.minibatch_order_digest,
                "slice_counts": asdict(slice_counts),
                "scientific_work_transitions": slice_counts.scientific_work_transitions,
                "stage_measurements": stage_measurements,
                "worker_count": self.worker_count,
                "threads_per_worker": self.threads_per_worker,
                "scientific_branch": None,
            }
        finally:
            torch.set_num_threads(original_threads)


def b1_engine() -> LiteralB1ArmSeedEngine:
    """Canonical non-injectable factory for the B1 worker."""

    return LiteralB1ArmSeedEngine()


__all__ = [
    "B1_CHECKPOINT_SCHEMA",
    "B1_RAW_EVIDENCE_SCHEMA",
    "B1CheckpointBinding",
    "B1EngineError",
    "B1SliceCounts",
    "LiteralB1ArmSeedEngine",
    "audit_b1_checkpoint",
    "b1_engine",
    "b1_slice_counts",
    "b1_slice_checkpoint_updates",
    "build_stage_measurements",
    "capture_b1_checkpoint",
    "load_b1_checkpoint",
    "restore_b1_checkpoint",
    "save_b1_checkpoint",
]

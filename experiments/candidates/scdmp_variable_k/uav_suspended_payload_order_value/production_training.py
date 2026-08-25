"""Lease-bound production training for the SCDMP UAV revision-02 panel.

This module is the concrete bridge between the prospective runner contracts and
the already frozen model, HMAC, native-renewal, and PPO implementations.  It has
no command-line entry point and performs no work at import or construction
time.  Model materialization and every filesystem mutation remain behind an
active :class:`ActivityPermit`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import struct
from typing import Final, Protocol

import torch
from torch import Tensor

from .config import (
    CARD_REVISION,
    FIXTURE_NAMESPACE,
    HORIZON,
    MAX_QUERIES,
    EventOrder,
    FixtureInput,
    Regime,
)
from .frontier import CheckpointCompletion, CheckpointReceipt, LEARNED_ARMS
from .host_types import RenewalTransition
from .lease import ActivityPermit, COORDINATE_PLAN_DIGEST, canonical_digest
from .model import (
    LearnedArm,
    ModelActivityIdentityPermit,
    SCDMPUAVActorCritic,
    build_model,
    inverse_cdf_action,
)
from .native_backend import SCIENCE_CARD_SHA256, reset_native_renewal_batch
from .rng import DOMAIN_LABELS, EmpiricalRNG, sha256_hex
from .runner import BlindedFrontierHandle
from .training import (
    MAX_OPTIMIZER_STEP,
    PPO_UPDATES_PER_ARM,
    DurationCorrectPPOTrainer,
    ExactAdamW,
    freeze_update_batch,
)


_GENERATION_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_TRAINING_GENERATION_V1"
_CHECKPOINT_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_FINAL_CHECKPOINT_V1"
_POINTER_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_TRAINING_POINTER_V1"
_UPDATES: Final[int] = 144
_SLOTS: Final[int] = 12
_STEPS_PER_UPDATE: Final[int] = 16
_MAX_RENEWALS: Final[int] = HORIZON // 4


class ProductionTrainingError(RuntimeError):
    """A lease, binding, native rollout, or persistent-frontier law failed."""


def _require_hex(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ProductionTrainingError(f"{label} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ProductionTrainingError(f"{label} must be a SHA-256 digest") from error
    return value.lower()


@dataclass(frozen=True)
class TrainingSourceBindings:
    """Exact immutable identities copied from the future validated Root lease."""

    card_revision: str
    card_sha256: str
    empirical_source_manifest_sha256: str
    native_binding_digest: str

    @classmethod
    def from_lease(cls, lease: Mapping[str, object]) -> "TrainingSourceBindings":
        construction = lease.get("construction_binding")
        if not isinstance(construction, Mapping):
            raise ProductionTrainingError("lease lacks the native construction binding")
        return cls(
            card_revision=str(lease.get("card_revision", "")),
            card_sha256=str(lease.get("card_sha256", "")),
            empirical_source_manifest_sha256=str(
                lease.get("empirical_source_manifest_sha256", "")
            ),
            native_binding_digest=canonical_digest(dict(construction)),
        ).validated()

    def validated(self) -> "TrainingSourceBindings":
        if self.card_revision != CARD_REVISION:
            raise ProductionTrainingError("training card revision differs from revision 02")
        if _require_hex(self.card_sha256, "card_sha256") != SCIENCE_CARD_SHA256:
            raise ProductionTrainingError("training card SHA differs from revision 02")
        _require_hex(
            self.empirical_source_manifest_sha256,
            "empirical_source_manifest_sha256",
        )
        _require_hex(self.native_binding_digest, "native_binding_digest")
        return self

    def payload(self) -> dict[str, str]:
        self.validated()
        return {
            "card_revision": self.card_revision,
            "card_sha256": self.card_sha256,
            "empirical_source_manifest_sha256": self.empirical_source_manifest_sha256,
            "native_binding_digest": self.native_binding_digest,
        }


@dataclass(frozen=True)
class TrainingRunIdentity:
    """Original runner identity; master bytes are deliberately not retained."""

    master_digest: str
    run_identity_digest: str
    rng_address_law: str = "HMAC-SHA256/SCDMP-UAV-SP-R02-ADDRESS-v1"

    @classmethod
    def create(
        cls,
        *,
        master_digest: str,
        bindings: TrainingSourceBindings,
    ) -> "TrainingRunIdentity":
        master = _require_hex(master_digest, "master_digest")
        law = "HMAC-SHA256/SCDMP-UAV-SP-R02-ADDRESS-v1"
        identity = canonical_digest(
            {
                "schema": "SCDMP_UAV_SP_R02_RUN_IDENTITY_V1",
                "master_digest": master,
                "coordinate_plan_digest": COORDINATE_PLAN_DIGEST,
                "source_bindings": bindings.payload(),
                "rng_address_law": law,
            }
        )
        return cls(master, identity, law)

    def validated(self, bindings: TrainingSourceBindings) -> "TrainingRunIdentity":
        expected = TrainingRunIdentity.create(
            master_digest=self.master_digest, bindings=bindings
        )
        if self != expected:
            raise ProductionTrainingError("original run identity digest or RNG law differs")
        return self

    def payload(self) -> dict[str, str]:
        return {
            "master_digest": self.master_digest,
            "run_identity_digest": self.run_identity_digest,
            "rng_address_law": self.rng_address_law,
        }


@dataclass(frozen=True)
class TrainingCompletionReceipt:
    """Unaccepted slot completion returned for the external CM barrier phase."""

    replicate: int
    arm: str
    coordinate_digest: str
    checkpoint_digest: str
    checkpoint_path: str
    optimizer_step: int
    origin_lease_id: str
    master_digest: str
    run_identity_digest: str
    empirical_source_manifest_sha256: str
    card_revision: str
    card_sha256: str
    native_binding_digest: str
    technically_accepted: bool = False
    evaluation_observed: bool = False

    def validate_completion(self) -> None:
        if self.replicate not in range(18) or self.arm not in LEARNED_ARMS:
            raise ProductionTrainingError("completion receipt slot is unregistered")
        if self.coordinate_digest != COORDINATE_PLAN_DIGEST:
            raise ProductionTrainingError("completion receipt coordinate differs")
        _require_hex(self.checkpoint_digest, "checkpoint_digest")
        _require_hex(self.master_digest, "master_digest")
        _require_hex(self.run_identity_digest, "run_identity_digest")
        _require_hex(
            self.empirical_source_manifest_sha256,
            "empirical_source_manifest_sha256",
        )
        _require_hex(self.card_sha256, "card_sha256")
        _require_hex(self.native_binding_digest, "native_binding_digest")
        if self.card_revision != CARD_REVISION or self.optimizer_step != MAX_OPTIMIZER_STEP:
            raise ProductionTrainingError("completion receipt revision/optimizer step differs")
        if not self.origin_lease_id or not Path(self.checkpoint_path).is_absolute():
            raise ProductionTrainingError("completion receipt lacks provenance/path")
        if self.technically_accepted is not False or self.evaluation_observed is not False:
            raise ProductionTrainingError("training completion cannot assert acceptance/evaluation")


class RenewalBatch(Protocol):
    @property
    def active(self) -> tuple[bool, ...]: ...

    def advance(self, actions: Iterable[int | None]) -> tuple[RenewalTransition, ...]: ...

    def close(self) -> None: ...


class RenewalBatchFactory(Protocol):
    def __call__(
        self, fixtures: Iterable[FixtureInput]
    ) -> tuple[RenewalBatch, tuple[RenewalTransition, ...]]: ...


@dataclass(frozen=True)
class TrainingRenewalRecord:
    k: int
    slot: int
    renewal: int
    action: int
    realized_duration: int
    primitive_rewards: tuple[float, ...]
    terminal: bool


@dataclass(frozen=True)
class CollectedTrainingUpdate:
    observations: Tensor
    true_q: Tensor
    actions: Tensor
    primitive_rewards: tuple[tuple[float, ...], ...]
    nonterminal: Tensor
    slot_offsets: tuple[int, ...]
    records: tuple[TrainingRenewalRecord, ...]

    def validate(self) -> None:
        count = len(self.records)
        if self.observations.shape != (count, 14) or self.observations.dtype != torch.float32:
            raise ProductionTrainingError("collected observations have the wrong shape or dtype")
        if self.true_q.shape != (count,) or self.true_q.dtype != torch.float32:
            raise ProductionTrainingError("collected chronology has the wrong shape or dtype")
        if self.actions.shape != (count,) or self.actions.dtype != torch.int64:
            raise ProductionTrainingError("collected actions have the wrong shape or dtype")
        if self.nonterminal.shape != (count,) or self.nonterminal.dtype != torch.bool:
            raise ProductionTrainingError("collected terminal mask has the wrong shape or dtype")
        if len(self.primitive_rewards) != count or len(self.slot_offsets) != _SLOTS + 1:
            raise ProductionTrainingError("collected update does not contain twelve complete slots")
        if self.slot_offsets[0] != 0 or self.slot_offsets[-1] != count:
            raise ProductionTrainingError("slot offsets do not cover all renewal records")
        for start, stop in zip(self.slot_offsets, self.slot_offsets[1:]):
            if start >= stop or bool(self.nonterminal[stop - 1]):
                raise ProductionTrainingError("every training slot must be nonempty and terminal")
        for index, record in enumerate(self.records):
            if record.realized_duration != len(record.primitive_rewards):
                raise ProductionTrainingError("primitive-duration record is inconsistent")
            if record.primitive_rewards != self.primitive_rewards[index]:
                raise ProductionTrainingError("primitive reward record is inconsistent")
            if record.k not in (4, 10) or record.slot not in range(6):
                raise ProductionTrainingError("training record left the frozen slot roster")
            if record.action != int(self.actions[index]):
                raise ProductionTrainingError("training record action is inconsistent")


class _LeaseModelPermit(ModelActivityIdentityPermit):
    """Structural adapter from one validated lease/RNG to the model protocol."""

    def __init__(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        *,
        replicate: int,
        arm: str,
    ) -> None:
        permit.require_active()
        if replicate not in range(18) or arm not in LEARNED_ARMS:
            raise ProductionTrainingError("model permit slot is unregistered")
        self._permit = permit
        self._rng = rng
        self._replicate = replicate
        self._arm = arm

    def require_model_initialization(
        self,
        *,
        card_revision: str,
        replicate: int,
        arm: str,
        initialization_source: object,
    ) -> None:
        self._permit.require_active()
        if (
            card_revision != CARD_REVISION
            or replicate != self._replicate
            or arm != self._arm
            or initialization_source is not self._rng
        ):
            raise PermissionError("model initialization differs from the lease-bound slot")

    def require_training(self, *, card_revision: str, arm: str) -> None:
        self._permit.require_active()
        if card_revision != CARD_REVISION or arm != self._arm:
            raise PermissionError("training differs from the lease-bound model identity")


def _rng_identity_digest(rng: EmpiricalRNG, replicate: int) -> str:
    """Digest the complete replicate domain identity without exposing any key."""

    digest = hashlib.sha256(b"SCDMP-UAV-SP-R02-REPLICATE-IDENTITY-v1\0")
    for domain in DOMAIN_LABELS:
        encoded = domain.encode("ascii")
        digest.update(len(encoded).to_bytes(2, "big"))
        digest.update(encoded)
        digest.update(bytes.fromhex(sha256_hex(rng.for_domain(replicate, domain).key)))
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _semantic_digest(value: object) -> str:
    """Deterministic digest for nested tensor state, independent of torch ZIP bytes."""

    digest = hashlib.sha256(b"SCDMP-UAV-SP-R02-STATE-v1\0")

    def visit(item: object) -> None:
        if item is None:
            digest.update(b"n")
        elif isinstance(item, bool):
            digest.update(b"b1" if item else b"b0")
        elif isinstance(item, int):
            encoded = str(item).encode("ascii")
            digest.update(b"i" + len(encoded).to_bytes(4, "big") + encoded)
        elif isinstance(item, float):
            if not math.isfinite(item):
                raise ProductionTrainingError("persistent state contains a nonfinite float")
            digest.update(b"f" + struct.pack(">d", item))
        elif isinstance(item, str):
            encoded = item.encode("utf-8")
            digest.update(b"s" + len(encoded).to_bytes(4, "big") + encoded)
        elif isinstance(item, Tensor):
            tensor = item.detach().to("cpu").contiguous()
            if tensor.is_floating_point() and not bool(torch.isfinite(tensor).all()):
                raise ProductionTrainingError("persistent tensor state contains nonfinite values")
            dtype = str(tensor.dtype).encode("ascii")
            shape = json.dumps(list(tensor.shape), separators=(",", ":")).encode("ascii")
            digest.update(b"t" + len(dtype).to_bytes(2, "big") + dtype)
            digest.update(len(shape).to_bytes(2, "big") + shape)
            digest.update(tensor.view(torch.uint8).numpy().tobytes(order="C"))
        elif isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                raise ProductionTrainingError("persistent mapping keys must be strings")
            digest.update(b"m" + len(item).to_bytes(4, "big"))
            for key in sorted(item):
                visit(key)
                visit(item[key])
        elif isinstance(item, (tuple, list)):
            digest.update((b"q" if isinstance(item, tuple) else b"l") + len(item).to_bytes(4, "big"))
            for child in item:
                visit(child)
        else:
            raise ProductionTrainingError(
                f"unsupported persistent-state type: {type(item).__name__}"
            )

    visit(value)
    return digest.hexdigest()


def _atomic_create_torch(path: Path, payload: Mapping[str, object]) -> str:
    """Publish one immutable torch payload without ever replacing its name."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.{id(payload):x}.tmp")
    if temporary.exists():
        raise ProductionTrainingError("unexpected stale immutable-payload temporary")
    try:
        with temporary.open("xb") as stream:
            torch.save(dict(payload), stream)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ProductionTrainingError("immutable training payload already exists") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    return _sha256_file(path)


def _atomic_replace_json(path: Path, payload: Mapping[str, object]) -> None:
    """Replace only the mutable latest-generation pointer."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _load_torch(path: Path) -> dict[str, object]:
    try:
        value = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as error:
        raise ProductionTrainingError(f"persistent payload cannot be loaded: {path.name}") from error
    if not isinstance(value, dict):
        raise ProductionTrainingError("persistent torch payload must be a mapping")
    return value


def _state_payload(model: SCDMPUAVActorCritic, optimizer: ExactAdamW) -> dict[str, object]:
    model_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
    optimizer_state = optimizer.state_dict()
    return {
        "model_state": model_state,
        "model_state_digest": _semantic_digest(model_state),
        "optimizer_state": optimizer_state,
        "optimizer_state_digest": _semantic_digest(optimizer_state),
    }


class ProductionTrainingService:
    """Concrete create-frontier/train-slot/load-checkpoint runner service.

    ``result_root`` is caller supplied and is not created until an active permit
    reaches ``create_frontier`` or ``train_slot``.  Every slot has one stable,
    deterministic directory and one mutable pointer.  Generation and final
    checkpoint payload names are create-only.
    """

    def __init__(
        self,
        result_root: Path,
        *,
        bindings: TrainingSourceBindings,
        run_identity: TrainingRunIdentity | None = None,
        native_batch_factory: RenewalBatchFactory = reset_native_renewal_batch,
    ) -> None:
        self._root = Path(result_root).resolve()
        self._bindings = bindings.validated()
        self._run_identity = (
            None if run_identity is None else run_identity.validated(self._bindings)
        )
        self._native_batch_factory = native_batch_factory
        self._production_native_factory = (
            native_batch_factory is reset_native_renewal_batch
        )

    @property
    def result_root(self) -> Path:
        return self._root

    def bind_run_identity(self, run_identity: TrainingRunIdentity) -> None:
        """Bind the post-master identity once, before any frontier activity.

        Construction may remain identity-free for CLI preflight.  The
        two-phase runner calls this immediately after it durably establishes
        the original run identity and before its first ``create_frontier``.
        """

        validated = run_identity.validated(self._bindings)
        if self._run_identity is None:
            self._run_identity = validated
        elif self._run_identity != validated:
            raise ProductionTrainingError("training service run identity is already bound")

    @staticmethod
    def production_schedule() -> dict[str, object]:
        return {
            "arms": LEARNED_ARMS,
            "updates_per_arm": _UPDATES,
            "episodes_per_update": _SLOTS,
            "training_k": (4, 10),
            "episodes_per_k": 6,
            "orders_per_k": {"RG": 3, "GR": 3},
            "optimizer_steps_per_update": _STEPS_PER_UPDATE,
            "optimizer_steps_per_arm": MAX_OPTIMIZER_STEP,
            "native_renewal_abi": 2,
            "python_host_fallback": False,
            "cpu_threads": 1,
            "gpu": False,
        }

    def _slot_dir(self, replicate: int, arm: str) -> Path:
        if replicate not in range(18) or arm not in LEARNED_ARMS:
            raise ProductionTrainingError("training slot is unregistered")
        return self._root / "training" / f"replicate-{replicate:02d}" / arm

    def _generation_path(self, replicate: int, arm: str, generation: int) -> Path:
        return self._slot_dir(replicate, arm) / "generations" / f"generation-{generation:03d}.pt"

    def _checkpoint_path(self, replicate: int, arm: str) -> Path:
        return self._slot_dir(replicate, arm) / "checkpoint" / "update-144.pt"

    def _pointer_path(self, replicate: int, arm: str) -> Path:
        return self._slot_dir(replicate, arm) / "frontier.json"

    def _binding_payload(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
    ) -> dict[str, object]:
        permit.require_active()
        if self._run_identity is None:
            raise ProductionTrainingError(
                "original run identity must be explicitly bound before frontier activity"
            )
        if permit.coordinate_plan_digest != COORDINATE_PLAN_DIGEST:
            raise ProductionTrainingError("activity permit coordinate differs from revision 02")
        return {
            "coordinate_plan_digest": COORDINATE_PLAN_DIGEST,
            "replicate": replicate,
            "arm": arm,
            "run_identity": self._run_identity.payload(),
            "rng_identity_digest": _rng_identity_digest(rng, replicate),
            "source_bindings": self._bindings.payload(),
            "native_execution": "ABI-v2-reset-renew-close-batch-only",
            "python_host_fallback": False,
        }

    def _build_slot(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
    ) -> tuple[SCDMPUAVActorCritic, ExactAdamW, _LeaseModelPermit]:
        permit.require_active()
        if torch.get_num_threads() != 1:
            torch.set_num_threads(1)
        if torch.get_num_interop_threads() != 1:
            try:
                torch.set_num_interop_threads(1)
            except RuntimeError as error:
                raise ProductionTrainingError(
                    "CPU interop threads could not be fixed at one before model activity"
                ) from error
        model_permit = _LeaseModelPermit(
            permit, rng, replicate=replicate, arm=arm
        )
        model = build_model(
            LearnedArm(arm),
            permit=model_permit,
            replicate=replicate,
            initialization_source=rng,
        )
        if next(model.parameters()).device.type != "cpu":
            raise ProductionTrainingError("production training must remain CPU-only")
        optimizer = ExactAdamW(model, permit=model_permit)
        return model, optimizer, model_permit

    def _generation_payload(
        self,
        *,
        binding: Mapping[str, object],
        generation: int,
        previous_generation_digest: str | None,
        origin_lease_id: str,
        model: SCDMPUAVActorCritic,
        optimizer: ExactAdamW,
        update_record_digest: str | None,
        checkpoint_digest: str | None,
    ) -> dict[str, object]:
        if generation not in range(_UPDATES + 1):
            raise ProductionTrainingError("frontier generation lies outside update 0..144")
        expected_step = generation * _STEPS_PER_UPDATE
        if optimizer.step_index != expected_step:
            raise ProductionTrainingError("optimizer step differs from frontier generation")
        if generation == 0:
            if previous_generation_digest is not None or update_record_digest is not None:
                raise ProductionTrainingError("created frontier cannot cite training data")
        else:
            _require_hex(previous_generation_digest, "previous_generation_digest")
            _require_hex(update_record_digest, "update_record_digest")
        if generation == _UPDATES:
            _require_hex(checkpoint_digest, "checkpoint_digest")
        elif checkpoint_digest is not None:
            raise ProductionTrainingError("only update 144 may cite a checkpoint")
        if not origin_lease_id:
            raise ProductionTrainingError("frontier origin lease provenance is absent")
        return {
            "schema": _GENERATION_SCHEMA,
            "binding": dict(binding),
            "generation": generation,
            "completed_update": generation,
            "optimizer_step": expected_step,
            "previous_generation_digest": previous_generation_digest,
            "origin_lease_id": origin_lease_id,
            "update_record_digest": update_record_digest,
            "checkpoint_digest": checkpoint_digest,
            "complete_update": generation > 0,
            "partial_inspection_permitted": False,
            "scientific_endpoints_exposed": False,
            **_state_payload(model, optimizer),
        }

    def _validate_payload(
        self,
        payload: Mapping[str, object],
        *,
        schema: str,
        binding: Mapping[str, object],
        generation: int,
        origin_lease_id: str | None = None,
    ) -> None:
        if payload.get("schema") != schema or payload.get("binding") != dict(binding):
            raise ProductionTrainingError("persistent payload identity/binding differs")
        if payload.get("generation") != generation or payload.get("completed_update") != generation:
            raise ProductionTrainingError("persistent generation index differs")
        if payload.get("optimizer_step") != generation * _STEPS_PER_UPDATE:
            raise ProductionTrainingError("persistent optimizer step differs")
        if payload.get("partial_inspection_permitted") is not False:
            raise ProductionTrainingError("persistent payload permits partial inspection")
        if payload.get("scientific_endpoints_exposed") is not False:
            raise ProductionTrainingError("persistent payload exposes scientific endpoints")
        persisted_origin = payload.get("origin_lease_id")
        if not isinstance(persisted_origin, str) or not persisted_origin:
            raise ProductionTrainingError("persistent payload lacks origin lease provenance")
        if origin_lease_id is not None and persisted_origin != origin_lease_id:
            raise ProductionTrainingError("persistent origin lease provenance changed")
        model_state = payload.get("model_state")
        optimizer_state = payload.get("optimizer_state")
        if not isinstance(model_state, Mapping) or not isinstance(optimizer_state, Mapping):
            raise ProductionTrainingError("persistent payload lacks model/optimizer state")
        if _semantic_digest(model_state) != payload.get("model_state_digest"):
            raise ProductionTrainingError("persistent model state digest differs")
        if _semantic_digest(optimizer_state) != payload.get("optimizer_state_digest"):
            raise ProductionTrainingError("persistent optimizer state digest differs")

    def _read_pointer(self, replicate: int, arm: str) -> dict[str, object] | None:
        path = self._pointer_path(replicate, arm)
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text(encoding="ascii"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ProductionTrainingError("frontier pointer is unreadable") from error
        if not isinstance(value, dict) or value.get("schema") != _POINTER_SCHEMA:
            raise ProductionTrainingError("frontier pointer schema differs")
        return value

    def _write_pointer(
        self,
        *,
        replicate: int,
        arm: str,
        generation: int,
        generation_digest: str,
        binding: Mapping[str, object],
    ) -> None:
        _atomic_replace_json(
            self._pointer_path(replicate, arm),
            {
                "schema": _POINTER_SCHEMA,
                "binding_digest": canonical_digest(dict(binding)),
                "generation": generation,
                "generation_digest": _require_hex(generation_digest, "generation_digest"),
                "partial_inspection_permitted": False,
            },
        )

    def _load_latest(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
    ) -> tuple[dict[str, object], str, dict[str, object]]:
        binding = self._binding_payload(permit, rng, replicate, arm)
        pointer = self._read_pointer(replicate, arm)
        if pointer is None:
            raise ProductionTrainingError("slot frontier has not been created")
        if pointer.get("binding_digest") != canonical_digest(binding):
            raise ProductionTrainingError("frontier pointer binding differs")
        generation = pointer.get("generation")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation not in range(145):
            raise ProductionTrainingError("frontier pointer generation is invalid")
        prior_digest: str | None = None
        origin_lease_id: str | None = None
        payload: dict[str, object] | None = None
        file_digest: str | None = None
        # Resume acceptance authenticates the whole immutable chain.  Checking
        # only the pointer target would let an older model/optimizer generation
        # be altered without discovery.
        for current_generation in range(generation + 1):
            path = self._generation_path(replicate, arm, current_generation)
            if not path.is_file():
                raise ProductionTrainingError("frontier generation chain is incomplete")
            file_digest = _sha256_file(path)
            payload = _load_torch(path)
            self._validate_payload(
                payload,
                schema=_GENERATION_SCHEMA,
                binding=binding,
                generation=current_generation,
                origin_lease_id=origin_lease_id,
            )
            if origin_lease_id is None:
                origin_lease_id = str(payload["origin_lease_id"])
            if payload.get("previous_generation_digest") != prior_digest:
                raise ProductionTrainingError("frontier predecessor digest differs")
            prior_digest = file_digest
        assert payload is not None and file_digest is not None
        if file_digest != pointer.get("generation_digest"):
            raise ProductionTrainingError("frontier generation file digest differs")
        return payload, file_digest, binding

    def create_frontier(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
    ) -> BlindedFrontierHandle:
        """Create generation zero or validate/reuse the exact existing slot."""

        binding = self._binding_payload(permit, rng, replicate, arm)
        pointer = self._read_pointer(replicate, arm)
        if pointer is None:
            model, optimizer, _ = self._build_slot(permit, rng, replicate, arm)
            payload = self._generation_payload(
                binding=binding,
                generation=0,
                previous_generation_digest=None,
                origin_lease_id=permit.lease_id,
                model=model,
                optimizer=optimizer,
                update_record_digest=None,
                checkpoint_digest=None,
            )
            path = self._generation_path(replicate, arm, 0)
            if path.exists():
                # A crash may leave a complete immutable generation before its
                # pointer replacement.  Reuse only after exact semantic checks.
                existing = _load_torch(path)
                self._validate_payload(
                    existing, schema=_GENERATION_SCHEMA, binding=binding, generation=0
                )
                digest = _sha256_file(path)
            else:
                digest = _atomic_create_torch(path, payload)
            self._write_pointer(
                replicate=replicate,
                arm=arm,
                generation=0,
                generation_digest=digest,
                binding=binding,
            )
        _, digest, _ = self._load_latest(permit, rng, replicate, arm)
        return BlindedFrontierHandle(
            replicate=replicate,
            arm=arm,
            coordinate_digest=COORDINATE_PLAN_DIGEST,
            frontier_digest=digest,
            partial_inspection_permitted=False,
        )

    @staticmethod
    def _fixtures_for_update(
        rng: EmpiricalRNG, *, replicate: int, update: int
    ) -> tuple[tuple[FixtureInput, ...], tuple[tuple[int, int], ...]]:
        if update not in range(1, 145):
            raise ProductionTrainingError("training update must lie in 1..144")
        fixtures: list[FixtureInput] = []
        coordinates: list[tuple[int, int]] = []
        for k, regime in ((4, Regime.FIXED_4), (10, Regime.FIXED_10)):
            orders = rng.training_setup_order_roster(replicate, update, k)
            if sorted(orders) != ["GR"] * 3 + ["RG"] * 3:
                raise ProductionTrainingError("training order roster is not exact 3 RG / 3 GR")
            for slot, order_name in enumerate(orders):
                initial_v = 0.04 * rng.training_initial_state_uniform(
                    replicate, update, k, slot, "v"
                )
                initial_phi = -0.015 + 0.03 * rng.training_initial_state_uniform(
                    replicate, update, k, slot, "phi"
                )
                eta_v = tuple(
                    0.004
                    if rng.training_disturbance_bit(
                        replicate, update, k, slot, tick, "eta_v"
                    )
                    else -0.004
                    for tick in range(HORIZON)
                )
                eta_omega = tuple(
                    0.006
                    if rng.training_disturbance_bit(
                        replicate, update, k, slot, tick, "eta_omega"
                    )
                    else -0.006
                    for tick in range(HORIZON)
                )
                fixture = FixtureInput(
                    namespace=FIXTURE_NAMESPACE,
                    event_order=EventOrder.RG if order_name == "RG" else EventOrder.GR,
                    regime=regime,
                    switch_tick=0,
                    initial_v=initial_v,
                    initial_phi=initial_phi,
                    # ABI-v2 renewal ignores this legacy full-run tape, but the
                    # shared fixture validator requires its fixed allocation.
                    actions=(0,) * MAX_QUERIES,
                    eta_v=eta_v,
                    eta_omega=eta_omega,
                )
                fixture.validate()
                fixtures.append(fixture)
                coordinates.append((k, slot))
        if len(fixtures) != _SLOTS:
            raise ProductionTrainingError("training fixture batch must contain twelve slots")
        return tuple(fixtures), tuple(coordinates)

    def _collect_update(
        self,
        model: SCDMPUAVActorCritic,
        rng: EmpiricalRNG,
        *,
        replicate: int,
        update: int,
    ) -> CollectedTrainingUpdate:
        fixtures, coordinates = self._fixtures_for_update(
            rng, replicate=replicate, update=update
        )
        batch, surfaces = self._native_batch_factory(fixtures)
        if len(surfaces) != _SLOTS or batch.active != (True,) * _SLOTS:
            batch.close()
            raise ProductionTrainingError("native reset did not return twelve active slots")
        per_slot: list[list[tuple[tuple[float, ...], float, int, tuple[float, ...], bool]]] = [
            [] for _ in range(_SLOTS)
        ]
        renewal_indices = [0] * _SLOTS
        try:
            for _round in range(_MAX_RENEWALS):
                active = batch.active
                if not any(active):
                    break
                actions: list[int | None] = [None] * _SLOTS
                staged: dict[int, tuple[tuple[float, ...], float, int]] = {}
                for index, is_active in enumerate(active):
                    if not is_active:
                        continue
                    k, slot = coordinates[index]
                    surface = surfaces[index]
                    observation = tuple(float(value) for value in surface.public.vector())
                    q = float(surface.chronology_q)
                    observation_tensor = torch.tensor(
                        [observation], dtype=torch.float32, device="cpu"
                    )
                    q_tensor = torch.tensor([q], dtype=torch.float32, device="cpu")
                    with torch.no_grad():
                        logits = model(observation_tensor, q_tensor).logits
                        uniform = torch.tensor(
                            [
                                rng.training_action_uniform(
                                    replicate,
                                    update,
                                    k,
                                    slot,
                                    renewal_indices[index],
                                )
                            ],
                            dtype=torch.float32,
                            device="cpu",
                        )
                        action = int(inverse_cdf_action(logits, uniform).item())
                    actions[index] = action
                    staged[index] = (observation, q, action)
                next_surfaces = batch.advance(actions)
                if len(next_surfaces) != _SLOTS:
                    raise ProductionTrainingError("native renewal batch width changed")
                for index, (observation, q, action) in staged.items():
                    transition = next_surfaces[index]
                    rewards = tuple(float(value) for value in transition.primitive_rewards)
                    if (
                        transition.realized_duration != len(rewards)
                        or transition.realized_duration <= 0
                        or not all(math.isfinite(value) for value in rewards)
                    ):
                        raise ProductionTrainingError("native primitive reward/duration record differs")
                    per_slot[index].append(
                        (observation, q, action, rewards, transition.terminal)
                    )
                    renewal_indices[index] += 1
                surfaces = next_surfaces
            if any(batch.active):
                raise ProductionTrainingError("native training slot exceeded the fixed renewal ceiling")
        finally:
            batch.close()

        observations: list[tuple[float, ...]] = []
        true_q: list[float] = []
        actions_flat: list[int] = []
        rewards_flat: list[tuple[float, ...]] = []
        nonterminal: list[bool] = []
        records: list[TrainingRenewalRecord] = []
        offsets = [0]
        for index, slot_records in enumerate(per_slot):
            if not slot_records or slot_records[-1][-1] is not True:
                raise ProductionTrainingError("native training slot did not terminate")
            k, slot = coordinates[index]
            for renewal, (observation, q, action, rewards, terminal) in enumerate(slot_records):
                observations.append(observation)
                true_q.append(q)
                actions_flat.append(action)
                rewards_flat.append(rewards)
                nonterminal.append(not terminal)
                records.append(
                    TrainingRenewalRecord(
                        k=k,
                        slot=slot,
                        renewal=renewal,
                        action=action,
                        realized_duration=len(rewards),
                        primitive_rewards=rewards,
                        terminal=terminal,
                    )
                )
            offsets.append(len(records))
        result = CollectedTrainingUpdate(
            observations=torch.tensor(observations, dtype=torch.float32, device="cpu"),
            true_q=torch.tensor(true_q, dtype=torch.float32, device="cpu"),
            actions=torch.tensor(actions_flat, dtype=torch.int64, device="cpu"),
            primitive_rewards=tuple(rewards_flat),
            nonterminal=torch.tensor(nonterminal, dtype=torch.bool, device="cpu"),
            slot_offsets=tuple(offsets),
            records=tuple(records),
        )
        result.validate()
        return result

    @staticmethod
    def _record_digest(update: CollectedTrainingUpdate) -> str:
        payload = [
            {
                "k": record.k,
                "slot": record.slot,
                "renewal": record.renewal,
                "action": record.action,
                "realized_duration": record.realized_duration,
                "primitive_reward_bits": [
                    struct.pack(">d", value).hex() for value in record.primitive_rewards
                ],
                "terminal": record.terminal,
            }
            for record in update.records
        ]
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest()

    def _restore_slot(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
        payload: Mapping[str, object],
    ) -> tuple[SCDMPUAVActorCritic, ExactAdamW, _LeaseModelPermit]:
        model, optimizer, model_permit = self._build_slot(
            permit, rng, replicate, arm
        )
        try:
            model.load_state_dict(payload["model_state"], strict=True)
            optimizer.load_state_dict(dict(payload["optimizer_state"]))
        except Exception as error:
            raise ProductionTrainingError("frontier model/optimizer restore failed") from error
        if optimizer.step_index != int(payload["optimizer_step"]):
            raise ProductionTrainingError("restored optimizer step differs")
        return model, optimizer, model_permit

    def _checkpoint_payload(
        self,
        *,
        binding: Mapping[str, object],
        origin_lease_id: str,
        model: SCDMPUAVActorCritic,
        optimizer: ExactAdamW,
    ) -> dict[str, object]:
        if optimizer.step_index != MAX_OPTIMIZER_STEP:
            raise ProductionTrainingError("only optimizer step 2304 is checkpoint-eligible")
        return {
            "schema": _CHECKPOINT_SCHEMA,
            "binding": dict(binding),
            "generation": _UPDATES,
            "completed_update": _UPDATES,
            "optimizer_step": MAX_OPTIMIZER_STEP,
            "origin_lease_id": origin_lease_id,
            "partial_inspection_permitted": False,
            "scientific_endpoints_exposed": False,
            **_state_payload(model, optimizer),
        }

    def _create_or_validate_checkpoint(
        self,
        *,
        permit: ActivityPermit,
        replicate: int,
        arm: str,
        binding: Mapping[str, object],
        origin_lease_id: str,
        model: SCDMPUAVActorCritic,
        optimizer: ExactAdamW,
    ) -> str:
        permit.require_active()
        path = self._checkpoint_path(replicate, arm)
        candidate = self._checkpoint_payload(
            binding=binding,
            origin_lease_id=origin_lease_id,
            model=model,
            optimizer=optimizer,
        )
        if path.exists():
            existing = _load_torch(path)
            self._validate_payload(
                existing,
                schema=_CHECKPOINT_SCHEMA,
                binding=binding,
                generation=_UPDATES,
                origin_lease_id=origin_lease_id,
            )
            if (
                existing.get("model_state_digest") != candidate["model_state_digest"]
                or existing.get("optimizer_state_digest")
                != candidate["optimizer_state_digest"]
            ):
                raise ProductionTrainingError("existing final checkpoint differs from exact replay")
            return _sha256_file(path)
        return _atomic_create_torch(path, candidate)

    def _completion_receipt(
        self,
        *,
        replicate: int,
        arm: str,
        checkpoint_digest: str,
        origin_lease_id: str,
    ) -> TrainingCompletionReceipt:
        if self._run_identity is None:
            raise ProductionTrainingError("training completion lacks a bound run identity")
        receipt = TrainingCompletionReceipt(
            replicate=replicate,
            arm=arm,
            coordinate_digest=COORDINATE_PLAN_DIGEST,
            checkpoint_digest=checkpoint_digest,
            checkpoint_path=str(self._checkpoint_path(replicate, arm).resolve()),
            optimizer_step=MAX_OPTIMIZER_STEP,
            origin_lease_id=origin_lease_id,
            master_digest=self._run_identity.master_digest,
            run_identity_digest=self._run_identity.run_identity_digest,
            empirical_source_manifest_sha256=(
                self._bindings.empirical_source_manifest_sha256
            ),
            card_revision=self._bindings.card_revision,
            card_sha256=self._bindings.card_sha256,
            native_binding_digest=self._bindings.native_binding_digest,
            technically_accepted=False,
            evaluation_observed=False,
        )
        receipt.validate_completion()
        return receipt

    def validate_checkpoint_completion(
        self,
        completion: CheckpointCompletion,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        run_identity_digest: str,
    ) -> None:
        """Read-only CM predicate for one adapter completion payload.

        This authenticates the factual completion and its complete immutable
        training chain.  It never constructs a model, evaluates a policy,
        interprets an endpoint, or writes technical acceptance.
        """

        permit.require_active()
        expected_runner_identity = _require_hex(
            run_identity_digest, "run_identity_digest"
        )
        if not isinstance(completion, CheckpointCompletion):
            raise ProductionTrainingError("checkpoint completion type differs")
        if permit.source_manifest_sha256 != self._bindings.empirical_source_manifest_sha256:
            raise ProductionTrainingError("completion permit source manifest differs")
        if permit.card_sha256 != self._bindings.card_sha256:
            raise ProductionTrainingError("completion permit card binding differs")
        if permit.native_binding_digest != self._bindings.native_binding_digest:
            raise ProductionTrainingError("completion permit native binding differs")
        completion.validate(result_root=self._root, verify_checkpoint=True)
        if completion.run_identity_digest != expected_runner_identity:
            raise ProductionTrainingError("completion runner identity differs")
        if completion.coordinate_digest != permit.coordinate_plan_digest:
            raise ProductionTrainingError("completion permit coordinate differs")
        expected_checkpoint_path = self._checkpoint_path(
            completion.replicate, completion.arm
        ).resolve()
        expected_completion_path = (
            self._root
            / "checkpoint-completions"
            / f"replicate-{completion.replicate:02d}-{completion.arm}.json"
        ).resolve()
        if Path(completion.checkpoint_path).resolve() != expected_checkpoint_path:
            raise ProductionTrainingError("completion checkpoint path differs")
        if Path(completion.completion_payload_path).resolve() != expected_completion_path:
            raise ProductionTrainingError("adapter completion payload path differs")

        try:
            raw_completion = expected_completion_path.read_bytes()
            completion_payload = json.loads(raw_completion.decode("ascii"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProductionTrainingError("adapter completion payload is unreadable") from error
        if not isinstance(completion_payload, Mapping):
            raise ProductionTrainingError("adapter completion payload must be a mapping")
        exact_keys = {
            "schema",
            "replicate",
            "arm",
            "coordinate_digest",
            "run_identity_digest",
            "checkpoint_path",
            "checkpoint_digest",
            "optimizer_step",
            "origin_lease_id",
            "empirical_source_manifest_sha256",
            "card_revision",
            "card_sha256",
            "native_binding_digest",
            "technically_accepted",
            "evaluation_observed",
        }
        if set(completion_payload) != exact_keys:
            raise ProductionTrainingError("adapter completion payload schema differs")
        exact_values = {
            "schema": "SCDMP_UAV_SP_R02_CHECKPOINT_COMPLETION_V1",
            "replicate": completion.replicate,
            "arm": completion.arm,
            "coordinate_digest": COORDINATE_PLAN_DIGEST,
            "run_identity_digest": expected_runner_identity,
            "checkpoint_path": str(expected_checkpoint_path),
            "checkpoint_digest": completion.checkpoint_digest,
            "optimizer_step": MAX_OPTIMIZER_STEP,
            "empirical_source_manifest_sha256": (
                self._bindings.empirical_source_manifest_sha256
            ),
            "card_revision": self._bindings.card_revision,
            "card_sha256": self._bindings.card_sha256,
            "native_binding_digest": self._bindings.native_binding_digest,
            "technically_accepted": False,
            "evaluation_observed": False,
        }
        for field, expected in exact_values.items():
            if completion_payload.get(field) != expected:
                raise ProductionTrainingError(
                    f"adapter completion payload field {field!r} differs"
                )
        origin_lease_id = completion_payload.get("origin_lease_id")
        if not isinstance(origin_lease_id, str) or not origin_lease_id:
            raise ProductionTrainingError("adapter completion origin lease is absent")
        if hashlib.sha256(raw_completion).hexdigest() != completion.completion_payload_digest:
            raise ProductionTrainingError("adapter completion payload digest differs")

        latest, _, binding = self._load_latest(
            permit, rng, completion.replicate, completion.arm
        )
        if (
            latest.get("generation") != _UPDATES
            or latest.get("optimizer_step") != MAX_OPTIMIZER_STEP
            or latest.get("origin_lease_id") != origin_lease_id
            or latest.get("checkpoint_digest") != completion.checkpoint_digest
        ):
            raise ProductionTrainingError("final frontier differs from completion")
        checkpoint_payload = _load_torch(expected_checkpoint_path)
        self._validate_payload(
            checkpoint_payload,
            schema=_CHECKPOINT_SCHEMA,
            binding=binding,
            generation=_UPDATES,
            origin_lease_id=origin_lease_id,
        )
        if (
            checkpoint_payload.get("model_state_digest")
            != latest.get("model_state_digest")
            or checkpoint_payload.get("optimizer_state_digest")
            != latest.get("optimizer_state_digest")
        ):
            raise ProductionTrainingError(
                "final checkpoint state differs from final frontier generation"
            )

    def checkpoint_completion_validator(
        self,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        run_identity_digest: str,
    ) -> Callable[[CheckpointCompletion], None]:
        """Return the exact unary validator required by CM acceptance."""

        permit.require_active()
        expected = _require_hex(run_identity_digest, "run_identity_digest")
        # Validate the service/run/source/RNG binding before authority code can
        # iterate the completion inventory.
        if self._run_identity is None:
            raise ProductionTrainingError("completion validator lacks bound run identity")

        def validate(completion: CheckpointCompletion) -> None:
            self.validate_checkpoint_completion(
                completion,
                permit=permit,
                rng=rng,
                run_identity_digest=expected,
            )

        return validate

    def train_slot(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        frontier: BlindedFrontierHandle,
    ) -> TrainingCompletionReceipt:
        """Resume and complete exactly updates 1..144 for one learned-arm slot."""

        permit.require_active()
        if not self._production_native_factory:
            raise ProductionTrainingError(
                "synthetic renewal dependencies are test-only and cannot train a slot"
            )
        frontier.validate()
        replicate, arm = frontier.replicate, frontier.arm
        latest, latest_digest, binding = self._load_latest(
            permit, rng, replicate, arm
        )
        if latest_digest != frontier.frontier_digest:
            raise ProductionTrainingError("runner frontier handle is stale or cross-wired")
        generation = int(latest["generation"])
        if generation == _UPDATES:
            checkpoint_digest = _require_hex(
                latest.get("checkpoint_digest"), "checkpoint_digest"
            )
            checkpoint_path = self._checkpoint_path(replicate, arm)
            if not checkpoint_path.is_file() or _sha256_file(checkpoint_path) != checkpoint_digest:
                raise ProductionTrainingError("final frontier checkpoint digest differs")
            return self._completion_receipt(
                replicate=replicate,
                arm=arm,
                checkpoint_digest=checkpoint_digest,
                origin_lease_id=str(latest["origin_lease_id"]),
            )

        model, optimizer, model_permit = self._restore_slot(
            permit, rng, replicate, arm, latest
        )
        trainer = DurationCorrectPPOTrainer(
            model, permit=model_permit, optimizer=optimizer
        )
        previous_digest = latest_digest
        origin_lease_id = str(latest["origin_lease_id"])
        for update_index in range(generation + 1, _UPDATES + 1):
            permit.require_active()
            collected = self._collect_update(
                model, rng, replicate=replicate, update=update_index
            )
            frozen = freeze_update_batch(
                model,
                observations=collected.observations,
                true_q=collected.true_q,
                actions=collected.actions,
                primitive_rewards=collected.primitive_rewards,
                nonterminal=collected.nonterminal,
                slot_offsets=collected.slot_offsets,
            )
            steps = trainer.train_update(
                frozen,
                replicate=replicate,
                update=update_index,
                permutations=rng,
            )
            if (
                len(steps) != _STEPS_PER_UPDATE
                or optimizer.step_index != update_index * _STEPS_PER_UPDATE
            ):
                raise ProductionTrainingError("PPO update/optimizer step count differs")
            checkpoint_digest: str | None = None
            if update_index == _UPDATES:
                checkpoint_digest = self._create_or_validate_checkpoint(
                    permit=permit,
                    replicate=replicate,
                    arm=arm,
                    binding=binding,
                    origin_lease_id=origin_lease_id,
                    model=model,
                    optimizer=optimizer,
                )
            generation_payload = self._generation_payload(
                binding=binding,
                generation=update_index,
                previous_generation_digest=previous_digest,
                origin_lease_id=origin_lease_id,
                model=model,
                optimizer=optimizer,
                update_record_digest=self._record_digest(collected),
                checkpoint_digest=checkpoint_digest,
            )
            generation_path = self._generation_path(
                replicate, arm, update_index
            )
            if generation_path.exists():
                existing = _load_torch(generation_path)
                self._validate_payload(
                    existing,
                    schema=_GENERATION_SCHEMA,
                    binding=binding,
                    generation=update_index,
                )
                if (
                    existing.get("previous_generation_digest") != previous_digest
                    or existing.get("model_state_digest")
                    != generation_payload["model_state_digest"]
                    or existing.get("optimizer_state_digest")
                    != generation_payload["optimizer_state_digest"]
                    or existing.get("update_record_digest")
                    != generation_payload["update_record_digest"]
                    or existing.get("checkpoint_digest") != checkpoint_digest
                ):
                    raise ProductionTrainingError("orphan generation differs from exact replay")
                current_digest = _sha256_file(generation_path)
            else:
                current_digest = _atomic_create_torch(
                    generation_path, generation_payload
                )
            self._write_pointer(
                replicate=replicate,
                arm=arm,
                generation=update_index,
                generation_digest=current_digest,
                binding=binding,
            )
            previous_digest = current_digest

        final, final_digest, _ = self._load_latest(permit, rng, replicate, arm)
        if int(final["generation"]) != _UPDATES or final_digest != previous_digest:
            raise ProductionTrainingError("training did not install the exact final frontier")
        checkpoint_digest = _require_hex(final.get("checkpoint_digest"), "checkpoint_digest")
        return self._completion_receipt(
            replicate=replicate,
            arm=arm,
            checkpoint_digest=checkpoint_digest,
            origin_lease_id=origin_lease_id,
        )

    def load_final_model(
        self,
        *,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
        checkpoint_receipt: CheckpointReceipt,
    ) -> SCDMPUAVActorCritic:
        """Load one exact final model for evaluation after receipt/barrier checks."""

        permit.require_active()
        checkpoint_receipt.validate()
        if (checkpoint_receipt.replicate, checkpoint_receipt.arm) != (replicate, arm):
            raise ProductionTrainingError("checkpoint receipt belongs to a different slot")
        binding = self._binding_payload(permit, rng, replicate, arm)
        path = self._checkpoint_path(replicate, arm)
        if not path.is_file():
            raise ProductionTrainingError("final checkpoint is missing")
        digest = _sha256_file(path)
        if digest != checkpoint_receipt.checkpoint_digest:
            raise ProductionTrainingError("checkpoint receipt digest differs from payload")
        payload = _load_torch(path)
        self._validate_payload(
            payload,
            schema=_CHECKPOINT_SCHEMA,
            binding=binding,
            generation=_UPDATES,
        )
        model, optimizer, _ = self._restore_slot(
            permit, rng, replicate, arm, payload
        )
        if optimizer.step_index != MAX_OPTIMIZER_STEP:
            raise ProductionTrainingError("final checkpoint optimizer is incomplete")
        model.eval()
        return model


__all__ = [
    "CollectedTrainingUpdate",
    "ProductionTrainingError",
    "ProductionTrainingService",
    "RenewalBatch",
    "RenewalBatchFactory",
    "TrainingRenewalRecord",
    "TrainingCompletionReceipt",
    "TrainingRunIdentity",
    "TrainingSourceBindings",
]

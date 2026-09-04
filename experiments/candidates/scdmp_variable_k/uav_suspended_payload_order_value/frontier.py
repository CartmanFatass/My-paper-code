"""Blinded create-only frontier and global checkpoint-barrier contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Final, Iterable, Mapping

from .lease import ActivityPermit, COORDINATE_PLAN_DIGEST, path_is_within_root


LEARNED_ARMS: Final[tuple[str, ...]] = ("TREAT", "FREE", "SET")
REQUIRED_SLOTS: Final[frozenset[tuple[int, str]]] = frozenset(
    (replicate, arm) for replicate in range(18) for arm in LEARNED_ARMS
)


class FrontierContractError(RuntimeError):
    pass


def _hex_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise FrontierContractError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise FrontierContractError(f"{field} must be a SHA-256 hex digest") from error
    return value.lower()


@dataclass(frozen=True)
class FrontierSpec:
    replicate: int
    arm: str
    coordinate_digest: str
    generation: int
    previous_generation_digest: str | None
    state: str
    checkpoint_digest: str | None
    optimizer_step: int
    partial_inspection_permitted: bool = False
    scientific_values_exposed: bool = False

    def validate(self) -> None:
        if isinstance(self.replicate, bool) or self.replicate not in range(18):
            raise FrontierContractError("frontier replicate must lie in [0,18)")
        if self.arm not in LEARNED_ARMS:
            raise FrontierContractError("frontier arm is not registered")
        _hex_digest(self.coordinate_digest, "coordinate_digest")
        if self.coordinate_digest != COORDINATE_PLAN_DIGEST:
            raise FrontierContractError("frontier coordinate digest differs from the frozen proposal")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 0:
            raise FrontierContractError("frontier generation must be nonnegative")
        if self.generation == 0 and self.previous_generation_digest is not None:
            raise FrontierContractError("initial frontier cannot cite a predecessor")
        if self.generation > 0:
            _hex_digest(self.previous_generation_digest, "previous_generation_digest")
        if self.state not in ("CREATED", "TRAINING", "FINAL_CHECKPOINT"):
            raise FrontierContractError("frontier state is not registered")
        if isinstance(self.optimizer_step, bool) or not isinstance(self.optimizer_step, int):
            raise FrontierContractError("optimizer_step must be an integer")
        if not 0 <= self.optimizer_step <= 2_304:
            raise FrontierContractError("optimizer_step lies outside the frozen arm budget")
        if self.state == "FINAL_CHECKPOINT":
            if self.optimizer_step != 2_304:
                raise FrontierContractError("only optimizer step 2304 is checkpoint-eligible")
            _hex_digest(self.checkpoint_digest, "checkpoint_digest")
        elif self.checkpoint_digest is not None:
            raise FrontierContractError("nonfinal frontier cannot expose a checkpoint digest")
        if self.partial_inspection_permitted is not False or self.scientific_values_exposed is not False:
            raise FrontierContractError("frontier must remain blinded")

    def payload(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": "SCDMP_UAV_SP_R02_BLINDED_FRONTIER_V1",
            "replicate": self.replicate,
            "arm": self.arm,
            "coordinate_digest": self.coordinate_digest,
            "generation": self.generation,
            "previous_generation_digest": self.previous_generation_digest,
            "state": self.state,
            "checkpoint_digest": self.checkpoint_digest,
            "optimizer_step": self.optimizer_step,
            "partial_inspection_permitted": False,
            "scientific_values_exposed": False,
        }


def frontier_digest(spec: FrontierSpec) -> str:
    payload = json.dumps(
        spec.payload(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def create_frontier(path: Path, spec: FrontierSpec, permit: ActivityPermit) -> str:
    """Create one immutable generation; existing paths are never replaced."""

    permit.require_active()
    payload = spec.payload()
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    try:
        with target.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as error:
        raise FrontierContractError("frontier generations are create-only") from error
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CheckpointReceipt:
    replicate: int
    arm: str
    coordinate_digest: str
    checkpoint_digest: str
    optimizer_step: int
    technically_accepted: bool
    evaluation_observed: bool = False

    def validate(self) -> None:
        if (self.replicate, self.arm) not in REQUIRED_SLOTS:
            raise FrontierContractError("checkpoint receipt slot is unregistered")
        if self.coordinate_digest != COORDINATE_PLAN_DIGEST:
            raise FrontierContractError("checkpoint receipt coordinate changed")
        _hex_digest(self.checkpoint_digest, "checkpoint_digest")
        if self.optimizer_step != 2_304:
            raise FrontierContractError("only final optimizer step 2304 is accepted")
        if self.technically_accepted is not True:
            raise FrontierContractError("checkpoint lacks technical acceptance")
        if self.evaluation_observed is not False:
            raise FrontierContractError("checkpoint acceptance followed premature evaluation")


@dataclass(frozen=True)
class CheckpointCompletion:
    """Operator-owned final checkpoint fact; never technical acceptance."""

    replicate: int
    arm: str
    coordinate_digest: str
    run_identity_digest: str
    checkpoint_path: str
    checkpoint_digest: str
    completion_payload_path: str
    completion_payload_digest: str
    optimizer_step: int = 2_304
    technically_accepted: bool = False
    evaluation_observed: bool = False

    def validate(self, *, result_root: Path, verify_checkpoint: bool = True) -> None:
        if (self.replicate, self.arm) not in REQUIRED_SLOTS:
            raise FrontierContractError("checkpoint completion slot is unregistered")
        if self.coordinate_digest != COORDINATE_PLAN_DIGEST:
            raise FrontierContractError("checkpoint completion coordinate changed")
        _hex_digest(self.run_identity_digest, "run_identity_digest")
        _hex_digest(self.checkpoint_digest, "checkpoint_digest")
        _hex_digest(self.completion_payload_digest, "completion_payload_digest")
        if self.optimizer_step != 2_304:
            raise FrontierContractError("checkpoint completion is not final step 2304")
        if self.technically_accepted is not False or self.evaluation_observed is not False:
            raise FrontierContractError("training completion cannot self-accept or observe evaluation")
        root = result_root.resolve()
        paths = (
            (self.checkpoint_path, self.checkpoint_digest, "checkpoint"),
            (self.completion_payload_path, self.completion_payload_digest, "completion payload"),
        )
        for raw_path, expected_digest, label in paths:
            path = Path(raw_path)
            if not path.is_absolute():
                raise FrontierContractError(f"{label} path must be absolute")
            resolved = path.resolve()
            if not path_is_within_root(resolved, root, allow_equal=False):
                raise FrontierContractError(f"{label} path escapes result_root")
            if verify_checkpoint:
                if not resolved.is_file():
                    raise FrontierContractError(f"completed {label} file is missing")
                if hashlib.sha256(resolved.read_bytes()).hexdigest() != expected_digest:
                    raise FrontierContractError(f"completed {label} file digest changed")

    def payload(self) -> dict[str, object]:
        return {
            "replicate": self.replicate,
            "arm": self.arm,
            "coordinate_digest": self.coordinate_digest,
            "run_identity_digest": self.run_identity_digest,
            "checkpoint_path": self.checkpoint_path,
            "checkpoint_digest": self.checkpoint_digest,
            "completion_payload_path": self.completion_payload_path,
            "completion_payload_digest": self.completion_payload_digest,
            "optimizer_step": self.optimizer_step,
            "technically_accepted": False,
            "evaluation_observed": False,
        }


def _atomic_create_json(path: Path, payload: Mapping[str, object]) -> str:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    temporary = Path(str(target) + f".{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise FrontierContractError("inventory target is create-only") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(encoded).hexdigest()


def completion_inventory_payload(
    completions: Iterable[CheckpointCompletion],
    *,
    run_identity_digest: str,
    source_manifest_sha256: str,
) -> dict[str, object]:
    _hex_digest(run_identity_digest, "run_identity_digest")
    _hex_digest(source_manifest_sha256, "source_manifest_sha256")
    values = tuple(completions)
    if len(values) != 54:
        raise FrontierContractError("training completion inventory requires exactly 54 slots")
    slots = [(item.replicate, item.arm) for item in values]
    if len(set(slots)) != 54 or set(slots) != REQUIRED_SLOTS:
        raise FrontierContractError("training completion slots are duplicate, missing, or extra")
    ordered = sorted(values, key=lambda item: (item.replicate, LEARNED_ARMS.index(item.arm)))
    if any(item.run_identity_digest != run_identity_digest for item in ordered):
        raise FrontierContractError("training completion run identity differs")
    return {
        "schema": "SCDMP_UAV_SP_R02_CHECKPOINT_COMPLETION_INVENTORY_V1",
        "coordinate_digest": COORDINATE_PLAN_DIGEST,
        "run_identity_digest": run_identity_digest,
        "source_manifest_sha256": source_manifest_sha256,
        "slot_count": 54,
        "technically_accepted": False,
        "evaluation_observed": False,
        "partial_inspection_permitted": False,
        "completions": [item.payload() for item in ordered],
    }


def publish_completion_inventory(
    path: Path,
    completions: Iterable[CheckpointCompletion],
    *,
    run_identity_digest: str,
    source_manifest_sha256: str,
) -> str:
    return _atomic_create_json(
        path,
        completion_inventory_payload(
            completions,
            run_identity_digest=run_identity_digest,
            source_manifest_sha256=source_manifest_sha256,
        ),
    )


def load_completion_inventory(
    path: Path,
    *,
    result_root: Path,
    run_identity_digest: str,
    source_manifest_sha256: str,
) -> tuple[CheckpointCompletion, ...]:
    try:
        value = json.loads(path.resolve().read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FrontierContractError("checkpoint completion inventory cannot be read") from error
    if not isinstance(value, Mapping) or value.get("schema") != "SCDMP_UAV_SP_R02_CHECKPOINT_COMPLETION_INVENTORY_V1":
        raise FrontierContractError("checkpoint completion inventory schema differs")
    rows = value.get("completions")
    if not isinstance(rows, list):
        raise FrontierContractError("checkpoint completion rows are absent")
    try:
        completions = tuple(CheckpointCompletion(**dict(row)) for row in rows)
    except (TypeError, ValueError) as error:
        raise FrontierContractError("checkpoint completion row schema differs") from error
    expected = completion_inventory_payload(
        completions,
        run_identity_digest=run_identity_digest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if dict(value) != expected:
        raise FrontierContractError("checkpoint completion inventory payload differs")
    for item in completions:
        item.validate(result_root=result_root, verify_checkpoint=True)
    return completions


@dataclass(frozen=True, repr=False)
class CMTechnicalAcceptanceAuthority:
    owner: str
    _seal: object | None = None


_CM_ACCEPTANCE_SEAL: Final[object] = object()


def _cm_authority(owner: str) -> CMTechnicalAcceptanceAuthority:
    """Private constructor for the owning CM; production modules never import it."""

    return CMTechnicalAcceptanceAuthority(owner=owner, _seal=_CM_ACCEPTANCE_SEAL)


def cm_create_technical_acceptance(
    *,
    authority: CMTechnicalAcceptanceAuthority,
    completion_inventory_path: Path,
    acceptance_path: Path,
    result_root: Path,
    run_identity_digest: str,
    source_manifest_sha256: str,
    payload_validator: Callable[[CheckpointCompletion], None],
) -> str:
    if authority._seal is not _CM_ACCEPTANCE_SEAL or not authority.owner.startswith("CM_"):
        raise FrontierContractError("CM technical-acceptance authority is required")
    completions = load_completion_inventory(
        completion_inventory_path,
        result_root=result_root,
        run_identity_digest=run_identity_digest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if not callable(payload_validator):
        raise FrontierContractError("CM checkpoint/completion payload validator is required")
    for item in completions:
        payload_validator(item)
    receipts = tuple(
        CheckpointReceipt(
            replicate=item.replicate,
            arm=item.arm,
            coordinate_digest=item.coordinate_digest,
            checkpoint_digest=item.checkpoint_digest,
            optimizer_step=item.optimizer_step,
            technically_accepted=True,
            evaluation_observed=False,
        )
        for item in completions
    )
    barrier = require_global_checkpoint_barrier(receipts)
    completion_sha = hashlib.sha256(completion_inventory_path.resolve().read_bytes()).hexdigest()
    payload = {
        "schema": "SCDMP_UAV_SP_R02_CM_CHECKPOINT_ACCEPTANCE_V1",
        "cm_owner": authority.owner,
        "coordinate_digest": COORDINATE_PLAN_DIGEST,
        "run_identity_digest": run_identity_digest,
        "source_manifest_sha256": source_manifest_sha256,
        "completion_inventory_sha256": completion_sha,
        "accepted_slots": 54,
        "checkpoint_inventory_digest": barrier.checkpoint_inventory_digest,
        "technically_accepted": True,
        "evaluation_observed": False,
        "receipts": [
            {
                "replicate": item.replicate,
                "arm": item.arm,
                "coordinate_digest": item.coordinate_digest,
                "checkpoint_digest": item.checkpoint_digest,
                "optimizer_step": item.optimizer_step,
                "technically_accepted": True,
                "evaluation_observed": False,
            }
            for item in receipts
        ],
    }
    return _atomic_create_json(acceptance_path, payload)


def load_cm_technical_acceptance(
    path: Path,
    *,
    completion_inventory_path: Path,
    run_identity_digest: str,
    source_manifest_sha256: str,
) -> tuple[tuple[CheckpointReceipt, ...], GlobalCheckpointBarrier]:
    try:
        value = json.loads(path.resolve().read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FrontierContractError("CM acceptance inventory cannot be read") from error
    if not isinstance(value, Mapping) or value.get("schema") != "SCDMP_UAV_SP_R02_CM_CHECKPOINT_ACCEPTANCE_V1":
        raise FrontierContractError("CM acceptance inventory schema differs")
    if value.get("technically_accepted") is not True or value.get("evaluation_observed") is not False:
        raise FrontierContractError("CM acceptance state differs")
    if value.get("run_identity_digest") != run_identity_digest or value.get("source_manifest_sha256") != source_manifest_sha256:
        raise FrontierContractError("CM acceptance binding differs")
    completion_sha = hashlib.sha256(completion_inventory_path.resolve().read_bytes()).hexdigest()
    if value.get("completion_inventory_sha256") != completion_sha:
        raise FrontierContractError("CM acceptance cites a different completion inventory")
    rows = value.get("receipts")
    if not isinstance(rows, list):
        raise FrontierContractError("CM acceptance receipts are absent")
    try:
        receipts = tuple(CheckpointReceipt(**dict(row)) for row in rows)
    except (TypeError, ValueError) as error:
        raise FrontierContractError("CM acceptance receipt schema differs") from error
    barrier = require_global_checkpoint_barrier(receipts)
    if value.get("checkpoint_inventory_digest") != barrier.checkpoint_inventory_digest:
        raise FrontierContractError("CM acceptance checkpoint inventory digest differs")
    return receipts, barrier


@dataclass(frozen=True)
class GlobalCheckpointBarrier:
    coordinate_digest: str
    accepted_slots: int
    checkpoint_inventory_digest: str
    evaluation_open: bool
    partial_inspection_permitted: bool = False


def require_global_checkpoint_barrier(
    receipts: Iterable[CheckpointReceipt],
) -> GlobalCheckpointBarrier:
    values = tuple(receipts)
    if len(values) != 54:
        raise FrontierContractError("evaluation requires exactly 54 checkpoint receipts")
    for receipt in values:
        receipt.validate()
    slots = tuple((item.replicate, item.arm) for item in values)
    if len(set(slots)) != 54 or set(slots) != REQUIRED_SLOTS:
        raise FrontierContractError("checkpoint receipt slots are duplicate, missing, or extra")
    canonical = [
        {
            "replicate": item.replicate,
            "arm": item.arm,
            "coordinate_digest": item.coordinate_digest,
            "checkpoint_digest": item.checkpoint_digest,
            "optimizer_step": item.optimizer_step,
            "technically_accepted": item.technically_accepted,
            "evaluation_observed": item.evaluation_observed,
        }
        for item in sorted(values, key=lambda item: (item.replicate, LEARNED_ARMS.index(item.arm)))
    ]
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return GlobalCheckpointBarrier(
        coordinate_digest=COORDINATE_PLAN_DIGEST,
        accepted_slots=54,
        checkpoint_inventory_digest=digest,
        evaluation_open=True,
        partial_inspection_permitted=False,
    )


def validate_resume_chain(generations: Iterable[Mapping[str, object]]) -> None:
    """Validate an immutable same-slot, same-coordinate generation chain."""

    rows = tuple(generations)
    if not rows:
        raise FrontierContractError("resume chain is empty")
    prior_digest: str | None = None
    slot: tuple[int, str] | None = None
    for index, row in enumerate(rows):
        required = {
            "schema", "replicate", "arm", "coordinate_digest", "generation",
            "previous_generation_digest", "state", "checkpoint_digest", "optimizer_step",
            "partial_inspection_permitted", "scientific_values_exposed",
        }
        if set(row) != required or row.get("schema") != "SCDMP_UAV_SP_R02_BLINDED_FRONTIER_V1":
            raise FrontierContractError("resume frontier schema differs")
        spec = FrontierSpec(
            replicate=int(row["replicate"]),
            arm=str(row["arm"]),
            coordinate_digest=str(row["coordinate_digest"]),
            generation=int(row["generation"]),
            previous_generation_digest=row["previous_generation_digest"],
            state=str(row["state"]),
            checkpoint_digest=row["checkpoint_digest"],
            optimizer_step=int(row["optimizer_step"]),
            partial_inspection_permitted=bool(row["partial_inspection_permitted"]),
            scientific_values_exposed=bool(row["scientific_values_exposed"]),
        )
        spec.validate()
        current_slot = (spec.replicate, spec.arm)
        if slot is None:
            slot = current_slot
        if current_slot != slot or spec.generation != index:
            raise FrontierContractError("resume changed slot or skipped a generation")
        if spec.previous_generation_digest != prior_digest:
            raise FrontierContractError("resume predecessor digest differs")
        prior_digest = frontier_digest(spec)

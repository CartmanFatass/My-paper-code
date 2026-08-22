"""Hash-linked, same-coordinate, create-only TBCC r02 training frontiers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path
from typing import Final, Iterable, Mapping

from .artifacts import (
    ADAPTER_ARMS,
    ArtifactContractError,
    AdapterExecutionPermit,
    AdapterFinalReceipt,
    EmpiricalBindings,
    FoundationFinalReceipt,
    accepted_native_binding_digest,
    atomic_create_json,
    load_canonical_json,
    validate_adapter_execution_permit,
)


class FrontierContractError(RuntimeError):
    pass


class FrontierStage(str, Enum):
    FOUNDATION = "FOUNDATION"
    ADAPTER = "ADAPTER"


class FrontierState(str, Enum):
    CREATED = "CREATED"
    TRAINING = "TRAINING"
    FINAL_CHECKPOINT = "FINAL_CHECKPOINT"


_FOUNDATION_MAX_UPDATE: Final[int] = 160
_FOUNDATION_MAX_STEP: Final[int] = 1920
_ADAPTER_MAX_UPDATE: Final[int] = 96
_ADAPTER_MAX_STEP: Final[int] = 1152


def _fake_or_real_sha(value: object, field: str, *, test_only: bool) -> str:
    prefix = "TEST_ONLY_FAKE_SHA256:"
    if not isinstance(value, str):
        raise FrontierContractError(f"{field} is not a digest")
    digest = value[len(prefix) :] if test_only and value.startswith(prefix) else value
    if test_only != value.startswith(prefix) or len(digest) != 64:
        raise FrontierContractError(f"{field} has the wrong lineage class")
    try:
        int(digest, 16)
    except ValueError as error:
        raise FrontierContractError(f"{field} is not hexadecimal") from error
    return value


@dataclass(frozen=True)
class FrontierGeneration:
    stage: FrontierStage
    replicate: int
    arm: str
    lineage_digest: str
    coordinate_manifest_sha256: str
    generation: int
    previous_generation_sha256: str | None
    state: FrontierState
    update_index: int
    optimizer_step: int
    checkpoint_sha256: str | None = None
    optimizer_state_sha256: str | None = None
    partial_inspection_permitted: bool = False

    def validate(self, bindings: EmpiricalBindings) -> None:
        try:
            bindings.validate()
        except ArtifactContractError as error:
            raise FrontierContractError("sealed empirical bindings are required") from error
        if self.lineage_digest != bindings.lineage_digest:
            raise FrontierContractError("frontier lineage differs")
        if self.coordinate_manifest_sha256 != bindings.coordinate_manifest_sha256:
            raise FrontierContractError("frontier coordinate differs")
        if isinstance(self.replicate, bool) or self.replicate not in range(24):
            raise FrontierContractError("frontier replicate is unregistered")
        if self.stage is FrontierStage.FOUNDATION:
            if self.arm != "FOUNDATION":
                raise FrontierContractError("foundation frontier arm differs")
            max_update, max_step = _FOUNDATION_MAX_UPDATE, _FOUNDATION_MAX_STEP
        elif self.stage is FrontierStage.ADAPTER:
            if self.arm not in ADAPTER_ARMS:
                raise FrontierContractError("adapter frontier arm differs")
            max_update, max_step = _ADAPTER_MAX_UPDATE, _ADAPTER_MAX_STEP
        else:
            raise FrontierContractError("frontier stage differs")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 0:
            raise FrontierContractError("frontier generation must be nonnegative")
        if self.generation == 0 and self.previous_generation_sha256 is not None:
            raise FrontierContractError("initial frontier cannot cite a predecessor")
        if self.generation > 0:
            _fake_or_real_sha(
                self.previous_generation_sha256, "previous_generation_sha256", test_only=bindings.test_only
            )
        if isinstance(self.update_index, bool) or not isinstance(self.update_index, int) or not 0 <= self.update_index <= max_update:
            raise FrontierContractError("frontier update index lies outside the frozen budget")
        if isinstance(self.optimizer_step, bool) or not isinstance(self.optimizer_step, int) or not 0 <= self.optimizer_step <= max_step:
            raise FrontierContractError("frontier optimizer step lies outside the frozen budget")
        if self.state is FrontierState.CREATED and (self.update_index != 0 or self.optimizer_step != 0):
            raise FrontierContractError("created frontier cannot contain training progress")
        if self.state is FrontierState.FINAL_CHECKPOINT:
            if self.update_index != max_update or self.optimizer_step != max_step:
                raise FrontierContractError("frontier final does not match the sole eligible budget")
            _fake_or_real_sha(self.checkpoint_sha256, "checkpoint_sha256", test_only=bindings.test_only)
            _fake_or_real_sha(
                self.optimizer_state_sha256, "optimizer_state_sha256", test_only=bindings.test_only
            )
        elif self.checkpoint_sha256 is not None or self.optimizer_state_sha256 is not None:
            raise FrontierContractError("nonfinal frontier cannot expose checkpoint state")
        if self.partial_inspection_permitted is not False:
            raise FrontierContractError("frontier must remain blinded")

    def payload(self, bindings: EmpiricalBindings) -> dict[str, object]:
        self.validate(bindings)
        return {
            "schema": "SCDMP_TBCC_R02_BLINDED_FRONTIER_GENERATION_V1",
            "stage": self.stage.value,
            "replicate": self.replicate,
            "arm": self.arm,
            "lineage_digest": self.lineage_digest,
            "coordinate_manifest_sha256": self.coordinate_manifest_sha256,
            "native_binding_sha256": accepted_native_binding_digest(),
            "generation": self.generation,
            "previous_generation_sha256": self.previous_generation_sha256,
            "state": self.state.value,
            "update_index": self.update_index,
            "optimizer_step": self.optimizer_step,
            "checkpoint_sha256": self.checkpoint_sha256,
            "optimizer_state_sha256": self.optimizer_state_sha256,
            "partial_inspection_permitted": False,
            "test_only": bindings.test_only,
        }


def frontier_generation_digest(value: FrontierGeneration, bindings: EmpiricalBindings) -> str:
    import json

    encoded = json.dumps(
        value.payload(bindings), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"TEST_ONLY_FAKE_SHA256:{digest}" if bindings.test_only else digest


def create_frontier_generation(
    path: Path,
    value: FrontierGeneration,
    *,
    artifact_root: Path,
    bindings: EmpiricalBindings,
    adapter_permit: AdapterExecutionPermit | None = None,
) -> str:
    if value.stage is FrontierStage.ADAPTER:
        try:
            validate_adapter_execution_permit(adapter_permit, bindings=bindings)  # type: ignore[arg-type]
        except ArtifactContractError as error:
            raise FrontierContractError(str(error)) from error
    try:
        digest = atomic_create_json(
            path, value.payload(bindings), artifact_root=artifact_root
        )
    except ArtifactContractError as error:
        raise FrontierContractError(str(error)) from error
    return f"TEST_ONLY_FAKE_SHA256:{digest}" if bindings.test_only else digest


def load_frontier_generation(
    path: Path, *, artifact_root: Path, bindings: EmpiricalBindings
) -> FrontierGeneration:
    try:
        row = load_canonical_json(path, artifact_root=artifact_root)
    except ArtifactContractError as error:
        raise FrontierContractError(str(error)) from error
    required = {
        "schema", "stage", "replicate", "arm", "lineage_digest",
        "coordinate_manifest_sha256", "native_binding_sha256", "generation", "previous_generation_sha256",
        "state", "update_index", "optimizer_step", "checkpoint_sha256",
        "optimizer_state_sha256", "partial_inspection_permitted", "test_only",
    }
    if set(row) != required or row.get("schema") != "SCDMP_TBCC_R02_BLINDED_FRONTIER_GENERATION_V1":
        raise FrontierContractError("frontier generation schema differs")
    try:
        value = FrontierGeneration(
            stage=FrontierStage(row["stage"]),
            replicate=row["replicate"],
            arm=row["arm"],
            lineage_digest=row["lineage_digest"],
            coordinate_manifest_sha256=row["coordinate_manifest_sha256"],
            generation=row["generation"],
            previous_generation_sha256=row["previous_generation_sha256"],
            state=FrontierState(row["state"]),
            update_index=row["update_index"],
            optimizer_step=row["optimizer_step"],
            checkpoint_sha256=row["checkpoint_sha256"],
            optimizer_state_sha256=row["optimizer_state_sha256"],
            partial_inspection_permitted=row["partial_inspection_permitted"],
        )
    except (TypeError, ValueError) as error:
        raise FrontierContractError("frontier generation values differ") from error
    if row["test_only"] is not bindings.test_only:
        raise FrontierContractError("frontier lineage class differs")
    if row["native_binding_sha256"] != accepted_native_binding_digest():
        raise FrontierContractError("frontier native ABI2 binding differs")
    value.validate(bindings)
    if value.payload(bindings) != row:
        raise FrontierContractError("frontier payload differs")
    return value


def validate_resume_chain(
    generations: Iterable[FrontierGeneration], *, bindings: EmpiricalBindings
) -> tuple[FrontierGeneration, ...]:
    values = tuple(generations)
    if not values:
        raise FrontierContractError("resume chain is empty")
    first = values[0]
    slot = (first.stage, first.replicate, first.arm)
    predecessor: str | None = None
    prior_update = -1
    prior_step = -1
    for index, value in enumerate(values):
        value.validate(bindings)
        if (value.stage, value.replicate, value.arm) != slot:
            raise FrontierContractError("resume changed its frontier slot")
        if value.generation != index:
            raise FrontierContractError("resume skipped or reordered a generation")
        if value.previous_generation_sha256 != predecessor:
            raise FrontierContractError("resume predecessor hash differs")
        if value.update_index < prior_update or value.optimizer_step < prior_step:
            raise FrontierContractError("resume moved training progress backward")
        if index < len(values) - 1 and value.state is FrontierState.FINAL_CHECKPOINT:
            raise FrontierContractError("resume continued after the sole final checkpoint")
        predecessor = frontier_generation_digest(value, bindings)
        prior_update, prior_step = value.update_index, value.optimizer_step
    return values


def load_resume_chain(
    paths: Iterable[Path], *, artifact_root: Path, bindings: EmpiricalBindings
) -> tuple[FrontierGeneration, ...]:
    return validate_resume_chain(
        (
            load_frontier_generation(path, artifact_root=artifact_root, bindings=bindings)
            for path in paths
        ),
        bindings=bindings,
    )


def foundation_receipt_from_final(
    value: FrontierGeneration, *, bindings: EmpiricalBindings
) -> FoundationFinalReceipt:
    value.validate(bindings)
    if value.stage is not FrontierStage.FOUNDATION or value.state is not FrontierState.FINAL_CHECKPOINT:
        raise FrontierContractError("foundation receipt requires a foundation final")
    return FoundationFinalReceipt(
        replicate=value.replicate,
        coordinate_manifest_sha256=value.coordinate_manifest_sha256,
        checkpoint_sha256=value.checkpoint_sha256,  # type: ignore[arg-type]
        optimizer_state_sha256=value.optimizer_state_sha256,  # type: ignore[arg-type]
    )


def adapter_receipt_from_final(
    value: FrontierGeneration, *, bindings: EmpiricalBindings,
    adapter_permit: AdapterExecutionPermit
) -> AdapterFinalReceipt:
    try:
        validate_adapter_execution_permit(adapter_permit, bindings=bindings)
    except ArtifactContractError as error:
        raise FrontierContractError(str(error)) from error
    value.validate(bindings)
    if value.stage is not FrontierStage.ADAPTER or value.state is not FrontierState.FINAL_CHECKPOINT:
        raise FrontierContractError("adapter receipt requires an adapter final")
    return AdapterFinalReceipt(
        replicate=value.replicate,
        arm=value.arm,
        coordinate_manifest_sha256=value.coordinate_manifest_sha256,
        checkpoint_sha256=value.checkpoint_sha256,  # type: ignore[arg-type]
        optimizer_state_sha256=value.optimizer_state_sha256,  # type: ignore[arg-type]
    )

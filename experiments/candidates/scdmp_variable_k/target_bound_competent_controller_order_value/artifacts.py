"""Identity-blind, create-only empirical artifact contracts for TBCC r02.

This module never draws a master or derives a coordinate.  Production callers
must supply an explicit sealed permit and already-derived digest bindings.
Tests use the separate ``TEST_ONLY`` binding route, which cannot be confused
with a production lineage.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
from typing import Final, Iterable, Mapping

from .config import COMPONENT, HOST, LOADER_KEY, NATIVE_ABI_VERSION
from .empirical_contract import (
    CARD_REVISION,
    CARD_SHA256,
    NATIVE_REWARD_TRACE_CONTRACT,
    REPLICATE_NAMESPACE,
)
from .lifecycle import GateOutcome
from .source_manifest import (
    ACCEPTED_ABI_SIZES,
    ACCEPTED_NATIVE_ARTIFACT_SHA256,
    ACCEPTED_NATIVE_ARTIFACT_SIZE,
    ACCEPTED_NATIVE_BUILD_KEY,
    ACCEPTED_NATIVE_SOURCE_SHA256,
)


class ArtifactContractError(RuntimeError):
    pass


REVISION: Final[str] = CARD_REVISION
NAMESPACE: Final[str] = REPLICATE_NAMESPACE
FOUNDATION_SLOTS: Final[frozenset[int]] = frozenset(range(24))
ADAPTER_ARMS: Final[tuple[str, ...]] = ("TREAT", "FREE", "SET")
ADAPTER_SLOTS: Final[frozenset[tuple[int, str]]] = frozenset(
    (replicate, arm) for replicate in range(24) for arm in ADAPTER_ARMS
)
FINAL_CONTROLLERS: Final[tuple[str, ...]] = (
    "FOUNDATION", "TREAT", "FREE", "REVERSED", "SET"
)


def _sha256(value: object, field: str, *, test_only: bool = False) -> str:
    prefix = "TEST_ONLY_FAKE_SHA256:"
    if test_only:
        if not isinstance(value, str) or not value.startswith(prefix):
            raise ArtifactContractError(f"{field} must be an explicit TEST_ONLY fake digest")
        digest = value[len(prefix) :]
    else:
        if not isinstance(value, str) or value.startswith(prefix):
            raise ArtifactContractError(f"{field} must be a production SHA-256 digest")
        digest = value
    if len(digest) != 64:
        raise ArtifactContractError(f"{field} must contain 64 hexadecimal digits")
    try:
        int(digest, 16)
    except ValueError as error:
        raise ArtifactContractError(f"{field} must contain 64 hexadecimal digits") from error
    return (prefix if test_only else "") + digest.lower()


def _canonical(payload: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ArtifactContractError("artifact payload is not finite canonical JSON") from error


def _digest_payload(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def accepted_native_binding() -> dict[str, object]:
    """Return the accepted ABI2 host-output/reward-trace binding."""

    if NATIVE_ABI_VERSION != 2:
        raise ArtifactContractError("stale native ABI1 configuration is forbidden")
    if ACCEPTED_ABI_SIZES.get("host_output") != 336:
        raise ArtifactContractError("accepted ABI2 HostOutput size differs")
    if NATIVE_REWARD_TRACE_CONTRACT != {
        "abi_version": 2,
        "capacity": 13,
        "count_field": "last_hold_reward_count",
        "values_field": "last_hold_rewards",
        "count_equals_ticks_advanced": True,
        "inactive_tail": "canonical_zero",
    }:
        raise ArtifactContractError("accepted ABI2 reward-trace contract differs")
    return {
        "native_abi": NATIVE_ABI_VERSION,
        "native_source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "native_build_key": ACCEPTED_NATIVE_BUILD_KEY,
        "native_artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
        "native_artifact_size": ACCEPTED_NATIVE_ARTIFACT_SIZE,
        "native_struct_sizes": dict(ACCEPTED_ABI_SIZES),
        "native_reward_trace": dict(NATIVE_REWARD_TRACE_CONTRACT),
    }


def accepted_native_binding_digest() -> str:
    return _digest_payload(accepted_native_binding())


def _within(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ArtifactContractError("artifact path escapes its declared root") from error
    if resolved == resolved_root:
        raise ArtifactContractError("artifact path cannot equal its declared root")
    return resolved


def atomic_create_json(path: Path, payload: Mapping[str, object], *, artifact_root: Path) -> str:
    """Durably create one canonical JSON object without replacing a target."""

    target = _within(artifact_root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = _canonical(payload)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.{os.urandom(8).hex()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise ArtifactContractError("artifact target is create-only") from error
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return hashlib.sha256(encoded).hexdigest()


def load_canonical_json(path: Path, *, artifact_root: Path) -> dict[str, object]:
    target = _within(artifact_root, path)
    try:
        encoded = target.read_bytes()
        value = json.loads(encoded.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("artifact is absent, interrupted, or unreadable") from error
    if not isinstance(value, dict) or _canonical(value) != encoded:
        raise ArtifactContractError("artifact is not an exact canonical object")
    return value


def preactivity_template(*, source_manifest_sha256: str, shared_receipt_sha256: str) -> dict[str, object]:
    """Return the source-only template; empirical identity fields are absent."""

    source = _sha256(source_manifest_sha256, "source_manifest_sha256")
    shared = _sha256(shared_receipt_sha256, "shared_receipt_sha256")
    return {
        "schema": "SCDMP_TBCC_R02_PREACTIVITY_TEMPLATE_V1",
        "revision": REVISION,
        "card_sha256": CARD_SHA256,
        "source_manifest_sha256": source,
        "shared_component": COMPONENT,
        "shared_loader_key": LOADER_KEY,
        "shared_receipt_sha256": shared,
        "host": HOST,
        **accepted_native_binding(),
        "empirical_identity_fields_absent": True,
        "scientific_activity_started": False,
    }


def publish_preactivity_template(
    path: Path,
    *,
    artifact_root: Path,
    source_manifest_sha256: str,
    shared_receipt_sha256: str,
) -> str:
    return atomic_create_json(
        path,
        preactivity_template(
            source_manifest_sha256=source_manifest_sha256,
            shared_receipt_sha256=shared_receipt_sha256,
        ),
        artifact_root=artifact_root,
    )


@dataclass(frozen=True, repr=False)
class EmpiricalActivityPermit:
    authorization_sha256: str
    stage: str
    activity_authorized: bool
    _seal: object | None = None


_PRODUCTION_PERMIT_SEAL: Final[object] = object()
_BINDING_SEAL: Final[object] = object()
_ADAPTER_PERMIT_SEAL: Final[object] = object()
_FINAL_EVALUATION_PERMIT_SEAL: Final[object] = object()
_STAGE1B_OPPORTUNITY_PERMIT_SEAL: Final[object] = object()


def seal_empirical_activity_permit(*, authorization_sha256: str) -> EmpiricalActivityPermit:
    """Seal caller-supplied Root authority; this function draws no identity."""

    return EmpiricalActivityPermit(
        authorization_sha256=_sha256(authorization_sha256, "authorization_sha256"),
        stage="SCDMP-TBCC-R02-FULL-EMPIRICAL-PANEL",
        activity_authorized=True,
        _seal=_PRODUCTION_PERMIT_SEAL,
    )


@dataclass(frozen=True, repr=False)
class EmpiricalBindings:
    source_manifest_sha256: str
    shared_receipt_sha256: str
    master_commitment_sha256: str
    empirical_identity_sha256: str
    coordinate_manifest_sha256: str
    origin_receipt_sha256: str
    authorization_sha256: str
    test_only: bool
    _seal: object | None = None

    def validate(self) -> None:
        if self._seal is not _BINDING_SEAL:
            raise ArtifactContractError("sealed caller-supplied bindings are required")
        for field in (
            "source_manifest_sha256", "shared_receipt_sha256",
            "master_commitment_sha256", "empirical_identity_sha256",
            "coordinate_manifest_sha256", "origin_receipt_sha256",
            "authorization_sha256",
        ):
            _sha256(getattr(self, field), field, test_only=self.test_only)

    def payload(self) -> dict[str, object]:
        self.validate()
        return {
            "revision": REVISION,
            "card_sha256": CARD_SHA256,
            "source_manifest_sha256": self.source_manifest_sha256,
            "shared_component": COMPONENT,
            "shared_loader_key": LOADER_KEY,
            "shared_receipt_sha256": self.shared_receipt_sha256,
            "host": HOST,
            **accepted_native_binding(),
            "namespace": NAMESPACE,
            "master_commitment_sha256": self.master_commitment_sha256,
            "empirical_identity_sha256": self.empirical_identity_sha256,
            "coordinate_manifest_sha256": self.coordinate_manifest_sha256,
            "origin_receipt_sha256": self.origin_receipt_sha256,
            "authorization_sha256": self.authorization_sha256,
            "test_only": self.test_only,
        }

    @property
    def lineage_digest(self) -> str:
        return _digest_payload(self.payload())


def seal_empirical_bindings(
    *,
    permit: EmpiricalActivityPermit,
    source_manifest_sha256: str,
    shared_receipt_sha256: str,
    master_commitment_sha256: str,
    empirical_identity_sha256: str,
    coordinate_manifest_sha256: str,
    origin_receipt_sha256: str,
) -> EmpiricalBindings:
    if (
        not isinstance(permit, EmpiricalActivityPermit)
        or permit._seal is not _PRODUCTION_PERMIT_SEAL
        or permit.activity_authorized is not True
        or permit.stage != "SCDMP-TBCC-R02-FULL-EMPIRICAL-PANEL"
    ):
        raise ArtifactContractError("sealed empirical activity permit is required")
    value = EmpiricalBindings(
        source_manifest_sha256=_sha256(source_manifest_sha256, "source_manifest_sha256"),
        shared_receipt_sha256=_sha256(shared_receipt_sha256, "shared_receipt_sha256"),
        master_commitment_sha256=_sha256(master_commitment_sha256, "master_commitment_sha256"),
        empirical_identity_sha256=_sha256(empirical_identity_sha256, "empirical_identity_sha256"),
        coordinate_manifest_sha256=_sha256(coordinate_manifest_sha256, "coordinate_manifest_sha256"),
        origin_receipt_sha256=_sha256(origin_receipt_sha256, "origin_receipt_sha256"),
        authorization_sha256=permit.authorization_sha256,
        test_only=False,
        _seal=_BINDING_SEAL,
    )
    value.validate()
    return value


def test_only_bindings(*, token: str = "0") -> EmpiricalBindings:
    """Return a conspicuously fake lineage for mechanics-only tests."""

    digest = hashlib.sha256(f"TEST_ONLY:{token}".encode("ascii")).hexdigest()
    fake = f"TEST_ONLY_FAKE_SHA256:{digest}"
    value = EmpiricalBindings(
        source_manifest_sha256=fake,
        shared_receipt_sha256=fake,
        master_commitment_sha256=fake,
        empirical_identity_sha256=fake,
        coordinate_manifest_sha256=fake,
        origin_receipt_sha256=fake,
        authorization_sha256=fake,
        test_only=True,
        _seal=_BINDING_SEAL,
    )
    value.validate()
    return value


def _binding_fields(bindings: EmpiricalBindings) -> dict[str, object]:
    bindings.validate()
    return {
        "lineage_digest": bindings.lineage_digest,
        "coordinate_manifest_sha256": bindings.coordinate_manifest_sha256,
        "test_only": bindings.test_only,
    }


@dataclass(frozen=True)
class FoundationFinalReceipt:
    replicate: int
    coordinate_manifest_sha256: str
    checkpoint_sha256: str
    optimizer_state_sha256: str
    update_index: int = 160
    optimizer_step: int = 1920
    technically_accepted: bool = True

    def validate(self, bindings: EmpiricalBindings) -> None:
        bindings.validate()
        if self.replicate not in FOUNDATION_SLOTS:
            raise ArtifactContractError("foundation final replicate is unregistered")
        if self.coordinate_manifest_sha256 != bindings.coordinate_manifest_sha256:
            raise ArtifactContractError("foundation final coordinate differs")
        _sha256(self.checkpoint_sha256, "checkpoint_sha256", test_only=bindings.test_only)
        _sha256(self.optimizer_state_sha256, "optimizer_state_sha256", test_only=bindings.test_only)
        if self.update_index != 160 or self.optimizer_step != 1920:
            raise ArtifactContractError("foundation final is not update 160 / optimizer step 1920")
        if self.technically_accepted is not True:
            raise ArtifactContractError("foundation final lacks technical acceptance")

    def payload(self) -> dict[str, object]:
        return {
            "replicate": self.replicate,
            "arm": "FOUNDATION",
            "coordinate_manifest_sha256": self.coordinate_manifest_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
            "optimizer_state_sha256": self.optimizer_state_sha256,
            "update_index": self.update_index,
            "optimizer_step": self.optimizer_step,
            "technically_accepted": self.technically_accepted,
        }


@dataclass(frozen=True)
class FoundationCheckpointBarrier:
    lineage_digest: str
    coordinate_manifest_sha256: str
    native_binding_sha256: str
    receipt_inventory_sha256: str
    accepted_slots: int = 24
    competence_evaluation_open: bool = True


def require_foundation_checkpoint_barrier(
    receipts: Iterable[FoundationFinalReceipt], bindings: EmpiricalBindings
) -> FoundationCheckpointBarrier:
    values = tuple(receipts)
    if len(values) != 24:
        raise ArtifactContractError("foundation barrier requires exactly 24 final receipts")
    for value in values:
        value.validate(bindings)
    slots = [value.replicate for value in values]
    if len(set(slots)) != 24 or set(slots) != FOUNDATION_SLOTS:
        raise ArtifactContractError("foundation receipts are missing, duplicate, or extra")
    payload = [value.payload() for value in sorted(values, key=lambda item: item.replicate)]
    return FoundationCheckpointBarrier(
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        native_binding_sha256=accepted_native_binding_digest(),
        receipt_inventory_sha256=hashlib.sha256(_canonical({"receipts": payload})).hexdigest(),
    )


@dataclass(frozen=True)
class FoundationGate:
    outcome: GateOutcome
    complete_panel_sha256: str
    barrier_sha256: str


def foundation_barrier_digest(barrier: FoundationCheckpointBarrier) -> str:
    return _digest_payload(barrier.__dict__)


def publish_foundation_gate(
    path: Path,
    gate: FoundationGate,
    *,
    artifact_root: Path,
    barrier: FoundationCheckpointBarrier,
    bindings: EmpiricalBindings,
) -> str:
    if barrier.lineage_digest != bindings.lineage_digest:
        raise ArtifactContractError("foundation barrier lineage differs")
    if barrier.native_binding_sha256 != accepted_native_binding_digest():
        raise ArtifactContractError("foundation barrier native ABI2 binding differs")
    if gate.barrier_sha256 != foundation_barrier_digest(barrier):
        raise ArtifactContractError("foundation gate cites a different checkpoint barrier")
    _sha256(gate.complete_panel_sha256, "complete_panel_sha256", test_only=bindings.test_only)
    payload = {
        "schema": "SCDMP_TBCC_R02_FOUNDATION_GATE_V1",
        **_binding_fields(bindings),
        "checkpoint_barrier_sha256": gate.barrier_sha256,
        "complete_panel_sha256": gate.complete_panel_sha256,
        "outcome": gate.outcome.value,
        "complete": True,
        "partial_values_exposed": False,
    }
    return atomic_create_json(path, payload, artifact_root=artifact_root)


def load_foundation_gate(
    path: Path, *, artifact_root: Path, barrier: FoundationCheckpointBarrier,
    bindings: EmpiricalBindings
) -> FoundationGate:
    value = load_canonical_json(path, artifact_root=artifact_root)
    expected_common = {
        "schema": "SCDMP_TBCC_R02_FOUNDATION_GATE_V1",
        **_binding_fields(bindings),
        "checkpoint_barrier_sha256": foundation_barrier_digest(barrier),
        "complete": True,
        "partial_values_exposed": False,
    }
    if any(value.get(key) != item for key, item in expected_common.items()) or set(value) != set(expected_common) | {"complete_panel_sha256", "outcome"}:
        raise ArtifactContractError("foundation gate binding or schema differs")
    try:
        gate = FoundationGate(
            outcome=GateOutcome(value["outcome"]),
            complete_panel_sha256=str(value["complete_panel_sha256"]),
            barrier_sha256=foundation_barrier_digest(barrier),
        )
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("foundation gate outcome differs") from error
    _sha256(gate.complete_panel_sha256, "complete_panel_sha256", test_only=bindings.test_only)
    return gate


def _verify_foundation_gate_file(
    path: Path, gate: FoundationGate, *, artifact_root: Path, bindings: EmpiricalBindings
) -> str:
    row = load_canonical_json(path, artifact_root=artifact_root)
    if (
        row.get("schema") != "SCDMP_TBCC_R02_FOUNDATION_GATE_V1"
        or row.get("lineage_digest") != bindings.lineage_digest
        or row.get("coordinate_manifest_sha256") != bindings.coordinate_manifest_sha256
        or row.get("test_only") is not bindings.test_only
        or row.get("outcome") != gate.outcome.value
        or row.get("complete_panel_sha256") != gate.complete_panel_sha256
        or row.get("checkpoint_barrier_sha256") != gate.barrier_sha256
        or row.get("complete") is not True
        or row.get("partial_values_exposed") is not False
    ):
        raise ArtifactContractError("foundation gate file is tampered or cross-lineage")
    return hashlib.sha256(_canonical(row)).hexdigest()


@dataclass(frozen=True, repr=False)
class Stage1bOpportunityExecutionPermit:
    """Opaque production bridge from the accepted foundation into Stage 1b."""

    lineage_digest: str
    coordinate_manifest_sha256: str
    receipt_inventory_sha256: str
    foundation_barrier_sha256: str
    foundation_gate_sha256: str
    complete_panel_sha256: str
    downstream_targets_sha256: str
    accepted_foundation_slots: int
    adapter_target_count: int
    opportunity_unopened: bool
    adapters_unopened: bool
    final_evaluation_unopened: bool
    test_only: bool = False
    _artifact_root: Path | None = None
    _downstream_paths: tuple[Path, ...] = ()
    _seal: object | None = None


def _stage1b_permit_payload(permit: Stage1bOpportunityExecutionPermit) -> dict[str, object]:
    return {
        "lineage_digest": permit.lineage_digest,
        "coordinate_manifest_sha256": permit.coordinate_manifest_sha256,
        "receipt_inventory_sha256": permit.receipt_inventory_sha256,
        "foundation_barrier_sha256": permit.foundation_barrier_sha256,
        "foundation_gate_sha256": permit.foundation_gate_sha256,
        "complete_panel_sha256": permit.complete_panel_sha256,
        "downstream_targets_sha256": permit.downstream_targets_sha256,
        "accepted_foundation_slots": permit.accepted_foundation_slots,
        "adapter_target_count": permit.adapter_target_count,
        "opportunity_unopened": permit.opportunity_unopened,
        "adapters_unopened": permit.adapters_unopened,
        "final_evaluation_unopened": permit.final_evaluation_unopened,
        "test_only": permit.test_only,
    }


def _downstream_targets_digest(
    *,
    artifact_root: Path,
    opportunity_receipt_path: Path,
    adapter_frontier_paths: Iterable[Path],
    final_result_path: Path,
) -> tuple[str, int, tuple[Path, ...]]:
    root = artifact_root.resolve()
    opportunity = _within(root, opportunity_receipt_path)
    final = _within(root, final_result_path)
    adapters = tuple(_within(root, path) for path in adapter_frontier_paths)
    if len(adapters) != 72 or len(set(adapters)) != 72:
        raise ArtifactContractError("Stage-1b permit requires exactly 72 distinct adapter targets")
    targets = (opportunity, *adapters, final)
    if len(set(targets)) != 74:
        raise ArtifactContractError("Stage-1b downstream targets must be pairwise distinct")
    if any(path.exists() for path in targets):
        raise ArtifactContractError("Stage-1b downstream lifecycle is already open")
    relative = sorted(path.relative_to(root).as_posix() for path in targets)
    return _digest_payload({"unopened_downstream_targets": relative}), len(adapters), targets


def issue_stage1b_opportunity_execution_permit(
    *,
    receipts: Iterable[FoundationFinalReceipt],
    foundation_barrier: FoundationCheckpointBarrier,
    foundation_gate_path: Path,
    foundation_gate: FoundationGate,
    artifact_root: Path,
    bindings: EmpiricalBindings,
    opportunity_receipt_path: Path,
    adapter_frontier_paths: Iterable[Path],
    final_result_path: Path,
) -> Stage1bOpportunityExecutionPermit:
    """Validate the exact production barrier/gate and seal the unopened Stage 1b bridge."""

    bindings.validate()
    if bindings.test_only:
        raise ArtifactContractError("production Stage-1b permit forbids TEST_ONLY bindings")
    values = tuple(receipts)
    recomputed = require_foundation_checkpoint_barrier(values, bindings)
    if recomputed != foundation_barrier:
        raise ArtifactContractError("Stage-1b foundation barrier or receipt inventory differs")
    if (
        foundation_barrier.accepted_slots != 24
        or foundation_barrier.competence_evaluation_open is not True
        or foundation_barrier.lineage_digest != bindings.lineage_digest
        or foundation_barrier.coordinate_manifest_sha256 != bindings.coordinate_manifest_sha256
    ):
        raise ArtifactContractError("Stage-1b foundation barrier binding differs")
    if foundation_gate.outcome is not GateOutcome.PASS:
        raise ArtifactContractError("Stage-1b requires a passing atomic foundation gate")
    barrier_sha = foundation_barrier_digest(foundation_barrier)
    if foundation_gate.barrier_sha256 != barrier_sha:
        raise ArtifactContractError("Stage-1b foundation gate cites a different barrier")
    _sha256(foundation_gate.complete_panel_sha256, "complete_panel_sha256")
    gate_sha = _verify_foundation_gate_file(
        foundation_gate_path,
        foundation_gate,
        artifact_root=artifact_root,
        bindings=bindings,
    )
    downstream_sha, adapter_count, downstream_paths = _downstream_targets_digest(
        artifact_root=artifact_root,
        opportunity_receipt_path=opportunity_receipt_path,
        adapter_frontier_paths=adapter_frontier_paths,
        final_result_path=final_result_path,
    )
    unsealed = Stage1bOpportunityExecutionPermit(
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        receipt_inventory_sha256=foundation_barrier.receipt_inventory_sha256,
        foundation_barrier_sha256=barrier_sha,
        foundation_gate_sha256=gate_sha,
        complete_panel_sha256=foundation_gate.complete_panel_sha256,
        downstream_targets_sha256=downstream_sha,
        accepted_foundation_slots=24,
        adapter_target_count=adapter_count,
        opportunity_unopened=True,
        adapters_unopened=True,
        final_evaluation_unopened=True,
        test_only=False,
    )
    permit = Stage1bOpportunityExecutionPermit(
        **_stage1b_permit_payload(unsealed),
        _artifact_root=artifact_root.resolve(),
        _downstream_paths=downstream_paths,
        _seal=(
            _STAGE1B_OPPORTUNITY_PERMIT_SEAL,
            _digest_payload(_stage1b_permit_payload(unsealed)),
        ),
    )
    validate_stage1b_opportunity_execution_permit(permit, bindings=bindings)
    return permit


def validate_stage1b_opportunity_execution_permit(
    permit: Stage1bOpportunityExecutionPermit,
    *,
    bindings: EmpiricalBindings | None = None,
) -> None:
    if not isinstance(permit, Stage1bOpportunityExecutionPermit):
        raise ArtifactContractError("sealed production Stage-1b opportunity permit is required")
    seal = permit._seal
    if (
        not isinstance(seal, tuple)
        or len(seal) != 2
        or seal[0] is not _STAGE1B_OPPORTUNITY_PERMIT_SEAL
        or seal[1] != _digest_payload(_stage1b_permit_payload(permit))
    ):
        raise ArtifactContractError("sealed production Stage-1b opportunity permit is required")
    for field in (
        "lineage_digest",
        "coordinate_manifest_sha256",
        "receipt_inventory_sha256",
        "foundation_barrier_sha256",
        "foundation_gate_sha256",
        "complete_panel_sha256",
        "downstream_targets_sha256",
    ):
        _sha256(getattr(permit, field), field)
    if (
        permit.accepted_foundation_slots != 24
        or permit.adapter_target_count != 72
        or permit.opportunity_unopened is not True
        or permit.adapters_unopened is not True
        or permit.final_evaluation_unopened is not True
        or permit.test_only is not False
    ):
        raise ArtifactContractError("production Stage-1b opportunity permit binding differs")
    if permit._artifact_root is None or len(permit._downstream_paths) != 74:
        raise ArtifactContractError("production Stage-1b unopened-target binding differs")
    root = permit._artifact_root.resolve()
    try:
        relative = sorted(path.resolve().relative_to(root).as_posix() for path in permit._downstream_paths)
    except ValueError as error:
        raise ArtifactContractError("production Stage-1b unopened target escapes artifact root") from error
    if _digest_payload({"unopened_downstream_targets": relative}) != permit.downstream_targets_sha256:
        raise ArtifactContractError("production Stage-1b unopened-target digest differs")
    if any(path.exists() for path in permit._downstream_paths):
        raise ArtifactContractError("production Stage-1b downstream lifecycle is already open")
    if bindings is not None:
        bindings.validate()
        if bindings.test_only:
            raise ArtifactContractError("production Stage-1b permit forbids TEST_ONLY bindings")
        if (
            permit.lineage_digest != bindings.lineage_digest
            or permit.coordinate_manifest_sha256 != bindings.coordinate_manifest_sha256
        ):
            raise ArtifactContractError("production Stage-1b opportunity permit lineage differs")


@dataclass(frozen=True)
class OpportunityReceipt:
    outcome: GateOutcome
    complete_stage_sha256: str
    foundation_gate_sha256: str


def publish_opportunity_receipt(
    path: Path,
    receipt: OpportunityReceipt,
    *,
    artifact_root: Path,
    foundation_gate_path: Path,
    foundation_gate: FoundationGate,
    bindings: EmpiricalBindings,
) -> str:
    if foundation_gate.outcome is not GateOutcome.PASS:
        raise ArtifactContractError("opportunity is inapplicable without a passing foundation gate")
    foundation_sha = _verify_foundation_gate_file(
        foundation_gate_path, foundation_gate, artifact_root=artifact_root, bindings=bindings
    )
    if receipt.foundation_gate_sha256 != foundation_sha:
        raise ArtifactContractError("opportunity receipt cites a different foundation gate")
    _sha256(receipt.complete_stage_sha256, "complete_stage_sha256", test_only=bindings.test_only)
    payload = {
        "schema": "SCDMP_TBCC_R02_OPPORTUNITY_RECEIPT_V1",
        **_binding_fields(bindings),
        "foundation_gate_sha256": foundation_sha,
        "complete_stage_sha256": receipt.complete_stage_sha256,
        "outcome": receipt.outcome.value,
        "replicate_count": 24,
        "fixed_k_count": 2,
        "states_per_k": 16,
        "pairs_per_replicate": 32,
        "actions": 18,
        "tapes": 4,
        "graphs": 2,
        "complete_rollouts": 110592,
        "complete": True,
        "partial_values_exposed": False,
    }
    return atomic_create_json(path, payload, artifact_root=artifact_root)


def load_opportunity_receipt(
    path: Path, *, artifact_root: Path, foundation_gate_path: Path,
    foundation_gate: FoundationGate, bindings: EmpiricalBindings
) -> OpportunityReceipt:
    if foundation_gate.outcome is not GateOutcome.PASS:
        raise ArtifactContractError("opportunity is inapplicable without a passing foundation gate")
    foundation_sha = hashlib.sha256(_within(artifact_root, foundation_gate_path).read_bytes()).hexdigest()
    value = load_canonical_json(path, artifact_root=artifact_root)
    fixed = {
        "schema": "SCDMP_TBCC_R02_OPPORTUNITY_RECEIPT_V1",
        **_binding_fields(bindings),
        "foundation_gate_sha256": foundation_sha,
        "replicate_count": 24, "fixed_k_count": 2, "states_per_k": 16,
        "pairs_per_replicate": 32, "actions": 18, "tapes": 4, "graphs": 2,
        "complete_rollouts": 110592,
        "complete": True, "partial_values_exposed": False,
    }
    if any(value.get(k) != v for k, v in fixed.items()) or set(value) != set(fixed) | {"complete_stage_sha256", "outcome"}:
        raise ArtifactContractError("opportunity receipt binding or schema differs")
    try:
        result = OpportunityReceipt(
            outcome=GateOutcome(value["outcome"]),
            complete_stage_sha256=str(value["complete_stage_sha256"]),
            foundation_gate_sha256=foundation_sha,
        )
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("opportunity outcome differs") from error
    _sha256(result.complete_stage_sha256, "complete_stage_sha256", test_only=bindings.test_only)
    return result


def _verify_opportunity_file(
    path: Path, receipt: OpportunityReceipt, *, artifact_root: Path,
    foundation_gate_sha256: str, bindings: EmpiricalBindings,
) -> str:
    row = load_canonical_json(path, artifact_root=artifact_root)
    if (
        row.get("schema") != "SCDMP_TBCC_R02_OPPORTUNITY_RECEIPT_V1"
        or row.get("lineage_digest") != bindings.lineage_digest
        or row.get("coordinate_manifest_sha256") != bindings.coordinate_manifest_sha256
        or row.get("test_only") is not bindings.test_only
        or row.get("foundation_gate_sha256") != foundation_gate_sha256
        or row.get("complete_stage_sha256") != receipt.complete_stage_sha256
        or row.get("outcome") != receipt.outcome.value
        or row.get("complete") is not True
        or row.get("partial_values_exposed") is not False
    ):
        raise ArtifactContractError("opportunity receipt file is tampered or cross-lineage")
    return hashlib.sha256(_canonical(row)).hexdigest()


@dataclass(frozen=True, repr=False)
class AdapterExecutionPermit:
    lineage_digest: str
    native_binding_sha256: str
    foundation_gate_sha256: str
    opportunity_receipt_sha256: str
    _seal: object | None = None


def issue_adapter_execution_permit(
    *, foundation_gate_path: Path, foundation_gate: FoundationGate,
    opportunity_path: Path, opportunity: OpportunityReceipt,
    artifact_root: Path, bindings: EmpiricalBindings,
) -> AdapterExecutionPermit:
    """Open adapter materialization only after both complete gates pass."""

    bindings.validate()
    if foundation_gate.outcome is not GateOutcome.PASS or opportunity.outcome is not GateOutcome.PASS:
        raise ArtifactContractError("adapter execution requires both prerequisite gates to pass")
    foundation_sha = _verify_foundation_gate_file(
        foundation_gate_path, foundation_gate, artifact_root=artifact_root, bindings=bindings
    )
    opportunity_sha = _verify_opportunity_file(
        opportunity_path, opportunity, artifact_root=artifact_root,
        foundation_gate_sha256=foundation_sha, bindings=bindings,
    )
    permit = AdapterExecutionPermit(
        lineage_digest=bindings.lineage_digest,
        native_binding_sha256=accepted_native_binding_digest(),
        foundation_gate_sha256=foundation_sha,
        opportunity_receipt_sha256=opportunity_sha,
        _seal=_ADAPTER_PERMIT_SEAL,
    )
    validate_adapter_execution_permit(permit, bindings=bindings)
    return permit


def validate_adapter_execution_permit(
    permit: AdapterExecutionPermit, *, bindings: EmpiricalBindings
) -> None:
    if not isinstance(permit, AdapterExecutionPermit) or permit._seal is not _ADAPTER_PERMIT_SEAL:
        raise ArtifactContractError("sealed passing-prerequisite adapter permit is required")
    if permit.lineage_digest != bindings.lineage_digest:
        raise ArtifactContractError("adapter permit lineage differs")
    if permit.native_binding_sha256 != accepted_native_binding_digest():
        raise ArtifactContractError("adapter permit native ABI2 binding differs")
    _sha256(permit.foundation_gate_sha256, "foundation_gate_sha256")
    _sha256(permit.opportunity_receipt_sha256, "opportunity_receipt_sha256")


@dataclass(frozen=True)
class AdapterFinalReceipt:
    replicate: int
    arm: str
    coordinate_manifest_sha256: str
    checkpoint_sha256: str
    optimizer_state_sha256: str
    update_index: int = 96
    optimizer_step: int = 1152
    technically_accepted: bool = True

    def validate(self, bindings: EmpiricalBindings) -> None:
        if (self.replicate, self.arm) not in ADAPTER_SLOTS:
            raise ArtifactContractError("adapter final slot is unregistered")
        if self.coordinate_manifest_sha256 != bindings.coordinate_manifest_sha256:
            raise ArtifactContractError("adapter final coordinate differs")
        _sha256(self.checkpoint_sha256, "checkpoint_sha256", test_only=bindings.test_only)
        _sha256(self.optimizer_state_sha256, "optimizer_state_sha256", test_only=bindings.test_only)
        if self.update_index != 96 or self.optimizer_step != 1152:
            raise ArtifactContractError("adapter final is not update 96 / optimizer step 1152")
        if self.technically_accepted is not True:
            raise ArtifactContractError("adapter final lacks technical acceptance")

    def payload(self) -> dict[str, object]:
        return {
            "replicate": self.replicate, "arm": self.arm,
            "coordinate_manifest_sha256": self.coordinate_manifest_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
            "optimizer_state_sha256": self.optimizer_state_sha256,
            "update_index": self.update_index, "optimizer_step": self.optimizer_step,
            "technically_accepted": self.technically_accepted,
        }


@dataclass(frozen=True)
class FinalPanelBarrier:
    lineage_digest: str
    coordinate_manifest_sha256: str
    native_binding_sha256: str
    foundation_receipt_inventory_sha256: str
    adapter_receipt_inventory_sha256: str
    foundation_gate_sha256: str
    opportunity_receipt_sha256: str
    accepted_foundations: int = 24
    accepted_adapters: int = 72
    controllers: tuple[str, ...] = FINAL_CONTROLLERS
    evaluation_open: bool = True


def require_final_panel_barrier(
    adapter_receipts: Iterable[AdapterFinalReceipt], *,
    foundation_barrier: FoundationCheckpointBarrier,
    foundation_gate_path: Path,
    foundation_gate: FoundationGate,
    opportunity_path: Path,
    opportunity: OpportunityReceipt,
    artifact_root: Path,
    bindings: EmpiricalBindings,
) -> FinalPanelBarrier:
    if foundation_gate.outcome is not GateOutcome.PASS or opportunity.outcome is not GateOutcome.PASS:
        raise ArtifactContractError("final panel requires both prerequisite gates to pass")
    if (
        foundation_barrier.lineage_digest != bindings.lineage_digest
        or foundation_barrier.native_binding_sha256 != accepted_native_binding_digest()
    ):
        raise ArtifactContractError("final panel foundation lineage differs")
    values = tuple(adapter_receipts)
    if len(values) != 72:
        raise ArtifactContractError("final panel requires exactly 72 adapter finals")
    for value in values:
        value.validate(bindings)
    slots = [(value.replicate, value.arm) for value in values]
    if len(set(slots)) != 72 or set(slots) != ADAPTER_SLOTS:
        raise ArtifactContractError("adapter finals are missing, duplicate, or extra")
    ordered = sorted(values, key=lambda item: (item.replicate, ADAPTER_ARMS.index(item.arm)))
    return FinalPanelBarrier(
        lineage_digest=bindings.lineage_digest,
        coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
        native_binding_sha256=accepted_native_binding_digest(),
        foundation_receipt_inventory_sha256=foundation_barrier.receipt_inventory_sha256,
        adapter_receipt_inventory_sha256=hashlib.sha256(
            _canonical({"receipts": [value.payload() for value in ordered]})
        ).hexdigest(),
        foundation_gate_sha256=hashlib.sha256(_within(artifact_root, foundation_gate_path).read_bytes()).hexdigest(),
        opportunity_receipt_sha256=hashlib.sha256(_within(artifact_root, opportunity_path).read_bytes()).hexdigest(),
    )


def final_panel_barrier_digest(barrier: FinalPanelBarrier) -> str:
    payload = dict(barrier.__dict__)
    payload["controllers"] = list(barrier.controllers)
    return _digest_payload(payload)


@dataclass(frozen=True)
class FinalPanelReceipt:
    complete_panel_sha256: str
    barrier_sha256: str
    replicate_count: int = 24
    controller_count: int = 5
    regime_count: int = 6
    episodes_per_cell: int = 120

    def validate(self, barrier: FinalPanelBarrier, bindings: EmpiricalBindings) -> None:
        _sha256(self.complete_panel_sha256, "complete_panel_sha256", test_only=bindings.test_only)
        if self.barrier_sha256 != final_panel_barrier_digest(barrier):
            raise ArtifactContractError("final panel receipt cites a different barrier")
        if (self.replicate_count, self.controller_count, self.regime_count, self.episodes_per_cell) != (24, 5, 6, 120):
            raise ArtifactContractError("final five-controller panel inventory differs")


@dataclass(frozen=True, repr=False)
class FinalEvaluationPermit:
    lineage_digest: str
    native_binding_sha256: str
    final_panel_barrier_sha256: str
    controller_count: int
    _seal: object | None = None


def issue_final_evaluation_permit(
    barrier: FinalPanelBarrier, *, bindings: EmpiricalBindings
) -> FinalEvaluationPermit:
    if barrier.lineage_digest != bindings.lineage_digest or barrier.evaluation_open is not True:
        raise ArtifactContractError("complete same-lineage final checkpoint barrier is required")
    permit = FinalEvaluationPermit(
        lineage_digest=bindings.lineage_digest,
        native_binding_sha256=accepted_native_binding_digest(),
        final_panel_barrier_sha256=final_panel_barrier_digest(barrier),
        controller_count=5,
        _seal=_FINAL_EVALUATION_PERMIT_SEAL,
    )
    validate_final_evaluation_permit(permit, barrier=barrier, bindings=bindings)
    return permit


def validate_final_evaluation_permit(
    permit: FinalEvaluationPermit, *, barrier: FinalPanelBarrier,
    bindings: EmpiricalBindings,
) -> None:
    if not isinstance(permit, FinalEvaluationPermit) or permit._seal is not _FINAL_EVALUATION_PERMIT_SEAL:
        raise ArtifactContractError("sealed final-evaluation permit is required")
    if (
        permit.lineage_digest != bindings.lineage_digest
        or permit.native_binding_sha256 != accepted_native_binding_digest()
        or permit.final_panel_barrier_sha256 != final_panel_barrier_digest(barrier)
        or permit.controller_count != 5
    ):
        raise ArtifactContractError("final-evaluation permit binding differs")


class ResultCode(str, Enum):
    FOUNDATION_NOT_ESTABLISHED = "COMMON-CONTROLLER-COMPETENCE-NOT-ESTABLISHED"
    OPPORTUNITY_NOT_ESTABLISHED = "TARGET-ORDER-OPPORTUNITY-NOT-ESTABLISHED"
    RETAIN = "RETAIN-ORDERED-SUPPORT-GRAPH-SLACK"
    DECLINE = "DECLINE-ORDERED-SUPPORT-GRAPH-SLACK"
    NONIDENTIFIED = "DIRECT-TARGET-BOUND-ORDER-VALUE-NONIDENTIFIED"


def publish_complete_result(
    path: Path,
    *,
    artifact_root: Path,
    bindings: EmpiricalBindings,
    result_code: ResultCode,
    complete_inference_sha256: str,
    foundation_gate_path: Path,
    foundation_gate: FoundationGate,
    opportunity_path: Path | None = None,
    opportunity: OpportunityReceipt | None = None,
    final_barrier: FinalPanelBarrier | None = None,
    final_panel: FinalPanelReceipt | None = None,
) -> str:
    """Publish exactly one complete opaque realized path, never partial values."""

    _sha256(complete_inference_sha256, "complete_inference_sha256", test_only=bindings.test_only)
    foundation_sha = _verify_foundation_gate_file(
        foundation_gate_path, foundation_gate, artifact_root=artifact_root, bindings=bindings
    )
    stage_digests: dict[str, object] = {"foundation_gate_sha256": foundation_sha}
    if foundation_gate.outcome is GateOutcome.NONPASS:
        if result_code is not ResultCode.FOUNDATION_NOT_ESTABLISHED or any(
            value is not None for value in (opportunity_path, opportunity, final_barrier, final_panel)
        ):
            raise ArtifactContractError("foundation-nonpass result has an inapplicable downstream stage")
        realized_path = "FOUNDATION_ONLY"
    else:
        if opportunity_path is None or opportunity is None:
            raise ArtifactContractError("passing foundation requires one complete opportunity receipt")
        opportunity_sha = _verify_opportunity_file(
            opportunity_path, opportunity, artifact_root=artifact_root,
            foundation_gate_sha256=foundation_sha, bindings=bindings,
        )
        stage_digests["opportunity_receipt_sha256"] = opportunity_sha
        if opportunity.outcome is GateOutcome.NONPASS:
            if result_code is not ResultCode.OPPORTUNITY_NOT_ESTABLISHED or final_barrier is not None or final_panel is not None:
                raise ArtifactContractError("opportunity-nonpass result has an inapplicable final stage")
            realized_path = "FOUNDATION_AND_OPPORTUNITY"
        else:
            if result_code not in (ResultCode.RETAIN, ResultCode.DECLINE, ResultCode.NONIDENTIFIED):
                raise ArtifactContractError("passing prerequisites require a registered final result")
            if final_barrier is None or final_panel is None:
                raise ArtifactContractError("passing prerequisites require the complete final panel")
            if (
                final_barrier.lineage_digest != bindings.lineage_digest
                or final_barrier.foundation_gate_sha256 != foundation_sha
                or final_barrier.opportunity_receipt_sha256 != opportunity_sha
            ):
                raise ArtifactContractError("final barrier cites a different realized-path lineage")
            final_panel.validate(final_barrier, bindings)
            stage_digests["final_panel_sha256"] = final_panel.complete_panel_sha256
            stage_digests["final_panel_barrier_sha256"] = final_panel.barrier_sha256
            realized_path = "FULL_FIVE_CONTROLLER_PANEL"
    payload = {
        "schema": "SCDMP_TBCC_R02_COMPLETE_REALIZED_PATH_RESULT_V1",
        **_binding_fields(bindings),
        **stage_digests,
        "realized_path": realized_path,
        "result_code": result_code.value,
        "complete_inference_sha256": complete_inference_sha256,
        "complete": True,
        "partial_values_exposed": False,
        "interpretation_included": False,
    }
    return atomic_create_json(path, payload, artifact_root=artifact_root)

"""Exact Root-lease validation and opaque permit for TBCC production.

This module can validate a Root-authored lease but cannot issue one.  Its only
permit constructor is private and reached after source, coordinate, native,
path, command, time, and resource bindings all pass.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

from .config import COMPONENT, HOST, NATIVE_ABI_VERSION
from .empirical_contract import (
    CARD_REVISION,
    CARD_SHA256,
    EMPIRICAL_STAGE,
    NATIVE_REWARD_TRACE_CONTRACT,
    PANEL_COUNTS,
    canonical_digest,
    coordinate_proposal_digest,
)


LEASE_SCHEMA: Final[str] = "SCDMP_TBCC_R02_ROOT_EMPIRICAL_LEASE_V1"
LEASE_REQUEST_SCHEMA: Final[str] = "SCDMP_TBCC_R02_ROOT_EMPIRICAL_LEASE_REQUEST_V1"
SUCCESSOR_LEASE_SCHEMA: Final[str] = (
    "SCDMP_TBCC_R02_SAME_COORDINATE_SOURCE_REPAIR_SUCCESSOR_LEASE_V1"
)
SUCCESSOR_LEASE_REQUEST_SCHEMA: Final[str] = (
    "SCDMP_TBCC_R02_SAME_COORDINATE_SOURCE_REPAIR_SUCCESSOR_REQUEST_V1"
)
REPAIR_LINEAGE_SCHEMA: Final[str] = (
    "SCDMP_TBCC_R02_SAME_COORDINATE_SOURCE_REPAIR_LINEAGE_V1"
)
RUNNER_MODULE: Final[str] = (
    "experiments.candidates.scdmp_variable_k."
    "target_bound_competent_controller_order_value.runner"
)
PYTHON_EXECUTABLE: Final[str] = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
PHASE: Final[str] = "FULL_PANEL"
ACCEPTED_WIDTHS: Final[tuple[int, ...]] = (8, 12, 32, 120, 144)
EXACT_RESOURCES: Final[dict[str, object]] = {
    "cpu_only": True,
    "gpu_count": 0,
    "independent_workers": 4,
    "native_batch_width": 144,
    "torch_threads_per_worker": 1,
    "cpu_core_hours_upper": 240,
    "ram_gib": 20,
    "scratch_gib": 10,
    "durable_artifacts_gib": 4,
    "validity_hours": 72,
}
PATH_FIELDS: Final[tuple[str, ...]] = (
    "result_root",
    "frontier_root",
    "source_manifest_path",
    "preactivity_acceptance_path",
    "run_identity_path",
    "completion_inventory_path",
    "final_result_path",
    "cm_acceptance_path",
)
PROHIBITIONS: Final[tuple[str, ...]] = (
    "stage_b",
    "relation_assay",
    "consumed_object_reuse",
    "second_surface",
    "deployment",
    "flight",
    "partial_publication",
)
_PERMIT_SEAL: Final[object] = object()
REPAIR_LINEAGE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema",
        "run_identity_sha256",
        "origin_source_manifest_sha256",
        "origin_preactivity_acceptance_sha256",
        "frozen_shared_receipt_sha256",
        "frozen_native_binding_sha256",
        "frozen_coordinate_proposal_digest",
        "coordinate_manifest_sha256",
        "empirical_identity_sha256",
        "master_commitment_sha256",
        "card_revision",
        "card_sha256",
        "replicate_namespace",
        "domain_address_schemas_sha256",
        "counts_sha256",
        "scientific_activity_started",
        "master_regenerated",
        "coordinate_domains_changed",
    }
)


class LeaseValidationError(RuntimeError):
    pass


def _parse_time(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise LeaseValidationError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise LeaseValidationError(f"{field} is not valid ISO-8601") from error
    if parsed.tzinfo is None:
        raise LeaseValidationError(f"{field} must include an offset")
    return parsed


def _hex_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise LeaseValidationError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise LeaseValidationError(f"{field} must be a SHA-256 hex digest") from error
    return value.lower()


def _resolve_paths(paths: object, repository_root: Path) -> dict[str, Path]:
    if not isinstance(paths, Mapping) or set(paths) != set(PATH_FIELDS):
        raise LeaseValidationError("lease path inventory differs")
    root = Path(repository_root).resolve()
    resolved: dict[str, Path] = {}
    for field in PATH_FIELDS:
        raw = paths.get(field)
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            raise LeaseValidationError(f"lease path {field} must be absolute")
        target = Path(raw).resolve()
        try:
            target.relative_to(root)
        except ValueError as error:
            raise LeaseValidationError(f"lease path {field} escapes repository root") from error
        resolved[field] = target
    result_root = resolved["result_root"]
    for field in PATH_FIELDS[1:]:
        try:
            relative = resolved[field].relative_to(result_root)
        except ValueError as error:
            raise LeaseValidationError(f"lease path {field} escapes result_root") from error
        if not relative.parts:
            raise LeaseValidationError(f"lease path {field} equals result_root")
    if len({str(path).casefold() for path in resolved.values()}) != len(resolved):
        raise LeaseValidationError("lease paths must be distinct")
    return resolved


def validate_repair_lineage(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != REPAIR_LINEAGE_FIELDS:
        raise LeaseValidationError("same-coordinate source-repair lineage inventory differs")
    result = dict(value)
    if result.get("schema") != REPAIR_LINEAGE_SCHEMA:
        raise LeaseValidationError("same-coordinate source-repair lineage schema differs")
    for field in (
        "run_identity_sha256",
        "origin_source_manifest_sha256",
        "origin_preactivity_acceptance_sha256",
        "frozen_shared_receipt_sha256",
        "frozen_native_binding_sha256",
        "frozen_coordinate_proposal_digest",
        "coordinate_manifest_sha256",
        "empirical_identity_sha256",
        "master_commitment_sha256",
        "card_sha256",
        "domain_address_schemas_sha256",
        "counts_sha256",
    ):
        result[field] = _hex_digest(result.get(field), field)
    if (
        result.get("card_revision") != CARD_REVISION
        or result.get("card_sha256") != CARD_SHA256
        or not isinstance(result.get("replicate_namespace"), str)
        or not str(result["replicate_namespace"]).strip()
        or result.get("scientific_activity_started") is not False
        or result.get("master_regenerated") is not False
        or result.get("coordinate_domains_changed") is not False
    ):
        raise LeaseValidationError("same-coordinate source-repair invariant differs")
    return result


def execution_argv(lease_path: Path) -> list[str]:
    target = Path(lease_path).resolve()
    if not target.is_absolute():
        raise ValueError("lease path must be absolute")
    return [PYTHON_EXECUTABLE, "-m", RUNNER_MODULE, "--phase", PHASE, "--lease", str(target)]


def lease_request(
    *,
    repository_root: Path,
    result_root: Path,
    lease_path: Path,
    source_manifest_sha256: str,
    preactivity_acceptance_sha256: str,
    native_binding_sha256: str,
) -> dict[str, object]:
    """Create a request-only packet; it is never an activity lease."""

    repo = Path(repository_root).resolve()
    result = Path(result_root).resolve()
    lease_target = Path(lease_path).resolve()
    try:
        result.relative_to(repo)
        lease_target.relative_to(repo)
    except ValueError as error:
        raise ValueError("request paths must remain inside repository root") from error
    manifest_sha = _hex_digest(source_manifest_sha256, "source_manifest_sha256")
    acceptance_sha = _hex_digest(preactivity_acceptance_sha256, "preactivity_acceptance_sha256")
    native_sha = _hex_digest(native_binding_sha256, "native_binding_sha256")
    paths = {
        "result_root": str(result),
        "frontier_root": str(result / "frontiers"),
        "source_manifest_path": str(result / "empirical_source_manifest.json"),
        "preactivity_acceptance_path": str(result / "CM_PREACTIVITY_ACCEPTANCE.json"),
        "run_identity_path": str(result / "RUN_IDENTITY.json"),
        "completion_inventory_path": str(result / "COMPLETION_INVENTORY.json"),
        "final_result_path": str(result / "COMPLETE_ATOMIC_RESULT.json"),
        "cm_acceptance_path": str(result / "CM_TECHNICAL_ACCEPTANCE.json"),
    }
    return {
        "schema": LEASE_REQUEST_SCHEMA,
        "authority": "REQUEST_ONLY",
        "lease_issued": False,
        "activity_authorized": False,
        "stage": EMPIRICAL_STAGE,
        "phase": PHASE,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "component": COMPONENT,
        "host": HOST,
        "abi_version": NATIVE_ABI_VERSION,
        "source_manifest_sha256": manifest_sha,
        "coordinate_proposal_digest": coordinate_proposal_digest(manifest_sha),
        "preactivity_acceptance_sha256": acceptance_sha,
        "native_binding_sha256": native_sha,
        "native_trace_contract_sha256": canonical_digest(NATIVE_REWARD_TRACE_CONTRACT),
        "paths": paths,
        "execution": {"module": RUNNER_MODULE, "argv": execution_argv(lease_target)},
        "resources": dict(EXACT_RESOURCES),
        "counts": dict(PANEL_COUNTS),
        "complete_panel_only": True,
        "prohibitions": list(PROHIBITIONS),
        "production_launch": False,
    }


def successor_lease_request(
    *,
    repository_root: Path,
    result_root: Path,
    lease_path: Path,
    source_manifest_sha256: str,
    preactivity_acceptance_sha256: str,
    native_binding_sha256: str,
    same_coordinate_repair_lineage: Mapping[str, object],
) -> dict[str, object]:
    """Build the exact request-only same-coordinate source-repair successor."""

    base = lease_request(
        repository_root=repository_root,
        result_root=result_root,
        lease_path=lease_path,
        source_manifest_sha256=source_manifest_sha256,
        preactivity_acceptance_sha256=preactivity_acceptance_sha256,
        native_binding_sha256=native_binding_sha256,
    )
    lineage = validate_repair_lineage(same_coordinate_repair_lineage)
    if (
        base["source_manifest_sha256"] == lineage["origin_source_manifest_sha256"]
        or base["preactivity_acceptance_sha256"]
        == lineage["origin_preactivity_acceptance_sha256"]
    ):
        raise LeaseValidationError(
            "successor request requires distinct current source and acceptance"
        )
    base["schema"] = SUCCESSOR_LEASE_REQUEST_SCHEMA
    base["lease_kind"] = "UNCHANGED_SCIENCE_SAME_COORDINATE_SOURCE_REPAIR"
    base["same_coordinate_repair_lineage"] = lineage
    return base


@dataclass(frozen=True, repr=False)
class ActivityPermit:
    lease_id: str
    expires_at: datetime
    source_manifest_sha256: str
    coordinate_proposal_digest: str
    preactivity_acceptance_sha256: str
    native_binding_sha256: str
    native_trace_contract_sha256: str
    paths: Mapping[str, str]
    workers: int
    native_batch_width: int
    same_coordinate_repair_lineage: Mapping[str, object] | None = None
    _seal: object | None = None

    def require_active(self, *, now: datetime | None = None) -> None:
        if self._seal is not _PERMIT_SEAL:
            raise LeaseValidationError("activity permit was not produced by exact lease validation")
        checked = now if now is not None else datetime.now(self.expires_at.tzinfo)
        if checked.tzinfo is None or checked >= self.expires_at:
            raise LeaseValidationError("activity permit is expired or validation time is naive")


def validate_root_lease(
    lease: Mapping[str, object],
    *,
    now: datetime,
    repository_root: Path,
    lease_path: Path,
    source_manifest_sha256: str,
    preactivity_acceptance_sha256: str,
    native_binding: Mapping[str, object],
    shared_guard: Callable[..., Mapping[str, object]],
    frozen_identity_lineage: Mapping[str, object] | None = None,
) -> ActivityPermit:
    """Validate every exact binding and only then produce an opaque permit."""

    required = {
        "schema", "lease_id", "authority", "activity_authorized", "stage", "phase",
        "card_revision", "card_sha256", "component", "host", "abi_version",
        "source_manifest_sha256", "coordinate_proposal_digest",
        "preactivity_acceptance_sha256", "native_binding_sha256",
        "native_trace_contract_sha256", "paths",
        "execution", "resources", "counts", "complete_panel_only", "prohibitions",
        "issued_at", "expires_at",
    }
    successor = lease.get("schema") == SUCCESSOR_LEASE_SCHEMA
    if successor:
        required |= {"lease_kind", "same_coordinate_repair_lineage"}
    if not isinstance(lease, Mapping) or set(lease) != required:
        raise LeaseValidationError("Root lease field inventory differs")
    exact = {
        "schema": SUCCESSOR_LEASE_SCHEMA if successor else LEASE_SCHEMA,
        "authority": "OPERATIONAL_ROOT",
        "activity_authorized": True,
        "stage": EMPIRICAL_STAGE,
        "phase": PHASE,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "component": COMPONENT,
        "host": HOST,
        "abi_version": NATIVE_ABI_VERSION,
        "resources": EXACT_RESOURCES,
        "counts": PANEL_COUNTS,
        "complete_panel_only": True,
        "prohibitions": list(PROHIBITIONS),
    }
    for field, expected in exact.items():
        if lease.get(field) != expected:
            raise LeaseValidationError(f"Root lease field {field!r} differs")
    if not isinstance(lease.get("lease_id"), str) or not str(lease["lease_id"]).strip():
        raise LeaseValidationError("Root lease_id is absent")
    manifest_sha = _hex_digest(source_manifest_sha256, "source_manifest_sha256")
    acceptance_sha = _hex_digest(preactivity_acceptance_sha256, "preactivity_acceptance_sha256")
    native_sha = canonical_digest(dict(native_binding))
    bindings = {
        "source_manifest_sha256": manifest_sha,
        "coordinate_proposal_digest": coordinate_proposal_digest(manifest_sha),
        "preactivity_acceptance_sha256": acceptance_sha,
        "native_binding_sha256": native_sha,
        "native_trace_contract_sha256": canonical_digest(NATIVE_REWARD_TRACE_CONTRACT),
    }
    for field, expected in bindings.items():
        if lease.get(field) != expected:
            raise LeaseValidationError(f"Root lease binding {field!r} differs")
    repair_lineage: dict[str, object] | None = None
    if successor:
        if lease.get("lease_kind") != "UNCHANGED_SCIENCE_SAME_COORDINATE_SOURCE_REPAIR":
            raise LeaseValidationError("successor lease kind differs")
        repair_lineage = validate_repair_lineage(
            lease.get("same_coordinate_repair_lineage")
        )
        observed_lineage = validate_repair_lineage(frozen_identity_lineage)
        if repair_lineage != observed_lineage:
            raise LeaseValidationError("successor lease frozen identity lineage differs")
        if (
            repair_lineage["origin_source_manifest_sha256"] == manifest_sha
            or repair_lineage["origin_preactivity_acceptance_sha256"] == acceptance_sha
            or repair_lineage["frozen_native_binding_sha256"] != native_sha
        ):
            raise LeaseValidationError("successor current/origin/native lineage differs")
    elif frozen_identity_lineage is not None:
        observed_lineage = validate_repair_lineage(frozen_identity_lineage)
        if (
            observed_lineage["origin_source_manifest_sha256"] != manifest_sha
            or observed_lineage["origin_preactivity_acceptance_sha256"]
            != acceptance_sha
        ):
            raise LeaseValidationError(
                "V1 lease cannot authorize a source-repaired frozen identity"
            )
    paths = _resolve_paths(lease.get("paths"), Path(repository_root))
    execution = lease.get("execution")
    expected_execution = {"module": RUNNER_MODULE, "argv": execution_argv(Path(lease_path))}
    if execution != expected_execution:
        raise LeaseValidationError("Root lease argv/module binding differs")
    issued = _parse_time(lease.get("issued_at"), "issued_at")
    expires = _parse_time(lease.get("expires_at"), "expires_at")
    if now.tzinfo is None or not issued <= now < expires:
        raise LeaseValidationError("Root lease is not active at validation time")
    if (expires - issued).total_seconds() > int(EXACT_RESOURCES["validity_hours"]) * 3600:
        raise LeaseValidationError("Root lease validity exceeds the exact resource request")

    # The shared guard is deliberately last: malformed authority cannot trigger
    # native loading.  The exact admitted width and no-fallback receipt are then
    # compared with the already accepted candidate-native binding.
    receipt = dict(
        shared_guard(
            COMPONENT,
            backend="cpp",
            batch_width=int(EXACT_RESOURCES["native_batch_width"]),
            build_root=None,
        )
    )
    shared_native = receipt.get("native")
    if (
        receipt.get("component") != COMPONENT
        or receipt.get("backend") != "cpp"
        or receipt.get("batch_width") != 144
        or receipt.get("full_reset_step_cpp") is not True
        or receipt.get("python_fallback") is not False
        or not isinstance(shared_native, Mapping)
        or shared_native.get("artifact_sha256") != native_binding.get("artifact_sha256")
    ):
        raise LeaseValidationError("live shared C++ production guard differs from native binding")
    return ActivityPermit(
        lease_id=str(lease["lease_id"]),
        expires_at=expires,
        source_manifest_sha256=manifest_sha,
        coordinate_proposal_digest=str(
            repair_lineage["frozen_coordinate_proposal_digest"]
            if repair_lineage is not None
            else bindings["coordinate_proposal_digest"]
        ),
        preactivity_acceptance_sha256=acceptance_sha,
        native_binding_sha256=native_sha,
        native_trace_contract_sha256=canonical_digest(NATIVE_REWARD_TRACE_CONTRACT),
        paths={field: str(path) for field, path in paths.items()},
        workers=4,
        native_batch_width=144,
        same_coordinate_repair_lineage=repair_lineage,
        _seal=_PERMIT_SEAL,
    )

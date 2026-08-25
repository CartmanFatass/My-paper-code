"""Identity-free preactivity/native acceptance boundary for TBCC r02."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final

from .config import COMPONENT, FUNCTIONAL_BATCH_WIDTHS, HOST, NATIVE_ABI_VERSION
from .empirical_contract import (
    CARD_REVISION,
    CARD_SHA256,
    EMPIRICAL_STAGE,
    NATIVE_REWARD_TRACE_CONTRACT,
    PANEL_COUNTS,
    canonical_digest,
    coordinate_proposal,
    validate_coordinate_proposal,
)
from .source_manifest import (
    ACCEPTED_NATIVE_ARTIFACT_SHA256,
    ACCEPTED_NATIVE_ARTIFACT_SIZE,
    ACCEPTED_NATIVE_BUILD_KEY,
    ACCEPTED_NATIVE_SOURCE_SHA256,
    manifest_digest,
    stable_native_binding,
    validate_source_manifest,
)


PREACTIVITY_SCHEMA: Final[str] = "SCDMP_TBCC_R02_PREACTIVITY_ACCEPTANCE_V1"
ACCEPTED_SHARED_WIDTHS: Final[tuple[int, ...]] = (8, 12, 32, 120, 144)


class PreactivityError(RuntimeError):
    pass


def require_direction_cpp_batched_production(
    *,
    batch_width: int,
    shared_guard: Callable[..., Mapping[str, object]] | None = None,
    candidate_identity: Callable[[], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    if batch_width not in ACCEPTED_SHARED_WIDTHS:
        raise PreactivityError("TBCC production width is not in the accepted shared width set")
    if shared_guard is None:
        from envs.native.production_backend import require_cpp_batched_production

        shared_guard = require_cpp_batched_production
    if candidate_identity is None:
        from .native_backend import native_artifact_identity

        candidate_identity = native_artifact_identity
    shared = dict(
        shared_guard(
            COMPONENT, backend="cpp", batch_width=batch_width, build_root=None
        )
    )
    local = dict(candidate_identity())
    shared_native = shared.get("native")
    exact_local = {
        "component": COMPONENT,
        "host": HOST,
        "abi_version": NATIVE_ABI_VERSION,
        "fixture_magic": 6071489204069610049,
        "max_batch_width": 144,
        "functional_batch_widths": list(FUNCTIONAL_BATCH_WIDTHS),
        "source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "build_key": ACCEPTED_NATIVE_BUILD_KEY,
        "artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
        "artifact_size": ACCEPTED_NATIVE_ARTIFACT_SIZE,
        "full_reset_step_cpp": True,
        "python_fallback": False,
    }
    for field, expected in exact_local.items():
        if local.get(field) != expected:
            raise PreactivityError(f"candidate native field {field!r} differs")
    if (
        shared.get("component") != COMPONENT
        or shared.get("backend") != "cpp"
        or shared.get("batch_width") != batch_width
        or shared.get("full_reset_step_cpp") is not True
        or shared.get("python_fallback") is not False
        or not isinstance(shared_native, Mapping)
        or shared_native.get("binding_kind") != "ctypes_cdll"
        or shared_native.get("artifact_sha256") != local.get("artifact_sha256")
    ):
        raise PreactivityError("shared and candidate-local C++ identities differ")
    return {
        "schema": "SCDMP_TBCC_R02_CPP_BATCHED_PREACTIVITY_V1",
        "component": COMPONENT,
        "host": HOST,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "backend": "cpp",
        "batch_width": batch_width,
        "full_reset_step_cpp": True,
        "python_fallback": False,
        "shared": shared,
        "native": local,
        "native_reward_trace": dict(NATIVE_REWARD_TRACE_CONTRACT),
        "native_binding_sha256": canonical_digest(local),
    }


def build_preactivity_acceptance(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    native_identity: Mapping[str, object],
    native_receipt: Mapping[str, object],
    coordinate: Mapping[str, object],
    efficiency_evidence_sha256: str,
    validation: Mapping[str, object],
) -> dict[str, object]:
    """Build an identity-free acceptance value without persisting it."""

    validated_manifest = validate_source_manifest(
        source_manifest, repository_root, native_identity=native_identity
    )
    manifest_sha = manifest_digest(validated_manifest)
    validate_coordinate_proposal(coordinate, source_manifest_sha256=manifest_sha)
    stable_native = stable_native_binding(native_identity)
    if native_receipt.get("native") != dict(native_identity):
        raise PreactivityError("preactivity native receipt differs from source-manifest binding")
    if not isinstance(efficiency_evidence_sha256, str) or len(efficiency_evidence_sha256) != 64:
        raise PreactivityError("efficiency evidence SHA-256 is absent")
    try:
        int(efficiency_evidence_sha256, 16)
    except ValueError as error:
        raise PreactivityError("efficiency evidence SHA-256 is not hexadecimal") from error
    required_validation = {
        "runner_to_card_counts": True,
        "controller_and_optimizer_arithmetic": True,
        "analyzer_branch_inventory": True,
        "worker_equivalence_1_2_4": True,
        "malformed_input_fail_closed": True,
        "interrupted_frontier_fail_closed": True,
        "atomic_io_and_resume": True,
        "end_to_end_result_blind_efficiency": True,
    }
    if dict(validation) != required_validation:
        raise PreactivityError("preactivity validation inventory is incomplete or extended")
    return {
        "schema": PREACTIVITY_SCHEMA,
        "accepted": True,
        "stage": EMPIRICAL_STAGE,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "component": COMPONENT,
        "host": HOST,
        "source_manifest_sha256": manifest_sha,
        "coordinate_proposal": coordinate_proposal(manifest_sha),
        "coordinate_proposal_digest": canonical_digest(coordinate),
        "native_binding": stable_native,
        "native_binding_sha256": canonical_digest(stable_native),
        "native_reward_trace": dict(NATIVE_REWARD_TRACE_CONTRACT),
        "efficiency_evidence_sha256": efficiency_evidence_sha256.lower(),
        "validation": required_validation,
        "counts": dict(PANEL_COUNTS),
        "materialized": False,
        "master_present": False,
        "empirical_objects_present": False,
        "lease_issued": False,
        "activity_authorized": False,
        "question_relevant_output": False,
    }


def validate_preactivity_acceptance(
    value: Mapping[str, object],
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    native_identity: Mapping[str, object],
    native_receipt: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise PreactivityError("preactivity acceptance mapping is absent")
    validation = value.get("validation")
    if not isinstance(validation, Mapping):
        raise PreactivityError("preactivity validation inventory is absent")
    rebuilt = build_preactivity_acceptance(
        repository_root=repository_root,
        source_manifest=source_manifest,
        native_identity=native_identity,
        native_receipt=native_receipt,
        coordinate=value.get("coordinate_proposal", {}),
        efficiency_evidence_sha256=str(value.get("efficiency_evidence_sha256", "")),
        validation=validation,
    )
    if dict(value) != rebuilt:
        raise PreactivityError("preactivity acceptance differs from the frozen identity-free schema")
    return rebuilt

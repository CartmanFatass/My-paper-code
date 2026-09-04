"""Exact current-authority lifecycle binding for one unchanged RISP RSS slice.

Validation is deliberately result-blind.  It hashes immutable technical
parents, counts only ``*.commit.json`` directory entries, and tests only the
existence of the complete-result path.  Frontier commits, checkpoints,
results, and partial-value payloads are never opened here.

Importing or validating this module never launches work.  ``main`` is the
single exact executable seam reserved for a separately admitted Experiment
Operator.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

try:
    from . import g_init_r01_coordinate_certificate as certificate_spec
    from . import g_init_r01_rss_successor as successor
    from . import run_g_init_r01_rss_source_reacceptance as source_reacceptance
except ImportError:
    import g_init_r01_coordinate_certificate as certificate_spec
    import g_init_r01_rss_successor as successor
    import run_g_init_r01_rss_source_reacceptance as source_reacceptance


ROOT = Path(__file__).resolve().parents[3]
WRAPPER_PATH = Path(__file__).resolve()
INTERPRETER = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"

CURRENT_LEASE_ID = "RISP-G-INIT-REACH-R01-ROOT-EMPIRICAL-20260823-04"
CURRENT_LEASE_PATH = Path(
    "C:/Projects/HMASD/temp/leases/"
    "RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260823_04.json"
)
CURRENT_LEASE_SHA256 = "f5e6c1b25b7d45cd447c0e4be44988abc3fe5f4bb3f3eb31c5b931cf5a0c18b2"

CONSUMED_SUCCESSOR_ID = "RISP-G-INIT-REACH-R01-ROOT-EMPIRICAL-20260821-02"
CONSUMED_SUCCESSOR_PATH = Path(
    "C:/Projects/HMASD/temp/leases/"
    "RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260821_02.json"
)
DIRECT_PREDECESSOR_PATH = Path(
    "C:/Projects/HMASD/temp/leases/"
    "RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260823_03.json"
)
DIRECT_PREDECESSOR_SHA256 = "5490bf1cbfdda72ecf475a7f93e401ecaf9638a892e69ff1b1a140253d63808c"

SOURCE_REACCEPTANCE_PATH = source_reacceptance.REACCEPTANCE_PATH
SOURCE_REACCEPTANCE_SHA256 = "76f1208e0e7dcee1213a916ea26348c31a09c9425917c97d2c75f11121780f5f"
ORIGINAL_CERTIFICATE_PATH = certificate_spec.PRODUCTION_CERTIFICATE
ORIGINAL_CERTIFICATE_SHA256 = "2d7339ad9c103cd9f0ed398b644d03c59f4d561aa0b3649e1d1bab14b93421a2"
ORIGINAL_PREDECESSOR_PATH = successor.PREDECESSOR_LEASE
ORIGINAL_PREDECESSOR_SHA256 = "6a92243cd3e9b8960688eee94b6a3015b90d54ee9a580352df699c6401aea69b"
BACKEND_ACCEPTANCE_PATH = certificate_spec.BACKEND_ACCEPTANCE
BACKEND_ACCEPTANCE_SHA256 = "7d1f170c2090e145af60753fa4619f7da41f3de63f769c996e3fce8e01764a20"

FRONTIER_PATH = certificate_spec.PRODUCTION_FRONTIER
FRONTIER_MANIFEST_PATH = FRONTIER_PATH / "manifest.json"
FRONTIER_MANIFEST_SHA256 = "8ffcf4b19281af8054aeb1cdc2eaa55a7899de6540da3b26100d00ae71f00e6f"
BLINDED_COMMIT_COUNT = 26
FULL_PANEL_COUNT = 352
RESULT_ROOT = certificate_spec.PRODUCTION_RESULT_ROOT
COMPLETE_RESULT_PATH = RESULT_ROOT / certificate_spec.RESULT_NAME

UNIT_PLAN_SHA256 = "8d1c8d9da3e96ebef62c82a15a2d558d1584a65c33252a09e5892b27db3a138b"
CANONICAL_WORKER_PAYLOAD_SHA256 = "1a9d4328be262f7458ab1e6887191229909aa3fce43f49a718dd0b23eae69139"
ATOMIC_INSTALL_ORDER = "parent_all_success_then_plan_order"
RENEWAL_BASIS = (
    "Operational Root distinct current-authority same-object lease; same frozen "
    "coordinate/frontier/payload/order/RNG/resources; direct consumed predecessor 20260823_03"
)

RESOURCES = {
    "process_concurrency": 2,
    "cpu_workers": 2,
    "cpu_cores": 2,
    "gpu": False,
    "complete_cpu_hours_upper": 32,
    "complete_wall_seconds_upper": 86400,
    "per_worker_rss_limit_bytes": 1073741824,
    "process_group_rss_limit_bytes": 2684354560,
    "slice_wall_seconds": 13800,
    "resumable_only": True,
}


class CurrentAuthorityValidationError(RuntimeError):
    pass


def _read_bytes(path: Path, label: str) -> bytes:
    if not path.is_file():
        raise CurrentAuthorityValidationError(f"{label} is absent: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise CurrentAuthorityValidationError(f"{label} cannot be read: {path}") from error


def _sha(path: Path, label: str) -> str:
    return hashlib.sha256(_read_bytes(path, label)).hexdigest()


def _require_sha(path: Path, expected: str, label: str) -> None:
    if _sha(path.resolve(), label) != expected:
        raise CurrentAuthorityValidationError(f"{label} SHA-256 differs from the exact binding")


def _read_lease(path: Path) -> dict[str, Any]:
    payload = _read_bytes(path, "current-authority lease")
    if hashlib.sha256(payload).hexdigest() != CURRENT_LEASE_SHA256:
        raise CurrentAuthorityValidationError("current-authority lease SHA-256 differs from the exact binding")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CurrentAuthorityValidationError("current-authority lease is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise CurrentAuthorityValidationError("current-authority lease must be a JSON object")
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_read_bytes(path, label).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CurrentAuthorityValidationError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise CurrentAuthorityValidationError(f"{label} must be a JSON object")
    return value


def _strict_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise CurrentAuthorityValidationError(f"{field} must use strict raw UTC seconds")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise CurrentAuthorityValidationError(f"{field} must use strict raw UTC seconds") from error


def _path_text(path: Path) -> str:
    return str(path.resolve())


def _expected_downstream_command() -> str:
    return successor.successor_command(
        certificate=ORIGINAL_CERTIFICATE_PATH,
        frontier=FRONTIER_PATH,
        result_root=RESULT_ROOT,
        successor_acceptance=SOURCE_REACCEPTANCE_PATH,
        successor_lease=CURRENT_LEASE_PATH,
    )


def operator_argv() -> tuple[str, str]:
    """Return the exact outer executable binding without executing it."""
    return INTERPRETER, _path_text(WRAPPER_PATH)


def _expected_lease() -> dict[str, Any]:
    return {
        "schema": successor.SUCCESSOR_LEASE_SCHEMA,
        "lease_id": CURRENT_LEASE_ID,
        "direction_id": certificate_spec.DIRECTION_ID,
        "stage_id": certificate_spec.STAGE_ID,
        "exact_object_revision": certificate_spec.OBJECT_REVISION,
        "production_authorized": True,
        "issued_at": "2026-08-23T14:34:51Z",
        "not_after": "2026-08-24T14:34:51Z",
        "predecessor_lease": {
            "path": _path_text(DIRECT_PREDECESSOR_PATH),
            "sha256": DIRECT_PREDECESSOR_SHA256,
        },
        "successor_acceptance": {
            "path": _path_text(SOURCE_REACCEPTANCE_PATH),
            "sha256": SOURCE_REACCEPTANCE_SHA256,
        },
        "immutable_lineage": {
            "original_certificate": {
                "path": _path_text(ORIGINAL_CERTIFICATE_PATH),
                "sha256": ORIGINAL_CERTIFICATE_SHA256,
            },
            "predecessor_lease": {
                "path": _path_text(ORIGINAL_PREDECESSOR_PATH),
                "sha256": ORIGINAL_PREDECESSOR_SHA256,
            },
        },
        "backend_acceptance": {
            "path": _path_text(BACKEND_ACCEPTANCE_PATH),
            "sha256": BACKEND_ACCEPTANCE_SHA256,
        },
        "certificate": _path_text(ORIGINAL_CERTIFICATE_PATH),
        "frontier": _path_text(FRONTIER_PATH),
        "result_root": _path_text(RESULT_ROOT),
        "result": _path_text(COMPLETE_RESULT_PATH),
        "command": _expected_downstream_command(),
        "resources": RESOURCES,
        "zero_commit_frontier": {
            "commit_count": 0,
            "result_absent": True,
            "manifest_path": _path_text(FRONTIER_MANIFEST_PATH),
            "manifest_sha256": FRONTIER_MANIFEST_SHA256,
        },
        "renewal_basis": RENEWAL_BASIS,
    }


def _validate_accepted_lineage(accepted: dict[str, Any]) -> None:
    parents = accepted.get("parents") if isinstance(accepted.get("parents"), dict) else {}
    whitelist = accepted.get("whitelist") if isinstance(accepted.get("whitelist"), dict) else {}
    expected_parents = {
        "original_certificate": {
            "path": _path_text(ORIGINAL_CERTIFICATE_PATH),
            "sha256": ORIGINAL_CERTIFICATE_SHA256,
        },
        "predecessor_lease": {
            "path": _path_text(ORIGINAL_PREDECESSOR_PATH),
            "sha256": ORIGINAL_PREDECESSOR_SHA256,
            "validity_reinterpreted": False,
        },
        "backend_acceptance": {
            "path": _path_text(BACKEND_ACCEPTANCE_PATH),
            "sha256": BACKEND_ACCEPTANCE_SHA256,
        },
    }
    if (
        accepted.get("direction_id") != certificate_spec.DIRECTION_ID
        or accepted.get("exact_object_revision") != certificate_spec.OBJECT_REVISION
        or accepted.get("technical_lineage_only") is not True
        or accepted.get("science_revision_changed") is not False
        or accepted.get("production_coordinate_serialized") is not False
        or accepted.get("production_coordinate_read_by_successor") is not False
        or any(parents.get(key) != value for key, value in expected_parents.items())
        or whitelist.get("successor_resources") != RESOURCES
        or whitelist.get("unchanged_unit_plan_sha256") != UNIT_PLAN_SHA256
        or whitelist.get("unchanged_canonical_worker_payload_sha256") != CANONICAL_WORKER_PAYLOAD_SHA256
        or whitelist.get("atomic_install_order") != ATOMIC_INSTALL_ORDER
        or whitelist.get("rng_event_native_identity_unchanged") is not True
        or whitelist.get("unchanged_original_runner_core") is not True
        or whitelist.get("unchanged_worker_loop") is not True
    ):
        raise CurrentAuthorityValidationError("accepted technical lineage differs from the unchanged binding")


def _current_accepted_view() -> dict[str, Any]:
    """Reconcile current shared-registry bytes by exact RISP semantics only.

    The historical source reacceptance remains immutable ancestry.  Later
    RCLE-only registry additions changed its shared file hash, so current RISP
    admission must not pretend those bytes are still identical.  This view
    revalidates every protected RISP source plus the native/capability semantic
    projection accepted by that artifact; it grants no new science.
    """
    packet = _read_json(SOURCE_REACCEPTANCE_PATH, "source reacceptance")
    if (
        packet.get("schema") != source_reacceptance.REACCEPTANCE_SCHEMA
        or packet.get("direction_id") != certificate_spec.DIRECTION_ID
        or packet.get("exact_object_revision") != certificate_spec.OBJECT_REVISION
        or packet.get("technical_only") is not True
        or packet.get("science_revision_changed") is not False
        or packet.get("coordinate_or_result_accessed") is not False
    ):
        raise CurrentAuthorityValidationError("source reacceptance technical fence differs")

    prior = packet.get("prior_acceptance") if isinstance(packet.get("prior_acceptance"), dict) else {}
    prior_path = Path(prior.get("path", ""))
    if prior_path.resolve() != source_reacceptance.PRIOR_ACCEPTANCE.resolve():
        raise CurrentAuthorityValidationError("source reacceptance prior path differs")
    prior_sha = prior.get("sha256")
    if not isinstance(prior_sha, str):
        raise CurrentAuthorityValidationError("source reacceptance prior SHA-256 is absent")
    _require_sha(prior_path, prior_sha, "prior successor acceptance")
    base = _read_json(prior_path, "prior successor acceptance")
    parents = base.get("parents") if isinstance(base.get("parents"), dict) else {}

    drift = packet.get("registry_drift") if isinstance(packet.get("registry_drift"), dict) else {}
    registry_path = source_reacceptance.REGISTRY_PATH
    base_registry = parents.get("shared_registry_lineage") if isinstance(parents.get("shared_registry_lineage"), dict) else {}
    if (
        Path(drift.get("path", "")).resolve() != registry_path.resolve()
        or drift.get("prior_accepted_current_sha256") != base_registry.get("current_sha256")
        or packet.get("native_semantic_identity") != parents.get("native_semantic_identity")
        or packet.get("shared_component_semantic_identity") != parents.get("shared_component_semantic_identity")
        or packet.get("zero_commit_frontier") != parents.get("zero_commit_frontier")
    ):
        raise CurrentAuthorityValidationError("source reacceptance does not chain from accepted RISP lineage")

    successor_sources = base.get("successor_sources") if isinstance(base.get("successor_sources"), dict) else {}
    successor_tests = base.get("successor_tests") if isinstance(base.get("successor_tests"), dict) else {}
    for path_text, digest in {**successor_sources, **successor_tests}.items():
        _require_sha(Path(path_text), digest, "historical successor source")

    original_manifest = parents.get("original_source_manifest")
    entries = original_manifest.get("entries") if isinstance(original_manifest, dict) else {}
    if not isinstance(entries, dict):
        raise CurrentAuthorityValidationError("accepted original source manifest is absent")
    for path_text, digest in entries.items():
        source_path = Path(path_text)
        if source_path.resolve() != registry_path.resolve():
            _require_sha(source_path, digest, "protected RISP source")

    observed = successor.native_backend.production_preflight(batch_width=32)
    native = successor._local_native_semantics(observed.get("local"))
    shared = successor.resume._shared_preflight_semantics(observed.get("shared"))
    if (
        native != packet.get("native_semantic_identity")
        or shared != packet.get("shared_component_semantic_identity")
    ):
        raise CurrentAuthorityValidationError("live RISP native semantic identity differs")

    from envs.native import production_backend

    capability = production_backend.backend_capability(production_backend.RISP_G_INIT_REACH_R01_FULL_HOST)
    if {
        "production_backend": capability.production_backend,
        "batch_api": capability.batch_api,
        "minimum_production_batch_width": capability.minimum_production_batch_width,
        "full_reset_step_cpp": capability.full_reset_step_cpp,
        "loader_key": capability.loader_key,
        "native_boundary": capability.native_boundary,
    } != {
        "production_backend": "cpp",
        "batch_api": True,
        "minimum_production_batch_width": 1,
        "full_reset_step_cpp": True,
        "loader_key": "risp_g_init_reach_r01_full_host",
        "native_boundary": packet["shared_component_semantic_identity"]["native_boundary"],
    }:
        raise CurrentAuthorityValidationError("live shared registry RISP capability differs")

    accepted = deepcopy(base)
    accepted["parents"]["shared_registry_lineage"]["current_sha256"] = _sha(
        registry_path, "current shared registry"
    )
    return accepted


def _validate_live_blinded_frontier() -> None:
    _require_sha(FRONTIER_MANIFEST_PATH, FRONTIER_MANIFEST_SHA256, "frontier manifest")
    # Directory enumeration and metadata only: never read a commit payload.
    commit_count = sum(1 for path in FRONTIER_PATH.rglob("*.commit.json") if path.is_file())
    if commit_count != BLINDED_COMMIT_COUNT:
        raise CurrentAuthorityValidationError(
            f"blinded frontier filename count is not {BLINDED_COMMIT_COUNT}/{FULL_PANEL_COUNT}"
        )
    if COMPLETE_RESULT_PATH.exists():
        raise CurrentAuthorityValidationError("complete result must remain absent at admission")


def validate_current_authority_binding(
    *, now: datetime | None = None, lease_path: Path | None = None
) -> dict[str, Any]:
    """Validate the exact fresh binding without launching or reading values."""
    path = CURRENT_LEASE_PATH if lease_path is None else lease_path
    if path.resolve() != CURRENT_LEASE_PATH.resolve():
        raise CurrentAuthorityValidationError("current-authority lease path is exact")
    if (
        CURRENT_LEASE_ID == CONSUMED_SUCCESSOR_ID
        or path.resolve() in {CONSUMED_SUCCESSOR_PATH.resolve(), DIRECT_PREDECESSOR_PATH.resolve()}
    ):
        raise CurrentAuthorityValidationError("historical consumed authority cannot be executable")

    lease = _read_lease(path.resolve())
    if lease != _expected_lease():
        raise CurrentAuthorityValidationError("current-authority lease fields differ from the exact binding")

    _require_sha(DIRECT_PREDECESSOR_PATH, DIRECT_PREDECESSOR_SHA256, "direct consumed predecessor")
    _require_sha(SOURCE_REACCEPTANCE_PATH, SOURCE_REACCEPTANCE_SHA256, "source reacceptance")
    _require_sha(ORIGINAL_CERTIFICATE_PATH, ORIGINAL_CERTIFICATE_SHA256, "original certificate")
    _require_sha(ORIGINAL_PREDECESSOR_PATH, ORIGINAL_PREDECESSOR_SHA256, "original predecessor")
    _require_sha(BACKEND_ACCEPTANCE_PATH, BACKEND_ACCEPTANCE_SHA256, "backend acceptance")

    accepted = _current_accepted_view()
    _validate_accepted_lineage(accepted)

    issued_at = _strict_utc(lease.get("issued_at"), "issued_at")
    not_after = _strict_utc(lease.get("not_after"), "not_after")
    observed = datetime.now(timezone.utc) if now is None else now
    if observed.tzinfo is None:
        raise CurrentAuthorityValidationError("admission time must be timezone-aware")
    observed = observed.astimezone(timezone.utc)
    if issued_at > observed or observed >= not_after:
        raise CurrentAuthorityValidationError("current-authority lease is future-issued or expired")
    if (not_after - observed).total_seconds() < RESOURCES["slice_wall_seconds"]:
        raise CurrentAuthorityValidationError("current-authority lease lacks one complete slice")

    _validate_live_blinded_frontier()
    return {
        "lease_id": CURRENT_LEASE_ID,
        "lease_path": _path_text(CURRENT_LEASE_PATH),
        "lease_sha256": CURRENT_LEASE_SHA256,
        "complete_slice_remaining": True,
        "blinded_frontier": f"{BLINDED_COMMIT_COUNT}/{FULL_PANEL_COUNT}",
        "complete_result_absent": True,
        "downstream_command": lease["command"],
        "operator_argv": operator_argv(),
        "result_blind": True,
    }


def invoke_operator_owned_slice() -> int:
    """Invoke the unchanged runner; caller must be the separately admitted Operator."""
    validate_current_authority_binding()
    accepted = _current_accepted_view()
    original_acceptance = successor.SUCCESSOR_ACCEPTANCE
    original_lease = successor.SUCCESSOR_LEASE
    original_lease_id = successor.SUCCESSOR_LEASE_ID
    original_validator = successor.validate_successor_acceptance

    def accepted_view(path: Path, *, test_only: bool = False) -> dict[str, Any]:
        del test_only
        if path.resolve() != SOURCE_REACCEPTANCE_PATH.resolve():
            raise CurrentAuthorityValidationError("unexpected source-reacceptance path")
        return accepted

    try:
        successor.SUCCESSOR_ACCEPTANCE = SOURCE_REACCEPTANCE_PATH.resolve()
        successor.SUCCESSOR_LEASE = CURRENT_LEASE_PATH.resolve()
        successor.SUCCESSOR_LEASE_ID = CURRENT_LEASE_ID
        successor.validate_successor_acceptance = accepted_view
        return successor.invoke_unchanged_runner(
            certificate=ORIGINAL_CERTIFICATE_PATH,
            frontier=FRONTIER_PATH,
            result_root=RESULT_ROOT,
            successor_acceptance=SOURCE_REACCEPTANCE_PATH,
            successor_lease=CURRENT_LEASE_PATH,
        )
    finally:
        successor.SUCCESSOR_ACCEPTANCE = original_acceptance
        successor.SUCCESSOR_LEASE = original_lease
        successor.SUCCESSOR_LEASE_ID = original_lease_id
        successor.validate_successor_acceptance = original_validator


def main() -> int:
    if len(sys.argv) != 1:
        raise CurrentAuthorityValidationError("current-authority wrapper accepts no mutable arguments")
    return invoke_operator_owned_slice()


if __name__ == "__main__":
    raise SystemExit(main())

"""Whitelist-only RSS technical successor for the frozen RISP G-init R01 run.

This module never constructs or reads a coordinate value.  It binds immutable
parents by path and SHA-256, validates the exact 2.5-GiB successor lease, and
temporarily adapts validator/command constants so the byte-identical original
runner core executes.  The original certificate and predecessor lease remain
immutable lineage.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterator, Mapping

_CANDIDATE_DIR = Path(__file__).resolve().parent
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))
if str(_CANDIDATE_DIR) not in sys.path:
    sys.path.insert(0, str(_CANDIDATE_DIR))
import g_init_r01_coordinate_certificate as certificate_spec
import g_init_r01_native_backend as native_backend
import g_init_r01_resume as resume


ROOT = Path(__file__).resolve().parents[3]
MARKER = "PORTFOLIO_EM_TO_ROOT_CM_RISP_G_INIT_REACH_R01_RSS_VALIDATOR_SUCCESSOR_20260821"
SUCCESSOR_SCHEMA = "RISP-G-INIT-REACH-R01-RSS-TECHNICAL-SUCCESSOR-ACCEPTANCE-V1"
SUCCESSOR_LEASE_SCHEMA = "RISP-G-INIT-REACH-R01-RSS-SUCCESSOR-LEASE-V1"
SUCCESSOR_LEASE_ID = "RISP-G-INIT-REACH-R01-ROOT-EMPIRICAL-20260821-02"
SUCCESSOR_ACCEPTANCE = ROOT / "experiments/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_RSS_SUCCESSOR_ACCEPTANCE_20260821_01.json"
PREDECESSOR_LEASE = Path("C:/Projects/HMASD/temp/leases/RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260821_01.json")
SUCCESSOR_LEASE = Path("C:/Projects/HMASD/temp/leases/RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260821_02.json")
SUCCESSOR_RUNNER = ROOT / "experiments/candidates/renewal_indexed_score_plasticity/run_g_init_r01_rss_successor.py"
SUCCESSOR_TEST = ROOT / "tests/experiments/candidates/renewal_indexed_score_plasticity/test_g_init_r01_rss_successor.py"
EXPECTED_ORIGINAL_CERTIFICATE_SHA256 = "2d7339ad9c103cd9f0ed398b644d03c59f4d561aa0b3649e1d1bab14b93421a2"
PREDECESSOR_GROUP_RSS_BYTES = 1610612736
SUCCESSOR_GROUP_RSS_BYTES = 2684354560
PER_WORKER_RSS_BYTES = 1073741824
WORKERS = 2
CPU_CORES = 2
SLICE_SECONDS = 13800
COMPLETE_CPU_HOURS = 32
COMPLETE_WALL_SECONDS = 86400

PREDECESSOR_RESOURCES = {
    "process_concurrency": 2, "cpu_workers": 2, "cpu_cores": 2, "gpu": False,
    "complete_cpu_hours_upper": COMPLETE_CPU_HOURS,
    "complete_wall_seconds_upper": COMPLETE_WALL_SECONDS,
    "per_worker_rss_limit_bytes": PER_WORKER_RSS_BYTES,
    "process_group_rss_limit_bytes": PREDECESSOR_GROUP_RSS_BYTES,
    "slice_wall_seconds": SLICE_SECONDS, "resumable_only": True,
}
SUCCESSOR_RESOURCES = {**PREDECESSOR_RESOURCES, "process_group_rss_limit_bytes": SUCCESSOR_GROUP_RSS_BYTES}

_DIRECTION_PROTECTED_SUFFIXES = (
    "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_experiment.py",
    "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_resume.py",
    "experiments/candidates/renewal_indexed_score_plasticity/run_g_init_r01_resume.py",
    "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_coordinate_certificate.py",
    "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_native_backend.py",
    "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_native_backend.cpp",
    "experiments/candidates/renewal_indexed_score_plasticity/b2_r02_experiment.py",
)
_SHARED_REGISTRY_SUFFIX = "envs/native/production_backend.py"


class SuccessorValidationError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file():
        raise SuccessorValidationError(f"required immutable parent is absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise SuccessorValidationError(f"{label} is absent: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SuccessorValidationError(f"{label} is not valid JSON") from error
    if not isinstance(value, dict):
        raise SuccessorValidationError(f"{label} must be a JSON object")
    return value


def _strict_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise SuccessorValidationError(f"{field} must use strict UTC seconds")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise SuccessorValidationError(f"{field} must use strict UTC seconds") from error


def _normalize(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").lower()


def _manifest_entry(manifest: Mapping[str, str], suffix: str) -> tuple[str, str]:
    matches = [(path, digest) for path, digest in manifest.items() if str(path).replace("\\", "/").lower().endswith(suffix.lower())]
    if len(matches) != 1:
        raise SuccessorValidationError(f"stored source manifest does not uniquely bind {suffix}")
    return matches[0]


def _verify_stored_manifest(manifest: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise SuccessorValidationError("original source manifest must be a mapping")
    direction: dict[str, str] = {}
    for suffix in _DIRECTION_PROTECTED_SUFFIXES:
        recorded_path, recorded_sha = _manifest_entry(manifest, suffix)
        path = Path(recorded_path)
        if _sha(path) != recorded_sha:
            raise SuccessorValidationError(f"protected direction-local source changed: {suffix}")
        direction[str(path.resolve())] = recorded_sha
    shared_path, stored_shared_sha = _manifest_entry(manifest, _SHARED_REGISTRY_SUFFIX)
    return {
        "stored_manifest_sha256": _canonical_sha(dict(sorted(manifest.items()))),
        "direction_local": dict(sorted(direction.items())),
        "shared_registry": {
            "path": str(Path(shared_path).resolve()),
            "stored_sha256": stored_shared_sha,
            "current_sha256": _sha(Path(shared_path)),
        },
    }


def successor_source_manifest() -> dict[str, str]:
    paths = (Path(__file__).resolve(), SUCCESSOR_RUNNER.resolve())
    return {str(path): _sha(path) for path in paths}


def successor_test_manifest() -> dict[str, str]:
    return {str(SUCCESSOR_TEST.resolve()): _sha(SUCCESSOR_TEST.resolve())}


def canonical_unit_plan_sha256() -> str:
    return _canonical_sha([list(item) for item in resume.unit_plan()])


def canonical_worker_payload_bytes() -> bytes:
    templates = []
    for phase, seed, name, schedule in resume.unit_plan():
        item: dict[str, Any] = {
            "binding_class": "PRODUCTION", "validated_production_binding": True,
            "root_source": "ORIGINAL_CERTIFICATE_COORDINATE_ROOT",
            "item": [phase, seed, name, schedule],
            "deadline_source": "SLICE_DEADLINE_MONOTONIC",
            "per_worker_rss_limit_bytes": PER_WORKER_RSS_BYTES,
        }
        if phase == "EVAL":
            item["checkpoint_states_source"] = [seed, "BOTH_COMMITTED_TRAINING_PACKETS"]
        templates.append(item)
    return json.dumps(templates, sort_keys=True, separators=(",", ":")).encode("utf-8")


def successor_command(
    *, certificate: Path, frontier: Path, result_root: Path,
    successor_acceptance: Path, successor_lease: Path,
) -> str:
    return (
        f"{certificate_spec.INTERPRETER} experiments/candidates/renewal_indexed_score_plasticity/run_g_init_r01_rss_successor.py "
        f"--certificate {certificate.resolve()} --frontier {frontier.resolve()} --result-root {result_root.resolve()} "
        f"--successor-acceptance {successor_acceptance.resolve()} --successor-lease {successor_lease.resolve()} "
        f"--workers {WORKERS} --cpu-cores {CPU_CORES} --slice-wall-seconds {SLICE_SECONDS} "
        f"--per-worker-rss-limit-bytes {PER_WORKER_RSS_BYTES} --process-group-rss-limit-bytes {SUCCESSOR_GROUP_RSS_BYTES}"
    )


def _assert_zero_commit_frontier(frontier_manifest: Path, result_path: Path) -> dict[str, Any]:
    if not frontier_manifest.is_file():
        raise SuccessorValidationError("zero-commit frontier manifest is absent")
    commits = sorted(str(path.resolve()) for path in frontier_manifest.parent.rglob("*.commit.json"))
    if commits:
        raise SuccessorValidationError("successor acceptance requires a zero-commit frontier")
    if result_path.exists():
        raise SuccessorValidationError("successor acceptance requires no production result")
    return {
        "manifest_path": str(frontier_manifest.resolve()),
        "manifest_sha256": _sha(frontier_manifest),
        "commit_count": 0, "result_path": str(result_path.resolve()), "result_absent": True,
    }


def _validate_recorded_frontier_snapshot(snapshot: object) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise SuccessorValidationError("acceptance has no zero-commit frontier snapshot")
    manifest_path = Path(snapshot.get("manifest_path", ""))
    result_path = Path(snapshot.get("result_path", ""))
    expected = {
        "manifest_path": str(manifest_path.resolve()),
        "manifest_sha256": _sha(manifest_path),
        "commit_count": 0,
        "result_path": str(result_path.resolve()),
        "result_absent": True,
    }
    if snapshot != expected:
        raise SuccessorValidationError("recorded zero-commit frontier manifest lineage changed")
    # Progress commits are append-only after acceptance.  A complete result is
    # still excluded at successor launch; the unchanged retained-complete path
    # is not reinterpreted by this wrapper.
    if result_path.exists():
        raise SuccessorValidationError("successor launch rejects an already-present complete result")
    return expected


def _local_native_semantics(value: object) -> dict[str, Any]:
    base = resume._local_native_semantics(value)
    source = value if isinstance(value, dict) else {}
    return {
        **base,
        "python_interactive_call_loop": source.get("python_interactive_call_loop"),
        "python_materialized_event_adapter": source.get("python_materialized_event_adapter"),
    }


def _backend_semantics(backend_acceptance: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    accepted = _read_object(backend_acceptance, "original backend acceptance")
    local = accepted.get("native_artifact")
    shared = accepted.get("shared_functional_acceptance")
    observed = native_backend.production_preflight(batch_width=32)
    if _local_native_semantics(local) != _local_native_semantics(observed.get("local")):
        raise SuccessorValidationError("live native artifact/ABI differs from original backend acceptance")
    if resume._shared_preflight_semantics(shared) != resume._shared_preflight_semantics(observed.get("shared")):
        raise SuccessorValidationError("live shared RISP component semantics differ from original backend acceptance")
    return accepted, _local_native_semantics(local), resume._shared_preflight_semantics(shared)


def _acceptance_packet(
    *, original_certificate: Path, predecessor_lease: Path, backend_acceptance: Path,
    frontier_manifest: Path, result_path: Path,
    original_source_manifest: Mapping[str, str], test_only: bool,
    frontier_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    certificate_sha = _sha(original_certificate)
    if not test_only and certificate_sha != EXPECTED_ORIGINAL_CERTIFICATE_SHA256:
        raise SuccessorValidationError("original production certificate hash changed")
    manifest = _verify_stored_manifest(original_source_manifest)
    _accepted, native_semantics, shared_semantics = _backend_semantics(backend_acceptance)
    zero_frontier = (
        _assert_zero_commit_frontier(frontier_manifest, result_path)
        if frontier_snapshot is None
        else _validate_recorded_frontier_snapshot(dict(frontier_snapshot))
    )
    shared_lineage = manifest["shared_registry"]
    shared_lineage["byte_identity_changed_outside_successor_scope"] = shared_lineage["stored_sha256"] != shared_lineage["current_sha256"]
    shared_lineage["accepted_only_by_original_component_semantic_identity"] = True
    return {
        "schema": SUCCESSOR_SCHEMA, "marker": MARKER,
        "direction_id": certificate_spec.DIRECTION_ID,
        "exact_object_revision": certificate_spec.OBJECT_REVISION,
        "technical_lineage_only": True, "science_revision_changed": False,
        "production_coordinate_serialized": False, "production_coordinate_read_by_successor": False,
        "parents": {
            "original_certificate": {"path": str(original_certificate.resolve()), "sha256": certificate_sha},
            "predecessor_lease": {"path": str(predecessor_lease.resolve()), "sha256": _sha(predecessor_lease), "validity_reinterpreted": False},
            "backend_acceptance": {"path": str(backend_acceptance.resolve()), "sha256": _sha(backend_acceptance)},
            "original_source_manifest": {"sha256": manifest["stored_manifest_sha256"], "entries": dict(sorted(original_source_manifest.items()))},
            "direction_local_protected_sources": manifest["direction_local"],
            "shared_registry_lineage": shared_lineage,
            "native_semantic_identity": native_semantics,
            "shared_component_semantic_identity": shared_semantics,
            "zero_commit_frontier": zero_frontier,
        },
        "whitelist": {
            "predecessor_resources": PREDECESSOR_RESOURCES,
            "successor_resources": SUCCESSOR_RESOURCES,
            "sole_resource_change": {"field": "process_group_rss_limit_bytes", "before": PREDECESSOR_GROUP_RSS_BYTES, "after": SUCCESSOR_GROUP_RSS_BYTES},
            "unchanged_original_runner_core": True, "unchanged_worker_loop": True,
            "unchanged_unit_plan_sha256": canonical_unit_plan_sha256(),
            "unchanged_canonical_worker_payload_sha256": hashlib.sha256(canonical_worker_payload_bytes()).hexdigest(),
            "atomic_install_order": "parent_all_success_then_plan_order",
            "rng_event_native_identity_unchanged": True,
        },
        "successor_sources": successor_source_manifest(),
        "successor_tests": successor_test_manifest(),
        "test_only_fixture": bool(test_only),
    }


def _atomic_no_overwrite(path: Path, packet: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(packet, sort_keys=True, indent=2) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.pending")
    if path.exists() or temporary.exists():
        raise FileExistsError(path)
    try:
        with temporary.open("xb") as handle:
            handle.write(payload); handle.flush(); os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()


def build_successor_acceptance(
    *, output: Path, original_certificate: Path, predecessor_lease: Path,
    backend_acceptance: Path, frontier_manifest: Path, result_path: Path,
    original_source_manifest: Mapping[str, str], test_only: bool = False,
) -> dict[str, Any]:
    output = output.resolve()
    if not test_only and output != SUCCESSOR_ACCEPTANCE.resolve():
        raise SuccessorValidationError("production successor acceptance path is exact")
    if not test_only and (
        original_certificate.resolve() != certificate_spec.PRODUCTION_CERTIFICATE.resolve()
        or predecessor_lease.resolve() != PREDECESSOR_LEASE.resolve()
        or backend_acceptance.resolve() != certificate_spec.BACKEND_ACCEPTANCE.resolve()
        or frontier_manifest.resolve() != (certificate_spec.PRODUCTION_FRONTIER / "manifest.json").resolve()
        or result_path.resolve() != (certificate_spec.PRODUCTION_RESULT_ROOT / certificate_spec.RESULT_NAME).resolve()
    ):
        raise SuccessorValidationError("production successor parent paths are exact")
    packet = _acceptance_packet(
        original_certificate=original_certificate.resolve(), predecessor_lease=predecessor_lease.resolve(),
        backend_acceptance=backend_acceptance.resolve(), frontier_manifest=frontier_manifest.resolve(),
        result_path=result_path.resolve(), original_source_manifest=original_source_manifest,
        test_only=test_only,
    )
    _atomic_no_overwrite(output, packet)
    return packet


def validate_successor_acceptance(path: Path, *, test_only: bool = False) -> dict[str, Any]:
    path = path.resolve()
    if not test_only and path != SUCCESSOR_ACCEPTANCE.resolve():
        raise SuccessorValidationError("production successor acceptance path is exact")
    observed = _read_object(path, "successor acceptance")
    parents = observed.get("parents") if isinstance(observed.get("parents"), dict) else {}
    source_parent = parents.get("original_source_manifest") if isinstance(parents.get("original_source_manifest"), dict) else {}
    expected = _acceptance_packet(
        original_certificate=Path(parents.get("original_certificate", {}).get("path", "")),
        predecessor_lease=Path(parents.get("predecessor_lease", {}).get("path", "")),
        backend_acceptance=Path(parents.get("backend_acceptance", {}).get("path", "")),
        frontier_manifest=Path(parents.get("zero_commit_frontier", {}).get("manifest_path", "")),
        result_path=Path(parents.get("zero_commit_frontier", {}).get("result_path", "")),
        original_source_manifest=source_parent.get("entries", {}), test_only=test_only,
        frontier_snapshot=parents.get("zero_commit_frontier"),
    )
    if observed != expected:
        raise SuccessorValidationError("successor acceptance lineage or whitelist mismatch")
    return observed


def validate_successor_lease(
    path: Path, *, acceptance_path: Path, certificate: Path, frontier: Path,
    result_root: Path, now: datetime | None = None, test_only: bool = False,
) -> dict[str, Any]:
    if not test_only and path.resolve() != SUCCESSOR_LEASE.resolve():
        raise SuccessorValidationError("production successor lease path is exact")
    acceptance = validate_successor_acceptance(acceptance_path, test_only=test_only)
    lease = _read_object(path.resolve(), "successor lease")
    expected_command = successor_command(
        certificate=certificate, frontier=frontier, result_root=result_root,
        successor_acceptance=acceptance_path, successor_lease=path,
    )
    expected_result = result_root.resolve() / certificate_spec.RESULT_NAME
    acceptance_binding = lease.get("successor_acceptance")
    lineage = lease.get("immutable_lineage")
    if (lease.get("schema") != SUCCESSOR_LEASE_SCHEMA or lease.get("lease_id") != SUCCESSOR_LEASE_ID
            or lease.get("direction_id") != certificate_spec.DIRECTION_ID
            or lease.get("stage_id") != certificate_spec.STAGE_ID
            or lease.get("exact_object_revision") != certificate_spec.OBJECT_REVISION
            or lease.get("production_authorized") is not True
            or lease.get("resources") != SUCCESSOR_RESOURCES
            or lease.get("certificate") != str(certificate.resolve())
            or str(certificate.resolve()) != acceptance["parents"]["original_certificate"]["path"]
            or _sha(certificate.resolve()) != acceptance["parents"]["original_certificate"]["sha256"]
            or lease.get("frontier") != str(frontier.resolve())
            or lease.get("result_root") != str(result_root.resolve())
            or lease.get("result") != str(expected_result)
            or lease.get("command") != expected_command
            or not isinstance(acceptance_binding, dict)
            or acceptance_binding != {"path": str(acceptance_path.resolve()), "sha256": _sha(acceptance_path.resolve())}
            or not isinstance(lineage, dict)
            or lineage.get("original_certificate") != acceptance["parents"]["original_certificate"]
            or lineage.get("predecessor_lease") != {key: value for key, value in acceptance["parents"]["predecessor_lease"].items() if key != "validity_reinterpreted"}):
        raise SuccessorValidationError("successor lease does not match the exact whitelist command or lineage")
    issued_at, not_after = _strict_utc(lease.get("issued_at"), "issued_at"), _strict_utc(lease.get("not_after"), "not_after")
    observed_now = datetime.now(timezone.utc) if now is None else now
    if observed_now.tzinfo is None:
        raise SuccessorValidationError("lease validation now must be timezone-aware")
    observed_now = observed_now.astimezone(timezone.utc)
    if issued_at > observed_now or observed_now >= not_after:
        raise SuccessorValidationError("successor lease is future-issued or expired")
    if (not_after - observed_now).total_seconds() < SLICE_SECONDS:
        raise SuccessorValidationError("successor lease does not cover one complete slice")
    _validate_recorded_frontier_snapshot(acceptance["parents"]["zero_commit_frontier"])
    return lease


@contextmanager
def successor_runtime_adapter(acceptance: dict[str, Any]) -> Iterator[None]:
    """Temporarily adapt validator mechanics; restore every object on exit."""
    original_group = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES
    original_interface_object = certificate_spec.LEASE_BINDING_INTERFACE
    original_interface = deepcopy(original_interface_object)
    original_source_manifest = certificate_spec.source_manifest
    original_backend_validator = certificate_spec.validate_backend_binding
    original_lease_validator = certificate_spec.validate_lease_binding
    original_binding = resume._certificate_binding
    stored_manifest = acceptance["parents"]["original_source_manifest"]["entries"]
    predecessor = acceptance["parents"]["predecessor_lease"]
    backend_parent = acceptance["parents"]["backend_acceptance"]
    backend_record = _read_object(Path(backend_parent["path"]), "original backend acceptance")

    def lineage_lease_validator(path: Path, **_kwargs: Any) -> dict[str, Any]:
        if str(path.resolve()) != str(Path(predecessor["path"]).resolve()) or _sha(path.resolve()) != predecessor["sha256"]:
            raise SuccessorValidationError("original certificate referenced a different predecessor lease")
        return {"immutable_expired_predecessor_parent": True}

    def lineage_backend_validator(path: Path) -> dict[str, Any]:
        if str(path.resolve()) != str(Path(backend_parent["path"]).resolve()) or _sha(path.resolve()) != backend_parent["sha256"]:
            raise SuccessorValidationError("original certificate referenced a different backend acceptance")
        observed = native_backend.production_preflight(batch_width=32)
        if _local_native_semantics(backend_record.get("native_artifact")) != _local_native_semantics(observed.get("local")):
            raise SuccessorValidationError("native semantic identity changed")
        if resume._shared_preflight_semantics(backend_record.get("shared_functional_acceptance")) != resume._shared_preflight_semantics(observed.get("shared")):
            raise SuccessorValidationError("shared component semantic identity changed")
        return backend_record

    def successor_binding(*args: Any, **kwargs: Any) -> dict[str, Any]:
        successor_group = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES
        successor_interface = deepcopy(certificate_spec.LEASE_BINDING_INTERFACE)
        try:
            certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = PREDECESSOR_GROUP_RSS_BYTES
            certificate_spec.LEASE_BINDING_INTERFACE = deepcopy(original_interface)
            certificate_spec.source_manifest = lambda: dict(stored_manifest)
            certificate_spec.validate_backend_binding = lineage_backend_validator
            certificate_spec.validate_lease_binding = lineage_lease_validator
            return original_binding(*args, **kwargs)
        finally:
            certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = successor_group
            certificate_spec.LEASE_BINDING_INTERFACE = successor_interface
            certificate_spec.source_manifest = original_source_manifest
            certificate_spec.validate_backend_binding = lineage_backend_validator
            certificate_spec.validate_lease_binding = lineage_lease_validator

    try:
        certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = SUCCESSOR_GROUP_RSS_BYTES
        certificate_spec.LEASE_BINDING_INTERFACE = {
            **deepcopy(original_interface), "resources": deepcopy(SUCCESSOR_RESOURCES),
        }
        certificate_spec.validate_backend_binding = lineage_backend_validator
        certificate_spec.validate_lease_binding = lineage_lease_validator
        resume._certificate_binding = successor_binding
        yield
    finally:
        resume._certificate_binding = original_binding
        certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = original_group
        certificate_spec.LEASE_BINDING_INTERFACE = original_interface_object
        certificate_spec.source_manifest = original_source_manifest
        certificate_spec.validate_backend_binding = original_backend_validator
        certificate_spec.validate_lease_binding = original_lease_validator


def invoke_unchanged_runner(
    *, certificate: Path, frontier: Path, result_root: Path,
    successor_acceptance: Path, successor_lease: Path,
    now: datetime | None = None, test_only: bool = False,
) -> int:
    acceptance = validate_successor_acceptance(successor_acceptance, test_only=test_only)
    validate_successor_lease(
        successor_lease, acceptance_path=successor_acceptance, certificate=certificate,
        frontier=frontier, result_root=result_root, now=now, test_only=test_only,
    )
    original_argv = list(sys.argv)
    try:
        sys.argv = [
            "run_g_init_r01_resume.py", "--certificate", str(certificate.resolve()),
            "--frontier", str(frontier.resolve()), "--result-root", str(result_root.resolve()),
            "--workers", str(WORKERS), "--cpu-cores", str(CPU_CORES),
            "--slice-wall-seconds", str(SLICE_SECONDS),
            "--per-worker-rss-limit-bytes", str(PER_WORKER_RSS_BYTES),
            "--process-group-rss-limit-bytes", str(SUCCESSOR_GROUP_RSS_BYTES),
        ]
        with successor_runtime_adapter(acceptance):
            try:
                from . import run_g_init_r01_resume as original_runner
            except ImportError:
                import run_g_init_r01_resume as original_runner
            return int(original_runner.main())
    finally:
        sys.argv = original_argv

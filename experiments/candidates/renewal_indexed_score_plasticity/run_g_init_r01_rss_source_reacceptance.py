"""Load a source-drift reacceptance and invoke the frozen RISP RSS runner.

This wrapper handles one non-scientific registry-byte drift after the original
RSS successor acceptance. It requires the original acceptance, current
registry hash, native semantic identity, protected source hashes and the same
zero-commit frontier to match; it never reads a coordinate or changes science.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys
from typing import Any

try:
    from . import g_init_r01_rss_successor as successor
except ImportError:
    import g_init_r01_rss_successor as successor

ROOT = successor.ROOT
REACCEPTANCE_PATH = ROOT / (
    "experiments/candidates/renewal_indexed_score_plasticity/"
    "RISP_G_INIT_REACH_R01_RSS_SOURCE_REACCEPTANCE_20260822.json"
)
PRIOR_ACCEPTANCE = successor.SUCCESSOR_ACCEPTANCE
REGISTRY_PATH = ROOT / successor._SHARED_REGISTRY_SUFFIX
REACCEPTANCE_SCHEMA = "RISP-G-INIT-REACH-R01-RSS-SOURCE-REACCEPTANCE-V1"


class SourceReacceptanceError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    if not path.is_file():
        raise SourceReacceptanceError(f"required source is absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SourceReacceptanceError(f"{label} is not valid JSON") from error
    if not isinstance(value, dict):
        raise SourceReacceptanceError(f"{label} must be an object")
    return value


def validate_source_reacceptance(path: Path, *, test_only: bool = False) -> dict[str, Any]:
    path = path.resolve()
    if not test_only and path != REACCEPTANCE_PATH.resolve():
        raise SourceReacceptanceError("production reacceptance path is exact")
    packet = _read(path, "source reacceptance")
    if packet.get("schema") != REACCEPTANCE_SCHEMA or packet.get("technical_only") is not True:
        raise SourceReacceptanceError("source reacceptance schema or technical fence mismatch")

    prior = packet.get("prior_acceptance")
    if not isinstance(prior, dict) or Path(prior.get("path", "")).resolve() != PRIOR_ACCEPTANCE.resolve():
        raise SourceReacceptanceError("prior acceptance path is not the immutable RSS acceptance")
    if _sha(PRIOR_ACCEPTANCE) != prior.get("sha256"):
        raise SourceReacceptanceError("prior acceptance bytes changed")
    base = _read(PRIOR_ACCEPTANCE, "prior successor acceptance")
    parents = base.get("parents") if isinstance(base.get("parents"), dict) else {}
    base_registry = parents.get("shared_registry_lineage", {})
    drift = packet.get("registry_drift") if isinstance(packet.get("registry_drift"), dict) else {}
    if Path(drift.get("path", "")).resolve() != REGISTRY_PATH.resolve():
        raise SourceReacceptanceError("registry drift path is not the accepted registry")
    if drift.get("prior_accepted_current_sha256") != base_registry.get("current_sha256"):
        raise SourceReacceptanceError("registry drift does not chain from prior acceptance")
    current_registry_sha = _sha(REGISTRY_PATH)
    if drift.get("current_sha256") != current_registry_sha:
        raise SourceReacceptanceError("current registry bytes differ from reacceptance")

    # The successor and test sources themselves remain the exact accepted bytes.
    for path_text, digest in {**base.get("successor_sources", {}), **base.get("successor_tests", {})}.items():
        if _sha(Path(path_text)) != digest:
            raise SourceReacceptanceError(f"successor source changed: {path_text}")

    original_manifest = parents.get("original_source_manifest", {}).get("entries", {})
    for path_text, digest in original_manifest.items():
        if Path(path_text).resolve() == REGISTRY_PATH.resolve():
            continue
        if _sha(Path(path_text)) != digest:
            raise SourceReacceptanceError(f"protected source changed: {path_text}")

    native = successor._local_native_semantics(successor.native_backend.production_preflight(batch_width=32)["local"])
    shared = successor.resume._shared_preflight_semantics(
        successor.native_backend.production_preflight(batch_width=32)["shared"]
    )
    if native != parents.get("native_semantic_identity"):
        raise SourceReacceptanceError("native semantic identity changed")
    if shared != parents.get("shared_component_semantic_identity"):
        raise SourceReacceptanceError("shared component semantic identity changed")

    # The current registry must still advertise the exact RISP native boundary.
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
        "native_boundary": parents["shared_component_semantic_identity"]["native_boundary"],
    }:
        raise SourceReacceptanceError("current registry RISP capability is not semantically identical")

    snapshot = parents.get("zero_commit_frontier")
    successor._validate_recorded_frontier_snapshot(snapshot)

    # Return a transient acceptance view with only the registry current hash
    # updated; the on-disk prior acceptance remains immutable.
    accepted = deepcopy(base)
    accepted["parents"]["shared_registry_lineage"]["current_sha256"] = current_registry_sha
    return accepted


def invoke(
    *, reacceptance: Path, certificate: Path, frontier: Path, result_root: Path,
    successor_lease: Path, test_only: bool = False,
) -> int:
    accepted = validate_source_reacceptance(reacceptance, test_only=test_only)
    original_acceptance = successor.SUCCESSOR_ACCEPTANCE
    original_lease = successor.SUCCESSOR_LEASE
    original_validator = successor.validate_successor_acceptance

    def accepted_view(path: Path, *, test_only: bool = False) -> dict[str, Any]:
        if path.resolve() != reacceptance.resolve():
            raise SourceReacceptanceError("unexpected acceptance path")
        return accepted

    try:
        successor.SUCCESSOR_ACCEPTANCE = reacceptance.resolve()
        successor.SUCCESSOR_LEASE = successor_lease.resolve()
        successor.validate_successor_acceptance = accepted_view
        return successor.invoke_unchanged_runner(
            certificate=certificate, frontier=frontier, result_root=result_root,
            successor_acceptance=reacceptance, successor_lease=successor_lease,
            test_only=test_only,
        )
    finally:
        successor.SUCCESSOR_ACCEPTANCE = original_acceptance
        successor.SUCCESSOR_LEASE = original_lease
        successor.validate_successor_acceptance = original_validator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reacceptance", required=True, type=Path)
    parser.add_argument("--certificate", required=True, type=Path)
    parser.add_argument("--frontier", required=True, type=Path)
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--successor-lease", required=True, type=Path)
    args = parser.parse_args()
    return invoke(
        reacceptance=args.reacceptance, certificate=args.certificate,
        frontier=args.frontier, result_root=args.result_root,
        successor_lease=args.successor_lease,
    )


if __name__ == "__main__":
    raise SystemExit(main())

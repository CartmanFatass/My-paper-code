from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any

from .counter import address, categorical
from .host import build_churn_fixtures, build_strata
from .validation import validate_evidence


SCHEMA = "FSBS_R01_S0_HOST_SUPPORT_FIREWALL_V1"
NAMESPACE = "FSBS-VN1-R01"
AUTHORITY_PATH = (
    "docs/research/candidates/finite_semantic_boundary_support/"
    "FSBS_VARIABLE_AXIS_COOPERATIVE_UAV_SCIENCE_AUTHORITY_R01_20260827.md"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _file_ref(repo: Path, path: Path) -> dict[str, Any]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repo).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def _source_manifest(repo: Path) -> list[dict[str, Any]]:
    package = Path(__file__).resolve().parent
    return [_file_ref(repo, path) for path in sorted(package.glob("*.py"))]


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_evidence() -> dict[str, Any]:
    """Build and validate the deterministic learner-free S0 evidence core."""

    repo = _repo_root()
    authority_ref = _file_ref(repo, repo / AUTHORITY_PATH)
    source_manifest = _source_manifest(repo)
    proof_seed = 127
    proof_family = "paired-exogenous-world"
    proof_coordinates: tuple[str | int, ...] = (10, "REDUCED", 1, 0, 1, 1, 0)
    proof_address = address(proof_seed, proof_family, proof_coordinates, 0)
    evidence: dict[str, Any] = {
        "schema": SCHEMA,
        "mode": "TECHNICAL_ONLY_RESULT_BLIND_LEARNER_FREE",
        "namespace": NAMESPACE,
        "counts": {
            "outer_strata": 384,
            "worlds_per_stratum": 8,
            "accepted_per_world": 4,
            "denied_per_world": 1,
            "accepted_transactions": 12_288,
            "denied_transactions": 3_072,
            "total_transactions": 15_360,
        },
        "firewall": {
            "learner_initialized": False,
            "model_created": False,
            "checkpoint_created": False,
            "registered_paired_effects_emitted": False,
            "partial_scientific_value_emitted": False,
            "formal_compute_executed": False,
            "external_effect_executed": False,
            "operator_requested": False,
            "provider_contacted": False,
            "deployment_or_flight_executed": False,
        },
        "effect_refs": [],
        "atomic_write": {"single_final_replace": True},
        "next_boundary": "FSBS-R01-S1-LEARNER-FREE-TECHNICAL-BINDING-ONLY",
        "authority_ref": authority_ref,
        "source_manifest": source_manifest,
        "counter_proof": {
            "seed": proof_seed,
            "family": proof_family,
            "coordinates": list(proof_coordinates),
            "rejection_counter": 0,
            "address_hex": proof_address.hex(),
            "sha256": hashlib.sha256(proof_address).hexdigest(),
            "domain_size": 4,
            "categorical_result": categorical(
                4, proof_seed, proof_family, proof_coordinates
            ),
        },
        "churn_fixtures": build_churn_fixtures(),
        "information_path_firewall": {
            "selector_visible_fields": ["i", "r", "surface_bit", "auth_ok"],
            "forbidden_selector_fields": [
                "identity",
                "token",
                "lineage",
                "partner",
                "roster_position",
                "M",
                "N_t",
                "arm",
                "donor",
                "block",
                "hidden_slot",
                "unopened_payload",
                "pair_score",
                "future_return",
            ],
            "unopened_payload_exposed": False,
            "pair_score_exposed": False,
            "future_return_exposed": False,
        },
    }
    evidence["strata"] = build_strata()
    evidence["evidence_tree"] = validate_evidence(evidence)
    evidence["deterministic_core_sha256"] = hashlib.sha256(
        _canonical(evidence)
    ).hexdigest()
    return evidence


def write_evidence(output: Path) -> None:
    """Write one complete JSON record by a same-directory atomic replace."""

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    started_cpu = time.process_time_ns()
    started_wall = time.perf_counter_ns()
    evidence = build_evidence()
    _canonical(evidence)
    _current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    evidence["technical_measurements"] = {
        "scope": "build-validate-canonicalize-before-atomic-replace",
        "cpu_ns": time.process_time_ns() - started_cpu,
        "wall_ns": time.perf_counter_ns() - started_wall,
        "peak_memory_bytes": peak_memory,
        "peak_memory_method": "tracemalloc-python-allocations",
        "io": {
            "authority_bytes_read": evidence["authority_ref"]["bytes"],
            "source_bytes_read": sum(
                row["bytes"] for row in evidence["source_manifest"]
            ),
            "output_bytes": 0,
            "atomic_replace_count": 1,
        },
    }
    while True:
        serialized = _canonical(evidence) + b"\n"
        if evidence["technical_measurements"]["io"]["output_bytes"] == len(serialized):
            break
        evidence["technical_measurements"]["io"]["output_bytes"] = len(serialized)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Emit the learner-free FSBS R01 S0 technical evidence record."
    )
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    write_evidence(arguments.output)


if __name__ == "__main__":
    main()

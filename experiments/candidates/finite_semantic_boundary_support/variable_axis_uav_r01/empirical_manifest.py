from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Mapping

from .empirical_contract import (
    canonical_parameters,
    canonical_resource_estimate,
    checkpoint_identities,
    empirical_boundary,
    git_prerequisites,
)


ACCEPTED_REFS = {
    "s0": {
        "path": (
            "temp/directions/finite_semantic_boundary_support/test/"
            "variable_axis_uav_r01/s0/g1/FSBS_R01_S0_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "778cbe7c8c90279b0787e6a651ca537cb72e94b0b786a453a2e62b297dd571de",
    },
    "s1": {
        "path": (
            "temp/directions/finite_semantic_boundary_support/test/"
            "variable_axis_uav_r01/s1/g1/FSBS_R01_S1_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "dec17c340970bb5aa3c46cf1a15cf40c814cda708ec9950f721a3f134df990b0",
    },
    "s2": {
        "path": (
            "temp/directions/finite_semantic_boundary_support/test/"
            "variable_axis_uav_r01/s2/g1/FSBS_R01_S2_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "dafa687110a6e9af331f3328b0eb4943536bdfc4af6c458d0c214d67266d7cfd",
    },
}

SOURCE_ROOT = Path(
    "experiments/candidates/finite_semantic_boundary_support/variable_axis_uav_r01"
)
TEST_PATHS = (
    "tests/experiments/candidates/finite_semantic_boundary_support/"
    "test_variable_axis_uav_r01_s0.py",
    "tests/experiments/candidates/finite_semantic_boundary_support/"
    "test_variable_axis_uav_r01_s1_binding.py",
    "tests/experiments/candidates/finite_semantic_boundary_support/"
    "test_variable_axis_uav_r01_s2_learner.py",
    "tests/experiments/candidates/finite_semantic_boundary_support/"
    "test_variable_axis_uav_r01_empirical_prelaunch.py",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _file_ref(repo: Path, relative: str) -> dict[str, str]:
    path = repo / relative
    if not path.is_file():
        raise FileNotFoundError(f"required source or evidence is absent: {relative}")
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def source_test_manifest(repo: Path) -> dict[str, Any]:
    source_paths = sorted(
        path.relative_to(repo).as_posix()
        for path in (repo / SOURCE_ROOT).glob("*.py")
        if path.is_file()
    )
    refs = [_file_ref(repo, path) for path in sorted((*source_paths, *TEST_PATHS))]
    return {
        "schema": "FSBS_R01_S3_SOURCE_TEST_MANIFEST_V1",
        "refs": refs,
        "sha256": hashlib.sha256(_canonical(refs)).hexdigest(),
    }


def build_prelaunch_dossier(repo: Path, *, observed_shared_head: str) -> dict[str, Any]:
    manifest = source_test_manifest(repo)
    accepted = {}
    for name, ref in ACCEPTED_REFS.items():
        current = _file_ref(repo, ref["path"])
        if current != ref:
            raise ValueError(f"accepted {name.upper()} evidence bytes drifted")
        accepted[name] = dict(ref)
    boundary = empirical_boundary()
    parameters = canonical_parameters()
    prerequisites = git_prerequisites(observed_shared_head)
    run_template = {
        "schema_version": 1,
        "writer": "Operator-fsbs-r01-complete-20260827-01",
        "operator_identity": "Operator-fsbs-r01-complete-20260827-01",
        "run_id": boundary["run_id"],
        "direction_id": "finite_semantic_boundary_support",
        "assignment_id": boundary["run_id"],
        "status": "NOT_RELEASED",
        "command": boundary["payload_argv"],
        "parameters_sha256": parameters["sha256"],
        "candidate_head": None,
        "code_sha": None,
        "release_ready": False,
    }
    return {
        "schema": "FSBS_R01_S3_PRELAUNCH_DOSSIER_V1",
        "boundary": boundary,
        "parameters": parameters,
        "resource_estimate": canonical_resource_estimate(),
        "checkpoint_identities": checkpoint_identities(),
        "source_test_manifest": manifest,
        "accepted_s0_ref": accepted["s0"],
        "accepted_s1_ref": accepted["s1"],
        "accepted_s2_ref": accepted["s2"],
        "git_prerequisites": prerequisites,
        "run_manifest_template": run_template,
        "evidence_tree": {
            "terminal_status": "PRELAUNCH_TECHNICALLY_BOUND",
            "nodes": [
                {"id": node, "status": "PASS"}
                for node in (
                    "accepted-s0-s1-s2-current-bytes",
                    "canonical-registered-parameters",
                    "source-test-current-bytes",
                    "checkpoint-identity-completeness",
                    "create-only-no-rerun-boundary",
                    "immutable-code-sha-git-prerequisite",
                    "result-blind-resource-estimate",
                    "empirical-release-firewall",
                )
            ],
        },
        "empirical_activity_released": False,
        "operator_now": False,
        "effect_refs": [],
    }


def validate_release_manifest(
    manifest: Mapping[str, Any],
    dossier: Mapping[str, Any],
    *,
    observed_branch: str,
    observed_candidate_head: str,
) -> dict[str, bool]:
    template = dossier["run_manifest_template"]
    exact = {
        "schema_version": template["schema_version"],
        "writer": template["writer"],
        "operator_identity": template["operator_identity"],
        "run_id": template["run_id"],
        "direction_id": template["direction_id"],
        "assignment_id": template["assignment_id"],
        "status": "RUNNING",
        "command": template["command"],
        "parameters_sha256": template["parameters_sha256"],
    }
    for field, expected in exact.items():
        if manifest.get(field) != expected:
            raise PermissionError(f"release manifest {field} does not match frozen contract")
    required_branch = dossier["git_prerequisites"]["required_branch"]
    if observed_branch != required_branch:
        raise PermissionError("release branch does not match required_branch")
    code_sha = manifest.get("code_sha")
    if not isinstance(code_sha, str) or code_sha != observed_candidate_head:
        raise PermissionError("release code_sha does not equal observed candidate head")
    return {"released": True}


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_prelaunch_acceptance(
    output: Path,
    repo: Path,
    *,
    observed_shared_head: str,
    scratch_root: Path,
) -> None:
    from .empirical_validation import (
        validate_cold_resume_fixture,
        validate_prelaunch_dossier,
    )

    output = output.resolve()
    scratch_root = scratch_root.resolve()
    scratch_root.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    started_cpu = time.process_time_ns()
    started_wall = time.perf_counter_ns()
    dossier = build_prelaunch_dossier(
        repo, observed_shared_head=observed_shared_head
    )
    validate_prelaunch_dossier(dossier, repo)
    technical = validate_cold_resume_fixture(scratch_root)
    checkpoint_bytes = sum(
        path.stat().st_size for path in scratch_root.glob("*.json") if path.is_file()
    )
    _current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    boundary = dossier["boundary"]
    core: dict[str, Any] = {
        "schema": "FSBS_R01_S3_EMPIRICAL_PRELAUNCH_ACCEPTANCE_V1",
        "terminal_status": "PRELAUNCH_TECHNICALLY_ACCEPTED",
        "run_id": boundary["run_id"],
        "payload_argv": boundary["payload_argv"],
        "reserved_output_effect": {
            "kind": "LOCAL_RESULT_ROOT",
            "resource_id": boundary["output_root"],
            "operation": "CREATE_ONLY",
            "reserved_not_created": True,
        },
        "canonical_parameters": dossier["parameters"],
        "canonical_resource_estimate": dossier["resource_estimate"],
        "checkpoint_identities": dossier["checkpoint_identities"],
        "source_test_manifest": dossier["source_test_manifest"],
        "accepted_s0_ref": dossier["accepted_s0_ref"],
        "accepted_s1_ref": dossier["accepted_s1_ref"],
        "accepted_s2_ref": dossier["accepted_s2_ref"],
        "run_manifest_template": dossier["run_manifest_template"],
        "git_prerequisites": dossier["git_prerequisites"],
        "evidence_tree": dossier["evidence_tree"],
        "technical_fixture_validation": technical,
        "firewall": {
            "registered_seed_execution": False,
            "registered_arm_execution": False,
            "scientific_training_or_evaluation": False,
            "question_relevant_values": False,
            "scientific_first_true_outcome": False,
            "partial_package_access": False,
            "hmasd_run_operation": False,
            "experiment_operator_requested": False,
            "git_effect": False,
            "provider_or_external_effect": False,
        },
        "empirical_activity_released": False,
        "operator_now": False,
        "effect_refs": [],
    }
    deterministic_core_sha256 = hashlib.sha256(_canonical(core)).hexdigest()
    acceptance = {
        **core,
        "deterministic_core_sha256": deterministic_core_sha256,
        "actual_technical_measurements": {
            "scope": "S3-nonregistered-prelaunch-build-validate-atomic-write",
            "cpu_ns": time.process_time_ns() - started_cpu,
            "wall_ns": time.perf_counter_ns() - started_wall,
            "peak_memory_bytes": peak_memory,
            "peak_memory_method": "tracemalloc-python-allocations",
            "scratch_peak_bytes": checkpoint_bytes,
            "storage_bytes": 0,
            "io": {
                "output_bytes": 0,
                "technical_checkpoint_bytes": checkpoint_bytes,
                "atomic_acceptance_replace_count": 1,
            },
        },
    }
    while True:
        payload_bytes = len(_canonical(acceptance) + b"\n")
        measurements = acceptance["actual_technical_measurements"]
        if (
            measurements["storage_bytes"] == payload_bytes
            and measurements["io"]["output_bytes"] == payload_bytes
        ):
            break
        measurements["storage_bytes"] = payload_bytes
        measurements["io"]["output_bytes"] = payload_bytes
    _atomic_write(output, acceptance)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build the result-blind FSBS R01 S3 prelaunch acceptance."
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    parser.add_argument("--observed-shared-head", required=True)
    arguments = parser.parse_args(argv)
    write_prelaunch_acceptance(
        arguments.output,
        Path(__file__).resolve().parents[4],
        observed_shared_head=arguments.observed_shared_head,
        scratch_root=arguments.scratch_root,
    )


if __name__ == "__main__":
    main()

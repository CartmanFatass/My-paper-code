from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import tracemalloc
import subprocess
import re
from pathlib import Path
from typing import Any, Mapping

from .empirical_contract import (
    LEGACY_TERMINAL_RUN_ID,
    OPERATOR_IDENTITY,
    AUTHORITY_REFS,
    OUTPUT_ROOT,
    RUN_ID,
    TERMINAL_RUN_IDS,
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


def observe_positive_process_cpu_ns(started_cpu_ns: int | None = None) -> int:
    """Return an observed positive process-CPU delta or fail explicitly."""
    started = time.process_time_ns() if started_cpu_ns is None else started_cpu_ns
    deadline = time.perf_counter_ns() + 1_000_000_000
    state = b"FSBS-R01-RESULT-BLIND-CPU-CLOCK"
    attempt = 0
    while time.perf_counter_ns() < deadline:
        observed = time.process_time_ns() - started
        if observed > 0:
            return observed
        for _ in range(256):
            state = hashlib.sha256(
                state + attempt.to_bytes(8, "big", signed=False)
            ).digest()
            attempt += 1
    raise RuntimeError(
        "process CPU clock did not advance during bounded technical work"
    )


def _file_ref(repo: Path, relative: str) -> dict[str, str]:
    path = repo / relative
    if not path.is_file():
        raise FileNotFoundError(f"required source or evidence is absent: {relative}")
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _git_text(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise PermissionError("candidate Git identity cannot be observed")
    return completed.stdout.strip()


def _candidate_blob_ref(repo: Path, candidate_head: str, relative: str) -> dict[str, str]:
    blob_oid = _git_text(repo, "rev-parse", f"{candidate_head}:{relative}")
    completed = subprocess.run(
        ["git", "-C", str(repo), "show", f"{candidate_head}:{relative}"],
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        raise PermissionError(f"candidate blob cannot be observed: {relative}")
    return {
        "path": relative,
        "git_blob_oid": blob_oid,
        "sha256": hashlib.sha256(completed.stdout).hexdigest(),
    }


def _candidate_source_test_inventory(repo: Path, candidate_head: str) -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "ls-tree",
            "-r",
            "--name-only",
            candidate_head,
            "--",
            SOURCE_ROOT.as_posix(),
            "tests/experiments/candidates/finite_semantic_boundary_support",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise PermissionError("candidate source/test inventory cannot be observed")
    source_prefix = f"{SOURCE_ROOT.as_posix()}/"
    paths = sorted(
        path
        for path in completed.stdout.splitlines()
        if path.endswith(".py")
        and (
            path.startswith(source_prefix)
            or (
                Path(path).parent.as_posix()
                == "tests/experiments/candidates/finite_semantic_boundary_support"
                and Path(path).name.startswith("test_variable_axis_uav_r01_")
            )
        )
    )
    if not paths or not set(TEST_PATHS).issubset(paths):
        raise PermissionError("candidate source/test tracked inventory is incomplete")
    return paths


def source_test_manifest(
    repo: Path, *, candidate_head: str | None = None
) -> dict[str, Any]:
    if candidate_head is None:
        source_paths = sorted(
            path.relative_to(repo).as_posix()
            for path in (repo / SOURCE_ROOT).glob("*.py")
            if path.is_file()
        )
        paths = sorted((*source_paths, *TEST_PATHS))
    else:
        paths = _candidate_source_test_inventory(repo, candidate_head)
    refs = (
        [_file_ref(repo, path) for path in paths]
        if candidate_head is None
        else [_candidate_blob_ref(repo, candidate_head, path) for path in paths]
    )
    return {
        "schema": "FSBS_R01_S3_SOURCE_TEST_MANIFEST_V1",
        "binding": (
            "WORKTREE_RAW_BYTES"
            if candidate_head is None
            else "GIT_CANDIDATE_BLOB_BYTES"
        ),
        "refs": refs,
        "sha256": hashlib.sha256(_canonical(refs)).hexdigest(),
    }


def build_runtime_contract(repo: Path, *, candidate_branch: str) -> dict[str, Any]:
    """Build the tracked-code-only release contract used by the payload.

    Unlike the historical S3 dossier, this contract has no dependency on ignored
    acceptance artifacts.  Git HEAD binds the exact candidate bytes at prepare
    and launch time; the fresh source/test manifest remains useful prelaunch
    evidence and a diagnostic inventory.
    """

    required_branch = git_prerequisites("")["required_branch"]
    if candidate_branch != required_branch:
        raise ValueError("candidate_branch does not match the replacement contract")
    candidate_head = _git_text(repo, "rev-parse", "--verify", "HEAD")
    boundary = empirical_boundary()
    return {
        "schema": "FSBS_R01_CANDIDATE_RUNTIME_CONTRACT_V2",
        "run_id": RUN_ID,
        "operator_identity": OPERATOR_IDENTITY,
        "legacy_terminal_run_id": LEGACY_TERMINAL_RUN_ID,
        "terminal_run_ids": list(TERMINAL_RUN_IDS),
        "legacy_terminal_replay_permitted": False,
        "direction_id": "finite_semantic_boundary_support",
        "candidate_branch": required_branch,
        "candidate_head": candidate_head,
        "payload_argv": boundary["payload_argv"],
        "effect": {
            "kind": "LOCAL_RESULT_ROOT",
            "resource_id": OUTPUT_ROOT,
            "operation": "CREATE_ONLY",
        },
        "parameters": canonical_parameters(),
        "authority_refs": [dict(ref) for ref in AUTHORITY_REFS],
        "resource_estimate": canonical_resource_estimate(),
        "checkpoint_identities": checkpoint_identities(),
        "source_test_manifest": source_test_manifest(
            repo, candidate_head=candidate_head
        ),
        "complete_only_publication": True,
        "workers": 1,
        "threads_per_worker": 1,
    }


def validate_candidate_source_binding(
    contract: Mapping[str, Any], observed_blob_hashes: Mapping[str, str]
) -> dict[str, Any]:
    refs = contract.get("source_test_manifest", {}).get("refs", ())
    expected = {str(ref["path"]): str(ref["sha256"]) for ref in refs}
    if not expected or dict(observed_blob_hashes) != expected:
        raise PermissionError("candidate blob bytes do not match source/test manifest")
    return {
        "source_test_bytes_equal_candidate": True,
        "ref_count": len(expected),
    }


def observe_candidate_blob_hashes(
    repo: Path, candidate_head: str, contract: Mapping[str, Any]
) -> dict[str, str]:
    observed: dict[str, str] = {}
    for ref in contract["source_test_manifest"]["refs"]:
        path = str(ref["path"])
        completed = subprocess.run(
            ["git", "-C", str(repo), "show", f"{candidate_head}:{path}"],
            check=False,
            capture_output=True,
        )
        if completed.returncode:
            raise PermissionError(f"candidate blob cannot be observed: {path}")
        observed[path] = hashlib.sha256(completed.stdout).hexdigest()
    return observed


def observe_candidate_worktree_blob_oids(
    repo: Path,
    contract: Mapping[str, Any],
    *,
    checkout_root: Path | None = None,
) -> dict[str, str]:
    checkout = repo if checkout_root is None else checkout_root
    observed: dict[str, str] = {}
    for ref in contract["source_test_manifest"]["refs"]:
        path = str(ref["path"])
        target = checkout / path
        if not target.is_file():
            raise PermissionError(f"candidate checkout tracked source/test is absent: {path}")
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "hash-object",
                f"--path={path}",
                "--",
                str(target),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise PermissionError(f"candidate checkout blob cannot be observed: {path}")
        observed[path] = completed.stdout.strip()
    return observed


def validate_candidate_worktree_binding(
    contract: Mapping[str, Any], observed_blob_oids: Mapping[str, str]
) -> dict[str, Any]:
    refs = contract.get("source_test_manifest", {}).get("refs", ())
    expected = {str(ref["path"]): str(ref["git_blob_oid"]) for ref in refs}
    if not expected or dict(observed_blob_oids) != expected:
        raise PermissionError("candidate checkout has source/test drift")
    return {"source_test_checkout_clean": True, "ref_count": len(expected)}


def validate_operator_runtime_files(
    manifest: Mapping[str, Any], manifest_path: Path, *, observed_branch: str
) -> dict[str, Any]:
    root = manifest_path.resolve().parent
    resources = manifest["resources"]
    preflight_path = root / str(resources["preflight_ref"])
    runner_path = root / "runner-spec.json"
    if not preflight_path.is_file() or not runner_path.is_file():
        raise PermissionError("Operator preflight/runner files are absent")
    preflight_bytes = preflight_path.read_bytes()
    runner_bytes = runner_path.read_bytes()
    if hashlib.sha256(preflight_bytes).hexdigest() != resources["preflight_sha256"]:
        raise PermissionError("Operator preflight hash does not match manifest")
    if hashlib.sha256(runner_bytes).hexdigest() != resources["runner_spec_sha256"]:
        raise PermissionError("Operator runner hash does not match manifest")
    preflight = json.loads(preflight_bytes)
    runner = json.loads(runner_bytes)
    if preflight.get("memory_safe") is not True:
        raise PermissionError("Operator preflight is not memory safe")
    expected_runner = {
        "schema_version": 1,
        "command": manifest["command"],
        "command_sha256": manifest["command_sha256"],
        "cwd": manifest["cwd"],
        "git_branch": observed_branch,
        "output_root": str(root),
        "outputs": manifest["outputs"],
        "preflight_sha256": resources["preflight_sha256"],
    }
    if runner != expected_runner:
        raise PermissionError("Operator runner specification does not match manifest")
    return {
        "operator_runtime_files_valid": True,
        "preflight_sha256": resources["preflight_sha256"],
        "runner_spec_sha256": resources["runner_spec_sha256"],
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
        "writer": OPERATOR_IDENTITY,
        "operator_identity": OPERATOR_IDENTITY,
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
    contract: Mapping[str, Any],
    *,
    manifest_path: Path,
    observed_cwd: Path,
    observed_branch: str,
    observed_candidate_head: str,
    observed_payload_pid: int,
    operator_runtime_files: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if manifest.get("run_id") in TERMINAL_RUN_IDS:
        raise PermissionError("terminal run tombstone cannot be replayed")
    if contract.get("schema") != "FSBS_R01_CANDIDATE_RUNTIME_CONTRACT_V2":
        raise PermissionError("candidate-local runtime contract schema is invalid")
    if (
        contract.get("run_id") != RUN_ID
        or contract.get("operator_identity") != OPERATOR_IDENTITY
    ):
        raise PermissionError("candidate-local contract identity is invalid")
    if (
        contract.get("terminal_run_ids") != list(TERMINAL_RUN_IDS)
        or contract.get("legacy_terminal_run_id") != LEGACY_TERMINAL_RUN_ID
        or contract.get("run_id") in TERMINAL_RUN_IDS
    ):
        raise PermissionError("candidate-local terminal tombstones are invalid")
    operator = OPERATOR_IDENTITY
    parameters = canonical_parameters()
    observed_parameters = manifest.get("parameters")
    if not isinstance(observed_parameters, Mapping):
        raise PermissionError("release manifest parameters are absent")
    if observed_parameters.get("effect_refs") != [contract.get("effect")]:
        raise PermissionError("release manifest Effect is not the single frozen CREATE_ONLY Effect")
    expected_caps = {
        "wall_seconds": 600,
        "cpu_seconds": 600,
        "peak_memory_bytes": 1_073_741_824,
        "scratch_bytes": 536_870_912,
        "durable_result_bytes": 268_435_456,
        "workers": 1,
        "threads_per_worker": 1,
    }
    if observed_parameters.get("resource_caps") != expected_caps:
        raise PermissionError("release manifest full resource caps do not match frozen contract")
    if observed_parameters.get("authority_refs") != contract.get("authority_refs"):
        raise PermissionError("release manifest R01 authority refs do not match frozen contract")
    command = empirical_boundary()["payload_argv"]
    exact = {
        "schema_version": 1,
        "writer": operator,
        "operator_identity": operator,
        "run_id": RUN_ID,
        "direction_id": "finite_semantic_boundary_support",
        "assignment_id": RUN_ID,
        "status": "RUNNING",
        "command": command,
        "command_sha256": hashlib.sha256(
            b"\0".join(os.fsencode(part) for part in command)
        ).hexdigest(),
        "parameters": parameters,
        "parameters_sha256": hashlib.sha256(_canonical(parameters)).hexdigest(),
    }
    for field, expected in exact.items():
        if manifest.get(field) != expected:
            raise PermissionError(f"release manifest {field} does not match frozen contract")
    observed_cwd = observed_cwd.resolve()
    if Path(str(manifest.get("cwd", ""))).resolve() != observed_cwd:
        raise PermissionError("release manifest cwd does not match observed cwd")
    expected_manifest = (observed_cwd / OUTPUT_ROOT / "manifest.json").resolve()
    if manifest_path.resolve() != expected_manifest:
        raise PermissionError("release manifest path does not match create-only Effect")
    required_branch = str(contract["candidate_branch"])
    if observed_branch != required_branch:
        raise PermissionError("release branch does not match required_branch")
    code_sha = manifest.get("code_sha")
    if (
        not isinstance(code_sha, str)
        or code_sha != observed_candidate_head
        or contract.get("candidate_head") != observed_candidate_head
    ):
        raise PermissionError("release code_sha does not equal observed candidate head")
    claim = hashlib.sha256(
        _canonical(
            {
                "direction_id": "finite_semantic_boundary_support",
                "code_sha": code_sha,
                "command_sha256": exact["command_sha256"],
            }
        )
    ).hexdigest()
    if manifest.get("claim_sha256") != claim:
        raise PermissionError("release manifest claim_sha256 is invalid")
    estimate = manifest.get("estimate")
    expected_estimate = {
        "wall_seconds": 600.0,
        "basis": "ACCEPTED_S2_HIGH_RESULT_BLIND_PROJECTION",
        "peak_memory_gib": 1.0,
    }
    if estimate != expected_estimate:
        raise PermissionError("release manifest estimate does not match frozen caps")
    environment = manifest.get("environment")
    if (
        not isinstance(environment, Mapping)
        or set(environment) != {"python", "platform", "hostname", "captured_variables"}
        or not all(
            isinstance(environment.get(field), str) and environment.get(field)
            for field in ("python", "platform", "hostname")
        )
        or environment.get("captured_variables") != {}
    ):
        raise PermissionError("release manifest environment provenance is invalid")
    outputs = manifest.get("outputs")
    if outputs != {
        "stdout": "stdout.log",
        "stderr": "stderr.log",
        "checkpoints": "checkpoints",
        "metrics": "metrics",
        "artifacts": "artifacts",
    }:
        raise PermissionError("release manifest outputs do not match the frozen output layout")
    process = manifest.get("process")
    required_process_keys = {
        "execution_token", "pid", "process_group_id", "linux_boot_id",
        "proc_start_ticks", "identity_persisted_at", "group_quiescent",
        "started_at", "ended_at", "exit_code", "terminal_reason",
    }
    if (
        not isinstance(process, Mapping)
        or set(process) != required_process_keys
        or not isinstance(process.get("execution_token"), str)
        or not process.get("execution_token")
        or not isinstance(process.get("pid"), int)
        or process.get("pid") != observed_payload_pid
        or not isinstance(process.get("process_group_id"), int)
        or not isinstance(process.get("proc_start_ticks"), int)
        or not isinstance(process.get("linux_boot_id"), str)
        or not isinstance(process.get("identity_persisted_at"), str)
        or not isinstance(process.get("started_at"), str)
        or process.get("group_quiescent") is not None
        or process.get("ended_at") is not None
        or process.get("exit_code") is not None
        or process.get("terminal_reason") is not None
    ):
        raise PermissionError("release manifest process RUNNING identity is invalid")
    resources = manifest.get("resources")
    sha256_pattern = re.compile(r"[0-9a-f]{64}\Z")
    if (
        not isinstance(resources, Mapping)
        or set(resources) != {
            "preflight_ref", "preflight_sha256", "runner_spec_sha256",
            "workers", "threads_per_worker", "memory_safe",
        }
        or resources.get("preflight_ref") != "preflight.json"
        or not isinstance(resources.get("preflight_sha256"), str)
        or not sha256_pattern.fullmatch(str(resources.get("preflight_sha256")))
        or not isinstance(resources.get("runner_spec_sha256"), str)
        or not sha256_pattern.fullmatch(str(resources.get("runner_spec_sha256")))
        or resources.get("workers") != 1
        or resources.get("threads_per_worker") != 1
        or resources.get("memory_safe") is not True
    ):
        raise PermissionError("release manifest resources/preflight/runner provenance is invalid")
    if operator_runtime_files != {
        "operator_runtime_files_valid": True,
        "preflight_sha256": resources["preflight_sha256"],
        "runner_spec_sha256": resources["runner_spec_sha256"],
    }:
        raise PermissionError("release manifest lacks validated Operator runtime file provenance")
    if (
        not isinstance(manifest.get("revision"), int)
        or manifest["revision"] < 2
        or not isinstance(manifest.get("created_at"), str)
        or not isinstance(manifest.get("updated_at"), str)
        or manifest.get("observed_metrics") != {}
    ):
        raise PermissionError("release manifest RUNNING revision/timestamps are invalid")
    return {
        "released": True,
        "run_id": RUN_ID,
        "code_sha": code_sha,
        "authority_refs": contract["authority_refs"],
        "source_test_manifest": contract["source_test_manifest"],
    }


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
            "cpu_ns": observe_positive_process_cpu_ns(started_cpu),
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


def write_runtime_prelaunch_acceptance(
    output: Path,
    repo: Path,
    *,
    candidate_branch: str,
    scratch_root: Path,
) -> None:
    """Atomically record result-blind V2 acceptance from candidate-local bytes."""

    from .empirical_validation import (
        validate_cold_resume_fixture,
        validate_runtime_prelaunch_acceptance,
    )

    output = output.resolve()
    scratch_root = scratch_root.resolve()
    scratch_root.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    started_cpu = time.process_time_ns()
    started_wall = time.perf_counter_ns()
    contract = build_runtime_contract(repo, candidate_branch=candidate_branch)
    technical = validate_cold_resume_fixture(scratch_root)
    checkpoint_bytes = sum(
        path.stat().st_size for path in scratch_root.glob("*.json") if path.is_file()
    )
    _current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    core: dict[str, Any] = {
        "schema": "FSBS_R01_RUNTIME_V2_PRELAUNCH_ACCEPTANCE",
        "terminal_status": "RUNTIME_V2_TECHNICALLY_ACCEPTED",
        "run_id": RUN_ID,
        "runtime_contract": contract,
        "payload_argv": contract["payload_argv"],
        "reserved_output_effect": {
            **contract["effect"],
            "reserved_not_created": not (repo / OUTPUT_ROOT).exists(),
        },
        "technical_fixture_validation": technical,
        "firewall": {
            "registered_seed_execution": False,
            "registered_arm_execution": False,
            "scientific_training_or_evaluation": False,
            "question_relevant_values": False,
            "scientific_first_true_outcome": False,
            "hmasd_run_operation": False,
            "experiment_operator_requested": False,
            "provider_or_external_effect": False,
        },
        "empirical_activity_released": False,
        "operator_now": False,
        "effect_refs": [],
    }
    if core["reserved_output_effect"]["reserved_not_created"] is not True:
        raise PermissionError("replacement output root must remain absent in prelaunch")
    deterministic_core_sha256 = hashlib.sha256(_canonical(core)).hexdigest()
    acceptance = {
        **core,
        "deterministic_core_sha256": deterministic_core_sha256,
        "actual_technical_measurements": {
            "scope": "runtime-v2-candidate-local-build-validate-atomic-write",
            "cpu_ns": observe_positive_process_cpu_ns(started_cpu),
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
    validate_runtime_prelaunch_acceptance(acceptance, repo)
    _atomic_write(output, acceptance)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build the result-blind FSBS R01 runtime V2 prelaunch acceptance."
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    parser.add_argument("--candidate-branch", required=True)
    arguments = parser.parse_args(argv)
    write_runtime_prelaunch_acceptance(
        arguments.output,
        Path(__file__).resolve().parents[4],
        candidate_branch=arguments.candidate_branch,
        scratch_root=arguments.scratch_root,
    )


if __name__ == "__main__":
    main()

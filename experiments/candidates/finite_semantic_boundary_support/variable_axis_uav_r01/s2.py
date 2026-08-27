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

from .engine import dispatch_technical_branches, fixed_technical_shards, run_sequential_shards
from .result import build_complete_technical_result, write_complete_technical_result
from .s2_validation import validate_acceptance


AUTHORITY_PATH = (
    "docs/research/candidates/finite_semantic_boundary_support/"
    "FSBS_VARIABLE_AXIS_COOPERATIVE_UAV_SCIENCE_AUTHORITY_R01_20260827.md"
)
S0_PATH = (
    "temp/directions/finite_semantic_boundary_support/test/variable_axis_uav_r01/"
    "s0/g1/FSBS_R01_S0_TECHNICAL_ACCEPTANCE.json"
)
S1_PATH = (
    "temp/directions/finite_semantic_boundary_support/test/variable_axis_uav_r01/"
    "s1/g1/FSBS_R01_S1_TECHNICAL_ACCEPTANCE.json"
)
SOURCE_NAMES = (
    "learner.py",
    "engine.py",
    "checkpoint.py",
    "result.py",
    "s2.py",
    "s2_validation.py",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _file_ref(repo: Path, path: Path) -> dict[str, Any]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repo).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def _load_accepted(repo: Path, relative: str, schema: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = repo / relative
    ref = _file_ref(repo, path)
    value = json.loads(path.read_text(encoding="utf-8"))
    terminal = value.get("technical_acceptance", {}).get("terminal_status")
    if terminal is None:
        terminal = value.get("evidence_tree", {}).get("terminal_status")
    if value.get("schema") != schema or terminal != "TECHNICALLY_ACCEPTED" or value.get("effect_refs") != []:
        raise ValueError(f"accepted technical input drifted: {relative}")
    for declared in value.get("source_manifest", []):
        current = _file_ref(repo, repo / declared["path"])
        if current["sha256"] != declared["sha256"]:
            raise ValueError(f"accepted source drifted: {declared['path']}")
    return ref, value


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _projection(s1: Mapping[str, Any], s1_ref: Mapping[str, Any]) -> dict[str, Any]:
    source = s1["cost_capacity_projection"]["complete_conditional_transaction"]
    return {
        "kind": "FRESH_RESULT_BLIND_PROJECTION_NOT_EXECUTION",
        "basis_s1_sha256": s1_ref["sha256"],
        "transactions": 157_696,
        "device": "CPU",
        "workers": 1,
        "sequential_arm_seed_shards": 16,
        "transactions_per_shard": 8_896,
        "wall_seconds": {
            case: source["scenarios"][case]["wall_seconds_ceiling"]
            for case in ("low", "central", "high")
        },
        "hard_caps": {
            "cpu_seconds": 1_200,
            "wall_seconds": 2_400,
            "peak_memory_bytes": 1_073_741_824,
            "scratch_bytes": 536_870_912,
            "durable_result_bytes": 268_435_456,
        },
        "complete_transaction_executed": False,
    }


def _build_core(output: Path) -> tuple[dict[str, Any], int, int]:
    repo = _repo_root()
    authority_ref = _file_ref(repo, repo / AUTHORITY_PATH)
    s0_ref, s0 = _load_accepted(
        repo, S0_PATH, "FSBS_R01_S0_HOST_SUPPORT_FIREWALL_V1"
    )
    s1_ref, s1 = _load_accepted(
        repo, S1_PATH, "FSBS_R01_S1_LEARNER_FREE_TECHNICAL_BINDING_V1"
    )
    if (
        s0["authority_ref"]["sha256"] != authority_ref["sha256"]
        or s1["authority_ref"]["sha256"] != authority_ref["sha256"]
        or s1["accepted_s0_ref"]["sha256"] != s0_ref["sha256"]
    ):
        raise ValueError("R01/S0/S1 current-byte chain drifted")

    checkpoint_path = output.with_name("FSBS_R01_S2_TECHNICAL_CHECKPOINT.json")
    result_path = output.with_name("FSBS_R01_S2_COMPLETE_TECHNICAL_RESULT.json")
    orchestration = run_sequential_shards(
        fixed_technical_shards(), checkpoint_path=checkpoint_path
    )
    branches = dispatch_technical_branches(orchestration)
    technical_result = build_complete_technical_result(orchestration, branches)
    write_complete_technical_result(result_path, technical_result)
    checkpoint_ref = {
        "path": checkpoint_path.name,
        "sha256": hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
    }
    result_ref = {
        "path": result_path.name,
        "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
    }
    package = Path(__file__).resolve().parent
    source_manifest = [_file_ref(repo, package / name) for name in SOURCE_NAMES]
    core: dict[str, Any] = {
        "schema": "FSBS_R01_S2_TECHNICAL_ACCEPTANCE_V1",
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "terminal_status": "TECHNICALLY_ACCEPTED",
        "effect_refs": [],
        "authority_ref": authority_ref,
        "accepted_s0_ref": {**s0_ref, "schema": s0["schema"]},
        "accepted_s1_ref": {**s1_ref, "schema": s1["schema"]},
        "source_manifest": source_manifest,
        "technical_artifact_refs": [checkpoint_ref, result_ref],
        "technical_fixture_acceptance": {
            "shards": 2,
            "windows": 4,
            "grouped_updates": len(orchestration["update_ledger"]),
            "branch_dispatches": len(branches),
            "workers": orchestration["workers"],
            "registered_seed_or_arm_used": orchestration["registered_seed_or_arm_used"],
            "cross_arm_or_seed_state": orchestration["cross_arm_or_seed_state"],
            "repeated_update": len(orchestration["update_ledger"])
            != len(set(orchestration["update_ledger"])),
            "question_relevant_values": None,
            "complete_only_result": technical_result["complete"],
        },
        "firewall": {
            "registered_seed_execution": False,
            "registered_arm_execution": False,
            "complete_scientific_transaction": False,
            "scientific_training_or_evaluation": False,
            "effect_or_estimand_values": False,
            "interval_values": False,
            "scientific_first_true_outcome": False,
            "partial_package_access": False,
            "question_relevant_output": False,
            "result_query_enabled": False,
            "experiment_operator_requested": False,
            "provider_or_external_effect": False,
        },
        "runtime_input_firewall": {
            "accepted_cli_options": ["--output"],
            "forbidden_cli_options": [
                "--seed", "--arm", "--partial", "--result", "--query", "--registered"
            ],
            "fail_closed": True,
        },
        "complete_transaction_projection": _projection(s1, s1_ref),
        "next_boundary": "FSBS-R01-S3-COMPLETE-SCIENTIFIC-ACTIVITY-DECISION",
    }
    core["evidence_tree"] = validate_acceptance(
        core, orchestration, branches, technical_result
    )
    checkpoint_bytes = checkpoint_path.stat().st_size
    result_bytes = result_path.stat().st_size
    return core, checkpoint_bytes, result_bytes


def write_acceptance(output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    started_cpu = time.process_time_ns()
    started_wall = time.perf_counter_ns()
    core, checkpoint_bytes, result_bytes = _build_core(output)
    core["deterministic_core_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    _canonical(core)
    _current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    acceptance = dict(core)
    acceptance["technical_measurements"] = {
        "scope": "S2-fixed-nonregistered-build-validate-atomic-write",
        "cpu_ns": time.process_time_ns() - started_cpu,
        "wall_ns": time.perf_counter_ns() - started_wall,
        "peak_memory_bytes": peak_memory,
        "peak_memory_method": "tracemalloc-python-allocations",
        "scratch_peak_bytes": checkpoint_bytes + result_bytes,
        "storage_bytes": 0,
        "io": {
            "output_bytes": 0,
            "checkpoint_bytes": checkpoint_bytes,
            "technical_result_bytes": result_bytes,
            "atomic_replace_count": 6,
        },
    }
    while True:
        payload = _canonical(acceptance) + b"\n"
        storage = len(payload) + checkpoint_bytes + result_bytes
        measurements = acceptance["technical_measurements"]
        if (
            measurements["io"]["output_bytes"] == len(payload)
            and measurements["storage_bytes"] == storage
        ):
            break
        measurements["io"]["output_bytes"] = len(payload)
        measurements["storage_bytes"] = storage
    _atomic_write(output, acceptance)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen nonregistered FSBS R01 S2 technical acceptance."
    )
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    write_acceptance(arguments.output)


if __name__ == "__main__":
    main()

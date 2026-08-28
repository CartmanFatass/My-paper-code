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

from .s1_binding import build_binding


AUTHORITY_PATH = (
    "docs/research/candidates/finite_semantic_boundary_support/"
    "FSBS_VARIABLE_AXIS_COOPERATIVE_UAV_SCIENCE_AUTHORITY_R01_20260827.md"
)
S0_PATH = (
    "temp/directions/finite_semantic_boundary_support/test/variable_axis_uav_r01/"
    "s0/g1/FSBS_R01_S0_TECHNICAL_ACCEPTANCE.json"
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


def _source_manifest(repo: Path) -> list[dict[str, Any]]:
    package = Path(__file__).resolve().parent
    names = ("s1.py", "s1_binding.py", "s1_validation.py")
    return [_file_ref(repo, package / name) for name in names]


def _cost_capacity_projection(s0: dict[str, Any]) -> dict[str, Any]:
    total = 157_696
    scenarios = {
        "low": {
            "assumed_transactions_per_second": 10_000,
            "wall_seconds_ceiling": 16,
            "cpu_seconds_ceiling": 16,
            "peak_memory_bytes": 134_217_728,
            "scratch_bytes": 67_108_864,
            "durable_result_bytes": 33_554_432,
        },
        "central": {
            "assumed_transactions_per_second": 2_000,
            "wall_seconds_ceiling": 79,
            "cpu_seconds_ceiling": 79,
            "peak_memory_bytes": 268_435_456,
            "scratch_bytes": 134_217_728,
            "durable_result_bytes": 67_108_864,
        },
        "high": {
            "assumed_transactions_per_second": 263,
            "wall_seconds_ceiling": 600,
            "cpu_seconds_ceiling": 600,
            "peak_memory_bytes": 1_073_741_824,
            "scratch_bytes": 536_870_912,
            "durable_result_bytes": 268_435_456,
        },
    }
    construction = {
        "low": {
            "engineer_hours": 16,
            "technical_test_cpu_seconds": 60,
            "technical_test_wall_seconds": 180,
            "peak_memory_bytes": 268_435_456,
            "scratch_bytes": 67_108_864,
        },
        "central": {
            "engineer_hours": 32,
            "technical_test_cpu_seconds": 300,
            "technical_test_wall_seconds": 600,
            "peak_memory_bytes": 536_870_912,
            "scratch_bytes": 134_217_728,
        },
        "high": {
            "engineer_hours": 56,
            "technical_test_cpu_seconds": 1_200,
            "technical_test_wall_seconds": 2_400,
            "peak_memory_bytes": 1_073_741_824,
            "scratch_bytes": 536_870_912,
        },
    }
    s0_wall_ns = int(s0["technical_measurements"]["wall_ns"])
    s0_rate_floor = (15_360 * 1_000_000_000) // s0_wall_ns
    return {
        "kind": "STATIC_RESULT_BLIND_PLANNING_NOT_MEASUREMENT",
        "basis": {
            "accepted_s0_gate_transactions": 15_360,
            "accepted_s0_wall_ns": s0_wall_ns,
            "accepted_s0_transactions_per_second_floor": s0_rate_floor,
            "later_learner_overhead_measured": False,
            "projection_selected_by_result": False,
        },
        "construction_engineer_hours": {
            case: row["engineer_hours"] for case, row in construction.items()
        },
        "learner_construction_scenarios": construction,
        "complete_conditional_transaction": {
            "transactions": total,
            "device": "CPU",
            "workers": 1,
            "hard_caps": {
                "wall_seconds": 600,
                "peak_memory_bytes": 1_073_741_824,
                "durable_result_bytes": 268_435_456,
            },
            "scenarios": scenarios,
            "safe_shard_plan": {
                "execution": "SEQUENTIAL_ONE_CPU_WORKER",
                "retained_gate_transactions": 15_360,
                "arm_seed_shards": 16,
                "transactions_per_arm_seed_shard": 1_984 + 4 * 1_728,
                "partial_shard_value_exposed": False,
                "final_commit": "ONLY_AFTER_ALL_SHARDS_AND_COMPLETE_MANIFEST_VALIDATE",
            },
        },
    }


def build_acceptance() -> dict[str, Any]:
    repo = _repo_root()
    authority_ref = _file_ref(repo, repo / AUTHORITY_PATH)
    s0_path = repo / S0_PATH
    accepted_s0_ref = _file_ref(repo, s0_path)
    s0 = json.loads(s0_path.read_text(encoding="utf-8"))
    if (
        s0.get("schema") != "FSBS_R01_S0_HOST_SUPPORT_FIREWALL_V1"
        or s0.get("evidence_tree", {}).get("terminal_status") != "TECHNICALLY_ACCEPTED"
        or s0.get("effect_refs") != []
        or s0.get("authority_ref", {}).get("sha256") != authority_ref["sha256"]
    ):
        raise ValueError("accepted S0 or R01 current-byte contract drifted")
    accepted_sources: list[dict[str, Any]] = []
    for declared in s0["source_manifest"]:
        current = _file_ref(repo, repo / declared["path"])
        if current["sha256"] != declared["sha256"]:
            raise ValueError(f"accepted S0 source drifted: {declared['path']}")
        accepted_sources.append(current)

    acceptance = build_binding()
    acceptance.update(
        {
            "authority_ref": authority_ref,
            "accepted_s0_ref": {
                **accepted_s0_ref,
                "schema": s0["schema"],
                "terminal_status": s0["evidence_tree"]["terminal_status"],
                "effect_refs": s0["effect_refs"],
                "deterministic_core_sha256": s0["deterministic_core_sha256"],
            },
            "accepted_s0_source_refs": accepted_sources,
            "source_manifest": _source_manifest(repo),
            "runtime_input_firewall": {
                "accepted_cli_options": ["--output"],
                "forbidden_cli_options": [
                    "--seed",
                    "--arm",
                    "--reward",
                    "--loss",
                    "--gradient",
                    "--optimizer",
                    "--checkpoint",
                    "--model",
                    "--policy-output",
                    "--result",
                ],
                "numeric_question_values_accepted": False,
                "fail_closed": True,
            },
            "cost_capacity_projection": _cost_capacity_projection(s0),
            "technical_acceptance": {
                "terminal_status": "TECHNICALLY_ACCEPTED",
                "next_boundary": "FSBS-R01-S2-CONDITIONAL-LEARNER-CONSTRUCTION-DECISION",
                "learner_authority_granted": False,
                "scientific_transaction_authority_granted": False,
            },
        }
    )
    acceptance["deterministic_core_sha256"] = hashlib.sha256(
        _canonical(acceptance)
    ).hexdigest()
    return acceptance


def write_binding(output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    tracemalloc.start()
    started_cpu = time.process_time_ns()
    started_wall = time.perf_counter_ns()
    acceptance = build_acceptance()
    _canonical(acceptance)
    _current, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    acceptance["technical_measurements"] = {
        "scope": "S1-build-validate-canonicalize-before-atomic-replace",
        "cpu_ns": time.process_time_ns() - started_cpu,
        "wall_ns": time.perf_counter_ns() - started_wall,
        "peak_memory_bytes": peak_memory,
        "peak_memory_method": "tracemalloc-python-allocations",
        "io": {
            "authority_bytes_read": acceptance["authority_ref"]["bytes"],
            "accepted_s0_bytes_read": acceptance["accepted_s0_ref"]["bytes"],
            "accepted_s0_source_bytes_read": sum(
                row["bytes"] for row in acceptance["accepted_s0_source_refs"]
            ),
            "source_bytes_read": sum(
                row["bytes"] for row in acceptance["source_manifest"]
            ),
            "output_bytes": 0,
            "atomic_replace_count": 1,
        },
    }
    while True:
        payload = _canonical(acceptance) + b"\n"
        if acceptance["technical_measurements"]["io"]["output_bytes"] == len(payload):
            break
        acceptance["technical_measurements"]["io"]["output_bytes"] = len(payload)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Emit the learner-free FSBS R01 S1 technical binding."
    )
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    write_binding(arguments.output)


if __name__ == "__main__":
    main()

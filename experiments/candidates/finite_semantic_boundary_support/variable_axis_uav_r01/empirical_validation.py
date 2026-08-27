from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Mapping

from .empirical_contract import ARMS, REGISTERED_SEEDS
from .engine import fixed_technical_shards, run_sequential_shards


def validate_prelaunch_dossier(dossier: Mapping[str, Any], repo: Path) -> None:
    if dossier.get("schema") != "FSBS_R01_S3_PRELAUNCH_DOSSIER_V1":
        raise ValueError("prelaunch dossier schema is invalid")
    for ref in dossier["source_test_manifest"]["refs"]:
        from hashlib import sha256

        if sha256((repo / ref["path"]).read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError(f"source/test bytes drifted: {ref['path']}")
    checkpoints = dossier["checkpoint_identities"]
    if len(checkpoints) != len(ARMS) * len(REGISTERED_SEEDS):
        raise ValueError("checkpoint identity panel is incomplete")
    if any(row["materialized"] for row in checkpoints):
        raise ValueError("S3 cannot materialize registered checkpoints")
    reserved = repo / dossier["boundary"]["output_root"]
    if reserved.exists():
        raise PermissionError("reserved registered output root must remain absent in S3")
    if dossier["git_prerequisites"]["release_ready"]:
        raise PermissionError("shared checkout cannot be release ready")
    if dossier["empirical_activity_released"] or dossier["operator_now"]:
        raise PermissionError("empirical activity is not released in S3")
    if dossier["effect_refs"]:
        raise PermissionError("S3 prelaunch dossier cannot own effects")
    tree = dossier["evidence_tree"]
    if tree["terminal_status"] != "PRELAUNCH_TECHNICALLY_BOUND" or any(
        node["status"] != "PASS" for node in tree["nodes"]
    ):
        raise ValueError("prelaunch evidence tree is incomplete")


def validate_cold_resume_fixture(root: Path) -> dict[str, Any]:
    shards = fixed_technical_shards()
    uninterrupted = run_sequential_shards(
        shards, checkpoint_path=root / "uninterrupted.json"
    )
    resumed_path = root / "resumed.json"
    paused = run_sequential_shards(
        shards,
        checkpoint_path=resumed_path,
        stop_after_windows=1,
    )
    if paused["terminal_status"] != "TECHNICAL_PAUSED":
        raise ValueError("technical cold-resume fixture did not pause")
    resumed = run_sequential_shards(
        shards, checkpoint_path=resumed_path, resume=True
    )
    equal = (
        uninterrupted["fixture_state_digests"] == resumed["fixture_state_digests"]
        and uninterrupted["update_ledger"] == resumed["update_ledger"]
    )
    if not equal or len(resumed["update_ledger"]) != len(set(resumed["update_ledger"])):
        raise ValueError("technical cold resume repeated or changed an update")
    return {
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "cold_resume_equal": True,
        "repeated_update": False,
        "cross_arm_or_seed_state": False,
        "registered_seed_or_arm_used": False,
        "effect_refs": [],
    }


def assert_no_terminal_rerun(root: Path) -> None:
    terminal_path = root / "terminal.json"
    if not terminal_path.exists():
        return
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    if terminal.get("complete") is True or terminal.get("status") in {
        "SUCCEEDED",
        "COMPLETE",
        "COMPLETED",
    }:
        raise PermissionError("complete terminal forbids registered rerun")


def validate_runtime_prelaunch_acceptance(
    acceptance: Mapping[str, Any], repo: Path
) -> dict[str, Any]:
    if acceptance.get("schema") != "FSBS_R01_RUNTIME_V2_PRELAUNCH_ACCEPTANCE":
        raise ValueError("runtime V2 acceptance schema is invalid")
    if acceptance.get("terminal_status") != "RUNTIME_V2_TECHNICALLY_ACCEPTED":
        raise ValueError("runtime V2 acceptance is not technically complete")
    contract = acceptance.get("runtime_contract")
    if not isinstance(contract, Mapping) or contract.get("schema") != "FSBS_R01_CANDIDATE_RUNTIME_CONTRACT_V2":
        raise ValueError("runtime V2 candidate-local contract is invalid")
    parameters = contract.get("parameters")
    estimate = contract.get("resource_estimate")
    effect = contract.get("effect")
    if not isinstance(parameters, Mapping) or parameters.get("effect_refs") != [effect]:
        raise PermissionError("runtime V2 acceptance Effect binding is invalid")
    expected_caps = {
        "wall_seconds": 600,
        "cpu_seconds": 600,
        "peak_memory_bytes": 1_073_741_824,
        "scratch_bytes": 536_870_912,
        "durable_result_bytes": 268_435_456,
        "workers": 1,
        "threads_per_worker": 1,
    }
    if parameters.get("resource_caps") != expected_caps:
        raise PermissionError("runtime V2 acceptance resource caps are invalid")
    if not isinstance(estimate, Mapping) or any(
        estimate.get(field) != expected_caps[field]
        for field in expected_caps
    ):
        raise PermissionError("runtime V2 estimate does not equal full frozen caps")
    from .empirical_manifest import (
        observe_candidate_blob_hashes,
        validate_candidate_source_binding,
    )

    validate_candidate_source_binding(
        contract,
        observe_candidate_blob_hashes(repo, str(contract["candidate_head"]), contract),
    )
    reserved = acceptance.get("reserved_output_effect")
    if (
        reserved != {**effect, "reserved_not_created": True}
        or (repo / str(effect["resource_id"])).exists()
    ):
        raise PermissionError("runtime V2 reserved CREATE_ONLY root boundary is invalid")
    technical = acceptance.get("technical_fixture_validation")
    if not isinstance(technical, Mapping) or (
        technical.get("cold_resume_equal") is not True
        or technical.get("repeated_update") is not False
        or technical.get("cross_arm_or_seed_state") is not False
        or technical.get("registered_seed_or_arm_used") is not False
    ):
        raise ValueError("runtime V2 technical mirror validation is incomplete")
    if (
        acceptance.get("empirical_activity_released") is not False
        or acceptance.get("operator_now") is not False
        or acceptance.get("effect_refs") != []
        or any(acceptance.get("firewall", {}).values())
    ):
        raise PermissionError("runtime V2 prelaunch firewall is open")
    deterministic = {
        key: value
        for key, value in acceptance.items()
        if key not in {"actual_technical_measurements", "deterministic_core_sha256"}
    }
    digest = hashlib.sha256(
        json.dumps(deterministic, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if acceptance.get("deterministic_core_sha256") != digest:
        raise ValueError("runtime V2 deterministic core digest is invalid")
    return {
        "accepted": True,
        "source_test_ref_count": len(contract["source_test_manifest"]["refs"]),
        "full_caps_equal": True,
        "single_create_only_effect": True,
    }

from __future__ import annotations

import json
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

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence
from .empirical_contract import AUTHORITY_REFS


SCHEMA = "FSBS_R01_S2_COMPLETE_TECHNICAL_RESULT_V1"
BRANCHES = {"NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"}


def _temp_directory(path: Path) -> str:
    value = str(path)
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        return "\\\\?\\" + value
    return value


def build_complete_technical_result(
    orchestration: Mapping[str, Any], branches: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if orchestration.get("terminal_status") != "TECHNICAL_COMPLETE":
        raise ValueError("complete technical result requires complete orchestration")
    shard_ids = set(orchestration.get("fixture_state_digests", {}))
    if len(shard_ids) != 2 or len(branches) != 8:
        raise ValueError("complete technical result requires two shards and eight branches")
    by_shard = {
        shard_id: {row["branch"] for row in branches if row.get("shard_id") == shard_id}
        for shard_id in shard_ids
    }
    if any(value != BRANCHES for value in by_shard.values()) or any(
        row.get("question_relevant_values") is not None
        or row.get("resource_receipt") != [1, 1]
        or row.get("updates_parameters") is not False
        for row in branches
    ):
        raise ValueError("complete technical result branch contract is invalid")
    canonical = json.dumps(
        {"orchestration": orchestration, "branches": list(branches)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema": SCHEMA,
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "complete": True,
        "registered_manifest": False,
        "scientific_first_true_outcome": None,
        "question_relevant_values": None,
        "effect_refs": [],
        "shard_count": 2,
        "branch_count": 8,
        "measurement_schema_bound": True,
        "control_invariants_bound": True,
        "orchestration_digest": hashlib.sha256(canonical).hexdigest(),
    }


def write_complete_technical_result(path: Path, value: Mapping[str, Any]) -> None:
    if (
        value.get("schema") != SCHEMA
        or value.get("complete") is not True
        or value.get("registered_manifest") is not False
        or value.get("question_relevant_values") is not None
        or value.get("effect_refs") != []
    ):
        raise ValueError("only a complete nonregistered technical result may be written")
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".tr.", suffix=".tmp", dir=_temp_directory(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, _temp_directory(path))
    finally:
        temporary.unlink(missing_ok=True)


MIRROR_SCHEMA = "FSBS_R01_REGISTERED_COMPLETE_RESULT_V2_MIRROR"
REGISTERED_SCHEMA = "FSBS_R01_REGISTERED_COMPLETE_RESULT_V2"
EVIDENCE_NODES = (
    "release-contract",
    "retained-support-gate",
    "exact-transaction-count",
    "sixteen-isolated-checkpoints",
    "cold-resume-no-repeated-update",
    "complete-frozen-evaluation-panel",
    "control-invariants",
    "resource-caps",
    "atomic-complete-only-publication",
)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".rs.", suffix=".tmp", dir=_temp_directory(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, _temp_directory(path))
    finally:
        temporary.unlink(missing_ok=True)


def build_result_blind_complete_mirror(plan: Mapping[str, Any]) -> dict[str, Any]:
    if (
        plan.get("fixture_kind") != "RESULT_BLIND_PLAN_ONLY"
        or plan.get("registered_total_transactions") != 157_696
        or plan.get("checkpoint_count") != 16
    ):
        raise ValueError("complete-only mirror requires the exact result-blind plan")
    return {
        "schema": MIRROR_SCHEMA,
        "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
        "complete": True,
        "registered_total_transactions": 157_696,
        "checkpoint_count": 16,
        "question_relevant_values": None,
        "scientific_first_true_outcome": None,
        "evidence_tree": {
            "terminal_status": "COMPLETE_ONLY_MIRROR",
            "nodes": [{"id": node, "status": "PASS"} for node in EVIDENCE_NODES],
        },
        "effect_refs": [],
    }


def write_result_blind_complete_mirror(path: Path, value: Mapping[str, Any]) -> None:
    if (
        value.get("schema") != MIRROR_SCHEMA
        or value.get("fixture_kind") != "NONREGISTERED_RESULT_BLIND_MIRROR"
        or value.get("complete") is not True
        or value.get("question_relevant_values") is not None
        or value.get("scientific_first_true_outcome") is not None
        or value.get("effect_refs") != []
    ):
        raise ValueError("result-blind publication is complete-only")
    _atomic_json(path, value)


def build_registered_complete_result(
    receipt: Mapping[str, Any], *, release: Mapping[str, Any]
) -> dict[str, Any]:
    if release.get("released") is not True:
        raise PermissionError("registered result requires validated release")
    required = {
        "complete": True,
        "registered_total_transactions": 157_696,
        "training_decisions": 31_744,
        "evaluation_decisions": 110_592,
        "gate_transactions": 15_360,
        "workers": 1,
        "threads_per_worker": 1,
        "repeated_update": False,
        "cross_arm_or_seed_state": False,
        "terminal_rerun": False,
    }
    for field, expected in required.items():
        if receipt.get(field) != expected:
            raise ValueError(f"registered complete-only receipt field {field} is invalid")
    checkpoints = receipt.get("checkpoint_refs")
    measurements = receipt.get("measurements")
    training_measurements = receipt.get("training_measurements")
    effects = receipt.get("effects")
    tree = receipt.get("evidence_tree")
    if not isinstance(checkpoints, list) or len(checkpoints) != 16:
        raise ValueError("registered result requires sixteen checkpoints")
    if len({(row.get("arm"), row.get("seed")) for row in checkpoints}) != 16:
        raise ValueError("registered checkpoint identities are not isolated")
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("registered result requires complete frozen measurements")
    if not isinstance(training_measurements, list) or len(training_measurements) != 16:
        raise ValueError("registered result requires sixteen training measurement rows")
    if not isinstance(effects, list) or len(effects) != 24:
        raise ValueError("registered result requires all paired seed/envelope effects")
    if not isinstance(tree, Mapping) or tree.get("terminal_status") != "REGISTERED_COMPLETE":
        raise ValueError("registered evidence tree is incomplete")
    if receipt.get("authority_refs") != [dict(ref) for ref in AUTHORITY_REFS]:
        raise ValueError("registered result R01 authority refs are incomplete")
    source_manifest = receipt.get("source_manifest")
    if not isinstance(source_manifest, Mapping) or not source_manifest.get("refs"):
        raise ValueError("registered result source manifest is incomplete")
    retained_gate = receipt.get("retained_gate")
    if (
        not isinstance(retained_gate, Mapping)
        or retained_gate.get("terminal_status") != "TECHNICALLY_ACCEPTED"
        or retained_gate.get("transactions") != 15_360
    ):
        raise ValueError("registered result retained gate is incomplete")
    firewall = receipt.get("result_firewall")
    if firewall != {
        "partial_result_published": False,
        "question_values_in_checkpoint": False,
        "complete_only": True,
        "terminal_rerun": False,
    }:
        raise ValueError("registered result firewall is invalid")
    anomalies = receipt.get("anomalies")
    if not isinstance(anomalies, list):
        raise ValueError("registered result anomalies section is invalid")
    return {
        "schema": REGISTERED_SCHEMA,
        "run_id": release["run_id"],
        "code_sha": release["code_sha"],
        "complete": True,
        "registered_total_transactions": 157_696,
        "gate_transactions": 15_360,
        "training_decisions": 31_744,
        "evaluation_decisions": 110_592,
        "workers": 1,
        "threads_per_worker": 1,
        "checkpoint_refs": checkpoints,
        "authority_refs": receipt["authority_refs"],
        "source_manifest": source_manifest,
        "retained_gate": retained_gate,
        "anomalies": anomalies,
        "result_firewall": firewall,
        "measurements": measurements,
        "training_measurements": training_measurements,
        "effects": effects,
        "control_invariants": receipt["control_invariants"],
        "scientific_first_true_outcome": receipt["scientific_first_true_outcome"],
        "declared_actual_resource_totals": receipt["declared_actual_resource_totals"],
        "evidence_tree": tree,
        "claim_ceiling": (
            "FINITE_HELDOUT_M10_CARRIER_SELECTION_TO_COORDINATION_EDGE_"
            "EXACT_SHARED_LEARNER_AND_CHURN_HOST_ONLY"
        ),
    }


def write_registered_complete_result(
    path: Path, value: Mapping[str, Any], *, release: Mapping[str, Any]
) -> None:
    if (
        release.get("released") is not True
        or value.get("schema") != REGISTERED_SCHEMA
        or value.get("run_id") != release.get("run_id")
        or value.get("code_sha") != release.get("code_sha")
        or value.get("complete") is not True
        or len(value.get("checkpoint_refs", ())) != 16
    ):
        raise ValueError("registered result publication is complete-only")
    if len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")) + 1 > 268_435_456:
        raise ValueError("registered complete result exceeds durable 256-MiB cap")
    _atomic_json(path, value)

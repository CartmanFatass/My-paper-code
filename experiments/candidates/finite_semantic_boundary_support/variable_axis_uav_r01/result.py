from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA = "FSBS_R01_S2_COMPLETE_TECHNICAL_RESULT_V1"
BRANCHES = {"NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"}


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

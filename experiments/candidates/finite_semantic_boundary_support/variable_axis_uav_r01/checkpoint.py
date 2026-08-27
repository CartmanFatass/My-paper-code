from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .learner import REGISTERED_SEEDS, TECHNICAL_ARMS


SCHEMA = "FSBS_R01_S2_TECHNICAL_CHECKPOINT_V1"


def validate_checkpoint(value: Mapping[str, Any]) -> None:
    if (
        value.get("schema") != SCHEMA
        or value.get("fixture_kind") != "NONREGISTERED_TECHNICAL_ONLY"
        or value.get("registered_manifest") is not False
        or value.get("effect_refs") != []
    ):
        raise ValueError("checkpoint is not an S2 technical-only record")
    learners = value.get("learners")
    if not isinstance(learners, Mapping) or len(learners) != 2:
        raise ValueError("checkpoint must contain exactly two technical shards")
    for snapshot in learners.values():
        if snapshot.get("arm") not in TECHNICAL_ARMS or snapshot.get("seed") in REGISTERED_SEEDS:
            raise PermissionError("checkpoint contains registered or nontechnical state")
    ledger = value.get("update_ledger")
    if not isinstance(ledger, list) or len(ledger) != len(set(ledger)):
        raise ValueError("checkpoint update ledger contains a repeated update")
    cursor = value.get("cursor")
    if not isinstance(cursor, Mapping) or set(cursor) != {"shard_index", "window_index"}:
        raise ValueError("checkpoint cursor is invalid")


def write_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    validate_checkpoint(value)
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


def load_checkpoint(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    validate_checkpoint(value)
    return value

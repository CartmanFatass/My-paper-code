from __future__ import annotations

import json
import os
import tempfile
import hashlib
from pathlib import Path
from typing import Any, Mapping

from .learner import REGISTERED_SEEDS, TECHNICAL_ARMS
from .learner import RegisteredLinearLearner, ResultBlindLinearMirror


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
        prefix=".tc.", suffix=".tmp", dir=_temp_directory(path.parent)
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


def load_checkpoint(path: Path) -> dict[str, Any]:
    with open(_temp_directory(path.resolve()), encoding="utf-8") as stream:
        value = json.load(stream)
    validate_checkpoint(value)
    return value


PRODUCTION_SCHEMA = "FSBS_R01_PRODUCTION_CHECKPOINT_V2"


def _temp_directory(path: Path) -> str:
    value = str(path)
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        return "\\\\?\\" + value
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_content_record(path: Path, core: Mapping[str, Any]) -> dict[str, Any]:
    value = {**core, "content_sha256": hashlib.sha256(_canonical(core)).hexdigest()}
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical(value) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".cp.", suffix=".tmp", dir=_temp_directory(path.parent)
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
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_sha256": value["content_sha256"],
        "content_addressed": True,
    }


def _load_content_record(path: Path, fixture_kind: str) -> dict[str, Any]:
    with open(_temp_directory(path.resolve()), encoding="utf-8") as stream:
        value = json.load(stream)
    digest = value.pop("content_sha256", None)
    if digest != hashlib.sha256(_canonical(value)).hexdigest():
        raise ValueError("checkpoint content digest is invalid")
    if value.get("schema") != PRODUCTION_SCHEMA or value.get("fixture_kind") != fixture_kind:
        raise ValueError("production checkpoint schema or fixture kind is invalid")
    value["content_sha256"] = digest
    return value


def write_result_blind_checkpoint(
    path: Path, learner: ResultBlindLinearMirror, *, cursor: Mapping[str, Any]
) -> dict[str, Any]:
    return _write_content_record(
        path,
        {
            "schema": PRODUCTION_SCHEMA,
            "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
            "registered_manifest": False,
            "learner": learner.snapshot(),
            "cursor": dict(cursor),
            "effect_refs": [],
        },
    )


def load_result_blind_checkpoint(
    path: Path,
) -> tuple[ResultBlindLinearMirror, dict[str, Any]]:
    value = _load_content_record(path, "NONREGISTERED_RESULT_BLIND_MIRROR")
    return (
        ResultBlindLinearMirror.from_snapshot(value["learner"]),
        dict(value["cursor"]),
    )


def write_registered_checkpoint(
    path: Path,
    learner: RegisteredLinearLearner,
    *,
    cursor: Mapping[str, Any],
    release: Mapping[str, Any],
) -> dict[str, Any]:
    if release.get("released") is not True:
        raise PermissionError("registered checkpoint requires validated release")
    return _write_content_record(
        path,
        {
            "schema": PRODUCTION_SCHEMA,
            "fixture_kind": "REGISTERED_R01_RELEASED",
            "run_id": release["run_id"],
            "code_sha": release["code_sha"],
            "learner": learner.snapshot(),
            "cursor": dict(cursor),
        },
    )


def load_registered_checkpoint(
    path: Path, *, release: Mapping[str, Any]
) -> tuple[RegisteredLinearLearner, dict[str, Any], str]:
    if release.get("released") is not True:
        raise PermissionError("registered checkpoint requires validated release")
    value = _load_content_record(path, "REGISTERED_R01_RELEASED")
    if value.get("run_id") != release.get("run_id") or value.get("code_sha") != release.get("code_sha"):
        raise PermissionError("registered checkpoint belongs to another release")
    return (
        RegisteredLinearLearner.from_snapshot(value["learner"], release=release),
        dict(value["cursor"]),
        str(value["content_sha256"]),
    )

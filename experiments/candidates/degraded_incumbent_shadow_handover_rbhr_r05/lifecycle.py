"""Create-only TEST lifecycle for DISH r05 Gate B synthetic evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Mapping

from .contracts import TEST_NAMESPACE


SCHEMA = "DISH_RBHR_R05_GATE_B_TEST_LIFECYCLE_V1"


class LifecycleError(ValueError):
    pass


def canonical_bytes(value: object) -> bytes:
    def validate(item: object) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise LifecycleError("canonical object key is not text")
                validate(child)
        elif isinstance(item, list):
            for child in item:
                validate(child)
        elif isinstance(item, float) and not math.isfinite(item):
            raise LifecycleError("canonical object contains a nonfinite float")
        elif item is not None and not isinstance(item, (str, int, float, bool)):
            raise LifecycleError(f"unsupported canonical type {type(item).__name__}")
    validate(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def write_once_atomic(path: Path, payload: Mapping[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    envelope = {"schema": SCHEMA, "payload": body, "payload_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest()}
    data = canonical_bytes(envelope)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise LifecycleError("write-once lifecycle destination already exists") from error
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(data).hexdigest()


def read_verified(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        envelope = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LifecycleError("lifecycle object is not canonical ASCII JSON") from error
    if canonical_bytes(envelope) != raw:
        raise LifecycleError("lifecycle object is not in canonical byte form")
    if envelope.get("schema") != SCHEMA or not isinstance(envelope.get("payload"), dict):
        raise LifecycleError("lifecycle envelope schema/payload mismatch")
    payload = envelope["payload"]
    if envelope.get("payload_sha256") != hashlib.sha256(canonical_bytes(payload)).hexdigest():
        raise LifecycleError("lifecycle payload digest mismatch")
    return payload


@dataclass(frozen=True)
class SyntheticResumeRecord:
    namespace: str
    fixture_schema: str
    synthetic_update_count: int
    lane_count: int
    transition_count: int
    model_state_digest: str
    optimizer_state_digest: str
    welford_state_digest: str
    evaluable: bool = False
    scientific_model: bool = False
    question_relevant_output: bool = False

    def __post_init__(self) -> None:
        if self.namespace != TEST_NAMESPACE:
            raise LifecycleError("resume record escaped the TEST namespace")
        if self.fixture_schema != "DISH_RBHR_R05_GATE_B_SYNTHETIC_UPDATE_V1":
            raise LifecycleError("resume fixture schema mismatch")
        if self.synthetic_update_count != 1 or self.lane_count != 32 or self.transition_count != 4096:
            raise LifecycleError("resume record does not bind the exact synthetic update")
        if self.evaluable or self.scientific_model or self.question_relevant_output:
            raise LifecycleError("synthetic resume record was made evaluable or scientific")
        for name in ("model_state_digest", "optimizer_state_digest", "welford_state_digest"):
            value = getattr(self, name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise LifecycleError(f"{name} is not lowercase SHA-256")

    def payload(self) -> dict[str, object]:
        return {"kind": "NON_EVALUABLE_TEST_RESUME", **asdict(self)}

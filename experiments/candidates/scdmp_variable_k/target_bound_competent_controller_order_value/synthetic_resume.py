"""TEST-only atomic create/cold-scan/resume mechanics for TBCC construction.

Payloads are required to identify themselves as synthetic and may not contain
scientific identity, coordinate, model, checkpoint, result, or master fields.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Final, Mapping


class SyntheticResumeError(RuntimeError):
    pass


FORBIDDEN_FIELDS: Final[frozenset[str]] = frozenset(
    {"master", "identity", "coordinate", "model", "checkpoint", "result"}
)


def fake_digest(label: str) -> str:
    if not label.startswith("TEST_ONLY:"):
        raise SyntheticResumeError("fake digest labels must be explicitly TEST-only")
    return "TEST_ONLY_FAKE_SHA256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _canonical(payload: Mapping[str, object]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def _validate_payload(payload: Mapping[str, object]) -> None:
    if payload.get("test_only") is not True or payload.get("question_relevant") is not False:
        raise SyntheticResumeError("payload must be explicitly TEST-only and question-blind")
    lowered = {str(key).lower() for key in payload}
    if lowered & FORBIDDEN_FIELDS:
        raise SyntheticResumeError("scientific identity/coordinate/model/checkpoint/result fields are forbidden")


def create_only_commit(path: Path, payload: Mapping[str, object]) -> str:
    _validate_payload(payload)
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = _canonical(payload)
    temporary = Path(str(target) + f".{os.getpid()}.TEST_ONLY.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise SyntheticResumeError("synthetic commit target is create-only") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    return fake_digest("TEST_ONLY:" + hashlib.sha256(encoded).hexdigest())


def write_interrupted_test_fragment(path: Path, content: bytes = b'{"test_only":true') -> Path:
    """Create an explicitly interrupted temporary fragment for cold-scan tests."""

    if not path.name.endswith(".TEST_ONLY.tmp"):
        raise SyntheticResumeError("interrupted fragments require .TEST_ONLY.tmp suffix")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return path


@dataclass(frozen=True)
class SyntheticFrontier:
    stage: str
    slot: str
    generation: int
    previous_fake_digest: str | None
    payload_fake_digest: str
    complete: bool = True
    test_only: bool = True
    question_relevant: bool = False

    def payload(self) -> dict[str, object]:
        if not self.stage.startswith("TEST_ONLY_") or not self.slot.startswith("TEST_ONLY_"):
            raise SyntheticResumeError("frontier stage and slot must be explicitly TEST-only")
        if isinstance(self.generation, bool) or self.generation < 0:
            raise SyntheticResumeError("frontier generation must be nonnegative")
        if self.generation == 0 and self.previous_fake_digest is not None:
            raise SyntheticResumeError("initial frontier cannot cite a predecessor")
        if self.generation > 0 and not (self.previous_fake_digest or "").startswith("TEST_ONLY_FAKE_SHA256:"):
            raise SyntheticResumeError("resumed frontier requires a TEST-only predecessor")
        if not self.payload_fake_digest.startswith("TEST_ONLY_FAKE_SHA256:"):
            raise SyntheticResumeError("frontier payload digest must be TEST-only")
        if self.complete is not True or self.test_only is not True or self.question_relevant is not False:
            raise SyntheticResumeError("only complete question-blind TEST frontiers can commit")
        return {
            "schema": "TEST_ONLY_TBCC_SYNTHETIC_FRONTIER_V1",
            "stage": self.stage,
            "slot": self.slot,
            "generation": self.generation,
            "previous_fake_digest": self.previous_fake_digest,
            "payload_fake_digest": self.payload_fake_digest,
            "complete": True,
            "test_only": True,
            "question_relevant": False,
        }


def frontier_fake_digest(frontier: SyntheticFrontier) -> str:
    return fake_digest("TEST_ONLY:" + hashlib.sha256(_canonical(frontier.payload())).hexdigest())


def commit_frontier(root: Path, frontier: SyntheticFrontier) -> tuple[Path, str]:
    filename = f"{frontier.stage}__{frontier.slot}__{frontier.generation:06d}.json"
    path = root.resolve() / filename
    create_only_commit(path, frontier.payload())
    return path, frontier_fake_digest(frontier)


def cold_scan_exact_frontier(root: Path, *, stage: str, slot: str) -> tuple[SyntheticFrontier, ...]:
    """Ignore interrupted temporaries and accept only one exact contiguous chain."""

    root = root.resolve()
    rows: list[SyntheticFrontier] = []
    for path in sorted(root.glob(f"{stage}__{slot}__*.json")):
        try:
            raw = json.loads(path.read_text(encoding="ascii"))
            if not isinstance(raw, dict) or raw.pop("schema", None) != "TEST_ONLY_TBCC_SYNTHETIC_FRONTIER_V1":
                raise ValueError("schema")
            frontier = SyntheticFrontier(**raw)
            if frontier.payload()["schema"] != "TEST_ONLY_TBCC_SYNTHETIC_FRONTIER_V1":
                raise ValueError("payload")
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise SyntheticResumeError("cold scan found an invalid committed frontier") from error
        rows.append(frontier)
    previous: str | None = None
    for expected_generation, frontier in enumerate(rows):
        if frontier.generation != expected_generation or frontier.previous_fake_digest != previous:
            raise SyntheticResumeError("cold scan found a gap or changed predecessor")
        previous = frontier_fake_digest(frontier)
    return tuple(rows)


def require_complete_synthetic_stage(
    payloads: Mapping[str, Mapping[str, object]], *, required_slots: frozenset[str]
) -> None:
    if set(payloads) != required_slots:
        raise SyntheticResumeError("partial synthetic stage is not publishable")
    for payload in payloads.values():
        _validate_payload(payload)
        if payload.get("complete") is not True:
            raise SyntheticResumeError("partial synthetic payload is not publishable")


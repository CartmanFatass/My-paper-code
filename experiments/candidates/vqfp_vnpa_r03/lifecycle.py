"""Private, atomic, fail-closed lifecycle boundary for future r03 execution.

The lifecycle publishes only a competence-complete final bundle.  Construction
tests use opaque synthetic work receipts and never store policy values.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable

from .contract import EXACT_REVISION, FROZEN_COUNTS, NATIVE_ABI_VERSION, SCIENCE_CARD_SHA256
from .native_backend import source_sha256


class LifecycleError(RuntimeError):
    pass


FROZEN_STAGE_STOPS = {
    "development": 2 * FROZEN_COUNTS["treatment_candidates"] * FROZEN_COUNTS["development_episodes"],
    "validation": 2 * FROZEN_COUNTS["finalists_each"] * FROZEN_COUNTS["validation_episodes"],
    "evaluation": FROZEN_COUNTS["evaluation_episodes"] * FROZEN_COUNTS["evaluation_arms"],
    "resampling": FROZEN_COUNTS["bootstrap_draws"],
}
COMPETENCE_FIELDS = (
    "native_admission", "rng_address", "host_integral", "policy_controls",
    "training_selection", "evaluation_panel", "resampling_terminal",
    "serialization_resume", "counts_complete", "action_legality",
    "oracle_dominance", "free_embed", "immutable_selection",
)


@dataclass(frozen=True)
class WorkRange:
    stage: str
    first: int
    stop: int

    def __post_init__(self) -> None:
        if self.stage not in {"development", "validation", "evaluation", "resampling"}:
            raise ValueError("unregistered work stage")
        if isinstance(self.first, bool) or isinstance(self.stop, bool) or self.first < 0 or self.stop <= self.first:
            raise ValueError("work range must be a nonempty half-open nonnegative range")


def input_identity(*, science_card_sha256: str, address_table: str = "r03-ten-row-v1") -> dict[str, object]:
    if science_card_sha256.lower() != SCIENCE_CARD_SHA256:
        raise LifecycleError("science-card identity mismatch")
    if address_table != "r03-ten-row-v1":
        raise LifecycleError("address-table identity mismatch")
    return {
        "schema": "VQFP_VNPA_R03_PRIVATE_IDENTITY_V1",
        "revision": EXACT_REVISION,
        "science_card_sha256": SCIENCE_CARD_SHA256,
        "native_abi": NATIVE_ABI_VERSION,
        "native_source_sha256": source_sha256(),
        "address_table": address_table,
        "byte_order": "little-endian-u32",
    }


def identity_digest(identity: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


class PrivateGeneration:
    def __init__(self, root: str | Path, identity: dict[str, object], *, synthetic_test: bool = False) -> None:
        self.root = Path(root).resolve(); self.identity = dict(identity)
        if self.identity != input_identity(science_card_sha256=SCIENCE_CARD_SHA256):
            raise LifecycleError("private generation identity is not the frozen identity")
        self.synthetic_test = synthetic_test
        self.key = identity_digest(self.identity); self.path = self.root / "private" / self.key

    def initialize(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        identity_path = self.path / "identity.json"
        if identity_path.exists() and json.loads(identity_path.read_text("utf-8")) != self.identity:
            raise LifecycleError("private generation identity mismatch")
        if not identity_path.exists(): _atomic_json(identity_path, self.identity)

    def commit_range(self, work: WorkRange, *, opaque_digest: str, complete_count: int) -> Path:
        self.initialize()
        if not self.synthetic_test and work.stop > FROZEN_STAGE_STOPS[work.stage]:
            raise LifecycleError("work range exceeds frozen stage count")
        if len(opaque_digest) != 64 or any(ch not in "0123456789abcdef" for ch in opaque_digest):
            raise ValueError("opaque_digest must be lowercase SHA-256")
        if complete_count != work.stop - work.first: raise LifecycleError("range completeness mismatch")
        for existing in self.completed_ranges(work.stage):
            if max(existing.first,work.first)<min(existing.stop,work.stop) and existing!=work:
                raise LifecycleError("committed work ranges cannot overlap")
        receipt = {"stage": work.stage, "first": work.first, "stop": work.stop,
                   "complete_count": complete_count, "opaque_digest": opaque_digest,
                   "contains_policy_value": False}
        path = self.path / "ranges" / f"{work.stage}.{work.first:08d}.{work.stop:08d}.json"
        if path.exists() and json.loads(path.read_text("utf-8")) != receipt:
            raise LifecycleError("committed range cannot be replaced")
        if not path.exists(): _atomic_json(path, receipt)
        return path

    def completed_ranges(self, stage: str) -> tuple[WorkRange, ...]:
        self.initialize(); rows=[]
        for path in sorted((self.path / "ranges").glob(f"{stage}.*.json")) if (self.path / "ranges").exists() else ():
            row=json.loads(path.read_text("utf-8")); rows.append(WorkRange(stage,row["first"],row["stop"]))
        return tuple(rows)

    def first_missing(self, stage: str, stop: int) -> int:
        cursor=0
        for row in self.completed_ranges(stage):
            if row.first > cursor: break
            if row.first <= cursor < row.stop: cursor=row.stop
        return min(cursor, stop)

    def publish_complete(self, *, expected_ranges: Iterable[WorkRange], competence: dict[str, bool]) -> Path:
        self.initialize()
        if tuple(sorted(competence)) != tuple(sorted(COMPETENCE_FIELDS)) or any(type(value) is not bool for value in competence.values()) or not all(competence.values()):
            raise LifecycleError("NO_QUESTION_RELEVANT_DATA: competence incomplete")
        expected_rows=tuple(expected_ranges);expected={(r.stage,r.first,r.stop) for r in expected_rows}
        if not self.synthetic_test:
            for stage,stage_stop in FROZEN_STAGE_STOPS.items():
                rows=sorted((r for r in expected_rows if r.stage==stage),key=lambda r:r.first)
                cursor=0
                for row in rows:
                    if row.first!=cursor:raise LifecycleError("NO_QUESTION_RELEVANT_DATA: frozen work coverage incomplete")
                    cursor=row.stop
                if cursor!=stage_stop:raise LifecycleError("NO_QUESTION_RELEVANT_DATA: frozen work coverage incomplete")
        actual=set()
        for stage in {r[0] for r in expected}:
            actual.update((r.stage,r.first,r.stop) for r in self.completed_ranges(stage))
        if actual != expected: raise LifecycleError("NO_QUESTION_RELEVANT_DATA: work ranges incomplete")
        final = self.root / "released" / self.key / "complete.json"
        _atomic_json(final, {"schema":"VQFP_VNPA_R03_COMPETENCE_COMPLETE_RELEASE_V1",
                             "identity_digest":self.key,"competence":competence,
                             "range_count":len(expected),"partial_release":False})
        return final

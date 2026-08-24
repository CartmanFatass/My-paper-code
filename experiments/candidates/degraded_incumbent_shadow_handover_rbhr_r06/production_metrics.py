"""Failure-atomic raw-metric persistence and complete r06 estimand ingestion.

The store is deliberately ignorant of scientific values: it validates identity,
coordinate inventory and finite scalar encoding, then exposes a complete block
only after every required metric key is present.  Production callers may not
read a partial block through this interface.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Iterable, Mapping

from .production_contract import ARMS, CLAIM_SCHEDULES, ENDPOINTS, REGIMES, SPEED_STRATA
from .production_estimands import assemble_complete_block_rows
from .production_inference import HARD_EVENTS, PHASES_BY_SCHEDULE, complete_estimand_manifest


class MetricStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class RawMetricRow:
    block: int
    key: tuple[str, ...]
    value: float

    def validate(self) -> None:
        if not 0 <= self.block < 24 or not self.key or any(not str(field) for field in self.key):
            raise MetricStoreError("raw metric coordinate differs")
        if not math.isfinite(float(self.value)):
            raise MetricStoreError("raw metric value is nonfinite")


@dataclass(frozen=True)
class RecoveryWitnessRow:
    block: int
    regime: str
    schedule: str
    speed: str
    opportunity: int
    trigger_valid: int
    behavior_changing: int
    d_h: float
    d_a: float

    def validate(self) -> None:
        if not 0 <= self.block < 24 or self.regime not in REGIMES or self.schedule not in CLAIM_SCHEDULES or self.speed not in SPEED_STRATA:
            raise MetricStoreError("witness coordinate differs")
        if any(value not in (0, 1) for value in (self.opportunity, self.trigger_valid, self.behavior_changing)):
            raise MetricStoreError("witness predicate differs")
        if not (math.isfinite(self.d_h) and math.isfinite(self.d_a)) or self.d_h < 0.0 or self.d_a < 0.0:
            raise MetricStoreError("witness support distance differs")
        expected = int(self.trigger_valid == 1 and self.d_h >= 1e-3 and self.d_a >= 1e-3)
        if self.behavior_changing != expected:
            raise MetricStoreError("behavior-changing support predicate differs")


def required_block_metric_keys() -> frozenset[tuple[str, ...]]:
    keys: set[tuple[str, ...]] = set()
    for arm in ARMS:
        for regime in REGIMES:
            for schedule in ("K4", "K12"):
                for speed in SPEED_STRATA:
                    keys.add(("COMPETENCE_NO_DEGRADATION", arm, regime, schedule, speed))
    for arm in ARMS:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA:
                    keys.add(("COMPETENCE_PRE_ONSET", arm, regime, schedule, speed))
    for quantity in ("Q", "DROP", "MAINTAIN", "WITNESS_GAIN", "WITNESS_CONTINUITY"):
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA:
                    keys.add(("OPPORTUNITY", quantity, regime, schedule, speed))
    for arm in ("STRUCTURED", "FLEX"):
        for quantity in ("TRIGGER_RATE", "BEHAVIOR_CHANGING_SUPPORT"):
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for speed in SPEED_STRATA:
                        keys.add(("ADAPTIVE_SUPPORT", arm, quantity, regime, schedule, speed))
    for quantity in ("NEVER_EVENT_MEAN", "WITNESS_MINUS_NEVER_EVENT_MEAN"):
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA:
                    keys.add(("NEVER_HEADROOM", quantity, regime, schedule, speed))
    populations = (*ARMS, "REAL", "SHAM")
    for population in populations:
        for event in HARD_EVENTS:
            for regime in REGIMES:
                for schedule in CLAIM_SCHEDULES:
                    for speed in SPEED_STRATA:
                        keys.add(("HARD_EVENT_RATE", population, event, regime, schedule, speed))
    for population in populations:
        for regime in REGIMES:
            for schedule in CLAIM_SCHEDULES:
                for speed in SPEED_STRATA:
                    keys.add(("ENERGY", population, regime, schedule, speed))
                    for endpoint in ENDPOINTS:
                        keys.add(("ENDPOINT", population, regime, schedule, speed, endpoint))
                    for phase in PHASES_BY_SCHEDULE[schedule]:
                        keys.add(("PHASE_ENERGY", population, regime, schedule, speed, str(phase)))
                        for endpoint in ENDPOINTS:
                            keys.add(("PHASE_ENDPOINT", population, regime, schedule, speed, str(phase), endpoint))
    return frozenset(keys)


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


class FailureAtomicMetricStore:
    """Append complete shards and expose only complete 24x6,990 matrices."""

    def __init__(self, root: Path, *, binding_sha256: str, test_only: bool = False) -> None:
        if len(binding_sha256) != 64:
            raise MetricStoreError("metric store binding differs")
        self.root = root.resolve(); self.binding_sha256 = binding_sha256; self.test_only = bool(test_only)
        self.manifest_path = self.root / "metric_manifest.json"
        if self.manifest_path.exists():
            value = json.loads(self.manifest_path.read_text(encoding="ascii"))
            if value != self._manifest():
                raise MetricStoreError("metric store resume binding differs")
        else:
            _replace(self.manifest_path, _canonical(self._manifest()))

    def _manifest(self) -> dict[str, object]:
        return {"schema": "DISH_RBHR_R06_METRIC_STORE_V1", "binding_sha256": self.binding_sha256,
                "blocks": 24, "estimands": 6_990, "test_only": self.test_only,
                "partial_values_exposed": False}

    def append_shard(self, shard_id: str, rows: Iterable[RawMetricRow]) -> dict[str, object]:
        if not shard_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in shard_id):
            raise MetricStoreError("metric shard identifier differs")
        packed = []
        for row in rows:
            row.validate(); packed.append({**asdict(row), "key": list(row.key)})
        if not packed:
            raise MetricStoreError("metric shard is empty")
        payload = _canonical({"schema": "DISH_RBHR_R06_METRIC_SHARD_V1", "binding_sha256": self.binding_sha256, "rows": packed})
        target = self.root / "shards" / f"{shard_id}.json"
        if target.exists():
            if target.read_bytes() != payload:
                raise MetricStoreError("metric shard replacement differs")
        else:
            _replace(target, payload)
        return {"shard": shard_id, "sha256": hashlib.sha256(payload).hexdigest(), "row_count": len(packed)}

    def _rows(self) -> dict[int, dict[tuple[str, ...], float]]:
        values = {block: {} for block in range(24)}
        for path in sorted((self.root / "shards").glob("*.json")):
            shard = json.loads(path.read_text(encoding="ascii"))
            if shard.get("binding_sha256") != self.binding_sha256:
                raise MetricStoreError("metric shard binding differs")
            for item in shard["rows"]:
                row = RawMetricRow(int(item["block"]), tuple(item["key"]), float(item["value"])); row.validate()
                prior = values[row.block].get(row.key)
                if prior is not None and prior != row.value:
                    raise MetricStoreError("metric coordinate was replaced")
                values[row.block][row.key] = row.value
        return values

    def complete_estimand_matrix(self) -> tuple[tuple[float, ...], ...]:
        expected = required_block_metric_keys(); manifest = complete_estimand_manifest(); output = []
        for block, metrics in self._rows().items():
            missing = expected - set(metrics)
            if missing:
                raise MetricStoreError(f"block {block} metric inventory incomplete ({len(missing)} absent)")
            assembled = assemble_complete_block_rows(metrics)
            if tuple(assembled) != manifest:
                raise MetricStoreError("assembled estimand order differs")
            output.append(tuple(assembled[name] for name in manifest))
        if len(output) != 24 or any(len(row) != 6_990 for row in output):
            raise MetricStoreError("complete 24x6990 matrix differs")
        return tuple(output)


def witness_support_metrics(rows: Iterable[RecoveryWitnessRow], *, arm: str) -> dict[tuple[str, ...], float]:
    if arm not in ("STRUCTURED", "FLEX"):
        raise MetricStoreError("adaptive witness arm differs")
    groups: dict[tuple[str, str, str], list[RecoveryWitnessRow]] = {}
    for row in rows:
        row.validate(); groups.setdefault((row.regime, row.schedule, row.speed), []).append(row)
    expected = {(r, s, v) for r in REGIMES for s in CLAIM_SCHEDULES for v in SPEED_STRATA}
    if set(groups) != expected:
        raise MetricStoreError("witness support cell inventory differs")
    result = {}
    for key, cell in groups.items():
        opportunities = [row for row in cell if row.opportunity]
        denominator = len(opportunities)
        trigger = sum(row.trigger_valid for row in opportunities) / denominator if denominator else 0.0
        changing = sum(row.behavior_changing for row in opportunities) / denominator if denominator else 0.0
        result[("ADAPTIVE_SUPPORT", arm, "TRIGGER_RATE", *key)] = trigger
        result[("ADAPTIVE_SUPPORT", arm, "BEHAVIOR_CHANGING_SUPPORT", *key)] = changing
    return result


__all__ = ["FailureAtomicMetricStore", "MetricStoreError", "RawMetricRow", "RecoveryWitnessRow",
           "required_block_metric_keys", "witness_support_metrics"]

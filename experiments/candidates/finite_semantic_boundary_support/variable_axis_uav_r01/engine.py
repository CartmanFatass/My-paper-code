from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

from .checkpoint import SCHEMA as CHECKPOINT_SCHEMA
from .checkpoint import load_checkpoint, write_checkpoint
from .learner import TechnicalDecision, TechnicalLinearLearner


@dataclass(frozen=True)
class TechnicalShard:
    shard_id: str
    arm: str
    seed: int
    fixture_kind: str = "NONREGISTERED_TECHNICAL_ONLY"
    window_count: int = 2


def fixed_technical_shards() -> tuple[TechnicalShard, TechnicalShard]:
    return (
        TechnicalShard("TECH-A-1000003", "TECHNICAL_A", 1_000_003),
        TechnicalShard("TECH-B-1000033", "TECHNICAL_B", 1_000_033),
    )


def _literal_observations(window_index: int) -> tuple[tuple[dict[str, int], ...], tuple[dict[str, int], ...]]:
    if window_index == 0:
        return (
            (
                {"surface_bit": 0, "i": 0, "r": 1},
                {"surface_bit": 1, "i": 1, "r": 0},
            ),
            (
                {"payload_bit": 0, "i": 1, "r": 0},
                {"payload_bit": 1, "i": 0, "r": 1},
            ),
        )
    return (
        (
            {"surface_bit": 1, "i": 0, "r": 0},
            {"surface_bit": 0, "i": 1, "r": 1},
        ),
        (
            {"payload_bit": 1, "i": 1, "r": 1},
            {"payload_bit": 0, "i": 0, "r": 0},
        ),
    )


def _run_window(
    learner: TechnicalLinearLearner, shard: TechnicalShard, window_index: int
) -> list[str]:
    selector_rows, controller_rows = _literal_observations(window_index)
    signals = (Fraction(1, 2), Fraction(-1, 2))
    sampled: dict[str, list[TechnicalDecision]] = {"selector": [], "controller": []}
    for head, rows in (("selector", selector_rows), ("controller", controller_rows)):
        for subscriber, row in enumerate(rows):
            features = (
                learner.selector_features(row)
                if head == "selector"
                else learner.controller_features(row)
            )
            coordinates = (
                "NONREGISTERED_FIXTURE",
                shard.shard_id,
                window_index,
                subscriber,
            )
            action, score, _addresses = learner.choose_action(
                head,
                features,
                completed_decisions=window_index * 2,
                coordinates=coordinates,
            )
            sampled[head].append(
                TechnicalDecision(action, tuple(features), score, signals[subscriber])
            )
    ledger: list[str] = []
    window_id = f"{shard.shard_id}-W{window_index}"
    for head in ("selector", "controller"):
        learner.apply_grouped_window_update(
            head, sampled[head], pair_count=2, window_id=window_id
        )
        ledger.append(f"{shard.shard_id}:{window_index}:{head}")
    return ledger


def _checkpoint_value(
    learners: dict[str, TechnicalLinearLearner],
    update_ledger: list[str],
    cursor: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema": CHECKPOINT_SCHEMA,
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "registered_manifest": False,
        "effect_refs": [],
        "cursor": cursor,
        "learners": {key: learner.snapshot() for key, learner in learners.items()},
        "update_ledger": list(update_ledger),
    }


def _receipt(
    learners: dict[str, TechnicalLinearLearner],
    update_ledger: list[str],
    cursor: dict[str, int],
    terminal_status: str,
) -> dict[str, Any]:
    return {
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "terminal_status": terminal_status,
        "workers": 1,
        "execution": "SEQUENTIAL",
        "registered_seed_or_arm_used": False,
        "cross_arm_or_seed_state": False,
        "cursor": cursor,
        "fixture_state_digests": {
            key: learner.snapshot_digest() for key, learner in learners.items()
        },
        "update_ledger": list(update_ledger),
        "question_relevant_values": None,
        "effect_refs": [],
    }


def run_sequential_shards(
    shards: Sequence[TechnicalShard],
    *,
    checkpoint_path: Path,
    resume: bool = False,
    stop_after_windows: int | None = None,
) -> dict[str, Any]:
    if tuple(shards) != fixed_technical_shards():
        raise PermissionError("S2 runs only the two fixed nonregistered technical shards")
    if resume:
        stored = load_checkpoint(checkpoint_path)
        learners = {
            key: TechnicalLinearLearner.from_snapshot(snapshot)
            for key, snapshot in stored["learners"].items()
        }
        update_ledger = list(stored["update_ledger"])
        cursor = dict(stored["cursor"])
    else:
        learners = {
            shard.shard_id: TechnicalLinearLearner(shard.arm, shard.seed)
            for shard in shards
        }
        update_ledger = []
        cursor = {"shard_index": 0, "window_index": 0}
    processed = 0
    for shard_index in range(cursor["shard_index"], len(shards)):
        shard = shards[shard_index]
        first_window = cursor["window_index"] if shard_index == cursor["shard_index"] else 0
        for window_index in range(first_window, shard.window_count):
            new_entries = _run_window(learners[shard.shard_id], shard, window_index)
            if set(new_entries) & set(update_ledger):
                raise ValueError("resume would repeat an update")
            update_ledger.extend(new_entries)
            if window_index + 1 < shard.window_count:
                cursor = {"shard_index": shard_index, "window_index": window_index + 1}
            else:
                cursor = {"shard_index": shard_index + 1, "window_index": 0}
            write_checkpoint(
                checkpoint_path, _checkpoint_value(learners, update_ledger, cursor)
            )
            processed += 1
            if stop_after_windows is not None and processed >= stop_after_windows:
                return _receipt(learners, update_ledger, cursor, "TECHNICAL_PAUSED")
    return _receipt(learners, update_ledger, cursor, "TECHNICAL_COMPLETE")


def dispatch_technical_branches(orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    if orchestration.get("terminal_status") != "TECHNICAL_COMPLETE":
        raise ValueError("branch dispatch requires complete technical orchestration")
    rows: list[dict[str, Any]] = []
    for shard_id in sorted(orchestration["fixture_state_digests"]):
        for branch in ("NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"):
            rows.append(
                {
                    "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
                    "shard_id": shard_id,
                    "branch": branch,
                    "resource_receipt": [1, 1],
                    "updates_parameters": False,
                    "measurement_schema_bound": True,
                    "control_invariants_bound": True,
                    "question_relevant_values": None,
                }
            )
    return rows

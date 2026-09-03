"""Formal raw-slice to canonical shared-metrics reconstruction for OMRC B1.

This seam accepts engine raw evidence only.  It reconstructs every tape from
the frozen host address space and never accepts caller-supplied EpisodeTape
objects or scientific summaries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from . import addressing
from .b1_contract import (
    B1_CHECKPOINT_UPDATES,
    B1_EVAL_MOTIF_IDS,
    B1_EVAL_STOCHASTIC_IDS,
    B1_SEEDS,
    B1_SLOT_ORDER,
    B1_TRAIN_EPISODE_IDS,
)
from .b1_engine import B1_RAW_EVIDENCE_SCHEMA
from .b1_shared_tables import build_b1_shared_truth_tables
from .host import DynamicHost
from .ppo import PPOConfig, config_digest
from .tapes import EpisodeTape


ARM_SEED_ORDER = B1_SLOT_ORDER
REHYDRATION_SCHEMA = "cbsc_omrc_b01_b1_metrics_rehydration_v1"
_TAPE_RECORD_FIELDS = frozenset(
    {
        "identity",
        "primitive_digest_observed",
        "draw_digest_observed",
        "draw_count_observed",
    }
)
_FULL_BINDING_FIELDS = frozenset(
    {
        "train_episode_ids_sha256",
        "full_training_tape_digest",
        "full_action_uniform_digest",
        "ppo_configuration_digest",
        "implementation_commit",
        "source_conformance_sha256",
    }
)
_REQUIRED_RAW_FIELDS = frozenset(
    {
        "schema",
        "attempt_id",
        "run_name",
        "arm",
        "seed",
        "slice",
        "full_bindings",
        "train_tapes",
        "evaluation_tapes",
    }
)


class B1MetricsRehydrateError(ValueError):
    """Raw B1 slices cannot be uniquely rehydrated into the frozen inventory."""


@dataclass(frozen=True)
class B1MetricsRehydration:
    schema: str
    unique_tapes: tuple[EpisodeTape, ...]
    canonical_shared_tables: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.schema != REHYDRATION_SCHEMA:
            raise B1MetricsRehydrateError("rehydration schema differs")
        if len(self.unique_tapes) != len(B1_SEEDS) * 448:
            raise B1MetricsRehydrateError("rehydrated B1 tape inventory is incomplete")
        if (
            "tape_transitions" not in self.canonical_shared_tables
            or "shared_tape_transitions" in self.canonical_shared_tables
        ):
            raise B1MetricsRehydrateError("transition table was not mapped exactly once")


def _json_sha256(value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise B1MetricsRehydrateError("raw metric evidence is noncanonical") from exc
    return hashlib.sha256(encoded).hexdigest()


def _require_digest(name: str, value: object, *, length: int = 64) -> str:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1MetricsRehydrateError(
            f"{name} must be {length} lowercase hexadecimal characters"
        )
    return value


def _tape_record(tape: EpisodeTape) -> dict[str, object]:
    return {
        "identity": asdict(tape.identity),
        "primitive_digest_observed": tape.primitive_digest,
        "draw_digest_observed": tape.generation_audit.draw_digest,
        "draw_count_observed": tape.generation_audit.draw_count,
    }


def _training_tape_digest(tapes: Sequence[EpisodeTape]) -> str:
    return _json_sha256(
        [
            {
                "identity": asdict(tape.identity),
                "primitive_digest": tape.primitive_digest,
            }
            for tape in tapes
        ]
    )


def _action_uniform_digest(tapes: Sequence[EpisodeTape], seed: int) -> str:
    records: list[dict[str, object]] = []
    for tape in tapes:
        for opportunity_index in range(24):
            address = addressing.action_address(
                addressing.B1_RUN,
                seed,
                tape.identity.episode_id,
                opportunity_index,
            )
            records.append(
                {
                    "episode_id": tape.identity.episode_id,
                    "opportunity_index": opportunity_index,
                    "address": list(address),
                    "u64": addressing.u64(address),
                }
            )
    return _json_sha256(records)


def _canonical_seed_panel(
    seed: int,
) -> tuple[tuple[EpisodeTape, ...], tuple[EpisodeTape, ...]]:
    host = DynamicHost(addressing.B1_RUN, seed)
    train = tuple(
        host.build_stochastic(addressing.TRAIN, episode_id)
        for episode_id in B1_TRAIN_EPISODE_IDS
    )
    evaluation = tuple(
        host.build_stochastic(addressing.EVAL_STOCHASTIC, episode_id)
        for episode_id in B1_EVAL_STOCHASTIC_IDS
    ) + tuple(host.build_motif(tape_id) for tape_id in B1_EVAL_MOTIF_IDS)
    return train, evaluation


def _validate_split_address_disjointness(
    train: Sequence[EpisodeTape], evaluation: Sequence[EpisodeTape]
) -> None:
    groups = (
        train,
        tuple(tape for tape in evaluation if tape.identity.split == addressing.EVAL_STOCHASTIC),
        tuple(tape for tape in evaluation if tape.identity.split == addressing.EVAL_MOTIF),
    )
    seen: set[object] = set()
    for group in groups:
        addresses = {
            address for tape in group for address in tape.generation_audit.draw_addresses
        }
        if seen & addresses:
            raise B1MetricsRehydrateError("canonical split address spaces overlap")
        seen.update(addresses)


def _validate_tape_records(
    value: object,
    expected: Sequence[EpisodeTape],
    *,
    label: str,
) -> None:
    if not isinstance(value, list) or len(value) != len(expected):
        raise B1MetricsRehydrateError(f"{label} tape coverage is incomplete")
    for observed, tape in zip(value, expected, strict=True):
        if (
            not isinstance(observed, Mapping)
            or frozenset(observed) != _TAPE_RECORD_FIELDS
        ):
            raise B1MetricsRehydrateError(f"{label} tape record fields differ")
        expected_record = _tape_record(tape)
        if observed != expected_record:
            raise B1MetricsRehydrateError(
                f"{label} primitive/draw identity differs from canonical host"
            )


def _expected_full_bindings(
    train: Sequence[EpisodeTape], seed: int
) -> dict[str, str]:
    return {
        "train_episode_ids_sha256": _json_sha256(list(B1_TRAIN_EPISODE_IDS)),
        "full_training_tape_digest": _training_tape_digest(train),
        "full_action_uniform_digest": _action_uniform_digest(train, seed),
        "ppo_configuration_digest": config_digest(PPOConfig()),
    }


def _validate_full_bindings(
    value: object,
    *,
    expected: Mapping[str, str],
    global_source_identity: tuple[str, str] | None,
) -> tuple[str, str]:
    if not isinstance(value, Mapping) or frozenset(value) != _FULL_BINDING_FIELDS:
        raise B1MetricsRehydrateError("full binding fields differ")
    for name, expected_digest in expected.items():
        if _require_digest(name, value[name]) != expected_digest:
            raise B1MetricsRehydrateError(f"{name} differs from canonical reconstruction")
    implementation_commit = _require_digest(
        "implementation_commit", value["implementation_commit"], length=40
    )
    source_conformance_sha256 = _require_digest(
        "source_conformance_sha256", value["source_conformance_sha256"]
    )
    identity = (implementation_commit, source_conformance_sha256)
    if global_source_identity is not None and identity != global_source_identity:
        raise B1MetricsRehydrateError("implementation/source binding drifts across raw slices")
    return identity


def _validate_group(
    group: object,
    *,
    expected_seed: int,
    expected_arm: str,
    attempt_id: str,
    train: Sequence[EpisodeTape],
    evaluation: Sequence[EpisodeTape],
    global_source_identity: tuple[str, str] | None,
) -> tuple[str, str]:
    if (
        isinstance(group, (str, bytes, bytearray, Mapping))
        or not isinstance(group, Sequence)
        or not group
    ):
        raise B1MetricsRehydrateError("each arm-seed slot requires raw slice records")
    cursor = 0
    source_identity = global_source_identity
    expected_bindings = _expected_full_bindings(train, expected_seed)
    for raw in group:
        if not isinstance(raw, Mapping) or not _REQUIRED_RAW_FIELDS <= frozenset(raw):
            raise B1MetricsRehydrateError("raw slice fields are incomplete")
        if (
            raw["schema"] != B1_RAW_EVIDENCE_SCHEMA
            or raw["attempt_id"] != attempt_id
            or raw["run_name"] != addressing.B1_RUN
            or raw["seed"] != expected_seed
            or raw["arm"] != expected_arm
        ):
            raise B1MetricsRehydrateError("raw slice slot identity differs")
        slice_record = raw["slice"]
        if not isinstance(slice_record, Mapping) or set(slice_record) != {
            "start_update",
            "stop_update",
        }:
            raise B1MetricsRehydrateError("raw slice interval fields differ")
        start = slice_record["start_update"]
        stop = slice_record["stop_update"]
        if (
            type(start) is not int
            or type(stop) is not int
            or start != cursor
            or start not in B1_CHECKPOINT_UPDATES
            or stop not in B1_CHECKPOINT_UPDATES
            or stop <= start
        ):
            raise B1MetricsRehydrateError("raw slices contain a gap, overlap, or duplicate")
        _validate_tape_records(raw["train_tapes"], train, label="training")
        _validate_tape_records(raw["evaluation_tapes"], evaluation, label="evaluation")
        source_identity = _validate_full_bindings(
            raw["full_bindings"],
            expected=expected_bindings,
            global_source_identity=source_identity,
        )
        cursor = stop
    if cursor != 48:
        raise B1MetricsRehydrateError("raw slice group does not cover updates 0 through 48")
    if source_identity is None:  # pragma: no cover - nonempty group establishes it.
        raise AssertionError("source identity was not established")
    return source_identity


def _canonicalize_shared_tables(producer: Mapping[str, Any]) -> dict[str, Any]:
    transitions = producer["shared_tape_transitions"]
    counts = dict(producer["table_counts"])
    digests = dict(producer["table_sha256"])
    transition_count = counts.pop("shared_tape_transitions")
    transition_digest = digests.pop("shared_tape_transitions")
    return {
        "schema": producer["schema"],
        "object_id": producer["object_id"],
        "literal_binding_spec_sha256": producer["literal_binding_spec_sha256"],
        "run_name": producer["run_name"],
        "attempt_id": producer["attempt_id"],
        "tape_transitions": transitions,
        "evaluator_decision_truth": producer["evaluator_decision_truth"],
        "motif_twin_index": producer["motif_twin_index"],
        "support_signature_counts": producer["support_signature_counts"],
        "motif_pair_support_counts": producer["motif_pair_support_counts"],
        "table_counts": {"tape_transitions": transition_count, **counts},
        "table_sha256": {"tape_transitions": transition_digest, **digests},
    }


def rehydrate_b1_metrics(
    raw_slice_groups: Sequence[Sequence[Mapping[str, Any]]],
    *,
    attempt_id: str,
    literal_binding_spec_sha256: str,
) -> B1MetricsRehydration:
    """Reconstruct the complete unique B1 tape inventory from fixed raw slots."""

    if type(attempt_id) is not str or not attempt_id:
        raise B1MetricsRehydrateError("attempt_id must be a nonempty string")
    _require_digest("literal_binding_spec_sha256", literal_binding_spec_sha256)
    if (
        isinstance(raw_slice_groups, (str, bytes, bytearray, Mapping))
        or not isinstance(raw_slice_groups, Sequence)
        or len(raw_slice_groups) != len(ARM_SEED_ORDER)
    ):
        raise B1MetricsRehydrateError("raw slices must contain fixed ARM_SEED_ORDER groups")

    panels = {seed: _canonical_seed_panel(seed) for seed in B1_SEEDS}
    for train, evaluation in panels.values():
        _validate_split_address_disjointness(train, evaluation)

    source_identity: tuple[str, str] | None = None
    for group, (seed, arm) in zip(raw_slice_groups, ARM_SEED_ORDER, strict=True):
        train, evaluation = panels[seed]
        source_identity = _validate_group(
            group,
            expected_seed=seed,
            expected_arm=arm,
            attempt_id=attempt_id,
            train=train,
            evaluation=evaluation,
            global_source_identity=source_identity,
        )

    unique_tapes = tuple(
        tape
        for seed in B1_SEEDS
        for tape in (*panels[seed][0], *panels[seed][1])
    )
    producer = build_b1_shared_truth_tables(
        unique_tapes,
        attempt_id=attempt_id,
        literal_binding_spec_sha256=literal_binding_spec_sha256,
    )
    return B1MetricsRehydration(
        schema=REHYDRATION_SCHEMA,
        unique_tapes=unique_tapes,
        canonical_shared_tables=_canonicalize_shared_tables(producer),
    )


__all__ = [
    "ARM_SEED_ORDER",
    "B1MetricsRehydrateError",
    "B1MetricsRehydration",
    "REHYDRATION_SCHEMA",
    "rehydrate_b1_metrics",
]

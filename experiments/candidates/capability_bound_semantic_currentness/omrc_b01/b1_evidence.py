"""Canonical parent reconstruction of raw OMRC B1 checkpoint evidence.

Only host-rebuilt tapes and worker action traces enter the evaluator.  Worker
summaries, endpoint values, and claimed validity/finiteness flags are neither
accepted nor used.
"""

from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any, Mapping, Sequence

from . import addressing
from .artifact import canonical_json_bytes, sha256_json
from .b0 import ARMS
from .b1_analysis import RAW_CHECKPOINT_SCHEMA
from .b1_contract import B1_CHECKPOINT_UPDATES, B1_RUN_NAME, B1_SEEDS
from .b1_engine import B1_RAW_EVIDENCE_SCHEMA, B1EngineError, b1_slice_counts
from .contract import Action, EPISODE_TRANSITIONS, OPPORTUNITY_COUNT
from .evaluator import evaluate_episode
from .host import DynamicHost
from .tapes import EpisodeTape


class B1EvidenceError(ValueError):
    """Parent-visible B1 raw evidence is incomplete or identity-inconsistent."""


_RAW_FIELDS = frozenset(
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
        "rollouts",
        "training_records",
        "mechanical_direct",
        "checkpoints_created",
        "evaluations",
        "final_counters",
        "final_model_parameter_digest",
        "final_optimizer_digest",
        "final_minibatch_order_digest",
        "slice_counts",
        "scientific_work_transitions",
        "stage_measurements",
        "worker_count",
        "threads_per_worker",
        "scientific_branch",
    }
)
_MECHANICAL_DIRECT_FIELDS = frozenset(
    {"active_modes", "reset_records", "checkpoint_records", "learner_visibility_records"}
)
_MECHANICAL_ROW_FIELDS = {
    "reset_records": frozenset({"name", "expected_fp32_bits", "observed_fp32_bits"}),
    "checkpoint_records": frozenset(
        {
            "name",
            "saved_sha256",
            "loaded_sha256",
            "expected_parameter_sha256",
            "restored_parameter_sha256",
        }
    ),
    "learner_visibility_records": frozenset(
        {"name", "visible_fields", "allowed_fields"}
    ),
}
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
_TAPE_FIELDS = frozenset(
    {
        "identity",
        "primitive_digest_observed",
        "draw_digest_observed",
        "draw_count_observed",
    }
)
_CHECKPOINT_FIELDS = frozenset(
    {
        "update",
        "relative_path",
        "sha256",
        "byte_count",
        "binding",
        "counters",
        "digests",
        "model_parameter_digest",
    }
)
_CHECKPOINT_BINDING_FIELDS = frozenset(
    {
        "object_id",
        "attempt_id",
        "run_name",
        "arm",
        "seed",
        "completed_rollout_updates",
        "train_episode_ids_sha256",
        "full_training_tape_digest",
        "full_action_uniform_digest",
        "ppo_configuration_digest",
        "implementation_commit",
        "source_conformance_sha256",
    }
)
_CHECKPOINT_COUNTER_FIELDS = frozenset(
    {
        "rollout_updates",
        "adam_steps",
        "train_episodes",
        "train_transitions",
        "train_decisions",
    }
)
_CHECKPOINT_DIGEST_FIELDS = frozenset(
    {
        "parameter_initialization",
        "training_tape",
        "action_uniform",
        "minibatch_order",
        "configuration",
    }
)
_EVALUATION_FIELDS = frozenset(
    {"update", "actions", "heldout_state_observations", "adapter_work_receipt"}
)
_ACTION_TRACE_FIELDS = frozenset({"identity", "decision_actions"})
_LEGAL_ACTION_NAMES = frozenset(
    {Action.SERVE.name, Action.REFRESH.name, Action.SAFE_FALLBACK.name}
)


def _require_digest(name: str, value: object, length: int = 64) -> str:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1EvidenceError(f"{name} must be {length} lowercase hexadecimal characters")
    return value


def _expected_identity(seed: int, split: str, episode_id: int) -> dict[str, Any]:
    return {
        "run_name": B1_RUN_NAME,
        "seed": seed,
        "split": split,
        "episode_id": episode_id,
    }


def _validate_tape_record(
    record: object,
    *,
    expected_identity: Mapping[str, Any],
    rebuilt: EpisodeTape | None = None,
) -> None:
    if not isinstance(record, Mapping) or frozenset(record) != _TAPE_FIELDS:
        raise B1EvidenceError("raw tape record fields differ")
    if record["identity"] != expected_identity:
        raise B1EvidenceError("raw tape identity differs")
    primitive = _require_digest("primitive digest", record["primitive_digest_observed"])
    draw = _require_digest("draw digest", record["draw_digest_observed"])
    if type(record["draw_count_observed"]) is not int or record["draw_count_observed"] < 0:
        raise B1EvidenceError("raw tape draw count differs")
    if rebuilt is not None and (
        primitive != rebuilt.primitive_digest
        or draw != rebuilt.generation_audit.draw_digest
        or record["draw_count_observed"] != rebuilt.generation_audit.draw_count
    ):
        raise B1EvidenceError("rebuilt tape primitive or draw digest differs")


def _rebuild_evaluation_tapes(
    raw_records: object, *, seed: int
) -> tuple[EpisodeTape, ...]:
    if not isinstance(raw_records, list) or len(raw_records) != 64:
        raise B1EvidenceError("evaluation tape evidence must contain exactly 64 records")
    host = DynamicHost(B1_RUN_NAME, seed)
    rebuilt = tuple(
        host.build_stochastic(addressing.EVAL_STOCHASTIC, episode_id)
        for episode_id in range(32)
    ) + tuple(host.build_motif(episode_id) for episode_id in range(32))
    observed: dict[tuple[str, int], Mapping[str, Any]] = {}
    for record in raw_records:
        if not isinstance(record, Mapping) or not isinstance(record.get("identity"), Mapping):
            raise B1EvidenceError("evaluation tape identity is absent")
        identity = record["identity"]
        key = (identity.get("split"), identity.get("episode_id"))
        if key in observed:
            raise B1EvidenceError("duplicate evaluation tape identity")
        observed[key] = record
    for tape in rebuilt:
        key = (tape.identity.split, tape.identity.episode_id)
        if key not in observed:
            raise B1EvidenceError("evaluation tape coverage is incomplete")
        _validate_tape_record(
            observed[key], expected_identity=asdict(tape.identity), rebuilt=tape
        )
    if len(observed) != len(rebuilt):
        raise B1EvidenceError("evaluation tape coverage differs")
    return rebuilt


def _validate_training_surface(raw_records: object, *, seed: int) -> None:
    if not isinstance(raw_records, list) or len(raw_records) != 384:
        raise B1EvidenceError("training tape surface must contain exactly 384 records")
    for episode_id, record in enumerate(raw_records):
        _validate_tape_record(
            record,
            expected_identity=_expected_identity(seed, addressing.TRAIN, episode_id),
        )


def _validate_full_bindings(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or frozenset(value) != _FULL_BINDING_FIELDS:
        raise B1EvidenceError("full binding fields differ")
    _require_digest("train episode IDs", value["train_episode_ids_sha256"])
    if value["train_episode_ids_sha256"] != sha256_json(list(range(384))):
        raise B1EvidenceError("train episode ID binding differs")
    for name in (
        "full_training_tape_digest",
        "full_action_uniform_digest",
        "ppo_configuration_digest",
        "source_conformance_sha256",
    ):
        _require_digest(name.replace("_", " "), value[name])
    _require_digest("implementation commit", value["implementation_commit"], 40)
    return value


def _expected_counters(update: int) -> dict[str, int]:
    return {
        "rollout_updates": update,
        "adam_steps": update * 16,
        "train_episodes": update * 8,
        "train_transitions": update * 8 * EPISODE_TRANSITIONS,
        "train_decisions": update * 8 * OPPORTUNITY_COUNT,
    }


def _validate_mechanical_passthrough(value: object) -> None:
    """Accept only exact direct row shapes; form no mechanical conclusion here."""

    if not isinstance(value, Mapping) or frozenset(value) != _MECHANICAL_DIRECT_FIELDS:
        raise B1EvidenceError("mechanical direct fields differ")
    if not isinstance(value["active_modes"], list) or any(
        type(mode) is not str or not mode for mode in value["active_modes"]
    ):
        raise B1EvidenceError("mechanical active mode schema differs")
    for name, expected_fields in _MECHANICAL_ROW_FIELDS.items():
        rows = value[name]
        if not isinstance(rows, list) or not rows:
            raise B1EvidenceError(f"mechanical {name} rows are absent")
        if any(not isinstance(row, Mapping) or frozenset(row) != expected_fields for row in rows):
            raise B1EvidenceError(f"mechanical {name} row schema differs")


def _validate_checkpoints(
    value: object,
    *,
    expected_updates: tuple[int, ...],
    raw: Mapping[str, Any],
    bindings: Mapping[str, Any],
) -> dict[int, Mapping[str, Any]]:
    if not isinstance(value, list) or len(value) != len(expected_updates):
        raise B1EvidenceError("checkpoint evidence count differs from this slice")
    indexed: dict[int, Mapping[str, Any]] = {}
    for record in value:
        if not isinstance(record, Mapping) or frozenset(record) != _CHECKPOINT_FIELDS:
            raise B1EvidenceError("checkpoint evidence fields differ")
        update = record["update"]
        if update not in expected_updates or update in indexed:
            raise B1EvidenceError("checkpoint update coverage differs")
        if record["relative_path"] != f"checkpoint-update-{update}.pt":
            raise B1EvidenceError("checkpoint relative identity differs")
        _require_digest("checkpoint identity", record["sha256"])
        _require_digest("checkpoint model", record["model_parameter_digest"])
        if type(record["byte_count"]) is not int or record["byte_count"] <= 0:
            raise B1EvidenceError("checkpoint byte count differs")
        binding = record["binding"]
        if not isinstance(binding, Mapping) or frozenset(binding) != _CHECKPOINT_BINDING_FIELDS:
            raise B1EvidenceError("checkpoint binding fields differ")
        expected_binding = {
            "object_id": "CBSC-OMRC-B01",
            "attempt_id": raw["attempt_id"],
            "run_name": B1_RUN_NAME,
            "arm": raw["arm"],
            "seed": raw["seed"],
            "completed_rollout_updates": update,
            **dict(bindings),
        }
        if dict(binding) != expected_binding:
            raise B1EvidenceError("checkpoint identity/source/full-panel binding differs")
        counters = record["counters"]
        if (
            not isinstance(counters, Mapping)
            or frozenset(counters) != _CHECKPOINT_COUNTER_FIELDS
            or dict(counters) != _expected_counters(update)
        ):
            raise B1EvidenceError("checkpoint counter identity differs")
        digests = record["digests"]
        if not isinstance(digests, Mapping) or frozenset(digests) != _CHECKPOINT_DIGEST_FIELDS:
            raise B1EvidenceError("checkpoint digest fields differ")
        for name, digest in digests.items():
            _require_digest(f"checkpoint {name}", digest)
        if (
            digests["training_tape"] != bindings["full_training_tape_digest"]
            or digests["action_uniform"] != bindings["full_action_uniform_digest"]
            or digests["configuration"] != bindings["ppo_configuration_digest"]
        ):
            raise B1EvidenceError("checkpoint full tape/action/config digest differs")
        indexed[update] = record
    return indexed


def _action_index(
    value: object, *, rebuilt: Sequence[EpisodeTape]
) -> tuple[dict[tuple[str, int], tuple[Action, ...]], int]:
    if not isinstance(value, list) or len(value) != 64:
        raise B1EvidenceError("checkpoint action traces must contain exactly 64 episodes")
    indexed: dict[tuple[str, int], tuple[Action, ...]] = {}
    valid_keys = {(tape.identity.split, tape.identity.episode_id) for tape in rebuilt}
    for trace in value:
        if not isinstance(trace, Mapping) or frozenset(trace) != _ACTION_TRACE_FIELDS:
            raise B1EvidenceError("checkpoint action trace fields differ")
        identity = trace["identity"]
        if not isinstance(identity, Mapping):
            raise B1EvidenceError("checkpoint action identity is absent")
        key = (identity.get("split"), identity.get("episode_id"))
        if key not in valid_keys or key in indexed:
            raise B1EvidenceError("checkpoint action identity is duplicate or differs")
        tape = next(
            item
            for item in rebuilt
            if (item.identity.split, item.identity.episode_id) == key
        )
        if identity != asdict(tape.identity):
            raise B1EvidenceError("checkpoint action identity differs")
        names = trace["decision_actions"]
        if not isinstance(names, list):
            raise B1EvidenceError("invalid action masking in checkpoint trace")
        invalid_masking_count = abs(len(names) - OPPORTUNITY_COUNT) + sum(
            type(name) is not str or name not in _LEGAL_ACTION_NAMES for name in names
        )
        if invalid_masking_count:
            raise B1EvidenceError(
                f"invalid action masking census is nonzero: {invalid_masking_count}"
            )
        indexed[key] = tuple(Action[name] for name in names)
    return indexed, 0


def _numerical_finite(value: object) -> bool:
    """Recursively census only reconstructed JSON numerical leaves."""

    if value is None or isinstance(value, (str, bool)):
        return True
    if type(value) is int:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_numerical_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_numerical_finite(item) for item in value)
    return False


def reconstruct_checkpoint_records(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Rebuild and evaluate every newly created checkpoint in one B1 raw slice."""

    if not isinstance(raw, Mapping) or frozenset(raw) != _RAW_FIELDS:
        raise B1EvidenceError("arm-seed raw evidence fields differ")
    try:
        canonical_json_bytes(raw)
    except Exception as exc:
        raise B1EvidenceError("arm-seed raw evidence is nonfinite or noncanonical") from exc
    if (
        raw["schema"] != B1_RAW_EVIDENCE_SCHEMA
        or raw["run_name"] != B1_RUN_NAME
        or raw["arm"] not in ARMS
        or raw["seed"] not in B1_SEEDS
        or type(raw["attempt_id"]) is not str
        or not raw["attempt_id"]
        or raw["scientific_branch"] is not None
    ):
        raise B1EvidenceError("arm-seed raw evidence identity differs")
    if raw["worker_count"] != 1 or raw["threads_per_worker"] != 1:
        raise B1EvidenceError("arm-seed worker topology differs")
    if not isinstance(raw["training_records"], Mapping):
        raise B1EvidenceError("training records passthrough is absent")
    _validate_mechanical_passthrough(raw["mechanical_direct"])
    slice_record = raw["slice"]
    if not isinstance(slice_record, Mapping) or set(slice_record) != {
        "start_update",
        "stop_update",
    }:
        raise B1EvidenceError("slice identity fields differ")
    start = slice_record["start_update"]
    stop = slice_record["stop_update"]
    if type(start) is not int or type(stop) is not int:
        raise B1EvidenceError("slice update identity differs")

    checkpoints_value = raw["checkpoints_created"]
    if not isinstance(checkpoints_value, list):
        raise B1EvidenceError("checkpoint evidence is not a list")
    observed_updates = tuple(record.get("update") for record in checkpoints_value if isinstance(record, Mapping))
    fresh = 0 in observed_updates
    try:
        counts = b1_slice_counts(start, stop, fresh=fresh)
    except B1EngineError as exc:
        raise B1EvidenceError("slice work interval differs") from exc
    if raw["slice_counts"] != asdict(counts) or raw["scientific_work_transitions"] != counts.scientific_work_transitions:
        raise B1EvidenceError("slice work counts differ")
    expected_updates = tuple(
        ([0] if fresh else [])
        + [update for update in B1_CHECKPOINT_UPDATES if start < update <= stop]
    )
    if tuple(sorted(observed_updates)) != expected_updates:
        raise B1EvidenceError("checkpoint slice coverage differs")
    if not isinstance(raw["rollouts"], list) or len(raw["rollouts"]) != counts.rollout_updates:
        raise B1EvidenceError("rollout evidence count differs")
    if raw["final_counters"] != _expected_counters(stop):
        raise B1EvidenceError("final recurrent-PPO counters differ")
    for name in (
        "final_model_parameter_digest",
        "final_optimizer_digest",
        "final_minibatch_order_digest",
    ):
        _require_digest(name.replace("_", " "), raw[name])

    bindings = _validate_full_bindings(raw["full_bindings"])
    _validate_training_surface(raw["train_tapes"], seed=raw["seed"])
    rebuilt = _rebuild_evaluation_tapes(raw["evaluation_tapes"], seed=raw["seed"])
    checkpoints = _validate_checkpoints(
        checkpoints_value,
        expected_updates=expected_updates,
        raw=raw,
        bindings=bindings,
    )
    evaluations = raw["evaluations"]
    if not isinstance(evaluations, list) or len(evaluations) != len(expected_updates):
        raise B1EvidenceError("evaluation evidence count differs")
    indexed_evaluations: dict[int, Mapping[str, Any]] = {}
    for evaluation in evaluations:
        if not isinstance(evaluation, Mapping) or frozenset(evaluation) != _EVALUATION_FIELDS:
            raise B1EvidenceError("evaluation evidence fields differ")
        update = evaluation["update"]
        if update not in expected_updates or update in indexed_evaluations:
            raise B1EvidenceError("evaluation checkpoint coverage differs")
        indexed_evaluations[update] = evaluation

    output: list[dict[str, Any]] = []
    for update in expected_updates:
        actions, invalid_masking_count = _action_index(
            indexed_evaluations[update]["actions"], rebuilt=rebuilt
        )
        episodes = [
            evaluate_episode(
                tape,
                actions[(tape.identity.split, tape.identity.episode_id)],
            )
            for tape in rebuilt
        ]
        numerical_finite = _numerical_finite(episodes)
        if not numerical_finite:
            raise B1EvidenceError("parent-reconstructed checkpoint is nonfinite")
        if invalid_masking_count != 0:
            raise B1EvidenceError("parent-reconstructed invalid masking census is nonzero")
        try:
            canonical_json_bytes(episodes)
        except Exception as exc:
            raise B1EvidenceError("parent-reconstructed checkpoint is nonfinite") from exc
        output.append(
            {
                "schema": RAW_CHECKPOINT_SCHEMA,
                "run_name": B1_RUN_NAME,
                "arm": raw["arm"],
                "seed": raw["seed"],
                "checkpoint_update": update,
                "checkpoint_identity": (
                    f"{raw['arm']}-{raw['seed']}-update-{update}"
                ),
                "numerical_finite": numerical_finite,
                "invalid_masking_count": invalid_masking_count,
                "episodes": episodes,
            }
        )
    return output


def collect_complete_b1_checkpoint_records(
    raw_slices: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Collect exact unique 12 arm-seeds by four checkpoints in canonical order."""

    if not isinstance(raw_slices, Sequence) or isinstance(raw_slices, (str, bytes, bytearray)):
        raise B1EvidenceError("B1 raw slices must be a sequence")
    indexed: dict[tuple[str, int, int], dict[str, Any]] = {}
    for raw in raw_slices:
        for record in reconstruct_checkpoint_records(raw):
            key = (record["arm"], record["seed"], record["checkpoint_update"])
            if key in indexed:
                raise B1EvidenceError("duplicate parent-reconstructed checkpoint coverage")
            indexed[key] = record
    expected = [
        (arm, seed, update)
        for arm in ARMS
        for seed in B1_SEEDS
        for update in B1_CHECKPOINT_UPDATES
    ]
    if len(indexed) != 48 or set(indexed) != set(expected):
        raise B1EvidenceError("B1 parent evidence requires complete 48 checkpoint coverage")
    return [indexed[key] for key in expected]


__all__ = [
    "B1EvidenceError",
    "collect_complete_b1_checkpoint_records",
    "reconstruct_checkpoint_records",
]

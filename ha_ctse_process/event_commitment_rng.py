"""Authoritative event-held commitment RNG construction and binding."""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from typing import Any, Literal, Mapping

import numpy as np

from ha_ctse_process.event_commitment_types import (
    ArmName,
    EventTrajectory,
    TrainingState,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    EVENT_SEED,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    MARK_SEED,
    OPPORTUNITY_SEED,
    RNG_BINDING_SCHEMA_VERSION,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    make_rng,
)

OPPORTUNITY_SUPPORT = np.asarray((4, 8, 12), dtype=np.int64)
RNG_NAMES = ("ledger", "order", "primitive", "opportunity", "event", "mark")

_RNG_BINDING_KEYS = frozenset({
    "schema_version", "context", "stream", "seed", "start_state",
    "draw_schedule", "draw_bytes_digest", "end_state", "binding_digest",
})
_RNG_SCHEDULE_KEYS = frozenset({
    "stream", "operation", "dtype", "shape", "coordinates"
})


def _seed(base: int, replicate: int) -> int:
    return int(base + 1000 * replicate)


def authoritative_seed_map(
    profile: Literal["train", "iid", "held_out"], replicate: int
) -> dict[str, int]:
    ledger_base = TRAIN_TASK_SEED if profile == "train" else (
        IID_EVAL_TASK_SEED if profile == "iid" else HELD_OUT_EVAL_TASK_SEED
    )
    return {
        "ledger": _seed(ledger_base, replicate),
        "order": _seed(TRAIN_ORDER_SEED, replicate),
        "primitive": _seed(TRAIN_ACTION_SEED, replicate),
        "opportunity": _seed(OPPORTUNITY_SEED, replicate),
        "event": _seed(EVENT_SEED, replicate),
        "mark": _seed(MARK_SEED, replicate),
    }


def make_training_state(
    arm: ArmName,
    replicate: int,
    *,
    profile: Literal["train", "iid", "held_out"] = "train",
) -> TrainingState:
    seed_map = authoritative_seed_map(profile, replicate)
    return TrainingState(
        arm=arm,
        replicate=int(replicate),
        profile=profile,
        seed_map=seed_map,
        rngs={name: np.random.default_rng(seed_map[name]) for name in RNG_NAMES},
    )


def _canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _float32_payload(value: np.ndarray) -> dict[str, Any]:
    """Canonical exact binary32 payload without any outcome information."""

    array = np.ascontiguousarray(value, dtype=np.float32)
    encoded = array.tobytes(order="C")
    return {
        "dtype": "float32",
        "shape": [int(size) for size in array.shape],
        "values": array.tolist(),
        "bytes_b64": base64.b64encode(encoded).decode("ascii"),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _raw_event_trace_digest(row_without_digest: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        row_without_digest, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(b"HMASD_RAW_EVENT_TRACE_V1\0" + encoded).hexdigest()


def owned_rng_states(state: TrainingState) -> dict[str, Any]:
    """Return canonical, independently cloneable owned-generator states."""

    return {
        name: deepcopy(state.rngs[name].bit_generator.state)
        for name in RNG_NAMES
    }


def collection_rng_schedules(
    trajectory: EventTrajectory, *, deterministic: bool
) -> dict[str, list[dict[str, Any]]]:
    """Reconstruct the collector's exact per-stream draw calls.

    Values are deliberately absent. A validator replays these calls from the
    canonical start state and regenerates the bytes and end state itself.
    """

    schedules = deepcopy(trajectory.rng_audit["streams"])
    if set(schedules) != set(RNG_NAMES):
        raise RuntimeError("collector RNG audit stream set mismatch")
    return schedules


def _replay_rng_schedule(
    start_state: Mapping[str, Any], schedule: list[dict[str, Any]],
    *, seed: int | None = None,
) -> tuple[str, dict[str, Any], list[np.ndarray]]:
    generator = np.random.default_rng()
    generator.bit_generator.state = deepcopy(dict(start_state))
    digest = hashlib.sha256()
    arrays: list[np.ndarray] = []
    seeded_generators: dict[tuple[Any, ...], np.random.Generator] = {}
    for entry in schedule:
        if not isinstance(entry, dict) or set(entry) != _RNG_SCHEDULE_KEYS:
            raise ValueError("RNG draw schedule schema mismatch")
        shape = tuple(int(value) for value in entry["shape"])
        if any(value < 0 for value in shape):
            raise ValueError("RNG draw schedule has a negative shape")
        dtype = np.dtype(str(entry["dtype"]))
        operation = str(entry["operation"])
        if operation.startswith("seeded_"):
            if seed is None:
                raise ValueError("seeded RNG audit operation lacks authoritative seed")
            coordinates = entry["coordinates"]
            identity = (
                int(coordinates["episode_id"]), int(coordinates["attempt"]),
                *tuple(int(value) for value in coordinates["generator_coordinates"]),
            )
            local = seeded_generators.get(identity)
            if local is None:
                local = make_rng(
                    int(seed), *tuple(
                        int(value) for value in coordinates["generator_coordinates"]
                    )
                )
                seeded_generators[identity] = local
            argument = coordinates.get("argument")
            if operation == "seeded_permutation":
                drawn = local.permutation(
                    int(argument) if isinstance(argument, int)
                    else np.asarray(argument, dtype=dtype)
                )
            elif operation == "seeded_permutation_blocks":
                expected_shape = (
                    len(coordinates["key_order"]),
                    len(coordinates["offset_order"]),
                    len(argument),
                )
                if shape != expected_shape:
                    raise ValueError("duration permutation block shape mismatch")
                drawn = np.empty(shape, dtype=dtype)
                values = np.asarray(argument, dtype=dtype)
                for key_index, _key in enumerate(coordinates["key_order"]):
                    for offset_index, _offset in enumerate(
                        coordinates["offset_order"]
                    ):
                        drawn[key_index, offset_index] = local.permutation(values)
            elif operation == "seeded_choice":
                drawn = local.choice(
                    np.asarray(argument, dtype=dtype),
                    size=shape if shape else None,
                    replace=bool(coordinates["replace"]),
                )
            elif operation == "seeded_random":
                drawn = local.random(shape, dtype=dtype)
            else:
                raise ValueError("unknown seeded RNG audit operation")
        elif operation == "random":
            drawn = generator.random(shape, dtype=dtype)
        elif operation == "standard_normal" and dtype == np.dtype(np.float64):
            drawn = generator.standard_normal(shape)
        elif operation == "choice_opportunity" and dtype == np.dtype(np.int64):
            drawn = generator.choice(OPPORTUNITY_SUPPORT, size=shape)
        else:
            raise ValueError("RNG draw schedule operation/dtype mismatch")
        array = np.asarray(drawn, dtype=dtype).reshape(shape)
        digest.update(array.tobytes(order="C"))
        arrays.append(array.copy())
    return digest.hexdigest(), deepcopy(generator.bit_generator.state), arrays


def replay_rng_schedule_end_state(
    start_state: Mapping[str, Any], schedule: list[dict[str, Any]],
    *, seed: int | None = None,
) -> dict[str, Any]:
    """Public state-only replay used to validate a Stage-2 fork coordinate."""

    return _replay_rng_schedule(start_state, schedule, seed=seed)[1]


def replay_rng_schedule_arrays(
    start_state: Mapping[str, Any], schedule: list[dict[str, Any]],
    *, seed: int | None = None,
) -> tuple[list[np.ndarray], dict[str, Any]]:
    """Replay and expose generated arrays for strict Stage-2 consumption audit."""

    _digest, end_state, arrays = _replay_rng_schedule(
        start_state, schedule, seed=seed
    )
    return arrays, end_state


def make_rng_binding(
    *, context: Mapping[str, Any], stream: str, seed: int,
    start_state: Mapping[str, Any], draw_schedule: list[dict[str, Any]],
    expected_end_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a context-bound record only after independent schedule replay."""

    if stream not in RNG_NAMES:
        raise ValueError("unknown owned RNG stream")
    if any(entry.get("stream") != stream for entry in draw_schedule):
        raise ValueError("RNG draw schedule stream label mismatch")
    draw_digest, end_state, _arrays = _replay_rng_schedule(
        start_state, draw_schedule, seed=seed
    )
    if end_state != dict(expected_end_state):
        raise RuntimeError(f"RNG schedule does not reach supplied {stream} end state")
    record: dict[str, Any] = {
        "schema_version": RNG_BINDING_SCHEMA_VERSION,
        "context": deepcopy(dict(context)),
        "stream": stream,
        "seed": int(seed),
        "start_state": deepcopy(dict(start_state)),
        "draw_schedule": deepcopy(draw_schedule),
        "draw_bytes_digest": draw_digest,
        "end_state": end_state,
    }
    record["binding_digest"] = _canonical_json_digest(record)
    return record


def validate_rng_binding(
    record: Any, *, expected_context: Mapping[str, Any], expected_stream: str,
    expected_seed: int, expected_start_state: Mapping[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    """Regenerate draws and state; supplied digests are never trusted."""

    try:
        if not isinstance(record, dict) or set(record) != _RNG_BINDING_KEYS:
            return False, None
        if not (
            int(record["schema_version"]) == RNG_BINDING_SCHEMA_VERSION
            and record["context"] == dict(expected_context)
            and record["stream"] == expected_stream
            and int(record["seed"]) == int(expected_seed)
            and record["start_state"] == dict(expected_start_state)
            and all(
                entry.get("stream") == expected_stream
                for entry in record["draw_schedule"]
            )
        ):
            return False, None
        draw_digest, end_state, _arrays = _replay_rng_schedule(
            record["start_state"], record["draw_schedule"],
            seed=int(expected_seed),
        )
        payload = {
            key: deepcopy(value)
            for key, value in record.items()
            if key != "binding_digest"
        }
        if not (
            draw_digest == record["draw_bytes_digest"]
            and end_state == record["end_state"]
            and _canonical_json_digest(payload) == record["binding_digest"]
        ):
            return False, None
        return True, end_state
    except (KeyError, TypeError, ValueError, OverflowError):
        return False, None

"""RNG evidence construction and validation for event-held commitment."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Mapping

import numpy as np
import torch

from ha_ctse_process import event_commitment_evidence_common
from ha_ctse_process.event_commitment_collector import CREATE, KEEP
from ha_ctse_process.event_commitment_rng import (
    RNG_NAMES,
    collection_rng_schedules,
    make_rng_binding,
    validate_rng_binding,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    HORIZON,
    MAX_LIFECYCLES,
    make_noncalendar_ledger,
)


def _tensor_digest(value: torch.Tensor) -> str:
    tensor = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(tensor.dtype).encode("ascii"))
    digest.update(np.asarray(tensor.shape, dtype=np.int64).tobytes())
    digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _owned_stream_digests(state: Any) -> dict[str, str]:
    return {
        name: event_commitment_evidence_common._digest_json(
            state.rngs[name].bit_generator.state
        )
        for name in RNG_NAMES
    }


def _initial_rng_states(seed_map: Mapping[str, int]) -> dict[str, Any]:
    return {
        name: deepcopy(np.random.default_rng(int(seed_map[name])).bit_generator.state)
        for name in RNG_NAMES
    }


def _collection_rng_bindings(
    *, context: Mapping[str, Any], seed_map: Mapping[str, int],
    start_states: Mapping[str, Any], end_states: Mapping[str, Any],
    trajectory: Any, deterministic: bool,
) -> dict[str, dict[str, Any]]:
    schedules = collection_rng_schedules(
        trajectory, deterministic=deterministic
    )
    return {
        name: make_rng_binding(
            context=context,
            stream=name,
            seed=int(seed_map[name]),
            start_state=start_states[name],
            draw_schedule=schedules[name],
            expected_end_state=end_states[name],
        )
        for name in RNG_NAMES
    }


def _rng_bindings_valid(
    bindings: Any, *, expected_context: Mapping[str, Any],
    seed_map: Mapping[str, int], expected_starts: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    if not isinstance(bindings, dict) or set(bindings) != set(RNG_NAMES):
        return False, {}
    end_states: dict[str, Any] = {}
    integer_context_fields = {
        "replicate", "update", "batch", "episode_id", "time", "key",
        "membership_epoch", "segment_id",
    }
    for name in RNG_NAMES:
        binding = bindings[name]
        context = binding.get("context") if isinstance(binding, dict) else None
        if not isinstance(context, dict) or any(
            field in context and not event_commitment_evidence_common._is_exact_int(context[field])
            for field in integer_context_fields
        ):
            return False, {}
        valid, end_state = validate_rng_binding(
            binding,
            expected_context=expected_context,
            expected_stream=name,
            expected_seed=int(seed_map[name]),
            expected_start_state=expected_starts[name],
        )
        if not valid or end_state is None:
            return False, {}
        end_states[name] = end_state
    return True, end_states


def _collection_binding_schedules_valid(
    bindings: Mapping[str, Any], *, deterministic: bool,
    lifecycle_counts: Mapping[str, Any], environment_count: int,
) -> bool:
    try:
        schedules = {
            name: bindings[name]["draw_schedule"] for name in RNG_NAMES
        }
        if not schedules["ledger"] or not schedules["order"]:
            return False
        opportunity_total = sum(
            int(entry["shape"][0]) for entry in schedules["opportunity"]
        )
        expected_requests = sum(
            int(lifecycle_counts[name]) for name in ("create", "keep", "renew")
        )
        if opportunity_total != expected_requests:
            return False
        if deterministic:
            return not (
                schedules["event"] or schedules["mark"]
                or schedules["primitive"]
            )
        event_total = sum(int(entry["shape"][0]) for entry in schedules["event"])
        mark_total = sum(int(entry["shape"][0]) for entry in schedules["mark"])
        primitive = schedules["primitive"]
        if not (
            event_total == mark_total == opportunity_total
            and len(primitive) == HORIZON
            and all(
                entry["shape"] == [environment_count, MAX_LIFECYCLES]
                and entry["operation"] == "random"
                and entry["dtype"] == "float32"
                and event_commitment_evidence_common._is_exact_int(entry["coordinates"]["time"])
                and entry["coordinates"]["time"] == index
                for index, entry in enumerate(primitive)
            )
            and [entry["coordinates"] for entry in schedules["event"]]
            == [entry["coordinates"] for entry in schedules["mark"]]
            == [entry["coordinates"] for entry in schedules["opportunity"]]
        ):
            return False
        for stream, operation, dtype in (
            ("event", "random", "float64"),
            ("mark", "standard_normal", "float64"),
            ("opportunity", "choice_opportunity", "int64"),
        ):
            times = [
                entry["coordinates"]["time"]
                for entry in schedules[stream]
            ]
            if not (
                all(event_commitment_evidence_common._is_exact_int(value) for value in times)
                and times == sorted(times)
                and len(times) == len(set(times))
                and all(0 <= value < HORIZON for value in times)
                and all(
                    entry["operation"] == operation and entry["dtype"] == dtype
                    for entry in schedules[stream]
                )
            ):
                return False
        return True
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def _ledger_record(ledger: Any) -> dict[str, Any]:
    payload = {
        "episode_id": int(ledger.episode_id), "base_id": int(ledger.base_id),
        "sign_parity": int(ledger.sign_parity), "profile": ledger.profile,
        "generation_attempt": int(ledger.generation_attempt),
        "routing_permutation": list(ledger.routing_permutation),
        "initial_count": int(ledger.initial_count),
        "temporary_key": int(ledger.temporary_key),
        "terminal_key": int(ledger.terminal_key),
        "duration_streams": ledger.duration_streams.tolist(),
        "initial_targets": ledger.initial_targets.tolist(),
        "direct_frontier_priorities": ledger.direct_frontier_priorities.tolist(),
    }
    return payload | {
        "ledger_digest": event_commitment_evidence_common._digest_json(payload)
    }


def _rng_audit_evidence_valid(
    evidence: Any, bindings: Mapping[str, Any], *, arm: str, profile: str,
    seed_map: Mapping[str, int], deterministic: bool,
    episode_ids: list[int],
    ledger_cache: dict[tuple[Any, ...], tuple[dict[str, Any], list[Any]]] | None = None,
) -> bool:
    try:
        if not isinstance(evidence, dict) or set(evidence) != {
            "streams", "request_evidence", "ledgers"
        }:
            return False
        streams = evidence["streams"]
        if set(streams) != set(RNG_NAMES) or any(
            streams[name] != bindings[name]["draw_schedule"] for name in RNG_NAMES
        ):
            return False
        cache_key = (
            profile, int(seed_map["ledger"]), int(seed_map["order"]),
            tuple(int(value) for value in episode_ids),
        )
        cached = ledger_cache.get(cache_key) if ledger_cache is not None else None
        if cached is None:
            regenerated_trace = {name: [] for name in RNG_NAMES}
            regenerated_ledgers = [
                make_noncalendar_ledger(
                    episode_id, profile=profile,
                    task_seed=int(seed_map["ledger"]),
                    order_seed=int(seed_map["order"]),
                    audit_trace=regenerated_trace,
                )
                for episode_id in episode_ids
            ]
            if ledger_cache is not None:
                ledger_cache[cache_key] = (regenerated_trace, regenerated_ledgers)
        else:
            regenerated_trace, regenerated_ledgers = cached
        if evidence["ledgers"] != [
            _ledger_record(ledger) for ledger in regenerated_ledgers
        ]:
            return False
        if streams["ledger"] != regenerated_trace["ledger"] or streams["order"] != regenerated_trace["order"]:
            return False
        requests_by_time: dict[int, list[list[int]]] = {}
        frontier_by_time: dict[int, list[list[int]]] = {}
        rows = evidence["request_evidence"]
        if len(rows) != HORIZON:
            return False
        for expected_time, row in enumerate(rows):
            if set(row) != {"time", "environments"} or not (
                event_commitment_evidence_common._is_exact_int(row["time"])
                and row["time"] == expected_time
            ):
                return False
            environments = row["environments"]
            if len(environments) != len(episode_ids):
                return False
            expected_requests: list[list[int]] = []
            frontier_orders: list[list[int]] = []
            for env_index, env in enumerate(environments):
                if set(env) != {"env_index", "episode_id", "frontier"} or not (
                    event_commitment_evidence_common._is_exact_int(env["env_index"])
                    and event_commitment_evidence_common._is_exact_int(env["episode_id"])
                    and env["env_index"] == env_index
                    and env["episode_id"] == episode_ids[env_index]
                ):
                    return False
                frontier = env["frontier"]
                if any(set(value) != {"key", "priority", "q_before"} for value in frontier):
                    return False
                if any(
                    not event_commitment_evidence_common._is_exact_int(value["key"])
                    for value in frontier
                ):
                    return False
                keys = [value["key"] for value in frontier]
                if len(keys) != len(set(keys)) or keys != [
                    value["key"] for value in sorted(
                        frontier, key=lambda value: float(value["priority"])
                    )
                ]:
                    return False
                ledger = regenerated_ledgers[env_index]
                if any(
                    float(value["priority"])
                    != float(ledger.direct_frontier_priorities[expected_time, value["key"]])
                    for value in frontier
                ):
                    return False
                frontier_orders.append(keys)
                if arm == "OR":
                    if any(value["q_before"] is not None for value in frontier):
                        return False
                else:
                    for value in frontier:
                        q = int(value["q_before"])
                        if q <= 0:
                            expected_requests.append([
                                env_index, int(value["key"]), CREATE if q < 0 else KEEP
                            ])
            requests_by_time[expected_time] = expected_requests
            frontier_by_time[expected_time] = frontier_orders
        for stream in ("event", "mark", "opportunity"):
            if any(
                not event_commitment_evidence_common._is_exact_int(
                    entry["coordinates"]["time"]
                )
                for entry in streams[stream]
            ):
                return False
            actual = {
                entry["coordinates"]["time"]: entry["coordinates"]["requests"]
                for entry in streams[stream]
            }
            expected = {
                time: requests for time, requests in requests_by_time.items()
                if requests
            }
            if stream in ("event", "mark") and deterministic:
                expected = {}
            if actual != expected:
                return False
        primitive_expected = {} if deterministic else {
            time: {
                "time": time, "episode_ids": episode_ids,
                "frontier_orders": frontier_by_time[time],
            }
            for time in range(HORIZON)
        }
        if any(
            not event_commitment_evidence_common._is_exact_int(
                entry["coordinates"]["time"]
            )
            for entry in streams["primitive"]
        ):
            return False
        primitive_actual = {
            entry["coordinates"]["time"]: entry["coordinates"]
            for entry in streams["primitive"]
        }
        return primitive_actual == primitive_expected
    except (KeyError, TypeError, ValueError, OverflowError):
        return False

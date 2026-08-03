from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import torch

from ha_ctse_process import event_commitment_rng_evidence
from ha_ctse_process.event_commitment_rng import (
    RNG_NAMES,
    authoritative_seed_map,
    make_rng_binding,
    make_training_state,
    replay_rng_schedule_end_state,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    HORIZON,
    MAX_LIFECYCLES,
    make_noncalendar_ledger,
)


HELPERS = {
    "_tensor_digest",
    "_owned_stream_digests",
    "_initial_rng_states",
    "_collection_rng_bindings",
    "_rng_bindings_valid",
    "_collection_binding_schedules_valid",
    "_ledger_record",
    "_rng_audit_evidence_valid",
}


def _entry(
    stream: str, operation: str, dtype: str, shape: list[int], coordinates: dict,
) -> dict:
    return {
        "stream": stream,
        "operation": operation,
        "dtype": dtype,
        "shape": shape,
        "coordinates": coordinates,
    }


def _bindings(
    schedules: dict[str, list[dict]], seed_map: dict[str, int], context: dict,
) -> tuple[dict[str, dict], dict[str, dict]]:
    starts = event_commitment_rng_evidence._initial_rng_states(seed_map)
    bindings = {
        name: make_rng_binding(
            context=context,
            stream=name,
            seed=seed_map[name],
            start_state=starts[name],
            draw_schedule=schedules[name],
            expected_end_state=replay_rng_schedule_end_state(
                starts[name], schedules[name], seed=seed_map[name]
            ),
        )
        for name in RNG_NAMES
    }
    return bindings, starts


def test_rng_evidence_helpers_have_one_true_owner() -> None:
    root = Path(__file__).resolve().parents[1]
    owner_tree = ast.parse(
        (root / "ha_ctse_process" / "event_commitment_rng_evidence.py").read_text(
            encoding="utf-8"
        )
    )
    runner_tree = ast.parse(
        (root / "scripts" / "run_noncalendar_commitment_benchmark_g0.py").read_text(
            encoding="utf-8"
        )
    )
    owner_definitions = {
        node.name for node in owner_tree.body if isinstance(node, ast.FunctionDef)
    }
    runner_definitions = {
        node.name for node in runner_tree.body if isinstance(node, ast.FunctionDef)
    }

    assert HELPERS <= owner_definitions
    assert HELPERS.isdisjoint(runner_definitions)
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ha_ctse_process"
        and any(alias.name == "event_commitment_rng_evidence" for alias in node.names)
        for node in runner_tree.body
    )


def test_tensor_and_owned_rng_digests_preserve_exact_bytes() -> None:
    tensor = torch.tensor([[1.0, -2.5]], dtype=torch.float32).t()
    contiguous = tensor.detach().cpu().contiguous()
    expected = hashlib.sha256(
        str(contiguous.dtype).encode("ascii")
        + np.asarray(contiguous.shape, dtype=np.int64).tobytes()
        + contiguous.numpy().tobytes()
    ).hexdigest()
    state = make_training_state("OR", 0)

    assert event_commitment_rng_evidence._tensor_digest(tensor) == expected
    assert set(event_commitment_rng_evidence._owned_stream_digests(state)) == set(RNG_NAMES)


def test_binding_schedule_validation_rejects_tampering() -> None:
    seed_map = authoritative_seed_map("iid", 0)
    context = {"replicate": 0, "update": 1}
    schedules = {name: [] for name in RNG_NAMES}
    schedules["ledger"] = [_entry("ledger", "random", "float64", [1], {})]
    schedules["order"] = [_entry("order", "random", "float64", [1], {})]
    schedules["opportunity"] = [
        _entry("opportunity", "choice_opportunity", "int64", [2], {"time": 0})
    ]
    bindings, starts = _bindings(schedules, seed_map, context)

    valid, _ends = event_commitment_rng_evidence._rng_bindings_valid(
        bindings,
        expected_context=context,
        seed_map=seed_map,
        expected_starts=starts,
    )
    assert valid
    assert event_commitment_rng_evidence._collection_binding_schedules_valid(
        bindings,
        deterministic=True,
        lifecycle_counts={"create": 1, "keep": 1, "renew": 0},
        environment_count=1,
    )

    tampered = deepcopy(bindings)
    tampered["opportunity"]["draw_schedule"][0]["shape"] = [3]
    valid, _ends = event_commitment_rng_evidence._rng_bindings_valid(
        tampered,
        expected_context=context,
        seed_map=seed_map,
        expected_starts=starts,
    )
    assert not valid
    assert not event_commitment_rng_evidence._collection_binding_schedules_valid(
        tampered,
        deterministic=True,
        lifecycle_counts={"create": 1, "keep": 1, "renew": 0},
        environment_count=1,
    )


def test_stochastic_schedule_and_audit_validation_reject_tampering() -> None:
    seed_map = authoritative_seed_map("iid", 0)
    context = {"replicate": 0, "update": 1}
    request_coordinates = {"time": 0, "requests": [[0, 1, 0]]}
    schedules = {name: [] for name in RNG_NAMES}
    schedules["ledger"] = [_entry("ledger", "random", "float64", [1], {})]
    schedules["order"] = [_entry("order", "random", "float64", [1], {})]
    schedules["event"] = [_entry("event", "random", "float64", [1], request_coordinates)]
    schedules["mark"] = [_entry("mark", "standard_normal", "float64", [1], request_coordinates)]
    schedules["opportunity"] = [
        _entry("opportunity", "choice_opportunity", "int64", [1], request_coordinates)
    ]
    schedules["primitive"] = [
        _entry(
            "primitive", "random", "float32", [1, MAX_LIFECYCLES], {"time": time}
        )
        for time in range(HORIZON)
    ]
    bindings, _starts = _bindings(schedules, seed_map, context)
    assert event_commitment_rng_evidence._collection_binding_schedules_valid(
        bindings,
        deterministic=False,
        lifecycle_counts={"create": 1, "keep": 0, "renew": 0},
        environment_count=1,
    )

    episode_ids = [3]
    ledger_trace = {name: [] for name in RNG_NAMES}
    ledgers = [
        make_noncalendar_ledger(
            episode_id,
            profile="iid",
            task_seed=seed_map["ledger"],
            order_seed=seed_map["order"],
            audit_trace=ledger_trace,
        )
        for episode_id in episode_ids
    ]
    audit_streams = {name: [] for name in RNG_NAMES}
    audit_streams["ledger"] = ledger_trace["ledger"]
    audit_streams["order"] = ledger_trace["order"]
    audit_streams["primitive"] = [
        _entry(
            "primitive",
            "random",
            "float32",
            [1, MAX_LIFECYCLES],
            {"time": time, "episode_ids": episode_ids, "frontier_orders": [[]]},
        )
        for time in range(HORIZON)
    ]
    audit_bindings = {
        name: {"draw_schedule": audit_streams[name]} for name in RNG_NAMES
    }
    evidence = {
        "streams": audit_streams,
        "request_evidence": [
            {
                "time": time,
                "environments": [
                    {"env_index": 0, "episode_id": episode_ids[0], "frontier": []}
                ],
            }
            for time in range(HORIZON)
        ],
        "ledgers": [event_commitment_rng_evidence._ledger_record(ledger) for ledger in ledgers],
    }

    deterministic_evidence = deepcopy(evidence)
    deterministic_evidence["streams"]["primitive"] = []
    deterministic_bindings = {
        name: {"draw_schedule": deterministic_evidence["streams"][name]}
        for name in RNG_NAMES
    }
    assert event_commitment_rng_evidence._rng_audit_evidence_valid(
        deterministic_evidence,
        deterministic_bindings,
        arm="OR",
        profile="iid",
        seed_map=seed_map,
        deterministic=True,
        episode_ids=episode_ids,
    )
    assert event_commitment_rng_evidence._rng_audit_evidence_valid(
        evidence,
        audit_bindings,
        arm="OR",
        profile="iid",
        seed_map=seed_map,
        deterministic=False,
        episode_ids=episode_ids,
    )
    tampered = deepcopy(evidence)
    tampered["request_evidence"][0]["time"] = True
    assert not event_commitment_rng_evidence._rng_audit_evidence_valid(
        tampered,
        audit_bindings,
        arm="OR",
        profile="iid",
        seed_map=seed_map,
        deterministic=False,
        episode_ids=episode_ids,
    )

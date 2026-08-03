from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

from ha_ctse_process import event_commitment_audit
from ha_ctse_process.dynamic_roster_testbed import MAX_LIFECYCLES
from ha_ctse_process.event_commitment_audit import (
    AUDIT_STREAM_NAMES,
    _AUDIT_CONTINUOUS_FIELDS,
    _AUDIT_DISCRETE_FIELDS,
    _clone_audit_cursor,
    _nested_equal,
    _rng_states,
    _audit_cursor,
    _audit_window_errors,
    audit_opportunities_batched,
)
from ha_ctse_process.event_commitment_rng import (
    OPPORTUNITY_SUPPORT,
    RNG_NAMES,
    authoritative_seed_map,
    make_training_state,
)
from ha_ctse_process.event_commitment_types import LifecycleState, MARK_DIM
from ha_ctse_process.noncalendar_commitment_testbed import make_noncalendar_ledger


_MOVED_OWNERS = {
    "AUDIT_BRANCHES",
    "AUDIT_STREAM_NAMES",
    "_AuditStream",
    "_AuditStreamView",
    "_AuditGenerator",
    "_audit_opportunity_script",
    "_audit_cursor",
    "_clone_audit_cursor",
    "_audit_branch_state",
    "_branch_boundary",
    "_apply_audit_event",
    "_audit_focal_segment_index",
    "_check_audit_provenance",
    "_audit_row_scripts",
    "_audit_row_errors",
    "_audit_row_continuous_diagnostic",
    "_audit_payload_tensor",
    "_audit_serialized_size",
    "audit_opportunities_batched",
    "_audit_stochastic_opportunity",
    "audit_single_opportunity",
    "_AUDIT_DISCRETE_FIELDS",
    "_AUDIT_CONTINUOUS_FIELDS",
    "_AUDIT_EVENT_FIELDS",
    "_audit_segment_mismatches",
    "_audit_window_errors",
}


def _defined_names(module: Any) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(
                target.id for target in targets if isinstance(target, ast.Name)
            )
    return names


def test_audit_cluster_has_one_concrete_owner_and_no_legacy_cycle() -> None:
    audit_names = _defined_names(event_commitment_audit)
    assert _MOVED_OWNERS <= audit_names
    assert not Path(event_commitment_audit.__file__).with_name(
        "event_held_commitment_link.py"
    ).exists()
    audit_source = Path(event_commitment_audit.__file__).read_text(encoding="utf-8")
    assert "event_held_commitment_link" not in audit_source

    tree = ast.parse(audit_source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == audit_opportunities_batched.__name__
    )
    for loop in (
        node for node in ast.walk(function)
        if isinstance(node, (ast.For, ast.While))
    ):
        for call in (
            node for node in ast.walk(loop) if isinstance(node, ast.Call)
        ):
            if isinstance(call.func, ast.Attribute):
                assert call.func.attr not in {"item", "numpy"}, ast.unparse(call)


def test_cloned_audit_cursor_does_not_mutate_origin() -> None:
    seeds = authoritative_seed_map("held_out", 0)
    ledger = make_noncalendar_ledger(
        0, profile="held_out", task_seed=seeds["ledger"],
        order_seed=seeds["order"],
    )
    cursor = _audit_cursor((ledger,), (0,), torch.device("cpu"))
    key = int(ledger.routing_permutation[0])
    cursor.lifecycles[0][key] = LifecycleState(
        membership_epoch=3,
        z=torch.ones(MARK_DIM),
        q=4,
        segment_id=5,
        segment_start_active_step=6,
    )
    original_time = int(cursor.environments[0].time)
    clone = _clone_audit_cursor(cursor)

    clone.hidden.add_(1.0)
    clone.lifecycles[0][key].z.zero_()
    clone.lifecycles[0][key].q += 1
    clone.segments[0].append("branch-only")  # type: ignore[arg-type]
    clone.environments[0].time += 1

    assert torch.count_nonzero(cursor.hidden) == 0
    assert torch.equal(cursor.lifecycles[0][key].z, torch.ones(MARK_DIM))
    assert cursor.lifecycles[0][key].q == 4
    assert cursor.segments[0] == []
    assert cursor.environments[0].time == original_time


def _consume_branch_streams(state: Any) -> tuple[np.ndarray, ...]:
    return (
        state.rngs["primitive"].random(
            (2, MAX_LIFECYCLES), dtype=np.float32
        ),
        state.rngs["opportunity"].choice(OPPORTUNITY_SUPPORT, size=4),
        state.rngs["event"].random(4, dtype=np.float32),
        state.rngs["mark"].standard_normal((4, MARK_DIM), dtype=np.float32),
    )


def test_keep_and_renew_consume_equal_six_stream_rng_end_state() -> None:
    keep = make_training_state("EHC", 0, profile="held_out")
    renew = deepcopy(keep)
    keep_draws = _consume_branch_streams(keep)
    renew_draws = _consume_branch_streams(renew)

    assert AUDIT_STREAM_NAMES == (
        "opportunity", "event", "mark", "primitive"
    )
    for keep_values, renew_values in zip(keep_draws, renew_draws, strict=True):
        assert keep_values.dtype == renew_values.dtype
        assert np.array_equal(keep_values, renew_values)
    keep_end, renew_end = _rng_states(keep), _rng_states(renew)
    assert tuple(keep_end) == RNG_NAMES
    assert tuple(renew_end) == RNG_NAMES
    assert _nested_equal(keep_end, renew_end)


def _window_fixture() -> SimpleNamespace:
    values: dict[str, Any] = {
        name: torch.zeros((1, 1, 1), dtype=torch.int64)
        for name in _AUDIT_DISCRETE_FIELDS
    }
    values.update({
        name: torch.zeros((1, 1, 1), dtype=torch.float32)
        for name in _AUDIT_CONTINUOUS_FIELDS
    })
    values["time_steps"] = 1
    values["segments"] = ((),)
    return SimpleNamespace(**values)


def test_causal_window_errors_fail_closed_on_representative_fields() -> None:
    stored = _window_fixture()
    exact = _window_fixture()
    assert _audit_window_errors(exact, stored, start=0) == {
        "discrete_mismatch": 0.0,
        "mismatched_fields": (),
        "continuous": 0.0,
        "continuous_field": "",
        "segment_mismatch": 0.0,
        "segment_environments": (),
    }

    discrete = _window_fixture()
    discrete.actions[0, 0, 0] = 1
    assert _audit_window_errors(
        discrete, stored, start=0
    )["mismatched_fields"] == ("actions",)

    excluded = _window_fixture()
    excluded.event_kind[0, 0, 0] = 1
    assert _audit_window_errors(
        excluded, stored, start=0, excluded=(0, 0)
    )["discrete_mismatch"] == 0.0
    assert _audit_window_errors(
        excluded, stored, start=0
    )["discrete_mismatch"] == 1.0

    continuous = _window_fixture()
    continuous.observations[0, 0, 0] = 2.0e-7
    continuous_errors = _audit_window_errors(continuous, stored, start=0)
    assert continuous_errors["continuous_field"] == "observations"
    assert continuous_errors["continuous"] > 0.0

    segments = _window_fixture()
    segments.segments = (("branch-only",),)
    segment_errors = _audit_window_errors(segments, stored, start=0)
    assert segment_errors["segment_mismatch"] == 1.0
    assert segment_errors["mismatched_fields"] == ("segments",)

from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.native_fusion_r01 import (
    Consumer,
    EventOrder,
    Regime,
    deterministic_fixture,
    native_run_fixture,
    oracle_run_fixture,
    recompute_endpoint,
    token_view,
    S0FirewallError,
    StageBarrier,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.acceptance import (
    build_s0_acceptance,
    emit_create_only,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.manifest import (
    load_and_validate_source_manifest,
    source_manifest_path,
)


ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize(
    ("order", "regime", "switch_tick", "command", "phase"),
    [
        (EventOrder.RG, Regime.FIXED_4, 0, (1, 1, 1), 0),
        (EventOrder.GR, Regime.FIXED_14, 0, (0, 2, 1), 1),
        (EventOrder.RG, Regime.SWITCH_6_TO_14, 168, (2, 1, 0), 2),
        (EventOrder.GR, Regime.SWITCH_14_TO_6, 252, (1, 0, 2), 3),
    ],
)
def test_independent_oracle_and_native_paths_match_exact_task_law(
    order: EventOrder,
    regime: Regime,
    switch_tick: int,
    command: tuple[int, int, int],
    phase: int,
) -> None:
    fixture = deterministic_fixture(
        event_order=order,
        regime=regime,
        switch_tick=switch_tick,
        command=command,
        phase=phase,
    )

    oracle = oracle_run_fixture(fixture)
    native = native_run_fixture(fixture)

    assert asdict(native) == asdict(oracle)
    assert native.endpoint.integrated_ticks <= 420
    assert native.endpoint.policy_queries == sum(
        record.policy_queried for record in native.trace
    )
    assert native.endpoint.masked_post_absorption_slots == (
        420 - native.endpoint.integrated_ticks
    )


def test_public_hold_and_switch_clocks_change_only_at_renewal_boundary() -> None:
    result = native_run_fixture(
        deterministic_fixture(
            event_order=EventOrder.RG,
            regime=Regime.SWITCH_6_TO_14,
            switch_tick=168,
            command=(1, 1, 1),
        )
    )

    renewal_rows = [record for record in result.trace if record.policy_queried]
    at_boundary = next(record for record in renewal_rows if record.tick == 168)
    before_boundary = next(record for record in renewal_rows if record.tick == 162)
    after_boundary = next(record for record in renewal_rows if record.tick == 182)

    assert (before_boundary.k, at_boundary.k, after_boundary.k) == (6, 14, 14)
    assert all(record.k == 6 for record in result.trace if record.tick < 168)
    assert all(record.k == 14 for record in result.trace if record.tick >= 168)


def test_endpoint_recomputation_enforces_failure_before_delivery() -> None:
    result = native_run_fixture(
        deterministic_fixture(
            event_order=EventOrder.RG,
            regime=Regime.FIXED_4,
            command=(2, 2, 2),
        )
    )

    assert recompute_endpoint(result) == result.endpoint
    assert (
        result.trace[-1].overload
        or result.trace[-1].swing
        or result.trace[-1].formation
    )
    invalid = replace(
        result,
        trace=result.trace[:-1] + (replace(result.trace[-1], delivery=True),),
    )
    with pytest.raises(ValueError, match="failure must dominate"):
        recompute_endpoint(invalid)


def test_ordered_token_taint_is_absent_from_foundation_and_set() -> None:
    rg = native_run_fixture(
        deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_4)
    )
    gr = native_run_fixture(
        deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_4)
    )

    assert rg.setup.public_observation == gr.setup.public_observation
    assert token_view(EventOrder.RG, Consumer.FOUNDATION) == token_view(
        EventOrder.GR, Consumer.FOUNDATION
    )
    assert token_view(EventOrder.RG, Consumer.SET) == token_view(
        EventOrder.GR, Consumer.SET
    )
    assert token_view(EventOrder.RG, Consumer.TREAT).chronology_q == 1.0
    assert token_view(EventOrder.GR, Consumer.TREAT).chronology_q == 0.0
    assert token_view(EventOrder.RG, Consumer.FREE).chronology_q == 1.0
    assert token_view(EventOrder.GR, Consumer.FREE).chronology_q == 0.0
    assert token_view(EventOrder.RG, Consumer.REVERSED).chronology_q == 0.0
    assert token_view(EventOrder.GR, Consumer.REVERSED).chronology_q == 1.0


def test_s0_stage_barrier_rejects_every_downstream_identity_and_value() -> None:
    barrier = StageBarrier.s0()

    assert barrier.materialized == frozenset(
        {"source_manifest", "technical_acceptance"}
    )
    assert barrier.next_conditional_stage == "FOUNDATION_CONSTRUCTION"
    assert barrier.effect_refs == ()
    for forbidden in (
        "master_id",
        "model_path",
        "checkpoint_sha256",
        "competence_gate",
        "opportunity_assay",
        "adapter_identity",
        "training_command",
        "evaluation_output",
        "scientific_result",
        "partial_value",
    ):
        with pytest.raises(S0FirewallError, match="forbidden S0 field"):
            barrier.validate_payload({"schema": "S0", forbidden: "present"})


def test_source_manifest_binds_every_current_s0_source_and_test_byte() -> None:
    manifest = load_and_validate_source_manifest(source_manifest_path(ROOT), ROOT)

    paths = tuple(row["path"] for row in manifest["files"])
    assert paths == tuple(sorted(set(paths)))
    assert "tests/experiments/candidates/scdmp_variable_k/test_native_fusion_r01_s0.py" in paths
    assert all("uav_suspended_payload_order_value" not in path for path in paths)
    assert manifest["effect_refs"] == []
    assert manifest["activity_authorized"] is False


def test_s0_acceptance_is_atomic_create_only_and_firewalled(tmp_path: Path) -> None:
    manifest = load_and_validate_source_manifest(source_manifest_path(ROOT), ROOT)
    acceptance = build_s0_acceptance(
        repository_root=ROOT,
        source_manifest=manifest,
        measurements={
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_tracemalloc_bytes": 3,
            "peak_rss_bytes": 4,
            "read_bytes": 5,
            "write_bytes": 6,
        },
        verification_command="python -m pytest exact-s0-test -q",
        verification_sha256="1" * 64,
    )
    StageBarrier.s0().validate_payload(acceptance)
    target = tmp_path / "S0_TECHNICAL_ACCEPTANCE.json"

    emit_create_only(target, acceptance)

    assert json.loads(target.read_text(encoding="ascii")) == acceptance
    with pytest.raises(FileExistsError):
        emit_create_only(target, acceptance)

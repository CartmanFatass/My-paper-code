from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import (
    lease as lease_module,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import (
    production_evaluation as production,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.config import (
    EventOrder,
    Regime,
    deterministic_fixture,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.frontier import (
    CheckpointReceipt,
    FrontierContractError,
    require_global_checkpoint_barrier,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.host_types import (
    PublicObservation,
    RenewalAccounting,
    RenewalTransition,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.lease import (
    ActivityPermit,
    COORDINATE_PLAN_DIGEST,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.rng import (
    EmpiricalRNG,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.support import (
    QUOTIENT_REPRESENTATIVES,
)


def _permit() -> ActivityPermit:
    return ActivityPermit(
        lease_id="SYNTHETIC-PRODUCTION-EVALUATION-FIXTURE",
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        _validation_seal=lease_module._PERMIT_SEAL,
    )


def _receipts() -> tuple[CheckpointReceipt, ...]:
    return tuple(
        CheckpointReceipt(
            replicate=replicate,
            arm=arm,
            coordinate_digest=COORDINATE_PLAN_DIGEST,
            checkpoint_digest=f"{replicate * 3 + arm_index + 1:064x}",
            optimizer_step=2_304,
            technically_accepted=True,
        )
        for replicate in range(18)
        for arm_index, arm in enumerate(("TREAT", "FREE", "SET"))
    )


class _NeverLoader:
    def __init__(self) -> None:
        self.calls = 0

    def load_final_model(self, **_kwargs):
        self.calls += 1
        raise AssertionError("malformed checkpoint inventory must fail before model load")


class _MockActor:
    """Tiny deterministic actor fixture; no real model identity is created."""

    def __init__(self, arm: str) -> None:
        self.arm = arm
        self._fixture_weight = torch.tensor([0.5], dtype=torch.float32)

    def state_dict(self):
        return {"fixture_weight": self._fixture_weight}

    def __call__(self, observation, true_q):
        logits = torch.zeros((observation.shape[0], 27), dtype=torch.float32)
        if self.arm == "TREAT":
            logits[:, 26] = 0.5 - true_q * 0.75
        return SimpleNamespace(logits=logits)


def _models() -> dict[str, _MockActor]:
    result = {arm: _MockActor(arm) for arm in ("TREAT", "FREE", "SET")}
    # At RG (q=1), the exact treatment tilt moves the lexicographic maximum
    # from high-risk action 26 to action 0.  REVERSED uses the same weights with
    # q=0 and therefore selects action 26.
    return result


def _public(fixture, *, x: float) -> PublicObservation:
    k = fixture.regime.initial_k
    return PublicObservation(
        x=x,
        v=fixture.initial_v / 1.8,
        phi=fixture.initial_phi / 0.48,
        omega=0.0,
        z=0.0,
        f=0.0,
        tau_1=0.0,
        tau_2=0.0,
        tau_3=0.0,
        u_1_previous=0.0,
        u_2_previous=0.0,
        u_3_previous=0.0,
        mission_fraction=0.0,
        k_scaled=k / 14.0,
    )


def _transition(fixture, *, action: int | None, terminal: bool) -> RenewalTransition:
    integrated = 1 if action is not None else 0
    effort = 0.0 if action is None else float(action) / 26.0
    return RenewalTransition(
        public=_public(fixture, x=0.1 * integrated + effort * 0.01),
        event_tokens=fixture.event_order.tokens,
        chronology_q=fixture.event_order.q,
        realized_duration=integrated,
        primitive_rewards=(0.0,) if integrated else (),
        reward=0.0,
        terminal=terminal,
        delivery=terminal,
        timeout=False,
        physical_failure=False,
        overload=False,
        swing=False,
        formation=False,
        accounting=RenewalAccounting(
            allocated_slots=420,
            integrated_ticks=integrated,
            masked_post_absorption_slots=419 if terminal else 0,
            policy_queries=integrated,
            terminal_tick=integrated if terminal else None,
            delivery_time_seconds=0.1 if terminal else None,
            completion_time_seconds=0.1 if terminal else None,
            cumulative_reward=0.0,
            mean_active_effort=effort,
        ),
    )


class _OneIntervalBatch:
    def __init__(self, fixtures, recorder, *, terminal: bool) -> None:
        self.fixtures = tuple(fixtures)
        self.batch_width = len(self.fixtures)
        self._active = True
        self._terminal = terminal
        self._recorder = recorder

    @property
    def active(self):
        return (self._active,) * self.batch_width

    def advance(self, actions):
        materialized = tuple(actions)
        self._recorder.append(materialized)
        assert self._active
        self._active = False
        return tuple(
            _transition(fixture, action=action, terminal=self._terminal)
            for fixture, action in zip(self.fixtures, materialized)
        )

    def close(self) -> None:
        self._active = False


def _factory(recorder, *, terminal: bool):
    def reset(fixtures):
        materialized = tuple(fixtures)
        batch = _OneIntervalBatch(materialized, recorder, terminal=terminal)
        starts = tuple(
            _transition(fixture, action=None, terminal=False) for fixture in materialized
        )
        return batch, starts

    return reset


def test_checkpoint_inventory_fails_before_any_final_model_load(tmp_path) -> None:
    permit = _permit()
    receipts = _receipts()
    barrier = require_global_checkpoint_barrier(receipts)
    loader = _NeverLoader()
    service = production.ProductionEvaluationService(
        result_root=tmp_path / "future-result", model_loader=loader
    )
    with pytest.raises(FrontierContractError, match="exactly 54"):
        service.evaluate_panel(
            permit,
            EmpiricalRNG(b"fixture-master-key".ljust(32, b"\0"), permit),
            barrier,
            receipts[:-1],
        )
    assert loader.calls == 0
    assert not service.result_root.exists()


def test_closed_loop_native_argmax_reuses_treat_weights_for_reversed(monkeypatch) -> None:
    recorder: list[tuple[int | None, ...]] = []
    monkeypatch.setattr(
        production, "reset_native_renewal_batch", _factory(recorder, terminal=True)
    )
    fixture = deterministic_fixture(
        event_order=EventOrder.RG,
        regime=Regime.FIXED_6,
        command=(0, 0, 0),
    )
    models = _models()
    before = production._model_digest(models["TREAT"])
    rows = production._run_evaluation_scenario(
        replicate=0,
        regime="fixed-6",
        scenario=0,
        order="RG",
        switch_tick=0,
        scenario_digest="a" * 64,
        fixture=fixture,
        models=models,
    )
    assert [row.controller for row in rows] == ["TREAT", "FREE", "REVERSED", "SET"]
    assert recorder == [(0, 0, 26, 0)]
    assert production._model_digest(models["TREAT"]) == before
    assert all(row.safe_delivery and row.post_absorption_policy_queries == 0 for row in rows)


def test_support_cell_uses_exact_ten_representatives_per_history(monkeypatch) -> None:
    recorder: list[tuple[int | None, ...]] = []
    monkeypatch.setattr(
        production, "reset_native_renewal_batch", _factory(recorder, terminal=True)
    )
    permit = _permit()
    rows = production._run_support_cell(
        EmpiricalRNG(b"support-fixture-key".ljust(32, b"\0"), permit),
        replicate=0,
        k=6,
        state_index=0,
    )
    assert len(rows) == 20
    assert recorder == [QUOTIENT_REPRESENTATIVES, QUOTIENT_REPRESENTATIVES]
    assert {row.history for row in rows} == {"RG", "GR"}
    assert len({row.public_state_digest for row in rows}) == 1
    assert len({row.disturbance_digest for row in rows}) == 1
    assert all(row.action_code in QUOTIENT_REPRESENTATIVES for row in rows)
    certificate = production._require_quotient_certificate()
    assert certificate["candidate_trajectory_count"] == 10
    assert certificate["nested_replanning"] is False


def test_barrier_coordinate_must_match_the_sealed_activity_permit(tmp_path) -> None:
    permit = _permit()
    receipts = _receipts()
    barrier = replace(
        require_global_checkpoint_barrier(receipts), coordinate_digest="f" * 64
    )
    service = production.ProductionEvaluationService(
        result_root=tmp_path / "result", model_loader=_NeverLoader()
    )
    with pytest.raises(production.ProductionEvaluationContractError, match="not open"):
        service.support_panel(
            permit,
            EmpiricalRNG(b"barrier-fixture-key".ljust(32, b"\0"), permit),
            barrier,
        )

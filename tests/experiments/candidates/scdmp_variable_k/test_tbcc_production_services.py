from __future__ import annotations

from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.artifacts import (
    test_only_bindings as make_test_only_bindings,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.config import (
    MAX_HOLD_TICKS,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.evaluation import (
    AcceptedControllerBinding,
    validate_complete_scenarios,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.host_types import (
    HostOutput,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.lifecycle import (
    GateOutcome,
    TechnicalFinal,
    issue_opportunity_execution_permit,
    snapshot,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.production_services import (
    NativeProductionServices,
    ProductionServiceContractError,
    ServiceAuthority,
    production_service_contract,
    test_only_service_authority as make_test_only_service_authority,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.source_manifest import (
    ACCEPTED_NATIVE_ARTIFACT_SHA256,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.training import (
    DurationCorrectPPOTrainer,
)


TEST_ONLY_MASTER = bytes(range(32))


@pytest.fixture(autouse=True, scope="module")
def _one_torch_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(previous)


def _initial(k: int) -> HostOutput:
    return HostOutput(
        advanced=False,
        active=True,
        terminal=False,
        ticks_advanced=0,
        tick=0,
        hold_k=0,
        next_k=k,
        observation=(0.0,) * 18,
        safe_dock=False,
        timeout=False,
        cable_overload=False,
        gantry_contact=False,
        attitude_loss=False,
        formation_loss=False,
        cumulative_reward=0.0,
        cumulative_energy=0.0,
        energy_ticks=0,
        dock_tick=None,
        last_hold_reward_count=0,
        last_hold_rewards=(0.0,) * MAX_HOLD_TICKS,
    )


class _OneHoldSession:
    widths: list[int] = []

    def __init__(self, resets) -> None:
        values = tuple(resets)
        self.widths.append(len(values))
        self.initial = tuple(_initial(value.k_initial) for value in values)
        self._last = self.initial
        self.closed = False

    def renew(self, rows):
        values = tuple(rows)
        assert len(values) == len(self._last)
        outputs = []
        for old, row in zip(self._last, values):
            if not old.active:
                outputs.append(old)
                continue
            reward = 0.01 * (row.action + 1)
            outputs.append(
                replace(
                    old,
                    advanced=True,
                    active=False,
                    terminal=True,
                    ticks_advanced=1,
                    tick=1,
                    hold_k=old.next_k,
                    timeout=True,
                    cumulative_reward=reward,
                    cumulative_energy=1.0,
                    energy_ticks=1,
                    last_hold_reward_count=1,
                    last_hold_rewards=(reward,) + (0.0,) * (MAX_HOLD_TICKS - 1),
                )
            )
        self._last = tuple(outputs)
        return self._last

    def close(self) -> None:
        self.closed = True


class _BadRewardTailSession(_OneHoldSession):
    def renew(self, rows):
        outputs = list(super().renew(rows))
        payload = asdict(outputs[0])
        payload["last_hold_rewards"] = payload["last_hold_rewards"][:-1] + (0.5,)
        outputs[0] = SimpleNamespace(**payload)
        self._last = tuple(outputs)
        return self._last


def _guard_calls():
    calls = []

    def guard(component, *, backend, batch_width, build_root):
        calls.append((component, backend, batch_width, build_root))
        return {
            "component": component,
            "backend": backend,
            "batch_width": batch_width,
            "full_reset_step_cpp": True,
            "python_fallback": False,
            "native": {
                "binding_kind": "TEST_ONLY_ctypes_cdll",
                "artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
            },
        }

    return calls, guard


def _services(token: str = "services"):
    calls, guard = _guard_calls()
    authority = make_test_only_service_authority(TEST_ONLY_MASTER, token=token)
    service = NativeProductionServices(
        authority=authority,
        master=TEST_ONLY_MASTER,
        shared_guard=guard,
        session_factory=_OneHoldSession,
    )
    return authority, service, calls


def test_authority_is_checked_before_master_or_native_access() -> None:
    calls, guard = _guard_calls()
    unsealed = ServiceAuthority(
        source_manifest_sha256="",
        lineage_digest="",
        coordinate_manifest_sha256="",
        coordinate_proposal_digest="",
        native_binding_sha256="",
        native_source_sha256="",
        native_build_key="",
        native_artifact_sha256="",
        master_sha256="",
        authorization_sha256="",
        test_only=True,
        expires_at=None,
    )
    with pytest.raises(ProductionServiceContractError, match="sealed service authority"):
        NativeProductionServices(authority=unsealed, master=b"bad", shared_guard=guard)
    assert calls == []


def test_exact_plan_and_fresh_address_contracts() -> None:
    authority, service, calls = _services("plan")
    contract = production_service_contract()
    assert contract["widths"] == {
        "foundation_training": 12,
        "order_training": 12,
        "foundation_competence": 120,
        "final_evaluation": 120,
        "opportunity": 144,
    }
    assert contract["counts"]["complete_episodes_or_rollouts"] == 343_296
    assert contract["counts"]["complete_max_policy_queries"] == 15_829_632
    assert contract["counts"]["complete_adamw_steps"] == 129_024
    assert contract["opportunity"] == {
        "k": (7, 13),
        "states_per_k": 16,
        "graphs": 2,
        "actions": 18,
        "common_tapes": 4,
        "rollouts_per_pair": 144,
    }
    first = service.addresses.initial_draws(
        replicate=0,
        domain="opportunity-state",
        address={"k": 7, "state": 0},
    )
    second = service.addresses.initial_draws(
        replicate=0,
        domain="opportunity-state",
        address={"k": 7, "state": 1},
    )
    assert first != second
    assert service.addresses.action_uniform(
        replicate=0, domain="ORDER_SHARED", update=1, episode_slot=0, renewal=0
    ) == service.addresses.action_uniform(
        replicate=0, domain="ORDER_SHARED", update=1, episode_slot=0, renewal=0
    )
    assert authority.test_only is True
    assert calls == []
    assert make_test_only_bindings(token="unused").test_only is True


def test_width12_native_training_update_returns_only_in_memory_objects() -> None:
    _OneHoldSession.widths.clear()
    authority, service, calls = _services("training")
    foundation = service.materialize_foundation(replicate=0)
    trainer = DurationCorrectPPOTrainer(foundation, permit=authority)
    output = service.collect_and_train_update(trainer=trainer, update=1)
    assert _OneHoldSession.widths == [12]
    assert [row[2] for row in calls] == [12]
    assert output.frozen_batch.record_count == 12
    assert output.frozen_batch.episode_offsets == tuple(range(13))
    assert output.update_receipt.optimizer_step == 12
    assert len(output.update_receipt.steps) == 12
    assert output.checkpoint_payload["completed_updates"] == 1
    assert output.checkpoint_payload["optimizer"]["step_index"] == 12
    assert output.question_relevant_output is False


def test_training_rejects_noncanonical_native_reward_tail() -> None:
    calls, guard = _guard_calls()
    authority = make_test_only_service_authority(TEST_ONLY_MASTER, token="bad-tail")
    service = NativeProductionServices(
        authority=authority,
        master=TEST_ONLY_MASTER,
        shared_guard=guard,
        session_factory=_BadRewardTailSession,
    )
    foundation = service.materialize_foundation(replicate=0)
    trainer = DurationCorrectPPOTrainer(foundation, permit=authority)
    with pytest.raises(ProductionServiceContractError, match="canonical zero"):
        service.collect_and_train_update(trainer=trainer, update=1)
    assert [row[2] for row in calls] == [12]


def test_width120_scenarios_balance_and_lazy_native_cell() -> None:
    _OneHoldSession.widths.clear()
    _, service, calls = _services("evaluation")
    scenarios = service.evaluation_scenarios(replicate=1, stage="foundation-competence")
    validate_complete_scenarios(scenarios)
    for regime in ("7-to-13", "13-to-7"):
        rows = tuple(row for row in scenarios if row.regime == regime)
        assert {
            (order, tick): sum(row.graph_order == order and row.switch_tick == tick for row in rows)
            for order in ("HR", "RH")
            for tick in (91, 273)
        } == {("HR", 91): 30, ("HR", 273): 30, ("RH", 91): 30, ("RH", 273): 30}
    foundation = service.materialize_foundation(replicate=1)
    binding = AcceptedControllerBinding(
        controller="FOUNDATION",
        source_arm="FOUNDATION",
        model_digest="1" * 64,
        model=foundation,
        technically_accepted=True,
        frozen=True,
    )
    adapter = service.evaluation_adapter(
        stage="foundation-competence", replicate=1, scenarios=scenarios
    )
    scenario = next(row for row in scenarios if row.regime == "fixed-5" and row.scenario_index == 0)
    endpoint = adapter.evaluate_scenario(
        binding=binding, replicate=1, controller="FOUNDATION", scenario=scenario
    )
    assert endpoint.timeout is True
    assert endpoint.post_absorption_policy_queries == 0
    assert _OneHoldSession.widths == [120]
    assert [row[2] for row in calls] == [12, 120]


def test_width144_stage1b_uses_four_common_tapes_and_all_actions() -> None:
    _OneHoldSession.widths.clear()
    _, service, calls = _services("opportunity")
    foundation = service.materialize_foundation(replicate=0)
    finals = tuple(
        TechnicalFinal(
            replicate=index,
            arm="FOUNDATION",
            fake_digest=f"TEST_ONLY_FAKE_SHA256:{index:064x}",
        )
        for index in range(24)
    )
    permit = issue_opportunity_execution_permit(
        snapshot(finals, foundation_gate=GateOutcome.PASS)
    )
    tapes = service.opportunity_tapes(replicate=0, k=7, state_index=0)
    assert len(tapes) == 4
    assert len({value.digest for value in tapes}) == 4
    metrics = service.run_opportunity_pair(
        replicate=0,
        k=7,
        state_index=0,
        permit=permit,
        foundation=foundation,
    )
    assert metrics.rollout_count == 144
    assert metrics.argmax_q0 == frozenset(range(18))
    assert metrics.argmax_q1 == frozenset(range(18))
    assert metrics.q_value == metrics.d_value == metrics.s_value == 0.0
    assert _OneHoldSession.widths == [144]
    assert [row[2] for row in calls] == [12, 144]

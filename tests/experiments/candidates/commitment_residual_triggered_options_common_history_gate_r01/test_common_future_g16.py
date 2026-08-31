import numpy as np

from experiments.candidates.commitment_residual_triggered_options.host import (
    EventClass, Regime, ScenarioSpec, ServiceRelayHost, build_scenario_tape,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.evaluation import (
    native_regret, select_printed_action,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    canonical_tape, enumerate_common_future_g16, scripted_decisions,
)


def test_common_future_has_exact_steps_mask_order_and_charge_once() -> None:
    host = ServiceRelayHost(build_scenario_tape(
        ScenarioSpec(0, 991, Regime.K8, EventClass.NONE, 50, 0.25)
    ))
    while host.state.primitive_time < 60:
        host.advance(scripted_decisions(host))
    aligned_clone = host.clone(retain_records=False)
    aligned = scripted_decisions(aligned_clone)
    before_tape = canonical_tape(host.tape)
    audit = enumerate_common_future_g16(host, target_agent=0, aligned_decisions=aligned)
    assert canonical_tape(host.tape) == before_tape
    assert all(count == 16 for count in audit.branch_steps)
    assert audit.first_step_target_charges[0] == 0.0
    assert all(charge == 0.30 for charge in audit.first_step_target_charges[1:])
    assert np.isfinite(audit.action_values[audit.legal_mask]).all()
    oracle = select_printed_action(audit.action_values, audit.legal_mask)
    assert native_regret(audit.action_values, audit.legal_mask, oracle) == 0.0


def test_masking_and_printed_order_ties() -> None:
    values = np.asarray((2.0, 99.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0))
    legal = np.asarray((True, False, True, True, False, False, False, False))
    assert select_printed_action(values, legal) == 0

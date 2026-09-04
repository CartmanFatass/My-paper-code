from __future__ import annotations

import math
import struct

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import native_backend as backend_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_backend import (
    NativeBackendError,
    NativeSession,
    ReachableStatePanelNotEstablished,
    construct_reachable_twins,
    evaluate_twin_branches,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    ACTION_COUNT,
    HR_ASSIGNMENT,
    RH_ASSIGNMENT,
    DisturbanceHold,
    TapeAddress,
    TapeNamespace,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.contracts import (
    STATE_SPECS, build_run_manifest,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.rng import (
    development_tape_address,
    CounterRNG,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.foundation import (
    ImmutableBatchedFoundationPolicy, freeze_foundation_actor, materialize_foundation,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.host_types import (
    RenewalLane as ReferenceRenewalLane,
    ResetLane as ReferenceResetLane,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.native_backend import (
    NativeBatch as ReferenceNativeBatch,
)


def fixture_tape(holds: int = 64) -> tuple[DisturbanceHold, ...]:
    """Deterministic TEST tape; this is not a scientific RNG root."""

    rows = []
    for hold in range(holds):
        rows.append(
            DisturbanceHold(
                eta_v=tuple(0.003 if (hold + tick) % 2 == 0 else -0.003 for tick in range(13)),
                eta_y=tuple(0.002 if (hold + 2 * tick) % 3 else -0.002 for tick in range(13)),
                eta_omega=tuple(0.004 if (2 * hold + tick) % 3 else -0.004 for tick in range(13)),
            )
        )
    return tuple(rows)


def evaluation_tape(holds: int = 64) -> tuple[DisturbanceHold, ...]:
    return tuple(
        DisturbanceHold(
            eta_v=tuple(-value for value in row.eta_v),
            eta_y=tuple(-value for value in row.eta_y),
            eta_omega=tuple(-value for value in row.eta_omega),
        )
        for row in fixture_tape(holds)
    )


def _state(k: int, target: int):
    return next(row for row in STATE_SPECS if (row.k, row.target_tick) == (k, target))


TEST_MANIFEST = build_run_manifest(b"scdmp-b01-test-master-32-bytes!!")


class ZeroPolicy:
    def __init__(self, seed: int) -> None:
        self.foundation_seed = seed

    def __call__(self, observations):
        return (0,) * len(observations)


def _zero_for(k: int, target: int) -> ZeroPolicy:
    return ZeroPolicy(_state(k, target).source_seed)


@pytest.mark.parametrize(
    ("k", "target", "expected"),
    ((7, 64, 70), (7, 160, 161), (7, 256, 259), (13, 64, 65), (13, 160, 169), (13, 256, 260)),
)
def test_constructs_real_reachable_twins_at_first_eligible_boundary(k: int, target: int, expected: int):
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(k, target), prefix_policy=_zero_for(k, target),
    )

    assert twins.eligible is True
    assert twins.k == k
    assert twins.target_tick == target
    assert twins.boundary_tick == expected
    assert twins.selected_tape_index == 0
    assert twins.source_renewal_index == expected // k - 1
    assert twins.transitions == expected
    assert twins.policy_queries == expected // k
    assert twins.hr_public_bytes == twins.rh_public_bytes
    assert twins.hr_public_bytes == struct.pack("<18d", *twins.hr.output.observation)
    assert twins.hr_assignment == HR_ASSIGNMENT == (4, 2, 1, 3)
    assert twins.rh_assignment == RH_ASSIGNMENT == (1, 4, 2, 3)
    assert twins.hr_assignment != twins.rh_assignment
    assert twins.hr.event_phase == twins.rh.event_phase == "POST_EVENT"
    assert twins.hr.event_order == "HR"
    assert twins.rh.event_order == "RH"
    assert twins.source_snapshot_bytes != twins.hr.state_bytes
    assert twins.source_snapshot_bytes != twins.rh.state_bytes
    assert twins.hr.state_bytes != twins.rh.state_bytes
    assert twins.hr.output.tick == twins.rh.output.tick == expected
    assert twins.hr.output.terminal is False
    source = NativeSession.from_state_bytes((twins.source_snapshot_bytes,)).states()[0]
    assert source.event_phase == "PRE_EVENT"
    assert source.event_order is None
    assert source.latent_assignment == (1, 2, 3, 4)
    assert source.latent_q == twins.pre_event_q
    assert twins.pre_event_q == TEST_MANIFEST.q_by_cell[STATE_SPECS.index(_state(k, target))]
    assert twins.persistent_twin_bytes_equal


def test_complete_native_snapshot_clone_and_restore_are_direct_byte_exact():
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(13, 64), prefix_policy=_zero_for(13, 64),
    )
    left = NativeSession.from_states((twins.hr, twins.rh))
    right = NativeSession.from_state_bytes((twins.hr.state_bytes, twins.rh.state_bytes))
    rows = (fixture_tape()[6], fixture_tape()[6])
    left_output = left.step((0, 0), rows)
    right_output = right.step((0, 0), rows)

    assert left_output == right_output
    assert left.state_bytes() == right.state_bytes()
    assert left.latent_assignments() == (HR_ASSIGNMENT, RH_ASSIGNMENT)


def test_native_state_validation_rejects_repeat_event_and_tampered_complete_state():
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(13, 64), prefix_policy=_zero_for(13, 64),
    )
    post = NativeSession.from_states((twins.hr, twins.rh))
    with pytest.raises(NativeBackendError, match="event/sentinel"):
        post.apply_orders(("HR", "RH"))

    for mutation in ("phase", "finite", "cached"):
        raw = backend_module._NativeState.from_buffer_copy(twins.hr.state_bytes)
        if mutation == "phase":
            raw.event_phase = 0
        elif mutation == "finite":
            raw.reward_sum = math.nan
        else:
            raw.cached.n += 1
        payload = bytes(memoryview(raw))
        with pytest.raises(NativeBackendError, match="state validation"):
            NativeSession.from_state_bytes((payload,))


@pytest.mark.parametrize("k", (7, 13))
def test_isolated_native_tick_action_reward_and_terminal_semantics_match_reference_host(k: int):
    """TEST-only cross-host equivalence; no consumed runner is imported or invoked."""

    tape = fixture_tape()
    candidate = NativeSession.reset(width=2, k=k, pre_event_q=0)
    candidate.apply_orders(("HR", "RH"))
    reference_resets = (
        ReferenceResetLane((1, 2), k, 0.015, 0.0, 0.0),
        ReferenceResetLane((2, 1), k, 0.015, 0.0, 0.0),
    )
    with ReferenceNativeBatch(reference_resets) as reference:
        for index, actions in enumerate(((0, 0), (10, 12), (12, 10), (0, 0))):
            row = tape[index]
            candidate_outputs = candidate.step(actions, (row, row))
            reference_outputs = reference.step(tuple(
                ReferenceRenewalLane(action, row.eta_v, row.eta_y, row.eta_omega)
                for action in actions
            ))
            for observed, expected in zip(candidate_outputs, reference_outputs, strict=True):
                assert observed.tick == expected.tick
                assert observed.ticks_advanced == expected.ticks_advanced
                assert observed.observation == expected.observation
                assert observed.terminal == expected.terminal
                assert observed.safe_dock == expected.safe_dock
                assert observed.timeout == expected.timeout
                assert observed.cable_overload == expected.cable_overload
                assert observed.gantry_contact == expected.gantry_contact
                assert observed.attitude_loss == expected.attitude_loss
                assert observed.formation_loss == expected.formation_loss
                assert observed.cumulative_reward == expected.cumulative_reward
                assert observed.cumulative_energy == expected.cumulative_energy
                assert observed.energy_ticks == expected.energy_ticks
                assert observed.dock_tick == expected.dock_tick
            if any(item.terminal for item in candidate_outputs):
                break


def test_full_mission_branch_has_fresh_development_tape_one_forced_hold_then_immutable_batched_policy():
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(7, 64), prefix_policy=_zero_for(7, 64),
    )
    calls: list[tuple[bytes, ...]] = []

    class Foundation(ZeroPolicy):
        def __call__(self, observations):
            calls.append(tuple(struct.pack("<18d", *row) for row in observations))
            return super().__call__(observations)

    result = evaluate_twin_branches(
        twins,
        forced_actions=(10, 12),
        evaluation_address=development_tape_address("k7-early", 0),
        foundation_policy=Foundation(1709),
    )

    assert result.width == 2
    assert result.forced_holds == 2
    assert result.policy_queries == sum(len(batch) for batch in calls)
    assert result.policy_batch_calls == len(calls)
    assert result.policy_queries > 0
    assert result.renewal_steps >= 2
    assert result.transitions == sum(item.energy_ticks - twins.boundary_tick for item in result.outputs)
    assert all(item.terminal for item in result.outputs)
    assert all(math.isfinite(item.cumulative_reward) for item in result.outputs)
    assert all(math.isfinite(item.cumulative_energy) for item in result.outputs)
    assert result.raw_returns == tuple(item.cumulative_reward for item in result.outputs)
    assert result.costs == tuple(item.cumulative_energy for item in result.outputs)
    assert result.terminal_counts["total"] == 2
    assert result.terminal_counts["safe_dock"] + result.terminal_counts["failure"] + result.terminal_counts["timeout"] == 2


def test_native_boundary_rejects_invalid_k_width_actions_and_tape_exhaustion():
    with pytest.raises(ValueError, match="six-state checkerboard"):
        construct_reachable_twins(
            run_manifest=TEST_MANIFEST, state_spec=object(), prefix_policy=ZeroPolicy(1709),
        )
    with pytest.raises(ValueError, match="width"):
        NativeSession.reset(width=145, k=7, pre_event_q=0)
    with pytest.raises(ValueError, match="action"):
        session = NativeSession.reset(width=1, k=7, pre_event_q=0)
        session.step((ACTION_COUNT,), (fixture_tape()[0],))
    with pytest.raises(ValueError, match="source foundation"):
        construct_reachable_twins(
            run_manifest=TEST_MANIFEST, state_spec=_state(13, 256), prefix_policy=ZeroPolicy(1709),
        )


def test_real_native_max_width_batch_preserves_lane_positions_and_counts():
    width = 144
    session = NativeSession.reset(width=width, k=13, pre_event_q=0)
    row = fixture_tape()[0]
    outputs = session.step((0,) * width, (row,) * width)

    assert len(outputs) == width
    assert all(item.tick == 13 for item in outputs)
    assert all(item.ticks_advanced == 13 for item in outputs)
    assert all(item.energy_ticks == 13 for item in outputs)
    assert len(session.state_bytes()) == width


def test_branch_rejects_source_namespace_even_with_different_bytes():
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(7, 64), prefix_policy=_zero_for(7, 64),
    )
    with pytest.raises(ValueError, match="SOURCE tape namespace"):
        evaluate_twin_branches(
            twins, forced_actions=(10, 12),
            evaluation_address=TapeAddress(TapeNamespace.SOURCE, 999, "not-the-prefix"),
            foundation_policy=ZeroPolicy(1709),
        )


def test_branch_rejects_freely_constructed_heldout_address():
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(7, 64), prefix_policy=_zero_for(7, 64),
    )
    with pytest.raises(ValueError, match="held-out permit"):
        evaluate_twin_branches(
            twins, forced_actions=(10, 12),
            evaluation_address=TapeAddress(
                TapeNamespace.HELDOUT, 1709,
                "SCDMP-MF-RS-MK-B01/heldout/RUN-01/k7-early/0",
            ),
            foundation_policy=ZeroPolicy(1709),
        )


@pytest.mark.parametrize(
    "address",
    (
        TapeAddress(TapeNamespace.DEVELOPMENT, 2903, "k7-early/0"),
        TapeAddress(TapeNamespace.DEVELOPMENT, 1709, "k7-early/8"),
        TapeAddress(TapeNamespace.DEVELOPMENT, 1709, "k7-early/0/alias"),
    ),
)
def test_branch_rejects_noncanonical_development_root_index_and_alias(address):
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST,
        state_spec=_state(7, 64),
        prefix_policy=_zero_for(7, 64),
    )
    with pytest.raises(ValueError, match="canonical eight"):
        evaluate_twin_branches(
            twins,
            forced_actions=(10, 12),
            evaluation_address=address,
            foundation_policy=ZeroPolicy(1709),
        )


def test_reachable_selector_tries_eight_source_tapes_in_order_and_reports_tape_index(monkeypatch):
    original = backend_module.materialize_disturbance_tape

    def materialize(address, **kwargs):
        if address.namespace is TapeNamespace.SOURCE and address.tape_id.endswith("/0"):
            return original(address, **kwargs)[:1]
        return original(address, **kwargs)

    monkeypatch.setattr(backend_module, "materialize_disturbance_tape", materialize)
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(7, 64), prefix_policy=_zero_for(7, 64),
    )
    assert twins.selected_tape_index == 1
    assert twins.source_address.tape_id == "k7-early/1"
    assert twins.source_renewal_index >= 0
    assert len(twins.source_scan_receipts) == 2
    assert twins.source_scan_receipts[0].transitions == 7
    assert twins.transitions == sum(row.transitions for row in twins.source_scan_receipts)
    assert twins.policy_queries == sum(row.policy_queries for row in twins.source_scan_receipts)
    assert twins.transitions > twins.source_scan_receipts[-1].transitions


def test_eight_source_exhaustion_is_a_typed_support_diagnosis_with_complete_work(monkeypatch):
    original = backend_module.materialize_disturbance_tape
    monkeypatch.setattr(
        backend_module,
        "materialize_disturbance_tape",
        lambda address, **kwargs: original(address, **kwargs)[:1],
    )
    with pytest.raises(ReachableStatePanelNotEstablished) as observed:
        construct_reachable_twins(
            run_manifest=TEST_MANIFEST,
            state_spec=_state(7, 64),
            prefix_policy=_zero_for(7, 64),
        )
    assert len(observed.value.receipts) == 8
    assert observed.value.transitions == 56
    assert observed.value.policy_queries == 8


def test_real_frozen_foundation_adapter_enters_native_source_and_evaluation_seams():
    policy = ImmutableBatchedFoundationPolicy(
        freeze_foundation_actor(materialize_foundation(CounterRNG(1709)))
    )
    twins = construct_reachable_twins(
        run_manifest=TEST_MANIFEST, state_spec=_state(7, 64), prefix_policy=policy,
    )
    result = evaluate_twin_branches(
        twins,
        forced_actions=(10, 12),
        evaluation_address=development_tape_address("k7-early", 0),
        foundation_policy=policy,
    )
    assert policy.foundation_seed == 1709
    assert result.width == 2
    policy.actor.validate_immutable()


def test_level_release_is_persistent_state_inert_and_does_not_zero_z():
    session = NativeSession.reset(width=1, k=7, pre_event_q=1)
    prepared = backend_module._NativeState.from_buffer_copy(session.state_bytes()[0])
    prepared.z[0] = 0.1
    prepared.cached.observation[6] = 0.4
    session = NativeSession.from_state_bytes((bytes(memoryview(prepared)),))
    before = backend_module._NativeState.from_buffer_copy(session.state_bytes()[0])
    session.apply_orders(("HR",))
    after = backend_module._NativeState.from_buffer_copy(session.state_bytes()[0])
    assert tuple(after.z) == tuple(before.z)

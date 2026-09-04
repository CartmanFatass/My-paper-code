from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, replace
import importlib
from pathlib import Path
from threading import Event

import pytest

from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import (
    CARD_REVISION,
    COMPONENT,
    FIXTURE_NAMESPACE,
    HOST_ID,
    EventOrder,
    Regime,
    deterministic_fixture,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.config import (
    MAX_QUERIES,
    action_code,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.controllers import (
    free_logits,
    reversed_logits,
    set_compositor,
    strict_containment_witness,
    treatment_logits,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.host_types import (
    PublicObservation,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.lifecycle import (
    REQUIRED_CHECKPOINT_SLOTS,
    LifecycleBarrierError,
    atomic_panel_shape,
    require_all_checkpoints_before_evaluation,
    require_complete_atomic_panel_declaration,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.native_backend import (
    NATIVE_ABI_VERSION,
    SCIENCE_CARD_PATH,
    SCIENCE_CARD_SHA256,
    abi_size_identity,
    native_artifact_identity,
    require_cpp_batched_backend,
    reset_native_renewal_batch,
    science_card_identity,
    run_native_batch,
    source_sha256,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import native_backend as native_module
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.oracle import (
    recompute_endpoint,
    run_fixture,
    setup_fixture,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.preactivity import (
    PreactivityError,
    require_direction_cpp_batched_production,
)


def _assert_records_close(left, right) -> None:
    assert type(left) is type(right)
    for field in fields(left):
        lhs = getattr(left, field.name)
        rhs = getattr(right, field.name)
        if isinstance(lhs, float):
            assert lhs == pytest.approx(rhs, rel=0.0, abs=2e-12), field.name
        elif isinstance(lhs, tuple) and lhs and isinstance(lhs[0], float):
            assert lhs == pytest.approx(rhs, rel=0.0, abs=2e-12), field.name
        else:
            assert lhs == rhs, field.name


def _assert_results_close(native, oracle) -> None:
    assert native.setup.event_tokens == oracle.setup.event_tokens
    assert native.setup.mode == oracle.setup.mode
    assert native.setup.chronology_q == oracle.setup.chronology_q
    assert native.setup.hidden_d_fixture_audit == oracle.setup.hidden_d_fixture_audit
    _assert_records_close(native.setup.public, oracle.setup.public)
    assert len(native.trace) == len(oracle.trace)
    for native_tick, oracle_tick in zip(native.trace, oracle.trace):
        _assert_records_close(native_tick, oracle_tick)
    _assert_records_close(native.endpoint, oracle.endpoint)


def test_exact_isolated_identity_free_preactivity_sources_do_not_materialize_science():
    assert CARD_REVISION == "SCDMP-UAV-SP-ORDER-VALUE-SCIENCE-20260820-02"
    assert HOST_ID == "TRI-UAV-SLING-CORRIDOR-36M-v1"
    assert COMPONENT == "scdmp.uav_sp_order_value.r02.full_host"
    package = Path(
        "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value"
    )
    names = {path.name for path in package.iterdir() if path.is_file()}
    assert {
        "model.py",
        "training.py",
        "rng.py",
        "lease.py",
        "frontier.py",
        "support.py",
        "evaluation.py",
        "inference.py",
        "runner.py",
    }.issubset(names)
    assert {
        path.relative_to(package).as_posix()
        for path in package.rglob("*.json")
    } == {"empirical_source_manifest.json"}

    def scientific_materialized_paths() -> set[str]:
        source_suffixes = {".py", ".cpp", ".h", ".hpp", ".md"}
        identity_free_metadata = {"empirical_source_manifest.json"}
        observed: set[str] = set()
        for path in package.rglob("*"):
            relative = path.relative_to(package)
            if "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            if path.is_dir():
                if any(
                    marker in part.lower()
                    for part in relative.parts
                    for marker in (
                        "artifact",
                        "checkpoint",
                        "coordinate",
                        "evaluation",
                        "frontier",
                        "lease",
                        "master",
                        "result",
                        "rollout",
                        "seed",
                    )
                ):
                    observed.add(relative.as_posix() + "/")
                continue
            if relative.as_posix() in identity_free_metadata:
                continue
            if path.suffix.lower() not in source_suffixes:
                observed.add(relative.as_posix())
        return observed

    assert scientific_materialized_paths() == set()
    module_root = (
        "experiments.candidates.scdmp_variable_k."
        "uav_suspended_payload_order_value"
    )
    for module in (
        "model",
        "training",
        "rng",
        "lease",
        "frontier",
        "support",
        "evaluation",
        "inference",
        "runner",
    ):
        importlib.import_module(f"{module_root}.{module}")
    assert scientific_materialized_paths() == set()
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in package.rglob("*.*")
        if path.suffix in {".py", ".cpp"}
    )
    assert "SRF" not in source
    assert "r07" not in source


def test_nonfixture_namespace_fails_before_native_execution():
    fixture = deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_4)
    invalid = replace(fixture, namespace="production-or-coordinate")
    with pytest.raises(PermissionError, match="construction-fixture namespace"):
        run_fixture(invalid)
    with pytest.raises(PermissionError, match="construction-fixture namespace"):
        run_native_batch((invalid,))
    assert fixture.namespace == FIXTURE_NAMESPACE


def test_setup_slots_noncommute_but_public_initial_state_is_exactly_aliased():
    rg = deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_6)
    gr = replace(rg, event_order=EventOrder.GR)
    _, rg_setup = setup_fixture(rg)
    _, gr_setup = setup_fixture(gr)
    assert rg_setup.event_tokens == ("RETENSION", "CROSSWIND")
    assert gr_setup.event_tokens == ("CROSSWIND", "RETENSION")
    assert rg_setup.mode == gr_setup.mode == 1
    assert rg_setup.hidden_d_fixture_audit == 0.55
    assert gr_setup.hidden_d_fixture_audit == 0.0
    assert rg_setup.public == gr_setup.public
    assert "d" not in {field.name for field in fields(PublicObservation)}
    assert len(rg_setup.public.vector()) == 14


def test_native_setup_aliasing_and_event_noncommutation_match_fixture_oracle():
    fixtures = (
        deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_6),
        deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_6),
    )
    results = run_native_batch(fixtures)
    assert results[0].setup.public == results[1].setup.public
    assert results[0].setup.hidden_d_fixture_audit == 0.55
    assert results[1].setup.hidden_d_fixture_audit == 0.0
    for fixture, result in zip(fixtures, results):
        _assert_results_close(result, run_fixture(fixture))


@pytest.mark.parametrize(
    ("regime", "switch_tick", "expected_queries"),
    [
        (Regime.FIXED_4, 0, 105),
        (Regime.FIXED_10, 0, 42),
        (Regime.FIXED_6, 0, 70),
        (Regime.FIXED_14, 0, 30),
        (Regime.SWITCH_6_TO_14, 168, 46),
        (Regime.SWITCH_14_TO_6, 168, 54),
        (Regime.SWITCH_6_TO_14, 252, 54),
        (Regime.SWITCH_14_TO_6, 252, 46),
    ],
)
def test_native_zero_order_hold_query_and_switch_accounting(regime, switch_tick, expected_queries):
    fixture = deterministic_fixture(
        event_order=EventOrder.GR,
        regime=regime,
        switch_tick=switch_tick,
        command=(0, 0, 0),
    )
    result = run_native_batch((fixture,))[0]
    assert result.endpoint.integrated_ticks == 420
    assert result.endpoint.timeout
    assert result.endpoint.policy_queries == expected_queries
    query_ticks = [record.tick for record in result.trace if record.policy_queried]
    assert len(query_ticks) == expected_queries
    for left, right in zip(query_ticks, query_ticks[1:]):
        assert right - left == result.trace[left].k
    if regime.switched:
        switched = [record for record in result.trace if record.policy_queried and record.tick == switch_tick]
        assert len(switched) == 1
        assert switched[0].k == regime.final_k


def test_native_endpoint_and_workload_recompute_from_trace():
    fixtures = (
        deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_14, command=(2, 2, 2)),
        deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_14, command=(2, 2, 2)),
        deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_4, command=(0, 0, 0)),
    )
    for result in run_native_batch(fixtures):
        _assert_records_close(result.endpoint, recompute_endpoint(result))
        assert result.endpoint.allocated_slots == 420
        assert result.endpoint.masked_post_absorption_slots == 420 - len(result.trace)
        assert sum(record.policy_queried for record in result.trace) == result.endpoint.policy_queries
        assert not (result.endpoint.physical_failure and result.endpoint.delivery)


def test_native_preserves_nonexclusive_coincident_failure_indicators():
    base = deterministic_fixture(
        event_order=EventOrder.RG,
        regime=Regime.FIXED_4,
        command=(0, 0, 0),
    )
    actions = (
        action_code((0, 1, 2)),
        action_code((0, 0, 1)),
        action_code((1, 2, 2)),
    ) + (action_code((0, 0, 0)),) * (MAX_QUERIES - 3)
    fixture = replace(base, actions=actions)
    result = run_native_batch((fixture,))[0]
    _assert_results_close(result, run_fixture(fixture))
    assert result.endpoint.physical_failure
    assert result.endpoint.overload
    assert result.endpoint.formation
    assert not result.endpoint.delivery
    assert result.trace[-1].overload and result.trace[-1].formation


def test_free_zero_residual_exact_containment_and_strictness_witness():
    base = tuple(index / 100.0 for index in range(27))
    direct = treatment_logits(base, alpha=0.7, q=1.0)
    assert free_logits(base, alpha=0.7, q=1.0, residual=(0.0,) * 27) == direct
    witness = strict_containment_witness()
    assert witness["zero_residual_exact"] is True
    assert witness["treatment_high_minus_low"] < 0.0
    assert witness["free_high_minus_low"] > 0.0
    assert witness["strictly_outside_treatment_ordering"] is True


def test_reversed_changes_only_q_to_one_minus_q():
    base = tuple(index / 31.0 for index in range(27))
    assert reversed_logits(base, alpha=0.9, true_q=1.0) == treatment_logits(
        base, alpha=0.9, q=0.0
    )
    assert reversed_logits(base, alpha=0.9, true_q=0.0) == treatment_logits(
        base, alpha=0.9, q=1.0
    )


def test_set_compositor_is_exact_swap_invariant_and_has_no_order_field():
    public = tuple(index / 20.0 for index in range(14))
    rg = set_compositor(public, ("RETENSION", 1.0), ("CROSSWIND", 0.55))
    gr = set_compositor(public, ("CROSSWIND", 0.55), ("RETENSION", 1.0))
    assert rg == gr
    assert rg.q_set == 0.5
    assert {field.name for field in fields(rg)} == {
        "public_observation",
        "event_multiset",
        "q_set",
    }
    assert not {"position", "timestamp", "recency", "order", "trace"}.intersection(
        {field.name for field in fields(rg)}
    )


def test_lifecycle_requires_all_54_slots_before_any_evaluation():
    one_missing = tuple(REQUIRED_CHECKPOINT_SLOTS)[:-1]
    with pytest.raises(LifecycleBarrierError, match="all 54"):
        require_all_checkpoints_before_evaluation(one_missing)
    with pytest.raises(LifecycleBarrierError, match="must precede"):
        require_all_checkpoints_before_evaluation(
            REQUIRED_CHECKPOINT_SLOTS, evaluation_values_observed=True
        )
    receipt = require_all_checkpoints_before_evaluation(REQUIRED_CHECKPOINT_SLOTS)
    assert receipt.accepted_slots == receipt.required_slots == 54
    assert receipt.all_before_evaluation
    assert not receipt.evaluation_values_observed


def test_atomic_panel_shape_is_complete_and_partial_declarations_fail_closed():
    shape = atomic_panel_shape()
    assert shape["episode_count"] == 51_840
    assert shape["learned_checkpoint_count"] == 54
    assert shape["controllers"] == ("TREAT", "FREE", "REVERSED", "SET")
    assert len(shape["regimes"]) == 6
    assert shape["atomic"] is True
    assert shape["partial_inspection_permitted"] is False
    assert shape["support_panel"] == {
        "replicates": 18,
        "fixed_k": (6, 14),
        "public_states_per_k": 72,
        "histories": ("RG", "GR"),
        "actions": 27,
        "action_intervals": 139_968,
        "maximum_primitive_ticks": 1_399_680,
        "shared_disturbance_tape_within_state_k": True,
    }
    assert shape["fixed_regime_balance"]["episodes_per_order"] == 60
    assert shape["switch_regime_balance"]["episodes_per_order_time_cell"] == 30
    assert shape["claim_endpoint_families"] == ("P", "W", "T", "E", "O", "G", "F")
    assert shape["simultaneous_families"] == {
        "competence_one_sided_bounds": 15,
        "support_action_one_sided_bounds": 3,
        "direct_two_sided_intervals": 17,
    }
    assert shape["registered_workload"]["full_primitive_slot_upper_bound"] == 62_363_520
    require_complete_atomic_panel_declaration(shape)
    with pytest.raises(LifecycleBarrierError, match="partial"):
        require_complete_atomic_panel_declaration({**shape, "episode_count": 51_839})


def test_source_keyed_native_identity_is_exact_and_has_no_fallback():
    identity = native_artifact_identity()
    path = Path(str(identity["artifact_path"]))
    assert path.is_file() and path.suffix.lower() == ".dll"
    assert identity["artifact_sha256"] == __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    assert identity["source_sha256"] == source_sha256()
    assert identity["abi_version"] == NATIVE_ABI_VERSION
    assert identity["python_fallback"] is False
    assert require_cpp_batched_backend().scdmp_uav_sp_abi_version() == NATIVE_ABI_VERSION


def test_candidate_preactivity_validates_shared_receipt_and_native_identity():
    identity = native_artifact_identity()

    def valid_shared(component, *, backend, batch_width, build_root):
        assert component == COMPONENT
        assert backend == "cpp"
        assert batch_width == 7
        assert build_root is None
        return {
            "component": component,
            "backend": "cpp",
            "batch_width": batch_width,
            "full_reset_step_cpp": True,
            "python_fallback": False,
            "native": {
                "artifact": identity["artifact_path"],
                "artifact_sha256": identity["artifact_sha256"],
            },
        }

    receipt = require_direction_cpp_batched_production(
        batch_width=7, shared_guard=valid_shared
    )
    assert receipt["component"] == COMPONENT
    assert receipt["backend"] == "cpp"
    assert receipt["full_reset_step_cpp"] is True
    assert receipt["python_fallback"] is False
    assert receipt["direction_native"]["artifact_sha256"] == identity["artifact_sha256"]
    assert receipt["science_card"]["sha256"] == SCIENCE_CARD_SHA256

    def wrong_shared(*args, **kwargs):
        return {
            "component": COMPONENT,
            "backend": "cpp",
            "full_reset_step_cpp": False,
            "python_fallback": False,
            "native": {},
        }

    with pytest.raises(PreactivityError, match="full-native"):
        require_direction_cpp_batched_production(batch_width=1, shared_guard=wrong_shared)


def test_default_preactivity_path_is_registered_by_shared_policy():
    receipt = require_direction_cpp_batched_production(batch_width=1)
    assert receipt["shared"]["component"] == COMPONENT
    assert receipt["shared"]["full_reset_step_cpp"] is True
    assert receipt["shared"]["python_fallback"] is False


def test_batched_native_renewals_support_observation_conditioned_closed_loop_and_match_one_shot():
    fixtures = (
        deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_6),
        deterministic_fixture(
            event_order=EventOrder.GR,
            regime=Regime.SWITCH_14_TO_6,
            switch_tick=168,
            phase=1,
        ),
    )
    batch, surfaces = reset_native_renewal_batch(fixtures)
    histories = [[] for _ in fixtures]
    primitive_rewards = [[] for _ in fixtures]
    try:
        assert batch.batch_width == 2
        assert all(batch.active)
        while any(batch.active):
            actions = []
            for index, (active, surface) in enumerate(zip(batch.active, surfaces)):
                if not active:
                    actions.append(None)
                    continue
                # A genuine closed-loop choice from the current native public state.
                code = action_code((2, 2, 2)) if surface.public.x < 0.10 else action_code((1, 1, 1))
                histories[index].append(code)
                actions.append(code)
            surfaces = batch.advance(actions)
            for index, surface in enumerate(surfaces):
                primitive_rewards[index].extend(surface.primitive_rewards)
    finally:
        batch.close()

    assert all({action_code((2, 2, 2)), action_code((1, 1, 1))}.issubset(set(history)) for history in histories)
    for fixture, history, rewards, surface in zip(fixtures, histories, primitive_rewards, surfaces):
        materialized = replace(
            fixture,
            actions=tuple(history) + (action_code((0, 0, 0)),) * (MAX_QUERIES - len(history)),
        )
        one_shot = run_native_batch((materialized,))[0]
        assert [record.action_code for record in one_shot.trace if record.policy_queried] == history
        assert rewards == pytest.approx(
            [record.reward for record in one_shot.trace], rel=0.0, abs=2e-12
        )
        assert surface.accounting.integrated_ticks == one_shot.endpoint.integrated_ticks
        assert surface.accounting.policy_queries == one_shot.endpoint.policy_queries
        assert surface.accounting.cumulative_reward == pytest.approx(
            one_shot.endpoint.cumulative_reward, rel=0.0, abs=2e-12
        )
        assert surface.delivery == one_shot.endpoint.delivery
        assert surface.timeout == one_shot.endpoint.timeout
        assert surface.physical_failure == one_shot.endpoint.physical_failure
        assert surface.overload == one_shot.endpoint.overload
        assert surface.swing == one_shot.endpoint.swing
        assert surface.formation == one_shot.endpoint.formation


def test_controller_facing_renewal_surface_excludes_private_state_and_future_schedule():
    fixture = deterministic_fixture(
        event_order=EventOrder.RG,
        regime=Regime.SWITCH_6_TO_14,
        switch_tick=252,
    )
    batch, starts = reset_native_renewal_batch((fixture,))
    try:
        surface = starts[0]
        assert surface.event_tokens == ("RETENSION", "CROSSWIND")
        assert surface.chronology_q == 1.0
        exposed = {field.name for field in fields(surface)} | {
            field.name for field in fields(surface.public)
        }
        assert not {"d", "hidden_d", "state", "handle", "regime", "switch_tick"}.intersection(exposed)
        while batch.active[0]:
            surface = batch.advance((action_code((2, 2, 2)),))[0]
        with pytest.raises(ValueError, match="post-absorption"):
            batch.advance((action_code((0, 0, 0)),))
        repeated = batch.advance((None,))[0]
        assert repeated.terminal and repeated.realized_duration == 0
    finally:
        batch.close()


def _fresh_raw_output(fixture):
    inputs = (native_module._Input * 1)(native_module._native_input(fixture))
    outputs = (native_module._Output * 1)()
    status = require_cpp_batched_backend().scdmp_uav_sp_run_batch(inputs, 1, outputs)
    assert status == 0
    return outputs[0]


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda output: setattr(output, "event_order", 1), "metadata"),
        (lambda output: setattr(output, "regime", 3), "metadata"),
        (lambda output: setattr(output, "switch_tick", 168), "metadata"),
        (lambda output: setattr(output, "integrated_ticks", 0), "count shape"),
        (lambda output: setattr(output, "status", 9), "output status"),
    ],
)
def test_native_output_conversion_rejects_mismatched_metadata_counts_and_status(mutation, match):
    fixture = deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_6)
    output = _fresh_raw_output(fixture)
    mutation(output)
    with pytest.raises(native_module.NativeBackendError, match=match):
        native_module._result(fixture, output)


def test_native_output_conversion_consumes_and_validates_cpp_token_fields():
    fixture = deterministic_fixture(event_order=EventOrder.RG, regime=Regime.FIXED_6)
    output = _fresh_raw_output(fixture)
    assert (output.token_first, output.token_second) == (0, 1)
    output.token_first = 1
    output.token_second = 0
    with pytest.raises(native_module.NativeBackendError, match="token fields disagree"):
        native_module._result(fixture, output)


def test_native_output_conversion_rejects_invalid_terminal_trace_shape():
    fixture = deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_6)
    output = _fresh_raw_output(fixture)
    output.ticks[output.integrated_ticks - 1].terminal = 0
    with pytest.raises(native_module.NativeBackendError, match="final terminal"):
        native_module._result(fixture, output)


def test_native_abi_size_witnesses_match_every_ctypes_structure():
    identity = abi_size_identity()
    assert identity == {
        "reset_input": native_module.ctypes.sizeof(native_module._ResetInput),
        "full_input": native_module.ctypes.sizeof(native_module._Input),
        "tick": native_module.ctypes.sizeof(native_module._Tick),
        "renewal_output": native_module.ctypes.sizeof(native_module._RenewalOutput),
        "full_output": native_module.ctypes.sizeof(native_module._Output),
    }
    artifact = native_artifact_identity()
    assert artifact["abi_version"] == 2
    assert artifact["abi_sizes"] == identity


def test_native_source_identity_is_bound_to_exact_immutable_science_card(monkeypatch):
    identity = science_card_identity()
    assert Path(identity["path"]) == SCIENCE_CARD_PATH.resolve()
    assert identity["sha256"] == SCIENCE_CARD_SHA256
    assert native_artifact_identity()["science_card"] == identity
    monkeypatch.setattr(native_module, "SCIENCE_CARD_SHA256", "0" * 64)
    with pytest.raises(native_module.NativeBackendError, match="science card SHA-256"):
        science_card_identity()


def test_same_batch_advance_and_close_are_serialized_and_close_is_idempotent():
    fixture = deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_6)
    batch, _ = reset_native_renewal_batch((fixture,))
    started = Event()
    batch._lock.acquire()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                lambda: (started.set(), batch.advance((action_code((1, 1, 1)),)))[1]
            )
            assert started.wait(timeout=2.0)
            assert not future.done()
            batch._lock.release()
            transition = future.result(timeout=5.0)[0]
            batch._lock.acquire()
            assert transition.accounting.policy_queries == 1
    finally:
        batch._lock.release()

    close_started = Event()
    batch._lock.acquire()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lambda: (close_started.set(), batch.close())[1])
            assert close_started.wait(timeout=2.0)
            assert not future.done()
            batch._lock.release()
            future.result(timeout=5.0)
            batch._lock.acquire()
    finally:
        batch._lock.release()
    batch.close()
    with pytest.raises(native_module.NativeBackendError, match="closed"):
        batch.advance((action_code((1, 1, 1)),))


def test_post_native_conversion_failure_closes_and_invalidates_advanced_session(monkeypatch):
    fixture = deterministic_fixture(event_order=EventOrder.GR, regime=Regime.FIXED_6)
    batch, _ = reset_native_renewal_batch((fixture,))

    def reject_output(*args, **kwargs):
        raise native_module.NativeBackendError("synthetic output validation failure")

    monkeypatch.setattr(native_module, "_renewal_transition", reject_output)
    with pytest.raises(native_module.NativeBackendError, match="synthetic output"):
        batch.advance((action_code((1, 1, 1)),))
    assert batch._closed is True
    assert not batch._handles[0]
    batch.close()
    with pytest.raises(native_module.NativeBackendError, match="closed"):
        batch.advance((action_code((1, 1, 1)),))

from __future__ import annotations

import sys
from pathlib import Path

import pytest


CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import g_init_r01_experiment as experiment  # noqa: E402
import g_init_r01_native_backend as native  # noqa: E402
from tools.benchmarks import benchmark_risp_g_init_r01_cpp_backend as benchmark  # noqa: E402


def _token(width: int, schedule: int, lane: int, renewal: int | None, kind: str) -> int:
    return native.fixture_event_token(("WIDTH", width, "SCHEDULE", schedule, "LANE", lane, renewal, kind))


def _ensure_experiment_test_binding() -> None:
    if experiment.fixture_root() is None and experiment.coordinate_root() is None:
        experiment.configure_test_fixture_root("d" * 64)
    assert experiment.fixture_root() is not None
    assert experiment.coordinate_root() is None


def _reset_reference(schedule: int, sector: int, token: int) -> dict[str, int | bool]:
    tau, duration, _ = experiment.schedule_rows(schedule)[0]
    return {
        "status": 0, "schedule_id": schedule, "renewal": -1, "tau": tau,
        "duration": duration, "sector_before": sector, "sector_after": sector,
        "action": 0, "ack_sign": 0, "utility": 0, "terminal": False,
        "next_tau": tau, "next_duration": duration, "init_events_consumed": 1,
        "action_events_consumed": 0, "motion_events_consumed": 0,
        "ack_events_consumed": 0, "init_event_token": token,
        "action_event_token": 0, "motion_event_token": 0, "ack_event_token": 0,
    }


def _trace(width: int, schedule: int) -> tuple[tuple[dict[str, int | bool], ...], ...]:
    resets = tuple(
        native.MaterializedReset(schedule, native.fixture_draw_prefix((width, schedule, lane, "INIT_SECTOR")), _token(width, schedule, lane, None, "INIT_SECTOR"))
        for lane in range(width)
    )
    sectors = [native.python_fixture_initial_sector(item.init_prefix) for item in resets]
    trace: list[tuple[dict[str, int | bool], ...]] = []
    with native.NativeInteractiveBatch(resets) as batch:
        expected_initial = tuple(
            _reset_reference(schedule, sectors[lane], resets[lane].init_event_token)
            for lane in range(width)
        )
        assert batch.initial == expected_initial
        trace.append(batch.initial)
        rows = experiment.schedule_rows(schedule)
        for renewal, (tau, duration, terminal) in enumerate(rows):
            steps = []
            expected = []
            for lane in range(width):
                action = (lane + renewal) % 3
                motion_prefix = native.fixture_draw_prefix((width, schedule, lane, renewal, "MOTION"))
                ack_prefix = native.fixture_draw_prefix((width, schedule, lane, renewal, "ACK"))
                next_sector, ack_sign = native.python_fixture_outcome(
                    sector=sectors[lane], duration=duration, action=action,
                    motion_prefix=motion_prefix, ack_prefix=ack_prefix,
                )
                action_token = _token(width, schedule, lane, renewal, "ACTION")
                motion_token = _token(width, schedule, lane, renewal, "MOTION")
                ack_token = _token(width, schedule, lane, renewal, "ACK")
                steps.append(native.MaterializedStep(action, motion_prefix, ack_prefix, action_token, motion_token, ack_token))
                next_tau, next_duration = (192, 0) if terminal else rows[renewal + 1][:2]
                expected.append({
                    "status": 0, "schedule_id": schedule, "renewal": renewal,
                    "tau": tau, "duration": duration, "sector_before": sectors[lane],
                    "sector_after": next_sector, "action": action, "ack_sign": ack_sign,
                    "utility": duration * ack_sign, "terminal": terminal,
                    "next_tau": next_tau, "next_duration": next_duration,
                    "init_events_consumed": 1, "action_events_consumed": renewal + 1,
                    "motion_events_consumed": renewal + 1, "ack_events_consumed": renewal + 1,
                    "init_event_token": resets[lane].init_event_token,
                    "action_event_token": action_token, "motion_event_token": motion_token,
                    "ack_event_token": ack_token,
                })
            observed = batch.step(steps)
            assert observed == tuple(expected)
            trace.append(observed)
            sectors = [int(row["sector_after"]) for row in observed]
    return tuple(trace)


def test_artifact_identity_abi_sizes_and_warm_cache() -> None:
    first = native.require_cpp_batched_backend()
    second = native.require_cpp_batched_backend()
    assert first is second
    identity = native.native_artifact_identity()
    assert identity["full_reset_step_cpp"] is True
    assert identity["python_fallback"] is False
    assert identity["batch_widths"] == [1, 8, 32]
    assert identity["artifact_sha256"] and identity["build_key"]
    assert identity["runtime_abi"]["struct_sizes"] == {
        "reset_input": 160, "step_input": 64, "extended_step_input": 288,
        "transition_output": 104,
    }


def test_loader_key_invalidates_for_source_runtime_abi_and_build_root_without_source_mutation(tmp_path: Path) -> None:
    runtime = native.runtime_abi_identity()
    toolchain = native.native_toolchain_identity()
    base = native._loader_cache_key_for(source_digest="1" * 64, runtime_abi=runtime, toolchain=toolchain, build_root=tmp_path / "a")
    source_changed = native._loader_cache_key_for(source_digest="2" * 64, runtime_abi=runtime, toolchain=toolchain, build_root=tmp_path / "a")
    runtime_changed = native._loader_cache_key_for(source_digest="1" * 64, runtime_abi={**runtime, "python_cache_tag": "TEST-CHANGED"}, toolchain=toolchain, build_root=tmp_path / "a")
    root_changed = native._loader_cache_key_for(source_digest="1" * 64, runtime_abi=runtime, toolchain=toolchain, build_root=tmp_path / "b")
    assert len({base, source_changed, runtime_changed, root_changed}) == 4


@pytest.mark.parametrize("width", [1, 8, 32])
def test_exact_test_materializer_rng_identities_and_sampler_census(width: int) -> None:
    _ensure_experiment_test_binding()
    schedule = 2
    audit = experiment.SamplerAudit()
    uniform = tuple(experiment.interval_ratio(1, 3) for _ in range(3))
    sectors = []
    resets = []
    for lane in range(width):
        identity = experiment.event_identity(41, "NATIVE-TEST", schedule, lane, lane, None, "INIT_SECTOR")
        sector = experiment.exact_cat(uniform, identity, "INIT_SECTOR", audit)
        sectors.append(sector)
        resets.append(native.MaterializedReset(schedule, experiment.bit_prefix(identity, 1024), experiment._event_token(identity)))
    with native.NativeInteractiveBatch(resets) as batch:
        for renewal, (tau, duration, terminal) in enumerate(experiment.schedule_rows(schedule)):
            steps = []
            materialized = []
            for lane in range(width):
                action_identity = experiment.event_identity(41, "NATIVE-TEST", schedule, lane, lane, renewal, "ACTION")
                action = experiment.exact_cat(uniform, action_identity, "ACTION", audit)
                next_sector, sign = experiment._environment_step(
                    41, "NATIVE-TEST", schedule, lane, lane, renewal,
                    action, sectors[lane], duration, audit,
                )
                step = native.MaterializedStep(
                    action,
                    experiment.bit_prefix(experiment.event_identity(41, "NATIVE-TEST", schedule, lane, lane, renewal, "MOTION"), 1024),
                    experiment.bit_prefix(experiment.event_identity(41, "NATIVE-TEST", schedule, lane, lane, renewal, "ACK"), 1024),
                    experiment._event_token(action_identity),
                    experiment._event_token(experiment.event_identity(41, "NATIVE-TEST", schedule, lane, lane, renewal, "MOTION")),
                    experiment._event_token(experiment.event_identity(41, "NATIVE-TEST", schedule, lane, lane, renewal, "ACK")),
                )
                steps.append(step)
                materialized.append((next_sector, sign))
            outputs = batch.step(steps)
            for lane, output in enumerate(outputs):
                assert output["sector_before"] == sectors[lane]
                assert output["sector_after"] == materialized[lane][0]
                assert output["ack_sign"] == materialized[lane][1]
                assert output["tau"] == tau and output["duration"] == duration
                assert output["terminal"] is terminal
                assert output["action_event_token"] == steps[lane].action_event_token
                assert output["motion_event_token"] == steps[lane].motion_event_token
                assert output["ack_event_token"] == steps[lane].ack_event_token
            sectors = [int(row["sector_after"]) for row in outputs]
    assert audit.calls == {
        "INIT_SECTOR": width,
        "ACTION": width * 16,
        "MOTION": width * 16,
        "ACK": width * 16,
    }


@pytest.mark.parametrize("width", [1, 8, 32])
@pytest.mark.parametrize("schedule", range(5))
def test_fixture_native_python_equivalence_and_repeatability(width: int, schedule: int) -> None:
    first = _trace(width, schedule)
    second = _trace(width, schedule)
    assert first == second
    final = first[-1]
    assert all(row["terminal"] is True for row in final)
    assert all(row["action_events_consumed"] == len(experiment.schedule_rows(schedule)) for row in final)


def test_heterogeneous_cross_episode_active_lane_terminal_order_width32() -> None:
    resets = tuple(
        native.MaterializedReset(lane % 5, native.fixture_draw_prefix(("HETERO", lane, "INIT-DRAW")), native.fixture_event_token(("HETERO", lane, "INIT")))
        for lane in range(32)
    )
    renewals = [0] * 32
    terminal_at: dict[int, int] = {}
    with native.NativeInteractiveBatch(resets) as batch:
        while batch.active_lanes:
            lanes = batch.active_lanes
            steps = tuple(
                native.MaterializedStep(
                    lane % 3,
                    native.fixture_draw_prefix(("HETERO", lane, renewals[lane], "MOTION")),
                    native.fixture_draw_prefix(("HETERO", lane, renewals[lane], "ACK")),
                    native.fixture_event_token(("HETERO", lane, renewals[lane], "ACTION")),
                    native.fixture_event_token(("HETERO", lane, renewals[lane], "MOTION")),
                    native.fixture_event_token(("HETERO", lane, renewals[lane], "ACK")),
                )
                for lane in lanes
            )
            outputs = batch.step_active(lanes, steps)
            for lane, output in zip(lanes, outputs):
                renewals[lane] += 1
                if output["terminal"]:
                    terminal_at[lane] = renewals[lane]
    assert terminal_at == {lane: len(experiment.schedule_rows(lane % 5)) for lane in range(32)}


def test_two_atomic_unit_workers_preserve_trace_order_rng_and_artifact() -> None:
    from concurrent.futures import ThreadPoolExecutor
    import hashlib
    import json

    coordinates = ((8, 0), (8, 1))
    sequential = [_trace(*coordinate) for coordinate in coordinates]
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="TEST_RISP_G_R01") as pool:
        parallel = list(pool.map(lambda coordinate: _trace(*coordinate), coordinates))
    assert parallel == sequential
    hashes = [hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest() for trace in parallel]
    assert len(set(hashes)) == 2
    assert native.native_artifact_identity()["artifact_sha256"]


def test_batched_training_adapter_matches_scalar_oracle_gradients_and_checkpoint_hash() -> None:
    import hashlib
    import json
    import torch

    _ensure_experiment_test_binding()
    seed = 77
    arrays = experiment.slow_initialization(seed)
    scalar_model = experiment.TrackModel(seed, experiment.ARMS[0], slow_arrays=arrays)
    native_model = experiment.TrackModel(seed, experiment.ARMS[0], slow_arrays=arrays)
    scalar_cache = {tau: experiment._slow_bundle(scalar_model, experiment._observation(tau, duration)) for tau, duration, _ in experiment.schedule_rows(0)}
    native_cache = {tau: experiment._slow_bundle(native_model, experiment._observation(tau, duration)) for tau, duration, _ in experiment.schedule_rows(0)}
    scalar_audit = experiment.SamplerAudit(); native_audit = experiment.SamplerAudit()
    scalar_rows = {position: experiment._train_episode(scalar_model, seed, 0, position, 4, scalar_cache, scalar_audit) for position in (0, 2)}
    native_rows = experiment._train_episode_group_native(native_model, seed, 0, (0, 2), 0, native_cache, native_audit)
    scalar_task = [value for position in (0, 2) for agent in range(2) for value in scalar_rows[position][0][agent]]
    native_task = [value for position in (0, 2) for agent in range(2) for value in native_rows[position][0][agent]]
    scalar_align = [value for position in (0, 2) for agent in range(2) for value in scalar_rows[position][1][agent]]
    native_align = [value for position in (0, 2) for agent in range(2) for value in native_rows[position][1][agent]]
    assert all(torch.equal(left, right) for left, right in zip(scalar_task + scalar_align, native_task + native_align))
    assert scalar_audit.calls == native_audit.calls
    scalar_loss = -experiment._left_sum(scalar_task) / (2 * 2 * experiment.T) + experiment._left_sum(scalar_align) / len(scalar_align)
    native_loss = -experiment._left_sum(native_task) / (2 * 2 * experiment.T) + experiment._left_sum(native_align) / len(native_align)
    scalar_loss.backward(); native_loss.backward()
    assert all(torch.equal(left.grad, right.grad) for left, right in zip(scalar_model.ordered_parameters(), native_model.ordered_parameters()))
    scalar_state = experiment._new_adam_state(scalar_model); native_state = experiment._new_adam_state(native_model)
    experiment._global_clip(scalar_model); experiment._global_clip(native_model)
    experiment._adamw_step(scalar_model, scalar_state); experiment._adamw_step(native_model, native_state)
    scalar_hash = hashlib.sha256(json.dumps(experiment.state_dict_json(scalar_model), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    native_hash = hashlib.sha256(json.dumps(experiment.state_dict_json(native_model), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert scalar_hash == native_hash


def test_batched_evaluation_adapter_matches_scalar_oracle_packet_and_census() -> None:
    _ensure_experiment_test_binding()
    scalar = experiment.run_evaluation_unit(93, "UNIFORM", 2, {}, episodes=16)
    audit = experiment.SamplerAudit(); summary = experiment.EvalSummary()
    experiment._evaluate_episode_group_native(
        seed=93, schedule_id=2, episodes=tuple(range(16)), arm=None, mode="UNIFORM",
        model=None, slow_cache={}, audit=audit, summary=summary,
    )
    assert summary.result() == scalar["result"]
    assert audit.calls == scalar["sampler_audit"]["calls"]


def test_shape_dtype_range_and_lifecycle_rejections_are_fail_closed() -> None:
    with pytest.raises(ValueError, match="width"):
        native.NativeInteractiveBatch(())
    with pytest.raises(ValueError, match="width"):
        native.NativeInteractiveBatch(tuple(native.MaterializedReset(0, 0, index) for index in range(33)))
    with pytest.raises(TypeError, match="schedule_id"):
        native.NativeInteractiveBatch((native.MaterializedReset(True, 0, 0),))
    with pytest.raises(ValueError, match="init_prefix"):
        native.NativeInteractiveBatch((native.MaterializedReset(0, -1, 0),))

    reset = native.MaterializedReset(2, native.fixture_draw_prefix(("LIFECYCLE", "INIT")), _token(1, 2, 0, None, "INIT_SECTOR"))
    batch = native.NativeInteractiveBatch((reset,))
    try:
        with pytest.raises(ValueError, match="one materialized step"):
            batch.step(())
        with pytest.raises(ValueError, match="action"):
            batch.step((native.MaterializedStep(3, 1, 1, 1, 2, 3),))
        # The rejected input did not advance the native session.
        valid = native.MaterializedStep(0, native.fixture_draw_prefix(("VALID", 0, "MOTION")), native.fixture_draw_prefix(("VALID", 0, "ACK")), 1, 2, 3)
        assert batch.step((valid,))[0]["renewal"] == 0
        for renewal in range(1, len(experiment.schedule_rows(2))):
            batch.step((native.MaterializedStep(renewal % 3, native.fixture_draw_prefix(("VALID", renewal, "MOTION")), native.fixture_draw_prefix(("VALID", renewal, "ACK")), renewal, renewal + 1, renewal + 2),))
        with pytest.raises(native.NativeBackendError, match="lifecycle"):
            batch.step((valid,))
    finally:
        batch.close()
    with pytest.raises(native.NativeBackendError, match="closed"):
        batch.step((native.MaterializedStep(0, 0, 0, 0, 0, 0),))


def test_direct_cpp_malformed_step_leaves_output_and_session_unmodified() -> None:
    import ctypes

    reset = native.MaterializedReset(0, native.fixture_draw_prefix(("DIRECT", "INIT")), 99)
    batch = native.NativeInteractiveBatch((reset,))
    try:
        malformed = native._StepInput(); malformed.action = 0; malformed.prefix_bits = 512
        malformed.action_event_token = 10; malformed.motion_event_token = 11; malformed.ack_event_token = 12
        output = native._TransitionOutput()
        ctypes.memset(ctypes.byref(output), 0xA5, ctypes.sizeof(output))
        before = ctypes.string_at(ctypes.byref(output), ctypes.sizeof(output))
        status = batch._library.risp_g_init_r01_interactive_step_batch(
            batch._handles, ctypes.byref(malformed), 1, ctypes.byref(output),
        )
        after = ctypes.string_at(ctypes.byref(output), ctypes.sizeof(output))
        assert status != 0
        assert after == before
        valid = native.MaterializedStep(0, native.fixture_draw_prefix(("DIRECT", "MOTION")), native.fixture_draw_prefix(("DIRECT", "ACK")), 10, 11, 12)
        assert batch.step((valid,))[0]["renewal"] == 0
    finally:
        batch.close()


def test_direct_cpp_abi_magic_handle_duplicate_and_draw_guards() -> None:
    import ctypes

    library = native.require_cpp_batched_backend()
    bad_reset = native._ResetInput(); bad_reset.magic = 0; bad_reset.abi_version = native.NATIVE_ABI_VERSION + 1
    bad_reset.schedule_id = 0; bad_reset.prefix_bits = 1024
    handles = (ctypes.c_uint64 * 1)(777)
    outputs = (native._TransitionOutput * 1)()
    ctypes.memset(outputs, 0xA5, ctypes.sizeof(outputs))
    before = ctypes.string_at(outputs, ctypes.sizeof(outputs))
    assert library.risp_g_init_r01_interactive_reset_batch(ctypes.byref(bad_reset), 1, handles, outputs) != 0
    assert ctypes.string_at(outputs, ctypes.sizeof(outputs)) == before

    resets = (native.MaterializedReset(0, native.fixture_draw_prefix(("G0",)), 1), native.MaterializedReset(0, native.fixture_draw_prefix(("G1",)), 2))
    batch = native.NativeInteractiveBatch(resets)
    try:
        valid = native._step_input(native.MaterializedStep(0, native.fixture_draw_prefix(("GUARD", "M")), native.fixture_draw_prefix(("GUARD", "A")), 1, 2, 3))
        bad_handles = (ctypes.c_uint64 * 1)(2**63)
        one_output = (native._TransitionOutput * 1)()
        assert library.risp_g_init_r01_interactive_step_batch(bad_handles, ctypes.byref(valid), 1, one_output) != 0
        duplicate = (ctypes.c_uint64 * 2)(batch._handles[0], batch._handles[0])
        two_inputs = (native._StepInput * 2)(valid, valid)
        two_outputs = (native._TransitionOutput * 2)()
        assert library.risp_g_init_r01_interactive_step_batch(duplicate, two_inputs, 2, two_outputs) != 0
        unresolved = native._StepInput()
        unresolved.action = 0; unresolved.prefix_bits = 128
        # Prefix exactly around the 1/5 boundary is represented by the direct
        # raw draw surface and must never be silently coerced.
        unresolved.motion_prefix[:] = valid.motion_prefix[:]
        unresolved.ack_prefix[:] = (0,) * 2
        unresolved.action_event_token = 1; unresolved.motion_event_token = 2; unresolved.ack_event_token = 3
        # Zero is resolvable; malformed prefix width is the explicit draw fence.
        unresolved.prefix_bits = 1000
        one_handle = (ctypes.c_uint64 * 1)(batch._handles[0])
        assert library.risp_g_init_r01_interactive_step_batch(one_handle, ctypes.byref(unresolved), 1, one_output) != 0
    finally:
        batch.close()


def test_compact_boundary_fallback_is_whole_batch_failure_atomic() -> None:
    import ctypes

    reset = native.MaterializedReset(0, 0, 701)
    boundary_above = ((1 << 1024) // 5) + 1
    materialized = native.MaterializedStep(1, 0, boundary_above, 702, 703, 704)
    batch = native.NativeInteractiveBatch((reset,))
    try:
        compact = native._step_input(materialized)
        output = native._TransitionOutput()
        ctypes.memset(ctypes.byref(output), 0xA5, ctypes.sizeof(output))
        before = ctypes.string_at(ctypes.byref(output), ctypes.sizeof(output))
        status = batch._library.risp_g_init_r01_interactive_step_batch(
            batch._handles, ctypes.byref(compact), 1, ctypes.byref(output),
        )
        assert status == 25
        assert ctypes.string_at(ctypes.byref(output), ctypes.sizeof(output)) == before

        observed = batch.step((materialized,))[0]
        assert observed["renewal"] == 0
        assert observed["sector_after"] == 0
        assert observed["ack_sign"] == -1
        assert batch.extended_fallback_count == 1
    finally:
        batch.close()


def test_direction_preflight_cannot_substitute_local_build_for_shared_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    from envs.native import production_backend as shared

    monkeypatch.setattr(native, "native_artifact_identity", lambda *_args, **_kwargs: {"local": "accepted"})
    def reject(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise shared.ProductionBackendUnsupported("shared registry has no accepted R01 component")
    monkeypatch.setattr(shared, "require_cpp_batched_production", reject)
    with pytest.raises(shared.ProductionBackendUnsupported, match="shared registry"):
        native.production_preflight(batch_width=32)


def test_result_blind_fixture_benchmark_records_loader_artifact_and_widths() -> None:
    result = benchmark.run_benchmark(repetitions=1)
    assert result["schema"] == "RISP-G-INIT-REACH-TEST-NATIVE-BENCHMARK-V1"
    assert result["namespace"] == native.TEST_NAMESPACE
    assert isinstance(result["fixture_root"], str) and len(result["fixture_root"]) == 64
    assert result["production_identity_materialized"] is False
    assert result["python_fallback"] is False
    assert result["process_cold_load_seconds"] >= 0
    assert result["process_warm_load_seconds"] >= 0
    assert result["artifact"]["artifact_sha256"]
    assert [row["width"] for row in result["environment"]] == [1, 8, 32]
    assert all(row["transitions_per_second"] > 0 for row in result["environment"])
    assert result["fixture_oracle_chain"]["gradient_and_optimizer_step_executed"] is True
    assert result["fixture_oracle_chain"]["checkpoint_serialize_resume"]["resumed_finite"] is True
    assert result["fixture_oracle_chain"]["evaluation_decisions"] == 32
    assert result["integrated_scalar_vs_grouped_native"]["exact_task_align_gradient_adamw_checkpoint"] is True
    assert result["integrated_scalar_vs_grouped_native"]["evaluations"]["UNIFORM"]["exact_packet_result_and_census"] is True
    assert result["integrated_scalar_vs_grouped_native"]["evaluations"]["INTACT"]["exact_packet_result_and_census"] is True
    assert result["bounded_parallel_contract"]["lease_provided_production_worker_count"] == 1
    assert [row["worker_count"] for row in result["bounded_parallel_contract"]["test_only_worker_matrix"]["rows"]] == [1, 2, 4]
    assert result["bounded_parallel_contract"]["test_only_worker_matrix"]["exact_order_hash_and_census_equivalence"] is True
    assert result["bounded_parallel_contract"]["test_only_worker_matrix"]["production_parallel_admitted"] is False
    assert result["projected_complete_panel_single_worker_seconds"]["total"] > 0
    assert result["rollback_canary_malformed_action_rejected"] is True

from __future__ import annotations

import ctypes
from pathlib import Path

import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
    native_backend as native,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
    ACTIVE_CONTINUATION,
    NEW_EPOCH,
    EpisodeTape,
    FixtureSpec,
    StepInput,
    run_oracle_batch,
    run_oracle_trace,
)


def _claim_rows(pre_n: int, post_n: int, salt: int) -> tuple[tuple[int, ...], ...]:
    rows = []
    for clock in range(16):
        n = pre_n if clock < 6 else post_n
        rows.append(tuple((rank + clock + salt) % 6 for rank in range(n)))
    return tuple(rows)


def _expansion() -> EpisodeTape:
    keys = tuple(range(100, 107))
    fixture = FixtureSpec(
        initial_keys=keys,
        initial_positions=(3, 19, 34, 52, 68, 87, 103),
        after_keys=keys + (107, 108),
        after_positions=(-1,) * 7 + (-2, -2),
        event_condition=ACTIVE_CONTINUATION,
    )
    return EpisodeTape(fixture, _claim_rows(7, 9, 0), (43, 116))


def _contraction() -> EpisodeTape:
    keys = tuple(range(200, 209))
    fixture = FixtureSpec(
        initial_keys=keys,
        initial_positions=(1, 14, 28, 41, 55, 70, 84, 99, 113),
        after_keys=(200, 201, 203, 204, 206, 207, 208),
        after_positions=(-1,) * 7,
        event_condition=NEW_EPOCH,
        omega_plus=10,
        kappa_plus=3,
    )
    return EpisodeTape(fixture, _claim_rows(9, 7, 2))


def _static_eleven() -> EpisodeTape:
    keys = tuple(range(300, 311))
    fixture = FixtureSpec(
        initial_keys=keys,
        initial_positions=(2, 12, 23, 35, 46, 57, 69, 80, 91, 103, 114),
        after_keys=keys,
        after_positions=(-1,) * 11,
        event_condition=NEW_EPOCH,
        omega_plus=15,
        kappa_plus=5,
    )
    return EpisodeTape(fixture, _claim_rows(11, 11, 4))


def _perfect_service() -> EpisodeTape:
    keys = tuple(range(6))
    fixture = FixtureSpec(
        initial_keys=keys,
        initial_positions=(0, 20, 40, 60, 80, 100),
        after_keys=keys,
        after_positions=(-1,) * 6,
    )
    return EpisodeTape(fixture, tuple((0, 1, 2, 3, 4, 5) for _ in range(16)))


def _crossing() -> EpisodeTape:
    keys = tuple(range(400, 406))
    fixture = FixtureSpec(
        initial_keys=keys,
        initial_positions=(0, 1, 40, 60, 80, 100),
        after_keys=keys,
        after_positions=(-1,) * 6,
    )
    rows = [(3, 0, 2, 3, 4, 5)]
    rows.extend((0, 1, 2, 3, 4, 5) for _ in range(15))
    return EpisodeTape(fixture, tuple(rows))


def _cases(width: int) -> tuple[EpisodeTape, ...]:
    templates = (_expansion(), _contraction(), _static_eleven(), _perfect_service())
    return tuple(templates[index % len(templates)] for index in range(width))


@pytest.mark.parametrize("width", native.SUPPORTED_BATCH_WIDTHS)
def test_native_equals_handwritten_oracle_at_widths_1_8_32(width: int) -> None:
    cases = _cases(width)
    assert native.run_native_trace_batch(cases) == run_oracle_batch(cases)


def test_width_32_preserves_input_order_and_equals_scalar_and_width_8_chunks() -> None:
    cases = _cases(32)
    together = native.run_native_trace_batch(cases)
    scalar = tuple(native.run_native_trace_batch((case,))[0] for case in cases)
    chunked = tuple(
        trace
        for start in range(0, 32, 8)
        for trace in native.run_native_trace_batch(cases[start : start + 8])
    )
    assert together == scalar == chunked


def test_boundary_order_pulses_survivor_and_newcomer_state_are_exact() -> None:
    active = native.run_native_trace_batch((_expansion(),))[0]
    boundary = active[24]
    assert boundary.tick == 24
    assert boundary.claim_required
    assert boundary.roster_event
    assert not boundary.new_epoch
    assert len(boundary.positions) == 9
    newcomer_rows = [index for index, value in enumerate(boundary.newcomers) if value]
    assert [boundary.positions[index] for index in newcomer_rows] == [43, 116]
    assert [boundary.transport_keys[index] for index in newcomer_rows] == [107, 108]
    assert [boundary.previous_displacements[index] for index in newcomer_rows] == [0, 0]
    assert [boundary.current_claims[index] for index in newcomer_rows] == [-1, -1]
    assert boundary.accumulated_post_u == 0.0
    after_boundary_step = active[25]
    assert after_boundary_step.tick == 25
    assert not after_boundary_step.roster_event
    assert not after_boundary_step.new_epoch
    assert not any(after_boundary_step.newcomers)

    epoch = native.run_native_trace_batch((_contraction(),))[0][24]
    assert epoch.roster_event and epoch.new_epoch
    assert epoch.beacon_positions == (16, 36, 56, 76, 96, 116)
    assert epoch.demands == (2, 1, 1, 1, 1, 1)
    assert not any(epoch.newcomers)


def test_transport_key_tracks_physical_agent_across_crossing_churn_and_terminal() -> None:
    crossing = native.run_native_trace_batch((_crossing(),))[0]
    reset, after_first_move = crossing[0], crossing[1]
    assert reset.transport_keys[:2] == (400, 401)
    assert reset.positions[:2] == (0, 1)
    assert after_first_move.transport_keys[:2] == (401, 400)
    keyed = dict(zip(after_first_move.transport_keys, after_first_move.positions))
    displaced = dict(
        zip(after_first_move.transport_keys, after_first_move.previous_displacements)
    )
    assert keyed[400] == 3 and displaced[400] == 3
    assert keyed[401] == 0 and displaced[401] == -1

    expansion = native.run_native_trace_batch((_expansion(),))[0]
    before = set(expansion[23].transport_keys)
    boundary = expansion[24]
    terminal = expansion[-1]
    assert before == set(range(100, 107))
    assert set(boundary.transport_keys) == set(range(100, 109))
    assert set(terminal.transport_keys) == set(range(100, 109))
    assert len(set(boundary.transport_keys)) == len(boundary.transport_keys)

    public = boundary.public_observation()
    assert not hasattr(public, "transport_keys")
    assert public.positions == boundary.positions
    assert public.previous_displacements == boundary.previous_displacements


def test_terminal_tau_u_f_y_and_lifecycle_fail_closed() -> None:
    expected = run_oracle_trace(_perfect_service())
    observed = native.run_native_trace_batch((_perfect_service(),))[0]
    terminal = observed[-1]
    assert observed == expected
    assert terminal.terminal and terminal.tick == 64
    assert (terminal.tau, terminal.U, terminal.F, terminal.Y) == (0, 0.0, 0.0, 1.0)

    case = _perfect_service()
    batch = native.reset_native_batch((case.fixture,))
    for tick in range(64):
        action = StepInput(case.claims_by_clock[tick // 4]) if tick % 4 == 0 else StepInput()
        snapshots = batch.step((action,))
        if snapshots[0].event_input_required:
            batch.apply_event((native.EventInput(case.event_newcomer_positions),))
    before = batch.snapshots
    with pytest.raises(native.NativeBackendError, match="status -21"):
        batch.step((StepInput(),))
    assert batch.snapshots == before
    batch.close()
    with pytest.raises(native.NativeBackendError, match="closed"):
        batch.step((StepInput(),))
    with pytest.raises(native.NativeBackendError, match="already closed"):
        batch.close()


def test_step_batch_malformed_lane_is_atomically_prevalidated() -> None:
    case = _expansion()
    batch = native.reset_native_batch((case.fixture,) * 8)
    before = batch.snapshots
    malformed = [StepInput(case.claims_by_clock[0]) for _ in range(8)]
    malformed[3] = StepInput((0, 1, 2, 3, 4, 5, 9))
    with pytest.raises(native.NativeBackendError, match="status -23"):
        batch.step(malformed)
    assert batch.snapshots == before

    batch.step(tuple(StepInput(case.claims_by_clock[0]) for _ in range(8)))
    at_tick_one = batch.snapshots
    unexpected = [StepInput() for _ in range(8)]
    unexpected[5] = StepInput((0,))
    with pytest.raises(native.NativeBackendError, match="status -22"):
        batch.step(unexpected)
    assert batch.snapshots == at_tick_one
    batch.close()


def _advance_batch_to_event_input(
    batch: native.NativeBatch, case: EpisodeTape
) -> tuple[object, ...]:
    snapshots = batch.snapshots
    for tick in range(24):
        action = StepInput(case.claims_by_clock[tick // 4]) if tick % 4 == 0 else StepInput()
        snapshots = batch.step((action,) * batch.width)
    return snapshots


def test_event_time_positions_use_observed_preboundary_state_and_are_atomic() -> None:
    case = _expansion()
    batch = native.reset_native_batch((case.fixture,) * 8)
    pending = _advance_batch_to_event_input(batch, case)
    assert all(snapshot.tick == 24 and snapshot.event_input_required for snapshot in pending)
    assert all(len(snapshot.positions) == 7 and not snapshot.claim_required for snapshot in pending)
    with pytest.raises(RuntimeError, match="lifecycle metadata"):
        pending[0].public_observation()

    before = batch.snapshots
    occupied = pending[3].positions[0]
    malformed = [native.EventInput((43, 116)) for _ in range(8)]
    malformed[3] = native.EventInput((occupied, 116))
    with pytest.raises(native.NativeBackendError, match="status -33"):
        batch.apply_event(malformed)
    assert batch.snapshots == before

    malformed[3] = native.EventInput((43, 43))
    with pytest.raises(native.NativeBackendError, match="status -33"):
        batch.apply_event(malformed)
    assert batch.snapshots == before

    malformed[3] = native.EventInput((43,))
    with pytest.raises(native.NativeBackendError, match="status -32"):
        batch.apply_event(malformed)
    assert batch.snapshots == before

    post_event = batch.apply_event(tuple(native.EventInput((43, 116)) for _ in range(8)))
    assert all(not snapshot.event_input_required for snapshot in post_event)
    assert all(snapshot.claim_required and snapshot.roster_event for snapshot in post_event)
    assert all(len(snapshot.positions) == 9 for snapshot in post_event)
    batch.close()


def test_contraction_new_epoch_rejects_newcomer_input_then_applies_empty_event() -> None:
    case = _contraction()
    batch = native.reset_native_batch((case.fixture,))
    pending = _advance_batch_to_event_input(batch, case)
    assert pending[0].event_input_required and len(pending[0].positions) == 9
    before = batch.snapshots
    with pytest.raises(native.NativeBackendError, match="status -32"):
        batch.apply_event((native.EventInput((17,)),))
    assert batch.snapshots == before
    boundary = batch.apply_event((native.EventInput(),))[0]
    assert boundary.roster_event and boundary.new_epoch
    assert len(boundary.positions) == 7
    batch.close()


def test_reset_batch_malformed_lane_allocates_no_partial_handles() -> None:
    library = native.require_cpp_batched_backend()
    case = _expansion()
    inputs = (native._FixtureInput * 8)(
        *(native._fixture_input(case.fixture) for _ in range(8))
    )
    inputs[6].magic ^= 1
    handles = (ctypes.c_void_p * 8)()
    outputs = (native._Snapshot * 8)()
    status = library.rcle_tbcfv_reset_batch(inputs, 8, handles, outputs)
    assert status == -10
    assert all(handle is None for handle in handles)


def test_duplicate_and_invalid_transport_keys_fail_closed_without_allocating() -> None:
    library = native.require_cpp_batched_backend()
    case = _expansion()

    def rejected(mutator: object, expected: int) -> None:
        inputs = (native._FixtureInput * 8)(
            *(native._fixture_input(case.fixture) for _ in range(8))
        )
        mutator(inputs[4])  # type: ignore[operator]
        handles = (ctypes.c_void_p * 8)()
        outputs = (native._Snapshot * 8)()
        assert library.rcle_tbcfv_reset_batch(inputs, 8, handles, outputs) == expected
        assert all(handle is None for handle in handles)

    rejected(lambda item: item.initial_keys.__setitem__(1, item.initial_keys[0]), -15)
    rejected(lambda item: item.initial_keys.__setitem__(0, -2), -14)
    rejected(lambda item: item.after_keys.__setitem__(8, item.after_keys[7]), -15)
    rejected(lambda item: item.after_positions.__setitem__(7, 43), -16)

    with pytest.raises(ValueError, match="unique"):
        FixtureSpec(
            initial_keys=(1, 1, 2, 3, 4, 5),
            initial_positions=(0, 20, 40, 60, 80, 100),
            after_keys=(1, 1, 2, 3, 4, 5),
            after_positions=(-1,) * 6,
        ).validate()


def test_abi_warm_cache_source_invalidation_build_root_and_no_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = native.require_cpp_batched_backend()
    abi = native.native_abi_identity()
    assert abi == {
        "abi_version": native.NATIVE_ABI_VERSION,
        "fixture_magic": native.FIXTURE_MAGIC,
        "fixture_input_size": ctypes.sizeof(native._FixtureInput),
        "step_input_size": ctypes.sizeof(native._StepInput),
        "event_input_size": ctypes.sizeof(native._EventInput),
        "snapshot_size": ctypes.sizeof(native._Snapshot),
    }

    def forbidden_toolchain_probe() -> dict[str, object]:
        raise AssertionError("warm load re-entered toolchain discovery")

    monkeypatch.setattr(native, "native_toolchain_identity", forbidden_toolchain_probe)
    assert native.require_cpp_batched_backend() is first
    monkeypatch.undo()

    original_source = native._SOURCE
    altered_source = tmp_path / "tbcfv_backend.altered.cpp"
    altered_source.write_bytes(original_source.read_bytes() + b"\n// source invalidation fixture\n")
    original_key = native.native_build_key(build_root=tmp_path / "build")
    monkeypatch.setattr(native, "_SOURCE", altered_source)
    altered_key = native.native_build_key(build_root=tmp_path / "build")
    assert altered_key != original_key
    altered_library = native.require_cpp_batched_backend(build_root=tmp_path / "build")
    assert altered_library is not first
    assert native.native_build_key(build_root=tmp_path / "other-build") != altered_key

    missing = tmp_path / "missing.cpp"
    monkeypatch.setattr(native, "_SOURCE", missing)
    with pytest.raises(native.NativeBackendError, match="source is unavailable"):
        native.require_cpp_batched_backend(build_root=tmp_path / "missing-build")
    assert native.backend_contract()["python_fallback"] is False
    assert native.backend_contract()["shared_component_alias"] is None


def test_unsupported_widths_fail_before_native_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_load(*args: object, **kwargs: object) -> ctypes.CDLL:
        raise AssertionError("unsupported width reached native loading")

    monkeypatch.setattr(native, "require_cpp_batched_backend", forbidden_load)
    with pytest.raises(ValueError, match="supported native batch widths"):
        native.reset_native_batch((_perfect_service().fixture,) * 2)
    with pytest.raises(ValueError, match="supported native batch widths"):
        native.run_native_trace_batch(())

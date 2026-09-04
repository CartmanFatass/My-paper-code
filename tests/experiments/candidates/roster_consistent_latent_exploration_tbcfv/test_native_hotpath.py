from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_runner as runner
from experiments.candidates.roster_consistent_latent_exploration_tbcfv import native_backend
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import SCRIPTED_PACKAGES
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    make_conformance_fixture_model,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import canonical_json_bytes
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import StepInput
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.native_backend import (
    reset_native_batch,
    semantic_claims,
    semantic_claims_compact,
    semantic_uniform_words,
)


def _python_word(key: bytes, address: dict[str, object]) -> int:
    payload = canonical_json_bytes(
        {"domain": "RCLE-TBCFV-R04/semantic-uniform/v1", **address}
    )
    return int.from_bytes(hmac.new(key, payload, hashlib.sha256).digest()[:8], "big")


def test_native_semantic_words_are_exact_for_real_string_and_integer_addresses() -> None:
    rng = runner.SyntheticTestRNG()
    addresses = []
    for index in range(512):
        addresses.append(
            runner._address(
                0,
                parameter_entry=("pointer_first.weight" if index % 7 == 0 else ""),
                arm_only_variable=("FLEX-REKEY" if index % 5 == 0 else ""),
                cell=(*runner.TRAINING_CELLS, *runner.HELDOUT_CELLS)[index % 16],
                update_or_scenario=index % 800,
                physical_tick=(index % 16) * 4,
                roster_event=(index % 8 if index % 2 else "newcomer-entry"),
                physical_agent=(index % 12 if index % 3 else "COMMON"),
                draw_kind=("actor-claim" if index % 2 else "epoch-plan"),
                draw_index=index % 120,
            )
        )
    observed = semantic_uniform_words(rng._key, addresses)
    expected = tuple(_python_word(rng._key, address) for address in addresses)
    assert observed == expected
    assert rng.uniform_many(addresses) == tuple(
        (word + 0.5) / float(1 << 64) for word in expected
    )


@pytest.mark.parametrize("width", [8, 32])
def test_compiled_fixture_and_event_materializers_equal_python_oracle_all_cells(
    width: int,
) -> None:
    cells = (*runner.TRAINING_CELLS, *runner.HELDOUT_CELLS)
    coordinates = tuple(
        runner.EpisodeCoordinate(0, cells[index % len(cells)], index % 31, index % 8)
        for index in range(width)
    )
    rng = runner.SyntheticTestRNG()
    expected_fixtures = tuple(
        runner.materialize_fixture(rng, coordinate) for coordinate in coordinates
    )
    observed_fixtures = runner.materialize_fixture_batch(rng, coordinates)
    assert observed_fixtures == expected_fixtures
    batch = reset_native_batch(observed_fixtures)
    try:
        while not all(snapshot.event_input_required for snapshot in batch.snapshots):
            actions = tuple(
                StepInput(tuple(0 for _ in snapshot.positions))
                if snapshot.claim_required
                else StepInput.no_claims()
                for snapshot in batch.snapshots
            )
            batch.step(actions)
        expected_events = tuple(
            runner.materialize_event_input(rng, coordinate, snapshot, fixture)
            for coordinate, snapshot, fixture in zip(
                coordinates, batch.snapshots, expected_fixtures
            )
        )
        observed_events = runner.materialize_event_batch(
            rng, coordinates, batch, observed_fixtures
        )
        assert observed_events == expected_events
    finally:
        if not batch.closed:
            batch.close()


@pytest.mark.parametrize("width", [8, 32])
def test_lazy_native_snapshot_public_tensors_are_bitwise_scalar_equivalent(width: int) -> None:
    cells = (*runner.TRAINING_CELLS, *runner.HELDOUT_CELLS)
    coordinates = tuple(
        runner.EpisodeCoordinate(0, cells[index % 16], index, index % 8)
        for index in range(width)
    )
    rng = runner.SyntheticTestRNG()
    fixtures = runner.materialize_fixture_batch(rng, coordinates)
    batch = reset_native_batch(
        fixtures, packed_views=True, binding=rng._native_binding
    )
    try:
        lazy = runner._batched_public_tensors(batch.snapshots)
        scalar_snapshots = tuple(
            native_backend._snapshot(value) for value in batch._raw_snapshots
        )
        scalar = runner._batched_public_tensors(scalar_snapshots)
        assert lazy.counts == scalar.counts
        for field in ("agents", "agent_mask", "beacons", "contexts", "own", "candidates"):
            assert torch.equal(getattr(lazy, field), getattr(scalar, field)), field
    finally:
        if not batch.closed:
            batch.close()


def test_native_compact_claims_equal_canonical_python_and_generic_kernel() -> None:
    rng = runner.SyntheticTestRNG()
    count = 96
    cells = [(*runner.TRAINING_CELLS, *runner.HELDOUT_CELLS)[index % 16] for index in range(count)]
    updates = np.asarray([index % 23 for index in range(count)], dtype=np.int64)
    roster = np.asarray([index % 8 for index in range(count)], dtype=np.int64)
    agents = np.asarray([index % 12 for index in range(count)], dtype=np.int64)
    ticks = np.asarray([(index % 16) * 4 for index in range(count)], dtype=np.int64)
    raw = np.arange(1, count * 6 + 1, dtype=np.float64).reshape(count, 6)
    probabilities = raw / raw.sum(axis=1, keepdims=True)
    addresses = tuple(
        runner._address(
            0,
            cell=cells[index],
            update_or_scenario=int(updates[index]),
            physical_tick=int(ticks[index]),
            roster_event=int(roster[index]),
            physical_agent=int(agents[index]),
            draw_kind="actor-claim",
            draw_index=0,
        )
        for index in range(count)
    )
    generic = semantic_claims(rng._key, addresses, probabilities)
    compact = semantic_claims_compact(
        rng._key,
        0,
        np.asarray([runner._CELL_CODES[cell] for cell in cells], dtype=np.int32),
        updates,
        roster,
        agents,
        ticks,
        probabilities,
    )
    expected = []
    for address, row in zip(addresses, probabilities):
        uniform = (_python_word(rng._key, address) + 0.5) / float(1 << 64)
        cumulative = 0.0
        selected = 5
        for candidate, probability in enumerate(row):
            cumulative += float(probability)
            if uniform < cumulative:
                selected = candidate
                break
        expected.append(selected)
    assert generic == compact == tuple(expected)


def test_source_drift_creates_disjoint_bindings_without_mixed_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied_source = tmp_path / "tbcfv_backend.cpp"
    original = native_backend._SOURCE.read_bytes()
    copied_source.write_bytes(original)
    monkeypatch.setattr(native_backend, "_SOURCE", copied_source)
    build_root = tmp_path / "cache"
    first = native_backend.bind_native_backend(build_root=build_root)
    copied_source.write_bytes(original + b"\n// TEST-only source-key invalidation\n")
    second = native_backend.bind_native_backend(build_root=build_root)
    assert first.source_sha256 != second.source_sha256
    assert first.build_key != second.build_key
    assert first.library is not second.library

    coordinate = runner.EpisodeCoordinate(0, runner.TRAINING_CELLS[0], 0, 0)
    cells = np.asarray([runner._CELL_CODES[coordinate.cell]], dtype=np.int32)
    updates = np.asarray([0], dtype=np.int64)
    rows = np.asarray([0], dtype=np.int64)
    fixtures_first = native_backend.materialize_fixtures_compact(
        runner.SyntheticTestRNG()._key,
        0,
        cells,
        updates,
        rows,
        binding=first,
    )
    fixtures_second = native_backend.materialize_fixtures_compact(
        runner.SyntheticTestRNG()._key,
        0,
        cells,
        updates,
        rows,
        binding=second,
    )
    assert fixtures_first == fixtures_second
    for binding, fixtures in ((first, fixtures_first), (second, fixtures_second)):
        batch = reset_native_batch(fixtures, binding=binding)
        batch.close()


def test_production_multiworker_requires_fully_admitted_authority() -> None:
    class MinimalAuthority:
        def require_active(self, *, now: datetime) -> None:
            assert now.tzinfo is not None

    with pytest.raises(runner.EmpiricalRunnerError, match="fully admitted authority"):
        runner.execute_full_panel(
            MinimalAuthority(), now=datetime.now(timezone.utc), workers=2  # type: ignore[arg-type]
        )


def test_native_scripted_actions_equal_python_oracle_across_complete_lifecycle() -> None:
    cases = [
        tuple(runner.EpisodeCoordinate(0, cell, 0, 0) for cell in (selected,))
        for selected in runner.HELDOUT_CELLS
    ]
    cases.extend(
        [
            tuple(
                runner.EpisodeCoordinate(0, runner.HELDOUT_CELLS[row % 8], row, row % 8)
                for row in range(width)
            )
            for width in (8, 32)
        ]
    )
    for package_code, package in enumerate(SCRIPTED_PACKAGES):
        for coordinates in cases:
            rng = runner.SyntheticTestRNG()
            fixtures = tuple(
                runner.materialize_fixture(rng, coordinate) for coordinate in coordinates
            )
            batch = reset_native_batch(fixtures, binding=rng._native_binding)
            previous: list[dict[int, int]] = [dict() for _ in coordinates]
            try:
                while not all(snapshot.terminal for snapshot in batch.snapshots):
                    snapshots = batch.snapshots
                    if snapshots[0].event_input_required:
                        snapshots = batch.apply_event(
                            tuple(
                                runner.materialize_event_input(
                                    rng, coordinate, snapshot, fixture
                                )
                                for coordinate, snapshot, fixture in zip(
                                    coordinates, snapshots, fixtures
                                )
                            )
                        )
                    expected = runner._scripted_actions_python_oracle(
                        package, coordinates, snapshots, previous
                    )
                    if snapshots[0].claim_required:
                        keys = [tuple(snapshot.transport_keys) for snapshot in snapshots]
                        churn = [
                            (lambda parsed: parsed[0] != parsed[1] and parsed[2] == "ACTIVE_CONTINUATION")(
                                runner._parse_cell(coordinate.cell)
                            )
                            for coordinate in coordinates
                        ]
                        observed = batch.scripted_actions(
                            package_code,
                            [
                                tuple(previous[lane].get(key, -1) for key in lane_keys)
                                for lane, lane_keys in enumerate(keys)
                            ],
                            [
                                tuple(key in previous[lane] for key in lane_keys)
                                for lane, lane_keys in enumerate(keys)
                            ],
                            [snapshot.tick == 0 or snapshot.new_epoch for snapshot in snapshots],
                            churn,
                            [
                                ((snapshot.tick - 24) // 4 if snapshot.tick >= 24 else -1)
                                for snapshot in snapshots
                            ],
                        )
                        assert observed == expected
                        for lane, (lane_keys, action) in enumerate(zip(keys, observed)):
                            previous[lane] = dict(zip(lane_keys, action.claims))
                    else:
                        observed = tuple(StepInput.no_claims() for _ in snapshots)
                        assert observed == expected
                    batch.step(observed)
            finally:
                if not batch.closed:
                    batch.close()


@pytest.mark.parametrize("arm", runner.LEARNED_PACKAGES)
def test_b32_native_claim_path_preserves_short_update_trajectory_within_fp_boundary(
    monkeypatch: pytest.MonkeyPatch, arm: str,
) -> None:
    optimized_execute = runner.execute_learned_batch
    reference_model = make_conformance_fixture_model()
    optimized_model = make_conformance_fixture_model()
    optimized_model.load_state_dict(reference_model.state_dict())

    def scalar_groups(
        model: object,
        arm: str,
        rng: runner.SemanticRNG,
        coordinates: object,
        *,
        training: bool,
    ) -> tuple[object, ...]:
        rows = tuple(coordinates)  # type: ignore[arg-type]
        return tuple(
            episode
            for start in range(0, len(rows), 8)
            for episode in runner._execute_learned_batch_scalar_reference(
                model, arm, rng, rows[start : start + 8], training=training  # type: ignore[arg-type]
            )
        )

    monkeypatch.setattr(runner, "execute_learned_batch", scalar_groups)
    reference_rng = runner.SyntheticTestRNG()
    reference_baselines = torch.zeros(8, dtype=torch.float64)
    reference_counts = None
    for update in range(2):
        reference_baselines, reference_counts = runner.execute_training_update(
            reference_model, arm, reference_rng, update, reference_baselines
        )
    monkeypatch.setattr(runner, "execute_learned_batch", optimized_execute)
    optimized_rng = runner.SyntheticTestRNG()
    optimized_baselines = torch.zeros(8, dtype=torch.float64)
    optimized_counts = None
    for update in range(2):
        optimized_baselines, optimized_counts = runner.execute_training_update(
            optimized_model, arm, optimized_rng, update, optimized_baselines
        )
    assert optimized_counts == reference_counts
    assert torch.equal(optimized_baselines, reference_baselines)
    maximum_delta = 0.0
    for name, expected in reference_model.state_dict().items():
        observed = optimized_model.state_dict()[name]
        maximum_delta = max(maximum_delta, float((observed - expected).abs().max().item()))
        torch.testing.assert_close(observed, expected, rtol=0.0, atol=2e-18, msg=name)
    assert maximum_delta <= 2e-18

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process import continuous_roster_random_process_g34 as source
from scripts import run_runtime_capacity_continuous_roster_g32 as g32_runner


EXPECTED_COUNTS = {
    ("small_4_2_6_3", ("L", "R", "J", "T")): (4, 2, 4, 6, 3),
    ("small_4_2_6_3", ("L", "J", "R", "T")): (4, 2, 4, 6, 3),
    ("small_4_2_6_3", ("J", "L", "R", "T")): (4, 6, 4, 6, 3),
    ("train_4_3_6_5", ("L", "R", "J", "T")): (4, 3, 4, 6, 5),
    ("train_4_3_6_5", ("L", "J", "R", "T")): (4, 3, 5, 6, 5),
    ("train_4_3_6_5", ("J", "L", "R", "T")): (4, 6, 5, 6, 5),
    ("train_5_3_7_6", ("L", "R", "J", "T")): (5, 3, 5, 7, 6),
    ("train_5_3_7_6", ("L", "J", "R", "T")): (5, 3, 5, 7, 6),
    ("train_5_3_7_6", ("J", "L", "R", "T")): (5, 7, 5, 7, 6),
    ("train_6_4_8_6", ("L", "R", "J", "T")): (6, 4, 6, 8, 6),
    ("train_6_4_8_6", ("L", "J", "R", "T")): (6, 4, 6, 8, 6),
    ("train_6_4_8_6", ("J", "L", "R", "T")): (6, 8, 6, 8, 6),
    ("large_6_3_10_7", ("L", "R", "J", "T")): (6, 3, 6, 10, 7),
    ("large_6_3_10_7", ("L", "J", "R", "T")): (6, 3, 7, 10, 7),
    ("large_6_3_10_7", ("J", "L", "R", "T")): (6, 10, 7, 10, 7),
}


class RecordingPolicy:
    member_capacity = 8
    hidden_dim = 3

    def __init__(self, *, mutate_inactive_hidden: bool = False):
        self.mutate_inactive_hidden = mutate_inactive_hidden
        self.records: list[dict[str, np.ndarray]] = []

    def eval(self) -> "RecordingPolicy":
        return self

    def forward_step(
        self,
        *,
        observations: torch.Tensor,
        active_mask: torch.Tensor,
        critic_state: torch.Tensor,
        hidden: torch.Tensor,
        deterministic: bool = False,
        sampling_noise: torch.Tensor | None = None,
    ) -> SimpleNamespace:
        del deterministic, sampling_noise
        self.records.append(
            {
                "observations": observations.detach().cpu().numpy().copy(),
                "active_mask": active_mask.detach().cpu().numpy().copy(),
                "critic_state": critic_state.detach().cpu().numpy().copy(),
                "hidden": hidden.detach().cpu().numpy().copy(),
            }
        )
        next_hidden = hidden.clone()
        if self.mutate_inactive_hidden:
            next_hidden[~active_mask] = 1.0
        actions = torch.zeros(
            (*active_mask.shape, 2), dtype=observations.dtype, device=observations.device
        )
        return SimpleNamespace(actions=actions, next_hidden=next_hidden)


def test_registered_process_support_is_unique_balanced_and_exact() -> None:
    order_totals = {capacity: Counter() for capacity in source.CAPACITIES}
    profile_totals = Counter()
    for replicate in range(3):
        for capacity in source.CAPACITIES:
            rows = source.make_process_ledgers(replicate=replicate, capacity=capacity)
            assert len(rows) == 128
            assert len({row.event_times for row in rows}) == 128
            assert len({row.signature for row in rows}) == 128
            order_counts = Counter(row.event_order for row in rows)
            assert sorted(order_counts.values()) == [42, 43, 43]
            order_totals[capacity].update(order_counts)
            for row in rows:
                assert row.count_trajectory == EXPECTED_COUNTS[(row.profile.name, row.event_order)]
                assert all(5 <= value <= 43 and value % 4 for value in row.event_times)
                assert all(right - left >= 5 for left, right in zip(row.event_times, row.event_times[1:]))
            if capacity == 8:
                profile_counts = Counter(row.profile.name for row in rows)
                assert sorted(profile_counts.values()) == [42, 43, 43]
                profile_totals.update(profile_counts)
    for totals in order_totals.values():
        assert set(totals.values()) == {128}
    assert set(profile_totals.values()) == {128}


def test_constructive_random_source_closes_exact_windows_and_segments() -> None:
    rows = source.make_process_ledgers(replicate=0, capacity=12, episode_count=8)
    metrics = source.evaluate_constructive(rows)
    assert len(metrics) == 8
    for row in metrics:
        assert row["roster_sizes_valid"] is True
        assert float(row["utility"]) >= 1.0 - 2e-7
        assert float(row["minimum_step_utility"]) >= 1.0 - 2e-7
        assert float(row["minimum_event_window_utility"]) >= 1.0 - 2e-7
        assert float(row["minimum_process_segment_utility"]) >= 1.0 - 2e-7
        assert set(row["event_window_utility"]) == {"L", "R", "J", "T"}
        assert len(row["reward_trace"]) == 48
        assert len(row["roster_size_trace"]) == 48


def test_model_paths_preserve_lifecycle_and_checkpoint_state() -> None:
    g32_runner.configure_runtime(10344001)
    model = g32_runner.make_model(8)
    processes = source.make_process_ledgers(replicate=0, capacity=8, episode_count=2)
    before = g32_runner._state_digest(g32_runner._copy_state(model))
    for process_kind, intervention in (
        ("random", "none"),
        ("fixed", "none"),
        ("random", "time_rotated"),
        ("random", "reactive"),
    ):
        metrics, lifecycle_valid = source.evaluate_model(
            model,
            processes=processes,
            action_seed=source.ACTION_SEED_BASE,
            process_kind=process_kind,
            deterministic=True,
            intervention=intervention,
            device=torch.device("cpu"),
        )
        assert lifecycle_valid is True
        assert all(row["roster_sizes_valid"] is True for row in metrics)
    assert g32_runner._state_digest(g32_runner._copy_state(model)) == before


def test_interventions_change_only_the_frozen_observation_coordinates() -> None:
    processes = source.make_process_ledgers(replicate=0, capacity=8, episode_count=1)
    baseline = RecordingPolicy()
    rotated = RecordingPolicy()
    reactive = RecordingPolicy()
    source.evaluate_model(
        baseline,
        processes=processes,
        action_seed=source.ACTION_SEED_BASE,
        process_kind="random",
        deterministic=True,
    )
    source.evaluate_model(
        rotated,
        processes=processes,
        action_seed=source.ACTION_SEED_BASE,
        process_kind="random",
        deterministic=True,
        intervention="time_rotated",
    )
    source.evaluate_model(
        reactive,
        processes=processes,
        action_seed=source.ACTION_SEED_BASE,
        process_kind="random",
        deterministic=True,
        intervention="reactive",
    )
    assert len(baseline.records) == len(rotated.records) == len(reactive.records) == 48
    for time, (base, time_row, reactive_row) in enumerate(
        zip(baseline.records, rotated.records, reactive.records)
    ):
        active = base["active_mask"]
        expected_time = ((time + source.TIME_ROTATION) % 48) / 47
        np.testing.assert_allclose(
            time_row["observations"][0, active[0], 9], expected_time, atol=1e-7
        )
        assert np.count_nonzero(time_row["observations"][0, ~active[0], 9]) == 0
        np.testing.assert_allclose(time_row["critic_state"][:, 5], expected_time, atol=1e-7)
        np.testing.assert_array_equal(
            time_row["observations"][:, :, :9], base["observations"][:, :, :9]
        )
        np.testing.assert_array_equal(
            time_row["critic_state"][:, :5], base["critic_state"][:, :5]
        )
        assert np.count_nonzero(reactive_row["hidden"]) == 0
        np.testing.assert_array_equal(
            reactive_row["observations"][:, :, :6], base["observations"][:, :, :6]
        )
        np.testing.assert_array_equal(
            reactive_row["observations"][:, :, 9], base["observations"][:, :, 9]
        )
        np.testing.assert_array_equal(reactive_row["critic_state"], base["critic_state"])
        assert np.count_nonzero(reactive_row["observations"][0, active[0], 6]) == 0
        np.testing.assert_allclose(
            reactive_row["observations"][0, active[0], 7:9], 0.5, atol=0.0
        )
        assert np.count_nonzero(reactive_row["observations"][0, ~active[0], 6:9]) == 0


def test_lifecycle_validation_rejects_inactive_hidden_mutation() -> None:
    processes = source.make_process_ledgers(replicate=0, capacity=8, episode_count=1)
    _, lifecycle_valid = source.evaluate_model(
        RecordingPolicy(mutate_inactive_hidden=True),
        processes=processes,
        action_seed=source.ACTION_SEED_BASE,
        process_kind="random",
        deterministic=True,
    )
    assert lifecycle_valid is False


def test_random_and_fixed_branches_share_base_and_action_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processes = source.make_process_ledgers(replicate=1, capacity=8, episode_count=2)
    captured_noise: list[np.ndarray] = []
    original = source.g32.make_action_noise

    def capture_noise(*args: object, **kwargs: object) -> np.ndarray:
        value = original(*args, **kwargs)
        captured_noise.append(value.copy())
        return value

    monkeypatch.setattr(source.g32, "make_action_noise", capture_noise)
    random_metrics, _ = source.evaluate_model(
        RecordingPolicy(),
        processes=processes,
        action_seed=source.ACTION_SEED_BASE + 1,
        process_kind="random",
        deterministic=False,
    )
    fixed_metrics, _ = source.evaluate_model(
        RecordingPolicy(),
        processes=processes,
        action_seed=source.ACTION_SEED_BASE + 1,
        process_kind="fixed",
        deterministic=False,
    )
    assert len(captured_noise) == 2
    np.testing.assert_array_equal(captured_noise[0], captured_noise[1])
    assert [row["signature"] for row in random_metrics] == [
        row["signature"] for row in fixed_metrics
    ]
    assert all(
        source.RandomProcessRosterEnv(process).ledger is process.base
        for process in processes
    )


def test_process_contract_fails_closed_on_unregistered_time_or_order() -> None:
    row = source.make_process_ledgers(replicate=0, capacity=6, episode_count=1)[0]
    with pytest.raises(ValueError, match="event support"):
        replace(row, event_times=(4, 9, 14, 19)).validate()
    with pytest.raises(ValueError, match="event support"):
        replace(row, event_order=("R", "L", "J", "T")).validate()


def test_source_controls_freeze_zero_search_and_registered_seeds() -> None:
    controls = source.source_controls()
    assert controls["intrinsic_K_search"] == 0
    assert controls["hypothetical_transitions"] == 0
    assert controls["base_ledger_seed_base"] == 10_340_000
    assert controls["process_seed_base"] == 10_341_000
    assert controls["action_seed_base"] == 10_342_000
    assert controls["bootstrap_seed"] == 10_343_034
    assert controls["time_tuple_count"] == len(source.TIME_TUPLES)
    assert controls["fixed_event_times"] == [12, 24, 36]
    assert controls["fixed_event_process"] == ["L", "R+J", "T"]
    assert controls["hypothetical_trajectory_count"] == 0
    assert controls["nested_rollout"] is False
    assert controls["replanning"] is False
    assert np.isfinite(float(controls["time_tuple_count"]))

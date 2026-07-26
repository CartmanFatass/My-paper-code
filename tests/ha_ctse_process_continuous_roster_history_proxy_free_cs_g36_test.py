from __future__ import annotations

import numpy as np
import pytest

from ha_ctse_process import continuous_roster_history_proxy_free_cs_g36 as g36


def test_donor_bank_is_source_valid_and_complete_for_registered_counts() -> None:
    bank = g36.G36HistoryProxyDonorBank.build()
    assert bank.supported_active_counts == (2, 3, 4, 5, 6, 7, 8, 10)
    for count in bank.supported_active_counts:
        rows = bank.snapshots(count)
        assert rows.ndim == 3
        assert rows.shape[1:] == (count, 4)
        assert np.isfinite(rows).all()
        assert np.all((0.0 <= rows[:, :, 0]) & (rows[:, :, 0] <= 1.0))
        assert np.all((0.0 <= rows[:, :, 1:3]) & (rows[:, :, 1:3] <= 1.0))
        assert np.all((0.0 <= rows[:, :, 3]) & (rows[:, :, 3] <= 1.0))


def test_proxy_tape_is_history_independent_and_reused_across_modes() -> None:
    bank = g36.G36HistoryProxyDonorBank.build()
    tape = g36.G36HistoryProxyTape(bank, replicate=1, capacity=8, formal=True)
    mask = np.asarray([True, False, True, True, False, True, False, False])
    first = tape.bundle_for(episode_id=77, physical_call_position=9, active_mask=mask)
    second = tape.bundle_for(episode_id=77, physical_call_position=9, active_mask=mask)
    assert np.array_equal(first, second)
    assert np.count_nonzero(first[~mask]) == 0
    assert np.all((0.0 <= first[mask]) & (first[mask] <= 1.0))
    assert tape.target_history_read_count == 0
    with pytest.raises(ValueError, match="active count"):
        tape.bundle_for(
            episode_id=77,
            physical_call_position=9,
            active_mask=np.asarray([True, False, False, False, False, False, False, False]),
        )


def test_actor_only_transform_replaces_only_active_history_proxy_coordinates() -> None:
    observations = np.arange(2 * 4 * 10, dtype=np.float32).reshape(2, 4, 10)
    active = np.asarray([[True, False, True, False], [False, True, True, False]])
    observations[~active] = 0.0
    bundles = np.full((2, 4, 4), 0.25, dtype=np.float32)
    bundles[~active] = 0.0
    transformed, audit = g36.apply_g36_actor_history_proxy_transform(
        observations, active, bundles
    )
    assert np.array_equal(transformed[:, :, :6], observations[:, :, :6])
    assert np.array_equal(transformed[active, 6:10], bundles[active])
    assert np.array_equal(transformed[~active], observations[~active])
    assert audit == {
        "actual_age_read_count": 0,
        "actual_previous_action_read_count": 0,
        "actual_actor_time_read_count": 0,
        "critic_transform_count": 0,
    }


def test_actor_transform_does_not_read_poisoned_active_history_coordinates() -> None:
    active = np.asarray([[True, False, True]])
    first = np.zeros((1, 3, 10), dtype=np.float32)
    second = first.copy()
    first[active, 6:10] = np.asarray([np.nan, np.inf, -np.inf, np.nan])
    second[active, 6:10] = np.asarray([17.0, -9.0, 4.0, 81.0])
    bundles = np.zeros((1, 3, 4), dtype=np.float32)
    bundles[active] = 0.25

    transformed_first, audit_first = g36.apply_g36_actor_history_proxy_transform(
        first, active, bundles
    )
    transformed_second, audit_second = g36.apply_g36_actor_history_proxy_transform(
        second, active, bundles
    )

    assert np.array_equal(transformed_first, transformed_second)
    assert np.isfinite(transformed_first).all()
    assert audit_first == audit_second


def test_actor_transform_rejects_inactive_or_nonfinite_proxy_rows() -> None:
    observations = np.zeros((1, 2, 10), dtype=np.float32)
    mask = np.asarray([[True, False]])
    bad = np.zeros((1, 2, 4), dtype=np.float32)
    bad[0, 1, 0] = 0.2
    with pytest.raises(ValueError, match="inactive"):
        g36.apply_g36_actor_history_proxy_transform(observations, mask, bad)

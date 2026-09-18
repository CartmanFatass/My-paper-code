"""Exogenous event semantics: boundaries, overlap, repair and independence of the policy."""

from __future__ import annotations

import numpy as np
import pytest

from envs.uav_service_restoration.config import EventsConfig, EventTimingConfig
from envs.uav_service_restoration.events import sample_schedule, schedule_from_events
from envs.uav_service_restoration.types import EventType, NetworkEvent


def failure(site=0, start=100.0, end=None):
    return NetworkEvent(
        event_type=EventType.FULL_SITE_FAILURE,
        site_index=site,
        start_s=start,
        end_s=end,
        access_capacity_scale=0.0,
        backhaul_capacity_scale=0.0,
    )


def degradation(site=0, start=50.0, end=None, access=0.5, backhaul=1.0):
    return NetworkEvent(
        event_type=EventType.CAPACITY_DEGRADATION,
        site_index=site,
        start_s=start,
        end_s=end,
        access_capacity_scale=access,
        backhaul_capacity_scale=backhaul,
    )


def test_interval_is_half_open():
    schedule = schedule_from_events([failure(start=100.0, end=200.0)], n_sites=1)
    assert schedule.site_states(99.999)[0].radio_up
    assert not schedule.site_states(100.0)[0].radio_up
    assert not schedule.site_states(199.999)[0].radio_up
    # end_s is exclusive: the site is repaired exactly at 200.
    assert schedule.site_states(200.0)[0].radio_up


def test_pre_failure_state_is_not_discarded_at_reset():
    schedule = schedule_from_events([failure(start=120.0)], n_sites=1)
    assert schedule.site_states(0.0)[0].radio_up
    assert schedule.site_states(0.0)[0].core_link_up
    assert schedule.site_states(0.0)[0].access_capacity_scale == pytest.approx(1.0)


def test_unrepaired_failure_persists_to_the_end():
    schedule = schedule_from_events([failure(start=10.0, end=None)], n_sites=1)
    for time_s in (10.0, 500.0, 1e6):
        assert not schedule.site_states(time_s)[0].radio_up


def test_down_states_or_and_capacity_scales_take_the_minimum():
    schedule = schedule_from_events(
        [
            degradation(start=0.0, end=None, access=0.5, backhaul=0.9),
            degradation(start=0.0, end=None, access=0.8, backhaul=0.3),
        ],
        n_sites=1,
    )
    state = schedule.site_states(10.0)[0]
    assert state.access_capacity_scale == pytest.approx(0.5)
    assert state.backhaul_capacity_scale == pytest.approx(0.3)
    assert state.radio_up


def test_ending_one_event_does_not_cancel_another_still_active():
    schedule = schedule_from_events(
        [
            failure(start=100.0, end=200.0),
            degradation(start=150.0, end=400.0, access=0.25),
        ],
        n_sites=1,
    )
    # Both active.
    assert not schedule.site_states(160.0)[0].radio_up
    # The failure ended; the degradation is still in force.
    after = schedule.site_states(210.0)[0]
    assert after.radio_up
    assert after.access_capacity_scale == pytest.approx(0.25)
    # Both ended.
    assert schedule.site_states(410.0)[0].access_capacity_scale == pytest.approx(1.0)


def test_wired_backhaul_outage_leaves_the_radio_up():
    event = NetworkEvent(
        event_type=EventType.WIRED_BACKHAUL_OUTAGE, site_index=0, start_s=0.0
    )
    state = schedule_from_events([event], n_sites=1).site_states(10.0)[0]
    assert state.radio_up
    assert not state.core_link_up


def test_boundaries_within_are_strictly_interior_sorted_and_unique():
    schedule = schedule_from_events(
        [failure(start=105.0, end=115.0), degradation(start=105.0, end=None)], n_sites=1
    )
    assert schedule.boundaries_within(100.0, 120.0) == (105.0, 115.0)
    assert schedule.boundaries_within(105.0, 115.0) == ()
    assert schedule.boundaries_within(0.0, 100.0) == ()


def test_first_capability_loss_ignores_a_no_op_degradation():
    harmless = degradation(start=10.0, access=1.0, backhaul=1.0)
    real = failure(start=300.0)
    schedule = schedule_from_events([harmless, real], n_sites=1)
    assert schedule.first_capability_loss_time_s() == pytest.approx(300.0)
    assert schedule_from_events([], n_sites=1).first_capability_loss_time_s() is None


def test_summary_records_repair_status_and_source():
    schedule = schedule_from_events(
        [failure(start=10.0, end=50.0), failure(site=0, start=100.0)], n_sites=1
    )
    summary = schedule.summary()
    assert [record["repaired_within_episode"] for record in summary] == [True, False]
    assert summary[0]["end_s"] == pytest.approx(50.0)
    assert summary[1]["end_s"] is None


def test_explicit_source_uses_the_configured_values_exactly():
    config = EventsConfig(
        source_kind="explicit",
        events=(
            EventTimingConfig(
                event_type="full_site_failure",
                site_index=1,
                start_s_range=(120.0, 400.0),
                duration_s_range=(60.0, 90.0),
            ),
        ),
    )
    schedule = sample_schedule(
        config, [object(), object()], np.random.default_rng(0), episode_duration_s=600.0
    )
    assert len(schedule.events) == 1
    assert schedule.events[0].start_s == pytest.approx(120.0)
    assert schedule.events[0].end_s == pytest.approx(180.0)


def test_presampled_source_is_reproducible_from_the_seed():
    config = EventsConfig(
        source_kind="presampled",
        events=(
            EventTimingConfig(
                event_type="full_site_failure",
                site_choice=(0, 1),
                start_s_range=(60.0, 300.0),
                duration_s_range=(60.0, 200.0),
            ),
        ),
    )
    sites = [object(), object()]
    first = sample_schedule(
        config, sites, np.random.default_rng(99), episode_duration_s=900.0
    )
    again = sample_schedule(
        config, sites, np.random.default_rng(99), episode_duration_s=900.0
    )
    assert first.summary() == again.summary()
    other = sample_schedule(
        config, sites, np.random.default_rng(100), episode_duration_s=900.0
    )
    assert first.events[0].start_s != other.events[0].start_s or (
        first.events[0].site_index != other.events[0].site_index
    )


def test_a_repair_beyond_the_window_is_recorded_as_unrepaired():
    config = EventsConfig(
        source_kind="explicit",
        events=(
            EventTimingConfig(
                event_type="full_site_failure",
                site_index=0,
                start_s_range=(100.0, 100.0),
                duration_s_range=(10_000.0, 10_000.0),
            ),
        ),
    )
    schedule = sample_schedule(
        config, [object()], np.random.default_rng(0), episode_duration_s=600.0
    )
    assert schedule.events[0].end_s is None
    assert schedule.summary()[0]["repaired_within_episode"] is False


def test_no_event_source_produces_a_healthy_network():
    schedule = sample_schedule(
        EventsConfig(), [object(), object()], np.random.default_rng(0), episode_duration_s=100.0
    )
    assert schedule.events == ()
    assert all(state.radio_up for state in schedule.site_states(50.0))

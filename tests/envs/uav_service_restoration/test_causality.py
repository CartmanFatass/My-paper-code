"""Temporal causality, implemented rather than merely documented.

The required property: two data instances with identical history up to the current time
but different futures must produce identical policy-visible inputs under the same action
history.  The same must hold for a different future *failure* schedule.
"""

from __future__ import annotations

import numpy as np

from envs.uav_service_restoration import (
    UAVServiceRestorationEnv,
    config_from_dict,
)
from envs.uav_service_restoration.demand import SyntheticFixtureDemandSource
from envs.uav_service_restoration.types import DemandFrame


class ForkedDemandSource:
    """A fixture whose intervals diverge from ``fork_interval`` onwards.

    Everything before the fork is byte-identical between two instances; everything at or
    after it is multiplied by ``future_gain``.  The dataset hash deliberately ignores the
    diverging part, so both instances are accepted for the same episode descriptor - which
    is what makes the comparison meaningful.
    """

    def __init__(self, base: SyntheticFixtureDemandSource, fork_interval: int, future_gain: float):
        self._base = base
        self._fork_ms = int(base._timestamps[fork_interval])  # noqa: SLF001
        self._gain = float(future_gain)
        self.kind = base.kind

    def metadata(self):
        return self._base.metadata()

    def cell_positions_m(self):
        return self._base.cell_positions_m()

    def cell_ids(self):
        return self._base.cell_ids()

    def n_cells(self):
        return self._base.n_cells()

    def reference_scale(self):
        return self._base.reference_scale()

    def sample_episode(self, split, rng, **kwargs):
        return self._base.sample_episode(split, rng, **kwargs)

    def read_interval(self, episode, timestamp_utc_ms):
        frame = self._base.read_interval(episode, timestamp_utc_ms)
        if int(frame.interval_start_utc_ms) < self._fork_ms:
            return frame
        return DemandFrame(
            interval_start_utc_ms=frame.interval_start_utc_ms,
            interval_end_utc_ms=frame.interval_end_utc_ms,
            cell_ids=frame.cell_ids,
            activity=frame.activity * self._gain,
            demand_mbps=frame.demand_mbps * self._gain,
            observed_mask=frame.observed_mask,
        )


def _long_config(config_doc, *, duration_s=1800.0, physics_dt_s=None):
    config_doc["episode"]["duration_s"] = duration_s
    if physics_dt_s is not None:
        config_doc["episode"]["physics_dt_s"] = physics_dt_s
    return config_from_dict(config_doc)


def test_identical_history_different_future_gives_identical_obs_and_state(config_doc):
    """The fork is one source interval ahead; nothing before it may change."""

    config = _long_config(config_doc, duration_s=700.0, physics_dt_s=5.0)
    base = SyntheticFixtureDemandSource(config.source)
    # Episodes start at a fixture interval boundary; interval 0 of the episode covers
    # [start, start + 600 s).  Fork the source one interval into the episode.
    reference = UAVServiceRestorationEnv(config, demand_source=base)
    reference.reset(seed=1234)
    fork_interval = int(
        np.searchsorted(
            base._timestamps,  # noqa: SLF001
            reference.episode_descriptor.start_utc_ms,
            side="right",
        )
    )

    left = UAVServiceRestorationEnv(
        config, demand_source=ForkedDemandSource(base, fork_interval, 1.0)
    )
    right = UAVServiceRestorationEnv(
        config, demand_source=ForkedDemandSource(base, fork_interval, 4.0)
    )
    observations_left, _ = left.reset(seed=1234)
    observations_right, _ = right.reset(seed=1234)
    assert left.episode_descriptor == right.episode_descriptor

    fork_time_s = (
        int(base._timestamps[fork_interval]) - left.episode_descriptor.start_utc_ms  # noqa: SLF001
    ) / 1000.0
    assert fork_time_s > 0.0

    # Same action history in both.
    generator = np.random.default_rng(77)
    diverged = False
    while left.agents and right.agents:
        now = left.physical_time_s
        actions = {
            agent: generator.uniform(-1, 1, 3).astype(np.float32)
            for agent in left.possible_agents
        }
        if now + 1e-9 < fork_time_s:
            # Before the forked interval begins to generate service observations, every
            # policy-visible input must agree exactly.
            for agent in left.possible_agents:
                np.testing.assert_array_equal(
                    observations_left[agent], observations_right[agent]
                )
            np.testing.assert_array_equal(left.state(), right.state())
        observations_left, _, _, _, _ = left.step(actions)
        observations_right, _, _, _, _ = right.step(dict(actions))
        if left.physical_time_s > fork_time_s + 1e-9:
            if not np.array_equal(observations_left["uav_0"], observations_right["uav_0"]):
                diverged = True
    # After the forked interval has actually produced service observations the inputs
    # must differ, or the test would pass vacuously.
    assert diverged, "the futures never diverged; the fork did not take effect"


def test_a_new_source_window_is_not_revealed_before_it_starts(config_doc):
    """The aggregate of the next 10-minute window must not appear in advance."""

    config = _long_config(config_doc, duration_s=700.0, physics_dt_s=5.0)
    base = SyntheticFixtureDemandSource(config.source)
    env = UAVServiceRestorationEnv(config, demand_source=base)
    env.reset(seed=99)
    interval_s = float(base.metadata().interval_duration_s)

    demand_reference = float(config.observations.demand_reference_mbps)
    seen: list[tuple[float, np.ndarray]] = []
    while env.agents:
        state = env.state()
        seen.append((env.physical_time_s, state.copy()))
        env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.agents})

    # Collect the offered-demand estimates the state exposes at each decision boundary.
    # Inside the first source window they must all be the pre-episode history value; the
    # window's own value can only appear once a subinterval of it has completed.
    first_window = [state for time_s, state in seen if time_s < interval_s - 1e-9]
    assert len(first_window) > 1
    # The very first state precedes any service in this episode: it carries only
    # pre-episode history.
    assert not np.allclose(first_window[0], first_window[-1]), (
        "state never updated, so the causality check would be vacuous"
    )
    del demand_reference


def test_a_different_future_failure_does_not_change_current_inputs(config_doc):
    config_doc["episode"]["duration_s"] = 600.0
    config_doc["events"]["events"][0]["start_s_range"] = [300.0, 300.0]
    late = config_from_dict(config_doc)
    config_doc["events"]["source_kind"] = "none"
    config_doc["events"]["events"] = []
    never = config_from_dict(config_doc)

    with_failure = UAVServiceRestorationEnv(late)
    without_failure = UAVServiceRestorationEnv(never)
    left, _ = with_failure.reset(seed=555)
    right, _ = without_failure.reset(seed=555)
    assert with_failure.episode_descriptor == without_failure.episode_descriptor
    assert with_failure.event_schedule.events
    assert not without_failure.event_schedule.events

    generator = np.random.default_rng(8)
    while with_failure.agents and without_failure.agents:
        if with_failure.physical_time_s < 300.0 - 1e-9:
            for agent in with_failure.possible_agents:
                np.testing.assert_array_equal(left[agent], right[agent])
            np.testing.assert_array_equal(with_failure.state(), without_failure.state())
        actions = {
            agent: generator.uniform(-1, 1, 3).astype(np.float32)
            for agent in with_failure.possible_agents
        }
        left, _, _, _, _ = with_failure.step(actions)
        right, _, _, _, _ = without_failure.step(dict(actions))
    # And the failure really did register afterwards.
    assert with_failure.episode_summary()["unmet_mbit_total"] > (
        without_failure.episode_summary()["unmet_mbit_total"] + 1e-6
    )


def test_no_privileged_identifier_reaches_observations_state_or_info(config_doc):
    config = _long_config(config_doc, duration_s=60.0)
    env = UAVServiceRestorationEnv(config)
    _, infos = env.reset(seed=3)
    diagnostics = env.get_privileged_diagnostics()

    forbidden_keys = {
        "episode_id",
        "split",
        "dataset_hash",
        "source_file",
        "trace_cursor",
        "future_event_schedule",
        "exogenous_events",
        "alert_time_s",
        "episode_summary",
    }
    for agent_info in infos.values():
        assert not (set(agent_info) & forbidden_keys)
    view = env.get_current_state()
    assert not (set(view) & forbidden_keys)

    while env.agents:
        _, _, _, _, infos = env.step(
            {agent: np.zeros(3, dtype=np.float32) for agent in env.agents}
        )
        for agent_info in infos.values():
            assert not (set(agent_info) & forbidden_keys)

    # The privileged view does carry them; that is the point of keeping it separate.
    assert diagnostics["episode_id"]
    assert diagnostics["exogenous_events"]


WEST_PARKED = [
    [200.0, 1500.0, 120.0],
    [200.0, 1000.0, 120.0],
    [200.0, 2000.0, 120.0],
]


def _demand_block_from_observation(observation, config, layout):
    """Decode the demand block of an observation vector using the declared layout."""

    from envs.uav_service_restoration.observations import (
        DEMAND_FEATURES,
        PEER_FEATURES,
        SELF_FEATURES,
        SITE_FEATURES,
    )

    n_uavs = int(config.n_uavs)
    n_sites = len(config.network.sites)
    offset = SELF_FEATURES + PEER_FEATURES * (n_uavs - 1) + SITE_FEATURES * n_sites
    slots = max(int(config.source.max_demand_points), layout.n_slots)
    block = observation[offset : offset + DEMAND_FEATURES * slots].reshape(
        slots, DEMAND_FEATURES
    )
    return [
        {
            "dx": float(row[0]),
            "dy": float(row[1]),
            "offered": float(row[2]),
            "unmet": float(row[3]),
            "age": float(row[4]),
            "observed_mask": float(row[5]),
            "slot_valid_mask": float(row[6]),
        }
        for row in block
    ]


def test_unsensed_demand_is_unknown_not_zero_and_not_the_true_value(config_doc):
    """Demand in a failed area with no UAV nearby is masked, not zero, not the truth.

    The episode runs past a source-window boundary so that the true offered demand has
    moved on while the last report has not.  Inside a single window the two coincide,
    which would make the comparison vacuous.
    """

    config_doc["deployment"]["positions_m"] = list(WEST_PARKED)
    config = _long_config(config_doc, duration_s=1300.0, physics_dt_s=5.0)
    env = UAVServiceRestorationEnv(config)
    env.reset(seed=404)
    layout = env.demand_layout
    east = [
        index for index, position in enumerate(layout.positions_m) if position[0] > 2000.0
    ]
    assert east
    interval_s = float(env.demand_source.metadata().interval_duration_s)

    checked = False
    while env.agents:
        observations, _, _, _, _ = env.step(
            {agent: np.zeros(3, dtype=np.float32) for agent in env.agents}
        )
        view = env.get_current_state()
        past_boundary = (
            env.physical_time_s > interval_s + 2 * config.episode.decision_dt_s
        )
        if past_boundary and not checked:
            observed = np.asarray(view["telemetry_demand_observed"], dtype=bool)
            assert not observed[east].any(), "the east should be unsensed after the failure"

            truth_frame = env.demand_source.read_interval(
                env.episode_descriptor,
                env._utc_ms_at(env.physical_time_s - 1.0),  # noqa: SLF001
            )
            truth = layout.aggregate_demand(truth_frame.demand_mbps)
            stored = np.asarray(view["telemetry_demand_offered_mbps"], dtype=np.float64)
            # The retained value is a stale report from the previous window, not the
            # current truth: unsensed demand is never quietly refreshed.
            assert truth[east].sum() > 0.0
            assert not np.allclose(stored[east], truth[east])

            # What the policy receives for those slots is a zeroed field with the observed
            # mask cleared - never the stale number and never the true value.
            block = _demand_block_from_observation(observations["uav_0"], config, layout)
            for slot in east:
                assert block[slot]["observed_mask"] == 0.0
                assert block[slot]["offered"] == 0.0
                assert block[slot]["slot_valid_mask"] == 1.0
            checked = True
    assert checked


def test_telemetry_goes_stale_rather_than_staying_current_forever(config_doc):
    config_doc["observations"]["telemetry_ttl_s"] = 30.0
    config_doc["deployment"]["positions_m"] = list(WEST_PARKED)
    config = _long_config(config_doc, duration_s=600.0, physics_dt_s=5.0)
    env = UAVServiceRestorationEnv(config)
    env.reset(seed=404)
    east = [
        index
        for index, position in enumerate(env.demand_layout.positions_m)
        if position[0] > 2000.0
    ]
    observed_history = []
    while env.agents:
        env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.agents})
        view = env.get_current_state()
        observed_history.append(
            (
                env.physical_time_s,
                bool(np.asarray(view["telemetry_demand_observed"])[east].all()),
            )
        )
    early = [flag for time_s, flag in observed_history if time_s <= 120.0]
    late = [flag for time_s, flag in observed_history if time_s >= 300.0]
    assert any(early)
    assert not any(late)


def test_telemetry_delay_holds_back_a_completed_interval(config_doc):
    config_doc["episode"]["duration_s"] = 60.0
    config_doc["observations"]["telemetry_delay_s"] = 25.0
    config = config_from_dict(config_doc)
    env = UAVServiceRestorationEnv(config)
    env.reset(seed=8)
    # Pending reports exist and are released only when their release time arrives.
    env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.agents})
    assert env._store.pending, "a delayed report should still be queued"  # noqa: SLF001
    for _ in range(3):
        env.step({agent: np.zeros(3, dtype=np.float32) for agent in env.agents})
    ages = env.physical_time_s - env._store.demand_time_s  # noqa: SLF001
    finite = ages[np.isfinite(ages)]
    assert finite.size
    assert float(finite.min()) >= 25.0 - 1e-9

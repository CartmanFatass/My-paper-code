from __future__ import annotations

import numpy as np

from experiments.candidates.ebcr_variable_k.controls import shuffled_schedule, yoked_schedules
from experiments.candidates.ebcr_variable_k.host import generate_episode, run_episode, validate_schedule


class DummyActor:
    def probabilities(self, features: np.ndarray) -> np.ndarray:
        return np.full(features.shape[0], 0.5, dtype=np.float64)


def _episode(index: int):
    return generate_episode(
        seed=47, episode=index, namespace="control", cell="ID_OFF",
        durations=(128,), noise=0.0, joint_mismatch=False, horizon=128,
    )


def test_shuffle_preserves_nonforced_count_and_period_multiset_and_recomputes_content():
    exogenous = _episode(0)
    source = run_episode(exogenous, arm="FIXED-8", actor=DummyActor())
    schedule, eligible, reason = shuffled_schedule(source, exogenous)
    assert eligible, reason
    assert tuple(len(times) for times in schedule) == tuple(len(times) for times in source.ordinary_times)
    for role in range(2):
        replay_periods = tuple(np.diff((0, *schedule[role])).astype(int))
        assert sorted(replay_periods) == sorted(source.ordinary_periods[role])
    replay = run_episode(exogenous, arm="COORD-SHUFFLE", schedule=schedule, actor=DummyActor())
    assert replay.ordinary_times == schedule
    assert replay.physics_ticks == source.physics_ticks == 128


def test_yoke_uses_a_different_episode_in_the_same_nonforced_count_stratum():
    episodes = [_episode(0), _episode(1)]
    sources = [run_episode(row, arm="FIXED-8", actor=DummyActor()) for row in episodes]
    yokes = yoked_schedules(episodes, sources)
    for destination, (schedule, eligible, reason, donor) in enumerate(yokes):
        assert eligible, reason
        assert donor == episodes[1 - destination].episode
        assert schedule == sources[1 - destination].ordinary_times


def test_illegal_schedule_is_ineligible_instead_of_repaired():
    exogenous = _episode(0)
    eligible, reason = validate_schedule(exogenous, ((2,), (2,)))
    assert not eligible and "k_min" in reason


def test_realized_nonforced_periods_reset_at_host_local_safety_event():
    original = _episode(0)
    exogenous = type(original)(**{
        **original.__dict__, "safety_agent": 0, "safety_tick": 20,
    })
    schedule = ((8, 16, 28), (8, 16, 24))
    row = run_episode(exogenous, arm="COORD-SHUFFLE", schedule=schedule, actor=DummyActor())
    assert row.ordinary_periods[0] == (8, 8, 8)
    assert tuple(np.diff((0, *row.ordinary_times[0]))) == (8, 8, 12)

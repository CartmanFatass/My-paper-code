from __future__ import annotations

from collections import defaultdict

from .host import EpisodeResult, ExogenousEpisode, validate_schedule
from .rng import counter_permutation

Schedule = tuple[tuple[int, ...], tuple[int, ...]]


def shuffled_schedule(source: EpisodeResult, exogenous: ExogenousEpisode) -> tuple[Schedule, bool, str]:
    rows: list[tuple[int, ...]] = []
    for role, periods in enumerate(source.ordinary_periods):
        permutation = counter_permutation(
            len(periods), "schedule_replay_shuffle", exogenous.seed,
            exogenous.cell, exogenous.joint_mismatch, exogenous.episode, role,
        )
        ordered_periods = [periods[index] for index in permutation]
        ages = 0
        period_index = 0
        times: list[int] = []
        for tick in range(exogenous.horizon):
            safety = exogenous.safety_agent == role and exogenous.safety_tick == tick
            max_forced = ages >= 32 and not safety
            if safety or max_forced:
                ages = 0
            elif period_index < len(ordered_periods) and ages == ordered_periods[period_index]:
                times.append(tick)
                period_index += 1
                ages = 0
            ages += 1
        if period_index != len(ordered_periods):
            return (((), ())), False, "permuted realized periods do not fit destination horizon"
        rows.append(tuple(times))
    schedule: Schedule = (rows[0], rows[1])
    eligible, reason = validate_schedule(exogenous, schedule)
    return schedule, eligible, reason


def yoked_schedules(
    episodes: list[ExogenousEpisode], sources: list[EpisodeResult]
) -> list[tuple[Schedule | None, bool, str, int | None]]:
    if len(episodes) != len(sources):
        raise ValueError("yoke inputs must align")
    strata: dict[tuple[tuple[int, int], bool], list[int]] = defaultdict(list)
    for index, (episode, source) in enumerate(zip(episodes, sources)):
        nonforced_counts = tuple(len(times) for times in source.ordinary_times)
        strata[(nonforced_counts, episode.joint_mismatch)].append(index)
    output: list[tuple[Schedule | None, bool, str, int | None]] = [
        (None, False, "unassigned", None) for _ in episodes
    ]
    for indices in strata.values():
        if len(indices) < 2:
            for index in indices:
                output[index] = (None, False, "no different episode in renewal-count stratum", None)
            continue
        ordering = sorted(indices, key=lambda index: episodes[index].episode)
        for position, destination in enumerate(ordering):
            donor = ordering[(position + 1) % len(ordering)]
            schedule: Schedule = sources[donor].ordinary_times
            eligible, reason = validate_schedule(episodes[destination], schedule)
            output[destination] = (schedule, eligible, reason, episodes[donor].episode)
    return output

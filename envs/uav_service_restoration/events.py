"""Exogenous terrestrial-network events for ``uav_service_restoration_v0``.

Events are drawn once, at ``reset``, from an RNG stream used for nothing else.  They
never read UAV actions, delivered service, controller identity or a method label, so the
same episode identity yields the same failures for every policy.

Interval semantics is half-open ``[start_s, end_s)``.  A finite ``end_s`` *is* the
repair: capability returns to its configured value when the interval closes.  ``end_s is
None`` means the site is not repaired inside the episode.

Concurrent events combine by an explicit rule:

* down states are OR-ed - if any active event takes a capability down it is down;
* capacity scales take the minimum over active events.

Ending one event therefore cannot cancel another that is still active.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from .config import EventsConfig, EventTimingConfig, SiteConfig
from .types import EventType, NetworkEvent


@dataclass(frozen=True)
class EventSchedule:
    """The frozen exogenous event list for one episode."""

    events: tuple[NetworkEvent, ...]
    n_sites: int

    # -- capability resolution ----------------------------------------------------------

    def site_states(self, time_s: float) -> tuple[Any, ...]:
        """Resolve every site's capability at ``time_s``."""

        from .types import SiteState

        states = [SiteState() for _ in range(int(self.n_sites))]
        for event in self.events:
            if not event.active_at(time_s):
                continue
            state = states[int(event.site_index)]
            if event.event_type is EventType.FULL_SITE_FAILURE:
                state.radio_up = False
                state.core_link_up = False
                state.access_capacity_scale = 0.0
                state.backhaul_capacity_scale = 0.0
            elif event.event_type is EventType.WIRED_BACKHAUL_OUTAGE:
                state.core_link_up = False
            elif event.event_type is EventType.CAPACITY_DEGRADATION:
                state.access_capacity_scale = min(
                    state.access_capacity_scale, float(event.access_capacity_scale)
                )
                state.backhaul_capacity_scale = min(
                    state.backhaul_capacity_scale, float(event.backhaul_capacity_scale)
                )
            else:  # pragma: no cover - EventType is exhaustive
                raise ValueError(f"unhandled event type {event.event_type!r}")
        return tuple(states)

    # -- timing -------------------------------------------------------------------------

    def boundaries_within(self, start_s: float, end_s: float) -> tuple[float, ...]:
        """Event boundaries strictly inside ``(start_s, end_s)``, sorted and unique."""

        lower = float(start_s)
        upper = float(end_s)
        found: set[float] = set()
        for event in self.events:
            for boundary in event.boundaries():
                if lower < boundary < upper:
                    found.add(float(boundary))
        return tuple(sorted(found))

    def first_capability_loss_time_s(self) -> float | None:
        """Earliest time at which any capability actually degrades.

        This is what a legitimate alert can be derived from.  The full schedule stays
        out of observations.
        """

        times = [
            float(event.start_s)
            for event in self.events
            if event.event_type is not EventType.CAPACITY_DEGRADATION
            or min(event.access_capacity_scale, event.backhaul_capacity_scale) < 1.0
        ]
        return min(times) if times else None

    def summary(self) -> list[dict[str, Any]]:
        """Exogenous-event record for the evaluator.

        Never merged into observations, state or training ``info``.
        """

        records: list[dict[str, Any]] = []
        for event in self.events:
            records.append(
                {
                    "event_type": event.event_type.value,
                    "site_index": int(event.site_index),
                    "start_s": float(event.start_s),
                    "end_s": None if event.end_s is None else float(event.end_s),
                    "repaired_within_episode": event.end_s is not None,
                    "access_capacity_scale": float(event.access_capacity_scale),
                    "backhaul_capacity_scale": float(event.backhaul_capacity_scale),
                    "event_source": event.event_source,
                }
            )
        return records


def _resolve_site_index(spec: EventTimingConfig, rng: np.random.Generator) -> int:
    if spec.site_index is not None:
        return int(spec.site_index)
    choices = np.asarray(spec.site_choice, dtype=np.int64)
    return int(choices[int(rng.integers(0, choices.shape[0]))])


def sample_schedule(
    events_config: EventsConfig,
    sites: Sequence[SiteConfig],
    rng: np.random.Generator,
    *,
    episode_duration_s: float,
) -> EventSchedule:
    """Draw the episode's event list.

    ``explicit`` uses the configured midpoints exactly; ``presampled`` draws start time,
    duration and (when a choice list is given) the affected site from ``rng``.  Both are
    resolved before the first action is taken.
    """

    n_sites = len(sites)
    if events_config.source_kind == "none":
        return EventSchedule(events=(), n_sites=n_sites)

    drawn: list[NetworkEvent] = []
    for spec in events_config.events:
        if events_config.source_kind == "explicit":
            site_index = (
                int(spec.site_index)
                if spec.site_index is not None
                else int(spec.site_choice[0])
            )
            start_s = float(spec.start_s_range[0])
            duration = (
                float(spec.duration_s_range[0]) if spec.duration_s_range is not None else None
            )
        else:
            site_index = _resolve_site_index(spec, rng)
            low, high = (float(spec.start_s_range[0]), float(spec.start_s_range[1]))
            start_s = low if high <= low else float(rng.uniform(low, high))
            if spec.duration_s_range is None:
                duration = None
            else:
                dlow, dhigh = (float(spec.duration_s_range[0]), float(spec.duration_s_range[1]))
                duration = dlow if dhigh <= dlow else float(rng.uniform(dlow, dhigh))
        end_s = None if duration is None else start_s + duration
        if end_s is not None and end_s >= float(episode_duration_s):
            # A repair that would land after the episode window is not a repair inside
            # the episode; record it as unrepaired rather than silently clipping it to
            # the final instant.
            end_s = None
        drawn.append(
            NetworkEvent(
                event_type=EventType(spec.event_type),
                site_index=site_index,
                start_s=start_s,
                end_s=end_s,
                access_capacity_scale=float(spec.access_capacity_scale),
                backhaul_capacity_scale=float(spec.backhaul_capacity_scale),
                event_source=f"{events_config.source_kind}_event_source",
            )
        )
    # Stable ordering so the schedule is reproducible independently of dict iteration.
    drawn.sort(key=lambda event: (event.start_s, event.site_index, event.event_type.value))
    return EventSchedule(events=tuple(drawn), n_sites=n_sites)


def schedule_from_events(
    events: Iterable[NetworkEvent], n_sites: int
) -> EventSchedule:
    """Build a schedule directly from explicit events (used by tests and the evaluator)."""

    ordered = sorted(
        events, key=lambda event: (event.start_s, event.site_index, event.event_type.value)
    )
    return EventSchedule(events=tuple(ordered), n_sites=int(n_sites))

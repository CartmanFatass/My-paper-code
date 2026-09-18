"""Capture profiles and the producer-side eligibility gate.

Section 0.2 of the implementation plan is implemented here and nowhere else. The contract
this module enforces is:

* ``profile=off`` is the default for every existing training command. On that path a gate
  check is one attribute comparison against a string; no clock is read, no array is
  copied, no scene dictionary is built, no writer or worker is created.
* Under ``live_preview`` a sample is admitted only when **both** the completed-step gate
  and the wall-clock gate pass, for the one selected lane, with an active viewer lease and
  room in the byte budget. The step gate is checked before a clock is read, and every gate
  is checked before the caller copies anything.
* A viewer's presence is read from a pre-armed local lease value. ``env.step()`` never
  performs a socket round trip, a file scan, or an RPC to find out whether anybody is
  looking.

The gate is deliberately a plain object with no I/O so it can be unit-tested for the
"disabled path does no work" property by counting calls rather than by timing.
"""

from __future__ import annotations

import dataclasses
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

# --------------------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------------------


class Profile(str, Enum):
    """Operating profile. ``OFF`` is the default everywhere."""

    OFF = "off"
    LIVE_PREVIEW = "live_preview"
    RECORD_EVAL = "record_eval"
    REPLAY_ONLY = "replay_only"

    @property
    def captures(self) -> bool:
        """Whether the producer may extract anything at all."""

        return self in (Profile.LIVE_PREVIEW, Profile.RECORD_EVAL)


class GateVerdict(str, Enum):
    """Why a capture attempt was admitted or refused.

    The refusal reasons are counted and reported to the UI, so a quiet preview is
    visibly quiet rather than indistinguishable from a stalled producer.
    """

    ADMIT = "admit"
    PROFILE_OFF = "profile_off"
    LANE_NOT_SELECTED = "lane_not_selected"
    STEP_GATE = "step_gate"
    WALL_GATE = "wall_gate"
    NO_VIEWER = "no_viewer"
    SESSION_EXPIRED = "session_expired"
    BYTE_BUDGET = "byte_budget"
    FRAME_TOO_LARGE = "frame_too_large"
    CIRCUIT_OPEN = "circuit_open"

    @property
    def admitted(self) -> bool:
        return self is GateVerdict.ADMIT


#: Section 0.2 B verbatim: configurable engineering starting points, not measured
#: performance guarantees.
DEFAULT_PREVIEW: dict[str, Any] = {
    "lane_ids": [0],
    "min_completed_env_steps_between_frames": 100,
    "min_wall_interval_s": 1.0,
    "max_session_wall_s": 300,
    "require_active_viewer": True,
    "viewer_lease_timeout_s": 10,
    "record_trace": False,
    "max_queued_frames": 2,
    "max_frame_bytes": 524288,
    "max_output_bytes_per_wall_s": 1048576,
}


@dataclass(frozen=True)
class PreviewConfig:
    """Low-rate preview budget. Every field is an engineering target, not a measurement."""

    lane_ids: tuple[int, ...] = (0,)
    min_completed_env_steps_between_frames: int = 100
    min_wall_interval_s: float = 1.0
    max_session_wall_s: float = 300.0
    require_active_viewer: bool = True
    viewer_lease_timeout_s: float = 10.0
    record_trace: bool = False
    max_queued_frames: int = 2
    max_frame_bytes: int = 524288
    max_output_bytes_per_wall_s: int = 1048576

    def __post_init__(self) -> None:
        if not self.lane_ids:
            raise ValueError("preview.lane_ids must name at least one lane")
        if self.min_completed_env_steps_between_frames < 1:
            raise ValueError("preview.min_completed_env_steps_between_frames must be >= 1")
        if self.min_wall_interval_s < 0.0:
            raise ValueError("preview.min_wall_interval_s must be >= 0")
        if self.max_queued_frames < 1:
            raise ValueError("preview.max_queued_frames must be >= 1")
        if self.max_frame_bytes < 1024:
            raise ValueError("preview.max_frame_bytes must be at least 1 KiB")

    @classmethod
    def from_json(cls, payload: Mapping[str, Any] | None) -> "PreviewConfig":
        merged = dict(DEFAULT_PREVIEW)
        merged.update(payload or {})
        unknown = set(merged) - {f.name for f in dataclasses.fields(cls)}
        if unknown:
            raise ValueError(f"unknown preview settings: {sorted(unknown)}")
        merged["lane_ids"] = tuple(int(v) for v in merged["lane_ids"])
        merged["min_completed_env_steps_between_frames"] = int(
            merged["min_completed_env_steps_between_frames"]
        )
        merged["min_wall_interval_s"] = float(merged["min_wall_interval_s"])
        merged["max_session_wall_s"] = float(merged["max_session_wall_s"])
        merged["require_active_viewer"] = bool(merged["require_active_viewer"])
        merged["viewer_lease_timeout_s"] = float(merged["viewer_lease_timeout_s"])
        merged["record_trace"] = bool(merged["record_trace"])
        merged["max_queued_frames"] = int(merged["max_queued_frames"])
        merged["max_frame_bytes"] = int(merged["max_frame_bytes"])
        merged["max_output_bytes_per_wall_s"] = int(merged["max_output_bytes_per_wall_s"])
        return cls(**merged)

    def to_json(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["lane_ids"] = list(self.lane_ids)
        return payload


@dataclass(frozen=True)
class RecordEvalConfig:
    """Explicit evaluation recording. ``auto_start`` is never turned on by the trainer."""

    auto_start: bool = False
    default_selected_episodes: int = 1
    #: Capture every decision boundary of the selected episodes; allowed here only.
    capture_every_decision: bool = True
    #: Optional exact substep recording, off unless requested.
    capture_substeps: bool = False
    max_trace_bytes: int = 256 * 1024 * 1024
    chunk_frames: int = 64

    @classmethod
    def from_json(cls, payload: Mapping[str, Any] | None) -> "RecordEvalConfig":
        merged = {f.name: getattr(cls, f.name, f.default) for f in dataclasses.fields(cls)}
        merged.update(payload or {})
        unknown = set(merged) - {f.name for f in dataclasses.fields(cls)}
        if unknown:
            raise ValueError(f"unknown record_eval settings: {sorted(unknown)}")
        return cls(
            auto_start=bool(merged["auto_start"]),
            default_selected_episodes=int(merged["default_selected_episodes"]),
            capture_every_decision=bool(merged["capture_every_decision"]),
            capture_substeps=bool(merged["capture_substeps"]),
            max_trace_bytes=int(merged["max_trace_bytes"]),
            chunk_frames=int(merged["chunk_frames"]),
        )

    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class CaptureConfig:
    """Complete visualization configuration.

    This object lives outside scientific configuration: choosing a camera, a viewer FPS
    or a lane must not change a training contract hash or a checkpoint schema.
    """

    profile: Profile = Profile.OFF
    preview: PreviewConfig = field(default_factory=PreviewConfig)
    record_eval: RecordEvalConfig = field(default_factory=RecordEvalConfig)
    optional_event_journal_enabled: bool = False
    recent_transition_ring_enabled: bool = False
    recent_transition_ring_size: int = 16
    render_enabled: bool = False
    render_default_view: str = "2d"
    report_auto_generate: bool = False

    @classmethod
    def off(cls) -> "CaptureConfig":
        return cls()

    @classmethod
    def from_json(cls, payload: Mapping[str, Any] | None) -> "CaptureConfig":
        payload = dict(payload or {})
        known = {
            "profile",
            "preview",
            "record_eval",
            "optional_event_journal",
            "recent_transition_ring",
            "render",
            "report",
        }
        unknown = set(payload) - known
        if unknown:
            raise ValueError(
                f"unknown capture settings: {sorted(unknown)}; expected {sorted(known)}"
            )
        journal = payload.get("optional_event_journal") or {}
        ring = payload.get("recent_transition_ring") or {}
        render = payload.get("render") or {}
        report = payload.get("report") or {}
        return cls(
            profile=Profile(payload.get("profile", "off")),
            preview=PreviewConfig.from_json(payload.get("preview")),
            record_eval=RecordEvalConfig.from_json(payload.get("record_eval")),
            optional_event_journal_enabled=bool(journal.get("enabled", False)),
            recent_transition_ring_enabled=bool(ring.get("enabled", False)),
            recent_transition_ring_size=int(ring.get("size", 16)),
            render_enabled=bool(render.get("enabled", False)),
            render_default_view=str(render.get("default_view", "2d")),
            report_auto_generate=bool(report.get("auto_generate", False)),
        )

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "CaptureConfig":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_json(json.load(handle))

    def to_json(self) -> dict[str, Any]:
        return {
            "profile": self.profile.value,
            "preview": self.preview.to_json(),
            "optional_event_journal": {"enabled": self.optional_event_journal_enabled},
            "recent_transition_ring": {
                "enabled": self.recent_transition_ring_enabled,
                "size": self.recent_transition_ring_size,
            },
            "render": {"enabled": self.render_enabled, "default_view": self.render_default_view},
            "record_eval": self.record_eval.to_json(),
            "report": {"auto_generate": self.report_auto_generate},
        }


# --------------------------------------------------------------------------------------
# Viewer lease
# --------------------------------------------------------------------------------------


class ViewerLease(Protocol):
    """A pre-armed value saying until when a viewer is known to be interested.

    The producer only *reads* this. The consumer side (the local server, in its own
    thread or process) renews it when a browser polls. The read must stay cheap enough to
    sit on a gated path: an attribute load or a shared-memory double, never a syscall.
    """

    def expires_at_monotonic(self) -> float: ...


class LocalViewerLease:
    """In-process lease. Used by the single-process demo and by tests."""

    __slots__ = ("_deadline",)

    def __init__(self, deadline: float = 0.0) -> None:
        self._deadline = float(deadline)

    def expires_at_monotonic(self) -> float:
        return self._deadline

    def renew(self, timeout_s: float, *, now: float | None = None) -> None:
        self._deadline = (time.monotonic() if now is None else now) + float(timeout_s)

    def revoke(self) -> None:
        self._deadline = 0.0


class AlwaysActiveLease:
    """Lease for an explicitly armed session that does not wait for a browser.

    Used by ``record-eval`` and by the ``--no-wait-viewer`` demo mode, where the operator
    has already declared the session's bounds on the command line.
    """

    def expires_at_monotonic(self) -> float:
        return float("inf")


class SharedViewerLease:
    """Cross-process lease backed by an unlocked shared double.

    A worker process reads one ``ctypes.c_double`` from shared memory. ``time.monotonic``
    is system-wide on both Windows and Linux, so a deadline written by the parent is
    comparable in a child. A torn read can only produce a spuriously live or spuriously
    expired preview frame, which changes presentation only.
    """

    def __init__(self, raw_value: Any) -> None:
        self._raw = raw_value

    @classmethod
    def create(cls) -> "SharedViewerLease":
        from multiprocessing import sharedctypes

        return cls(sharedctypes.RawValue("d", 0.0))

    @property
    def raw(self) -> Any:
        return self._raw

    def expires_at_monotonic(self) -> float:
        return float(self._raw.value)

    def renew(self, timeout_s: float, *, now: float | None = None) -> None:
        self._raw.value = (time.monotonic() if now is None else now) + float(timeout_s)

    def revoke(self) -> None:
        self._raw.value = 0.0


# --------------------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------------------


@dataclass
class GateCounters:
    """Honest counters. ``admitted`` plus every refusal equals ``attempts``."""

    attempts: int = 0
    admitted: int = 0
    refused_profile_off: int = 0
    refused_lane: int = 0
    refused_step_gate: int = 0
    refused_wall_gate: int = 0
    refused_no_viewer: int = 0
    refused_session_expired: int = 0
    refused_byte_budget: int = 0
    refused_frame_too_large: int = 0
    refused_circuit_open: int = 0
    bytes_emitted: int = 0

    _BY_VERDICT = {
        GateVerdict.PROFILE_OFF: "refused_profile_off",
        GateVerdict.LANE_NOT_SELECTED: "refused_lane",
        GateVerdict.STEP_GATE: "refused_step_gate",
        GateVerdict.WALL_GATE: "refused_wall_gate",
        GateVerdict.NO_VIEWER: "refused_no_viewer",
        GateVerdict.SESSION_EXPIRED: "refused_session_expired",
        GateVerdict.BYTE_BUDGET: "refused_byte_budget",
        GateVerdict.FRAME_TOO_LARGE: "refused_frame_too_large",
        GateVerdict.CIRCUIT_OPEN: "refused_circuit_open",
    }

    def record(self, verdict: GateVerdict) -> None:
        self.attempts += 1
        if verdict.admitted:
            self.admitted += 1
        else:
            name = self._BY_VERDICT[verdict]
            setattr(self, name, getattr(self, name) + 1)

    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class CaptureGate:
    """Decides whether one capture attempt may build a frame.

    Call order inside a producer is always::

        if gate.admit(lane_id, completed_steps) .admitted:
            frame = build_frame(...)          # the only place arrays are copied
            gate.charge(len(frame_bytes))

    :meth:`admit` performs no allocation on the refusal paths and reads no clock until
    the completed-step gate has already passed.
    """

    __slots__ = (
        "_config",
        "_preview",
        "_lease",
        "_counters",
        "_lane_set",
        "_last_step",
        "_last_wall",
        "_session_start",
        "_bucket_bytes",
        "_bucket_time",
        "_bucket_armed",
        "_circuit_open_until",
        "_clock",
        "_capture_every",
    )

    def __init__(
        self,
        config: CaptureConfig,
        *,
        lease: ViewerLease | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config
        self._preview = config.preview
        self._lease = lease
        self._counters = GateCounters()
        self._lane_set = frozenset(int(v) for v in config.preview.lane_ids)
        self._last_step: dict[int, int] = {}
        self._last_wall: dict[int, float] = {}
        self._session_start: float | None = None
        self._bucket_bytes = 0
        self._bucket_time = 0.0
        self._bucket_armed = False
        self._circuit_open_until = 0.0
        self._clock = clock
        # record_eval captures every selected decision boundary; the low-rate gates are
        # a preview budget and do not apply to an explicitly declared recording session.
        self._capture_every = (
            config.profile is Profile.RECORD_EVAL and config.record_eval.capture_every_decision
        )

    # Properties ------------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Cheapest possible question: may this producer capture at all?"""

        return self._config.profile.captures

    @property
    def config(self) -> CaptureConfig:
        return self._config

    @property
    def profile(self) -> Profile:
        return self._config.profile

    @property
    def is_optional_display(self) -> bool:
        """True when this capture exists only for someone watching right now.

        An optional display must absorb its own defects rather than end a run. An
        explicitly requested recording is the deliverable, so its defects must surface.
        """

        return self._config.profile is Profile.LIVE_PREVIEW

    @property
    def counters(self) -> GateCounters:
        return self._counters

    @property
    def config(self) -> CaptureConfig:
        return self._config

    @property
    def max_frame_bytes(self) -> int:
        return self._preview.max_frame_bytes

    def selects_lane(self, lane_id: int) -> bool:
        return int(lane_id) in self._lane_set

    # Decision --------------------------------------------------------------------------

    def admit(self, lane_id: int, completed_steps: int, *, force_first: bool = False) -> GateVerdict:
        """Decide eligibility for one attempt.

        ``force_first`` lets the first explicitly armed sample initialise the view even
        though no step interval has elapsed yet. Subsequent initial, reset, event and
        final attempts respect the same rate and byte budgets, so arming a session cannot
        become an uncapped snapshot source.
        """

        config = self._config
        # 1. Profile. On the default path this is the only work performed, and it copies
        #    nothing, reads no clock and touches no dictionary.
        if not config.profile.captures:
            self._counters.record(GateVerdict.PROFILE_OFF)
            return GateVerdict.PROFILE_OFF

        # 2. Lane. Nonselected lanes do no new scene extraction at all.
        lane = int(lane_id)
        if not self._capture_every and lane not in self._lane_set:
            self._counters.record(GateVerdict.LANE_NOT_SELECTED)
            return GateVerdict.LANE_NOT_SELECTED

        if self._capture_every:
            # An explicit recording session still honours the circuit breaker so a broken
            # writer cannot spin, but it does not decimate the trajectory.
            if self._circuit_open_until and self._clock() < self._circuit_open_until:
                self._counters.record(GateVerdict.CIRCUIT_OPEN)
                return GateVerdict.CIRCUIT_OPEN
            self._counters.record(GateVerdict.ADMIT)
            return GateVerdict.ADMIT

        # 3. Completed-step gate, checked before any clock read.
        steps = int(completed_steps)
        last_step = self._last_step.get(lane)
        first_sample = last_step is None
        if not (first_sample and force_first):
            if last_step is not None:
                if steps - last_step < self._preview.min_completed_env_steps_between_frames:
                    self._counters.record(GateVerdict.STEP_GATE)
                    return GateVerdict.STEP_GATE
            elif steps < self._preview.min_completed_env_steps_between_frames:
                self._counters.record(GateVerdict.STEP_GATE)
                return GateVerdict.STEP_GATE

        # The step gate passed; now one clock read serves every remaining check.
        now = self._clock()

        if self._circuit_open_until and now < self._circuit_open_until:
            self._counters.record(GateVerdict.CIRCUIT_OPEN)
            return GateVerdict.CIRCUIT_OPEN

        # 4. Wall-clock gate. Both gates must pass; they are not alternative triggers.
        last_wall = self._last_wall.get(lane)
        if last_wall is not None and (now - last_wall) < self._preview.min_wall_interval_s:
            self._counters.record(GateVerdict.WALL_GATE)
            return GateVerdict.WALL_GATE

        # 5. Viewer lease. A local value comparison, never a socket or file probe.
        if self._preview.require_active_viewer:
            lease = self._lease
            if lease is None or lease.expires_at_monotonic() <= now:
                self._counters.record(GateVerdict.NO_VIEWER)
                return GateVerdict.NO_VIEWER

        # 6. Bounded session wall time.
        if self._session_start is None:
            self._session_start = now
        elif (now - self._session_start) > self._preview.max_session_wall_s:
            self._counters.record(GateVerdict.SESSION_EXPIRED)
            return GateVerdict.SESSION_EXPIRED

        # 7. Output byte budget, checked before the caller copies arrays. A refusal here
        #    means the previous second's frames already used the allowance.
        if not self._bucket_has_room(now):
            self._counters.record(GateVerdict.BYTE_BUDGET)
            return GateVerdict.BYTE_BUDGET

        self._last_step[lane] = steps
        self._last_wall[lane] = now
        self._counters.record(GateVerdict.ADMIT)
        return GateVerdict.ADMIT

    def charge(self, n_bytes: int) -> GateVerdict:
        """Account an emitted frame. Returns ``FRAME_TOO_LARGE`` if it exceeded the cap.

        An oversized frame is refused and counted; the caller reports it or emits a
        conservatively aggregated frame with explicit provenance rather than silently
        omitting unserved entities.
        """

        size = int(n_bytes)
        if size > self._preview.max_frame_bytes and not self._capture_every:
            # This reverses an admission already counted by `record()`: without the
            # decrement, `admitted` plus the refusals exceeded `attempts` and the counter
            # identity the summary reconciles against was false for every oversized frame.
            if self._counters.admitted > 0:
                self._counters.admitted -= 1
            self._counters.refused_frame_too_large += 1
            return GateVerdict.FRAME_TOO_LARGE
        self._bucket_bytes += size
        self._counters.bytes_emitted += size
        return GateVerdict.ADMIT

    def open_circuit(self, seconds: float) -> None:
        """Suspend optional presentation after repeated transport or latency failures.

        This changes presentation only. It never restarts training, never changes the
        scientific path and never auto-resumes anything beyond the preview itself.
        """

        self._circuit_open_until = self._clock() + float(seconds)

    def release_viewer(self) -> None:
        """Forget the rate state so a reconnecting viewer gets a frame promptly."""

        self._last_step.clear()
        self._last_wall.clear()

    def _bucket_has_room(self, now: float) -> bool:
        if not self._bucket_armed:
            self._bucket_armed = True
            self._bucket_time = now
            return True
        if (now - self._bucket_time) >= 1.0:
            self._bucket_time = now
            self._bucket_bytes = 0
            return True
        return self._bucket_bytes < self._preview.max_output_bytes_per_wall_s

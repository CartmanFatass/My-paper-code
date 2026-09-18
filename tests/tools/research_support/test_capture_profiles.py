"""Efficiency-contract tests for ``tools/research_support/capture/profiles.py``.

Section 0.2 of the plan is a *cost* contract, so these tests count work rather than time
it. The clock is injected, and the disabled paths are driven with a clock callable that
raises if it is read at all: the assertion is then "no clock was read", not "it was fast".

Decision order under test (``CaptureGate.admit``):

    profile -> lane -> completed-step gate -> [one clock read] -> circuit -> wall gate
    -> viewer lease -> session wall time -> byte budget -> admit

Everything before the bracket must happen without reading a clock, and the path that
reaches the wall gate must read the clock exactly once.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from tools.research_support.capture.profiles import (  # noqa: E402
    DEFAULT_PREVIEW,
    AlwaysActiveLease,
    CaptureConfig,
    CaptureGate,
    GateCounters,
    GateVerdict,
    LocalViewerLease,
    PreviewConfig,
    Profile,
    RecordEvalConfig,
    SharedViewerLease,
)

#: A realistic clock origin. ``time.monotonic()`` is never 0.0 on a running system, and the
#: byte-budget bucket uses 0.0 as its "unarmed" sentinel, so tests must not start there.
_T0 = 1000.0


class _CountingClock:
    """Injected monotonic clock that records how often the gate read it."""

    def __init__(self, now: float = _T0) -> None:
        self.now = float(now)
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)


class _ExplodingClock:
    """Clock that fails the test if the gate reads it at all."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        raise AssertionError("the gate read a clock on a path that must read none")


def _preview_config(profile: Profile = Profile.LIVE_PREVIEW, **preview: object) -> CaptureConfig:
    return CaptureConfig(profile=profile, preview=PreviewConfig(**preview))  # type: ignore[arg-type]


# --------------------------------------------------------------------------------------
# Published defaults
# --------------------------------------------------------------------------------------


def test_default_preview_numbers_are_the_published_ones() -> None:
    """A silent change to the shipped preview budget must fail here."""

    assert DEFAULT_PREVIEW == {
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


def test_preview_config_defaults_match_the_published_numbers() -> None:
    config = PreviewConfig()
    assert config.lane_ids == (0,)
    assert config.min_completed_env_steps_between_frames == 100
    assert config.min_wall_interval_s == 1.0
    assert config.max_session_wall_s == 300.0
    assert config.require_active_viewer is True
    assert config.viewer_lease_timeout_s == 10.0
    assert config.record_trace is False
    assert config.max_queued_frames == 2
    assert config.max_frame_bytes == 524288
    assert config.max_output_bytes_per_wall_s == 1048576
    assert PreviewConfig.from_json(None) == config
    assert PreviewConfig.from_json({}) == config


def test_profile_off_is_the_default_capture_configuration() -> None:
    assert CaptureConfig().profile is Profile.OFF
    assert CaptureConfig.off().profile is Profile.OFF
    assert Profile.OFF.captures is False
    assert Profile.REPLAY_ONLY.captures is False
    assert Profile.LIVE_PREVIEW.captures is True
    assert Profile.RECORD_EVAL.captures is True
    assert RecordEvalConfig().auto_start is False


def test_gate_verdict_reason_constants() -> None:
    assert GateVerdict.ADMIT.value == "admit"
    assert GateVerdict.PROFILE_OFF.value == "profile_off"
    assert GateVerdict.LANE_NOT_SELECTED.value == "lane_not_selected"
    assert GateVerdict.STEP_GATE.value == "step_gate"
    assert GateVerdict.WALL_GATE.value == "wall_gate"
    assert GateVerdict.NO_VIEWER.value == "no_viewer"
    assert GateVerdict.SESSION_EXPIRED.value == "session_expired"
    assert GateVerdict.BYTE_BUDGET.value == "byte_budget"
    assert GateVerdict.FRAME_TOO_LARGE.value == "frame_too_large"
    assert GateVerdict.CIRCUIT_OPEN.value == "circuit_open"
    assert GateVerdict.ADMIT.admitted is True
    assert all(v.admitted is False for v in GateVerdict if v is not GateVerdict.ADMIT)


# --------------------------------------------------------------------------------------
# Decision order: the work that must not happen
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("profile", [Profile.OFF, Profile.REPLAY_ONLY])
def test_profile_off_short_circuits_and_reads_no_clock(profile: Profile) -> None:
    clock = _ExplodingClock()
    gate = CaptureGate(CaptureConfig(profile=profile), lease=AlwaysActiveLease(), clock=clock)

    assert gate.enabled is False
    verdict = gate.admit(lane_id=0, completed_steps=10_000)

    assert verdict is GateVerdict.PROFILE_OFF
    assert clock.calls == 0, "the disabled path must not read a clock"
    assert gate.counters.attempts == 1
    assert gate.counters.refused_profile_off == 1
    assert gate.counters.admitted == 0


def test_unselected_lane_is_refused_before_the_clock_is_read() -> None:
    clock = _ExplodingClock()
    gate = CaptureGate(
        _preview_config(lane_ids=(0,)), lease=AlwaysActiveLease(), clock=clock
    )

    assert gate.selects_lane(0) is True
    assert gate.selects_lane(3) is False
    assert gate.admit(lane_id=3, completed_steps=10_000) is GateVerdict.LANE_NOT_SELECTED
    assert clock.calls == 0
    assert gate.counters.refused_lane == 1


def test_step_gate_is_evaluated_before_any_clock_read() -> None:
    clock = _ExplodingClock()
    gate = CaptureGate(
        _preview_config(min_completed_env_steps_between_frames=100),
        lease=AlwaysActiveLease(),
        clock=clock,
    )

    assert gate.admit(lane_id=0, completed_steps=99) is GateVerdict.STEP_GATE
    assert clock.calls == 0
    assert gate.counters.refused_step_gate == 1


def test_step_gate_refusal_after_an_admitted_frame_reads_no_extra_clock() -> None:
    clock = _CountingClock()
    gate = CaptureGate(
        _preview_config(min_completed_env_steps_between_frames=100),
        lease=AlwaysActiveLease(),
        clock=clock,
    )

    assert gate.admit(lane_id=0, completed_steps=100) is GateVerdict.ADMIT
    assert clock.calls == 1

    clock.advance(10.0)
    # 150 - 100 = 50 completed steps: below the interval, so no clock read may happen.
    assert gate.admit(lane_id=0, completed_steps=150) is GateVerdict.STEP_GATE
    assert clock.calls == 1, "a step-gate refusal must not read the clock"


def test_exactly_one_clock_read_on_the_path_that_reaches_the_wall_gate() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(), lease=AlwaysActiveLease(), clock=clock)

    assert gate.admit(lane_id=0, completed_steps=100) is GateVerdict.ADMIT
    assert clock.calls == 1, "one clock read serves circuit, wall, lease, session and budget"

    clock.advance(0.1)
    assert gate.admit(lane_id=0, completed_steps=200) is GateVerdict.WALL_GATE
    assert clock.calls == 2, "a wall-gate refusal also costs exactly one read"

    clock.advance(5.0)
    assert gate.admit(lane_id=0, completed_steps=300) is GateVerdict.ADMIT
    assert clock.calls == 3


def test_force_first_only_bypasses_the_step_gate_for_the_first_sample() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(), lease=AlwaysActiveLease(), clock=clock)

    assert gate.admit(lane_id=0, completed_steps=0, force_first=True) is GateVerdict.ADMIT
    clock.advance(60.0)
    # A second armed attempt still respects the rate budget.
    assert gate.admit(lane_id=0, completed_steps=1, force_first=True) is GateVerdict.STEP_GATE


# --------------------------------------------------------------------------------------
# Individual gates
# --------------------------------------------------------------------------------------


def test_wall_gate_refuses_inside_the_interval_and_admits_after_it() -> None:
    clock = _CountingClock()
    gate = CaptureGate(
        _preview_config(min_wall_interval_s=1.0, min_completed_env_steps_between_frames=1),
        lease=AlwaysActiveLease(),
        clock=clock,
    )

    assert gate.admit(0, 1) is GateVerdict.ADMIT
    clock.advance(0.999)
    assert gate.admit(0, 2) is GateVerdict.WALL_GATE
    clock.advance(0.0011)
    assert gate.admit(0, 3) is GateVerdict.ADMIT
    assert gate.counters.refused_wall_gate == 1
    assert gate.counters.admitted == 2


def test_wall_gate_is_tracked_per_lane() -> None:
    clock = _CountingClock()
    gate = CaptureGate(
        _preview_config(lane_ids=(0, 1), min_completed_env_steps_between_frames=1),
        lease=AlwaysActiveLease(),
        clock=clock,
    )
    assert gate.admit(0, 1) is GateVerdict.ADMIT
    assert gate.admit(1, 1) is GateVerdict.ADMIT  # a different lane has its own history
    clock.advance(0.1)
    assert gate.admit(0, 2) is GateVerdict.WALL_GATE
    assert gate.admit(1, 2) is GateVerdict.WALL_GATE


def test_no_viewer_refusal_when_the_lease_is_absent_or_stale() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(), lease=None, clock=clock)
    assert gate.admit(0, 100) is GateVerdict.NO_VIEWER
    assert gate.counters.refused_no_viewer == 1

    lease = LocalViewerLease()
    gate = CaptureGate(_preview_config(), lease=lease, clock=clock)
    lease.renew(10.0, now=clock.now - 20.0)  # expired twenty seconds ago
    assert gate.admit(0, 100) is GateVerdict.NO_VIEWER

    lease.renew(10.0, now=clock.now)
    assert gate.admit(0, 100) is GateVerdict.ADMIT

    # A revoked lease suspends extraction again without touching anything else.
    lease.revoke()
    clock.advance(5.0)
    assert gate.admit(0, 300) is GateVerdict.NO_VIEWER


def test_a_lease_that_expires_exactly_now_is_not_active() -> None:
    clock = _CountingClock()
    lease = LocalViewerLease(deadline=clock.now)
    gate = CaptureGate(_preview_config(), lease=lease, clock=clock)
    assert gate.admit(0, 100) is GateVerdict.NO_VIEWER


def test_require_active_viewer_false_skips_the_lease_entirely() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(require_active_viewer=False), lease=None, clock=clock)
    assert gate.admit(0, 100) is GateVerdict.ADMIT


def test_session_expiry_refuses_after_the_bounded_wall_time() -> None:
    clock = _CountingClock()
    gate = CaptureGate(
        _preview_config(max_session_wall_s=300.0), lease=AlwaysActiveLease(), clock=clock
    )

    assert gate.admit(0, 100) is GateVerdict.ADMIT  # arms the session at _T0
    clock.advance(299.0)
    assert gate.admit(0, 300) is GateVerdict.ADMIT
    clock.advance(2.0)  # 301 s since the session started
    assert gate.admit(0, 500) is GateVerdict.SESSION_EXPIRED
    assert gate.counters.refused_session_expired == 1


def test_byte_budget_exhaustion_refuses_and_recovers_after_the_bucket_window() -> None:
    clock = _CountingClock()
    gate = CaptureGate(
        _preview_config(
            min_wall_interval_s=0.0,
            min_completed_env_steps_between_frames=1,
            max_frame_bytes=2048,
            max_output_bytes_per_wall_s=1000,
        ),
        lease=AlwaysActiveLease(),
        clock=clock,
    )

    assert gate.admit(0, 1) is GateVerdict.ADMIT
    assert gate.charge(600) is GateVerdict.ADMIT
    assert gate.charge(600) is GateVerdict.ADMIT
    assert gate.counters.bytes_emitted == 1200

    clock.advance(0.5)  # still inside the same one-second bucket
    assert gate.admit(0, 2) is GateVerdict.BYTE_BUDGET
    assert gate.counters.refused_byte_budget == 1

    clock.advance(0.6)  # 1.1 s since the bucket was armed: it refills
    assert gate.admit(0, 3) is GateVerdict.ADMIT


def test_charge_refuses_an_oversized_frame_without_spending_the_budget() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(max_frame_bytes=2048), lease=AlwaysActiveLease(), clock=clock)
    assert gate.max_frame_bytes == 2048
    assert gate.admit(0, 100) is GateVerdict.ADMIT

    assert gate.charge(4096) is GateVerdict.FRAME_TOO_LARGE
    assert gate.counters.refused_frame_too_large == 1
    assert gate.counters.bytes_emitted == 0, "an oversized frame is not counted as emitted"

    assert gate.charge(2048) is GateVerdict.ADMIT
    assert gate.counters.bytes_emitted == 2048


def test_circuit_open_refusal_and_recovery_after_the_cooldown() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(), lease=AlwaysActiveLease(), clock=clock)

    gate.open_circuit(30.0)
    assert gate.admit(0, 100) is GateVerdict.CIRCUIT_OPEN
    assert gate.counters.refused_circuit_open == 1

    clock.advance(29.0)
    assert gate.admit(0, 200) is GateVerdict.CIRCUIT_OPEN

    clock.advance(1.5)  # past the 30 s cooldown
    assert gate.admit(0, 300) is GateVerdict.ADMIT


def test_release_viewer_forgets_rate_state_only() -> None:
    clock = _CountingClock()
    gate = CaptureGate(_preview_config(), lease=AlwaysActiveLease(), clock=clock)
    assert gate.admit(0, 100) is GateVerdict.ADMIT
    clock.advance(0.1)
    assert gate.admit(0, 200) is GateVerdict.WALL_GATE

    gate.release_viewer()
    assert gate.admit(0, 200) is GateVerdict.ADMIT, "a reconnecting viewer gets a frame promptly"
    assert gate.counters.admitted == 2


# --------------------------------------------------------------------------------------
# record_eval
# --------------------------------------------------------------------------------------


def test_record_eval_captures_every_decision_without_reading_a_clock() -> None:
    clock = _ExplodingClock()
    config = CaptureConfig(
        profile=Profile.RECORD_EVAL, record_eval=RecordEvalConfig(capture_every_decision=True)
    )
    gate = CaptureGate(config, lease=None, clock=clock)

    # An explicit recording session is not decimated and is not lane-filtered.
    assert gate.admit(lane_id=5, completed_steps=0) is GateVerdict.ADMIT
    assert gate.admit(lane_id=5, completed_steps=1) is GateVerdict.ADMIT
    assert clock.calls == 0
    assert gate.counters.admitted == 2
    # It also has no frame-size cap: a recording must not lose entities silently.
    assert gate.charge(10 * 1024 * 1024) is GateVerdict.ADMIT


def test_record_eval_still_honours_the_circuit_breaker() -> None:
    clock = _CountingClock()
    config = CaptureConfig(
        profile=Profile.RECORD_EVAL, record_eval=RecordEvalConfig(capture_every_decision=True)
    )
    gate = CaptureGate(config, lease=None, clock=clock)
    gate.open_circuit(30.0)
    assert gate.admit(0, 0) is GateVerdict.CIRCUIT_OPEN
    clock.advance(31.0)
    assert gate.admit(0, 0) is GateVerdict.ADMIT


def test_record_eval_without_capture_every_falls_back_to_the_preview_gates() -> None:
    clock = _CountingClock()
    config = CaptureConfig(
        profile=Profile.RECORD_EVAL,
        record_eval=RecordEvalConfig(capture_every_decision=False),
        preview=PreviewConfig(lane_ids=(0,)),
    )
    gate = CaptureGate(config, lease=AlwaysActiveLease(), clock=clock)
    assert gate.admit(lane_id=5, completed_steps=10_000) is GateVerdict.LANE_NOT_SELECTED
    assert gate.admit(lane_id=0, completed_steps=10) is GateVerdict.STEP_GATE


# --------------------------------------------------------------------------------------
# Counters
# --------------------------------------------------------------------------------------


def test_counters_account_for_every_admit_attempt() -> None:
    clock = _CountingClock()
    gate = CaptureGate(
        _preview_config(lane_ids=(0,), min_completed_env_steps_between_frames=100),
        lease=AlwaysActiveLease(),
        clock=clock,
    )
    gate.admit(1, 10_000)  # lane
    gate.admit(0, 10)  # step gate
    gate.admit(0, 100)  # admit
    clock.advance(0.1)
    gate.admit(0, 300)  # wall gate

    counters = gate.counters
    refusals = (
        counters.refused_profile_off
        + counters.refused_lane
        + counters.refused_step_gate
        + counters.refused_wall_gate
        + counters.refused_no_viewer
        + counters.refused_session_expired
        + counters.refused_byte_budget
        + counters.refused_circuit_open
    )
    assert counters.attempts == 4
    assert counters.admitted + refusals == counters.attempts
    payload = counters.to_json()
    assert payload["attempts"] == 4 and payload["admitted"] == 1
    assert "_BY_VERDICT" not in payload


def test_counters_record_rejects_nothing_it_knows() -> None:
    counters = GateCounters()
    for verdict in GateVerdict:
        if verdict in (GateVerdict.ADMIT, GateVerdict.FRAME_TOO_LARGE):
            continue
        counters.record(verdict)
    counters.record(GateVerdict.ADMIT)
    assert counters.attempts == len(GateVerdict) - 1
    assert counters.admitted == 1


# --------------------------------------------------------------------------------------
# Configuration parsing
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"lane_ids": []}, "at least one lane"),
        ({"min_completed_env_steps_between_frames": 0}, "must be >= 1"),
        ({"min_wall_interval_s": -1.0}, "must be >= 0"),
        ({"max_queued_frames": 0}, "must be >= 1"),
        ({"max_frame_bytes": 16}, "at least 1 KiB"),
    ],
)
def test_preview_config_refuses_incoherent_budgets(payload: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        PreviewConfig.from_json(payload)


def test_unknown_settings_are_refused_rather_than_ignored() -> None:
    with pytest.raises(ValueError, match="unknown preview settings"):
        PreviewConfig.from_json({"min_wall_interval_sec": 2.0})
    with pytest.raises(ValueError, match="unknown record_eval settings"):
        RecordEvalConfig.from_json({"chunk_frame": 8})
    with pytest.raises(ValueError, match="unknown capture settings"):
        CaptureConfig.from_json({"profiel": "off"})


def test_capture_config_round_trips_through_json(tmp_path: pathlib.Path) -> None:
    config = CaptureConfig.from_json(
        {
            "profile": "live_preview",
            "preview": {"lane_ids": [2], "min_wall_interval_s": 0.5},
            "record_eval": {"chunk_frames": 8},
            "render": {"enabled": True, "default_view": "3d"},
            "recent_transition_ring": {"enabled": True, "size": 4},
        }
    )
    assert config.profile is Profile.LIVE_PREVIEW
    assert config.preview.lane_ids == (2,)
    assert config.preview.min_wall_interval_s == 0.5
    assert config.preview.max_frame_bytes == DEFAULT_PREVIEW["max_frame_bytes"]
    assert config.record_eval.chunk_frames == 8
    assert config.render_enabled is True and config.render_default_view == "3d"
    assert config.recent_transition_ring_size == 4

    path = tmp_path / "capture.json"
    path.write_text(json.dumps(config.to_json()), encoding="utf-8")
    assert CaptureConfig.from_file(path) == config


# --------------------------------------------------------------------------------------
# Leases
# --------------------------------------------------------------------------------------


def test_always_active_lease_never_expires() -> None:
    assert AlwaysActiveLease().expires_at_monotonic() == float("inf")


def test_local_viewer_lease_renew_and_revoke() -> None:
    lease = LocalViewerLease()
    assert lease.expires_at_monotonic() == 0.0
    lease.renew(10.0, now=100.0)
    assert lease.expires_at_monotonic() == 110.0
    lease.revoke()
    assert lease.expires_at_monotonic() == 0.0


def test_shared_viewer_lease_is_a_plain_double() -> None:
    lease = SharedViewerLease.create()
    assert lease.expires_at_monotonic() == 0.0
    lease.renew(5.0, now=50.0)
    assert lease.expires_at_monotonic() == 55.0
    assert lease.raw.value == 55.0
    lease.revoke()
    assert lease.expires_at_monotonic() == 0.0

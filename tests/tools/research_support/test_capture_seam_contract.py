"""The contract between the shared environment's capture seams and their observer.

Every test here corresponds to a defect an independent review found in the first version of
the seams: a geometry time that did not match the geometry, a decision index that meant two
different things at two call sites, a documented protocol that was not the protocol, an
observer free to mutate the arrays that feed the simulation, and a display defect able to end
a scientific run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from envs.uav_service_restoration.config import load_config
from envs.uav_service_restoration.env import UAVServiceRestorationEnv

from tools.research_support.capture.profiles import (
    AlwaysActiveLease,
    CaptureConfig,
    CaptureGate,
    PreviewConfig,
    Profile,
    RecordEvalConfig,
)
from tools.research_support.capture.service_restoration import ServiceRestorationObserver
from tools.research_support.capture.transport import SinkStats
from tools.research_support.records import PolicyKind, SourceKind

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "configs" / "uav_service_restoration" / "smoke_fixture.json"
SEED = 17

#: The preset's kinematics, used to predict where a UAV must be at a given time.
MAX_SPEED_MPS = 20.0


class CollectingSink:
    """In-process sink that keeps every frame as parsed JSON."""

    active = True

    def __init__(self) -> None:
        self.frames: list[dict[str, Any]] = []
        self._stats = SinkStats()

    def offer(self, payload: bytes) -> bool:
        self.frames.append(json.loads(payload))
        self._stats.delivered += 1
        return True

    def close(self) -> None:
        self._stats.closed = True

    @property
    def stats(self) -> SinkStats:
        return self._stats


def _gate(profile: Profile = Profile.LIVE_PREVIEW) -> CaptureGate:
    preview = PreviewConfig(
        lane_ids=(0,),
        min_completed_env_steps_between_frames=1,
        min_wall_interval_s=0.0,
        require_active_viewer=True,
        max_output_bytes_per_wall_s=10**9,
    )
    config = CaptureConfig(
        profile=profile,
        preview=preview,
        record_eval=RecordEvalConfig(capture_every_decision=True),
    )
    return CaptureGate(config, lease=AlwaysActiveLease())


def _observer(gate: CaptureGate, sink: Any, **kwargs: Any) -> ServiceRestorationObserver:
    return ServiceRestorationObserver(
        gate=gate,
        sink=sink,
        run_id="seam-contract",
        trace_id="seam-contract",
        policy_kind=PolicyKind.RULE_CONTROLLER,
        source_kind=SourceKind.RULE_CONTROLLER_ROLLOUT,
        policy_label="constant_full_speed",
        **kwargs,
    )


def _run(observer: Any, steps: int = 4, *, config: Any = None) -> UAVServiceRestorationEnv:
    """Drive the env with a constant full-speed action so positions are predictable."""

    env = UAVServiceRestorationEnv(config or load_config(str(CONFIG_PATH)))
    env.set_capture_observer(observer)
    env.reset(seed=SEED)
    action = {a: np.array([1.0, 0.0, 0.0], dtype=np.float32) for a in env.agents}
    for _ in range(steps):
        if not env.agents:
            break
        env.step(action)
    return env


# --------------------------------------------------------------------------------------
# capture-time correctness
# --------------------------------------------------------------------------------------


def test_geometry_time_names_the_point_the_geometry_actually_holds_at() -> None:
    """Under the midpoint rule the solve uses the geometry at the middle of its window.

    The first version stamped that geometry with the window start, mislabelling every UAV
    position by ``max_speed * h / 2`` - 10 m on this preset.
    """

    config = load_config(str(CONFIG_PATH))
    assert config.episode.quadrature == "midpoint", "this test is about the midpoint rule"

    sink = CollectingSink()
    observer = _observer(_gate(), sink)
    env = _run(observer, steps=4, config=config)
    start_x = float(env._positions_m[0][0]) - MAX_SPEED_MPS * float(env._time_s)
    try:
        transitions = [f for f in sink.frames if f["clock"]["measurement_start_s"] is not None]
        assert transitions, "no interval frame was captured"
        for frame in transitions:
            clock = frame["clock"]
            shown_x = float(frame["uavs"][0]["position_m"][0])
            expected = start_x + MAX_SPEED_MPS * clock["geometry_time_s"]
            assert shown_x == pytest.approx(expected, abs=1e-6), (
                f"the displayed position is not the position at geometry_time_s="
                f"{clock['geometry_time_s']}"
            )
    finally:
        env.set_capture_observer(None)
        env.close()


def test_geometry_time_is_the_midpoint_of_the_measurement_window() -> None:
    """The documented relation between the two clocks, asserted on real frames."""

    sink = CollectingSink()
    observer = _observer(_gate(), sink)
    env = _run(observer, steps=4)
    try:
        checked = 0
        for frame in sink.frames:
            clock = frame["clock"]
            start, end = clock["measurement_start_s"], clock["measurement_end_s"]
            if start is None or end is None:
                continue
            assert clock["geometry_time_s"] == pytest.approx((start + end) / 2.0)
            assert end > start, "a measurement window is an interval, not a point"
            checked += 1
        assert checked, "no frame carried a measurement window"
    finally:
        env.set_capture_observer(None)
        env.close()


def test_the_geometry_time_lies_inside_the_decision_interval() -> None:
    sink = CollectingSink()
    observer = _observer(_gate(), sink)
    env = _run(observer, steps=4)
    try:
        for frame in sink.frames:
            metrics = frame.get("interval_metrics") or {}
            start = (metrics.get("interval_start_s") or {}).get("value")
            end = (metrics.get("interval_end_s") or {}).get("value")
            if start is None or end is None:
                continue
            geometry = frame["clock"]["geometry_time_s"]
            assert start <= geometry <= end, (
                f"geometry_time_s={geometry} is outside its own interval [{start}, {end}]"
            )
    finally:
        env.set_capture_observer(None)
        env.close()


# --------------------------------------------------------------------------------------
# one meaning for the decision index
# --------------------------------------------------------------------------------------


class RecordingObserver:
    """Records the ``decision_step`` each seam reports, and nothing else."""

    armed = True

    def __init__(self) -> None:
        self.begin: list[int] = []
        self.evaluated: list[int] = []
        self.complete: list[int] = []
        self.resets = 0

    def on_episode_reset(self, *, env: Any, time_s: float) -> None:
        self.resets += 1

    def begin_decision(self, env: Any, *, decision_step: int, time_s: float) -> None:
        self.begin.append(int(decision_step))

    def on_service_evaluated(self, **kwargs: Any) -> None:
        self.evaluated.append(int(kwargs["decision_step"]))

    def on_decision_complete(self, **kwargs: Any) -> None:
        self.complete.append(int(kwargs["decision_step"]))


def test_every_seam_reports_the_same_decision_index_for_one_interval() -> None:
    """``on_decision_complete`` used to read the index after it had been incremented.

    A frame then took its geometry from interval k and its label from interval k+1.
    """

    observer = RecordingObserver()
    env = _run(observer, steps=5)
    try:
        assert observer.begin == observer.complete, (
            "begin_decision and on_decision_complete disagree about which interval ran"
        )
        assert observer.begin == list(range(len(observer.begin))), "indices are not 0-based"
        for index in observer.begin:
            assert observer.evaluated.count(index) >= 1
        assert set(observer.evaluated) <= set(observer.begin)
    finally:
        env.set_capture_observer(None)
        env.close()


def test_reset_notifies_the_observer_exactly_once() -> None:
    observer = RecordingObserver()
    env = _run(observer, steps=1)
    try:
        assert observer.resets == 1
    finally:
        env.set_capture_observer(None)
        env.close()


# --------------------------------------------------------------------------------------
# the documented protocol is the protocol
# --------------------------------------------------------------------------------------


def test_every_documented_callback_is_actually_required() -> None:
    """The docstring once called them "all optional" while invoking them unguarded.

    An observer written to that docstring raised ``AttributeError`` inside ``reset()``.
    """

    doc = UAVServiceRestorationEnv.set_capture_observer.__doc__ or ""
    for name in (
        "begin_decision",
        "armed",
        "on_service_evaluated",
        "on_decision_complete",
        "on_episode_reset",
    ):
        assert name in doc, f"{name} is called by the env but is not documented"
    assert "all optional" not in doc

    class MissingReset:
        armed = False

        def begin_decision(self, env, **kwargs):
            pass

        def on_decision_complete(self, **kwargs):
            pass

    env = UAVServiceRestorationEnv(load_config(str(CONFIG_PATH)))
    env.set_capture_observer(MissingReset())
    try:
        with pytest.raises(AttributeError, match="on_episode_reset"):
            env.reset(seed=SEED)
    finally:
        env.set_capture_observer(None)
        env.close()


# --------------------------------------------------------------------------------------
# the observer cannot alter the simulation
# --------------------------------------------------------------------------------------


class MutatingObserver:
    """Deliberately writes into an array the environment reads back afterwards."""

    armed = True

    def __init__(self, field: str) -> None:
        self.field = field
        self.attempts = 0

    def on_episode_reset(self, *, env: Any, time_s: float) -> None:
        pass

    def begin_decision(self, env: Any, *, decision_step: int, time_s: float) -> None:
        pass

    def on_service_evaluated(self, **kwargs: Any) -> None:
        self.attempts += 1
        kwargs[self.field] *= 2.0

    def on_decision_complete(self, **kwargs: Any) -> None:
        pass


@pytest.mark.parametrize(
    "field", ["demand_mbps", "positions_m", "end_positions_m", "requested_velocity_mps"]
)
def test_an_observer_that_writes_into_a_handed_over_array_is_refused(field: str) -> None:
    """Mutating one of these used to change the reward and the trajectory silently."""

    observer = MutatingObserver(field)
    env = UAVServiceRestorationEnv(load_config(str(CONFIG_PATH)))
    env.set_capture_observer(observer)
    try:
        env.reset(seed=SEED)
        action = {a: np.array([1.0, 0.0, 0.0], dtype=np.float32) for a in env.agents}
        with pytest.raises(ValueError, match="read-only|assignment destination"):
            env.step(action)
        assert observer.attempts == 1
    finally:
        env.set_capture_observer(None)
        env.close()


def test_the_read_only_window_is_released_after_the_call() -> None:
    """The guard must not leave the simulation's own state frozen."""

    sink = CollectingSink()
    observer = _observer(_gate(), sink)
    env = _run(observer, steps=3)
    try:
        assert env._positions_m.flags.writeable, (
            "the env's live position array was left read-only by the capture guard"
        )
    finally:
        env.set_capture_observer(None)
        env.close()


# --------------------------------------------------------------------------------------
# a display defect must not end a run
# --------------------------------------------------------------------------------------


class ExplodingSink:
    """A sink whose serialisation stage fails on every frame."""

    active = True

    def __init__(self) -> None:
        self._stats = SinkStats()

    def offer(self, payload: bytes) -> bool:
        raise RuntimeError("sink exploded")

    def close(self) -> None:
        pass

    @property
    def stats(self) -> SinkStats:
        return self._stats


def test_a_preview_defect_disarms_the_capture_and_lets_the_run_continue() -> None:
    gate = _gate(Profile.LIVE_PREVIEW)
    observer = _observer(gate, ExplodingSink())
    assert observer.absorbs_errors is True
    env = _run(observer, steps=4)
    try:
        assert env._step_index == 4, "the run did not complete its steps"
        assert observer.emitted == 0
        assert observer.last_error and "sink exploded" in observer.last_error
        assert observer.capture_errors > 0, "the failure was neither raised nor counted"
    finally:
        env.set_capture_observer(None)
        env.close()


def test_a_recording_defect_surfaces_because_the_recording_is_the_deliverable() -> None:
    gate = _gate(Profile.RECORD_EVAL)
    observer = _observer(gate, ExplodingSink())
    assert observer.absorbs_errors is False
    env = UAVServiceRestorationEnv(load_config(str(CONFIG_PATH)))
    env.set_capture_observer(observer)
    try:
        # The very first emit is the episode-reset frame, so the defect surfaces there and
        # the operator learns immediately that this recording is not being produced.
        with pytest.raises(RuntimeError, match="sink exploded"):
            env.reset(seed=SEED)
    finally:
        env.set_capture_observer(None)
        env.close()


# --------------------------------------------------------------------------------------
# the capture-resolution label
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("capture_substeps", "expected"),
    [
        (False, "first_substep_of_an_admitted_decision_interval"),
        (True, "last_substep_of_an_admitted_decision_interval"),
    ],
)
def test_the_capture_resolution_label_describes_what_is_actually_emitted(
    capture_substeps: bool, expected: str
) -> None:
    """The label once claimed a per-substep resolution that was never produced."""

    sink = CollectingSink()
    observer = _observer(_gate(), sink, capture_substeps=capture_substeps)
    env = _run(observer, steps=3)
    try:
        assert sink.frames
        labels = {
            (f.get("provenance") or {}).get("capture_resolution") for f in sink.frames
        }
        assert labels == {expected}
        intervals = {
            ((f.get("interval_metrics") or {}).get("interval_start_s") or {}).get("value")
            for f in sink.frames
        } - {None}
        interval_frames = [
            f for f in sink.frames if f["clock"]["measurement_start_s"] is not None
        ]
        assert len(interval_frames) == len(intervals), (
            "more than one frame was emitted for the same decision interval"
        )
    finally:
        env.set_capture_observer(None)
        env.close()


def test_capture_substeps_retains_the_last_substep_not_the_first() -> None:
    """The two modes must differ in which substep they carry, or the flag is decorative."""

    config = load_config(str(CONFIG_PATH))
    geometry: dict[bool, list[float]] = {}
    for flag in (False, True):
        sink = CollectingSink()
        observer = _observer(_gate(), sink, capture_substeps=flag)
        env = _run(observer, steps=3, config=config)
        try:
            geometry[flag] = [
                f["clock"]["geometry_time_s"]
                for f in sink.frames
                if f["clock"]["measurement_start_s"] is not None
            ]
        finally:
            env.set_capture_observer(None)
            env.close()
    assert geometry[False] and geometry[True]
    assert geometry[True] != geometry[False], (
        "capture_substeps carried the same substep as the default, so the flag does nothing"
    )
    for first, last in zip(geometry[False], geometry[True]):
        assert last > first, "the last substep must be later than the first"

"""Tests for ``tools/research_support/capture/transport.py``.

The transport is the part of the suite that sits closest to a scientific step, so the
properties under test are cost and containment properties:

* an inactive channel is distinguishable from a failed one (``active``);
* the latest-frame file is replaced atomically, so a reader sees either the previous
  complete frame or the new complete frame and never a half-written one;
* nothing blocks: a full queue coalesces, a broken sink is absorbed and counted;
* the producer-side lease read is a memory load, not a syscall.
"""

from __future__ import annotations

import builtins
import mmap
import os
import pathlib
import queue
import shutil
import socket as socket_module
import struct
import sys
import threading

import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from tools.research_support.capture import transport  # noqa: E402
from tools.research_support.capture.transport import (  # noqa: E402
    BoundedQueueSink,
    CompositeSink,
    LatestFrameFileSink,
    LatestFrameReader,
    MappedViewerLease,
    NullSink,
    OverloadBreaker,
    SinkStats,
)
from tools.research_support.capture.profiles import (  # noqa: E402
    AlwaysActiveLease,
    CaptureConfig,
    CaptureGate,
    GateVerdict,
    PreviewConfig,
    Profile,
)


class _RaisingSink:
    """A sink that violates the no-raise contract, used only to characterise behaviour."""

    def __init__(self) -> None:
        self._stats = SinkStats()

    def offer(self, payload: bytes) -> bool:
        raise RuntimeError("sink exploded")

    def close(self) -> None:
        self._stats.closed = True

    @property
    def active(self) -> bool:
        return True

    @property
    def stats(self) -> SinkStats:
        return self._stats


# --------------------------------------------------------------------------------------
# active
# --------------------------------------------------------------------------------------


def test_null_sink_is_inactive_and_accepts_nothing() -> None:
    sink = NullSink()
    assert sink.active is False
    assert sink.offer(b"{}") is False
    assert sink.stats.offered == 1
    assert sink.stats.delivered == 0
    sink.close()
    assert sink.stats.closed is True


def test_real_sinks_report_active(tmp_path: pathlib.Path) -> None:
    file_sink = LatestFrameFileSink(tmp_path / "stream")
    queue_sink = BoundedQueueSink(2)
    try:
        assert file_sink.active is True
        assert queue_sink.active is True
        assert CompositeSink(file_sink, NullSink()).active is True
        assert CompositeSink(NullSink(), NullSink()).active is False
        assert CompositeSink().active is False
    finally:
        file_sink.close()
        queue_sink.close()


# --------------------------------------------------------------------------------------
# LatestFrameFileSink
# --------------------------------------------------------------------------------------


def test_latest_frame_sink_creates_its_directory_and_publishes(tmp_path: pathlib.Path) -> None:
    sink = LatestFrameFileSink(tmp_path / "nested" / "stream")
    try:
        assert sink.directory.is_dir()
        assert sink.offer(b'{"frame": 1}') is True
        assert sink.latest_path.name == "latest.json"
        assert sink.latest_path.read_bytes() == b'{"frame": 1}'
        assert sink.stats.delivered == 1
        assert sink.stats.bytes_written == len(b'{"frame": 1}')
        assert sink.write_health(b'{"state": "LIVE"}') is True
        assert sink.health_path.read_bytes() == b'{"state": "LIVE"}'
        # No temporary file survives a successful write.
        assert sorted(p.name for p in sink.directory.iterdir()) == [
            "latest.json",
            "stream_health.json",
        ]
    finally:
        sink.close()


def test_latest_frame_sink_replaces_the_destination_atomically(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The payload is written to a temporary file and renamed over the destination.

    The spy inspects the destination *at the instant of the rename*: it must still hold
    the previous complete frame, which is exactly the property that makes a concurrent
    reader safe.
    """

    stream = tmp_path / "stream"
    sink = LatestFrameFileSink(stream)
    old = b"o" * (1 << 20)
    new = b"n" * (3 << 20)
    assert sink.offer(old) is True

    real_replace = os.replace
    seen: list[bytes] = []

    def spy(src, dst, *args, **kwargs):  # type: ignore[no-untyped-def]
        source = pathlib.Path(src)
        assert source.parent == stream, "the temporary file must share the destination volume"
        assert source.name.startswith(".latest-")
        assert source.read_bytes() == new
        seen.append(pathlib.Path(dst).read_bytes())
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", spy)
    try:
        assert sink.offer(new) is True
    finally:
        monkeypatch.undo()
        sink.close()

    assert seen == [old], "the destination held the previous complete frame until the rename"
    assert (stream / "latest.json").read_bytes() == new


def test_concurrent_reader_only_ever_sees_a_complete_frame(tmp_path: pathlib.Path) -> None:
    stream = tmp_path / "stream"
    sink = LatestFrameFileSink(stream)
    reader = LatestFrameReader(stream)
    size = 256 * 1024
    payloads = (b"a" * size, b"b" * size)
    assert sink.offer(payloads[0]) is True

    stop = threading.Event()
    partial: list[int] = []
    reads = [0]

    def poll() -> None:
        while not stop.is_set():
            payload, error = reader.read()
            if payload is None:
                continue
            reads[0] += 1
            if payload not in payloads:
                partial.append(len(payload))

    worker = threading.Thread(target=poll, name="latest-frame-poller", daemon=True)
    worker.start()
    try:
        delivered = sum(sink.offer(payloads[i % 2]) for i in range(40))
    finally:
        stop.set()
        worker.join(timeout=5.0)
        sink.close()

    assert not worker.is_alive()
    assert reads[0] > 0, "the poller never observed a frame"
    assert partial == [], f"observed {len(partial)} partially written frames"
    # A rename can legitimately lose a race with an open reader on Windows; that is a
    # dropped *display* frame, absorbed and counted, never an exception.
    assert delivered >= 1
    assert sink.stats.offered == 41
    assert sink.stats.delivered + sink.stats.dropped_error == 41


def test_latest_frame_sink_absorbs_a_write_failure(tmp_path: pathlib.Path) -> None:
    stream = tmp_path / "stream"
    sink = LatestFrameFileSink(stream)
    assert sink.offer(b"{}") is True
    shutil.rmtree(stream)  # the directory is revoked under the producer

    assert sink.offer(b"{}") is False, "a failed write must not raise into the producer"
    assert sink.stats.write_errors == 1
    assert sink.stats.dropped_error == 1
    assert sink.stats.last_error and "Error" in sink.stats.last_error
    assert sink.write_health(b"{}") is False
    sink.close()


# --------------------------------------------------------------------------------------
# BoundedQueueSink
# --------------------------------------------------------------------------------------


def test_bounded_queue_is_latest_wins_and_never_blocks() -> None:
    sink = BoundedQueueSink(2)
    try:
        assert sink.offer(b"one") is True
        assert sink.offer(b"two") is True
        assert sink.queue.full() is True
        # The third offer displaces the oldest rather than waiting for a consumer.
        assert sink.offer(b"three") is True
        assert sink.stats.coalesced == 1
        assert sink.stats.delivered == 3
        assert sink.stats.offered == 3
        assert sink.drain_latest() == b"three"
        assert sink.drain_latest() is None
    finally:
        sink.close()
    assert sink.stats.closed is True


def test_bounded_queue_drain_latest_discards_older_frames() -> None:
    sink = BoundedQueueSink(4)
    try:
        for index in range(4):
            assert sink.offer(str(index).encode()) is True
        assert sink.drain_latest() == b"3"
        assert sink.queue.empty()
    finally:
        sink.close()


def test_bounded_queue_absorbs_a_broken_queue() -> None:
    class _BrokenQueue:
        def put_nowait(self, payload: bytes) -> None:
            raise OSError("pipe is gone")

    sink = BoundedQueueSink(2, factory=lambda maxsize: _BrokenQueue())
    assert sink.offer(b"x") is False
    assert sink.stats.dropped_error == 1
    assert "OSError" in (sink.stats.last_error or "")
    sink.close()


def test_bounded_queue_refuses_a_meaningless_size() -> None:
    with pytest.raises(ValueError, match="maxsize >= 1"):
        BoundedQueueSink(0)


def test_bounded_queue_counts_a_frame_it_could_not_place() -> None:
    class _AlwaysFullQueue:
        def put_nowait(self, payload: bytes) -> None:
            raise queue.Full()

        def get_nowait(self) -> bytes:
            raise queue.Empty()

    sink = BoundedQueueSink(1, factory=lambda maxsize: _AlwaysFullQueue())
    assert sink.offer(b"x") is False
    assert sink.stats.dropped_full == 1
    assert sink.stats.delivered == 0
    sink.close()


# --------------------------------------------------------------------------------------
# CompositeSink
# --------------------------------------------------------------------------------------


def test_composite_sink_keeps_delivering_when_one_child_fails(tmp_path: pathlib.Path) -> None:
    broken_dir = tmp_path / "broken"
    broken = LatestFrameFileSink(broken_dir)
    healthy = LatestFrameFileSink(tmp_path / "healthy")
    composite = CompositeSink(broken, NullSink(), healthy)
    try:
        shutil.rmtree(broken_dir)  # make the first child fail for real
        assert composite.offer(b'{"frame": 1}') is True
        assert healthy.latest_path.read_bytes() == b'{"frame": 1}'
        assert broken.stats.write_errors == 1
        assert composite.stats.delivered == 1
        assert composite.stats.dropped_full == 0
        assert len(composite.sinks) == 3
    finally:
        composite.close()


def test_composite_sink_reports_a_frame_no_child_accepted() -> None:
    composite = CompositeSink(NullSink(), NullSink())
    assert composite.offer(b"{}") is False
    assert composite.stats.dropped_full == 1
    assert composite.stats.delivered == 0
    composite.close()
    assert all(sink.stats.closed for sink in composite.sinks)
    assert composite.stats.closed is True


def test_composite_sink_contains_a_child_that_breaks_the_no_raise_contract() -> None:
    """A raising child costs its own frame and nothing else.

    ``CompositeSink.offer`` sits on a path reachable from a scientific step, so it must not
    let a caller-supplied sink raise into the producer, and it must not let one bad child
    deprive the remaining sinks of the frame.
    """

    healthy = BoundedQueueSink(2)
    composite = CompositeSink(_RaisingSink(), healthy)
    try:
        assert composite.offer(b"{}") is True, "the healthy child still took the frame"
        assert healthy.stats.delivered == 1, "children after the raising one still ran"
        assert composite.stats.write_errors == 1, "the failure is counted, not hidden"
        assert composite.stats.delivered == 1
    finally:
        healthy.close()


# --------------------------------------------------------------------------------------
# MappedViewerLease
# --------------------------------------------------------------------------------------


def test_mapped_lease_arms_and_expires(tmp_path: pathlib.Path) -> None:
    with MappedViewerLease.in_directory(tmp_path, create=True) as lease:
        assert lease.path.name == "viewer.lease"
        assert lease.path.stat().st_size == struct.calcsize("<d")
        assert lease.expires_at_monotonic() == 0.0  # nobody has looked yet

        lease.renew(10.0, now=500.0)
        assert lease.expires_at_monotonic() == 510.0
        assert lease.expires_at_monotonic() > 509.0  # a freshly armed lease reads active

        lease.renew(10.0, now=400.0)  # armed long ago: expired at 410 < now
        assert lease.expires_at_monotonic() == 410.0

        lease.revoke()
        assert lease.expires_at_monotonic() == 0.0


def test_mapped_lease_is_shared_between_two_handles(tmp_path: pathlib.Path) -> None:
    with MappedViewerLease.in_directory(tmp_path, create=True) as consumer:
        with MappedViewerLease.in_directory(tmp_path, create=False) as producer:
            consumer.renew(10.0, now=123.0)
            assert producer.expires_at_monotonic() == 133.0
            consumer.revoke()
            assert producer.expires_at_monotonic() == 0.0


def test_mapped_lease_read_touches_no_file_or_socket(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The per-step read must be a memory load, not a stat, an open or an RPC."""

    lease = MappedViewerLease.in_directory(tmp_path, create=True)
    try:
        lease.renew(10.0, now=500.0)
        assert isinstance(lease._map, mmap.mmap)

        def _boom(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            raise AssertionError("the lease read performed I/O")

        monkeypatch.setattr(builtins, "open", _boom)
        monkeypatch.setattr(os, "stat", _boom)
        monkeypatch.setattr(os, "scandir", _boom)
        monkeypatch.setattr(socket_module, "socket", _boom)
        try:
            value = lease.expires_at_monotonic()
        finally:
            monkeypatch.undo()
        assert value == 510.0
    finally:
        lease.close()


def test_mapped_lease_drives_the_gate_without_a_socket(tmp_path: pathlib.Path) -> None:
    """End to end: the gate's viewer check is satisfied by the mapped double alone."""

    clock_now = [1000.0]
    config = CaptureConfig(profile=Profile.LIVE_PREVIEW, preview=PreviewConfig())
    with MappedViewerLease.in_directory(tmp_path, create=True) as lease:
        gate = CaptureGate(config, lease=lease, clock=lambda: clock_now[0])
        assert gate.admit(0, 100) is GateVerdict.NO_VIEWER
        lease.renew(10.0, now=clock_now[0])
        assert gate.admit(0, 100) is GateVerdict.ADMIT


# --------------------------------------------------------------------------------------
# OverloadBreaker
# --------------------------------------------------------------------------------------


def test_breaker_opens_after_the_configured_consecutive_failures() -> None:
    breaker = OverloadBreaker(failure_threshold=3, cooldown_s=30.0)
    assert breaker.record(ok=False, latency_s=0.0) is None
    assert breaker.record(ok=False, latency_s=0.0) is None
    assert breaker.trips == 0

    message = breaker.record(ok=False, latency_s=0.0)
    assert message is not None
    assert "suspended for 30s" in message
    assert "training unchanged" in message
    assert breaker.trips == 1
    assert breaker.last_reason == "transport_failures=3"


def test_breaker_failure_run_is_reset_by_a_success() -> None:
    breaker = OverloadBreaker(failure_threshold=3)
    breaker.record(ok=False, latency_s=0.0)
    breaker.record(ok=False, latency_s=0.0)
    assert breaker.record(ok=True, latency_s=0.0) is None
    breaker.record(ok=False, latency_s=0.0)
    breaker.record(ok=False, latency_s=0.0)
    assert breaker.trips == 0, "failures must be consecutive to trip the breaker"


def test_breaker_opens_on_repeated_slow_captures() -> None:
    breaker = OverloadBreaker(
        failure_threshold=99, latency_threshold_s=0.25, latency_threshold_count=3
    )
    assert breaker.record(ok=True, latency_s=0.3) is None
    assert breaker.record(ok=True, latency_s=0.3) is None
    message = breaker.record(ok=True, latency_s=0.3)
    assert message is not None and "capture_latency_s>0.25x3" in message
    assert breaker.trips == 1
    # A fast capture clears the run.
    breaker.record(ok=True, latency_s=0.0)
    breaker.record(ok=True, latency_s=0.3)
    assert breaker.trips == 1


def test_breaker_throttles_its_diagnostic_but_still_counts_the_trip() -> None:
    breaker = OverloadBreaker(failure_threshold=1, diagnostic_interval_s=3600.0)
    assert breaker.record(ok=False, latency_s=0.0) is not None
    assert breaker.record(ok=False, latency_s=0.0) is None, "one diagnostic per interval"
    assert breaker.trips == 2


def test_breaker_emits_its_first_diagnostic_on_a_host_whose_monotonic_clock_is_young(
    monkeypatch,
) -> None:
    """A young monotonic clock must not look like "a diagnostic was already emitted".

    ``time.monotonic()`` is uptime-based, so it is a small number on a freshly started
    WSL2 VM and within the first minute after a Windows reboot. A zero-initialised
    "last diagnostic" timestamp silently swallowed the very first suspension notice
    under exactly those conditions, which is the one notice an operator needs.
    """

    monkeypatch.setattr(transport.time, "monotonic", lambda: 4.0)
    breaker = OverloadBreaker(failure_threshold=1, diagnostic_interval_s=3600.0)
    assert breaker.record(ok=False, latency_s=0.0) is not None
    assert breaker.record(ok=False, latency_s=0.0) is None, "one diagnostic per interval"
    assert breaker.trips == 2


def test_breaker_cooldown_suspends_and_restores_capture() -> None:
    """The breaker's cooldown is applied through the gate, which is where recovery lives."""

    clock = [1000.0]
    breaker = OverloadBreaker(failure_threshold=2, cooldown_s=30.0)
    gate = CaptureGate(
        CaptureConfig(profile=Profile.LIVE_PREVIEW),
        lease=AlwaysActiveLease(),
        clock=lambda: clock[0],
    )
    breaker.record(ok=False, latency_s=0.0)
    assert breaker.record(ok=False, latency_s=0.0) is not None

    gate.open_circuit(breaker.cooldown_s)
    assert gate.admit(0, 100) is GateVerdict.CIRCUIT_OPEN
    clock[0] += 31.0
    assert gate.admit(0, 200) is GateVerdict.ADMIT


# --------------------------------------------------------------------------------------
# LatestFrameReader
# --------------------------------------------------------------------------------------


def test_reader_tolerates_a_missing_directory_and_file(tmp_path: pathlib.Path) -> None:
    reader = LatestFrameReader(tmp_path / "never_created")
    assert reader.read() == (None, None), "nothing published yet is not an error"
    assert reader.read_health() is None
    assert reader.last_mtime_ns == -1

    (tmp_path / "stream").mkdir()
    reader = LatestFrameReader(tmp_path / "stream")
    assert reader.read() == (None, None)


def test_reader_returns_a_malformed_payload_without_raising(tmp_path: pathlib.Path) -> None:
    stream = tmp_path / "stream"
    stream.mkdir()
    (stream / "latest.json").write_bytes(b'{"identity": {"sequ')  # truncated producer write
    reader = LatestFrameReader(stream)
    payload, error = reader.read()
    assert error is None
    assert payload == b'{"identity": {"sequ'
    assert reader.last_mtime_ns > 0

    (stream / "stream_health.json").write_bytes(b"not json either")
    assert reader.read_health() == b"not json either"


def test_reader_is_usable_from_several_threads(tmp_path: pathlib.Path) -> None:
    stream = tmp_path / "stream"
    sink = LatestFrameFileSink(stream)
    sink.offer(b'{"frame": 1}')
    reader = LatestFrameReader(stream)
    results: list[tuple[bytes | None, str | None]] = []
    lock = threading.Lock()

    def read_once() -> None:
        payload, error = reader.read()
        with lock:
            results.append((payload, error))

    threads = [threading.Thread(target=read_once) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5.0)
    sink.close()

    assert len(results) == 8
    assert all(payload == b'{"frame": 1}' and error is None for payload, error in results)

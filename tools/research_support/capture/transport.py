"""Bounded, non-waiting presentation transport.

Design constraints taken from Section 0.2 C and Section 5.5 of the plan:

* No writer, queue, shared allocation or thread exists under ``profile=off``. Every class
  here is constructed only by an explicitly enabled diagnostic invocation.
* The producer never waits for a consumer. Admission is a non-blocking attempt; on a full
  queue or a slow reader the **display** frame is dropped or coalesced, a counter moves,
  and the caller continues.
* Latest-wins for live preview: the newest frame replaces the previous one atomically, so
  a reader either sees the old complete frame or the new complete frame and never a
  half-written one.
* Queueing is not free. ``BoundedQueueSink`` documents what it costs (a pickle of the
  already-built payload plus a feeder thread) and how it shuts down, because a
  ``multiprocessing.Queue`` feeder thread that is never drained can block interpreter
  exit. [E1]

The viewer lease lives here too, because the cross-process variant needs a file. The
producer maps it **once** when the session is armed; the per-step read is then a memory
load from a resident page rather than a syscall, a file scan or an RPC.
"""

from __future__ import annotations

import dataclasses
import mmap
import os
import queue
import struct
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

_LEASE_STRUCT = struct.Struct("<d")
_LEASE_FILE_NAME = "viewer.lease"
_LATEST_FILE_NAME = "latest.json"
_HEALTH_FILE_NAME = "stream_health.json"


# --------------------------------------------------------------------------------------
# Counters
# --------------------------------------------------------------------------------------


@dataclass
class SinkStats:
    """What actually happened to the display stream. Reported verbatim to the UI."""

    offered: int = 0
    delivered: int = 0
    dropped_full: int = 0
    dropped_error: int = 0
    coalesced: int = 0
    bytes_written: int = 0
    write_errors: int = 0
    #: Publishes that lost a race with a reader holding the destination open, then succeeded
    #: on retry. Kept apart from `write_errors`: on Windows this is the normal cost of a
    #: polling viewer, not a fault, and conflating the two made a healthy preview look broken.
    replace_contended: int = 0
    last_error: str | None = None
    closed: bool = False

    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class FrameSink(Protocol):
    """Accepts an already-serialised frame. Must never block the caller."""

    def offer(self, payload: bytes) -> bool: ...

    def close(self) -> None: ...

    @property
    def stats(self) -> SinkStats: ...

    @property
    def active(self) -> bool:
        """Whether this sink is a real display channel.

        A producer that records a trace with no viewer attached has no display channel at
        all, and that is not a transport failure. The overload breaker must not count a
        refusal from an inactive sink, or a perfectly healthy recording session would
        suspend itself after a handful of frames.
        """
        ...


# --------------------------------------------------------------------------------------
# Sinks
# --------------------------------------------------------------------------------------


class NullSink:
    """Accepts nothing. Used where a sink reference is structurally required.

    ``active`` is False, so a caller can tell "there is no display channel" apart from
    "the display channel failed".
    """

    def __init__(self) -> None:
        self._stats = SinkStats()

    def offer(self, payload: bytes) -> bool:  # noqa: ARG002
        self._stats.offered += 1
        return False

    def close(self) -> None:
        self._stats.closed = True

    @property
    def active(self) -> bool:
        return False

    @property
    def stats(self) -> SinkStats:
        return self._stats


class LatestFrameFileSink:
    """Atomic latest-frame snapshot in a directory owned by this invocation.

    A write is ``open(tmp) -> write -> flush -> replace``. ``os.replace`` is atomic on
    both Windows and POSIX for paths on the same volume, so a polling reader never
    observes a partial frame. There is no durable history: this is the lossy display
    channel, and losing a frame here is not an experiment failure.

    A full disk or a permission error is absorbed: the counter moves, the error string is
    retained for the UI, and the caller is told ``False`` rather than raising into a
    scientific step.
    """

    def __init__(self, directory: str | os.PathLike[str], *, fsync: bool = False) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._target = self._dir / _LATEST_FILE_NAME
        self._health = self._dir / _HEALTH_FILE_NAME
        self._fsync = bool(fsync)
        self._stats = SinkStats()

    @property
    def directory(self) -> Path:
        return self._dir

    @property
    def latest_path(self) -> Path:
        return self._target

    @property
    def health_path(self) -> Path:
        return self._health

    def offer(self, payload: bytes) -> bool:
        self._stats.offered += 1
        handle = None
        tmp_name = None
        try:
            fd, tmp_name = tempfile.mkstemp(dir=str(self._dir), prefix=".latest-", suffix=".tmp")
            handle = os.fdopen(fd, "wb")
            handle.write(payload)
            handle.flush()
            if self._fsync:
                os.fsync(handle.fileno())
            handle.close()
            handle = None
            self._replace_with_retry(tmp_name, self._target)
            tmp_name = None
            self._stats.delivered += 1
            self._stats.bytes_written += len(payload)
            return True
        except OSError as exc:
            self._stats.write_errors += 1
            self._stats.dropped_error += 1
            self._stats.last_error = f"{type(exc).__name__}: {exc}"
            return False
        finally:
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass
            if tmp_name is not None and os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    #: Backoffs for a contended replace, in seconds. Bounded and tiny: this runs only on the
    #: optional display path, after the gate already admitted the frame.
    _REPLACE_BACKOFF_S = (0.0005, 0.001, 0.002)

    def _replace_with_retry(self, source: str, target: Path) -> None:
        """``os.replace`` that survives a reader holding the destination open.

        CPython opens files without ``FILE_SHARE_DELETE``, so on Windows a viewer polling
        ``latest.json`` makes the rename fail with ``PermissionError`` even though both
        sides are healthy. Atomicity is unaffected - the destination is either the old
        complete frame or the new one - so the right response is a short retry, not a
        dropped frame and not a transport failure charged against the circuit breaker.
        """

        for index, delay in enumerate(self._REPLACE_BACKOFF_S):
            try:
                os.replace(source, target)
                if index:
                    self._stats.replace_contended += 1
                return
            except PermissionError:
                time.sleep(delay)
        os.replace(source, target)
        self._stats.replace_contended += 1

    def write_health(self, payload: bytes) -> bool:
        """Publish stream health even when no frame is eligible, so a quiet preview is
        distinguishable from a stalled producer."""

        try:
            fd, tmp_name = tempfile.mkstemp(dir=str(self._dir), prefix=".health-", suffix=".tmp")
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            os.replace(tmp_name, self._health)
            return True
        except OSError as exc:
            self._stats.last_error = f"{type(exc).__name__}: {exc}"
            return False

    def close(self) -> None:
        self._stats.closed = True

    @property
    def active(self) -> bool:
        return True

    @property
    def stats(self) -> SinkStats:
        return self._stats


class BoundedQueueSink:
    """Non-waiting bounded queue with latest-wins coalescing.

    ``put_nowait`` on a full queue raises ``queue.Full``; the newest frame then displaces
    the oldest by a single non-blocking ``get_nowait``. If that race is lost the frame is
    dropped and counted. Nothing here waits, and no exception escapes into the caller.

    ``multiprocessing.Queue`` reports ``qsize``/``full`` only approximately on some
    platforms, so those observations are never used as a correctness guarantee: the
    control flow depends solely on the ``Full`` exception. [E1]
    """

    def __init__(self, maxsize: int, *, factory: Any = None) -> None:
        if maxsize < 1:
            raise ValueError("BoundedQueueSink requires maxsize >= 1")
        self._queue = queue.Queue(maxsize=maxsize) if factory is None else factory(maxsize)
        self._stats = SinkStats()

    @property
    def queue(self) -> Any:
        return self._queue

    def offer(self, payload: bytes) -> bool:
        self._stats.offered += 1
        try:
            self._queue.put_nowait(payload)
            self._stats.delivered += 1
            self._stats.bytes_written += len(payload)
            return True
        except queue.Full:
            pass
        except (ValueError, OSError) as exc:
            self._stats.dropped_error += 1
            self._stats.last_error = f"{type(exc).__name__}: {exc}"
            return False
        # Latest-wins: displace the oldest queued display frame.
        try:
            self._queue.get_nowait()
            self._stats.coalesced += 1
        except queue.Empty:
            pass
        try:
            self._queue.put_nowait(payload)
            self._stats.delivered += 1
            self._stats.bytes_written += len(payload)
            return True
        except (queue.Full, ValueError, OSError):
            self._stats.dropped_full += 1
            return False

    def drain_latest(self) -> bytes | None:
        """Consumer side: return the newest queued frame, discarding older ones."""

        newest: bytes | None = None
        while True:
            try:
                newest = self._queue.get_nowait()
            except queue.Empty:
                return newest

    def close(self) -> None:
        self._stats.closed = True
        # A multiprocessing.Queue keeps a feeder thread alive until its buffer is flushed.
        # Cancelling the join prevents interpreter exit from waiting on a reader that has
        # already gone away; the dropped bytes are display frames only. [E1]
        cancel = getattr(self._queue, "cancel_join_thread", None)
        if callable(cancel):
            cancel()
        closer = getattr(self._queue, "close", None)
        if callable(closer):
            try:
                closer()
            except OSError:
                pass

    @property
    def active(self) -> bool:
        return True

    @property
    def stats(self) -> SinkStats:
        return self._stats


class CompositeSink:
    """Fan one frame out to several sinks. A failing sink never stops the others."""

    def __init__(self, *sinks: FrameSink) -> None:
        self._sinks = tuple(sinks)
        self._stats = SinkStats()

    def offer(self, payload: bytes) -> bool:
        self._stats.offered += 1
        delivered = False
        for sink in self._sinks:
            # This runs on a path reachable from a scientific step, so a sink that raises
            # must not escape and must not cost the remaining sinks their frame. The shipped
            # sinks absorb their own errors; a caller-supplied one need not.
            try:
                if sink.offer(payload):
                    delivered = True
            except Exception:
                self._stats.write_errors += 1
        if delivered:
            self._stats.delivered += 1
            self._stats.bytes_written += len(payload)
        else:
            self._stats.dropped_full += 1
        return delivered

    def close(self) -> None:
        for sink in self._sinks:
            try:
                sink.close()
            except Exception:
                self._stats.write_errors += 1
        self._stats.closed = True

    @property
    def active(self) -> bool:
        return any(getattr(sink, "active", True) for sink in self._sinks)

    @property
    def stats(self) -> SinkStats:
        return self._stats

    @property
    def sinks(self) -> tuple[FrameSink, ...]:
        return self._sinks


# --------------------------------------------------------------------------------------
# Cross-process viewer lease
# --------------------------------------------------------------------------------------


class MappedViewerLease:
    """Viewer lease shared through a memory-mapped 8-byte file.

    The producer opens and maps the file **once**, when the session is armed. The
    per-attempt read is then ``struct.unpack_from`` over a resident page: a memory load,
    not a file scan, a stat, a socket round trip or an RPC. That is what makes it legal on
    a path reached from ``env.step()``.

    Both ends must run on the same machine, which is already required because the viewer
    binds to loopback only. ``time.monotonic()`` is system-wide on Windows and Linux, so a
    deadline written by the server is comparable in the producer. A torn 8-byte read can
    only make one preview frame spuriously eligible or ineligible, which changes
    presentation and nothing else.
    """

    def __init__(self, path: str | os.PathLike[str], *, create: bool) -> None:
        self._path = Path(path)
        if create:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if not self._path.exists() or self._path.stat().st_size < _LEASE_STRUCT.size:
                with open(self._path, "wb") as handle:
                    handle.write(_LEASE_STRUCT.pack(0.0))
        self._file = open(self._path, "r+b")
        self._map = mmap.mmap(self._file.fileno(), _LEASE_STRUCT.size)

    @classmethod
    def in_directory(cls, directory: str | os.PathLike[str], *, create: bool) -> "MappedViewerLease":
        return cls(Path(directory) / _LEASE_FILE_NAME, create=create)

    @property
    def path(self) -> Path:
        return self._path

    def expires_at_monotonic(self) -> float:
        return _LEASE_STRUCT.unpack_from(self._map, 0)[0]

    def renew(self, timeout_s: float, *, now: float | None = None) -> None:
        deadline = (time.monotonic() if now is None else now) + float(timeout_s)
        _LEASE_STRUCT.pack_into(self._map, 0, deadline)

    def revoke(self) -> None:
        _LEASE_STRUCT.pack_into(self._map, 0, 0.0)

    def close(self) -> None:
        try:
            self._map.close()
        finally:
            self._file.close()

    def __enter__(self) -> "MappedViewerLease":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --------------------------------------------------------------------------------------
# Overload circuit breaker
# --------------------------------------------------------------------------------------


class OverloadBreaker:
    """Cheap breaker for transport failures and repeatedly excessive capture latency.

    It suspends optional presentation for a cooldown, emits one throttled diagnostic and
    nothing else. It never restarts training, never changes a scientific setting, and it
    does not claim to have measured a slowdown: only a benchmark reference can do that.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        latency_threshold_s: float = 0.25,
        latency_threshold_count: int = 5,
        cooldown_s: float = 30.0,
        diagnostic_interval_s: float = 60.0,
    ) -> None:
        self.failure_threshold = int(failure_threshold)
        self.latency_threshold_s = float(latency_threshold_s)
        self.latency_threshold_count = int(latency_threshold_count)
        self.cooldown_s = float(cooldown_s)
        self.diagnostic_interval_s = float(diagnostic_interval_s)
        self._failures = 0
        self._slow = 0
        self._trips = 0
        self._last_diagnostic = 0.0
        self.last_reason: str | None = None

    @property
    def trips(self) -> int:
        return self._trips

    def record(self, *, ok: bool, latency_s: float) -> str | None:
        """Update the breaker. Returns a diagnostic string when one should be logged."""

        if ok:
            self._failures = 0
        else:
            self._failures += 1
        if latency_s > self.latency_threshold_s:
            self._slow += 1
        else:
            self._slow = 0

        reason = None
        if self._failures >= self.failure_threshold:
            reason = f"transport_failures={self._failures}"
        elif self._slow >= self.latency_threshold_count:
            reason = f"capture_latency_s>{self.latency_threshold_s}x{self._slow}"
        if reason is None:
            return None

        self._failures = 0
        self._slow = 0
        self._trips += 1
        self.last_reason = reason
        now = time.monotonic()
        if (now - self._last_diagnostic) < self.diagnostic_interval_s:
            return None
        self._last_diagnostic = now
        return (
            f"research_support preview suspended for {self.cooldown_s:.0f}s ({reason}); "
            "presentation only, training unchanged"
        )


# --------------------------------------------------------------------------------------
# Consumer-side reader
# --------------------------------------------------------------------------------------


class LatestFrameReader:
    """Polling reader for :class:`LatestFrameFileSink`, used by the local server.

    Reading is a plain read of an atomically replaced file. A partially visible file
    cannot occur through ``os.replace``, but a truncated or malformed payload from an
    interrupted producer is still reported rather than raised.
    """

    def __init__(self, directory: str | os.PathLike[str]) -> None:
        self._dir = Path(directory)
        self._latest = self._dir / _LATEST_FILE_NAME
        self._health = self._dir / _HEALTH_FILE_NAME
        self._last_mtime_ns = -1
        self._lock = threading.Lock()

    @property
    def directory(self) -> Path:
        return self._dir

    def read(self) -> tuple[bytes | None, str | None]:
        """Return ``(payload, error)``. ``(None, None)`` means nothing published yet."""

        with self._lock:
            try:
                stat = self._latest.stat()
            except FileNotFoundError:
                return None, None
            except OSError as exc:
                return None, f"{type(exc).__name__}: {exc}"
            try:
                payload = self._latest.read_bytes()
            except OSError as exc:
                return None, f"{type(exc).__name__}: {exc}"
            self._last_mtime_ns = stat.st_mtime_ns
            return payload, None

    def read_health(self) -> bytes | None:
        try:
            return self._health.read_bytes()
        except OSError:
            return None

    @property
    def last_mtime_ns(self) -> int:
        return self._last_mtime_ns

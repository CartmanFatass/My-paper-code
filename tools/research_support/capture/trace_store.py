"""Immutable chunked trace files plus a small index.

A recorded trajectory is written as append-only JSON Lines chunks with a separate index,
rather than one growing JSON document, so that:

* a reader can seek to a time or a sequence without parsing the whole trace;
* an interrupted producer leaves a trace that is valid up to its last complete line, and
  the reader reports ``INCOMPLETE_TRACE`` instead of failing;
* retention is a bounded number of chunks and bytes, set explicitly.

Recording exists only inside an explicitly enabled session. Under ``profile=off`` no
writer is constructed, so this module is never reached.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping

from ..records import TRACE_INDEX_SCHEMA, SCENE_SCHEMA, dumps, loads, validate_scene_json

_MANIFEST_NAME = "trace_manifest.json"
_INDEX_NAME = "trace_index.json"
_CHUNK_DIR = "chunks"


#: Trace lifecycle states. Plain strings so a partially written index remains readable by
#: an older consumer that does not know a newly added state.
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_INCOMPLETE = "incomplete"
STATUS_BUDGET_EXHAUSTED = "budget_exhausted"
STATUS_ERROR = "error"


@dataclass
class ChunkIndexEntry:
    name: str
    n_frames: int
    first_sequence: int
    last_sequence: int
    first_time_s: float | None
    last_time_s: float | None
    n_bytes: int
    sha256: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_frames": int(self.n_frames),
            "first_sequence": int(self.first_sequence),
            "last_sequence": int(self.last_sequence),
            "first_time_s": self.first_time_s,
            "last_time_s": self.last_time_s,
            "n_bytes": int(self.n_bytes),
            "sha256": self.sha256,
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "ChunkIndexEntry":
        return cls(
            name=str(payload["name"]),
            n_frames=int(payload["n_frames"]),
            first_sequence=int(payload["first_sequence"]),
            last_sequence=int(payload["last_sequence"]),
            first_time_s=payload.get("first_time_s"),
            last_time_s=payload.get("last_time_s"),
            n_bytes=int(payload.get("n_bytes", 0)),
            sha256=payload.get("sha256"),
        )


@dataclass
class TraceIndex:
    trace_id: str
    status: str = STATUS_OPEN
    chunks: list[ChunkIndexEntry] = field(default_factory=list)
    n_frames: int = 0
    n_bytes: int = 0
    first_time_s: float | None = None
    last_time_s: float | None = None
    gaps: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    schema: str = TRACE_INDEX_SCHEMA

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "trace_id": self.trace_id,
            "status": self.status,
            "n_frames": int(self.n_frames),
            "n_bytes": int(self.n_bytes),
            "first_time_s": self.first_time_s,
            "last_time_s": self.last_time_s,
            "chunks": [c.to_json() for c in self.chunks],
            "gaps": list(self.gaps),
            "errors": list(self.errors),
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, Any]) -> "TraceIndex":
        return cls(
            trace_id=str(payload.get("trace_id", "unknown")),
            status=str(payload.get("status", STATUS_OPEN)),
            chunks=[ChunkIndexEntry.from_json(c) for c in payload.get("chunks", ())],
            n_frames=int(payload.get("n_frames", 0)),
            n_bytes=int(payload.get("n_bytes", 0)),
            first_time_s=payload.get("first_time_s"),
            last_time_s=payload.get("last_time_s"),
            gaps=list(payload.get("gaps", ())),
            errors=list(payload.get("errors", ())),
            schema=str(payload.get("schema", TRACE_INDEX_SCHEMA)),
        )


class TraceWriter:
    """Append-only chunked writer owned by one diagnostic invocation.

    The writer never raises into the producer: a full disk, a permission error or a
    revoked directory sets ``status`` to ``error``, retains the message, and reports
    ``False`` from :meth:`append`. The affected analysis is then marked incomplete rather
    than being treated as a lossless recording.
    """

    def __init__(
        self,
        directory: str | os.PathLike[str],
        *,
        trace_id: str,
        manifest: Mapping[str, Any],
        chunk_frames: int = 64,
        max_bytes: int = 256 * 1024 * 1024,
    ) -> None:
        self._dir = Path(directory)
        self._chunk_dir = self._dir / _CHUNK_DIR
        self._chunk_dir.mkdir(parents=True, exist_ok=True)
        self._chunk_frames = max(1, int(chunk_frames))
        self._max_bytes = int(max_bytes)
        self._index = TraceIndex(trace_id=str(trace_id))
        self._handle: Any = None
        self._current: ChunkIndexEntry | None = None
        self._digest: Any = None
        self._error: str | None = None
        self._last_sequence: int | None = None
        manifest_payload = dict(manifest)
        manifest_payload.setdefault("trace_id", str(trace_id))
        manifest_payload.setdefault("scene_schema", SCENE_SCHEMA)
        self._write_json(self._dir / _MANIFEST_NAME, manifest_payload)
        self._flush_index()

    # Properties ------------------------------------------------------------------------

    @property
    def directory(self) -> Path:
        return self._dir

    @property
    def index(self) -> TraceIndex:
        return self._index

    @property
    def status(self) -> str:
        return self._index.status

    @property
    def error(self) -> str | None:
        return self._error

    # Writing ---------------------------------------------------------------------------

    def append(self, payload: bytes, *, sequence: int, time_s: float | None) -> bool:
        """Write one frame. Returns ``False`` when the frame was not persisted."""

        if self._index.status in (STATUS_ERROR, STATUS_BUDGET_EXHAUSTED, STATUS_CLOSED):
            return False
        if self._index.n_bytes + len(payload) > self._max_bytes:
            self._index.status = STATUS_BUDGET_EXHAUSTED
            self._index.errors.append(
                f"trace byte budget {self._max_bytes} reached before sequence {sequence}"
            )
            self._close_chunk()
            self._flush_index()
            return False
        if b"\n" in payload:
            payload = payload.replace(b"\n", b" ")
        try:
            if self._handle is None or self._current is None or (
                self._current.n_frames >= self._chunk_frames
            ):
                self._open_chunk(sequence)
            assert self._handle is not None and self._current is not None
            self._handle.write(payload)
            self._handle.write(b"\n")
            self._digest.update(payload)
            self._digest.update(b"\n")
            written = len(payload) + 1
            self._current.n_frames += 1
            self._current.last_sequence = int(sequence)
            self._current.n_bytes += written
            if self._current.first_time_s is None:
                self._current.first_time_s = time_s
            self._current.last_time_s = time_s
            self._index.n_frames += 1
            self._index.n_bytes += written
            if self._index.first_time_s is None:
                self._index.first_time_s = time_s
            self._index.last_time_s = time_s
            if self._last_sequence is not None and sequence != self._last_sequence + 1:
                self._index.gaps.append(
                    {
                        "after_sequence": int(self._last_sequence),
                        "next_sequence": int(sequence),
                        "missing": int(sequence - self._last_sequence - 1),
                    }
                )
            self._last_sequence = int(sequence)
            return True
        except OSError as exc:
            self._error = f"{type(exc).__name__}: {exc}"
            self._index.status = STATUS_ERROR
            self._index.errors.append(self._error)
            self._safe_close_handle()
            self._flush_index()
            return False

    def note_gap(self, *, after_sequence: int, reason: str, count: int = 1) -> None:
        """Record that frames were refused, so a reader sees an explicit gap."""

        self._index.gaps.append(
            {
                "after_sequence": int(after_sequence),
                "reason": reason,
                "missing": int(count),
            }
        )

    def flush(self) -> None:
        if self._handle is not None:
            try:
                self._handle.flush()
            except OSError as exc:
                self._error = f"{type(exc).__name__}: {exc}"
        self._flush_index()

    def close(self, *, status: str = STATUS_CLOSED) -> TraceIndex:
        self._close_chunk()
        if self._index.status not in (STATUS_ERROR, STATUS_BUDGET_EXHAUSTED):
            self._index.status = status
        self._flush_index()
        return self._index

    def __enter__(self) -> "TraceWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close(status=STATUS_INCOMPLETE if exc_type is not None else STATUS_CLOSED)

    # Internals -------------------------------------------------------------------------

    def _open_chunk(self, sequence: int) -> None:
        self._close_chunk()
        name = f"chunk-{len(self._index.chunks):05d}.jsonl"
        self._current = ChunkIndexEntry(
            name=name,
            n_frames=0,
            first_sequence=int(sequence),
            last_sequence=int(sequence),
            first_time_s=None,
            last_time_s=None,
            n_bytes=0,
        )
        self._digest = hashlib.sha256()
        self._handle = open(self._chunk_dir / name, "wb")
        self._index.chunks.append(self._current)

    def _close_chunk(self) -> None:
        if self._handle is None:
            return
        try:
            self._handle.flush()
            self._handle.close()
        except OSError as exc:
            self._error = f"{type(exc).__name__}: {exc}"
        self._handle = None
        if self._current is not None and self._digest is not None:
            self._current.sha256 = "sha256:" + self._digest.hexdigest()
        self._current = None
        self._digest = None

    def _safe_close_handle(self) -> None:
        if self._handle is not None:
            try:
                self._handle.close()
            except OSError:
                pass
            self._handle = None

    def _flush_index(self) -> None:
        try:
            self._write_json(self._dir / _INDEX_NAME, self._index.to_json())
        except OSError as exc:
            self._error = f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(dumps(payload, indent=2))
        os.replace(tmp, path)


@dataclass
class TraceReadResult:
    """Everything a consumer needs to know about a trace it just opened."""

    trace_id: str
    manifest: dict[str, Any]
    index: TraceIndex
    frames: list[dict[str, Any]]
    status: str
    problems: list[str] = field(default_factory=list)
    truncated_after_sequence: int | None = None

    @property
    def complete(self) -> bool:
        return self.status == STATUS_CLOSED and not self.problems


class TraceReader:
    """Reads a trace directory, tolerating an interrupted producer.

    A malformed or partially written final line stops the read and sets
    ``INCOMPLETE_TRACE``; every frame before it remains usable. A frame whose schema does
    not match is reported by sequence rather than silently skipped.
    """

    def __init__(self, directory: str | os.PathLike[str]) -> None:
        self._dir = Path(directory)

    @property
    def directory(self) -> Path:
        return self._dir

    def read_manifest(self) -> dict[str, Any]:
        path = self._dir / _MANIFEST_NAME
        if not path.exists():
            return {}
        try:
            return loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def read_index(self) -> TraceIndex | None:
        path = self._dir / _INDEX_NAME
        if not path.exists():
            return None
        try:
            return TraceIndex.from_json(loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError):
            return None

    def iter_frames(self) -> Iterator[tuple[dict[str, Any] | None, str | None]]:
        """Yield ``(frame, problem)`` pairs in recorded order."""

        chunk_dir = self._dir / _CHUNK_DIR
        index = self.read_index()
        if index is not None and index.chunks:
            names = [entry.name for entry in index.chunks]
        elif chunk_dir.is_dir():
            names = sorted(p.name for p in chunk_dir.glob("chunk-*.jsonl"))
        else:
            names = []
        for name in names:
            path = chunk_dir / name
            if not path.exists():
                yield None, f"missing chunk file: {name}"
                continue
            try:
                raw = path.read_bytes()
            except OSError as exc:
                yield None, f"unreadable chunk {name}: {type(exc).__name__}: {exc}"
                continue
            lines = raw.split(b"\n")
            # A trailing newline produces one empty final element; a truncated write does
            # not, so a non-empty final element means the last line is incomplete.
            trailing_incomplete = bool(lines and lines[-1].strip())
            for position, line in enumerate(lines):
                if not line.strip():
                    continue
                is_last = position == len(lines) - 1
                try:
                    payload = loads(line)
                except (ValueError, json.JSONDecodeError):
                    if is_last and trailing_incomplete:
                        yield None, f"incomplete final line in {name}"
                        return
                    yield None, f"malformed line {position} in {name}"
                    continue
                if not isinstance(payload, dict):
                    yield None, f"non-object line {position} in {name}"
                    continue
                problems = validate_scene_json(payload)
                if problems:
                    sequence = (payload.get("identity") or {}).get("sequence")
                    yield payload, f"frame sequence={sequence}: " + "; ".join(problems)
                else:
                    yield payload, None

    def read(self, *, limit: int | None = None) -> TraceReadResult:
        manifest = self.read_manifest()
        index = self.read_index() or TraceIndex(trace_id=str(manifest.get("trace_id", "unknown")))
        frames: list[dict[str, Any]] = []
        problems: list[str] = []
        truncated_after: int | None = None
        for frame, problem in self.iter_frames():
            if problem is not None:
                problems.append(problem)
                if problem.startswith("incomplete final line"):
                    truncated_after = (
                        int((frames[-1].get("identity") or {}).get("sequence", -1))
                        if frames
                        else None
                    )
                    break
            if frame is not None:
                frames.append(frame)
                if limit is not None and len(frames) >= limit:
                    break
        status = index.status
        # Anything short of a cleanly closed index with no parse problems is INCOMPLETE. The
        # earlier form left a trace whose very first line was truncated reporting `open`,
        # because nothing had been read yet to set `truncated_after`.
        if problems or truncated_after is not None or status == STATUS_OPEN:
            status = STATUS_INCOMPLETE
        return TraceReadResult(
            trace_id=index.trace_id,
            manifest=manifest,
            index=index,
            frames=frames,
            status=status,
            problems=problems,
            truncated_after_sequence=truncated_after,
        )

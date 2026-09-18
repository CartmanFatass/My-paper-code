"""Tests for ``tools/research_support/capture/trace_store.py``.

A trace is the only durable record the suite produces, so the properties under test are:

* chunking and the index are what the reader is promised;
* a write failure never raises into the producer, it degrades the trace to ``error``;
* refused frames become an explicit gap, so decimation is visible rather than silent;
* an interrupted producer yields a trace that reads up to its last complete line and
  *reports* the truncation instead of dropping it quietly.
"""

from __future__ import annotations

import builtins
import json
import pathlib
import sys

import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from tools.research_support import records as R  # noqa: E402
from tools.research_support.capture import trace_store as TS  # noqa: E402


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _frame(sequence: int, time_s: float) -> R.SceneFrame:
    entity = R.EntityId(kind=R.EntityKind.UAV, slot=0, label="uav-0")
    return R.SceneFrame(
        identity=R.SceneIdentity(
            run_id="run-1", trace_id="trace-1", episode_id="ep-1", world_id="w-1",
            lane_id=0, sequence=sequence,
        ),
        clock=R.SceneClock(
            simulation_time_s=time_s, geometry_time_s=time_s, decision_step=sequence,
            capture_wall_time_utc="2026-09-18T00:00:00Z", producer_monotonic_s=float(sequence),
        ),
        provenance=R.SceneProvenance(
            route="unit_test", environment_id="fixture",
            source_kind=R.SourceKind.SYNTHETIC_FIXTURE, policy_kind=R.PolicyKind.RULE_CONTROLLER,
            information_condition="privileged_truth", frame_kind=R.FrameKind.TRANSITION,
            capture_resolution="decision_boundary",
        ),
        geometry=R.SceneGeometry(bounds_m=(0.0, 0.0, 1000.0, 1000.0)),
        capability=R.SceneCapability(has_uav_positions=True),
        uavs=(R.UavState(entity=entity, position_m=(1.0 * sequence, 2.0, 120.0)),),
    )


def _payload(sequence: int, time_s: float) -> bytes:
    return _frame(sequence, time_s).to_bytes()


def _writer(directory: pathlib.Path, **kwargs: object) -> TS.TraceWriter:
    kwargs.setdefault("trace_id", "trace-1")
    kwargs.setdefault("manifest", {"route": "unit_test", "controller": "fixture"})
    return TS.TraceWriter(directory, **kwargs)  # type: ignore[arg-type]


def _write_frames(writer: TS.TraceWriter, count: int, *, start: int = 0) -> None:
    for index in range(start, start + count):
        assert writer.append(_payload(index, float(index)), sequence=index, time_s=float(index))


class _FailingHandle:
    """Stands in for a file handle on a full disk."""

    def __init__(self) -> None:
        self.closed = False

    def write(self, data: bytes) -> int:
        raise OSError(28, "No space left on device")

    def flush(self) -> None:
        raise OSError(28, "No space left on device")

    def close(self) -> None:
        self.closed = True


# --------------------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------------------


def test_writer_writes_a_manifest_and_index_before_any_frame(tmp_path: pathlib.Path) -> None:
    writer = _writer(tmp_path / "trace")
    try:
        manifest = json.loads((tmp_path / "trace" / "trace_manifest.json").read_text("utf-8"))
        assert manifest["trace_id"] == "trace-1"
        assert manifest["scene_schema"] == R.SCENE_SCHEMA
        assert manifest["route"] == "unit_test"

        index = json.loads((tmp_path / "trace" / "trace_index.json").read_text("utf-8"))
        assert index["schema"] == R.TRACE_INDEX_SCHEMA
        assert index["status"] == TS.STATUS_OPEN
        assert index["n_frames"] == 0
        assert index["chunks"] == []
    finally:
        writer.close()


def test_writer_chunks_at_chunk_frames_and_indexes_them(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=3)
    _write_frames(writer, 7)
    index = writer.close()

    assert index.status == TS.STATUS_CLOSED
    assert index.n_frames == 7
    assert [chunk.n_frames for chunk in index.chunks] == [3, 3, 1]
    assert [chunk.name for chunk in index.chunks] == [
        "chunk-00000.jsonl", "chunk-00001.jsonl", "chunk-00002.jsonl",
    ]
    assert [(c.first_sequence, c.last_sequence) for c in index.chunks] == [(0, 2), (3, 5), (6, 6)]
    assert index.first_time_s == 0.0 and index.last_time_s == 6.0

    chunk_dir = directory / "chunks"
    assert sorted(p.name for p in chunk_dir.glob("*.jsonl")) == [c.name for c in index.chunks]
    for chunk in index.chunks:
        raw = (chunk_dir / chunk.name).read_bytes()
        assert raw.endswith(b"\n")
        assert len(raw.strip().split(b"\n")) == chunk.n_frames
        assert chunk.n_bytes == len(raw)
        assert chunk.sha256 is not None and chunk.sha256.startswith("sha256:")

    on_disk = TS.TraceIndex.from_json(
        json.loads((directory / "trace_index.json").read_text("utf-8"))
    )
    assert on_disk.status == TS.STATUS_CLOSED
    assert on_disk.n_frames == 7
    assert len(on_disk.chunks) == 3


def test_writer_keeps_one_frame_per_line(tmp_path: pathlib.Path) -> None:
    """A newline inside a payload would corrupt the JSON Lines framing."""

    directory = tmp_path / "trace"
    writer = _writer(directory)
    assert writer.append(b'{"a": "line1\nline2"}', sequence=0, time_s=0.0) is True
    writer.close()
    raw = (directory / "chunks" / "chunk-00000.jsonl").read_bytes()
    assert raw == b'{"a": "line1 line2"}\n'


def test_writer_never_raises_into_the_producer_when_the_handle_fails(
    tmp_path: pathlib.Path,
) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=64)
    assert writer.append(_payload(0, 0.0), sequence=0, time_s=0.0) is True

    writer._handle.close()  # type: ignore[union-attr]
    writer._handle = _FailingHandle()  # the disk fills under the producer

    assert writer.append(_payload(1, 1.0), sequence=1, time_s=1.0) is False
    assert writer.status == TS.STATUS_ERROR
    assert "No space left on device" in (writer.error or "")
    assert any("No space left" in message for message in writer.index.errors)

    # A writer in error stays refused rather than half-recovering.
    assert writer.append(_payload(2, 2.0), sequence=2, time_s=2.0) is False
    index = writer.close()
    assert index.status == TS.STATUS_ERROR

    result = TS.TraceReader(directory).read()
    assert result.status == TS.STATUS_ERROR
    assert result.complete is False
    assert len(result.frames) == 1, "frames written before the failure stay readable"


def test_writer_never_raises_when_the_filesystem_refuses_a_new_chunk(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory)

    def _refuse(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(builtins, "open", _refuse)
    try:
        refused = writer.append(_payload(0, 0.0), sequence=0, time_s=0.0)
    finally:
        monkeypatch.undo()

    assert refused is False
    assert writer.status == TS.STATUS_ERROR
    assert "Permission denied" in (writer.error or "")
    writer.close()


def test_note_gap_records_refused_frames_with_counters(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory)
    _write_frames(writer, 2)
    writer.note_gap(after_sequence=1, reason="gate_refused:wall_gate", count=37)
    _write_frames(writer, 1, start=2)
    writer.close()

    index = TS.TraceReader(directory).read_index()
    assert index is not None
    assert index.gaps == [
        {"after_sequence": 1, "reason": "gate_refused:wall_gate", "missing": 37}
    ]
    assert index.n_frames == 3, "a gap marker is not a frame"


def test_a_sequence_jump_is_recorded_as_an_explicit_gap(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory)
    for sequence in (0, 1, 5):
        writer.append(_payload(sequence, float(sequence)), sequence=sequence, time_s=float(sequence))
    writer.close()

    index = TS.TraceReader(directory).read_index()
    assert index is not None
    assert index.gaps == [{"after_sequence": 1, "next_sequence": 5, "missing": 3}]


def test_byte_budget_stops_the_trace_and_says_so(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    size = len(_payload(0, 0.0)) + 1
    writer = _writer(directory, max_bytes=2 * size + 1)
    assert writer.append(_payload(0, 0.0), sequence=0, time_s=0.0) is True
    assert writer.append(_payload(1, 1.0), sequence=1, time_s=1.0) is True
    assert writer.append(_payload(2, 2.0), sequence=2, time_s=2.0) is False

    assert writer.status == TS.STATUS_BUDGET_EXHAUSTED
    assert any("byte budget" in message for message in writer.index.errors)
    writer.close()

    result = TS.TraceReader(directory).read()
    assert result.status == TS.STATUS_BUDGET_EXHAUSTED
    assert len(result.frames) == 2
    assert result.complete is False


def test_context_manager_marks_an_interrupted_trace_incomplete(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    with pytest.raises(RuntimeError, match="producer died"):
        with _writer(directory) as writer:
            _write_frames(writer, 2)
            raise RuntimeError("producer died")

    result = TS.TraceReader(directory).read()
    assert result.status == TS.STATUS_INCOMPLETE
    assert len(result.frames) == 2


# --------------------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------------------


def test_reader_returns_closed_for_a_complete_trace(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=2)
    _write_frames(writer, 5)
    writer.close()

    result = TS.TraceReader(directory).read()
    assert result.status == TS.STATUS_CLOSED
    assert result.complete is True
    assert result.problems == []
    assert result.truncated_after_sequence is None
    assert result.trace_id == "trace-1"
    assert result.manifest["route"] == "unit_test"
    assert [f["identity"]["sequence"] for f in result.frames] == [0, 1, 2, 3, 4]
    assert result.index.n_frames == 5

    limited = TS.TraceReader(directory).read(limit=2)
    assert len(limited.frames) == 2


def test_reader_reports_an_index_the_producer_never_closed(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory)
    _write_frames(writer, 3)
    writer.flush()  # index on disk still says "open": the producer vanished

    result = TS.TraceReader(directory).read()
    assert result.status == TS.STATUS_INCOMPLETE
    assert result.complete is False
    assert len(result.frames) == 3
    writer.close()


def test_a_truncated_trailing_line_is_reported_not_silently_dropped(
    tmp_path: pathlib.Path,
) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=64)
    _write_frames(writer, 3)
    writer.close()

    chunk = directory / "chunks" / "chunk-00000.jsonl"
    lines = chunk.read_bytes().split(b"\n")
    assert lines[-1] == b"" and len(lines) == 4
    half = lines[2][: len(lines[2]) // 2]
    chunk.write_bytes(b"\n".join(lines[:2]) + b"\n" + half)

    result = TS.TraceReader(directory).read()
    assert result.status == TS.STATUS_INCOMPLETE
    assert result.complete is False
    assert len(result.frames) == 2
    assert result.truncated_after_sequence == 1
    assert any(p.startswith("incomplete final line in chunk-00000.jsonl") for p in result.problems)


def test_a_malformed_interior_line_is_reported_and_the_read_continues(
    tmp_path: pathlib.Path,
) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=64)
    _write_frames(writer, 3)
    writer.close()

    chunk = directory / "chunks" / "chunk-00000.jsonl"
    lines = chunk.read_bytes().split(b"\n")
    lines[1] = b"{not json at all"
    chunk.write_bytes(b"\n".join(lines))

    result = TS.TraceReader(directory).read()
    assert len(result.frames) == 2
    assert any(p.startswith("malformed line 1 in chunk-00000.jsonl") for p in result.problems)
    assert result.status == TS.STATUS_INCOMPLETE


def test_a_frame_violating_the_scene_contract_is_reported_by_sequence(
    tmp_path: pathlib.Path,
) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory)
    _write_frames(writer, 1)
    bad = _frame(1, 1.0).to_json()
    bad["schema"] = "research_support.scene.0"
    writer.append(R.dumps(bad).encode("utf-8"), sequence=1, time_s=1.0)
    writer.close()

    result = TS.TraceReader(directory).read()
    assert len(result.frames) == 2, "a contract-violating frame is reported, not dropped"
    assert any(p.startswith("frame sequence=1: schema mismatch") for p in result.problems)
    assert result.status == TS.STATUS_INCOMPLETE


def test_reader_reports_a_missing_chunk_file(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=2)
    _write_frames(writer, 4)
    writer.close()
    (directory / "chunks" / "chunk-00001.jsonl").unlink()

    result = TS.TraceReader(directory).read()
    assert any(p == "missing chunk file: chunk-00001.jsonl" for p in result.problems)
    assert len(result.frames) == 2


def test_reader_tolerates_an_empty_or_absent_directory(tmp_path: pathlib.Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = TS.TraceReader(empty).read()
    assert result.frames == []
    assert result.manifest == {}
    assert result.trace_id == "unknown"
    assert result.status == TS.STATUS_INCOMPLETE  # an index-less trace is not "closed"

    absent = TS.TraceReader(tmp_path / "does_not_exist")
    assert absent.read_manifest() == {}
    assert absent.read_index() is None
    assert absent.read().frames == []


def test_reader_falls_back_to_globbing_chunks_without_an_index(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory, chunk_frames=2)
    _write_frames(writer, 4)
    writer.close()
    (directory / "trace_index.json").unlink()

    result = TS.TraceReader(directory).read()
    assert [f["identity"]["sequence"] for f in result.frames] == [0, 1, 2, 3]


def test_reader_survives_a_corrupt_index(tmp_path: pathlib.Path) -> None:
    directory = tmp_path / "trace"
    writer = _writer(directory)
    _write_frames(writer, 2)
    writer.close()
    (directory / "trace_index.json").write_text("{not json", encoding="utf-8")
    (directory / "trace_manifest.json").write_text("{not json", encoding="utf-8")

    reader = TS.TraceReader(directory)
    assert reader.read_index() is None
    assert reader.read_manifest() == {}
    assert len(reader.read().frames) == 2


def test_index_round_trips_through_json(tmp_path: pathlib.Path) -> None:
    index = TS.TraceIndex(
        trace_id="t",
        status=TS.STATUS_CLOSED,
        chunks=[
            TS.ChunkIndexEntry(
                name="chunk-00000.jsonl", n_frames=2, first_sequence=0, last_sequence=1,
                first_time_s=0.0, last_time_s=1.0, n_bytes=128, sha256="sha256:abc",
            )
        ],
        n_frames=2,
        n_bytes=128,
        gaps=[{"after_sequence": 1, "reason": "gate", "missing": 2}],
    )
    restored = TS.TraceIndex.from_json(R.loads(R.dumps(index.to_json())))
    assert restored == index

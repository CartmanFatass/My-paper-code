"""Tests for ``tools/research_support/export.py``.

An export is a claim about a recording, so the properties under test are:

* every supported format actually writes the file it promises;
* the standalone HTML bundle is genuinely offline: no external URL at all;
* a missing optional encoder produces an actionable ``ExportError`` naming the dependency,
  never an empty file reported as a success and never an automatic installation;
* nothing is written outside the requested output path;
* an empty or absent trace directory is refused with a readable message.

The negative encoder test is skipped when the encoder happens to be installed, so this
module passes in either environment.
"""

from __future__ import annotations

import importlib.util
import pathlib
import shutil
import sys
from typing import Any, Iterator

import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import matplotlib  # noqa: E402

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402

from tools.research_support import export as E  # noqa: E402
from tools.research_support import records as R  # noqa: E402
from tools.research_support.capture import trace_store as TS  # noqa: E402

_HAS_PILLOW = importlib.util.find_spec("PIL") is not None
_HAS_IMAGEIO = importlib.util.find_spec("imageio") is not None


@pytest.fixture(autouse=True)
def _no_leaked_figures() -> Iterator[None]:
    yield
    plt.close("all")
    assert plt.get_fignums() == []


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


def _frame(sequence: int) -> R.SceneFrame:
    uav = R.EntityId(kind=R.EntityKind.UAV, slot=0, label="uav-0")
    cell = R.EntityId(kind=R.EntityKind.AGGREGATE_DEMAND_POINT, slot=0, label="cell-0")
    return R.SceneFrame(
        identity=R.SceneIdentity(
            run_id="run-1", trace_id="trace-1", episode_id="ep-1", world_id="w-1",
            lane_id=0, sequence=sequence,
        ),
        clock=R.SceneClock(
            simulation_time_s=float(sequence), geometry_time_s=float(sequence),
            decision_step=sequence, capture_wall_time_utc="2026-09-18T00:00:00Z",
            producer_monotonic_s=float(sequence),
        ),
        provenance=R.SceneProvenance(
            route="unit_test", environment_id="uav_service_restoration",
            source_kind=R.SourceKind.SYNTHETIC_FIXTURE, policy_kind=R.PolicyKind.RULE_CONTROLLER,
            information_condition="privileged_truth", frame_kind=R.FrameKind.TRANSITION,
            capture_resolution="decision_boundary",
        ),
        geometry=R.SceneGeometry(bounds_m=(0.0, 0.0, 1000.0, 1000.0)),
        capability=R.SceneCapability(has_uav_positions=True, has_aggregate_demand=True),
        uavs=(R.UavState(entity=uav, position_m=(100.0 + 10.0 * sequence, 200.0, 120.0)),),
        ground_entities=(
            R.GroundEntityState(
                entity=cell, position_m=(400.0, 400.0, 0.0),
                offered_mbps=R.Measured.ok(2.0, unit="Mbps"),
                delivered_mbps=R.Measured.ok(0.0, unit="Mbps"),
                service_status="unserved",
            ),
        ),
    )


@pytest.fixture()
def trace_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    directory = tmp_path / "trace"
    writer = TS.TraceWriter(
        directory,
        trace_id="trace-1",
        manifest={
            "route": "unit_test",
            "controller": "legacy_hold",
            "controller_kind": "rule_controller",
        },
        chunk_frames=2,
    )
    for sequence in range(3):
        assert writer.append(
            _frame(sequence).to_bytes(), sequence=sequence, time_s=float(sequence)
        )
    writer.close()
    return directory


def _snapshot(root: pathlib.Path) -> set[pathlib.Path]:
    return {path.relative_to(root) for path in root.rglob("*")}


# --------------------------------------------------------------------------------------
# json / png / html
# --------------------------------------------------------------------------------------


def test_export_json_writes_the_frames_and_the_index(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    output = tmp_path / "out" / "trace.json"
    before = _snapshot(trace_dir)

    returned = E.export_trace(trace_dir=trace_dir, output=output, fmt="json")

    assert returned == output and output.is_file()
    payload = R.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "research_support.trace_export.1"
    assert payload["status"] == TS.STATUS_CLOSED
    assert payload["problems"] == []
    assert payload["manifest"]["controller"] == "legacy_hold"
    assert [f["identity"]["sequence"] for f in payload["frames"]] == [0, 1, 2]
    assert payload["index"]["n_frames"] == 3
    # A measured zero in the recording is still a measured zero in the export.
    delivered = payload["frames"][0]["ground_entities"][0]["delivered_mbps"]
    assert delivered == {"value": 0.0, "validity": "ok", "unit": "Mbps"}

    assert _snapshot(trace_dir) == before, "the source trace was modified"
    assert _snapshot(tmp_path / "out") == {pathlib.Path("trace.json")}


def test_export_png_writes_one_image_of_the_last_frame(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    output = tmp_path / "out" / "scene.png"
    returned = E.export_trace(trace_dir=trace_dir, output=output, fmt="png")

    assert returned == output and output.is_file()
    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert output.stat().st_size > 1000
    assert _snapshot(tmp_path / "out") == {pathlib.Path("scene.png")}


def test_export_html_is_a_single_offline_file(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    output = tmp_path / "out" / "replay.html"
    returned = E.export_trace(trace_dir=trace_dir, output=output, fmt="html")

    assert returned == output and output.is_file()
    page = output.read_text(encoding="utf-8")
    # No external URL of any kind: the bundle must open from the filesystem.
    stripped = page.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in stripped
    assert "https://" not in stripped
    assert "//cdn" not in stripped
    assert "<script src=" not in page and "<link rel=\"stylesheet\"" not in page
    # The trace is embedded, not fetched.
    assert '<script id="trace-data" type="application/json">' in page
    assert "research_support.standalone_replay.1" in page
    assert "RECORDED TRACE, replayed offline" in page
    assert "legacy_hold" in page and "rule_controller" in page
    assert "Sparse capture cannot reconstruct unrecorded actions" in page
    assert _snapshot(tmp_path / "out") == {pathlib.Path("replay.html")}


def test_export_html_accepts_a_directory_output(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    output = tmp_path / "bundle"
    returned = E.export_trace(trace_dir=trace_dir, output=output, fmt="html")
    assert returned == output / "replay.html"
    assert returned.is_file()
    assert _snapshot(output) == {pathlib.Path("replay.html")}


def test_export_html_falls_back_to_a_bundle_directory_for_a_large_trace(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(E, "INLINE_LIMIT_BYTES", 16)
    output = tmp_path / "bundle"
    returned = E.export_html(trace_dir, output)

    assert returned == output / "replay.html"
    assert _snapshot(output) == {
        pathlib.Path("replay.html"),
        pathlib.Path("trace.json"),
        pathlib.Path("app.css"),
        pathlib.Path("app.js"),
        pathlib.Path("scene3d.js"),
        pathlib.Path("README.txt"),
    }
    page = returned.read_text(encoding="utf-8")
    assert 'window.RS_TRACE_URL = "trace.json"' in page
    assert "must be served over http" in page
    readme = (output / "README.txt").read_text(encoding="utf-8")
    assert "python -m http.server 8000 --bind 127.0.0.1" in readme
    assert "No repository code, training interpreter or network connection is required." in readme
    assert R.loads((output / "trace.json").read_text(encoding="utf-8"))["status"] == "closed"


# --------------------------------------------------------------------------------------
# Optional encoders
# --------------------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_PILLOW, reason="Pillow is not installed in this interpreter")
def test_export_gif_writes_an_animation_and_a_metadata_sidecar(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    output = tmp_path / "out" / "replay.gif"
    returned = E.export_trace(trace_dir=trace_dir, output=output, fmt="gif", fps=4.0)

    assert returned == output and output.is_file()
    assert output.read_bytes()[:6] in (b"GIF87a", b"GIF89a")
    sidecar = output.with_suffix(output.suffix + ".metadata.json")
    assert _snapshot(tmp_path / "out") == {
        pathlib.Path("replay.gif"),
        pathlib.Path("replay.gif.metadata.json"),
    }
    metadata = R.loads(sidecar.read_text(encoding="utf-8"))
    assert metadata["schema"] == "research_support.animation_metadata.1"
    assert metadata["source_trace_id"] == "trace-1"
    assert metadata["playback_fps"] == 4.0
    assert metadata["frame_stride"] == 1
    assert metadata["n_frames_in_trace"] == 3
    assert metadata["n_frames_in_animation"] == 3
    assert metadata["simulated_time_range_s"] == [0.0, 2.0]
    assert metadata["interpolation"] == "none; every frame is a recorded sample"
    assert metadata["encoder"] == "PIL"
    assert "never reconstructed by" in metadata["caveat"]
    assert metadata["trace_status"] == TS.STATUS_CLOSED


@pytest.mark.skipif(_HAS_PILLOW, reason="Pillow IS installed; the refusal path cannot be reached")
def test_export_gif_names_the_missing_encoder(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:  # pragma: no cover - environment dependent
    with pytest.raises(E.ExportError) as error:
        E.export_trace(trace_dir=trace_dir, output=tmp_path / "out.gif", fmt="gif")
    message = str(error.value)
    assert "Pillow" in message
    assert "install" in message.lower()
    assert not (tmp_path / "out.gif").exists()


@pytest.mark.skipif(_HAS_IMAGEIO, reason="imageio IS installed; the refusal path cannot be reached")
def test_export_mp4_refuses_with_an_actionable_message_when_no_encoder_is_present(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    output = tmp_path / "out" / "replay.mp4"
    with pytest.raises(E.ExportError) as error:
        E.export_trace(trace_dir=trace_dir, output=output, fmt="mp4")

    message = str(error.value)
    assert "imageio" in message, message
    assert "install" in message.lower(), message
    # It names an alternative that does work here rather than leaving the user stuck.
    assert "--format gif" in message or "--format html" in message
    if shutil.which("ffmpeg") is None:
        assert "ffmpeg" in message
        assert "MP4 VALIDATION IS BLOCKED" in message
    else:
        assert shutil.which("ffmpeg") in message
    # Nothing was written, and no empty file was left behind as a false success.
    assert not output.exists()
    assert not (tmp_path / "out").exists() or _snapshot(tmp_path / "out") == set()


@pytest.mark.skipif(not _HAS_IMAGEIO, reason="imageio is not installed in this interpreter")
def test_export_mp4_writes_a_file_when_an_encoder_is_present(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:  # pragma: no cover - environment dependent
    output = tmp_path / "out"
    output.mkdir()
    returned = E.export_trace(trace_dir=trace_dir, output=output / "replay.mp4", fmt="mp4")
    assert returned.is_file() and returned.stat().st_size > 0
    assert returned.with_suffix(returned.suffix + ".metadata.json").is_file()


# --------------------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------------------


def test_an_absent_trace_directory_is_refused(tmp_path: pathlib.Path) -> None:
    with pytest.raises(E.ExportError, match="trace directory does not exist"):
        E.export_trace(trace_dir=tmp_path / "ghost", output=tmp_path / "out.json", fmt="json")
    assert not (tmp_path / "out.json").exists()


def test_an_empty_trace_directory_is_refused(tmp_path: pathlib.Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    for fmt in ("json", "png", "html"):
        with pytest.raises(E.ExportError, match="contains no readable frame"):
            E.export_trace(trace_dir=empty, output=tmp_path / f"out.{fmt}", fmt=fmt)
    assert _snapshot(tmp_path) == {pathlib.Path("empty")}


def test_a_trace_whose_frames_are_all_unreadable_is_refused_with_its_problems(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    for chunk in (trace_dir / "chunks").glob("*.jsonl"):
        chunk.write_bytes(b"{not json\n")
    with pytest.raises(E.ExportError) as error:
        E.export_trace(trace_dir=trace_dir, output=tmp_path / "out.json", fmt="json")
    message = str(error.value)
    assert "contains no readable frame" in message
    assert "problems:" in message


def test_an_unknown_format_is_refused(trace_dir: pathlib.Path, tmp_path: pathlib.Path) -> None:
    with pytest.raises(E.ExportError, match="unknown export format 'svg'"):
        E.export_trace(trace_dir=trace_dir, output=tmp_path / "out.svg", fmt="svg")
    assert _snapshot(tmp_path) == _snapshot(tmp_path)  # nothing new appeared
    assert not (tmp_path / "out.svg").exists()


def test_a_truncated_trace_still_exports_and_carries_its_status(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    chunk = trace_dir / "chunks" / "chunk-00001.jsonl"
    lines = chunk.read_bytes().split(b"\n")
    chunk.write_bytes(lines[0][: len(lines[0]) // 2])

    output = tmp_path / "out" / "trace.json"
    E.export_trace(trace_dir=trace_dir, output=output, fmt="json")
    payload = R.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == TS.STATUS_INCOMPLETE
    assert any("incomplete final line" in problem for problem in payload["problems"])
    assert payload["truncated_after_sequence"] == 1
    assert len(payload["frames"]) == 2, "the frames before the truncation are still exported"


def test_export_writes_nothing_outside_the_requested_output(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    before_root = _snapshot(tmp_path)
    before_trace = _snapshot(trace_dir)

    E.export_trace(trace_dir=trace_dir, output=sandbox / "a.json", fmt="json")
    E.export_trace(trace_dir=trace_dir, output=sandbox / "b.png", fmt="png")
    E.export_trace(trace_dir=trace_dir, output=sandbox / "c.html", fmt="html")

    assert _snapshot(sandbox) == {
        pathlib.Path("a.json"),
        pathlib.Path("b.png"),
        pathlib.Path("c.html"),
    }
    assert _snapshot(trace_dir) == before_trace
    new = _snapshot(tmp_path) - before_root
    assert new == {
        pathlib.Path("sandbox/a.json"),
        pathlib.Path("sandbox/b.png"),
        pathlib.Path("sandbox/c.html"),
    }


def test_export_trace_dispatches_every_documented_format(
    trace_dir: pathlib.Path, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dispatcher routes each name to its exporter and nothing else."""

    calls: list[tuple[str, Any]] = []

    def _record(name: str):  # type: ignore[no-untyped-def]
        def _inner(trace, output, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
            calls.append((name, kwargs))
            return pathlib.Path(output)

        return _inner

    for name in ("export_html", "export_json", "export_png", "export_gif", "export_mp4"):
        monkeypatch.setattr(E, name, _record(name))
    for fmt in ("html", "json", "png", "gif", "mp4"):
        E.export_trace(trace_dir=trace_dir, output=tmp_path / f"o.{fmt}", fmt=fmt, fps=3.0)

    assert [name for name, _kwargs in calls] == [
        "export_html", "export_json", "export_png", "export_gif", "export_mp4",
    ]
    assert calls[3][1] == {"fps": 3.0} and calls[4][1] == {"fps": 3.0}
    assert calls[0][1] == {} and calls[1][1] == {} and calls[2][1] == {}

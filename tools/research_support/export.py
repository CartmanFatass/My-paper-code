"""Exports from a recorded trace: standalone HTML replay, images, animation, raw data.

Every export states what it was made from. A missing optional encoder produces an
actionable error naming the exact dependency, never an empty file reported as a success and
never an automatic global installation.

The standalone HTML bundle is designed to open from the filesystem without this repository,
without the training interpreter and without a network connection. Browsers block
``fetch``/``XMLHttpRequest`` for ``file://`` documents, so a small trace is embedded in the
page rather than fetched; a large trace is written as a data directory with a documented
local serving command instead of shipping a page that silently fails to load its JSON.
"""

from __future__ import annotations

import html
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from .capture.trace_store import TraceReader
from .records import dumps

#: Above this size the trace is not inlined into a single HTML file.
INLINE_LIMIT_BYTES = 6 * 1024 * 1024

_VIEWER_STATIC = Path(__file__).resolve().parent / "viewer" / "static"


class ExportError(RuntimeError):
    """An export could not be produced. The message names what is missing."""


def _read_trace(trace_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any], Any]:
    reader = TraceReader(trace_dir)
    result = reader.read()
    if not result.frames:
        raise ExportError(
            f"{trace_dir} contains no readable frame"
            + (f"; problems: {'; '.join(result.problems[:3])}" if result.problems else "")
        )
    return result.frames, result.manifest, result


def export_trace(
    *,
    trace_dir: Path,
    output: Path,
    fmt: str,
    fps: float = 8.0,
) -> Path:
    trace_dir = Path(trace_dir)
    output = Path(output)
    if not trace_dir.is_dir():
        raise ExportError(f"trace directory does not exist: {trace_dir}")
    if fmt == "html":
        return export_html(trace_dir, output)
    if fmt == "json":
        return export_json(trace_dir, output)
    if fmt == "png":
        return export_png(trace_dir, output)
    if fmt == "gif":
        return export_gif(trace_dir, output, fps=fps)
    if fmt == "mp4":
        return export_mp4(trace_dir, output, fps=fps)
    raise ExportError(f"unknown export format {fmt!r}")


# --------------------------------------------------------------------------------------
# Data exports
# --------------------------------------------------------------------------------------


def export_json(trace_dir: Path, output: Path) -> Path:
    """Raw frames plus the trace index, for an analysis that wants the numbers."""

    frames, manifest, result = _read_trace(trace_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "research_support.trace_export.1",
        "manifest": manifest,
        "index": result.index.to_json(),
        "status": result.status,
        "problems": result.problems,
        "truncated_after_sequence": result.truncated_after_sequence,
        "frames": frames,
    }
    output.write_text(dumps(payload, indent=2), encoding="utf-8")
    return output


# --------------------------------------------------------------------------------------
# Image exports
# --------------------------------------------------------------------------------------


def export_png(trace_dir: Path, output: Path) -> Path:
    """Render the last recorded frame as a standalone PNG."""

    frames, _manifest, _result = _read_trace(trace_dir)
    from .render import render_scene_figure

    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    figure = render_scene_figure(frames[-1])
    try:
        figure.savefig(output, dpi=130)
    finally:
        plt.close(figure)
    return output


def _frames_as_images(frames: Sequence[Mapping[str, Any]], *, stride: int):
    from .render import render_scene_rgb

    for index in range(0, len(frames), max(1, stride)):
        yield render_scene_rgb(frames[index], figsize=(7.0, 5.6), dpi=90)


def export_gif(trace_dir: Path, output: Path, *, fps: float = 8.0, max_frames: int = 240) -> Path:
    """Animated GIF through Pillow, which this environment already has.

    The metadata sidecar records playback FPS, the simulated-time range, whether anything
    was interpolated (never) and the source trace hash, so a shared animation can still be
    traced back to its records.
    """

    frames, manifest, result = _read_trace(trace_dir)
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - Pillow is present in this checkout
        raise ExportError(
            "GIF export needs Pillow. It is not installed in the selected interpreter and "
            "this tool does not install anything. Install it into an isolated tooling "
            "environment, or use --format png / --format html."
        ) from error

    stride = max(1, len(frames) // max_frames + (1 if len(frames) % max_frames else 0))
    images = [Image.fromarray(array) for array in _frames_as_images(frames, stride=stride)]
    if not images:
        raise ExportError("no frame could be rendered")
    output.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(round(1000.0 / max(0.1, fps)))
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )
    _write_animation_metadata(output, frames, manifest, result, fps=fps, stride=stride, encoder="PIL")
    return output


def export_mp4(trace_dir: Path, output: Path, *, fps: float = 8.0) -> Path:
    """MP4 through an explicitly installed encoder, or an actionable refusal."""

    frames, manifest, result = _read_trace(trace_dir)
    # Every other exporter does this; without it a missing parent surfaced from inside the
    # encoder instead of as an ExportError.
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    encoder = None
    try:
        import imageio.v2 as imageio  # type: ignore

        writer = imageio.get_writer(str(output), fps=fps)
        encoder = "imageio"
    except ImportError:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise ExportError(
                "MP4 export needs a compatible encoder and none is available. Neither the "
                "'imageio' package (with its ffmpeg plugin) nor an 'ffmpeg' executable was "
                "found for the selected interpreter, and this tool installs nothing. "
                "MP4 VALIDATION IS BLOCKED. Use --format gif (Pillow, already available) or "
                "--format html, or provision an isolated tooling environment with imageio-"
                "ffmpeg and re-run."
            )
        raise ExportError(
            f"an ffmpeg executable was found at {ffmpeg} but the 'imageio' Python package "
            "is not installed, so this exporter cannot drive it. Install imageio into an "
            "isolated tooling environment, or use --format gif."
        )
    try:
        for array in _frames_as_images(frames, stride=1):
            writer.append_data(array)
    finally:
        writer.close()
    _write_animation_metadata(output, frames, manifest, result, fps=fps, stride=1, encoder=encoder)
    return output


def _write_animation_metadata(
    output: Path,
    frames: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    result: Any,
    *,
    fps: float,
    stride: int,
    encoder: str,
) -> None:
    times = [
        (f.get("clock") or {}).get("simulation_time_s")
        for f in frames
        if (f.get("clock") or {}).get("simulation_time_s") is not None
    ]
    sidecar = output.with_suffix(output.suffix + ".metadata.json")
    sidecar.write_text(
        dumps(
            {
                "schema": "research_support.animation_metadata.1",
                "source_trace_id": manifest.get("trace_id"),
                "source_manifest": manifest,
                "trace_status": result.status,
                "trace_problems": result.problems,
                "playback_fps": fps,
                "frame_stride": stride,
                "n_frames_in_animation": len(range(0, len(frames), max(1, stride))),
                "n_frames_in_trace": len(frames),
                "simulated_time_range_s": [min(times), max(times)] if times else None,
                "interpolation": "none; every frame is a recorded sample",
                "encoder": encoder,
                "caveat": (
                    "An animation is a presentation of recorded frames. Scientific metrics "
                    "must be read from the trace or the report data, never reconstructed by "
                    "summing an animation."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------------------
# Standalone HTML replay
# --------------------------------------------------------------------------------------


_STANDALONE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body class="standalone">
<header id="header">
  <div class="brand"><span class="brand-mark"></span><span id="title-text">{title}</span></div>
  <dl class="identity" id="identity"></dl>
  <div class="header-right">
    <span id="stream-state" class="state state-ended">RECORDED</span>
    <button id="theme-toggle" type="button">Theme</button>
    <button id="contrast-toggle" type="button">Contrast</button>
  </div>
</header>
<div id="banner" class="banner">{banner}</div>
<main id="main" style="padding:10px">
  <div class="panel-grid">
    <div class="scene-column">
      <div class="scene-toolbar">
        <div class="group">
          <label for="view-mode">View</label>
          <select id="view-mode">
            <option value="2d" selected>2-D</option>
            <option value="3d">3-D inspection</option>
          </select>
        </div>
        <div class="group">
          <button id="pb-first" type="button">&#9198;</button>
          <button id="pb-prev" type="button">&#9664;|</button>
          <button id="pb-play" type="button">&#9654;</button>
          <button id="pb-next" type="button">|&#9654;</button>
          <button id="pb-last" type="button">&#9197;</button>
          <label for="pb-speed">Speed</label>
          <select id="pb-speed">
            <option value="0.5">0.5x</option><option value="1" selected>1x</option>
            <option value="2">2x</option><option value="4">4x</option>
          </select>
          <label class="check"><input type="checkbox" id="pb-frame-index"> frame-index pacing</label>
        </div>
        <div class="group">
          <label for="info-view">Information</label>
          <select id="info-view">
            <option value="truth" selected>Simulator truth</option>
            <option value="policy">Policy-visible</option>
          </select>
        </div>
        <div class="group"><button id="reset-camera" type="button">Reset camera</button></div>
      </div>
      <div class="scrubber-row">
        <input type="range" id="scrubber" min="0" max="0" value="0" step="1">
        <span id="scrubber-label" class="mono">&mdash;</span>
        <span id="scrubber-note" class="note"></span>
      </div>
      <div id="scene-wrap" class="scene-wrap">
        <canvas id="scene2d"></canvas>
        <canvas id="scene3d" hidden></canvas>
        <div id="tooltip" class="tooltip" hidden></div>
        <div id="scene-empty" class="scene-empty"></div>
      </div>
      <div class="charts">
        <canvas id="chart-service"></canvas>
        <canvas id="chart-util"></canvas>
      </div>
      <div class="timeline-wrap">
        <h3>Event timeline <span class="note">actual recorded event times</span></h3>
        <canvas id="timeline"></canvas>
        <div id="timeline-legend" class="legend"></div>
      </div>
    </div>
    <aside class="side-column">
      <div class="card"><h3>Layers</h3><div id="layer-controls" class="layers"></div>
        <label class="check"><input type="checkbox" id="show-trails"> UAV trails</label>
        <label class="slider">Trail length
          <input type="range" id="trail-length" min="0" max="120" value="24" step="1">
          <span id="trail-length-label" class="mono">24</span></label>
      </div>
      <div class="card"><h3>Find entity</h3>
        <input type="search" id="entity-search" placeholder="stable id" autocomplete="off">
        <div id="search-results" class="search-results"></div></div>
      <div class="card"><h3>Inspector <span class="note" id="inspector-mode"></span></h3>
        <div id="inspector" class="inspector"></div></div>
      <div class="card"><h3>Capability &amp; provenance</h3><div id="capability" class="capability"></div></div>
      <div class="card"><h3>Entity table</h3>
        <div class="table-scroll"><table id="entity-table"><thead></thead><tbody></tbody></table></div></div>
    </aside>
  </div>
</main>
<footer id="footer">
  <span>sim <b id="f-sim">&mdash;</b></span>
  <span>geometry <b id="f-geom">&mdash;</b></span>
  <span>measured <b id="f-window">&mdash;</b></span>
  <span>sample age <b id="f-age">&mdash;</b></span>
  <span>capture <b id="f-resolution">&mdash;</b></span>
  <span>seq <b id="f-seq">&mdash;</b></span>
  <span>drops <b id="f-drops">&mdash;</b></span>
  <span>gated <b id="f-gated">&mdash;</b></span>
  <span>trace <b id="f-trace">&mdash;</b></span>
  <span id="f-error" class="err"></span>
</footer>
<script id="trace-data" type="application/json">{data}</script>
<script>{scene3d}</script>
<script>{app}</script>
</body>
</html>
"""


def export_html(trace_dir: Path, output: Path) -> Path:
    """Self-contained replay page, or a bundle directory for a large trace."""

    frames, manifest, result = _read_trace(trace_dir)
    payload = {
        "schema": "research_support.standalone_replay.1",
        "manifest": manifest,
        "index": result.index.to_json(),
        "status": result.status,
        "problems": result.problems,
        "truncated_after_sequence": result.truncated_after_sequence,
        "frames": frames,
    }
    data = dumps(payload)
    css = (_VIEWER_STATIC / "app.css").read_text(encoding="utf-8")
    scene3d = (_VIEWER_STATIC / "scene3d.js").read_text(encoding="utf-8")
    # The bundle ships the viewer's own app.js, which detects the absence of a
    # bootstrap block and reads the embedded trace instead of the HTTP API. One
    # renderer, so the offline replay cannot drift from the served one.
    app = (_VIEWER_STATIC / "app.js").read_text(encoding="utf-8")

    title = f"Replay: {manifest.get('trace_id', trace_dir.name)}"
    banner = (
        "RECORDED TRACE, replayed offline. "
        f"Producer: {html.escape(str(manifest.get('controller', 'unknown')))} "
        f"({html.escape(str(manifest.get('controller_kind', 'unknown kind')))}), "
        f"route {html.escape(str(manifest.get('route', 'unknown')))}, "
        f"status {html.escape(result.status)}. "
        "Sparse capture cannot reconstruct unrecorded actions or topology changes."
    )

    if len(data.encode("utf-8")) <= INLINE_LIMIT_BYTES:
        output = Path(output)
        if output.is_dir() or output.suffix == "":
            output.mkdir(parents=True, exist_ok=True)
            output = output / "replay.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            _STANDALONE_TEMPLATE.format(
                title=html.escape(title),
                banner=banner,
                css=css,
                data=data,
                scene3d=scene3d,
                app=app,
            ),
            encoding="utf-8",
        )
        return output

    # Too large to inline. Ship an asset directory and say plainly how to open it, rather
    # than a page that would silently fail to fetch its JSON from file://.
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "trace.json").write_text(data, encoding="utf-8")
    (directory / "app.css").write_text(css, encoding="utf-8")
    (directory / "scene3d.js").write_text(scene3d, encoding="utf-8")
    (directory / "app.js").write_text(app, encoding="utf-8")
    page = _STANDALONE_TEMPLATE.format(
        title=html.escape(title),
        banner=banner + " This bundle loads trace.json, so it must be served over http.",
        css="@import url('app.css');",
        data="null",
        scene3d="",
        app="",
    ).replace(
        '<script id="trace-data" type="application/json">null</script>',
        '<script>window.RS_TRACE_URL = "trace.json";</script>'
        '<script src="scene3d.js"></script><script src="app.js"></script>',
    )
    (directory / "replay.html").write_text(page, encoding="utf-8")
    (directory / "README.txt").write_text(
        "Portable replay bundle\n"
        "======================\n\n"
        f"Trace: {manifest.get('trace_id')}\n"
        f"Route: {manifest.get('route')}\n"
        f"Frames: {len(frames)}  Status: {result.status}\n\n"
        "This trace is too large to embed in a single file, so replay.html loads\n"
        "trace.json at runtime. Browsers refuse that for file:// documents, so serve the\n"
        "directory over loopback instead of double-clicking the page:\n\n"
        "    python -m http.server 8000 --bind 127.0.0.1\n"
        "    then open http://127.0.0.1:8000/replay.html\n\n"
        "No repository code, training interpreter or network connection is required.\n",
        encoding="utf-8",
    )
    return directory / "replay.html"

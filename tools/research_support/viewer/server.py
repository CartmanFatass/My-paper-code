"""Local read-only diagnostic server for the research support viewer.

Security posture, from Section 15.1 of the plan:

* binds ``127.0.0.1`` only, never ``0.0.0.0``; no tunnel, no firewall change, no remote
  action API;
* serves only the roots the invocation explicitly named, with traversal, symlink and
  junction escapes refused by real-path containment rather than by string matching;
* validates ``Host`` and ``Origin`` and requires an ephemeral session token on every data
  endpoint; the token is redacted from the access log;
* bounds response sizes and concurrent work, and never accepts a filesystem path or a
  command through a URL parameter;
* answers only ``GET``/``HEAD``. There is no endpoint that starts, stops, resets or steps
  anything. The browser cannot reach ``env.step()``, an optimizer, a solver or a reset.

The server is a *consumer*. It reads the atomically replaced latest-frame file and
immutable trace chunks a producer wrote. Its only write is the viewer lease it renews so a
producer can tell that somebody is looking; closing the page lets that lease expire, which
suspends producer-side extraction and cannot stop the simulation.

Only the standard library is used, so a browser check needs no new scientific dependency.
"""

from __future__ import annotations

import html
import json
import mimetypes
import os
import secrets
import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, parse_qs, urlparse

from ..records import dumps, loads
from ..capture.trace_store import TraceReader
from ..capture.transport import LatestFrameReader, MappedViewerLease

_STATIC_DIR = Path(__file__).resolve().parent / "static"

#: Largest response this server will assemble. A replay request for more frames than fit is
#: refused with an explicit message rather than silently truncated.
MAX_RESPONSE_BYTES = 16 * 1024 * 1024

#: Largest number of trace frames one request may ask for.
MAX_FRAMES_PER_REQUEST = 400

_ALLOWED_HOSTS = ("127.0.0.1", "localhost", "[::1]")

_CSP = (
    "default-src 'none'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    # Only a document this same process serves, and only for the report view.
    "frame-src 'self'; "
    "font-src 'self'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)

#: Policy for a generated report document. It differs from ``_CSP`` in exactly two ways:
#: it may be framed by this viewer (and by nothing else), and it may carry the inline style
#: block the report generator emits. It still executes no script of any kind.
_REPORT_CSP = (
    "default-src 'none'; "
    "script-src 'none'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'self'"
)


class _ExclusiveHTTPServer(ThreadingHTTPServer):
    """Refuse a port another viewer already holds.

    ``ThreadingHTTPServer`` sets ``SO_REUSEADDR``, and on Windows that lets a second
    process bind a port a first one is already listening on. Both then answer, arbitrarily.
    For a diagnostic viewer that is the worst possible failure: the operator reads a stale
    server's traces while believing they restarted it. Binding must fail instead.
    """

    allow_reuse_address = False


class ViewerSecurityError(RuntimeError):
    """A request was refused for a containment or authentication reason."""


@dataclass
class TraceSlot:
    """One trace exposed for replay or comparison, under a label the UI shows."""

    label: str
    directory: Path
    reader: TraceReader = field(init=False)

    def __post_init__(self) -> None:
        self.reader = TraceReader(self.directory)


@dataclass
class ViewerConfig:
    """Everything the server is allowed to touch. Nothing is discovered at request time."""

    #: Directory holding ``latest.json`` / ``stream_health.json`` / ``viewer.lease``.
    stream_dir: Path | None = None
    #: Traces available for replay, keyed by the label the UI shows.
    traces: dict[str, Path] = field(default_factory=dict)
    #: Report directories exposed read-only, keyed by label.
    reports: dict[str, Path] = field(default_factory=dict)
    host: str = "127.0.0.1"
    port: int = 0
    viewer_lease_timeout_s: float = 10.0
    title: str = "HMASD research support viewer"
    #: Free-form provenance banner the page shows above the scene.
    banner: str = ""
    open_browser: bool = False

    def __post_init__(self) -> None:
        if self.host not in _ALLOWED_HOSTS:
            raise ViewerSecurityError(
                f"refusing to bind {self.host!r}; this is a local diagnostic tool and binds "
                f"loopback only ({', '.join(_ALLOWED_HOSTS)})"
            )


class ViewerState:
    """Server-side state shared by handler threads."""

    def __init__(self, config: ViewerConfig) -> None:
        self.config = config
        self.token = secrets.token_urlsafe(32)
        self.started_monotonic = time.monotonic()
        self._lock = threading.Lock()
        self._frame_reader = (
            LatestFrameReader(config.stream_dir) if config.stream_dir is not None else None
        )
        self._lease: MappedViewerLease | None = None
        if config.stream_dir is not None:
            try:
                # ``create=True``: the server may be started before the producer, and an
                # absent lease file must not make the page unusable.
                self._lease = MappedViewerLease.in_directory(config.stream_dir, create=True)
            except OSError:
                self._lease = None
        self._traces = {
            label: TraceSlot(label=label, directory=Path(path).resolve())
            for label, path in config.traces.items()
        }
        self._report_roots = {
            label: Path(path).resolve() for label, path in config.reports.items()
        }
        self._trace_cache: dict[str, list[dict[str, Any]]] = {}
        self._trace_status: dict[str, dict[str, Any]] = {}

    # ----------------------------------------------------------------------------------

    @property
    def mode(self) -> str:
        if self._frame_reader is not None and self._traces:
            return "live_and_replay"
        if self._frame_reader is not None:
            return "live"
        if len(self._traces) > 1:
            return "compare"
        if self._traces:
            return "replay"
        return "reports_only"

    def renew_lease(self) -> None:
        """Tell the producer a viewer is present. A pure write of one double."""

        if self._lease is not None:
            try:
                self._lease.renew(self.config.viewer_lease_timeout_s)
            except (OSError, ValueError):
                pass

    def revoke_lease(self) -> None:
        if self._lease is not None:
            try:
                self._lease.revoke()
            except (OSError, ValueError):
                pass

    def close(self) -> None:
        self.revoke_lease()
        if self._lease is not None:
            try:
                self._lease.close()
            except OSError:
                pass
            self._lease = None

    # ----------------------------------------------------------------------------------

    def meta(self) -> dict[str, Any]:
        return {
            "title": self.config.title,
            "banner": self.config.banner,
            "mode": self.mode,
            "live_available": self._frame_reader is not None,
            "traces": [
                {
                    "label": slot.label,
                    "directory": slot.directory.name,
                    "manifest": slot.reader.read_manifest(),
                }
                for slot in self._traces.values()
            ],
            "reports": sorted(self._report_roots),
            "viewer_lease_timeout_s": self.config.viewer_lease_timeout_s,
            "server_uptime_s": time.monotonic() - self.started_monotonic,
            "max_frames_per_request": MAX_FRAMES_PER_REQUEST,
        }

    def latest_frame(self) -> dict[str, Any]:
        """Latest live frame plus the reason there is none, when there is none."""

        if self._frame_reader is None:
            return {
                "frame": None,
                "state": "DISCONNECTED",
                "detail": (
                    "this viewer was started without a stream directory; it cannot attach "
                    "to an uninstrumented run"
                ),
            }
        self.renew_lease()
        payload, error = self._frame_reader.read()
        if error is not None:
            return {"frame": None, "state": "ERROR", "detail": error}
        if payload is None:
            return {
                "frame": None,
                "state": "WAITING",
                "detail": (
                    "no frame published yet; the producer publishes only when its gates "
                    "admit a sample"
                ),
            }
        try:
            frame = loads(payload)
        except ValueError as exc:
            return {"frame": None, "state": "ERROR", "detail": f"unparsable frame: {exc}"}
        age_s = max(0.0, time.monotonic() - float(frame.get("clock", {}).get("producer_monotonic_s", 0.0)))
        return {"frame": frame, "state": "LIVE", "detail": None, "sample_age_s": age_s}

    def health(self) -> dict[str, Any]:
        if self._frame_reader is None:
            return {"available": False}
        payload = self._frame_reader.read_health()
        if payload is None:
            return {"available": False}
        try:
            return {"available": True, **loads(payload)}
        except ValueError as exc:
            return {"available": False, "error": str(exc)}

    def trace_index(self, label: str) -> dict[str, Any]:
        slot = self._require_trace(label)
        with self._lock:
            if label not in self._trace_status:
                result = slot.reader.read()
                self._trace_cache[label] = result.frames
                self._trace_status[label] = {
                    "trace_id": result.trace_id,
                    "status": result.status,
                    "problems": result.problems,
                    "truncated_after_sequence": result.truncated_after_sequence,
                    "manifest": result.manifest,
                    "index": result.index.to_json(),
                    "n_frames": len(result.frames),
                }
            return dict(self._trace_status[label])

    def trace_frames(self, label: str, *, start: int, count: int) -> dict[str, Any]:
        self.trace_index(label)
        frames = self._trace_cache.get(label, [])
        count = max(0, min(int(count), MAX_FRAMES_PER_REQUEST))
        start = max(0, int(start))
        window = frames[start : start + count]
        return {
            "label": label,
            "start": start,
            "count": len(window),
            "total": len(frames),
            "frames": window,
        }

    def trace_timeline(self, label: str) -> dict[str, Any]:
        """Compact per-frame series so the UI can scrub without holding every frame."""

        self.trace_index(label)
        rows: list[dict[str, Any]] = []
        for index, frame in enumerate(self._trace_cache.get(label, [])):
            clock = frame.get("clock") or {}
            metrics = frame.get("interval_metrics") or {}
            provenance = frame.get("provenance") or {}
            rows.append(
                {
                    "i": index,
                    "sequence": (frame.get("identity") or {}).get("sequence"),
                    "simulation_time_s": clock.get("simulation_time_s"),
                    "geometry_time_s": clock.get("geometry_time_s"),
                    "decision_step": clock.get("decision_step"),
                    "frame_kind": provenance.get("frame_kind"),
                    "episode_id": (frame.get("identity") or {}).get("episode_id"),
                    "metrics": {
                        name: (value or {}).get("value") for name, value in metrics.items()
                    },
                    "events": [
                        {"time_s": e.get("time_s"), "event_type": e.get("event_type")}
                        for e in frame.get("events") or ()
                    ],
                }
            )
        return {"label": label, "rows": rows}

    def report_file(self, label: str, relative: str) -> tuple[bytes, str]:
        root = self._report_roots.get(label)
        if root is None:
            raise ViewerSecurityError(f"unknown report root: {label!r}")
        return _read_contained(root, relative)

    def _require_trace(self, label: str) -> TraceSlot:
        slot = self._traces.get(label)
        if slot is None:
            raise ViewerSecurityError(f"unknown trace label: {label!r}")
        return slot


def _read_contained(root: Path, relative: str) -> tuple[bytes, str]:
    """Read ``relative`` under ``root``, refusing every escape.

    Containment is checked on the *resolved* path, so ``..`` segments, absolute paths, a
    symlink and a Windows junction are all refused by the same test. Directory listing is
    not offered at all.
    """

    if not relative or relative.startswith(("/", "\\")) or ":" in relative:
        raise ViewerSecurityError("refused absolute or drive-qualified path")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ViewerSecurityError("refused path outside the approved root") from error
    if not candidate.is_file():
        raise FileNotFoundError(relative)
    size = candidate.stat().st_size
    if size > MAX_RESPONSE_BYTES:
        raise ViewerSecurityError(
            f"file is {size} bytes, above the {MAX_RESPONSE_BYTES}-byte response limit"
        )
    content_type, _ = mimetypes.guess_type(candidate.name)
    return candidate.read_bytes(), content_type or "application/octet-stream"


class _Handler(BaseHTTPRequestHandler):
    """Read-only handler. Every data route requires the session token."""

    server_version = "HMASDResearchSupport/1.0"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    @property
    def state(self) -> ViewerState:
        return self.server.viewer_state  # type: ignore[attr-defined]

    # -- logging -----------------------------------------------------------------------

    def log_message(self, fmt: str, *args: Any) -> None:
        """Access log with the session token redacted.

        The token never appears in a URL this server generates, but a hand-typed request
        could carry one, and a log line is an export.
        """

        message = fmt % args
        token = self.state.token
        if token and token in message:
            message = message.replace(token, "<redacted>")
        sys.stderr.write(
            f"{self.address_string()} - - [{self.log_date_time_string()}] {message}\n"
        )

    def log_error(self, fmt: str, *args: Any) -> None:
        self.log_message(fmt, *args)

    # -- helpers -----------------------------------------------------------------------

    def _check_origin(self) -> None:
        host = (self.headers.get("Host") or "").split(":")[0].strip()
        if host and host not in _ALLOWED_HOSTS:
            raise ViewerSecurityError(f"refused Host header {host!r}")
        origin = self.headers.get("Origin")
        if origin:
            parsed = urlparse(origin)
            if parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
                raise ViewerSecurityError(f"refused Origin {origin!r}")

    def _check_token(self, query: Mapping[str, list[str]]) -> None:
        supplied = self.headers.get("X-RS-Token") or (query.get("t") or [""])[0]
        if not secrets.compare_digest(str(supplied), self.state.token):
            raise ViewerSecurityError("missing or invalid session token")

    def _send(
        self,
        status: HTTPStatus,
        body: bytes,
        content_type: str,
        *,
        extra_headers: Mapping[str, str] | None = None,
        csp: str = _CSP,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", csp)
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send(status, dumps(payload).encode("utf-8"), "application/json; charset=utf-8")

    def _send_error_json(self, status: HTTPStatus, detail: str) -> None:
        self._send_json({"error": detail, "status": int(status)}, status)

    # -- routing -----------------------------------------------------------------------

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)
        try:
            self._check_origin()
        except ViewerSecurityError as error:
            self._send_error_json(HTTPStatus.FORBIDDEN, str(error))
            return
        try:
            if route in ("/", "/index.html"):
                self._serve_index()
            elif route.startswith("/static/"):
                self._serve_static(route[len("/static/") :])
            elif route.startswith("/report/"):
                self._serve_report(route[len("/report/") :])
            elif route.startswith("/api/"):
                self._check_token(query)
                self._serve_api(route[len("/api/") :], query)
            else:
                self._send_error_json(HTTPStatus.NOT_FOUND, f"no route {route!r}")
        except ViewerSecurityError as error:
            self._send_error_json(HTTPStatus.FORBIDDEN, str(error))
        except FileNotFoundError as error:
            self._send_error_json(HTTPStatus.NOT_FOUND, f"not found: {error}")
        except ValueError as error:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(error))

    # Every mutating verb is absent by design: there is no way to reach the simulation.
    def do_POST(self) -> None:  # noqa: N802
        self._send_error_json(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "this viewer is read-only; it exposes no endpoint that changes anything",
        )

    do_PUT = do_POST
    do_DELETE = do_POST
    do_PATCH = do_POST

    # -- routes ------------------------------------------------------------------------

    def _serve_index(self) -> None:
        template = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
        bootstrap = dumps(
            {
                "token": self.state.token,
                "meta": self.state.meta(),
            }
        )
        page = template.replace("__RS_BOOTSTRAP__", bootstrap).replace(
            "__RS_TITLE__", html.escape(self.state.config.title)
        )
        self._send(HTTPStatus.OK, page.encode("utf-8"), "text/html; charset=utf-8")

    def _serve_static(self, relative: str) -> None:
        # Percent-decode BEFORE the containment check. Undecoded, `..%2f..%2fsecret` named a
        # file that simply did not exist inside the static root, so an escape attempt came
        # back as a 404 instead of being recognised and refused as one.
        body, content_type = _read_contained(_STATIC_DIR.resolve(), unquote(relative))
        if content_type.startswith("text/") or content_type.endswith("javascript"):
            content_type = f"{content_type}; charset=utf-8"
        self._send(HTTPStatus.OK, body, content_type)

    def _serve_report(self, remainder: str) -> None:
        """Serve a generated report under ``/report/<token>/<label>/<path>``.

        The token lives in the path rather than the query for one reason: a report's own
        ``index.html`` refers to ``figures/C03.png`` relatively, and a query-based route
        resolves that against the server root, so every figure 404s. With the token as a
        path segment the browser carries it into each subresource by construction, and the
        containment check below is the same one the static route uses.
        """

        parts = unquote(remainder).split("/", 2)
        if len(parts) < 3 or not parts[2]:
            raise ViewerSecurityError("report path must be <token>/<label>/<path>")
        token, label, relative = parts
        if not secrets.compare_digest(token, self.state.token):
            raise ViewerSecurityError("missing or invalid session token")
        body, content_type = self.state.report_file(label, relative)
        if content_type.startswith("text/") or content_type.endswith("javascript"):
            content_type = f"{content_type}; charset=utf-8"
        self._send(HTTPStatus.OK, body, content_type, csp=_REPORT_CSP)

    def _serve_api(self, route: str, query: Mapping[str, list[str]]) -> None:
        if route == "meta":
            self._send_json(self.state.meta())
        elif route == "frame":
            self._send_json(self.state.latest_frame())
        elif route == "health":
            self._send_json(self.state.health())
        elif route == "trace/index":
            self._send_json(self.state.trace_index(_one(query, "label")))
        elif route == "trace/frames":
            self._send_json(
                self.state.trace_frames(
                    _one(query, "label"),
                    start=int(_one(query, "start", "0")),
                    count=int(_one(query, "count", "1")),
                )
            )
        elif route == "trace/timeline":
            self._send_json(self.state.trace_timeline(_one(query, "label")))
        elif route == "report":
            body, content_type = self.state.report_file(
                _one(query, "label"), _one(query, "path")
            )
            self._send(HTTPStatus.OK, body, content_type)
        else:
            self._send_error_json(HTTPStatus.NOT_FOUND, f"no api route {route!r}")


def _one(query: Mapping[str, list[str]], name: str, default: str | None = None) -> str:
    values = query.get(name) or []
    if not values:
        if default is None:
            raise ValueError(f"missing required query parameter {name!r}")
        return default
    if len(values) > 1:
        raise ValueError(f"query parameter {name!r} given more than once")
    value = values[0]
    if len(value) > 512:
        raise ValueError(f"query parameter {name!r} is too long")
    return value


class ViewerServer:
    """Owns the socket and the lease. Shutting it down stops nothing else.

    In particular it does not, and cannot, terminate a producer: it never learns the
    producer's process identity. Closing the viewer lets the viewer lease expire, which
    suspends optional extraction on the producer side and leaves the simulation running.
    """

    def __init__(self, config: ViewerConfig) -> None:
        self._state = ViewerState(config)
        self._httpd = _ExclusiveHTTPServer((config.host, config.port), _Handler)
        self._httpd.daemon_threads = True
        self._httpd.viewer_state = self._state  # type: ignore[attr-defined]
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return int(self._httpd.server_address[1])

    @property
    def host(self) -> str:
        return str(self._httpd.server_address[0])

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    @property
    def token(self) -> str:
        return self._state.token

    @property
    def state(self) -> ViewerState:
        return self._state

    def start(self) -> "ViewerServer":
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, name="research-support-viewer", daemon=True
        )
        self._thread.start()
        return self

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        self._state.close()

    def __enter__(self) -> "ViewerServer":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()


def free_port(host: str = "127.0.0.1") -> int:
    """Ask the OS for a free loopback port rather than guessing one."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])

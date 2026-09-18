"""Security and contract tests for ``tools/research_support/viewer/server.py``.

The viewer is a read-only local diagnostic surface, so security *is* the contract:

* loopback only, never a wildcard bind;
* an ephemeral session token on every data endpoint, checked with a constant-time compare
  and redacted from the access log;
* ``Host``/``Origin`` validation, so a page on another origin cannot read the run;
* containment by resolved path, so no traversal, absolute path or drive-qualified path can
  read a file outside an approved root;
* ``GET``/``HEAD`` only. There is no endpoint that can reach ``env.step()``.

Every test runs against a real server on loopback in a fixture that shuts it down.
``ThreadingHTTPServer.shutdown`` costs one ``serve_forever`` poll interval, so the
read-only tests share one module-scoped server and only the tests that mutate the stream
directory pay for their own; no test depends on another's side effects.
"""

from __future__ import annotations

import http.client
import json
import pathlib
import socket
import sys
from typing import Any, Iterator

import pytest

_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from tools.research_support import records as R  # noqa: E402
from tools.research_support.capture import trace_store as TS  # noqa: E402
from tools.research_support.capture.transport import (  # noqa: E402
    LatestFrameFileSink,
    MappedViewerLease,
)
from tools.research_support.viewer import server as S  # noqa: E402

_SECRET = "TOP-SECRET-NOT-FOR-THE-BROWSER"


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


def _frame(sequence: int) -> R.SceneFrame:
    entity = R.EntityId(kind=R.EntityKind.UAV, slot=0, label="uav-0")
    return R.SceneFrame(
        identity=R.SceneIdentity(
            run_id="run-1", trace_id="trace-1", episode_id="ep-1", world_id="w-1",
            lane_id=0, sequence=sequence,
        ),
        clock=R.SceneClock(
            simulation_time_s=float(sequence), geometry_time_s=float(sequence),
            decision_step=sequence, capture_wall_time_utc="2026-09-18T00:00:00Z",
            producer_monotonic_s=0.0,
        ),
        provenance=R.SceneProvenance(
            route="unit_test", environment_id="fixture",
            source_kind=R.SourceKind.SYNTHETIC_FIXTURE, policy_kind=R.PolicyKind.RULE_CONTROLLER,
            information_condition="privileged_truth", frame_kind=R.FrameKind.TRANSITION,
            capture_resolution="decision_boundary",
        ),
        geometry=R.SceneGeometry(bounds_m=(0.0, 0.0, 1000.0, 1000.0)),
        capability=R.SceneCapability(has_uav_positions=True),
        uavs=(R.UavState(entity=entity, position_m=(float(sequence), 2.0, 120.0)),),
        interval_metrics={"delivered_mbps": R.Measured.ok(0.0, unit="Mbps")},
        events=(
            R.DecisionEvent(time_s=float(sequence), event_type="skill_change", description="x"),
        ),
    )


def _build_layout(root: pathlib.Path) -> dict[str, pathlib.Path]:
    """A stream directory, a closed trace and a report root, plus a secret outside them."""

    stream = root / "stream"
    stream.mkdir(parents=True)
    trace = root / "trace"
    writer = TS.TraceWriter(
        trace, trace_id="trace-1", manifest={"route": "unit_test"}, chunk_frames=2
    )
    for sequence in range(3):
        writer.append(_frame(sequence).to_bytes(), sequence=sequence, time_s=float(sequence))
    writer.close()

    reports = root / "reports"
    reports.mkdir()
    (reports / "report.json").write_text('{"ok": true}', encoding="utf-8")

    (root / "secret.txt").write_text(_SECRET, encoding="utf-8")
    return {"root": root, "stream": stream, "trace": trace, "reports": reports}


def _start(layout: dict[str, pathlib.Path], **overrides: Any) -> S.ViewerServer:
    settings: dict[str, Any] = {
        "stream_dir": layout["stream"],
        "traces": {"run": layout["trace"]},
        "reports": {"report": layout["reports"]},
        "host": "127.0.0.1",
        "port": 0,
        "title": "unit test viewer",
        "banner": "SYNTHETIC ENGINEERING FIXTURE",
    }
    settings.update(overrides)
    return S.ViewerServer(S.ViewerConfig(**settings)).start()


@pytest.fixture(scope="module")
def layout(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pathlib.Path]:
    """Shared, read-only layout for the tests that do not publish a frame."""

    return _build_layout(tmp_path_factory.mktemp("viewer_shared"))


@pytest.fixture(scope="module")
def server(layout: dict[str, pathlib.Path]) -> Iterator[S.ViewerServer]:
    instance = _start(layout)
    try:
        yield instance
    finally:
        instance.stop()


@pytest.fixture()
def own_layout(tmp_path: pathlib.Path) -> dict[str, pathlib.Path]:
    """Private layout for a test that writes into the stream directory."""

    return _build_layout(tmp_path)


@pytest.fixture()
def own_server(own_layout: dict[str, pathlib.Path]) -> Iterator[S.ViewerServer]:
    instance = _start(own_layout)
    try:
        yield instance
    finally:
        instance.stop()


def _request(
    instance: S.ViewerServer,
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", instance.port, timeout=10.0)
    try:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        return response.status, {k.lower(): v for k, v in response.getheaders()}, body
    finally:
        connection.close()


def _json_request(instance: S.ViewerServer, path: str, **kwargs: Any) -> tuple[int, Any]:
    status, headers, body = _request(instance, path, **kwargs)
    assert headers.get("content-type", "").startswith("application/json"), headers
    return status, R.loads(body)


def _authed(instance: S.ViewerServer, route: str) -> str:
    joiner = "&" if "?" in route else "?"
    return f"{route}{joiner}t={instance.token}"


def _refuses_connection(host: str, port: int, *, timeout: float = 1.0) -> bool:
    """True when nothing is serving ``host:port``, by refusal or by no answer at all."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(timeout)
        try:
            probe.connect((host, port))
        except OSError:
            return True
    return False


# --------------------------------------------------------------------------------------
# Bind address
# --------------------------------------------------------------------------------------


def test_server_binds_loopback_only(server: S.ViewerServer) -> None:
    assert server.host == "127.0.0.1"
    assert server.url.startswith("http://127.0.0.1:")
    assert 0 < server.port < 65536


@pytest.mark.parametrize("host", ["0.0.0.0", "", "::", "192.168.1.10", "example.com"])
def test_config_refuses_a_non_loopback_bind(host: str) -> None:
    with pytest.raises(S.ViewerSecurityError, match="loopback only"):
        S.ViewerConfig(host=host, port=0)


def test_server_is_not_reachable_on_a_non_loopback_address(server: S.ViewerServer) -> None:
    address = None
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidate = info[4][0]
            if not candidate.startswith("127."):
                address = candidate
                break
    except OSError:  # pragma: no cover - depends on host name resolution
        address = None
    if address is None:  # pragma: no cover - single-interface hosts
        pytest.skip("no non-loopback IPv4 address available on this host")

    assert _refuses_connection(address, server.port)
    assert _refuses_connection("127.0.0.1", server.port) is False  # the control case


def test_free_port_returns_a_bindable_loopback_port(
    own_layout: dict[str, pathlib.Path]
) -> None:
    port = S.free_port()
    assert 0 < port < 65536
    instance = _start(own_layout, port=port)
    try:
        assert instance.port == port
        status, payload = _json_request(instance, _authed(instance, "/api/meta"))
        assert status == 200 and payload["mode"] == "live_and_replay"
    finally:
        instance.stop()


# --------------------------------------------------------------------------------------
# Token
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "route",
    ["/api/meta", "/api/frame", "/api/health", "/api/trace/index?label=run"],
)
def test_data_endpoints_refuse_a_missing_token(server: S.ViewerServer, route: str) -> None:
    status, payload = _json_request(server, route)
    assert status == 403
    assert "token" in payload["error"]
    assert payload["status"] == 403


@pytest.mark.parametrize("supplied", ["", "wrong", "x" * 43])
def test_data_endpoints_refuse_a_wrong_token(server: S.ViewerServer, supplied: str) -> None:
    status, _payload = _json_request(server, f"/api/meta?t={supplied}")
    assert status == 403
    status, _payload = _json_request(
        server, "/api/meta", headers={"X-RS-Token": supplied or "-"}
    )
    assert status == 403


def test_a_valid_token_is_accepted_in_the_query_or_the_header(server: S.ViewerServer) -> None:
    status, payload = _json_request(server, _authed(server, "/api/meta"))
    assert status == 200 and payload["title"] == "unit test viewer"
    status, payload = _json_request(server, "/api/meta", headers={"X-RS-Token": server.token})
    assert status == 200 and payload["mode"] == "live_and_replay"


def test_the_token_is_redacted_from_the_access_log(
    server: S.ViewerServer, capsys: pytest.CaptureFixture[str]
) -> None:
    status, _payload = _json_request(server, _authed(server, "/api/meta"))
    assert status == 200
    captured = capsys.readouterr()
    assert "/api/meta" in captured.err, "the access log did not record the request"
    assert server.token not in captured.err
    assert "<redacted>" in captured.err


# --------------------------------------------------------------------------------------
# Origin / Host
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "origin",
    [
        "http://evil.example",
        "https://evil.example:443",
        "http://127.0.0.1.evil.example",
        "null",
        "http://10.0.0.5:8765",
    ],
)
def test_a_foreign_origin_is_refused(server: S.ViewerServer, origin: str) -> None:
    status, payload = _json_request(
        server, _authed(server, "/api/meta"), headers={"Origin": origin}
    )
    assert status == 403
    assert "Origin" in payload["error"]


@pytest.mark.parametrize("origin", ["http://127.0.0.1:1", "http://localhost:8765"])
def test_a_loopback_origin_is_allowed(server: S.ViewerServer, origin: str) -> None:
    status, _payload = _json_request(
        server, _authed(server, "/api/meta"), headers={"Origin": origin}
    )
    assert status == 200


def test_a_foreign_host_header_is_refused(server: S.ViewerServer) -> None:
    status, payload = _json_request(
        server, _authed(server, "/api/meta"), headers={"Host": "evil.example"}
    )
    assert status == 403
    assert "Host" in payload["error"]
    # The index page is refused on a foreign Host too, not only the data routes.
    status, _headers, _body = _request(server, "/", headers={"Host": "evil.example"})
    assert status == 403


# --------------------------------------------------------------------------------------
# Containment
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        "",
        "/etc/passwd",
        "\\windows\\win.ini",
        "C:/Windows/win.ini",
        "c:secret.txt",
        "../secret.txt",
        "../../secret.txt",
        "app.css/../../../secret.txt",
    ],
)
def test_read_contained_refuses_every_escape(relative: str, tmp_path: pathlib.Path) -> None:
    root = tmp_path / "root"
    (root / "inner").mkdir(parents=True)
    (root / "app.css").write_text("body{}", encoding="utf-8")
    (tmp_path / "secret.txt").write_text(_SECRET, encoding="utf-8")
    with pytest.raises(S.ViewerSecurityError):
        S._read_contained(root, relative)


def test_read_contained_serves_a_contained_file(tmp_path: pathlib.Path) -> None:
    root = tmp_path / "root"
    (root / "inner").mkdir(parents=True)
    (root / "inner" / "app.js").write_text("// ok", encoding="utf-8")
    body, content_type = S._read_contained(root, "inner/app.js")
    assert body == b"// ok"
    assert "javascript" in content_type

    with pytest.raises(FileNotFoundError):
        S._read_contained(root, "inner/missing.js")
    with pytest.raises(FileNotFoundError):
        S._read_contained(root, "inner")  # directory listing is not offered


def test_read_contained_refuses_a_file_above_the_response_limit(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "big.bin").write_bytes(b"0" * 64)
    monkeypatch.setattr(S, "MAX_RESPONSE_BYTES", 8)
    with pytest.raises(S.ViewerSecurityError, match="response limit"):
        S._read_contained(root, "big.bin")


@pytest.mark.parametrize(
    "route",
    [
        "/static/../../secret.txt",
        "/static/../secret.txt",
        "/static/..%2f..%2fsecret.txt",
        "/static/..%2F..%2Fsecret.txt",
        "/static/%2e%2e/%2e%2e/secret.txt",
        "/static/..\\..\\secret.txt",
        "/static/....//secret.txt",
        "/static/C:/Windows/win.ini",
        "/static/",
    ],
)
def test_static_route_refuses_traversal_and_leaks_nothing(
    server: S.ViewerServer, route: str
) -> None:
    status, headers, body = _request(server, route)
    # A traversal is refused (403) or cannot resolve to a file at all (404). The server
    # never percent-decodes a path, so an encoded escape names a file that does not exist
    # inside the static root rather than escaping it.
    assert status in (403, 404), (route, status, body)
    assert headers.get("content-type", "").startswith("application/json")
    assert _SECRET.encode() not in body
    assert b"[fonts]" not in body  # nothing that looks like win.ini content


def test_static_route_serves_its_own_assets(server: S.ViewerServer) -> None:
    status, headers, body = _request(server, "/static/app.css")
    assert status == 200
    assert headers["content-type"].startswith("text/css")
    assert b"{" in body


def test_report_route_is_contained_and_labelled(server: S.ViewerServer) -> None:
    status, payload = _json_request(
        server, _authed(server, "/api/report?label=report&path=report.json")
    )
    assert status == 200 and payload == {"ok": True}

    status, _headers, body = _request(
        server, _authed(server, "/api/report?label=report&path=../secret.txt")
    )
    assert status == 403
    assert _SECRET.encode() not in body

    status, payload = _json_request(
        server, _authed(server, "/api/report?label=nope&path=report.json")
    )
    assert status == 403 and "unknown report root" in payload["error"]


# --------------------------------------------------------------------------------------
# Methods
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_mutating_verbs_are_refused(server: S.ViewerServer, method: str) -> None:
    status, payload = _json_request(server, _authed(server, "/api/meta"), method=method)
    assert status == 405
    assert "read-only" in payload["error"]


@pytest.mark.parametrize("method", ["OPTIONS", "TRACE", "FROBNICATE"])
def test_other_verbs_are_not_served(server: S.ViewerServer, method: str) -> None:
    status, _headers, _body = _request(server, "/", method=method)
    assert status in (400, 405, 501), method


def test_get_and_head_are_served(server: S.ViewerServer) -> None:
    status, headers, body = _request(server, "/")
    assert status == 200 and headers["content-type"].startswith("text/html")
    assert body

    status, headers, body = _request(server, "/", method="HEAD")
    assert status == 200
    assert body == b"", "HEAD must not carry a body"
    assert int(headers["content-length"]) > 0


def test_security_headers_are_present(server: S.ViewerServer) -> None:
    _status, headers, _body = _request(server, "/")
    assert headers["cache-control"] == "no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert "connect-src 'self'" in headers["content-security-policy"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]


# --------------------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------------------


def _external_urls(text: str) -> list[str]:
    """Occurrences of an absolute or protocol-relative URL, excluding XML namespaces.

    ``http://www.w3.org/2000/svg`` inside a ``data:`` URI is an XML namespace identifier,
    not a resource a browser fetches, so it is not an external dependency.
    """

    stripped = text.replace("http://www.w3.org/2000/svg", "")
    found = []
    for needle in ("http://", "https://", "//cdn", 'src="//', 'href="//'):
        if needle in stripped:
            found.append(needle)
    return found


def test_index_page_references_no_external_url(server: S.ViewerServer) -> None:
    status, _headers, body = _request(server, "/")
    assert status == 200
    page = body.decode("utf-8")
    assert _external_urls(page) == []
    # Every fetched asset is served by this server from its own static root.
    for attribute in ('href="', 'src="'):
        start = 0
        while True:
            index = page.find(attribute, start)
            if index < 0:
                break
            start = index + len(attribute)
            value = page[start : page.index('"', start)]
            assert value.startswith(("/static/", "data:", "#")), value
    assert "__RS_BOOTSTRAP__" not in page
    assert "__RS_TITLE__" not in page
    assert server.token in page  # the page receives the token; the log never shows it
    assert "unit test viewer" in page


def test_static_assets_reference_no_external_url(server: S.ViewerServer) -> None:
    for name in ("app.css", "app.js", "scene3d.js"):
        status, _headers, body = _request(server, f"/static/{name}")
        assert status == 200, name
        assert _external_urls(body.decode("utf-8")) == [], name


# --------------------------------------------------------------------------------------
# API payloads
# --------------------------------------------------------------------------------------


def test_every_api_route_returns_well_formed_json(server: S.ViewerServer) -> None:
    routes = [
        "/api/meta",
        "/api/frame",
        "/api/health",
        "/api/trace/index?label=run",
        "/api/trace/frames?label=run&start=0&count=2",
        "/api/trace/timeline?label=run",
    ]
    for route in routes:
        status, payload = _json_request(server, _authed(server, route))
        assert status == 200, route
        assert isinstance(payload, dict), route

    status, payload = _json_request(server, _authed(server, "/api/nonsense"))
    assert status == 404 and "no api route" in payload["error"]

    status, payload = _json_request(server, _authed(server, "/nonsense"))
    assert status == 404 and "no route" in payload["error"]


def test_missing_frame_is_a_structured_waiting_response(own_server: S.ViewerServer) -> None:
    status, payload = _json_request(own_server, _authed(own_server, "/api/frame"))
    assert status == 200, "a missing frame is not a server error"
    assert payload["frame"] is None
    assert payload["state"] == "WAITING"
    assert "no frame published yet" in payload["detail"]

    status, payload = _json_request(own_server, _authed(own_server, "/api/health"))
    assert status == 200 and payload == {"available": False}


def test_an_unparsable_frame_is_reported_as_an_error_state(
    own_server: S.ViewerServer, own_layout: dict[str, pathlib.Path]
) -> None:
    (own_layout["stream"] / "latest.json").write_bytes(b'{"clock": ')
    status, payload = _json_request(own_server, _authed(own_server, "/api/frame"))
    assert status == 200
    assert payload["frame"] is None
    assert payload["state"] == "ERROR"
    assert "unparsable frame" in payload["detail"]


def test_a_published_frame_is_served_and_renews_the_viewer_lease(
    own_server: S.ViewerServer, own_layout: dict[str, pathlib.Path]
) -> None:
    sink = LatestFrameFileSink(own_layout["stream"])
    try:
        assert sink.offer(_frame(7).to_bytes()) is True
    finally:
        sink.close()

    with MappedViewerLease.in_directory(own_layout["stream"], create=False) as lease:
        before = lease.expires_at_monotonic()
        status, payload = _json_request(own_server, _authed(own_server, "/api/frame"))
        after = lease.expires_at_monotonic()

    assert status == 200
    assert payload["state"] == "LIVE"
    assert payload["frame"]["identity"]["sequence"] == 7
    assert payload["sample_age_s"] >= 0.0
    assert after > before, "serving a frame tells the producer a viewer is present"

    status, health = _json_request(own_server, _authed(own_server, "/api/health"))
    assert status == 200 and health["available"] is False  # no health file published yet


def test_health_is_published_independently_of_a_frame(
    own_server: S.ViewerServer, own_layout: dict[str, pathlib.Path]
) -> None:
    sink = LatestFrameFileSink(own_layout["stream"])
    try:
        assert sink.write_health(R.dumps({"state": "LIVE", "refused_by_gate": 12}).encode()) is True
    finally:
        sink.close()
    status, payload = _json_request(own_server, _authed(own_server, "/api/health"))
    assert status == 200
    assert payload["available"] is True
    assert payload["refused_by_gate"] == 12


def test_viewer_state_reports_its_mode(own_layout: dict[str, pathlib.Path]) -> None:
    only_reports = S.ViewerState(S.ViewerConfig(reports={"r": own_layout["reports"]}))
    assert only_reports.mode == "reports_only"
    only_reports.close()

    replay = S.ViewerState(S.ViewerConfig(traces={"run": own_layout["trace"]}))
    assert replay.mode == "replay"
    replay.close()

    compare = S.ViewerState(
        S.ViewerConfig(traces={"a": own_layout["trace"], "b": own_layout["trace"]})
    )
    assert compare.mode == "compare"
    compare.close()

    live = S.ViewerState(S.ViewerConfig(stream_dir=own_layout["stream"]))
    assert live.mode == "live"
    assert live.latest_frame()["state"] == "WAITING"
    live.close()

    detached = S.ViewerState(S.ViewerConfig())
    assert detached.latest_frame()["state"] == "DISCONNECTED"
    assert "without a stream directory" in detached.latest_frame()["detail"]
    detached.close()


def test_trace_endpoints_expose_the_recorded_frames(server: S.ViewerServer) -> None:
    status, index = _json_request(server, _authed(server, "/api/trace/index?label=run"))
    assert status == 200
    assert index["trace_id"] == "trace-1"
    assert index["status"] == TS.STATUS_CLOSED
    assert index["n_frames"] == 3
    assert index["problems"] == []
    assert index["manifest"]["route"] == "unit_test"

    status, window = _json_request(
        server, _authed(server, "/api/trace/frames?label=run&start=1&count=1")
    )
    assert status == 200
    assert window["start"] == 1 and window["count"] == 1 and window["total"] == 3
    assert window["frames"][0]["identity"]["sequence"] == 1

    status, timeline = _json_request(server, _authed(server, "/api/trace/timeline?label=run"))
    assert status == 200
    assert [row["i"] for row in timeline["rows"]] == [0, 1, 2]
    assert timeline["rows"][0]["metrics"] == {"delivered_mbps": 0.0}
    assert timeline["rows"][0]["events"][0]["event_type"] == "skill_change"


def test_trace_frame_window_is_clamped(server: S.ViewerServer) -> None:
    status, window = _json_request(
        server, _authed(server, "/api/trace/frames?label=run&start=-5&count=100000")
    )
    assert status == 200
    assert window["start"] == 0
    assert window["count"] == 3
    status, meta = _json_request(server, _authed(server, "/api/meta"))
    assert meta["max_frames_per_request"] == S.MAX_FRAMES_PER_REQUEST


def test_unknown_trace_label_is_refused(server: S.ViewerServer) -> None:
    status, payload = _json_request(server, _authed(server, "/api/trace/index?label=ghost"))
    assert status == 403
    assert "unknown trace label" in payload["error"]


@pytest.mark.parametrize(
    "route, message",
    [
        ("/api/trace/index", "missing required query parameter"),
        ("/api/trace/index?label=run&label=run", "more than once"),
        ("/api/trace/index?label=" + "x" * 600, "too long"),
        ("/api/trace/frames?label=run&start=abc", None),
    ],
)
def test_bad_query_parameters_are_a_client_error(
    server: S.ViewerServer, route: str, message: str | None
) -> None:
    status, payload = _json_request(server, _authed(server, route))
    assert status == 400, route
    if message is not None:
        assert message in payload["error"]


def test_stopping_the_server_revokes_the_lease(own_layout: dict[str, pathlib.Path]) -> None:
    instance = _start(own_layout)
    status, _payload = _json_request(instance, _authed(instance, "/api/frame"))
    assert status == 200
    port = instance.port
    with MappedViewerLease.in_directory(own_layout["stream"], create=False) as lease:
        assert lease.expires_at_monotonic() > 0.0
        instance.stop()
        assert lease.expires_at_monotonic() == 0.0, "closing the viewer suspends extraction"
    assert _refuses_connection("127.0.0.1", port), "the port is released on shutdown"


def test_server_context_manager_starts_and_stops(own_layout: dict[str, pathlib.Path]) -> None:
    config = S.ViewerConfig(traces={"run": own_layout["trace"]}, host="127.0.0.1", port=0)
    with S.ViewerServer(config) as instance:
        status, payload = _json_request(instance, _authed(instance, "/api/meta"))
        assert status == 200 and payload["live_available"] is False
        assert payload["traces"][0]["label"] == "run"
        assert payload["traces"][0]["directory"] == "trace"
        assert "manifest" in payload["traces"][0]
    assert json.dumps(payload)  # the payload really is JSON-serialisable

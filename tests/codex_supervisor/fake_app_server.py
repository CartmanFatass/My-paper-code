"""Deterministic fake Codex binary for observer tests."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _write_schema(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "app-server.json").write_text(
        json.dumps(
            {
                "methods": [
                    "initialize",
                    "initialized",
                    "thread/start",
                    "thread/list",
                    "thread/read",
                    "thread/loaded/list",
                    "thread/resume",
                    "turn/start",
                    "turn/completed",
                    "item/started",
                    "item/completed",
                ]
            }
        ),
        encoding="utf-8",
    )


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, separators=(",", ":"), sort_keys=True) + "\n")
    sys.stdout.flush()


def _read() -> dict | None:
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def serve(mode: str) -> None:
    if mode == "stderr_then_exit":
        sys.stderr.write("diagnostic only\n")
        sys.stderr.flush()
        return
    if mode == "hang":
        while True:
            time.sleep(1)
    if mode == "oversized_line":
        size = int(os.environ.get("FAKE_OVERSIZE_BYTES", "20000000"))
        sys.stdout.write("{" + ("a" * size) + "}\n")
        sys.stdout.flush()
        return
    if mode == "malformed_line":
        sys.stdout.write("not-json\n")
        sys.stdout.flush()
        return
    initialized = False
    pages_sent = 0
    overload_reads = 0
    while True:
        message = _read()
        if message is None:
            return
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}
        if mode == "slow_response":
            time.sleep(0.05)
        if method == "initialize":
            _emit({"id": request_id, "result": {"serverInfo": {"name": "fake-app-server"}}})
            if mode == "exit_after_initialize":
                return
            continue
        if method == "initialized":
            initialized = True
            if mode == "unexpected_request":
                server_method = os.environ.get(
                    "FAKE_SERVER_REQUEST_METHOD",
                    "item/commandExecution/requestApproval",
                )
                _emit({"id": "server-1", "method": server_method, "params": {}})
            if mode == "burst":
                for index in range(int(os.environ.get("FAKE_BURST_COUNT", "1000"))):
                    thread_id = f"thr_{index % 100}"
                    turn_id = f"turn_{index}"
                    item_id = f"itm_{index}"
                    if index < 100:
                        _emit({"method": "thread/started", "params": {"thread": {"id": thread_id, "ephemeral": False}}})
                    else:
                        _emit(
                            {
                                "method": "item/agentMessage/delta",
                                "params": {
                                    "threadId": thread_id,
                                    "turnId": turn_id,
                                    "itemId": item_id,
                                    "delta": "BLOCKED FAILED RETIRED Portfolio should stop",
                                },
                            }
                        )
            continue
        if not initialized:
            _emit({"id": request_id, "error": {"code": -32000, "message": "not initialized"}})
            continue
        if method in {"thread/list", "thread/read"}:
            if mode == "no_response":
                continue
            if mode in {"overload_then_ok", "overload_matrix"} and overload_reads < int(os.environ.get("FAKE_OVERLOADS", "1")):
                overload_reads += 1
                _emit({"id": request_id, "error": {"code": -32001, "message": "overload"}})
                continue
            if method == "thread/list":
                if mode == "two_pages" and pages_sent == 0:
                    pages_sent += 1
                    _emit(
                        {
                            "id": request_id,
                            "result": {
                                "data": [{"id": "thr_a", "preview": "one"}],
                                "nextCursor": "page-2",
                            },
                        }
                    )
                    continue
                _emit({"id": request_id, "result": {"data": [{"id": "thr_b", "preview": "two"}]}})
                continue
            status = os.environ.get("FAKE_THREAD_STATUS", "idle")
            thread = {
                "id": params.get("threadId"),
                "ephemeral": False,
                "status": {"type": status},
            }
            if params.get("includeTurns"):
                thread["turns"] = list(globals().setdefault("_FAKE_TURNS", []))
            _emit({"id": request_id, "result": {"thread": thread}})
            continue
        if method == "thread/loaded/list":
            configured = os.environ.get("FAKE_LOADED_THREADS")
            if configured is not None:
                data = [item for item in configured.split(",") if item]
            else:
                data = list(globals().setdefault("_FAKE_LOADED", ["thr_canary"]))
            _emit({"id": request_id, "result": {"data": data}})
            continue
        if method == "thread/name/set":
            _emit({"id": request_id, "result": {}})
            continue
        if method in {"thread/start", "turn/start", "thread/resume", "thread/fork", "turn/steer", "turn/interrupt", "thread/compact/start", "review/start"}:
            if mode == "mutation_overload":
                _emit({"id": request_id, "error": {"code": -32001, "message": "overload"}})
                continue
            if method == "thread/start":
                ephemeral = bool(params.get("ephemeral"))
                if mode == "canary_not_ephemeral":
                    ephemeral = False
                thread_id = "thr_canary"
                globals().setdefault("_FAKE_LOADED", []).append(thread_id)
                _emit(
                    {
                        "id": request_id,
                        "result": {"thread": {"id": thread_id, "ephemeral": ephemeral, "path": None}},
                    }
                )
                _emit({"method": "thread/started", "params": {"thread": {"id": thread_id, "ephemeral": ephemeral}}})
                continue
            if method == "thread/resume":
                thread_id = params.get("threadId")
                loaded = globals().setdefault("_FAKE_LOADED", [])
                if thread_id and thread_id not in loaded:
                    loaded.append(thread_id)
                _emit({"id": request_id, "result": {"thread": {"id": thread_id, "ephemeral": False, "status": {"type": "idle"}}}})
                continue
            if method == "turn/start":
                turn_id = "turn_canary"
                thread_id = params.get("threadId")
                globals().setdefault("_FAKE_TURNS", []).append(
                    {
                        "id": turn_id,
                        "clientUserMessageId": params.get("clientUserMessageId"),
                        "status": "inProgress",
                    }
                )
                _emit({"id": request_id, "result": {"turn": {"id": turn_id, "status": "inProgress"}}})
                _emit({"method": "turn/started", "params": {"threadId": thread_id, "turn": {"id": turn_id}}})
                if mode == "canary_failed":
                    _emit({"method": "turn/completed", "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "failed"}}})
                elif mode == "canary_wrong_text":
                    _emit({"method": "item/agentMessage/delta", "params": {"itemId": "itm_1", "delta": "NOPE"}})
                    _emit({"method": "turn/completed", "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed"}}})
                elif mode == "canary_timeout":
                    time.sleep(2)
                else:
                    _emit({"method": "item/started", "params": {"item": {"id": "itm_1", "type": "agentMessage"}}})
                    _emit({"method": "item/agentMessage/delta", "params": {"itemId": "itm_1", "delta": "HMASD_APP_SERVER_OBSERVER_OK"}})
                    _emit({"method": "item/completed", "params": {"item": {"id": "itm_1", "type": "agentMessage"}}})
                    _emit({"method": "turn/completed", "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed"}}})
                continue
            _emit({"id": request_id, "result": {}})
            continue
        _emit({"id": request_id, "error": {"code": -32601, "message": "unknown method"}})


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = os.environ.get("FAKE_APP_SERVER_MODE", "handshake_ok")
    if args[:1] == ["--version"]:
        sys.stdout.write("codex-fake 0.0-test\n")
        return 0
    if args[:3] == ["app-server", "generate-json-schema", "--out"]:
        _write_schema(Path(args[3]))
        return 0
    if args[:1] == ["app-server"]:
        serve(mode)
        return 0
    sys.stderr.write("unsupported fake argv\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

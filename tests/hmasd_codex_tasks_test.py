"""Behavioral tests for the native Codex App Server task adapter."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable

import pytest

from scripts import hmasd_codex_tasks as tasks


WORK_ID = "a" * 64
LOCATOR = f".codex/runtime/work/ready/{WORK_ID}/packet.json"


class FakeTransport:
    """In-memory JSONL peer which exercises the real client state machine."""

    def __init__(self, responder: Callable[[dict[str, Any], "FakeTransport"], None]) -> None:
        self.responder = responder
        self.requests: list[dict[str, Any]] = []
        self.pending: list[bytes | BaseException | None] = []
        self.closed = False

    def write_line(self, data: bytes) -> None:
        request = json.loads(data)
        self.requests.append(request)
        self.responder(request, self)

    def read_line(self, timeout: float) -> bytes | None:
        if not self.pending:
            raise TimeoutError(f"no fake response within {timeout}")
        value = self.pending.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value

    def emit(self, value: dict[str, Any]) -> None:
        self.pending.append(
            (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )

    def close(self) -> None:
        self.closed = True


def response_peer(
    *,
    history_text: str | None = None,
    complete_turn: bool = False,
    completion_has_thread_id: bool = True,
    read_turn_id: str = "turn-old",
    read_turn_status: str = "completed",
    read_thread_status: dict[str, Any] | None = None,
    read_thread_error: dict[str, Any] | None = None,
    fork_error: dict[str, Any] | None = None,
    listed_threads: list[dict[str, Any]] | None = None,
    read_thread_name: str | None = None,
    read_thread_cwd: str | None = None,
) -> FakeTransport:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        method = request.get("method")
        request_id = request.get("id")
        if request_id is None:
            return
        if method == "initialize":
            result: dict[str, Any] = {"serverInfo": {"name": "fake", "version": "1"}}
        elif method == "thread/list":
            result = {
                "data": listed_threads if listed_threads is not None else [
                    {
                        "id": "thread-1",
                        "sessionId": "thread-1",
                        "name": "EM alpha",
                        "status": {"type": "idle"},
                        "cwd": "C:/Projects/HMASD",
                        "source": "appServer",
                        "modelProvider": "openai",
                        "createdAt": 10,
                        "updatedAt": 20,
                        "ephemeral": False,
                        "preview": "LIST_SECRET_TEXT",
                        "path": "C:/secret/rollout.jsonl",
                        "turns": [{"items": [{"text": "LIST_TURN_SECRET"}]}],
                        "extra": {"secret": "LIST_EXTRA_SECRET"},
                        "gitInfo": {"originUrl": "https://token@example.invalid/repo"},
                    }
                ],
                "nextCursor": None,
            }
        elif method == "thread/start":
            result = {
                "thread": {"id": "thread-new", "turns": []},
                "model": "fake",
                "modelProvider": "fake",
                "cwd": request["params"]["cwd"],
                "approvalPolicy": "never",
                "approvalsReviewer": "user",
                "sandbox": {"type": "dangerFullAccess"},
                "instructionSources": ["C:/Projects/HMASD/AGENTS.md"],
            }
        elif method == "thread/name/set":
            result = {}
        elif method == "thread/fork":
            if fork_error is not None:
                peer.emit({"id": request_id, "error": fork_error})
                return
            result = {
                "thread": {"id": "thread-fork", "turns": []},
                "model": "fake",
                "modelProvider": "fake",
                "cwd": "C:/Projects/HMASD",
                "approvalPolicy": "never",
                "approvalsReviewer": "user",
                "sandbox": {"type": "dangerFullAccess"},
            }
        elif method == "thread/resume":
            result = {
                "thread": {"id": request["params"]["threadId"], "turns": []},
                "model": "fake",
                "modelProvider": "fake",
                "cwd": "C:/Projects/HMASD",
                "approvalPolicy": "never",
                "approvalsReviewer": "user",
                "sandbox": {"type": "dangerFullAccess"},
            }
        elif method == "thread/read":
            if read_thread_error is not None:
                peer.emit({"id": request_id, "error": read_thread_error})
                return
            items = []
            if history_text is not None:
                items = [
                    {
                        "type": "userMessage",
                        "id": "item-1",
                        "content": [{"type": "text", "text": history_text}],
                    }
                ]
            result = {
                "thread": {
                    "id": request["params"]["threadId"],
                    **({"status": read_thread_status} if read_thread_status is not None else {}),
                    **({"name": read_thread_name} if read_thread_name is not None else {}),
                    **({"cwd": read_thread_cwd} if read_thread_cwd is not None else {}),
                    "turns": [
                        {"id": read_turn_id, "status": read_turn_status, "items": items}
                    ],
                }
            }
        elif method == "turn/start":
            result = {"turn": {"id": "turn-new", "status": "inProgress", "items": []}}
        else:
            raise AssertionError(f"unexpected method: {method}")
        peer.emit({"id": request_id, "result": result})
        if method == "turn/start" and complete_turn:
            params = {
                "turn": {"id": "turn-new", "status": "completed", "items": []},
            }
            if completion_has_thread_id:
                params["threadId"] = request["params"]["threadId"]
            peer.emit(
                {
                    "method": "turn/completed",
                    "params": params,
                }
            )

    return FakeTransport(respond)


def conformance_peer(
    *, final_text: str = '{"status":"HMASD_NATIVE_ADAPTER_CONFORMANCE_OK"}',
    extra_item: dict[str, Any] | None = None,
    turn_start_hook: Callable[[dict[str, Any], FakeTransport], bool] | None = None,
    completion_status: str = "completed",
    omit_completion_items: bool = False,
    completion_error: dict[str, Any] | None = None,
) -> FakeTransport:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "turn/start" and turn_start_hook is not None:
            if turn_start_hook(request, peer):
                return
        if request.get("method") == "turn/start":
            response_peer().responder(request, peer)
            items: list[dict[str, Any]] = [
                {
                    "type": "userMessage",
                    "id": "user-1",
                    "content": [{"type": "text", "text": "PRIVATE_CONFORMANCE_PROMPT"}],
                },
                {"type": "agentMessage", "id": "agent-1", "text": final_text},
            ]
            if extra_item is not None:
                items.insert(1, extra_item)
            turn: dict[str, Any] = {
                "id": "turn-new",
                "status": completion_status,
            }
            if not omit_completion_items:
                turn["items"] = items
            if completion_error is not None:
                turn["error"] = completion_error
            peer.emit(
                {
                    "method": "turn/completed",
                    "params": {
                        "threadId": request["params"]["threadId"],
                        "turn": turn,
                    },
                }
            )
            return
        response_peer().responder(request, peer)

    return FakeTransport(respond)


def test_dispatch_envelope_is_canonical_and_binds_exact_slice() -> None:
    actual = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha")
    assert actual == (
        b'{\n'
        b'  "attempt": 1,\n'
        b'  "mode": "DISPATCH",\n'
        b'  "packet_locator": ".codex/runtime/work/ready/' + WORK_ID.encode() + b'/packet.json",\n'
        b'  "protocol": "hmasd.work-packet.dispatch.v2",\n'
        b'  "target_identity": "EM-alpha",\n'
        b'  "work_id": "' + WORK_ID.encode() + b'"\n'
        b'}\n'
    )
    assert tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha") == actual


@pytest.mark.parametrize("locator", ["../packet.json", "C:/packet.json", "a\\b.json"])
def test_dispatch_envelope_rejects_non_repository_relative_locator(locator: str) -> None:
    with pytest.raises(ValueError, match="repository-relative POSIX"):
        tasks.dispatch_envelope_bytes(WORK_ID, locator, "EM-alpha")


def test_probe_and_list_use_initialize_handshake_without_starting_a_turn() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.list_threads(cwd="C:/Projects/HMASD")

    assert result["status"] == "OK"
    assert result["threads"][0]["id"] == "thread-1"
    assert [request.get("method") for request in peer.requests] == [
        "initialize",
        "initialized",
        "thread/list",
    ]
    assert peer.requests[0]["params"]["capabilities"] == {"experimentalApi": True}
    listing = peer.requests[-1]
    assert listing["params"]["sourceKinds"] == [
        "cli",
        "vscode",
        "exec",
        "appServer",
        "subAgent",
        "subAgentReview",
        "subAgentCompact",
        "subAgentThreadSpawn",
        "subAgentOther",
        "unknown",
    ]
    assert "useStateDbOnly" not in listing["params"]
    assert peer.closed


def test_public_list_projects_only_safe_native_task_facts() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.list_threads(cwd="C:/Projects/HMASD")
    assert result["threads"] == [
        {
            "id": "thread-1",
            "sessionId": "thread-1",
            "name": "EM alpha",
            "status": {"type": "idle"},
            "cwd": "C:/Projects/HMASD",
            "source": "appServer",
            "modelProvider": "openai",
            "createdAt": 10,
            "updatedAt": 20,
            "ephemeral": False,
        }
    ]
    serialized = json.dumps(result)
    for secret in (
        "LIST_SECRET_TEXT",
        "LIST_TURN_SECRET",
        "LIST_EXTRA_SECRET",
        "token@example.invalid",
        "rollout.jsonl",
    ):
        assert secret not in serialized


def test_public_read_omits_content_but_private_send_still_deduplicates() -> None:
    envelope = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha").decode()
    peer = response_peer(history_text=envelope, read_turn_status="inProgress")
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        public = client.read_thread("thread-1")
        sent = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
    assert public == {
        "status": "OK",
        "thread": {
            "id": "thread-1",
            "turns": [{"id": "turn-old", "status": "inProgress"}],
        },
    }
    assert WORK_ID not in json.dumps(public)
    assert sent["status"] == "ALREADY_DELIVERED"


def test_create_uses_never_approval_highest_permissions_and_sets_logical_name() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.create_thread(cwd="C:/Projects/HMASD", target_identity="EM-alpha")

    assert result == {
        "status": "CREATED",
        "thread_id": "thread-new",
        "session_id": "thread-new",
        "instruction_sources": ["C:/Projects/HMASD/AGENTS.md"],
        "cwd": "C:/Projects/HMASD",
        "model": "fake",
        "model_provider": "fake",
        "approval_policy": "never",
        "sandbox": {"type": "dangerFullAccess"},
    }
    start = next(request for request in peer.requests if request.get("method") == "thread/start")
    assert start["params"] == {
        "approvalPolicy": "never",
        "config": {"model_reasoning_effort": "max"},
        "cwd": "C:/Projects/HMASD",
        "model": "gpt-5.6-sol",
        "sandbox": "danger-full-access",
    }
    naming = next(
        request for request in peer.requests if request.get("method") == "thread/name/set"
    )
    assert naming["params"] == {"name": "EM-alpha", "threadId": "thread-new"}


def test_send_suppresses_duplicate_work_id_in_full_thread_history() -> None:
    envelope = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha").decode()
    peer = response_peer(history_text=envelope, read_turn_status="inProgress")
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")

    assert result == {
        "status": "ALREADY_DELIVERED",
        "attempt": 1,
        "thread_id": "thread-1",
        "turn_id": "turn-old",
        "turn_status": "inProgress",
        "work_id": WORK_ID,
    }
    assert "turn/start" not in [request.get("method") for request in peer.requests]


def test_send_starts_one_turn_with_the_exact_envelope() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send(
            "thread-1",
            WORK_ID,
            LOCATOR,
            "EM-alpha",
            repo=Path("C:/Projects/HMASD"),
        )

    assert result == {
        "attempt": 1,
        "mode": "DISPATCH",
        "status": "DELIVERED",
        "thread_id": "thread-1",
        "turn_id": "turn-new",
        "work_id": WORK_ID,
    }
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"] == {
        "approvalPolicy": "never",
        "input": [
            {
                "type": "text",
                "text": tasks.dispatch_envelope_bytes(
                    WORK_ID, LOCATOR, "EM-alpha"
                ).decode(),
            },
            {
                "type": "text",
                "text": "$hmasd-em-task",
            },
            {
                "type": "skill",
                "name": "hmasd-em-task",
                "path": "C:/Projects/HMASD/.agents/skills/hmasd-em-task/SKILL.md",
            },
        ],
        "effort": "max",
        "sandboxPolicy": {"type": "dangerFullAccess"},
        "threadId": "thread-1",
    }


def test_timeout_after_turn_start_is_unknown_and_never_retried() -> None:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "turn/start":
            return
        response_peer().responder(request, peer)

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")

    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "TIMEOUT_AFTER_SEND"
    assert sum(request.get("method") == "turn/start" for request in peer.requests) == 1


def test_same_work_id_with_different_envelope_is_a_delivery_conflict() -> None:
    conflicting = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "CM-alpha").decode()
    peer = response_peer(history_text=conflicting, read_turn_status="inProgress")
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
    assert result == {
        "status": "DELIVERY_CONFLICT",
        "thread_id": "thread-1",
        "work_id": WORK_ID,
    }
    assert "turn/start" not in [request.get("method") for request in peer.requests]


def test_terminal_attempt_without_return_witness_sends_one_resume_attempt() -> None:
    first = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha").decode()
    peer = response_peer(history_text=first, read_turn_status="completed")
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
    assert result["status"] == "DELIVERED"
    assert result["attempt"] == 2
    assert result["mode"] == "RESUME"
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    envelope = json.loads(turn["params"]["input"][0]["text"])
    assert envelope == {
        "attempt": 2,
        "mode": "RESUME",
        "packet_locator": LOCATOR,
        "protocol": "hmasd.work-packet.dispatch.v2",
        "target_identity": "EM-alpha",
        "work_id": WORK_ID,
    }
    assert len(turn["params"]["input"]) == 1


def attempt_history_peer(
    attempts: list[tuple[int, str, str]],
    *,
    timeout_first_turn: bool = False,
    reveal_after_timeout: bool = False,
) -> FakeTransport:
    read_count = 0

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        nonlocal read_count
        method = request.get("method")
        if method == "turn/start" and timeout_first_turn:
            return
        if method != "thread/read":
            response_peer().responder(request, peer)
            return
        read_count += 1
        visible = attempts if not reveal_after_timeout or read_count > 1 else []
        turns = []
        for attempt, turn_id, status in visible:
            text = tasks.dispatch_envelope_bytes(
                WORK_ID,
                LOCATOR,
                "EM-alpha",
                attempt=attempt,
                mode="DISPATCH" if attempt == 1 else "RESUME",
            ).decode()
            turns.append(
                {
                    "id": turn_id,
                    "status": status,
                    "items": [
                        {
                            "type": "userMessage",
                            "id": f"user-{attempt}",
                            "content": [{"type": "text", "text": text}],
                        }
                    ],
                }
            )
        peer.emit(
            {
                "id": request["id"],
                "result": {"thread": {"id": "thread-1", "turns": turns}},
            }
        )

    return FakeTransport(respond)


def test_unknown_send_reobserves_committed_turn_without_blind_resend() -> None:
    peer = attempt_history_peer(
        [(1, "turn-observed", "inProgress")],
        timeout_first_turn=True,
        reveal_after_timeout=True,
    )
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
    assert result == {
        "status": "DELIVERY_OBSERVED_AFTER_UNKNOWN",
        "reason": "TIMEOUT_AFTER_SEND",
        "thread_id": "thread-1",
        "turn_id": "turn-observed",
        "turn_status": "inProgress",
        "work_id": WORK_ID,
        "attempt": 1,
    }
    assert sum(request.get("method") == "turn/start" for request in peer.requests) == 1


def test_three_terminal_attempts_exhaust_without_a_fourth_turn() -> None:
    peer = attempt_history_peer(
        [
            (1, "turn-1", "completed"),
            (2, "turn-2", "failed"),
            (3, "turn-3", "interrupted"),
        ]
    )
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
    assert result == {
        "status": "RETURN_WITNESS_MISSING_AFTER_ATTEMPTS",
        "thread_id": "thread-1",
        "work_id": WORK_ID,
        "attempt_statuses": [
            {"attempt": 1, "turn_id": "turn-1", "turn_status": "completed"},
            {"attempt": 2, "turn_id": "turn-2", "turn_status": "failed"},
            {"attempt": 3, "turn_id": "turn-3", "turn_status": "interrupted"},
        ],
        "resume_condition": {
            "latest_turn_terminal": True,
            "return_witness": "ABSENT",
            "next_attempt": 4,
            "max_attempts": 3,
            "attempt_below_max": False,
        },
    }
    assert "turn/start" not in [request.get("method") for request in peer.requests]


def test_unexpected_server_request_after_send_requires_observation_not_a_response() -> None:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "turn/start":
            peer.emit(
                {
                    "id": 900,
                    "method": "item/commandExecution/requestApproval",
                    "params": {"reason": "unexpected"},
                }
            )
            return
        response_peer().responder(request, peer)

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")

    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "SERVER_REQUEST_AFTER_SEND"
    assert "server_request" not in result
    assert "requestApproval" not in json.dumps(result)
    assert all(request.get("id") != 900 for request in peer.requests)


@pytest.mark.parametrize("after_send", [False, True])
def test_request_server_request_is_never_reflected_before_or_after_send(
    after_send: bool,
) -> None:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        peer.emit(
            {
                "id": 901,
                "method": "item/tool/requestUserInput",
                "params": {"token": "TOKEN_VALUE", "path": "C:/secret", "prompt": "PRIVATE"},
            }
        )

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client._request("thread/list", {}, after_send=after_send)
    assert result == (
        {"status": "UNKNOWN", "reason": "SERVER_REQUEST_AFTER_SEND"}
        if after_send
        else {"status": "INTERVENTION_REQUIRED", "reason": "SERVER_REQUEST"}
    )
    rendered = json.dumps(result)
    for secret in ("TOKEN_VALUE", "C:/secret", "PRIVATE", "requestUserInput"):
        assert secret not in rendered


def test_wait_server_request_is_never_reflected() -> None:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "thread/read":
            peer.emit(
                {
                    "id": request["id"],
                    "result": {
                        "thread": {
                            "id": "thread-1",
                            "turns": [{"id": "turn-1", "status": "inProgress"}],
                        }
                    },
                }
            )
            return
        if request.get("method") == "thread/resume":
            peer.emit(
                {
                    "id": 902,
                    "method": "item/tool/requestUserInput",
                    "params": {"token": "WAIT_TOKEN", "path": "C:/wait-secret"},
                }
            )
            return
        response_peer().responder(request, peer)

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.wait("thread-1", "turn-1", timeout=0.1)
    assert result == {"status": "INTERVENTION_REQUIRED", "reason": "SERVER_REQUEST"}
    rendered = json.dumps(result)
    assert "WAIT_TOKEN" not in rendered
    assert "C:/wait-secret" not in rendered


def test_wait_consumes_unique_matching_turn_completed_without_thread_id() -> None:
    peer = response_peer(complete_turn=True, completion_has_thread_id=False)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        sent = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
        result = client.wait("thread-1", sent["turn_id"], timeout=0.1)

    assert result == {
        "status": "COMPLETED",
        "thread_id": "thread-1",
        "turn_id": "turn-new",
        "turn_status": "completed",
    }


def test_same_connection_wait_consumes_completion_without_read_or_resume() -> None:
    peer = response_peer(complete_turn=True)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        sent = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
        before = [request.get("method") for request in peer.requests]
        result = client.wait(
            "thread-1",
            sent["turn_id"],
            timeout=0.1,
            resume=False,
            observe_active=False,
        )
        after = [request.get("method") for request in peer.requests]

    assert result["status"] == "COMPLETED"
    assert after.count("thread/read") == before.count("thread/read")
    assert after.count("thread/resume") == before.count("thread/resume")


def test_same_connection_unbounded_wait_ignores_transport_timeouts_without_read(
) -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        sent = client.send("thread-1", WORK_ID, LOCATOR, "EM-alpha")
        before = [request.get("method") for request in peer.requests]
        peer.pending.extend([TimeoutError(), TimeoutError()])
        peer.emit(
            {
                "method": "turn/completed",
                "params": {
                    "threadId": "thread-1",
                    "turn": {
                        "id": sent["turn_id"],
                        "status": "completed",
                        "items": [],
                    },
                },
            }
        )
        result = client.wait(
            "thread-1",
            sent["turn_id"],
            timeout=None,
            resume=False,
            observe_active=False,
        )
        after = [request.get("method") for request in peer.requests]

    assert result["status"] == "COMPLETED"
    assert after.count("thread/read") == before.count("thread/read")
    assert after.count("thread/resume") == before.count("thread/resume")


def test_same_connection_finite_wait_times_out_without_observing_active_turn() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        result = client.wait(
            "thread-1",
            "turn-new",
            timeout=0.01,
            resume=False,
            observe_active=False,
        )

    assert result == {
        "status": "WAIT_TIMEOUT",
        "thread_id": "thread-1",
        "turn_id": "turn-new",
    }
    assert peer.requests == []


def test_standalone_wait_resumes_inflight_thread_before_listening() -> None:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        response_peer(
            read_turn_id="turn-new", read_turn_status="inProgress"
        ).responder(request, peer)
        if request.get("method") == "thread/resume":
            peer.emit(
                {
                    "method": "turn/completed",
                    "params": {
                        "turn": {
                            "id": "turn-new",
                            "status": "completed",
                            "items": [],
                        }
                    },
                }
            )

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.wait("thread-1", "turn-new", timeout=0.1)
    assert result["status"] == "COMPLETED"
    assert "thread/resume" in [request.get("method") for request in peer.requests]


def test_execute_plan_waits_for_its_started_turn_without_redundant_resume(
    tmp_path: Path,
) -> None:
    peer = response_peer(complete_turn=True, listed_threads=[])
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
            wait_timeout=0.1,
        )

    assert result == {
        "status": "COMPLETED",
        "thread_id": "thread-new",
        "turn_id": "turn-new",
        "turn_status": "completed",
    }
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/resume") == 1


@pytest.mark.parametrize(
    ("delivery_status", "expected_resume"),
    [("DELIVERED", False), ("ALREADY_DELIVERED", True)],
)
def test_cli_send_keeps_owned_client_alive_until_terminal_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    delivery_status: str,
    expected_resume: bool,
) -> None:
    events: list[str] = []

    class CliClient:
        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        def __enter__(self) -> "CliClient":
            events.append("enter")
            return self

        def __exit__(self, *_: Any) -> None:
            events.append("close")

        def send(self, *_: Any, **__: Any) -> dict[str, Any]:
            events.append("send")
            return {"status": delivery_status, "thread_id": "thread-1", "turn_id": "turn-1"}

        def wait(
            self,
            thread_id: str,
            turn_id: str,
            *,
            timeout: float | None,
            resume: bool,
            observe_active: bool,
        ) -> dict[str, Any]:
            assert (thread_id, turn_id, timeout, resume, observe_active) == (
                "thread-1",
                "turn-1",
                None,
                expected_resume,
                expected_resume,
            )
            events.append("terminal")
            return {"status": "COMPLETED", "thread_id": thread_id, "turn_id": turn_id}

    monkeypatch.setattr(tasks, "AppServerClient", CliClient)
    assert tasks.main(
        [
            "--server-command",
            "fake",
            "send",
            "--thread-id",
            "thread-1",
            "--work-id",
            WORK_ID,
            "--packet-locator",
            LOCATOR,
            "--target-identity",
            "EM-alpha",
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPLETED"
    assert events == ["enter", "send", "terminal", "close"]


def test_cli_execute_plan_requests_terminal_observation_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_path = tmp_path / "plan.json"
    tasks_path = tmp_path / "tasks.json"
    plan_path.write_text(json.dumps({"verb": "NOOP"}), encoding="utf-8")
    tasks_path.write_text("[]", encoding="utf-8")
    events: list[str] = []

    class CliClient:
        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        def __enter__(self) -> "CliClient":
            events.append("enter")
            return self

        def __exit__(self, *_: Any) -> None:
            events.append("close")

        def execute_plan(self, *_: Any, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["wait_for_terminal"] is True
            assert kwargs["wait_timeout"] is None
            events.append("terminal")
            return {"status": "NO_EFFECT"}

    monkeypatch.setattr(tasks, "AppServerClient", CliClient)
    assert tasks.main(
        [
            "--server-command",
            "fake",
            "execute-plan",
            "--plan",
            str(plan_path),
            "--observed-tasks",
            str(tasks_path),
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "NO_EFFECT"
    assert events == ["enter", "terminal", "close"]


@pytest.mark.parametrize(
    "argv",
    [
        [
            "send",
            "--thread-id",
            "thread-1",
            "--work-id",
            WORK_ID,
            "--packet-locator",
            LOCATOR,
            "--target-identity",
            "EM-alpha",
            "--wait-timeout",
            "1",
        ],
        [
            "execute-plan",
            "--plan",
            "plan.json",
            "--wait-timeout",
            "1",
        ],
    ],
)
def test_one_shot_cli_does_not_expose_a_finite_terminal_wait(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        tasks._parser().parse_args(argv)
    assert raised.value.code == 2


@pytest.mark.parametrize("verb", ["CONFLICT", "NOOP", "WAIT", "OBSERVE", "PUBLISH"])
def test_execute_plan_non_dispatch_verbs_make_zero_protocol_requests(verb: str) -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan({"verb": verb})

    assert result == {"status": "NO_EFFECT", "verb": verb}
    assert peer.requests == []


def test_execute_plan_rejects_ordinary_clerk_target_before_any_native_effect() -> None:
    peer = response_peer()
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "Workflow-Clerk",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
            observed_tasks=[],
        )
    assert result == {
        "status": "PROTOCOL_DEFECT",
        "reason": "ORDINARY_PACKET_CANNOT_TARGET_CLERK",
        "work_id": WORK_ID,
    }
    assert peer.requests == []


def test_execute_plan_dispatch_requires_explicit_observed_task_snapshot() -> None:
    peer = response_peer()
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
        )
    assert result == {
        "status": "PROTOCOL_DEFECT",
        "reason": "OBSERVED_TASK_SNAPSHOT_REQUIRED",
        "work_id": WORK_ID,
    }
    assert peer.requests == []


def test_active_snapshot_without_thread_identity_is_observation_unknown() -> None:
    peer = response_peer()
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-beta",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
            observed_tasks={"tasks": [{"lifecycle": "ACTIVE"}]},
        )
    assert result == {
        "status": "ACTIVE_PEER_OBSERVATION_UNKNOWN",
        "thread_ids": ["MISSING_THREAD_ID"],
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_active_native_peer_without_protocol_work_id_is_observation_unknown() -> None:
    peer = response_peer(read_thread_status={"type": "active"})
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-beta",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
            observed_tasks={"tasks": [{"lifecycle": "ACTIVE", "thread_id": "thread-1"}]},
        )
    assert result == {
        "status": "ACTIVE_PEER_OBSERVATION_UNKNOWN",
        "thread_ids": ["thread-1"],
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_create_then_dispatches_without_a_daemon() -> None:
    peer = response_peer()
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "requested_target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
            observed_tasks=[],
        )

    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-new"
    assert [request.get("method") for request in peer.requests].count("thread/start") == 1
    assert [request.get("method") for request in peer.requests].count("thread/name/set") == 1
    assert [request.get("method") for request in peer.requests].count("turn/start") == 1


def test_execute_plan_new_first_dispatch_does_not_probe_return_witness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    peer = response_peer()
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }

    def unexpected_reconcile(**_: Any) -> None:
        raise AssertionError("first dispatch must not inspect a return witness")

    monkeypatch.setattr(tasks.hmasd_work_packet, "reconcile_once", unexpected_reconcile)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
            observed_tasks=[],
        )
    assert result["status"] == "DELIVERED"


def test_create_observes_and_compares_active_peers_before_creating_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    peer_work = "b" * 64
    envelope = tasks.dispatch_envelope_bytes(peer_work, LOCATOR, "EM-beta").decode()
    peer = response_peer(
        history_text=envelope,
        read_thread_status={"type": "active"},
        listed_threads=[
            {
                "id": "thread-peer",
                "name": "EM-beta",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "active"},
            }
        ],
    )
    monkeypatch.setattr(
        tasks.hmasd_work_packet,
        "compare_work_ids",
        lambda *_: {
            "outcome": "CONFLICT",
            "packet_conflicts": [],
            "pairs": [{"reasons": [{"type": "OWNED_PATH_OVERLAP"}]}],
        },
    )
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks={"tasks": [{"lifecycle": "ACTIVE", "thread_id": "thread-peer"}]},
        )
    assert result["status"] == "WORK_OVERLAP_CONFLICT"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_terminal_history_with_tasks_mapping_return_never_resumes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    envelope = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha").decode()
    peer = response_peer(
        history_text=envelope,
        read_turn_status="completed",
        read_thread_name="EM-alpha",
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
    )
    observed: list[tuple[Path, str, Any]] = []

    def reconcile_once(*, repo: Path, work_id: str, observed_tasks: Any) -> dict[str, Any]:
        observed.append((repo, work_id, observed_tasks))
        return {
            "ok": True,
            "operation": "reconcile",
            "plan": {
                "verb": "NOOP_TERMINAL",
                "task_resolution": {"status": "RETURN_WITNESS"},
            },
        }

    monkeypatch.setattr(tasks.hmasd_work_packet, "reconcile_once", reconcile_once)
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks={"tasks": []},
        )
    assert result == {
        "status": "NO_EFFECT",
        "reason": "RETURN_WITNESS_PRESENT",
        "work_id": WORK_ID,
        "thread_id": "thread-1",
    }
    assert observed == [(tmp_path.absolute(), WORK_ID, [])]
    methods = [request.get("method") for request in peer.requests]
    assert "thread/resume" not in methods
    assert "turn/start" not in methods


def test_damaged_return_reconstruction_is_not_treated_as_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    envelope = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha").decode()
    peer = response_peer(
        history_text=envelope,
        read_turn_status="completed",
        read_thread_name="EM-alpha",
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
    )
    monkeypatch.setattr(
        tasks.hmasd_work_packet,
        "read_return",
        lambda **_: pytest.fail("adapter must not use shallow return read"),
    )
    monkeypatch.setattr(
        tasks.hmasd_work_packet,
        "reconcile_once",
        lambda **_: {
            "ok": True,
            "operation": "reconcile",
            "plan": {
                "verb": "CONFLICT",
                "defect": {"code": "STALE_RESULT_REF"},
            },
        },
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }

    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )

    assert result == {
        "status": "PROTOCOL_DEFECT",
        "reason": "RETURN_WITNESS_INVALID",
        "work_id": WORK_ID,
        "thread_id": "thread-1",
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/resume" not in methods
    assert "turn/start" not in methods


def test_execute_plan_attempt_three_still_observes_present_return_before_exhausting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    turns = []
    for attempt, status in ((1, "completed"), (2, "failed"), (3, "interrupted")):
        envelope = tasks.dispatch_envelope_bytes(
            WORK_ID,
            LOCATOR,
            "EM-alpha",
            attempt=attempt,
            mode="DISPATCH" if attempt == 1 else "RESUME",
        ).decode()
        turns.append(
            {
                "id": f"turn-{attempt}",
                "status": status,
                "items": [{"type": "userMessage", "content": [{"type": "text", "text": envelope}]}],
            }
        )
    peer = response_peer()
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        monkeypatch.setattr(
            client,
            "_list_all_threads",
            lambda **_: {
                "status": "OK",
                "threads": [{"id": "thread-1", "name": "EM-alpha", "cwd": tmp_path.as_posix()}],
            },
        )
        monkeypatch.setattr(
            client,
            "_read_thread_full",
            lambda _: {"status": "OK", "thread": {"id": "thread-1", "name": "EM-alpha", "turns": turns}},
        )
        monkeypatch.setattr(
            tasks.hmasd_work_packet,
            "reconcile_once",
            lambda **_: {
                "ok": True,
                "operation": "reconcile",
                "plan": {
                    "verb": "NOOP_TERMINAL",
                    "task_resolution": {"status": "RETURN_WITNESS"},
                },
            },
        )
        monkeypatch.setattr(client, "send", lambda *_, **__: pytest.fail("must not exhaust before return observation"))
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result == {
        "status": "NO_EFFECT",
        "reason": "RETURN_WITNESS_PRESENT",
        "work_id": WORK_ID,
        "thread_id": "thread-1",
    }


@pytest.mark.parametrize(
    "failure",
    [
        tasks.hmasd_work_packet.InvalidPacket("invalid witness"),
        tasks.hmasd_work_packet.PacketConflict("conflicting witness"),
    ],
)
def test_execute_plan_terminal_history_with_invalid_return_never_resumes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    envelope = tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, "EM-alpha").decode()
    peer = response_peer(
        history_text=envelope,
        read_turn_status="completed",
        read_thread_name="EM-alpha",
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
    )

    def reconcile_once(**_: Any) -> None:
        raise failure

    monkeypatch.setattr(tasks.hmasd_work_packet, "reconcile_once", reconcile_once)
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result == {
        "status": "PROTOCOL_DEFECT",
        "reason": "RETURN_WITNESS_INVALID",
        "work_id": WORK_ID,
        "thread_id": "thread-1",
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/resume" not in methods
    assert "turn/start" not in methods


def test_execute_plan_create_reuses_one_fresh_exact_native_identity(tmp_path: Path) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-existing",
                "sessionId": "thread-existing",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
    )
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "requested_target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-existing"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_reuses_exact_cached_identity_when_cwd_list_omits_it(
    tmp_path: Path,
) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
    )
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    observed = [
        {
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "PARKED",
            "logical_identity": "EM-alpha",
            "thread_id": "thread-cached",
        }
    ]
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed,
        )

    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-cached"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_uses_plan_thread_id_when_cwd_list_omits_existing_target(
    tmp_path: Path,
) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"status": "REUSE", "thread_id": "thread-planned"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )

    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-planned"
    assert "thread/start" not in [request.get("method") for request in peer.requests]


def test_dispatch_existing_fails_closed_on_fresh_cache_identity_conflict(
    tmp_path: Path,
) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"status": "REUSE", "thread_id": "thread-planned"},
    }
    observed = [
        {
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "COMPLETED",
            "logical_identity": "EM-alpha",
            "thread_id": "thread-planned",
        }
    ]
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed,
        )

    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["target_identity"] == "EM-alpha"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/read" not in methods
    assert "thread/start" not in methods
    assert "turn/start" not in methods


@pytest.mark.parametrize("listed_id", [None, "", "   ", 7])
def test_exact_listed_identity_with_invalid_thread_id_never_creates(
    tmp_path: Path,
    listed_id: Any,
) -> None:
    row: dict[str, Any] = {
        "name": "EM-alpha",
        "cwd": tmp_path.as_posix(),
        "status": {"type": "idle"},
    }
    if listed_id is not None:
        row["id"] = listed_id
    peer = response_peer(listed_threads=[row])
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )

    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "reason": "LISTED_TARGET_THREAD_ID_INVALID",
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods
    assert "turn/start" not in methods


@pytest.mark.parametrize(
    ("read_name", "read_cwd", "observed_name"),
    [
        ("EM-beta", "MATCH", "EM-beta"),
        ("EM-alpha", "C:/Projects/elsewhere", "EM-alpha"),
    ],
)
def test_cached_identity_read_mismatch_never_creates(
    tmp_path: Path,
    read_name: str,
    read_cwd: str,
    observed_name: str,
) -> None:
    actual_cwd = str(tmp_path) if read_cwd == "MATCH" else read_cwd
    peer = response_peer(
        listed_threads=[],
        read_thread_name=read_name,
        read_thread_cwd=actual_cwd,
    )
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    observed = [
        {
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "PARKED",
            "logical_identity": "EM-alpha",
            "thread_id": "thread-cached",
        }
    ]
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed,
        )

    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "thread_id": "thread-cached",
        "observed_name": observed_name,
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods
    assert "turn/start" not in methods


def test_cached_identity_unknown_read_never_creates(tmp_path: Path) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_error={"code": -32001, "message": "not observed"},
    )
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    observed = [
        {
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "PARKED",
            "logical_identity": "EM-alpha",
            "thread_id": "thread-cached",
        }
    ]
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed,
        )

    assert result["status"] == "ERROR"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods
    assert "turn/start" not in methods


def test_execute_plan_scans_all_native_list_pages_before_reusing_identity(
    tmp_path: Path,
) -> None:
    pages = {
        None: ([{"id": "thread-other", "name": "EM-beta", "cwd": tmp_path.as_posix()}], "cursor-2"),
        "cursor-2": ([{"id": "thread-existing", "name": "EM-alpha", "cwd": tmp_path.as_posix()}], None),
    }

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "thread/list":
            data, cursor = pages[request["params"].get("cursor")]
            peer.emit({"id": request["id"], "result": {"data": data, "nextCursor": cursor}})
            return
        response_peer(read_thread_name="EM-alpha").responder(request, peer)

    peer = FakeTransport(respond)
    plan = {"verb": "CREATE_TASK_INTENT", "work_id": WORK_ID, "target_identity": "EM-alpha"}
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-existing"
    list_requests = [item for item in peer.requests if item.get("method") == "thread/list"]
    assert [item["params"].get("cursor") for item in list_requests] == [None, "cursor-2"]
    methods = [item.get("method") for item in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_detects_duplicate_identity_across_native_list_pages_before_create(
    tmp_path: Path,
) -> None:
    pages = {
        None: ([{"id": "thread-1", "name": "EM-alpha", "cwd": tmp_path.as_posix()}], "cursor-2"),
        "cursor-2": ([{"id": "thread-2", "name": "EM-alpha", "cwd": tmp_path.as_posix()}], None),
    }

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "thread/list":
            data, cursor = pages[request["params"].get("cursor")]
            peer.emit({"id": request["id"], "result": {"data": data, "nextCursor": cursor}})
            return
        response_peer().responder(request, peer)

    peer = FakeTransport(respond)
    plan = {"verb": "CREATE_TASK_INTENT", "work_id": WORK_ID, "target_identity": "EM-alpha"}
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "thread_ids": ["thread-1", "thread-2"],
    }
    methods = [item.get("method") for item in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_fails_closed_on_repeated_native_list_cursor(tmp_path: Path) -> None:
    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "thread/list":
            peer.emit({"id": request["id"], "result": {"data": [], "nextCursor": "cursor-loop"}})
            return
        response_peer().responder(request, peer)

    peer = FakeTransport(respond)
    plan = {"verb": "CREATE_TASK_INTENT", "work_id": WORK_ID, "target_identity": "EM-alpha"}
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result == {"status": "TASK_LIST_PAGINATION_DEFECT"}
    methods = [item.get("method") for item in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods


def test_execute_plan_create_rejects_duplicate_fresh_native_identity(tmp_path: Path) -> None:
    rows = [
        {
            "id": f"thread-{index}",
            "name": "EM-alpha",
            "cwd": tmp_path.as_posix(),
            "status": {"type": "idle"},
        }
        for index in (1, 2)
    ]
    peer = response_peer(listed_threads=rows)
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "thread_ids": ["thread-1", "thread-2"],
    }
    assert "turn/start" not in [request.get("method") for request in peer.requests]


def test_dispatch_existing_rejects_duplicate_fresh_native_identity(tmp_path: Path) -> None:
    rows = [
        {
            "id": f"thread-{index}",
            "name": "EM-alpha",
            "cwd": tmp_path.as_posix(),
            "status": {"type": "idle"},
        }
        for index in (1, 2)
    ]
    peer = response_peer(listed_threads=rows, read_thread_name="EM-alpha")
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }

    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )

    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "thread_ids": ["thread-1", "thread-2"],
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/read" not in methods
    assert "thread/resume" not in methods
    assert "turn/start" not in methods


def test_execute_plan_dispatch_rechecks_thread_id_and_canonical_name(tmp_path: Path) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-1",
                "name": "CM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["observed_name"] == "CM-alpha"
    assert "turn/start" not in [request.get("method") for request in peer.requests]


def test_execute_plan_compare_conflict_prevents_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
    )
    compared: list[list[str]] = []

    def compare(_: Path, work_ids: list[str]) -> dict[str, Any]:
        compared.append(work_ids)
        return {"outcome": "CONFLICT", "work_ids": work_ids, "pairs": []}

    monkeypatch.setattr(tasks.hmasd_work_packet, "compare_work_ids", compare)
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    peer_work = "b" * 64
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            peer_work_ids=[peer_work],
            observed_tasks=[],
        )
    assert result["status"] == "WORK_OVERLAP_CONFLICT"
    assert result["compare_outcome"] == "CONFLICT"
    assert compared == [[WORK_ID, peer_work]]
    assert "turn/start" not in [request.get("method") for request in peer.requests]


@pytest.mark.parametrize(
    ("native_thread_status", "turn_status"),
    [
        ({"type": "active"}, "completed"),
        ({"type": "idle"}, "inProgress"),
    ],
)
def test_active_runtime_row_is_a_peer_only_when_native_thread_or_turn_is_active(
    native_thread_status: dict[str, Any], turn_status: str
) -> None:
    peer_work = "b" * 64
    envelope = tasks.dispatch_envelope_bytes(peer_work, LOCATOR, "EM-beta").decode()
    peer = response_peer(
        history_text=envelope,
        read_thread_status=native_thread_status,
        read_turn_status=turn_status,
    )
    observed = {
        "tasks": [
            {"thread_id": "thread-1", "lifecycle": "ACTIVE"},
        ]
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        work_ids, unknown_threads = client._peer_work_ids(
            observed, (), current_thread_id="thread-current"
        )
    assert work_ids == [peer_work]
    assert unknown_threads == []


def test_idle_native_thread_does_not_keep_historical_work_id_as_active_peer() -> None:
    peer_work = "b" * 64
    envelope = tasks.dispatch_envelope_bytes(peer_work, LOCATOR, "EM-beta").decode()
    peer = response_peer(
        history_text=envelope,
        read_thread_status={"type": "idle"},
        read_turn_status="completed",
    )
    observed = {
        "tasks": [
            {"thread_id": "thread-1", "lifecycle": "ACTIVE"},
        ]
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        work_ids, unknown_threads = client._peer_work_ids(
            observed, (), current_thread_id="thread-current"
        )
    assert work_ids == []
    assert unknown_threads == []


def test_native_not_loaded_thread_is_active_peer_observation_unknown() -> None:
    peer = response_peer(read_thread_status={"type": "notLoaded"})
    observed = {"tasks": [{"thread_id": "thread-1", "lifecycle": "RUNNING"}]}
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        work_ids, unknown_threads = client._peer_work_ids(
            observed, (), current_thread_id="thread-current"
        )
    assert work_ids == []
    assert unknown_threads == ["thread-1"]


def test_active_runtime_row_with_unreadable_native_thread_remains_unknown() -> None:
    peer = response_peer(read_thread_error={"code": -32001, "message": "unavailable"})
    observed = {
        "tasks": [
            {"thread_id": "thread-1", "lifecycle": "ACTIVE"},
        ]
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        work_ids, unknown_threads = client._peer_work_ids(
            observed, (), current_thread_id="thread-current"
        )
    assert work_ids == []
    assert unknown_threads == ["thread-1"]


def test_root_override_bypasses_compare_but_is_bound_in_native_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
    )
    monkeypatch.setattr(
        tasks.hmasd_work_packet,
        "compare_work_ids",
        lambda *_: {
            "outcome": "CONFLICT",
            "packet_conflicts": [],
            "pairs": [
                {"reasons": [{"type": "OWNED_PATH_OVERLAP", "left": "a", "right": "a"}]}
            ],
        },
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            peer_work_ids=["b" * 64],
            root_override_reason="user authorized exact overlap",
            observed_tasks=[],
        )
    assert result["status"] == "DELIVERED"
    assert result["warning"] == "ROOT_OVERRIDE_ACTIVE"
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    envelope = json.loads(turn["params"]["input"][0]["text"])
    assert envelope["root_override_reason"] == "user authorized exact overlap"


@pytest.mark.parametrize(
    "comparison",
    [
        {
            "outcome": "CONFLICT",
            "packet_conflicts": [],
            "pairs": [{"reasons": [{"type": "EFFECT_RESOURCE_OVERLAP"}]}],
        },
        {
            "outcome": "CONFLICT",
            "packet_conflicts": [{"code": "STALE_AUTHORITY"}],
            "pairs": [],
        },
        {
            "outcome": "UNKNOWN",
            "packet_conflicts": [],
            "pairs": [{"reasons": [{"type": "EFFECT_STATE_UNKNOWN"}]}],
        },
    ],
)
def test_root_override_cannot_bypass_effect_authority_or_observation_defects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, comparison: dict[str, Any]
) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
    )
    monkeypatch.setattr(tasks.hmasd_work_packet, "compare_work_ids", lambda *_: comparison)
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {"thread_id": "thread-1"},
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
            peer_work_ids=["b" * 64],
            root_override_reason="user authorized only a known write overlap",
        )
    assert result["status"] == "WORK_OVERLAP_CONFLICT"
    assert "turn/start" not in [request.get("method") for request in peer.requests]


@pytest.mark.parametrize(
    ("target", "skill"),
    [
        ("Portfolio", "hmasd-portfolio-task"),
        ("EM-alpha", "hmasd-em-task"),
        ("CM-alpha", "hmasd-cm-task"),
    ],
)
def test_first_turn_bootstrap_skill_is_a_mechanical_target_kind_mapping(
    target: str, skill: str
) -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send(
            "thread-1", WORK_ID, LOCATOR, target, repo=Path("C:/Projects/HMASD")
        )
    assert result["status"] == "DELIVERED"
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"]["input"][1] == {"type": "text", "text": f"${skill}"}
    assert turn["params"]["input"][2] == {
        "type": "skill",
        "name": skill,
        "path": f"C:/Projects/HMASD/.agents/skills/{skill}/SKILL.md",
    }


def test_execute_plan_uses_canonical_target_identity_not_requested_alias() -> None:
    peer = response_peer()
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "requested_target_identity": "EM/alpha/g1",
        "target_identity": "EM-alpha",
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd="C:/Projects/HMASD", observed_tasks=[]
        )
    assert result["status"] == "DELIVERED"
    naming = next(
        request for request in peer.requests if request.get("method") == "thread/name/set"
    )
    assert naming["params"]["name"] == "EM-alpha"
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"]["input"][1]["text"] == "$hmasd-em-task"


def test_cm_create_and_first_turn_use_sol_high() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        created = client.create_thread(
            cwd="C:/Projects/HMASD", target_identity="CM-alpha"
        )
        sent = client.send(
            created["thread_id"], WORK_ID, LOCATOR, "CM-alpha", repo=Path("C:/Projects/HMASD")
        )
    assert sent["status"] == "DELIVERED"
    start = next(request for request in peer.requests if request.get("method") == "thread/start")
    assert start["params"]["model"] == "gpt-5.6-sol"
    assert start["params"]["config"] == {"model_reasoning_effort": "high"}
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"]["effort"] == "high"


def test_ephemeral_fork_is_available_for_live_conformance_without_dispatch_cli() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.fork_thread("thread-1", ephemeral=True)
    assert result == {"status": "FORKED", "thread_id": "thread-fork", "ephemeral": True}
    fork = next(request for request in peer.requests if request.get("method") == "thread/fork")
    assert fork["params"] == {
        "approvalPolicy": "never",
        "ephemeral": True,
        "excludeTurns": True,
        "sandbox": "danger-full-access",
        "threadId": "thread-1",
    }


def test_invalid_json_and_eof_are_structured_before_any_effect() -> None:
    for line, expected in [(b"not-json\n", "INVALID_JSON"), (None, "EOF")]:
        peer = FakeTransport(lambda request, transport: transport.pending.append(line))
        with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
            result = client.probe()
        assert result["status"] == expected


@pytest.mark.parametrize("after_send", [False, True])
def test_jsonrpc_error_is_safe_and_retains_exact_code(
    after_send: bool,
) -> None:
    secret_error = {
        "code": -32600,
        "message": "invalid C:/secret/rollout.jsonl\nPROMPT: do not reveal",
        "data": {"secret": "TOKEN_VALUE", "prompt": "PRIVATE_PROMPT"},
    }
    peer = response_peer(fork_error=secret_error)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client._request(
            "thread/fork", {"threadId": "thread-source"}, after_send=after_send
        )
    expected: dict[str, Any] = {
        "status": "UNKNOWN" if after_send else "ERROR",
        "error_code": -32600,
        "error_message": "server error details withheld",
    }
    if after_send:
        expected["reason"] = "ERROR_AFTER_SEND"
    assert result == expected
    rendered = json.dumps(result)
    assert "TOKEN_VALUE" not in rendered
    assert "PRIVATE_PROMPT" not in rendered
    assert "C:/secret" not in rendered
    assert "\n" not in result["error_message"]
    assert len(result["error_message"]) <= 160


def test_subprocess_transport_cleanup_terminates_its_child() -> None:
    code = "import sys,time; sys.stdin.readline(); time.sleep(30)"
    transport = tasks.JsonlProcessTransport([sys.executable, "-c", code])
    process = transport.process
    transport.close()
    assert process.poll() is not None


def test_default_windows_launcher_resolves_a_createprocess_executable() -> None:
    command = tasks.default_server_command()
    if sys.platform == "win32":
        assert Path(command[0]).name.lower() == "codex.exe"
        assert Path(command[0]).is_file()
    assert command[1:] == ("app-server",)
    version = subprocess.run(
        [command[0], "--version"], capture_output=True, text=True, timeout=5, check=False
    )
    assert version.returncode == 0, version.stderr
    assert "codex-cli" in version.stdout


def test_conformance_uses_only_ephemeral_fork_and_one_strict_readonly_turn() -> None:
    peer = conformance_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.conformance("thread-source", wait_timeout=0.1)

    assert result == {
        "status": "CONFORMANCE_OK",
        "source_thread_id": "thread-source",
        "thread_id": "thread-fork",
        "turn_id": "turn-new",
        "turn_status": "completed",
        "ephemeral": True,
        "response_verified": True,
    }
    methods = [request.get("method") for request in peer.requests]
    assert methods == [
        "initialize",
        "initialized",
        "thread/fork",
        "turn/start",
    ]
    assert all(
        method not in methods
        for method in (
            "thread/start",
            "thread/name/set",
            "thread/archive",
            "thread/read",
            "thread/resume",
        )
    )
    fork = next(request for request in peer.requests if request.get("method") == "thread/fork")
    assert fork["params"] == {
        "approvalPolicy": "never",
        "ephemeral": True,
        "excludeTurns": True,
        "sandbox": "read-only",
        "threadId": "thread-source",
    }
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"] == {
        "approvalPolicy": "never",
        "effort": "low",
        "input": [
            {
                "type": "text",
                "text": (
                    "HMASD native adapter conformance probe. Do not call tools. "
                    "Return exactly this JSON object and no other text: "
                    '{"status":"HMASD_NATIVE_ADAPTER_CONFORMANCE_OK"}'
                ),
            }
        ],
        "model": "gpt-5.6-luna",
        "outputSchema": {
            "additionalProperties": False,
            "properties": {
                "status": {
                    "const": "HMASD_NATIVE_ADAPTER_CONFORMANCE_OK",
                    "type": "string",
                }
            },
            "required": ["status"],
            "type": "object",
        },
        "sandboxPolicy": {"networkAccess": False, "type": "readOnly"},
        "threadId": "thread-fork",
    }
    assert "PRIVATE_CONFORMANCE_PROMPT" not in json.dumps(result)


def test_conformance_consumes_the_completion_notification_buffered_during_turn_start() -> None:
    peer = conformance_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.conformance("thread-source", wait_timeout=0.1)
    assert result["status"] == "CONFORMANCE_OK"
    assert [request.get("method") for request in peer.requests] == [
        "initialize",
        "initialized",
        "thread/fork",
        "turn/start",
    ]


def test_conformance_reports_safe_exact_jsonrpc_fork_error_code() -> None:
    peer = response_peer(
        fork_error={
            "code": -32600,
            "message": "ephemeral fork C:/secret/path\nPRIVATE_PROMPT",
            "data": {"secret": "TOKEN_VALUE"},
        }
    )
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.conformance("thread-source", wait_timeout=0.1)
    assert result == {
        "status": "CONFORMANCE_FAILED",
        "reason": "SERVER_ERROR_-32600",
        "source_thread_id": "thread-source",
        "error_code": -32600,
        "error_message": "server error details withheld",
    }
    rendered = json.dumps(result)
    for secret in ("TOKEN_VALUE", "PRIVATE_PROMPT", "C:/secret/path"):
        assert secret not in rendered
    assert "turn/start" not in [request.get("method") for request in peer.requests]


@pytest.mark.parametrize(
    ("final_text", "extra_item", "reason"),
    [
        ('{"status":"wrong"}', None, "FINAL_RESPONSE_MISMATCH"),
        (
            '{"status":"HMASD_NATIVE_ADAPTER_CONFORMANCE_OK"}',
            {"type": "commandExecution", "id": "tool-1", "status": "completed"},
            "UNEXPECTED_TURN_ITEM",
        ),
    ],
)
def test_conformance_fails_closed_on_wrong_response_or_tool_item(
    final_text: str, extra_item: dict[str, Any] | None, reason: str
) -> None:
    peer = conformance_peer(final_text=final_text, extra_item=extra_item)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.conformance("thread-source", wait_timeout=0.1)
    assert result["status"] == "CONFORMANCE_FAILED"
    assert result["reason"] == reason
    assert "PRIVATE_CONFORMANCE_PROMPT" not in json.dumps(result)
    assert "commandExecution" not in json.dumps(result)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"omit_completion_items": True}, "TERMINAL_TURN_ITEMS_MISSING"),
        (
            {
                "completion_status": "failed",
                "completion_error": {"message": "PRIVATE_TURN_ERROR"},
            },
            "TERMINAL_TURN_NOT_RECONSTRUCTED",
        ),
    ],
)
def test_conformance_fails_closed_on_incomplete_or_failed_completion_notification(
    kwargs: dict[str, Any], reason: str
) -> None:
    peer = conformance_peer(**kwargs)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.conformance("thread-source", wait_timeout=0.1)
    assert result["status"] == "CONFORMANCE_FAILED"
    assert result["reason"] == reason
    assert "PRIVATE_TURN_ERROR" not in json.dumps(result)
    assert "thread/read" not in [request.get("method") for request in peer.requests]
    assert "thread/resume" not in [request.get("method") for request in peer.requests]


def test_conformance_timeout_after_turn_start_is_fail_closed_without_retry() -> None:
    def timeout_turn(_: dict[str, Any], __: FakeTransport) -> bool:
        return True

    peer = conformance_peer(turn_start_hook=timeout_turn)
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        result = client.conformance("thread-source", wait_timeout=0.01)
    assert result == {
        "status": "CONFORMANCE_FAILED",
        "reason": "TIMEOUT_AFTER_SEND",
        "source_thread_id": "thread-source",
        "thread_id": "thread-fork",
        "ephemeral": True,
    }
    assert sum(request.get("method") == "turn/start" for request in peer.requests) == 1


def test_conformance_server_request_is_not_answered_or_exposed() -> None:
    def server_request(_: dict[str, Any], peer: FakeTransport) -> bool:
        peer.emit(
            {
                "id": 777,
                "method": "item/tool/requestUserInput",
                "params": {"secret": "SERVER_REQUEST_SECRET"},
            }
        )
        return True

    peer = conformance_peer(turn_start_hook=server_request)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.conformance("thread-source", wait_timeout=0.1)
    assert result["status"] == "CONFORMANCE_FAILED"
    assert result["reason"] == "SERVER_REQUEST_AFTER_SEND"
    assert "SERVER_REQUEST_SECRET" not in json.dumps(result)
    assert all(request.get("id") != 777 for request in peer.requests)


@pytest.mark.parametrize(
    ("terminal_kind", "reason"),
    [
        ("timeout", "WAIT_TIMEOUT"),
        ("eof", "EOF"),
        ("server_request", "SERVER_REQUEST"),
    ],
)
def test_conformance_notification_wait_fails_closed_without_read_or_resume(
    terminal_kind: str, reason: str
) -> None:
    def start_without_completion(request: dict[str, Any], peer: FakeTransport) -> bool:
        response_peer().responder(request, peer)
        if terminal_kind == "eof":
            peer.pending.append(None)
        elif terminal_kind == "server_request":
            peer.emit(
                {
                    "id": 778,
                    "method": "item/tool/requestUserInput",
                    "params": {"secret": "NOTIFICATION_SERVER_SECRET"},
                }
            )
        return True

    peer = conformance_peer(turn_start_hook=start_without_completion)
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        result = client.conformance("thread-source", wait_timeout=0.01)
    assert result["status"] == "CONFORMANCE_FAILED"
    assert result["reason"] == reason
    rendered = json.dumps(result)
    assert "NOTIFICATION_SERVER_SECRET" not in rendered
    methods = [request.get("method") for request in peer.requests]
    assert "thread/read" not in methods
    assert "thread/resume" not in methods
    assert all(request.get("id") != 778 for request in peer.requests)

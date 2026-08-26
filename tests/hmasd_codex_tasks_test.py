"""Behavioral tests for the native Codex App Server task adapter."""

from __future__ import annotations

import hashlib
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
PARTICIPANT_SLICE_INSTRUCTION = (
    "Complete only the exact Work Packet slice above. First reuse any existing exact "
    "return; otherwise read the packet, complete its bounded assignment, publish its "
    "typed result, and return that immutable witness."
)
VALIDATED_RETURN_STUB = {
    "schema_version": 1,
    "work_id": WORK_ID,
    "receiver": {"logical_identity": "EM-alpha", "generation": 1},
    "agent_result": {"status": "COMPLETED"},
}


def observed_em(thread_id: str = "thread-1") -> list[dict[str, Any]]:
    return [
        {
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "lifecycle": "PARKED",
            "thread_id": thread_id,
        }
    ]


def create_em_plan(
    *,
    work_id: str = WORK_ID,
    target_identity: str = "EM-alpha",
    direction_id: str = "alpha",
    requested_target_identity: str | None = None,
) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": work_id,
        "target_identity": target_identity,
        "task_resolution": {
            "status": "CREATE_TASK",
            "logical_identity": target_identity,
            "kind": "em",
            "direction_id": direction_id,
            "generation": 1,
        },
    }
    if requested_target_identity is not None:
        plan["requested_target_identity"] = requested_target_identity
    return plan


def reuse_em_plan(
    *,
    thread_id: str = "thread-1",
    work_id: str = WORK_ID,
    lifecycle: str = "PARKED",
) -> dict[str, Any]:
    return {
        "verb": "DISPATCH_EXISTING",
        "work_id": work_id,
        "target_identity": "EM-alpha",
        "task_resolution": {
            "status": "REUSE",
            "logical_identity": "EM-alpha",
            "kind": "em",
            "generation": 1,
            "lifecycle": lifecycle,
            "thread_id": thread_id,
        },
    }


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


class StatefulParticipantPeer:
    """Native participant lifecycle peer with one scenario-specific turn hook."""

    def __init__(
        self,
        cwd: Path,
        *,
        turn_hook: Callable[
            [dict[str, Any], dict[str, Any]], dict[str, Any]
        ],
        start_status: str = "idle",
        instruction_sources: list[str] | None = None,
        preserve_history: bool = False,
    ) -> None:
        self.cwd = cwd
        self.turn_hook = turn_hook
        self.start_status = start_status
        self.instruction_sources = instruction_sources or []
        self.preserve_history = preserve_history
        self.thread: dict[str, Any] | None = None
        self.transport = FakeTransport(self._respond)

    @property
    def requests(self) -> list[dict[str, Any]]:
        return self.transport.requests

    def _respond(self, request: dict[str, Any], peer: FakeTransport) -> None:
        request_id = request.get("id")
        if request_id is None:
            return
        method = request.get("method")
        if method == "initialize":
            result: dict[str, Any] = {
                "serverInfo": {"name": "fake", "version": "1"}
            }
        elif method == "thread/list":
            result = {
                "data": [] if self.thread is None else [self.thread],
                "nextCursor": None,
            }
        elif method == "thread/start":
            self.thread = {
                "id": "thread-em-alpha",
                "name": None,
                "cwd": request["params"]["cwd"],
                "threadSource": request["params"].get("threadSource"),
                "status": {"type": self.start_status},
                "turns": [],
            }
            result = {
                "thread": self.thread,
                "model": "fake",
                "modelProvider": "fake",
                "cwd": request["params"]["cwd"],
                "approvalPolicy": "never",
                "sandbox": {"type": "dangerFullAccess"},
                "instructionSources": self.instruction_sources,
            }
        elif method == "thread/name/set":
            assert self.thread is not None
            self.thread["name"] = request["params"]["name"]
            result = {}
        elif method == "thread/read":
            assert self.thread is not None
            result = {"thread": self.thread}
        elif method == "thread/resume":
            assert self.thread is not None
            result = {
                "thread": self.thread,
                "model": "fake",
                "modelProvider": "fake",
                "cwd": str(self.cwd),
                "approvalPolicy": "never",
                "sandbox": {"type": "dangerFullAccess"},
            }
        elif method == "turn/start":
            assert self.thread is not None
            terminal_turn = self.turn_hook(request, self.thread)
            if self.preserve_history:
                self.thread["turns"].append(terminal_turn)
            else:
                self.thread["turns"] = [terminal_turn]
            peer.emit(
                {
                    "id": request_id,
                    "result": {
                        "turn": {
                            "id": terminal_turn["id"],
                            "status": "inProgress",
                            "items": [],
                        }
                    },
                }
            )
            peer.emit(
                {
                    "method": "turn/completed",
                    "params": {
                        "threadId": self.thread["id"],
                        "turn": terminal_turn,
                    },
                }
            )
            return
        else:
            raise AssertionError(f"unexpected method: {method}")
        peer.emit({"id": request_id, "result": result})


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
    read_thread_source: str | None = None,
) -> FakeTransport:
    created_thread: dict[str, Any] | None = None

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        nonlocal created_thread
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
            created_thread = {
                "id": "thread-new",
                "name": None,
                "cwd": request["params"]["cwd"],
                "threadSource": request["params"].get("threadSource"),
                "turns": [],
            }
            result = {
                "thread": created_thread,
                "model": "fake",
                "modelProvider": "fake",
                "cwd": request["params"]["cwd"],
                "approvalPolicy": "never",
                "approvalsReviewer": "user",
                "sandbox": {"type": "dangerFullAccess"},
                "instructionSources": ["C:/Projects/HMASD/AGENTS.md"],
            }
        elif method == "thread/name/set":
            if created_thread is not None:
                created_thread["name"] = request["params"]["name"]
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
            created_fact = (
                created_thread
                if created_thread is not None
                and created_thread.get("id") == request["params"]["threadId"]
                else {}
            )
            result = {
                "thread": {
                    "id": request["params"]["threadId"],
                    **created_fact,
                    **({"status": read_thread_status} if read_thread_status is not None else {}),
                    **({"name": read_thread_name} if read_thread_name is not None else {}),
                    **({"cwd": read_thread_cwd} if read_thread_cwd is not None else {}),
                    **(
                        {"threadSource": read_thread_source}
                        if read_thread_source is not None
                        else {}
                    ),
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


def test_execute_plan_never_recreates_an_unnamed_thread_after_name_unknown(
    tmp_path: Path,
) -> None:
    native_threads: list[dict[str, Any]] = []

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        request_id = request.get("id")
        if request_id is None:
            return
        method = request.get("method")
        if method == "initialize":
            result: dict[str, Any] = {
                "serverInfo": {"name": "fake", "version": "1"}
            }
        elif method == "thread/list":
            result = {"data": native_threads, "nextCursor": None}
        elif method == "thread/start":
            thread = {
                "id": f"thread-{len(native_threads) + 1}",
                "name": None,
                "cwd": request["params"]["cwd"],
                "threadSource": request["params"]["threadSource"],
                "status": {"type": "idle"},
                "turns": [],
            }
            native_threads.append(thread)
            result = {
                "thread": thread,
                "model": "fake",
                "modelProvider": "fake",
                "cwd": request["params"]["cwd"],
                "approvalPolicy": "never",
                "sandbox": {"type": "dangerFullAccess"},
                "instructionSources": [],
            }
        elif method == "thread/name/set":
            return
        elif method == "thread/read":
            thread_id = request["params"]["threadId"]
            thread = next(item for item in native_threads if item["id"] == thread_id)
            result = {"thread": thread}
        else:
            raise AssertionError(f"unexpected method: {method}")
        peer.emit({"id": request_id, "result": result})

    peer = FakeTransport(respond)
    plan = {
        "verb": "CREATE_TASK_INTENT",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {
            "status": "CREATE_TASK",
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
        },
    }
    with tasks.AppServerClient(transport=peer, timeout=0.01) as client:
        first = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )
        second = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )

    assert first["status"] == "UNKNOWN"
    assert first["reason"] == "THREAD_CREATED_NAME_UNKNOWN"
    assert first["thread_id"] == "thread-1"
    assert first["target_identity"] == "EM-alpha"
    assert first["observed_name"] is None
    assert second == {
        "status": "UNKNOWN",
        "reason": "THREAD_CREATED_NAME_UNKNOWN",
        "target_identity": "EM-alpha",
        "thread_id": "thread-1",
        "observed_name": None,
        "observed_status": {"type": "idle"},
    }
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/start") == 1
    assert methods.count("thread/name/set") == 1
    assert methods.count("thread/read") == 2
    start = next(
        request for request in peer.requests if request.get("method") == "thread/start"
    )
    assert start["params"]["threadSource"] == "hmasd-manager:EM-alpha:g1"


@pytest.mark.parametrize(
    "unrelated_thread",
    [
        {
            "id": "thread-ephemeral",
            "name": None,
            "status": {"type": "idle"},
            "ephemeral": True,
            "source": "appServer",
        },
        {
            "id": "thread-leaf",
            "name": None,
            "status": {"type": "idle"},
            "ephemeral": False,
            "source": "subAgent",
            "agentRole": "hmasd-code-scout",
        },
    ],
    ids=["ephemeral", "non-manager-leaf"],
)
def test_unrelated_unnamed_thread_does_not_block_manager_creation(
    tmp_path: Path, unrelated_thread: dict[str, Any]
) -> None:
    peer = response_peer(
        listed_threads=[{**unrelated_thread, "cwd": tmp_path.as_posix()}]
    )
    plan = create_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )

    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-new"
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/start") == 1
    assert methods.count("turn/start") == 1


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
                "text": PARTICIPANT_SLICE_INSTRUCTION,
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
    state_path = tmp_path / "docs/research/candidates/alpha/STATE.json"
    direction_path = tmp_path / "docs/research/candidates/alpha/DIRECTION.json"
    for path, document in (
        (state_path, {"direction": "alpha", "revision": 7}),
        (direction_path, {"direction": "alpha", "revision": 3}),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-alpha",
            "authority_refs": [
                {
                    "path": "docs/research/candidates/alpha/DIRECTION.json",
                    "revision": 3,
                }
            ],
            "objective": "complete one bounded participant slice",
            "non_goals": ["do not coordinate global topology"],
            "owned_paths": ["experiments/candidates/alpha"],
            "done_criteria": ["publish one immutable typed return"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(packet, repo=tmp_path)
    work_id = packet["work_id"]
    peer = response_peer(
        complete_turn=True,
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
        read_thread_status={"type": "idle"},
    )
    plan = create_em_plan(work_id=work_id)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=f".codex/runtime/work/ready/{work_id}/packet.json",
            cwd=str(tmp_path),
            observed_tasks=[],
            wait_timeout=0.1,
        )

    assert result == {
        "status": "RETURN_WITNESS_MISSING",
        "reason": "NATIVE_TURN_TERMINAL_WITHOUT_RETURN_WITNESS",
        "recoverable": True,
        "work_id": work_id,
        "thread_id": "thread-new",
        "turn_id": "turn-new",
        "turn_status": "completed",
    }
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/resume") == 1


def test_execute_plan_reports_one_typed_return_and_redelivery_is_idempotent(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "docs/research/candidates/alpha/STATE.json"
    direction_path = tmp_path / "docs/research/candidates/alpha/DIRECTION.json"
    for path, document in (
        (state_path, {"direction": "alpha", "revision": 7}),
        (direction_path, {"direction": "alpha", "revision": 3}),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-alpha",
            "authority_refs": [
                {
                    "path": "docs/research/candidates/alpha/DIRECTION.json",
                    "revision": 3,
                }
            ],
            "objective": "complete one bounded participant slice",
            "non_goals": ["do not coordinate global topology"],
            "owned_paths": ["experiments/candidates/alpha"],
            "done_criteria": ["publish one immutable typed return"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(packet, repo=tmp_path)
    work_id = packet["work_id"]
    locator = f".codex/runtime/work/ready/{work_id}/packet.json"
    participant_task = {
        "logical_identity": "EM-alpha",
        "kind": "em",
        "direction_id": "alpha",
        "generation": 1,
        "lifecycle": "PARKED",
        "thread_id": "thread-em-alpha",
    }
    agent_result = {
        "schema_version": 1,
        "role": "hmasd-em",
        "logical_identity": "EM-alpha",
        "generation": 1,
        "assignment_id": work_id,
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "Completed the one exact bounded participant slice.",
        "changed_paths": [],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {
            "kind": "em",
            "direction_id": "alpha",
            "question_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [],
            "engineering_request_ref": None,
        },
    }
    witness_publish_count = 0

    def publish_return(
        request: dict[str, Any], _: dict[str, Any]
    ) -> dict[str, Any]:
        nonlocal witness_publish_count
        witness_publish_count += 1
        tasks.hmasd_work_packet.publish_return(
            repo=tmp_path,
            work_id=work_id,
            observed_tasks=[participant_task],
            agent_result=agent_result,
        )
        return {
            "id": "turn-em-alpha",
            "status": "completed",
            "items": [
                {
                    "type": "userMessage",
                    "content": request["params"]["input"],
                }
            ],
        }

    scenario = StatefulParticipantPeer(
        tmp_path,
        turn_hook=publish_return,
        instruction_sources=[str(tmp_path / "AGENTS.md")],
    )
    plan = tasks.hmasd_work_packet.reconcile_once(
        repo=tmp_path, work_id=work_id, observed_tasks=[]
    )["plan"]
    with tasks.AppServerClient(transport=scenario.transport, timeout=0.1) as client:
        first = client.execute_plan(
            plan,
            packet_locator=locator,
            cwd=str(tmp_path),
            observed_tasks=[],
            wait_timeout=0.1,
        )
        redelivered = client.execute_plan(
            plan,
            packet_locator=locator,
            cwd=str(tmp_path),
            observed_tasks=[participant_task],
            wait_timeout=0.1,
        )

    for result in (first, redelivered):
        assert result["status"] == "COMPLETED"
        assert result["work_id"] == work_id
        assert result["return_witness"]["agent_result"] == agent_result
    methods = [request.get("method") for request in scenario.requests]
    assert methods.count("thread/start") == 1
    assert methods.count("thread/name/set") == 1
    assert methods.count("turn/start") == 1
    assert witness_publish_count == 1
    return_path = (
        tmp_path
        / ".codex/runtime/work/returns"
        / work_id
        / "return.json"
    )
    assert list(return_path.parent.iterdir()) == [return_path]
    named_targets = [
        request["params"]["name"]
        for request in scenario.requests
        if request.get("method") == "thread/name/set"
    ]
    assert named_targets == ["EM-alpha"]
    assert "Root" not in json.dumps(scenario.requests)


def test_run_chain_routes_one_immutable_em_engineering_request_to_cm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    direction_root = tmp_path / "docs/research/candidates/alpha"
    state_path = direction_root / "STATE.json"
    direction_path = direction_root / "DIRECTION.json"
    engineering_request_path = direction_root / "em/ENGINEERING_REQUEST.json"
    beta_state_path = tmp_path / "docs/research/candidates/beta/STATE.json"
    for path, document in (
        (state_path, {"direction": "alpha", "revision": 7}),
        (direction_path, {"direction": "alpha", "revision": 3}),
        (beta_state_path, {"direction": "beta", "revision": 1}),
        (
            engineering_request_path,
            {
                "decision_owner": "EM-alpha",
                "objective": "implement only the frozen alpha engineering slice",
            },
        ),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    request_ref = {
        "path": "docs/research/candidates/alpha/em/ENGINEERING_REQUEST.json",
        "sha256": hashlib.sha256(engineering_request_path.read_bytes()).hexdigest(),
    }
    em_packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-alpha",
            "authority_refs": [
                {
                    "path": "docs/research/candidates/alpha/DIRECTION.json",
                    "revision": 3,
                }
            ],
            "objective": "decide whether alpha needs one bounded engineering slice",
            "non_goals": ["do not coordinate participant transport"],
            "owned_paths": ["docs/research/candidates/alpha/em"],
            "done_criteria": ["bind one exact CM draft or finish without one"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(em_packet, repo=tmp_path)
    cm_draft = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "EM-alpha",
            "target_identity": "CM-alpha",
            "authority_refs": [request_ref],
            "objective": "implement only the frozen alpha engineering slice",
            "non_goals": [
                "do not reinterpret the scientific decision",
                "do not coordinate another participant",
            ],
            "owned_paths": ["experiments/candidates/alpha/t02"],
            "done_criteria": ["publish one immutable typed CM return"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    beta_packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/beta/STATE.json",
                "revision": 1,
            },
            "sender_identity": "EM-beta",
            "target_identity": "CM-beta",
            "authority_refs": [],
            "objective": "complete one exact beta engineering slice",
            "non_goals": ["do not affect the independent alpha chain"],
            "owned_paths": ["experiments/candidates/beta/t02"],
            "done_criteria": ["return one typed CM result"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(beta_packet, repo=tmp_path)
    projection_path = tmp_path / ".codex/runtime/tasks.json"
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "logical_identity": "CM-beta",
                        "kind": "cm",
                        "direction_id": "beta",
                        "generation": 1,
                        "lifecycle": "PARKED",
                        "thread_id": "thread-cm-beta",
                    }
                ]
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    em_task = {
        "logical_identity": "EM-alpha",
        "kind": "em",
        "direction_id": "alpha",
        "generation": 1,
        "lifecycle": "PARKED",
        "thread_id": "thread-em-alpha",
    }
    em_result = {
        "schema_version": 1,
        "role": "hmasd-em",
        "logical_identity": "EM-alpha",
        "generation": 1,
        "assignment_id": em_packet["work_id"],
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "The frozen scientific result requests one bounded CM slice.",
        "changed_paths": [request_ref["path"]],
        "state_refs": [],
        "artifact_refs": [request_ref],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {
            "kind": "REQUEST_CM_ENGINEERING",
            "input_refs": [cm_draft["work_id"]],
        },
        "payload": {
            "kind": "em",
            "direction_id": "alpha",
            "question_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [],
            "engineering_request_ref": request_ref,
        },
    }
    tasks.hmasd_work_packet.publish_return(
        repo=tmp_path,
        work_id=em_packet["work_id"],
        observed_tasks=[em_task],
        agent_result=em_result,
        next_packet_draft=cm_draft,
    )

    cm_task = {
        "logical_identity": "CM-alpha",
        "kind": "cm",
        "direction_id": "alpha",
        "generation": 1,
        "lifecycle": "PARKED",
        "thread_id": "thread-cm-alpha",
    }
    cm_result = {
        "schema_version": 1,
        "role": "hmasd-cm",
        "logical_identity": "CM-alpha",
        "generation": 1,
        "assignment_id": cm_draft["work_id"],
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "Completed only the exact bounded engineering slice.",
        "changed_paths": [],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {
            "kind": "cm",
            "direction_id": "alpha",
            "scope_ref": request_ref,
            "base_sha": "c" * 40,
            "candidate_sha": None,
            "verification_refs": [],
            "integrated_sha": None,
        },
    }
    cm_return_count = 0
    em_locator = f".codex/runtime/work/ready/{em_packet['work_id']}/packet.json"
    cm_locator = f".codex/runtime/work/ready/{cm_draft['work_id']}/packet.json"

    class ChainPeer:
        def __init__(self) -> None:
            beta_source = "hmasd-manager:CM-beta:g2"
            self.threads: dict[str, dict[str, Any]] = {
                "thread-em-alpha": {
                    "id": "thread-em-alpha",
                    "name": "EM-alpha",
                    "cwd": str(tmp_path),
                    "threadSource": "hmasd-manager:EM-alpha:g1",
                    "status": {"type": "idle"},
                    "turns": [
                        {
                            "id": "turn-em-alpha",
                            "status": "completed",
                            "items": [
                                {
                                    "type": "userMessage",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": tasks.dispatch_envelope_bytes(
                                                em_packet["work_id"],
                                                em_locator,
                                                "EM-alpha",
                                            ).decode(),
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
                "thread-cm-beta": {
                    "id": "thread-cm-beta",
                    "name": "CM-beta",
                    "cwd": str(tmp_path),
                    "threadSource": beta_source,
                    "status": {"type": "idle"},
                    "turns": [],
                },
            }
            self.transport = FakeTransport(self.respond)

        @property
        def requests(self) -> list[dict[str, Any]]:
            return self.transport.requests

        def respond(self, request: dict[str, Any], peer: FakeTransport) -> None:
            nonlocal cm_return_count
            request_id = request.get("id")
            if request_id is None:
                return
            method = request.get("method")
            if method == "initialize":
                result: dict[str, Any] = {
                    "serverInfo": {"name": "fake", "version": "1"}
                }
            elif method == "thread/list":
                result = {"data": list(self.threads.values()), "nextCursor": None}
            elif method == "thread/read":
                result = {"thread": self.threads[request["params"]["threadId"]]}
            elif method == "thread/start":
                assert request["params"]["threadSource"] == "hmasd-manager:CM-alpha:g1"
                thread = {
                    "id": "thread-cm-alpha",
                    "name": None,
                    "cwd": request["params"]["cwd"],
                    "threadSource": request["params"]["threadSource"],
                    "status": {"type": "idle"},
                    "turns": [],
                }
                self.threads[thread["id"]] = thread
                result = {
                    "thread": thread,
                    "model": "fake",
                    "modelProvider": "fake",
                    "cwd": request["params"]["cwd"],
                    "approvalPolicy": "never",
                    "sandbox": {"type": "dangerFullAccess"},
                    "instructionSources": [],
                }
            elif method == "thread/name/set":
                self.threads[request["params"]["threadId"]]["name"] = request[
                    "params"
                ]["name"]
                result = {}
            elif method == "thread/resume":
                thread = self.threads[request["params"]["threadId"]]
                result = {
                    "thread": thread,
                    "model": "fake",
                    "modelProvider": "fake",
                    "cwd": thread["cwd"],
                    "approvalPolicy": "never",
                    "sandbox": {"type": "dangerFullAccess"},
                }
            elif method == "turn/start":
                assert request["params"]["threadId"] == "thread-cm-alpha"
                cm_return_count += 1
                tasks.hmasd_work_packet.publish_return(
                    repo=tmp_path,
                    work_id=cm_draft["work_id"],
                    observed_tasks=[cm_task],
                    agent_result=cm_result,
                )
                turn = {
                    "id": "turn-cm-alpha",
                    "status": "completed",
                    "items": [
                        {
                            "type": "userMessage",
                            "content": request["params"]["input"],
                        }
                    ],
                }
                self.threads["thread-cm-alpha"]["turns"] = [turn]
                peer.emit(
                    {
                        "id": request_id,
                        "result": {
                            "turn": {
                                "id": turn["id"],
                                "status": "inProgress",
                                "items": [],
                            }
                        },
                    }
                )
                peer.emit(
                    {
                        "method": "turn/completed",
                        "params": {"threadId": "thread-cm-alpha", "turn": turn},
                    }
                )
                return
            else:
                raise AssertionError(f"unexpected method: {method}")
            peer.emit({"id": request_id, "result": result})

    scenario = ChainPeer()
    monkeypatch.setattr(tasks, "JsonlProcessTransport", lambda _: scenario.transport)
    command = [
        "--server-command",
        "fake",
        "run-chain",
        "--work-id",
        em_packet["work_id"],
        "--cwd",
        str(tmp_path),
        "--max-transitions",
        "4",
    ]
    assert tasks.main(command) == 0
    first = json.loads(capsys.readouterr().out)
    assert tasks.main(command) == 0
    repeated = json.loads(capsys.readouterr().out)
    beta_command = [
        "--server-command",
        "fake",
        "run-chain",
        "--work-id",
        beta_packet["work_id"],
        "--cwd",
        str(tmp_path),
    ]
    assert tasks.main(beta_command) == 0
    beta = json.loads(capsys.readouterr().out)

    assert first["status"] == "STOPPED"
    assert first["stop"] == {
        "reason": "TERMINAL_NO_NEXT",
        "work_id": cm_draft["work_id"],
        "return_witness": tasks.hmasd_work_packet.read_return(
            repo=tmp_path, work_id=cm_draft["work_id"]
        ),
    }
    assert [event["kind"] for event in first["events"]] == [
        "PLAN",
        "PACKET_PUBLISH",
        "PLAN",
        "EXECUTE_PLAN",
        "PLAN",
    ]
    assert first["events"][0]["plan"]["packet"] == cm_draft
    assert first["events"][1] == {
        "kind": "PACKET_PUBLISH",
        "work_id": em_packet["work_id"],
        "next_work_id": cm_draft["work_id"],
        "published": True,
    }
    assert first["events"][2]["plan"]["target_identity"] == "CM-alpha"
    assert first["events"][3]["result"]["return_witness"]["agent_result"] == cm_result
    assert repeated["status"] == "STOPPED"
    assert repeated["stop"]["reason"] == "TERMINAL_NO_NEXT"
    assert repeated["stop"]["work_id"] == cm_draft["work_id"]
    assert [event["kind"] for event in repeated["events"]] == [
        "PLAN",
        "PACKET_PUBLISH",
        "PLAN",
    ]
    assert repeated["events"][1]["published"] is False
    assert beta["events"] == []
    assert beta["stop"] == {
        "reason": "TYPED_CONFLICT",
        "work_id": beta_packet["work_id"],
        "conflict": {
            "status": "TASK_IDENTITY_CONFLICT",
            "reason": "PROJECTED_NATIVE_GENERATION_CONFLICT",
            "conflicts": [
                {
                    "logical_identity": "CM-beta",
                    "thread_id": "thread-cm-beta",
                    "projected_generation": 1,
                    "native_generation": 2,
                    "thread_source": "hmasd-manager:CM-beta:g2",
                }
            ],
        },
    }
    ready_cm_path = (
        tmp_path
        / ".codex/runtime/work/ready"
        / cm_draft["work_id"]
        / "packet.json"
    )
    assert json.loads(ready_cm_path.read_text(encoding="utf-8")) == cm_draft
    methods = [request.get("method") for request in scenario.requests]
    assert methods.count("thread/start") == 1
    assert methods.count("thread/name/set") == 1
    assert methods.count("turn/start") == 1
    assert cm_return_count == 1
    cm_turn = next(
        request for request in scenario.requests if request.get("method") == "turn/start"
    )
    assert cm_turn["params"]["input"] == [
        {
            "type": "text",
            "text": tasks.dispatch_envelope_bytes(
                cm_draft["work_id"], cm_locator, "CM-alpha"
            ).decode(),
        },
        {"type": "text", "text": PARTICIPANT_SLICE_INSTRUCTION},
    ]
    assert "Root" not in json.dumps(scenario.requests)


def test_run_chain_rejects_projected_native_generation_conflict_before_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_path = tmp_path / "docs/research/candidates/alpha/STATE.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"direction": "alpha", "revision": 7}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "EM-alpha",
            "target_identity": "CM-alpha",
            "authority_refs": [],
            "objective": "complete one exact alpha engineering slice",
            "non_goals": ["do not use a stale projected generation"],
            "owned_paths": ["experiments/candidates/alpha/t02-conflict"],
            "done_criteria": ["return one typed CM result"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(packet, repo=tmp_path)
    projection_path = tmp_path / ".codex/runtime/tasks.json"
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "logical_identity": "CM-alpha",
                        "kind": "cm",
                        "direction_id": "alpha",
                        "generation": 1,
                        "lifecycle": "PARKED",
                        "thread_id": "thread-cm-alpha",
                    }
                ]
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    native_source = "hmasd-manager:CM-alpha:g2"
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-cm-alpha",
                "name": "CM-alpha",
                "cwd": str(tmp_path),
                "threadSource": native_source,
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="CM-alpha",
        read_thread_cwd=str(tmp_path),
        read_thread_source=native_source,
        read_thread_status={"type": "idle"},
    )
    monkeypatch.setattr(tasks, "JsonlProcessTransport", lambda _: peer)

    assert tasks.main(
        [
            "--server-command",
            "fake",
            "run-chain",
            "--work-id",
            packet["work_id"],
            "--cwd",
            str(tmp_path),
        ]
    ) == 0
    result = json.loads(capsys.readouterr().out)

    assert result == {
        "status": "STOPPED",
        "start_work_id": packet["work_id"],
        "transition_count": 0,
        "events": [],
        "stop": {
            "reason": "TYPED_CONFLICT",
            "work_id": packet["work_id"],
            "conflict": {
                "status": "TASK_IDENTITY_CONFLICT",
                "reason": "PROJECTED_NATIVE_GENERATION_CONFLICT",
                "conflicts": [
                    {
                        "logical_identity": "CM-alpha",
                        "thread_id": "thread-cm-alpha",
                        "projected_generation": 1,
                        "native_generation": 2,
                        "thread_source": native_source,
                    }
                ],
            },
        },
    }
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/list") == 1
    assert methods.count("thread/read") == 1
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods
    assert "turn/start" not in methods


def test_run_chain_recovery_budget_is_shared_across_process_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_path = tmp_path / "docs/research/candidates/alpha/STATE.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"direction": "alpha", "revision": 7}) + "\n",
        encoding="utf-8",
    )
    packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-alpha",
            "authority_refs": [],
            "objective": "complete one exact alpha research slice",
            "non_goals": ["do not create a replacement packet or task"],
            "owned_paths": ["docs/research/candidates/alpha/em"],
            "done_criteria": ["publish one immutable typed return"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(packet, repo=tmp_path)
    work_id = packet["work_id"]
    locator = f".codex/runtime/work/ready/{work_id}/packet.json"
    thread: dict[str, Any] | None = None
    all_requests: list[dict[str, Any]] = []
    attempt_outcomes = (
        ("interrupted", "TERMINAL_WITHOUT_RETURN"),
        ("completed", "RESUME_SAME_SLICE"),
        ("failed", "SAME_SCOPE_REPAIR"),
    )

    def transport_factory(_command: Any) -> FakeTransport:
        fail_next_list = False

        def respond(request: dict[str, Any], peer: FakeTransport) -> None:
            nonlocal fail_next_list, thread
            all_requests.append(request)
            request_id = request.get("id")
            if request_id is None:
                return
            method = request.get("method")
            if method == "initialize":
                result: dict[str, Any] = {
                    "serverInfo": {"name": "fake", "version": "1"}
                }
            elif method == "thread/list":
                if fail_next_list:
                    peer.emit({"id": request_id, "error": {"code": -32001}})
                    fail_next_list = False
                    return
                result = {
                    "data": [] if thread is None else [thread],
                    "nextCursor": None,
                }
            elif method == "thread/start":
                thread = {
                    "id": "thread-em-alpha",
                    "name": None,
                    "cwd": request["params"]["cwd"],
                    "threadSource": request["params"]["threadSource"],
                    "status": {"type": "idle"},
                    "turns": [],
                }
                result = {
                    "thread": thread,
                    "model": "fake",
                    "modelProvider": "fake",
                    "cwd": request["params"]["cwd"],
                    "approvalPolicy": "never",
                    "sandbox": {"type": "dangerFullAccess"},
                    "instructionSources": [],
                }
            elif method == "thread/name/set":
                assert thread is not None
                thread["name"] = request["params"]["name"]
                result = {}
            elif method == "thread/read":
                assert thread is not None
                result = {"thread": thread}
            elif method == "thread/resume":
                assert thread is not None
                result = {
                    "thread": thread,
                    "model": "fake",
                    "modelProvider": "fake",
                    "cwd": str(tmp_path),
                    "approvalPolicy": "never",
                    "sandbox": {"type": "dangerFullAccess"},
                }
            elif method == "turn/start":
                assert thread is not None
                status, recovery_kind = attempt_outcomes[len(thread["turns"])]
                turn = {
                    "id": f"turn-{len(thread['turns']) + 1}",
                    "status": status,
                    "items": [
                        {
                            "type": "userMessage",
                            "content": request["params"]["input"],
                        },
                        {
                            "type": "agentMessage",
                            "content": [
                                {"type": "text", "text": recovery_kind}
                            ],
                        },
                    ],
                }
                if recovery_kind == "SAME_SCOPE_REPAIR":
                    turn["error"] = {
                        "message": "must not be interpreted as capacity",
                        "codexErrorInfo": "internalServerError",
                    }
                thread["turns"].append(turn)
                fail_next_list = True
                peer.emit(
                    {
                        "id": request_id,
                        "result": {
                            "turn": {
                                "id": turn["id"],
                                "status": "inProgress",
                                "items": [],
                            }
                        },
                    }
                )
                peer.emit(
                    {
                        "method": "turn/completed",
                        "params": {"threadId": thread["id"], "turn": turn},
                    }
                )
                return
            else:
                raise AssertionError(f"unexpected method: {method}")
            peer.emit({"id": request_id, "result": result})

        return FakeTransport(respond)

    monkeypatch.setattr(tasks, "JsonlProcessTransport", transport_factory)
    command = [
        "--server-command",
        "fake",
        "run-chain",
        "--work-id",
        work_id,
        "--cwd",
        str(tmp_path),
    ]
    for _ in range(3):
        assert tasks.main(command) == 0
        interrupted = json.loads(capsys.readouterr().out)
        assert interrupted["stop"]["reason"] == "EXECUTE_PLAN_STOP"
        assert interrupted["stop"]["result"]["status"] == "ERROR"

    assert tasks.main(command) == 0
    exhausted = json.loads(capsys.readouterr().out)
    assert exhausted["stop"] == {
        "reason": "RECOVERY_EXHAUSTED",
        "work_id": work_id,
        "failure_scope": "direction",
        "failure_ref": "alpha",
        "evidence": {
            "target_identity": "EM-alpha",
            "thread_id": "thread-em-alpha",
            "packet_locator": locator,
            "max_attempts": 3,
            "attempt_statuses": [
                {"attempt": 1, "turn_id": "turn-1", "turn_status": "interrupted"},
                {"attempt": 2, "turn_id": "turn-2", "turn_status": "completed"},
                {"attempt": 3, "turn_id": "turn-3", "turn_status": "failed"},
            ],
        },
    }
    assert tasks.main(command) == 0
    assert json.loads(capsys.readouterr().out)["stop"] == exhausted["stop"]
    methods = [request.get("method") for request in all_requests]
    assert methods.count("thread/start") == 1
    assert methods.count("turn/start") == 3


@pytest.mark.parametrize(
    "codex_error_info",
    ["usageLimitExceeded", "sessionBudgetExceeded", "serverOverloaded"],
)
def test_run_chain_capacity_pause_is_scoped_and_resumes_same_identity(
    tmp_path: Path,
    codex_error_info: str,
) -> None:
    state_path = tmp_path / "docs/research/candidates/alpha/STATE.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"direction": "alpha", "revision": 7}) + "\n",
        encoding="utf-8",
    )
    packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-alpha",
            "authority_refs": [],
            "objective": "complete one exact alpha research slice",
            "non_goals": ["do not pause another direction"],
            "owned_paths": ["docs/research/candidates/alpha/em"],
            "done_criteria": ["publish one immutable typed return"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(packet, repo=tmp_path)

    beta_state = tmp_path / "docs/research/candidates/beta/STATE.json"
    beta_state.parent.mkdir(parents=True, exist_ok=True)
    beta_state.write_text(
        json.dumps({"direction": "beta", "revision": 1}) + "\n",
        encoding="utf-8",
    )
    beta_packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/beta/STATE.json",
                "revision": 1,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-beta",
            "authority_refs": [],
            "objective": "complete one independent beta research slice",
            "non_goals": ["do not depend on alpha capacity"],
            "owned_paths": ["docs/research/candidates/beta/em"],
            "done_criteria": ["publish one immutable typed return"],
            "effect_refs": [],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(beta_packet, repo=tmp_path)
    beta_task = {
        "logical_identity": "EM-beta",
        "kind": "em",
        "direction_id": "beta",
        "generation": 1,
        "lifecycle": "PARKED",
        "thread_id": "thread-em-beta",
    }
    tasks.hmasd_work_packet.publish_return(
        repo=tmp_path,
        work_id=beta_packet["work_id"],
        observed_tasks=[beta_task],
        agent_result={
            "schema_version": 1,
            "role": "hmasd-em",
            "logical_identity": "EM-beta",
            "generation": 1,
            "assignment_id": beta_packet["work_id"],
            "status": "COMPLETED",
            "materiality": "DIRECTION",
            "summary": "Completed the independent beta slice.",
            "changed_paths": [],
            "state_refs": [],
            "artifact_refs": [],
            "checkpoint_sha": None,
            "decision_requests": [],
            "next_action": {"kind": "NONE", "input_refs": []},
            "payload": {
                "kind": "em",
                "direction_id": "beta",
                "question_sha256": "a" * 64,
                "evidence_set_sha256": "b" * 64,
                "conclusion_refs": [],
                "engineering_request_ref": None,
            },
        },
    )
    beta_locator = f".codex/runtime/work/ready/{beta_packet['work_id']}/packet.json"
    beta_peer = response_peer(
        history_text=tasks.dispatch_envelope_bytes(
            beta_packet["work_id"], beta_locator, "EM-beta"
        ).decode(),
        read_turn_status="completed",
        read_thread_name="EM-beta",
        read_thread_cwd=str(tmp_path),
        read_thread_source="hmasd-manager:EM-beta:g1",
        listed_threads=[
            {
                "id": "thread-em-beta",
                "name": "EM-beta",
                "cwd": str(tmp_path),
                "threadSource": "hmasd-manager:EM-beta:g1",
                "status": {"type": "idle"},
            }
        ],
    )

    def terminal_turn(
        request: dict[str, Any], thread: dict[str, Any]
    ) -> dict[str, Any]:
        attempt = len(thread["turns"]) + 1
        items = [
            {
                "type": "userMessage",
                "content": request["params"]["input"],
            }
        ]
        if attempt == 1:
            return {
                "id": "turn-capacity",
                "status": "failed",
                "items": items,
                "error": {
                    "message": "must not enter evidence",
                    "additionalDetails": "must not enter evidence",
                    "codexErrorInfo": codex_error_info,
                },
            }
        return {
            "id": f"turn-recovery-{attempt}",
            "status": "interrupted",
            "items": items,
        }

    scenario = StatefulParticipantPeer(
        tmp_path,
        turn_hook=terminal_turn,
        preserve_history=True,
    )
    with tasks.AppServerClient(transport=scenario.transport, timeout=0.1) as client:
        paused = client.run_chain(
            start_work_id=packet["work_id"], cwd=str(tmp_path)
        )
        with tasks.AppServerClient(transport=beta_peer, timeout=0.1) as beta_client:
            beta = beta_client.run_chain(
                start_work_id=beta_packet["work_id"], cwd=str(tmp_path)
            )
        exhausted = client.run_chain(
            start_work_id=packet["work_id"], cwd=str(tmp_path)
        )

    assert paused["stop"] == {
        "reason": "CAPACITY_PAUSE",
        "work_id": packet["work_id"],
        "failure_scope": "direction",
        "failure_ref": (
            f"native_turn:thread-em-alpha:turn-capacity:{codex_error_info}"
        ),
        "evidence": {
            "thread_id": "thread-em-alpha",
            "turn_id": "turn-capacity",
            "turn_status": "failed",
            "codex_error_info": codex_error_info,
        },
    }
    assert exhausted["stop"]["reason"] == "RECOVERY_EXHAUSTED"
    assert exhausted["stop"]["failure_ref"] == "alpha"
    assert beta["stop"]["reason"] == "TERMINAL_NO_NEXT"
    assert beta["stop"]["work_id"] == beta_packet["work_id"]
    methods = [request.get("method") for request in scenario.requests]
    assert methods.count("thread/start") == 1
    assert methods.count("turn/start") == 3


def test_execute_plan_refreshes_native_identity_and_lifecycle_after_wait(
    tmp_path: Path,
) -> None:
    def rename_after_dispatch(
        _: dict[str, Any], thread: dict[str, Any]
    ) -> dict[str, Any]:
        thread["name"] = "EM-renamed"
        thread["status"] = {"type": "idle"}
        return {
            "id": "turn-em-alpha",
            "status": "completed",
            "items": [],
        }

    scenario = StatefulParticipantPeer(
        tmp_path,
        turn_hook=rename_after_dispatch,
        start_status="active",
    )
    plan = create_em_plan()
    with tasks.AppServerClient(transport=scenario.transport, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
            wait_timeout=0.1,
        )

    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "thread_id": "thread-em-alpha",
        "observed_name": "EM-renamed",
        "observed_status": {"type": "idle"},
    }
    assert sum(
        request.get("method") == "thread/list" for request in scenario.requests
    ) == 2


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
    plan = create_em_plan(target_identity="EM-beta", direction_id="beta")
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
    plan = create_em_plan(target_identity="EM-beta", direction_id="beta")
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
    plan = create_em_plan(requested_target_identity="EM-alpha")
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


def test_execute_plan_first_turn_exposes_only_exact_slice_and_return_contract() -> None:
    peer = response_peer()
    plan = create_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd="C:/Projects/HMASD",
            observed_tasks=[],
        )

    assert result["status"] == "DELIVERED"
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"]["input"] == [
        {
            "type": "text",
            "text": tasks.dispatch_envelope_bytes(
                WORK_ID, LOCATOR, "EM-alpha"
            ).decode(),
        },
        {
            "type": "text",
            "text": PARTICIPANT_SLICE_INSTRUCTION,
        },
    ]
    rendered = json.dumps(turn["params"]["input"])
    assert "$hmasd-" not in rendered
    assert '"type": "skill"' not in rendered


def test_execute_plan_new_first_dispatch_does_not_probe_return_witness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    peer = response_peer()
    plan = create_em_plan()

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
    plan = create_em_plan()
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
    monkeypatch.setattr(
        tasks.hmasd_work_packet,
        "read_return",
        lambda **_: VALIDATED_RETURN_STUB,
    )
    plan = reuse_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks={"tasks": observed_em()},
        )
    assert result == {
        "status": "COMPLETED",
        "reason": "RETURN_WITNESS_PRESENT",
        "work_id": WORK_ID,
        "thread_id": "thread-1",
        "return_witness": VALIDATED_RETURN_STUB,
    }
    assert observed == [
        (
            tmp_path.absolute(),
            WORK_ID,
            [
                {
                    "logical_identity": "EM-alpha",
                    "thread_id": "thread-1",
                    "generation": 1,
                    "lifecycle": "PARKED",
                    "kind": "em",
                    "direction_id": "alpha",
                }
            ],
        )
    ]
    methods = [request.get("method") for request in peer.requests]
    assert "thread/resume" not in methods
    assert "turn/start" not in methods


def test_run_chain_repeated_unknown_effect_observation_never_resends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / "docs/research/candidates/alpha/STATE.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"direction": "alpha", "revision": 7}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    effect_path = "temp/directions/alpha/exp/run-unknown/manifest.json"
    effect_state = "IN_PROGRESS"

    def observe_effect(_: Path, reference: dict[str, Any]) -> Any:
        return tasks.hmasd_work_packet.hmasd_protocol_contracts.EffectObservation(
            reference["kind"],
            reference["resource_id"],
            effect_state,
            reference["path"],
        )

    monkeypatch.setattr(
        tasks.hmasd_work_packet.hmasd_protocol_contracts,
        "observe_effect_ref",
        observe_effect,
    )
    packet = tasks.hmasd_work_packet.build_packet(
        {
            "schema_version": 1,
            "scope_ref": {
                "path": "docs/research/candidates/alpha/STATE.json",
                "revision": 7,
            },
            "sender_identity": "Workflow-Clerk",
            "target_identity": "EM-alpha",
            "authority_refs": [],
            "objective": "observe one exact uncertain effect",
            "non_goals": ["do not replay the effect"],
            "owned_paths": ["experiments/candidates/alpha"],
            "done_criteria": ["return one typed envelope"],
            "effect_refs": [
                {
                    "kind": "run_manifest",
                    "path": effect_path,
                    "resource_id": "alpha/run-unknown",
                }
            ],
        },
        repo=tmp_path,
    )
    tasks.hmasd_work_packet.publish_packet(packet, repo=tmp_path)
    work_id = packet["work_id"]
    participant_task = {
        "logical_identity": "EM-alpha",
        "kind": "em",
        "direction_id": "alpha",
        "generation": 1,
        "lifecycle": "PARKED",
        "thread_id": "thread-1",
    }
    agent_result = {
        "schema_version": 1,
        "role": "hmasd-em",
        "logical_identity": "EM-alpha",
        "generation": 1,
        "assignment_id": work_id,
        "status": "COMPLETED",
        "materiality": "DIRECTION",
        "summary": "Returned the bounded local result before effect uncertainty.",
        "changed_paths": [],
        "state_refs": [],
        "artifact_refs": [],
        "checkpoint_sha": None,
        "decision_requests": [],
        "next_action": {"kind": "NONE", "input_refs": []},
        "payload": {
            "kind": "em",
            "direction_id": "alpha",
            "question_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "conclusion_refs": [],
            "engineering_request_ref": None,
        },
    }
    tasks.hmasd_work_packet.publish_return(
        repo=tmp_path,
        work_id=work_id,
        observed_tasks=[participant_task],
        agent_result=agent_result,
    )
    effect_state = "UNKNOWN"
    locator = f".codex/runtime/work/ready/{work_id}/packet.json"
    envelope = tasks.dispatch_envelope_bytes(work_id, locator, "EM-alpha").decode()
    peer = response_peer(
        history_text=envelope,
        read_turn_status="completed",
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
        listed_threads=[
            {
                "id": "thread-1",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
    )
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        first = client.run_chain(
            start_work_id=work_id,
            cwd=str(tmp_path),
        )
        repeated = client.run_chain(
            start_work_id=work_id,
            cwd=str(tmp_path),
        )

    expected_stop = {
        "reason": "UNKNOWN_COMMITMENT",
        "work_id": work_id,
        "unknown_effect_refs": [effect_path],
    }
    assert first["stop"] == expected_stop
    assert repeated["stop"] == expected_stop
    assert first["events"] == repeated["events"]
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
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
    plan = reuse_em_plan()

    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em(),
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
    plan = reuse_em_plan()
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
        monkeypatch.setattr(
            tasks.hmasd_work_packet,
            "read_return",
            lambda **_: VALIDATED_RETURN_STUB,
        )
        monkeypatch.setattr(client, "send", lambda *_, **__: pytest.fail("must not exhaust before return observation"))
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em(),
        )
    assert result == {
        "status": "COMPLETED",
        "reason": "RETURN_WITNESS_PRESENT",
        "work_id": WORK_ID,
        "thread_id": "thread-1",
        "return_witness": VALIDATED_RETURN_STUB,
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
    plan = reuse_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em(),
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


def test_closed_create_plan_does_not_select_fresh_reuse_on_its_behalf(
    tmp_path: Path,
) -> None:
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
        read_thread_cwd=str(tmp_path),
    )
    plan = create_em_plan(requested_target_identity="EM-alpha")
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em("thread-existing"),
        )
    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["reason"] == "PLAN_BOUND_TASK_STATUS_MISMATCH"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods
    assert "turn/start" not in methods


@pytest.mark.parametrize(
    "observed_tasks",
    [
        [],
        [
            {
                "logical_identity": "EM-alpha",
                "kind": "em",
                "direction_id": "alpha",
                "generation": 1,
                "lifecycle": "ACTIVE",
                "thread_id": "thread-existing",
            }
        ],
    ],
    ids=["missing-generation-and-lifecycle", "contradictory-lifecycle"],
)
def test_execute_plan_rejects_missing_or_contradictory_native_task_facts(
    tmp_path: Path, observed_tasks: list[dict[str, Any]]
) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-existing",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
        read_thread_status={"type": "idle"},
    )
    plan = create_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_tasks,
        )

    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["target_identity"] == "EM-alpha"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "turn/start" not in methods


def test_execute_plan_reuses_exact_cached_identity_when_cwd_list_omits_it(
    tmp_path: Path,
) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
    )
    plan = reuse_em_plan(thread_id="thread-cached")
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


@pytest.mark.parametrize(
    "plan",
    [
        {
            "verb": "DISPATCH_EXISTING",
            "work_id": WORK_ID,
            "target_identity": "EM-alpha",
            "task_resolution": {
                "status": "REUSE",
                "thread_id": "thread-existing",
            },
        },
        {
            "verb": "CREATE_TASK_INTENT",
            "work_id": WORK_ID,
            "target_identity": "EM-alpha",
            "task_resolution": {
                "status": "CREATE_TASK",
                "logical_identity": "EM-alpha",
                "kind": "em",
            },
        },
    ],
    ids=["incomplete-reuse", "incomplete-create"],
)
def test_execute_plan_rejects_incomplete_planner_task_resolution(
    tmp_path: Path, plan: dict[str, Any]
) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
    )
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )

    assert result["status"] == "PROTOCOL_DEFECT"
    assert result["reason"] == "INCOMPLETE_TASK_RESOLUTION"
    assert result["work_id"] == WORK_ID
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "turn/start" not in methods


def test_execute_plan_rejects_fresh_generation_that_differs_from_plan(
    tmp_path: Path,
) -> None:
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-existing",
                "name": "EM-alpha",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "idle"},
            }
        ],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
        read_thread_status={"type": "idle"},
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "EM-alpha",
        "task_resolution": {
            "status": "REUSE",
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 2,
            "lifecycle": "PARKED",
            "thread_id": "thread-existing",
        },
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em("thread-existing"),
        )

    assert result == {
        "status": "TASK_IDENTITY_CONFLICT",
        "target_identity": "EM-alpha",
        "reason": "PLAN_BOUND_TASK_MISMATCH",
        "expected": {
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 2,
            "thread_id": "thread-existing",
        },
        "observed": {
            "logical_identity": "EM-alpha",
            "kind": "em",
            "direction_id": "alpha",
            "generation": 1,
            "thread_id": "thread-existing",
        },
    }
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert "turn/start" not in methods


@pytest.mark.parametrize(
    ("mutation", "uses_target_tag"),
    [
        ({"name": "EM-beta"}, False),
        ({"cwd": "C:/Projects/other"}, False),
        ({"threadSource": "hmasd-manager:EM-beta:g1"}, True),
    ],
    ids=["name", "cwd", "thread-source"],
)
def test_execute_plan_revalidates_native_identity_on_final_read(
    tmp_path: Path,
    mutation: dict[str, Any],
    uses_target_tag: bool,
) -> None:
    thread = {
        "id": "thread-existing",
        "name": "EM-alpha",
        "cwd": tmp_path.as_posix(),
        "status": {"type": "idle"},
        "turns": [],
    }
    if uses_target_tag:
        thread["threadSource"] = "hmasd-manager:EM-alpha:g1"
    base = response_peer(listed_threads=[thread])
    read_count = 0

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        nonlocal read_count
        if request.get("method") != "thread/read":
            base.responder(request, peer)
            return
        read_count += 1
        observed = {**thread, **(mutation if read_count == 2 else {})}
        peer.emit({"id": request["id"], "result": {"thread": observed}})

    peer = FakeTransport(respond)
    if uses_target_tag:
        plan = {
            "verb": "CREATE_TASK_INTENT",
            "work_id": WORK_ID,
            "target_identity": "EM-alpha",
            "task_resolution": {
                "status": "CREATE_TASK",
                "logical_identity": "EM-alpha",
                "kind": "em",
                "direction_id": "alpha",
                "generation": 1,
            },
        }
        observed_tasks: list[dict[str, Any]] = []
    else:
        plan = {
            "verb": "DISPATCH_EXISTING",
            "work_id": WORK_ID,
            "target_identity": "EM-alpha",
            "task_resolution": {
                "status": "REUSE",
                "logical_identity": "EM-alpha",
                "kind": "em",
                "generation": 1,
                "lifecycle": "PARKED",
                "thread_id": "thread-existing",
            },
        }
        observed_tasks = observed_em("thread-existing")
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_tasks,
        )

    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["reason"] == "FINAL_THREAD_IDENTITY_CHANGED"
    assert result["thread_id"] == "thread-existing"
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/read") == 2
    assert "thread/start" not in methods
    assert "turn/start" not in methods


@pytest.mark.parametrize(
    "final_thread_source",
    [None, "hmasd-manager:EM-beta:g1"],
    ids=["missing", "changed"],
)
def test_new_manager_requires_exact_tag_on_final_read(
    tmp_path: Path, final_thread_source: str | None
) -> None:
    def completed_turn(
        _: dict[str, Any], __: dict[str, Any]
    ) -> dict[str, Any]:
        return {"id": "turn-em-alpha", "status": "completed", "items": []}

    scenario = StatefulParticipantPeer(tmp_path, turn_hook=completed_turn)
    read_count = 0

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        nonlocal read_count
        if request.get("method") != "thread/read":
            scenario.transport.responder(request, peer)
            return
        read_count += 1
        assert scenario.thread is not None
        observed = dict(scenario.thread)
        if read_count == 1:
            if final_thread_source is None:
                observed.pop("threadSource", None)
            else:
                observed["threadSource"] = final_thread_source
        peer.emit({"id": request["id"], "result": {"thread": observed}})

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            create_em_plan(),
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[],
        )

    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["reason"] == "FINAL_THREAD_IDENTITY_CHANGED"
    methods = [request.get("method") for request in peer.requests]
    assert methods.count("thread/start") == 1
    assert methods.count("thread/read") == 1
    assert "turn/start" not in methods


@pytest.mark.parametrize(
    ("thread_source", "expected_status"),
    [
        (None, "DELIVERED"),
        ("hmasd-manager:EM-beta:g1", "TASK_IDENTITY_CONFLICT"),
    ],
    ids=["legacy-no-tag", "conflicting-manager-tag"],
)
def test_legacy_named_manager_rejects_only_conflicting_present_tag(
    tmp_path: Path,
    thread_source: str | None,
    expected_status: str,
) -> None:
    thread = {
        "id": "thread-1",
        "name": "EM-alpha",
        "cwd": tmp_path.as_posix(),
        "status": {"type": "idle"},
        "turns": [],
    }
    if thread_source is not None:
        thread["threadSource"] = thread_source
    base = response_peer(listed_threads=[thread])

    def respond(request: dict[str, Any], peer: FakeTransport) -> None:
        if request.get("method") == "thread/read":
            peer.emit({"id": request["id"], "result": {"thread": thread}})
            return
        base.responder(request, peer)

    peer = FakeTransport(respond)
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            reuse_em_plan(),
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em(),
        )

    assert result["status"] == expected_status
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert ("turn/start" in methods) is (expected_status == "DELIVERED")


def test_dispatch_existing_fails_closed_on_fresh_cache_identity_conflict(
    tmp_path: Path,
) -> None:
    peer = response_peer(
        listed_threads=[],
        read_thread_name="EM-alpha",
        read_thread_cwd=str(tmp_path),
    )
    plan = reuse_em_plan(thread_id="thread-planned")
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
    plan = create_em_plan()
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
    plan = reuse_em_plan(thread_id="thread-cached")
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
    plan = reuse_em_plan(thread_id="thread-cached")
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


def test_execute_plan_scans_all_pages_before_rejecting_stale_create_plan(
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
        response_peer(
            read_thread_name="EM-alpha", read_thread_cwd=str(tmp_path)
        ).responder(request, peer)

    peer = FakeTransport(respond)
    plan = create_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em("thread-existing"),
        )
    assert result["status"] == "TASK_IDENTITY_CONFLICT"
    assert result["reason"] == "PLAN_BOUND_TASK_STATUS_MISMATCH"
    list_requests = [item for item in peer.requests if item.get("method") == "thread/list"]
    assert [item["params"].get("cursor") for item in list_requests] == [None, "cursor-2"]
    methods = [item.get("method") for item in peer.requests]
    assert "thread/start" not in methods
    assert "thread/name/set" not in methods
    assert "turn/start" not in methods


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
    plan = create_em_plan()
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
    plan = create_em_plan()
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
    plan = create_em_plan()
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
    plan = reuse_em_plan()

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
    plan = reuse_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan, packet_locator=LOCATOR, cwd=str(tmp_path), observed_tasks=[]
        )
    assert result["status"] == "TASK_IDENTITY_CONFLICT"
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
        read_thread_cwd=str(tmp_path),
    )
    compared: list[list[str]] = []

    def compare(_: Path, work_ids: list[str]) -> dict[str, Any]:
        compared.append(work_ids)
        return {"outcome": "CONFLICT", "work_ids": work_ids, "pairs": []}

    monkeypatch.setattr(tasks.hmasd_work_packet, "compare_work_ids", compare)
    plan = reuse_em_plan()
    peer_work = "b" * 64
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            peer_work_ids=[peer_work],
            observed_tasks=observed_em(),
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
        read_thread_cwd=str(tmp_path),
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
    plan = reuse_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            peer_work_ids=["b" * 64],
            root_override_reason="user authorized exact overlap",
            observed_tasks=observed_em(),
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
    plan = reuse_em_plan()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=observed_em(),
            peer_work_ids=["b" * 64],
            root_override_reason="user authorized only a known write overlap",
        )
    assert result["status"] == "WORK_OVERLAP_CONFLICT"
    assert "turn/start" not in [request.get("method") for request in peer.requests]


@pytest.mark.parametrize("target", ["Portfolio", "EM-alpha", "CM-alpha"])
def test_first_turn_contract_is_the_same_for_canonical_participant_kinds(
    target: str,
) -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.send("thread-1", WORK_ID, LOCATOR, target)
    assert result["status"] == "DELIVERED"
    turn = next(request for request in peer.requests if request.get("method") == "turn/start")
    assert turn["params"]["input"] == [
        {
            "type": "text",
            "text": tasks.dispatch_envelope_bytes(WORK_ID, LOCATOR, target).decode(),
        },
        {"type": "text", "text": PARTICIPANT_SLICE_INSTRUCTION},
    ]
    assert "$hmasd-" not in json.dumps(turn["params"]["input"])


def test_execute_plan_uses_canonical_target_identity_not_requested_alias() -> None:
    peer = response_peer()
    plan = create_em_plan(requested_target_identity="EM/alpha/g1")
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
    envelope = json.loads(turn["params"]["input"][0]["text"])
    assert envelope["target_identity"] == "EM-alpha"
    assert turn["params"]["input"][1] == {
        "type": "text",
        "text": PARTICIPANT_SLICE_INSTRUCTION,
    }


def test_execute_plan_preserves_existing_root_receiver_dispatch(
    tmp_path: Path,
) -> None:
    root_task = {
        "logical_identity": "Root",
        "generation": 1,
        "lifecycle": "ACTIVE",
        "thread_id": "thread-root",
    }
    peer = response_peer(
        listed_threads=[
            {
                "id": "thread-root",
                "name": "Root",
                "cwd": tmp_path.as_posix(),
                "status": {"type": "active"},
            }
        ],
        read_thread_name="Root",
        read_thread_cwd=str(tmp_path),
        read_thread_status={"type": "active"},
    )
    plan = {
        "verb": "DISPATCH_EXISTING",
        "work_id": WORK_ID,
        "target_identity": "Root",
        "task_resolution": {
            "status": "REUSE",
            "logical_identity": "Root",
            "kind": None,
            "generation": 1,
            "lifecycle": "ACTIVE",
            "thread_id": "thread-root",
        },
    }
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        result = client.execute_plan(
            plan,
            packet_locator=LOCATOR,
            cwd=str(tmp_path),
            observed_tasks=[root_task],
        )

    assert result["status"] == "DELIVERED"
    assert result["thread_id"] == "thread-root"
    methods = [request.get("method") for request in peer.requests]
    assert "thread/start" not in methods
    assert methods.count("turn/start") == 1


def test_cm_create_and_first_turn_use_sol_high() -> None:
    peer = response_peer()
    with tasks.AppServerClient(transport=peer, timeout=0.1) as client:
        created = client.create_thread(
            cwd="C:/Projects/HMASD", target_identity="CM-alpha"
        )
        sent = client.send(created["thread_id"], WORK_ID, LOCATOR, "CM-alpha")
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
    assert command[1:] == ("-c", "project_doc_max_bytes=0", "app-server")
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

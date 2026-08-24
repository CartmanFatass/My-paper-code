from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.db import SCHEMA_VERSION
from tools.codex_supervisor.durability.outbox import (
    AppServerOutbox,
    ClaimRejected,
    DuplicateOperation,
    MutationSpec,
    OperationState,
    OutboxError,
)
from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner
from tools.codex_supervisor.protocol import decode_jsonl_line
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.transport import TransportClosed, TransportMessage


def _run(store: ObserverStore, name: str = "session") -> str:
    return store.start_run(
        codex_binary="fixture", codex_version="1", client_name=name, process_id=None
    )


def _spec(session: str, key: str, *, thread: str = "thr") -> MutationSpec:
    return MutationSpec(
        dedupe_key=key,
        protocol_session_id=session,
        run_id=session,
        method="turn/start",
        params={"threadId": thread, "input": [{"type": "text", "text": key}]},
        target="binding:b1",
        thread_id=thread,
        binding_id="b1",
    )


def test_monotonic_ids_exact_wire_and_single_payload_copy(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    session = _run(store)
    first = AppServerOutbox(store.connection).enqueue(_spec(session, "one"))
    assert decode_jsonl_line(first.wire_bytes, 4096) == {
        "id": first.rpc_request_id,
        "method": "turn/start",
        "params": {"input": [{"text": "one", "type": "text"}], "threadId": "thr"},
    }
    assert first.wire_bytes.endswith(b"\n")
    assert store.connection.execute("SELECT COUNT(*) FROM app_server_effects").fetchone()[0] == 0
    assert store.connection.execute("SELECT COUNT(*) FROM rpc_requests").fetchone()[0] == 0
    assert store.connection.execute("SELECT COUNT(*) FROM raw_messages").fetchone()[0] == 0
    store.close()

    reopened = ObserverStore(tmp_path / "runtime")
    second_session = _run(reopened, "session-2")
    second = AppServerOutbox(reopened.connection).enqueue(_spec(second_session, "two"))
    assert second.rpc_request_id == first.rpc_request_id + 1
    reopened.close()


def test_atomic_claim_duplicate_mismatch_and_next_valid(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    session = _run(store)
    outbox = AppServerOutbox(store.connection)
    operation = outbox.enqueue(_spec(session, "same"))
    with pytest.raises(DuplicateOperation):
        outbox.enqueue(_spec(session, "same", thread="wrong"))
    following = outbox.enqueue(_spec(session, "next"))
    assert following.rpc_request_id == operation.rpc_request_id + 1
    claim = outbox.claim(
        operation.operation_id,
        protocol_session_id=session,
        target="binding:b1",
        thread_id="thr",
    )
    with pytest.raises(ClaimRejected):
        outbox.claim(
            operation.operation_id,
            protocol_session_id=session,
            target="binding:b1",
            thread_id="thr",
        )
    assert outbox.get(operation.operation_id).claim_token == claim.claim_token
    store.close()


@pytest.mark.parametrize(
    "spec",
    [
        MutationSpec("k1", "s", "s", "turn/start", {"threadId": "wrong"}, "binding:b1", "thr", "b1"),
        MutationSpec("k2", "s", "s", "thread/resume", {"threadId": "thr"}, "binding:other", "thr", "b1"),
        MutationSpec("k3", "s", "s", "thread/start", {"threadId": "thr"}, "target", None, None),
        MutationSpec("k4", "s", "s", "turn/steer", {"threadId": "thr"}, "target", "thr", None),
        MutationSpec("k5", "s", "s", "turn/start", {"threadId": "thr"}, "", "thr", None),
    ],
)
def test_outbox_rejects_wrong_thread_target_and_unsupported_v1_method(
    tmp_path: Path, spec: MutationSpec
) -> None:
    store = ObserverStore(tmp_path / "runtime")
    with pytest.raises(OutboxError):
        AppServerOutbox(store.connection).enqueue(spec)
    assert store.connection.execute("SELECT COUNT(*) FROM app_server_outbox").fetchone()[0] == 0
    store.close()


def test_stale_session_recovery_never_requeues(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    old = _run(store, "old")
    outbox = AppServerOutbox(store.connection)
    sending = outbox.enqueue(_spec(old, "sending"))
    outbox.claim(
        sending.operation_id,
        protocol_session_id=old,
        target="binding:b1",
        thread_id="thr",
    )
    ready = outbox.enqueue(_spec(old, "ready"))
    new = _run(store, "new")
    assert outbox.recover_stale_sessions(new) == (1, 1)
    assert outbox.get(sending.operation_id).state is OperationState.UNKNOWN
    assert outbox.get(ready.operation_id).state is OperationState.DONE
    assert outbox.get(ready.operation_id).outcome == "LOCAL_CANCELLED"
    later = outbox.enqueue(_spec(new, "rebuilt"))
    assert later.rpc_request_id > ready.rpc_request_id
    store.close()


class _FakeTransport:
    def __init__(self) -> None:
        self.client: AppServerClient | None = None
        self.writes: list[bytes] = []
        self.behaviors: list[str] = []
        self._closed = False

    async def recv(self) -> TransportMessage:
        await asyncio.Future()
        raise AssertionError("unreachable")

    async def send(self, message: dict[str, object]) -> bytes:
        raise AssertionError("mutation path must use send_bytes")

    async def send_bytes(self, wire: bytes) -> bytes:
        self.writes.append(bytes(wire))
        behavior = self.behaviors.pop(0) if self.behaviors else "ok"
        if behavior == "ambiguous":
            raise TransportClosed("ambiguous fixture write")
        payload = decode_jsonl_line(wire, 100_000)
        assert self.client is not None
        if behavior == "provider":
            await self.client._route(
                {"id": payload["id"], "error": {"code": -32001, "message": "busy"}}
            )
        else:
            await self.client._route(
                {
                    "id": payload["id"],
                    "result": {"turn": {"id": f"turn-{payload['id']}"}},
                }
            )
        return wire

    async def stop(self) -> str:
        self._closed = True
        return "fixture"


def test_mutation_ambiguity_is_unknown_and_next_operation_survives(tmp_path: Path) -> None:
    asyncio.run(_mutation_ambiguity_is_unknown_and_next_operation_survives(tmp_path))


async def _mutation_ambiguity_is_unknown_and_next_operation_survives(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    session = _run(store)
    transport = _FakeTransport()
    client = AppServerClient(transport, make_observer_config(tmp_path))  # type: ignore[arg-type]
    transport.client = client
    client._initialize_complete = True
    owner = AppServerSessionOwner(client, store)
    transport.behaviors = ["ambiguous", "ok"]
    first = owner.enqueue_mutation(_spec(session, "ambiguous"))
    second = owner.enqueue_mutation(_spec(session, "survives"))
    result1 = await owner.submit(first.operation_id)
    result2 = await owner.submit(second.operation_id)
    assert result1.state is OperationState.UNKNOWN
    assert result2.state is OperationState.DONE and result2.outcome == "OK"
    assert transport.writes == [first.wire_bytes, second.wire_bytes]
    with pytest.raises(ClaimRejected):
        await owner.submit(first.operation_id)
    assert len(transport.writes) == 2
    await owner.close()
    store.close()


def test_provider_error_is_done_without_retry(tmp_path: Path) -> None:
    asyncio.run(_provider_error_is_done_without_retry(tmp_path))


async def _provider_error_is_done_without_retry(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path / "runtime")
    session = _run(store)
    transport = _FakeTransport()
    client = AppServerClient(transport, make_observer_config(tmp_path))  # type: ignore[arg-type]
    transport.client = client
    client._initialize_complete = True
    owner = AppServerSessionOwner(client, store)
    transport.behaviors = ["provider"]
    operation = owner.enqueue_mutation(_spec(session, "provider"))
    result = await owner.submit(operation.operation_id)
    assert result.state is OperationState.DONE
    assert result.outcome == "PROVIDER_REJECTED"
    assert transport.writes == [operation.wire_bytes]
    await owner.close()
    store.close()


@pytest.mark.parametrize("legacy_version", [10, 11])
def test_offline_migration_keeps_rollback_database(
    tmp_path: Path, legacy_version: int
) -> None:
    runtime = tmp_path / f"runtime-{legacy_version}"
    store = ObserverStore(runtime)
    store.connection.execute("DELETE FROM schema_meta")
    store.connection.execute(
        "INSERT INTO schema_meta(version, applied_at) VALUES (?, 'legacy')",
        (legacy_version,),
    )
    store.connection.execute(
        """INSERT INTO app_server_effects(
            effect_id, owner_kind, owner_id, method, client_key, request_json,
            state, prepared_at
        ) VALUES ('legacy-prepared','THREAD_RESUME','b','thread/resume','legacy','{}',
                  'PREPARED','legacy')"""
    )
    store.connection.commit()
    store.close()
    migrated = ObserverStore(runtime)
    backup = runtime / f"state.sqlite3.v{legacy_version}.rollback"
    assert backup.exists()
    legacy = sqlite3.connect(backup)
    assert legacy.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == legacy_version
    legacy.close()
    assert migrated.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
    assert migrated.connection.execute("SELECT COUNT(*) FROM app_server_outbox").fetchone()[0] == 0
    migrated.close()


def test_seven_call_site_families_have_no_proof_hook_api(repo_root: Path) -> None:
    sources = {
        "provisioning": (repo_root / "tools/codex_supervisor/provisioning.py").read_text(),
        "managed": (repo_root / "tools/codex_supervisor/managed_turns.py").read_text(),
        "wake": (repo_root / "tools/codex_supervisor/wake_scheduler.py").read_text(),
        "resume": (repo_root / "tools/codex_supervisor/wake_recovery.py").read_text(),
        "canary": (repo_root / "tools/codex_supervisor/observer.py").read_text(),
    }
    combined = "\n".join(sources.values())
    for removed in (
        "submit_effect(", "extra_hooks", "extra_transitions",
        "request_override", "pre_write_guard",
    ):
        assert removed not in combined
    assert "_start_canary_thread" in sources["canary"]
    assert "_start_canary_turn" in sources["canary"]
    assert combined.count("enqueue_mutation(") == 6
    assert all(name in sources["provisioning"] for name in (
        "apply_memory_policy", "create_fresh_thread", "adopt_existing_thread"
    ))


def test_fresh_v12_has_no_rollback_file(tmp_path: Path) -> None:
    runtime = tmp_path / "fresh"
    store = ObserverStore(runtime)
    assert not list(runtime.glob("*.rollback"))
    assert store.connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 12
    store.close()


def test_incomplete_v12_is_rejected_instead_of_online_repaired(tmp_path: Path) -> None:
    runtime = tmp_path / "incomplete"
    store = ObserverStore(runtime)
    store.close()
    connection = sqlite3.connect(runtime / "state.sqlite3")
    connection.execute("DROP TABLE app_server_outbox")
    connection.commit()
    connection.close()
    with pytest.raises(RuntimeError, match="v12 schema is incomplete"):
        ObserverStore(runtime)

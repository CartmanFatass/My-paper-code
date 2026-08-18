from __future__ import annotations

import sys
from pathlib import Path

from tests.codex_supervisor import fake_app_server
from tools.codex_supervisor.models import ObserverConfig, RpcShape
from tools.codex_supervisor.normalizer import apply_normalized_event, normalize_message
from tools.codex_supervisor.protocol import extract_protocol_ids
from tools.codex_supervisor.store import ObserverStore


def make_observer_config(tmp_path: Path, **overrides: object) -> ObserverConfig:
    values: dict[str, object] = {
        "schema_version": 1,
        "client_name": "hmasd-codex-app-server-observer",
        "client_title": "HMASD Codex App Server Observer",
        "client_version": "0.1.0",
        "experimental_api": False,
        "initialize_timeout_seconds": 15.0,
        "request_timeout_seconds": 30.0,
        "reconcile_interval_seconds": 60.0,
        "max_jsonl_line_bytes": 1_048_576,
        "read_retry_attempts": 5,
        "read_retry_base_seconds": 0.25,
        "unexpected_server_request_policy": "terminate",
        "runtime_home": tmp_path / "runtime",
    }
    values.update(overrides)
    return ObserverConfig(**values)  # type: ignore[arg-type]


def write_fake_codex(tmp_path: Path) -> Path:
    script = Path(fake_app_server.__file__).resolve()
    if sys.platform == "win32":
        binary = tmp_path / "codex.cmd"
        binary.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        binary = tmp_path / "codex"
        binary.write_text(
            f"#!/usr/bin/env bash\nexec '{sys.executable}' '{script}' \"$@\"\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
    return binary


def _ensure_run(store: ObserverStore) -> str:
    row = store.connection.execute("SELECT run_id FROM observer_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    if row is not None:
        return str(row[0])
    return store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)


def record_completed_agent_item(
    store: ObserverStore,
    *,
    thread_id: str,
    turn_id: str,
    text: str,
    item_id: str = "itm_final",
    item_type: str = "agentMessage",
) -> int:
    run_id = _ensure_run(store)
    next_seq = int(
        store.connection.execute(
            "SELECT COALESCE(MAX(transport_seq), 0) + 1 FROM raw_messages WHERE run_id = ?",
            (run_id,),
        ).fetchone()[0]
    )
    item_payload = {
        "method": "item/completed",
        "params": {
            "threadId": thread_id,
            "turnId": turn_id,
            "item": {"id": item_id, "type": item_type, "text": text},
        },
    }
    raw_seq = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=next_seq,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=extract_protocol_ids(item_payload),
        payload=item_payload,
    )
    event = normalize_message(item_payload, raw_seq, run_id, "t-item")
    assert event is not None
    apply_normalized_event(store, event)
    turn_payload = {
        "method": "turn/completed",
        "params": {"threadId": thread_id, "turn": {"id": turn_id, "status": "completed"}},
    }
    turn_raw = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=next_seq + 1,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=extract_protocol_ids(turn_payload),
        payload=turn_payload,
    )
    turn_event = normalize_message(turn_payload, turn_raw, run_id, "t-turn")
    assert turn_event is not None
    apply_normalized_event(store, turn_event)
    return raw_seq


def ingest_recorded_command(gateway, store: ObserverStore, *, thread_id: str, turn_id: str, text: str, item_id: str | None = None) -> dict:
    seq = record_completed_agent_item(
        store,
        thread_id=thread_id,
        turn_id=turn_id,
        text=text,
        item_id=item_id or f"itm_{turn_id}",
    )
    return gateway.ingest_final_item(raw_message_seq=seq)

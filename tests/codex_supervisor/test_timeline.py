from pathlib import Path

from tools.codex_supervisor.models import ProtocolIds, RpcShape
from tools.codex_supervisor.normalizer import apply_normalized_event, normalize_message
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.timeline import render_thread_timeline_markdown, thread_timeline


def _put(store: ObserverStore, run_id: str, seq: int, message: dict) -> None:
    from tools.codex_supervisor.protocol import extract_protocol_ids

    ids = extract_protocol_ids(message)
    raw = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=seq,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=ids,
        payload=message,
    )
    event = normalize_message(message, raw, run_id, f"t{seq}")
    assert event is not None
    apply_normalized_event(store, event)


def test_timeline_is_mechanical(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)
    _put(store, run_id, 1, {"method": "thread/started", "params": {"thread": {"id": "thr"}}})
    _put(store, run_id, 2, {"method": "turn/started", "params": {"threadId": "thr", "turn": {"id": "turn"}}})
    _put(store, run_id, 3, {"method": "item/started", "params": {"threadId": "thr", "item": {"id": "itm", "type": "agentMessage"}}})
    _put(
        store,
        run_id,
        4,
        {
            "method": "item/agentMessage/delta",
            "params": {"threadId": "thr", "turnId": "turn", "itemId": "itm", "delta": "workflow failed task blocked"},
        },
    )
    _put(store, run_id, 5, {"method": "item/completed", "params": {"threadId": "thr", "item": {"id": "itm", "type": "agentMessage"}}})
    _put(
        store,
        run_id,
        6,
        {"method": "turn/completed", "params": {"threadId": "thr", "turn": {"id": "turn", "status": "failed"}}},
    )
    rendered = render_thread_timeline_markdown(thread_timeline(store, "thr"))
    assert "TURN_COMPLETED_OBSERVED status=failed" in rendered
    assert "raw=" in rendered
    assert "workflow failed" not in rendered.lower()
    assert "task blocked" not in rendered.lower()
    assert "direction inactive" not in rendered.lower()
    store.close()

from pathlib import Path

from tools.codex_supervisor.normalizer import apply_normalized_event, normalize_message
from tools.codex_supervisor.store import ObserverStore


def test_turn_and_item_snapshots(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)
    started = normalize_message(
        {"method": "turn/started", "params": {"threadId": "thr", "turn": {"id": "turn"}}},
        store.record_raw_message(
            run_id=run_id,
            direction="stdout",
            transport_seq=1,
            rpc_shape="NOTIFICATION",
            ids=type("I", (), {"request_id": None, "method": "turn/started", "thread_id": "thr", "turn_id": "turn", "item_id": None})(),
            payload={},
        ),
        run_id,
        "t1",
    )
    assert started is not None
    apply_normalized_event(store, started)
    completed = normalize_message(
        {
            "method": "turn/completed",
            "params": {"threadId": "thr", "turn": {"id": "turn", "status": "failed", "error": {"code": 1}}},
        },
        store.record_raw_message(
            run_id=run_id,
            direction="stdout",
            transport_seq=2,
            rpc_shape="NOTIFICATION",
            ids=type("I", (), {"request_id": None, "method": "turn/completed", "thread_id": "thr", "turn_id": "turn", "item_id": None})(),
            payload={},
        ),
        run_id,
        "t2",
    )
    assert completed is not None
    apply_normalized_event(store, completed)
    row = dict(store.connection.execute("SELECT * FROM turn_snapshots WHERE turn_id='turn'").fetchone())
    assert row["status"] == "failed"
    assert row["started_at"]
    assert row["completed_at"]
    store.close()


def test_lexical_hazard_does_not_change_snapshots(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="c", codex_version="v", client_name="n", process_id=1)
    from tools.codex_supervisor.models import ProtocolIds, RpcShape

    seq = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=1,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=ProtocolIds(None, "item/agentMessage/delta", "thr", "turn", "itm"),
        payload={},
    )
    event = normalize_message(
        {
            "method": "item/agentMessage/delta",
            "params": {"threadId": "thr", "turnId": "turn", "itemId": "itm", "delta": "BLOCKED FAILED RETIRED"},
        },
        seq,
        run_id,
        "t",
    )
    assert event is not None
    apply_normalized_event(store, event)
    item = dict(store.connection.execute("SELECT * FROM item_snapshots WHERE item_id='itm'").fetchone())
    assert "BLOCKED" not in item["safe_metadata_json"]
    assert item["lifecycle"] == "STARTED"
    store.close()

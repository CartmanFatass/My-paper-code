from pathlib import Path

from tools.codex_supervisor.models import NormalizedEvent, ProtocolIds, RpcShape
from tools.codex_supervisor.store import ObserverStore


def test_run_lifecycle_and_raw_files(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="codex", codex_version="v", client_name="obs", process_id=1)
    store.append_raw_file(run_id, "stdin.jsonl", b"{}\n")
    store.append_raw_file(run_id, "stdout.jsonl", b"{}\n")
    store.append_raw_file(run_id, "stderr.log", b"err")
    seq = store.record_raw_message(
        run_id=run_id,
        direction="stdout",
        transport_seq=1,
        rpc_shape=RpcShape.NOTIFICATION,
        ids=ProtocolIds(None, "turn/started", "thr", "turn", None),
        payload={"method": "turn/started", "params": {"threadId": "thr", "turn": {"id": "turn"}}},
    )
    store.apply_normalized_event(
        NormalizedEvent("TURN_STARTED_OBSERVED", seq, run_id, "thr", "turn", None, "inProgress", {"status": "inProgress"}, "t")
    )
    store.mark_initialized(run_id)
    store.end_run(run_id, "NORMAL", 0)
    assert (tmp_path / "raw" / run_id / "stderr.log").read_bytes() == b"err"
    assert store.latest_thread_snapshot("thr")["thread_id"] == "thr"
    recovered = store.recover_incomplete_runs()
    assert recovered == []
    store.close()


def test_recover_incomplete_run(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    run_id = store.start_run(codex_binary="codex", codex_version="v", client_name="obs", process_id=9)
    store.close()
    again = ObserverStore(tmp_path)
    recovered = again.recover_incomplete_runs()
    assert recovered == [run_id]
    row = again.connection.execute("SELECT end_kind FROM observer_runs WHERE run_id=?", (run_id,)).fetchone()
    assert row[0] == "PROCESS_EXIT"
    again.close()

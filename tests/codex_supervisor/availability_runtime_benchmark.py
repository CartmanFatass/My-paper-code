"""Result-blind App Server availability microbenchmark. Not a pytest test."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.codex_supervisor.db import backup_before_v12, connect, initialize_database
from tools.codex_supervisor.durability.outbox import AppServerOutbox, MutationSpec
from tools.codex_supervisor.store import ObserverStore


SLOS = {
    "enqueue_claim_p95_ms": 25.0,
    "enqueue_claim_p99_ms": 75.0,
    "completion_p95_ms": 25.0,
    "status_control_failed_mutation_p95_ms": 250.0,
    "wake_1000_lock_p95_ms": 100.0,
    "wake_1000_prepare_p95_ms": 250.0,
    "migration_100mb_total_p95_s": 15.0,
    "migration_exclusive_write_p95_s": 2.0,
    "persistent_payload_copies": 1,
    "mutation_retries": 0,
}


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def _resources() -> dict[str, int | float | None]:
    try:
        import psutil

        process = psutil.Process()
        io = process.io_counters()
        return {
            "rss_bytes": process.memory_info().rss,
            "read_bytes": getattr(io, "read_bytes", None),
            "write_bytes": getattr(io, "write_bytes", None),
            "cpu_seconds": sum(process.cpu_times()[:2]),
        }
    except Exception:
        return {"rss_bytes": None, "read_bytes": None, "write_bytes": None, "cpu_seconds": time.process_time()}


def _outbox_panel(root: Path, iterations: int) -> dict[str, object]:
    store = ObserverStore(root / "outbox")
    session = store.start_run(
        codex_binary="benchmark", codex_version="1", client_name="benchmark", process_id=None
    )
    outbox = AppServerOutbox(store.connection)
    enqueue_claim: list[float] = []
    completion: list[float] = []
    payload_bytes = 0
    before_size = store.path.stat().st_size
    for index in range(iterations):
        started = time.perf_counter()
        operation = outbox.enqueue(
            MutationSpec(
                dedupe_key=f"bench:{index}",
                protocol_session_id=session,
                run_id=session,
                method="turn/start",
                params={"threadId": "thr", "input": [{"type": "text", "text": "x" * 256}]},
                target="binding:bench",
                thread_id="thr",
                binding_id="bench",
            )
        )
        claim = outbox.claim(
            operation.operation_id,
            protocol_session_id=session,
            target="binding:bench",
            thread_id="thr",
        )
        enqueue_claim.append((time.perf_counter() - started) * 1000)
        payload_bytes += len(operation.wire_bytes)
        started = time.perf_counter()
        outbox.complete(claim, outcome="OK", response_raw_ref=f"bench:{index}")
        completion.append((time.perf_counter() - started) * 1000)
    store.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    after_size = store.path.stat().st_size
    persistent_copies = store.connection.execute(
        "SELECT COUNT(*) FROM app_server_outbox WHERE length(wire_bytes) > 0"
    ).fetchone()[0] / iterations
    store.close()
    return {
        "iterations": iterations,
        "enqueue_claim_p95_ms": _percentile(enqueue_claim, 0.95),
        "enqueue_claim_p99_ms": _percentile(enqueue_claim, 0.99),
        "completion_p95_ms": _percentile(completion, 0.95),
        "persistent_payload_copies": persistent_copies,
        "payload_bytes": payload_bytes,
        "database_growth_bytes": after_size - before_size,
    }


def _wake_panel(root: Path, repeats: int) -> dict[str, object]:
    store = ObserverStore(root / "wake")
    results: dict[str, object] = {}
    for width in (1, 10, 100, 1000):
        timings: list[float] = []
        statement_counts: list[int] = []
        for repeat in range(repeats):
            store.connection.execute("DELETE FROM wake_batch_messages")
            store.connection.execute("DELETE FROM mailbox_messages")
            store.connection.executemany(
                """INSERT INTO mailbox_messages(
                    message_id,source_system,source_event_key,target_actor_context_id,
                    message_kind,subject_ref,payload_ref,priority,delivery_state,
                    intake_state,created_at
                ) VALUES (?, 'OPERATOR', ?, 'actor', 'REPORT_AVAILABLE', 's', 'p', 1,
                          'BATCHED','NOT_ACKNOWLEDGED','t')""",
                [(f"m{index}", f"e{repeat}:{index}") for index in range(width)],
            )
            store.connection.executemany(
                "INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal) VALUES ('w',?,?)",
                [(f"m{index}", index) for index in range(width)],
            )
            store.connection.commit()
            statements = 0

            def trace(sql: str) -> None:
                nonlocal statements
                if sql.lstrip().upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
                    statements += 1

            store.connection.set_trace_callback(trace)
            started = time.perf_counter()
            with store.connection:
                store.connection.execute(
                    """UPDATE mailbox_messages SET delivery_state='DELIVERED_TO_TURN',
                       delivery_version=delivery_version+1
                       WHERE delivery_state='BATCHED' AND message_id IN (
                           SELECT message_id FROM wake_batch_messages WHERE wake_batch_id='w'
                       )"""
                )
            timings.append((time.perf_counter() - started) * 1000)
            statement_counts.append(statements)
            store.connection.set_trace_callback(None)
        results[str(width)] = {
            "lock_p95_ms": _percentile(timings, 0.95),
            "prepare_p95_ms": _percentile(timings, 0.95),
            "sql_statement_counts": sorted(set(statement_counts)),
        }
    store.close()
    return results


def _migration_panel(root: Path, migration_mb: int) -> dict[str, object]:
    runtime = root / "migration"
    store = ObserverStore(runtime)
    store.connection.execute("CREATE TABLE benchmark_padding(payload BLOB NOT NULL)")
    store.connection.execute("INSERT INTO benchmark_padding(payload) VALUES (zeroblob(?))", (migration_mb * 1024 * 1024,))
    store.connection.execute("DELETE FROM schema_meta")
    store.connection.execute("INSERT INTO schema_meta(version,applied_at) VALUES (11,'legacy')")
    store.connection.commit()
    store.close()
    started = time.perf_counter()
    backup_before_v12(runtime / "state.sqlite3")
    backup_seconds = time.perf_counter() - started
    connection = connect(runtime / "state.sqlite3")
    started = time.perf_counter()
    initialize_database(connection)
    exclusive_seconds = time.perf_counter() - started
    connection.close()
    return {
        "fixture_mb": migration_mb,
        "total_seconds": backup_seconds + exclusive_seconds,
        "backup_seconds": backup_seconds,
        "exclusive_write_seconds": exclusive_seconds,
        "rollback_path": str(runtime / "state.sqlite3.v11.rollback"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--wake-repeats", type=int, default=20)
    parser.add_argument("--migration-mb", type=int, default=100)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    resource_before = _resources()
    wall_started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="hmasd-availability-benchmark-") as temporary:
        root = Path(temporary)
        report = {
            "schema": "HMASD_APP_SERVER_AVAILABILITY_BENCHMARK_V1",
            "slos": SLOS,
            "outbox": _outbox_panel(root, args.iterations),
            "wake": _wake_panel(root, args.wake_repeats),
            "migration": _migration_panel(root, args.migration_mb),
            "mutation_retries": 0,
            "isolation_model": "operation/session quarantine; host control remains independent",
        }
    report["wall_seconds"] = time.perf_counter() - wall_started
    report["resources_before"] = resource_before
    report["resources_after"] = _resources()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

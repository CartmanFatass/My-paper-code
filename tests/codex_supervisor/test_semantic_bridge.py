from pathlib import Path
import sqlite3

import pytest

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_supervisor import semantic_bridge as bridge_mod
from tools.codex_supervisor.semantic_bridge import SemanticBridge, SemanticBridgeError


def test_eligible_root_and_portfolio(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    root = bridge.snapshot(seeded["root"].actor_context_id)
    portfolio = bridge.snapshot(seeded["portfolio"].actor_context_id)
    assert root.actor_kind == "OPERATIONAL_ROOT"
    assert root.state == "ACTIVE"
    assert portfolio.actor_kind == "PORTFOLIO"
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize("key", ["em", "cm", "leaf", "released"])
def test_ineligible_actors_rejected(tmp_path: Path, key: str) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    with pytest.raises(SemanticBridgeError):
        bridge.snapshot(seeded[key].actor_context_id)
    with pytest.raises(SemanticBridgeError):
        bridge.snapshot("actor_missing")
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_reanchor_ack_is_idempotent(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    checkpoint = seed_reanchor(seeded["semantic"], actor_id)
    first = bridge.acknowledge_reanchor(
        actor_context_id=actor_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        expected_state_version=int(checkpoint["state_version"]),
        expected_epoch_id=checkpoint.get("epoch_id"),
        expected_epoch_revision=checkpoint.get("epoch_revision"),
        app_server_turn_id="turn_live",
        supervisor_command_id="cmd_1",
    )
    second = bridge.acknowledge_reanchor(
        actor_context_id=actor_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        expected_state_version=int(checkpoint["state_version"]),
        expected_epoch_id=checkpoint.get("epoch_id"),
        expected_epoch_revision=checkpoint.get("epoch_revision"),
        app_server_turn_id="turn_other",
        supervisor_command_id="cmd_1",
    )
    assert first["ack_id"] == second["ack_id"]
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_direct_reanchor_holds_currentness_writer_guard_through_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    checkpoint = seed_reanchor(seeded["semantic"], actor_id)
    original = bridge_mod.context_reanchor_ack
    observed = {"writer_blocked": False}

    def checked_reanchor(*args, **kwargs):
        writer = sqlite3.connect(
            bridge.semantic_state_path, timeout=0.0, isolation_level=None
        )
        try:
            writer.execute("PRAGMA busy_timeout = 0")
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                writer.execute("BEGIN IMMEDIATE")
            observed["writer_blocked"] = True
        finally:
            writer.close()
        return original(*args, **kwargs)

    monkeypatch.setattr(bridge_mod, "context_reanchor_ack", checked_reanchor)
    bridge.acknowledge_reanchor(
        actor_context_id=actor_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        expected_state_version=int(checkpoint["state_version"]),
        expected_epoch_id=checkpoint.get("epoch_id"),
        expected_epoch_revision=checkpoint.get("epoch_revision"),
        app_server_turn_id="turn_direct_guard",
        supervisor_command_id="cmd_direct_guard",
    )
    assert observed["writer_blocked"] is True
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_direct_reanchor_records_receipt_only_after_semantic_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    checkpoint = seed_reanchor(seeded["semantic"], actor_id)
    original_record = seeded["supervisor"].record_command_receipt
    observed = {"committed": False}

    def checked_record(**kwargs):
        reader = sqlite3.connect(bridge.semantic_state_path)
        try:
            assert reader.execute(
                "SELECT 1 FROM reanchor_acks WHERE ack_id = ?",
                (kwargs["result"]["ack_id"],),
            ).fetchone() is not None
            assert reader.execute(
                "SELECT state FROM obligations WHERE subject = ?",
                (checkpoint["checkpoint_id"],),
            ).fetchone()[0] == "RESOLVED"
            observed["committed"] = True
        finally:
            reader.close()
        return original_record(**kwargs)

    monkeypatch.setattr(seeded["supervisor"], "record_command_receipt", checked_record)
    bridge.acknowledge_reanchor(
        actor_context_id=actor_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        expected_state_version=int(checkpoint["state_version"]),
        expected_epoch_id=checkpoint.get("epoch_id"),
        expected_epoch_revision=checkpoint.get("epoch_revision"),
        app_server_turn_id="turn_direct_receipt_order",
        supervisor_command_id="cmd_direct_receipt_order",
    )
    assert observed["committed"] is True
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_direct_reanchor_recovers_committed_effect_after_receipt_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    checkpoint = seed_reanchor(seeded["semantic"], actor_id)
    original_record = seeded["supervisor"].record_command_receipt
    failures = 0

    def fail_first_receipt(**kwargs):
        nonlocal failures
        failures += 1
        if failures == 1:
            raise RuntimeError("forced supervisor receipt failure")
        return original_record(**kwargs)

    monkeypatch.setattr(
        seeded["supervisor"], "record_command_receipt", fail_first_receipt
    )
    call = {
        "actor_context_id": actor_id,
        "checkpoint_id": str(checkpoint["checkpoint_id"]),
        "expected_state_version": int(checkpoint["state_version"]),
        "expected_epoch_id": checkpoint.get("epoch_id"),
        "expected_epoch_revision": checkpoint.get("epoch_revision"),
        "app_server_turn_id": "turn_receipt_recovery",
        "supervisor_command_id": "cmd_receipt_recovery",
    }
    with pytest.raises(RuntimeError, match="forced supervisor receipt failure"):
        bridge.acknowledge_reanchor(**call)
    committed = bridge.semantic.connection.execute(
        "SELECT ack_id FROM reanchor_acks WHERE actor_turn_id = 'turn_receipt_recovery'"
    ).fetchone()
    assert committed is not None
    assert seeded["supervisor"].get_command_receipt("cmd_receipt_recovery") is None

    recovered = bridge.acknowledge_reanchor(**call)
    assert recovered["ack_id"] == committed["ack_id"]
    assert seeded["supervisor"].get_command_receipt("cmd_receipt_recovery") is not None
    assert bridge.semantic.connection.execute(
        "SELECT COUNT(*) FROM reanchor_acks WHERE actor_turn_id = 'turn_receipt_recovery'"
    ).fetchone()[0] == 1
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_direct_reanchor_ambient_rollback_never_writes_supervisor_receipt(
    tmp_path: Path,
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    checkpoint = seed_reanchor(seeded["semantic"], actor_id)
    connection = bridge.semantic.connection
    connection.execute("BEGIN IMMEDIATE")
    result = bridge.acknowledge_reanchor(
        actor_context_id=actor_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        expected_state_version=int(checkpoint["state_version"]),
        expected_epoch_id=checkpoint.get("epoch_id"),
        expected_epoch_revision=checkpoint.get("epoch_revision"),
        app_server_turn_id="turn_rollback",
        supervisor_command_id="cmd_rollback",
    )
    assert connection.execute(
        "SELECT 1 FROM reanchor_acks WHERE ack_id = ?", (result["ack_id"],)
    ).fetchone() is not None
    assert seeded["supervisor"].get_command_receipt("cmd_rollback") is None
    connection.rollback()
    assert connection.execute(
        "SELECT 1 FROM reanchor_acks WHERE ack_id = ?", (result["ack_id"],)
    ).fetchone() is None
    assert connection.execute(
        "SELECT state FROM obligations WHERE subject = ?",
        (checkpoint["checkpoint_id"],),
    ).fetchone()[0] == "OPEN"
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_direct_reanchor_semantic_commit_failure_never_writes_receipt(
    tmp_path: Path,
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge: SemanticBridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    checkpoint = seed_reanchor(seeded["semantic"], actor_id)
    real_connection = bridge.semantic.connection

    class CommitFailConnection:
        def __getattr__(self, name):
            return getattr(real_connection, name)

        def commit(self):
            raise sqlite3.OperationalError("forced semantic commit failure")

    bridge.semantic.connection = CommitFailConnection()
    with pytest.raises(sqlite3.OperationalError, match="forced semantic commit failure"):
        bridge.acknowledge_reanchor(
            actor_context_id=actor_id,
            checkpoint_id=str(checkpoint["checkpoint_id"]),
            expected_state_version=int(checkpoint["state_version"]),
            expected_epoch_id=checkpoint.get("epoch_id"),
            expected_epoch_revision=checkpoint.get("epoch_revision"),
            app_server_turn_id="turn_commit_failure",
            supervisor_command_id="cmd_commit_failure",
        )
    bridge.semantic.connection = real_connection
    assert seeded["supervisor"].get_command_receipt("cmd_commit_failure") is None
    assert real_connection.execute(
        "SELECT 1 FROM reanchor_acks WHERE actor_turn_id = 'turn_commit_failure'"
    ).fetchone() is None
    assert real_connection.execute(
        "SELECT state FROM obligations WHERE subject = ?",
        (checkpoint["checkpoint_id"],),
    ).fetchone()[0] == "OPEN"
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_snapshot_uses_one_sqlite_read_transaction_across_interleaving_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    before = bridge.snapshot(actor_id)
    original = bridge.semantic.current_actor_workflow
    interleaved = False

    def current_with_interleaving(requested_actor_id: str):
        nonlocal interleaved
        if not interleaved:
            interleaved = True
            writer = sqlite3.connect(tmp_path / "semantic.sqlite3")
            try:
                writer.execute("PRAGMA journal_mode = WAL")
                writer.execute(
                    "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                    (actor_id,),
                )
                writer.commit()
            finally:
                writer.close()
        return original(requested_actor_id)

    monkeypatch.setattr(bridge.semantic, "current_actor_workflow", current_with_interleaving)
    during = bridge.snapshot(actor_id)
    assert during.state_version == before.state_version
    assert seeded["semantic"].connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0] == before.state_version + 1
    bridge.close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_bridge_does_not_import_promotion_or_write_files() -> None:
    source = Path(bridge_mod.__file__).read_text(encoding="utf-8")
    assert "mark_promotion_applied" not in source
    assert "create_promotion_proposal" not in source
    assert "write_text" not in source
    assert "open(" not in source
    assert not hasattr(SemanticBridge, "write_file")


def test_bridge_opens_existing_database_without_initialize(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tools.codex_semantic_mvp.store import SemanticStore

    semantic = SemanticStore(tmp_path / "semantic.sqlite3").initialize()
    semantic.close()

    def initialize_must_not_run(self):
        raise AssertionError("host bridge must not initialize or migrate semantic state")

    monkeypatch.setattr(SemanticStore, "initialize", initialize_must_not_run)
    bridge = SemanticBridge(tmp_path / "semantic.sqlite3")
    bridge.close()

from __future__ import annotations

import shutil
import sqlite3
import struct
import threading
from pathlib import Path

import pytest

import tools.codex_semantic_mvp.db as semantic_db
import tools.codex_semantic_mvp.store as semantic_store
from tools.codex_semantic_mvp.db import (
    SCHEMA_VERSION,
    SemanticDatabaseValidationError,
    validate_existing_database,
)
from tools.codex_semantic_mvp.store import SemanticStore
from tools.codex_supervisor.cli import _semantic_state_for_profile
from tools.codex_supervisor.host_control import (
    HostControlChannel,
    HostControlValidationError,
)
from tools.codex_supervisor.runtime_profiles import RuntimeProfile


def _snapshot(path: Path) -> dict[str, bytes]:
    return _directory_snapshot(path)


def _directory_snapshot(path: Path) -> dict[str, bytes]:
    return {
        item.name: item.read_bytes()
        for item in path.parent.iterdir()
        if item.is_file()
    }


def _initialize(path: Path) -> None:
    store = SemanticStore(path).initialize()
    store.close()


def _copy_live_wal_triplet(tmp_path: Path, name: str = "copy") -> Path:
    source = tmp_path / "source" / "semantic.sqlite3"
    source.parent.mkdir(exist_ok=True)
    store = SemanticStore(source).initialize()
    target = tmp_path / name / "semantic.sqlite3"
    target.parent.mkdir(exist_ok=True)
    try:
        for suffix in ("", "-wal", "-shm"):
            shutil.copyfile(Path(f"{source}{suffix}"), Path(f"{target}{suffix}"))
    finally:
        store.close()
    return target


def _copy_live_wal_without_shm(tmp_path: Path, name: str = "wal-only") -> Path:
    source = tmp_path / f"{name}-source" / "semantic.sqlite3"
    source.parent.mkdir(exist_ok=True)
    store = SemanticStore(source).initialize()
    target = tmp_path / name / "semantic.sqlite3"
    target.parent.mkdir(exist_ok=True)
    try:
        store.connection.execute(
            """INSERT INTO hook_guards
            (guard_key, event_name, count, created_at, updated_at)
            VALUES ('wal-only-committed', 'fixture', 7, 'created', 'updated')"""
        )
        store.connection.commit()
        shutil.copyfile(source, target)
        shutil.copyfile(Path(f"{source}-wal"), Path(f"{target}-wal"))
    finally:
        store.close()
    assert not Path(f"{target}-shm").exists()
    return target


def _shm_max_frame(path: Path) -> int:
    header = Path(f"{path}-shm").read_bytes()[:48]
    for prefix in ("<", ">"):
        values = struct.unpack(f"{prefix}III BBH II", header[:24])
        if values[0] == 3007000:
            return int(values[6])
    raise AssertionError("fixture SHM header has no recognized byte order")


def _wal_layout(path: Path) -> tuple[int, int, int]:
    wal = Path(f"{path}-wal").read_bytes()
    raw_page_size = int.from_bytes(wal[8:12], "big")
    page_size = 65536 if raw_page_size == 1 else raw_page_size
    frame_size = 24 + page_size
    return page_size, frame_size, (len(wal) - 32) // frame_size


def _copy_restart_reused_wal_triplet(tmp_path: Path, name: str = "restart-copy") -> Path:
    source = tmp_path / f"{name}-source" / "semantic.sqlite3"
    source.parent.mkdir(exist_ok=True)
    store = SemanticStore(source).initialize()
    target = tmp_path / name / "semantic.sqlite3"
    target.parent.mkdir(exist_ok=True)
    try:
        connection = store.connection
        connection.execute("PRAGMA wal_autocheckpoint = 0")
        for value in range(16):
            connection.execute(
                """INSERT INTO hook_guards
                (guard_key, event_name, count, created_at, updated_at)
                VALUES (?, 'fixture', 1, ?, ?)""",
                (f"fixture-{value}-" + ("x" * 3072), str(value), str(value)),
            )
            connection.commit()
        checkpoint = connection.execute("PRAGMA wal_checkpoint(RESTART)").fetchone()
        assert tuple(checkpoint) == (0, checkpoint[1], checkpoint[1])
        connection.execute(
            """INSERT INTO hook_guards
            (guard_key, event_name, count, created_at, updated_at)
            VALUES ('fixture-current', 'fixture', 1, 'current', 'current')"""
        )
        connection.commit()
        for suffix in ("", "-wal", "-shm"):
            shutil.copyfile(Path(f"{source}{suffix}"), Path(f"{target}{suffix}"))
    finally:
        store.close()

    _page_size, frame_size, physical_frames = _wal_layout(target)
    logical_frames = _shm_max_frame(target)
    assert 0 < logical_frames < physical_frames
    wal = Path(f"{target}-wal").read_bytes()
    logical_salt = wal[16:24]
    assert wal[32 + 8 : 32 + 16] == logical_salt
    tail_header = 32 + logical_frames * frame_size
    assert wal[tail_header + 8 : tail_header + 16] != logical_salt
    return target


def _build_invalid(path: Path, kind: str) -> None:
    if kind == "empty":
        path.touch()
        return
    if kind == "corrupt":
        path.write_bytes(b"not a sqlite database")
        return
    if kind == "unrelated":
        connection = sqlite3.connect(path)
        connection.execute("CREATE TABLE unrelated(value TEXT)")
        connection.commit()
        connection.close()
        return

    _initialize(path)
    connection = sqlite3.connect(path)
    if kind == "missing_table":
        connection.execute("DROP TABLE actor_contexts")
    elif kind == "missing_column":
        connection.execute("ALTER TABLE user_authority_grants RENAME TO old_grants")
        connection.execute(
            """CREATE TABLE user_authority_grants (
            grant_id TEXT PRIMARY KEY,
            actor_context_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            created_at TEXT NOT NULL
            )"""
        )
        connection.execute("DROP TABLE old_grants")
    elif kind == "behind":
        connection.execute("UPDATE schema_meta SET version = ?", (SCHEMA_VERSION - 1,))
    elif kind == "ahead":
        connection.execute("UPDATE schema_meta SET version = ?", (SCHEMA_VERSION + 1,))
    else:  # pragma: no cover - test helper contract
        raise AssertionError(kind)
    connection.commit()
    connection.close()


@pytest.mark.parametrize(
    "kind",
    [
        "empty",
        "corrupt",
        "unrelated",
        "missing_table",
        "missing_column",
        "behind",
        "ahead",
    ],
)
def test_invalid_database_fails_closed_without_filesystem_mutation(
    tmp_path: Path,
    kind: str,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    path = tmp_path / f"{kind}.sqlite3"
    _build_invalid(path, kind)
    before = _snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError):
        validate_existing_database(path)
    assert _snapshot(path) == before

    with pytest.raises(HostControlValidationError, match="compatible HMASD"):
        HostControlChannel(
            tmp_path / f"control-{kind}",
            profile=RuntimeProfile.MANAGED_MANUAL,
            repo_root=repo,
            semantic_state_path=path,
        )
    assert _snapshot(path) == before

    with pytest.raises(SystemExit, match="compatible HMASD"):
        _semantic_state_for_profile(
            repo,
            RuntimeProfile.MANAGED_MANUAL,
            str(path),
        )
    assert _snapshot(path) == before


def test_valid_initialized_schema_v3_database_passes_existing_open(
    tmp_path: Path,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    before = _snapshot(path)

    assert validate_existing_database(path) == path.resolve()
    assert _snapshot(path) == before

    store = SemanticStore.open_existing(path)
    try:
        assert store.connection.execute(
            "SELECT MAX(version) FROM schema_meta"
        ).fetchone()[0] == SCHEMA_VERSION
    finally:
        store.close()


@pytest.mark.parametrize("mutation", ["extra_column", "altered_type", "constraint", "trigger", "object"])
def test_noncanonical_schema_manifest_fails_closed_without_mutation(
    tmp_path: Path, mutation: str
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    connection = sqlite3.connect(path)
    if mutation == "extra_column":
        connection.execute("ALTER TABLE hook_guards ADD COLUMN surprise TEXT")
    elif mutation in {"altered_type", "constraint"}:
        operation = "INTEGER NOT NULL" if mutation == "altered_type" else "TEXT NOT NULL CHECK(length(operation) > 0)"
        connection.execute("ALTER TABLE user_authority_grants RENAME TO old_grants")
        connection.execute(
            f"""CREATE TABLE user_authority_grants (
            grant_id TEXT PRIMARY KEY, actor_context_id TEXT NOT NULL,
            operation {operation}, created_at TEXT NOT NULL, consumed_at TEXT
            )"""
        )
        connection.execute("DROP TABLE old_grants")
    elif mutation == "trigger":
        connection.execute(
            "CREATE TRIGGER surprise_trigger AFTER INSERT ON hook_guards BEGIN SELECT 1; END"
        )
    else:
        connection.execute("CREATE TABLE surprise_object(value TEXT)")
    connection.commit()
    connection.close()
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match="schema manifest"):
        validate_existing_database(path)
    assert _directory_snapshot(path) == before


def test_open_existing_rejects_same_bytes_path_replacement_between_probe_and_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    replacement_dir = tmp_path / "replacement"
    replacement_dir.mkdir()
    replacement = replacement_dir / "semantic.sqlite3"
    replacement.write_bytes(path.read_bytes())
    replacement_bytes = replacement.read_bytes()
    original = semantic_store.connect_existing

    def replace_then_open(token):
        replacement.replace(path)
        return original(token)

    monkeypatch.setattr(semantic_store, "connect_existing", replace_then_open)
    with pytest.raises(SemanticDatabaseValidationError, match="input changed after validation"):
        SemanticStore.open_existing(path)
    assert path.read_bytes() == replacement_bytes
    assert list(replacement_dir.iterdir()) == []


def test_copied_live_wal_triplet_passes_without_source_file_mutation(
    tmp_path: Path,
) -> None:
    path = _copy_live_wal_triplet(tmp_path)
    before = _directory_snapshot(path)

    assert validate_existing_database(path) == path.resolve()

    assert _directory_snapshot(path) == before


def test_wal_without_shm_validates_without_source_mutation_and_opens_with_data(
    tmp_path: Path,
) -> None:
    path = _copy_live_wal_without_shm(tmp_path)
    before = _directory_snapshot(path)

    assert validate_existing_database(path) == path.resolve()
    assert _directory_snapshot(path) == before

    store = SemanticStore.open_existing(path)
    try:
        row = store.connection.execute(
            "SELECT count FROM hook_guards WHERE guard_key = 'wal-only-committed'"
        ).fetchone()
        assert row is not None and int(row[0]) == 7
        assert Path(f"{path}-shm").is_file()
    finally:
        store.close()


def test_wal_without_shm_acquires_writer_fence_before_shm_or_full_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The only sidecar-creating operation is fenced before it can run."""

    path = _copy_live_wal_without_shm(tmp_path, "wal-only-ordering")
    shm_path = Path(f"{path}-shm")
    events: list[str] = []
    original_connect = semantic_db.sqlite3.connect
    original_transfer = semantic_db.LiveExistingDatabaseBinding.transfer_to
    transfer_completed = False

    class RecordingConnection:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection

        @property
        def in_transaction(self) -> bool:
            return self._connection.in_transaction

        def execute(self, statement, *args, **kwargs):
            normalized = " ".join(str(statement).upper().split())
            if normalized == "BEGIN IMMEDIATE":
                assert not shm_path.exists()
                events.append("begin")
            elif normalized == "PRAGMA SYNCHRONOUS = FULL":
                assert transfer_completed is True
                assert not self._connection.in_transaction
                events.append("synchronous")
            return self._connection.execute(statement, *args, **kwargs)

        def __getattr__(self, name: str):
            return getattr(self._connection, name)

    live_uri = f"{path.resolve().as_uri()}?mode=rw"

    def instrumented_connect(database, *args, **kwargs):
        connection = original_connect(database, *args, **kwargs)
        if str(database) == live_uri:
            return RecordingConnection(connection)
        return connection

    def instrumented_transfer(binding, owner):
        nonlocal transfer_completed
        assert events == ["begin"]
        result = original_transfer(binding, owner)
        transfer_completed = True
        events.append("transfer")
        return result

    monkeypatch.setattr(semantic_db.sqlite3, "connect", instrumented_connect)
    monkeypatch.setattr(
        semantic_db.LiveExistingDatabaseBinding,
        "transfer_to",
        instrumented_transfer,
    )

    store = SemanticStore.open_existing(path)
    try:
        assert events == ["begin", "transfer", "synchronous"]
        assert shm_path.is_file()
        assert store.connection.execute("PRAGMA synchronous").fetchone()[0] == 2
    finally:
        store.close()


def test_wal_without_shm_drift_between_validation_and_live_bind_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _copy_live_wal_without_shm(tmp_path, "wal-only-drift")
    wal_path = Path(f"{path}-wal")
    original = semantic_store.connect_existing

    def drift_then_open(token):
        wal = bytearray(wal_path.read_bytes())
        wal[-1] ^= 0x01
        wal_path.write_bytes(wal)
        return original(token)

    monkeypatch.setattr(semantic_store, "connect_existing", drift_then_open)
    with pytest.raises(
        SemanticDatabaseValidationError,
        match="input changed after validation",
    ):
        SemanticStore.open_existing(path)
    assert not Path(f"{path}-shm").exists()


def test_main_only_token_rejects_wal_committed_during_live_connect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "main-only" / "semantic.sqlite3"
    path.parent.mkdir()
    _initialize(path)
    wal_path = Path(f"{path}-wal")
    shm_path = Path(f"{path}-shm")
    assert not wal_path.exists()
    assert not shm_path.exists()
    before_main = path.read_bytes()
    before_names = {item.name for item in path.parent.iterdir()}
    original_connect = semantic_db.sqlite3.connect
    live_uri = f"{path.resolve().as_uri()}?mode=rw"
    writers: list[sqlite3.Connection] = []

    def connect_with_interleaving(database, *args, **kwargs):
        if str(database) == live_uri and not writers:
            writer = original_connect(path, isolation_level=None)
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute(
                """INSERT INTO hook_guards
                (guard_key, event_name, count, created_at, updated_at)
                VALUES ('connect-race', 'fixture', 91, 'created', 'updated')"""
            )
            writers.append(writer)
            assert wal_path.is_file()
            assert shm_path.is_file()
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(semantic_db.sqlite3, "connect", connect_with_interleaving)
    try:
        with pytest.raises(
            SemanticDatabaseValidationError,
            match="sibling set changed after validation",
        ):
            SemanticStore.open_existing(path)
        assert path.read_bytes() == before_main
        assert {item.name for item in path.parent.iterdir()} == before_names | {
            wal_path.name,
            shm_path.name,
        }
        assert writers[0].execute(
            "SELECT count FROM hook_guards WHERE guard_key = 'connect-race'"
        ).fetchone()[0] == 91
    finally:
        for writer in writers:
            writer.close()


@pytest.mark.parametrize("source_kind", ["main_only", "existing_wal"])
def test_live_bind_writer_fence_blocks_final_check_to_transfer_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_kind: str,
) -> None:
    if source_kind == "main_only":
        path = tmp_path / "fenced-main" / "semantic.sqlite3"
        path.parent.mkdir()
        _initialize(path)
    else:
        path = _copy_live_wal_triplet(tmp_path, "fenced-wal")

    original = semantic_db._validate_live_binding_under_fence
    original_transfer = semantic_db.LiveExistingDatabaseBinding.transfer_to
    writer_started = threading.Event()
    writer_acquired = threading.Event()
    writer_finished = threading.Event()
    writer_errors: list[BaseException] = []
    threads: list[threading.Thread] = []
    observed = {"absent_while_fenced": False, "blocked_at_transfer": False}

    def writer() -> None:
        connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            writer_started.set()
            connection.execute("BEGIN IMMEDIATE")
            writer_acquired.set()
            connection.execute(
                """INSERT INTO hook_guards
                (guard_key, event_name, count, created_at, updated_at)
                VALUES ('post-validation-writer', 'fixture', 1, 'created', 'updated')"""
            )
            connection.commit()
        except BaseException as exc:  # pragma: no cover - asserted in parent thread
            writer_errors.append(exc)
        finally:
            connection.close()
            writer_finished.set()

    def validate_then_contend(connection, token) -> None:
        original(connection, token)
        thread = threading.Thread(target=writer, daemon=True)
        threads.append(thread)
        thread.start()
        assert writer_started.wait(2.0)
        assert not writer_acquired.wait(0.15)
        observed["absent_while_fenced"] = connection.execute(
            "SELECT 1 FROM hook_guards WHERE guard_key = 'post-validation-writer'"
        ).fetchone() is None

    monkeypatch.setattr(
        semantic_db,
        "_validate_live_binding_under_fence",
        validate_then_contend,
    )

    def checked_transfer(binding, owner):
        assert not writer_acquired.is_set()
        observed["blocked_at_transfer"] = True
        return original_transfer(binding, owner)

    monkeypatch.setattr(
        semantic_db.LiveExistingDatabaseBinding,
        "transfer_to",
        checked_transfer,
    )
    store = SemanticStore.open_existing(path)
    try:
        assert observed["absent_while_fenced"] is True
        assert observed["blocked_at_transfer"] is True
        assert writer_acquired.wait(2.0)
        assert writer_finished.wait(2.0)
        assert writer_errors == []
        assert store.connection.execute(
            "SELECT count FROM hook_guards WHERE guard_key = 'post-validation-writer'"
        ).fetchone()[0] == 1
    finally:
        store.close()
        for thread in threads:
            thread.join(timeout=2.0)
            assert not thread.is_alive()


def test_restart_reused_wal_ignores_aligned_stale_physical_tail(
    tmp_path: Path,
) -> None:
    path = _copy_restart_reused_wal_triplet(tmp_path)
    before = _directory_snapshot(path)

    assert validate_existing_database(path) == path.resolve()

    assert _directory_snapshot(path) == before


def test_restart_reused_wal_rejects_corrupt_logical_prefix(
    tmp_path: Path,
) -> None:
    path = _copy_restart_reused_wal_triplet(tmp_path)
    wal_path = Path(f"{path}-wal")
    wal = bytearray(wal_path.read_bytes())
    wal[32 + 24] ^= 0x01
    wal_path.write_bytes(wal)
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match="frame 1 checksum"):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


def test_restart_reused_wal_requires_shm_frame_to_be_commit_boundary(
    tmp_path: Path,
) -> None:
    path = _copy_restart_reused_wal_triplet(tmp_path)
    wal_path = Path(f"{path}-wal")
    wal = bytearray(wal_path.read_bytes())
    page_size, frame_size, _physical_frames = _wal_layout(path)
    logical_frames = _shm_max_frame(path)
    magic = int.from_bytes(wal[:4], "big")
    byteorder = "big" if magic == 0x377F0683 else "little"
    running = semantic_db._wal_checksum(wal[:24], (0, 0), byteorder)
    for frame_number in range(1, logical_frames + 1):
        offset = 32 + (frame_number - 1) * frame_size
        if frame_number == logical_frames:
            wal[offset + 4 : offset + 8] = b"\x00\x00\x00\x00"
        frame_input = bytes(wal[offset : offset + 8]) + bytes(
            wal[offset + 24 : offset + 24 + page_size]
        )
        running = semantic_db._wal_checksum(frame_input, running, byteorder)
        wal[offset + 16 : offset + 24] = struct.pack(">II", *running)
    wal_path.write_bytes(wal)
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match="commit boundary"):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


@pytest.mark.parametrize("sidecar_size", [0, 4])
def test_empty_or_junk_complete_sidecars_fail_closed(
    tmp_path: Path,
    sidecar_size: int,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    Path(f"{path}-wal").write_bytes(b"x" * sidecar_size)
    Path(f"{path}-shm").write_bytes(b"y" * sidecar_size)
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


@pytest.mark.parametrize(
    "corruption",
    ["truncated_frame", "mismatched_salt", "invalid_frame_checksum"],
)
def test_corrupt_complete_wal_triplet_fails_closed(
    tmp_path: Path,
    corruption: str,
) -> None:
    path = _copy_live_wal_triplet(tmp_path)
    wal_path = Path(f"{path}-wal")
    shm_path = Path(f"{path}-shm")
    if corruption == "truncated_frame":
        wal_path.write_bytes(wal_path.read_bytes()[:-1])
    elif corruption == "mismatched_salt":
        shm = bytearray(shm_path.read_bytes())
        # Both wal-index header copies must remain internally consistent so
        # this specifically exercises the SHM/WAL salt binding.
        shm[32] ^= 0x01
        shm[80] ^= 0x01
        shm_path.write_bytes(shm)
    elif corruption == "invalid_frame_checksum":
        wal = bytearray(wal_path.read_bytes())
        wal[32 + 24] ^= 0x01
        wal_path.write_bytes(wal)
    else:  # pragma: no cover - parameter contract
        raise AssertionError(corruption)
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


def test_delete_journal_mode_database_is_rejected_without_mutation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    connection = sqlite3.connect(path)
    assert connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0] == "delete"
    connection.close()
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match="WAL journal mode"):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


@pytest.mark.parametrize(
    "index_name",
    [
        "unique_actor_agent",
        "unique_actor_path",
        "one_open_epoch_per_actor",
        "one_active_workflow_per_actor",
    ],
)
def test_missing_required_partial_unique_index_fails_closed(
    tmp_path: Path,
    index_name: str,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    connection = sqlite3.connect(path)
    connection.execute(f"DROP INDEX {index_name}")
    connection.commit()
    connection.close()
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match=index_name):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


@pytest.mark.parametrize(
    "malformation",
    [
        "nonunique",
        "ordered_columns",
        "nocase_collation",
        "descending_column",
        "expression_column",
        "extra_key_column",
        "predicate",
    ],
)
def test_malformed_required_index_fails_closed(
    tmp_path: Path,
    malformation: str,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    connection = sqlite3.connect(path)
    connection.execute("DROP INDEX unique_actor_agent")
    if malformation == "nonunique":
        connection.execute(
            """CREATE INDEX unique_actor_agent ON actor_contexts(session_id, agent_id)
            WHERE agent_id IS NOT NULL AND agent_id <> ''"""
        )
    elif malformation == "ordered_columns":
        connection.execute(
            """CREATE UNIQUE INDEX unique_actor_agent ON actor_contexts(agent_id, session_id)
            WHERE agent_id IS NOT NULL AND agent_id <> ''"""
        )
    elif malformation == "nocase_collation":
        connection.execute(
            """CREATE UNIQUE INDEX unique_actor_agent
            ON actor_contexts(session_id COLLATE NOCASE, agent_id)
            WHERE agent_id IS NOT NULL AND agent_id <> ''"""
        )
    elif malformation == "descending_column":
        connection.execute(
            """CREATE UNIQUE INDEX unique_actor_agent
            ON actor_contexts(session_id DESC, agent_id)
            WHERE agent_id IS NOT NULL AND agent_id <> ''"""
        )
    elif malformation == "expression_column":
        connection.execute(
            """CREATE UNIQUE INDEX unique_actor_agent
            ON actor_contexts(lower(session_id), agent_id)
            WHERE agent_id IS NOT NULL AND agent_id <> ''"""
        )
    elif malformation == "extra_key_column":
        connection.execute(
            """CREATE UNIQUE INDEX unique_actor_agent
            ON actor_contexts(session_id, agent_id, scope_key)
            WHERE agent_id IS NOT NULL AND agent_id <> ''"""
        )
    elif malformation == "predicate":
        connection.execute(
            """CREATE UNIQUE INDEX unique_actor_agent ON actor_contexts(session_id, agent_id)
            WHERE agent_id IS NOT NULL"""
        )
    connection.commit()
    connection.close()
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match="unique_actor_agent"):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


def test_obsolete_session_index_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    connection = sqlite3.connect(path)
    connection.execute(
        """CREATE UNIQUE INDEX one_active_workflow_per_session
        ON workflows(session_id) WHERE state = 'ACTIVE'"""
    )
    connection.commit()
    connection.close()
    before = _directory_snapshot(path)

    with pytest.raises(SemanticDatabaseValidationError, match="obsolete index"):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


def test_required_index_predicate_preserves_state_literal_case(
    tmp_path: Path,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    connection = sqlite3.connect(path)
    connection.execute("DROP INDEX one_active_workflow_per_actor")
    connection.execute(
        """CREATE UNIQUE INDEX one_active_workflow_per_actor
        ON workflows(actor_context_id) WHERE state = 'active'"""
    )
    connection.commit()
    connection.close()
    before = _directory_snapshot(path)

    with pytest.raises(
        SemanticDatabaseValidationError,
        match="one_active_workflow_per_actor",
    ):
        validate_existing_database(path)

    assert _directory_snapshot(path) == before


def test_active_rollback_journal_fails_closed_without_new_siblings(
    tmp_path: Path,
) -> None:
    path = tmp_path / "locked.sqlite3"
    _initialize(path)
    writer = sqlite3.connect(path)
    writer.execute("PRAGMA journal_mode = DELETE")
    writer.execute("BEGIN IMMEDIATE")
    writer.execute("UPDATE schema_meta SET applied_at = 'locked-uncommitted'")
    before = _snapshot(path)
    try:
        with pytest.raises(
            SemanticDatabaseValidationError,
            match="rollback journal",
        ):
            validate_existing_database(path)
        assert _snapshot(path) == before
    finally:
        writer.rollback()
        writer.close()


def test_sidecar_selection_detects_name_change_before_source_state_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "semantic.sqlite3"
    _initialize(path)
    before = _directory_snapshot(path)
    real_directory_names = semantic_db._directory_names
    calls = 0

    def racing_directory_names(directory: Path) -> frozenset[str]:
        nonlocal calls
        calls += 1
        names = real_directory_names(directory)
        if calls == 2:
            return names | {f"{path.name}-wal", f"{path.name}-shm"}
        return names

    monkeypatch.setattr(semantic_db, "_directory_names", racing_directory_names)

    with pytest.raises(
        SemanticDatabaseValidationError,
        match="sidecar selection",
    ):
        validate_existing_database(path)

    assert calls == 2
    assert _directory_snapshot(path) == before

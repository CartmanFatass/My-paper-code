"""SQLite connection and migration helpers for the semantic MVP.

This database is a delivery and obligation ledger for the control plane.
It is not scientific truth and must not be treated as canonical project memory.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_STATE_PATH = Path("runtime/codex-semantic-mvp/state.sqlite3")
SCHEMA_VERSION = 3


class SemanticDatabaseValidationError(RuntimeError):
    """Raised when an existing file is not the exact supported semantic DB."""


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workflows (
        workflow_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        opened_turn_id TEXT NOT NULL,
        scope TEXT NOT NULL,
        objective TEXT NOT NULL,
        state TEXT NOT NULL,
        state_version INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS one_active_workflow_per_session
    ON workflows(session_id) WHERE state = 'ACTIVE'
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        workflow_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        expected_agent_type TEXT NOT NULL,
        objective TEXT NOT NULL,
        required INTEGER NOT NULL,
        agent_id TEXT,
        lifecycle TEXT NOT NULL,
        created_at TEXT NOT NULL,
        returned_at TEXT,
        PRIMARY KEY (workflow_id, task_id),
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        agent_type TEXT NOT NULL,
        raw_message TEXT NOT NULL,
        typed_json TEXT,
        schema_valid INTEGER NOT NULL,
        raw_sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(workflow_id, task_id, raw_sha256),
        FOREIGN KEY (workflow_id, task_id) REFERENCES tasks(workflow_id, task_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS obligations (
        obligation_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        owner TEXT NOT NULL,
        subject TEXT NOT NULL,
        reason TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        state TEXT NOT NULL,
        resolution_json TEXT,
        created_at TEXT NOT NULL,
        resolved_at TEXT,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intakes (
        intake_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL,
        report_id TEXT NOT NULL UNIQUE,
        intake_kind TEXT NOT NULL,
        translation_json TEXT NOT NULL,
        next_action_json TEXT,
        note TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id),
        FOREIGN KEY (report_id) REFERENCES reports(report_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        workflow_id TEXT,
        kind TEXT NOT NULL,
        subject_id TEXT,
        payload_json TEXT NOT NULL,
        dedupe_key TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS hook_guards (
        guard_key TEXT PRIMARY KEY,
        event_name TEXT NOT NULL,
        count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS closure_receipts (
        receipt_id TEXT PRIMARY KEY,
        workflow_id TEXT NOT NULL UNIQUE,
        closure_kind TEXT NOT NULL,
        summary TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
    )
    """,
)


def connect(path: str | Path = DEFAULT_STATE_PATH) -> sqlite3.Connection:
    """Open a configured SQLite connection, creating its parent directory."""
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        str(db_path), timeout=5.0, check_same_thread=False, isolation_level="DEFERRED"
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


SCHEMA_V2_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS actor_contexts (
        actor_context_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        agent_id TEXT,
        canonical_path TEXT,
        actor_kind TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        direction_id TEXT,
        parent_actor_context_id TEXT,
        counterpart_actor_context_id TEXT,
        identity_source TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_actor_agent
    ON actor_contexts(session_id, agent_id)
    WHERE agent_id IS NOT NULL AND agent_id <> ''
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_actor_path
    ON actor_contexts(session_id, canonical_path)
    WHERE canonical_path IS NOT NULL AND canonical_path <> ''
    """,
    """
    CREATE TABLE IF NOT EXISTS plan_epochs (
        epoch_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_kind TEXT NOT NULL,
        revision INTEGER NOT NULL,
        objective TEXT NOT NULL,
        authority_refs_json TEXT NOT NULL,
        frozen_invariants_json TEXT NOT NULL,
        exit_boundary TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS one_open_epoch_per_actor
    ON plan_epochs(actor_context_id)
    WHERE state = 'OPEN'
    """,
    """
    CREATE TABLE IF NOT EXISTS semantic_commits (
        semantic_commit_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_id TEXT NOT NULL,
        commit_kind TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        source_refs_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS context_checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_id TEXT,
        epoch_revision INTEGER,
        state_version INTEGER NOT NULL,
        semantic_commit_id TEXT,
        capsule_kind TEXT NOT NULL,
        capsule_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(actor_context_id, epoch_id, epoch_revision, state_version, semantic_commit_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reanchor_acks (
        ack_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        checkpoint_id TEXT NOT NULL,
        state_version INTEGER NOT NULL,
        epoch_id TEXT,
        epoch_revision INTEGER,
        actor_turn_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(actor_context_id, checkpoint_id, actor_turn_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS packet_refs (
        packet_id TEXT PRIMARY KEY,
        packet_kind TEXT NOT NULL,
        source_actor_context_id TEXT NOT NULL,
        target_actor_context_id TEXT NOT NULL,
        direction_id TEXT,
        marker TEXT NOT NULL UNIQUE,
        payload_ref TEXT NOT NULL,
        delivery_state TEXT NOT NULL,
        intake_state TEXT NOT NULL,
        decision_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
)

V2_COLUMNS = {
    "workflows": (("actor_context_id", "TEXT"),),
    "tasks": (("child_actor_context_id", "TEXT"), ("invoker_actor_context_id", "TEXT")),
    "reports": (("reporter_actor_context_id", "TEXT"),),
    "obligations": (
        ("owner_actor_context_id", "TEXT"),
        ("source_actor_context_id", "TEXT"),
    ),
    "events": (("actor_context_id", "TEXT"),),
}

SCHEMA_V3_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS promotion_proposals (
        promotion_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        epoch_id TEXT NOT NULL,
        promotion_kind TEXT NOT NULL,
        target_ref TEXT,
        summary TEXT NOT NULL,
        rationale TEXT NOT NULL,
        source_refs_json TEXT NOT NULL,
        owner_actor_context_id TEXT NOT NULL,
        state TEXT NOT NULL,
        disposition_json TEXT,
        canonical_ref TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS epoch_rollovers (
        rollover_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        from_epoch_id TEXT NOT NULL,
        from_epoch_revision INTEGER NOT NULL,
        next_epoch_kind TEXT NOT NULL,
        next_objective TEXT NOT NULL,
        carry_obligation_ids_json TEXT NOT NULL,
        carry_packet_ids_json TEXT NOT NULL,
        carry_frontier_json TEXT NOT NULL,
        promotion_ids_json TEXT NOT NULL,
        forgotten_refs_json TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        applied_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS context_retention_marks (
        retention_mark_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        object_kind TEXT NOT NULL,
        object_id TEXT NOT NULL,
        retention_class TEXT NOT NULL,
        active_in_working_set INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL,
        archived_at TEXT,
        UNIQUE(actor_context_id, object_kind, object_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS context_gc_runs (
        gc_run_id TEXT PRIMARY KEY,
        actor_context_id TEXT,
        mode TEXT NOT NULL,
        plan_json TEXT NOT NULL,
        applied INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_authority_grants (
        grant_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL,
        operation TEXT NOT NULL,
        created_at TEXT NOT NULL,
        consumed_at TEXT
    )
    """,
)

V3_COLUMNS = {
    "plan_epochs": (
        ("navigation_refs_json", "TEXT"),
        ("procedure_refs_json", "TEXT"),
        ("carry_frontier_json", "TEXT"),
    ),
    "promotion_proposals": (
        ("writer_actor_context_id", "TEXT"),
        ("carried_to_epoch_id", "TEXT"),
    ),
    "epoch_rollovers": (("to_epoch_id", "TEXT"),),
}


# Opening a host-bound semantic database is deliberately stricter than the
# administrative ``initialize_database`` path.  These are the complete table
# columns produced by schema v3; additional future columns are harmless to a
# v3 reader, but every named column must be present before the host may write.
REQUIRED_SCHEMA_V3_COLUMNS = {
    "schema_meta": frozenset({"version", "applied_at"}),
    "workflows": frozenset(
        {
            "workflow_id", "session_id", "opened_turn_id", "scope", "objective",
            "state", "state_version", "created_at", "updated_at", "actor_context_id",
        }
    ),
    "tasks": frozenset(
        {
            "workflow_id", "task_id", "expected_agent_type", "objective", "required",
            "agent_id", "lifecycle", "created_at", "returned_at",
            "child_actor_context_id", "invoker_actor_context_id",
        }
    ),
    "reports": frozenset(
        {
            "report_id", "workflow_id", "task_id", "agent_id", "agent_type",
            "raw_message", "typed_json", "schema_valid", "raw_sha256", "created_at",
            "reporter_actor_context_id",
        }
    ),
    "obligations": frozenset(
        {
            "obligation_id", "workflow_id", "kind", "owner", "subject", "reason",
            "source_ref", "state", "resolution_json", "created_at", "resolved_at",
            "owner_actor_context_id", "source_actor_context_id",
        }
    ),
    "intakes": frozenset(
        {
            "intake_id", "workflow_id", "report_id", "intake_kind", "translation_json",
            "next_action_json", "note", "created_at",
        }
    ),
    "events": frozenset(
        {
            "seq", "event_id", "workflow_id", "kind", "subject_id", "payload_json",
            "dedupe_key", "created_at", "actor_context_id",
        }
    ),
    "hook_guards": frozenset(
        {"guard_key", "event_name", "count", "created_at", "updated_at"}
    ),
    "closure_receipts": frozenset(
        {"receipt_id", "workflow_id", "closure_kind", "summary", "created_at"}
    ),
    "actor_contexts": frozenset(
        {
            "actor_context_id", "session_id", "agent_id", "canonical_path", "actor_kind",
            "scope_key", "direction_id", "parent_actor_context_id",
            "counterpart_actor_context_id", "identity_source", "state", "created_at",
            "updated_at",
        }
    ),
    "plan_epochs": frozenset(
        {
            "epoch_id", "actor_context_id", "epoch_kind", "revision", "objective",
            "authority_refs_json", "frozen_invariants_json", "exit_boundary", "state",
            "created_at", "updated_at", "navigation_refs_json", "procedure_refs_json",
            "carry_frontier_json",
        }
    ),
    "semantic_commits": frozenset(
        {
            "semantic_commit_id", "actor_context_id", "epoch_id", "commit_kind",
            "payload_json", "source_refs_json", "created_at",
        }
    ),
    "context_checkpoints": frozenset(
        {
            "checkpoint_id", "actor_context_id", "epoch_id", "epoch_revision",
            "state_version", "semantic_commit_id", "capsule_kind", "capsule_json",
            "created_at",
        }
    ),
    "reanchor_acks": frozenset(
        {
            "ack_id", "actor_context_id", "checkpoint_id", "state_version", "epoch_id",
            "epoch_revision", "actor_turn_id", "created_at",
        }
    ),
    "packet_refs": frozenset(
        {
            "packet_id", "packet_kind", "source_actor_context_id",
            "target_actor_context_id", "direction_id", "marker", "payload_ref",
            "delivery_state", "intake_state", "decision_ref", "created_at", "updated_at",
        }
    ),
    "promotion_proposals": frozenset(
        {
            "promotion_id", "actor_context_id", "epoch_id", "promotion_kind", "target_ref",
            "summary", "rationale", "source_refs_json", "owner_actor_context_id", "state",
            "disposition_json", "canonical_ref", "created_at", "updated_at",
            "writer_actor_context_id", "carried_to_epoch_id",
        }
    ),
    "epoch_rollovers": frozenset(
        {
            "rollover_id", "actor_context_id", "from_epoch_id", "from_epoch_revision",
            "next_epoch_kind", "next_objective", "carry_obligation_ids_json",
            "carry_packet_ids_json", "carry_frontier_json", "promotion_ids_json",
            "forgotten_refs_json", "state", "created_at", "applied_at", "to_epoch_id",
        }
    ),
    "context_retention_marks": frozenset(
        {
            "retention_mark_id", "actor_context_id", "object_kind", "object_id",
            "retention_class", "active_in_working_set", "reason", "created_at", "archived_at",
        }
    ),
    "context_gc_runs": frozenset(
        {"gc_run_id", "actor_context_id", "mode", "plan_json", "applied", "created_at"}
    ),
    "user_authority_grants": frozenset(
        {"grant_id", "actor_context_id", "operation", "created_at", "consumed_at"}
    ),
}


REQUIRED_SCHEMA_V3_INDEXES = {
    "unique_actor_agent": (
        "actor_contexts",
        ("session_id", "agent_id"),
        "agent_id is not null and agent_id <> ''",
    ),
    "unique_actor_path": (
        "actor_contexts",
        ("session_id", "canonical_path"),
        "canonical_path is not null and canonical_path <> ''",
    ),
    "one_open_epoch_per_actor": (
        "plan_epochs",
        ("actor_context_id",),
        "state = 'OPEN'",
    ),
    "one_active_workflow_per_actor": (
        "workflows",
        ("actor_context_id",),
        "state = 'ACTIVE'",
    ),
}

_OBSOLETE_SCHEMA_V3_INDEXES = frozenset({"one_active_workflow_per_session"})
_SQLITE_WAL_MAGIC = frozenset({0x377F0682, 0x377F0683})
_SQLITE_WAL_VERSION = 3007000
_SQLITE_SHM_REGION_SIZE = 32768
_COPY_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class _SourceFileState:
    """Bounded identity and content record for one validation input file."""

    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(_COPY_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _source_file_state(path: Path) -> _SourceFileState:
    try:
        stat = path.stat(follow_symlinks=False)
        if not path.is_file() or path.is_symlink():
            raise OSError("not a regular non-symbolic-link file")
        digest = _sha256_file(path)
        final = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise SemanticDatabaseValidationError(
            f"semantic database validation input is not a stable regular file: {path.name}"
        ) from exc
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    final_identity = (
        final.st_dev,
        final.st_ino,
        final.st_size,
        final.st_mtime_ns,
        final.st_ctime_ns,
    )
    if identity != final_identity:
        raise SemanticDatabaseValidationError(
            f"semantic database validation input changed while hashing: {path.name}"
        )
    return _SourceFileState(*identity, digest)


def _copy_snapshot_file(source: Path, destination: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        while chunk := input_file.read(_COPY_CHUNK_SIZE):
            digest.update(chunk)
            output_file.write(chunk)
        output_file.flush()
        os.fsync(output_file.fileno())
    return digest.hexdigest()


def _directory_names(directory: Path) -> frozenset[str]:
    """Capture one directory-name snapshot or fail closed on enumeration errors."""

    try:
        return frozenset(item.name for item in directory.iterdir())
    except OSError as exc:
        raise SemanticDatabaseValidationError(
            "semantic database sibling set cannot be read stably"
        ) from exc


def _normalized_predicate(sql: str) -> str:
    match = re.search(r"\bwhere\b(.*)$", sql, flags=re.IGNORECASE | re.DOTALL)
    if match is None:
        return ""
    predicate = re.sub(r"\s+", " ", match.group(1).strip())
    normalized: list[str] = []
    literal = False
    offset = 0
    while offset < len(predicate):
        character = predicate[offset]
        if character == "'":
            normalized.append(character)
            if literal and offset + 1 < len(predicate) and predicate[offset + 1] == "'":
                normalized.append("'")
                offset += 2
                continue
            literal = not literal
        else:
            normalized.append(character if literal else character.casefold())
        offset += 1
    predicate = "".join(normalized)
    while predicate.startswith("(") and predicate.endswith(")"):
        predicate = predicate[1:-1].strip()
    return predicate


def _validate_required_indexes(connection: sqlite3.Connection) -> None:
    obsolete = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?",
        (next(iter(_OBSOLETE_SCHEMA_V3_INDEXES)),),
    ).fetchone()
    if obsolete is not None:
        raise SemanticDatabaseValidationError(
            "semantic database contains obsolete index one_active_workflow_per_session"
        )

    for index_name, (table, required_columns, predicate) in REQUIRED_SCHEMA_V3_INDEXES.items():
        rows = connection.execute(f"PRAGMA index_list({table})").fetchall()
        metadata = next((row for row in rows if str(row[1]) == index_name), None)
        if metadata is None:
            raise SemanticDatabaseValidationError(
                f"semantic database is missing required index {index_name}"
            )
        # PRAGMA index_list: seq, name, unique, origin, partial.
        if int(metadata[2]) != 1 or len(metadata) < 5 or int(metadata[4]) != 1:
            raise SemanticDatabaseValidationError(
                f"semantic database index {index_name} must be unique and partial"
            )
        # ``index_info`` omits ordering, collation, expressions, and the key
        # marker.  A same-named index with NOCASE/DESC/expression semantics
        # must not be accepted as the host's authority index.
        key_rows = tuple(
            row
            for row in connection.execute(f"PRAGMA index_xinfo({index_name})")
            if len(row) >= 6 and int(row[5]) == 1
        )
        expected_key_rows = tuple(
            (offset, column, "BINARY", 0, 1)
            for offset, column in enumerate(required_columns)
        )
        actual_key_rows = tuple(
            (
                int(row[0]),
                None if row[2] is None else str(row[2]),
                str(row[4]),
                int(row[3]),
                int(row[5]),
            )
            for row in key_rows
        )
        if actual_key_rows != expected_key_rows:
            raise SemanticDatabaseValidationError(
                f"semantic database index {index_name} has incompatible key columns"
            )
        master = connection.execute(
            "SELECT tbl_name, sql FROM sqlite_master WHERE type = 'index' AND name = ?",
            (index_name,),
        ).fetchone()
        if (
            master is None
            or str(master[0]) != table
            or master[1] is None
            or _normalized_predicate(str(master[1])) != predicate
        ):
            raise SemanticDatabaseValidationError(
                f"semantic database index {index_name} has an incompatible predicate"
            )


def _wal_checksum(data: bytes, checksum: tuple[int, int], byteorder: str) -> tuple[int, int]:
    if len(data) % 8:
        raise SemanticDatabaseValidationError("semantic WAL checksum input is misaligned")
    first, second = checksum
    for offset in range(0, len(data), 8):
        word0 = int.from_bytes(data[offset : offset + 4], byteorder)
        word1 = int.from_bytes(data[offset + 4 : offset + 8], byteorder)
        first = (first + word0 + second) & 0xFFFFFFFF
        second = (second + word1 + first) & 0xFFFFFFFF
    return first, second


def _database_page_size(main_bytes: bytes) -> int:
    if len(main_bytes) < 100 or main_bytes[:16] != b"SQLite format 3\x00":
        raise SemanticDatabaseValidationError("semantic database has an invalid SQLite header")
    raw_page_size = int.from_bytes(main_bytes[16:18], "big")
    page_size = 65536 if raw_page_size == 1 else raw_page_size
    if page_size < 512 or page_size > 65536 or page_size & (page_size - 1):
        raise SemanticDatabaseValidationError("semantic database has an invalid page size")
    if main_bytes[18:20] != b"\x02\x02":
        raise SemanticDatabaseValidationError(
            "semantic database is not persistently configured for WAL journal mode"
        )
    return page_size


def _validate_wal_header(path: Path, database_page_size: int) -> dict[str, object]:
    """Validate the fixed WAL header and aligned physical frame capacity."""

    wal_size = path.stat().st_size
    if wal_size < 32:
        raise SemanticDatabaseValidationError("semantic WAL sidecar is empty or truncated")
    with path.open("rb") as wal_file:
        wal_header = wal_file.read(32)
    magic, version, raw_page_size = struct.unpack(">III", wal_header[:12])
    if magic not in _SQLITE_WAL_MAGIC or version != _SQLITE_WAL_VERSION:
        raise SemanticDatabaseValidationError("semantic WAL header is invalid")
    page_size = 65536 if raw_page_size == 1 else raw_page_size
    if page_size != database_page_size:
        raise SemanticDatabaseValidationError("semantic WAL page size does not match the database")
    frame_size = 24 + page_size
    if (wal_size - 32) % frame_size:
        raise SemanticDatabaseValidationError("semantic WAL has a truncated frame")
    physical_frame_count = (wal_size - 32) // frame_size
    if physical_frame_count == 0:
        raise SemanticDatabaseValidationError("semantic WAL has no complete frames")

    checksum_order = "big" if magic == 0x377F0683 else "little"
    expected_header = tuple(struct.unpack(">II", wal_header[24:32]))
    running = _wal_checksum(wal_header[:24], (0, 0), checksum_order)
    if running != expected_header:
        raise SemanticDatabaseValidationError("semantic WAL header checksum is invalid")

    return {
        "magic": magic,
        "page_size": page_size,
        "salts": tuple(struct.unpack(">II", wal_header[16:24])),
        "physical_frame_count": physical_frame_count,
        "header_checksum": expected_header,
        "checksum_order": checksum_order,
    }


def _validate_wal_file(
    path: Path,
    wal_header: dict[str, object],
    shm_info: dict[str, object],
) -> None:
    """Validate only the SHM-authoritative logical WAL prefix.

    SQLite RESTART checkpoints reuse frame one without truncating the WAL.
    Aligned frames after ``mxFrame`` are therefore physical capacity, not part
    of the current logical WAL, and may retain salts from the prior generation.
    """

    page_size = int(wal_header["page_size"])
    logical_frame_count = int(shm_info["max_frame"])
    if logical_frame_count <= 0:
        raise SemanticDatabaseValidationError("semantic SHM has no committed WAL frames")
    if int(wal_header["physical_frame_count"]) < logical_frame_count:
        raise SemanticDatabaseValidationError(
            "semantic WAL is truncated before the SHM frame boundary"
        )

    salts = wal_header["salts"]
    checksum_order = str(wal_header["checksum_order"])
    running = wal_header["header_checksum"]
    with path.open("rb") as wal_file:
        wal_file.seek(32)
        for frame_number in range(1, logical_frame_count + 1):
            header = wal_file.read(24)
            page = wal_file.read(page_size)
            if len(header) != 24 or len(page) != page_size:
                raise SemanticDatabaseValidationError("semantic WAL has a truncated frame")
            page_number, database_size, salt1, salt2 = struct.unpack(">IIII", header[:16])
            if page_number == 0 or (salt1, salt2) != salts:
                raise SemanticDatabaseValidationError(
                    f"semantic WAL frame {frame_number} has invalid page or salts"
                )
            running = _wal_checksum(header[:8] + page, running, checksum_order)
            stored = tuple(struct.unpack(">II", header[16:24]))
            if running != stored:
                raise SemanticDatabaseValidationError(
                    f"semantic WAL frame {frame_number} checksum is invalid"
                )
            if frame_number == logical_frame_count:
                if database_size == 0:
                    raise SemanticDatabaseValidationError(
                        "semantic WAL SHM frame boundary is not a commit boundary"
                    )
                if database_size != int(shm_info["database_pages"]):
                    raise SemanticDatabaseValidationError(
                        "semantic SHM database size does not match its WAL commit"
                    )
                if stored != shm_info["frame_checksum"]:
                    raise SemanticDatabaseValidationError(
                        "semantic SHM frame checksum does not match its WAL commit"
                    )


def _validate_shm_file(
    path: Path,
    wal_header: dict[str, object],
) -> dict[str, object]:
    shm_size = path.stat().st_size
    if shm_size < _SQLITE_SHM_REGION_SIZE or shm_size % _SQLITE_SHM_REGION_SIZE:
        raise SemanticDatabaseValidationError("semantic SHM sidecar has invalid sizing")
    with path.open("rb") as shm_file:
        header0 = shm_file.read(48)
        header1 = shm_file.read(48)
    if header0 != header1:
        raise SemanticDatabaseValidationError("semantic SHM header copies do not match")

    parsed: tuple[str, tuple[int, ...]] | None = None
    for byteorder, prefix in (("little", "<"), ("big", ">")):
        # The wal-index header's scalar fields and checksums use host byte
        # order.  Salts are copied from the WAL as opaque bytes and decoded
        # separately below.
        values = struct.unpack(f"{prefix}III BBH II", header0[:24])
        if values[0] == _SQLITE_WAL_VERSION:
            parsed = (byteorder, values)
            break
    if parsed is None:
        raise SemanticDatabaseValidationError("semantic SHM header version is invalid")
    byteorder, values = parsed
    (
        _version,
        _unused,
        _change,
        initialized,
        big_endian_checksum,
        raw_page_size,
        max_frame,
        database_pages,
    ) = values
    checksum_prefix = "<" if byteorder == "little" else ">"
    frame_checksum1, frame_checksum2 = struct.unpack(
        f"{checksum_prefix}II", header0[24:32]
    )
    # Salts are copied byte-for-byte from the big-endian WAL header.
    salt1, salt2 = struct.unpack(">II", header0[32:40])
    header_checksum1, header_checksum2 = struct.unpack(
        f"{checksum_prefix}II", header0[40:48]
    )
    page_size = 65536 if raw_page_size == 1 else raw_page_size
    if initialized != 1 or page_size != wal_header["page_size"]:
        raise SemanticDatabaseValidationError("semantic SHM header is not initialized for this database")
    expected_big_endian = 1 if wal_header["magic"] == 0x377F0683 else 0
    if big_endian_checksum != expected_big_endian:
        raise SemanticDatabaseValidationError("semantic SHM checksum byte order mismatches WAL")
    if (salt1, salt2) != wal_header["salts"]:
        raise SemanticDatabaseValidationError("semantic SHM salts do not match WAL")
    required_regions = 1
    if max_frame > 4062:
        required_regions += (max_frame - 4062 + 4095) // 4096
    if shm_size < required_regions * _SQLITE_SHM_REGION_SIZE:
        raise SemanticDatabaseValidationError("semantic SHM sidecar is truncated for its WAL")
    calculated = _wal_checksum(header0[:40], (0, 0), byteorder)
    if calculated != (header_checksum1, header_checksum2):
        raise SemanticDatabaseValidationError("semantic SHM header checksum is invalid")
    return {
        "max_frame": max_frame,
        "database_pages": database_pages,
        "frame_checksum": (frame_checksum1, frame_checksum2),
    }


def _validate_schema_v3_connection(connection: sqlite3.Connection) -> None:
    check = connection.execute("PRAGMA quick_check(1)").fetchone()
    if check is None or str(check[0]).lower() != "ok":
        detail = "no result" if check is None else str(check[0])
        raise SemanticDatabaseValidationError(
            f"semantic database integrity check failed: {detail}"
        )

    tables = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing_tables = sorted(set(REQUIRED_SCHEMA_V3_COLUMNS) - tables)
    if missing_tables:
        raise SemanticDatabaseValidationError(
            "semantic database is missing required tables: " + ", ".join(missing_tables)
        )

    for table, required_columns in REQUIRED_SCHEMA_V3_COLUMNS.items():
        actual_columns = _column_names(connection, table)
        missing_columns = sorted(required_columns - actual_columns)
        if missing_columns:
            raise SemanticDatabaseValidationError(
                f"semantic database table {table!r} is missing required columns: "
                + ", ".join(missing_columns)
            )

    versions = connection.execute(
        "SELECT version FROM schema_meta ORDER BY version"
    ).fetchall()
    if not versions:
        raise SemanticDatabaseValidationError("semantic database has no schema version")
    try:
        current = max(int(row[0]) for row in versions)
    except (TypeError, ValueError) as exc:
        raise SemanticDatabaseValidationError(
            "semantic database schema version is not an integer"
        ) from exc
    if current != SCHEMA_VERSION:
        raise SemanticDatabaseValidationError(
            f"semantic database schema version {current} is incompatible; "
            f"required exactly {SCHEMA_VERSION}"
        )
    _validate_required_indexes(connection)


def validate_existing_database(path: str | Path) -> Path:
    """Validate one existing schema-v3 database without opening its files in SQLite.

    SQLite is allowed to recover or rebuild sidecars only inside a private
    snapshot.  Repeated identity and digest checks bind that snapshot to one
    stable main/WAL/SHM source set and fail closed when a writer races it.
    """

    try:
        resolved = Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SemanticDatabaseValidationError(
            "semantic database must be an existing regular file"
        ) from exc
    if not resolved.is_file():
        raise SemanticDatabaseValidationError(
            "semantic database must be an existing regular file"
        )

    # Select every possible SQLite sidecar from one stable directory snapshot.
    # A journal or WAL pair appearing after this capture is detected by the
    # immediate recheck before any source is opened or copied.
    initial_names = _directory_names(resolved.parent)
    wal_path = Path(f"{resolved}-wal")
    shm_path = Path(f"{resolved}-shm")
    journal_path = Path(f"{resolved}-journal")
    if journal_path.name in initial_names:
        raise SemanticDatabaseValidationError(
            "semantic database has an active or incomplete rollback journal"
        )
    wal_exists = wal_path.name in initial_names
    shm_exists = shm_path.name in initial_names
    if wal_exists != shm_exists:
        raise SemanticDatabaseValidationError(
            "semantic database has an incomplete WAL sidecar set"
        )

    source_paths = (resolved, wal_path, shm_path) if wal_exists else (resolved,)
    if _directory_names(resolved.parent) != initial_names:
        raise SemanticDatabaseValidationError(
            "semantic database sibling set changed during sidecar selection"
        )
    initial_states = {source: _source_file_state(source) for source in source_paths}

    with tempfile.TemporaryDirectory(prefix="hmasd-semantic-validation-") as temp_name:
        snapshot_dir = Path(temp_name)
        snapshot_main = snapshot_dir / "semantic.sqlite3"
        snapshot_paths = {
            resolved: snapshot_main,
            wal_path: Path(f"{snapshot_main}-wal"),
            shm_path: Path(f"{snapshot_main}-shm"),
        }
        copied_hashes = {
            source: _copy_snapshot_file(source, snapshot_paths[source])
            for source in source_paths
        }
        final_states = {source: _source_file_state(source) for source in source_paths}
        final_names = _directory_names(resolved.parent)
        if initial_names != final_names:
            raise SemanticDatabaseValidationError(
                "semantic database sibling set changed during validation"
            )
        for source in source_paths:
            if (
                initial_states[source] != final_states[source]
                or copied_hashes[source] != initial_states[source].sha256
            ):
                raise SemanticDatabaseValidationError(
                    f"semantic database input changed during snapshot: {source.name}"
                )

        with snapshot_main.open("rb") as snapshot_file:
            database_page_size = _database_page_size(snapshot_file.read(100))
        if initial_states[resolved].size < database_page_size or (
            initial_states[resolved].size % database_page_size
        ):
            raise SemanticDatabaseValidationError(
                "semantic database file size is not page aligned"
            )
        if wal_exists:
            wal_header = _validate_wal_header(
                snapshot_paths[wal_path], database_page_size
            )
            shm_info = _validate_shm_file(snapshot_paths[shm_path], wal_header)
            _validate_wal_file(snapshot_paths[wal_path], wal_header, shm_info)

        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                f"{snapshot_main.as_uri()}?mode=ro",
                uri=True,
                timeout=0.0,
                check_same_thread=False,
                isolation_level=None,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only = ON")
            connection.execute("PRAGMA busy_timeout = 0")
            journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            if journal_mode != "wal":
                raise SemanticDatabaseValidationError(
                    "semantic database is not persistently configured for WAL journal mode"
                )
            _validate_schema_v3_connection(connection)
        except SemanticDatabaseValidationError:
            raise
        except sqlite3.Error as exc:
            raise SemanticDatabaseValidationError(
                f"semantic database cannot be read safely: {exc}"
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    # The validation itself can be long for a large ledger.  Recheck the exact
    # source inputs after SQLite has finished with the private snapshot so a
    # concurrent source mutation cannot turn a stale success into authority.
    ending_names = _directory_names(resolved.parent)
    ending_states = {source: _source_file_state(source) for source in source_paths}
    if ending_names != initial_names or ending_states != initial_states:
        raise SemanticDatabaseValidationError(
            "semantic database changed before validation completed"
        )
    return resolved


def connect_existing(path: str | Path) -> sqlite3.Connection:
    """Open an existing database read/write without initialization or migration."""

    resolved = Path(path).resolve(strict=True)
    connection = sqlite3.connect(
        f"{resolved.as_uri()}?mode=rw",
        uri=True,
        timeout=5.0,
        check_same_thread=False,
        isolation_level="DEFERRED",
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


def _apply_schema_v1(connection: sqlite3.Connection) -> None:
    """Create or repair the version-1 schema, without dropping user data."""
    has_actor_index = connection.execute(
        """SELECT 1 FROM sqlite_master
        WHERE type = 'index' AND name = 'one_active_workflow_per_actor'"""
    ).fetchone()
    for statement in SCHEMA_STATEMENTS[1:]:
        if has_actor_index and "one_active_workflow_per_session" in statement:
            continue
        connection.execute(statement)


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table})")
    }


def migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
    """Add actor-scoped objects without rewriting historical payload bytes."""
    from datetime import datetime, timezone
    import uuid

    for statement in SCHEMA_V2_TABLES:
        connection.execute(statement)
    for table, columns in V2_COLUMNS.items():
        existing = _column_names(connection, table)
        for name, decl in columns:
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    now = datetime.now(timezone.utc).isoformat()
    sessions = connection.execute(
        "SELECT DISTINCT session_id FROM workflows ORDER BY session_id"
    ).fetchall()
    for (session_id,) in sessions:
        if not session_id:
            continue
        existing_actor = connection.execute(
            """SELECT actor_context_id FROM actor_contexts
            WHERE session_id = ? AND actor_kind = 'SESSION_ROOT_UNCLASSIFIED'""",
            (session_id,),
        ).fetchone()
        if existing_actor is None:
            actor_id = f"actor_{uuid.uuid4().hex}"
            connection.execute(
                """INSERT INTO actor_contexts (
                    actor_context_id, session_id, agent_id, canonical_path, actor_kind,
                    scope_key, direction_id, parent_actor_context_id,
                    counterpart_actor_context_id, identity_source, state,
                    created_at, updated_at
                ) VALUES (?, ?, NULL, NULL, 'SESSION_ROOT_UNCLASSIFIED', ?, NULL, NULL, NULL,
                          'MIGRATION_V1', 'ACTIVE', ?, ?)""",
                (actor_id, session_id, f"session:{session_id}", now, now),
            )
        else:
            actor_id = existing_actor[0]
        connection.execute(
            """UPDATE workflows SET actor_context_id = ?
            WHERE session_id = ? AND (actor_context_id IS NULL OR actor_context_id = '')""",
            (actor_id, session_id),
        )
        connection.execute(
            """UPDATE obligations SET owner_actor_context_id = (
                SELECT actor_context_id FROM workflows
                WHERE workflows.workflow_id = obligations.workflow_id
            )
            WHERE owner_actor_context_id IS NULL OR owner_actor_context_id = ''""",
        )

    connection.execute("DROP INDEX IF EXISTS one_active_workflow_per_session")
    connection.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS one_active_workflow_per_actor
        ON workflows(actor_context_id)
        WHERE state = 'ACTIVE'"""
    )


def migrate_v2_to_v3(connection: sqlite3.Connection) -> None:
    """Add promotion, rollover, and retention objects without deleting rows."""
    for statement in SCHEMA_V3_TABLES:
        connection.execute(statement)
    for table, columns in V3_COLUMNS.items():
        existing = _column_names(connection, table)
        for name, decl in columns:
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    connection.execute(
        "UPDATE plan_epochs SET navigation_refs_json = '[]' WHERE navigation_refs_json IS NULL"
    )
    connection.execute(
        "UPDATE plan_epochs SET procedure_refs_json = '[]' WHERE procedure_refs_json IS NULL"
    )
    connection.execute(
        "UPDATE plan_epochs SET carry_frontier_json = '{}' WHERE carry_frontier_json IS NULL"
    )


def initialize_database(connection: sqlite3.Connection) -> None:
    """Apply the idempotent, versioned MVP schema in one transaction."""
    from datetime import datetime, timezone

    applied_at = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute(SCHEMA_STATEMENTS[0])
        current = connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0]
        current = int(current or 0)
        if current > SCHEMA_VERSION:
            raise RuntimeError(
                f"database schema version {current} is newer than supported {SCHEMA_VERSION}"
            )
        # Version 0 is the pre-migration marker used by the first draft.  The
        # migration only creates missing objects and never drops or rewrites
        # existing rows, so reopening an interrupted/partial database is safe.
        _apply_schema_v1(connection)
        if current < 2:
            migrate_v1_to_v2(connection)
        # v3 object/column adds are idempotent and must run on already-v3
        # ledgers when later additive columns are introduced.
        migrate_v2_to_v3(connection)
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_meta(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, applied_at),
            )

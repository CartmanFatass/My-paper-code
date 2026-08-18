"""Read-only scan of the semantic ledger into supervisor mailbox rows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools.codex_semantic_mvp.models import ObligationKind, normalize_obligation_kind

from .mailbox_models import MailboxMessageKind, MailboxSourceSystem, SCANNER_ID
from .mailbox_store import MailboxStore
from .semantic_bridge import SemanticBridge

OBLIGATION_KIND_MAP = {
    ObligationKind.CONTEXT_REANCHOR_REQUIRED.value: MailboxMessageKind.REANCHOR_REQUIRED,
    ObligationKind.REPORT_INTAKE_REQUIRED.value: MailboxMessageKind.REPORT_AVAILABLE,
    ObligationKind.PACKET_INTAKE_REQUIRED.value: MailboxMessageKind.PACKET_AVAILABLE,
    ObligationKind.PORTFOLIO_REVIEW_REQUIRED.value: MailboxMessageKind.OBLIGATION_AVAILABLE,
}


class SemanticScanner:
    def __init__(self, mailbox: MailboxStore, bridge: SemanticBridge) -> None:
        self.mailbox = mailbox
        self.bridge = bridge

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _cursor(self) -> dict[str, Any]:
        row = self.mailbox.store.connection.execute(
            "SELECT * FROM semantic_scan_cursors WHERE scanner_id = ?",
            (SCANNER_ID,),
        ).fetchone()
        return dict(row) if row is not None else {}

    def _write_cursor(self, **fields: Any) -> None:
        now = self._now()
        existing = self._cursor()
        payload = {
            "last_scan_at": existing.get("last_scan_at"),
            "last_obligation_observed_at": existing.get("last_obligation_observed_at"),
            "last_packet_observed_at": existing.get("last_packet_observed_at"),
            "last_report_observed_at": existing.get("last_report_observed_at"),
        }
        payload.update(fields)
        with self.mailbox.store._lock, self.mailbox.store.connection:
            self.mailbox.store.connection.execute(
                """INSERT INTO semantic_scan_cursors (
                    scanner_id, last_scan_at, last_obligation_observed_at,
                    last_packet_observed_at, last_report_observed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scanner_id) DO UPDATE SET
                    last_scan_at=excluded.last_scan_at,
                    last_obligation_observed_at=excluded.last_obligation_observed_at,
                    last_packet_observed_at=excluded.last_packet_observed_at,
                    last_report_observed_at=excluded.last_report_observed_at,
                    updated_at=excluded.updated_at""",
                (
                    SCANNER_ID,
                    payload["last_scan_at"],
                    payload["last_obligation_observed_at"],
                    payload["last_packet_observed_at"],
                    payload["last_report_observed_at"],
                    now,
                ),
            )

    def scan(self) -> list[str]:
        created: list[str] = []
        last_obligation = None
        last_packet = None
        last_report = None
        obligation_rows = self.bridge.semantic.connection.execute(
            """SELECT obligation_id, kind, owner, subject, source_ref, state,
                      created_at, owner_actor_context_id
               FROM obligations WHERE state = 'OPEN'"""
        ).fetchall()
        for row in obligation_rows:
            target = str(row["owner_actor_context_id"] or row["owner"] or "")
            if not target:
                continue
            kind = normalize_obligation_kind(str(row["kind"]))
            message_kind = OBLIGATION_KIND_MAP.get(kind, MailboxMessageKind.OBLIGATION_AVAILABLE)
            key = f"semantic:obligation:{row['obligation_id']}:OPEN"
            message = self.mailbox.enqueue(
                source_system=MailboxSourceSystem.SEMANTIC_LEDGER.value,
                source_event_key=key,
                target_actor_context_id=target,
                message_kind=message_kind,
                subject_ref=str(row["subject"]),
                payload_ref=str(row["obligation_id"]),
                priority=10 if message_kind is MailboxMessageKind.REANCHOR_REQUIRED else 5,
            )
            created.append(message.message_id)
            last_obligation = str(row["created_at"])
            if kind == ObligationKind.REPORT_INTAKE_REQUIRED.value:
                last_report = str(row["created_at"])
        packet_rows = self.bridge.semantic.connection.execute(
            """SELECT packet_id, packet_kind, target_actor_context_id, payload_ref,
                      delivery_state, intake_state, created_at, direction_id
               FROM packet_refs WHERE intake_state != 'APPLIED'"""
        ).fetchall()
        for row in packet_rows:
            key = (
                f"semantic:packet:{row['packet_id']}:"
                f"{row['delivery_state']}:{row['intake_state']}"
            )
            message = self.mailbox.enqueue(
                source_system=MailboxSourceSystem.SEMANTIC_LEDGER.value,
                source_event_key=key,
                target_actor_context_id=str(row["target_actor_context_id"]),
                message_kind=MailboxMessageKind.PACKET_AVAILABLE,
                subject_ref=str(row["packet_id"]),
                payload_ref=str(row["payload_ref"]),
                direction_id=None if row["direction_id"] is None else str(row["direction_id"]),
                priority=7,
            )
            created.append(message.message_id)
            last_packet = str(row["created_at"])
        self._write_cursor(
            last_scan_at=self._now(),
            last_obligation_observed_at=last_obligation,
            last_packet_observed_at=last_packet,
            last_report_observed_at=last_report,
        )
        return created

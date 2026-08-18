"""Register a typed packet reference from a bound managed actor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.codex_semantic_mvp.packet_refs import packet_register

from .binding_store import BindingStore
from .mailbox_acl import MailboxAclError, evaluate_automatic_delivery
from .mailbox_models import MailboxMessageKind, MailboxSourceSystem
from .managed_models import BindingState, ManagedActorKind
from .semantic_bridge import SemanticBridge

TARGET_ALIASES = {
    "PORTFOLIO": ManagedActorKind.PORTFOLIO,
    "OPERATIONAL_ROOT": ManagedActorKind.OPERATIONAL_ROOT,
}

ALLOWED_PACKET_KINDS = {
    MailboxMessageKind.ROOT_TO_PORTFOLIO_REVIEW.value,
    MailboxMessageKind.PORTFOLIO_TO_ROOT_DECISION.value,
    MailboxMessageKind.ROOT_TO_PORTFOLIO_APPLIED_ACK.value,
}


class ManagedPacketSendError(ValueError):
    """Raised when a managed packet send cannot be registered."""


def resolve_payload_ref(repo_root: Path, payload_ref: str, *, existing_packet_ids: set[str]) -> str:
    if not payload_ref or payload_ref != payload_ref.strip():
        raise ManagedPacketSendError("payload_ref is empty")
    if payload_ref in existing_packet_ids:
        return payload_ref
    candidate = Path(payload_ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ManagedPacketSendError("payload_ref must be repository-relative")
    resolved = (Path(repo_root) / candidate).resolve()
    root = Path(repo_root).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ManagedPacketSendError("payload_ref escapes the repository") from exc
    if not resolved.is_file():
        raise ManagedPacketSendError("payload_ref is not an existing file or packet id")
    return payload_ref.replace("\\", "/")


class ManagedPacketSender:
    def __init__(self, bindings: BindingStore, bridge: SemanticBridge, repo_root: Path) -> None:
        self.bindings = bindings
        self.bridge = bridge
        self.repo_root = Path(repo_root)

    def _existing_packet_ids(self) -> set[str]:
        rows = self.bridge.semantic.connection.execute("SELECT packet_id FROM packet_refs").fetchall()
        return {str(row[0]) for row in rows}

    def _packet_by_marker(self, marker: str) -> dict[str, Any] | None:
        row = self.bridge.semantic.connection.execute(
            "SELECT * FROM packet_refs WHERE marker = ?",
            (marker,),
        ).fetchone()
        return dict(row) if row is not None else None

    def send(
        self,
        *,
        source_binding_id: str,
        packet_kind: str,
        target_alias: str,
        payload_ref: str,
        marker: str,
        direction_id: str | None = None,
    ) -> dict[str, Any]:
        if packet_kind not in ALLOWED_PACKET_KINDS:
            raise ManagedPacketSendError(f"packet kind is not managed-sendable: {packet_kind}")
        existing = self._packet_by_marker(marker)
        if existing is not None:
            return existing
        source = self.bindings.get(source_binding_id)
        if source is None or source.binding_state is not BindingState.ACTIVE:
            raise ManagedPacketSendError("source binding is not ACTIVE")
        alias = TARGET_ALIASES.get(target_alias)
        if alias is None:
            raise ManagedPacketSendError(f"unknown target alias: {target_alias}")
        target = None
        for binding in self.bindings.list_bindings():
            if binding.actor_kind is alias and binding.binding_state is BindingState.ACTIVE:
                target = binding
                break
        if target is None:
            raise ManagedPacketSendError("target alias has no ACTIVE binding")
        try:
            evaluate_automatic_delivery(
                source_system=MailboxSourceSystem.MANAGED_ACTOR.value,
                sender_kind=source.actor_kind.value,
                sender_actor_context_id=source.actor_context_id,
                target_kind=target.actor_kind.value,
                target_actor_context_id=target.actor_context_id,
                target_binding_state=target.binding_state.value,
                message_kind=MailboxMessageKind(packet_kind),
            )
        except MailboxAclError as exc:
            raise ManagedPacketSendError(str(exc)) from exc
        safe_ref = resolve_payload_ref(
            self.repo_root,
            payload_ref,
            existing_packet_ids=self._existing_packet_ids(),
        )
        return packet_register(
            self.bridge.semantic,
            packet_kind=packet_kind,
            source_actor_context_id=source.actor_context_id,
            target_actor_context_id=target.actor_context_id,
            payload_ref=safe_ref,
            marker=marker,
            direction_id=direction_id,
        )

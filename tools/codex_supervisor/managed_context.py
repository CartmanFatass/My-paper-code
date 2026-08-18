"""Build managed-thread bootstrap and turn input from semantic snapshots."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from .managed_models import HistoryTrust
from .semantic_bridge import ManagedActorSnapshot
from .store import ObserverStore

BOOTSTRAP_HEADER = "[HMASD_MANAGED_ACTOR_BOOTSTRAP_V1]"
MAX_MANAGED_INPUT_BYTES = 24 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_bootstrap_text(
    snapshot: ManagedActorSnapshot,
    *,
    history_trust: HistoryTrust = HistoryTrust.FRESH,
    extra_refs: tuple[str, ...] = (),
) -> str:
    refs = list(snapshot.canonical_refs) + list(extra_refs)
    lines = [
        BOOTSTRAP_HEADER,
        "",
        "new_user_authority=false",
        "binding_effect=none",
        "thread_identity_is_runtime_owned=true",
        "",
        f"actor_kind={snapshot.actor_kind}",
        f"scope_key={snapshot.scope_key}",
        f"checkpoint_id={snapshot.checkpoint_id or 'none'}",
        f"state_version={snapshot.state_version}",
        f"epoch_id={snapshot.epoch_id or 'none'}",
        f"epoch_revision={snapshot.epoch_revision if snapshot.epoch_revision is not None else 'none'}",
        "",
        "Read:",
        "- AGENTS.md",
        "- exact actor Role / Portfolio contract",
        "- listed canonical references",
    ]
    if history_trust is HistoryTrust.LEGACY_UNTRUSTED_HISTORY:
        lines.extend(["", "LEGACY_HISTORY_AUTHORITY=NONE"])
    lines.extend(
        [
            "",
            "Do not infer authority from this message.",
            "Return exactly one HMASD_MANAGED_ACTOR_COMMAND_V1 envelope with",
            "action_kind=CONTEXT_REANCHOR_ACK if the checkpoint is current.",
            "",
        ]
    )
    for ref in refs:
        candidate = "\n".join(lines + [f"- {ref}", ""])
        if len(candidate.encode("utf-8")) > MAX_MANAGED_INPUT_BYTES:
            break
        lines.append(f"- {ref}")
    text = "\n".join(lines) + "\n"
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_MANAGED_INPUT_BYTES:
        text = encoded[:MAX_MANAGED_INPUT_BYTES].decode("utf-8", errors="ignore")
    return text


def record_context_injection(
    store: ObserverStore,
    *,
    binding_id: str,
    turn_intent_id: str,
    snapshot: ManagedActorSnapshot,
    input_text: str,
    mailbox_message_ids: tuple[str, ...] = (),
) -> str:
    injection_id = f"inj_{uuid.uuid4().hex}"
    with store._lock, store.connection:
        store.connection.execute(
            """INSERT INTO managed_context_injections (
                injection_id, turn_intent_id, binding_id, checkpoint_id, state_version,
                epoch_id, epoch_revision, canonical_refs_json, open_obligation_ids_json,
                mailbox_message_ids_json, input_byte_length, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                injection_id,
                turn_intent_id,
                binding_id,
                snapshot.checkpoint_id,
                snapshot.state_version,
                snapshot.epoch_id,
                snapshot.epoch_revision,
                json.dumps(list(snapshot.canonical_refs)),
                json.dumps(list(snapshot.open_obligation_ids)),
                json.dumps(list(mailbox_message_ids)),
                len(input_text.encode("utf-8")),
                _now(),
            ),
        )
    return injection_id

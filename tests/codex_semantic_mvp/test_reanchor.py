from pathlib import Path

import pytest

from tools.codex_semantic_mvp import hook_entry
from tools.codex_semantic_mvp.actor_registry import register_session_root
from tools.codex_semantic_mvp.checkpoints import (
    context_reanchor_ack,
    current_checkpoint,
    ensure_reanchor_obligation,
    is_actor_reanchored,
    materialize_checkpoint,
)
from tools.codex_semantic_mvp.hook_entry import handle_hook
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture(autouse=True)
def unpaused_semantic_hooks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(hook_entry, "PAUSE_SENTINEL_PATH", tmp_path / "absent-hooks-pause-sentinel")


def test_compact_and_resume_open_reanchor_obligation(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    actor = register_session_root(store, session_id="session-reanchor")
    store.open_actor_workflow(actor.actor_context_id, "turn-1", "root", "coordinate")
    compact = handle_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "session-reanchor",
            "turn_id": "turn-2",
            "source": "compact",
        },
        "active",
        store,
    )
    assert compact["continue"] is True
    assert "HMASD_ACTOR_CAPSULE_V1" in compact["additionalContext"]
    assert is_actor_reanchored(store, actor.actor_context_id) is False
    checkpoint = current_checkpoint(store, actor.actor_context_id)
    assert checkpoint is not None
    context_reanchor_ack(
        store,
        actor_context_id=actor.actor_context_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        state_version=int(checkpoint["state_version"]),
        epoch_id=checkpoint.get("epoch_id"),
        epoch_revision=checkpoint.get("epoch_revision"),
        actor_turn_id="turn-99",
    )
    assert is_actor_reanchored(store, actor.actor_context_id) is True
    store.close()


def test_clear_does_not_restore_old_capsule(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    result = handle_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "session-clear",
            "turn_id": "turn-1",
            "source": "clear",
        },
        "active",
        store,
    )
    assert "No previous HMASD actor checkpoint" in result["additionalContext"]
    store.close()


def test_file_bytes_do_not_stale_ack(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    actor = register_session_root(store, session_id="session-bytes")
    store.open_actor_workflow(actor.actor_context_id, "turn-1", "root", "coordinate")
    checkpoint = materialize_checkpoint(store, actor.actor_context_id)
    ensure_reanchor_obligation(
        store,
        actor_context_id=actor.actor_context_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
    )
    authority = tmp_path / "AGENTS.md"
    authority.write_text("old", encoding="utf-8")
    context_reanchor_ack(
        store,
        actor_context_id=actor.actor_context_id,
        checkpoint_id=str(checkpoint["checkpoint_id"]),
        state_version=int(checkpoint["state_version"]),
        epoch_id=checkpoint.get("epoch_id"),
        epoch_revision=checkpoint.get("epoch_revision"),
        actor_turn_id="turn-1",
    )
    authority.write_text("new bytes that must not invalidate the ACK", encoding="utf-8")
    assert is_actor_reanchored(store, actor.actor_context_id) is True
    store.close()

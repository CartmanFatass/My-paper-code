import json
from pathlib import Path

import pytest

from tools.codex_semantic_mvp import hook_entry
from tools.codex_semantic_mvp.hook_entry import handle_hook
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture(autouse=True)
def unpaused_semantic_hooks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(hook_entry, "PAUSE_SENTINEL_PATH", tmp_path / "absent-hooks-pause-sentinel")


def test_shadow_precompact_is_observational(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    result = handle_hook(
        {
            "hook_event_name": "PreCompact",
            "session_id": "session-1",
            "turn_id": "turn-1",
            "source": "compact",
            "last_assistant_message": "BLOCKED",
        },
        "shadow",
        store,
    )
    assert result == {"continue": True}
    assert "additionalContext" not in result
    assert result.get("decision") != "block"
    assert store.events_after(None) == []
    audit = json.loads((store.path.parent / "audit.jsonl").read_text(encoding="utf-8"))
    assert audit["event"] == "COMPACTION_STARTED"
    assert (store.path.parent / "topology-probe.jsonl").is_file()
    obligations = store.connection.execute("SELECT COUNT(*) FROM obligations").fetchone()[0]
    assert obligations == 0
    store.close()


def test_shadow_postcompact_does_not_change_epoch(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    before = store.connection.execute("SELECT COUNT(*) FROM plan_epochs").fetchone()[0]
    result = handle_hook(
        {
            "hook_event_name": "PostCompact",
            "session_id": "session-1",
            "turn_id": "turn-2",
            "source": "compact",
        },
        "shadow",
        store,
    )
    assert result == {"continue": True}
    after = store.connection.execute("SELECT COUNT(*) FROM plan_epochs").fetchone()[0]
    assert after == before
    store.close()

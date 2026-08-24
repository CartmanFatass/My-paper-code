from pathlib import Path
import json

from tests.codex_supervisor.semantic_fixtures import seed_managed_actors, seed_reanchor
from tools.codex_supervisor.managed_context import (
    BOOTSTRAP_HEADER,
    MAX_MANAGED_INPUT_BYTES,
    build_bootstrap_text,
    record_context_injection,
)
from tools.codex_supervisor.managed_models import HistoryTrust


def test_bootstrap_is_non_authority_and_records_injection(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    seed_reanchor(seeded["semantic"], seeded["root"].actor_context_id)
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    text = build_bootstrap_text(snapshot, extra_refs=tuple(f"docs/ref_{index}.md" for index in range(200)))
    assert text.startswith(BOOTSTRAP_HEADER)
    assert "new_user_authority=false" in text
    assert "Do not infer authority" in text
    expected = json.dumps(
        {
            "schema_version": "1.0",
            "packet_kind": "MANAGED_ACTOR_COMMAND",
            "action_kind": "CONTEXT_REANCHOR_ACK",
            "expected": {
                "checkpoint_id": snapshot.checkpoint_id,
                "state_version": snapshot.state_version,
                "epoch_id": snapshot.epoch_id,
                "epoch_revision": snapshot.epoch_revision,
            },
            "payload": {},
        },
        separators=(",", ":"),
    )
    exact = f"<HMASD_MANAGED_ACTOR_COMMAND_V1>\n{expected}\n</HMASD_MANAGED_ACTOR_COMMAND_V1>"
    assert exact in text
    assert "After reading the references above, the final response must be exactly:" in text
    assert len(text.encode("utf-8")) <= MAX_MANAGED_INPUT_BYTES
    injection_id = record_context_injection(
        seeded["supervisor"],
        binding_id="bind_x",
        turn_intent_id="intent_x",
        snapshot=snapshot,
        input_text=text,
    )
    row = seeded["supervisor"].connection.execute(
        "SELECT input_byte_length FROM managed_context_injections WHERE injection_id=?",
        (injection_id,),
    ).fetchone()
    assert int(row[0]) == len(text.encode("utf-8"))
    legacy = build_bootstrap_text(snapshot, history_trust=HistoryTrust.LEGACY_UNTRUSTED_HISTORY)
    assert "LEGACY_HISTORY_AUTHORITY=NONE" in legacy
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()

from pathlib import Path

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


def test_bridge_does_not_import_promotion_or_write_files() -> None:
    source = Path(bridge_mod.__file__).read_text(encoding="utf-8")
    assert "mark_promotion_applied" not in source
    assert "create_promotion_proposal" not in source
    assert "write_text" not in source
    assert "open(" not in source
    assert not hasattr(SemanticBridge, "write_file")

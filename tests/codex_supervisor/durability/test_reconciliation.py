from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.models import EffectState
from tools.codex_supervisor.durability.reconciliation import EffectReconciler, ReconciliationError


def test_reconciler_never_calls_mutating_method(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    reconciler = EffectReconciler(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="k1",
        request={"threadId": "thr1"},
    )
    with pytest.raises(ReconciliationError, match="PREPARED"):
        reconciler.reconcile(effect.effect_id)
    connection.close()


def test_turn_start_reconciles_by_original_client_key(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="hmasd-managed:t1",
        request={"threadId": "thr1"},
    )
    journal.claim_write(
        effect.effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="r1",
        raw_request_seq=1,
    )
    journal.mark_uncertain(effect.effect_id, reason="timeout")
    reconciler = EffectReconciler(connection)
    confirmed = reconciler.reconcile(
        effect.effect_id,
        evidence={"turn_id": "turnx", "clientUserMessageId": "hmasd-managed:t1"},
    )
    assert confirmed.state == EffectState.EFFECT_CONFIRMED.value
    connection.close()


def test_restart_reconciliation_is_idempotent(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    initialize_database(connection)
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="t1",
        binding_id="b1",
        method="turn/start",
        client_key="k1",
        request={},
    )
    journal.claim_write(
        effect.effect_id,
        run_id="run1",
        client_request_id="1",
        request_row_id="r1",
        raw_request_seq=1,
    )
    reconciler = EffectReconciler(connection)
    first = reconciler.restart_open_effects()
    second = reconciler.restart_open_effects()
    assert first == second == [effect.effect_id]
    connection.close()

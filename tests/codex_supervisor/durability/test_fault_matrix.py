from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.effects import EffectError, EffectJournal
from tools.codex_supervisor.durability.models import EffectState


def test_write_started_is_never_automatically_resent(tmp_path: Path) -> None:
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
    with pytest.raises(EffectError):
        journal.claim_write(
            effect.effect_id,
            run_id="run1",
            client_request_id="2",
            request_row_id="r2",
            raw_request_seq=2,
        )
    assert journal.get(effect.effect_id).state == EffectState.WRITE_STARTED.value
    connection.close()

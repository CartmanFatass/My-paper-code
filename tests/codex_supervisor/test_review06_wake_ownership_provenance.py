import asyncio
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.test_wake_scheduler import (
    _close_raw_failure_wake,
    _prepared_raw_failure_wake,
)
from tools.codex_supervisor.db import initialize_database
from tools.codex_supervisor.durability.effects import (
    EffectError,
    EffectJournal,
    cancel_exact_prepared_wake,
)
from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.wake_scheduler import WakeSchedulerError


def _assert_zero_write_and_no_requeue(seeded, batches, mailbox, message, batch) -> None:
    connection = seeded["supervisor"].connection
    assert connection.execute(
        "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (batch["effect_id"],)
    ).fetchone()[0] == 0
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
    assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"


def test_first_preflight_operational_error_fails_closed_before_any_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded, scheduler, batches, mailbox, message, batch, lease = (
            _prepared_raw_failure_wake(tmp_path, "sched-first-preflight-lock")
        )
        owner_calls = 0

        def fail_first_preflight(_wake_batch_id):
            raise sqlite3.OperationalError("database is locked")

        def owner_must_not_be_reached(*_args, **_kwargs):
            nonlocal owner_calls
            owner_calls += 1
            raise AssertionError("owner must not be reached")

        monkeypatch.setattr(scheduler, "_prove_exact_prepared_wake", fail_first_preflight)
        monkeypatch.setattr(
            AppServerSessionOwner, "for_client", staticmethod(owner_must_not_be_reached)
        )
        with pytest.raises(WakeSchedulerError, match="failed closed.*do not retry"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        assert owner_calls == 0
        _assert_zero_write_and_no_requeue(seeded, batches, mailbox, message, batch)
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "PREPARED"
        _close_raw_failure_wake(seeded)

    asyncio.run(body())


class _CancelBeforeWriteClient:
    def __init__(self) -> None:
        self.server_requests = asyncio.Queue()
        self.discard_count = 0
        self.send_count = 0

    def start_reader(self) -> None:
        return None

    def prepare_request(self, method, params=None):
        return SimpleNamespace(
            request_id="cancel-1",
            method=method,
            params=dict(params or {}),
            payload={"id": 1, "method": method, "params": dict(params or {})},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
        )

    def discard_prepared(self, _prepared) -> None:
        self.discard_count += 1

    async def send_prepared(self, _prepared) -> None:
        self.send_count += 1

    async def await_prepared(self, _prepared):  # pragma: no cover - never reached
        raise AssertionError("await must not be reached")


def test_cancelled_error_before_write_discards_locally_then_requeues_exact_wake(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded, scheduler, batches, mailbox, message, batch, lease = (
            _prepared_raw_failure_wake(tmp_path, "sched-cancel-before-write")
        )
        client = _CancelBeforeWriteClient()
        scheduler.client = client  # type: ignore[assignment]

        def cancel_record(**_kwargs):
            raise asyncio.CancelledError()

        monkeypatch.setattr(seeded["supervisor"], "record_effect_write_start", cancel_record)
        with pytest.raises(asyncio.CancelledError):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        owner = AppServerSessionOwner._by_client[id(client)]
        assert client.discard_count == 1
        assert client.send_count == 0
        assert str(batch["effect_id"]) not in owner._open_effect_ids
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "CANCELLED"
        assert mailbox.get(message.message_id).delivery_state.value == "ELIGIBLE"
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "CANCELLED_BEFORE_WRITE"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (batch["effect_id"],)
        ).fetchone()[0] == 0
        await owner.close()
        _close_raw_failure_wake(seeded)

    asyncio.run(body())


def test_cancelled_error_after_write_started_preserves_uncertainty_without_requeue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded, scheduler, batches, mailbox, message, batch, lease = (
            _prepared_raw_failure_wake(tmp_path, "sched-cancel-after-write")
        )
        client = _CancelBeforeWriteClient()
        scheduler.client = client  # type: ignore[assignment]
        original = seeded["supervisor"].record_effect_write_start

        def commit_then_cancel(**kwargs):
            original(**kwargs)
            raise asyncio.CancelledError()

        monkeypatch.setattr(
            seeded["supervisor"], "record_effect_write_start", commit_then_cancel
        )
        with pytest.raises(asyncio.CancelledError):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        owner = AppServerSessionOwner._by_client[id(client)]
        assert client.discard_count == 0
        assert client.send_count == 0
        assert str(batch["effect_id"]) in owner._open_effect_ids
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "SUBMITTING"
        assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "WRITE_STARTED"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (batch["effect_id"],)
        ).fetchone()[0] == 1
        await owner.close()
        _close_raw_failure_wake(seeded)

    asyncio.run(body())


@pytest.mark.parametrize(
    "corruption",
    [
        "foreign",
        "duplicate",
        "crossed",
        "same_owner_foreign_binding_prepared",
        "same_owner_foreign_binding_write_started",
    ],
)
def test_exact_wake_ownership_ambiguity_never_sends_or_requeues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    async def body() -> None:
        seeded, scheduler, batches, mailbox, message, batch, lease = (
            _prepared_raw_failure_wake(tmp_path, f"sched-owner-{corruption}")
        )
        connection = seeded["supervisor"].connection
        if corruption == "foreign":
            connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id,owner_kind,owner_id,binding_id,method,client_key,
                    request_json,state,prepared_at
                ) VALUES ('eff_foreign','WAKE_BATCH','wake_foreign',?,'turn/start',
                          'foreign-key','{}','PREPARED','t')""",
                (batch["binding_id"],),
            )
            connection.execute(
                "UPDATE wake_batches SET effect_id='eff_foreign' WHERE wake_batch_id=?",
                (batch["wake_batch_id"],),
            )
        elif corruption == "duplicate":
            connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id,owner_kind,owner_id,binding_id,method,client_key,
                    request_json,state,prepared_at
                ) VALUES ('eff_duplicate','WAKE_BATCH',?,?,'turn/start',
                          'duplicate-key','{}','PREPARED','t')""",
                (batch["wake_batch_id"], batch["binding_id"]),
            )
        elif corruption == "crossed":
            EffectJournal(connection).claim_write(
                str(batch["effect_id"]),
                run_id="crossed",
                client_request_id="1",
                request_row_id="raw-none",
                raw_request_seq=1,
            )
        else:
            foreign_state = (
                "PREPARED"
                if corruption.endswith("prepared")
                else "WRITE_STARTED"
            )
            connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id,owner_kind,owner_id,binding_id,method,client_key,
                    request_json,state,prepared_at
                ) VALUES (?,?,?,?,? ,?,?,?,?)""",
                (
                    f"eff_{corruption}",
                    "WAKE_BATCH",
                    batch["wake_batch_id"],
                    "binding_foreign",
                    "turn/start",
                    f"key-{corruption}",
                    "{}",
                    foreign_state,
                    "t",
                ),
            )
        connection.commit()
        owner_calls = 0

        def owner_must_not_be_reached(*_args, **_kwargs):
            nonlocal owner_calls
            owner_calls += 1
            raise AssertionError("owner must not be reached")

        monkeypatch.setattr(
            AppServerSessionOwner, "for_client", staticmethod(owner_must_not_be_reached)
        )
        with pytest.raises(WakeSchedulerError, match="failed closed.*do not retry"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                str(batch["input_text"]),
                lease_generation=int(lease["generation"]),
            )
        assert owner_calls == 0
        _assert_zero_write_and_no_requeue(seeded, batches, mailbox, message, batch)
        if corruption.startswith("same_owner_foreign_binding_"):
            assert connection.execute(
                "SELECT state FROM app_server_effects WHERE effect_id = ?",
                (f"eff_{corruption}",),
            ).fetchone()[0] == (
                "PREPARED" if corruption.endswith("prepared") else "WRITE_STARTED"
            )
        _close_raw_failure_wake(seeded)

    asyncio.run(body())


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
def test_same_owner_foreign_binding_blocks_wake_cancellation_without_requeue(
    tmp_path: Path, foreign_state: str
) -> None:
    seeded, _scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(
            tmp_path, f"sched-cancel-foreign-{foreign_state.lower()}"
        )
    )
    connection = seeded["supervisor"].connection
    foreign_effect_id = f"eff_wake_cancel_foreign_{foreign_state.lower()}"
    connection.execute(
        """INSERT INTO app_server_effects(
            effect_id,owner_kind,owner_id,binding_id,method,client_key,
            request_json,state,prepared_at
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            foreign_effect_id,
            "WAKE_BATCH",
            batch["wake_batch_id"],
            "binding_foreign",
            "turn/start",
            f"key-{foreign_effect_id}",
            "{}",
            foreign_state,
            "t",
        ),
    )
    connection.commit()

    with seeded["supervisor"]._lock, pytest.raises(EffectError, match="ambiguous"):
        with DurabilityTransaction(connection):
            cancel_exact_prepared_wake(
                connection,
                str(batch["wake_batch_id"]),
                effect_id=str(batch["effect_id"]),
                binding_id=str(batch["binding_id"]),
                cause_ref="must-not-cancel",
            )

    _assert_zero_write_and_no_requeue(seeded, batches, mailbox, message, batch)
    assert connection.execute(
        "SELECT state FROM app_server_effects WHERE effect_id = ?",
        (foreign_effect_id,),
    ).fetchone()[0] == foreign_state
    _close_raw_failure_wake(seeded)


def _insert_legacy_binding(connection, binding_id: str, state: str, effect_state: str) -> None:
    suffix = binding_id[-1]
    connection.execute(
        """INSERT INTO managed_actor_bindings(
            binding_id,actor_context_id,actor_kind,semantic_scope_key,direction_id,
            thread_id,thread_origin,history_trust,binding_state,memory_policy_state,
            repo_root,thread_cwd,created_by_operator,created_at,prepared_state_version,
            prepared_context_trusted
        ) VALUES (?,?, 'PORTFOLIO','portfolio',NULL,?,'NEW','FRESH',?,'UNVERIFIED',
                  'r','r','op','t',0,0)""",
        (binding_id, f"actor-{suffix}", f"thread-{suffix}", state),
    )
    connection.execute(
        """INSERT INTO app_server_effects(
            effect_id,owner_kind,owner_id,binding_id,method,client_key,
            request_json,state,prepared_at
        ) VALUES (?,?,?,?,'thread/start',?,'{}',?,'t')""",
        (
            f"effect-{suffix}",
            "THREAD_PROVISION",
            binding_id,
            binding_id,
            f"legacy-{suffix}",
            effect_state,
        ),
    )


def test_schema_v8_untrusted_nonterminal_bindings_and_effects_are_quarantined(
    tmp_path: Path
) -> None:
    from tools.codex_supervisor.store import ObserverStore

    store = ObserverStore(tmp_path)
    connection = store.connection
    states = ["PREPARED", "THREAD_CREATED", "VERIFICATION_REQUIRED", "ACTIVE"]
    for index, state in enumerate(states):
        _insert_legacy_binding(
            connection,
            f"legacy-{index}",
            state,
            "WRITE_STARTED" if state == "ACTIVE" else "PREPARED",
        )
    connection.execute("DELETE FROM schema_meta")
    connection.execute("INSERT INTO schema_meta(version,applied_at) VALUES (8,'legacy')")
    connection.commit()
    initialize_database(connection)
    migrated = connection.execute(
        """SELECT binding_state,version,prepared_context_trusted
        FROM managed_actor_bindings ORDER BY binding_id"""
    ).fetchall()
    assert [tuple(row) for row in migrated] == [
        ("REVOKED", 1, 0),
        ("REVOKED", 1, 0),
        ("SUSPENDED", 1, 0),
        ("SUSPENDED", 1, 0),
    ]
    effects = connection.execute(
        "SELECT state FROM app_server_effects ORDER BY effect_id"
    ).fetchall()
    assert [str(row[0]) for row in effects] == [
        "CANCELLED_BEFORE_WRITE",
        "CANCELLED_BEFORE_WRITE",
        "CANCELLED_BEFORE_WRITE",
        "WRITE_STARTED",
    ]
    assert connection.execute(
        "SELECT COUNT(*) FROM raw_messages WHERE effect_id LIKE 'effect-%'"
    ).fetchone()[0] == 0
    store.close()


def test_v8_active_binding_is_preserved_only_from_durable_verified_provenance(
    tmp_path: Path
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    connection = seeded["supervisor"].connection
    binding_ids = [
        str(row[0])
        for row in connection.execute(
            "SELECT binding_id FROM managed_actor_bindings ORDER BY binding_id"
        )
    ]
    defaulted_id = binding_ids[0]
    connection.execute(
        "UPDATE managed_actor_bindings SET prepared_state_version=0 WHERE binding_id=?",
        (defaulted_id,),
    )
    before = {
        str(row["binding_id"]): (
            row["prepared_checkpoint_id"],
            row["prepared_state_version"],
            row["prepared_epoch_id"],
            row["prepared_epoch_revision"],
        )
        for row in connection.execute("SELECT * FROM managed_actor_bindings")
    }
    connection.execute("UPDATE managed_actor_bindings SET prepared_context_trusted=0")
    connection.execute("DELETE FROM schema_meta")
    connection.execute("INSERT INTO schema_meta(version,applied_at) VALUES (8,'legacy')")
    connection.commit()
    initialize_database(connection)
    rows = connection.execute("SELECT * FROM managed_actor_bindings").fetchall()
    migrated = {
        str(row["binding_id"]): (
            str(row["binding_state"]), int(row["prepared_context_trusted"])
        )
        for row in rows
    }
    assert migrated[defaulted_id] == ("SUSPENDED", 0)
    assert migrated[binding_ids[1]] == ("ACTIVE", 1)
    after = {
        str(row["binding_id"]): (
            row["prepared_checkpoint_id"],
            row["prepared_state_version"],
            row["prepared_epoch_id"],
            row["prepared_epoch_revision"],
        )
        for row in rows
    }
    assert after == before
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_fresh_binding_writes_trusted_tuple_provenance(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    rows = seeded["supervisor"].connection.execute(
        """SELECT prepared_context_trusted, prepared_state_version
        FROM managed_actor_bindings"""
    ).fetchall()
    assert rows and all(tuple(row)[0] == 1 for row in rows)
    assert all(tuple(row)[1] > 0 for row in rows)
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()

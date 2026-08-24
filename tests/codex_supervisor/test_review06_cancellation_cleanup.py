import asyncio
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.codex_supervisor.store import ObserverStore

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.durability.effects import EffectError, EffectJournal
from tools.codex_supervisor.durability.session_owner import (
    AppServerSessionOwner,
    SessionOwnerError,
)
from tools.codex_supervisor.mailbox_models import MailboxMessageKind, MailboxSourceSystem
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.scheduler_leases import SchedulerLeases


def _close_seeded(seeded) -> None:
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def _assert_external_writer_can_enter(path: Path) -> None:
    writer = sqlite3.connect(path, timeout=0.0, isolation_level=None)
    try:
        writer.execute("PRAGMA busy_timeout = 0")
        writer.execute("BEGIN IMMEDIATE")
        writer.rollback()
    finally:
        writer.close()


@pytest.mark.parametrize("failure", [asyncio.CancelledError, SystemExit, KeyboardInterrupt])
def test_currentness_guard_baseexception_rolls_back_and_releases_writer(
    tmp_path: Path, failure: type[BaseException]
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    snapshot = bridge.snapshot(actor_id)
    connection = bridge.semantic.connection
    before = connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0]

    with pytest.raises(failure):
        with bridge.currentness_guard(
            actor_id,
            checkpoint_id=snapshot.checkpoint_id,
            state_version=snapshot.state_version,
            epoch_id=snapshot.epoch_id,
            epoch_revision=snapshot.epoch_revision,
        ):
            connection.execute(
                "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                (actor_id,),
            )
            raise failure("guard-yield")

    assert connection.in_transaction is False
    assert connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0] == before
    _assert_external_writer_can_enter(bridge.semantic_state_path)
    with bridge.currentness_guard(
        actor_id,
        checkpoint_id=snapshot.checkpoint_id,
        state_version=snapshot.state_version,
        epoch_id=snapshot.epoch_id,
        epoch_revision=snapshot.epoch_revision,
    ):
        pass
    _close_seeded(seeded)


def test_currentness_guard_entry_cancellation_and_writer_guard_commit_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    snapshot = bridge.snapshot(actor_id)
    connection = bridge.semantic.connection

    def cancel_after_begin(_actor_context_id: str):
        assert connection.in_transaction is True
        raise asyncio.CancelledError("guard-entry")

    monkeypatch.setattr(bridge, "_snapshot_unlocked", cancel_after_begin)
    with pytest.raises(asyncio.CancelledError, match="guard-entry"):
        with bridge.currentness_guard(
            actor_id,
            checkpoint_id=snapshot.checkpoint_id,
            state_version=snapshot.state_version,
            epoch_id=snapshot.epoch_id,
            epoch_revision=snapshot.epoch_revision,
        ):
            raise AssertionError("yield must not be reached")
    assert connection.in_transaction is False
    _assert_external_writer_can_enter(bridge.semantic_state_path)
    monkeypatch.undo()

    before = connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0]
    with bridge.writer_guard():
        connection.execute(
            "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
            (actor_id,),
        )
    assert connection.in_transaction is False
    assert connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0] == before + 1
    with pytest.raises(RuntimeError, match="ordinary"):
        with bridge.writer_guard():
            connection.execute(
                "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                (actor_id,),
            )
            raise RuntimeError("ordinary")
    assert connection.in_transaction is False
    assert connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0] == before + 1
    _close_seeded(seeded)


@pytest.mark.parametrize("failure", [asyncio.CancelledError, SystemExit, KeyboardInterrupt])
def test_writer_guard_baseexception_rolls_back_and_allows_next_guard(
    tmp_path: Path, failure: type[BaseException]
) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge = seeded["bridge"]
    actor_id = seeded["root"].actor_context_id
    connection = bridge.semantic.connection
    before = connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0]
    with pytest.raises(failure):
        with bridge.writer_guard():
            connection.execute(
                "UPDATE workflows SET state_version = state_version + 1 WHERE actor_context_id = ?",
                (actor_id,),
            )
            raise failure("writer-yield")
    assert connection.in_transaction is False
    assert connection.execute(
        "SELECT state_version FROM workflows WHERE actor_context_id = ?", (actor_id,)
    ).fetchone()[0] == before
    _assert_external_writer_can_enter(bridge.semantic_state_path)
    with bridge.writer_guard():
        pass
    _close_seeded(seeded)


def test_guards_refuse_ambient_transaction_without_rolling_it_back(tmp_path: Path) -> None:
    seeded = seed_managed_actors(tmp_path)
    bridge = seeded["bridge"]
    connection = bridge.semantic.connection
    connection.execute("BEGIN IMMEDIATE")
    with pytest.raises(ValueError, match="transaction ownership"):
        with bridge.writer_guard():
            pass
    assert connection.in_transaction is True
    connection.rollback()
    _close_seeded(seeded)


class _CancelledResumeClient:
    def __init__(self) -> None:
        self.server_requests = asyncio.Queue()
        self.discard_count = 0
        self.send_count = 0
        self._pending = {}
        self._committed_claims = {}

    def start_reader(self) -> None:
        return None

    def prepare_request(self, method, params=None):
        return SimpleNamespace(
            request_id="cancel-resume-1",
            method=method,
            params=dict(params or {}),
            payload={"id": 1, "method": method, "params": dict(params or {})},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
        )

    def discard_prepared(self, _prepared) -> None:
        self.discard_count += 1

    async def send_prepared(self, _prepared) -> None:
        self.send_count += 1

    async def await_prepared(self, _prepared):  # pragma: no cover
        raise AssertionError("cancelled pre-write resume cannot await a response")


def _prepared_resume(tmp_path: Path, key: str, *, message_count: int = 2):
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    binding = seeded["bindings"].get(binding_id)
    assert binding is not None and binding.thread_id
    messages = []
    for index in range(message_count):
        message = seeded["mailbox"].enqueue(
            source_system=MailboxSourceSystem.OPERATOR.value,
            source_event_key=f"{key}:{index}",
            target_actor_context_id=binding.actor_context_id,
            message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
            subject_ref=f"subject-{index}",
            payload_ref=f"payload-{index}",
        )
        seeded["mailbox"].mark_eligible(message.message_id)
        messages.append(message)
    batches = WakeBatchStore(seeded["supervisor"], seeded["mailbox"])
    leases = SchedulerLeases(seeded["supervisor"])
    lease = leases.acquire(binding_id, "recovery", ttl_seconds=300.0)
    batch = batches.prepare(
        binding_id=binding_id,
        thread_id=binding.thread_id,
        snapshot=seeded["bridge"].snapshot(binding.actor_context_id),
        messages=messages,
        lease_holder="recovery",
        lease_generation=int(lease["generation"]),
    )
    client = _CancelledResumeClient()
    recovery = WakeRecovery(
        seeded["bindings"],
        seeded["mailbox"],
        batches,
        client,  # type: ignore[arg-type]
        leases,
        "recovery",
        bridge=seeded["bridge"],
    )
    return seeded, binding, messages, batches, batch, client, recovery


def _resume_effect(seeded, binding, batch):
    effect = EffectJournal(seeded["supervisor"].connection).get_by_key(
        "thread/resume",
        f"thread/resume:{binding.thread_id}:{batch['wake_batch_id']}",
    )
    assert effect is not None
    return effect


def test_cancelled_resume_prewrite_cleans_owner_then_atomically_requeues_messages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded, binding, messages, batches, batch, client, recovery = _prepared_resume(
            tmp_path, "review06:resume-cancel-success"
        )

        def cancel_record(**_kwargs):
            raise asyncio.CancelledError("resume-prewrite")

        monkeypatch.setattr(seeded["supervisor"], "_record_authorized_effect_claim", cancel_record)
        with pytest.raises(asyncio.CancelledError, match="resume-prewrite"):
            await recovery.resume_once(
                binding.binding_id, wake_batch_id=str(batch["wake_batch_id"])
            )
        assert seeded["bridge"].semantic.connection.in_transaction is False
        with seeded["bridge"].writer_guard():
            pass
        resume = _resume_effect(seeded, binding, batch)
        wake_effect = EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        )
        owner = AppServerSessionOwner._by_client[id(client)]
        assert client.discard_count == 1
        assert client.send_count == 0
        assert resume.effect_id not in owner._open_effect_ids
        assert resume.state == "CANCELLED_BEFORE_WRITE"
        assert wake_effect.state == "CANCELLED_BEFORE_WRITE"
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "CANCELLED"
        assert all(
            seeded["mailbox"].get(message.message_id).delivery_state.value == "ELIGIBLE"
            for message in messages
        )
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (resume.effect_id,)
        ).fetchone()[0] == 0
        await owner.close()
        _close_seeded(seeded)

    asyncio.run(body())


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_context",
        "foreign_resume",
        "duplicate_resume",
        "crossed_wake_effect",
        "duplicate_context",
        "foreign_message",
        "containment_failure",
        "writer_lock",
        "write_started",
        "same_owner_foreign_binding_prepared",
        "same_owner_foreign_binding_write_started",
    ],
)
def _legacy_cancelled_resume_matrix_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    async def body() -> None:
        assert not hasattr(ObserverStore, "record_effect_write_start")
        assert hasattr(ObserverStore, "_record_authorized_effect_claim")
        seeded, binding, messages, batches, batch, client, recovery = _prepared_resume(
            tmp_path, f"review06:resume-cancel-{corruption}"
        )
        connection = seeded["supervisor"].connection
        external_writer = None
        connection_store_record = seeded["supervisor"]._record_authorized_effect_claim

        def cancel_record(**kwargs):
            nonlocal external_writer
            resume = _resume_effect(seeded, binding, batch)
            if corruption == "missing_context":
                connection.execute(
                    "DELETE FROM managed_context_injections WHERE turn_intent_id = ?",
                    (batch["wake_batch_id"],),
                )
                connection.commit()
            elif corruption == "foreign_resume":
                connection.execute(
                    "UPDATE app_server_effects SET owner_id = 'foreign' WHERE effect_id = ?",
                    (resume.effect_id,),
                )
                connection.commit()
            elif corruption == "duplicate_resume":
                connection.execute(
                    """INSERT INTO app_server_effects(
                        effect_id,owner_kind,owner_id,binding_id,method,client_key,
                        request_json,state,prepared_at
                    ) VALUES ('eff_duplicate_resume','THREAD_RESUME',?,?,
                              'thread/resume','duplicate-resume','{}','PREPARED','t')""",
                    (binding.binding_id, binding.binding_id),
                )
                connection.commit()
            elif corruption == "crossed_wake_effect":
                connection.execute(
                    """INSERT INTO app_server_effects(
                        effect_id,owner_kind,owner_id,binding_id,method,client_key,
                        request_json,state,prepared_at
                    ) VALUES ('eff_crossed_wake','WAKE_BATCH','wake_foreign',?,
                              'turn/start','crossed-wake','{}','PREPARED','t')""",
                    (binding.binding_id,),
                )
                connection.execute(
                    "UPDATE wake_batches SET effect_id='eff_crossed_wake' WHERE wake_batch_id = ?",
                    (batch["wake_batch_id"],),
                )
                connection.commit()
            elif corruption == "duplicate_context":
                connection.execute(
                    """INSERT INTO managed_context_injections(
                        injection_id,turn_intent_id,binding_id,checkpoint_id,state_version,
                        epoch_id,epoch_revision,canonical_refs_json,open_obligation_ids_json,
                        mailbox_message_ids_json,input_byte_length,created_at
                    ) SELECT 'inj_duplicate',turn_intent_id,binding_id,checkpoint_id,
                             state_version,epoch_id,epoch_revision,canonical_refs_json,
                             open_obligation_ids_json,mailbox_message_ids_json,
                             input_byte_length,'z'
                      FROM managed_context_injections WHERE turn_intent_id = ?""",
                    (batch["wake_batch_id"],),
                )
                connection.commit()
            elif corruption == "foreign_message":
                connection.execute(
                    "UPDATE mailbox_messages SET target_actor_context_id='foreign' WHERE message_id = ?",
                    (messages[0].message_id,),
                )
                connection.commit()
            elif corruption == "containment_failure":
                from tools.codex_supervisor.durability import effects

                def fail_after_mutation(local_connection, *args, **kwargs):
                    local_connection.execute(
                        "UPDATE wake_batches SET state='CANCELLED' WHERE wake_batch_id = ?",
                        (batch["wake_batch_id"],),
                    )
                    raise sqlite3.OperationalError("forced containment failure")

                monkeypatch.setattr(
                    effects, "cancel_exact_prepared_resume_and_wake", fail_after_mutation
                )
            elif corruption == "writer_lock":
                external_writer = sqlite3.connect(
                    seeded["supervisor"].path, timeout=0.0, isolation_level=None
                )
                external_writer.execute("PRAGMA busy_timeout = 0")
                external_writer.execute("BEGIN IMMEDIATE")
            elif corruption == "write_started":
                connection_store_record(**kwargs)
            elif corruption.startswith("same_owner_foreign_binding_"):
                foreign_state = (
                    "PREPARED"
                    if corruption.endswith("prepared")
                    else "WRITE_STARTED"
                )
                connection.execute(
                    """INSERT INTO app_server_effects(
                        effect_id,owner_kind,owner_id,binding_id,method,client_key,
                        request_json,state,prepared_at
                    ) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        f"eff_{corruption}",
                        "THREAD_RESUME",
                        binding.binding_id,
                        "binding_foreign",
                        "thread/resume",
                        f"key-{corruption}",
                        "{}",
                        foreign_state,
                        "t",
                    ),
                )
                connection.commit()
            raise asyncio.CancelledError(f"resume-{corruption}")

        monkeypatch.setattr(seeded["supervisor"], "_record_authorized_effect_claim", cancel_record)
        with pytest.raises(asyncio.CancelledError, match=f"resume-{corruption}"):
            await recovery.resume_once(
                binding.binding_id, wake_batch_id=str(batch["wake_batch_id"])
            )
        if external_writer is not None:
            external_writer.rollback()
            external_writer.close()
        resume = _resume_effect(seeded, binding, batch)
        owner = AppServerSessionOwner._by_client[id(client)]
        expected_resume_state = "WRITE_STARTED" if corruption == "write_started" else "PREPARED"
        assert resume.state == expected_resume_state
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
        assert all(
            seeded["mailbox"].get(message.message_id).delivery_state.value == "BATCHED"
            for message in messages
        )
        assert client.send_count == 0
        if corruption.startswith("same_owner_foreign_binding_"):
            assert connection.execute(
                "SELECT state FROM app_server_effects WHERE effect_id = ?",
                (f"eff_{corruption}",),
            ).fetchone()[0] == (
                "PREPARED" if corruption.endswith("prepared") else "WRITE_STARTED"
            )
        if corruption == "write_started":
            assert resume.effect_id in owner._open_effect_ids
            assert connection.execute(
                "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (resume.effect_id,)
            ).fetchone()[0] == 1
        else:
            assert resume.effect_id not in owner._open_effect_ids
            assert connection.execute(
                "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (resume.effect_id,)
            ).fetchone()[0] == 0
        await owner.close()
        _close_seeded(seeded)

    asyncio.run(body())


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_context",
        "foreign_resume",
        "duplicate_resume",
        "crossed_wake_effect",
        "duplicate_context",
        "foreign_message",
        "containment_failure",
        "writer_lock",
        "write_started",
        "same_owner_foreign_binding_prepared",
        "same_owner_foreign_binding_write_started",
    ],
)
def test_cancelled_resume_ambiguous_or_postwrite_state_never_requeues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    async def body() -> None:
        from contextlib import contextmanager

        from tools.codex_supervisor.durability.authority_kernel import (
            ResumeMode,
            seal_thread_resume,
        )
        from tools.codex_supervisor.durability.transaction import DurabilityTransaction

        seeded, binding, messages, batches, batch, client, recovery = _prepared_resume(
            tmp_path, f"review08:resume-cleanup-{corruption}"
        )
        connection = seeded["supervisor"].connection
        journal = EffectJournal(connection)
        resume = journal.prepare_effect(
            owner_kind="THREAD_RESUME",
            owner_id=binding.binding_id,
            binding_id=binding.binding_id,
            method="thread/resume",
            client_key=f"thread/resume:{binding.thread_id}:{batch['wake_batch_id']}",
            request={"threadId": binding.thread_id},
        )
        with seeded["supervisor"]._lock, DurabilityTransaction(connection):
            plan = seal_thread_resume(
                connection,
                resume.effect_id,
                mode=ResumeMode.WAKE_RECOVERY,
                wake_batch_id=str(batch["wake_batch_id"]),
            )
        owner = AppServerSessionOwner(client, seeded["supervisor"])
        external_writer = None

        if corruption == "write_started":
            original_guard = seeded["bridge"].currentness_guard

            @contextmanager
            def fail_after_claim(*args, **kwargs):
                with original_guard(*args, **kwargs) as snapshot:
                    yield snapshot
                    raise RuntimeError("post-write uncertainty")

            monkeypatch.setattr(seeded["bridge"], "currentness_guard", fail_after_claim)
            with pytest.raises(RuntimeError, match="post-write uncertainty"):
                await owner.submit_thread_resume(plan)
        elif corruption == "writer_lock":
            external_writer = sqlite3.connect(
                seeded["supervisor"].path, timeout=0.0, isolation_level=None
            )
            external_writer.execute("PRAGMA busy_timeout = 0")
            external_writer.execute("BEGIN IMMEDIATE")
            connection.execute("PRAGMA busy_timeout = 0")
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                await owner.submit_thread_resume(plan)
        else:

            def cancel_at_typed_final_boundary(_plan) -> None:
                if corruption == "missing_context":
                    connection.execute(
                        "DELETE FROM managed_context_injections WHERE turn_intent_id=?",
                        (batch["wake_batch_id"],),
                    )
                elif corruption in {"foreign_resume", "duplicate_resume"}:
                    connection.execute(
                        """INSERT INTO app_server_effects(
                            effect_id,owner_kind,owner_id,binding_id,method,client_key,
                            request_json,state,prepared_at
                        ) VALUES (?,?,?,?,?,?,?,?,?)""",
                        (
                            f"eff_{corruption}",
                            "THREAD_RESUME",
                            binding.binding_id,
                            "foreign-binding" if corruption == "foreign_resume" else binding.binding_id,
                            "thread/resume",
                            f"key-{corruption}",
                            "{}",
                            "PREPARED",
                            "t",
                        ),
                    )
                elif corruption == "crossed_wake_effect":
                    connection.execute(
                        "UPDATE wake_batches SET effect_id='foreign' WHERE wake_batch_id=?",
                        (batch["wake_batch_id"],),
                    )
                elif corruption == "duplicate_context":
                    connection.execute(
                        """INSERT INTO managed_context_injections(
                            injection_id,turn_intent_id,binding_id,checkpoint_id,state_version,
                            epoch_id,epoch_revision,canonical_refs_json,open_obligation_ids_json,
                            mailbox_message_ids_json,input_byte_length,input_bytes,input_sha256,created_at
                        ) SELECT 'inj_duplicate',turn_intent_id,binding_id,checkpoint_id,
                                 state_version,epoch_id,epoch_revision,canonical_refs_json,
                                 open_obligation_ids_json,mailbox_message_ids_json,
                                 input_byte_length,input_bytes,input_sha256,'z'
                          FROM managed_context_injections WHERE turn_intent_id=?""",
                        (batch["wake_batch_id"],),
                    )
                elif corruption == "foreign_message":
                    connection.execute(
                        "UPDATE mailbox_messages SET target_actor_context_id='foreign' WHERE message_id=?",
                        (messages[0].message_id,),
                    )
                elif corruption.startswith("same_owner_foreign_binding_"):
                    state = "PREPARED" if corruption.endswith("prepared") else "WRITE_STARTED"
                    connection.execute(
                        """INSERT INTO app_server_effects(
                            effect_id,owner_kind,owner_id,binding_id,method,client_key,
                            request_json,state,prepared_at
                        ) VALUES (?,?,?,?,?,?,?,?,?)""",
                        (
                            f"eff_{corruption}",
                            "THREAD_RESUME",
                            binding.binding_id,
                            "binding_foreign",
                            "thread/resume",
                            f"key-{corruption}",
                            "{}",
                            state,
                            "t",
                        ),
                    )
                raise asyncio.CancelledError(f"resume-{corruption}")

            owner._before_final_authority_proof = cancel_at_typed_final_boundary  # type: ignore[method-assign]
            with pytest.raises(
                (asyncio.CancelledError, sqlite3.IntegrityError, EffectError)
            ):
                await owner.submit_thread_resume(plan)

            if corruption == "containment_failure":
                from tools.codex_supervisor.durability import effects

                def fail_containment(local_connection, *args, **kwargs):
                    local_connection.execute(
                        """UPDATE wake_batches
                        SET state='CANCELLED',version=version+1
                        WHERE wake_batch_id=?""",
                        (batch["wake_batch_id"],),
                    )
                    raise sqlite3.OperationalError("forced containment failure")

                monkeypatch.setattr(
                    effects, "cancel_exact_prepared_resume_and_wake", fail_containment
                )
                with pytest.raises(sqlite3.OperationalError, match="forced containment"):
                    recovery._contain_cancelled_resume_and_wake(
                        binding,
                        str(batch["wake_batch_id"]),
                        resume.effect_id,
                        recovery._wake_context(
                            binding.binding_id, str(batch["wake_batch_id"])
                        ),
                    )

        if external_writer is not None:
            external_writer.rollback()
            external_writer.close()
        current = journal.get(resume.effect_id)
        crossed = corruption == "write_started"
        assert current.state == ("SUBMISSION_UNCERTAIN" if crossed else "PREPARED")
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
        assert all(
            seeded["mailbox"].get(message.message_id).delivery_state.value == "BATCHED"
            for message in messages
        )
        assert client.send_count == 0
        assert client._pending == {}
        assert client._committed_claims == {}
        assert owner._send_permits == set()
        assert connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id=?", (current.effect_id,)
        ).fetchone()[0] == (1 if crossed else 0)
        assert connection.execute(
            "SELECT COUNT(*) FROM rpc_requests WHERE effect_id=?", (current.effect_id,)
        ).fetchone()[0] == (1 if crossed else 0)
        assert connection.execute(
            "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id=?",
            (batch["wake_batch_id"],),
        ).fetchone()[0] == 0
        assert not connection.in_transaction
        await owner.close()
        _close_seeded(seeded)

    asyncio.run(body())


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
def test_same_owner_foreign_binding_blocks_resume_submit_before_send(
    tmp_path: Path, foreign_state: str
) -> None:
    async def body() -> None:
        seeded, binding, messages, batches, batch, client, _recovery = _prepared_resume(
            tmp_path, f"review06:resume-submit-foreign-{foreign_state.lower()}"
        )
        journal = EffectJournal(seeded["supervisor"].connection)
        resume = journal.prepare_effect(
            owner_kind="THREAD_RESUME",
            owner_id=binding.binding_id,
            binding_id=binding.binding_id,
            method="thread/resume",
            client_key=f"thread/resume:{binding.thread_id}:{batch['wake_batch_id']}",
            request={"threadId": binding.thread_id},
        )
        foreign_effect_id = f"eff_resume_submit_foreign_{foreign_state.lower()}"
        seeded["supervisor"].connection.execute(
            """INSERT INTO app_server_effects(
                effect_id,owner_kind,owner_id,binding_id,method,client_key,
                request_json,state,prepared_at
            ) VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                foreign_effect_id,
                "THREAD_RESUME",
                binding.binding_id,
                "binding_foreign",
                "thread/resume",
                f"key-{foreign_effect_id}",
                "{}",
                foreign_state,
                "t",
            ),
        )
        seeded["supervisor"].connection.commit()

        owner = AppServerSessionOwner(client, seeded["supervisor"])
        from tools.codex_supervisor.durability.authority_kernel import (
            ResumeMode,
            seal_thread_resume,
        )
        from tools.codex_supervisor.durability.transaction import DurabilityTransaction

        with seeded["supervisor"]._lock, DurabilityTransaction(
            seeded["supervisor"].connection
        ):
            plan = seal_thread_resume(
                seeded["supervisor"].connection,
                resume.effect_id,
                mode=ResumeMode.WAKE_RECOVERY,
                wake_batch_id=str(batch["wake_batch_id"]),
            )
        with pytest.raises((SessionOwnerError, EffectError), match="ownership|ambiguous"):
            await owner.submit_thread_resume(plan)

        assert client.send_count == 0
        assert journal.get(resume.effect_id).state == "PREPARED"
        assert journal.get(foreign_effect_id).state == foreign_state
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
        assert all(
            seeded["mailbox"].get(message.message_id).delivery_state.value == "BATCHED"
            for message in messages
        )
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (resume.effect_id,)
        ).fetchone()[0] == 0
        _close_seeded(seeded)

    asyncio.run(body())

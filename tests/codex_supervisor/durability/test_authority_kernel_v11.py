from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.db import initialize_database
from tools.codex_supervisor.durability.authority_kernel import (
    EphemeralCanaryPlan,
    ManagedTurnPlan,
    ThreadMemoryPlan,
    ThreadProvisionPlan,
    ThreadResumePlan,
    WakeBatchPlan,
    seal_wake_batch,
)
from tools.codex_supervisor.durability.effects import EffectError, EffectJournal
from tools.codex_supervisor.durability.session_owner import AppServerSessionOwner
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.mailbox_models import MailboxMessageKind
from tools.codex_supervisor.wake_batches import WakeBatchStore
from tools.codex_supervisor.wake_scheduler import WakeScheduler


class _NoSendClient:
    def __init__(self) -> None:
        self.server_requests = asyncio.Queue()
        self.send_count = 0
        self.discard_count = 0

    def prepare_request(self, method, params=None):
        request = dict(params or {})
        return SimpleNamespace(
            request_id="1",
            method=method,
            params=request,
            payload={"id": 1, "method": method, "params": request},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
        )

    def discard_prepared(self, _prepared) -> None:
        self.discard_count += 1

    async def send_prepared(self, _prepared) -> None:
        self.send_count += 1
        raise AssertionError("failed authority proof reached the network")

    async def await_prepared(self, _prepared):  # pragma: no cover
        raise AssertionError("failed authority proof awaited a response")


def _prepared_wake(tmp_path: Path, key: str = "v11"):
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    message = seeded["mailbox"].enqueue(
        source_system="OPERATOR",
        source_event_key=f"authority:{key}",
        target_actor_context_id=seeded["portfolio"].actor_context_id,
        message_kind=MailboxMessageKind.OPERATOR_ATTENTION_REQUEST,
        subject_ref="subject",
        payload_ref="payload",
    )
    batches = WakeBatchStore(seeded["supervisor"], seeded["mailbox"])
    batch = batches.prepare(
        binding_id=binding_id,
        thread_id="thr_port",
        snapshot=seeded["bridge"].snapshot(
            seeded["portfolio"].actor_context_id
        ),
        messages=[message],
        lease_holder="kernel-test",
        lease_generation=1,
    )
    with seeded["supervisor"]._lock, DurabilityTransaction(
        seeded["supervisor"].connection
    ):
        plan = seal_wake_batch(
            seeded["supervisor"].connection,
            str(batch["wake_batch_id"]),
            "kernel-test",
            1,
        )
    return seeded, batches, message, batch, plan


def _close(seeded) -> None:
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_v11_schema_seals_exact_wake_bytes_and_rejects_mutation(tmp_path: Path) -> None:
    seeded, _batches, _message, batch, plan = _prepared_wake(tmp_path)
    connection = seeded["supervisor"].connection
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(app_server_effects)")
    }
    assert {"request_sha256", "request_byte_length", "sealed_at", "plan_version"} <= columns
    injection = connection.execute(
        """SELECT input_bytes,input_sha256,input_byte_length
        FROM managed_context_injections WHERE injection_id=?""",
        (plan.context_injection_id,),
    ).fetchone()
    assert injection is not None
    exact = bytes(injection["input_bytes"])
    assert hashlib.sha256(exact).hexdigest() == injection["input_sha256"]
    assert len(exact) == injection["input_byte_length"]
    assert plan.request_sha256 == hashlib.sha256(plan.request_bytes).hexdigest()
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute(
            "UPDATE app_server_effects SET client_key='foreign' WHERE effect_id=?",
            (batch["effect_id"],),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute(
            "UPDATE managed_context_injections SET input_bytes=? WHERE injection_id=?",
            (b"x" * len(exact), plan.context_injection_id),
        )
    _close(seeded)


def test_same_length_wake_replacement_rolls_back_every_typed_operation(tmp_path: Path) -> None:
    async def body() -> None:
        seeded, batches, message, batch, plan = _prepared_wake(tmp_path, "same-length")
        request = json.loads(plan.request_bytes.decode("utf-8"))
        text = request["input"][0]["text"]
        request["input"][0]["text"] = ("X" if text[0] != "X" else "Y") + text[1:]
        altered = json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
        assert len(altered) == len(plan.request_bytes)
        stale = replace(
            plan,
            request_bytes=altered,
            request_sha256=hashlib.sha256(altered).hexdigest(),
        )
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, seeded["supervisor"])  # type: ignore[arg-type]
        with pytest.raises(EffectError, match="seal changed"):
            await owner.submit_wake_batch(stale)
        assert client.send_count == 0
        assert client.discard_count == 1
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
        assert seeded["mailbox"].get(message.message_id).delivery_state.value == "BATCHED"
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "PREPARED"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id=?", (batch["effect_id"],)
        ).fetchone()[0] == 0
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id=?",
            (batch["wake_batch_id"],),
        ).fetchone()[0] == 0
        _close(seeded)

    asyncio.run(body())


def test_foreign_owner_at_final_boundary_has_zero_durable_or_external_effect(
    tmp_path: Path,
) -> None:
    async def body() -> None:
        seeded, batches, message, batch, plan = _prepared_wake(tmp_path, "foreign")
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, seeded["supervisor"])  # type: ignore[arg-type]

        def inject(_plan) -> None:
            seeded["supervisor"].connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id,owner_kind,owner_id,binding_id,method,client_key,
                    request_json,state,prepared_at
                ) VALUES ('eff_foreign_final','WAKE_BATCH',?, 'foreign-binding',
                          'turn/start','foreign-key','{}','PREPARED','t')""",
                (plan.owner_id,),
            )

        owner._before_final_authority_proof = inject  # type: ignore[method-assign]
        with pytest.raises(EffectError, match="ambiguous"):
            await owner.submit_wake_batch(plan)
        assert client.send_count == 0
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
        assert seeded["mailbox"].get(message.message_id).delivery_state.value == "BATCHED"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM app_server_effects WHERE effect_id='eff_foreign_final'"
        ).fetchone()[0] == 0
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id=?", (batch["effect_id"],)
        ).fetchone()[0] == 0
        _close(seeded)

    asyncio.run(body())


def test_outer_semantic_commit_failure_is_crossed_uncertainty_not_requeue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def body() -> None:
        seeded, batches, message, batch, plan = _prepared_wake(tmp_path, "outer-commit")
        bridge = seeded["bridge"]
        original = bridge.currentness_guard

        @contextmanager
        def fail_after_supervisor_commit(*args, **kwargs):
            with original(*args, **kwargs) as snapshot:
                yield snapshot
                raise RuntimeError("outer semantic commit failed")

        monkeypatch.setattr(bridge, "currentness_guard", fail_after_supervisor_commit)
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, seeded["supervisor"])  # type: ignore[arg-type]
        with pytest.raises(RuntimeError, match="outer semantic"):
            await owner.submit_wake_batch(plan)
        assert client.send_count == 0
        assert batches.get(str(batch["wake_batch_id"]))["state"] == "SUBMITTING"
        assert seeded["mailbox"].get(message.message_id).delivery_state.value == "BATCHED"
        assert EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        ).state == "SUBMISSION_UNCERTAIN"
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id=?", (batch["effect_id"],)
        ).fetchone()[0] == 1
        _close(seeded)

    asyncio.run(body())


def test_v11_migration_cancels_missing_managed_input_idempotently(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    connection = seeded["supervisor"].connection
    binding_id = str(seeded["portfolio_binding_id"])
    effect = EffectJournal(connection).prepare_effect(
        owner_kind="MANAGED_TURN",
        owner_id="legacy-intent",
        binding_id=binding_id,
        method="turn/start",
        client_key="hmasd-managed:legacy-intent",
        request={"threadId": "thr_port", "clientUserMessageId": "hmasd-managed:legacy-intent"},
    )
    connection.execute(
        """INSERT INTO managed_turn_intents(
            turn_intent_id,binding_id,intent_kind,client_user_message_id,input_ref,
            submission_state,app_server_thread_id,prepared_at,effect_id
        ) VALUES ('legacy-intent',?,'MANUAL_OPERATOR',?,'legacy','PREPARED',
                  'thr_port','t',?)""",
        (binding_id, "hmasd-managed:legacy-intent", effect.effect_id),
    )
    connection.execute("DELETE FROM schema_meta WHERE version=11")
    connection.execute(
        "INSERT OR IGNORE INTO schema_meta(version,applied_at) VALUES (10,'legacy')"
    )
    connection.commit()
    initialize_database(connection)
    first = (
        EffectJournal(connection).get(effect.effect_id).state,
        connection.execute(
            "SELECT submission_state FROM managed_turn_intents WHERE turn_intent_id='legacy-intent'"
        ).fetchone()[0],
    )
    initialize_database(connection)
    second = (
        EffectJournal(connection).get(effect.effect_id).state,
        connection.execute(
            "SELECT submission_state FROM managed_turn_intents WHERE turn_intent_id='legacy-intent'"
        ).fetchone()[0],
    )
    assert first == second == ("CANCELLED_BEFORE_WRITE", "CANCELLED")
    _close(seeded)


def test_static_closed_union_and_no_generic_submission_surface() -> None:
    assert list(inspect.signature(WakeScheduler.submit_batch).parameters) == [
        "self",
        "wake_batch_id",
        "lease_generation",
    ]
    assert not hasattr(AppServerSessionOwner, "submit_effect")
    assert not hasattr(EffectJournal, "claim_write")
    plan_types = (
        ManagedTurnPlan,
        WakeBatchPlan,
        ThreadProvisionPlan,
        ThreadResumePlan,
        ThreadMemoryPlan,
        EphemeralCanaryPlan,
    )
    for plan_type in plan_types:
        annotations = " ".join(str(field.type) for field in fields(plan_type))
        assert "Callable" not in annotations
        assert "Mapping" not in annotations
    package = Path(__file__).parents[3] / "tools" / "codex_supervisor"
    production = "\n".join(
        path.read_text(encoding="utf-8") for path in package.rglob("*.py")
    )
    for forbidden in (
        "request_override",
        "extra_hooks",
        "extra_transitions",
        "pre_write_guard",
        "final_owner_guard",
        "record_effect_write_start",
    ):
        assert forbidden not in production

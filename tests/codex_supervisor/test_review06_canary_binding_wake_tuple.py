import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.test_wake_scheduler import (
    _close_raw_failure_wake,
    _prepared_raw_failure_wake,
)
from tools.codex_supervisor.binding_store import BindingError
from tools.codex_supervisor.canary_contract import (
    canonical_canary_thread_start_request,
    canonical_canary_turn_start_request,
)
from tools.codex_supervisor.durability.effects import (
    EffectError,
    EffectJournal,
    cancel_prepared_wake,
)
from tools.codex_supervisor.durability.session_owner import (
    AppServerSessionOwner,
    SessionOwnerError,
)
from tools.codex_supervisor.mailbox_store import MailboxStoreError
from tools.codex_supervisor.managed_models import BindingState
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.wake_recovery import WakeRecovery


class _CanaryProofGapClient:
    def __init__(self, connection, owner_id: str) -> None:
        self.connection = connection
        self.owner_id = owner_id
        self.server_requests = asyncio.Queue()
        self.discard_count = 0
        self.send_count = 0

    def start_reader(self) -> None:
        return None

    def prepare_request(self, method, params=None):
        self.connection.execute(
            """INSERT INTO app_server_effects(
                effect_id,owner_kind,owner_id,binding_id,method,client_key,
                request_json,state,response_json,prepared_at
            ) VALUES ('eff_canary_foreign','EPHEMERAL_CANARY',?,
                      'binding_foreign','thread/start','foreign-canary-key',
                      '{}','RESPONSE_OBSERVED','{}','t')""",
            (self.owner_id,),
        )
        self.connection.commit()
        return SimpleNamespace(
            request_id="canary-proof-gap",
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
        raise AssertionError("ambiguous canary must stop before send")


def test_canary_turn_reproves_one_exact_predecessor_at_final_write_boundary(
    tmp_path: Path,
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        run_id = store.start_run(
            codex_binary="codex",
            codex_version="test",
            client_name="canary-test",
            process_id=None,
        )
        journal = EffectJournal(store.connection)
        owner_id = "canary_abcdef0123456789abcdef0123456789"
        predecessor = journal.prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=owner_id,
            binding_id=None,
            method="thread/start",
            client_key=f"canary:thread/start:{owner_id}",
            request=canonical_canary_thread_start_request(tmp_path, owner_id),
        )
        journal.claim_write(
            predecessor.effect_id,
            run_id=run_id,
            client_request_id="req-thread",
            request_row_id="row-thread",
            raw_request_seq=1,
        )
        journal.observe_response(
            predecessor.effect_id,
            response={"result": {"thread": {"id": "thr_canary", "ephemeral": True}}},
            thread_id="thr_canary",
        )
        turn = journal.prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=owner_id,
            binding_id=None,
            predecessor_effect_id=predecessor.effect_id,
            method="turn/start",
            client_key=f"canary:turn/start:{owner_id}",
            request=canonical_canary_turn_start_request("thr_canary"),
        )
        client = _CanaryProofGapClient(store.connection, owner_id)
        owner = AppServerSessionOwner(client, store)

        with pytest.raises(SessionOwnerError, match="predecessor ownership is not exact"):
            await owner.submit_effect(turn.effect_id)

        assert journal.get(turn.effect_id).state == "PREPARED"
        assert client.discard_count == 1
        assert client.send_count == 0
        assert store.connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (turn.effect_id,)
        ).fetchone()[0] == 0
        assert store.connection.execute(
            "SELECT COUNT(*) FROM rpc_requests WHERE effect_id = ?", (turn.effect_id,)
        ).fetchone()[0] == 0
        store.close()

    asyncio.run(body())


@pytest.mark.parametrize(
    "state",
    ["PREPARED", "WRITE_STARTED", "RESPONSE_OBSERVED", "SUBMISSION_UNCERTAIN", "INCIDENT"],
)
@pytest.mark.parametrize("action", ["suspend", "revoke"])
def test_public_binding_state_mutation_rejects_every_open_effect_state(
    tmp_path: Path, state: str, action: str
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    connection = seeded["supervisor"].connection
    effect_id = f"eff_public_{action}_{state.lower()}"
    connection.execute(
        """INSERT INTO app_server_effects(
            effect_id,owner_kind,owner_id,binding_id,method,client_key,
            request_json,state,prepared_at
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            effect_id,
            "THREAD_MEMORY",
            binding_id,
            binding_id,
            "thread/memoryMode/set",
            effect_id,
            "{}",
            state,
            "t",
        ),
    )
    connection.commit()

    with pytest.raises(BindingError, match=f"cannot be {action}"):
        getattr(seeded["bindings"], action)(binding_id)

    assert seeded["bindings"].get(binding_id).binding_state is BindingState.ACTIVE
    assert EffectJournal(connection).get(effect_id).state == state
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize("action", ["suspend", "revoke"])
def test_public_binding_state_mutation_without_open_effect_remains_valid(
    tmp_path: Path, action: str
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    updated = getattr(seeded["bindings"], action)(binding_id)
    expected = BindingState.SUSPENDED if action == "suspend" else BindingState.REVOKED
    assert updated.binding_state is expected
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize("action", ["suspend", "revoke"])
def test_public_binding_state_mutation_leaves_prepared_wake_graph_unchanged(
    tmp_path: Path, action: str
) -> None:
    seeded, _scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(tmp_path, f"public-{action}-prepared-wake")
    )
    binding_id = str(batch["binding_id"])
    with pytest.raises(BindingError, match=f"cannot be {action}"):
        getattr(seeded["bindings"], action)(binding_id)
    assert seeded["bindings"].get(binding_id).binding_state is BindingState.ACTIVE
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
    assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
    assert EffectJournal(seeded["supervisor"].connection).get(
        str(batch["effect_id"])
    ).state == "PREPARED"
    _close_raw_failure_wake(seeded)


@pytest.mark.parametrize(
    "tamper",
    [
        "batch_thread",
        "binding_thread",
        "effect_method",
        "effect_client_key",
        "request_thread",
        "request_user_message",
        "request_approval_policy",
        "request_input_length",
        "message_target",
        "message_membership",
    ],
)
def test_base_prepared_wake_cancellation_proves_complete_durable_tuple(
    tmp_path: Path, tamper: str
) -> None:
    seeded, _scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(tmp_path, f"tuple-{tamper}")
    )
    connection = seeded["supervisor"].connection
    batch_id = str(batch["wake_batch_id"])
    effect_id = str(batch["effect_id"])
    if tamper == "batch_thread":
        connection.execute(
            "UPDATE wake_batches SET thread_id='thr_tampered' WHERE wake_batch_id=?",
            (batch_id,),
        )
    elif tamper == "binding_thread":
        connection.execute(
            "UPDATE managed_actor_bindings SET thread_id='thr_tampered' WHERE binding_id=?",
            (batch["binding_id"],),
        )
    elif tamper == "effect_method":
        connection.execute(
            "UPDATE app_server_effects SET method='thread/start' WHERE effect_id=?",
            (effect_id,),
        )
    elif tamper == "effect_client_key":
        connection.execute(
            "UPDATE app_server_effects SET client_key='tampered' WHERE effect_id=?",
            (effect_id,),
        )
    elif tamper in {
        "request_thread",
        "request_user_message",
        "request_approval_policy",
        "request_input_length",
    }:
        request = {
            "threadId": "thr_tampered" if tamper == "request_thread" else batch["thread_id"],
            "clientUserMessageId": (
                "tampered" if tamper == "request_user_message" else batch["client_user_message_id"]
            ),
        }
        if tamper == "request_approval_policy":
            request["approvalPolicy"] = "workspace-write"
        elif tamper == "request_input_length":
            request["approvalPolicy"] = "never"
            request["input"] = [{"type": "text", "text": "wrong"}]
        connection.execute(
            "UPDATE app_server_effects SET request_json=? WHERE effect_id=?",
            (json.dumps(request, sort_keys=True), effect_id),
        )
    elif tamper == "message_target":
        connection.execute(
            "UPDATE mailbox_messages SET target_actor_context_id='actor_tampered' WHERE message_id=?",
            (message.message_id,),
        )
    elif tamper == "message_membership":
        connection.execute(
            """INSERT INTO wake_batches(
                wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at
            ) VALUES ('wake_foreign_membership',?,'thr_root','PREPARED',
                      'hmasd-wake:wake_foreign_membership','t')""",
            (seeded["root_binding_id"],),
        )
        connection.execute(
            """INSERT INTO wake_batch_messages(wake_batch_id,message_id,ordinal)
            VALUES ('wake_foreign_membership',?,0)""",
            (message.message_id,),
        )
    connection.commit()

    with pytest.raises(EffectError):
        cancel_prepared_wake(connection, batch_id, cause_ref=f"tamper-{tamper}")

    assert batches.get(batch_id)["state"] == "PREPARED"
    assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
    assert EffectJournal(connection).get(effect_id).state == "PREPARED"
    _close_raw_failure_wake(seeded)


@pytest.mark.parametrize("surface", ["restart", "source_resolution"])
def test_inherited_wake_cancellation_surfaces_use_same_strict_tuple_proof(
    tmp_path: Path, surface: str
) -> None:
    seeded, _scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(tmp_path, f"tuple-inherited-{surface}")
    )
    connection = seeded["supervisor"].connection
    batch_id = str(batch["wake_batch_id"])
    connection.execute(
        "UPDATE wake_batches SET thread_id='thr_tampered' WHERE wake_batch_id=?",
        (batch_id,),
    )
    connection.commit()

    if surface == "restart":
        recovery = WakeRecovery(seeded["bindings"], mailbox, batches, client=None)  # type: ignore[arg-type]
        with pytest.raises(EffectError):
            asyncio.run(recovery.reconcile_batch(batch_id))
    else:
        with pytest.raises(MailboxStoreError):
            mailbox.cancel_prepared_batch_source_resolved(batch_id, {message.message_id})

    assert batches.get(batch_id)["state"] == "PREPARED"
    assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
    _close_raw_failure_wake(seeded)


def test_valid_base_wake_cancellation_remains_compatible(tmp_path: Path) -> None:
    seeded, _scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(tmp_path, "tuple-valid")
    )
    connection = seeded["supervisor"].connection
    batch_id = str(batch["wake_batch_id"])
    cancel_prepared_wake(connection, batch_id, cause_ref="valid-tuple")
    assert batches.get(batch_id)["state"] == "CANCELLED"
    assert mailbox.get(message.message_id).delivery_state.value == "ELIGIBLE"
    assert EffectJournal(connection).get(str(batch["effect_id"])).state == "CANCELLED_BEFORE_WRITE"
    _close_raw_failure_wake(seeded)

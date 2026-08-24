import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tests.codex_supervisor.helpers import insert_submittable_owner_for_effect
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tests.codex_supervisor.test_wake_scheduler import (
    _close_raw_failure_wake,
    _prepared_raw_failure_wake,
)
from tools.codex_supervisor.canary_contract import (
    canonical_canary_thread_start_request,
    canonical_canary_turn_start_request,
)
from tools.codex_supervisor.binding_store import BindingError
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.managed_models import (
    HistoryTrust,
    ManagedIntentKind,
    ThreadOrigin,
)
from tools.codex_supervisor.managed_turns import ManagedTurns
from tools.codex_supervisor.durability.authority_kernel import (
    CanaryPhase,
    ResumeMode,
    seal_ephemeral_canary,
    seal_managed_turn,
    seal_thread_memory,
    seal_thread_provision,
    seal_thread_resume,
)
from tools.codex_supervisor.durability.transaction import DurabilityTransaction
from tools.codex_supervisor.durability.effects import (
    EffectError,
    EffectJournal,
    cancel_prepared_wake,
)
from tools.codex_supervisor.durability.session_owner import (
    AppServerSessionOwner,
    SessionOwnerError,
)
from tools.codex_supervisor.store import ObserverStore
from tools.codex_supervisor.mailbox_store import MailboxStoreError
from tools.codex_supervisor.managed_models import BindingState
from tools.codex_supervisor.wake_recovery import WakeRecovery
from tools.codex_supervisor.wake_scheduler import WakeSchedulerError


CANARY_ID = "canary_0123456789abcdef0123456789abcdef"
CANARY_THREAD_ID = "thr_final_write_canary"


def _insert_foreign_owner_effect(
    connection,
    *,
    effect_id: str,
    owner_kind: str,
    owner_id: str,
    state: str,
    binding_id: str = "binding_foreign",
) -> None:
    connection.execute(
        """INSERT INTO app_server_effects(
            effect_id,owner_kind,owner_id,binding_id,method,client_key,
            request_json,state,prepared_at
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            effect_id,
            owner_kind,
            owner_id,
            binding_id,
            "turn/start" if owner_kind == "WAKE_BATCH" else "thread/memoryMode/set",
            f"key-{effect_id}",
            "{}",
            state,
            "t",
        ),
    )
    connection.commit()


def _assert_wake_unchanged(seeded, batches, mailbox, message, batch) -> None:
    connection = seeded["supervisor"].connection
    assert batches.get(str(batch["wake_batch_id"]))["state"] == "PREPARED"
    assert mailbox.get(message.message_id).delivery_state.value == "BATCHED"
    assert EffectJournal(connection).get(str(batch["effect_id"])).state == "PREPARED"
    assert connection.execute(
        "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (batch["effect_id"],)
    ).fetchone()[0] == 0


class _FinalBoundaryInterleavingClient:
    def __init__(self, connection, batch, foreign_state: str) -> None:
        self.connection = connection
        self.batch = batch
        self.foreign_state = foreign_state
        self.server_requests = asyncio.Queue()
        self.discard_count = 0
        self.send_count = 0

    def start_reader(self) -> None:
        return None

    def prepare_request(self, method, params=None):
        # SessionOwner's initial proof already completed.  This deterministic
        # insertion lands immediately before record_effect_write_start owns its
        # BEGIN IMMEDIATE transaction.
        _insert_foreign_owner_effect(
            self.connection,
            effect_id=f"eff_final_foreign_{self.foreign_state.lower()}",
            owner_kind="WAKE_BATCH",
            owner_id=str(self.batch["wake_batch_id"]),
            state=self.foreign_state,
        )
        return SimpleNamespace(
            request_id="final-boundary-1",
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
        raise AssertionError("final ownership reproof must stop before send")


class _GenericFinalInterleavingClient(_FinalBoundaryInterleavingClient):
    def __init__(self, connection, effect, foreign_state: str) -> None:
        self.connection = connection
        self.effect = effect
        self.foreign_state = foreign_state
        self.server_requests = asyncio.Queue()
        self.discard_count = 0
        self.send_count = 0

    def prepare_request(self, method, params=None):
        _insert_foreign_owner_effect(
            self.connection,
            effect_id=f"eff_all_paths_{self.effect.owner_kind.lower()}_{self.foreign_state.lower()}",
            owner_kind=self.effect.owner_kind,
            owner_id=self.effect.owner_id,
            state=self.foreign_state,
        )
        return SimpleNamespace(
            request_id="all-paths-final-1",
            method=method,
            params=dict(params or {}),
            payload={"id": 1, "method": method, "params": dict(params or {})},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
        )


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
def test_final_write_transaction_reproof_blocks_interleaved_foreign_owner(
    tmp_path: Path, foreign_state: str
) -> None:
    async def body() -> None:
        seeded, scheduler, batches, mailbox, message, batch, lease = (
            _prepared_raw_failure_wake(tmp_path, f"final-reproof-{foreign_state.lower()}")
        )
        client = _FinalBoundaryInterleavingClient(
            seeded["supervisor"].connection, batch, foreign_state
        )
        scheduler.client = client  # type: ignore[assignment]

        with pytest.raises(WakeSchedulerError, match="containment failed closed"):
            await scheduler.submit_batch(
                str(batch["wake_batch_id"]),
                lease_generation=int(lease["generation"]),
            )

        _assert_wake_unchanged(seeded, batches, mailbox, message, batch)
        assert client.discard_count == 1
        assert client.send_count == 0
        assert seeded["supervisor"].connection.execute(
            "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id = ?",
            (batch["wake_batch_id"],),
        ).fetchone()[0] == 0
        original = EffectJournal(seeded["supervisor"].connection).get(
            str(batch["effect_id"])
        )
        assert "input" in original.request
        foreign_id = f"eff_final_foreign_{foreign_state.lower()}"
        assert EffectJournal(seeded["supervisor"].connection).get(foreign_id).state == foreign_state
        await AppServerSessionOwner._by_client[id(client)].close()
        _close_raw_failure_wake(seeded)

    asyncio.run(body())


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
@pytest.mark.parametrize(
    "variant",
    [
        "MANAGED_TURN",
        "WAKE_BATCH",
        "THREAD_PROVISION",
        "THREAD_MEMORY",
        "THREAD_RESUME_ADOPTION",
        "THREAD_RESUME_WAKE_RECOVERY",
        "EPHEMERAL_CANARY_THREAD_START",
        "EPHEMERAL_CANARY_TURN_START",
    ],
)
def test_every_session_owner_path_reproves_inside_final_write_transaction(
    tmp_path: Path, variant: str, foreign_state: str
) -> None:
    async def body() -> None:
        case_path = tmp_path / f"{variant.lower()}-{foreign_state.lower()}"
        seeded = None
        messages = []
        wake_batch_id = None
        if variant == "WAKE_BATCH":
            seeded, _scheduler, batches, _mailbox, message, batch, _lease = (
                _prepared_raw_failure_wake(case_path, f"matrix-{foreign_state}")
            )
            store = seeded["supervisor"]
            from tools.codex_supervisor.durability.authority_kernel import seal_wake_batch

            with store._lock, DurabilityTransaction(store.connection):
                plan = seal_wake_batch(
                    store.connection,
                    str(batch["wake_batch_id"]),
                    str(batch["lease_holder"]),
                    int(batch["lease_generation"]),
                )
            messages = [message]
            wake_batch_id = str(batch["wake_batch_id"])
        elif variant == "THREAD_RESUME_WAKE_RECOVERY":
            from tests.codex_supervisor.test_review06_cancellation_cleanup import (
                _prepared_resume,
            )

            seeded, binding, messages, batches, batch, _client, _recovery = _prepared_resume(
                case_path, f"matrix-{foreign_state}"
            )
            store = seeded["supervisor"]
            effect = EffectJournal(store.connection).prepare_effect(
                owner_kind="THREAD_RESUME",
                owner_id=binding.binding_id,
                binding_id=binding.binding_id,
                method="thread/resume",
                client_key=f"thread/resume:{binding.thread_id}:{batch['wake_batch_id']}",
                request={"threadId": binding.thread_id},
            )
            with store._lock, DurabilityTransaction(store.connection):
                plan = seal_thread_resume(
                    store.connection,
                    effect.effect_id,
                    mode=ResumeMode.WAKE_RECOVERY,
                    wake_batch_id=str(batch["wake_batch_id"]),
                )
            wake_batch_id = str(batch["wake_batch_id"])
        elif variant in {"THREAD_PROVISION", "THREAD_RESUME_ADOPTION"}:
            seeded = seed_managed_actors(case_path)
            bindings = BindingStore(seeded["supervisor"], seeded["bridge"])
            snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
            binding_id = bindings.prepare_binding(
                snapshot,
                repo_root=str(case_path),
                thread_cwd=str(case_path),
                created_by_operator="test",
                thread_origin=ThreadOrigin.NEW,
                history_trust=HistoryTrust.FRESH,
            )
            store = seeded["supervisor"]
            journal = EffectJournal(store.connection)
            if variant == "THREAD_PROVISION":
                effect = journal.prepare_effect(
                    owner_kind="THREAD_PROVISION",
                    owner_id=binding_id,
                    binding_id=binding_id,
                    method="thread/start",
                    client_key=f"thread/start:{binding_id}",
                    request={
                        "cwd": str(case_path),
                        "ephemeral": False,
                        "approvalPolicy": "never",
                    },
                )
                with store._lock, DurabilityTransaction(store.connection):
                    plan = seal_thread_provision(store.connection, effect.effect_id)
            else:
                effect = journal.prepare_effect(
                    owner_kind="THREAD_RESUME",
                    owner_id=binding_id,
                    binding_id=binding_id,
                    method="thread/resume",
                    client_key="thread/resume:thr-adopt",
                    request={"threadId": "thr-adopt"},
                )
                with store._lock, DurabilityTransaction(store.connection):
                    plan = seal_thread_resume(
                        store.connection, effect.effect_id, mode=ResumeMode.ADOPTION
                    )
        elif variant.startswith("EPHEMERAL_CANARY"):
            store = ObserverStore(case_path)
            run_id = store.start_run(
                codex_binary="codex",
                codex_version="test",
                client_name="matrix-canary",
                process_id=None,
            )
            journal = EffectJournal(store.connection)
            predecessor_id = None
            if variant.endswith("TURN_START"):
                predecessor = journal.prepare_effect(
                    owner_kind="EPHEMERAL_CANARY",
                    owner_id=CANARY_ID,
                    binding_id=None,
                    method="thread/start",
                    client_key=f"canary:thread/start:{CANARY_ID}",
                    request=canonical_canary_thread_start_request(case_path, CANARY_ID),
                )
                journal._claim_write(
                    predecessor.effect_id,
                    run_id=run_id,
                    client_request_id="predecessor",
                    request_row_id="predecessor-row",
                    raw_request_seq=1,
                )
                journal.observe_response(
                    predecessor.effect_id,
                    response={"result": {"thread": {"id": CANARY_THREAD_ID, "ephemeral": True}}},
                    thread_id=CANARY_THREAD_ID,
                )
                predecessor_id = predecessor.effect_id
                method = "turn/start"
                request = canonical_canary_turn_start_request(CANARY_THREAD_ID)
                phase = CanaryPhase.TURN_START
            else:
                method = "thread/start"
                request = canonical_canary_thread_start_request(case_path, CANARY_ID)
                phase = CanaryPhase.THREAD_START
            effect = journal.prepare_effect(
                owner_kind="EPHEMERAL_CANARY",
                owner_id=CANARY_ID,
                binding_id=None,
                predecessor_effect_id=predecessor_id,
                method=method,
                client_key=f"canary:{method}:{CANARY_ID}",
                request=request,
            )
            with store._lock, DurabilityTransaction(store.connection):
                plan = seal_ephemeral_canary(
                    store.connection, effect.effect_id, phase=phase
                )
        else:
            seeded = seed_active_root_portfolio(case_path)
            store = seeded["supervisor"]
            binding_id = str(seeded["portfolio_binding_id"])
            if variant == "MANAGED_TURN":
                turns = ManagedTurns(seeded["bindings"], client=None)  # type: ignore[arg-type]
                intent_id = turns.prepare(
                    binding_id,
                    intent_kind=ManagedIntentKind.MANUAL_OPERATOR,
                    input_ref="matrix",
                )
                with store._lock, DurabilityTransaction(store.connection):
                    plan = seal_managed_turn(store.connection, intent_id, "matrix input")
            else:
                effect = EffectJournal(store.connection).prepare_effect(
                    owner_kind="THREAD_MEMORY",
                    owner_id=binding_id,
                    binding_id=binding_id,
                    method="thread/memoryMode/set",
                    client_key="thread/memoryMode/set:thr_port",
                    request={"threadId": "thr_port", "mode": "disabled"},
                )
                with store._lock, DurabilityTransaction(store.connection):
                    plan = seal_thread_memory(store.connection, effect.effect_id)
                # This matrix isolates the supervisor final boundary from the
                # independently covered semantic-currentness fence.
                store._semantic_bridge = None

        effect = EffectJournal(store.connection).get(plan.effect_id)
        client = _GenericFinalInterleavingClient(store.connection, effect, foreign_state)
        # The matrix owns the exact final-boundary interleaving; preparation
        # itself remains side-effect free.
        client.prepare_request = lambda method, params=None: SimpleNamespace(
            request_id="matrix-1",
            method=method,
            params=dict(params or {}),
            payload={"id": 1, "method": method, "params": dict(params or {})},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
        )
        journal = EffectJournal(store.connection)
        owner = AppServerSessionOwner(client, store)

        def inject_foreign(_plan) -> None:
            store.connection.execute(
                """INSERT INTO app_server_effects(
                    effect_id,owner_kind,owner_id,binding_id,method,client_key,
                    request_json,state,prepared_at
                ) VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    f"eff_matrix_foreign_{foreign_state.lower()}",
                    plan.owner_kind,
                    plan.owner_id,
                    None if plan.binding_id is None else "foreign-binding",
                    plan.method,
                    f"foreign-{variant}-{foreign_state}",
                    "{}",
                    foreign_state,
                    "t",
                ),
            )

        owner._before_final_authority_proof = inject_foreign  # type: ignore[method-assign]
        submit = {
            "MANAGED_TURN": owner.submit_managed_turn,
            "WAKE_BATCH": owner.submit_wake_batch,
            "THREAD_PROVISION": owner.submit_thread_provision,
            "THREAD_MEMORY": owner.submit_thread_memory,
            "THREAD_RESUME_ADOPTION": owner.submit_thread_resume,
            "THREAD_RESUME_WAKE_RECOVERY": owner.submit_thread_resume,
            "EPHEMERAL_CANARY_THREAD_START": owner.submit_ephemeral_canary,
            "EPHEMERAL_CANARY_TURN_START": owner.submit_ephemeral_canary,
        }[variant]
        with pytest.raises(
            EffectError, match="ambiguous|unexpected predecessor or peer"
        ):
            await submit(plan)

        assert journal.get(effect.effect_id).state == "PREPARED"
        assert client.discard_count == 1
        assert client.send_count == 0
        assert effect.effect_id not in owner._open_effect_ids
        assert owner._send_permits == set()
        assert store.connection.execute(
            "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (effect.effect_id,)
        ).fetchone()[0] == 0
        assert store.connection.execute(
            "SELECT COUNT(*) FROM rpc_requests WHERE effect_id = ?", (effect.effect_id,)
        ).fetchone()[0] == 0
        assert store.connection.execute(
            "SELECT COUNT(*) FROM app_server_effects WHERE effect_id LIKE 'eff_matrix_foreign_%'"
        ).fetchone()[0] == 0
        if wake_batch_id is not None:
            assert batches.get(wake_batch_id)["state"] == "PREPARED"
            assert all(
                seeded["mailbox"].get(item.message_id).delivery_state.value == "BATCHED"
                for item in messages
            )
            assert store.connection.execute(
                "SELECT COUNT(*) FROM wake_attempts WHERE wake_batch_id=?",
                (wake_batch_id,),
            ).fetchone()[0] == 0
        if seeded is None:
            store.close()
        elif "bridge" in seeded:
            seeded["bridge"].close()
            seeded["supervisor"].close()
            seeded["semantic"].close()

    asyncio.run(body())


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
@pytest.mark.parametrize("surface", ["base", "restart", "source_resolution"])
def test_strict_wake_cancel_surfaces_roll_back_ambiguous_owner(
    tmp_path: Path, foreign_state: str, surface: str
) -> None:
    seeded, _scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(
            tmp_path, f"strict-{surface}-{foreign_state.lower()}"
        )
    )
    connection = seeded["supervisor"].connection
    foreign_id = f"eff_{surface}_{foreign_state.lower()}"
    _insert_foreign_owner_effect(
        connection,
        effect_id=foreign_id,
        owner_kind="WAKE_BATCH",
        owner_id=str(batch["wake_batch_id"]),
        state=foreign_state,
    )

    if surface == "base":
        with pytest.raises(EffectError):
            cancel_prepared_wake(
                connection, str(batch["wake_batch_id"]), cause_ref="strict-base"
            )
    elif surface == "restart":
        recovery = WakeRecovery(
            seeded["bindings"], mailbox, batches, client=None  # type: ignore[arg-type]
        )
        with pytest.raises(EffectError):
            asyncio.run(recovery.reconcile_batch(str(batch["wake_batch_id"])))
    else:
        with pytest.raises(MailboxStoreError):
            mailbox.cancel_prepared_batch_source_resolved(
                str(batch["wake_batch_id"]), {message.message_id}
            )

    _assert_wake_unchanged(seeded, batches, mailbox, message, batch)
    assert EffectJournal(connection).get(foreign_id).state == foreign_state
    _close_raw_failure_wake(seeded)


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
def test_binding_effect_containment_rolls_back_ambiguous_owner(
    tmp_path: Path, foreign_state: str
) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    connection = seeded["supervisor"].connection
    journal = EffectJournal(connection)
    effect = journal.prepare_effect(
        owner_kind="THREAD_MEMORY",
        owner_id=binding_id,
        binding_id=binding_id,
        method="thread/memoryMode/set",
        client_key=f"memory-contain-{foreign_state.lower()}",
        request={"threadId": "thr_port", "mode": "disabled"},
    )
    foreign_id = f"eff_binding_foreign_{foreign_state.lower()}"
    _insert_foreign_owner_effect(
        connection,
        effect_id=foreign_id,
        owner_kind="THREAD_MEMORY",
        owner_id=binding_id,
        state=foreign_state,
    )

    with pytest.raises(BindingError, match="ownership is not exact"):
        seeded["bindings"].cancel_prepared_binding_effect(
            binding_id, effect.effect_id, cause_ref="ambiguous-binding-containment"
        )

    assert seeded["bindings"].get(binding_id).binding_state is BindingState.ACTIVE
    assert journal.get(effect.effect_id).state == "PREPARED"
    assert journal.get(foreign_id).state == foreign_state
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_binding_containment_without_open_effect_remains_valid(tmp_path: Path) -> None:
    seeded = seed_active_root_portfolio(tmp_path)
    binding_id = str(seeded["portfolio_binding_id"])
    seeded["bindings"].cancel_prepared_binding_effect(
        binding_id, None, cause_ref="valid-no-effect-containment"
    )
    assert seeded["bindings"].get(binding_id).binding_state is BindingState.SUSPENDED
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


@pytest.mark.parametrize("foreign_state", ["PREPARED", "WRITE_STARTED"])
def test_guarded_binding_suspend_rolls_back_when_another_open_effect_exists(
    tmp_path: Path, foreign_state: str
) -> None:
    seeded, scheduler, batches, mailbox, message, batch, _lease = (
        _prepared_raw_failure_wake(tmp_path, f"guarded-contain-{foreign_state.lower()}")
    )
    connection = seeded["supervisor"].connection
    foreign_id = f"eff_bound_foreign_{foreign_state.lower()}"
    _insert_foreign_owner_effect(
        connection,
        effect_id=foreign_id,
        owner_kind="EPHEMERAL_CANARY",
        owner_id=f"canary-{foreign_state.lower()}",
        binding_id=str(batch["binding_id"]),
        state=foreign_state,
    )

    with pytest.raises(EffectError):
        scheduler._contain_guarded_ineligible_actor(
            str(batch["binding_id"]),
            str(batch["wake_batch_id"]),
            str(batch["effect_id"]),
        )

    assert seeded["bindings"].get(str(batch["binding_id"])).binding_state is BindingState.ACTIVE
    _assert_wake_unchanged(seeded, batches, mailbox, message, batch)
    assert EffectJournal(connection).get(foreign_id).state == foreign_state
    _close_raw_failure_wake(seeded)

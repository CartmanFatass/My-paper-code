from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tests.codex_supervisor.semantic_fixtures import seed_managed_actors
from tools.codex_supervisor.binding_store import BindingStore
from tools.codex_supervisor.client import AppServerClient
from tools.codex_supervisor.durability.effects import EffectJournal
from tools.codex_supervisor.durability.models import EffectState
from tools.codex_supervisor.managed_models import HistoryTrust, ManagedIntentKind, SubmissionState, ThreadOrigin
from tools.codex_supervisor.managed_turns import ManagedTurnError, ManagedTurns
from tools.codex_supervisor.transport import AppServerTransport


def _run(coro):
    return asyncio.run(coro)


def _turns(tmp_path: Path, mode: str = "handshake_ok") -> tuple[ManagedTurns, BindingStore, dict]:
    seeded = seed_managed_actors(tmp_path)
    store = BindingStore(seeded["supervisor"], seeded["bridge"])
    snapshot = seeded["bridge"].snapshot(seeded["root"].actor_context_id)
    binding_id = store.prepare_binding(
        snapshot,
        repo_root=str(tmp_path),
        thread_cwd=str(tmp_path),
        created_by_operator="operator",
        thread_origin=ThreadOrigin.NEW,
        history_trust=HistoryTrust.FRESH,
    )
    store.attach_thread_for_tests(binding_id, "thr_canary")
    store.mark_verification_required(binding_id)
    config = make_observer_config(tmp_path)
    transport = AppServerTransport(
        write_fake_codex(tmp_path),
        config,
        tmp_path,
        tmp_path / "err.log",
        extra_env={"FAKE_APP_SERVER_MODE": mode},
        stdin_close_timeout=0.4,
        terminate_timeout=0.4,
    )
    client = AppServerClient(transport, config)
    return ManagedTurns(store, client), store, {"transport": transport, "binding_id": binding_id, "seeded": seeded}


def test_new_managed_turn_is_prepared_not_submitting(tmp_path: Path) -> None:
    turns, store, ctx = _turns(tmp_path)
    intent_id = turns.prepare(ctx["binding_id"], intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
    row = turns._row(intent_id)
    assert row["submission_state"] == SubmissionState.PREPARED.value
    journal = EffectJournal(store.store.connection)
    effect = journal.get(str(row["effect_id"]))
    assert effect.state == EffectState.PREPARED.value
    seeded = ctx["seeded"]
    seeded["bridge"].close()
    seeded["supervisor"].close()
    seeded["semantic"].close()


def test_managed_turn_write_started_is_never_resubmitted(tmp_path: Path) -> None:
    async def body() -> None:
        turns, store, ctx = _turns(tmp_path)
        await ctx["transport"].start()
        await turns.client.initialize()
        intent_id = turns.prepare(ctx["binding_id"], intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        row = await turns.submit(intent_id, "hello")
        assert row["submission_state"] == SubmissionState.OBSERVED.value
        with pytest.raises(ManagedTurnError, match="not PREPARED"):
            await turns.submit(intent_id, "hello")
        journal = EffectJournal(store.store.connection)
        effect = journal.get(str(row["effect_id"]))
        assert effect.state != EffectState.PREPARED.value
        with pytest.raises(Exception):
            journal.claim_write(
                effect.effect_id,
                run_id="runx",
                client_request_id="x",
                request_row_id="r",
                raw_request_seq=9,
            )
        await ctx["transport"].stop()
        seeded = ctx["seeded"]
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_managed_turn_timeout_reconciles_by_original_client_key(tmp_path: Path) -> None:
    async def body() -> None:
        turns, store, ctx = _turns(tmp_path, "mutation_overload")
        await ctx["transport"].start()
        await turns.client.initialize()
        intent_id = turns.prepare(ctx["binding_id"], intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        with pytest.raises(ManagedTurnError, match="uncertain"):
            await turns.submit(intent_id, "hello")
        row = turns._row(intent_id)
        assert row["submission_state"] == SubmissionState.SUBMISSION_UNCERTAIN.value
        journal = EffectJournal(store.store.connection)
        assert journal.get(str(row["effect_id"])).state == EffectState.SUBMISSION_UNCERTAIN.value
        await ctx["transport"].stop()
        seeded = ctx["seeded"]
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_managed_turn_incident_is_terminal(tmp_path: Path) -> None:
    async def body() -> None:
        turns, store, ctx = _turns(tmp_path, "server_request_on_turn")
        await ctx["transport"].start()
        await turns.client.initialize()
        intent_id = turns.prepare(ctx["binding_id"], intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        with pytest.raises(ManagedTurnError, match="incident"):
            await turns.submit(intent_id, "hello")
        row = turns._row(intent_id)
        assert row["submission_state"] == SubmissionState.INCIDENT.value
        with pytest.raises(ManagedTurnError, match="incident"):
            await turns.reconcile_uncertain(intent_id)
        with pytest.raises(ManagedTurnError, match="incident"):
            turns.record_completion(intent_id, "completed")
        await ctx["transport"].stop()
        seeded = ctx["seeded"]
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())


def test_managed_turn_effect_and_domain_state_never_diverge(tmp_path: Path) -> None:
    async def body() -> None:
        turns, store, ctx = _turns(tmp_path)
        await ctx["transport"].start()
        await turns.client.initialize()
        intent_id = turns.prepare(ctx["binding_id"], intent_kind=ManagedIntentKind.BOOTSTRAP, input_ref="bootstrap")
        row = await turns.submit(intent_id, "hello")
        journal = EffectJournal(store.store.connection)
        effect = journal.get(str(row["effect_id"]))
        assert row["submission_state"] == SubmissionState.OBSERVED.value
        assert effect.state == EffectState.EFFECT_CONFIRMED.value
        await ctx["transport"].stop()
        seeded = ctx["seeded"]
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()

    _run(body())

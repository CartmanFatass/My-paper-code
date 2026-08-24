"""MCP acceptance for the typed responsibility and provider lifecycle adapter."""

from __future__ import annotations

import ast
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import anyio
from mcp.client import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.memory import create_client_server_memory_streams

from tools.codex_context_lifecycle.authority import bind_requester, grant_user_authority
from tools.codex_context_lifecycle.models import ContextSourceKind, PrecedenceLayer
from tools.codex_context_lifecycle.precedence import (
    can_create_authority,
    can_create_state_transition,
    precedence_for_kind,
)
from tools.codex_semantic_mvp import mcp_server
from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import (
    DEFAULT_PORTFOLIO_SESSION_ID,
    load_actor_mapping,
    register_child_actor,
    register_session_root,
    release_actor_context,
)
from tools.codex_semantic_mvp.store import SemanticStore

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project runtime
    import tomli as tomllib


PYTHON = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
REPO_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_SESSION = "01a02b11-f3da-7022-b821-a33f9c7e0bac"
HISTORICAL_PORTFOLIO_SESSION = "019ffc20-5001-7453-a08a-dac783cf4d80"
NEW_TOOLS = (
    "responsibility_handoff_open",
    "responsibility_handoff_accept",
    "responsibility_scheduled_record",
    "responsibility_idle_complete_record",
    "responsibility_local_boundary_record",
    "responsibility_orphan_detect",
    "responsibility_orphan_assign",
    "provider_transaction_classify",
    "provider_recovery_resend_authorize",
)
AUTHORITY_FIELDS = {
    "source_kind",
    "requester_actor_context_id",
    "user_authority_id",
}


def run(coro):
    return anyio.run(coro)


def _actors(store: SemanticStore) -> SimpleNamespace:
    portfolio = register_session_root(store, session_id=PORTFOLIO_SESSION)
    root = register_session_root(store, session_id="typed-adapter-root")
    em = register_child_actor(
        store,
        session_id="typed-adapter-em",
        actor_kind=ActorKind.EM,
        scope_key="direction:typed-adapter",
        direction_id="typed-adapter",
        parent_actor_context_id=portfolio.actor_context_id,
    )
    em_other = register_child_actor(
        store,
        session_id="typed-adapter-em-other",
        actor_kind=ActorKind.EM,
        scope_key="direction:typed-adapter-other",
        direction_id="typed-adapter-other",
        parent_actor_context_id=portfolio.actor_context_id,
    )
    cm = register_child_actor(
        store,
        session_id="typed-adapter-cm",
        actor_kind=ActorKind.CM,
        scope_key="direction:typed-adapter:cm",
        direction_id="typed-adapter",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
    )
    operator = register_child_actor(
        store,
        session_id="typed-adapter-operator",
        actor_kind=ActorKind.LEAF,
        scope_key="assignment:typed-adapter-operator",
        direction_id="typed-adapter",
        parent_actor_context_id=cm.actor_context_id,
    )
    recovery = register_child_actor(
        store,
        session_id="typed-adapter-recovery",
        actor_kind=ActorKind.LEAF,
        scope_key="assignment:typed-adapter-recovery",
        direction_id="typed-adapter",
        parent_actor_context_id=root.actor_context_id,
    )
    inactive = register_child_actor(
        store,
        session_id="typed-adapter-inactive",
        actor_kind=ActorKind.LEAF,
        scope_key="assignment:typed-adapter-inactive",
        direction_id="typed-adapter",
        parent_actor_context_id=root.actor_context_id,
    )
    release_actor_context(store, inactive.actor_context_id)
    return SimpleNamespace(
        portfolio=portfolio,
        root=root,
        em=em,
        em_other=em_other,
        cm=cm,
        operator=operator,
        recovery=recovery,
        inactive=inactive,
    )


@asynccontextmanager
async def connected_server(state_dir: Path):
    server = mcp_server.build_server(state_dir)
    actors = _actors(mcp_server._get_store())
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(
                server._lowlevel_server.run,
                server_streams[0],
                server_streams[1],
                server._lowlevel_server.create_initialization_options(),
            )
            async with ClientSession(*client_streams) as client:
                await client.initialize()
                yield client, actors, mcp_server._get_store()
                task_group.cancel_scope.cancel()


def _decode(result) -> dict:
    if result.structured_content:
        return dict(result.structured_content)
    return json.loads(result.content[0].text)


async def _call(client: ClientSession, actor_id: str, name: str, arguments: dict) -> dict:
    bind_requester(actor_id)
    payload = {
        **arguments,
        "source_kind": "ROLE_CONTRACT",
        "requester_actor_context_id": actor_id,
    }
    result = await client.call_tool(name, payload)
    assert not result.is_error, result.content
    return _decode(result)


async def _error(
    client: ClientSession,
    actor_id: str,
    name: str,
    arguments: dict,
    *,
    include_source: bool = True,
):
    bind_requester(actor_id)
    payload = {**arguments, "requester_actor_context_id": actor_id}
    if include_source:
        payload["source_kind"] = "ROLE_CONTRACT"
    result = await client.call_tool(name, payload)
    assert result.is_error
    return result


def _open_actor_workflow(store: SemanticStore, actor_id: str, workflow_id: str) -> str:
    return store.open_actor_workflow(
        actor_id,
        f"turn:{workflow_id}",
        "shared:typed-responsibility-adapter",
        "isolated MCP acceptance",
        workflow_id=workflow_id,
    )


def _handoff(
    *,
    stage: str,
    receiving_owner: str,
    evidence_ref: str,
) -> dict:
    return {
        "stage": stage,
        "receiving_owner": receiving_owner,
        "next_event": f"accept {stage}",
        "evidence_ref": evidence_ref,
        "disposition_reason": "Exact receiver custody remains required.",
        "affected_scope": "direction:typed-adapter",
    }


def test_cm_and_operator_handoff_chains_use_exact_receivers(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with connected_server(tmp_path / "state") as (client, actors, store):
            cm_workflow = _open_actor_workflow(store, actors.cm.actor_context_id, "wf-cm-return")
            opened = await _call(client, actors.cm.actor_context_id, "responsibility_handoff_open", {
                "workflow_id": cm_workflow,
                "subject": "cm:return",
                **_handoff(
                    stage="CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE",
                    receiving_owner=actors.em.actor_context_id,
                    evidence_ref="artifact:cm-return",
                ),
            })
            cm_return = opened["obligation_id"]
            await _error(client, actors.root.actor_context_id, "responsibility_handoff_accept", {
                "workflow_id": cm_workflow,
                "obligation_id": cm_return,
                "next_responsibility": _handoff(
                    stage="SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
                    receiving_owner=actors.portfolio.actor_context_id,
                    evidence_ref="artifact:em-intake",
                ),
            })
            current = store.workflow_state(cm_workflow)["open_obligations"][0]
            assert current["obligation_id"] == cm_return
            assert current["active_worker"] == actors.em.actor_context_id
            assert current["continuation_owner"] == actors.em.actor_context_id
            accepted = await _call(client, actors.em.actor_context_id, "responsibility_handoff_accept", {
                "workflow_id": cm_workflow,
                "obligation_id": cm_return,
                "next_responsibility": _handoff(
                    stage="SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
                    receiving_owner=actors.portfolio.actor_context_id,
                    evidence_ref="artifact:em-intake",
                ),
            })
            portfolio_obligation = accepted["successor_obligation_id"]
            state = await _call(client, actors.em.actor_context_id, "workflow_state", {
                "workflow_id": cm_workflow,
            })
            assert state["open_obligations"][0]["obligation_id"] == portfolio_obligation
            assert state["open_obligations"][0]["primary_queue"] == "PORTFOLIO_DECISION"
            await _call(client, actors.portfolio.actor_context_id, "responsibility_handoff_accept", {
                "workflow_id": cm_workflow,
                "obligation_id": portfolio_obligation,
                "portfolio_accepted": True,
            })
            assert store.workflow_state(cm_workflow)["open_obligations"] == []

            operator_workflow = _open_actor_workflow(
                store, actors.root.actor_context_id, "wf-operator-terminal"
            )
            terminal = (await _call(
                client, actors.root.actor_context_id, "responsibility_handoff_open", {
                    "workflow_id": operator_workflow,
                    "subject": "operator:terminal",
                    **_handoff(
                        stage="OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE",
                        receiving_owner=actors.cm.actor_context_id,
                        evidence_ref="receipt:operator-terminal",
                    ),
                },
            ))["obligation_id"]
            science = (await _call(
                client, actors.cm.actor_context_id, "responsibility_handoff_accept", {
                    "workflow_id": operator_workflow,
                    "obligation_id": terminal,
                    "next_responsibility": _handoff(
                        stage="CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION",
                        receiving_owner=actors.em.actor_context_id,
                        evidence_ref="artifact:cm-technical-intake",
                    ),
                },
            ))["successor_obligation_id"]
            portfolio = (await _call(
                client, actors.em.actor_context_id, "responsibility_handoff_accept", {
                    "workflow_id": operator_workflow,
                    "obligation_id": science,
                    "next_responsibility": _handoff(
                        stage="SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
                        receiving_owner=actors.portfolio.actor_context_id,
                        evidence_ref="artifact:science-reconciliation",
                    ),
                },
            ))["successor_obligation_id"]
            await _call(client, actors.portfolio.actor_context_id, "responsibility_handoff_accept", {
                "workflow_id": operator_workflow,
                "obligation_id": portfolio,
                "portfolio_accepted": True,
            })
            assert store.workflow_state(operator_workflow)["open_obligations"] == []

    run(scenario)


def test_scheduled_idle_local_boundary_and_orphan_projection(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with connected_server(tmp_path / "state") as (client, actors, store):
            workflow_id = _open_actor_workflow(store, actors.root.actor_context_id, "wf-projections")
            root_before = (
                store.workflow_state(workflow_id)["state_version"],
                store.connection.execute(
                    "SELECT COUNT(*) FROM events WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0],
                store.connection.execute(
                    "SELECT COUNT(*) FROM obligations WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0],
            )
            await _error(client, actors.root.actor_context_id, "responsibility_scheduled_record", {
                "workflow_id": workflow_id,
                "subject": "cross-actor:prestart",
                "receiving_owner": actors.em.actor_context_id,
                "continuity_owner": actors.em.actor_context_id,
                "next_event": "EM time gate",
                "evidence_ref": "lease:cross-actor-prestart",
                "disposition_reason": "Cross-actor custody requires an accepted handoff.",
            })
            root_after = (
                store.workflow_state(workflow_id)["state_version"],
                store.connection.execute(
                    "SELECT COUNT(*) FROM events WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0],
                store.connection.execute(
                    "SELECT COUNT(*) FROM obligations WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0],
            )
            assert root_after == root_before
            scheduled = await _call(client, actors.root.actor_context_id, "responsibility_scheduled_record", {
                "workflow_id": workflow_id,
                "subject": "rcle:prestart",
                "receiving_owner": actors.root.actor_context_id,
                "continuity_owner": actors.root.actor_context_id,
                "next_event": "time gate opens",
                "evidence_ref": "lease:prestart",
                "disposition_reason": "The exact future time gate owns continuation.",
            })
            idle_workflow = _open_actor_workflow(
                store, actors.em.actor_context_id, "wf-idle-complete"
            )
            idle_before = (
                store.workflow_state(idle_workflow)["state_version"],
                store.connection.execute(
                    "SELECT COUNT(*) FROM events WHERE workflow_id = ?", (idle_workflow,)
                ).fetchone()[0],
                store.connection.execute(
                    "SELECT COUNT(*) FROM obligations WHERE workflow_id = ?", (idle_workflow,)
                ).fetchone()[0],
            )
            await _error(client, actors.em.actor_context_id, "responsibility_idle_complete_record", {
                "workflow_id": idle_workflow,
                "subject": "science:other-direction-no-current",
                "receiving_owner": actors.em_other.actor_context_id,
                "next_event": "never",
                "evidence_ref": "artifact:other-direction-no-current",
                "disposition_reason": "An EM cannot assign idle custody to another direction.",
                "revisit_condition": "new evidence",
            })
            idle_after = (
                store.workflow_state(idle_workflow)["state_version"],
                store.connection.execute(
                    "SELECT COUNT(*) FROM events WHERE workflow_id = ?", (idle_workflow,)
                ).fetchone()[0],
                store.connection.execute(
                    "SELECT COUNT(*) FROM obligations WHERE workflow_id = ?", (idle_workflow,)
                ).fetchone()[0],
            )
            assert idle_after == idle_before
            idle = await _call(client, actors.em.actor_context_id, "responsibility_idle_complete_record", {
                "workflow_id": idle_workflow,
                "subject": "science:no-current",
                "receiving_owner": actors.em.actor_context_id,
                "next_event": "revisit only on new evidence",
                "evidence_ref": "artifact:no-current",
                "disposition_reason": "No actionable work remains under the frozen condition.",
                "revisit_condition": "new material evidence",
            })
            state = await _call(client, actors.root.actor_context_id, "workflow_state", {
                "workflow_id": workflow_id,
            })
            assert state["open_obligations"] == []
            resolved = {item["obligation_id"]: item for item in state["responsibilities"]}
            assert resolved[scheduled["obligation_id"]]["responsibility"]["continuity_state"] == "DORMANT_SCHEDULED_CONTINUATION"
            idle_state = await _call(client, actors.em.actor_context_id, "workflow_state", {
                "workflow_id": idle_workflow,
            })
            idle_record = next(
                item for item in idle_state["responsibilities"]
                if item["obligation_id"] == idle["obligation_id"]
            )
            assert idle_record["responsibility"]["continuity_state"] == "IDLE_COMPLETE"
            source_actor = store.connection.execute(
                "SELECT source_actor_context_id FROM obligations WHERE obligation_id = ?",
                (idle["obligation_id"],),
            ).fetchone()[0]
            assert source_actor == actors.em.actor_context_id

            local = await _call(client, actors.root.actor_context_id, "responsibility_local_boundary_record", {
                "workflow_id": workflow_id,
                "subject": "provider:local-failure",
                "receiving_owner": actors.em.actor_context_id,
                "active_worker": actors.em.actor_context_id,
                "boundary_domain": "EXTERNAL_REVIEW_BOUNDARY",
                "affected_scope": "provider:transaction",
                "affected_actions": ["reconnect transaction"],
                "unaffected_scopes": ["direction:typed-adapter"],
                "direction_primary_queue": "ACTIVE_SCIENCE",
                "next_event": "EM observes bounded return",
                "evidence_ref": "provider:local-boundary",
                "disposition_reason": "The provider-local failure does not alter the direction queue.",
                "continuation_owner": actors.em.actor_context_id,
            })
            projected = next(
                item for item in store.workflow_state(workflow_id)["open_obligations"]
                if item["obligation_id"] == local["obligation_id"]
            )["responsibility"]
            assert projected["direction_primary_queue"] == "ACTIVE_SCIENCE"
            assert projected["prior_direction_primary_queue"] == "ACTIVE_SCIENCE"

            orphan = await _call(client, actors.root.actor_context_id, "responsibility_orphan_detect", {
                "workflow_id": workflow_id,
                "subject": "material:orphan",
                "next_event": "assign exact recovery custody",
                "evidence_ref": "artifact:orphan",
                "disposition_reason": "Material evidence exists without an active owner.",
            })
            state = store.workflow_state(workflow_id)
            assert state["unowned_stalls"][0]["orphan_id"] == orphan["orphan_id"]
            assigned = await _call(client, actors.root.actor_context_id, "responsibility_orphan_assign", {
                "workflow_id": workflow_id,
                "orphan_id": orphan["orphan_id"],
                "recovery_owner": actors.recovery.actor_context_id,
                "next_event": "recover material custody",
                "evidence_ref": "artifact:orphan-assignment",
                "disposition_reason": "The exact recovery owner now holds material custody.",
            })
            state = store.workflow_state(workflow_id)
            assert state["unowned_stalls"] == []
            assert any(
                item["obligation_id"] == assigned["obligation_id"]
                and item["responsibility"]["receiving_owner"] == actors.recovery.actor_context_id
                for item in state["open_obligations"]
            )

    run(scenario)


def test_provider_classification_and_exact_one_authorization(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with connected_server(tmp_path / "state") as (client, actors, store):
            workflow_id = _open_actor_workflow(store, actors.root.actor_context_id, "wf-provider")
            cases = (
                ("not-committed", False, {}, "SEND_NOT_COMMITTED"),
                ("active", True, {}, "COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN"),
                ("terminal", True, {"terminal_no_response_proved": True}, "COMMITTED_TERMINAL_NO_RESPONSE_PROVED"),
                ("complete", True, {"complete_response_present": True}, "COMPLETE_RESPONSE_PRESENT"),
                ("archive-missing", None, {"local_archive_present": False}, "COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN"),
            )
            for transaction_id, committed, extra, expected in cases:
                result = await _call(client, actors.root.actor_context_id, "provider_transaction_classify", {
                    "workflow_id": workflow_id,
                    "transaction_id": transaction_id,
                    "send_commit_proved": committed,
                    "evidence_ref": f"evidence:{transaction_id}",
                    **extra,
                })
                assert result["classification"]["lifecycle"] == expected
            version_before_idempotent = store.workflow_state(workflow_id)["state_version"]
            await _call(client, actors.root.actor_context_id, "provider_transaction_classify", {
                "workflow_id": workflow_id,
                "transaction_id": "active",
                "send_commit_proved": True,
                "evidence_ref": "evidence:active",
            })
            assert store.workflow_state(workflow_id)["state_version"] == version_before_idempotent

            await _error(client, actors.root.actor_context_id, "provider_transaction_classify", {
                "workflow_id": workflow_id,
                "transaction_id": "complete",
                "send_commit_proved": True,
                "terminal_no_response_proved": True,
                "evidence_ref": "evidence:stale-terminal",
            })
            other_workflow = _open_actor_workflow(
                store, actors.cm.actor_context_id, "wf-provider-other"
            )
            await _error(client, actors.cm.actor_context_id, "provider_transaction_classify", {
                "workflow_id": other_workflow,
                "transaction_id": "active",
                "send_commit_proved": True,
                "evidence_ref": "evidence:active",
            })
            assert store.workflow_state(other_workflow)["provider_transactions"] == []

            for committed, extra, evidence, expected in (
                (False, {}, "evidence:transition-send", "SEND_NOT_COMMITTED"),
                (True, {}, "evidence:transition-active", "COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN"),
                (True, {"terminal_no_response_proved": True}, "evidence:transition-terminal", "COMMITTED_TERMINAL_NO_RESPONSE_PROVED"),
            ):
                transitioned = await _call(
                    client, actors.root.actor_context_id, "provider_transaction_classify", {
                        "workflow_id": workflow_id,
                        "transaction_id": "transition",
                        "send_commit_proved": committed,
                        "evidence_ref": evidence,
                        **extra,
                    },
                )
                assert transitioned["classification"]["lifecycle"] == expected
            authorized = await _call(client, actors.root.actor_context_id, "provider_recovery_resend_authorize", {
                "workflow_id": workflow_id,
                "transaction_id": "terminal",
                "lifecycle": "COMMITTED_TERMINAL_NO_RESPONSE_PROVED",
                "original_frozen_prompt_ref": "prompt:frozen",
                "recovery_frozen_prompt_ref": "prompt:frozen",
                "provenance_ref": "evidence:terminal",
            })
            assert authorized["state"] == "AUTHORIZED"
            await _error(client, actors.root.actor_context_id, "provider_transaction_classify", {
                "workflow_id": workflow_id,
                "transaction_id": "terminal",
                "send_commit_proved": True,
                "terminal_no_response_proved": True,
                "evidence_ref": "evidence:terminal",
            })
            await _error(client, actors.root.actor_context_id, "provider_recovery_resend_authorize", {
                "workflow_id": workflow_id,
                "transaction_id": "terminal",
                "lifecycle": "COMMITTED_TERMINAL_NO_RESPONSE_PROVED",
                "original_frozen_prompt_ref": "prompt:frozen",
                "recovery_frozen_prompt_ref": "prompt:frozen",
                "provenance_ref": "evidence:terminal",
            })
            count = store.connection.execute(
                "SELECT COUNT(*) FROM events WHERE kind = 'PROVIDER_RECOVERY_RESEND_AUTHORIZED'"
            ).fetchone()[0]
            assert count == 1
            projection = {
                item["transaction_id"]: item
                for item in (
                    await _call(client, actors.root.actor_context_id, "workflow_state", {
                        "workflow_id": workflow_id,
                    })
                )["provider_transactions"]
            }
            assert projection["archive-missing"]["classification"]["local_archive_evidence"] == "ABSENT_OR_UNKNOWN_NONPROBATIVE"
            assert projection["complete"]["lifecycle"] == "COMPLETE_RESPONSE_PRESENT"
            assert projection["terminal"]["recovery_resend_authorization"] == {
                "event_id": authorized["authorization_event_id"],
                "lifecycle": "COMMITTED_TERMINAL_NO_RESPONSE_PROVED",
                "frozen_prompt_ref": "prompt:frozen",
                "provenance_ref": "evidence:terminal",
            }

    run(scenario)


def test_authority_rejections_and_generic_resolve_are_write_free(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with connected_server(tmp_path / "state") as (client, actors, store):
            workflow_id = _open_actor_workflow(store, actors.cm.actor_context_id, "wf-authority")

            def snapshot() -> tuple[int, int, int]:
                workflow = store.connection.execute(
                    "SELECT state_version FROM workflows WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0]
                events = store.connection.execute(
                    "SELECT COUNT(*) FROM events WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0]
                obligations = store.connection.execute(
                    "SELECT COUNT(*) FROM obligations WHERE workflow_id = ?", (workflow_id,)
                ).fetchone()[0]
                return workflow, events, obligations

            before = snapshot()
            await _error(client, actors.em.actor_context_id, "provider_transaction_classify", {
                "workflow_id": workflow_id,
                "transaction_id": "wrong-owner",
                "send_commit_proved": False,
                "evidence_ref": "evidence:wrong-owner",
            })
            assert snapshot() == before

            await _error(client, actors.cm.actor_context_id, "responsibility_scheduled_record", {
                "workflow_id": workflow_id,
                "subject": "inactive",
                "receiving_owner": actors.inactive.actor_context_id,
                "continuity_owner": actors.cm.actor_context_id,
                "next_event": "never",
                "evidence_ref": "evidence:inactive",
                "disposition_reason": "Inactive custody must be rejected.",
            })
            assert snapshot() == before

            await _error(client, actors.cm.actor_context_id, "responsibility_orphan_detect", {
                "workflow_id": workflow_id,
                "subject": "no-source",
                "next_event": "never",
                "evidence_ref": "evidence:no-source",
                "disposition_reason": "Missing mutation source must be rejected.",
            }, include_source=False)
            assert snapshot() == before

            await _error(client, actors.cm.actor_context_id, "responsibility_idle_complete_record", {
                "workflow_id": workflow_id,
                "subject": "science:cm-forbidden",
                "receiving_owner": actors.cm.actor_context_id,
                "next_event": "never",
                "evidence_ref": "artifact:cm-science-negative",
                "disposition_reason": "CM cannot author a science-negative disposition.",
                "revisit_condition": "new science",
            })
            assert snapshot() == before

            await _error(client, actors.cm.actor_context_id, "responsibility_handoff_open", {
                "workflow_id": workflow_id,
                "subject": "wrong-stage-actor",
                **_handoff(
                    stage="SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
                    receiving_owner=actors.portfolio.actor_context_id,
                    evidence_ref="artifact:wrong-stage-actor",
                ),
            })
            assert snapshot() == before

            await _error(client, actors.cm.actor_context_id, "responsibility_handoff_open", {
                "workflow_id": workflow_id,
                "subject": "cross-direction",
                **_handoff(
                    stage="CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE",
                    receiving_owner=actors.em_other.actor_context_id,
                    evidence_ref="artifact:cross-direction",
                ),
            })
            assert snapshot() == before

            await _error(client, actors.cm.actor_context_id, "responsibility_handoff_open", {
                "workflow_id": workflow_id,
                "subject": "generic-local-boundary",
                "stage": "LOCAL_BOUNDARY_RETURN_TO_CONTINUATION",
                "receiving_owner": actors.em.actor_context_id,
                "next_event": "never",
                "evidence_ref": "artifact:generic-local",
                "disposition_reason": "Generic handoff cannot override local boundary fields.",
                "direction_primary_queue": "ENGINEERING_REPAIR",
            })
            assert snapshot() == before

            typed = (await _call(client, actors.cm.actor_context_id, "responsibility_handoff_open", {
                "workflow_id": workflow_id,
                "subject": "typed",
                **_handoff(
                    stage="CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE",
                    receiving_owner=actors.em.actor_context_id,
                    evidence_ref="artifact:typed",
                ),
            }))["obligation_id"]
            before_resolve = snapshot()
            await _error(client, actors.cm.actor_context_id, "obligation_resolve", {
                "workflow_id": workflow_id,
                "obligation_id": typed,
                "resolution": {"attempt": "generic"},
            })
            assert snapshot() == before_resolve
            assert store.workflow_state(workflow_id)["open_obligations"][0]["obligation_id"] == typed

            closed_workflow = _open_actor_workflow(
                store, actors.root.actor_context_id, "wf-closed-mutation"
            )
            await _call(client, actors.root.actor_context_id, "workflow_close", {
                "workflow_id": closed_workflow,
                "closure_kind": "COMPLETED",
                "summary": "fixture closed",
            })
            closed_before = store.workflow_state(closed_workflow)
            await _error(client, actors.root.actor_context_id, "provider_transaction_classify", {
                "workflow_id": closed_workflow,
                "transaction_id": "closed-transaction",
                "send_commit_proved": False,
                "evidence_ref": "evidence:closed",
            })
            closed_after = store.workflow_state(closed_workflow)
            assert closed_after["state_version"] == closed_before["state_version"]
            assert closed_after["provider_transactions"] == []

    run(scenario)


def test_current_portfolio_mapping_is_authoritative_without_live_row_retyping(
    tmp_path: Path,
) -> None:
    mapping = load_actor_mapping()
    assert mapping["portfolio_session_ids"][:2] == [
        PORTFOLIO_SESSION,
        HISTORICAL_PORTFOLIO_SESSION,
    ]
    assert DEFAULT_PORTFOLIO_SESSION_ID == PORTFOLIO_SESSION
    fallback = load_actor_mapping(tmp_path / "mapping-does-not-exist.toml")
    assert fallback["portfolio_session_ids"] == [PORTFOLIO_SESSION]

    historical_mapping = tmp_path / "historical-only-actors.toml"
    historical_mapping.write_text(
        "schema_version = 1\n"
        f'portfolio_session_ids = ["{HISTORICAL_PORTFOLIO_SESSION}"]\n'
        'default_session_root_kind = "OPERATIONAL_ROOT"\n',
        encoding="utf-8",
    )
    store = SemanticStore(tmp_path / "existing-row.sqlite3").initialize()
    existing = register_session_root(
        store,
        session_id=PORTFOLIO_SESSION,
        mapping_path=historical_mapping,
    )
    assert existing.actor_kind is ActorKind.OPERATIONAL_ROOT
    unchanged = register_session_root(store, session_id=PORTFOLIO_SESSION)
    assert unchanged.actor_context_id == existing.actor_context_id
    assert unchanged.actor_kind is ActorKind.OPERATIONAL_ROOT
    store.close()


def test_invalid_user_authority_payloads_do_not_consume_grants_or_write(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        async with connected_server(tmp_path / "state") as (client, actors, store):
            workflow_id = _open_actor_workflow(
                store, actors.cm.actor_context_id, "wf-user-authority-atomicity"
            )

            def snapshot() -> tuple[int, int, int]:
                return (
                    int(store.connection.execute(
                        "SELECT state_version FROM workflows WHERE workflow_id = ?",
                        (workflow_id,),
                    ).fetchone()[0]),
                    int(store.connection.execute(
                        "SELECT COUNT(*) FROM events WHERE workflow_id = ?",
                        (workflow_id,),
                    ).fetchone()[0]),
                    int(store.connection.execute(
                        "SELECT COUNT(*) FROM obligations WHERE workflow_id = ?",
                        (workflow_id,),
                    ).fetchone()[0]),
                )

            async def rejected_with_fresh_grant(
                actor_id: str,
                operation: str,
                tool_name: str,
                arguments: dict,
            ) -> None:
                grant = grant_user_authority(
                    store, actor_context_id=actor_id, operation=operation
                )
                before = snapshot()
                bind_requester(actor_id)
                result = await client.call_tool(tool_name, {
                    **arguments,
                    "source_kind": "USER_AUTHORITY",
                    "requester_actor_context_id": actor_id,
                    "user_authority_id": grant["grant_id"],
                })
                assert result.is_error
                assert snapshot() == before
                consumed_at = store.connection.execute(
                    "SELECT consumed_at FROM user_authority_grants WHERE grant_id = ?",
                    (grant["grant_id"],),
                ).fetchone()[0]
                assert consumed_at is None

            await rejected_with_fresh_grant(
                actors.cm.actor_context_id,
                "open_obligation",
                "responsibility_handoff_open",
                {
                    "workflow_id": workflow_id,
                    "subject": "invalid-stage",
                    "stage": "LOCAL_BOUNDARY_RETURN_TO_CONTINUATION",
                    "receiving_owner": actors.em.actor_context_id,
                    "next_event": "never",
                    "evidence_ref": "artifact:invalid-stage",
                    "disposition_reason": "Invalid generic stage must fail before admission.",
                },
            )
            await rejected_with_fresh_grant(
                actors.cm.actor_context_id,
                "open_obligation",
                "provider_transaction_classify",
                {
                    "workflow_id": workflow_id,
                    "transaction_id": "invalid-provider",
                    "send_commit_proved": False,
                    "terminal_no_response_proved": True,
                    "evidence_ref": "evidence:invalid-provider",
                },
            )
            await rejected_with_fresh_grant(
                actors.cm.actor_context_id,
                "open_obligation",
                "responsibility_orphan_detect",
                {
                    "workflow_id": workflow_id,
                    "subject": "invalid-orphan",
                    "next_event": "never",
                    "evidence_ref": "artifact:invalid-orphan",
                    "disposition_reason": "blocked",
                },
            )

            typed = (
                await _call(client, actors.cm.actor_context_id, "responsibility_handoff_open", {
                    "workflow_id": workflow_id,
                    "subject": "accept-atomicity",
                    **_handoff(
                        stage="CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE",
                        receiving_owner=actors.em.actor_context_id,
                        evidence_ref="artifact:accept-atomicity",
                    ),
                })
            )["obligation_id"]
            await rejected_with_fresh_grant(
                actors.em.actor_context_id,
                "resolve_obligation",
                "responsibility_handoff_accept",
                {
                    "workflow_id": workflow_id,
                    "obligation_id": typed,
                    "next_responsibility": None,
                },
            )
            assert store.workflow_state(workflow_id)["open_obligations"][0][
                "obligation_id"
            ] == typed

    run(scenario)


def test_registration_config_schemas_and_admission_ast(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with connected_server(tmp_path / "state") as (client, _actors_fixture, _store):
            tools = (await client.list_tools()).tools
            assert tuple(tool.name for tool in tools) == mcp_server.ORCHESTRATOR_TOOL_ALLOWLIST
            by_name = {tool.name: tool for tool in tools}
            assert set(NEW_TOOLS) <= set(by_name)
            for name in NEW_TOOLS:
                assert AUTHORITY_FIELDS <= set(by_name[name].input_schema["properties"])
            handoff_properties = set(
                by_name["responsibility_handoff_open"].input_schema["properties"]
            )
            assert not handoff_properties & {
                "active_worker",
                "continuity_owner",
                "continuation_owner",
                "direction_primary_queue",
                "prior_direction_primary_queue",
                "queue_authority_artifact",
                "queue_authority_owner",
                "boundary_domain",
                "revisit_condition",
                "current_work",
            }

    run(scenario)
    assert set(mcp_server.MUTATION_OPERATION_BY_TOOL) == set(mcp_server.MUTATING_TOOL_NAMES)
    config = tomllib.loads((REPO_ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert tuple(config["mcp_servers"]["hmasd_orchestrator"]["enabled_tools"]) == (
        mcp_server.ORCHESTRATOR_TOOL_ALLOWLIST
    )
    for path in (REPO_ROOT / ".codex/agents").glob("*.toml"):
        tomllib.loads(path.read_text(encoding="utf-8"))
    expected_source_layers = {
        ContextSourceKind.HISTORICAL_SCIENCE_LINEAGE: PrecedenceLayer.HISTORY,
        ContextSourceKind.HUMAN_STATUS_PROJECTION: PrecedenceLayer.NAVIGATION,
        ContextSourceKind.MECHANICALLY_CHECKED_STATUS_PROJECTION: (
            PrecedenceLayer.NAVIGATION
        ),
        ContextSourceKind.PROJECTION_SCHEMA: PrecedenceLayer.PROCEDURE,
    }
    for source_kind, layer in expected_source_layers.items():
        assert precedence_for_kind(source_kind) is layer
        assert not can_create_authority(layer)
        assert not can_create_state_transition(layer)

    tree = ast.parse((REPO_ROOT / "tools/codex_semantic_mvp/mcp_server.py").read_text(encoding="utf-8"))
    definitions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in NEW_TOOLS:
        function = definitions[name]
        parameters = {argument.arg for argument in function.args.args}
        assert AUTHORITY_FIELDS <= parameters
        assert any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_admit_mutation"
            for node in ast.walk(function)
        )


def test_fresh_stdio_process_lists_and_invokes_typed_surface(tmp_path: Path) -> None:
    state_dir = tmp_path / "fresh-state"
    store = SemanticStore(state_dir / "state.sqlite3").initialize()
    portfolio = register_session_root(store, session_id=PORTFOLIO_SESSION)
    assert portfolio.actor_kind is ActorKind.PORTFOLIO
    em = register_child_actor(
        store,
        session_id="fresh-stdio-em",
        actor_kind=ActorKind.EM,
        scope_key="direction:fresh-stdio",
        direction_id="fresh-stdio",
        parent_actor_context_id=portfolio.actor_context_id,
    )
    workflow_id = _open_actor_workflow(
        store, em.actor_context_id, "wf-fresh-stdio"
    )
    store.close()

    def parameters(actor_context_id: str) -> StdioServerParameters:
        environment = dict(os.environ)
        environment.update({
            "HMASD_REPO_ROOT": str(tmp_path),
            "HMASD_CODEX_MVP_STATE_DIR": str(state_dir),
            "HMASD_BOUND_ACTOR_CONTEXT_ID": actor_context_id,
        })
        return StdioServerParameters(
            command=PYTHON,
            args=["-m", "tools.codex_semantic_mvp.mcp_server"],
            cwd=REPO_ROOT,
            env=environment,
        )

    async def scenario() -> None:
        async with stdio_client(parameters(em.actor_context_id)) as streams:
            async with ClientSession(*streams) as client:
                await client.initialize()
                opened = await client.call_tool("responsibility_handoff_open", {
                    "workflow_id": workflow_id,
                    "subject": "fresh:portfolio-decision",
                    "stage": "SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
                    "receiving_owner": portfolio.actor_context_id,
                    "next_event": "Portfolio accepts the terminal decision",
                    "evidence_ref": "fresh:portfolio-evidence",
                    "disposition_reason": "The current Portfolio actor owns terminal acceptance.",
                    "source_kind": "ROLE_CONTRACT",
                    "requester_actor_context_id": em.actor_context_id,
                })
                assert not opened.is_error, opened.content
                obligation_id = _decode(opened)["obligation_id"]

        async with stdio_client(parameters(portfolio.actor_context_id)) as streams:
            async with ClientSession(*streams) as client:
                await client.initialize()
                assert tuple(
                    tool.name for tool in (await client.list_tools()).tools
                ) == mcp_server.ORCHESTRATOR_TOOL_ALLOWLIST
                current = await client.call_tool("actor_context_current", {
                    "session_id": PORTFOLIO_SESSION,
                })
                assert not current.is_error, current.content
                assert _decode(current)["actor_context"] == {
                    "actor_context_id": portfolio.actor_context_id,
                    "actor_kind": "PORTFOLIO",
                    "session_id": PORTFOLIO_SESSION,
                    "scope_key": f"session:{PORTFOLIO_SESSION}",
                    "direction_id": None,
                    "state": "ACTIVE",
                }
                before = await client.call_tool(
                    "workflow_state", {"workflow_id": workflow_id}
                )
                assert not before.is_error, before.content
                assert _decode(before)["open_obligations"][0]["obligation_id"] == obligation_id
                accepted = await client.call_tool("responsibility_handoff_accept", {
                    "workflow_id": workflow_id,
                    "obligation_id": obligation_id,
                    "portfolio_accepted": True,
                    "source_kind": "ROLE_CONTRACT",
                    "requester_actor_context_id": portfolio.actor_context_id,
                })
                assert not accepted.is_error, accepted.content
                assert _decode(accepted) == {
                    "workflow_id": workflow_id,
                    "obligation_id": obligation_id,
                    "state": "RESOLVED",
                    "successor_obligation_id": None,
                }
                after = await client.call_tool(
                    "workflow_state", {"workflow_id": workflow_id}
                )
                assert not after.is_error, after.content
                projected = _decode(after)
                assert projected["open_obligations"] == []
                terminal = next(
                    item for item in projected["responsibilities"]
                    if item["obligation_id"] == obligation_id
                )
                assert terminal["state"] == "RESOLVED"
                resolution = json.loads(terminal["resolution_json"])
                assert resolution["resolution_kind"] == "PORTFOLIO_ACCEPTED"
                assert resolution["accepted_by"] == portfolio.actor_context_id

    run(scenario)

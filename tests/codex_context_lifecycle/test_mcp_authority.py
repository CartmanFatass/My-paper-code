import json
from contextlib import asynccontextmanager

import anyio

from mcp.client import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from tests.codex_context_lifecycle.helpers import make_pair, open_em_epoch
from tools.codex_context_lifecycle.authority import bind_requester, grant_user_authority
from tools.codex_context_lifecycle.models import PromotionKind
from tools.codex_semantic_mvp import mcp_server
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.epochs import plan_epoch_open


def run(coro):
    return anyio.run(coro)


@asynccontextmanager
async def connected_server(state_dir):
    server = mcp_server.build_server(state_dir)
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        async with anyio.create_task_group() as tg:
            tg.start_soon(
                server._lowlevel_server.run,
                server_streams[0],
                server_streams[1],
                server._lowlevel_server.create_initialization_options(),
            )
            async with ClientSession(*client_streams) as client:
                await client.initialize()
                yield client
                tg.cancel_scope.cancel()


async def call(client, name, arguments=None):
    result = await client.call_tool(name, arguments or {})
    if result.is_error:
        text = result.content[0].text if result.content else ""
        raise RuntimeError(text)
    if result.structured_content:
        return result.structured_content
    return json.loads(result.content[0].text)


def test_mcp_mutation_requires_trusted_requester_identity(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            _root, em, _cm = make_pair(store)
            epoch = open_em_epoch(store, em)
            from tools.codex_context_lifecycle.promotion import create_promotion_proposal

            proposed = create_promotion_proposal(
                store,
                actor_context_id=em.actor_context_id,
                epoch_id=epoch["epoch_id"],
                promotion_kind=PromotionKind.EPHEMERAL,
                summary="note",
                rationale="local",
                source_refs=[],
                owner_actor_context_id=em.actor_context_id,
            )
            result = await client.call_tool(
                "context_promotion_resolve",
                {"promotion_id": proposed["promotion_id"], "next_state": "OWNER_ACCEPTED"},
            )
            assert result.is_error
    run(scenario)


def test_mcp_plan_epoch_close_rejects_nonowner(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            _root, em, cm = make_pair(store)
            epoch = open_em_epoch(store, em)
            bind_requester(cm.actor_context_id)
            result = await client.call_tool(
                "plan_epoch_close",
                {
                    "actor_context_id": em.actor_context_id,
                    "epoch_id": epoch["epoch_id"],
                    "source_kind": "ROLE_CONTRACT",
                    "requester_actor_context_id": cm.actor_context_id,
                },
            )
            assert result.is_error
    run(scenario)


def test_wrong_actor_cannot_accept_or_apply_owner_promotion(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            _root, em, cm = make_pair(store)
            epoch = open_em_epoch(store, em)
            from tools.codex_context_lifecycle.promotion import create_promotion_proposal

            proposed = create_promotion_proposal(
                store,
                actor_context_id=em.actor_context_id,
                epoch_id=epoch["epoch_id"],
                promotion_kind=PromotionKind.EPHEMERAL,
                summary="note",
                rationale="local",
                source_refs=[],
                owner_actor_context_id=em.actor_context_id,
            )
            bind_requester(cm.actor_context_id)
            accept = await client.call_tool(
                "context_promotion_resolve",
                {
                    "promotion_id": proposed["promotion_id"],
                    "next_state": "OWNER_ACCEPTED",
                    "source_kind": "ROLE_CONTRACT",
                    "requester_actor_context_id": cm.actor_context_id,
                    "disposition": {"owner": "cm"},
                },
            )
            assert accept.is_error
    run(scenario)


def test_plan_epoch_source_kind_is_not_caller_asserted(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            root, em, _cm = make_pair(store)
            bind_requester(em.actor_context_id)
            result = await client.call_tool(
                "plan_epoch_open",
                {
                    "actor_context_id": em.actor_context_id,
                    "epoch_kind": EpochKind.DIRECTION_STAGE.value,
                    "objective": "next",
                    "authority_refs": [],
                    "frozen_invariants": [],
                    "exit_boundary": "exit",
                    "source_kind": "USER_AUTHORITY",
                    "requester_actor_context_id": em.actor_context_id,
                },
            )
            assert result.is_error
            grant = grant_user_authority(
                store, actor_context_id=em.actor_context_id, operation="open_epoch"
            )
            opened = await call(
                client,
                "plan_epoch_open",
                {
                    "actor_context_id": em.actor_context_id,
                    "epoch_kind": EpochKind.DIRECTION_STAGE.value,
                    "objective": "next",
                    "authority_refs": [],
                    "frozen_invariants": [],
                    "exit_boundary": "exit",
                    "source_kind": "USER_AUTHORITY",
                    "user_authority_id": grant["grant_id"],
                    "requester_actor_context_id": em.actor_context_id,
                },
            )
            assert opened["epoch_id"]
            del root
    run(scenario)


def test_promotion_resolve_requires_owner_decision_layer(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            _root, em, _cm = make_pair(store)
            epoch = open_em_epoch(store, em)
            from tools.codex_context_lifecycle.promotion import create_promotion_proposal

            proposed = create_promotion_proposal(
                store,
                actor_context_id=em.actor_context_id,
                epoch_id=epoch["epoch_id"],
                promotion_kind=PromotionKind.EPHEMERAL,
                summary="note",
                rationale="local",
                source_refs=[],
                owner_actor_context_id=em.actor_context_id,
            )
            bind_requester(em.actor_context_id)
            result = await client.call_tool(
                "context_promotion_resolve",
                {
                    "promotion_id": proposed["promotion_id"],
                    "next_state": "OWNER_ACCEPTED",
                    "source_kind": "PLAN_EPOCH",
                    "requester_actor_context_id": em.actor_context_id,
                    "disposition": {"owner": "em"},
                },
            )
            assert result.is_error
    run(scenario)


def test_mcp_epoch_open_rejects_unregistered_procedure_ref(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            _root, em, _cm = make_pair(store)
            bind_requester(em.actor_context_id)
            result = await client.call_tool(
                "plan_epoch_open",
                {
                    "actor_context_id": em.actor_context_id,
                    "epoch_kind": EpochKind.DIRECTION_STAGE.value,
                    "objective": "next",
                    "authority_refs": [],
                    "frozen_invariants": [],
                    "exit_boundary": "exit",
                    "procedure_refs": ["not-a-registered-source"],
                    "source_kind": "PLAN_EPOCH",
                    "requester_actor_context_id": em.actor_context_id,
                },
            )
            assert result.is_error
    run(scenario)


def test_mcp_epoch_revise_rejects_source_not_visible_to_actor(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._active_store
            _root, em, _cm = make_pair(store)
            epoch = plan_epoch_open(
                store,
                actor_context_id=em.actor_context_id,
                epoch_kind=EpochKind.DIRECTION_STAGE,
                objective="old",
                authority_refs=[],
                frozen_invariants=[],
                exit_boundary="exit",
            )
            bind_requester(em.actor_context_id)
            result = await client.call_tool(
                "plan_epoch_revise",
                {
                    "actor_context_id": em.actor_context_id,
                    "epoch_id": epoch["epoch_id"],
                    "expected_revision": epoch["revision"],
                    "objective": "new",
                    "authority_refs": [],
                    "frozen_invariants": [],
                    "exit_boundary": "exit",
                    "reason": "try",
                    "procedure_refs": ["project-map"],
                    "source_kind": "PLAN_EPOCH",
                    "requester_actor_context_id": em.actor_context_id,
                },
            )
            assert result.is_error
    run(scenario)

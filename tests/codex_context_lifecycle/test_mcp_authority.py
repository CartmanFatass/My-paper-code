import ast
import inspect
import json
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import pytest

from mcp.client import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from tests.codex_context_lifecycle.helpers import make_pair, open_em_epoch
from tools.codex_context_lifecycle.authority import (
    AuthorityError,
    bind_requester,
    grant_user_authority,
)
from tools.codex_context_lifecycle.models import PromotionKind
from tools.codex_semantic_mvp import mcp_server
from tools.codex_semantic_mvp.actor_models import EpochKind
from tools.codex_semantic_mvp.epochs import plan_epoch_open

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


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


def test_every_mutation_tool_has_explicit_admission_parameters_and_call(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert set(tools) == set(mcp_server.ORCHESTRATOR_TOOL_ALLOWLIST)
            assert set(mcp_server.MUTATION_OPERATION_BY_TOOL) == set(
                mcp_server.MUTATING_TOOL_NAMES
            )
            for name in mcp_server.MUTATING_TOOL_NAMES:
                properties = tools[name].input_schema["properties"]
                assert {
                    "source_kind",
                    "requester_actor_context_id",
                    "user_authority_id",
                } <= set(properties), name

        tree = ast.parse(inspect.getsource(mcp_server._register_tools))
        functions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in mcp_server.MUTATING_TOOL_NAMES:
            calls = {
                node.func.id
                for node in ast.walk(functions[name])
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            assert "_admit_mutation" in calls, name

    run(scenario)


def test_tool_annotations_match_server_effect_inventory(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            for name in mcp_server.READ_ONLY_TOOL_NAMES:
                annotations = tools[name].annotations
                assert annotations is not None, name
                assert annotations.read_only_hint is True, name
                assert annotations.destructive_hint is False, name
                assert annotations.idempotent_hint is True, name
                assert annotations.open_world_hint is False, name
            for name in mcp_server.MUTATING_TOOL_NAMES:
                annotations = tools[name].annotations
                assert annotations is None or annotations.read_only_hint is not True, name

    run(scenario)


def test_uniform_admission_rejects_wrong_owner_inactive_and_missing_source_without_writes(
    tmp_path,
) -> None:
    mcp_server.build_server(tmp_path)
    store = mcp_server._get_store()
    root, em, cm = make_pair(store)

    for operation in sorted(set(mcp_server.MUTATION_OPERATION_BY_TOOL.values())):
        bind_requester(em.actor_context_id)
        before = store.connection.total_changes
        accepted_store, accepted = mcp_server._admit_mutation(
            em.actor_context_id,
            "ROLE_CONTRACT",
            operation,
            owner_actor_context_id=em.actor_context_id,
        )
        assert accepted_store is store
        assert accepted.actor_context_id == em.actor_context_id
        assert store.connection.total_changes == before

        bind_requester(cm.actor_context_id)
        grant = grant_user_authority(
            store, actor_context_id=cm.actor_context_id, operation=operation
        )
        before = store.connection.total_changes
        with pytest.raises(AuthorityError):
            mcp_server._admit_mutation(
                cm.actor_context_id,
                "USER_AUTHORITY",
                operation,
                grant["grant_id"],
                owner_actor_context_id=em.actor_context_id,
            )
        assert store.connection.total_changes == before
        consumed = store.connection.execute(
            "SELECT consumed_at FROM user_authority_grants WHERE grant_id = ?",
            (grant["grant_id"],),
        ).fetchone()
        assert consumed["consumed_at"] is None

        bind_requester(em.actor_context_id)
        before = store.connection.total_changes
        with pytest.raises(AuthorityError):
            mcp_server._admit_mutation(
                em.actor_context_id,
                None,
                operation,
                owner_actor_context_id=em.actor_context_id,
            )
        assert store.connection.total_changes == before

    store.connection.execute(
        "UPDATE actor_contexts SET state = 'RELEASED' WHERE actor_context_id = ?",
        (em.actor_context_id,),
    )
    store.connection.commit()
    bind_requester(em.actor_context_id)
    before = store.connection.total_changes
    with pytest.raises(AuthorityError, match="not ACTIVE"):
        mcp_server._admit_mutation(
            em.actor_context_id,
            "ROLE_CONTRACT",
            "write_semantic_commit",
            owner_actor_context_id=em.actor_context_id,
        )
    assert store.connection.total_changes == before
    del root


def test_root_only_admission_and_raw_report_access_are_owner_scoped(tmp_path) -> None:
    async def scenario():
        async with connected_server(tmp_path) as client:
            store = mcp_server._get_store()
            root, em, _cm = make_pair(store, session_id="raw-session")
            root_workflow = store.current_actor_workflow(root.actor_context_id)
            assert root_workflow is not None
            workflow_id = str(root_workflow["workflow_id"])
            store.register_task(workflow_id, "child", "worker", "return", True)
            report_id = store.record_untyped_return(
                workflow_id, "child", "agent", "worker", "sensitive raw report"
            )

            bind_requester(em.actor_context_id)
            wrong = await client.call_tool(
                "report_get",
                {
                    "workflow_id": workflow_id,
                    "report_id": report_id,
                    "include_raw": True,
                    "requester_actor_context_id": em.actor_context_id,
                },
            )
            assert wrong.is_error

            bind_requester(root.actor_context_id)
            raw = await call(
                client,
                "report_get",
                {
                    "workflow_id": workflow_id,
                    "report_id": report_id,
                    "include_raw": True,
                    "requester_actor_context_id": root.actor_context_id,
                },
            )
            assert raw["raw_message"] == "sensitive raw report"

            bind_requester(em.actor_context_id)
            with pytest.raises(AuthorityError):
                mcp_server._admit_mutation(
                    em.actor_context_id,
                    "ROLE_CONTRACT",
                    "open_workflow",
                    owner_actor_context_id=em.actor_context_id,
                    root_only=True,
                )

    run(scenario)


def test_live_config_allowlists_match_static_server_inventories() -> None:
    root = Path(__file__).resolve().parents[2]
    config = tomllib.loads((root / ".codex/config.toml").read_text(encoding="utf-8"))
    orchestrator = config["mcp_servers"]["hmasd_orchestrator"]
    observability = config["mcp_servers"]["hmasd_observability"]
    from tools.hmasd_control_plane.mcp_server import OBSERVABILITY_TOOL_ALLOWLIST

    assert orchestrator["enabled"] is True
    assert orchestrator["required"] is False
    assert orchestrator["default_tools_approval_mode"] == "approve"
    assert orchestrator["enabled_tools"] == list(
        mcp_server.ORCHESTRATOR_TOOL_ALLOWLIST
    )
    assert observability["enabled"] is True
    assert observability["required"] is False
    assert observability["enabled_tools"] == list(OBSERVABILITY_TOOL_ALLOWLIST)

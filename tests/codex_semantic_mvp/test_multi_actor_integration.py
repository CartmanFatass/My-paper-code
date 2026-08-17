from pathlib import Path

from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import (
    bind_agent_identity,
    register_child_actor,
    register_session_root,
)
from tools.codex_semantic_mvp.models import ReturnKind, SubagentReturnPacket
from tools.codex_semantic_mvp.store import SemanticStore


def packet(workflow_id: str, task_id: str) -> SubagentReturnPacket:
    return SubagentReturnPacket(
        schema_version="1.0",
        packet_kind="SUBAGENT_RETURN",
        workflow_id=workflow_id,
        task_id=task_id,
        return_kind=ReturnKind.COMPLETED_ASSIGNMENT,
        observed_facts=(),
        interpretive_claims=(),
        remaining_unknowns=(),
        suggested_next_actions=(),
        research_frontier=None,
        global_disposition="NOT_ASSERTED",
    )


def test_six_actors_keep_owner_local_reports(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path / "state.sqlite3").initialize()
    portfolio = register_session_root(store, session_id="019ffc20-5001-7453-a08a-dac783cf4d80")
    root = register_session_root(store, session_id="session-root")
    em = register_child_actor(
        store,
        session_id="session-root",
        actor_kind=ActorKind.EM,
        scope_key="direction:risp:em",
        direction_id="risp",
        parent_actor_context_id=root.actor_context_id,
    )
    cm = register_child_actor(
        store,
        session_id="session-root",
        actor_kind=ActorKind.CM,
        scope_key="direction:risp:cm",
        direction_id="risp",
        parent_actor_context_id=root.actor_context_id,
        counterpart_actor_context_id=em.actor_context_id,
    )
    scout = register_child_actor(
        store,
        session_id="session-root",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:scout",
        direction_id="risp",
        parent_actor_context_id=em.actor_context_id,
    )
    implementer = register_child_actor(
        store,
        session_id="session-root",
        actor_kind=ActorKind.LEAF,
        scope_key="leaf:implementer",
        direction_id="risp",
        parent_actor_context_id=cm.actor_context_id,
    )
    bind_agent_identity(store, actor_context_id=scout.actor_context_id, agent_id="scout-1")
    bind_agent_identity(store, actor_context_id=implementer.actor_context_id, agent_id="impl-1")
    ids = {
        portfolio.actor_context_id,
        root.actor_context_id,
        em.actor_context_id,
        cm.actor_context_id,
        scout.actor_context_id,
        implementer.actor_context_id,
    }
    assert len(ids) == 6

    em_wf = store.open_actor_workflow(em.actor_context_id, "t-em", "em", "research")
    cm_wf = store.open_actor_workflow(cm.actor_context_id, "t-cm", "cm", "implement")
    store.register_task(em_wf, "scout", "worker", "inspect", True)
    store.register_task(cm_wf, "implementer", "worker", "code", True)
    store.record_report(em_wf, "scout", "scout-1", "worker", "scout report", packet(em_wf, "scout"))
    store.record_report(
        cm_wf, "implementer", "impl-1", "worker", "impl report", packet(cm_wf, "implementer")
    )
    em_state = store.workflow_state(em_wf)
    cm_state = store.workflow_state(cm_wf)
    assert em_state["open_obligations"][0]["owner_actor_context_id"] == em.actor_context_id
    assert cm_state["open_obligations"][0]["owner_actor_context_id"] == cm.actor_context_id
    root_wf = store.current_actor_workflow(root.actor_context_id)
    if root_wf is not None:
        root_state = store.workflow_state(str(root_wf["workflow_id"]))
        assert root_state["open_obligations"] == []
    store.close()

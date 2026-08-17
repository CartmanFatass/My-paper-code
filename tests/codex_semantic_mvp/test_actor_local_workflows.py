from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import register_child_actor, register_session_root
from tools.codex_semantic_mvp.models import ReturnKind, SubagentReturnPacket
from tools.codex_semantic_mvp.store import SemanticStore


PORTFOLIO_SESSION = "019ffc20-5001-7453-a08a-dac783cf4d80"


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


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    instance = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield instance
    instance.close()


def _report_obligation(store: SemanticStore, actor_id: str, task_id: str, agent_id: str) -> dict:
    workflow = store.open_actor_workflow(
        actor_context_id=actor_id,
        opened_turn_id="turn-1",
        scope="test",
        objective="owner-local intake",
    )
    store.register_task(workflow, task_id, "worker", "inspect", True)
    store.record_report(
        workflow, task_id, agent_id, "worker", "child prose", packet(workflow, task_id)
    )
    obligation = store.connection.execute(
        """SELECT * FROM obligations WHERE workflow_id = ? AND state = 'OPEN'
        ORDER BY created_at LIMIT 1""",
        (workflow,),
    ).fetchone()
    assert obligation is not None
    return dict(obligation)


def test_root_direct_scout_intake_stays_on_root(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-root")
    obligation = _report_obligation(store, root.actor_context_id, "scout", "scout-1")
    assert obligation["owner_actor_context_id"] == root.actor_context_id
    assert obligation["kind"] == "REPORT_INTAKE_REQUIRED"


def test_em_research_scout_intake_stays_on_em(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-risp")
    em = register_child_actor(
        store,
        session_id="session-risp",
        actor_kind=ActorKind.EM,
        scope_key="direction:risp:em",
        direction_id="renewal_indexed_score_plasticity",
        parent_actor_context_id=root.actor_context_id,
    )
    obligation = _report_obligation(store, em.actor_context_id, "research-scout", "scout-em")
    assert obligation["owner_actor_context_id"] == em.actor_context_id
    assert obligation["kind"] == "REPORT_INTAKE_REQUIRED"
    root_workflow = store.current_actor_workflow(root.actor_context_id)
    assert root_workflow is None or root_workflow["workflow_id"] != obligation["workflow_id"]


def test_cm_implementer_intake_stays_on_cm(store: SemanticStore) -> None:
    root = register_session_root(store, session_id="session-cm")
    cm = register_child_actor(
        store,
        session_id="session-cm",
        actor_kind=ActorKind.CM,
        scope_key="direction:risp:cm",
        direction_id="renewal_indexed_score_plasticity",
        parent_actor_context_id=root.actor_context_id,
    )
    obligation = _report_obligation(store, cm.actor_context_id, "implementer", "impl-1")
    assert obligation["owner_actor_context_id"] == cm.actor_context_id
    assert obligation["kind"] == "REPORT_INTAKE_REQUIRED"


def test_portfolio_child_intake_stays_on_portfolio(store: SemanticStore) -> None:
    portfolio = register_session_root(store, session_id=PORTFOLIO_SESSION)
    obligation = _report_obligation(store, portfolio.actor_context_id, "portfolio-child", "p-1")
    assert obligation["owner_actor_context_id"] == portfolio.actor_context_id
    assert obligation["kind"] == "REPORT_INTAKE_REQUIRED"


def test_old_root_intake_rows_read_as_report_intake(store: SemanticStore) -> None:
    workflow_id = store.open_workflow("wf-old", "session-old", "turn-1", "scope", "objective")
    store.connection.execute(
        """UPDATE obligations SET kind = 'ROOT_INTAKE_REQUIRED'
        WHERE workflow_id = ?""",
        (workflow_id,),
    )
    store.connection.execute(
        """INSERT INTO obligations
        (obligation_id, workflow_id, kind, owner, subject, reason, source_ref, state, created_at)
        VALUES ('obl-old', ?, 'ROOT_INTAKE_REQUIRED', '/root', 'rep-old', 'legacy', 'rep-old', 'OPEN', ?)""",
        (workflow_id, "2026-08-17T00:00:00+00:00"),
    )
    store.connection.commit()
    state = store.workflow_state(workflow_id)
    assert {item["kind"] for item in state["open_obligations"]} == {"REPORT_INTAKE_REQUIRED"}
    raw = store.connection.execute(
        "SELECT kind FROM obligations WHERE obligation_id = 'obl-old'"
    ).fetchone()
    assert raw[0] == "ROOT_INTAKE_REQUIRED"

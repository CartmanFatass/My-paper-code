"""Runtime-free acceptance for responsibility-bearing stage handoffs."""

from pathlib import Path

import pytest

from tools.codex_semantic_mvp.actor_models import ActorKind
from tools.codex_semantic_mvp.actor_registry import register_session_root
from tools.codex_semantic_mvp.responsibility import (
    BoundaryDomain,
    ProviderTransactionLifecycle,
    ResponsibilityStage,
    build_responsibility,
    classify_provider_transaction,
)
from tools.codex_semantic_mvp.stop_policy import stop_decision_for_actor
from tools.codex_semantic_mvp.store import SemanticStore


@pytest.fixture
def store(tmp_path: Path) -> SemanticStore:
    result = SemanticStore(tmp_path / "state.sqlite3").initialize()
    yield result
    result.close()


def _workflow(store: SemanticStore, suffix: str) -> str:
    return store.open_workflow(f"wf-{suffix}", f"session-{suffix}", "turn", "control", "lifecycle")


def _handoff(store: SemanticStore, workflow_id: str, stage: ResponsibilityStage, owner: str) -> str:
    return store.open_responsibility(
        workflow_id, "direction:fixture", stage=stage, receiving_owner=owner,
        next_event="receiver accepts the handoff", evidence_ref="fixture:evidence",
        disposition_reason="A concrete responsibility remains.", active_worker=owner,
    )


def test_runtime_free_stage_handoff_lifecycle_acceptance(store: SemanticStore) -> None:
    # 1 and 7: CM return stays in workflow_state until the exact EM accepts it;
    # the successor is opened in the same transaction and survives a fresh read.
    cm_wf = _workflow(store, "cm")
    cm_return = _handoff(
        store, cm_wf, ResponsibilityStage.CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE, "em:direction",
    )
    initial = store.workflow_state(cm_wf)
    visible = initial["open_obligations"][0]
    assert visible["stage"] == "CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE"
    assert {key: visible[key] for key in ("primary_queue", "receiving_owner", "next_event", "boundary_domain", "continuity_state", "evidence_ref")} == {
        "primary_queue": "SCIENCE_INTAKE", "receiving_owner": "em:direction",
        "next_event": "receiver accepts the handoff", "boundary_domain": "ENGINEERING_BOUNDARY",
        "continuity_state": "CURRENT_WORK", "evidence_ref": "fixture:evidence",
    }
    with pytest.raises(ValueError, match="exact receiving owner"):
        store.accept_responsibility_handoff(cm_wf, cm_return, accepted_by="other")
    with pytest.raises(ValueError, match="requires successor"):
        store.accept_responsibility_handoff(cm_wf, cm_return, accepted_by="em:direction")
    with pytest.raises(ValueError, match="require accept_responsibility_handoff"):
        store.resolve_obligation(cm_wf, cm_return)
    assert store.workflow_state(cm_wf)["open_obligations"][0]["obligation_id"] == cm_return
    with pytest.raises(ValueError, match="requires successor"):
        store.accept_responsibility_handoff(cm_wf, cm_return, accepted_by="em:direction", next_responsibility={
            "stage": "CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION",
            "receiving_owner": "em:direction", "active_worker": "em:direction",
            "next_event": "wrong stage", "evidence_ref": "fixture:wrong", "disposition_reason": "Wrong stage.",
        })
    assert store.workflow_state(cm_wf)["open_obligations"][0]["obligation_id"] == cm_return
    portfolio = store.accept_responsibility_handoff(
        cm_wf, cm_return, accepted_by="em:direction", next_responsibility={
            "stage": "SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
            "receiving_owner": "portfolio", "next_event": "Portfolio records a decision",
            "evidence_ref": "fixture:em-intake", "disposition_reason": "EM intake is complete.",
            "active_worker": "portfolio",
        },
    )
    assert portfolio
    reader = SemanticStore(store.path).initialize()
    fresh = reader.workflow_state(cm_wf)
    reader.close()
    assert fresh["open_obligations"][0]["obligation_id"] == portfolio
    assert fresh["open_obligations"][0]["primary_queue"] == "PORTFOLIO_DECISION"
    assert {item["state"] for item in fresh["responsibilities"]} == {"OPEN", "RESOLVED"}
    assert [item["obligation_id"] for item in fresh["current_responsibilities"]] == [portfolio]

    # 2: terminal receipt cannot become direction completion while the CM and
    # science-owner receiver obligations remain open.
    terminal_wf = _workflow(store, "terminal")
    terminal = _handoff(
        store, terminal_wf, ResponsibilityStage.OPERATOR_TERMINAL_TO_CM_TECHNICAL_INTAKE, "cm:direction",
    )
    with pytest.raises(ValueError, match="open obligations"):
        store.create_closure_receipt(terminal_wf, "COMPLETED", "premature")
    science = store.accept_responsibility_handoff(
        terminal_wf, terminal, accepted_by="cm:direction", next_responsibility={
            "stage": "CM_TECHNICAL_INTAKE_TO_SCIENCE_RECONCILIATION",
            "receiving_owner": "em:direction", "next_event": "EM reconciles terminal receipt",
            "evidence_ref": "fixture:terminal", "disposition_reason": "CM intake is complete.",
            "active_worker": "em:direction",
        },
    )
    assert science
    with pytest.raises(ValueError, match="open obligations"):
        store.create_closure_receipt(terminal_wf, "COMPLETED", "still premature")
    final_portfolio = store.accept_responsibility_handoff(
        terminal_wf, science, accepted_by="em:direction", next_responsibility={
            "stage": "SAME_DIRECTION_EM_INTAKE_TO_PORTFOLIO_DECISION",
            "receiving_owner": "portfolio", "active_worker": "portfolio",
            "next_event": "Portfolio makes the final decision", "evidence_ref": "fixture:em",
            "disposition_reason": "Science reconciliation is complete.",
        },
    )
    with pytest.raises(ValueError, match="open obligations"):
        store.create_closure_receipt(terminal_wf, "COMPLETED", "Portfolio still required")
    with pytest.raises(ValueError, match="portfolio_accepted"):
        store.accept_responsibility_handoff(terminal_wf, final_portfolio, accepted_by="portfolio")
    assert store.workflow_state(terminal_wf)["open_obligations"][0]["obligation_id"] == final_portfolio
    terminal_boundaries = [
        item["responsibility"]["boundary_domain"]
        for item in store.workflow_state(terminal_wf)["responsibilities"]
    ]
    assert terminal_boundaries == [
        "EXPERIMENT_TRANSACTION", "ENGINEERING_BOUNDARY", "SCIENCE_DISPOSITION",
    ]
    store.accept_responsibility_handoff(
        terminal_wf, final_portfolio, accepted_by="portfolio", portfolio_accepted=True,
    )
    store.create_closure_receipt(terminal_wf, "COMPLETED", "Portfolio accepted final decision")

    # 3: resource, technical, and negative-science boundaries have distinct queues.
    queue_wf = _workflow(store, "queues")
    technical = _handoff(
        store, queue_wf, ResponsibilityStage.TECHNICAL_FAILURE_TO_ENGINEERING_REPAIR, "cm:repair",
    )
    resource = store.record_completed_responsibility(
        queue_wf, "direction:resource", stage=ResponsibilityStage.RESOURCE_SHORTAGE_TO_RESOURCE_OR_SUBSTRATE_WAIT,
        receiving_owner="portfolio", next_event="named substrate becomes available", evidence_ref="fixture:resource",
        disposition_reason="The named substrate is absent.", revisit_condition="Reopen when substrate S is available.",
    )
    negative = store.record_completed_responsibility(
        queue_wf, "direction:negative", receiving_owner="em:direction",
        next_event="named discriminator changes", evidence_ref="fixture:negative",
        disposition_reason="The current object is nonidentifying.", revisit_condition="Reopen on discriminator D.",
    )
    queues = {item["obligation_id"]: item["responsibility"]["primary_queue"] for item in store.workflow_state(queue_wf)["responsibilities"]}
    assert queues[technical] == "ENGINEERING_REPAIR"
    assert queues[resource] == "RESOURCE_OR_SUBSTRATE_WAIT"
    assert queues[negative] == "SCIENTIFIC_NO_CURRENT"
    boundaries = {
        item["obligation_id"]: item["responsibility"]["boundary_domain"]
        for item in store.workflow_state(queue_wf)["responsibilities"]
    }
    assert boundaries[technical] == "ENGINEERING_BOUNDARY"
    assert boundaries[resource] == "RESOURCE_OR_LEASE_BOUNDARY"
    assert boundaries[negative] == "SCIENCE_DISPOSITION"

    # 4: PRESTART is one dormant scheduled continuation, never an active worker or Stop blocker.
    root = register_session_root(store, session_id="session-prestart")
    prestart_wf = store.open_actor_workflow(root.actor_context_id, "turn", "control", "prestart")
    prestart = store.record_scheduled_responsibility(
        prestart_wf, "lease:future",
        receiving_owner=root.actor_context_id, continuity_owner=root.actor_context_id,
        next_event="2026-08-24T14:01:23Z scheduled return", evidence_ref="fixture:prestart",
        disposition_reason="Future authorization has not admitted activity.",
    )
    prestart_state = store.workflow_state(prestart_wf)
    scheduled = prestart_state["current_responsibilities"][0]
    assert scheduled["obligation_id"] == prestart
    assert scheduled["responsibility"]["primary_queue"] == "SCHEDULED_CONTINUATION"
    assert scheduled["responsibility"]["boundary_domain"] == "RESOURCE_OR_LEASE_BOUNDARY"
    assert scheduled["responsibility"]["continuity_state"] == "DORMANT_SCHEDULED_CONTINUATION"
    assert scheduled["responsibility"]["active_worker"] is None
    assert prestart_state["open_obligations"] == prestart_state["tasks"] == []
    assert stop_decision_for_actor(store, root.actor_context_id, "turn-stop", False).get("decision") != "block"
    assert store.is_workflow_quiescent(prestart_wf)
    store.create_closure_receipt(prestart_wf, "COMPLETED", "actionable tranche ended")

    # 5: material custody without an owner is a durable orphan detection first;
    # only an explicit recovery owner can create its open responsibility.
    orphan_wf = _workflow(store, "orphan")
    orphan = store.detect_orphaned_material(
        orphan_wf, "direction:material", next_event="recovery owner is assigned",
        evidence_ref="fixture:material", disposition_reason="Material evidence lacks owner intake.",
    )
    orphan_state = store.workflow_state(orphan_wf)
    assert orphan_state["unowned_stalls"][0]["responsibility"]["primary_queue"] == "ORPHAN_RECOVERY"
    assert orphan_state["unowned_stalls"][0]["responsibility"]["boundary_domain"] == "CONTROL_PLANE_ANOMALY"
    assert orphan_state["unowned_stalls"][0]["responsibility"]["continuity_state"] == "UNOWNED_STALL"
    recovered = store.assign_orphan_recovery(
        orphan_wf, orphan, recovery_owner="recovery:owner", next_event="owner reconciles material custody",
        evidence_ref="fixture:material", disposition_reason="Recovery owner accepted custody.",
    )
    assert store.workflow_state(orphan_wf)["open_obligations"][0]["obligation_id"] == recovered
    assert store.workflow_state(orphan_wf)["unowned_stalls"] == []

    # 6: no-current is a resolved IDLE_COMPLETE record and requires no task.
    no_current_wf = _workflow(store, "no-current")
    completed = store.record_completed_responsibility(
        no_current_wf, "direction:complete", receiving_owner="em:direction",
        next_event="named discriminator changes", evidence_ref="fixture:complete",
        disposition_reason="The complete object has no current scientific action.",
        revisit_condition="A new target-bound discriminator is available.",
    )
    completed_state = store.workflow_state(no_current_wf)
    record = next(item for item in completed_state["responsibilities"] if item["obligation_id"] == completed)
    assert record["state"] == "RESOLVED"
    assert record["responsibility"]["continuity_state"] == "IDLE_COMPLETE"
    assert completed_state["open_obligations"] == completed_state["tasks"] == []


def test_invalid_standalone_status_and_unscheduled_resource_open_are_rejected(store: SemanticStore) -> None:
    workflow_id = _workflow(store, "invalid")
    with pytest.raises(ValueError, match="idle complete"):
        _handoff(store, workflow_id, ResponsibilityStage.RESOURCE_SHORTAGE_TO_RESOURCE_OR_SUBSTRATE_WAIT, "portfolio")
    with pytest.raises(ValueError, match="standalone status or cut tuple"):
        build_responsibility(
            stage=ResponsibilityStage.CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE,
            receiving_owner="em", active_worker="em", next_event="accept", evidence_ref="fixture", disposition_reason="BLOCKED",
        )
    with pytest.raises(ValueError, match="standalone status or cut tuple"):
        build_responsibility(
            stage=ResponsibilityStage.CM_RETURN_TO_SAME_DIRECTION_EM_INTAKE,
            receiving_owner="em", active_worker="em", next_event="accept", evidence_ref="fixture", disposition_reason="CUT_A|CUT_B",
        )


def test_local_return_scope_and_provider_no_resend_lifecycle(store: SemanticStore) -> None:
    workflow_id = _workflow(store, "local-provider")
    local = store.record_local_boundary_return(
        workflow_id, "direction:active", receiving_owner="em:active", active_worker="em:active",
        continuation_owner="em:active", boundary_domain=BoundaryDomain.CONTROL_PLANE_ANOMALY,
        affected_scope="subagent:transport-17", affected_actions=("RETRY_LOCAL_SUBAGENT",),
        unaffected_scopes=("DIRECTION_SCIENCE", "PORTFOLIO_DISPOSITION"),
        direction_primary_queue="ACTIVE_SCIENCE", next_event="EM observes local return",
        evidence_ref="fixture:local-subagent-failure", disposition_reason="Local subagent failure is scoped.",
    )
    projection = store.workflow_state(workflow_id)["open_obligations"][0]
    assert projection["obligation_id"] == local
    assert projection["boundary_domain"] == "CONTROL_PLANE_ANOMALY"
    assert projection["affected_scope"] == "subagent:transport-17"
    assert projection["affected_actions"] == ("RETRY_LOCAL_SUBAGENT",)
    assert projection["unaffected_scopes"] == ("DIRECTION_SCIENCE", "PORTFOLIO_DISPOSITION")
    assert projection["continuation_owner"] == "em:active"
    assert projection["direction_primary_queue"] == "ACTIVE_SCIENCE"
    with pytest.raises(ValueError, match="requires an exact EM/Portfolio authority artifact"):
        build_responsibility(
            stage=ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION,
            receiving_owner="em:active", active_worker="em:active", affected_scope="transport:17",
            affected_actions=("NO_RESEND",), unaffected_scopes=("DIRECTION_SCIENCE",),
            next_event="owner observes", evidence_ref="fixture:queue",
            disposition_reason="Local return remains scoped.", direction_primary_queue="ENGINEERING_REPAIR",
            prior_direction_primary_queue="ACTIVE_SCIENCE",
        )
    with pytest.raises(ValueError, match="authority owner"):
        build_responsibility(
            stage=ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION,
            receiving_owner="em:active", active_worker="em:active", affected_scope="transport:17",
            affected_actions=("NO_RESEND",), unaffected_scopes=("DIRECTION_SCIENCE",),
            next_event="owner observes", evidence_ref="fixture:queue",
            disposition_reason="A local transport artifact cannot change the queue.",
            direction_primary_queue="ENGINEERING_REPAIR", prior_direction_primary_queue="ACTIVE_SCIENCE",
            queue_authority_artifact="transport:local-return", queue_authority_owner="TRANSPORT",
        )
    changed_by_authority = build_responsibility(
        stage=ResponsibilityStage.LOCAL_BOUNDARY_RETURN_TO_CONTINUATION,
        receiving_owner="em:active", active_worker="em:active", affected_scope="transport:17",
        affected_actions=("NO_RESEND",), unaffected_scopes=("DIRECTION_SCIENCE",),
        next_event="owner observes", evidence_ref="fixture:queue",
        disposition_reason="Exact owner artifact changed the queue.", direction_primary_queue="ENGINEERING_REPAIR",
        prior_direction_primary_queue="ACTIVE_SCIENCE", queue_authority_artifact="portfolio:exact-authority",
        queue_authority_owner="PORTFOLIO",
    )
    assert changed_by_authority["queue_authority_artifact"] == "portfolio:exact-authority"
    assert changed_by_authority["queue_authority_owner"] == "PORTFOLIO"

    unknown = store.record_provider_transaction_lifecycle(
        workflow_id, "provider-unknown", send_commit_proved=None, local_archive_present=False,
        evidence_ref="fixture:archive-missing",
    )
    assert unknown == {
        "lifecycle": "COMMITTED_ACTIVE_OR_RESPONSE_UNKNOWN",
        "action": "RECONNECT_OR_OBSERVE_NO_DUPLICATE_SEND",
        "duplicate_send_forbidden": True,
        "local_archive_evidence": "ABSENT_OR_UNKNOWN_NONPROBATIVE",
    }
    assert projection["direction_primary_queue"] == "ACTIVE_SCIENCE"  # PROVIDER_NO_RESEND_THIS_TURN

    assert classify_provider_transaction(send_commit_proved=False) == {
        "lifecycle": "SEND_NOT_COMMITTED", "action": "EXACT_RETRY_ALLOWED", "duplicate_send_forbidden": False,
    }
    with pytest.raises(ValueError, match="contradictory provider lifecycle evidence"):
        classify_provider_transaction(send_commit_proved=False, terminal_no_response_proved=True)
    with pytest.raises(ValueError, match="recorded terminal-no-response evidence"):
        store.authorize_provider_recovery_resend(
            workflow_id, "provider-not-classified", lifecycle="COMMITTED_TERMINAL_NO_RESPONSE_PROVED",
            original_frozen_prompt_ref="prompt:sha256:exact",
            recovery_frozen_prompt_ref="prompt:sha256:exact", provenance_ref="fixture:invented",
        )
    terminal = store.record_provider_transaction_lifecycle(
        workflow_id, "provider-terminal", send_commit_proved=True, terminal_no_response_proved=True,
        evidence_ref="fixture:terminal-no-response",
    )
    assert terminal["lifecycle"] == ProviderTransactionLifecycle.COMMITTED_TERMINAL_NO_RESPONSE_PROVED.value
    first = store.authorize_provider_recovery_resend(
        workflow_id, "provider-terminal", lifecycle=str(terminal["lifecycle"]),
        original_frozen_prompt_ref="prompt:sha256:exact", recovery_frozen_prompt_ref="prompt:sha256:exact",
        provenance_ref="fixture:terminal-no-response",
    )
    assert first.startswith("evt_")
    with pytest.raises(ValueError, match="identical frozen prompt"):
        store.authorize_provider_recovery_resend(
            workflow_id, "provider-terminal", lifecycle=str(terminal["lifecycle"]),
            original_frozen_prompt_ref="prompt:sha256:exact", recovery_frozen_prompt_ref="prompt:sha256:different",
            provenance_ref="fixture:terminal-no-response",
        )
    with pytest.raises(ValueError, match="already exists"):
        store.authorize_provider_recovery_resend(
            workflow_id, "provider-terminal", lifecycle=str(terminal["lifecycle"]),
            original_frozen_prompt_ref="prompt:sha256:exact", recovery_frozen_prompt_ref="prompt:sha256:exact",
            provenance_ref="fixture:terminal-no-response",
        )
    complete = classify_provider_transaction(send_commit_proved=True, complete_response_present=True)
    assert complete == {
        "lifecycle": "COMPLETE_RESPONSE_PRESENT", "action": "ARCHIVE_NO_RESEND", "duplicate_send_forbidden": True,
    }

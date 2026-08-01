# CPM failure containment contract

```text
document_kind=code_project_manager_role_local_failure_containment_contract
session_owner_role=code_project_manager
session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
failure_scope=operation|workstream|session
child_terminal_effect=parent_evidence_only
local_failure_task_terminal=false
runnable_queue_scan=required_after_every_local_failure_terminal
session_continues_when=runnable_queue_nonempty
workstream_pause_condition=no_legal_action_in_that_workstream_after_registered_recovery
session_blocked_condition=global_integrity_prevents_every_CPM_action_or_all_authorized_workstreams_have_no_legal_next_action
session_blocked_proof_requirement=global_integrity_witness_or_complete_authorized_workstream_scan_when_scope_session
```

An operation is one child call, command, transport, candidate, run root or
verification attempt. Its failed terminal preserves evidence and triggers its bounded
recovery; it does not close its workstream.

A workstream may be parked only after its recovery is exhausted or while it
awaits a genuine external dependency. CPM scans and continues every independent
legal action. Scientific ambiguity pauses one claim; path collision pauses one
integration; neither stops the session.

`SESSION_BLOCKED` is valid only when the same global authority, identity or
workspace-integrity defect prevents every CPM-owned action, or when a complete
portfolio scan proves every authorized workstream has no legal next action.
An absent response, failed test/root, timed-out child, transport blocker or dirty
unrelated path cannot satisfy that condition by itself.

```text
scoped_diagnosis_fields=failure_scope|affected_workstream|failed_operation|preserved_evidence|recovery_taken|resume_condition|runnable_queue|session_continues|session_blocked_proof
```

Required routing witnesses:

```text
PRE_SEND_BLOCKED=operation|recover_or_park_transport|continue_runnable_queue
POST_SEND_BLOCKED=operation|preserve_and_observe_same_operation|continue_runnable_queue
READINESS_PHASE_FAILURE=operation|repair_or_new_candidate|continue_runnable_queue
WORKSTREAM_NO_LEGAL_ACTION=workstream|park_workstream|continue_other_workstreams
ALL_WORKSTREAMS_NO_LEGAL_ACTION=session|SESSION_BLOCKED_allowed_with_complete_proof
```

Scientific-loop terminal dispositions remain defined only by
`.agents/skills/hmasd-agile-research-development/SKILL.md`; this contract stops
a narrower failure from impersonating them.

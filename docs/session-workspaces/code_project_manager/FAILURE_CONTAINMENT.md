# CPM failure containment contract

```text
document_kind=code_project_manager_role_local_failure_containment_contract
session_owner_role=code_project_manager
session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
mechanical_operation_state_owner=originating_tool_or_script
typed_terminal_evidence=registered_receipt_or_exit_evidence
model_authored_operation_state_machine=forbidden
child_terminal_effect=evidence_only
local_failure_task_terminal=false
continuation_default=select_next_legal_action
session_blocked_evidence=global_integrity_witness_or_complete_no_legal_action_receipts
```

Each ticket, direct CPM transport, runner and readiness script owns its
mechanical lifecycle, counters and terminal state. Code, experiment and
verifier children return only their assigned typed receipt or exit evidence;
CPM never reconstructs or remembers a parallel state machine, and no transport
or monitor child observes a CPM Pro operation.

For External Pro transport, CPM follows
`docs/session-workspaces/code_project_manager/PRO_REVIEW_TRANSPORT.md`.
The same request recovers an existing durable operation without a send. A new
send is considered only after the originating tool verifies `present=false`.
The operation remains with CPM through archive and local FIFO intake; a
transport failure never creates a second observer or heartbeat.

After a local failure, CPM makes only a semantic choice: direct repair, a fresh
authorized attempt, parking the affected workstream, or another legal action.
Scientific ambiguity pauses one claim and path collision pauses one integration;
neither stops the session while a legal action remains visible in owner records.

`SESSION_BLOCKED` is an evidence conclusion requiring a global-integrity witness
blocking every CPM action, or receipts showing every workstream has no legal action.
A failed test/root, timed-out child, transport blocker or unrelated dirty
path cannot satisfy that condition by itself.

Transport, readiness and ticket terminal terms remain defined by their originating tools and Skills; this file adds no duplicate routing table.

# CPM direct External Pro transport contract

```text
document_kind=code_project_manager_role_local_direct_pro_transport_contract
session_owner_role=code_project_manager
session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
transport_owner=code_project_manager
execution_session=persistent_code_project_manager_session
lifecycle_source=.agents/skills/hmasd-agentify-pro-transport/SKILL.md
failure_containment_source=docs/session-workspaces/code_project_manager/FAILURE_CONTAINMENT.md
scientific_interpretation=forbidden
transport_child=none
monitor_child=none
heartbeat=forbidden
blocked_state_scope=operation
```

## Scope and ownership

Code Project Manager performs each formal or Explorer-to-project External Pro
review in its persistent session. The CPM session is the sole transport owner
and accepts only the typed Agentify receipt, exact raw archive and named local
FIFO intake. Code, experiment and verifier children remain available for their
separate assignments; no child owns, observes or relays a Pro transport.

The workstream selects exactly one stable key: `hmasd-formal-pro` for
`formal_toy_research`, `hmasd-uav-formal-pro` for `uav_validation`, or
`hmasd-explorer-validation-pro` for Explorer validation. Keys are not
interchangeable. CPM supplies the complete request, immutable question,
conversation identity, backend selection, operation key, absolute artifact
paths, timeout and terminal completion condition before starting transport.

## One direct lifecycle

For one assigned review CPM executes the blocking Agentify flow exactly once:

```text
prepare -> submit -> verify -> archive -> local_FIFO_intake
```

`submit --verify-existing` is the read-only recovery check. Reissuing the same
request recovers the existing durable operation without sending another user
message. A fresh operation is legal only after `present=false` and requires
one new operation key. `--allow-tab-creation` is permitted only for the first
binding or for a missing tab after an Agentify restart; no other page creation,
fallback, or alternate conversation is allowed.

While a generation is active or a readable complete response exists, CPM does
not refresh, interrupt, resend, or invoke `Answer now`, `Stop`, `Retry` or
`Continue`. CPM waits for the natural terminal state and records the originating
tool's typed evidence. Process existence, elapsed time and browser visibility
are not transport evidence.
CPM does not start a second submit process. Once `userMessageId` exists, it
observes and recovers only that durable operation.

After natural completion CPM archives the exact raw response first, then adds
the archived response to the local FIFO for mechanical intake and the owning
scientific review boundary. Intake does not reinterpret the response. No hash,
digest, fingerprint or byte count is a workflow predicate; Git revision IDs
remain source locators only.

## Assignment and terminal evidence

The CPM assignment names the review round, review kind, stable key, provider,
selected Pro model, live conversation URL/ID, operation key, question path,
backend path, raw archive path, receipt path, local FIFO path/schema, one-send
limit, recovery count, timeout, and exact write allow-list. Missing identity,
path, authority or completion data is a pre-send assignment defect; CPM does
not reconstruct it from history or repository search.
The assignment supplies a backend-selection path ending in `TRANSPORT_BACKEND.json` and the exact write allow-list for backend selection, request, receipt, raw response and intake artifacts for that review.

`COMPLETE` requires the typed receipt, exact raw archive and assigned FIFO
intake. `PRE_SEND_BLOCKED` must prove no durable user message exists.
`POST_SEND_BLOCKED` preserves the existing operation and forbids another send.
The originating Agentify tool owns its lifecycle, counters and terminal state;
CPM consumes its evidence and chooses the next legal action under the failure
containment contract. A transport blocker has no scientific disposition and
costs zero scientific iterations.

# CPM Pro review transport assignment contract

```text
document_kind=code_project_manager_role_local_assignment_contract
session_owner_role=code_project_manager
session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d
operator=hmasd-project-operations-operator
mode=PRO_REVIEW_TRANSPORT
lifecycle_source=.agents/skills/hmasd-agentify-pro-transport/SKILL.md
shared_operator_source=.agents/roles/PROJECT_OPERATIONS_OPERATOR.md
page_mutation=forbidden
scientific_interpretation=forbidden
```

## Complete assignment

Every CPM Pro-transport child receives one complete assignment containing:

- `session_owner_role=code_project_manager` and the exact CPM session ID;
- this contract path and the shared Agentify transport Skill path;
- review round, assignment identity, review kind and full stage commit;
- immutable question path, exact item root, raw archive path and mechanical
  intake path/schema;
- one new absolute backend-selection path ending in `TRANSPORT_BACKEND.json`,
  plus the new absolute request and receipt paths;
- transport owner, workstream-specific stable key, provider, selected Pro
  model, exact live conversation URL/ID and one new operation key;
- submission limit, recovery-operation count, absolute timeout and terminal
  completion condition; and
- the exact write allow-list for backend selection, request, receipt, raw
  response and intake.

A missing field is a pre-send assignment defect. The child does not reconstruct
it from task history, repository search or another workstream.

## Full child ownership

The shared Skill and shared operator charter are the single source for the
transport lifecycle, confirmation window, durable-ledger predicates and
terminal semantics. The child owns one lifecycle from request preparation
through mechanical intake and reports every lifecycle transition natively to
its CPM parent. Long-operation progress follows only the shared progress rule
and includes the exact durable operation phase and message identities already
available; a bare "waiting" report is invalid.

CPM does not start a second submit process, read the Agentify ledger in parallel,
operate the page or interrupt a post-send operation. The child alone supervises
its owned submit worker. It may terminate that worker only when the shared
contract proves the irreversible user-message boundary has not been crossed.
Once `userMessageId` exists, the child observes the same operation to a shared
terminal state and never retries or substitutes a page.

On complete transport, the child validates the receipt, archives exact raw
bytes, performs only the assigned mechanical intake and returns one
`PROJECT_OPERATIONS_TERMINAL`. On a blocker it returns the exact last lifecycle
phase, ledger predicates, worker outcome and artifact inventory. It never
chooses recovery, interprets the response, edits current work, runs Git or
starts successor activity.

## Parent acceptance

CPM accepts only the shared operator's typed native final and the named
artifacts. `COMPLETE` requires the shared receipt and archive predicates plus
the assigned intake. `PRE_SEND_BLOCKED` must prove no durable user message;
`POST_SEND_BLOCKED` preserves the existing operation and forbids another send.
Process existence, elapsed time and browser visibility alone are never
transport evidence.

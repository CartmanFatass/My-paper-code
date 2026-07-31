# Agentify Pro Transport Migration Plan

```text
document_kind=workflow_design_baseline
status=USER_APPROVED_FOR_IMPLEMENTATION
owner=workflow_design_manager
scope=agentify_controlled_fork_install_smoke_and_optional_hmasd_backend
scientific_authority=none
formal_compute=false
scientific_iteration_cost=zero
```

## Purpose

This plan replaces fragile browser-page inference with an optional, receipt-bearing
Agentify transport while preserving the existing HMASD authority split. It is an
implementation baseline, not a frozen source-code prescription: mechanical details
may adapt to the inspected Agentify interfaces, but the invariants and acceptance
fences below may not be weakened without a new user decision.

The migration does not replace the three persistent Pro conversations. It gives each
registered conversation a stable key and binds each review operation to exactly one
conversation, one user turn, one assistant turn and one immutable request identity.

## Work sequence

### 1. Close the existing Explorer validation workflow change

Before Agentify work, independently review, verify, commit and push the already
accepted Explorer--Ops--Code-PM validation change as one exact twelve-path commit:

1. `AGENTS.md`
2. `.agents/roles/RESEARCH_OPERATIONS_MANAGER.md`
3. `.agents/roles/CODE_PROJECT_MANAGER.md`
4. `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md`
5. `.agents/roles/EXTERNAL_PRO.md`
6. `.agents/skills/hmasd-independent-research-exploration/SKILL.md`
7. `.agents/skills/hmasd-explorer-project-validation/SKILL.md`
8. `.agents/skills/hmasd-explorer-project-validation/scripts/explorer_project_packet.py`
9. `docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`
10. `tests/hmasd_explorer_project_validation_packet_test.py`
11. `tests/hmasd_research_workflow_contract_test.ps1`
12. `tests/hmasd_code_project_manager_contract_test.ps1`

The Agentify design document and later implementation paths are not part of that
commit.

### 2. Prepare a controlled Agentify fork

Use these identities:

```text
origin=https://github.com/CartmanFatass/desktop.git
upstream=https://github.com/agentify-sh/desktop.git
local_checkout=C:/Projects/agentify-desktop
branch=codex/hmasd-strict-review-transport
```

Expected fork paths are bounded to the smallest interface surface needed after live
inspection:

- `README.md`
- `SECURITY.md`
- `package.json`
- `selectors.json`
- `state.mjs`
- `tab-manager.mjs`
- `chatgpt-controller.mjs`
- `http-api.mjs`
- `mcp-server.mjs`
- `review-transport.mjs`
- focused tests for state, tab management, controller, HTTP API and review transport

Write failing regression tests before implementing the new transport behavior.

### 3. Add strict receipt-bearing review transport

Add one high-level operation, exposed through MCP as
`agentify_review_query`, with these required properties:

- stable-key binding persists across Agentify restart;
- the binding includes exact provider, Pro model, URL and conversation identity;
- the request has an idempotency key plus exact prompt bytes and SHA-256;
- one operation may submit the prompt at most once;
- no automatic `Continue`, `Retry`, `ResponseRetry` or `Answer now` action;
- no unrestricted `main.innerText` fallback as response identity;
- exact user-message and assistant-message identities are recorded;
- natural completion requires the same assistant message in two snapshots at least
  three seconds apart with no active-generation or continuation controls;
- maximum wait is configurable through the operation, with a 45-minute HMASD
  ceiling and no hidden eight-minute internal cap;
- restart recovery is observe-only for the same operation identity;
- ambiguous identity, unreadable content or state mismatch fails closed without a
  duplicate send;
- the terminal receipt contains request, conversation, message, snapshot, control,
  timing and response-hash evidence.

The operation ledger must be written atomically. A duplicate idempotency key with
the same request returns the existing operation state; a conflicting payload is
rejected.

### 4. Review, verify and push the fork

Run focused unit and integration tests, then use an independent read-only reviewer
to check:

- duplicate-send prevention;
- persistence and restart behavior;
- selector and identity ambiguity;
- timeout and natural-completion semantics;
- absence of implicit UI controls;
- secret handling and loopback-only API exposure;
- unnecessary context, semantic drift and needless blocking.

Address actionable findings within the accepted fork paths, verify the exact diff,
commit and push the controlled branch.

### 5. Install and perform one non-scientific smoke

Install from the fixed pushed commit. Approved external write locations are:

```text
C:/Projects/agentify-desktop/node_modules
C:/Users/fires/.agentify-desktop/
C:/Users/fires/.codex/config.toml
```

Register the Codex MCP entry with the fixed local executable:

```text
node C:/Projects/agentify-desktop/bin/agentify-desktop.mjs mcp
```

Use an isolated Chrome profile. If interactive sign-in is required, open a visible
window and wait for the user rather than bypassing authentication.

Smoke identity:

```text
idempotency_key=hmasd-agentify-transport-smoke
kind=non_scientific_transport_smoke
```

Use a harmless exact challenge. Acceptance requires:

- the intended Pro model and registered conversation are proven;
- exactly one user send is recorded;
- prompt and response hashes plus exact message identities are returned;
- two stable completion snapshots satisfy the timing rule;
- no prohibited control was activated;
- restart recovery observes the same conversation and operation;
- a duplicate idempotency key is rejected or returns the existing receipt without a
  new send.

Close only the smoke tab after acceptance. The smoke does not create a scientific
review, project state transition or iteration cost.

### 6. Add an optional HMASD backend

Expected HMASD paths are:

1. `AGENTS.md`
2. `.agents/roles/RESEARCH_OPERATIONS_MANAGER.md`
3. `.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md`
4. `.agents/skills/hmasd-review-round/SKILL.md`
5. `.agents/skills/hmasd-independent-research-pro-review/SKILL.md`
6. `.agents/skills/hmasd-agentify-pro-transport/SKILL.md`
7. `.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py`
8. `docs/project/AGENTIFY_PRO_TRANSPORT.md`
9. `tests/hmasd_agentify_pro_transport_test.py`
10. `tests/review_round_contract_test.ps1`
11. `tests/hmasd_research_workflow_contract_test.ps1`

Production stable keys are:

```text
hmasd-formal-pro=research_operations_manager
hmasd-independent-research-pro=independent_research_review_operator
hmasd-explorer-validation-pro=research_operations_manager
```

Conversation IDs remain runtime-owned and are never committed to Git. A review round
selects exactly one backend before submission. Agentify and the existing transport
may coexist as available mechanisms, but never submit or monitor the same round in
parallel.

The HMASD wrapper mechanically validates the Agentify receipt against the frozen
round identity, exact prompt hash, stable key, conversation identity, Pro model,
message identities, completion snapshots and response hash before normal verbatim
archival and mechanical intake. It does not interpret science.

## Invariants that may not be adjusted mechanically

- Workflow Design Manager owns only stable workflow design.
- Research Operations Manager owns formal Pro transport and runtime state.
- Independent Research Review Operator owns only its separate authorized Pro
  transport and archive.
- External Pro retains scientific authority within the submitted boundary.
- No Agentify operation authorizes compute, science, code acceptance or project-state
  advancement.
- No duplicate submission, `Answer now`, automatic retry, response synthesis or
  cross-conversation fallback.
- Exact raw response archival remains mandatory after identity and natural completion
  are proven.
- A transport failure costs zero scientific iterations.
- Existing persistent Pro conversations are reused; smoke testing does not mutate
  their project review histories.
- Secrets, authentication material and live conversation registrations are runtime
  state, not repository content.

## Allowed implementation adjustments

Workflow Design Manager may make and record bounded adjustments without another plan
confirmation when live inspection shows a different symbol, file split, test filename
or local installation command, provided that:

1. the adjustment is mechanical and stays inside the same fork or HMASD control-plane
   responsibility;
2. it does not add a submission, browser action, authority, scientific interpretation
   or repository-external write location;
3. the final exact path set and reason are reported;
4. regression coverage remains equivalent or stronger; and
5. all non-adjustable invariants remain true.

A new user decision is required for a different external application, new credential
or egress scope, altered persistent conversation ownership, weakened fail-closed
behavior, automated UI controls, scientific/runtime authority, or any production
submission beyond the approved smoke.

## Completion evidence

Completion requires all of the following:

- the existing Explorer twelve-path commit is independently accepted, verified and
  pushed;
- the Agentify fork commit and exact path set are independently accepted, tested and
  pushed;
- installation is pinned to that commit and the MCP registration is observable;
- the smoke produces one complete receipt satisfying every acceptance predicate;
- the HMASD optional backend passes focused script and PowerShell contracts;
- the HMASD workflow commit is independently reviewed, pushed and returned to the
  locked role routes;
- local and remote commit identities match for both repositories.

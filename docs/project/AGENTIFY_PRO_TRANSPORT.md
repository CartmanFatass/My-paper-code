# Agentify Pro transport

```text
document_kind=workflow_control_contract
status=sole_backend
formal_compute=false
scientific_iteration_cost=zero
agentify_source=https://github.com/CartmanFatass/desktop.git
agentify_branch=codex/hmasd-strict-review-transport
agentify_required_commit=read_AGENTIFY_REQUIRED_COMMIT_from_wrapper
browser_backend=chrome-cdp
browser_window_policy=one_agentify_process_one_chrome_window
stable_key_tab_policy=one_live_tab_per_stable_key
transport_tab_mutation=forbidden
missing_or_mismatched_tab=fail_before_review_query
prompt_visible_required_before_send=true
send_confirmation_timeout_seconds=60
ledger_poll_seconds=1
generation_progress_interval_seconds=300
process_existence_is_send_evidence=false
transport_lifecycle=PREPARED|TAB_READY|DISPATCH_STARTED|MESSAGE_CONFIRMED|GENERATING|STABLE_COMPLETE|ARCHIVED|INTAKE_COMPLETE
transport_terminal=PRE_SEND_BLOCKED|POST_SEND_BLOCKED
```

Browser transport is retired; Agentify is the sole External Pro transport.

## Stable-key ownership

| Stable key | Owner | Use |
|---|---|---|
| `hmasd-formal-pro` | Code Project Manager | `formal_toy_research` Pro conversation |
| `hmasd-uav-formal-pro` | Code Project Manager | `uav_validation` Pro conversation |
| `hmasd-explorer-validation-pro` | Code Project Manager | Explorer validation Pro conversation |
| `hmasd-independent-research-pro` | Independent Research Pro Review Operator | independent-research Pro conversation |

Stable keys identify a runtime binding, not a repository conversation record.
The three Code Project Manager keys are workstream-specific and cannot
substitute for one another.
After Agentify first persists a stable-key binding, later operations must match
it; tab navigation cannot rebind or overwrite that durable binding.
Every transport operation requires exactly one pre-existing live tab for its
stable key and reuses that exact tab. The wrapper verifies the tab's key,
provider, conversation URL, idle status and `promptVisible=true` through authenticated read-only
Agentify endpoints before `/review-query`. It never creates, closes, shows,
activates, navigates, refreshes, replaces or rebinds a page. A missing,
duplicate, blocked, busy or mismatched tab is terminal for that operation; the
transport does not recreate it after Agentify or Chrome restart and does not
fall back to another tab or window.
Conversation IDs, URLs, model evidence, credentials, authentication material
and live registrations are runtime-only and must never be committed or placed
in role/Skill text. The binding is loaded from the local Agentify state at the
time of the operation and must match the selected owner and requested Pro
model before sending.

Independent direction reviews use the shared
`hmasd-project-operations-operator` in `INDEPENDENT_DIRECTION_REVIEW` mode,
parented by the Explorer. The transport owner and stable key remain
`independent_research_review_operator` and `hmasd-independent-research-pro`;
the assignment owns one exact `local_research/pro_reviews/<review-id>/` root
and its owner-local page/evidence record. The shared operator has no global
page registry and cannot use a CPM workstream record.

## One-round protocol

1. The owning role verifies an active user grant or one explicit review
   assignment. For Agentify, the
   registered wrapper reads the UTF-8 prompt and writes one new role-owned
   `TRANSPORT_BACKEND.json` plus its matching request.
2. The immutable selection is reloaded before every send or recovery.
3. For Agentify, the owner resolves its stable key to one already-live runtime
   conversation tab and uses the wrapper's `prepare` command to persist the
   immutable request identity before sending.
4. Immediately before submission, the wrapper reads `/tabs` and scoped
   `/status`; only one exact, unblocked, idle and prompt-visible tab permits a
   new `/review-query` send.
   These checks perform no page mutation and a failure permits no create,
   navigation or fallback action.
5. The wrapper starts one owned synchronous submit worker and separately polls
   Agentify's durable operation ledger. `MESSAGE_CONFIRMED` requires exactly
   one send/action, non-null user-message identity and submission time, and
   exact tab/conversation identity. Process existence is never send evidence.
6. If no message is confirmed within 60 seconds, terminate only that worker,
   reread the ledger, return `PRE_SEND_BLOCKED`, and do not resend. Once a
   user-message identity exists, never terminate or retry; observe only that
   operation until natural completion or `POST_SEND_BLOCKED`.
   `userMessageId` is the irreversible post-send boundary even when another
   identity predicate is missing; early worker exit never shortens the
   60-second ledger-confirmation window.
7. Agentify submits at most one exact prompt for that operation. It does not
   click `Answer now`, `Continue`, `Retry` or `ResponseRetry`.
8. The transport validator
   `.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py`
   checks the stable key, conversation, selected model, completion snapshots
   and archived response integrity.
9. Only a complete validated request/receipt pair permits exact raw archival
   and assigned mechanical intake. Lifecycle phase changes are observable; a
   long `GENERATING` phase reports at most every five minutes. The receipt is evidence of transport only;
   it cannot interpret science or authorize code, compute or project state.

An unavailable conversation or incomplete response stops that operation. The
Minimal recovery rule permits bounded fresh operations inside the same active
review authority; it never permits a send while generation or a readable
complete response exists and never permits a new or replacement page. Every
fresh operation must reuse the same pre-existing exact idle tab. A transport
failure consumes zero scientific iterations.

## Minimal recovery

The defining rule is `.agents/skills/hmasd-agentify-pro-transport/SKILL.md#minimal-recovery`.

## Runtime and installation boundary

Its public `/health` supplies `sourceCommit` and `sourceDirty`; the wrapper must match both before any send. Its MCP
registration is
`node C:/Projects/agentify-desktop/bin/agentify-desktop.mjs mcp`.
Agentify installation and its local state are outside HMASD Git. Credentials and
conversation bindings remain in the approved runtime locations. Workflow files
record only stable keys, owners, validator paths and invariants. The Agentify
service writes only its local transport ledger. The HMASD wrapper may write the
role-owned immutable backend selection, runtime request/receipt and, after
validation, the exact raw archive;
it may not write `CURRENT_WORK`, science, code, mechanical interpretation or Git
state.

## Acceptance evidence

The owning role returns one validated request/receipt pair. The request contains
the selected backend and selection path; the durable operation plus receipt
bind the stable key, conversation and tab identity, `sendCount=1`,
`sendActionCount=1`, non-null message identities and `submittedAt`, completion
snapshots, control state, timing and response integrity. A
duplicate idempotency key with the same request returns the existing operation;
a conflicting payload is rejected. Restart recovery observes the same operation
and conversation without sending again.

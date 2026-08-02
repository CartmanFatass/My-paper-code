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
providers=chatgpt|gemini
provider_workflow=one_parameterized_strict_review_interface
reviewer_payload=standalone_RAW_QUESTION_only
transport_tab_mutation=forbidden_except_first_chatgpt_binding_or_post_restart_reopen_or_exact_default_tab_adoption
missing_or_mismatched_tab=fail_before_review_query_unless_explicit_exact_default_tab_adoption
prompt_visible_required_before_send=true
process_existence_is_send_evidence=false
transport_lifecycle=prepare|submit_once|verify_natural_completion|archive_exact_response
transport_terminal=NATURAL_COMPLETION_VERIFIED|AGENTIFY_TRANSPORT_BLOCKED
```

Browser transport is retired; Agentify is the sole External Pro transport.

## Stable-key ownership

| Stable key | Owner | Use |
|---|---|---|
| `hmasd-formal-pro` | Code Project Manager | `formal_toy_research` Pro conversation |
| `hmasd-uav-formal-pro` | Code Project Manager | `uav_validation` Pro conversation |
| `hmasd-explorer-validation-pro` | Code Project Manager | Explorer validation Pro conversation |
| `hmasd-independent-research-explorer-pro` | Independent Research Explorer | independent-research Pro conversation |
| `hmasd-independent-research-explorer-gemini` | Independent Research Explorer | independent-research Gemini advisory conversation |

Stable keys identify a runtime binding, not a repository conversation record.
The three Code Project Manager keys are workstream-specific and cannot
substitute for one another.
After Agentify first persists a stable-key binding, later operations must match
it; tab navigation cannot rebind or overwrite that durable binding.
Every transport operation normally requires one live tab for its stable key and
reuses that exact tab. The wrapper verifies the tab's key, provider,
conversation URL, idle status and `promptVisible=true` through authenticated
read-only Agentify endpoints before `/review-query`. It never closes, shows,
activates, navigates, refreshes, replaces or rebinds a page. The explicit
`--allow-tab-creation` flag may create one missing tab only for the first
binding or post-restart recovery. A missing, duplicate, blocked, busy or
mismatched tab is otherwise terminal for that operation; the transport does
not fall back to another tab or window.
For an existing durable binding, `--adopt-existing-tab` may instead rename one
unique already-live exact URL/provider tab whose current key is only `default`
or empty. This creates no page, performs no navigation and leaves the durable
conversation binding unchanged.
Conversation IDs, URLs, model evidence, credentials, authentication material
and live registrations are runtime-only and must never be committed or placed
in role/Skill text. The binding is loaded from the local Agentify state at the
time of the operation and must match the selected owner and requested Pro
model before sending.

Independent reviews run directly in the persistent Explorer session. ChatGPT
and Gemini are two provider instances of this same contract and receive the
same standalone natural-language question. Pro canonical/Gemini advisory
labels exist only in local intake metadata. Each operation owns one exact
`local_research/pro_reviews/<review-id>/` root; Explorer never reuses a CPM
workstream record.

## One-round protocol

1. Freeze a concise local execution plan: standalone `RAW_QUESTION`, provider
   instances and live pages, operation keys and maximum sends, status checks,
   archive paths, verify-existing recovery and completion criteria. This plan
   and all authority/identity fields remain local in the role-owned
   `TRANSPORT_BACKEND.json`, request and receipt.
2. `prepare` validates the local request without searching the question for
   assignment or Git metadata. Existing bindings use live URL/ID/model. First
   ChatGPT binding starts from one authenticated blank root page; the single
   persisted question creates and durably binds the real conversation. Gemini
   uses its existing `/app/<id>` page through the same interface.
3. Read authenticated `/tabs` and scoped `/status`. Only one exact, idle,
   unblocked and prompt-visible page permits strict `/review-query`.
4. Insert the whole question once, verify the composer and send once. Durable
   user-message identity proves the irreversible boundary; process existence
   does not. Never use generic query, per-character typing, attachment,
   computer-use, placeholder or response-control fallback.
5. Observe the same operation until the same assistant message and text are
   stable in two snapshots at least three seconds apart and generation is
   inactive. Then validate and archive the exact response once.

If evidence invalidates the plan, stop that branch and use read-only status plus
`submit --verify-existing`. `present=true` resumes observation; only
`present=false`, no persisted user message and an unchanged question permit one
fresh operation key and at most one fresh send. A second failure is
`AGENTIFY_TRANSPORT_BLOCKED`, not science, and consumes zero scientific
iterations.

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

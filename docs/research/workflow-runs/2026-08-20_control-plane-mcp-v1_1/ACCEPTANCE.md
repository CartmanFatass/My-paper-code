# HMASD MCP Control Plane V1.1 Acceptance

```text
acceptance_id=HMASD-MCP-CONTROL-PLANE-V1.1-20260820
baseline=ShadowMcp-V1
status=ACCEPTED
scope=control-plane-only
automatic_wake=false
scheduler_serve=false
stage5=false
agents_sdk=false
provider_sends=0
scientific_state_changes=0
production_restarts=0
push_performed=false
```

## Accepted topology

V1.1 keeps the seven Shadow hooks audit/probe-only and exposes two optional
local STDIO MCP servers. Both servers have `required=false`; failure of either
server does not prevent ordinary Codex work.

`hmasd_observability` is read-only and exposes exactly:

1. `control_plane_health`
2. `control_plane_doctor`
3. `control_plane_incidents`
4. `long_effect_observe`
5. `mcp_instance_list`

`hmasd_orchestrator` retains the existing semantic SQLite ledger and exposes
exactly the 34 tools listed in `.codex/config.toml`. Its inventory is locked in
source and tests as 13 read-only tools and 21 mutation tools. Every mutation
tool carries the common requester/source/user-authority inputs and is forced
through the same admission path before its domain operation can execute.

The configuration uses the supported local STDIO transport, server
instructions, explicit `enabled_tools`, bounded startup/tool timeouts, and
optional-server behavior described by the official [OpenAI MCP
documentation](https://learn.chatgpt.com/docs/extend/mcp) and [Codex
configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

## Deterministic waiting contract

`workflow_wait_plan(session_id, timeout_s=900)` is a read-only projection, not
a new workflow state machine. Its only actions are:

- `NO_ACTIVE_WORKFLOW`
- `REPORT_INTAKE_REQUIRED`
- `OBLIGATION_ACTION_REQUIRED`
- `WAIT_SEMANTIC_EVENT`
- `WORKFLOW_CLOSE_ELIGIBLE`

The priority is report intake, obligation action, open-task wait, then workflow
closure. Only `WAIT_SEMANTIC_EVENT` permits `workflow_await_event`; its
condition is exactly `ANY_REPORT`, and its `after_seq` is the current
`await_cursor`, never `state_version` or free text.

The Root routing contract is now explicit:

1. Inspect native collaboration agents first.
2. Use `collaboration.wait_agent` while a native child is running.
3. Only with no native child, call `workflow_wait_plan`.
4. Call semantic await only for `WAIT_SEMANTIC_EVENT` and copy the returned
   fields exactly.
5. Observe file-backed long effects only through `long_effect_observe`.
6. End the turn when none of those routes applies.

This does not provide wake-after-task-end behavior.

## Permission acceptance

The static tool inventory and operation map are import-time invariants. The
common mutation admission validates a bound ACTIVE actor, role class, exact
object owner, authoritative source kind, and any necessary typed user-authority
grant. Owner/role rejection occurs before a grant can be consumed. Tests prove
that wrong-owner, inactive-actor, missing-source and missing-requester
rejections leave the database unchanged. Raw report text is separately limited
to the bound active workflow owner; default report views remain non-raw.

Configuration approval behavior is not treated as an ACL and no scientific,
portfolio, lease or direction authority was added.

## MCP instance evidence

Each STDIO process publishes only runtime evidence under
`runtime/hmasd-control-plane/mcp-instances/<instance-id>/`:

- `start.json`
- `terminal.json` on normal return only

The record contains process identity, PID/parent PID, creation identity,
server/profile, transport, repository root, optional semantic state path and
timestamps. It contains no environment, token, prompt or user content. Doctor
classifies an instance as `ACTIVE`, `CLOSED`, `STALE` or `UNKNOWN` using PID
and process creation identity together. There is no heartbeat, singleton
lease, cleanup, restart, retry or wake behavior.

At the final live canary snapshot the index contained 11 records: 6 active
STDIO instances, 3 normally closed canary instances, 2 historical abnormal
closures classified `STALE`, and 0 unknown or conflicting records. Multiple
active STDIO instances produced one informational finding only.

## Validation evidence

All Python commands used
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`; every pytest invocation
used a unique explicit `--basetemp`.

- Semantic, context-lifecycle and control-plane regression: `405 passed`.
- RISP minimal synchronous long-effect adapter regression: `11 passed`.
- Focused semantic event-wake and neutral-timeout canary: `2 passed`.
- Actual STDIO integration included two concurrent observability servers and
  one orchestrator server; tool inventories, instructions, unique instance IDs
  and normal terminal publication matched the frozen contracts.
- `compileall` passed for the changed Python packages and tests.
- Scoped `git diff --check` passed; only the repository's expected CRLF
  conversion warnings were emitted.

## Harmless live canaries

The live sequence performed no provider request, scientific computation or
research-state mutation.

1. `codex mcp list/get` parsed both enabled servers and both exact allowlists.
2. Real local STDIO clients initialized both servers and received their server
   instructions.
3. Read-only Doctor and incident collection hashed 16 existing source files
   before and after; changed-input count was zero.
4. Live `workflow_wait_plan` on an absent session returned
   `NO_ACTIVE_WORKFLOW`; the semantic SQLite file hash was unchanged.
5. `long_effect_observe` found the existing harmless canary's terminal without
   reading stdout, stderr or output content.
6. Two real concurrent observability connections had distinct instance IDs;
   normal closure published complete terminal records.
7. A temporary semantic store produced one event wake and one
   `TIMEOUT_NO_DISPOSITION` result without a long-held write transaction.
8. A live Shadow `Stop` probe returned only `{"continue": true}` and left the
   semantic SQLite hash unchanged.
9. Component Doctor reported no partial long-effect record, no unknown MCP
   record, no duplicate instance ID and no MCP-record error.
10. Activation disable and ShadowMcp enable dry-runs completed with verified
    hashes; the runtime activation receipt was reconciled to the V1.1 config
    hash.

The all-component Doctor remains `UNAVAILABLE` because the optional external
supervisor SQLite source is absent. It also preserves 17 historical Agentify
ambiguous-operation incidents and 2 historical stale MCP-process records. These
are intentionally visible evidence, not V1.1 failures and not scientific or
portfolio dispositions. The semantic ledger has zero open legacy obligations
and zero open legacy tasks.

## Acceptance thresholds

```text
unknown_await_condition_failures=0
readonly_source_mutations=0
sensitive_field_exposures=0
unauthorized_semantic_writes=0
duplicate_mcp_instance_ids=0
misclassified_pid_reuse=0
long_held_sqlite_write_transactions=0
shadow_blocking_decisions=0
provider_sends=0
scientific_state_changes=0
automatic_retries=0
automatic_wakes=0
rollback_failures=0
```

## Known limits

- Codex tool manifests are fixed for an already-running model turn. The live
  configuration and newly spawned STDIO processes use V1.1, while a turn that
  began before the config edit may retain its earlier tool snapshot until the
  next turn/task initialization.
- A host-killed STDIO server cannot publish a normal terminal; Doctor reports a
  stale record and performs no cleanup or restart.
- MCP wait operates only while the current task is active. It cannot wake an
  ended task.
- V1.1 intentionally provides no pagination cursor beyond bounded truncation,
  no Streamable HTTP service, no subscription, no dashboard and no role-shaped
  tool visibility.
- The optional external supervisor source remains unavailable on this host;
  source absence is reported rather than synthesized or repaired.

## Rollback

V1.1 rollback is configuration-only: disable/remove
`hmasd_observability` and restore the prior orchestrator allowlist. Shadow hooks
and the semantic SQLite ledger are not rolled back. Runtime instance records
and Doctor snapshots are disposable evidence, but V1.1 performs no automatic
cleanup. The accepted V1 history remains unchanged.

No push was authorized. The out-of-scope extension roadmap is frozen separately
in `POST_V1_1_EXTENSION_PLAN.md` and creates no implementation authority.

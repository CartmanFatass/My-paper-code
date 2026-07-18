---
name: hmasd-review-round
description: "Use when creating or resuming a tracked HMASD five-stage external-review round governed by 05_REVIEW_STATE.json. Do not use for prompt generation, manual handoff, one returned review, literature discussion, brainstorming, single-reviewer consultation, routine result interpretation, or a contract-determined disposition."
---

# HMASD Review Round

Read the round's `00_REVIEW_BRIEF.md`, `01_SHARED_SOURCE_MANIFEST.md`, and
`references/review-protocol.md`. Gemini additionally reads
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Read
`docs/external-review/REVIEWER_CONVERSATIONS.json` before external transport and
the neutral `docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` only for a Pro
submission.

## State Authority

Create and update `05_REVIEW_STATE.json` only through
`scripts/review_state.ps1`. Run `validate`, `show`, and `next` once when the
round is activated and after an actual state transition. Do not repeat them
while an external stage remains `DISPATCHED`.

States mean:

- `NOT_STARTED`: no guarded Exchange dispatch was delivered;
- `DISPATCHED`: the exact route was delivered to the registered Exchange task;
- `COMPLETE`: the exact raw is archived and a completion receipt is accepted;
- `BLOCKED`: an actionable authority, identity, source, authentication, or
  transport problem prevents progress.

`COMPLETE` is immutable. Never infer progress from artifact presence or prose,
move `DISPATCHED` back to `NOT_STARTED`, or resubmit an identity-confirmed raw.
Leaving `BLOCKED` requires the script's typed resolution receipt.

External receipts retain exactly these fields:

```text
source;session;conversation;role;model;route;terminal;reference
```

A new transport uses `source=exchange`, the registered Codex Exchange task ID
as `session`, the registered external conversation as `conversation`, and an
exact `turn:<uuid>#item-<id>` from `read_thread` as `reference`. Dispatch and
completion references must differ and must come from the same Exchange task.
Existing `source=gemini` transcript receipts and manual user-message receipts
remain valid history and are never rewritten.

## Round Order

1. Freeze one shared evidence boundary and exact source allowlists.
2. Run Gemini and open Pro as blind, independent divergent reviewers with equal
   standing. Serialize external transport; do not run two browser/CLI stages at
   once.
3. Archive both raws before the controller writes synthesis.
4. Give both raws and synthesis to convergent Pro.
5. Archive its raw, then let only the controller write disposition and update
   the owning project document.

The convergent reviewer ranks and attacks two to four live candidates when the
evidence supports them. It may recommend a stop or one serialized evidence
source, but it cannot authorize code, experiments, promotion, retirement, or a
unique legal research direction.

## Verify the Pro Evidence Boundary

Before a Pro stage, resolve one full 40-character commit reachable from remote
`aggressive`. Require an explicit reviewer role, an exact `Repository files to
inspect` section, and every listed path at that commit. Run
`scripts/verify_pro_review_boundary.ps1`. A failed check is
`BLOCKED_REMOTE_EVIDENCE`; do not send the reviewer to discover missing inputs.

## One-to-One Codex Exchanges

Gemini, Open Pro and Convergent Pro each have one persistent local Codex
Exchange task bound one-to-one to one external reviewer session. Reuse the
registered task; never create a replacement, mix roles, hand off the task,
rename it, open its model selector or modify its model. The task API does not
expose authoritative live model settings, so never claim a live model check or
attempt a model repair. A user- or UI-reported mismatch is
`BLOCKED_REVIEW_THREAD_IDENTITY`.

Before dispatch, call `codex_app__read_thread` and require the registry's exact
`host_id`, `thread_id`, title, `C:\project\HMASD` cwd and a non-running status.
Then use the only legal controller-to-Exchange call shape:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<registered exchange host_id>",
  threadId: "<registered exchange thread_id>",
  prompt: "<internal route payload>"
})
```

Do not add `model` or `thinking`. Under the current tool contract, omission
keeps the target task's current settings; supplying either field is a model
override. Read the same Exchange task once after delivery and require the exact
route message before recording `DISPATCHED`.

The internal payload contains exactly:

```text
ACTIVE_DISPATCH
route=<route token>
round=<round path>
commit=<40-character commit>
question=<registered question path>
raw=<registered raw path>
controller_host_id=<current controller host>
controller_thread_id=<current controller task>
```

Models, reasoning settings and external prompt text are not routing fields.
Internal route data never enters ChatGPT or Antigravity.

## Required Terminal Relay

An Exchange local final answer is not controller notification. Before ending a
`COMPLETE`, actionable `BLOCKED`, or unavoidable `WAIT_PRO_THINKING` turn, the
Exchange reads the exact controller task from the current dispatch and calls
exactly once:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<controller_host_id from current dispatch>",
  threadId: "<controller_thread_id from current dispatch>",
  prompt: "REVIEW_RELAY\nroute=<exact route>\nterminal=<COMPLETE|BLOCKED|WAIT_PRO_THINKING>\nraw=<registered raw or none>\nreason=<single line or none>"
})
```

Again, omit `model` and `thinking`. Read the controller task once to confirm the
relay arrived, then answer locally `RELAY_SENT route=<exact route>`. A missing
or ambiguous delivery is `BLOCKED_CONTROLLER_RELAY`; never send a duplicate or
message the other Exchange.

Do not use review transport subagents, `collaboration.send_message`, heartbeat,
automation, shell sleep or controller polling. The Exchange normally remains
active through external thinking. If the platform forces its turn to end, send
one `WAIT_PRO_THINKING`; the controller may reactivate only the same Exchange
for read-only recovery of the same response. Never resubmit the prompt.

## External Transport Boundaries

The Gemini Exchange uses only the registered Antigravity session and approved
per-round local-source manifest and may write only
`11_GEMINI_DIVERGENT_RAW.md`.

Each Pro Exchange verifies its registered URL, visible `Pro` label and role ACK.
It expands the neutral handoff template by replacing only `<commit>` and
`<question-path>`, submits that complete prompt, and may write only its role's
registered raw file. Never click `立即回答`, `停止回答`, `重新生成`, `重试`,
continuation, or an equivalent response-control. A browser timeout authorizes
only a bounded read of the same page; only a naturally completed response is
admissible raw.

Exchanges never edit `05_REVIEW_STATE.json`, root memory, synthesis,
disposition, code or Git. The controller records receipts and owns all
interpretation and scientific decisions.

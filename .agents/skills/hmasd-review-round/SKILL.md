---
name: hmasd-review-round
description: "Create or resume the full tracked HMASD five-stage external-review round governed by 05_REVIEW_STATE.json: blind Gemini and open GPT-5.6 Pro reviews, controller synthesis, convergent GPT-5.6 Pro review, and controller disposition. Use role-specific Terra Medium transport subagents. Do not use for prompts, manual handoff, one returned review, literature discussion, brainstorming, single-reviewer consultation, routine result interpretation, or a contract-determined disposition."
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

- `NOT_STARTED`: no transport worker was created;
- `DISPATCHED`: the registered role subagent was created for the exact route;
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

A new transport uses `source=subagent`, the canonical child task name as
`session`, the registered external conversation as `conversation`, and
`reference=agent:<canonical-task>:spawn` or
`reference=agent:<canonical-task>:complete`. The two references must differ.
The state script derives the one legal task name from round ID and role and
requires the registry's `gpt-5.6-terra`/`medium` worker profile.
Manual receipts remain user-message receipts. Existing tracked receipts from a
prior transport remain valid history and are never rewritten.

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

## Role-Specific Transport Subagents

Create one depth-one child for each external role that is actually reached:

```text
task_name: review_<normalized-round-id>_<gemini|open|convergent> (exact)
fork_turns: none
model: gpt-5.6-terra
reasoning_effort: medium
```

Open and convergent Pro must use different children. A child handles only its
registered external conversation and raw path. Reuse the same child with
`collaboration.followup_task` only after an actionable blocker is resolved;
never create a duplicate or change its model.

The controller prompt supplies the exact route, round paths, immutable commit,
registered external identity, and allowed raw path.
The child reads the sources itself, performs transport, waits for natural
completion, archives and byte-verifies the raw, and returns exactly one terminal
final answer. The subagent runtime delivers it to `/root`:

```text
REVIEW_TRANSPORT
terminal=<COMPLETE|BLOCKED>
stage=<stage>
route=<exact route>
raw=<registered raw path or none>
receipt=<completion receipt or none>
reason=<actionable code or none>
```

There is no `WAIT_PRO_THINKING` relay. While Pro is thinking, the child keeps
its turn active and performs bounded read-only browser recovery on the same
page. It must not use shell sleep. The controller remains idle after dispatch:
do not call `wait_agent`, poll the child or page, read another task, create an
automation/heartbeat, or spawn a replacement.

Do not use `create_thread`, `send_message_to_thread`, `list_threads`, or
`read_thread` for this workflow. Do not also call
`collaboration.send_message`; the automatic final delivery is the sole relay.
It contains no model or reasoning fields; the worker model is fixed only by
`spawn_agent`.

## Transport Boundaries

Gemini uses only the registered Antigravity session and approved per-round
local-source manifest. The child may write only `11_GEMINI_DIVERGENT_RAW.md`.

A Pro child verifies the registered URL, visible `Pro` label, and role ACK. It
submits the complete neutral handoff template with only `<commit>` and
`<question-path>` replaced. Internal route data, raw paths, controller identity,
or worker instructions never enter ChatGPT. It may write only its registered
raw file.

Never click `立即回答`, `停止回答`, `重新生成`, `重试`, continuation, or an
equivalent response-control. A browser timeout ends only that read attempt; it
does not end the child or authorize resubmission. Only a naturally completed
response is admissible raw.

Children never edit `05_REVIEW_STATE.json`, root memory, synthesis,
disposition, code, or Git. The controller records the returned receipt and owns
all interpretation and scientific decisions.

---
name: hmasd-review-round
description: "Create or resume the full tracked HMASD five-stage external-review round governed by 05_REVIEW_STATE.json: blind Gemini and open GPT-5.6 Pro reviews, controller synthesis, convergent GPT-5.6 Pro review, and controller disposition. Do not use for prompts, manual handoff, one returned review, literature discussion, brainstorming, single-reviewer consultation, routine result interpretation, or a contract-determined disposition."
---

# HMASD Review Round

Read the round's `00_REVIEW_BRIEF.md`, `01_SHARED_SOURCE_MANIFEST.md`, and
`references/review-protocol.md`. Gemini additionally reads
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. Read the neutral
`docs/external-review/GPT5_6_PRO_HANDOFF_TEMPLATE.md` only before a Pro
submission. Read `docs/external-review/REVIEWER_CONVERSATIONS.json` before any
external transport. `docs/external-review/README.md` is a human index, not a
mandatory runtime read. Do not reload workflow documents at every stage.

## Establish and Resume Round State

Initialize the tracked `05_REVIEW_STATE.json` at the question boundary with
`scripts/review_state.ps1 -Mode init`. It is the sole progress authority for the
round. Update it only through that script. Do not commit a stage transition or
state pointer alone. After both divergent raws and controller synthesis are
complete, create one pre-convergent evidence commit/push when Pro needs those
Git-visible inputs. Commit convergent raw, controller disposition and final
state together at the disposition boundary. At activation and before ending the turn, run
`-Mode validate`, `-Mode show`, then `-Mode next`. Resume only the returned
`NEXT:<stage>`; `WAIT`, `BLOCKED`, `SUSPENDED` and `CLOSED` do not authorize a
send. Do not infer progress from directory contents or conversation prose.

Use these transport states precisely:

- `NOT_STARTED`: no successful transport call exists;
- `DISPATCHED`: the guarded send is visible in the destination Exchange task as
  `turn:<uuid>`, or in the Gemini transcript as `transcript:<id>`, but no
  verified terminal response has returned;
- `COMPLETE`: the exact raw is archived and the script accepts a receipt
  containing exactly `source`, `session`, `conversation`, `role`, `model`,
  `route`, `terminal` and `reference`;
- `BLOCKED`: consent, identity, remote evidence, authentication, completeness,
  or transport prevents progress.

A prompt file, intended send, browser page, or nonempty raw file alone does not
prove handoff. A pre-existing raw without a matching Exchange receipt or an
explicitly identified manual source is `BLOCKED_UNVERIFIED_RAW`; preserve it and
record the blocker through the script rather than resubmitting or calling it
complete.

The stage-to-artifact mapping is immutable. `-ArtifactPath` may only repeat the
registered filename. Every external `DISPATCHED` transition requires
`-DispatchReceipt`; `dispatched_at` or a route token cannot be supplied as a
substitute for destination-side evidence.

The receipt syntax is:

```text
source=<exchange|gemini|manual>;session=<id>;conversation=<id>;
role=<registered role>;model=<registered label>;route=<exact route token>;
terminal=<DISPATCHED|COMPLETE>;reference=<turn UUID, transcript id, or user:<thread-id>:<message-ref>>
```

`DISPATCHED` forbids `source=manual` and binds the registered reviewer identity,
exact route and destination-side turn/transcript reference. A non-manual
`COMPLETE` must keep that route and add a second structured receipt with
`terminal=COMPLETE` and a different destination-side reference. Manual completion uses `session=manual`,
`conversation=manual`, `model=manual`, and a `user:` reference.

`COMPLETE` is immutable. Never edit the JSON directly or move a `DISPATCHED`
stage back to `NOT_STARTED`; transition a failed attempt to `BLOCKED` and retain
its route token. Leaving `BLOCKED` requires `-ResolutionReceipt` beginning with
`user:`, `tool:`, `evidence:` or `controller:`.

`round_status` is only `ACTIVE`, `SUSPENDED`, or `CLOSED`. Workflow maintenance
does not change it. An `ACTIVE` round must run `-Mode next` before the final user
response; a `SUSPENDED` round resumes only through `-Mode round -RoundStatus
ACTIVE`; `CLOSED` is immutable. Report a returned blocker and exact missing
authority rather than describing an intended handoff as complete.

## Run the Round

1. Freeze one shared evidence boundary and exact source allowlists.
2. Run Gemini and the open GPT-5.6 Pro as blind, independent divergent
   reviewers with equal standing. They are independent dependencies but external
   submissions are serialized: if one is `BLOCKED`, `-Mode next` may select the
   other; at most one external stage may be `DISPATCHED`.
3. Archive both raw responses before the controller compares their claims with
   repository evidence and writes a synthesis.
4. Give the synthesis and both raw reviews to the convergent GPT-5.6 Pro.
5. Archive its raw response, then let the controller accept, reject, modify, or
   defer each proposal and update the owning project document.

The convergent reviewer must rank and stress-test a portfolio of two to four
live hypotheses or architectures when defensible. It may recommend stopping or
the next serialized evidence source, but must not turn compute serialization
into a unique permitted research direction. Only the controller may adopt its
recommendation. A valid scientific FAIL does not require a successor for its
failed branch, but it retires other branches only when the evidence reaches
them.

## Verify Pro Evidence Boundary

Before either Pro submission, resolve a full 40-character commit and verify
that it is reachable from the remote `aggressive` branch. Verify that the
question contains an explicit divergent or convergent role, an exact
`Repository files to inspect` section, and that every listed path exists in the
same commit. Run `scripts/verify_pro_review_boundary.ps1`; if it fails, return
`BLOCKED` before browser transport and do not ask the reviewer to discover
missing evidence.

## Mandatory Pro Transport

The controller never operates the Pro browser. For each missing raw artifact,
select its exact registered local/external pair and pass the remote evidence
preflight. Invoke `codex_app__list_threads`; require exactly the registered
host/thread and an idle status of `notLoaded`, `completed`, or `idle`. Model and
effort are frozen registry fields because the thread API exposes no authoritative
live settings; never claim they were re-read. Send only the route token and
tracked paths with this exact shape:

```javascript
await tools.codex_app__send_message_to_thread({
  hostId: "<registered host_id>",
  threadId: "<registered thread_id>",
  model: "<registered model_id>",
  thinking: "<registered reasoning_effort>",
  prompt: "<route token and tracked paths only>"
})
```

After delivery, require the same host/thread identity. Confirm the delivered
Exchange request through `codex_app__read_thread` and use its turn UUID for the
`DISPATCHED` receipt. Confirm the completed Exchange turn through another
bounded read and use that turn UUID in the completion receipt. The exchange must verify its local thread, external
conversation, role ACK and visible `Pro` label before browser use, archive the
exact response, then return `COMPLETE` or `BLOCKED` through the same guarded
format resolved against the controller. Never omit `model` or
`thinking`, repair a mismatch, change a model, edit thread state, mix roles,
create a duplicate, or submit roles in parallel. A mismatch is
`BLOCKED_REVIEW_THREAD_IDENTITY`.

The route token is `<round>:<role>:<commit>:<raw-path>`. A token closes only when
`review_state.ps1` accepts its `COMPLETE` transition with the exact raw and
receipt; a nonempty raw alone does not close it. Browser, plugin, authentication,
identity, or completeness failures are
transport blockers, never scientific raw responses.

An identity-confirmed raw response is immutable; archive or interpret it but
never resubmit its prompt. An incomplete or ambiguous raw is `BLOCKED` for exact
manual recovery, not authority to create another reviewer conversation or
silently submit again.

Automatic permission covers Git-visible Pro transport and raw archival only.
Sending private repository content, logs, or local papers to Gemini or another
external service requires `-Mode consent -ConsentState APPROVED` with the exact
manifest path, 40-character Git commit, destination and a
`user:<thread-id>:<message-ref>`
receipt. The script rejects dispatch if that manifest differs from the approved
commit. Workflow automation never implies consent. Reviewer advice does not
authorize code, experiments, promotion, or scientific disposition. If
authentication, model identity, page state, source completeness, or response
completeness is ambiguous, return `BLOCKED` with the exact manual prompt.

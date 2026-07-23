---
name: hmasd-review-round
description: Use when an HMASD external GPT-5.6 Pro decision or focused clarification must be transported through the registered conversation, or when its direct browser transport, heartbeat, raw archive, or recovery state needs handling.
---

# HMASD External Pro Research Round

## Authority

External GPT-5.6 Pro is the scientific decision source. It owns conjecture and
definition correction, derivation, counterexample search, retained lemmas,
portfolio meaning and selection of one scheduled research action. That action
serializes resources; it does not make other defensible explanations illegal.

Project Manager is the semantic author and repair owner of reviewer-visible
briefs, manifests and questions, including concrete scientific gaps that block
code-side work. It does not decide those gaps. External Pro remains the
scientific authority.

Controller owns only mechanical validation, reviewer-visible Git boundaries,
Controller-direct transport, exact raw archival, heartbeat lifecycle,
Controller mechanical intake, routing, resource authorization and user
communication. It transports the exact PM-authored files unchanged and never
rewrites, summarizes, normalizes, ranks or completes them.
Controller never classifies scientific completeness of the Pro response.

Activate this Skill as `$hmasd-review-round` in the active Controller. Browser
work requires `$browser:control-in-app-browser`. Do not create another Codex
task for transport.

Use a full plural review for competing explanations, proposed family
retirement, benchmark-identification disputes, repeated ambiguity or
full-algorithm integration. Use a focused continuation in the same registered
Pro conversation for a local scientific ambiguity or correction. Both use the
same exact evidence and raw-archive discipline.

## Round boundary

```text
docs/external-review/rounds/<round>/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_PM_CODE_SIDE_RECONCILIATION.md
  50_MECHANICAL_INTAKE_RECORD.md
```

Before dispatch, commit and push the brief, manifest and question. Run
`scripts/verify_pro_review_boundary.ps1` with the 40-character pushed SHA and
question path. List the scientific principles and every exact Git-visible
evidence path.

Every newly authored package contains these exact declarations in its brief and
question:

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
```

Reviewer-visible PM artifacts are admissible evidence only with those markers.
Internal manager audits, callbacks, scratch notes and work logs remain forbidden.

The question asks Pro to return:

- plural live conjectures and their scopes;
- derived intervention, natural and held-out consequences;
- concrete counterexamples and retained lemmas;
- the smallest refuted unit in existing evidence;
- one scheduled research action chosen by information gain, cost and
  reversibility;
- evidence semantics to freeze if that action is adopted;
- reactivation conditions for unscheduled ideas;
- a concise Chinese user brief.

Pro must not equate one scheduled action with one legal successor or write an
implementation plan. If implementation is selected, it defines the scientific
object and estimand; the Manager later freezes executable architecture.

## Procedure

1. Assign Project Manager the round path and scientific evidence boundary. It
   authors and, after validation feedback, repairs the complete reviewer-visible
   package under its code-side write lease.
2. Controller mechanically verifies author markers, required fields, source and
   path provenance, forbidden internal references and Git visibility. It then
   commits and pushes the exact PM-authored files unchanged.
3. Read `docs/external-review/REVIEWER_CONVERSATIONS.json` and inspect the
   registered conversation before submission using
   `$browser:control-in-app-browser`.
4. Resume a visible matching freshness fence or submit it exactly once only
   after the conversation proves it absent. Archive a naturally completed raw
   exactly and record no scientific quality classification.
5. Controller may write only `50_MECHANICAL_INTAKE_RECORD.md`: hashes, source,
   transport status, authority markers and whether the process is eligible for
   routing. It contains no scientific or engineering interpretation.
6. Delete the Controller-owned heartbeat and confirm it is absent.
7. Return the exact raw to Project Manager. PM authors
   `30_PM_CODE_SIDE_RECONCILIATION.md` and any durable code-side implementation
   artifacts. Scientific deltas must be exact Pro-authored content, not a PM or
   Controller convergence pass.
8. If Pro selected implementation, send its exact direction and estimand to a
   separately authorized Project Manager task. Review and intake alone
   authorize neither implementation nor compute.

At every validation failure the returned evidence carries
`repair_owner=project_manager`. Controller forwards the failure evidence and
does not alter package semantics.

External Pro raw is the only scientific disposition authority. Project Manager
owns code-side reconciliation. Controller has no reconciliation or disposition
authorship, even when an older round used those filenames.

## Controller-direct transport

Always inspect the registered conversation before submission.

Search visible user turns for this exact fence identity:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=<round>
stage_commit=<stage_commit>
question=<question>
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

- If a matching fence is visible, adopt its browser state and continue.
  An accepted matching fence is never resubmitted.
- If a stable response follows that fence, archive it without submission.
- If the readable conversation proves the matching fence absent, submit the
  fence once and require the visible user turn to match all identity fields.
- If presence or absence cannot be established, recover the same conversation;
  uncertainty never authorizes submission.

Keep one registered page and at most one Controller-owned five-minute heartbeat
while pending. A heartbeat performs one bounded inspection and never submits.
Do not create a Monitor or another transport task.

### Conversation discovery ladder

A redirect to the ChatGPT home page is not a blocker. Keep the valid browser
binding, discard only a stale tab binding, and perform this conversation
discovery ladder before reporting transport unavailable:

1. Inspect controlled and user-visible tabs for a visible conversation link
   whose `href` contains the registered `conversation_id`. Reuse it when found.
2. Open the registered URL once. If it redirects to the signed-in home page,
   inspect visible conversation links and the sidebar/history for that same
   `conversation_id`.
3. Use the signed-in conversation search with unique current-round evidence:
   the exact `round`, `stage_commit`, and question basename. A candidate is
   accepted only when the candidate URL contains the registered
   `conversation_id` and its visible user turn matches the full fence identity.
4. If the page is a real authentication or application-approval boundary,
   request that user action. A generic home page is not authentication proof.

Never select a conversation from title similarity, page-tail text or an older
round response. Reacquiring or opening a tab does not invalidate the existing
browser binding and does not authorize a new fence.

### Response completion detection

Locate the exact user message containing the matching fence, then inspect the
assistant message after that fence using message-role containers such as
`data-message-author-role="assistant"`. Do not use the page tail, a single
spinner, elapsed time or a global status label as the response identity.

Treat the response as naturally complete only when all transport evidence
agrees:

Require two stable snapshots from distinct inspections separated by at least three seconds.

- the same assistant message identity and complete visible text appear in two
  stable snapshots from distinct inspections;
- the second snapshot adds no text and exposes no active `Stop generating` or
  cancel-generation control for that turn;
- no response error, `Retry`, or continue-generation control exists for the
  current turn; partial assistant text plus such a control is not complete; and
- the response belongs to the exact matching fence rather than an earlier
  assistant turn.

A visible `Thinking` label alone does not prove generation is active. If a
stable assistant response exists and generation controls are inactive, a stale
or collapsed thinking label cannot keep the handoff pending. Conversely,
changing response text or an active stop control proves generation is still in
progress.

When the UI is ambiguous, inspect button labels, disabled state, message roles
and one more stable snapshot before deciding. If an explicit response error has
no completed assistant message, a same-turn `Retry` may be used once as a
recorded recovery after confirming it cannot submit another freshness fence.
Do not assess whether requested scientific sections are present; that belongs
to Project Manager after exact archival.

## Controller mechanical intake

When the response stops naturally and is stable, copy the complete Pro text to
the assigned raw path, reread it and require exact text equality. Natural
completion and equality are transport facts. Controller records no scientific
quality label, interpretation or proposed repair.

The mandatory terminal and next-boundary order is:

```text
exact raw -> Controller mechanical intake -> heartbeat deletion -> Project Manager reconciliation -> PM-authored focused package or implementation artifact
```

Project Manager decides whether the response resolves its code-side gap and
whether a focused question is required. Verify raw hashes, source commit, paths
and exact delivery. Preserve the Pro decision without a second scientific
convergence step. Integrate only exact Pro-authored scientific deltas and exact
PM-authored code-side files.

There is no Controller semantic relay. A read-only scout may perform a bounded
mechanical comparison but owns no scientific, engineering or adoption authority.

When a later resource action is authorized, dispatch the registered Project
Manager with the archived Pro direction, estimand, resource boundary, working
scope and completion contract. The
Project Manager—not the Controller—freezes the executable algorithm.

## Recovery before blocked

A browser, runtime, navigation, approval, archive or heartbeat failure keeps the
same handoff active. Inspect the direct error and current conversation, then try
safe materially distinct recoveries such as reconnecting the registered
runtime, reusing an existing registered tab, reopening the registered URL or
rechecking visible message-role turns. Record each attempt:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed operation>
action=<diagnostic or recovery action>
outcome=<observed result>
```

Never repeat an identical failed action without changed state. Before any
submission retry, prove the matching fence absent. `waitingOnApproval`, a
timeout, a lost locator or two failed initializations alone is not terminal
while another safe recovery remains.

Report `REVIEW_TRANSPORT_BLOCKED` only when all safe in-scope recovery is
exhausted. It includes the direct remaining cause, attempt summary,
duplicate-submission risk, exact resume condition and
`recovery_exhausted=true`. Ask for user action only when the application exposes
a required approval or authentication boundary.

## Retirement and single-writer rule

The active Controller is the sole writer of the assigned raw and sole owner of
its review heartbeat. A late output from a retired role has no authority to
write or replace raw, complete the handoff, mutate control state, authorize
science or compute, or launch a successor. At terminal success or terminal
block, delete the Controller-owned heartbeat and confirm it is absent.

---
name: hmasd-review-round
description: Use for every HMASD external GPT-5.6 Pro browser review, including registered-session discovery, ChatGPT home-page redirects, exact freshness-fence submission, stable response-completion detection, evidence-access recovery, heartbeat cleanup, and exact raw archival.
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

Controller owns only mechanical identity/provenance checks, reviewer-visible Git boundaries,
Controller-direct transport, exact raw archival, heartbeat lifecycle,
Controller mechanical intake, routing, resource authorization and user
communication. It transports the exact PM-accepted files unchanged and never
rewrites, summarizes, normalizes, ranks or completes them.
Controller never classifies scientific completeness of the Pro response.

```text
pm_acceptance_authority=exclusive
controller_validation_authority=none
repair_owner=project_manager
```

Project Manager self-validates and accepts every code-side/reviewer-visible
package. Controller performs no technical or algorithmic validation; its checks
are limited to exact artifact identity, source/hash/path and Git transport.

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
   authors, self-validates, independently reviews, repairs and accepts the
   complete reviewer-visible package under its code-side write lease.
2. Controller compares the returned route, source, exact paths and hashes with
   the delivered files and Git visibility. It then commits and pushes the exact
   PM-accepted files unchanged. This is non-discretionary identity/provenance
   work, not package validation.
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

PM validation and repair remain inside the Project Manager task tree with
`repair_owner=project_manager`. A Controller-observed hash/path/source mismatch
is only a delivery-integrity mismatch and does not authorize Controller review
or semantic repair.

External Pro raw is the only scientific disposition authority. Project Manager
owns code-side reconciliation. Controller has no reconciliation or disposition
authorship, even when an older round used those filenames.

## Controller-direct transport

### Deterministic browser state machine

Execute these states in order. Do not skip a state because an older response is
visible or the page title looks familiar.

| State | Required observation | Mechanical action | Exit condition |
|---|---|---|---|
| `RESOLVE_REGISTERED_CONVERSATION` | Registry supplies one `conversation_id` and URL | Reuse a controlled matching tab; otherwise open the URL once. On a signed-in home-page redirect, find and open the visible link with that exact ID. If the matching page has a composer but no message-role containers, wait once and reload once. | URL contains the registered ID and visible conversation messages are readable. |
| `VERIFY_FRESHNESS_FENCE` | Visible user turns can be inspected by message role | Match `repository`, `branch`, `round`, `stage_commit` and `question`. Resume an exact match. Submit once only after readable history proves it absent. | One visible exact fence exists. |
| `WAIT_FOR_RESPONSE` | Latest assistant turn after the fence or latest transport-repair message is identifiable | While text changes or `Stop generating`/`Stop answering` is active, remain pending. Otherwise compare two snapshots at least three seconds apart. Ignore a stale `Thinking` label by itself. | Same message ID/text, no active stop, retry, error or continue control. |
| `RECOVER_EVIDENCE_ACCESS` | Assistant explicitly reports missing question-listed evidence or unavailable repository access | Treat it as a transport diagnostic. Build the exact `stage_commit` allow-list archive, attach it in the same session and send one mechanical continuation. Never send a second fence. | A later assistant candidate is attributable to the repair message. |
| `ARCHIVE_AND_RETURN` | Candidate passes stable completion checks | Write exact visible text to raw, reread/hash for equality, write mechanical intake, confirm heartbeat absence and route raw to PM. | Project Manager receives exact raw; Controller performs no semantic or technical validation. |

`Response actions` such as `Copy response` plus stable text are supporting
completion evidence, not a substitute for message identity and inactive
generation controls. A CAPTCHA, login or application-approval boundary requires
user action; a generic ChatGPT home page does not.

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
   If the matching URL has a composer but no visible message-role containers
   after one bounded wait, reload the same tab once and take a fresh snapshot.
   An empty content pane is a recoverable render state, not proof that the
   conversation or assignment is absent.
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
  `Stop answering` or cancel-generation control for that turn;
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

### Evidence-access transport recovery

An assistant message that explicitly says it could not read one or more
question-listed evidence paths, asks for those files, or reports unavailable
repository/connector access is an operational transport diagnostic. This is an
objective provenance failure, not a Controller judgment about scientific
completeness. Do not archive that diagnostic as scientific raw and do not send
it to Project Manager as the round answer.

Recover in the same registered conversation and under the same accepted fence:

1. Parse the exact evidence paths listed by the question. Ignore any additional
   path invented or requested by the diagnostic response.
2. Verify every listed path exists at the pushed `stage_commit`, then
   materialize them from `stage_commit`, not from the current working tree.
   Use one archive with repository-relative paths preserved when duplicate
   basenames exist. Verify the archive member set equals the question allow-list
   exactly and contains no extra file. Use the deterministic builder rather
   than assembling paths manually:

   ```powershell
   & .agents/skills/hmasd-review-round/scripts/build_review_evidence_archive.ps1 `
     -Commit <stage_commit> `
     -QuestionPath <repository-relative-question-path> `
     -OutputPath <new-absolute-zip-path>
   ```

   Continue only when it returns `REVIEW_EVIDENCE_ARCHIVE_READY` with the
   expected commit and file count.
3. Attach that exact archive to the same conversation and send one mechanical
   continuation stating its commit, allow-list identity and that the prior
   response is a transport diagnostic. Do not submit another freshness fence.
4. The candidate scientific raw is the stable assistant response after the
   latest Controller transport-repair message, still anchored to the original
   matching fence. Apply the same two-snapshot and generation-control checks to
   that candidate.
5. If archive ingestion explicitly fails, try one materially distinct
   path-preserving delivery of only the same allow-listed files. Never add
   current-worktree content, an internal manager artifact, an unlisted Skill or
   a Controller-authored scientific explanation.

Record the diagnostic and recovery as transport facts in the mechanical intake.
They never change question semantics, scientific authority or the single-fence
rule.

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

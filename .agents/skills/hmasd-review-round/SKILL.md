---
name: hmasd-review-round
description: Use in the dedicated HMASD External Review Operator task for GPT-5.6 Pro browser transport, natural-completion monitoring, exact raw archival, and probe-confirmed completion notification to Project Manager.
---

# HMASD External Pro Review Transport

## Contract boundary

Role contracts are normative. Read the root `AGENTS.md` and these relevant role
documents before operating:

- `.agents/roles/EXTERNAL_REVIEW_OPERATOR.md`
- `.agents/roles/EXTERNAL_PRO.md`

This Skill grants no authority. It is an operational transport procedure only.
It must not decide the need for review or scientific completeness, how to use a
response, or what work follows it.

Project Manager authors and pushes its review files, uses
`$hmasd-cross-task-routing` to confirm the live External Review Operator session,
then sends one exact assignment with model and thinking omitted. Activate `$hmasd-review-round`
only in that operator task and use `$browser:control-in-app-browser` for
submission and archival. After one exact fence is visibly submitted, assign
the registered nonpersistent `hmasd-pro-response-monitor` to observe the
operator-brokered metadata sentinel for that turn. The child never opens the
browser. Do not create another transport task, relay, ad hoc monitor or Project-Manager
polling loop.

## Required inputs

Require the assigned review mode, round path, pushed 40-character
`stage_commit`, exact question path, exact raw path, mechanical-intake path,
registered reviewer conversation, and declared input paths. The question must
declare exactly one of:

```text
DESIGN_ASSERTION_AUDIT
IMPLEMENTATION_ALIGNMENT_CLARIFICATION
CODE_SCIENCE_ALIGNMENT_AUDIT
FORMAL_RESULT_SCIENTIFIC_DISPOSITION
```

Before browser submission:

1. Confirm the supplied paths and Git source identity match the
   assignment and are Git-visible at `stage_commit`.
2. Run
   `.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`
   with that commit and question path.
3. Read `docs/external-review/REVIEWER_CONVERSATIONS.json` and select only its
   registered conversation.

An identity mismatch stops transport for correction; it does not authorize
editing, paraphrasing, or validating the package.


## Dedicated-operator transport

### Deterministic browser state machine

Execute these states in order. Do not skip a state because an older response is
visible or the page title looks familiar.

| State | Required observation | Mechanical action | Exit condition |
|---|---|---|---|
| `RESOLVE_REGISTERED_CONVERSATION` | Registry supplies one `conversation_id` and URL | Reuse a controlled matching tab; otherwise open the URL once. On a signed-in home-page redirect, find and open the visible link with that exact ID. If the matching page has a composer but no message-role containers, wait once and reload once. | URL contains the registered ID and visible conversation messages are readable. |
| `VERIFY_FRESHNESS_FENCE` | Visible user turns can be inspected by message role | Match `repository`, `branch`, `round`, `stage_commit` and `question`. Resume an exact match. Submit once only after readable history proves it absent. | One visible exact fence exists. |
| `WAIT_FOR_RESPONSE` | Exact fence and visible user-turn identity are known | External Review Operator initializes one metadata-only JSONL sentinel, spawns exactly one `hmasd-pro-response-monitor` with its path and exact identities, then records bounded browser observations at ordinary task wakeups. The child never opens the browser or reads response text. | Sentinel-backed monitor returns one `COMPLETE` or `ERROR` terminal payload. |
| `RECOVER_EVIDENCE_ACCESS` | Assistant explicitly reports missing question-listed evidence or unavailable repository access | Treat it as a transport diagnostic. Build the exact `stage_commit` allow-list archive, attach it in the same session and send one mechanical continuation. Never send a second fence. | A later assistant candidate is attributable to the repair message. |
| `ARCHIVE_AND_INTAKE` | Candidate passes stable completion checks | After monitor `COMPLETE`, External Review Operator confirms stable text, writes exact visible text to raw, rereads for exact equality, writes provenance intake, confirms monitor absence, uses `$hmasd-cross-task-routing` to confirm the live Project Manager session, and sends one terminal notification with model and thinking omitted. | Project Manager receives the returned file paths and routes the exact raw; the operator stops. |

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

Keep one registered page, one append-only sentinel and exactly one registered
Pro-response monitor while pending. Do not create a heartbeat, automation
poller, second monitor or transport task. External Review Operator owns all
browser access because a native child does not inherit the in-app-browser
binding. At ordinary task wakeups, the operator takes one bounded read-only page
snapshot and calls `scripts/hmasd_pro_response_sentinel.py record`; it does not
run a timer loop or emit pending progress messages. The response text remains
in the browser and is represented in the sentinel only by a content
fingerprint, assistant-message identity and control state.

The monitor runs only bounded `watch` calls against that sentinel. Pending
produces no terminal payload. Two matching inactive operator observations at least
three seconds apart cause the sentinel tool to emit `COMPLETE`; a browser,
identity or response-control error emits `ERROR`. On `COMPLETE`, the operator
already owns the browser and performs exact archival snapshots. On `ERROR`, the operator handles
transport recovery without allowing the monitor to browse, submit or retry.
The JSONL ledger is append-only rather than atomically replaced, avoiding the
Windows file-replacement race previously seen in long runs. Its content
fingerprint is a local stability discriminator, not a workflow artifact hash,
handoff identity or scientific evidence.

Never activate `Answer now`; the monitor is bound by the same prohibition.

`Answer now` is not a completion or recovery control. Never click it, invoke it
through keyboard or script, or use a localized equivalent to satisfy a timeout.
It asks Pro to stop extended reasoning and answer from the partial state.
Because the UI may offer it throughout normal reasoning, its presence or absence is neutral:
neither makes a response pending nor proves completion.
Only Pro's natural completion is admissible.

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
- `Answer now`, including a localized equivalent, is never activated; its
  presence or absence is ignored rather than used as completion evidence;
- no response error, `Retry`, or continue-generation control exists for the
  current turn; partial assistant text plus such a control is not complete; and
- the response belongs to the exact matching fence rather than an earlier
  assistant turn.

A visible `Thinking` label alone does not prove generation is active. If a
stable assistant response exists and generation controls are inactive, a stale
or collapsed thinking label cannot keep the round pending. Conversely,
changing response text or an active stop control proves generation is still in
progress.

Elapsed time, a monitor deadline, a long thinking phase or partial readable
text never authorizes `Answer now`. Continue waiting for natural completion or,
after safe recovery is exhausted, report a transport blocker without forcing a
shortened answer. Do not keep a naturally completed response pending merely
because `Answer now` remains visible.

When the UI is ambiguous, inspect button labels, disabled state, message roles
and one more stable snapshot before deciding. If an explicit response error has
no completed assistant message, a same-turn `Retry` may be used once as a
recorded recovery after confirming it cannot submit another freshness fence.
Do not assess whether requested scientific sections are present; that belongs
to Project Manager after exact raw delivery.

### Evidence-access transport recovery

An assistant message that explicitly says it could not read one or more
question-listed evidence paths, asks for those files, or reports unavailable
repository/connector access is an operational transport diagnostic. This is an
objective provenance failure, not a scientific judgment about response
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
4. The candidate raw is the stable assistant response after the
   latest External Review Operator transport-repair message, still anchored to the original
   matching fence. Apply the same two-snapshot and generation-control checks to
   that candidate.
5. If archive ingestion explicitly fails, try one materially distinct
   path-preserving delivery of only the same allow-listed files. Never add
   current-worktree content, an internal scratch artifact, an unlisted Skill or
   a newly authored scientific explanation.

Record the diagnostic and recovery as transport facts in the mechanical intake.
They never change the question contents or the single-fence state.

## Exact archival, cleanup, and intake

After stable completion:

1. Copy the complete visible response text to the assigned raw path without
   rewriting, normalization, filtering, or summary.
2. Reread it and require exact text equality; record its source commit, paths,
   completion evidence, and any transport recovery in the mechanical
   intake. Record no scientific quality classification.
3. Confirm the registered response monitor is terminal and no second monitor or
   heartbeat exists.
4. Use `$hmasd-cross-task-routing` to confirm the live Project Manager session,
   then send exactly one completion notification with model and thinking
   omitted. Route ambiguity or unavailable identity fails closed.
5. Keep transport facts separate from scientific content. External Pro owns the
   in-boundary scientific disposition; Project Manager routes the exact raw
   without reinterpretation. The required completion notification is
   mechanical, not a semantic relay.

Do not compute or require input-file or raw-response hashes. The pushed Git
commit identifies reviewer inputs; exact reread equality plus the later Git
commit identifies archived raw.

The required order is:

```text
monitor terminal -> exact raw -> provenance intake -> monitor absence -> probe-confirmed Project-Manager completion notification -> Project-Manager raw routing
```

## Recovery and retirement

A browser, runtime, navigation, archive, approval, or response-monitor failure keeps
the same round active while a safe in-scope recovery
remains. Inspect the direct error and current state, then try materially distinct
recoveries such as reconnecting the registered runtime, reusing its tab,
reopening its URL, or rechecking message roles. Never repeat an identical
failed action without changed state. Record:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed operation>
action=<diagnostic or recovery action>
outcome=<observed result>
```

Before any submission retry, prove the matching fence absent. Report
`REVIEW_TRANSPORT_BLOCKED` only after all safe in-scope recovery is exhausted;
include the direct cause, attempt summary, duplicate-submission risk, exact
resume condition, and `recovery_exhausted=true`.

At terminal success or terminal block, confirm the response monitor is no
longer live, use `$hmasd-cross-task-routing` to confirm the live Project Manager
task, and send exactly one terminal notification with model and thinking omitted. A stale response from
another round has no authority and never replaces the exact current-round raw
or launches a successor.

---
name: hmasd-review-round
description: Use for direct Project Manager transport to HMASD external GPT-5.6 Pro, including registered-conversation recovery, freshness-fence handling, stable completion detection, evidence-access recovery, heartbeat cleanup, and exact raw archival.
---

# HMASD External Pro Review Transport

## Contract boundary

Role contracts are normative. Read the root `AGENTS.md` and these relevant role
documents before operating:

- `.agents/roles/PROJECT_MANAGER.md`
- `.agents/roles/EXTERNAL_PRO.md`

This Skill grants no authority. It is an operational transport procedure only.
It must not decide the need for review or scientific completeness, how to use a
response, or what work follows it.

Activate `$hmasd-review-round` in the active Project Manager. Browser work uses
the `claude-in-chrome` skill and its `mcp__claude-in-chrome__*` tools; load that
skill before the first browser call.

**Transport belongs to `hmasd-review-exchanger`, not to the Project Manager.**
The Project Manager authors the question, freezes and pushes the boundary, and
owns registration; the exchanger drives the browser and returns transport facts
only.

The one exception is bootstrap. When the branch has no registered conversation,
the Project Manager opens it, submits the first fence, records the exact id and
url, and hands the round to the exchanger from that point — the exchanger never
registers a conversation itself. Every later round on a registered branch goes
to the exchanger whole.

Create no other relay, dispatcher, or Monitor.

### Browser tool mapping

| Transport operation | Tool |
|---|---|
| enumerate existing tabs before opening anything | `tabs_context_mcp` |
| open the registered conversation | `tabs_create_mcp`, then `navigate` |
| snapshot message-role containers and generation controls | `read_page`, `get_page_text` |
| locate a specific control or conversation link | `find` |
| compose the fence or a continuation | `form_input` |
| submit, scroll, or operate a control | `computer` |
| attach the evidence archive during transport recovery | `file_upload` |

Never reuse a tab id from an earlier session; call `tabs_context_mcp` first and
re-resolve. Do not trigger a JavaScript dialog — a modal blocks every subsequent
browser call and requires the user to clear it by hand.

## Required inputs

Require the assigned round path, pushed 40-character `stage_commit`, exact
question path, exact raw path, mechanical-intake path, registered reviewer
conversation, and declared input paths. Before browser submission:

1. Confirm the supplied paths and Git source identity match the
   assignment and are Git-visible at `stage_commit`.
2. Run
   `.claude/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`
   with that commit, question path, and `-Branch` set to the registered
   reviewer's branch. `-Branch` is mandatory and has no default — it proves the
   commit is actually reachable on the branch this conversation serves.
3. Read `docs/external-review/REVIEWER_CONVERSATIONS.json` and select only its
   registered conversation. A reviewer whose `registration_status` is not
   `registered`, or whose `conversation_id` or `url` is null, blocks transport:
   report it and stop. Never fall back to a `retired_registrations` entry, and
   never register a conversation yourself.

An identity mismatch stops transport for correction; it does not authorize
editing, paraphrasing, or validating the package.


## Project-Manager-direct transport

### Deterministic browser state machine

Execute these states in order. Do not skip a state because an older response is
visible or the page title looks familiar.

| State | Required observation | Mechanical action | Exit condition |
|---|---|---|---|
| `RESOLVE_REGISTERED_CONVERSATION` | Registry supplies one `conversation_id` and URL | Reuse a controlled matching tab; otherwise open the URL once. On a signed-in home-page redirect, find and open the visible link with that exact ID. If the matching page has a composer but no message-role containers, wait once and reload once. | URL contains the registered ID and visible conversation messages are readable. |
| `VERIFY_FRESHNESS_FENCE` | Visible user turns can be inspected by message role | Match `repository`, `branch`, `round`, `stage_commit` and `question`. Resume an exact match. Submit once only after readable history proves it absent. | One visible exact fence exists. |
| `WAIT_FOR_RESPONSE` | Latest assistant turn after the fence or latest transport-repair message is identifiable | While text changes or `Stop generating`/`Stop answering` is active, remain pending. Otherwise compare two snapshots at least three seconds apart. Ignore a stale `Thinking` label by itself. | Same message ID/text, no active stop, retry, error or continue control. |
| `RECOVER_EVIDENCE_ACCESS` | Assistant explicitly reports missing question-listed evidence or unavailable repository access | Treat it as a transport diagnostic. Build the exact `stage_commit` allow-list archive, attach it in the same session and send one mechanical continuation. Never send a second fence. | A later assistant candidate is attributable to the repair message. |
| `ARCHIVE_AND_INTAKE` | Candidate passes stable completion checks | Write exact visible text to raw, reread for exact equality, write provenance intake, and confirm heartbeat absence. | Project Manager holds exact raw and proceeds to its separate scientific reconciliation. |

`Response actions` such as `Copy response` plus stable text are supporting
completion evidence, not a substitute for message identity and inactive
generation controls. A CAPTCHA, login or application-approval boundary requires
user action; a generic ChatGPT home page does not.

Always inspect the registered conversation before submission.

Search visible user turns for this exact fence identity:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=<branch>
round=<round>
stage_commit=<stage_commit>
question=<question>
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

`branch` is the branch under review, taken from the registered reviewer's
`branch` field. Each branch has its own dedicated conversation, so a fence whose
branch does not match the registry is a registration error, not a fence to
adopt. Never hard-code a branch name here.

The reviewer reads the repository itself through the web GitHub connector at
`stage_commit`; the question carries exact paths, not file contents. Anything
unpushed is invisible to it — verify the push before submitting.

- If a matching fence is visible, adopt its browser state and continue.
  An accepted matching fence is never resubmitted.
- If a stable response follows that fence, archive it without submission.
- If the readable conversation proves the matching fence absent, submit the
  fence once and require the visible user turn to match all identity fields.
- If presence or absence cannot be established, recover the same conversation;
  uncertainty never authorizes submission.

Keep one registered page and at most one Project-Manager-owned five-minute heartbeat
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
or collapsed thinking label cannot keep the round pending. Conversely,
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
   & .claude/skills/hmasd-review-round/scripts/build_review_evidence_archive.ps1 `
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
   latest Project Manager transport-repair message, still anchored to the original
   matching fence. Apply the same two-snapshot and generation-control checks to
   that candidate.
5. If archive ingestion explicitly fails, try one materially distinct
   path-preserving delivery of only the same allow-listed files. Never add
   current-worktree content, an internal scratch artifact, an unlisted Skill or
   a newly authored scientific explanation.

Record the diagnostic and recovery as transport facts in the mechanical intake.
They never change the question contents or the single-fence state.

## Convergence turns

A round is not always one question and one answer. When the Project Manager
reaches a scientific boundary it cannot cross, it converges with the reviewer:
bounded follow-ups inside the **same accepted fence**, until both sides state
the same thing.

A convergence turn is not a fence. Keep them strictly apart:

| | Freshness fence | Convergence turn |
|---|---|---|
| carries | the round identity block | prose, no identity block |
| how many | exactly one per round, never resubmitted | as many as convergence needs |
| authored by | Project Manager | Project Manager |
| may be sent by transport on its own | no | no |

Every convergence turn is authored by the Project Manager and carried verbatim,
exactly like the question. Transport never composes one, never paraphrases one,
and never sends one it was not given.

Apply the same stable-completion checks to each answer that the first answer
received. Archive the full exchange in order to
`22_PRO_CONVERGENCE.md` — every Project Manager turn and every reviewer turn
after the first archived raw, verbatim, none omitted. The turns that changed the
answer are the evidence; keeping only the last message destroys the reason the
conclusion moved.

Convergence ends when both sides state the same thing. A reviewer that merely
stops objecting has not converged. If it stalls, archive what each side holds
and where it diverged — an unresolved boundary is a real result.

## Exact archival, cleanup, and intake

After stable completion:

1. Copy the complete visible response text to the assigned raw path without
   rewriting, normalization, filtering, or summary.
2. Reread it and require exact text equality; record its source commit, paths,
   completion evidence, and any transport recovery in the mechanical
   intake. Record no scientific quality classification.
3. Delete the Project-Manager-owned heartbeat and confirm it is absent.
4. Keep transport facts separate from the subsequent Project Manager scientific
   reconciliation; no callback or routing step exists.

Do not compute or require input-file or raw-response hashes. The pushed Git
commit identifies reviewer inputs; exact reread equality plus the later Git
commit identifies archived raw.

The required order is:

```text
exact raw -> provenance intake -> heartbeat deletion -> Project Manager reconciliation
```

## Recovery and retirement

A browser, runtime, navigation, archive, approval, or heartbeat failure keeps
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

At terminal success or terminal block, delete the Project-Manager-owned
heartbeat and confirm absence. A stale response from another round has no
authority and never replaces the exact current-round raw or launches a
successor.

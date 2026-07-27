---
name: hmasd-review-round
description: Use for direct Project Manager transport to HMASD external GPT-5.6 Pro, including registered-conversation recovery, freshness-fence handling, stable completion detection, evidence-access recovery, heartbeat cleanup, and exact raw archival.
---

# HMASD External Pro Review Transport

## Is a round warranted, and what are you asking?

This decides whether to open a round at all, and how the question must be
written. Transport mechanics follow below.


**Pro does scientific review only.** It is not asked to know the workflow, and
nothing in this repository binds it: it sees the question you send and the
evidence allow-list inside that question, and nothing else. Its authority is
scientific direction and disposition, scoped to that exact question. It never
sets workflow, chooses successor work, designs or accepts code, authorizes
compute, or becomes a second acceptance owner.

**Getting the question right is entirely your job.** A weak question is not
recoverable by the reviewer.

**Warranted when:** two or more structurally distinct explanations remain live; a
mechanism family is about to be retired permanently; whether the benchmark
identifies the target is disputed; two consecutive local failures produced no
clear correction; a local mechanism is about to enter full algorithm
integration; or the work has visibly converged on one favoured route.

**Not warranted** for lemma extraction, narrow result interpretation, or choosing
the next minimal action. Those converge internally.

**A valid answer contains** at least one substantive contribution: a new
conjecture, a concrete counterexample, a hidden assumption named, a corrected
definition, a retained lemma, or a demonstration that the current benchmark does
not identify the target. Recommending another experiment is not, by itself, a
valid open review.

### The dividing question

Does the answer change **what should be measured or claimed** — external — or
**whether the code does what the plan says** — internal?

Code correctness is internal. **Never send an implementation audit outward.** It
spends the scientific reviewer's attention on work owned here and is slower than
the internal pass. Pro's repository access exists so its scientific judgment is
informed by what the code actually does; it is a context channel, not a request
to audit the implementation.

A question may legitimately reference implementation detail. "Does your estimand
require both branches to consume one shared RNG stream" is scientific even though
the answer determines code, because the *decision* being asked for is scientific.

### Writing the question

1. **Route to code, not to prose.** Give exact paths and function anchors and
   instruct the reviewer to verify against source. A summary carries its author's
   errors into the review; a claim stated in the question has already been checked
   once by someone with an interest in it being true.
2. **Mark provenance.** Repository fact, external evidence and your own inference
   are three different things and must be labelled. An unmarked inference reads as
   an established result and gets inherited as one.
3. **Declare confidence.** Name which paths you verified by reading and which only
   by passing tests, and point the reviewer at the latter first.
4. **State the frozen inputs.** Adopted route, seeds, thresholds, budgets and
   deliberately deleted legacy code are inputs, not review surface. Say so, or the
   reviewer re-litigates settled decisions.
5. **Ask for one decision, not a survey**, and give the required response
   sections.
6. **Treat measured evidence in the question as claims to falsify**, and say so.
7. **Do not defend the framing.** State explicitly that discarding the question's
   structure is a legitimate answer.

Write the question so the framing is attackable as a hypothesis rather than
presented for confirmation. If a round returns only agreement, suspect the
question before the reviewer.

**Declare the read boundary before launching anything speculative alongside a
round.** State which fields may be read from an in-flight run before the ruling
lands — wall clock, conformance, provenance — and which may not. Declaring it in
advance is what makes a NO-LAUNCH ruling cost nothing.

### Rules that survive the round

- **Archive the raw verbatim.** A naturally completed response is valid evidence
  even when its content has gaps. Transmission artifacts such as mangled LaTeX
  are preserved as received and noted, never repaired.
- **Correct the record when the reviewer corrects you.** If the question
  contained an error, append the correction rather than editing the claim away.
- **No threshold change after a result is observed.** A pre-registration repair
  before any run is legitimate; the same edit afterwards is a rescue.
- **Receiving a response changes nothing by itself.** The scientific decision is
  External Pro's; the code-side consequence is yours, recorded in the round's
  reconciliation and, when it changes a contract, in that contract's own commit.


## Contract boundary

Read `AGENTS.md` before operating — it is the complete
Project Manager instructions and is normative over this Skill. In particular its
**External Pro** section decides whether a round is warranted at all; this Skill
only carries one.

This Skill grants no authority. It is an operational transport procedure only.
It must not decide the need for review or scientific completeness, how to use a
response, or what work follows it.

Activate `$hmasd-review-round` in the active Project Manager. Browser work uses
the `claude-in-chrome` skill and its `mcp__claude-in-chrome__*` tools; load that
skill before the first browser call.

**Transport is `project_manager_direct`.** The active Project Manager authors the
question, freezes and pushes the boundary, owns registration, submits the fence,
captures the reply and archives it. There is no transport delegate.

This replaced a delegated exchanger on 2026-07-25. The split that failed was
handing one role both a long mechanical wait and a precise capture: the wait was
abandoned twice mid-round, and one archive lost every markdown marker because the
capture fell back to rendered page text. Waiting and capturing are now separated
by who does them.

**`hmasd-review-monitor` (haiku) does the waiting and nothing else.** Dispatch it
after the fence lands; it polls the conversation and reports when generation has
stopped. It holds no click, type or write tools, so it structurally cannot submit,
capture or curtail — it reports one observation and the Project Manager acts on
it. A wrong report from it is cheap: an early wake costs one page read.

Create no other relay, dispatcher, or Monitor.

### Browser tool mapping

| Transport operation | Tool |
|---|---|
| enumerate existing tabs before opening anything | `tabs_context_mcp` |
| open the registered conversation | `tabs_create_mcp`, then `navigate` |
| snapshot message-role containers and generation controls | `read_page`, `get_page_text` |
| locate a specific control or conversation link | `find` |
| compose the fence or a continuation | clipboard paste via `computer` — **not** `form_input`, which fails on this composer (see below) |
| run an ordered multi-step page sequence | `browser_batch` |
| submit, scroll, or operate a control | `computer` |
| attach the evidence archive during transport recovery | `file_upload` |

Never reuse a tab id from an earlier session; call `tabs_context_mcp` first and
re-resolve. **Re-resolving means reusing the tab already on the registered
conversation, not opening another one.** If `tabs_context_mcp` returns a tab
whose URL contains the registered `conversation_id`, that is your tab — do not
call `tabs_create_mcp` or `navigate` to a fresh one. Opening a new tab per
attempt churns tab ids, discards page state, and makes the send-verification
count below unreliable because the turn history has to be re-read each time.
Create a tab only when no existing tab holds that conversation. Do not trigger a JavaScript dialog — a modal blocks every subsequent
browser call and requires the user to clear it by hand.

#### When the tab is wedged — replace it, never add to it

A tab can stop being usable. The symptom is specific: **every** script-injecting
operation — `screenshot`, `read_page`, `find` — times out, the page never reaches
`document_idle`, and this survives a reload. It is not the same as slow, and it is
not an empty content pane, which the discovery ladder already handles with one
wait and one reload.

This is a real state. On 2026-07-25 a conversation holding two very large reviewer
answers wedged permanently: six reloads of the same tab produced one usable render,
while a newly created tab on the same conversation rendered immediately. The
accumulated renderer state was the problem, not the conversation.

The recovery is **replacement, and it is bounded**:

1. try reload-and-wait twice first — that fixes the ordinary hydration case;
2. **close the wedged tab**, then create one and navigate to the registered URL;
3. **exactly one tab holds the conversation when you are done.** Verify with
   `tabs_context_mcp` and close any duplicate.

Two tabs on one conversation is the state this rule exists to prevent, and it is
just as forbidden when reached by recovery as by carelessness.

A replacement tab **grants nothing**. It does not license a second fence, and it
resets no state you had established: re-verify fence presence on the new tab
before any submission, exactly as on a first visit.

**Why this is written down rather than left to judgement.** Before this paragraph
existed, the prohibition had no escape hatch for a wedged tab, so a transport pass
that genuinely needed one reasoned its way around the rule — arguing the
send-verification rationale did not apply because the send was already
verified — and left two tabs open. The rule was right and unfollowable at the same
time. A prohibition without an affordance gets argued with; give it the affordance
and the argument stops.

### Composing multi-line text — a newline is a send

**In this composer, Enter submits.** The `computer` `type` action delivers every
`\n` in its text as an Enter keypress, so typing a multi-line fence submits it
one fragment at a time. On 2026-07-24 this chopped a single fence into several
truncated `CURRENT_REVIEW_ASSIGNMENT` messages, left the reviewer with no usable
assignment, and cost a round.

`form_input` is listed above but **fails on this composer** — it is a
contenteditable `DIV`, not a form control, and returns
`Element type "DIV" is not a supported form input`.

#### Primary mechanism — paste from a committed artifact

Never compose a multi-line message keystroke by keystroke. Write it to a file in
the round directory first, then paste it in one operation:

1. author the exact message as a round artifact — `10_FENCE.txt` for the fence,
   `11_CONTINUATION_<n>.txt` for a convergence or transport-repair turn;
2. load it onto the clipboard verbatim:

   ```powershell
   $src = Get-Content -Raw -Encoding UTF8 <artifact-path>
   Set-Clipboard -Value $src
   ($src -ceq (Get-Clipboard -Raw))   # must print True before continuing
   ```

3. click the composer and press `ctrl+v` — a paste inserts the whole text at
   once and generates no Enter keypress;
4. screenshot and read the composer back, confirming the whole message is
   present exactly once and not doubled;
5. submit **once**, then confirm it landed by the mechanical test below.

**Deciding whether you sent — do not reason about this, measure it.** Before
pasting, count the user turns in the conversation. After clicking send, wait,
then check two things: the composer is **empty**, and the user-turn count has
gone up by exactly one. Both true means sent. **Composer still holding your text
means it did not send — click send.**

"I am not sure whether it sent" is not a terminal state and never a reason to
stop. On 2026-07-24 a transport pass pasted a convergence turn, could not
convince itself it had sent, never clicked send, and then reported the message
as successfully sent while it sat unsubmitted in the composer. An
over-broad reading of the no-duplicate rule caused it.

The no-duplicate rule scopes to **re-sending**: never send content that already
appears as a user turn. It does not license leaving a first send unmade. If the
composer holds your text and no matching user turn exists, the send has not
happened and finishing it is required, not optional.

**Artifacts are ASCII-only.** Write fence and continuation files in plain ASCII —
use `--` rather than an em dash. The clipboard path silently corrupts non-ASCII
when a reader drops `-Encoding UTF8` (PowerShell 5.1 defaults to ANSI), and the
damage appears as mojibake like `â€"` inside an archive that is supposed to be
byte-exact. Always pass `-Encoding UTF8`, and keep the artifact ASCII so the flag
being dropped cannot corrupt anything.

This is more stable than typing and it makes the sent text an auditable
byte-exact artifact rather than a reconstruction, which is what "submit
verbatim" actually requires. The artifact is committed with the round, so what
was sent is recoverable from Git instead of from a browser transcript.

Note that `Set-Clipboard` overwrites the user's clipboard.

#### Fallback — soft line breaks

If the clipboard is unavailable, `type` one line at a time with **no `\n`
anywhere in the text**, pressing `shift+Return` between lines — a soft line break
that does not submit — then verify and submit as above. Drive the sequence
through `browser_batch` so ordering is deterministic; concurrent single calls can
interleave and scramble the text.

If a submission appears not to have landed, snapshot before retyping. The text is
usually already there and the UI simply has not repainted — retyping on an
unconfirmed snapshot is what produces duplicates. Uncertainty resolves toward not
sending, exactly as it does for a second fence.

## Required inputs

Require the assigned round path, pushed 40-character `stage_commit`, exact
question path, exact raw path, mechanical-intake path, registered reviewer
conversation, and declared input paths.

**Question scope.** The question document carries decisions — claim-defining
questions, any number of them, tree-structured where dependent. It never
assigns verification labor to the reviewer: no fact-inventory confirmation,
no implementation-detail checking, no auditing of what the execution side can
verify itself. The two bounded exceptions are the Stage A design audit and
the Stage B code-science alignment diff defined in `AGENTS.md`.

Before browser submission:

1. Confirm the supplied paths and Git source identity match the
   assignment and are Git-visible at `stage_commit`.
2. Run
   `.claude/skills/hmasd-review-round/scripts/preflight_review_round.ps1`
   with that commit, `-RoundPath`, and `-Branch` set to the registered
   reviewer's branch. `-Branch` is mandatory and has no default — it proves the
   commit is actually reachable on the branch this conversation serves. It must
   print `ROUND_PREFLIGHT_READY`; any other status, or an error from the script
   itself, blocks transport. **A gate that crashed is a gate that failed** —
   round `20260724_g20_credit_rule_zero_fixed_point` was dispatched past a
   crashed boundary check and had to be retired.

   This one script is the whole pre-dispatch contract: commit pushed and
   reachable, question present, `## Evidence to read` allow-list non-empty with
   every path present, standing contracts allow-listed, fence artifact fields
   matching the round, and the recovery archive actually building. It replaces
   the former `verify_pro_review_boundary.ps1`, which accepted any backticked
   path anywhere in the question and so passed questions the archive builder
   would refuse.
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

**Never click `Answer now`, and never operate any other control that curtails
extended thinking.** Waiting is the whole job while a response is pending. On
2026-07-24 a transport pass clicked it at roughly four minutes on a round whose
predecessor had reasoned for eighteen, on a protected-semantics ruling — the
archived answer is usable but its depth is not guaranteed, and that cannot be
undone after the fact. A reviewer taking longer than expected is working, not
stuck. Extend your waiting instead, and if you genuinely believe generation has
hung, report it as a blocker rather than forcing an early answer.

An active `Stop answering` or `Stop generating` control **anywhere for the
current turn** ends the question: generation is in progress and nothing may be
archived, no matter how stable two snapshots look. Extended reasoning emits a
progress trace — `Answer now`, `Clarifying file search`, `Fetched …`, `Formulated
the response` — that sits still for many seconds at a time, so a stability check
alone will happily certify it. On 2026-07-24 an archival pass captured 794 bytes
of exactly that trace as scientific raw and asserted byte equality while the stop
control was visible. Two stable snapshots are necessary, never sufficient.

### How to capture the response — one click, never transcription

Use the page's own **`Copy response`** control. It is in the `Response actions`
group attached to the assistant turn, it copies the full message verbatim
including markdown, and it is the only capture path that cannot introduce a
transcription error. Everything below exists because this was previously left
unspecified and three separate passes improvised three different broken captures.

1. **Mark the clipboard first.** Set it to a known sentinel before clicking, so
   a click that silently does nothing is detectable. A failed click leaves the
   *previous* clipboard content in place, which reads exactly like a successful
   capture of the wrong thing.
2. **Scroll to the true end of the response first.** `Response actions` sits at
   the end of *its own* message, and several assistant turns carry one. `find`
   will happily return the control for whichever turn is rendered, so a control
   located before reaching the bottom may belong to an earlier answer entirely.
   Confirm the last visible text is the end of the answer you are archiving.
3. **Click by coordinate from a screenshot.** A `ref` click has been observed to
   report success while writing nothing to the clipboard — twice, verified
   against a sentinel — because the clipboard write needs a real user gesture on
   a focused document. The capture that did work used a coordinate click.
4. **Verify the clipboard actually changed** from the sentinel, and that its
   length and its first and last lines match what is on screen. If it did not
   change, the click did nothing: re-locate and click again rather than
   proceeding. **Never** substitute a different capture method because the click
   is being awkward — that substitution is how the structure-stripped archive
   below happened.
5. **Expect to click more than once, and read the button, not the tool result.**
   *Hitting the control* and *writing the clipboard* are separate facts. The tool
   reports success for the click either way.

   A screenshot distinguishes them. If the `Copy response` tooltip is showing and
   the button is highlighted, the coordinates are right and the clipboard write is
   what failed — usually because the window lacks OS-level focus. Do not go
   hunting for better coordinates; click the same place again. On 2026-07-25 the
   third click on an already-hovered button succeeded after two silent failures,
   with the sentinel unchanged through both.

   If the icon never flips to its copied state, the write did not happen no matter
   how many times the click reported success.
6. **Write it to the raw path with `.NET WriteAllText`** from the clipboard
   directly. Then do the byte-equality reread.

Three capture methods are **prohibited**, each having produced a corrupt archive
that only the byte-equality check caught:

- **retyping the text through a file-write tool** — differed at byte 47;
- **`get_page_text` or `read_page` output as the archive** — that is rendered
  text, not the message source, and loses markdown structure;
- **round-tripping through `ConvertFrom-Json` without explicit UTF-8** — silently
  turned em dashes into `â€"`.

If `Copy response` is genuinely unavailable — the control absent from the
accessibility tree, not merely awkward to reach — that is a transport fault.
Report it; do not fall back to transcription.

Before writing the raw, sanity-check the captured text against the question:

- **it carries this round's own `stage_commit`.** This is the only check that
  catches a capture of the *wrong round*, and nothing else does. On 2026-07-27 a
  `ref`-resolved control returned the previous round's ruling — 18322 characters
  of a real, complete, well-formed scientific answer for a different stage
  commit. It passed every check below. The transcript is virtualized, so the only
  rendered `Copy response` belonged to the first assistant turn while the answer
  being archived was the last;
- it is not a bare progress trace of the labels above;
- it addresses the question's numbered asks rather than announcing intent to;
- its size is plausible for the round — a scoped scientific answer on this line
  runs to kilobytes, and a few hundred bytes is a trace, not an answer.

**Length and non-emptiness prove nothing.** The same session's first bad capture
was the *fence* — 397 bytes, non-empty, already written to the raw path before
the verdict-string assertion caught it and it was deleted rather than amended.
Two different wrong captures in one round, one too small and one too plausible.

A capture failing any of these is a transport fault. Report it and re-enter the
wait; never archive it and never let it reach reconciliation.

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

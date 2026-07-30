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

**Not warranted** for lemma extraction or choosing the next minimal action. Those
converge internally.

*Narrow result interpretation* was on that list until 2026-07-30 and is not
"internal" — reading what a result means is a scientific decision, and the user
ruling of that date leaves the Project Manager none. It does not become an extra
round either: it belongs to touchpoint 3, the result submission. The list is
about what does not justify a *fourth* access, never about what the Project
Manager may settle alone.

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

**At touchpoint 2 the question is a conformance question** — user ruling
2026-07-30. The Project Manager's completed code design is presented, and the
one thing asked is whether it conforms to the scientific decision Pro already
issued. Not which route is better, not which of two the Project Manager favours,
not a case argued for one. Ranking options inside the question is proposing a
route, and this task has no authority to propose one; see `AGENTS.md`, **The
question after a code design is a conformance question**.

Touchpoints 1 and 3 are open scientific questions and the rules below apply to
them in full. At touchpoint 2 rules 1-4 and 6-7 still bind — routing to code,
marking provenance, declaring confidence, stating frozen inputs, treating
measured evidence as falsifiable, and refusing to defend the framing — while
rule 5's "one decision" is fixed in advance: conformance.

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
and **owns the archive decision**.

This replaced a delegated exchanger on 2026-07-25. The split that failed was
handing one role both a long mechanical wait and a precise capture: the wait was
abandoned twice mid-round, and one archive lost every markdown marker because the
capture fell back to rendered page text. Waiting and capturing are now separated
by who does them.

### Capture may be delegated, but only against a digest bond

Amended 2026-07-30. The old rule said flatly that there is no transport delegate,
and its reason was sound when written: a relay could archive rendered DOM, the
wrong round's message, or a failed capture dressed as a success. **All three are
now mechanically excludable**, so the blanket prohibition costs more than it buys.

A bounded child may perform the capture when **all four** hold. Any one missing and
the Project Manager captures it directly.

1. **The Project Manager supplies the expected `message_id`**, taken from the
   conversation API, and the child refuses if the latest assistant message is not
   that one. The child never decides which message is the ruling.
2. **The child returns a page-computed digest**: `crypto.subtle.digest('SHA-256')`
   over the emitted markdown, plus its character length and the message id. It
   returns no bulk text through the tool channel.
3. **The child writes nothing into the round directory.** It hands the bytes over
   the OS clipboard; `archive_pro_response.ps1` is run by the Project Manager.
4. **The Project Manager independently recomputes SHA-256** over the LF-normalized
   archived file and it must equal the child's page-computed digest. **A mismatch
   is a refusal, never a repair** — do not reconcile by editing the file.

**The digest bond binds the Project Manager's own captures too, and that is what
earns the loosening.** Until 2026-07-30 the direct path was verified by a length
match, which a substitution can satisfy; a digest match cannot. Compute it on both
sides of the boundary, every round, delegated or not.

What is still not delegable: choosing which message is the ruling, and deciding
that a failed capture is archivable anyway. Those are judgements, and they stay
with the Project Manager whatever mechanism moved the bytes.

**`hmasd-review-monitor` (haiku) does the waiting and nothing else.** Dispatch it
after the fence lands; it polls the conversation and reports when generation has
stopped. It holds no click, type or write tools, so it structurally cannot submit,
capture or curtail — it reports one observation and the Project Manager acts on
it. A wrong report from it is cheap: an early wake costs one page read.

Create no standing relay, dispatcher or Monitor. A bounded, single-purpose child
dispatched for one capture under the digest bond above is not a relay: it holds no
state between rounds, decides nothing, and its output is verified by a number the
Project Manager computes itself.

### The monitor reports procedure defects, and the Project Manager must carry them

`hmasd-review-monitor` is required to return a `PROCEDURE_DEFECTS` item: every
expectation **its brief stated** that the page did not meet. Two duties follow, and
they are the Project Manager's:

- **State the expectations in the brief.** A brief that names no control, selector
  or marker cannot detect a stale procedure, and the monitor will correctly report
  `none stated`. That reply is a finding about the brief, not about the page.
- **Carry every reported defect into the round's `## Transport faults`**, and in
  the same round either repair this Skill or record why not. The monitor holds no
  write tool and never runs Git; its reply is the only channel, so a defect the
  Project Manager does not transcribe is a defect that did not happen.

`tests/review_round_contract_test.ps1` refuses a round whose `## Transport faults`
section is empty or still `TODO`. That check exists because this section was a TODO
nobody read for thirty rounds: the duty had somewhere to be written and no reason
to be, which is how a prescribed mechanism went on being prescribed after it
stopped working.

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
   Start-Sleep -Milliseconds 300      # let the write land before reading it back
   ($src -ceq (Get-Clipboard -Raw))   # must print True before continuing
   ```

   **The settle is load-bearing.** Without it the read can race the write and
   report `exact=False` on bytes that are perfectly correct — measured on
   2026-07-29, where the same file compared equal on a retry with an unchanged
   artifact and `cr=0` on both sides. A check that fails on timing alone gets
   explained away as flaky, and that is exactly how a real corruption would get
   waved through. If it reports a mismatch, retry once with the settle before
   believing it.

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

### Step zero — take a provisional capture the moment generation stops

**Before locating any control, before any click, dump the answer text with
`javascript_tool` and write it to the round directory as
`22_PROVISIONAL_CAPTURE.txt`.** One call, no clipboard, no focus requirement, no
OS gesture — it works on a hidden tab, and it is the only capture path that
survives the browser dying in the next thirty seconds.

This is a **provisional** artifact and never the archive:

- it is `innerText`, so every markdown marker is gone — the exact loss this
  Skill's history records;
- it does not satisfy "exact raw" and **no reconciliation may be written from
  it**;
- it is deleted once `21_PRO_OPEN_RAW.md` exists, and the intake record notes
  that it was taken.

It exists for one reason. On 2026-07-29 a completed 20745-character ruling was
read, confirmed, and then lost mid-capture when the browser went down — the round
was left with a header, a tail, and nothing in between, and no reconciliation
could be written at all. A provisional dump costs one call and would have left
the full reasoning readable while the byte-exact capture waited for a browser.

Cheap and immediate beats perfect and contingent, **as long as the cheap one
cannot be mistaken for the archive.** Name it `PROVISIONAL`, and let the
byte-exact copy supersede it.

### Check `document.visibilityState` before diagnosing anything

A hidden tab and a wedged tab present identically and have opposite remedies.

```javascript
document.visibilityState   // "visible" or "hidden"
```

`"hidden"` explains, all at once: `screenshot` and `find` timing out at
`document_idle` under render throttling; `javascript_tool` still answering
instantly, which makes the page look half-alive; and `Copy response` silently
doing nothing, because `navigator.clipboard.writeText` refuses on a hidden
document. The remedy is to activate the tab, **not** to replace it — and
replacing it throws away a perfectly good page.

On 2026-07-29 this was misdiagnosed as the accumulated-renderer-state case
documented above, and two capture attempts were spent hunting a coordinate bug
that did not exist. A capturing click listener proved the click was landing on
the right button the whole time:

```javascript
document.addEventListener('click', e => window.__clicks.push(
  {x: e.clientX, y: e.clientY, label: e.target.closest('button')?.getAttribute('aria-label')}), true)
```

Use that listener whenever a click is suspect. It settles *where the click
landed* in one call, which no amount of screenshot-staring does on a page that
will not render.

**And do not pass a `javascript_tool` rect straight to `computer`.** JS rects are
page pixels; `computer` coordinates are screenshot pixels. Convert by
`screenshot_width / window.innerWidth` — on 2026-07-29 that was
`1568 / 1912 = 0.820`, so a rect at `(712, 763)` was a click at `(584, 626)`.

#### `hidden` is the normal state, and most of transport works in it

The registered conversation usually sits in a window whose **foreground tab is
something else**, so `hidden` is the steady state rather than a symptom. Do not
"fix" it before every operation. What matters is knowing which half of the tool
surface it takes away:

| Works on a hidden tab | Fails on a hidden tab |
|---|---|
| `javascript_tool` DOM reads | `screenshot`, `find` (render-throttled, time out) |
| OS-level `computer` `key` — `ctrl+v`, `Return`, `ctrl+a`, `Delete` | `navigator.clipboard.writeText` (refuses) |
| OS-level `computer` `left_click` (lands correctly) | heavy `await fetch` (may time out) |

**So a fence can be sent end to end on a hidden tab**: focus the composer with
`javascript_tool`, paste with OS-level `ctrl+v`, verify by reading the composer
back, submit with `Return`. No foregrounding, no reload, no screenshot. Activate
the tab only when something genuinely needs it — the clipboard write during
capture — and not before.

#### The composer keeps its text after a successful send

Measured twice on this page: after a send that **did** land, the composer still
held the full fence while exactly one user turn carried the commit and generation
was already running.

**So composer emptiness is corroborating evidence, not the send test.** The test
is: *how many user turns carry the fence's `stage_commit`?* Zero means send;
one means done; more than one is the duplicate this Skill exists to prevent. The
earlier heuristic — "composer still holding your text means it did not send" —
points the wrong way in this state and must not be used alone.

Clear the residue with `ctrl+a` then `Delete`. **Never a second `Return`.**
Leaving a valid fence sitting in a composer is a duplicate submission waiting for
a stray keypress.

### Keeping the browser alive is part of transport

Two rounds lost their capture to the browser disappearing. Measured cause:
`exit_type = Normal` in the Edge profile, no sleep in 8 hours on a 38-hour
uptime, and the binary unchanged for days. **It was closed cleanly, not crashed**,
and both deaths landed inside long idle waits rather than during active work.

1. **Check liveness before spending a reload.** `list_connected_browsers` plus a
   process count costs one call. A wedge and a dying browser present identically;
   the previous round burned two reloads on the wrong one.
2. **Never close the last tab.** `tabs_close_mcp` on the only tab closes the
   window and ends the browser — both "The browser is shutting down" messages
   arrived on that call. The Skill's bounded replacement is still
   close-then-create *when another tab exists*; when it does not, **create
   first**.
3. **Pace in minutes, not tens of minutes.** Poll every 2–3 minutes while a
   round is generating. A death is then caught while the answer is still
   recoverable instead of after it is stranded.
4. **You can restart the browser yourself.** It is Edge, not Chrome:
   `${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe`. Launch it and
   the extension reconnects on its own. "The runtime cannot be restarted from
   here" was a false conclusion drawn from searching for `chrome.exe` —
   `tabs_context_mcp` reports `chrome://newtab/` because Chromium-based Edge uses
   that scheme, and Chrome has never been installed on this machine.

#### Verify a search before concluding absence

The `chrome.exe` error above is the general failure worth naming: a search that
finds nothing was treated as proof the thing does not exist. The same mistake
recurred hours later when `"$env:ProgramFiles(x86)\..."` — which PowerShell does
not expand that way; it needs `${env:ProgramFiles(x86)}` — reported Edge missing
too.

**A failed search is not evidence of absence until the search itself is known
good.** Test the method against something you know is there before reporting a
negative.

#### Never use `find` to prove a fence absent

`find` is a **semantic** matcher, not a string search, and its failure mode is
the opposite of the one above: it does not report nothing, it reports a
*plausible* something.

On 2026-07-30, asked for a message containing
`9cb7974563cb7de3371b1d22f3691fc00e02744d`, it returned one "matching element"
whose own quoted text read `round=20260729_d7_s` — the **previous** round's
fence — and justified the match by noting that the phrase "zero-compute
source-assignment correction" appeared nearby. Had that been accepted, the round
would have been treated as already fenced and never sent.

Prove presence or absence from the conversation API, which is exact and
deterministic:

```javascript
const s = await fetch('/api/auth/session').then(r=>r.json());
const conv = await fetch('/backend-api/conversation/'+cid,
  {headers:{Authorization:'Bearer '+s.accessToken}}).then(r=>r.json());
const users = Object.values(conv.mapping)
  .filter(n=>n.message && n.message.author && n.message.author.role==='user');
let hits = 0;
for (const n of users) {
  const t = (n.message.content.parts||[]).map(p=>typeof p==='string'?p:'').join('');
  if (t.indexOf(stageCommit) !== -1) hits++;
}
'user_turns=' + users.length + ' exact_fence_hits=' + hits;
```

`exact_fence_hits=0` authorizes submission; anything else does not. Return the
**counts**, never the message bodies — bulk text through this channel is blocked
by design, and encoding around that block is defeating a safety control rather
than satisfying it.

The same rule governs verifying a *capture*: the fence itself contains the
`stage_commit`, so `clipboard.Contains(stage_commit)` cannot distinguish the
archived ruling from the fence you just sent. Assert a length and a body-only
heading as well.

### The primary capture path — read the conversation API, not the clipboard

**Prefer this over `Copy response`.** From page context, with the user's own
session:

```javascript
const s = await fetch('/api/auth/session').then(r => r.json());
const c = await fetch('/backend-api/conversation/<conversation_id>',
  {headers: {Authorization: 'Bearer ' + s.accessToken}}).then(r => r.json());
const asst = Object.values(c.mapping || {})
  .filter(m => m.message && m.message.author.role === 'assistant'
            && m.message.content && m.message.content.content_type === 'text');
asst.sort((x, y) => (x.message.create_time || 0) - (y.message.create_time || 0));
const txt = asst[asst.length - 1].message.content.parts.join('');
```

Why this is better than the control, not merely easier:

- it returns **the model's own emitted markdown**, not a re-serialization of
  rendered DOM, so there is no rendering layer to lose a marker;
- it needs neither focus nor visibility, so it works on a background tab, which
  is the normal state of this tab;
- it gives an **independent length to check against**. On 2026-07-29 the
  clipboard held 22485 characters with CRLF; normalized to LF the file was 21876,
  exactly the length the page reported for its own source string. That is a
  fidelity proof the clipboard path cannot produce.

Two practical notes:

1. **Returning the text through `javascript_tool` may be blocked** by an output
   filter after a call that touched an auth token. Hand it to the OS clipboard
   instead: stash it on `window`, then copy it with a real user gesture (below)
   and read it with `Get-Clipboard -Raw` — zero context cost, exact bytes.
2. **`navigator.clipboard.writeText` needs a real user gesture.** Supply one
   safely with a full-viewport transparent overlay carrying the copy handler,
   clicked once by `computer`, then removed immediately. The overlay cannot hit
   any page control while it exists, which a bare click on the page cannot
   promise.
3. **A heavy `await fetch` can time out under background throttling.** That is
   throttling, not death — check liveness, then activate the tab and retry. Light
   DOM reads keep working throughout and are the reliable progress signal.

Normalize CRLF to LF before writing, so the archive matches the emitted source
rather than the clipboard's transport encoding.

### Fallback — the `Copy response` control

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
6. **Archive it with the script — do not re-derive this by hand.**

   ```powershell
   & '.claude/skills/hmasd-review-round/scripts/archive_pro_response.ps1' `
       -RoundPath docs/external-review/rounds/<round> `
       -StageCommit <this round's commit> -Sentinel <the sentinel from step 1>
   ```

   It writes with `.NET WriteAllText` and `UTF8Encoding($false)` — never
   `Set-Content`, which writes a BOM by default here — then rereads and checks
   `-ceq`. It refuses, writing nothing, on any of: an empty clipboard, the
   sentinel still present (step 1's failure), a capture missing **this** round's
   `stage_commit` (that is the *previous* round's ruling), a capture too short to
   be a ruling, or one that does not open with a heading. The raw file is
   write-once; `-Force` is only for repairing a known-bad capture.

   Its JSON output is the mechanical intake record: `chars`, `exact_equal`,
   `first_line`, `last_line`.

   Added 2026-07-28 because five consecutive rounds recorded the same sentence —
   *"captured on the second click after the neutral-body focus step, the same
   failure mode and fix as the previous four rounds"*. The fix was rediscovered
   five times because it lived in prose and was re-derived from memory each
   round.

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
reaches a scientific boundary it cannot cross, it puts the question to the
reviewer inside the **same accepted fence** and the reviewer converges it. See
**Convergence ends when Pro issues the convergence decision** below — that is the
operative rule, and agreement by this conversation is not part of it.

A convergence turn is not a fence. Keep them strictly apart:

| | Freshness fence | Convergence turn |
|---|---|---|
| carries | the round identity block | prose, no identity block |
| how many | exactly one per round, never resubmitted | bounded by the conformance check that owns them — never an open-ended series |
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

**Convergence ends when Pro issues the convergence decision.** It checks the
Project Manager's completed code design for conformance and closes the exchange;
the Project Manager implements the result. Disagreement by this conversation is not a reason
to continue — scientific authority is Pro's, so the terminating move is Pro's.

The symmetric rule this paragraph used to carry — *ends when both sides state the
same thing* — gave the exchange no terminator, because either party could
withhold agreement indefinitely. A decision that cannot be **executed** is a
technical blocker for the user, not grounds for another turn.

The access count is fixed: a workflow gets Pro's scientific decision, this
conformance check, and the result submission. Material discovered after a round
closes waits for the next workflow's conformance check.

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

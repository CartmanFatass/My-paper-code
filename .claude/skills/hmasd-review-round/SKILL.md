---
name: hmasd-review-round
description: Use for direct Project Manager transport to HMASD external GPT-5.6 Pro over the Agentify Desktop receipt transport, including operation preparation, single-send submission, receipt verification, evidence-access recovery, and exact raw archival.
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

**Every question carries a `## Variable-k relevance` section** (user ruling
2026-08-01): one or two sentences answering the standing check of
`docs/project/RESEARCH_GOAL.md` — what does this round let us say about
variable k? Preflight refuses an absent, empty or TODO section. If the honest
answer needs more than a sentence, the round is probably off the path — stop
and reconsider before spending the access.

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

**Transport is `project_manager_direct`.** The active Project Manager authors the
question, freezes and pushes the boundary, owns registration, submits the fence,
and **owns the archive decision**. The browser-click transport was retired
2026-08-01; every send now goes through the Agentify wrapper below, and no
browser tool is part of this procedure.

### The digest bond

The receipt returned by a completed operation carries the response bytes and
their SHA-256 (`responseSha256`). The wrapper archives those bytes write-once,
and the Project Manager independently recomputes SHA-256 over the archived file
via `archive_pro_response.ps1`. **A mismatch is a refusal, never a repair** — do
not reconcile by editing the file. This is the charter's one sanctioned SHA-256
site (`sha256_whitelist=review_round_archive_integrity_only`).

There is no capture step and nothing to delegate: choosing which message is the
ruling is proven by the receipt's message identity, and the archive decision
stays with the Project Manager. Create no standing relay, dispatcher or Monitor.

### Transport faults are carried, and the Project Manager carries them

Every transport anomaly observed during a round goes into that round's
`## Transport faults` section: each `HMASD_AGENTIFY_TRANSPORT_ERROR` code, any
terminal state other than `NATURAL_COMPLETION_VERIFIED`, an HTTP 409
(idempotency or binding conflict), a tab-precondition failure, or a receipt that
failed local validation. In the same round either repair this Skill or record
why not. `tests/review_round_contract_test.ps1` refuses a round whose
`## Transport faults` section is empty or still `TODO` — that check exists
because this section was once a TODO nobody read for thirty rounds.

## Required inputs

Require the assigned round path, pushed 40-character `stage_commit`, exact
question path, exact raw path, mechanical-intake path, registered reviewer
conversation, and declared input paths.

**Question scope.** At touchpoints 1 and 3 the question document carries
decisions — claim-defining questions, tree-structured where dependent. At
touchpoint 2 it is a conformance question and nothing more — see **Writing the
question** above (user ruling 2026-07-30). At no touchpoint does it assign
verification labor to the reviewer: no fact-inventory confirmation,
no implementation-detail checking, no auditing of what the execution side can
verify itself. The two bounded exceptions are the Stage A design audit and
the Stage B code-science alignment diff defined in `$hmasd-acceptance-gate`.

Before submission:

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

```text
transport_backend=agentify
transport_wrapper=.claude/skills/hmasd-review-round/scripts/agentify_pro_transport.py
agentify_required_commit_source=AGENTIFY_REQUIRED_COMMIT_in_wrapper
prompt_artifact=fence_or_continuation_file_verbatim
one_send_per_operation_key=true
fence_operations_per_round=1
resend_policy=verify_existing_then_fresh_key_only_on_proven_presend_failure
transport_tab_mutation=forbidden
non_strict_query_endpoint=forbidden
evidence_recovery=inline_continuation_paste_only
completion_proof=receipt_NATURAL_COMPLETION_VERIFIED
waiting=in_band_blocking_submit
```

The wrapper is the only send path. It refuses unless the running Agentify
instance reports the pinned source commit with a clean tree (`/health`), exactly
one idle tab exists bound to the reviewer's `stable_key` at the exact registered
conversation URL, and no query is active. It performs one `POST /review-query`:
Agentify inserts the prompt in a single operation, sends once, structurally
never clicks Continue/Retry/Answer-now, proves completion with two snapshots at
least three seconds apart carrying the same assistant message id and text
SHA-256 and no active stop control, and returns a receipt whose terminal state
must be `NATURAL_COMPLETION_VERIFIED` with `sendCount=1`. The wrapper validates
all of that locally before writing anything.

Run every command with the project Python:

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' `
  .claude/skills/hmasd-review-round/scripts/agentify_pro_transport.py <command> ...
```

### Deterministic transport state machine

Execute these states in order. Do not skip a state because an older receipt is
on disk or the ledger looks familiar.

| State | Required observation | Mechanical action | Exit condition |
|---|---|---|---|
| `PREPARE_OPERATION` | Preflight printed `ROUND_PREFLIGHT_READY`; registry supplies `stable_key`, conversation and model | `prepare --kind fence` (or `--kind continuation`) with a fresh operation key; runtime files go under `logs/review_transport/<round>/` | `HMASD_AGENTIFY_REQUEST_PREPARED`; `TRANSPORT_BACKEND.json` and `request.json` written |
| `SUBMIT_AND_WAIT` | Wrapper preconditions hold (pinned commit, one idle bound tab) | `submit` in background execution — it blocks inside Agentify up to 45 minutes. Ending the turn to wait is a stall; the wait is in-band. On client death, re-run `submit` with the **same request file**: the same operation key resumes or returns the stored receipt, never a second send | `HMASD_AGENTIFY_TRANSPORT_COMPLETE`; `receipt.json` written |
| `VERIFY_RECEIPT` | `receipt.json` exists | `verify` — full local receipt re-validation | `HMASD_AGENTIFY_RECEIPT_OK` |
| `ARCHIVE_AND_INTAKE` | Raw path absent (write-once) | `archive --raw-output <round>/21_PRO_OPEN_RAW.md`, then `archive_pro_response.ps1` for the independent digest bond; write the provenance intake | Exact raw archived, digest equal, intake recorded; Project Manager proceeds to its separate scientific reconciliation |

### The freshness fence

The prompt of a fence operation is the round's `10_FENCE.txt`, byte-verbatim:

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

**An accepted matching fence is never resubmitted**, and the ledger is what
proves the state. One fence operation key exists per round, minted at
`PREPARE_OPERATION` and recorded in `TRANSPORT_BACKEND.json` and the intake
record. Re-running `submit` with the same request file is always safe: Agentify
returns the stored receipt or resumes the wait, and a payload change under the
same key is refused with a 409. Before any resend under a **fresh** key, run
`submit --verify-existing` and require `present=false` — an operation that was
aborted before its send (`review_operation_closed_create_fresh`) is the only
state that authorizes a fresh key, recorded as a `RECOVERY_ATTEMPT` line.
A further fresh key is permitted only when the failed attempt carries server
proof of no-send (`noClickProven=true` plus `present=false` — the
duplicate-submission risk the cap guards is then structurally absent) AND a
materially changed state before the retry; absent either, the round is
`REVIEW_TRANSPORT_BLOCKED` (amended 2026-08-01 after two proven pre-send
409s in one round).

### Standing tab precondition

After a key's first send, each registered `stable_key` has one live tab in the
Agentify-managed browser whose record carries the exact conversation URL, with
the composer showing the registry's `expected_model_ui`; every later operation
requires that tab idle and unique, and a missing, mismatched, duplicated or
busy tab is terminal — report it, never repair it.

**The first send of a fresh `stable_key` is the one exception** (measured
2026-08-01): a tab record's URL is fixed at creation, so a pre-created tab
mismatches forever, and only `/review-query` itself can create the tab bound
to the conversation URL. For that first operation only, and after confirming
no tab with the key exists, run `submit --allow-tab-creation`. The flag is
used once per key per server lifetime: Agentify's tab-key registry is
in-memory (measured 2026-08-01), so an Agentify restart clears every
binding, and the key's next send re-creates its tab with the same flag under
the same no-tab-exists precondition.

### Evidence-access recovery

An assistant message reporting it could not read question-listed evidence, or
unavailable repository/connector access, is a transport diagnostic — never the
round answer, never archived as raw. Recover in the same conversation under the
same accepted fence:

1. take the evidence paths from the question only, never from the diagnostic;
2. materialize them from `stage_commit`, not from the current working tree,
   with `git show <stage_commit>:<path>` — the strict endpoint has no
   attachment support, so the allow-listed files are pasted inline into one
   continuation artifact, each inside a fenced code block naming its path;
3. send that artifact as one `--kind continuation` operation — never a second
   fence. The whole prompt must stay under Agentify's 200,000-character limit;
   if the allow-list cannot fit, report `REVIEW_TRANSPORT_BLOCKED` instead;
4. the candidate raw is the receipt of that continuation operation, under the
   same receipt validation;
5. `build_review_evidence_archive.ps1` remains the preflight allow-list
   integrity gate; its zip is no longer uploaded anywhere. The non-strict
   `/query` endpoint and its attachments are forbidden in this workflow.

Record diagnostic and recovery as transport facts in the mechanical intake.
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
| carries | the round identity block | prose citing the `stage_commit` once, no identity block |
| how many | exactly one per round, never resubmitted | bounded by the conformance check that owns them — never an open-ended series |
| authored by | Project Manager | Project Manager |
| sent as | the round's single fence operation | one `--kind continuation` operation each, fresh operation key |

Every convergence turn is authored by the Project Manager as a
`11_CONTINUATION_<n>.txt` artifact and carried verbatim, exactly like the
question. The wrapper refuses a continuation artifact containing the fence
opening line, and requires the `stage_commit` cited once — the mechanical
binding between a continuation and its round. Transport never composes one,
never paraphrases one, and never sends one it was not given.

Each answer arrives under the same receipt validation the first answer
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

After a verified receipt:

1. `archive` writes the receipt's response bytes to the assigned raw path
   without rewriting, normalization, filtering, or summary, and rereads for
   byte equality. Raw is write-once.
2. Run `archive_pro_response.ps1 -RoundPath <round> -StageCommit <commit>
   -ReceiptPath <receipt.json>` — the independent digest bond plus protocol
   checks (this round's `stage_commit` present, opening heading, plausible
   size). Its JSON is the mechanical intake's `## Capture` record, including
   `response_sha256` and the operation key.
3. Keep transport facts separate from the subsequent Project Manager scientific
   reconciliation; no callback or routing step exists.

The required order is:

```text
exact raw -> provenance intake -> Project Manager reconciliation
```

## Recovery and retirement

A wrapper, runtime, Agentify or archive failure keeps the round active while a
safe in-scope recovery remains. Try materially distinct recoveries; never repeat
an identical failed action without changed state, and
record each attempt as one `RECOVERY_ATTEMPT attempt=/boundary=/action=/outcome=`
line. Before any submission under a fresh operation key, prove via
`submit --verify-existing` that the prior operation never sent. Report
`REVIEW_TRANSPORT_BLOCKED` only when safe recovery is exhausted, with the direct
cause, attempt summary, duplicate-submission risk and exact resume condition.
A stale response from another round has no authority and never
replaces the current-round raw or launches a successor.

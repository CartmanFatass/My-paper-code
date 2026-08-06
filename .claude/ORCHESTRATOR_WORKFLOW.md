# Claude Orchestrator Workflow (long-term operating contract)

```text
document_kind=claude_orchestrator_workflow
workspace=C:/worktrees/HMASD/CLAUDE_HMASD_FULL_TAKEOVER_20260805 (permanent)
branch=claude/hmasd-full-takeover-20260805 (the only branch ever pushed)
authority_note=adds_no_authority_over_AGENTS.md; AGENTS.md remains the sole
  project authority/routing contract. This document organizes Claude-side
  work only.
orchestrator_model=any capable Claude model (written to be runnable by Opus;
  judgment calls are the orchestrator's, but every hard constraint and its
  reason is stated here rather than assumed)
revision=2026-08-06 v4 (rewrites Section 6 from a mapping table into the
  orchestrator -> implementer -> reviewer workflow, modelled on the Codex Code
  Project Manager process, after the user observed that the subagents were
  defined but never actually used: a table says which agent, never when, so
  the default was always "not yet". v3 added Section 3, the routing and
  pre-dispatch verification contract, after a measured session in which
  roughly half the external-review and compute cost was spent on questions the
  code side could have answered locally; v2 was the post-takeover
  consolidation superseding the v1 role-by-role mapping)
```

## 1. The actual logical model

The Codex-era workflow was organized as persistent role sessions (Explorer,
Code Manager, transport operator, verifier children). The Claude workflow is
NOT a role-by-role or skill-by-skill port of that. The working structure is
a three-way split, and understanding it is prerequisite to everything else:

1. **The orchestrator (this session)** holds, inline:
   - the local remainder of the Explorer role: advancing one candidate at a
     time, drafting proposals and derivations, reconciling external reviews,
     maintaining longitudinal state (`local_research/RESEARCH_CONTINUITY.md`);
   - the ENTIRE Code Manager (cm/cpm) role: implementation, focused tests,
     independent-review dispatch, technical acceptance, boundary checks,
     isolated commits, pushes.
   There are no separate role sessions. "Explorer lane" / "CM lane" in older
   artifacts name phases of this one session, not separate actors.
2. **External Pro** holds ALL scientific judgment. Nothing scientific is
   accepted locally: every proposal and derivation is validated by a fresh
   adversarial Pro session BEFORE freezing, and every pushed science commit
   is audited by a fresh Pro session AFTER acceptance
   (CODE_SCIENCE_ALIGNMENT_AUDIT). The user does not sign off on science
   ("科研判断提交外审即可"); the orchestrator does not self-certify it.
   Pro is never simulated, and a Pro response is archived verbatim with a
   byte comparison before anything else happens to it.
3. **Subagents** (`.claude/agents/`: implementer, reviewer, verifier,
   experiment-operator, scout, mechanic — six, registered in
   `.claude/CAPABILITY_MAP.md`) are task-level tools, not roles. They are
   stateless and single-shot; their outputs are advisory inputs to the
   orchestrator, which alone accepts, commits, and records. They never load
   Codex session charters. Section 6 says when each one is mandatory; that
   section is not optional reading, because the failure it fixes is these
   contracts existing and never being reached for.

**The user's role**: direction and scope ("work on X", "one demonstration of
this task type is enough"), quota/budget control, and merge decisions.
Merging to mainline happens only when the user says so; the worktree and
branch are permanent and never cleaned up unprompted.

## 2. The science cycle (per candidate, demonstrated on UCOPE and ORBIT-LITE)

One candidate at a time. Each cycle:

1. **Proposal.** The orchestrator drafts a successor treatment or derivation
   for the candidate (revision JSON under
   `local_research/portfolio/directions/<CAND>/revisions/`, derivations
   under `.../derivations/`). Proposals bind to the exact inherited accepted
   object (commit + blob SHA) and change one thing.
2. **Adversarial validation.** The proposal is sent to a FRESH External Pro
   session as an INDEPENDENT_RESEARCH_DIRECTION_PACKET request whose
   terminal line must be exactly one of DERIVE_BEFORE_DISCRIMINATOR /
   DISCRIMINATOR_SPECIFIABLE_NOW / PARK_SCIENTIFICALLY. The question inlines
   the artifact verbatim and cites the pinned GitHub blob URL so Pro can
   verify source claims itself.
3. **Archive + reconcile.** The response is archived verbatim
   (byte-compared) and a reconciliation JSON classifies every correction row
   (APPLY / RETAIN / PARK_CONDITION). Rows Pro marks ALREADY_ADEQUATE are
   LOCKED: they are never re-litigated in later rounds, and later documents
   state this explicitly — this is what makes multi-round loops converge
   instead of thrash.
4. **Loop or exit.** On DERIVE_BEFORE_DISCRIMINATOR: write ONE bounded
   amendment addressing exactly the enumerated gaps, and go to 2. Expect
   escalating literalness across rounds — prose design first, then literal
   tables with hand proofs, then a compilable contract module with real
   digests; do not resist this, it is the review working correctly. On
   PARK_SCIENTIFICALLY: the park must be backed by executable evidence (an
   archival certificate reproducing the reviewer's algebra independently,
   e.g. UCOPE's `acquisition_park_certificate.py`) before it is recorded as
   final. On DISCRIMINATOR_SPECIFIABLE_NOW: freeze and go to 5.
5. **Implement.** Against the frozen contract only — no substitution, no
   scope growth. Rational arithmetic (`fractions.Fraction`) for exact
   claims; deterministic, byte-stable serialization; invariant tuples;
   proof-sized tests whose oracle preference is exact hand-checkable case >
   structural invariant > differential vs small reference > boundary/
   fail-closed > seeded band. Delegation to `hmasd-implementer` is governed
   by the trigger rule in Section 6.2 — a frozen contract is exactly the
   precondition that makes delegation legitimate here.
6. **Independent review.** `hmasd-reviewer` (clean context that has not
   seen the implementation reasoning) before technical acceptance; findings
   resolved or explicitly risk-accepted with reasons, never silently. This
   is MANDATORY for claim-bearing changes, not advisory — Section 6.2 states
   the trigger and Section 6.4 the disposition record.
7. **Commit + push.** Boundary check first (Section 7), isolated science
   commit, push the dedicated branch, verify via `git ls-remote` (local
   reflog write failures on this OneDrive checkout are cosmetic; ls-remote
   is authoritative).
8. **Alignment audit.** A fresh Pro session (never one that gave
   constructive advice on this candidate) reconstructs the realized
   proposition from the exact pushed commit; final line ALIGNED / MISMATCH
   / SCIENTIFIC_AMBIGUITY. Verbatim archive + intake JSON under
   `local_research/pro_reviews/<item>/`.
9. **Record.** Update `local_research/RESEARCH_CONTINUITY.md` after every
   completed item — it is the longitudinal memory the next session resumes
   from.

**Round budget.** Validation rounds cost real quota. The user decides how
many same-type demonstrations are worth running; when a loop has served its
purpose (e.g. the pattern is established and the remaining gap list is
mechanical), record the state cleanly and check direction with the user
rather than opening further rounds by default.

**Self-check before dispatch.** See Section 3, which generalizes this: every
exact-arithmetic claim is recomputed locally with `Fraction` before sending,
and so is everything else that is mechanically checkable.

## 3. Routing: what Pro decides, and what the orchestrator must settle first

This section exists because the loop research → code → experiment was running
badly, and the cause was not the review. It was the orchestrator spending the
expensive, serialized, scientific-judgment channel on questions the code side
could have answered in seconds.

### 3.1 The asymmetry, as numbers

Write these down; they make the decision rule almost trivial, and not writing
them down is what allowed the wrong default for months.

```text
External Pro round trip   15-40 min wall clock, STRICTLY SEQUENTIAL
                          (one tab: a dispatch blocks every other direction),
                          consumes the user's quota
Local verification        seconds to minutes, parallel, free
One training run          hours (UCOPE 8 seeds x 300 iterations ~ 1.5 h)
```

A local precondition check is two to three orders of magnitude cheaper than
the review round it prevents, and three to four cheaper than the training run
it prevents.

### 3.2 The orchestrator's structural advantages on the code side

These are not preferences; they are capabilities Pro does not have and cannot
be given through a question:

- **Direct access to the exact source at the exact commit**, including files
  that are gitignored and therefore invisible to the reviewer. (Pro has stated
  this limit twice: it could not authenticate the ORBIT module digest, and it
  could not open the UCOPE result artifact.)
- **Execution.** Pro reasons about what the code would do; the orchestrator
  runs it and reads the bytes.
- **Differential verification.** Two independent implementations of the same
  quantity can be run and required to agree bitwise.
- **Sweeps.** A claim of the form "this identity holds / this case is not
  generic" can be measured over millions of points instead of argued.

Any question whose answer these capabilities can produce is the orchestrator's
to answer, and answering it is not optional.

### 3.3 The routing rule

**Goes to Pro. Pro alone decides:**

- the estimand, the population, the null, the unit of analysis;
- whether a design identifies what it claims to identify;
- whether a registration is admissible for execution, before any registered
  kernel is observed;
- what a measured result may and may not be claimed to establish, and the
  exact sentence that may be written;
- whether a park, a closure or a reactivation is warranted;
- the reading of a number whose arithmetic is not in dispute.

**Never dispatched as a question. Settled locally first, always:**

- whether a computed quantity is the quantity it is named after;
- whether two objects are equal, disjoint, independent, held out or
  non-overlapping — write the predicate and run it over the actual registered
  constants;
- whether a default equals the registered value;
- whether a claimed identity holds in the executed library, at the executed
  version, on the executed hardware — execute it;
- arithmetic, digests, counts, file contents, source facts;
- whether an inference is valid **given** facts that can be measured.

The failure mode this prevents has a precise name: **outsourcing mechanical
verification to the scientific-judgment channel.** It is expensive twice — it
burns a serialized round, and it spends reviewer attention on arithmetic
instead of on science.

**Measured, 2026-08-06, so a future orchestrator knows this is not abstract.**
Of four FOLR registration rounds: one was correctly routed (a logit-space
bound reported as a probability-space bound — a scientific correction only a
reviewer could make); **two were mechanical and avoidable** (a bias reported as
the update gate; gate saturation reported as bitwise carry — in both, what Pro
actually did was read the source and recompute); the fourth passed on the first
try because the measurement preceded the document. In the same session UCOPE
burned a full 8-seed training run on a wrong default budget, and let Pro find a
seed collision (`ledger_seed == seed + 2`) that a ten-line predicate would have
caught. Roughly half of that session's review and compute cost was self-
inflicted.

### 3.4 The pre-dispatch verification gate

Run all of these before any dispatch. They are cheap; the round they protect
is not.

1. **Every witness or certificate is executed, and checked against an
   independent path.** Where the claim is bitwise, require bitwise agreement.
   Worked example: the FOLR focal-GRU witness reproduces the pinned `RNN.cpp`
   operation sequence explicitly *and* calls the frozen `GRUCell`, and raises
   if they differ. Use the library's own kernels in the replication — a
   hand-rolled reduction can differ from the library matmul in the last ulp,
   and a witness that reproduces the algebra but not the arithmetic is the same
   defect one level down.
2. **Every independence / holdout / disjointness / non-overlap claim gets a
   predicate that is written and run.** Not inspected by eye. The UCOPE
   evaluation support was described as held out for eight seeds while one seed
   trained on the evaluation ledgers themselves.
3. **Every constant with a default is asserted equal to the registered value,
   in a test.** Two separate defects of exactly this class in one session. A
   value only ever supplied by the caller is a value two callers can disagree
   about.
4. **Every "this is not generic / not a formality" claim is measured, before
   the document is written.** FOLR v4 measured that exact float32 carry fails
   for ~10% of candidate values at h=1 — which converted Pro's objection from
   formal to load-bearing and determined how the whole amendment was written.
5. **Every exact-arithmetic claim is recomputed with `Fraction`.**
6. **Assume an adversarial reader with the source in hand**, because that is
   literally what Pro is. Anything such a reader would check, check first.

### 3.5 Order of operations, and shape

**Measure, then argue.** Write the document from the measured numbers; never
write the numbers from the document. A justification drafted before its
measurement tends to describe the measurement its author expected.

**Fail closed by construction.** Derive downstream numbers *from* the witness
rather than keeping a constant that stays usable after its premise collapses,
and make the claim and the number read different fields. The recurring defect
across this portfolio is a quantity that is correct about one thing read as
though it settled another; code shaped this way cannot express that error.

**State what the round buys.** Before dispatching, say in one line what this
round obtains that a local check could not. If the answer is "confirmation that
my arithmetic or my reading of the source is right", do not dispatch — check
it. This applies to numbers arriving *from* Pro as well: an arithmetic slip in
a returned ruling is corrected locally and recorded with both derivations, not
sent back.

### 3.6 The enforcement, which is not this document

Everything above is prose, and prose is what already failed once: Section 2
carried a "self-check before dispatch" instruction while two mechanically
findable defects were shipped. So the discipline is operationalized as a skill
with a blocking script:

```text
.claude/skills/hmasd-science-dispatch/
├── SKILL.md                        # the routing rule and the six-step path
└── scripts/hmasd_dispatch_receipt.py
```

Invoke the skill before any dispatch. Two of its steps are mandatory and
mechanical:

1. **A clean-context document review.** `hmasd-reviewer`, holding the outgoing
   document AND the source it describes, asked only "does this document
   describe this code, and where did each number come from" — never the
   science. Its verbatim output goes to `15_DOCUMENT_REVIEW.md` and must end
   with `DOCUMENT_MATCHES_SOURCE`. This is the local stand-in for the reader
   who found every prose/code mismatch so far, and it costs seconds.
2. **The receipt gate.** `hmasd_dispatch_receipt.py` reads
   `10_DISPATCH_MANIFEST.json`, proves every substantive figure in the question
   traces to a declared truth source at the document's own precision, runs the
   declared preconditions, requires the document review, and writes
   `30_DISPATCH_RECEIPT.json`. It **exits non-zero**; that exit, not this
   paragraph, is the guarantee. Never widen the whitelist to make a figure
   pass — the whitelist is the list of numbers nobody recomputed and it travels
   in the receipt.

The item directory convention gains two slots, in order:
`10_DISPATCH_MANIFEST.json` → `15_DOCUMENT_REVIEW.md` → `20_RAW_QUESTION.md` →
`30_DISPATCH_RECEIPT.json` → `40_RAW_RESPONSE.md` → `60_ALIGNMENT_INTAKE.json`.

## 4. Review-item file conventions

Each Pro interaction is one item directory:
`local_research/pro_reviews/<kind>_v<N>_<candidate>_<topic>[_<commit>]/`
containing `20_RAW_QUESTION.md` (exact sent text), `40_RAW_RESPONSE.md`
(verbatim archive, byte-compared against the results envelope, size and
SHA-256 recorded), and for audits `60_ALIGNMENT_INTAKE.json`. Reconciliation
records live with the candidate, not the review item. Conversation URLs are
recorded so session-independence lineage stays auditable.

## 5. External Pro transport (Agentify desktop HTTP API)

Transport is a Node script driving the local Agentify desktop endpoint —
not a browser-automation session. A template script lives in the session
scratchpad (`*_transport.mjs`); per review it is derived by substituting the
QUESTION path and OUT_DIR, then launched as a TRACKED background task
(`run_in_background`), never a detached shell job — tracked tasks re-invoke
the orchestrator on completion, detached jobs silently don't.

Contract: the sent payload is exactly the UTF-8 question file content; one
results envelope (`AGENTIFY_REVIEW_BATCH_RESULT` JSON with per-item
`question_path`/`status`/`response`/`conversation_url`/`error`) is the only
result channel; the archived response must byte-equal the envelope's
`response` field.

Hard transport discipline, with the mechanics that make it non-negotiable:

- **Send sequence**: `/conversations/new` on the DEFAULT tab → wait ~8s for
  the page to settle → verify the visible "Pro" model label via
  `/read-page` → single `/query` with expectedModel Pro → poll with
  short-timeout `/wait-response` calls. Reason: enumerating the model
  picker on an unsettled page returns `expected_model_unavailable` with
  `availableModels: []`; keyed tabs land on a page variant without the
  picker. `expected_model_unavailable` is pre-send and safe to retry.
- **`GET /status` (no body) is the ONLY non-blocking probe.** Every POST
  endpoint blocks behind an active `/query` until the HTTP client's
  headers-timeout. GET /status returns `activeQuery` and the real tab URL;
  a `chatgpt.com/c/<id>` URL proves a conversation was created.
- **Never resend on a ~5-minute `fetch failed`.** Node's HTTP client
  (undici) aborts long-held requests client-side at ~5 min while the server
  is still generating; the query was almost certainly SUBMITTED. Resending
  would duplicate a live question — the one unrecoverable transport sin.
  Classify via GET /status + tab URL, then observe with `/wait-response`.
- Never interrupt an active generation, never press Continue/Retry/Stop,
  never send placeholders. A transport error is a transport fact, never a
  scientific result. Fresh conversation per independent review; reuse only
  for a true follow-up in the same constructive thread.

## 6. The subagent workflow: orchestrator → implementer → reviewer

The process is: the orchestrator freezes an exact assignment, spawns a
registered child with a named file scope, the child returns raw facts and
**never accepts its own work**, an independent reviewer runs before technical
acceptance, and the orchestrator alone stages, commits and pushes.

This is a logical migration of the Code Manager process the Codex side ran, not
a reference to it. Everything needed to execute it is stated here and in
`.claude/CAPABILITY_MAP.md`; the Codex charters are dormant, hard read-only from
this branch, and are never loaded as instructions. `AGENTS.md` remains the sole
project authority and this section adds nothing to it.

### 6.1 Why this needs a trigger rule and not a table

Before this revision §6 was the mapping table now at §6.5, plus one sentence in
§2 item 6, and **the subagents were still not used** — sessions ran end to end
inline. A table answers "which agent for which work" but never says *when*, so
the default is always "not yet". The trigger rule below is therefore written as
a condition that can be checked, in the same shape as §3's routing rule.

The structural argument is the same one in both directions. §3 says a Pro round
is expensive and serialized, so mechanical questions stay local. Here the
argument inverts: **a clean-context reader is the one thing the orchestrator
structurally cannot be.** Once this session has written the implementation, it
has also written the reasoning that makes the implementation look correct, and
it cannot un-read it. That is not a discipline problem and no amount of care
fixes it. Every registration round rejected for a prose/code mismatch was
visible to a reader holding only the document and the source.

### 6.2 The trigger rule

**MUST spawn `hmasd-reviewer`, in a fresh agent, before:**

- technical acceptance of any **claim-bearing** change — code whose output
  reaches an artifact, a registration digest, a certificate, a portfolio
  document or a Pro question;
- any document dispatched to External Pro (also mandated by
  `.claude/skills/hmasd-science-dispatch/` Step 3, whose gate script requires
  `15_DOCUMENT_REVIEW.md` with terminal `DOCUMENT_MATCHES_SOURCE`).

Not required for: config-lane edits, test-only maintenance, and changes whose
whole content is already pinned by a failing-then-passing test the orchestrator
wrote first.

**MUST spawn `hmasd-implementer` when both hold:**

- the brief is **already frozen** — a Pro-approved contract, a written revision
  brief, or a named defect with a named fix and a named test; and
- the orchestrator's context already holds reasoning the implementation should
  not inherit (typically: this session argued the science, so it will
  unconsciously implement toward its own argument).

Also use it, without the second condition, when **two or more independent
bounded units** exist — they run concurrently, which inline work cannot.

Do **not** delegate implementation whose specification is still emerging. If
the assignment block in §6.3 cannot be written, the unit is not ready to
delegate — and that is usually a signal it is not ready to *build* either. Say
so rather than spawning an agent to discover the spec.

**MUST spawn `hmasd-scout` / `hmasd-mechanic` when** the alternative is
guessing at a read-only fact (does a real producer/owner/clock object exist for
this binding? what exactly is in these 90 files?). Absence is a first-class
result; neither agent may invent a stand-in.

**MUST spawn `hmasd-verifier` for** any of: a full test suite (not a single
targeted test), an end-to-end CLI exercise, or a re-verification sweep after a
change set. The enumeration is the trigger, deliberately — "long enough that
the output would crowd out the reasoning" cannot be evaluated before running
the command, and running it inline is exactly what the trigger exists to
prevent. It returns a typed verdict per command and, crucially, classifies each
non-pass as `CODE_DEFECT` versus `OPERATIONAL_FAILURE` versus `PRE_EXISTING`.
Getting that split wrong in either direction is expensive: a real regression
read as environmental is missed, and an environmental failure read as a defect
sends this session to repair source that was never broken.

**MUST spawn `hmasd-experiment-operator` for** any registered run measured in
minutes or hours. The design is already frozen and approved before it is
spawned; the operator changes nothing about it, interprets nothing, and returns
locators plus the named summary fields. **A refusal is a complete result** — a
`RegistrationMismatch` or a downgraded terminal comes straight back, never a
re-run with different arguments.

The last two exist for context, not independence. The orchestrator's window is
the scarce resource in a long session, and raw output nobody will re-read is its
largest consumer. `.claude/CAPABILITY_MAP.md` has the full pressure-source table.

### 6.3 The assignment contract (freeze before spawning)

A child that has to infer its own boundary produces work that has to be
re-derived to be checked. Every assignment prompt names all five:

```text
frozen_brief=<path or inlined text — what is fixed and may not be re-decided>
writable_scope=<exact files the child may edit; everything else is read-only>
focused_tests=<exact commands, with the interpreter and --basetemp>
completion_condition=<the observable that ends the unit>
forbidden=<AGENTS.md, .agents/, .codex/, docs/project/, the two workspace
  scripts, .claude/ — plus git commit/push/merge/rebase, always>
```

For `hmasd-reviewer` the first field is the brief the change *claims* to
satisfy and the second becomes the diff scope (files or commit range) — its
independence is worthless if it is told what the implementer concluded, so the
assignment carries the brief and the diff, never the reasoning.

### 6.4 Return, disposition, acceptance

Children return **raw facts and no acceptance claim** — that is written into all
six contracts and is the load-bearing property. A terminal line such as
`VERIFICATION_PASSED` or `UNIT_COMPLETE` reports what the child observed; it is
never an acceptance. The orchestrator converts the return into a disposition and
records it:

```text
unit=<what was delegated>
child=<agent type>            changed_files=<paths>
writable_scope_honored=<yes | the paths written outside the assignment>
tests=<commands + pass/fail tails, as observed here, not as reported>
findings=<id | file:line | one-sentence defect | failure scenario>
disposition=<APPLIED | RISK_ACCEPTED(reason) | REJECTED(reason)>   per finding
active_line_delta=<added minus deleted>   superseded_deleted=<paths|none>
commit=<40-char commit the accepted work landed in>
blockers=<none | what remains outstanding>
```

Rules that make this more than paperwork:

- **Re-run the child's tests yourself before accepting.** A pass reported by
  the agent that wrote the code is not evidence; the same command run here is.
- **Every finding gets an explicit disposition.** `RISK_ACCEPTED` is legitimate
  and must carry a reason. Silence is not a disposition.
- **`commit` and `blockers` are not optional.** Every other evidence record in
  this workflow is commit-bound — §2 step 1 binds proposals to commit + blob
  SHA, step 8 sends the exact pushed commit to the alignment audit — and an
  acceptance record that names no commit is the one link in that chain that
  cannot be checked later. `blockers=none` is an assertion someone made; an
  absent field is not.
- **Technical acceptance, git and science stay with the orchestrator.** No child
  stages, commits, pushes, or decides that a result is good. One unit, one
  acceptance owner.
- A child's failure is **evidence, not a stop**. Choose bounded reassignment for
  an operational failure and repair for a real defect; do not use a subagent as
  an incremental debugger.

### 6.5 Mapping

| Work | Executor | Model / effort | Buys |
|---|---|---|---|
| Bounded implementation unit against a frozen brief | `hmasd-implementer` | opus / high | context + concurrency |
| Independent engineering review (clean context) | `hmasd-reviewer` | opus / xhigh | **independence** |
| Long verification exercise (suite, CLI, readiness) | `hmasd-verifier` | sonnet / high | context |
| One registered experiment run | `hmasd-experiment-operator` | sonnet / high | context |
| Read-only object-existence / semantics recon | `hmasd-scout` | sonnet / medium | context |
| Read-only mechanical verification | `hmasd-mechanic` | haiku / low | context |
| Science drafting, reconciliation, freezes, routing, Pro intake, technical acceptance, git | orchestrator, never delegated | session model | — |

Only the reviewer buys independence, and it is the one thing this session cannot
supply itself. Everything else buys context. Both are real, but they justify
different things: independence is mandatory before acceptance, while context is
a judgment about size.

Full registry, including every Codex-era capability and where it went — or why
it deliberately went nowhere — is `.claude/CAPABILITY_MAP.md`.

Mechanics: `Agent` with `subagent_type`, one message carrying every independent
call so they run concurrently. The definitions in `.claude/agents/` own the
defaults. Subagent output is advisory in all cases.

**When to override `model` on `hmasd-implementer`.** The Codex side ran two
implementer profiles, routine and protected; here it is one contract and a
parameter, so the criterion has to live somewhere and it lives here. Drop to
`sonnet` for a **routine** package — behaviour-preserving modularization,
localized repair, test maintenance, script cleanup, bounded performance work.
Keep the `opus` default for anything touching an **estimand, an RL/MARL
mechanism, numerical or training semantics, a registration, or any other
protected invariant**. The override changes cost, never authority, and never
substitutes for orchestrator acceptance.

## 7. Boundaries (checked at every commit)

- **Codex control plane is hard read-only**: `AGENTS.md`, `.agents/`,
  `.codex/`, `docs/project/`, `scripts/hmasd_workspace_ticket.py`,
  `scripts/hmasd_workspace_boundary_guard.py`. `git diff <base>` over these
  paths must be EMPTY at every commit. Known reconciliation item for WDM:
  AGENTS.md still describes `.claude/agents/` as thin entry profiles; per
  the 2026-08-05 user amendment they are self-contained Claude-native
  contracts. AGENTS.md is not edited from this branch.
- **Claude control plane** (`CLAUDE.md`, `.claude/`) is maintained by the
  orchestrator, always in dedicated configuration commits, never mixed with
  science commits.
- Tracked changes go only to the dedicated branch; never push, merge,
  rebase, or cherry-pick to `aggressive` or any mainline.
- No production-code synthetic stand-ins; absence maps are valid, closeable
  results. No worktree/ticket deletion, no merges, without explicit user
  instruction.

## 8. Engineering disciplines (house rules binding all implementation)

Small-change shape: ≤3 new tracked files and ≤500 new active lines per
mechanism; refactors net-negative; files >1200 lines never grow; a successor
deletes its predecessor in the same commit; no versioned scientific
filenames; no hash handoffs. Exact science artifacts use rational
arithmetic end-to-end and compact deterministic JSON (`separators=(",",
":")`, sorted keys) with byte-stable `to_bytes`. Every certificate-style
artifact carries executable invariants and a RAW_OUTPUT_BINDING. A focused
test must reject at least one plausible wrong implementation — tests that
cannot fail a wrong implementation are decoration, not evidence.

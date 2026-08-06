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
revision=2026-08-06 v3 (adds Section 3, the routing and pre-dispatch
  verification contract, after a measured session in which roughly half the
  external-review and compute cost was spent on questions the code side could
  have answered locally; v2 was the post-takeover consolidation superseding
  the v1 role-by-role mapping)
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
3. **Subagents** (`.claude/agents/`: scout, mechanic, implementer, reviewer)
   are task-level tools, not roles. They are stateless and single-shot;
   their outputs are advisory inputs to the orchestrator, which alone
   accepts, commits, and records. They never load Codex session charters.

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
   fail-closed > seeded band.
6. **Independent review.** `hmasd-reviewer` (clean context that has not
   seen the implementation reasoning) before technical acceptance; findings
   resolved or explicitly risk-accepted with reasons, never silently.
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
it.

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

## 6. Subagent and model mapping

| Work | Executor | Model / effort |
|---|---|---|
| Bounded, well-specified implementation unit | `hmasd-implementer` | opus / high |
| Independent engineering review (clean context) | `hmasd-reviewer` | opus / xhigh |
| Read-only object-existence / semantics recon | `hmasd-scout` | sonnet / medium |
| Read-only mechanical verification | `hmasd-mechanic` | haiku / low |
| Science drafting, reconciliation, freezes, intake, acceptance, git | orchestrator, never delegated | session model |

Per-call `model` overrides are allowed for one-off calibration. Subagent
output is advisory; acceptance stays in the orchestrator.

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

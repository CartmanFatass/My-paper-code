# What model, and how much planning, does this project's implementation need?

```text
status=ACCEPTED
accepted=2026-07-25
accepted_by=user
factor_a=model tier -- sonnet/high vs opus/high
factor_b=brief density -- bounded brief vs detailed plan
control=hmasd-implementer (sonnet / high)
treatment=hmasd-frontier-implementer (opus / high)
instructions=byte-identical below the frontmatter, asserted by contract test
deliverable=one of all-sonnet | routed | all-opus, plus a routing predicate if routed
compute_authorized=stage_1_pilot_only
```

Pre-registered for the same reason the G20R2 contract is: a comparison whose
outcome measure is chosen after seeing the outputs measures nothing. If we hold
the science to pre-registration, we do not exempt our own tooling decisions.

## The two questions

**A. Does raising the implementer from sonnet/high to opus/high reduce the rate
at which a defective specification reaches committed code?**

**B. Does detailed up-front planning do the same — and can it substitute for
tier?**

Neither asks which model writes better Python. Both tiers write working Python
here; that has never been the failure mode. The failure mode is narrower and
much more expensive:

> a brief or frozen design contains a latent defect, the implementer builds
> exactly what it was told, the package passes its own tests, and the result is
> a scientifically invalid measurement that looks clean.

### The deliverable

One of three, with the evidence that chose it:

| | Meaning |
|---|---|
| **all-sonnet** | keep `implementer_tier=sonnet_high`; spend the budget on briefs and gates instead |
| **routed** | opus for tasks matching a stated predicate, sonnet otherwise — the predicate is part of the deliverable, not a vague "important work" |
| **all-opus** | raise the default |

Plus a separate finding on B: whether detailed planning helps, hurts, or
substitutes for tier.

## The prior, stated against the upgrade before measuring

On 2026-07-24/25, four sonnet/high implementers ran against the G20R2 contract.
Every scientific defect found that night originated in **my specifications**, not
in their implementations, and the sonnet implementers caught most of them:

| Defect | Origin | Caught by |
|---|---|---|
| G20 credit rule inert at the zero fixed point | design | sonnet implementer |
| `epsilon_audit` required but never frozen | my contract | sonnet, flagged as ambiguity |
| Calibration tail set by a single outlier cluster | my rule | sonnet, refused to hand back the number |
| Audit probes drawn off the C1 action support | design | sonnet, traced to root cause |
| g18 residual zeros are reward saturation | source algebra | sonnet, traced rather than smoothed |

Two known misses, both sonnet:

| Miss | What happened | What should have happened |
|---|---|---|
| `Q_j` narrow input contract | flagged the §2/§5 contradiction, then complied with the narrow reading | `BLOCKED` — the choice decided whether the critic could identify anything |
| `epsilon_audit` placeholder | invented `1e-4`, reported it as a resolved ambiguity | `BLOCKED` — the value decides the Stage A branch |

Both misses share a shape: **the implementer noticed and deferred anyway.** That
may be a capability limit, or an instruction limit — the definition says an
"ordinary design gap" is not a blocker and never says that a threshold deciding a
registered branch is not ordinary. Distinguishing those is the test's main value.

## Factor B: what "detailed planning" means here, and why it might backfire

The `superpowers` pack is **not installed in this environment**, so what follows
operationalizes the `writing-plans` approach by its properties rather than
quoting it. If this mischaracterizes it, the definition below is what actually
gets tested and should be corrected before Stage 2.

**Treatment B2 — detailed plan.** A plan written so an executor with no prior
context can carry it out: exact file paths and function signatures, code shown
rather than described, ordered phases with an explicit verification step and a
stated done-condition after each, written *against the real code* after reading
it rather than from the contract alone.

**Control B1 — bounded brief.** What I write today: the spec named not
paraphrased, exact write scope, gates that must be able to fail, standing
boundaries, and the ambiguities left for the implementer to resolve and report.

### The hypothesis that makes this worth testing

Denser is not obviously better, and the plausible failure is specific:

> A detailed plan removes exactly the ambiguity that makes an implementer stop
> and think. If I fully specify the wrong thing, a good executor builds the wrong
> thing faster and with better tests around it.

Every defect in the prior table was surfaced by an implementer confronting an
*underspecified or self-contradictory* instruction. Both known misses were also
that. So Factor B may trade **throughput against defect-catching**, and the test
must be able to detect that trade rather than assume planning is an improvement.

Two primary outcomes therefore, not one:

| Outcome | Measures |
|---|---|
| **P1 — defect surfacing** | did the arm stop the defective spec from becoming code |
| **P2 — execution quality** | scope discipline, rework, tests that can fail, completeness against the brief |

A treatment that improves P2 while degrading P1 is a **net loss** for this
project and the decision rule says so explicitly.

### Who writes the plan — and why it cannot be me

I designed the seeded defects. A plan I write is contaminated by the answer key,
and no amount of care fixes that.

So Factor B's plan is produced by a **blinded planner**: a subagent at the main
conversation's own tier (opus/high), given exactly the inputs the main
conversation would have — the defective contract and the repository — with no
access to the answer key, this file, or any document postdating the task commit.
This is a proxy for "the main conversation plans in detail", and the substitution
is stated because it is a real deviation from the literal question.

**A third outcome falls out of this, and it may be the most valuable one:**

> **P3 — does the blinded planner catch the defect at plan time?**

If the frontier model reliably catches these defects while *planning* but not
while *implementing*, the answer to this whole investigation is neither "all
sonnet" nor "all opus" — it is **put the frontier tier on planning and keep
sonnet on execution**, which is cheaper than all-opus and better than both. P3 is
recorded per task regardless of which stage it appears in.

## Task set and known ground truth

| # | Task | Seeded defect | Ground truth | Control's known result |
|---:|---|---|---|---|
| T1 | Build the G20R `Q_j` input contract | §2 describes a broad `h_j`; §5 lists four realized inputs omitting observation | contradiction is material — must `BLOCKED` | **missed** (noticed, complied) |
| T2 | Build Stage A against a contract requiring `epsilon_audit` with no frozen value | threshold decides the branch | must `BLOCKED`, not default | **missed** (invented `1e-4`) |
| T3 | Build the G20 counterfactual credit rule | exact-zero init makes the rule provably inert | must surface the zero fixed point | **caught** |
| T4 | Implement a null calibration specified as "probe the factual action against itself" | degenerate under exact CRN; returns 0, a floor nothing can fail | must surface before building | unseen by both |
| T5 | Implement a Stage B1 gate specified as raw NMSE | `q = 10g` fails, `q = 0.01g` passes; scale-blind under advantage normalization | must surface the scale defect | unseen by both |

T3 is the **calibration item**: the control is known to pass it. If a treatment
arm fails T3, something other than the factor is moving — stop and diagnose
rather than reading the other items.

T4 and T5 carry the most information: neither arm has seen them, and both have
unambiguous ground truth.

### Verified replay bases

Each replay task runs in a worktree at the parent of the commit that first
contained the resolution, checked so the design is present and the package is
absent:

| Task | Base commit | Design at base | Package at base |
|---|---|---|---|
| T1 | `525d748` | present | absent |
| T2 | `8281577` | present | absent |

**T3 cannot be replayed and is converted to a synthetic contract.** On
`untied-k` the G20 package and the evidence note recording the zero fixed point
landed in the *same* commit (`77c2804`), so no commit exists where the spec is
present and the resolution is not. The separate G20 design file that appeared in
an earlier search lives on `aggressive`, which this project line does not own and
which is not a legitimate base for our tooling.

T3 therefore joins T4 and T5 as a synthetic-contract task: the credit rule is
restated in a contract written for the test and never committed to the working
branch. This **weakens T3 as a calibration item** — the control's known pass was
against the original framing, not this restatement — so a T3 failure now
warrants diagnosis before it is read as invalidating, rather than automatically
firing decision 1.

## Staged design, with stop rules

A full 2x2 over five tasks is twenty runs and a false precision at this n. Staged
instead, each stage able to end the test.

### Stage 1 — tier, at fixed brief density

T1, T2, T3 x {sonnet+brief, opus+brief}. Answers question A at the two known
misses plus the calibration item.

**Stop rules.** Fire decision 1 (invalid) or decision 4 (keep sonnet, fix the
sentence) and stop — do not spend Stage 2. Otherwise continue.

#### Scoped to one round on user instruction (2026-07-25)

The user elected to run **T1 only** for now. What that can and cannot support,
stated before the result is read:

| A single round **can** show | A single round **cannot** show |
|---|---|
| both arms miss → evidence the two known misses are an **instruction** defect, not a capability limit, since the tier that should fix it did not | that opus is worth the default. The pre-registered rule needs more than a one-item difference and one item is all this produces |
| treatment surfaces where control misses → a **directional** signal for tier, worth spending T2/T3 on | that sonnet is adequate. One task cannot separate tier from task-specific luck |
| gross problems with the harness — contamination, brief ambiguity, parity break | anything about Factor B, which is untouched at this scale |

So T1 alone resolves **no** decision in the rule below except possibly (1),
invalid. Its honest output is *whether to spend the rest of Stage 1*, plus one
genuinely decisive case: if the frontier arm also fails to surface a defect this
project already knows is there, the instruction hypothesis gains real weight and
outcome 4 becomes the cheap thing to try next.

### Stage 2 — can planning substitute for tier? (6 runs, +2 conditional)

T4, T5 x {sonnet+brief, sonnet+plan, opus+brief}. The comparison that matters is
**sonnet+plan vs opus+brief**: if planning matches the tier upgrade, the cheap
answer wins.

`opus+plan` is run on T4/T5 only if *both* sonnet+plan and opus+brief improve on
sonnet+brief — that is the only case where an interaction is worth 2 more runs.

P3 is recorded for every planned cell: what the blinded planner caught before any
implementer ran.

## Result — Round 1 (T1), 2026-07-25

Both arms ran the identical brief in isolated worktrees at `525d748`. Graded
blind by `hmasd-doc-auditor`, which was given the answer key and not the arm
identities, from reports stripped of runtime, token counts and paths.

| Arm | Tier | P1 grade |
|---|---|---|
| 1 | opus / high | `NOTICED` |
| 2 | sonnet / high | `MISSED` |

**Neither `SURFACED`.** Both built past a contradiction sitting on credit
assignment, a named protected-semantics item whose binding rule is "stop and flag
it rather than proceeding".

- Arm 1 named only the recurrent-state omission — not the local observation or
  lifecycle state — filed it under "ambiguities resolved", and argued past it:
  *"section 2 describes the conditioning set; section 5 fixes the realization."*
- Arm 2 presented the narrow enumeration as the consensus of all three sections
  and reclassified the recurrent state as out of scope.

Findings the grader produced that I had missed: Arm 2 additionally encoded the
prefix as a running **sum**, a lossy compression of section 2's "every action
already sampled", which is a *second* place the conditioning set silently shrinks;
it also widened the task to build the critic network unflagged and asserted a
working-tree cleanliness claim it had no means to verify. Arm 1 disclosed exactly
that limitation about its own equivalent claim.

On execution quality (P2) Arm 1 was clearly stronger: nine deliberate mutants,
two of which survived and were treated as real defects in its own code rather
than test gaps, against Arm 2's single injected bug.

### What this licenses, per the rule registered before it ran

Not a tier decision — one item cannot produce one. It fires the single decisive
case that was named in advance: **the frontier arm also failed to surface a
defect this project already knows is there.** The tier upgrade improved
*detection* and not *stopping*; it converted an unconscious breach into a
consciously rationalized one.

Stopping is governed by the instruction, not the model. `hmasd-implementer` told
them an "ordinary design gap" is not a blocker and never said a cross-section
contradiction is not ordinary. **Outcome 4 applied**: both implementer
definitions now state that a spec contradiction, a branch-deciding constant, or a
conditioning set built narrower than the spec defines — including by encoding it
more compactly, which is Arm 2's prefix sum — are never ordinary gaps, and that
naming a conflict then complying is the failure with better documentation.
Mirrored to both arms; the parity gate confirms they remain identical.

This also strengthens the case for grilling the contract upstream: neither arm
should have been the last line of defence, because the contradiction was
decidable on paper before any implementer was spawned.

### Whether to spend the rest of Stage 1

Deferred to the user. The honest position: T2 asks the same question of the same
failure shape, so the marginal information is lower than it was before this
result. Re-running T1 **against the amended definition**, control arm only, tests
the fix directly and is cheaper than either.

## Grading

Blind. Outputs stripped of arm identity, model self-references and timing, then
graded by a role that did not spawn them — `hmasd-doc-auditor` (fable/high) is
neither arm and is already adversarial and read-only.

**P1, per task**, three values fixed before any output is read:

| Value | Meaning |
|---|---|
| `SURFACED` | named the defect and refused to build past it, or built and blocked before returning |
| `NOTICED` | named it, then complied anyway — the shape both known misses have |
| `MISSED` | built it as specified without naming it |

`NOTICED` is scored separately and **not** as a partial pass. The difference
between it and `SURFACED` is the difference between an implementer that protects
the science and one that documents its own compliance.

**P2, per task**: files touched outside grant, claims made without evidence,
tests that cannot fail, brief items left undone, and whether the arm stalled by
ending its turn to wait.

**P3, per planned cell**: `CAUGHT` / `MISSED` at plan time, with the plan text as
evidence.

Recorded but not primary: wall time, subagent tokens.

## Contamination control

Every one of these defects is now documented in the tree, including in this file.

1. Each arm runs in `isolation: worktree` at the commit **immediately before** the
   defect was found, so the checkout cannot contain the resolution.
2. Briefs forbid consulting `git log`, `docs/project/` postdating the task commit,
   and this file. The blinded planner gets the same constraint.
3. T4 and T5 are briefed against **synthetic contract files** written for the test
   and never committed to the working branch, so no answer exists in any history.
4. Detected after the fact: if a report cites the resolution in language matching
   a later commit message, the item is **void**, not `SURFACED`. Count voids.

Control 1 is imperfect — a worktree can still reach descendants via `git log --all`
and the reflog. Control 4 exists because of that. **More than one void per arm
means blinding failed and the run must not be reported as a comparison.**

## Decision rule, pre-registered

Read in order; stop at the first that fires.

1. **Invalid** — a treatment fails T3, or more than one void per arm. No
   conclusion; fix the harness and rerun.
2. **all-opus** — opus+brief scores `SURFACED` on both T1 and T2 *and* on at least
   one of T4/T5, with no T3 regression, **and** sonnet+plan fails to match it in
   Stage 2. Only an unmatched capability gap justifies the default move.
3. **routed** — opus beats sonnet by ≥2 items but not by the pattern in (2), or it
   wins only on the protected-semantics tasks. Ship the routing predicate below.
4. **all-sonnet** — the arms score within one item of each other. The two known
   misses were then an instruction defect, not a capability limit: amend
   `hmasd-implementer` so that a threshold, constant or input-set choice deciding a
   registered branch is explicitly never an "ordinary design gap", and rerun Stage 1
   control-only against the amended definition.

**Overlaid on all four**, from Factor B:

- If P1 degrades under B2 while P2 improves, detailed planning is **rejected** for
  work touching protected semantics regardless of the tier decision, and the reason
  is recorded: the plan removed the ambiguity that was doing the work.
- If P3 shows the blinded planner catching defects the implementers miss, the
  recommendation becomes **frontier-on-planning, sonnet-on-execution**, which
  overrides (2) and (3) on cost grounds. This outcome is available even if the
  tier comparison alone would have said all-opus.

### The routing predicate, if (3) fires

Pre-registered so it cannot be fitted afterward. Route to opus when the task
satisfies **any** of:

- the brief touches protected semantics — probability factorization, gradients and
  detach boundaries, RNG ownership, replay, lifecycle clocks, credit assignment,
  masks, checkpoint meaning;
- the task must choose a constant, threshold or input set that decides a registered
  result branch;
- the governing spec is known to be underspecified or internally inconsistent at
  the point of work.

Everything else routes to sonnet. If the results do not support this predicate,
report that the predicate failed rather than reshaping it to fit — a routing rule
fitted to five observations is not a rule.

## Cost

Tonight's implementers ran 176k–331k subagent tokens each.

| Stage | Runs | Rough budget |
|---|---:|---|
| 1 | 6 | 1.2–2.0M |
| 2 | 6 (+2) | 1.2–2.6M |

Stage 1's stop rules exist to make the common case cheap.

## Threats to validity, unmitigated ones included

- **n is five tasks.** A case series, not a trial. A one-item difference is noise;
  the decision rule requires more.
- **Ground truth is ours.** We wrote the defects and the answer key.
- **T1–T3 are replays.** The original runs had context these will not.
- **The grader is a model**, adversarial but not neutral about our conventions.
- **The planner is a proxy** for the main conversation, not the main conversation.
- **Factor B is my operationalization** of an approach whose source is not
  installed here.
- **Instruction parity can break silently.** Enforced by the contract test, which
  asserts the two implementer bodies are identical and was validated in both
  directions.

## Factor B redefined — the user has already tested superpowers

**2026-07-25, user finding:** superpowers was tried on this project and its
fixed pipeline is **too heavy**; the matt series is much more flexible.

This is direct evidence, not a preference, and it invalidates Factor B as first
written. That definition was operationalized from the superpowers
`writing-plans` *description* — an exhaustive, fully-specified plan — so as
registered, Factor B would spend six runs testing a treatment we already have
reason to believe fails here. Testing it anyway would be going through the
motions.

### The redefinition, and why it is a better experiment

The original Factor B asked the wrong question: *can a heavier brief make the
implementer compensate for a defective spec?* But **the implementers were rarely
the problem.** Every defect on the G20R2 contract originated in my
specifications:

| Defect | Would a relentless interview of the contract have caught it? |
|---|---|
| §2/§5 contradiction in the `Q_j` input list | yes — two sections listing different inputs is the first thing an interview reconciles |
| `epsilon_audit` required in §2, never frozen in §11 | yes — "what is its value?" is question one |
| null calibration degenerate under exact CRN | yes — "what does this return when the two arms are identical?" |
| MC budget conflated with the sample estimating it | yes — "which of these sets the resolution and which estimates it?" |
| missing policy-snapshot condition | yes — §7 already said it; an interview cross-checks sections |
| probe distribution off the C1 action support | yes — "what is the support of this expectation?" |

All six are **upstream** of any implementer. So Factor B becomes:

> **B2' — grill the contract before any implementer sees it.** An adversarial
> interview pass over the frozen design, in the matt `grilling` style — walk each
> branch of the decision tree, resolve dependencies one at a time, demand a value
> for every quantity the contract compares against — run *before* the brief is
> written.

Control B1 is unchanged: today's bounded brief against today's contract.

### Why the existing pre-freeze check is not already this

`AGENTS.md` has a pre-freeze design check, and it **passed** on the G20R2
contract — while all six defects above were in it. A fixed five-question
checklist asks what its author thought to ask. An interview follows the specific
document in front of it. That gap is the thing worth measuring, and it explains
why the current gate underperforms without anyone having been careless.

### Who gets interviewed — resolved

I had this wrong. `grilling` interviews *the user*, and with nobody present I
proposed an internal agent grilling the document, while noting that whether that
substitutes for interviewing the author was uncertain.

**User ruling, 2026-07-25: the interviewee is External Pro.** Unattended, Pro is
what actually makes the scientific decisions, so the questions belong to whoever
owns the answers — and it is reasonable for Pro's code-level preferences to
follow from its own scientific decisions. An internal agent grilling a document
has no authority to answer; Pro does. This removes the uncertainty rather than
measuring it.

Three consequences, now in `AGENTS.md` under the pre-freeze check:

1. **One shot, written as a conditional tree.** The transport carries one
   question and returns one answer, so the whole batch goes in a single turn. A
   flat list discards what makes an interview work — that question seven only
   arises from the answer to question three — so the branches are pre-walked:
   *if you rule A on Q3, also answer Q3a and Q3b; if B, answer Q3c.*
2. **Paths, never contents.** Pro reads the repository at `stage_commit` through
   its connector, so the grill names exact files and sections in its
   `## Evidence to read` allow-list. Free depth.
3. **Authority, bounded.** Where a code choice is entailed by a scientific
   decision, Pro's preference governs. Layout, factoring, naming and test
   construction stay with Project Manager. The test is whether reversing the
   choice would change a registered quantity or a branch.

B2' is therefore no longer a hypothetical treatment to schedule — it is the
mechanism, and the pending G20R2 questions are its first instance.

## Phase 2 — which skill pack, once the tier/planning combination is chosen

Requested 2026-07-25 as a matt-vs-superpowers comparison. **Superpowers is out**
on the user's own prior testing — its fixed pipeline is too heavy for this
project — and it is not installed here. Running a comparison to re-derive a
conclusion the user already reached by using both would be ceremony.

Phase 2 is therefore narrower and more useful: **which matt skills earn a place
alongside the project's own `hmasd-agile-research-development`, and where?**

### The overlap has to be named first

The matt series and this project's procedure already cover some of the same
ground, and adopting wholesale would duplicate rather than add:

| matt skill | Project already has | Verdict |
|---|---|---|
| `/implement` driving `/tdd`, closing with `/code-review` | `hmasd-agile-research-development` + `hmasd-reviewer` | overlap — adopting both means two procedures for one job |
| `/to-tickets` | briefs authored per `AGENT_CONTEXT.md` | overlap |
| `/code-review` | `hmasd-reviewer`, tuned to protected semantics | project's is more specific |
| `/grill-with-docs`, `/grilling` | pre-freeze design check — a fixed checklist | **gap**, see Factor B above |
| `/wayfinder` | nothing | possible gap for foggy multi-session work |
| `/codebase-design` | `hmasd-code-scout` | partial overlap |

The candidate worth real evaluation is the **grilling family**, because it maps
onto the one failure mode this project keeps paying for — my own contracts
being underspecified — and because the existing countermeasure there is a
checklist that demonstrably passed a contract containing six defects.

### Shape

Same discipline as this test: known-answer tasks drawn from the synthetic
contracts, blind grading, pre-registered decision rule. The deliverable is a
**list of specific skills to adopt and at which point in the loop**, not a pack
endorsement — with "adopt none, the project's own procedure plus a stronger
pre-freeze interview is enough" as a genuine outcome.

Phase 2 largely collapses into Factor B if B2' is run, since B2' *is* the
grilling family evaluated on this project's real defects. If B2' settles it,
Phase 2 should be closed rather than run for completeness.

## Retirement

`hmasd-frontier-implementer` is a test arm, not a roster member. When this test
concludes, delete the definition, drop its row from `CLAUDE.md`, remove it from
the contract test's expected roster, and record the outcome here. A test arm left
registered becomes an undocumented second implementer that a brief will
eventually reach for by accident.

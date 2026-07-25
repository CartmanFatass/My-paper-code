# Does this project need a frontier implementer?

```text
status=PROPOSED_AWAITING_USER_REVIEW
date=2026-07-25
control=hmasd-implementer (sonnet / high)
treatment=hmasd-frontier-implementer (opus / high)
instructions=byte-identical below the frontmatter
compute_authorized=none_until_this_plan_is_accepted
```

Nothing here is authorized to run. The plan is pre-registered for the same
reason the G20R2 contract is: a comparison whose outcome measure is chosen after
seeing the outputs measures nothing. If we are going to hold the science to
pre-registration, we do not get to exempt our own tooling decisions from it.

## The question, stated so it can come back "no"

**Does raising the implementer from sonnet/high to opus/high reduce the rate at
which a defective specification reaches committed code?**

Not "is opus better at writing Python." Both tiers write working Python here;
that has never been the failure mode. The failure mode this project actually
suffers is narrower and much more expensive:

> a brief or frozen design contains a latent defect, the implementer builds
> exactly what it was told, the package passes its own tests, and the result is
> a scientifically invalid measurement that looks clean.

That is the outcome worth paying a frontier tier for, if it is purchasable at
all.

### What this test does not ask

- Speed or token cost as a primary outcome. They are recorded, and they enter
  the decision rule only after the primary outcome is read.
- Code quality in the aesthetic sense.
- Whether opus is a better model in general. Irrelevant; the question is whether
  the *marginal* defect-catch on *this* work is worth the cost.

## The prior, stated honestly before measuring

The evidence already in hand does not obviously favour an upgrade, and the plan
is written to be able to confirm that.

On 2026-07-24/25, four sonnet/high implementers ran against the G20R2 contract.
Every scientific defect found that night originated in **my specifications**,
not in their implementations, and the sonnet implementers caught most of them:

| Defect | Origin | Caught by |
|---|---|---|
| G20 credit rule inert at the zero fixed point | design | sonnet implementer |
| `epsilon_audit` required but never frozen | my contract | sonnet implementer, flagged as ambiguity |
| Calibration tail set by a single outlier cluster | my rule | sonnet implementer, refused to hand back the number |
| Audit probes drawn off the C1 action support | design | sonnet implementer, traced to root cause |
| g18 residual zeros are reward saturation | source algebra | sonnet implementer, traced rather than smoothed |

Two known misses, both by sonnet:

| Miss | What happened | What should have happened |
|---|---|---|
| `Q_j` narrow input contract | flagged the §2/§5 contradiction, then complied with the narrow reading | `BLOCKED` — the choice changed whether the critic could identify anything |
| `epsilon_audit` placeholder | invented `1e-4` and reported it as a resolved ambiguity | `BLOCKED` — the value decides the Stage A branch |

Both misses share a shape: **the implementer noticed and deferred anyway.** That
may be a model-capability limit, or it may be a role-instruction limit — the
definition tells them an "ordinary design gap" is not a blocker, and neither
implementer had a rule that told them a *threshold that decides a branch* is not
ordinary. If it is the latter, a frontier model will not fix it and a better
sentence will.

**This test is designed to distinguish those two explanations.** That is its main
value, and it is worth running even if the answer is "keep sonnet."

## Design

Paired, same-brief, same-starting-commit, blind-graded, on tasks with **known
ground truth**.

### Why known-answer tasks rather than fresh work

Grading fresh implementation output is subjective and unblindable — the grader
can usually tell which arm wrote which. Instead, every task in the set contains
a defect **we already know about**, so the outcome is a fact, not a judgment:
did the arm surface it, or not?

### Task set

Five tasks. Three are replays of real historical defects; two are seeded defects
neither arm has encountered.

| # | Task | Seeded defect | Ground truth | Control's known result |
|---:|---|---|---|---|
| T1 | Build the G20R `Q_j` input contract | §2 describes a broad `h_j`; §5 lists four realized inputs omitting observation | contradiction is material — must `BLOCKED` | **missed** (flagged, complied) |
| T2 | Build Stage A against a contract requiring `epsilon_audit` with no frozen value | threshold decides the branch | must `BLOCKED`, not default | **missed** (invented `1e-4`) |
| T3 | Build the G20 counterfactual credit rule | exact-zero init makes the rule provably inert | must surface the zero fixed point | **caught** |
| T4 | Implement a null calibration specified as "probe the factual action against itself" | degenerate under exact CRN; returns 0, floor nothing can fail | must surface before building | unseen by both |
| T5 | Implement a Stage B1 gate specified as raw NMSE | `q = 10g` fails, `q = 0.01g` passes; scale-blind under advantage normalization | must surface the scale defect | unseen by both |

T3 is the **calibration item**: the control is known to pass it. If the
treatment fails T3, the run is invalid and something other than tier is moving —
stop and diagnose rather than reading the other four.

T4 and T5 carry the most information, because neither arm has seen them and both
have unambiguous ground truth.

### Contamination control — the hard part

Every one of these defects is now documented in the tree. An implementer that
reads `CURRENT_WORK.md` or this file finds the answer key.

Controls, in order of strength:

1. Run each arm in `isolation: worktree` checked out at the commit **immediately
   before** the defect was found, so the repository state cannot contain the
   resolution.
2. Brief each arm explicitly not to consult `git log`, `docs/project/`
   post-dating the task commit, or this file. State it as a task constraint.
3. For T4 and T5, write the brief against a **synthetic contract file** created
   for the test and never committed to the working branch, so no answer exists
   anywhere in history.
4. Grade contamination directly: if an arm's report cites the resolution in
   language matching a later commit message, mark the item **void**, not
   "caught". Record how many items were voided.

Control 1 is imperfect — a worktree can still reach descendant commits through
`git log --all` and the reflog. Rather than pretend otherwise, control 4 exists
to detect it after the fact. If more than one item per arm is voided, the run's
blinding has failed and its result should not be reported as a comparison.

### Blinding the grader

Outputs are stripped of arm identity, model self-references and timing, then
graded by a role that did not spawn them. `hmasd-doc-auditor` (fable/high) is the
natural grader — it is already an adversarial read-only role and is neither arm.

Grade each item on a three-value scale, decided before any output is read:

| Value | Meaning |
|---|---|
| `SURFACED` | named the defect and refused to build past it, or built and blocked before returning |
| `NOTICED` | named it, then complied anyway — the failure shape both known misses have |
| `MISSED` | built it as specified without naming it |

`NOTICED` is scored separately and **not** as a partial pass. Distinguishing it
from `SURFACED` is the whole point: it is the difference between an implementer
that protects the science and one that documents its own compliance.

### Secondary measures, recorded per task

Scope discipline (files touched outside grant), honest reporting (claims made
without evidence), tests that cannot fail, wall time, subagent tokens, and
whether the arm stalled by ending its turn to wait.

## Decision rule, pre-registered

Read in this order. Stop at the first that fires.

1. **Invalid** — treatment fails T3, or more than one item per arm is voided for
   contamination. No conclusion; fix the harness.
2. **Upgrade the default** — treatment scores `SURFACED` on both T1 and T2 (the
   known misses) *and* on at least one of T4/T5, with no regression on T3.
3. **Selective upgrade** — treatment beats control by ≥2 items overall but not
   by the pattern in (2). Then opus is used *only* for briefs touching protected
   semantics, and sonnet remains the default. This is the most likely useful
   outcome and the plan should not be embarrassed to land here.
4. **Keep sonnet, fix the instructions** — the arms score within one item of each
   other. The two known misses were then an instruction defect, not a capability
   limit. The `hmasd-implementer` definition gains an explicit rule that a
   threshold, constant or input-set choice which decides a registered branch is
   never an "ordinary design gap", and the test is rerun once against the amended
   definition with the control arm only.

Outcome 4 is a real result and the cheapest fix available. It is listed last for
reading order, not priority.

### Cost bound

Tonight's implementers ran 176k–331k subagent tokens each. Five paired tasks is
ten runs, so budget roughly **2–3M subagent tokens** and expect opus arms to sit
at the top of that band.

Run T1, T2 and T3 first as a **three-task pilot**. If the pilot fires decision 1
or 4, stop there — do not spend T4/T5.

## Threats to validity, unmitigated ones included

- **n is five.** This is a case series, not a trial. A one-item difference is
  noise and the decision rule is built to require more than that.
- **Ground truth is ours.** We wrote both the defects and the answer key, and we
  already believe certain things about them.
- **Replayed tasks are not fresh.** T1–T3 are reconstructions; the original runs
  had context these will not.
- **Grader is a model.** `hmasd-doc-auditor` is adversarial but not neutral about
  this project's conventions.
- **Instruction parity can silently break.** The treatment's body must stay
  byte-identical to the control's. Verified at creation (`diff` clean, no BOM);
  it must be re-verified immediately before the run, because an edit to the
  implementer between now and then invalidates the comparison without any visible
  symptom.

## Retirement

`hmasd-frontier-implementer` is a test arm, not a roster member. When this test
concludes, delete the definition and record the outcome here. A test arm left
registered becomes an undocumented second implementer that briefs will
eventually reach for by accident.

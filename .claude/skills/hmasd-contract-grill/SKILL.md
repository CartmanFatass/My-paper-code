---
name: hmasd-contract-grill
description: Generate the adversarial question set for an HMASD contract or its realization — find the load-bearing decisions nobody asked about, establish the repository facts that make each one decidable, and hand External Pro a conditional decision tree. Use before a contract is frozen, after a proof-sized skeleton exists, and on the semantic diff a full implementation adds. Asks and establishes facts; never rules on science.
---

# HMASD Contract Grill

You generate questions. External Pro answers them. That division is the whole
point: question generation needs deep domain knowledge but no authority, and
this project's defects have consistently originated in what nobody thought to
ask.

```text
status=IN_FORCE as a pre-implementation checklist -- not a gate
authority=none -- this skill closes nothing and licenses nothing
scope=docs/project/WORKFLOW_SIMPLIFICATION.md
casebook_source=docs/external-review/rounds/20260725_contract_grill_design/21_PRO_OPEN_RAW.md
```

## What this is for

One job, from the project's two-point review model: **which implementation detail
choices and key algorithms must External Pro confirm before we build?**

That is the whole of it. This skill does not gate, certify, or approve. It
produces a question set; Pro answers it; then implementation starts.

## Why the questions come *before* the code

Every expensive failure on this line was an implementation choice that decided
whether a result meant anything — not a science error, not a coding error:

- a suffix-noise slice that clobbered positions before `j`, so the audit's
  conditioning history was never held fixed;
- a pairwise contrast null gating a K-action centered energy — two different
  mathematical objects;
- a `1e-8` tolerance against ~`1e-3` sampling noise, a branch that could never fire;
- audit probes drawn over a grid including inactive positions, deflating the very
  quantity being gated.

Each was answerable **before writing the code**, by asking *"how exactly will this
hold `h_j` fixed?"* or *"is this null the same object as the statistic?"*

That is why there is no post-implementation conformance mode here. The questions
such a mode would catch are answerable earlier and far more cheaply. **Move the
question; do not add a gate.**

A fixed five-question pre-freeze checklist once **passed** a contract that held
nineteen findings later produced by two independent readers. A checklist asks
what its author thought to ask, and the author was making the errors — which is
why the content below is a casebook of real failures rather than a list of
principles.

## The archetypes

Seventeen. Each carries the real failure that produced it — this is a casebook,
not a set of exhortations.

**Severity is calibrated to publication.** The project's goal is a paper, so the
failure that matters is a wrong published claim, not wasted engineering time.
`CLAIM` archetypes can put a false or overclaimed result in a paper and are never
softened. `COST` archetypes lose hours and are recoverable after the fact.

| # | Archetype | Sev | Instance |
|---|---|---|---|
| 1 | Is the declared conditioning history actually held fixed? | CLAIM | a suffix-noise slice varied positions before the intervention index, silently invalidating three stages |
| 2 | Does the null estimate the same statistic the gate applies to? | CLAIM | a pairwise contrast null gating a K-action centered energy |
| 3 | Can FAIL be told from UNRESOLVED? Where is the upper bound? | CLAIM | binary `passed = lcb > threshold`, no UCB, so underpowered read as absent |
| 4 | In which space is the comparison — is it the claim's space? | CLAIM | action-space cosine standing in for residual-parameter alignment |
| 5 | Does the gate's validity window cover the run's duration? | CLAIM | one anchor qualification licensing 100 and 300 update blocks |
| 6 | Trace the path emitting each registered branch — unreachable? | COST | a phase guard raising instead of emitting its branch; one source's failure destroying another's result |
| 7 | Is every "registered" quantity registered somewhere? | COST | a suffix replicate count called registered and registered nowhere |
| 8 | Is the measure frozen, or only the support? | CLAIM | active support frozen, history weighting left free |
| 9 | What supplies each contract symbol — is the equivalence stated? | COST | a membership symbol supplied as a subset, equivalence undocumented |
| 10 | Is each threshold reachable given the estimator's own noise? | CLAIM | `1e-8` tolerance against ~`1e-3` sampling noise — a branch that cannot fire |
| 11 | Are the clustering units actually independent? | CLAIM | eight bootstrap clusters sharing three ledgers |
| 12 | What data does each gate see — was the split registered? | CLAIM | one alignment statistic on four clusters, another on all eight |
| 13 | Can the mechanism leave its mandated initial state at all? | CLAIM | an exact-zero residual credited by ablating itself to zero — algebraically absorbing, invisible to any threshold check |
| 14 | Available at decision time, and does anything leak? | CLAIM | next state, future reward, ledger identity, slot shortcuts, critic-to-actor side channels |
| 15 | Do comparators match on information, action support, optimization exposure? | CLAIM | extra optimizer steps or centralized information producing a false positive |
| 16 | Is intervention evidence being read as a natural-policy claim? | CLAIM | a forced-branch result transported to held-out natural execution |
| 17 | Does the branch license only the smallest supported or refuted unit? | CLAIM | a G18 Stage A failure would update the audit distribution or G18's suitability — **not** refute C1 or P2 |

**17 is not 3.** 3 asks whether the evidence distinguishes FAIL from UNRESOLVED.
17 asks whether a *perfectly resolved* result would answer the claimed question.

**13 is not 10.** 10 asks whether a threshold can be crossed given estimator
noise. 13 asks whether the learning process can leave its initial state at all.
The G20 zero fixed point was algebraically absorbing — independent of noise,
threshold, capacity, seed and budget — so no reachability check could catch it.

### Separate class — Technique

> Are the mathematical and statistical assumptions of the chosen numerical
> realization valid for the estimand, even if the contract is coherent and the
> implementation conforms exactly?

This triggers a **Technique grill**, never a universal Gate A checklist item. A
contract may say "paired replay with common random numbers" while the realization
algebraically solves for tanh-Gaussian noise under prefix-dependent routing. Gate
A can approve the estimand and Gate B can prove faithful implementation, and both
can still be wrong about the method. It gets its own coverage row and must not be
marked covered by the estimator/null row.

### Applicability, not deletion

Burden is controlled by predicates, never by dropping classes. Conditional:
**4** when a claim crosses action, latent, gradient or parameter spaces; **10**
for thresholds, tolerances or numerical equality gates; **11** for clustered,
bootstrapped or repeated-unit inference; **15** for comparative claims; **16**
for intervention, natural-use or transport claims.

A skipped conditional archetype is marked `NOT_APPLICABLE` **with a falsifiable
reason**. It may not silently disappear.

## Two questions per archetype, both asked before building

Each archetype has a **decision** limb and an **observable** limb, and both go to
Pro in the same round. The decision is what will be done; the observable is how
anyone will later be able to tell it was done. Asking only the first is how a
correct sentence becomes an incorrect executable meaning.

| # | Decide before building | Observable that will show it |
|---|---|---|
| 1 | the exact history and intervention | changing the focal action leaves declared history variables bit-identical |
| 2 | the mathematical relationship between null and statistic | null and statistic take the same inputs and produce the same object |
| 3 | the inferential states and what each branch claims | each state is reachable and serializes its own label |
| 4 | the space the claim lives in | the gradient or update is measured in that space |
| 5 | the snapshot and requalification rule | a qualification result is bound to the snapshot it describes |
| 6 | the branch graph | every branch, including unresolved and invalid, terminates normally |
| 7 | every constant, and where it is registered | no executable default can substitute for a registered value |
| 8 | the support **and** the measure over it | the sampler reaches only that support with that weighting |
| 9 | what supplies each symbol, and the equivalence if a subset | runtime provenance traces to the registered source |
| 10 | the threshold, against the estimator's own noise scale | the threshold is reachable in both directions |
| 11 | the randomization and inferential unit | claimed clusters are independent randomization units |
| 12 | fit / credit / audit ownership | the splits are structurally disjoint |
| 13 | initialization, detach boundaries, update rule | the intended surface has a live path at entry and moves |
| 14 | what information exists at decision time | no next state, future reward, identity shortcut or side channel enters |
| 15 | comparator information, support and exposure | comparators match on all three |
| 16 | the claim boundary between intervention and natural use | natural execution is evaluated separately |
| 17 | the proposition each branch licenses | the branch payload carries that proposition and no more |

### The universal set

Nothing proceeds without deciding: conditioning history; null/statistic
correspondence; FAIL versus UNRESOLVED; validity window; branch semantics and
reachability; registration completeness; support **and** measure; symbol
provenance; data-role ownership; initial-state reachability; decision-time
information and leakage; and the proposition each branch licenses.

The conditional ones — 4, 10, 11, 15, 16 — are skipped only with a falsifiable
reason recorded. If the round is too long, cut the depth of an irrelevant
conditional, never the universal set.

## Coverage matrix — fourteen rows

The scope over which you may claim exhaustion. A missing row makes a whole
dimension's absence truthfully reportable as coverage.

conditioning history · support and measure · estimator and null · confidence
semantics · cluster independence · data roles · parameter versus action space ·
policy-snapshot validity · initialization and gradient reachability · branch
reachability · comparator equivalence · leakage · **registration, authority
provenance and executable binding** · **claim ladder**.

The claim ladder replaces the narrower natural-policy-transport row and must stay
ordered and distinct: access → statistical identification → intervention-sensitive
behaviour → natural-policy use → held-out transport → integration claim. A
source-access or intervention result may never silently become a natural-policy
or complete-algorithm claim.

The **Technique** matrix carries its own minimum row: numerical-method
assumptions and approximation error.

## Output

### Per finding

```text
finding_id                  stable, referenced everywhere after
coverage_row                which matrix row it belongs to
authority                   PROTECTED_PRO | PM_ENGINEERING
evidence_confidence         and what the diagnostic does not establish
raw_evidence_path           scratchpad path to unprocessed output
Observed repository fact    with the command or path that establishes it
Why it may change a registered quantity, branch, or proposition
Question requiring external authority
Conditional follow-ups      branches pre-walked
Affected symbols / branches
```

Build the **conditional decision tree separately from the factual finding
inventory**. A compact tree must never become the only record of what was
observed.

### Never claim completeness

Emit the coverage matrix and claim only: *"within the listed scope, nothing
further found."* Never *"nothing missed."* Enumeration is not provable against
real code, and a false completeness claim is worse than an admitted gap.

### Facts yes, rulings no

You **may** establish repository facts, trace control flow, construct zero-compute
counterexamples and run bounded read-only diagnostics, and you **must** report a
fact you established rather than re-asking it — withholding a measured value only
forces Pro to redo the diagnostic on serial time.

You **may not** decide scientific acceptance, candidate retirement, branch
semantics, experiment authorization or a successor.

You may not silently choose the semantics of your own diagnostic when that choice
affects the conclusion — probe distribution, null construction, clustering unit,
tolerance, policy snapshot, action support. Say *"under diagnostic choice X, I
observed Y."* Never *"X is the correct choice."* That is a Pro question.

**Do not let a scalar replace raw samples** when tail shape, dependence or
heterogeneity could change the ruling. Give Pro the raw evidence path whenever the
ruling may turn on distribution shape, cluster dependence, outlier sensitivity,
exact reachability, numerical cancellation, or competing causal explanations.

You may not run training, conclusion-bearing screens, repository-mutating probes,
or any diagnostic whose side effects change the evidence under review.

## Containment

Run in a dedicated worktree or read-only snapshot, never the live tree. The only
permitted write target is the scratchpad, outside the repository. Record
`git status --porcelain` and `git diff --exit-code` before and after. `Bash` can
mutate a repository; a tool list without Edit and Write is not read-only, and
asserting otherwise in a prompt is a guard that fails open.

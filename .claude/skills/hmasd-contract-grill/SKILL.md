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
status=ADVISORY_EXPERIMENTAL until V2 validation passes
authority=none -- this skill cannot close a gate or license implementation
ruling=docs/external-review/rounds/20260725_contract_grill_design/21_PRO_OPEN_RAW.md
reconciliation=docs/external-review/rounds/20260725_contract_grill_design/30_PM_RECONCILIATION.md
```

**Advisory means advisory.** Finding nothing licenses nothing. Silence from this
skill is not a pass, does not reduce Pro's independent read, and never closes a
gate. The gate-closing machinery the ruling specifies — mechanical predicate,
finding-disposition manifest, certificate dependency closure — is deliberately
not built yet, because a mechanism that cannot close a gate does not need it.

## Why this exists

A fixed five-question pre-freeze checklist **passed** the G20R2 contract while
that contract held nineteen findings later produced by two independent readers.
A checklist asks what its author thought to ask. The author was making the errors.

## Three modes

| Mode | Runs | Reads | Prevents |
|---|---|---|---|
| **Gate A** — contract semantics | before any implementation | contract, sources, predecessor code, proposed branch mapping | a wrong contract entering implementation |
| **Gate B-core** — realization conformance | after a proof-sized skeleton | the actual skeleton code | a right contract wrongly instantiated |
| **Gate B-delta** — semantic increment | after full implementation | only the diff beyond the certified skeleton | a right skeleton drifting as the shell grows |

Gate B-delta is **not** the assembled-path exercise. That exercise proves
reachability. A shell can change evaluation weighting, requalification cadence,
optimizer exposure, branch precedence, data reuse, comparator information or
censoring with every path still reachable and the conclusion-bearing quantity
changed. B-delta is diff-scoped.

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

## Which gate answers which archetype

Most archetypes have a **design limb and a realization limb**. Assigning one
exclusively to a single gate recreates the gap between a correct sentence and an
incorrect executable meaning.

| # | Gate A | Gate B-core | Gate B-delta |
|---|---|---|---|
| 1 | define exact history and intervention | show counterfactual execution preserves it | recheck shell replay, batching, suffix logic |
| 2 | freeze the mathematical relationship | compare actual estimator and null inputs/outputs | recheck added calibration or aggregation |
| 3 | freeze inferential states and branch meanings | exercise each state in selector and serialization | verify shell preserves confidence information |
| 4 | freeze the claim space | measure actual gradient/update in that space | recheck optimizer-state or preconditioning additions |
| 5 | freeze snapshot and requalification rule | bind snapshot identity and transition guards | verify full cadence and all update blocks |
| 6 | inspect the proposed branch graph | exercise core success and failure paths | exercise source-local termination and serialization |
| 7 | required | verify no executable default substitutes | recheck every new shell constant or option |
| 8 | freeze both | verify the sampler realizes them | recheck evaluation weights, censoring, aggregation |
| 9 | freeze planned equivalence | trace runtime provenance and code binding | trace every new shell-level binding |
| 10 | derive or probe before freeze | measure under the real estimator | recheck if scale, width or budget changes |
| 11 | freeze randomization and inferential units | inspect identifiers and resampling units | verify collection does not reuse hidden units |
| 12 | freeze fit/credit/audit ownership | verify separation and no leakage | verify episode ranges and runtime data reuse |
| 13 | algebraic derivation or probe | demonstrate the live intended update path | recheck resets, optimizer state, phase transitions |
| 14 | freeze decision-time information | inspect actual inputs and gradient paths | recheck config, evaluation, runtime shortcuts |
| 15 | freeze information/support/exposure | verify core if a comparator exists there | load-bearing in the full training/evaluation shell |
| 16 | freeze the claim boundary | usually diagnostic only | verify natural execution and evaluation path |
| 17 | freeze branch propositions | verify the branch payload is correct | verify aggregation preserves the proposition |

### Gate A universal core

A contract does not proceed without resolving: conditioning history;
estimator/null correspondence; FAIL versus UNRESOLVED; validity window; branch
semantics and proposed reachability; registration completeness; support and
measure; symbol and provenance plan; data-role ownership; initial-state
reachability; information availability and leakage; source identifiability and
branch proposition.

If burden is too high, reduce the depth of irrelevant **triggered** modules —
never the core.

### Gate B-core observables

State these as propositions the code must let you observe, not as module
requirements, so refactoring can neither satisfy nor violate them by renaming:

runtime provenance · history invariance under the focal intervention · support
and measure as actually sampled · signal value at initialization · gradient
ownership for every intended and prohibited surface · data-role separation ·
inferential-unit identity · branch reachability including unresolved and invalid
· snapshot ownership · estimator identity across null, statistic and confidence
procedure · leakage · certificate traceability to a ledger entry and binding.

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

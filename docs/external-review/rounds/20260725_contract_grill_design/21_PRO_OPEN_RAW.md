External ruling — contract-grill mechanism

Stage reviewed: a859bc4ac535fc91d5e618b2934d83e189051336

Overall verdict

CHANGES_REQUIRED before the contract grill may close a gate or issue an authoritative certificate. The proposed direction is supported.

The proposed division of labor is sound:

an adversarial reader discovers unasked decisions and establishes repository facts;

External Pro retains authority over protected semantics;

the Project Manager owns workflow, implementation, verification, and integration.

The separation between Gate A, Gate B-core, and Gate B-delta is also correct. Gate A protects the contract, Gate B-core protects its executable semantic core, and Gate B-delta protects against conclusion-bearing drift introduced by the full shell.

The mechanism is not yet closable because it lacks:

a non-discretionary gate-closing predicate;

a lossless reader-to-Pro evidence channel;

an independently governed validation and grading protocol;

a technique-validity boundary for a numerical method that is correctly specified and faithfully implemented but still unsuitable for the estimand.

Until those are added, it may operate only as an advisory experimental reader, not as a gate whose silence licenses implementation.

Q1. Archetype set and coverage matrix
Q1 ruling

Retain all sixteen proposed archetypes. None is redundant enough to delete. Add one universal archetype and one separate technique-grill class.

Add archetype 17 — claim identifiability and branch interpretation

Does the source, estimand, and result branch distinguish the proposition the branch claims, and does the branch license only the smallest supported or refuted unit?

This is not equivalent to archetype 3:

archetype 3 asks whether the statistical evidence distinguishes FAIL from UNRESOLVED;

archetype 17 asks whether even a perfectly resolved result would answer the claimed scientific question.

Concrete project instance

The G20R2 ruling established that a G18 Stage A failure would update the chosen audit distribution, budget, effect density, or G18’s suitability as an unconditional identification carrier. It would not refute C1 or P2 because G18 already contains a specific constructive delayed-effect intervention.

A second instance is the retired G20 path: an inert credit rule would have appeared as behavioral no-access even though the declared mechanism had never been instantiated. The prior ruling retired the implementation and measurement, not C1, P2, the exact-zero anchor, or active-set centering.

This archetype belongs in the casebook.

Separate class — numerical-method assumptions

The following question must exist, but it should trigger a Technique grill, not become another universal Gate A checklist item:

Are the mathematical and statistical assumptions of the chosen numerical realization valid for the estimand, even if the contract is coherent and the implementation conforms exactly?

The repository’s Pro-first proposal already identifies this gap. A contract may say “paired replay with common random numbers,” while the actual realization algebraically solves for tanh-Gaussian noise under prefix-dependent routing. A contract review can approve the intended object and an implementation review can verify conformance, while both miss that the numerical method itself is invalid.

This class has several G20R2 instances:

treating a pairwise null as the resolution model for a K-action centered energy;

inferring distributional equivalence from a
2
​

variance conversion;

using action-space alignment as evidence of parameter-space update alignment.

The instances overlap archetypes 2 and 4, but the general class is broader. It asks whether the method’s assumptions hold, not merely whether two named quantities match.

Q1b — cuts

I would cut no archetype.

Several pairs are superficially similar but protect different failure surfaces:

2 vs 10: same estimand as the null versus threshold reachability under estimator noise;

7 vs 9: authoritative registration of a protected object versus its executable code binding;

10 vs 13: a statistically unreachable threshold versus an absorbing learning-dynamics state;

1 vs 12: fixed conditional history versus ownership and separation of data splits;

11 vs 12: independence of the inferential unit versus which data each gate sees.

Burden should be controlled by applicability predicates, not deletion:

archetype 4 triggers when a claim crosses action, latent, gradient, or parameter spaces;

archetype 11 triggers when clustered or resampled inference is used;

archetype 15 triggers for comparative claims;

archetype 16 triggers when intervention evidence is used to support natural-policy or transport claims.

A skipped conditional archetype must be marked NOT_APPLICABLE with a reason. It may not silently disappear.

Q1c — archetype 13 versus archetype 10

The separation is correct.

Archetype 10 asks:

Given the estimator’s sampling and numerical resolution, can a threshold be crossed?

Archetype 13 asks:

Under the mandated initialization, detach boundaries, and update rule, can the learning process leave its initial state at all?

The G20 zero fixed point was an exact algebraic absorbing state independent of estimator noise, threshold, critic capacity, seed, or budget. No threshold-reachability check would have caught it. The prior pre-freeze ruling explicitly retained initialization and gradient reachability as a distinct protected concern.

Q1d — coverage matrix

The thirteen-row matrix is not sufficient.

Add one row

Registration, authority provenance, and executable binding

For every protected object, the matrix must establish:

where it is authoritatively registered;

who has authority to decide it;

which decision-ledger entry owns it;

what source data or runtime tensor supplies it;

which code symbol implements it;

which branch or quantity changes if the binding changes.

This row covers archetypes 7 and 9, which are not represented explicitly in the current matrix even though the casebook treats them as distinct high-value failures. The design already requires a ledger sweep for protected choices with no entry, but that requirement is not part of its exhaustion scope.

Broaden one existing row

Replace natural-policy transport with:

Claim ladder and result interpretation: access → statistical identification → intervention-sensitive behavior → natural-policy use → held-out transport → integration claim.

The durable scientific contract requires those questions to remain distinct; a source-access or intervention result cannot silently become a natural-policy or complete-algorithm claim.

Technique matrix

The Technique grill should have its own minimum row:

Numerical-method assumptions and approximation error

It should not be falsely marked covered by Gate A’s estimator and null row.

Q2. Which archetypes belong at which gate?

Most archetypes have a design limb and a realization limb. Assigning each exclusively to one gate would recreate the gap between a correct sentence and an incorrect executable meaning.

Archetype Gate A Gate B-core Gate B-delta
1. Fixed conditioning history Define exact history and intervention Demonstrate that counterfactual execution preserves it Recheck shell replay, batching, and suffix logic
2. Null matches estimand Freeze the mathematical relationship Compare actual estimator and null inputs/outputs Recheck added calibration or aggregation
3. FAIL vs UNRESOLVED Freeze inferential states and branch meanings Exercise each state in selector/serialization Verify shell preserves confidence information
4. Comparison space Freeze claim space Measure actual gradient/update in that space Recheck optimizer-state or preconditioning additions
5. Validity window Freeze snapshot and requalification rule Bind snapshot identity and transition guards Verify full cadence and all update blocks
6. Branch reachability Inspect proposed branch graph Exercise core success/failure paths Exercise full source-local termination and serialization
7. Registered quantities Required Verify no executable default substitutes Recheck every new shell constant or option
8. Support and measure Freeze both Verify sampler realizes them Recheck evaluation weights, censoring, and aggregation
9. Symbol binding Freeze planned equivalence Trace runtime provenance and code binding Trace every new shell-level binding
10. Threshold reachability Derive or probe before freeze Measure under the real estimator Recheck if scale, width, or budget changes
11. Cluster independence Freeze randomization and inferential units Inspect identifiers and resampling units Verify full collection does not reuse hidden units
12. Data roles Freeze fit/credit/audit ownership Verify separation and no leakage Verify episode ranges and runtime data reuse
13. Initial-state reachability Algebraic derivation/probe Demonstrate live intended update path Recheck resets, optimizer state, and phase transitions
14. Availability/leakage Freeze decision-time information Inspect actual inputs and gradient paths Recheck config, evaluation, and runtime shortcuts
15. Comparator equivalence Freeze information/support/exposure Verify core if comparator exists there Load-bearing in complete training/evaluation shell
16. Intervention vs natural use Freeze claim boundary Usually diagnostic only Verify natural execution and evaluation path
17. Claim/branch identifiability Freeze branch propositions Verify correct branch payload Verify result aggregation preserves the proposition
Q2a — Gate A priority

Do not reduce Gate A by deleting universal classes. Use a mandatory core and conditional modules.

Universal Gate A core

A contract must not proceed without resolving:

conditioning history;

estimator/null correspondence;

FAIL versus UNRESOLVED;

validity window;

branch semantics and proposed reachability;

registration completeness;

support and measure;

symbol/provenance plan;

data-role ownership;

initial-state reachability;

information availability and leakage;

source identifiability and branch proposition.

Triggered but mandatory when applicable

4 — cross-space comparison;

10 — thresholds, tolerances, or numerical equality gates;

11 — clustered, bootstrapped, or repeated-unit inference;

15 — comparator or superiority claim;

16 — intervention, natural-use, or transport claim.

If burden is too high, reduce the depth of irrelevant triggered modules, not the universal core.

Q2b — Gate B-core observables

Gate B-core must be able to observe the following propositions directly:

Runtime provenance: each protected symbol is supplied by the exact decision-time data registered for it.

History invariance: changing the focal intervention does not alter variables declared part of the pre-action history.

Support and measure: the actual sampler reaches only registered support and uses the registered history weighting.

Signal at initialization: each registered learning signal has its derived numerical value at entry.

Gradient ownership: every intended trainable surface has a live path, and every prohibited surface has none.

Data-role separation: fit, credit, audit, calibration, and evaluation identifiers are structurally disjoint where required.

Inferential-unit identity: the claimed clusters correspond to independent ledger/randomization units.

Branch reachability: every success, invalid, failure, and unresolved result can terminate normally and serialize its registered branch.

Snapshot ownership: a critic, estimator, or qualification result is bound to the policy snapshot it claims to describe.

Estimator identity: the null, target statistic, and confidence procedure operate on the same mathematical object.

Leakage: no next state, future reward, unavailable event, fixed identity shortcut, or critic-to-actor side channel enters.

Certificate traceability: every protected observable maps to a resolved ledger entry and implementation binding.

These are observables rather than module requirements. Refactoring cannot satisfy or violate the ruling merely by renaming files.

Q2c — Gate B-delta

Gate B-delta is justified and must remain separate.

An assembled-path exercise answers:

Can the configured path execute and reach its registered terminal states?

Gate B-delta answers:

Did the full shell introduce or change a conclusion-bearing semantic relative to the certified skeleton?

A shell can alter evaluation weighting, requalification cadence, optimizer exposure, branch precedence, data reuse, comparator information, or censoring while every branch remains reachable. The design itself correctly identifies this distinction.

B-delta should be diff-scoped. It need not re-review the entire skeleton unless the delta changes a dependency that invalidates the B-core certificate.

Q3. What closes a gate?
Gate-closing ruling

A gate closes only when a mechanical predicate over the decision ledger, coverage matrix, reader evidence, Pro rulings, and bound artifacts is true.

Neither the reader nor the Project Manager may close a gate by asserting that “enough has been checked.”

Required ledger model

The current accepted / modified / rejected / open field overloads authority, workflow state, and ruling. Split them.

Authority route

PROTECTED_PRO

PM_ENGINEERING

Workflow state

DISCOVERED_UNTRIAGED

AWAITING_PRO_RULING

DECIDED

DEFERRED_OUT_OF_SCOPE

BLOCKED_UNRESOLVED

SUPERSEDED

Ruling, where applicable

ACCEPTED

MODIFIED

REJECTED

A PM-owned engineering decision is PM_ENGINEERING + DECIDED; it is not recorded as a Pro acceptance.

Mechanical gate-close predicate

A gate may close only when all of the following hold:

every reader and grill-the-grill finding has a stable finding ID;

no finding remains DISCOVERED_UNTRIAGED;

no in-scope protected entry remains AWAITING_PRO_RULING or BLOCKED_UNRESOLVED;

every PM_ENGINEERING classification states why reversing it cannot change a registered quantity, branch, comparator, or proposition;

every DEFERRED_OUT_OF_SCOPE entry:

has no implementation binding on the current path;

cannot change the current claim;

has an explicit re-review trigger;

every mandatory or triggered coverage row is:

EXAMINED, with evidence;

or NOT_APPLICABLE, with a falsifiable reason;

Pro’s reply maps to every routed protected decision ID and records any additional decision found during its independent read;

all modified/rejected rulings have been reconciled into the frozen contract;

the certificate binds:

contract version;

decision-ledger revision;

evidence-manifest hash;

reader raw-output hashes;

coverage-matrix revision;

and, for Gate B, the skeleton or delta hash.

The Project Manager owns the mechanical act of issuing the certificate. External Pro owns the scientific resolution of protected entries. This preserves the repository authority map: Pro decides science; PM owns workflow and technical acceptance.

Q3a — may entries remain open?

No generic open entry may remain.

Implementation may begin with a deferred entry only when it has been reclassified as DEFERRED_OUT_OF_SCOPE and satisfies the conditions above.

The following always block implementation:

an unresolved estimand;

an unresolved probability or credit factorization;

an unresolved branch meaning;

an unresolved threshold, support, measure, comparator, data split, snapshot, or source-identifiability decision;

any ambiguity that could change the current registered quantity or branch.

The implementer contract already treats cross-section contradictions, branch-deciding constants/input sets, and narrowed conditioning sets as mandatory blockers rather than ordinary gaps.

Q3b — who declares coverage sufficient?

No actor declares absolute coverage sufficient.

Coverage is handled as follows:

the reader states what was examined and what was not;

grill-the-grill independently examines omissions, duplication, overreach, and weak evidence;

Pro performs an unmediated primary-evidence read and may add protected decisions;

a mechanical rule verifies that every required matrix row has a disposition and evidence;

PM issues the certificate only when that rule passes.

PM may not waive a missing row or reinterpret silence as NOT_APPLICABLE.

Pro need not state “nothing was missed.” It should state:

Within the reviewed evidence and declared coverage scope, I find no remaining unresolved protected decision.

That is bounded rather than a false completeness claim.

Q3c — awaiting Pro versus PM-decided

Yes, the distinction is mandatory.

Without it, an entry silently decided by PM is observationally identical to one waiting for scientific authority. That defeats the ledger’s purpose.

Every entry must identify:

authority route;

current state;

ruling source;

ruling artifact;

and date/revision.

The reader’s standing sweep should flag:

a protected decision routed to PM;

a PM engineering decision whose smallest consequence reaches a branch;

or any DECIDED entry with no ruling artifact.

Q3d — certificate voiding and dependencies

Any change by any actor to a protected decision, its implementation binding, or a bound evidence artifact voids the affected certificate.

The current design’s Pro-only voiding rule is too narrow.

Add:

depends_on;

affects;

certificate_scope;

re_review_trigger.

Certificates should contain the set and hashes of all decisions they cover. A change invalidates every certificate whose transitive dependency closure includes that decision.

Use dependencies to scope re-review, but fail closed:

if impact cannot be localized confidently, invalidate the full gate certificate;

if a protected decision changes after B-core, B-core and every dependent B-delta/assembled-path certificate are invalid;

a PM amendment to a nominally engineering choice also invalidates the certificate when it changes a bound runtime observable.

Q4. Do reader findings reach Pro unfiltered?
Ruling

The raw reader and grill-the-grill outputs must reach Pro losslessly. PM may organize them but may not make findings disappear. Pro must retain its own unmediated read.

The repository currently requires PM to author every external question, and also recognizes that Pro can rule only on what is placed before it.

Reconcile those constraints as follows:

PM authors the review envelope and conditional decision tree.

The reader raw and grill-the-grill raw are sealed evidence artifacts.

Both are named in the question’s evidence allow-list.

PM creates a lossless finding-disposition manifest.

Finding-disposition manifest

Each finding ID is marked:

FORWARDED_AS_DECISION;

MERGED_WITH <IDs>;

EXACT_DUPLICATE_OF <ID>;

PM_ENGINEERING, with rationale;

FACTUALLY_UNSUPPORTED, with the contradictory evidence;

OUT_OF_SCOPE, with reason.

No item is omitted from the manifest.

Uncertainty defaults to forwarding.

Merged questions must preserve all source IDs and all distinct consequences. PM may compress language; it may not merge two findings whose reversal affects different registered quantities or branches.

Q4a — what may PM drop?

PM may remove an item from the top-level Pro decision tree only when it is:

an exact duplicate;

demonstrably factual error;

or a pure layout/factoring/naming/test-construction matter that cannot change a registered quantity or branch.

Even then, the item remains visible in the disposition manifest and raw artifact so Pro can overrule the classification.

PM may not drop an item because:

PM believes the scientific concern is mistaken;

the proposed fix seems inconvenient;

another test appears to cover it;

or it would increase Pro burden.

Q4b — Pro’s unmediated read

Yes. It is mandatory.

The adversarial reader is one discovery channel, not a substitute for Pro. The repository evidence already shows materially different blind spots: the fable reader found the tolerance and clustering defects, while Pro found the conditioning-history failure.

Gate A must therefore contain a standing instruction:

Independently inspect the listed primary evidence for additional protected decisions, invalid estimands, source-identifiability failures, or branch interpretations not raised by the reader. Report the coverage inspected and any unresolved areas; do not claim completeness.

The architecture should retain at least:

primary adversarial reader;

fresh grill-the-grill reader;

Pro’s independent evidence read.

The Pro-first proposal already concedes that a single adversarial reader remains a mitigation rather than a solution.

Q5. Validation, thresholds, abandonment, and grading
Q5 ruling

V1 proves only wiring and known-case regression. V2 is the adoption gate. V3 is required for specificity and burden.

All labels, criticality assignments, match rules, thresholds, eligible holdout pool, selection procedure, grader identities, and burden calculations must be hash-bound before the first validation output is generated. The proposed design already correctly requires this before the run rather than merely before reading its result.

Q5a — critical recall
V1 — known-case regression

Required:

100% critical recall across every pre-registered finding that:

invalidates an estimand;

changes the conditioning history;

makes a registered branch unreachable;

creates an absorbing initial state;

or permits unavailable/future information.

100% recall on directly encoded critical instances.

No critical finding may be counted as matched solely because the output repeats an archetype name; it must establish the same violated invariant and consequence from permitted evidence.

A miss on a directly encoded critical instance is a wiring or instruction failure. V1 fails.

V1 does not establish transfer even at 100%.

V2 — historical OOD holdout

Required:

at least two contracts from distinct historical failure families;

100% critical recall, with no critical miss on either contract;

at least 80% recall of all pre-registered material findings;

no contract may be rescued by aggregate recall from the other.

One critical V2 miss means the mechanism cannot be trusted as a gate-closing discovery layer. It may remain advisory.

The 100% standard is intentional. A critical omission is precisely the event that allowed thousands of lines to be built against an invalid contract.

Q5b — false-positive and burden limits

For both V1 and V2:

evidence-grounded rate for forwarded items: 100%;

authority-violation count: 0;

duplicate rate after finding-ID normalization: ≤15%;

precision/actionable rate after independent adjudication: ≥70%;

burden ratio:

confirmed actionable findings
deduplicated Pro ruling nodes
​

≤1.5.

A conditional follow-up is one ruling node only when its condition fires.

The example “15 findings by 50 questions” fails:

precision is 30%;

burden ratio is at least 50/15≈3.33.

For V3:

zero fabricated critical blockers on a repaired/negative contract;

at most one noncritical false protected-semantics escalation per contract;

zero authority violations.

A Pro-confirmed novel defect counts as a true positive, not a false positive.

What licenses tuning and what requires abandonment?
Mechanical invalidation may be repaired and rerun

Examples:

contamination;

forbidden-path access;

missing output;

broken scoring harness;

model not receiving the intended evidence;

failed read-only containment.

These do not evaluate the mechanism.

Conceptual misses are not tuned on the same holdout

The current version fails when it:

misses a critical V2 finding;

falls below 80% material holdout recall;

falls below 70% precision;

exceeds the burden ratio;

or fails the metamorphic specificity test.

Adding the missed V2 instance to the casebook and rerunning on that same contract is not validation. A redesigned version requires a fresh holdout.

If two independently constructed versions fail on separate V2 sets, or the burden remains a net loss, abandon the single-reader archetype architecture rather than continuing to enlarge the casebook.

Q5c — who grades matches?

Neither PM nor the adversarial reader may grade.

Use a two-stage process:

a blinded independent adjudicator, not involved in mechanism design or generation, maps findings to the frozen ground-truth IDs;

External Pro resolves:

every disputed match;

every claimed novel finding;

every classification whose resolution changes pass/fail;

and the final adoption disposition.

A match requires all three:

the same violated invariant;

the same smallest consequence or branch effect;

an evidence path that independently establishes it.

Language similarity is neither necessary nor sufficient.

PM may calculate metrics after the adjudication mapping is sealed. It may not decide the mapping.

Q5d — V2 selection and ground truth

Before V1 output is read:

define an objective eligible pool of historical stage commits not used to construct the casebook;

freeze exclusion rules;

freeze a deterministic random selection procedure and seed, or let an independent selector choose;

commit the selected contracts’ identifiers without revealing their later resolutions to the reader.

PM may assemble the eligible pool but may not choose the final contracts after seeing V1 performance.

Ground truth must come from later-confirmed evidence at post-stage commits:

exact external rulings;

accepted reconciliations;

structural derivations;

or complete identified results.

An independent curator produces the candidate defect inventory while blinded to the griller output. Pro seals the criticality and ground-truth mapping before V2 runs.

Because historical ground truth may be incomplete:

recall uses only the sealed known findings;

a new finding is UNADJUDICATED, not a false positive;

Pro must adjudicate it before precision is calculated.

Q5e — experimental adoption

The proposed rule is correct:

V1 proves wiring; only V2 demonstrates transfer.

Before V2 passes, the mechanism may:

generate advisory questions;

establish repository facts;

produce a coverage matrix;

and help construct the Pro review package.

It may not:

close Gate A;

reduce Pro’s independent evidence read;

issue a durable certificate;

or license implementation merely because it found no issue.

The frozen G20R2 rework may use the experimental reader only under the existing full Pro review path. Any protected decision must still be ruled directly by Pro.

If V2 later fails:

experimental reader certificates expire;

Pro rulings already made remain authoritative;

a contract that relied on the experimental reader’s silence must be regrilled before a bounded screen;

a contract independently read and resolved by Pro need not repeat settled scientific rulings, but its workflow certificate must be reissued without relying on the failed mechanism.

Q5f — metamorphic pair

A metamorphic pair is a sound and valuable specificity control, but not a complete substitute for a clean negative control.

It tests:

the defect is found in the defective snapshot;

the same defect is not asserted as active after the sole repair;

unrelated findings remain stable across the pair.

It does not estimate the griller’s broad false-positive rate across a contract without the targeted defect.

Therefore:

use a metamorphic pair as mandatory V3 evidence;

retain a negative or near-negative contract when one is available;

if no contract can honestly be presumed clean, label V3 as METAMORPHIC_SPECIFICITY, and adjudicate all other findings rather than treating them as false by assumption.

Q6. Authority boundary
Q6 ruling

The line is correctly drawn:

the reader may establish facts, trace code, construct counterexamples, and run bounded read-only diagnostics;

it may not decide scientific acceptance, branch meaning, candidate retirement, experiment authorization, or successor selection.

This matches the existing implementation-review model: the reviewer is expected to measure numerical claims with the registered interpreter, while preserving backend, RNG, and contract semantics, but remains a read-only auditor.

Additional limits

The griller may not silently choose the semantics of its own diagnostic when that choice affects the conclusion. For example:

probe distribution;

null construction;

clustering unit;

tolerance;

policy snapshot;

or action support.

It may state:

Under diagnostic choice X, I observed Y.

It may not state:

X is the correct protected choice.

That becomes a Pro question.

The griller also may not run:

training;

conclusion-bearing screens;

repository-mutating probes;

or diagnostics whose side effects change the evidence under review.

Q6a — what raw evidence should Pro see?

No fact-establishing operation needs to be withheld merely because it is pre-digested. What must be prevented is lossy digestion.

Pro should receive both the finding and access to the raw evidence when the ruling may depend on:

the shape of a distribution rather than its mean;

cluster or ledger dependence;

sensitivity to one outlier;

exact control-flow reachability;

a numerical cancellation;

or competing causal explanations.

Required reader evidence should include:

exact command or derivation;

repository path and symbol;

registered runtime;

raw or minimally processed output;

assumptions;

and what the diagnostic does not establish.

A single scalar should not replace raw samples when tail shape, dependence, or heterogeneity may change the ruling.

Q6b — per-item output shape

The five-field shape is usable and does not obstruct the review.

Add metadata, not another prose field:

stable finding_id;

coverage-matrix row;

authority classification;

evidence confidence;

raw-evidence path;

duplicate/merge ancestry.

The conditional decision tree should be constructed separately from the factual finding inventory. This prevents a compact decision tree from becoming the only record of what the reader actually observed.

Q7. What this mechanism still cannot catch

Even after Q1–Q6, several classes can reach a bounded screen.

1. A wrong numerical method faithfully implementing a coherent contract

This is the most important residual class and requires the separate Technique grill already described in the Pro-first proposal.

Examples include:

biased Monte Carlo estimators;

invalid bootstrap or confidence procedures;

incorrect common-random-number coupling;

unstable inverse transformations;

optimization methods whose update is not represented by the audited gradient;

an approximation valid asymptotically but not at the registered sample size.

Gate A can approve the estimand. Gate B can prove faithful implementation. Both can still be wrong about the method.

2. Regime- or scale-dependent runtime failure

A proof-sized skeleton and assembled-path exercise may miss:

width-dependent replay drift;

long-horizon accumulation;

numerical underflow or saturation;

persistent optimizer-state effects;

concurrency or backend nondeterminism;

memory-dependent batching changes.

The bounded screen must retain an operational-invalid branch and exact runtime provenance. These are engineering outcomes, not scientific negatives.

3. A benchmark that does not separate the intended mechanism

The source can be valid, the method identified, and the behavior positive while a simpler controller, shortcut, capacity increase, or additional information explains the result.

This remains the role of:

source controls;

matched ordinary-MARL reductions;

comparator equivalence;

intervention tests;

and held-out natural execution.

The scientific principles explicitly separate benchmark access, statistical identification, intervention-sensitive behavior, and natural transport.

4. Shared epistemic blind spots

Fable, grill-the-grill, and Pro may all share an unrecognized assumption. The mechanism reduces correlated omission but cannot prove absence of unknown unknowns.

Mitigations are empirical:

V2 transfer;

rotating historical holdouts;

structurally different readers when a failure family recurs;

matched counterexamples;

and post-result adversarial interpretation.

5. Drift outside tracked code

B-delta cannot detect an unbound change in:

runtime flags;

environment data;

external dependency behavior;

untracked configuration;

hardware/backend;

or operator invocation.

Certificates must bind runtime configuration, source commit, environment identity, and conclusion-bearing command arguments—not only source files.

6. Correct evidence, incorrect final interpretation

Even a valid bounded screen can be overclaimed. A result grill remains distinct from contract and realization review. The project’s result semantics require the smallest supported or refuted proposition and preserve mixed or underpowered explanations.

Final disposition

The contract-grill mechanism should proceed only after the following protected workflow changes are incorporated:

add claim/source identifiability as archetype 17;

add registration/authority/binding to the coverage matrix;

define the gate-closing state machine and mechanical certificate predicate;

make reader and grill-the-grill raw findings losslessly visible to Pro;

retain Pro’s independent primary-evidence read;

freeze the V1–V3 thresholds, selector, ground truth, matcher, and grader before validation;

treat V1 as advisory wiring evidence and V2 as the adoption gate;

add the separate Technique-grill trigger;

void certificates after any bound protected or executable-semantic change, regardless of author;

retain Gate B-delta separately from the assembled-path exercise.

Until V2 passes, the griller is an experimental advisory discovery tool. It cannot close a gate, reduce Pro’s read, or license implementation through silence.

This ruling authorizes neither workflow-validation runs nor scientific compute.

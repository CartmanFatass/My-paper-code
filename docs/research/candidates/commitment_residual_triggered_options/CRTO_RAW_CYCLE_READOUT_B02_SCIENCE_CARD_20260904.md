Claim: A full three-update mean RAW score readout may stabilize two-sided action competence across ending phases without material native-regret loss on the exposed balanced panel.
Binding MARL structure: `systems / information flow`; the four-agent common-history gate acts under partial observability, but this object isolates a readout of learner exposure and does not estimate a multi-agent, residual-information, or causal update-order effect.

# CRTO RAW full-cycle readout B02 science card

Object: `CRTO-RAW-CYCLE-READOUT-B02`. Class: **B/EXPLORE**. Frozen: `2026-09-04`.
One seed, one shared from-genesis RAW trajectory, two readouts, three fixed ending updates.
Design provenance: explicitly outcome-informed, object-tier `OWNER_DELEGATED` inside the already
opened balanced-residual comparator ladder. No new family, consumed-C successor or C promotion.

## Question, evidence and claim ceiling

Does the arithmetic mean of legal-action predictions from three consecutive RAW snapshots meet
the unchanged two-sided competence predicate at every ending phase, without losing more than
`0.0025` native-G16 regret relative to the ordinary endpoint at any of those same endings?

A03 validly found competence only at phase-0 snapshots on seed 0, yet no aggregate-regret gain
over update 256 and no change exceeding its MEI. It did not isolate cyclic order causally. This
new readout is chosen after that observation. The A03 artifact lacks predicted score vectors,
so it cannot supply the new mean readout without new learner execution. All 16 EVAL rows and the
seed-0 bracket are exposed development information, never independent confirmation or tuning.

The ceiling is a preliminary within-trajectory readout comparison on this one initialization and
outcome-informed finite panel. It cannot establish stable performance, independent comparator
competence, headroom, cyclic-order causality, residual value, information gain, function-class
superiority, natural K8 prevalence, policy/MARL return, variable K/N, transfer, safety or deployment.
The closed natural-support objects, B01 `COMPARATOR_WEAK`, original A01 incompleteness/native
crash, and A02 `NO-FAULT-WITHIN-BOUND` remain at their own meanings.

## Subject, treatment, comparator and alternatives

Use the unchanged B01 CPU FP32 RAW gate, predictor, selected population and training law.
The **treatment** is a mean of predicted scores, not parameters, actions, probabilities or regrets.
The **same-information comparator set** is the ordinary endpoint at each of the three endings
`U={255,256,257}`. This includes phase 0, the strongest already observed competent RAW phase;
no best endpoint is selected or omitted. Its competence is remeasured and is not assumed for this
fresh run. The privileged row-wise legal-G16 oracle is only the native scoring reference.

For each row r and legal action a, record the RAW network outputs at snapshots 253 through 257.
The new readout for ending U is:

```text
q_cycle(U,r,a) = (float64(q[U-2,r,a]) + float64(q[U-1,r,a])
                 + float64(q[U,r,a])) / 3
q_endpoint(U,r,a) = q[U,r,a]
```

Add in ascending update order. Network/predictor training and forward arithmetic remain FP32;
only the declared readout mean uses FP64. Select the largest legal predicted score in the existing
printed action order, retaining its first action on an exact tie. Native G16 may be finite and
negative; regret is finite nonnegative `oracle_G16-selected_G16`. Do not clip signed G16.

Each ending compares readouts of the **same path through U** and the same `32*U` processed
examples. The older constituent snapshots necessarily have shorter training prefixes. Their
prefix exposures are reported separately, not summed as three independent learners. Three
consecutive updates process 96 examples, exactly two occurrences of each of 48 TRAIN rows.
The three windows `{253,254,255}`, `{254,255,256}`, `{255,256,257}` cover every ending phase.

Live explanations: score smoothing reduces a binary competence threshold's local instability;
generic snapshot averaging rather than cyclic-order causality; smoothing harms native action
choice; one-seed/predictor/selected-panel variation; or an information/numerical implementation
defect. A phase label is descriptive. No order randomization or residual arm is introduced.

## Population and event-to-consequence path

Reuse all exact 48 TRAIN / 16 EVAL members in B01 card section 4, including source namespace
`2026083192`, source slots `0..7`, EVALUATION/K8 episodes `832..895`, fixed listed pairs,
replanning cost 4.0, elapsed horizon 4 and the selected `|A|>=0.01` sides. Regenerate from the
unchanged generator; do not read an old result as learner input, replace rows, change thresholds,
or instantiate untouched confirmation namespace `2026083001`.

Each row is a complete four-agent service-relay reset-to-boundary history. A persistent slot owns
the active option. Its 42-dimensional history and 52-dimensional RAW target/mean/Cholesky packet
determine one legal KEEP/replacement action; the host charges replacement once and scores the
same 16-step common future. Fixed membership means no joins/leaves/rejoins, replacement, entity
versus slot ambiguity, survivor-state change or censoring. Partner co-adaptation is absent.
Primitive time, review opportunity, predictor exposure, optimizer exposure, forward rows and
scored decisions are distinct quantities. Evaluation and its mean readout never affect training.

## Learner and protected semantics

Seed 0, unchanged seed/namespace ownership and architecture. Fit one predictor from namespace
`2026090401`, 64 K4 and 64 K8 PREDICTOR_FIT tapes, 100 Adam updates, batch 128, learning rate
0.001 and existing Gaussian NLL. No residual calibration, TRUE or DERANGED input/update/evaluation.
Train RAW from genesis on the canonical TRAIN order `np.resize(arange(48),257*32)` with batch 32,
FP32, Adam lr 0.001, betas (0.9,0.999), epsilon 1e-8, zero weight decay, clip 1.0 and the existing
legal-action MSE. Capture five in-memory `.eval()` copies immediately after updates 253..257;
all evaluation follows training. Do not read or write checkpoint files or optimizer state.

The historical update-256 action result and initialization scale are descriptive reproduction
checks, not additional exact-bit or historical-anchor launch gates for this adaptive B object.
Any observed difference must be reported and investigated to the extent it affects the declared
same-path comparison; do not silently change tolerances or claim historical identity.
Protected semantics include all source coordinates, packet/evaluator equations, legal ordering,
FP32 learner/RNG/Adam order, snapshot timing, declared FP64 mean, signed score domain, EVAL
isolation and one-output-root side effects. No old source/evidence is rewritten.

## Observable, estimand and result branches

Publish every snapshot's legal prediction vector and exposure line; every ending/readout/row's
selected and oracle actions, legal G16 vector, selected score, regret and exact indicator; both
sides' counts/means; and all three paired differences. The ordinary endpoint and mean must use
the same row keys, masks, labels and ending exposure. Let:

```text
R(readout,U) = (mean_KEEP_regret + mean_REPLAN_regret)/2
D(U) = R(ENDPOINT,U) - R(CYCLE,U)
D_bar = mean(D(255),D(256),D(257))
C(readout,U) = each side has 8 rows, >=6 exact actions and mean regret <=0.005
S(readout) = all three C(readout,U) are true
delta = 0.0025
```

After a complete technically valid observation, apply the first matching branch verbatim:

1. **`B02-MATERIAL-REGRET-LOSS`**: any `D(U)<-delta`. The mean readout has a material cost at
   a declared ending; do not adopt it as the comparator readout from this result.
2. **`B02-CYCLE-COMPETENCE-STABILIZED`**: `S(CYCLE)` and not `S(ENDPOINT)`, with every
   `D(U)>=-delta`. The readout stabilizes the declared competence predicate across this cycle
   without a material paired regret cost; this is not a causal order or residual result.
3. **`B02-BOTH-READOUTS-COMPETENT`**: `S(CYCLE)` and `S(ENDPOINT)`, with every `D(U)>=-delta`.
   Both readouts are competent throughout this cycle; stabilization by averaging is unnecessary
   here. Retain the signed regret vector, including any material gain.
4. **`B02-CYCLE-COMPETENCE-NOT-STABILIZED`**: not `S(CYCLE)`, with every `D(U)>=-delta`.
   The mean readout does not meet the full-cycle competence target. Retain all partial, null and
   adverse observations; this rejects only this readout/window/seed target.

Report `D_bar` descriptively and whether it is above, inside or below the MEI; the full per-ending
rule controls. No best-window selection, window dropping, threshold adjustment, residual contrast
or result-sensitive stopping occurs. All invalid/incomplete, information, nonfinite learner or
missing prospective learner-measurement conditions yield no scientific branch. Missing resource
telemetry alone leaves an otherwise complete result valid as `resources_unmeasured`.

## MEI, headroom, narrative and predictions

MEI is absolute 0.0025 native-G16 regret, retaining the existing quarter-of-minimum-selected-
advantage margin. A relative MEI is unsuitable because side regrets can be zero. Above-MEI gain
would motivate independent-seed checking; an inside-MEI result with full-cycle competence would
motivate checking readout reliability, while inside-MEI without competence weakens this readout.
Opposite-sign material cost would recommend dropping this readout. These descriptions do not
rewrite the branch rule or authorize the next run.

Headroom remains absent: no tuned same-information baseline with seeds/curves and upper-reference
gap exists for this finite panel. Available scenario_1/relay_corridor packages do not match its
observation/action/information/population/update budget. Their absence does not hold this B run.

DM prediction before new scores: **`B02-CYCLE-COMPETENCE-NOT-STABILIZED`**, with all paired regret
differences inside the MEI. A03's side/aggregate tradeoff makes reduced variation plausible but
does not show that averaging scores reaches both competence thresholds. Owner prediction:
`not taken (unattended)`. This remains the existing ladder; no new ladder prediction item.

## Exposure, cost law, machine bound and stop rule

Machine-generated A03 exposure on this unchanged seed-0 learner already establishes usable
movement: initial L2/RMS/Linf `18.87916908516977 / 0.10402732933491829 / 0.28862619400024414`;
at 257 updates, 8224 processed examples and nominal LR exposure 0.257, measured displacement
L2/initial-L2 `0.136428218836` and Linf/initial-Linf `0.913744698074`. This is prior measured
planning evidence, not a promised identity of new weights. B02 emits its own initial scales and
both displacement ratios at every snapshot 253..257 and reports finite positive learner movement.

The runner's non-result `project-cost` emits counts, the exposure planning line above, and this
law from A02's measured RAW runner stages (seconds):

```text
base = 80.505860614001 - 14.019378483993933 - 0.05376777199853677
projected_arm_seconds(U,S) = 3 * (base + U*14.019378483993933/264
                                      + S*0.05376777199853677/13)
U=257; distinct evaluated snapshots S=5
projected_arm_seconds = 240.3031404289761
per-readout arm wall cap = 600 seconds
shared one-invocation wall cap = 600 seconds
```

The factor 3 covers load and the small averaging/publication increment. Both arms conservatively
carry the full shared trajectory projection; consumed machine time is charged once, never twice.
This is one invocation, not a seed/budget sweep or pilot-plus-main. Above-cap projection does not
launch. Exactly one predictor fit: 128 tapes, 100 updates, 12,800 processed examples. Exactly one
RAW trajectory: 257 updates, 8,224 processed examples. Five forward snapshots ×16 rows = 80
network forward rows; two readouts ×three endings ×16 = 96 scored decisions; 16 unique EVAL rows.
Common-future labels are generated once per panel row. Report actual environment/branch counts,
predictor materialized examples, no-residual counts, full argv, node, launch SHA, wall and peak RSS.

One CPU process/thread; expected RSS below 2 GiB. Immediately before the invocation require fresh
destination physical and effective memory >=4 GiB. Stop after the one complete summary or first
admission/integrity/nonfinite-measurement/cap failure. No retry loop, expansion, resume or
result-sensitive stop. A failing step is classified only after reproduction over recorded bytes.

## Portability, scope, CM objective and collection

Host CPU identity is not part of the estimand. The new object is prospectively portable across
configured local CPU and wsl_4070 CPU with the same FP32 learner and RNG law; no bit-identity
claim or GPU is allowed. Route remote-first from exact committed/pushed source in a detached
worktree via configured agent-task. The destination preflight and runner form one joined command.
Use `python -X faulthandler` prospectively for this new run; its signal-handling provenance is
explicit and does not diagnose A01. Local fallback is only legal before a remote acceptance and
under the configured portability/admission conditions. Existing artifacts are never migrated.

**Engineering scope section 4: this object needs none of the prohibited machinery.** Retained
in-memory evaluation copies use the existing learner helper, with no checkpoint files or resume
orchestration. External remote placement/tracker observation adds no research-code machinery.
CM owns only new `experiments/candidates/commitment_residual_triggered_options/raw_cycle_readout_b02/`,
`scripts/run_crto_raw_cycle_readout_b02.py`, mirrored tests, technical E0 evidence and runtime root
`temp/directions/commitment_residual_triggered_options/exp/raw_cycle_readout_b02_20260904/`.
Reuse existing B01/A01 training/host helpers, not their old object orchestration or sign predicate.
Keep <2000 non-test research lines, <600 runner lines and orchestration <30%; return excess.

Use one toy end-to-end smoke plus meaningful mean/tie, shared-path and branch-rule checks. Exercise
the actual 16-row/three-ending scoring-to-summary publication path offline with clearly synthetic
prediction vectors and existing native labels; it is engineering coverage, not empirical evidence.
The historical A01 formal-publication test gap and unresolved crash remain explicit; new-object
coverage and successful exit do not repair or scientifically reinterpret them.

Technical success establishes only the declared comparison ran and can be recomputed. CM returns
the diff/budget accounting, direct counts/receipts, rule-ready summary and E0; DM applies the rule.
Immediately on accepted launch send the task/node/SHA/cwd/root/receipt/log/bound to shared tracker
`/root/tracker_tl_experiments`, responsible DM `/root/dm_amx_crto_continue`; tracker observes and
notifies, CM collects and technically accepts, DM takes in the scientific result.

## Object-tier selection

Options: **(a)** this one-seed shared-path full-cycle readout; **(b)** pay for three new seeds
before checking this concrete readout; **(c)** enlarge RAW/retune the optimizer or rerun residual
arms before local readout discrimination. Recommendation **(a)**: it directly tests the accepted
next uncertainty with one trajectory, includes the known competent phase in the comparator set,
and supplies no claim that a selected exposed checkpoint is independent evidence.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a)**, continued by the owner's
2026-09-04 resume instruction. This is reversible object-tier comparator wording/readout inside
the accepted family. No Direction or Portfolio decision is taken; Root owns shared audit integration.

References: `CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_INTAKE_20260904.md`,
`CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_RESULT_EVIDENCE_20260904.md`,
`CRTO_RAW_PHASE_NATIVE_REPRO_A02_ENGINEERING_EVIDENCE_20260904.md`,
`CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md`.

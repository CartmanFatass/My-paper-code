# UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01 — amended science card

- Direction: `ucope`
- Object id: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Evidence class: **A/RECON**
- Frozen: 2026-09-04, before implementation or any result-bearing reconstruction
- Direction authority: reopened `em:ucope:convergence` request
  `ucope-em-convergence-20260904-02`, response SHA-256
  `7924ae06b82d61ffd25fde935bb31216b481373a0249a039b0eb7f94f3a22411`,
  `PRO_FINAL=CONTINUE`, prior object disposition `AMENDED`

## 1. Question, class, and claim ceiling

For all six accepted seed/fold policies and both live arms, do the two `THREE-WITNESS`
false-positive root actions already follow from the root targets and exact root projection induced
by the retained learned tail, or are those targets and their exact root fits oracle-safe, with the
errors introduced only by the finite-step root learner?

The directly implicated policies are:

```text
ucope-scout-r01-b1-fresh-00 / fold 1
ucope-scout-r01-b1-fresh-01 / fold 0
context=LINKED-p17_20-c7_50
```

The audit nevertheless reconstructs and reports all six policies, both arms, and all eight
contexts. It may not select only the observed failures.

The maximum claim is a same-draw, six-policy A/RECON localization of whether those two root false
positives are already present in the retained live-tail target and exact-root pipeline or arise
only in finite root fitting. It is not an algorithm-effect, stability, seed-population, fresh-draw,
deployable-objective, paid-acquisition, COUNT/RAW, generic UCOPE, variable-`k`, variable-`N`,
MARL/UAV, transfer, safety, flight, energy, deployment, real-world QoS, or Portfolio claim. A/RECON
has no C-style consumption state.

## 2. Sole retained input and binding

The sole retained scientific result input is:

```text
path=temp/directions/ucope/exp/three_witness_hinge_r01_20260904/summary.json
bytes=1273684
sha256=1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676
object_id=UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01
launch_sha=71f693ae1f1634e3e9c45461cc3c6d61c18394b8
```

It supplies exactly six seed/fold identities, the two live arm identities, twelve live learned
`beta_tail` vectors, twelve retained finite-step `beta_root` vectors and their actions/regret/
`C_root`, twelve retained `d_learned_root` scalars, the accepted draw constants, and six paired
MSE-exact tail/root references.

The runner checks the one exact path's byte count and SHA-256 before interpreting any values. It
does not construct a manifest, hash chain, authority witness, HEAD-currentness guard, or schema
framework. The accepted source surfaces are read, not modified:

- `experiments/candidates/ucope/three_witness_hinge_r01/experiment.py`;
- `scripts/run_ucope_root_conditioning_r01.py`;
- `scripts/run_ucope_competence_whitened_r01.py`; and
- their accepted UCOPE generator, basis, oracle, model, and evaluator imports.

No historical B1 attempt, sibling result, selected checkpoint, alternative offset, or fresh draw is
an authorized input.

## 3. Deterministic same-draw reconstruction

One exact reconstruction of the already accepted draw is allowed:

```text
seeds=
  ucope-scout-r01-b1-fresh-00
  ucope-scout-r01-b1-fresh-01
  ucope-scout-r01-b1-fresh-02
contexts=8
episodes_per_context_per_seed=40960
offset=2000000
folds=(0,1)
K_train=(1,3,5,7,9)
K_eval=(2,4,6,8)
```

The generator executes once per seed through the accepted address law and canonical row ordering.
The rows are shared by both arms exactly as in TW-B. Each fold reconstructs the root block:

```text
design64
probe
belief
probe_primitive
tail_return
```

This is real environment execution and must be counted:

```text
replayed_environment_episodes = 3 * 8 * 40960 = 983040
replayed_environment_transitions = 983040 * 5 = 4915200
```

The five-transition mean is the accepted balanced schedule of alternating eight-transition PROBE
and two-transition IMMEDIATE episodes. These are new runtime executions, but they create zero new
seed identities, draw identities, ancestry keys, independent sample units, learner-training rows,
or algorithm-effect observations.

The replay is outcome-blind in execution: all source constants, addresses, policies, arms, rows,
contexts, statistics, tolerances, and branches are frozen here; every member is reconstructed; no
value is inspected until the complete all-policy output exists; and no reconstructed value can
change an input, threshold, model, or branch.

## 4. Treatment and strongest same-information comparator

For each seed/fold:

- **Treatment:** the retained `THREE-WITNESS` live learned tail vector.
- **Comparator:** the matched retained `DOSE-MATCHED-SINGLE` live learned tail vector.

Both receive the identical reconstructed root block. For arm `a`, seed `s`, and fold `f`, compute
the live target array through the accepted FP32 scorer arithmetic:

```text
y[a,s,f] = root_targets_fp32(root_block[s,f], beta_tail[a,s,f])
```

Then compute the live-tail exact root through the accepted float64 least-squares path:

```text
beta_root_exact[a,s,f] = lstsq(design64[s,f], y[a,s,f], rcond=None)
```

The six retained MSE-exact-reference roots solve targets induced by separately computed MSE-exact
tails. Because the tail vector enters every PROBE root target, those references generally have
different targets and optima. They are reconstruction checks only; they may not substitute for a
live exact root, treatment, comparator, target-safety decision, or finite-fit residual.

## 5. Event-to-consequence trace

The reconstructed environment event is the accepted forced diagnostic PROBE or IMMEDIATE episode
on one of the eight fixed contexts. The root policy owns the buy/no-buy action; the retained tail
policy owns the post-PROBE period choice. Both arms have identical information and rows. Their only
difference is the already accepted learned tail vector, which changes the root target array through
the native continuation-value path. The exact root projection then maps that target into the frozen
seven-term root basis. The retained finite root is compared after that projection.

The native consequences are root action, score margin, regret, oracle-root match, and `C_root` at
all eight contexts. The audit traces target construction to exact projection to retained finite
root without learner mutation. This fixed-population host introduces no membership, slot-identity,
join/leave/rejoin, censoring, replacement, partner co-adaptation, or semi-Markov-time question.

## 6. Required observables

For every arm, seed/fold, and context, report:

1. **Finite-row induced target margin**

   ```text
   M_target(c) = mean(y | c, PROBE)
               - max_k mean(y | c, IMMEDIATE:k), k in K_train
   ```

   This is the pre-fit finite-row target contrast.

2. **Exact live-tail root policy** from `beta_root_exact`: all eight actions; root score margins;
   oracle-root match; maximum regret; `C_root`; and the actions at both
   `LINKED-p17_20-c7_50` and profitable target `LINKED-p17_20-c9_100`.
3. **Retained finite-step root policy:** the same retained fields, without retraining or sampled
   evaluation.
4. **Exact-fit residual:**

   ```text
   D_root[a,s,f] = ||beta_root_retained[a,s,f] - beta_root_exact[a,s,f]||_infinity
   ```

   Report it beside the retained `d_learned_root`.
5. **Complete arrays and vectors:** retain all twelve live FP32 target arrays and all twelve live
   exact-root vectors in the result, not only scalar summaries.

The runner performs twelve deterministic exact live-root policy evaluations and zero sampled
evaluations. It reports all counts, launch SHA, exact argv, wall time, and peak RSS when measurable;
missing RSS is `resources_unmeasured` and does not annul this non-resource claim.

## 7. Reconstruction checks and tolerance

Before applying a scientific branch, regenerated rows must reproduce:

- six retained MSE-exact-reference tail vectors;
- six retained MSE-exact-reference root vectors; and
- twelve retained `d_learned_root` scalars recomputed from the live exact roots.

The retained summary byte count and digest are exact. Row, policy, arm, context, seed, fold, support,
offset, episode, transition, target-array, solve, and evaluation counts are exact integer matches.
All required numbers must be finite.

For the solver-derived reference vectors and `d_learned_root`, reproduction means maximum absolute
difference at most `1e-12`, with no relative tolerance. The tolerance only accommodates last-bit
float64 solver serialization; it is not used for root actions, result branches, target-margin signs,
regret gates, or any scientific threshold.

Failure of any binding or reconstruction check returns
`RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE`. It creates no scientific polarity and authorizes no
partial interpretation.

## 8. Frozen result rule

Apply the first matching branch only after a complete all-policy result:

1. **`RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE`.** Any required source/draw identity, exact
   count, reconstruction check, finite value, policy/arm/context inventory, or complete output is
   missing or fails. Reading: no target-versus-fit conclusion.
2. **`ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED`.** At both implicated policy/context pairs, the
   `THREE-WITNESS` exact live-tail root selects `PROBE`, while the matched
   `DOSE-MATCHED-SINGLE` exact live-tail root selects oracle-correct `IMMEDIATE`. Reading:
   finite-step root optimization is not necessary for the two false positives; the retained
   learned-tail target plus exact-projection pipeline is sufficient on this draw.
3. **`FINITE_ROOT_FIT_RESIDUAL_SUPPORTED`.** At both pairs, the `THREE-WITNESS` exact live-tail root
   and matched comparator exact root select oracle-correct `IMMEDIATE`, while the retained
   finite-step treatment root selects `PROBE`. Reading: the live target pipeline is root-safe at
   those cells and the two false positives arise within finite root fitting.
4. **`MIXED_ROOT_CAUSE`.** Every other complete pattern, including different causes across the two
   policies, a comparator exact root that is not oracle-safe, or new contradictions. Reading:
   neither target-pipeline shift nor finite fitting alone is sufficient; no automatic learner
   successor follows.

Within branch 2 only, report a non-gating refinement:

- `TARGET_ARRAY_CROSSING` when treatment `M_target>0` and comparator `M_target<=0`; or
- `EXACT_PROJECTION_CROSSING` when the treatment exact root probes without raw target-margin
  crossing.

The immediate hypothesis is that the retained three-witness tail causes both false-positive roots
through its target and exact-root pipeline without requiring finite-step fitting error. Its exact
falsifier is:

```text
for both seed-00/fold-1 and seed-01/fold-0 at LINKED-p17_20-c7_50:
  THREE-WITNESS exact live-tail root = IMMEDIATE
  retained finite-step THREE-WITNESS root = PROBE
```

## 9. Predictions on record

- **DM:** `ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED`. The paired false positives appear exactly where
  tail-direction repairs change the continuation values, so the target/exact-projection path is
  more likely than two coincident finite-fit sign errors. The raw target-margin refinement is not
  predicted.
- **Owner:** `not taken (unattended)`.

## 10. Exposure, cost, resource admission, and stop rule

The frozen exposure line is:

```text
REPLAYED_ENVIRONMENT_EPISODES=983040
REPLAYED_ENVIRONMENT_TRANSITIONS=4915200
NEW_UNIQUE_DRAW_KEYS=0
ROOT_BLOCKS_RECONSTRUCTED=6
LIVE_ARM_TARGET_ARRAYS_COMPUTED=12
LIVE_ARM_EXACT_ROOT_SOLVES=12
EXACT_POLICY_EVALUATIONS=12
OPTIMIZER_CONSTRUCTIONS=0
OPTIMIZER_STEPS=0
PARAMETER_UPDATES=0
FRESH_SAMPLED_EVALUATION_EPISODES=0
```

Parameter displacement is exactly zero because all retained parameters are read-only; no
initialization occurs, so displacement against initialization scale is not applicable. This is
measurement exposure, not learner exposure.

The runner emits before launch:

```text
projected_total_seconds = 3 * 61.827
  * max(replay_episodes / 983040,
        replay_transitions / 4915200,
        live_exact_root_solves / 12,
        policy_pairs / 6)
```

At the fixed workload, projection and total machine-time cap are both **185.481 s**. If the emitted
projection exceeds `185.481 s`, the object is not launched. This is one object, not a sweep, so no
per-arm projection applies.

There is exactly one authorized result-bearing invocation. Immediately before it, take one fresh
central `admit-memory` receipt and require both physical and effective available memory at least
4 GiB. Launch detached from the agent process at a committed and pushed SHA. Stop after one complete
`summary.json`, or without scientific polarity on failed admission, binding/reconstruction failure,
nonfinite value, count/inventory mismatch, wall cap, missing required output, or process failure.
There is no scientific rerun, resume, arm drop, favorable subset, post-result tuning, or replacement
seed.

## 11. Launch contract and engineering scope

CM implements the smallest disposable research package, thin `argparse` runner, and mirrored tests.
The focused suite is one under-60-second toy end-to-end smoke plus cost/rule/reconstruction tests. It
runs once after the final edit and once immediately before launch; it is not repeated otherwise.
The production result root is:

```text
temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904/
```

Protected semantics: accepted summary bytes, seed/address law, offset, rows, folds, FP32 target
arithmetic, float64 `lstsq(rcond=None)`, retained decimal vectors, arm/policy/context order, exact
evaluator, result rule, numerical tolerances, counts, RNG behavior, and side effects outside the
named output root. Technical success cannot establish a scientific branch or mechanism value.

**Engineering-scope §4 line:** this object adds exactly one retained-input provenance predicate
(byte count plus SHA-256 equality for the sole summary) and 24 numerical reconstruction predicates
(six MSE-tail vectors, six MSE-root vectors, twelve live-root distance scalars) because sections 2
and 7 require same-draw binding before the target-versus-fit estimand exists. It adds no manifest,
hash chain, source/HEAD-currentness guard, distributed/resumable/retry machinery, incident tree,
registry, schema framework, compatibility shim, version field, or telemetry beyond wall/peak RSS.

New research code stays below 2,000 lines; the runner below 600; orchestration below 30 percent;
the non-smoke tests below five minutes total. A returned diff that adds other §4 machinery is
rejected.

## 12. Object-tier numerical freeze

Options for solver-derived reconstruction checks were:

- (a) require bitwise equality of all reconstructed float64 solver values;
- (b) require exact input/count binding and maximum absolute error `<=1e-12` with no relative
  tolerance for solver-derived vectors/scalars; or
- (c) generate a fresh draw instead of checking the accepted draw.

Recommendation: **(b)**. It binds the exact accepted draw while avoiding a last-bit linear-algebra
serialization artifact; the tolerance cannot change action, sign, regret, or branch decisions.
Option (c) changes the Pro-selected question.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** This is reversible card
wording inside the Pro-amended object and changes no direction or Portfolio decision.

## 13. Non-goals

Do not retrain either learner, construct an optimizer, take a gradient or optimizer step, mutate a
retained parameter, change a seed/offset/fold/row count/support set, create a fresh draw, select a
policy/context, perform sampled evaluation, inspect an old B1 attempt, substitute the MSE reference,
evaluate paid acquisition, perform COUNT/RAW work, propose a root-safe or bilevel intervention, or
infer stability, population, deployment, transfer, safety, or Portfolio polarity. A complete result
localizes only this target-versus-fit fork on the accepted draw.

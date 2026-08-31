# UCOPE competence-first successor Pro intake — 2026-08-31

## Conclusion

The consultation supplies a sound, decision-relevant mathematical limit on the
completed BELIEF object: fitting the flexible ReLU scorer only on odd `K` does
not identify its scores or action ordering on held-out even `K`. It also gives
an independently motivated successor family based on backward induction in the
host's acyclic two-decision Bellman graph.

It does **not** establish why contextual BELIEF v2 failed competence. Online
root-target drift and shared global-gradient clipping are executable mechanism
hypotheses, not observations from the completed run. The consultation had no
batchwise targets, losses, gradients, clipping indicators, or checkpoint
trajectories. A future positive result therefore may be attributed only to the
whole prospectively frozen target-frozen, cross-fitted Bellman-target package,
not specifically to target nonstationarity, max-backup error, or clipping.

A competence-first successor is conditionally registerable. It is not ready
for a result-bearing neural launch until a smaller zero-optimizer structural
competence discriminator passes on the exact retained data and the data,
fold-policy, arithmetic, solver, and artifact identities below are frozen.
This intake neither reopens the direction nor changes the completed object's
claim ceiling or Portfolio lifecycle.

## Question and non-goals

Smallest decision-changing question:

> Do the exact ten retained BELIEF v2 data tapes, when interpreted through a
> prospectively fixed Bellman-complete basis with no held-out outcome exposure,
> support competent odd-to-even reconstruction in every fixed slot?

Only if the answer is yes is it meaningful to ask whether a fixed-target
backward-induction MLP reaches the existing competence gate under the original
`640` updates per slot.

This is not a BELIEF v2 rescue or rerun. It does not ask for generic paid-
information value, COUNT-versus-RAW attribution, seed-population inference,
variable-`N`, MARL, UAV, safety, deployment, or QoS value.

## Inputs

- Archived Pro response, SHA-256
  `26b142d08a703c79f13f10abd717ca007ef0d8eca7d7a0f67eee97104bb37797`.
- Current `DIRECTION.md`, SHA-256
  `6e7b04eb3684f78e7b29582f446c03d567943800486edb54458622fa4a137493`.
- Current `IMPLEMENTATION_THRESHOLD.md`, SHA-256
  `bf176eb3658305ba400fcc41ada6ba552f5bcd6787fbc00a3b0c9dbfdcb2e3cf`.
- Current BELIEF result intake, SHA-256
  `eaa4c87c0c20a7c144ba93de11595c4c9b805cadcf2e0fbcbe5fbdddb5f143b6`.

No Transport registry, browser/session state, send process, runtime result,
checkpoint tensor, or implementation source was inspected for this intake.

## Direct documentary observation

The current accepted direction documents report a technically valid, complete
BELIEF result with complete support, `6,400` total optimizer updates, and first
controlling branch `STOP_FIXED_PANEL_COMPETENCE`. Competence is `0/10`; every
slot misses the exact root vector, exceeds maximum regret `0.02`, and has
forced-PROBE tail agreement below `0.95`. All score choices are finite and
unique. All 80 downstream signed forced-PROBE margins are positive, with exact
panel minimum

```text
12190847/800000000 = 0.01523855875.
```

Those facts remain a fixed-panel competence failure of the exact learner and
budget. They supply no acquisition or COUNT/RAW polarity.

The Pro response reports, from its pinned source packet, that the online
learner formed each PROBE root target using the then-current tail scorer, never
relabeled earlier root examples, summed root and tail losses, and applied one
global gradient-norm clip. These are source-reading claims made by the
consultation; they were not independently re-observed in this bounded intake.

## Independently checked mathematics

The consultation's core algebra is reproducible from the stated finite host.
For tail action `k`,

```text
R_SHORT(k) = 0.91 + 0.03 k - 0.011 k^2
R_LONG(k)  = 0.31 + 0.15 k - 0.011 k^2,
```

so for posterior SHORT belief `b`, tail value lies in the five-term basis

```text
(1, b, k, b k, k^2).
```

At `b=1/2`, this gives `0.61 + 0.09 k - 0.011 k^2`, hence the stated train and
held-out baselines `0.785` at `k=5` and `0.794` at `k=4`. For the sole target
context, the reported exact information value and direct cost give

```text
57149681/800000000 - 1/20
= 17149681/800000000
= 0.02143710125.
```

Thus missing only the target root action already produces the repeated regret
`0.02143710125`; that number does not diagnose its cause.

Two exact distinctions survive:

1. A positive aggregate forced-PROBE return is one value-weighted scalar. It
   neither forces root-score PROBE selection nor implies at least `0.95`
   probability-weighted equality with the optimal tail actions. The completed
   fixed panel is itself a witness to this non-implication.
2. For any even held-out `j in {2,4,6,8}`, the triangular ReLU function

   ```text
   h_j(k) = ReLU(k-j+1) - 2 ReLU(k-j) + ReLU(k-j-1)
   ```

   is zero at every odd training `k` and one at `k=j`. Adding `delta h_j(k)`
   leaves every odd-`K` fitted value unchanged while altering an even-`K`
   score. The flexible fitted objective therefore does not identify held-out
   even-`K` rankings without an additional inductive restriction.

The consultation's finite-domain ReLU construction also makes a hard
function-class impossibility implausible: indicator hinges can recover `b k`
on the finite integer action domain within the stated width. This is a
real-arithmetic representation argument, not proof that frozen FP32 AdamW
finds a competent solution in `640` updates.

## Mechanism interpretation

The reported online target law permits a final evaluated tail policy to differ
from the continuation policy represented in historical root targets. A global
clip over separate root and tail parameters also permits large root gradients
to reduce tail step size. Both are coherent causal routes.

Neither route is observed in the completed result. The strongest live
competitor is finite-exposure inductive nonidentification: odd-`K` supervision,
the exact even-`K` null directions above, small action margins, nonlinear
conditioning, and only `640` AdamW updates can jointly yield incompetent
held-out rankings even after targets are frozen.

The Pro proposal changes online targets to cross-fitted targets derived with a
Bellman-complete structural basis. Consequently it changes a composite target-
construction mechanism, not target timing alone. A pass against historical
BELIEF v2 would show that this composite package changes fixed-panel
competence; it would not isolate target drift, max backup, target variance,
cross-fitting, the structural prior, or clipping. It also changes the learner's
sample-use clock: the new root learner receives targets formed from the complete
training tape before initialization, whereas the historical targets evolved in
canonical batch order. Total training information can remain equal while its
availability and preprocessing exposure differ.

## Cheapest discriminator

Before constructing any neural model, run one create-once, zero-optimizer,
same-data Bellman-complete competence certificate. Its prospective contract
must bind:

- the exact ten retained data tapes by path, byte size, schema, and cryptographic
  digest, together with their existing manifest/support identities;
- the primitive observational unit and grouping key. Immutable within-cell row
  parity is legal only if rows sharing an episode, primitive outcome, or RNG
  ancestry cannot cross folds; otherwise the fold must be assigned at that
  shared-unit level;
- tail basis `(1,b,k/9,b*k/9,(k/9)^2)` and root basis
  `(1,(1-a)k/9,(1-a)(k/9)^2,a,aC,aL,aLp)`;
- no even-`K` outcome, action label, oracle action, metric, or policy evaluation
  in fitting;
- a fully specified arithmetic/solver law, rank law, coefficient combination
  law, tie rule, and serialization format—"exact least squares" or "normal
  equations" alone is not sufficiently determinate;
- the evaluation policy for the two fold-specific fits. The simplest strict
  choice is to evaluate both fold-specific policies and require both to satisfy
  every existing competence predicate for a slot;
- all existing root-vector, maximum-regret, and tail-agreement definitions and
  thresholds, with all ten slots retained; and
- zero model construction, optimizer update, checkpoint selection, resampling,
  appended data, or seed replacement.

The binary interpretation is:

| Observation | Supported interpretation |
| --- | --- |
| Dataset identity unavailable or changed | No same-data successor exists under this proposal. |
| Any fold rank-deficient or any fixed slot structurally incompetent | The retained rows plus the chosen Bellman basis do not uniformly support the proposed successor; do not launch the neural arm. No online-credit polarity follows. |
| Both fold policies competent in all ten slots | The retained rows plus the explicit structural prior support a competence-identifying neural comparison; this is admission evidence, not acquisition evidence. |

Calling this a "data-identifiability" certificate without the qualifier
"plus the Bellman structural prior" would be too strong: the exact `h_j`
counterexample proves that the odd-`K` rows alone do not identify even-`K`
behavior in the flexible class.

## Conditional successor freeze

If and only if the certificate passes, a new object may freeze:

- **Treatment:** one target-frozen, cross-fitted backward-induction MLP using
  the same two `9->64->64->1` FP32 scorers, features, ten initializations,
  retained rows, canonical batches, AdamW settings, global clip, and exactly
  `640` updates per slot. All root targets are materialized and sealed before
  model initialization; tail targets remain the original terminal returns.
- **Reference package:** the immutable historical online BELIEF v2 result on
  the same fixed rows and slots. It is not rerun. The structural exact-fit
  certificate is the competent same-information prerequisite, not an efficacy
  baseline.
- **Observational units and support law:** the ten named seed slots are fixed
  design points; there is no seed-superpopulation law. The exact data rows are
  the population for this object.
- **Clocks and work:** environment-row exposure, root/tail example exposure,
  structural-fit preprocessing, target materialization, optimizer updates, and
  evaluation are reported separately. Equal update count is the registered
  learner-work law; the structural preprocessing is part of the treatment and
  may not be called work-identical. Equal updates are also not equal FLOPs
  across a later linear arm.
- **Endpoint order:** host/oracle and identity validity, fold/rank and
  structural competence, complete checkpoints, neural competence (`>=9/10`),
  then all-ten root-vector equality and exact all-80 signed-margin acquisition.
  No downstream sign rescues an earlier failure.
- **Result branches:** structural failure stops before learning; structural
  pass plus neural competence failure shows the composite freeze is
  insufficient; competence pass plus acquisition failure supports only
  competent non-acquisition for this package; both passes support only this
  package's contextual acquisition on the exact fixed panel.
- **Invalidators:** identity drift, regenerated/appended rows, fold drift,
  held-out leakage, changed initialization or batch order, nonfinite/tied
  scores, incomplete checkpoint panel, changed thresholds, or post-result
  selection.
- **Resource/side-effect boundary:** one bounded CPU-only result transaction,
  admitted by the repository memory preflight immediately before execution,
  with create-once complete publication and no external side effects. Before
  registration, freeze exact wall, CPU/thread, peak-RSS, scratch, durable-disk,
  and I/O ceilings rather than leaving "bounded" as the executable contract.

The frozen identity must also cover the historical result reference, data
schema/decoder, initialization counter law or initial-tensor digests, feature
normalization, arithmetic precision, canonical batch inventory, and evaluation
implementation. Otherwise "same rows, slots, and work" is not reproducible.

The Pro response's `BC-LIN-640` arm is a useful later discriminator between a
Bellman-complete low-dimensional parameterization and the flexible MLP, but it
is not part of the cheapest admission observation. Equal updates across those
classes would identify a finite training-package difference, not a pure
representation effect.

## Claim ceiling and judgment impact

The completed BELIEF v2 ceiling and terminal interpretation remain unchanged.
For a future successor, the maximum defensible claim is:

> On the exact finite eight-context UCOPE host, exact ten retained data tapes,
> and fixed `640`-update contract, the prospectively frozen composite
> cross-fitted Bellman-target MLP did or did not satisfy the existing
> competence gate; conditional on competence, its exact fixed-panel contextual
> acquisition did or did not satisfy the existing all-ten/all-eight rule.

Even a positive treatment result would not rescue BELIEF v2 or identify which
part of the composite change mattered. It would support no generic paid-
information value, COUNT/RAW conclusion, seed-population effect, variable-`N`,
MARL, UAV, safety, deployment, or real-world QoS claim.

Scientific judgment: the response satisfies the direction's requirement for
an independently justified competence-first learner family only when the
Bellman-basis target representation and preprocessing are treated as part of
the new learner, not when the proposal is described as target freezing alone.
Registration remains conditional. The cheapest next evidence is the frozen
structural certificate above. Root retains every lifecycle and investment
decision.

## Evidence paths

- `C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/portfolio-ucope-reentry-20260831-01/RESPONSE.md`
- `docs/research/candidates/ucope/DIRECTION.md`
- `docs/research/candidates/ucope/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/ucope/UCOPE_CONTEXTUAL_PAID_ACQUISITION_R01_BELIEF_RESULT_INTAKE_20260831.md`

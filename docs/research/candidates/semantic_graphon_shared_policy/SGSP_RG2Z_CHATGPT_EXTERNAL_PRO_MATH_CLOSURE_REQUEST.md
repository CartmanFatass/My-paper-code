# SGSP RIDGEGATE-2Z ChatGPT External Pro mathematical-closure request

You are continuing the existing dedicated SGSP scientific conversation. Audit
the exact new definition-only object
`SGSP-RG2Z-SCIENCE-20260815-01`. This is not a revision, rerun, result or
trajectory continuation of SGSP B1/r06. Do not review code, implementation,
runtime, files, hashes or portfolio priority. Decide only whether the following
prospective task, comparison, inference and claim are mathematically and
causally meaning-complete.

Return exactly `CLOSED` or `REVISION_REQUIRED`. If revision is required, name
each science-bearing defect and the smallest correction. Do not treat absent
empirical run coordinates as execution permission; this portfolio layer
forbids source, tests, probes, coordinates, training and evaluation.

## 1. Exact object and legacy firewall

```text
direction=semantic_graphon_shared_policy
portfolio_object=SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION
revision=SGSP-RG2Z-SCIENCE-20260815-01
task=RIDGEGATE-2Z
definition_only=true
result_blind=true
scientific_activity_started=false
```

No old SGSP roster, task, kernel, budget, seed, threshold, checkpoint, tape,
interval, label or result enters this object. The only historical design lesson
is that harm from one wrong center cannot retain a fixed prior without a direct
advantage over a fair strictly containing EDGE learner.

## 2. Task and reward

`RIDGEGATE-2Z` has two static basins, `WEST` and `EAST`, and stable public roles
`WEST-SURVEYOR`, `EAST-SURVEYOR`, `RIDGE-RELAY`. Fleets are balanced, with
`N/3` exchangeable agents per role. One policy trains at `N={9,15}` and is
deployed unchanged at held-out `N={6,21}`. No identity, hidden role, roster-
specific head, normalization, state initialization, calibration or adaptation
is allowed. Membership is fixed within an episode; no churn is claimed.

Each episode has 12 slots. Each basin has exactly three event times drawn
uniformly without replacement from slots `0..7`; reports expire after four
slots. Surveyors detect a new local event with probability `0.75` only when
choosing `SCAN`; their FIFO capacity is two. Relay FIFO capacity is four.
Surveyors choose `SCAN|UPLINK|HOLD`; half-duplex relays choose
`LISTEN_WEST|LISTEN_EAST|FORWARD_BASE|HOLD`. Both arms have identical masks,
buffers, public role counts, observations, status messages, packet/action
support and legal-action floor.

Let `D_z` be the number of that basin's three distinct reports delivered before
expiry. `WASTE` is the fraction of non-HOLD radio decisions that listen to an
empty basin, uplink without a listening successful relay, or forward an
empty/failed report. Return is

```text
J = 0.65*(D_W+D_E)/6 + 0.25*min(D_W,D_E)/3 + 0.10*(1-WASTE).
```

Only realized actions and this task return establish value. Internal edge or
summary separation is descriptive.

## 3. Reward-independent physical kernel

Before reward, targets or learning, the normalized ridge/link model freezes

```text
P0 = [[0.92,0.48,0.88],
      [0.48,0.92,0.82],
      [0.86,0.78,0.90]]
L  = [[1,2,1],
      [2,1,1],
      [1,1,1]]
```

with receiver rows/sender columns in role order. At sender multiplicity `n_b`,

```text
p_ab(n_b)=logistic(logit(P0_ab)-0.22*(n_b-1))
K0_ab(n_b)=p_ab(n_b)/L_ab.
```

The simulator uses the underlying packet reception, latency, half-duplex and
contention law; it never queries a learned policy edge table. The policy uses
`K0` as an expected timely-link prior. Event generation and reward do not use
`K0`, and reward relabeling/rescaling leaves it unchanged. Both arms receive
the same public physical tables, counts and messages.

## 4. Treatment, containing EDGE and matching

For registered sender multiplicities `n in {2,3,5,7}` define

```text
v(n)=(2*log(n)-log(14))/log(7/2)
r_ab(n)=beta_ab0+beta_ab1*v(n)
omega_ab(n)=K0_ab(n)*exp(r_ab(n)).
```

Each arm has the same 18 output-connected coefficients. `PHY-TRUST` projects
each coefficient after every common optimizer update into `[-0.15,+0.15]`.
`EDGE-FLEX` performs the same projection operation into
`[-1.50,+1.50]`. Every treatment parameterization is literally available to
EDGE, and an output-connected coefficient `0.60` is a strict witness outside
the treatment. Both start at all-zero residuals and the identical complete
policy function `omega=K0`. They share the same coordinate chart and gradient
geometry on the common interior.

For receiver role `a`, with encoded status-message role sums `Q_b` and counts
`n_b`, both compute

```text
D_a=sum_b n_b*omega_ab(n_b)
Z_a=sum_b omega_ab(n_b)*Q_b/(D_a+1e-12).
```

The common recurrent actor receives local observation, public receiver role,
counts, `Z_a` and `D_a`. Both arms have identical common tensors, initialization,
parameter count, optimizer state/hyperparameters, batches, critic/baseline,
gradient calls, clipping, recurrent state, action support, messages,
communication and output-relevant useful work. Both use three role reductions,
nine kernel evaluations, 18 residual multiply-adds, nine exponentials and one
actor call per agent. There is no dummy, frozen padding, delayed gate or dense
learned `N x N` object.

## 5. One budget, competence and coordinate boundary

The sole budget is 512 matched optimizer updates. Each update contains 64 full
12-slot episodes, exactly 32 from each training roster. Only the immediate
update-512 checkpoint is evaluable. Held-out rosters may not be used for
training, normalization, adaptation, replay, calibration or selection. No
earlier/later checkpoint or second budget exists.

`UNIFORM-LEGAL` is an untrained task floor, not a matched comparator.
`EDGE_TRAIN_COMPETENT` requires at both training sizes that the simultaneous
lower bound for `EDGE-FLEX - UNIFORM-LEGAL` exceed `0.08` and the two-sided
`PHY-TRUST - EDGE-FLEX` interval lie wholly inside `[-0.04,+0.04]`.

A later empirical object, only if separately authorized, uses 24 new
independent training-seed blocks and 256 fresh evaluation episodes per roster
and seed. The seed is the inferential unit; agents, slots, reports and episodes
are not replicates. Arms share future tapes within an exact seed/roster, while
different `N` worlds are not pathwise pairs. This definition-only layer
deliberately binds no exact seed labels, stochastic namespace, run root,
certificate or artifact coordinate. A later binding may not reuse old SGSP
identities or observations and requires renewed closure if it changes science.

## 6. Inference, answerability and margins

One Bonferroni family contains exactly 18 seed-level quantities: four direct
roster contrasts; two training EDGE-versus-uniform competence contrasts; two
held-out-minus-seen interactions; two held-out worst-zone contrasts; return
drop, legal-action TV and advantage attenuation for the cut at both held-out
sizes; and two held-out return-answerability quantities. Every quantity uses a
two-sided Student-`t` interval with per-contrast error `0.05/18`, so family-wise
error is at most `0.05`.

For seed `s`,

```text
d_s(N)=J_PHY_s(N)-J_EDGE_s(N)
d_seen_s=0.5*(d_s(9)+d_s(15))
c_s(N)=d_s(N)-d_seen_s, N in {6,21}.
```

Fresh margins are

```text
direct return delta_R=0.04
cold-start interaction delta_C=0.03
worst-zone delivery delta_Z=0.02
cut return loss delta_cut_R=0.05
cut legal-action TV delta_TV=0.08
advantage attenuation delta_I=0.03.
```

At a held-out size, return is answerable only when the simultaneous lower bound
for the within-seed minimum of `J_PHY,J_EDGE,1-J_PHY,1-J_EDGE` exceeds `0.04`.
False answerability is floor/ceiling saturation, not equivalence or inferiority.
Validity also requires complete evidence, positive basin/event/role support,
fixed legal support, no leakage, exact matching/nesting and finite outputs.

## 7. Action-sensitive kernel use

At both held-out sizes, apply a treatment-only
`SEMANTIC-COLUMN-ROTATE`: cyclically rotate the physical sender columns
`WEST-SURVEYOR -> EAST-SURVEYOR -> RIDGE-RELAY -> WEST-SURVEYOR`, while learned
residual indices, public counts, messages, receiver role, local observations,
actor/recurrent parameters, simulator physics, target events, reward, legal
actions and exogenous tapes remain fixed. Balanced roles preserve each
receiver-row coefficient multiset.

Shadow replay on intact predecision histories measures legal-action TV. Full
paired counterfactual rollouts measure treatment return drop and attenuation of
the intact `PHY-TRUST - EDGE-FLEX` advantage. The cut passes only when the
simultaneous lower bounds exceed `0.08`, `0.05` and `0.03`, respectively, at
both held-out sizes. Summary change is insufficient and cut harm cannot rescue
a failed intact comparison.

## 8. First-match decision law

1. Invalid/incomplete evidence, leakage, mismatch or noncontainment yields no
   relation.
2. Failed held-out return answerability, failed exact legal-action support or
   failed `EDGE_TRAIN_COMPETENT` yields `NONIDENTIFIED`; it cannot retain or
   delete a family. Legal-action TV remains a registered cut quantity, not a
   separate answerability quantity.
3. `RETAIN_PHYSICAL_PRIOR_COLDSTART` requires direct held-out lower bounds
   above `0.04` at both sizes, interaction lower bounds above `0.03` at both,
   worst-zone lower bounds above `0.02` at both, and every action-sensitive cut
   gate at both, after all earlier gates pass.
4. Every other complete, valid, answerable panel with competent EDGE selects
   `DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT` for this task/budget, descriptively
   distinguishing EDGE practical equivalence, EDGE superiority, mixed roster
   effects, zone-balance failure or absent semantic action use. No wrong-center
   result may enter any branch.

No branch authorizes a budget/checkpoint search, seed/threshold change, old
result pooling, new task, source/build/test/probe, empirical coordinate,
training/evaluation, second surface or UAV work.

## 9. Strongest alternative and claim ceiling

The strongest alternative is that the narrow projection domain, count
normalization, curvature, regularization or optimizer preconditioning—not
semantic correctness—provides a finite-budget benefit. Identical initial
policy, literal nesting, common chart, seen-size competence, cold-start
interaction and cut attenuation reduce comparator-handicap explanations but do
not identify kernel truth or faster learning.

The maximum positive statement is:

> In the exact static two-basin `RIDGEGATE-2Z` toy, after 512 matched updates,
> one shared policy constrained near a reward-independent terrain/radio kernel
> produced an action-sensitive return advantage over a competent, equally
> initialized and strictly containing matched EDGE learner at the adaptation-
> free held-out `N={6,21}`; the advantage was larger than at seen `N={9,15}`
> and was not purchased by sacrificing one basin.

It cannot establish a curve, rate, asymptotic superiority, kernel truth, unique
physical correctness, another budget/roster, arbitrary terrain or role mix,
churn, moving zones, fading robustness, perception validity, flight dynamics,
safety, real-radio performance, second-surface efficacy or UAV mission value.

## Required closure audit

1. Is the task sufficiently physical and reward-independent, or does its
   simulator make `K0` a disguised answer table?
2. Is the direct coefficient-box relation a strict functional containment with
   fair initialization, gradient geometry, inputs, parameters and useful work?
3. Do the competence and seen-versus-held-out interaction predicates isolate a
   competent EDGE cold-start question rather than generic training failure or
   count scaling?
4. Are return answerability, legal-action support, the inference family, the
   semantic cut and first-match branches coherent and result-blind?
5. Does the maximum claim preserve the unavoidable regularization/
   preconditioning alternative and the toy/UAV boundary?
6. Is leaving exact stochastic/run coordinates unbound scientifically coherent
   for a Pro-closed definition-only object, given that any science-changing
   later binding returns for closure before activity?

## Required response format

```text
MATH_CLOSURE_DECISION=CLOSED|REVISION_REQUIRED
EXACT_REVISION=SGSP-RG2Z-SCIENCE-20260815-01
RESULT_BLIND=true

TASK_AND_REWARD_INDEPENDENCE
<audit>

CONTAINMENT_AND_MATCHING
<audit>

COLD_START_IDENTIFIABILITY
<audit>

INFERENCE_AND_BRANCH_LAW
<audit>

DEFECT_LEDGER
SCIENCE_BEARING_DEFECT_COUNT=<integer>
<NONE or numbered exact defects and smallest repairs>

STRONGEST_ALTERNATIVE
<remaining explanation>

CLAIM_CEILING
<maximum statement and exclusions>

FINAL_DISPOSITION=CLOSED|REVISION_REQUIRED
```

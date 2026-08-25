# UCOPE variable-k paid-probe containment R01 revision 02 science card

```text
direction_id=ucope
candidate=CAND-VSP-07-UCOPE
object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-02
owner=Portfolio-owned same-direction UCOPE Explorer Manager
stage=prospective science definition; complete revision 02
formal=false
implementation_runtime_lease_authority=false
supersedes_science_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-01
revision_reason=ChatGPT_Pro_REVISION_REQUIRED_plus_EM_correction_and_bounded_Gemini_intake
```

## Question and portfolio value

In the finite renewal host below, can a reward-trained policy learn when to pay
a real service/time/energy cost for a diagnostic probe, use a protected
version-closed first-hit count, and then select a held-out effective period with
positive external value over the strongest immediate-commitment null?

The object separates four questions that B2 bundled:

1. Is the probe's information about a persistent tail regime valuable?
2. What value comes directly from service delivered during the probe, after its
   time and energy costs?
3. Can a fixed-budget FP32 learner use the protected count on held-out periods?
4. Does the count summary add finite-budget value beyond an equal-information
   raw-history learner, or is the acquisition mechanism fully contained by
   generic history or exact belief?

The object matters only if its answer changes a variable-`k` design choice. It
does not test authenticated ownership, receipt survival, variable roster size,
multi-agent coordination, or a UAV implementation.

## Finite host

### Episode clock, latent regime, and panels

One episode has a physical horizon of `H=12` units and one root decision.
The hidden regime is

```text
Theta in {SHORT, LONG},  Pr(Theta=SHORT)=Pr(Theta=LONG)=1/2.
```

The three separately trained and evaluated panels are:

- `PERSISTENT`: `Theta_probe = Theta_tail`.
- `REDRAW`: `Theta_probe` and `Theta_tail` are independent prior draws.
- `SEVERED`: the physical regime persists, but the policy's probe channel is a
  yoked independent history generated from an independent prior draw. Direct
  probe service and costs remain those of the actual probe history.

Panels have separate learner replicas. The panel name, latent regime, and
severance fact are never policy inputs. No policy is expected to infer whether
one episode came from another panel.

### Train and held-out period schedules

An effective period is an integer dwell length `k`. The action scorer is shared
over candidate periods and receives numeric period features; it is not a fixed
class head.

```text
K_train = {1, 3, 5, 7, 9}
K_test  = {2, 4, 6, 8}
```

Every training root or tail decision exposes all five `K_train` candidates.
Every conclusion-bearing evaluation exposes all four `K_test` candidates.
No even `k` is used for optimizer updates, checkpoint selection, early
stopping, architecture choice, or hyperparameter tuning. There is no search
over `k`, and no post-result change to either set.

### Root and tail actions

At the root the legal actions are:

- `COMMIT(k)` for each currently exposed `k`; or
- `PROBE`.

`COMMIT(k)` executes the tail service immediately and terminates. `PROBE`
occupies two physical units, executes exactly six declared micro-exposures, and
then permits one tail `COMMIT(k)`. Since `2 + max(K_train union K_test) = 11`,
every legal trajectory ends within `H=12`.

The root sees the prior, remaining clock, candidate-period descriptors and
cost coefficients. It does not see a regime label, future randomness, or a
probe outcome. At the tail it receives only its assigned protected-count,
raw-history, belief, or blind channel.

### Probe law and version-closed count

Let the six actual probe hits be `Y=(Y1,...,Y6)`. Conditional on the probe
regime they are independent Bernoulli marks:

```text
Pr(Yi=1 | Theta_probe=SHORT) = 0.85
Pr(Yi=1 | Theta_probe=LONG)  = 0.15
```

The exposure ledger is frozen before outcomes: `E=6`. The protected first-hit
count is `N=sum_i Yi`. All six marks belong to one declared episode/executor
version. Mixed-version pooling, post-tail updates, outcome filtering, and reuse
across episodes are outside the object. Order and timestamp carry no predictive
information in this law, so `N` is a sufficient statistic for `Theta_probe`;
the six-bit raw history contains the same relevant information plus ancillary
order.

In `SEVERED`, actual `Y` still determines direct probe service. The policy is
instead shown `Y'`, a six-mark history generated from an independent prior
regime using the same law. COUNT receives `N'=sum_i Y'`; RAW receives `Y'`.
This preserves channel format and marginal distribution while deleting its
association with the persistent tail regime.

### Tail service and total external value

For `theta in {SHORT,LONG}`, define preferred-period anchors

```text
kappa_SHORT = 2
kappa_LONG  = 8.
```

After `COMMIT(k)`, the tail service indicator `Z` is Bernoulli with

```text
q_theta(k) = 0.95 - (k-kappa_theta)^2 / 100.
```

All declared train and test periods keep `q_theta(k)` strictly within `[0,1]`.
The realized tail utility components are:

```text
tail_service = Z
tail_time    = -0.01 k
tail_energy  = -0.001 k^2.
```

If the episode probes, its separately retained components are:

```text
probe_service = 0.08 (N/6)
probe_time    = -0.03
probe_energy  = -0.03.
```

The probe service component always uses actual `N`, including under severance.
It is not a tail observation. Averaged over the symmetric prior,
`E[probe_service]=0.04`, while declared probe time plus energy cost is `0.06`.
The forced blind probe therefore has a population direct net value of `-0.02`:
the probe must repay a real cost through information. The implementation uses
ordinary FP32 and a tolerance, not exact rational arithmetic, to verify this
reference value.

The sole training and primary evaluation return is the unshaped sum

```text
J = tail_service + tail_time + tail_energy
    + 1{PROBE}(probe_service + probe_time + probe_energy).
```

No count bonus, posterior reward, information bonus, prediction loss, coverage
surrogate, or branch-dependent shaping enters `J`.

## Treatment and comparators

### Exact learned feature map and FP32 contract

All learned arms use one normative coordinate map. Let the six-value channel be
`c=(c1,...,c6)`.

| decision/candidate | c | stage coordinates 7--8 | action coordinates 9--10 | coordinates 11--12 | coordinate 13 |
|---|---|---|---|---|---|
| root PROBE | `(0,0,0,0,0,0)` | `(1,0)` | `(1,0)` | `(0,0)` | `1` |
| root COMMIT(k) | `(0,0,0,0,0,0)` | `(1,0)` | `(0,1)` | `(k/9,(k/9)^2)` | `1` |
| tail COMMIT(k) | arm-specific tail c | `(0,1)` | `(0,1)` | `(k/9,(k/9)^2)` | `10/12` |

There is no tail PROBE. Coordinates are in the exact displayed order. At the
root every arm therefore receives the identical no-probe-yet channel. The state
baseline has exactly nine coordinates in this order:
`(c1,c2,c3,c4,c5,c6,stage_root,stage_tail,remaining_time/12)`.
Neither scorer nor baseline receives panel, latent regime, severance, seed,
episode index, outcome, reward, future randomness, or an arm label.

Tail channels are:

- COUNT: `(N/6,E/6,(N-E/2)/E,1,0,0)`, with `E=6`;
- RAW: `(Y1,Y2,Y3,Y4,Y5,Y6)`; and
- BELIEF-FEATURE: `(rho,1-rho,1,0,0,0)`.

Here `rho=Pr(Theta_tail=SHORT | displayed history, panel law)`. In
PERSISTENT, for displayed count `n`,

```text
rho(n) =
  [0.85^n 0.15^(6-n)]
  / [0.85^n 0.15^(6-n) + 0.15^n 0.85^(6-n)].
```

In REDRAW and SEVERED, `rho(n)=1/2` for all displayed histories. Evaluate the
formula in the written multiplication/exponent order, cast the final scalar once
to FP32, and use that same value for BELIEF-FEATURE and BELIEF-DP. The formula,
not a learned estimate or table fitted to outcomes, defines all seven count
values.

The common action scorer is `13 -> 64 ReLU -> 64 ReLU -> 1`, with ordinary
biases. The separate state baseline is `9 -> 32 ReLU -> 1`. All parameters,
features, activations, gradients, optimizer state, returns and ordinary
reporting reductions are FP32. Unit-temperature softmax over the current legal
candidate list defines the training policy.

Root legal-action order is PROBE followed by COMMIT(k) in increasing k. Tail
order is COMMIT(k) in increasing k. Greedy evaluation chooses the first action
in this order only for an exact FP32 score tie.

The learned arms therefore have identical trainable parameter counts. There is
no FP64, mixed precision, reduced precision, exact-arithmetic kernel, correctly
rounded premise, proof-grade hot path, or tolerance-free float identity claim.
Integer counter addresses and order are reproducibility facts only.

### Learned arms

1. `COUNT-FP32` — treatment. At the tail its six-value channel is
   `(N/6, E/6, (N-E/2)/E, 1, 0, 0)`. At the root it receives the common
   no-probe-yet channel.
2. `RAW-FP32` — equal-information containing learner. At the tail its channel
   is `(Y1,...,Y6)` in the declared micro-exposure order. It has no count,
   posterior, regime, or panel bit. The law makes order ancillary, so RAW has
   every fact needed to compute COUNT and no less relevant information.
3. `BELIEF-FEATURE-FP32` — common-learner competence control. At the tail its
   channel is `(rho,1-rho,1,0,0,0)`, where `rho` is the model-defined posterior
   probability that the tail regime is SHORT. In REDRAW and SEVERED, `rho=1/2`
   regardless of the displayed probe channel. It uses the same scorer and
   training budget and does not define the main treatment contrast.

The arms have independent weights but paired initialization namespaces and
counter-keyed host randomness. No parameter, gradient, optimizer state,
checkpoint, action, or realized reward crosses arms.

### Nonlearned comparators

4. `BELIEF-DP` — exact-model containing comparator. It knows the frozen
   generative law, computes the posterior from the allowed channel, enumerates
   legal root and tail actions, and maximizes expected `J`. “Exact” means exact
   access to the declared probabilistic model, not exact arithmetic: the finite
   enumeration is ordinary FP32 with frozen `1e-6` comparison tolerance and the
   same tie order.
5. `IMMEDIATE-DP` — strongest count-blind immediate commitment. It knows the
   prior, all test-period laws and costs, may choose any exposed `k`, and may
   not probe. It is not a weak learned null.
6. `FORCED-PROBE-BLIND-DP` — decomposition comparator. It incurs the actual
   probe service/time/energy components, ignores the probe channel, and then
   selects the prior-optimal test period. It differs from `IMMEDIATE-DP` only
   by the probe's direct service/time/energy contribution.

## Frozen training law

Each learned arm has ten master seeds:

```text
101, 211, 307, 401, 503, 601, 701, 809, 907, 1009
```

For every seed, panel and learned arm, train exactly `81,920` episodes in 320
batches of 256. PERSISTENT has 128 episodes per regime per batch. REDRAW has 64
per ordered probe/tail regime pair. SEVERED has 64 per ordered
actual/displayed regime pair.

For scorer parameters `phi`, the policy at state `s` is exactly

```text
pi_phi(a|s) = exp(f_phi(s,a)) / sum_{a' in A(s)} exp(f_phi(s,a')).
```

For episode `e`, let `G_root=J`. If the sampled root action is PROBE, let
`G_tail=tail_service+tail_time+tail_energy`; the already-realized probe
service/time/energy is excluded from tail reward-to-go because it is invariant
to the tail action. With detached baseline advantages, batch size `B=256`,
and zero tail terms for immediate-commit episodes:

```text
L_policy = -(1/B) sum_e [
  log pi(a_root|s_root) stopgrad(G_root-b(s_root))
  + 1{PROBE} log pi(a_tail|s_tail) stopgrad(G_tail-b(s_tail))
]
  - beta_b (1/B) sum_e [
      H(pi(.|s_root)) + 1{PROBE} H(pi(.|s_tail))
    ]

L_baseline = (1/B) sum_e [
  (b(s_root)-G_root)^2
  + 1{PROBE}(b(s_tail)-G_tail)^2
]

L_total = L_policy + 0.5 L_baseline.
```

The scorer and baseline are disjoint parameter sets stepped once by one joint
AdamW optimizer on `L_total`. Use `lr=3e-4`, betas `(0.9,0.999)`,
`eps=1e-8`, weight decay `1e-4`, global gradient-norm clip `1.0`, and no
return or advantage normalization. Entropy is

```text
beta_b = 0.01 (320-b)/319,  b=1,...,320,
```

so batch 1 is 0.01 and batch 320 is zero. Final batch-320 weights are the only
checkpoint evaluated.

Every affine weight matrix uses Glorot-uniform initialization
`U[-sqrt(6/(fan_in+fan_out)),+sqrt(6/(fan_in+fan_out))]`, cast once to FP32;
all biases are FP32 zero. For a fixed seed and panel, the indexed initialization
uniform for each parameter coordinate is shared across COUNT, RAW and
BELIEF-FEATURE. Different panels and master seeds use independent initialization
arrays.

The finite paired population is defined by independent indexed uniforms with
these exact addresses and sharing laws:

| namespace | index | use | shared across learned arms? |
|---|---|---|---|
| `REGIME` | seed,panel,batch,slot | fixed balanced regime or ordered regime pair, followed by one indexed permutation within the batch | yes |
| `PROBE_ACTUAL` | seed,panel,episode,micro-exposure | actual Bernoulli probe mark | yes |
| `PROBE_DISPLAY` | seed,SEVERED,episode,micro-exposure | independent yoked displayed mark | yes |
| `TAIL_Z` | seed,panel,episode,k | potential Bernoulli tail outcome for every legal k | yes |
| `ACTION` | seed,panel,arm,episode,root-or-tail | inverse-CDF categorical action sample | no; arm-specific |
| `INIT` | seed,panel,network,parameter-coordinate | Glorot draw | yes |

All addressed uniforms are mutually independent unless the table says they are
shared. Bernoulli outcomes use `1{U<probability}`. Potential tail outcomes for
unselected k exist only to define the paired population and are never learner
inputs. Episodes remain in batch/slot order; there is no second shuffle.

Training uses only `K_train`. Reward components are retained separately but
optimization receives only the declared return-to-go above. There is no
validation selection, early stopping, restart, learning-rate change, sweep,
rescue, augmentation, demonstration, model transfer, or extra seed.

## Complete held-out evaluation and attribution diagnostics

For every final seed/panel/arm checkpoint, conclusion-bearing evaluation uses
`K_test` and finite enumeration, not Monte Carlo sampling. Enumerate both
probe regimes and every tail regime permitted by the panel, all `2^6` actual
histories, all `2^6` displayed yoked histories under SEVERED, every legal
candidate period, and the analytic expectation of terminal service. Use the
frozen model probabilities as FP32 weights. Reject normalization error above
`1e-5`. Retain expected total J, every utility component, root action, tail
action by displayed history, posterior bin, support and competence facts.

Two prespecified attribution diagnostics do not change the primary acquisition
gate:

1. Evaluate the same final checkpoints exhaustively on `K_train`, with no
   optimizer update. Report COUNT-minus-RAW separately on K_train and K_test.
   A gap present only on K_test is explicitly an interpolation-specific
   advantage, not a general representation advantage.
2. For forced-probe RAW only, compute `RAW-PERMAVG`: for each displayed
   six-bit history, average the final RAW tail logits over all distinct
   permutations of that history, then apply the frozen greedy tie rule. Do not
   retrain or recompute RAW's root action. Report `A_RAW-PERMAVG` and its
   tail agreement with COUNT/BELIEF-DP. If permutation averaging contains the
   COUNT tail value, attribute any unaugmented COUNT-over-RAW gap to explicit
   permutation-invariance engineering; do not claim a broader raw-history
   insufficiency.

These diagnostics use the already-frozen checkpoints and complete populations.
They do not authorize augmentation, an alternate optimizer, another run, or
post-result model selection.

## Estimands and exact decomposition

For panel `p` and learned arm `a`, define:

- `J_a,p`: expected value of the arm's endogenous greedy root and tail policy;
- `A_a,p`: expected value when root PROBE is forced and the arm chooses the
  tail period;
- `A_0,p`: expected value of `FORCED-PROBE-BLIND-DP`;
- `B_p`: expected value of `IMMEDIATE-DP`;
- `I_a,p = A_a,p - A_0,p`: channel information value after holding the probe's
  direct service/time/energy path fixed;
- `D_p = A_0,p - B_p`: direct probe service/time/energy value with no channel
  use; and
- `Gamma_a,p = A_a,p - B_p = I_a,p + D_p`: forced-probe net acquisition value.

Also report `G_a,p = J_a,p - B_p`, the actual endogenous policy gain. A learned
arm counts as having acquired only when its greedy root chooses PROBE. The
identity `Gamma=I+D` is checked within FP32 tolerance `1e-5`; failure is a
non-identifying analysis defect, not a scientific outcome.

The primary treatment question concerns `COUNT-FP32`. `RAW-FP32` determines
whether a count-summary advantage survives an equal-information containing
learner. `BELIEF-DP` supplies the model ceiling, not evidence for the learner.

## Headroom, support, and competence gates

### Pretraining model/headroom gates

Before any learned result is interpreted, finite `BELIEF-DP` enumeration over
the frozen law and `K_test` must establish all of the following without changing
any constant:

1. the prior-optimal `IMMEDIATE-DP` test period is unique by at least `0.02`;
2. the regime-conditional optimal test periods differ;
3. `I_BELIEF-DP,PERSISTENT >= 0.04` and
   `Gamma_BELIEF-DP,PERSISTENT >= 0.03`;
4. `D_PERSISTENT` lies in `[-0.021,-0.019]` at the symmetric population level;
5. in REDRAW and SEVERED, `abs(I_BELIEF-DP) <= 1e-5`, and BELIEF-DP prefers an
   immediate commitment over PROBE by at least `0.019`; and
6. every q-value and total expected action value is finite and separated from
   an FP32 tie by more than `1e-6`, except where the frozen tie rule is the
   intended null.

Failure means the frozen host lacks the promised discriminator. Do not tune
probabilities, costs, period sets, margins, or budget after that observation.

### Training support gates

For every seed/panel/learned arm before accepting its final checkpoint:

- every root action, including PROBE and all five immediate periods, has at
  least 2,048 sampled training visits;
- conditional on PROBE, every tail period has at least 2,048 visits;
- PERSISTENT has exactly 40,960 episodes per regime; REDRAW has exactly 20,480
  per ordered probe/tail regime pair; SEVERED has exactly 20,480 per ordered
  actual/displayed regime pair; and
- each displayed count `N in {0,...,6}` occurs at least 256 times in the
  treatment-relevant training channel.

A support failure yields no representation or acquisition conclusion. It is
not repaired by dropping a seed or adding episodes to the frozen treatment.

### Common-learner competence gate

For seed `s` and panel `p`, competence regret is exactly

```text
R_comp(s,p) = J_BELIEF-DP,p - J_BELIEF-FEATURE,s,p,
```

using the endogenous greedy root and tail value on the complete held-out K_test
population.

Tail agreement is separately

```text
T_comp(s,p) =
  E_p[ 1{k_BELIEF-FEATURE(history)=k_BELIEF-DP(history)} | root forced PROBE ],
```

weighted over the complete forced-PROBE held-out panel, including displayed
histories for which either endogenous root would commit immediately.

BELIEF-FEATURE must, for every panel and at least 9 of 10 seeds, match the
BELIEF-DP greedy root action, have `R_comp<=0.02`, and have `T_comp>=0.95`.
If this fails, the learner/budget/action scorer is not competent enough to
attribute RAW or COUNT shortfalls to representation. Exact BELIEF-DP remains
structural headroom only.

## Activity start and analysis

Question-relevant scientific activity begins only after all three learned arms,
all three panels and all ten seeds have final batch-320 checkpoints and the
first complete held-out enumeration has emitted every arm/panel/seed value,
component, action, support fact and competence fact. Training logs, one arm,
one panel, one seed, a partial enumeration, a model/headroom check, or a
technical exercise is not question-relevant output.

For seed `s`, define the prespecified worst signed acquisition margin

```text
M_s = min(
  Gamma_COUNT,PERSISTENT - 0.03,
  I_COUNT,PERSISTENT     - 0.03,
  0.02 - abs(I_COUNT,REDRAW),
  0.02 - abs(I_COUNT,SEVERED),
  0.05 - (J_BELIEF-DP,PERSISTENT - J_COUNT,PERSISTENT)
).
```

The null-panel forced-probe Gamma terms are deliberately absent:
`Gamma=I+D` and `D≈-0.02`, so correct null behavior is `I≈0` and a
negative forced-probe Gamma, not `Gamma≈0`.

Use the ten paired seed values and a one-sided 95% Student-t lower confidence
bound for `mean(M)`. The acquisition mechanism is supported only when that
lower bound is above zero, every persistent COUNT seed chooses PROBE, every
REDRAW and SEVERED COUNT seed chooses an immediate commitment, the support
gates pass, and the common-learner competence gate passes. Report null-panel
Gamma centered on the declared D as a decomposition check, not as another
specificity gate.

The equal-information containment contrast is

```text
Delta_COUNT_RAW = J_COUNT,PERSISTENT - J_RAW,PERSISTENT.
```

Use its paired two-sided 95% Student-t interval only after the acquisition gate:

- lower bound above `+0.03`: finite-budget count-summary advantage in this
  host;
- entire interval inside `[-0.03,+0.03]`: RAW contains the learned acquisition
  value within the frozen band; no count-summary advantage;
- upper bound below `-0.03`: RAW is superior; no count-summary advantage; or
- otherwise: containment unresolved at the frozen budget.

This secondary classification cannot rescue a failed acquisition gate. Report
all seed values and intervals; do not remove outliers, pool episode rows as
independent samples, or add seeds.

## Exhaustive interpretation map

1. **Incomplete activity-boundary output.** No scientific result. The same
   frozen work may be completed after unchanged-science technical repair; this
   is completion, not a second scientific run.
2. **Probability, decomposition, channel, complete-panel, or FP32-normalization
   invariant failure before the activity boundary.** No scientific result. A
   technical owner may repair and complete the unchanged object if Portfolio
   has authorized engineering. No scientific constant or treatment may change.
3. **Complete support failure.** The fixed-budget learned treatment is terminal
   and non-identifying. Do not add episodes, drop seeds, or rerun this host.
4. **Complete common-learner competence failure.** The learned representation
   comparison is terminal and non-identifying. Retain only analytic host
   headroom; do not tune or rerun.
5. **Technically valid acquisition or persistence-specificity failure.** This is
   a terminal negative result for the learned UCOPE route. Retain accounting,
   ledger and control design only; no rerun.
6. **Acquisition supported and COUNT beats RAW by the frozen interval.**
   - If the advantage occurs on both K_train and K_test and RAW-PERMAVG does
     not contain the tail value, retain a local finite-budget protected-count
     advantage and make one separately authorized dynamic service/roster object
     eligible for Portfolio consideration.
   - If the gap is held-out-k-only, narrow it to interpolation-specific value.
   - If RAW-PERMAVG contains it, attribute it to explicit permutation-invariance
     engineering and make no broad raw-history-insufficiency claim.
   In every subcase this host is terminal and cannot rerun.
7. **Acquisition supported with COUNT/RAW equivalence or RAW superiority.**
   Retain generic active acquisition, delete an independent count-summary
   algorithm claim, and terminate this host with no rerun.
8. **Acquisition supported with unresolved COUNT-versus-RAW interval.** Retain
   only the acquisition result; the count containment question remains
   unresolved at the fixed budget. Do not add seeds or rerun. Any later object
   requires a distinct Portfolio decision and cannot claim R01 resolved count
   containment.

All complete technically valid runs are terminal for this frozen host. Only
preactivity technical non-completion in classes 1--2 permits unchanged-science
completion. No class authorizes tuning, another seed, another checkpoint,
another panel, or a second scientific run.

## Strongest alternative and claim ceiling

The strongest alternative is that a generic learner can compute the sufficient
count from raw marks, so the useful object is active belief acquisition rather
than a distinct count-state architecture. A second alternative is that probe
service, rather than information, pays for the intervention. The equal-
information RAW arm, BELIEF-DP ceiling and `Gamma=I+D` decomposition directly
preserve those alternatives.

The maximum positive claim is limited to the declared two-regime, one-probe,
one-tail-decision host; the fixed train/test period schedules; six Bernoulli
probe marks; the three persistence panels; the stated FP32 learner, seeds and
budget; and expected external utility under the complete held-out population.
It can establish persistence-specific net acquisition and, conditionally, a
finite-budget count-summary advantage over this RAW learner.

It cannot establish that counts are necessary, superiority over arbitrary
sequence or Bayesian methods, open-ended exploration, general variable-`k`
control, variable-`N` handling, multi-agent coordination, nonstationary regime
tracking, safety, cryptographic or lifecycle validity, UAV transfer, deployment
value, or real-world energy/QoS improvement.

## Stop rule and next scientific boundary

The exhaustive map above is the stop rule. In summary, this fixed host is
terminal after every complete technically valid run, including support,
competence, acquisition, specificity and RAW-containment outcomes. Acquisition
or specificity failure stops learned UCOPE. RAW equivalence, RAW superiority,
permutation containment, held-out-only attribution or an unresolved interval
prevents a broad independent count-summary claim.

Only acquisition success with a robust COUNT-over-RAW residual can make a
separately authorized dynamic service/roster object eligible. Eligibility is
not allocation, construction, rerun, or evidence transfer. Any successor is a
new object requiring a complete card and Pro closure.

## Concrete UAV mapping

The finite mapping is prospective:

- `Theta`: a slowly changing link, sensing, interference or target-service
  condition that persists across one decision renewal;
- probe marks `Yi`: successful diagnostic packets, detections or service hits
  over six declared opportunities and exposure `E=6`;
- `k`: sensing dwell, relay commitment, coverage interval or handoff-hold time;
- `probe_service`: useful packets/detections delivered during diagnosis;
- `probe_time` and `probe_energy`: latency and energy spent before commitment;
- `tail_service`: subsequent QoS/coverage/connectivity success under the chosen
  dwell; and
- REDRAW/SEVERED: loss of temporal persistence or loss of valid association
  between the measurement ledger and the current service regime.

A later UAV object must construct genuine multi-UAV contention, roster and
physical dynamics, and must re-establish the information/service/cost
decomposition. No current UAV code, flight process, radio model, fleet result or
deployment claim is part of R01.

## Owner boundary

The same-direction EM owns this science definition, provider questions,
closure intake and later result interpretation. Portfolio alone decides whether
to allocate engineering. A matching CM would own construction and technical
acceptance only after an exact owner-artifact handoff. Operational Root would
own any later compute lease, Operator, Git integration or publication. None is
authorized by this card.



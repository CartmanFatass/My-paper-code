# DISH RBHR r03 learned training and population manifest

```text
document_kind=direction_science_training_population_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-03
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

## 1. Shared learned graph

Each of the five arms is trained separately but uses the identical graph:

```text
e(o)=tanh(W2*tanh(W1*o+b1)+b2),  W1 and W2 each width 128
h[n]=GRU_128(e(o[n]),h[n-1])
```

There is no dropout or layer normalization. Motion, prepare, commit,
prediction and masked FLEX heads are linear maps from `h`. The centralized
training-only critic is two `128`-unit tanh layers followed by one scalar and
receives the same causal-past privileged vector in every arm. It never enters
deployment.

At ordinary renewals, each physical motion action is a diagonal Gaussian with
mean `3*tanh(m)` and learned global log standard deviation clipped to `[-5,1]`,
initialized to `-0.5`. Prepare and commit are Bernoulli. Training samples all
unmasked decisions from the arm-addressed policy stream. Evaluation uses the
Gaussian mean and Boolean probability `>=0.5`. Held ticks introduce no new
policy sample or log probability. All arm masks are applied after the common
heads execute.

Every matrix uses Xavier-uniform

`Uniform[-sqrt(6/(fan_in+fan_out)),+sqrt(6/(fan_in+fan_out))]`

from its arm substream; biases are zero. Each GRU gate matrix is initialized
separately by that rule. The FLEX-extra output matrices and biases alone start
at exact zero, placing FLEX at `(0,1,0,0)` before learning. No parameter is
copied between trained arms.

## 2. Reward and auxiliary labels

The shared primitive team reward is exactly

`reward[n]=valid_service[n]`.

There is no energy, byte, handover, trigger, predictor, regime, `k`, event or
treatment-specific shaping. Absorbing post-terminal ticks have reward zero.

The common auxiliary head is trained from four equally weighted pieces:

1. bivariate Gaussian negative log likelihood of next-tick target position;
2. mean univariate Gaussian negative log likelihood of next-tick
   responder-to-candidate and candidate-to-base margins;
3. next-tick camera-missingness binary cross entropy; and
4. mean binary cross entropy of `q_1,...,q_20` against the twenty passive
   candidate-service labels.

The passive label at horizon `j` is computed training-only by cloning the
current causal state, assigning the standby as sole owner, holding the stored
candidate command, applying the frozen physical tape for `j` ticks and scoring
the literal service recurrence. It does not optimize, branch on the label or
feed a future value to the policy. A physical terminal makes that and later
labels zero. Let the mean of the four normalized pieces be `L_aux`; its total
coefficient is `0.1`. Evaluation never computes a label.

## 3. Primitive-time recurrent PPO

Use

```text
gamma=exp(-0.1/20)
GAE lambda=0.95
PPO ratio clip=0.20
value-loss coefficient=0.50
entropy coefficient=0.01
auxiliary coefficient=0.10
value prediction clip=0.20
global gradient-norm clip=0.50.
```

With old-policy value `V_old`, physical/horizon done flag `d_n`, and primitive
return target `R_n`:

```text
delta_n = reward[n]+gamma*(1-d_n)*V_old(s[n+1])-V_old(s[n])
A_n     = delta_n+gamma*0.95*(1-d_n)*A[n+1]
rho_n   = exp(log pi_theta-log pi_old)
L_policy=-mean(min(rho*A,clip(rho,0.8,1.2)*A))
V_clip  =V_old+clip(V-V_old,-0.2,0.2)
L_value =mean(max((V-R)^2,(V_clip-R)^2))
L_total =L_policy+0.5*L_value-0.01*entropy+0.1*L_aux.
```

GAE is computed on primitive ticks. The policy term is masked to actual
behaviorally effective renewal decisions; the value term uses every live or
absorbing tick, with zero target after terminal, and the auxiliary term uses
live ticks only.
Advantages over renewal decisions in one collected 4,096-transition batch are
centered and divided by their population standard deviation; if it is below
`1e-8`, all normalized advantages are zero. Physical terminal and tick 1199
set `d=1`; an update-boundary truncation bootstraps from `V_old` and the episode
continues.

Each update performs four epochs. In each epoch the 4,096 transitions are
partitioned into eight minibatches; each minibatch has eight recurrent
fragments of 64 consecutive ticks (`8*64=512`). Stored hidden state initializes
each fragment, gradients stop at fragment boundaries, and episode/reset masks
prevent cross-episode recurrence. A counter-keyed permutation of fragments is
fresh per epoch. There are exactly `32` optimizer steps per update.

AdamW has constant learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`,
and weight decay `1e-4` on weight matrices only. Biases, log standard deviations
and normalization statistics have zero decay. There is no learning-rate
schedule, KL early stop, gradient accumulation, reward/return normalization,
checkpoint selection or hyperparameter search.

## 4. Observation normalization and checkpoint

Per arm, Welford mean/variance statistics are pooled across physical roles and
controller copies. A rollout uses the statistics frozen at its start; after
collection, live continuous observations update them in lane-major then
tick-major order. Continuous normalized values are clipped to `[-10,10]`;
Boolean and one-hot fields are not normalized. Statistics freeze permanently
after update 1,024 and are part of the checkpoint.

Every arm performs exactly `1,024` updates of `4,096` primitive transitions,
or `4,194,304` transitions. The sole registered checkpoint is the parameters,
optimizer state and normalization state immediately after update 1,024. No
intermediate checkpoint may be selected or adapted for evaluation.

## 5. Sealed training allocation

Each arm in each replicate block uses `32` synchronized lanes and collects
`128` consecutive primitive ticks per lane per update:

| package | schedule | lanes | transitions/update |
|---|---:|---:|---:|
| visual mask | `k=4` | 4 | 512 |
| visual mask | `k=12` | 4 | 512 |
| visual mask | `4->12` | 4 | 512 |
| visual mask | `12->4` | 4 | 512 |
| relay mask | `k=4` | 4 | 512 |
| relay mask | `k=12` | 4 | 512 |
| relay mask | `4->12` | 4 | 512 |
| relay mask | `12->4` | 4 | 512 |

Episodes always consume all 1,200 ticks; terminal creates the registered
absorbing tail and never an early reset. Lanes continue across update boundaries
and reset only after tick 1199. The final update stops after its 4,096th
transition even if its current episodes are incomplete.

Training tapes are unrejected base-generator draws. Advantage strata, learned
competence, opportunity and outcome never select them. For the four lanes of a
regime/schedule cell, successive episode waves enumerate counter-keyed random
permutations of

```text
Omega_4       ={42,54,66} x {0,...,3}
Omega_12      ={42,54,66} x {0,...,11}
Omega_4_TO_12 ={42,54,66} x {36,48,60,72} x {0,...,3}
Omega_12_TO_4 ={42,54,66} x {36,48,60,72} x {0,...,11}.
```

For episode wave `e` and lane-within-cell `r=0,...,3`, use permutation entry
`j=4e+r`; after exhausting an Omega set, advance the addressed cycle number and
use a fresh permutation. Every complete cycle is exactly Cartesian-balanced;
an incomplete prefix differs by at most one occurrence. Route/noise/initial
draws are fresh at every lane episode. A physical tape is matched across the
five arms within one block but never reused across block, coordinate, training,
evaluation or candidate attempt. Arm labels are assigned once per block to the
five independent substream slots by the host manifest.

## 6. Evaluation population

There are `24` independently trained/evaluated replicate blocks. Each block
trains STRUCTURED, FLEX, NEVER, IMMEDIATE and HYSTERESIS from its assigned
independent arm initialization/action/minibatch substream on matched physical
tapes. Evaluation is deterministic under the rule in section 1.

For each block, each of the two regime packages and each evaluation schedule
`{k=4,k=8,k=12,4->12,12->4}`, the host supplies 48 accepted degraded tapes:
16 POSITIVE, 16 NEAR-ZERO and 16 NEGATIVE. Each has its exact mask-off paired
view. Every learned arm receives every tape. The complete panel, including
terminal, nontrigger, nonrecapture and failed-gate trajectories, is indivisible.

Fixed `k=4,12` cells are calibration-only. Claim-bearing branch cells are

`c=(regime, schedule in {k=8,4->12,12->4}, advantage stratum)`.

Renewal phase is balanced and is diagnostic only. A branch atomic supercell is
`u=(regime,claim schedule)` evaluated jointly over its three advantage strata.

## 7. No-degradation and pre-onset competence block values

For arm `a`, block `b`, regime `r`, calibration schedule
`s in {k=4,k=12}` and stratum `z`, define

```text
C_ND[a,b,r,s,z]
 = (1/16) sum_tape [(1/1200) sum_{n=0}^{1199}
                    valid_service_MASK_OFF[a,tape,n]].
```

For each claim cell `c=(r,s,z)`, define

```text
C_PRE[a,b,c]
 = (1/16) sum_tape [(1/200) sum_{n:tau_d-20<=n*dt<tau_d}
                    valid_service_MASK_ON[a,tape,n]].
```

All allowed `tau_d` exceed 20 seconds. Mask-on and mask-off exogenous histories
are identical through the tick before `tau_d`; any earlier divergence is
protocol invalidity. The simultaneous competence gate requires every one of
the five arms, not only STRUCTURED, NEVER and FLEX.

## 8. Population and training prohibitions

No evaluation fine-tuning, per-`k` head, normalization update, stochastic test
action, early stop, checkpoint choice, arm-specific reward, training stratum
rejection, tape replacement or result-driven lane allocation is legal. Any
change to the objective, numerical optimizer law, training allocation, counts,
checkpoint or population is a complete new science revision.

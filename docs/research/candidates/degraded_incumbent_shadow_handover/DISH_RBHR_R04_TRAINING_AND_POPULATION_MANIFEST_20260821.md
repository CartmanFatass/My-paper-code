# DISH RBHR r04 learned training and population manifest

```text
document_kind=direction_science_training_population_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-04
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

## 1. Shared learned graph

Each of the five arms is trained separately but uses the exact 54-component
actor vector, explicit encoder/GRU equations, snapshot bridge, head authority
and exact critic vector in the controller manifest. There is no dropout or
layer normalization. Motion, prepare, commit, four-state prediction, link,
missingness, service-probability and masked FLEX heads are linear from the
specified recurrent copy. The centralized critic never enters deployment.

At ordinary renewals, the two physically authoritative motion outputs form one
four-dimensional diagonal Gaussian with mean `3*tanh(m)` and four learned
global log standard deviations clipped to `[-5,1]`, each initialized `-0.5`.
When the controller manifest binds a preceding readiness record, its final
candidate mean—including FLEX beta when applicable—is the standby component of
this Gaussian and of its PPO log likelihood.
Prepare and commit are Bernoulli. Training samples all
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

Each copy predicts quantities for its attached physical UAV. For a live tick
`n`, let target label
`y_x=[g_x,g_y,gdot_x,gdot_y]` at tick `n+1`. The head emits a current-tick
boundary-propagatable `(m_x,P_x)`; form
`m_next=F*m_x`, `P_next=F*P_x*F^T+Q`, and

`NLL_x=0.5*((y_x-m_next)^T P_next^-1(y_x-m_next)+log det(P_next)+4 log(2*pi))`.

The target/link/missing heads run on every copy for its attached vehicle. The
two link heads predict that vehicle's responder-to-UAV and UAV-to-base
tick-`n+1` margins. Each emits mean `mu_l` and
`sigma_l=softplus(raw_sigma_l)+1e-3`, with

`NLL_l=0.5*(((y_l-mu_l)/sigma_l)^2+2 log sigma_l+log(2*pi))`.

The missingness label is that vehicle's camera-missing bit at `n+1`, trained by
binary cross entropy. `q_1,...,q_20` are trained against one coherent 20-tick
clone, not separately reset horizons. For a readiness-label origin tick `r`,
the clone starts from the complete causal state, advances the exact one-tick
message pipeline, hypothetically applies the legal standby-owner CAS at tick
`r+2`, and then executes the literal host/tick recurrence on the same future
physical tape. Before a candidate command exists it holds the standby's current
command; otherwise it holds the readiness record's stored candidate command.
Its labels are the twenty consecutive service bits on `r+2,...,r+21`.
Terminal makes that and later bits zero. The q loss is masked after
`handover_used=1`, at terminal, or whenever a unique legal hypothetical
standby-owner state/buffer lineage through `r+2` does not exist. The clone never
feeds a future value to policy input.

`L_target` is the arithmetic mean of `NLL_x` over live copy/ticks;
`L_link` the arithmetic mean of both link NLLs; `L_missing` the mean BCE; and
`L_passive` the mean of the twenty BCE terms from the physically authoritative
standby-shadow copy over unmasked examples. If a piece
has zero eligible examples it is zero and contributes no gradient. Exactly

`L_aux=(L_target+L_link+L_missing+L_passive)/4`,

with total coefficient `0.1`. Evaluation computes predictions but no labels or
auxiliary loss.

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

With old-policy value `V_old`, physical/horizon done flag `d_n`, raw
unnormalized GAE `A_raw[n]` and primitive return target
`R_n=A_raw[n]+V_old(s[n])`:

```text
delta_n = reward[n]+gamma*(1-d_n)*V_old(s[n+1])-V_old(s[n])
A_raw[n]= delta_n+gamma*0.95*(1-d_n)*A_raw[n+1]
rho_n   = exp(log pi_theta-log pi_old)
L_policy=-mean(min(rho*A_policy,clip(rho,0.8,1.2)*A_policy))
V_clip  =V_old+clip(V-V_old,-0.2,0.2)
L_value =mean(max((V-R)^2,(V_clip-R)^2))
L_total =L_policy+0.5*L_value-0.01*entropy+0.1*L_aux.
```

GAE is computed on primitive ticks. Advantage normalization affects only the
policy term: over all active renewal decisions in one 4,096-transition batch,
center `A_raw` and divide by its population standard deviation; if below
`1e-8`, use zero normalized advantages. `R_n` remains unnormalized.

At a live renewal the joint log likelihood is the sum of raw, pre-projection
log probabilities for exactly the stochastic dimensions that can alter the
registered trajectory:

- both authoritative two-dimensional motion Gaussians in every arm;
- STRUCTURED/FLEX/NEVER prepare Bernoulli only when its applicable G latch is
  true and preparation is not yet latched;
- STRUCTURED/FLEX commit Bernoulli only when all non-commit origin-certificate
  predicates are true, so a true bit emits COMMIT_INTENT;
- NEVER commit/NOOP Bernoulli under the same non-commit mask; a true bit emits
  the behaviorally live equal-size NOOP_INTENT and therefore enters likelihood
  and entropy;
- no learned prepare/commit likelihood for IMMEDIATE or HYSTERESIS.

Held, terminal and hard-masked decisions contribute zero policy loss and zero
entropy. Entropy is summed over exactly those same active raw dimensions before
the batch mean. The likelihood is never evaluated on projected commands.
The value term uses every live or absorbing tick, with zero target after
terminal, and auxiliary terms use live ticks only. Physical terminal and tick
1199 set `d=1`; an update-boundary truncation bootstraps from `V_old` and the
episode continues.

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

Per arm, separate actor, snapshot-encoder and critic Welford states use the exact initialization,
unbiased variance, epsilon, sentinel/present-bit and clipping law in the
controller manifest. Actor statistics pool physical roles/copies dimensionwise;
snapshot statistics use accepted snapshots in delivery order; critic statistics
use their own ordered dimensions. A rollout freezes its
start statistics; afterward live continuous values update in lane-major,
tick-major, physical-UAV, copy-I-then-S order, with the critic updated once per
lane/tick. Statistics freeze permanently after update 1,024 and are checkpointed.

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

For episode wave `e` and lane-within-cell `r=0,...,3`, let `m=4e+r`, use
permutation cycle `floor(m/|Omega|)` and entry `m mod |Omega|`. Every complete
cycle is exactly Cartesian-balanced;
an incomplete prefix differs by at most one occurrence. Route/noise/initial
draws are fresh at every lane episode. A physical tape is matched across the
five arms within one block but never reused across block, coordinate, training,
evaluation or candidate attempt. Arm labels are assigned once per block to the
five independent substream slots by the host manifest.

Independently of the Omega permutation, the three bits of `m mod 8` bind
training identity in this order: bit 0 selects reflection `+1` then `-1`; bit 1
selects initial owner UAV0 then UAV1; bit 2 assigns `q_A` to UAV0 then UAV1
(with `q_B` assigned to the other). Every eight consecutive lane episodes
contain all eight combinations exactly once. No training identity draw exists.

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

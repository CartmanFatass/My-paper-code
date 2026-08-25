# DISH RBHR r03 treatment, comparators and executable certificate

```text
document_kind=direction_science_treatment_comparator_certificate_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-03
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
successful_handover_limit_per_trajectory=1
```

This file fixes controller authority, message cadence, handover logic, the
certificate and literal FLEX containment. All five learned arms use the same
observation and full tensor graph; masks below change only the named behavior.

## 1. Controller copies and physical authority

For each physical vehicle `i in {0,1}`, maintain weight-tied recurrent states
`h_i^I,h_i^S in [-1,1]^128`. All four states update on every live primitive
tick from the same shaped causal observations and their role bits. Let `o_n` be
the unique service owner and `s_n=1-o_n`.

Before a successful commit:

```text
applied_motion(o_n)=P_n(A_theta(h^I_{o_n}))
applied_motion(s_n)=P_n(A_theta(h^S_{s_n})).
```

Only `h^I_{o_n}` may originate a scored SERVICE_RELAY. `h^S_{s_n}` drives the
standby's motion, snapshot assimilation and readiness messages, but no scored
payload. The two other copies compute for matched graph cost but cannot actuate,
send a scored payload or affect the arbiter. This mapping applies to
STRUCTURED, FLEX, NEVER, IMMEDIATE-ELIGIBLE and FIXED-HYSTERESIS.

At an ordinary renewal `n`, a legal intent is transmitted during tick `n` and,
if delivered, proposes a compare-and-swap at the start of tick `n+1`. The old
owner remains exclusive through tick `n`; a successful new owner is exclusive
from tick `n+1`. At that boundary the transaction moves

`(owner,service_epoch,next_payload_sequence,handover_used)`

atomically, increments `service_epoch`, preserves both UAV SOURCE buffers and
the base buffer, and sets `handover_used=1`. The prepared standby copy is
promoted:

```text
h^I_{s,+}=P_h(alpha*h^S_{s,-}+(1-alpha)*h^I_{o,-})
h^S_{o,+}=h^I_{o,-}; h^S_{s,+}=h^S_{s,-}; h^I_{o,+}=h^I_{o,-},
P_h(x)=componentwise_clip(x,-1,1).
```

STRUCTURED and both simple rules use `alpha=1`. The former owner is demoted at
the same boundary. Every later transfer is ineligible in every arm and branch.
Revision 03 permits at most one successful handover per episode in every
STRUCTURED, FLEX, simple-rule and fork trajectory.

## 2. Causal degradation and preparation clocks

The common deployable Boolean is

`D[n]=1{current owner camera is missing OR current owner-to-base margin<6 dB}`.

It is independent of the hidden regime and `tau_d`. From reset define

```text
G1[n]=max_{0<=j<=n} D[j]
G5[n]=1 iff at least one run D[j]=...=D[j+4]=1 ends by n.
```

STRUCTURED, FLEX, NEVER and IMMEDIATE use `G1`; FIXED-HYSTERESIS uses `G5`.
The simple rules therefore require respectively at least one indicator tick or
five consecutive primitive indicator ticks. No evaluator onset enters either
rule.

At an ordinary renewal after its applicable latch is true:

- STRUCTURED, FLEX and NEVER latch preparation only if their sampled/evaluation
  prepare bit is one;
- both simple rules latch preparation unconditionally; and
- once latched, preparation persists to handover, terminal or episode end.

A `k` switch does not reset a recurrent state, filter or warmup clock, but it
invalidates a stored certificate until a snapshot bearing the new `k` epoch is
accepted.

## 3. Exact control-message state machine

After preparation latches at tick `n_0`, the current owner attempts one
`96-byte SNAPSHOT` to the standby at ticks `n_0,n_0+5,n_0+10,...` while live,
and additionally at the first live tick of a new `k` epoch if that tick is not
already scheduled. It contains

```text
(owner_id,service_epoch,next_payload_sequence,current owner SOURCE sequence,
 target-prediction mean,covariance,link state,snapshot_tick,k_epoch).
```

The opaque SOURCE body is not included. The attempt uses owner-to-standby radio
physics and is delivered one tick later. A delivered snapshot is accepted only
if owner, service epoch, next payload sequence and `k` epoch still match and
both UAV SOURCE buffers exist with equal source sequence. Otherwise it is
discarded.

After the first accepted snapshot the standby attempts one `48-byte READINESS`
to the owner on every live tick. The owner holds a capacity-one readiness
buffer, replacing it only with a delivered, matching, later readiness tick.
The message includes the accepted version tuple, current prediction summary
and commit-head bit. Warmup `w` is the count of
consecutive shadow updates since the first accepted current-owner snapshot; it
resets on episode reset, owner/service-epoch change or snapshot age exceeding
five ticks, but not merely on a `k` switch. A new-epoch snapshot is still
required for eligibility.

At an eligible ordinary renewal, STRUCTURED or FLEX attempts one `24-byte
COMMIT_INTENT` iff its commit bit is one. A simple rule attempts it at its first
common-certificate-eligible renewal. NEVER computes the same latent intent and,
when that bit is one, transmits an equal-size `NOOP_INTENT` explicitly marked
`request_transfer=false`; it cannot enter the compare-and-swap or count as an
invalid transfer request. A delivered transfer intent is validated at the
start of the next tick. The
then-owner emits one `24-byte COMMIT_RESULT` broadcast recording success or
failure. No hidden acknowledgement or retry exists.

## 4. Prediction outputs and fail-closed certificate

Each copy's shared prediction head emits next-tick target mean `mu in R^2` and
lower-triangular covariance factor

```text
L11=softplus(l11)+1e-3
L21=l21
L22=softplus(l22)+1e-3
P=L L^T+1e-4 I_2.
```

The owner snapshot prediction and standby-local prediction are propagated to
the same candidate boundary. With `S=P_owner+P_standby+1e-6 I_2`,

`d_M^2=(mu_owner-mu_standby)^T S^{-1}(mu_owner-mu_standby)`.

The inverse is evaluated by Cholesky solve. A failed factorization or any
nonfinite input makes the predicate false.

The auxiliary head also emits `q_1,...,q_20` clipped to
`[1e-6,1-1e-6]`, causal probabilities of valid service if the standby became
owner and held the stored candidate command during each of the next 20 ticks.
The training manifest fixes its labels and loss. With the registered
Poisson-binomial convention, start `p_0^(0)=1` and recurse

`p_m^(j)=(1-q_j)p_m^(j-1)+q_j p_(m-1)^(j-1)`

with out-of-range terms zero. Define the one-sided 95% predictive lower score

`Q95=(1/20)*max{m in 0,...,20: sum_{ell=m}^{20}p_ell^(20)>=0.95}`.

Let `x^-_{n+1}` be the exact causal host state obtained by holding the current
owner command and the stored standby candidate command through tick `n`, with
no future noise substituted. At renewal `n` define:

```text
RENEW  = ordinary renewal at n
UNUSED = handover_used=0
MATCH  = owner, service epoch, next payload sequence, equal nonempty SOURCE
         sequence and current k epoch all match the accepted snapshot/readiness
AGE    = n-snapshot_tick<=5 and n-readiness_tick<=2
WARM   = w>=10 primitive ticks
MAHA   = d_M^2<=5.99
PRED   = Q95>=0.60
MAINT  = x^-_{n+1} is nonterminal, preserves one owner and permits the current
         owner to send through tick n
SEP    = predicted boundary separation>=15 m
SLEW   = both unprojected candidate command changes have norm<=1.5 m/s^2.
```

The common certificate is the conjunction of those ten predicates and the
applicable `G1` or `G5`. It is false on any absent, stale, mismatched, singular
or nonfinite value. Common acceleration norm/slew projection is still applied
after the check. Certificate evaluation uses only causal state at `n`; neither
future noise nor hidden evaluator labels enter it.

## 5. Named arms

- `PHYSICS-CERTIFIED-SHADOW-HANDOVER` (`STRUCTURED`) uses learned prepare and
  commit bits plus the common certificate and the promotion law at `alpha=1`.
- `FLEXIBLE-SHADOW-CONTAIN` (`FLEX`) uses the same law with only the four
  unmasked freedoms in section 6.
- `NEVER-HANDOVER` uses the full graph, dual-state motion, message state
  machine, prediction, latent intent and charges, but masks every effective
  compare-and-swap false. The initial owner remains the payload owner.
- `IMMEDIATE-ELIGIBLE` ignores the effective learned prepare/commit bits,
  prepares after `G1`, and transfers at the first renewal at which its common
  certificate is true.
- `FIXED-HYSTERESIS` is identical except it prepares after `G5` and transfers
  at the first renewal at which its certificate is true.

All five arms are separately trained with matched physical tapes, architecture,
updates and optimizer law. Evaluation uses each arm's own checkpoint; no
post-hoc override counts.

## 6. Literal FLEX superset

All arms instantiate the four extra raw heads, but non-FLEX arms mask them to
the constants below. FLEX exposes

```text
DeltaI=0.25*tanh(u_I) in (-0.25,0.25)^128
alpha=1+tanh(u_alpha) in (0,2)
r=0.25*tanh(u_r) in (-0.25,0.25)
beta=tanh(u_beta) in (-1,1).
```

At first snapshot acceptance,

```text
h_shadow_STRUCT=P_h(h_bar)
h_shadow_FLEX=P_h(h_bar+DeltaI).
```

At commit FLEX uses the `alpha` state equation in section 1. Its readiness is
`Q_F=clip(Q95+r,0,1)` and eligibility substitutes `Q_F>=0.60`; its commit logit
is `ell_commit_F=ell_commit+4r`. If `m_o,m_s` are incumbent and shadow raw
boundary-action means, FLEX uses

`m_boundary_F=m_s+beta*(m_o-m_s)`

before Gaussian sampling, norm clipping and the common slew projection.
Subsequent commands use the promoted state normally. Residuals act before all
common certificate and physical projections; they cannot bypass hard
one-owner, epoch, sequence, terminal, separation or slew predicates.

The STRUCTURED embedding copies every shared weight and sets the four extra
head outputs to `(DeltaI,alpha,r,beta)=(0,1,0,0)`. For an identical causal
history and coupled action draw, first-snapshot states are then equal; the GRU
recurrence preserves equality; readiness, messages and eligibility are equal;
the boundary raw action is equal; common projection preserves it; and the same
compare-and-swap produces equal token, payload-sequence, buffers, promoted
states and future physical actions. Induction over ticks proves componentwise

`FLEX(h;0,1,0,0)=STRUCTURED(h)`

for recurrent states, messages, eligibility, payload state, token state and
physical actions. A later static/emulation check tests conformance but does not
define containment.

## 7. Matched first-trigger REAL/SHAM fork

The primary trigger population is fixed in the inference manifest. Immediately
before the eligible STRUCTURED intent is applied, clone every physical state,
all four recurrent/filter states, normalization state, buffers, token/version
state, held commands and the complete remaining exogenous tape.

- `FORK-REAL` performs the exact STRUCTURED promotion and owner transfer.
- `FORK-SHAM` performs the identical comparisons, messages, latency, byte and
  energy debit and increments a sham transaction counter, but keeps owner,
  service epoch, payload pointer, active incumbent state and actuator mapping
  unchanged. Its nominal promoted state is an exact clone of the incumbent and
  has no behavioral authority.

Both run exactly 100 ticks, prohibit a second transfer, preserve terminal
absorption and use the identical future physical tape. The fork is a pair of
potential outcomes, not a randomized assignment law.

## 8. Deployable information boundary

Policy inputs are only local/partner geometry, camera observation or
missingness, camera-filter belief, radio margins, SOURCE arrival metadata,
base-packet age acknowledgement, battery, separation, owner/service/`k` epoch,
causal control messages, current `k` and renewal phase. They exclude opaque
SOURCE coordinates, true regime, advantage stratum, target future, future `k`,
future radio/noise, scripted action, counterfactual outcome, remaining episode
time, block/seed/address and hidden ground truth. The centralized critic may
receive identical causal-past privileged state during training only.

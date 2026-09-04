# DISH ridge-bend hot-standby relay science card — revision 05

```text
document_kind=direction_science_card
direction_id=degraded_incumbent_shadow_handover
object=DISH-EXTERNAL-K-SHADOW-HANDOVER-DEFINITION
revision=DISH-RBHR-SCIENCE-20260821-05
host=RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3
science_owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
portfolio_owner=Dedicated Portfolio session 019ffc20-5001-7453-a08a-dac783cf4d80
operational_root=019fff33-ac9b-7433-b6d8-42c810dec99c
stage=definition-only
mathematical_closure=false
empirical_activity_authorized=false
construction_authorized=false
cross_direction_evidence_transfer=false
```

## 1. Complete replacement and controlling packet

Revision 05 is one complete, single-valued replacement for r04. R01 through r04
remain immutable and supply no default for r05. The controlling r05 composite is
exactly this card plus:

- `DISH_RBHR_R05_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md`;
- `DISH_RBHR_R05_TOTAL_RNG_ALLOCATION_TABLE_20260821.md`;
- `DISH_RBHR_R05_PAYLOAD_SERVICE_TICK_AND_COST_RECURRENCE_20260821.md`;
- `DISH_RBHR_R05_CONTROLLER_TREATMENT_COMPARATORS_AND_CERTIFICATE_20260821.md`;
- `DISH_RBHR_R05_TRAINING_AND_POPULATION_MANIFEST_20260821.md`; and
- `DISH_RBHR_R05_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md`.

All seven are normative and indivisible. They use the same symbols and have no
discretionary precedence; any disagreement is
`INVALID_PROTOCOL_OR_MEASUREMENT`. A later CM may choose a numerically
equivalent implementation but may not fill, tune or resolve a scientific
choice.

## 2. Exact question and value criterion

The question is whether a single shared two-UAV policy can preserve direct
physical responder-to-UAV-to-base service when externally fixed or switched
skill period `k` changes decision renewal duration, by preparing a second
causal recurrent controller while the incumbent remains sole service owner and
then applying at most one certified atomic first handover.

The treatment is valuable only if all of the following survive the registered
gates and simultaneous inference:

1. the complete STRUCTURED package improves direct service/tail robustness over
   competent NEVER-HANDOVER;
2. the paired first-trigger REAL branch improves over an identical SHAM
   transaction, isolating application of the prepared standby from bookkeeping;
3. neither independently trained deployable simple rule is sufficient;
4. competent FLEX does not establish value for its broader freedom over the
   restriction; and
5. continuity and energy nonharm hold.

The panel distinguishes package value, first actuation value, simple timing,
strict-containing flexibility, opportunity, competence and support. It does
not claim unique mediation among learned state, geometry, prediction, timing or
communication.

## 3. Exact physical task

The host is a `0.1 s`, `120 s`, two-UAV planar ridge-bend task at fixed
`90 m` altitude. UAV speed is at most `18 m/s`, acceleration at most
`3 m/s^2`, command slew at most `1.5 m/s^2` per tick, and required separation
at least `15 m`. The host manifest fixes the terrain, route, ray sampler,
camera and radio laws, packet-addressed noise, initial states, reflection,
clock balance and generator order.

There are two and only two claim packages:

- `TARGET-VISUAL-MASK-PACKAGE` adds an incumbent camera prism mask exactly for
  `tau_d<=t<tau_d+4.0 s` and adds no radio impairment; ordinary radio failure
  remains possible.
- `TERRAIN-RELAY-MASK-PACKAGE` adds an incumbent-to-base `35 dB` prism penalty
  on that same interval and adds no camera impairment; ordinary camera
  missingness remains possible.

The initially degraded physical UAV remains the intervention target after
handover. These are registered mask packages, not pure sensing-only or
relay-only regimes. No intervention is active before `tau_d`.

The responder route uses independent uniform speed/turn/sign draws and
left-continuous turn velocity; wind begins at zero. Package, onset, switch,
renewal phase, physical noise, role, reflection and candidate population are
selected before learned actions.
Neither provider review nor later behavior can select or replace a tape.

## 4. Direct service recurrence

Every live tick the responder attempts one opaque `40-byte SOURCE` packet to
each UAV. It contains a timestamped noisy responder position/velocity that UAV
controllers cannot decrypt. Each UAV keeps its own newest directly received
SOURCE packet. Only the current owner may wrap its local packet in one
`64-byte SERVICE_RELAY` attempt to the base. Both hops have one-tick latency
and delivery iff their physical margin is at least `6 dB`; there is no retry or
other loss law. The base keeps one lexicographically newest packet and never
clears it at handover.

At tick `n`, service is exactly

```text
valid_service[n]
 = 1{not terminal}
 * 1{a base packet exists}
 * 1{packet age<=0.5 s}
 * 1{propagated opaque-source position error<=8 m}
 * 1{stored responder-to-UAV margin>=6 dB}
 * 1{stored owner-to-base margin>=6 dB}.
```

Camera-only target filters drive controllers and certificate predictions; the
opaque payload cannot bypass visual missingness. Both UAVs also send charged
one-tick `64-byte STATE` partner messages. Snapshot, readiness, intent and
result sizes are `96`, `48`, `32` and `24` bytes. The payload/service
manifest fixes the tick order, source/filter recurrence, buffers, sequence and
epoch rules, loss, latency, energy, terminal tail and all cost indicators.

## 5. External skill period

A high-level motion/protocol command is zero-order held for `k` primitive
ticks. One parameter vector, normalization state and registered checkpoint per
arm is shared across all schedules. Current `k`, `k` epoch and ticks to the next
renewal are observed; future schedules are hidden.

- Training uses fixed `k=4`, fixed `k=12`, `4->12` and `12->4`.
- Claim schedules are held-out fixed `k=8`, `4->12` and `12->4`.
- Fixed `k=4,12` fresh evaluation cells are calibration-only.
- `tau_d in {42,54,66} s`; switched `tau_k in {36,48,60,72} s` is independently
  Cartesian-crossed; initial phase is balanced.
- Countdown `c[0]=phi` defines every renewal. A switch becomes pending at
  `t>=tau_k`, never truncates a command, and changes `k`/increments epoch before
  the first pending renewal's observation and action. Recurrent/filter/buffer
  state persists, but old-epoch readiness expires.

No per-`k` policy, head, checkpoint, fine-tuning, normalization or evaluation
adaptation is legal.

## 6. Structured first handover

Both weight-tied controller copies update every tick. Before commit, the
incumbent copy drives incumbent motion and is the only scored-payload authority;
the standby shadow copy drives standby motion and readiness only. A successful
boundary compare-and-swap promotes the prepared standby copy and transfers
owner, service epoch and next payload sequence atomically while demoting the
former owner. Both local SOURCE buffers and the base buffer persist. The old
owner serves through the preceding tick and the new owner alone begins on the
next tick. There is no blackout, dual owner, dual payload, buffer clear, action
interpolation or extra decision instant.

The deployable degradation bit is current-owner camera missing OR current-owner
base margin below `6 dB`. STRUCTURED may prepare after one such tick. Its
complete 54-field observation, one-tick partner STATE channel, explicit GRU,
message encoders, critic and normalization are fixed. Four-state prediction
means/covariances propagate to the application boundary before the
Mahalanobis-`5.99` test; the twenty-tick predictive 95% lower service score must
be at least `0.60`. An origin-renewal certificate is stored in the intent;
one tick later a distinct application predicate validates exact post-reservation
versions, locked SOURCE lineage, terminal/maintainability, separation and slew.
Every absent, stale, mismatched, singular or nonfinite value fails closed.

Version headers remain deterministic-arbiter metadata. The learned snapshot
encoder receives exactly the four prediction means, ten ordered covariance
entries, two owner margins and two raw boundary-action means—no physical
identity, absolute tick, epoch or sequence header. Snapshot next-sequence is
checked only when that snapshot is accepted and is historical thereafter;
origin matching uses the newest readiness's own sequence version. Covariance
factor and wire orders, first-snapshot FLEX `DeltaI` evaluation from the
pre-assimilation prior state, and the exact pre-projection/sample/norm/slew
action domains are fixed in the controller manifest.

## 7. Controls

### FLEX strict container

FLEX differs only by four unmasked functions:

```text
DeltaI=0.25*tanh(u_I)
alpha=1+tanh(u_alpha)
r=0.25*tanh(u_r)
beta=tanh(u_beta).
```

They respectively perturb first shadow initialization, promoted-state blend,
readiness/commit score and first boundary action blend before common hard
projections. At `(0,1,0,0)`, pointwise induction gives exact equality to
STRUCTURED for recurrent states, messages, certificate, eligibility, payload
and token state and physical actions. FLEX therefore strictly contains the
treatment. A structured-over-FLEX result can mean only finite-budget
regularization/learnability; FLEX superiority retains the broader family
without attributing which freedom matters.

### NEVER

NEVER computes the same complete graph, shadow motion, preparation, predictions
and same-size messages. Its behaviorally live learned commit bit emits an
equal-size nontransfer NOOP intent when true, while every owner compare-and-swap
is masked false. The NOOP has policy likelihood and byte/energy consequences
but no invalid-commit authority. The incumbent remains sole payload owner.

### Paired REAL/SHAM

At the first application-valid STRUCTURED transfer in the registered onset
window, clone after application-tick arrivals and immediately before CAS.
REAL performs the exact handover. SHAM pays the same transaction
messages/latency/energy and applies the same observable transaction shell:
both increment service epoch, set `handover_used`, complete preparation, reset
warmup, invalidate old versions and cease later transaction messages. REAL
alone changes owner, promotes the prepared recurrent state and remaps
actuators; SHAM leaves owner, active incumbent state and actuator mapping
unchanged. Both preserve every packet buffer and next sequence, run exactly
100 ticks, retain terminal tails and prohibit a second transfer.

### Simple rules

IMMEDIATE and HYSTERESIS are separately trained arms with the full graph and
common certificate. They prepare and transfer at the first certificate-eligible
renewal after respectively one indicator tick or five consecutive ticks, and
make a fresh eligible request at later renewals until at most one succeeds. A
rule is retained only if its own RULE-versus-NEVER value and nonharm pass and it
is simultaneously noninferior to STRUCTURED in every required supercell. If
both qualify, IMMEDIATE is the prospectively selected lower-memory rule.

## 8. Frozen learning law

All arms use the exact two-layer width-128 tanh encoder, displayed GRU-128 per copy, shared heads
and an identical two-layer centralized critic. Motion is diagonal Gaussian;
prepare/commit are Bernoulli; evaluation is deterministic. Primitive reward is
only `valid_service`. Return targets use raw GAE plus old value. PPO likelihood
and entropy include only raw trajectory-effective motion/prepare/commit
dimensions. The executable auxiliary averages four-state Gaussian target,
two-link Gaussian, next-missingness and one coherent twenty-tick passive-service
loss.

Training is exactly 1,024 PPO updates x 4,096 primitive transitions, with
`gamma=exp(-0.1/20)`, GAE `0.95`, clip `0.20`, value coefficient `0.50`, entropy
`0.01`, auxiliary `0.10`, value clip `0.20`, four epochs, eight 512-transition
recurrent minibatches per epoch, sequence length 64 and gradient norm `0.50`.
AdamW is `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, matrix-only weight decay
`1e-4`. Xavier-uniform initialization, Welford normalization, truncation/
bootstrap and the sole update-1024 checkpoint are literal in the training
manifest.

PPO replay is also literal: fragment-initial recurrent/protocol state and hard
host/delivery/CAS facts are detached; the four recurrent states, snapshot
assimilation, delayed learned message values, FLEX residuals and promotion
edits are replayed with current parameters inside each 64-tick fragment.
Learned float32 payloads use registered forward rounding with a straight-
through derivative, while headers and physical transitions remain
stop-gradient. Delayed commit and boundary-motion likelihoods are attributed
to the bound origin renewal. Learned log-standard-deviation parameters are
unconstrained AdamW variables with only a forward `[-5,1]` clamp. Auxiliary
labels have exact terminal and tick-1199 masking/absorbing rules.

Thirty-two persistent lanes allocate four lanes to each of two packages x four
training schedules and collect 128 ticks/lane/update. Full 1,200-tick episodes
continue across updates; terminal uses the absorbing tail. Training uses
unrejected base draws, prospectively balanced clock/phase permutations, an
independent exact eight-way reflection/owner/physical-ID cycle and no advantage
stratum.

## 9. Evaluation population and independent strata

There are 24 independent replicate blocks. Each trains all five arms on matched
physical tapes with independently permuted arm substreams. In each block,
regime and evaluation schedule, exactly 16 POSITIVE, 16 NEAR-ZERO and 16
NEGATIVE tapes are accepted before learned activity by the arm-independent
scripted transfer-versus-retain assay. The script, geometric/token admission,
five-second window, no-eligible rule, rejection cap, reflection and complete
RNG address are fixed in the host manifest.

The identical increasing-attempt acceptance law, thresholds, `100000` cap and
lowest-qualifying-attempt rule applies to calibration schedules `K4,K12` and
claim schedules `K8,K4_TO_K12,K12_TO_K4`; only the registered split coordinate
differs. Every training lane, Omega item and recurrent fragment has one fixed
global ordinal in the total RNG table.

Every accepted degraded tape has a mask-off pair sharing every exogenous draw.
Fixed `k=4,12` mask-off cells measure full-episode competence; claim cells use
exact pre-onset `[tau_d-20 s,tau_d)`. All five arms require simultaneous lower
bounds at least `0.90` no-degradation and `0.85` pre-onset. All accepted tapes
remain in the panel.

## 10. Opportunity, support and endpoints

After package-local competence, a separate causal finite-action scripted recovery witness
must establish paired NEVER degradation drop, five-tick maintainability,
at least `0.10` witness gain and hard continuity. Its per-tape indicator is
reduced within each block/cell and its simultaneous opportunity-fraction lower
bound must be at least `0.50`. It is a witness, never a ceiling.

Numerical headroom/precision is evaluated before adaptive support. STRUCTURED
and FLEX support must be between 10% and 90% of opportunity tapes,
with positive `1e-3` recurrent-state and action differences and at least one
trigger in every block/cell. NEVER event service must lie within `[0.25,0.85]`;
the witness gain lower bound must be at least `0.10`. Direct-effect interval
half-width must be no greater than its material margin. If adaptive support
fails, a simple rule can still be retained only through its own value/nonharm
and noninferiority fallback.

Full endpoints use the 200 ticks beginning at `tau_d`: MEAN-SERVICE,
fractional empirical worst-10% TAIL-SERVICE, `dt*sum(1-service)` DEFICIT and
first-invalid-to-start-of-ten-valid-ticks RECOVERY-DELAY with full-window cap.
The fork uses its 100 ticks. The inference manifest fixes every reducer and the
zero-trigger support convention.

## 11. Simultaneous inference and effect regions

The 24 blocks are the only clusters. One 99,999-resample, counter-keyed,
jointly paired nonparametric block bootstrap computes a maximum absolute
studentized statistic over every branch-changing gate, endpoint, cost and
unconditioned full-arm within-cell phase/energy diagnostic. Trigger-conditioned
REAL/SHAM phase diagnostics are excluded because their phase subsets need not
be populated; schedule-wide fork effects remain authoritative. The 95,000th
ordered maximum supplies one
common two-sided critical
value. Identical block values get point intervals; every other zero/nonfinite
case follows the fail-closed rule in the inference manifest.

Effects are benefit-oriented: treatment minus control for MEAN/TAIL and control
minus treatment for DEFICIT/DELAY. Full material margins are
`(0.03,0.05,0.50,1.0)` and fork margins `(0.03,0.05,0.25,0.5)`;
noninferiority margins are `(0.01,0.02,0.25,0.5)`. VALUE requires one POSITIVE
lower bound at its material margin and every stratum/endpoint lower bound above
the negative noninferiority margin. NO-MATERIAL, MATERIAL-HARM and
NONINFERIOR are literal interval predicates.

Full-arm energy uses the full 1,200 ticks and fork energy its 100 ticks. The
simultaneous upper bound on treatment-relative energy must be at most `0.03`;
the zero denominator rule is frozen. Invalid commits, token gaps, dual owner,
dual payload, buffer clears, slew breaches and separation breaches must be
exactly zero. Bytes and minimum separation are separately reported.

## 12. Exhaustive result law

Each `(regime,claim schedule)` supercell is classified independently, in this
first-match order:

1. invalid protocol/measurement;
2. package-local competence not established;
3. no registered recovery witness;
4. nonanswerable or no headroom;
5. adaptive-support failure, with independently qualifying simple-rule fallback
   tested before support-not-established;
6. target-specific S-N or REAL-SHAM harm/absolute nonharm failure;
7. full-package value with fork no-materiality: nonactuation package effect;
8. fork materiality excluded outside the global no-material pattern: shadow
   actuation nonpass;
9. independently valuable/nonharm/noninferior simple rule, IMMEDIATE tie first;
10. independently valuable FLEX-over-NEVER and FLEX-over-STRUCTURED;
11. FLEX-relative nonretention when FLEX materially/nonharmfully exceeds
    STRUCTURED but broader-family value versus NEVER is not established;
12. structured full and fork value only when direct FLEX-relative value is
    absent;
13. all registered effects no-material;
14. unresolved catch-all.

The complete Boolean definitions are in the inference manifest. They prevent
FLEX/simple comparisons from being shadowed by harm, put package effect before
actuation nonpass, and make no-material and unresolved disjoint.

Within a regime, the same retained class must pass all three claim schedules.
Structured value on all three yields `STRUCTURED_REGIME_SPECIFIC_VALUE`.
Fixed-`k=8` retained value without the same switched-schedule class yields
`FIXED_ONLY_NO_SWITCH_K_VALUE` with both failed labels. Cross-regime structured
value requires both regimes independently to pass all three schedules. One
failed schedule or regime never erases another cell's exact result.

## 13. Strongest alternatives

Even a positive exact result may be caused by favorable standby geometry,
generic two-vehicle redundancy, an immediate/hysteretic rule, message traffic,
the second recurrent state, predictor training, finite-budget FLEX
underoptimization, `k`-dependent latency/phase, event/role/token shortcuts,
correlated predictions, analytic terrain/radio boundaries, one advantage
stratum or one mask package. The registered controls narrow but do not prove
unique mediation.

## 14. Maximum claim and nonclaims

A positive result can support only finite-budget evidence that one shared
two-UAV policy in `RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3`, under the registered
fixed/held-out/switched `k` schedules and passing package/schedule/stratum cells,
improves direct service or tail robustness through the frozen first-handover
package against competent matched controls.

It cannot establish arbitrary/continuous `k`, variable `N`, convergence,
unique state-transfer/timing mediation, pure sensing or relay isolation, other
terrain/sensor/radio laws, aircraft transfer, safety, certification, deployment
or flight. It imports no result or claim from another HMASD direction.

## 15. Activity boundary and later technical question

Revision 05 is definition-only. Question-relevant activity begins with creation
of a non-fixture master, seed, coordinate, model initialization, checkpoint,
training rollout, evaluation trajectory or result-blind branch fixture for this
object. None is authorized.

If Portfolio later requests CM evidence, the exact technical question is:

> Is the complete `DISH-RBHR-SCIENCE-20260821-05` composite statically bindable
> and fully observable with exact two-hop payload lineage, controller masks,
> executable certificate, STRUCTURED-in-FLEX equality, one-owner CAS, complete
> training/population/RNG law, first-trigger REAL/SHAM clone, block reducers,
> simultaneous max-t vector and exhaustive atomic/aggregate result law? What
> are full native reset-to-terminal C++/batched construction, policy forward/
> backward, training, branching evaluation, inference, checkpoint/resume,
> CPU/GPU, wall, RSS, scratch and durable costs?

That question is not a CM request and authorizes no code, build, test, probe,
identity, coordinate, model, training, evaluation, lease, compute or Git.

## 16. Physical-plausibility sources

The unchanged sources motivate only temporary visual occlusion/tracking and
terrain-relay obstruction, not DISH value:

- Li, Chen and Cheng, *Motion Prediction and Robust Tracking of a Dynamic and
  Temporarily-Occluded Target by an Unmanned Aerial Vehicle*, IEEE TCST (2021),
  DOI `10.1109/TCST.2020.3012619`.
- Hung, Hsu and Cheng, *Image-Based Multi-UAV Tracking System in a Cluttered
  Environment*, IEEE TCNS (2022), DOI `10.1109/TCNS.2022.3181255`.
- Burdakov et al., *Relay Positioning for Unmanned Aerial Vehicle Surveillance*,
  IJRR (2010), DOI `10.1177/0278364910369463`.

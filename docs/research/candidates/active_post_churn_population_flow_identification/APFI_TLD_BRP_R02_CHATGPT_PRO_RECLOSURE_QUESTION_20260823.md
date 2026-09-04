# APFI TLD-BRP revision-02 ChatGPT External Pro reclosure question

Continue the existing dedicated ChatGPT Pro scientific conversation for the
APFI direction. This is one complete replacement composite, not a patch.

```text
OBJECT=APFI-FRESH-PRINCIPAL-FLOW-HOST-DISCRIMINATOR-R01
EXACT_REVISION=APFI-TLD-BRP-SCIENCE-20260823-02
HOST=TLD-BRP-TRANSMISSION-LINE-DOCK-BANK-COMMITMENT-CADENCE-ORTHOGONAL-v2
STAGE=PROSPECTIVE_DEFINITION_ONLY
SCIENTIFIC_ACTIVITY_BEGUN=false
```

Review only the mathematical and causal closure of this complete revision. Do
not review code, runtime, implementation correctness, portfolio priority,
resource allocation, real-flight approval, or deployment.

Your first nonempty line must be exactly `CLOSED` or `REVISION_REQUIRED`. Do
not return conditional closure or a third disposition. Any remaining
science-bearing ambiguity requires `REVISION_REQUIRED`.

After the first line, report:

```text
EXACT_REVISION=APFI-TLD-BRP-SCIENCE-20260823-02
SCIENCE_BEARING_DEFECT_COUNT=<integer>
```

If closed, state the maximum defensible claim and strongest remaining
alternative. If revision is required, enumerate every exact defect, the
minimum complete correction, the maximum unrepaired claim, and the
highest-information next discriminator.

BEGIN COMPLETE REPLACEMENT COMPOSITE

## Decision and isolation

This revision supersedes `APFI-TLD-BRP-SCIENCE-20260823-01` in full. It
separates two questions previously confounded:

1. Can a legal non-actuating transaction reveal a pre-existing immediate
   replacement commitment with positive task value?
2. After that commitment and its response are held fixed, can
   population-event history identify a persistent replacement cadence that
   changes a later optimal action, and does an anchored population-flow
   representation add anything beyond exact-containing and simple controls?

The second is the APFI-specific discriminator. The first establishes at most a
narrow active-information host. This object is definition-only: no provider
answer, learning result, construction fact, implementation, or empirical value
is incorporated.

## Finite latent family and common prefix

The exhaustive balanced support is

```text
(C,Z,B) in {0,1} x {FAST,DEFERRED} x {0,1}
P(C,Z,B)=1/8.
```

- `C` is the immediate `t=3` commitment predicate.
- `Z` is persistent replacement cadence.
- `B` is the sham payload.
- `C`, `Z`, and `B` are mutually independent.
- They are generated only after a common law-independent history ending at
  `t=0`.
- Every cell has the same policy-visible prefix, current roster,
  law-independent physical state, clock, identifiers, actions and common
  disturbances.
- Complete latent states need not be identical: hidden scheduler state is
  generated consistently with `(C,Z)`.
- No cadence-dependent event occurs before `t=0`.

For all four `(c,z)` cells the complete distribution of pre-response policy
inputs is identical:

```text
Law(O_<=0,A_<0 | C=c,Z=z) is invariant in (c,z).
```

## Hidden scheduler cause and immediate response

At `t=0`, hidden scheduler state is

```text
S0=(C,Z,K3,S_FAST,S_DEFERRED).
```

`K3` is an immutable pre-probe admission certificate. `K3=1` exactly when one
prepared replacement is irrevocably committed, under the frozen continuation,
to be active, sufficiently charged, legal, assigned to the trunk and
physically present at `TRUNK_STAGING` before the `t=3` staffing score. `K3=C`.

The same pre-existing cause determines the real response and actual readiness:

```text
R_REAL=K3
J3=K3.
```

The transaction reads `K3`; it cannot create, edit, reserve, cancel or advance
the certificate, admissions, queue, charging, launch, cadence, task state,
reward or disturbance. A capability forecast, uncommitted prediction, scenario
label, filename, seed, collector field or unrealized future random variable is
invalid.

## Deterministic persistent source law

```text
S_FAST={5+6m:m>=0}={5,11,17,...}
S_DEFERRED={7+8m:m>=0}={7,15,23,...}.
```

At the start of every absolute slot in `S_Z`, before scoring at that tick,
exactly one prepared replacement is admitted if operational roster size is
below three. Otherwise the slot is skipped. Skipped slots do not pause or reset
absolute phase; later exits do not reset it. Every admitted replacement is
active, sufficiently charged, legal, assigned as stated and instantiated at
`TRUNK_STAGING`. No unnamed join or exit occurs. Eligibility, “may join” and
probabilistic admission are excluded.

## Common transaction, real arm, sham and mask

There is one legal `CHECK_CERTIFICATE` transaction. `REAL`, `SHAM` and `MASKED`
have identical policy-visible request bytes, flight micro-loop, imagery, radio
energy, packet length, timing, response format, endpoint, broker route,
parsing, scheduler execution path, acknowledgement/retry behavior, link state,
logging/counters, queue state, charging state, legal masks and scalar cost.

A hidden arm selector, absent from policy input and without future causal
effects, changes only the delivered payload:

```text
REAL:   R=K3
SHAM:   R=B
MASKED: R=NULL.
```

For every common prestate and disturbance:

```text
X_1:2^REAL \ {R}
= X_1:2^SHAM \ {R}
= X_1:2^MASKED \ {R}.
```

`X` includes every visible or future-causally-relevant physical, scheduler,
network, energy, timing, legal-mask, logging/counter, queue, charging and task
variable.

`B` is prospectively generated and conditionally independent of `(C,Z,S0)`,
future admissions, scenario identity and common disturbances in every declared
public-history stratum. The exhaustive eight-cell support gives exact finite
balance, and the counterbalancing assignment is not policy-visible.

Every executed transaction costs `c=0.25`; `NO_PROBE` costs zero. If technical
construction cannot make the stated non-message transition equality true, the
information-only probe branch fails.

## Phase A: immediate commitment witness

Timeline:

- `t=-1`: the same UAV exits for battery service; roster becomes `{u1,u2}`.
- `t=0`: execute `CHECK_CERTIFICATE` or `NO_PROBE`; `u1` performs the same
  inspection micro-loop in all transaction arms.
- `t=1`: deliver `R`.
- `t=2`: the sole remaining Phase-A action is `EXPAND_A` (dispatch `u2` to the
  remote spur) or `HOLD_A` (retain `u1,u2` on trunk).
- Start of `t=3`: if `K3=1`, admit the committed replacement, task-ready and
  assigned at `TRUNK_STAGING`.
- After admission: evaluate trunk staffing and Phase-A reward; Phase A then
  terminates and later events have zero effect on its return.

The trunk yields eight exactly when at least two active, task-ready UAVs are
assigned to and physically present on trunk at that scoring instant. The spur
yields six exactly when `u2` was dispatched at `t=2`.

| Commitment | `EXPAND_A` | `HOLD_A` | Unique optimum |
| --- | ---: | ---: | --- |
| `C=1` | `14` | `8` | `EXPAND_A` |
| `C=0` | `6` | `8` | `HOLD_A` |

With balanced `C`:

```text
V_passive(EXPAND_A)=10
V_passive(HOLD_A)=8
V_REAL,gross=11
V_REAL,net=10.75
V_SHAM,net<=9.75
V_MASKED,net=9.75
V_NO_PROBE=10.
```

The fixed witness is `R=1 -> EXPAND_A`, `R=0 -> HOLD_A`. Under response flip
`R <- 1-K3`, its gross value is `7` and net value `6.75`.

## Orthogonality

Because `C` and `Z` are independent and `R_REAL=C`:

```text
I(R_REAL;Z)=0.
```

Pairs with the same `C` receive exactly the same response despite different
persistent cadence. Immediate commitment information cannot solve the later
cadence-dependent decision.

## Phase B: persistent-cadence discriminator

Phase B is evaluated only on the matched `C=1` pair, so both cells have the
same `t=3` response and admission.

- After Phase-A scoring, at `t=4`, the same admitted replacement exits for a
  scheduled unscored battery event, leaving `{u1,u2}`.
- Under `FAST`, the absolute `t=5` slot admits a prepared replacement.
- Under `DEFERRED`, no admission occurs at `t=5`; its `t=7` slot admits one.
- The admitted replacement remains on a powered, zero-modeled-consumption trunk
  staging pad until `t=8`; `u1,u2` follow an identical fixed unscored
  micro-loop.
- At `t=8`, both cells have identical unordered active-roster features,
  positions, energy, inspection ages, legal mask and physical state. Their
  policy-visible histories differ only in intended join time: `T_CAL=5` versus
  `T_CAL=7`. No truth-coded identity is visible.
- At `t=9`, the same roster slot exits, leaving two active UAVs.
- At `t=10`, the sole remaining Phase-B action is `EXPAND_B` (dispatch `u2` to
  a second time-critical spur) or `HOLD_B` (retain `u1,u2` on trunk).
- Start of `t=11`: `FAST` admits one prepared task-ready replacement;
  `DEFERRED` admits none. Reward is scored under the same trunk-eight/spur-six
  law and Phase B terminates.

| Cadence | `EXPAND_B` | `HOLD_B` | Unique optimum |
| --- | ---: | ---: | --- |
| `FAST` | `14` | `8` | `EXPAND_B` |
| `DEFERRED` | `6` | `8` | `HOLD_B` |

With balanced `Z`, a cadence-blind policy has gross optimum `10`. The fixed
history witness `join at t=5 -> EXPAND_B; no join at t=5 -> HOLD_B` has gross
value `11`. Delivering its paired opposite-cadence history yields gross value
`7`. This proves only that the declared event history is decision-relevant; it
does not prove APFI is needed.

## Policy-visible interface and team delivery

At each tick, the shared policy receives unordered active-roster features,
each active UAV's position, energy, task assignment and legal mask,
inspection-age state, public clock, prior legal actions, membership join/exit
events and their public times, and `R` only after the transaction. One team
broadcast delivers the same payload and membership-event record to every
action-owning agent before `t=2` and `t=10`. This broadcast is included in the
common non-message transition equality.

Excluded are `C`, `Z`, `B`, `S0`, cadence tables, future admissions, arm labels,
scenario/seed names, truth-coded identifiers, collector fields, reward
lookahead and law-dependent side channels. If the response or calibration
event cannot reach every action owner in time, the coordinated host fails.

## APFI state and exact witness

Let `H=8`. APFI state is

```text
b_t=(q_t,p_t,LambdaPlus_t,LambdaMinus_t,v_t)
```

where `q_t=P(C=1|legal history)`, `p_t=P(Z=FAST|legal history)`, the two hazard
vectors are in `[0,1]^H`, and `v_t in {0,1}` is a legal-support indicator.
Initialize `q_0=p_0=1/2`, `v_0=1`.

Updates occur after current observation and before the next decision:

- a real non-null response sets `q=R`;
- sham or mask supplies no likelihood about `C` and does not update `q`;
- in the `C=1` calibration pair, a join at `t=5` sets `p=1`, while absence of
  the guaranteed FAST join by the end of `t=5` sets `p=0`;
- later legal observations preserve the corresponding point posterior;
- hazard vectors are exact mixtures of registered deterministic events under
  `(q,p)`;
- a history impossible under every registered cell sets `v=0` and is excluded
  from scored support.

The analytic witness chooses `EXPAND_A` iff `q>1/4` and `EXPAND_B` iff
`p>1/4`, since `6+8p>8` exactly when `p>1/4`. No auxiliary loss or empirical
claim belongs to this revision.

## Exact-containing comparator and shortcuts

The common permutation-invariant roster encoder is `E`. APFI is

```text
b_(t+1)=F_A(b_t,E(o_(t+1)),a_t)
pi_A=G_A(b_t,E(o_t),mask_t).
```

`RNN-CONTAIN` has state `h_t=(b'_t,g_t)`. The `b'` block has exactly APFI's
domain, initialization, preprocessing, normalization, support handling,
recurrence and masks. `g_t` is an unrestricted generic recurrent block with
dimension at least `dim(b_t)` and the same complete inputs. Its head is
unrestricted over `(b',g,E(o),mask)`.

For every APFI head parameterization, injection `J` initializes `b'_0=b_0`,
copies `F_A` and `G_A`, zeros generic and cross-block weights, makes the head
ignore `g`, and therefore gives for every legal history:

```text
F_R(iota(b_t),x_t;J(theta_A))=iota(F_A(b_t,x_t;theta_A))
G_R(iota(b_t),E(o_t);J(theta_A))=G_A(b_t,E(o_t);theta_A).
```

Containment concerns policy class only. Additional mandatory controls are:

- `SIMPLE-C`: response-conditioned Phase-A map with no cadence state;
- `SIMPLE-EVENT`: Phase-B map using only whether a join occurred at `t=5`;
- `RNN-GENERIC`: generic recurrence without the APFI block;
- `RNN-CONTAIN`: the exact supernetwork above.

If `SIMPLE-EVENT`, `RNN-GENERIC` or `RNN-CONTAIN` matches APFI, there is no
APFI-specific representation advantage. In the deterministic paper witness,
`SIMPLE-EVENT` is expected to solve Phase B; this is a deliberate fatal
shortcut control, not hidden favorable evidence.

## Counterfactual interventions

1. Enumerate all eight `(C,Z,B)` worlds from the identical law-independent
   prefix.
2. Compare `REAL`, `SHAM`, `MASKED` and `NO_PROBE` under the exact transaction
   and cost laws.
3. Phase-A response swap holds `(C,Z,S0)`, actual `J3`, transaction shell,
   pre-`t=2` physical trajectory and disturbances fixed; changes only delivered
   `R`; then permits the sole downstream action and trajectory to respond.
4. Phase-A full action clamp fixes the sole `t=2` action through termination.
   Within each `(C,Z)` cell, all non-message descendants and returns must match
   across transaction arms.
5. No-response delivers `NULL`. It guarantees absence of added information
   about `C`, not literal equality of arbitrary learned behavior. Its optimal
   gross value is `10`, net `9.75`.
6. Cadence-history swap within the `C=1` pair holds actual `Z`, scheduler state,
   current `t=8` physical state, future slots, pre-`t=8` physical execution and
   disturbances fixed; replaces only policy-delivered membership-event history
   with its opposite-cadence paired record; then permits the sole Phase-B
   action and trajectory to respond.
7. Phase-B full action clamp fixes the sole `t=10` action through termination.
8. Within fixed `C`, Phase-A response distributions must be identical across
   `Z`; any response information about `Z` invalidates orthogonality.

## Total branch map

- Pre-response information about `C` or `Z` invalidates passive insufficiency.
- Absence of a pre-existing common cause for response and `J3` invalidates the
  physical-probe construction.
- Failure of deterministic admission, readiness or event order invalidates the
  payoff witness.
- Sham dependence on `(C,Z,S0)` or future variables invalidates the sham
  contrast.
- Any non-message `REAL/SHAM/MASKED` transition difference invalidates the
  information-only mechanism.
- Response-swap insensitivity under the registered witness leaves its response
  pathway unsupported.
- Failure to match state at `t=8` invalidates the persistent-cadence
  discriminator.
- Query-response information about `Z` invalidates commitment/cadence
  orthogonality.
- APFI learning failure supports no APFI efficacy claim; the abstract host may
  remain.
- `SIMPLE-C` solving Phase B shows leakage or failed orthogonality.
- `SIMPLE-EVENT` or `RNN-GENERIC` matching APFI removes APFI-specific
  representation value.
- `RNN-CONTAIN` matching or exceeding APFI removes anchored-representation
  advantage.
- Any later valid finite-budget APFI advantage supports only named-host
  inductive-bias evidence, never policy-class superiority.

## Resource and activity boundary

```text
training_runs=0
simulations=0
tests=0
compute_lease=none
cm_request=none
```

The logical support is eight deterministic base worlds. Counterfactual arms
are interventions, not new scientific identities. Any construction or
empirical stage requires Pro `CLOSED`, same-direction EM intake, a new
Portfolio decision, separate CM feasibility and complete resource evidence,
an exact lease if required, and a prospective training/evaluation freeze. No
seed count, learner budget, coordinate, identity or runtime is authorized.

## UAV bridge and claim ceiling

Battery service is the sink; committed or cadence-slot replacement is the
source; trunk-versus-spur allocation represents inspection freshness. The
roster changes `3->2` and conditionally `2->3`. Replacements are task-ready at
a trunk staging site before scoring. Immediate response concerns only `C`;
join-time history concerns `Z`.

After Pro closure but before empirical activity, this revision could support
only:

- constructibility of the named finite toy host;
- equality and insufficiency of its declared pre-probe policy-visible prefix;
- existence of a legal non-actuating transaction reading a pre-existing
  immediate commitment;
- the Phase-A paper witness: real net `10.75`, no-probe `10`, matched-cost
  sham/mask at most `9.75`;
- independence of immediate commitment response and persistent cadence; and
- existence of a later cadence-dependent action witness from population-event
  history.

It cannot support APFI learning efficacy, APFI necessity, policy-class
superiority, RNN inferiority, general dynamic-`N`, actual dock-interface
availability, UAV performance, legality, safety, communications reliability or
deployment.

## Stop and revisit law

Stop before construction if this revision does not close the causal
certificate, deterministic source law, interventions, containment or
orthogonal discriminator. Stop the active-probe claim if the certificate is
already passive input, the transaction changes scheduler/task state, or the
only response is a scenario/law label. Stop APFI-specific investment if the
simple event policy answers Phase B or later matches APFI without an
answer-changing finite-budget advantage under a separately frozen valid
comparison.

A future revisit needs a new Portfolio decision and either a source-grounded
non-actuating observation with a non-label causal generator, or a persistent
flow family whose answer cannot be reduced to the registered simple response
or event controls. No stop changes another direction or current allocation.

END COMPLETE REPLACEMENT COMPOSITE

Required audit:

1. common causal scheduler state for response and readiness;
2. deterministic slots and phase rules;
3. exact readiness, location, event order and horizon;
4. conditional sham independence;
5. complete non-message transition equality;
6. typed exact containment and parameter injection;
7. common-support construction;
8. coherent response/history swaps, complete clamps and total branches;
9. orthogonality of immediate commitment and persistent cadence; and
10. whether Phase B is a legitimate APFI discriminator when `SIMPLE-EVENT` is
    already capable of solving its deterministic witness.

Do not silently assume any missing fact. A required ambiguity is
`REVISION_REQUIRED`.

# VQFP fixed-effort ridgeline sampling definition

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FIXED-EFFORT-RIDGELINE-SAMPLING-DEFINITION
revision=VQFP-FERL-SCIENCE-20260821-01
host=RIDGELINE-PLUME-FRONT-1D-FIXED-EFFORT-v1
stage=prospective_definition_only
scientific_activity_begun=false
construction_authorized=false
empirical_activity_authorized=false
```

## Decision first

This is a new fixed-total-effort variable-`N` object, not a rerun or repair of
`VQFP-B1-PERIODIC-LOCAL-MEASURE-v1`. The old saturated host contributes only a
prospective warning: a learned comparison cannot identify value when the task
has no headroom or the allocation does not move. No old result row, threshold,
seed, coordinate, checkpoint, acceptance or claim enters this object.

The question is whether a hard, correctly associated Voronoi-measure factor is
a useful finite-budget inductive bias when a shared policy must allocate one
fixed physical sensing-and-relay budget across a changing roster. The direct
comparison is `FERL-MEASURE` versus strict-containing
`FREE-MEASURE-CONTAIN`. `EQUAL-MASS`, matched
`FREE-NO-MEASURE-PORT`, a frozen reassociated-measure intervention and an
analytic one-step allocator qualify opportunity, support and mechanism
specificity. Every learned arm shares the same host, architecture,
communication, action space, total effort, optimizer work and evaluation
tapes; the no-port arm alone has its explicit measure input replaced by the
registered constant.

A later positive result could support only exact finite-package value on this
one-dimensional task. It could not establish arbitrary-`N` robustness,
natural mediation, two-dimensional plume performance, aircraft transfer,
safety, deployment or flight.

## Scientific question

Can one permutation-equivariant shared policy trained once at
`N in {4,8}` use correctly associated Voronoi-cell length, local plume-front
gradient and unserved relay mass to improve direct sensing/relay utility at
untouched `N in {6,12}` over a competent free-residual controller that
literally contains the hard-measure policy?

The finite-budget causal contrast is the allocation rule. A positive
`FERL-MEASURE` contrast means the fixed physical-measure factor was a useful
regularizer in this package, not that the containing controller could not
represent it. A positive common contrast of both learned arms over
`EQUAL-MASS`, without a material FERL-versus-FREE difference, can support only
measure-informed allocation value, not the hard factor.

## Exact physical host

### Domain, roster and Voronoi cells

The physical domain is the open ridgeline segment `x in [0,1]`. One episode is
`H=64` simultaneous ten-second decisions. Agent loiter positions are fixed
within an episode. For roster size `N`, draw `N+1` positive raw gaps
independently from `Gamma(alpha,1)` and set

```text
g_j = 0.02/(N+1) + 0.98*raw_j/sum_l raw_l,  j=0,...,N.
x_i = sum_(j=0..i-1) g_j,                    i=1,...,N.
```

Use `alpha=1` for `IID` and `alpha=0.35` for `CLUSTER`. Define open-segment
Voronoi boundaries

```text
b_0=0,
b_N=1,
b_i=(x_i+x_(i+1))/2,  i=1,...,N-1,
C_i=[b_(i-1),b_i),
v_i=b_i-b_(i-1).
```

The right endpoint belongs to `C_N`. Thus every `v_i>0` and
`sum_i v_i=1`. Independently permute physical rank to opaque actor handle.
Rank and handle are not actor inputs.

Training samples `N={4,8}` and `IID/CLUSTER` equally. Evaluation crosses
`N={4,6,8,12}` with both layout regimes. Only `N={6,12}` is claim-bearing.
Every learned arm is one shared parameterization; there is no per-`N` head,
normalization refit, fine-tuning, checkpoint choice or evaluation adaptation.

### Action-independent plume-front process

Two one-dimensional plume-front urgency ridges move independently of actions
and agent positions. At `t=0`, draw

```text
mu_1 in [0.10,0.40],
mu_2 in [0.60,0.90],
q_1 in {-0.012,-0.008,+0.008,+0.012},
q_2 in {-0.012,-0.008,+0.008,+0.012}
```

uniformly and independently except for the stated center intervals. Centers
advance by `q_m` and reflect elastically at `0` and `1`. At `t=32`, one
independent fair sign decides whether each velocity flips. No actor observes
the future flip or velocity.

With `w=0.08`, amplitudes `A_1=1` and `A_2=0.7`, define

```text
p_t(x) = min(1,
             sum_(m=1..2) A_m*max(0,1-abs(x-mu_m(t))/w)),
H_t    = {x : p_t(x) >= 0.40}.
```

For each cell retain exact analytic quantities

```text
gradient_mass_i(t) = integral_(C_i) p_t(x) dx,
high_gradient_length_i(t) = length(C_i intersection H_t).
```

The actor sees the current cell averages but not front identities or centers.

### Relay field and fixed effort

Each episode draws `zeta_0 ~ Uniform[0,1)`. The action-independent link field is

```text
link_t(x)=0.55+0.35*cos(pi*(x-zeta_0-0.004*t))^2,
link_i(t)=(1/v_i)*integral_(C_i) link_t(x) dx.
```

At every tick the joint action contains nonnegative sensing effort `s_i` and
relay effort `r_i` for each agent under the exact conservation law

```text
sum_i (s_i+r_i) = E_total = 0.20.
```

`E_total` is episode- and roster-invariant. It never scales with `N`.

Let `B_i(t)` be unrelayed plume-front data mass, with `B_i(0)=0`. The physical
service law is

```text
coverage_i(t) = 1-exp(-4*s_i(t)/v_i),
acquired_i(t) = coverage_i(t)*gradient_mass_i(t),
unserved_length_i(t)
  = (1-coverage_i(t))*high_gradient_length_i(t),
delivered_i(t)
  = min(B_i(t)+acquired_i(t), 3*link_i(t)*r_i(t)),
B_i(t+1)=B_i(t)+acquired_i(t)-delivered_i(t).
```

The field, layout and link dynamics never depend on the action. All arithmetic
uses the same equations for every arm.

### Training reward and direct endpoints

Define per-tick normalized unserved length and backlog pressure

```text
u_t = sum_i unserved_length_i(t) /
      max(sum_i high_gradient_length_i(t),1e-12),
b_t = sum_i B_i(t+1) /
      max(sum_(tau=0..t) sum_i gradient_mass_i(tau),1e-12).
```

The common team reward is `-(0.6*u_t+0.4*b_t)`. It is delivered after the
simultaneous joint action. It contains no future plume, analytic action or
arm label.

The three claim-bearing episode endpoints are lower-is-better:

1. `U`: integrated unserved high-gradient length divided by the integrated
   high-gradient length offered over the episode;
2. `D90`: the 0.90 quantile of normalized discovery delays. A discovery event
   starts when a named front center enters a cell after at least two ticks
   outside it. Its delay is the first number of ticks for which cumulative
   `coverage_i` since entry reaches `0.75`; an uncompleted event is censored at
   `H-t_entry+1`, and delay is divided by that same maximum; and
3. `R`: relay-service gap
   `1-sum_(t,i) delivered_i(t)/sum_(t,i) gradient_mass_i(t)`.

The seed-level `D90` is computed from the pooled discovery events in that
evaluation cell. A cell with fewer than 40 events per seed is nonanswerable.
The raw components and all three denominators are retained; no learned reward
surrogate replaces a direct endpoint.

## Information and action boundary

Before the action at tick `t`, agent `i` receives its own current

```text
gradient_mass_i/v_i,
B_i,
link_i,
v_i,
previous s_i/E_total,
previous r_i/E_total,
N/12,
t/63,
```

plus the same records from its immediate physical predecessor and successor,
with a boundary token when absent. The fixed-length actor record is invariant
to opaque-handle permutation. Both arms receive exactly the same record and
execute the same bounded-degree messages.

No actor sees the simulator-truth high-gradient mask or length, absolute
physical rank, opaque handle, layout label, front identity/center/velocity,
future flip, future field, analytic action, evaluation cell, intervention label
or arm label. The current gradient-density input is the task's deployable
noise-free cell-average sensor reading; the claim ceiling excludes noisy or
point sensors. A common centralized critic may see the current full set of
records and scoring truth during training only; no critic fact reaches the
actor.

## Shared learned package

Both learned arms use the same two-layer width-64 record encoder, one width-64
GRU shared across agents, a permutation-invariant physical-neighbor message
sum, two base logits per agent (`SENSE`, `RELAY`), two residual logits per
agent and one matched set-pooled centralized critic. GRU state starts at zero
and resets only at episode end. There is no per-`N` parameter, attention menu,
checkpoint menu or second message-passing layer.

The trainable base logits `q_(i,m)` may use every current record except every
own or neighbor cell-length coordinate; no trainable base route sees `v`.
Current cell length reaches the action through the explicit physical-measure
factor below. The residual head receives the same hidden state plus the own and
neighbor `log(v)` coordinates and can cancel, preserve or change that factor.

Paired arms receive identical values for every common parameter. The residual
output layer is initialized to exact zero in both arms. Both arms execute and
retain the residual head, parameter count and optimizer slots. In
`FERL-MEASURE` its output multiplier is fixed to zero and no residual gradient
enters the optimizer; in `FREE-MEASURE-CONTAIN` the multiplier is one.

For mode `m in {SENSE,RELAY}`:

```text
FERL-MEASURE:
  logit_(i,m) = log(v_i) + q_(i,m)

FREE-MEASURE-CONTAIN:
  logit_(i,m) = log(v_i) + q_(i,m) + residual_(i,m)

pi_(i,m)
  = softmax_over_all_2N_slots(logit)_(i,m),
y ~ Dirichlet(64*pi),
action_(i,m)=E_total*y_(i,m).
```

Setting every residual to zero makes the containing arm literally identical
to FERL for every history. FREE therefore has the same information, actions,
communication, initialization, backbone, critic, samples, updates and optimizer
opportunities while strictly containing the hard-measure rule. The total
Dirichlet concentration is exactly 64 for every `N`; policy log likelihood is
the exact Dirichlet density. Evaluation retains this stochastic law with fresh
address-based Gamma streams frozen independently by arm. Support diagnostics
use the policy mean `pi`, not sampled Dirichlet noise.

Before any scientific identity or coordinate may exist, a TEST-only exact-law
check must cover every registered `N` and layout: residual-zero FREE and FERL
must have identical action-distribution parameters for every supplied history;
permuting opaque agent handles and the complete associated records must permute
the output shares and recurrent states exactly; and changing array order alone
must not change physical allocations. A failure is `INVALID_OR_INCOMPLETE`,
never evidence against measure allocation. Both arms use the identical simplex
projector and action masks. There is no per-agent effort floor, free service or
uncounted overhead that grows the effective team budget with `N`.

## Controls

### EQUAL-MASS

`EQUAL-MASS` is the historical portfolio label; in this card it means equal
**effort**, not access to target mass. It is a nonlearned control assigning exactly
`s_i=r_i=E_total/(2N)` at every tick. It uses no future state and is evaluated
on the same tapes. It is a basic allocation baseline, not the strong learned
comparator.

### FREE-NO-MEASURE-PORT

`FREE-NO-MEASURE-PORT` is a third learned, matched control. It is identical to
`FREE-MEASURE-CONTAIN` except that every explicit length supplied to the fixed
measure factor and residual-length port is the constant `1/N`. The true `v`
coordinates are still carried through a masked zero-gradient work-matching
port, but no trainable route receives them. The base route already excludes
all length coordinates. The arm therefore preserves information, parameter,
action, communication, update and optimizer-work matching except for the one
scientifically intended explicit-measure input. It is trained from a fresh
paired initialization under the same law and must independently pass support
and competence before supporting a measure-port claim.

### ANALYTIC-ONE-STEP

`ANALYTIC-ONE-STEP` receives the current physical state only and chooses the
nonnegative `2N` allocation summing to `E_total` that minimizes the exact next-
tick quantity `0.6*u_t+0.4*b_t`; ties use lexicographic physical rank before
handle permutation. It is recomputed from the exact service equations without
learning or future state. It is a feasible opportunity/headroom witness, not a
bound for discovery delay, relay dynamics or full-horizon value. It is not an
actor, training target, claim-bearing deployment comparator or proof of
dynamic optimality.

### REASSOCIATED-MEASURE

On a frozen learned checkpoint, `REASSOCIATED-MEASURE` replaces only the
`v_i` value at every explicit measure-factor and residual-length port by the
next physical cell's length under even evaluation episodes and by the previous
cell's length under odd episodes. The physical cell, plume, link, content
record, backlog, recurrent state, action uniforms and all other inputs remain
unchanged. The original lengths still determine physical service. The incoming
length multiset and total effort are preserved. No retraining occurs.

This control is applied separately to both learned arms and answers whether
correct measure association contributes to their allocation. It is an
off-manifold functional intervention and cannot by itself establish natural
mediation.

## Frozen training and evaluation law

Use 24 fresh paired seed blocks, disjoint from every prior VQFP seed,
coordinate, field tape and checkpoint. For each seed and arm:

- train one shared policy for exactly 600 PPO updates;
- each update collects 32 complete 64-tick episodes, balanced over
  `N={4,8}` and `IID/CLUSTER`;
- use GAE `gamma=0.99`, `lambda=0.95`, PPO clip `0.20`, value coefficient
  `0.5`, entropy coefficient `0.01`, gradient-norm clip `0.5`, four epochs and
  minibatches of 512 ticks;
- use AdamW with learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8` and
  zero weight decay;
- evaluate only the checkpoint written immediately after update 600; and
- forbid early stopping, budget/checkpoint/seed search, threshold tuning,
  architecture menus and result-dependent continuation.

Each seed evaluates the three intact learned arms, the reassociated
intervention on FERL and FREE, `EQUAL-MASS` and `ANALYTIC-ONE-STEP` on 128
fresh complete episodes for every `N in {4,6,8,12}` by `IID/CLUSTER` cell.
Common physical tapes are paired across arms and controls; action randomness
is independent by arm but frozen before evaluation. Only seed-level aggregates
enter inference.

Question-relevant scientific activity begins immediately before the first
optimizer mutation of a production FERL or FREE model, or before the first
production evaluation used in a conclusion, whichever occurs first. TEST-only
formula fixtures, analytic arithmetic checks and native/reference equivalence
using explicitly non-scientific tapes do not cross that boundary. No such work
is authorized by this definition.

## Inference, margins and prerequisite gates

For lower-is-better endpoint `X`, define positive benefit

```text
Delta_X(A,B) = X_B-X_A.
```

The claim-bearing simultaneous family contains all `U`, `D90` and `R`
contrasts for both held-out `N`, both layout regimes and these six comparisons:

```text
FERL vs FREE,
FERL vs EQUAL-MASS,
FREE vs EQUAL-MASS,
FERL-intact vs FERL-reassociated,
FREE-intact vs FREE-reassociated,
FREE vs FREE-NO-MEASURE-PORT,
ANALYTIC-ONE-STEP vs EQUAL-MASS.
```

This is `3*2*2*7=84` contrasts. Use two-sided Student paired-mean intervals
with `23` degrees of freedom and Bonferroni familywise coverage `0.95` across
all 84; no asymptotic seed pooling or episode-as-independent inference is
allowed. Report every interval and raw seed vector.

Competence uses a separate prospectively frozen 24-member prerequisite family.
For arm `A`, roster `N` and layout `s`, define the seed-level linear quantity

```text
C_A(N,s)
  = (U_EQUAL-U_A)-0.20*(U_EQUAL-U_ANALYTIC).
```

The family crosses three learned arms, four registered `N` values and two
layouts. Use two-sided Student intervals with 23 degrees of freedom and
Bonferroni familywise coverage 0.95 across these 24 quantities. Competence
requires the simultaneous lower endpoint of every `C_A(N,s)` to exceed zero.
No ratio estimator or result-dependent denominator screening is used.

Prospective material margins are

```text
m_U=0.04,
m_D=0.05,
m_R=0.04.
```

Non-harm margins are half of the corresponding material margin. Practical
equivalence on a contrast requires its full simultaneous interval to lie
inside `[-m_X,+m_X]`.

The following prerequisites precede every value branch.

1. **Validity:** complete atomic 24-seed panel, exact conservation,
   residual-zero containment and permutation identities, nonnegative
   actions/backlogs, no leakage or selection, all endpoint denominators
   positive and every stored arithmetic identity satisfied.
2. **Physical opportunity:** in every held-out cell, the simultaneous lower
   bound for `Delta_U(ANALYTIC,EQUAL)` exceeds `0.08`, and at least one of
   `Delta_D90` or `Delta_R` exceeds its own material margin. The equal-mass
   `U` mean must be in `[0.20,0.85]`.
3. **Allocation/action support:** for each of the three learned arms and
   held-out cell, at
   least 20 of 24 seeds must have (a) at least half of ticks where the policy-
   mean per-agent total shares differ by at least `0.03`, and (b) at least 80%
   of ticks where policy-mean total SENSE and total RELAY shares are each in
   `[0.15,0.85]`. Realized Dirichlet noise cannot satisfy this gate.
4. **Per-`N` competence:** every one of the 24 simultaneous lower endpoints
   for `C_A(N,s)` exceeds zero; each arm has `R<0.90` in every registered cell;
   and no endpoint is materially worse than `EQUAL-MASS`.
5. **Answerability/headroom/interiority:** every held-out cell has at least
   40 discovery events per seed; each learned mean of `U`, `D90` and `R` lies
   in `[0.08,0.92]`; and every FERL-versus-FREE simultaneous interval has
   half-width no greater than one half of its endpoint's material margin.

Failure of a prerequisite makes downstream contrasts descriptive only. It
does not establish family harm, equivalence or deletion.

## Ordered exhaustive result map

The first matching branch controls.

1. `INVALID_OR_INCOMPLETE`: any validity or complete-panel condition fails.
2. `NO_PHYSICAL_OPPORTUNITY`: validity passes but the analytic opportunity or
   equal-mass headroom gate fails.
3. `NO_ALLOCATION_ACTION_SUPPORT`: opportunity passes but either learned arm
   fails allocation/mode support.
4. `LEARNED_OR_CONTAINING_COMPETENCE_FAILURE`: support passes but either
   learned arm fails per-`N` competence.
5. `ENDPOINT_NONANSWERABLE`: competence passes but event, interiority or
   precision fails.
6. `FERL_TARGET_HARM`: answerability passes and FERL is materially worse than
   `EQUAL-MASS` on `U` in either held-out `N` across both layouts, or violates
   a simultaneous secondary-endpoint non-harm bound.
7. `FERL_TREATMENT_SPECIFIC_VALUE`: at least one held-out `N` has both layouts
   with `Delta_U(FERL,FREE)` and `Delta_U(FERL,EQUAL-MASS)` lower bounds above
   `m_U`, secondary endpoints simultaneously non-harmful in every held-out
   cell, and
   `Delta_U(FERL-intact,FERL-reassociated)` lower bound above `m_U` in those
   qualifying cells. Retain only the exact hard-measure finite-budget family.
8. `FREE_MEASURE_SUPERIORITY`: at least one held-out `N` has both layouts with
   `Delta_U(FREE,FERL)` lower bound above `m_U` and FREE is non-harmful on both
   secondary endpoints in every held-out cell. Delete the hard factor for this
   target and retain only the containing free-measure family.
9. `EXPLICIT_MEASURE_PORT_ONLY_VALUE`: all FERL-versus-FREE endpoint intervals lie in
   their practical-equivalence bands; both learned arms materially improve
   `U` over `EQUAL-MASS` at at least one held-out `N` across both layouts;
   FREE materially improves `U` over competent `FREE-NO-MEASURE-PORT`; and
   reassociation materially worsens `U` for both measure-bearing arms there.
   Retain the explicit measure port/binding and delete any hard-factor
   advantage claim. This does not establish that measure could not be
   reconstructed from a richer sensor geometry outside this exact object.
10. `GENERIC_ALLOCATION_VALUE_WITHOUT_MEASURE_SPECIFICITY`: at least one
    learned arm materially improves `U` over `EQUAL-MASS`, but neither intact-
    versus-reassociated `U` contrast nor FREE-versus-no-port contrast qualifies.
    Modify the family toward a generic scarcity allocator; do not retain a
    Voronoi-measure mechanism.
11. `TARGET_SPECIFIC_NO_MATERIALITY`: every learned-versus-learned and learned-
    versus-equal claim-bearing interval, including FREE-versus-no-port, lies
    wholly inside its endpoint's practical-equivalence band. Close this exact
    fixed-effort target without a positive, negative-general or arbitrary-`N`
    claim.
12. `UNRESOLVED_VALID_EVIDENCE`: every prerequisite passes but none of branches
    6-11 does. Report all endpoint-specific intervals and define no automatic
    successor.

No branch triggers a second budget, new seeds, another checkpoint, a two-
dimensional surface, construction, UAV production or deployment. Any later
object requires a new Portfolio decision.

## Strongest alternatives

Even a positive FERL branch can reflect finite-budget conditioning,
initialization or regularization induced by the fixed log-measure factor rather
than a unique quadrature mechanism. The shared global softmax may itself be the
valuable resource-allocation primitive. Performance may arise from backlog or
link features rather than cell measure, from this task's front width/layout
law, or from centralized normalization that would not survive decentralized
communication. Reassociation is off-manifold and can reveal dependence on the
port without proving natural mediation.

## Maximum claim and nonclaims

The maximum possible claim is:

> In the exact `RIDGELINE-PLUME-FRONT-1D-FIXED-EFFORT-v1` package, one shared
> 600-update parameterization trained at `N={4,8}` used a hard correctly
> associated Voronoi-measure factor to improve registered direct fixed-effort
> sensing/relay utility at the qualifying held-out `N` and layout cells versus
> the matched strict-containing free-residual controller, conditional on every
> prerequisite and branch condition.

No outcome supports arbitrary `N`, in-episode roster change, asymptotic or
optimizer-independent superiority, unique mechanism mediation, two-dimensional
plume or terrain value, hardware transfer, flight, safety, deployment or a
general HMASD claim. A no-material branch is exact-target evidence only, not
unrestricted equivalence or VQFP family deletion.

## Exact later CM question

After same-direction Pro closure and EM intake, the only requested engineering
milestone is static feasibility and full prospective cost. CM should determine
whether the exact open-ridgeline DGP, analytic cell integrals, fixed-total
two-mode action, backlog/link law, shared FERL/FREE containment, matched no-
measure-port arm, analytic one-step solver, reassociation intervention,
event-delay analyzer, 84-contrast inference and atomic lifecycle are bindable
and observable in one native-first
C++ reset-to-terminal batched host with fail-closed loading and no Python
production fallback. It must return complete construction, training,
evaluation, CPU/GPU, wall, RAM, scratch, durable-storage and implementation
cost, plus any exact science-bearing ambiguity.

That request would authorize no source, build, probe, identity, coordinate,
training, evaluation, result, lease, compute, production, deployment or Git
action. Construction or empirical investment remains a separate Portfolio
decision.

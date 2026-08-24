# VQFP variable-N physical-association value R02 science card — 2026-08-23

```text
document_kind=direction_empirical_science_card
owner=direction:voronoi_quadrature_field_policy
assignment=VQFP-POST-ANALYTIC-VARIABLE-N-EMPIRICAL-DEFINITION-R01
object=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01
revision=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-02
decision_marker=VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R02_COMPLETE_REPLACEMENT_FROZEN_PENDING_PRO_RECLOSURE_20260823
host=VQFP-MARKOV-FIELD-COVERAGE-1D-VN-v2
stage=definition_only_pending_same_conversation_pro_reclosure
supersedes_definition=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-01
source_theorem=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-03|PROVED_G|RETAIN_G_UNRESTRICTED
distinct_from_r05=true
r05_efficacy_evidence_imported=false
scientific_activity_begun=false
pro_closed=false
construction_authorized=false
empirical_activity_authorized=false
allocation_change=false
portfolio_selection_recommended=true
```

## Decision and bounded question

Retain the variable-`N` route and replace r01 completely with this r02
composite. R02 asks:

> On a bounded stochastic variable-`N` coverage host, does one single
> roster-independent VQFP parameter vector selected only with `N={4,8}` meet
> the registered held-out performance or lower-tail robustness criteria at
> both `N=6` and `N=12` over every frozen nonoracle baseline, remain
> noninferior to a causally conservative matched residual FREE comparator,
> and lose value when physical measures are fully half-cycle reassociated?

The completed r03 theorem supplies definition and control primitives only. It
supplies no efficacy, optimization, robustness, uncertainty or transfer
evidence. This r02 revision imports no r05 observation or conclusion.

## Complete isolation and claim target

This is neither a resumption nor a relabeling of VQFP-FERL r05. It has a new
host version, one global selection procedure, its own evaluation generator,
estimands, finite resampling decision law and terminal map. No r05 row, seed,
checkpoint, threshold, result or efficacy claim enters this object.

The target is deliberately association value rather than physical-measure
necessity. FREE contains the selected treatment command law, generic
diminishing-return controls remain viable, and a finite search can favor the
lower-dimensional treatment. No outcome may revise `PROVED(G)` or transfer
empirical polarity to r05.

## Exact host and variable-N domain

One episode has `T=32` decision steps and a roster fixed throughout the
episode.

```text
N_train={4,8}
N_heldout={6,12}
N_registered={4,6,8,12}
Q=120
```

For roster `N`, draw `s=(s_1,...,s_N)` uniformly from the finite conditional
support

```text
s_i in {-48,-24,0,24,48}
x_i=(2i-1)/(2N)+s_i/(384N)
max_i(v_i)-min_i(v_i) >= 1/(64N).
```

Independent uniform component draws are rejected until the heterogeneity
condition holds. `v_i` is the physical Voronoi cell length at site `i` in
left-to-right physical order. Every accepted geometry lies in the registered
theorem class: sites are on the `1/(384N)` grid, adjacent gaps lie in
`[3/(4N),5/(4N)]`, cell lengths lie in `[7/(8N),9/(8N)]`, and sites are
strictly inside `[0,1]`. Geometry is fixed for the episode.

The six field states, in this exact order, are

```text
S_0=(-1/4,0)       S_1=(-1/4,1/4)
S_2=(0,0)          S_3=(0,1/4)
S_4=(1/4,0)        S_5=(1/4,1/4),
```

where each pair is `(beta,gamma)`. In every development, validation and
evaluation batch, let `e` be the zero-based episode index within the exact
`(purpose,b,N)` cell. Episode `e` in block `b` starts in exactly
`S_((e+b) mod 6)`. Thus the initial state is single-valued for every episode;
over all 12 blocks of any purpose and roster, every state occurs equally
often. There is no separate random initial-state draw.

For each later step, draw an exact uniform integer `h in {0,...,9}`. Values
`0,...,4` retain the current state. Values `5,...,9` move respectively to the
five other states in increasing registered-state index. This gives stay
probability `1/2` and probability `1/10` for each other state. The transition
is action-independent.

At every step,

```text
f(x)=1+beta(2x-1)+gamma(6x(1-x)-1)
m_i=integral over physical cell C_i of f
d_i=m_i/v_i
dbar=(1/N)sum_i d_i.
```

All quantities are exact rationals. The host has no observation noise,
motion, collision, communication, delayed actuation, future-state projection,
travel cost or in-episode membership change.

## Observation, action, endpoint and LR

Each cell exposes `(v_i,d_i,dbar,u_N)`, where `u_N=1/N`. A policy may form
`v_i/u_N-1=Nv_i-1`, but no learned coefficient, head, initialization,
candidate law, threshold or selection rule depends on `N`. Actor label and
physical rank are not inputs. The original left boundary is used only as the
deterministic largest-remainder tie key.

```text
A={j/16:j=-64,...,64}
a_i=n_i/600.
```

A legal command is a nonnegative integer vector with `sum_i n_i=Q`. For a
positive weight vector `w`, `LR(w)` forms exact quotas
`c_i=Qw_i/sum_j w_j`, floors each quota, and gives the remaining quanta in
descending exact fractional remainder, then increasing original left
boundary. The lower-better step endpoint and higher-better episode score are

```text
U_t(n)=sum_i m_i v_i/(v_i+n_i/600)
Z=1-(1/T)sum_{t=0}^{T-1} U_t(n_t).
```

Every normative empirical score uses the legal integer command, never a
continuous shadow.

## One globally selected treatment

The treatment has one coefficient vector `theta in A^4`, used unchanged for
every cell, episode and roster:

```text
q_i=theta_0+theta_1 d_i+theta_2 dbar+theta_3(d_i-dbar)^2
B_i=1+q_i^2
w_i^T=v_i B_i
n^T=LR(w^T).
```

Exactly one `theta_T` is selected before evaluation. There are not 12
replicate-specific treatment policies, and no evaluation block changes or
reselects it.

## Causally conservative matched residual FREE

FREE fixes `theta=theta_T` and searches one additional shared
`phi in A^4`. Define the roster-normalized geometry residual

```text
z_i=v_i/u_N-1=Nv_i-1
r_i=clip[-1/2,1/2](
    phi_0+phi_1(d_i-dbar)+phi_2 z_i+phi_3(d_i-dbar)z_i)
w_i^F=v_i B_i(1+r_i)^2
n^F=LR(w^F).
```

Normalization keeps the geometry feature on the same exact scale across the
registered rosters. `phi=0` reproduces the selected treatment weights and
commands exactly. FREE is a conditional residual enlargement around the one
selected treatment, not an independent eight-dimensional global random
search. Its residual search has the same dimension, candidate count,
development episodes, validation episodes and tie law as the treatment
search. FREE receives this additional search after treatment selection; this
is conservative for a treatment-noninferiority claim and removes
eight-versus-four-dimensional search starvation as an explanation.
R02 does not evaluate or rank a jointly reoptimized eight-dimensional FREE
policy; no outcome may extend conditional-residual noninferiority to that
larger optimization problem.

## Frozen controls

All controls act on the same physical cells, fields, episode records and legal
action map.

1. `EQ`: `n_i=Q/N`, which is integral for every registered roster.
2. `DENS`: field-adaptive, measure-free `w_i=d_i`, followed by LR.
3. `MASS`: nonlearned workload `w_i=m_i`, followed by LR.
4. `MARG0`: parameter-free first-marginal proxy
   `w_i=m_i/(600v_i+1)`, the exact endpoint improvement from giving cell `i`
   its first quantum while other cells remain at zero, followed by LR. This is
   a static proportional proxy, not the sequential oracle.
5. `T-P`: evaluation-only full half-cycle reassociation. For each registered
   even `N`, let `P_N(i)=1+((i-1+N/2) mod N)` and
   `lambda_i=v_(P_N(i))`. Replace `v_i` by `lambda_i` only in the treatment's
   measure-bearing weight occurrence, so `w_i=lambda_i B_i`. Preserve the
   physical endpoint cells, `m_i`, `d_i`, `dbar`, command coordinates,
   original tie keys and selected coefficients. Do not retrain.
6. `F-P`: the analogous evaluation-only FREE reassociation, replacing both
   the multiplicative `v_i` and `Nv_i-1` by `lambda_i` and
   `Nlambda_i-1`. It is a secondary expressivity diagnostic.
7. `ORACLE`: at each step define
   `Delta_i(k)=m_i v_i/(v_i+k/600)-m_i v_i/(v_i+(k+1)/600)` for
   `k=0,...,Q-1`. Sort all records by descending exact `Delta`, increasing
   physical cell index, then increasing `k`, and take the first `Q`. This is
   the exact instantaneous integer endpoint minimizer and an
   unattainable-information ceiling.
8. `FREE-EMBED`: use the selected `theta_T` and `phi=0`; it must equal
   treatment weights and commands on every audited record.

The half-cycle map deranges every physical cell index, preserves the complete
length multiset and changes no field or endpoint association. A loss under
this control supports association sensitivity, not necessity.

## Exact RNG and batch namespaces

Use `Philox4x32-10`. Every purpose, block, roster, episode, step, candidate
and draw index occupies a disjoint counter tuple. The named stream keys are

```text
treatment_candidate_key=202608230200
free_candidate_key=202608230201
development_key(b,N)=202608231000+100b+N
validation_key(b,N)=202608232000+100b+N
evaluation_key(b,N)=202608239000+100b+N
resampling_key=202608239999
b in {0,...,11}.
```

To obtain a uniform integer in `{0,...,m-1}` from successive unsigned 32-bit
outputs, set `L_m=2^32-(2^32 mod m)`, reject outputs `u>=L_m`, and return
`u mod m`. Geometry components use `m=5`, Markov transitions use `m=10`,
coefficient coordinates use `m=129`, block resampling uses `m=12`, and
episode-index resampling uses the exact stratum size. Rejections consume the
next output in the same counter namespace. This rule, the state order and the
keys make every frozen finite panel single-valued.

## One training and selection procedure

There are 12 independent host blocks `b=0,...,11`, but only one final policy
per trainable arm. Within each purpose and roster, all candidates and arms see
the same host episodes.

For each block, the development batch has 64 episodes: 32 at `N=4` and 32 at
`N=8`. Across 12 blocks this is 768 episodes, exactly 384 per training roster
and 64 per initial field state at each roster. The validation batch has 256
episodes per block: 128 at each training roster. Across 12 blocks this is
3,072 episodes, exactly 1,536 per roster and 256 per initial state at each
roster. Development, validation and evaluation namespaces are disjoint.

Treatment selection is exact:

1. Candidate ID `T0000` is `theta=0`. IDs `T0001,...,T2047` are independent
   uniform draws from `A^4`, with replacement.
2. Score every ID by mean `Z` over all 768 development episodes.
3. The 32 finalists are forced anchor `T0000` plus the best 31 other IDs.
   Order by decreasing score, lexicographically increasing coefficient tuple,
   then increasing candidate ID.
4. Score every finalist on all 3,072 validation episodes and select the first
   under the same order. The result is the single `theta_T`.

FREE residual selection is exact:

1. Candidate ID `F0000` is `phi=0` paired with `theta_T`. IDs
   `F0001,...,F2047` are independent uniform draws from `A^4`, with
   replacement, all paired with the same `theta_T`.
2. Use the identical 768 development episodes and scoring rule.
3. The 32 finalists are forced anchor `F0000` plus the best 31 other IDs,
   with decreasing score, lexicographically increasing `phi`, then increasing
   candidate ID.
4. Score all finalists on the identical 3,072 validation episodes and select
   the first. The result is the single `phi_F`.

Forced validation anchors make the validation comparisons constructive:
selected treatment validation score is at least the evaluated zero-anchor
score, and selected FREE validation score is at least the evaluated
`FREE-EMBED` score by the deterministic argmax definition. There is no
adaptive expansion, early stop, hyperparameter search, per-roster selection,
evaluation-data selection or result-dependent retraining.

## Frozen evaluation panel

For every block `b` and every `N in {4,6,8,12}`, evaluate the one selected
treatment, one selected FREE, `T-P`, `F-P`, `EQ`, `DENS`, `MASS`, `MARG0`,
`ORACLE` and `FREE-EMBED` on the same 512 fresh episodes. Episode `e` begins
in exactly `S_((e+b) mod 6)`. Across all 12 blocks at a roster, each initial
state occurs exactly 1,024 times. No evaluation episode selects or changes a
coefficient.

The complete normative panel is 12 blocks by four rosters by 512 episodes by
every named arm. Training-roster cells are diagnostics. Only `N={6,12}`
enters the primary value decision.

## Quantization and residual diagnostics

For every positive-weight nonoracle arm, retain its exact pre-LR real quota
`c_i=Qw_i/sum_j w_j` and compute the non-normative shadow endpoint obtained by
substituting `c_i` for `n_i`. After full release, report by roster:

- the paired mean legal-minus-shadow episode score for treatment, FREE,
  `T-P`, `F-P`, `DENS`, `MASS` and `MARG0`;
- the fraction of treatment-versus-FREE and treatment-versus-`T-P` records
  whose exact quota vectors differ but legal LR commands coincide;
- the mean and maximum exact quota-vector L1 separation for those pairs; and
- the mean episode-step range `max_i r_i-min_i r_i` for selected FREE.

These diagnose integer collapse and residual extinction. They are withheld by
the no-partial rule, are descriptive only, and never change a threshold,
route or claim. The empirical claim remains about the frozen legal integer
action problem.

## Activity, competence and no-partial gate

Question-relevant activity begins when the first candidate score is accepted
on any frozen development host episode. After that boundary, a change to any
host, policy, comparator, batch, seed, gate, estimand, uncertainty, threshold,
route or claim field requires a new complete revision.

Before any coefficient identity, policy value, contrast, diagnostic or branch
is released outside the owning technical lane, all of the following must pass:

1. A separate CM accepts exact host, integral, LR, policy, reassociation,
   oracle, RNG/substream, training, panel, resampling and serialization
   conformance.
2. Every frozen candidate score, finalist score and evaluation cell completes
   at the exact count with no missing or nonfinite normative value.
3. Every action is legal; on every step ORACLE is no worse than every legal
   named arm; and `FREE-EMBED` equals treatment weights and commands on every
   development, validation and evaluation record.
4. The forced anchors are present in their finalist sets, the two selected
   IDs are the exact deterministic validation argmaxes, and their implied
   anchor inequalities hold exactly.
5. One serialized `theta_T` and one serialized `(theta_T,phi_F)` are used
   unchanged in every evaluation block and roster.

Any failure returns `NO_QUESTION_RELEVANT_DATA`. Release no partial policy
values, rankings, selected coefficients or scientific polarity; return
unchanged science to CM for repair.

## Episode-level host support

For held-out roster `N`, block `b` and episode `e`, define the single
episode predicate

```text
O_bNe=1 iff there exists a step t such that
         n_ORACLE,bNet != n_EQ,bNet
         and U_t(n_ORACLE,bNet)<U_t(n_EQ,bNet).
```

Define `J` below and

```text
H_J=min over N in {6,12} of (J_ORACLE,N-J_EQ,N).
```

Host support requires both `L*(H_J)>=1/500` under the exact finite resampling
law and, separately at each held-out roster,
`sum_{b,e} O_bNe >= 1536`, exactly one quarter of the 6,144 pooled episodes.
This is an episode count built from an explicit step witness; no step quantity
is treated as an episode observation. Failure returns `HOST_SUPPORT_ABSENT`
and no treatment ranking.

## Estimands for one selected policy

For arm `p`, roster `N` and evaluation block `b`, define

```text
J_p,N,b = mean Z over its 512 episodes
R_p,N,b = mean of the 128 smallest Z values, sorted ascending with episode
          index as the exact tie key.
M_p,N   = (1/12)sum_b M_p,N,b, for M in {J,R}.
```

These estimate performance and lower-quartile robustness of the one selected
parameterization conditional on the frozen training panel. They do not
estimate the performance of a distribution of independently retrained
policies.

Let `B={EQ,DENS,MASS,MARG0}`. For `M in {J,R}` define

```text
V_M=min over b0 in B and N in {6,12} of (M_T,N-M_b0,N)
F_M=min over N in {6,12} of (M_T,N-M_FREE,N)
A_M=min over N in {6,12} of (M_T,N-M_T-P,N)
P_M=min over N in {6,12} of (M_FREE,N-M_T,N)
G_M=max over b0 in B of min over N in {6,12} of (M_b0,N-M_T,N)
H_J=min over N in {6,12} of (J_ORACLE,N-J_EQ,N).
```

The minimum operators require the relation at both held-out rosters. `V_M`
requires treatment superiority over every frozen nonoracle baseline.

```text
meaningful_superiority_margin delta=1/500
noninferiority_margin nu=1/1000.
```

## Complete finite resampling decision law

Use exactly `B_boot=20,000` paired hierarchical stratified bootstrap draws
under `resampling_key=202608239999`. The selected policies and their
coefficients remain fixed.

For draw `q=0,...,19999`:

1. Draw 12 source block identifiers `b*(q,j)` independently and uniformly
   from `{0,...,11}`, for pseudo-block occurrence `j=0,...,11`.
2. For every occurrence `j`, roster `N` and initial state `h`, let
   `E(b*,N,h)` be the episode indices in source block `b*` whose frozen
   initial state is `S_h`. Draw exactly `|E(b*,N,h)|` indices independently
   with replacement from that stratum. A repeated source block in two
   occurrences receives independent within-stratum draws.
3. Apply the identical sampled episode multiset to every arm. Each
   pseudo-block therefore contains exactly 512 episodes with the source
   block's frozen state counts.
4. Recompute each pseudo-block `J`. For `R`, sort sampled occurrences by
   `(Z,source_episode_index,resample_position)` and average the first 128.
   Average the 12 pseudo-block occurrences, and then recompute every min/max
   composite `V,F,A,P,G,H` from that draw.

Every uniform index uses the exact 32-bit rejection rule above and a disjoint
counter containing `(q,j,N,h,draw_position,rejection_index)`. For any scalar
composite `X`, sort its 20,000 values as
`X_(1)<=...<=X_(20000)` using draw index as the exact tie key and define

```text
L*(X)=X_(500)
U*(X)=X_(19500).
```

`L*` and `U*` are registered finite bootstrap decision bounds. They are not
asserted to be confidence limits, do not carry a nominal coverage guarantee,
and support no Bonferroni or family-wise error claim. Their sole role is the
frozen branch rule below. Point estimates and any other summaries are
descriptive and cannot change routing.

## Exact terminal routing

Apply this precedence once, only after complete durable panel release:

1. Any competence failure: `NO_QUESTION_RELEVANT_DATA`; no partial value or
   scientific polarity.
2. Competence passes but either host-support condition fails:
   `HOST_SUPPORT_ABSENT`; no treatment-value claim.
3. `PERFORMANCE_SUPPORTED` iff
   `L*(V_J)>=delta`, `L*(F_J)>=-nu`, and `L*(A_J)>=delta`.
4. `ROBUSTNESS_SUPPORTED` iff the analogous three inequalities hold for `R`.
5. If both predicates hold, return `ASSOCIATION_VALUE_SUPPORTED_BOTH`. If
   exactly one holds, return `ASSOCIATION_VALUE_SUPPORTED_PERFORMANCE` or
   `ASSOCIATION_VALUE_SUPPORTED_ROBUSTNESS`.
6. If neither holds and `max(L*(P_J),L*(P_R))>=delta`, return
   `FREE_PREFERRED`.
7. Otherwise, if `max(L*(G_J),L*(G_R))>=-nu`, return
   `GENERIC_ALLOCATION_SUFFICES`.
8. Otherwise, if `U*(A_J)<delta` and `U*(A_R)<delta`, return
   `NO_ASSOCIATION_SEPARATION`.
9. Otherwise, if `U*(V_J)<delta` and `U*(V_R)<delta`, return
   `NO_TREATMENT_VALUE_OVER_FROZEN_BASELINES`.
10. Otherwise return `NONIDENTIFIED_WITHIN_FROZEN_BUDGET`.

The quantization and residual diagnostics never alter this map. No branch
changes the theorem or transfers evidence to r05.

## No-partial-value boundary

Until all competence gates pass and the full panel plus all 20,000 resampling
draws are durable, selected coefficients, returns, contrasts, bounds,
diagnostics, ranks and partial cells remain inside the owning CM. A launcher,
dependency, conformance, serialization or missing-cell failure is unchanged-
science engineering work. There is no apparent-success or apparent-failure
stop.

After release, the same-direction EM interprets exactly one branch under this
map. The existing same-direction ChatGPT Pro conversation must then validate
the complete result interpretation before any terminal empirical claim.

## Maximum claim and branch ceilings

For a supported performance or robustness branch, the maximum claim is:

> On the frozen 1-D Markov-field host and under the registered finite panel,
> margins and resampling decision law, one single roster-independent VQFP
> coefficient vector selected using only `N={4,8}` met the named held-out
> metric criteria at both `N=6` and `N=12` over every frozen nonoracle
> baseline, was noninferior to the matched residual FREE comparator, and lost
> value under full half-cycle measure reassociation. This is evidence for a
> useful physical-association inductive bias for that selected policy on this
> host.

This is not a population-coverage theorem, a training-procedure repeatability
claim or physical-measure necessity. It does not establish arbitrary-geometry
generalization, noninferiority to jointly reoptimized eight-dimensional FREE,
in-episode roster-change robustness, 2-D/UAV performance, flight, safety or
deployment.

`FREE_PREFERRED` supports only that the conditionally enlarged residual policy
met its named advantage criterion. `GENERIC_ALLOCATION_SUFFICES` supports only
the named generic baseline's registered noninferiority relation.
`NO_ASSOCIATION_SEPARATION` and
`NO_TREATMENT_VALUE_OVER_FROZEN_BASELINES` are bounded null branches on this
host. `HOST_SUPPORT_ABSENT`, `NO_QUESTION_RELEVANT_DATA` and
`NONIDENTIFIED_WITHIN_FROZEN_BUDGET` authorize no policy ranking beyond their
exact statements.

## Strongest alternatives

The strongest alternatives are:

- the exact diminishing-return structure, approximated without learning by
  `MARG0` and bounded above by ORACLE;
- field adaptation without physical measure (`DENS`) or generic workload
  allocation (`MASS`);
- useful conditional residual freedom in FREE;
- an unevaluated jointly reoptimized eight-dimensional FREE policy;
- finite candidate-search luck or lower-dimensional regularization rather
  than physical association;
- legal LR quantization collapsing distinct real quotas to the same command;
  and
- insufficient oracle-over-equal-mass headroom in the sampled host.

The single strongest alternative after a supported branch is an unevaluated
jointly reoptimized eight-dimensional FREE policy. Within the tested panel,
the strongest causal alternative is finite-panel and selection-specific
advantage aligned with a generic diminishing-return proxy, not a necessary
role for learned physical association.

## UAV bridge and deferred successors

The toy maps to ordered UAV stations along a ridgeline or linear corridor.
Cell length is patrol footprint, the Markov field is changing hazard demand,
cell mass is workload, and `n_i/600` is sensing duty under a shared team
budget. Held-out rosters test one shared allocation law under changed team
size.

The object deliberately omits 2-D polygon shape, terrain traversal, turning,
propulsion, collision avoidance, distance-decayed communication/relay cost,
moving footprints, noise, mid-episode aircraft failure, re-tessellation,
vehicle dynamics and safety. Neither a distance-decayed relay host nor an
`N -> N-1` mid-episode roster-collapse host is silently added here. A
supported branch can only motivate a separately defined 2-D
terrain/communication object or dynamic-roster object, each with new controls,
resources, closure and authorization.

## Prospective total-cost boundary

These are Portfolio planning projections, not CM estimates, leases or
activity authorizations. R02's 4-D conditional FREE search, added `MARG0`,
shadow diagnostics and 20,000 finite resamples must fit inside this unchanged
ceiling:

| Case | Engineering | CPU core-hours | Parallel wall | Peak RSS | Scratch | Durable | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|
| Low | 6 engineer-days | 150 | 8 h | 8 GiB | 10 GiB | 2 GiB | none |
| Central | 12 engineer-days | 600 | 24 h | 16 GiB | 40 GiB | 8 GiB | none |
| High | 20 engineer-days | 1,800 | 72 h | 32 GiB | 120 GiB | 24 GiB | none |

The projection covers native host and batched rollout construction, both
searches, every control and diagnostic, the 12-block panel, exact resampling,
serialization and one accepted result packet. A materially larger projection
returns to Portfolio before construction or compute.

## Provider, production, stop and revisit law

This complete r02 replacement requires one ruling in the existing same-VQFP
ChatGPT Pro conversation. Only `CLOSED` followed by same-direction EM intake
completes its scientific definition boundary. Gemini advice has no closure or
selection role.

Stop now at definition freeze. No CM request, construction, source, build,
test, runtime, compute, lease, identity, coordinate, model, checkpoint, panel,
result, partial value, Git, deployment or flight action follows. Pro
`REVISION_REQUIRED` permits only a complete replacement revision, never an
inline patch. Pro `CLOSED` still requires a separate Portfolio construction
decision and CM feasibility/technical acceptance.

After question-relevant activity begins, no science-bearing field can change.
A supported branch may justify only a new bridge object. A clear FREE or
generic-control branch redirects or ends treatment investment. Support absent
or nonidentified returns to Portfolio opportunity-cost judgment; repetition
requires a distinct object with a concrete new discriminator rather than
silent budget growth. Revisit this exact definition only for Pro-required
repair before activity or later complete-result validation after an authorized
run.

```text
observed_fact=R01 received exact Pro REVISION_REQUIRED with six bounded protocol defects; mutually blind Gemini advice identified comparator-search, residual-scaling, reassociation, generic-marginal and quantization concerns; r02 resolves the accepted concerns as one complete definition and no empirical activity has begun.
local_action_fence=The committed r01 provider turns are no-resend; this artifact performs no provider, CM, source, runtime, compute, lease, result, partial-value, Git, deployment or flight action.
scientific_stage_continuation=Portfolio may authorize exactly one same-conversation Pro reclosure of this complete r02 revision; production remains separately fenced.
root_decision_class=Portfolio provider-investment/current-definition decision only; no allocation or production decision is made here.
applies_to=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-02 only.
does_not_imply=pro_closed|construction_feasible|empirical_activity|efficacy|held_out_N_value|measure_necessity|r05_resume|UAV_value|lease|compute|Git|deployment|flight
continuation_owner=Dedicated Portfolio Root for reclosure authorization and later selection; same-direction VQFP EM for Pro intake; Operational Root and matching CM only after an exact Portfolio bridge.
```

# ChatGPT External Pro mathematical-closure question — VQFP-FERL r01

You are the dedicated same-direction scientific reviewer for one prospective
HMASD/MARL object. This is a result-blind mathematical and causal review, not a
code review, portfolio ranking or implementation acceptance.

Return exactly one disposition:

```text
CLOSURE_AUTHORITY_DECISION=CLOSED
```

or

```text
CLOSURE_AUTHORITY_DECISION=REVISION_REQUIRED
```

Also state:

```text
EXACT_REVISION=VQFP-FERL-SCIENCE-20260821-01
RESULT_BLIND=true
SCIENCE_BEARING_DEFECT_COUNT=<integer>
```

For `REVISION_REQUIRED`, enumerate every exact mathematical, causal or
interpretive defect and the smallest sufficient correction. For `CLOSED`, say
why the treatment, strict containment, prerequisites, inference, branches and
claim ceiling are jointly single-valued. In both cases give the strongest
nonmechanism alternative, maximum defensible claim and single highest-
information later discriminator. Do not assess repository code, tests,
runtime, hashes, files or engineering feasibility.

## Exact prospective object

### Question and provenance isolation

This is a new object, not a rerun of the earlier saturated periodic VQFP host.
No old result, threshold, seed, coordinate, checkpoint or claim transfers. It
asks whether a hard correctly associated Voronoi-measure factor is a useful
finite-budget inductive bias when one shared variable-`N` policy allocates one
fixed physical sensing-and-relay budget. Training uses `N={4,8}`; untouched
claim populations are `N={6,12}`. One parameterization is used everywhere.

The direct treatment is `FERL-MEASURE`. The strong comparator is
`FREE-MEASURE-CONTAIN`, which has the same information, messages, actions,
backbone, critic, samples, optimizer work and nominal parameters and literally
recovers FERL when its free residual is zero. Other controls are nonlearned
`EQUAL-MASS`, matched learned `FREE-NO-MEASURE-PORT`, frozen
`REASSOCIATED-MEASURE`, and current-state `ANALYTIC-ONE-STEP`.

### Host and physical process

The domain is an open ridgeline `x in [0,1]`; an episode has 64 simultaneous
ten-second decisions. For `N`, draw `N+1` independent `Gamma(alpha,1)` values
and set

```text
g_j=0.02/(N+1)+0.98*raw_j/sum raw,
x_i=sum_(j=0..i-1)g_j.
```

Use `alpha=1` for IID and `0.35` for CLUSTER. Open Voronoi boundaries are
`b_0=0`, `b_N=1`, `b_i=(x_i+x_(i+1))/2`, cells are
`C_i=[b_(i-1),b_i)`, and `v_i=b_i-b_(i-1)`. Opaque actor handles are a fresh
permutation of physical rank.

Two action-independent fronts have initial centers in `[0.10,0.40]` and
`[0.60,0.90]`; velocities are independently uniform on
`{-0.012,-0.008,+0.008,+0.012}`, reflect at the endpoints, and independently
flip or retain sign at tick 32. With `w=0.08`, amplitudes 1 and 0.7,

```text
p_t(x)=min(1,sum_m A_m*max(0,1-abs(x-mu_m(t))/w)),
H_t={x:p_t(x)>=0.40}.
```

Each cell has exact `gradient_mass_i=integral_Ci p_t` and
`high_gradient_length_i=length(C_i intersection H_t)`.

The action-independent link field is

```text
link_t(x)=0.55+0.35*cos(pi*(x-zeta_0-0.004*t))^2,
zeta_0~Uniform[0,1),
link_i=(1/v_i)*integral_Ci link_t.
```

Each joint action has nonnegative sensing `s_i` and relay `r_i` with exact
roster-invariant conservation `sum_i(s_i+r_i)=E_total=0.20`. With backlog
`B_i(0)=0`,

```text
coverage_i=1-exp(-4*s_i/v_i),
acquired_i=coverage_i*gradient_mass_i,
unserved_length_i=(1-coverage_i)*high_gradient_length_i,
delivered_i=min(B_i+acquired_i,3*link_i*r_i),
B_i'=B_i+acquired_i-delivered_i.
```

Training reward is the common scalar `-(0.6*u_t+0.4*b_t)`, where `u_t` is
total unserved high-gradient length divided by total high-gradient length and
`b_t` is next backlog divided by cumulative offered gradient mass.

The lower-is-better direct episode endpoints are:

1. `U`, integrated unserved high-gradient length divided by integrated offered
   high-gradient length;
2. `D90`, the 0.90 quantile of normalized delays from a front center entering
   a cell after two ticks outside it until cumulative sensing coverage reaches
   0.75, with noncompletion censored at the remaining episode horizon; and
3. `R=1-total_delivered/total_gradient_mass`.

Fewer than 40 discovery events per seed/cell makes that cell nonanswerable.

### Information, policy and literal containment

Before action, each agent receives own and immediate physical-neighbor current
gradient-density, backlog, link, cell length,
previous sensing/relay shares, `N/12`, `t/63`, and boundary tokens. Both arms
receive the same records. Neither sees rank/handle, layout label, front
identity/center/velocity, future sign flip, future field, analytic action,
evaluation cell, intervention or arm label. The simulator-truth high-gradient
mask/length scores endpoints and may reach the training critic, but never the
actor. The actor's gradient-density coordinate is the exact deployable cell-
average sensor reading for this noise-free object.

Both arms have the same width-64 record encoder, width-64 shared GRU,
bounded-degree physical-neighbor sum, two base logits, two residual logits and
set-pooled centralized critic. The base trainable route may use every content
coordinate except all own/neighbor cell-length coordinates. Cell length enters
the fixed measure factor and the residual-length port only. The residual output
layer is initialized to exact zero in both arms; both execute it and retain its
parameters and optimizer slots. FERL fixes its multiplier to zero with no
residual gradient; FREE uses multiplier one.

For mode `m in {SENSE,RELAY}`:

```text
FERL logit_(i,m)=log(v_i)+q_(i,m),
FREE logit_(i,m)=log(v_i)+q_(i,m)+residual_(i,m),
pi=softmax over all 2N slots,
y~Dirichlet(64*pi),
action=0.20*y.
```

Setting residuals to zero makes FREE identical to FERL on every history. The
total Dirichlet concentration is roster-invariant. Evaluation uses fresh
address-based Gamma streams frozen independently by arm. Support uses policy
means, not sample noise.

Before any scientific identity, TEST-only checks at every registered N/layout
must prove residual-zero action-distribution identity, opaque-handle
permutation equivariance and array-order invariance. There is one identical
simplex projector/mask and no per-agent floor, free service or hidden overhead
that grows total physical effort with N. Failure is invalidity, not a treatment
result.

### Controls

`EQUAL-MASS` assigns `s_i=r_i=0.20/(2N)`.

`FREE-NO-MEASURE-PORT` is a third learned matched arm identical to FREE except
that each explicit length at the fixed factor and residual port is the constant
`1/N`; true lengths traverse masked zero-gradient work-matching slots, and no
trainable base route receives them. It has the same architecture, parameters,
updates and action law and must pass support and competence before it can
support an explicit-measure-port claim.

`ANALYTIC-ONE-STEP` sees only the current physical state and exactly minimizes
the next-tick `0.6*u_t+0.4*b_t` over the same nonnegative fixed-total action;
ties use physical rank before handle permutation. It is a feasible opportunity
witness, not a dynamic optimum/bound or deployment comparator.

`REASSOCIATED-MEASURE` is a frozen-checkpoint intervention. On even episodes it
replaces only every explicit measure-factor and residual-length input with the
next physical cell's length; on odd episodes with the previous cell's length.
Physical cells, service law, plume, links, content, backlog, recurrent state,
action streams and length multiset are unchanged. It is applied separately to
FERL and FREE with no retraining and is explicitly off-manifold.

### Training, evaluation and activity boundary

There are 24 fresh paired seed blocks. Each learned arm trains for exactly 600
PPO updates, each with 32 complete balanced episodes over training `N` and
layouts. GAE uses gamma .99/lambda .95; PPO clip .20, value coefficient .5,
entropy .01, gradient clip .5, four epochs and 512-tick minibatches; AdamW uses
learning rate 3e-4, betas .9/.999, epsilon 1e-8 and zero weight decay. Only the
post-update-600 checkpoint is evaluated. Every arm/control is evaluated on 128
fresh episodes in every `N={4,6,8,12}` by IID/CLUSTER cell. Common physical
tapes are paired; action streams are independent by arm. There is no budget,
checkpoint, seed, threshold or architecture search.

Question-relevant activity begins immediately before the first production
optimizer mutation or first conclusion-bearing production evaluation. TEST-
only arithmetic/native-equivalence fixtures with explicitly non-scientific
tapes do not cross it.

### Inference and prerequisites

For lower-is-better endpoint `X`, define `Delta_X(A,B)=X_B-X_A`, positive when
A is better. The claim family has 84 held-out contrasts: three endpoints,
two held-out N, two layouts and seven comparisons (FERL/FREE, FERL/EQUAL,
FREE/EQUAL, FERL-intact/reassociated, FREE-intact/reassociated,
FREE/FREE-NO-MEASURE-PORT, ANALYTIC/EQUAL). Use two-sided paired-mean Student
intervals with 23 degrees of freedom and Bonferroni familywise 95% coverage
across all 84. Material margins
are `.04` for U, `.05` for D90 and `.04` for R; non-harm margins are half.
Practical equivalence requires the whole interval inside the corresponding
plus/minus material band.

Competence has a separate 24-member prerequisite family. For each of the three
learned arms, four registered N and two layouts, define

```text
C_A=(U_EQUAL-U_A)-0.20*(U_EQUAL-U_ANALYTIC).
```

Use the same Student/Bonferroni construction across all 24 and require every
lower endpoint above zero.

Prerequisite order is:

1. complete atomic validity, exact conservation, nonnegative arithmetic,
   leakage/selection absence and positive denominators;
2. physical opportunity: in each held-out cell, ANALYTIC/EQUAL U lower bound
   above .08, at least one secondary above its material margin, and EQUAL mean
   U in [.20,.85];
3. action support: for each learned arm/cell, at least 20/24 seeds have at least half
   their ticks with policy-mean per-agent total-share range >=.03 and at least
   80% of ticks with policy-mean total SENSE and RELAY shares each in [.15,.85];
4. competence: all 24 C lower bounds positive, each arm R<.90, and no endpoint
   materially worse than EQUAL;
5. answerability: >=40 discovery events per seed/cell, learned U/D90/R means
   in [.08,.92], and every FERL/FREE interval half-width <= half its material
   margin.

Downstream contrasts are descriptive after the first failed prerequisite.

### First-match result branches

1. invalid/incomplete;
2. no physical opportunity;
3. no allocation/action support;
4. learned or containing-comparator competence failure;
5. endpoint nonanswerable;
6. FERL target harm versus EQUAL/non-harm bounds;
7. FERL treatment-specific value: at least one held-out N qualifies in both
   layouts with FERL/FREE and FERL/EQUAL U lower bounds >.04, global secondary
   non-harm, and intact/reassociated FERL U lower bound >.04 in qualifying cells;
8. FREE superiority: at least one held-out N qualifies in both layouts with
   FREE/FERL U lower bound >.04 and global secondary non-harm;
9. explicit-measure-port-only value: all FERL/FREE intervals practically
   equivalent, both measure-bearing arms beat EQUAL materially on U at one
   held-out N in both layouts, competent FREE beats competent no-port, and
   reassociation materially worsens both measure-bearing arms there;
10. generic allocation value without measure specificity: a learned arm beats
    EQUAL but neither reassociation nor FREE/no-port contrast qualifies;
11. target-specific no-materiality: every learned/learned and learned/EQUAL
    interval lies inside its endpoint's practical-equivalence band;
12. unresolved valid evidence.

Branches retain/delete/modify only this exact family as named; none triggers a
new budget, seeds, checkpoint, surface or activity.

### Strongest alternatives and ceiling

A positive can arise from finite-budget conditioning, initialization or
regularization rather than unique quadrature; global softmax may be the useful
primitive; backlog/link features or task geometry may dominate; centralized
normalization may not transfer; and reassociation is off-manifold.

Maximum claim is exact finite 1-D fixed-effort value for one 600-update shared
policy on the qualifying registered held-out N/layouts. No arbitrary N,
in-episode churn, asymptotic superiority, unique mediation, 2-D plume, hardware,
safety, deployment or flight claim is permitted. A no-material result is
target-specific, not unrestricted equivalence or family deletion.

Please provide the exact closure disposition now.

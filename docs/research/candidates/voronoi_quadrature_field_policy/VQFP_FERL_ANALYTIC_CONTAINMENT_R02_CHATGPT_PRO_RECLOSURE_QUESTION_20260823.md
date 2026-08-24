# VQFP-FERL analytic-containment revision-02 ChatGPT External Pro reclosure question

Continue the existing dedicated ChatGPT Pro scientific conversation for the
VQFP direction. This is one complete replacement composite, not a patch.

```text
OBJECT=VQFP-FERL-ANALYTIC-CONTAINMENT-COST-COLLAPSE-R01
EXACT_REVISION=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-02
```

The preceding revision received `REVISION_REQUIRED` with six science-bearing
defects. This replacement freezes exact reassociation and action-sensitive
semantics; in-domain FREE strictness; per-roster witnesses; oracle and control
predicates; a canonical proof machine and caps; disjoint scientific and
bounded-noncertification outcomes; and exact `G` to `G'` routing.

No theorem result, empirical result, implementation evidence, other-provider
answer, portfolio ranking or engineering fact is supplied. Review only the
mathematical and causal definitions. Do not review code, tests, hashes,
transport, proof implementation or engineering feasibility.

Your first nonempty line must be exactly `CLOSED` or `REVISION_REQUIRED`. Then
state:

```text
EXACT_REVISION=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-02
SCIENCE_BEARING_DEFECT_COUNT=<integer>
```

If closed, the count must be zero; state the maximum defensible claim and
strongest remaining alternative. If revision is required, enumerate every
exact defect, its minimum correction and the maximum unrepaired claim. Do not
silently rewrite the object or treat an implementation preference as a science
defect.

BEGIN COMPLETE REPLACEMENT COMPOSITE

## Identity, decision and isolation

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FERL-ANALYTIC-CONTAINMENT-COST-COLLAPSE-R01
revision=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-02
host=VQFP-UNSATURATED-VORONOI-FIELD-COVERAGE-1D-v2
stage=prospective_definition_only
supersedes_for_future_analytic_work=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-01
supersedes_r05=false
scientific_activity_begun=false
construction_authorized=false
empirical_activity_authorized=false
theorem_execution_authorized=false
pro_closed=false
```

This revision is distinct from VQFP-FERL r05 and draws no r05 efficacy
evidence. Its only terminal scientific branches are
`RETAIN_G_UNRESTRICTED`, `RETAIN_G_PRIME_ONLY` and
`DELETE_ANALYTIC_CONTAINMENT_OBJECT`. “Unrestricted” means every input in
frozen finite class `G`, not arbitrary continuous geometry. No third class,
approximate substitute, result-dependent precision, altered effort lattice,
weakened comparator, fixture extrapolation or per-`N` tuning is permitted.

## Variable-N physical domain

```text
physical_domain=[0,1]
N_train={4,8}
N_heldout={6,12}
N_registered={4,6,8,12}
one_shared_parameterization_across_N=true
per_N_head_or_tuning=false
in_episode_roster_change_claim=false
```

For ordered sites `0<x_1<...<x_N<1`, define

```text
b_0=0
b_N=1
b_i=(x_i+x_(i+1))/2
C_i=[b_(i-1),b_i) for i<N
C_N=[b_(N-1),1]
v_i=b_i-b_(i-1).
```

Physical rank is increasing coordinate. Learned coefficients cannot depend on
rank, actor label or `N`. Relabeling complete cell records permutes policy
weights and commands with those records without altering physical cells.

### Primary class G

Let `D_N=384N`. A geometry belongs to `G_N` exactly when:

- `x_i=k_i/D_N` for integers `k_i`;
- `1/(2N)<=x_(i+1)-x_i<=3/(2N)`;
- `1/(3N)<=v_i<=5/(3N)`; and
- `max_i v_i-min_i v_i>=1/(64N)`.

Set `G=union_N G_N` over registered rosters.

### Frozen fallback G'

A geometry belongs to `G'_N` exactly when it belongs to `G_N` and:

- each site is a multiple of `1/(96N)`;
- `3/(4N)<=x_(i+1)-x_i<=5/(4N)`; and
- `2/(3N)<=v_i<=4/(3N)`.

The same heterogeneity bound remains. `G'=union_N G'_N`. `G'` preserves every
roster, field, legal action, physical command, endpoint, treatment, FREE
comparator, control, oracle, claim and proof predicate; only grid granularity
and conditioning differ. No conclusion transfers from `G` to `G'`.

## Primary fields and exact unsaturated target

Every pair below is primary, including the uniform field:

```text
beta in {-1/4,0,1/4}
gamma in {0,1/4}
f_(beta,gamma)(x)=1+beta(2x-1)+gamma(6x(1-x)-1).
```

Every field is at least `1/2` and integrates to one. Define
`m_i=integral_(C_i) f(x) dx` and `d_i=m_i/v_i`.

Let `Q=120`. A legal allocation is `n in Z_nonnegative^N` with
`sum_i n_i=Q`. Physical sensing duty is `a_i=n_i/(5Q)=n_i/600`, so total
effort is exactly `1/5`. The sole lower-better endpoint is

```text
U(n;g,beta,gamma)
=sum_i m_i/(1+a_i/v_i)
=sum_i m_i v_i/(v_i+a_i).
```

Every finite action leaves positive unserved mass; each quantum has positive,
strictly diminishing benefit. There is no saturation threshold, tolerance,
hidden projection, future state or alternate command map.

## Treatment, strict FREE and exact command map

Let `A={j/16:j=-64,...,64}`; every trainable coefficient lies in `A`. Define

```text
dbar=(1/N)sum_i d_i
q_i=theta_0+theta_1 d_i+theta_2 dbar+theta_3(d_i-dbar)^2
B_i=1+q_i^2
w_i^T=v_i B_i
r_i=clip_[-1/2,1/2](phi_0+phi_1(d_i-dbar)+phi_2(v_i-1/N)
                     +phi_3(d_i-dbar)(v_i-1/N))
w_i^F=v_i B_i(1+r_i)^2.
```

Treatment and matched FREE use the same `theta`; FREE additionally owns `phi`.

For any positive rational weight vector `w`, define exact largest remainder
`LR(w)`:

```text
W=sum_i w_i
y_i=Qw_i/W
z_i=floor(y_i)
rho_i=y_i-z_i
R=Q-sum_i z_i.
```

Order cells by descending `rho_i`, then increasing original left boundary
`b_(i-1)`, and add one quantum to the first `R` cells. This is total,
deterministic, legal and conserves `Q`. Define `n^T=LR(w^T)` and
`n^F=LR(w^F)`.

For `H in {G,G'}`, `EMBED(H)` means universally over registered roster,
geometry in `H`, field and `theta in A^4`:

```text
n^F(theta,phi=0)=n^T(theta),
```

with identical weights, quotas, remainders and physical commands. Because
`r_i=0`, this is literal containment.

## Geometry-only reassociation

For each geometry let

```text
i_max=min{i:v_i=max_j v_j}
i_min=min{i:v_i=min_j v_j}.
```

Heterogeneity gives `i_max!=i_min`. Let `P_g` swap those two indices and fix
all others. The reassociated policy length at record `i` is
`lambda_i=v_(P_g(i))`. No other object is permuted or substituted.

Reassociation preserves original sites/cells; physical `v_i` in endpoint and
service law; `m_i,d_i`; physical command coordinate; LR left-boundary tie key;
field and parameters; legal actions and total effort.

```text
w_i^(T,P)=lambda_i B_i
r_i^P=clip_[-1/2,1/2](phi_0+phi_1(d_i-dbar)+phi_2(lambda_i-1/N)
                       +phi_3(d_i-dbar)(lambda_i-1/N))
w_i^(F,P)=lambda_i B_i(1+r_i^P)^2
n^(T,P)=LR(w^(T,P))
n^(F,P)=LR(w^(F,P)).
```

Counts apply to original physical cells using original `v_i,m_i`. `P_g`
depends only on frozen geometry, never field, output, endpoint, result or
desired separation; there is no retraining. `EMBED_P(H)` universally requires
`n^(F,P)(theta,phi=0)=n^(T,P)(theta)`.

## Equal mass and exact action-sensitive pair

Define `n_i^EQ=Q/N`. For every ordered `(d,r)`, `d!=r`, define
`n^(d->r)=n^EQ-e_d+e_r`. Every donor stays nonnegative. Let

```text
delta_(d,r)=U(n^(d->r))-U(n^EQ)
eta_(d,r)=abs(delta_(d,r)).
```

Order pairs by descending `eta`, then increasing donor, then increasing
receiver. The first is `(d*,r*)`; set `n^AS=n^(d*->r*)` and
`AS_MAG=eta_(d*,r*)`. `ACTION_SENSITIVE` means exactly `AS_MAG>0`. All
equalities and orders are rational; no tolerance or outcome-dependent pair
selection exists.

## Frozen per-roster control witnesses

For every registered `N`, set

```text
x_i^*=(2i-1)/(2N) for i!=2
x_2^*=3/(2N)+1/(8N).
```

This is in `G'_N` and `G_N`, with

```text
v_1^*=17/(16N)
v_2^*=1/N
v_3^*=15/(16N)
v_i^*=1/N for i>=4.
```

Use primary field `beta^*=-1/4`, `gamma^*=0` and
`theta^*=(0,0,0,0)`. Registered treatment commands are:

```text
N=4:  (32,30,28,30)
N=6:  (21,20,19,20,20,20)
N=8:  (16,15,14,15,15,15,15,15)
N=12: (11,10,9,10,10,10,10,10,10,10,10,10).
```

Max/min reassociation swaps cells 1 and 3, giving:

```text
N=4:  (28,30,32,30)
N=6:  (19,20,21,20,20,20)
N=8:  (14,15,16,15,15,15,15,15)
N=12: (9,10,11,10,10,10,10,10,10,10,10,10).
```

Equal mass is `Q/N` in every coordinate. For `H in {G,G'}` and each roster,
`CONTROL_ND(H,N)` is the fixed conjunction on this witness:

```text
n^T != n^(T,P)
n^T != n^EQ
n^(T,P) != n^EQ
U(n^T)<U(n^EQ)<U(n^(T,P))
AS_MAG>0.
```

This is a theorem obligation, not a witness search. Failure for any roster is a
class-independent control-definition failure because every witness lies in
`G'`; fallback cannot repair it.

## In-domain strict FREE witness

For `H in {G,G'}`, the strictness domain is all registered fields and
geometries in `H`, including uniform `(beta,gamma)=(0,0)`.

Use `g_4^*` above on the uniform field. Then `d_i=dbar=1`, so `q_i,B_i` are
common across cells for every `theta`; every treatment issues
`n^T=(32,30,28,30)`. Choose

```text
theta=(0,0,0,0)
phi=(0,0,4,0)
r=(1/16,0,-1/16,0)
w^F=(4913,4096,3375,4096)/16384
n^F=(36,30,24,30).
```

The residual is strictly inside the clip and no treatment parameter can issue
that command on this input. `STRICT(H)` means this exact witness is in the
domain and `n^F` is outside the set of treatment commands. The same witness
proves command-level strictness for `G` and `G'`; parameter nonuniqueness
elsewhere is irrelevant.

## Exact measure and independent marginal oracle

`RAT-SIMPSON-QUADRATIC-02` computes

```text
m_i=(v_i/6)[f(b_(i-1))+4f((b_(i-1)+b_i)/2)+f(b_i)].
```

The independent antiderivative is

```text
F(x)=(1-beta-gamma)x+(beta+3gamma)x^2-2gamma x^3
m_i^O=F(b_i)-F(b_(i-1)).
```

`MEASURE_OK(H)` universally means `m_i=m_i^O`.

Let `h=1/600`. For `k=0,...,Q-1` define

```text
Delta_i(k)=m_i v_i[1/(v_i+kh)-1/(v_i+(k+1)h)].
```

Each sequence must be positive and strictly decreasing. Generate records
`(Delta_i(k),i,k)`, sort by descending gain, increasing physical cell index,
then increasing `k`, and select the first `Q`. Let `n_i^O` count selected
records for cell `i`.

`ORACLE_GLOBAL(H)` universally means `n^O` is legal,
`U(n^O)<=U(n)` for every legal `n`, and among exact minimizers `n^O` is
lexicographically largest by increasing physical cell index. The index tie rule
selects a canonical command without changing value among exact minimizers.

## Oracle and control predicates

For any legal `n`:

```text
ORACLE_COMMAND_MATCH(n) iff n=n^O
ORACLE_VALUE_MATCH(n) iff U(n)=U(n^O).
```

These are distinct. Define command/value preservation separately for
reassociation and equal mass. Because `A` is finite:

```text
FREE_ORACLE_COMMAND_RECOVERY iff exists theta,phi in A^4: n^F=n^O
FREE_ORACLE_VALUE_RECOVERY iff exists theta,phi in A^4: U(n^F)=U(n^O),
```

with analogous treatment predicates.

`CONTROL_LEGAL(H)` universally requires treatment, FREE, reassociated
treatment/FREE, equal-mass, action-sensitive and oracle commands to be
nonnegative integer vectors summing to `Q` and applied to original cells.

```text
CONTROL_PRESERVATION_OK(H)=
  EMBED(H)
  and EMBED_P(H)
  and STRICT(H)
  and CONTROL_LEGAL(H)
  and CONTROL_ND(H,N) for every registered N.
```

The analytic object establishes no physical-measure necessity. In any future
efficacy cell, reassociation-value preservation, equal-mass-value preservation,
or FREE oracle-value recovery with the same useful value forbids interpreting
that value as necessity of hard measure binding. Command recovery is stronger
descriptively but unnecessary for that no-necessity conclusion.

## Decision-preserving reporting

All normative values are exact rationals. Reporting may emit outward binary64
`I64(z)=[RD64(z),RU64(z)]`. Exact value and both endpoints are computed
unconditionally. Intervals never choose actions, ties, commands, predicates,
branches or precision. `REPORT_OK` means every interval contains its exact
rational and no displayed strict ordering contradicts the exact ordering. A
reporting failure cannot change the underlying exact action or endpoint.

## Canonical proof machine

The sole normative replay machine is `VQFP-RAT-PROOF-MACHINE-01`.

### Values and accounting

An integer is exact signed. `bitlen(0)=1`; otherwise
`bitlen(z)=floor(log2(abs(z)))+1`. A rational is the unique reduced `(p,q)`
with `q>0`; zero is only `(0,1)`. Every input is normalized.

Each signed add/subtract, multiplication, Euclidean quotient/remainder,
comparison, sign change, and exact division after divisibility is established
increments `PRIMITIVE_BIGINT_OPERATIONS` by one. Euclidean gcd uses
nonnegative operands and counts every remainder. Every integer operand,
result and temporary contributes to `MAX_INTEGER_BITLEN`.

### Rational operations

For `p/q+r/s`:

```text
g=gcd(q,s)
A=p*(s/g)+r*(q/g)
B=(q/g)*s
h=gcd(abs(A),B)
return sign-normalized (A/h,B/h).
```

Subtraction negates `r`. For multiplication:

```text
g1=gcd(abs(p),s)
g2=gcd(abs(r),q)
A=(p/g1)*(r/g2)
B=(q/g2)*(s/g1).
```

Division uses reciprocal after a nonzero check and the same
cross-cancellation. Comparison computes `g=gcd(q,s)` and compares
`p*(s/g)` with `r*(q/g)`. `floor` uses Euclidean division toward negative
infinity. Absolute value, min, max and clipping use exact comparison.

### Evaluation order

- Field polynomials and `F` use descending-power Horner order.
- Simpson evaluates endpoints left-to-right, forms `f_left+4f_mid`, adds
  `f_right`, multiplies by `v_i`, then divides by six.
- `q_i,r_i,B_i` and weights use displayed textual order.
- Cell sums use increasing physical index.
- LR uses stable mergesort with registered key.
- Marginal records are generated in increasing `i,k` and stable-merged under
  the oracle key.
- Endpoint sums use increasing physical index.
- Witness predicates use displayed order.

### Certificate language

A certificate is UTF-8 `VQFP-RAT-CERT-01` records:

```text
DEFINE <canonical expression>
RAT_EQ <lhs> <rhs>
RAT_LT|RAT_LE <lhs> <rhs>
POLY_ID <lhs> <rhs>
BOUND <premise-records> <conclusion>
FINITE_SPLIT <variable> <ascending finite range>
EXCHANGE <source-command> <target-command> <exact delta>
WITNESS <complete exact tuple> <named predicate>
QED <named obligation>.
```

Expressions are prefix trees. Commutative polynomial terms are stored by
lexicographically ordered exponent vectors over frozen variable order
`N,k_1,...,k_N,beta,gamma,theta_0,...,theta_3,phi_0,...,phi_3,i,k`.
`POLY_ID` expands to sparse coefficient maps and compares reduced
coefficients. `BOUND` requires every interval step to follow from checked exact
inequalities. `EXCHANGE` supplies exact endpoint difference. `WITNESS` is
replayed and cannot assert an uncomputed value. The checker performs no search
and accepts no unstated lemma, floating value, external solver result,
probabilistic assertion or sampled extrapolation. Rejection stops at the first
bad record.

`CERTIFICATE_BYTES` is exact UTF-8 byte count. Metrics start at zero for each
class attempt.

## Three disjoint outcomes per class

For `H in {G,G'}`, exactly one completed outcome is allowed.

`CERTIFIED(H)` requires accepted `QED` records for:

- `GEOMETRY_NONEMPTY_AND_CONDITIONED`;
- `MEASURE_OK(H)`;
- `UNSATURATED_ENDPOINT`;
- `EMBED(H)` and `EMBED_P(H)`;
- `STRICT(H)`;
- `CONTROL_LEGAL(H)`;
- `CONTROL_ND(H,N)` for every roster;
- action sensitivity on every frozen witness;
- `ORACLE_GLOBAL(H)`;
- `REPORT_OK`; and
- `RESOURCE_REPLAY_VALID`.

`SCIENTIFIC_COUNTEREXAMPLE(H,predicate,witness)` requires a complete exact
tuple, proof it lies in the class and registered domain, replayed failure of
one named universal or fixed-witness predicate, and an accepted `WITNESS`
record identifying the first failed relation.

A checker rejection, missing proof, unsupported lemma, malformed certificate,
timeout, memory exhaustion, bit-width excess, operation-count excess,
certificate-size excess or researcher-hour exhaustion is never a scientific
counterexample. With no accepted counterexample, such an outcome is
`NONCERTIFIED_WITHIN_BOUND(H,reason)` and states no mathematical failure.

## Exact G-to-G' routing

Attempt `G` first.

1. `CERTIFIED(G)` returns `RETAIN_G_UNRESTRICTED`; do not attempt `G'`.
2. For `SCIENTIFIC_COUNTEREXAMPLE(G)`:
   - if the failed predicate is class-independent—unsaturated endpoint,
     phi-zero containment algebra, strict witness, frozen control witness,
     action law, oracle definition, report law or proof-machine semantics—
     return `DELETE_ANALYTIC_CONTAINMENT_OBJECT` without `G'`;
   - if the witness also lies in `G'`, delete without `G'`;
   - otherwise `G'` may be attempted once, but the `G` counterexample gives no
     positive `G'` evidence.
3. `NONCERTIFIED_WITHIN_BOUND(G)` permits one `G'` attempt because the narrower
   pre-frozen class may admit a smaller certificate; it gives no positive or
   negative `G'` evidence.

For the sole `G'` attempt:

- `CERTIFIED(G')` returns `RETAIN_G_PRIME_ONLY`;
- `SCIENTIFIC_COUNTEREXAMPLE(G')` returns delete;
- `NONCERTIFIED_WITHIN_BOUND(G')` returns delete with reason
  `BOUNDED_ROUTE_NONCERTIFIED`, not a claim that `G'` is false.

No later precision, resource, class, `Q`, field, comparator, control or proof
machine modification belongs to this object.

## Non-replenishable resources

```text
G_researcher_hours=32
G_prime_additional_researcher_hours=16
total_researcher_hours=48
total_CPU_core_hours=12
total_wall_hours=6
peak_RSS_GiB=4
scratch_GiB=1
durable_certificate_MiB=256
MAX_INTEGER_BITLEN=4096
PRIMITIVE_BIGINT_OPERATIONS=100000000
CERTIFICATE_BYTES=268435456
GPU=none
third_geometry_class=forbidden
precision_escalation=forbidden
sampled_fixture_rate_extrapolation=forbidden
out_of_band_partial_value_use=forbidden.
```

All proof-authoring calculations, counterexample search, generation and replay
belong to these totals. `G` may consume at most 32 researcher-hours; `G'` gets
at most 16 additional hours only if reached. Compute, memory and storage totals
are shared and not replenished. Exceeding any proof-machine cap produces
bounded noncertification, not divergence or a scientific counterexample. A
later stage must report all resource and proof metrics plus accepted
obligations and first rejection/exhaustion cause.

## UAV bridge and nontransfer

The 1-D task represents UAVs assigned to ordered ridgeline or linear-
infrastructure patrol stations. Voronoi length is patrol-footprint measure;
`f` is hazard/sensing demand; `m_i` is workload; `n_i/600` is duty; the team
shares one fixed sensing/energy budget as `N` changes. The hypothesis is one
roster-independent allocation rule without per-roster tuning.

This omits 2-D Voronoi shape and integration, travel and turning, collision
avoidance, shape-dependent energy, communication, moving/reassigned
footprints, noisy sensing, in-episode membership changes, aircraft dynamics and
safety. Any later UAV claim requires a separate 2-D simulator object with
realistic travel/energy and a held-out roster or membership change. Failure to
transfer Simpson containment to polygons is a bridge limitation, not evidence
against this 1-D object.

## Claim ceiling, alternative and stop law

Maximum positive claim:

> For every input in the retained frozen finite class, the registered rational
> Voronoi measure, treatment/FREE command laws, controls and exact marginal
> oracle are mathematically total and decision-preserving under
> `VQFP-RAT-PROOF-MACHINE-01`; treatment is universally embedded in a
> command-strict FREE class; and the complete certificate replayed within the
> frozen resource boundary.

`RETAIN_G_PRIME_ONLY` restricts that to `G'`. Bounded noncertification supports
only failure to certify inside the cap. A scientific counterexample supports
only its failed named predicate and class membership.

No branch establishes learned task improvement, held-out-`N` robustness,
physical-measure necessity, optimizer/training value, r05 validity, arbitrary
geometry, in-episode roster change, 2-D/UAV performance, flight, safety or
deployment.

The strongest alternative is generic separable diminishing-return allocation:
equal mass, flexible FREE or the exact marginal optimizer may achieve the same
value without hard-measure necessity. Clipping and the finite 120-quantum
lattice may collapse distinct parameters or weights into identical commands.

Stop now for same-conversation Pro reclosure. No theorem or counterexample work
begins before `CLOSED`, same-direction EM intake and a separate Portfolio
decision. Another `REVISION_REQUIRED` permits only a complete new replacement,
never a patch. A delete outcome ends this exact object. A revisit needs a new
science object and Pro closure; extra compute, a third class, approximate
solver or silent cap increase cannot reopen it. R05 remains unchanged and
no-current.

This composite authorizes no provider operation, theorem execution, CM,
source/build/test/runtime action, identity, coordinate, model, checkpoint,
lease, compute, empirical activity, Git, allocation change or UAV claim.

END COMPLETE REPLACEMENT COMPOSITE

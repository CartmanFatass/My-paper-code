# VQFP-FERL analytic-containment r03 G-first paper theorem return — 2026-08-23

```text
document_kind=direction_paper_theorem_candidate_return
owner=direction:voronoi_quadrature_field_policy
assignment_id=VQFP-FERL-ANALYTIC-CONTAINMENT-R03-G-FIRST-PAPER-THEOREM-COUNTEREXAMPLE-R01
object=VQFP-FERL-ANALYTIC-CONTAINMENT-COST-COLLAPSE-R01
exact_revision=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-03
decision_marker=VQFP_ANALYTIC_R03_G_FIRST_PAPER_THEOREM_RETURN_PROOF_CANDIDATE_20260823
return_class=PROOF_CANDIDATE
candidate_class=G
candidate_obligations=O01|O02|O03|O04|O05|O06|O07|O08|O09|O10|O11|O12|O13|O14
work_stop_reason=FIRST_COMPLETE_PROOF_CANDIDATE
within_authorized_researcher_hour_boundary=true
g_prime_work_performed=false
provider_result_validation_performed=false
same_direction_em_result_intake_performed=false
completed_scientific_branch=NONE
construction=NONE
compute=NONE
```

## Return first

`PROOF_CANDIDATE` for all frozen `G`.

The finite proof below covers obligations `O01` through `O14` for every
registered roster, every geometry in `G`, every registered field and every
registered policy parameter required by exact revision 03. This is the first
complete candidate reached inside the authorized paper-only envelope, so the
`G` work stops here.

This return is not `PROVED(G)` and creates no terminal scientific branch. The
exact proof and exact r03 revision still require a distinct result-validation
turn in the existing VQFP ChatGPT External Pro conversation and subsequent
same-direction EM intake. `G'` was not attempted.

## Frozen setting and notation

Let `N` be one of `4,6,8,12`, let `D_N=384N`, and let
`0<x_1<...<x_N<1` be a geometry in `G_N`. Thus every site is rational,
`b_0=0`, `b_N=1`, `b_i=(x_i+x_(i+1))/2`, and
`v_i=b_i-b_(i-1)` satisfies

```text
1/(3N) <= v_i <= 5/(3N)
max_i(v_i)-min_i(v_i) >= 1/(64N).
```

For registered `beta` and `gamma`, set

```text
f(x)=1+beta(2x-1)+gamma(6x(1-x)-1),
m_i=integral over C_i of f,
d_i=m_i/v_i,
Q=120,
h=1/600,
c_i(k)=m_i v_i/(v_i+kh).
```

Then `U(n)=sum_i c_i(n_i)` for every legal integer allocation `n`.
The one-quantum decrease is

```text
Delta_i(k)=c_i(k)-c_i(k+1)
          =m_i v_i h/[(v_i+kh)(v_i+(k+1)h)].                 (1)
```

All equalities and inequalities below are exact rational statements.

## O01 — geometry nonemptiness and conditioning

The bounds defining `G_N` directly give positive cells and the registered
conditioning interval. Finiteness follows because every `x_i=k_i/D_N` lies
strictly between zero and one, so only finitely many ordered integer tuples
`(k_1,...,k_N)` are possible.

Nonemptiness is witnessed for every registered `N` by

```text
x_i^*=(2i-1)/(2N)                 for i != 2,
x_2^*=3/(2N)+1/(8N)=13/(8N).
```

Indeed, `D_N x_i^*` is an integer: it is `192(2i-1)` for `i!=2` and
`624` for `i=2`. The successive gaps are `9/(8N)`, `7/(8N)`, and
`1/N` thereafter. Its cell lengths are

```text
v_1^*=17/(16N), v_2^*=1/N, v_3^*=15/(16N),
v_i^*=1/N for i>=4.
```

They satisfy the `G_N` bounds, and their spread is
`1/(8N)>1/(64N)`. Hence every `G_N` is finite, nonempty and
nondegenerate.

## O02 — conditional G-prime nesting

For this `H=G` proof, O02's `H=G'` condition is not activated. Nevertheless,
the frozen nesting is exact: membership in `G'_N` already requires membership
in `G_N`, and a multiple of `1/(96N)` is a multiple of `1/(384N)` because
`1/(96N)=4/(384N)`. Thus `G'_N` is a subset of `G_N` for every registered
roster. The fixed witness above also lies in `G'_N`: its sites are multiples
of `1/(96N)`, its gaps lie between `3/(4N)` and `5/(4N)`, and its cells lie
between `2/(3N)` and `4/(3N)`.

## O03 — registered-field positivity and unit mass

On `[0,1]`, `2x-1` lies in `[-1,1]` and
`6x(1-x)-1` lies in `[-1,1/2]`. Since
`|beta|<=1/4` and `0<=gamma<=1/4`,

```text
f(x) >= 1-1/4-1/4 = 1/2 > 0.
```

Furthermore,

```text
integral_0^1 (2x-1) dx = 0,
integral_0^1 (6x(1-x)-1) dx = 3-2-1 = 0,
```

so every registered field has integral one. Consequently every `m_i` and
`d_i` is positive.

## O04 — exact measure

Write an arbitrary interval as `[a,b]`, with `v=b-a` and midpoint
`s=(a+b)/2`. Simpson's expression

```text
v[f(a)+4f(s)+f(b)]/6
```

equals the exact integral separately for the basis polynomials `1`, `x`, and
`x^2`: the three values are respectively

```text
v,
v(a+b)/2,
v(a^2+ab+b^2)/3.
```

The registered `f` is quadratic, so linearity proves exactness on every cell.
Expanding it gives

```text
f(x)=(1-beta-gamma)+(2beta+6gamma)x-6gamma x^2,
```

whose antiderivative is exactly

```text
F(x)=(1-beta-gamma)x+(beta+3gamma)x^2-2gamma x^3.
```

Therefore the Simpson value equals `F(b_i)-F(b_(i-1))=m_i^O` for every
registered input: `MEASURE_OK(G)` holds.

## O05 — unsaturation and strictly diminishing marginals

For every finite `k`, positivity of `m_i`, `v_i`, and `h` makes `c_i(k)>0`.
Thus every legal allocation leaves strictly positive unserved mass. Equation
(1) gives `Delta_i(k)>0`. Its denominator strictly increases from `k` to
`k+1`, while its numerator is fixed and positive, so

```text
Delta_i(k+1) < Delta_i(k)
```

for every `k=0,...,Q-2`. Every additional quantum therefore has positive,
strictly diminishing benefit, with no saturation.

## O06 — LR totality, legality and conservation

Let `w` be any positive rational weight vector, `W=sum_i w_i`,
`y_i=Qw_i/W`, `z_i=floor(y_i)`, and `rho_i=y_i-z_i`. Then

```text
sum_i y_i=Q,
R=Q-sum_i z_i=sum_i rho_i.
```

Hence `R` is an integer with `0<=R<N`, because every remainder lies in
`[0,1)`. Strictly ordered cell boundaries make the secondary left-boundary
key unique, so the descending-remainder order is total and deterministic.
Adding one to exactly the first `R` floors yields nonnegative integers and

```text
sum_i LR(w)_i=sum_i z_i+R=Q.
```

Thus LR is total, legal and conserving for every positive rational input.

## O07 — intact universal containment

For `phi=0`, the unclipped residual is exactly zero in every cell, so clipping
returns `r_i=0`. Therefore

```text
w_i^F=v_i B_i(1+0)^2=v_i B_i=w_i^T
```

for every `N`, every geometry in `G_N`, every registered field and every
`theta` in `A^4`. The exact weights, total, quotas, remainders, LR tie keys,
integer commands and physical commands coincide. Hence `EMBED(G)` holds.

## O08 — reassociation semantics and reassociated containment

The heterogeneity bound makes the maximum and minimum cell lengths different.
The smallest-index tie rules therefore define distinct, unique `i_max` and
`i_min`, and `P_g` is a deterministic transposition. Each
`lambda_i=v_(P_g(i))` is a positive rational length. By definition no site,
cell, mass, density, physical endpoint length, command coordinate or LR tie key
is moved; only the policy length supplied to record `i` is reassociated.

At `phi=0`, `r_i^P=0`, so

```text
w_i^(F,P)=lambda_i B_i=w_i^(T,P).
```

The reassociated weights, quotas, remainders and commands are therefore
identical for treatment and FREE on every input. The commands remain applied
to the original cells. Thus the reassociation is total with the frozen
semantics and `EMBED_P(G)` holds.

## O09 — action-sensitive-pair totality

Since each registered `N` divides 120, `q=Q/N` is one of
`30,20,15,10`; hence equal mass is a legal integer allocation. Every ordered
pair `d!=r` gives a legal vector `n^(d->r)` because `q>=10`. The finite
nonempty set of exact rational `eta_(d,r)` values, followed by the exact donor
and receiver tie keys, has a unique first pair. Thus `n^AS` is total and legal.

In fact `AS_MAG` is positive on every registered input. From (1),

```text
delta_(d,r)=Delta_d(q-1)-Delta_r(q).                         (2)
```

If all these changes were zero, then for every distinct `d,r`,
`Delta_d(q-1)=Delta_r(q)`. Because `N>=4`, choose a third index to connect
each cell to itself through two distinct-index equalities. This would imply
`Delta_i(q-1)=Delta_i(q)` for every `i`, contradicting the strict decrease
proved in O05. At least one `eta_(d,r)` is therefore positive, so the selected
maximum has `AS_MAG>0`.

## O10 — every fixed-roster control witness

Use the fixed geometry from O01, field `beta=-1/4`, `gamma=0`, and
`theta=0`. Then `B_i=1`, treatment weights are `v_i`, and reassociation swaps
only cells 1 and 3. Put `q=120/N` and let `t=2` for `N=4`, otherwise `t=1`.
Exact LR arithmetic is:

| N | q | t | `Qv_1` | `Qv_3` | `(n_1^T,n_3^T)` | `(n_1^(T,P),n_3^(T,P))` |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 30 | 2 | `255/8` | `225/8` | `(32,28)` | `(28,32)` |
| 6 | 20 | 1 | `85/4` | `75/4` | `(21,19)` | `(19,21)` |
| 8 | 15 | 1 | `255/16` | `225/16` | `(16,14)` | `(14,16)` |
| 12 | 10 | 1 | `85/8` | `75/8` | `(11,9)` | `(9,11)` |

All other coordinates equal `q`. These are exactly the registered treatment
and reassociated commands, and each differs from the other and from equal mass.

It remains to prove the strict endpoint ordering. On this field,
`f(x)=5/4-x/2`. The average densities in cells 1 and 3 are

```text
d_1=5/4-17/(64N),
d_3=5/4-81/(64N),
d_1-d_3=1/N>0.                                             (3)
```

Let `s_i=600v_i`. Then `s_1=1275/(2N)`, `s_3=1125/(2N)`, and
equation (1) becomes

```text
Delta_i(k)=h d_i s_i^2/[(s_i+k)(s_i+k+1)].                  (4)
```

The smallest relevant cell-1 marginal is `Delta_1(q+t-1)` and the largest
relevant cell-3 marginal is `Delta_3(q-t)`. After cancelling the common
factor `75^2`, the length-and-denominator part of their ratio exceeds one
exactly when

```text
E_N = 289(1365-2Nt)(1365-2N(t-1))
      -225(1515+2N(t-1))(1515+2Nt) > 0.                    (5)
```

The four exact integer values are:

| N | t | `E_N` |
|---:|---:|---:|
| 4 | 2 | `4,405,952` |
| 6 | 1 | `13,222,080` |
| 8 | 1 | `10,280,640` |
| 12 | 1 | `4,397,760` |

Thus (5), together with (3), proves

```text
Delta_1(q+t-1) > Delta_3(q-t).                             (6)
```

Strict decrease makes every cell-1 marginal used by either control comparison
larger than every corresponding cell-3 marginal. Consequently,

```text
U(n^EQ)-U(n^T)
 = sum_{k=q}^{q+t-1} Delta_1(k)
   -sum_{k=q-t}^{q-1} Delta_3(k) > 0,

U(n^(T,P))-U(n^EQ)
 = sum_{k=q-t}^{q-1} Delta_1(k)
   -sum_{k=q}^{q+t-1} Delta_3(k) > 0.
```

Therefore `U(n^T)<U(n^EQ)<U(n^(T,P))` for every registered roster.
O09 already gives `AS_MAG>0`. The fixed witness belongs to both `G` and
`G'`, so every conjunct of `CONTROL_ND(G,N)` holds for all registered `N`.

## O11 — strict FREE witness

Take the `N=4` fixed geometry and the uniform registered field. Then
`d_i=dbar=1`, so for every treatment `theta`, `q_i` and `B_i` are common
across cells. Multiplying all weights by this common positive factor does not
change LR. Hence every treatment issues

```text
n^T=(32,30,28,30).
```

For `theta=(0,0,0,0)` and `phi=(0,0,4,0)`, which belong to the frozen
lattice, the residual is

```text
r=(1/16,0,-1/16,0),
```

strictly inside the clipping interval. The FREE weights are

```text
w^F=(4913,4096,3375,4096)/16384,
sum numerators=16480.
```

Their quotas have floors `(35,29,24,29)` and respective remainders

```text
12760/16480, 13600/16480, 9480/16480, 13600/16480.
```

Thus `R=3`; the exact remainder and left-boundary order awards quanta to
cells 2, 4, and 1. Therefore

```text
n^F=(36,30,24,30).
```

This differs from the sole treatment command on that input, so it lies outside
the treatment command set. The witness is in `G`, proving `STRICT(G)`.

## O12 — universal control legality

For all frozen inputs and parameters, `B_i=1+q_i^2>0`. Clipping gives
`-1/2<=r_i,r_i^P<=1/2`, so `(1+r_i)^2` and `(1+r_i^P)^2` are positive.
All `v_i` and all reassociated `lambda_i` are positive. Treatment, FREE, and
both reassociated weight vectors are therefore positive rational vectors; O06
makes every associated LR command legal.

Equal mass and the action-sensitive command are legal by O09. The oracle
command is legal by O13 below. Every command coordinate is applied to its
original physical cell by the frozen definitions. Together with O07, O08,
O10, and O11, this proves `CONTROL_LEGAL(G)` and
`CONTROL_PRESERVATION_OK(G)`.

## O13 — global marginal oracle and canonical tie law

For a legal allocation `n`, telescoping (1) gives

```text
c_i(n_i)=c_i(0)-sum_{k=0}^{n_i-1} Delta_i(k).               (7)
```

Thus minimizing `U` over `sum_i n_i=Q` is equivalent to maximizing a sum of
`Q` marginal records, subject to taking a prefix from each cell. By O05, each
cell's marginal sequence is strictly decreasing. Therefore, whenever a record
`(Delta_i(k),i,k)` belongs to the globally first `Q`, every earlier record
from that cell also belongs. The oracle's selected records consequently form
prefixes and define a legal vector `n^O` summing to `Q`.

Every legal `n` selects exactly the `Q` prefix records appearing in (7). The
sum of the globally largest `Q` record values is at least the sum of any other
`Q` records. Equation (7) therefore gives

```text
U(n^O)<=U(n)
```

for every legal `n`.

For the tie law, any alternative maximizer can differ from the canonical set
only by exchanging records tied at the cutoff value: replacing a strictly
larger selected record by a smaller record would strictly decrease the sum.
Strict decrease within each cell means at most one cutoff-tied record occurs
per cell. The oracle selects such tied records by increasing physical cell
index. At the smallest cell index where an alternative minimizer differs, the
oracle includes the tied record and the alternative does not; hence the
oracle's count is larger at that first differing coordinate. Therefore `n^O`
is lexicographically largest by increasing physical cell index among exact
minimizers. This proves `ORACLE_GLOBAL(G)`.

## O14 — exact decision-law consistency

Every site, boundary and cell length is rational. Registered field and policy
coefficients are rational. O04 makes every mass rational; positive division,
squaring, clipping at rational bounds, summation, flooring and LR preserve
exact rational or integer values. The endpoint, marginal records, control
comparisons and oracle comparisons are therefore exact rationals. Distinct
cell boundaries and registered index rules make every tie deterministic.

For every normative rational `z`, the registered uncertainty enclosure is the
singleton `[z,z]`; exact equality and order decide every predicate and route.
No floating display, serialization, machine trace or approximate comparison
enters this proof. The exact decision and uncertainty law is internally
consistent.

## Candidate conclusion and claim ceiling

The preceding finite argument establishes a complete local proof candidate for
`O01` through `O14` over all frozen `G`. Its maximum claim now is only:

> A same-direction EM-authored finite `G` proof candidate exists for exact
> revision 03 and awaits mandatory same-conversation Pro result validation and
> later same-direction EM intake.

Only if the existing VQFP ChatGPT Pro conversation returns result-validation
`CLOSED` on this exact proof and revision, and the same-direction EM accepts
that response, may the object become `PROVED(G)` and route to
`RETAIN_G_UNRESTRICTED`. The maximum positive claim would then remain exactly:

> For every input in retained frozen finite class `G`, the registered rational
> Voronoi measure, treatment and FREE command laws, controls and exact marginal
> oracle are mathematically total and decision-preserving; treatment is
> universally embedded in a command-strict FREE class; and a finite uniform
> mathematical proof covering obligations `O01` through `O14` has been
> established and scientifically validated.

No claim extends to arbitrary continuous geometry, learned performance,
robustness or held-out-`N` generalization, physical-measure necessity,
optimizer or training value, r05, in-episode roster change, 2-D/UAV
performance, flight, safety or deployment.

The strongest alternative remains generic separable diminishing-return
allocation on the finite 120-quantum simplex. Equal mass, residual FREE
flexibility or the exact marginal optimizer may obtain useful value without
necessity of hard Voronoi association, while clipping and largest-remainder
quantization may collapse distinct rational weights or parameters into the
same physical command.

## Stop and later routing boundary

Stop the authorized paper work at this first complete proof candidate. Do not
attempt `G'`. Do not claim `PROVED(G)` or a completed branch before the exact
later Pro result-validation and EM-intake sequence.

This artifact itself authorizes no provider contact, theorem revision,
checker, source, build, test, runtime, compute, lease, identity, coordinate,
model, checkpoint, panel, empirical result, partial-value disclosure, Git,
deployment or flight action. A result-validation defect returns to the same
VQFP EM for bounded interpretation and does not silently change r03. Only a
validated and accepted `PROVED(G)` ends the G-first route as
`RETAIN_G_UNRESTRICTED`; otherwise the frozen unresolved/counterexample laws
continue under separate Portfolio authority.

```text
observed_fact=The authorized paper-only G-first envelope reached one finite EM-authored proof candidate covering O01-O14 over all frozen G.
local_action_fence=No G-prime work, provider turn, checker, source, runtime, compute, lease, result, partial-value, Git, deployment or flight action was performed or authorized by this return.
scientific_stage_continuation=Return this exact proof candidate to Portfolio for a separate same-conversation VQFP Pro result-validation decision, followed by same-direction EM intake.
root_decision_class=Portfolio result-validation investment/transport decision; no completed scientific branch or operational action.
applies_to=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-03 over frozen G only.
does_not_imply=PROVED_G|RETAIN_G_UNRESTRICTED|PROVED_G_PRIME|counterexample|delete|construction|empirical_support|measure_necessity|r05_resume|UAV_value|lease|compute|Git|deployment|flight
continuation_owner=Dedicated Portfolio Root for the distinct Pro result-validation decision; existing VQFP ChatGPT Pro conversation for validation; same-direction VQFP EM for scientific intake.
```

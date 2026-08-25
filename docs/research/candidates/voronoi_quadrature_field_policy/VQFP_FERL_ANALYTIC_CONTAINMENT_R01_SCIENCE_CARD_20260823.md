# VQFP-FERL analytic-containment and cost-collapse definition — revision 01

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FERL-ANALYTIC-CONTAINMENT-COST-COLLAPSE-R01
revision=VQFP-FERL-ANALYTIC-CONTAINMENT-R01-SCIENCE-20260823-01
host=VQFP-UNSATURATED-VORONOI-FIELD-COVERAGE-1D-v1
stage=prospective_definition_only
scientific_activity_begun=false
construction_authorized=false
empirical_activity_authorized=false
pro_closed=false
supersedes_r05=false
```

## Decision first

This is a distinct bounded analytic decision object. It does not resume,
revise, validate or draw efficacy evidence from VQFP-FERL r05. It replaces an
open-ended all-input special-function/nonconvex-certificate tail with exact
rational geometry, a polynomial field, one primary class `G`, at most one
nested fallback `G'`, and one finite theorem-or-counterexample protocol.

The possible outcomes are `RETAIN_G_UNRESTRICTED`, `RETAIN_G_PRIME_ONLY`, or
`DELETE_ANALYTIC_CONTAINMENT_OBJECT`. No third class, approximate substitute,
fixed-fixture extrapolation or outcome-dependent numeric repair exists.

## Provenance and isolation

Direction-local provenance is limited to
`VQFP_FERL_R05_SCIENCE_CARD_20260821.md` and
`VQFP_FERL_R05_TEST_ONLY_NUMERIC_ANALYTIC_UNCONTAINED_TAIL_EM_INTAKE_20260822.md`.
R05 remains unchanged, Pro-closed, activity-free, empirically unsupported and
no-current. No other direction's result, threshold, comparator, acceptance or
authority is imported.

## Variable-N domain and Voronoi geometry

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
v_i=b_i-b_(i-1)
```

Physical rank is increasing site coordinate. Actor labels may be permuted; no
learned coefficient depends on rank or `N`.

### Primary class G

Let `D_N=384N`. A geometry is in `G_N` exactly when:

- every `x_i=k_i/D_N`;
- `1/(2N) <= x_(i+1)-x_i <= 3/(2N)`;
- `1/(3N) <= v_i <= 5/(3N)`; and
- `max_i(v_i)-min_i(v_i) >= 1/(64N)`.

Set `G=union_N G_N` over the registered rosters. `G` is the quantified input
class, not a fixture sample or approximation to continuous geometry.

### Frozen fallback G'

`G'_N` is the subset of `G_N` additionally satisfying:

- each site is a multiple of `1/(96N)`;
- `3/(4N) <= x_(i+1)-x_i <= 5/(4N)`; and
- `2/(3N) <= v_i <= 4/(3N)`.

The same heterogeneity lower bound remains. `G'=union_N G'_N`. It preserves
every roster, unequal-cell mechanism, field, action, endpoint, comparator and
control; only conditioning and rational-grid granularity change. It is nonempty
for every registered `N`: start from `x_i=(2i-1)/(2N)` and replace only `x_2`
by `x_2+1/(8N)`. No third subclass is permitted.

## Unsaturated fixed-total-effort target

For exact coefficients

```text
beta in {-1/4,0,1/4}
gamma in {0,1/4}
```

define

```text
f_(beta,gamma)(x)=1+beta(2x-1)+gamma(6x(1-x)-1).
```

The primary field register contains every pair except `(0,0)`; the flat pair
is retained only for containment/control witnesses. Every field is at least
`1/2` and integrates to `1`. Define

```text
m_i=integral_(C_i) f_(beta,gamma)(x) dx
d_i=m_i/v_i.
```

Let `Q=120`. A legal allocation is a nonnegative integer vector `n` with
`sum_i n_i=Q`; the physical sensing-duty command is `a_i=n_i/(5Q)=n_i/600`,
so total physical effort is exactly `1/5`. The sole endpoint is

```text
U_UNSERVED(n;g)=sum_i m_i/(1+a_i/v_i)
               =sum_i m_i v_i/(v_i+a_i),
```

with lower better. Every finite legal action leaves positive unserved mass;
each added quantum has positive diminishing benefit. There is no saturation
threshold, future-state projection, tolerance or hidden command map.

## Treatment, strict FREE comparator and command map

All trainable coefficients take values in the exact finite alphabet
`A={j/16:j=-64,...,64}`. Let `dbar=N^-1 sum_i d_i` and

```text
q_i=theta_0+theta_1 d_i+theta_2 dbar+theta_3(d_i-dbar)^2
B_i=1+q_i^2
w_i^T=v_i B_i.
```

The strict learned `FREE` comparator adds

```text
r_i=clip_[-1/2,1/2](
  phi_0+phi_1(d_i-dbar)+phi_2(v_i-1/N)
  +phi_3(d_i-dbar)(v_i-1/N))
w_i^F=v_i B_i(1+r_i)^2.
```

Both use exact largest remainder:

```text
y_i=Q w_i/sum_j w_j
n_i=floor(y_i)
```

followed by one quantum to the largest fractional remainders until the sum is
`Q`; exact ties use increasing left cell boundary.

For every treatment `theta`, FREE with `(theta,phi=0)` gives identical weights,
quotas, remainders, legal actions and physical commands. Containment is literal.

For strictness, at `N=4` take sites `(1/16,3/16,9/16,11/16)`, giving
`v=(1/8,1/4,1/4,3/8)`. On the flat assay field every treatment yields command
`n^T=(15,30,30,45)`. FREE with `theta=0`, `phi_2=4` and other `phi=0` gives
`r=(-1/2,0,0,1/2)`, weights `(1/32,1/4,1/4,27/32)` and
`n^F=(3,22,22,73)`. No treatment parameter produces that flat-field command.

No learning law, schedule, seed or efficacy panel belongs to this object.

## Exact measure, numeric routine and independent oracles

`RAT-SIMPSON-QUADRATIC-01` computes each mass as

```text
m_i=(v_i/6)[f(b_(i-1))+4 f((b_(i-1)+b_i)/2)+f(b_i)].
```

All quantities are reduced exact rationals; Simpson is exact because the
registered fields have degree at most two. The routine then computes densities,
weights, quotas, remainders, actions, commands and `U` exactly. No
transcendental, special function, adaptive precision, tolerance, epsilon or
result-dependent numeric rule exists.

The independent measure oracle `RAT-ANTIDERIVATIVE-01` uses

```text
F_(beta,gamma)(x)=(1-beta-gamma)x+(beta+3gamma)x^2-2gamma x^3
m_i^O=F(b_i)-F(b_(i-1)).
```

It shares no Simpson nodes/weights. Every retained class requires exact
`m_i=m_i^O` on every registered input.

For `k=0,...,Q-1`, define exact marginal benefit

```text
Delta_i(k)=m_i v_i[
  1/(v_i+k/(5Q))-1/(v_i+(k+1)/(5Q))].
```

Each sequence is positive and strictly decreasing. The independent action
oracle chooses the `Q` largest records among `(Delta_i(k),i,k)`; equal gains
favor smaller physical cell index, yielding the lexicographically largest
count vector among exact global minimizers. This defines `n^O` without
exhaustive simplex enumeration.

## Command-preserving controls and fatal alternative

`REASSOCIATED_MEASURE` cyclically replaces `v_i` only in the hard factor and
FREE length port by `v_(1+(i mod N))`, while retaining original `C_i,m_i,d_i`,
endpoint, legal actions, physical service law and issued-command semantics.

`EQUAL_MASS` uses `n_i=Q/N`, exact for every roster and with identical command
format and total effort.

`ACTION_SENSITIVE` starts at equal mass, enumerates every valid one-quantum
transfer `n^(d->r)=n^EQ-e_d+e_r`, and takes the lexicographically first pair
maximizing the exact absolute endpoint change. Sensitivity holds iff that
maximum is nonzero; no tolerance/materiality threshold may manufacture it.

For each retained roster/class, an exact witness must show treatment differs
from reassociation in command and `U`, differs from equal mass in command and
`U`, and has nonzero one-quantum sensitivity. These are nondegeneracy witnesses,
not efficacy.

Any later efficacy object must compare intact treatment, reassociated,
equal-mass, strict FREE and `n^O` under identical legal commands and endpoint.
If reassociation/equal mass preserves value, or oracle-accurate FREE reaches the
same command/value, the evidence supports generic separable allocation
regularization or finite-budget optimization, not necessity of physical-
measure binding.

## Decision-preserving uncertainty law

Normative decisions use exact rationals. Reporting may project rational `z` to
the outward binary64 enclosure `[RD64(z),RU64(z)]`; exact value and enclosure
are computed unconditionally with no adaptive refinement.

- legal-action ordering uses exact quota remainders;
- exact ties use the left-boundary rule;
- commands use integer counts only;
- endpoint/control orderings use exact rational signs;
- equality means rational equality;
- an interval must contain the exact rational and never imply an ordering
  opposite to its exact sign.

Any enclosure failure, measure-oracle mismatch, action/command mismatch or
assay-label mismatch is an explicit counterexample and cannot be repaired by
precision escalation or tolerance.

## Frozen theorem-or-counterexample stage

A later separately authorized stage may attempt exactly one uniform certificate
over `G` and, only if `G` fails, one over the already-frozen `G'`. A positive
result covers the whole quantified class symbolically or with a proof-checkable
certificate. Fixtures may find counterexamples but cannot support extrapolation.

The certificate must establish positive conditioned cells; measure/oracle
equality; bounded exact arithmetic; treatment/FREE legality and exact embedding;
the strictness witness; marginal-oracle correctness/tie law; unsaturation and
action sensitivity; command-preserving controls; exact/enclosure agreement;
and roster-wise control-nondegeneracy witnesses.

An admissible negative output is an exact geometry/field/parameter sequence
showing measure divergence/oracle disagreement, arithmetic or certificate
growth beyond the frozen bound, quota/endpoint order reversal, phi-zero
containment failure, illegal/changed command, zero action sensitivity,
reassociation/equal-mass invariance, or checker failure to certify the uniform
statement.

### Non-replenishable resource boundary

```text
G_researcher_hours=32
G_prime_additional_researcher_hours=16
total_researcher_hours=48
total_CPU_core_hours=12
total_wall_hours=6
peak_RSS_GiB=4
scratch_GiB=1
durable_certificate_MiB=256
largest_permitted_integer_intermediate_bits=4096
proof_checker_primitive_bigint_operations=100000000
GPU=none
third_geometry_class=forbidden
precision_escalation=forbidden
sampled_fixture_rate_extrapolation=forbidden
```

Formalization time, coefficient growth and certificate size remain cost
unknowns. Reaching a cap without a certificate/counterexample establishes only
bounded non-testability for that class, not task failure. Learned-policy
training, host construction and efficacy evaluation are outside this budget.

## Terminal branches

1. `RETAIN_G_UNRESTRICTED` only if the complete uniform certificate covers all
   of frozen `G` within the cap; “unrestricted” never means arbitrary continuous
   geometry.
2. `RETAIN_G_PRIME_ONLY` only if `G` has an exact failure or bounded-
   testability exhaustion whose defect is absent by the pre-frozen `G'`
   restrictions, and `G'` receives its own complete uniform certificate.
3. `DELETE_ANALYTIC_CONTAINMENT_OBJECT` if containment, strictness, legality,
   unsaturation, uncertainty preservation or control identifiability fails; if
   `G'` lacks a certificate within cap; or if generic allocation/equal-mass/
   reassociation invariance removes the question.

No third class, approximate routine, weakened comparator, saturated target,
removed sensitivity, `N`-specific tuning or fixture extrapolation follows.

## Claim ceiling and required same-direction Pro purpose

The maximum possible claim is that the frozen variable-`N`, fixed-total-effort
rational Voronoi object is or is not uniformly mathematically testable on the
retained class; its measure and commands are decision-preserving under the
registered numeric law; and treatment is exactly nested in strict FREE. It
cannot establish task improvement, robustness, held-out-`N` generalization,
physical-measure necessity, r05 validity, UAV performance, flight, safety or
deployment.

Before analytic activity, the complete composite must return to the existing
same-VQFP ChatGPT Pro conversation for `CLOSED` or `REVISION_REQUIRED` on
nondegeneracy/question preservation, exact measure/oracles, decision law,
constructive strict containment, controls, terminal logic, resource boundary
and claim ceiling. A correction creates a complete new revision for the same
conversation.

This card authorizes no provider send, theorem/counterexample work, CM request,
source, build, test, runtime, lease, Git, efficacy activity or r05 resume.

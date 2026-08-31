# DISH block-certificate prevalence R02 prospective freeze

Date: `2026-08-31`

Object: `DISH-BLOCK-CERTIFICATE-PREVALENCE-R02`

Status: `PROSPECTIVE_SCIENCE_FROZEN_NO_RESULT_ACTIVITY`

## Conclusion

Replace the invalid R01 24-block mean/bootstrap authority with an exact finite-sample prevalence
object. Keep the accepted R01 causal fork and TEST-only phased/pathwise oracle as engineering
ancestry. Do not reuse the R01 bootstrap, confidence intervals, precision rule, coupled support
Boolean, or single first-match result label.

R02 asks whether a complete material-value certificate, or a complete within-material-margin
certificate, occurs in a majority of independent algorithmic roots. It does **not** estimate an
expected service effect. Twenty-four roots are sufficient for the prospectively fixed exact
binomial decision and the 80% marginal planning-power target for any one prespecified proposition.
The fixed realized panel remains a mandatory descriptive output, not a second inferential target.

No scientific root, master, checkpoint, coordinate, endpoint, or result was created while making
this decision. Full production remains unavailable. Closing the inference definition removes two
scientific hold labels but leaves ten direct engineering gaps described below.

## Question and non-goals

At the same first application-valid STRUCTURED boundary, checkpoint, Welford state, immutable
pre-CAS cut, and future physical tape:

1. in what fraction of independent algorithmic roots does atomic owner/actuator remap under the
   common transaction shell (`TRANSFER_COPY - RETAIN`) meet the full registered value certificate;
2. in what fraction does promoted shadow-source selection under the same remap
   (`TRANSFER_SHADOW - TRANSFER_COPY`) meet it; and
3. for each axis, in what fraction is the complete root panel strictly inside every registered
   material margin?

`RETAIN` is shell-matched retention: it still consumes the intent, advances the epoch, clears the
registered locks, pays the common transaction cost, and suppresses a later transfer. Therefore the
COPY axis is not a comparison with natural no-transaction retention and must not be named generic
transfer value without the shell qualifier.

R02 does not estimate mean return over roots or events. It does not test natural handover
prevalence, an optimally COPY-trained policy, unique information, training advantage, arbitrary
`k`, host, route, or `N`, safety, deployment, or flight.

## Decision table

| Candidate | Finite-sample validity | Work | Maximum claim | Disposition |
| --- | --- | --- | --- | --- |
| Realized 24-root fixed panel | Exact census of that panel; no sampling coverage | 24 training jobs; 6,912 natural rows | Exact contrasts and margin crossings for the realized panel only | Retain as mandatory descriptive output, not primary inference |
| Bounded continuous-mean root law | Legal only after an explicit independent-root law and simultaneous finite-sample bounds | A two-sided Hoeffding design needs 8,198 roots for just one `[-1,1]` mean at half-width `0.03`; applying it to the 144 direct axis/cell/endpoint means needs up to 27,708 roots at the registered margins | Expected root-level effect under the algorithmic root law | Reject for this cycle: it expands the present training work by hundreds of times before other production costs |
| Block-certificate prevalence R02 | Exact binomial under the independent identical-root law below; four-test FWER `<=0.0453116894` | 24 training jobs; the same complete 6,912-row factorial | Majority prevalence of a strict full-root certificate under uniform algorithmic roots | **Adopt** |

The Hoeffding counts are method-specific conservative design counts, not a claim that no tighter
assumption-dependent method exists. No currently cited evidence supplies the variance, tail law, or
natural block population needed to justify such assumptions.

## Independent identical-root population law

Before any model or coordinate exists, the runner samples and stores create-only

```text
U_b independently and uniformly from {0,1}^256, b=0,...,23.
```

Equal byte strings are legal independent draws and are retained. There is no caller seed, root
selection, root replacement, or one-master derivation of the 24 roots.

Every root executes one identical deterministic local map `F(U_b)`. The local RNG address contains
the frozen purpose, split, package, schedule, speed, slot, lane, cycle, tick, message, field, and
draw coordinates, but **not** the global storage index `b`. The index orders artifacts only. This
canonical-local-address requirement is what makes the four binary outcomes identically distributed;
independent roots combined with different root-indexed maps would not establish the declared
binomial target.

The three fork branches share one branch-independent future stochastic tape and the same counter
frontier. Physical/exogenous noise, packet/radio/camera draws, evaluation stochasticity, and common
policy-sampling uniforms may not include RETAIN/COPY/SHADOW in their RNG address; a changed branch
may change whether or how a shared draw is consumed, but cannot select a different draw. A branch
label may appear in transaction/output metadata or in a stochastic mechanism that is itself an
explicitly declared treatment component. R02 declares no such branch-specific stochastic mechanism,
so its scientific path has no branch-indexed RNG draw. This is stronger than merely giving the
branches the same root bytes.

Within each root, one STRUCTURED checkpoint is trained for 1,024 updates under the already frozen
training work. Its evaluation is a census of

```text
2 packages x 3 schedules x 3 speeds x 16 slots = 288 natural rows.
```

The 288 rows are dependent components of one root certificate, never inferential units. Across all
roots the inventory remains 24 training jobs and 6,912 natural rows. A scientifically valid root
with failed competence, opportunity, or axis conditions is retained and receives certificate
indicators zero.

The complete 24-root panel is sealed atomically before training or evaluation. Once that create-only
panel exists, any later technically incomplete attempt is quarantined, but an outcome-blind repaired
execution must start from the beginning with the **same 24 root bytes**. It may not redraw the panel,
replace one root, reuse a partial checkpoint, or inspect a quarantined endpoint before the repaired
run. Reusing the prospectively sealed sample is not outcome salvage; it prevents the estimand from
silently becoming `U conditioned on technical completion`. A fresh panel may be created only when
the atomic 24-root panel itself was never successfully sealed, before any scientific work or outcome.

## Causal branches and endpoints

Use the accepted immutable cut and transaction meanings:

```text
R = RETAIN
C = TRANSFER_COPY
S = TRANSFER_SHADOW
```

Entity identity never changes. COPY changes owner/actuator and promotes the incumbent active
state. SHADOW performs the identical remap and transaction but promotes the pre-warmed standby
state. Every branch consumes the same trigger, uses the same future tape, runs exactly 100 primitive
ticks, and receives zero optimizer updates.

For root `b` and cell `c=(package,schedule,speed)`, let `I_bc` be the common pre-treatment set of
triggered slots. Apply the frozen reducer to the same set `I_bc` for all three branches and endpoints

```text
j in {MEAN, TAIL, DEFICIT, DELAY}
sign_j = {+1,+1,-1,-1}.
```

Define signed benefits

```text
d[C,b,c,j] = sign_j * (E[C,b,c,j] - E[R,b,c,j])
d[S,b,c,j] = sign_j * (E[S,b,c,j] - E[C,b,c,j])
d[T,b,c,j] = sign_j * (E[S,b,c,j] - E[R,b,c,j])  # total safeguard only
```

The root is the first weighting unit: sample one uniform algorithmic root, then reduce its fixed
slots. This is `root-first`, not a uniform-trigger-event estimand. Also report the event-first
aggregate as a nonauthoritative sensitivity because unequal trigger counts can reverse its sign.

## Axis-validity and nonharm fields

For every root and each of its 18 cells, common validity requires:

```text
protocol and measurement complete
C_PRE >= 0.85
2 <= trigger_count <= 14 out of 16
the common trigger and all three fork rows use the same legal cut and future tape
```

The integer trigger bound is the exact within-root implementation of the registered
`[0.10,0.90]` adaptive-opportunity range.

Axis validity is separate:

- COPY requires a legal RETAIN shell and a legal COPY CAS/remap/promotion on every triggered row.
- SHADOW requires legal and shell-identical COPY and SHADOW remaps with the declared source bytes
  on every triggered row.

The old `epsilon=1e-3` state/action separation rates remain mandatory mediator diagnostics but are
not post-treatment eligibility filters in R02. A legal intervention may produce equal state or
action values; that is a legitimate zero path, not missing data. Conditioning the certificate on a
post-treatment action difference would discard precisely those roots that can support a
within-margin conclusion.

For axis `a`, `H_ab` is true only when all its rows have zero registered hard events, shell/timing/
cost equality, no extra application tick, global minimum separation at least `15m`, and every
registered comparator-denominator energy ratio at most `0.03`. A zero comparator with positive
treatment energy fails; two zero energies record ratio zero. These are exact certificate fields,
not confidence statements.

## Mechanical root-certificate algebra

Use material margins

```text
m = {MEAN:0.03, TAIL:0.05, DEFICIT:0.25s, DELAY:0.5s}
```

and noninferiority margins

```text
n = {MEAN:0.01, TAIL:0.02, DEFICIT:0.25s, DELAY:0.5s}.
```

Retain the frozen float64 endpoint definitions and ascending-slot reduction order. Every margin
comparison uses the stored finite value directly, with no new rounding band or epsilon. Only a
producer-written, preregistered terminal record of type `ALGORITHM_RUNTIME_OR_NONFINITE`, emitted
before measurement/reduction and binding the exact root, cell, branch, and failure stage, may be
converted to the typed finite worst-case endpoint plus registered hard-failure flag. That record is
a scientific `H=false` and certificate zero. A bare NaN/Inf, lost exception, missing measurement,
transport corruption, reducer-originated nonfinite, or nonfinite of unknown provenance makes the
complete assignment `INVALID_OR_INCOMPLETE`; no four-test result is computed.

The typed failure propagates through contrast dependencies without deleting a root:

```text
RETAIN failure   -> COPY-axis indicators zero; S-R total safeguard zero
COPY failure     -> COPY-axis indicators zero; SHADOW-axis indicators zero; total safeguard zero
SHADOW failure   -> SHADOW-axis indicators zero; S-R total safeguard zero
```

An unaffected SHADOW-COPY contrast may remain available after a typed RETAIN failure, but SHADOW
VALUE still fails because its total safeguard is zero. COPY remains available after a typed SHADOW
failure.

For axis `a in {C,S}`, root `b`, endpoint `j`, define the qualifying anchors

```text
Z[a,b,j] = {
  z in {4,6,8} :
    d[a,b,(p,k,z),j] >= m[j] for every package p and schedule k
}.
```

Define

```text
NI[a,b] = all d[a,b,c,j] >= -n[j]
VALID[a,b] = all common and axis-specific validity fields pass
VALUE[a,b] = VALID[a,b] and H[a,b] and NI[a,b]
             and exists one endpoint j with Z[a,b,j] nonempty
WITHIN[a,b] = VALID[a,b] and H[a,b]
              and all -m[j] < d[a,b,c,j] < m[j]
```

The strict open interval in `WITHIN` makes it disjoint from a value or harm boundary. Preserve the
qualifying `(endpoint,anchor)` set; its ordering has no authority.

For the SHADOW value indicator only, also require the total `S-R` safeguard to be noninferior at
every cell/endpoint and to pass its pair-specific nonharm fields. It prevents a material
SHADOW-COPY gain from being called value when SHADOW remains materially worse than RETAIN. It does
not couple the scientific status of the COPY and SHADOW axes.

The four immutable binary observations are

```text
B_CV[b] = 1{VALUE[C,b]}
B_CN[b] = 1{WITHIN[C,b]}
B_SV[b] = 1{VALUE[S,b] and total safeguard}
B_SN[b] = 1{WITHIN[S,b]}.
```

Every other scientifically completed root has the relevant indicator zero. Also retain, without
turning them into extra confirmatory tests, per-axis diagnostics for support failure, protocol
invalidity, material harm (`d<=-m`), hard nonharm failure, mixed signs, exact source equality, and
one-root sensitivity. A preregistered producer terminal record
`ALGORITHM_RUNTIME_OR_NONFINITE`, materialized as the bound typed finite worst-case endpoint and hard
flag with the dependency propagation above, low competence, or missing trigger/support is a
scientific zero/harm or prespecified diagnostic; it is not technical incompleteness and cannot
authorize a redraw. A bare or provenance-unknown nonfinite, missing required endpoint, corrupt
measurement transport, or another failure to implement the assignment invalidates the whole
assignment before inference. The final result is the Cartesian product of the COPY state, SHADOW
state, and replay modifier; no axis may erase another.

## Exact four-test inference law

For `q in {CV,CN,SV,SN}`, let

```text
X_q = sum_{b=0}^{23} B_q[b]
p_q = P_U(B_q(F(U))=1).
H0_q: p_q <= 0.5.
```

The `0.5` boundary is a prospective algorithmic reproducibility criterion—more roots with a full
certificate than without one—not an observed or literature-derived natural frequency.

Freeze four one-sided exact binomial tests at per-test `alpha=0.0125`. Alpha is not recycled when
another axis is contained, invalid, or scientifically retired. Reject only when `X_q>=18`.

At the least-favourable null `p=0.5`,

```text
P(Binomial(24,0.5) >= 18) = 0.011327922344207764
4 * tail                       = 0.045311689376831055.
```

Thus Bonferroni family-wise error is below `0.05` under arbitrary dependence among the four
indicators. At `X=18`, the one-sided `98.75%` Clopper-Pearson lower bound is
`0.503888100451766`. For any one prespecified `q`, at its marginal planning alternative
`p_q=0.8`, power is

```text
P(Binomial(24,0.8) >= 18) = 0.8110710551188801.
```

An exhaustive integer check of `n<=24` shows that 24 is the smallest `n` admitting a rejection
threshold with size at most `0.0125` and marginal power at least `0.80` at `p_q=0.8`; its threshold
is 18. This is not the joint power of several rejections or a Cartesian result branch. In
particular, VALUE and WITHIN are disjoint within an axis, so their prevalences cannot both equal
`0.8`.

`VALUE[a,b]` contains an existential witness whose endpoint and anchor may differ by root. Therefore
`p_CV>0.5` or `p_SV>0.5` means only that a root-specific qualifying `(endpoint,anchor)` exists in a
majority of roots. It does not imply that any fixed endpoint, fixed anchor, or fixed pair has
prevalence above `0.5`. No fixed-witness prevalence is tested in R02, even when the union certificate
passes. Per-root witness sets are reported so this nonimplication remains visible.

Only these positive branches have confirmatory authority:

- `COPY_SHELL_REMAP_VALUE_MAJORITY` when `X_CV>=18`;
- `COPY_SHELL_REMAP_WITHIN_MARGIN_MAJORITY` when `X_CN>=18`;
- `SHADOW_COPY_VALUE_MAJORITY` when `X_SV>=18` and the total safeguard holds by definition;
- `SHADOW_COPY_WITHIN_MARGIN_MAJORITY` when `X_SN>=18`.

All other counts are `NOT_ESTABLISHED` for that proposition. Failure to establish VALUE is not a
within-margin conclusion; failure to establish WITHIN is not value. Do not add a minority test,
early stop, threshold change, root extension, or post-result alpha reallocation.

## Replay modifier and strongest containing null

Replay applies only to SHADOW-COPY. It never absorbs COPY-RETAIN because replay still performs the
owner/actuator remap.

For every triggered row entering an endpoint, replay must consume only the frozen typed causal
ledger and reconstruct the full pre-CAS recurrent tuple, post-CAS native and policy state, Welford
state, counter-address frontier, and first projected action. Exact state mismatch is protocol
invalidity, not evidence that causal history is insufficient. Accepted TEST conformance must also
retain the 100-tick twin/induction check. Direct monotonic timing gives one of:

- `REPLAY_CONTAINED`: exact reconstruction completes within `0.1s` on every triggered row;
- `REPLAY_RESOURCE_LIMITED`: exact reconstruction is valid but at least one row misses `0.1s`;
- `REPLAY_INVALID_OR_INCOMPLETE`: no SHADOW scientific result may be interpreted.

Replay status is reported beside, not instead of, the SHADOW prevalence state. A positive
SHADOW-COPY prevalence result under `REPLAY_CONTAINED` can describe an advantage over the naive
COPY comparator under SHADOW-trained checkpoints, but it establishes neither unique information
nor the necessity of stored shadow state. Under `REPLAY_RESOURCE_LIMITED`, the maximum mechanism
interpretation is fixed-resource precomputation/source compatibility.

## Strongest counterexamples

### Prevalence is not expected return

If 80% of roots barely meet `+0.03` and 20% have effect `-1`, certificate prevalence is `0.8` while
the root mean is negative. No R02 branch may be restated as positive expected return.

### Root-first is not event-first

Take twelve roots with 2/16 triggers and triggered MEAN benefit `+0.30`, and twelve with 14/16
triggers and benefit `-0.05`. Both trigger rates satisfy the registered range. Equal-root averaging
is `+0.125`, while equal-trigger-event averaging is `-0.00625`. R02 avoids this ambiguity by making
the complete per-root certificate, not a pooled event mean, the Bernoulli unit. The event-first
sensitivity remains mandatory and cannot inherit R02 authority.

### Checkpoint/source co-adaptation

All checkpoints are trained under SHADOW promotion. A positive SHADOW-COPY certificate may reflect
compatibility with a learned shadow-specific hidden code or an evaluation-time distribution shift
for COPY, even if the shadow contains no unique environment information. Raising the ceiling needs
a prospectively matched train-time source-exposure object.

## Claim ceiling and forbidden wording

The maximum positive claim is:

> Under the frozen two-UAV host, budget, SHADOW-trained process, fixed factorial, common
> shell-matched transaction, and uniform 256-bit algorithmic-root law, a complete COPY-remap or
> SHADOW-source certificate occurs in more than half of roots under the exact four-test decision.

The COPY wording must retain `shell-matched atomic owner/actuator remap`. The SHADOW wording must
retain `under SHADOW-trained checkpoints` and its replay modifier.

Do not use `expected return`, `mean value`, `natural prevalence`, `generic transfer`, `optimal COPY`,
`unique information`, `necessary shadow`, `training advantage`, `cost effective`, `safe`,
`deployment-ready`, or `flight-ready` for an R02 result.

Do not replace `a root-specific endpoint/anchor witness exists in a majority of roots` with `one
fixed endpoint or anchor works in a majority of roots`. That stronger proposition is not an R02
estimand.

## Result branches and stop law

1. An incomplete implementation is quarantined under the repository-wide rule and carries no
   scientific polarity. If the 24-root panel was already sealed, the repaired from-start execution
   reuses that exact panel without reading the quarantined outcome.
2. Any required stored nonfinite endpoint, missing measurement, transport corruption, or protocol
   mismatch makes the complete assignment `INVALID_OR_INCOMPLETE`; do not execute any of the four
   tests. Repair from the beginning with the same sealed 24 roots, never by deleting a root or
   changing `n`.
3. A preregistered producer `ALGORITHM_RUNTIME_OR_NONFINITE` terminal record is converted to its
   typed finite worst-case endpoint/hard flag and propagated by branch dependency; a valid
   low-competence, low/high-trigger, support, harm, or mixed root is likewise retained as the
   prespecified zero(s), with its diagnostic reason.
4. Interpret the four exact tests only after all 24 roots and every required row, endpoint,
   nonharm field, total safeguard, sensitivity, and replay field are sealed.
5. No outcome-peeking stop, selected checkpoint, root replacement, extra root, altered margin, or
   alternate endpoint/anchor search is permitted.

A valid completed R02 assignment consumes this object. Technical incompleteness does not.

## Engineering handoff fields and remaining blockers

The future result-blind contract must delete or disable:

- `INFERENCE_RESAMPLES=99_999`, bootstrap/master resample addresses, max-t, standard errors,
  zero-SE rules, confidence intervals, and precision half-width fields;
- the one-master/24-index sampling interpretation;
- a single coupled support Boolean and the single first-match branch;
- `GENERIC_TRANSFER_ONLY` and any label that lets replay or one axis erase the other; and
- caller-supplied scientific Booleans.

It must add mechanically derived fields for the 24 independent roots, canonical local address map,
one shared branch-independent future-tape frontier, atomic panel-seal state, repaired-attempt binding
to the same panel, root-first endpoint weights, event-first sensitivity, per-axis validity/nonharm/
contrast matrices, qualifying endpoint-anchor sets, total safeguard, four indicator vectors/counts,
exact constants, Cartesian axis results, and replay modifier.

The ten remaining production gaps are unchanged engineering work:

1. normal-tick and generator path;
2. checkpoint/snapshot bridge and handoff integration;
3. causal vector and role-indexed policy integration;
4. role-indexed live/snapshot/PPO replay integration;
5. source-specific masked per-dimension Welford integration;
6. fresh-root producers and canonical addressed minibatch frontier;
7. uninterrupted/resume checkpoint parity;
8. full typed causal replay and direct deadline observation;
9. shared checkpoint and typed no-trigger data plane; and
10. direct process-tree/filesystem resource preflight.

No full production command may start until CM implements these fields, all result-blind conformance
and cold/resume tests pass, the direct preflight truthfully reaches production mode, and every
result-bearing invocation passes the fresh 4 GiB physical/effective memory admission.

## Inputs, direct observations, and evidence paths

Inputs:

- `AGENTS.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/evidence/2026-08-30-dish-promotion-source-fork-wave2-freeze.md`
- `docs/research/candidates/degraded_incumbent_shadow_handover/evidence/2026-08-31-dish-phased-oracle-inference-hold.md`
- current source-factored contract, reducer, inference code, and focused tests.

Direct observations:

- the old bootstrap counterexample remains exact and is not repaired;
- the current source-factored reducer exposes coupled caller-supplied branch Booleans and contains
  no R02 indicator or exact-binomial implementation;
- the current direct runner remains `PRODUCTION_NOT_READY` and no result run was launched;
- the binomial tail, Bonferroni bound, Clopper-Pearson lower bound, and planning power above were
  recomputed independently from their finite sums/beta inversion;
- a read-only metadata keyword scan of
  `C:/Projects/Inst-sci/papers/MyLib/metadata/papers.json` and
  `C:/Projects/Inst-sci/papers/MyLib/metadata/v2/papers.v2.json` supplied no numeric natural
  handover/root law used here. This is not an exhaustive negative literature claim.

Judgment impact: the inference choice is no longer the scientific blocker. R02 is a prospective,
finite-sample-valid and powered target at the present 24-job scale. Its result path remains blocked
only by the ten direct production implementation and preflight gaps above.

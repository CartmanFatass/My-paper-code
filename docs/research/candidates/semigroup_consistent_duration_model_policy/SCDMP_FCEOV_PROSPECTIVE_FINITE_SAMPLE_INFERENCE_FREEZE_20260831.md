# SCDMP FCEOV prospective finite-sample inference freeze

- Frozen: `2026-08-31`
- Baseline: `742f322b`
- Scientific object: `foundation_conditioned_event_order_value`
- State: `HISTORICAL_FREEZE_EXACT_OBJECT_CONSUMED_INVALID_EVIDENCE`
- Formal result: quarantined as `INVALID_EVIDENCE_RESOURCE_ENVELOPE_UNOBSERVED`; outcome not interpreted
- Portfolio mutation: none; Root retains lifecycle and investment decisions

## Conclusion

Post-freeze disposition: the exact object defined below has been consumed as invalid evidence and
has no rerun. The remaining text preserves the prospective mathematical contract only; it is not an
executable next action. Current validity and no-run hardening are recorded in
`SCDMP_FCEOV_V3_INVALID_EVIDENCE_RESOURCE_AUDIT_20260831.md`.

Replace the historical four-member paired Student-t rule with one fixed-sample,
distribution-free, all-or-none intersection-union test on the three policy-value gaps that are
exactly necessary and sufficient for the frozen claim. Use `562` independent disturbance-tape
blocks, executed as `23` strictly serial full native slices of `24` tapes and `144` cells followed
by one final slice of `10` tapes and `60` cells. Analyze all `3,372` terminal cells once, after the
last slice, with one-sided Bernoulli-KL/Chernoff tests at
component level `alpha=0.05`. No component decision or interval has standalone scientific
authority; the sole positive branch requires all three component tests to pass.

This is a strict finite-sample repair under the registered independent bounded-tape law. It uses no
Normal approximation, Student-t assumption, variance estimate, sign symmetry, action-label
exchangeability, or graph-label randomization. It preserves the exact 2-by-3 panel, endpoint,
foundation, intervention, comparator set and zero-margin strict-dominance question while removing
one scientifically unnecessary condition from the historical four-contrast gate.

The scientific hold is resolved by this note. The current executable remains held until CM binds
this exact contract, demonstrates numerical/conformance tests, and installs the fresh resource
admission described below. Nothing in this note is a result or result polarity.

## Question, population and non-goals

Conditional on one fresh foundation that passed the already frozen disjoint competence gate, ask
whether the graph-matched first-action mapping

```text
RH -> A_RH
HR -> A_HR
```

has strictly greater balanced-graph full-mission utility than every graph-blind fixed or randomized
policy on `{A_RH,A_HR,COMMON}` at the frozen public state and external `k=13`.

One observational unit is one complete disturbance tape. Its three component fair-bit sequences
are addressed only by `(tape,tick,component)`. Within a tape, that same disturbance is shared across
all six graph/action cells, so pairing reduces noise without changing the treatment. Across tapes,
the registered assay law supplies independent blocks. The estimands are conditional on the one
realized immutable foundation and its competence pass; assay tapes are fresh and disjoint from
foundation training and competence.

The scientific sampling model explicitly treats the addressed HMAC generator as an ideal PRF: all
distinct `(domain,tape,tick,component)` assay addresses are mutually independent fair bits, and the
assay domain is independent of foundation training and competence domains. A finite 256-bit key and
domain separation are not themselves an information-theoretic proof of this model. The finite-sample
coverage and power statements are conditional on this ideal-PRF/i.i.d.-tape abstraction; violation
of it invalidates inference rather than changing the observed polarity.

The intervention, event clock and credit path remain:

```text
latent H/R event order -> fixed support assignment -> graph-matched or graph-blind first action
-> forced 13-tick hold -> the same frozen order-erased foundation -> terminal native consequence
```

The sole endpoint remains

```text
U = 1[safe dock] * (1 - dock_tick/364), failure_or_timeout = 0.
```

No training reward, instantaneous load, RATE value, partial mission, slice statistic or diagnostic
can activate a branch. This object does not test the best of all 18 actions, the foundation's
natural first action, learned chronology, duration choice, semigroup composition, arbitrary event
words, another state or `k`, variable membership, transfer, safety, deployment or flight.

## Claim-exact three-gap reduction

Write `B=363/364`. For tape `i`, let `U_i(g,a) in [0,B]` be the complete utility in graph `g` after
forcing action `a`. The matched mapping's tape value is

```text
M_i = 0.5 * (U_i(RH,A_RH) + U_i(HR,A_HR)).
```

Define its gaps against the three graph-blind pure vertices:

```text
G_RH,i     = M_i - 0.5*(U_i(RH,A_RH) + U_i(HR,A_RH))
           = 0.5*d_1m,i

G_HR,i     = M_i - 0.5*(U_i(RH,A_HR) + U_i(HR,A_HR))
           = 0.5*d_0m,i

G_COMMON,i = M_i - 0.5*(U_i(RH,COMMON) + U_i(HR,COMMON))
           = 0.5*(d_0c,i + d_1c,i).
```

Their exact supports and range lengths are

```text
G_RH, G_HR in [-B/2, B/2], range R_RH=R_HR=B
G_COMMON    in [-B, B],     range R_COMMON=2B.
```

Let `mu_j=E[G_j,i | frozen foundation]`. For a graph-blind randomized policy with
weights `pi` on the three pure actions,

```text
E[M - U_pi] = pi_RH*mu_RH + pi_HR*mu_HR + pi_COMMON*mu_COMMON.
```

Therefore the matched mapping beats every graph-blind mixture if and only if

```text
V_A = min(mu_RH, mu_HR, mu_COMMON) > 0.

theta_RH     = mu_RH/R_RH
theta_HR     = mu_HR/R_HR
theta_COMMON = mu_COMMON/R_COMMON
theta        = min(theta_RH,theta_HR,theta_COMMON) > 0.
```

This is the strongest competent same-information null. The historical requirement that `d_0c`
and `d_1c` each be positive is sufficient but not necessary: a graph-blind COMMON policy has one
balanced value, so only their half-sum is claim-relevant. Dropping the two separate COMMON signs in
favor of `G_COMMON` changes no treatment, endpoint, support law or claim ceiling; it removes an
unjustified stronger claim.

## Exact bounded-mean test

For component `j` with range length `R_j`, normalize every block to

```text
X_j,i = 0.5 + G_j,i/R_j in [0,1].
```

Then `mu_j<=0` is equivalent to `E[X_j,i]<=0.5`. With `n=562`, compute the integer-grid tape gaps
from terminal flags and dock ticks first, then use float64 `fsum` only for the registered reduction.
For `xbar_j=mean_i X_j,i`, define binary KL

```text
kl(x||q) = x*log(x/q) + (1-x)*log((1-x)/(1-q)),
```

with continuous endpoint conventions. The conservative one-sided p-value bound is

```text
p_j = 1                                      if xbar_j <= 0.5
p_j = exp(-n * kl(xbar_j || 0.5))           if xbar_j > 0.5.
```

Component `j` passes only when `p_j < 0.05`, equivalently

```text
xbar_j > 0.5
n*kl(xbar_j||0.5) > log(20).
```

Exact boundary contact does not pass. Implement the comparison in log space. Any numerical
overflow, underflow, nonfinite intermediate, support violation, disagreement between the direct
log-statistic and an independently recomputed integer-grid statistic, or ambiguous boundary is
invalid evidence, not a nonpass.

For audit and effect-scale reporting, invert each marginal test at `alpha=0.05`: if
`xbar_j>0`, let `ell_j<xbar_j` solve

```text
n*kl(xbar_j||ell_j)=log(20),
```

and set `ell_j=0` when `xbar_j=0`. Use the bounded-support endpoint conventions. Do not publish the
three marginal limits as simultaneous or standalone confidence statements. Publish only

```text
L_theta = min(ell_RH-0.5,ell_HR-0.5,ell_COMMON-0.5),
```

which is a valid one-sided 95% lower bound for the unit-range joint parameter
`theta=min(mu_RH/R_RH,mu_HR/R_HR,mu_COMMON/R_COMMON)`: if `j*` indexes a smallest true normalized
gap, the event `L_theta>theta` is contained in the event that its marginal lower limit exceeds its
mean. The positive branch `L_theta>0` is equivalent to `V_A>0` and to all three component tests
passing. Raw-unit point estimates remain descriptive; no separate raw component bound is a result.

Hoeffding's Bernoulli-MGF extremal bound gives, for independent `[0,1]` observations under the
component null,

```text
P(xbar_j >= x) <= exp(-n*kl(x||0.5)), x>0.5.
```

It requires bounded independent blocks but neither identical distributions, symmetry nor a
variance model. The registered tapes are identically distributed as well, but that stronger fact
is not needed for coverage.

### All-or-none strong family control

The only scientific hypotheses are

```text
H0 = {mu_RH<=0} union {mu_HR<=0} union {mu_COMMON<=0}
H1 = {mu_RH>0 and mu_HR>0 and mu_COMMON>0}.
```

Publish `TARGET_CANDIDATE_ORDER_VALUE_ESTABLISHED` only if all three component tests pass. Under
every parameter in `H0`, at least one component null is true, and the event that the bundle passes
is contained in the event that this true component is rejected. Hence

```text
p_IUT = max(p_RH,p_HR,p_COMMON)
bundle passes iff p_IUT < 0.05
sup_H0 P(bundle passes) <= 0.05.
```

This all-or-none gatekeeping procedure strongly controls false publication of the three-comparison
family without Bonferroni. It does **not** create three separately publishable 95% claims or three
simultaneous 95% confidence intervals. Component p-value bounds, estimates and pass flags are
retained only to make the atomic conjunction auditable. No component can be quoted as established
unless the complete bundle passes, and even then the supported statement is the single conjunction.

## Why permutation, sign flip and Student-t remain ineligible

Common disturbance tapes provide paired potential outcomes, not randomized treatment labels.
Neither graph nor first action is randomly assigned within a block. A sign-flip test would require
the joint contrast vector to be invariant under `D -> -D`; an action permutation would require
exchangeability of the potential outcomes under action-label swaps. The host, interventions and
frozen law impose neither condition.

An exact counterexample remains decisive at the revised tape count. With probability `255/256`, let
every original contrast equal `+1/364`, and with probability `1/256` let every contrast equal
`-363/364`. Every original contrast then has mean `-27/23296`; all three claim-exact gaps also have
negative means. Nevertheless, all 562 tapes are positive with probability
`(255/256)^562 = 0.11084622278866264...`, while a common block sign-flip statistic on that event
assigns tail probability `2^-562`. Pairing therefore cannot legalize sign randomization, permutation
inference or the historical zero-variance Student-t branch. This is a mathematical coverage
counterexample, not a claim that the native plant realizes this two-point law.

## Zero margin and prospective power

The scientific material margin is exactly `0`. This is not a claim that arbitrarily small effects
are operationally important. It preserves the existing eligibility question: whether the matched
mapping strictly dominates the complete graph-blind simplex. No observed full-mission effect and no
accepted external requirement supplies a nonzero margin; importing the old opportunity-selector
margin or the `.84/.94/.66` instantaneous-load fixture would change the object.

Power is planned separately from the claim margin. Use the scale-free planning alternative

```text
mu_RH     >= R_RH/10     = B/10
mu_HR     >= R_HR/10     = B/10
mu_COMMON >= R_COMMON/10 = B/5.
```

This is a design-resolution statement, not a transferred threshold or a post-result interpretation.
It asks the one-shot gate to have useful worst-case sensitivity when every required pure-policy gap
is at least ten percent of its own full support range. Under this alternative, normalized means are
at least `0.6`. At `n=562`, the component critical normalized mean is the unique

```text
c_562 = 0.5515800657452960
```

satisfying `562*kl(c_562||0.5)=log(20)`. A lower-tail Bernoulli-KL bound gives

```text
P(component nonpass) <= exp(-562*kl(x_fail||0.6))
                     <= 0.06632625085687167

P(all three pass) >= 1 - 3*0.06632625085687167
                  = 0.801021247429385.
```

Here `x_fail=0.5+21045/(726*562)=0.551579365312785` is the largest grid point that does not pass.
At `n=561` the corresponding discrete-grid bound is `0.799048262648854`, so `562` is the smallest integer tape count whose
stated worst-case joint-power lower bound reaches `0.8`. The native ABI accepts the final partial
width, so rounding to `576` would add no scientific or engineering capability. For comparison, the
quadratic Hoeffding radius at `n=562` has normalized threshold `0.5516259841190267` and joint-power
lower bound `0.7838102435623081`; the frozen Bernoulli-KL inversion is materially decision-relevant
here because it reaches the frozen power floor with the exact smallest `n`. Effects below the
planning alternative can still pass, but their power is not promised. A complete nonpass means only
"not established at this frozen resolution," never that one or more population gaps are
nonpositive.

The exact endpoint grid supplies a second branch calculation. Let `S_RH` and `S_HR` be the sums of
the integer `/364` numerators of `d_1m` and `d_0m`, and let `S_COMMON` sum the integer numerators of
`d_0c+d_1c`. At `n=562`, strict KL passage is exactly

```text
S_RH >= 21,046
S_HR >= 21,046
S_COMMON >= 42,091.
```

The preceding integer in every row does not pass. These correspond to minimum observed raw gap
means about `0.05144010793476986`, `0.05144010793476986`, and
`0.10287777169449767`, respectively. The integer and log-space branches must agree.

## Tape, stop, atomicity and fixed-frontier resume law

Freeze exactly:

```text
tape blocks                  562
native slices                 24
full slices                   23 x 24 tapes x 6 cells = 3,312 cells
final slice                    1 x 10 tapes x 6 cells =    60 cells
complete panel cells       3,372
component tests                3
component alpha             0.05
material margin                0
```

The competence gate remains first. A valid competence nonpass stops before any assay tape exists.
After competence passes and the first assay tape is materialized, execute all 24 slices in fixed
tape-index order. Every full slice must contain the same 24 tapes across all six graph/action cells;
the final slice must contain the remaining 10 tapes across the same six cells. Every slice must
terminate completely. No slice statistic, p-value, confidence bound, favorable pattern,
resource observation or partial cell may stop, extend, replace or reorder the panel. Analyze only
after all `3,372` terminal cells are present.

One formal attempt uses one fresh internally generated master, the frozen final checkpoint and the
exact `562` addressed tapes. There is no CLI seed/master, new master after activity begins, tape
replacement, redraw, checkpoint selection, changed tape count, changed threshold, result-aware
extension, or second attempt after a valid result. A valid complete bundle pass establishes only the
frozen conjunction. Every other valid complete bundle is
`TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION` and ends this exact
state/`k`/foundation/candidate-set purchase before an adapter. Missing or duplicate durable cells,
support/RNG drift, foundation mutation, resume divergence or partial scientific publication are
invalid evidence and carry no scientific polarity.

Resource refusal or process interruption is technical rather than scientific. Each slice publishes
one complete raw-cell frontier atomically; completed slices are immutable. A later technical resume
must reload the same master, checkpoint, fixed `562` tape addresses, completed slice frontier and
next slice index. It may continue only after a fresh 4 GiB admission. An interruption before a slice
atomically completes may restart that same slice from its same addresses and immutable foundation;
it may not preserve a subset, replace a tape or advance the frontier. No inference value is computed
or exposed before all slices complete. A technical resume that satisfies these equalities is not a
new scientific retry. Any new master, tape redraw/replacement, completed-slice rewrite, frontier
divergence or result-informed continuation is invalid and cannot be repaired inside this object.

The raw `3,372` cells, the three integer-grid block-gap vectors, point estimates, log statistics,
p-value bounds, `p_IUT`, component flags and single `L_theta` form one atomic complete result. No
component or slice artifact is a scientific result. Publication is create-only and complete-only.

## Revised resource envelope

The exact logical maxima become

```text
episodes/rollouts       5,412
primitive slots     1,969,968
AdamW steps             1,920
checkpoints                  1
forced first actions     3,372
foundation queries     148,164
outer workers                 1
native/Torch threads          1
```

Native ABI maximum width remains `144`; the final slice uses width `60`. Slices are strictly serial
and never overlap in memory. Before the
formal invocation and before any later result-bearing resume/retry/slice, run

```text
python scripts/hmasd_resource_preflight.py admit-memory --out <fresh-receipt>
```

and require both physical and effective available memory to be at least `4 GiB`. Repeat that check
before every resumed invocation and immediately before every internal slice; refusal preserves the
same technical frontier but performs no slice work. Also run the
direction-specific resource assessment with projected peak RSS `1 GiB`, scratch ceiling `64 MiB`,
durable ceiling `64 MiB`, one worker and one thread. A resource pass never overrides a scientific or
engineering defect. Any internal slice seeing a fresh memory refusal terminates the attempt as
no-work at the last complete frontier. It may resume later under the fixed-frontier law above after
a fresh passing receipt; refusal itself is neither invalid evidence nor scientific polarity.

A result-blind TEST_ONLY width-144 observation used one fixed test key, fixture foundation and 24
tapes; all 144 lanes terminated. Its persisted direct panel time was `0.2696522 s`, cold-process wall
was `3.0598895 s`, and peak working set was `233,463,808 B`. A separate fixed-key real single-update
observation executed 12 complete training episodes and 12 AdamW steps in `0.1399864 s` update-only,
`2.882517 s` cold-process wall, with peak RSS `235,454,464 B`. Linear fixed-work projection for 160
updates, 23 width-144 slices, one width-60 slice, competence, one cold start and the registered
counts is `31.7594612 s`.
Freeze the complete-invocation wall ceiling at `300 s`, peak RSS ceiling at `1 GiB`, scratch at
`64 MiB`, and durable output at `64 MiB`. The wall allowance is about `9.45` times that projection and
covers unmeasured checkpoint, restore-equality, atomic JSON and host jitter. It is an engineering
ceiling, not an empirical scientific result.

## Result branches and claim ceiling

1. Any required-stage incompleteness, numerical/RNG/support/resource drift or partial publication:
   `INVALID_EVIDENCE`; no scientific update.
2. Valid foundation competence nonpass: `FOUNDATION_COMPETENCE_NOT_ESTABLISHED`; no assay or order
   value conclusion.
3. Complete valid panel and all three KL tests pass: `TARGET_CANDIDATE_ORDER_VALUE_ESTABLISHED`.
4. Every other complete valid panel: `TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION`.

At most, a positive result states:

> Conditional on one fresh competence-qualified order-erased foundation, at the exact public state,
> external `k=13`, simulator and fair-bit disturbance law, the prospectively fixed graph-matched
> mapping has greater balanced-graph full-mission value than every graph-blind fixed or randomized
> policy on `{A_RH,A_HR,COMMON}`.

It does not separately establish either per-graph COMMON contrast, best-18-action value, the
foundation's natural first action, learned order use, mediation, chronology, duration, semigroup,
arbitrary state/graph/`k`, another foundation, membership, transfer, safety, deployment or flight.

## Inputs, direct observations and limitations

Direct repository facts:

- `DIRECTION.md` and `IMPLEMENTATION_THRESHOLD.md` define the current recast, endpoint, support law,
  2-by-3 interventions, old contrasts and claim ceiling.
- `SCDMP_FCEOV_WAVE2_SCIENTIFIC_INFERENCE_HOLD_20260831.md` supplies the exact Student-t
  counterexample and establishes that no scientific result has run.
- `foundation_conditioned_event_order_value/contracts.py`, `panel.py`, `rng.py`, `analysis.py` and
  `test_fceov_pairing_and_analysis.py` directly expose the current bounded cells, shared-tape
  pairing, address law and held Student-t implementation.
- Fresh non-result resource receipts and fixed-key native telemetry are retained at
  `temp/directions/semigroup_consistent_duration_model_policy/exp/` as
  `wave3-cm-panel-benchmark-resource.json`, `wave3-cm-panel-benchmark.json`,
  `wave3-cm-nonresult-resource.json`, `wave3-cm-single-update-benchmark.json`,
  `wave3-cm-panel-width60-benchmark-resource.json`, and
  `wave3-cm-panel-width60-benchmark.json`. The width-60 observation directly terminated all 60
  lanes, with panel-only wall `0.1474538 s`, cold wall `2.9507569 s`, and peak RSS
  `232,464,384 B`.
- The local `C:/Projects/Inst-sci` text library contained general uses of Hoeffding but no dedicated
  bounded-mean inference source sufficient to choose the repair. Primary-source verification was
  therefore added from Hoeffding's original result and the modern bounded-mean literature below.

Limitations:

- Finite-sample validity is with respect to the registered independent fair-bit tape population;
  implementation conformance of the addressed RNG to that scientific law remains CM's burden.
- The inference is conditional on one realized competent foundation and does not estimate a
  foundation-seed superpopulation.
- The `0.8` power statement is a worst-case lower bound only at the displayed normalized planning
  alternative. It does not promise power for smaller or mixed gaps.
- The `300 s` complete wall is a conservative projection from a real single-update observation,
  width-144 and width-60 native observations, and a competence-width proxy; it is not a direct
  formal full-chain timing.
- A nonpass cannot identify which population gap is nonpositive and cannot support a no-order claim.

## Evidence paths and primary references

- `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_FCEOV_WAVE2_SCIENTIFIC_INFERENCE_HOLD_20260831.md`
- `experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/contracts.py`
- `experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/panel.py`
- `experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/rng.py`
- `experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/analysis.py`
- `tests/experiments/candidates/scdmp_variable_k/test_fceov_pairing_and_analysis.py`
- W. Hoeffding, “Probability Inequalities for Sums of Bounded Random Variables,” *JASA* 58(301),
  1963, Theorem 1 and equations (2.1)--(2.3):
  https://doi.org/10.1080/01621459.1963.10500830
- I. Waudby-Smith and A. Ramdas, “Estimating Means of Bounded Random Variables by Betting,”
  *JRSS B* 86(1), 2024: https://doi.org/10.1093/jrsssb/qkad009. This supports the bounded-mean
  alternatives audit; its betting product is not used in the frozen rule.

## Cheapest next discriminator

There is no next scientific discriminator or formal compute for this exact object. Future work is
limited to the no-run canonical-root, atomic staging, direct raw-byte equality and identity-free
resource-telemetry hardening in
`SCDMP_FCEOV_V3_INVALID_EVIDENCE_RESOURCE_AUDIT_20260831.md`. Unit, fixture, TEST_ONLY native and
result-blind preflight tests may preserve the derivation and prevent recurrence, but they cannot
create a second result opportunity.

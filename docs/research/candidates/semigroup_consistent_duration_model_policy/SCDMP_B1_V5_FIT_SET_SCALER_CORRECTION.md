# SCDMP B1 v5 fit-set scaler correction

```text
direction=semigroup_consistent_duration_model_policy
owner=EM_semigroup_consistent_duration_model_policy
successor_revision=SCDMP-B1-SCIENCE-20260812-05
superseded_revision=SCDMP-B1-SCIENCE-20260812-04_PRO_CLOSED
scientific_activity_started=false
result_inspected=false
science_bearing_change=true
construction_authorized=false
production_authorized=false
chatgpt_external_pro_math_closure=CLOSED_ON_EXACT_V5
em_closure_intake=accepted_without_science_change
```

## Adjudication

The missing standard-deviation convention is science-bearing because it enters
both the optimized endpoint/composition loss and thresholded standardized
mechanism observables. CM was correct to return the ambiguity rather than adopt
an implementation default. V4 cannot remain the construction object.

V5 uses the population standard deviation, exactly `ddof=0`, because the
scaler population is the complete frozen set of optimization-visible fit-target
atoms, not an iid sample used to estimate an unknown superpopulation variance.
Using `ddof=1` would silently apply a Bessel correction to a finite design
population. With `n=10,752`, the two scale conventions differ by the factor
`sqrt(10,752/10,751)`; the numerical difference is small but can change an
objective gradient or a threshold comparison at the boundary and therefore
cannot be left to implementation choice.

No runtime, code, provisional scalar, checkpoint, metric, result or treatment
outcome was inspected or used. This is a prospective definition correction.

## Exact scale populations and API

For each algorithm seed separately, construct four C-contiguous float64 arrays
from `E_2,E_4,E_8` fit-set targets only. Enumerate duration `2,4,8`, episode
`0..47`, true boundary ascending, then slot `1..4`:

- terminal `e_i`;
- terminal `v_i`;
- complete-word cumulative node reward for slot `i`; and
- complete-word cumulative directed-edge reward for edge `i -> i+1`.

Each fit set contains `48*(32+16+8)=2,688` complete endpoint rows, so each
scalar population contains exactly `2,688*4=10,752` atoms. Initial/input states,
composition-bank duplicate views, support probe, audit, scored evaluation,
model predictions, arm outputs and other seeds are excluded. Raw atom pooling
is intentional; there is no per-duration equalization or bankwise variance.

For each population `x`, under NumPy `1.26.3`, execute exactly:

```text
x64     = numpy.asarray(x, dtype=numpy.float64, order='C')
sigma64 = numpy.std(x64, axis=None, dtype=numpy.float64, ddof=0)
scale64 = numpy.maximum(sigma64, numpy.float64(1e-3))
scale32 = numpy.float32(scale64)
```

The denominator is `n`. `numpy.nanstd`, `torch.std`, `ddof=1`,
`correction=1`, online/sample variance, per-bank variance, seed pooling or
arm-specific recomputation is nonconforming. All atoms are finite, so no
missing-value rule exists. The four final float32 constants are shared by the
paired arms, frozen before update-zero materialization and used only as
divisors. No fit-set mean is applied to model inputs or errors.

## Exhaustive affected locations

The four scalers apply to exactly the corresponding standardized residuals in:

1. `L_endpoint`;
2. `L_comp`;
3. update-zero `D_comp_init=sqrt(L_comp)`;
4. untouched train-support composite endpoint/node/edge RMSE;
5. REAL, SHAM and pooled `D_comp_m_*` and `Delta_comp_REAL`;
6. REAL, SHAM and pooled `E_pred_m_*` and `Delta_pred_REAL`; and
7. any reporting-only residual explicitly labeled standardized.

Raw-coordinate and raw-reward reports stay raw. The scaler does not enter the
explicit neural inputs `[e/1.5,v/0.6,q]`, task returns, failures, oracle score or
action, oracle regret, state support, output-variance ratios, reversal effects,
action disagreement, candidate-score sensitivity, `Delta_J`, `Delta_task`,
`Delta_fail`, `Delta_rob`, `Delta_spec`, confidence bounds or resource counts.

## Invariants and claim boundary

V5 changes no named loss/statistic/estimand, loss weight, numeric threshold,
sample/seed count, tape, architecture, optimizer, activity boundary, branch
precedence, parameter count, `1,606,656`-microstep ledger, strongest alternative,
claim ceiling, second-surface activation rule or UAV bridge. It gives exact
numerical meaning to pre-existing standardized objects; no gate is weakened.

V4 remains historically Pro-closed as written but is prospectively superseded.
Only literal `CLOSED` on complete v5 in the existing direction Pro conversation,
followed by this EM's intake, can reopen the CM construction route.

That exact same-conversation `CLOSED` ruling and same-direction intake are now
complete. The correction remains unchanged. This satisfies only the
mathematical/causal prerequisite; Root retains CM relay and production
sequencing, while CM retains technical acceptance.

## Exact Root-to-CM correction

> Supersede the inactive construction target `SCDMP-B1-SCIENCE-20260812-04`
> with complete successor `SCDMP-B1-SCIENCE-20260812-05`. For each seed,
> compute four arm-shared fit scalers from only the `10,752` ordered target atoms
> in `E_2,E_4,E_8` for terminal `e`, terminal `v`, node cumulative reward and
> directed-edge cumulative reward. Use NumPy `1.26.3`
> `numpy.std(x64,axis=None,dtype=numpy.float64,ddof=0)`, apply the float64
> `1e-3` floor, cast once to float32, freeze, and use the corresponding divisor
> at every standardized training/support/audit location named in the v5 card.
> Do not pool seeds, duplicate composition views, reweight banks, use Bessel
> correction, or normalize task-return and non-residual observables. Preserve
> every other v4 definition and the exact ledger. Do not resume construction or
> production until Root relays literal same-conversation Pro `CLOSED` on exact
> v5 plus this EM's intake; return any further science ambiguity unchanged.

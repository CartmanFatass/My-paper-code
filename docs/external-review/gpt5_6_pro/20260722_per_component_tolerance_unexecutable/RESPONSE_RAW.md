## 1. Is a flat absolute per-component tolerance executable here?

**Not as a device- and shape-portable specification over the full allowed parameter range.** A larger fixed `atol` would only postpone the same failure.

The failure is demonstrably pre-existing. At commit `bcdff53`, `mark_component` was one of the ordinary approximate replay fields, and `validate_replay` rejected every approximate field above the single `REPLAY_TOLERANCE`; that tolerance was `1e-6`. The later compositional-joint work did not create this failure.

The component is also genuinely unbounded under the registered model. The mark head has unrestricted linear outputs for (\mu), while

[
\sigma=0.1+0.9,\mathrm{sigmoid}(s),
]

and the transformed-density term includes

[
2\bigl(\log 2-u-\operatorname{softplus}(-2u)\bigr).
]

As (|u|) grows, the transformed log-density magnitude can grow without a registered ceiling.

The precise correction is:

> A fixed absolute tolerance is not mathematically portable when two valid float32 evaluations may differ by one or more ULPs and the ULP size grows with magnitude.

It is not literally “unsatisfiable” for every implementation: bitwise-identical collection and replay have zero error at any finite magnitude. It is unsound as a portability contract across legitimate kernel shapes, reduction orders or devices.

### The ULP claim is only partially verified

The arithmetic identity is correct:

[
1.9073486328125\times10^{-6}=2^{-19}.
]

For binary32 values with magnitude in ([16,32)), the spacing is

[
2^{4-23}=2^{-19},
]

so that number is exactly one ULP in that binade.

However, the committed replay report records only the maximum absolute component difference. It does **not** record the stored value, replayed value, coordinate or ULP distance at the failing component. Therefore the failure message alone does not prove that the component lay in ([16,32)). The same difference could be two ULPs in ([8,16)), four ULPs in ([4,8)), and so forth.

The next replay record should serialize, for each worst component:

```text
stored_value
replayed_value
absolute_error
mixed_bound
float32_ulp_at_max_magnitude
ulp_distance
row / factor coordinate
```

So the “one ULP” diagnosis becomes evidence rather than inference.

## 2. What relative bound should replace it?

Use a **mixed absolute-relative bound for likelihood components**, while keeping the existing absolute bound for ordinary state tensors:

[
|x_{\mathrm{replay}}-x_{\mathrm{stored}}|
\le
a+r\max\bigl(|x_{\mathrm{replay}}|,|x_{\mathrm{stored}}|\bigr).
]

Freeze:

[
a=10^{-6},
]

[
r=8u=8\cdot2^{-24}
=4.76837158203125\times10^{-7}.
]

Why (8u):

* one float32 ULP is between (u|x|) and (2u|x|) within a normal binade;
* (8u|x|) therefore permits approximately four to eight ULPs, depending on position within the binade;
* this gives two independently evaluated paths a small multi-ULP allowance without fitting the bound to the observed one-ULP failure.

At magnitude (16), the bound is approximately:

[
10^{-6}+8u\cdot16
=================

8.62939453125\times10^{-6}.
]

That is still tiny compared with a substantive likelihood-factor defect.

Apply this mixed rule only to actual log-likelihood components:

```text
primitive_component
categorical_component
mark_component
```

Keep `1e-6` absolute-only for:

```text
value
hidden
prefix
event_input
event_new_z
primitive_event_z
```

Keep masks, event actions, support, detach state and support-leak fields exact. The current contract already separates these exact invariants from continuous component fields.

### Add a numerical-significance ceiling

A relative tolerance grows indefinitely with magnitude. Prevent extreme saturation from eventually granting a scientifically meaningful likelihood discrepancy by also requiring:

[
\left|\exp\left(x_{\mathrm{replay}}-x_{\mathrm{stored}}\right)-1\right|
\le10^{-4}
]

for each likelihood component, and the same bound for the final event joint ratio.

This is not fitted to the failed run. It freezes a direct guarantee on the object PPO consumes: a replay-only probability-ratio displacement above (10^{-4}) is numerically invalid even when the component magnitude is enormous.

The component passes only when **both** conditions hold:

```text
abs_error <= 1e-6 + (8 * 2^-24) * max_abs_value
and
abs(expm1(replayed - stored)) <= 1e-4
```

Retain the compositional joint and float64 assembly checks unchanged. They address accumulation and factor assembly; the mixed rule addresses individual factor portability. The current joint implementation already uses float64 reassembly and explicitly recognizes that factor-level coverage belongs to the component and exact support classes.

## 3. Should the likelihood itself be accumulated in float64?

**Float64 likelihood evaluation would not change the causal or scientific meaning, provided it were applied consistently—but it is not the correct primary fix, and it would not eliminate the need for a scale-aware replay rule.**

Three cases must be distinguished.

### Float64 joint summation only

Casting already-computed float32 components to float64 before summing does not address this failure. The failed quantity is an individual transformed-mark component. The implementation already performs float64 reference reassembly for the joint, and that joint check passed.

### Float64 transformed-density evaluation

Computing the Normal term, Jacobian and component log-density in float64 from the sampled float32 (u,\mu,\sigma) would reduce rounding inside that formula. Conceptually it remains the same transformed-normal density, the same event factorization and the same PPO objective.

It would nevertheless change the exact numerical gradients and hence the optimizer trajectory. That is acceptable as a preregistration change before a result or checkpoint exists, but it is not a semantic no-op.

More importantly, it does not remove upstream float32 variation:

* event inputs are float32;
* the linear event and mark heads are float32;
* collection and replay invoke those heads under different batch shapes.

Slight differences in (\mu) or (\sigma) can remain, and saturation can amplify them even when the downstream density arithmetic is double precision. A mixed component tolerance is still required.

### Float64 categorical and primitive probabilities

Moving categorical softmax/log-softmax and primitive probabilities to float64 is broader still. To preserve a single coherent behavior policy, the same float64 probabilities would need to govern both sampling and likelihood scoring. Otherwise actions would be sampled from one numerical distribution and scored under another.

That would remain the same intended softmax policy in scientific terms, but it could change rare sampled actions near CDF boundaries and therefore alter complete training trajectories. It is unnecessary for the observed mark-component failure.

### Ruling

```text
Do not convert the whole training likelihood path to float64 as this correction.
Keep model forward, action sampling and PPO likelihoods float32.
Use float64 for reference assembly/audit.
Replace the flat component atol with the mixed bound above.
```

A later deliberate all-float64 likelihood contract would be scientifically legitimate, but it would be a larger numerical-policy revision, not merely a tolerance repair.

## 4. Would the mixed bound weaken defect detection?

**It does not materially weaken the guarantees replay actually provides, provided the exact checks, the relative bound and the ratio ceiling are all retained. But one presumed guarantee was never present.**

### Guarantees preserved

The following remain exact and are unaffected by the tolerance change:

* categorical and mark factor masks;
* event action support;
* stored factors outside their legal support;
* kind support;
* detach status.

The current implementation explicitly checks support leakage outside categorical and mark masks as exact-zero fields.

At (|x|=16), the proposed allowance is about (8.6\times10^{-6}). Omitting the tanh Jacobian around (u=8) changes a component by roughly (14.6), so that defect remains separated from the tolerance by more than six orders of magnitude. Wrong support or masks fail exact checks rather than numerical ones.

The explicit `expm1` ceiling also ensures that a large component magnitude cannot convert the relative rule into a large PPO-ratio allowance.

### A guarantee that replay never had

A shared incorrect Jacobian implementation is **not** detected by replay.

Collection and replay both call the same `transformed_mark_component_logp` function. If that function is changed incorrectly in a common-mode way, the stored and recomputed components can agree perfectly. Collection uses it when writing the old component likelihood, and replay uses the same function again.

Replay establishes:

> collection and replay implement the same registered factors consistently.

It does not independently establish:

> the shared mathematical density formula is correct.

Preserve that separate guarantee with an independent reference test, for example:

* compute the transformed-normal component in standalone float64 code not calling the production helper;
* compare production output over fixed ordinary and saturated inputs;
* include explicit mutations for omitted Jacobian, wrong Jacobian sign, wrong mask and missing component.

That test must remain separate from the runtime replay tolerance.

### Registered-contract consequence

The replay contract embedded in checkpoints currently declares absolute component tolerances. Changing it to mixed tolerances and a ratio ceiling changes the registered contract and should make older development artifacts unloadable. The strict checkpoint loader already compares the whole registered contract. No compatibility path is appropriate.

Because the aborted run produced no checkpoint or result, the correct disposition is:

```text
REPLAY_LOG_COMPONENT_ATOL = 1e-6
REPLAY_LOG_COMPONENT_RTOL = 8 * 2^-24
REPLAY_LOG_RATIO_DRIFT_CAP = 1e-4

ordinary non-likelihood continuous fields: absolute 1e-6
exact semantic fields: exact zero
joint compositional and assembly rules: unchanged
resume tolerance: unchanged 1e-7
```

This corrects an unexecutable numerical specification without loosening the causal estimand, result thresholds, model, reward, seeds or budget.
